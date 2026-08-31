# #235 North America five-economy macro coverage

**Research date:** 31 August 2026 (+07)
**Phase:** `SOURCE_DESIGN` — design review requested; no runtime change
**Packet:** `tasks/235-north-america-macro-cohort-spec.md` at reviewer anchor `acbbb82`
**Public triage receipt:** `issuecomment-5477977514`
**Published base used for this handoff:** `origin/master` at `472cfe6d42ba43ab535a2ff676220896d5aaaacd`
**Scope:** source, legal, coverage, and API-boundary evidence only. No provider request, raw-row retention,
source registration, RED test, API/model change, production code, push, or issue closure was performed.

## Executive disposition

**Aggregate outcome: `PARTIAL_COHORT`.** The existing country-generic World Bank path has durable,
response-backed evidence for the five Canada annual cells already approved under #200, and older
research contains bounded USA examples. The remaining cells are not promoted from a syntactically
routable country code or a generic dataset page. They remain `NOT_PROBED`, with the USA policy-rate
cell at `SEMANTICS_GAP` because the current display contract names an SBV proxy. This is a useful
coverage inventory, not a claim that the five-country × ten-indicator panel is available.

No new source qualifies for an API/RED decision in this note. The existing public primitive remains:

```python
vnfin.macro.get_indicator(country_iso3, indicator) -> IndicatorSeries
```

The cohort is documentation/test scope only. There is no ranking/report/batch API, no dynamic cohort
lookup, and no runtime substitution. A missing, null, unobserved, legally uncleared, or unverified
cell stays missing/unknown; it is never zero-filled, forward-filled, interpolated, ranked away, or
relabelled from another frequency, country, unit, or rate concept.

## Clean-room and evidence rules

Before this research I read `docs/vnstock-blacklist.md`. Every web search used the required exclusion:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted package, repository, site, documentation, endpoint map, schema, fixture, or behavior
was opened, cited, compared, or used. The research used only official UN, World Bank, IMF, and
DBnomics-owner/operator pages plus already-retained repository evidence from the approved #200
macro work. No third-party ranking or wrapper was used.

Existing retained evidence and new static evidence are kept separate:

- The #200 retained live-probe summary says that the current country-generic World Bank path returned
  Canada GDP, GDP growth, CPI, inflation, and unemployment with **66, 65, 66, 66, and 35 points**
  respectively. The approved regression tests in `tests/test_macro_worldbank.py` are synthetic
  fixtures: they prove the parser/code path, not current provider availability.
- The older global macro report records bounded USA WDI examples, including USA CPI with 65
  non-null annual observations from 1960 through 2024 and example GDP/inflation responses. Those
  examples are not enlarged into a full ten-cell or current-date claim here.
- No #235 provider dispatch was made. Thus every row without an explicit retained response reference
  is `NOT_PROBED`; its route is not evidence of observations, bounds, or rights.

Raw provider bodies, headers, cookies, credentials, and real row values are not added to this report.
Illustrative cohort values below are the already-retained official-query findings in the reviewer
brief, not a new runtime data capability.

## Geography and frozen cohort

The geography is **UN M49 North America `003`**, intersected with the official UN Member States list.
M49 is a statistical classification, not a political-affiliation or sovereignty rule. The resulting
23-country ISO3 universe is:

```text
ATG BHS BRB BLZ CAN CRI CUB DMA DOM GRD GTM HND HTI
JAM KNA LCA MEX NIC PAN SLV TTO USA VCT
```

