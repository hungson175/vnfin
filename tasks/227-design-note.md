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
| HOSE public statistics/feed/service | Aggregate/product/account/tariff evidence only; no no-login route plus full response/legal contract |
| SSI FastConnect daily stock price | Foreign fields documented, but access-token flow and no full-HOSE/rights proof block this no-login gate |
| Existing SSI iBoard universe | Current snapshot input only; partial/listing-date warnings and separate rights/source identity remain |
| HNX/UPCoM/SSC/other provider leads | Wrong-board, aggregate-only, or no-login/legal/coverage gaps; no substitution |

## Qualification contract for a future source

One exact owner + route/version + operation must pass every axis conjunctively:

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

If a source later qualifies, `symbols=None` obtains the existing current-HOSE universe exactly once
at request start. Freeze its canonical symbol tuple, `board="HOSE"`, source, real
`fetched_at_utc`, optional `as_of`, warnings, and count. Do not commit or hard-code a live cohort.
An explicit symbol iterable or `EquityUniverse` uses the same validation/provenance/budget path.
Malformed, empty, duplicate/conflicting, non-HOSE, legally blocked, or unbounded input fails before
any flow dispatch, with exactly zero flow calls.

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

`FULL` later means every symbol in the frozen current snapshot and every provider-eligible session,
with declared bounds, reconciled native totals/pages/cursors, no unexplained gap/conflict, and known
listing/retention/nonpublication boundaries. It does **not** mean the statutory historical HOSE
roster. `QUALIFIED_PARTIAL` later requires provider-declared narrower bounds plus complete
served/unserved/unknown/budget accounting and no unknown/transport/pagination gap. Current evidence
does not support either qualification.

## Atomic global budget and transport

One invocation owns one sequential (`max_concurrency=1`) ledger shared by universe discovery and
flow work. Track separately:

```text
symbols, logical_units, physical_dispatches, pages_or_cursors,
retries, redirects, compressed_bytes, decompressed_bytes
```

Reserve the next logical/page/physical/retry/redirect unit atomically before dispatch. A failed
reservation dispatches nothing. Each retry/redirect is a real physical operation. A malformed,
identity-mismatched, unexpected-status, or MIME-invalid response consumes its attempted reservation
and accepts no rows. Charge streamed compressed bytes before decompression and decompressed bytes
after decoding; crossing either finite cap aborts and discards private rows. No numeric ceiling or
retry timing is frozen until owner rate/pagination evidence exists.

After exhaustion, preserve prior sanitized **real** attempts and mark affected symbols with a
budget outcome; never fabricate a `SourceAttempt` or `diagnostics_truncated` marker, and never
return empty, zero, `NOT_SERVED`, or complete/partial coverage. Future transport evidence must
record exact route/version, expected status class, complete MIME after the first colon, effective
route, redirects, strict TLS, UA/session/WAF behavior, pagination, and byte semantics. Generic
maintenance HTML or unexpected/colon-suffixed MIME fails even when HTTP status is 200. Public
diagnostics are bounded/sanitized and contain no raw URL/query/body/header/provider prose/cookie/
token/secret/live value.

## Owner/legal reopen gate

One exact provider-owned flow unit must positively evidence all of the following: named owner and
dataset; automated no-login/no-paid access or exact license terms; caller return; raw/normalized
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

## Future API boundary (not authorized)

Do not freeze a public signature, model, warning/error grammar, diagnostics carrier, or unit schema
in this source-gap note. If a source later qualifies, the separate design must decide an immutable
snapshot, row/history, provenance, coverage, per-symbol-outcome, and bounded-attempt contract with
inclusive date bounds and deterministic `(session, code)` ordering. Then the lifecycle is:

1. API/model freezes the public contract.
2. Separate RED authorization permits failing tests only.
3. Reviewer verifies RED and authorizes implementation.
4. Implementation reaches GREEN.
5. Code review.
6. Publish.

No RED, production code, source registration, live probe, or coverage claim is authorized by this
note.

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
