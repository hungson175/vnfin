# #163 — VSDC CASH-dividend spine: BUILD SPEC (self-contained)

**For:** a fresh general-purpose build sub-agent. Build TDD-first (Red → Green → Refactor).
**Scope:** v1 = a new `vnfin.corp_actions` domain serving **CASH dividends** scraped from the VSDC
(Vietnam Securities Depository) public announcement pages. **STOCK/RIGHTS/BONUS = v2** (out of scope).
**ex-date enrichment (VNDirect finfo leg) = HELD** (not in this build) → `ex_date` is **always `None`**.

Design gate is CLEARED by `vnfin-oss-reviewer` (2026-06-21 12:07 + 12:09). Do not re-open design.
Read this spec + the template files it cites. **Do not search/read/cite VNStock** (HARD blacklist).

---

## 0. Hard constraints (read first — violating any of these fails review)

1. **TDD:** write the failing test FIRST, then the minimum code to pass. No code without a test.
2. **No network in unit tests.** Inject `http_get` (see transport pattern §5). All HTTP is stubbed
   to return committed fixture HTML.
3. **Synthetic fixtures only.** The 6 fixtures in `tests/fixtures/corp_actions/*.html` already exist
   (real DOM structure, fabricated values; incl. `vsdc_sidebar_same_org.html`). Use them. The crawl
   cycle/truncation tests (§9.13–14) use a STUBBED `http_get` page-graph, not new static fixtures.
   Do NOT add real issuer rows anywhere.
4. **Warning tokens must be EXACT STATIC STRING LITERALS** (no f-string interpolation of the token
   stem) so the #188 AST scanner discovers them. e.g. `warnings.append("ex_date_unavailable")` — a
   trailing `: detail` is fine (`f"ex_date_unavailable: {why}"` is OK because the stem is literal at
   the start), but the token stem itself must be a literal substring.
5. **Do NOT run `scripts/dump_api_surface.py`** and do NOT edit `tests/snapshots/public_api_v0_2_0.json`.
   The new domain is *additive* → `test_live_surface_introduces_no_breaking_changes` stays green by
   design (additive diffs are printed, not failed). Confirm that test is green; never regen the baseline.
6. **No `git add -A`** (private gitignored tooling exists). The orchestrator handles git; you return a
   diff/summary. Do not push, do not close issues, do not message the reviewer.
7. Every event/result carries the provider's own date — never fabricate `now()` into a data field
   (a `fetched_at_utc` stamped at fetch time is fine and expected; a *record/pay/as_of* date must come
   from the page).

---

## 1. Source: VSDC announcement pages (HTML scrape)

- **Endpoint:** `GET https://vsd.vn/vi/ad/{id}` — `{id}` is a **sequential integer** (~197000 in 2025),
  keyless, server-rendered HTML (no JSON API). `/en/ad/{id}` is the English mirror; build against `/vi/`.
- History reaches ~2011. VSDC is the depository: it publishes **record date + pay date + ratio/cash**
  but **NO ex-date**.
