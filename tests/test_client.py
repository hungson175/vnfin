from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.client import FailoverPriceClient
from vnfin.exceptions import AllSourcesFailed, EmptyData, SourceUnavailable
from vnfin.models import Interval, PriceBar, PriceHistory
from vnfin.sources.base import PriceSource

WIDE = (date(2024, 1, 1), date(2024, 1, 31))


class FakeSource(PriceSource):
    def __init__(self, name, result, supported=(Interval.D1,)):
        self._name = name
        self._result = result  # a PriceHistory or an Exception to raise
        self._supported = set(supported)
        self.calls = 0

    @property
    def name(self):
        return self._name

    def supports(self, interval):
        return interval in self._supported

    def get_history(self, symbol, interval, start, end):
        self.calls += 1
        if isinstance(self._result, Exception):
            raise self._result
        # Synthetic helpers may hard-code a symbol; ensure the fake behaves like a
        # real source and returns the requested public symbol so identity checks
        # do not reject otherwise-valid synthetic results.
        if hasattr(self._result, "symbol") and self._result.symbol != symbol:
            from dataclasses import replace

            return replace(self._result, symbol=symbol)
        return self._result


class RawFakeSource(PriceSource):
    """Like FakeSource but does NOT patch the returned symbol.

    Used for tests that intentionally want a wrong-identity result.
    """

    def __init__(self, name, result, supported=(Interval.D1,)):
        self._name = name
        self._result = result
        self._supported = set(supported)
        self.calls = 0

    @property
    def name(self):
        return self._name

    def supports(self, interval):
        return interval in self._supported

    def get_history(self, symbol, interval, start, end):
        self.calls += 1
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def test_failover_to_second_source(synth):
    s1 = FakeSource("s1", SourceUnavailable("down"))
    s2 = FakeSource("s2", synth.make_history("s2", 2))
    client = FailoverPriceClient([s1, s2])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "s2"
    assert len(h) == 2
    assert s1.calls == 1 and s2.calls == 1
    assert [a.ok for a in h.attempts] == [False, True]


def test_stops_after_first_valid_source(synth):
    s1 = FakeSource("s1", synth.make_history("s1", 2))
    s2 = FakeSource("s2", synth.make_history("s2", 2))
    client = FailoverPriceClient([s1, s2])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "s1"
    assert s2.calls == 0
    assert len(h.attempts) == 1 and h.attempts[0].ok is True


def test_at_most_three_attempts():
    sources = [FakeSource(f"s{i}", SourceUnavailable("x")) for i in range(5)]
    client = FailoverPriceClient(sources, max_attempts=3)
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_daily("FPT", *WIDE)
    assert len(ei.value.attempts) == 3
    assert [s.calls for s in sources] == [1, 1, 1, 0, 0]


def test_incapable_source_skipped_without_call(synth):
    s1 = FakeSource("s1", synth.make_history("s1", 2), supported=(Interval.H1,))  # no daily
    s2 = FakeSource("s2", synth.make_history("s2", 2))
    client = FailoverPriceClient([s1, s2])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "s2"
    assert s1.calls == 0
    assert len(h.attempts) == 1  # s1 never counted as an attempt


def test_empty_result_falls_through(synth):
    s1 = FakeSource("s1", synth.make_history("s1", 0))  # empty
    s2 = FakeSource("s2", synth.make_history("s2", 2))
    client = FailoverPriceClient([s1, s2])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "s2"
    assert s1.calls == 1
    assert h.attempts[0].ok is False and "empty" in h.attempts[0].reason


def test_no_capable_source_raises_unsupported(synth):
    from vnfin.exceptions import UnsupportedInterval

    s = FakeSource("s1", synth.make_history("s1", 2), supported=(Interval.H1,))
    client = FailoverPriceClient([s])
    with pytest.raises(UnsupportedInterval):
        client.get_daily("FPT", *WIDE)
    assert s.calls == 0


def test_partial_end_coverage_warning(synth):
    # bars end 2024-01-04; requested end 2024-01-31 -> >7d -> soft warning
    s = FakeSource("s1", synth.make_history("s1", 3))
    client = FailoverPriceClient([s])
    h = client.get_daily("FPT", date(2024, 1, 1), date(2024, 1, 31))
    assert h.source == "s1"
    assert any("partial_end_coverage" in w for w in h.warnings)


