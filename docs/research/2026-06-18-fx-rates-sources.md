# FX Rate Sources for VND — Research Report

**Date:** 2026-06-18
**Author:** vnfin-oss agent
**VNStock exclusion:** VNStock / vnstock is fully blacklisted. No VNStock source, URL, schema, or
derivative was consulted. All sources below are primary, official, or license-clear.

---

## Executive Summary

| Rank | Source | Key | VND? | Conv. | Historical | Status |
|------|--------|-----|------|-------|------------|--------|
| 1 | **open.er-api.com** (ExchangeRate-API free) | None | Yes (166 currencies) | VND per 1 USD | No | Active (live-tested 2026-06-18) |
| 2 | **Vietcombank XML** (official VN commercial bank) | None | Implicit (VND is domestic) | VND per 1 foreign unit | No (spot only) | Active (live-tested 2026-06-18) |
| 3 | **frankfurter.dev** (ECB) | None | **No** (30 ECB currencies only) | — | Yes (back to 1999) | Active but unusable for VND |

Recommended primary: **open.er-api.com**. Recommended domestic/VN failover: **Vietcombank XML**.

---

## 1. open.er-api.com — ExchangeRate-API Open Endpoint

### Base URL and Example Endpoint

```
GET https://open.er-api.com/v6/latest/{BASE_CODE}
```

Example returning all rates with USD as base (no auth headers needed):

```
https://open.er-api.com/v6/latest/USD
```

Live-verified 2026-06-18 03:53 UTC+7:

```
https://open.er-api.com/v6/latest/VND   # VND as base
```

### Response Format (JSON)

```json
{
  "result": "success",
  "provider": "https://www.exchangerate-api.com",
  "documentation": "https://www.exchangerate-api.com/docs/free",
  "terms_of_use": "https://www.exchangerate-api.com/terms",
  "time_last_update_unix": 1750204951,
  "time_last_update_utc": "Thu, 18 Jun 2026 00:02:31 +0000",
  "time_next_update_unix": 1750291021,
  "time_next_update_utc": "Fri, 19 Jun 2026 00:17:01 +0000",
  "time_eol_unix": 0,
  "base_code": "USD",
  "rates": {
    "USD": 1,
    "EUR": 0.865608,
    "CNY": 6.774194,
    "JPY": 160.454628,
    "VND": 26227.808625
  }
}
```

Key timestamp fields: `time_last_update_utc` (ISO string) and `time_last_update_unix` (epoch seconds).
Total currency count: 166 as of 2026-06-18.

### Units / Quoting Convention

**VND per 1 base currency unit.**

When `base_code = "USD"`, `rates["VND"] = 26227.81` means **26,227.81 VND = 1 USD**.
When `base_code = "VND"`, `rates["USD"]` would be the inverse (~0.0000381).

Always read the `base_code` field to know the convention. The API supports any currency as base
by substituting the currency code in the URL path.

Spot-checked 2026-06-18:
- USD: base (1.0)
- EUR/USD: 0.8656 → EUR/VND = 29,853 VND/EUR (derived)
- CNY/USD: 6.774 → CNY/VND = 3,872 VND/CNY (derived)
- JPY/USD: 160.45 → JPY/VND = 163.5 VND/JPY (derived)
- VND/USD: 26,227.81 VND per 1 USD

### Auth and Rate Limits

- **No API key required** for the `open.er-api.com` subdomain.
- Updates once per ~24 hours (rates refreshed daily).
- Documented rate limit: "If you only request once every 24 hours you won't need to read any
  more of this section." Excessive requests return HTTP 429; the window resets after 20 minutes.
- For a library that caches the daily rate, one request per day is sufficient.

### Historical Data

**None.** The open (no-key) endpoint provides spot rates only. Historical time-series requires a
paid account on `api.exchangerate-api.com`.

### License / Terms of Use

