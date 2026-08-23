# #207 daily USD/VND history — source vetting

**Date:** 2026-08-23 (UTC+7)
**Packet:** `tasks/207-daily-usdvnd-fx-history-spec.md` (reviewer packet `3d60102`)
**Requested window:** inclusive `2018-08-01..2026-08-19`
**Decision:** **SOURCE-GAP CLOSURE** — no daily capability, production code, RED tests, or
source-backed API claim is authorized by this note.

This report is a clean-room source and legal review for the existing `vnfin.fx.history()` path.
It does not implement a provider, infer missing observations, or turn an official publication
page into a reuse licence. The annual World Bank behavior remains the only supported historical FX
behavior.

## 1. Clean-room and research boundary

Before this research I ran the repository checklist at `docs/vnstock-blacklist.md`. The exact search
exclusion was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted source, artifact, endpoint map, schema, code, test, or behavior was opened, cited,
compared, or used. All evidence below is from provider-owned official pages/APIs, the World Bank
official catalogue/API, or already-reviewed repository source notes.

The only requested capability is a daily `USD`/`VND` history primitive. Directional signals,
session mapping, conversion helpers, intraday FX, cross-rates, interpolation, resampling, and
trading decisions are out of scope. A numeric value expressed as VND per USD is not by itself a
compatible economic basis: central reference, bank transfer quote, bilateral end-of-period rate,
and annual period average remain different source units for failover purposes.

## 2. Existing behavior that must not change

The current implementation and source notes establish these compatibility boundaries:

| Existing contract | Preservation rule |
| --- | --- |
| `vnfin.fx.history(base, quote, start, end, *, frequency=Frequency.ANNUAL, ...)` | Keep the signature, validation order, and annual default. |
| Annual source | `WorldBankFXHistorySource` over WDI `PA.NUS.FCRF`, source token `worldbank_fx`, annual period-average, USD/VND only. |
| Annual bounds | Inclusive calendar-year filtering; existing `None` bound semantics and pre-network validation remain unchanged. |
| `FXPoint.date` | Annual points remain Jan 1 reference-year keys; this is not a publication timestamp. |
| `fetched_at_utc` | Retrieval time only. It does not establish observation, publication, or first-availability time. |
| `rate_on()` / `rate_for_year()` | Exact lookup only. A future daily history must make `rate_for_year()` reject non-annual history rather than reinterpret a daily Jan 1 point. |
| Diagnostics | Existing annual `SourceCapability` and `explain_fx_coverage()` behavior remains additive-only and unchanged until a separately approved daily implementation. |

The present code correctly rejects `Frequency.DAILY` before transport. This report does not change
that rejection.

## 3. Bounded probe protocol

The date command was run as `2026-08-23T08:09:36+0700`. Live probes used a fresh process with no
cookie jar, no credentials, no proxy, no browser automation, IPv4, a 5-second connect timeout,
15-second total timeout, and no retry. The request used the project's desktop-Chrome `User-Agent`
because SBV has historically been User-Agent-sensitive; this was an explicit header only, not a
browser session or a challenge bypass. The current SBV result below shows that a browser-shaped
User-Agent does not establish reliable JSON access.

Only status, effective host/path, media type, envelope shape, counts, and dates were retained. Raw
responses, current FX values, response bodies, cookies, and screenshots were not written to the
repository. The nine HTTP calls were bounded as follows:

| Candidate | Calls | Route/observation | Sanitized result |
| --- | ---: | --- | --- |
| SBV | 3 | Headless structured-content route: a deliberately negative wire `page=0`, wire `page=1`, and a date-filter variant; `pageSize=100` | All were HTTP 200, `text/html; charset=utf-8`, no redirect, 246-byte HTML `Request Rejected` pages; no JSON envelope or rows. |
| BIS | 2 | Official SDMX `WS_XRU`: `M.VN.VND.E` and the explicit daily key `D.VN.VND.E` | Monthly route was HTTP 200 CSV; daily key was HTTP 404 XML. |
| Federal Reserve | 1 | Official H.10 current release/country table | HTTP 200 HTML; the table had 23 bilateral currency rows plus index rows and no VND/Vietnam row. |
| Vietcombank | 2 | Official `api/exchangerates?date=` at `2018-08-01` and `2020-01-02` | HTTP 200 JSON envelope with `Count`, `Data`, `Date`, `UpdatedDate`; both `Data` arrays were empty. This is not proof of historical absence. |
| World Bank | 1 | WDI `VNM/PA.NUS.FCRF`, `format=json`, small `per_page` | HTTP 200 JSON with the normal metadata/observations envelope; five annual rows were returned for the bounded probe. |

