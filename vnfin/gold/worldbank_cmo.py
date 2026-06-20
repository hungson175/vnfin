"""World Bank CMO "Pink Sheet" annual gold source (issue #185).

Serves **annual** world-gold (XAU/USD, USD per troy ounce) history from the World Bank
Commodity Markets "Pink Sheet" historical-data ``.xlsx`` distribution. This is the
annual-history source that the #178 ``world_reference_history_vnd`` synthesis uses for
its world-gold leg: CMO annual gold IS "spot average of daily rates" (LBMA-sourced) —
already an annual average of daily spot — so it preserves the synthesis's
``annual-avg × annual-avg`` basis exactly while working from a datacenter host (unlike
the daily CurrencyApi/Stooq legs, which are sparse/anti-bot-blocked server-side).

Design: ``docs/design/issue-185-annual-world-gold-source.md`` (D1–D6, gate notes N1/N2).
Provenance/contract/attribution: ``docs/sources/cmo-gold-annual.md``.

Standalone **history** source (inherits :class:`~vnfin.transport.HttpDataSource`, NOT
``GoldSource``) — mirroring :class:`~vnfin.fx.history_worldbank.WorldBankFXHistorySource`.
CMO is annual-history-only; it is fetched DIRECTLY (it must NOT be a peer inside the
daily ``FailoverGoldClient``, whose 50% weekday-coverage gate would wrongly reject an
annual series).

xlsx parsing uses **stdlib only** (``zipfile`` + ``xml.etree.ElementTree``) — no
openpyxl/pandas — so the core synthesis works out-of-the-box server-side. The parser is
scoped to exactly CMO's shape; anything unexpected fails safe as ``InvalidData``.

Error discipline (gate note N2): every recoverable failure raises a
:class:`~vnfin.exceptions.SourceError` SUBCLASS (``SourceUnavailable`` /
``InvalidData`` / ``EmptyData``) so the synthesis ``except SourceError`` fallback
engages; a genuine programmer bug propagates (fails loud).

License: World Bank Commodity Markets data is **CC-BY 4.0** — attribution
"Source: The World Bank — Commodity Markets (Pink Sheet)". Runtime-fetch only; no
bundled provider rows (the committed test fixture is a test asset, not a shipped dataset).

Clean-room: endpoint, sheet name, split-header layout and units were learned only from
the World Bank's own server. Zero vnstock.
"""
from __future__ import annotations

import math
import posixpath
import re
import zipfile
from datetime import date, datetime, timezone
from io import BytesIO
from typing import Optional

from xml.etree import ElementTree as ET

from ..exceptions import EmptyData, InvalidData, SourceError, SourceUnavailable
from ..transport import HttpDataSource
from ..validation import validate_date_range
from .models import GoldBar, GoldHistory

_USD_PER_OZ = "USD/oz"

#: SpreadsheetML (worksheet/workbook/sharedStrings) namespace.
_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
#: officeDocument relationship namespace (the ``r:id`` attribute on ``<sheet>``).
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
#: package relationships namespace (``workbook.xml.rels`` ``<Relationship>``).
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

#: The sheet that carries annual nominal-USD prices (gold among them).
_SHEET_NAME = "Annual Prices (Nominal)"
#: Exact (trimmed) header texts of the SPLIT gold header: a name-row cell ``Gold`` and
#: the units-row cell directly below it ``($/troy oz)`` in the SAME column. The match
#: requires BOTH (Platinum etc. also carry ``($/troy oz)``, so the name disambiguates).
_GOLD_NAME = "Gold"
_GOLD_UNITS = "($/troy oz)"

#: GATE NOTE N1 — plausible gold band (USD/oz). A parsed value outside this is a gross
#: misparse (wrong column / mis-resolved shared-string index), never a legitimate value
#: (1960 ≈ 35, 2025 ≈ 3441). The split-header text match is the primary defense; this
#: magnitude guard is the backstop so a misparse can never feed the synthesis.
_GOLD_MIN_USD_OZ = 20.0
_GOLD_MAX_USD_OZ = 10000.0

