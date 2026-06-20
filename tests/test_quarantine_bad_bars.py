"""Issue #186 — quarantine-and-warn for isolated bad upstream bars (shared UDF parse path).

A single per-bar data-quality failure must DROP that bar and KEEP the rest, disclosing it
via a never-silent ``quarantined_invalid_bars`` warning — instead of raising and aborting the
whole response (which made one bad bar in a 10y window block the entire VN-Index chart). A
SYSTEMATICALLY-broken source still fails over via a threshold+floor guard. Structural/shape
failures (misaligned arrays, malformed envelope/status) stay HARD raises.

Synthetic fixtures only — clean-room, zero VNStock.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import EmptyData, InvalidData
from vnfin.models import AdjustmentPolicy, Interval
from vnfin.sources.udf import (
    QUARANTINED_INVALID_BARS,
    _QUARANTINE_ABS_FLOOR,
    _QUARANTINE_FRACTION,
    UDFSource,
)


# --------------------------------------------------------------------------- #
# dummy sources exercising the SHARED parse loop directly
# --------------------------------------------------------------------------- #
class _Eq(UDFSource):
    """Equity-like adapter: exact-timestamp duplicate keying (#66), x1000 price scale."""

    NAME = "eq_dummy"
    BASE_URL = "https://example.test"
    HISTORY_PATH = "/history"
    SUPPORTED = frozenset({Interval.D1, Interval.H1})
    RESOLUTION_MAP = {Interval.D1: "D", Interval.H1: "60"}
    ADJUSTMENT_POLICY = AdjustmentPolicy.PROVIDER_ADJUSTED
    PRICE_SCALE = 1000.0
    EXCHANGE = "HOSE"

    def _build_params(self, provider_symbol, resolution, frm, to):
        return {"symbol": provider_symbol, "resolution": resolution, "from": frm, "to": to}


class _Idx(_Eq):
    """Index-like adapter: one bar per CALENDAR DATE (#162) — date-keyed dedupe/conflict."""

    NAME = "idx_dummy"
    PRICE_SCALE = 1.0
    _DEDUPE_IDENTICAL_DUPLICATE_BARS = True


def _ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _payload(rows, status="ok") -> str:
    """rows: (date_str, o, h, l, c, v) -> bare UDF JSON."""
    return json.dumps(
        {
            "s": status,
            "t": [_ts(r[0]) for r in rows],
            "o": [r[1] for r in rows],
            "h": [r[2] for r in rows],
            "l": [r[3] for r in rows],
            "c": [r[4] for r in rows],
            "v": [r[5] for r in rows],
        }
    )


def _eq(text, cls=_Eq):
    return cls(http_get=lambda url, params, headers: text)


# wide windows fully containing every fixture date
WIDE_EQ = (date(2024, 1, 1), date(2024, 1, 31))
SPAN = (date(2016, 1, 1), date(2022, 12, 31))

_GOOD_A = ("2024-01-03", 72.3, 73.0, 72.1, 72.8, 1_200_000)
_GOOD_B = ("2024-01-30", 72.8, 73.2, 72.5, 73.0, 900_000)


def _quarantine_warning(hist):
    matches = [w for w in hist.warnings if w.startswith(QUARANTINED_INVALID_BARS)]
    return matches[0] if matches else None


# --------------------------------------------------------------------------- #
# 1. RED regression — the exact reported bug (both bad dates, multi-year span)
# --------------------------------------------------------------------------- #
def _clean_monthly_index_rows():
    # one clean bar per month across 2017-2021 (day 15) -> NEVER collides with the
    # injected bad dates (2018-08-22, 2020-12-25). Index points around ~1000.
    rows = []
    for year in range(2017, 2022):
        for month in range(1, 13):
            base = 1000.0 + (year - 2017) * 10 + month
            rows.append(
                (f"{year}-{month:02d}-15", base, base + 5.0, base - 5.0, base + 2.0, 100_000_000)
            )
    return rows


def test_regression_one_bad_bar_no_longer_blocks_multiyear_index_chart():
    # THE #186 bug: a 2018-08-22 OHLC-invariant bar AND a 2020-12-25 conflicting same-date
    # pair exist in a multi-year VN-Index series. Pre-fix -> InvalidData aborts the WHOLE
    # fetch. Post-fix -> the 60 clean monthly bars are served + both bad dates disclosed.
    clean = _clean_monthly_index_rows()
    bad_ohlc = ("2018-08-22", 1100.0, 1105.0, 1199.0, 1102.0, 100_000_000)  # low > high
    conflict_a = ("2020-12-25", 1300.0, 1310.0, 1295.0, 1305.0, 100_000_000)
    conflict_b = ("2020-12-25", 1301.0, 1311.0, 1296.0, 1306.0, 111_000_000)  # conflicting
    rows = clean + [bad_ohlc, conflict_a, conflict_b]

    h = _eq(_payload(rows), cls=_Idx).get_history("VNINDEX", Interval.D1, *SPAN)

    served = {b.time.date() for b in h.bars}
    assert len(h.bars) == len(clean)               # every clean monthly bar survives
    assert date(2018, 8, 22) not in served         # OHLC-invariant bar dropped
    assert date(2020, 12, 25) not in served        # conflicting date dropped ENTIRELY
    warn = _quarantine_warning(h)
    assert warn is not None
    assert "2018-08-22" in warn and "OHLC invariant" in warn
    assert "2020-12-25" in warn and "conflicting same-date" in warn
    assert "dropped 3 bar(s)" in warn              # 1 OHLC + 2 conflicting rows


def test_regression_pre_fix_would_have_raised_is_now_served():
    # A minimal equity series whose ONLY defect is a single OHLC-invariant bar: served,
    # not raised (the per-bar check is correct; aborting the whole range was the bug).
    rows = [_GOOD_A, ("2024-01-02", 72.0, 72.5, 99.0, 72.3, 1000), _GOOD_B]  # low 99 > high
    h = _eq(_payload(rows)).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 3), date(2024, 1, 30)]
    assert _quarantine_warning(h) is not None