def test_full_coverage_no_warning(synth):
    s = FakeSource("s1", synth.make_history("s1", 3))
    client = FailoverPriceClient([s])
    h = client.get_daily("FPT", date(2024, 1, 1), date(2024, 1, 5))
    assert h.warnings == ()


def test_partial_start_coverage_warning_with_datetime_inputs(synth):
    from datetime import datetime

    s = FakeSource("s1", synth.make_history("s1", 3))  # bars 2024-01-02..04
    client = FailoverPriceClient([s])
    h = client.get_history("FPT", Interval.D1, datetime(2023, 11, 1), datetime(2024, 1, 4))
    assert any("partial_start_coverage" in w for w in h.warnings)


def test_rejects_history_entirely_outside_requested_range(synth):
    # Issue #84: non-empty series with zero bars in the window is a source miss.
    from datetime import datetime, timezone

    from vnfin.models import AdjustmentPolicy, PriceBar, PriceHistory

    oor = PriceHistory(
        symbol="FPT",
        interval=Interval.D1,
        adjustment_policy=AdjustmentPolicy.PROVIDER_ADJUSTED,
        source="oor",
        bars=(
            PriceBar(datetime(2030, 1, 1, tzinfo=timezone.utc), 1.0, 1.0, 1.0, 1.0, 1),
        ),
        currency="VND",
        value_unit="VND",
    )
    s1 = FakeSource("oor", oor)
    s2 = FakeSource("good", _history_through("good", date(2025, 1, 2), n=2))
    h = FailoverPriceClient([s1, s2]).get_daily("FPT", date(2025, 1, 1), date(2025, 1, 3))
    assert h.source == "good"
    assert s1.calls == 1 and s2.calls == 1

    with pytest.raises(AllSourcesFailed):
        FailoverPriceClient([FakeSource("oor", oor)]).get_daily(
            "FPT", date(2025, 1, 1), date(2025, 1, 3)
        )


def _history_through(source, last_day, n=3):
    """Synthetic daily PriceHistory whose final bar lands exactly on ``last_day``.

    Obviously-fake symbol + fabricated OHLCV; no real provider rows.
    """
    from datetime import datetime, timedelta, timezone

    from vnfin.models import AdjustmentPolicy, PriceBar, PriceHistory

    days = [last_day - timedelta(days=n - 1 - i) for i in range(n)]
    bars = tuple(
        PriceBar(
            time=datetime(d.year, d.month, d.day, tzinfo=timezone.utc),
            open=72.0,
            high=73.0,
            low=71.0,
            close=72.5,
            volume=1000 + i,
        )
        for i, d in enumerate(days)
    )
    return PriceHistory(
        symbol="ZZZFAKE",
        interval=Interval.D1,
        adjustment_policy=AdjustmentPolicy.PROVIDER_ADJUSTED,
        source=source,
        bars=bars,
        exchange="HOSE",
        provider_symbol="ZZZFAKE",
    )


def test_no_false_staleness_over_weekend():
    # Last bar Fri 2024-01-05; request ends Sun 2024-01-07 (weekend).
    # The market did not trade Sat/Sun, so the series is NOT stale -> no warning.
    from datetime import date

    s = FakeSource("s1", _history_through("s1", date(2024, 1, 5)))
    client = FailoverPriceClient([s])
    h = client.get_daily("ZZZFAKE", date(2023, 12, 1), date(2024, 1, 7))
    assert not any("partial_end_coverage" in w for w in h.warnings)


def test_no_false_staleness_over_holiday_block():
    # Last bar Fri 2023-12-29; request ends Mon 2024-01-01 (New Year holiday).
    # Latest expected trading day is 2023-12-29, which the series already has.
    # Even though the raw gap could look large, there is no staleness.
    from datetime import date

    s = FakeSource("s1", _history_through("s1", date(2023, 12, 29)))
    client = FailoverPriceClient([s])
    h = client.get_daily("ZZZFAKE", date(2023, 12, 1), date(2024, 1, 1))
    assert not any("partial_end_coverage" in w for w in h.warnings)


