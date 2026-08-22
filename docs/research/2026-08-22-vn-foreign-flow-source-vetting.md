# #201 source-vetting report — Vietnamese equity foreign-investor daily flow

**Research date:** 2026-08-22 (Vietnam time)
**Issue:** #201, accepted source-gated; reviewer packet `tasks/201-vn-equity-foreign-flow-spec.md` at reviewer commit `62e1e32`
**Repository state:** research/design only; no production code and no provider rows committed
**Blacklist compliance:** the mandatory project exclusion was applied to every search. No excluded result was opened, cited, cloned, installed, compared, or used. All evidence below is first-party exchange/regulator documentation or a first-party exchange web/API probe.

## Executive decision

**Disposition: SOURCE-GAP CLOSURE. No source is enabled and no production implementation is
authorized.** The probes found useful technical leads, but no candidate currently satisfies the
complete source gate: no-auth runtime, 2018-current coverage, response-backed identity, exact
units/date semantics, stable field contract, and written OSS/runtime/cache/redistribution terms.

The independent status axes are:

| Candidate | Technical reachability | Historical coverage | Response identity/date | Units/field semantics | Legal/runtime/reuse | TLS chain | Operational stability | Disposition |
|---|---|---|---|---|---|---|---|---|
| HOSE `tradingresult/{code}` | `PASS` observed without credentials | `SAMPLED_ONLY`; three names do not prove market-wide 2018-current completeness | Symbol returned; epoch/session-date convention `UNRESOLVED` | Raw volume/value multiplier and field stability `UNRESOLVED` | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `PASS` under strict-client control | Rate/SLA/cache terms `UNRESOLVED`; intermittent 500 observed | `DISABLED` |
| HOSE `foreign/{code}` | `PASS` observed without credentials | History sampled | Response symbol missing; `RESPONSE_IDENTITY_MISSING_REJECTED` | Component arithmetic observed; units still unresolved | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `PASS` under strict-client control | Unbounded route; no published limit | `DISABLED; not a fallback` |
| HNX listed report | Historical HTTP observations only; current strict-client access fails | Historical samples only; no range/completeness proof | `RESPONSE_DATE_IDENTITY_UNRESOLVED`; request token is not response identity | VND label present; volume scale and field stability `UNRESOLVED` | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `TLS_CHAIN_VERIFICATION_FAIL` | Undocumented HTML seam; rate/cache/SLA `UNRESOLVED` | `DISABLED` |
| HNX UPCoM report | Historical HTTP observations only; current strict-client access fails | `FAIL`; historical date inputs ignored | `RESPONSE_DATE_IDENTITY_UNRESOLVED`; unchanged snapshots do not prove requested date | VND label present; volume semantics unresolved | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `TLS_CHAIN_VERIFICATION_FAIL` | Snapshot behavior undocumented | `DISABLED` |

**Current strict TLS operational axis (rechecked 2026-08-22):** HOSE passed the same
standard-client control, but `hnx.vn` failed strict certificate verification: `curl` reported
error 60 and Python reported `CERTIFICATE_VERIFY_FAILED` because the observed server chain did not
provide a verifiable issuer path. Earlier HNX/UPCoM HTTP observations are historical evidence only;
they do not clear `TLS_CHAIN_VERIFICATION_FAIL` or make the routes currently reproducible. Probes
must never use `--insecure` or `-k`. A valid, verified certificate chain is a separate mandatory
condition before either HNX route can reopen.

* **HOSE/HSX:** a 22 August 2026 probe served sampled 2018-01-01–2026-08-21 windows for
  FPT, VIC, and VCB, but three names do not establish market-wide coverage. The official
  Swagger and tariff do not establish reuse, caching, retention, or redistribution permission.
* **HNX listed:** direct POSTs returned rows for sampled dates when the request token matched the
  requested date, but the response did not provide an authoritative session-date marker. This
  is an undocumented technical observation, not an identity-safe historical source.
* **UPCoM:** the endpoint returned an identical current snapshot for current, 2018, and 2000 date
  inputs, so it cannot support the requested historical contract.
* **SSC/regulator pages, HNX aggregate PDFs, and token-gated commercial API documentation** are
  legal/reference or aggregate evidence, not qualifying no-auth per-symbol sources.

The correction artifact therefore records a **candidate boundary pending source-owner clearance**
only. It does not package a parser contract for shipping, enable a default chain, or imply that
public reachability grants lawful reuse.

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

