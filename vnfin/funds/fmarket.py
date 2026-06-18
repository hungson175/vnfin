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
from .models import Fund, FundHolding, FundList, NavHistory, NavPoint

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

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
    import math

    if value is None:
        raise InvalidData(f"fmarket: missing numeric value ({ctx})")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidData(f"fmarket: malformed number ({ctx})") from exc
    if not math.isfinite(out):
        raise InvalidData(f"fmarket: non-finite number ({ctx})")
    return out


class FmarketFundSource:
    """Adapter for Fmarket's public fund-data API.

    ``http_get(url, params=None, headers=None, json_body=None) -> text``. When
    ``json_body`` is provided the default transport issues a POST with that JSON
    body; otherwise it issues a GET. Injectable for testing.
    """

    name = "fmarket"

    def __init__(self, http_get=None, timeout: float = 25.0):
        self._http_get = http_get or self._default_http_get
        self._timeout = timeout

    # --- public API -------------------------------------------------------

    def list_funds(self, asset_type=None, search="", page_size: int = 100) -> FundList:
        """List VN open-ended mutual funds.

        ``asset_type`` optionally filters by provider asset-class code (e.g.
        ``"STOCK"``); ``search`` does a free-text name/code search.
        """
        body = {
            "types": ["NEW_FUND", "TRADING_FUND"],
            "sortField": "navTo6Months",
            "sortOrder": "DESC",
            "page": 1,
            "pageSize": page_size,
            "isIpo": False,
            "fundAssetTypes": [asset_type] if asset_type else [],
            "searchField": search or "",
        }
        parsed = self._post(_BASE_URL + _FILTER_PATH, body, who="filter")
        data = parsed.get("data") or {}
        rows = data.get("rows")
        if not rows:
            raise EmptyData("fmarket: no funds returned")
        funds = tuple(self._parse_fund(r) for r in rows)
        return FundList(
            funds=funds,
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
            "productId": int(product_id),
            "fromDate": lo_str,
            "toDate": hi_str,
        }
        parsed = self._post(_BASE_URL + _NAV_PATH, body, who="nav-history")
        rows = parsed.get("data")
        if not rows:
            raise EmptyData(f"fmarket: no NAV history for product {product_id}")
        points = sorted(
            (self._parse_nav_point(r) for r in rows), key=lambda p: p.date
        )
        # The server only reliably enforces toDate, and not even that near recent
        # boundaries — so filter BOTH bounds client-side for an exact window.
        if lo is not None:
            points = [p for p in points if p.date >= lo]
        if hi is not None:
            points = [p for p in points if p.date <= hi]
        if not points:
            raise EmptyData(f"fmarket: no NAV history for product {product_id} in range")
        return NavHistory(
            product_id=int(product_id),
            points=tuple(points),
            source=self.name,
            currency="VND",
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def holdings(self, product_id: int) -> tuple[FundHolding, ...]:
        """Top disclosed portfolio holdings for a fund (by internal ``product_id``)."""
        url = f"{_BASE_URL}{_DETAIL_PATH}/{int(product_id)}"
        parsed = self._get(url, who="holdings")
        data = parsed.get("data") or {}
        rows = data.get("productTopHoldingList")
        if not rows:
            raise EmptyData(f"fmarket: no holdings for product {product_id}")
        return tuple(self._parse_holding(r) for r in rows)

    # --- row parsers ------------------------------------------------------

    @staticmethod
    def _parse_fund(row) -> Fund:
        if not isinstance(row, dict):
            raise InvalidData("fmarket: fund row is not an object")
        code = row.get("code") or row.get("shortName")
        fid = row.get("id")
        if code is None or fid is None:
            raise InvalidData("fmarket: fund row missing code/id")
        try:
            fid = int(fid)
        except (TypeError, ValueError) as exc:
            raise InvalidData("fmarket: fund row has non-integer id") from exc
        nav = _as_float(row.get("nav"), f"fund {code} nav")
        if nav < 0:
            raise InvalidData(f"fmarket: negative nav for fund {code}")
        owner = row.get("owner") or {}
        if not isinstance(owner, dict):
            raise InvalidData(f"fmarket: fund {code} owner is not an object")
        manager = owner.get("name") or owner.get("shortName") or ""
        asset = row.get("dataFundAssetType") or {}
        if not isinstance(asset, dict):
            raise InvalidData(
                f"fmarket: fund {code} dataFundAssetType is not an object"
            )
        asset_type = asset.get("code") or ""
        return Fund(
            code=str(code),
            name=str(row.get("name") or code),
            id=fid,
            nav=nav,
            manager=str(manager),
            asset_type=str(asset_type),
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
            d = datetime.strptime(str(raw_date), "%Y-%m-%d").date()
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"fmarket: malformed navDate {raw_date!r}") from exc
        nav = _as_float(row.get("nav"), f"nav on {raw_date}")
        if nav < 0:
            raise InvalidData(f"fmarket: negative nav on {raw_date}")
        return NavPoint(date=d, nav=nav)

    @staticmethod
    def _parse_holding(row) -> FundHolding:
        if not isinstance(row, dict):
            raise InvalidData("fmarket: holding row is not an object")
        stock_code = row.get("stockCode")
        if not stock_code:
            raise InvalidData("fmarket: holding row missing stockCode")
        weight = _as_float(row.get("netAssetPercent"), f"holding {stock_code} weight")
        if not (0.0 <= weight <= 100.0):
            raise InvalidData(
                f"fmarket: holding {stock_code} weight out of range: {weight}"
            )
        industry = row.get("industry")
        price = row.get("price")
        price_unit = None
        if price is not None:
            # Provider price scale is unverified/ambiguous — keep it RAW, never
            # normalize. Surface the value plus an explicit "raw" unit tag so
            # callers never mistake it for a canonical money unit.
            price = _as_float(price, f"holding {stock_code} price")
            price_unit = "raw"
        return FundHolding(
            stock_code=str(stock_code),
            weight_pct=weight,
            industry=str(industry) if industry is not None else None,
            price_raw=price,
            price_unit=price_unit,
        )

    # --- transport --------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "User-Agent": _UA,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _post(self, url, body, who):
        try:
            text = self._http_get(url, None, self._headers(), body)
        except Exception as exc:  # transport-level
            raise SourceUnavailable(f"fmarket transport error ({who}): {exc}") from exc
        return self._unwrap(_parse_json(text, who), who)

    def _get(self, url, who):
        try:
            text = self._http_get(url, None, self._headers(), None)
        except Exception as exc:  # transport-level
            raise SourceUnavailable(f"fmarket transport error ({who}): {exc}") from exc
        return self._unwrap(_parse_json(text, who), who)

    @staticmethod
    def _unwrap(parsed, who):
        if not isinstance(parsed, dict):
            raise InvalidData(f"fmarket: unexpected top-level JSON from {who}")
        # The provider wraps every response in an application-level status/code
        # envelope. A 2xx HTTP transport can still carry an application error
        # (e.g. status:500). Treat any non-2xx application status as a source
        # failure so it never parses as success.
        for key in ("status", "code"):
            raw = parsed.get(key)
            if raw is None:
                continue
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

    def _default_http_get(self, url, params=None, headers=None, json_body=None):  # pragma: no cover - network
        import httpx

        transport = httpx.HTTPTransport(local_address="0.0.0.0")  # force IPv4
        with httpx.Client(transport=transport, timeout=self._timeout, headers=headers) as client:
            if json_body is not None:
                resp = client.post(url, params=params, json=json_body)
            else:
                resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.text


_DEFAULT_FROM = "2000-01-01"  # far before any VN fund inception


def _coerce_date(value, label) -> date:
    """Coerce a ``date``/``datetime``/``YYYY-MM-DD`` string to a ``date``.

    Raises :class:`InvalidData` (never a raw ``ValueError``/``TypeError``) on a
    malformed caller-supplied date so the public method stays failover-safe.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise InvalidData(f"fmarket: malformed {label} {value!r}") from exc


def _today_ymd() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
