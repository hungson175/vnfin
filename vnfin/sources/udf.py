"""Shared base for TradingView-UDF style price sources.

Handles the common transport, UDF envelope parsing, array alignment, timezone
conversion, price/volume scaling, and structural validation. Each concrete adapter
subclasses this and overrides only what differs: ``BASE_URL``, ``HISTORY_PATH``,
``SUPPORTED``, ``RESOLUTION_MAP``, ``PRICE_SCALE``, ``ADJUSTMENT_POLICY``,
``EXCHANGE``, ``_build_params``, ``_headers``, and ``_extract`` (envelope unwrap).
"""
from __future__ import annotations

import math
from datetime import date, datetime, time, timezone

from ..exceptions import EmptyData, InvalidData, UnsupportedInterval
from ..models import AdjustmentPolicy, Interval, PriceBar, PriceHistory
from ..transport import DEFAULT_UA, HttpDataSource
from .base import VN_TZ, PriceSource


class UDFSource(HttpDataSource, PriceSource):
    # --- per-adapter configuration (override in subclasses) ---
    NAME = "udf"
    BASE_URL = ""
    HISTORY_PATH = "/history"
    SUPPORTED = frozenset({Interval.D1})
    RESOLUTION_MAP = {Interval.D1: "D"}
    ADJUSTMENT_POLICY = AdjustmentPolicy.UNKNOWN
    PRICE_SCALE = 1.0  # multiply feed price to reach VND (e.g. 1000 if feed is in thousands)
    VOLUME_SCALE = 1.0
    EXCHANGE = None

    def __init__(self, http_get=None, timeout: float = 25.0):
        # http_get(url, params, headers) -> response text. Injectable for testing.
        super().__init__(http_get=http_get, timeout=timeout)

    @property
    def name(self) -> str:
        return self.NAME

    def supports(self, interval: Interval) -> bool:
        return interval in self.SUPPORTED

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.strip().upper()

    # --- subclass hooks ---
    def _build_params(self, provider_symbol, resolution, frm, to):  # pragma: no cover
        raise NotImplementedError

    def _headers(self) -> dict:
        return {"User-Agent": DEFAULT_UA}

    def _extract(self, parsed):
        """Return the UDF dict (arrays t/o/h/l/c/v + status s). Override for envelopes."""
        return parsed

    # --- core flow ---
    def get_history(self, symbol, interval, start, end) -> PriceHistory:
        if not self.supports(interval):
            raise UnsupportedInterval(
                f"{self.name} does not support interval {getattr(interval, 'value', interval)}"
            )
        psym = self.normalize_symbol(symbol)
        resolution = self.RESOLUTION_MAP[interval]
        lo, hi = self._range_bounds(start, end)
        frm = int(lo.astimezone(timezone.utc).timestamp())
        to = int(hi.astimezone(timezone.utc).timestamp())
        url = self.BASE_URL + self.HISTORY_PATH
        params = self._build_params(psym, resolution, frm, to)

        parsed = self._request_json(url, params=params, headers=self._headers())
        data = self._extract(parsed) or {}
        status = data.get("s")
        if status in ("no_data", "error"):
            raise EmptyData(f"{self.name}: status={status}")

        bars = [b for b in self._build_bars(data) if lo <= b.time <= hi]
        if not bars:
            raise EmptyData(f"{self.name}: no bars in requested range")

        return PriceHistory(
            symbol=psym,
            interval=interval,
            adjustment_policy=self.ADJUSTMENT_POLICY,
            source=self.name,
            bars=tuple(bars),
            currency="VND",
            exchange=self.EXCHANGE,
            provider_symbol=psym,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _build_bars(self, data) -> list[PriceBar]:
        try:
            t = data["t"]
            o, h, l, c = data["o"], data["h"], data["l"], data["c"]
            v = data.get("v") or [0] * len(t)
        except (KeyError, TypeError) as exc:
            raise InvalidData(f"{self.name}: missing UDF arrays") from exc

        n = len(t)
        if not (len(o) == len(h) == len(l) == len(c) == len(v) == n):
            raise InvalidData(f"{self.name}: misaligned UDF arrays")

        bars: list[PriceBar] = []
        for i in range(n):
            try:
                tm = datetime.fromtimestamp(int(t[i]), tz=timezone.utc).astimezone(VN_TZ)
                op = float(o[i]) * self.PRICE_SCALE
                hp = float(h[i]) * self.PRICE_SCALE
                lp = float(l[i]) * self.PRICE_SCALE
                cp = float(c[i]) * self.PRICE_SCALE
                raw_vol = float(v[i]) * self.VOLUME_SCALE
            except (TypeError, ValueError, OverflowError) as exc:
                # Malformed scalar (null, garbage string, overflow) must surface as a
                # SourceError so FailoverPriceClient fails over instead of crashing.
                raise InvalidData(f"{self.name}: malformed scalar at row {i}") from exc
            if not all(math.isfinite(x) for x in (op, hp, lp, cp, raw_vol)):
                raise InvalidData(f"{self.name}: non-finite OHLCV at row {i}")
            if raw_vol < 0:
                raise InvalidData(f"{self.name}: negative volume at row {i}")
            vol = int(round(raw_vol))
            if not (lp <= op <= hp and lp <= cp <= hp and lp <= hp):
                raise InvalidData(f"{self.name}: OHLC invariant violated at {tm.date()}")
            bars.append(PriceBar(time=tm, open=op, high=hp, low=lp, close=cp, volume=vol))

        bars.sort(key=lambda b: b.time)
        return bars

    @staticmethod
    def _range_bounds(start, end):
        def norm(d, end_of_day):
            if isinstance(d, datetime):
                return d if d.tzinfo else d.replace(tzinfo=VN_TZ)
            tt = time(23, 59, 59) if end_of_day else time(0, 0, 0)
            return datetime.combine(d, tt, tzinfo=VN_TZ)

        return norm(start, False), norm(end, True)