The official ECB page was inspected once through its published currency roster rather than crawled.
No per-date fan-out was attempted for Vietcombank or the repository currency CDN. The prior SBV
intake observation in the packet remains relevant: `totalCount=1947` was seen on the requested-window
date-filtered query, but full pagination was not completed and later pages produced HTTP-200 HTML
WAF pages. That observation is not treated as a successful coverage proof or an unfiltered count.

## 4. Candidate matrix

Disposition tokens are axis-specific. `NOT_SERVED` means the official route does not provide the
requested daily USD/VND basis; `TRANSPORT_INCONCLUSIVE` means an empty/HTML response cannot prove
absence; `LEGAL_GAP` means public access is not a grant of automated reuse, caching, storage, or
caller-facing redistribution; `CALL_BUDGET_GAP` means the bounded retrieval contract is not
proven; and `BASIS_GAP` means the quote is economically different from the requested basis.

| Candidate and owner | Exact observed or documented basis | Requested daily span evidence | Legal/runtime posture | Overall disposition |
| --- | --- | --- | --- | --- |
| **State Bank of Vietnam (SBV)**, `sbv.gov.vn` | Official central USD/VND concept; route is `/o/headless-delivery/v1.0/content-structures/137473/structured-contents`; fields named by the packet include `NgayBatDau`, `NgayBanHanh`, `TyGiaSo`, `TyGiaChu`, `SoVanBan`. | No response-backed identity or dates in the fresh probe: every request was an HTML WAF rejection. Prior `totalCount=1947`/20-page observation was not reconciled. | No API automation, rate, caching, storage, or redistribution permission was found. The official publication duty is not a licence. | `LEGAL_GAP` + `CALL_BUDGET_GAP` + `TRANSPORT_INCONCLUSIVE`; **not TDD-qualified**. |
| **BIS**, `stats.bis.org`, `WS_XRU` | Official CSV proved Vietnam/VND, USD bilateral, monthly **end-of-period** series (`FREQ=M`, 833 distinct periods, 1957-01 through 2026-05). | `D.VN.VND.E` returned 404. BIS documentation says daily exists only for a subset of economies; it cannot promote Vietnam's monthly series to daily. | Statistics terms permit reuse with BIS attribution and no misleading endorsement; API terms are separately as-is and may be limited/suspended. | `NOT_SERVED` for daily; monthly end-of-period is a different frequency/basis. |
| **Federal Reserve H.10**, `federalreserve.gov` | Current official table publishes bilateral rates for its listed currencies and separate indexes. | The current country table had no Vietnam/VND row. A guessed FRED identifier was not used as evidence. | Official public table, but no requested VND series was served by the inspected H.10 route. | `NOT_SERVED`. |
| **Vietcombank**, `vietcombank.com.vn` | First-party route/documentation describes `cash`, `transfer`, and `sell` bank quotes, not an SBV central reference rate; the page says “for reference only”. | Bounded calls at the 2018 boundary and a 2020 date returned empty `Data`; intake found no 2018 rows and did not establish a complete start. A one-date-per-request crawl would require thousands of calls, while the date API's own rate policy is unknown. | No open-data licence; public access and “for reference only” do not authorize automated history retrieval or redistribution. | `COVERAGE_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `CALL_BUDGET_GAP`. |
| **World Bank WDI**, `api.worldbank.org` | `PA.NUS.FCRF` is official exchange rate, LCU per US$, **annual period average**. VNM maps to VND/USD; current library behavior is already qualified for annual history. | WDI catalogue metadata says annual periodicity; it cannot serve the requested daily observations. | CC BY 4.0 with attribution; existing library remains runtime-fetch-only with no bundled rows. | `NOT_SERVED` for daily; preserve as the annual source. |
| **ECB / Frankfurter** | ECB reference rates are EUR-base working-day information rates and the official published roster does not include VND. Frankfurter cannot create an independent owner, VND series, or licence. | No official VND daily series was found in the roster; no cross-quote or facade was used as a history oracle. | ECB page is informational and does not supply the requested VND basis; a facade cannot repair that source gap. | `NOT_SERVED` + `BASIS_GAP`. |
| **open.er-api** | Repository source note documents `latest/USD`, current/spot only, approximately daily refresh; no historical endpoint. | No historical route or full-span coverage. | Terms prohibit raw-data redistribution; caching is allowed under the provider terms, but this does not authorize a new daily-history product. | `NOT_SERVED` + `LEGAL_GAP`; never backfill history. |
| **Repository currency CDN adapter** | One date-pinned document per date, maximum 1,100-day range, known coverage only from approximately 2024-03-02. | Requested window is about eight years and exceeds the cap; per-date fan-out is not an acceptable FX-history path. | It is not an owner/official USD/VND history contract and cannot supply a stronger legal/runtime basis. | `NOT_SERVED` + `COVERAGE_GAP` + `CALL_BUDGET_GAP`. |

