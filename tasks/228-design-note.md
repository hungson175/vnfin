# #228 design note — no-key multi-year world-gold daily history

**Packet:** `tasks/228-stitched-world-gold-daily-history-spec.md` at reviewer `967baf2`
**Published base:** `origin/master` `832945b8f411e17c50b0dca8a810540fcd45123a`
**Prior activation context:** `fbea1f1e9f78c506c34db7fd36ad2a51a1c324b1` is excluded from the
corrected clean ancestry and is not a publishable parent.
**Prior reviewed HEAD:** `d78cd339bb74168c93347143c8b23368d8a2c828`; BLOCK report reviewer
`498fdb8`, delivery `cc4b9005`, BLOCK-first record `e0f0a62`; clean BLOCK record `9cf501f`.
**Correction base:** clean `origin/master` `832945b8f411e17c50b0dca8a810540fcd45123a`.
**Phase:** `DESIGN_REVIEW`
**Disposition:** **`SOURCE-GAP CLOSURE`**
**New chain:** empty; no provider registration or runtime capability

This is the exact docs-only source/design artifact for #228. It freezes no public API, model,
warning/error grammar, chunking flag, source selection, or cross-source stitch. It authorizes no
provider probe, RED test, production code, source registration, push, or issue close before an
exact-SHA design PASS.

## 1. Scope and compatibility boundary

The future product need is a provenance-safe, no-login daily XAU/USD history primitive for the
inclusive requested window `2018-01-01..2026-08-21`. The caller's shock/hold strategy is out of
scope. Futures, ETFs, domestic VND quotes, annual/monthly series, USD crosses, proxy substitution,
and a caller-side backtest are not substitutes.

The current gold surface remains unchanged:

- `CurrencyApiGoldSource.get_history(start, end)` fetches one date-pinned document per calendar
  day, reads `usd.xau`, inverts it to USD/oz, skips its existing `SourceUnavailable` days, and
  returns the existing `GoldHistory`/`GoldBar` shape.
- The current adapter rejects ranges wider than 1,100 days and applies the conservative local
  guard `COVERAGE_START = 2024-03-02`; these are implementation boundaries, not provider/source
  coverage claims. Splitting the request does not alter the guards or establish earlier provider
  coverage.
- `default_world_gold_client()` remains Currency API only. Stooq remains explicit opt-in because
  its existing technical reachability is not a maintained default. Gold API remains spot-only.
- The annual World Bank CMO/world-reference path remains annual and separate. No new daily chain,
  accessor, source enum, coverage warning, or public diagnostic is added by this note.

The companion evidence report is
[`docs/research/2026-08-24-world-gold-multiyear-daily-history-source-vetting.md`](../docs/research/2026-08-24-world-gold-multiyear-daily-history-source-vetting.md).
It applies the mandatory clean-room exclusion and records no candidate data dispatch or live row.

## 2. Source decision

No one source unit passes all identity, coverage, transport, budget, and legal/reuse axes. The
new chain therefore stays empty and the correct disposition is `SOURCE-GAP CLOSURE`.