| Candidate | Per-symbol | Boards | Daily/history evidence | No-auth probe | Legal/reuse evidence | Independent status |
|---|---:|---|---|---|---|---|
| Official HOSE market API, `tradingresult/{code}` | Yes | HOSE | Date-filtered; sampled 2018-01-02 through 2026-08-21 | 200 without credentials | Paid foreign-investor statistics; no OSS/runtime/cache/redistribution grant or rate terms found | **TECHNICAL_REACHABILITY_PASS; SEMANTICS_UNRESOLVED; LEGAL_UNRESOLVED_PERMISSION_REQUIRED** |
| Official HOSE market API, `foreign/{code}` | Not safely response-identified | HOSE | Unbounded paginated history; sampled 2009-01-02 through 2026-08-21 | 200 without credentials | Same paid-data concern | **RESPONSE_IDENTITY_MISSING_REJECTED; not a fallback** |
| Official HNX listed-equity report | Yes in returned HTML rows in historical observations | HNX | UI window limited to most recent month; direct POST sampled 2018–2026 dates when `default-date` matched; no range API or returned session marker | Historical 200 HTML + direct POST; current strict TLS chain fails | Commercial package/fee material; no open licence; copyright/all rights reserved | **TECHNICAL_CANDIDATE_UNDOCUMENTED; TLS_CHAIN_VERIFICATION_FAIL; RESPONSE_DATE_IDENTITY_UNRESOLVED; LEGAL_UNRESOLVED_PERMISSION_REQUIRED** |
| Official HNX UPCoM report | Current snapshot in historical observations | UPCoM | Direct endpoint ignored 2026, 2018, and 2000 date values in probe; identical snapshot | Historical 200 HTML + direct POST; current strict TLS chain fails | No open licence found; same copyright concern | **HISTORICAL_COVERAGE_FAIL; TLS_CHAIN_VERIFICATION_FAIL; LEGAL_UNRESOLVED_PERMISSION_REQUIRED** |
| HNX foreign trading by index / industry PDFs | No | HNX/UPCoM aggregates | Daily aggregate/index or industry tables | Public PDF | Copyright notice; no redistribution grant | **SCOPE_FAIL** |
| SSC reporting/statistics pages | No per-symbol daily series found | Market aggregate | Monthly/aggregate publication and reporting obligation | Public pages/PDF | Regulatory publication is not a data licence | **SCOPE_FAIL** |
| SSI FastConnect | Yes in documented API family | HOSE/HNX/UPCOM | Docs expose daily fields, but access-token flow is required | **No** | Commercial/API terms require separate review | **NO_AUTH_FAIL** |

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

> The following is an observed first-party probe shape, not a stable provider contract and not
> an approved adapter contract. It is retained only to identify source-gap closure evidence.

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
reportDate                         observed integral/epoch-like date field; unit/timezone/session mapping unresolved
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

The normalized component totals and nets are derived for this observed route because the payload
fields shown above are components. A future provider-published net, if present, must be validated
against the exact component difference; a matching published net retains `SOURCE_PUBLISHED`
provenance, while a net computed from components is `DERIVED`.

```text
foreign_buy_volume  = mainBuyForeignVolume  + bigLotBuyForeignVolume
foreign_sell_volume = mainSellForeignVolume + bigLotSellForeignVolume
foreign_buy_value   = mainBuyForeignValue   + bigLotBuyForeignValue
foreign_sell_value  = mainSellForeignValue  + bigLotSellForeignValue
foreign_net_volume  = foreign_buy_volume - foreign_sell_volume
foreign_net_value   = foreign_buy_value   - foreign_sell_value
```

The design must mark every total with field-level provenance. Missing components remain `None`; a
present zero remains zero. Any published total or net used by a future source must be checked
against its components and rejected on conflict; a validated published net must not be relabelled
as derived merely because it equals the arithmetic result.

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
enforce a client hard ceiling before any unbounded loop. The separately observed `foreign` route
accepted 100 and returned 45 pages for the 4,401-row sample; its missing response symbol means it
is rejected regardless of its pagination behavior. No published maximum exists.

The endpoint returned `symbol` in the date-filtered response. The parser must trim and
canonicalize it, compare it with the requested symbol, and fail closed on a mismatch. Exchange
identity is source-bound to HOSE; no response from this route may be relabelled HNX or UPCoM.

### 3.4 Rejected same-host route (not a fallback)

The official Swagger also exposes:

```text
GET https://api.hsx.vn/mk/api/v1/market/securities/foreign/{code}
    ?pageIndex=1&pageSize=100
```

This route has no date parameters. A probe for the same public symbol returned 4,401 rows in
45 pages at `pageSize=100`, with the last page reaching 2009-01-02. Its field spellings are
`mainBuyerForeign*`/`mainSellerForeign*` and `bigLotBuyerForeign*`/`bigLotSellerForeign*`;
its total foreign volumes matched the main-plus-big-lot sum for all 20 overlapping first-page
dates checked against `tradingresult`. The response does **not** echo a symbol. The requested
path token proves only what the client asked for, not what the server returned, so this route
fails the hard response-identity invariant and is **removed from the candidate chain**. It must
not be used as a fallback, whole-result or otherwise, unless first-party evidence adds a
response-backed symbol identity and the source gate is reopened. Its lack of a server-side date
bound is an additional operational concern.

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
  No published request-rate limit was located. This packet authorizes only strict sequential
  single-symbol/bulk paging (`max_concurrency=1`); it makes no concurrency-above-one promise.
  Parallel execution requires written provider terms and a separately reviewed deterministic
  wave/barrier contract, with a shared request/page/attempt ledger, bounded retries, and no
  persistent cache.
