# Daily USD/VND history — source and API status

**Research date:** 30 August 2026 (UTC+7)<br>
**Request owner:** `quant-researcher-frontier` (internal; no public GitHub issue)<br>
**Requested window:** inclusive `2000-01-01..2026-08-30`<br>
**Disposition:** **SOURCE-GAP / CURRENT API BLOCKED** — no daily provider was qualified and no
daily capability, source registration, RED test, or production change is authorized by this note.

This is a clean-room source and API status record. It does not inspect or infer daily FX values,
turn a current/annual quote into a daily series, or treat a reachable web page as a reuse licence.
The existing annual World Bank behavior remains unchanged.

## 1. Frozen request and boundary

The frozen request is:

```python
fx.history(
    "USD",
    "VND",
    start=date(2000, 1, 1),
    end=date(2026, 8, 30),
    frequency=Frequency.DAILY,
)
```

Required semantics are response-backed observed date and rate, explicit unit and daily
frequency, provider/source identity, real coverage, bounded warnings, and documented rights,
rate-limit, and cache posture. Missing observations remain missing. Annual substitution,
interpolation, weekend/holiday fill, stale carry, credentials, keys, payment, and fabricated
coverage are prohibited. The cross-asset measurement in the originating research folder is not
an implementation or source-quality oracle; only its predeclared source-gate result is recorded
here.

Before this research I ran `docs/vnstock-blacklist.md`. The exclusion was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted source, code, endpoint map, schema, test, or behavior was opened, cited, compared,
or used. Evidence below is from official provider pages, official terms/catalogues, and the
repository's already-reviewed primary-source report. Static web research on 30 August 2026 did
not register, contact, download, accept terms, or call a provider data endpoint.

## 2. Separate status results

| Axis | Status | Exact evidence / meaning |
| --- | --- | --- |
| **Installed API** | `BLOCKED_UNSUPPORTED_FREQUENCY` | The frozen gate exits `1` before transport with `vnfin.exceptions.InvalidData: fx.history: only annual frequency is supported in v1, got 'daily'`. |
| **Current runtime chain** | `EMPTY_FOR_DAILY` | `WorldBankFXHistorySource` is the only historical source and is annual `PA.NUS.FCRF`; no daily source is registered. |
| **Daily source qualification** | `SOURCE_GAP` | No candidate has all of direct pair identity, response-backed daily observations, real requested-span bounds, legal/runtime permission, and bounded retrieval in one unit. This is “not qualified/found under the gate,” not a proof that no source exists anywhere. |
| **Returned data** | `NONE` | No daily rows, values, response body, data manifest, or coverage claim were produced or inspected. |
| **Implementation** | `NOT_AUTHORIZED` | No API/model change, source adapter, RED test, probe, credentialed path, or payment path is authorized. |

### 2.1 Frozen source-gate evidence

The evidence was read as data from the external research workspace; its test or measurement code was
not executed by this task. The immutable external evidence commit is
`b7519f985946480fa03c103732d326b0f3c94390`.

```text
/home/hungson175/dev/trading-projects/quant-trading/quant-researcher-frontier/research/2026-08-30-vnfin-usdvnd-daily-cross-asset-anatomy/
```

`RESULTS.md` is at the evidence root; the four gate artifacts are under its `tdd/` child:

| Exact artifact path | Blob identity | Retained fact |
| --- | --- | --- |
| `RESULTS.md` (root) | `10403aeb58fc315f4843d083ffd57e41f6c42365` | `SOURCE_BLOCKED / NO_DAILY_CONTRACT`; no values, replay, or economic claim. |
| `tdd/source_gate.stdout` | `c93f8e77cd4d8fff1056b0bedc7fce92644b436e` | `request=vnfin.fx.history(USD,VND,2000-01-01..2026-08-30,Frequency.DAILY)` |
| `tdd/source_gate.stderr` | `4715ea12a99e5f27386911b5db000f6acd48b86d` | Exact traceback ends with `InvalidData: fx.history: only annual frequency is supported in v1, got 'daily'`. |
| `tdd/source_gate.exit` | `d00491fd7e5bb6fa28c517a0bb32b8b506539d4d` | `1` |
| `tdd/red_exit.txt` | `0cfbf08886fca9a91cb753ec8734c84fcbe52c9f` | `2`; the intentionally failing implementation-side collection was not turned into a green implementation. |