| Exact qualification unit | Evidence boundary | Blocking axes | Design disposition |
| --- | --- | --- | --- |
| fawazahmed0 date-pinned Currency API via jsDelivr at `.../v1/currencies/usd.json` | Official repository documents the route pattern, date selector, daily update and repository CC0; its generator/workflow describes publication but the date selector is not a cryptographic content pin and upstream data provenance is not established; local current code proves only the existing 2024-03-02 implementation boundary | No provider-declared 2018 bound, response-backed evidence in this round, correction/retention contract, or underlying data/package/CDN rights; no unlimited crawl grant | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| fawazahmed0 date-pinned Cloudflare fallback at `{date}.currency-api.pages.dev/v1/currencies/usd.json` | Official repository documents a separate fallback host | No independent response identity, provider bound, coverage, WAF/redirect/byte contract, rate policy, or reuse grant | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| Stooq official XAU/USD daily CSV operation | Official operator/terms pages identify Stooq/Tomasz Kulawik, disclaim completeness/continuous availability, prohibit redistribution without consent, and robots disallow generic user agents; the fixed operation is path plus `s=xauusd`, `i=d` | No response-backed instrument/unit/date contract, provider bound, correction/revision contract, no-login automation permission, or finite rate policy; existing exported opt-in adapter is only a technical lead | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| Perth Mint historical CSV operation | Official page describes downloadable daily files for 2016–2021 | No exact stable automated route, response-backed identity, continuous requested bound, revision/transport contract or OSS redistribution permission | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| Perth Mint spot-graph operation | Official page describes a separate daily graph publication from June 2020 | No exact route, response-backed history identity, requested bound, revision/transport contract or OSS redistribution permission | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| LBMA/IBA Gold Price | Official benchmark identity is USD per troy ounce and auction schedule is public | Twice-daily licensed benchmark, not an admitted no-key spot operation; historical/redistribution use requires IBA licensing | `LEGAL_GAP` + `IDENTITY_GAP` |
| World Gold Council gold-price data | Official page describes reference-price frequencies and USD/troy-ounce units; methodology/terms identify vendor/proprietary inputs and restrictions | No complete daily response route, provider bound, exact row/revision contract, or unrestricted OSS redistribution | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| FRED LBMA series/API | Official API supports bulk history and its terms are available; official notice records removal of daily LBMA series in 2022 | API key is required; no current exact requested-range operation with cleared series identity, provider bound or downstream rights is qualified | `COVERAGE_UNPROVEN` + `LEGAL_GAP` + `IDENTITY_GAP` |
| World Bank CMO/Pink Sheet | Existing official/in-repo source is annual/monthly | Wrong cadence/field for daily history; remains an annual path only | `FIELD_GAP` |

An official landing page, package licence, “free” label, browser visibility, HTTP success, or
robots policy is not proof of automation, caller return, cache/storage, derivative, commercial,
redistribution, or resale rights. No candidate is a fallback for this source-gap closure.

## 2.1 Evidence units and zero-dispatch accounting

The source gate distinguishes a candidate data operation from static evidence. Each evidence
unit is exactly one tuple `(evidence_id, owner, canonical host/path, route/version, operation)`.
Each retained row below has one path, one route/version and one operation; no row bundles multiple
pages or routes. The repository root `package.json` and published npm package page are distinct
units. No candidate data operation was dispatched.

