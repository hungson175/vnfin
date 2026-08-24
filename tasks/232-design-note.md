# #232 design note — raw CSI 300 CNY daily index history

**Date:** 24 August 2026 (UTC+7)
**Packet:** `tasks/232-csi300-raw-cny-history-spec.md` at reviewer `c69e145`
**Published design base:** `origin/master` exact `d76bd6b6388855cb06a0febf575646a9b960556e`
**Activation receipt:** local `023b23d2df3e04c208437ffe0260dc281854fb05` (excluded from this clean handoff ancestry)
**Phase:** `SOURCE_DESIGN` / docs-only
**Disposition:** **`SOURCE-GAP CLOSURE`**
**New raw CSI 300 chain:** empty
**Companion evidence:** [`docs/research/2026-08-24-csi300-raw-cny-history-source-vetting.md`](../docs/research/2026-08-24-csi300-raw-cny-history-source-vetting.md)

This note binds the source/design gate only. It authorizes no source registration, selector, enum,
model, warning, exception, RED test, API/model decision, proxy replacement, live data retention,
production code, push, or issue close.

## 1. Scope and clean-room boundary

The target is provider-published **raw CSI 300 daily history in CNY index points**, with a requested
inclusive lower bound of `2013-01-01` and a provider-current upper bound. It excludes ASHR or any
other ETF, futures, CFD, total-return/net-return series, currency conversion, constituent-basket
reconstruction, local calculation, cross-provider/date/field stitch, and downstream China-risk or
trading signal logic.

The project blacklist checklist was read before this source review. The exact exclusion appended to every
web search was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

Only official CSI, SSE, CIIS, SSI, and exchange/regulator evidence is used. No blacklisted or
derivative source, wrapper, copied dataset, endpoint map, login/session bypass, paid/private feed,
credential, query-bearing URL, raw response, live value, raw body/header, cookie, token, response
digest, or provider exception prose is retained. No provider route was probed.

## 2. Current behavior and no-capability contract

The current world-index path is separate and unchanged:

- `vnfin.indices.world("^CSI300", ...)` may serve the US-listed `ASHR` ETF through Alpha Vantage;
- its metadata is `USD/share (ASHR ETF)`, with `proxy_for="^CSI300"` and a `proxy_substitution`
  warning; and
- no caller may treat that result as raw CSI 300 CNY index points, silently convert it, merge it,
  or use it to fill a raw-history gap.

This design does not add a raw CSI 300 selector to `index_history`, `index_history_stitched`, or
`world`. It does not change existing world/VN index sources, source order, cache identity, models,
exports, snapshots, warnings, or documentation. The new raw chain is empty and there is no
runtime capability claim.

A source-gap design PASS can authorize only publication of the exact research/design/backlog
artifacts, remote verification, a clean no-capability resolution, and issue closure. It cannot
authorize RED, an API/model decision, a source adapter, a transport seam, or implementation.

## 3. Qualification unit and decision

A future qualification unit is one complete tuple:

```text
owner + route operator + exact host/path/version/operation
+ response-backed CSI 300/raw-price-index identity
+ CNY/index-points/session/date/field semantics
+ provider-declared bounds and reconciled daily coverage
+ status/MIME/redirect/pagination/revision behavior
+ finite rate/retry/page/redirect/byte policy
+ written or exact published reuse rights
```

Every member must pass in one route set. An owner factsheet cannot repair an API identity gap; a
generic API schema cannot repair a CNY/points or raw-versus-return gap; a commercial product cannot
be treated as an OSS licence; and agreement between providers cannot establish response identity.

| Candidate | Established evidence | Blocking axes | Design result |
| --- | --- | --- | --- |
| CSI owner/factsheet/methodology | CSI official code `000300`, CNY/RMB metadata, point semantics, price-versus-return distinction, publication controls | no no-login history response, field schema, bounds/pages/revisions, or reuse grant | `SOURCE-GAP` |
| SSE/CIIS historical product | official CSI-index/SHSE-SZSE 300 historical-data product lead, daily CSV/yearly subscription, official historical bound statement | subscription/licence, exact 000300 response identity, OHLC/volume/revision schema, caller-return rights | `SOURCE-GAP` |
| CSI CSIBridge portal | official API discovery and subscription-key documentation | no exact CSI 300 product route retained; key required; autonomous-agent written authorization required | `SOURCE-GAP` |
| SSI FastConnect DailyIndex | official generic index/date/page schema and authenticated market-data documentation | account/key/approval, generic not CSI300-specific, no raw/OHLC/CNY/coverage/reuse proof | `SOURCE-GAP` |