* Intermittent HTTP 500 responses were observed on oversized/less stable route probes and by an
  independent official-source verification; retry only bounded transient failures and preserve
  every attempt in diagnostics. There is no SLA evidence.
* **Legal status: LEGAL_UNRESOLVED_PERMISSION_REQUIRED.** The paid fee schedule is strong
  evidence that the same class of data is commercially supplied; it is not by itself a
  prohibition on public web retrieval, but it does not grant OSS runtime or redistribution
  rights. This report is evidence only: no parser, adapter, public model, facade, runtime
  request, cache, fixture containing provider rows, or default source chain is authorized while
  terms remain unresolved. Runtime attribution and retention rules can be recorded only after
  the owner supplies written terms for the exact dataset/endpoint.

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

The sanitized form shapes for the two official routes are distinct and must remain distinct in
any future probe or adapter specification:

```text
POST /ModuleReportStockETFs/Report_MD_TradingResult/ListData_Listed
p_keysearch=dd/mm/yyyy|0|0|SYMBOL|0|ALL|dd/mm/yyyy
pColOrder=col_a&pOrderType=ASC&pCurrentPage=1&pRecordOnPage=50&pIsSearch=1

POST /ModuleReportStockETFs/Report_MD_TradingResult/ListData_UPCoM
p_keysearch=dd/mm/yyyy|0|0|SYMBOL|0|ALL|dd/mm/yyyy|
pColOrder=col_a&pOrderType=ASC&pCurrentPage=1&pRecordOnPage=50&pIsSearch=1
```

The final date token is an input shape only. It is not accepted as the response session date
without an authoritative returned marker.

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
the current page date instead returned an empty historical result. The response itself did not
contain an authoritative session-date marker that could distinguish a requested date from a
server-selected date. The date-token coupling is therefore **response-date identity unresolved**,
not an identity contract; the seam cannot be an enabled adapter without owner evidence or a
returned date field.

The UPCoM endpoint returned 821 current records for 2026-08-21, 2018-08-01, and 2000-01-01,
with identical response bytes in the probe—even when the final date token was changed. It is
therefore a current snapshot and ignores the historical date for this path, not evidence of
UPCoM historical coverage.

Historical reports were observed without credentials and provided the required gross
buy/sell volume/value plus ISIN, but the current strict standard-client probe cannot verify the
`hnx.vn` TLS chain. The listed HNX route is a per-session HTML report, not a server-side date-range
API: a 2018–current history would require one request per candidate trading date and local
filtering/pagination. The endpoints provide no documented machine-readable licence or published
rate limit. The direct POST is an undocumented web seam with unresolved response-date identity and
`TLS_CHAIN_VERIFICATION_FAIL`; it must not be treated as a durable OSS source without verified
TLS, provider confirmation, and the other reopen evidence.

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
and HNX pages/PDFs identify HNX copyright. **Legal status is
`LEGAL_UNRESOLVED_PERMISSION_REQUIRED`.** HNX listed history remains both technically
undocumented and response-date-identity unresolved; UPCoM remains a historical-coverage
failure. Neither is enabled until reuse terms, endpoint stability, rate limits, identity
semantics, and UPCoM history are resolved.

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