The installed facade validates the requested frequency and raises before constructing or calling
the annual source. Therefore the exception proves the current API boundary only; it does not prove
provider non-publication.

## 3. Current vnfin behavior to preserve

The current `vnfin.fx.history()` contract is additive-only and must not be changed by this status
work:

| Existing behavior | Required preservation |
| --- | --- |
| `frequency=Frequency.ANNUAL` default | Keep the default, validation order, and exact error behavior for unsupported frequency. |
| World Bank `PA.NUS.FCRF` | Keep `source="worldbank_fx"`, annual periodicity, period-average semantics, and `VND per 1 USD` unit. |
| Annual dates | Jan-1 reference-year keys remain annual observation keys, not daily publication timestamps. |
| `rate_on()` / `rate_for_year()` | Exact lookup only; no fill, interpolation, nearest-date lookup, or daily reinterpretation. |
| Spot sources | `open_er_api` and Vietcombank remain spot/current sources, not historical fallback sources. |
| Diagnostics | Current daily request reports unsupported frequency; do not relabel it as a daily coverage success. |

The official World Bank catalogue describes `PA.NUS.FCRF` as “Official exchange rate (LCU per US$,
period average)” with **annual** periodicity and CC BY 4.0; it is not a daily USD/VND source:
[`PA.NUS.FCRF` metadata](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/PA.NUS.FCRF).

## 4. Candidate source audit

“Earliest servable date” below means the earliest date that is response-backed and qualified for
the requested **direct daily USD/VND** contract. `NOT_RETAINED` means the evidence did not prove
one; it must not be replaced with a documented market-start date or a guessed lower bound.

| Owner / route family | Direct daily USD/VND identity and real bounds | Legal, rate, cache, and redistribution posture | Status |
| --- | --- | --- | --- |
| **State Bank of Vietnam (SBV)** — candidate central-rate publication route | The official SBV publication context and the packet's headless route make this the only technically plausible central-rate candidate. The already-reviewed 23 August 2026 bounded evidence retained HTTP-200 HTML/WAF responses rather than a response-backed JSON envelope. No symbol/pair, numeric field, effective date, earliest date, latest date, page total, or full-span coverage was proven. Earliest/latest: `NOT_RETAINED`. | Publication authority proves neither automated access nor caching, storage, retention, caller-facing return, or redistribution permission. No owner-approved rate/retry policy was retained. A browser-shaped User-Agent is not a rights or reliability grant. | **`TRANSPORT_INCONCLUSIVE + LEGAL_GAP + RATE_POLICY_GAP`; not qualified.** |
| **BIS WS_XRU** — official bilateral exchange-rate statistics | The official BIS topic says daily data exist for only some reference areas and that availability varies. The prior bounded repository audit found the exact `D.VN.VND.E` key unserved while `M.VN.VND.E` was monthly end-of-period. The monthly series cannot be promoted to daily, and no daily earliest/latest VNM bound is retained. | BIS statistics terms permit reproduction with citation and no misleading endorsement/no added user charge; API access is as-is and may be limited or suspended. Exact VNM daily route, basis, and source-period contract still require proof. | **`NOT_SERVED_OR_UNPROVEN` for direct daily USD/VND; monthly is not a substitute.** |
| **ECB reference rates** — official EUR-base data | The official portal exposes daily USD/EUR and other EUR-base reference series. Its published reference roster does not establish a VND series. Direct USD/VND is therefore not served by the inspected owner roster; earliest/latest: `NOT_APPLICABLE` for the direct pair. | ECB rates are information/reference rates on working days. A USD/EUR and EUR/VND cross would be a new synthetic cross-rate and is explicitly out of scope; it would not establish direct USD/VND identity or rights for that derived series. | **`NOT_SERVED + BASIS_GAP`; no cross-rate.** |
| **Vietcombank** — official commercial-bank quote/history pages | The official page exposes cash-buy, transfer-buy, and sell quotes and labels the table “for reference only.” The repository's prior bounded date-route observations returned an empty `Data` array but were correctly not treated as historical absence. Earliest/latest daily history: `NOT_RETAINED`; full 2000-current coverage is unproven. | No explicit open-data/reuse licence, historical retention contract, or date-API rate policy is retained. Transfer is a commercial-bank quote, not an SBV central-rate basis. A one-request-per-date crawl would need a provider-approved rate and a bounded budget. | **`BASIS_GAP + LEGAL_GAP + COVERAGE_UNPROVEN + RATE_POLICY_GAP`; not qualified.** |
| **World Bank WDI** — `PA.NUS.FCRF` | Official `VNM` data are annual period-average LCU/USD, not daily. The existing source note retains a first non-null annual observation at 1983, but that is not a daily bound. | CC BY 4.0 with attribution; existing runtime-fetch-only annual behavior remains lawful under the reviewed posture. | **`NOT_SERVED` for daily; preserve annual source.** |
| **ExchangeRate-API open** — current spot route | Repository source evidence documents a current `latest/USD` route with no historical endpoint. Earliest/latest daily history: `NOT_APPLICABLE`. | Terms prohibit redistribution of raw data even though caching is permitted; no historical product may be inferred from a current refresh. | **`NOT_SERVED + REDISTRIBUTION_GAP`; never history.** |
| **Repository date-pinned currency CDN** | Existing repository research documents a per-date adapter with a maximum 1,100-day range and a known lower bound around 2 March 2024. That is neither 2000-current coverage nor a newly qualified official direct source. | No stronger owner/route/legal contract for the requested full-span history is established. | **`COVERAGE_GAP + CALL_BUDGET_GAP`; no expansion.** |