#: Ordered tuple of vintage-coded CMO annual-xlsx URLs (D4). Tried in order; a per-URL
#: 404/anti-bot/non-xlsx/parse-failure falls through to the next; all-fail →
#: ``SourceUnavailable``. v1 is a SINGLE confirmed current vintage (no prior vintage was
#: reproducible); the iterate-and-continue structure lets a prior vintage be prepended/
#: appended when the World Bank next rotates the hash. The hash segment is a per-release
#: digest, NOT a credential — it is a public CC-BY data URL (allowlisted in the
#: no-secrets scanner by explicit project decision; see tests/test_no_secrets.py).
_CMO_ANNUAL_URLS = (
    "https://thedocs.worldbank.org/en/doc/"
    "74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/"
    "CMO-Historical-Data-Annual.xlsx",
)

#: An A1-style cell reference like ``BP7`` -> column letters + row number.
_CELL_REF_RE = re.compile(r"^([A-Z]+)([0-9]+)$")
#: A 4-digit calendar year (the col-0 data-row marker).
_YEAR_RE = re.compile(r"^[0-9]{4}$")


def _local(tag: str) -> str:
    """Strip an XML namespace from ``{ns}tag`` -> ``tag`` (namespace-agnostic walk)."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _col_index(letters: str) -> int:
    """0-based column index from spreadsheet column letters (``A`` -> 0, ``BP`` -> 67)."""
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _parse_ref(ref: str):
    """``BP7`` -> ``(col_index0, row_number)``; ``None`` if unparseable."""
    m = _CELL_REF_RE.match(ref or "")
    if not m:
        return None
    return _col_index(m.group(1)), int(m.group(2))


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    """Build the shared-string table (each ``<si>`` -> its concatenated ``<t>`` text).

    Missing ``sharedStrings.xml`` is tolerated as an empty table (a worksheet with no
    shared strings is legal); a malformed one is ``InvalidData``.
    """
    try:
        raw = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise InvalidData(f"worldbank_cmo: malformed sharedStrings.xml ({exc})") from exc
    out: list[str] = []
    for si in root:
        if _local(si.tag) != "si":
            continue
        out.append("".join(t.text or "" for t in si.iter() if _local(t.tag) == "t"))
    return out


def _resolve_worksheet_path(zf: zipfile.ZipFile) -> str:
    """Map the ``Annual Prices (Nominal)`` sheet name -> its worksheet part path.

    workbook.xml gives the sheet's ``r:id``; ``workbook.xml.rels`` resolves that id to a
    worksheet ``Target`` (resolved RELATIVE to ``xl/`` — never hard-coded as sheet2.xml).
    """
    try:
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
    except KeyError as exc:
        raise InvalidData("worldbank_cmo: workbook.xml not found in xlsx") from exc
    except ET.ParseError as exc:
        raise InvalidData(f"worldbank_cmo: malformed workbook.xml ({exc})") from exc

    rid = None
    for sheet in wb.iter():
        if _local(sheet.tag) != "sheet":
            continue
        name = sheet.get("name")
        if name is not None and name.strip() == _SHEET_NAME:
            # the r:id attribute is namespaced.
            rid = sheet.get(f"{{{_REL_NS}}}id") or sheet.get("id")
            break
    if rid is None:
        raise InvalidData(
            f"worldbank_cmo: sheet {_SHEET_NAME!r} not found in workbook.xml"
        )

    try:
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    except KeyError as exc:
        raise InvalidData("worldbank_cmo: workbook.xml.rels not found") from exc
    except ET.ParseError as exc:
        raise InvalidData(f"worldbank_cmo: malformed workbook.xml.rels ({exc})") from exc

    target = None
    for rel in rels:
        if _local(rel.tag) != "Relationship":
            continue
        if rel.get("Id") == rid:
            target = rel.get("Target")
            break
    if not target:
        raise InvalidData(f"worldbank_cmo: relationship {rid!r} has no worksheet target")

    # Targets in workbook.xml.rels are relative to the xl/ directory. Resolve the
    # relative reference, collapsing any "." / ".." per the OOXML/RFC-3986 rules, so a
    # crafted Target cannot divert the read to a differently-named "xl/../..." zip
    # member; the resolved path is then validated against the real parts.
    target = target.lstrip("/")
    if target.startswith("xl/"):
        path = target
    else:
        path = "xl/" + target
    path = posixpath.normpath(path)
    if path not in zf.namelist():
        raise InvalidData(f"worldbank_cmo: worksheet part {path!r} not in xlsx")
    return path


def _cell_text(cell, shared: list[str]) -> Optional[str]:
    """Return a cell's display text (resolving a shared-string index) or ``None``."""
    t = cell.get("t")
    v = None
    inline = None
    for child in cell:
        lt = _local(child.tag)
        if lt == "v":
            v = child.text
        elif lt == "is":  # inline string
            inline = "".join(x.text or "" for x in child.iter() if _local(x.tag) == "t")
    if t == "s":
        if v is None:
            return None
        try:
            idx = int(v)
        except (TypeError, ValueError):
            return None
        if 0 <= idx < len(shared):
            return shared[idx]
        return None
    if t == "inlineStr":
        return inline
    return v


