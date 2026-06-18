"""Coinbase Exchange public candles adapter (clean-room) — crypto BACKUP source.

Built only against Coinbase's own documented public market-data endpoint
(``GET https://api.exchange.coinbase.com/products/{PRODUCT}/candles``) and the
live-verified response shape — see ``docs/research/2026-06-18-crypto.md`` for
provenance, the exact array index map, units, granularity set, and compliance caveats.

Key facts (live-verified):
- Keyless public endpoint. No API key.
- Response is a JSON ARRAY OF ARRAYS (not a UDF envelope), NEWEST-FIRST. Each row:
  ``[time_sec, low, high, open, close, volume]``. NOTE two differences vs Binance:
    1. ``time`` is epoch SECONDS (not milliseconds).
    2. the order is ``low, high, open, close`` (NOT ``open, high, low, close``).
  Numeric fields are JSON NUMBERS (not strings).
- Prices are in the product's native QUOTE asset (true fiat USD, also USDC). A
  USD-stablecoin quote (USD/USDC/USDT/...) is reported as ``currency="USD"`` so the
  failover chain with Binance is unit-homogeneous; non-USD quotes keep their actual
  quote asset.
- Volume (index 5) is BASE-asset volume and fractional -> kept as float.
- An error is returned as a JSON OBJECT, e.g. ``{"message":"NotFound"}`` (bad product)
  or ``{"message":"Unsupported granularity"}``.
- Up to ~300 candles per call; the adapter PAGINATES backward via start/end ISO8601
  windows until the requested ``start`` is covered or a short page arrives.
- Granularity is in SECONDS and limited to {60, 300, 900, 3600, 21600, 86400}, i.e.
  1m / 5m / 15m / 1h / 6h / 1d. Coinbase has NO 30m, weekly, or monthly candle, so
  those intervals are NOT supported (the failover capability guard skips this source
  for them and stays on a source that does, e.g. Binance).

Symbol handling
---------------
Coinbase products are ``BASE-QUOTE`` with a hyphen (e.g. ``BTC-USD``). This adapter
accepts BOTH that hyphenated product form and the Binance-style concatenated form
(``BTCUSDT``) and normalizes internally so the same ``get_klines(symbol, ...)`` call
works across the failover chain. A USD-stablecoin quote (USDT/USDC/...) is mapped to a
Coinbase ``-USD`` product (Coinbase's native fiat pair).

This adapter follows the same conventions as ``vnfin.crypto.binance``: injectable
``http_get`` via :class:`vnfin.transport.HttpDataSource`, transport errors wrapped as
``SourceUnavailable``, malformed/garbage scalars and self-inconsistent rows wrapped as
``InvalidData`` (failover-safe), provider error objects / no-data wrapped as ``EmptyData``.
"""
from __future__ import annotations

import math
from datetime import date, datetime, time, timezone

from ..exceptions import EmptyData, InvalidData, UnsupportedInterval
from ..models import Interval
from ..transport import DEFAULT_UA, HttpDataSource
from .models import CryptoBar, CryptoHistory

# Coinbase candle array index map (verified live, NEWEST-FIRST, low/high/open/close).
_TIME = 0  # epoch SECONDS
_LOW = 1
_HIGH = 2
_OPEN = 3
_CLOSE = 4
_VOLUME = 5
_MIN_FIELDS = 6

# USD-stablecoin quote assets reported to callers as ``currency="USD"`` (~1:1).
_USD_STABLE_QUOTES = ("USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USDP", "DAI", "USD")
# Quotes that have NO native Coinbase product and must be redirected to the BASE-USD
# fiat product (e.g. a caller passing the Binance BTCUSDT gets the Coinbase BTC-USD
# product). USDC/USD are kept as their own native Coinbase product legs.
_REDIRECT_TO_USD_PRODUCT = ("USDT", "BUSD", "FDUSD", "TUSD", "USDP", "DAI")
# Other recognized quote assets, kept as the literal quote currency / product leg.
_OTHER_QUOTES = ("BTC", "ETH", "EUR", "GBP", "USDC", "DAI")
# Longest-first so e.g. FDUSD is matched before USD and USDC before USD.
_KNOWN_QUOTES = tuple(
    sorted(set(_USD_STABLE_QUOTES) | set(_OTHER_QUOTES), key=len, reverse=True)
)

# Interval -> bar duration in seconds (for advancing the backward pagination window).
_INTERVAL_SEC = {
    Interval.M1: 60,
    Interval.M5: 5 * 60,
    Interval.M15: 15 * 60,
    Interval.H1: 60 * 60,
    Interval.D1: 24 * 60 * 60,
}
# Coinbase caps each call at ~300 candles. An inclusive [lo, hi] window of
# ``step * (PAGE_CANDLES - 1)`` holds EXACTLY PAGE_CANDLES candle slots, so the
# provider never has to drop a boundary candle to honor its 300-row cap. (Using
# ``step * PAGE_CANDLES`` spans 301 inclusive slots -> the provider truncates one
# boundary candle per page, which the backward step then skips: B10 regression.)
_PAGE_CANDLES = 300
# Candle slots per page window (inclusive range): one fewer than the candle cap.
_PAGE_SPAN_CANDLES = _PAGE_CANDLES - 1
# Safety cap on pagination calls to bound deep-history backfills.
_MAX_PAGES = 5000


