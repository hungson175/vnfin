# #236 design note — Singapore macro coverage

**Date:** 17 September 2026 (+07)
**Packet:** `triage-202609171910-issue236-singapore-macro.md` at reviewer `ef81fe2`
**Public triage:** `issuecomment-5714070058`
**Source/design base:** published `origin/master` `8d450a40cd9763a58bdb85c5f125edcc18d182da`
**Phase:** `DESIGN_BLOCK_CORRECTION` -> `DESIGN_REVIEW_REQUESTED`
**Implementation status:** no RED, API/model, adapter, registration, production-code, push, or close

## Decision

Choose **`PARTIAL_PARITY / NO_NEW_SOURCE_YET`**.

All eight annual `SGP` cells have exact, technically and legally qualified World Bank WDI primary
legs. Only five complete default chains are qualified: the existing IMF fallbacks behind growth,
inflation, and unemployment are not legally cleared for an OSS automatic default.

| Indicator | Outcome | Exact primary | Observed usable non-null coverage | Boundary |
|---|---|---|---|---|
| `GDP` | `QUALIFIED_EXISTING` | `NY.GDP.MKTP.CD` | 66 annual points, 1960–2025 | current US$, USD |
| `GDP_GROWTH` | `PARTIAL` | qualified WDI `NY.GDP.MKTP.KD.ZG`; uncleared IMF `NGDP_RPCH` fallback | 65 WDI annual points, 1961–2025 | WDI leg qualifies; whole chain does not |
| `CPI` | `QUALIFIED_EXISTING` | `FP.CPI.TOTL` | 66 annual points, 1960–2025 | index level, 2010=100 metadata |
| `INFLATION` | `PARTIAL` | qualified WDI `FP.CPI.TOTL.ZG`; uncleared IMF `PCPIPCH` fallback | 65 WDI annual points, 1961–2025 | WDI leg qualifies; whole chain does not |
| `UNEMPLOYMENT` | `PARTIAL` | qualified WDI `SL.UEM.TOTL.ZS`; uncleared IMF `LUR` fallback | 35 WDI annual points, 1991–2025 | WDI leg qualifies; whole chain does not |
| `CPI_YOY` | `ROUTE_GAP + LEGAL_GAP` | candidate SingStat `M213781`, row `1` | 775 monthly periods, 1962 Jan–2026 Jul | exact identity and `Per Cent` unit; OpenAPI contract and permission lifecycle unretained |
| `POLICY_RATE` | `SEMANTICS_GAP` | none | not applicable | Singapore's policy instrument is S$NEER; no interest-rate proxy |
| `LENDING_RATE` | `QUALIFIED_EXISTING` | `FR.INR.LEND` | 44 annual points, 1978–2021 | historical aggregate only; five-year current lag |
| `DEPOSIT_RATE` | `QUALIFIED_EXISTING` | `FR.INR.DPST` | 45 annual points, 1977–2021 | historical aggregate only; five-year current lag |
| `REAL_INTEREST_RATE` | `QUALIFIED_EXISTING` | `FR.INR.RINR` | 44 annual points, 1978–2021 | historical; GDP-deflator-adjusted lending rate; five-year lag |

The product surface remains exactly:

```python
vnfin.macro.get_indicator("SGP", indicator) -> IndicatorSeries
```

No Singapore helper, report object, coverage API, enum/model change, proxy, derivation, fill, or
cross-source point stitch is justified. The disposition is **8 technically qualified WDI primary
legs / 5 qualified whole chains / 3 partial whole chains / 1 route+legal gap / 1 semantics gap**.
The complete one-row-per-cell technical and permission matrices, request receipts, legal analysis,
direct official links, and discovery-incident ledger are in
`docs/research/2026-09-17-singapore-macro-official-sources.md`.

## Existing annual route decision

Retain World Bank as the qualified primary leg for all eight annual concepts. Every WDI metadata
and observation request returned HTTP 200 `application/json;charset=utf-8` with no redirect, exact
source/code/country identities, page 1 of 1,
and `lastupdated=2026-07-13`. There were no duplicate years or interior gaps inside each non-null
bound. World Bank's exact indicator pages are marked CC BY 4.0; API v2 requires no key. Attribution
and change indication remain required, dataset/third-party exceptions prevail, numerical quota is
not retained, and the API/terms may change.

