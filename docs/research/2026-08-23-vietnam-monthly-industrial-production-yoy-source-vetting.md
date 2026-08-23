# Vietnam monthly industrial-production YoY source vetting — #219

**Research date:** 2026-08-23 (UTC+7)
**Packet:** `tasks/219-vietnam-monthly-industrial-production-yoy-spec.md` at reviewer `f2d0187`
**Phase:** source/design gate only; no runtime capability is enabled by this report
**Requested inclusive window:** `2018-01-01..2026-08-19`
**Requested target:** `VNM` + future `MacroIndicator.INDUSTRIAL_PRODUCTION_YOY`
**Disposition:** **SOURCE-GAP CLOSURE**
**New source chain:** empty

This is a bounded clean-room source and legal review. A source qualifies only when one owner,
one route/version, one exact national monthly IIP YoY series or release template, one observation
and revision convention, the requested coverage, a bounded runtime contract, and lawful reuse
rights pass together. No provider meets that conjunctive gate. This report therefore authorizes
no enum, registry, adapter, default chain, model, test, API, or production capability.

## 1. Clean-room and product boundary

Before this research, `docs/vnstock-blacklist.md` was read. The exact search exclusions were:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited or derivative result was opened, cited, compared, installed, imported, or used.
The evidence below is limited to official Vietnamese statistics, official international
statistical portals, their documented routes, and official terms/contact material. Licensing
uncertainty is reported as a gap rather than inferred away.

The existing public surfaces are `get_indicator(country_iso3, indicator)` and `IndicatorSeries`.
The requested enum member and call below are **hypothetical future API only**: the enum member is
absent from current v0.2/current code and is not callable in this source-gap review.

```python
vnfin.macro.get_indicator(
    "VNM", vnfin.macro.MacroIndicator.INDUSTRIAL_PRODUCTION_YOY
) -> IndicatorSeries
```

The future canonical contract is fixed by the packet: indicator value
`industrial_production_yoy`, name `Industrial Production Year-over-Year`, unit and value-unit
`%`, currency `None`, frequency `MONTHLY`, and a point key equal to the provider observation
month normalized to a plain month-start date. A release/publication date is not an observation
month. The current `get_indicator(country_iso3, indicator)` signature and existing default
indicator behavior remain unchanged. `VNM` must be checked before network; other countries,
malformed countries, and unsupported indicators must remain zero-network failures.

This report does not add a date argument, derive YoY from an index, convert annual/quarterly or
cumulative growth to monthly observations, substitute manufacturing-only output, use CPI or
market data, or create an acceleration/VN30F signal. The new source chain is empty. Current
macro behavior is unchanged.

## 2. Decision and short rationale

| Candidate | What was established | Blocking qualification gaps | Disposition |
|---|---|---|---|
| Vietnam NSO/GSO | Official monthly IIP release family publishes national whole-industry comparisons and an official IIP table catalogue exists | No stable no-login machine-readable row contract for exact monthly YoY across the requested window; PXWeb table is index-level/year-oriented; page/totals/revision/precision and reuse rights are not reconciled | `SOURCE_GAP` |
| IMF | Official metadata identifies Vietnam Production Index as monthly; IMF documents expose SDMX/API families | Exact no-login provider-owned VNM monthly IIP YoY series, direct values, route/auth contract, requested coverage, and reuse rights are not proven; current API documentation points to sign-in/beta access | `SOURCE_GAP` |
| World Bank | Public GEM/industrial-production catalogue and a Vietnam macro dashboard exist | Exact VNM provider-owned YoY series, direct row identity, current coverage, revision, and redistribution contract are not proven; dashboard is a secondary compilation | `SOURCE_GAP` |
| UN MBS | Official no-login viewer/web service exposes a Vietnam industrial-production series family | The exposed series is an index level (`2010=100`), not provider-published YoY; bounded viewer evidence does not reach the requested window; licence/rate/revision contract is incomplete | `SOURCE_GAP` |

The official NSO release family is the strongest semantic lead, but narrative release text is not
a reconciled series endpoint. The UN MBS route is the strongest no-login technical lead, but it
is the wrong measure and its observed data ends before the requested span. Neither can repair the
other. A third-party or secondary compilation would not close an owner, identity, or rights gap.

## 3. Bounded research method and evidence ledger

