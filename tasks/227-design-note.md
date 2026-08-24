# #227 full-HOSE daily foreign-flow source/design note

**Access date:** 24 August 2026 (UTC+7)
**Packet:** reviewer anchor `29206690269215dba1a35bb13ee7c621055e7fca`
**Published base:** `origin/master` `483ff56522e713ae8495dc515e4e4f5915655bd7`
**Phase:** `SOURCE_DESIGN`
**Disposition:** **`SOURCE-GAP CLOSURE`**
**Chain:** empty; no provider registration, probe, RED test, model, facade, or runtime capability

## Scope boundary

The requested primitive is one exact current-HOSE universe snapshot and daily foreign-investor flow
history for that snapshot. It is not historical HOSE membership, intraday/order-book/tape data,
VN30/VN30F logic, ranking, breadth, portfolio, backtest, basket aggregation, or cross-provider
stitching. The current equity-universe surface is a separate discovery input; it never proves the
flow response's exchange or symbol identity.

The companion research report is
[`docs/research/2026-08-24-full-hose-daily-foreign-flow-source-vetting.md`](../docs/research/2026-08-24-full-hose-daily-foreign-flow-source-vetting.md).
It records only first-party exchange/provider/regulator evidence and no live rows.

## Source decision

The public HOSE foreign-investor statistics UI and daily PDFs establish aggregate/top-five
presentation, not a full-board daily-history operation. HOSE's richer Market Data Feed/Webservice
is account/tariff-oriented, and the reviewed official material does not grant the no-login
automation, caller-return, storage, or redistribution rights required here. No source is
`QUALIFIED` or `QUALIFIED_PARTIAL`.

Missing evidence is not source absence, zero flow, zero traffic, or permission. Candidate dispatch
is zero because this is documentation/search-only research.

| Exact unit | Disposition at this gate |
| --- | --- |
| HOSE `tradingresult/{code}` | Historical `SAMPLED_ONLY`; symbol seen in #201, but session/date, scale, whole-board bounds, rate, revisions, and rights unresolved |
| HOSE `foreign/{code}` | `IDENTITY_GAP`; no response-backed symbol; never a fallback |
| HOSE stocks statistics UI | Aggregate-by-security evidence only; no per-symbol response/legal contract |
| HOSE daily summary PDF | Aggregate/top-five evidence only; no full-board row/history contract |
| HOSE annual report | Aggregate annual/monthly terminology only; no daily per-symbol route |
| HOSE market-data feed page | Product/feed evidence only; no public no-login foreign-flow contract |
| HOSE ECM login route | Account/password boundary; no no-login operation or reuse grant |
| HOSE information-service tariff | Product/fee catalogue only; not automation, caller-return, or redistribution permission |
| SSI FastConnect daily stock price | Foreign fields documented, but access-token flow and no full-HOSE/rights proof block this no-login gate |
| Existing SSI iBoard universe | Current snapshot input only; partial/listing-date warnings and separate rights/source identity remain |
| FiinGroup HOSE Stock V2 | Foreign fields named, but no-login/full-HOSE/legal/revision proof is missing; not qualified |

HNX/UPCoM/SSC material is a wrong-board or aggregate-only scope exclusion, not a candidate source
unit and never a fallback. `NOT_SERVED` is reserved for a future provider response that explicitly
declares unsupported, out-of-bound, or unlisted. The current source-table disposition
`NOT_QUALIFIED` means that authentication, legal, coverage, or runtime gates are unproven; it never
asserts provider absence.

## Qualification contract for a future source

One exact provider-owned flow route/version/operation and one independently qualified universe
route/version/operation must each pass their applicable axes conjunctively; their owners may differ,
but the response-backed identifier binding must be explicit and no cross-owner flow stitch is allowed:

- **Identity:** response-backed `exchange=HOSE`, canonical symbol, plain Vietnam trading-session
  date, and immutable current-snapshot provenance; no request-path identity or cross-owner join.
- **Fields:** foreign buy/sell volume and value, exact VND scale/precision, provider-defined net,
  main-board versus put-through scope, null versus zero, publication lag, and correction/revision.
- **Coverage:** provider-declared history bounds, eligible sessions, listing/retention boundary,
  native bulk or explicitly authorized per-symbol operation, page/cursor/totals reconciliation, and
  no claim that today's cohort is historical HOSE membership.
