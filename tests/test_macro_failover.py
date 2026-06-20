"""Tests for the macro failover client + default chain — SYNTHETIC only.

Exercises ``default_macro_sources()`` and ``get_indicator(country, indicator)``
wired over the generic :class:`vnfin.failover.FailoverClient` with a per-indicator
unit-homogeneity guard. Uses fake in-memory sources and fabricated values; no
network, no real provider rows.
"""
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.exceptions import (
    AllSourcesFailed,
    EmptyData,
    InvalidData,
    SourceUnavailable,
    UnitMismatchError,
)
from vnfin.macro import (
    DBnomicsSource,
    IMFDataMapperSource,
    IndicatorSeries,
    MacroIndicator,
    WorldBankMacroSource,
    canonical_currency,
    canonical_indicator_code,
    canonical_indicator_name,
    canonical_unit,
    default_macro_client,
    default_macro_sources,
    get_indicator,
)
from vnfin.macro.dbnomics import _SERIES_END_GAP


# ---- fake sources (declare unit_for + get_indicator like the real ones) ----

class FakeMacroSource:
    def __init__(self, name, units, behavior=None):
        # units: {MacroIndicator: unit-str-or-None(unsupported)}
        self._name = name
        self._units = units
        self._behavior = behavior or {}

    @property
    def name(self):
        return self._name

    def unit_for(self, indicator):
        u = self._units.get(MacroIndicator(indicator))
        if u is None:
            raise InvalidData(f"{self._name}: unsupported indicator {indicator}")
        return u

    def get_indicator(self, country_iso3, indicator):
        from vnfin.macro.indicators import canonical_currency

        ind = MacroIndicator(indicator)
        b = self._behavior.get(ind, "ok")
        if b == "unavailable":
            raise SourceUnavailable(f"{self._name}: down")
        if b == "empty":
            raise EmptyData(f"{self._name}: empty")
        if b == "invalid":
            raise InvalidData(f"{self._name}: bad")
        unit = self.unit_for(ind)
        return IndicatorSeries(
            country=country_iso3.upper(),
            indicator_code=canonical_indicator_code(ind),
            indicator_name=canonical_indicator_name(ind),
            points=((date(2023, 1, 1), 42.0),),
            source=self._name,
            unit=unit,
            currency=canonical_currency(ind),
            fetched_at_utc=datetime.now(timezone.utc),
        )


PCT = {MacroIndicator.GDP_GROWTH: "%", MacroIndicator.INFLATION: "%", MacroIndicator.UNEMPLOYMENT: "%"}


# ---- default chain composition --------------------------------------------

def test_default_macro_sources_order_is_wb_imf_dbnomics():
    srcs = default_macro_sources()
    assert isinstance(srcs[0], WorldBankMacroSource)
    assert isinstance(srcs[1], IMFDataMapperSource)
    assert isinstance(srcs[2], DBnomicsSource)
    assert len(srcs) == 3


def test_default_chain_excludes_fred_byok():
    from vnfin.macro import FREDMacroSource
    srcs = default_macro_sources()
    assert not any(isinstance(s, FREDMacroSource) for s in srcs)


# ---- happy path failover ---------------------------------------------------

def test_first_source_serves_when_healthy():
    a = FakeMacroSource("a", PCT)
    b = FakeMacroSource("b", PCT)
    res = get_indicator("ZZZ", MacroIndicator.GDP_GROWTH, sources=[a, b])
    assert res.source == "a"
    assert res.unit == "%"


def test_fails_over_to_second_on_unavailable():
    a = FakeMacroSource("a", PCT, behavior={MacroIndicator.GDP_GROWTH: "unavailable"})
    b = FakeMacroSource("b", PCT)
    res = get_indicator("ZZZ", MacroIndicator.GDP_GROWTH, sources=[a, b])
    assert res.source == "b"


def test_fails_over_on_empty_then_invalid_then_ok():
    a = FakeMacroSource("a", PCT, behavior={MacroIndicator.INFLATION: "empty"})
    b = FakeMacroSource("b", PCT, behavior={MacroIndicator.INFLATION: "invalid"})
    c = FakeMacroSource("c", PCT)
    res = get_indicator("ZZZ", MacroIndicator.INFLATION, sources=[a, b, c])
    assert res.source == "c"


def test_all_fail_raises_all_sources_failed():
    a = FakeMacroSource("a", PCT, behavior={MacroIndicator.INFLATION: "unavailable"})
    b = FakeMacroSource("b", PCT, behavior={MacroIndicator.INFLATION: "empty"})
    with pytest.raises(AllSourcesFailed):
        get_indicator("ZZZ", MacroIndicator.INFLATION, sources=[a, b])


# ---- per-indicator unit guard ---------------------------------------------

def test_noncanonical_unit_source_is_filtered_out_not_raised():
    # B6/B7: the canonical GDP unit is "current US$". A source declaring a
    # different unit ("national currency") must be DROPPED before the engine is
    # built (so the default GDP chain never raises UnitMismatchError), and the
    # canonical-unit source must serve the request.
    a = FakeMacroSource("a", {MacroIndicator.GDP: "current US$"})
    b = FakeMacroSource("b", {MacroIndicator.GDP: "national currency"})
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[a, b])
    assert res.source == "a"
    assert res.unit == "current US$"