All observations were no-credential, read-only GETs or page/document reads against official
owners. No login, API key, `Authorization` header, browser session, challenge solving, proxy,
paid feed, or reporter-supplied endpoint was used. A browser-like user-agent was used as a bounded
transport choice for selected public pages; no no-user-agent control was run, so its necessity is
**NOT_ESTABLISHED** and it is not an automation or permission claim. Cookies, raw headers, bodies,
live indicator values, response digests, query-bearing URLs, and credentials were not retained.

The ledger distinguishes a planned logical cell from a physical dispatch. A physical dispatch is
one actual HTTP request, including a page/cursor request, retry, or redirect follow-up. Local byte
and decompression accounting is separate resource accounting and is never a physical dispatch.
`NOT_PROBED` and `NOT_ESTABLISHED` mean unresolved evidence, never confirmed non-service or
historical absence. The table is a retained **route-cell** ledger, not an all-traffic ledger:
documentation reads and semantic page reads whose transport ledger was not retained are explicitly
marked `NOT_RETAINED` below.

| Evidence cell | Logical / physical dispatches | Retries | Pages/cursors | Transport observation | Retained evidence |
|---|---:|---:|---:|---|---|
| NSO IIP archive index and sampled archive pages | 8 / 8 | 0 | 8 page requests, no cursor contract | `200`; sanitized complete Content-Type observed as `text/html; charset=UTF-8`; normalized media type `text/html`; no redirect was observed in the bounded pass | shape/date/title metadata only; no body or values |
| NSO release calendar | 1 / 1 | 0 | 1 | `200`; sanitized complete Content-Type observed as `text/html; charset=UTF-8`; normalized media type `text/html` | route/date metadata only |
| NSO individual release-document semantic sample | logical/physical/retry/page/redirect totals **NOT_RETAINED**; semantic sample count is recorded separately below | **NOT_RETAINED** | **NOT_RETAINED** | selected release pages were read; per-document status, sanitized complete Content-Type, normalized media type, redirect, and retry fields are **NOT_RETAINED** | title/path/semantic metadata only; no body or values |
| NSO PXWeb UI plus three no-credential API-path candidates | 4 / 4 | 0 for this retained probe cell | no data page/cursor reached | UI page rendered in browser context; bounded shell UI/API attempts timed out; timed-out API response status and both MIME fields are **NOT_RETAINED** | table metadata only |
| IMF catalogue/API documentation and DSBB metadata | qualifying data dispatches: 0; documentation traffic totals **NOT_RETAINED** | **NOT_RETAINED** | **NOT_RETAINED** | documentation/catalogue evidence only; no qualifying data route was called | public metadata and access/legal gaps |
| World Bank GEM/catalogue/dashboard material | direct row dispatches: 0; documentation/dashboard traffic totals **NOT_RETAINED** | **NOT_RETAINED** | **NOT_RETAINED** | public catalogue/dashboard material only; no exact qualifying row route was called | dataset-level metadata only |
| UN MBS viewer, table notes, technical notes, and web-service documentation | retained viewer data cell 2 / 2; documentation traffic totals **NOT_RETAINED** | 0 for retained viewer cell; **NOT_RETAINED** for docs | 2 viewer windows; documentation pages **NOT_RETAINED** | viewer `200`; sanitized complete Content-Type observed as `text/html; charset=utf-8`; normalized media type `text/html`; no redirect was observed in the bounded viewer pass | shape, series-label, and coverage metadata only; no values |

The complete Content-Type values above are sanitized observations; raw header blocks were not
retained. A cell with an unretained response has both the complete-value and normalized-media-type
dimensions marked `NOT_RETAINED`. The ledger is research evidence, not a future runtime quota. It
does not turn an HTML page into a series, and it does not support a false absence claim when a
route timed out or returned no rows. There is no global zero-retry claim: zero is asserted only for
retained cells, and every unretained traffic dimension remains explicitly `NOT_RETAINED`.

## 4. Official Vietnam NSO/GSO candidate

### 4.1 Owner, identity, and semantic evidence