Primary pages used for the static refresh include the [BIS bilateral exchange-rate overview](https://data.bis.org/topics/XRU),
[BIS permitted-use terms](https://www.bis.org/about/legal/permitted-use-statistics), the
[ECB reference-rate catalogue](https://data.ecb.europa.eu/data/data-categories/ecbeurosystem-policy-and-exchange-rates/exchange-rates/reference-rates),
and Vietcombank's [official exchange-rate page](https://www.vietcombank.com.vn/en/To-Chuc/SMEs/KHTC---Ti-gia---SMEs).
The prior detailed primary-source audit is [`2026-08-23-daily-usdvnd-fx-history-source-vetting.md`](2026-08-23-daily-usdvnd-fx-history-source-vetting.md).

The exact route families retained in the prior audit are: SBV's candidate publication context
[`sbv591621`](https://www.sbv.gov.vn/vi/web/sbv_portal/w/sbv591621) and candidate headless route
`https://sbv.gov.vn/o/headless-delivery/v1.0/content-structures/137473/structured-contents`;
BIS `WS_XRU` keys [`M.VN.VND.E`](https://data.bis.org/topics/XRU/BIS%2CWS_XRU%2C1.0/M.VN.VND.E)
and the previously checked daily key
`https://stats.bis.org/api/v1/data/WS_XRU/D.VN.VND.E?format=csvfile`;
Vietcombank's documented date route
`https://www.vietcombank.com.vn/api/exchangerates?date=YYYY-MM-DD`; World Bank's annual
[`PA.NUS.FCRF` API](https://api.worldbank.org/v2/country/VNM/indicator/PA.NUS.FCRF?format=json);
and the existing spot route in [`fx-open-er-api.md`](../sources/fx-open-er-api.md). The route strings
are identity/provenance references, not authorization to call them in this task.

### 4.1 Why the source status is not “daily coverage gap”

An empty response, 404, HTML WAF page, current-page date, market launch date, or documentation
maximum is not a daily observation or an absence oracle. A candidate can be promoted only when a
single owner/route/version unit proves, from a valid response family and its terms:

1. direct USD/VND pair and economic basis;
2. exact date field and daily frequency semantics;
3. real first/last observed dates and the provider's non-publication calendar;
4. complete page/total reconciliation without hidden retry or unbounded fan-out;
5. finite positive rate and exact VND-per-USD unit; and
6. automated access, rate, cache/storage, retention, attribution, and caller-facing redistribution
   rights compatible with a public OSS client.

Until all six axes pass together, the status is `SOURCE_GAP`/unqualified—not a fabricated daily
series and not a claim that a provider has no data.

## 5. Future source/API design gate (not implementation authorization)

This is the design direction for a later source-qualified change. It deliberately does not freeze
unsupported provider route details or numeric budgets.

### 5.1 Qualification unit

One candidate is one owner, canonical route and version, direct USD/VND economic basis, date and
publication convention, response schema, and legal/runtime contract. A source is not qualified by
combining ECB legs, annual World Bank points, current spot quotes, or different provider calendars.
There is no daily failover chain until two independent sources qualify the **same** basis and date
semantics; a single qualified source is a single-source path for the entire requested window.

### 5.2 Required response-backed result

After a separate design PASS and later RED-first authorization, the additive API must expose at
least:

```python
fx.history(
    "USD", "VND", start=start, end=end, frequency=Frequency.DAILY
) -> FXHistory
```

Every returned result must carry response-backed `base`, `quote`, `unit="VND per 1 USD"`,
`frequency=Frequency.DAILY`, provider/source identifier, observed `date`/`rate` points, retrieval
timestamp, coverage metadata/diagnostic, and bounded sanitized warnings. The provider's exact
rate basis and unit scale must be explicit; a number with a similar magnitude is not enough.

Dates are provider observation/reference dates. `fetched_at_utc` is retrieval time only and cannot
be used as an observation, publication, first-availability, or look-ahead timestamp. If a provider
publishes a timestamp, its timezone, meaning, revision behavior, and relationship to the observed
date must be proven separately. No timezone conversion may be invented for a date-only field.

### 5.3 Missingness, coverage, and atomicity

- Return only provider observations in the inclusive requested window, strictly ascending and
  unique.
- Never emit zero, forward-fill, stale carry, interpolation, annual expansion, weekend/holiday
  rows, current-spot backfill, or cross-provider stitching.
- A provider-declared holiday/non-publication date may be absent only when the provider's calendar
  semantics are response/document-backed; otherwise the absence is unresolved, not a warning.
- A missing/unreconciled page, duplicate, invalid row, unknown gap, malformed envelope, or
  incomplete boundary fails the whole retrieval. No partial `FXHistory` is returned.
- “Coverage” must distinguish requested window, response-backed observed bounds, provider-declared
  non-publication, and unresolved transport/identity gaps. Documentation or market start dates do
  not fill these fields.

### 5.4 Legal and runtime gate

Written terms or a clearly applicable licence must cover the exact route and intended use: no-login
automation, request frequency and retries, caching/storage/retention, attribution, commercial
use, caller-facing return/redistribution in a public OSS library, and revisions. “Public,” “free,”
“for reference only,” or currently reachable is not permission. If any axis is unknown, keep the
daily chain empty and report `LEGAL_GAP`.

### 5.5 Budget and diagnostics gate

The future implementation must use one deterministic global reservation ledger, not a per-page
counter that can be exceeded by concurrency, retries, decompression, redirects, or date fan-out.
Each physical request (including an explicitly authorized retry) reserves and consumes one unit
before dispatch; a failed reservation dispatches nothing. No library retry, redirect follow, cache
read, or provider pacing rule may be assumed. Exact numeric ceilings and any rate window must be
source-specific, owner-backed, and reviewed before RED. Exhaustion returns no partial history and
records a typed budget outcome rather than a fake coverage warning.

Diagnostics must keep `unsupported_frequency`, `source_gap`, `coverage_gap`, transport failure,
identity failure, and legal failure distinct. Public warnings are a finite sanitized token set;
raw URLs, response bodies, headers, exceptions, cookies, credentials, and provider free text never
escape. A successful warning cannot hide an unresolved transport or rights gap.

## 6. Final disposition and reopen evidence

**Current source status:** no qualified daily USD/VND source.<br>
**Current API status:** deterministic annual-only rejection before network.<br>
**Current runtime:** annual World Bank only; daily chain empty.<br>
**Earliest qualified daily date:** `NOT_RETAINED` for every candidate.

Reopen requires a new source/design packet with one exact owner/route unit, response-backed identity
and bounds, legal/runtime permission, and a finite budget/diagnostic contract. Only after an exact
design PASS may a separate RED-first packet define synthetic tests; only after RED review may code
be written. This note itself authorizes no probe, credential, payment, RED, API/model change,
production code, source registration, push, or issue closure.
