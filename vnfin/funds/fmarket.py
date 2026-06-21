"""Fmarket fund-data adapter (clean-room).

Talks to Fmarket's own public, no-auth JSON API (``api.fmarket.vn``) for VN
open-ended mutual funds:

  - ``list_funds()``  -> POST /res/products/filter
  - ``nav_history(product_id)`` -> POST /res/product/get-nav-history  (isAllData:1)
  - ``holdings(product_id)``         -> GET /res/products/{id}
  - ``asset_allocation(product_id)`` -> GET /res/products/{id}

The product-detail document carries the per-line-item holdings (equities in
``productTopHoldingList`` and bonds in ``productTopHoldingBondList`` — bond funds
disclose only the latter) and the top-level asset-class split
(``productAssetHoldingList``). ``holdings()`` merges both line-item lists;
``asset_allocation()`` reads the class split off the same document.

NAV is VND per fund unit; ``navDate`` is ``YYYY-MM-DD``. Provenance, compliance,
and shape notes live in ``docs/sources/funds-fmarket.md``.

Transport errors are wrapped as :class:`SourceUnavailable`; malformed / garbage
payloads as :class:`InvalidData`; no-data responses as :class:`EmptyData`. This
keeps the adapter failover-safe (it never leaks raw exceptions to callers).

Runtime fetch only — no caching or redistribution of provider data.
"""
from __future__ import annotations

import math
import statistics
from datetime import date, datetime, timezone

from .._contracts import (
    MISSING,
    canonical_enum_tag,
    canonical_fund_code,
    canonical_security_symbol,
    enum_tag_or_other,
    optional_present,
    require_non_empty_str,
    require_present,
)
from ..exceptions import EmptyData, InvalidData, SourceUnavailable, StaleData
from ..sources.base import VN_TZ
from ..transport import DEFAULT_UA, HttpDataSource
from ..validation import validate_iso_date_string
from .models import (
    AssetAllocation,
    AssetClassWeight,
    Fund,
    FundHolding,
    FundList,
    NavHistory,
    NavPoint,
)

_BASE_URL = "https://api.fmarket.vn"
_FILTER_PATH = "/res/products/filter"
_NAV_PATH = "/res/product/get-nav-history"
_DETAIL_PATH = "/res/products"  # + /{id}

# Issue #172-RESIDUAL: success-path NAV end-gap warning. Cadence-relative (NOT the
# stock trading calendar — fund NAV cadence varies: daily vs weekly/twice-monthly),
# inferred over a TRAILING window of recent diffs so a daily->weekly switch does not
# false-positive. Design: docs/design/nav-success-path-staleness.md.
_NAV_END_GAP = "nav_end_gap"            # mechanical token (matches partial_end_coverage style)
_NAV_END_GAP_FACTOR = 2                  # threshold = max(FACTOR * typical_gap, MIN_DAYS)
_NAV_END_GAP_MIN_DAYS = 7                # daily-fund floor (a holiday weekend never trips it)
_NAV_END_GAP_SINGLE_POINT_DAYS = 14     # single-point fallback (cadence unknown)
_NAV_END_GAP_CADENCE_WINDOW = 8         # most-recent diffs feeding the cadence median (all if fewer)

# Issue #190: list-level NAV-staleness warning on FundList. A fund whose own
# `nav_as_of` is older than this many CALENDAR days (vs the injected `today`) is stale.
# Calendar days (no holiday-calendar dep); list-level (one token, enumeration capped).
_FUND_NAV_STALE_DAYS = 7                 # gap == 7 NOT stale; gap == 8 stale
_FUND_NAV_STALE = "fund_nav_stale"       # mechanical token prefix (fact-first)
_FUND_NAV_STALE_CAP = 5                  # max enumerated stale codes before "+M more"


def _parse_json(text, who):
    import json

    try:
        return json.loads(text)
    except (ValueError, TypeError) as exc:
        raise InvalidData(f"fmarket: non-JSON response from {who}") from exc


def _as_float(value, ctx):
    """Coerce a JSON scalar to a finite float or raise InvalidData."""
    from ..coerce import parse_provider_float

    return parse_provider_float(value, label=ctx, source="fmarket")


def _require_data_object(data, who: str) -> dict:
    """Return ``data`` when it is a dict; treat ``None`` as empty; reject other shapes."""
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise InvalidData(f"fmarket: {who} data is not an object")
    return data


def _require_array(value, who: str):
    """Return ``value`` when it is a list; treat ``None`` as absent; reject other shapes."""
    if value is None:
        return None
    if not isinstance(value, list):
        raise InvalidData(f"fmarket: {who} is not an array")
    return value


