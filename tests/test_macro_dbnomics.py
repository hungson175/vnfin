"""Tests for the DBnomics (IMF/IFS) macro source — SYNTHETIC fixtures only.

Shape mirrors the DBnomics v22 series envelope
(``{"series": {"docs": [{"period_start_day": [...], "value": [...], ...}]}}``)
with NO real provider rows: fabricated periods/values, fake country ``ZZ``.
"""
import json
from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable
from vnfin.macro import DBnomicsSource, IndicatorSeries
from vnfin.macro.dbnomics import (
    _SERIES_END_GAP,
    _SERIES_END_GAP_FLOOR_DAYS,
    _series_end_gap_warning,
)
from vnfin.macro.indicators import (
    MacroIndicator,
    canonical_indicator_code,
    canonical_indicator_name,
)

COUNTRY = "ZZZ"  # ISO3 requested by callers; DBnomics IFS uses a 2-letter code internally


def dbn_success(series_code="A.ZZ.NGDP_XDC", periods=None, values=None):
    if periods is None:
        periods = ["2021-01-01", "2022-01-01", "2023-01-01"]
    if values is None:
        values = [100.0, 200.0, 300.0]
    doc = {
        "@frequency": "annual",
        "dataset_code": "IFS",
        "dataset_name": "International Financial Statistics (fake)",
        "provider_code": "IMF",
        "series_code": series_code,
        "series_name": "Fake series",
        "period": [p[:4] for p in periods],
        "period_start_day": periods,
        "value": values,
    }
    return json.dumps({"series": {"docs": [doc], "num_found": 1, "limit": 1000, "offset": 0}})


def dbn_no_docs():
    return json.dumps({"series": {"docs": [], "num_found": 0}})


def _static(text):
    def _g(url, params, headers):
        return text
    return _g


def _raising(exc):
    def _g(url, params, headers):
        raise exc
    return _g


def _src(text):
    return DBnomicsSource(http_get=_static(text))


# --- parsing ---------------------------------------------------------------

def test_parses_success_into_indicator_series():
    res = _src(dbn_success()).get_indicator(COUNTRY, MacroIndicator.GDP)
    assert isinstance(res, IndicatorSeries)
    assert res.source == "dbnomics"
    assert len(res.points) == 3


def test_parallel_arrays_zipped_in_order():
    res = _src(dbn_success(
        periods=["2021-01-01", "2022-01-01"], values=[11.0, 22.0]
    )).get_indicator(COUNTRY, MacroIndicator.GDP)
    assert res.points[0] == (date(2021, 1, 1), pytest.approx(11.0))
    assert res.points[1] == (date(2022, 1, 1), pytest.approx(22.0))


def test_monthly_period_start_day_parsed():
    res = _src(dbn_success(
        series_code="M.ZZ.PCPI_IX",
        periods=["2022-01-01", "2022-02-01", "2022-03-01"],
        values=[101.0, 102.0, 103.0],
    )).get_indicator(COUNTRY, MacroIndicator.CPI)
    months = [(d.year, d.month) for (d, _v) in res.points]
    assert months == [(2022, 1), (2022, 2), (2022, 3)]


def test_unit_is_canonical_for_indicator():
    res = _src(dbn_success()).get_indicator(COUNTRY, MacroIndicator.GDP)
    # DBnomics GDP is national currency -> NOT the canonical USD level.
    assert res.unit == "national currency"


def test_cpi_unit_is_index():
    res = _src(dbn_success(series_code="M.ZZ.PCPI_IX")).get_indicator(COUNTRY, MacroIndicator.CPI)
    assert res.unit == "index"


def test_dbnomics_series_code_mismatch_raises_invalid():
    # Issue #21: a doc whose series_code names a different series (e.g. another country) must
    # raise InvalidData, not be stamped with the requested indicator identity.
    payload = dbn_success(series_code="M.US.PCPI_IX")  # request resolves to M.ZZ.PCPI_IX
    with pytest.raises(InvalidData):
        _src(payload).get_indicator(COUNTRY, MacroIndicator.CPI)


