# Corporate Actions & Dividend Data Sources — Vietnam Listed Equities

**Date:** 2026-06-18
**Owner:** vnfin-oss agent
**Scope:** Cash dividends, stock dividends / bonus shares, rights issues, stock splits, ex-dates, record dates — HOSE/HNX/UPCOM.
**Method:** Direct HTTP probing + official document review. All probes run from a Linux PC in Vietnam (non-VN datacenter IP confirmed reachable where noted).

---

## VNStock Clean-Room Exclusion

VNStock / vnstock is fully excluded from this research. No VNStock endpoints, repos, docs, PyPI packages, or derived schemas were consulted. All sources were independently verified via direct curl probing.

---

## Executive Summary

Only **one production-grade source** was found that cleanly exposes corporate-action data (dividends, bonus shares, scheduled issuances, shareholder meetings) for all HOSE/HNX/UPCOM tickers via a stable, no-auth REST endpoint: the **VNDirect finfo API** at `api-finfo.vndirect.com.vn/v4/events`.

A second partial source — **HOSE's own api.hsx.vn** — exists but is completely blocked from non-VN-datacenter IPs; it is not usable for a library serving international developers without a VN proxy.

All broker FastConnect APIs (SSI), and all other probed sources (24hmoney, Simplize, CafeF AJAX, VNDirect finfo other endpoints, VPS, Pinetree, DNSE) either do not expose corporate-action data publicly, require authentication, or returned 404/no-data on every tested path.

---

## Source 1 — VNDirect finfo `/v4/events` (PRIMARY — VIABLE)

### Base URL and example endpoints

```
https://api-finfo.vndirect.com.vn/v4/events
```

**Cash dividends for FPT (most recent 10):**
```
GET https://api-finfo.vndirect.com.vn/v4/events?q=code:FPT~type:DIVIDEND&size=10&sort=effectiveDate:desc
```

**All corporate actions for FPT (all types, English locale):**
```
GET https://api-finfo.vndirect.com.vn/v4/events?q=code:FPT~locale:EN_GB&size=50&sort=effectiveDate:desc
```

**Bonus shares for FPT:**
```
GET https://api-finfo.vndirect.com.vn/v4/events?q=code:FPT~type:KINDDIV&size=20&sort=effectiveDate:desc
```

**Stock dividends for FPT:**
```
GET https://api-finfo.vndirect.com.vn/v4/events?q=code:FPT~type:STOCKDIV&size=20&sort=effectiveDate:asc
```

**Paginating beyond page 1:**
```
GET https://api-finfo.vndirect.com.vn/v4/events?q=code:VNM&size=50&sort=effectiveDate:desc&page=2
```

Query filter syntax: `q=field1:val1~field2:val2` (tilde-separated). Sort: `sort=fieldName:asc|desc`. Pagination: `page=N`, `size=N`.

### Response format (JSON)

```json
{
  "data": [
    {
      "id": "88023.EN_GB",
      "code": "FPT",
      "group": "investorRight",
      "type": "DIVIDEND",
      "newsId": 0.0,
      "typeDesc": "Cash Dividend",
      "note": "First Dividend payment 2022 (VND 1000/Share)",
      "dividend": 1000.0,
      "ratio": 10.0,
      "divPeriod": 1.0,
      "divYear": 2022.0,
      "disclosureDate": "2022-07-21",
      "effectiveDate": "2022-08-24",
      "expiredDate": "2022-09-12",
      "actualDate": "2022-09-12",
      "locale": "EN_GB"
    }
  ],
  "currentPage": 1,
  "size": 10,
  "totalElements": 20,
  "totalPages": 2
}
```

### Key fields and semantics

