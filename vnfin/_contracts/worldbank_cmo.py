"""Shared, domain-neutral World Bank CMO "Pink Sheet" annual-xlsx parser (#196).

Extracted verbatim from ``vnfin/gold/worldbank_cmo.py`` (issue #185) so the gold source
and the new public precious-metals domain (``vnfin/metals/``) read the SAME World Bank
Commodity Markets annual ``.xlsx`` without duplicating the OOXML machinery. The parser is
genuinely domain-neutral: a frozen :class:`MetalSpec` parameterizes it per metal (the
split-header NAME cell + per-metal plausibility band); gold's observable output stays
byte-for-byte identical (it delegates to :func:`parse_cmo_annual` with its own spec).

xlsx parsing uses **stdlib only** (``zipfile`` + ``xml.etree.ElementTree``) — no
openpyxl/pandas — so the core works out-of-the-box server-side. The parser is scoped to
exactly CMO's shape; anything unexpected fails safe as :class:`~vnfin.exceptions.InvalidData`.

Every guard from the original gold parser is preserved here, generalized by the spec:
rels-resolved worksheet (never a hard-coded sheet index), split-header NAME+units match in
the SAME column, finite/positive value, per-metal magnitude band, duplicate-year and
non-monotonic-year guards, and the EmptyData/InvalidData fail-safe.

License: World Bank Commodity Markets data is **CC-BY 4.0** — attribution "Source: The
World Bank — Commodity Markets (Pink Sheet)". Runtime-fetch only; no bundled provider rows.

Clean-room: endpoint, sheet name, split-header layout and units were learned only from the
World Bank's own server. Zero vnstock.
"""
from __future__ import annotations

import math
import posixpath
import re
import zipfile
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

from xml.etree import ElementTree as ET

from ..exceptions import InvalidData

_USD_PER_OZ = "USD/oz"

#: SpreadsheetML (worksheet/workbook/sharedStrings) namespace.
_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
#: officeDocument relationship namespace (the ``r:id`` attribute on ``<sheet>``).
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
#: package relationships namespace (``workbook.xml.rels`` ``<Relationship>``).
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

#: The sheet that carries annual nominal-USD prices (gold/platinum/silver among them).
_SHEET_NAME = "Annual Prices (Nominal)"

#: Ordered tuple of vintage-coded CMO annual-xlsx URLs (D4). Tried in order; a per-URL
#: 404/anti-bot/non-xlsx/parse-failure falls through to the next; all-fail →
#: ``SourceUnavailable``. v1 is a SINGLE confirmed current vintage (no prior vintage was
#: reproducible); the iterate-and-continue structure lets a prior vintage be prepended/
#: appended when the World Bank next rotates the hash. The hash segment is a per-release
#: digest, NOT a credential — it is a public CC-BY data URL (allowlisted in the
#: no-secrets scanner by explicit project decision; see tests/test_no_secrets.py). Gold
#: re-exports this name (``vnfin.gold.worldbank_cmo._CMO_ANNUAL_URLS``) for back-compat.
_CMO_ANNUAL_URLS = (
    "https://thedocs.worldbank.org/en/doc/"
    "74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/"
    "CMO-Historical-Data-Annual.xlsx",
)

#: An A1-style cell reference like ``BP7`` -> column letters + row number.
_CELL_REF_RE = re.compile(r"^([A-Z]+)([0-9]+)$")
#: A 4-digit calendar year (the col-0 data-row marker).
_YEAR_RE = re.compile(r"^[0-9]{4}$")


@dataclass(frozen=True)
class MetalSpec:
    """Per-metal parameters for :func:`parse_cmo_annual`.

    ``product`` is the ISO-4217 commodity code (``"XAU"`` / ``"XAG"`` / ``"XPT"``);
    ``name_row`` is the exact split-header NAME cell text (``"Gold"`` / ``"Silver"`` /
    ``"Platinum"``) matched together with ``units_row`` in the SAME column (the units
    string is shared across all three, so the name disambiguates). ``min_usd_oz`` /
    ``max_usd_oz`` are the per-metal plausibility band (a magnitude backstop behind the
    split-header text match; re-derived per metal from its own measured range, never
    byte-copied across metals).
    """

    product: str
    name_row: str
    min_usd_oz: float
    max_usd_oz: float
    units_row: str = "($/troy oz)"


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


