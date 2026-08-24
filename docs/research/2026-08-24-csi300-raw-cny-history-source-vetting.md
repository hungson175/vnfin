# CSI 300 raw CNY daily-history source vetting — #232

**Research/access date:** 24 August 2026 (UTC+7)
**Packet:** `tasks/232-csi300-raw-cny-history-spec.md` at reviewer `c69e145`
**Published base:** `origin/master` exact `d76bd6b6388855cb06a0febf575646a9b960556e`
**Local activation receipt:** `023b23d2df3e04c208437ffe0260dc281854fb05` (not in this clean publish ancestry)
**Phase:** `SOURCE_DESIGN` / docs-only
**Requested lower bound:** `2013-01-01`; upper bound is the provider's current published bound at a future qualified run
**Disposition:** **`SOURCE-GAP CLOSURE`**
**New raw CSI 300 chain:** empty

This is a clean-room source, identity, semantics, runtime, and reuse review. It does not add a
source, selector, model, API, test, proxy replacement, or runtime capability. No candidate data route
was probed. The current `^CSI300` world-index behavior remains the separately documented ASHR ETF
proxy in USD/share.

## 1. Clean-room boundary and research method

The project blacklist checklist was read before this research. The exact exclusion appended to every
web search was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted or derivative result was opened, cited, compared, installed, imported, or used. The
research uses only official CSI, SSE, CIIS, SSI, and exchange/regulator-owned material. Search
results that were not official primary evidence were discarded. A missing licence, route, field,
or response identity is recorded as a gap, never inferred from a chart, factsheet, filename, or
provider name.

No login, API key, subscription, account, token, browser session, cookie, WAF challenge, endpoint
probe, live price, raw row, raw body, raw header, query-bearing URL, response digest, provider
exception, copied dataset, wrapper, notebook, unofficial endpoint map, or paid/private feed was
retained. Static official pages and PDFs are evidence review only; they are not candidate data
fetches.

## 2. Existing repository boundary

The current world-index accessor has an explicit, separate contract:

- `vnfin.indices.world("^CSI300", ...)` asks for a world-index symbol but may serve the US-listed
  `ASHR` ETF through the existing Alpha Vantage path, labelled `USD/share (ASHR ETF)` with
  `proxy_for="^CSI300"` and a `proxy_substitution` warning;
- the ASHR result is not a CSI 300 index-point series, does not carry CNY index-point semantics,
  and must not be silently relabelled, converted, merged, or used as raw history; and
- the new raw-index design does not alter the world-index chain, Alpha Vantage BYOK behavior,
  Stooq behavior, `PriceHistory` snapshots, or any existing Vietnam-index route.

The current index-value allow-list has no newly served CSI 300 raw route. This packet does not add a
raw selector or claim that a current `index_history` call can serve it. A future API/model decision
must choose an explicit raw-versus-proxy boundary without changing existing callers silently.

## 3. Requested primitive and qualification predicate

The requested primitive is provider-published **daily raw CSI 300 index history in CNY index
points**. It is not an ETF, futures contract, constituent basket, total-return index, net-return
index, currency-converted series, synthetic local calculation, or caller-side signal.

One qualification unit is the complete tuple:

```text
legal owner + route operator + exact host/path/version/operation
+ response-backed CSI 300 identity and raw-price-index semantics
+ CNY/index-points/date/time/field contract
+ provider-declared bounds and reconciled daily coverage
+ status/MIME/redirect/pagination/revision behavior
+ finite rate/retry/page/redirect/byte budget
+ automation, cache, storage, attribution, derivative, and redistribution rights
```

All tuple members are conjunctive. CSI methodology can establish what the index is, but cannot make
a generic provider response a CSI 300 response. A public chart, current snapshot, generic API method,
search-result title, or official factsheet cannot establish a reusable historical route.

### 3.1 Required identity and value semantics

A future accepted response must prove, in the response or an explicitly bound provider contract:

