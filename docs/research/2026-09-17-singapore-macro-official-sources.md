# #236 official-source research — Singapore macro coverage

**Research date:** 17 September 2026 (+07)  
**Target base:** `origin/master` `8d450a40cd9763a58bdb85c5f125edcc18d182da`  
**Issue:** `hungson175/vnfin#236`  
**Public intake:** `issuecomment-5714070058`  
**Phase:** source/API design only; no RED tests or production code

## Clean-room declaration

This research excludes VNStock and every VNStock-derived source. Every discovery query used:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result was opened, cited, compared, or used. An irrelevant third-party result was
shown in one search-results listing; it was not opened, cited, or used. Evidence is limited to the
repository at the target base and official World Bank, IMF, Singapore Department of Statistics
(SingStat), Monetary Authority of Singapore (MAS), and data.gov.sg surfaces. Government ownership
is not treated as a permission grant; technical access and legal permission are separate gates.

## Question, frozen scope, and result

The question is which of the ten existing provider-independent `MacroIndicator` cells can be
supported honestly for `SGP` without changing the public primitive:

```python
vnfin.macro.get_indicator("SGP", indicator) -> IndicatorSeries
```

The cells are `GDP`, `GDP_GROWTH`, `CPI`, `INFLATION`, `UNEMPLOYMENT`, `CPI_YOY`,
`POLICY_RATE`, `LENDING_RATE`, `DEPOSIT_RATE`, and `REAL_INTEREST_RATE`. No proxy,
substitute, interpolation, cross-source point stitch, hidden endpoint, rendered-page scrape, or
missing-value fill is allowed.

| Outcome | Cells | Meaning |
|---|---|---|
| `QUALIFIED_EXISTING` | GDP, GDP_GROWTH, CPI, INFLATION, UNEMPLOYMENT, LENDING_RATE, DEPOSIT_RATE, REAL_INTEREST_RATE | Existing World Bank WDI v2 routes returned exact `SGP` and code identities. Rate cells are useful historical series but end in 2021; this is not a current-rate claim. |
| `LEGAL_GAP` | CPI_YOY | SingStat `M213781`, row key `1` / `All Items`, is the exact provider-published monthly concept and responded correctly, but the exact route's use/return/cache/redistribution terms and retained unit field are not cleared. It is also a documentation-contract gap because the advertised catalog URL returned HTML. |
| `SEMANTICS_GAP` | POLICY_RATE | Singapore's monetary-policy stance is exchange-rate-centred. SORA, interbank rates, facility rates, MAS Bills and SGS yields are not an official policy target and cannot fill this cell. |

There are **8 qualified existing cells, 1 legal/contract gap, and 1 semantic gap**. No new source,
enum, model, adapter, registration, or capability claim is approved by this research.

## Pre-transport plan and process accounting

The request plan was committed before provider-data transport at `945c981bf14936aec77e380c8e8f4d888786f32b`.
Provider probes were sequential `GET`s with zero retries, 5-second connect and 25-second total
timeouts, owner-preserving redirects, a 4 MiB compressed / 16 MiB decompressed local ceiling, and
sanitized summaries only. Unexpected auth, WAF/HTML, redirect, pagination, identity, MIME, or byte
behavior was a stop condition. No raw provider rows or response bodies are committed.

The provider budget was respected: 26 of 34 logical and physical reservations were used. The
search-discovery budget was **not** respected: orchestration issued 25 query strings in 7 search
dispatches instead of the declared 6/6 ceiling. All used the exclusion string and official-domain
intent; only direct official pages support the findings. This is a process deviation, not hidden as
unused capacity. It did not add provider-data calls or alter the provider probe set, but the reviewer
must decide whether the design can pass with this disclosed deviation. Sixteen official-document
URL-open actions were made within the 18-action reservation; the browser abstraction did not retain
underlying HTTP request count, bytes, or redirect hops.

### Design-block correction mini-budget (committed before access)

Reviewer block `9b4c8f76` permits a narrowly bounded B1 correction and forbids further search
discovery. The correction budget is atomic and independent of unused reservations above:

| Correction surface | Logical reservation | Physical ceiling | Exact purpose and stop rule |
|---|---:|---:|---|
| Search engine | 0 | 0 | No further discovery query, including retry or alternate wording |
| SingStat official OpenAPI page | 1 | 1 | Direct open of `/view-api/for-developers/openapi`; retain only contract metadata, official links, and clause locators; expected HTML |
| SingStat Terms of Use | 1 | 1 | Follow only the official page's exact “Terms of Use” navigation target; no guessed path or alternate search |
| SingStat API Terms of Service | 1 | 1 | Follow only the official page's exact “API Terms of Service” navigation target; no guessed path or alternate search |
| SingStat `M213781` | 1 | 1 | One exact existing table request solely because the prior private receipt omitted `uoM`; retain sanitized table/row metadata and response-contract keys, not values/rows |
| **Correction total** | **4** | **4** | Zero retries; an unavailable, unexpected, or exhausted reservation stops that evidence leg |

