# #201 source-vetting report — Vietnamese equity foreign-investor daily flow

**Research date:** 2026-08-22 (Vietnam time)
**Issue:** #201, accepted source-gated; reviewer packet `tasks/201-vn-equity-foreign-flow-spec.md` at reviewer commit `62e1e32`
**Repository state:** research/design only; no production code and no provider rows committed
**Blacklist compliance:** the mandatory project exclusion was applied to every search. No excluded result was opened, cited, cloned, installed, compared, or used. All evidence below is first-party exchange/regulator documentation or a first-party exchange web/API probe.

## Executive decision

There is one technically credible no-auth source for a bounded first implementation:

* **HOSE/HSX official market API** exposes per-symbol daily foreign buy/sell components and a
  server-side date range. A 22 August 2026 probe served 2018-01-01–2026-08-21 windows for
  FPT, VIC, and VCB (2,154 rows, 108 pages per sampled symbol). This is a **technical
  candidate**, not yet a legal clearance: the official Swagger contains no reuse licence,
  rate-limit statement, caching permission, or redistribution terms.
* **HNX official web reports** expose per-symbol buy/sell volume and VND value for HNX-listed
  and UPCoM securities, with ISIN and foreign-room fields. The listed-equity HTML page guards
  its UI to the most recent month, but the underlying no-auth POST returned rows for sampled
  trading dates in 2018, 2019, and 2026 when the request's `default-date` token matched the
  requested trading date. This is an **undocumented historical web seam**, not a documented
  archival API or a coverage guarantee. The UPCoM endpoint returned the same current snapshot
  for current, 2018, and 2000 date inputs, so UPCoM remains a historical source gap. HNX also
  publishes commercial package/fee material and copyright/all-rights-reserved notices; no
  open-data licence was found.
* **SSC/regulator pages and HNX PDFs** found in this round are aggregate/monthly, by-index, or
  by-industry—not a lawful no-auth per-symbol daily history. They cannot be a v1 adapter.
* **SSI FastConnect documentation** requires an access token, so it is not a no-auth candidate.

**Recommendation for the design gate:** approve a source-bounded contract and a HOSE-first
implementation only after legal permission/terms are resolved. Do not promise HNX/UPCoM
2018-current coverage, do not stitch sources, and do not bundle or persist provider rows while
the licence remains unknown. If the reviewer requires all three boards before implementation,
the correct state is **blocked by source gap**, not a fabricated fallback.

## 1. Method and evidence boundary

* Search date was re-checked with `date '+%d/%m/%Y - %A'` immediately before the web round.
* Search queries used the repository's mandatory exclusions. Results containing excluded
  material were skipped rather than opened or cited.
* Direct probes used only official hosts. The HOSE and HNX pages were inspected as public web
  pages/Swagger/UI contracts; no third-party endpoint map or implementation was used.
* Probe output was reduced to field names, response shape, counts, date bounds, and arithmetic
  checks. No raw provider rows are stored in this report, fixtures, package, or distribution.
* “No-auth” below means **the request succeeded without an API key, bearer token, login, or
  Authorization header in the observed probe**. It does not mean the provider has granted OSS
  redistribution or commercial reuse rights.

## 2. Candidate matrix

| Candidate | Per-symbol | Boards | Daily/history evidence | No-auth probe | Legal/reuse evidence | Verdict |
|---|---:|---|---|---|---|---|
| Official HOSE market API, `tradingresult/{code}` | Yes | HOSE | Date-filtered; sampled 2018-01-02 through 2026-08-21 | 200 without credentials | Official fee schedule lists paid foreign-investor statistics; no OSS redistribution grant or API rate/caching terms found | **Technical PASS; legal FAIL/UNKNOWN** |
| Official HOSE market API, `foreign/{code}` | Yes | HOSE | Unbounded paginated history; sampled 2009-01-02 through 2026-08-21 | 200 without credentials | Same paid-data/redistribution concern | **Fallback technical PASS; legal FAIL/UNKNOWN** |
| Official HNX listed-equity report | Yes | HNX | UI window limited to most recent month; direct POST sampled 2018–2026 dates when `default-date` matched the requested date; no range API | 200 HTML + direct POST | Commercial package/fee material; no open licence; copyright/all rights reserved | **Technical candidate; legal FAIL/UNKNOWN** |
| Official HNX UPCoM report | Yes, current snapshot | UPCoM | Direct endpoint ignored 2026, 2018, and 2000 date values in probe; identical snapshot | 200 HTML + direct POST | No open licence found; same copyright concern | **History FAIL; legal UNKNOWN** |
| HNX foreign trading by index / industry PDFs | No | HNX/UPCoM aggregates | Daily aggregate/index or industry tables | Public PDF | Copyright notice; no redistribution grant | **Scope FAIL** |
| SSC reporting/statistics pages | No per-symbol daily series found | Market aggregate | Monthly/aggregate publication and reporting obligation | Public pages/PDF | Regulatory publication is not a data licence | **Scope FAIL** |
| SSI FastConnect | Yes in documented API family | HOSE/HNX/UPCOM | Docs expose daily fields, but access-token flow is required | **No** | Commercial/API terms require separate review | **No-auth FAIL** |

