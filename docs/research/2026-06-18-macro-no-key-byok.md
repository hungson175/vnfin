# Macro data without personal API keys — research (no-key-first + BYOK)

**Date:** 2026-06-18  **Question (Boss):** publishing the library shouldn't force users to share/own a key (FRED-style) and get rate-limited. Can macro be no-key or scraped?

**Answer: yes — macro is fully covered by no-key official APIs; no key is required out of the box. FRED is the *only* keyed one we'd want, and it stays optional bring-your-own-key (never scraped).** Clean-room: VNStock excluded.

## No-key sources (all verified live 2026-06-18 with curl)

| Source | Auth | Countries (of US/CN/JP/DE/**VN**) | Freq / depth | License |
|--------|------|-----------------------------------|--------------|---------|
| **World Bank** `api.worldbank.org/v2` | none | **all 5 incl. VN** | annual, 1960–2024 (VN CPI 1995–) | CC BY 4.0 (attribution) |
| **IMF DataMapper** `imf.org/external/datamapper/api/v1` | none | **all 5 incl. VN** | annual WEO 1980–2025 + projections | all-rights-reserved (on-demand OK, no bundling) |
| **DBnomics** `api.db.nomics.world/v22` | none | **all 5 incl. VN** (via IMF/IFS) | VN GDP 2000–, CPI monthly 1995– | ODbL + per-series upstream terms |
| **OECD SDMX** `sdmx.oecd.org/public/rest` | none | US/CN/JP/DE (not VN) | monthly CPI, CLI | attribution, no bundling |
| **ECB** `data-api.ecb.europa.eu` | none | DE (euro-area) | monthly HICP 1996– | attribution |
| **Eurostat** `ec.europa.eu/eurostat/api/...` | none | DE (EU) | monthly HICP 1997–, quarterly GDP | attribution ("Source: Eurostat") |
| **US Treasury Fiscal Data** `api.fiscaldata.treasury.gov` | none | US | yields/rates/debt | US public domain |
| **US BLS v1** `api.bls.gov` | none (25 req/day) | US | CPI, unemployment | US public domain |

> Verified curls (examples): World Bank `…/country/VNM/indicator/NY.GDP.MKTP.CD?format=json`; IMF `…/api/v1/PCPIPCH/USA/CHN/JPN/DEU/VNM`; DBnomics `…/v22/series/IMF/IFS/M.VN.PCPI_IX?observations=1`.

## Keyed sources — optional bring-your-own-key only (env var, never bundled)

| Source | Key | Use |
|--------|-----|-----|
| **BLS v2** | `BLS_API_KEY` (free) | upgrade: 500 req/day, 20-yr range |
| **BEA** | `BEA_API_KEY` (free, required) | US GDP (NIPA) |
| **FRED** | `FRED_API_KEY` (free) | breadth/fallback — **official API only** |

## FRED specifically (Boss's example)

- `fredgraph.csv?id=…` *does* return data with no key, **but FRED's Terms of Use prohibit automated scraping outside the API**, and the **June-2024 update added anti-caching/anti-AI clauses** ([ToU](https://fred.stlouisfed.org/docs/api/terms_of_use.html)). → **Do not scrape FRED.**
- FRED is mostly a *redistributor* of BEA/BLS/Treasury (US public-domain) data — so we get the same series no-key from the primary sources, World Bank, IMF, or DBnomics. FRED stays an **optional BYOK** convenience via its official API.

## BYOK is the OSS standard

yfinance (no keys at all), pandas-datareader & OpenBB (env-var / runtime BYOK, zero bundled keys). Shipping a shared key → guaranteed rate-exhaustion, ToS violation, revocation, and secret-leak (PyPI is public). We bundle **no** keys.

## Vietnam note

No no-key *monthly* VN macro API exists; World Bank/IMF/DBnomics cover VN **annually** (CPI monthly via DBnomics/IMF-IFS). GSO/SBV have no stable API (scrape-only, fragile) → defer as a future BETA source.

Sources: World Bank, IMF DataMapper, DBnomics, OECD, ECB, Eurostat, BLS, BEA, Treasury Fiscal Data official docs (see per-source links in the agent transcripts).
