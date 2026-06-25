"""Issue #196 — public ANNUAL precious-metals history (silver + platinum).

``vnfin.metals.history(metal, start, end)`` fetches the World Bank Commodity Markets
annual ``.xlsx`` (Pink Sheet) via the SHARED stdlib parser
(:func:`vnfin._contracts.worldbank_cmo.parse_cmo_annual`) and emits one Jan-1-stamped
``MetalBar`` per calendar year as a ``MetalHistory``.

Everything here is synthetic + offline EXCEPT the one committed real-vintage fixture
``tests/fixtures/cmo/CMO-Historical-Data-Annual.xlsx`` (it proves the parser handles the
REAL split-header layout for silver/platinum AND that gold's value-identity is preserved
post-extraction). No network, ever. The synthetic xlsx builder is reused from the gold
test (a copy here so the gold test file stays UNTOUCHED), extended with multiple metal
columns so a wrong column can be fed under a metal's identity (the band test).
"""
from __future__ import annotations

import dataclasses
import io
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceError, SourceUnavailable
from vnfin.gold.worldbank_cmo import WorldBankCmoGoldSource, _parse_cmo_annual_gold
from vnfin.metals import (
    SUPPORTED_METALS,
    MetalBar,
    MetalHistory,
    history,
    source,
)
from vnfin.metals.sources import (
    _PLATINUM_SPEC,
    _SILVER_SPEC,
    WorldBankCmoMetalSource,
)
from vnfin._contracts.worldbank_cmo import MetalSpec, parse_cmo_annual

# OOXML namespaces.
_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cmo" / "CMO-Historical-Data-Annual.xlsx"

# Real-vintage column layout (probed from the committed fixture).
_GOLD_COL = 67
_PLATINUM_COL = 68
_SILVER_COL = 69


# --------------------------------------------------------------------------- #
# Synthetic multi-metal-xlsx builder (stdlib zipfile + hand-written OOXML)      #
# --------------------------------------------------------------------------- #
def _col_letters(idx0: int) -> str:
    """0-based column index -> spreadsheet column letters (0 -> A, 67 -> BP)."""
    n = idx0 + 1
    out = ""
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_cmo_xlsx_metals(
    *,
    sheet_name="Annual Prices (Nominal)",
    columns=None,
    rows=None,
    name_row=7,
    units_row=8,
    data_start_row=9,
    worksheet_target="worksheets/sheet2.xml",
):
    """Build a minimal valid multi-metal CMO-shaped xlsx in memory.

    ``columns`` maps a metal NAME ("Gold"/"Platinum"/"Silver") -> ``(col0, units)``; each
    metal's header is SPLIT (name on ``name_row``, units on ``units_row`` directly below,
    both in its column). ``rows`` maps ``{year: {metal_name: value}}`` (a metal absent from
    a year's dict has no cell that year). Years go in column 0.
    """
    if columns is None:
        columns = {
            "Gold": (_GOLD_COL, "($/troy oz)"),
            "Platinum": (_PLATINUM_COL, "($/troy oz)"),
            "Silver": (_SILVER_COL, "($/troy oz)"),
        }
    if rows is None:
        rows = {2024: {"Silver": 28.27, "Platinum": 955.17, "Gold": 2387.70}}

    shared: list[str] = []
    shared_idx: dict[str, int] = {}

    def _ss(text: str) -> int:
        if text not in shared_idx:
            shared_idx[text] = len(shared)
            shared.append(text)
        return shared_idx[text]

    title_idx = _ss("World Bank Commodity Price Data (The Pink Sheet)")

    def _cell(col0: int, row: int, value, *, shared_string=False):
        ref = f"{_col_letters(col0)}{row}"
        if shared_string:
            return f'<c r="{ref}" t="s"><v>{value}</v></c>'
        return f'<c r="{ref}"><v>{value}</v></c>'

    rows_xml: list[str] = []
    rows_xml.append(f'<row r="1">{_cell(0, 1, title_idx, shared_string=True)}</row>')

    # name row
    name_cells = [
        _cell(col, name_row, _ss(metal), shared_string=True)
        for metal, (col, _units) in columns.items()
    ]
    rows_xml.append(f'<row r="{name_row}">{"".join(name_cells)}</row>')

    # units row (directly below)
    units_cells = [
        _cell(col, units_row, _ss(units), shared_string=True)
        for _metal, (col, units) in columns.items()
    ]
    rows_xml.append(f'<row r="{units_row}">{"".join(units_cells)}</row>')

    # data rows: year in col 0, each metal value in its column
    r = data_start_row
    for year in sorted(rows):
        per_metal = rows[year]
        cells = [_cell(0, r, year)]
        for metal, (col, _units) in columns.items():
            if metal in per_metal and per_metal[metal] is not None:
                cells.append(_cell(col, r, per_metal[metal]))
        rows_xml.append(f'<row r="{r}">{"".join(cells)}</row>')
        r += 1

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{_NS}"><sheetData>{"".join(rows_xml)}</sheetData></worksheet>'
    )
    si_xml = "".join(f"<si><t>{_xml_escape(s)}</t></si>" for s in shared)
    shared_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="{_NS}" count="{len(shared)}" uniqueCount="{len(shared)}">'
        f"{si_xml}</sst>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<workbook xmlns="{_NS}" xmlns:r="{_REL_NS}"><sheets>'
        '<sheet name="AFOSHEET" sheetId="22" state="hidden" r:id="rId1"/>'
        f'<sheet name="{_xml_escape(sheet_name)}" sheetId="26" r:id="rId2"/>'
        "</sheets></workbook>"
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="{worksheet_target}"/>'
        '<Relationship Id="rId12" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        "</Relationships>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    empty_sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{_NS}"><sheetData/></worksheet>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", workbook_xml)
        z.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        z.writestr("xl/sharedStrings.xml", shared_xml)
        z.writestr("xl/worksheets/sheet1.xml", empty_sheet)
        z.writestr(f"xl/{worksheet_target}", sheet_xml)
    return buf.getvalue()


