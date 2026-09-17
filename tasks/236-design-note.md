# #236 design note — Singapore macro coverage

**Date:** 17 September 2026 (+07)
**Packet:** `triage-202609171910-issue236-singapore-macro.md` at reviewer `ef81fe2`
**Public triage:** `issuecomment-5714070058`
**Source/design base:** published `origin/master` `8d450a40cd9763a58bdb85c5f125edcc18d182da`
**Phase:** `SOURCE_DESIGN` -> `DESIGN_REVIEW_REQUESTED`
**Implementation status:** no RED, API/model, adapter, registration, production-code, push, or close

## Decision

Choose **`PARTIAL_PARITY / NO_NEW_SOURCE_YET`**.

Eight of the ten requested `SGP` cells are already honestly served by the generic World Bank WDI
path. Exact bounded probes returned the requested Singapore and indicator identities:

| Indicator | Outcome | Exact primary | Observed usable non-null coverage | Boundary |
|---|---|---|---|---|
| `GDP` | `QUALIFIED_EXISTING` | `NY.GDP.MKTP.CD` | 66 annual points, 1960–2025 | current US$, USD |
| `GDP_GROWTH` | `QUALIFIED_EXISTING` | `NY.GDP.MKTP.KD.ZG` | 65 annual points, 1961–2025 | real annual growth % |
| `CPI` | `QUALIFIED_EXISTING` | `FP.CPI.TOTL` | 66 annual points, 1960–2025 | index level, 2010=100 metadata |
| `INFLATION` | `QUALIFIED_EXISTING` | `FP.CPI.TOTL.ZG` | 65 annual points, 1961–2025 | annual consumer-price change % |
| `UNEMPLOYMENT` | `QUALIFIED_EXISTING` | `SL.UEM.TOTL.ZS` | 35 annual points, 1991–2025 | modeled ILO estimate % |
| `CPI_YOY` | `LEGAL_GAP` | candidate SingStat `M213781`, row `1` | 775 monthly periods, 1962 Jan–2026 Jul | exact provider-published concept, but terms/stable contract/unit evidence incomplete |
| `POLICY_RATE` | `SEMANTICS_GAP` | none | not applicable | Singapore's policy instrument is S$NEER; no interest-rate proxy |
| `LENDING_RATE` | `QUALIFIED_EXISTING` | `FR.INR.LEND` | 44 annual points, 1978–2021 | historical aggregate only; five-year current lag |
| `DEPOSIT_RATE` | `QUALIFIED_EXISTING` | `FR.INR.DPST` | 45 annual points, 1977–2021 | historical aggregate only; five-year current lag |
| `REAL_INTEREST_RATE` | `QUALIFIED_EXISTING` | `FR.INR.RINR` | 44 annual points, 1978–2021 | historical; GDP-deflator-adjusted lending rate; five-year lag |

The product surface remains exactly:

```python
vnfin.macro.get_indicator("SGP", indicator) -> IndicatorSeries
```

No Singapore helper, report object, coverage API, enum/model change, proxy, derivation, fill, or
cross-source point stitch is justified. The complete one-row-per-cell technical and permission
matrices, request receipts, legal analysis, and direct official links are in
`docs/research/2026-09-17-singapore-macro-official-sources.md`.

## Existing annual route decision

Retain World Bank as primary for all eight annual concepts. Every WDI metadata and observation
request returned HTTP 200 JSON with no redirect, exact source/code/country identities, page 1 of 1,
and `lastupdated=2026-07-13`. There were no duplicate years or interior gaps inside each non-null
bound. World Bank's exact indicator pages are marked CC BY 4.0; API v2 requires no key. Attribution
and change indication remain required, dataset/third-party exceptions prevail, numerical quota is
not retained, and the API/terms may change.

For `GDP_GROWTH`, `INFLATION`, and `UNEMPLOYMENT`, retain the existing IMF DataMapper fallback in
its current position and semantics; do not promote it. The three exact routes returned `SGP` with
52 annual points for 1980–2031. vnfin's adapter classifies current UTC year 2026 onward as
projections and `latest()` excludes them. That cutoff is an internal conservative approximation,
not provider per-point actual/estimate/forecast lineage. IMF terms prohibit bulk automated download
without permission and direct commercial reuse to a permission request, so this design does not
assert a new OSS legal qualification for IMF. World Bank primary qualification is independent.

