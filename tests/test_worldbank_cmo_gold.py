"""Issue #185 — World Bank CMO "Pink Sheet" annual gold source.

``WorldBankCmoGoldSource`` fetches the World Bank Commodity Markets annual ``.xlsx``
(Pink Sheet historical data) and parses it with a SCOPED stdlib OOXML reader (stdlib
``zipfile`` + ``xml.etree`` only — no openpyxl/pandas) into an annual XAU/USD gold
series, then emits one Jan-1-stamped ``GoldBar`` per calendar year.

Everything here is synthetic + offline EXCEPT the one committed real-vintage fixture
``tests/fixtures/cmo/CMO-Historical-Data-Annual.xlsx`` (the highest-value test — it
proves the parser handles the REAL split-header layout). No network, ever.
"""
from __future__ import annotations

import io
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from vnfin.exceptions import (
    EmptyData,
    InvalidData,
    SourceError,
    SourceUnavailable,
)
from vnfin.gold.models import GoldHistory
from vnfin.gold.worldbank_cmo import (
    _CMO_ANNUAL_URLS,
    WorldBankCmoGoldSource,
    _parse_cmo_annual_gold,
)

# OOXML namespaces.
_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cmo" / "CMO-Historical-Data-Annual.xlsx"


# --------------------------------------------------------------------------- #
# Synthetic minimal-xlsx builder (stdlib zipfile + hand-written OOXML)          #
# --------------------------------------------------------------------------- #
def _col_letters(idx0: int) -> str:
    """0-based column index -> spreadsheet column letters (0 -> A, 67 -> BP)."""
    n = idx0 + 1
    out = ""
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def _build_cmo_xlsx(
    *,
    sheet_name="Annual Prices (Nominal)",
    gold_name="Gold",
    gold_units="($/troy oz)",
    gold_col=67,
    rows=None,
    name_row=7,
    units_row=8,
    data_start_row=9,
    include_gold_name=True,
    include_gold_units=True,
    worksheet_target="worksheets/sheet2.xml",
    extra_year_cols=True,
):
    """Build a minimal valid CMO-shaped xlsx in memory.

    ``rows`` is {year: gold_value}. The gold header is SPLIT: ``gold_name`` on
    ``name_row`` and ``gold_units`` on ``units_row`` directly below, both in
    ``gold_col``. Year goes in column 0. Numeric cells are stored as RAW numbers
    (no ``t`` attr); header cells are shared strings (``t="s"``).
    """
    if rows is None:
        rows = {2022: 1800.0, 2023: 1942.67, 2024: 2387.70}

    # --- shared strings (only the text/header cells) ---
    shared: list[str] = []
    shared_idx: dict[str, int] = {}

    def _ss(text: str) -> int:
        if text not in shared_idx:
            shared_idx[text] = len(shared)
            shared.append(text)
        return shared_idx[text]

    title_idx = _ss("World Bank Commodity Price Data (The Pink Sheet)")
    gold_name_idx = _ss(gold_name) if include_gold_name else None
    gold_units_idx = _ss(gold_units) if include_gold_units else None
    # A sibling column to stress the BOTH-cell match (same units, different name).
    plat_name_idx = _ss("Platinum")
    plat_units_idx = _ss("($/troy oz)")

    # --- worksheet sheetData ---
    def _cell(col0: int, row: int, value, *, shared_string=False):
        ref = f"{_col_letters(col0)}{row}"
        if shared_string:
            return f'<c r="{ref}" t="s"><v>{value}</v></c>'
        return f'<c r="{ref}"><v>{value}</v></c>'

    plat_col = gold_col + 2  # a distinct neighbor column

    rows_xml: list[str] = []
    # title row
    rows_xml.append(f'<row r="1">{_cell(0, 1, title_idx, shared_string=True)}</row>')

    # name row (headers)
    name_cells = []
    if include_gold_name and gold_name_idx is not None:
        name_cells.append(_cell(gold_col, name_row, gold_name_idx, shared_string=True))
    name_cells.append(_cell(plat_col, name_row, plat_name_idx, shared_string=True))
    rows_xml.append(f'<row r="{name_row}">{"".join(name_cells)}</row>')

    # units row (directly below)
    units_cells = []
    if include_gold_units and gold_units_idx is not None:
        units_cells.append(_cell(gold_col, units_row, gold_units_idx, shared_string=True))
    units_cells.append(_cell(plat_col, units_row, plat_units_idx, shared_string=True))
    rows_xml.append(f'<row r="{units_row}">{"".join(units_cells)}</row>')

    # data rows: year in col 0 (raw number), gold value in gold_col (raw number)
    r = data_start_row
    for year in sorted(rows):
        val = rows[year]
        cells = [_cell(0, r, year)]
        if val is not None:
            cells.append(_cell(gold_col, r, val))
        # a platinum value too (raw number) for realism
        cells.append(_cell(plat_col, r, 950.0))
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

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _ROOT_RELS)
        z.writestr("xl/workbook.xml", workbook_xml)
        z.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        z.writestr("xl/sharedStrings.xml", shared_xml)
        # always write a sheet1 stub + the target worksheet
        z.writestr("xl/worksheets/sheet1.xml", _EMPTY_SHEET)
        z.writestr(f"xl/{worksheet_target}", sheet_xml)
    return buf.getvalue()


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    "</Types>"
)
_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    "</Relationships>"
)
_EMPTY_SHEET = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<worksheet xmlns="{_NS}"><sheetData/></worksheet>'
)