def _parse_cmo_annual_gold(raw: bytes) -> dict:
    """Parse the CMO annual-prices xlsx bytes into ``{year: usd_per_oz}``.

    Steps (D2): open the zip; resolve the ``Annual Prices (Nominal)`` worksheet via
    workbook + rels (never hard-coded); build the shared-string table; locate the gold
    column by its SPLIT header (name-row cell ``Gold`` AND the units-row cell directly
    below it ``($/troy oz)`` in the SAME column); then read each data row's year (col 0,
    a 4-digit value) and gold value.

    Every malformed/unexpected condition (bad zip, sheet/header/units missing or
    mismatched, no data rows, non-numeric or out-of-band price, duplicate/non-monotonic
    year) raises :class:`~vnfin.exceptions.InvalidData`. The N1 magnitude band and the
    positivity/finiteness guards are applied here so a misparsed column can never reach
    the source layer.
    """
    if not isinstance(raw, (bytes, bytearray)):
        raise InvalidData(
            f"worldbank_cmo: expected xlsx bytes, got {type(raw).__name__}"
        )
    # Non-xlsx body (HTML/empty/truncated/bad-magic) -> not a valid zip.
    try:
        zf = zipfile.ZipFile(BytesIO(bytes(raw)))
    except zipfile.BadZipFile as exc:
        raise InvalidData(f"worldbank_cmo: response is not a valid xlsx/zip ({exc})") from exc

    with zf:
        shared = _shared_strings(zf)
        sheet_path = _resolve_worksheet_path(zf)
        try:
            sheet = ET.fromstring(zf.read(sheet_path))
        except ET.ParseError as exc:
            raise InvalidData(f"worldbank_cmo: malformed worksheet {sheet_path} ({exc})") from exc

        # Index every cell by (col0, row) -> text so we can match the split header and
        # then read data rows without assuming any particular row/column position.
        cells: dict = {}
        for row in sheet.iter():
            if _local(row.tag) != "row":
                continue
            for c in row:
                if _local(c.tag) != "c":
                    continue
                rc = _parse_ref(c.get("r") or "")
                if rc is None:
                    continue
                cells[rc] = _cell_text(c, shared)

        # --- locate the gold column by the SPLIT header (Gold name + ($/troy oz) units
        #     directly below, same column) ---
        gold_col = None
        units_row = None
        for (col, row), text in cells.items():
            if text is None or text.strip() != _GOLD_NAME:
                continue
            below = cells.get((col, row + 1))
            if below is not None and below.strip() == _GOLD_UNITS:
                gold_col = col
                units_row = row + 1
                break
        if gold_col is None:
            # Distinguish a missing/units-mismatched header for a clearer diagnostic.
            has_name = any(
                t is not None and t.strip() == _GOLD_NAME for t in cells.values()
            )
            if has_name:
                raise InvalidData(
                    f"worldbank_cmo: found a {_GOLD_NAME!r} header but no "
                    f"{_GOLD_UNITS!r} units cell directly below it (split-header match failed)"
                )
            raise InvalidData(
                f"worldbank_cmo: no {_GOLD_NAME!r} ({_GOLD_UNITS}) header in sheet {_SHEET_NAME!r}"
            )

        # --- read data rows: col-0 cell is a 4-digit year; gold value in gold_col ---
        out: dict = {}
        last_year = None
        # iterate rows below the units row in ascending row order
        data_refs = sorted(
            ((col, row) for (col, row) in cells if col == 0 and row > units_row),
            key=lambda rc: rc[1],
        )
        for (_, row) in data_refs:
            year_text = cells.get((0, row))
            if year_text is None or not _YEAR_RE.match(year_text.strip()):
                continue
            year = int(year_text.strip())
            price = _coerce_price(cells.get((gold_col, row)), year)
            if year in out:
                raise InvalidData(f"worldbank_cmo: duplicate year {year} in CMO sheet")
            if last_year is not None and year <= last_year:
                raise InvalidData(
                    f"worldbank_cmo: non-monotonic year {year} after {last_year}"
                )
            last_year = year
            out[year] = price

    if not out:
        raise InvalidData("worldbank_cmo: no annual gold data rows found in CMO sheet")
    return out