- **Discovery (how `dividends(symbol)` finds a ticker's announcement IDs)** — two real, observed signals:
  1. **Same-org sidebar:** every page has a "Tin cùng tổ chức" block with `<a href="/vi/ad/{id}">`
     links to that company's *other* announcements (deep history). Parse these for crawl expansion.
  2. **Recent-ID-window scan:** scan a bounded window of recent IDs (downward from a rolling watermark)
     and filter by ticker to find a seed when none is supplied.
  Combined strategy: get a seed for `symbol` (caller-supplied `seed_id`, or recent-window scan), then
  crawl the seed's same-org sidebar to enumerate the company's announcement IDs, fetch+parse each.
- **Crawl safety (reviewer MUST-ADDS 2026-06-21 12:30 — completeness guards, do NOT skip):**
  1. **Visited-ID dedup + cycle guard:** the sidebar can re-list the seed or form link cycles. Track a
     `visited: set[int]`; never re-fetch a visited id; bound the crawl (frontier + a depth/breadth cap)
     so a cyclic page graph TERMINATES. A re-listed/looping id is skipped, not re-walked.
  2. **Never-silent cap disclosure:** if the crawl stops at `max_fetch` (or the depth bound) while
     unvisited frontier IDs remain (history NOT exhausted), the result MUST carry the never-silent token
     `coverage_truncated_at_max_fetch` (4th token, §6). NEVER return a truncated dividend history as if
     complete — a silently-capped history is a survivorship/completeness bug (a 5y backtest on it is
     wrong; same class as the #175 never-silent guards).
- **Risk:** scrape is materially more fragile than the lib's JSON sources. Isolate ALL HTML parsing
  behind the tight contract in §3, pin it with the fixtures, and emit the never-silent
  `vsdc_parse_degraded` token on any cash-dividend page whose amount cannot be extracted — a layout
  drift must never silently corrupt or empty a result.

---

## 2. Files

**Create** (new domain, mirror the `vnfin/gold/` layout):
- `vnfin/corp_actions/__init__.py` — public facade + `__all__` + `dividends(...)` factory.
- `vnfin/corp_actions/models.py` — `CashDividendEvent`, `DividendHistory` (frozen dataclasses).
- `vnfin/corp_actions/base.py` — `CorpActionSource` port (subclass `HttpDataSource`) + `VN_TZ`.
- `vnfin/corp_actions/vsdc.py` — `VsdcCashDividendSource` adapter (fetch + parse + discover).
- `tests/test_corp_actions_vsdc.py` — the TDD suite (parse contract + models + discovery + tokens).

**Edit:**
- `vnfin/__init__.py` — add `corp_actions` to the top-level `from . import (...)` and to `__all__`
  + a one-line facade comment in the module docstring table.
- `vnfin/diagnostics.py` — add `explain_corp_actions_coverage()` + a `_CORP_ACTIONS_CAPS` capability
  tuple; include it in `source_capabilities()`; add the name to `__all__`.
- `skills/vnfin/SKILL.md` — add 4 rows to the `## Warning tokens` table (the public table the #180
  guard reads).
- `tests/test_docs_contract.py` — add the 4 tokens to the `_WARNING_TOKENS_180` tuple (~line 551).
- `CHANGELOG` / `docs/api.md` — add the new public domain (public-API change ⇒ docs in same change).
  Find the changelog file (grep `mixed_source` / `deferred to v2` to locate it) and add a `#163` entry.

**Already committed (use, don't recreate):** `tests/fixtures/corp_actions/`:
- `vsdc_cash_dividend_clean.html` — clean cash div, pay label `Ngày thanh toán:` →
  TST / HOSE / record 2024-03-15 / pay 2024-04-10 / 12% / 1200đ / div_year 2024.
- `vsdc_cash_dividend_paylabel_thoigian.html` — pay label `Thời gian thực hiện:` →
  TST / HOSE / record 2022-06-20 / pay 2022-07-18 / 14% / 1400đ / div_year 2022.
- `vsdc_bundled_voting_plus_cash.html` — bundled voting + cash; TWO `Tỷ lệ thực hiện:` lines, must
  pick the cash one via the cash parenthetical → BAR / HNX / record 2025-06-25 / pay 2025-07-07 /
  5% / 500đ / div_year 2025.
- `vsdc_non_dividend_warrant.html` — covered-warrant reg with the trap word "Bằng tiền" (settlement
  method) → parser yields **None** (not a cash dividend), and **must NOT** emit `vsdc_parse_degraded`.
- `vsdc_cash_dividend_degraded.html` — cash-dividend title + record date but unparseable ratio
  (`(đang cập nhật)`, no cash parenthetical) → returns an event with `ratio_pct=None`,
  `cash_per_share=None`, and `warnings` containing `vsdc_parse_degraded`.

---

## 3. The VSDC parse contract (probed live 2026-06-21 — pin EXACTLY)

Parse the page **body**; locate fields by CSS class/label, **never by element position or column width**.

- **Title / ticker:** `<h3 class="title-category">{TICKER}: {title}</h3>`. Ticker = text before the
  first `:`. A **cash dividend** is identified by the title (or the `Lý do mục đích:` reason) containing
  **"cổ tức"** AND **"bằng tiền"** (accent-insensitive match recommended — see `_strip_accents` in
  `vnfin/gold/vn.py:59`). Title verb varies: "Chi trả cổ tức …", "Trả cổ tức …", "Chi cổ tức …".
- **as_of timestamp:** `<div class="time-newstcph">Cập nhật ngày DD/MM/YYYY - HH:MM:SS</div>`. Parse to
  a `datetime` (VN_TZ). This is the provider's own publish time → use as the event/result `as_of`.
- **Structured fields:** rows of the shape
  `<div class="row"><div class="... item-info">LABEL:</div><div class="... item-info item-info-main">VALUE</div></div>`.
  **Pair the value to the label by the `item-info` / `item-info-main` classes — the `col-md-*` widths
  VARY across pages (3/9, 4/8, 7/5) and MUST NOT be used.** Labels you need:
  - `Mã chứng khoán:` → ticker (cross-check vs the title ticker).
  - `Nơi giao dịch:` → exchange (e.g. HOSE / HNX / UPCOM). Optional.
  - `Ngày đăng ký cuối cùng:` → **record_date** (DD/MM/YYYY) — reliable, structured.
  - `Lý do mục đích:` → reason (used for cash-dividend detection as a fallback to the title).
- **Ratio + pay date** are in a free-text justify block:
  `<p><div style="text-align: justify;"> … <br /> … </div></p>` with `<br />` line separators.
  - **Ratio line / cash anchor:** the line containing the parenthetical **`(… được nhận {N} đồng)`**
    uniquely identifies the cash-dividend ratio (and distinguishes it from a voting ratio line like
    `01 cổ phiếu – 01 quyền biểu quyết` on bundled pages). Extract:
    - `cash_per_share` = `{N}` from `được nhận {N} đồng` — Vietnamese thousands sep is `.`
      so `"1.400"` → `1400.0`, `"500"` → `500.0`.
    - `ratio_pct` = the percent before `%/cổ phiếu` / `% /cổ phiếu`, e.g. `14%` → `14.0`, `5%` → `5.0`.
  - **Pay date line:** label is **either** `Ngày thanh toán:` **or** `Thời gian thực hiện:`, followed by
    a `DD/MM/YYYY`. Accept both labels. On a `Thời gian thực hiện:` line whose value is not a date
    (e.g. "Dự kiến trong Quý III"), treat pay_date as absent (None) — do not crash.
- **div_year:** parse the year from "… năm YYYY …" in the title/reason; else `None`.
- **Number/date formats:** dates `DD/MM/YYYY`; strip `.` thousands separators before `int/float`.

**Degradation rule (never silent):** if the page IS a cash dividend (title/reason match) and has a
record date, but the cash parenthetical / ratio cannot be parsed → still return a `CashDividendEvent`
(record_date set, `cash_per_share=None`, `ratio_pct=None`) with `vsdc_parse_degraded` in its warnings.
If the page is not a cash dividend at all → return None (no event, no degraded token).

---

## 4. Models (`vnfin/corp_actions/models.py`)

Mirror `vnfin/gold/models.py` style: `@dataclass(frozen=True)`, explicit unit/currency/source fields,
`__post_init__` boundary validation raising `InvalidData` (import from `..exceptions`).

```python
@dataclass(frozen=True)
class CashDividendEvent:
    code: str                          # ticker, upper-cased, non-empty
    kind: str                          # always "CASH" in v1
    cash_per_share: Optional[float]    # VND per share; None if degraded
    ratio_pct: Optional[float]         # percent of par; None if degraded
    ex_date: Optional[date]            # ALWAYS None in v1 (finfo leg held)
    record_date: Optional[date]
    pay_date: Optional[date]
    div_year: Optional[int]
    source: str                        # "vsdc"
    as_of: Optional[datetime]          # provider publish time (time-newstcph)
    exchange: Optional[str] = None
    announcement_id: Optional[int] = None
    warnings: tuple[str, ...] = ()
```

`__post_init__` validation (raise `InvalidData`): `code` non-empty str; `kind == "CASH"`;
`cash_per_share`/`ratio_pct` when present must be finite and `> 0` (reject bool, NaN, ≤0 — mirror the
GoldQuote numeric guard); dates must be `datetime.date` when present. **`ex_date_unavailable` must be
in `warnings` whenever `ex_date is None`** (i.e. always in v1) — enforce/append at construction in the
adapter, and assert it in tests for every event.

```python
@dataclass(frozen=True)
class DividendHistory:
    code: str
    source: str                        # "vsdc"
    currency: str                      # "VND"
    events: tuple[CashDividendEvent, ...]
    fetched_at_utc: Optional[datetime] = None
    as_of: Optional[datetime] = None   # max event as_of, provider-derived
    warnings: tuple[str, ...] = ()     # list-level; ALWAYS contains corp_action_source_partial in v1
```

Events should be ordered (e.g. by record_date, then announcement_id) deterministically. Consider a
`to_df()`/`__iter__` only if a sibling list result has one and a test needs it — otherwise keep minimal.

---

## 5. Adapter (`vnfin/corp_actions/vsdc.py`) + port (`base.py`)

- `base.py`: `from ..transport import HttpDataSource`; `VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")`; define a
  small `CorpActionSource(HttpDataSource, ABC)` port with `name` and an abstract
  `dividends(symbol, *, start=None, end=None) -> DividendHistory`.
- `VsdcCashDividendSource(CorpActionSource)`:
  - `name = "vsdc"`, `BASE_URL = "https://vsd.vn/vi/ad/"`.
  - Constructor passes through to `HttpDataSource.__init__` (injectable `http_get`, `timeout`). Optional
    `latest_id` watermark (default a documented module constant, e.g. `LATEST_ID_HINT = 197000`,
    overridable) used only by the recent-window scan default discovery.
  - `fetch_announcement(announcement_id) -> str`: `self._request_text(self.BASE_URL + str(id))` — this
    wraps transport failures as `SourceUnavailable` automatically (see `vnfin/transport.py`).
  - `parse_announcement(html, *, announcement_id=None) -> Optional[CashDividendEvent]`: the pure parser
    implementing §3. **Pure function of the HTML string** — this is the fixture-tested core. Use
    `html.parser` via stdlib (`html.parser.HTMLParser`) or regex shape-guards consistent with the repo
    (the gold scrape uses `re`; do whichever is cleaner and well-tested — no new heavy deps; BeautifulSoup
    is acceptable ONLY if already a declared dependency, otherwise stdlib/regex).
  - `discover_same_org_ids(html) -> tuple[int, ...]`: extract `/vi/ad/{id}` links from the same-org
    sidebar block.
  - `dividends(symbol, *, start=None, end=None, seed_id=None, max_fetch=300) -> DividendHistory`:
    discovery per §1 (seed → sidebar crawl; or recent-window scan when no seed), fetch+parse each, keep
    cash events for `symbol` within `[start, end]`. Always: per-event `ex_date_unavailable`; list-level
    `corp_action_source_partial` (v1 = VSDC-spine-only, ex-date leg not active). Wrap malformed HTML the
    parser cannot make sense of as `InvalidData` only when it is structurally broken — a *recognized but
    unparseable cash dividend* is the `vsdc_parse_degraded` path (an event), NOT an exception.
  - **Crawl invariants (§1 must-adds):** maintain `visited: set[int]`, never re-fetch a visited id, bound
    the frontier+depth so a cyclic sidebar graph terminates; when the crawl is capped by `max_fetch`/depth
    with unvisited frontier IDs still pending, append `coverage_truncated_at_max_fetch` to
    `history.warnings` (never return a truncated history as complete).
  - `start`/`end` filtering uses `validate_date_range` from `vnfin/validation.py` if a sibling uses it.

Transport: rely on `HttpDataSource._request_text` (forces IPv4, browser UA, 25s, wraps errors). Do not
re-implement transport.

---

## 6. Warning tokens — #180/#188 lockstep (land all 4 together)

The 4 tokens (all EXACT static literals):
| Token | Level | When |
|---|---|---|
| `ex_date_unavailable` | per-event | Every event in v1 (`ex_date is None`; finfo leg held). Never fabricate/derive an ex-date. |
| `corp_action_source_partial` | per-result (DividendHistory) | Always present in v1 — result is from the VSDC depository spine ALONE; ex-date enrichment leg is not active. (In v2 this fires when the finfo leg is down.) |
| `vsdc_parse_degraded` | per-event | A page IS a cash dividend (title/reason) with a record date but the ratio/cash parenthetical is unparseable → amount fields None, never silently dropped. |
| `coverage_truncated_at_max_fetch` | per-result (DividendHistory) | Discovery stopped at `max_fetch`/depth bound while unvisited frontier IDs remained → history is NOT exhaustive; never return a truncated history as complete (reviewer must-add 12:30). |

For EACH token, in the SAME change:
1. **Emit it as a literal** in `vnfin/corp_actions/` (so #188 AST discovery sees it).
2. **Add a row** to the `## Warning tokens` table in `skills/vnfin/SKILL.md` (column format:
   `| token | Result/accessor | Meaning | #163 |`).
3. **Add it** to `_WARNING_TOKENS_180` in `tests/test_docs_contract.py` (~line 551, with a `# #163`
   comment).

Then run the doc-contract suite. **Gate on the SWEEP being green** (the bidirectional doc↔code +
#188 forward-discovery bijection: `code-emits ⊆ tuple ⊆ {SKILL table ∧ code-literal}`), **NOT on any
magic count.** (For reference only, the reviewer states the current baseline is 37 documented tokens;
#163 takes it 37→41 — but assert the sweep, never the number.) Do not touch unrelated existing tokens.

---

## 7. Diagnostic (`vnfin/diagnostics.py`)

Add `explain_corp_actions_coverage() -> RequestDiagnostic` mirroring `explain_fixed_income_coverage()`
(offline, no network). It should disclose: the VSDC spine (record/pay/ratio/cash, history ~2011, cash
only in v1); that **ex-date is unavailable in v1** (finfo enrichment leg held; pre-2022 floor noted for
v2); that STOCK/RIGHTS/BONUS are v2; and the scrape-discovery approach + its bounds. Put coverage facts
in `notes` / `suggested_actions` and an appropriate `status` (e.g. `"ex_date_unavailable"` or
`"partial_coverage"`) — **do not** put tokens meant for `result.warnings` here (those live on results).
Add a `_CORP_ACTIONS_CAPS` `SourceCapability` tuple, include it in `source_capabilities()`, and add
`"explain_corp_actions_coverage"` to `diagnostics.__all__`.

---

## 8. Public API wiring

- `vnfin/corp_actions/__init__.py`: export `CashDividendEvent`, `DividendHistory`, `CorpActionSource`,
  `VsdcCashDividendSource`, and a `dividends(symbol, *, start=None, end=None, http_get=None,
  timeout=25.0, **kw) -> DividendHistory` factory (builds `VsdcCashDividendSource` and calls it). Mirror
  the docstring/`__all__` discipline of `vnfin/gold/__init__.py`. Document clearly: **v1 = CASH only,
  ex-date unavailable, scrape source.**
- `vnfin/__init__.py`: add `corp_actions` to the `from . import (...)` block and `__all__`; add a
  one-line row to the facade table in the module docstring (e.g.
  `vnfin.corp_actions  # cash dividends (VND) -> .dividends()`).

---

## 9. TDD plan (write tests FIRST; map each to a fixture/invariant)

`tests/test_corp_actions_vsdc.py` — load fixtures via `Path(__file__).parent / "fixtures/corp_actions"`.

Parser (pure, no network):
1. clean fixture → event with exactly TST/HOSE/2024-03-15/2024-04-10/12.0/1200.0/div_year 2024;
   `ex_date is None`; `"ex_date_unavailable"` in `event.warnings`; `"vsdc_parse_degraded"` NOT present.
2. paylabel-thoigian fixture → parses `Thời gian thực hiện:` as pay_date 2022-07-18; 14.0/1400.0.
3. bundled fixture → picks the CASH ratio (5.0/500.0, pay 2025-07-07), ignores the voting ratio; exactly
   one cash event; BAR/HNX.
4. non-dividend-warrant fixture → `parse_announcement(...) is None`; assert `vsdc_parse_degraded` NOT
   emitted (it is correctly "not a dividend", not a parse failure).
5. degraded fixture → returns an event; `cash_per_share is None` and `ratio_pct is None`;
   `"vsdc_parse_degraded"` in warnings; `record_date == 2024-09-10`; still has `ex_date_unavailable`.
6. column-width independence: a regression asserting the parser pairs label→value by class even when
   `col-md-*` widths differ (the fixtures already vary widths; assert at least one non-4/8 case parses).

Models (boundary validation):
7. `CashDividendEvent` rejects `kind != "CASH"`, non-finite/≤0 `cash_per_share`, bool amounts → `InvalidData`.
8. constructing an event with `ex_date=None` and no `ex_date_unavailable` is caught (either the model
   enforces it, or the adapter always appends it — test whichever you implement).

Discovery + adapter (inject `http_get` mapping id→fixture HTML):
9. `discover_same_org_ids(html)` extracts the sidebar IDs from a fixture that has a same-org block.
   (Create a small `vsdc_sidebar_same_org.html` fixture, OR extend the clean fixture with a sidebar
   block — SYNTHETIC, fabricated IDs that map to the other fixtures.)
10. `dividends("TST", ...)` with a stub `http_get` returning the TST fixtures for the relevant IDs →
    `DividendHistory` with the expected TST cash events, `currency == "VND"`,
    `"corp_action_source_partial"` in `history.warnings`, every event has `ex_date_unavailable`.
11. date-range filter: `start`/`end` correctly include/exclude events by record_date.
12. transport failure (stub raises) → surfaces as `SourceUnavailable` (assert the adapter wraps it).
13. **cycle/dedup (reviewer must-add):** stub `http_get` returns a same-org sidebar page-graph that
    re-lists the seed and forms a link cycle (e.g. A's sidebar → B, B's sidebar → A) → `dividends(...)`
    TERMINATES, fetches each id AT MOST ONCE (assert the stub's per-id call count ≤ 1), no infinite loop.
14. **never-silent truncation (reviewer must-add):** frontier larger than `max_fetch` (e.g.
    `max_fetch=2` over 5 discoverable ids) → `"coverage_truncated_at_max_fetch"` IS in
    `history.warnings`; re-run with `max_fetch` large enough to exhaust the frontier → that token is
    ABSENT (the asymmetry proves it is NOT always-on like `corp_action_source_partial`).

Diagnostic:
15. `explain_corp_actions_coverage()` returns a `RequestDiagnostic` (offline), discloses cash-only +
    ex-date-unavailable + v2 scope; `source_capabilities()` includes the corp-actions cap(s).

Lockstep (these existing suites must pass on the merged tree):
16. `tests/test_docs_contract.py` (#180 bidirectional + #188 forward-discovery) green with the 4 new
    tokens added to the tuple + SKILL table + emitted as literals.
17. `tests/test_public_api_surface.py::test_live_surface_introduces_no_breaking_changes` green (the new
    domain is additive — printed, not failed; do not regen the baseline).

Run the FULL suite (`.venv/bin/python -m pytest -q`) and report pass/fail counts + any diffs.

---

## 10. Out of scope (do NOT build)

- VNDirect finfo ex-date leg (held for Boss-nod + cassette). `ex_date` stays `None`.
- STOCK / RIGHTS / BONUS dividends (v2).
- Total-return / price-adjusted series (v2; behind a future `possible_double_count` token).
- Any live/network integration test (opt-in only, skipped in CI; not required here).
- VNStock anything (HARD blacklist).

## 11. Deliverable

Return: a concise summary of files created/edited, the new test names, the full-suite pass count, and
any decisions/assumptions made (especially around discovery defaults — flag these for the reviewer).
Do NOT push, close issues, message the reviewer, or run `dump_api_surface.py`.
