# Vietnam monthly industrial-production YoY source vetting — #219

**Research date:** 2026-08-23 (UTC+7)
**Packet:** `tasks/219-vietnam-monthly-industrial-production-yoy-spec.md` at reviewer `f2d0187`
**Phase:** source/design gate only; no runtime capability is enabled by this report
**Requested inclusive window:** `2018-01-01..2026-08-19`
**Canonical target:** `VNM` + `MacroIndicator.INDUSTRIAL_PRODUCTION_YOY`
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

The requested primitive is the existing macro surface, only if a future source qualifies:

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

The ledger distinguishes a planned logical cell from a physical dispatch. A retry, redirect
follow-up, pagination request, cursor request, or hidden parallel call would be a separate
physical dispatch. `NOT_PROBED` and `NOT_ESTABLISHED` mean unresolved evidence, never confirmed
non-service or historical absence.

| Evidence cell | Logical / physical dispatches | Retries | Pages/cursors | Transport observation | Retained evidence |
|---|---:|---:|---:|---|---|
| NSO IIP archive index and sampled archive pages | 8 / 8 | 0 | 8 page requests, no cursor contract | `200`; HTML; normalized MIME observed as `text/html; charset=UTF-8`; no redirect was observed in the bounded pass | shape/date/title metadata only; no body or values |
| NSO release calendar | 1 / 1 | 0 | 1 | `200`; HTML; normalized MIME observed as `text/html; charset=UTF-8` | route/date metadata only |
| NSO individual release-document family | bounded reads of selected 2018, 2020, 2023, and 2026 releases; per-document runtime ledger not retained | 0 recorded | no machine pagination | HTML release pages rendered; no API contract or complete MIME ledger retained | title/date/semantic metadata only; no values |
| NSO PXWeb UI plus three no-credential API-path candidates | 4 / 4 | 0 | no data page/cursor reached | UI page rendered in browser context; the bounded shell UI/API attempts timed out; no response MIME/status was accepted for the timed-out API attempts | table metadata only |
| IMF catalogue/API documentation and DSBB metadata | 0 data dispatches | 0 | none | documentation/catalogue evidence only; no qualifying data route was called | public metadata and access/legal gaps |
| World Bank GEM/catalogue/dashboard material | 0 direct row dispatches | 0 | no reconciled VNM row page | public catalogue/dashboard material only; no exact qualifying row route was called | dataset-level metadata only |
| UN MBS viewer, table notes, technical notes, and web-service documentation | 2 bounded viewer dispatches; documentation reads separate | 0 | 2 viewer windows; no cursor contract established | viewer `200`; HTML UTF-8; normalized MIME observation `text/html; charset=utf-8`; no redirect was observed in the bounded viewer pass | shape, series-label, and coverage metadata only; no values |

The ledger is research evidence, not a future runtime quota. It does not turn an HTML page into a
series, and it does not support a false absence claim when a route timed out or returned no rows.

## 4. Official Vietnam NSO/GSO candidate

### 4.1 Owner, identity, and semantic evidence

The official [NSO IIP archive](https://www.nso.gov.vn/en/iip/) is a monthly release index. As
observed on the research date, it listed recent monthly releases through July 2026 and older
monthly releases through the archive pagination. The [NSO industry statistics page](https://www.nso.gov.vn/en/industry/)
lists official industrial-production tables and the [release calendar](https://www.nso.gov.vn/en/release-calendar-3/)
provides the publication-calendar route. Individual official releases from the requested era and
recent years are clearly monthly IIP releases. Their narrative semantics distinguish the overall
industry comparison with the same period of the previous year from other monthly, cumulative,
sector, and annual statements. This establishes a strong owner and concept lead, not a machine
row contract.

The official [industry methodology](https://www.nso.gov.vn/en/metadata/2019/03/industry-2/)
describes IIP as a production-growth measure aggregated to whole industry and other levels and
explains the use of the same period of the previous year and the previous period as comparison
bases. It does not, by itself, publish a stable exact VNM monthly YoY series with row identity,
revision ID, nullability, page totals, and redistribution terms. The release pages also use
estimated/preliminary language in the monthly context; a typed preliminary/final/revised vintage
contract was not established.

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
| Status/MIME/redirect | Viewer `200`, HTML UTF-8; normalized MIME observed as `text/html; charset=utf-8`; no redirect observed in bounded viewer pass |
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
5. **Runtime:** no-login or explicitly permitted access, exact status/full MIME/effective route,
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
| `SCHEMA_DRIFT` | Full MIME, envelope, identity, type, or required field contract fails | No |
| `BUDGET_EXHAUSTED` | The request-scoped deterministic ledger is exhausted before a required dispatch | No |
| `LEGAL_GAP` | Technical data exists but permission/terms are not sufficient for this library | No |
| `IDENTITY_GAP` | Response or catalogue cannot prove the exact VNM national IIP YoY unit | No |

An empty HTML page, empty JSON array, timeout, 403, generic error, or missing archive page is not
`PUBLISHED_EMPTY`, `MISSING_MONTH`, or `COVERAGE_BOUNDARY` without provider-backed evidence. A
partial provider response with unreconciled page/cursor state is `SCHEMA_DRIFT` or
`TRANSPORT_FAILURE`/`COVERAGE_BOUNDARY` according to the verified failure, never `FULL`.

### 9.2 Bounded public diagnostics

If a future source qualifies, public diagnostics may expose only a finite source token and finite
outcome/warning fields, for example `source=nso`, `outcome=COVERAGE_BOUNDARY`, and integer logical,
physical, page, retry, and byte counters within the request ledger. The exact public shape must be
reviewed against the existing `IndicatorSeries` compatibility surface before implementation.
Raw URLs, query strings, bodies, headers, cookies, exception text, provider names not in the
allow-list, arbitrary response strings, and unbounded model text must never appear. A missing
revision/as-of field is a bounded `REVISION_UNAVAILABLE` warning, not a fabricated publication
date. Diagnostics are warnings only when the returned series remains fully valid; transport,
identity, legal, schema, or budget failures return no partial `IndicatorSeries`.

### 9.3 Deterministic global dispatch ledger

The future implementation must use one sequential request-scoped ledger for the whole result:

- reserve each eligible logical source attempt atomically before adapter entry;
- reserve each physical HTTP dispatch immediately before network, including every page, cursor,
  retry, redirect follow-up, or bounded decompression/byte operation;
- capability skips make zero physical calls, consume no attempt, and do not create a public
  attempt record;
- never reset the ledger per page, provider, or fallback source;
- on exhaustion, discard all private partial rows and return one bounded `BUDGET_EXHAUSTED`
  diagnostic, preserving only previously sanitized attempts if the reviewed public contract later
  provides such a field; and
- commit a result atomically only after identity, measure, coverage, revision, and legal gates
  pass for the whole provider unit.

No numeric ceiling is frozen in this source-gap note. A later owner/rate review must establish
finite logical, physical, retry, page, redirect, byte, and decompression limits from the qualified
route's policy; absence of a published policy is a `RATE_POLICY_GAP`, not unlimited budget.

## 10. Reopen criteria and release boundary

Reopen requires a fresh primary-source packet and **all** of the following conjunctively:

1. an official owner confirms one stable route/version or release-template family and real contact
   path, with no-login or explicitly permitted automation and exact full-MIME/status/redirect/WAF
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
