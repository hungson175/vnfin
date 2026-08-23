# Source vetting — annual ROE ratio history

**Date:** 2026-08-23 (UTC+7)  
**Issue:** #220  
**Packet:** `tasks/220-annual-roe-ratio-history-spec.md` at reviewer anchor
`314cd53b4a7f3a0c36f6a1bb45efed2611733f4a`  
**Phase:** `SOURCE_DESIGN` / documentation only  
**Disposition:** **SOURCE-GAP CLOSURE**  
**New source chain:** empty  
**Runtime status:** unchanged; no ROE mapping, cadence change, parser, failover, model, RED test,
API, or coverage capability is authorized.

This report is a design/source record, not an assertion that any candidate is qualified. The requested
annual ROE contract remains blocked until one owner unit proves every identity, cadence, coverage,
runtime, and legal axis together.

## 1. Clean-room and scope boundary

`docs/vnstock-blacklist.md` was read before this research task. Every search and source review applied
this exclusion:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited or derivative material was opened, cited, compared, installed, imported, or used. Only
official provider, exchange, regulator, developer, and investor-relations sources were considered.
The reporter's external raw artifact and digest were not opened, copied, hashed, verified, cited, or
used as a source, coverage, retention, or failure oracle.

The current public call is deliberately preserved:

```python
vnfin.fundamentals.client().get_financials(
    symbol, StatementType.RATIOS, Period.ANNUAL, limit=8
) -> tuple[FinancialReport, ...]
```

Current VNDirect and CafeF ratio reports use `Period.UNKNOWN`, because their ratio responses are
keyed by a provider date/report object without a response-backed annual fiscal-period contract. That
truth must not be relabeled. The separate 26-metric API continues to make zero ratio calls and keeps
ROE/ROA/ROIC blocked. No ratio is derived from net income/equity, and no current, TTM, request-echo,
quarterly, proxy, or third-party value is substituted.

## 2. Decision summary

No investigated unit qualifies for TDD:

| Candidate unit | What is response-backed | Blocking axes | Disposition |
|---|---|---|---|
| VNDirect `/v4/ratios`, corporate and bank symbol families | Provider symbol, `ratioCode`, `itemCode`, `reportDate`, numeric row shape | No annual request/response marker; `reportDate` is not proven fiscal-year end; definition/scale/revision and redistribution rights are not established | `SOURCE-GAP` |
| CafeF `GetDataChiSoTaiChinh.ashx`, corporate and bank symbol families | `Data.Value` period objects expose `Time`, `Year`, `Quater`, `ReportType`, and ratio lines | Request `ReportType=NAM` is not response identity; current runtime intentionally returns `Period.UNKNOWN`; null/absent cadence fields are tolerated; exact ROE definition/scale/revision and redistribution rights are not established | `SOURCE-GAP` |
| SSI FastConnect / iBoard family | Official API documentation and official financial-report archive | API access is account/API-key controlled; official archive is SSI's own reports, not a broad machine-readable annual-ROE route; no no-login VN30 history or redistribution grant | `SOURCE-GAP` |
| TCBS / TCInvest family | Official TCInvest page explains ROE and official OpenAPI documentation exists | Dashboard is JavaScript/WAF gated in the bounded probe; OpenAPI requires API key plus OTP/JWT; no public annual ROE route/schema/cadence/reuse contract | `SOURCE-GAP` |
| Official exchange/issuer filings | Annual audited documents can establish an issuer's reported statements in a document | Not a single provider-published, multi-symbol ROE series; extracting or deriving a ratio is outside the requested source unit; no uniform route, pagination, revision, or redistribution contract | `SOURCE-GAP` |

The result is not “no values exist.” It is that no single owner + exact route + exact ROE code and
scale + annual fiscal identity + coverage + legal/runtime contract was proven. The source chain stays
empty and current behavior stays unchanged.

## 3. Qualification unit and axes

A source can qualify only as this complete unit:

```text
owner + canonical route/version + exact ROE code/definition/scale
+ annual cadence and fiscal-date/publication/revision semantics
+ symbol/template coverage + bounded runtime + written reuse rights
```

The gate is conjunctive:

1. **Transport:** owner host/path, method, status, complete and normalized MIME, redirect/effective
   route, auth/session/UA/WAF behavior, bounded bytes, and a finite request/page/retry ledger.