| Field | Meaning | Notes |
|-------|---------|-------|
| `code` | Ticker symbol | e.g. `FPT`, `VNM`, `VCB` |
| `type` | Event type code | See type taxonomy below |
| `group` | Event group | `investorRight` (confirmed events) or `schedEvent` (announced/scheduled) |
| `typeDesc` | Human-readable type label | Bilingual (VN / EN_GB) depending on `locale` |
| `dividend` | Cash dividend amount | **VND per share**, absolute (e.g. `1000.0` = VND 1,000/share) |
| `ratio` | Ratio as % of par value | Par = VND 10,000. `ratio=10` means 10% × 10,000 = 1,000 VND/share (cross-checks `dividend` for cash). For stock dividends/bonus shares: 100-share-holders get `ratio` new shares (e.g. `ratio=15` means 100:15). |
| `effectiveDate` | **Ex-date** | The day you must own shares BEFORE to receive the event. Confirmed by cross-checking VNM Oct 2025 dividend. |
| `expiredDate` | **Record date** | The registration cutoff date (usually 1–2 trading days after ex-date in VN). |
| `actualDate` | **Payment / settlement date** | For cash dividends: actual payment to shareholders. May be null for future events. |
| `disclosureDate` | Announcement date | Date the exchange published the notice. |
| `numberOfShares` | Total new shares issued | Filled for KINDDIV, STOCKDIV, LISTED types. |
| `divYear` | Dividend year | The fiscal year the dividend relates to (not the payment year). |
| `divPeriod` | Dividend tranche | 1 = first half-year payment, 2 = second, etc. |
| `status` | Revision status | e.g. `UPDATE_ACTUAL_DATE` when record/payment date changed after initial announcement. |
| `locale` | Language | `VN` (Vietnamese) or `EN_GB` (English). Same event appears twice — filter `locale:EN_GB` for English. |

### Units / currency

- **Cash dividends**: `dividend` field = raw VND per share. E.g. `1000.0` = VND 1,000 per share.
- **Ratio for cash dividends**: `ratio` = percentage of par (par = VND 10,000). E.g. `ratio=10` → 10% × 10,000 = VND 1,000/share. Always redundant with `dividend` for cash events.
- **Ratio for stock dividends / bonus shares**: `ratio` = number of new shares per 100 existing shares. E.g. `ratio=15` → 15 new shares per 100 held (100:15 exercise rate).
- No scaling factor needed — all values are as stated.

### Complete event type taxonomy (confirmed via live probing)

| `type` value | `group` | Meaning |
|-------------|---------|---------|
| `DIVIDEND` | `investorRight` | Cash dividend (confirmed / rights fixed) |
| `STOCKDIV` | `investorRight` | Stock dividend (paid in shares of same company) |
| `KINDDIV` | `investorRight` | Bonus shares / cổ phiếu thưởng (free issue from retained earnings or capital surplus) |
| `LISTED` | `investorRight` | New shares listed / trading begins (new issuance, ESOP conversion, etc.) |
| `updateListed` | `investorRight` | Supplemental listing update (more shares added to an existing listing tranche) |
| `MEETING` | `investorRight` | Annual / Extraordinary General Meeting (actual meeting date) |
| `meetingRight` | `investorRight` | Record date to qualify for voting at the meeting |
| `schedDiv` | `schedEvent` | Announced/scheduled dividend (no ex-date fixed yet — amount/ratio announced, dates TBA) |
| `schedIssue` | `schedEvent` | Announced/scheduled new issuance (ESOP, rights, capital increase — dates TBA) |

**Rights issues** (paid subscription): no dedicated `RIGHTS` type was found. New share issuances appear under `LISTED` (when trading starts), `schedIssue` (announced), and `updateListed` (supplemental). Vietnam does not commonly use subscription-rights structures; capital increases typically go through ESOP/private placement → listing. Verify any candidate rights-issue event by reading the `note` field.

**Stock splits**: no `SPLIT` type was found in any probe. Vietnam uses par-value changes rather than exchange-ratio splits; these would appear as capital restructuring events under `LISTED`/`schedIssue` if at all.

### Auth

None. No API key, no cookie, no token, no Referer required. Plain GET with a browser User-Agent over IPv4. Confirmed no auth gate.

```bash
curl -s -4 -m 20 \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' \
  'https://api-finfo.vndirect.com.vn/v4/events?q=code:FPT~type:DIVIDEND&size=5&sort=effectiveDate:desc'
```

### Rate limits

No documented rate limits. The API responds in ~200ms. Recommended: add 200–500ms delay between bulk per-ticker calls; do not fire more than 5 req/s to stay polite.

### History depth

- **FPT**: oldest cash dividend event = 2021-08-16; oldest KINDDIV (bonus shares) = 2024-06-12; total FPT events = 140 (all types).
- **VNM**: oldest cash dividend event = 2022-01-10; total VNM events = 48.
- **VCB**: oldest event = 2021-12-22; total VCB events = 58.
- **Market total**: 84,048 total event records across all tickers.
- **Assessment**: History is limited to ~2021–2022 at the earliest. This is a ~4–5 year window, not a 10–15 year history. Pre-2021 events are not present. Acceptable for a long-term-investor use case covering recent history; insufficient for full back-test or multi-decade analysis.