def _serve(raw: bytes, calls=None):
    """An http_get that returns the xlsx bytes for the CMO URL (records calls if given)."""

    def _get(url, params=None, headers=None):
        if calls is not None:
            calls.append(url)
        assert "worldbank.org" in url
        return raw

    return _get


# --------------------------------------------------------------------------- #
# 1. Parse correctness (real fixture) + gold value-identity regression          #
# --------------------------------------------------------------------------- #
def test_real_fixture_silver_parses_correctly():
    raw = REAL_FIXTURE.read_bytes()
    src = WorldBankCmoMetalSource("silver", http_get=_serve(raw))
    out = src.get_history(date(2024, 1, 1), date(2025, 12, 31))
    by_year = {b.date.year: b.price for b in out.bars}
    assert out.product == "XAG"
    assert by_year[2025] == pytest.approx(39.80, abs=0.01)
    assert by_year[2024] == pytest.approx(28.27, abs=0.01)


def test_real_fixture_platinum_parses_correctly():
    raw = REAL_FIXTURE.read_bytes()
    out = history("platinum", date(2024, 1, 1), date(2025, 12, 31), http_get=_serve(raw))
    by_year = {b.date.year: b.price for b in out.bars}
    assert out.product == "XPT"
    assert by_year[2025] == pytest.approx(1278.29, abs=0.01)
    assert by_year[2024] == pytest.approx(955.17, abs=0.01)


def test_real_fixture_via_product_code_alias():
    raw = REAL_FIXTURE.read_bytes()
    out = history("XAG", date(2025, 1, 1), date(2025, 12, 31), http_get=_serve(raw))
    assert out.product == "XAG"
    assert out.bars[0].price == pytest.approx(39.80, abs=0.01)


def test_gold_value_identity_preserved_post_extraction():
    # gate (a): the gold source's parsed values must be byte-identical to the shared
    # parser path after the extraction. Assert the GOLD source output AND that the gold
    # delegator and the shared parser agree on the same dict (no drift in the move).
    raw = REAL_FIXTURE.read_bytes()
    gold_src = WorldBankCmoGoldSource(http_get=_serve(raw))
    out = gold_src.get_history(date(2024, 1, 1), date(2025, 12, 31))
    by_year = {b.date.year: b.price for b in out.bars}
    assert out.product == "XAU"
    assert by_year[2025] == pytest.approx(3441.51, abs=0.01)
    assert by_year[2024] == pytest.approx(2387.70, abs=0.01)
    # the delegator and the shared parser with the gold spec produce the same dict
    gold_spec = MetalSpec(product="XAU", name_row="Gold", min_usd_oz=20.0, max_usd_oz=10000.0)
    assert _parse_cmo_annual_gold(raw) == parse_cmo_annual(raw, gold_spec)