The three document/navigation actions may not leave the official SingStat host family. The exact
table request remains a sequential `GET` with a 5-second connect timeout, 25-second total timeout,
4 MiB compressed / 16 MiB decompressed local ceiling, complete status/MIME/final-host capture, and
zero redirects/retries. Expected document HTML is not a WAF failure by itself; unexpected login,
challenge, external redirect, or missing official navigation target stops that leg. Retain only
sanitized hashes, link targets, clause headings/locators, and short paraphrases. No raw body,
provider observation, header, cookie, or live value is committed. Unused capacity expires after
this correction and cannot be reassigned.

## Existing architecture at the target base

The source order is World Bank -> IMF DataMapper -> DBnomics. Canonical-unit filtering and optional
country eligibility run before cache, transport, or attempt creation.

| Indicator | Canonical contract | Existing effective `SGP` route |
|---|---|---|
| GDP | annual `current US$`, currency `USD` | World Bank only; IMF `NGDPD` (`USD bn`) and DBnomics national-currency GDP are unit-filtered |
| GDP_GROWTH | annual `%` | World Bank -> IMF `NGDP_RPCH` |
| CPI | annual `index` | World Bank only; DBnomics has no `SGP` country mapping |
| INFLATION | annual `%` | World Bank -> IMF `PCPIPCH` |
| UNEMPLOYMENT | annual `%` | World Bank -> IMF `LUR` |
| CPI_YOY | monthly `%` | no eligible source; DBnomics has no `SGP` mapping |
| POLICY_RATE | monthly `% per annum` | no eligible source; DBnomics has no `SGP` mapping and its route is separately VNM-only |
| LENDING_RATE | annual `%` | World Bank only |
| DEPOSIT_RATE | annual `%` | World Bank only |
| REAL_INTEREST_RATE | annual `%` | World Bank only |

Consequently `SGP/CPI_YOY` and `SGP/POLICY_RATE` currently fail before cache/transport with zero
source attempts. The VNM-only `FPOLM_PA` policy-rate boundary remains intact. The frozen
`IndicatorSeries`, exact returned-identity guards, ascending/unique dates, finite-value checks,
canonical unit/currency, frequency, projection boundary, source provenance, warnings, and
`fetched_at_utc` remain invariants.

## Ten-cell evidence matrix — technical behavior

Each row retains its own concept, ownership, route, response, identity, shape, coverage, and
operational evidence. `NOT_RETAINED` is not zero; `NOT_DISPATCHED` is not a negative response.