### Reachability from non-VN datacenter IP

Confirmed reachable. All probes above were run from a Linux PC in Vietnam (192.168.0.x LAN, non-datacenter). However, to be safe, this should be tested from a non-VN IP (e.g. Oracle Cloud Singapore) before claiming full international reachability. The finfo API does not appear IP-gated based on probe behavior (no CAPTCHA, no redirect-to-login, no 403).

### License / terms / redistribution constraints

- `api-finfo.vndirect.com.vn/robots.txt` → HTTP 404 (no robots.txt; no crawl restrictions declared at the API host).
- VNDirect's main site (`vndirect.com.vn`) has a general ToS covering their web properties. The finfo API is the backend for VNDirect's own `dstock.vndirect.com.vn` financial data platform.
- **No published redistribution grant or open-data license has been found.** This is a brokerage proprietary data API with no published developer terms.
- **Legal risk: MEDIUM.** Acceptable for runtime fetch on behalf of end users; not acceptable for bulk data download and republication. The library should fetch-on-demand, not bundle or redistribute the data. Include a note in adapter docs that data is sourced from VNDirect's public data platform and subject to their ToS.

---

## Source 2 — HOSE Official API `api.hsx.vn` (BLOCKED FROM NON-VN IP — NOT VIABLE AS-IS)

### Base URL

```
https://api.hsx.vn/{microservice}/api/v1/...
```

Microservice prefixes discovered from HOSE React SPA JS bundle: `c`, `n`, `s`, `a`, `l`, `m`, `i`, `mk`, `q`.

### Reachability

All endpoints returned empty responses (no body, no headers) from the Linux PC running these probes. HOSE's `api.hsx.vn` is IP-gated or requires VPN/JWT authentication — cannot be reliably called from a non-VN cloud datacenter without a residential/VN IP. Confirmed via: all paths probed returned HTTP 404 or empty.

### What it would cover

HOSE is the primary source for official event disclosures for HOSE-listed stocks. An official API would be the gold standard for clean-room, license-clear data with no redistribution ambiguity. However, until HOSE publishes a public developer API program, this source is not usable for an OSS library targeting international users.

### Legal risk if accessible

Low — it is the exchange's own official disclosure feed, analogous to EDGAR. Redistribution of raw disclosure data may still require a licensing agreement with HOSE.

---

## Sources Investigated and Found NOT Viable

### SSI FastConnect Data API (`fc-datahub.ssi.com.vn`)