# --------------------------------------------------------------------------- #
# 2. Band RED on the band (gate b) — prove RED by widening, not ImportError      #
# --------------------------------------------------------------------------- #
def test_silver_band_rejects_gold_magnitude_column_at_parser():
    # PARSER level (gate b): feed gold's recent value (3441.51) UNDER the "Silver" header
    # -> 3441.51 > 75 ceiling -> InvalidData directly (the band rejects by magnitude).
    raw = _build_cmo_xlsx_metals(
        rows={2024: {"Silver": 3441.51, "Platinum": 955.17, "Gold": 2387.70}}
    )
    with pytest.raises(InvalidData):
        parse_cmo_annual(raw, _SILVER_SPEC)


def test_silver_band_rejection_surfaces_as_source_error():
    # SOURCE level: the parser's band InvalidData on the only URL exhausts _CMO_ANNUAL_URLS
    # -> surfaces as SourceUnavailable (a SourceError subclass; mirrors gold's discipline).
    raw = _build_cmo_xlsx_metals(
        rows={2024: {"Silver": 3441.51, "Platinum": 955.17, "Gold": 2387.70}}
    )
    with pytest.raises(SourceError):
        history("silver", date(2024, 1, 1), date(2024, 12, 31), http_get=_serve(raw))


def test_platinum_band_rejects_silver_magnitude_column_at_parser():
    # Feed silver's value (39.80) UNDER the "Platinum" header -> 39.80 < 50 floor ->
    # InvalidData directly at the parser.
    raw = _build_cmo_xlsx_metals(
        rows={2024: {"Platinum": 39.80, "Silver": 28.27, "Gold": 2387.70}}
    )
    with pytest.raises(InvalidData):
        parse_cmo_annual(raw, _PLATINUM_SPEC)


def test_platinum_band_rejection_surfaces_as_source_error():
    raw = _build_cmo_xlsx_metals(
        rows={2024: {"Platinum": 39.80, "Silver": 28.27, "Gold": 2387.70}}
    )
    with pytest.raises(SourceError):
        history("platinum", date(2024, 1, 1), date(2024, 12, 31), http_get=_serve(raw))


def test_band_is_the_reason_widening_would_let_it_through():
    # Proof the band (not some other guard) is what rejects: the SAME 3441.51 value parses
    # fine when fed through a spec whose band is widened to [0, 1e9]. If the test went
    # green for any reason OTHER than the band, this in-band parse would also fail.
    raw = _build_cmo_xlsx_metals(rows={2024: {"Silver": 3441.51}})
    wide = MetalSpec(product="XAG", name_row="Silver", min_usd_oz=0.0, max_usd_oz=1e9)
    out = parse_cmo_annual(raw, wide)
    assert out == {2024: 3441.51}
    # and the production silver spec rejects exactly the same bytes on the band
    with pytest.raises(InvalidData):
        parse_cmo_annual(raw, _SILVER_SPEC)


def test_in_band_value_parses_for_each_metal():
    # A value comfortably INSIDE each metal's band parses (the band is not over-tight).
    raw_ag = _build_cmo_xlsx_metals(rows={2024: {"Silver": 39.80}})
    assert parse_cmo_annual(raw_ag, _SILVER_SPEC) == {2024: 39.80}
    raw_pt = _build_cmo_xlsx_metals(rows={2024: {"Platinum": 1278.29}})
    assert parse_cmo_annual(raw_pt, _PLATINUM_SPEC) == {2024: 1278.29}