The official references are the [UN M49 methodology](https://unstats.un.org/unsd/methodology/m49/)
and the [UN Member States list](https://www.un.org/about-us/member-states).

Rank the universe only by World Bank WDI `NY.GDP.MKTP.CD`, **GDP (current US$)**, in one common
year. The latest strict common year retained by the packet is **2020**:

| Rank | Economy | ISO3 | 2020 GDP, current US$ |
|---:|---|---|---:|
| 1 | United States | `USA` | `21,375,281,000,000` |
| 2 | Canada | `CAN` | `1,655,686,966,881.99` |
| 3 | Mexico | `MEX` | `1,121,064,767,168.8` |
| 4 | Cuba | `CUB` | `107,352,000,000` |
| 5 | Dominican Republic | `DOM` | `78,546,672,406.8291` |

The retained reproducible [official 2020 WDI query](https://api.worldbank.org/v2/country/ATG%3BBHS%3BBRB%3BBLZ%3BCAN%3BCRI%3BCUB%3BDMA%3BDOM%3BGRD%3BGTM%3BHND%3BHTI%3BJAM%3BKNA%3BLCA%3BMEX%3BNIC%3BPAN%3BSLV%3BTTO%3BUSA%3BVCT/indicator/NY.GDP.MKTP.CD?date=2020&format=json&per_page=100)
binds the code, year, and unit. The five-member cohort is frozen as `USA/CAN/MEX/CUB/DOM`; future
WDI revisions must not silently change it.

For freshness only, the packet retains this **incomplete 2025 available-case appendix**:

| Rank among non-null 2025 observations | Economy | ISO3 | 2025 GDP, current US$ |
|---:|---|---|---:|
| 1 | United States | `USA` | `30,769,700,000,000` |
| 2 | Canada | `CAN` | `2,319,899,772,425.92` |
| 3 | Mexico | `MEX` | `1,832,641,364,775.52` |
| 4 | Dominican Republic | `DOM` | `127,407,463,759.043` |
| 5 | Guatemala | `GTM` | `123,306,008,821.471` |

The [official 2025 WDI query](https://api.worldbank.org/v2/country/ATG%3BBHS%3BBRB%3BBLZ%3BCAN%3BCRI%3BCUB%3BDMA%3BDOM%3BGRD%3BGTM%3BHND%3BHTI%3BJAM%3BKNA%3BLCA%3BMEX%3BNIC%3BPAN%3BSLV%3BTTO%3BUSA%3BVCT/indicator/NY.GDP.MKTP.CD?date=2025&format=json&per_page=100)
has null Cuba and The Bahamas in the retained evidence. Therefore this appendix is not a ranking
of the full universe: it must not replace Cuba with Guatemala, imply Guatemala outranks unobserved
Cuba, or become runtime membership.

## Provider and legal evidence

### World Bank WDI — annual primary route

| Axis | Bound in this design |
|---|---|
| Owner/operator | World Bank / `api.worldbank.org` Indicators API v2 |
| Route/method | `GET https://api.worldbank.org/v2/country/{ISO3}/indicator/{CODE}?format=json&per_page={N}&date={Y1}:{Y2}`; one country or a semicolon-separated country set; provider concept code stays in the path |
| Response identity | Expected `countryiso3code`, `indicator.id`, `date`, `value`, `unit`; a syntactically valid ISO3 or code is not response identity |
| Transport | JSON envelope `[meta, observations]`; status, complete `Content-Type`, redirect final identity, and TLS outcome must be retained by any future probe; no #235 dispatch occurred |
| Auth/session | No API key/token is documented for the public v2 route; future requests use no cookies, login, or session; no credentials are stored |
| Provider history | Official API documentation describes date filters, multi-country/multi-indicator calls, pagination, and a documented 60-indicator limit; this does not prove any cell's returned observations |
| Terms | World Bank-produced open datasets default to CC BY 4.0 with attribution, but the [public-licenses page](https://datacatalog.worldbank.org/public-licenses) also warns that additional dataset-specific and third-party restrictions can apply. No new redistribution grant is inferred. |
| Runtime/cache | Existing `vnfin` fetches rows on demand and returns `IndicatorSeries`; no #235 body/header bundle, cache, or dataset is added. A future extension must retain only permitted metadata and attribution unless terms expressly allow storage/redistribution. |

The relevant primary pages are the [indicator API query documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries),
[API basic call structures](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures),
and [WDI API overview](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392).

### IMF IFS via DBnomics — monthly candidate route

| Axis | Bound in this design |
|---|---|
| Owner/operator | Underlying owner: IMF IFS; route operator: DBnomics |
| Route/method | `GET https://api.db.nomics.world/v22/series/IMF/IFS/{FREQ}.{CC}.{IFS_CODE}?observations=1`; current adapter uses `M.{CC}.PCPI_PC_CP_A_PT` for CPI YoY and `M.{CC}.FPOLM_PA` for policy-rate-like data |
| Auth/session | Current documented route is no-key; no login, cookies, or payment are authorized for this design |
| Identity | DBnomics series identity must carry exact frequency, IMF country code, and IFS concept. A working URL alone is not proof that the concept is the country's official rate or that the returned country is the requested ISO3 |
| Status/MIME/coverage | No #235 response was dispatched or retained. Exact dimensions, row count, first/last period, nulls, gaps, revisions, and final MIME remain unobserved for all five-country monthly cells |
| Terms | DBnomics publishes an ODbL/operator context, while upstream IMF data remains subject to IMF terms; the [DBnomics IMF provider page](https://db.nomics.world/IMF) links to the [IMF terms](http://datahelp.imf.org/tos). Do not bundle or redistribute rows without exact applicable permission. |
| Current-code hazard | `vnfin/macro/dbnomics.py` displays `POLICY_RATE` as an **SBV refinancing-rate proxy**. That label is not valid for North America; the USA policy cell is therefore a `SEMANTICS_GAP`, not a proven US policy rate. |

The static [IMF IFS dataset page](https://db.nomics.world/IMF/IFS?tab=table) exposes dataset
dimensions, but it is not retained response proof for a particular country/concept cell.

### IMF DataMapper fallback

The current no-key chain also contains the IMF DataMapper for selected annual percentage concepts:
`NGDP_RPCH` (real GDP growth), `PCPIPCH` (CPI inflation), and `LUR` (unemployment). It emits
annual WEO values and can mix projections; the existing model uses `projection_from_year` to keep
future values out of `latest()`. It is not used to fill the matrix by inference. Its distinct unit,
projection, identity, and IMF terms must be re-verified in any future cell qualification; no new
route or fallback is introduced here.

## Current repository/API boundary

The current `MacroIndicator` enum has exactly ten members in
`vnfin/macro/indicators.py:39-59`:

```text
GDP, GDP_GROWTH, CPI, INFLATION, UNEMPLOYMENT,
CPI_YOY, POLICY_RATE, LENDING_RATE, DEPOSIT_RATE, REAL_INTEREST_RATE
```

The World Bank map in `vnfin/macro/worldbank.py:55-71` contains eight annual concepts:

| Canonical indicator | Exact WDI concept | Frequency | Unit | Currency | Semantics |
|---|---|---|---|---|---|
| `GDP` | `NY.GDP.MKTP.CD` | annual | `current US$` | `USD` | nominal GDP level |
| `GDP_GROWTH` | `NY.GDP.MKTP.KD.ZG` | annual | `%` | none | real GDP growth, annual percent |
| `CPI` | `FP.CPI.TOTL` | annual | `index` | none | CPI index level, not inflation |
| `INFLATION` | `FP.CPI.TOTL.ZG` | annual | `%` | none | CPI inflation, annual percent |
| `UNEMPLOYMENT` | `SL.UEM.TOTL.ZS` | annual | `%` | none | unemployment share of labour force |
| `LENDING_RATE` | `FR.INR.LEND` | annual | `%` | none | aggregate lending rate, percent p.a. |
| `DEPOSIT_RATE` | `FR.INR.DPST` | annual | `%` | none | aggregate deposit rate, not a tenor curve |
| `REAL_INTEREST_RATE` | `FR.INR.RINR` | annual | `%` | none | real interest rate, may be negative |

The DBnomics map in `vnfin/macro/dbnomics.py:75-82` contains monthly `CPI_YOY` and `POLICY_RATE`
concepts, with the explicit ISO3 map currently including `USA` but not `CAN`, `MEX`, `CUB`, or
`DOM`. A map entry is a route declaration, not coverage proof.

`MacroClient` (`vnfin/macro/client.py:172-231`) validates ISO3 and indicator before dispatch,
pre-filters sources by canonical unit, skips incapable sources without a network call, then runs the
existing failover chain. It has a bounded caller-configurable `max_attempts` default of three but
no #235-specific batch budget or cache. `IndicatorSeries` (`vnfin/macro/models.py:33-119`) is frozen,
uses `(date, value)` points, carries `source`, `unit`, `value_unit`, `currency`, `frequency`,
`projection_from_year`, `fetched_at_utc`, and `warnings`; `to_dataframe()` adds `is_projection` and
metadata in `df.attrs`. `fetched_at_utc` is retrieval provenance, not an observation/publication
date. No coverage object or ranking state is added.

Two existing documentation drifts are recorded but deliberately not edited in this source-design
packet: `docs/api.md:164` omits `CPI` from its inline list, and
`docs/sources/macro-dbnomics.md:5` still describes DBnomics as the only default CPI-index source.
They are implementation/docs follow-ups only, not evidence of a new capability.

## 5 × 10 cell matrix

### Matrix conventions

Every row below is one independent `(country, canonical indicator)` cell. No row inherits an
observation, bound, legal decision, or response identity from another row.

- `WB` means the exact World Bank route and concept shown in that row; `DBN/IMF` means the exact
  DBnomics/IMF IFS series template shown in that row. `GET` is the proposed provider method, not a
  #235 dispatch.
- `NOT_PROBED` means no response was requested for that cell: status, complete MIME, redirects,
  returned identity, count, first/last observation, null/gap pattern, revision, and transport result
  are all `NOT_OBSERVED`, not zero or empty.
- `CAN/#200` is the retained #200 live-probe summary only. Its counts are response-backed; its
  per-cell first/last dates and full header/terms receipt were not retained in that handoff. The
  synthetic CAN tests are not substituted for this evidence.
- `USA/old-report` means the bounded response evidence in the 18 June global macro report. It is
  `PARTIAL` where an example or narrower retained span exists, never full-cohort proof.
- For all WB rows, `actual/projection` is `published annual observation; provider-level projection
  flag not retained; current WB adapter stamps no projection boundary`. For DBN rows it is
  `published monthly period; no projection flag retained`. A future IMF WEO fallback must preserve
  its separate projection boundary and cannot be merged silently.
- All percent/index cells have `currency=None`; only GDP has `currency="USD"`. No row may use the
  shared SBV policy-rate display text outside Vietnam.

| Cell | Exact provider concept, owner/operator, route and method | Frequency · unit · currency · semantic · actual/projection | Response identity, transport and auth/session | Count, bounds, gaps, revisions and legal/cache evidence | Outcome |
|---|---|---|---|---|---|
| `USA × GDP` | WB / World Bank / `GET https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `current US$` · USD · nominal GDP level · published annual, projection flag not retained | `USA/old-report` returned a GDP example; no #235 response; expected country=`USA`, indicator=`NY.GDP.MKTP.CD`; historical status/MIME/redirect/session receipt not retained; no auth | Example observation exists but full count/bounds, nulls, revisions, and current lag are not retained; WB default CC BY candidate with dataset/third-party caveat; existing on-demand `IndicatorSeries`, no new body/cache ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `PARTIAL` |
| `USA × GDP_GROWTH` | WB / World Bank / `GET https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real GDP growth, not GDP level · published annual, projection flag not retained | No retained exact USA response for this cell in the cited evidence; no status/MIME/redirect/identity/session; no auth | Count/bounds/nulls/gaps/revisions not observed; WDI legal candidate only, no new redistribution claim; no #235 cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `USA × CPI` | WB / World Bank / `GET https://api.worldbank.org/v2/country/USA/indicator/FP.CPI.TOTL?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `index` · none · CPI level, not inflation · published annual, projection flag not retained | Retained global report records USA 65 non-null observations for 1960–2024; exact country/code identity is the WDI route; no #235 dispatch or complete status/MIME/redirect receipt; no auth | Observed count=65, first=1960, last=2024 in older retained report; current gap/revisions/terms receipt not re-established; no new cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `PARTIAL` |
| `USA × INFLATION` | WB / World Bank / `GET https://api.worldbank.org/v2/country/USA/indicator/FP.CPI.TOTL.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · CPI YoY inflation, not CPI level · published annual, projection flag not retained | Older report retains USA examples for 2022 and 2023; exact route identity is code-bound; no #235 status/MIME/redirect/session receipt; no auth | Example response only; complete count/bounds/null/revision/current-lag not retained; WDI terms remain candidate with caveat; no body/cache added ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `PARTIAL` |
| `USA × UNEMPLOYMENT` | WB / World Bank / `GET https://api.worldbank.org/v2/country/USA/indicator/SL.UEM.TOTL.ZS?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · labour-force unemployment share, bounded 0–100 · published annual, projection flag not retained | Older global report says the multi-country response included USA unemployment, but no exact per-cell response receipt is retained here; no #235 status/MIME/redirect/session; no auth | Exact count/bounds/null/gaps/revisions/current lag not retained; no new legal/cache claim ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `PARTIAL` |
| `USA × CPI_YOY` | DBN/IMF / IMF owns concept, DBnomics operates route / `GET https://api.db.nomics.world/v22/series/IMF/IFS/M.US.PCPI_PC_CP_A_PT?observations=1` | monthly · `%` · none · CPI change versus same month prior year, not annual WDI inflation · published monthly, projection flag not retained | Route is mechanically mapped in current code, but no response was requested for #235; returned identity/status/MIME/redirect/session/count are not observed; no auth | No date bounds/null/gap/revision receipt; IMF/DBnomics terms require exact downstream review; no raw/cache data ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `USA × POLICY_RATE` | DBN/IMF / IMF owns IFS, DBnomics operates route / `GET https://api.db.nomics.world/v22/series/IMF/IFS/M.US.FPOLM_PA?observations=1` | monthly · `% per annum` · none · monetary-policy-related rate only; not proven announced US policy rate · published monthly, projection flag not retained | No #235 response; current public display override says `SBV refinancing-rate proxy`, which contradicts North American identity; no status/MIME/redirect/session; no auth | Exact US concept/authority, count/bounds/nulls/revisions, and terms not proven; no cache/body ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `SEMANTICS_GAP` |
| `USA × LENDING_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/USA/indicator/FR.INR.LEND?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate lending rate, not policy rate · published annual, projection flag not retained | No #235 response or returned identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI legal candidate only; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `USA × DEPOSIT_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/USA/indicator/FR.INR.DPST?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate deposit rate, not a tenor curve · published annual, projection flag not retained | No #235 response or returned identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI legal candidate only; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `USA × REAL_INTEREST_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/USA/indicator/FR.INR.RINR?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real interest rate, may be negative · published annual, projection flag not retained | No #235 response or returned identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI legal candidate only; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CAN × GDP` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CAN/indicator/NY.GDP.MKTP.CD?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `current US$` · USD · nominal GDP level · published annual, projection flag not retained | `CAN/#200`: response-backed existing path, expected country=`CAN`, code exact; historical status/MIME/redirect/session details not retained; no auth | Retained count=66; exact first/last/null/gap/revision/current-lag receipt not retained; existing WDI route/terms, no new cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `PROVEN_EXISTING` |
| `CAN × GDP_GROWTH` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CAN/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real GDP growth · published annual, projection flag not retained | `CAN/#200`: response-backed existing path, country/code expected exact; status/MIME/redirect/session details not retained; no auth | Retained count=65; first/last/null/gap/revision/current-lag not retained; WDI terms/cache boundary as above ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `PROVEN_EXISTING` |
| `CAN × CPI` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CAN/indicator/FP.CPI.TOTL?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `index` · none · CPI level, not inflation · published annual, projection flag not retained | `CAN/#200`: response-backed existing path, country/code expected exact; status/MIME/redirect/session details not retained; no auth | Retained count=66; first/last/null/gap/revision/current-lag not retained; WDI terms/cache boundary as above ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `PROVEN_EXISTING` |
| `CAN × INFLATION` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CAN/indicator/FP.CPI.TOTL.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · CPI YoY inflation · published annual, projection flag not retained | `CAN/#200`: response-backed existing path, country/code expected exact; status/MIME/redirect/session details not retained; no auth | Retained count=66; first/last/null/gap/revision/current-lag not retained; WDI terms/cache boundary as above ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `PROVEN_EXISTING` |
| `CAN × UNEMPLOYMENT` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CAN/indicator/SL.UEM.TOTL.ZS?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · labour-force unemployment share, 0–100 boundary · published annual, projection flag not retained | `CAN/#200`: response-backed existing path, country/code expected exact; status/MIME/redirect/session details not retained; no auth | Retained count=35; first/last/null/gap/revision/current-lag not retained; WDI terms/cache boundary as above ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `PROVEN_EXISTING` |
| `CAN × CPI_YOY` | DBN/IMF / IMF owns concept, DBnomics operates route / no current `CAN` IFS map; candidate would be `GET https://api.db.nomics.world/v22/series/IMF/IFS/M.{CC}.PCPI_PC_CP_A_PT?observations=1` only after exact CC is proven | monthly · `%` · none · monthly CPI YoY, not annual WDI inflation · published monthly, projection flag not retained | No exact CAN country/concept response, status/MIME/redirect/session, or dimension proof; no auth | No count/bounds/null/gap/revision/rights receipt; generic IFS possibility is not a source qualification; no cache/body ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CAN × POLICY_RATE` | DBN/IMF / IMF owns concept, DBnomics operates route / no current `CAN` map; candidate `https://api.db.nomics.world/v22/series/IMF/IFS/M.{CC}.FPOLM_PA?observations=1` is not an announced-rate proof | monthly · `% per annum` · none · monetary-policy-related rate only · published monthly, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth; no SBV label may be reused | No exact authority, count/bounds/null/gap/revision/terms; no cache/body ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CAN × LENDING_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CAN/indicator/FR.INR.LEND?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate lending rate · published annual, projection flag not retained | No #200 response for this rate; no returned identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not retained; route/terms candidate only; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CAN × DEPOSIT_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CAN/indicator/FR.INR.DPST?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate deposit rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not retained; route/terms candidate only; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CAN × REAL_INTEREST_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CAN/indicator/FR.INR.RINR?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real interest rate, may be negative · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not retained; route/terms candidate only; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × GDP` | WB / World Bank / `GET https://api.worldbank.org/v2/country/MEX/indicator/NY.GDP.MKTP.CD?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `current US$` · USD · nominal GDP level · published annual, projection flag not retained | No response; returned country/code, status/MIME/redirect/session not observed; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × GDP_GROWTH` | WB / World Bank / `GET https://api.worldbank.org/v2/country/MEX/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real GDP growth · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × CPI` | WB / World Bank / `GET https://api.worldbank.org/v2/country/MEX/indicator/FP.CPI.TOTL?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `index` · none · CPI level · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × INFLATION` | WB / World Bank / `GET https://api.worldbank.org/v2/country/MEX/indicator/FP.CPI.TOTL.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · CPI YoY inflation · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × UNEMPLOYMENT` | WB / World Bank / `GET https://api.worldbank.org/v2/country/MEX/indicator/SL.UEM.TOTL.ZS?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · labour-force unemployment share, 0–100 · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × CPI_YOY` | DBN/IMF / IMF owns concept, DBnomics operates route / candidate `M.{CC}.PCPI_PC_CP_A_PT?observations=1` only after exact MEX dimension proof | monthly · `%` · none · CPI YoY · published monthly, projection flag not retained | No exact country/concept response or transport identity; no auth | No count/bounds/null/gap/revision/rights receipt; no substitution from annual inflation; no cache/body ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × POLICY_RATE` | DBN/IMF / IMF owns concept, DBnomics operates route / candidate `https://api.db.nomics.world/v22/series/IMF/IFS/M.{CC}.FPOLM_PA?observations=1` only after exact MEX concept/authority proof | monthly · `% per annum` · none · policy-like rate, not assumed announced rate · published monthly, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | No exact authority/count/bounds/null/gaps/revisions/terms; no SBV label; no cache/body ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × LENDING_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/MEX/indicator/FR.INR.LEND?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate lending rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × DEPOSIT_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/MEX/indicator/FR.INR.DPST?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate deposit rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `MEX × REAL_INTEREST_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/MEX/indicator/FR.INR.RINR?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real interest rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × GDP` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CUB/indicator/NY.GDP.MKTP.CD?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `current US$` · USD · nominal GDP level · published annual, projection flag not retained | No #235 response/identity/status/MIME/redirect/session; no auth | 2020 value is retained for cohort ranking, but this matrix cell's series count/bounds/null/gaps/revisions/current lag were not audited; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × GDP_GROWTH` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CUB/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real GDP growth · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × CPI` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CUB/indicator/FP.CPI.TOTL?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `index` · none · CPI level · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × INFLATION` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CUB/indicator/FP.CPI.TOTL.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · CPI YoY inflation · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × UNEMPLOYMENT` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CUB/indicator/SL.UEM.TOTL.ZS?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · labour-force unemployment share · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × CPI_YOY` | DBN/IMF / IMF owns concept, DBnomics operates route / candidate `M.{CC}.PCPI_PC_CP_A_PT?observations=1` only after exact CUB dimension proof | monthly · `%` · none · CPI YoY · published monthly, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | No count/bounds/null/gaps/revisions/terms; no annual substitution or fill; no cache/body ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × POLICY_RATE` | DBN/IMF / IMF owns concept, DBnomics operates route / candidate `https://api.db.nomics.world/v22/series/IMF/IFS/M.{CC}.FPOLM_PA?observations=1` only after exact CUB concept/authority proof | monthly · `% per annum` · none · policy-like rate only · published monthly, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | No exact authority/count/bounds/null/gaps/revisions/terms; no SBV label; no cache/body ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × LENDING_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CUB/indicator/FR.INR.LEND?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate lending rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × DEPOSIT_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CUB/indicator/FR.INR.DPST?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate deposit rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `CUB × REAL_INTEREST_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/CUB/indicator/FR.INR.RINR?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real interest rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × GDP` | WB / World Bank / `GET https://api.worldbank.org/v2/country/DOM/indicator/NY.GDP.MKTP.CD?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `current US$` · USD · nominal GDP level · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | 2020 value is retained for cohort ranking, but series count/bounds/null/gaps/revisions/current lag are not retained; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × GDP_GROWTH` | WB / World Bank / `GET https://api.worldbank.org/v2/country/DOM/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real GDP growth · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × CPI` | WB / World Bank / `GET https://api.worldbank.org/v2/country/DOM/indicator/FP.CPI.TOTL?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `index` · none · CPI level · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × INFLATION` | WB / World Bank / `GET https://api.worldbank.org/v2/country/DOM/indicator/FP.CPI.TOTL.ZG?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · CPI YoY inflation · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × UNEMPLOYMENT` | WB / World Bank / `GET https://api.worldbank.org/v2/country/DOM/indicator/SL.UEM.TOTL.ZS?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · labour-force unemployment share · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × CPI_YOY` | DBN/IMF / IMF owns concept, DBnomics operates route / candidate `M.{CC}.PCPI_PC_CP_A_PT?observations=1` only after exact DOM dimension proof | monthly · `%` · none · CPI YoY · published monthly, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | No count/bounds/null/gaps/revisions/terms; no annual substitution/fill; no cache/body ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × POLICY_RATE` | DBN/IMF / IMF owns concept, DBnomics operates route / candidate `https://api.db.nomics.world/v22/series/IMF/IFS/M.{CC}.FPOLM_PA?observations=1` only after exact DOM concept/authority proof | monthly · `% per annum` · none · policy-like rate only · published monthly, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | No exact authority/count/bounds/null/gaps/revisions/terms; no SBV label; no cache/body ; terms_version=DBnomics IMF-provider page + linked IMF TOS observed 2026-08-31; automation=current no-key route; caller_return=IndicatorSeries only after identity; cache/storage=#235 none; retention/deletion=no rows/bundle; commercial/derivative/redistribution=NOT_CLEARED for upstream IMF rows; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × LENDING_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/DOM/indicator/FR.INR.LEND?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate lending rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × DEPOSIT_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/DOM/indicator/FR.INR.DPST?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · aggregate deposit rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |
| `DOM × REAL_INTEREST_RATE` | WB / World Bank / `GET https://api.worldbank.org/v2/country/DOM/indicator/FR.INR.RINR?format=json&per_page={N}&date={Y1}:{Y2}` | annual · `%` · none · real interest rate · published annual, projection flag not retained | No response/identity/status/MIME/redirect/session; no auth | Count/bounds/null/gaps/revisions/current lag not observed; WDI terms candidate; no cache/body ; terms_version=World Bank public-licenses page observed 2026-08-31; effective_dataset_terms=NOT_RETAINED; automation=existing runtime; caller_return=IndicatorSeries; cache/storage=#235 none; retention/deletion=no body/bundle; commercial/derivative/redistribution=NO_NEW_GRANT; amendment/revocation=NOT_RETAINED | `NOT_PROBED` |

**Matrix count:** 50 independent cells = 5 `PROVEN_EXISTING` + 4 `PARTIAL` + 1
`SEMANTICS_GAP` + 40 `NOT_PROBED`. The count is an evidence disposition, not a success rate and
not a coverage assertion. The five `CAN/#200` cells are existing behavior; they do not imply the
other five Canada indicators, the other four countries, or current 2026 bounds.

## Bounded no-network and future observation plan

The plan below is written for a later, separately reviewed observation. It was **not activated** for
#235, so no provider dispatch occurred.

### WDI plan (not dispatched)

- At most one logical and one physical no-retry multi-country request for the five frozen countries,
  eight WDI annual concepts, and `1960:2025`; the maximum logical cell envelope is `5 × 8 × 66 =
  2,640` country-indicator-year positions, including nulls.
- Sequential only; 25-second timeout; no cookies/session/credentials; no redirect except an
  owner-host-preserving final identity; no raw body/header retention and no row/value publication.
- Before using any row, reconcile provider `page/pages/per_page/total` and the returned country/code
  identity. A page/total mismatch, wrong MIME, HTML/WAF, unexpected redirect, timeout, malformed
  envelope, identity mismatch, byte exhaustion, or late failure invalidates the whole observation;
  it cannot yield a partial series.
- The future request must bind finite compressed and decompressed byte ceilings before dispatch. No
  source-backed byte ceilings were retained in this static pass, so this plan remains unactivated.

### DBnomics/IMF monthly plan (not dispatched)

- At most eight logical and eight physical no-retry candidate observations for `CAN/MEX/CUB/DOM ×
  (CPI_YOY, POLICY_RATE)`, sequential, one request per candidate, 25-second timeout, no unbounded
  pagination, and no raw rows.
- Dispatch requires official dataset dimensions to prove the exact country/concept path and a terms
  review that permits the intended on-demand use. It must not infer that `FPOLM_PA` is an announced
  national policy rate.
- A future observation retains only sanitized final URL template/version, status and complete MIME,
  response-backed owner/country/concept identity, count/bounds/null/gap/revision facts, and the
  logical/physical/bytes ledger. Any source, identity, transport, legal, or budget failure yields no
  cell result.

The total candidate ceiling is therefore **9 logical / 9 physical, zero retries**, but the ceiling is
not a license to dispatch. Until finite byte limits and exact terms are bound, the correct status is
`NOT_PROBED`.

## API, missingness, and atomicity contract

The source-design decision is **no new public API/model**. Preserve the current
`get_indicator(ISO3, MacroIndicator)` and frozen `IndicatorSeries` contract. Do not add a ranking
helper, country dashboard, batch convenience method, coverage object, dynamic cohort, source map,
or country-specific production branch in #235.

For any future implementation decision:

1. Validate caller ISO3 and indicator before cache/network. A malformed caller input is not a provider
   gap and must not consume a provider attempt.
2. Accept a result only when returned country and exact provider concept/code match the requested
   cell, complete MIME/status/redirect identity is permitted, frequency/unit/currency/level-vs-rate
   semantics match, and actual/projection lineage is explicit.
3. Provider `null` values remain missing; an all-null or no-row result is typed empty/missing, not a
   zero series. No forward fill, interpolation, annual/monthly substitution, PPP/constant-price
   substitution, country/region proxy, policy-rate relabel, or cross-provider stitch is allowed.
4. Reconcile all provider-declared pages/totals with retained rows before returning. A late failure,
   budget exhaustion, identity conflict, or unresolved page is atomic: return no partially assembled
   `IndicatorSeries` and no misleading coverage warning.
5. Keep observation date, publication/release date, revision/correction date, and retrieval
   `fetched_at_utc` distinct. Annual dates use the existing Jan-1 representation; monthly dates use
   provider month-start only after exact period identity is verified.
6. Existing failover may choose one healthy, unit-compatible source; it must not combine values from
   multiple sources to make the cohort appear complete. WEO projections remain separate from actuals.
7. The current macro module has no #235 cache. If a future implementation introduces one, its key
   must include country, canonical indicator, exact provider concept, requested window, route/version,
   and terms/reuse scope; caller failures and malformed responses must fail before cache write, and
   provider rows must not be persisted without an explicit rights decision.

## Deferred RED and release matrix

No RED authorization is requested or implied. After a source/design PASS, a separate API/model and
RED decision must pin at least these offline synthetic-fixture cases:

1. **World Bank 40-case matrix:** `USA/CAN/MEX/CUB/DOM × 8 WDI concepts`, exact route/code/params,
   returned country/code identity, unit/currency/frequency, Jan-1 dates, ascending unique points,
   null/missing rows, bounds, page reconciliation, one-dispatch behavior, and no country-specific
   production branch. Fixtures may use real contract identifiers only when identity routing is the
   behavior under test; all display names, dates, and values remain synthetic.
2. **Monthly exact-dimension cases:** every future-qualified DBnomics country/concept pair, exact
   two-letter path, monthly periods, country-neutral identity, source/operator attribution, no SBV
   label leakage, staleness warning behavior, and unsupported/unmapped countries failing before a
   malformed dispatch.
3. **Malformed provider/caller cases:** malformed ISO3/indicator/date, wrong country/concept,
   duplicate/conflicting dates, non-finite/bool/out-of-range values, missing or naive metadata,
   invalid projection boundary, and rows outside the requested window.
4. **Coverage/atomic cases:** exact full/partial/not-served/unknown distinctions, provider current
   lag, null years, revision/correction, authoritative empty versus transport failure,
   page/total mismatch, late failure, and no false partial return.
5. **Transport/security cases:** wrong or incomplete MIME, status, owner-host redirect, TLS/WAF,
   timeout, rate/retry, compressed/decompressed byte ceiling, cache, and bounded sanitized
   diagnostics with no query/header/cookie/credential leakage.
6. **Regression/release cases:** all existing VNM/USA/CAN behavior, source ordering, unit filtering,
   IMF projection handling, FRED BYOK isolation, no network in offline tests, docs/API/units/skill/
   CHANGELOG updates only if a later public API actually changes, full pytest, isolated wheel/sdist,
   blacklist/secret/diff/path/object/clean-tree gates, and exact remote-anchor verification.

Tests must pin the honest dispositions, including missing and unsupported cells; no test may assert
that all 50 cells succeed.

## Conjunctive reopen criteria

A future request may reopen a specific cell only when **all** applicable axes pass in one retained,
source-specific evidence set:

1. owner/operator and exact route/version/method are named;
2. response-backed country, canonical concept/code, frequency, unit, currency, level/rate/growth
   meaning, and actual/projection status match;
3. status, complete MIME, redirect final identity, TLS/session/auth posture, pagination/totals, and
   bounded response bytes are retained;
4. provider-declared and observed first/last dates, count, null/interior-gap/duplicate/conflict,
   revision/correction and current-lag semantics are reconciled;
5. automation, caller return, cache/storage, retention/deletion, attribution, commercial/derivative
   use, redistribution, amendment, and revocation terms are explicit for the exact route/data;
6. finite logical/physical/retry/rate/concurrency/backoff/byte budgets are atomic and mechanically
   enforceable; and
7. a separate API/model decision and RED matrix approves any change to the public surface.

For the monthly four unmapped countries, exact IMF dimensions and country concept authority are
additional gates. For USA `POLICY_RATE`, the SBV proxy label must be removed or replaced by a
country-correct, response-backed identity before it can leave `SEMANTICS_GAP`. Until then no monthly
North America policy-rate result is claimed.

## Lifecycle and required transition

The source/design handoff is local only. The backlog records the intake first, and the final handoff
will change the #235 row to reviewer-owned `REVIEW_REQUESTED` with `RETURN_EXACT_SHA_DESIGN_VERDICT`,
bind the exact content/design blobs and final commit, and preserve the clean published base
`472cfe6`. A design PASS would authorize only the next explicitly reviewed API/model decision (if
needed), never RED, production code, source registration, push, or closure.

## Sources and durable repository evidence

Primary sources:

- [UN M49 methodology](https://unstats.un.org/unsd/methodology/m49/)
- [UN Member States](https://www.un.org/about-us/member-states)
- [World Bank indicator API queries](https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries)
- [World Bank API basic call structures](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures)
- [World Bank WDI API overview](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392)
- [World Bank public licenses](https://datacatalog.worldbank.org/public-licenses)
- [World Bank 2020 cohort query](https://api.worldbank.org/v2/country/ATG%3BBHS%3BBRB%3BBLZ%3BCAN%3BCRI%3BCUB%3BDMA%3BDOM%3BGRD%3BGTM%3BHND%3BHTI%3BJAM%3BKNA%3BLCA%3BMEX%3BNIC%3BPAN%3BSLV%3BTTO%3BUSA%3BVCT/indicator/NY.GDP.MKTP.CD?date=2020&format=json&per_page=100)
- [World Bank 2025 available-case query](https://api.worldbank.org/v2/country/ATG%3BBHS%3BBRB%3BBLZ%3BCAN%3BCRI%3BCUB%3BDMA%3BDOM%3BGRD%3BGTM%3BHND%3BHTI%3BJAM%3BKNA%3BLCA%3BMEX%3BNIC%3BPAN%3BSLV%3BTTO%3BUSA%3BVCT/indicator/NY.GDP.MKTP.CD?date=2025&format=json&per_page=100)
- [IMF IFS](https://data.imf.org/ifs)
- [IMF CPI dataset](https://data.imf.org/Datasets/CPI)
- [DBnomics IMF provider](https://db.nomics.world/IMF)
- [DBnomics IMF/IFS dataset](https://db.nomics.world/IMF/IFS?tab=table)
- [IMF terms linked by DBnomics](http://datahelp.imf.org/tos)

Durable repository evidence:

- `tasks/199-200-design-note.md` — approved #200 Canada live-probe summary and source/API boundary.
- `tests/test_macro_worldbank.py` — offline synthetic CAN public-path regression; not live coverage.
- `docs/research/2026-06-18-macro-global-cross-country.md` — older bounded USA/global WDI
  response evidence; not a #235 full-panel result.
- `vnfin/macro/indicators.py`, `vnfin/macro/worldbank.py`, `vnfin/macro/dbnomics.py`,
  `vnfin/macro/client.py`, and `vnfin/macro/models.py` — current API/source/model anchors.

## Bottom summary

- Aggregate: **`PARTIAL_COHORT`**, not a complete five-country panel.
- Frozen cohort: `USA/CAN/MEX/CUB/DOM`, strict common-year 2020 WDI GDP.
- 2025 `USA/CAN/MEX/DOM/GTM` is an incomplete appendix; it never replaces Cuba.
- Matrix: 50 independent cells: 5 proven CAN, 4 partial USA, 1 policy-rate semantics gap, 40 not probed.
- Preserve `get_indicator` and `IndicatorSeries`; no ranking, batch, substitution, or new model.
- No #235 provider dispatch, raw row, RED test, code, source registration, or capability claim occurred.
- Future observation ceiling: at most 9 logical/physical requests, zero retries, only after exact gates.
- Need from reviewer: exact-SHA source/design verdict; no Boss decision is required at this stage.