def test_no_false_staleness_over_long_tet_break():
    # 2024 Tet weekday closures span Feb 8-14 (plus the weekend Feb 10-11).
    # Last bar is the last pre-Tet trading day (Wed 2024-02-07); request ends on the
    # last Tet holiday (Wed 2024-02-14). The >7d raw gap would have falsely warned
    # under the old day-gap-only rule; the calendar suppresses it.
    from datetime import date

    s = FakeSource("s1", _history_through("s1", date(2024, 2, 7)))
    client = FailoverPriceClient([s])
    h = client.get_daily("ZZZFAKE", date(2024, 1, 1), date(2024, 2, 14))
    assert not any("partial_end_coverage" in w for w in h.warnings)


def test_genuine_staleness_still_warns():
    # Last bar 2024-01-04 but request ends a full month later on a normal trading day
    # (Wed 2024-01-31). Latest expected trading day is 2024-01-31; the series is behind
    # it by far more than the tolerance -> the staleness warning still fires.
    from datetime import date

    s = FakeSource("s1", _history_through("s1", date(2024, 1, 4)))
    client = FailoverPriceClient([s])
    h = client.get_daily("ZZZFAKE", date(2024, 1, 1), date(2024, 1, 31))
    assert any("partial_end_coverage" in w for w in h.warnings)


def _unit_source(name, unit, synth):
    s = FakeSource(name, synth.make_history(name, 2))
    s.unit = unit
    return s


def test_price_client_rejects_mixed_units(synth):
    from vnfin.exceptions import UnitMismatchError

    vnd = _unit_source("equity", "VND", synth)
    pts = _unit_source("index", "points", synth)
    with pytest.raises(UnitMismatchError):
        FailoverPriceClient([vnd, pts])


def test_price_client_allows_homogeneous_units(synth):
    a = _unit_source("a", "VND", synth)
    b = _unit_source("b", "VND", synth)
    client = FailoverPriceClient([a, b])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "a"


def test_default_index_chain_is_homogeneous_points():
    # The shipped index chain must construct cleanly (all sources declare "points").
    from vnfin.indices.client import default_index_sources

    client = FailoverPriceClient(default_index_sources())
    assert {s.unit for s in client.sources} == {"points"}


def test_default_equity_chain_is_homogeneous_vnd():
    from vnfin.sources.registry import default_sources

    client = FailoverPriceClient(default_sources())
    assert {s.unit for s in client.sources} == {"VND"}


# --- B5: REQUIRE-DATES contract -------------------------------------------- #
# start/end are required and validated BEFORE any source call. Missing/invalid
# dates raise a stable VnfinError (InvalidData), never a raw TypeError, and never
# burn a failover attempt.


def test_get_history_without_dates_raises_vnfin_error_not_typeerror(synth):
    from vnfin.exceptions import InvalidData, VnfinError

    s = FakeSource("s1", synth.make_history("s1", 2))
    client = FailoverPriceClient([s])
    with pytest.raises(VnfinError) as ei:
        client.get_history("FAKECO")  # no start/end
    assert isinstance(ei.value, InvalidData)
    assert not isinstance(ei.value, TypeError)
    assert s.calls == 0  # validated up front, no source call / failover attempt


def test_default_client_get_history_without_dates_raises_vnfin_error():
    import vnfin
    from vnfin.exceptions import VnfinError

    with pytest.raises(VnfinError):
        vnfin.default_client().get_history("FAKECO")  # no start/end


def test_prices_history_facade_without_dates_raises_vnfin_error():
    import vnfin
    from vnfin.exceptions import VnfinError

    with pytest.raises(VnfinError):
        # http_get injected so we never touch the network; validation fires first.
        vnfin.prices.history("FAKECO", http_get=lambda url, params, headers: "{}")


def test_get_history_with_only_start_raises_vnfin_error(synth):
    from vnfin.exceptions import InvalidData

    s = FakeSource("s1", synth.make_history("s1", 2))
    client = FailoverPriceClient([s])
    with pytest.raises(InvalidData):
        client.get_history("FAKECO", Interval.D1, date(2024, 1, 1), None)
    assert s.calls == 0


