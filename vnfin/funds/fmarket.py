"""Fmarket fund-data adapter (clean-room).

Talks to Fmarket's own public, no-auth JSON API (``api.fmarket.vn``) for VN
open-ended mutual funds:

  - ``list_funds()``  -> POST /res/products/filter
  - ``nav_history(product_id)`` -> POST /res/product/get-nav-history  (isAllData:1)
  - ``holdings(product_id)``    -> GET  /res/products/{id}

NAV is VND per fund unit; ``navDate`` is ``YYYY-MM-DD``. Provenance, compliance,
and shape notes live in ``docs/sources/funds-fmarket.md``.

Transport errors are wrapped as :class:`SourceUnavailable`; malformed / garbage
payloads as :class:`InvalidData`; no-data responses as :class:`EmptyData`. This
keeps the adapter failover-safe (it never leaks raw exceptions to callers).

Runtime fetch only — no caching or redistribution of provider data.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from ..exceptions import EmptyData, InvalidData, SourceUnavailable
from ..transport import DEFAULT_UA, HttpDataSource
from ..validation import validate_iso_date_string
from .models import Fund, FundHolding, FundList, NavHistory, NavPoint

_BASE_URL = "https://api.fmarket.vn"
_FILTER_PATH = "/res/products/filter"
_NAV_PATH = "/res/product/get-nav-history"
_DETAIL_PATH = "/res/products"  # + /{id}


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
        return FundList(
            funds=tuple(funds),
            source=self.name,
            currency="VND",
            fetched_at_utc=datetime.now(timezone.utc),
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
        lo_str = lo.isoformat() if lo is not None else _DEFAULT_FROM
        hi_str = hi.isoformat() if hi is not None else _today_ymd()
        body = {
            "isAllData": 1,
            "productId": fid,
            "fromDate": lo_str,
            "toDate": hi_str,
        }
        parsed = self._post(_BASE_URL + _NAV_PATH, body, who="nav-history")
        rows = _require_array(parsed.get("data"), who="nav-history data")
        if rows is None or len(rows) == 0:
            raise EmptyData(f"fmarket: no NAV history for product {product_id}")
        seen_dates: set[date] = set()
        points: list[NavPoint] = []
        for r in rows:
            # Issue #21 (reopen): a NAV row that exposes a productId must identify
            # the requested fund. A present productId must be a non-bool int equal
            # to fid; a mismatched/malformed value is a provider/cache identity
            # error, not data to stamp as the requested product.
            if isinstance(r, dict):
                row_pid = r.get("productId")
                if row_pid is not None and (
                    isinstance(row_pid, bool) or not isinstance(row_pid, int) or row_pid != fid
                ):
                    raise InvalidData(
                        f"fmarket: nav row productId {row_pid!r} != requested {fid}"
                    )
            point = self._parse_nav_point(r)
            if point.date in seen_dates:
                raise InvalidData(
                    f"fmarket: duplicate navDate {point.date.isoformat()} for product {product_id}"
                )
            seen_dates.add(point.date)
            points.append(point)
        points.sort(key=lambda p: p.date)
        # The server only reliably enforces toDate, and not even that near recent
        # boundaries — so filter BOTH bounds client-side for an exact window.
        if lo is not None:
            points = [p for p in points if p.date >= lo]
        if hi is not None:
            points = [p for p in points if p.date <= hi]
        if not points:
            raise EmptyData(f"fmarket: no NAV history for product {product_id} in range")
        return NavHistory(
            product_id=fid,
            points=tuple(points),
            source=self.name,
            currency="VND",
            value_unit="VND/unit",  # NAV is money per fund unit
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def holdings(self, product_id: int) -> tuple[FundHolding, ...]:
        """Top disclosed portfolio holdings for a fund (by internal ``product_id``)."""
        fid = _validate_product_id(product_id)
        url = f"{_BASE_URL}{_DETAIL_PATH}/{fid}"
        parsed = self._get(url, who="holdings")
        data = _require_data_object(parsed.get("data"), who="holdings")
        # Issue #21 (reopen): validate the returned detail identity before trusting
        # its holdings. A present `id` must be a non-bool int equal to fid (a
        # mismatch is a wrong-fund detail document). `code` has no requested
        # counterpart to compare, but a present value must still be a non-empty
        # canonical string so a corrupt identity shape is not silently accepted.
        detail_id = data.get("id")
        if detail_id is not None and (
            isinstance(detail_id, bool) or not isinstance(detail_id, int) or detail_id != fid
        ):
            raise InvalidData(
                f"fmarket: holdings detail id {detail_id!r} != requested {fid}"
            )
        detail_code = data.get("code")
        if detail_code is not None and (
            not isinstance(detail_code, str) or not detail_code.strip()
        ):
            raise InvalidData(
                f"fmarket: holdings detail code {detail_code!r} is not a non-empty string"
            )
        rows = _require_array(
            data.get("productTopHoldingList"), who="holdings productTopHoldingList"
        )
        if rows is None or len(rows) == 0:
            raise EmptyData(f"fmarket: no holdings for product {product_id}")
        seen: set[str] = set()
        holdings = tuple(self._parse_holding(r, seen) for r in rows)
        total_weight = sum(h.weight_pct for h in holdings)
        if total_weight > 100.0 + 1e-9:
            raise InvalidData(
                f"fmarket: aggregate holdings weight exceeds 100% ({total_weight})"
            )
        return holdings

    # --- row parsers ------------------------------------------------------

    @staticmethod
    def _parse_fund(row) -> Fund:
        if not isinstance(row, dict):
            raise InvalidData("fmarket: fund row is not an object")
        code = row.get("code")
        short = row.get("shortName")
        if code is not None:
            if not isinstance(code, str):
                raise InvalidData("fmarket: fund row code is not a string")
            raw_code = code
        elif short is not None:
            if not isinstance(short, str):
                raise InvalidData("fmarket: fund row shortName is not a string")
            raw_code = short
        else:
            raise InvalidData("fmarket: fund row missing code")
        code = raw_code.strip()
        if not code:
            raise InvalidData("fmarket: fund row missing code")
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
        return Fund(
            code=str(code),
            name=name,
            id=fid,
            nav=nav,
            manager=manager,
            asset_type=asset_type,
            currency="VND",
        )

    @staticmethod
    def _parse_nav_point(row) -> NavPoint:
        if not isinstance(row, dict):
            raise InvalidData("fmarket: nav row is not an object")
        raw_date = row.get("navDate")
        if not raw_date:
            raise InvalidData("fmarket: nav row missing navDate")
        try:
            d = validate_iso_date_string(raw_date, label="navDate")
        except InvalidData as exc:
            raise InvalidData(f"fmarket: malformed navDate {raw_date!r}") from exc
        nav = _as_float(row.get("nav"), f"nav on {raw_date}")
        # Issue #13: zero NAV is not a valid market observation.
        if nav <= 0:
            raise InvalidData(f"fmarket: non-positive nav on {raw_date}")
        return NavPoint(date=d, nav=nav)

    @staticmethod
    def _parse_holding(row, seen_codes=None) -> FundHolding:
        if not isinstance(row, dict):
            raise InvalidData("fmarket: holding row is not an object")
        raw_code = row.get("stockCode")
        if not raw_code or not isinstance(raw_code, str):
            raise InvalidData("fmarket: holding row missing stockCode")
        stock_code = raw_code.strip().upper()
        if not stock_code:
            raise InvalidData("fmarket: holding row has blank stockCode")
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
        )

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


def _today_ymd() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


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
