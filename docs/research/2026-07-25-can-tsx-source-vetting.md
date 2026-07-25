# Canadian Equity Index Source Vetting — S&P/TSX Composite, S&P/TSX 60, S&P/TSX Venture Composite

- **Date:** 2026-07-25
- **Author:** vnfin-oss research pass (redo after design-gate BLOCK on prior pass)
- **Target identities (NATIVE INDEX POINTS ONLY — no ETF/futures/neighboring-index proxy):**
  1. S&P/TSX Composite Index
  2. S&P/TSX 60 Index
  3. S&P/TSX Venture Composite Index

## Clean-room statement

This pass excluded VNStock/VNStock-derived material throughout. Every web search appended
`-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"`. No VNStock
repo, site, PyPI package, or VNStock-derived snippet/schema was opened, read, cloned, or cited at any
point in this research.

---

## 1. S&P Dow Jones Indices (S&P DJI) — the official index administrator

- **Ownership/operator:** S&P Dow Jones Indices LLC (joint venture, S&P Global + CME Group), the
  administrator that calculates/owns all three target indices.
- **URL/endpoint:** `https://www.spglobal.com/spdji/en/indices/equity/sp-tsx-composite-index/`
  (methodology/marketing page); `https://www.spglobal.com/spdji/en/brochure/article/api-data-solutions-brochure/`
  ("API Data Solutions" brochure).
