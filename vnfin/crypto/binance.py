"""Binance public klines adapter (clean-room).

Built only against Binance's own documented public market-data endpoint
(``GET https://api.binance.com/api/v3/klines``) and the live-verified response
shape — see ``docs/sources/crypto-binance.md`` for provenance, the exact array
index map, units, rate-limit notes, and compliance caveats.

Key facts (live-verified):
- Keyless public endpoint. No API key.
- Response is a JSON ARRAY OF ARRAYS (not a UDF envelope). Each row:
  ``[openTime_ms, open, high, low, close, volume, closeTime_ms, quoteVolume,
  numTrades, takerBuyBase, takerBuyQuote, ignore]``. Numeric fields are STRINGS.
- Prices are in the pair's QUOTE asset. USD-stablecoin quotes (USDT/USDC/BUSD/
  FDUSD/TUSD/USD) are reported as ``currency="USD"`` (~1:1); non-USD quotes
  (e.g. ``ETHBTC`` -> BTC) keep their actual quote asset as ``currency``. No
  price scaling applied. The base/quote legs are parsed from the symbol.
- Volume (index 5) is BASE-asset volume and fractional -> kept as float.
- An error is returned as a JSON OBJECT, e.g. ``{"code":-1121,"msg":"Invalid symbol."}``.
- Up to 1000 rows per call; the adapter PAGINATES via startTime/endTime (epoch ms),
  advancing past the last returned bar until the requested ``end`` is covered or the
  provider returns a short page, so long ranges are not silently truncated.
- Deep daily history (BTCUSDT genesis 2017-08-17). Rate limit is request-weight
  based (klines weight ~1-10/call depending on limit; ~1200 weight/min budget),
  surfaced via ``x-mbx-used-weight`` response headers.

This adapter follows the same conventions as ``vnfin.sources.udf.UDFSource``:
injectable ``http_get`` (default httpx forcing IPv4 + browser UA + 25s timeout),
transport errors wrapped as ``SourceUnavailable``, malformed/garbage scalars and
self-inconsistent rows wrapped as ``InvalidData`` (failover-safe), no-data wrapped
as ``EmptyData``.
"""
from __future__ import annotations

import math
from datetime import date, datetime, time, timezone

from ..exceptions import (
    EmptyData,
    InvalidData,
    UnsupportedInterval,
)
from ..models import Interval
from ..transport import DEFAULT_UA, HttpDataSource
from .models import CryptoBar, CryptoHistory

# Binance kline array index map (verified live).
_OPEN_TIME = 0
_OPEN = 1
_HIGH = 2
_LOW = 3
_CLOSE = 4
_VOLUME = 5
_MIN_FIELDS = 6  # we read indices 0..5; rows always have 12 but require at least 6

# USD-stablecoin quote assets reported to callers as ``currency="USD"`` (~1:1).
_USD_STABLE_QUOTES = ("USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USDP", "DAI", "USD")
# Other recognized Binance quote assets, kept as the literal quote currency.
_OTHER_QUOTES = ("BTC", "ETH", "BNB", "EUR", "GBP", "TRY", "BRL", "JPY", "AUD")
# Longest-first so e.g. FDUSD is matched before USD and BUSD before USD.
_KNOWN_QUOTES = tuple(
    sorted(set(_USD_STABLE_QUOTES) | set(_OTHER_QUOTES), key=len, reverse=True)
)
# Interval -> bar duration in milliseconds (for advancing the pagination cursor).
_INTERVAL_MS = {
    Interval.M1: 60_000,
    Interval.M5: 5 * 60_000,
    Interval.M15: 15 * 60_000,
    Interval.M30: 30 * 60_000,
    Interval.H1: 60 * 60_000,
    Interval.D1: 24 * 60 * 60_000,
    Interval.W1: 7 * 24 * 60 * 60_000,
    # Calendar months vary; 28 days is a safe lower bound so the cursor never
    # overshoots a real bar (we always advance past the last returned openTime).
    Interval.MN1: 28 * 24 * 60 * 60_000,
}
# Safety cap on pagination calls to bound deep-history backfills.
_MAX_PAGES = 5000


