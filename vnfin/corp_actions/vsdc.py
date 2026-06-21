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
silently corrupting or dropping the event. Under the #163 v1 de-scope a recognized ratio whose
line carries a tax / withholding signal (thuế / TNCN / khấu trừ) is net-vs-gross ambiguous and is
WITHHELD (``ratio_pct=None``) + disclosed via the distinct ``vsdc_ratio_tax_deferred`` token rather
than classified (net-vs-gross classification is deferred to v2).

Discovery (finding a ticker's announcement IDs) uses two observed signals: a per-page
"Tin cùng tổ chức" same-org sidebar of ``/vi/ad/{id}`` links, and a bounded recent-ID-window
scan downward from a documented watermark when no seed is given. From the seed the crawl is a
**bounded multi-hop BFS** over that same-org sidebar graph: each reachable page is fetched
exactly once (a visited-id set is the cycle guard — a sidebar that re-lists the seed or links
in a loop still terminates), and ``max_fetch`` caps the number of pages fetched. If the crawl
stops with the frontier not exhausted it surfaces the never-silent
``coverage_truncated_at_max_fetch`` token rather than returning a partial history as complete.
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
#: Per-result: the ratio context PARSED FINE but carries a tax / withholding signal (thuế / TNCN /
#: khấu trừ), so its `%` is net-vs-gross ambiguous. Under the #163 v1 de-scope we do NOT classify
#: net-vs-gross (an open-ended, silent-wrong-prone problem); the ratio is INTENTIONALLY withheld
#: (ratio_pct=None) and disclosed via this token. Distinct from vsdc_parse_degraded, which means a
#: field could not be PARSED (a data-quality fault). net-vs-gross classification is a v2 scope item.
VSDC_RATIO_TAX_DEFERRED = "vsdc_ratio_tax_deferred"
CORP_ACTION_SOURCE_PARTIAL = "corp_action_source_partial"
#: Per-result: the bounded crawl stopped at ``max_fetch`` with same-org announcements still
#: un-fetched, so the returned history is NOT exhaustive (never silently truncated).
COVERAGE_TRUNCATED_AT_MAX_FETCH = "coverage_truncated_at_max_fetch"
#: Per-result: ≥1 same-org announcement page failed to fetch OR parse during the crawl, so its
#: (and any onward-linked) events are absent — the history may be incomplete (never silent).
CORP_ACTION_FETCH_INCOMPLETE = "corp_action_fetch_incomplete"
#: Per-result: no-seed auto-discovery scanned its recent-ID window WITHOUT finding any
#: announcement page for the ticker, so the empty history is NOT a confirmed never-paid — the
#: discovery window may simply be too small / too recent. Pass a ``seed_id`` (or widen the
#: window) for an authoritative result. Absent whenever a seed was found or supplied.
CORP_ACTION_SEED_NOT_FOUND = "corp_action_seed_not_found"

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


# Net-of-tax / withholding SIGNAL tokens (accent-stripped). Under the #163 v1 de-scope a ratio from a
# line carrying ANY of these is net-vs-gross ambiguous and is WITHHELD (ratio_pct=None +
# vsdc_ratio_tax_deferred), NOT classified — net-vs-gross is a v2 scope decision. The set must cover
# EVERY net marker (not just the explicit tax noun) or a thuế-elided net figure leaks through as gross.
#: Standalone net/tax NOUNS — any one present on the line withholds. ròng / net are the bare "net"
#: words; thuế / TNCN the tax nouns. (All are word-boundary tokens: 'trong'->'trong'≠'rong',
#: 'internet'->'internet'≠'net', so neither false-trips.)
_RATIO_NET_NOUNS = frozenset({"thue", "tncn", "rong", "net"})
#: Net-received compound markers, matched as ADJACENT bigrams (not set co-occurrence) so the boilerplate
#: 'thực hiện … được nhận' on EVERY clean cash line — which has both 'thuc' and 'nhan' but never
#: adjacent — does not false-trip. These are the standard VN terms for the after-tax figure a holder
#: actually receives: thực nhận / thực lĩnh / thực lãnh.
_RATIO_NET_BIGRAMS = frozenset({("thuc", "nhan"), ("thuc", "linh"), ("thuc", "lanh")})


def _line_has_tax_signal(text: str) -> bool:
    """True when a justify ratio line carries a net-of-tax / withholding signal, so its `%` could be
    an after-tax figure that must never be served as the gross ratio. Detected by:
      - a standalone net/tax noun (thuế / TNCN / ròng / net), OR
      - an adjacent net-received bigram (thực nhận / thực lĩnh / thực lãnh), OR
      - the adjacent withholding bigram khấu trừ ('thuế' is often elided, e.g. 'đã thực hiện khấu
        trừ'); adjacency (not bare khau+tru co-occurrence) so an unrelated 'khấu hao' (depreciation)
        plus a stray 'trừ' does not false-trip.
    Word-boundary + accent-stripped throughout: 'thực hiện' (every page), 'được nhận' (every cash
    line), 'internet', 'trong', 'trước' (token 'truoc' != 'tru') never register. A line with any signal
    has its ratio WITHHELD under the v1 de-scope (#163) — we no longer classify net-vs-gross (v2). NOTE:
    a bare 'đã trừ' / 'sau khi trừ' with NO tax/net noun stays served (ambiguous 'deducted what?';
    matches the pre-de-scope behaviour) — tracked for the v2 classifier corpus."""
    toks = re.findall(r"[a-z0-9]+", _strip_accents(text))  # ORDERED, for the adjacency checks
    if set(toks) & _RATIO_NET_NOUNS:
        return True
    bigrams = set(zip(toks, toks[1:]))
    return bool(bigrams & _RATIO_NET_BIGRAMS) or ("khau", "tru") in bigrams

# A per-share cash amount in EITHER VSDC phrasing — "…được nhận 1.200 đồng" OR
# "…số tiền 1.200 đồng/cổ phiếu". Used only to COUNT tranches (multi-tranche detection); the
# primary cash value is still extracted via _CASH_RE. Non-overlapping findall counts a single
# "được nhận X đồng/cổ phiếu" once; a bare "10.000 đồng" (no anchor, no /cổ phiếu) is NOT matched,
# so a par/face-value mention never inflates the count.
_CASH_MENTION_RE = re.compile(
    r"(?:được\s+nhận\s+|số\s+tiền\s+)[\d.]+\s*đồng|[\d.]+\s*đồng\s*/\s*(?:cổ\s*phiếu|cp)\b",
    re.IGNORECASE,
)


def _parse_ratio_pct(token: str) -> Optional[float]:
    """Parse a dividend RATIO percentage. Unlike a VND cash amount, a percentage never uses a
    thousands separator — both '.' and ',' are DECIMAL points ('8.5' and '8,5' -> 8.5). (Cash keeps
    _parse_vn_number, where '.' is thousands: '1.200' -> 1200.)"""
    try:
        return float(token.replace(",", "."))
    except ValueError:
        return None


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

        # Par value ("Mệnh giá") for the cash↔ratio cross-check (cash ≈ ratio/100 × par). NOTE:
        # real VSDC pages do NOT carry a par field, so the no-par branch below is the real-world
        # path; par-confirm is a defensive bonus for the rare page that includes it. Trust only a
        # plausible par (≥ 1000 VND) so a stray small number never mis-confirms (SECONDARY).
        par: Optional[float] = None
        par_raw = fields.get("Mệnh giá:")
        if par_raw:
            par_num = re.search(r"[\d.]+", par_raw)
            if par_num:
                par_val = _parse_vn_number(par_num.group(0))
                if par_val is not None and par_val >= 1000:
                    par = par_val

        # Ratio + cash from the justify block (the cash parenthetical anchors the line).
        cash_per_share: Optional[float] = None
        ratio_pct: Optional[float] = None
        ratio_uncertain = False
        ratio_tax_deferred = False
        pay_date: Optional[date] = None
        lines = self._justify_lines(html)
        # Multi-tranche: a page listing >1 per-share cash amount (đợt 1 + đợt 2, in EITHER phrasing)
        # is a single CashDividendEvent in v1 that surfaces only the FIRST tranche — the dropped
        # tranche(s) are DISCLOSED via the degraded token rather than silently lost.
        cash_anchor_count = sum(len(_CASH_MENTION_RE.findall(line)) for line in lines)
        # A ratio token may live on a different justify line than the cash anchor; track whether the
        # page states ANY ratio so a cash-found-but-unpaired result degrades (never silent).
        any_ratio_token = any(_RATIO_RE.search(line) for line in lines)
        for line in lines:
            cash_m = _CASH_RE.search(line)
            if cash_m and cash_per_share is None:
                cash_per_share = _parse_vn_number(cash_m.group("cash"))
                prefix = line[: cash_m.start()]
                # DE-SCOPE (#163 v1): if the ratio line carries ANY tax / withholding signal its `%`
                # is net-vs-gross ambiguous — we do NOT classify it (that was open-ended and
                # silent-wrong-prone). WITHHOLD the ratio and disclose via vsdc_ratio_tax_deferred.
                # A ratio is served ONLY from a fully tax-free line. (v2 = classify behind a corpus.)
                matches = list(_RATIO_RE.finditer(prefix))
                had_ratio_token = bool(matches)
                if _line_has_tax_signal(line):
                    ratio_tax_deferred = True
                else:
                    # Tax-free line: serve a single unambiguous gross %/cổ phiếu, optionally
                    # par-cross-checked (cash ≈ ratio/100 × par). Bounded 0 < pct ≤ 100.
                    gross_cands = [
                        pct
                        for rm in matches
                        if (pct := _parse_ratio_pct(rm.group("pct"))) is not None
                        and 0 < pct <= 100
                    ]
                    chosen: Optional[float] = None
                    if par is not None and cash_per_share is not None:
                        tol = max(1.0, 0.005 * cash_per_share)
                        confirmed = sorted(
                            {c for c in gross_cands if abs(c / 100.0 * par - cash_per_share) <= tol}
                        )
                        if len(confirmed) == 1:
                            chosen = confirmed[0]
                        elif len(confirmed) > 1:
                            ratio_uncertain = True
                    elif len(gross_cands) == 1:
                        chosen = gross_cands[0]
                    ratio_pct = chosen
                    if had_ratio_token and chosen is None:
                        ratio_uncertain = True
            pay_m = _PAY_LINE_RE.search(line)
            if pay_m and pay_date is None:
                pay_date = _parse_dmy(pay_m.group("date"))

        warnings: list[str] = [EX_DATE_UNAVAILABLE]
        # Degradation (never-silent): surface the event with affected fields None + the token when a
        # PRIMARY field is unparseable (record date, or both ratio AND cash), the cash↔ratio pairing
        # is ambiguous/net-qualified, a ratio is stated on the page but NOT on the cash line
        # (cross-line, unpaired), or the page lists multiple cash tranches (only the first surfaced).
        cross_line_unpaired = (
            cash_per_share is not None
            and ratio_pct is None
            and any_ratio_token
            and not ratio_tax_deferred
        )
        if ratio_tax_deferred:
            warnings.append(VSDC_RATIO_TAX_DEFERRED)
        if (
            record_date is None
            or (cash_per_share is None and ratio_pct is None)
            or ratio_uncertain
            or cross_line_unpaired
            or cash_anchor_count > 1
        ):
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
        window scan downward from ``latest_id`` to find a seed; then a bounded multi-hop
        BFS over the seed's same-org sidebar graph enumerates the company's announcement
        IDs. Each page is fetched at most once (visited-id cycle guard) and parsed; cash
        events for ``symbol`` within ``[start, end]`` are kept. Every event carries
        ``ex_date_unavailable``; the result always carries ``corp_action_source_partial``
        (v1 = the VSDC spine alone, no ex-date leg), additionally
        ``coverage_truncated_at_max_fetch`` when the crawl stopped at ``max_fetch`` with the
        frontier not exhausted, ``corp_action_fetch_incomplete`` when ≥1 page failed to fetch or
        parse, and ``corp_action_seed_not_found`` when no-seed auto-discovery found no page for
        the ticker (the empty result is not a confirmed never-paid). ``max_fetch`` must be a
        positive int (a non-positive budget would silently return an empty history →
        ``InvalidData``).
        """
        code = validate_non_empty_string(symbol, "symbol").upper()
        lo, hi = validate_date_range(start, end, allow_none=True, name="dividends")
        if isinstance(max_fetch, bool) or not isinstance(max_fetch, int) or max_fetch < 1:
            # a non-positive budget would silently return an empty history as if complete.
            raise InvalidData(
                f"dividends: max_fetch must be a positive int, got {max_fetch!r}"
            )

        events, truncated, failed_fetches, seed_found = self._crawl(
            code, seed_id=seed_id, lo=lo, hi=hi, max_fetch=max_fetch
        )

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

        warnings: list[str] = [CORP_ACTION_SOURCE_PARTIAL]
        if truncated:
            warnings.append(COVERAGE_TRUNCATED_AT_MAX_FETCH)
        if not seed_found:
            # no-seed auto-discovery exhausted its window without a seed page → the empty
            # history is disclosed as not-authoritative (distinct from a confirmed never-paid).
            warnings.append(CORP_ACTION_SEED_NOT_FOUND)
        if failed_fetches:
            warnings.append(
                f"{CORP_ACTION_FETCH_INCOMPLETE}: {failed_fetches} announcement "
                "page(s) skipped (fetch or parse failed)"
            )

        return DividendHistory(
            code=code,
            source=self.name,
            currency="VND",
            events=tuple(events),
            fetched_at_utc=fetched_at,
            as_of=list_as_of,
            warnings=tuple(warnings),
        )

    def _crawl(
        self,
        code: str,
        *,
        seed_id: Optional[int],
        lo: Optional[date],
        hi: Optional[date],
        max_fetch: int,
    ) -> tuple[list[CashDividendEvent], bool, int, bool]:
        """Bounded multi-hop BFS over the same-org sidebar graph from a seed.

        Fetches each reachable page exactly once — a ``visited`` set is the cycle guard, so
        a sidebar that re-lists the seed or links in a loop still terminates — parses it
        inline, and keeps cash events for ``code`` whose effective date (``record_date``, or
        ``pay_date`` when the record date is unparseable) falls in ``[lo, hi]``. ``max_fetch``
        bounds the number of pages fetched; if the loop stops with the frontier not exhausted
        the returned ``truncated`` flag is ``True``. A per-page failure to FETCH (``SourceError``)
        or to PARSE (``InvalidData`` — empty/whitespace body, unresolvable ticker) is tolerated
        (it does not sink the crawl) but counted, so the caller can disclose the resulting
        coverage gap. ``seed_found`` is ``False`` only when no-seed auto-discovery found no page
        for the ticker. Returns ``(events, truncated, failed, seed_found)``.
        """
        events: list[CashDividendEvent] = []

        seed = seed_id if seed_id is not None else self._find_seed(code, max_fetch=max_fetch)
        if seed is None:
            # no-seed auto-discovery found no announcement page for the ticker in its window:
            # the empty history is NOT a confirmed never-paid (seed_found=False discloses it).
            return events, False, 0, False

        queue: list[int] = [seed]
        enqueued: set[int] = {seed}  # ids ever scheduled (dedup at enqueue time)
        visited: set[int] = set()  # ids already fetched (cycle guard: never re-fetch)
        head = 0
        fetches = 0
        failed = 0

        while head < len(queue) and fetches < max_fetch:
            ann_id = queue[head]
            head += 1
            if ann_id in visited:
                continue
            visited.add(ann_id)
            fetches += 1
            try:
                html = self.fetch_announcement(ann_id)
                ev = self.parse_announcement(html, announcement_id=ann_id)
            except (SourceError, InvalidData):
                # a page that fails to FETCH (SourceError) or to PARSE (InvalidData: empty/
                # whitespace body or a cash-div page with no resolvable ticker) must not sink the
                # whole crawl — counted so the caller discloses the gap (never silently
                # incomplete). The parse call previously sat OUTSIDE this try, so its InvalidData
                # propagated past the guard and one bad sibling page crashed the entire
                # dividends() call. (InvalidData IS a SourceError subclass; SourceError alone would
                # catch it — the tuple is explicit for the reader and robust to hierarchy changes.)
                failed += 1
                continue
            if ev is not None and ev.code == code:
                # window on the record date, falling back to the pay date when the record
                # date is unparseable — so a real, dated-by-payment event is not dropped.
                window_date = ev.record_date or ev.pay_date
                if self._in_window(window_date, lo, hi):
                    events.append(ev)
            for sid in self.discover_same_org_ids(html):
                if sid not in enqueued:
                    enqueued.add(sid)
                    queue.append(sid)

        # frontier not exhausted (stopped at the cap) → coverage is truncated.
        truncated = head < len(queue)
        return events, truncated, failed, True

    def _find_seed(self, code: str, *, max_fetch: int) -> Optional[int]:
        """No seed given: scan a bounded recent-ID window downward from ``latest_id`` for the
        first page whose ticker is ``code``; return its id (the BFS re-fetches from there)."""
        window = min(max_fetch, DEFAULT_MAX_FETCH)
        for offset in range(window):
            ann_id = self.latest_id - offset
            if ann_id <= 0:
                break
            try:
                html = self.fetch_announcement(ann_id)
                ev = self.parse_announcement(html, announcement_id=ann_id)
            except (SourceError, InvalidData):
                # a fetch OR parse failure on a scanned page must not crash discovery — skip it.
                continue
            if ev is not None and ev.code == code:
                return ann_id
        return None

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