| Indicator / outcome | Exact concept, owner, operator, route/version/method | Request -> returned identity; HTTP/MIME/final host/auth | Frequency, unit/base, semantics, actual/projection | Bounds, integrity, revision/current lag | Rate/page/retry/byte behavior |
|---|---|---|---|---|---|
| **GDP** `QUALIFIED_EXISTING` | WDI `NY.GDP.MKTP.CD`, World Bank owner/operator; Indicators API v2 `GET /country/SGP/indicator/NY.GDP.MKTP.CD?format=json&per_page=20000` | `SGP` + code -> `countryiso3code=SGP`, Singapore, exact code/name; 200, complete `application/json;charset=utf-8`, final `api.worldbank.org`, 0 redirects; no key/session | Annual; canonical `current US$`, `USD`; nominal current-price level. Row unit blank, canonical unit is bound from exact WDI metadata/code. No projection flag returned; adapter exposes observations without a projection boundary. | Provider-declared SGP bounds NOT_RETAINED; 66 non-null, 1960–2025, 0 null, 0 interior gaps, 0 duplicate years; envelope `lastupdated=2026-07-13`; observation status blank; revision/provisional lineage NOT_RETAINED; lag 1 year. | Numeric provider quota/concurrency NOT_RETAINED; page 1/1, total 66, per_page 20000, sourceid 2; qualification retry 0; 13,882 bytes, under local ceiling. |
| **GDP_GROWTH** `QUALIFIED_EXISTING` | WDI `NY.GDP.MKTP.KD.ZG`, World Bank; v2 GET as above. Existing fallback: IMF/WEO DataMapper `NGDP_RPCH`, IMF owner/operator, `GET /external/datamapper/api/v1/NGDP_RPCH/SGP`. | WDI exact SGP/code: 200 JSON, final WB host, 0 redirects, no auth. IMF exact code/SGP nested identity: 200 `application/json`, final `www.imf.org`, 0 redirects, no auth observed. | Annual `%`; WDI real constant-price annual growth. IMF annual `%`; 2026+ conservatively marked projections by vnfin, not a per-point IMF flag. | WDI 65 non-null/1 null, 1961–2025, 0 interior gaps/dups, update 2026-07-13, lag 1. IMF 52 non-null, 1980–2031, 0 gaps; six years 2026–2031 fall under adapter projection cutoff; exact WEO estimate/forecast lineage and revision vintage NOT_RETAINED. | WDI page 1/1 total 66; 14,339 bytes. IMF no pagination in adapter; 121,723 bytes. Provider quotas NOT_RETAINED; retry 0; local ceilings passed. |
| **CPI** `QUALIFIED_EXISTING` | WDI `FP.CPI.TOTL`, World Bank; v2 GET. SingStat `M213751` row `1` is a separate monthly candidate, not a same-frequency failover. | WDI exact SGP/code: 200 JSON, WB host, 0 redirects, no auth. `M213751` separately returned table id/title and exact `All Items` row through `GET /api/table/tabledata/M213751`, 200 `application/json; charset=utf-8`, SingStat host, 0 redirects, no auth observed. | Canonical WDI annual `index`, metadata name carries `2010=100`; index level. SingStat candidate is monthly, non-seasonally-adjusted title, 2024 base; exact `uoM` was not retained, so it cannot silently replace annual WDI or be registered. No projection flags. | WDI 66 non-null, 1960–2025, no null/gap/dup, update 2026-07-13, lag 1. SingStat `All Items`: 787 periods, 1961 Jan–2026 Jul, 0 retained markers/dups; table updated 24 Aug 2026; correction/revision policy NOT_RETAINED. | WDI page 1/1 total 66, 14,729 bytes. SingStat full table 182,860 bytes; paging/limit contract NOT_RETAINED. Quotas NOT_RETAINED; retry 0; local ceilings passed. |
| **INFLATION** `QUALIFIED_EXISTING` | WDI `FP.CPI.TOTL.ZG`, World Bank, v2 GET. Existing fallback IMF DataMapper `PCPIPCH`. | Both returned exact requested SGP/code; WDI 200 `application/json;charset=utf-8`, WB final host; IMF 200 `application/json`, IMF final host; 0 redirects; no auth observed. | Annual `%`; WDI annual consumer-price change. IMF annual average consumer-price inflation; 2026+ marked projections by vnfin's current-year rule. Neither is the monthly CPI_YOY cell. | WDI 65 non-null/1 null, 1961–2025, 0 interior gaps/dups, update 2026-07-13, lag 1. IMF 52 non-null, 1980–2031, 0 gaps; 2026–2031 treated as projections; exact vintage/revisions NOT_RETAINED. | WDI page 1/1 total 66, 15,224 bytes. IMF no adapter pagination, 120,999 bytes. Provider quotas NOT_RETAINED; retry 0; local ceilings passed. |
| **UNEMPLOYMENT** `QUALIFIED_EXISTING` | WDI `SL.UEM.TOTL.ZS`, World Bank, modeled ILO estimate; v2 GET. Existing fallback IMF DataMapper `LUR`. SingStat `M182332` is a distinct end-June seasonally-adjusted national table, not silently equivalent. | WDI/IMF exact requested SGP/code: 200, complete JSON MIME, owner host, 0 redirects, no auth observed. SingStat table route: 200 JSON, exact title; row `4`, `Total Unemployment Rate, (SA)`. | WDI annual `% of labour force`, modeled estimate; IMF annual `%`, with 2026+ internal projection cutoff. SingStat annual end-June seasonally adjusted point-in-time rate is semantically different. | WDI 35 non-null/31 null envelope positions, 1991–2025, no gaps within non-null bounds/dups, update 2026-07-13, lag 1. IMF 52 non-null, 1980–2031, no gaps, 2026–2031 projection-classed. SingStat row has 35 periods, 1992–2026, no retained markers/dups, table updated 31 Jul 2026. Revision lineage NOT_RETAINED. | WDI page 1/1 total 66, 16,394 bytes. IMF 58,066 bytes. SingStat table 3,538 bytes. No numeric provider quota retained; retry 0; ceilings passed. |
| **CPI_YOY** `LEGAL_GAP` | Exact technical candidate: SingStat-owned/operated `M213781`, row key `1`, `All Items`, “Percent Change In CPI Over Corresponding Period Of Previous Year…Monthly”; `GET /api/table/tabledata/M213781`. | Requested table -> exact id/title/frequency/row key and label; envelope StatusCode 200; HTTP 200, complete `application/json; charset=utf-8`, final `tablebuilder.singstat.gov.sg`, 0 redirects; no auth observed. Catalog/OpenAPI URL instead returned 200 `text/html`, so stable machine contract is not established. | Monthly same-month-prior-year percentage change, 2024 CPI base family; provider-published, so no local derivation. Exact response `uoM` value was not retained and cannot be inferred as a cleared unit. No projection flag. | Provider-declared bounds NOT_RETAINED; observed 775 periods, 1962 Jan–2026 Jul, 0 retained missing markers/dups; table updated 24 Aug 2026; revision/correction policy and current-lag rule NOT_RETAINED. | 168,396 bytes, retry 0, no redirect, under local ceiling. Pagination/limit/rate/concurrency/byte contract NOT_RETAINED. Route and permission remain unregistered. |
| **POLICY_RATE** `SEMANTICS_GAP` | No qualifying concept. MAS owner/operator surfaces examined: S$NEER policy framework, SORA, facilities, MAS Bills/SGS yields. No route was selected because none is the canonical monetary-policy target-rate concept. | `NOT_DISPATCHED`; requested/returned identity, status, MIME, redirect/final host, and auth are `NOT_RETAINED`. Existing DBnomics SGP route is absent and the policy route stays VNM-only. | Canonical cell expects monthly `% per annum` policy rate. Singapore manages S$NEER band slope/width/centre; the basket/band are undisclosed. SORA is an unsecured overnight transaction benchmark, not a target. Facility rates/yields are distinct. Actual/projection not applicable. | Bounds/count/null/gap/dup/revision/lag `NOT_RETAINED`; absence of a qualifying concept is not `NO_DATA`. | Direct MAS portal is JS-only; exact public API contract, quota, pages, retries, bytes, and no-key posture NOT_RETAINED. No transport occurred. |
| **LENDING_RATE** `QUALIFIED_EXISTING` | WDI `FR.INR.LEND`, World Bank; annual lending rate generally meeting private-sector short/medium financing needs; v2 GET. data.gov.sg bank-rates dataset is only a local candidate and was not dispatched. | WDI exact SGP/code: 200 JSON, WB host, 0 redirects, no auth. Local candidate exact series identity NOT_RETAINED; no row-position selection allowed. | Annual `%`, no currency; aggregate lending-rate concept, not policy rate. No projection flag. Local monthly end-period rates cannot replace it without exact row definition/equivalence. | WDI 44 non-null/22 null positions, 1978–2021, 0 interior gaps/dups, update 2026-07-13, **5-year lag**. Revision flags NOT_RETAINED. Qualified as historical only; no current-rate claim. | Page 1/1 total 66, 13,623 bytes; quota NOT_RETAINED; retry 0; local ceiling passed. |
| **DEPOSIT_RATE** `QUALIFIED_EXISTING` | WDI `FR.INR.DPST`, World Bank; commercial/similar-bank demand/time/savings deposit rate; v2 GET. data.gov.sg bank-rates dataset remains an unprobed candidate. | WDI exact SGP/code: 200 JSON, WB host, 0 redirects, no auth. Local series identity/equivalence NOT_RETAINED. | Annual aggregate `%`, no currency; not a tenor-specific quote or policy rate. No projection flag. | WDI 45 non-null/21 null positions, 1977–2021, 0 interior gaps/dups, update 2026-07-13, **5-year lag**. Revision flags NOT_RETAINED. Historical-only qualification. | Page 1/1 total 66, 13,811 bytes; quota NOT_RETAINED; retry 0; local ceiling passed. |
| **REAL_INTEREST_RATE** `QUALIFIED_EXISTING` | WDI `FR.INR.RINR`, World Bank; lending rate adjusted by GDP-deflator inflation; v2 GET. No exact local MAS/SingStat/data.gov concept found. | WDI exact SGP/code: 200 JSON, WB host, 0 redirects, no auth. Local candidate `NO_DATA` for the exact concept; no nominal-minus-CPI derivation. | Annual `%`, may be negative; exact WDI real-interest concept. No projection flag. | WDI 44 non-null/22 null positions, 1978–2021, 0 interior gaps/dups, update 2026-07-13, **5-year lag**. Revision flags NOT_RETAINED. Historical-only qualification. | Page 1/1 total 66, 13,758 bytes; quota NOT_RETAINED; retry 0; local ceiling passed. |