- **Runtime:** documented auth/session/UA/WAF behavior, rate/retry/concurrency policy, redirects,
  compressed/decompressed byte ceilings, and one sequential global budget shared by discovery and
  flow work. Numeric ceilings remain unfrozen until owner evidence exists.
- **Legal:** explicit automation, cache/storage/retention/deletion, caller return, attribution,
  commercial/derivative, redistribution/resale, amendment, and revocation terms.
- **No-false-absence:** every snapshot symbol receives a terminal typed outcome. WAF, timeout,
  malformed/missing identity, truncation, unknown bounds, conflict, or budget exhaustion is fatal
  or unknown—not empty, zero, or complete coverage.

## Snapshot and source separation

If a source later qualifies, caller preflight validates and canonicalizes `exchange`, inclusive
dates, and explicit symbols/universe **before** universe lookup, cache lookup, or any network
operation. Malformed, empty, duplicate/conflicting, non-HOSE, legally blocked, or unbounded input
fails with zero universe calls, zero flow calls, and an untouched cache. Only after that preflight
does `symbols=None` obtain the existing current-HOSE universe exactly once at request start.
Freeze its canonical symbol tuple, `board="HOSE"`, source, real `fetched_at_utc`, optional `as_of`,
warnings, and count. Do not commit or hard-code a live cohort.

An explicit symbol iterable or `EquityUniverse` is a requested cohort and uses the same
validation/provenance/budget path; it is never evidence of a full-HOSE roster. The existing SSI
index-basket/partial-roster snapshot likewise retains `UNIVERSE_GAP` and listing-date warnings.
Those warnings must prevent a `FULL_HOSE` label even when every symbol in that requested cohort is
served. A complete full-HOSE result requires an authoritative complete current-HOSE snapshot with
response-backed board identity, declared count/bounds/as-of, and reconciliation before flow work.

The existing universe's index-basket/partial-roster and unavailable-listing-date warnings are
preserved. `fetched_at_utc` is not `as_of`; current membership is not historical membership. The
current snapshot may be applied to older sessions only with a clear survivorship/listing/delisting
limitation. Universe source identity is never flow-source identity or flow-data permission.

## Row, value, and terminal-outcome contract

These are future qualification predicates, not current public fields or enums.

- A row is keyed by `(code, session)`, with response-backed canonical HOSE code and a plain provider
  Vietnam trading-session date. Request order, path token, retrieval date, publication timestamp,
  or guessed UTC conversion cannot supply either key.
- `buy_value` and `sell_value` require source-backed daily meaning, exact VND scale/precision,
  nullability, and explicit main-board/put-through scope. A provider net or approved exact
  `buy_value - sell_value` derivation must be validated in one exact representation; contradictory
  provider net is rejected, never overwritten.
- Reject booleans, non-finite or scale-mismatched numbers, invalid nulls, identity mismatch,
  conflicting duplicates, and structurally missing required fields. Provider zero stays zero;
  missing/blank/unavailable is not zero. No fill, stitch, aggregate allocation, or OHLCV estimate.
- Provider publication lag, revision/correction identity, retention/deletion, and session calendar
  must be documented before a source can qualify.

Every snapshot symbol and provider-eligible session receives exactly one design-level terminal
outcome. Use a finite vocabulary only after a separate API decision; the design categories are:

| Outcome | Meaning | Forbidden conflation |
| --- | --- | --- |
| `SERVED` | Valid response-backed identity, fields, units, and values | Not complete-board proof by itself |
| `SERVED_DECLARED_PARTIAL` | Provider-declared narrower bound reconciled fully | Not a full-HOSE claim |
| `EMPTY_AUTHORITATIVE` | Valid identity/range/totals/calendar and provider nonpublication prove no row | Not blank/timeout/WAF/unknown total |
| `NOT_SERVED` | Provider explicitly declares unsupported/out-of-bound/unlisted | Not inferred from transport failure |
| `IDENTITY_GAP` / `FIELD_GAP` | Returned response fails required identity/field/value checks | Not zero or source absence |
| `COVERAGE_GAP` / `PAGINATION_GAP` | Bounds/pages/totals/cursors cannot reconcile the requested set | Not partial-success-as-full |
| `TRANSPORT_INCONCLUSIVE` | Status/MIME/redirect/WAF/timeout/body/TLS prevents safe interpretation | Not authoritative empty |
| `CALL_BUDGET_GAP` | Atomic budget prevents or terminates work | Not zero traffic or nonpublication |
| `NOT_DISPATCHED` | Input/source gate prevented a flow call | Not provider response or absence |

