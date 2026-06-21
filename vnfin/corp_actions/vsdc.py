"""VSDC cash-dividend scrape adapter (issue #163).

Source: the Vietnam Securities Depository & Clearing (VSDC) public announcement pages,
``GET https://vsd.vn/vi/ad/{id}`` — server-rendered HTML, keyless, ``{id}`` a sequential
integer (~197000 in 2025). The depository publishes record date + pay date + ratio/cash
but **NO ex-date**, so every emitted event's ``ex_date`` is ``None`` (the finfo
enrichment leg is held for v2) and carries the ``ex_date_unavailable`` token.

The scrape is materially more fragile than the library's JSON sources, so ALL HTML
parsing is isolated behind the tight contract in :meth:`parse_announcement` (a pure
function of the HTML string, fixture-pinned), label→value pairing keys on the
``item-info`` / ``item-info-main`` CSS classes (never on element position or
``col-md-*`` widths, which vary across pages), and a recognized cash-dividend page whose
amounts cannot be parsed emits the never-silent ``vsdc_parse_degraded`` token rather than
silently corrupting or dropping the event.

Discovery (finding a ticker's announcement IDs) uses two observed signals: a per-page
"Tin cùng tổ chức" same-org sidebar of ``/vi/ad/{id}`` links (deep history), and a
bounded recent-ID-window scan downward from a documented watermark when no seed is given.
All endpoints/shapes were learned from the provider's own pages (clean-room; no vnstock).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Optional

from ..exceptions import InvalidData, SourceError
from ..validation import validate_date_range, validate_non_empty_string
from .base import VN_TZ, CorpActionSource
from .models import CashDividendEvent, DividendHistory

# Warning tokens (#163) — declared as EXACT STATIC STRING LITERALS at the emission module so
# the #188 forward-discovery AST scanner resolves them from the warnings positions below.
# Kept in lockstep with the skills/vnfin/SKILL.md "## Warning tokens" table and the
# tests/test_docs_contract.py::_WARNING_TOKENS_180 tuple.
EX_DATE_UNAVAILABLE = "ex_date_unavailable"
VSDC_PARSE_DEGRADED = "vsdc_parse_degraded"
CORP_ACTION_SOURCE_PARTIAL = "corp_action_source_partial"

#: Documented default recent-ID watermark for the no-seed recent-window scan. Override
#: via the constructor ``latest_id=`` — this is a rolling hint, not a hard bound.
LATEST_ID_HINT = 197000

#: Default cap on the number of announcement pages fetched per ``dividends`` call.
DEFAULT_MAX_FETCH = 300

# --- title / fields ------------------------------------------------------------ #
_TITLE_RE = re.compile(
    r'<h3[^>]*class="[^"]*\btitle-category\b[^"]*"[^>]*>(?P<title>.*?)</h3>',
    re.IGNORECASE | re.DOTALL,
)
# Provider publish time: "Cập nhật ngày DD/MM/YYYY - HH:MM:SS" inside time-newstcph.
_AS_OF_RE = re.compile(
    r'class="[^"]*\btime-newstcph\b[^"]*"[^>]*>(?P<body>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
_AS_OF_TS_RE = re.compile(r"(?P<d>\d{2})/(?P<m>\d{2})/(?P<y>\d{4})\s*-\s*(?P<H>\d{2}):(?P<M>\d{2}):(?P<S>\d{2})")

# A structured info <div ... class="... item-info ...">VALUE</div> block. We capture the
# class list and the inner text and classify it as a LABEL (item-info, NOT item-info-main)
# or a VALUE (item-info-main) by the class — NEVER by the col-md-* width.
_INFO_DIV_RE = re.compile(
    r'<div[^>]*class="(?P<cls>[^"]*\bitem-info\b[^"]*)"[^>]*>(?P<inner>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)

# Ratio + cash anchor (the line uniquely identified by the cash parenthetical).
_CASH_RE = re.compile(r"được\s+nhận\s+(?P<cash>[\d.]+)\s*đồng", re.IGNORECASE)
_RATIO_RE = re.compile(r"(?P<pct>\d+(?:[.,]\d+)?)\s*%\s*/?\s*cổ\s*phiếu", re.IGNORECASE)
# Pay-date line: either label, followed (on the same line) by a DD/MM/YYYY.
_PAY_LINE_RE = re.compile(
    r"(?:Ngày\s+thanh\s+toán|Thời\s+gian\s+thực\s+hiện)\s*:\s*(?P<date>\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
_DATE_DMY_RE = re.compile(r"(?P<d>\d{2})/(?P<m>\d{2})/(?P<y>\d{4})")
_DIV_YEAR_RE = re.compile(r"năm\s+(?P<y>\d{4})", re.IGNORECASE)
# Same-org sidebar links: /vi/ad/{id}. Restricted to the ad path so nav/category
# links (/vi/, /alo/…, /gt-…) are ignored.
_AD_LINK_RE = re.compile(r'href="/vi/ad/(?P<id>\d+)"', re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_accents(text: str) -> str:
    """Lowercase + strip Vietnamese diacritics for robust accent-insensitive matching."""
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn").lower()


def _text(raw: str) -> str:
    """Strip tags + collapse whitespace from an HTML fragment."""
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", raw)).strip()


def _is_cash_dividend(*texts: str) -> bool:
    """A cash dividend mentions 'cổ tức' AND 'bằng tiền' (accent-insensitive)."""
    blob = _strip_accents(" ".join(t for t in texts if t))
    return "co tuc" in blob and "bang tien" in blob


def _parse_dmy(token: str) -> Optional[date]:
    m = _DATE_DMY_RE.fullmatch(token)
    if not m:
        return None
    try:
        return date(int(m.group("y")), int(m.group("m")), int(m.group("d")))
    except ValueError:
        return None


def _parse_vn_number(token: str) -> Optional[float]:
    """Parse a Vietnamese-formatted number ('1.200' -> 1200.0, '500' -> 500.0)."""
    cleaned = token.replace(".", "").replace(",", ".")
    try:
        val = float(cleaned)
    except ValueError:
        return None
    return val


class VsdcCashDividendSource(CorpActionSource):
    """VSDC public cash-dividend announcement scrape adapter (VND per share).

    v1 = CASH dividends only. ``ex_date`` is always ``None`` (depository publishes none;
    finfo leg held) and every event carries ``ex_date_unavailable``; every result carries
    ``corp_action_source_partial``. STOCK/RIGHTS/BONUS are deferred to v2.
    """

    name = "vsdc"
    BASE_URL = "https://vsd.vn/vi/ad/"

    def __init__(self, *args, latest_id: int = LATEST_ID_HINT, **kwargs):
        super().__init__(*args, **kwargs)
        self.latest_id = latest_id

    # --- transport ------------------------------------------------------------ #
    def fetch_announcement(self, announcement_id: int) -> str:
        """Fetch one announcement page; transport failures wrap as SourceUnavailable."""
        return self._request_text(self.BASE_URL + str(announcement_id))

    # --- structured-field helpers --------------------------------------------- #
    @staticmethod
    def _info_fields(html: str) -> dict[str, str]:
        """Pair LABEL→VALUE structured rows by the item-info / item-info-main classes.

        We scan every ``item-info`` div in document order: a div WITHOUT
        ``item-info-main`` is a label, the next div WITH ``item-info-main`` is its value.
        Pairing is purely by class — the ``col-md-*`` widths are never consulted.
        """
        fields: dict[str, str] = {}
        pending_label: Optional[str] = None
        for m in _INFO_DIV_RE.finditer(html):
            cls = m.group("cls")
            inner = _text(m.group("inner"))
            is_value = "item-info-main" in cls
            if is_value:
                if pending_label is not None:
                    fields.setdefault(pending_label, inner)
                    pending_label = None
            else:
                # a label div (item-info but not item-info-main)
                pending_label = inner
        return fields

    def _parse_as_of(self, html: str) -> Optional[datetime]:
        m = _AS_OF_RE.search(html)
        if not m:
            return None
        ts = _AS_OF_TS_RE.search(m.group("body"))
        if not ts:
            return None
        try:
            return datetime(
                int(ts.group("y")), int(ts.group("m")), int(ts.group("d")),
                int(ts.group("H")), int(ts.group("M")), int(ts.group("S")),
                tzinfo=VN_TZ,
            )
        except ValueError:
            return None

    @staticmethod
    def _justify_lines(html: str) -> list[str]:
        """The <br />-separated free-text lines of the justify block (ratio + pay date)."""
        m = re.search(
            r'text-align:\s*justify;?[^>]*>(?P<body>.*?)</div>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if not m:
            return []
        body = m.group("body")
        # split on <br ...> then strip remaining tags per line.
        raw_lines = re.split(r"<br\s*/?>", body, flags=re.IGNORECASE)
        return [_text(line) for line in raw_lines if _text(line)]

    # --- the pure parser ------------------------------------------------------ #
    def parse_announcement(
        self, html: str, *, announcement_id: Optional[int] = None
    ) -> Optional[CashDividendEvent]:
        """Parse one announcement page → a CashDividendEvent, or None if not a cash div.

        Returns ``None`` when the page is not a cash dividend at all (no degraded token).
        Returns a degraded event (amounts ``None`` + ``vsdc_parse_degraded``) when the
        page IS a cash dividend with a record date but the ratio/cash cannot be parsed.
        """
        if not isinstance(html, str) or not html.strip():
            raise InvalidData("vsdc: empty announcement HTML")

        title_m = _TITLE_RE.search(html)
        title = _text(title_m.group("title")) if title_m else ""
        fields = self._info_fields(html)
        reason = fields.get("Lý do mục đích:", "")

        # Detection: cash dividend iff title OR reason carries 'cổ tức' + 'bằng tiền'.
        if not _is_cash_dividend(title, reason):
            return None

        # Ticker: prefer the structured 'Mã chứng khoán:' (exact label), cross-check title.
        code = fields.get("Mã chứng khoán:")
        if not code:
            # fall back to the title prefix before the first ':'
            code = title.split(":", 1)[0].strip() if ":" in title else ""
        code = (code or "").strip().upper()
        if not code:
            raise InvalidData("vsdc: cash-dividend page with no resolvable ticker")

        exchange = fields.get("Nơi giao dịch:") or None
        record_date = _parse_dmy((fields.get("Ngày đăng ký cuối cùng:") or "").strip())

        div_year = None
        ym = _DIV_YEAR_RE.search(" ".join(t for t in (title, reason) if t))
        if ym:
            div_year = int(ym.group("y"))

        as_of = self._parse_as_of(html)

        # Ratio + cash from the justify block (the cash parenthetical anchors the line).
        cash_per_share: Optional[float] = None
        ratio_pct: Optional[float] = None
        pay_date: Optional[date] = None
        lines = self._justify_lines(html)
        for line in lines:
            cash_m = _CASH_RE.search(line)
            if cash_m and cash_per_share is None:
                cash_per_share = _parse_vn_number(cash_m.group("cash"))
                ratio_m = _RATIO_RE.search(line)
                if ratio_m:
                    ratio_pct = _parse_vn_number(ratio_m.group("pct"))
            pay_m = _PAY_LINE_RE.search(line)
            if pay_m and pay_date is None:
                pay_date = _parse_dmy(pay_m.group("date"))

        warnings: list[str] = [EX_DATE_UNAVAILABLE]
        # Degradation: a recognized cash dividend with a record date but no parseable
        # ratio/cash → never-silent token, amounts stay None.
        if cash_per_share is None and ratio_pct is None:
            warnings.append(VSDC_PARSE_DEGRADED)

        return CashDividendEvent(
            code=code,
            kind="CASH",
            cash_per_share=cash_per_share,
            ratio_pct=ratio_pct,
            ex_date=None,
            record_date=record_date,
            pay_date=pay_date,
            div_year=div_year,
            source=self.name,
            as_of=as_of,
            exchange=exchange,
            announcement_id=announcement_id,
            warnings=tuple(warnings),
        )

    # --- discovery ------------------------------------------------------------ #
    @staticmethod
    def discover_same_org_ids(html: str) -> tuple[int, ...]:
        """Extract the same-org sidebar's ``/vi/ad/{id}`` announcement IDs (deduped, ordered)."""
        seen: dict[int, None] = {}
        for m in _AD_LINK_RE.finditer(html):
            seen.setdefault(int(m.group("id")), None)
        return tuple(seen.keys())

    # --- top-level dividends -------------------------------------------------- #
    def dividends(
        self,
        symbol: str,
        *,
        start=None,
        end=None,
        seed_id: Optional[int] = None,
        max_fetch: int = DEFAULT_MAX_FETCH,
    ) -> DividendHistory:
        """Discover, fetch and parse a company's cash-dividend history (VND/share).

        Discovery: a caller-supplied ``seed_id`` (preferred), else a bounded recent-ID
        window scan downward from ``latest_id`` to find a seed; then the seed page's
        same-org sidebar is crawled to enumerate the company's announcement IDs. Each
        page is fetched + parsed; cash events for ``symbol`` within ``[start, end]`` are
        kept. Every event carries ``ex_date_unavailable``; the result always carries
        ``corp_action_source_partial`` (v1 = the VSDC spine alone, no ex-date leg).
        """
        code = validate_non_empty_string(symbol, "symbol").upper()
        lo, hi = validate_date_range(start, end, allow_none=True, name="dividends")

        ids = self._discover_ids(code, seed_id=seed_id, max_fetch=max_fetch)

        events: list[CashDividendEvent] = []
        for ann_id in ids:
            try:
                html = self.fetch_announcement(ann_id)
            except SourceError:
                # an individual page failing must not sink the whole crawl.
                continue
            ev = self.parse_announcement(html, announcement_id=ann_id)
            if ev is None or ev.code != code:
                continue
            if not self._in_window(ev.record_date, lo, hi):
                continue
            events.append(ev)

        # deterministic order: record_date (None last), then announcement_id.
        events.sort(
            key=lambda e: (
                e.record_date is None,
                e.record_date or date.min,
                e.announcement_id or 0,
            )
        )
        as_of_values = [e.as_of for e in events if e.as_of is not None]
        list_as_of = max(as_of_values) if as_of_values else None
        fetched_at = datetime.now(tz=VN_TZ)

        return DividendHistory(
            code=code,
            source=self.name,
            currency="VND",
            events=tuple(events),
            fetched_at_utc=fetched_at,
            as_of=list_as_of,
            warnings=(CORP_ACTION_SOURCE_PARTIAL,),
        )

    def _discover_ids(
        self, code: str, *, seed_id: Optional[int], max_fetch: int
    ) -> tuple[int, ...]:
        """Resolve the set of announcement IDs to fetch for ``code``.

        With a ``seed_id``: include the seed + crawl its same-org sidebar. Without a seed:
        scan a bounded recent-ID window downward from ``latest_id`` to find the first page
        whose ticker is ``code``, then crawl that seed's sidebar.
        """
        if seed_id is not None:
            return self._crawl_from_seed(seed_id, max_fetch=max_fetch)

        # no seed → bounded downward recent-window scan to find one.
        window = min(max_fetch, DEFAULT_MAX_FETCH)
        for offset in range(window):
            ann_id = self.latest_id - offset
            if ann_id <= 0:
                break
            try:
                html = self.fetch_announcement(ann_id)
            except SourceError:
                continue
            ev = self.parse_announcement(html, announcement_id=ann_id)
            if ev is not None and ev.code == code:
                return self._crawl_from_seed(ann_id, max_fetch=max_fetch, seed_html=html)
        return ()

    def _crawl_from_seed(
        self, seed_id: int, *, max_fetch: int, seed_html: Optional[str] = None
    ) -> tuple[int, ...]:
        """Seed + its same-org sidebar IDs, capped at ``max_fetch`` (seed first, deduped)."""
        if seed_html is None:
            try:
                seed_html = self.fetch_announcement(seed_id)
            except SourceError:
                seed_html = None
        ordered: dict[int, None] = {seed_id: None}
        if seed_html is not None:
            for sid in self.discover_same_org_ids(seed_html):
                ordered.setdefault(sid, None)
        return tuple(ordered.keys())[:max_fetch]

    @staticmethod
    def _in_window(d: Optional[date], lo: Optional[date], hi: Optional[date]) -> bool:
        if d is None:
            # no record date → keep only when the window is fully open.
            return lo is None and hi is None
        if lo is not None and d < lo:
            return False
        if hi is not None and d > hi:
            return False
        return True