All WDI metadata requests also returned exact code, source id `2` / World Development Indicators,
source note, and source organization. The observation envelopes were page 1 of 1 with `total=66`,
`per_page=20000`, `sourceid=2`, and `lastupdated=2026-07-13`. Empty WDI row `unit` and
`obs_status` strings are reported as observed, not treated as proof of no unit or no estimate.

## Ten-cell evidence matrix — permissions and caller lifecycle

| Indicator / outcome | Terms/version/effective date | Automation and caller return | Cache/storage; retention/deletion | Attribution; commercial/derivative; redistribution | Amendment/revocation |
|---|---|---|---|---|---|
| **GDP** `QUALIFIED_EXISTING` | World Bank dataset terms; series marked CC BY 4.0; page effective date NOT_RETAINED | API automation and returned data use cleared in principle for the labeled dataset, subject to reasonable/non-abusive volume | Copy/storage allowed by license; vnfin cache off by default; retention/deletion term NOT_RETAINED | Credit World Bank/dataset/source organization and indicate changes; commercial use, derivatives, and redistribution allowed under CC BY 4.0, subject to third-party/dataset exceptions | API/terms may change or access be revoked; exact notice/versioning promise NOT_RETAINED |
| **GDP_GROWTH** `QUALIFIED_EXISTING` | WDI: CC BY 4.0, effective date NOT_RETAINED. IMF fallback: IMF copyright/terms effective 11 Oct 2024; WEO covered by special data terms | WDI cleared as above. IMF terms permit data use with conditions, but bulk automated download is prohibited without permission and commercial reuse requests permission; therefore IMF automation/commercial posture is `NOT_CLEARED` for an OSS default | WDI copy/storage allowed, no retained TTL/deletion. IMF cache/storage/retention/deletion NOT_CLEARED/NOT_RETAINED; current cache off | WDI attribution/change indication, commercial/derivative/redistribution allowed. IMF requires accurate attribution and transformation disclosure; standalone sale disclosure; commercial reuse NOT_CLEARED | Both may amend/revoke/change API; precise advance notice NOT_RETAINED |
| **CPI** `QUALIFIED_EXISTING` | WDI CC BY 4.0, effective date NOT_RETAINED. Direct SingStat candidate terms/version/effective date NOT_RETAINED | WDI automation/caller return cleared. Direct SingStat automation/caller return NOT_CLEARED | WDI copy/storage allowed; no retained TTL/deletion. SingStat cache/storage/retention/deletion NOT_CLEARED/NOT_RETAINED | WDI attribution required; commercial/derivative/redistribution allowed. SingStat attribution/commercial/derivative/redistribution NOT_CLEARED | WDI change/revocation possible. SingStat amendment/revocation NOT_RETAINED |
| **INFLATION** `QUALIFIED_EXISTING` | Same WDI CC BY 4.0 primary and IMF special-data fallback posture as GDP_GROWTH | WDI cleared; IMF bulk automation/commercial reuse NOT_CLEARED without permission | WDI storage allowed/no retained TTL; IMF lifecycle NOT_CLEARED/NOT_RETAINED; cache off | WDI attribution and reuse allowed; IMF attribution/transformation conditions, commercial reuse NOT_CLEARED | Terms/API may change; exact notice NOT_RETAINED |
| **UNEMPLOYMENT** `QUALIFIED_EXISTING` | Same WDI primary and IMF fallback posture; direct SingStat terms NOT_RETAINED | WDI cleared; IMF bulk/commercial posture NOT_CLEARED; SingStat caller use NOT_CLEARED | WDI storage allowed/no retained TTL; IMF/SingStat lifecycle NOT_CLEARED/NOT_RETAINED | WDI attribution/reuse allowed; IMF conditional attribution with commercial gap; SingStat reuse NOT_CLEARED | Change/revocation possible; route-specific notice NOT_RETAINED |
| **CPI_YOY** `LEGAL_GAP` | Direct SingStat route terms/version/effective date NOT_RETAINED | Automation and returning rows to callers NOT_CLEARED | Cache/storage/retention/deletion NOT_CLEARED/NOT_RETAINED | Attribution, commercial/derivative use, and redistribution NOT_CLEARED | Amendment/revocation NOT_RETAINED |
| **POLICY_RATE** `SEMANTICS_GAP` | No qualifying dataset/route, so no transferable terms. Direct MAS eServices terms could not be retained | NOT_APPLICABLE to a rejected proxy; direct MAS automation/caller return NOT_CLEARED | NOT_APPLICABLE; direct MAS storage/retention/deletion NOT_CLEARED/NOT_RETAINED | NOT_APPLICABLE. MAS bilateral FX also names Refinitiv-derived rights, so it cannot be presumed redistributable | NOT_RETAINED |
| **LENDING_RATE** `QUALIFIED_EXISTING` | WDI series CC BY 4.0, effective date NOT_RETAINED. data.gov.sg candidate would be ODL 1.0, but it is not the qualified cell route | WDI automation/caller return cleared. Candidate data.gov public API allows commercial/noncommercial calls, but exact series identity remains unqualified | WDI storage allowed/no retained TTL. data.gov ODL permits copying; no retained retention/deletion duty; API termination means stop API use | WDI credit/reuse allowed. data.gov candidate would require conspicuous dataset/source/access-date/current-license notice and permits commercial/derivative/redistribution subject to exclusions | WDI/API and data.gov terms can change; data.gov access can be suspended/terminated |
| **DEPOSIT_RATE** `QUALIFIED_EXISTING` | Same WDI primary and unqualified data.gov ODL-candidate posture as LENDING_RATE | WDI cleared; data.gov candidate not promoted without exact series proof | WDI storage allowed/no TTL retained; candidate lifecycle as above | WDI attribution/reuse allowed; candidate ODL rights do not cure identity/semantic gaps | Change/suspension/revocation possible; notice NOT_RETAINED |
| **REAL_INTEREST_RATE** `QUALIFIED_EXISTING` | WDI series CC BY 4.0, effective date NOT_RETAINED; no exact local dataset | WDI automation/caller return cleared; local derivation not authorized | WDI storage allowed/no retained TTL/deletion; cache off | WDI attribution required; commercial/derivative/redistribution allowed under CC BY 4.0 | API/terms may change/revoke; exact notice NOT_RETAINED |

