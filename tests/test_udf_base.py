import json
from datetime import date, timedelta

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, UnsupportedInterval
from vnfin.models import AdjustmentPolicy, Interval
from vnfin.sources.udf import UDFSource


class DummyBare(UDFSource):
    NAME = "dummy"
    BASE_URL = "https://example.test"
    HISTORY_PATH = "/history"
    SUPPORTED = frozenset({Interval.D1})
    RESOLUTION_MAP = {Interval.D1: "D"}
    ADJUSTMENT_POLICY = AdjustmentPolicy.PROVIDER_ADJUSTED
    PRICE_SCALE = 1000.0  # feed is in thousands of VND
    EXCHANGE = "HOSE"

    def _build_params(self, provider_symbol, resolution, frm, to):
        return {"symbol": provider_symbol, "resolution": resolution, "from": frm, "to": to}


class DummyEnvelope(DummyBare):
    NAME = "dummy_env"

    def _extract(self, parsed):
        return parsed["data"]


WIDE = (date(2024, 1, 1), date(2024, 1, 31))


def src_with(synth_text):
    return DummyBare(http_get=lambda url, params, headers: synth_text)


def test_parses_bare_udf(synth):
    s = src_with(synth.bare())
    h = s.get_history("fpt", Interval.D1, *WIDE)
    assert len(h) == 3
    assert h.source == "dummy"
    assert h.exchange == "HOSE"
    assert h.provider_symbol == "FPT"  # normalized uppercase
    assert h.adjustment_policy is AdjustmentPolicy.PROVIDER_ADJUSTED


def test_price_scaling_to_vnd(synth):
    h = src_with(synth.bare()).get_history("FPT", Interval.D1, *WIDE)
    # feed close 72.3 (thousands) -> 72,300 VND
    assert h.bars[0].close == pytest.approx(72_300.0)
    assert h.bars[0].open == pytest.approx(72_000.0)


def test_timezone_is_vietnam(synth):
    h = src_with(synth.bare()).get_history("FPT", Interval.D1, *WIDE)
    bar = h.bars[0]
    assert bar.time.utcoffset() == timedelta(hours=7)
    assert bar.time.date() == date(2024, 1, 2)


def test_bars_sorted_and_range_filtered(synth):
    s = src_with(synth.bare())
    h = s.get_history("FPT", Interval.D1, date(2024, 1, 3), date(2024, 1, 3))
    assert len(h) == 1
    assert h.bars[0].time.date() == date(2024, 1, 3)


def test_status_no_data_raises_empty(synth):
    s = src_with(synth.bare(status="no_data"))
    with pytest.raises(EmptyData):
        s.get_history("FPT", Interval.D1, *WIDE)


def test_status_error_raises_empty(synth):
    s = src_with(synth.bare(status="error"))
    with pytest.raises(EmptyData):
        s.get_history("FPT", Interval.D1, *WIDE)


def test_status_unknown_raises_invalid(synth):
    # Issue #39: any UDF status other than "ok" must be treated as bad data.
    s = src_with(synth.bare(status="unexpected"))
    with pytest.raises(InvalidData):
        s.get_history("FPT", Interval.D1, *WIDE)