@pytest.mark.parametrize("bad_code", [123, [], {}, "", "   ", None])
def test_dbnomics_malformed_series_code_raises_invalid(bad_code):
    # Issue #21 (BLOCK): a present-but-malformed/blank/null series_code must not be accepted
    # and stamped with the requested indicator identity.
    payload = dbn_success(series_code=bad_code)
    with pytest.raises(InvalidData):
        _src(payload).get_indicator(COUNTRY, MacroIndicator.CPI)


def test_source_unit_for_indicator():
    s = _src(dbn_success())
    assert s.unit_for(MacroIndicator.CPI) == "index"
    assert s.unit_for(MacroIndicator.GDP) == "national currency"


# --- request shape ---------------------------------------------------------

def test_request_url_and_observations_param():
    captured = {}

    def _g(url, params, headers):
        captured["url"] = url
        captured["params"] = params
        return dbn_success()

    DBnomicsSource(http_get=_g).get_indicator("zzz", MacroIndicator.GDP)
    assert captured["url"].startswith("https://api.db.nomics.world/v22/series/IMF/IFS/")
    assert "ZZ" in captured["url"]  # ISO3 -> ISO2 mapping in series id
    assert str(captured["params"]["observations"]) == "1"


# --- empties / nulls -------------------------------------------------------

def test_no_docs_raises_empty():
    with pytest.raises(EmptyData):
        _src(dbn_no_docs()).get_indicator(COUNTRY, MacroIndicator.GDP)


def test_null_values_skipped():
    res = _src(dbn_success(
        periods=["2021-01-01", "2022-01-01", "2023-01-01"], values=[1.0, None, 3.0]
    )).get_indicator(COUNTRY, MacroIndicator.GDP)
    years = [d.year for (d, _v) in res.points]
    assert years == [2021, 2023]


def test_na_string_value_skipped():
    # DBnomics encodes missing as the string "NA"
    res = _src(dbn_success(
        periods=["2021-01-01", "2022-01-01"], values=["NA", 5.0]
    )).get_indicator(COUNTRY, MacroIndicator.GDP)
    assert [d.year for (d, _v) in res.points] == [2022]


def test_all_null_raises_empty():
    with pytest.raises(EmptyData):
        _src(dbn_success(periods=["2021-01-01"], values=[None])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


# --- malformed -------------------------------------------------------------

def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html/>").get_indicator(COUNTRY, MacroIndicator.GDP)


def test_missing_series_key_raises_invalid():
    with pytest.raises(InvalidData):
        _src(json.dumps({"_meta": {}})).get_indicator(COUNTRY, MacroIndicator.GDP)


def test_length_mismatch_arrays_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success(periods=["2021-01-01", "2022-01-01"], values=[1.0])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_garbage_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success(periods=["2021-01-01"], values=["definitely-not-a-number"])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_garbage_period_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success(periods=["nonsense"], values=[1.0])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_unsupported_indicator_raises_invalid():
    # GDP_GROWTH (%) is not in DBnomics/IFS map here -> InvalidData
    with pytest.raises(InvalidData):
        _src(dbn_success()).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


# --- transport / validation ------------------------------------------------

def test_transport_error_wrapped_as_unavailable():
    with pytest.raises(SourceUnavailable):
        DBnomicsSource(http_get=_raising(TimeoutError("t"))).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_empty_country_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success()).get_indicator("", MacroIndicator.GDP)


def test_unknown_country_iso3_raises_invalid():
    # A fake ISO3 with no ISO2 mapping must fail cleanly (InvalidData), not crash.
    with pytest.raises(InvalidData):
        _src(dbn_success()).get_indicator("QQQ", MacroIndicator.GDP)