### Legal source notes

- The World Bank dataset terms permit extraction, download, copying, sharing, and adaptation of
  World Bank-produced open datasets under CC BY 4.0 unless a dataset is specifically labeled
  otherwise. Dataset-specific and third-party restrictions still prevail. The eight inspected
  indicator pages are marked CC BY 4.0. Numeric API rate/concurrency limits were not retained.
- IMF copyright/terms, effective 11 October 2024, cover WEO under special data terms. They permit
  download, extraction, copying, derivatives, publication and distribution with accurate
  attribution and transformation disclosure, but prohibit bulk automated download without
  permission and direct commercial users to request permission. Therefore the three existing IMF
  fallbacks are not newly legal-qualified by this note. The WEO disclaimer also warns of continual
  updates, revisions, estimates, projections and spliced historical series.
- Singapore Open Data Licence 1.0 allows access, copying, distribution, adaptation and commercial
  use with a conspicuous source/dataset/access-date/current-license notice, subject to excluded
  rights. data.gov.sg API terms separately allow commercial/noncommercial API clients, require
  credential confidentiality where applicable, and reserve modification/suspension/termination.
  These rights apply to an exact data.gov dataset; they do not transfer to direct SingStat/MAS
  routes or cure a missing series identity.
- Direct SingStat and MAS route-specific terms were not retained. MAS bilateral FX pages explicitly
  describe Refinitiv-derived inputs, so official hosting cannot be treated as an open-data grant.

