# #217 daily CNY/VND history — source vetting

**Date:** 2026-08-23 (UTC+7)
**Packet:** `tasks/217-daily-cnyvnd-fx-history-spec.md` (reviewer packet `4159d74`)
**Requested window:** inclusive `2018-01-01..2026-08-19`
**Decision:** **SOURCE-GAP CLOSURE** — no daily CNY/VND capability, RED tests, production
code, source registration, or source-backed daily API claim is authorized by this report.

The requested economic series is exact `CNY` base / `VND` quote: **VND per 1 CNY**.  A
USD/VND value, a CNY/USD value, a current quote, a bank quote with a different basis, a
midpoint, or a cross-derived value is not a substitute.  The existing annual World Bank
USD/VND behavior remains unchanged.

## 1. Disposition and hard boundary

No investigated unit passes all of the following as one tuple:

```text
owner + exact route/version + direct CNY/VND identity + one provider field/basis
+ VND per 1 CNY scale + requested coverage + date/revision semantics
+ bounded no-auth runtime + lawful automated access/caller return/storage posture
```

Therefore:

- the future daily CNY/VND source chain remains empty (`()`), not merely unconfigured;
- `vnfin.fx.history(..., frequency=Frequency.DAILY)` remains unserved and unchanged;
- no provider is promoted by numerical agreement, cross-rate arithmetic, a facade, a
  current quote, a search result, or an empty response;
- no raw response, live rate, cookie, header, query-bearing URL, or live fixture is
  retained in this repository; and
- a later implementation requires a fresh design/implementation authorization.  This
  report is not a production capability.

## 2. Clean-room and research protocol

Before this task I read `docs/vnstock-blacklist.md`.  Every search used this exclusion:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited source, derivative artifact, endpoint map, schema, code, test, notebook,
package, or behavior was opened, cited, compared, or used.  Evidence below is limited to
owner-operated official portals/APIs, official provider terms, and the repository's
already-reviewed annual FX source notes.  Public reachability is recorded separately from
permission to automate, cache, return, or redistribute data.

The direct probe clock was recorded first as `23/08/2026 - Sunday 16:17:20 +0700`.
Probes used a fresh process, no credentials, no cookie jar, no browser session, no proxy,
IPv4, a 5-second connect timeout, a 15-second total timeout, no automatic retry, and an
explicit desktop User-Agent.  The User-Agent was a normal request header, not challenge
solving or browser automation.  One bounded manual repeat was made for the Vietcombank
2018 date route after a DNS timeout; it is identified as a repeat rather than a hidden
library retry.  Only status, complete MIME, effective host/path, envelope shape, counts,
dates, and legal statements were retained.

Query-bearing date parameters were used only during bounded live probes and are not written
below or committed.  Canonical route references are path-only.

## 3. Bounded probe ledger

The ledger counts direct no-auth HTTP attempts where a route was probed.  A page inspection
from an official portal is marked separately; it is not represented as a successful data
retrieval.  An HTTP 200 with HTML, an empty envelope, a timeout, or a 404 is never treated as
historical absence unless the provider's own product/calendar metadata supplies that meaning.

