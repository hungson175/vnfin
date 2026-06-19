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

- **#123–#126 failover returned-object guard cluster** — design APPROVE_WITH_NOTES
  (review-202606191252-consolidated). Order: #125 → #123/#124 → #126 (engine-level provenance
  guard + result-source extractor for fundamentals tuple; reject not restamp; gold datetime keys
  rejected).
  - **#125** container type-check — DONE: pushed `8226ab5`, closed. APPROVE (review-202606191256
    + full-gate 202606191258).
  - **#123** macro point-key type — committed `ec7586c` (NOT pushed). Awaiting review.
  - **#124** price/crypto/gold bar-key type — committed `45ed0a8` (NOT pushed). Awaiting review
    (requested together with #123).
  - **#126** provenance mismatch — LAST. Held until #123/#124 land (engine-level change, avoid
    deep stack). Plan: engine `provenance_of` guard + result-source extractor (fundamentals
    returns a tuple), reject mismatch (not restamp).

## Review blockers (reviewer BLOCK/P1 waiting for fix)

- _(none)_

## Poller triage (newly triaged)

- **#127** — labelled `bug`/queued by reviewer poller 12:50 (last_seen 2026-06-19T05:52:49Z).
  Not yet scoped. Triage + TDD after the #123–#126 cluster lands. `./bin/gh-maintainer issue view 127`.

## Next (the only remaining open bugs — all 12 are in the Now gap-fix queue above)

_All other backlog items verified-fixed and closed during the 2026-06-19 sweep (43→12 open)._

## Done today (trim periodically)

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