# --- level-indicator positivity guard (issue #16) --------------------------
def test_gdp_negative_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success(periods=["2023-01-01"], values=[-100.0])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_cpi_negative_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(
            dbn_success(
                series_code="M.ZZ.PCPI_IX", periods=["2023-01-01"], values=[-10.0]
            )
        ).get_indicator(COUNTRY, MacroIndicator.CPI)


def test_cpi_zero_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(
            dbn_success(
                series_code="M.ZZ.PCPI_IX", periods=["2023-01-01"], values=[0.0]
            )
        ).get_indicator(COUNTRY, MacroIndicator.CPI)


# --- period_start_day vs frequency contract (issue #104) -------------------

def test_annual_gdp_non_jan_1_raises_invalid():
    with pytest.raises(InvalidData, match="period"):
        _src(dbn_success(periods=["2024-02-01"], values=[123.0])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_monthly_cpi_non_month_start_raises_invalid():
    with pytest.raises(InvalidData, match="period"):
        _src(
            dbn_success(
                series_code="M.ZZ.PCPI_IX", periods=["2024-01-15"], values=[123.0]
            )
        ).get_indicator(COUNTRY, MacroIndicator.CPI)



# --------------------------------------------------------------------------- #
# Issue #104 — period_start_day must be a canonical YYYY-MM-DD string (no coerce);
# Issue #66 — duplicate canonical period_start_day in one response must reject.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "bad_period",
    ["20240101", "2024-W01-1", " 2024-01-01 ", "2024-1-1", "2024/01/01", "2024-01-01T00:00:00"],
    ids=["compact", "iso_week", "padded", "non_zero_pad", "slashes", "datetime"],
)
def test_dbnomics_rejects_noncanonical_period_start_day(bad_period):
    payload = dbn_success(periods=[bad_period], values=[123.0])
    with pytest.raises(InvalidData):
        _src(payload).get_indicator(COUNTRY, MacroIndicator.GDP)


def test_dbnomics_rejects_nonstring_period_start_day():
    # A non-string period_start_day (built inline; the helper assumes strings).
    doc = {
        "@frequency": "annual",
        "series_code": "A.ZZ.NGDP_XDC",
        "period": ["2024"],
        "period_start_day": [20240101],
        "value": [123.0],
    }
    payload = json.dumps({"series": {"docs": [doc], "num_found": 1}})
    with pytest.raises(InvalidData):
        _src(payload).get_indicator(COUNTRY, MacroIndicator.GDP)


def test_dbnomics_rejects_duplicate_period_start_day():
    payload = dbn_success(periods=["2024-01-01", "2024-01-01"], values=[100.0, 200.0])
    with pytest.raises(InvalidData, match="duplicate period_start_day"):
        _src(payload).get_indicator(COUNTRY, MacroIndicator.GDP)


def test_dbnomics_canonical_distinct_dates_accepted():
    res = _src(
        dbn_success(periods=["2021-01-01", "2022-01-01"], values=[100.0, 200.0])
    ).get_indicator(COUNTRY, MacroIndicator.GDP)
    assert [p[0] for p in res.points] == [date(2021, 1, 1), date(2022, 1, 1)]


# --- #179: monthly CPI YoY + SBV policy rate (DBnomics-only) ----------------

# Verbose SBV-proxy DISPLAY label; must stay separate from the stable canonical
# "Policy Rate" identity (N-a). Mirrors _DBN_MAP[POLICY_RATE] 5th element.
_POLICY_RATE_DISPLAY = "Policy Rate (SBV refinancing-rate proxy, IMF IFS FPOLM_PA)"


