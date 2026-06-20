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

# Issue #186: quarantine-and-warn for isolated bad upstream bars. A single per-bar
# data-quality failure (OHLC invariant, non-positive/non-finite price, bad volume,
# conflicting/duplicate timestamp, malformed scalar) drops THAT bar and keeps the rest,
# disclosing it via this never-silent warning token — instead of raising and aborting the
# whole response (which made one bad bar in a 10y window block the entire VN-Index chart).
QUARANTINED_INVALID_BARS = "quarantined_invalid_bars"

# A systematically-broken source must still fail over: raise (→ failover) when the number
# of quarantined rows exceeds ``max(_QUARANTINE_ABS_FLOOR, _QUARANTINE_FRACTION * n)``.
# The FRACTION fails a mostly-bad response; the absolute FLOOR guarantees a few isolated
# glitches NEVER block ANY window — without it a short window would fail on a single bad
# bar (1 of 5 = 20% > 10%), re-creating the very bug #186 fixes. (Mirrors the gold-leg
# coverage gate: a few isolated glitches quarantine, a mostly-bad response fails over.)
_QUARANTINE_FRACTION = 0.10
_QUARANTINE_ABS_FLOOR = 3


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
    # Issue #162/#186: duplicate-timestamp policy. Default (equity, #66): ANY duplicate
    # timestamp is conflicting provider data -> the timestamp is dropped entirely
    # (#186 quarantine; was a hard raise). Index sources opt in to deduping an
    # IDENTICAL-OHLCV same-date duplicate (keep first) while a CONFLICTING same-date bar
    # drops that date entirely (#186; was a hard raise) — see _IndexUDFMixin. Equity
    # behavior is unchanged when False (no identical-dedupe symmetry).
    _DEDUPE_IDENTICAL_DUPLICATE_BARS = False
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
        # Issue #21 (reopen): key-presence is the trigger (not truthiness). A
        # PRESENT but blank/null/non-string symbol must NOT be treated as an absent
        # field and stamped as the requested ticker; only a truly missing key keeps
        # the legacy absent-is-ok behavior.
        if "symbol" in data:
            resp_symbol = data["symbol"]
            if not isinstance(resp_symbol, str) or not resp_symbol.strip():
                raise InvalidData(
                    f"{self.name}: present response symbol {resp_symbol!r} must be a "
                    f"non-empty string identifying the requested {symbol!r}"
                )
            resp_sym_norm = resp_symbol.strip().upper()
            canonical = symbol.strip().upper()
            if resp_sym_norm not in (psym, canonical):
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

        bars = [b for b in self._build_bars(data, interval) if lo <= b.time <= hi]
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
            warnings=self._quarantine_warnings(),
        )

    def _quarantine_warnings(self) -> tuple[str, ...]:
        """Issue #186: build the never-silent ``quarantined_invalid_bars`` warning (or no
        warning) from the rows ``_build_bars`` dropped. ``self._quarantined`` is one entry
        per dropped ROW; the human tail lists each dropped (date, reason) once."""
        quarantined = getattr(self, "_quarantined", None)
        if not quarantined:
            return ()
        seen_pairs: list[tuple[str, str]] = []
        for pair in quarantined:
            if pair not in seen_pairs:
                seen_pairs.append(pair)
        detail = "; ".join(f"{label}: {reason}" for label, reason in seen_pairs)
        return (
            f"{QUARANTINED_INVALID_BARS}: dropped {len(quarantined)} bar(s) — {detail}",
        )

    def _build_bars(self, data, interval) -> list[PriceBar]:
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
        # Issue #66/#162: duplicate detection. Equity (default) keys by EXACT timestamp and
        # raises on ANY duplicate (#66). Index sources opt in (_DEDUPE_IDENTICAL_DUPLICATE_BARS)
        # to "one bar per CALENDAR DATE" — but ONLY for D1: key by tm.date() and compare
        # OHLCV+volume ignoring the intraday timestamp (identical -> dedupe keep-first;
        # conflicting -> raise). For intraday index intervals (e.g. H1) two bars legitimately
        # share a calendar date, so date-keying would wrongly collapse them — keep exact-timestamp
        # behavior there. (Index adapters support intraday via their equity base's SUPPORTED set;
        # the base UDFSource default is D1-only but subclasses may widen it.)
        seen: dict = {}  # key (calendar date | exact timestamp) -> PriceBar
        dedup_by_date = self._DEDUPE_IDENTICAL_DUPLICATE_BARS and interval is Interval.D1
        self._dedup_occurred = False  # Issue #162: set if an identical same-date dup was deduped
        # Issue #186: per-bar data-quality failures QUARANTINE the offending row (keep the
        # rest) instead of raising and aborting the whole response. ``quarantined`` records
        # one (label, reason) per dropped ROW (drives both the warning and the threshold);
        # ``poisoned`` holds keys dropped ENTIRELY (conflicting/duplicate — can't pick).
        # Structural/array-shape failures above this loop still HARD-RAISE.
        quarantined: list[tuple[str, str]] = []
        poisoned: set = set()
        for i in range(n):
            try:
                ts = parse_provider_int(t[i], label=f"timestamp at row {i}", source=self.name)
                tm = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(VN_TZ)
                op = parse_provider_float(o[i], label=f"open at row {i}", source=self.name) * self.PRICE_SCALE
                hp = parse_provider_float(h[i], label=f"high at row {i}", source=self.name) * self.PRICE_SCALE
                lp = parse_provider_float(l[i], label=f"low at row {i}", source=self.name) * self.PRICE_SCALE
                cp = parse_provider_float(c[i], label=f"close at row {i}", source=self.name) * self.PRICE_SCALE
                raw_vol = parse_provider_float(v[i], label=f"volume at row {i}", source=self.name) * self.VOLUME_SCALE
            except (InvalidData, TypeError, ValueError, OverflowError, OSError):
                # Issue #186: a single unparseable scalar is a per-ROW failure (the array
                # SHAPE is fine) -> quarantine that row, labelled by index (the timestamp is
                # unknown). The coerce helpers raise InvalidData for null/NaN/bool/garbage
                # scalars; datetime.fromtimestamp raises Overflow/OSError for an out-of-range
                # epoch. All are this-row-only — a systematically-bad column trips the
                # threshold below -> failover. A structural array-shape error still hard-raises
                # above this loop (it never reaches here).
                quarantined.append((f"row {i}", "malformed scalar"))
                continue
            if not all(math.isfinite(x) for x in (op, hp, lp, cp, raw_vol)):
                quarantined.append((tm.date().isoformat(), "non-finite OHLCV"))
                continue
            # Issue #13: zero/negative price observations are not valid market data.
            if not all(x > 0 for x in (op, hp, lp, cp)):
                quarantined.append((tm.date().isoformat(), "non-positive price"))
                continue
            if raw_vol < 0:
                quarantined.append((tm.date().isoformat(), "negative volume"))
                continue
            # Issue #120: equity/index volume must be whole after VOLUME_SCALE.
            if not raw_vol.is_integer():
                quarantined.append((tm.date().isoformat(), "fractional volume"))
                continue
            vol = int(raw_vol)
            if not (lp <= op <= hp and lp <= cp <= hp and lp <= hp):
                quarantined.append((tm.date().isoformat(), "OHLC invariant violated"))
                continue
            bar = PriceBar(time=tm, open=op, high=hp, low=lp, close=cp, volume=vol)
            # Issue #66/#162/#186: duplicate handling. dedup_by_date (index D1): an IDENTICAL
            # same-date bar (same OHLCV, even at a different intraday timestamp) dedupes
            # (keep first, #162); a CONFLICTING same-date bar drops the date ENTIRELY (#186 —
            # can't pick which is right). Equity / intraday (exact-timestamp key, #66): ANY
            # duplicate timestamp drops that timestamp entirely (#186 generalizes #66's
            # never-silently-pick intent to quarantine+drop rather than abort the whole fetch).
            # Each dropped row counts toward the threshold; the #162 identical dedupe does NOT.
            key = tm.date() if dedup_by_date else tm
            reason = (
                "conflicting same-date bars" if dedup_by_date
                else "duplicate observation timestamp"
            )
            if key in poisoned:
                quarantined.append((tm.date().isoformat(), reason))
                continue
            if key in seen:
                if dedup_by_date:
                    prev = seen[key]
                    if (prev.open, prev.high, prev.low, prev.close, prev.volume) == (
                        op, hp, lp, cp, vol
                    ):
                        self._dedup_occurred = True
                        continue  # identical same-date bar -> dedupe (keep first, #162)
                # conflicting (index) or any duplicate (equity/intraday) -> poison the key:
                # count the prior kept row + this row; the prior is removed from bars below.
                poisoned.add(key)
                quarantined.append((seen[key].time.date().isoformat(), reason))
                quarantined.append((tm.date().isoformat(), reason))
                continue
            seen[key] = bar
            bars.append(bar)

        # Drop any already-kept bar whose key was later poisoned (conflicting/duplicate).
        if poisoned:
            bars = [
                b for b in bars
                if (b.time.date() if dedup_by_date else b.time) not in poisoned
            ]

        # Issue #186: a systematically-broken response still fails over. Raise (-> failover)
        # when quarantined rows exceed max(absolute floor, fraction x n) over ALL provider
        # rows n (before range filtering). The floor guarantees a few isolated glitches never
        # block ANY window; the fraction fails a mostly-bad source.
        if n and len(quarantined) > max(_QUARANTINE_ABS_FLOOR, _QUARANTINE_FRACTION * n):
            raise InvalidData(
                f"{self.name}: {len(quarantined)}/{n} bars failed data-quality checks "
                f"(> max(floor={_QUARANTINE_ABS_FLOOR}, "
                f"{int(_QUARANTINE_FRACTION * 100)}%)) — source systematically broken"
            )

        self._quarantined = quarantined
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
