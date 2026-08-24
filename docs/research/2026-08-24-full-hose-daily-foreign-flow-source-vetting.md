# Full-HOSE daily foreign-investor flow source vetting — #227

**Access date:** 24 August 2026 (UTC+7)
**Packet:** `tasks/227-full-hose-daily-foreign-flow-spec.md`, reviewer anchor `29206690269215dba1a35bb13ee7c621055e7fca`
**Published base:** `origin/master` `483ff56522e713ae8495dc515e4e4f5915655bd7`
**Phase:** source/design only
**Disposition:** **`SOURCE-GAP CLOSURE`**
**Runtime chain:** empty; no provider is registered or callable

## Decision

Official HOSE/HSX material proves that HOSE publishes foreign-investor trading summaries and
offers market-data services, but it does **not** prove one lawful, no-login, full-current-HOSE,
per-symbol daily-history operation with response identity, historical bounds, pagination, finite
runtime policy, and caller-return/redistribution rights. The closest public pages are aggregate or
top-five summaries; the richer webservice is contract/login-oriented. No candidate therefore meets
the packet's conjunctive gate, and no `QUALIFIED_PARTIAL` disposition is justified.

This is not a claim that HOSE has no commercial or private data. It is a bounded source-gap result.
No live API request was made, no live row was retained, and no third-party code was run.

## Clean-room boundary

Before research, `docs/vnstock-blacklist.md` was read. Every web search used this exact exclusion:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result or derivative material was opened, cited, compared, installed, or used. Only
official exchange/regulator/provider pages and documents, plus dated local evidence, are retained
below. No query-bearing URL, raw body/header,
cookie, token, response digest, provider exception, live universe, live flow value, or source-derived
fixture is committed.

## Evidence accounting

Static pages/documents are research evidence, not runtime dispatches. Candidate flow dispatches are
`0` logical and `0` physical. `0` means no request was made; it does not mean zero rows, zero traffic,
source absence, or permission. Static transport counters are `NOT_RETAINED`, not invented.

| Channel | Logical | Physical | Pages | Retries | Redirects | Compressed/decompressed bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Official pages/documents read statically | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| Candidate HOSE flow dispatches | `0` | `0` | `0` | `0` | `0` | `0/0` |

## Official source units

Each row is an independent owner + route/operation. A UI, PDF, tariff, or protocol document is
not silently promoted to an API or joined to another owner's data.

