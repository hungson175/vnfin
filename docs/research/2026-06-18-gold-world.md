# Step research — Gold — world (XAU/USD) spot + historical

**Date:** 2026-06-18  **Domain:** Gold — world (XAU/USD) spot + historical  **Working sources:** 2

VNStock clean-room exclusion applied; endpoints from providers' own servers + public protocols.

> Verified 2 working no-auth world-gold sources from this host. gold-api.com gives live XAU (and XAG) spot in USD as clean JSON, no key, no history. fawazahmed0 currency-api (jsdelivr/pages.dev CDN, no key) gives daily XAU cross-rates vs 340+ currencies AND date-pinned daily history back to ~2024-03-02; invert usd.xau to get USD/oz, giving a buildable daily EOD series. Yahoo GC=F (429), stooq CSV (JS challenge), and FRED LBMA (IP-blocked) all failed from this IP and are omitted as working sources but documented in notes.

> ⚠️ Redistribution: no published grant on these endpoints — personal/internal research, runtime-fetch only, no bundled data.

### gold-api.com (live spot)
- **Host:** `api.gold-api.com`
- **Data:** Live world gold spot price XAU/USD (also silver XAG/USD via /price/XAG). Single latest tick only — no history.
- **Auth:** None (no key, no header).
- **History:** None — live/latest snapshot only.
- **Coverage:** World spot XAU/USD and XAG/USD.
- **Format:** JSON object: {currency, currencySymbol, exchangeRate, name, price, symbol, updatedAt(ISO8601 UTC), updatedAtReadable}. price = USD per troy ounce.
- **Endpoints:** https://api.gold-api.com/price/{SYMBOL}  where SYMBOL in {XAU, XAG}. (?date= is NOT supported -> {"error":"Symbol not found"}.)
- **Terms:** robots.txt returns 404/Not found (no disallow rules). Free public JSON API; no documented rate limit hit during testing. Third-party aggregator, not an exchange — fine for live spot display, not authoritative for settlem
```bash
curl -s -m 25 https://api.gold-api.com/price/XAU
```
_proof:_ {"currency":"USD","name":"Gold","price":4382.100098,"symbol":"XAU","updatedAt":"2026-06-17T17:54:08Z"}  (silver: {"name":"Silver","price":71.483002,"symbol":"XAG"})

### fawazahmed0 currency-api (daily XAU history, CDN-hosted)
- **Host:** `cdn.jsdelivr.net (primary) / currency-api.pages.dev (fallback)`
- **Data:** Daily XAU cross-rates vs 340+ currencies/cryptos. xau.usd = USD value of 1 troy ounce of gold. usd.xau = ounces per 1 USD (invert for USD/oz). Date-pinned daily history -> buildable EOD XAU/USD series.
- **Auth:** None (no key). Public CDN.
- **History:** Daily back to ~2024-03-02 (verified: @2024-03-05 OK, @2024-03-01 -> 404). ~2.25 years of daily EOD as of test. Each day is a separate published date tag.
- **Coverage:** World gold XAU vs 340+ fiat+crypto currencies (USD, EUR, GBP, JPY, VND, etc.). One value per day (EOD-style).
- **Format:** JSON: {"date":"YYYY-MM-DD", "xau":{"usd":4323.18,"eur":3723.02,"gbp":3218.97,"vnd":113767321.14, ...341 keys}}. xau.usd units = USD per troy ounce. Inverse via usd.xau (oz per USD; 1/that = USD/oz).
- **Endpoints:** Latest: https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json | Historical (date-pinned npm tag): https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{YYYY-MM-DD}/v1/currencies/{base}.json | Fallback host: https://{latest|YYYY-MM-DD}.currency-api.pages.dev/v1/currencies/{base}.json | base = xau (gold-as-base) or usd (then read .usd.xau and invert).
- **Terms:** Open-source community API, free, no key, no documented rate limit; CDN-served (jsdelivr) so highly available. License field in package.json is null but project is published as free/open data. Date-pin only works for date
```bash
curl -s -m 25 https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/xau.json
```
_proof:_ @latest -> {date:2026-06-17, xau.usd:4323.1765, xau.eur:3723.0222, xau.gbp:3218.9723}. Date-pinned: @2026-06-10 xau.usd=4181.73; @2025-06-01 xau.usd=3292.10; @2025-01-02 xau.usd=2633.42; @2024-06-03 xau.usd=2329.37; @2024-03-05 OK. Series via usd base: 06-17 USD/oz=4323.18, 06-16=4325.42, 06-15=4329.07, 06-12=4195.63.

## Notes

VNStock and all derivatives fully excluded; only provider-native / global open sources hit directly. Three candidates FAILED from this host and are omitted as non-working HERE (but noted): (1) Yahoo Finance query1/query2 GC=F + XAUUSD=X returns HTTP 429 "Too Many Requests" on every attempt including the cookie+crumb flow — the datacenter IP is hard-throttled; works from residential IPs but NOT reproducible here. (2) stooq.com / stooq.pl CSV (https://stooq.com/q/d/l/?s=xauusd&i=d) now returns a JavaScript proof-of-work anti-bot challenge page (SHA-256 PoW + /__verify) instead of CSV, even with a browser UA — needs a JS-capable browser, so the plain-curl CSV path is dead. (3) FRED LBMA gold CSV (fredgraph.csv?id=GOLDAMGBD228NLBM, the authoritative London fix) connects over TLS but Akamai never returns a body (HTTP 000, hangs) — IP/datacenter block; authoritative-but-unreachable from here. 