| Requirement | HOSE official API | HNX listed report | UPCoM report | source-gap disposition |
|---|---|---|---|---|
| Per-symbol buy/sell volume | Component fields observed; raw scale unresolved | Rows observed on current/historical probes; volume scale unresolved | Current snapshot rows | No implementation until unit evidence is written |
| Per-symbol buy/sell VND value | Field labels observed; raw scale unresolved | Explicit VND label | Explicit VND label | No implementation until source contract is approved |
| Daily identity/date | `reportDate` + `symbol` returned, but epoch/session semantics unresolved | Requested date plus rows; authoritative returned session marker absent | Requested page plus rows; date ignored | Require response-backed identity and exact date semantics |
| HOSE/HNX/UPCoM target boards | HOSE only | HNX only | UPCoM only | No cross-board fallback or stitching |
| 2018-current date filter | Technically sampled for three names | Date-coupled per-session observation, no range API or completeness proof | Date ignored/current snapshot | Historical coverage remains unapproved |
| No-auth request | Observed | Observed | Observed | No-auth is not a licence |
| Open licence/redistribution | Paid-data schedule; no OSS grant found | Paid package catalogue; no OSS grant; copyright signal | Paid package catalogue; no OSS grant; copyright signal | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` |
| Published rate limits | Not found | Not found | Not found | No runtime fan-out until provider terms authorize it |

The candidate boundary is consequently **pending source-owner clearance**:

1. **No source is enabled:** no parser, adapter, public model, facade, runtime request, cache,
   fixture containing provider rows, push, or issue close is authorized by this report.
2. **Reopen only with owner evidence:** the source owner must provide written permission and
   technical terms for no-paid automated runtime use, exact units, response identity/date,
   field stability, publication cadence/lag, rate limits, caching/retention, attribution, and
   downstream redistribution. The full checklist is in Section 7.
3. **HNX:** retain the listed POST only as a research lead with unresolved response-date identity;
   do not label it a historical archive or use request-date coupling as proof.
4. **UPCoM:** keep explicitly unavailable until an archival per-symbol source and rights evidence
   are found. Do not reconstruct from index/industry aggregates or use the current snapshot as
   historical data.

## 7. Source-gap closure and reopen criteria

### 7.1 Status vocabulary

The report uses independent axes rather than collapsing evidence into one ambiguous combined
status:

* `PASS` means the specific property was positively evidenced for the stated route and probe;
* `FAIL` means the probe demonstrated that the property does not hold (for example, UPCoM
  historical date inputs were ignored);
* `UNRESOLVED` means evidence is absent or insufficient, not that a legal prohibition was proved;
* `SAMPLED_ONLY` means observations are not a market-wide or completeness guarantee;
* `TLS_CHAIN_VERIFICATION_FAIL` means the current standard client cannot verify the official
  server certificate chain; earlier HTTP success does not clear this axis;
* `DISABLED` is the current engineering disposition, not a source fact.

The current disposition is `DISABLED` for every candidate. A candidate can be reopened only when
all applicable technical, semantic, coverage, operational, and legal axes below are evidenced
for the same endpoint/dataset. No-auth reachability, a public UI, a permissive robots file, or a
paid fee schedule is not owner permission.

### 7.2 Owner/contact path

The owner path must be first-party and must identify the exact dataset rather than relying on a
general website contact:

| Candidate | Owner | Official contact/data-service path |
|---|---|---|
| HOSE `tradingresult/{code}` | Ho Chi Minh Stock Exchange (HOSE/HSX) market-information/data-service owner | [HOSE contact page](https://www.hsx.vn/vi/lien-he); [data-feed page](https://www.hsx.vn/vi/data-feed); [official information-service tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf) |
| HNX listed report | Hanoi Stock Exchange (HNX) information-service/data owner | [HNX contact page](https://www.hnx.vn/vi-vn/lien-he.html); [HNX listed-data catalogue](https://www.hnx.vn/dich-vu-cctt/du-lieu-cung-cap-list.html); [technical-requirements page](https://www.hnx.vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html) |
| HNX UPCoM report | Hanoi Stock Exchange (HNX) information-service/data owner | [HNX contact page](https://www.hnx.vn/vi-vn/lien-he.html); [HNX UPCoM catalogue](https://www.hnx.vn/dich-vu-cctt/du-lieu-cung-cap-up.html); [technical-requirements page](https://www.hnx.vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html) |

No individual contact is inferred from a web page. A reopen packet must record the official
contact/channel, request date, responding owner/team, written artifact or reference number, and
the exact endpoint/dataset covered by the response.

### 7.3 Conjunctive reopen evidence

At least one candidate must obtain written owner evidence for every applicable item:

1. No-paid automated OSS runtime use, including whether the public frontend/API/XHR route is
   intended for automated clients rather than only interactive UI use.
2. Exact endpoint, dataset/version, supported boards, and whether rows may be redistributed by a
   downstream open-source package.
3. Raw volume multiplier and an explicit statement that volume means shares; exact value meaning,
   raw scale, currency, and whether VND values are whole VND or displayed units.
4. `reportDate` epoch convention, timezone, exchange-session-date mapping, and an authoritative
   returned date marker. A request parameter or path token alone never proves response identity.
5. Response-backed canonical symbol/ISIN identity, including invalid-symbol, empty, error, and
   schema-drift response shapes. The requested path token is not a substitute for a returned
   identity field.
6. Stable JSON/HTML field names, field definitions, component/total arithmetic, and a change
   notification or versioning policy.
7. Dataset inception, per-symbol listing/delisting, symbol rename, board transfer, and corporate-
   action identity rules; no assumption that a symbol's 2018 row exists.
8. Publication cadence, current-session availability, end-of-day publication lag, historical
   retention floor, and whether missing sessions are expected or represent an outage.
9. Pagination limits, request-rate/concurrency limits, retry guidance, caching/retention/replay
   permission, attribution, trademark/use-of-name constraints, and downstream redistribution.
10. An official written artifact plus an official-host-only opt-in probe reproducing the contract;
    sanitized counts/digests may be committed, but raw provider rows remain untracked.

Only after all required axes for one candidate are `PASS`/approved may a new correction packet
request a design gate. The next gate must explicitly re-check the exact owner evidence, source
identity tuple, unit proof, coverage proof, request budget, and synthetic verification matrix.

## 8. Reproducible official-host-only probe procedure

This appendix is opt-in research tooling, not a CI test or an implementation recipe. The only
allowlisted hosts are `api.hsx.vn` and `hnx.vn`; redirects are rejected and the effective URL is
recorded and compared with the requested URL. It uses no credentials, cookies, bearer headers,
third-party hosts, or persistent cache. Raw responses must stay under `/tmp/vnfin-201-probes/` (or
another ignored directory) and must never be committed. The current HNX TLS failure is an expected
recordable outcome: the script continues after a curl failure so it can write a complete status
manifest. Strict TLS is mandatory; no `--insecure` or `-k` flag is permitted.

The sanitized manifest records client/package/repository versions, timestamp/timezone, the exact
method/URL/query/form/body/header request shape, explicit absence of Cookie/Authorization/API-key
material, curl exit code, HTTP status, effective URL, redirect rejection, expected content type,
`transport_accepted`, `body_accepted`, final `accepted`, cache-control, byte count, a canonical
SHA-256 digest of sanitized aggregate metadata, row/field observations only after acceptance,
date-bound computation status, and syntactic versus authoritative date-marker status. The complete
sanitized aggregate is embedded in `manifest.txt` between explicit delimiters. It contains no
raw-response hash; raw output remains ignored and private.

For HNX and UPCoM, body acceptance is route-specific: after exact MIME normalization to the lower-
case media type before any `;` parameters, one report table must contain one heading row with all
six exact normalized fields (`Security code`, `ISIN code`, `Buy volume`, `Buy value`, `Sell volume`,
`Sell value`) and a distinct non-heading `td` row with non-empty values at those six mapped
columns. Every mapped data value must also be outside `REQUIRED_HEADINGS`, regardless of its column;
this rejects a cyclic or otherwise permuted heading-only row. A generic document, maintenance page,
unrelated table, off-table field phrases, or MIME such as `text/htmlx` is rejected and produces no
payload observations. A valid report table nested inside layout HTML is allowed when this table-local
contract passes.

```bash
set -euo pipefail
out=/tmp/vnfin-201-probes/$(date +%Y%m%d-%H%M%S)
mkdir -p "$out"
manifest="$out/manifest.txt"
printf 'probe_time=%s\n' "$(date '+%d/%m/%Y - %A %H:%M %z')" > "$manifest"
python --version >> "$manifest"
curl --version | sed -n '1p' >> "$manifest"
git -C /home/hungson175/dev/vnfin-oss rev-parse HEAD >> "$manifest"
python - <<'PY' >> "$manifest"
try:
    from importlib.metadata import version
    print("vnfin_version=" + version("vnfin"))