class BinanceCryptoSource(HttpDataSource):
    """Adapter over Binance public ``/api/v3/klines``.

    Constructed once and reused. Prices are denominated in the pair's quote asset;
    USD-stablecoin quotes (USDT/USDC/...) are reported as ``currency="USD"``.
    """

    NAME = "binance"
    BASE_URL = "https://api.binance.com"
    KLINES_PATH = "/api/v3/klines"
    CURRENCY = "USD"
    #: Declared unit for the failover unit-homogeneity guard. USD-stablecoin quote
    #: pairs (USDT/USDC/...) are reported as USD, so the default chain is unit-homogeneous.
    unit = "USD"
    MAX_LIMIT = 1000

    # All vnfin intervals map to a Binance interval token (all verified live).
    RESOLUTION_MAP = {
        Interval.M1: "1m",
        Interval.M5: "5m",
        Interval.M15: "15m",
        Interval.M30: "30m",
        Interval.H1: "1h",
        Interval.D1: "1d",
        Interval.W1: "1w",
        Interval.MN1: "1M",
    }
    SUPPORTED = frozenset(RESOLUTION_MAP)

    def __init__(self, http_get=None, timeout: float = 25.0):
        # http_get(url, params, headers) -> response text. Injectable for testing.
        super().__init__(http_get=http_get, timeout=timeout)

    @property
    def name(self) -> str:
        return self.NAME

    def supports(self, interval: Interval) -> bool:
        return interval in self.SUPPORTED

    def normalize_symbol(self, symbol: str) -> str:
        if symbol is None or not isinstance(symbol, str) or not symbol.strip():
            raise InvalidData(f"{self.name}: empty/invalid symbol {symbol!r}")
        return symbol.strip().upper()

    def parse_symbol(self, symbol: str):
        """Split a Binance concatenated pair into ``(base, quote, currency)``.

        Binance symbols have no separator (e.g. ``BTCUSDT`` = base BTC / quote USDT).
        We match the longest known quote-asset suffix. ``currency`` is ``"USD"`` for
        USD-stablecoin quotes and the literal quote asset otherwise. An unrecognized
        quote asset raises ``InvalidData`` so a failover client moves on instead of
        silently mislabeling the price unit.
        """
        psym = self.normalize_symbol(symbol)
        for q in _KNOWN_QUOTES:
            if psym.endswith(q) and len(psym) > len(q):
                base = psym[: -len(q)]
                currency = "USD" if q in _USD_STABLE_QUOTES else q
                return base, q, currency
        raise InvalidData(
            f"{self.name}: cannot determine quote asset for symbol {psym!r} "
            f"(unknown quote suffix)"
        )

    # --- core flow ----------------------------------------------------------

    def get_klines(self, symbol, interval: Interval = Interval.D1, start=None, end=None) -> CryptoHistory:
        """Fetch normalized crypto OHLCV for ``symbol`` (e.g. ``BTCUSDT``).

        Raises a ``SourceError`` subclass on failure so a failover client can move on:
        ``SourceUnavailable`` (transport), ``EmptyData`` (no rows / error object),
        ``InvalidData`` (malformed/garbage/self-inconsistent), ``UnsupportedInterval``.
        """
        if not self.supports(interval):
            raise UnsupportedInterval(
                f"{self.name} does not support interval {getattr(interval, 'value', interval)}"
            )
        psym = self.normalize_symbol(symbol)
        base_asset, quote_asset, currency = self.parse_symbol(psym)
        token = self.RESOLUTION_MAP[interval]
        lo, hi = self._range_bounds(start, end)
        lo_ms = int(lo.astimezone(timezone.utc).timestamp() * 1000)
        hi_ms = int(hi.astimezone(timezone.utc).timestamp() * 1000)
        step_ms = _INTERVAL_MS[interval]

        # Paginate: Binance caps each call at MAX_LIMIT (1000) rows. Walk forward from
        # the last returned open time until ``end`` is covered or a short page arrives,
        # so long ranges are not silently truncated.
        all_bars: list[CryptoBar] = []
        seen_open_ms: set[int] = set()
        cursor = lo_ms
        warnings: list[str] = []
        pages = 0
        while cursor <= hi_ms:
            pages += 1
            if pages > _MAX_PAGES:
                warnings.append(
                    f"partial_coverage: stopped after {_MAX_PAGES} pages; range may be incomplete"
                )
                break
            parsed = self._fetch_page(psym, token, cursor, hi_ms)
            if not parsed:
                if not all_bars:
                    raise EmptyData(f"{self.name}: empty klines")
                break
            page_bars = self._build_bars(parsed)
            last_open_ms = None
            for b in page_bars:
                ms = int(b.time.timestamp() * 1000)
                last_open_ms = ms
                if ms in seen_open_ms or not (lo_ms <= ms <= hi_ms):
                    continue
                seen_open_ms.add(ms)
                all_bars.append(b)
            # A short page (fewer than the cap) means the provider has no more data.
            if len(parsed) < self.MAX_LIMIT:
                break
            # Advance strictly past the last bar to avoid an infinite loop / re-fetch.
            nxt = (last_open_ms + step_ms) if last_open_ms is not None else (cursor + step_ms)
            if nxt <= cursor:
                nxt = cursor + step_ms
            cursor = nxt

        all_bars.sort(key=lambda b: b.time)
        if not all_bars:
            raise EmptyData(f"{self.name}: no bars in requested range")

        return CryptoHistory(
            symbol=psym,
            interval=interval,
            source=self.name,
            bars=tuple(all_bars),
            currency=currency,
            value_unit=currency,  # price unit IS the quote asset / currency
            provider_symbol=psym,
            fetched_at_utc=datetime.now(timezone.utc),
            warnings=tuple(warnings),
            base_asset=base_asset,
            quote_asset=quote_asset,
            price_unit=f"{quote_asset} per {base_asset}",
            volume_unit=base_asset,
        )

    def _fetch_page(self, psym: str, token: str, start_ms: int, end_ms: int):
        """Fetch and validate one klines page. Returns the raw row list (possibly empty).

        Wraps transport errors as ``SourceUnavailable``, non-JSON as ``InvalidData``,
        and Binance error objects as ``EmptyData`` (all ``SourceError`` subclasses).
        """
        url = self.BASE_URL + self.KLINES_PATH
        params = {
            "symbol": psym,
            "interval": token,
            "limit": self.MAX_LIMIT,
            "startTime": start_ms,
            "endTime": end_ms,
        }
        parsed = self._request_json(url, params=params, headers=self._headers())

        # Binance returns an error as a JSON object {"code":..,"msg":..}; success is a list.
        if isinstance(parsed, dict):
            msg = parsed.get("msg") or parsed.get("code")
            raise EmptyData(f"{self.name}: provider error ({msg})")
        if not isinstance(parsed, list):
            raise InvalidData(f"{self.name}: unexpected payload type {type(parsed).__name__}")
        return parsed

    def _build_bars(self, rows) -> list[CryptoBar]:
        bars: list[CryptoBar] = []
        for i, row in enumerate(rows):
            if not isinstance(row, (list, tuple)) or len(row) < _MIN_FIELDS:
                raise InvalidData(f"{self.name}: malformed kline row {i}")
            try:
                ms = int(row[_OPEN_TIME])
                tm = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
                op = float(row[_OPEN])
                hp = float(row[_HIGH])
                lp = float(row[_LOW])
                cp = float(row[_CLOSE])
                vol = float(row[_VOLUME])
            except (TypeError, ValueError, OverflowError) as exc:
                # Malformed scalar (null, garbage string, overflow) must surface as a
                # SourceError so a failover client fails over instead of crashing.
                raise InvalidData(f"{self.name}: malformed scalar at row {i}") from exc
            if not all(math.isfinite(x) for x in (op, hp, lp, cp, vol)):
                raise InvalidData(f"{self.name}: non-finite OHLCV at row {i}")
            if vol < 0:
                raise InvalidData(f"{self.name}: negative volume at row {i}")
            if any(x < 0 for x in (op, hp, lp, cp)):
                # Crypto OHLC prices cannot be negative; a negative price is malformed.
                raise InvalidData(f"{self.name}: negative price at row {i}")
            if not (lp <= op <= hp and lp <= cp <= hp and lp <= hp):
                raise InvalidData(
                    f"{self.name}: OHLC invariant violated at {tm.isoformat()}"
                )
            bars.append(CryptoBar(time=tm, open=op, high=hp, low=lp, close=cp, volume=vol))

        bars.sort(key=lambda b: b.time)
        return bars

    # --- helpers ------------------------------------------------------------

    def _headers(self) -> dict:
        return {"User-Agent": DEFAULT_UA}

    @staticmethod
    def _range_bounds(start, end):
        """Normalize a (start, end) request window to tz-aware UTC datetimes.

        Bare dates become start-of-day / end-of-day in UTC. Naive datetimes are
        assumed UTC. Defaults: start = epoch (so Binance returns genesis), end = now.
        """

        def norm(d, end_of_day, default):
            if d is None:
                return default
            if isinstance(d, datetime):
                return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
            if isinstance(d, date):
                tt = time(23, 59, 59) if end_of_day else time(0, 0, 0)
                return datetime.combine(d, tt, tzinfo=timezone.utc)
            raise InvalidData(f"binance: unsupported range bound {d!r}")

        lo = norm(start, False, datetime(1970, 1, 1, tzinfo=timezone.utc))
        hi = norm(end, True, datetime.now(timezone.utc))
        return lo, hi
