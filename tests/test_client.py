from datetime import date

import pytest

from vnfin.client import FailoverPriceClient
from vnfin.exceptions import AllSourcesFailed, EmptyData, SourceUnavailable
from vnfin.models import Interval
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