def test_only_noncanonical_unit_sources_raises_all_sources_failed():
    # If EVERY source for the indicator emits a noncanonical unit, none are
    # eligible -> a clean AllSourcesFailed (capability), never a wrong-unit result.
    a = FakeMacroSource("a", {MacroIndicator.GDP: "national currency"})
    b = FakeMacroSource("b", {MacroIndicator.GDP: "USD bn"})
    with pytest.raises(AllSourcesFailed):
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[a, b])


def test_reject_reason_refuses_to_relabel_a_drifted_unit():
    # B7 backstop: a source declares the canonical unit (passes the pre-filter)
    # but its returned series carries a DIFFERENT non-empty unit. The result guard
    # must reject it so failover can move on, not silently relabel it.
    class DriftingSource:
        name = "drift"

        def unit_for(self, indicator):
            return "current US$"  # declares canonical -> survives pre-filter

        def supports(self, indicator):
            return MacroIndicator(indicator) == MacroIndicator.GDP

        def get_indicator(self, country_iso3, indicator):
            return IndicatorSeries(
                country=country_iso3.upper(),
                # Canonical identity so #78 identity validation passes and the test
                # isolates the UNIT drift (the behavior under test).
                indicator_code=canonical_indicator_code(MacroIndicator.GDP),
                indicator_name=canonical_indicator_name(MacroIndicator.GDP),
                points=((date(2022, 1, 1), 1000.0),),
                source=self.name,
                unit="national currency",  # drifted away from canonical at fetch time
                fetched_at_utc=datetime.now(timezone.utc),
            )

    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[DriftingSource()])
    assert "unit mismatch" in ei.value.attempts[0].reason


def test_default_gdp_chain_does_not_raise_unit_mismatch():
    # The real default chain (WB current US$, IMF USD bn, DBnomics national
    # currency) must NOT raise UnitMismatchError for GDP: only WB is canonical, so
    # the chain reduces to WB and serves a synthetic GDP level.
    import json as _json
    from vnfin.macro import default_macro_client

    wb_text = _json.dumps([
        {"page": 1, "pages": 1, "per_page": 50, "total": 1},
        [{"indicator": {"id": "NY.GDP.MKTP.CD", "value": "Fake GDP"},
          "country": {"id": "ZZ", "value": "Fakeland"}, "countryiso3code": "ZZZ",
          "date": "2022", "value": 777000000.0, "unit": "current US$"}],
    ])
    wb = WorldBankMacroSource(http_get=lambda u, p, h: wb_text)
    imf = IMFDataMapperSource(http_get=lambda u, p, h: _json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: _json.dumps({"series": {"docs": []}}))
    res = default_macro_client(sources=[wb, imf, dbn]).get_indicator("ZZZ", MacroIndicator.GDP)
    assert res.source == "worldbank"
    assert res.unit == "current US$"
    assert res.currency == "USD"
    assert res.points[0][1] == pytest.approx(777000000.0)


def test_default_cpi_chain_does_not_raise_unit_mismatch():
    # CPI canonical unit is "index"; only DBnomics serves it -> chain reduces to
    # DBnomics, returns a synthetic monthly index without UnitMismatchError.
    import json as _json
    from vnfin.macro import default_macro_client

    dbn_text = _json.dumps({"series": {"docs": [{
        "series_code": "M.ZZ.PCPI_IX",
        "period_start_day": ["2022-01-01", "2022-02-01"],
        "period": ["2022", "2022"],
        "value": [110.0, 111.0],
    }]}})
    wb = WorldBankMacroSource(http_get=lambda u, p, h: _json.dumps([{"total": 0}, None]))
    imf = IMFDataMapperSource(http_get=lambda u, p, h: _json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: dbn_text)
    res = default_macro_client(sources=[wb, imf, dbn]).get_indicator("ZZZ", MacroIndicator.CPI)
    assert res.source == "dbnomics"
    assert res.unit == "index"
    assert res.currency is None
    assert res.frequency.value == "monthly"


def test_unit_guard_allows_same_unit_chain():
    a = FakeMacroSource("a", {MacroIndicator.GDP: "current US$"},
                        behavior={MacroIndicator.GDP: "unavailable"})
    b = FakeMacroSource("b", {MacroIndicator.GDP: "current US$"})
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[a, b])
    assert res.source == "b"
    assert res.unit == "current US$"


def test_source_not_supporting_indicator_is_skipped_not_a_failure():
    # 'a' does not support UNEMPLOYMENT -> skipped (capability), 'b' serves it.
    a = FakeMacroSource("a", {MacroIndicator.GDP_GROWTH: "%"})  # no UNEMPLOYMENT
    b = FakeMacroSource("b", PCT)
    res = get_indicator("ZZZ", MacroIndicator.UNEMPLOYMENT, sources=[a, b])
    assert res.source == "b"


def test_no_source_supports_indicator_raises():
    a = FakeMacroSource("a", {MacroIndicator.GDP_GROWTH: "%"})
    b = FakeMacroSource("b", {MacroIndicator.GDP_GROWTH: "%"})
    with pytest.raises((AllSourcesFailed, InvalidData)):
        get_indicator("ZZZ", MacroIndicator.UNEMPLOYMENT, sources=[a, b])


# ---- BYOK skip-without-network (C4) ---------------------------------------

def test_keyless_fred_skipped_without_network_in_chain(monkeypatch):
    # C4: a BYOK source with no key must be skipped BEFORE any network call when
    # placed in a failover chain (not advertised-then-crashing, no NotImplemented).
    from vnfin.macro import FREDMacroSource

    monkeypatch.delenv("FRED_API_KEY", raising=False)
    calls = {"fred": 0}

    def fred_get(url, params, headers):
        calls["fred"] += 1
        return "{}"

    keyless_fred = FREDMacroSource(http_get=fred_get)  # no key
    wb = FakeMacroSource("wb", PCT)  # canonical percent source serves it
    res = get_indicator("ZZZ", MacroIndicator.GDP_GROWTH, sources=[keyless_fred, wb])
    assert res.source == "wb"
    assert calls["fred"] == 0  # keyless FRED never touched the network