def test_cpi_yoy_monthly_happy_path(monkeypatch):
    # N-b: realistic CPI-YoY magnitude (~3%, not 0.03). Pin _today near last obs so
    # the staleness warning does not fire (value asserts kept separate from gap).
    monkeypatch.setattr("vnfin.macro.dbnomics._today", lambda: date(2024, 4, 1))
    res = _src(dbn_success(
        series_code="M.ZZ.PCPI_PC_CP_A_PT",
        periods=["2024-01-01", "2024-02-01", "2024-03-01"],
        values=[3.1, 2.9, 3.2],
    )).get_indicator(COUNTRY, MacroIndicator.CPI_YOY)
    assert res.unit == "%"
    assert res.currency is None
    assert res.frequency.value == "monthly"
    assert res.indicator_code == "M.ZZ.PCPI_PC_CP_A_PT"
    assert res.indicator_name == "cpi_yoy (PCPI_PC_CP_A_PT)"
    assert res.points[-1] == (date(2024, 3, 1), pytest.approx(3.2))
    assert res.warnings == ()  # fresh -> no staleness warning


def test_policy_rate_monthly_happy_path(monkeypatch):
    # N-b: policy rate ~4.5 percent-points, NOT a 0.045 fraction.
    monkeypatch.setattr("vnfin.macro.dbnomics._today", lambda: date(2024, 4, 1))
    res = _src(dbn_success(
        series_code="M.ZZ.FPOLM_PA",
        periods=["2024-01-01", "2024-02-01", "2024-03-01"],
        values=[6.0, 5.0, 4.5],
    )).get_indicator(COUNTRY, MacroIndicator.POLICY_RATE)
    assert res.unit == "% per annum"
    assert res.currency is None
    assert res.frequency.value == "monthly"
    assert res.indicator_code == "M.ZZ.FPOLM_PA"
    # honest verbose proxy DISPLAY label rides on the result name
    assert res.indicator_name == _POLICY_RATE_DISPLAY
    assert res.points[-1][1] == pytest.approx(4.5)  # magnitude, not 0.045


def test_policy_rate_identity_keyed_to_code_not_display():
    # N-a: the verbose proxy string is display-only; the STABLE canonical identity
    # stays "policy_rate"/"Policy Rate" (Boss can edit the disclosure text without
    # destabilizing identity / the cross-collision guard).
    assert canonical_indicator_code(MacroIndicator.POLICY_RATE) == "policy_rate"
    assert canonical_indicator_name(MacroIndicator.POLICY_RATE) == "Policy Rate"
    assert _POLICY_RATE_DISPLAY != canonical_indicator_name(MacroIndicator.POLICY_RATE)
    # indicator_identity() (declared) returns the SAME verbose name the result carries
    code, name = _src(dbn_success()).indicator_identity("ZZZ", MacroIndicator.POLICY_RATE)
    assert code == "M.ZZ.FPOLM_PA"
    assert name == _POLICY_RATE_DISPLAY


def test_cpi_yoy_deflation_negative_allowed(monkeypatch):
    # CPI_YOY is not a level indicator -> a negative (deflation) value is accepted.
    monkeypatch.setattr("vnfin.macro.dbnomics._today", lambda: date(2024, 4, 1))
    res = _src(dbn_success(
        series_code="M.ZZ.PCPI_PC_CP_A_PT",
        periods=["2024-01-01", "2024-02-01", "2024-03-01"],
        values=[1.2, -0.5, 0.3],
    )).get_indicator(COUNTRY, MacroIndicator.CPI_YOY)
    assert res.points[1][1] == pytest.approx(-0.5)


# --- staleness: pure helper (deterministic, injected `today`) ---------------

def test_series_end_gap_warns_when_stale():
    # last obs 2023-12, today 2026-06 (~30mo) >> 210d floor -> one mechanical warning.
    points = [(date(2023, 10, 1), 5.0), (date(2023, 11, 1), 4.5), (date(2023, 12, 1), 4.5)]
    out = _series_end_gap_warning(points, date(2026, 6, 1))
    assert len(out) == 1
    assert out[0].startswith(f"{_SERIES_END_GAP}:")
    assert "2023-12-01" in out[0]