For `GDP_GROWTH`, `INFLATION`, and `UNEMPLOYMENT`, the existing IMF DataMapper fallbacks make the
**whole default chains `PARTIAL`**, even though each WDI primary leg qualifies independently. The
three exact IMF routes returned `SGP` with 52 annual points for 1980–2031. vnfin's adapter classifies
current UTC year 2026 onward as projections and `latest()` excludes them. That cutoff is an internal
conservative approximation, not provider per-point actual/estimate/forecast lineage. IMF terms
prohibit bulk automated download without permission and direct commercial reuse to a permission
request, so IMF is not legally cleared for an OSS default. Before any code, a separate API/model
decision must either legally qualify IMF or country-gate it for `SGP` before cache/transport; this
design authorizes neither option and does not describe the present whole chains as qualified.

`GDP` remains World Bank-only because IMF `NGDPD` is `USD bn` rather than the canonical current-US$
level. `CPI` remains annual World Bank-only; the exact monthly SingStat index differs in frequency
and base. The three WDI interest rates are qualified as **historical** series, not current Singapore
bank-rate capability. No staleness warning or code change is authorized in this phase.

## Monthly CPI decision

SingStat table `M213781` is the exact provider-published monthly same-month-prior-year percent-change
concept. Exact retained identity is table `M213781`, series key `1`, row label `All Items`, title
“Percent Change In Consumer Price Index (CPI) Over Corresponding Period Of Previous Year, 2024 As
Base Year, Monthly.” The route returned 200 `application/json; charset=utf-8`, no redirect, 775
unique periods from 1962 Jan through 2026 Jul, exact response `uoM="Per Cent"`, and no retained
missing marker. The envelope exposed `Data`, `DataCount`, `Message`, and `StatusCode`; the response
carried `limit="5000"` with null offset/sort/filter/range fields. Therefore a local YoY derivation
is unnecessary and remains forbidden.

It is **not registered** because all conjunctive gates did not pass:

1. the catalog is not a specification, and the actual official OpenAPI developer page returned
   only a JavaScript shell, so method/parameter/error/paging/max/version behavior is not retained;
2. route rate/byte/revision/correction behavior is not documented sufficiently;
3. the official general Terms of Use target returned 403, while the exact API Terms URL/content,
   version, and effective date were not exposed within the bounded official-page path; and
4. direct SingStat automation, caller return, cache/storage, retention/deletion, attribution,
   commercial/derivative use, redistribution, amendment, and revocation terms were not cleared.

Singapore Open Data Licence rights on an exact data.gov.sg dataset cannot be transferred to this
direct SingStat route. The outcome is therefore `ROUTE_GAP + LEGAL_GAP`, not merely a legal gap.
Reopen only with an exact official licensed dataset/route plus unit, stable
row-key, missingness, correction, pagination, runtime-limit, and caller-lifecycle proof.

`M213751` is a technically exact non-seasonally-adjusted monthly CPI index candidate; `M213752` is
seasonally adjusted and rejected as the default; `M213811` is annual YoY and rejected for the
monthly cell. None is a silent failover for the annual WDI CPI contract.

## Singapore monetary-policy boundary