def test_keyless_fred_supports_is_false_no_network(monkeypatch):
    # The capability probe itself must not hit the network.
    from vnfin.macro import FREDMacroSource

    monkeypatch.delenv("FRED_API_KEY", raising=False)
    calls = {"n": 0}

    def fred_get(url, params, headers):
        calls["n"] += 1
        return "{}"

    s = FREDMacroSource(http_get=fred_get)
    assert s.supports(MacroIndicator.GDP_GROWTH) is False
    assert calls["n"] == 0


# ---- client object ---------------------------------------------------------

def test_default_macro_client_get_indicator_real_sources_offline():
    # Build the real client but feed each real source a static fake http_get so
    # no network is touched; confirm WB (first) wins with synthetic GDP_GROWTH.
    wb_text = json.dumps([
        {"page": 1, "pages": 1, "per_page": 50, "total": 1},
        [{"indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "Fake growth"},
          "country": {"id": "ZZ", "value": "Fakeland"}, "countryiso3code": "ZZZ",
          "date": "2023", "value": 5.5, "unit": "", "obs_status": "", "decimal": 1}],
    ])

    def wb_get(url, params, headers):
        return wb_text

    wb = WorldBankMacroSource(http_get=wb_get)
    imf = IMFDataMapperSource(http_get=lambda u, p, h: json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: json.dumps({"series": {"docs": []}}))
    client = default_macro_client(sources=[wb, imf, dbn])
    res = client.get_indicator("ZZZ", MacroIndicator.GDP_GROWTH)
    assert res.source == "worldbank"
    assert res.unit == "%"
    assert res.points[0][1] == pytest.approx(5.5)


def test_client_unit_property_reflects_indicator():
    a = FakeMacroSource("a", PCT)
    b = FakeMacroSource("b", PCT)
    client = default_macro_client(sources=[a, b])
    # The client serves per-indicator; the chain unit for GDP_GROWTH is "%".
    res = client.get_indicator("ZZZ", MacroIndicator.GDP_GROWTH)
    assert res.unit == "%"


def test_empty_country_raises_invalid_before_network():
    a = FakeMacroSource("a", PCT)
    with pytest.raises(InvalidData):
        get_indicator("", MacroIndicator.GDP_GROWTH, sources=[a])


def test_unknown_indicator_raises_invalid_data():
    # Issue #48: unknown indicators must surface as InvalidData (failover-safe),
    # not a raw ValueError.
    a = FakeMacroSource("a", PCT)
    with pytest.raises(InvalidData):
        get_indicator("ZZZ", "not_a_real_indicator", sources=[a])


# --- Issue #32: country input must be a valid ISO3 code -------------------------

@pytest.mark.parametrize("bad", ["US", "USAA", "12A", "U$D", 123, ["USA"], "", "   "])
def test_get_indicator_rejects_invalid_country(bad):
    a = FakeMacroSource("a", PCT)
    with pytest.raises(InvalidData):
        get_indicator(bad, MacroIndicator.GDP_GROWTH, sources=[a])


def test_get_indicator_normalizes_valid_country_to_uppercase():
    a = FakeMacroSource("a", PCT)
    res = get_indicator("vnm", MacroIndicator.GDP_GROWTH, sources=[a])
    assert res.country == "VNM"


def test_country_validation_runs_before_network():
    a = FakeMacroSource("a", PCT)
    calls = {"n": 0}

    class CountingSource(FakeMacroSource):
        def get_indicator(self, country_iso3, indicator):
            calls["n"] += 1
            return super().get_indicator(country_iso3, indicator)

    with pytest.raises(InvalidData):
        get_indicator("US", MacroIndicator.GDP_GROWTH, sources=[CountingSource("a", PCT)])
    assert calls["n"] == 0


# --- Batch-1 result guards: identity, unit/currency, level-indicator values ----


def _make_fake_for_guard(indicator, **overrides):
    class GuardSource:
        name = "guard"

        def __init__(self):
            self.unit_for = lambda ind: canonical_unit(indicator)
            self.supports = lambda ind: True

        def get_indicator(self, country_iso3, indicator_arg):
            defaults = dict(
                country=country_iso3.upper(),
                indicator_code=canonical_indicator_code(indicator),
                indicator_name=canonical_indicator_name(indicator),
                points=((date(2023, 1, 1), 42.0),),
                source="guard",
                unit=canonical_unit(indicator),
                value_unit=canonical_unit(indicator),
                currency=canonical_currency(indicator),
                fetched_at_utc=datetime.now(timezone.utc),
            )
            defaults.update(overrides)
            return IndicatorSeries(**defaults)

    return GuardSource()


def test_rejects_returned_country_mismatch():
    src = _make_fake_for_guard(MacroIndicator.GDP_GROWTH, country="USA")
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("VNM", MacroIndicator.GDP_GROWTH, sources=[src])
    assert "country" in ei.value.attempts[0].reason


def test_rejects_returned_unit_mismatch():
    src = _make_fake_for_guard(MacroIndicator.GDP_GROWTH, unit="USD bn", value_unit="USD bn")
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("VNM", MacroIndicator.GDP_GROWTH, sources=[src])
    assert "unit" in ei.value.attempts[0].reason