No candidate is `QUALIFIED FOR API/RED` or `QUALIFIED_PARTIAL`. The safe disposition is
`SOURCE-GAP CLOSURE` and the raw chain stays empty.

## 4. Identity and semantic gates for a future source

A future response must prove all fields below, not merely echo the requested token:

| Gate | Required response-backed proof | Fail-closed condition |
| --- | --- | --- |
| Instrument | CSI 300 name/code/owner and request-response agreement; documented alias mapping only | ASHR/ETF/future/CFD/other index/unknown code/mismatch |
| Series type | raw price index, not total return or net return | adjusted/return/synthetic/converted series |
| Currency/unit | exact `CNY` or `RMB` metadata and canonical `index points` unit | missing, inferred, contradictory, or security-price units |
| Session | provider China trading-session date and declared timezone; retrieval timestamp separate and UTC-aware | retrieval date substituted, naive timestamp, UTC truncation, undocumented timezone |
| Values | finite required values; `low <= open/close <= high`; declared precision and nullability | boolean, non-finite, negative, malformed, null required value, invariant failure |
| Volume | optional only with same-provider meaning, unit, type, precision, and nullability | borrowed ETF/constituent/exchange/futures volume or invented zero |
| Revision | correction/restatement/withdrawal identity, active revision, publication/retrieval separation | conflicting revision, stale response, unbound correction |
| Calendar | provider-defined eligible sessions, holidays, suspensions, non-publication | missing date unexplained inside declared eligible range |

CSI's official methodology establishes that CSI 300 is measured in points and distinguishes its
price index from total-return and net-return derivatives. The factsheet establishes the official
code and RMB metadata. Those documents do not make a future provider response identity-positive.
The future source must bind the fields above to one exact route/version and legal route set.

### 4.1 Alias and wrong-instrument contract

No public alias is frozen in this source-gap design. A future API decision may define a canonical
raw selector and documented provider aliases only after a response-backed mapping. Until then,
`000300`, `399300`, `SHSZ300`, `SHSN300`, `.CSI300`, `CSI300`, ETF tickers, futures symbols, and
return-index codes are not interchangeable. A response carrying a different code or instrument
fails identity; it is not remapped by string similarity.

The existing `^CSI300` world symbol remains a proxy request with its loud ASHR/USD metadata. It is
not an identity alias for a raw CNY index selector.

## 5. Coverage, empty, and atomicity contract

`FULL` requires one provider route set to declare and serve every eligible daily session from
`2013-01-01` through its current published bound, with reconciled totals/pages/cursors, no
unexplained gap, duplicate, conflict, truncation, or revision ambiguity, and a disclosed current
bound lag.

`QUALIFIED_PARTIAL` requires a provider-declared narrower complete range and must expose both served
and unserved/unknown bounds. The caller cannot turn a recent-only product into `2013-current` by
assuming earlier data or concatenating another source.

One source wins the whole request. A strict request never combines CSI and SSE/CIIS/SSI dates, uses
one source's OHLC with another's close, or fills a missing page from ASHR or a basket. Any identity
mismatch, late-page failure, conflicting date, unknown bound, revision conflict, or budget
exhaustion discards all private rows and returns no partial/false-complete/zero-filled result.

`NOT_SERVED` and authoritative empty are future typed outcomes only:

- `NOT_SERVED` requires a response-backed provider declaration that the requested exact CSI 300
  scope is outside the provider's service. A timeout, WAF, missing page, uncalled route, or generic
  API documentation cannot produce it.
- `EMPTY_AUTHORITATIVE` requires request/response identity, provider-declared bounds/totals,
  complete pagination, calendar semantics, and explicit non-publication semantics to reconcile.
- timeout, challenge/WAF, unknown bounds, stale/current-only page, truncated/decompression-failed
  response, missing identity, or a missing rights axis is unknown/fatal, never empty, zero, or
  absence proof.
- non-trading sessions have no synthetic row; a date gap is accepted only when the provider explains
  it within its declared calendar/non-publication contract.

## 6. Sanitized source and budget ledger

This source-design pass made no candidate data dispatch. Static official research traffic is not a
candidate ledger and its per-request status/MIME/redirect/bytes were not retained.

```text
candidate logical units / physical dispatches / pages / documents / retries / redirects /
compressed bytes / decompressed bytes = 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0
```

