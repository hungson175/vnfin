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

- **Failover-guard cluster verification** (#69,#72,#73,#74,#83,#85,#86). FINDING (Explore map
  2026-06-19): these guards appear ALREADY PRESENT in code (added in earlier batch commits
  ab727ef/d78b245-era) but have NO dedicated regression tests and the issues are still open.
  Approach: write a regression test encoding each reporter's reproduction (TDD-characterization).
  Test PASSES → guard works → close issue with the now-committed test. Test FAILS → real gap →
  fix it. Same likely applies to the source-adapter cluster — verify before re-implementing.
  Starting with FX group (#72 bid/ask, #83 as_of_utc) in `vnfin/fx/client.py`.

## Review blockers (reviewer BLOCK/P1 waiting for fix)

- _(none)_

## Poller triage (newly triaged)

- _(none pending)_

## Next (queued open bugs — fix ALL; group by domain to batch reviewer-approved stacks)

Failover identity/units/bounds/ordering guards:
- #69 crypto failover currency vs value_unit mismatch
- #70 fundamental failover currency-unit disagreement (VND chain)
- #71 macro client relabels conflicting value_unit/currency
- #72 FX failover invalid bid/ask metadata
- #73 price failover unit/adjustment metadata contradicts chain
- #74 world-gold failover unit metadata contradicts USD/oz chain
- #76 world-gold failover history date bounds
- #77 crypto failover interval/date bounds
- #78 macro failover country/indicator identity contradicts request
- #79 fundamental failover malformed requests / wrong-identity reports
- #82 price/crypto/gold failover returned identity contradicts request
- #83 FX failover invalid as_of_utc timestamps
- #85 price/crypto/gold failover unsorted histories
- #86 failover accepts economically impossible observations

Source-adapter input/identity/units hardening:
- #15 domestic gold negative buy/sell spreads
- #21 adapters don't validate response identity before stamping identifiers
- #22 response cache key collisions when secret params redacted
- #26 fundamental statements accept duplicate line-item codes
- #28 FX get_rates malformed currency codes from provider rows
- #32 macro country input not validated as ISO3
- #35 currency-api gold history document date identity
- #37 HttpDataSource invalid retry/cache options leak TypeError
- #41 Fmarket missing application-status envelope
- #49 FRED forwards invalid date bounds to provider
- #65 direct price source classes leak raw errors for malformed caller inputs
- #66 time-series sources accept duplicate observation keys
- #67 PNJ duplicate/non-string product keys
- #68 Fmarket duplicate fund codes / provider IDs
- #75 index constituents malformed selectors leak raw errors
- #80 gold factory selectors leak raw AttributeError for non-string input
- #81 fundamentals return reports with no line items
- #93 OpenErApi FX inconsistent USD self-rate anchor
- #97 Fmarket list_funds stringifies malformed fund metadata/asset types
- #104 DBnomics period dates contradict result frequency
- #108 World Bank/IMF non-canonical provider year keys
- #109 Fmarket containers misclassify malformed falsy payloads as empty
- #111 VNDirect misclassifies malformed falsy data containers as empty

## Done today (trim periodically)

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