| Owner/unit | Canonical route (no query) | Bounded observation | Identity/coverage result | Disposition |
| --- | --- | --- | --- | --- |
| Vietcombank dated quote API | [`www.vietcombank.com.vn/api/exchangerates`](https://www.vietcombank.com.vn/api/exchangerates) | 4 direct date attempts: 2018 boundary repeat ended HTTP 200 `application/json; charset=utf-8`, 2026-08-19 ended HTTP 200 with no redirect; one 2020 attempt and the first 2018 attempt timed out during DNS | 2018 response had `Count=0` and an empty `Data`; 2026 response had `Count=20`, `Data` length 20, `Date`, `UpdatedDate`, and one CNY object with `cash`, `transfer`, and `sell` fields. No full-span, unit, rate-policy, or reuse contract | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| Vietcombank XML quote feed | [`portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx`](https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx) | 1 direct HTTP 200, complete MIME `text/xml; charset=utf-8`, no redirect | Root `ExrateList`; 20 `Exrate` nodes; CNY node has provider fields `Buy`, `Transfer`, `Sell`; response is current/spot, not a dated historical series. The response itself says it is for reference only and limits requests to one every five minutes | `BASIS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` |
| Vietcombank public quote page | [`www.vietcombank.com.vn/KHCN/Cong-cu-tien-ich/Ty-gia`](https://www.vietcombank.com.vn/KHCN/Cong-cu-tien-ich/Ty-gia) | 1 official page inspection | Page lists CNY and labels the three columns as cash purchase, transfer purchase, and sale; it says the table is for reference only. These labels do not grant historical automation or select a future field | `BASIS_GAP` + `LEGAL_GAP` |
| State Bank of Vietnam (SBV) rate pages | [`sbv.gov.vn/vi/trang-chu`](https://www.sbv.gov.vn/vi/trang-chu) links to `dttktt.sbv.gov.vn/TyGia/faces/TyGiaSGD.jspx`, `TyGiaCheo.jspx`, and `TyGiaTrungTam.jspx` | 3 direct route attempts, all connection timeouts; official portal navigation to the three routes also timed out | The portal proves that official reference, cross-rate, and central-rate products are separate surfaces. No response-backed CNY/VND row, field, unit, date, page count, calendar, or reuse contract was obtained. The central USD/VND concept cannot be converted into CNY/VND | `TRANSPORT_INCONCLUSIVE` + `IDENTITY_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP`
| PBOC / CFETS | [`pbc.gov.cn` RMB-rate announcement](https://www.pbc.gov.cn/zhengcehuobisi/125207/125217/125925/2025122609114878612/index.html); [`CFETS spot instruments`](https://www.chinamoney.com.cn/english/prdfsmrfs/) | 1 official PBOC announcement inspection and 1 official CFETS product-page inspection | The PBOC announcement identifies PBOC authorization of CFETS and lists its direct RMB parity currencies without VND. CFETS's spot instrument list also omits VND. CFETS states that market-data use requires written authorization | `NOT_SERVED` + `LEGAL_GAP`
| BIS bilateral rates | [`BIS VND/USD page`](https://data.bis.org/topics/XRU/BIS%2CWS_XRU%2C1.0/M.VN.VND.E) and [`BIS documentation`](https://www.bis.org/statistics/xrusd/xrusd_doc.pdf) | 2 bounded API-route probes were made for USD-bilateral daily/monthly keys without credentials; both returned typed 404 XML. The owner data page and documentation were used for semantics, not the failed key as an absence oracle | BIS documents the dataset as nominal rates against USD; the Vietnam page is VND/USD at monthly frequency. ECB-derived or USD-derived arithmetic would violate direct-pair identity | `NOT_SERVED` + `BASIS_GAP`
| ECB reference rates | [`ECB reference-rate roster`](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html); [`ECB CNY page`](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-cny.en.html) | 2 official page inspections; no date fan-out | CNY is listed against EUR; VND is not in the published roster. The rates are information-only working-day reference rates, not a direct CNY/VND product | `NOT_SERVED` + `BASIS_GAP`
| World Bank WDI | [`World Bank WDI API family`](https://api.worldbank.org/v2/country/VNM/indicator/PA.NUS.FCRF) and [`WDI catalogue`](https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators) | 1 direct HTTP 200 JSON probe | `PA.NUS.FCRF` returned six annual observations for the bounded 2020–2025 check and identifies official exchange rate, LCU per US$, period average. It is the existing annual USD/VND source, not daily CNY/VND | `NOT_SERVED` for this request; annual behavior preserved |
| Federal Reserve H.10 / FRED | [`Federal Reserve H.10 current release`](https://www.federalreserve.gov/releases/h10/current/); [`FRED DEXCHUS`](https://fred.stlouisfed.org/series/DEXCHUS) | 1 direct H.10 HTTP 200 HTML probe and 1 official FRED series inspection | H.10 current table had no Vietnam/VND row. FRED's concrete daily CNY series is CNY/USD, not CNY/VND; converting it with another series is forbidden | `NOT_SERVED` + `BASIS_GAP`
| Current open-rate API | [`ExchangeRate-API open endpoint`](https://open.er-api.com/v6/latest/USD) and [`terms`](https://www.exchangerate-api.com/terms) | No history probe; repository source note and provider terms were checked | The no-key endpoint is current/spot only and has no historical retention contract. Its raw-data redistribution restriction independently disqualifies it from a new historical product | `NOT_SERVED` + `LEGAL_GAP`

The failed/empty rows above do not prove that a historical observation never existed. They
only identify what the bounded route could and could not establish. No date-by-date crawl was
attempted.

## 4. Candidate records and source/legal axes

### 4.1 Vietcombank — current CNY identity, but no qualified historical unit

The owner page is useful evidence that Vietcombank currently displays CNY and separates cash
purchase, transfer purchase, and sale. The dated API's response envelope also returned a CNY
object with these three fields for the bounded recent-date probe. This is **not** enough to
choose one historical field:

1. the response has no explicit machine-readable `base`, `quote`, scale, or economic-basis
   contract;
2. the page's labels establish bank-side transaction direction, but do not establish a
   stable `VND per 1 CNY` historical series, publication time, or revision policy;
3. the 2018 response is an empty envelope with zero placeholder dates. It is not a proof of
   no historical data, and the 2020 timeout is transport-unknown;
4. the API's request/rate policy, retention, pagination/bulk behavior, and automation rights
   are not published in the inspected owner materials; and
5. the XML route is current/spot only. Its provider comment says “for reference only” and
   “only one request every five minutes”; that statement is not silently transferred to the
   dated API.

The three bank fields are mutually exclusive qualification bases. A future implementation
must select exactly one only after the same provider route and written provider semantics
prove direction, unit, date, scale, revisions, and legal/runtime rights. It must never average
the fields into a midpoint or use the XML spot route to fill the dated API.

**Legal axes recorded independently:**

| Axis | Observed VCB posture | Required before qualification |
| --- | --- | --- |
| Owner/source identity | Vietcombank owner pages and hosts | Keep exact owner route and stable provider token |
| Automated access | Public route reachable in some probes; no automation grant found | Written owner permission or explicit terms for the exact route and request pattern |
| Caller-facing return | Not granted by “for reference only” | Explicit permission to return normalized historical observations |
| Storage/cache | Not stated for the dated API | Explicit retention/cache permission and duration |
| Redistribution/commercial | Not stated | Explicit permission or licence covering the library's use and downstream context |
| Attribution | Not stated beyond owner branding | Exact attribution requirement |
| Rate/retry | XML says one request per five minutes; dated API is unknown | Route-specific request budget, retry, and WAF policy |
| Revisions/publication | `Date`/`UpdatedDate` exist in one response but semantics are unproven | Provider-defined observation date, publication/update, and revision behavior |

Overall VCB is not `PARTIAL`: the response-backed CNY row is useful discovery evidence, but
identity/basis, full historical coverage, and legal/runtime axes are not a qualification unit.

### 4.2 SBV — official rate surfaces, no response-backed CNY/VND proof

The SBV official home page separates: central rate, reference rates at the Foreign Exchange
Management Department, and VND cross rates for tax calculation. The linked routes are kept as
independent candidates:

- `https://dttktt.sbv.gov.vn/TyGia/faces/TyGiaTrungTam.jspx`
- `https://dttktt.sbv.gov.vn/TyGia/faces/TyGiaSGD.jspx`
- `https://dttktt.sbv.gov.vn/TyGia/faces/TyGiaCheo.jspx`

All three direct route attempts timed out before a response. Consequently this report does
not assert a JSON/XML schema, CNY row, unit, scale, effective date, pagination, historical
retention, or count. The official central-rate USD/VND concept is a wrong-basis boundary for
this task; no conversion through it is allowed. A cross-rate page or a reference page would
need a fresh response-backed direct CNY/VND product before it could be considered.

SBV's publication role establishes ownership, not a licence for automated retrieval, caching,
caller-facing return, redistribution, rate, or retry. Those rights remain `LEGAL_GAP` until
the owner documents them or grants written permission.

### 4.3 PBOC / CFETS — no public direct pair and explicit data-licence gate

The official PBOC announcement says PBOC authorizes CFETS to publish RMB central parity and
lists the currencies in that announcement; VND is not present. The official CFETS spot-product
page lists the supported RMB/FX instruments and also omits VND. These observations dispose of
the public direct-pair candidate as `NOT_SERVED`; they do not authorize a guessed instrument,
hidden endpoint, or regional-pair substitution.

CFETS's [market-data service terms](https://www.chinamoney.com.cn/english/svcmds/) state that
an institution or individual needs written CFETS authorization and may not copy, transmit,
save, use, publish, sell, or process CFETS market data without that permission. A no-login
page is therefore not a lawful reusable source for this library. Even written permission would
still need exact CNY/VND identity, date/scale/coverage, and bounded API evidence; it would not
make a CNY/USD or other pair qualify.

### 4.4 BIS — direct USD bilateral data is not direct CNY/VND

BIS documents its nominal bilateral exchange-rate data as rates against USD and explains that
some series are calculated from national-currency/EUR and EUR/USD cross rates. The official
Vietnam page is a VND/USD page at monthly frequency. This is a wrong frequency/basis and,
where cross-calculated, a wrong direct-identity model for #217. BIS terms may permit reuse with
attribution and restrictions, but a permissive legal posture cannot repair the missing direct
CNY/VND unit.

### 4.5 ECB / Frankfurter — CNY exists, VND and direct pair do not

The ECB roster is explicitly EUR-base and lists CNY but not VND. The CNY page exposes a
working-day EUR/CNY reference series and an SDMX download, not CNY/VND. ECB's information-only
reference-rate language and working-day calendar do not establish a VND daily series or
same-day availability. Frankfurter is a consumer facade over reference data; it cannot become
the owner, direct-pair identity, retention contract, or licence oracle. No ECB/Frankfurter
cross-rate is used.

### 4.6 World Bank — preserve annual USD/VND only

The official WDI indicator `PA.NUS.FCRF` is annual official exchange rate in local currency
per US dollar, period average. It is the existing `vnfin.fx.history()` source and remains
untouched. It cannot be stamped daily, converted into CNY/VND, or used as a fallback for the
new request. Its public WDI terms/attribution do not change this frequency and pair boundary.

### 4.7 H.10 / FRED / current open endpoints

The Federal Reserve H.10 current release does not list Vietnam/VND. FRED's concrete daily CNY
series is CNY/USD and identifies H.10 as its source; it is not a direct CNY/VND series.
No arithmetic combination of these datasets is permitted.

The repository's existing open.er-api source note records a no-key current/spot endpoint,
approximately daily refresh, no historical endpoint, and provider terms prohibiting raw-data
redistribution. It remains a spot source only. A current quote cannot prove historical
retention or fill any date in the requested span.

## 5. Exact future retrieval and coverage contract

This section is a design boundary for a future, separately authorized implementation. It does
not change current runtime behavior.

### 5.1 Qualification unit and direct identity

One unit is exactly:

```text
provider_token
+ canonical route/version (query template excluded from public provenance)
+ response-backed base=CNY and quote=VND
+ one provider-observed numeric field and one economic basis token
+ provider reference-date convention and revision convention
+ one scale proven by owner response/documentation
+ one coverage/calendar contract and one legal/runtime contract
```

The normalized value must be **VND per 1 CNY**. A provider value quoted per 100 CNY may be
divided by 100 only when the same owner response/documentation proves that scale; ambiguous
scale is `BASIS_GAP`, never a guessed normalization. Reversed direction, CNY/USD, USD/VND,
EUR/CNY, a central-rate conversion, a midpoint, and any stitched cross are rejected.

The provider basis must be a finite closed token, not free text. Candidate tokens are
illustrative only and are not published now; examples include `bank_transfer_buy` or
`official_daily_central_parity` only if a future owner response proves the exact meaning.

### 5.2 Coverage accounting

Full qualification is for the literal inclusive bounds `2018-01-01..2026-08-19`.

- Input bounds are plain `datetime.date` values and are validated before network.
- Returned observations are provider observations, ascending, unique, finite, positive,
  non-boolean, inside the requested bounds, and never forward-filled, backfilled,
  interpolated, resampled, or nearest-matched.
- A provider-declared weekend/holiday non-publication may explain a missing calendar date
  only when the same provider supplies the calendar/status evidence. A nearest business day
  is never silently substituted.
- Every page/cursor is successful and accounted for. A page that returns no rows before its
  provider count/page/cursor ledger is reconciled is `COVERAGE_UNKNOWN`/`COVERAGE_GAP`, not a
  successful empty page. A truncated or unreconciled page fails the entire retrieval.
- A `FULL` result requires provider total = reconciled row total, distinct-date count = row
  count, no unexplained internal gaps, observed bounds covering the requested contract, and
  an explicit revision/update rule.
- `PARTIAL` is allowed only for a single independently qualified unit whose provider-declared
  observed bounds and page reconciliation pass. Its diagnostics must expose exact observed
  bounds and must not call the requested full span complete.
- An empty response is a typed unknown/transport/coverage outcome unless provider metadata
  explicitly declares non-publication. It is never a false-absence oracle.

### 5.3 Global deterministic budget

The future request owns one ledger; per-source budgets are not additive and cannot reset the
global budget. The exact finite ceilings are:

| Counter | Ceiling | Rule |
| --- | ---: | --- |
| logical source attempts | 4 | deterministic candidate order; capability skips consume zero |
| logical page/cursor dispatches | 64 | one reservation per page/cursor; no per-day fan-out |
| total retry reservations | 32 | at most one retry for a given page/cursor |
| physical HTTP calls | 96 | every initial/retry call reserves one unit before dispatch |
| redirect hops | 0 | a 3xx response is a typed transport failure; no host change or follow |
| response body bytes | 64 MiB total and 8 MiB per response | bounded streaming/decompression; overflow fails closed |

The scheduler is sequential and deterministic. Each reservation atomically checks and updates
the global tuple `(source_attempts, page_dispatches, retries, physical_calls, response_bytes_total)`.
If any check fails, it returns `FX_CALL_BUDGET_GAP` and performs no HTTP call. A retry reserves
both its page identity and its retry slot; it cannot be created after exhaustion. A capability
skip records no attempt and no call. HTTP status, complete MIME, redirect, WAF/HTML, parse,
and body-size failures consume the reservation actually dispatched. Budget exhaustion returns
no partial `FXHistory` and is never reported as provider absence. The library must not claim a
numeric delay/rate policy unless the provider supplies one; an unknown provider rate policy is
`FX_RATE_POLICY_GAP`, not an invented sleep.

Each dispatched page/cursor has one ledger row containing only typed fields:
`provider_token`, logical page/cursor, retry index, dispatch status, complete MIME, row count,
and provider total/page/cursor metadata. The row is reserved before dispatch and finalized
once; a retry uses the same logical page with retry index one. Missing, duplicate, or
unreconciled rows fail the source attempt as a whole. No later source may reuse those rows.

### 5.4 Status axes and sanitized diagnostics

Coverage, attempt, and transport are separate axes. They must not be collapsed into a single
empty result:

```text
coverage_status = FULL | PARTIAL | UNKNOWN | NOT_SERVED
attempt_status  = SKIPPED | STARTED | SUCCEEDED | FAILED | BUDGET_EXHAUSTED
transport_status = NOT_RUN | SUCCESS | TIMEOUT | HTTP_ERROR | MIME_ERROR | REDIRECT
                  | BODY_LIMIT | PARSE_ERROR | WAF_OR_HTML
```

Only HTTP 200 with an exact allow-listed complete MIME can be a successful data response.
Every 3xx (redirect disabled), 204, 4xx, and 5xx response is `FX_HTTP_STATUS_UNEXPECTED`;
it is never an empty successful page. DNS, connection, TLS, and timeout failures map to the
single finite offline token `FX_OFFLINE`. HTML/challenge/WAF bodies map to `FX_WAF_OR_HTML`;
a complete MIME mismatch maps to `FX_MIME_MISMATCH`. No raw status code, response body, or
exception text is public.

The closed public error tokens are:

```text
FX_UNSUPPORTED_PAIR
FX_UNSUPPORTED_FREQUENCY
FX_SOURCE_GAP
FX_IDENTITY_GAP
FX_BASIS_GAP
FX_COVERAGE_GAP
FX_COVERAGE_UNKNOWN
FX_TRANSPORT_INCONCLUSIVE
FX_OFFLINE
FX_HTTP_STATUS_UNEXPECTED
FX_MIME_MISMATCH
FX_WAF_OR_HTML
FX_RESPONSE_INVALID
FX_BODY_LIMIT
FX_CALL_BUDGET_GAP
FX_RATE_POLICY_GAP
FX_LEGAL_GAP
```

The closed warning tokens are finite and non-sensitive:

```text
FX_PARTIAL_PROVIDER_BOUNDS
FX_PROVIDER_NONPUBLICATION
FX_REVISION_POSSIBLE
FX_RETRIEVAL_TIME_ONLY
```

Diagnostics may expose only typed tokens, canonical provider tokens, integer counts, plain
ISO dates, exact coverage statuses, and UTC retrieval time. They must not expose URLs/query
strings, response text, headers, cookies, credentials, raw exceptions, live rates, or provider
prose. An attempt record, if added later, must use the canonical provider token rather than
the route URL and must be emitted only for a real reserved dispatch; no fabricated “empty
attempt” or “diagnostics truncated” attempt is allowed.

## 6. Conjunctive reopen evidence

The source gap can be reopened only when **all** gates below pass for one same provider/route/
basis unit. Evidence from different providers cannot be combined.

1. **Owner response and transport:** a no-login owner response is obtained with complete
   `Content-Type` parsed after the first colon; the normalized MIME is an exact allow-list
   member; HTML/WAF/challenge/redirect/truncated body is rejected.
2. **Direct identity and basis:** the response and owner documentation prove `CNY` base,
   `VND` quote, VND per 1 CNY direction, one selected field/basis, scale, date convention,
   and revision semantics without a cross-rate or midpoint.
3. **Coverage:** the requested inclusive bounds are covered or the provider-declared bounded
   `PARTIAL` contract is independently useful; counts/pages/cursors reconcile; rows are
   distinct and complete; provider calendar/status explains any non-publication; no empty or
   unreconciled page is treated as absence.
4. **Runtime budget/rate:** provider API pagination, rate, retry, body, and WAF policy is
   documented and fits the single atomic global ledger above; no date fan-out is needed.
5. **Legal/reuse:** written permission or an explicit licence covers automated access,
   caller-facing return, storage/cache, redistribution, attribution, commercial use, and
   rate/retry behavior. Public access alone is insufficient.
6. **Compatibility:** a later implementation plan preserves annual USD/VND byte compatibility,
   rejects unsupported pairs/frequencies before network, carries one typed basis, preserves
   exact observation dates, and emits sanitized diagnostics. A fresh RED-first implementation
   review is still required after this design gate.

Until all six are demonstrated, the chain remains empty and the disposition remains
`SOURCE-GAP CLOSURE`.

## 7. Sources

- [SBV official home and rate menu](https://www.sbv.gov.vn/vi/trang-chu)
- [Vietcombank rate page](https://www.vietcombank.com.vn/KHCN/Cong-cu-tien-ich/Ty-gia)
- [Vietcombank XML route](https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx)
- [PBOC/CFETS RMB parity announcement](https://www.pbc.gov.cn/zhengcehuobisi/125207/125217/125925/2025122609114878612/index.html)
- [CFETS RMB/FX spot instruments](https://www.chinamoney.com.cn/english/prdfsmrfs/)
- [CFETS market-data service and written-licence terms](https://www.chinamoney.com.cn/english/svcmds/)
- [BIS Vietnam VND/USD data page](https://data.bis.org/topics/XRU/BIS%2CWS_XRU%2C1.0/M.VN.VND.E)
- [BIS USD bilateral-rate documentation](https://www.bis.org/statistics/xrusd/xrusd_doc.pdf)
- [BIS permitted-use/API terms](https://data.bis.org/help/legal)
- [ECB reference-rate roster](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
- [World Bank WDI catalogue](https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators)
- [Federal Reserve H.10](https://www.federalreserve.gov/releases/h10/current/)
- [FRED CNY/USD series](https://fred.stlouisfed.org/series/DEXCHUS)