# --------------------------------------------------------------------------- #
# 2. Per-validation quarantine (drop the one bad row, keep the rest, name it)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "bad_row, reason_fragment",
    [
        (("2024-01-02", 72.0, 72.5, 99.0, 72.3, 1000), "OHLC invariant"),       # low>high
        (("2024-01-02", 72.0, 72.5, 71.8, 0.0, 1000), "non-positive price"),    # zero close
        (("2024-01-02", 72.0, 72.5, 71.8, -5.0, 1000), "non-positive price"),   # negative
        (("2024-01-02", 72.0, 72.5, 71.8, 72.3, -5), "negative volume"),        # neg vol
        (("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1000.5), "fractional volume"),  # frac vol
    ],
)
def test_per_validation_quarantine_keeps_the_rest(bad_row, reason_fragment):
    rows = [_GOOD_A, bad_row, _GOOD_B]
    h = _eq(_payload(rows)).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 3), date(2024, 1, 30)]
    warn = _quarantine_warning(h)
    assert warn is not None and reason_fragment in warn
    assert "2024-01-02" in warn


def test_nan_scalar_quarantined_as_malformed_keeps_the_rest():
    # A bare NaN (json.loads parses it) is rejected by the coerce helper -> caught as a
    # per-row "malformed scalar" -> quarantine, not abort.
    payload = (
        '{"s":"ok","t":[%d,%d,%d],"o":[72.3,72.0,72.8],"h":[73.0,72.5,73.2],'
        '"l":[72.1,71.8,72.5],"c":[72.8,NaN,73.0],"v":[1200000,1000,900000]}'
        % (_ts(_GOOD_A[0]), _ts("2024-01-02"), _ts(_GOOD_B[0]))
    )
    h = _eq(payload).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 3), date(2024, 1, 30)]
    warn = _quarantine_warning(h)
    assert warn is not None and "malformed scalar" in warn