2. **Response identity:** requested symbol, exact ROE item/code, numerator/denominator convention,
   annual fiscal period, fiscal-period end date, and revision/as-of identity are response-backed.
3. **Semantics:** percentage versus fraction, average versus ending equity, attributable versus total
   profit, consolidated versus separate entity, preliminary/audited/revised status, and nullability
   are explicit. A label `ROE` alone is insufficient.
4. **Coverage:** provider-declared bounds, eight distinct complete annual reports, pagination/count/
   cursor reconciliation, gaps, duplicates/conflicts, and current corporate/bank/template diversity.
5. **Legal/runtime:** rate and retry policy, automation permission, cache/storage/retention,
   attribution, commercial use, derivative use, and redistribution rights for the exact data.
6. **Atomic failure:** malformed identity, wrong cadence/date/unit, missing ROE, unresolved page,
   budget, legal, and transport errors do not yield a partial or false-empty success.

A request parameter such as `ReportType=NAM`, a page title, a current snapshot, a date inferred from
retrieval time, or a statement from an unrelated issuer cannot satisfy response identity.

## 4. Dated bounded observations

The following observations were made on 2026-08-23 using no credentials and a browser-like User-Agent
where a provider route was probed. The bodies were discarded after bounded envelope/key inspection;
no values, raw rows, response digests, cookies, credentials, or query-bearing URLs are committed.
A physical dispatch means one HTTP request. The byte count below is an observation only, not a future
library ceiling. `NOT_RETAINED` means the field was not preserved and cannot be used as evidence.

| Unit | Retained observation | Identity/cadence result | Legal/runtime result | Outcome |
|---|---|---|---|---|
| VNDirect ratio route, corporate cohort | 1 logical / 1 physical; HTTP 200; normalized MIME `application/json`; JSON envelope keys `data`, `currentPage`, `size`, `totalElements`, `totalPages`; first row exposed `reportDate` and `ratioCode` | No `reportType`, fiscal-period, annual, revision, or publication field was retained | Browser-like UA was used; no written automation or redistribution grant for this route was found | `IDENTITY_GAP` + `LEGAL_GAP` |
| VNDirect ratio route, bank cohort | 1 logical / 1 physical; same envelope/key shape | Same missing annual identity; bank/corporate template is not encoded as a ratio cadence contract | Same legal/runtime gap | `IDENTITY_GAP` + `LEGAL_GAP` |
| CafeF ratio route, corporate cohort | 1 logical / 1 physical; HTTP 200; JSON body with `text/plain; charset=utf-8` MIME; envelope keys `Data`, `Message`, `Success`; first period exposed `Time`, `Year`, `Quater`, `ReportType`, `Value`, `Conten` | Field presence does not prove value semantics; current adapter must tolerate present-null/absent `ReportType` and returns `Period.UNKNOWN` | Browser-like UA was used; no exact-value redistribution grant was found | `IDENTITY_GAP` + `LEGAL_GAP` |
| CafeF ratio route, bank cohort | 1 logical / 1 physical; same envelope/key shape | Same request-selector versus response-identity gap; no stable annual fiscal/revision contract | Same legal/runtime gap | `IDENTITY_GAP` + `LEGAL_GAP` |
| TCInvest public dashboard | 1 logical / 1 physical; HTTP 403; HTML MIME; no JSON schema retained | JavaScript/WAF page is not a response-backed annual ROE route | No anonymous machine-readable contract | `TRANSPORT_FAILURE` |
| TCBS official OpenAPI landing page | 1 logical / 1 physical; HTTP 200 HTML | Official documentation describes market/trading access, not a public annual ROE history schema | API key plus OTP/JWT is required; access is not no-login | `AUTH_GAP` |
| SSI developer documentation | Official documentation page reachable; API key/secret -> bearer-token flow is documented | No anonymous annual ROE response/schema | Account/API credentials and provider access level control fundamental information | `AUTH_GAP` |

The probe table is deliberately not a coverage claim. It records transport and shape only; no raw
provider value is committed. The two symbol cohorts are count-only corporate/bank template checks,
not a hard-coded runtime basket and not proof of current VN30 membership.

## 5. Candidate evidence

### 5.1 VNDirect

**Canonical owner routes**