def _parse_update_at(raw):
    """Parse a provider epoch-**millisecond** ``updateAt`` to a tz-aware UTC datetime.

    Returns ``None`` (never a fabricated ``now()``) when the field is absent or
    malformed — a holding/allocation freshness stamp must reflect the provider, not
    the fetch time. Rejects ``bool``; accepts a positive ``int`` or an integral,
    finite ``float`` (providers send e.g. ``1700000000000.0``). Out-of-range epochs
    (``ValueError``/``OverflowError``/``OSError``) also yield ``None``.
    """
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, float):
        if not math.isfinite(raw) or not raw.is_integer():
            return None
        raw = int(raw)
    if not isinstance(raw, int) or raw <= 0:
        return None
    try:
        return datetime.fromtimestamp(raw / 1000.0, tz=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def _optional_str(value, *, ctx: str) -> str:
    """Return a stripped string field, treating absent/blank as empty."""
    if value is None or value == "":
        return ""
    if not isinstance(value, str):
        raise InvalidData(f"fmarket: {ctx} is not a string")
    return value.strip()


def _pick_manager(owner: dict, *, fund_code: str) -> str:
    for key in ("name", "shortName"):
        val = owner.get(key)
        if val is None or val == "":
            continue
        if not isinstance(val, str):
            raise InvalidData(f"fmarket: fund {fund_code} owner {key} is not a string")
        stripped = val.strip()
        if stripped:
            return stripped
    return ""


class FmarketFundSource(HttpDataSource):
    """Adapter for Fmarket's public fund-data API.

    ``http_get(url, params=None, headers=None, json_body=None) -> text``. When
    ``json_body`` is provided the shared transport issues a POST with that JSON
    body; otherwise it issues a GET. Injectable for testing.
    """

    NAME = "fmarket"
    name = "fmarket"

    # --- public API -------------------------------------------------------

    def list_funds(self, asset_type=None, search="", page_size: int = 100) -> FundList:
        """List VN open-ended mutual funds.

        ``asset_type`` optionally filters by provider asset-class code (e.g.
        ``"STOCK"``); ``search`` does a free-text name/code search.
        """
        if not isinstance(page_size, int) or isinstance(page_size, bool):
            raise InvalidData("fmarket: page_size must be an integer")
        if not (1 <= page_size <= 1000):
            raise InvalidData("fmarket: page_size must be between 1 and 1000")
        # Issue #56: caller-supplied filters must be strings (or absent).
        if asset_type is not None and not isinstance(asset_type, str):
            raise InvalidData("fmarket: asset_type must be a string")
        if not isinstance(search, str):
            raise InvalidData("fmarket: search must be a string")
        # Treat whitespace-only asset_type/search as absent so the provider body
        # never contains a blank filter.
        asset = asset_type.strip() if asset_type else ""
        query = search.strip() if search else ""
        body = {
            "types": ["NEW_FUND", "TRADING_FUND"],
            "sortField": "navTo6Months",
            "sortOrder": "DESC",
            "page": 1,
            "pageSize": page_size,
            "isIpo": False,
            "fundAssetTypes": [asset] if asset else [],
            "searchField": query,
        }
        parsed = self._post(_BASE_URL + _FILTER_PATH, body, who="filter")
        data = _require_data_object(parsed.get("data"), who="filter")
        rows = _require_array(data.get("rows"), who="filter rows")
        if rows is None or len(rows) == 0:
            raise EmptyData("fmarket: no funds returned")
        seen_codes: set[str] = set()
        seen_ids: set[int] = set()
        funds: list[Fund] = []
        for r in rows:
            fund = self._parse_fund(r)
            # Issue #68: dedupe on the case-insensitive code so "TESTCO" and " testco "
            # collide (fund.code is already stripped in _parse_fund).
            code_key = fund.code.casefold()
            if code_key in seen_codes:
                raise InvalidData(f"fmarket: duplicate fund code {fund.code} in response")
            if fund.id in seen_ids:
                raise InvalidData(f"fmarket: duplicate fund id {fund.id} in response")
            seen_codes.add(code_key)
            seen_ids.add(fund.id)
            funds.append(fund)
        # Issue #190: surface list-level NAV staleness. `today` is injected via _today()
        # (deterministic in tests); the warning never invents a date and is leak-safe.
        warnings = _fund_nav_stale_warning(funds, _today())
        return FundList(
            funds=tuple(funds),
            source=self.name,
            currency="VND",
            fetched_at_utc=datetime.now(timezone.utc),
            warnings=warnings,
        )

    def nav_history(self, product_id: int, from_date=None, to_date=None) -> NavHistory:
        """Daily NAV history for a fund (by internal ``product_id``).

        With no date window the full inception-to-now history is requested.
        ``from_date``/``to_date`` (``date`` or ``YYYY-MM-DD`` string) window the
        series. Note the upstream server requires both ``fromDate`` and ``toDate``
        to be present (an absent pair returns HTTP 400) and only enforces the
        ``toDate`` upper bound server-side, so we always send a default pair and
        additionally filter the lower bound client-side for an exact window.
        """
        fid = _validate_product_id(product_id)
        # Parse/validate both bounds up front so a malformed caller date raises
        # InvalidData (never a raw ValueError) and an inverted window is rejected.
        lo = _coerce_date(from_date, "from_date") if from_date is not None else None
        hi = _coerce_date(to_date, "to_date") if to_date is not None else None
        if lo is not None and hi is not None and lo > hi:
            raise InvalidData(
                f"fmarket: from_date {lo.isoformat()} is after to_date {hi.isoformat()}"
            )
        # Issue #144: the upstream server mishandles a NARROW window — a request with
        # the caller's fromDate/toDate can return inception-anchored rows that do NOT
        # overlap the requested range, so client-side filtering then drops everything
        # (wrong EmptyData). Always request the WIDE/default window and apply the
        # caller's bounds CLIENT-SIDE only, where the full history is reliably returned.
        body = {
            "isAllData": 1,
            "productId": fid,
            "fromDate": _DEFAULT_FROM,
            "toDate": _today_ymd(),
        }
        parsed = self._post(_BASE_URL + _NAV_PATH, body, who="nav-history")
        rows = _require_array(parsed.get("data"), who="nav-history data")
        if rows is None or len(rows) == 0:
            raise EmptyData(f"fmarket: no NAV history for product {product_id}")
        seen: dict[date, float] = {}
        points: list[NavPoint] = []
        deduped = 0
        max_navdate: date | None = None  # #172: latest navDate over ALL rows (pre-filter)
        for r in rows:
            # Issue #144: parse navDate FIRST and skip out-of-window rows BEFORE the
            # productId / value / duplicate guards — the broad fetch legitimately
            # brings extra rows outside the caller's window, and those must not fail
            # the request (e.g. an out-of-window duplicate or odd productId). An
            # in-window duplicate is still fatal (below).
            d = self._nav_row_date(r)
            # Issue #172: track the newest navDate across the FULL (pre-window-filter)
            # row set so a stale feed (history ending before the window) is
            # distinguishable from genuinely-empty data. Date-only, no #21/#158/value
            # guards on out-of-window rows (that would reintroduce the #144 bug).
            if max_navdate is None or d > max_navdate:
                max_navdate = d
            if (lo is not None and d < lo) or (hi is not None and d > hi):
                continue
            # Issue #21 (reopen): an in-window NAV row that EXPOSES a productId must
            # identify the requested fund. Key-presence is the trigger (not
            # truthiness): a present ``productId: null`` does not bypass the guard; a
            # present value must be a non-bool int equal to fid. A row that omits
            # productId is accepted (the request already scoped the fund).
            if "productId" in r:
                row_pid = r["productId"]
                if isinstance(row_pid, bool) or not isinstance(row_pid, int) or row_pid != fid:
                    raise InvalidData(
                        f"fmarket: nav row productId {row_pid!r} != requested {fid}"
                    )
            point = self._parse_nav_point(r)
            # Issue #158: a duplicate navDate within the window is only fatal when the NAV
            # CONFLICTS. An identical-value duplicate is harmless provider repetition —
            # dedupe it (keep first) and warn; a different NAV for the same date is
            # ambiguous data and fails closed.
            if point.date in seen:
                if point.nav != seen[point.date]:
                    raise InvalidData(
                        f"fmarket: conflicting navDate {point.date.isoformat()} for product "
                        f"{product_id} ({seen[point.date]} vs {point.nav})"
                    )
                deduped += 1
                continue
            seen[point.date] = point.nav
            points.append(point)
        points.sort(key=lambda p: p.date)
        if not points:
            # Issue #172: history is non-empty but no row falls in the caller's window.
            # If the newest navDate is strictly BEFORE the requested window start, the
            # feed is stale (or the fund is closed) — surface an explicit, actionable
            # StaleData (still an EmptyData subclass) naming the data gap, instead of a
            # silent EmptyData. Pre-inception windows and sparse/weekend straddles
            # (lo <= max_navdate) stay plain EmptyData.
            if lo is not None and max_navdate is not None and max_navdate < lo:
                end = hi.isoformat() if hi is not None else _today_ymd()
                raise StaleData(
                    f"fmarket: NAV history for product {product_id} ends at "
                    f"{max_navdate.isoformat()}, before requested {lo.isoformat()}..{end}"
                )
            raise EmptyData(f"fmarket: no NAV history for product {product_id} in range")
        warnings: tuple[str, ...] = ()
        if deduped:
            warnings = (
                # #180: mechanical token prefix (fact-first), cause in the tail.
                f"deduped_duplicate_nav_rows: {deduped} duplicate navDate row(s) with identical NAV",
            )
        # Issue #172-RESIDUAL: success-path cadence-relative end-gap warning. Appended
        # AFTER the dedup warning (dedup stays first). `today` is injected (never
        # written into the result); `fetched_at_utc` below stays the real fetch stamp.
        warnings = warnings + _nav_end_gap_warning(points, hi, _today())
        return NavHistory(
            product_id=fid,
            points=tuple(points),
            source=self.name,
            currency="VND",
            value_unit="VND/unit",  # NAV is money per fund unit
            fetched_at_utc=datetime.now(timezone.utc),
            warnings=warnings,
        )

    def _fetch_detail_data(self, fid: int, who: str) -> dict:
        """GET the product-detail document and enforce the #21 fund-identity guard.

        ``holdings()`` and ``asset_allocation()`` both read the same
        ``/res/products/{id}`` document, so the identity check lives here once.

        Issue #21 (reopen): the detail document MUST identify the requested fund — a
        missing/null id bypasses identity entirely, so ``id`` is required: a non-bool
        int equal to ``fid`` (None/missing, bool, non-int, or mismatch all reject).
        ``code`` has no requested counterpart to compare, but a present value must be
        a non-empty CANONICAL string (no surrounding whitespace) so a corrupt identity
        shape is not silently accepted.
        """
        url = f"{_BASE_URL}{_DETAIL_PATH}/{fid}"
        parsed = self._get(url, who=who)
        data = _require_data_object(parsed.get("data"), who=who)
        detail_id = data.get("id")
        if isinstance(detail_id, bool) or not isinstance(detail_id, int) or detail_id != fid:
            raise InvalidData(
                f"fmarket: {who} detail id {detail_id!r} != requested {fid}"
            )
        detail_code = data.get("code")
        if detail_code is not None and (
            not isinstance(detail_code, str)
            or not detail_code
            or detail_code != detail_code.strip()
        ):
            raise InvalidData(
                f"fmarket: {who} detail code {detail_code!r} is not a non-empty canonical string"
            )
        return data

    def holdings(self, product_id: int) -> tuple[FundHolding, ...]:
        """Top disclosed portfolio holdings for a fund (by internal ``product_id``).

        Returns equity holdings (``productTopHoldingList``) followed by bond holdings
        (``productTopHoldingBondList``) — a bond fund discloses only the latter, so a
        pure-bond or balanced fund now returns its real positions instead of empty
        data. Each :class:`FundHolding` carries ``instrument_type`` (``"STOCK"``/
        ``"BOND"``). :class:`EmptyData` is raised only when *both* lists are empty/
        absent (the fund has published no holdings yet).
        """
        fid = _validate_product_id(product_id)
        data = self._fetch_detail_data(fid, who="holdings")
        equity = (
            _require_array(
                data.get("productTopHoldingList"), who="holdings productTopHoldingList"
            )
            or []
        )
        bonds = (
            _require_array(
                data.get("productTopHoldingBondList"),
                who="holdings productTopHoldingBondList",
            )
            or []
        )
        if not equity and not bonds:
            raise EmptyData(
                f"fmarket: no holdings published yet for product {product_id}"
            )
        # One dedup set spans BOTH lists: the same code in equity and bond is a
        # provider self-inconsistency that fails closed. Equity rows come first so
        # the equity-only ordering callers already rely on is preserved.
        seen: set[str] = set()
        holdings = tuple(
            [self._parse_holding(r, seen, default_type="STOCK") for r in equity]
            + [self._parse_holding(r, seen, default_type="BOND") for r in bonds]
        )
        total_weight = sum(h.weight_pct for h in holdings)
        if total_weight > 100.0 + 1e-9:
            raise InvalidData(
                f"fmarket: aggregate holdings weight exceeds 100% ({total_weight})"
            )
        return holdings

    def asset_allocation(self, product_id: int) -> AssetAllocation:
        """Asset-class split (equity/bond/cash) for a fund, off the same detail doc.

        Parses ``productAssetHoldingList`` into typed :class:`AssetClassWeight` rows.
        Each class code is validated against ``{STOCK, BOND, CASH}`` (a present-but-
        unrecognized class fails closed). The disclosed weights are NOT forced to sum
        to 100% (partial disclosure is allowed). ``as_of_utc`` is the freshest per-row
        ``updateAt`` (``None`` when the provider omits it). :class:`EmptyData` is
        raised when the allocation list is empty/absent.
        """
        fid = _validate_product_id(product_id)
        data = self._fetch_detail_data(fid, who="asset-allocation")
        rows = _require_array(
            data.get("productAssetHoldingList"),
            who="asset-allocation productAssetHoldingList",
        )
        if rows is None or len(rows) == 0:
            raise EmptyData(
                f"fmarket: no asset allocation published yet for product {product_id}"
            )
        seen: set[str] = set()
        classes: list[AssetClassWeight] = []
        as_of = None
        for row in rows:
            classes.append(self._parse_asset_class(row, seen))
            row_as_of = _parse_update_at(row.get("updateAt")) if isinstance(row, dict) else None
            if row_as_of is not None and (as_of is None or row_as_of > as_of):
                as_of = row_as_of
        code = data.get("code") if isinstance(data.get("code"), str) else None
        return AssetAllocation(
            product_id=fid,
            classes=tuple(classes),
            source="fmarket",
            currency="VND",
            code=code,
            as_of_utc=as_of,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    # --- row parsers ------------------------------------------------------

    @staticmethod
    def _parse_fund(row) -> Fund:
        if not isinstance(row, dict):
            raise InvalidData("fmarket: fund row is not an object")
        # Issue #33: fund code is a public fund identifier. Key-presence is the
        # trigger: a PRESENT `code` (incl. null) must be a canonical fund code
        # (null/blank/malformed-non-blank fail closed) — it must NOT fall back to
        # shortName. Only a truly ABSENT `code` key may fall back to `shortName`
        # (itself then required canonical). canonical_fund_code normalizes
        # (strip().upper()) then validates [A-Z][A-Z0-9]*.
        code_val = optional_present(row, "code")
        if code_val is not MISSING:
            code = canonical_fund_code(code_val, "fmarket fund code")
        else:
            short = optional_present(row, "shortName")
            if short is MISSING:
                raise InvalidData("fmarket: fund row missing code")
            code = canonical_fund_code(short, "fmarket fund shortName")
        fid = row.get("id")
        if fid is None:
            raise InvalidData("fmarket: fund row missing id")
        if isinstance(fid, bool) or not isinstance(fid, int):
            raise InvalidData(f"fmarket: fund row has non-integer id {fid!r}")
        if fid <= 0:
            raise InvalidData(f"fmarket: fund row has non-positive id {fid}")
        nav = _as_float(row.get("nav"), f"fund {code} nav")
        if nav <= 0:
            raise InvalidData(f"fmarket: non-positive nav for fund {code}")
        owner = row.get("owner")
        if owner is None:
            owner = {}
        elif not isinstance(owner, dict):
            raise InvalidData(f"fmarket: fund {code} owner is not an object")
        manager = _pick_manager(owner, fund_code=code)
        asset = row.get("dataFundAssetType")
        if asset is None:
            asset = {}
        elif not isinstance(asset, dict):
            raise InvalidData(
                f"fmarket: fund {code} dataFundAssetType is not an object"
            )
        asset_type = _optional_str(
            asset.get("code"), ctx=f"fund {code} asset type code"
        )
        raw_name = row.get("name")
        if raw_name is None or raw_name == "":
            name = code
        else:
            name = _optional_str(raw_name, ctx=f"fund {code} name") or code
        # #181: the provider's OWN per-fund NAV date lives at extra.lastNAVDate, an
        # epoch-ms at VN-local midnight. Reuse the epoch-ms converter, then take the
        # VN calendar date. Never fabricate: absent extra / absent / null / non-
        # positive / garbage lastNAVDate -> None (the converter returns None), and a
        # missing nav date must never blow up the whole list. The two `updateAt`
        # distractors (top-level + productNavChange) are deliberately NOT used.
        extra = row.get("extra")
        nav_as_of = None
        if isinstance(extra, dict):
            dt = _parse_update_at(extra.get("lastNAVDate"))
            if dt is not None:
                nav_as_of = dt.astimezone(VN_TZ).date()
        return Fund(
            code=str(code),
            name=name,
            id=fid,
            nav=nav,
            manager=manager,
            asset_type=asset_type,
            currency="VND",
            nav_as_of=nav_as_of,
        )

    @staticmethod
    def _nav_row_date(row) -> date:
        """Issue #144: parse ONLY the navDate (row-object + date validity) so the
        caller's window can be applied before the productId/value/duplicate guards.
        A non-object row or malformed/missing navDate fails closed (row integrity is
        independent of the window)."""
        if not isinstance(row, dict):
            raise InvalidData("fmarket: nav row is not an object")
        raw_date = row.get("navDate")
        if not raw_date:
            raise InvalidData("fmarket: nav row missing navDate")
        try:
            return validate_iso_date_string(raw_date, label="navDate")
        except InvalidData as exc:
            raise InvalidData(f"fmarket: malformed navDate {raw_date!r}") from exc

    @staticmethod
    def _parse_nav_point(row) -> NavPoint:
        d = FmarketFundSource._nav_row_date(row)
        raw_date = row.get("navDate")
        nav = _as_float(row.get("nav"), f"nav on {raw_date}")
        # Issue #13: zero NAV is not a valid market observation.
        if nav <= 0:
            raise InvalidData(f"fmarket: non-positive nav on {raw_date}")
        return NavPoint(date=d, nav=nav)

    @staticmethod
    def _parse_holding(row, seen_codes=None, *, default_type: str = "STOCK") -> FundHolding:
        if not isinstance(row, dict):
            raise InvalidData("fmarket: holding row is not an object")
        # Issue #173 (residual): resolve instrument_type FIRST (it needs only the
        # row's `type` + the per-list default), then choose stockCode strictness by
        # type. The accepted set is the known reals {STOCK, BOND, UNLISTED_BOND}
        # (listed vs unlisted is a real credit-risk distinction worth carrying); a
        # present-but-unknown *stringlike* type maps to the honest "OTHER" tag
        # rather than fail-closing a whole fund (a holdings tuple has no per-row
        # warning channel). A present-MALFORMED `type` (non-string / blank) is a
        # genuine data-quality error and still fails closed via enum_tag_or_other.
        # An absent `type` falls back to the per-list default (equity list -> STOCK,
        # bond list -> BOND).
        instrument_type = (
            enum_tag_or_other(
                optional_present(row, "type"),
                {"STOCK", "BOND", "UNLISTED_BOND"},
                "fmarket holding type",
                missing_ok=True,
                other="OTHER",
            )
            or default_type
        )
        # Issue #34 / #173: stockCode is a public identifier. For equities it stays
        # STRICT — a present blank or malformed non-blank shape (internal space /
        # punctuation / digit-first) fails closed via canonical_security_symbol
        # (strip().upper() then [A-Z][A-Z0-9]*). For bond / unlisted-bond / other
        # rows it is RELAXED: a real Fmarket unlisted-bond row may carry a
        # descriptive phrase (e.g. 'Trái phiếu chưa niêm yết') instead of a
        # canonical code, which must NOT hard-fail the fund. The key must still be
        # present and a non-empty string (present-null / blank / missing still fail
        # closed); it is stripped and stored verbatim (no upper-case, no grammar).
        raw_code = require_present(row, "stockCode", "fmarket holding stockCode")
        if instrument_type == "STOCK":
            stock_code = canonical_security_symbol(raw_code, "fmarket holding stockCode")
        else:
            stock_code = require_non_empty_str(
                raw_code, "fmarket holding stockCode", canonical=False
            )
        if seen_codes is not None:
            if stock_code in seen_codes:
                raise InvalidData(f"fmarket: duplicate holding stock code {stock_code}")
            seen_codes.add(stock_code)
        weight = _as_float(row.get("netAssetPercent"), f"holding {stock_code} weight")
        if not (0.0 <= weight <= 100.0):
            raise InvalidData(
                f"fmarket: holding {stock_code} weight out of range: {weight}"
            )
        industry = row.get("industry")
        if industry is not None and not isinstance(industry, str):
            raise InvalidData(f"fmarket: holding {stock_code} industry is not a string")
        price = row.get("price")
        price_unit = None
        if price is not None:
            # Provider price scale is unverified/ambiguous — keep it RAW, never
            # normalize. Surface the value plus an explicit "raw" unit tag so
            # callers never mistake it for a canonical money unit.
            price = _as_float(price, f"holding {stock_code} price")
            if price < 0:
                raise InvalidData(f"fmarket: holding {stock_code} price is negative: {price}")
            price_unit = "raw"
        return FundHolding(
            stock_code=stock_code,
            weight_pct=weight,
            industry=industry,
            price_raw=price,
            price_unit=price_unit,
            instrument_type=instrument_type,
            as_of_utc=_parse_update_at(row.get("updateAt")),
        )

    @staticmethod
    def _parse_asset_class(row, seen_codes=None) -> AssetClassWeight:
        """Parse one ``productAssetHoldingList`` row into an :class:`AssetClassWeight`.

        ``assetType`` must be an object; its ``code`` is validated against
        ``{STOCK, BOND, CASH}`` (present-but-unrecognized fails closed). ``assetPercent``
        is range-checked 0-100. A class code repeated within the list fails closed.
        """
        if not isinstance(row, dict):
            raise InvalidData("fmarket: asset-allocation row is not an object")
        asset_type = row.get("assetType")
        if not isinstance(asset_type, dict):
            raise InvalidData("fmarket: asset-allocation row assetType is not an object")
        asset_class = canonical_enum_tag(
            optional_present(asset_type, "code"),
            {"STOCK", "BOND", "CASH"},
            "fmarket asset-allocation class code",
        )
        if seen_codes is not None:
            if asset_class in seen_codes:
                raise InvalidData(
                    f"fmarket: duplicate asset-allocation class {asset_class}"
                )
            seen_codes.add(asset_class)
        weight = _as_float(
            row.get("assetPercent"), f"asset-allocation {asset_class} weight"
        )
        if not (0.0 <= weight <= 100.0):
            raise InvalidData(
                f"fmarket: asset-allocation {asset_class} weight out of range: {weight}"
            )
        return AssetClassWeight(asset_class=asset_class, weight_pct=weight)

    # --- transport --------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "User-Agent": DEFAULT_UA,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _post(self, url, body, who):
        # ``json_body`` makes the shared transport issue a POST; transport errors are
        # wrapped as SourceUnavailable by the base. Keep ``_parse_json`` (who-context
        # message) and ``_unwrap`` (application-status envelope check) here.
        text = self._request_text(url, params=None, headers=self._headers(), json_body=body)
        return self._unwrap(_parse_json(text, who), who)

    def _get(self, url, who):
        text = self._request_text(url, params=None, headers=self._headers())
        return self._unwrap(_parse_json(text, who), who)

    @staticmethod
    def _unwrap(parsed, who):
        if not isinstance(parsed, dict):
            raise InvalidData(f"fmarket: unexpected top-level JSON from {who}")
        # The provider wraps every response in an application-level status/code
        # envelope. A 2xx HTTP transport can still carry an application error
        # (e.g. status:500). Treat any non-2xx application status as a source
        # failure so it never parses as success. The envelope is required: missing
        # both status and code means the response shape is not a valid Fmarket
        # envelope and must raise InvalidData (issue #41).
        status_raw = parsed.get("status")
        code_raw = parsed.get("code")
        if status_raw is None and code_raw is None:
            raise InvalidData(f"fmarket: missing status/code envelope from {who}")
        for key, raw in (("status", status_raw), ("code", code_raw)):
            if raw is None:
                continue
            # Issue #41 (reopen): the application status/code is an integer. A bare
            # int(raw) silently TRUNCATES a fractional float (int(200.9) -> 200),
            # letting a malformed non-2xx-ish value pass as success, and bool would
            # coerce (int(True) -> 1). Reject a bool or a non-integral float before
            # coercion; integral floats, ints, and digit strings remain valid.
            if isinstance(raw, bool) or (isinstance(raw, float) and not raw.is_integer()):
                raise InvalidData(
                    f"fmarket: non-integer {key} in {who} envelope: {raw!r}"
                )
            try:
                status = int(raw)
            except (TypeError, ValueError) as exc:
                raise InvalidData(
                    f"fmarket: non-integer {key} in {who} envelope: {raw!r}"
                ) from exc
            if not (200 <= status < 300):
                msg = parsed.get("message") or ""
                raise SourceUnavailable(
                    f"fmarket: {who} returned application {key}={status} {msg}".strip()
                )
        return parsed


_DEFAULT_FROM = "2000-01-01"  # far before any VN fund inception


def _coerce_date(value, label) -> date:
    """Coerce a ``date``/``datetime``/``YYYY-MM-DD`` string to a ``date``.

    Raises :class:`InvalidData` (never a raw ``ValueError``/``TypeError``) on a
    malformed caller-supplied date so the public method stays failover-safe.
    """
    try:
        return validate_iso_date_string(value, label=label)
    except InvalidData as exc:
        raise InvalidData(f"fmarket: malformed {label} {value!r}") from exc


def _today() -> date:
    """The current UTC calendar date — the injected `today` for end-gap freshness.

    A `date` (not a `datetime`): the success-path end-gap warning judges a calendar
    gap, never a fetch timestamp. Tests pin this for determinism; it never leaks into
    ``NavHistory.fetched_at_utc`` (which stays the real ``datetime.now(timezone.utc)``).
    """
    return datetime.now(timezone.utc).date()


def _today_ymd() -> str:
    return _today().isoformat()


def _nav_end_gap_warning(points, to_date, today) -> tuple[str, ...]:
    """Cadence-relative end-gap warning for a SUCCESSFUL ``nav_history`` return.

    ``points`` is a non-empty, ascending, deduped ``tuple[NavPoint, ...]`` (the caller
    guarantees this). ``to_date`` is the requested window end (``date`` or ``None`` for
    an open/now window). ``today`` is a REQUIRED injected ``date`` — this function MUST
    NOT call ``datetime.now()`` / ``date.today()`` so it is fully deterministic.

    Returns a one-element tuple naming the gap/cadence/threshold when the latest NAV is
    older than the fund's own (trailing) cadence allows, else ``()``. Never raises.
    """
    # reference: open/now window -> today (cannot expect NAV beyond today); a past
    # window -> its end. min() clamps a future to_date back to today.
    reference = min(to_date, today) if to_date is not None else today
    gap_days = (reference - points[-1].date).days
    if gap_days <= 0:
        return ()  # series reaches the window end -> fresh
    if len(points) >= 2:
        diffs = [
            (points[i + 1].date - points[i].date).days
            for i in range(len(points) - 1)
        ]
        window = diffs[-_NAV_END_GAP_CADENCE_WINDOW:]  # last N (all if fewer) — CURRENT regime
        typical_gap = max(1, int(statistics.median(window)))  # robust to a single holiday outlier
        threshold = max(_NAV_END_GAP_FACTOR * typical_gap, _NAV_END_GAP_MIN_DAYS)
    else:
        typical_gap = None  # single point: cadence unknown
        threshold = _NAV_END_GAP_SINGLE_POINT_DAYS
    if gap_days > threshold:
        cadence = "unknown (single NAV point)" if typical_gap is None else f"~{typical_gap}d"
        return (
            f"{_NAV_END_GAP}: latest NAV {points[-1].date.isoformat()} is {gap_days}d "
            f"before {reference.isoformat()} (typical cadence {cadence}; "
            f"threshold {threshold}d) — fund NAV feed may be delayed, paused, or the "
            f"fund dormant",
        )
    return ()


def _fund_nav_stale_warning(funds, today, *, threshold_days=_FUND_NAV_STALE_DAYS) -> tuple[str, ...]:
    """List-level NAV-staleness warning for a SUCCESSFUL ``list_funds`` return.

    For each ``Fund`` with a known ``nav_as_of`` (``None`` is NEVER flagged — unknown
    is not stale, and a date is never invented), compute the CALENDAR-day gap to the
    injected ``today``; the fund is stale iff ``gap > threshold_days`` (so ``gap ==
    threshold_days`` is fresh, ``gap == threshold_days + 1`` stale).

    ``today`` is a REQUIRED injected ``date`` — this function MUST NOT call
    ``datetime.now()`` / ``date.today()`` so it is fully deterministic. Returns a
    one-element tuple naming the stale fund codes (@ their ``nav_as_of``, capped at
    ``_FUND_NAV_STALE_CAP`` codes + ``+M more``) when ≥1 fund is stale, else ``()``.
    Leak-safe: built only from fund codes + dates — no exception trail, no secrets.
    """
    stale = [
        f
        for f in funds
        if f.nav_as_of is not None and (today - f.nav_as_of).days > threshold_days
    ]
    if not stale:
        return ()
    shown = stale[:_FUND_NAV_STALE_CAP]
    enumerated = ", ".join(f"{f.code}@{f.nav_as_of.isoformat()}" for f in shown)
    more = len(stale) - len(shown)
    if more > 0:
        enumerated = f"{enumerated}, +{more} more"
    detail = (
        f"{len(stale)} fund(s) NAV older than {threshold_days}d as of "
        f"{today.isoformat()}: {enumerated}"
    )
    return (f"{_FUND_NAV_STALE}: {detail}",)


def _validate_product_id(product_id) -> int:
    """Validate a fund ``product_id`` and return a clean positive int.

    Raises :class:`InvalidData` for non-integers, non-positive values, or types
    that would otherwise silently truncate (e.g. ``3.7 -> 3``) or crash.
    """
    if isinstance(product_id, bool) or not isinstance(product_id, int):
        raise InvalidData(f"fmarket: product_id must be a positive integer, got {type(product_id).__name__}")
    if product_id <= 0:
        raise InvalidData(f"fmarket: product_id must be positive, got {product_id!r}")
    return product_id
