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
provider/regulator pages, official provider documentation, the repository's existing primary-source
contract, or previously reviewed primary-source notes. No blacklisted-derived material is part of
the design.

This round has two explicitly separate evidence channels:

1. **Static document research:** official pages, catalogues, PDFs, and documentation were read as
   source evidence. The research tool did not retain or measure its underlying web transport log;
   therefore static-document logical/physical counts are `NOT_RETAINED`/`NOT_MEASURED`, not zero.
   The canonical references below are an evidence inventory, not a claim that a provider data route
   was dispatched. No raw page body, header block, cookie, query URL, response digest, or provider
   exception was retained.
2. **Candidate data/API dispatch:** no EUR/VND candidate data endpoint, API route, page/cursor, or
   retry was dispatched. This channel has exactly `0 / 0 / 0 / 0` for
   `logical targets / physical calls / page-or-cursor calls / retries`. Those zeros do not describe
   static-document transport or a provider's future allowance.

| Evidence channel | Logical retrievals | Physical calls | Pages/cursors | Retries | Retained transport material |
| --- | --- | --- | --- | --- | --- |
| Official static page/document research | `NOT_RETAINED` / `NOT_MEASURED` | `NOT_RETAINED` / `NOT_MEASURED` | `NOT_RETAINED` | `NOT_RETAINED` | Sanitized source facts and canonical references only |
| Candidate EUR/VND data/API dispatch | `0` | `0` | `0` | `0` | No live rate, response, body, header, exception, or artifact |
| Credentials, cookies, browser session, proxy, challenge bypass | `0` | `0` | `0` | `0` | None |

`NOT_RETAINED` means that the field was not obtained or transport-measured in this design round;
it is not a negative response and not a coverage oracle. `0` in the second row means no candidate
data/API dispatch occurred. The route/path entries below are query-free canonical references and
static evidence labels, not recorded HTTP methods or live request logs.

## 3. Evidence inventory and candidate ledger

### 3.1 Candidate disposition matrix

Every row is a separate provider/route/version/basis unit. A shared host does not merge economic
fields, response identities, legal terms, or budgets. The matrix is a source-gap ledger, not a
failover chain.