def test_rejects_returned_currency_mismatch():
    src = _make_fake_for_guard(MacroIndicator.GDP, currency="VND")
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("VNM", MacroIndicator.GDP, sources=[src])
    assert "currency" in ei.value.attempts[0].reason


def test_rejects_negative_gdp_level():
    src = _make_fake_for_guard(MacroIndicator.GDP, points=((date(2023, 1, 1), -1.0),))
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("VNM", MacroIndicator.GDP, sources=[src])
    assert "must be positive" in ei.value.attempts[0].reason


def test_rejects_unemployment_out_of_bounds():
    src = _make_fake_for_guard(
        MacroIndicator.UNEMPLOYMENT, points=((date(2023, 1, 1), 101.0),)
    )
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("VNM", MacroIndicator.UNEMPLOYMENT, sources=[src])
    assert "between 0 and 100" in ei.value.attempts[0].reason


# --- Issue #78 follow-up: returned series must answer the requested indicator ----


def test_rejects_returned_indicator_mismatch():
    src = _make_fake_for_guard(
        MacroIndicator.INFLATION,
        indicator_code=canonical_indicator_code(MacroIndicator.GDP),
        indicator_name=canonical_indicator_name(MacroIndicator.GDP),
    )
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("VNM", MacroIndicator.INFLATION, sources=[src])
    assert "indicator" in ei.value.attempts[0].reason


# --- Issue #95: series points must be strictly ascending by date -----------------


def test_rejects_unsorted_points():
    src = _make_fake_for_guard(
        MacroIndicator.GDP_GROWTH,
        points=((date(2023, 1, 1), 5.0), (date(2022, 1, 1), 4.0)),
    )
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("VNM", MacroIndicator.GDP_GROWTH, sources=[src])
    assert "ascending" in ei.value.attempts[0].reason


# --- Issue #96: point values must be finite -------------------------------------


def test_rejects_non_finite_point_values():
    from math import nan

    src = _make_fake_for_guard(
        MacroIndicator.GDP_GROWTH,
        points=((date(2023, 1, 1), nan),),
    )
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("VNM", MacroIndicator.GDP_GROWTH, sources=[src])
    assert "finite" in ei.value.attempts[0].reason


# --------------------------------------------------------------------------- #
# Issue #125 — malformed (non-typed) macro result container -> rejected attempt,
# not a raw AttributeError from len(series.points).
# --------------------------------------------------------------------------- #
class _MalformedMacroSource:
    """Declares the canonical unit (survives the pre-filter) but returns a
    non-IndicatorSeries object from get_indicator."""

    def __init__(self, name, bad):
        self.name = name
        self._bad = bad

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def get_indicator(self, country_iso3, indicator):
        return self._bad


@pytest.mark.parametrize(
    "bad",
    [{}, None, [], 42, "series", object()],
    ids=["dict", "none", "list", "int", "str", "object"],
)
def test_rejects_malformed_macro_result_container(bad):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator(
            "ZZZ", MacroIndicator.GDP, sources=[_MalformedMacroSource("bad", bad)]
        )
    assert "unexpected result type" in ei.value.attempts[0].reason


def test_malformed_macro_container_failsover_to_backup():
    good = FakeMacroSource(
        "good", {MacroIndicator.GDP: canonical_unit(MacroIndicator.GDP)}
    )
    res = get_indicator(
        "ZZZ",
        MacroIndicator.GDP,
        sources=[_MalformedMacroSource("bad", {}), good],
    )
    assert res.source == "good"


# --------------------------------------------------------------------------- #
# Issue #123 — IndicatorSeries.points keys must be plain datetime.date. A source
# returning str/int/None/datetime keys must be rejected, not accepted or leaked
# as a raw TypeError from the ascending-order compare.
# --------------------------------------------------------------------------- #
class _PointsMacroSource:
    """Returns a well-formed IndicatorSeries except for caller-supplied points."""

    def __init__(self, name, points):
        self.name = name
        self._points = points

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def get_indicator(self, country_iso3, indicator):
        ind = MacroIndicator(indicator)
        return IndicatorSeries(
            country=country_iso3.upper(),
            indicator_code=canonical_indicator_code(ind),
            indicator_name=canonical_indicator_name(ind),
            points=tuple(self._points),
            source=self.name,
            unit=canonical_unit(ind),
            currency=canonical_currency(ind),
            fetched_at_utc=datetime.now(timezone.utc),
        )


@pytest.mark.parametrize(
    "points",
    [
        [("2024-01-01", 1.0)],
        [(datetime(2024, 1, 1, tzinfo=timezone.utc), 1.0)],
        [(datetime(2024, 1, 1), 1.0)],
        [(20240101, 1.0)],
        [(None, 1.0)],
        [(date(2023, 1, 1), 1.0), ("2024-01-01", 2.0)],
    ],
    ids=["str", "aware_datetime", "naive_datetime", "int", "none", "mixed"],
)
def test_rejects_malformed_macro_point_date(points):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_PointsMacroSource("bad", points)])
    assert "malformed point date" in ei.value.attempts[0].reason


def test_malformed_macro_point_date_failsover_to_backup():
    good = FakeMacroSource("good", {MacroIndicator.GDP: canonical_unit(MacroIndicator.GDP)})
    res = get_indicator(
        "ZZZ",
        MacroIndicator.GDP,
        sources=[_PointsMacroSource("bad", [("2024-01-01", 1.0)]), good],
    )
    assert res.source == "good"