| Unit and official route | Documented facts | Missing qualification axes | Disposition |
| --- | --- | --- | --- |
| **HOSE foreign-investor statistics — stocks**
  [`/vi/du-lieu-giao-dich/giao-dich-ndtnn/co-phieu`](https://www.hsx.vn/vi/du-lieu-giao-dich/giao-dich-ndtnn/co-phieu) | Public date-range UI; “aggregate trading by security”; volume labels in `100` shares and value labels in million VND; a separate twelve-month monthly summary distinguishes foreign buy/sell from the market. | No published API/schema, response-backed `exchange`/symbol/session identity, exact buy/sell row fields, history retention, page/cursor/totals contract, revision policy, rate policy, or reuse terms. Static HTML currently exposes a JavaScript shell rather than a documented response. | `IDENTITY_GAP`, `FIELD_GAP`, `COVERAGE_GAP`, `PAGINATION_GAP`, `RATE_POLICY_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| **HOSE daily trading-summary PDF series**
  [27 February 2026 official summary](https://staticfile.hsx.vn/Uploads/UploadDocuments/2440741/20260227%20Tong%20hop%20thong%20tin%20giao%20dich.pdf) | A dated two-page official summary labels market-wide foreigner `buying`, `selling`, and `buying-selling`, with trading volume in shares and trading value in billion VND; it also publishes only top-five foreign-trading lists. | Top-five/market aggregate is not every current-HOSE symbol; no full-board history index, pagination, row totals, retention, corrections/revisions, response identity, or OSS reuse contract. | `FIELD_GAP`, `COVERAGE_GAP`, `PAGINATION_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| **HOSE annual/statistical reports**
  [2024 annual report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896445/B%C3%81O%20C%C3%81O%20TH%C6%AF%E1%BB%9CNG%20NI%C3%8AN%20%28ANUAL%20REPORT%29%202024.pdf) | Official annual/monthly foreign-investor statistics identify buy, sell, and buy-minus-sell volume/value; the report explicitly says foreign statistics include order matching and put-through and breaks results down by security type. | Aggregate/report evidence is not a daily per-symbol full-board history route; no machine contract, current universe snapshot, page/revision semantics, runtime policy, or redistribution permission. No report rows are retained. | `FIELD_GAP`, `COVERAGE_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| **HOSE market-data feed page**
  [`Data feed`](https://www.hsx.vn/vi/data-feed) | HOSE advertises a Market Data Feed/Webservice delivered through an HOSE API. | No public no-login route/version, foreign-flow package/schema, pagination/history/retention, rate/retry/concurrency, caller-return, storage/cache, attribution, or redistribution/OSS permission. | `LEGAL_GAP`, `RATE_POLICY_GAP`, `TRANSPORT_INCONCLUSIVE`, `NOT_PROBED` |
| **HOSE ECM login route**
  [`ECM login`](https://ecm.hsx.vn/hoseecm/login) | This route presents an account/password login boundary. | An authentication gate is not a no-login route or reuse grant; no foreign-flow package/schema, history, pagination, rate, caller-return, storage, or redistribution terms are retained. | `AUTH_REQUIRED`, `LEGAL_GAP`, `NOT_PROBED` |
| **HOSE information-service tariff document**
  [official tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf) | The tariff distinguishes display/non-display and online, delayed, and end-of-day products. | A fee/product catalogue does not grant OSS automation, caller return, storage/cache, or redistribution; no route/schema/history/revision/rate contract is retained. | `LEGAL_GAP`, `NOT_PROBED` |
| **HOSE current-listing/universe lead**
  [`Listed stocks`](https://www.hsx.vn/vi/quan-ly-niem-yet/co-phieu) | Official current listing navigation exists and is separate from foreign-flow statistics. | The public representation is a JavaScript shell in static retrieval; no deterministic snapshot schema, response-backed board identity, count/as-of boundary, listing/delisting history, or flow-response binding is published in retained evidence. | `UNIVERSE_GAP`, `IDENTITY_GAP`, `NOT_PROBED` |

## What is established versus missing

**Established:** HOSE is the owner of the official public pages, PDF summaries, market-data service
catalogue, and listing navigation. HOSE uses foreign buy/sell/net terminology and publishes
volume/value units. Official summaries distinguish aggregate market statistics and top-five lists;
official annual statistics explicitly include matching and put-through.

**Not established:** one exact current-HOSE universe snapshot; one response-backed `(exchange, code,
session)` identity; per-symbol daily gross/net value fields and scale; main-board/put-through scope;
session timezone, publication lag, correction/revision behavior; arbitrary historical retention;
native bulk/per-symbol pagination and reconciliation; no-login automation; rate/retry/concurrency
limits; and rights to cache, store, return to callers, redistribute, or make derivatives.

The official listing page cannot be used to turn today's cohort into historical membership. A symbol
from a separate universe page would not prove the flow response's board or symbol identity.

## SSI, prior-HOSE, and non-HOSE source boundaries

The official SSI [FastConnect API specifications](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)
document a `DailyStockPrice` operation with `Tradingdate`, `Symbol`, date inputs, `market=HOSE`,
pagination inputs, and foreign total buy/sell volume/value fields. The same documentation exposes a
separate `AccessToken` operation. This is a provider schema lead, not a no-login qualification:
the documentation does not provide a public OSS caller-return/redistribution grant, full current-HOSE
history bound, revision contract, native bulk reconciliation, or finite runtime terms. It is
`NOT_QUALIFIED` for this packet's no-login source gate, not a claim that SSI has no licensed product
or that the provider explicitly does not serve the operation.

The existing `ssi_iboard_universe` source is a separate current snapshot operation. Its local source
contract records runtime-fetch/no-redistribution posture, index-basket-derived partial coverage, and
unavailable listing dates. Those warnings are preserved if it supplies the snapshot; they do not
authorize the SSI flow fields or turn current membership into historical membership. The official
[SSI iBoard terms](https://www.ssi.com.vn/khach-hang-ca-nhan/dieu-khoan-va-chinh-sach-iboard) must
be reviewed separately before any new public caller-return surface broadens that existing contract.

The dated #201 report remains historical evidence. Its HOSE `tradingresult/{code}` sample returned a
symbol and foreign component fields, but only for three sampled names; `reportDate` session meaning,
raw value scale, current-board completeness, rate terms, revision semantics, and reuse rights stayed
unresolved. Its same-host `foreign/{code}` sample lacked a response symbol and is rejected as a
fallback. This #227 round made **zero** candidate data dispatches and does not upgrade those
observations.

HNX/UPCoM per-symbol reports are wrong-board, HNX aggregate PDFs are not HOSE rows, and SSC
publication/statistics pages are aggregate or legal evidence. None may be relabelled HOSE or used to
fill a missing symbol/session. A provider-owned [FiinGroup HOSE Stock V2 description](https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/hose-stock-v2)
names foreign total fields, but its public documentation does not establish no-login automation,
full-current-HOSE bounds, caller return, redistribution, rate, or revision terms; it remains
`NOT_QUALIFIED` for this source gate, not an assertion of provider non-service.

## Sanitized per-unit ledger

Each route below is one owner + canonical route/version + operation. `NR` means `NOT_RETAINED`,
`NP` means `NOT_PROBED`, and `NA` means wrong-board/scope. The ledger is not a fabricated runtime
record: all candidate flow dispatches in this round are zero. A static page or Swagger document
does not create a `SourceAttempt`.

| Unit | Route/method/status/MIME/effective-route/redirect evidence | Logical/physical/pages/retries/redirects/compressed/decompressed | Identity/field/coverage evidence | Access and rights evidence | Total disposition |
| --- | --- | --- | --- | --- | --- |
| `HOSE-TRADINGRESULT` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Historical #201 sample: response symbol + component labels; date/session, scale, full-board bounds, revision and totals unresolved | No retained rate, automation, cache, caller-return, redistribution, amendment, or revocation grant | `SAMPLED_ONLY`, `IDENTITY_DATE_GAP`, `FIELD_UNIT_GAP`, `COVERAGE_GAP`, `LEGAL_GAP`, `RATE_POLICY_GAP` |
| `HOSE-FOREIGN` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Historical response lacked returned symbol and date-bound contract | Same unresolved HOSE rights/rate posture | `IDENTITY_GAP`; rejected, no fallback |
| `HOSE-STOCK-STATISTICS-UI` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Static stock UI is aggregate-by-security evidence; no per-symbol response contract | Public visibility is not permission | `FIELD_GAP`, `COVERAGE_GAP`, `PAGINATION_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| `HOSE-DAILY-SUMMARY-PDF` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Dated market aggregate/top-five summary; no full-board row contract | Public PDF is not a caller-return or redistribution grant | `FIELD_GAP`, `COVERAGE_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| `HOSE-ANNUAL-REPORT` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Annual/monthly aggregate and matching/put-through terminology; no daily row contract | Report publication is not runtime/reuse permission | `FIELD_GAP`, `COVERAGE_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| `HOSE-DATA-FEED-PAGE` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Product/feed existence; exact foreign-flow route, bounds, and envelope not retained | No public no-login OSS/caller-return/cache/redistribution evidence | `LEGAL_GAP`, `RATE_POLICY_GAP`, `TRANSPORT_INCONCLUSIVE`, `NOT_PROBED` |
| `HOSE-ECM-LOGIN` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Account/password boundary; no public response contract retained | Authentication gate is not no-login permission | `AUTH_REQUIRED`, `LEGAL_GAP`, `NOT_PROBED` |
| `HOSE-TARIFF-PDF` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Product/fee categories only; no flow route or runtime contract | Fee visibility is not automation, caller-return, or redistribution permission | `LEGAL_GAP`, `NOT_PROBED` |
| `SSI-DAILY-STOCK` | `NR/GET/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Docs name `Tradingdate`, `Symbol`, HOSE selector, and foreign fields; response identity/scale/history unproven | AccessToken flow documented; no public no-login or exact data-rights grant retained | `NOT_QUALIFIED`, `LEGAL_GAP`, `COVERAGE_GAP`, `RATE_POLICY_GAP` |
| `SSI-IBOARD-UNIVERSE` | Existing source contract; no new flow dispatch | `0/0/0/0/0/0/0` for this round | Current snapshot only; partial-roster/listing-date warnings preserved; not flow identity | Existing runtime-fetch/no-redistribution contract is not flow permission | `CURRENT_SNAPSHOT_ONLY`, `UNIVERSE_GAP`; separate source |
| `FIINGROUP-HOSE-V2` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Provider docs name foreign fields; full-HOSE identity/bounds/revision unproven | Provider rights, no-login automation, caller return, and redistribution unretained | `NOT_QUALIFIED`, `LEGAL_GAP`, `COVERAGE_GAP`, `RATE_POLICY_GAP` |

The `0` values mean “not dispatched in this research round,” never zero rows, zero traffic, no
source, or permission. A future budget exhaustion preserves prior sanitized real attempts and
never fabricates a `SourceAttempt` or `diagnostics_truncated` record. HNX/UPCoM/SSC material is a
wrong-board or aggregate-only scope exclusion, not one combined source unit and never a fallback.
`NOT_QUALIFIED` is a source-qualification disposition; it does not assert provider absence.

## Future qualification contract — design only

If a source reopens, first validate and canonicalize caller `exchange`, inclusive dates, and any
explicit symbols/universe before **any** universe lookup, cache lookup, or network operation. A
malformed, empty, duplicate/conflicting, non-HOSE, legally blocked, or unbounded caller input fails
with zero universe calls, zero flow calls, and an untouched cache. Only after that preflight may
`symbols=None` fetch the current HOSE universe once and freeze its exact canonical symbol tuple,
`board="HOSE"`, source, real `fetched_at_utc`, optional `as_of`, warnings, and count.

An explicit symbol iterable or an `EquityUniverse` is a requested cohort, not proof of the full
HOSE roster. The current SSI snapshot is likewise a partial/universe-gap cohort when its retained
warnings say so. Preserve those warnings and listing/survivorship limits; never label either cohort
`FULL_HOSE` or claim a historical statutory roster. A full-HOSE result requires an independently
authoritative complete current-HOSE snapshot with response-backed board identity, declared count
and bounds/as-of, and reconciliation before flow work.

The flow source must independently return/establish canonical code, HOSE board, and plain Vietnam
session date. A request path token, request order, retrieval time, publication timestamp, or guessed
UTC conversion is not identity. Each `(code, session)` gets one terminal design-level outcome:
`SERVED`, `SERVED_DECLARED_PARTIAL`, `EMPTY_AUTHORITATIVE`, `NOT_SERVED`, `IDENTITY_GAP`,
`FIELD_GAP`, `COVERAGE_GAP`, `PAGINATION_GAP`, `TRANSPORT_INCONCLUSIVE`, `CALL_BUDGET_GAP`, or
`NOT_DISPATCHED`. These are not current public enums. Future `NOT_SERVED` is valid only for a
response-backed provider declaration of unsupported, out-of-bound, or unlisted; the current
research disposition for unproven no-login/legal/coverage is `NOT_QUALIFIED`.

`REQUESTED_COHORT_COMPLETE` (a future internal coverage result, not a public enum) requires all
symbols in the explicitly requested or retained snapshot cohort and all provider-eligible sessions,
provider-declared bounds, reconciled native totals/pages/cursors, no unexplained conflicts/gaps, and
known listing/retention/nonpublication boundaries. It is never `FULL_HOSE`. `FULL_HOSE` requires an
authoritative complete current-HOSE snapshot with declared count/bounds/as-of, then the same
terminal outcome and reconciliation guarantees for every symbol/session. `QUALIFIED_PARTIAL`
requires a provider-declared narrower provider bound plus complete served/unserved/unknown/budget
accounting; it may not claim a full-HOSE roster or 2018-current coverage. An HTTP 200 blank/HTML/
WAF/timeout/unknown total/malformed or identity-mismatched page is unknown, never authoritative
empty or zero.

The future ledger is one sequential invocation-owned budget shared by universe discovery and flow:
`symbols`, `logical_units`, `physical_dispatches`, `pages_or_cursors`, `retries`, `redirects`,
`compressed_bytes`, and `decompressed_bytes`. Every dimension has an atomic reservation, charge,
release, and reconciliation: explicit symbols reserve their count during preflight; a discovered
snapshot reserves its validated count before the first flow dispatch; each logical/page/physical/
retry/redirect unit reserves before dispatch; and streamed compressed/decompressed bytes charge at
their respective stages. `charged + released == reserved` must reconcile for every dimension, with
no decrement of charged work and no uninvoked-source attempt. A reservation failure or charge overrun
in **any** dimension is globally fatal: discard every private row/accumulator and return no history,
partial board, per-symbol budget result, empty, zero, or complete/partial coverage. Preserve only
bounded sanitized real attempts/counters on a future deferred diagnostic/error carrier; never
fabricate an attempt or truncation marker. Freeze no numeric ceiling until owner rate/pagination
evidence exists. Parse complete `Content-Type` after the first colon and reject generic maintenance
HTML or an unexpected MIME even with HTTP 200. No stitch, fill, aggregate/OHLCV reconstruction,
automatic fallback, raw URL/query/body/header/provider prose, secrets, cookies, tokens, or live values.

## Owner/legal contact and reopen axes

One future qualification must bind **two exact units** conjunctively: one provider-owned flow
route/version/operation and one independently qualified current-HOSE universe route/version/
operation. The owners may differ, but response-backed identifier binding must be proven; a universe
owner never grants flow rights and no cross-owner flow stitch is allowed.

Use only first-party contact/data-service paths: [HOSE contact](https://www.hsx.vn/vi/lien-he),
[HOSE data-feed](https://www.hsx.vn/vi/data-feed), [HOSE tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf),
[SSI FastConnect specs](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs), and
[SSI iBoard terms](https://www.ssi.com.vn/khach-hang-ca-nhan/dieu-khoan-va-chinh-sach-iboard).
The future packet must identify the exact owner/dataset and positively prove automated access,
caller return, cache/storage/retention/deletion, attribution, commercial/derivative use,
redistribution/resale, rate/retry/concurrency, amendment, and revocation. Public page visibility,
Swagger, robots, HTTP 200, a fee catalogue, or a universe contract is not permission.

## Reopen evidence

Reopen only when the exact flow unit and the exact universe unit each supply the following in official
documentation or written owner permission, with their binding explicitly evidenced:

1. The universe unit provides full current-HOSE board scope and one immutable snapshot with symbol
   count, `as_of`, listing/delisting boundary, and response-backed exchange/code identity.
2. The flow unit provides daily session date, foreign buy/sell volume and value, exact VND scale,
   net arithmetic, null/zero meaning, matching versus put-through scope, publication lag, and
   correction/revision semantics.
3. The flow unit provides provider-declared history bounds, eligible sessions, pages/cursors/totals,
   native bulk or an
   explicitly rate-authorized per-symbol operation, and deterministic reconciliation.
4. Explicit no-false-absence behavior: every snapshot symbol has a terminal typed outcome; WAF,
   timeout, malformed identity, truncation, unknown bounds, and budget exhaustion are not empty.
5. Finite rate/retry/concurrency, redirect, compressed/decompressed-byte, and whole-board budget
   rules, with owner-authorized automation and a bounded diagnostic contract.
6. Legal permission for the applicable flow and universe operations: automation, caller return,
   cache/storage/retention/deletion, attribution, commercial/derivative use, redistribution/resale,
   amendment, and revocation.

Only after those gates pass may a separate API/model decision and RED-first authorization begin. This
packet freezes no public model, warning grammar, exception, source registration, or runtime behavior.

## Sources

- [HOSE foreign-investor statistics — stocks](https://www.hsx.vn/vi/du-lieu-giao-dich/giao-dich-ndtnn/co-phieu)
- [HOSE daily trading summary, 27 February 2026](https://staticfile.hsx.vn/Uploads/UploadDocuments/2440741/20260227%20Tong%20hop%20thong%20tin%20giao%20dich.pdf)
- [HOSE 2024 annual report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896445/B%C3%81O%20C%C3%81O%20TH%C6%AF%E1%BB%9CNG%20NI%C3%8AN%20%28ANUAL%20REPORT%29%202024.pdf)
- [HOSE data feed](https://www.hsx.vn/vi/data-feed)
- [HOSE ECM login](https://ecm.hsx.vn/hoseecm/login)
- [HOSE information-service tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf)
- [HOSE listed-stock navigation](https://www.hsx.vn/vi/quan-ly-niem-yet/co-phieu)
- [SSI FastConnect API specifications](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)
- [SSI iBoard terms and policy](https://www.ssi.com.vn/khach-hang-ca-nhan/dieu-khoan-va-chinh-sach-iboard)
- [FiinGroup HOSE Stock V2 provider documentation](https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/hose-stock-v2)
- Local dated evidence: `docs/research/2026-08-22-vn-foreign-flow-source-vetting.md` (#201; historical only)
- Local current-universe contract: `docs/sources/equities-universe.md`

## Bottom summary

- Decision: **`SOURCE-GAP CLOSURE`**; no current full-HOSE daily foreign-flow source qualifies.
- HOSE public statistics are aggregate/top-five; the separate market-data feed page, ECM login route,
  and information-service tariff are individual official leads whose retained evidence does not
  qualify a public no-login foreign-flow operation or bind those routes/documents to one another.
- Prior HOSE `tradingresult` evidence is sampled only; `foreign/{code}` fails response identity.
- SSI documents daily foreign fields but requires an access-token flow and lacks rights/coverage proof.
- Existing SSI universe is current/partial and remains separate from flow identity and legal scope; it can never establish `FULL_HOSE`.
- Candidate dispatches are zero; no live rows, probes, RED tests, code, or runtime capability were added.
- Reopen requires conjunctive identity, coverage, transport/budget, legal, and exact-SHA gates.
- Need from Boss: **nothing**; return this source-gap packet for reviewer design review.