except Exception:
    print("vnfin_version=uninstalled-or-local-checkout")
PY
printf '%s\n' \
  'sent_headers=Accept,Content-Type(where form),User-Agent only' \
  'cookie=absent' 'authorization=absent' 'api_key=absent' \
  'tls=standard-verification-required' 'insecure_flags=forbidden' >> "$manifest"

# This is the exact sanitized request shape. HNX uses an explicitly unfiltered form (empty
# symbol component), so the probe does not pretend that a HOSE-only symbol is board-valid.
cat > "$out/requests.json" <<'JSON'
{
  "hose": {
    "method": "GET",
    "url": "https://api.hsx.vn/mk/api/v1/market/securities/tradingresult/FPT?fromDate=2018-01-01&toDate=2026-08-21&pageIndex=1&pageSize=20",
    "query": {"fromDate": "2018-01-01", "toDate": "2026-08-21", "pageIndex": "1", "pageSize": "20"},
    "form": null,
    "headers": ["Accept: application/json", "User-Agent: vnfin-201-probe/1"],
    "auth_headers_absent": true
  },
  "hnx_listed": {
    "method": "POST",
    "url": "https://hnx.vn/ModuleReportStockETFs/Report_MD_TradingResult/ListData_Listed",
    "query": {},
    "form": {"p_keysearch": "01/03/2018|0|0||0|ALL|01/03/2018", "pColOrder": "col_a", "pOrderType": "ASC", "pCurrentPage": "1", "pRecordOnPage": "50", "pIsSearch": "1"},
    "headers": ["Accept: text/html", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8", "User-Agent: vnfin-201-probe/1"],
    "auth_headers_absent": true
  },
  "upcom": {
    "method": "POST",
    "url": "https://hnx.vn/ModuleReportStockETFs/Report_MD_TradingResult/ListData_UPCoM",
    "query": {},
    "form": {"p_keysearch": "01/03/2018|0|0||0|ALL|01/03/2018|", "pColOrder": "col_a", "pOrderType": "ASC", "pCurrentPage": "1", "pRecordOnPage": "50", "pIsSearch": "1"},
    "headers": ["Accept: text/html", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8", "User-Agent: vnfin-201-probe/1"],
    "auth_headers_absent": true
  }
}
JSON
cat "$out/requests.json" >> "$manifest"

printf 'name\tcurl_exit_code\thttp_status\teffective_url\tredirect_rejected\tcontent_type\texpected_content_type\tbody_bytes\ttransport_accepted\tbody_accepted\taccepted\n' > "$out/status.tsv"

record_status() {
  name="$1"
  requested_url="$2"
  output_file="$3"
  expected_content_type="$4"
  curl_exit_code="$5"
  http_status=000
  effective_url=not_observed
  if IFS=$'\t' read -r observed_status observed_url < "$out/$name.transport"; then
    if [ -n "${observed_status:-}" ]; then
      http_status="$observed_status"
    fi
    if [ -n "${observed_url:-}" ]; then
      effective_url="$observed_url"
    fi
  fi
  body_bytes=0
  if [ -f "$out/$output_file" ]; then
    body_bytes=$(wc -c < "$out/$output_file")
  fi
  content_type=$(awk 'BEGIN{IGNORECASE=1} /^[[:space:]]*content-type[[:space:]]*:/ {
    value=$0
    sub(/^[^:]*:/, "", value)
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
    split(value, parts, ";")
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", parts[1])
    print tolower(parts[1])
    exit
  }' "$out/$name.headers")
  redirect_rejected=false
  case "$http_status" in 3??) redirect_rejected=true ;; esac
  if [ "$effective_url" != "$requested_url" ]; then redirect_rejected=true; fi
  if [ "$curl_exit_code" -eq 47 ]; then redirect_rejected=true; fi
  transport_accepted=false
  if [ "$curl_exit_code" -eq 0 ] \
     && [ "$http_status" -eq 200 ] \
     && [ "$effective_url" = "$requested_url" ] \
     && [ "$redirect_rejected" = false ]; then
    transport_accepted=true
  fi
  body_accepted=false
  if [ "$transport_accepted" = true ] \
     && [ "$body_bytes" -gt 0 ] \
     && [ "$content_type" = "$expected_content_type" ]; then
    case "$name" in
      hose)
        if python -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p.get("success") is True and isinstance((p.get("data") or {}).get("list"), list)' "$out/$output_file"; then
          body_accepted=true
        fi
        ;;
      hnx|upcom)
        if python - "$out/$output_file" <<'PY'
