# Step research — Macro — Vietnam

**Date:** 2026-06-18  **Domain:** Macro — Vietnam  **Working sources:** 3

VNStock clean-room exclusion applied; endpoints from providers' own servers + public protocols.

> Verified 3 working no-auth structured sources for Vietnam macro, all curl-tested live: (1) World Bank Indicators API — the cleanest, deepest single source (GDP, CPI/inflation, USD/VND rate, M2, trade, FDI in one consistent annual JSON schema, ~1486 indicators); (2) IMF DataMapper API — same indicators plus forecasts to ~2031; (3) FRED fredgraph.csv — no-key CSV fallback for a few WB-sourced VN series. Official VN portals fall short: GSO (gso.gov.vn) is unreachable (TLS hangs -> HTTP 000, WAF/geo block) and SBV is a Liferay HTML portal with no stable public JSON API (exchange/rate widgets are Chart.js + govt CDN, legacy .jspx endpoints now 404). All data is ANNUAL only; no no-auth daily/month

> ⚠️ Redistribution: no published grant on these endpoints — personal/internal research, runtime-fetch only, no bundled data.

### World Bank Indicators API (country VNM)
- **Host:** `api.worldbank.org`
- **Data:** Full VN macro panel as annual time series: CPI level (FP.CPI.TOTL, 2010=100), CPI inflation %% YoY (FP.CPI.TOTL.ZG), GDP current US$ (NY.GDP.MKTP.CD), real GDP growth %% (NY.GDP.MKTP.KD.ZG), broad money M2 %%GDP (FM.LBL.BMNY.GD.ZS), trade %%GDP (NE.TRD.GNFS.ZS), exports/imports US$ (NE.EXP.GNFS.CD / NE.IMP.GNFS.CD), net FDI inflows US$ (BX.KLT.DINV.CD.WD), official exchange rate VND/USD period avg
- **Auth:** None (no key, fully open)
- **History:** Annual, deep: CPI inflation 1996-2024 (29 pts), real GDP growth 1985-2024 (40), GDP US$ 1985+, FDI 1970-2024 (55), exchange rate 1983-2024 (40), M2%%GDP 1992-2022, lending rate ...-2023. Updated quarterly (lastupdated 20
- **Coverage:** Vietnam (ISO3 VNM / id VN) plus all other countries via same template. Annual frequency only (no monthly/daily).
- **Format:** JSON array of 2 elements: [0]=pagination metadata {page,pages,per_page,total,lastupdated}; [1]=array of observations, each {indicator:{id,value}, country:{id,value}, countryiso3code:'VNM', date:'YYYY' (string year), value:float|null, unit, obs_status, decimal}. Units per indicator (US$ absolute, %%, index 2010=100, VND/USD). Note: response has UTF-8 BOM — decode with utf-8-sig.
- **Endpoints:** https://api.worldbank.org/v2/country/VNM/indicator/{INDICATOR_CODE}?format=json&per_page={N}&date={Y1}:{Y2}  (params: format=json|xml, per_page, date range, mrnev=1 for most-recent-non-empty, page). Discover codes: https://api.worldbank.org/v2/indicator?format=json&source=2&per_page={N}
- **Terms:** Public WDI API, CC BY 4.0 data (World Bank Open Data terms), free redistribution with attribution. No robots issue for the API host. No rate-limit key required; be polite with per_page paging.
```bash
curl -s 'https://api.worldbank.org/v2/country/VNM/indicator/FP.CPI.TOTL.ZG?format=json&per_page=80'
```
_proof:_ FP.CPI.TOTL.ZG VNM: date 2024 value=3.6211. FP.CPI.TOTL (index 2010=100): 2023=183.073, 2022=177.306, 2021=171.880, 2020=168.784. NY.GDP.MKTP.CD: 2023=433,857,681,378 US$. PA.NUS.FCRF: 2024=24164.9 VND/USD. BX.KLT.DINV.CD.WD: 2024=20,170,000,000 US$. NE.EXP.GNFS.CD 2024=4.295e11, NE.IMP.GNFS.CD 2024=3.988e11 US$. FR.INR.LEND 2023=9.32%%.

### IMF DataMapper API (WEO, country VNM)
- **Host:** `www.imf.org`
- **Data:** IMF World Economic Outlook indicators for VN incl. HISTORY + FORECASTS to ~2031: CPI inflation %% avg (PCPIPCH), real GDP growth %% (NGDP_RPCH), GDP US$ (NGDPD), GDP per capita, current account balance US$ bn (BCA), current account %%GDP (BCA_NGDPD), govt debt %%GDP (GGXWDG_NGDP), unemployment, etc.
- **Auth:** None (no key, fully open)
- **History:** Annual 1980 -> ~2031 (incl. multi-year forecasts), 52 points for VNM on PCPIPCH/BCA. Updated twice a year with WEO releases.
- **Coverage:** Vietnam VNM plus all IMF member economies. Annual only.
- **Format:** JSON: {"values":{"<INDICATOR>":{"<ISO3>":{"<YEAR>":<float>, ...}}}}. Years are string keys mapping to floats. Caller must drill into ['values'][IND][ISO3]. Mixes historical + WEO projections (no per-point actual/forecast flag — current+future years are forecasts).
- **Endpoints:** https://www.imf.org/external/datamapper/api/v1/{INDICATOR}/{ISO3}  (one or more ISO3 codes comma-sep; omit country to get all). Indicator list: https://www.imf.org/external/datamapper/api/v1/indicators
- **Terms:** Public IMF DataMapper endpoint backing the IMF website charts; free for use with IMF attribution. No auth, no robots block on the api path. Forecast values should be labeled as estimates downstream.
```bash
curl -s 'https://www.imf.org/external/datamapper/api/v1/PCPIPCH/VNM'
```
_proof:_ PCPIPCH (CPI inflation %% avg) VNM: 2023=3.3, 2024=3.6, 2025=3.3, 2026=4.9(fcast). NGDP_RPCH (real GDP growth %%) VNM: 2023=5.1, 2024=7, 2025=8, 2026=7.1(fcast). BCA (current acct bal US$ bn) VNM 2024=30.385. Range 1980..2031 (52 pts).

### FRED public CSV (St. Louis Fed, World-Bank-sourced VN series)
- **Host:** `fred.stlouisfed.org`
- **Data:** Convenience CSV download of select VN macro series (WB-sourced): CPI inflation %% YoY (FPCPITOTLZGVNM), GDP current US$ (MKTGDPVNA646NWDB), nominal exchange-rate index (DDOE01VNA086NWDB). Good as a no-key CSV fallback; for the full indicator set World Bank API is richer.
- **Auth:** None for the fredgraph.csv download path (the /fred/series JSON API does require an api_key — returns HTTP 400/needs key).
- **History:** CPI inflation FPCPITOTLZGVNM 1996-01-01 .. 2024-01-01 (29 annual rows). GDP MKTGDPVNA646NWDB 1985 .. 2024 (40 rows). Exchange-rate index DDOE01VNA086NWDB only 1994 .. 2017 (stale).
- **Coverage:** Vietnam (these specific series). Annual frequency.
- **Format:** Plain CSV: header 'observation_date,{SERIES_ID}' then rows 'YYYY-MM-DD,value'. Annual series are dated YYYY-01-01. Units depend on series (%% for inflation, US$ for GDP, index for the exchange-rate series).
- **Endpoints:** https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}  (CSV, no key). NOTE: api.stlouisfed.org/fred/series/* needs api_key. Invalid IDs return an HTML page, not CSV — validate by checking the header row.
- **Terms:** FRED is free; underlying VN series are World Bank (CC BY 4.0) re-hosted. fredgraph.csv is the documented no-key export path. Respect FRED terms / attribution.
```bash
curl -s 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=FPCPITOTLZGVNM'
```
_proof:_ FPCPITOTLZGVNM: 1996-01-01,5.675 ; last 2024-01-01,3.6211 (29 rows). MKTGDPVNA646NWDB: 1985-01-01,1.409e10 ; last 2024-01-01,4.764e11 (40 rows). DDOE01VNA086NWDB last row 2017-01-01 (stale, not recommended for FX).

## Notes

CLEAN-ROOM: vnstock and all derivatives fully excluded; no vnstock-derived endpoints, repos, sites, or schemas were consulted or used. All endpoints learned from provider API structure and general API knowledge. Web searches were not needed (direct API testing sufficed); the vnstock exclusion holds regardless.

VERIFICATION SUMMARY (all curl-tested live on 2026-06-18 from this Linux host):
- WORKING (structured JSON/CSV, no auth): World Bank API (best, deepest panel), IMF DataMapper (adds forecasts to ~2031), FRED fredgraph.csv (no-key CSV fallback). World Bank API is the cleanest single source for VN macro and covers GDP, CPI/inflation, exchange rate, M2, trade, FDI in one consistent schema/units.

OFFICIAL VN PORTALS — NOT usable as scrapeable structured sources from this host:
- GSO (gso.gov.vn / www.gso.gov.vn, IP 210.245.31.100): TLS connects but the server HANGS after server-hello 