# --------------------------------------------------------------------------- #
# 3. Unsupported metal / gold-routing (gate d) — BEFORE any network             #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("metal", ["palladium", "XPD", "copper", "", "  ", None, 7])
def test_unsupported_metal_raises_before_network(metal):
    calls = []
    raw = _build_cmo_xlsx_metals()
    with pytest.raises(InvalidData):
        history(metal, date(2024, 1, 1), date(2024, 12, 31), http_get=_serve(raw, calls))
    assert calls == []  # never reached the network


def test_unsupported_metal_message_names_the_metal():
    with pytest.raises(InvalidData) as exc:
        history("palladium", date(2024, 1, 1), date(2024, 12, 31), http_get=lambda *a, **k: b"")
    assert "palladium" in str(exc.value)


def test_gold_routes_to_vnfin_gold():
    calls = []
    raw = _build_cmo_xlsx_metals()
    with pytest.raises(InvalidData) as exc:
        history("gold", date(2024, 1, 1), date(2024, 12, 31), http_get=_serve(raw, calls))
    msg = str(exc.value)
    assert "vnfin.gold" in msg
    assert calls == []  # routed before any network


def test_gold_code_xau_also_routes_to_vnfin_gold():
    with pytest.raises(InvalidData) as exc:
        history("XAU", date(2024, 1, 1), date(2024, 12, 31), http_get=lambda *a, **k: b"")
    assert "vnfin.gold" in str(exc.value)


# --------------------------------------------------------------------------- #
# 4. Result metadata (never-silent)                                            #
# --------------------------------------------------------------------------- #
def test_result_metadata_is_never_silent():
    raw = _build_cmo_xlsx_metals(rows={2024: {"Silver": 28.27}})
    out = history("silver", date(2024, 1, 1), date(2024, 12, 31), http_get=_serve(raw))
    assert isinstance(out, MetalHistory)
    assert out.product in ("XAG", "XPT")
    assert out.unit == "USD/oz"
    assert out.value_unit == "USD/oz"
    assert out.currency == "USD"
    assert out.source == "worldbank_cmo_metal"
    assert out.frequency == "annual"
    assert out.attribution.startswith("Source: The World Bank")
    assert out.fetched_at_utc is not None and out.fetched_at_utc.tzinfo is not None


def test_history_emits_one_bar_per_year_jan1():
    raw = _build_cmo_xlsx_metals(rows={2024: {"Silver": 28.27}})
    out = history("silver", date(2024, 3, 5), date(2024, 9, 9), http_get=_serve(raw))
    assert len(out.bars) == 1
    assert out.bars[0].date == date(2024, 1, 1)


def test_history_filters_to_requested_year_span():
    raw = _build_cmo_xlsx_metals(
        rows={2022: {"Silver": 21.7}, 2023: {"Silver": 23.3}, 2024: {"Silver": 28.27}}
    )
    out = history("silver", date(2023, 6, 1), date(2024, 6, 1), http_get=_serve(raw))
    assert [b.date.year for b in out.bars] == [2023, 2024]


# --------------------------------------------------------------------------- #
# 5. Column-absent vintage (gate d) — never relabel another metal's column      #
# --------------------------------------------------------------------------- #
def test_silver_column_absent_raises_naming_silver_at_parser():
    # A sheet with Gold + Platinum but NO Silver column: the PARSER raises InvalidData
    # naming Silver (never relabels gold's/platinum's column as silver).
    raw = _build_cmo_xlsx_metals(
        columns={
            "Gold": (_GOLD_COL, "($/troy oz)"),
            "Platinum": (_PLATINUM_COL, "($/troy oz)"),
        },
        rows={2024: {"Gold": 2387.70, "Platinum": 955.17}},
    )
    with pytest.raises((InvalidData, EmptyData)) as exc:
        parse_cmo_annual(raw, _SILVER_SPEC)
    assert "Silver" in str(exc.value)


def test_silver_column_absent_message_names_silver_at_source():
    # SOURCE level: the column-absent InvalidData surfaces as SourceUnavailable whose
    # aggregated message still names Silver (so the failure is diagnosable per metal).
    raw = _build_cmo_xlsx_metals(
        columns={
            "Gold": (_GOLD_COL, "($/troy oz)"),
            "Platinum": (_PLATINUM_COL, "($/troy oz)"),
        },
        rows={2024: {"Gold": 2387.70, "Platinum": 955.17}},
    )
    with pytest.raises(SourceError) as exc:
        history("silver", date(2024, 1, 1), date(2024, 12, 31), http_get=_serve(raw))
    assert "Silver" in str(exc.value)