def test_accepts_plain_date_macro_points():
    src = _PointsMacroSource("ok", [(date(2022, 1, 1), 1.0), (date(2023, 1, 1), 2.0)])
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[src])
    assert res.source == "ok"
    assert [p[0] for p in res.points] == [date(2022, 1, 1), date(2023, 1, 1)]


# --------------------------------------------------------------------------- #
# Issue #126 — provenance: an IndicatorSeries stamped with a source that is not
# the producing source's name is rejected; failover continues.
# --------------------------------------------------------------------------- #
class _StampMacroSource:
    """Returns a valid IndicatorSeries stamped with an arbitrary `stamped` source."""

    def __init__(self, name, stamped):
        self.name = name
        self._stamped = stamped

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def get_indicator(self, country_iso3, indicator):
        ind = MacroIndicator(indicator)
        return IndicatorSeries(
            country=country_iso3.upper(),
            indicator_code=canonical_indicator_code(ind),
            indicator_name=canonical_indicator_name(ind),
            points=((date(2023, 1, 1), 42.0),),
            source=self._stamped,
            unit=canonical_unit(ind),
            currency=canonical_currency(ind),
            fetched_at_utc=datetime.now(timezone.utc),
        )


def test_rejects_macro_provenance_mismatch_and_failsover():
    bad = _StampMacroSource("real", "claimed_backup")
    good = FakeMacroSource("good", {MacroIndicator.GDP: canonical_unit(MacroIndicator.GDP)})
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[bad, good])
    assert res.source == "good"


def test_macro_provenance_match_is_accepted():
    src = _StampMacroSource("real", "real")
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[src])
    assert res.source == "real"


# Issue #125 (reopen) — malformed macro point shape (reject before unpack).
@pytest.mark.parametrize(
    "points",
    [
        [object()],
        [()],
        [(date(2024, 1, 1), 1.0, 2.0)],
        [{date(2024, 1, 1): 1.0, date(2024, 1, 2): 2.0}],
        ["xy"],
    ],
    ids=["object", "empty_tuple", "3tuple", "dict_2keys", "str2"],
)
def test_rejects_malformed_macro_point_shape(points):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_PointsMacroSource("bad", points)])
    assert "malformed point" in ei.value.attempts[0].reason


def test_malformed_macro_point_shape_failsover_to_backup():
    good = FakeMacroSource("good", {MacroIndicator.GDP: canonical_unit(MacroIndicator.GDP)})
    res = get_indicator(
        "ZZZ", MacroIndicator.GDP, sources=[_PointsMacroSource("bad", [object()]), good]
    )
    assert res.source == "good"


# Issue #127 — present-malformed macro fetched_at_utc rejected (None allowed).
class _TsMacroSource:
    def __init__(self, name, fetched_at_utc):
        self.name = name
        self._ts = fetched_at_utc

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def get_indicator(self, country_iso3, indicator):
        ind = MacroIndicator(indicator)
        return IndicatorSeries(
            country=country_iso3.upper(),
            indicator_code=canonical_indicator_code(ind),
            indicator_name=canonical_indicator_name(ind),
            points=((date(2023, 1, 1), 42.0),),
            source=self.name,
            unit=canonical_unit(ind),
            currency=canonical_currency(ind),
            fetched_at_utc=self._ts,
        )


@pytest.mark.parametrize(
    "bad_ts",
    [datetime(2026, 6, 19, 3), datetime(2026, 6, 19, 10, tzinfo=timezone(timedelta(hours=7))), "2026-06-19T03:00:00Z", 1718766000],
    ids=["naive", "non_utc", "str", "int"],
)
def test_rejects_malformed_macro_fetched_at_utc(bad_ts):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_TsMacroSource("bad", bad_ts)])
    assert "fetched_at_utc" in ei.value.attempts[0].reason


def test_accepts_none_macro_fetched_at_utc():
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[_TsMacroSource("ok", None)])
    assert res.source == "ok"


# Issue #128 — macro warnings must be tuple[str, ...].
class _WarnMacroSource:
    def __init__(self, name, warnings):
        self.name = name
        self._warnings = warnings

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def get_indicator(self, country_iso3, indicator):
        ind = MacroIndicator(indicator)
        return IndicatorSeries(
            country=country_iso3.upper(),
            indicator_code=canonical_indicator_code(ind),
            indicator_name=canonical_indicator_name(ind),
            points=((date(2023, 1, 1), 42.0),),
            source=self.name,
            unit=canonical_unit(ind),
            currency=canonical_currency(ind),
            fetched_at_utc=datetime.now(timezone.utc),
            warnings=self._warnings,
        )


@pytest.mark.parametrize(
    "bad_warnings",
    [None, ["w"], "w", (1,), (None,)],
    ids=["none", "list", "str", "int_member", "none_member"],
)
def test_rejects_malformed_macro_warnings(bad_warnings):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_WarnMacroSource("bad", bad_warnings)])
    assert "warnings" in ei.value.attempts[0].reason


# --------------------------------------------------------------------------- #
# Issue #132 — frequency must be a Frequency enum + point dates consistent.
# Issue #131 — projection_from_year None or int year within the series span.
# --------------------------------------------------------------------------- #
from vnfin.macro.indicators import Frequency  # noqa: E402


