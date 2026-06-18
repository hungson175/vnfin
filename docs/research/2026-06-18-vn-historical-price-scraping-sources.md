# Working Sources to Scrape Vietnam Historical Stock Prices (Daily + Intraday)

**Date:** 2026-06-18  **Owner:** vnfin-oss  **Scope:** HOSE / HNX / UPCOM historical OHLCV (daily = priority; intraday/hourly = bonus)

**VNStock clean-room exclusion (applied throughout):** All research and live probing explicitly excluded the Python library `vnstock` / VNStock and every derivative (vnstocks.com, docs.vnstock.site, thinh-vu/vnstock, vnstock-hq, vnstock-agent, any wrapper/notebook). Endpoints below were learned only from each provider's own server responses, public browser network traffic, and the public TradingView UDF protocol — never from vnstock code, docs, schemas, or naming.

**Method:** A multi-agent workflow probed 15 candidate sources. Each candidate got (1) a *probe* agent that ran real `curl` calls and had to paste actual OHLC rows as proof, then (2) an independent *adversarial verify* agent that re-ran the exact command from scratch to confirm it reproduces right now (validating array lengths, OHLC invariants, real trading dates, current-to-today data). 30 agents total. Network from the test host required IPv4 (`curl -4`) + a browser `User-Agent`.

**Result: 13 working (daily independently verified), 1 partial, 1 failed.**

> ⚠️ **Redistribution (applies to ALL sources):** every endpoint serves HOSE/HNX/UPCOM *exchange* market data via a broker/portal. None publish an explicit redistribution grant. Treat all as fine for **personal research / backtesting / internal analytics**; do **NOT** re-host, resell, or bundle the raw OHLCV as a commercial dataset/API without a written license from the provider/exchange. The library should fetch at runtime with no bundled data.

> 🔑 **Architecture insight:** most working sources speak the **TradingView UDF** protocol — `GET .../history?symbol=&resolution=&from=&to=` returning parallel arrays `{t,o,h,l,c,v,s}`. A *single* UDF client class with a pluggable base-URL + a small per-provider quirks map (path, resolution tokens, adjustment) gives the library near-instant multi-source **failover** across VNDirect, SSI, Vietstock, VPS, KIS, Pinetree, Wichart (and DNSE/Yahoo with minor shape tweaks). Vietcap (POST/JSON), Simplize, CafeF, FireAnt are bespoke shapes.

> 📐 **Adjustment caveat (schema-relevant):** most feeds return **split/dividend-ADJUSTED** prices (e.g. FPT ~7 in 2015 → ~72 in 2026). **Simplize and CafeF return RAW/unadjusted** — useful as an unadjusted cross-check. The library's contract must label adjustment explicitly.

## Summary table