| Candidate unit | Official owner/route evidence | What is actually evidenced without candidate dispatch | Missing qualification axes | Deterministic disposition |
| --- | --- | --- | --- | --- |
| VCB historical EUR cash field | [Vietcombank rate page](https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia) | Current page labels a EUR cash-buy column and a reference surface only | Historical response field/date/revision, direct scale, requested bounds, automation, caller return, storage, redistribution, rate policy | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| VCB historical EUR transfer field | Same official rate page | Current page labels a distinct EUR transfer-buy column and a reference surface only | Same axes, independently of cash and sell | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| VCB historical EUR sell field | Same official rate page | Current page labels a distinct EUR sell column and a reference surface only | Same axes, independently of cash and transfer | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| SBV central VND/USD product | [SBV portal](https://www.sbv.gov.vn/) and [catalogue](https://www.sbv.gov.vn/documents/d/sbv_portal/527697) | Official menu distinguishes a central-rate product | Direct EUR/VND field, daily history, scale/date/revision, requested bounds, reuse/runtime | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` |
| SBV reference-rate product | Same official portal/catalogue | Official menu distinguishes reference rates between VND and foreign currencies | Direct daily EUR/VND response, field/basis/date, requested bounds, reuse/runtime | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` |
| SBV weekly tax cross-rate product | Same official portal/catalogue | Official catalogue describes a weekly VND cross-rate product for tax calculation | Daily market-history identity, requested daily span, reusable automation/return terms | `NOT_SERVED` + `BASIS_GAP` |
| ECB direct EUR/VND reference-rate unit | [ECB roster](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html) and [framework](https://www.ecb.europa.eu/stats/pdf/exchange/Frameworkfortheeuroforeignexchangereferencerates.en.pdf) | Current official EUR roster has 30 currencies and no VND row; framework permits USD-cross construction | Direct VND owner field, requested coverage, direct-only basis, reuse contract | `NOT_SERVED` + `BASIS_GAP` |
| Frankfurter v2 unfiltered facade | [Frankfurter docs](https://frankfurter.dev/) and [VND catalogue](https://frankfurter.dev/currencies/vnd/) | Official facade says default output is blended and VND has catalogue metadata | One direct owner field/basis, exact response identity, coverage/revision, underlying rights, route policy | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| Frankfurter v2 `providers=ECB` unit | [Frankfurter ECB provider](https://frankfurter.dev/providers/ecb/) | Provider-filter documentation exists; no provider-filter response was obtained; inspected ECB roster has no VND | Response-backed direct ECB/VND identity, field/basis, revision, rights, bounded route | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| Frankfurter underlying-provider inventory | [Frankfurter providers](https://frankfurter.dev/providers/) | The facade says underlying provider terms control use; the complete provider inventory was not independently reviewed for this pair | Per-provider route/field/basis, response identity, coverage, rights, revision, rate policy | `SOURCE-GAP` + `IDENTITY_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| BIS bilateral exchange-rate unit | [BIS overview](https://data.bis.org/topics/XRU) and [statistics](https://www.bis.org/statistics/dataportal/exr.htm) | Official dataset is nominally against USD and combines sources | Direct EUR/VND identity and one-provider basis; legal review cannot repair wrong pair | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` |
| World Bank `PA.NUS.FCRF` | [World Bank indicator](https://data.worldbank.org/indicator/PA.NUS.FCRF) | Official annual local-currency-per-USD period-average with CC BY 4.0; this is the current annual USD/VND source | Daily EUR/VND pair, cadence, direct basis, requested coverage | `NOT_SERVED` + `BASIS_GAP` |
| Federal Reserve H.10 | [Federal Reserve H.10](https://www.federalreserve.gov/releases/h10/current/) | Prior primary-source review records USD-based controls; no new data request | Direct EUR/VND field/basis, span, reuse/runtime | `NOT_SERVED` + `IDENTITY_GAP` |
| FRED DEXCHUS | [FRED DEXCHUS](https://fred.stlouisfed.org/series/DEXCHUS) | Prior primary-source review records a wrong-pair/USD control; no new data request | Direct EUR/VND owner field/basis, span, reuse/runtime | `NOT_SERVED` + `IDENTITY_GAP` |
| `open.er-api` current endpoint | [Repository source contract](../sources/fx-open-er-api.md) | Existing route is current-only, USD-anchored, derives EUR/VND from two USD legs, is rate-limited, and prohibits raw redistribution | Direct historical provider field/basis, requested coverage, lawful raw return, bounded historical route | `NOT_SERVED` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| Unofficial aggregators, copied data, login/paid/broker/private/proxy routes | Excluded by packet and clean-room policy | No candidate evidence retained and no request made | All axes | `EXCLUDED` — never a fallback |

`COVERAGE_GAP` is deliberately absent from this no-probe matrix. It is reserved for a qualified
unit whose owner-declared or response-backed boundary proves that a requested span is outside its
served coverage; unproven history uses `SOURCE-GAP` plus the proven specific gaps above.

### 3.2 Per-unit no-probe transport ledger

The packet requires route, transport, budget, and identity axes to be total even when no candidate
is dispatched. `Static reference` identifies a page/document used as evidence; it is not an HTTP
method claim. Candidate counters are always
`logical targets / physical calls / page-or-cursor calls / retries` and are independent of static
document research.

| Unit | Canonical host/path (query-free) | Static reference/evidence | Candidate dispatch | HTTP / complete MIME / effective route | Auth / session / UA / WAF | Candidate counters | Response identity / bounds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VCB EUR cash | `www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia` | Page reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Current cash label; historical response/bounds `NOT_RETAINED` |
| VCB EUR transfer | Same VCB path | Page reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Current transfer label; historical response/bounds `NOT_RETAINED` |
| VCB EUR sell | Same VCB path | Page reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Current sell label; historical response/bounds `NOT_RETAINED` |
| SBV central VND/USD | `www.sbv.gov.vn/` + catalogue path `documents/d/sbv_portal/527697` | Portal/catalogue reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Product label only; direct EUR/VND `NOT_RETAINED` |
| SBV reference rate | Same SBV paths | Portal/catalogue reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Product label only; daily field/bounds `NOT_RETAINED` |
| SBV weekly tax cross-rate | Same SBV paths | Catalogue cadence/product reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Weekly tax product; daily market history `NOT_SERVED` |
| ECB direct EUR/VND | `www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html` + framework PDF | Roster/framework reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Current roster lacks VND; direct unit `NOT_SERVED` |
| Frankfurter unfiltered | `frankfurter.dev/` + `frankfurter.dev/currencies/vnd/` | Docs/catalogue reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | VND catalogue/blend metadata only; direct identity `NOT_RETAINED` |
| Frankfurter `providers=ECB` | `frankfurter.dev/providers/ecb/` | Provider-page reference only; no filter request | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Provider metadata only; direct VND response `NOT_RETAINED` |
| Frankfurter underlying inventory | `frankfurter.dev/providers/` | Inventory reference incomplete; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Per-provider fields/bounds `NOT_RETAINED` |
| BIS bilateral | `data.bis.org/topics/XRU` + `www.bis.org/statistics/dataportal/exr.htm` | Overview/methodology reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | USD-relative/combined-source method; direct pair `IDENTITY_GAP` |
| World Bank annual | `data.worldbank.org/indicator/PA.NUS.FCRF` | Catalogue/licence reference only; transport not retained/measured | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Annual USD period average; daily unit `NOT_SERVED` |
| Federal Reserve H.10 | `www.federalreserve.gov/releases/h10/current/` | Prior primary-source reference; no new request | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | USD control; direct pair `NOT_SERVED` |
| FRED DEXCHUS | `fred.stlouisfed.org/series/DEXCHUS` | Prior primary-source reference; no new request | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Wrong-pair/USD control; direct pair `NOT_SERVED` |
| `open.er-api` current | `open.er-api.com/v6/latest/USD` | Existing repository contract reference only; no live request | None | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED` | `0 / 0 / 0 / 0` | Current USD anchor/cross-derived only; history `NOT_SERVED` |

No route-specific complete MIME, redirect/effective-route, WAF, session, user-agent, body-size,
page, retry, or rate-policy fact is silently filled in. Candidate zeroes are real for the dispatch
channel only; they do not describe static-document transport or a provider's future allowance.

### 3.3 Coverage and outcome ledger

The requested bounds are inclusive `2018-01-01 / 2026-08-20`. This table is response-row
accounting, not dispatch accounting. Each response column is `NOT_RETAINED` when no candidate
response was obtained, or `NOT_APPLICABLE` when the official evidence already proves that the
exact daily unit is not the product. Candidate dispatch counts remain only in §3.2.

| Unit | Requested interval | Provider-declared cadence/bounds | Response rows / distinct / duplicates / missing publication dates | Deterministic outcome |
| --- | --- | --- | --- | --- |
| VCB EUR cash | `2018-01-01 / 2026-08-20` | Current reference page; historical bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `SOURCE-GAP` + identity/basis/legal/rate gaps |
| VCB EUR transfer | `2018-01-01 / 2026-08-20` | Current reference page; historical bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `SOURCE-GAP` + identity/basis/legal/rate gaps |
| VCB EUR sell | `2018-01-01 / 2026-08-20` | Current reference page; historical bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `SOURCE-GAP` + identity/basis/legal/rate gaps |
| SBV central VND/USD | `2018-01-01 / 2026-08-20` | Central product label; direct EUR/VND history `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `SOURCE-GAP` + identity/basis/legal gaps |
| SBV reference rate | `2018-01-01 / 2026-08-20` | Reference-product label; direct daily bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `SOURCE-GAP` + identity/basis/legal gaps |
| SBV weekly tax cross-rate | `2018-01-01 / 2026-08-20` | Official catalogue says weekly tax-calculation product | `NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE` | `NOT_SERVED` + `BASIS_GAP` |
| ECB direct EUR/VND | `2018-01-01 / 2026-08-20` | Current roster has no VND row | `NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE` | `NOT_SERVED` + `BASIS_GAP` |
| Frankfurter unfiltered | `2018-01-01 / 2026-08-20` | VND catalogue/blend metadata; pair bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `SOURCE-GAP` + identity/basis/legal/rate gaps |
| Frankfurter `providers=ECB` | `2018-01-01 / 2026-08-20` | Provider metadata; direct VND bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `SOURCE-GAP` + identity/basis/legal/rate gaps |
| Frankfurter underlying inventory | `2018-01-01 / 2026-08-20` | Provider inventory not fully reviewed; bounds `NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `SOURCE-GAP` + identity/legal/rate gaps |
| BIS bilateral | `2018-01-01 / 2026-08-20` | USD-relative/combined-source dataset, wrong direct unit | `NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE` | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` |
| World Bank annual | `2018-01-01 / 2026-08-20` | Annual USD period-average only | `NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE` | `NOT_SERVED` + `BASIS_GAP` |
| Federal Reserve H.10 | `2018-01-01 / 2026-08-20` | Prior USD control; no direct unit | `NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE` | `NOT_SERVED` + `IDENTITY_GAP` |
| FRED DEXCHUS | `2018-01-01 / 2026-08-20` | Prior wrong-pair/USD control; no direct unit | `NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE` | `NOT_SERVED` + `IDENTITY_GAP` |
| `open.er-api` current | `2018-01-01 / 2026-08-20` | Current USD endpoint only; no history bounds | `NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE / NOT_APPLICABLE` | `NOT_SERVED` + identity/basis/legal/rate gaps |

A future qualified unit may use `COVERAGE_GAP` only after its direct identity, basis, legal, and
runtime axes pass and an owner-declared or response-backed boundary proves that the requested span
is outside the served range. No row above qualifies, so none uses `COVERAGE_GAP`.

For a future qualified daily source, a missing date is deterministic:

- an owner calendar/status that says the date was not published yields `NONPUBLICATION_RECONCILED`,
  no row, and no fatal error; the date is not shifted, filled, or fabricated;
- a publication-eligible date with no row is `missing_requested_endpoint` and fails the whole source;
- an empty, timed-out, WAF, connection, or unreconciled response is transport/schema failure, not
  zero-row `NOT_SERVED` and not `COVERAGE_GAP`; and
- unknown calendar/status evidence is unresolved and returns no series. No false absence is inferred.

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

### 3.9 `open.er-api` — current-only USD anchor is a negative control

The existing repository source contract at [`docs/sources/fx-open-er-api.md`](../sources/fx-open-er-api.md)
records the canonical current route `https://open.er-api.com/v6/latest/USD`. It returns rates keyed
as currencies per USD, derives EUR/VND by combining the USD/VND and USD/EUR fields, refreshes about
daily, and documents rate limiting. Its terms prohibit redistribution of raw data. No route was
called in this round. It therefore cannot be a direct historical EUR/VND unit, and its exact
negative disposition is `NOT_SERVED + IDENTITY_GAP + BASIS_GAP + LEGAL_GAP + RATE_POLICY_GAP`.

## 4. Legal and reuse posture

The following axes are independent and are recorded for every candidate unit:

```text
owner identity; automated access; caller-facing return; storage/cache;
redistribution; attribution; commercial use; rate/retry/pacing;
terms amendment/revocation; observation/data revision/retention
```

`PROVEN` means only that the cited primary source explicitly supports the narrow cell. `NOT_RETAINED`
means this no-probe design did not retain the answer. `CONDITIONAL` means provider terms may govern
but the exact unit is not bound. `NOT_APPLICABLE` means the axis cannot qualify the wrong product;
it is not permission.

| Unit | Owner identity | Automated access | Caller return | Storage/cache | Redistribution | Attribution | Commercial use | Rate/retry/pacing | Terms amendment/revocation | Observation/data revision/retention |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VCB EUR cash | Surface owner `PROVEN`; historical field `GAP` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| VCB EUR transfer | Surface owner `PROVEN`; historical field `GAP` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| VCB EUR sell | Surface owner `PROVEN`; historical field `GAP` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| SBV central VND/USD | Product owner `PROVEN`; direct EUR/VND field `GAP` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| SBV reference rate | Product owner `PROVEN`; direct daily field `GAP` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| SBV weekly tax cross-rate | Product owner `PROVEN`; daily market unit `NOT_APPLICABLE` | `NOT_RETAINED` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| ECB direct EUR/VND | Roster owner `PROVEN`; direct VND `NOT_SERVED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| Frankfurter unfiltered | Facade owner `PROVEN`; direct owner `GAP` | `CONDITIONAL` | `CONDITIONAL` | `CONDITIONAL` | `CONDITIONAL` | `NOT_RETAINED` | `CONDITIONAL` | `CONDITIONAL` | `NOT_RETAINED` | `NOT_RETAINED` |
| Frankfurter `providers=ECB` | Facade/provider label `PROVEN`; direct ECB/VND `GAP` | `CONDITIONAL` | `CONDITIONAL` | `CONDITIONAL` | `CONDITIONAL` | `NOT_RETAINED` | `CONDITIONAL` | `CONDITIONAL` | `NOT_RETAINED` | `NOT_RETAINED` |
| Frankfurter underlying inventory | Inventory not fully reviewed | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| BIS bilateral | Dataset owner/method `PROVEN`; requested pair wrong | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| World Bank annual | Indicator owner/basis `PROVEN`; daily pair wrong | `NOT_RETAINED` | `PROVEN annual CC BY 4.0 only` | `PROVEN annual CC BY 4.0 conditions` | `PROVEN annual CC BY 4.0 conditions` | `PROVEN attribution requirement` | `PROVEN subject to CC BY 4.0` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| Federal Reserve H.10 | Owner `PROVEN`; direct pair `GAP` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| FRED DEXCHUS | Owner `PROVEN`; direct pair `GAP` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| `open.er-api` current | Route owner/source contract `PROVEN`; historical direct unit `GAP` | `PROVEN current no-key route only` | `PROVEN current client use only` | `PROVEN cache allowed for current client` | `PROVEN raw redistribution prohibited` | `PROVEN requested attribution` | `PROVEN commercial use stated` | `PROVEN current rate limit; history NOT_APPLICABLE` | `NOT_RETAINED` | `NOT_RETAINED` |

No public/no-login/free surface receives an inferred licence. Terms amendment/revocation is kept
separate from observation/data revision/retention: a provider may revise observations without
changing terms, and terms may change without changing historical rows. A future qualification must
refresh both columns for the exact route/unit.

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
| Accessors | `rate_on()` is exact-match-only. Current facade-produced histories are annual, but `rate_for_year()` is presently exact Jan-1 sugar over `rate_on()` with no frequency guard; a manually constructed daily history can therefore return a Jan-1 point. A future authorized daily implementation must add and test explicit non-annual rejection. No runtime change is made here. |
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
   that date is recorded as `NONPUBLICATION_RECONCILED` with no row. A publication-eligible date
   with no row is `missing_requested_endpoint` and fails the whole source. Empty responses,
   unknown calendar status, and unreconciled pages also fail the whole source with no partial history;
6. `rate_on()` remains exact-match-only and a future daily implementation must make
   `rate_for_year()` reject non-annual histories.

Any future `rate_basis` field, warning tuple, public coverage result, error carrier, or provider
attempt carrier must be additive, finite, sanitized, snapshot-tested, and reviewed with annual
constructor/DataFrame/diagnostic compatibility. This source-gap packet does not add or promise one.

### 6.3 Coverage and no-false-absence

`FULL` is possible only when the provider declares or proves served bounds covering both requested
endpoints (or proves that a boundary endpoint is a provider-calendar nonpublication) and
page/count/cursor/calendar reconciliation succeeds. `QUALIFIED_PARTIAL` is possible only when a
qualified provider declares a narrower bound and all identity, basis, legal, and runtime axes still
pass; it must expose that bound and never imply requested full coverage.

`COVERAGE_GAP` is a qualified-provider coverage disposition only: it requires an owner-declared or
response-backed served boundary that is known to exclude part of the requested interval. It cannot
be inferred from a no-probe page, empty response, timeout, WAF, or missing retained rows. In this
round every unproven history remains `SOURCE-GAP` or an exact `NOT_SERVED` negative.

For a future qualified source, the exact date rule is:

```text
publication-eligible date + no row       -> missing_requested_endpoint (fatal, no series)
provider calendar/status says no publish -> NONPUBLICATION_RECONCILED (no row, not fatal)
unknown calendar/status                  -> unexplained_gap (fatal, no series)
empty/WAF/timeout/connection/unreconciled -> transport/schema failure (no absence claim)
```

No result in the last two rows may be returned as a successful empty series or as `NOT_SERVED` or
`COVERAGE_GAP`. No weekend/holiday row may be fabricated, shifted, forward-filled, backfilled,
interpolated, resampled, or synthesized through USD.

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
uses another media type must receive its own exact parser contract; generic “JSON-like” acceptance
is not allowed.

The following is an explicitly **provisional, non-public** internal classification map for the
source-gap design. It is complete for the currently named transport/response classes; a later
route-qualified design must add any provider-specific class before implementation and must not
silently map it to absence:

| Condition | Provisional internal token/outcome | Series/absence rule |
| --- | --- | --- |
| Successful validated response | `ok` | May proceed to coverage reconciliation |
| DNS/connect/reset before complete response | `connection_error` | No series; not `NOT_SERVED` |
| TLS handshake/chain failure | `tls_error` | No series; not `NOT_SERVED` |
| Timeout | `timeout` | No series; not `NOT_SERVED` |
| HTTP rate limit | `rate_limited` | No series; not `NOT_SERVED` |
| Other unexpected status | `unexpected_http_status` | No series; not `NOT_SERVED` |
| Redirect/effective-route mismatch | `redirect` or `effective_route_mismatch` | No series; not `NOT_SERVED` |
| WAF/challenge HTML | `waf_challenge` | No series; not `NOT_SERVED` |
| Body/decompressed byte ceiling | `body_limit` | No partial series |
| Zero-byte successful body | `empty_response` | No series; not `NOT_SERVED` |
| Valid schema with zero observations | `empty_result` | No series; not an absence oracle |
| Wrong/missing/malformed MIME | `mime_mismatch` | No series |
| Parse/schema/identity/basis failure | `json_parse_error`, `schema_error`, `identity_mismatch`, or `basis_mismatch` | No series |
| Duplicate/page/date reconciliation failure | `duplicate_or_overlap`, `page_reconciliation_error`, `out_of_window_date`, or `unexplained_gap` | No series |
| Publication-eligible requested date missing | `missing_requested_endpoint` | No series |
| Provider calendar/status proves nonpublication | `NONPUBLICATION_RECONCILED` | No row; not fatal; no filling |
| Atomic budget exhaustion | `budget_exhausted` | No partial series |

These names are internal design vocabulary only, not a current public API. Raw URL, query, body,
header, exception, cookie, credential, provider prose, and live rate never enter public diagnostics.
Public status/warning tokens require a separate compatibility review.

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
   attribution, commercial use, rate/retry/pacing, terms amendment/revocation, and
   observation/data revision/correction/retention;
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
- [Repository `open.er-api` source contract](../sources/fx-open-er-api.md)
- [Previously reviewed #217 primary-source note](2026-08-23-daily-cnyvnd-fx-history-source-vetting.md)

## Bottom summary

- Decision: **SOURCE-GAP CLOSURE**; no direct daily EUR/VND unit qualifies.
- Current daily chain stays empty; annual World Bank USD/VND behavior is unchanged.
- Candidate data/API dispatch: 0 logical calls, 0 physical calls, 0 page/cursor calls, 0 retries; static-document transport was not retained or measured.
- VCB/SBV lack response-backed daily identity, coverage, runtime, and reuse proof.
- ECB does not publish VND in the inspected EUR roster; cross-rate derivation is forbidden.
- Frankfurter is a blended facade with underlying-provider/legal/rate gaps, not a direct source.
- Reopen requires all identity, basis, coverage, bounded-runtime, legal, and compatibility axes.
- No RED, code, push, or close is authorized before exact design PASS.