def test_status_missing_raises_invalid(synth):
    # Issue #39: a missing `s` field must NOT be silently accepted as success.
    payload = json.dumps(
        {"t": [synth.ts("2024-01-02")], "o": [72.0], "h": [72.5], "l": [71.8], "c": [72.0], "v": [1000]}
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_empty_arrays_raise_empty(synth):
    s = src_with(synth.bare(rows=[]))
    with pytest.raises(EmptyData):
        s.get_history("FPT", Interval.D1, *WIDE)


def test_misaligned_arrays_raise_invalid():
    payload = json.dumps({"s": "ok", "t": [1, 2, 3], "o": [1, 2], "h": [1], "l": [1], "c": [1], "v": [1]})
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


# --- Issue #55: empty volume array is malformed, not a clean zero-volume bar -----

def test_empty_volume_array_raises_invalid(synth):
    payload = json.dumps(
        {
            "s": "ok",
            "t": [synth.ts("2024-01-02")],
            "o": [72.0],
            "h": [73.0],
            "l": [71.0],
            "c": [72.0],
            "v": [],
        }
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_missing_volume_array_defaults_to_zero(synth):
    # A missing 'v' field is an intentional provider shortcut (no volume data).
    payload = json.dumps(
        {
            "s": "ok",
            "t": [synth.ts("2024-01-02")],
            "o": [72.0],
            "h": [73.0],
            "l": [71.0],
            "c": [72.0],
        }
    )
    h = src_with(payload).get_history("FPT", Interval.D1, *WIDE)
    assert h.bars[0].volume == 0


def test_ohlc_invariant_violation_quarantined_lone_row_empty(synth):
    # #186: low (99) > high (72.5) is a per-row value-quality failure → the row is
    # quarantined (dropped), never served. A lone bad row leaves zero bars → EmptyData
    # (a SourceError → failover-safe). Keep-the-rest is covered in test_quarantine_bad_bars.py.
    bad = [("2024-01-02", 72.0, 72.5, 99.0, 72.3, 1000)]
    with pytest.raises(EmptyData):
        src_with(synth.bare(rows=bad)).get_history("FPT", Interval.D1, *WIDE)


def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        src_with("<html>nope</html>").get_history("FPT", Interval.D1, *WIDE)


def test_unsupported_interval_raises(synth):
    with pytest.raises(UnsupportedInterval):
        src_with(synth.bare()).get_history("FPT", Interval.H1, *WIDE)


def test_transport_error_wrapped(synth):
    s = DummyBare(http_get=synth.raising_get(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.get_history("FPT", Interval.D1, *WIDE)


def test_envelope_unwrap(synth):
    s = DummyEnvelope(http_get=lambda url, params, headers: synth.env())
    h = s.get_history("FPT", Interval.D1, *WIDE)
    assert len(h) == 3
    assert h.source == "dummy_env"


# --- P1: malformed scalars stay failover-safe (a SourceError), never a raw exception.
# Under #186 a lone bad row is quarantined (dropped) → zero bars → EmptyData (still a
# SourceError, so failover behaviour is unchanged). Keep-the-rest + the warning are
# covered in test_quarantine_bad_bars.py. ---


def test_none_close_quarantined_lone_row_empty(synth):
    payload = json.dumps(
        {"s": "ok", "t": [synth.ts("2024-01-02")], "o": [72.0], "h": [72.5], "l": [71.8], "c": [None], "v": [1000]}
    )
    with pytest.raises(EmptyData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_garbage_timestamp_quarantined_lone_row_empty():
    payload = json.dumps(
        {"s": "ok", "t": ["not-a-ts"], "o": [72.0], "h": [72.5], "l": [71.8], "c": [72.0], "v": [1000]}
    )
    with pytest.raises(EmptyData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_nan_price_quarantined_lone_row_empty(synth):
    # json.loads parses bare NaN by default -> float('nan'); the malformed scalar is
    # quarantined at parse. A lone bad row leaves zero bars → EmptyData.
    payload = '{"s":"ok","t":[%d],"o":[72.0],"h":[72.5],"l":[71.8],"c":[NaN],"v":[1000]}' % synth.ts("2024-01-02")
    with pytest.raises(EmptyData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_negative_volume_quarantined_lone_row_empty(synth):
    bad = [("2024-01-02", 72.0, 72.5, 71.8, 72.3, -5)]
    with pytest.raises(EmptyData):
        src_with(synth.bare(rows=bad)).get_history("FPT", Interval.D1, *WIDE)


def test_fractional_volume_quarantined_lone_row_empty(synth):
    # Issue #120: equity/index UDF volume must be a whole number after VOLUME_SCALE. A
    # fractional volume is provider/parse drift; under #186 the row is quarantined (never
    # silently rounded via int(round(...))). A lone bad row leaves zero bars → EmptyData.
    bad = [("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1000.5)]
    with pytest.raises(EmptyData):
        src_with(synth.bare(rows=bad)).get_history("FPT", Interval.D1, *WIDE)


def test_whole_float_volume_accepted(synth):
    rows = [("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1000.0)]
    hist = src_with(synth.bare(rows=rows)).get_history("FPT", Interval.D1, *WIDE)
    assert hist.bars[0].volume == 1000


def test_duplicate_observation_timestamp_quarantined_lone_pair_empty(synth):
    # Issue #66 + #186: two rows sharing one observation timestamp are conflicting provider
    # data; we never silently pick one. Under #186 the timestamp is dropped ENTIRELY (both
    # rows quarantined) instead of raising on sight. A lone conflicting pair leaves zero
    # bars → EmptyData (a SourceError → failover-safe). See test_quarantine_bad_bars.py for
    # the keep-the-rest + warning behaviour.
    rows = [
        ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1000),
        ("2024-01-02", 73.0, 74.0, 72.0, 73.5, 2000),
    ]
    with pytest.raises(EmptyData):
        src_with(synth.bare(rows=rows)).get_history("FPT", Interval.D1, *WIDE)


def test_equity_identical_duplicate_timestamp_quarantined_lone_pair_empty(synth):
    # Issue #162 must NOT leak into equity: the index dedupe-identical opt-in is gated by
    # _DEDUPE_IDENTICAL_DUPLICATE_BARS (default False). With it off, an equity adapter has
    # NO identical-dedupe symmetry — even an identical duplicate timestamp is treated as a
    # duplicate observation and the timestamp is dropped (#186 quarantine), never served as
    # an ambiguous duplicate-keyed bar. A lone identical pair → zero bars → EmptyData.
    rows = [
        ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1000),
        ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1000),  # identical duplicate
    ]
    assert DummyBare._DEDUPE_IDENTICAL_DUPLICATE_BARS is False
    with pytest.raises(EmptyData):
        src_with(synth.bare(rows=rows)).get_history("FPT", Interval.D1, *WIDE)


def test_missing_array_raises_invalid(synth):
    payload = json.dumps(
        {"s": "ok", "t": [synth.ts("2024-01-02")], "o": [72.0], "h": [72.5], "l": [71.8], "v": [1000]}
    )  # no 'c'
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


# --- Reviewer blockers: malformed UDF shapes must raise InvalidData, never raw ---

@pytest.mark.parametrize("bad_top", ["[]", '"x"', "123"])
def test_non_object_top_level_raises_invalid(bad_top):
    with pytest.raises(InvalidData):
        src_with(bad_top).get_history("FPT", Interval.D1, *WIDE)


def test_null_t_array_raises_invalid(synth):
    payload = json.dumps(
        {"s": "ok", "t": None, "o": [72.0], "h": [73.0], "l": [71.0], "c": [72.0], "v": [1000]}
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_scalar_t_array_raises_invalid(synth):
    payload = json.dumps(
        {"s": "ok", "t": 42, "o": [72.0], "h": [73.0], "l": [71.0], "c": [72.0], "v": [1000]}
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_scalar_volume_array_raises_invalid(synth):
    payload = json.dumps(
        {"s": "ok", "t": [synth.ts("2024-01-02")], "o": [72.0], "h": [73.0], "l": [71.0], "c": [72.0], "v": 1000}
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_envelope_missing_data_raises_invalid(synth):
    # DummyEnvelope._extract does parsed["data"]; a missing 'data' key must be
    # converted to InvalidData instead of leaking KeyError.
    payload = json.dumps(
        {"s": "ok", "t": [synth.ts("2024-01-02")], "o": [72.0], "h": [73.0], "l": [71.0], "c": [72.0], "v": [1000]}
    )
    with pytest.raises(InvalidData):
        DummyEnvelope(http_get=lambda url, params, headers: payload).get_history(
            "FPT", Interval.D1, *WIDE
        )


def test_naive_datetime_input_accepted(synth):
    from datetime import datetime

    h = src_with(synth.bare()).get_history(
        "FPT", Interval.D1, datetime(2024, 1, 1), datetime(2024, 1, 31)
    )
    assert len(h) == 3


# --- Issue #21: adapters must validate response identity before stamping identifiers

def test_response_symbol_mismatch_raises_invalid(synth):
    # The UDF payload claims the data is for "OTHER" but we requested "FPT".
    payload = json.dumps(
        {
            "symbol": "OTHER",
            "s": "ok",
            "t": [synth.ts("2024-01-02")],
            "o": [72.0],
            "h": [73.0],
            "l": [71.0],
            "c": [72.0],
            "v": [1000],
        }
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


# --- Issue #13: price parsers must reject zero-valued market observations (never serve them)

@pytest.mark.parametrize("zero_field", ["o", "h", "l", "c"])
def test_zero_price_quarantined_lone_row_empty(synth, zero_field):
    # #186: a non-positive price is a per-row value-quality failure → the row is
    # quarantined (dropped), never served. A lone bad row leaves zero bars → EmptyData.
    row = {"t": [synth.ts("2024-01-02")], "o": [72.0], "h": [73.0], "l": [71.0], "c": [72.0], "v": [1000]}
    row[zero_field] = [0.0]
    payload = json.dumps({"s": "ok", **row})
    with pytest.raises(EmptyData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_zero_volume_is_allowed(synth):
    # Volume can legitimately be zero; only prices must be positive.
    payload = json.dumps(
        {
            "s": "ok",
            "t": [synth.ts("2024-01-02")],
            "o": [72.0],
            "h": [73.0],
            "l": [71.0],
            "c": [72.0],
            "v": [0],
        }
    )
    h = src_with(payload).get_history("FPT", Interval.D1, *WIDE)
    assert h.bars[0].volume == 0


# --- Issue #21 (reopen): a PRESENT blank/null symbol must not bypass the guard
@pytest.mark.parametrize("bad_sym", ["", "   ", None], ids=["blank", "whitespace", "null"])
def test_udf_present_blank_or_null_symbol_raises_invalid(synth, bad_sym):
    payload = json.dumps(
        {
            "symbol": bad_sym,
            "s": "ok",
            "t": [synth.ts("2024-01-02")],
            "o": [72.0], "h": [73.0], "l": [71.0], "c": [72.0], "v": [1000],
        }
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_udf_absent_symbol_key_is_accepted(synth):
    # No 'symbol' key at all -> legacy absent-is-ok behaviour preserved.
    payload = json.dumps(
        {
            "s": "ok",
            "t": [synth.ts("2024-01-02")],
            "o": [72.0], "h": [73.0], "l": [71.0], "c": [72.0], "v": [1000],
        }
    )
    h = src_with(payload).get_history("FPT", Interval.D1, *WIDE)
    assert h.symbol == "FPT"