## SingStat and MAS candidate decisions

### SingStat exact probes

| Table | Retained result | Decision |
|---|---|---|
| `M213751` | CPI, 2024 base, monthly; `All Items`, series `1`; 1961 Jan–2026 Jul | Exact monthly index candidate, but different frequency/base from current WDI CPI and direct terms/unit contract not cleared. Do not use as silent failover. |
| `M213752` | Same family, explicitly seasonally adjusted | Reject as canonical CPI default; seasonality differs. |
| `M213781` | Monthly CPI corresponding-period percent change; `All Items`, series `1`; 1962 Jan–2026 Jul | Exact provider-published CPI_YOY candidate; hold at `LEGAL_GAP`, no local calculation. |
| `M213811` | Annual corresponding-period CPI percent change | Reject for monthly CPI_YOY. |
| `M016101` | Annual production account at current prices; rows begin Output, Intermediate Consumption, Gross Value Added | Not canonical GDP in current US dollars; reject as replacement. |
| `M182332` | Annual end-June, seasonally adjusted unemployment; exact total row `4` | Semantically distinct from WDI modeled ILO annual estimate; no silent failover. |

The catalog/OpenAPI URL `https://tablebuilder.singstat.gov.sg/view-api/find-apis` returned 200
`text/html` rather than a machine-readable contract. No hidden endpoint discovery followed.

### Monetary-policy boundary