from html.parser import HTMLParser
import pathlib
import re
import sys

REQUIRED_HEADINGS = {
    "security code",
    "isin code",
    "buy volume",
    "buy value",
    "sell volume",
    "sell value",
}

def normalize_cell(text):
    text = " ".join(text.split()).lower()
    return re.sub(r"\s*\(vnd\)$", "", text).strip()

class ReportShapeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table_stack = []
        self.invalid = False

    def handle_starttag(self, tag, _attrs):
        tag = tag.lower()
        if tag == "table":
            state = {"rows": [], "row": None, "cell": None, "cell_tag": None}
            self.tables.append(state)
            self.table_stack.append(state)
        elif not self.table_stack:
            return
        elif tag == "tr":
            state = self.table_stack[-1]
            if state["row"] is not None:
                self.invalid = True
            state["row"] = []
        elif tag in {"th", "td"}:
            state = self.table_stack[-1]
            if state["row"] is None or state["cell"] is not None:
                self.invalid = True
            state["cell"] = []
            state["cell_tag"] = tag

    def handle_endtag(self, tag):
        tag = tag.lower()
        if not self.table_stack:
            return
        state = self.table_stack[-1]
        if tag in {"th", "td"}:
            if state["cell"] is None or state["cell_tag"] != tag:
                self.invalid = True
            elif state["row"] is not None:
                state["row"].append((tag, normalize_cell(" ".join(state["cell"]))))
            state["cell"] = None
            state["cell_tag"] = None
        elif tag == "tr":
            if state["row"] is None or state["cell"] is not None:
                self.invalid = True
            elif state["row"]:
                state["rows"].append(state["row"])
            state["row"] = None
        elif tag == "table":
            if state["row"] is not None or state["cell"] is not None:
                self.invalid = True
            self.table_stack.pop()

    def handle_data(self, data):
        if self.table_stack and self.table_stack[-1]["cell"] is not None:
            self.table_stack[-1]["cell"].append(data)

parser = ReportShapeParser()
parser.feed(pathlib.Path(sys.argv[1]).read_text(errors="replace"))
parser.close()

def report_table_ok(table):
    for heading_index, heading_row in enumerate(table["rows"]):
        heading_positions = {}
        duplicate_heading = False
        for column, (_tag, cell) in enumerate(heading_row):
            if cell in REQUIRED_HEADINGS:
                if cell in heading_positions:
                    duplicate_heading = True
                heading_positions[cell] = column
        if duplicate_heading or set(heading_positions) != REQUIRED_HEADINGS:
            continue
        for data_index, data_row in enumerate(table["rows"]):
            if data_index == heading_index:
                continue
            if any(tag != "td" for tag, _cell in data_row):
                continue
            if max(heading_positions.values()) >= len(data_row):
                continue
            data_values = {
                heading: data_row[column][1]
                for heading, column in heading_positions.items()
            }
            if any(not value for value in data_values.values()):
                continue
            if any(value in REQUIRED_HEADINGS for value in data_values.values()):
                continue
            return True
    return False

