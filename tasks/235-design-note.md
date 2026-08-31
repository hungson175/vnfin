# #235 design note — North America five-economy macro cohort

**Date:** 31 August 2026 (+07)
**Packet:** `tasks/235-north-america-macro-cohort-spec.md` at reviewer `acbbb82`
**Public triage:** `issuecomment-5477977514`
**Source/design base:** published `origin/master` `472cfe6d42ba43ab535a2ff676220896d5aaaacd`
**Phase:** `SOURCE_DESIGN` → `REVIEW_REQUESTED`
**Implementation status:** no RED, API/model, source-registration, production-code, push, or close

## Decision

Choose **`PARTIAL_COHORT`** as the documentation/design disposition. The current library already has
response-backed Canada World Bank behavior for five annual cells from the approved #200 work,
bounded older USA evidence for three annual cells, and a separate one-year GDP ranking observation
for each frozen member in the accepted packet. Thirty-eight cells remain unprobed and the USA
monthly policy-rate cell has an explicit semantics problem. No new source is qualified for an
API/RED extension decision by this note.

The product surface remains exactly:

```python
vnfin.macro.get_indicator(country_iso3, indicator) -> IndicatorSeries
```

Do not add a ranking API, cohort/report object, batch convenience API, dynamic membership lookup,
country-specific branch, new enum member, source registration, coverage model, or cross-provider
stitch. The 5 × 10 table is documentation/test scope. A future design that wants to promote a cell
must satisfy every conjunctive source, identity, coverage, legal, and budget gate in this note and
then obtain a separate API/model and RED decision.

## Frozen scope

Geography is UN M49 North America `003`, intersected with UN Member States. The canonical strict
common-year cohort is:

```text
USA, CAN, MEX, CUB, DOM
```

It is ranked only by World Bank `NY.GDP.MKTP.CD` GDP in current US dollars using the accepted
packet's frozen common year 2020. This design does not independently prove that no later common year
exists: 2021–2024 were not independently retained or audited, and the query is reproducible ranking
context only. The 2025 available-case `USA/CAN/MEX/DOM/GTM` result is an explicitly incomplete appendix; it
cannot replace Cuba, become runtime membership, or be compared as if all eligible countries had a
2025 observation. The full source evidence and official links are in
`docs/research/2026-08-31-north-america-five-economy-macro-coverage.md`.

The accepted packet's upstream ranking evidence is retained separately at
`acbbb82:docs/research/2026-08-31-issue235-north-america-macro-cohort.md` (blob
`621545ca505ff6234cad32b9be7989d5e5add426`), observed 2026-08-31. Its official 2020 and incomplete
2025 WDI GDP responses are ranking-only evidence: they bind returned country/code/date/value/unit
for the GDP observation, but do not establish a full series cell or activate the future observation
plan.

The ten audited indicators are:

```text
GDP, GDP_GROWTH, CPI, INFLATION, UNEMPLOYMENT,
CPI_YOY, POLICY_RATE, LENDING_RATE, DEPOSIT_RATE, REAL_INTEREST_RATE
```

The source report contains 50 independent rows. Its status grid is reproduced here so the design
outcome is explicit and reviewable:

| Country | GDP | GDP_GROWTH | CPI | INFLATION | UNEMPLOYMENT | CPI_YOY | POLICY_RATE | LENDING_RATE | DEPOSIT_RATE | REAL_INTEREST_RATE |
|---|---|---|---|---|---|---|---|---|---|---|
| USA | `PARTIAL` | `NOT_PROBED` | `PARTIAL` | `PARTIAL` | `NOT_PROBED` | `NOT_PROBED` | `SEMANTICS_GAP` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` |
| CAN | `PROVEN_EXISTING` | `PROVEN_EXISTING` | `PROVEN_EXISTING` | `PROVEN_EXISTING` | `PROVEN_EXISTING` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` |
| MEX | `PARTIAL` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` |
| CUB | `PARTIAL` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` |
| DOM | `PARTIAL` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` | `NOT_PROBED` |

Counts are **5 `PROVEN_EXISTING`, 6 `PARTIAL`, 1 `SEMANTICS_GAP`, and 38 `NOT_PROBED`**. The
`PROVEN_EXISTING` label means the existing public source path returned the exact Canada concept
in the retained #200 live summary; it does not promote the unretained date bounds to a complete
2018/current or 1960/current coverage claim. `PARTIAL` means USA GDP/CPI/INFLATION have bounded
older evidence and MEX/CUB/DOM GDP have one-year 2020 ranking evidence; none is a complete cell
qualification. USA unemployment is `NOT_PROBED` because its older broad statement lacks an exact
retained per-cell response.

## Source and semantic decision

### Annual World Bank family

The canonical annual provider is World Bank WDI, with these exact concepts:

| Indicator | Code | Frequency | Unit/currency | Meaning and boundary |
|---|---|---|---|---|
| `GDP` | `NY.GDP.MKTP.CD` | annual | `current US$` / `USD` | nominal GDP level; no PPP or constant-price replacement |
| `GDP_GROWTH` | `NY.GDP.MKTP.KD.ZG` | annual | `%` / none | real GDP growth, not nominal GDP |
| `CPI` | `FP.CPI.TOTL` | annual | `index` / none | CPI level, not inflation |
| `INFLATION` | `FP.CPI.TOTL.ZG` | annual | `%` / none | CPI YoY inflation, not CPI level |
| `UNEMPLOYMENT` | `SL.UEM.TOTL.ZS` | annual | `%` / none | unemployment share of labour force; retain 0–100 validation |
| `LENDING_RATE` | `FR.INR.LEND` | annual | `%` / none | aggregate lending rate, not policy rate |
| `DEPOSIT_RATE` | `FR.INR.DPST` | annual | `%` / none | aggregate deposit rate, not a tenor curve |
| `REAL_INTEREST_RATE` | `FR.INR.RINR` | annual | `%` / none | real interest rate; valid negative values remain possible |

Route template, for a future exact observation only:

```text
GET https://api.worldbank.org/v2/country/{ISO3}/indicator/{CODE}
    ?format=json&per_page={N}&date={Y1}:{Y2}