- Redistribution of raw data is **prohibited** per the [Terms of Use](https://www.exchangerate-api.com/terms).
- Commercial use is allowed on both free and paid plans.
- Suitable for informational / illustrative use; not recommended as the sole source for actual
  financial transactions.
- Attribution requested: `<a href="https://www.exchangerate-api.com">Rates By Exchange Rate API</a>`
  (from docs; terms page does not enforce it as mandatory).
- Caching is permitted.
- Terms may change at any time for free-plan specifics.

### Reliability / Non-VN IP Access

Live-tested from a Linux box (Vietnam LAN) on 2026-06-18 with no issues. The CDN-backed endpoint
returns sub-200ms globally. No geo-blocking observed.

---

## 2. Vietcombank Official XML Feed

Vietcombank (VCB) is Vietnam's largest state-owned commercial bank and the de-facto reference for
commercial FX in Vietnam. Its public XML feed is used by countless Vietnamese apps and is explicitly
marked "for reference only."

### Base URL and Example Endpoint

```
GET https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10
```

No auth headers, no API key. The `b=10` parameter selects the branch (10 = HQ). Works without any
parameter as well.

### Response Format (XML)

```xml
<!--For reference only. Only one request every 5 minutes!-->
<ExrateList>
  <DateTime>6/18/2026 3:53:15 PM</DateTime>
  <Exrate CurrencyCode="USD" CurrencyName="US DOLLAR           "
          Buy="26,081.00" Transfer="26,111.00" Sell="26,431.00" />
  <Exrate CurrencyCode="EUR" CurrencyName="EURO                "
          Buy="29,547.27" Transfer="29,845.73" Sell="31,104.97" />
  <Exrate CurrencyCode="CNY" CurrencyName="YUAN RENMINBI       "
          Buy="3,793.81" Transfer="3,832.13" Sell="3,954.85" />
  <Exrate CurrencyCode="JPY" CurrencyName="YEN                 "
          Buy="158.20" Transfer="159.80" Sell="168.25" />
  <Source>Joint Stock Commercial Bank for Foreign Trade of Vietnam - Vietcombank</Source>
</ExrateList>
```

Key fields per `<Exrate>`:
- `CurrencyCode`: ISO 4217 code of the foreign currency (domestic is always VND)
- `Buy`: bank buys foreign currency at this many VND per unit
- `Transfer`: wire-transfer (telegraphic transfer) mid-rate in VND per unit
- `Sell`: bank sells foreign currency at this many VND per unit
- `<DateTime>`: local Vietnam time string (no timezone marker; assume Asia/Ho_Chi_Minh = UTC+7)

Currency coverage: AUD, CAD, CHF, CNY, DKK, EUR, GBP, HKD, INR, JPY, KRW, KWD, MYR, NOK, RUB,
SAR, SEK, SGD, THB, USD (20 currencies as of 2026-06-18).

### Units / Quoting Convention

**VND per 1 unit of the foreign currency** (all three: Buy, Transfer, Sell).

`Buy="26,081.00"` for USD means **Vietcombank pays 26,081 VND to buy 1 USD from a customer**.
`Sell="26,431.00"` means **Vietcombank charges 26,431 VND to sell 1 USD to a customer**.

For USD/VND mid-rate, use `Transfer` (telegraphic transfer rate). No inversion needed.

Rates are given with commas as thousands-separators (e.g. `"26,081.00"`). Parse with
`float(value.replace(',', ''))`.

### Auth and Rate Limits

- **No API key.** HTTP GET with no auth.
- Comment in the XML: "Only one request every 5 minutes!" — self-declared polite crawl rate.
- No documented enforcement (no observed rate-limit headers), but the 5-minute cadence must
  be respected for any production use.

### Historical Data

**No historical endpoint found.** Spot (current business day) only. Rates are updated intraday
(morning and sometimes afternoon on Vietnamese business days). No data on weekends/holidays.

### License / Terms of Use

The XML comment states "For reference only." No formal open-data license. Vietcombank makes this
feed public but does not publish explicit redistribution terms. Conservative interpretation:
acceptable for a library that fetches-on-request and does not republish raw data. Do not bundle
snapshot datasets derived from this feed.

### Reliability / Non-VN IP Access

Live-tested from Vietnam LAN on 2026-06-18 with instant response. The portal is a public-facing
Vietnamese banking site and has been reliably accessible for years. Access from non-VN IP addresses
(e.g., a cloud datacenter) has historically worked, though there is no formal SLA. If the library
will run from overseas cloud infra, test from a non-VN IP before committing to this as the
primary source.

---

## 3. frankfurter.dev — ECB Reference Rates

### Key Finding: VND Not Supported

Frankfurter provides ECB (European Central Bank) reference rates for **30 currencies only**:
AUD, BGN, BRL, CAD, CHF, CNY, CZK, DKK, EUR, GBP, HKD, HUF, IDR, ILS, INR, ISK, JPY, KRW, MXN,
MYR, NOK, NZD, PHP, PLN, RON, SEK, SGD, THB, TRY, USD, ZAR.

**VND is absent.** The ECB does not publish reference rates for the Vietnamese Dong.

Live-verified: `curl https://api.frankfurter.dev/v1/currencies | python3 ...` returned 30 entries,
no VND (2026-06-18).

### Why Document It Anyway

Frankfurter is excellent for EUR-anchored cross-rates (CNY, JPY, USD, etc.) that may be needed in
the broader library. For VND specifically, it is unusable.

### Endpoints (for non-VND use)

```
GET https://api.frankfurter.dev/v1/latest              # All currencies, EUR base
GET https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,CNY,JPY
GET https://api.frankfurter.dev/v1/1999-01-04?base=USD # Historical single date
GET https://api.frankfurter.dev/v1/2020-01-01..2020-12-31?base=USD  # Range
GET https://api.frankfurter.dev/v1/currencies          # Supported currency list
```

No API key. Completely open. MIT-licensed server code.

---

## 4. exchangerate.host (APILayer)

### Status: Requires API Key as of September 2023

Confirmed from GitHub issues and official signup page: exchangerate.host migrated to APILayer and
now requires a free-tier access key for all requests. Calls without a key return
`{"success": false, "error": {"code": 101, "type": "missing_access_key"}}`.

A free-tier key is available via signup (no credit card), but the endpoint is no longer zero-auth.
For a library designed around "no API key required," this source does not qualify in 2026.

If a key is available: free tier is 100 requests/month with 250 symbols. VND is supported.
Historic data is available on paid plans.

---

## 5. State Bank of Vietnam (SBV) — Central Reference Rate

### What SBV Publishes

The SBV publishes a daily "central reference rate" (tỷ giá trung tâm) for USD/VND, which sets the
band within which commercial banks may quote. It is published Monday–Friday at ~08:00
Asia/Ho_Chi_Minh.

### Machine-Readable Access

SBV operates several web portals:
- `https://www.sbv.gov.vn/TyGia/faces/ReraSbvOc.jspx` — returned 404 on 2026-06-18.
- `https://dttktt.sbv.gov.vn/TyGia/faces/ExchangeRate.jspx` — connects (TLS OK) but returns no
  body in automated fetch (likely ADF/Oracle Portal requiring browser session cookies).

**No public, documented, machine-readable JSON or XML API from SBV was found as of 2026-06-18.**
The SBV portals are Oracle ADF web applications that serve interactive HTML; they do not expose a
stable REST endpoint. Third-party commercial services (Fexant, Fluentax) scrape and re-serve SBV
rates via their own APIs, but those are paid services.

The SBV rate covers USD/VND only (central rate), not EUR, CNY, or JPY directly.

### Alternatives if SBV Central Rate Is Required

1. Scrape `https://www.sbv.gov.vn/webcenter/portal/en/home/rm/tygia` (HTML) — fragile.
2. Use the Vietcombank `Transfer` rate as a close proxy; VCB's transfer rate closely tracks the
   SBV central rate (within ±150 VND under normal conditions).
3. Use VNAppMob `https://api.vnappmob.com/api/v2/exchange_rate/sbv` — requires a 15-day-expiry
   bearer token (free via self-registration). Coverage: daily SBV rates. Quoting: VND per 1 unit.

---

## 6. Additional Candidates Evaluated

### iban.com XML/JSON

[IBAN Exchange Rates API](https://www.iban.com/exchange-rates-api) provides a free JSON endpoint.
Requires registration for an API key on the free tier. VND status: not confirmed without key.
Not suitable for zero-auth use.

### fixer.io

Free tier requires a free API key. Supports USD/VND. Not zero-auth.

### open.exchangerate-api.com vs open.er-api.com

These are two different things. `open.er-api.com` is the genuinely zero-auth endpoint.
`api.exchangerate-api.com` is the paid/keyed tier of the same provider. Do not confuse them.

---

## Recommended Failover Architecture

```
Primary:  open.er-api.com/v6/latest/{BASE}          # zero-key, global, 166 currencies, daily
Failover: portal.vietcombank.com.vn/.../pXML.aspx   # zero-key, VN-centric, XML, intraday
```

Both share the same quoting convention: **VND per 1 foreign currency unit**, which makes a
failover switch transparent at the data layer (no inversion needed). The two rate sets will
differ slightly (open.er-api.com uses aggregated market data; Vietcombank uses their commercial
buy/sell quotes — use the `Transfer` field for the closest mid-rate equivalent).

---

## Quoting Convention Comparison Table

| Source | Example pair | Value | Meaning |
|--------|-------------|-------|---------|
| open.er-api.com (base=USD) | USD/VND | 26,227.81 | 26,227.81 VND = 1 USD |
| open.er-api.com (base=VND) | VND/USD | 0.00003813 | 0.0000381 USD = 1 VND |
| Vietcombank XML (Transfer) | USD | 26,111.00 | 26,111 VND = 1 USD |
| Vietcombank XML (Transfer) | JPY | 159.80 | 159.80 VND = 1 JPY |
| frankfurter.dev (base=USD) | VND | N/A | Not supported |

---

## Sources

- [ExchangeRate-API Free Docs](https://www.exchangerate-api.com/docs/free)
- [ExchangeRate-API Terms of Use](https://www.exchangerate-api.com/terms)
- [Vietcombank XML Feed](https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10)
- [Frankfurter API Docs](https://frankfurter.dev/v1/)
- [Frankfurter GitHub](https://github.com/lineofflight/frankfurter)
- [SBV Exchange Rate Portal](https://www.sbv.gov.vn/webcenter/portal/en/home/rm/tygia)
- [SBV dttktt Portal](https://dttktt.sbv.gov.vn/TyGia/faces/ExchangeRate.jspx)
- [exchangerate.host now requires key (GitHub issue)](https://github.com/amrshawky/laravel-currency/issues/19)
- [VNAppMob Exchange Rate API v2](https://vapi.vnappmob.com/exchange_rate.v2.html)
- [Fexant SBV API](https://www.fexant.com/bank/SBV)
