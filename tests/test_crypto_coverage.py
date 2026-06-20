"""Issue #169: crypto bounded daily history must not silently accept partial coverage.

Option B (reviewer-approved, review-202606201356): failover-first — a source that fully covers
the requested window wins; a partial primary is not accepted as a clean full success (backup gets a
chance); if NO source fully covers, return the BEST-AVAILABLE result + an explicit, exact
``partial_coverage`` warning (never a silent full-success). Best-available = max covered requested-day
overlap, then source order.

All sources here are SYNTHETIC stubs (no network) so coverage scenarios are controlled exactly.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from vnfin.crypto import CryptoHistory, FailoverCryptoClient
from vnfin.crypto.client import (
    _PARTIAL_COVERAGE_WARNING_TEMPLATE,
    _partial_coverage_warning,
)
from vnfin.crypto.models import CryptoBar
from vnfin.exceptions import AllSourcesFailed
from vnfin.models import Interval

UTC = timezone.utc


def _hist(source, days, *, symbol="BTCUSDT", currency="USD", base="BTC", quote="USDT"):
    bars = tuple(
        CryptoBar(datetime(d.year, d.month, d.day, tzinfo=UTC), 100.0, 110.0, 90.0, 105.0, 1.0)
        for d in days
    )
    return CryptoHistory(
        symbol=symbol,
        interval=Interval.D1,
        source=source,
        bars=bars,
        currency=currency,
        value_unit=currency,
        base_asset=base,
        quote_asset=quote,
    )


class _Stub:
    unit = "USD"

    def __init__(self, name, hist=None, exc=None, supports=True):
        self.name = name
        self._hist = hist
        self._exc = exc
        self._supports = supports
        self.calls = 0

    def supports(self, interval):
        return self._supports

    def get_klines(self, symbol, interval, start, end):
        self.calls += 1
        if self._exc is not None:
            raise self._exc
        return self._hist


W_START, W_END = date(2026, 6, 1), date(2026, 6, 30)


# --- warning constant -------------------------------------------------------
def test_partial_coverage_warning_constant_and_format():
    w = _partial_coverage_warning(W_START, W_END, date(2026, 6, 10), date(2026, 6, 12))
    assert w == "partial_coverage: requested 2026-06-01..2026-06-30, returned 2026-06-10..2026-06-12"
    assert "partial_coverage" in _PARTIAL_COVERAGE_WARNING_TEMPLATE
    # all four dates present
    for tok in ("{start}", "{end}", "{first}", "{last}"):
        assert tok in _PARTIAL_COVERAGE_WARNING_TEMPLATE


# --- failover-first ---------------------------------------------------------
def test_partial_primary_full_backup_selects_backup_no_warning():
    primary = _Stub("primary", _hist("primary", [date(2026, 6, 15), date(2026, 6, 16)]))
    backup = _Stub("backup", _hist("backup", [W_START, date(2026, 6, 15), W_END]))  # full
    client = FailoverCryptoClient([primary, backup])
    h = client.get_klines("BTCUSDT", Interval.D1, W_START, W_END)
    assert h.source == "backup"
    assert h.warnings == ()  # full coverage -> no partial warning


def test_full_primary_wins_backup_not_called():
    primary = _Stub("primary", _hist("primary", [W_START, date(2026, 6, 15), W_END]))  # full
    backup = _Stub("backup", _hist("backup", [W_START, W_END]))
    client = FailoverCryptoClient([primary, backup])
    h = client.get_klines("BTCUSDT", Interval.D1, W_START, W_END)
    assert h.source == "primary"
    assert h.warnings == ()
    assert backup.calls == 0  # failover-first: full primary -> backup never called


# --- best-available + exact warning -----------------------------------------
def test_both_partial_best_overlap_selected_with_exact_warning():
    # primary overlap 1; backup overlap 3 -> backup wins (more overlap), neither full.
    primary = _Stub("primary", _hist("primary", [date(2026, 6, 20)]))
    backup = _Stub("backup", _hist("backup", [date(2026, 6, 10), date(2026, 6, 11), date(2026, 6, 12)]))
    client = FailoverCryptoClient([primary, backup])
    h = client.get_klines("BTCUSDT", Interval.D1, W_START, W_END)
    assert h.source == "backup"
    assert h.warnings == (
        "partial_coverage: requested 2026-06-01..2026-06-30, returned 2026-06-10..2026-06-12",
    )


def test_both_partial_overlap_tie_breaks_on_source_order():
    primary = _Stub("primary", _hist("primary", [date(2026, 6, 10)]))
    backup = _Stub("backup", _hist("backup", [date(2026, 6, 20)]))
    client = FailoverCryptoClient([primary, backup])
    h = client.get_klines("BTCUSDT", Interval.D1, W_START, W_END)
    assert h.source == "primary"  # tie on overlap -> earlier source
    assert h.warnings[0].startswith("partial_coverage:")


def test_prefix_gap_partial_warning():
    primary = _Stub("primary", _hist("primary", [date(2026, 6, 15), W_END]))  # first > start
    client = FailoverCryptoClient([primary])
    h = client.get_klines("BTCUSDT", Interval.D1, W_START, W_END)
    assert h.warnings == (
        "partial_coverage: requested 2026-06-01..2026-06-30, returned 2026-06-15..2026-06-30",
    )


def test_suffix_gap_partial_warning():
    primary = _Stub("primary", _hist("primary", [W_START, date(2026, 6, 15)]))  # last < end
    client = FailoverCryptoClient([primary])
    h = client.get_klines("BTCUSDT", Interval.D1, W_START, W_END)
    assert h.warnings == (
        "partial_coverage: requested 2026-06-01..2026-06-30, returned 2026-06-01..2026-06-15",
    )


# --- unbounded unchanged ----------------------------------------------------
def test_unbounded_no_coverage_check_no_warning():
    primary = _Stub("primary", _hist("primary", [date(2026, 6, 15), date(2026, 6, 16)]))
    backup = _Stub("backup", _hist("backup", [W_START, W_END]))
    client = FailoverCryptoClient([primary, backup])
    h = client.get_klines("BTCUSDT", Interval.D1)  # no start/end
    assert h.source == "primary"
    assert h.warnings == ()
    assert backup.calls == 0


# --- hard guards still hard-reject (coverage is separate) -------------------
def test_hard_invalid_unit_still_rejected_then_failover():
    # primary returns a BTC-quoted (non-USD) series -> HARD reject; backup full USD -> selected.
    primary = _Stub("primary", _hist("primary", [W_START, W_END], currency="BTC", quote="BTC"))
    backup = _Stub("backup", _hist("backup", [W_START, date(2026, 6, 15), W_END]))
    client = FailoverCryptoClient([primary, backup])
    h = client.get_klines("BTCUSDT", Interval.D1, W_START, W_END)
    assert h.source == "backup"
    assert h.warnings == ()


def test_all_hard_invalid_raises_all_sources_failed():
    primary = _Stub("primary", _hist("primary", [W_START, W_END], currency="BTC", quote="BTC"))
    client = FailoverCryptoClient([primary])
    with pytest.raises(AllSourcesFailed):
        client.get_klines("BTCUSDT", Interval.D1, W_START, W_END)


def test_zero_overlap_all_sources_raises_all_sources_failed():
    # data entirely outside the requested window -> no candidate -> AllSourcesFailed.
    primary = _Stub("primary", _hist("primary", [date(2030, 1, 1), date(2030, 1, 2)]))
    client = FailoverCryptoClient([primary])
    with pytest.raises(AllSourcesFailed):
        client.get_klines("BTCUSDT", Interval.D1, W_START, W_END)


def test_one_sided_start_bound_prefix_partial():
    # only `start` requested (open end): first bar after start -> partial.
    primary = _Stub("primary", _hist("primary", [date(2026, 6, 15), date(2026, 6, 16)]))
    client = FailoverCryptoClient([primary])
    h = client.get_klines("BTCUSDT", Interval.D1, W_START, None)
    assert h.warnings == (
        "partial_coverage: requested 2026-06-01..open, returned 2026-06-15..2026-06-16",
    )