class _MetaMacroSource:
    """Returns a valid GDP series with caller-set frequency/points/projection."""

    def __init__(self, name, *, points=((date(2023, 1, 1), 42.0),), frequency=Frequency.ANNUAL, projection_from_year=None):
        self.name = name
        self._points = points
        self._frequency = frequency
        self._pfy = projection_from_year

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def get_indicator(self, country_iso3, indicator):
        ind = MacroIndicator(indicator)
        return IndicatorSeries(
            country=country_iso3.upper(),
            indicator_code=canonical_indicator_code(ind),
            indicator_name=canonical_indicator_name(ind),
            points=tuple(self._points),
            source=self.name,
            unit=canonical_unit(ind),
            currency=canonical_currency(ind),
            frequency=self._frequency,
            projection_from_year=self._pfy,
            fetched_at_utc=datetime.now(timezone.utc),
        )


@pytest.mark.parametrize("bad_freq", ["annual", True, 1, None, []], ids=["str", "bool", "int", "none", "list"])
def test_rejects_malformed_macro_frequency(bad_freq):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_MetaMacroSource("bad", frequency=bad_freq)])
    assert "malformed frequency" in ei.value.attempts[0].reason


@pytest.mark.parametrize(
    "freq,bad_point",
    [
        (Frequency.ANNUAL, date(2023, 6, 15)),
        (Frequency.QUARTERLY, date(2023, 2, 1)),
        (Frequency.MONTHLY, date(2023, 1, 15)),
    ],
    ids=["annual_not_jan1", "quarterly_bad_month", "monthly_not_day1"],
)
def test_rejects_frequency_date_inconsistency(freq, bad_point):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_MetaMacroSource("bad", points=((bad_point, 42.0),), frequency=freq)])
    assert "inconsistent with" in ei.value.attempts[0].reason


@pytest.mark.parametrize(
    "freq,point",
    [
        (Frequency.ANNUAL, date(2023, 1, 1)),
        (Frequency.QUARTERLY, date(2023, 4, 1)),
        (Frequency.MONTHLY, date(2023, 3, 1)),
        (Frequency.DAILY, date(2023, 3, 17)),
    ],
    ids=["annual", "quarterly", "monthly", "daily_any"],
)
def test_accepts_consistent_frequency_dates(freq, point):
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[_MetaMacroSource("ok", points=((point, 42.0),), frequency=freq)])
    assert res.source == "ok"


_SPAN = ((date(2020, 1, 1), 1.0), (date(2021, 1, 1), 2.0), (date(2022, 1, 1), 3.0))


@pytest.mark.parametrize("bad_pfy", [True, 1.5, "2021", [], 2019, 2023], ids=["bool", "float", "str", "list", "before_first", "after_last"])
def test_rejects_malformed_or_out_of_span_projection_year(bad_pfy):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_MetaMacroSource("bad", points=_SPAN, projection_from_year=bad_pfy)])
    assert "projection_from_year" in ei.value.attempts[0].reason


@pytest.mark.parametrize("pfy", [None, 2020, 2021, 2022], ids=["none", "eq_first", "mid", "eq_last"])
def test_accepts_valid_projection_year(pfy):
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[_MetaMacroSource("ok", points=_SPAN, projection_from_year=pfy)])
    assert res.source == "ok"


# --------------------------------------------------------------------------- #
# Issue #134 — macro descriptive metadata: indicator_code/name non-empty str,
# country_name present => str. A truthy non-string (123) must be rejected.
# --------------------------------------------------------------------------- #
_DESC_UNSET = object()  # distinguishes "use canonical default" from explicit None


class _DescMacroSource:
    def __init__(self, name, *, code=_DESC_UNSET, label=_DESC_UNSET, country_name="United States"):
        self.name = name
        self._code = code
        self._label = label
        self._country_name = country_name

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def get_indicator(self, country_iso3, indicator):
        ind = MacroIndicator(indicator)
        return IndicatorSeries(
            country=country_iso3.upper(),
            indicator_code=canonical_indicator_code(ind) if self._code is _DESC_UNSET else self._code,
            indicator_name=canonical_indicator_name(ind) if self._label is _DESC_UNSET else self._label,
            country_name=self._country_name,
            points=((date(2023, 1, 1), 42.0),),
            source=self.name,
            unit=canonical_unit(ind),
            currency=canonical_currency(ind),
            fetched_at_utc=datetime.now(timezone.utc),
        )


@pytest.mark.parametrize("bad", [123, True, [], {}, "", None], ids=["int", "bool", "list", "dict", "blank", "none"])
def test_rejects_malformed_macro_indicator_code(bad):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_DescMacroSource("bad", code=bad)])
    assert "indicator_code" in ei.value.attempts[0].reason


@pytest.mark.parametrize("bad", [123, True, [], {}, "", None], ids=["int", "bool", "list", "dict", "blank", "none"])
def test_rejects_malformed_macro_indicator_name(bad):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_DescMacroSource("bad", label=bad)])
    assert "indicator_name" in ei.value.attempts[0].reason


@pytest.mark.parametrize("bad", [123, True, [], {}], ids=["int", "bool", "list", "dict"])
def test_rejects_malformed_macro_country_name(bad):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_DescMacroSource("bad", country_name=bad)])
    assert "malformed country_name" in ei.value.attempts[0].reason


@pytest.mark.parametrize("cn", ["United States", None, ""], ids=["str", "none", "empty_str"])
def test_accepts_valid_macro_country_name(cn):
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[_DescMacroSource("ok", country_name=cn)])
    assert res.source == "ok"


def test_malformed_macro_descriptive_metadata_failsover_to_backup():
    good = FakeMacroSource("good", {MacroIndicator.GDP: canonical_unit(MacroIndicator.GDP)})
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[_DescMacroSource("bad", code=123), good])
    assert res.source == "good"


