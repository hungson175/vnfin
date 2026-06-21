# #163 design note — dividends / corporate actions (total-return deferred)

**Issue #163.** Architecture per the reviewer's source verdict (2026-06-21) + my verified finfo probe
(`tasks/163-finfo-exdate-probe-evidence.md`).

## Confirmed architecture
- **VSDC = data spine** (reviewer-vetted): record date + pay date + ratio/cash, deep history ~2011,
  keyless, LOW redist risk, CLEAN. **NO ex-date** (it's the depository).
- **VNDirect finfo = ex-date leg** (my probe verified): public host `api-finfo.vndirect.com.vn`,
  `effectiveDate` = ex-date, history floor ~2022. **HELD** for Boss posture nod (source change HNX→finfo)
  + a committed synthetic cassette/fixture.
- **HNX = DROPPED** — genuine TLS-cert failure; shipping `verify=False` in an OSS lib is a security
  non-starter (not a `-k` quirk).

## Proposed domain + models (new `vnfin.corp_actions` — no existing dividend domain)
- `DividendEvent` (frozen): `code`, `kind` (CASH/STOCK/RIGHTS), `cash_per_share` (VND, opt),
  `ratio_pct` (opt), `ex_date: Optional[date]`, `record_date: Optional[date]`, `pay_date: Optional[date]`,
  `div_year`, `source`, `as_of`, `warnings`. Carry the provider's own date, never fabricate `now()`
  ([[typed-result-carry-provider-as-of]]).
- `DividendHistory` (list wrapper): `code`, `source`, `currency="VND"`, `events`, `fetched_at_utc`,
  `warnings`. List-level staleness mirrors the funds pattern.

## API surface (proposed)
- `vnfin.corp_actions.dividends(symbol, start=None, end=None) -> DividendHistory`.
- `vnfin.diagnostics.explain_corp_actions_coverage()` (offline): spine vs ex-date-leg coverage, the
  ~2022 ex-date floor, the held finfo leg.
- **Total-return** (price-adjusted series) is mentioned in #163 → DEFER to v2 (derived calc on top of
  dividends + prices; out of v1 scope). Flag for reviewer.

## Source composition / normalization (the hard part)
- VSDC supplies record/pay/ratio/cash + deep history; finfo enriches `ex_date`.
- **Join key VSDC↔finfo:** finfo `effectiveDate` = VSDC `record_date` − 1 business day (proven on GMD).
  Candidate join: `(code, div_year, ratio/cash)` with a date-proximity tiebreak, OR
  `(code, record_date ≈ effectiveDate+1bd)`. **Reviewer design call.**
- **Pre-2022 (below finfo floor) or unmatched** → `ex_date=None` + `ex_date_unavailable` warning;
  never fabricate.
- **Dedupe finfo VN/EN locale rows** by `(code, type, div_year, effectiveDate, ratio)`.

## Warning tokens (#180/#188 lockstep, in-change)
- `ex_date_unavailable` (pre-floor/unmatched). Possibly `corp_action_source_partial` if the finfo leg is
  down. Each new token → SKILL.md table + `_WARNING_TOKENS_180` + emitted literal (#188). Baseline 37
  (post-#175) → +N. Gate on the sweep, not the count.

## finfo-leg GATING (HARD)
The ex-date leg ships ONLY after (1) Boss's posture nod on HNX→finfo, AND (2) a committed synthetic
fixture mirroring the verified finfo field map + ~2022 floor (real recording gitignored — see the
cassette reconciliation in the evidence note). **VSDC spine + its normalization tests may build first;**
ex-date enrichment lands behind the gate.

## TDD (fail-first, synthetic fixtures only)
- VSDC parse (synthetic fixture in the vetted format), record/pay/ratio extraction, deep-history range.
- finfo parse (synthetic JSON mirroring the verified shape), `effectiveDate`→ex_date, locale dedupe.
- Join/normalization; `ex_date_unavailable` on pre-floor rows; failover when finfo down.

## Open questions for the reviewer (gate)
1. **VSDC field map needed** — your `reviews/…163-source-revet-verdict.md` is in your Codex env, not my
   working tree. Please paste/commit the exact VSDC **endpoint URL + field names + format (HTML/JSON) +
   per-ticker query** you vetted, so I build against the source you approved (not a blind re-probe).
2. New domain `vnfin.corp_actions` vs extend an existing one? (lean new domain.)
3. Join key VSDC↔finfo — `(code, div_year, ratio)` vs `(record_date ≈ ex_date+1bd)`?
4. v1 scope: CASH dividends only first, or CASH+STOCK+RIGHTS together? (lean cash first, then stock/rights.)
5. Total-return — defer to v2 (my lean) or in scope now?
6. Warning tokens `ex_date_unavailable` (+ any others) confirmed for #180/#188?

## ✅ Reviewer confirmations (2026-06-21 11:59) — partial pre-approvals
- **finfo host de-risked:** `api-finfo.vndirect.com.vn` is ALREADY the library's fundamentals host
  (`vnfin/fundamentals/vndirect.py:110` `BASE_URL`, serving `/v4/financial_statements` + `/v4/ratios`).
  So the ex-date leg is a **NEW ENDPOINT (`/v4/events`) on the EXISTING accepted host + posture — not a
  new source/host/risk.** Boss nod is **low-bar** (reviewer surfacing it; it does NOT block starting).
- **`effectiveDate`=ex-date triangulated** (not asserted) — accepted.
- **Cassette reconciliation APPROVED exactly as proposed:** commit a SYNTHETIC fixture mirroring the
  verified shape (real keys + ~2022 floor, synth values) for the offline contract test; gitignore any
  raw recording for opt-in replay.
- **Must-holds (locked):** `ex_date_unavailable` token is **never-silent** on pre-2022 rows — never
  fabricate or silently derive; VN/EN dedupe by `(code, type, divYear, effectiveDate, ratio)`.
- **Reviewer instruction:** build the VSDC spine NOW; finfo ex-date leg gates on Boss-nod + cassette.
- **STILL OPEN (the one true blocker for the spine):** Q1 — the exact VSDC endpoint URL + field names +
  format from the reviewer's verdict report (not in my working tree).