- Ratio route: [`api-finfo.vndirect.com.vn/v4/ratios`](https://api-finfo.vndirect.com.vn/v4/ratios)
- Official financial-information archive: [`vndirect.com.vn/danh_muc_bao_cao/thong-tin-tai-chinh/`](https://www.vndirect.com.vn/danh_muc_bao_cao/thong-tin-tai-chinh/)
- Official application terms: [`vndirect.com.vn/dieu-khoan-su-dung/`](https://www.vndirect.com.vn/dieu-khoan-su-dung/)

The current clean-room adapter sends a symbol filter and receives rows keyed by `code`,
`ratioCode`, `itemCode`, `itemName`, `value`, and `reportDate`. The route has no request-side
annual/quarter selector in the current adapter contract. `reportDate` is a provider date field,
not proof that the row is an annual fiscal period end, and the route does not expose a retained
annual cadence marker, fiscal-date/publication distinction, vintage/revision identifier, or ROE
numerator/denominator definition in the observed envelope.

The label `ROE` and a finite number are therefore insufficient. A future qualified route would need
owner evidence that the code means annual ROE, whether the scale is percent or fraction, whether
profit is attributable or total, and whether equity is average or ending equity. It would also need
an exact eight-period history with provider bounds and page reconciliation. The official archive
shows VNDIRECT publishes annual financial documents, but an issuer's document archive does not prove
that the anonymous ratio route serves the same annual identity or grants OSS redistribution of its
ratio rows.

**Verdict:** `SOURCE-GAP`. Do not change the existing `Period.UNKNOWN` ratio behavior.

### 5.2 CafeF

**Canonical owner routes**

- Ratio route: [`cafef.vn/du-lieu/Ajax/PageNew/GetDataChiSoTaiChinh.ashx`](https://cafef.vn/du-lieu/Ajax/PageNew/GetDataChiSoTaiChinh.ashx)
- Official data-tool guide: [`cafef.vn/du-lieu/huong-dan-su-dung.chn`](https://cafef.vn/du-lieu/huong-dan-su-dung.chn)
- Official financial-data area: [`cafef.vn/du-lieu/BaoCaoTaiChinh_V2.aspx`](https://cafef.vn/du-lieu/BaoCaoTaiChinh_V2.aspx)

The route accepts request-side selectors for symbol, row count, end-date anchor, report type, and
sort direction. A bounded response exposed period objects with `Time`, `Year`, `Quater`,
`ReportType`, `Conten`, and ratio `Value` lines. That is useful shape evidence but does not prove
that a request-side `NAM` selector means every returned ROE line is an annual provider fiscal
period. The existing adapter intentionally treats ratio cadence as unknown: a descriptive
`ReportType` can be absent or null, a current snapshot date can be mistaken for a fiscal date, and
the public result is `Period.UNKNOWN`.

CafeF's official guide explains that its data tools include ROE and downloadable company data, but it
does not provide an OSS/commercial redistribution grant for the exact machine route. No stable
revision/as-of contract, exact average/ending-equity definition, or eight-period annual completeness
contract was found. Corporate and bank response shapes must be evaluated separately; a route that
returns a row for one template cannot be assumed to qualify the other.

**Verdict:** `SOURCE-GAP`. The route is not an annual-ROE source merely because the request contains
`ReportType=NAM`.

### 5.3 SSI

**Canonical owner routes**

- SSI developer overview: [`developers.ssi.com.vn/docs/getting-started/overview`](https://developers.ssi.com.vn/docs/getting-started/overview)
- Legacy FC API help: [`fc-data.ssi.com.vn/Help`](https://fc-data.ssi.com.vn/Help)
- Official financial-report archive: [`ssi.com.vn/en/investor-relation/financial-report`](https://www.ssi.com.vn/en/investor-relation/financial-report)
- Official terms: [`ssi.com.vn/en/terms-of-services`](https://www.ssi.com.vn/en/terms-of-services)

SSI's official developer material requires an API key and secret to obtain a bearer token and says
fundamental-information access depends on the customer's accessibility level. That is not a
no-login public route. SSI's public investor-relations archive is official and useful for issuer
filing provenance, but it is not a broad response-backed annual ROE API for the requested symbol
cohort. SSI's terms permit storage/analysis for one's own use and prohibit publishing or reproducing
the information to third parties without express written consent. That is incompatible with an OSS
runtime redistribution posture absent written permission.

**Verdict:** `SOURCE-GAP` / `AUTH_GAP` / `REDISTRIBUTION_GAP`.

### 5.4 TCBS / TCInvest

**Canonical owner routes**

- TCBS OpenAPI landing page: [`developers.tcbs.com.vn`](https://developers.tcbs.com.vn/)
- TCInvest analysis page: [`tcinvest.tcbs.com.vn/tc-analysis/dashboard`](https://tcinvest.tcbs.com.vn/tc-analysis/dashboard)
- Official TCBS annual-report page: [`tcbs.com.vn/quan-he-nha-dau-tu/bao-cao-tai-chinh/cbtt-ve-bao-cao-tai-chinh-va-bao-cao-ty-le-an-toan-tai-chinh-nam-2025-da-duoc-kiem-toan/`](https://www.tcbs.com.vn/quan-he-nha-dau-tu/bao-cao-tai-chinh/cbtt-ve-bao-cao-tai-chinh-va-bao-cao-ty-le-an-toan-tai-chinh-nam-2025-da-duoc-kiem-toan/)

The official TCInvest page describes ROE conceptually, but the bounded direct page request returned
HTTP 403 HTML and the browser-readable page requires JavaScript. TCBS OpenAPI documentation
requires an API key and OTP exchange for a JWT; it does not document an anonymous annual ROE
history route, provider code, fiscal-date field, pagination, or reuse grant. Issuer annual reports
are not a substitute for a multi-symbol ratio route and deriving ROE from statements is explicitly
out of scope.

**Verdict:** `SOURCE-GAP` / `AUTH_GAP` / `IDENTITY_GAP`.

### 5.5 Official exchange and issuer documents

HOSE's [VN30 index ground rules](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15ff11e799483abd11677ad0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf)
define VN30 as 30 constituents selected under the official index rules. HOSE's [index-data page](https://www.hsx.vn/vi/du-lieu-giao-dich/quy-mo-giao-dich/bo-chi-so)
exposes a VN30 data area, but the bounded public page did not provide a retained dated current
constituent snapshot suitable for a reproducible 2026-08-23 membership claim. The coverage axis is
therefore `UNKNOWN`, not `FULL`.

The official issuer/VNX disclosure route can prove that an individual annual filing exists. It does
not provide one owner unit with a common ROE code/definition/scale, eight-period pagination, revision
semantics, and lawful redistribution for all symbols. Parsing a filing or computing ROE from profit
and equity would be a different source/derivation project and is not allowed here.

## 6. Twelve-cell source matrix

Each row is a separate provider + route + template/identity unit. `UNKNOWN` is not a pass.

| Cell | Owner/route | Template | Code/identity | Annual fiscal/date | Coverage/runtime | Rights | Total |
|---|---|---|---|---|---|---|---|
| VND-01 | VNDirect `/v4/ratios` | corporate | `ratioCode`/`itemCode` and symbol observed; no annual marker | `UNKNOWN` (`reportDate` only) | shape reachable; pages/totals observed but annual rows unreconciled | no exact-route grant | `SOURCE-GAP` |
| VND-02 | VNDirect `/v4/ratios` | bank | same | `UNKNOWN` | same | same | `SOURCE-GAP` |
| VND-03 | VNDirect `/v4/ratios/latest` | corporate | route family is current/latest summary, not a retained annual history | `UNKNOWN` | no full-history contract | no grant | `SOURCE-GAP` |
| VND-04 | VNDirect `/v4/ratios/latest` | bank | same | `UNKNOWN` | no full-history contract | no grant | `SOURCE-GAP` |
| CFE-01 | CafeF `GetDataChiSoTaiChinh.ashx` | corporate | `Time`/`Year`/`Quater`/`ReportType` field shape observed | request selector not identity; null/absent tag possible | JSON shape reachable; count/revision bounds not proven | no exact-route grant | `SOURCE-GAP` |
| CFE-02 | CafeF `GetDataChiSoTaiChinh.ashx` | bank | same field shape, template behavior independent | same | same | same | `SOURCE-GAP` |
| CFE-03 | CafeF company annual data page | corporate | human-readable annual table, not ratio API identity | page labels do not bind machine ROE row | no bounded page/cursor API contract | no grant | `SOURCE-GAP` |
| CFE-04 | CafeF company annual data page | bank | human-readable annual table, not ratio API identity | same | same | same | `SOURCE-GAP` |
| SSI-01 | SSI FastConnect | market/fundamentals access | API key/secret and customer access level | no public annual ROE schema | no-login route absent | own-use terms; written consent required for redistribution | `SOURCE-GAP` |
| SSI-02 | SSI investor-relations archive | SSI issuer | annual reports are documents, not a multi-symbol ROE code | document fiscal period is not API identity | no common machine history | terms restrict third-party reproduction | `SOURCE-GAP` |
| TCX-01 | TCInvest analysis dashboard | corporate/bank UI | ROE explanation/UI only; no retained JSON identity | no response-backed annual field | direct bounded request 403; JS/WAF | no public reuse grant | `SOURCE-GAP` |
| TCX-02 | TCBS OpenAPI | API consumer | API documentation, no annual ROE route | no schema | API key + OTP/JWT | account/API terms not OSS redistribution | `SOURCE-GAP` |

No matrix cell passes all columns. The cells are not failover candidates and must not be combined.

## 7. Coverage and current-VN30 evidence

The HOSE ground rules establish the index universe as 30 constituents, but the dated current
membership snapshot was not retained from the public page. A bounded count-only diversity check
used two corporate-template and two bank-template cases against the two no-login provider route
families:

| Evidence unit | Count-only result | What it proves | What remains unknown |
|---|---:|---|---|
| VNDirect ratio route | 2 corporate + 2 bank transport responses | route shape exists for both template families | no current-VN30 membership, annual cadence, eight-period completeness, or rights |
| CafeF ratio route | 2 corporate + 2 bank transport responses | route envelope/period shape exists for both template families | no current-VN30 membership, annual cadence, revision, or rights |
| HOSE public VN30 universe | 30 constituents under official rules | index definition/count | dated 2026-08-23 symbol list and provider crosswalk were not retained |

Therefore the provider coverage result is `UNKNOWN`, not `FULL`, `PARTIAL`, or `EMPTY`. No hard-coded
VN30 list, source value, or runtime basket is added. A future reopen must retain a dated official
membership snapshot as count-only evidence plus exact response-backed symbol identity for each
sampled corporate/bank/template cell, without shipping the basket in the API.

## 8. Legal and runtime posture

| Candidate | Auth/automation | Rate/retry | Storage/retention | Redistribution | Decision |
|---|---|---|---|---|---|
| VNDirect | Browser-like UA was sufficient for bounded observation; automation permission not stated | No exact public route policy retained | no written cache/retention policy for ratio route | no OSS/commercial grant found | `LEGAL_GAP` |
| CafeF | No credential on bounded route observation; automation policy not stated | no exact route policy retained | no written cache/retention policy for ratio route | no OSS/commercial grant found | `LEGAL_GAP` |
| SSI | API key/secret or account-level access | provider-controlled | official terms govern | own-use only; third-party publication/reproduction requires written consent | `REDISTRIBUTION_GAP` |
| TCBS | API key + OTP/JWT for OpenAPI; dashboard 403 in bounded request | documentation recommends operational limits but not a public annual ROE licence | no exact annual-ROE retention terms | no exact redistribution grant | `AUTH/LEGAL_GAP` |
| HOSE/issuer documents | public viewing/download varies by document | no machine route contract | document terms/rights not an OSS data licence | no exact rights for extracted ROE series | `LEGAL_GAP` |

Robots visibility, public HTML, or a successful GET is not a redistribution licence. No candidate is
lawful to cache, repackage, or expose through a new public OSS data API on the evidence retained here.

## 9. Future contract if a source reopens qualification

This section is design-only and authorizes no implementation. Preserve the existing call shape. A
qualified source must return at most `limit` complete, distinct, newest-first reports where every
report has:

- `statement_type=RATIOS`, `period=Period.ANNUAL`, and provider fiscal-period-end `fiscal_date`;
- exactly one finite, non-boolean dimensionless line with canonical `item_code="ROE"`;
- `currency=None`, `value_unit="ratio"`, exact percent/fraction scale provenance, and no silent
  multiply/divide by 100;
- response-backed `symbol`, provider symbol, source, UTC retrieval time, bounded warnings, and
  revision/as-of metadata where provided; and
- no current snapshot, TTM, average-equity proxy, ROA/ROIC/margin, statement-derived ROE, or
  inferred Dec 31 date.

A provider code other than `ROE` qualifies only after owner documentation proves the identical
annual definition and the design binds the provider code to canonical `ROE`. A negative or zero ROE
is valid when the owner definition permits it; bool, non-finite, malformed, ambiguous-scale, wrong
unit, duplicate, or conflicting values fail closed.

One source supplies the whole request. No source stitches periods, repairs a missing ROE row, or
falls back for a partial accumulator. Capability skips consume no dispatch. A current/TTM or
cadence-unknown source is skipped or fails typed; it is never relabeled as annual.

## 10. Finite outcomes and no-false-absence diagnostics

The following vocabulary is internal design-only until a fresh API review approves a public carrier:

```text
FULL | PARTIAL | PUBLISHED_EMPTY | NOT_YET_PUBLISHED | MISSING_PERIOD |
COVERAGE_BOUNDARY | NOT_SERVED | TRANSPORT_FAILURE | SCHEMA_DRIFT |
BUDGET_EXHAUSTED | LEGAL_GAP | IDENTITY_GAP
```

- `FULL` requires eight or fewer complete distinct annual reports, provider-declared bounds, exact
  fiscal dates, response-backed ROE identity, and reconciled pages/counts/cursors.
- `PARTIAL` requires provider-declared supported bounds and reconciled returned pages. An unexplained
  interior gap, missing ROE, conflicting duplicate, or unreconciled page is failure/unknown.
- `PUBLISHED_EMPTY`, `NOT_YET_PUBLISHED`, and `COVERAGE_BOUNDARY` require an owner declaration;
  empty JSON, a timeout, a WAF/403, or a missing page is not any of them.
- `NOT_SERVED` is a pre-network capability decision and consumes zero physical dispatches.
- `TRANSPORT_FAILURE`, `SCHEMA_DRIFT`, `BUDGET_EXHAUSTED`, `LEGAL_GAP`, and `IDENTITY_GAP` never
  return a partial accumulator or an empty successful history.

Public result/exception/warning shapes remain current until a qualified-source API design passes.
Raw URL/query, bodies, headers, cookies, arbitrary provider text, and unbounded source names are
never public diagnostics.

## 11. Atomic deterministic budget contract

Numeric ceilings are intentionally not frozen before a qualifying route and published rate policy.
The future implementation must still reserve atomically:

1. one logical source attempt before adapter entry;
2. one physical dispatch immediately before each initial, page/cursor, retry, or redirect request;
3. separate byte/decompression counters that never increment physical dispatch;
4. zero attempt and zero dispatch for a capability skip; and
5. one request-scoped global ledger with no per-source/page/failover reset.

On exhaustion, discard private rows and retain only bounded sanitized attempts/outcomes. Do not emit a
partial report or infer absence. The future design must define one exact exception-versus-sentinel
carrier before RED; the current `FinancialReport`/`Period.UNKNOWN` behavior is unchanged.

## 12. Required future RED/release matrix

No RED is authorized by this source-gap handoff. If a source later qualifies, a fresh design must
pin a RED-first matrix covering:

| Area | Required positive/negative cases |
|---|---|
| Input/API | exact facade/direct-source annual request; `limit`; symbol/statement/period validation; zero-network malformed/unsupported inputs; current `RATIOS + QUARTER` compatibility |
| Identity | exact symbol, provider symbol, canonical `ROE`, provider-code alias only with owner proof; wrong symbol, missing code, duplicate/conflict, mixed entity/template |
| Cadence/date | provider annual marker and fiscal end; request echo, current, TTM, quarter, publication/retrieval date, inferred Dec 31, null/ambiguous date all RED |
| Semantics/unit | definition, average/ending equity, attributable/total profit, percent/fraction, valid negative/zero, bool/non-finite/malformed, wrong unit/currency |
| Coverage | eight distinct reports, newest-first, pages/counts/cursors, provider bounds, `FULL`/declared `PARTIAL`; duplicate period, missing ROE, interior gap, unreconciled/truncated response |
| Atomicity | one source for whole request; no cross-source stitch; capability skip; retry/page/redirect/byte/global-budget exhaustion discards accumulator |
| Provenance | source/provider symbol, fiscal date, UTC fetch time, revision/as-of, bounded warnings/attempts, DataFrame attrs, repr/equality/serialization, `FinancialReport.get("ROE")` |
| Scope | existing VNDirect/CafeF ratio behavior, all non-ratio statements, failover compatibility, and 26-metric zero-ratio-fetch remain green |
| Release | public docs/skill/CHANGELOG/API snapshot, blacklist/secret/diff/path/object/clean-tree gates, focused/full offline tests, isolated sdist/wheel |

The release decision must explicitly choose whether existing cadence-agnostic ratio callers remain
supported unchanged, receive a versioned annual-only capability, or require a documented release
boundary. No silent behavior change is allowed.

## 13. Reopen criteria and docs-only completion

Reopen requires one fresh primary-source packet proving all of these together:

- exact owner route/version, method, complete/normalized MIME, redirects, auth/UA/WAF behavior,
  bounded bytes/rate/retries, and automation permission;
- response-backed symbol, canonical ROE identity, definition, scale, annual cadence, fiscal date,
  nullability, revision/as-of semantics, and template/entity identity;
- provider-declared eight-period coverage, page/count/cursor/calendar reconciliation, duplicates,
  gaps, and current-VN30 corporate/bank evidence;
- lawful attribution, storage/cache, retention, commercial, derivative, and redistribution rights;
- finite sanitized outcomes, atomic global budget, existing API compatibility, and complete RED/
  release matrix.

A single annual document, ratio label, numeric agreement, request selector, current snapshot,
secondary dashboard, timeout/no-data response, or statement-derived calculation cannot reopen this
closure. A future `QUALIFIED_PARTIAL` must publish the provider-declared boundary and cannot silently
become `FULL`.

For this `SOURCE-GAP CLOSURE`, the allowed post-PASS sequence is only merged docs/full/build/
blacklist/diff gates, exact approved docs push, remote HEAD/ancestry/path verification, clean
no-capability resolution, close/re-read, and local completion. This does not authorize TDD or runtime
work. #222, #223, and #224 remain queued behind active #220.

## 14. Primary references

- [VNDirect ratio route](https://api-finfo.vndirect.com.vn/v4/ratios)
- [VNDirect financial-information archive](https://www.vndirect.com.vn/danh_muc_bao_cao/thong-tin-tai-chinh/)
- [VNDirect application terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/)
- [CafeF data-tool guide](https://cafef.vn/du-lieu/huong-dan-su-dung.chn)
- [CafeF ratio route](https://cafef.vn/du-lieu/Ajax/PageNew/GetDataChiSoTaiChinh.ashx)
- [SSI developer overview](https://developers.ssi.com.vn/docs/getting-started/overview)
- [SSI FC API help](https://fc-data.ssi.com.vn/Help)
- [SSI financial-report archive](https://www.ssi.com.vn/en/investor-relation/financial-report)
- [SSI terms of services](https://www.ssi.com.vn/en/terms-of-services)
- [TCBS OpenAPI](https://developers.tcbs.com.vn/)
- [TCInvest analysis landing page](https://tcinvest.tcbs.com.vn/tc-analysis/dashboard)
- [TCBS audited-report notice](https://www.tcbs.com.vn/quan-he-nha-dau-tu/bao-cao-tai-chinh/cbtt-ve-bao-cao-tai-chinh-va-bao-cao-ty-le-an-toan-tai-chinh-nam-2025-da-duoc-kiem-toan/)
- [HOSE VN30 ground rules](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15ff11e799483abd11677ad0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf)
- [HOSE index-data page](https://www.hsx.vn/vi/du-lieu-giao-dich/quy-mo-giao-dich/bo-chi-so)

## Bottom summary

- Decision: **SOURCE-GAP CLOSURE**; no candidate passes all annual-ROE axes.
- VNDirect exposes ratio/report dates, not proven annual fiscal identity or reuse rights.
- CafeF exposes annual-looking fields, but request selectors and nullable tags are not identity.
- SSI and TCBS official API paths are credential-gated; public documents are not a common ROE feed.
- Current VN30 coverage is `UNKNOWN`; no runtime basket or hard-coded membership list is added.
- Current `Period.UNKNOWN` ratios and zero-ratio 26-metric behavior remain unchanged.
- No RED, code, push, close, or production capability is authorized.
- Reviewer needs the exact committed two-artifact + backlog SHA for design review.