def test_column_absent_surfaces_as_source_error():
    raw = _build_cmo_xlsx_metals(
        columns={"Platinum": (_PLATINUM_COL, "($/troy oz)")},
        rows={2024: {"Platinum": 955.17}},
    )
    src = WorldBankCmoMetalSource("silver", http_get=_serve(raw))
    with pytest.raises(SourceError):
        src.get_history(date(2024, 1, 1), date(2024, 12, 31))


def test_empty_span_raises_empty_data():
    raw = _build_cmo_xlsx_metals(rows={2020: {"Silver": 20.5}})
    src = WorldBankCmoMetalSource("silver", http_get=_serve(raw))
    with pytest.raises(EmptyData):
        src.get_history(date(2030, 1, 1), date(2030, 12, 31))


# --------------------------------------------------------------------------- #
# Source — fail-closed bounds + transport discipline (parity with gold)         #
# --------------------------------------------------------------------------- #
def test_inverted_range_raises_before_network():
    calls = []
    raw = _build_cmo_xlsx_metals()
    src = WorldBankCmoMetalSource("silver", http_get=_serve(raw, calls))
    with pytest.raises(InvalidData):
        src.get_history(date(2024, 1, 1), date(2020, 1, 1))
    assert calls == []


def test_transport_failure_maps_to_source_unavailable():
    def _get(url, params=None, headers=None):
        raise ConnectionError("blocked")

    src = WorldBankCmoMetalSource("platinum", http_get=_get)
    with pytest.raises(SourceUnavailable):
        src.get_history(date(2000, 1, 1), date(2024, 12, 31))


def test_anti_bot_html_maps_to_source_unavailable():
    src = WorldBankCmoMetalSource("silver", http_get=lambda *a, **k: b"<html>blocked</html>")
    with pytest.raises(SourceUnavailable):
        src.get_history(date(2000, 1, 1), date(2024, 12, 31))


# --------------------------------------------------------------------------- #
# 6. Frozen + df + facade exports                                              #
# --------------------------------------------------------------------------- #
def test_metal_bar_and_history_are_frozen():
    bar = MetalBar(date=date(2024, 1, 1), price=28.27)
    with pytest.raises(dataclasses.FrozenInstanceError):
        bar.price = 1.0  # type: ignore[misc]
    hist = MetalHistory(
        product="XAG",
        unit="USD/oz",
        currency="USD",
        source="worldbank_cmo_metal",
        bars=(bar,),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        hist.product = "XPT"  # type: ignore[misc]
    # value_unit mirrors unit when omitted
    assert hist.value_unit == "USD/oz"
    assert hist.frequency == "annual"


def test_to_dataframe_yields_date_price_rows():
    pd = pytest.importorskip("pandas")
    raw = _build_cmo_xlsx_metals(
        rows={2023: {"Silver": 23.3}, 2024: {"Silver": 28.27}}
    )
    out = history("silver", date(2023, 1, 1), date(2024, 12, 31), http_get=_serve(raw))
    df = out.to_dataframe()
    assert list(df.columns) == ["price"]
    assert df.index.name == "date"
    assert df.loc[date(2024, 1, 1), "price"] == pytest.approx(28.27)
    assert df.attrs["product"] == "XAG"
    assert df.attrs["frequency"] == "annual"


def test_facade_exports_and_supported_metals():
    assert SUPPORTED_METALS == ("silver", "platinum")
    s = source("silver", http_get=lambda *a, **k: b"")
    assert isinstance(s, WorldBankCmoMetalSource)
    assert s.NAME == "worldbank_cmo_metal"


def test_iter_and_len_over_bars():
    raw = _build_cmo_xlsx_metals(
        rows={2022: {"Silver": 21.7}, 2023: {"Silver": 23.3}, 2024: {"Silver": 28.27}}
    )
    out = history("silver", date(2022, 1, 1), date(2024, 12, 31), http_get=_serve(raw))
    assert len(out) == 3
    assert [b.date.year for b in out] == [2022, 2023, 2024]