The `POLICY_RATE` cell remains `SEMANTICS_GAP`. MAS uses an exchange-rate-centred framework and
expresses stance through the S$NEER band's slope, width, and centre; the basket and band are
undisclosed ([MAS offering circular, policy-framework discussion](https://www.mas.gov.sg/-/media/mas/sgs/sgs-announcements-pdf/bonds-pdf/green-sgs-infrastructure-and-syndication/offering-circular.pdf)).
S$NEER is an exchange-rate variable, not a rate. MAS's domestic-interest-rate page identifies SORA
as a market benchmark, not a policy target
([MAS domestic interest rates / SORA](https://eservices.mas.gov.sg/Statistics/dir/DomesticInterestRates.aspx)).

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

The discovery-query plan was breached more severely than the blocked design reported: the whole
team issued **72 query strings in 19 dispatches** against the declared 6/6 cap. The first count of
25/7 omitted 47/12 delegated use. The exact delegated strings, official-result mapping, sanitized
private-log locators, cause analysis, and claim reconciliation are committed in
`docs/research/2026-09-17-singapore-macro-search-ledger.md`. The orchestrator's exact 25 strings are
`NOT_RETAINED` and support no claim. All retained exact strings carried the blacklist exclusion;
one irrelevant third-party listing was not opened or used. Only direct official pages and bounded
exact probes support the design. Logged official-document navigation also exceeded its reservation
at least 116 logical URL-open actions against 18; underlying physical HTTP count is
`NOT_RETAINED`.

Cause: the counter lived in the orchestrator narrative rather than one atomic team ledger,
delegates received no explicit reservation, and multi-query batches obscured logical use. Future
research is fail-closed: before any search, the parent must atomically verify
`used_queries + batch_size <= logical_cap` and `used_dispatches + 1 <= dispatch_cap`; delegates
default to zero allowance, failures do not restore capacity, and no rollover is allowed. The
correction made zero search queries. The incidents are presented for reviewer ruling, not
normalized away; the bounded provider probes were unaffected.

## Deferred RED/build gate

No RED or production code is authorized. If the reviewer later approves a qualified new source,
the separate build packet must cover this complete matrix:

1. Parameterize all eight WDI primary legs: exact request country/code, exact returned identity,
   canonical unit/currency/frequency, finite observations, ascending unique dates, and bounds.
2. Adversarially reject WDI wrong country/code, null/malformed/non-finite/boolean values, empty or
   out-of-window results, interior gaps where forbidden, conflicting duplicates, revisions, and
   stale-rate overclaims.
3. For WDI failure on the three partial cells, exercise the exact IMF codes/`SGP`/annual-percent
   paths; prove there is no IMF GDP substitution and do not enable these fallbacks for `SGP` until
   the separate legal-or-country-gate decision passes.
4. Freeze the 2026 IMF projection boundary: current-year onward warning/projection flags and
   `latest()` exclusion must remain exact.
5. Prove semantic/unit/frequency mismatch cannot stitch or fail over between WDI, IMF, SingStat,
   MAS, or data.gov observations.
6. Default `SGP/CPI_YOY` must make zero source/cache/HTTP attempts while its route/legal gates fail.
7. Default `SGP/POLICY_RATE` must likewise make zero attempts and reject every rate proxy.
8. A country-aware custom source with truthful support may serve either missing SGP cell; a custom
   source whose country hook returns false must be skipped before cache/transport.
9. A legacy/hookless custom source remains eligible, preserving backward compatibility.
10. VNM policy-rate routing plus USA and other-country behavior remain unchanged, including the
    existing VNM-only DBnomics guard.
11. If SingStat is later approved, pin exact GET/table/row/label/`Per Cent`/monthly day-1/base,
    envelope, MIME/final host/redirect/auth/paging/size behavior, missing markers, malformed values,
    duplicates, corrections, empty/out-of-window results, and no local YoY derivation.
12. Use synthetic committed fixtures and injected HTTP only; keep docs/source terms/warnings/API
    snapshot synchronized; assert no live rows, keys, or secrets; run the VNStock-blacklist
    clean-room scan, full suite, and wheel/sdist build on the merged tree.

## Lifecycle and next actor

- Intake receipt: `56fa8457`; packet `ef81fe2`; public anchor `issuecomment-5714070058`.
- Clean base: `8d450a40cd9763a58bdb85c5f125edcc18d182da`.
- Backlog intake: `7d7bf29e069967dca130c8b71bd7970da25ad85f`.
- Pre-transport plan: `945c981bf14936aec77e380c8e8f4d888786f32b`.
- Design-block correction mini-budget: `64706f4de916f823c9e4ef14fc90e7eff588c610`.
- Blocked design target: `5bbdec51841c374c9d454fdcc3b36ec846d690d6`; delivery
  `9b4c8f76`; reviewer commit `4890a84`; report
  `review-202609171937-issue236-design-BLOCK.md`.
- Historical correction actor: `vnfin-oss` (B1–B6 documents only; no RED/code).
- At the corrected exact-SHA handoff, current actor becomes `vnfin-oss-reviewer`; `vnfin-oss`
  waits for the verdict. The reviewer should fan out its own source/legal/API reviewers as required.
- No implementation, push, issue close, release, or capability claim follows without explicit
  reviewer authorization.

## Bottom summary

- Eight WDI primary legs are exact; five whole chains qualify and three IMF-fallback chains are `PARTIAL`.
- Five non-rate WDI legs reach 2025; lending/deposit/real-interest stop in 2021 and are historical-only.
- SingStat `M213781` is exact monthly CPI YoY in `Per Cent` but remains `ROUTE_GAP + LEGAL_GAP`.
- `POLICY_RATE` stays unsupported: Singapore's S$NEER framework has no honest interest-rate equivalent.
- Public API/model and source order stay unchanged; no new source, RED, code, snapshot, push, or close.
- Initial provider probe budget passed (26/34); correction used 3/4 actions and zero searches/retries/redirects.
- Search use was 72 queries/19 dispatches vs 6/6; the committed incident ledger and guard await reviewer ruling.
- Expansion ranking is trade, money supply, reserves, real retail sales, industrial production, then FX/S$NEER.
- Need from reviewer: exact-SHA design verdict and, if any subset passes, a separate API/model + RED authorization.