`REQUESTED_COHORT_COMPLETE` (a future internal coverage result, not a public enum) means every
symbol in the explicitly requested or retained snapshot cohort and every provider-eligible session
have declared bounds, reconciled native totals/pages/cursors, no unexplained gap/conflict, and known
listing/retention/nonpublication boundaries. It is never `FULL_HOSE`. `FULL_HOSE` later requires an
authoritative complete current-HOSE snapshot with declared count/bounds/as-of, then the same
terminal outcome and reconciliation guarantees for every symbol/session; it does not mean the
statutory historical HOSE roster. `QUALIFIED_PARTIAL` later requires provider-declared narrower
bounds plus complete served/unserved/unknown/budget accounting and no unknown/transport/pagination
gap. Current evidence supports neither qualification.

## Atomic global budget and transport

One invocation owns one sequential (`max_concurrency=1`) ledger shared by universe discovery and
flow work. Track separately:

```text
symbols, logical_units, physical_dispatches, pages_or_cursors,
retries, redirects, compressed_bytes, decompressed_bytes
```

Every ledger dimension has atomic `reserved`, `charged`, `released`, and reconciled counters:
`symbols`, `logical_units`, `physical_dispatches`, `pages_or_cursors`, `retries`, `redirects`,
`compressed_bytes`, and `decompressed_bytes`. Explicit symbols reserve their count during
preflight; a discovered snapshot reserves its validated count before the first flow dispatch. Each
logical/page/physical/retry/redirect unit reserves before dispatch; a retry or redirect is a real
physical operation. A failed reservation dispatches nothing, an uninvoked source adds no attempt,
and `charged + released == reserved` must reconcile for every dimension without decrementing
charged work. Streamed compressed bytes charge before decompression and decompressed bytes charge
after decoding. A malformed, identity-mismatched, unexpected-status, MIME-invalid, or over-cap
response consumes its real reservation and accepts no rows.

Exhaustion of **any** dimension is globally fatal: discard every private row/accumulator and return
no history, partial board, per-symbol budget result, empty, zero, or complete/partial coverage.
Preserve only bounded sanitized **real** attempts/counters on a future deferred diagnostic/error
carrier; never fabricate a `SourceAttempt` or `diagnostics_truncated` marker. No numeric ceiling or
retry timing is frozen until owner rate/pagination evidence exists. Future transport evidence must
record exact route/version, expected status class, complete MIME after the first colon, effective
route, redirects, strict TLS, UA/session/WAF behavior, pagination, and byte semantics. Generic
maintenance HTML or unexpected/colon-suffixed MIME fails even when HTTP status is 200. Public
diagnostics are bounded/sanitized and contain no raw URL/query/body/header/provider prose/cookie/
token/secret/live value.

## Owner/legal reopen gate

One exact provider-owned flow unit and one independently qualified universe unit must positively
evidence their respective owner/dataset, response-backed identity, and exact identifier binding.
The owners may differ; no universe contract grants flow permission. The flow unit must evidence
automated no-login/no-paid access or exact license terms; caller return; raw/normalized
storage/cache/retention/deletion; attribution, commercial, derivative and downstream use;
redistribution/resale; finite rate/retry/concurrency/page/redirect/byte limits; amendment/revocation;
and response-backed code/board/session/field/unit/revision semantics. Public page visibility,
Swagger, robots, HTTP 200, fee catalogue, or the existing universe contract is not permission.

