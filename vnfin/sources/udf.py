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

from ..coerce import parse_provider_float, parse_provider_int
from ..exceptions import EmptyData, InvalidData, UnsupportedInterval
from ..models import AdjustmentPolicy, Interval, PriceBar, PriceHistory
from ..transport import DEFAULT_UA, HttpDataSource
from ..validation import validate_date_range, validate_non_empty_string
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
    unit = "VND"  # equity UDF prices are money in VND (failover unit guard)

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
        # Issue #65: validate caller inputs before normalization or range conversion
        # so direct source calls raise stable InvalidData instead of raw TypeError.
        symbol = validate_non_empty_string(symbol, f"{self.name} symbol")
        if not isinstance(interval, Interval):
            raise InvalidData(
                f"{self.name}: interval must be a vnfin.models.Interval, got {type(interval).__name__}"
            )
        validate_date_range(start, end, name=f"{self.name} history")
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
        try:
            data = self._extract(parsed)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError) as exc:
            # Envelope extraction is adapter-specific; structural shape errors must
            # be converted to InvalidData so failover is never exposed to raw
            # exceptions. Library-level source errors (e.g. SourceUnavailable from
            # an outer-envelope check) are re-raised unchanged.
            raise InvalidData(f"{self.name}: malformed UDF envelope") from exc
        if not isinstance(data, dict):
            raise InvalidData(
                f"{self.name}: UDF data is not an object, got {type(data).__name__}"
            )

        # Issue #21: when the provider echoes the requested symbol in the response,
        # validate it matches what we asked for before stamping identifiers onto the
        # result. Accept either the provider alias or the canonical caller symbol.
        resp_symbol = data.get("symbol")
        if resp_symbol is not None:
            resp_sym_norm = str(resp_symbol).strip().upper()
            canonical = symbol.strip().upper()
            if resp_sym_norm and resp_sym_norm not in (psym, canonical):
                raise InvalidData(
                    f"{self.name}: response symbol {resp_symbol!r} does not match "
                    f"requested {canonical!r} (provider alias {psym!r})"
                )

        status = data.get("s")
        if status != "ok":
            # UDF status is strictly "ok" for success. "no_data" / "error" mean
            # empty for this request; anything else (missing, unknown, garbage) is
            # malformed data and must raise InvalidData so failover does not mask
            # provider contract drift.
            if status in ("no_data", "error"):
                raise EmptyData(f"{self.name}: status={status}")
            raise InvalidData(f"{self.name}: unexpected UDF status {status!r}")

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
            value_unit="VND",  # equity prices are money in VND
            exchange=self.EXCHANGE,
            provider_symbol=psym,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _build_bars(self, data) -> list[PriceBar]:
        # Required OHLC arrays must be present and list/tuple-like. Scalars,
        # strings, bytes, and None must raise InvalidData, never a raw TypeError.
        required = ("t", "o", "h", "l", "c")
        try:
            arrays = {k: data[k] for k in required}
        except (KeyError, TypeError) as exc:
            raise InvalidData(f"{self.name}: missing UDF arrays") from exc
        for k, v in arrays.items():
            if not isinstance(v, (list, tuple)):
                raise InvalidData(f"{self.name}: UDF array {k!r} is not a sequence")

        t = arrays["t"]
        o, h, l, c = arrays["o"], arrays["h"], arrays["l"], arrays["c"]
        n = len(t)
        if not (len(o) == len(h) == len(l) == len(c) == n):
            raise InvalidData(f"{self.name}: misaligned UDF arrays")

        # Issue #55: a present-but-empty volume array is structurally inconsistent
        # with non-empty OHLC arrays and must raise InvalidData. A missing volume
        # field or an explicit null is an intentional provider shortcut -> zeros.
        if "v" in data:
            v = data["v"]
            if v is None:
                v = [0] * n
            elif not isinstance(v, (list, tuple)):
                raise InvalidData(f"{self.name}: UDF array 'v' is not a sequence")
            elif len(v) != n:
                raise InvalidData(f"{self.name}: misaligned UDF arrays")
        else:
            v = [0] * n

        bars: list[PriceBar] = []
        seen_times: set = set()  # Issue #66: reject duplicate timestamps within one response
        for i in range(n):
            try:
                ts = parse_provider_int(t[i], label=f"timestamp at row {i}", source=self.name)
                tm = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(VN_TZ)
                op = parse_provider_float(o[i], label=f"open at row {i}", source=self.name) * self.PRICE_SCALE
                hp = parse_provider_float(h[i], label=f"high at row {i}", source=self.name) * self.PRICE_SCALE
                lp = parse_provider_float(l[i], label=f"low at row {i}", source=self.name) * self.PRICE_SCALE
                cp = parse_provider_float(c[i], label=f"close at row {i}", source=self.name) * self.PRICE_SCALE
                raw_vol = parse_provider_float(v[i], label=f"volume at row {i}", source=self.name) * self.VOLUME_SCALE
            except (TypeError, ValueError, OverflowError) as exc:
                # Malformed scalar (null, garbage string, overflow) must surface as a
                # SourceError so FailoverPriceClient fails over instead of crashing.
                raise InvalidData(f"{self.name}: malformed scalar at row {i}") from exc
            if not all(math.isfinite(x) for x in (op, hp, lp, cp, raw_vol)):
                raise InvalidData(f"{self.name}: non-finite OHLCV at row {i}")
            # Issue #13: zero price observations are not valid market data for an
            # equity/index series; reject them as provider/parse drift.
            if not all(x > 0 for x in (op, hp, lp, cp)):
                raise InvalidData(f"{self.name}: non-positive price at row {i}")
            if raw_vol < 0:
                raise InvalidData(f"{self.name}: negative volume at row {i}")
            # Issue #120: equity/index volume must be whole after VOLUME_SCALE. A fractional
            # value is provider/parse drift; reject it rather than silently rounding.
            if not raw_vol.is_integer():
                raise InvalidData(f"{self.name}: fractional volume {raw_vol!r} at row {i}")
            vol = int(raw_vol)
            if not (lp <= op <= hp and lp <= cp <= hp and lp <= hp):
                raise InvalidData(f"{self.name}: OHLC invariant violated at {tm.date()}")
            # Issue #66: a duplicate observation timestamp in one response is conflicting
            # provider data; reject it instead of returning an ambiguous duplicate-keyed series.
            if tm in seen_times:
                raise InvalidData(f"{self.name}: duplicate observation timestamp {tm.isoformat()}")
            seen_times.add(tm)
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