No candidate satisfies identity, basis, full-span coverage, legal/runtime permission, and bounded
retrieval as one qualification unit. Cross-provider numerical agreement would not repair that fact.

### 4.1 Required-axis ledger

This ledger makes the negative evidence explicit rather than treating an empty response as a
coverage oracle. “Requested first/last” means the literal first/last dates in the #207 daily window;
`unproven` is intentional when the route did not serve the requested daily cell.

| Source | Effective host / redirect | Auth, browser, MIME, bounded calls | Response identity, frequency, dates/count | Absence interpretation | Numeric/time/revision contract |
| --- | --- | --- | --- | --- | --- |
| SBV headless | `sbv.gov.vn`; no redirect in 3 probes | No credential supplied; explicit desktop-Chrome UA; no cookie/session; expected JSON but observed HTML; 3 physical calls, no successful page | Intended fields are named in the packet, but no response-backed item identity, count, page, reference date, requested first/last, or numeric field was available | `TRANSPORT_INCONCLUSIVE`, not provider non-publication | No numeric parse, unit, publication timestamp, calendar, revision, or update lag can be asserted; all remain reopen evidence |
| BIS `WS_XRU` | `stats.bis.org`; no redirect | No auth; direct SDMX/CSV; 2 physical calls | Response-backed `VN`/`VND`/USD identity, `FREQ=M`, 833 distinct periods, overall first/last `1957-01..2026-05`; requested daily first/last unserved | Daily 404 means this exact daily key is `NOT_SERVED`; it does not prove every BIS dataflow lacks daily VND | End-of-period monthly basis, provider observations only; official docs describe source provenance and multiple frequency semantics; revisions follow BIS updates |
| Fed H.10 | `www.federalreserve.gov`; no redirect | No auth; direct HTML; 1 physical call | Current table identity is the Fed's listed bilateral rows and indexes; no VND row; requested first/last unserved | Current catalogue/table `NOT_SERVED`; no historical absence inference beyond that inspected release | H.10's own daily-bilateral publication cadence is distinct from a VND qualification; no VND numeric/revision contract |
| Vietcombank API | `www.vietcombank.com.vn`; no redirect | No auth; direct JSON; no cookie/session; 2 physical calls; no bulk crawl | Envelope identity only (`Count`, `Data`, `Date`, `UpdatedDate`); `Data` empty for both probes; requested first/last unproven | Empty response is unresolved historical coverage, not proof of no rows; intake evidence still says 2018 boundary was not established | Cash/transfer/sell bank quote; provider update time is not observation/publication proof; date-API rate policy, retention, and revisions are unknown. The XML feed's five-minute statement is not transferred. |
| World Bank WDI | `api.worldbank.org`; no redirect | No auth; direct JSON; 1 physical call | `VNM`/`PA.NUS.FCRF` metadata and observations; bounded probe returned five annual rows, overall probe dates `2021..2025`; requested daily first/last unserved | `NOT_SERVED` because catalogue periodicity is annual, not because a daily response was empty | Annual period-average LCU/USD, CC BY 4.0, runtime fetch; annual behavior is already qualified and must not be relabeled |
| ECB reference rates | `www.ecb.europa.eu`; public page; no redirect asserted from page inspection | No auth; one page inspection; no API crawl | EUR-base published roster had no VND; requested daily USD/VND first/last unserved | `NOT_SERVED`/`BASIS_GAP`; no synthetic cross-quote | Working-day reference information only; TARGET closing-day rule and ECB update time do not establish VND daily availability or publication knowability |
| open.er-api / CDN | Provider route or repository adapter as documented; no owner redirect probe needed | open.er-api no-key current route; CDN no-key date fan-out; no historical call made | No historical response-backed identity or requested first/last; CDN has a documented 1,100-day cap and approximate 2024-03-02 lower boundary | Current-only/over-cap are bounded negative facts, not a missing-row fill instruction | open.er-api terms prohibit raw redistribution; CDN has no stronger official full-span/legal contract |

