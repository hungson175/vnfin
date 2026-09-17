# #236 search-discovery incident ledger

**Date:** 17 September 2026 (+07)
**Plan anchor:** `945c981bf14936aec77e380c8e8f4d888786f32b` at 19:11:55 +07
**Scope:** search-engine discovery only; provider API/data requests are in the main source report

## Sanitization and clean-room rule

Every query below ended with the same literal blacklist suffix:

```text
EXCLUSION=-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

`${EXCLUSION}` in a row is an exact substitution for that suffix, not an omitted or approximate query. No prohibited result was opened, cited, compared, or used. Search-result text is not source evidence; retained findings map to direct official URLs, official documents, or bounded exact provider probes in the main report.

## Incident total and completeness

- Committed hard ceiling: 6 logical query strings / 6 dispatches, including three baseline strings.
- Earlier unretained sequence: 25 strings / 7 dispatches, including the three baseline strings. Only seven topic groups, not the exact 25 strings or their result URLs, remain; therefore those strings and URLs are `NOT_RETAINED` and cannot support a claim.
- Fully retained sequence below: 47 strings / 12 dispatches, all after the plan commit and all carrying `${EXCLUSION}`.
- Whole-study observed total: **72 strings / 19 dispatches**. This supersedes the incorrect 25/7 figure in the blocked design.
- No further search-engine query was made during the correction.

### Earlier groups whose exact strings and result URLs were not retained

| Dispatch | Logical strings | Retained topic only | Claim treatment |
|---:|---:|---|---|
| UNRETAINED-01 | 3 | baseline official-source discovery | Exact strings unavailable; no claim may rely solely on this group |
| UNRETAINED-02 | 3 | IMF routes/terms | Exact strings unavailable; use retained batch BATCH-01/BATCH-02 or direct official sources instead |
| UNRETAINED-03 | 4 | SingStat table identifiers | Exact strings unavailable; use retained batches BATCH-03–BATCH-07 or direct table responses instead |
| UNRETAINED-04 | 4 | CPI and unemployment concepts | Exact strings unavailable; use retained batches BATCH-03–BATCH-07 or direct responses instead |
| UNRETAINED-05 | 4 | exact identifier follow-up | Exact strings unavailable; one irrelevant third-party listing appeared but was not opened or used |
| UNRETAINED-06 | 3 | API and terms | Exact strings unavailable; no permission claim relies on this group |
| UNRETAINED-07 | 4 | OpenAPI/developer-contract follow-up | Exact strings unavailable; no route-contract claim relies on this group |

## Exact retained query-batch ledger

| Evidence batch / time | Exact sanitized query strings | Exact official-URL mapping and retained use |
|---|---|---|
| BATCH-01<br>2026-09-17T19:13:29.227+07:00 | 1. `site:datahelpdesk.worldbank.org WDI API authentication rate limit terms CC BY 4.0 indicator API ${EXCLUSION}`<br>2. `site:databank.worldbank.org metadata NY.GDP.MKTP.CD NY.GDP.MKTP.KD.ZG FP.CPI.TOTL FP.CPI.TOTL.ZG SL.UEM.TOTL.ZS ${EXCLUSION}`<br>3. `site:databank.worldbank.org metadata FR.INR.LEND FR.INR.DPST FR.INR.RINR ${EXCLUSION}`<br>4. `site:worldbank.org indicator NY.GDP.MKTP.CD FR.INR.RINR definition metadata ${EXCLUSION}` | `RESULT_URL_NOT_RETAINED`. World Bank claims rely on the separately cited direct official pages and exact API probes, not this batch. |
| BATCH-02<br>2026-09-17T19:13:59.061+07:00 | 1. `site:imf.org/external/datamapper/api/v1 API documentation DataMapper NGDP_RPCH PCPIPCH LUR ${EXCLUSION}`<br>2. `site:imf.org DataMapper API terms of use projections NGDP_RPCH PCPIPCH LUR ${EXCLUSION}`<br>3. `site:imf.org WEO database NGDP_RPCH PCPIPCH LUR definition units projections ${EXCLUSION}` | `RESULT_URL_NOT_RETAINED`. IMF claims rely on the separately cited direct official terms/disclaimer and exact fallback probes, not this batch. |
| BATCH-03<br>2026-09-17T19:12:54.107+07:00 | 1. `site:singstat.gov.sg Singapore CPI monthly "Table Builder" "2019 As Base Year" September 2026 ${EXCLUSION}`<br>2. `site:tablebuilder.singstat.gov.sg "Consumer Price Indices" monthly API ${EXCLUSION}`<br>3. `site:singstat.gov.sg Singapore CPI "year-on-year" monthly SingStat table ${EXCLUSION}`<br>4. `site:singstat.gov.sg Singapore Department Statistics GDP unemployment API table terms use data API 2026 ${EXCLUSION}` | `RESULT_URL_NOT_RETAINED`. Later bounded table probes, not search snippets, establish SingStat identity. |
| BATCH-04<br>2026-09-17T19:13:04.675+07:00 | 1. `site:tablebuilder.singstat.gov.sg/table/TS/ "Consumer Price Indices (CPI)" "2024 As Base Year" ${EXCLUSION}`<br>2. `site:tablebuilder.singstat.gov.sg/table/TS/ "Percentage Change In Consumer Price Index" Monthly ${EXCLUSION}`<br>3. `site:tablebuilder.singstat.gov.sg/table/TS/ Singapore "Unemployment Rate" Monthly Quarterly Annual ${EXCLUSION}`<br>4. `site:tablebuilder.singstat.gov.sg "API Terms of Service" "last updated" ${EXCLUSION}` | `RESULT_URL_NOT_RETAINED`. Later bounded table probes establish identity; API-terms URL/content remains `NOT_RETAINED`. |
| BATCH-05<br>2026-09-17T19:13:17.284+07:00 | 1. `"M212261" Singapore CPI ${EXCLUSION}`<br>2. `site:tablebuilder.singstat.gov.sg/table/TS/ "Consumer Price Index (CPI)" "2024" ${EXCLUSION}`<br>3. `site:tablebuilder.singstat.gov.sg/view-api "OpenAPI" "tabledata" ${EXCLUSION}`<br>4. `site:tablebuilder.singstat.gov.sg "terms-of-use" OR "api-terms" SingStat ${EXCLUSION}` | [SingStat Data API catalog](https://tablebuilder.singstat.gov.sg/view-api/find-apis). `M212261` and terms result URLs are `RESULT_URL_NOT_RETAINED`; neither supports a claim. |
| BATCH-06<br>2026-09-17T19:13:33.539+07:00 | 1. `site:tablebuilder.singstat.gov.sg/table/TS/M213 "Percent Change In Consumer Price Index (CPI) Over Corresponding Period Of Previous Year, 2024 As Base Year" ${EXCLUSION}`<br>2. `site:tablebuilder.singstat.gov.sg/table/TS/M213 "Consumer Price Index (CPI), 2024 As Base Year" "Frequency Monthly" ${EXCLUSION}`<br>3. `site:tablebuilder.singstat.gov.sg/view-api SingStat Developer API request JSON CSV GET POST limit rate auth ${EXCLUSION}`<br>4. `site:tablebuilder.singstat.gov.sg "API Terms of Service" automation cache redistribute commercial attribution ${EXCLUSION}` | [SingStat Data API catalog](https://tablebuilder.singstat.gov.sg/view-api/find-apis). Later exact probes, not snippets, establish table identity; API-terms result URL is `RESULT_URL_NOT_RETAINED`. |
| BATCH-07<br>2026-09-17T19:13:58.756+07:00 | 1. `site:tablebuilder.singstat.gov.sg/table/TS/M213812 ${EXCLUSION}`<br>2. `site:tablebuilder.singstat.gov.sg "API Terms of Service" "automated" OR "redistribute" OR "commercial" OR "cache" ${EXCLUSION}`<br>3. `site:singstat.gov.sg "API Terms of Service" SingStat Data API ${EXCLUSION}`<br>4. `site:tablebuilder.singstat.gov.sg "Developer API" "POST" "JSON" "CSV" ${EXCLUSION}` | `RESULT_URL_NOT_RETAINED`. `M213812` supports no claim; API-terms URL/content and permissions remain `NOT_RETAINED`. |
| BATCH-08<br>2026-09-17T19:12:48.474+07:00 | 1. `site:mas.gov.sg monetary policy framework exchange rate Singapore policy rate SORA official ${EXCLUSION}`<br>2. `site:mas.gov.sg API statistics domestic interest rates prime lending fixed deposit official documentation ${EXCLUSION}`<br>3. `site:data.gov.sg Singapore API catalog MAS lending rate deposit rate real interest rate SORA interbank rate ${EXCLUSION}`<br>4. `site:mas.gov.sg terms of use API rate limit attribution redistribution commercial use official ${EXCLUSION}` | [MAS domestic interest rates / SORA](https://eservices.mas.gov.sg/Statistics/dir/DomesticInterestRates.aspx) and [data.gov API overview](https://guide.data.gov.sg/developer-guide/api-overview). No search result alone qualifies a route. |
| BATCH-09<br>2026-09-17T19:13:00.943+07:00 | 1. `site:mas.gov.sg/monetary-policy Singapore monetary policy exchange rate centred framework S$NEER policy band official policy interest rate ${EXCLUSION}`<br>2. `site:mas.gov.sg "three main features" monetary policy framework exchange rate Singapore official ${EXCLUSION}`<br>3. `site:guide.data.gov.sg API rate limits authentication terms license datasets download official ${EXCLUSION}`<br>4. `site:data.gov.sg/terms-of-use OR site:data.gov.sg/terms "Terms of Use" data API licence redistribution official ${EXCLUSION}` | [Attempted MAS circular target](https://www.mas.gov.sg/-/media/mas/sgs/sgs-announcements-pdf/bonds-pdf/green-sgs-infrastructure-and-syndication/offering-circular.pdf), [data.gov privacy and terms](https://data.gov.sg/privacy-and-terms), and [data.gov rate limits](https://guide.data.gov.sg/developer-guide/api-overview/api-rate-limits.md). The MAS target later returned maintenance HTML and has `SOURCE_LOCATOR_GAP`. |
| BATCH-10<br>2026-09-17T19:13:13.805+07:00 | 1. `site:data.gov.sg "Singapore Open Data Licence" version effective date attribution commercial derivative redistribution ${EXCLUSION}`<br>2. `site:data.gov.sg/datasets Singapore monthly interest rate prime lending fixed deposit SORA dataset ID SINGSTAT ${EXCLUSION}`<br>3. `site:data.gov.sg/datasets Singapore merchandise trade industrial production retail sales money supply reserves exchange rate MAS SINGSTAT dataset ${EXCLUSION}`<br>4. `site:tablebuilder.singstat.gov.sg API documentation table ids Singapore external trade industrial production retail sales official ${EXCLUSION}` | [Singapore Open Data Licence 1.0](https://data.gov.sg/open-data-licence), [data.gov privacy and terms](https://data.gov.sg/privacy-and-terms), and proposal-only [money supply dataset](https://data.gov.sg/datasets/d_7ed3eccba609ac0bdfcf406d939bdb0b/view). Exact row qualification remains deferred. |
| BATCH-11<br>2026-09-17T19:13:24.810+07:00 | 1. `site:guide.data.gov.sg/developer-guide "Dataset Downloads" API endpoint pagination bytes csv poll-download official ${EXCLUSION}`<br>2. `site:data.gov.sg/datasets "Industrial Production Index" Monthly SINGSTAT Singapore dataset ${EXCLUSION}`<br>3. `site:data.gov.sg/datasets "Retail Sales Index" Monthly SINGSTAT Singapore dataset ${EXCLUSION}`<br>4. `site:data.gov.sg/datasets "Official Foreign Reserves" OR "Foreign Reserves" OR "Exchange Rates" MAS Singapore monthly SINGSTAT ${EXCLUSION}` | [data.gov rate limits](https://guide.data.gov.sg/developer-guide/api-overview/api-rate-limits.md) and proposal-only [official reserves dataset](https://data.gov.sg/datasets/d_92afecf58ad03196ff6a7abb7a03d631/view). Other result URLs are `RESULT_URL_NOT_RETAINED`. |
| BATCH-12<br>2026-09-17T19:13:48.237+07:00 | 1. `site:data.gov.sg/datasets Singapore "Index Of Industrial Production" monthly SINGSTAT ${EXCLUSION}`<br>2. `site:data.gov.sg/datasets Singapore "Merchandise Trade" monthly total imports exports dataset SINGSTAT d_ ${EXCLUSION}`<br>3. `site:mas.gov.sg SORA SIBOR Singapore Government Securities MAS bills Overnight Funding Rate monetary policy operations framework official ${EXCLUSION}`<br>4. `site:data.gov.sg/datasets Singapore exchange rates monthly nominal effective exchange rate S$NEER MAS SINGSTAT dataset ${EXCLUSION}` | `RESULT_URL_NOT_RETAINED`. Later direct official pages support any retained trade/IIP/SORA claim; this batch itself supports no route qualification. |

Only literal, locally retained official results that exactly match an already-cited URL are listed.
Other results, inferred canonicalizations, and search snippets are excluded.
`RESULT_URL_NOT_RETAINED` does not mean that no result existed.

## Official-document action reconciliation

The blocked report's 16/18 official-document count also omitted 98 logical URL-open actions from
fully retained research sequences. Adding the earlier sequence's reported 16 actions and the
correction's two document opens gives **at least 116 logical URL-open actions**. Exact individual
actions from the earlier sequence, underlying physical HTTP requests, browser-internal retries,
bytes, and redirect hops are `NOT_RETAINED`; this is an attributable logical-action lower bound,
not reconstructed transport evidence. No claim relies solely on an unretained action.

## Breach cause and `PROCESS_CONTROL_GAP`

1. The committed counter was maintained separately by workstream rather than in one externally
   enforced reservation system.
2. Parallel research sequences began without explicit globally debited search reservations.
3. Six post-plan batches continued after the limit, while the first report counted only 25 strings
   / 7 dispatches and omitted the retained 47 / 12 sequence.
4. Multi-query batching obscured logical-string use.
5. No mechanism prevented a direct search call after nominal exhaustion.

The proposed counter formula is a policy description, **not an implemented or enforceable atomic
guard**: there is no shared durable state, lock/single-writer contract, pre-dispatch reservation
receipt, or bypass prevention. This is therefore a **`PROCESS_CONTROL_GAP`**. No later
search-discovery phase may start until a separate reviewer-approved, externally enforced
reservation mechanism exists and proves all four properties. A future mechanism must reject before
dispatch when `used_queries + batch_size > logical_cap` or
`used_dispatches + 1 > dispatch_cap`, default every workstream to zero allowance, issue durable
reservation receipts, prevent direct-call bypass, never restore capacity after failure, and forbid
rollover. Designing or implementing that mechanism is outside this docs-only correction. The #236
correction used zero search queries and needs no more research.

## Claim reconciliation

- WDI cell evidence comes from exact direct metadata/observation probes and official pages, not the unretained search sequence.
- SingStat table identity/unit comes from exact direct `M213781` responses; the unavailable OpenAPI/terms legs remain explicit route/legal gaps.
- MAS rate semantics use the retained direct SORA page; the policy-framework citation has `SOURCE_LOCATOR_GAP`, so the combined-source inference is explicitly qualified in the main report.
- The proposal-only expansion ranking is retained only where a batch above maps to a direct official data.gov dataset cited in the main report; unsupported claims are removed.

## Bottom summary

- Actual search use was 72 strings / 19 dispatches against a hard 6/6 ceiling.
- Exact query text exists for 47/12; the earlier 25/7 strings and result URLs are `NOT_RETAINED` and support no claim.
- Each retained batch now maps to exact official URLs or `RESULT_URL_NOT_RETAINED`.
- This public ledger uses neutral batch IDs and contains no machine-local source paths.
- Findings rely on direct official pages/probes, never search-result snippets.
- The narrative counter is a `PROCESS_CONTROL_GAP`, not an implemented atomic guard.
- Later search discovery is blocked pending a reviewer-approved externally enforced reservation mechanism.
- This correction made zero search queries; no further #236 research is required.
- Need from reviewer: accept or reject this C1/C2/C5 evidence-contract correction.