# --------------------------------------------------------------------------- #
# Parser — happy path + split-header matching                                  #
# --------------------------------------------------------------------------- #
def test_parser_reads_year_to_gold_by_split_header():
    raw = _build_cmo_xlsx(rows={2022: 1800.0, 2023: 1900.0, 2024: 2000.0})
    out = _parse_cmo_annual_gold(raw)
    assert out == {2022: 1800.0, 2023: 1900.0, 2024: 2000.0}


def test_parser_finds_gold_column_when_shifted():
    # The gold column index shifts between vintages; parser must locate it by the
    # split-header TEXT, never a hard-coded index.
    raw = _build_cmo_xlsx(gold_col=12, rows={2020: 1700.0, 2021: 1800.0})
    out = _parse_cmo_annual_gold(raw)
    assert out == {2020: 1700.0, 2021: 1800.0}


def test_parser_resolves_worksheet_via_rels_not_hardcoded():
    # Point the sheet rels at a non-sheet2 target; the parser must follow the rels.
    raw = _build_cmo_xlsx(worksheet_target="worksheets/sheet9.xml", rows={2021: 1800.0})
    out = _parse_cmo_annual_gold(raw)
    assert out == {2021: 1800.0}


def test_parser_rejects_dotdot_worksheet_target():
    # A crafted rels Target containing ".." must NOT divert the read to a
    # differently-named "xl/../..." zip member. The relative reference is resolved
    # (collapsing "." / ".." per the OOXML/RFC-3986 rules) and validated against the
    # real parts, so an out-of-band member fails safe as InvalidData rather than being
    # parsed silently. (_build_cmo_xlsx writes the worksheet at the literal
    # "xl/../evil/sheet.xml" member, which the unnormalized resolver would have read.)
    raw = _build_cmo_xlsx(worksheet_target="../evil/sheet.xml", rows={2021: 1800.0})
    with pytest.raises(InvalidData):
        _parse_cmo_annual_gold(raw)


# --------------------------------------------------------------------------- #
# Parser — robustness (each -> InvalidData)                                    #
# --------------------------------------------------------------------------- #
def test_parser_missing_gold_name_cell_raises_invalid():
    raw = _build_cmo_xlsx(include_gold_name=False)
    with pytest.raises(InvalidData):
        _parse_cmo_annual_gold(raw)


def test_parser_missing_units_cell_raises_invalid():
    raw = _build_cmo_xlsx(include_gold_units=False)
    with pytest.raises(InvalidData):
        _parse_cmo_annual_gold(raw)


def test_parser_units_mismatch_does_not_match_gold_column():
    # "Gold" present but its units cell is NOT ($/troy oz) -> must NOT match (guards
    # against a non-troy-oz gold column) -> InvalidData.
    raw = _build_cmo_xlsx(gold_units="($/mt)")
    with pytest.raises(InvalidData):
        _parse_cmo_annual_gold(raw)