`GDP` remains World Bank-only because IMF `NGDPD` is `USD bn` rather than the canonical current-US$
level. `CPI` remains annual World Bank-only; the exact monthly SingStat index differs in frequency
and base. The three WDI interest rates are qualified as **historical** series, not current Singapore
bank-rate capability. No staleness warning or code change is authorized in this phase.

## Monthly CPI decision

SingStat table `M213781` is the exact provider-published monthly same-month-prior-year percent-change
concept. Exact retained identity is table `M213781`, series key `1`, row label `All Items`, title
“Percent Change In Consumer Price Index (CPI) Over Corresponding Period Of Previous Year, 2024 As
Base Year, Monthly.” The route returned 200 `application/json; charset=utf-8`, no redirect, 775
unique periods from 1962 Jan through 2026 Jul, and no retained missing marker. Therefore a local YoY
derivation is unnecessary and remains forbidden.

It is **not registered** because all conjunctive gates did not pass:

1. the advertised catalog/OpenAPI URL returned HTML rather than a machine-readable contract;
2. the exact `uoM` response value was not retained in the sanitized receipt;
3. route paging/rate/byte/revision/correction behavior is not documented sufficiently; and
4. direct SingStat automation, caller return, cache/storage, retention/deletion, attribution,
   commercial/derivative use, redistribution, amendment, and revocation terms were not cleared.

Singapore Open Data Licence rights on an exact data.gov.sg dataset cannot be transferred to this
direct SingStat route. Reopen only with an exact official licensed dataset/route plus unit, stable
row-key, missingness, correction, pagination, runtime-limit, and caller-lifecycle proof.

`M213751` is a technically exact non-seasonally-adjusted monthly CPI index candidate; `M213752` is
seasonally adjusted and rejected as the default; `M213811` is annual YoY and rejected for the
monthly cell. None is a silent failover for the annual WDI CPI contract.

## Singapore monetary-policy boundary

The `POLICY_RATE` cell remains `SEMANTICS_GAP`. MAS uses an exchange-rate-centred framework and
expresses stance through the S$NEER band's slope, width, and centre. The basket and band are
undisclosed. S$NEER is an exchange-rate variable, not a rate.

Do not relabel any of these as `POLICY_RATE`:

- SORA or compounded SORA (market transaction benchmarks);
- SIBOR/interbank or commercial-bill rates (some discontinued/historical);
- standing-facility borrowing/deposit rates (operational facilities without retained target-rate
  semantics);
- MAS Bills, SGS repo, auction yields, or sovereign yields; or
- lending/deposit rates.

No MAS transport was dispatched because no exact canonical concept was selected. Preserve the
VNM-only DBnomics `FPOLM_PA` guard before cache/transport. An official S$NEER primitive, if later
qualified, needs a separately reviewed exchange-rate model and must not reuse `POLICY_RATE`.

## Exact API/model audit and preserved invariants

The ten enum values and current public primitive already exist. No additive public surface is
needed for the eight annual cells. Current `SGP/CPI_YOY` and `SGP/POLICY_RATE` have no eligible
default source and fail before cache/transport with zero attempts.

Preserve:

- World Bank -> IMF DataMapper -> DBnomics source order;
- exact canonical-unit filtering, followed by country eligibility before cache/transport;
- World Bank exact returned SGP/code guards and existing IMF nested code/SGP guard;
- frozen `IndicatorSeries` with ascending unique plain dates, finite values, source, `unit`,
  `value_unit`, currency, frequency, projection boundary, warnings, and UTC retrieval time;
- GDP/CPI positive and unemployment 0–100 value guards;
- `latest()` excluding IMF projections and no actual/projection fabrication;
- no point stitching between World Bank, IMF, SingStat, MAS, or data.gov.sg;
- cache off and source retries off by default; and
- existing VNM/USA/other-country/custom-source behavior and public snapshot.

A future SingStat source could fit the existing result model only after it proves exact table and
row identity, monthly period parsing to day 1, canonical `%`, source ownership/operator, revision
and missingness semantics, and the full legal/runtime gates. This is a compatibility observation,
not an API decision or build authorization.

## Additional primitive ranking — design proposals only