The official [NSO IIP archive](https://www.nso.gov.vn/en/iip/) is a monthly release index. As
observed on the research date, it listed recent monthly releases through July 2026 and older
monthly releases through the archive pagination. The [NSO industry statistics page](https://www.nso.gov.vn/en/industry/)
lists official industrial-production tables and the [release calendar](https://www.nso.gov.vn/en/release-calendar-3/)
provides the publication-calendar route. The exact semantic sample used here is seven monthly/period
release pages plus one annual negative control; the sanitized canonical paths are listed below.
The sampled monthly/period pages contain national IIP year-over-year comparison wording, while the
annual page is not treated as a monthly source. This is bounded narrative evidence only, not a
machine row contract.

The official [industry methodology](https://www.nso.gov.vn/en/metadata/2019/03/industry-2/)
establishes monthly/quarterly/yearly IIP index construction, current/base periods, and aggregation
to whole industry and other levels. It does **not** by itself establish the exact same-period-last-
year release-row contract claimed by this report. That semantic evidence is limited to the seven
sampled monthly/period release pages below. None supplies a stable machine series with row
identity, revision ID, nullability, page totals, or redistribution terms. The release pages also
use estimated/preliminary language in the monthly context; a typed preliminary/final/revised
vintage contract was not established.

### 4.2a Audited NSO semantic sample (no values retained)

The sample contains eight official canonical paths: seven monthly/period semantic pages and one
annual negative control. This count is a semantic-document count, not a transport dispatch count;
the transport ledger for these documents is `NOT_RETAINED` in Section 3.

| Sample class | Official canonical path | Use in this gate |
|---|---|---|
| Monthly | [July 2026 IIP release](https://www.nso.gov.vn/en/data-and-statistics/2026/08/index-of-industrial-production-in-july-of-2026/) | Monthly national-IIP YoY wording sample |
| Monthly | [May 2026 IIP release](https://www.nso.gov.vn/en/data-and-statistics/2026/06/index-of-industrial-production-in-may-of-2026/) | Monthly national-IIP YoY wording sample |
| Monthly | [January 2023 IIP release](https://www.nso.gov.vn/en/data-and-statistics/2023/01/index-of-industrial-production-in-january-of-2023/) | Monthly national-IIP YoY wording sample |
| Monthly | [October 2020 IIP release](https://www.nso.gov.vn/en/data-and-statistics/2020/10/monthly-index-of-industrial-production-in-2020-2/) | Monthly national-IIP YoY wording sample |
| Period/month | [February 2018 socio-economic release](https://www.nso.gov.vn/en/data-and-statistics/2019/10/report-socio-economic-situation-two-months-and-in-february-2018/) | Historical national-IIP YoY wording sample |
| Period/month | [May 2018 socio-economic release](https://www.nso.gov.vn/en/data-and-statistics/2019/10/report-social-and-economic-situations-five-months-and-in-may-2018/) | Historical national-IIP YoY wording sample |
| Period/month | [October 2018 socio-economic release](https://www.nso.gov.vn/en/data-and-statistics/2019/05/report-social-and-economic-situations-in-october-and-ten-months-of-2018/) | Historical national-IIP YoY wording sample |
| Annual negative control | [2018 annual IIP release](https://www.nso.gov.vn/en/data-and-statistics/2019/11/index-of-industrial-production-in-2018/) | Excluded annual cadence; not evidence for monthly capability |

### 4.2 Route and table cells

| NSO cell | Route evidence | Exact target test | Coverage/runtime/legal result |
|---|---|---|---|
| Monthly release archive | [Official IIP archive](https://www.nso.gov.vn/en/iip/), GET, no login | National whole-industry monthly releases contain the right comparison concept in narrative form, but not a stable machine row/schema | Archive navigation shows a useful historical release family, but no reconciled 104-month observation set, provider total, cursor contract, revision map, or machine nullability |
| Release calendar | [Official release calendar](https://www.nso.gov.vn/en/release-calendar-3/), GET, no login | Can support publication timing only if a future exact series binds it to observations | Calendar does not supply the target values, revision identifiers, or redistribution permission |
| Industry table catalogue | [Official industry catalogue](https://www.nso.gov.vn/en/industry/), GET, no login | Lists an “Index of Industrial production by industrial activity” family and other tables; this is not proof of a national monthly YoY row | Table names alone do not reconcile a monthly YoY route or request budget |
| PXWeb table `E07.01` | [Official PXWeb table](https://pxweb.nso.gov.vn/pxweb/en/Industry/Industry/E07.01.px/), GET/UI, no login observed | UI metadata describes industrial activity and year dimensions and a unit of `%`; the table is an index table, not a proven month-keyed provider-published YoY series | Three no-credential API-path candidates and a UI transport attempt timed out under bounded shell observation; no API status/MIME, response rows, totals, or page contract was accepted |

The PXWeb metadata is valuable official evidence, but a percent unit does not identify whether a
cell is an index level, a growth rate, a cumulative rate, or a specific YoY measure. The visible
dimensions do not establish the required monthly observation-month and national whole-industry
contract. A table title, UI rendering, or a timed-out API candidate cannot be used as a failover
or absence oracle.

### 4.3 NSO coverage, revision, and legal axes

- **Requested window:** The release archive contains monthly material from the requested era and
  current releases, but the evidence did not produce one reconciled machine series for every
  month from January 2018 through August 2026. The candidate month-key count is 104 only under a
  future source-declared monthly calendar; it is not an observed NSO total.
- **Provider bounds and pages:** archive pages are navigable, but release pages are documents,
  not a provider-declared series cursor. No total/page reconciliation or historical-vintage index
  was found.
- **Identity:** owner and whole-industry narrative semantics are strong; row-level VNM identity,
  exact provider series code, national scope in a machine response, and a stable release template
  are not proven together.
- **Measure and unit:** same-period-last-year narrative comparisons are promising. Exact raw YoY
  scale, decimal precision, rounding, nullability, seasonal-adjustment flag, and whether a value
  is preliminary or revised are not a stable machine contract.
- **Observation/revision:** release date is not observation month. A typed as-of/vintage/revision
  contract was not found. The future API must not use publication date as the point key.
- **Transport:** archive and calendar HTML were reachable without login in the bounded pass. The
  PXWeb API candidates timed out; this is `TRANSPORT_INCONCLUSIVE`, not `NOT_SERVED`.
- **Rate/retry/automation:** no route-specific public quota, retry, byte, or automation permission
  was established. A successful public page does not imply permission to crawl or redistribute.
- **Reuse/legal:** the [NSO footer](https://www.nso.gov.vn/en/) asks users to identify NSO as the
  source when citing and identifies NSO ownership/copyright. No clear open-data or commercial OSS
  redistribution licence for this IIP series was found. The unrelated licence of any other NSO
  publication cannot be generalized to IIP. Written permission or an explicit licence remains a
  `LEGAL_GAP`.
- **Contact/evidence path:** the official [Industrial and Construction Statistics Department](https://www.nso.gov.vn/en/industrial-and-construction-statistics-department/)
  is the owner-side route for clarifying the exact series, release template, API/runtime policy,
  revisions, and reuse rights. No permission was requested or obtained in this review.

**NSO disposition:** `SOURCE_GAP` with ordered axes
`(IDENTITY_GAP, MEASURE_GAP, COVERAGE_GAP, REVISION_GAP, TRANSPORT_INCONCLUSIVE, PAGE_TOTAL_GAP,
RATE_POLICY_GAP, LEGAL_GAP)`. The ordered tuple is complete for this candidate; it is not a
short-circuit reason and does not claim the provider has no data.

## 5. IMF candidate

The official [IMF API documentation](https://data.imf.org/en/Resource-Pages/IMF-API) documents
SDMX API families and the [IMF production-index access page](https://data.imf.org/en/news/accessing)
describes the transition from IFS to Production Indexes. The official [Vietnam DSBB metadata](https://dsbb.imf.org/e-gdds/country/VNM/summary-of-dissemination)
records Vietnam Production Index with monthly periodicity and a dissemination timeliness value.
These are useful metadata leads, but none of the reviewed pages proves a direct provider-owned
VNM series whose measure is exactly monthly national IIP YoY through the requested endpoint and
window.

The current API documentation indicates that the beta portal/API access flow uses account sign-in.
No credential was used and no no-login data route, exact series key, response identity, page total,
revision convention, or direct value was established. The monthly DSBB metadata is not a value
series and cannot be used as an absence oracle. A statistical-capacity glossary entry that points
to an older production-index concept is not an exact current VNM source.

| Axis | IMF result |
|---|---|
| Owner/route/method | Official IMF API/Production Index documentation; exact no-login value route **NOT_ESTABLISHED** |
| Status/MIME/redirect | No qualifying data dispatch; **NOT_PROBED** |
| Identity/measure | Monthly Vietnam Production Index metadata; exact national provider-published YoY identity **NOT_ESTABLISHED** |
| Coverage/revision | Requested 2018-01..2026-08 span, totals, gaps, vintage and preliminary/final semantics **NOT_ESTABLISHED** |
| Auth/session/UA/WAF | Current access documentation points to sign-in/beta access; no login or session workaround is allowed |
| Rate/retry/bytes | **NOT_ESTABLISHED** for the exact candidate route; no numeric ceiling frozen |
| Legal/redistribution | **NOT_ESTABLISHED** for the exact series and use case |
| Outcome | `SOURCE_GAP`, not confirmed non-service |

**IMF disposition:** `SOURCE_GAP` with `(IDENTITY_GAP, AUTH_GAP, COVERAGE_GAP, REVISION_GAP,
RUNTIME_GAP, RATE_POLICY_GAP, LEGAL_GAP)`. A later owner-provided no-login route would require a
fresh independent design review; IMF metadata cannot qualify NSO or UN observations.

## 6. World Bank candidate

The [World Bank GEM industrial-production page](https://databank.worldbank.org/embed/industrial-production/id/e351ac78)
exposes a public database view with a monthly option, and the [World Bank database catalogue](https://databank.worldbank.org/databases/page/2/orderby/date/direction/asc)
describes public industrial-production coverage. The official [Vietnam Macro Monitoring dashboard](https://documents1.worldbank.org/curated/en/099531509222524008/pdf/IDU-4f136c80-cd01-41aa-b5ba-5e81e7c7a197.pdf)
contains a Vietnam monthly industrial-production YoY chart, but it identifies its inputs as a
combination of Haver Analytics, NSO, S&P, and World Bank staff calculation. It is therefore a
secondary analytical artifact, not a direct provider-owned row source for this library.

No reviewed World Bank page proved all of: a VNM row/series code, national IIP YoY definition,
direct values, observation-month/revision identity, current requested coverage, page/totals
contract, rate policy, and redistribution permission. A public download button or monthly
selector is not a licence to redistribute an unresolved underlying series. No direct value-row
dispatch was made, and no absence is inferred.

| Axis | World Bank result |
|---|---|
| Owner/route/method | Public GEM/catalogue/dashboard pages; exact VNM provider-owned YoY row route **NOT_ESTABLISHED** |
| Status/MIME/redirect | No qualifying direct row dispatch; **NOT_PROBED** |
| Identity/measure | Dashboard presents a compiled Vietnam industrial-production YoY view; direct provider identity and raw-vs-derived provenance are unresolved |
| Coverage/revision | Exact 2018-01..2026-08 row coverage, totals, gaps, vintages and release markers **NOT_ESTABLISHED** |
| Auth/session/UA/WAF | Public page access observed; no automation permission or source-session contract established |
| Rate/retry/bytes | **NOT_ESTABLISHED**; no numeric ceiling frozen |
| Legal/redistribution | Dataset-level public visibility is not an exact commercial OSS redistribution grant for the underlying VNM series; **LEGAL_GAP** |
| Outcome | `SOURCE_GAP`, not confirmed non-service |

**World Bank disposition:** `SOURCE_GAP` with `(IDENTITY_GAP, PROVENANCE_GAP, COVERAGE_GAP,
REVISION_GAP, RUNTIME_GAP, RATE_POLICY_GAP, LEGAL_GAP)`. The dashboard remains contextual evidence
only and cannot fill an NSO or UN gap.

## 7. UN Statistics Division MBS candidate

The official [MBS technical notes](https://unstats.un.org/UNSD/mbs/app/mbsnotes.aspx) identify
Table 5 as the index of industrial production and explain that national indices may be rebased
and are generally not seasonally or working-day adjusted unless stated. The [MBS table notes](https://unstats.un.org/UNSD/mbs/tablenotes.aspx)
and the [MBS web service page](https://unstats.un.org/UNSD/mbs/api/wsMbsServices.asmx) document
official table/metadata operations and monthly period selectors. The [data viewer](https://unstats.un.org/UNSD/mbs/app/DataView.aspx)
is reachable without login in the bounded pass.

The viewer exposes a Vietnam `Industrial production - General index` family with a `2010=100`
base/rebase label. A bounded wider-window display showed the latest visible observation before
the requested period, while a bounded target-window display returned the page's no-data state.
No raw row or value is committed. This is not a provider-published YoY series. Deriving YoY locally
from an index is expressly out of scope until a separate design authorizes and specifies that
transformation; this report does not do so.

| Axis | UN MBS result |
|---|---|
| Owner/route/method | UNSD MBS viewer and documented web service, no-login GET/document route |
| Status/MIME/redirect | Viewer `200`; sanitized complete Content-Type observed as `text/html; charset=utf-8`; normalized media type `text/html`; no redirect observed in bounded viewer pass |
| Identity/measure | Vietnam industrial-production **index level**, general index, rebased label `2010=100`; not provider-published YoY |
| Coverage | Bounded target-window display had no data; wider display reached only an earlier pre-window observation; requested span is not covered by the observed unit |
| Pages/totals/revision | No provider-declared total/cursor/revision/vintage contract was established for the target unit |
| Time/seasonality/base | MBS notes provide index/rebase and adjustment context, but not the target YoY observation-month contract |
| Auth/session/UA/WAF | No login or credential used; UA necessity, crawl permission and session policy **NOT_ESTABLISHED** |
| Rate/retry/bytes | No public numeric quota, retry, or byte policy established; no numeric ceiling frozen |
| Legal/redistribution | MBS pages carry copyright/conditions-of-use language; no explicit licence for commercial OSS redistribution of this series was established |
| Outcome | `SOURCE_GAP`, not a confirmed absence of all UN data |

**UN MBS disposition:** `SOURCE_GAP` with `(MEASURE_GAP, COVERAGE_GAP, REVISION_GAP,
PAGE_TOTAL_GAP, RATE_POLICY_GAP, LEGAL_GAP)`. Its no-login transport does not overcome the wrong
measure and insufficient span.

## 8. Cross-candidate legal, runtime, and identity conclusion

No candidate has all axes below on one provider unit:

1. **Owner and route:** a stable official host/path and method, with effective route and redirect
   policy bound to the same owner.
2. **Response-backed identity:** Vietnam, national whole industry, exact IIP YoY measure, monthly
   cadence, `%` unit, and a provider series/release identifier in the response or authoritative
   machine schema. Request echo alone is insufficient.
3. **Observation semantics:** observation month distinct from release date; no local index-to-YoY
   transformation; nullability, precision/rounding, seasonal-adjustment and base/rebase semantics
   explicit; preliminary/final/revision identity typed.
4. **Coverage:** provider-served bounds and requested `2018-01-01..2026-08-19` evidence, with
   reconciled pages/cursors/totals and explicit month/calendar gaps. The candidate month keys are
   January 2018 through August 2026 (104 monthly keys) only if the source declares that monthly
   calendar; no provider total was accepted here.
5. **Runtime:** no-login or explicitly permitted access, exact status, sanitized complete
   Content-Type, normalized media type, effective route,
   bounded bytes, WAF/challenge behavior, rate/retry policy, deterministic global dispatch ledger,
   and no hidden pagination or redirect calls.
6. **Lawful reuse:** attribution, storage/cache, commercial use, retention, redistribution, and
   derivative-use rights for the exact values and route, not merely public page visibility.

The current status is therefore **not** `QUALIFIED_PARTIAL`: a narrative release family, an
index-level table, or a secondary dashboard does not provide a safely consumable partial series.
The empty chain is the fail-closed result.

## 9. Future no-false-absence and diagnostic contract

This section is design-only and is not implemented. It defines the minimum semantics a later
qualified source must satisfy without changing the current API prematurely.

### 9.1 Total outcome vocabulary

Every attempted source unit must map to exactly one bounded outcome. Unknown, empty, and failed
states are not interchangeable:

| Outcome token | Meaning | May claim historical absence? |
|---|---|---|
| `FULL` | All requested month keys are present, finite, unique, ascending, and page/total/calendar/revision checks pass | Yes, only for the reconciled request result |
| `PARTIAL` | Provider-declared supported bounds and reconciled returned pages explain an explicit requested boundary | Only the declared boundary; never the unexplained interior |
| `PUBLISHED_EMPTY` | Provider explicitly declares the requested series/month published and empty under its schema | Only that declared empty cell |
| `NOT_YET_PUBLISHED` | Provider release calendar or typed as-of metadata proves the observation is not yet published | Only the future/not-yet-published boundary |
| `MISSING_MONTH` | A complete provider calendar/total contract proves one month is absent from an otherwise reconciled published series | Only that proven gap; no fill or zero |
| `COVERAGE_BOUNDARY` | Provider-declared first/last supported observation excludes part of the request | Only the declared outside bound |
| `NOT_SERVED` | Capability, country, indicator, or interval is unsupported before network | No inference about provider history |
| `TRANSPORT_FAILURE` | Timeout, DNS/TLS, unexpected status, WAF/challenge, or connection failure | No |
| `SCHEMA_DRIFT` | Sanitized complete Content-Type/normalized media type, envelope, identity, type, or required field contract fails | No |
| `BUDGET_EXHAUSTED` | The request-scoped deterministic ledger is exhausted before a required dispatch | No |
| `LEGAL_GAP` | Technical data exists but permission/terms are not sufficient for this library | No |
| `IDENTITY_GAP` | Response or catalogue cannot prove the exact VNM national IIP YoY unit | No |

An empty HTML page, empty JSON array, timeout, 403, generic error, or missing archive page is not
`PUBLISHED_EMPTY`, `MISSING_MONTH`, or `COVERAGE_BOUNDARY` without provider-backed evidence. A
partial provider response with unreconciled page/cursor state is `SCHEMA_DRIFT` or
`TRANSPORT_FAILURE`/`COVERAGE_BOUNDARY` according to the verified failure, never `FULL`.

### 9.2 Bounded diagnostics — internal design only

The finite outcome vocabulary above is internal design-only. No new public source token, warning
field, exception, result carrier, or diagnostic shape is approved here. Current stable adapter
tokens remain `imf_datamapper` and `worldbank`; candidate labels such as `nso`, `imf`, `world_bank`,
and `un_mbs` are internal research labels, not public tokens. Current
`MacroClient.get_indicator()` behavior remains an `IndicatorSeries` result or an
`AllSourcesFailed` error carrying `SourceAttempt` records.

After a source qualifies, a separate compatibility review may decide whether finite source and
outcome fields can be projected onto that existing surface. Until then, raw URLs, query strings,
bodies, headers, cookies, exception text, arbitrary provider strings, and unbounded model text
must never appear. A missing revision/as-of field is only a future internal
`REVISION_UNAVAILABLE` warning, not a fabricated publication date. Transport, identity, legal,
schema, or budget failures do not authorize a partial `IndicatorSeries` or a new public carrier.

### 9.3 Deterministic global dispatch ledger

The future implementation must use one sequential request-scoped ledger for the whole result:

- reserve each eligible logical source attempt atomically before adapter entry;
- reserve each physical HTTP dispatch immediately before an HTTP request, including an initial
  request, page/cursor request, retry, or redirect follow-up; page/cursor labels describe the
  request and do not double-count it;
- reserve byte and decompression limits in separate local resource counters; those operations are
  not physical network dispatches and must never increment the physical HTTP counter;
- capability skips make zero physical calls, consume no attempt, and do not create a public
  attempt record;
- never reset the ledger per page, provider, or fallback source;
- on exhaustion, discard all private partial rows and record only an internal bounded
  `BUDGET_EXHAUSTED` outcome; the public exception/result carrier is deferred to a compatibility
  review. Preserve the current `IndicatorSeries`/`AllSourcesFailed` shape until then; and
- commit a result atomically only after identity, measure, coverage, revision, and legal gates
  pass for the whole provider unit.

No numeric ceiling is frozen in this source-gap note. A later owner/rate review must establish
finite logical, physical, retry, page, redirect, byte, and decompression limits from the qualified
route's policy; absence of a published policy is a `RATE_POLICY_GAP`, not unlimited budget.

## 10. Reopen criteria and release boundary

Reopen requires a fresh primary-source packet and **all** of the following conjunctively:

1. an official owner confirms one stable route/version or release-template family and real contact
   path, with no-login or explicitly permitted automation and exact status, complete Content-Type,
   normalized media type, redirect, and WAF
   behavior;
2. the same response/schema binds `VNM` to national whole-industry IIP, provider-published monthly
   YoY, `%`, exact series/release identity, observation-month convention, and nullability;
3. the provider supplies the requested span or a provider-declared partial bound with reconciled
   pages/totals/cursors, historical-vintage/revision semantics, and a complete month-gap policy;
4. rate, retry, page, redirect, byte, decompression, cache/storage, and retention behavior is
   bounded and lawful, with a deterministic global reservation ledger;
5. exact values may be used, stored, and redistributed under a clear licence or written
   permission, with attribution and commercial-OSS terms recorded; and
6. the response/error grammar is finite and sanitized, the current macro signature remains
   compatible, and an implementation packet includes the required RED matrix.

One successful page, one release value, one empty result, an index-level table, a secondary
dashboard, a guessed API path, or a third-party mirror does not reopen this closure. A future
`QUALIFIED_PARTIAL` decision must still pass all identity/legal/runtime gates and explicitly mark
the exact provider-declared boundary; it cannot silently become `FULL`.

## 11. Deferred implementation and completion sequence

No RED commit, enum/registry change, adapter, source registration, test, model, docs/API snapshot,
or CHANGELOG change is authorized by this report. If a future design instead reaches
`QUALIFIED FOR TDD` or `QUALIFIED_PARTIAL`, the next gate is a fresh RED-first implementation
packet covering the packet's API, identity, coverage, atomic budget, diagnostics, compatibility,
blacklist, secret, focused/full offline tests, and isolated build requirements.

For this **SOURCE-GAP CLOSURE** result, the only permitted next sequence after exact-SHA design
PASS is: rerun merged docs/full/build/blacklist/diff gates; push the exact approved docs range;
verify remote HEAD, ancestry, and the three approved paths; post a clean no-capability source-gap
resolution; close #219; re-read `CLOSED`/`COMPLETED`; and record local completion. No runtime
capability or future TDD is implied. Issues #220, #222, #223, and #224 remain queued and are not
activated by this note.

## 12. Source index

- [Vietnam NSO IIP archive](https://www.nso.gov.vn/en/iip/)
- [Vietnam NSO industry statistics](https://www.nso.gov.vn/en/industry/)
- [Vietnam NSO release calendar](https://www.nso.gov.vn/en/release-calendar-3/)
- [Vietnam NSO industry methodology](https://www.nso.gov.vn/en/metadata/2019/03/industry-2/)
- [Vietnam NSO Industrial and Construction Statistics Department](https://www.nso.gov.vn/en/industrial-and-construction-statistics-department/)
- [Vietnam NSO PXWeb industrial-production table](https://pxweb.nso.gov.vn/pxweb/en/Industry/Industry/E07.01.px/)
- [IMF API documentation](https://data.imf.org/en/Resource-Pages/IMF-API)
- [IMF Production Index access notes](https://data.imf.org/en/news/accessing)
- [IMF Vietnam DSBB metadata](https://dsbb.imf.org/e-gdds/country/VNM/summary-of-dissemination)
- [World Bank GEM industrial-production view](https://databank.worldbank.org/embed/industrial-production/id/e351ac78)
- [World Bank database catalogue](https://databank.worldbank.org/databases/page/2/orderby/date/direction/asc)
- [World Bank Vietnam Macro Monitoring dashboard](https://documents1.worldbank.org/curated/en/099531509222524008/pdf/IDU-4f136c80-cd01-41aa-b5ba-5e81e7c7a197.pdf)
- [UN MBS technical notes](https://unstats.un.org/UNSD/mbs/app/mbsnotes.aspx)
- [UN MBS table notes](https://unstats.un.org/UNSD/mbs/tablenotes.aspx)
- [UN MBS data viewer](https://unstats.un.org/UNSD/mbs/app/DataView.aspx)
- [UN MBS web service documentation](https://unstats.un.org/UNSD/mbs/api/wsMbsServices.asmx)

## Bottom summary

- Decision: **SOURCE-GAP CLOSURE** for #219; the new IIP YoY source chain stays empty.
- NSO is the strongest semantic lead but lacks a reconciled exact no-login monthly YoY contract.
- IMF/World Bank do not prove direct identity, coverage, revision, runtime, and reuse together.
- UN MBS is no-login but exposes an index level and does not reach the requested span.
- No false absence, local index-to-YoY derivation, fallback stitch, or capability is authorized.
- Only the requested research/design artifacts and backlog lifecycle may be committed.
- No RED, production code, push, or close before exact-SHA design PASS.
- Need from Boss: nothing; reviewer needs the exact committed SHA for design review.
