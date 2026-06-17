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
- Prices are in the quote asset (USDT ~ USD). No price scaling applied.
- Volume (index 5) is BASE-asset volume and fractional -> kept as float.
- An error is returned as a JSON OBJECT, e.g. ``{"code":-1121,"msg":"Invalid symbol."}``.
- Up to 1000 rows per call; paginate via startTime/endTime (epoch ms).
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

import json
import math
from datetime import date, datetime, time, timezone

from ..exceptions import (
    EmptyData,
    InvalidData,
    SourceUnavailable,
    UnsupportedInterval,
)
from ..models import Interval
from .models import CryptoBar, CryptoHistory

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Binance kline array index map (verified live).
_OPEN_TIME = 0
_OPEN = 1
_HIGH = 2
_LOW = 3
_CLOSE = 4
_VOLUME = 5
_MIN_FIELDS = 6  # we read indices 0..5; rows always have 12 but require at least 6


class BinanceCryptoSource:
    """Adapter over Binance public ``/api/v3/klines``.

    Constructed once and reused. Quote currency is USD (USDT pairs treated 1:1).
    """

    NAME = "binance"
    BASE_URL = "https://api.binance.com"
    KLINES_PATH = "/api/v3/klines"
    CURRENCY = "USD"
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
        self._http_get = http_get or self._default_http_get
        self._timeout = timeout

    @property
    def name(self) -> str:
        return self.NAME

    def supports(self, interval: Interval) -> bool:
        return interval in self.SUPPORTED

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.strip().upper()

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
        token = self.RESOLUTION_MAP[interval]
        lo, hi = self._range_bounds(start, end)
        url = self.BASE_URL + self.KLINES_PATH
        params = {
            "symbol": psym,
            "interval": token,
            "limit": self.MAX_LIMIT,
            "startTime": int(lo.astimezone(timezone.utc).timestamp() * 1000),
            "endTime": int(hi.astimezone(timezone.utc).timestamp() * 1000),
        }

        try:
            text = self._http_get(url, params, self._headers())
        except Exception as exc:  # transport-level
            raise SourceUnavailable(f"{self.name} transport error: {exc}") from exc

        try:
            parsed = json.loads(text)
        except (ValueError, TypeError) as exc:
            raise InvalidData(f"{self.name}: non-JSON response") from exc

        # Binance returns an error as a JSON object {"code":..,"msg":..}; success is a list.
        if isinstance(parsed, dict):
            msg = parsed.get("msg") or parsed.get("code")
            raise EmptyData(f"{self.name}: provider error ({msg})")
        if not isinstance(parsed, list):
            raise InvalidData(f"{self.name}: unexpected payload type {type(parsed).__name__}")
        if not parsed:
            raise EmptyData(f"{self.name}: empty klines")

        bars = [b for b in self._build_bars(parsed) if lo <= b.time <= hi]
        if not bars:
            raise EmptyData(f"{self.name}: no bars in requested range")

        return CryptoHistory(
            symbol=psym,
            interval=interval,
            source=self.name,
            bars=tuple(bars),
            currency=self.CURRENCY,
            provider_symbol=psym,
            fetched_at_utc=datetime.now(timezone.utc),
        )

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
            if not (lp <= op <= hp and lp <= cp <= hp and lp <= hp):
                raise InvalidData(
                    f"{self.name}: OHLC invariant violated at {tm.isoformat()}"
                )
            bars.append(CryptoBar(time=tm, open=op, high=hp, low=lp, close=cp, volume=vol))

        bars.sort(key=lambda b: b.time)
        return bars

    # --- helpers ------------------------------------------------------------

    def _headers(self) -> dict:
        return {"User-Agent": _UA}

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

    def _default_http_get(self, url, params, headers):  # pragma: no cover - network
        import httpx

        transport = httpx.HTTPTransport(local_address="0.0.0.0")  # force IPv4
        with httpx.Client(transport=transport, timeout=self._timeout, headers=headers) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.text