```

The exact future one-call route is:

```text
GET https://api.worldbank.org/v2/country/USA;CAN;MEX;CUB;DOM/indicator/NY.GDP.MKTP.CD;NY.GDP.MKTP.KD.ZG;FP.CPI.TOTL;FP.CPI.TOTL.ZG;SL.UEM.TOTL.ZS;FR.INR.LEND;FR.INR.DPST;FR.INR.RINR?date=1960:2025&format=json&per_page=20000
```

This binds `route_version=v2`, `method=GET`, one logical reservation, and one physical
dispatch with zero retries; no extra source parameter is assumed. Its response contract is one JSON
envelope `[metadata, observations]` with `page=1`, `pages=1`, `per_page=20000`, and `total=2640`,
covering every `(countryiso3code, indicator.id, date)` position for five countries, eight concepts,
and 66 years, including nulls. Each row must return an allowed country code, exact indicator code,
four-digit date, and provider value/unit; unique keys and the declared total must reconcile. A
missing/null position stays missing. Any page/total mismatch, identity mismatch, bad MIME, redirect,
byte exhaustion, or late failure invalidates the whole observation. The route is design evidence,
not a dispatch.

The provider must return the requested `countryiso3code` and exact `indicator.id`; the route's
syntactic validity is not an observation. The existing adapter's annual output has Jan-1 dates,
`frequency=annual`, `fetched_at_utc` as retrieval time, and no projection boundary. A provider
response that does not retain actual/estimate/projection semantics cannot be used to invent them.

### Monthly DBnomics/IMF family

The current map has only `USA` for the two monthly concepts:

```text
GET https://api.db.nomics.world/v22/series/IMF/IFS/M.US.PCPI_PC_CP_A_PT?observations=1
GET https://api.db.nomics.world/v22/series/IMF/IFS/M.US.FPOLM_PA?observations=1
```

`CPI_YOY` means monthly CPI percentage change versus the same month in the prior year and remains
separate from annual WDI `INFLATION`. `POLICY_RATE` is only a monetary-policy-related rate unless
the exact national authority/concept is proved. The current display name
`Policy Rate (SBV refinancing-rate proxy, IMF IFS FPOLM_PA)` is Vietnam-specific and cannot be
returned for any North American country. USA `POLICY_RATE` is therefore `SEMANTICS_GAP`.

For `CAN/MEX/CUB/DOM`, no exact DBnomics/IMF country/concept dimension response is retained. A
candidate `M.{CC}.{CONCEPT}` template is not a qualified route. The four countries remain
`NOT_PROBED`; no annual rate or national-central-bank value may fill a monthly cell.

### Fallback and model boundary

The existing IMF DataMapper fallback can carry annual `GDP_GROWTH`, `INFLATION`, and
`UNEMPLOYMENT`, but WEO may mix projections with history. Its different codes, projection boundary,
terms, and returned identity remain separate. The existing unit pre-filter and source ordering are
not changed. A future implementation must never combine World Bank, IMF WEO, and DBnomics points to
make a complete-looking cell.

`IndicatorSeries` stays frozen with `(date, value)` points, `source`, `unit`, `value_unit`,
`currency`, `frequency`, `projection_from_year`, `fetched_at_utc`, and `warnings`; its
`to_dataframe()` shape and attrs remain unchanged. No #235 coverage diagnostic or cache is added.
Existing docs drift (`docs/api.md` omits `CPI`; the DBnomics source guide overstates CPI routing) is
recorded for a later approved docs correction, not changed in this packet.

## Evidence and legal gate

Every cell requires a separate retained tuple:

```text
(owner, route_operator, route_version, method, concept/code, requested_identity,
returned_identity, status, complete_mime, redirect_final_host, auth/session,
frequency, unit/currency/semantics, actual_or_projection,
provider_declared_bounds, observed_count_and_bounds, nulls/gaps/duplicates,
revision/correction/current_lag, terms_version/effective_date,
automation, caller_return, cache/storage, retention/deletion,
attribution, commercial/derivative_use, redistribution, amendment, revocation)
```

No field is filled from a neighbouring country, indicator, provider, or generic route description.
The research matrix gives every one of its 50 rows a cell-local tuple for `terms_version`,
`terms_effective_date`, `automation`, `caller_return`, `cache/storage`, `retention/deletion`,
`attribution`, `commercial/derivative_use`, `redistribution`, `amendment`, and `revocation`. The
technical behavior fields describe the existing adapter only; they are never permission grants.
`NOT_RETAINED`, `NOT_CLEARED`, and `NO_NEW_GRANT` are explicit cell outcomes, not inherited global
assumptions, and remain distinct from zero, null, empty, denied, or permission granted.

- World Bank public licensing defaults for World Bank-produced open datasets to CC BY 4.0 with
  attribution, while its public licensing page warns that dataset-specific and third-party
  restrictions can apply. Existing current WDI behavior is retained; no new grant is asserted.
- DBnomics is an operator and the IFS data is IMF-owned. The DBnomics IMF page links to IMF terms;
  ODbL/operator context does not by itself grant redistribution of upstream IMF rows. No monthly
  extension is legally cleared in this note.
- No key, login, cookie, payment, or private credential path is accepted. No raw provider body,
  header, value, or dataset is bundled. A future rights decision must cover runtime retrieval,
  caller return, cache/storage, retention, attribution, commercial/derivative use, redistribution,
  amendment, and revocation for the exact route.

## Bounded observation plan (written, not activated)

The following is a future finite plan, not a #235 probe authorization. This builder made no
post-intake #235 cell-audit provider dispatch; the upstream ranking response is separately bound
as ranking-only evidence. The plan's atomic reservations are deterministic: reserve a unique logical candidate before opening
transport; increment physical usage only when a request is dispatched; retries are always zero; on
any failed reservation or exhausted budget, do not dispatch or fall through to an unreserved source.
A late failure invalidates the entire observation and releases no partial result to callers.

### World Bank reservation

- Reserve exactly one logical / one physical dispatch with zero retries for the semicolon-separated
  multi-country/multi-indicator URI above, covering five frozen countries × eight WDI concepts over
  `1960:2025`; maximum envelope `5 × 8 × 66 = 2,640` country-indicator-year positions including
  nulls.
- One page is required (`per_page=20000`, `page=1`, `pages=1`, `total=2640`); sequential,
  25-second timeout, zero retry, no cookies/session/credentials. Every response identity and unique
  key must reconcile to the exact 2,640-position envelope or the reservation fails closed.
- Redirects must preserve the owner host; complete MIME, status, `page/pages/per_page/total`, exact
  returned identities, and the whole response byte ledger are retained only as sanitized metadata.
- Project safety ceilings are `4 MiB` compressed and `32 MiB` decompressed per response. These are
  fail-closed guard values, not evidence that the provider permits a size; because source-backed
  byte limits were not retained in this static pass, this reservation is **not dispatched**.

### DBnomics/IMF reservations

- At most eight logical / eight physical candidate observations: `CAN/MEX/CUB/DOM ×
  (CPI_YOY, POLICY_RATE)`, one sequential request each, zero retries, 25-second timeout, no
  pagination unless separately budgeted.
- Exact official dimensions and applicable terms must be established before a request. A working
  series URL cannot establish national policy-rate identity or redistribution permission.
- Project safety ceilings are `1 MiB` compressed and `8 MiB` decompressed per response; they are
  fail-closed guards, not source limits. No source-backed byte/reuse receipt exists, so none of
  these eight reservations is dispatched.

**Total reservation ceiling:** 9 logical / 9 physical, zero retries. Any timeout, HTML/WAF, bad
MIME, unexpected redirect, pagination/total mismatch, byte exhaustion, identity conflict, or
incomplete legal axis yields no series and no partial coverage claim.

## Deferred API/RED/release matrix

No RED is authorized by this design. After a design PASS, a separate API/model decision must decide
whether any source-qualified cell can fit the unchanged primitive. Only then may reviewer-authorized
RED tests be written, using synthetic offline fixtures only:

1. 40 World Bank cell cases (`5 × 8`) against the exact semicolon-separated multi-indicator route
   and its `date=1960:2025&format=json&per_page=20000` contract, with request/response country and
   indicator identity, unit/currency/frequency, Jan-1 dates, bounds, nulls, ordering, exact
   `page/pages/per_page/total`, one-dispatch behavior, and no country-specific branch.
2. Each future-qualified DBnomics country/concept with exact IMF country code, monthly periods,
   country-neutral identity, source/operator attribution, no SBV-label leakage, and unsupported
   countries failing before dispatch.
3. Malformed caller/provider identity, MIME/status/redirect/TLS/WAF/timeout/rate/byte/cache,
   duplicate/conflicting dates, missing/naive metadata, non-finite/bool/out-of-range values, bad
   projection boundaries, and out-of-window rows.
4. Full/partial/not-served/unknown coverage, null-year and current-lag semantics, revision, empty
   versus failure, page/total mismatch, late failure, atomic no-partial behavior, and deterministic
   budget reservation/exhaustion.
5. Existing VNM/USA/CAN behavior, unit filtering, source order, IMF projection handling, FRED BYOK
   isolation, no network in offline tests, docs/API/units/skill/CHANGELOG changes only if a later
   public API changes, full pytest, isolated wheel/sdist, and exact path/object/ancestry/security
   gates.

No test may require every cell to succeed. Tests must preserve the documented gaps.

## Reopen criteria

A cell moves from `NOT_PROBED`/`PARTIAL`/`SEMANTICS_GAP` only when one exact retained route set
passes all applicable axes together:

1. owner, operator, route/version/method, and exact provider concept are bound;
2. returned country and concept identity, frequency, unit/currency, level/rate/growth semantics,
   and actual/projection status are response-backed;
3. status, complete MIME, owner-preserving redirect, TLS/session/auth, pagination/totals, and
   compressed/decompressed byte limits are bounded;
4. provider-declared and observed count/first/last dates, null/interior gaps, duplicate/conflict,
   current lag, revision/correction and calendar semantics reconcile;
5. terms version/effective date expressly cover automation, caller return, cache/storage,
   retention/deletion, attribution, commercial/derivative use, redistribution, amendment, and
   revocation;
6. logical/physical/retry/rate/concurrency/backoff/byte reservations are deterministic and atomic;
   and
7. a separate API/model decision and RED authorization approves any public change.

For monthly non-USA cells, official IMF dimensions and exact national concept authority are
additional gates. For USA `POLICY_RATE`, the SBV proxy display must be removed/replaced by a
country-correct response-backed concept before qualification. The API/model decision for this hazard
is mandatory before #235 can close; a design PASS cannot silently accept the current label or
diagnostics as a North American policy-rate contract.

## Lifecycle and release contract

The source report and this design note are the only substantive artifacts. The final backlog mirror
must bind the exact content/design blob IDs, final handoff SHA, clean `origin/master` base
`472cfe6`, packet `acbbb82`, public receipt `issuecomment-5477977514`, and actor
`vnfin-oss-reviewer` with next action `RETURN_EXACT_SHA_DESIGN_VERDICT`.

A reviewer `PASS` authorizes only a later, explicit API/model decision. It does not authorize RED,
production code, source registration, push, public capability/coverage claims, or issue closure.
A future implementation sequence is: API/model decision → separate RED authorization → TDD
implementation → exact-SHA code review → merged gates → publication/remote verification → clean
resolution/closure only when separately authorized.

## Clean-room references

The clean-room checklist is `docs/vnstock-blacklist.md`; the exact exclusion string is recorded in
the source report. Official source links and the full 50-cell evidence table are in
`docs/research/2026-08-31-north-america-five-economy-macro-coverage.md`. Existing #200 evidence is
kept at `tasks/199-200-design-note.md` and `tests/test_macro_worldbank.py`; those synthetic tests
are not live provider coverage. The reviewer-packet evidence
`acbbb82:docs/research/2026-08-31-issue235-north-america-macro-cohort.md` (blob
`621545ca505ff6234cad32b9be7989d5e5add426`) is retained as upstream ranking-only 2020/2025 response
evidence, separate from the builder's future cell-audit plan.

## Bottom summary

- Decision: **`PARTIAL_COHORT`**; no new cell qualifies for API/RED extension yet.
- Cohort: frozen `USA/CAN/MEX/CUB/DOM` from strict common-year 2020 WDI GDP.
- 2025 `USA/CAN/MEX/DOM/GTM` remains an incomplete appendix, never a Cuba substitute.
- Matrix: 50 cells; 5 proven CAN, 6 partial (USA GDP/CPI/INFLATION plus MEX/CUB/DOM GDP),
  1 policy semantics gap, and 38 unprobed.
- Preserve `get_indicator` and `IndicatorSeries`; no ranking, batch, substitution, or new model.
- Future traffic ceiling is 9 logical/physical requests, zero retries; no post-intake #235 cell-audit
  dispatch occurred, and the upstream ranking response is one-year evidence only.
- No RED, code, source registration, push, closure, or runtime/coverage claim is authorized.
- Need from reviewer: exact-SHA design verdict; no Boss decision is required now.