def test_get_history_with_inverted_range_raises_vnfin_error(synth):
    from vnfin.exceptions import InvalidData

    s = FakeSource("s1", synth.make_history("s1", 2))
    client = FailoverPriceClient([s])
    with pytest.raises(InvalidData):
        client.get_history("FAKECO", Interval.D1, date(2024, 1, 31), date(2024, 1, 1))
    assert s.calls == 0


def test_get_daily_without_dates_raises_vnfin_error(synth):
    from vnfin.exceptions import InvalidData

    s = FakeSource("s1", synth.make_history("s1", 2))
    client = FailoverPriceClient([s])
    with pytest.raises(InvalidData):
        client.get_daily("FAKECO", None, None)
    assert s.calls == 0


# --- Issue #23: invalid interval type must not leak AttributeError in failover path

def test_invalid_interval_type_raises_vnfin_error_not_attributeerror(synth):
    from vnfin.exceptions import InvalidData, VnfinError

    s = FakeSource("s1", synth.make_history("s1", 2))
    client = FailoverPriceClient([s])
    with pytest.raises(VnfinError) as ei:
        client.get_history("FAKECO", "D1", date(2024, 1, 1), date(2024, 1, 31))
    assert isinstance(ei.value, InvalidData)
    assert not isinstance(ei.value, AttributeError)
    assert s.calls == 0  # rejected before any source call


# --- Issue #7: price failover must guard against mixed adjustment policies

def test_price_client_rejects_mixed_adjustment_policies(synth):
    from vnfin.exceptions import VnfinError
    from vnfin.models import AdjustmentPolicy

    adj = FakeSource("adj", synth.make_history("adj", 2))
    adj.adjustment_policy = AdjustmentPolicy.PROVIDER_ADJUSTED
    raw = FakeSource("raw", synth.make_history("raw", 2))
    raw.adjustment_policy = AdjustmentPolicy.RAW
    with pytest.raises(VnfinError):
        FailoverPriceClient([adj, raw])


def test_price_client_allows_homogeneous_adjustment_policies(synth):
    from vnfin.models import AdjustmentPolicy

    a = FakeSource("a", synth.make_history("a", 2))
    a.adjustment_policy = AdjustmentPolicy.PROVIDER_ADJUSTED
    b = FakeSource("b", synth.make_history("b", 2))
    b.adjustment_policy = AdjustmentPolicy.PROVIDER_ADJUSTED
    client = FailoverPriceClient([a, b])
    h = client.get_daily("FAKECO", *WIDE)
    assert h.source == "a"


def test_price_client_accepts_generator_without_exhausting_it(synth):
    from vnfin.models import AdjustmentPolicy

    a = FakeSource("a", synth.make_history("a", 2))
    a.adjustment_policy = AdjustmentPolicy.PROVIDER_ADJUSTED
    client = FailoverPriceClient(iter([a]))
    h = client.get_daily("FAKECO", *WIDE)
    assert h.source == "a"
    assert len(client.sources) == 1


# --- Issue #9: empty/malformed symbols must be rejected before failover -----------


@pytest.mark.parametrize("bad_symbol", ["", "   ", "\t", None, 123])
def test_get_history_rejects_empty_symbol_before_source_call(synth, bad_symbol):
    from vnfin.exceptions import InvalidData

    s = FakeSource("s1", synth.make_history("s1", 2))
    client = FailoverPriceClient([s])
    with pytest.raises(InvalidData):
        client.get_history(bad_symbol, Interval.D1, *WIDE)
    assert s.calls == 0


# --- Batch-1 result guards: identity, metadata, OHLC invariants, sorting ----------


def _history_with_bars(source, symbol, bars, **kwargs):
    from vnfin.models import AdjustmentPolicy, PriceHistory

    defaults = dict(
        symbol=symbol,
        interval=Interval.D1,
        adjustment_policy=AdjustmentPolicy.PROVIDER_ADJUSTED,
        source=source,
        currency="VND",
        value_unit="VND",
    )
    defaults.update(kwargs)
    return PriceHistory(bars=bars, **defaults)


def _make_bad_history(**kwargs):
    from datetime import datetime, timezone
    from vnfin.models import AdjustmentPolicy

    defaults = dict(
        symbol="FPT",
        interval=Interval.D1,
        adjustment_policy=AdjustmentPolicy.PROVIDER_ADJUSTED,
        source="bad",
        bars=(PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 72, 73, 71, 72.5, 1000),),
        currency="VND",
        value_unit="VND",
    )
    defaults.update(kwargs)
    return PriceHistory(**defaults)