- requested identity is CSI 300 itself, with a provider symbol/code and name that agree with the
  request; `000300`, `399300`, `SHSZ300`, `SHSN300`, `.CSI300`, and provider aliases are not silently
  collapsed unless the same provider documents the exact equivalence;
- the series is the raw **price index**, not CSI 300 total-return, net-return, ETF, futures, CFD,
  adjusted security prices, USD conversion, or synthetic proxy;
- currency metadata is exactly CNY/RMB and value unit is exactly `index points`, not a CNY security
  price; the canonical public spelling is deferred until a later API decision;
- `session` is the provider's China market-session date in its declared timezone, normally
  `Asia/Shanghai` only when the source documents it; `retrieved_at_utc` is a separate UTC-aware
  retrieval timestamp and never a replacement for the session date;
- OHLC fields, if required by the future carrier, are finite provider-published index levels with
  `low <= open/close <= high`; booleans, non-finite, negative, malformed, or null required values
  fail atomically;
- optional volume is accepted only when the same provider defines volume for this exact index
  response, including unit, meaning, type, precision, and nullability; no constituent, ETF,
  exchange-total, turnover, or futures volume may be borrowed or replaced with zero; and
- corrections, revisions, duplicate/conflicting sessions, holidays, suspensions, non-publication,
  current-bound lag, and publication/retrieval timestamps are distinct source-backed dimensions.

The official CSI methodology says the index is calculated in points and distinguishes the price
index from total-return and net-return variants. That proves semantic controls, not a historical
response schema. A provider that returns only a close/index value without the required future field
contract remains unqualified for an OHLC carrier; no field is manufactured.

### 3.2 Coverage and result semantics

The fixed requested lower bound is inclusive `2013-01-01`. `FULL` is allowed only when one qualified
provider route set proves every provider-declared eligible session through its current published
bound, reconciles totals/pages/cursors, explains holidays and suspensions, proves no duplicate or
conflicting session, and discloses current-bound lag and revision behavior.

`QUALIFIED_PARTIAL` is allowed only for a provider-declared narrower useful interval whose first and
last bounds, eligible-session rule, totals/pages/cursors, gaps, revisions, and current lag reconcile.
The public disposition must expose served and unserved/unknown bounds. It must never be presented as
`2013-current` by caller inference.

One source wins the whole request. No source may supply dates while another supplies OHLC, no
cross-provider date stitch is allowed, and no ASHR/ETF/proxy observation may enter raw history.
Non-trading dates have no synthetic row. Empty is authoritative only when request identity,
provider-declared bounds/calendar/totals, and explicit non-publication semantics reconcile. Timeout,
WAF/challenge, unknown bounds, truncated pages, an uncalled route, or a recent-only page is fatal
unknown, not `NOT_SERVED`, zero, empty, or complete coverage.

## 4. Primary-source candidate matrix

The following are independent owner/route hypotheses. The static evidence rows do not represent
provider data dispatches. A route is not qualified merely because its owner publishes CSI 300 or a
generic index-data product.

