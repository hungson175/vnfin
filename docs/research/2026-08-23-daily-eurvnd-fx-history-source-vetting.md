# #224 daily EUR/VND history — source and legal vetting

**Artifact path:** `docs/research/2026-08-23-daily-eurvnd-fx-history-source-vetting.md`
**Research date:** 24 August 2026 (UTC+7); the packet fixes the `2026-08-23` filename.
**Packet:** `tasks/224-daily-eurvnd-fx-history-spec.md` at reviewer `b8ee1e5`
**Requested window:** inclusive `2018-01-01..2026-08-20`
**Requested economic series:** direct **VND per 1 EUR**
**Disposition:** **SOURCE-GAP CLOSURE** — no daily EUR/VND source qualifies for TDD.

This is a source/design record, not a runtime capability. The daily EUR/VND chain remains
empty and the current annual USD/VND behavior remains unchanged. No provider route was probed,
no live rate or response was retained, and no RED test, production code, source registration,
API claim, push, or issue closure is authorized by this report.

## 1. Decision and hard boundary

No candidate passes the following qualification tuple conjunctively:

```text
named owner + exact route/version + direct EUR/VND identity + one provider field/basis
+ VND per 1 EUR direction/scale + observation/publication/revision semantics
+ requested coverage or provider-declared partial coverage
+ bounded transport/rate/retry behavior + lawful automation/return/storage/redistribution
```

The absence of a qualifying tuple is not evidence that EUR/VND is unavailable everywhere. It is
the narrower engineering disposition that no lawful, response-backed, bounded, reusable unit is
ready for this library. In particular:

- a EUR/VND-looking route in a facade is not proof of a provider-published direct observation;
- an ECB EUR/USD rate plus another provider's USD/VND rate is forbidden triangulation;
- cash, transfer, sell, central, bilateral, market-close, period-average, and blended rates are
  different economic bases and are not interchangeable failover units;
- current/spot, annual, forward, interpolated, resampled, nearest, filled, or stamped values
  cannot satisfy a daily historical request;
- a public page, no-key route, HTTP status, empty response, WAF response, or search result cannot
  prove absence, permission to automate, caller-facing return, storage/cache, redistribution,
  rate/retry policy, or revision semantics; and
- the future chain must choose one qualified source for the whole request. It must never stitch
  dates or mix bases merely because the unit string is `VND per 1 EUR`.

## 2. Clean-room and no-probe protocol

Before this research I read [`docs/vnstock-blacklist.md`](../vnstock-blacklist.md). Every web
search used the mandatory exclusion:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result, page, code, documentation, schema, endpoint map, test, package, or
behavior was opened, cited, compared, or used. All retained evidence below comes from official
provider/regulator pages, official provider documentation, or previously reviewed primary-source
notes in this repository. No blacklisted-derived material is part of the design.

This was a **no-probe** research round:

| Evidence activity | Logical retrievals | Physical HTTP/API calls | Retries | Response/body/header retention |
| --- | ---: | ---: | ---: | --- |
| Official page/document reading and source-catalogue inspection | 0 | 0 | 0 | None |
| Candidate route/API dispatch | 0 | 0 | 0 | Not performed |
| Credentials, cookies, browser session, proxy, challenge bypass | 0 | 0 | 0 | None |

The route/path entries below are canonical, path-only references. No query-bearing URL, live
rate, raw response, raw header block, cookie, credential, response digest, provider exception,
or reporter artifact is retained. `NOT_RETAINED` means that a field was not obtained in this
no-probe round; it is not a negative response and not a coverage oracle.

## 3. Evidence inventory and candidate ledger

### 3.1 Candidate disposition matrix