For the rows that did not serve the requested daily cell, numeric type/finiteness/positivity,
rounding/scale, provisional status, publication time, and revision behavior are deliberately
`unproven`; the future gate must obtain them from one successful response family in a fully
reconciled retrieval. No provider
response is used as an absence oracle merely because it is empty, 404, or blocked.

## 5. Detailed source records

### 5.1 SBV central rate — only plausible full-span candidate, still blocked

**Owner and identity.** The [SBV official rate-policy article](https://www.sbv.gov.vn/vi/web/sbv_portal/w/sbv591621)
states the daily central rate publication context under Decision 2730/QĐ-NHNN. The first-party
headless route named by the packet is:

```text
https://sbv.gov.vn/o/headless-delivery/v1.0/content-structures/137473/structured-contents
```

The provider-owned route and the named fields are a technically plausible identity, not yet a
response-backed contract. Three bounded requests with the project Chrome User-Agent all returned
`200 text/html` WAF rejection pages. Therefore this review does **not** assert an SBV item count,
first/last date, row unit, pagination envelope, or full-span coverage. The earlier `totalCount=1947`
observation is recorded as an unverified intake fact, not as a qualified count.

**Required response contract before qualification.** A future probe must establish all of the
following from the same response family:

1. The complete normalized media type is exactly `application/json`; missing, HTML, XML, generic
   `text/*`, or a challenge page is a typed `TRANSPORT_INCONCLUSIVE` result, never an empty series.
2. The envelope has a non-negative integer total, explicit page metadata, and a finite item array.
   The exact field names and nesting must be copied from a successful owner response into synthetic
   tests; this report does not invent a schema that the WAF prevented us from seeing.
3. Each item has the named effective-date, publication/document, and numeric fields. `TyGiaSo` or
   the documented numeric equivalent must parse as a finite positive non-boolean number. The
   response-backed source identity and official central-rate definition must establish **VND per
   1 USD**; a URL parameter or a field label alone is insufficient.
4. `NgayBatDau` is parsed as an explicit UTC instant and converted to `Asia/Ho_Chi_Minh` before
   taking the provider reference date. `NgayBanHanh` remains a separate provider field. It must
   not be silently treated as a publication timestamp, availability timestamp, or look-ahead proof
   unless SBV documents that exact meaning and timezone.
5. Pages have no duplicate or overlapping item identity, the observed total equals the reconciled
   page sum, and the filtered result is complete. A page that returns HTML with HTTP 200 fails the
   whole retrieval; it is not an empty page and cannot produce a coverage warning.

**Bounded pagination and WAF policy.** Liferay's documented query contract is one-based: wire
`page=1` is the first page and `page=20` is the twentieth. The official query documentation is
<https://learn.liferay.com/w/dxp/integration/headless-apis/using-liferay-as-a-headless-platform/consuming-apis/api-query-parameters>.
The unverified intake observation was `totalCount=1947` from the requested-window date-filtered
query, and `pageSize=100` implies a minimum of 20 wire pages for that observation. A future
implementation may use internal zero-based slots only with the explicit mapping
`logical_slot 0..19 -> wire page 1..20`; it must never send `page=0` under this contract. Page base,
`lastPage`, total/count fields, and the exact successful envelope remain qualification evidence to
re-prove from owner documentation and a successful response family. The budget must not silently
grow:

| Counter | Exact future ceiling | Meaning |
| --- | ---: | --- |
| logical source attempts | 1 | SBV is one candidate; no incompatible failover. |
| logical page slots | 20 | Internal slots `0..19`, mapped to wire pages `1..20`; a reconciled count needing wire page 21 is `CALL_BUDGET_GAP`. |
| physical HTTP requests | 40 | At most one initial request plus one explicitly reserved retry per page; retries are included in this total. |
| retries per page | 1 | No hidden transport-library retries, backoff loops, or concurrent duplicate pages. |

The deterministic scheduler processes internal slots in ascending order and requests wire pages
`slot + 1`. Before every HTTP call it
atomically reserves `(page, retry_index)` and one physical budget unit. A failed reservation makes
no HTTP call. A WAF HTML response consumes the reserved unit, is recorded as
`TRANSPORT_INCONCLUSIVE`, and can receive only the one reserved retry. Exhaustion stops the run,
returns no partial history, and records `CALL_BUDGET_GAP`; it never fabricates a final
`SourceAttempt` or labels the missing rows as provider absence. No numeric request interval is
claimed until SBV supplies an owner-approved rate policy. A future runtime must refuse to schedule
the source without that policy, rather than invent a delay or claim that the existing five-minute
cadence applies to SBV.

**Transport outcome and retry contract.** This table is a future design rule, not a live capability
claim. It makes the one reserved retry executable and keeps deterministic validation failures out
of retry loops. Redirects are not followed; the effective host/path must remain the canonical route.

| Outcome | Internal result | May consume the one page retry? | Public result |
| --- | --- | --- | --- |
| Strict HTTP 200, normalized MIME exactly `application/json`, non-empty body, valid envelope | `ok` | No | Continue page reconciliation. |
| HTTP 200 HTML matching the observed WAF/challenge signature | `waf_html` / `transport_inconclusive` | Yes, once, only if owner pacing is authorized and a reservation succeeds | Never an empty page or coverage claim. |
| HTTP 200 with empty body, `204`, non-JSON/XML/other MIME, or malformed `Content-Type` | `empty_body`, `no_content`, or `mime_mismatch` | No | Fail the whole retrieval; no partial result. |
| Any `3xx`, redirect, or effective-host/path mismatch | `redirect` / `effective_route_mismatch` | No | Fail closed; no follow-up route or source identity inference. |
| `429` or `5xx` | `rate_limited` / `server_error` | Once, only if owner pacing is authorized and a reservation succeeds | On exhaustion, `transport_inconclusive`; no partial result. |
| Timeout, TLS, connection, or other transport exception | `timeout`, `tls_error`, or `transport_error` | Once, only if owner pacing is authorized and a reservation succeeds | On exhaustion, `transport_inconclusive`; no partial result. |
| JSON parse, schema, identity, numeric, duplicate, count/page, endpoint, or gap validation failure | Corresponding deterministic failure token | No | Fail the whole retrieval; never retry a bad deterministic payload. |

MIME normalization is strict: parse the complete `Content-Type` value, lower-case and trim its
media-type portion, and require exactly `application/json`; parameters do not turn HTML/XML into
JSON. Every retry consumes a reserved physical unit before transport. The runtime must refuse to
schedule any source request without owner-approved pacing, so this table does not invent a delay.

The three diagnostic layers are separate:

1. **Offline `RequestDiagnostic.status`:** no network is performed; current daily status remains
   `unsupported_frequency`. A future additive daily registry may use only reviewed statuses such
   as `source_gap`, `coverage_gap`, or `ok`, with a typed `rate_basis` on each capability; transport
   exceptions never appear in an offline result.
2. **Successful `FXHistory.warnings`:** only provider-calendar/time caveats can accompany a
   successful fully reconciled history: `provider_nonpublication`, `holiday_gap`,
   `publication_time_unavailable`, and `revision_or_release_lag`. The maximum is four tokens;
   deduplicate first, then emit in that canonical order, never caller/order/provider-text order.
3. **Internal/failure reasons:** only the finite tokens in the transport table and the coverage
   tokens `source_gap`, `coverage_gap`, `provider_nonpublication`, `holiday_gap`,
   `unexplained_gap`, and `call_budget_gap` may be retained. No raw URL, body, exception, cookie,
   credential, provider text, or live rate is public. A failed retrieval returns no `FXHistory`.

**Coverage and calendar.** A qualifying result must be one **fully reconciled retrieval from one
qualified source**, not one wire response: every required wire page succeeds, page/count metadata
reconciles, and all accepted rows are unique, in-window, and identity-valid. That retrieval must
contain both literal requested endpoints `2018-08-01` and `2026-08-19` as provider reference dates.
Both are ordinary weekdays, but the library must not assume that every weekday is published.
Incomplete pages/totals, a missing requested endpoint, an unexplained internal gap, duplicate,
out-of-window row, empty result, or partial first/last boundary fails the entire source and returns
no partial `FXHistory`. Only provider-owned calendar/status evidence may justify an absent
weekend/holiday/non-publication date; those accepted absences use the exact bounded warning tokens
defined below. No weekend row, zero, forward fill, backfill, interpolation, annual expansion, or
current-spot substitution is allowed.

**Legal and reuse.** The SBV portal's statutory/publication role proves ownership and source
identity, not permission to automate, cache, store, redistribute, or return raw data to callers.
The official portal footer gives an owner contact path (`thuongtrucweb@sbv.gov.vn`,
`https://www.sbv.gov.vn/webcenter/portal/vi/links/cm255?dDocName=SBV624625`); contacting a portal
editor is only a discovery path, not permission. Reopening requires written authorization from an
appropriate SBV owner that names the exact route, automated access, request budget/rate, caching and
storage, caller-facing redistribution, attribution, commercial use, and revision/retention policy.

### 5.2 BIS WS_XRU — official, reusable, but monthly for Vietnam

The official API route
[`M.VN.VND.E`](https://stats.bis.org/api/v1/data/WS_XRU/M.VN.VND.E?format=csvfile)
returned CSV with response-backed dimensions `FREQ=M`, `REF_AREA=VN`, `CURRENCY=VND`, collection
`E`, and title semantics “exchange rates against USD — Vietnam — Dong — monthly — end of period”.
It contained 833 distinct monthly periods from 1957-01 through 2026-05 in the bounded observation.
The explicit daily key
[`D.VN.VND.E`](https://stats.bis.org/api/v1/data/WS_XRU/D.VN.VND.E?format=csvfile)
returned HTTP 404 XML. The BIS documentation says daily series exist for approximately 80
economies, while lower-frequency histories are broader; that dataset-wide fact is not evidence
that Vietnam has daily data. The official [WS_XRU availability enumeration](https://data.bis.org/topics/XRU/BIS%2CWS_XRU%2C1.0)
records the Vietnam/VND cell under annual, monthly, and quarterly frequencies, not daily; the
guessed daily-key 404 is only corroborating evidence.

BIS statistics terms permit use with BIS attribution, no misleading endorsement/affiliation, and
no added charge to users of a commercial product. The API is as-is, may be updated or suspended,
and its access may be limited. The source is therefore legally attractive for a future monthly or
daily series if the exact series exists, but this Vietnam monthly end-of-period cell is
`NOT_SERVED` for the requested daily central-rate basis. It is not a failover candidate for SBV.

Sources: [BIS data documentation](https://www.bis.org/statistics/xrusd/xrusd_doc.pdf),
[BIS permitted-use terms](https://www.bis.org/terms_statistics.htm), and the
[BIS data page](https://data.bis.org/topics/XRU/BIS%2CWS_XRU%2C1.0/M.VN.VND.E).

### 5.3 Federal Reserve H.10 — no VND row in current official table

The bounded current H.10 country table was HTTP 200 HTML and contained the listed bilateral
currency rows plus broad/AFE/EME index rows. It did not contain Vietnam or VND. The official H.10
page describes weekly publication of daily bilateral rates, but a current VND absence is a
`NOT_SERVED` result for this route, not evidence that every historical Fed product lacks Vietnam.
No guessed FRED identifier was used as a substitute for the owner catalogue.

Sources: [H.10 current release](https://www.federalreserve.gov/releases/H10/) and
[H.10 summary/index definitions](https://www.federalreserve.gov/releases/h10/summary/default.htm).

### 5.4 Vietcombank — spot bank quote, not the requested historical basis

The official API shape is `GET https://www.vietcombank.com.vn/api/exchangerates?date=YYYY-MM-DD`.
The bounded calls returned a stable JSON envelope (`Count`, `Data`, `Date`, `UpdatedDate`) with an
empty `Data` array for both tested dates. That response is not treated as proof that rows do not
exist historically. The provider documentation and existing source note describe cash, transfer,
and sell quotes, no central-rate identity, and “for reference only”. The five-minute statement in
the checked-in note belongs to the distinct current XML feed; no provider-owned rate policy was
found for this date API, so its date-API rate policy is **unknown**. A full-span daily history would
require a large date fan-out and remains `CALL_BUDGET_GAP` in addition to its coverage, basis, and
legal gaps.

Sources: [Vietcombank rate page](https://vietcombank.com.vn/en/To-Chuc/SMEs/KHTC---Ti-gia---SMEs),
[Vietcombank API route](https://www.vietcombank.com.vn/api/exchangerates?date=2020-01-02), and
the checked-in [source note](../sources/fx-vietcombank.md).

### 5.5 World Bank — preserve the annual source, do not expand it

The official WDI API
[`PA.NUS.FCRF`](https://api.worldbank.org/v2/country/VNM/indicator/PA.NUS.FCRF?format=json&per_page=5)
returned the normal JSON metadata/observations envelope. The catalogue identifies WDI as annual
periodicity and CC BY 4.0. The series is “official exchange rate (LCU per US$, period average)”,
not a daily observation and not the SBV central rate. It remains the existing annual
`worldbank_fx` source with runtime fetch/no bundled rows; no daily fallback or annual-to-daily
stamping is allowed.

Sources: [World Bank WDI catalogue](https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators),
[WDI API](https://api.worldbank.org/v2/country/VNM/indicator/PA.NUS.FCRF?format=json), and the
checked-in [annual source note](../sources/fx-history-worldbank.md).

### 5.6 ECB, Frankfurter, open.er-api, and the date-pinned CDN

The ECB's official reference-rate page states that rates are EUR-base working-day information
rates and its published roster did not list VND. That is not an acceptable basis for a synthetic
USD/VND daily cross-quote. Frankfurter is a delivery facade, not an independent official owner or
licence, so it cannot repair the ECB gap.

The checked-in open.er-api note documents a `latest/USD` current endpoint, approximately daily
refresh, no historical route, and terms prohibiting raw-data redistribution. The repository's
date-pinned currency CDN adapter makes one request per date, caps ranges at 1,100 days, and has
known coverage only from approximately 2024-03-02. It cannot cover the requested eight-year span
within a bounded budget. None is a daily historical source for #207.

Source: [ECB reference-rate page](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html),
plus the checked-in [open.er-api note](../sources/fx-open-er-api.md) and the packet's repository
CDN boundary.

## 6. Future API contract (design only; not implemented)

This section records what a later, separately authorized implementation would have to prove. It
is not a promise that `Frequency.DAILY` works today.

### 6.1 Qualification unit and source selection

One qualified unit is exactly one provider, route/version/key, economic basis, reference-date and
publication convention, and legal/runtime contract. The provisional SBV token would be:

```text
source    = "sbv_central_fx"
rate_basis = "official_daily_central_rate"
unit      = value_unit = "VND per 1 USD"
frequency = Frequency.DAILY
```

These are proposed finite tokens, not current capability. The annual World Bank token and basis
remain independent:

```text
source     = "worldbank_fx"
rate_basis = "official_annual_period_average"
frequency  = Frequency.ANNUAL
```

The future public model contract is a trailing, compatibility-safe typed field:

```python
FXHistory.rate_basis: str | None = None
```

The only accepted non-`None` values in this design are
`official_annual_period_average` and `official_daily_central_rate`. The future annual factory
must populate the first token; the future daily adapter must validate and populate the second.
`FXHistory.to_dataframe()` must always put the same value in
`DataFrame.attrs["rate_basis"]`. A separately reviewed additive `SourceCapability.rate_basis:
str | None = None` field must carry the same token for the annual and daily capability entries;
the current annual capability entry is not silently changed in this source-gap commit. If the
implementation chooses a different typed alternative, that alternative must be reviewed before
reopening and must provide the same constructor, DataFrame, diagnostic, snapshot, repr/equality,
and serialization guarantees.

Adding the trailing field keeps existing positional constructors valid, but it is still a reviewed
public model change: the public API snapshot, dataclass field list, repr/equality expectations,
serialization shape, docs contract, and CHANGELOG/release note must be updated together. Annual
routing, validation, values, exact lookups, and diagnostics remain unchanged; this is the precise
compatibility promise, not a claim of byte-for-byte object identity after the additive field.

No source may be admitted merely because its numeric values have the same VND/USD scale. If only
SBV later qualifies, daily history is a single-source path and must expose no fabricated failover
attempts. A chain may be added only after at least two independent sources qualify for the same
central-rate basis and date semantics; it chooses one source for the whole window and never
stitches dates across providers.

### 6.2 Facade, bounds, and result guards

After a future design PASS and a separate TDD authorization:

- `history(..., frequency=Frequency.DAILY)` would require plain `date` `start` and `end`, both
  inclusive, and validate pair, frequency, bounds, and budget before network;
- the requested proof window would be exactly `2018-08-01..2026-08-19`, with both literal
  boundaries present in one fully reconciled retrieval from one qualified provider;
- output would contain provider observations only, strictly ascending and unique, with no weekend/
  holiday fabrication, fill, interpolation, nearest match, annual expansion, current-spot backfill,
  or cross-provider stitching;
- every rate would be finite, positive, non-boolean, and response-backed as VND per 1 USD; scale,
  inversion, rounding, and decimal semantics would be explicit rather than guessed;
- `FXPoint.date` would be the provider reference date after the explicit UTC-to-Vietnam conversion;
  `fetched_at_utc` would remain retrieval time only; and
- `rate_on()` would remain exact-match. `rate_for_year()` would raise `InvalidData` unless
  `frequency is Frequency.ANNUAL`.

No publication timestamp may be synthesized from `fetched_at_utc`, `NgayBanHanh`, or an HTTP date.
If SBV later documents an enforceable publication timestamp, it must be an additive typed field with
its own timezone, revision, and strict-prior tests. Without that field, same-date availability is
unproven; callers must use a conservative strict-prior rule (`point.date < target_session_date`).

### 6.3 Fail-closed diagnostics and no-false-absence rules

Public diagnostics must be finite and bounded. The future implementation may expose only sanitized
reason tokens from this allow-list:

```text
ok
unsupported_frequency
unsupported_pair
source_gap
coverage_gap
provider_nonpublication
holiday_gap
unexplained_gap
transport_inconclusive
schema_error
identity_mismatch
call_budget_gap
legal_gap
revision_or_release_lag
publication_time_unavailable
```

`source_gap`, `transport_inconclusive`, `schema_error`, `identity_mismatch`, and `call_budget_gap`
are not coverage claims. An empty body, HTML WAF page, timeout, incomplete page reconciliation,
or unproven route is an unresolved/transport outcome. `coverage_gap` is allowed only after a
qualified response and provider calendar/status account for the missing date. A successful
`FXHistory.warnings` tuple may contain at most four deduplicated tokens, in this exact order:
`provider_nonpublication`, `holiday_gap`, `publication_time_unavailable`,
`revision_or_release_lag`. No warning may contain a URL, query, response body, raw exception,
cookie, credential, provider free text, or live rate. Counts are non-negative integers bounded by
the ceilings above.

The annual `explain_fx_coverage()` capability registry stays unchanged. A later additive daily
capability entry must say `is_single_source=True`, exact source/basis, requested-span boundary,
publication-time limitation, and current status. Until then, daily remains a typed unsupported
frequency rather than a misleading daily `coverage_gap`.

## 7. Conjunctive reopen criteria

The disposition changes from **SOURCE-GAP CLOSURE** only when every item below passes in the same
source/design review. One failed item keeps the chain empty and daily capability unclaimed.

1. **Reuse permission:** SBV owner authorization covers the exact route, automation, request/rate
   budget, retry behavior, caching/storage, caller-facing return/redistribution, attribution,
   commercial use, and revisions/retention. No inference from no-auth access or statutory
   publication.
2. **Stable transport:** a fresh session using the documented runtime User-Agent returns strict JSON
   (not a 200 HTML WAF page), with no challenge/private-cookie/proxy bypass; the owner rate policy
   is explicit and compatible with the fixed 20-page/40-physical-request ceiling.
3. **Envelope and identity:** the exact successful schema, field nesting, pair direction, central
   basis, numeric type/positivity/scale, document identity, and UTC-to-`Asia/Ho_Chi_Minh` effective
   date conversion are response-backed and represented by synthetic RED cases.
4. **Pagination and coverage:** total/page reconciliation completes within the exact budget, with
   no duplicates or overlaps; both requested endpoint dates are present in one fully reconciled
   retrieval; provider calendar/status accounts for every accepted absence; incomplete pages,
   totals, endpoints, or unexplained internal gaps fail the source and return no partial history.
5. **Time semantics:** observation/reference date, publication date if any, retrieval time,
   revision behavior, and strict-prior limitation are documented separately. `fetched_at_utc` is
   never used as a knowability oracle.
6. **Typed basis and compatibility:** the reviewed trailing public `FXHistory.rate_basis` field (or
   an explicitly reviewed typed alternative) uses the exact annual/daily tokens, populates annual
   and daily results, appears in `DataFrame.attrs`, `SourceCapability`/diagnostics, public
   snapshots, repr/equality/serialization, docs contracts, and release notes. Annual World Bank
   routing, validation, values, exact lookups, default frequency, zero-network unsupported
   frequencies, and annual diagnostics remain unchanged.
7. **Reviewer transition:** the exact two-doc source/design range receives design PASS first. Only
   a later explicit authorization can start RED-first synthetic tests and production TDD; this
   source-gap commit itself never authorizes either.

## 8. Final disposition

SBV is the only technically plausible full-span candidate, but the current strict transport chain
fails and the legal/reuse and rate-policy contract is absent. BIS serves Vietnam monthly rather than
daily; H.10 and ECB do not serve VND; Vietcombank is a legally restricted spot bank quote with no
qualified historical coverage; World Bank remains annual; and spot/CDN routes cannot be expanded
into daily history.

Therefore #207 is **SOURCE-GAP CLOSURE**. The two requested artifacts may be reviewed and, if
approved, published as a no-capability resolution. No RED tests, production code, daily source
chain, push, or issue closure is authorized by this report.