| Unit | Official evidence and exact operation boundary | Positive evidence retained | Decisive gaps and disposition |
| --- | --- | --- | --- |
| `CSI-FACTSHEET-000300` | [CSI 300 official factsheet](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/000300factsheet.pdf); static factsheet document, not a history operation | CSI-owned identity, code `000300`, launch date, CNY/RMB metadata, 300 constituents, base date/value, price/return derivative labels, trademark/notice | No history route, response schema, bounds/pages/revisions, runtime, or reuse grant; `IDENTITY_PASS` + `COVERAGE_GAP` + `LEGAL_GAP` |
| `CSI-METHODOLOGY-000300` | [CSI 300 methodology](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/000300_Index_Methodology_cn.pdf); static methodology document | Points and three-decimal precision, price-index formula, official publication channels, daily/real-time publication, price versus total/net-return distinction, correction rules | Methodology is not an archive/API, does not disclose no-login automation, page totals, historical response fields, or OSS reuse; `RULE_CONTROL_ONLY` + `SEMANTICS_CONTROL` + `LEGAL_GAP` |
| `CSI-LANDING-000300` | [CSI index-detail/download landing](https://www.csindex.com.cn/en/indices/index-detail-download/000300); JavaScript web landing; underlying calls were not probed | Official owner navigation and a route family for index-detail/download material | No retained stable API/document operation, MIME/redirect/pagination, historical bound, response identity, or rights; `NAVIGATION_ONLY` + `TRANSPORT_INCONCLUSIVE` + `COVERAGE_GAP` |
| `CSI-CSIBRIDGE-API` | [CSI developer portal](https://uat-apim-developer.csiweb.cloud/GettingStarted); API product/discovery operation only; UAT hostname and product route are not treated as production data route | Official portal states a subscription key is needed, API products are exposed through the dashboard, and test calls use prefilled authorization/key headers | No exact CSI 300 product/route/response or history coverage was identified; subscription key is not no-login; portal's autonomous-agent policy requires written authorization; `AUTH_REQUIRED` + `IDENTITY_GAP` + `LEGAL_GAP` |
| `SSE-EOD-CSI` | [SSE historical data service](https://english.sse.com.cn/markets/dataservice/products/); day-end historical-data product operation | Official SSE says historical data includes the SHSE-SZSE 300 Index and CSI indices, is daily CSV, has a stated earliest date of 19 December 1990, and uses yearly subscription | Product is subscription/licensed; exact 000300 response identity, OHLC/close fields, CNY/points metadata, revisions, pages, current bound, and reuse rights are not retained; `COMMERCIAL_LEAD` + `AUTH_REQUIRED` + `SEMANTICS_GAP` + `LEGAL_GAP` |
| `CIIS-CSI-HIST` | [CIIS historical-data introduction](https://www.ciis.com.hk/hongkong/en/historicaldata1/his_introduction/index.shtml) and [product manual](https://www.ciis.com.hk/hongkong/en/uploadfiles/202211/07/2022110710413533120137.pdf); order/subscription operation | Official CIIS describes CSI historical products as directly provided by CSI and directs users to order forms/technical specifications; the manual describes index fields and RMB currency coding | Subscription/order route, not public no-login; exact CSI 300 OHLC semantics, route identity, 2013-current bound, revisions, and OSS/caller redistribution are not granted; `COMMERCIAL_LEAD` + `AUTH_REQUIRED` + `LEGAL_GAP` |
| `SSI-DAILYINDEX` | [SSI FastConnect overview](https://developers.ssi.com.vn/docs/getting-started/overview), [terms/environments](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments), and [official DailyIndex schema](https://fc-data.ssi.com.vn/Help/Api/POST-api-Market-GetDailyIndex); authenticated market-data operation | Generic DailyIndex request has `IndexId`, dates, page index/size; response schema has index identity/value/date/time and aggregate fields; official service documents key/secret, bearer token, limits, and historical data | Requires account, registration/approval, API key/secret; exact CSI 300 support, raw/return identity, CNY/points, OHLC, provider bounds, revisions, and redistribution rights are not proven; `AUTH_REQUIRED` + `IDENTITY_GAP` + `SEMANTICS_GAP` + `LEGAL_GAP` |
| `SSE-MARKET-DATA-RULE` | [SSE trading rules/data-ownership clause](https://www.sse.com.cn/lawandrules/sselawsrules/repeal/rules/c/c_20230418_5720138.shtml); legal control, not a data route | Official rule text states exchange trading information is owned by SSE and use/dissemination requires permission | This is a restriction/control, not a reuse grant; no route or caller-return permission; `LEGAL_CONTROL_ONLY` + `LEGAL_GAP` |

### 4.1 No candidate passes the no-login/reuse gate

CSI's own developer portal is not a keyless route: it requires a subscription key and states that
AI/autonomous access is prohibited unless CSI gives written authorization for each use. SSE's
historical data page describes yearly subscription, licensed dissemination, and overseas ordering
through CIIS. CIIS describes direct official products but an order/subscription workflow. SSI
requires a trading account, registration/approval, API key/secret, and bearer token. These are
legitimate commercial or controlled leads, but none is a public no-login route with an affirmative
OSS caller-return/cache/redistribution grant.

Public visibility, the official CSI methodology/factsheet, an index name in a generic API schema, a
CSV format, a paid catalogue, or an exchange's historical-data description does not prove the exact
raw CSI 300 route or permission for this library. The legal outcome is conservative: `LEGAL_GAP`.

### 4.2 Identity and semantics are not repaired by provider agreement

CSI official material proves that `000300` is CSI 300 and that the price index is measured in points.
The SSE data page proves a broad SHSE-SZSE 300/CSI historical-data product exists. SSI's DailyIndex
schema proves a generic index-value operation. None of these independently proves that a future
response has the requested response-backed `CSI 300` identity, raw price-index type, CNY metadata,
China session date, OHLC field meaning, optional volume definition, revision identity, and exact
2013-current bounds. A future source review must bind these facts to one provider route/version and
one legal route set; cross-source agreement cannot substitute for response identity.

## 5. Sanitized static-evidence and candidate-dispatch ledger

Static web/document reads were performed only for official evidence. Their per-request HTTP status,
complete Content-Type, normalized MIME, redirect chain, session/UA/WAF, and byte counters were not
retained as candidate transport records. They are therefore `NOT_RETAINED`, not zeros and not
successes.

The qualifying data ledger is separate and exact for this docs-only round:

```text
research hypotheses assessed: 7
provider-data logical units dispatched: 0
provider-data physical dispatches: 0
pages/cursors: 0
retries: 0
redirects: 0
compressed bytes: 0
decompressed bytes: 0
```

No `SourceAttempt`, `EMPTY_AUTHORITATIVE`, `NOT_SERVED`, `diagnostics_truncated`, or response
identity is fabricated. A future permitted probe must record a sanitized owner/route/version,
status class, complete Content-Type before deriving normalized MIME, final effective host, bounded
redirects, page/cursor/document identity, and exact logical/physical/byte ledger. It must not retain
raw bodies, headers, cookies, query-bearing URLs, tokens, or arbitrary provider exception prose.

| Unit family | Static evidence | Candidate data logical / physical | Pages / retries / redirects | Bytes | Response identity | Disposition |
| --- | --- | ---: | --- | --- | --- | --- |
| CSI owner factsheet/methodology/landing | official PDF and JS landing reads | `0 / 0` | `0 / 0 / 0` | `0 / 0` | no response retained | `IDENTITY_EVIDENCE_ONLY` |
| CSI CSIBridge | official portal read | `0 / 0` | `0 / 0 / 0` | `0 / 0` | no response retained | `AUTH_REQUIRED` + `LEGAL_GAP` |
| SSE/CIIS history products | official product/manual reads | `0 / 0` | `0 / 0 / 0` | `0 / 0` | no response retained | `COMMERCIAL_LEAD` + `SEMANTICS_GAP` |
| SSI DailyIndex | official docs/schema reads | `0 / 0` | `0 / 0 / 0` | `0 / 0` | no response retained | `AUTH_REQUIRED` + `IDENTITY_GAP` |

Static evidence is not counted as provider pages or retries. The zero candidate ledger is not a
claim that a provider has no data or no pages.

## 6. Legal, automation, and redistribution posture

The legal axes are independent and all are required:

| Axis | CSI owner material | SSE/CIIS data service | SSI FastConnect | Current disposition |
| --- | --- | --- | --- | --- |
| Automated access | CSI developer portal requires key and written authorization for autonomous/AI access | subscription/order and authority-controlled dissemination | account, approval, API key/secret, bearer token | `LEGAL_GAP` / `AUTH_REQUIRED` |
| Caller return | no published OSS caller-return permission | no public grant; licensed service posture | terms and account control; no OSS caller-return grant | `LEGAL_GAP` |
| Cache/storage/retention/deletion | not granted by factsheet/methodology | product contract required | product terms required | `LEGAL_GAP` |
| Attribution/trademark | CSI trademark/notice is not data licence | SSE/CIIS ownership notices | SSI provider terms | written exact permission required |
| Commercial/derivative use | not granted | subscription/licence scope unknown | account terms do not grant library redistribution | `LEGAL_GAP` |
| Redistribution/resale | not granted | licensed-vendor model and annual subscription | not granted | `LEGAL_GAP` |
| Rate/retry/concurrency | key/product policy not retained | service contract/product policy needed | headers disclosed but numeric route policy and reuse are not granted | `RATE_POLICY_GAP` |
| Amendment/revocation | portal/data terms may change; exact contract not retained | subscription/licence can be changed; exact terms not retained | account can be suspended; exact data rights not retained | `LEGAL_GAP` |

The SSE rule's ownership clause is a legal restriction, not permission. CSI factsheet disclaimers and
trademark notices are identity/notice controls, not redistribution grants. No public material found
in this bounded review grants this open-source library automation, caller return, transient cache,
durable storage, derivatives, commercial use, or resale for the exact series.

## 7. Future transport and budget contract (not authorized now)

No numeric runtime ceiling is frozen in this source-gap packet. A future source/API decision must
replace `NOT_FROZEN` with positive finite integers justified by the exact route's written/public rate
policy. The shape is fixed now so a later implementation cannot reset or hide accounting:

```text
max_logical_units       : positive integer, NOT_FROZEN
max_physical_dispatches: positive integer, NOT_FROZEN
max_pages               : positive integer, NOT_FROZEN
max_retries             : non-negative integer, NOT_FROZEN
max_redirects           : non-negative integer, NOT_FROZEN
max_compressed_bytes    : positive integer, NOT_FROZEN
max_decompressed_bytes  : positive integer, NOT_FROZEN
```

One request-scoped sequential ledger covers `logical_units`, `physical_dispatches`, `pages`,
`documents`, `retries`, `redirects`, `compressed_bytes`, and `decompressed_bytes`. Reservations are
atomic and deterministic:

1. validate caller inputs and capability before cache/network; invalid input consumes no ledger and
   makes zero dispatches;
2. reserve one logical unit before entering the chosen source route set;
3. reserve one physical dispatch immediately before every initial request, page request, retry, or
   redirect request; a failed dispatched attempt remains charged and is never refunded;
4. reserve a page/document before dispatching it; page/document counters are separate from physical
   dispatches and retries;
5. charge compressed bytes as received and decompressed bytes as decoded, before materialization;
6. use one sequential scheduler in provider-declared order; never reset the ledger per page, source,
   calendar segment, or field; and
7. on any exhausted reservation, malformed response, unknown bound, identity conflict, or rights
   uncertainty, discard all private rows and return one bounded terminal outcome. No partial, false
   complete, zero-filled, stitched, or silent-empty result is allowed.

No `diagnostics_truncated` attempt is invented. A diagnostic may mention only a fixed source role,
fixed outcome token, finite sanitized counts, and validated date bounds. It must never expose a raw
provider message, URL/query, header, cookie, body, token, or arbitrary route text.

## 8. Future no-false-absence and outcome contract

These are design-only names, not public API additions:

```text
QUALIFIED_FULL | QUALIFIED_PARTIAL | NOT_SERVED | EMPTY_AUTHORITATIVE
IDENTITY_GAP | SEMANTICS_GAP | CURRENCY_GAP | UNIT_GAP | COVERAGE_GAP
PAGINATION_GAP | REVISION_GAP | TRANSPORT_INCONCLUSIVE | AUTH_REQUIRED
LEGAL_GAP | RATE_POLICY_GAP | BUDGET_EXHAUSTED | SOURCE_FAILED
```

- `NOT_SERVED` requires a response-backed provider declaration that the exact CSI 300 scope is
  outside service. It is never produced from a timeout, missing page, WAF, uncalled route, or local
  validation failure.
- `EMPTY_AUTHORITATIVE` requires request/response identity, provider-declared bounds/totals,
  calendar/non-publication semantics, and complete pagination to reconcile. It is not a zero-value
  series and does not establish historical absence outside the declared bound.
- Unknown bounds, current-only pages, truncated/decompression-failed documents, redirect/final-host
  mismatch, missing identity, response/request mismatch, conflicting revisions, and budget
  exhaustion are terminal gap/failure outcomes.
- Non-trading sessions produce no synthetic row. Missing dates inside a declared eligible range are
  coverage gaps unless the provider explicitly explains them as holidays/suspensions/non-publication.
- An uncalled candidate has no attempt outcome and must not be rendered as `NOT_SERVED`.

## 9. Deferred API/model and RED/release matrix

No API/model name, enum, source registration, warning, exception, public metadata carrier, or RED
test is authorized by this source-gap pass. After a route qualifies, a separate API decision must
preserve the existing ASHR proxy boundary and choose an explicit raw selector/accessor. Only after
that API decision may a reviewer authorize RED-first tests.

| Area | Required future RED/release proof | Current status |
| --- | --- | --- |
| Current boundary | `^CSI300` still loudly returns ASHR/USD/share proxy metadata and warning; no raw CNY result is substituted | Deferred; no change |
| Input/preflight | malformed/blank/bool/reversed dates, non-D1 interval, proxy/ETF/future/return selector, and unsupported alias fail before cache/network | Deferred; no code |
| Identity | response-backed CSI 300 code/name/owner, request-response match, raw price-index versus total/net-return/ETF/future rejection, exchange alias rules | Deferred; no code |
| CNY/points | exact CNY/RMB metadata and `index points` unit; missing/contradictory scale and currency fail | Deferred; no code |
| Session/time | provider China session date/timezone, separate UTC-aware retrieval timestamp, no retrieval-date truncation | Deferred; no code |
| OHLC/value | finite provider values, `low <= open/close <= high`, type/nullability/precision, no booleans/non-finite/negative/synthetic values | Deferred; no code |
| Volume | optional only with same-provider definition, unit, meaning, type, and nullability; no borrowed/zero volume | Deferred; no code |
| Coverage | `2013-01-01` lower bound, current lag, FULL versus declared PARTIAL, eligible sessions, totals/pages/cursors, holidays, gaps, duplicates/conflicts | Deferred; no code |
| Revision | correction/restatement/withdrawal, active revision, publication versus effective/retrieval dates, conflicting document/row identity | Deferred; no code |
| Transport | status, complete MIME after first colon, normalized MIME, redirects/final host, TLS/session/WAF/challenge, bounded attachment/JSON/document handling | Deferred; no code |
| Budget | one global ledger, atomic reservations, sequential pages, retries/redirects/bytes charged, deterministic exhaustion, no fake attempts | Deferred; no code |
| Empty/no absence | authoritative empty versus unknown empty, `NOT_SERVED` only provider-backed, no silent zero or partial | Deferred; no code |
| Atomicity | late page/document failure, identity mismatch, revision conflict, any budget exhaustion discards all rows; no cross-provider/date/field stitch | Deferred; no code |
| Compatibility | existing Vietnam/world index paths, ASHR proxy warning, public snapshots/docs/import/version, and cache identity unchanged | Deferred; no code |
| Release | focused/full offline tests, docs/API/units/skill/CHANGELOG if public API changes, import/version, wheel/sdist, diff/path/object/blacklist/secret/clean-tree gates | Deferred; no code |

Synthetic fixtures may be used only in a later RED-first implementation round after exact source and
API approvals. No live row or provider body is bundled.

## 10. Conjunctive reopen and allowed completion sequence

A fresh source-design review may reopen this gap only when one exact provider route set proves all of
the following together:

1. CSI 300 response identity, raw price-index type, CNY/points, session/time, OHLC/value, optional
   provider-defined volume, correction/revision and non-publication semantics;
2. exact host/path/version/operation, complete status/MIME, redirect/final identity, auth/session/
   UA/WAF posture, pagination/document envelope, and no-login or written automation permission;
3. inclusive `2013-01-01..current-provider-bound` coverage or a provider-declared complete narrower
   bound, with totals/pages/cursors and no unexplained gaps;
4. finite route-specific rate, retry, concurrency, redirect, page, compressed-byte, and
   decompressed-byte policy; and
5. written/published rights for automation, caller return, cache/storage/retention/deletion,
   attribution, commercial/derivative use, redistribution/resale, amendment, and revocation.

An owner factsheet, methodology, current snapshot, generic API schema, timeout, subscription
catalogue, ETF/proxy, constituent basket, or cross-provider agreement cannot reopen the gap.

After exact design PASS the permitted sequence is: rerun merged docs/full/build/blacklist/secret/
diff gates; publish only the approved research/design/backlog paths; verify the exact remote anchor,
base ancestry, exclusions, and paths; post a clean no-capability `SOURCE-GAP` resolution; close and
re-read #232; then record local completion. This packet never authorizes probing, RED, an API/model
decision, source registration, production code, push, or close.

## 11. Primary references

- [CSI 300 official factsheet](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/000300factsheet.pdf)
- [CSI 300 methodology](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/000300_Index_Methodology_cn.pdf)
- [CSI index-detail/download landing](https://www.csindex.com.cn/en/indices/index-detail-download/000300)
- [CSI developer portal getting started](https://uat-apim-developer.csiweb.cloud/GettingStarted)
- [CSI equity-index calculation rules](https://oss-ch.csindex.com.cn/contract/cms_add/20240726155157-Calculation%20Rules%20for%20Equity%20Indices%20of%20China%20Securities%20Index%20Company%20Limited.pdf)
- [SSE historical data products](https://english.sse.com.cn/markets/dataservice/products/)
- [SSE trading rules and market-data ownership clause](https://www.sse.com.cn/lawandrules/sselawsrules/repeal/rules/c/c_20230418_5720138.shtml)
- [CIIS historical-data introduction](https://www.ciis.com.hk/hongkong/en/historicaldata1/his_introduction/index.shtml)
- [CIIS historical-data product manual](https://www.ciis.com.hk/hongkong/en/uploadfiles/202211/07/2022110710413533120137.pdf)
- [SSI FastConnect overview](https://developers.ssi.com.vn/docs/getting-started/overview)
- [SSI FastConnect terms and environments](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
- [SSI official DailyIndex schema](https://fc-data.ssi.com.vn/Help/Api/POST-api-Market-GetDailyIndex)

## Bottom summary

- #232 is a docs-only **SOURCE-GAP CLOSURE**; the raw CSI 300 CNY chain stays empty.
- CSI proves owner identity, points, CNY/RMB metadata, and publication controls, not a reusable no-login history route.
- SSE/CIIS provide official historical-data product leads, but subscription/licensing and exact response semantics remain blocked.
- SSI documents an authenticated generic DailyIndex route; it does not prove CSI 300 identity, OHLC, coverage, or reuse rights.
- Current `^CSI300 -> ASHR` USD/share proxy behavior remains unchanged and must not be relabelled.
- No probe, live row, proxy replacement, RED, API/model, code, push, or close is authorized.
- Reopen requires one exact route set with identity, 2013-current/declared coverage, finite budgets, and written rights.