## 3. HOSE/HSX official source

### 3.1 First-party references

* Exchange site: <https://www.hsx.vn/>
* Official Swagger UI: <https://api.hsx.vn/mk/swagger/index.html>
* Official Swagger document: <https://api.hsx.vn/mk/swagger/v1/swagger.json>
* Current frontend/API base: `https://api.hsx.vn/mk/api/v1`.
* Date-filtered route (the Swagger `/market-api/api/v1.0` server alias returned the same shape
  in the probe, but the current frontend uses `/mk/api/v1`):
  `GET https://api.hsx.vn/mk/api/v1/market/securities/tradingresult/{code}`
* Official security search used for identity probing:
  `GET https://api.hsx.vn/q/api/v1/search?indexName=securities&field=code%5E2%2Cisin%2Cfigi%2Cintroduction&query={code}&page=1&pageSize=100`
* Official robots file: <https://www.hsx.vn/robots.txt>

The Swagger document describes the server as `/market-api` and the route as
`/api/v1.0/market/securities/tradingresult/{code}`. The current frontend calls the equivalent
`/mk/api/v1` route. Both route forms returned the same response shape in this probe; the
frontend route is the design canonical and the documented alias is a reachability cross-check.
The Swagger exposes `fromDate`, `toDate`, `pageIndex`, and `pageSize`; no security scheme or
credential parameter was present in the document. The official frontend calls the same route
and renders the foreign fields beneath order-matching and put-through volume/value headings.

### 3.2 Exact observed request and response contract

```text
GET https://api.hsx.vn/mk/api/v1/market/securities/tradingresult/FPT
    ?fromDate=2018-01-01
    &toDate=2026-08-21
    &pageIndex=1
    &pageSize=20
```

Observed successful envelope:

```text
{"success": true, "message": null,
 "data": {"list": [...], "object": ..., "paging": {
   "pageIndex": 1, "pageSize": 20, "totalCount": ..., "totalPages": ...
 }}}
```

Relevant source-published component names are:

```text
reportDate                         Unix-seconds session date
symbol                             response identity (padded in some payloads)
mainBuyForeignVolume               order-matching buy volume
mainBuyForeignValue                order-matching buy value
mainSellForeignVolume              order-matching sell volume
mainSellForeignValue               order-matching sell value
bigLotBuyForeignVolume             put-through buy volume
bigLotBuyForeignValue              put-through buy value
bigLotSellForeignVolume            put-through sell volume
bigLotSellForeignValue             put-through sell value
```

The official tariff and UI identify foreign buy/sell share quantity and value fields, but the
per-symbol JSON has no machine-readable unit multiplier. The observed raw values are consistent
with shares/VND, yet that scale is still an inference at the API boundary. The parser must use
the official field labels as provenance, require non-negative whole-valued volume/value
numbers, and reject an unknown scale rather than silently multiply or divide. Written provider
confirmation is required before enabling the public `shares`/`VND` contract.

The normalized totals are explicitly derived for this route:

```text
foreign_buy_volume  = mainBuyForeignVolume  + bigLotBuyForeignVolume
foreign_sell_volume = mainSellForeignVolume + bigLotSellForeignVolume
foreign_buy_value   = mainBuyForeignValue   + bigLotBuyForeignValue
foreign_sell_value  = mainSellForeignValue  + bigLotSellForeignValue
foreign_net_volume  = foreign_buy_volume - foreign_sell_volume
foreign_net_value   = foreign_buy_value   - foreign_sell_value
```

