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


def test_ohlc_invariant_violation_raises_invalid(synth):
    # low (99) > high (72.5) -> invalid
    bad = [("2024-01-02", 72.0, 72.5, 99.0, 72.3, 1000)]
    with pytest.raises(InvalidData):
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


# --- P1: malformed scalars must raise InvalidData (failover-safe), not raw exceptions ---


def test_none_close_raises_invalid(synth):
    payload = json.dumps(
        {"s": "ok", "t": [synth.ts("2024-01-02")], "o": [72.0], "h": [72.5], "l": [71.8], "c": [None], "v": [1000]}
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_garbage_timestamp_raises_invalid():
    payload = json.dumps(
        {"s": "ok", "t": ["not-a-ts"], "o": [72.0], "h": [72.5], "l": [71.8], "c": [72.0], "v": [1000]}
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_nan_price_raises_invalid(synth):
    # json.loads parses bare NaN by default -> float('nan') -> non-finite guard
    payload = '{"s":"ok","t":[%d],"o":[72.0],"h":[72.5],"l":[71.8],"c":[NaN],"v":[1000]}' % synth.ts("2024-01-02")
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


def test_negative_volume_raises_invalid(synth):
    bad = [("2024-01-02", 72.0, 72.5, 71.8, 72.3, -5)]
    with pytest.raises(InvalidData):
        src_with(synth.bare(rows=bad)).get_history("FPT", Interval.D1, *WIDE)


def test_missing_array_raises_invalid(synth):
    payload = json.dumps(
        {"s": "ok", "t": [synth.ts("2024-01-02")], "o": [72.0], "h": [72.5], "l": [71.8], "v": [1000]}
    )  # no 'c'
    with pytest.raises(InvalidData):
        src_with(payload).get_history("FPT", Interval.D1, *WIDE)


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


# --- Issue #13: price parsers must reject zero-valued market observations

@pytest.mark.parametrize("zero_field", ["o", "h", "l", "c"])
def test_zero_price_rejected_as_invalid(synth, zero_field):
    row = {"t": [synth.ts("2024-01-02")], "o": [72.0], "h": [73.0], "l": [71.0], "c": [72.0], "v": [1000]}
    row[zero_field] = [0.0]
    payload = json.dumps({"s": "ok", **row})
    with pytest.raises(InvalidData):
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