shape_ok = not parser.invalid and not parser.table_stack and any(
    report_table_ok(table) for table in parser.tables
)
raise SystemExit(0 if shape_ok else 1)
PY
        then
          body_accepted=true
        fi
        ;;
    esac
  fi
  accepted=false
  if [ "$transport_accepted" = true ] && [ "$body_accepted" = true ]; then
    accepted=true
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$name" "$curl_exit_code" "$http_status" "$effective_url" "$redirect_rejected" \
    "$content_type" "$expected_content_type" "$body_bytes" "$transport_accepted" \
    "$body_accepted" "$accepted" \
    >> "$out/status.tsv"
}

run_probe() {
  name="$1"
  requested_url="$2"
  output_file="$3"
  expected_content_type="$4"
  shift 4
  : > "$out/$name.headers"
  : > "$out/$name.transport"
  : > "$out/$name.stderr"
  if curl --proto '=https' --proto-redir '=https' --fail --silent --show-error \
    --max-redirs 0 --max-time 25 \
    "$@" -D "$out/$name.headers" \
    --write-out '%{http_code}\t%{url_effective}\n' \
    "$requested_url" -o "$out/$output_file" \
    > "$out/$name.transport" 2> "$out/$name.stderr"; then
    curl_exit_code=0
  else
    curl_exit_code=$?
  fi
  record_status "$name" "$requested_url" "$output_file" "$expected_content_type" "$curl_exit_code"
}

# Official HOSE route; no Authorization, Cookie, or API key.
run_probe hose \
  'https://api.hsx.vn/mk/api/v1/market/securities/tradingresult/FPT?fromDate=2018-01-01&toDate=2026-08-21&pageIndex=1&pageSize=20' \
  hose.json \
  application/json \
  --header 'Accept: application/json' \
  --header 'User-Agent: vnfin-201-probe/1'

# Official HNX listed report. Empty symbol component is deliberate; request-date/default-date is
# input only and never accepted as response identity without an authoritative returned marker.
run_probe hnx \
  'https://hnx.vn/ModuleReportStockETFs/Report_MD_TradingResult/ListData_Listed' \
  hnx.html \
  text/html \
  --header 'Accept: text/html' \
  --header 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  --header 'User-Agent: vnfin-201-probe/1' \
  -X POST \
  --data-urlencode 'p_keysearch=01/03/2018|0|0||0|ALL|01/03/2018' \
  --data-urlencode 'pColOrder=col_a' \
  --data-urlencode 'pOrderType=ASC' \
  --data-urlencode 'pCurrentPage=1' \
  --data-urlencode 'pRecordOnPage=50' \
  --data-urlencode 'pIsSearch=1'

# Official HNX UPCoM report; retain a separate route and complete unfiltered form shape.
run_probe upcom \
  'https://hnx.vn/ModuleReportStockETFs/Report_MD_TradingResult/ListData_UPCoM' \
  upcom.html \
  text/html \
  --header 'Accept: text/html' \
  --header 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  --header 'User-Agent: vnfin-201-probe/1' \
  -X POST \
  --data-urlencode 'p_keysearch=01/03/2018|0|0||0|ALL|01/03/2018|' \
  --data-urlencode 'pColOrder=col_a' \
  --data-urlencode 'pOrderType=ASC' \
  --data-urlencode 'pCurrentPage=1' \
  --data-urlencode 'pRecordOnPage=50' \
  --data-urlencode 'pIsSearch=1'

cat "$out/status.tsv" >> "$manifest"
for response in hose.json hnx.html upcom.html; do
  if [ -f "$out/$response" ]; then
    wc -c "$out/$response" >> "$manifest"
  fi
done
awk 'BEGIN{IGNORECASE=1} /^(HTTP\/|content-type:|cache-control:)/ {print}' \
  "$out/hose.headers" "$out/hnx.headers" "$out/upcom.headers" >> "$manifest"

# Emit only a canonical, sanitized aggregate. The HNX marker state distinguishes an empty/no-body
# TLS failure from a successful response with no marker. Identity booleans require non-empty rows.
python - "$out" <<'PY'
import hashlib, json, pathlib, re, sys

out = pathlib.Path(sys.argv[1])

def read_json(path: pathlib.Path):
    if not path.is_file() or path.stat().st_size == 0:
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None

def status_rows():
    rows = {}
    for line in (out / "status.tsv").read_text().splitlines()[1:]:
        name, rc, http, effective, redirect, content_type, expected_content_type, body_bytes, transport, body, accepted = line.split("\t", 10)
        rows[name] = {
            "curl_exit_code": int(rc),
            "http_status": int(http),
            "effective_url": effective,
            "redirect_rejected": redirect == "true",
            "content_type": content_type,
            "expected_content_type": expected_content_type,
            "body_bytes": int(body_bytes),
            "transport_accepted": transport == "true",
            "body_accepted": body == "true",
            "accepted": accepted == "true",
        }
    return rows