The design must mark all six derived totals with field-level provenance. Missing components
remain `None`; a present zero remains zero. Any published total used by a future source must
be checked against its components and rejected on conflict.

### 3.3 Reachability, pagination, and coverage probes

On 2026-08-22, unauthenticated GET probes returned:

| Symbol sample | Requested window | Rows | Pages | First-page date span | Last-page date span |
|---|---|---:|---:|---|---|
| FPT | 2018-01-01–2026-08-21 | 2,154 | 108 | 2026-07-27–2026-08-21 | 2018-01-02–2018-01-19 |
| VIC | 2018-01-01–2026-08-21 | 2,154 | 108 | 2026-07-27–2026-08-21 | 2018-01-02–2018-01-19 |
| VCB | 2018-01-01–2026-08-21 | 2,154 | 108 | 2026-07-27–2026-08-21 | 2018-01-02–2018-01-19 |

These are reachability samples, not a promise that every security was listed in 2018 or that
every trading session has a row. The source did not provide a listing-date or complete-market
coverage field in this response. The first available session is therefore recorded as
`served_start`, not backfilled to the requested start.

The date-filtered `tradingresult` route capped `pageSize` at 20 in the observed response:
requests for 50, 100, and 1,000 were returned with `paging.pageSize == 20`. The adapter must
request 20, stop at the server-reported page count, reject page-count inconsistencies, and
enforce a client hard ceiling before any unbounded loop. The fallback `foreign` route accepted
100 and returned 45 pages for the 4,401-row sample; it has a separate, less stable cap and must
be probed/validated independently. No published maximum exists.

The endpoint returned `symbol` in the date-filtered response. The parser must trim and
canonicalize it, compare it with the requested symbol, and fail closed on a mismatch. Exchange
identity is source-bound to HOSE; no response from this route may be relabelled HNX or UPCoM.

### 3.4 Official same-host fallback

The official Swagger also exposes:

```text
GET https://api.hsx.vn/mk/api/v1/market/securities/foreign/{code}
    ?pageIndex=1&pageSize=100
```

This route has no date parameters. A probe for the same public symbol returned 4,401 rows in
45 pages at `pageSize=100`, with the last page reaching 2009-01-02. Its field spellings are
`mainBuyerForeign*`/`mainSellerForeign*` and `bigLotBuyerForeign*`/`bigLotSellerForeign*`;
its total foreign volumes matched the main-plus-big-lot sum for all 20 overlapping first-page
dates checked against `tradingresult`. The response does not echo the symbol; the requested
canonical path code is the identity key. It is a possible **whole-result fallback**, not a
second segment to stitch. The client paginates newest-first until the requested start is
passed, filters locally, and fails if the page ceiling is exceeded. Its lack of a server-side
date bound makes it more expensive and less desirable than `tradingresult`.

### 3.5 Legal and operational status

* The official robots file is permissive (`Disallow:` is empty), but robots is a crawl signal,
  not a copyright or redistribution grant.
* HOSE's official market-information fee schedule lists “foreign investor trading statistics”
  as a paid monthly/yearly product and describes fields including security code, foreign buy/
  sell share quantity, buy/sell value, remaining purchasable quantity, and foreign ownership.
  It also lists paid market-data feed/web-service products. Reference:
  <https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf>
* The Swagger `info` object exposed only a title/version; no licence, ToS, rate limit, caching,
  attribution, or redistribution terms were found in the inspected official pages/API
  document.
* No API key, bearer token, login, or `Authorization` header was used in the successful probe.
  No published request-rate limit was located. v1 should default to sequential single-symbol
  paging, max four concurrent bulk workers, no automatic retry storm, and no persistent cache.
* Intermittent HTTP 500 responses were observed on oversized/less stable route probes and by an
  independent official-source verification; retry only bounded transient failures and preserve
  every attempt in diagnostics. There is no SLA evidence.
* **Legal status: FAIL/UNKNOWN / permission required.** The paid fee schedule is strong
  evidence that the same class of data is commercially supplied; it is not by itself a
  prohibition on public web retrieval, but it prevents an OSS redistribution claim. Until HOSE
  confirms terms, package only the parser contract and synthetic fixtures; do not bundle
  responses, persist a dataset, or claim an open-data licence. Runtime attribution should name
  HOSE and the exact dataset/endpoint once an implementation is authorized.

