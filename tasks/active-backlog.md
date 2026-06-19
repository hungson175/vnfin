# vnfin-oss — Active Backlog

Operating discipline (Boss 2026-06-19): git history is the progress tracker (commit often);
every reviewer/poller task lands here FIRST, then is processed and removed/marked done with a
commit/issue ref. See `/tmp/vnfin-operating-protocol-202606190959.md`.

Goal (Boss 2026-06-19): work closely with vnfin-oss-reviewer to fix **ALL** GitHub issues/bugs.

Flow per item: design → discuss+converge with reviewer → TDD red-first → green (full suite +
public-API + docs-contract + cov ≥85%) → commit → reviewer code review → push to master →
close issue → advance watermark → mark Done here.

_Last synced: 2026-06-19 ~10:12 +07_

---

## Now (WIP — max 1–2)

- **Returned-metadata mini-batch #69/#131/#132/#133** — design APPROVE_WITH_NOTES
  (review-202606191405). ALL IMPLEMENTED + committed (NOT pushed), suite 1930 green, gates pass,
  no public-API change:
  - **#69** `33007c6` — crypto quote-metadata consistency (USD-equiv quote_asset, price_unit==
    "{quote} per {base}", volume_unit==base, provider_symbol non-empty canonical). Also fixed the
    inconsistent failover fixture default price_unit.
  - **#131+#132** `4548dcc` — macro frequency (Frequency enum + date/freq consistency) and
    projection_from_year (None or int year within span).
  - **#133** `1e5bf85` — price exchange/provider_symbol non-empty canonical str.
  **Awaiting ONE combined reviewer review (f795bd1..HEAD) → push → close all 4.**

- **Failover metadata/inner-row boundary batch: #125-reopen + #127 + #128 + #129 + #130** —
  design APPROVED (review-202606191336 #125r/#129; #127/#128 confirmed 13:38; #130 folded in).
  ALL IMPLEMENTED + committed (NOT pushed), full suite 1866 green, gates pass, no public-API change:
  - **#125-inner** `7199a4f` — per-domain row/item object type checks before deref.
  - **#129** `ae71706` — fundamentals `fiscal_date` must be plain date.
  - **#127** `9e3e61f` — `fetched_at_utc` tz-aware UTC when present (shared `_fetched_at_utc_reason`).
  - **#128** `1898a51` — `warnings` must be `tuple[str,...]` (shared `_warnings_reason`).
  - **#130** `046f1ba` — fundamentals report `is_bank`/`model_type`/`provider_symbol` metadata.
  **Awaiting ONE combined reviewer code review (f6b96da..HEAD) → push → close all 5.**

## Review blockers (reviewer BLOCK/P1 waiting for fix)

- _(none)_

## Poller triage (newly triaged)

- **Returned-metadata mini-batch: #69 / #131 / #132 / #133** (after #130 follow-up lands):
  - **#69** (REOPENED) — crypto quote-metadata residual.
  - **#131** — macro `projection_from_year`: None or real non-bool int year; sane vs first obs.
  - **#132** — macro `frequency`: must be a `Frequency` enum (reject str/bool/int/container/None);
    point dates consistent with frequency.
  - **#133** — price returned security metadata: `exchange` present⇒non-empty (accepted set),
    `provider_symbol` present⇒non-empty str not contradicting requested symbol.
  Scope each via `./bin/gh-maintainer issue view <n>`; combined design then TDD.

## Next (the only remaining open bugs — all 12 are in the Now gap-fix queue above)

_All other backlog items verified-fixed and closed during the 2026-06-19 sweep (43→12 open)._

## Done today (trim periodically)

- **Failover metadata/inner-row batch — COMPLETE, pushed + closed (`f6b96da..f795bd1`).**
  - **#125-reopen** `7199a4f` — inner row/item object type checks. APPROVE.
  - **#129** `ae71706` — fundamentals fiscal_date plain-date. APPROVE.
  - **#127** `9e3e61f` — fetched_at_utc tz-aware UTC (shared helper). APPROVE_WITH_NOTES.
  - **#128** `1898a51` — warnings tuple[str,...] (shared helper). APPROVE_WITH_NOTES.
  - **#130** `046f1ba`+`65bb2c4` — fundamentals report metadata (is_bank/model_type/
    provider_symbol); model_type allow-listed to {1,2,3,101,102,103} after reviewer follow-up
    BLOCK (reopened then re-closed). APPROVE. Suite 1879 green.
