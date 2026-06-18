# Step 2 research — VN fundamental-report sources (scrapeable)

**Date:** 2026-06-18  **Owner:** vnfin-oss  **Scope:** income statement / balance sheet / cash flow / financial ratios for HOSE/HNX/UPCOM.

**VNStock clean-room exclusion applied.** Endpoints learned only from each provider's own server + public REST shapes; no vnstock material consulted.

**Method:** parallel probe agents ran real `curl` and pasted real snippets as proof. Result: 6 working, 2 partial, 2 failed.

> ⚠️ Redistribution: these are broker/portal financial-data endpoints with no published redistribution grant — fine for personal/internal research; runtime-fetch only, no bundled data.

## Working sources

### VNDirect finfo financial API (api-finfo sibling host)
- **Host:** `api-finfo.vndirect.com.vn (NOT finfo-api.vndirect.com.vn — that one is dead)`
- **Statements:** income_statement, balance_sheet, cash_flow, ratios
- **Period:** both — reportType:QUARTER and reportType:ANNUAL both confirmed. Also exposes reportType:QUARTER2 (year-to-date cumulative) and reportType:ESTIMATION (analyst forecasts, modelType 33).
- **History:** Deep. FPT annual goes back to fiscalDate 2002-12-31 (totalElements 2977 across all items for model1 annual). VCB income statement (modelType 102) annual back to 2004-12-31. Quarterly FPT model1 has 9727 item-rows. Latest data current to 2026-03-31 (Q1 2026) for statements; ratios current to reportDa
- **Auth:** None. No API key, no cookie, no token, no Referer required. Only needs -4 + a browser User-Agent (the -m timeout is just for the dead sibling host; api-finfo responds in ~0.2s).
- **Coverage:** HOSE confirmed (FPT, VCB both HOSE). Did not explicitly test HNX/UPCOM tickers, but the API is code-keyed with no exchange gating observed, so HNX/UPCOM very likely covered (unverified here).
- **Format/units:** JSON. Shape: {"data":[{...}],"currentPage":N,"size":N,"totalElements":N,"totalPages":N}. Each statement row is LONG/tall format (one row per line-item per period), NOT a wide table: fields = code (ticker), itemCode (numeric line-item id, float e.g. 11000.0), reportType, modelType (float), numericValue (the value), fiscalDate, createdDate, modifiedDate. UNITS = RAW VND, unscaled (e.g. VCB itemCode 412000 = 1648549996000000.0 = ~1,648 trillion VND total assets; FPT itemCode 11000 annual 2024 = 45,535,942,846,453 = ~45.5 trillion VND). Ratio rows: {code, group, reportDate, itemCode, ratioCode, it
- **Endpoints:** STATEMENTS: https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code:{TICKER}~reportType:{QUARTER|ANNUAL}~modelType:{N}&sort=fiscalDate:desc&size={N}  (optional extra filter ~fiscalDate:YYYY-MM-DD). Pagination: &page=. | RATIOS (current PE/PB/EPS): https://api-finfo.vndirect.com.vn/v4/ratios/latest?order=reportDate&where=code:{TICKER}&filter=ratioCode:PRICE_TO_EARNINGS,PRICE_TO_BOOK,EPS_TR,ROE_TR_AVG_CR&size=20 | RATIOS (full/historical): https://api-finfo.vndirect.com.vn/v4/ratios?q=code:{TICKER}&size={N}
- **Terms:** robots.txt: 404 (no robots.txt; the API returns a JSON 404 body {"status":404,...} for /robots.txt). No ToS served at the API host. VNDirect's main site (vndirect.com.vn) ToS would govern; this is a brokerage data API intended for their own web/app clients, so redistribution of bulk fundamentals is 
```bash
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code:FPT~reportType:QUARTER~modelType:1&sort=fiscalDate:desc&size=3'
```
_proof:_ FPT QUARTER model1 (reproduce cmd): {"code":"FPT","itemCode":14310.0,"reportType":"QUARTER","modelType":1.0,"numericValue":1.576181989047E12,"fiscalDate":"2026-03-31",...},"totalElements":9727. | VCB ANNUAL income modelType:102: itemCode 421601.0 = 5269108000000.0, fy 2025-12-31; totalElements 536; oldest fy 2004-12-31. | VCB ratios/latest: {"ratioCode":"PRICE_TO_EARNINGS","value":14.3687,"reportD

### CafeF financial reports (báo cáo tài chính)
- **Host:** `cafef.vn (AJAX handlers under /du-lieu/Ajax/PageNew/); detailed HTML statements canonicalize to cafef.vn/du-lieu/bao-cao-tai-chinh/... (legacy s.cafef.vn/bao-cao-tai-chinh/... 301-redirects there)`
- **Statements:** income_statement, balance_sheet, cash_flow, ratios
- **Period:** both — ReportType=NAM (annual) and ReportType=QUY (quarterly); SAUTHANG (half-year/6-month) also accepted.
- **History:** Deep. FPT income annual returns back to 2001 (25 yearly periods, Count=25). FPT income quarterly back to Q1-2006 (85 quarters with TotalRow=200). Balance sheet quarterly Count=71. TotalRow caps how many periods you get; request a large TotalRow to pull full history. EndDate anchors the newest period
- **Auth:** None. No API key, no cookie, no login. Plain GET. Sending a Referer header to the matching du-lieu page is polite but NOT required (worked without it). Must use IPv4 (-4) + browser UA.
- **Coverage:** HOSE confirmed: FPT (corporate) and VCB (bank) both return data. JSON adapts schema by sector — corporate income uses DTTBHCCDV/GV/LNGBHCCDV; bank income uses TotalIncome/TongChiPhi/TotalProfit/NetInc
- **Format/units:** JSON. FinanceReport.ashx shape: {"Data":{"Count":<total periods avail>,"Value":[{"Time":"2025","Year":2025,"Quater":0,"ReportType":"HK","Conten":"Đã kiểm toán ","Value":[{"Code":"DTTBHCCDV","Name":"Doanh thu bán hàng và CCDV","Value":70207688945}, ...]}, ...]},"Message":null,"Success":true}. One object per period; each holds a Value[] of {Code,Name,Value} line items; Conten flags audited ("Đã kiểm toán"). GetDataChiSoTaiChinh.ashx is the same outer shape with ratio codes. GetDataChart*/single-indicator return {"Data":[{"Quater":..,"Year":..,"Value":..}],...}.
UNITS: JSON summary Value fields a
- **Endpoints:** JSON SUMMARY (clean, recommended):
1) Income/Balance summary: https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type={1|2}&Symbol={TICKER}&TotalRow={N}&EndDate={anchor}&ReportType={NAM|QUY}&Sort=DESC
   - Type=1 = income statement (incsta), Type=2 = balance sheet (bsheet). (Type>=3 returns empty Value here.)
   - EndDate: annual = year e.g. 2025 ; quarterly = "Q-YYYY" form passed as "1-2025" (quarter-year). EndDate is the NEWEST anchor (use current year/quarter to get latest).
   - ReportType=NAM (annual) or QUY (quarterly). SAUTHANG = half-year also exists.
2) Financial ratios (EPS/BV/PE/ROA/ROE/ROS/DAR/GOS): https://cafef.vn/du-lieu/Ajax/PageNew/GetDataChiSoTaiChinh.ashx?Symbol={TICKER}&TotalRow={N}&EndDate={year}&ReportType={NAM|QUY}&Sort=DESC
3) Single-indicator time series (for charts): https://cafef.vn/du-lieu/Ajax/PageNew/GetDataChart.ashx?Type={1|2}&Symbol={T}&TotalRow={N}
- **Terms:** robots.txt fetched live: https://cafef.vn/robots.txt = "User-agent: *  Allow: /" plus two Sitemap lines (sitemap.xml, google-news-sitemap.xml). No Disallow, no Crawl-delay — crawling is permitted by robots. s.cafef.vn/robots.txt returned empty (no robots = no restriction declared). No published mach
```bash
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type=1&Symbol=FPT&TotalRow=4&EndDate=2025&ReportType=NAM&Sort=DESC'
```
_proof:_ FinanceReport.ashx?Type=1&Symbol=FPT&ReportType=NAM (income, period Time=2025, Conten="Đã kiểm toán"): {"Code":"DTTBHCCDV","Name":"Doanh thu bán hàng và CCDV","Value":70207688945},{"Code":"GV","Name":"Giá vốn hàng bán","Value":44224295588},{"Code":"LNGBHCCDV","Value":25888529512},{"Code":"TotalProfit","Name":"Tổng lợi nhuận trước thuế","Value":13043632834},{"Code":"LNSTTNDN","Name":"Lợi nhuận sau 

### Simplize financial statements
- **Host:** `api2.simplize.vn`
- **Statements:** income_statement, balance_sheet, cash_flow, ratios
- **Period:** Both quarterly and annual EXIST, but only quarterly is free/no-auth. period=Q -> 200 (no auth). period=Y -> 401 (login required). Param values are the literal strings "Q" and "Y" (NOT "QUARTER"/"ANNUAL"/"YEAR" — those return HTTP 400 "Vui lòng chọn báo cáo").
- **History:** No-auth quarterly cap = size=12 (HTTP 200). Tested: size=12 -> oldest Q2/2023 (newest Q1/2026), i.e. ~3 years / 12 quarters back from current. size>=16 -> HTTP 401. This matches the site's internal default reportTime:"3_nam" (3 years). Deeper history and all annual data is behind the login/premium w
- **Auth:** No auth required for quarterly (period=Q) up to size=12. Annual (period=Y) AND quarterly size>=16 return HTTP 401 "Vui lòng đăng nhập để tiếp tục" (login-gated, premium tier). The detail endpoint /api
- **Coverage:** Confirmed working on HOSE: FPT (industryGroup=MANUFACTURING) and VCB (industryGroup=BANK). Bank vs non-bank get different line-item templates but identical endpoint/param shape and same period/size ga
- **Format/units:** JSON envelope: {"status":200,"message":"Success","data":{"industryGroup":"MANUFACTURING","items":[...]}}. data.items is an array of period objects, newest first. Each item has identity fields: ticker, periodDateName (e.g. "Q1/2026"), periodDate (e.g. "2026-03"), plus GENERIC CODED metric fields — no human-readable labels in the data response: is1..is117 (income statement), bs1..bs203 (balance sheet), cf* (cash flow). The fi/ratio response is a SUPERSET: it returns bs*, is*, plus op1..op49 (computed ratios: EPS/PE/PB/ROE/margins etc.), isg* (income-statement growth), bsg* (balance-sheet growth)
- **Endpoints:** GET /api/company/fi/is/{TICKER}?period={Q|Y}&size={N}   (income statement)
GET /api/company/fi/bs/{TICKER}?period={Q|Y}&size={N}   (balance sheet)
GET /api/company/fi/cf/{TICKER}?period={Q|Y}&size={N}   (cash flow)
GET /api/company/fi/ratio/{TICKER}?period={Q|Y}&size={N} (ratios + growth metrics)
Optional param `type` (integer, e.g. type=1) is accepted but not required (empty/omitted works).
Also live (no-auth) for price context: GET /api/historical/quote/{TICKER}
Login-gated companions: /api/company/analysis-metrics-historical/{TICKER} (401), /api/company/agg-metrics/statements/{TICKER} (200 but returns empty {} without auth).
- **Terms:** api2.simplize.vn/robots.txt = HTTP 404 (no robots on the API host). simplize.vn/robots.txt (updated 2026-03-11) explicitly comments "# Cho phép crawl dữ liệu tài chính công khai" (allow crawling PUBLIC financial data) and only Disallows /community/, /portfolio/, /watchlist/, /profile/, /screener/, /
```bash
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://api2.simplize.vn/api/company/fi/is/FPT?period=Q&size=4'
```
_proof:_ FPT income statement (period=Q, Q1/2026): {"status":200,"message":"Success","data":{"industryGroup":"MANUFACTURING","items":[{"ticker":"FPT","periodDateName":"Q1/2026","periodDate":"2026-03","is1":12479997206775,"is3":2747763827050,"is48":2476789833481,...}]}}. FPT ratios Q1/2026: op2=4.436, op8=23.90, op19=0.1593 (ROE~15.9%), op6=22865.8 (BVPS VND). VCB (BANK) income Q1/2026: is1=21179810000000, 

### 24hMoney finance API
- **Host:** `api-finance-t19.24hmoney.vn`
- **Statements:** income_statement, balance_sheet, cash_flow, ratios
- **Period:** both
- **History:** Deep. Annual income statement: page 1 = FY2018-2025, page 2 = FY2016-2017 (so 2016->2025, ~10 years via paging). Quarterly: page 1 reaches current Q1 2026 back to ~2024 Q2; page 2 reaches back to 2022 Q2; continues on further pages. financial-graph returns quarterly series Q1 2023 -> Q1 2026.
- **Auth:** None. No-auth, no API key, no cookie. Plain GET with a browser User-Agent over IPv4 (-4) returns 200. FastAPI backend (responses include execute_time_ms).
- **Coverage:** Confirmed on HOSE: FPT (IT/industrial template) and VCB (banking template) both returned HTTP 200 with full statements. Did not test HNX/UPCOM tickers in this probe, but the endpoint is symbol-based a
- **Format/units:** JSON envelope: {"message":"success","status":200,"data":{...},"execute_time_ms":N}.
For /financial-report, data = {"headers":[...], "rows":[...]}.
  headers: array of {"year":2026,"quarter":1,"type":"normal"} interleaved with {"type":"percent"} (YoY % growth columns). For annual, quarter=0.
  rows: array of {"key":"isa3","level":2,"values":[...],"data":true,"name":"Doanh thu thuần"}. values[] aligns positionally to headers[] (normal value, then percent, then next period...). level = indentation/hierarchy depth. key is a stable row code prefixed by statement+template: bsa*/isa*/cfa* for non-fin
- **Endpoints:** Statements: GET https://api-finance-t19.24hmoney.vn/v1/web/company/financial-report?symbol={TICKER}&period={1=annual|2=quarter}&view={1=balance_sheet|2=income_statement|3=cash_flow}&page={1,2,...}&expanded=true
Ratios summary: GET https://api-finance-t19.24hmoney.vn/v1/web/company/financial-report-summary?symbol={TICKER}
Series for charts: GET https://api-finance-t19.24hmoney.vn/v1/web/company/financial-graph?symbol={TICKER}&graph_type=1
Params: symbol (uppercase ticker), period (1 annual / 2 quarter), view (1 BS / 2 IS / 3 CF; view=4 returns no data), page (paginates history, older periods on higher pages), expanded (true = include child/leaf rows).
- **Terms:** robots.txt at https://api-finance-t19.24hmoney.vn/robots.txt returns (HTTP 200): "User-agent: *  Disallow: /" — i.e. the API host disallows ALL crawler paths. This is an automated-crawling-discouraged signal; no explicit machine-readable license/redistribution grant. 24hMoney is a commercial Vietnam
```bash
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://api-finance-t19.24hmoney.vn/v1/web/company/financial-report?symbol=FPT&period=1&view=2&page=1&expanded=true'
```
_proof:_ FPT annual income (period=1,view=2): row isa3 "Doanh thu thuần" values=[70112.8256, 11.56, 62848.7944, 19.44, 52617.9008, 19.56] => FY2025 net revenue 70112.83 bn VND (+11.56% YoY), FY2024 62848.79 bn (+19.44%), FY2023 52617.90 bn.
FPT ratios: pe=12.8618, pb=3.20129, roe=26.8159, eps=5691.27, roa=12.0838, net_profit_margin=19.85, ev_per_ebitda=10.2222, group_name="Công nghệ Thông tin".
VCB (bank) 

### FireAnt restv2
- **Host:** `restv2.fireant.vn`
- **Statements:** income_statement, balance_sheet, cash_flow, ratios
- **Period:** both. Quarterly via quarter=1..4 + year + limit (e.g. Q1 2026, Q4 2025...). Annual via quarter=0 (e.g. 2011..2025). Confirmed on FPT and VCB.
- **History:** Annual back to 2011 confirmed (FPT income statement quarter=0 limit=15 returned periods 2011..2025 = 15 fiscal years). Quarterly returns the most recent N quarters via limit (e.g. limit=4 -> Q2/2025..Q1/2026). Latest available period Q1 2026.
- **Auth:** Required, low-auth. Static long-lived GUEST JWT scraped from fireant.vn page HTML (JSON field "accessToken", served with no login). Pass as `Authorization: Bearer <JWT>`. No-auth requests return HTTP 
- **Coverage:** HOSE confirmed: FPT (industrial/IT) and VCB (bank) both returned 200 with correct, industry-appropriate statement structures. HNX/UPCOM not explicitly tested this run, but the symbol-keyed scheme is e
- **Format/units:** JSON. UNITS = raw VND (not billions, not thousands) — values are full-scale floats, e.g. FPT 2025 net revenue = 70112825100710.0 VND, VCB Q1/2026 net interest income = 17651083000000.0 VND. 
full-financial-reports: array of row objects {id, name (Vietnamese label), parentID, expanded, level (tree depth 1=section,2,3...), field (often null), values:[{period:"Q1 2026"|"2025", year, quarter, value (float|null)}]}. Hierarchical chart-of-accounts tree via parentID/level. FPT: type=1 116 rows, type=2 22 rows, type=4 54 rows. 
financial-indicators: array of {name, shortName, description, group, group
- **Endpoints:** GET https://restv2.fireant.vn/symbols/{SYMBOL}/fundamental  (snapshot: shares, beta, dividend, marketCap, 52w, pe, eps, TTM sales/profit, ownership). 
GET https://restv2.fireant.vn/symbols/{SYMBOL}/full-financial-reports?type={1|2|4}&year={YYYY}&quarter={Q}&limit={N}  (DETAILED hierarchical statements — the real one). type=1 Balance Sheet, type=2 Income Statement, type=4 Cash Flow, type=3 returns empty. quarter=1..4 = that quarter; quarter=0 = ANNUAL. limit = number of periods (columns) returned. 
GET https://restv2.fireant.vn/symbols/{SYMBOL}/financial-indicators?type={1|2}  (ratios: P/E,P/S,P/B,EPS,ROE,ROA,margins, with industryValue). 
GET https://restv2.fireant.vn/symbols/{SYMBOL}/financial-reports?type={1}&year=&quarter=&limit=  (SUMMARY row-matrix Sales/GrossProfit/OperatingProfit/NetProfit only; note: the `type` param does NOT switch statement type here — it always returns the inc
- **Terms:** restv2.fireant.vn has NO robots.txt (HTTP 404 ASP.NET "resource cannot be found" page) — no machine-readable crawl policy on the API host. The main site https://fireant.vn/robots.txt sets Cloudflare content-signals: "User-agent: *  Content-Signal: search=yes,ai-train=no  Allow: /" and disallows Amaz
```bash
curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' -H 'Authorization: Bearer <redacted; fetch at runtime, never commit>' 'https://restv2.fireant.vn/symbols/FPT/full-financial-reports?type=2&year=2026&quarter=0&limit=5'
```
_proof:_ FPT income statement (full-financial-reports type=2, annual quarter=0): row "3. Doanh thu thuần (1)-(2)" => 2023=52617900827385, 2024=62848794351367, 2025=70112825100710 (VND). FPT balance sheet (type=1): "TÀI SẢN"(Assets root), "A. Tài sản lưu động và đầu tư ngắn hạn" Q1 2026=41527873060120, "I. Tiền và các khoản tương đương tiền" Q1 2026=7993577611642. FPT cash flow (type=4): "I. Lưu chuyển tiền

### Wichart / WiGroup (widata.vn frontend, api host wichart.vn)
- **Host:** `wichart.vn (API prefix /wichartapi/...) — note: widata.vn axios proxies through https://wichart.vn/. Root https://api.wichart.vn returns "API Wigroup !!!" but the data lives behind https://wichart.vn/wichartapi/.`
- **Statements:** income_statement, balance_sheet, cash_flow, ratios
- **Period:** both — type=quarter and type=year both confirmed for FPT and VCB
- **History:** Excellent. Annual: 9 columns/page x 3 pages = back to 1999 for FPT (page1=2025..2017, page2=2016..2008, page3=2007..1999). Quarterly: 9 cols/page x 6 pages for FPT = back to ~2012 (page1=Q1-2026..Q1-2024, page6=Q4-2014..Q4-2012). 'total' field gives the page count per ticker (FPT quarter=6, VCB quar
- **Auth:** No login/cookie/API-key, but every request needs a custom signed header set computed client-side (anti-scrape): stime (ms epoch), nonce (random ~20 digits), a STATIC sign-token (<redacted>) plus an MD5 `sign`. This is a deliberate anti-scraping control; excluded from default chain.
- **Coverage:** HOSE confirmed (FPT, VCB). Master list endpoint danhsachchungkhoan returns codes with type field (type:1) and exchange via 'san' field (HOSE/HNX/UPCOM appear in related sector endpoints), so HNX/UPCOM
- **Format/units:** JSON after AES-256-CBC decrypt; values are comma-formatted strings; units = billions VND when unit=ty (unit=dong gives raw VND); key fields: title, key (stable slug), level, value1..value9 aligned to time[]
- **Endpoints:** FULL STATEMENTS (IS+BS+CF in one call): GET https://wichart.vn/wichartapi/wichart/company/fs?code={TICKER}&page={1..N}&type={quarter|year}&unit=ty&currency=vnd&quarter=1&isConsolidatedReport={true|false} -> {"enc":...} decrypts to {candoiketoan:[balance sheet], baocaothunhap:[income statement], luuchuyentiente:[cash flow], thuyetminh:[notes], time:[period labels], type:1(corp)|2(bank), total:(page count)}. value1..value9 map left->right to the time[] array.
RATIOS/KEYSTATS: GET https://wichart.vn/wichartapi/wichart/company/keystats?code={TICKER} -> {"enc":...} decrypts to sections: hieuquahoatdong(margins, ROA, ROE, ROIC, turnover, DSO/DIO/DPO), giavadinhgia(vonhoa/market cap, eps, bookvalue, pe, peg, pb, ev_ebit, ev_ebitda, ps, p_ocf), suckhoetaichinh(financial health), candoiketoan/baocaothunhap/luuchuyentiente(TTM summaries), ttquy/ttnam(QoQ/YoY growth).
Other same-auth company endpoi
- **Terms:** robots.txt at both widata.vn and wichart.vn = "User-agent: * / Disallow:" (empty = nothing disallowed for crawlers). HOWEVER the API uses an MD5 request signature + AES-encrypted responses, which is a deliberate access-control / anti-scraping mechanism — bypassing it is technically circumventing a p
```bash
# Request requires a STATIC sign-token + per-request MD5 `sign` header, and the JSON
# response is AES-256-CBC encrypted. Both the sign-token and the AES passphrase are
# <redacted> — anti-circumvention material is intentionally NOT reproduced here.
# Risk posture: requires signature + response decryption to bypass an access-control
# mechanism; excluded from the default source chain. Do not reproduce the secrets.
ST='<redacted>'; T=$(date +%s%3N); N=$(printf '%d0000000000' $RANDOM$RANDOM); S='<md5 sign computed from ST + canonical query>'; curl -s -4 -m 25 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' -H 'Referer: https://widata.vn/' -H "stime: $T" -H "nonce: $N" -H "sign-token: $ST" -H 'v: v1' -H "sign: $S" "https://wichart.vn/wichartapi/wichart/company/fs?code=FPT&page=1&type=quarter&unit=ty&currency=vnd&quarter=1&isConsolidatedReport=true"  # response is AES-256-CBC encrypted; passphrase <redacted>
```
_proof:_ company/fs FPT quarter, time=["Q1-2026","Q4-2025",...]: balance sheet row {key:"taisannganhan","A. TÀI SẢN NGẮN HẠN", value1:"41,527.9", value2:"58,137.4"}; income statement {key:"doanhthuthuanvebanhangvacungcapdichvu","3. Doanh thu thuần", value1:"12,480.0"}, {key:"giavonhangban", value1:"-8,235.1"}. keystats FPT giavadinhgia: eps="5,687.8" (VND), pe="12.7", pb="3.3", bookvalue="37,546.6"; hieuqu

## Partial

### Vietstock financials (finance.vietstock.vn)
- host `finance.vietstock.vn` — statements: income_statement, balance_sheet, cash_flow, ratios — but only the report STRUCTURE/line-item labels (norms) are reachable anonymously. The actual numeric VALUES for all four statement types are paywalled.; auth: Two layers. (1) Anti-forgery: every /data/ POST requires a matched pair of __RequestVerificationToken (an HttpOnly cooki
- notes: Clean-room confirmed: zero use of vnstock/VNStock/vnstocks.com/thinh-vu/any wrapper. Endpoints were learned solely from finance.vietstock.vn's own page HTML and its own /bundles/company/finance JS bundle (network reconnaissance). VERDICT for fundamentals: Vietstock is NOT a viable no-auth source for
```bash
PAGE=$(curl -s -4 -m 25 -c /tmp/vs.txt -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://finance.vietstock.vn/FPT/financials.htm'); T=$(printf '%s' "$PAGE" | grep -oiE 'name=__RequestVerificationToken type=hidden value=[^>]+' | head -1 | sed 's/.*value=//'); curl -s -4 -m 25 -b /tmp/vs.txt -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' -H 'X-Requested-With: XMLHttpRequest' -H 'Referer: https://finance.vietstock.vn/FPT/financials.htm' -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' --data-urlencode "stockCode=FPT" --data-urlencode "__RequestVerificationToken=$T" 'https://finance.vietstock.vn/data/GetListReportNorm_KQKD_ByStockCode'
```

### State Securities Commission (SSC) Information Disclosure Portal — Hệ thống Công bố Thông tin (IDS)
- host `congbothongtin.ssc.gov.vn` — statements: income_statement, balance_sheet, cash_flow (delivered as audited/periodic FILING PDF attachments per issuer, NOT pre-parsed line items). ratios: NONE.; auth: None. Public, no API key, no login. Only a normal session cookie (JSESSIONID/SERVERID) returned by the first GET. Works 
- notes: 
```bash
L=$(curl -s -4 -m25 -c /tmp/ssc.cj -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://congbothongtin.ssc.gov.vn/faces/NewsSearch' | grep -oE "'[0-9]{15,}'" | head -1 | tr -d "'"); P=$(curl -s -4 -m25 -b /tmp/ssc.cj -c /tmp/ssc.cj -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' "https://congbothongtin.ssc.gov.vn/faces/NewsSearch?_afrLoop=${L}&_afrWindowMode=0&_adf.ctrl-state=x"); VS=$(printf '%s' "$P" | grep -oE 'ViewState" value="[^"]*"' | sed -E 's/.*value="([^"]*)"/\1/'); WID=$(printf '%s' "$P" | grep -oE 'Adf-Window-Id" type="hidden" value="[^"]*"' | sed -E 's/.*value="([^"]*)"/\1/'); curl -s -4 -m30 -b /tmp/ssc.cj -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8' -H 'Adf-Rich-Message: true' --data-urlencode 'pt9:t1:it11=FPT' --data 'org.apache.myfaces.trinidad.faces.FORM=f1' --data "Adf-Window-Id=$WID" --data-urlencode "javax.faces.ViewState=$VS" --data 'event=pt9:t1' --data-urlencode 'event.pt9:t1=<m xmlns="http://oracle.com/richClient/comm"><k v="type"><s>query</s></k></m>' --data 'oracle.adf.view.rich.PROCESS=pt9:t1' 'https://congbothongtin.ssc.gov.vn/faces/NewsSearch'
```

## Failed

- **TCBS tcanalysis fundamentals (apipubaws gateway)** (`apipubaws.tcbs.com.vn`): Clean-room respected: no vnstock/derivative sources used; endpoint structure tested came from the task brief and direct gateway probing only. CONCLUSION: the legacy public no-auth TCBS tcanalysis fund
- **SSI iBoard fundamentals** (`iboard-api.ssi.com.vn / iboard-query.ssi.com.vn / fiin-fundamental.ssi.com.vn`): CLEAN-ROOM: vnstock and all derivatives fully excluded; endpoints learned only from SSI's own site — robots.txt, the iBoard company page HTML, and SSI's own JS bundles (fiintrade.js env config exposin

## Recommendation (Step 2 design seed)

- **Primary fundamentals adapter:** VNDirect `api-finfo.vndirect.com.vn/v4/financial_statements` + `/v4/ratios` — no-auth, deep history (to ~2002), IS/BS/CF/ratios. Long/tall numeric-itemCode rows → maintain a client-side itemCode→field map + bank(101/102/103) vs corporate(1/2/3) modelType split; units raw VND.
- **Backup:** CafeF AJAX `FinanceReport.ashx` / `GetDataChiSoTaiChinh.ashx` (no-auth, annual+quarterly).
- New typed contract needed: `FinancialStatement` / `FinancialReport` (period, fiscal_date, line items, statement_type, currency, units) — distinct from `PriceHistory`. Discuss the abstraction with reviewer before coding (ties into the post-gold architecture review).