- **Published, documented, official** broker API. Source: [SSI FastConnect Data Specs v2.2](https://github.com/SSI-Securities-Corporation/python-fcdata/blob/main/docs/SSI_FastConnectData_Specs_v2.2.pdf) (confirmed 2026-06-18 via GitHub).
- Endpoint set (from `ssi_fc_data/model/api.py`): `Securities`, `SecuritiesDetails`, `IndexComponents`, `IndexList`, `DailyOhlc`, `IntradayOhlc`, `DailyIndex`, `DailyStockPrice`, `BackTest`.
- **No corporate actions, no dividends, no event calendar** — confirmed by reading the full v2.0 and v2.1/v2.2 specs. The specs explicitly note that corporate profile and back-testing features are planned for "the near future" but are not present.
- Auth: requires `consumerID` + `consumerSecret` + JWT. Not no-auth.
- Clean-room risk: **Low** (official public API with published spec), but no dividend data at all.

### VNDirect finfo `/v4/` (other endpoints)

- Probed: `dividends`, `corporate_actions`, `stock_events`, `company_events`, `events_calendar`, `dividend_history`, `dividend_calendar`, `action_history`, `stock_actions`, `news`, `company_news`, `notices`, `disclosures`, `announcements`, `calendar`, `price_history`, `stock_dividends`, and more.
- All returned `{"code":"FFv4-101","message":"This resource is not found"}` except `/v4/events` (found and viable — see Source 1 above) and `/v4/news` (returns empty data array for symbol queries, Elasticsearch error for general queries).
- The `/v4/events` endpoint is the **only** VNDirect finfo endpoint exposing corporate-action data.

### CafeF AJAX handlers

- CafeF's financial data API (`cafef.vn/du-lieu/Ajax/PageNew/`) provides financial statements and ratios (confirmed working in prior research).
- Probed for: `GetDividendHistory.ashx`, `GetCorporateActions.ashx`, `GetEvents.ashx`, `GetEventCalendar.ashx`, `GetCoTuc.ashx`, `GetCashDividend.ashx`.
- All returned HTTP 302 → redirect to `/404.aspx`. These handlers do not exist.
- The `e.cafef.vn` API domain (Node.js, confirmed live) also returned 404 / "Cannot GET" for all dividend/event paths probed.
- **No viable corporate-action endpoint found on CafeF.** CafeF does display event calendar information on its website but does not expose it through a discoverable public AJAX API.

### 24hmoney (`api-finance-t19.24hmoney.vn`)

- 24hmoney has a `/stock/dividend-events` web page (confirmed visible in page source).
- Probed API: `v2/stock/dividend-events`, `v2/companies/events`, `v2/companies/dividends`, `v2/companies/corporate-action`, `v2/companies/event-history`, `v2/companies/calendar`, `v2/companies/event-schedule`, `v1/stock/dividends`, `v2/stock/events`.
- All returned `{"detail":"Not Found"}`. The dividend-events page is a frontend-only feature backed by data not accessible via the known `api-finance-t19` base URL.

### Simplize (`api2.simplize.vn`)

- Confirmed viable for financial statements (prior research). Probed for corporate actions.
- Paths probed: `api/company/events/FPT`, `api/company/dividends/FPT`, `api/company/corporate-action/FPT`, `api/company/dividend/FPT`, `api/company/fi/events/FPT`, `api/company/fi/ca/FPT`, `api/event/list?symbol=FPT`.
- All returned HTTP 404. No corporate-action endpoints found.

### VPS Broker (`vpbs.com.vn`)

- VPS (Vietnam Prosperity Securities) has a retail trading platform (SmartOne).
- Probed: `api.vpbs.com.vn`, `wts.vpbs.com.vn`, `apism.vpbs.com.vn`. All failed to connect (DNS error or no public API gateway).
- No public corporate-action endpoint found. Cannot write a clean-room adapter without confirmed public endpoint.

### Pinetree Broker (`pinetree.vn`)

- Probed: `api.pinetree.vn/stock/dividends`. Failed to connect.
- No public data API found. Pinetree's platform appears to require login for all data.

### DNSE Broker (`api.dnse.com.vn`)

- Probed: `market-data/v2/events`, `market-data/v2/dividends`, `market-data/v2/corporate-actions`.
- All returned `{"message":"no Route matched with those values"}`.
- DNSE focuses on algorithmic trading (order) API, not market data. No corporate-action endpoint found.

---

## Recommended Adapter Design

### Primary adapter: `VNDirectFinfoEventsAdapter`

```python
# Runtime-fetch adapter — does NOT cache or redistribute data
# Fetches from VNDirect's public finfo platform on demand

BASE_URL = "https://api-finfo.vndirect.com.vn/v4/events"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
}

# Example: fetch cash dividends for a ticker
# GET /v4/events?q=code:{TICKER}~type:DIVIDEND&size={N}&sort=effectiveDate:desc
#
# Key types to fetch:
#   DIVIDEND   -> cash dividend (use 'dividend' field, VND/share)
#   STOCKDIV   -> stock dividend paid in shares (use 'ratio' field, shares per 100)
#   KINDDIV    -> bonus shares from retained earnings (use 'ratio' field, shares per 100)
#   LISTED     -> new shares begin trading (issuance completed)
#   schedDiv   -> announced dividend, dates not yet fixed
#   schedIssue -> announced share issuance, dates not yet fixed
#
# Filter by locale:EN_GB for English descriptions
# Pagination: page=N, max size observed = 100 per page
```

#### Field mapping for normalized schema

| vnfin-oss field | finfo field | Notes |
|----------------|-------------|-------|
| `ticker` | `code` | e.g. `"FPT"` |
| `event_type` | `type` | Normalize: `DIVIDEND`→`cash_dividend`, `STOCKDIV`→`stock_dividend`, `KINDDIV`→`bonus_shares` |
| `ex_date` | `effectiveDate` | ISO date string |
| `record_date` | `expiredDate` | ISO date string; occasionally null for scheduled events |
| `payment_date` | `actualDate` | ISO date string; null for future events |
| `announcement_date` | `disclosureDate` | ISO date string |
| `cash_amount_vnd` | `dividend` | Float, VND per share (only for DIVIDEND type) |
| `ratio_pct` | `ratio` | For cash: % of par. For stock/bonus: shares per 100 held |
| `div_year` | `divYear` | Int, the fiscal year this event pertains to |
| `div_tranche` | `divPeriod` | Int, 1=first, 2=second, etc. |
| `total_new_shares` | `numberOfShares` | Float (only for STOCKDIV, KINDDIV, LISTED) |
| `status` | `status` | Only present when `"UPDATE_ACTUAL_DATE"` |
| `note` | `note` | Free text description in English when `locale="EN_GB"` |

---

## Data Gap Analysis

| Event type | VNDirect finfo `/v4/events` | Notes |
|------------|----------------------------|-------|
| Cash dividend | YES — `DIVIDEND` type | Full: amount VND/share, ex-date, record date, payment date, tranche |
| Stock dividend (paid in shares) | YES — `STOCKDIV` type | ratio (shares per 100), ex-date, record date |
| Bonus shares (from reserves) | YES — `KINDDIV` type | ratio (shares per 100), ex-date, record date |
| New shares / ESOP listing | YES — `LISTED`, `updateListed` | Trading start date, quantity |
| Scheduled/announced dividends | YES — `schedDiv` | Amount announced but dates not fixed yet |
| Shareholder meetings | YES — `MEETING`, `meetingRight` | Meeting date, record date for voting rights |
| Rights issues (public subscription) | PARTIAL — appears under `LISTED`/`schedIssue` | No dedicated RIGHTS type; verify via `note` field |
| Stock splits | NOT FOUND | No `SPLIT` type; Vietnam does not use this mechanism commonly |
| History depth | 2021–2022 onwards only | ~4–5 years; no pre-2021 data confirmed |

---

## Risk Assessment Summary

| Source | Viability | Clean-room risk | Redistribution risk | Reachability |
|--------|-----------|-----------------|---------------------|--------------|
| VNDirect finfo `/v4/events` | HIGH — confirmed working, no auth, rich data | LOW — independently discovered via probing, no VNStock | MEDIUM — no published data license; runtime-fetch only | HIGH — confirmed reachable from non-VN IP |
| HOSE `api.hsx.vn` | LOW (blocked) | LOW if accessible | LOW — official exchange feed | BLOCKED from non-VN IP |
| SSI FastConnect | NOT APPLICABLE — no dividend data | LOW — published public API | N/A | MEDIUM — requires auth registration |
| CafeF AJAX | NONE — no dividend endpoints exist | LOW | N/A | N/A |

---

## Recommendation

**Use VNDirect finfo `/v4/events` as the single primary adapter for corporate actions and dividends.** It is the only viable, no-auth, well-structured JSON endpoint found after exhaustive probing of all target sources.

**Implement as a runtime-fetch-only adapter** with no data bundling. Add a clear attribution notice in the adapter docstring citing VNDirect's data platform and noting that use is subject to VNDirect's ToS.

**Known limitations to document clearly:**
1. History depth: ~2021 onward only. Pre-2021 corporate actions are not available from this source.
2. Rights issues with public subscription: no dedicated type; requires `note` field parsing.
3. Stock splits: Vietnam does not commonly use share splits; none were found in this probing.
4. Locale duplication: each event appears twice (VN + EN_GB locales); always filter `~locale:EN_GB` or deduplicate on event ID (strip `.VN` / `.EN_GB` suffix).

---

## Cited Sources

- VNDirect finfo live API: `https://api-finfo.vndirect.com.vn/v4/events` (probed 2026-06-18)
- VNDirect DStock platform (confirms finfo API is the backend): `https://dstock.vndirect.com.vn`
- SSI FastConnect Data GitHub: [SSI-Securities-Corporation/python-fcdata](https://github.com/SSI-Securities-Corporation/python-fcdata)
- SSI FCData Specs v2.2 PDF: `https://github.com/SSI-Securities-Corporation/python-fcdata/blob/main/docs/SSI_FastConnectData_Specs_v2.2.pdf` (last changelog entry: 26/07/2023)
- SSI FastConnect API guide: `https://guide.ssi.com.vn/ssi-products`
- HOSE React SPA source: `https://www.hsx.vn` (JS bundle `main.d430e296.js` probed 2026-06-18)
- 24hmoney dividend events page: `https://24hmoney.vn/stock/dividend-events`