def _coerce_price(text, year: int) -> float:
    """Validate a gold cell: numeric, finite, positive, and within the N1 band."""
    if text is None or text == "":
        raise InvalidData(f"worldbank_cmo: missing gold value for {year}")
    try:
        price = float(text)
    except (TypeError, ValueError) as exc:
        raise InvalidData(f"worldbank_cmo: non-numeric gold value {text!r} for {year}") from exc
    if not math.isfinite(price) or price <= 0:
        raise InvalidData(f"worldbank_cmo: non-positive/non-finite gold value {price!r} for {year}")
    if not (_GOLD_MIN_USD_OZ <= price <= _GOLD_MAX_USD_OZ):
        raise InvalidData(
            f"worldbank_cmo: gold value {price!r} for {year} outside plausible band "
            f"[{_GOLD_MIN_USD_OZ}, {_GOLD_MAX_USD_OZ}] USD/oz (likely a column misparse)"
        )
    return price


class WorldBankCmoGoldSource(HttpDataSource):
    """Annual world-gold (XAU/USD) history from the World Bank CMO Pink Sheet xlsx.

    ``http_get(url, params, headers) -> response bytes`` is injectable so unit tests
    never touch the network (an injected stub returns the xlsx bytes directly).
    """

    NAME = "worldbank_cmo_gold"

    def __init__(self, http_get=None, timeout: float = 25.0):
        super().__init__(http_get=http_get, timeout=timeout)

    @property
    def name(self) -> str:
        return self.NAME

    def get_history(self, start: date, end: date) -> GoldHistory:
        """Fetch the CMO annual gold series and emit one Jan-1 ``GoldBar`` per year in
        the inclusive ``[start.year, end.year]`` span.

        Validates bounds fail-closed BEFORE any network call. Iterates
        :data:`_CMO_ANNUAL_URLS` in order: a per-URL transport/non-xlsx/parse failure
        falls through to the next; all-fail → :class:`~vnfin.exceptions.SourceUnavailable`.
        Returns ``GoldHistory(product="XAU", unit="USD/oz", ...)``. No years in span →
        :class:`~vnfin.exceptions.EmptyData`. Every recoverable failure is a
        :class:`~vnfin.exceptions.SourceError` subclass (N2).
        """
        lo, hi = validate_date_range(start, end, name="worldbank_cmo_gold.history")

        annual = self._fetch_annual()  # {year: usd_per_oz}

        lo_year, hi_year = lo.year, hi.year
        bars = [
            GoldBar(date=date(year, 1, 1), price=price)
            for year, price in sorted(annual.items())
            if lo_year <= year <= hi_year
        ]
        if not bars:
            raise EmptyData(
                f"{self.NAME}: no annual gold observations in {lo_year}..{hi_year}"
            )
        return GoldHistory(
            product="XAU",
            unit=_USD_PER_OZ,
            value_unit=_USD_PER_OZ,
            currency="USD",
            source=self.NAME,
            bars=tuple(bars),
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _fetch_annual(self) -> dict:
        """Try each vintage URL in order; return ``{year: usd_per_oz}`` from the first
        that fetches + parses. A per-URL ``SourceError`` (transport/non-xlsx/parse/
        out-of-band) is recorded and the next URL is tried; all-fail →
        ``SourceUnavailable`` carrying the per-URL reasons. A non-``SourceError``
        propagates (N2: a programmer bug fails loud)."""
        reasons = []
        for url in _CMO_ANNUAL_URLS:
            try:
                raw = self._request_bytes(url)
                return _parse_cmo_annual_gold(raw)
            except SourceError as exc:
                reasons.append(f"{url}: {type(exc).__name__}: {exc}")
                continue
        joined = "; ".join(reasons) or "no CMO URLs configured"
        raise SourceUnavailable(f"{self.NAME}: all CMO annual URLs failed -> {joined}")