def test_post_scale_overflow_quarantined_as_nonfinite():
    # A finite feed value that overflows to +inf AFTER the x1000 price scale exercises the
    # explicit non-finite OHLCV guard (the coerce helper only sees the finite pre-scale value).
    rows = [_GOOD_A, ("2024-01-02", 72.0, 72.5, 71.8, 1e306, 1000), _GOOD_B]  # 1e306*1000 -> inf
    h = _eq(_payload(rows)).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 3), date(2024, 1, 30)]
    warn = _quarantine_warning(h)
    assert warn is not None and "non-finite" in warn


def test_malformed_scalar_quarantined_keeps_the_rest():
    # A single unparseable scalar (null close) is a per-ROW failure -> quarantine that row
    # (labelled by index, since its timestamp is unknown), not a hard raise.
    payload = (
        '{"s":"ok","t":[%d,%d,%d],"o":[72.3,72.0,72.8],"h":[73.0,72.5,73.2],'
        '"l":[72.1,71.8,72.5],"c":[72.8,null,73.0],"v":[1200000,1000,900000]}'
        % (_ts(_GOOD_A[0]), _ts("2024-01-02"), _ts(_GOOD_B[0]))
    )
    h = _eq(payload).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 3), date(2024, 1, 30)]
    warn = _quarantine_warning(h)
    assert warn is not None and "malformed scalar" in warn


# --------------------------------------------------------------------------- #
# 3. Conflict / duplicate drop semantics
# --------------------------------------------------------------------------- #
def test_index_conflicting_same_date_drops_the_date_entirely():
    rows = [
        ("2024-01-03", 1000.0, 1010.0, 995.0, 1005.0, 100),
        ("2024-01-10", 1005.0, 1015.0, 1002.0, 1012.0, 110),
        ("2024-01-10", 1007.0, 1016.0, 1003.0, 1013.0, 111),  # conflicting same date
        ("2024-01-20", 1012.0, 1020.0, 1008.0, 1018.0, 120),
    ]
    h = _eq(_payload(rows), cls=_Idx).get_history("VNINDEX", Interval.D1, *WIDE_EQ)
    served = {b.time.date() for b in h.bars}
    assert date(2024, 1, 10) not in served  # BOTH conflicting bars dropped
    assert served == {date(2024, 1, 3), date(2024, 1, 20)}
    warn = _quarantine_warning(h)
    assert warn is not None and "conflicting same-date" in warn
    assert "dropped 2 bar(s)" in warn  # both rows counted


def test_index_identical_same_date_still_deduped_not_quarantined():
    # #162 UNCHANGED: an IDENTICAL same-date duplicate dedupes (keep first); it is NOT a
    # quarantine and emits no quarantine warning.
    rows = [
        ("2024-01-03", 1000.0, 1010.0, 995.0, 1005.0, 100),
        ("2024-01-10", 1005.0, 1015.0, 1002.0, 1012.0, 110),
        ("2024-01-10", 1005.0, 1015.0, 1002.0, 1012.0, 110),  # identical duplicate
    ]
    h = _eq(_payload(rows), cls=_Idx).get_history("VNINDEX", Interval.D1, *WIDE_EQ)
    assert {b.time.date() for b in h.bars} == {date(2024, 1, 3), date(2024, 1, 10)}
    assert _quarantine_warning(h) is None  # dedupe, not quarantine


def test_equity_exact_timestamp_duplicate_drops_the_timestamp():
    # #66 generalized (#186): ANY duplicate exact timestamp -> drop that timestamp entirely
    # + quarantine, keep the rest (was: abort the whole fetch).
    rows = [
        _GOOD_A,
        ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1000),
        ("2024-01-02", 73.0, 74.0, 72.0, 73.5, 2000),  # duplicate exact timestamp
    ]
    h = _eq(_payload(rows)).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 3)]
    warn = _quarantine_warning(h)
    assert warn is not None and "duplicate observation timestamp" in warn
    assert "dropped 2 bar(s)" in warn