def test_parser_sheet_not_found_raises_invalid():
    raw = _build_cmo_xlsx(sheet_name="Some Other Sheet")
    with pytest.raises(InvalidData):
        _parse_cmo_annual_gold(raw)


def test_parser_no_data_rows_raises_invalid():
    raw = _build_cmo_xlsx(rows={})
    with pytest.raises(InvalidData):
        _parse_cmo_annual_gold(raw)


def test_parser_non_numeric_price_raises_invalid():
    # Inject a non-numeric gold value via a hand-built sheet.
    raw = _build_cmo_xlsx(rows={2022: 1800.0})
    # Corrupt the gold value cell by rebuilding with a string price.
    bad = _build_cmo_xlsx_with_text_gold_value(2022, "not-a-number")
    with pytest.raises(InvalidData):
        _parse_cmo_annual_gold(bad)


def test_parser_non_xlsx_body_raises_invalid():
    for body in (b"", b"<html>blocked</html>", b"PK\x03\x04truncated-not-a-zip"):
        with pytest.raises(InvalidData):
            _parse_cmo_annual_gold(body)


def _build_cmo_xlsx_with_text_gold_value(year: int, text_value: str) -> bytes:
    """A CMO xlsx whose single gold data cell is a shared-string (text) value rather
    than a raw number — exercises the non-numeric-price guard."""
    gold_col = 67
    plat_col = gold_col + 2
    shared = [
        "World Bank Commodity Price Data (The Pink Sheet)",  # 0
        "Gold",  # 1
        "($/troy oz)",  # 2
        "Platinum",  # 3
        "($/troy oz)",  # 4
        text_value,  # 5
    ]

    def _cell(col0, row, value, ss=False):
        ref = f"{_col_letters(col0)}{row}"
        return f'<c r="{ref}" t="s"><v>{value}</v></c>' if ss else f'<c r="{ref}"><v>{value}</v></c>'

    rows_xml = [
        f'<row r="1">{_cell(0, 1, 0, ss=True)}</row>',
        f'<row r="7">{_cell(gold_col, 7, 1, ss=True)}{_cell(plat_col, 7, 3, ss=True)}</row>',
        f'<row r="8">{_cell(gold_col, 8, 2, ss=True)}{_cell(plat_col, 8, 4, ss=True)}</row>',
        # data row: year raw, gold value as shared-string text
        f'<row r="9">{_cell(0, 9, year)}{_cell(gold_col, 9, 5, ss=True)}</row>',
    ]
    sheet_xml = (
        '<?xml version="1.0"?>'
        f'<worksheet xmlns="{_NS}"><sheetData>{"".join(rows_xml)}</sheetData></worksheet>'
    )
    si_xml = "".join(f"<si><t>{_xml_escape(s)}</t></si>" for s in shared)
    shared_xml = f'<sst xmlns="{_NS}">{si_xml}</sst>'
    workbook_xml = (
        f'<workbook xmlns="{_NS}" xmlns:r="{_REL_NS}"><sheets>'
        '<sheet name="Annual Prices (Nominal)" sheetId="26" r:id="rId2"/>'
        "</sheets></workbook>"
    )
    rels_xml = (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
        '<Relationship Id="rId12" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        "</Relationships>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/workbook.xml", workbook_xml)
        z.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        z.writestr("xl/sharedStrings.xml", shared_xml)
        z.writestr("xl/worksheets/sheet2.xml", sheet_xml)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Parser — N1 magnitude guard + integrity guards (each -> InvalidData)         #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad", [0.0, -50.0, 19.99, 10000.01, 100000.0])
def test_parser_rejects_out_of_band_or_non_positive(bad):
    raw = _build_cmo_xlsx(rows={2022: 1800.0, 2023: bad})
    with pytest.raises(InvalidData):
        _parse_cmo_annual_gold(raw)


@pytest.mark.parametrize("ok", [20.0, 35.27, 3441.51, 10000.0])
def test_parser_accepts_in_band_values(ok):
    raw = _build_cmo_xlsx(rows={2022: ok})
    out = _parse_cmo_annual_gold(raw)
    assert out == {2022: ok}


# --------------------------------------------------------------------------- #
# Source — get_history happy path + contract                                   #
# --------------------------------------------------------------------------- #
def _serve(raw: bytes):
    """An http_get that returns the xlsx bytes for the CMO URL."""

    def _get(url, params=None, headers=None):
        assert "worldbank.org" in url
        return raw

    return _get


def test_source_name_and_class_attr():
    src = WorldBankCmoGoldSource(http_get=lambda *a, **k: b"")
    assert src.NAME == "worldbank_cmo_gold"
    assert src.name == "worldbank_cmo_gold"


def test_get_history_returns_annual_gold_history():
    raw = _build_cmo_xlsx(rows={2020: 1700.0, 2021: 1800.0, 2022: 1900.0})
    src = WorldBankCmoGoldSource(http_get=_serve(raw))
    out = src.get_history(date(2020, 1, 1), date(2022, 12, 31))
    assert isinstance(out, GoldHistory)
    assert out.product == "XAU"
    assert out.unit == "USD/oz" and out.value_unit == "USD/oz"
    assert out.currency == "USD"
    assert out.source == "worldbank_cmo_gold"
    assert [b.date for b in out.bars] == [date(2020, 1, 1), date(2021, 1, 1), date(2022, 1, 1)]
    assert [b.price for b in out.bars] == [1700.0, 1800.0, 1900.0]
    assert out.fetched_at_utc is not None and out.fetched_at_utc.tzinfo is not None


def test_get_history_filters_to_requested_year_span():
    raw = _build_cmo_xlsx(rows={2018: 1300.0, 2019: 1400.0, 2020: 1700.0, 2021: 1800.0})
    src = WorldBankCmoGoldSource(http_get=_serve(raw))
    out = src.get_history(date(2019, 6, 1), date(2020, 6, 1))
    # inclusive calendar-year window -> 2019 and 2020 only
    assert [b.date.year for b in out.bars] == [2019, 2020]


def test_get_history_emits_one_bar_per_year_jan1():
    raw = _build_cmo_xlsx(rows={2021: 1800.0})
    src = WorldBankCmoGoldSource(http_get=_serve(raw))
    out = src.get_history(date(2021, 3, 5), date(2021, 9, 9))
    assert len(out.bars) == 1
    assert out.bars[0].date == date(2021, 1, 1)


def test_get_history_empty_span_raises_empty_data():
    raw = _build_cmo_xlsx(rows={2020: 1700.0, 2021: 1800.0})
    src = WorldBankCmoGoldSource(http_get=_serve(raw))
    with pytest.raises(EmptyData):
        src.get_history(date(2025, 1, 1), date(2025, 12, 31))


# --------------------------------------------------------------------------- #
# Source — fail-closed bounds BEFORE any network call                          #
# --------------------------------------------------------------------------- #
def test_get_history_inverted_range_raises_before_network():
    calls = []

    def _get(url, params=None, headers=None):
        calls.append(url)
        return b""

    src = WorldBankCmoGoldSource(http_get=_get)
    with pytest.raises(InvalidData):
        src.get_history(date(2024, 1, 1), date(2020, 1, 1))
    assert calls == []  # no network call happened


def test_get_history_requires_both_bounds():
    src = WorldBankCmoGoldSource(http_get=lambda *a, **k: b"")
    with pytest.raises(InvalidData):
        src.get_history(None, date(2024, 1, 1))


# --------------------------------------------------------------------------- #
# Source — transport / URL-fallback / error mapping (N2 discipline)            #
# --------------------------------------------------------------------------- #
def test_get_history_transport_failure_maps_to_source_unavailable():
    def _get(url, params=None, headers=None):
        raise ConnectionError("blocked")

    src = WorldBankCmoGoldSource(http_get=_get)
    with pytest.raises(SourceUnavailable):
        src.get_history(date(2020, 1, 1), date(2024, 12, 31))


def test_get_history_anti_bot_html_maps_to_source_unavailable():
    # A non-xlsx HTML body on the only URL -> all URLs exhausted -> SourceUnavailable.
    src = WorldBankCmoGoldSource(http_get=lambda *a, **k: b"<html>blocked</html>")
    with pytest.raises(SourceUnavailable):
        src.get_history(date(2020, 1, 1), date(2024, 12, 31))


def test_get_history_url_fallback_first_raises_second_serves(monkeypatch):
    raw = _build_cmo_xlsx(rows={2021: 1800.0})
    url_a = "https://thedocs.worldbank.org/en/doc/AAAA-0050012026/related/CMO-old.xlsx"
    url_b = "https://thedocs.worldbank.org/en/doc/BBBB-0050012026/related/CMO-new.xlsx"
    monkeypatch.setattr(
        "vnfin.gold.worldbank_cmo._CMO_ANNUAL_URLS", (url_a, url_b)
    )

    def _get(url, params=None, headers=None):
        if url == url_a:
            raise ConnectionError("first vintage 404")
        if url == url_b:
            return raw
        raise AssertionError(f"unexpected url {url}")

    src = WorldBankCmoGoldSource(http_get=_get)
    out = src.get_history(date(2021, 1, 1), date(2021, 12, 31))
    assert [b.date.year for b in out.bars] == [2021]


def test_get_history_url_fallback_first_serves_non_xlsx_second_serves(monkeypatch):
    # First URL returns a non-xlsx body (parse failure) -> try next.
    raw = _build_cmo_xlsx(rows={2021: 1800.0})
    url_a = "https://thedocs.worldbank.org/en/doc/AAAA-0050012026/related/CMO-old.xlsx"
    url_b = "https://thedocs.worldbank.org/en/doc/BBBB-0050012026/related/CMO-new.xlsx"
    monkeypatch.setattr(
        "vnfin.gold.worldbank_cmo._CMO_ANNUAL_URLS", (url_a, url_b)
    )

    def _get(url, params=None, headers=None):
        return b"<html>not xlsx</html>" if url == url_a else raw

    src = WorldBankCmoGoldSource(http_get=_get)
    out = src.get_history(date(2021, 1, 1), date(2021, 12, 31))
    assert [b.date.year for b in out.bars] == [2021]


def test_get_history_all_urls_fail_raises_source_unavailable(monkeypatch):
    url_a = "https://thedocs.worldbank.org/en/doc/AAAA/related/CMO-a.xlsx"
    url_b = "https://thedocs.worldbank.org/en/doc/BBBB/related/CMO-b.xlsx"
    monkeypatch.setattr("vnfin.gold.worldbank_cmo._CMO_ANNUAL_URLS", (url_a, url_b))

    def _get(url, params=None, headers=None):
        raise ConnectionError("down")

    src = WorldBankCmoGoldSource(http_get=_get)
    with pytest.raises(SourceUnavailable):
        src.get_history(date(2020, 1, 1), date(2024, 12, 31))


# --------------------------------------------------------------------------- #
# Source — N1 magnitude + integrity guards surface as InvalidData... but is it #
# a SourceError subclass? (N2)                                                 #
# --------------------------------------------------------------------------- #
def test_parser_out_of_band_value_raises_invalid_data():
    # At the PARSER level an out-of-band value is InvalidData (N1 magnitude guard).
    raw = _build_cmo_xlsx(rows={2021: 1800.0, 2022: 5.0})  # 5 < 20 band floor
    with pytest.raises(InvalidData):
        _parse_cmo_annual_gold(raw)


def test_get_history_out_of_band_value_surfaces_as_source_error():
    # At the SOURCE level, a parse-failure on the only URL exhausts _CMO_ANNUAL_URLS,
    # so it surfaces as SourceUnavailable (D4: per-URL parse-failure -> try next; all
    # fail -> SourceUnavailable). Both are SourceError subclasses, so the synthesis
    # `except SourceError` fallback engages either way (N2).
    raw = _build_cmo_xlsx(rows={2021: 1800.0, 2022: 5.0})  # 5 < 20 band floor
    src = WorldBankCmoGoldSource(http_get=_serve(raw))
    with pytest.raises(SourceError):
        src.get_history(date(2020, 1, 1), date(2024, 12, 31))


def test_get_history_huge_value_surfaces_as_source_error():
    raw = _build_cmo_xlsx(rows={2021: 1800.0, 2022: 50000.0})  # > 10000 ceiling
    src = WorldBankCmoGoldSource(http_get=_serve(raw))
    with pytest.raises(SourceError):
        src.get_history(date(2020, 1, 1), date(2024, 12, 31))


def test_n2_every_recoverable_failure_is_a_source_error_subclass():
    # SourceUnavailable (transport), InvalidData (malformed), EmptyData (no years)
    # are ALL SourceError subclasses -> the synthesis `except SourceError` fallback
    # engages reliably.
    assert issubclass(SourceUnavailable, SourceError)
    assert issubclass(InvalidData, SourceError)
    assert issubclass(EmptyData, SourceError)

    # transport -> SourceUnavailable
    bad_transport = WorldBankCmoGoldSource(http_get=lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    with pytest.raises(SourceError):
        bad_transport.get_history(date(2020, 1, 1), date(2024, 12, 31))

    # malformed -> InvalidData
    bad_data = WorldBankCmoGoldSource(http_get=lambda *a, **k: _build_cmo_xlsx(rows={2022: 5.0}))
    with pytest.raises(SourceError):
        bad_data.get_history(date(2020, 1, 1), date(2024, 12, 31))

    # empty span -> EmptyData
    empty = WorldBankCmoGoldSource(http_get=_serve(_build_cmo_xlsx(rows={2020: 1700.0})))
    with pytest.raises(SourceError):
        empty.get_history(date(2030, 1, 1), date(2030, 12, 31))


def test_n2_non_source_error_bug_propagates(monkeypatch):
    # A genuine programmer bug (NOT a SourceError) must fail LOUD, never be wrapped
    # into a SourceError. Patch the parser to raise a bare RuntimeError.
    def _boom(raw):
        raise RuntimeError("programmer bug")

    monkeypatch.setattr("vnfin.gold.worldbank_cmo._parse_cmo_annual_gold", _boom)
    src = WorldBankCmoGoldSource(http_get=_serve(_build_cmo_xlsx(rows={2021: 1800.0})))
    with pytest.raises(RuntimeError):
        src.get_history(date(2021, 1, 1), date(2021, 12, 31))


# --------------------------------------------------------------------------- #
# THE highest-value test: parse the committed REAL CMO vintage fixture          #
# --------------------------------------------------------------------------- #
def test_real_vintage_fixture_parses_correctly():
    assert REAL_FIXTURE.exists(), f"missing committed fixture: {REAL_FIXTURE}"
    raw = REAL_FIXTURE.read_bytes()
    out = _parse_cmo_annual_gold(raw)
    # known values from the real Pink Sheet (verified at code time)
    assert out[1960] == pytest.approx(35.27, abs=0.01)
    assert out[2024] == pytest.approx(2387.70, abs=0.01)
    assert out[2025] == pytest.approx(3441.51, abs=0.01)
    # 66 points, 1960..2025, no gaps
    years = sorted(out)
    assert years[0] == 1960 and years[-1] == 2025
    assert len(out) == 66
    assert years == list(range(1960, 2026))


def test_real_vintage_source_get_history():
    raw = REAL_FIXTURE.read_bytes()
    src = WorldBankCmoGoldSource(http_get=_serve(raw))
    out = src.get_history(date(2023, 1, 1), date(2025, 12, 31))
    by_year = {b.date.year: b.price for b in out.bars}
    assert set(by_year) == {2023, 2024, 2025}
    assert by_year[2024] == pytest.approx(2387.70, abs=0.01)
    assert all(b.date.month == 1 and b.date.day == 1 for b in out.bars)


# --------------------------------------------------------------------------- #
# Clean-room / config sanity                                                   #
# --------------------------------------------------------------------------- #
def test_cmo_annual_urls_is_nonempty_tuple_of_worldbank_urls():
    assert isinstance(_CMO_ANNUAL_URLS, tuple) and _CMO_ANNUAL_URLS
    for u in _CMO_ANNUAL_URLS:
        assert u.startswith("https://") and "worldbank.org" in u
        assert u.endswith(".xlsx")