- **Auth requirements:** Not documented publicly. The brochure page and PDF describe an "API Data
  Solutions" product for on-demand programmatic access to index constituents/weights/GICS
  classifications, delivered historically via S&P DJI's proprietary Universal File Format (UFF) for
  batch/end-of-day delivery; language throughout is subscriber-oriented ("Subscribers can gain access
  to…") with no visible self-serve signup form, published pricing, or public API key registration flow.
- **Historical span/frequency:** Not documented publicly beyond "data packages distributed after the
  relevant market's close" (i.e., EOD).
- **Pagination/rate limits:** Not documented publicly (page unreachable — see below).
- **Redistribution/licensing posture:** Institutional/subscriber licensing model implied throughout
  (same family as TMX's exchange-distribution agreements, since S&P DJI licenses TMX to
  administer/distribute S&P/TSX data — see TMX section).
- **Dated reachability (2026-07-25):** `spglobal.com/spdji/...` brochure and PDF pages returned
  **HTTP 403** on direct fetch; findings above are from third-party search-index snippets only, not a
  directly read primary page.
- **Identity coverage:** S&P DJI unambiguously administers all 3 target indices (confirmed via its own
  methodology page title), but no evidence of a *self-serve, individually-licensable* API tier was
  found — only an institutional "API Data Solutions" brochure with no visible retail/individual
  onboarding path.
- **Category: not exposed through a lawful [self-serve] API** — bounded: this is based on incomplete
  evidence (pages 403'd); a subscriber-sales-gated API product exists in principle but no path for an
  individual OSS user to self-provision access was found.

---

## 2. TMX Datalinx (TMX Group) — the licensed Canadian distributor

TMX Group operates the Toronto Stock Exchange / TSX Venture Exchange and is licensed by S&P DJI to be
the primary commercial distributor of official S&P/TSX index-level data. **This is the main correction
from the prior pass** — see the (a)-(e) breakdown below.

- **Ownership/operator:** TMX Group Limited, via its "TMX Datalinx" data-services division
  (`tmxwebstore.com` storefront, `tmxinfoservices.com` marketing/reference pages,
  `docs.tmxanalytics.com` developer docs).
- **URLs probed directly (2026-07-25):**
  - `https://www.tmxwebstore.com/products/sptsx-historical-indices-tick-by-tick` → **HTTP 403**
  - `https://www.tmxwebstore.com/products/sp-tsx-equity-index-products` → not directly fetchable (403 pattern)
  - `https://www.tmxwebstore.com/products/custom-queries-pay-per-use-ppu` → **HTTP 403**
  - `https://www.tmxwebstore.com/faq` → **HTTP 403**
  - `https://www.tmxwebstore.com/terms-of-use` → not directly fetchable (403 pattern)
  - `https://docs.tmxanalytics.com/` → **HTTP 403**
  - `https://www.tmxinfoservices.com/corporate-reference-data/historical-data/tmx-historical-market-data-online-custom-queries` → **HTTP 403**
  - Tried multiple browser-like User-Agents/headers via both `curl` and `WebFetch`; every TMX-family
    domain returned 403 to this agent's fetch attempts. All findings below therefore come from
    third-party search-engine indexed snippets of these same pages (not a directly-read primary
    document) — flagged explicitly per finding.

### (a) Can TMX/S&P DJI adapter *code* be distributed?
No evidence found that distributing client/adapter *code* that calls TMX's service is restricted.
Nothing in any snippet addresses code distribution at all — this was not, as expected, a live issue.

### (b) Can each end user obtain their OWN license/access (real self-serve product)?
**Yes, evidenced.** Search-indexed FAQ/product-page content states:
- "A TMX Datalinx Webstore account is required, which is **free to create**" (via Okta registration).
- "Custom Queries - Pay Per Use (PPU)" is a named, individually-purchasable product: *"Pricing is
  subject to a minimum of $C163.53 per month, which is the minimum monthly charge for the total of
  purchases by standard products, custom queries, trades & quotes queries and on-line standard product
  file purchases during the month."*
- This is a real, individually-purchasable, non-enterprise-negotiated product — a materially different
  picture from the prior pass's framing of TMX as enterprise-sales-only.

### (c) Does the license forbid the *library* from redistributing/caching provider rows (vs. each user fetching their own copy)?
**Yes — but this is the standard "single end user" per-seat clause, not a blanket architecture ban.**
Indexed Terms-of-Use content states: *"Unless otherwise indicated, prices are for a single end user,
and do not include redistribution rights… prices are intended for direct subscribers and do not
reflect pricing for redistribution."* And: *"You will be required to accept a Market Data Services
Agreement, or other end user license agreement, for each Product you purchase."*
This reads as: TMX forbids one licensee from reselling/rebroadcasting the raw data feed to other
people (the distributor-vs-end-user pricing split the entire market-data industry uses) — it does
**not**, on the evidence available, forbid an individual licensee from running their own script/library
against their own account/token for their own use. This mirrors exactly how the project's existing
Alpha Vantage BYOK pattern already works (each user brings their own key/license), which is the
corrected legal framing the reviewer asked for.

### (d) Is there a documented, automatable API (vs. only gated manual/web/email delivery)?
**Yes — and this contradicts the pre-registered hypothesis that "no automatable API" would be the real
blocker.** Third-party search-indexed FAQ content directly states TMX Datalinx offers:
- A **REST-based API**: *"You can use a CURL based request to GET your data via a REST based API
  call… returns data in a machine-readable format suitable for integration into applications,
  databases, and workflows."*
- An **SFTP service** (account-credential or key-based, OpenSSH keys up to 8192 bits, 30-day file
  retention on the SFTP server).
- **Token-based auth**: *"Tokens are valid for 1 year. When the Token expires, you must login to TMX
  Webstore in order to reset it, a new one will then be issued."* This is architecturally an API-key
  model, not fundamentally different in shape from Alpha Vantage's.
- A dedicated developer docs subdomain exists (`docs.tmxanalytics.com`), though it 403'd on direct
  fetch and its content could not be independently read.

This is the single biggest correction from the prior pass: **the real blocker is not "no automatable
API."** A documented REST/SFTP delivery mechanism does exist.

### (e) Is the product practical/compatible with this library's BYOK posture?
**Genuinely unresolved, not conclusively blocked.** Two concrete frictions, both evidenced:
1. **Cost floor:** the Pay-Per-Use custom-queries product carries a **minimum monthly charge of
   ≈C$163.53**, i.e. every user needs a *paid* subscription with a real recurring cost floor, unlike
   Alpha Vantage's genuinely free tier. This is a materially different economics than the existing BYOK
   pattern, even though the auth *shape* (per-user token) is similar.
2. **Unread EULA text:** the actual "Market Data Services Agreement" / per-product end-user license
   text — which would definitively answer whether an individual's own automated script/software is
   permitted use under (c) — is **sign-in-gated** and could not be read directly (every TMX domain
   403'd this agent on every attempt, with multiple User-Agents). The redistribution language quoted
   above is reassuring but is pricing-page boilerplate, not the actual signed license clause set.

- **Historical span/frequency:** Search-indexed product descriptions state TMX's S&P/TSX index
  products include *"comprehensive index level files, constituent data files, corporate action files,
  and index notices"* and that *"historical market data available for download or via API delivery is
  available forever."* Tick-level intraday granularity (5-second interval index recalculation) is
  explicitly offered via the "S&P/TSX Historical Indices Tick by Tick" product.
- **Identity coverage:** TMX's own "S&P/TSX Equity Index Products" description explicitly lists
  *"Index Level Values"* as a delivered field across its S&P/TSX index product family, and separately
  names *"S&P/TSX 60 Risk Control Indices"* (built on the underlying S&P/TSX 60). This is strong
  evidence the underlying S&P/TSX Composite, S&P/TSX 60, and (via the broader index-product catalog)
  Venture Composite are all commercially available through TMX in principle — the *exact* package/tier
  boundaries are sign-in-gated and unconfirmed.
- **Category: inconclusive/unresolved** — a real, paid, individually-licensable, token-authenticated
  REST/SFTP API path exists (this reopens the door the prior pass closed), but full BYOK-practicality
  (exact EULA permission for automated per-user software use, and whether the ≈C$164/mo floor is
  acceptable to this project) could not be confirmed because every primary TMX document is sign-in- or
  bot-gated against direct fetch.

---

## 3. Bank of Canada (Valet API) / Statistics Canada

Two distinct government sources, evidenced separately.

### 3a. Bank of Canada Valet API
- **Ownership/operator:** Bank of Canada.
- **URL/endpoint:** `https://www.bankofcanada.ca/valet/docs`; series/groups lists at
  `https://www.bankofcanada.ca/valet/lists/series/json` and `.../lists/groups/json`.
- **Auth requirements:** None — free, public, no API key, stable versioned endpoints since 2017.
- **Dated reachability (2026-07-25):** Both list endpoints returned **HTTP 200** with valid JSON
  (2,524 groups; 15,906 series enumerated directly).
- **Identity coverage:** Programmatically searched the **full** series (15,906) and group (2,524)
  label/description text for "TSX"/"Toronto"/"composite". Zero matches correspond to a real, standard
  S&P/TSX equity index series. The only "TSX"-labeled series found are one-off chart-annotation series
  embedded in specific Monetary Policy Report analytical boxes (e.g. `SAN_LEBM180118_CHART2D_A_TSX`),
  not a general-purpose, continuously-updated S&P/TSX index series. Valet's actual coverage is FX
  rates, interest rates, monetary aggregates, and similar BoC-published indicators — not equity index
  levels (unsurprising: BoC does not administer or license S&P/TSX data).
- **Category: confirmed absent.**

### 3b. Statistics Canada — Table 10-10-0125-01 "Toronto Stock Exchange statistics"
**New finding not identified in the prior pass. REVISED 2026-07-25 (round-3) — a design-gate
reviewer independently replayed this candidate (report `gate-202607251810-issues199-200-design-
round2.md`, R2-B1/R2-B2) and found the round-2 version of this section overstated both the licence
and the currency status. Corrected below with additional first-hand verification.**

- **Ownership/operator:** Statistics Canada (federal statistical agency). **Not Statistics
  Canada's own primary data** — table metadata footnote 1 states verbatim: *"As of January 2017,
  this data is obtained from the Toronto Stock Exchange eReview, TMX Group Inc."* (footnote 3: prior
  to Jan 2017 the source was the Bank of Canada). This is third-party-sourced data republished by
  StatCan, confirmed via `getCubeMetadata` (`productId=10100125`, fetched 2026-07-25).
- **Program/survey record:** StatCan's own program page for survey **5268** (Toronto Stock Exchange
  Statistics), `https://www23.statcan.gc.ca/imdb-bmdi/pub/5268-eng.htm`, is StatCan's authoritative
  program-status record for this series family — I could not directly render its content in this
  pass (returned an empty/JS-shell response to a plain fetch); the design-gate reviewer's report
  cites it directly for the program's inactive/discontinued status. Treat that program-status claim
  as reviewer-sourced, not independently re-confirmed by me at the program-page level — but see the
  cube-metadata footnote below, which I did verify directly and corroborates discontinuation.
- **URL/endpoint:** Table page `https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1010012501`;
  programmatic retrieval via the StatCan Web Data Service (WDS) REST API:
  `https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/10100125/en` → returns
  `{"status":"SUCCESS","object":"https://www150.statcan.gc.ca/n1/tbl/csv/10100125-eng.zip"}`
  (**independently re-verified 2026-07-25, HTTP 200**). Per-series metadata via
  `getCubeMetadata`/`getSeriesInfoFromVector` (POST, JSON body) — **independently re-verified
  2026-07-25**.
- **Auth requirements:** **None** — free, public, no API key, documented REST endpoints.
- **Dated reachability (2026-07-25, independently re-verified):** `getFullTableDownloadCSV` → HTTP
  200; `getCubeMetadata` → HTTP 200, `cubeStartDate=1956-01-01`, `cubeEndDate=2023-09-01`,
  `nbSeriesCube=25`, `nbDatapointsCube=11428`, `releaseTime=2023-11-01T08:30`. **Footnote 4 on the
  cube (verbatim, confirmed):** *"Please note that this table is no longer being updated as of
  November 1, 2023."* This is StatCan's own explicit discontinuation statement — stronger than
  "effectively stale," and independent corroboration of the reviewer's "Inactive" program-status
  finding even though I could not directly re-render the program-status page itself.
- **Historical span/frequency — per-series, not table-wide (R2-B2 correction: the round-2 version
  wrongly generalized the cube's overall 1956–2023-09 span to every series).** Verified directly via
  `getSeriesInfoFromVector` (2026-07-25):

  | Series | Vector | Unit | Confirmed by |
  |---|---|---|---|
  | Composite, close | `v122620` | `Index, 2000=1000` | direct `getSeriesInfoFromVector` call, 2026-07-25 |
  | Composite, high | `v122618` | `Index, 2000=1000` | direct `getSeriesInfoFromVector` call, 2026-07-25 |
  | Composite, low | `v122619` | `Index, 2000=1000` | direct `getSeriesInfoFromVector` call, 2026-07-25 |
  | TSX 60 | `v19457778` | `Index` | reviewer-verified; vector ID independently confirmed present in my own metadata pull |

  Exact per-vector start/end dates were not re-pulled point-by-point in this pass (would require a
  full `getDataFromVectorsAndLatestNPeriods`/CSV date-column parse); the design-gate reviewer's
  report states them from a direct CSV replay: Composite close 1956-01–2023-09, Composite
  high/low 1976-01–2023-09, TSX 60 1982-01–2023-09 — cited here as reviewer-verified, not
  independently re-derived by me at the per-date level. All series share the **2023-09 stale-since
  cutoff** (~2.75 years as of 2026-07-25) confirmed by the cube-level `cubeEndDate` above.
- **Download shape / service limits:** full-table CSV download, no pagination (11,428 rows across
  25 series in one file per the cube metadata above). WDS-documented rate limits (25 req/sec/IP, 50
  server-wide, `409` during maintenance windows) per the reviewer's report — not independently
  re-verified by me (would require load-testing, out of scope for a vetting pass).
- **Identity coverage (verified directly by parsing the CSV's 25 distinct series names + the vector
  table above):**
  - **"Standard and Poor's/Toronto Stock Exchange Composite Index"** (close/high/low variants) —
    **present**, data through 2023-09.
  - **"Standard and Poor's/Toronto Stock Exchange 60 Index"** — **present**, data through 2023-09.
  - **S&P/TSX Venture Composite** — **absent**. No series with "Venture" in its name exists anywhere
    in the 25-series table.
- **Redistribution/licensing posture — CORRECTED (R2-B1, the decisive finding).** Round-2 wrongly
  called this the "Open Government Licence" with unqualified "openly licensed"/"lawful" language.
  The applicable instrument is the **Statistics Canada Open Licence**
  (`https://www.statcan.gc.ca/en/terms-conditions/open-licence`), a distinct instrument from the
  government-wide OGL. Its own FAQ
  (`https://www.statcan.gc.ca/en/terms-conditions/open-licence-faq`, fetched directly 2026-07-25)
  states verbatim: *"information for which third parties own intellectual property rights is
  excluded from the Statistics Canada Open Licence. For such materials, you will need to contact
  the owner to obtain guidelines on use of their information."* Given this table's own footnote 1
  names TMX Group Inc. (and, pre-2017, the Bank of Canada) as the data's actual source, and nothing
  in the committed record establishes that StatCan's agreement with TMX/S&P grants StatCan (and
  thus StatCan's licensees) the right to sub-license/redistribute the underlying index values, the
  correct classification is: **reuse rights for the TMX/S&P-sourced index values are unresolved**,
  not "openly licensed." Runtime-only retrieval by an end user reduces redistribution exposure
  somewhat but does not cure an unresolved third-party rights question for a library that would
  routinely re-serve the values to its own callers.
- **Category: technical identity/API confirmed; reuse rights inconclusive (not one of the 4
  standard labels, and not "confirmed present" as round-2 wrongly called it).** Composite + TSX 60:
  real, keyless, technically-reachable, monthly, **stale since 2023-09**, but **licence-unresolved**
  for the third-party index values. Venture Composite: **confirmed absent** (no series exists,
  independent of the licence question).

---

## 4. Alpha Vantage — corrected evidence (reviewer blocker #1)

- **Ownership/operator:** Alpha Vantage Inc.
- **Endpoint re-verified (correct one, per reviewer instruction):**
  `https://www.alphavantage.co/query?function=INDEX_CATALOG&apikey=demo&datatype=csv`
- **Dated reachability (2026-07-25):** **HTTP 200.** Downloaded and parsed directly: **317 data rows**
  (318 lines incl. header), header `symbol,name`. `grep -icE "TSX|GSPTSE|Toronto|Canada"` on the raw
  CSV → **0 matches**. This independently reproduces Boss's own probe result exactly.
- **Auth/tier semantics (from `alphavantage.co/documentation/#major-indices`, fetched directly):**
  `INDEX_CATALOG` is listed as a free **"🔧 Utility"** discovery endpoint (consistent with it working on
  the public `apikey=demo` test key without an error). The *actual OHLCV time-series* major-indices
  endpoints (DJI, SPX, NASDAQ Composite, NDX, VIX, Russell 2000) are separately documented and marked
  **"💡 Premium"**, and the documentation's own intro states the suite covers *"200+ major indices"* —
  but the only ones itemized on the documentation page are US indices; no Canadian/TSX index is named
  anywhere on the page.
- **Historical span/frequency:** Documented as daily/weekly/monthly for the (Premium, US-only-named)
  major-indices suite; `INDEX_CATALOG` itself is a symbol/name catalog only, not a time series.
- **Category: confirmed absent** — both via direct catalog enumeration (317 rows, 0 Canada/TSX matches)
  and via the documentation's own explicit index list (US-only enumerated indices).

---

## 5. Stooq

- **Ownership/operator:** Stooq (Poland-based free market-data aggregator); already used as a fallback
  in this project's existing `indices.world()` for `^SPX`.
- **URLs probed directly (2026-07-25):**
  - `https://stooq.com/q/d/l/?s=<sym>&i=d` for `^tsx, tsx, ^spx, ^gsptse, gsptse, ^tsx60, tsx60, ^tsxv,
    tsxv, ^tsxventure` — **every single one**, including the known-working `^spx` control, returned
    **HTTP 200 but a JavaScript proof-of-work bot-challenge page** ("This site requires JavaScript to
    verify your browser"), not CSV data. This is a site-wide anti-bot gate active today, not a
    symbol-specific rejection (confirmed because `^spx`, which this project's own code already
    consumes successfully via Stooq, hit the identical challenge page under this agent's fetch
    conditions).
  - `WebFetch` on both the quote page (`https://stooq.com/q/?s=%5Etsx`) and the CSV endpoint returned
    empty content (consistent with a JS-only interstitial page).
- **Identity coverage — S&P/TSX Composite:** Google's own indexed page titles for
  `https://stooq.com/q/?s=%5Etsx` read *"^TSX (0.00%) - S&P/TSX Composite Index - Canada - Stooq"* (and
  a second variant with a live % change), a strong circumstantial signal that Stooq lists `^TSX` =
  S&P/TSX Composite, Canada. This is **third-party search-cache evidence only** — this agent could not
  independently open the page or confirm live data/history depth/terms today.
- **Identity coverage — S&P/TSX 60 and Venture Composite:** No reliable cached page/title evidence
  found for either. A search-engine AI summary speculatively suggested symbols like `^TX60`/`^JX`, but
  this is an **unverified inference by the search tool, not primary evidence** — it is explicitly
  flagged here as unconfirmed, not adopted as a finding.
- **Terms of use / robots posture:** Not independently confirmed this round (site unreachable past the
  bot-challenge for a full pass).
- **Category:** S&P/TSX Composite = **inconclusive/unresolved** (identity plausible via cached title,
  but live reachability/verification blocked); S&P/TSX 60 and Venture Composite = **inconclusive/
  unresolved** (no reliable identity signal found at all — this is the honest floor, not "confirmed
  absent," since the site itself could not be searched directly). Also record: **temporarily
  unreachable** as the proximate, dated (2026-07-25) cause of the unresolved status.

---

## 6. Twelve Data — exact permutations tested (reviewer instruction #5)

- **Endpoint:** `https://api.twelvedata.com/symbol_search?symbol=<X>` (public search endpoint, no key
  required to query).
- **Exact permutations tested and exact results (2026-07-25, all HTTP 200):**

| Symbol string queried | Exact result |
|---|---|
| `GSPTSE` | `{"data":[],"status":"ok"}` — zero matches |
| `TSX` | 8 matches, **all ETFs/mutual funds** (Direxion `TSXD`/`TSXU`, several BMO "Growth Principal Protected Deposit Notes… Linked to TSX60 DSC/NL" — index-*linked* structured notes, not the index itself) |
| `%5EGSPTSE` (URL-encoded `^GSPTSE`) | `{"data":[],"status":"ok"}` — zero matches |
| `TSX60` | 6 matches, all the same BMO structured-note products referencing "TSX60" in their name — no direct index instrument |
| `TSXV` | `{"data":[],"status":"ok"}` — zero matches |
| `S%26P%2FTSX` (URL-encoded `S&P/TSX`) | 24+ matches, **all ETFs** (`XIC` iShares Core S&P/TSX Capped Composite Index ETF, `ZCN` BMO S&P/TSX Capped Composite Index ETF, `XSPC`, `HXF`, sector-capped ETFs, leveraged BetaPro ETFs, etc.) — zero results with `instrument_type` other than ETF/Mutual Fund |

- **Category: inconclusive/unresolved — downgraded from round-2's "confirmed absent" (R2-B3.1).**
  Six relevance-ranked `symbol_search` queries returning no native index instrument (only ETFs/
  structured notes) shows the search endpoint doesn't surface one under those specific query
  strings — it does not enumerate Twelve Data's complete index catalog, so it cannot support a
  "confirmed absent" claim the way the Alpha Vantage `INDEX_CATALOG` full-catalog pull does. Every
  probed permutation is, however, consistent with absence and with the proxy-only pattern the task
  excludes; a definitive answer would require Twelve Data's own complete index-catalog endpoint
  (not found/tested in this pass).

---

## 7. Financial Modeling Prep (FMP) — bounded per reviewer instruction #4

- **Endpoints tested directly:**
  - `https://financialmodelingprep.com/api/v3/quotes/index?apikey=demo` → **HTTP 401**,
    `{"Error Message":"Invalid API KEY..."}`
  - `https://financialmodelingprep.com/api/v3/symbol/available-indexes?apikey=demo` → **HTTP 401**, same error
  - `https://financialmodelingprep.com/stable/index-list?apikey=demo` → **HTTP 401**, same error
  - Docs page `https://site.financialmodelingprep.com/developer/docs/stable/indexes-list` → **HTTP 403**
    on direct fetch.
- **What blocked a definitive answer:** FMP's `demo` key (unlike Alpha Vantage's, which is a genuinely
  functional public test key for several endpoints) is **rejected outright (401)** on every index
  endpoint tried, and the public documentation page 403'd this agent's direct fetch. A search-engine AI
  summary claimed FMP's index list "includes TSX," but this claim could not be traced to any directly
  quotable, verified primary-source text — it reads as an unreliable inference from search snippets, not
  a fact this pass can stand behind.
- **Category: inconclusive/unresolved** — explicitly bounded: blocked by demo-key rejection (401) +
  docs-page 403; would require a real registered (even free-tier) FMP API key to test definitively.

---

## 8. Marketstack — bounded per reviewer instruction #4

- **Endpoints tested directly:**
  - `https://api.marketstack.com/v1/tickers?access_key=demo&search=GSPTSE` → **HTTP 401**,
    `{"error":{"code":"invalid_access_key",...}}`
  - `https://api.marketstack.com/v1/tickers?access_key=demo&search=TSX` → **HTTP 401**, same error
  - Docs (`marketstack.com/documentation` → redirects to `docs.apilayer.com/marketstack/docs/api-endpoints-v1`)
    → fetched successfully but returned **only a login-gated documentation shell** (page header/logo,
    no substantive endpoint/coverage content visible without an apilayer account).
- **What blocked a definitive answer:** `demo` is not a valid Marketstack access key (401 on every
  call), and the public docs mirror requires an apilayer.com login to show real content. No independent
  confirmation of index coverage (or its absence) was possible.
- **Category: inconclusive/unresolved** — explicitly bounded: blocked by invalid demo key (401) +
  login-gated docs mirror.

---

## Executive verdict

**Source-blocked overall for a live, daily, free/self-serve, lawful native-index-point API covering
all three headline S&P/TSX indices** — but this pass surfaces one genuine **partial** win the prior
pass missed, and meaningfully softens (without reversing) the TMX conclusion:

1. **No candidate in this pass provides all 3 target indices, daily, free, and self-serve.**
2. **Statistics Canada (Table 10-10-0125-01, free WDS API, no key) is technically reachable and
   directly verified to carry S&P/TSX Composite and S&P/TSX 60 as native index points** — but
   monthly, stale since 2023-09 (no update in ~2.75 years as of 2026-07-25), AND with **unresolved
   third-party reuse rights** (round-3 correction, R2-B1: the table's own footnotes name TMX Group/
   Bank of Canada as the actual data source, and the Statistics Canada Open Licence FAQ excludes
   third-party-owned IP — this is not "openly licensed," it is licence-unresolved). It does **not**
   carry Venture Composite at all regardless of the licence question.
3. **TMX Datalinx is the only entity with a documented, automatable, token-authenticated REST+SFTP API
   for all 3 indices at daily/tick granularity** — the prior pass's "legally impossible" conclusion is
   corrected to **"paid and EULA-unverified but architecturally plausible."** A real self-serve
   per-user account+purchase path exists (≈C$163.53/month minimum for Custom Queries), and the
   redistribution clause on its own does not forbid a BYOK architecture (each user under their own
   license, matching this project's existing Alpha Vantage pattern) — but the actual EULA text
   governing whether an individual's own automated script is a permitted use is sign-in-gated and could
   not be read this round. **Category: inconclusive/unresolved**, not "not exposed through a lawful
   API."
4. **S&P DJI direct and Alpha Vantage are cleanly resolved as not usable**: S&P DJI =
   institutional-subscriber-only as evidenced (bounded by 403s); Alpha Vantage = **confirmed absent**
   via direct, reproducible full-catalog endpoint evidence.
4b. **Twelve Data is downgraded to inconclusive/unresolved (round-3 correction, R2-B3.1)** — 6
   relevance-ranked `symbol_search` queries found no native instrument, but that does not enumerate
   Twelve Data's complete index catalog, so "confirmed absent" overstated the evidence.
5. **Stooq, FMP, and Marketstack remain genuinely unresolved**, each for a different, explicitly
   evidenced reason (Stooq: site-wide bot-challenge blocking direct verification despite a plausible
   cached-title identity signal for Composite only; FMP/Marketstack: demo-key rejection + gated docs).

**Recommendation for vnfin (round-3 correction):** do not build a native-index-point adapter for
these 3 indices from any source today — not because no technical/keyless path exists (StatCan's
does), but because StatCan's reuse rights for the third-party TMX/S&P index values are unresolved,
not license-clean as round-2 wrongly stated. A future build requires one of: (a) written
confirmation from Statistics Canada that Table 10-10-0125-01's TMX/S&P-sourced series are covered
for reuse/redistribution under the Open Licence, or an equivalent grant from TMX/S&P directly; (b) a
TMX Datalinx paid BYOK integration once the sign-in-gated EULA is read and confirms per-user
automated-retrieval is permitted use.

## What changed from the prior pass

1. **Alpha Vantage evidence corrected and independently re-verified.** Prior pass used the wrong
   endpoint (`LISTING_STATUS`, a US stocks/ETF catalog). This pass used `INDEX_CATALOG` (the correct
   discovery endpoint) directly via `curl`, reproducing Boss's own 317-row/0-match probe, and separately
   fetched AV's own documentation to characterize `INDEX_CATALOG` as a free "Utility" tier distinct from
   the Premium OHLCV major-indices endpoints (which explicitly enumerate only ~6 US indices).
2. **TMX legal framing corrected — the main fix.** The prior pass over-relied on the "single end user,
   no redistribution rights" pricing clause to declare an OSS BYOK adapter legally impossible. This pass
   separated the five distinct questions the reviewer specified and found: (a) code distribution not in
   question; (b) a real self-serve individual account + Pay-Per-Use product **does** exist; (c) the
   redistribution clause targets reselling data to third parties, not per-user automated retrieval;
   (d) **contrary to the pre-registered hypothesis, a documented, automatable REST API + SFTP with
   token auth does exist** — "no automatable API" is NOT the real blocker, evidence does not support it;
   (e) the real, evidenced friction is a **recurring cost floor (≈C$163.53/mo)** plus a
   **sign-in-gated, unread EULA** whose exact permitted-use language could not be confirmed. TMX is
   downgraded from "legally blocked" to "inconclusive/unresolved."
3. **New finding: Statistics Canada Table 10-10-0125-01**, not identified in the round-1 pass — a
   free, keyless, technically-reachable source for S&P/TSX Composite + S&P/TSX 60 (monthly,
   stale since 2023-09, no Venture Composite). **Round-3 correction (this section):** its licence
   status was overstated in round-2 as "Open Government Licence"/"openly licensed"/"lawful." A
   design-gate reviewer replay (`gate-202607251810-issues199-200-design-round2.md`) plus my own
   direct fetch of the Statistics Canada Open Licence FAQ and the table's own third-party-source
   footnotes established this is the distinct **Statistics Canada Open Licence**, which explicitly
   excludes third-party-owned IP — and the table's own footnotes name TMX Group (post-2017) / Bank
   of Canada (pre-2017) as the actual data source. Reuse rights for the index values are therefore
   **unresolved**, not license-clean. Per-vector coverage was also corrected from a single
   cube-wide 1956–2023-09 span to the reviewer-verified per-series spans (Composite close 1956-01–
   2023-09; Composite high/low 1976-01–2023-09; TSX 60 1982-01–2023-09), and the table's status is
   recorded as no-longer-updated-since-2023-11-01 per its own footnote 4 (independently
   re-verified), not merely "effectively stale."
4. **Stooq, Twelve Data, FMP, and Marketstack vetted with exact, reproducible evidence** per the
   reviewer's instructions (exact Twelve Data permutation table; Stooq bot-challenge documented with a
   working-control comparison against `^SPX`; FMP/Marketstack explicitly bounded as unresolved rather
   than silently treated as absent). **Round-3 correction:** Twelve Data's verdict was itself
   downgraded from "confirmed absent" to "inconclusive/unresolved" (R2-B3.1) — 6 relevance-ranked
   queries don't enumerate a full catalog.
5. **Bank of Canada Valet confirmed absent via a full programmatic sweep** of all 15,906 series and
   2,524 groups (not a spot-check), finding only incidental chart-annotation series, not a real S&P/TSX
   index series.

## Reopen criteria

Per the project's actual requirement — "a clearly licensed provider API whose terms permit end-user
runtime retrieval" (not a keyless/self-service-specific bar) — this candidate list reopens if any of the
following becomes true:

1. **TMX Datalinx:** the actual product-specific Market Data Services Agreement / EULA text (currently
   sign-in-gated) is obtained and confirms it permits an individual subscriber's own automated
   script/software to retrieve data under their own account/token for their own analytical use (i.e.
   does not require a separate "distributor" designation for that use case). If confirmed, a paid BYOK
   adapter (each user brings their own Datalinx account + API token, mirroring the existing Alpha
   Vantage pattern) becomes buildable — cost (≈C$164/mo floor) would then be a project/Boss cost-benefit
   decision, not a legal blocker.
2. **S&P DJI direct:** a documented individually-licensable (even paid) self-serve API signup path is
   found beyond the institutional-subscriber-oriented brochure currently on file.
3. **Statistics Canada (round-3 correction — NOT already usable today, licence-unresolved):**
   reopens once Statistics Canada confirms in writing that Table 10-10-0125-01's TMX/S&P-sourced
   Composite and TSX 60 series are covered for reuse/redistribution under the Statistics Canada
   Open Licence (or TMX/S&P supplies an equivalent grant directly). Even once reuse rights are
   confirmed, this stays an explicitly historical/archival series (frozen 2023-09, monthly) unless a
   successor/updated table is later found — it must never be presented as a current quote. A
   distinct lawful source would still be needed for Venture Composite regardless of the licence
   outcome for Composite/TSX 60.
4. **Stooq:** reopens once direct reachability succeeds past today's bot-challenge and the exact symbol
   set (especially S&P/TSX 60 and Venture Composite, currently unconfirmed) and stated terms of use are
   read directly rather than inferred from cached search-index titles.
5. **FMP / Marketstack:** reopen once tested against their documented index-catalog endpoints using a
   real (registered, even free-tier) API key rather than the non-functional `demo` key used in this
   pass.

---

*Research conducted 2026-07-25. All dated reachability results, endpoint responses, and permutation
tables above were produced by direct `curl`/`WebFetch` calls made during this session and are
reproducible from the exact URLs/parameters recorded.*