- **#123–#126 failover returned-object guard cluster — COMPLETE, all pushed + closed.**
  - **#125** outer container type-check — `8226ab5`. APPROVE.
  - **#123** macro point-key plain-date — `ec7586c`. APPROVE.
  - **#124** price/crypto tz-aware + gold plain-date bar keys — `45ed0a8`. APPROVE.
  - **#126** failover provenance guard (all 6 domains incl. FX; engine `provenance_of` +
    total fundamentals extractor w/ tuple sentinel) — `21c225f..f6b96da`. APPROVE after
    B1(FX)/B2(strict)/B3(unhashable)/B4(marker-collision) hardening. Suite 1750 green.
- **#122** fundamentals failover malformed-LineItem guard — pushed `d7a2190..c2a6be0`, closed.
  Strict `_validate_line_item` (canonical item_code, str name, finite non-bool value, dup-code
  reject) + B1 padded-code fix. Reviewer APPROVE (review-202606191245). Suite 1663 green.
- Pushed reviewed seven-commit stack `6f4a8da..a8479fc` to origin/master.
- Closed **#112** (29e942a), **#94** (ff159f5), **#14** (a8479fc) as fixed.
- Closed external duplicate **PR #115** as superseded (code not run).
- **#87** closed by reviewer as fixed (4db0c74 / a8479fc).
- **#107 / #110** closed by reviewer/poller #59 as fixed (watermark 2026-06-19T03:01:44Z).
- **#113 / #114** strict timestamp guards — pushed `a8479fc..9de091b`, closed (c76756a, 797ccad).
  Reviewer APPROVE_WITH_NOTES (review-202606191010). Watermark 2026-06-19T03:11:37Z.
- **#116** BTMC malformed weight tokens — pushed `9de091b..d384006`, closed. Reviewer
  APPROVE_WITH_NOTES (review-202606191021). Watermark 2026-06-19T03:21:45Z.
  Future-hardening note (non-blocking): `_QTY` left boundary allows a digit glued to a letter
  (`ABC5 LUONG`); out of #116 scope, revisit if such names ever appear.
- **#117** BTMC same-ts dedup — pushed `d384006..22bb20c`, closed (5050468, 2366ff6). Reviewer
  APPROVE (re-review inline after BLOCK on missing regression tests). Watermark 03:33:22Z.
- **#118** BTMC `@row` index validation — pushed `22bb20c..d97ef89`, closed (d97ef89). Reviewer
  APPROVE_WITH_NOTES (review-202606191038). Watermark 03:39:55Z. BTMC cluster complete.
- **#72, #83, #69, #73, #74, #85, #86** failover-guard cluster — VERIFIED already fixed + tested
  on master (guard + passing regression tests cited per issue); closed, no code change needed.
  Watermark 03:43:17Z. Reporters had filed against older commits.
- **#70, #71, #76, #77, #78, #79, #82** failover remaining — VERIFIED already fixed + tested;
  closed with cited tests. Watermark 03:47:08Z.
- **#15, #22, #32, #35, #37** + **#41, #67, #75, #80, #81, #93, #97, #104, #109** source-adapter
  cluster — VERIFIED already fixed + tested; closed with cited tests. Open 43→12.
- **#111** VNDirect type-before-truthiness — pushed `481ccfd`, closed. APPROVE_WITH_NOTES.
- **#119** CafeF Success bool — pushed `0b524a2`, closed. APPROVE.
- **#121** VNDirect strict modelType — pushed `4e0c05f`+`d5b9e03`, closed. APPROVE (after whitespace BLOCK fix).
- **#120** UDF fractional volume — pushed `ee710ac`, closed. APPROVE_WITH_NOTES. Open 12→8.
- **#68** fmarket case-insensitive code dedup — pushed `ab706b2`, closed. APPROVE.
- **#26, #49, #65** test-only gaps (guards already present) — regression tests added in `f2fb711`,
  pushed, closed. APPROVE. Open 8→4.
- **#28** Vietcombank get_rates ISO-4217 code skip — `defae64`, closed. APPROVE.
- **#108** WB/IMF canonical year keys — `45601f1`, closed. APPROVE.
- **#21** WB/DBnomics response-identity (incl. malformed/blank BLOCK fix) — `e053153`+`e72a10a`,
  closed. APPROVE (after BLOCK fix).
- **#66** time-series duplicate observation keys (UDF/Stooq per-response; Binance/Coinbase
  per-page, pagination dedupe preserved) — `5ee2f71`, closed. APPROVE/GO.

## 🎉 Milestone: 43-issue backlog fully cleared (2026-06-19)

Open count 43 → 0 in one session. ~21 were verified already-fixed (closed with cited passing
tests, reviewer-validated); the rest were real TDD fixes (BTMC cluster #113/#114/#116/#117/#118;
then #111/#119/#121/#120/#68/#28/#108/#21/#66), each reviewer-approved and pushed to master.