The following are not approved enum/model work:

1. **Merchandise trade** — high value/evidence; exact monthly data.gov candidate, with a 1999
   classification break that must remain explicit.
2. **Money supply** — high value/evidence; exact monthly candidate, but a July 2021 reporting and
   DBU/ACU structural break forbids silent stitching to the discontinued series.
3. **Official reserves** — medium-high value/high evidence; monthly end-period stock with a May 1999
   valuation break.
4. **Real retail sales** — medium-high value/high evidence but currently lagged; prefer
   seasonally-adjusted chained-volume index over nominal current prices.
5. **Industrial production** — high value but current evidence is stale through December 2019;
   find a current exact series/base first.
6. **Official FX / S$NEER** — high policy value but low legal/route evidence; bilateral MAS FX is
   Refinitiv-derived and S$NEER mechanics are undisclosed.

Each needs a separate source/legal/model gate and reviewer authorization before RED.

## Qualification accounting and disclosed deviation

The pre-transport provider plan was committed at `945c981`. Actual provider use was 26/34 logical
and 26/34 physical requests: 16 World Bank, 3 IMF, 7 SingStat, 0 MAS, 0 data.gov.sg. All dispatched
requests were sequential, status 200, zero-retry, and zero-redirect; 1,090,218 bytes were received,
within local ceilings. No provider rows or live response bodies are committed.

The discovery-query plan was breached: 25 query strings in 7 search dispatches were issued against
the declared 6/6 cap. All carried the exclusion and official-domain intent, and only direct official
pages support the note. One irrelevant third-party listing result was not opened or used. The
provider budget and exact probes were unaffected. This is explicitly presented for reviewer ruling,
not normalized away.

## Deferred RED/build gate

No RED or production code is authorized. If the reviewer later approves a qualified new source,
the separate build packet must require at least:

1. exact request/returned `SGP`, table id, row key and label; no display-position selection;
2. exact method/params/status/MIME/final host/redirect/auth/pagination/size behavior;
3. exact `%`, monthly cadence, day-1 dates, base/reference and same-month-prior-year semantics;
4. missing markers, nulls, booleans, malformed/non-finite values, empty and out-of-window rows;
5. identical/conflicting duplicates, revisions/corrections and current-lag behavior;
6. no local CPI derivation, proxy, fill, annual/monthly substitution, or cross-source point stitch;
7. `SGP/POLICY_RATE` still rejected before cache/transport and VNM route unchanged;
8. source failover only within identical concept/unit/frequency semantics;
9. offline synthetic fixtures only, injected HTTP, no live rows/keys/secrets;
10. docs, source terms, diagnostics/warnings, API snapshot, packaging, wheels/sdist and full suite in
    lockstep.

## Lifecycle and next actor

- Intake receipt: `56fa8457`; packet `ef81fe2`; public anchor `issuecomment-5714070058`.
- Clean base: `8d450a40cd9763a58bdb85c5f125edcc18d182da`.
- Backlog intake: `7d7bf29e069967dca130c8b71bd7970da25ad85f`.
- Pre-transport plan: `945c981bf14936aec77e380c8e8f4d888786f32b`.
- Current actor: `vnfin-oss`; next actor: `vnfin-oss-reviewer`.
- Next action: review this exact committed source/API design and return a design verdict. The
  reviewer should fan out its own source/legal/API reviewers as required.
- No implementation, push, issue close, release, or capability claim follows without explicit
  reviewer authorization.

## Bottom summary

- Eight of ten Singapore macro cells already work through exact World Bank WDI routes.
- The first five annual cells reach 2025; lending/deposit/real-interest stop in 2021 and are historical-only.
- SingStat `M213781` is the exact monthly CPI YoY candidate but remains a legal/contract/unit-evidence gap.
- `POLICY_RATE` stays unsupported: Singapore's S$NEER framework has no honest interest-rate equivalent.
- Public API/model and source order stay unchanged; no new source, RED, code, snapshot, push, or close.
- Provider probe budget passed (26/34, zero retry/redirect); discovery search cap breach is disclosed for ruling.
- Expansion ranking is trade, money supply, reserves, real retail sales, industrial production, then FX/S$NEER.
- Need from reviewer: exact-SHA design verdict and, if any subset passes, a separate API/model + RED authorization.