statuses = status_rows()
accepted_hose = statuses["hose"]["accepted"]
hose = read_json(out / "hose.json") if accepted_hose else None
hose = hose if isinstance(hose, dict) else {}
rows = ((hose.get("data") or {}).get("list") or [])

aggregate = {
    "probe_status": statuses,
    "hose_success": hose.get("success"),
    "hose_row_count": len(rows),
    "hose_fields": sorted({k for row in rows if isinstance(row, dict) for k in row}),
    "hose_has_symbol": accepted_hose and bool(rows) and all(isinstance(row, dict) and "symbol" in row for row in rows),
    "hose_has_reportDate": accepted_hose and bool(rows) and all(isinstance(row, dict) and "reportDate" in row for row in rows),
    "hose_reportDate_token_count": sum(
        isinstance(row, dict) and isinstance(row.get("reportDate"), int)
        and not isinstance(row.get("reportDate"), bool)
        for row in rows
    ),
    "hose_returned_date_bounds": "not_computed_owner_semantics_unresolved",
    "hose_reportDate_semantics": "observed_integral_or_epoch_like_unresolved",
    "hnx_shape": {},
}
for name in ("hnx", "upcom"):
    path = out / f"{name}.html"
    accepted_html = statuses[name]["accepted"]
    html = path.read_text(errors="replace") if accepted_html and path.is_file() and path.stat().st_size else ""
    hnx_status = statuses[name]
    marker = (
        "not_observed_transport_rejected"
        if not hnx_status["transport_accepted"]
        else "not_observed_empty"
        if hnx_status["body_bytes"] == 0
        else "not_observed_body_rejected"
        if not hnx_status["body_accepted"]
        else "present"
        if re.search(r"(?:sessionDate|tradingDate|data-session-date)", html, re.I)
        else "absent"
    )
    aggregate["hnx_shape"][name] = {
        "bytes": len(html.encode()),
        "row_like_tags": len(re.findall(r"<tr\b", html, re.I)) if accepted_html else 0,
        "has_security_code": bool(html) and bool(re.search(r"security\s+code", html, re.I)),
        "has_isin": bool(html) and bool(re.search(r"isin", html, re.I)),
        "has_buy_volume": bool(html) and bool(re.search(r"buy\s+volume", html, re.I)),
        "has_sell_volume": bool(html) and bool(re.search(r"sell\s+volume", html, re.I)),
        "returned_date_bounds": "not_computed_owner_semantics_unresolved",
        "syntactic_date_marker": marker,
        "authoritative_date_marker": "unresolved_owner_evidence",
        "identity_assertion": "not_applicable_unfiltered_probe" if accepted_html else "not_observed_rejected_body",
    }
canonical = json.dumps(aggregate, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
(out / "sanitized-aggregate.json").write_text(canonical + "\n")
(out / "sanitized-aggregate.sha256").write_text(
    hashlib.sha256(canonical.encode()).hexdigest() + "\n"
)
PY
printf '[sanitized-aggregate]\n' >> "$manifest"
cat "$out/sanitized-aggregate.json" >> "$manifest"
printf '\n[/sanitized-aggregate]\n' >> "$manifest"
printf 'sanitized_aggregate_sha256=%s\nmanifest_complete=true\n' \
  "$(cat "$out/sanitized-aggregate.sha256")" >> "$manifest"
```

The procedure must be rerun only after a source-owner response or a materially changed official
contract. A transport/body-accepted response is recorded as reachability and shape evidence only; a
2xx status other than the exact required `200` (including an empty `204`) is transport-rejected, and
a rejected transport or body produces no payload observations. Neither outcome promotes a
candidate, authorizes reuse, or establishes unit/date/identity semantics.

The offline mock gate includes a generic HNX/UPCoM maintenance body such as
`<html><body>Maintenance</body></html>`, an unrelated two-row layout table with the six phrases
outside that table, and wrong media types `text/htmlx`, `text/html:evil`, and
`application/json:evil`; each must retain `transport_accepted=true` only when its HTTP envelope is
otherwise valid, but set `body_accepted=false`, `accepted=false`, and emit no report-field
observations. The same-table negatives also include six empty `td` cells, whitespace-only cells,
heading labels repeated as a `td` row, a cyclic/permuted heading-only `td` row (for example,
`ISIN code`, `Buy volume`, `Buy value`, `Sell volume`, `Sell value`, `Security code`), and populated
cells shifted away from the required heading columns. The parser must reject any mapped value that
belongs to `REQUIRED_HEADINGS`, even when it appears under a different heading. A valid report table
nested inside layout HTML remains an accepted positive when its mapped cells are populated. A single
table containing the exact heading row and distinct data row is the only HTML body accepted by this
probe sketch.