## 4. HNX and UPCoM official source

### 4.1 First-party report pages and request shape

* Listed HNX page: <https://hnx.vn/en-gb/co-phieu-etfs/du-lieu-thi-truong-ny-kq-giao-dich.html?id=1>
* UPCoM page: <https://hnx.vn/en-gb/co-phieu-etfs/du-lieu-thi-truong-uc-kq-giao-dich.html?id=1>
* Listed XHR target:
  `POST https://hnx.vn/ModuleReportStockETFs/Report_MD_TradingResult/ListData_Listed`
* UPCoM XHR target:
  `POST https://hnx.vn/ModuleReportStockETFs/Report_MD_TradingResult/ListData_UPCoM`

The official HTML labels the per-symbol fields as `Security code`, `ISIN code`, `Buy volume`,
`Buy value (VND)`, `Sell volume`, and `Sell value (VND)`. A current direct POST used:

```text
p_keysearch      = dd/mm/yyyy|index|industry|symbol|board|trading-method|default-date
pColOrder        = col_a
pOrderType       = ASC
pCurrentPage     = 1
pRecordOnPage    = 50
pIsSearch        = 1
```

The VND unit is explicit. The volume label is quantity-like (and the Vietnamese table uses
`KL`), but neither the HTML nor the response provides a machine-readable “shares” unit; a
provider confirmation is required before a future adapter makes `volume_unit="shares"` a
rights/semantics claim rather than a documented assumption.

The HTML response is paginated. In a historical listed-date probe with 385 records,
`pRecordOnPage=0` returned all rows, `200` returned 200 rows on page 1 and 185 on page 2, and
values above 200 fell back to a small default. These are observed undocumented behaviors, not
stable API guarantees; a future adapter would hard-cap page size at 200 and validate total
record counts.

For the 2026-08-22 snapshot, the listed page embedded a current search window of
2026-07-21–2026-08-21 and warned in its own script that searches are limited to the first
months of the most recent transactions. A direct listed request for 2026-08-21 returned 299
records. The same POST with the requested date `01/03/2018` and the final `default-date` token
also set to `01/03/2018` returned 385 records; `01/03/2019` returned 378 records. Additional
independent probes covered the same shape on dates in 2020–2026. Keeping the final token at
the current page date instead returned an empty historical result, so the date-token coupling
must be documented if this seam is ever approved. This is technical evidence for an HNX
listed-history candidate, not proof of a stable archive or end-to-end completeness.

The UPCoM endpoint returned 821 current records for 2026-08-21, 2018-08-01, and 2000-01-01,
with identical response bytes in the probe—even when the final date token was changed. It is
therefore a current snapshot and ignores the historical date for this path, not evidence of
UPCoM historical coverage.

The reports are technically reachable without credentials and provide the required gross
buy/sell volume/value plus ISIN. The listed HNX route is a per-session HTML report, not a
server-side date-range API: a 2018–current history would require one request per candidate
trading date and local filtering/pagination. The endpoints provide no documented machine-
readable licence or published rate limit. The direct POST is an undocumented web seam and must
not be treated as a durable OSS source without provider confirmation.

### 4.2 Aggregate HNX evidence is not a substitute

HNX publishes official daily foreign trading by index PDFs, for example:

* <https://owa.hnx.vn/ftp/THONGKEGIAODICH/20251017/INDEX/20251017_ID_Foreigners_trading_by_index.pdf>

Those tables contain HNX/UPCoM/index and sector aggregates, not per-security rows. Older
official `CP` PDFs similarly expose industry/market totals rather than a symbol history. They
cannot satisfy #201's identity and per-symbol coverage contract. The PDF footer says
“Copyright by HANOI Stock Exchange All rights reserved.” This is a direct warning against
assuming that public download permits redistribution.

### 4.3 HNX legal status

The official HNX 2026 service catalogue lists paid packages containing per-security foreign
trading detail (including matched/negotiated buy/sell quantity and value), with contract-based
delivery/technical specifications. References:

* Listed data catalogue: <https://www.hnx.vn/dich-vu-cctt/du-lieu-cung-cap-list.html>
* UPCoM data catalogue: <https://www.hnx.vn/dich-vu-cctt/du-lieu-cung-cap-up.html>
* 2026 official fee PDF:
  <https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf>