MAS describes an exchange-rate-centred framework: S$NEER is managed against a trade-weighted basket
within an undisclosed band, and stance is expressed via the band's slope, width, and centre. S$NEER
is an exchange-rate-policy variable, not a rate. SORA is a volume-weighted unsecured overnight SGD
cash-market transaction benchmark; it is not a policy target. Historical interbank rates, facility
rates, MAS Bills, SGS repo/yields, and commercial-bill rates are also distinct concepts. The
`POLICY_RATE` cell therefore remains `SEMANTICS_GAP`, not a best-effort proxy.

The data.gov.sg “Current Banks Interest Rates (End Of Period), Monthly” candidate
`d_5fe5a4bb4a1ecc4d8a56a095832e2b24` is catalogued as MAS source / SingStat manager, monthly,
percent per annum, July 2005–July 2026. Its exact bank lending/deposit row identities and definitions
were not retained within the budget, so it cannot replace the existing annual WDI concepts. It has
no exact real-interest series, and nominal-minus-CPI derivation is not authorized.

## Runtime and API decision

The existing public API/model is sufficient for any future exact monthly series only if the result
preserves the provider table/series identity, exact `SGP` identity, canonical unit, monthly day-1
dates, no projection fabrication, source, retrieval time, and warnings. However, no new source is
registered in this phase.

Binding boundaries:

1. Keep World Bank as the annual primary for the eight qualified cells.
2. Preserve current source ordering, unit prefilter, country eligibility, exact returned-identity
   guards, immutable model, warnings, and no point stitching.
3. Do not register SingStat until exact terms, stable route contract, unit, row-key semantics,
   revision/missingness behavior, and runtime limits pass review.
4. Do not derive CPI_YOY while a provider-published candidate exists; no annual CPI derivation or
   missing-month interpolation.
5. Do not relax the VNM-only policy-rate guard or relabel any Singapore market/facility rate.
6. The WDI interest-rate cells must be documented as historical through 2021, not current.
7. No enum/model/public snapshot change is justified by this evidence.

## Ranked candidate expansion — proposal only

| Rank | Candidate primitive | Investor/analyst value | Evidence quality and blocking boundary |
|---:|---|---|---|
| 1 | Merchandise trade | High | High. data.gov dataset `d_31b2dcafe417ff922e1542d45ed6f176`, monthly current prices, declared Jan 1995–Jun 2026. Classification break at 1999 (SITC3 to SITC4.1/AHTN2022) must be explicit; exact rows/units/revisions still need a bounded probe. |
| 2 | Money supply | High | High with structural break. `d_7ed3eccba609ac0bdfcf406d939bdb0b`, monthly end-period, million dollars, Jul 2021–Jul 2026. Reporting-rule/DBU-ACU break means do not silently stitch discontinued `M920281`. |
| 3 | Official reserves | Medium-high | High. `d_92afecf58ad03196ff6a7abb7a03d631`, monthly end-period million dollars, Jan 1972 onward; May 1999 valuation break. Re-probe current bound/update discrepancy. |
| 4 | Real retail sales | Medium-high | High but currently lagged. `d_0cd4e1d703f04efda7dcf64485c950cc`, seasonally adjusted chained-volume monthly index, Jan 1985–Dec 2025. Prefer real volume over current-price alternative. |
| 5 | Industrial production | High | Low/currentness gap. Located dataset `d_183f0b0c1a539f150c0c0f080a66d357` is 2015-base monthly IIP but only through Dec 2019 and last catalog update June 2024. Find a current exact source before design. |
| 6 | Official FX / S$NEER | High | Low route/legal evidence. MAS bilateral FX is Refinitiv-derived; S$NEER basket/band are undisclosed and no stable licensed machine series was retained. It requires a separate exchange-rate model, never `POLICY_RATE`. |

These are not pre-approved enum members or API work. Each needs a separate source, legal, model,
and RED gate.

## Request ledger result