def test_rejects_returned_symbol_mismatch(synth):
    bad = _make_bad_history(symbol="OTHER")
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("bad", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert h.attempts[0].ok is False and "symbol mismatch" in h.attempts[0].reason


def test_lowercase_symbol_accepted_when_source_returns_uppercase():
    # Regression: real sources normalize to uppercase; the failover client must not
    # reject a valid result just because the caller passed a lowercase selector.
    bars = (PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10.5, 1000),)
    upper = _history_with_bars("upper", "VNM", bars)
    client = FailoverPriceClient([RawFakeSource("upper", upper)])
    h = client.get_daily("vnm", *WIDE)
    assert h.symbol == "VNM"
    assert h.source == "upper"


def test_rejects_returned_interval_mismatch(synth):
    bad = _make_bad_history(interval=Interval.W1)
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("bad", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert h.attempts[0].ok is False and "interval mismatch" in h.attempts[0].reason


def test_rejects_returned_unit_mismatch(synth):
    bad = _make_bad_history(currency="USD", value_unit="USD")
    good = FakeSource("good", synth.make_history("good", 2))
    good.unit = "VND"
    bad_src = RawFakeSource("bad", bad)
    bad_src.unit = "VND"
    client = FailoverPriceClient([bad_src, good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert h.attempts[0].ok is False and "currency mismatch" in h.attempts[0].reason


def test_rejects_returned_adjustment_policy_mismatch(synth):
    from vnfin.models import AdjustmentPolicy

    bad = _make_bad_history(adjustment_policy=AdjustmentPolicy.RAW)
    good = FakeSource("good", synth.make_history("good", 2))
    good.adjustment_policy = AdjustmentPolicy.PROVIDER_ADJUSTED
    bad_src = RawFakeSource("bad", bad)
    bad_src.adjustment_policy = AdjustmentPolicy.PROVIDER_ADJUSTED
    client = FailoverPriceClient([bad_src, good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert "adjustment_policy mismatch" in h.attempts[0].reason


def test_rejects_unsorted_bars(synth):
    from datetime import datetime, timezone

    bars = (
        PriceBar(datetime(2024, 1, 3, tzinfo=timezone.utc), 73, 73, 73, 73, 1000),
        PriceBar(datetime(2024, 1, 1, tzinfo=timezone.utc), 71, 71, 71, 71, 1000),
    )
    bad = _history_with_bars("bad", "FPT", bars)
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("bad", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert "not strictly ascending" in h.attempts[0].reason


@pytest.mark.parametrize(
    "bar_factory,expected_substring",
    [
        (
            lambda t: PriceBar(t, 100, 90, 110, 95, 1000),
            "open 100 not in [low 110, high 90]",
        ),
        (
            lambda t: PriceBar(t, 100, 110, 90, 95, -5),
            "volume must be non-negative",
        ),
        (
            lambda t: PriceBar(t, -1, 1, -2, 0, 1000),
            "open must be positive",
        ),
    ],
)
def test_rejects_economically_impossible_bars(synth, bar_factory, expected_substring):
    from datetime import datetime, timezone

    t = datetime(2024, 1, 2, tzinfo=timezone.utc)
    bad = _history_with_bars("bad", "FPT", (bar_factory(t),))
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("bad", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert expected_substring in h.attempts[0].reason


# --------------------------------------------------------------------------- #
# Issue #125 — malformed (non-typed) result containers must be recorded as a
# rejected source attempt (failover continues / clean AllSourcesFailed), never
# leak a raw AttributeError from the result guard.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "bad",
    [{}, None, [], 42, "history", object()],
    ids=["dict", "none", "list", "int", "str", "object"],
)
def test_rejects_malformed_result_container_and_failsover(bad, synth):
    s1 = RawFakeSource("s1", bad)
    s2 = FakeSource("s2", synth.make_history("s2", 2))
    client = FailoverPriceClient([s1, s2])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "s2"
    assert s1.calls == 1 and s2.calls == 1
    assert h.attempts[0].ok is False
    assert "unexpected result type" in h.attempts[0].reason


def test_all_malformed_containers_raise_clean_failure():
    client = FailoverPriceClient([RawFakeSource("s1", {}), RawFakeSource("s2", None)])
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_daily("FPT", *WIDE)
    assert all("unexpected result type" in a.reason for a in ei.value.attempts)


# --------------------------------------------------------------------------- #
# Issue #124 — PriceBar.time must be a timezone-AWARE datetime. Naive datetimes
# and non-datetime keys must be rejected before sort/window logic, never leak a
# raw TypeError/AttributeError.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "bad_time",
    [
        datetime(2024, 1, 2),  # naive
        date(2024, 1, 2),      # date, not datetime
        "2024-01-02",          # string
        None,
        1704153600,            # epoch int
    ],
    ids=["naive_datetime", "date", "str", "none", "int"],
)
def test_rejects_malformed_price_bar_time(bad_time):
    bad = _history_with_bars("bad", "FPT", (PriceBar(bad_time, 10, 11, 9, 10.5, 1000),))
    client = FailoverPriceClient([RawFakeSource("bad", bad)])
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_daily("FPT", *WIDE)
    assert "malformed bar time" in ei.value.attempts[0].reason


def test_malformed_price_bar_time_failsover_to_backup(synth):
    bad = _history_with_bars("bad", "FPT", (PriceBar(datetime(2024, 1, 2), 10, 11, 9, 10.5, 1000),))
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("bad", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert "malformed bar time" in h.attempts[0].reason


# --------------------------------------------------------------------------- #
# Issue #126 — a result whose stamped .source does not match the source that
# produced it is a provenance violation: rejected (never relabelled), failover
# continues, audit/backtest can trust result.source.
# --------------------------------------------------------------------------- #
def test_rejects_provenance_mismatch_and_failsover(synth):
    t = datetime(2024, 1, 2, tzinfo=timezone.utc)
    # Source named "real" returns a history stamped as another provider.
    bad = _history_with_bars("claimed_backup", "FPT", (PriceBar(t, 10, 11, 9, 10.5, 1000),))
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("real", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert "provenance mismatch" in h.attempts[0].reason


def test_provenance_match_is_accepted():
    bars = (PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10.5, 1000),)
    hist = _history_with_bars("real", "FPT", bars)
    client = FailoverPriceClient([RawFakeSource("real", hist)])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "real"


@pytest.mark.parametrize(
    "bad_source",
    [None, ["real"], ("real",), {"real"}, 123],
    ids=["none", "list", "tuple", "set", "int"],
)
def test_rejects_malformed_or_missing_price_provenance(bad_source, synth):
    # #126 B2: a single-result source must be a plain matching string. None,
    # collections (even containing the right name), and non-strings are rejected.
    t = datetime(2024, 1, 2, tzinfo=timezone.utc)
    bad = _history_with_bars(bad_source, "FPT", (PriceBar(t, 10, 11, 9, 10.5, 1000),))
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("real", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"


def test_single_source_malformed_price_provenance_raises():
    t = datetime(2024, 1, 2, tzinfo=timezone.utc)
    bad = _history_with_bars(None, "FPT", (PriceBar(t, 10, 11, 9, 10.5, 1000),))
    client = FailoverPriceClient([RawFakeSource("real", bad)])
    with pytest.raises(AllSourcesFailed):
        client.get_daily("FPT", *WIDE)


# --------------------------------------------------------------------------- #
# Issue #125 (reopen) — a malformed inner row object inside an otherwise typed
# container must be rejected before deref, not leak a raw AttributeError.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad_row", [object(), None, {}, "bar", 42], ids=["object", "none", "dict", "str", "int"])
def test_rejects_malformed_price_bar_object(bad_row):
    bad = _history_with_bars("real", "FPT", (bad_row,))
    client = FailoverPriceClient([RawFakeSource("real", bad)])
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_daily("FPT", *WIDE)
    assert "malformed bar object" in ei.value.attempts[0].reason


def test_malformed_price_bar_object_failsover_to_backup(synth):
    bad = _history_with_bars("real", "FPT", (object(),))
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("real", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert "malformed bar object" in h.attempts[0].reason


# --------------------------------------------------------------------------- #
# Issue #127 — present-malformed fetched_at_utc freshness metadata is rejected
# (None stays allowed).
# --------------------------------------------------------------------------- #
_BAD_TS = [
    datetime(2026, 6, 19, 3, 0, 0),  # naive
    datetime(2026, 6, 19, 10, 0, 0, tzinfo=timezone(timedelta(hours=7))),  # non-UTC
    "2026-06-19T03:00:00Z",
    1718766000,
]
_BAD_TS_IDS = ["naive", "non_utc", "str", "int"]


@pytest.mark.parametrize("bad_ts", _BAD_TS, ids=_BAD_TS_IDS)
def test_rejects_malformed_price_fetched_at_utc(bad_ts, synth):
    bars = (PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10.5, 1000),)
    bad = _history_with_bars("real", "FPT", bars, fetched_at_utc=bad_ts)
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("real", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert "fetched_at_utc" in h.attempts[0].reason


def test_accepts_none_price_fetched_at_utc():
    bars = (PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10.5, 1000),)
    hist = _history_with_bars("real", "FPT", bars, fetched_at_utc=None)
    client = FailoverPriceClient([RawFakeSource("real", hist)])
    assert client.get_daily("FPT", *WIDE).source == "real"


# --------------------------------------------------------------------------- #
# Issue #128 — warnings must be tuple[str, ...]; None/list/str/non-str rejected.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "bad_warnings",
    [None, ["w"], "w", (1,), (None,), ("ok", 2)],
    ids=["none", "list", "str", "int_member", "none_member", "mixed_member"],
)
def test_rejects_malformed_price_warnings(bad_warnings, synth):
    bars = (PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10.5, 1000),)
    bad = _history_with_bars("real", "FPT", bars, warnings=bad_warnings)
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("real", bad), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert "warnings" in h.attempts[0].reason


def test_accepts_valid_price_warnings():
    bars = (PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10.5, 1000),)
    hist = _history_with_bars("real", "FPT", bars, warnings=("a soft note",))
    client = FailoverPriceClient([RawFakeSource("real", hist)])
    assert client.get_daily("FPT", *WIDE).source == "real"


# --------------------------------------------------------------------------- #
# Issue #133 — returned price security metadata (exchange / provider_symbol),
# when present, must be a non-empty canonical string.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "field,bad",
    [
        ("exchange", []), ("exchange", {}), ("exchange", True), ("exchange", 123),
        ("exchange", ""), ("exchange", " HOSE"),
        ("provider_symbol", []), ("provider_symbol", {}), ("provider_symbol", True),
        ("provider_symbol", 123), ("provider_symbol", ""), ("provider_symbol", "AAA "),
    ],
    ids=["ex_list", "ex_dict", "ex_bool", "ex_int", "ex_blank", "ex_padded",
         "ps_list", "ps_dict", "ps_bool", "ps_int", "ps_blank", "ps_padded"],
)
def test_rejects_malformed_price_security_metadata(field, bad, synth):
    bars = (PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10.5, 1000),)
    bad_hist = _history_with_bars("real", "FPT", bars, **{field: bad})
    good = FakeSource("good", synth.make_history("good", 2))
    client = FailoverPriceClient([RawFakeSource("real", bad_hist), good])
    h = client.get_daily("FPT", *WIDE)
    assert h.source == "good"
    assert f"malformed {field}" in h.attempts[0].reason


def test_accepts_present_price_security_metadata():
    # Non-empty canonical strings are accepted (no accepted-set/contradiction rule).
    bars = (PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10.5, 1000),)
    hist = _history_with_bars("real", "FPT", bars, exchange="HOSE", provider_symbol="FPT")
    client = FailoverPriceClient([RawFakeSource("real", hist)])
    assert client.get_daily("FPT", *WIDE).source == "real"


def test_accepts_none_price_security_metadata():
    bars = (PriceBar(datetime(2024, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10.5, 1000),)
    hist = _history_with_bars("real", "FPT", bars, exchange=None, provider_symbol=None)
    client = FailoverPriceClient([RawFakeSource("real", hist)])
    assert client.get_daily("FPT", *WIDE).source == "real"