* Technical-requirements page: <https://www.hnx.vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html>
* HNX disclaimer: <https://www.hnx.vn/en-gb/khuyen-cao.html>

Direct report responses carried `Cache-Control: private`; no public caching grant was found.
The official hosts did not expose a usable robots policy or open-data licence in this round,
and HNX pages/PDFs identify HNX copyright. **Legal status is FAIL/UNKNOWN / permission or a
licensing contract required.** HNX listed history and UPCoM current data remain out of the v1
enabled chain until reuse terms, endpoint stability, rate limits, and UPCoM history are
resolved.

## 5. Regulator and other official candidates

* The SSC's current consolidated Vietnamese disclosure text (updated through 2026) says in
  Article 37 that an exchange must publish foreign-investor securities trading during market
  hours and publish end-of-day per-security trading/ownership information. It also sets a
  24-hour publication window. This is a **publication obligation**, not a public API,
  open-data licence, or redistribution grant. Reference:
  <https://ssc.gov.vn/cs/idcplg?IdcService=GET_FILE&allowInterrupt=1&dDocName=APPSSCGOVVN1620166107&dID=174608&filename=VBHN+so+10..pdf>
* The older SSC English reference to Circular 213/2012/TT-BTC also described daily/monthly/
  annual reports and five-year electronic retention, but the SSC explicitly warns that the
  English translation is for reference only. It is retained as historical context, not as a
  current legal conclusion:
  <https://ssc.gov.vn/webcenter/contentattachfile/idcplg?IdcService=GET_FILE&IsAttachment=1&Rendition=Circular+No.+213%2F2012%2FTT-BTC&dDocName=APPSSCGOVVN162086066&dID=47092&filename=CIRCULAR+No.213.2012.TT-BTC.pdf>
* SSC pages found in the search round publish market/month aggregate foreign volume/value,
  not a no-auth per-symbol daily dataset. They are evidence sources only, not adapters.
* Official SSI FastConnect documentation describes an `AccessToken` flow before calling its
  market APIs, so it is not a no-auth source for this issue:
  <https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs>

## 6. Build-vs-source-gap conclusion

| Requirement | HOSE official API | HNX listed report | UPCoM report | v1 disposition |
|---|---|---|---|---|
| Per-symbol buy/sell volume | Yes, component fields | Yes, current page | Yes, current snapshot | Normalize; do not mix sources in one result |
| Per-symbol buy/sell VND value | Yes, component fields | Yes, explicitly VND | Yes, explicitly VND | Normalize whole VND values; no scale guessing |
| Daily identity/date | `reportDate` + `symbol` | request date + symbol/ISIN | request page + symbol/ISIN | Validate and fail closed |
| HOSE/HNX/UPCoM target boards | HOSE only | HNX only | UPCoM only | HOSE-first; HNX legal/operational gate; UPCoM source-gap |
| 2018-current date filter | Technically observed for samples | Historical samples work through a date-coupled per-session POST; no range API | date ignored/current snapshot | Do not promise all-board history |
| No-auth request | Observed | Observed | Observed | No-auth is not a licence |
| Open licence/redistribution | Paid-data schedule; no OSS grant found | Paid package catalogue; no OSS grant; copyright signal | Paid package catalogue; no OSS grant; copyright signal | Legal gate before code/ship |
| Published rate limits | Not found | Not found | Not found | Conservative bounded client |

The lawful implementation boundary is consequently:

1. **Design now:** define a source-neutral immutable contract, source provenance, failover
   diagnostics, and a bulk API that can honestly represent unsupported boards and per-symbol
   failures.
2. **First implementation candidate:** HOSE `tradingresult` with the same-host `foreign`
   fallback, subject to written terms/permission. A source success is one complete source
   result; never append HNX/UPCoM rows to it.
3. **HNX:** retain the listed per-session endpoint as a technical candidate, but keep it
   disabled until HNX confirms that the undocumented route and/or a licensed package may be
   used by the OSS client. Do not call the current page a documented archive.
4. **UPCoM:** keep explicitly unavailable until an archival per-symbol source and rights
   evidence are found. Do not reconstruct from index/industry aggregates or use the current
   snapshot as historical data.