def coerce_price(text, year: int, spec: MetalSpec) -> float:
    """Validate a metal cell: numeric, finite, positive, and within ``spec``'s band.

    The InvalidData messages NAME the metal (``spec.name_row`` / ``spec.product``) and the
    band so a misparse is diagnosable per metal.
    """
    if text is None or text == "":
        raise InvalidData(
            f"worldbank_cmo: missing {spec.name_row} ({spec.product}) value for {year}"
        )
    try:
        price = float(text)
    except (TypeError, ValueError) as exc:
        raise InvalidData(
            f"worldbank_cmo: non-numeric {spec.name_row} ({spec.product}) value "
            f"{text!r} for {year}"
        ) from exc
    if not math.isfinite(price) or price <= 0:
        raise InvalidData(
            f"worldbank_cmo: non-positive/non-finite {spec.name_row} ({spec.product}) "
            f"value {price!r} for {year}"
        )
    if not (spec.min_usd_oz <= price <= spec.max_usd_oz):
        raise InvalidData(
            f"worldbank_cmo: {spec.name_row} ({spec.product}) value {price!r} for {year} "
            f"outside plausible band [{spec.min_usd_oz}, {spec.max_usd_oz}] USD/oz "
            f"(likely a column misparse)"
        )
    return price


def parse_cmo_annual(raw: bytes, spec: MetalSpec) -> dict:
    """Parse the CMO annual-prices xlsx bytes into ``{year: usd_per_oz}`` for ``spec``.

    Steps (D2): open the zip; resolve the ``Annual Prices (Nominal)`` worksheet via
    workbook + rels (never hard-coded); build the shared-string table; locate the metal
    column by its SPLIT header (name-row cell ``spec.name_row`` AND the units-row cell
    directly below it ``spec.units_row`` in the SAME column); then read each data row's
    year (col 0, a 4-digit value) and the metal's value.

    Every malformed/unexpected condition (bad zip, sheet/header/units missing or
    mismatched, no data rows, non-numeric or out-of-band price, duplicate/non-monotonic
    year) raises :class:`~vnfin.exceptions.InvalidData`. The per-metal magnitude band and
    the positivity/finiteness guards are applied here (via :func:`coerce_price`) so a
    misparsed column can never reach the source layer.
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

        # --- locate the metal column by the SPLIT header (name + units directly below,
        #     same column). Collect EVERY distinct matching column rather than stopping at
        #     the first: a forged/duplicate-header sheet with two columns that both satisfy
        #     the split header is AMBIGUOUS and must fail safe (never silently serve the
        #     first-in-scan column relabelled — never-fabricate, #196). ---
        matches: dict = {}  # col -> units_row (distinct matching columns)
        for (col, row), text in cells.items():
            if text is None or text.strip() != spec.name_row:
                continue
            below = cells.get((col, row + 1))
            if below is not None and below.strip() == spec.units_row:
                matches.setdefault(col, row + 1)
        if len(matches) > 1:
            raise InvalidData(
                f"worldbank_cmo: ambiguous — multiple {spec.name_row!r} ({spec.units_row}) "
                f"columns in sheet {_SHEET_NAME!r}"
            )
        metal_col = next(iter(matches), None)
        units_row = matches.get(metal_col) if metal_col is not None else None
        if metal_col is None:
            # Distinguish a missing/units-mismatched header for a clearer diagnostic.
            has_name = any(
                t is not None and t.strip() == spec.name_row for t in cells.values()
            )
            if has_name:
                raise InvalidData(
                    f"worldbank_cmo: found a {spec.name_row!r} header but no "
                    f"{spec.units_row!r} units cell directly below it (split-header match failed)"
                )
            raise InvalidData(
                f"worldbank_cmo: no {spec.name_row!r} ({spec.units_row}) header in "
                f"sheet {_SHEET_NAME!r}"
            )

        # --- read data rows: col-0 cell is a 4-digit year; metal value in metal_col ---
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
            price = coerce_price(cells.get((metal_col, row)), year, spec)
            if year in out:
                raise InvalidData(f"worldbank_cmo: duplicate year {year} in CMO sheet")
            if last_year is not None and year <= last_year:
                raise InvalidData(
                    f"worldbank_cmo: non-monotonic year {year} after {last_year}"
                )
            last_year = year
            out[year] = price

    if not out:
        raise InvalidData(
            f"worldbank_cmo: no annual {spec.name_row} data rows found in CMO sheet"
        )
    return out