def test_equity_identical_exact_timestamp_duplicate_also_dropped():
    # Baseline (no #162-style symmetry on equity): an IDENTICAL exact-ts equity duplicate
    # is still dropped+quarantined (equity has no dedupe-by-date opt-in).
    rows = [
        _GOOD_A,
        ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1000),
        ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1000),  # identical exact-ts duplicate
    ]
    assert _Eq._DEDUPE_IDENTICAL_DUPLICATE_BARS is False
    h = _eq(_payload(rows)).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 3)]
    assert _quarantine_warning(h) is not None


# --------------------------------------------------------------------------- #
# 4. Threshold + absolute-floor guard (fail iff q > max(FLOOR, FRACTION*n))
# --------------------------------------------------------------------------- #
def test_constants_have_expected_ratified_values():
    assert _QUARANTINE_FRACTION == 0.10
    assert _QUARANTINE_ABS_FLOOR == 3


def test_floor_allows_three_isolated_bad_in_short_window():
    # 5 rows, 3 bad: 3 > max(floor=3, 0.1*5=0.5)=3 is False -> serve the 2 good bars.
    rows = [
        ("2024-01-05", 72.0, 72.5, 71.8, 72.3, 1000),  # good
        ("2024-01-06", 72.0, 72.5, 99.0, 72.3, 1000),  # bad: low>high
        ("2024-01-07", 72.0, 72.5, 71.8, 0.0, 1000),   # bad: zero close
        ("2024-01-08", 72.0, 72.5, 71.8, 72.3, -1),    # bad: neg vol
        ("2024-01-09", 72.0, 72.5, 71.8, 72.3, 1000),  # good
    ]
    h = _eq(_payload(rows)).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 5), date(2024, 1, 9)]
    assert _quarantine_warning(h) is not None


def test_threshold_exceeded_in_short_window_fails_over():
    # 5 rows, 4 bad: 4 > max(3, 0.5)=3 is True -> InvalidData (a SourceError -> failover).
    rows = [
        ("2024-01-05", 72.0, 72.5, 71.8, 72.3, 1000),  # good
        ("2024-01-06", 72.0, 72.5, 99.0, 72.3, 1000),  # bad
        ("2024-01-07", 72.0, 72.5, 71.8, 0.0, 1000),   # bad
        ("2024-01-08", 72.0, 72.5, 71.8, 72.3, -1),    # bad
        ("2024-01-09", 72.0, 72.5, 71.8, -2.0, 1000),  # bad
    ]
    with pytest.raises(InvalidData, match="systematically broken"):
        _eq(_payload(rows)).get_history("FPT", Interval.D1, *WIDE_EQ)


def test_fraction_dominates_in_long_window():
    # 100 rows: 10 bad -> 10 > max(3, 10.0)=10 is False -> serve. 11 bad -> 11 > 10 -> raise.
    def mk(n_bad):
        rows = []
        for i in range(100):
            d = f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}"
            if i < n_bad:
                rows.append((d, 72.0, 72.5, 99.0, 72.3, 1000))  # OHLC-invariant
            else:
                rows.append((d, 72.0, 72.5, 71.8, 72.3, 1000))
        return rows

    window = (date(2024, 1, 1), date(2024, 12, 31))
    h = _eq(_payload(mk(10))).get_history("FPT", Interval.D1, *window)
    assert len(h.bars) == 90
    with pytest.raises(InvalidData, match="systematically broken"):
        _eq(_payload(mk(11))).get_history("FPT", Interval.D1, *window)


def test_single_all_bad_row_yields_emptydata_not_invaliddata():
    # 1 row, bad: 1 > max(3, 0.1)=3 is False -> quarantined -> 0 bars -> EmptyData
    # (still a SourceError -> failover). The floor never lets a single bad bar masquerade
    # as a systematic break.
    rows = [("2024-01-02", 72.0, 72.5, 99.0, 72.3, 1000)]
    with pytest.raises(EmptyData):
        _eq(_payload(rows)).get_history("FPT", Interval.D1, *WIDE_EQ)


