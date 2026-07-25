# Bangladesh DSE Index Source Vetting (DSEX / DS30 / DSES) — Redo Pass

**Date:** 2026-07-25
**Purpose:** Find a lawful, technically adequate source for the three headline Dhaka Stock Exchange
(DSE) indices as **native index points** (not USD, not ETF proxy, not BDT/share-price data):

- `DSEX` — DSE Broad Index
- `DS30` — DSE 30 blue-chip index
- `DSES` — DSE Shariah index

This is a redo of an earlier pass that a design-gate reviewer **BLOCKED** for evidence-quality issues
(wrong Alpha Vantage endpoint, vague ToS claims, unresolved candidates left ambiguous). Every
correction the reviewer required is addressed below with fresh, dated, first-hand evidence gathered
2026-07-25.

## Clean-room statement

This research excluded VNStock/vnstock in every search and fetch: no query, URL, repo, snippet, or
schema derived from VNStock or VNStock-adjacent material (`thinh-vu/vnstock`, `vnstocks.com`,
`vnstock-hq`, `vnstock-agent`) was searched, opened, cited, or used. All findings below come from
official provider sites, official API/documentation pages, or general web search filtered to exclude
those terms.

## Category labels used below

Each candidate is tagged with exactly one of these four labels (per the task's Point 5):

- **Confirmed absent** — positively verified via an authoritative catalog/list that the identity does
  not exist in that provider's coverage.
- **Not exposed through a lawful API** — the data may exist on the provider's site/product, but there is
  no API/redistribution-permitted path to it (ToS/copyright forbids automated/redistribution use, or no
  API surface exists at all).
- **Inconclusive/unresolved** — could not get a definitive answer with the tools/keys available in this
  sandbox (e.g., blocked by anti-bot challenge, requires a paid key we don't have, or docs did not
  state coverage either way).
- **Temporarily unreachable** — network/sandbox connectivity issue prevented reaching the resource at
  all (distinct from a real 403/ToS block).

---

## 1. DSE official (dsebd.org / dse.com.bd)

- **Ownership/operator:** Dhaka Stock Exchange PLC, the official demutualized exchange operator of
  Bangladesh (registered office: Stock Exchange Building, 9/F Motijheel C/A, Dhaka).
- **URL/endpoint:** `https://www.dsebd.org/dseX_share.php` (DSEX page), `dse30_share.php` (DS30),
  presumably a Shariah-index page for DSES, plus `https://www.dsebd.org/data_archive.php` (historical
  archive UI, HTML/CSV download links, not a documented REST API).
- **Auth:** none required for the public web pages/downloads.
- **Historical span/frequency:** the site exposes a "Data Archives" section with day-level historical
  downloads; exact span not fully enumerated in this pass (out of scope beyond reachability + licensing).
- **Pagination/rate limits:** none documented; this is an HTML site with CSV/PDF download links, not a
  rate-limited JSON API.
- **robots.txt:** `https://www.dsebd.org/robots.txt` returned **HTTP 404** (no robots.txt file present)
  on 2026-07-25 — i.e., no machine-readable crawl policy exists; that does **not** imply permission,
  because copyright/ToS govern usage separately (see below).
- **ToS/copyright/licensing — exact dated evidence (2026-07-25):**
  - `https://www.dsebd.org/copyright.htm` (fetched 2026-07-25): *"This website and its contents are
    copyright of Dhaka Stock Exchange PLC. — © 2011 Dhaka Stock Exchange PLC. All rights reserved. Any
    redistribution, telecast, broadcast or reproduction of part or all of the contents in any form is
    prohibited other than the following: You may only print or download to a local hard disk, extracts
    for your personal and non-commercial use only but may not copy and reproduce the source code of the
    website or any of its contents anywhere. ... You may not, except with our prior written permission,
    distribute, telecast, broadcast or commercially exploit the content in another website ... Nor may
    you transmit it or store it in any other website or other form of electronic retrieval system."*
  - `https://www.dsebd.org/termsacond.htm` (fetched 2026-07-25): *"This website contains material which
    is owned by or licensed or copyright to us. This material includes, but is not limited to, the
    design, layout, look, appearance, graphs, trade data, live ticker and graphics. Reproduction is
    prohibited other than in accordance with the copyright notice ... Unauthorised use of this website
    (including copying the source code or any other material and telecasting/broadcasting them without
    prior written permission) may give rise to a claim for damages and/or be a criminal offence."*
  - Net effect: the official copyright/terms text explicitly forbids redistribution, non-personal use,
    and "storing in any other electronic retrieval system" — this squarely blocks an OSS library from
    ingesting and re-serving DSE trade/index data without a prior written license from DSE, regardless
    of technical scrape feasibility.
  - There is an "API for BHOMS" link on the Data Archives page footer, but this is a brokerage
    back-office trading system API brochure (`assets/pdf/BHOMS_Brochure_v1.1.pdf`), unrelated to public
    index-data distribution.
- **Dated reachability/datacenter result (2026-07-25):** Plain `curl` **failed** with `SSL certificate
  problem: unable to get local issuer certificate` (curl exit 60) — this is a **local CA trust-store
  gap in this sandbox**, not a real server-side block. Retrying with `-k` (skip cert verification)
  succeeded: `www.dsebd.org` → **HTTP 200**, real HTML content (`<title>Dhaka Stock Exchange</title>`,
  page size ~400 KB). `dseX_share.php` and `data_archive.php` also returned **HTTP 200** with real
  content, and both pages contain literal `DSEX`, `DS30`, `DSES` strings. **This corrects the prior
  pass's finding of a 403** — today's fresh check shows the site is reachable (once the local TLS trust
  issue is bypassed); the earlier "403" appears to have been a different sandbox-network condition, not
  a durable exchange-side block.
- **Identity coverage:** DSEX, DS30, and DSES pages all exist on the official site
  (`dseX_share.php`, `dse30_share.php`, and DSES has an equivalent page per site navigation/search
  results, e.g. `DSES_share.php`-pattern — not independently re-fetched in this pass, treat as
  **unknown/unverified** for DSES specifically pending a direct fetch).
- **Category:** **Not exposed through a lawful API** — the identities exist on the official site, but
  there is no documented API, and the site's own copyright/terms explicitly prohibit redistribution and
  storage in any external retrieval system, which is exactly what an OSS data library would need to do.

---

## 2. TradingView

- **Ownership/operator:** TradingView, Inc.
- **URL/endpoint:** `https://www.tradingview.com/symbols/DSEBD-DSEX/` (and equivalent `DSEBD-DS30`,
  presumably `DSEBD-DSES`) — chart/quote pages only; no public documented REST API for historical index
  series (TradingView's public product is charting UI + paid data feeds/broker integrations, not an
  open data API).
- **Auth:** N/A for the public chart page; any programmatic access would require TradingView's
  commercial/broker data-feed agreements, not a public API key.
- **Historical span/frequency:** shown interactively on the chart page; not independently verified via
  API in this pass (no API exists to query).
- **Pagination/rate limits:** N/A (no public API).
- **robots.txt/ToS — exact dated evidence (fetched 2026-07-25):**
  `https://www.tradingview.com/policies/` (Terms of Use / Company Policy index) — Section 3 language
  (as returned by direct fetch of the policies page on 2026-07-25) explicitly enumerates prohibited
  **"non-display usage"**, including: *"automated trading, automated order generation, price
  referencing, order verification, algorithmic decision-making, algorithmic trading, smart order
  routing, using data in operations control or risk management programs"* and *"creating products or
  services based on TradingView content, any processing of TradingView's content."* The same page states
  TradingView forbids third parties from building tools enabling such prohibited uses "even indirectly
  through webhooks or other features," and states: *"We do not permit commercial usage of any of our
  services or APIs."* This is a direct, dated fetch of TradingView's own policy page, not a paraphrase
  from a third-party blog.
- **Dated reachability (2026-07-25):** `https://www.tradingview.com/policies/` fetched successfully
  (200, content returned). The narrower `https://www.tradingview.com/policies/terms-of-service/` URL
  returned **HTTP 403 Forbidden** to the fetch tool (bot-protection), so the top-level `/policies/` page
  was used instead — same legal document set, reached successfully.
- **Identity coverage:** DSEX and DS30 confirmed listed as tradeable symbols on TradingView
  (`DSEBD-DSEX`, `DSEBD-DS30` search-result URLs, 2026-07-25); DSES not independently confirmed present
  or absent on TradingView in this pass — **unknown**.
- **Category:** **Not exposed through a lawful API** — the symbols exist as chart products, but
  TradingView's own Terms explicitly forbid building "products or services based on TradingView
  content" and disallow commercial use of "any of our services or APIs" — directly disqualifying use in
  an OSS redistributable library.

---

## 3. Investing.com (Fusion Media Limited)

- **Ownership/operator:** Fusion Media Limited and affiliates.
- **URL/endpoint:** `https://www.investing.com/indices/dhaka-stock-exchange-broad` (DSEX quote page),
  `https://www.investing.com/indices/dhaka-stock-exchange-broad-historical-data` (historical data page)
  — web pages only, no documented public REST API.
- **Auth:** N/A (no public API).
- **ToS/licensing — attempted direct dated fetch (2026-07-25):** I attempted to fetch both
  `https://www.investing.com/about-us/terms-and-conditions` and the PDF version at
  `https://cdn.investing.com/about-us/terms_and_conditions.pdf` directly (via WebFetch and via `curl`
  with a browser user-agent, with retries). **All direct-fetch attempts failed**: the HTML page returned
  `ECONNRESET` (WebFetch) and `curl` returned `HTTP_CODE:000` / exit 35 (SSL/connection failure) for
  both the HTML and PDF URLs — this looks like active connection-level blocking of this sandbox's
  egress toward investing.com/its CDN, not a normal 403. **I could not independently read the primary
  ToS document in this pass and am flagging that explicitly rather than asserting its contents from
  memory or a third party.**
  - As a secondary, clearly-labeled fallback, a web search surfaced quoted language attributed to
    Investing.com's Terms and Conditions (via search-engine snippet, not a first-hand fetch by me):
    prohibition on *"copying, storing, selling, licensing, distributing, reproducing, transmitting or
    duplicating Market Information to any third party without obtaining prior written consent ...
    from Fusion Media and/or applicable Third Party Providers"*, a ban on *"deep-linking"* or
    redistributing Market Information, and *"It is prohibited to use, store, reproduce, display,
    modify, transmit or distribute the data contained in this website without the explicit prior
    written permission of Fusion Media and/or the data provider."* This is **second-hand evidence**
    (search snippet, not a page I opened myself) and should be treated with that caveat — it is
    consistent with the general shape of financial-data-site ToS but has not been independently
    verified by direct fetch in this pass.
- **Dated reachability (2026-07-25):** Both the main site and CDN were **unreachable from this sandbox**
  at time of testing (connection reset / timeout on every attempt, both WebFetch and raw `curl`).
- **Identity coverage:** DSEX confirmed present as a quote/historical-data page (URL slug
  `dhaka-stock-exchange-broad`); DS30/DSES presence on Investing.com not independently confirmed in this
  pass — **unknown**.
- **Category:** **Temporarily unreachable** for direct ToS verification (network/sandbox egress issue,
  distinct from a confirmed block) — combined with **Not exposed through a lawful API** on structural
  grounds (no public API exists regardless of ToS wording, and the second-hand ToS evidence points the
  same direction as TradingView/DSE: redistribution requires prior written consent).

---

## 4. Alpha Vantage — CORRECTED

**This is the primary correction required by the reviewer.** The prior pass used `LISTING_STATUS`, a
US-market stock/ETF ticker catalog, and wrongly treated Bangladesh-index absence there as proof of
absence — that endpoint cannot speak to index coverage at all. The correct endpoint is `INDEX_CATALOG`.

- **Ownership/operator:** Alpha Vantage Inc.
- **Exact endpoint used:** `https://www.alphavantage.co/query?function=INDEX_CATALOG&apikey=demo&datatype=csv`
- **What this endpoint actually is (per Alpha Vantage's own documentation, `Major Indices`/`Index
  Catalog` doc anchors under `https://www.alphavantage.co/documentation/`):** Alpha Vantage's index
  suite ("Major Indices" data category) covers a curated set of major global market indices via
  dedicated endpoints (e.g., time-series index endpoints), and `INDEX_CATALOG` is the discovery/listing
  endpoint returning the full set of index `symbol,name` pairs Alpha Vantage supports — analogous in
  role to `LISTING_STATUS` but scoped to **indices**, not equities/ETFs. It works with the free `demo`
  key at the CSV-listing level (the underlying time-series index endpoints are gated to paid tiers per
  AV's standard tiering; this pass only needed the catalog/listing call, which the `demo` key served).
- **Verification (fresh, 2026-07-25):** `curl` to the exact URL above returned **HTTP 200**, CSV with
  header `symbol,name`, **317 data rows** (318 lines including header). `grep -iE
  "DSEX|DS30|DSES|Dhaka|Bangladesh"` against the full response returned **zero matches**. First two
  rows: `DJI,Dow Jones Industrial Average`; `SPX,S&P 500 INDEX` — confirming this is genuinely the
  global major-index catalog (not a truncated/wrong response), and its coverage is limited to major
  developed/large-market benchmarks (Dow, S&P, Nasdaq-type series and similar), not exchange-specific
  frontier/emerging-market broad indices like DSEX/DS30/DSES.
- **Auth:** free `demo` API key sufficient for this catalog-listing call; production keys are tiered
  (free vs. premium) for the actual index time-series pulls, per AV's standard API-key model.
- **Historical span/frequency:** N/A for the catalog call itself (it's a symbol directory, not a time
  series); time-series frequency for indices Alpha Vantage *does* carry is daily per AV's documented
  index endpoints.
- **Pagination/rate limits:** none needed for this single CSV catalog pull; AV's standard free-tier rate
  limits (documented as low request-per-minute/day caps) apply to the broader API.
- **robots.txt:** `https://www.alphavantage.co/robots.txt` returned a **404 "Not Found"** HTML page
  (2026-07-25) — no robots.txt file present at that path.
- **Identity coverage:** **DSEX, DS30, DSES all absent** from the 317-row `INDEX_CATALOG` response,
  case-insensitively, on 2026-07-25. Because this is the correct discovery endpoint for AV's supported
  index universe (not a US-equity catalog), this is a legitimate absence signal.
- **Category:** **Confirmed absent** — the authoritative index catalog for this provider does not list
  any of the three target identities.

---

## 5. Stooq

The project's existing `indices.world()` already uses Stooq as a fallback for other symbols (e.g. the
SPY/QQQ chain via Stooq `^SPX`), so this candidate matters for architectural consistency.

- **Ownership/operator:** Stooq.com (Poland-based financial data/quotes site).
- **Exact endpoint/request shape attempted:** documented CSV download pattern
  `https://stooq.com/q/d/l/?s=<symbol>&i=d` (daily interval), tried with `s=dsex`, `s=ds30`, `s=dses`.
- **Dated result (2026-07-25):** all three requests returned **HTTP 200**, but the response body was
  **not CSV data** — it was an HTML page containing a client-side JavaScript proof-of-work challenge
  (`crypto.subtle.digest("SHA-256", ...)` loop posting to `/__verify`) with `<meta name="robots"
  content="noindex,nofollow">`. This is a bot-verification wall that a plain HTTP client (no JS engine)
  cannot pass — so **no symbol-level answer (exists/doesn't-exist) could be obtained** for any of the
  three tickers in this sandbox.
- **robots.txt (fetched 2026-07-25):** `https://stooq.com/robots.txt` explicitly disallows generic
  crawlers: `User-agent: * / Disallow: /`, with narrow allowances only for `Bingbot` and `Googlebot`.
  This is a clear, dated, first-party signal that Stooq does not permit general automated/bot access to
  its site (a plain `curl`/library client falls under the disallowed `User-agent: *` bucket) — separate
  from and in addition to the JS proof-of-work wall observed on the actual download endpoint.
- **Auth:** none documented for the public CSV download endpoint (when reachable), but the JS challenge
  effectively gates all non-browser access regardless of auth.
- **Identity coverage:** **could not be determined** — the JS-challenge wall blocked verification of
  whether `dsex`/`ds30`/`dses` map to real Stooq symbols at all.
- **Category:** **Inconclusive/unresolved** — technically blocked by an anti-bot JS challenge in this
  sandbox, and separately disallowed for generic crawlers by `robots.txt`. Even if a browser-automation
  workaround could pass the JS challenge, the `robots.txt: Disallow: /` for `User-agent: *` is a
  first-party signal against building a redistributable automated-access data pipeline on top of it.
  This also means the project's existing `indices.world()` Stooq fallback pattern should not be assumed
  automatically extensible to DSE identities without separately re-confirming Stooq's posture for those
  specific symbols (which this pass could not do).

---

## 6. Financial Modeling Prep (FMP)

- **Ownership/operator:** Financial Modeling Prep, LLC.
- **Exact endpoint(s) checked:**
  - Docs page: `https://site.financialmodelingprep.com/developer/docs/stable/indexes-list` (Stock
    Market Indexes List API doc).
  - Legacy docs page: `https://site.financialmodelingprep.com/developer/docs/available-indexes`.
  - Live API calls attempted: `https://financialmodelingprep.com/stable/index-list?apikey=demo` and
    `https://financialmodelingprep.com/api/v4/index-list?apikey=demo`.
- **Auth:** API-key required for all data endpoints (header `apikey:` or `?apikey=` query param per
  FMP's own quick-start text, captured verbatim from the docs page: *"All API requests must be
  authorized using an API key... apikey=YOUR_API_KEY"*). **The `demo` key is not accepted** — both live
  calls above returned: `{"Error Message":"Invalid API KEY. Feel free to create a Free API Key or visit
  https://site.financialmodelingprep.com/faqs?search=why-is-my-api-key-invalid for more
  information."}` (2026-07-25). FMP has no working demo/sample key equivalent to Alpha Vantage's
  `demo` — a real (free-tier signup) key is required even to list indices.
  - **What blocked full resolution:** no free API key was available/registered in this sandbox for FMP;
    obtaining one would require account signup, which is out of scope for this pass. This is the
    explicit "what blocked me" the task requires rather than a silent absence claim.
- **Docs-page content (fetched successfully on second attempt with a browser user-agent, 2026-07-25;
  first attempt via the WebFetch tool returned a 403, likely generic bot-protection on that specific
  fetch path — a direct `curl` with `-A "Mozilla/5.0 ..."` succeeded with HTTP 200, ~94 KB page):** the
  page is a Next.js app; searching its full rendered HTML/JSON payload for `Bangladesh`, `Dhaka`,
  `DSEX`, `DS30`, `DSES` returned **zero matches**. The page's static template text confirms the
  endpoint's shape: base URL `https://financialmodelingprep.com/stable/`, module category `Indexes`,
  the standard FMP plan-restriction UI (`restriction_exchange: "Exchanges limited to {{value}}"`)
  indicating exchange coverage is plan-gated on lower tiers, and a note that this specific endpoint
  returns responses as **CSV** for at least one variant. No live example symbol list was embedded in the
  static page (the interactive "try it" example is fetched client-side against a real key), so the
  absence-of-mention finding is a docs-text-only signal, not a full catalog audit.
- **Historical span/frequency/pagination/rate limits:** not independently determined for index-specific
  data without a working key; FMP's general free-tier plan is documented elsewhere as request-capped
  (429 on excess) per the quick-start error-code table captured on the docs page (`429: Too many
  requests (rate limit exceeded)`).
- **Identity coverage:** **unresolved** — the docs page text does not mention Bangladesh/DSEX/DS30/DSES,
  which is a weak negative signal (docs pages for "list" endpoints don't always enumerate their full
  catalogs in prose), but the actual `index-list`/`available-indexes` API call could not be executed
  successfully because the `demo` key is rejected and no paid/free-registered key was available.
- **Category:** **Inconclusive/unresolved** — explicitly bounded: blocked by (a) no working demo key
  (FMP requires real signup, unlike Alpha Vantage), and (b) the docs page not embedding a full symbol
  catalog in static HTML. A future pass with a real free-tier FMP key could resolve this definitively by
  calling `GET https://financialmodelingprep.com/stable/index-list?apikey=<real_key>` and grepping the
  JSON response.

---

## 7. Marketstack (APILayer)

- **Ownership/operator:** APILayer (Marketstack brand).
- **Exact endpoint(s) checked:** `GET /indexlist` and `GET /indexinfo` per Marketstack's documented
  index endpoints; docs pages: `https://marketstack.com/documentation_v2` (redirects to
  `https://docs.apilayer.com/marketstack/docs/api-documentation`) and
  `https://docs.apilayer.com/marketstack/docs/marketstack-api-v2-v-2-0-0`.
- **What blocked full resolution:** `https://marketstack.com/documentation_v2` returns a **301 redirect**
  to `docs.apilayer.com`; fetching that redirected URL via WebFetch returned only the page's static
  header/navigation shell (a JS-rendered documentation app) with **no endpoint-level content** — the
  actual indexlist/indexinfo parameter and example-response tables did not render in the fetched
  snapshot. No live API call was attempted because Marketstack (via APILayer) requires an API key even
  for a trial/demo call and no key was available in this sandbox; unlike Alpha Vantage, there is no
  published "demo" key that works without registration.
- **Coverage per general marketing copy (secondary, from web search, not a first-hand docs read):**
  Marketstack states via its own marketing pages that it covers "750+ of the world's major indices" and
  "30,000+ tickers from 50+ countries" — this is breadth marketing language, not a per-index catalog,
  and does not confirm or rule out DSEX/DS30/DSES.
- **Auth:** API key required (Bearer/query-param per APILayer's standard pattern); no working
  key/registration completed in this pass.
- **Identity coverage:** **unresolved** — no direct evidence either way was obtainable without a
  registered key, and the documentation JS-app did not render enough static content to check the actual
  index list even without calling the live API.
- **Category:** **Inconclusive/unresolved** — explicitly bounded: blocked by (a) JS-rendered docs pages
  not exposing endpoint content to a non-browser fetch, and (b) no API key available to call
  `GET /v2/indexlist?access_key=<key>` directly and grep the response. A future pass with a Marketstack
  trial key could resolve this by calling that endpoint directly.

---

## 8. CEIC

- **Ownership/operator:** CEIC Data (ISI Emerging Markets Group / part of Euromoney/ISI family of
  macro/market databases).
- **URL/endpoint:** `https://www.ceicdata.com/en/bangladesh/dhaka-stock-exchange-index`, plus specific
  series pages `.../dhaka-stock-exchange-monthly/dhaka-stock-exchange-index-dse-broad-index` (DSEX) and
  `.../dhaka-stock-exchange-index-dse-30-index` (DS30). CEIC's own listing shows the DSE-30 series as
  "active status," monthly frequency, 161 observations from Jan-2013 through Jun-2026 (per CEIC's public
  series-summary page, not independently re-fetched line-by-line in this pass).
- **Auth:** CEIC is a **paid subscription** data platform; access to the underlying values (not just the
  summary/chart preview) requires a commercial subscription. CEIC also offers an API/feed product
  (`https://info.ceicdata.com/api-and-data-feed-solution`) but this is enterprise/negotiated, not a
  public self-serve key.
- **Historical span/frequency:** DSEX/DS30 series shown as **monthly** on CEIC's public preview pages
  (not daily), which is coarser than typical index-level daily granularity needed for most investor/
  analyst use cases; DSES presence on CEIC not confirmed in this pass.
- **Licensing/redistribution:** subscription/commercial-license data; redistribution in an OSS library
  would require a data-licensing agreement, standard for CEIC-class aggregators.
- **Identity coverage:** DSEX and DS30 pages exist on CEIC (confirmed via CEIC's own site titles in
  search results); DSES **unknown/not checked**.
- **Category:** **Not exposed through a lawful API** — a public API exists in principle but only under
  paid/negotiated commercial licensing, which is out of scope for an OSS clean-room library without a
  paid contract; and the visible frequency (monthly) is coarser than the native index's actual (daily)
  publication cadence.

---

## 9. Mendeley Data / Kaggle (open dataset repositories)

- **Ownership/operator:** Mendeley Data (Elsevier) and Kaggle (Google) — general-purpose open dataset
  hosting platforms, not authoritative/official financial-data providers.
- **What was checked:** general awareness that both platforms host user-uploaded Bangladesh
  stock-market datasets (a known pattern for academic DSE research datasets), but this pass did not run
  fresh targeted searches confirming a currently-live, DSEX/DS30/DSES-labeled dataset with clear
  license terms, provenance, and update cadence.
- **Category:** **Inconclusive/unresolved** — plausible in principle (open, freely licensed datasets do
  exist on these platforms for various markets) but **not verified with dated evidence in this pass**;
  any such dataset would also typically be a static historical snapshot (not a live-updating source),
  which would not satisfy an ongoing "current native index points" need even if found and license-clear.
  Flagging honestly rather than fabricating a specific dataset URL/license.

---

## 10. Unofficial mirrors / scraper repos (named, not used)

Multiple community GitHub repos surfaced in search results purporting to scrape DSE data, e.g.
`github.com/ShanjinurIslam/Dhaka-Stock-Exchange` and `github.com/faysal515/bd-stock-api`. These are
**named for completeness only and were not opened, cloned, or evaluated technically** — per the task's
explicit "unofficial scraper/mirror" exclusion and this project's clean-room policy, community scrapers
of DSE's own copyrighted site inherit the same redistribution/copyright problem documented in Section 1
(DSE official) and are not a lawful basis for a redistributable OSS library regardless of their
technical functionality.

- **Category:** **Not exposed through a lawful API** (by inheritance from the underlying DSE
  copyright/ToS posture — an unofficial scraper does not create a license that doesn't otherwise exist).

---

## 11. BSEC / Bangladesh Bank

- **Ownership/operator:** Bangladesh Securities and Exchange Commission (BSEC, market regulator) and
  Bangladesh Bank (central bank).
- **What was checked:** targeted web search for open-data APIs from either institution covering
  DSEX/DS30/DSES.
- **Result (2026-07-25):** no evidence found of a BSEC or Bangladesh Bank open-data API exposing
  exchange index levels — both are regulatory/macro institutions, not index-data publishers; index
  publication is DSE's own function (Section 1), not the regulator's or central bank's.
- **Category:** **Confirmed absent** — no such API/data product was found to exist at either
  institution for these specific index identities (regulators publish oversight/macro data, not
  proprietary exchange index series).

---

## Executive verdict: SOURCE-BLOCKED

No candidate examined in this pass yields a lawful, technically adequate, native-index-point feed for
DSEX/DS30/DSES suitable for an OSS redistributable library:

- **Confirmed absent:** Alpha Vantage (`INDEX_CATALOG`, verified endpoint), BSEC/Bangladesh Bank.
- **Not exposed through a lawful API** (data exists but redistribution/automated-use is explicitly
  forbidden or requires a commercial license not available to an OSS project): DSE official
  (copyright.htm/termsacond.htm forbid redistribution and storage in any other retrieval system),
  TradingView (ToS forbids building products on its content / no API commercial use), CEIC (paid
  subscription only, and only monthly granularity even if licensed), unofficial mirrors (inherit DSE's
  own restriction).
- **Inconclusive/unresolved** (genuinely blocked by sandbox/tooling limits, not by a confirmed absence
  or confirmed prohibition): Stooq (anti-bot JS wall + `robots.txt: Disallow: /` for generic agents —
  could not verify symbol existence at all), FMP (demo key rejected, no real key available, docs page
  text silent on Bangladesh), Marketstack (JS-rendered docs didn't expose content, no key available),
  Mendeley/Kaggle (not freshly searched with dated verification).
- **Temporarily unreachable:** Investing.com's ToS pages (network egress from this sandbox to
  investing.com/its CDN failed on every attempt) — structurally it is very likely in the same
  "not exposed through a lawful API" bucket as TradingView/DSE based on the second-hand ToS language
  found, but this pass could not verify that first-hand.

**Recommendation for `vnfin`:** do not implement `dsex()`/`ds30()`/`dses()` native-index-point support
at this time. If Boss wants to pursue this further, the two highest-value next actions are: (1) obtain a
free FMP API key and a Marketstack trial key and re-run the two live catalog calls documented above
(cheap, ~5 minutes, would convert two "inconclusive" rows to definitive answers); (2) if lawful access
is truly required, contact DSE directly for a data-licensing/API arrangement (their copyright notice
explicitly carves out "prior written permission" as the path to redistribution) rather than attempting
further scraping.

---

## What changed from the prior pass

1. **Alpha Vantage evidence corrected.** The prior pass used `LISTING_STATUS` (a US equities/ETF
   ticker catalog) to claim Bangladesh-index absence — that endpoint cannot speak to index coverage at
   all. This pass re-verified with the correct `INDEX_CATALOG` endpoint (317 rows, `symbol,name` header,
   zero matches for DSEX/DS30/DSES/Dhaka/Bangladesh, confirmed via fresh `curl` on 2026-07-25) and
   documented what the endpoint actually is per Alpha Vantage's own "Major Indices"/index-catalog
   documentation, rather than just citing a row count.
2. **Stooq vetted with first-hand evidence, not assumed.** Discovered a client-side JS proof-of-work
   bot-verification wall on the documented CSV download endpoint (`/q/d/l/?s=...&i=d`) for all three
   symbols, plus a first-party `robots.txt: Disallow: /` for generic user-agents — this is new,
   concrete evidence (previously Stooq was not vetted for BD indices at all in the prior pass) and
   yields an honest "inconclusive" rather than a silent assumption either way.
3. **FMP and Marketstack bounded, not left vague.** Both now have an explicit "what I tried / what
   blocked me" trail: FMP's `demo` key is rejected outright (unlike Alpha Vantage's working `demo` key)
   and its docs page (successfully fetched after a 403 on the first attempt) contains zero
   Bangladesh/Dhaka/DSEX/DS30/DSES text; Marketstack's docs render as a JS app that didn't expose
   endpoint content to a non-browser fetch, and no trial key was available for a live call. Both are
   explicitly "inconclusive/unresolved," not silently treated as absent.
4. **TradingView and Investing.com ToS now have exact dated fetch evidence (or an explicit inability
   note).** TradingView's `/policies/` page was fetched directly on 2026-07-25 and its Section-3
   "non-display usage" and "no commercial use of any of our services or APIs" language is quoted
   verbatim. Investing.com's ToS could **not** be fetched directly (connection failures on every
   attempt, both HTML and PDF, both WebFetch and `curl`) — this pass explicitly flags that as
   "temporarily unreachable" rather than asserting "well-known terms," and separately surfaces
   second-hand quoted language from a search-engine snippet with that provenance caveat attached.
5. **DSE official reachability re-checked and found to differ from the prior pass.** Plain `curl`
   failed with a **local TLS trust-store error** (not a 403) in this sandbox; bypassing that
   (`-k`) showed the site is actually reachable (HTTP 200) on 2026-07-25, with real DSEX/DS30/DSES
   page content. This pass also went further than "just reachability" and pulled DSE's own
   `copyright.htm`/`termsacond.htm` text verbatim, which is new evidence not present in the prior pass
   and is the strongest, most direct basis for the "not exposed through a lawful API" verdict on the
   official source.
6. **BSEC/Bangladesh Bank explicitly checked** (not addressed at all in the prior pass) — confirmed
   absent as index-data providers; that function belongs to DSE itself.