class CoinbaseCryptoSource(HttpDataSource):
    """Adapter over Coinbase Exchange public ``/products/{PRODUCT}/candles``.

    Constructed once and reused. Prices are denominated in the product's native quote
    asset; USD-stablecoin quotes are reported as ``currency="USD"`` and ``unit="USD"``
    so this source can back up the Binance primary in one failover chain.
    """

    NAME = "coinbase"
    BASE_URL = "https://api.exchange.coinbase.com"
    CURRENCY = "USD"
    #: Declared unit for the failover unit-homogeneity guard.
    unit = "USD"

    # Coinbase granularities are in SECONDS. Only these six exist; 30m/1w/1M absent.
    RESOLUTION_MAP = {
        Interval.M1: 60,
        Interval.M5: 300,
        Interval.M15: 900,
        Interval.H1: 3600,
        Interval.D1: 86400,
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

    # --- symbol handling ----------------------------------------------------

    def normalize_symbol(self, symbol: str) -> str:
        if symbol is None or not isinstance(symbol, str) or not symbol.strip():
            raise InvalidData(f"{self.name}: empty/invalid symbol {symbol!r}")
        return symbol.strip().upper()

    def parse_symbol(self, symbol: str):
        """Resolve any input symbol to ``(base, quote, currency, product)``.

        Accepts a hyphenated Coinbase product (``BTC-USD``) or a Binance-style
        concatenated pair (``BTCUSDT``). ``currency`` is ``"USD"`` for USD-stablecoin
        quotes (and ``product`` becomes ``BASE-USD``, Coinbase's native fiat pair),
        otherwise the literal quote asset. An unrecognized quote raises ``InvalidData``
        so a failover client moves on instead of mislabeling the price unit.
        """
        sym = self.normalize_symbol(symbol)
        if "-" in sym:
            base, _, quote = sym.partition("-")
            if not base or not quote:
                raise InvalidData(f"{self.name}: malformed product symbol {sym!r}")
        else:
            base, quote = self._split_concatenated(sym)
        currency = "USD" if quote in _USD_STABLE_QUOTES else quote
        # Quotes Coinbase does not trade natively (e.g. USDT) redirect to the BASE-USD
        # fiat product; USDC/USD/non-USD quotes keep their own native Coinbase product.
        # The reported quote_asset reflects the ACTUAL Coinbase product leg, never a
        # synthetic leg Coinbase does not trade.
        product_quote = "USD" if quote in _REDIRECT_TO_USD_PRODUCT else quote
        product = f"{base}-{product_quote}"
        return base, product_quote, currency, product

    def _split_concatenated(self, sym: str):
        for q in _KNOWN_QUOTES:
            if sym.endswith(q) and len(sym) > len(q):
                return sym[: -len(q)], q
        raise InvalidData(
            f"{self.name}: cannot determine quote asset for symbol {sym!r} "
            f"(unknown quote suffix)"
        )

    # --- core flow ----------------------------------------------------------

    def get_klines(self, symbol, interval: Interval = Interval.D1, start=None, end=None) -> CryptoHistory:
        """Fetch normalized crypto OHLCV for ``symbol`` (e.g. ``BTC-USD`` or ``BTCUSDT``).

        Raises a ``SourceError`` subclass on failure so a failover client can move on:
        ``SourceUnavailable`` (transport), ``EmptyData`` (no rows / provider error),
        ``InvalidData`` (malformed/garbage/self-inconsistent), ``UnsupportedInterval``.
        """
        if not self.supports(interval):
            raise UnsupportedInterval(
                f"{self.name} does not support interval {getattr(interval, 'value', interval)}"
            )
        base_asset, quote_asset, currency, product = self.parse_symbol(symbol)
        granularity = self.RESOLUTION_MAP[interval]
        lo, hi = self._range_bounds(start, end)
        lo_sec = int(lo.astimezone(timezone.utc).timestamp())
        hi_sec = int(hi.astimezone(timezone.utc).timestamp())
        step_sec = _INTERVAL_SEC[interval]
        # Inclusive [lo, hi] window holding EXACTLY PAGE_CANDLES candle slots (see
        # _PAGE_SPAN_CANDLES) so the provider's 300-row cap never drops a boundary candle.
        page_span = step_sec * _PAGE_SPAN_CANDLES

        # Paginate backward: Coinbase returns ~300 newest candles per call. Walk the
        # [start, end] window in <=300-candle slabs from the most recent backward until
        # the requested ``start`` is covered, so long ranges are not silently truncated.
        # Consecutive slabs OVERLAP by one candle (the lower bound of one slab is the
        # upper bound of the next) and ``seen_sec`` de-duplicates, so a candle that
        # straddles a slab boundary can never be skipped.
        all_bars: list[CryptoBar] = []
        seen_sec: set[int] = set()
        warnings: list[str] = []
        window_hi = hi_sec
        pages = 0
        first_page = True
        while window_hi >= lo_sec:
            pages += 1
            if pages > _MAX_PAGES:
                warnings.append(
                    f"partial_coverage: stopped after {_MAX_PAGES} pages; range may be incomplete"
                )
                break
            window_lo = max(lo_sec, window_hi - page_span)
            parsed = self._fetch_page(product, granularity, window_lo, window_hi)
            if not parsed:
                # A provider error object already raised; an empty list just means this
                # slab has no candles — stop only if we already have data, else continue
                # to the next (older) slab unless we've exhausted the range.
                if all_bars or window_lo <= lo_sec:
                    break
                # Overlap by one candle (dedupe via seen_sec) so a boundary candle
                # straddling two slabs is never skipped.
                window_hi = window_lo
                first_page = False
                continue
            page_bars = self._build_bars(parsed)
            for b in page_bars:
                sec = int(b.time.timestamp())
                if sec in seen_sec or not (lo_sec <= sec <= hi_sec):
                    continue
                seen_sec.add(sec)
                all_bars.append(b)
            # Step to the next (older) slab. Overlap by one candle (the new upper
            # bound equals this slab's lower bound) so a candle on the slab boundary
            # is fetched by both slabs and de-duplicated by seen_sec, never skipped.
            if window_lo <= lo_sec:
                break
            window_hi = window_lo
            first_page = False

        all_bars.sort(key=lambda b: b.time)
        if not all_bars:
            raise EmptyData(f"{self.name}: no bars in requested range")

        return CryptoHistory(
            symbol=product,
            interval=interval,
            source=self.name,
            bars=tuple(all_bars),
            currency=currency,
            value_unit=currency,  # price unit IS the quote asset / currency
            provider_symbol=product,
            fetched_at_utc=datetime.now(timezone.utc),
            warnings=tuple(warnings),
            base_asset=base_asset,
            quote_asset=quote_asset,
            price_unit=f"{currency} per {base_asset}",
            volume_unit=base_asset,
        )

    def _fetch_page(self, product: str, granularity: int, start_sec: int, end_sec: int):
        """Fetch and validate one candles page. Returns the raw row list (possibly empty).

        Wraps transport errors as ``SourceUnavailable`` (via the transport base), non-JSON
        as ``InvalidData``, and Coinbase error objects as ``EmptyData``.
        """
        url = f"{self.BASE_URL}/products/{product}/candles"
        params = {
            "granularity": granularity,
            "start": self._iso(start_sec),
            "end": self._iso(end_sec),
        }
        parsed = self._request_json(url, params=params, headers=self._headers())

        # Coinbase returns an error as a JSON object {"message": ...}; success is a list.
        if isinstance(parsed, dict):
            msg = parsed.get("message") or parsed.get("error") or "provider error"
            raise EmptyData(f"{self.name}: provider error ({msg})")
        if not isinstance(parsed, list):
            raise InvalidData(f"{self.name}: unexpected payload type {type(parsed).__name__}")
        return parsed

    def _build_bars(self, rows) -> list[CryptoBar]:
        bars: list[CryptoBar] = []
        for i, row in enumerate(rows):
            if not isinstance(row, (list, tuple)) or len(row) < _MIN_FIELDS:
                raise InvalidData(f"{self.name}: malformed candle row {i}")
            try:
                sec = int(row[_TIME])
                tm = datetime.fromtimestamp(sec, tz=timezone.utc)
                lp = float(row[_LOW])
                hp = float(row[_HIGH])
                op = float(row[_OPEN])
                cp = float(row[_CLOSE])
                vol = float(row[_VOLUME])
            except (TypeError, ValueError, OverflowError) as exc:
                raise InvalidData(f"{self.name}: malformed scalar at row {i}") from exc
            if not all(math.isfinite(x) for x in (op, hp, lp, cp, vol)):
                raise InvalidData(f"{self.name}: non-finite OHLCV at row {i}")
            if vol < 0:
                raise InvalidData(f"{self.name}: negative volume at row {i}")
            if any(x < 0 for x in (op, hp, lp, cp)):
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
    def _iso(sec: int) -> str:
        return datetime.fromtimestamp(sec, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def _range_bounds(start, end):
        """Normalize a (start, end) request window to tz-aware UTC datetimes.

        Bare dates become start-of-day / end-of-day in UTC. Naive datetimes are
        assumed UTC. Defaults: start = epoch, end = now.
        """

        def norm(d, end_of_day, default):
            if d is None:
                return default
            if isinstance(d, datetime):
                return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
            if isinstance(d, date):
                tt = time(23, 59, 59) if end_of_day else time(0, 0, 0)
                return datetime.combine(d, tt, tzinfo=timezone.utc)
            raise InvalidData(f"coinbase: unsupported range bound {d!r}")

        lo = norm(start, False, datetime(1970, 1, 1, tzinfo=timezone.utc))
        hi = norm(end, True, datetime.now(timezone.utc))
        return lo, hi