def test_series_end_gap_no_warn_when_fresh():
    points = [(date(2024, 1, 1), 3.0), (date(2024, 2, 1), 3.1), (date(2024, 3, 1), 3.2)]
    assert _series_end_gap_warning(points, date(2024, 4, 1)) == ()  # ~31d gap


def test_series_end_gap_no_warn_when_series_reaches_today():
    # gap_days <= 0: the latest observation is on/after `today` (e.g. a same-day
    # publish, or today exactly at the last month-start). Never warns, never raises.
    points = [(date(2024, 1, 1), 3.0), (date(2024, 2, 1), 3.1), (date(2024, 3, 1), 3.2)]
    assert _series_end_gap_warning(points, date(2024, 3, 1)) == ()  # gap == 0
    assert _series_end_gap_warning(points, date(2024, 2, 15)) == ()  # gap < 0 (future-dated last obs)


def test_series_end_gap_floor_is_210_not_twice_cadence():
    # gap ~92d > 2x the ~30d monthly cadence (60d) but < the 210d floor: a healthy
    # monthly series within IMF's normal publication lag must NOT warn.
    assert _SERIES_END_GAP_FLOOR_DAYS == 210
    points = [(date(2024, 1, 1), 3.0), (date(2024, 2, 1), 3.1), (date(2024, 3, 1), 3.2)]
    assert _series_end_gap_warning(points, date(2024, 6, 1)) == ()


def test_series_end_gap_robust_to_single_cadence_gap():
    # a real monthly series can skip a month (FPOLM_PA skipped 2023-10); the median
    # cadence stays ~30d so the 210d floor still governs.
    points = [
        (date(2023, 7, 1), 4.5), (date(2023, 8, 1), 4.5), (date(2023, 9, 1), 4.5),
        (date(2023, 11, 1), 4.5), (date(2023, 12, 1), 4.5),
    ]
    out = _series_end_gap_warning(points, date(2026, 6, 1))
    assert len(out) == 1 and out[0].startswith(f"{_SERIES_END_GAP}:")


# --- staleness: through get_indicator (pinned _today) ----------------------

def test_get_indicator_emits_series_end_gap_when_stale(monkeypatch):
    monkeypatch.setattr("vnfin.macro.dbnomics._today", lambda: date(2026, 6, 1))
    res = _src(dbn_success(
        series_code="M.ZZ.FPOLM_PA",
        periods=["2023-10-01", "2023-11-01", "2023-12-01"],
        values=[5.0, 4.5, 4.5],
    )).get_indicator(COUNTRY, MacroIndicator.POLICY_RATE)
    assert any(w.startswith(f"{_SERIES_END_GAP}:") for w in res.warnings)
    # the pinned _today (a date) must NOT leak into fetched_at_utc (a real datetime)
    assert isinstance(res.fetched_at_utc, datetime)
    assert res.fetched_at_utc.tzinfo is not None
    assert res.fetched_at_utc.year >= 2024


def test_get_indicator_no_warning_when_fresh(monkeypatch):
    monkeypatch.setattr("vnfin.macro.dbnomics._today", lambda: date(2024, 4, 1))
    res = _src(dbn_success(
        series_code="M.ZZ.PCPI_PC_CP_A_PT",
        periods=["2024-01-01", "2024-02-01", "2024-03-01"],
        values=[3.1, 2.9, 3.2],
    )).get_indicator(COUNTRY, MacroIndicator.CPI_YOY)
    assert res.warnings == ()


def test_annual_gdp_never_warns_even_when_old(monkeypatch):
    # the staleness warning is MONTHLY-scoped (v1): annual GDP must not warn even
    # though its last obs (2023) is > 210d before a pinned 2026 today.
    monkeypatch.setattr("vnfin.macro.dbnomics._today", lambda: date(2026, 6, 1))
    res = _src(dbn_success()).get_indicator(COUNTRY, MacroIndicator.GDP)  # annual NGDP_XDC
    assert res.warnings == ()