# --------------------------------------------------------------------------- #
# 4b. Out-of-range / unplaceable rows must NOT drive the failover verdict.
# (Reviewer adversarial finding, #186 follow-up: the threshold was computed over ALL
#  provider rows BEFORE the requested-range filter, so a provider that pads its response
#  with bad rows OUTSIDE [start, end] could spuriously fail over an otherwise-clean
#  window — re-creating the very #186 bug in the padding region.)
# --------------------------------------------------------------------------- #
def test_out_of_range_bad_bars_do_not_fail_a_clean_window():
    # Provider pads the response with 8 OHLC-invalid rows BEFORE the requested window plus
    # 3 clean in-range bars. Pre-fix: 8 > max(3, 0.1*11)=3 -> InvalidData aborts a clean
    # window. Post-fix: the out-of-range rows are dropped WITHOUT quarantine/threshold
    # accounting -> the 3 clean bars are served, with NO quarantine warning (the drops are
    # outside the window the caller asked for, so they are not disclosed as quarantined).
    out_of_range_bad = [
        (f"2023-12-{d:02d}", 72.0, 72.5, 99.0, 72.3, 1000)  # low>high, BEFORE the window
        for d in range(20, 28)  # 8 bad rows, all out of range
    ]
    clean_in_range = [
        ("2024-01-05", 72.0, 72.5, 71.8, 72.3, 1000),
        ("2024-01-10", 72.1, 72.6, 71.9, 72.4, 1100),
        ("2024-01-15", 72.2, 72.7, 72.0, 72.5, 1200),
    ]
    rows = out_of_range_bad + clean_in_range
    h = _eq(_payload(rows)).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [
        date(2024, 1, 5), date(2024, 1, 10), date(2024, 1, 15)
    ]
    assert _quarantine_warning(h) is None  # out-of-range drops are silent, not quarantined


def test_unparseable_timestamp_rows_excluded_from_failover_threshold():
    # A row whose TIMESTAMP can't be parsed can be neither served nor range-attributed, so it
    # must NOT count toward the systematically-broken verdict (else out-of-window padding of
    # garbage-timestamp rows would spuriously fail over a clean window). It is still disclosed.
    clean = [
        ("2024-01-05", 72.0, 72.5, 71.8, 72.3, 1000),
        ("2024-01-10", 72.1, 72.6, 71.9, 72.4, 1100),
    ]
    null_ts = 5  # > max(3, 0.1*7)=3 pre-fix -> InvalidData; post-fix not counted -> serve 2
    payload = json.dumps(
        {
            "s": "ok",
            "t": [None] * null_ts + [_ts(r[0]) for r in clean],
            "o": [72.0] * null_ts + [r[1] for r in clean],
            "h": [72.5] * null_ts + [r[2] for r in clean],
            "l": [71.8] * null_ts + [r[3] for r in clean],
            "c": [72.3] * null_ts + [r[4] for r in clean],
            "v": [1000] * null_ts + [r[5] for r in clean],
        }
    )
    h = _eq(payload).get_history("FPT", Interval.D1, *WIDE_EQ)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 5), date(2024, 1, 10)]
    assert _quarantine_warning(h) is not None  # still disclosed (never silent)


def test_out_of_range_padding_does_not_break_prices_history():
    # End-to-end at the public API: every chart request goes through prices.history. A
    # provider padding 6 OHLC-invalid out-of-range rows must not knock the source out of the
    # failover chain — the clean requested window renders. This is the real #186 symptom.
    from vnfin import prices

    inner = {
        "s": "ok",
        "t": [_ts(f"2023-12-2{d}") for d in range(6)] + [_ts("2024-01-10"), _ts("2024-01-20")],
        "o": [72.0] * 6 + [72.0, 72.1],
        "h": [72.5] * 6 + [72.5, 72.6],
        "l": [99.0] * 6 + [71.8, 71.9],  # low>high for the 6 out-of-range rows only
        "c": [72.3] * 6 + [72.3, 72.4],
        "v": [1000] * 8,
    }
    env = json.dumps({"code": "SUCCESS", "message": "ok", "status": "ok", "data": inner})
    h = prices.history("FPT", Interval.D1, *WIDE_EQ, http_get=lambda u, p, hd: env)
    assert [b.time.date() for b in h.bars] == [date(2024, 1, 10), date(2024, 1, 20)]
    assert _quarantine_warning(h) is None


