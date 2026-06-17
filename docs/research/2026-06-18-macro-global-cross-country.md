# Step research — Macro — global cross-country (US/China/Japan/Germany and beyond): GDP, CPI/inflation, unemployment, policy rate, FX

**Date:** 2026-06-18  **Domain:** Macro — global cross-country (US/China/Japan/Germany and beyond): GDP, CPI/inflation, unemployment, policy rate, FX  **Working sources:** 4

VNStock clean-room exclusion applied; endpoints from providers' own servers + public protocols.

> Verified 3 no-auth working macro sources + 1 free-key source for global cross-country data. World Bank API (api.worldbank.org/v2) is the primary no-key backbone: JSON, all countries, multi-country in one call, deep history to 1960 (CPI/GDP/inflation/unemployment confirmed for USA/CHN/JPN/DEU). ECB Data Portal (data-api.ecb.europa.eu, no key) verified for euro-area HICP monthly + daily policy rates. OECD SDMX (sdmx.oecd.org, no key) verified for US unemployment/GDP (needs full key dims + browser UA). FRED (api.stlouisfed.org) needs a free 32-char API key — endpoint/param shape confirmed but no live row pulled. Dropped Stooq (now JS-challenge + robots Disallow *) and IMF SDMX 2.1 (XML-only, CP

> ⚠️ Redistribution: no published grant on these endpoints — personal/internal research, runtime-fetch only, no bundled data.

### World Bank Indicators API (v2)
- **Host:** `api.worldbank.org`
- **Data:** Cross-country macro time series (annual): GDP current US$ (NY.GDP.MKTP.CD), CPI index 2010=100 (FP.CPI.TOTL), inflation annual % (FP.CPI.TOTL.ZG), unemployment % (SL.UEM.TOTL.ZS), and ~1500 other World Development Indicators. All countries + aggregates via ISO3 codes, multi-country in one call with semicolon separator.
- **Auth:** NONE (no key, no token). Public open.
- **History:** Deep — annual data back to 1960 for core series (CPI USA: 65 non-null obs 1960-2024). Latest full-year ~2023-2024 (lastupdated 2026-04-08).
- **Coverage:** All World Bank member countries (~217) + regional/income aggregates. Verified USA/CHN/JPN/DEU returned in a single multi-country call.
- **Format:** JSON array of 2 elements: [0]=paging metadata {page,pages,per_page,total,lastupdated}, [1]=array of observation objects with fields indicator{id,value}, country{id,value}, countryiso3code, date (year string), value (number), unit. Units stated inside indicator.value (e.g. 'current US$', '2010=100', 'annual %').
- **Endpoints:** https://api.worldbank.org/v2/country/{ISO3[;ISO3...]}/indicator/{INDICATOR}?format=json&date={YYYY:YYYY}&per_page={N} ; indicator metadata: https://api.worldbank.org/v2/indicator/{INDICATOR}?format=json
- **Terms:** Most WDI data under CC-BY 4.0 (World Bank Open Data / Datacatalog public license, https://datacatalog.worldbank.org/public-licenses returns 200). Attribution required; redistribution allowed. No robots.txt on api host (4
```bash
curl -s -m 25 "https://api.worldbank.org/v2/country/USA;CHN;JPN;DEU/indicator/FP.CPI.TOTL.ZG?format=json&date=2022:2023&per_page=50"
```
_proof:_ Multi-country inflation FP.CPI.TOTL.ZG: USA 2022=8.0%, USA 2023=4.12%; DEU 2022=6.87%, 2023=5.95%; JPN 2022=2.5%, 2023=3.27%; CHN 2022=1.97%, 2023=0.23%. GDP NY.GDP.MKTP.CD USA 2023=27,292,170,793,214 US$. Unemployment SL.UEM.TOTL.ZS JPN 2023=2.6%.

### ECB Data Portal API (SDMX-JSON)
- **Host:** `data-api.ecb.europa.eu`
- **Data:** Euro-area / EU official macro & monetary series: HICP inflation (dataflow ICP), ECB policy rates incl. deposit facility / MRO / marginal lending (dataflow FM), exchange rates (EXR), monetary aggregates, yields. Daily/monthly periodicity depending on series.
- **Auth:** NONE (no key). Public.
- **History:** Deep — HICP monthly since 1990s, policy rates daily since 1999. Latest near-real-time (HICP through 2025-12, DFR through 2026-06-17).
- **Coverage:** Euro area (U2) aggregate + individual EU member states for many flows; FX EXR covers major world currencies vs EUR.
- **Format:** SDMX-JSON: top {header, dataSets, structure}. Observations in dataSets[0].series[key].observations as {index:[value,...]}; period labels in structure.dimensions.observation[0].values (map obs index -> period id). Units/scale in structure attributes.
- **Endpoints:** https://data-api.ecb.europa.eu/service/data/{DATAFLOW}/{SERIES_KEY}?lastNObservations={N}&format=jsondata (also startPeriod/endPeriod). HICP YoY: ICP/M.U2.N.000000.4.ANR ; Deposit facility rate: FM/D.U2.EUR.4F.KR.DFR.LEV
- **Terms:** Free public reuse under ECB copyright policy (attribution to ECB/SDW). robots.txt redirects (301). Documented public SDMX REST interface. No auth, no rate-limit hit.
```bash
curl -s -m 25 -H "Accept: application/json" "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV?lastNObservations=2&format=jsondata"
```
_proof:_ ECB HICP M.U2.N.000000.4.ANR (YoY %): 2025-09=2.2, 2025-10=2.1, 2025-11=2.1, 2025-12=1.9. Deposit facility FM/D.U2.EUR.4F.KR.DFR.LEV: 2026-06-16=2.0%, 2026-06-17=2.25%.

### OECD Data Explorer SDMX REST API
- **Host:** `sdmx.oecd.org`
- **Data:** OECD member + key partner macro series: harmonised unemployment rate (DSD_LFS@DF_IALFS_UNE_M), quarterly national accounts/GDP (DSD_NAMAIN1@DF_QNA), CPI, leading indicators, etc. Monthly/quarterly periodicity.
- **Auth:** NONE (public 'public/rest' path, no key).
- **History:** Series-dependent; monthly labour series multi-decade, quarterly GDP long. Latest 2025 (2025-Q1 returned).
- **Coverage:** All OECD members + accession/partner economies (USA/JPN/DEU directly; CHN in some partner-country flows).
- **Format:** SDMX-JSON 2.0: {meta, data{dataSets, structures}}. NOTE nested key is 'structures' (plural). Obs values in data.dataSets[0].series[key].observations; period ids in data.structures[0].dimensions.observation[0].values.
- **Endpoints:** https://sdmx.oecd.org/public/rest/data/{AGENCY,DATAFLOW,VERSION}/{KEY}?startPeriod=&endPeriod=&format=jsondata . KEY must supply ALL dimensions (use empty wildcards between dots; e.g. unemployment DSD needs 9 dims -> 'USA........'). Wrong dim count returns 'Not enough key values'.
- **Terms:** OECD terms allow free non-commercial reuse with attribution (some IO-restricted series). Requires a browser User-Agent (-A) or returns challenge. Public documented SDMX endpoint.
```bash
curl -s -m 25 -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,1.0/USA........?startPeriod=2025-01&endPeriod=2025-04&format=jsondata"
```
_proof:_ OECD US harmonised unemployment DF_IALFS_UNE_M: period 2025-Q1 unemployment rate = 4.37%.

### FRED (Federal Reserve Bank of St. Louis) API
- **Host:** `api.stlouisfed.org`
- **Data:** ~800k US + international macro/financial time series: CPI (CPIAUCSL), GDP (GDP), Fed Funds rate (FEDFUNDS/DFF), unemployment (UNRATE), plus international/country series. Daily/monthly/quarterly.
- **Auth:** REQUIRED — free API key (32-char lowercase alphanumeric) from https://fred.stlouisfed.org/docs/api/api_key.html. No key => HTTP 400 'Variable api_key is not set
- **History:** Deep, series-dependent (CPIAUCSL monthly since 1947, FEDFUNDS since 1954). Updated promptly after releases.
- **Coverage:** Primarily US; substantial international/global series and OECD/IMF-sourced country indicators mirrored.
- **Format:** JSON {observations:[{date,value},...], units, count, ...}. Values are strings; '.' denotes missing.
- **Endpoints:** https://api.stlouisfed.org/fred/series/observations?series_id={ID}&api_key={KEY}&file_type=json (also observation_start/observation_end, units, frequency). Series search: /fred/series/search
- **Terms:** Free key, generous limits (~120 req/min). FRED Terms of Use require key + attribution. Did NOT verify a live data pull (no key available here) — only confirmed the auth gate is a free key.
```bash
curl -s -m 25 "https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&file_type=json&api_key=YOUR_32CHAR_KEY"
```
_proof:_ No-key call returns {"error_code":400,"error_message":"...Variable api_key is not set..."}; dummy short key returns "...api_key is not a 32 character alpha-numeric lower-case string..." — confirms endpoint/param shape correct, only a free key is missing.

## Notes

VNStock clean-room rule honored: no vnstock/VNStock/vnstocks.com/thinh-vu/vnstock-hq sources searched, browsed, or cited. All endpoints learned from official provider APIs / the SDMX standard / general knowledge and verified by direct curl against each provider's own server.

PRIMARY no-key cross-country source = World Bank API: fully verified, deep history (1960+), all countries, multi-country in one call, JSON, no auth. Recommended backbone for the macro domain.

ECB Data Portal (no key) and OECD SDMX (no key) verified with real values — good for euro-area/EU high-frequency (daily policy rate, monthly HICP) and OECD labour/GDP respectively. Both SDMX-JSON: OECD uses data.structures (plural) + needs all key dimensions + a browser User-Agent; ECB uses structure (singular).

FRED: endpoint and param shape verified, but REQUIRES a free 32-char API key (confirmed by the exact validation err