# --------------------------------------------------------------------------- #
# Issue #135 — a present unit/value_unit must be a string; a falsey non-string
# ([] / {} / 0 / False) must be rejected, not silently relabeled to canonical.
# --------------------------------------------------------------------------- #
class _UnitMacroSource:
    def __init__(self, name, *, unit=_DESC_UNSET, value_unit=None):
        self.name = name
        self._unit = unit
        self._value_unit = value_unit

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def get_indicator(self, country_iso3, indicator):
        ind = MacroIndicator(indicator)
        return IndicatorSeries(
            country=country_iso3.upper(),
            indicator_code=canonical_indicator_code(ind),
            indicator_name=canonical_indicator_name(ind),
            points=((date(2023, 1, 1), 42.0),),
            source=self.name,
            unit=canonical_unit(ind) if self._unit is _DESC_UNSET else self._unit,
            value_unit=self._value_unit,
            currency=canonical_currency(ind),
            fetched_at_utc=datetime.now(timezone.utc),
        )


@pytest.mark.parametrize("bad", [[], {}, 0, False, 123], ids=["list", "dict", "zero", "false", "int"])
def test_rejects_falsey_nonstring_macro_unit(bad):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_UnitMacroSource("bad", unit=bad)])
    assert "malformed unit" in ei.value.attempts[0].reason


@pytest.mark.parametrize("bad", [[], {}, 0, False, 123], ids=["list", "dict", "zero", "false", "int"])
def test_rejects_falsey_nonstring_macro_value_unit(bad):
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_UnitMacroSource("bad", value_unit=bad)])
    assert "malformed value_unit" in ei.value.attempts[0].reason


def test_accepts_empty_string_macro_unit_placeholder():
    # An empty-string unit is a legitimate placeholder and is relabeled to canonical.
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[_UnitMacroSource("ok", unit="")])
    assert res.source == "ok" and res.unit == canonical_unit(MacroIndicator.GDP)


def test_falsey_nonstring_macro_unit_failsover_to_backup():
    good = FakeMacroSource("good", {MacroIndicator.GDP: canonical_unit(MacroIndicator.GDP)})
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[_UnitMacroSource("bad", unit=[]), good])
    assert res.source == "good"


def test_rejects_none_macro_unit():
    # #135 BLOCK fix: IndicatorSeries.unit is a non-optional str; None must be
    # rejected (not relabeled), unlike the legitimate empty-string placeholder.
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[_UnitMacroSource("bad", unit=None)])
    assert "malformed unit" in ei.value.attempts[0].reason


def test_accepts_none_macro_value_unit():
    # value_unit is Optional[str]; None stays allowed.
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[_UnitMacroSource("ok", value_unit=None)])
    assert res.source == "ok"


# --------------------------------------------------------------------------- #
# Issue #78 (reopen) — returned indicator identity must match the requested
# indicator. Undeclared sources must return CANONICAL code+name; sources that
# declare indicator_identity(country, indicator) are validated against it.
# --------------------------------------------------------------------------- #
def _series(*, code, name, source="s", unit=None, ind=MacroIndicator.GDP):
    return IndicatorSeries(
        country="ZZZ",
        indicator_code=code,
        indicator_name=name,
        points=((date(2023, 1, 1), 42.0),),
        source=source,
        unit=unit if unit is not None else canonical_unit(ind),
        currency=canonical_currency(ind),
        fetched_at_utc=datetime.now(timezone.utc),
    )


class _UndeclaredSource:
    """No indicator_identity -> must return canonical identity (else rejected)."""

    def __init__(self, name, code, label):
        self.name = name
        self._code = code
        self._label = label

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def get_indicator(self, country_iso3, indicator):
        return _series(code=self._code, name=self._label, source=self.name)


def test_undeclared_source_arbitrary_wrong_code_rejected():
    bad = _UndeclaredSource("bad", "WRONG_INDICATOR", canonical_indicator_name(MacroIndicator.GDP))
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[bad])
    assert "indicator_code" in ei.value.attempts[0].reason


def test_undeclared_source_arbitrary_wrong_name_rejected():
    bad = _UndeclaredSource("bad", canonical_indicator_code(MacroIndicator.GDP), "Wrong indicator label")
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[bad])
    assert "indicator_name" in ei.value.attempts[0].reason


def test_undeclared_source_both_wrong_rejected_and_failsover():
    bad = _UndeclaredSource("bad", "X", "Y")
    good = FakeMacroSource("good", {MacroIndicator.GDP: canonical_unit(MacroIndicator.GDP)})
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[bad, good])
    assert res.source == "good"


def test_undeclared_source_canonical_identity_accepted():
    ok = _UndeclaredSource(
        "ok", canonical_indicator_code(MacroIndicator.GDP), canonical_indicator_name(MacroIndicator.GDP)
    )
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[ok])
    assert res.source == "ok"


class _DeclaredSource:
    """Declares indicator_identity -> validated against the declared (code, name)."""

    def __init__(self, name, code, label, *, declared_code=None, declared_name=None):
        self.name = name
        self._code = code
        self._label = label
        self._declared = (declared_code, declared_name)

    def unit_for(self, indicator):
        return canonical_unit(MacroIndicator(indicator))

    def supports(self, indicator):
        return True

    def indicator_identity(self, country_iso3, indicator):
        return self._declared

    def get_indicator(self, country_iso3, indicator):
        return _series(code=self._code, name=self._label, source=self.name)