# --------------------------------------------------------------------------- #
# 5. Warning threads through BOTH public accessors; order = quarantine, then dedupe
# --------------------------------------------------------------------------- #
def test_quarantine_warning_surfaces_via_prices_history():
    from vnfin import prices

    inner = {
        "s": "ok",
        "t": [_ts(_GOOD_A[0]), _ts("2024-01-02"), _ts(_GOOD_B[0])],
        "o": [72.3, 72.0, 72.8], "h": [73.0, 72.5, 73.2],
        "l": [72.1, 99.0, 72.5], "c": [72.8, 72.3, 73.0],  # row 1 low>high
        "v": [1_200_000, 1000, 900_000],
    }
    env = json.dumps({"code": "SUCCESS", "message": "ok", "status": "ok", "data": inner})
    h = prices.history("FPT", Interval.D1, *WIDE_EQ, http_get=lambda u, p, hd: env)
    assert _quarantine_warning(h) is not None
    assert all(b.close > 0 for b in h.bars)


def test_quarantine_warning_surfaces_via_index_history():
    from vnfin.indices import index_history

    rows = [
        ("2024-06-10", 1000.0, 1010.0, 995.0, 1005.0, 100_000_000),
        ("2024-06-11", 1005.0, 1015.0, 1099.0, 1012.0, 110_000_000),  # low>high
        ("2024-06-12", 1012.0, 1020.0, 1008.0, 1018.0, 120_000_000),
    ]
    h = index_history(
        "VNINDEX", date(2024, 6, 1), date(2024, 6, 30),
        http_get=lambda u, p, hd: _payload(rows),
    )
    assert _quarantine_warning(h) is not None
    assert {b.time.date() for b in h.bars} == {date(2024, 6, 10), date(2024, 6, 12)}


def test_index_quarantine_warning_precedes_dedupe_token():
    from vnfin.indices import VPSIndexSource

    rows = [
        ("2024-06-10", 1000.0, 1010.0, 995.0, 1005.0, 100_000_000),
        ("2024-06-11", 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),
        ("2024-06-11", 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),  # identical -> dedupe
        ("2024-06-12", 1012.0, 1020.0, 1099.0, 1018.0, 120_000_000),  # low>high -> quarantine
    ]
    s = VPSIndexSource(http_get=lambda u, p, hd: _payload(rows))
    h = s.get_history("VNINDEX", Interval.D1, date(2024, 6, 1), date(2024, 6, 30))
    q_idx = next(i for i, w in enumerate(h.warnings) if w.startswith(QUARANTINED_INVALID_BARS))
    d_idx = next(i for i, w in enumerate(h.warnings) if w == "deduped_duplicate_daily_index_bars")
    assert q_idx < d_idx  # quarantine first, dedupe second
    assert {b.time.date() for b in h.bars} == {date(2024, 6, 10), date(2024, 6, 11)}


# --------------------------------------------------------------------------- #
# 6. Structural / shape failures STILL hard-raise (never quarantined)
# --------------------------------------------------------------------------- #
def test_misaligned_arrays_still_raise():
    payload = json.dumps(
        {"s": "ok", "t": [1, 2, 3], "o": [1, 2], "h": [1], "l": [1], "c": [1], "v": [1]}
    )
    with pytest.raises(InvalidData):
        _eq(payload).get_history("FPT", Interval.D1, *WIDE_EQ)


def test_scalar_array_still_raises():
    payload = json.dumps(
        {"s": "ok", "t": 42, "o": [72.0], "h": [73.0], "l": [71.0], "c": [72.0], "v": [1000]}
    )
    with pytest.raises(InvalidData):
        _eq(payload).get_history("FPT", Interval.D1, *WIDE_EQ)


def test_bad_status_still_raises():
    rows = [_GOOD_A]
    with pytest.raises(InvalidData):
        _eq(_payload(rows, status="weird_status")).get_history("FPT", Interval.D1, *WIDE_EQ)