No `SourceAttempt`, empty outcome, or diagnostics-truncation record is fabricated. `NOT_PROBED`,
`NOT_RETAINED`, and `NOT_ESTABLISHED` describe evidence state only; none means absent, empty, or
permission.

Future numeric ceilings are deliberately `NOT_FROZEN` until the exact route's written/public rate
policy is qualified. The future ledger shape is fixed and every ceiling must be a positive finite
integer except retry/redirect ceilings, which may be zero:

```text
max_logical_units, max_physical_dispatches, max_pages, max_documents,
max_retries, max_redirects, max_compressed_bytes, max_decompressed_bytes
```

Reservations are one deterministic request-scoped ledger:

1. caller validation and capability checks occur before cache/network and consume no budget;
2. reserve one logical unit before entering the selected source route set;
3. reserve one physical dispatch immediately before every initial request, page, retry, or redirect;
4. reserve page/document counters separately before the corresponding dispatch; a failed dispatched
   request remains charged and is never refunded;
5. charge compressed bytes as received and decompressed bytes as decoded, before materialization;
6. run pages sequentially in provider-declared order with no reset per page, calendar segment,
   source, field, or retry; and
7. on any ceiling exhaustion, abort/discard private rows and return one bounded terminal token.

There is no per-source fallback budget, no hidden page scheduler, no unbounded decompression, no
parallel fan-out, and no partial result after exhaustion. A future diagnostic can expose only a fixed
source role, fixed token, validated date, and finite counts; it cannot expose raw URL/query, headers,
cookies, body, token, or arbitrary provider exception text.

## 7. Legal and runtime posture

| Axis | CSI owner | SSE/CIIS product | SSI FastConnect | Status |
| --- | --- | --- | --- | --- |
| Automation | key-controlled CSI portal; AI/autonomous use requires written authorization | subscription/order and controlled dissemination | account, approval, API key/secret and bearer token | `AUTH_REQUIRED` + `LEGAL_GAP` |
| Caller return | no OSS grant in factsheet/methodology | no public grant; licensed product posture | no OSS caller-return grant | `LEGAL_GAP` |
| Cache/storage/retention/deletion | not granted | contract required | contract required | `LEGAL_GAP` |
| Attribution/trademark | notice/trademark only | ownership notice only | provider terms | not a reuse grant |
| Commercial/derivative | not granted | licence scope not retained | not granted | `LEGAL_GAP` |
| Redistribution/resale | not granted | licensed-vendor/subscription model | not granted | `LEGAL_GAP` |
| Rate/retry/concurrency | route policy not retained | product policy not retained | rate headers documented; numeric route rights not retained | `RATE_POLICY_GAP` |
| Amendment/revocation | exact contract not retained | subscription/licence terms not retained | account may be suspended; data rights not retained | `LEGAL_GAP` |

The official SSE rules' ownership restriction and CSI/SSI notices are controls, not permission for
this open-source library. Written permission would need to name the exact owner, route/version,
fields, bounds, caller return, storage, attribution, derivative/commercial, redistribution/resale,
rate, amendment, and revocation rights.

## 8. Deferred API/model decision and RED matrix

This packet freezes no public selector, accessor, enum, model, carrier, warning, exception, source
registration, or transport seam. After a qualified source, a separate API decision must decide
whether raw history is a new accessor or an explicit extension, while preserving the existing
`^CSI300` ASHR/USD proxy contract.

Only after source qualification and API PASS may RED tests be authorized. The future synthetic
offline matrix must include:

| Area | Required cases | Current status |
| --- | --- | --- |
| Preflight | malformed/blank/bool/reversed dates, non-D1, unknown/ETF/future/return selectors, zero network | deferred |
| Identity | correct/wrong/missing code/name/owner, request/response mismatch, raw-versus-return/ETF/future rejection | deferred |
| Currency/unit | exact CNY and points, missing/contradictory scale, security-price confusion | deferred |
| Session/time | provider China session date/timezone, retrieval UTC, publication separation, naive/UTC truncation negatives | deferred |
| Values | finite OHLC, low/open/close/high invariant, type/precision/nullability, no synthetic/negative/non-finite | deferred |
| Volume | provider-defined optional volume positive/negative/nullability/unit cases, no borrowed/zero volume | deferred |
| Coverage | 2013 lower bound, FULL, declared PARTIAL, current lag, totals/pages/cursors, holidays, gaps, duplicates | deferred |
| Revision | corrections, withdrawals, active revision, conflicting row/document, publication/effective/retrieval dates | deferred |
| Transport | status, complete MIME after first colon, normalized MIME, redirects/final host, TLS/session/WAF, envelope | deferred |
| Budget | logical/physical/page/document/retry/redirect/byte reservations, no reset, deterministic exhaustion | deferred |
| Atomicity | late page failure, identity mismatch, revision conflict, any exhaustion, no partial/zero/stitch | deferred |
| Empty | provider-backed `NOT_SERVED`, reconciled authoritative empty, unknown empty and timeout negatives | deferred |
| Compatibility | ASHR proxy warning/metadata, existing world/VN index paths, snapshots/docs/import/version | deferred |
| Release | focused/full offline tests, docs/API/units/skill/CHANGELOG if API changes, build, diff/path/object/security | deferred |

