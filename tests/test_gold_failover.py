"""World-gold failover + stooq backup tests — synthetic fixtures only.

No real provider rows are committed. The stooq CSV fixtures use the *documented*
column shape (``Date,Open,High,Low,Close,Volume``, USD/oz daily) with obviously-fake
fabricated numbers; the currency-api fixtures reuse the same synthetic shape as
``tests/test_gold.py``.

After B12 the **default** world-gold chain is the single reliable no-key source::

    default_world_gold_sources() == [CurrencyApiGoldSource]

Stooq stays an **explicit opt-in** backup (it answers a JS anti-bot challenge from
many server IPs). When opted in, ``[CurrencyApiGoldSource, StooqGoldSource]`` is a
valid same-unit (``USD/oz``) chain that the unit-homogeneity guard accepts; the
failover tests below build that two-source chain explicitly.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import (
    AllSourcesFailed,
    EmptyData,
    InvalidData,
    SourceUnavailable,
    UnitMismatchError,
    VnfinError,
)
from vnfin.gold import (
    CurrencyApiGoldSource,
    GoldBar,
    GoldHistory,
    GoldSource,
    StooqGoldSource,
)
from vnfin.gold import default_world_gold_sources, default_world_gold_client
from vnfin.gold.failover import FailoverGoldClient


# --------------------------------------------------------------------------- #
# Synthetic fixtures                                                          #
# --------------------------------------------------------------------------- #

# stooq daily CSV: documented shape Date,Open,High,Low,Close,Volume (USD/oz).
# SYNTHETIC obviously-fake round numbers; Close is the EOD price we keep.
_STOOQ_CSV = (
    "Date,Open,High,Low,Close,Volume\n"
    "2026-06-15,4000.0,4050.0,3990.0,4010.0,0\n"
    "2026-06-16,4010.0,4030.0,4000.0,4020.0,0\n"
    "2026-06-17,4020.0,4090.0,4015.0,4080.0,0\n"
)


def _currency_usd_json(d="2026-06-17", usd_xau=0.0002313114):
    return json.dumps({"date": d, "usd": {"eur": 0.86, "vnd": 26000.0, "xau": usd_xau}})


def _static_get(text):
    def _g(url, params=None, headers=None):
        return text

    return _g


def _raising_get(exc):
    def _g(url, params=None, headers=None):
        raise exc

    return _g


# --------------------------------------------------------------------------- #
# StooqGoldSource — parsing / units / failover-safe errors                     #
# --------------------------------------------------------------------------- #


def test_stooq_implements_port():
    assert issubclass(StooqGoldSource, GoldSource)


def test_stooq_capability_flags():
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    assert s.provides_history is True
    assert s.unit == "USD/oz"


def test_stooq_history_parses_csv_close_as_usd_oz():
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    hist = s.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert isinstance(hist, GoldHistory)
    assert hist.product == "XAU"
    assert hist.currency == "USD"
    assert hist.unit == "USD/oz"
    assert hist.value_unit == "USD/oz"
    assert hist.source == "stooq"
    assert len(hist) == 3
    dates = [b.date for b in hist.bars]
    assert dates == [date(2026, 6, 15), date(2026, 6, 16), date(2026, 6, 17)]
    # Close column is the EOD price we keep
    assert hist.bars[-1].price == pytest.approx(4080.0)
    assert isinstance(hist.bars[0], GoldBar)


def test_stooq_history_filters_to_requested_range():
    # full CSV spans 06-15..06-17; ask for only 06-16..06-17
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    hist = s.get_history(date(2026, 6, 16), date(2026, 6, 17))
    assert [b.date for b in hist.bars] == [date(2026, 6, 16), date(2026, 6, 17)]


def test_stooq_history_sorted_ascending():
    csv = (
        "Date,Open,High,Low,Close,Volume\n"
        "2026-06-17,4020.0,4090.0,4015.0,4080.0,0\n"
        "2026-06-15,4000.0,4050.0,3990.0,4010.0,0\n"
        "2026-06-16,4010.0,4030.0,4000.0,4020.0,0\n"
    )
    s = StooqGoldSource(http_get=_static_get(csv))
    hist = s.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert [b.date for b in hist.bars] == [
        date(2026, 6, 15),
        date(2026, 6, 16),
        date(2026, 6, 17),
    ]


def test_stooq_accepts_datetime_args():
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    hist = s.get_history(
        datetime(2026, 6, 15, 9, 0), datetime(2026, 6, 17, 17, 0)
    )
    assert len(hist) == 3


def test_stooq_empty_range_raises_empty():
    # CSV has data but none inside the requested window -> EmptyData
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    with pytest.raises(EmptyData):
        s.get_history(date(2025, 1, 1), date(2025, 1, 31))


def test_stooq_header_only_raises_empty():
    s = StooqGoldSource(http_get=_static_get("Date,Open,High,Low,Close,Volume\n"))
    with pytest.raises(EmptyData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_no_data_sentinel_raises_empty():
    # stooq returns the literal "No data" for an unknown symbol
    s = StooqGoldSource(http_get=_static_get("No data\n"))
    with pytest.raises(EmptyData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_malformed_close_raises_invalid():
    bad = (
        "Date,Open,High,Low,Close,Volume\n"
        "2026-06-17,4020.0,4090.0,4015.0,not-a-number,0\n"
    )
    s = StooqGoldSource(http_get=_static_get(bad))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_negative_close_raises_invalid():
    bad = (
        "Date,Open,High,Low,Close,Volume\n"
        "2026-06-17,4020.0,4090.0,4015.0,-5.0,0\n"
    )
    s = StooqGoldSource(http_get=_static_get(bad))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_bad_date_raises_invalid():
    bad = (
        "Date,Open,High,Low,Close,Volume\n"
        "garbage-date,4020.0,4090.0,4015.0,4080.0,0\n"
    )
    s = StooqGoldSource(http_get=_static_get(bad))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_missing_close_column_raises_invalid():
    bad = "Date,Open,High,Low,Volume\n2026-06-17,4020.0,4090.0,4015.0,0\n"
    s = StooqGoldSource(http_get=_static_get(bad))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_js_challenge_html_raises_unavailable():
    # stooq serves a JS proof-of-work challenge (HTML) instead of CSV from some IPs.
    # That must surface as SourceUnavailable so failover moves on, not InvalidData.
    html = (
        "<!DOCTYPE html><html><head></head><body>"
        "<noscript>This site requires JavaScript to verify your browser.</noscript>"
        "</body></html>"
    )
    s = StooqGoldSource(http_get=_static_get(html))
    with pytest.raises(SourceUnavailable):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_transport_error_wrapped():
    s = StooqGoldSource(http_get=_raising_get(ConnectionError("net")))
    with pytest.raises(SourceUnavailable):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_spot_quote_from_last_bar():
    # backup also satisfies the spot path (last EOD close), USD/oz
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    q = s.get_quote()
    assert q.product == "XAU"
    assert q.currency == "USD"
    assert q.unit == "USD/oz"
    assert q.buy == pytest.approx(4080.0)
    assert q.sell == pytest.approx(4080.0)
    assert q.source == "stooq"


# --------------------------------------------------------------------------- #
# World-gold failover wiring                                                  #
# --------------------------------------------------------------------------- #


def test_default_world_gold_sources_is_currency_api_only():
    # B12: the DEFAULT chain contains only the reliable no-key source. Stooq is NOT
    # in the default chain (it commonly hits an anti-bot challenge from server IPs).
    sources = default_world_gold_sources()
    assert [type(s) for s in sources] == [CurrencyApiGoldSource]
    assert not any(isinstance(s, StooqGoldSource) for s in sources)


def test_stooq_still_exported_as_opt_in_backup():
    # B12: Stooq stays importable/usable as an explicit opt-in source, just not default.
    sources = default_world_gold_sources() + [StooqGoldSource()]
    assert [type(s) for s in sources] == [CurrencyApiGoldSource, StooqGoldSource]


def test_world_gold_chain_is_usd_oz_homogeneous():
    # Opt Stooq in: both world sources declare USD/oz -> guard keeps both.
    client = FailoverGoldClient(default_world_gold_sources() + [StooqGoldSource()])
    assert client.unit == "USD/oz"
    assert len(client.sources) == 2


def test_world_gold_mixed_unit_chain_rejected():
    # a fabricated non-USD/oz source must be rejected by the unit guard
    class _BogusUnitSource(StooqGoldSource):
        unit = "VND/luong"

    with pytest.raises(UnitMismatchError):
        FailoverGoldClient(
            [
                CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json())),
                _BogusUnitSource(http_get=_static_get(_STOOQ_CSV)),
            ]
        )


def test_failover_uses_primary_when_healthy():
    primary = CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json(d="2026-06-17")))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(date(2026, 6, 17), date(2026, 6, 17))
    assert hist.source == "currency-api"
    assert hist.unit == "USD/oz"
    # attempts recorded; primary succeeded first
    assert hist.attempts[0].name == "currency-api"
    assert hist.attempts[0].ok is True


def test_failover_falls_through_to_stooq_on_primary_transport_error():
    primary = CurrencyApiGoldSource(http_get=_raising_get(ConnectionError("down")))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert hist.source == "stooq"
    assert len(hist) == 3
    # both attempts recorded: primary failed, backup ok
    names = [a.name for a in hist.attempts]
    assert names == ["currency-api", "stooq"]
    assert hist.attempts[0].ok is False
    assert hist.attempts[-1].ok is True


def test_failover_falls_through_on_primary_empty():
    # primary returns no usable rows (all dates 404) -> EmptyData -> fall through
    def _all_404(url, params=None, headers=None):
        raise FileNotFoundError("404")

    primary = CurrencyApiGoldSource(http_get=_all_404)
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert hist.source == "stooq"


def test_failover_all_sources_failed_raises():
    primary = CurrencyApiGoldSource(http_get=_raising_get(ConnectionError("down")))
    backup = StooqGoldSource(http_get=_raising_get(ConnectionError("down")))
    client = FailoverGoldClient([primary, backup])
    with pytest.raises(AllSourcesFailed):
        client.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_failover_never_leaks_raw_exception():
    # a raw, non-SourceError exception inside a source must not escape as itself;
    # transport wrapping turns it into SourceUnavailable, so the chain handles it.
    primary = CurrencyApiGoldSource(http_get=_raising_get(RuntimeError("weird")))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert hist.source == "stooq"


def test_default_world_gold_client_factory():
    client = default_world_gold_client()
    assert isinstance(client, FailoverGoldClient)
    assert client.unit == "USD/oz"
    # B12: default client now has the single reliable source (currency-api).
    assert len(client.sources) == 1
    assert isinstance(client.sources[0], CurrencyApiGoldSource)


def test_default_world_gold_client_accepts_injected_sources():
    primary = CurrencyApiGoldSource(http_get=_raising_get(ConnectionError("down")))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = default_world_gold_client(sources=[primary, backup])
    hist = client.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert hist.source == "stooq"


# --------------------------------------------------------------------------- #
# B11 — range-coverage acceptance (partial primary must not skip the backup)   #
# --------------------------------------------------------------------------- #

# A two-week window 2026-06-15 (Mon) .. 2026-06-26 (Fri): weekdays are
# 15,16,17,18,19 and 22,23,24,25,26 (20-21 are Sat/Sun) -> 10 expected trading days.
_WIN_START = date(2026, 6, 15)
_WIN_END = date(2026, 6, 26)
_WEEKDAYS = [
    date(2026, 6, d) for d in (15, 16, 17, 18, 19, 22, 23, 24, 25, 26)
]

# Backup stooq CSV that fully covers the 10-weekday window (obviously-fake numbers).
# High must cover the rising close so OHLC invariants hold across all rows.
_STOOQ_FULL_WINDOW_CSV = "Date,Open,High,Low,Close,Volume\n" + "".join(
    f"{d.isoformat()},4000.0,4100.0,3990.0,{4000.0 + i*10},0\n"
    for i, d in enumerate(_WEEKDAYS)
)


def _currency_only_for(available: set):
    """currency-api http_get that serves a doc only for the given calendar dates.

    The per-day request URL carries the date as the npm tag (``...@YYYY-MM-DD/...``).
    Dates not in ``available`` raise ``FileNotFoundError`` (a 404) -> the source skips
    that day, exactly like a real missing-date 404. This lets us fabricate a primary
    series with a controllable coverage fraction.
    """
    iso_dates = {d.isoformat() for d in available}

    def _g(url, params=None, headers=None):
        for iso in iso_dates:
            if f"@{iso}" in url:
                return _currency_usd_json(d=iso)
        raise FileNotFoundError(f"404 (no synthetic doc for {url})")

    return _g


def test_b11_materially_incomplete_primary_falls_through_to_backup():
    # Primary serves only 1 of 10 expected weekdays (10% < 50% min) -> must be
    # rejected as materially-incomplete and fall through to the complete backup.
    primary = CurrencyApiGoldSource(http_get=_currency_only_for({date(2026, 6, 15)}))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_FULL_WINDOW_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(_WIN_START, _WIN_END)
    assert hist.source == "stooq"
    # both attempts recorded: primary rejected for incomplete coverage, backup ok
    names = [a.name for a in hist.attempts]
    assert names == ["currency-api", "stooq"]
    assert hist.attempts[0].ok is False
    assert "materially-incomplete" in hist.attempts[0].reason
    assert hist.attempts[-1].ok is True


def test_b11_partial_primary_accepted_with_warning_in_middle_band():
    # Primary serves 6 of 10 weekdays (60%): >= 50% min so it is ACCEPTED, but
    # < 90% warn threshold so it carries a soft partial_coverage warning.
    served = set(_WEEKDAYS[:6])
    primary = CurrencyApiGoldSource(http_get=_currency_only_for(served))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_FULL_WINDOW_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(_WIN_START, _WIN_END)
    assert hist.source == "currency-api"
    assert len(hist.bars) == 6
    assert any("partial_coverage" in w for w in hist.warnings)
    assert hist.attempts[0].name == "currency-api"
    assert hist.attempts[0].ok is True


def test_b11_full_coverage_primary_accepted_without_warning():
    # Primary serves all 10 weekdays (100%) -> accepted, no coverage warning.
    primary = CurrencyApiGoldSource(http_get=_currency_only_for(set(_WEEKDAYS)))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_FULL_WINDOW_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(_WIN_START, _WIN_END)
    assert hist.source == "currency-api"
    assert len(hist.bars) == 10
    assert not any("partial_coverage" in w for w in hist.warnings)


def test_b11_incomplete_primary_and_incomplete_backup_all_sources_failed():
    # Neither source meets min coverage -> the chain raises AllSourcesFailed rather
    # than returning a materially-incomplete series.
    primary = CurrencyApiGoldSource(http_get=_currency_only_for({date(2026, 6, 15)}))
    # backup CSV has only one in-window weekday too
    one_day_csv = (
        "Date,Open,High,Low,Close,Volume\n2026-06-16,4010.0,4030.0,4000.0,4020.0,0\n"
    )
    backup = StooqGoldSource(http_get=_static_get(one_day_csv))
    client = FailoverGoldClient([primary, backup])
    with pytest.raises(AllSourcesFailed):
        client.get_history(_WIN_START, _WIN_END)


def test_b11_weekend_only_window_accepts_any_nonempty_result():
    # 2026-06-20 (Sat) .. 2026-06-21 (Sun): zero expected weekdays. A non-empty result
    # is accepted (nothing to be incomplete against) and carries no coverage warning.
    sat, sun = date(2026, 6, 20), date(2026, 6, 21)
    primary = CurrencyApiGoldSource(http_get=_currency_only_for({sat}))
    backup = StooqGoldSource(http_get=_raising_get(ConnectionError("down")))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(sat, sun)
    assert hist.source == "currency-api"
    assert len(hist.bars) == 1
    assert not any("partial_coverage" in w for w in hist.warnings)


def test_b11_single_weekday_full_coverage_no_warning():
    # The pre-existing single-weekday happy path still accepts cleanly (1/1 = 100%).
    primary = CurrencyApiGoldSource(
        http_get=_static_get(_currency_usd_json(d="2026-06-17"))
    )
    client = FailoverGoldClient([primary])
    hist = client.get_history(date(2026, 6, 17), date(2026, 6, 17))
    assert hist.source == "currency-api"
    assert not any("partial_coverage" in w for w in hist.warnings)


def test_b11_coverage_threshold_validation():
    src = [CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json()))]
    with pytest.raises(ValueError):
        FailoverGoldClient(src, min_coverage=-0.1)
    with pytest.raises(ValueError):
        FailoverGoldClient(src, min_coverage=1.5)
    with pytest.raises(ValueError):
        FailoverGoldClient(src, warn_coverage=2.0)
    with pytest.raises(ValueError):
        # warn must be >= min
        FailoverGoldClient(src, min_coverage=0.8, warn_coverage=0.5)
    with pytest.raises(ValueError, match="bool"):
        FailoverGoldClient(src, min_coverage=False, warn_coverage=False)
    with pytest.raises(ValueError, match="str"):
        FailoverGoldClient(src, min_coverage="0.5")

def test_b11_custom_min_coverage_accepts_lower_completeness():
    # With min_coverage lowered to 0.1, a 1/10 primary is now ACCEPTED (10% >= 10%).
    primary = CurrencyApiGoldSource(http_get=_currency_only_for({date(2026, 6, 15)}))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_FULL_WINDOW_CSV))
    client = FailoverGoldClient([primary, backup], min_coverage=0.1)
    hist = client.get_history(_WIN_START, _WIN_END)
    assert hist.source == "currency-api"
    assert len(hist.bars) == 1
    # still below warn threshold -> partial_coverage warning present
    assert any("partial_coverage" in w for w in hist.warnings)