def test_declared_source_matching_provider_identity_accepted():
    # Provider-specific (non-canonical) code/name accepted because they match the
    # source's own declaration.
    src = _DeclaredSource("wb", "NY.GDP.MKTP.CD", "Fake GDP", declared_code="NY.GDP.MKTP.CD", declared_name="Fake GDP")
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[src])
    assert res.source == "wb" and res.indicator_code == "NY.GDP.MKTP.CD"


def test_declared_source_code_mismatch_rejected():
    src = _DeclaredSource("wb", "WRONG.CODE", "Fake GDP", declared_code="NY.GDP.MKTP.CD", declared_name="Fake GDP")
    with pytest.raises(AllSourcesFailed) as ei:
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[src])
    assert "indicator_code" in ei.value.attempts[0].reason


def test_declared_source_name_none_is_code_only_but_requires_nonempty_name():
    # declared name None -> name is provider-derived; code validated, and a
    # non-empty name is still required by the result guard.
    ok = _DeclaredSource("wb", "NY.GDP.MKTP.CD", "Provider GDP name", declared_code="NY.GDP.MKTP.CD", declared_name=None)
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[ok])
    assert res.source == "wb" and res.indicator_name == "Provider GDP name"

    bad = _DeclaredSource("wb", "NY.GDP.MKTP.CD", "", declared_code="NY.GDP.MKTP.CD", declared_name=None)
    with pytest.raises(AllSourcesFailed):
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[bad])


# --- #179: monthly CPI YoY + SBV policy rate single-source chains -----------

def _dbn_monthly(series_code, periods, values):
    return json.dumps({"series": {"docs": [{
        "series_code": series_code,
        "period_start_day": periods,
        "period": [p[:4] for p in periods],
        "value": values,
    }]}})


def test_cpi_yoy_resolves_dbnomics_only_monthly():
    # only DBnomics maps CPI_YOY -> eligible_sources reduces the default chain to
    # DBnomics -> monthly % YoY by default, no unit-mismatch with the WB/IMF chain.
    dbn_text = _dbn_monthly("M.ZZ.PCPI_PC_CP_A_PT", ["2024-01-01", "2024-02-01"], [3.1, 3.2])
    wb = WorldBankMacroSource(http_get=lambda u, p, h: json.dumps([{"total": 0}, None]))
    imf = IMFDataMapperSource(http_get=lambda u, p, h: json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: dbn_text)
    res = default_macro_client(sources=[wb, imf, dbn]).get_indicator("ZZZ", MacroIndicator.CPI_YOY)
    assert res.source == "dbnomics"
    assert res.unit == "%"
    assert res.currency is None
    assert res.frequency.value == "monthly"


def test_policy_rate_resolves_dbnomics_only_monthly():
    dbn_text = _dbn_monthly("M.ZZ.FPOLM_PA", ["2024-01-01", "2024-02-01"], [5.0, 4.5])
    wb = WorldBankMacroSource(http_get=lambda u, p, h: json.dumps([{"total": 0}, None]))
    imf = IMFDataMapperSource(http_get=lambda u, p, h: json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: dbn_text)
    res = default_macro_client(sources=[wb, imf, dbn]).get_indicator("ZZZ", MacroIndicator.POLICY_RATE)
    assert res.source == "dbnomics"
    assert res.unit == "% per annum"
    assert res.frequency.value == "monthly"


def test_inflation_still_worldbank_annual_after_179():
    # Regression: adding CPI_YOY must NOT divert INFLATION; it still resolves to
    # WorldBank annual % (chain position #1) by default.
    wb_text = json.dumps([
        {"page": 1, "pages": 1, "per_page": 50, "total": 1},
        [{"indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation"},
          "country": {"id": "ZZ", "value": "Fakeland"}, "countryiso3code": "ZZZ",
          "date": "2022", "value": 3.3, "unit": "%", "obs_status": "", "decimal": 1}],
    ])
    wb = WorldBankMacroSource(http_get=lambda u, p, h: wb_text)
    imf = IMFDataMapperSource(http_get=lambda u, p, h: json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: json.dumps({"series": {"docs": []}}))
    res = default_macro_client(sources=[wb, imf, dbn]).get_indicator("ZZZ", MacroIndicator.INFLATION)
    assert res.source == "worldbank"
    assert res.unit == "%"
    assert res.frequency.value == "annual"


def test_series_end_gap_warning_survives_failover_finalize(monkeypatch):
    # Hardening: the monthly series_end_gap warning must survive the full MacroClient
    # path (FailoverClient._finalize), not just the source in isolation. A regression
    # that dropped source warnings in _finalize would be caught here. Pin _today far
    # past the last obs so the gap fires deterministically.
    monkeypatch.setattr("vnfin.macro.dbnomics._today", lambda: date(2026, 6, 1))
    dbn_text = _dbn_monthly("M.ZZ.FPOLM_PA", ["2023-10-01", "2023-11-01", "2023-12-01"], [5.0, 4.5, 4.5])
    wb = WorldBankMacroSource(http_get=lambda u, p, h: json.dumps([{"total": 0}, None]))
    imf = IMFDataMapperSource(http_get=lambda u, p, h: json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: dbn_text)
    res = default_macro_client(sources=[wb, imf, dbn]).get_indicator("ZZZ", MacroIndicator.POLICY_RATE)
    assert res.source == "dbnomics"
    assert any(w.startswith(f"{_SERIES_END_GAP}:") for w in res.warnings)