| Evidence ID | Owner | Canonical host/path | Route/version | Operation | Static-read traffic | Candidate data dispatch |
| --- | --- | --- | --- | --- | --- | --- |
| `FZ-REPO-README` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/README.md` | `main` | repository route/documentation description | `NOT_RETAINED` | `0` |
| `FZ-REPO-GENERATOR` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/currscript.js` | `main` | generator source description | `NOT_RETAINED` | `0` |
| `FZ-REPO-WORKFLOW` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/.github/workflows/run.yml` | `main` | publication workflow description | `NOT_RETAINED` | `0` |
| `FZ-REPO-PACKAGE` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/package.json` | `main` | repository root package manifest | `NOT_RETAINED` | `0` |
| `FZ-REPO-LICENSE` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/LICENSE` | `main` | repository licence document | `NOT_RETAINED` | `0` |
| `FZ-NPM-PACKAGE` | fawazahmed0 | `npmjs.com/package/@fawazahmed0/currency-api` | published package page | package identity page only | `NOT_RETAINED` | `0` |
| `FZ-JSDELIVR-USD-V1` | fawazahmed0/jsDelivr | `cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/usd.json` | `GET; @{date}/v1` | date-pinned USD document; candidate field `usd.xau` | `NOT_RETAINED` | `0` |
| `FZ-CF-USD-V1` | fawazahmed0/Cloudflare | `{date}.currency-api.pages.dev/v1/currencies/usd.json` | `GET; v1; date host` | date-pinned USD fallback document; candidate field `usd.xau` | `NOT_RETAINED` | `0` |
| `STQ-OPERATOR` | Stooq | `stooq.pl/stooq/` | HTML page | operator identity page | `NOT_RETAINED` | `0` |
| `STQ-TERMS` | Stooq | `stooq.pl/terms.html` | HTML page | terms page | `NOT_RETAINED` | `0` |
| `STQ-ROBOTS` | Stooq | `stooq.com/robots.txt` | robots text | robots policy document | `NOT_RETAINED` | `0` |
| `STQ-CSV-XAUUSD-DAILY` | Stooq | `stooq.com/q/d/l/` | `GET; daily CSV` | XAU/USD operation signature `s=xauusd`, `i=d` | `NOT_RETAINED` | `0` |
| `PERTH-HIST-PAGE` | Perth Mint | `perthmint.com/invest/information-for-investors/metal-prices/historical-metal-prices/` | HTML page | historical-CSV link description | `NOT_RETAINED` | `0` |
| `PERTH-GRAPH-PAGE` | Perth Mint | `perthmint.com/invest/information-for-investors/metal-prices/historical-metal-prices/` | HTML page | spot-graph link description | `NOT_RETAINED` | `0` |
| `LBMA-PRICES` | LBMA/IBA | `lbma.org.uk/prices-and-data/lbma-precious-metal-prices` | HTML page | benchmark price description | `NOT_RETAINED` | `0` |
| `LBMA-FAQ` | LBMA/IBA | `lbma.org.uk/prices-and-data/lbma-gold-price/lbma-gold-price` | HTML page | Gold Price identity/licensing FAQ | `NOT_RETAINED` | `0` |
| `WGC-PRICE` | World Gold Council | `gold.org/goldhub/data/gold-prices` | HTML page | price-data description | `NOT_RETAINED` | `0` |
| `WGC-METHODOLOGY` | World Gold Council | `gold.org/data/gold-price/methodology` | HTML page | methodology document | `NOT_RETAINED` | `0` |
| `WGC-TERMS` | World Gold Council | `gold.org/terms-and-conditions` | HTML page | reuse terms document | `NOT_RETAINED` | `0` |
| `FRED-API-DOCS` | Federal Reserve Bank of St. Louis | `fred.stlouisfed.org/docs/api/fred/v2/` | HTML docs | API documentation | `NOT_RETAINED` | `0` |
| `FRED-TERMS` | Federal Reserve Bank of St. Louis | `fred.stlouisfed.org/docs/api/terms_of_use.html` | HTML terms | API terms document | `NOT_RETAINED` | `0` |
| `FRED-REMOVAL` | Federal Reserve Bank of St. Louis | `news.research.stlouisfed.org/2022/01/ice-benchmark-administration-ltd-iba-data-to-be-removed-from-fred/` | HTML notice | daily-LBMA removal notice | `NOT_RETAINED` | `0` |
| `WB-CMO` | World Bank | `worldbank.org/en/research/commodity-markets` | HTML page | CMO monthly/annual operation description | `NOT_RETAINED` | `0` |

The aggregate candidate ledger is exactly
`logical/physical/pages/retries/redirects/compressed/decompressed = 0/0/0/0/0/0/0`.
`NOT_RETAINED` static traffic is not zero traffic; it means no static request count or raw
transport detail is asserted. No `SourceAttempt`, zero-row result, `EMPTY_AUTHORITATIVE`, or
`diagnostics_truncated` event is fabricated.

## 3. Qualification contract for a future exact unit

This is a design predicate, not a frozen public schema. Every applicable line must pass for one
`(owner, canonical host/path, route/version, operation)` unit before an API/model decision.

### 3.1 Response-backed identity and values

The future response must positively identify:

1. the exact XAU/USD spot operation (or a separately approved benchmark identity),
2. a provider-issued plain daily date and its session/timezone/cutoff rule,
3. price meaning as USD per troy ounce, including the direction of any reciprocal field, and
4. publication, nonpublication, correction, revision, precision, scale and nullability semantics.

No request tag, filename, URL token, retrieval date, guessed timezone, benchmark relabel, or
caller-provided symbol can supply identity. A `usd.xau` inversion is valid only when the exact
provider documentation and response establish ounces of gold per one USD. A foreign currency
conversion, annual value, futures settlement, ETF NAV, or domestic VND/weight quote fails identity.

Rows are keyed by unique plain dates and returned in strict ascending order. Reject booleans,
non-finite/non-positive values, malformed dates, duplicate/conflicting dates, wrong product or
currency, unit/scale mismatch, unexplained nulls, and response/request identity mismatch. No row
is filled, interpolated, forward/backfilled, synthesized from a USD cross, or changed to zero.

### 3.2 Coverage states

These states are future design language only; they are not current public enums or warnings.

| State | Required conjunctive evidence | Meaning |
| --- | --- | --- |
| `FULL` | Provider-declared eligible sessions cover the requested range; all totals/pages/chunks reconcile; no unexplained gaps/conflicts; history start/end and current lag are proven; calendar/nonpublication rule is documented | Complete only for the provider-declared eligible set |
| `QUALIFIED_PARTIAL` | Provider-declared narrower bound, exact served/unserved bounds/counts, and the same reconciliation/no-unknown guarantees | A declared narrower result, never a full requested-range claim |
| `COVERAGE_UNPROVEN` | No provider-declared bound or qualified response was retained for the exact operation | Evidence gap; not absence, empty, zero, or partial |
| `COVERAGE_GAP` | Provider or qualified response explicitly establishes that the requested range is outside a declared bound | A documented gap, not an empty row set; no current candidate earns this state |
| `EMPTY_AUTHORITATIVE` | Exact identity, interval, totals/calendar, and provider nonpublication semantics prove zero eligible rows | Typed empty may be considered only in a later API decision |
| `NOT_SERVED` | Provider explicitly declares unsupported/out-of-bound/unlisted for the exact operation | Never inferred from transport failure |
| `IDENTITY_GAP` / `FIELD_GAP` | Required identity/field/unit/date meaning is absent or fails validation | No rows accepted |
| `TRANSPORT_INCONCLUSIVE` | WAF/challenge, timeout, redirect, unexpected status/MIME, malformed body, truncation, or unknown transport semantics | Unknown/fatal; not absence |
| `CALL_BUDGET_GAP` | A global atomic budget prevents or terminates work | Unknown/fatal; not zero or partial success |

Weekday counting is not an authoritative holiday/session calendar. A 404 or no-publication body is
missing only when the exact source contract proves that it means an ineligible/no-publication date.
Timeout, WAF, rate limit, unexpected status/MIME, malformed body, unknown retention, and budget
exhaustion are never skippable missing dates. Any failed or unknown same-source chunk prevents a
false `FULL`; private partial rows are discarded unless a separately approved partial contract
exists.

## 4. Legal, transport, and source identity ledger

The future ledger is per exact unit, not one global “provider works” note. Retain only bounded,
sanitized structure:

| Axis | Required evidence | Current #228 status |
| --- | --- | --- |
| Owner/route/version/operation | Canonical host/path, operation, method, route version and effective route | Static leads only; no candidate operation dispatched |
| Response identity | XAU/USD product, date, field names, price meaning, unit, scale, precision and nullability in the response | `NOT_RETAINED`; no response-backed candidate identity |
| Coverage/revision | Provider-declared bounds, eligible dates, history start/end, current publication lag, corrections, retention/deletion and totals/pages | `COVERAGE_UNPROVEN` or `NOT_RETAINED` per matrix; `COVERAGE_GAP` requires an explicit provider bound |
| Access/transport | No-login/key/session/UA/WAF behavior, expected status class, complete MIME after the first header colon, redirects, pagination and TLS | `NOT_RETAINED`; no live candidate probe |
| Rate/budget | Owner rate/concurrency/retry policy plus finite page/chunk/redirect/compressed/decompressed-byte ceilings | `RATE_POLICY_GAP` or `NOT_RETAINED` |
| Legal/reuse | Automation, caller return, transient cache, storage/retention/deletion, attribution, commercial/derivative use, redistribution/resale, amendment and revocation | `LEGAL_GAP` unless an exact licence covers the route and output |

Static-document reads and candidate data dispatches are separate. For each unit the candidate
ledger is exactly `logical/physical/pages/retries/redirects/compressed/decompressed = 0/0/0/0/0/0/0`.
It is forbidden to turn that zero into a fake `SourceAttempt`, “zero rows”, `EMPTY_AUTHORITATIVE`,
or `diagnostics_truncated` event.

## 5. Atomic future request budget

No numeric ceiling is frozen by this source-gap note. After owner evidence and a separate API/model
decision, one invocation must use one deterministic sequential ledger shared by all sources and
same-source chunks:

```text
logical_units, physical_dispatches, pages_or_chunks, retries,
redirects, compressed_bytes, decompressed_bytes
```

- `max_concurrency = 1`; source choice and chunk scheduling are deterministic.
- Reserve every logical unit, page/chunk, physical dispatch, retry and redirect before dispatch.
- A retry or followed redirect is a new physical operation and consumes its own reservations.
- Charge compressed bytes while streaming and decompressed bytes after decoding; an over-ceiling
  response consumes the actual reservation and accepts no rows.
- Caller-malformed dates/types fail before cache or network. A malformed provider body fails after
  the real dispatch but before cache/return.
- Reservation failure dispatches nothing. Reconcile each dimension as
  `reserved = charged + released` without decrementing charged work.
- Exhaustion of **any** dimension is globally fatal: discard all private rows, do not return a
  partial/zero/empty/complete series, and preserve only real bounded attempts/counters.

Diagnostics are finite class tokens and bounded real counts only. Never retain raw query/path
values, URLs, body/header/cookie text, provider exception prose, credentials, secrets, live prices,
or invented attempt/truncation records.

## 6. Cross-source and same-source segment boundary

Single-source qualification remains the source gate; no current unit qualifies. A later API/model
decision may explicitly authorize a deterministic ordered `SegmentPlan`, but it is not automatic
failover and is not authorized by this source-design note. Each segment must independently qualify
owner, route/version/operation, response identity, plain-date rule, XAU/USD meaning, units,
precision, revision, provider-eligible coverage and legal/reuse axes. Same-source pagination/chunking
is retained inside the segment manifest, while cross-source segments retain their own identity.

A future segment entry must carry `segment_id`, exact source unit, route/version, requested and served
bounds, provider-eligible calendar, same-source `chunk` manifest, real `fetched_at_utc`, bounded
warnings/attempts, identity/unit/revision/legal evidence, and any provider-declared unserved
interval. The ordered plan is deterministic and non-overlapping except for an explicitly declared
seam overlap. It must be gap-free over the provider-eligible requested interval. A missing middle
segment, unknown transport/identity/budget outcome, or conflicting overlap is an atomic failure;
there is no source skip, silent fallback, or private partial return.

The future aggregate contract is:

- `FULL`: all requested provider-eligible sessions are covered by independently qualified segments;
  segment/chunk totals reconcile; seams agree under a frozen precision/date rule; no unknown interval
  remains; and `fetched_at_utc = max(real segment retrieval timestamps)`.
- `QUALIFIED_PARTIAL`: the ordered plan covers a provider-declared narrower bound with exact served
  and unserved counts and no unknown interval. It never claims the complete requested span.
- `COVERAGE_UNPROVEN`: any segment lacks provider-declared bound or response-backed evidence. It is
  not a partial or empty result. A future top-level `source` may be a deterministic sanitized
  composite token ordered by the plan only after that public rule is frozen; segment provenance
  remains visible and authoritative.

Fixings, futures, ETFs, domestic quotes, annual/monthly observations and derived USD crosses cannot
be stitched into daily XAU/USD history merely because values look comparable. The new chain remains
empty now.

## 7. Deferred API/RED/release matrix

All rows below are `DEFERRED / NOT_AUTHORIZED`. They are acceptance criteria for later source
qualification and API/model review, not implementation instructions for this commit. The lifecycle
is API/model freeze → separate RED authorization for failing tests only → reviewer verifies RED and
authorizes implementation → GREEN → code review → publication.

| Future gate | Required evidence/tests | Current status |
| --- | --- | --- |
| API/model freeze | Existing `get_history` compatibility; immutable history, coverage, provenance, segment/**chunk** manifest and attempt carriers; deterministic source/segment selection; public exports; serialization/repr/equality; DataFrame attrs; sanitized errors; zero-source semantics; public snapshot | Not authorized |
| Input and preflight RED | Inclusive/reversed/malformed/bool dates; empty, duplicate and custom source selection; malformed chunk/stitch options; every caller failure before cache/network with zero-call proof and untouched cache; current behavior unchanged | Not authorized |
| Exact and multi-year success RED | Exact one-window and requested multi-year planning; lower/upper boundary, precoverage, current lag, weekend/holiday/no-publication and declared partial/empty cases | Not authorized |
| Identity/value/revision RED | XAU/USD identity, date keys and cutoff, `usd.xau` direction if applicable, USD/oz, finite positive values, precision, nullability, duplicate/conflict, correction and revision cases | Not authorized |
| Chunk planner RED | One fetch per planned chunk; deterministic scheduler/order; boundary overlap/gap; out-of-order and duplicate rows; conflicting overlap; failed middle chunk; atomic no-false-`FULL` | Not authorized |
| Coverage/no-false-absence RED | Provider-declared bounds and totals; exact `FULL` versus `QUALIFIED_PARTIAL`; authoritative nonpublication versus unknown transport; no silent missing-day, zero-fill or partial claim | Not authorized |
| Transport/budget/cache RED | Expected status and complete MIME; redirect, WAF, timeout, TLS/UA/session, pagination, retry, compressed/decompressed byte ceilings; shared global exhaustion; reservation/charge/release; cache-before/after-failure ordering | Not authorized |
| Composite/stitch RED | Independently qualified source segments; deterministic plan; same-source chunk manifest; seam overlap agreement/conflict; missing middle; aggregate coverage; `fetched_at_utc` max; top-level and segment provenance | Not authorized |
| Diagnostics RED | Finite sanitized class tokens, real attempts and counters; bounded warnings; no URL/query/raw body/header/cookie/provider prose; no fake attempts or truncation marker; model/DataFrame/public diagnostic snapshot | Not authorized |
| Release/compatibility | Existing Currency API, Gold API, Stooq, failover and annual World Bank behavior; docs/API/units/tutorial/architecture/skill/CHANGELOG; full offline suite/import/version; blacklist/secret/diff/path/object/clean-tree; wheel/sdist; exact remote ancestry/path | Not authorized |

No RED authorization, implementation, live integration test, source registration, coverage claim,
or public API decision is implied by these rows.

## 8. Reopen and closure lifecycle

Reopen is conjunctive. A future owner request must supply all of the following together:

1. one exact provider route with response-backed XAU/USD identity, USD/oz meaning, daily date,
   cadence, correction/revision and no-publication semantics;
2. 2018-01-01..2026-08-21 coverage, or a provider-declared reconciled narrower partial bound;
3. explicit no-login automation or approved license/permission covering cache/storage, caller
   return, attribution, commercial/derivative use, redistribution, amendment and revocation;
4. finite owner/runtime evidence for rate/retry/concurrency, redirects, pages, status/MIME, TLS/
   UA/WAF/session and compressed/decompressed bytes;
5. an API/model contract decision freezes compatibility, immutable provenance/coverage/attempt
   carriers, same-source chunk manifests, no-false-absence semantics, and whether the exact
   deterministic `SegmentPlan`/aggregate contract in section 6 is allowed;
6. a separate RED authorization followed by reviewer verification; and
7. exact merged-tree gates and reviewer approval.

The lifecycle is exact: **source qualification → API/model contract freeze → RED authorization
permits failing tests only → reviewer verifies RED and authorizes implementation → GREEN → code
review → publication**.

For this source-gap outcome, after exact design PASS the permitted sequence is only: rerun merged
docs/full/build/blacklist/secret/diff/clean-tree gates; push the exact approved docs/source/backlog
anchor; verify remote HEAD, base ancestry, exclusions and exactly the three approved paths; post a
clean no-capability `SOURCE-GAP` resolution; close and re-read #228. There is no TDD or runtime
follow-on in this issue. Later capability work requires a fresh source qualification and design
PASS.

## Primary references

The complete source links and evidence ledger are in the companion research report. Key official
references are:

- [fawazahmed0 exchange-api](https://github.com/fawazahmed0/exchange-api), its [CC0 licence](https://github.com/fawazahmed0/exchange-api/blob/main/LICENSE), [generator](https://github.com/fawazahmed0/exchange-api/blob/main/currscript.js), and [publication workflow](https://github.com/fawazahmed0/exchange-api/blob/main/.github/workflows/run.yml)
- [exchange-api root package manifest](https://github.com/fawazahmed0/exchange-api/blob/main/package.json) — root repository metadata; not the published package page.
- [npm package page for `@fawazahmed0/currency-api`](https://www.npmjs.com/package/@fawazahmed0/currency-api) — published package identity only; no underlying data rights are inferred.
- [jsDelivr terms](https://www.jsdelivr.com/terms/terms-of-use) — CDN service constraints, not a data-rights grant.
- [The Perth Mint historical metal prices](https://www.perthmint.com/invest/information-for-investors/metal-prices/historical-metal-prices/)
- [Stooq official site](https://stooq.com/), [operator](https://stooq.pl/stooq/), [terms](https://stooq.pl/terms.html), [robots policy](https://stooq.com/robots.txt), and [daily path](https://stooq.com/q/d/l/)
- [LBMA precious-metal prices](https://www.lbma.org.uk/prices-and-data/lbma-precious-metal-prices) and [LBMA Gold Price FAQ](https://www.lbma.org.uk/prices-and-data/lbma-gold-price/lbma-gold-price)
- [World Gold Council gold prices](https://www.gold.org/goldhub/data/gold-prices), [methodology](https://www.gold.org/data/gold-price/methodology), and [terms](https://www.gold.org/terms-and-conditions)
- [FRED API documentation](https://fred.stlouisfed.org/docs/api/fred/v2/), [terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html), and [daily-LBMA removal notice](https://news.research.stlouisfed.org/2022/01/ice-benchmark-administration-ltd-iba-data-to-be-removed-from-fred/)
- [World Bank Commodity Markets](https://www.worldbank.org/en/research/commodity-markets)

## Bottom summary

- Decision: **`SOURCE-GAP CLOSURE`**; the new daily world-gold chain remains empty.
- Existing Currency API/Gold API/Stooq opt-in/failover and annual World Bank behavior are preserved.
- No candidate proves identity, 2018-current coverage, lawful reuse, runtime limits, and no-false-absence together.
- Future `FULL`/`QUALIFIED_PARTIAL` states require provider-declared bounds and full reconciliation; unknown failures are fatal.
- One sequential global budget must reserve/charge logical, physical, page, retry, redirect, compressed and decompressed dimensions atomically.
- Cross-source stitching, new API/model, warnings, RED tests and code are deferred/not authorized.
- Design-PASS publication is docs/source-gap only: exact three paths, clean remote verification, resolution, then close/re-read.
- Need from Boss: **nothing**; exact merged SHA will be returned for design review.