| Candidate unit | Official owner/route inspected | What is actually evidenced without a probe | Missing qualification axes | Disposition |
| --- | --- | --- | --- | --- |
| Vietcombank current/dated-rate family, each EUR cash/transfer/sell field independently | [Vietcombank rate page](https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia) | The current page lists EUR and three distinct bank quote columns; it labels the table as reference information and offers an XML link. This is current-surface evidence only. | Historical response-backed field identity, direct EUR/VND scale/date/revision, requested-span retention, pagination, automation/rate/retry, caller return, storage, redistribution, commercial use | `COVERAGE_GAP` + `BASIS_GAP` + `IDENTITY_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| State Bank of Vietnam official cross-rate product | [SBV official portal](https://www.sbv.gov.vn/) and [official statistical-product catalogue](https://www.sbv.gov.vn/documents/d/sbv_portal/527697) | The official menu distinguishes central rate, reference rates, and VND cross rates. The catalogue describes the VND cross-rate product as weekly and for tax-calculation purposes. | Daily historical direct EUR/VND response, field/basis/scale/date/revision, 2018–2026 bounds, transport/pagination, reuse and automation terms | `COVERAGE_GAP` + `BASIS_GAP` + `IDENTITY_GAP` + `LEGAL_GAP` |
| ECB euro reference-rate roster | [ECB reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html) and [framework](https://www.ecb.europa.eu/stats/pdf/exchange/Frameworkfortheeuroforeignexchangereferencerates.en.pdf) | The official page publishes a finite EUR-base roster; its current page contains 30 currencies and no VND row. The framework says an official EUR rate can use a USD cross when direct EUR data is unavailable. | A direct EUR/VND owner field, requested coverage, library redistribution terms, and a basis compatible with the packet's direct-only rule | `NOT_SERVED` + `BASIS_GAP` |
| Frankfurter v2, unfiltered facade | [Frankfurter v2 documentation](https://frankfurter.dev/) | The owner documentation says the default is blended across providers, provider filtering is separate, and underlying provider terms control use. The currency catalogue lists VND, but a currency listing is not a direct EUR/VND response or owner identity. | One direct provider/basis, response-backed EUR/VND field, exact coverage/revision, provider-specific rights, route rate policy, bounded runtime | `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| Frankfurter v2 with ECB provider selection | [Frankfurter ECB provider page](https://frankfurter.dev/providers/ecb/) | The facade describes an ECB provider with a published historical span and provider-specific filter examples. The current ECB official roster does not include VND; the facade page does not prove a direct EUR/VND ECB observation. | Direct provider response, VND membership in the selected ECB series, field/basis/revision, legal redistribution, route budget | `NOT_SERVED` or `IDENTITY_GAP` pending a future response; not a qualified unit |
| BIS bilateral exchange rates | [BIS bilateral exchange-rate overview](https://data.bis.org/topics/XRU) and [BIS exchange-rate statistics](https://www.bis.org/statistics/dataportal/exr.htm) | BIS describes its bilateral dataset as nominal rates against USD, with sources combined for consistency. That is not direct EUR/VND. | Direct EUR/VND identity, single-owner basis, and packet coverage; any legal grant cannot repair the wrong pair | `IDENTITY_GAP` + `BASIS_GAP` |
| World Bank WDI official exchange rate | [World Bank `PA.NUS.FCRF`](https://data.worldbank.org/indicator/PA.NUS.FCRF) | The indicator is official exchange rate in local currency per US dollar, period average, annual, with CC BY 4.0 shown by the catalogue. It is the existing annual USD/VND source. | Daily EUR/VND identity, cadence, direct pair, and coverage | `NOT_SERVED` + `BASIS_GAP`; preserve annual only |
| Federal Reserve/FRED negative controls | [Federal Reserve H.10](https://www.federalreserve.gov/releases/h10/current/) and [FRED DEXCHUS](https://fred.stlouisfed.org/series/DEXCHUS) | Prior reviewed #217 source evidence records H.10/FRED as USD-bilateral or USD/CNY controls, not direct EUR/VND. No new request was made here. | Direct EUR/VND owner field, basis, requested span, and reuse contract | `NOT_SERVED` + `IDENTITY_GAP` |
| Unofficial aggregators, copied datasets, open-rate facades without a direct owner contract, login/paid/broker/private routes | Excluded by packet and clean-room policy | No candidate evidence retained; no request made. | All axes | `EXCLUDED`, never a fallback |

The matrix is a source-gap ledger, not a ranking. A candidate may be reopened only as the same
provider + route/version + basis unit; evidence from one row cannot repair another row.

### 3.2 Per-unit no-probe transport ledger

The packet requires route, transport, budget, and identity axes to be total even when the round
does not dispatch a candidate. This ledger makes the no-probe state explicit. `GET` below means
an official page/document inspection only; it is not a data/API dispatch. The four counters are
`logical targets / physical calls / page or cursor calls / retries`, and every candidate is
`0 / 0 / 0 / 0`.

| Unit | Canonical host/path (query-free) | Method / parameter intent | HTTP / complete MIME / effective route | Auth / session / UA / WAF | Counters | Response identity / bounds |
| --- | --- | --- | --- | --- | --- | --- |
| VCB current rate surface; cash, transfer, sell kept as separate units | `www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia` | `GET` page inspection; no API/date parameter | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED`; no candidate dispatch | `0 / 0 / 0 / 0` | Current EUR/quote-column labels only; historical pair, field, bounds `NOT_RETAINED` |
| SBV cross-rate product | `www.sbv.gov.vn/` and `www.sbv.gov.vn/documents/d/sbv_portal/527697` | `GET` menu/catalogue inspection; no route parameter | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED`; no candidate dispatch | `0 / 0 / 0 / 0` | Weekly tax-cross-rate catalogue fact; direct daily response/bounds `NOT_RETAINED` |
| ECB EUR reference roster/framework | `www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html` and `www.ecb.europa.eu/stats/pdf/exchange/Frameworkfortheeuroforeignexchangereferencerates.en.pdf` | `GET` page/PDF inspection; no SDMX series key | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED`; no candidate dispatch | `0 / 0 / 0 / 0` | Roster has no current VND row; direct EUR/VND bounds `NOT_SERVED`/not established |
| Frankfurter unfiltered facade | `frankfurter.dev/` and `frankfurter.dev/currencies/vnd/` | `GET` documentation/catalogue inspection; no API pair/date request | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED`; no API dispatch | `0 / 0 / 0 / 0` | Nominal VND provider catalogue only; owner field/basis/pair bounds `NOT_RETAINED` |
| Frankfurter ECB provider | `frankfurter.dev/providers/ecb/` | `GET` provider-page inspection; no provider-filter request | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED`; no API dispatch | `0 / 0 / 0 / 0` | Provider metadata only; direct VND response/bounds `NOT_RETAINED` |
| BIS bilateral exchange rates | `data.bis.org/topics/XRU` and `www.bis.org/statistics/dataportal/exr.htm` | `GET` overview/methodology inspection; no SDMX key | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED`; no candidate dispatch | `0 / 0 / 0 / 0` | Official dataset is USD-relative/combined-source; direct EUR/VND `IDENTITY_GAP` |
| World Bank annual exchange-rate indicator | `data.worldbank.org/indicator/PA.NUS.FCRF` | `GET` catalogue inspection; no WDI API request | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED`; no candidate dispatch | `0 / 0 / 0 / 0` | Annual USD period-average/CC BY 4.0; daily EUR/VND `NOT_SERVED` |
| Federal Reserve/FRED negative controls | `www.federalreserve.gov/releases/h10/current/` and `fred.stlouisfed.org/series/DEXCHUS` | `GET` page references only; no new request | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED`; no new dispatch | `0 / 0 / 0 / 0` | Prior reviewed wrong-pair/USD controls; direct EUR/VND `NOT_SERVED` |

No route-specific complete MIME, redirect/effective-route, WAF, session, user-agent, body-size,
page, retry, or rate-policy fact is silently filled in. The zero counters are real for this
round; they do not describe a provider's future allowance.

### 3.3 Coverage and outcome ledger

The requested bounds are always the same for this issue. The table separates provider/catalogue
facts from response-backed row accounting; no response-backed row count is invented:

| Unit | Requested start/end | Provider-declared cadence/bounds | Response rows / distinct / duplicates / gaps | Outcome |
| --- | --- | --- | --- | --- |
| VCB cash | `2018-01-01 / 2026-08-20` | Current page only; historical bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `COVERAGE_GAP` |
| VCB transfer | `2018-01-01 / 2026-08-20` | Current page only; historical bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `COVERAGE_GAP` |
| VCB sell | `2018-01-01 / 2026-08-20` | Current page only; historical bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `COVERAGE_GAP` |
| SBV cross-rate | `2018-01-01 / 2026-08-20` | Official catalogue says weekly tax-calculation product; historical direct EUR/VND bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `COVERAGE_GAP` + `BASIS_GAP` |
| ECB direct EUR/VND | `2018-01-01 / 2026-08-20` | Current roster has no VND direct row | `0 / 0 / 0 / 0` candidate dispatch; no row oracle | `NOT_SERVED` for current roster |
| Frankfurter facade/ECB filter | `2018-01-01 / 2026-08-20` | Nominal VND catalogue/provider metadata only; pair bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `IDENTITY_GAP` + `COVERAGE_GAP` |
| BIS bilateral | `2018-01-01 / 2026-08-20` | USD-relative dataset; not direct EUR/VND | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `IDENTITY_GAP` + `BASIS_GAP` |
| World Bank annual | `2018-01-01 / 2026-08-20` | Annual period-average USD basis | `NOT_RETAINED` for this no-probe round | `NOT_SERVED` for daily EUR/VND |
| Federal Reserve/FRED | `2018-01-01 / 2026-08-20` | Prior reviewed wrong-pair/USD controls | `NOT_RETAINED` for this no-probe round | `NOT_SERVED` + `IDENTITY_GAP` |

An empty, timed-out, WAF, or unreconciled future retrieval would be `TRANSPORT_INCONCLUSIVE`
or another bounded failure, never a zero-row `NOT_SERVED` result. `FULL` and
`QUALIFIED_PARTIAL` are unavailable in this round because no direct response was retained.

### 3.4 Vietcombank — current quote surface does not prove history

The official rate page visibly separates `Mua tiền mặt` (cash buy), `Mua chuyển khoản`
(transfer buy), and `Bán` (sell), and lists EUR among the currencies. It also says the table is
for reference and exposes a current update date/time. Those facts establish neither a historical
EUR/VND observation nor a single economic basis. The page's XML link is a current-surface lead,
not permission to crawl a dated history.

Each field would be a separate qualification unit. It must not be averaged, selected by
convenience, or combined with another provider. In this no-probe round the following are all
`NOT_RETAINED`: historical envelope, exact field types, direction/scale, date versus update
timestamp, revision model, served bounds, page/count contract, complete MIME, effective route,
and response-level legal/rate policy. The current page's “reference” wording is not an
automation, cache, caller-return, or redistribution grant. Therefore no VCB field is a partial
daily source.

### 3.5 State Bank of Vietnam — official cross-rate product is not the requested daily series

The official SBV portal separates three concepts: the central VND/USD rate, reference rates
between VND and foreign currencies, and VND cross rates used to determine a tax-calculation
rate. The official statistical-product catalogue records the cross-rate product as **weekly**,
with a publication schedule around Thursday (or the preceding working day) and an effective-date
publication window. That is a useful owner/product distinction, but it does not prove a daily
historical EUR/VND market series from 01 January 2018 through 20 August 2026.

No SBV route was dispatched. The following therefore remain `NOT_RETAINED`: direct EUR/VND
response identity, selected field, scale, date/revision semantics, pagination, MIME, WAF/rate
behavior, and all reuse axes. The central USD/VND product cannot be converted through another
source. A future owner-approved cross-rate response would still need to prove that its basis is
the packet's direct economic series rather than a tax or USD-cross substitute.

### 3.6 ECB — official roster and cross-rate methodology fail the direct-only gate

The ECB reference-rate page states that currencies are quoted against the euro and publishes a
working-day reference rate roster. The current official page inspected on 24 August 2026 shows
30 currencies; VND is not among them. This supports `NOT_SERVED` for the current ECB direct
EUR/VND unit, not a universal statement about every historical or third-party dataset.

The ECB framework also explicitly describes a USD-cross fallback when direct EUR data is not
available for a currency. That methodology is precisely why this packet forbids accepting a
cross-derived EUR/VND result: it would not be a response-backed direct provider observation.
The ECB's reference rates are informational and not transaction quotes. No daily route or data
series was dispatched, so no coverage, redistribution, or response-level rights claim is made.

### 3.7 Frankfurter — pair syntax/currency catalogue is not direct identity

Frankfurter's official v2 documentation says it tracks daily rates from central banks and other
official sources, supports date ranges, blends rates across providers by default, and allows a
provider filter. Its FAQ says there are no monthly/daily quotas but requests are rate-limited to
prevent abuse, and that commercial use depends on each underlying provider's terms. The official
currency catalogue lists VND with provider coverage; the [VND catalogue page](https://frankfurter.dev/currencies/vnd/)
and ECB provider page list nominal provider span/count metadata.

Those are facade/documentation facts only. No Frankfurter route was called. The catalogue does
not identify one direct EUR/VND owner field, basis, revision rule, or a reusable provider licence
for this library. `providers=ECB` is not a qualification shortcut: the official ECB roster
inspected here has no VND row, and the ECB framework permits cross construction for some rates.
The unfiltered facade is expressly a blend. Therefore Frankfurter remains a candidate for a
future owner-evidence review, not a source registration or failover member.

### 3.8 BIS, World Bank, Federal Reserve, and FRED — exact negative boundaries

- BIS's bilateral exchange-rate dataset is defined against USD and combines sources. It cannot
  supply direct EUR/VND without forbidden cross arithmetic or a different economic basis.
- World Bank `PA.NUS.FCRF` is annual period-average local currency per US dollar. Its clear
  CC BY 4.0 licence is useful for the existing annual USD/VND behavior, not for daily EUR/VND.
- The prior reviewed #217 evidence records Federal Reserve H.10 and FRED controls as USD-based
  or otherwise wrong-pair controls. Their official pages remain negative controls; no new request
  is needed to turn them into a candidate.
- Unofficial open-rate APIs, aggregators, copied datasets, and broker/login feeds are outside the
  packet's primary-source/legal gate. They are not a substitute merely because they display EUR
  and VND symbols.

## 4. Legal and reuse posture

The following axes are independent and must be proven per provider route:

```text
owner identity; automated access; caller-facing return; storage/cache;
redistribution; attribution; commercial use; rate/retry/pacing; revision/correction/retention
```

| Unit | Public/legal evidence retained | Conservative result |
| --- | --- | --- |
| Vietcombank | Official page labels the table as reference information. No dated-history automation, cache, return, redistribution, or rate/retry terms were retained. | `LEGAL_GAP` and `RATE_POLICY_GAP`; no historical use authorization |
| SBV | Official ownership and a public menu/catalogue establish a public information surface only. No library automation, caching, caller-return, redistribution, or revision contract was retained. | `LEGAL_GAP`; public reachability is not permission |
| ECB | Reference rates are described as informational; the framework describes publication and methodology, not a vnfin redistribution grant for a missing VND series. | Direct pair already `NOT_SERVED`; reuse remains unproven |
| Frankfurter/underlying providers | Frankfurter says commercial use is allowed subject to each underlying provider's terms, and rate limiting prevents abuse. That does not grant a direct EUR/VND provider identity or a route-specific cache/redistribution contract. | `LEGAL_GAP` + `RATE_POLICY_GAP` for this unit |
| BIS | Official source/methodology can explain the USD-bilateral dataset, but its wrong pair/basis is decisive. | No qualification; legal review cannot repair identity |
| World Bank | CC BY 4.0 is explicitly shown for the annual indicator. | Annual USD/VND only; no daily EUR/VND substitution |

No source receives an inferred licence from being public, no-login, free, or technically
reachable. Written owner permission would still need to be accompanied by response-backed direct
identity, coverage, bounded runtime, and compatibility evidence.

For auditability, the nine legal/runtime axes are total per candidate even when the answer is
unknown:

| Unit | Owner identity | Automated access | Caller return | Storage/cache | Redistribution | Attribution | Commercial | Rate/retry | Revision/retention |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VCB historical field units | Surface owner known; historical field identity `GAP` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| SBV cross-rate product | Product owner known; direct daily field `GAP` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| ECB direct EUR/VND | Current direct unit `NOT_SERVED` | `UNKNOWN` for this unit | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| Frankfurter facade/provider | Facade owner known; underlying direct owner `GAP` | Public no-key docs only; permission `UNKNOWN` | Underlying terms `UNKNOWN` | Underlying terms `UNKNOWN` | Underlying terms `UNKNOWN` | Provider-specific | Commercial use conditional on underlying terms | Abuse-limited; numeric policy `UNKNOWN` | Provider-specific/`UNKNOWN` |
| BIS bilateral | Owner/dataset known; pair is wrong | Not decisive | Not decisive | Not decisive | Not decisive | Provider terms | Provider terms | Weekly publication; route policy `UNKNOWN` | Combined-source/revision semantics not direct EUR/VND |
| World Bank annual | Owner/indicator known; cadence/basis is wrong | Provider terms | CC BY 4.0 for annual data | CC BY 4.0 conditions | CC BY 4.0 conditions | Required attribution | CC BY 4.0 | Provider terms | Annual series only |

`UNKNOWN`/`GAP` is intentionally not a permission, and an axis marked “not decisive” cannot
repair the candidate's wrong pair or cadence.

## 5. Current repository/API boundary

The packet's v0.2.0 correction is preserved. The dereferenced tag commit is
`2fe50df4f27064140ff9f7a680227a2b337ec74a`; it exposes spot `get_rate()` only and has no public
`fx.history()`. The current published base at this handoff is `origin/master=728bb99`; the packet's
earlier current snapshot `c646c37` is historical intake context, not a new capability claim.

Current code still has the following compatibility contract:

| Surface | Current invariant while #224 is source-gap closed |
| --- | --- |
| `vnfin.fx.history` | Existing signature and validation order remain unchanged. |
| Default | `Frequency.ANNUAL` remains the default. |
| Qualified history | Only annual USD/VND from World Bank WDI `PA.NUS.FCRF`. |
| Annual meaning | VND per 1 USD, annual period average, Jan-1-stamped observation; not daily or year-end. |
| Daily request | `Frequency.DAILY` remains a typed pre-network `InvalidData` rejection; no source access. |
| Pair validation | Non-USD/VND history remains a typed pre-network rejection. |
| Models | Reuse of `FXPoint`/`FXHistory` is future-only design vocabulary; no second model/facade is added. |
| `Frequency` export | No `__all__` or snapshot change is made by this source-gap packet. A qualified future implementation must review additive export compatibility separately. |
| Accessors | `rate_on()` is exact-match-only; `rate_for_year()` remains annual-only and must not reinterpret daily Jan-1 observations. |
| Diagnostics | Existing offline coverage diagnostics and annual source/error wording remain unchanged. No transport or failover carrier is invented. |
| Spot | Existing spot adapters and their legal scope are untouched by #224. |

`fetched_at_utc` remains retrieval time only. It is not an observation date, publication time,
first-availability marker, or Vietnamese-session guarantee.

## 6. Future qualification contract — not implemented

This section records the exact gates for a later source, without freezing a public daily API or
claiming that any gate is currently met.

### 6.1 One-source identity and basis

A future qualification unit is exactly:

```text
provider owner + canonical route/version + response field
+ direct EUR/VND identity + provider economic basis
+ VND per 1 EUR direction/scale + observation/publication/revision semantics
+ requested or declared partial bounds + legal/runtime contract
```

The successful response must prove the pair and field itself. A path, query label, page title,
currency catalogue, numeric agreement, or caller inversion is not identity proof. No USD leg,
midpoint, cash/transfer/sell substitution, annual expansion, forward/backfill, interpolation,
resampling, nearest match, or synthetic weekend value is allowed.

If one unit later qualifies, it is the sole source for the request. A failover chain is allowed
only after two independently qualified units prove identical basis, date, revision, and calendar
semantics; one source wins the whole request and providers are never stitched by date. Until then
the new chain is empty and there is no `SourceAttempt`/provider-attempt public field.

### 6.2 Future request/result semantics

After a fresh implementation authorization, a qualified path would be allowed to handle only:

```python
vnfin.fx.history(
    "EUR", "VND", date(2018, 1, 1), date(2026, 8, 20),
    frequency=Frequency.DAILY,
)
```

The future validation contract is:

1. both bounds are required plain `datetime.date` values, inclusive, with `start <= end`;
2. unsupported pair/frequency, malformed/missing/reversed/excessive bounds, and unknown values
   fail before network;
3. returned rows are provider observations only, ascending, unique, finite, positive, and
   non-boolean, with `unit == value_unit == "VND per 1 EUR"`;
4. observation date, publication date, revision date, and retrieval time remain separate;
   without an owner-supplied publication timestamp, documentation must not promise same-day
   availability or a Vietnamese-session cutoff, and callers use a strict-prior date rule;
5. provider calendar/status evidence may explain a weekend, holiday, or declared nonpublication;
   an unexplained internal gap, missing requested endpoint, duplicate, out-of-window row, empty
   response, or unreconciled page fails the whole source and returns no partial history; and
6. `rate_on()` remains exact-match-only and `rate_for_year()` rejects daily histories.

Any future `rate_basis` field, warning tuple, public coverage result, error carrier, or provider
attempt carrier must be additive, finite, sanitized, snapshot-tested, and reviewed with annual
constructor/DataFrame/diagnostic compatibility. This source-gap packet does not add or promise
one.

### 6.3 Coverage and no-false-absence

`FULL` is possible only when the provider declares or proves served bounds covering both requested
endpoints and page/count/cursor/calendar reconciliation succeeds. `QUALIFIED_PARTIAL` is possible
only when the provider declares a narrower bound and all identity, basis, legal, and runtime axes
still pass; it must expose that bound and never imply the requested full span.

The following are unresolved, not absence claims:

```text
empty response; HTTP 200 HTML/challenge; timeout/TLS/connection failure;
redirect/effective-route mismatch; wrong MIME/status; schema/identity/basis failure;
budget or decompressed-byte exhaustion; unreconciled page/count/cursor; unknown calendar gap
```

They produce no series and cannot establish `NOT_SERVED` or `COVERAGE_GAP`. `NOT_SERVED` requires
owner/catalogue evidence that the exact unit is not published; `COVERAGE_GAP` requires a qualified
provider's declared/response-backed boundary. No false absence is inferred from this no-probe
round.

### 6.4 Future bounded transport and atomic budget

Numeric ceilings remain intentionally unfrozen until one candidate supplies a real documented
route, page/cursor contract, body size, and rate policy. The mechanics are fixed now:

- one request-scoped sequential ledger covers logical source attempts, physical dispatches,
  pages/cursors, retries, redirects, and decompressed bytes;
- every physical dispatch reserves its logical/page/retry/physical units atomically before
  transport; a failed reservation performs zero network calls;
- streamed decompressed bytes are charged after dispatch and overflow fails the whole request;
- a retry consumes a separately reserved unit; hidden HTTP-client retries, fan-out, date-per-call
  loops, concurrent page requests, and unbounded redirects are forbidden;
- exhaustion returns no partial accumulator and retains only bounded sanitized real attempts; it
  never fabricates an empty final attempt or a `diagnostics_truncated` attempt; and
- the owner-approved rate/pacing policy is a prerequisite, not a number to invent from another
  provider or from current spot behavior.

For a future JSON owner route, the complete `Content-Type` value must be parsed after the first
colon, its media-type portion lower-cased and trimmed, and compared exactly with `application/json`.
HTML/XML, missing, malformed, or colon-suffixed non-JSON media types fail closed. A route that
uses another documented media type must receive its own exact parser contract; generic “JSON-like”
acceptance is not allowed.

The future internal validation vocabulary is closed by design, but is not a current public API:

```text
ok, unexpected_http_status, mime_mismatch, redirect, effective_route_mismatch,
timeout, tls_error, rate_limited, server_error, waf_challenge, body_limit,
json_parse_error, schema_error, identity_mismatch, basis_mismatch,
duplicate_or_overlap, page_reconciliation_error, out_of_window_date,
missing_requested_endpoint, unexplained_gap, budget_exhausted
```

No raw URL, query, body, header, exception, cookie, credential, provider prose, or live rate may
escape into public diagnostics. Public status/warning tokens, if later needed, require a separate
compatibility review rather than being silently inferred from these internal names.

## 7. Conjunctive reopen criteria

The source gap remains closed until **all** of the following are evidenced for one candidate
unit:

1. official owner identity, canonical route/version, response-backed direct EUR/VND field, exact
   direction/scale, economic basis, and observation/publication/revision semantics;
2. strict full-MIME/effective-route/status behavior, bounded body/decompression, no private
   endpoint, proxy bypass, challenge solving, login, or paid credential;
3. exact requested bounds or owner-declared partial bounds, page/count/cursor reconciliation,
   duplicate/out-of-window checks, provider calendar/nonpublication evidence, and no fabricated
   rows;
4. finite owner-approved logical/physical/page/retry/redirect/byte budget and rate/pacing policy,
   with atomic reservation/exhaustion and no-false-partial behavior;
5. explicit legal answers for automated access, caller return, storage/cache, redistribution,
   attribution, commercial use, rate/retry, and revision/correction/retention;
6. annual USD/VND compatibility, existing model/facade reuse, exact daily unit, diagnostics and
   snapshot compatibility, and a public API design that does not claim unreviewed fields; and
7. a new exact-SHA reviewer design PASS followed by a separate RED-first implementation review.

Evidence from another pair, another basis, another provider, an empty/WAF response, an open
facade, or a search snippet cannot satisfy a missing criterion. A source-gap docs PASS, if granted,
authorizes only publication/resolution of these three docs paths; it does not authorize RED,
production code, source registration, push, or close before that exact PASS.

## 8. Sources

Official sources inspected or used as bounded negative controls:

- [Vietcombank official rate page](https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia)
- [State Bank of Vietnam official portal](https://www.sbv.gov.vn/)
- [SBV official statistical-product catalogue](https://www.sbv.gov.vn/documents/d/sbv_portal/527697)
- [ECB euro foreign exchange reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
- [ECB reference-rate framework](https://www.ecb.europa.eu/stats/pdf/exchange/Frameworkfortheeuroforeignexchangereferencerates.en.pdf)
- [ECB Data Portal exchange-rate overview](https://data.ecb.europa.eu/key-figures/ecb-interest-rates-and-exchange-rates/exchange-rates)
- [Frankfurter v2 documentation](https://frankfurter.dev/)
- [Frankfurter provider catalogue](https://frankfurter.dev/providers/)
- [Frankfurter ECB provider page](https://frankfurter.dev/providers/ecb/)
- [Frankfurter currency catalogue](https://frankfurter.dev/currencies/)
- [Frankfurter VND currency page](https://frankfurter.dev/currencies/vnd/)
- [Frankfurter v2 changelog](https://github.com/lineofflight/frankfurter/blob/main/CHANGELOG.md)
- [BIS bilateral exchange-rate overview](https://data.bis.org/topics/XRU)
- [BIS exchange-rate statistics](https://www.bis.org/statistics/dataportal/exr.htm)
- [World Bank official exchange-rate indicator](https://data.worldbank.org/indicator/PA.NUS.FCRF)
- [Federal Reserve H.10](https://www.federalreserve.gov/releases/h10/current/)
- [FRED DEXCHUS](https://fred.stlouisfed.org/series/DEXCHUS)
- [Previously reviewed #217 primary-source note](2026-08-23-daily-cnyvnd-fx-history-source-vetting.md)

## Bottom summary

- Decision: **SOURCE-GAP CLOSURE**; no direct daily EUR/VND unit qualifies.
- Current daily chain stays empty; annual World Bank USD/VND behavior is unchanged.
- No candidate route was probed: 0 logical calls, 0 physical calls, 0 retries, no live data retained.
- VCB/SBV lack response-backed daily identity, coverage, runtime, and reuse proof.
- ECB does not publish VND in the inspected EUR roster; cross-rate derivation is forbidden.
- Frankfurter is a blended facade with underlying-provider/legal/rate gaps, not a direct source.
- Reopen requires all identity, basis, coverage, bounded-runtime, legal, and compatibility axes.
- No RED, code, push, or close is authorized before exact design PASS.