No test, fixture, parser, mapping, adapter, model, or runtime capability is created in #232.

## 9. Conjunctive reopen gate and lifecycle

Reopen requires one fresh primary-source packet binding all of these to one route set:

1. response-backed CSI 300/raw-price-index identity, exact CNY/points, session/time, value/OHLC,
   optional provider-defined volume, and revision/non-publication semantics;
2. exact host/path/version/operation, status/complete MIME/normalized MIME, redirects/final host,
   auth/session/UA/WAF posture, pagination/document envelope, and no-login or written automation
   permission;
3. provider-declared `2013-01-01..current-bound` FULL coverage or a declared complete narrower
   bound with totals/pages/cursors and no unexplained gaps;
4. finite route-specific rate/retry/concurrency/page/redirect/byte ceilings with actual streaming
   and deterministic global exhaustion; and
5. written or exact published rights for automation, caller return, cache/storage/retention/
   deletion, attribution, commercial/derivative use, redistribution/resale, amendment, and
   revocation.

A factsheet, methodology, current snapshot, generic API schema, subscription catalogue, timeout,
ETF/proxy, basket, or cross-provider agreement cannot reopen the gap.

After exact design PASS, the allowed sequence is: rerun merged docs/full/build/blacklist/secret/
diff gates; publish only the exact approved research/design/backlog paths; verify remote HEAD, base
ancestry, exclusions, and paths; post a clean no-capability `SOURCE-GAP` resolution; close/re-read
#232; then record local completion. No later local receipt may cross the approved remote anchor.

## 10. Primary references

- [CSI 300 official factsheet](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/000300factsheet.pdf)
- [CSI 300 methodology](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/000300_Index_Methodology_cn.pdf)
- [CSI index-detail/download landing](https://www.csindex.com.cn/en/indices/index-detail-download/000300)
- [CSI developer portal](https://uat-apim-developer.csiweb.cloud/GettingStarted)
- [CSI equity-index calculation rules](https://oss-ch.csindex.com.cn/contract/cms_add/20240726155157-Calculation%20Rules%20for%20Equity%20Indices%20of%20China%20Securities%20Index%20Company%20Limited.pdf)
- [SSE historical data products](https://english.sse.com.cn/markets/dataservice/products/)
- [SSE market-data ownership rule](https://www.sse.com.cn/lawandrules/sselawsrules/repeal/rules/c/c_20230418_5720138.shtml)
- [CIIS historical-data introduction](https://www.ciis.com.hk/hongkong/en/historicaldata1/his_introduction/index.shtml)
- [CIIS historical-data product manual](https://www.ciis.com.hk/hongkong/en/uploadfiles/202211/07/2022110710413533120137.pdf)
- [SSI FastConnect overview](https://developers.ssi.com.vn/docs/getting-started/overview)
- [SSI FastConnect terms and environments](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
- [SSI DailyIndex schema](https://fc-data.ssi.com.vn/Help/Api/POST-api-Market-GetDailyIndex)

## Bottom summary

- #232 is `SOURCE_GAP_CLOSURE`; the raw CSI 300 CNY history chain remains empty.
- CSI identity/points/CNY evidence passes only as owner control, not as a reusable history route.
- SSE/CIIS are official subscription products; SSI is authenticated and generic; no keyless qualified unit exists.
- Identity, raw-versus-return semantics, OHLC/volume, coverage, budgets, and reuse rights remain conjunctive gaps.
- Existing `^CSI300 -> ASHR` USD/share proxy behavior is preserved exactly.
- No probe, live row, RED, API/model decision, source registration, code, push, or close is authorized.
- Reopen requires one exact route set with response identity, 2013-current/declared coverage, finite budgets, and rights.