| Surface | Logical used / reserved | Physical used / ceiling | Result, bytes, and stop reason |
|---|---:|---:|---|
| World Bank WDI v2 | 16 / 16 | 16 / 16 | 8 metadata + 8 SGP observation requests; all 200 `application/json;charset=utf-8`; 0 redirects; 121,556 bytes total (459–16,394 each); exact identities; reservation exhausted as planned |
| IMF DataMapper | 3 / 3 | 3 / 3 | three exact existing fallbacks; all 200 `application/json`; 0 redirects; 300,788 bytes total (58,066–121,723); reservation exhausted as planned |
| SingStat | 7 / 7 | 7 / 7 | one catalog request returned unexpected HTML and six exact tables returned 200 JSON; 0 redirects; 667,874 bytes total (1,050–182,860); no hidden discovery; reservation exhausted |
| MAS | 0 / 4 | 0 / 4 | no exact policy-rate concept or stable public contract selected; stopped before transport |
| data.gov.sg | 0 / 4 | 0 / 4 | official docs/catalog evidence was sufficient to identify future candidates; no exact row-qualified parity candidate selected within plan |
| **Provider total** | **26 / 34** | **26 / 34** | **1,090,218 bytes; zero retries; all dispatched requests 200; no redirects; no raw rows committed** |
| Official docs/terms | 16 / 18 URL actions | underlying transport NOT_RETAINED | official pages only; browser tool did not retain raw transport accounting |
| Search discovery | **25 / 6 query strings** | **7 / 6 dispatches** | **budget breach disclosed above**; no provider rows; no prohibited result opened or used |

The private sanitized receipts were used only during design and are not committed. Production
adapters currently do not enforce the qualification harness's MIME, redirect, or response-byte
ceilings; a future build must not claim those harness guarantees as runtime guarantees without code
and tests.

## Official sources

### World Bank

- [Indicators API overview](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation)
- [Indicator API queries](https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries)
- [Basic call structures](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures)
- [World Bank dataset terms](https://www.worldbank.org/ext/en/legal/terms-conditions/datasets)
- [World Bank public licenses](https://datacatalog.worldbank.org/public-licenses)
- Official indicator pages: [`NY.GDP.MKTP.CD`](https://data.worldbank.org/indicator/NY.GDP.MKTP.CD),
  [`NY.GDP.MKTP.KD.ZG`](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG),
  [`FP.CPI.TOTL`](https://data.worldbank.org/indicator/FP.CPI.TOTL),
  [`FP.CPI.TOTL.ZG`](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG),
  [`SL.UEM.TOTL.ZS`](https://data.worldbank.org/indicator/SL.UEM.TOTL.ZS),
  [`FR.INR.LEND`](https://data.worldbank.org/indicator/FR.INR.LEND),
  [`FR.INR.DPST`](https://data.worldbank.org/indicator/FR.INR.DPST), and
  [`FR.INR.RINR`](https://data.worldbank.org/indicator/FR.INR.RINR)

### IMF

- [IMF copyright and terms](https://www.imf.org/en/about/copyright-and-terms)
- [WEO database disclaimer](https://www.imf.org/en/publications/weo/weo-database/disclaimer)
- [IMF DataMapper](https://www.imf.org/external/datamapper/)

### Singapore official sources

- [SingStat Data API catalog](https://tablebuilder.singstat.gov.sg/view-api/find-apis)
- [SingStat `M213781` table route](https://tablebuilder.singstat.gov.sg/api/table/tabledata/M213781)
- [MAS domestic interest rates](https://eservices.mas.gov.sg/Statistics/dir/DomesticInterestRates.aspx)
- [MAS Financial Database](https://eservices.mas.gov.sg/statistics/fdanet/)
- [MAS API portal](https://eservices.mas.gov.sg/apimg-portal/home)
- [data.gov.sg developer API overview](https://guide.data.gov.sg/developer-guide/api-overview)
- [data.gov.sg search/filter API](https://guide.data.gov.sg/developer-guide/dataset-apis/search-and-filter-within-dataset.md)
- [data.gov.sg download API](https://guide.data.gov.sg/developer-guide/dataset-apis/download-dataset.md)
- [data.gov.sg rate limits](https://guide.data.gov.sg/developer-guide/api-overview/api-rate-limits.md)
- [Singapore Open Data Licence 1.0](https://data.gov.sg/open-data-licence)
- [data.gov.sg privacy and terms](https://data.gov.sg/privacy-and-terms)

## Bottom summary

- Eight annual `SGP` cells are existing World Bank routes with exact response-backed identities.
- GDP/growth/CPI/inflation/unemployment reach 2025; three rate cells end in 2021 and are historical-only.
- SingStat `M213781` is the exact provider-published monthly CPI YoY candidate, but remains a legal/contract gap.
- Singapore has no honest interest-rate `POLICY_RATE`; exchange-rate policy is a distinct future primitive.
- No new source, API/model, enum, adapter, RED test, or production code is approved here.
- Provider probes stayed within 26/34 calls, zero retries/redirects; no raw provider rows were committed.
- Search discovery exceeded its declared cap (25 queries/7 dispatches vs 6/6); reviewer must rule on the deviation.
- Need from reviewer: source/API design verdict and, only if approved, an exact API/model + RED authorization.