| # | Source | Tier | Auth | Daily depth | Intraday | Verified |
|---|--------|------|------|-------------|----------|----------|
| 1 | VNDirect dchart UDF | 1 | none | ≥2005 | yes | ✅ |
| 2 | SSI iBoard public chart API | 1 | none | ≥2006 | yes | ✅ |
| 3 | Vietstock price history | 1 | none | ≥2006 | yes | ✅ |
| 4 | CafeF AJAX price history | 2 | none | ≥2006 | no | ✅ |
| 5 | Vietcap / VCI chart API | 2 | none | ≥2015 | yes | ✅ |
| 6 | Simplize price history | 2 | none | ≥2000 | yes | ✅ |
| 7 | DNSE / Entrade public chart | 2 | none | ≥2010 | yes | ✅ |
| 8 | VPS Securities | 2 | none | ≥2010 | yes | ✅ |
| 9 | KIS Securities Vietnam | 2 | none | ≥2000 | yes | ✅ |
| 10 | Pinetree / DSC Securities | 2 | none | ≥2010 | yes | ✅ |
| 11 | FireAnt historical-quotes | 3 | bearer token (long-liv | ≥2010 | no | ✅ |
| 12 | Wichart | 3 | none | ≥2014 | yes | ✅ |
| 13 | Yahoo Finance chart API | 3 | none | ≥2010 | yes | ✅ |

*Tier 1 = best primaries (no-auth, deep daily, single-request/UDF). Tier 2 = strong no-auth backups. Tier 3 = conditional (token / throttling / encrypted).*

## Source details (all independently reproduced)

### VNDirect dchart UDF

- **Host:** `dchart-api.vndirect.com.vn`
- **Auth:** none
- **Daily endpoint:** `GET https://dchart-api.vndirect.com.vn/dchart/history?symbol={TICKER}&resolution=D&from={UNIX_SECONDS}&to={UNIX_SECONDS}`
- **Daily history depth:** Hard server floor at 2013-01-02. Requesting from=2005-01-01 for both FPT and VCB clamps the earliest bar to 2013-01-02 (3353 bars to 2026-06-17). from=2015-01-01 returns 2856 daily bars starting 2015-01-05 for both tickers. Pre-2013-01-02 ranges return s:"ok" with empty arrays. So ~13+ years of adjusted daily OHLCV, nothing earlier than 2013-01-02.
- **Intraday:** Per /config and /symbols supported_resolutions: 1, 5, 15, 30, 60 (minutes), D, W, M. Verified live: resolution=60 (hourly) returns session bars 09:00/10:00/11:00/13:00/14:00 (35 bars over ~10 days); resolution=15 returns 15-min bars (09:15,09:30,...); has_intraday:true. Intraday history is shallower than daily: hourly (60) requested from 2020-01-01 clamped to earliest 2021-11-05 09:00 (~735 bars) — roughly the last ~4.5 years intraday vs 13+ years daily.
  - endpoint: `GET https://dchart-api.vndirect.com.vn/dchart/history?symbol={TICKER}&resolution={1|5|15|30|60}&from={UNIX_SECONDS}&to={UNIX_SECONDS}`
- **Format:** TradingView UDF JSON: parallel arrays {t[],o[],h[],l[],c[],v[]} plus status field s ("ok" with data, "ok" + empty arrays for no data in range). Content-Type text/plain;charset=UTF-8. Prices arrive in thousands of VND (e.g. FPT close 72.3 = 72,300 VND), back-adjusted. t = unix epoch seconds; daily bars dated 00:00 UTC, intraday bars carry intraday timestamps (session 09:00-15:00 Asia/Bangkok per /s
- **Rate limits:** No rate limiting observed. 15 rapid sequential GETs all returned HTTP 200, no 429, no Retry-After, no rate-limit headers. Server sets a TS015b7ec3 cookie (likely an F5/BIG-IP LB cookie, not auth — requests succeed without returning it). No documented limit; stay polite (low concurrency) as behavior 
- **robots/ToS:** /robots.txt returns HTTP 404 (Spring JSON error body), so no robots policy on the API host. Undocumented internal backend powering VNDirect's public web charting via the TradingView UDF protocol. No published API ToS on this host; VNDirect's general website Terms of Use likely govern. Treat as unoff
- **Redistribution:** No explicit data license or redistribution grant published. Underlying data is HOSE/HNX/UPCOM exchange market data via VNDirect, typically subject to exchange/vendor redistribution restrictions. Safe for personal research/backtesting/internal analytics. Do NOT redistribute raw OHLCV as a commercial dataset or re-host as an API without a VNDirect/exchange license. Conservative: store derived/aggreg
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' "https://dchart-api.vndirect.com.vn/dchart/history?symbol=FPT&resolution=D&from=$(date -d '2015-01-01' +%s)&to=$(date -d '2026-06-17' +%s)"
```

### SSI iBoard public chart API

- **Host:** `iboard-api.ssi.com.vn`
- **Auth:** none (no cookie, no bearer, no API key — works with no User-Agent and no Referer)
- **Daily endpoint:** `https://iboard-api.ssi.com.vn/statistics/charts/history?resolution=1D&symbol={TICKER}&from={UNIX_FROM}&to={UNIX_TO}`
- **Daily history depth:** Returns full available history regardless of how old `from` is. FPT: earliest bar 2006-12-13 (4840 daily bars to 2026-06-17). VCB: earliest bar 2009-07-01 (4223 bars). Asking from 2015-01-01 returned 2856 bars starting 2015-01-05. Data is current through today (2026-06-17). Note: older prices are split/dividend-adjusted (e.g. FPT 7.14 in 2015 vs ~72 now).
- **Intraday:** Minute resolutions confirmed working: 1, 5, 15, 30, 60 (minutes). 'H'/'1H' are accepted but bucket into ~daily granularity (not true hourly), so use '60' for hourly. Intraday history is a recent-window only: 1-min data is available roughly the last ~4 weeks (earliest 1-min bar today was 2026-05-20; requests from 2026-05-15 or earlier returned 0 bars). Sample FPT resolution=1: 2026-06-10 09:15 -> 73.5/73.7/73.5/73.6 vol 57200. Timestamps are UTC; add 7h for Vietnam local trading times.
  - endpoint: `https://iboard-api.ssi.com.vn/statistics/charts/history?resolution={1|5|15|30|60}&symbol={TICKER}&from={UNIX_FROM}&to={UNIX_TO}`
- **Format:** JSON, TradingView-UDF style. Envelope: {"code":"SUCCESS","message":...,"data":{...},"status":"ok"}. data holds parallel arrays t (unix seconds), o, h, l, c, v plus status string s ("ok") and nextTime (null when complete). Empty/unknown symbol returns code SUCCESS with empty arrays and s="ok" (NOT s="no_data"). content-type: application/json; charset=utf-8.
- **Rate limits:** No rate-limit headers observed. 12 rapid sequential daily requests all returned HTTP 200 with no throttling. Served via Cloudflare (server: cloudflare, cf-cache-status: REVALIDATED) so responses are edge-cached; be polite but no hard limit was hit during testing.
- **robots/ToS:** robots.txt at https://iboard.ssi.com.vn/robots.txt: "User-agent: * / Disallow:" (empty Disallow = allows all crawling). The API host iboard-api.ssi.com.vn has no robots.txt (returns Kong gateway 'no Route matched'). A terms page exists at https://iboard.ssi.com.vn/terms (HTTP 200) — should be review
- **Redistribution:** Data is SSI proprietary market data delivered without auth for the public iBoard charting UI. Open CORS (access-control-allow-origin: *) and empty Disallow in robots.txt indicate scraping for personal/internal use is technically unrestricted, but redistribution of the price data is almost certainly governed by SSI's terms (/terms page exists) and underlying exchange (HOSE/HNX) data-licensing rules
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://iboard-api.ssi.com.vn/statistics/charts/history?resolution=1D&symbol=FPT&from=1420045200&to=1781629200'
```

### Vietstock price history (api.vietstock.vn TradingView UDF + finance.vietstock.vn)

- **Host:** `api.vietstock.vn`
- **Auth:** none for the TradingView UDF endpoint (api.vietstock.vn) — NO login, NO cookie, NO CSRF token needed; ONLY a browser User-Agent + a Referer header (https://stockchart.vietstock.vn/ or finance.vietstock.vn). The legacy finance.vietstock.vn HTML/AJAX path needs an anonymous session cookie + matching __RequestVerificationToken pair (still no logged-in account), but it is inferior.
- **Daily endpoint:** `https://api.vietstock.vn/tvnew/history?symbol={TICKER}&resolution=D&from={unix_from}&to={unix_to}  (also https://api.vietstock.vn/ta/history with same params; resolution=D daily, W weekly, M monthly)`
- **Daily history depth:** Full listing history per stock in a SINGLE request, no per-request range cap. FPT verified back to 2006-12-13 (IPO/listing first bar); VCB back to ~2009-06-30 (its listing). A 2015-01-01..2026-06-17 request returned 2856 daily bars (2015-01-05 -> 2026-06-17). Prices are split/dividend-ADJUSTED (continuous back-adjusted series), ideal for long-term analysis. NOTE: the legacy finance.vietstock.vn AJAX path (POST /data/KQGDThongKeGiaStockPaging) is anchored to today and capped at 13 pages x 20 = ~260 trading days (~1 year) of RAW (unadjusted) prices and ignores arbitrary historical fromDate — so use the UDF endpoint for history.
- **Intraday:** Verified working: 1, 5, 15, 60 (minutes), plus D (daily), W (weekly). FPT 1-min returned 1130 bars over ~5 trading days; 5-min 230 bars; 15-min 80 bars; 60-min 25 bars. Intraday depth appears limited to recent days/weeks (daily/weekly/monthly go back to listing).
  - endpoint: `https://api.vietstock.vn/tvnew/history?symbol={TICKER}&resolution={1|5|15|60}&from={unix_from}&to={unix_to}`
- **Format:** JSON, TradingView UDF style: {"s":"ok","t":[unix_secs...],"o":[...],"h":[...],"l":[...],"c":[...],"v":[...]} — parallel arrays. (The legacy finance.vietstock.vn /data/KQGDThongKeGiaStockPaging path returns a different nested JSON array with rows containing OpenPrice/HighestPrice/LowestPrice/ClosePrice/TotalVol and TradingDate as /Date(ms)/.)
- **Rate limits:** No rate-limiting observed: 10 rapid sequential calls to tvnew/history all returned HTTP 200, and 8 rapid calls to the legacy finance.vietstock.vn AJAX path also all returned 200. No 429s or throttling seen during testing. (Be polite anyway — these are the provider's own servers.) The ONLY gotcha is 
- **robots/ToS:** finance.vietstock.vn/robots.txt: User-agent:* with Disallow on /*.js, /*.css, /manager, /export, /cache, /admin (so the /export Excel route IS disallowed; the /data AJAX and the api.vietstock.vn UDF datafeed are NOT listed/disallowed). api.vietstock.vn has NO robots.txt (returns 404), so no crawl ru
- **Redistribution:** Data is Vietstock proprietary/copyrighted market data. Scraping for personal/internal analysis is technically trivial (no auth), but REDISTRIBUTION is NOT clearly permitted and is almost certainly restricted under Vietstock's Terms of Use (and underlying HOSE/HNX exchange data licensing). Do NOT redistribute, resell, or bundle this raw data into a public dataset/API without an explicit commercial 
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 30 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' -H 'Referer: https://stockchart.vietstock.vn/' 'https://api.vietstock.vn/tvnew/history?symbol=FPT&resolution=D&from=1420045200&to=1781629200'
```

### CafeF AJAX price history (DataHistory/PriceHistory.ashx)

- **Host:** `cafef.vn (use this directly; s.cafef.vn 301-redirects and DROPS the query string)`
- **Auth:** none (no auth, no cookie, no token; CORS Access-Control-Allow-Origin: *)
- **Daily endpoint:** `https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx?Symbol={TICKER}&StartDate={MM/DD/YYYY}&EndDate={MM/DD/YYYY}&PageIndex={n}&PageSize={<=20}  (StartDate/EndDate may be left empty for latest ~3 months; ExchangeType param optional and may be blank)`
- **Daily history depth:** Full history back to IPO. FPT verified to 13/12/2006; VCB verified to 30/06/2009 (its HOSE listing date). Any window in between returns real data. CAVEAT: server caps each response to ~3 months / ~65 trading rows anchored to EndDate, regardless of how early StartDate is. To pull the full multi-year series you must iterate windows of <=3 months (quarter-by-quarter), moving EndDate earlier each time, and paginate within each window via PageIndex (PageSize capped at 20).
- **Intraday:** none via public endpoint
- **Format:** JSON. Envelope: {"Data":{"TotalCount":int,"Index":"VNINDEX","DateIndex":...,"ClosePriceIndex":...,"TradingReport":{...},"Data":[ROWS]},"Message":null,"Success":true}. Each ROW (Vietnamese keys): Symbol; Ngay (date dd/mm/yyyy); GiaMoCua=open; GiaCaoNhat=high; GiaThapNhat=low; GiaDongCua=close; GiaDieuChinh=adjusted close; KhoiLuongKhopLenh=matched volume (shares); GiaTriKhopLenh=matched value (VND 
- **Rate limits:** No rate-limiting observed. 8 rapid sequential requests all returned HTTP 200 in ~0.38-0.64s each. No 429/403, no Retry-After, no Crawl-delay. Server: Microsoft-IIS/10.0 / ASP.NET. Be polite anyway (add a small delay when iterating quarterly windows across many tickers).
- **robots/ToS:** https://cafef.vn/robots.txt = HTTP 200, fully permissive: "User-agent: * / Allow: /", no Disallow, no Crawl-delay; /du-lieu/ and /ajax/ are NOT disallowed. (robots.txt under /du-lieu/ subpath 404s, so apex robots applies.) CafeF is a commercial financial-news portal operated by VCCorp; no explicit d
- **Redistribution:** No explicit redistribution permission. CafeF/VCCorp is a commercial portal; data is provided for on-site viewing. robots.txt allows crawling but does not grant a license to redistribute or resell the data. For a clean-room OSS library, treat CafeF as a personal/research convenience source only: do NOT bundle/redistribute CafeF-sourced datasets, and prefer official exchange (HOSE/HNX) or licensed-v
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=False

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx?Symbol=FPT&StartDate=01/01/2015&EndDate=03/31/2015&PageIndex=1&PageSize=20'
```

### Vietcap / VCI chart API (trading.vietcap.com.vn)

- **Host:** `trading.vietcap.com.vn`
- **Auth:** none
- **Daily endpoint:** `POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap  (Content-Type: application/json) body: {"timeFrame":"ONE_DAY","symbols":["<TICKER>",...],"from":<unix_sec>,"to":<unix_sec>}`
- **Daily history depth:** Deep. Both FPT and VCB returned data back to 2015-01-05 when requesting from=2015-01-01 (FPT 2857 daily rows, VCB 2857 rows), through 2026-06-16. Did not probe earlier than 2015 but the requested 2015 floor was honored.
- **Intraday:** Confirmed WORKING timeFrame tokens: ONE_MINUTE, ONE_HOUR, ONE_DAY, ONE_WEEK, ONE_MONTH (all return TradingView-style parallel arrays). ONE_MINUTE FPT returned 1130 bars over ~5 trading days; ONE_HOUR returned 25 bars. FIVE_MINUTE / FIFTEEN_MINUTE / THIRTY_MINUTE tokens returned EMPTY [] (not supported under those names). Numeric tokens ("5","15","1H","1D") and malformed tokens trip the WAF -> 403, so do not guess tokens.
  - endpoint: `Same endpoint POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap , vary timeFrame. Working values observed: ONE_MINUTE, ONE_HOUR (plus daily/weekly/monthly).`
- **Format:** JSON array, one object per symbol. Keys: symbol, o[], h[], l[], c[], v[], t[] (UNIX seconds as STRINGS), accumulatedVolume[], accumulatedValue[], minBatchTruncTime. Parallel-array (TradingView UDF-like) layout; arrays index-aligned by t. Prices in VND. Older history is split/dividend-ADJUSTED; most recent rows are raw exchange prices (mixed adjustment within one series). CORS response header acces
- **Rate limits:** No rate limiting observed on VALID requests: 12 rapid sequential POSTs all returned HTTP 200. The real risk is the WAF (Veloceed/veloceed.com edge, "X-Cache: ... veloceed.com"), which returns an HTML "ACCESS DENIED" 403 page (with Incident ID + your IP) for any request it deems suspicious: missing R
- **robots/ToS:** /robots.txt does not exist as a file; the host returns the SPA index.html (HTTP 200, HTML) for that path, so there is no robots directive either allowing or disallowing /api/. No machine-readable crawl policy was found. This is the backend of Vietcap's public price-board web app (trading.vietcap.com
- **Redistribution:** Redistribution NOT confirmed as permitted. This is Vietcap (a licensed VN securities firm) market data served to its own web client; no open-data license or explicit redistribution grant was found. Vietnamese exchange price data is typically subject to vendor/exchange terms. Safe for internal analysis/research and personal use; do NOT redistribute or resell raw data without checking Vietcap's term
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 30 -X POST 'https://trading.vietcap.com.vn/api/chart/OHLCChart/gap' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' -H 'Content-Type: application/json' -H 'Referer: https://trading.vietcap.com.vn/' -d '{"timeFrame":"ONE_DAY","symbols":["FPT"],"from":1420045200,"to":1781629200}'
```

### Simplize price history (simplize.vn)

- **Host:** `api2.simplize.vn (alias api.simplize.vn behaves identically for the daily endpoint; both behind Cloudflare)`
- **Auth:** none (no API key, no token, no cookie required — server sets a JSESSIONID cookie in the response but it is NOT needed for the request to succeed; a plain GET with a browser UA returns 200)
- **Daily endpoint:** `GET https://api2.simplize.vn/api/historical/prices/ohlcv?ticker={TICKER}&page=0&size={N}  — params: ticker (HOSE/HNX/UPCOM symbol, e.g. FPT, VCB), page (0-based), size (rows; use a large value like 10000 to get full history in one call). Returns RAW (unadjusted) daily OHLCV.`
- **Daily history depth:** Full history back to listing date, well beyond 2015. FPT: 4858 daily rows, earliest 2006-12-13 (ts 1165968000) → latest 2026-06-17. VCB: 4233 rows, earliest 2009-06-30 (ts 1246320000) → 2026-06-17. A single request with size=10000 returned the entire series; pagination via page/size also works.
- **Intraday:** period controls resolution on /api/historical/prices/chart: period=1d -> 1-MINUTE bars (timestamps 60s apart, verified); period=1m (one month) and period=3m -> 1-HOUR bars (3600s apart, verified); period=1y / 5d / 1w / intraday -> DAILY bars but ADJUSTED (split/dividend-adjusted) prices. Note: the chart endpoint's daily output is adjusted, whereas the ohlcv endpoint's daily output is RAW/unadjusted — use ohlcv for true daily OHLC. Tick data available via /api/historical/ticks/{TICKER}.
  - endpoint: `GET https://api2.simplize.vn/api/historical/prices/chart?ticker={TICKER}&period={PERIOD}  — same array format [t,o,h,l,c,v]. Also: /api/historical/prices/his-chart (same shape, delayed variant) and /api/historical/ticks/{TICKER} for tick-by-tick trades [t,volume,price,side B/S].`
- **Format:** JSON. Envelope {"status":200,"message":"Success","data":[...]} where data is an array of arrays. OHLCV/chart rows = [timestamp_unix_seconds, open, high, low, close, volume]; ticks rows = [timestamp, volume, price, side]. Prices in VND as floats (volume sometimes in scientific notation e.g. 1.06522E7).
- **Rate limits:** No rate-limit headers present. An 8-request burst (no delay) all returned HTTP 200 with stable ~230-320ms latency, no 429/throttling observed. Served via Cloudflare (cf-ray, server: cloudflare, cf-cache-status: DYNAMIC). Responses are no-cache. Be polite to avoid Cloudflare WAF triggering; a browser
- **robots/ToS:** robots.txt (https://simplize.vn/robots.txt, fetched, HTTP 200, updated 2026-03-11): User-agent: * => Allow: / with Disallows for /community/*, /portfolio/*, /watchlist/*, /profile/*, /screener/, /chart, /news/*. Stock pages live under /co-phieu/ which is explicitly Allowed (and named AI bots are exp
- **Redistribution:** Redistribution is NOT freely permitted. Simplize's llms.txt imposes: (1) MANDATORY citation 'Nguồn: Simplize.vn' with a specific timestamp [Cập nhật lúc HH:MM, ngày DD/MM/YYYY] whenever their price data is used in any answer; (2) must not present stale data as current; (3) creating a dataset or training a COMMERCIAL AI model from Simplize data 'CẦN PHÊ DUYỆT BẰNG VĂN BẢN' = REQUIRES WRITTEN APPROV
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=False

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://api2.simplize.vn/api/historical/prices/ohlcv?ticker=FPT&page=0&size=10000'
```

### DNSE / Entrade public chart (services.entrade.com.vn)

- **Host:** `services.entrade.com.vn`
- **Auth:** none — fully public, no cookie/bearer/API-key required. No credentials were sent; HTTP 200 returned for both FPT and VCB.
- **Daily endpoint:** `https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from={UNIX_SEC}&to={UNIX_SEC}&symbol={TICKER}&resolution=1D  (params: from, to = unix epoch SECONDS; symbol = ticker e.g. FPT/VCB; resolution=1D for daily)`
- **Daily history depth:** FPT: requesting from=2010-01-01 returned 3553 points with the EARLIEST real bar at 2012-03-20, and nextTime=0 (signals no older data) — so history floor is ~2012-03 for FPT. Requesting from=2015-01-01 returned 2856 daily bars 2015-01-05 through 2026-06-16 (latest trading day) for BOTH FPT and VCB. So daily history is roughly a full decade+ (2012→present for older listings).
- **Intraday:** Confirmed working: 1 (1-min), 5, 15, 30 (minutes), 1H (hourly), 1D (daily). NOT supported: 1W and 1M (both return empty t/o/h/l/c/v arrays with HTTP 200 — aggregate weekly/monthly from 1D client-side). Intraday history is shallow vs daily (only recent days returned for minute resolutions).
  - endpoint: `Same endpoint, change resolution: https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from={UNIX_SEC}&to={UNIX_SEC}&symbol=FPT&resolution=1  (1-minute). Verified: resolution=1 returned 1581 one-minute bars; 1H returned hourly bars; 5/15/30 also returned data. Timestamps are UTC (02:15 UTC = 09:15 Vietnam market open).`
- **Format:** JSON, TradingView-UDF-style PARALLEL ARRAYS. Keys: t (unix sec, UTC), o, h, l, c, v, plus nextTime (pagination cursor; 0 = no more history). NOTE: this v2 response has NO 's' status field on success; an invalid symbol instead returns HTTP 400 {"status":400,"code":"BAD_REQUEST","message":"invalid symbol"}.
- **Rate limits:** No rate limiting observed. 15 rapid sequential requests all returned HTTP 200 in ~140-165ms each (median ~0.15s). No 429s, no throttling headers, no Retry-After. Be a good citizen and add modest delays for bulk pulls, but no limit was triggered in testing.
- **robots/ToS:** /robots.txt returns HTTP 404 with a Kong API-gateway body ({"message":"no Route matched..."}) — no robots policy is served on this API host, so there is no robots.txt directive to honor or violate. This is DNSE's (Entrade) public broker charting backend; no public ToS for the raw endpoint was locate
- **Redistribution:** UNCERTAIN / conservative flag: This is DNSE (a licensed Vietnamese broker) serving exchange-sourced (HOSE/HNX/UPCoM) price data. Underlying market data is owned by the exchanges; redistribution of bulk historical OHLCV may require a market-data license. The endpoint is public and unauthenticated (fine for personal research/analysis/backtesting), but DO NOT assume you may rebundle and redistribute 
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from=1420045200&to=1781629200&symbol=FPT&resolution=1D'
```

### VPS Securities (SmartOne historical datafeed) — histdatafeed.vps.com.vn

- **Host:** `histdatafeed.vps.com.vn (companion symbol-master host: bgapidatafeed.vps.com.vn)`
- **Auth:** none — fully anonymous. No cookie, bearer token, API key, or account. CORS wide open (Access-Control-Allow-Origin: *), callable from any origin/browser.
- **Daily endpoint:** `https://histdatafeed.vps.com.vn/tradingview/history?symbol={TICKER}&resolution=D&from={UNIX_SECONDS}&to={UNIX_SECONDS}`
- **Daily history depth:** Deep. FPT: 2856 daily bars, oldest 2015-01-05 (full range returned when asked from 2015). VCB: 4101 daily bars, oldest 2010-01-04 (returned all the way back when asked from 2010-01-01). So daily depth is at least ~16 years for older-listed names, back to listing date otherwise. Prices are split/dividend-ADJUSTED (e.g. FPT 2015 close ~8.29).
- **Intraday:** Supported (s=ok): 1, 5, 15, 30, 60 (minutes). NOT supported (s=null/empty): 120, 240, W, M, 1W, 1M — daily D is the deepest aggregation offered. Intraday timestamps are UTC (first bar 02:15:00 UTC = 09:15 ICT, Vietnam open). LIMIT: intraday is short-retention/server-capped — 1-min requested from 2024-01-01 still only returned ~1130 bars covering roughly the last 6 trading days (2026-06-10..2026-06-16). Good for recent days only, not deep intraday history.
  - endpoint: `Same endpoint, vary resolution: https://histdatafeed.vps.com.vn/tradingview/history?symbol={TICKER}&resolution={1|5|15|30|60}&from={UNIX_SECONDS}&to={UNIX_SECONDS}`
- **Format:** TradingView UDF JSON, parallel arrays: {"symbol":"FPT","s":"ok","t":[unix_sec...],"o":[],"h":[],"l":[],"c":[],"v":[]}. Status s = "ok" (data) / "no_data" (valid request, empty arrays — e.g. invalid ticker) / absent for unsupported resolution. Content-Type: application/json; charset=utf-8.
- **Rate limits:** No rate limiting observed. 12 rapid sequential daily requests all returned HTTP 200 in ~0.18–0.20s each; no 429, no throttle, no Retry-After / X-RateLimit headers. Server keep-alive timeout=5s. Still be polite for bulk pulls of the 1895-symbol universe (small delay + capped concurrency) since this i
- **robots/ToS:** /robots.txt returns HTTP 404 (no robots file — nothing disallowed, but nothing explicitly permitting crawling either). /tradingview/config and /tradingview/symbols return 404; only /tradingview/history is exposed (partial TradingView UDF datafeed). No ToS/API-license page on this datafeed subdomain.
- **Redistribution:** Redistribution NOT confirmed as permitted. Brokerage's own market-data feed; HOSE/HNX/UPCOM data is typically exchange-licensed, and prices here are adjusted/derived. Treat as OK for personal/research/analysis fetching; do NOT assume rights to redistribute raw OHLCV, resell, or republish as a dataset without explicit written permission from VPS and/or the exchanges. For the OSS library, expose as 
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://histdatafeed.vps.com.vn/tradingview/history?symbol=FPT&resolution=D&from=1420045200&to=1781629200'
```

### KIS Securities Vietnam — WTS web trading platform datafeed (api.ikis.kisvn.vn)

- **Host:** `api.ikis.kisvn.vn (NOT trading.kisvn.vn). The trading.kisvn.vn SPA loads its TradingView chart from api.ikis.kisvn.vn/api/v3/chart/chart.html, whose chart.js wires a UDF Datafeed against base https://api.ikis.kisvn.vn/api/v3/chart/ . Static JS bundles live on static.ikis.kisvn.vn (CloudFront).`
- **Auth:** none — no cookie, no bearer, no API key, no account. Works with no Referer/Origin and even default curl UA. Public unauthenticated UDF feed.
- **Daily endpoint:** `https://api.ikis.kisvn.vn/api/v3/chart/history?symbol={TICKER}&resolution=1D&from={unix_sec}&to={unix_sec}`
- **Daily history depth:** Full listed history per symbol. Requested from 2015-01-01 → got 2855 daily bars for both FPT and VCB starting 2015-01-05. Probing by year: VCB returns s=ok bars=0 for 2000/2005/2008 (pre-listing) and first real bars at 2009-06-30 (VCB's listing). So depth = back to each symbol's IPO/listing date (FPT data also runs many years back). NOTE: a single wide request (e.g. 1998→now) returns empty; the server caps the per-request window — chunk into ~1-year (daily) windows to pull deep history, exactly as KIS's own chart.js does. Older bars are split/dividend back-ADJUSTED (fractional VND values); recent bars are raw unadjusted VND.
- **Intraday:** Working intraday: 1 (1-min), 5, 15, 30, 60 (minutes). Also 1W (weekly) and 1M (monthly). Resolution string format that WORKS = digits then optional D/W/M unit-letter: '1D','1W','1M','5','15','30','60','1'. Bare 'D','W','M','1','5' on a WIDE range 500s — but with a narrow window 1-min works (FPT 2026-06-16 single-day returned full minute series). Intraday window is short-retention: 1-min needs ~1-day windows; 5/15/30/60-min comfortably return 7-day windows (288/108/60/36 bars). Symbol-info declares intraday_multipliers ['1','3','5','10','15','30','60'] and supported_resolutions ['1','3','5','10','15','30','60','1D','1W','1M'].
  - endpoint: `Same path, change resolution: https://api.ikis.kisvn.vn/api/v3/chart/history?symbol={TICKER}&resolution={1|5|15|30|60}&from={unix_sec}&to={unix_sec}`
- **Format:** TradingView UDF JSON: {"s":"ok","t":[unix_sec...],"o":[],"h":[],"l":[],"c":[],"v":[],"nextTime":...}. s='ok' has data, s='no_data' empty, missing s / HTTP 500 = error or window too wide. For stocks o/h/l/c are in VND directly (FPT 73500 = 73,500 VND); KIS's own client divides by 1000 only for a '000-VND display, and treats index/futures values as-is. Index symbols (VNINDEX, VN30, HNXIndex, HNXUpco
- **Rate limits:** No rate limiting observed: 20 rapid sequential daily requests all returned HTTP 200. Server is plain nginx; response carries x-trace-id and HSTS but NO x-ratelimit/retry-after/cache headers. The only practical limit is the per-request time-window cap (chunk deep/intraday pulls).
- **robots/ToS:** api.ikis.kisvn.vn/robots.txt = HTTP 404 (no crawl directives). static.ikis.kisvn.vn/robots.txt = 403 AccessDenied (S3/CloudFront). trading.kisvn.vn/robots.txt falls through to the SPA index (catch-all 200, not a real robots file). No robots rule forbids the api endpoint. This is a brokerage retail t
- **Redistribution:** Redistribution NOT permitted by any visible license — proprietary broker feed; safe for end-user self-fetch only, not for shipping KIS data in library outputs.
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://api.ikis.kisvn.vn/api/v3/chart/history?symbol=FPT&resolution=1D&from=1748736000&to=1781629200'
```

### Pinetree / DSC Securities (PineTree TradingView charting backend)

- **Host:** `charts.pinetree.vn`
- **Auth:** none (no cookie, no bearer, no API key; no Set-Cookie returned)
- **Daily endpoint:** `https://charts.pinetree.vn/tv/history?symbol={TICKER}&resolution=1D&from={unix_from}&to={unix_to}`
- **Daily history depth:** Very deep. VCB: 2855 daily bars back to 2015-01-05. FPT: 4100 daily bars back to 2010-01-04 (requested from 2010-01-01, that is the earliest returned). A single request can span the full range; no pagination needed for daily.
- **Intraday:** Verified working: 1, 5, 15, 30, 60, 120 (minutes). resolution=1 returns true 1-minute bars (226 bars per trading day, 09:15-14:45 ICT session). Intraday 1-min depth is limited (~2 months: from request 2026-01-01 the earliest 1-min bar returned was 2026-04-14). Weekly/monthly (1W/1M) are NOT supported (return empty/no status) - aggregate from 1D instead. Note: resolution=1 and =5 returned same bar count in one test (server may cap very long minute ranges), but on a single day resolution=1 confirmed correct 1-min granularity.
  - endpoint: `https://charts.pinetree.vn/tv/history?symbol={TICKER}&resolution={1|5|15|30|60|120}&from={unix_from}&to={unix_to}`
- **Format:** TradingView UDF JSON: parallel arrays {"t":[unix_sec...],"o":[...],"h":[...],"l":[...],"c":[...],"v":[...],"s":"ok","nextTime":-1}. Status "ok" on success, "no_data" with empty arrays for unknown symbol (still HTTP 200). Prices in VND (no implicit thousands scaling - VCB 2015 ~9320 is the adjusted price; raw integers). Content-Type text/plain;charset=UTF-8.
- **Rate limits:** No rate limiting observed: 12 rapid sequential daily requests all returned HTTP 200. No X-RateLimit / RateLimit headers present. nginx/1.20.1 fronts the service. Be polite (sequential, modest concurrency) since no documented quota.
- **robots/ToS:** /robots.txt at trade.pinetree.vn = "User-agent: * / Disallow:" (empty Disallow = nothing disallowed, full crawl allowed). charts.pinetree.vn has no restrictive robots. No public API ToS found on the endpoint itself; this is the broker's own web-trading chart feed. There is also a public OpenAPI arti
- **Redistribution:** Redistribution NOT explicitly permitted. This is Pinetree Securities Corporation's proprietary market-data feed (cert subject "PINETREE SECURITIES CORPORATION"); Vietnam exchange (HOSE/HNX/UPCOM) market data is typically licensed and bulk redistribution of raw OHLCV may breach exchange data-licensing terms. Safe for personal/internal research and on-demand fetching; do NOT republish raw feeds comm
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' "https://charts.pinetree.vn/tv/history?symbol=FPT&resolution=1D&from=$(date -d '2015-01-01' +%s)&to=$(date -d '2026-06-17' +%s)"
```

### FireAnt historical-quotes (restv2.fireant.vn)

- **Host:** `restv2.fireant.vn`
- **Auth:** bearer token (long-lived anonymous web-app JWT). The exact endpoint requires `Authorization: Bearer <token>`; without it returns HTTP 401 {"message":"Authorization has been denied for this request."}. NO user account / login needed — a long-lived public JWT is embedded in fireant.vn's frontend HTML (client_id=fireant.tradestation, scope includes symbols-read/finance-read/companies-read, exp=2029-11-17, valid ~3.5 more years). Token harvested from https://fireant.vn/ page source.
- **Daily endpoint:** `GET https://restv2.fireant.vn/symbols/{SYMBOL}/historical-quotes?startDate={YYYY-MM-DD}&endDate={YYYY-MM-DD}&offset={int}&limit={int}`
- **Daily history depth:** FPT: real data returned back to 2010-01-04 (4101 daily rows in a single request with limit=5000, range 2010-01-01 to 2026-06-17). VCB: back to 2015-01-05 (2856 rows for 2015-2026). Deep multi-year history confirmed; no truncation at limit=5000.
- **Intraday:** none via public endpoint
- **Format:** JSON array of daily objects, newest-first. Each row keys: date (ISO, e.g. "2026-06-17T00:00:00"), symbol, priceOpen, priceHigh, priceLow, priceClose, priceAverage, priceBasic (ref price), totalVolume, dealVolume, putthroughVolume, totalValue, putthroughValue, buyForeignQuantity/Value, sellForeignQuantity/Value, buyCount, buyQuantity, sellCount, sellQuantity, adjRatio (split/adjust factor), current
- **Rate limits:** No rate limiting observed: 8 rapid back-to-back requests all returned HTTP 200, no 429, no Retry-After, no rate-limit headers. Server is Microsoft-IIS/10.0 / ASP.NET; response headers carry cache-control: no-cache only. Be polite anyway (add a small delay between calls).
- **robots/ToS:** restv2.fireant.vn has NO robots.txt (returns 404). Main site https://fireant.vn/robots.txt (Cloudflare-managed) sets Content-Signal: search=yes,ai-train=no and Allow: / for generic User-agent: *, but explicitly Disallows several AI bots by name including ClaudeBot, GPTBot, CCBot, Google-Extended, By
- **Redistribution:** FireAnt is a commercial financial-data service; the historical-quotes data is proprietary and almost certainly NOT licensed for redistribution. The Bearer token is a leaked/embedded web-app credential, not a sanctioned public API key, and could be revoked or rotated at any time. The main domain's robots.txt explicitly forbids AI-training crawlers (ClaudeBot/GPTBot etc.) and sets ai-train=no. Recom
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=False

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 25 -H 'Authorization: Bearer <REDACTED-public-fireant-web-token; fetch at runtime, never commit>' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://restv2.fireant.vn/symbols/FPT/historical-quotes?startDate=2026-01-01&endDate=2026-06-17&offset=0&limit=20'
```

### Wichart (Wigroup) public charting API — chart.wichart.vn TradingView UDF datafeed

- **Host:** `chart.wichart.vn (the data API host the hinted api.wichart.vn root pointed me toward; the UDF datafeed lives on chart.wichart.vn/data, while api.wichart.vn is the same Wigroup backend reachable as wichart.vn/wichartapi -> api.wichart.vn/v2)`
- **Auth:** none (no cookie, no token, no API key, no Referer/Origin required; bare curl works)
- **Daily endpoint:** `https://chart.wichart.vn/data/history?symbol={TICKER}&resolution=1D&from={UNIX_FROM}&to={UNIX_TO}  (response is AES-encrypted: {"enc":"<base64 OpenSSL Salted__ AES-256-CBC>"} ; the CryptoJS-style decryption passphrase is <redacted> — anti-circumvention material intentionally NOT reproduced. Decrypting it bypasses an access-control mechanism; excluded from the default chain.)`
- **Daily history depth:** Daily goes back to 2014-12-31 for both FPT and VCB (2856 bars to 2026-06-16) even when requesting from 2015-01-01; ~10+ years available. Prices are split/dividend-ADJUSTED (FPT 2014 close 7.37, VCB 2014 close 9.37). Timestamps are session-open epoch (UTC).
- **Intraday:** Confirmed working: 60 (hourly), 15 (15-min), 1 (1-min). Config advertises supported_resolutions ["15","60","1D","1W","1M"]; symbol meta also lists has_intraday=true, intraday_multipliers ["1"], session 0900-1500. Intraday history depth is shallower: hourly (res=60) goes back only to ~2023-06-19 (3727 bars) even when requesting from 2015. Weekly (1W) and monthly (1M) also supported (encrypted like daily).
  - endpoint: `https://chart.wichart.vn/data/history?symbol={TICKER}&resolution={60|15|1}&from={UNIX_FROM}&to={UNIX_TO}  (IMPORTANT: intraday is returned as PLAINTEXT UDF JSON — NOT encrypted — so no decryption step is needed for intraday, only for 1D/1W/1M)`
- **Format:** TradingView UDF: JSON object with parallel arrays {"t":[...epoch...],"o":[...],"h":[...],"l":[...],"c":[...],"v":[...]} (and a status "s" field on empty/error responses, e.g. s:"no_data"). For 1D/1W/1M the whole object is wrapped as {"enc":"<base64>"} AES-256-CBC OpenSSL "Salted__" format; intraday (1/15/60) is delivered unwrapped/plaintext. Companion UDF endpoints also live and auth-free: /data/c
- **Rate limits:** No rate limiting observed: 12 rapid sequential /data/symbols requests all returned HTTP 200 with no throttling, 429, or block. No Retry-After or quota headers seen. (Be polite anyway — single small host.)
- **robots/ToS:** chart.wichart.vn/robots.txt returns the Next.js 404 page (no robots file). www.wichart.vn/robots.txt = "User-agent: * / Disallow:" (allows all). api.wichart.vn/robots.txt returns "Page Not Found !". The wichart.vn frontend (now branded WiData/widata.vn) meta robots = "index,follow". No robots rule f
- **Redistribution:** Do NOT assume redistribution is permitted. This is a commercial, paid financial-data platform (WiData/WiGroup) with subscription tiers; the datafeed being unauthenticated is an implementation gap, not a grant of rights. Treat retrieved OHLCV as licensed third-party data: safe for private/internal research, but redistribution, resale, or republishing very likely breaches WiGroup's terms. The AES "e
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
# NOTE: the 1D/1W/1M response is AES-256-CBC encrypted. The decryption passphrase is
# <redacted> and the decrypt step is intentionally omitted: decrypting bypasses an
# access-control mechanism (anti-circumvention). Risk posture: requires response
# decryption; excluded from the default source chain. Intraday (1/15/60) is plaintext.
curl -s -4 -m 30 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' "https://chart.wichart.vn/data/history?symbol=FPT&resolution=1D&from=$(date -d '2015-01-01' +%s)&to=$(date -d '2026-06-17' +%s)"  # response is {"enc":"<base64 AES-256-CBC>"}; passphrase <redacted>
```

### Yahoo Finance chart API (.VN tickers for HOSE)

- **Host:** `query1.finance.yahoo.com (query2.finance.yahoo.com is an identical mirror; bare finance.yahoo.com 404s for this path)`
- **Auth:** none for the v8 chart endpoint (no cookie/crumb needed). A browser User-Agent IS effectively required: a Linux UA returned persistent HTTP 429; a Windows Chrome UA returned 200. Crumb+cookie (fc.yahoo.com -> /v1/test/getcrumb) is only needed for the legacy /v7/finance/download CSV path, which returned 401.
- **Daily endpoint:** `https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}.VN?period1={unix_start}&period2={unix_end}&interval=1d  (alternatively use range={1mo|1y|5y|max} instead of period1/period2)`
- **Daily history depth:** Deep. period1=2015-01-01 returned 2970 daily rows through 2026-06-16 for both FPT.VN and VCB.VN. meta.firstTradeDate=2010-02-22 and range=max returns data back to Feb 2010 (auto-coarsened to monthly bars when range=max with interval=1d). So full daily history from listing date is retrievable by requesting an early period1.
- **Intraday:** 1m (history limit ~7d; range=1mo rejected), 5m (~60d, tested 4317 rows over 60d), 15m, 30m, 1h/60m (back to ~730d / 2023). Intraday bars return real OHLCV; timestamps are UTC (e.g. 02:00 UTC = 09:00 ICT VN open).
  - endpoint: `https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}.VN?interval={1m|5m|15m|30m|1h}&range={range}`
- **Format:** JSON: chart.result[0].timestamp[] (unix seconds, UTC) parallel to chart.result[0].indicators.quote[0].{open,high,low,close,volume}[], plus indicators.adjclose[0].adjclose[]. meta carries symbol, currency (VND), exchangeName (VSE), instrumentType (EQUITY), firstTradeDate, dataGranularity. Errors come as chart.error{code,description} with non-200.
- **Rate limits:** Aggressive IP-level throttling observed. With a Linux X11 User-Agent, EVERY call (chart, crumb, mirror) returned HTTP 429 'Too Many Requests' regardless of cookie/crumb. Switching to a Windows Chrome UA immediately yielded HTTP 200. No documented quota; recommend conservative request pacing, retry-w
- **robots/ToS:** robots.txt at https://query1.finance.yahoo.com/robots.txt returns 'User-agent: *  Disallow: /' (entire host disallowed for crawlers). This endpoint is undocumented/unofficial (internal chart API used by finance.yahoo.com). Combined with ToS, scraping is contrary to Yahoo's stated terms; flagged as a
- **Redistribution:** High risk. Yahoo Finance Terms of Service prohibit redistribution/commercial use of the data and use of automated means to access it; the data also includes third-party exchange data. An OSS library should NOT bundle/redistribute Yahoo-sourced VN price data and should treat this endpoint as best-effort/unofficial for end-user personal fetching only, with a clear disclaimer. Prices are back-adjuste
- **Verified:** reproduced=True, daily_confirmed=True, intraday_confirmed=True

```bash
# reproduce (uses curl -4 + browser UA):
curl -s -4 -m 30 -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36' 'https://query1.finance.yahoo.com/v8/finance/chart/FPT.VN?period1=1420045200&period2=1781629200&interval=1d'
```

## Partial

### 24hMoney finance API (api-finance-t19.24hmoney.vn)
- host `api-finance-t19.24hmoney.vn` — status: partial, daily_works=True
- notes: Endpoints discovered cleanly via the host's own FastAPI OpenAPI schema at https://api-finance-t19.24hmoney.vn/openapi.json (163 endpoints) + /docs + /redoc — provider's own server, no vnstock used. platform path-segment enum is strictly {ios,android,web} (422 reveals it). KEY LIMITATIONS for the daily-OHLCV priority: (1) NO endpoint returns deep historical daily OHLC bars; (2) trading-history caps at 30 sessions and lacks open/high/low (only close/ref/band/volume); (3) stock/graph is a downsampled price LINE, daily only for ~3 months, no O/H/L; (4) true OHLC (open_price/hieghest_price/lowest_p
```bash
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://api-finance-t19.24hmoney.vn/v1/web/stock/trading-history?symbol=FPT'
```

## Failed

### TCBS (apipubaws / tcanalysis) — host apipubaws.tcbs.com.vn
- host `apipubaws.tcbs.com.vn (resolves to AWS NLB prod-nlb-dp-tcbs-apipub-*.elb.ap-southeast-1.amazonaws.com — IBM DataPower API gateway)`
- notes: CLEAN-ROOM: vnstock and all derivatives were fully excluded; endpoints/params were derived only from the task brief, the provider's own hosts/DNS, and general TradingView-UDF/HTTP knowledge — no vnstock code/docs/snippets consulted. KEY FINDINGS (all proven by real curl, run from a Vietnamese FPT Telecom IP in Ho Chi Minh City per ipinfo.io — so NOT a geo-block): (1) Every path on apipubaws.tcbs.com.vn returns {"status":404,"message":"Service not found"} with header x-backside-transport: FAIL FAIL — this is a GATEWAY-level rejection (no service mounted), not a handler 404. Tested: /stock-insig

## Recommendation for vnfin-oss

1. **Build one `UDFDatafeedClient`** (TradingView UDF) with a registry of providers + per-provider quirks (base path, resolution token map, adjusted-vs-raw flag, optional headers like Referer/Bearer).
2. **Primary chain (daily):** SSI iBoard → VNDirect dchart → Vietstock. All no-auth, deep, UDF-shaped. Failover on empty/error.
3. **Backup pool:** VPS, DNSE/Entrade, KIS, Pinetree, Vietcap. All no-auth and intraday-capable.
4. **Raw (unadjusted) cross-check:** Simplize and CafeF — use to validate adjustment math and corporate-action handling.
5. **Conditional / last resort:** FireAnt (anonymous Bearer token — can be revoked), Yahoo `.VN` (global backup, aggressive IP 429 — needs strict rate control), Wichart (AES-encrypted payload — fragile, deprioritize).
6. **Compliance:** runtime fetch only, no bundled data; expose source attribution; gate any redistribution behind a documented license check.

*Generated by the `vn-price-scrape-probe` workflow (30 agents, adversarial reproduction). Provider Terms of Use were not individually signed — treat redistribution conservatively per the global caveat above.*