Use only first-party [HOSE contact](https://www.hsx.vn/vi/lien-he), [HOSE data-feed](https://www.hsx.vn/vi/data-feed),
[HOSE tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf),
[SSI FastConnect specifications](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs),
and [SSI iBoard terms](https://www.ssi.com.vn/khach-hang-ca-nhan/dieu-khoan-va-chinh-sach-iboard)
for a future written request. Record the exact owner/team/channel, request date, written response or
reference, and dataset covered; infer no individual contact or permission.

## Future deferred API/RED/release matrix (not authorized)

This matrix is a retained release contract for a future qualified-source decision. It is explicitly
`DEFERRED/NOT_AUTHORIZED`: it freezes no current public signature, model, warning/error grammar,
diagnostics carrier, source registration, live probe, RED test, or runtime capability.

| Deferred gate | Required future contract or offline evidence | Current status |
| --- | --- | --- |
| API/model contract | Immutable universe-snapshot, per-symbol-outcome, row/history, coverage, provenance, and bounded-attempt carriers; inclusive date bounds; exact `exchange="HOSE"`; deterministic symbol ordering; DataFrame attrs; serialization/repr/equality; stable sanitized errors; caller preflight before universe/cache/network | `NOT_AUTHORIZED` |
| RED-1 universe/preflight | Current-universe acquisition/provenance; explicit-universe/symbol equivalence; invalid/empty/duplicate/conflicting/non-HOSE inputs; for each malformed input assert zero universe calls, zero flow calls, and untouched cache; exactly one snapshot fetch | `NOT_AUTHORIZED` |
| RED-2 values/identity | Board/symbol/session identity; main/put-through scope; VND scale; gross/net arithmetic; zero versus missing; ordering; duplicate/conflict; revision and publication-lag cases | `NOT_AUTHORIZED` |
| RED-3 coverage | Full-HOSE versus requested-cohort and declared-partial/unknown coverage; listing/retention boundaries; delisted/current symbols; terminal outcomes; native totals/pages/cursors; current lag; authoritative versus unknown empty; no silent drop | `NOT_AUTHORIZED` |
| RED-4 transport/budget | Malformed MIME/status/redirect/WAF/envelope; response/request identity mismatch; pagination truncation; retry/byte/global-budget failures across every ledger dimension; atomic no-partial behavior; no stitch/fill/OHLCV reconstruction | `NOT_AUTHORIZED` |
| RED-5 diagnostics/source separation | Snapshot/flow source separation; retrieval times; bounded sanitized diagnostics; no URL/query/provider/live-value leakage; public snapshots; current-universe survivorship warnings | `NOT_AUTHORIZED` |
| RED/release-6 compatibility | Existing equities universe/profile/sector compatibility; docs/API/units/tutorial/architecture/skill/CHANGELOG; full offline suite; import/version; blacklist/secret/diff/path/object/clean-tree gates; isolated wheel/sdist; exact remote anchor/ancestry/path verification | `NOT_AUTHORIZED` |

The lifecycle is immutable: **API/model freezes the contract → separate RED authorization permits
failing tests only → reviewer verifies RED and authorizes implementation → implementation reaches
GREEN → code review → publish**. No RED, production code, source registration, live probe, or
coverage claim is authorized by this source-gap packet.

## Lifecycle handoff

The #227 queue was activated after verified #226 closure; #228 remains queued after #227. The
backlog must retain the empty-chain/source-gap disposition, packet anchor, exact research/design
paths, and the next action `RETURN_EXACT_SHA_DESIGN_VERDICT`. The exact exclusion applied to every
web search was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited material was opened or used.

## Primary references

- [HOSE foreign-investor statistics](https://www.hsx.vn/vi/du-lieu-giao-dich/giao-dich-ndtnn/co-phieu)
- [HOSE data feed](https://www.hsx.vn/vi/data-feed)
- [HOSE Swagger UI](https://api.hsx.vn/mk/swagger/index.html)
- [HOSE information-service tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf)
- [SSI FastConnect API specifications](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)
- [SSI iBoard terms and policy](https://www.ssi.com.vn/khach-hang-ca-nhan/dieu-khoan-va-chinh-sach-iboard)
- [FiinGroup HOSE Stock V2 documentation](https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/hose-stock-v2)
- Local historical evidence: `docs/research/2026-08-22-vn-foreign-flow-source-vetting.md` (#201 only)
- Local current snapshot contract: `docs/sources/equities-universe.md`

## Bottom summary

- Disposition: **`SOURCE-GAP CLOSURE`**; the new full-HOSE flow chain remains empty.
- Current SSI universe is fetched/frozen once in any future request, but is not flow identity or historical membership.
- HOSE/SSI candidates lack conjunctive response identity, coverage, finite runtime, and legal proof.
- Every symbol/session later receives one terminal outcome; unknown absence is never zero or empty.
- No public API/model/diagnostic grammar is frozen; no probe, RED, code, or runtime capability is authorized.
- Reopen requires exact owner rights, declared bounds/reconciliation, atomic budget, and exact-SHA design PASS.
- Need from Boss: **nothing**; return this source-gap design for reviewer review.
