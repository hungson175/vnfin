# #228 world-gold multi-year daily-history source vetting

**Access date:** 24 August 2026 (UTC+7)
**Packet:** `tasks/228-stitched-world-gold-daily-history-spec.md` at reviewer anchor `967baf2`
**Published base:** `origin/master` `832945b8f411e17c50b0dca8a810540fcd45123a`
**Clean correction base:** `832945b8f411e17c50b0dca8a810540fcd45123a`
**Prior reviewed HEAD:** `d78cd339bb74168c93347143c8b23368d8a2c828`; BLOCK report reviewer `498fdb8`
**Phase:** `DESIGN_REVIEW`
**Disposition:** **`SOURCE-GAP CLOSURE`**
**New chain:** empty; current gold behavior is unchanged
**Correction provenance:** prior activation `fbea1f1e9f78c506c34db7fd36ad2a51a1c324b1` is excluded
from this corrected ancestry; it is retained only as historical activation context.

This is a documentation-only clean-room source and legal review. It does not add a provider,
probe a data route, retain a live row, freeze an API, authorize RED tests, or change runtime
behavior. The requested future primitive is inclusive daily XAU/USD history for
`2018-01-01..2026-08-21`, without credentials, silent gaps, proxy substitution, or a caller-side
trading strategy. No researched unit proves every required source, coverage, runtime, and rights
axis, so no unit is admitted to a new chain.

## Clean-room and research boundary

The exact exclusion applied to every web search was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited material, unofficial endpoint map, copied dataset, broker/private feed, credential,
proxy, reporter archive, or third-party code was opened, cited, or used. Research read official
owner pages, official repository documentation, official terms/licence pages, and existing
clean-room project documentation only. It did **not** call a candidate data/history operation.

The following are deliberately not retained: live prices, raw payloads or headers, cookies,
tokens, response digests, query-bearing URLs, and provider exception prose. A canonical host/path
or route pattern is retained only as a design identifier. `NOT_RETAINED` means that the axis was
not observed or retained; it is never a positive permission, absence, zero, or complete-coverage
claim.

## Decision and current boundary

### Decision

`SOURCE-GAP CLOSURE` is the only safe disposition at this gate. There is no single official or
clearly licensed no-login operation with response-backed XAU/USD daily identity, requested
2018-current coverage, correction semantics, finite automation/budget terms, and OSS caller-return
and redistribution rights. Some candidates are useful leads for a later permission/research round;
none is a qualified source or fallback now.

The new multi-year chain remains empty. Preserve the existing `CurrencyApiGoldSource`,
`GoldApiSource`, `StooqGoldSource`, `FailoverGoldClient`, and world-reference behavior byte-for-byte
in this source/design round. No new stitched facade, chunking flag, source registration, model,
warning grammar, or coverage claim is authorized.

### Existing behavior that must not be widened here

The tag-dereferenced v0.2.0 code is `2fe50df4f27064140ff9f7a680227a2b337ec74a`. The current
published behavior is the compatibility boundary:

- `CurrencyApiGoldSource.get_history(start, end)` fetches one date-pinned document per calendar day,
  reads the provider's `usd.xau` cross, and inverts it to USD per troy ounce.
- It rejects a range wider than `1,100` days and applies the conservative local guard
  `COVERAGE_START = 2024-03-02` in `vnfin/gold/currency_api.py`. A request wholly before that
  implementation guard fails before network fan-out; this is not a provider coverage assertion.
- Its existing loop skips `SourceUnavailable` days and returns the existing `GoldHistory` shape:
  product `XAU`, unit/value unit `USD/oz`, currency `USD`, ordered `GoldBar` rows, source,
  UTC retrieval time, warnings, and source attempts.
- `default_world_gold_client()` uses Currency API only. Stooq is exported but opt-in because
  datacenter anti-bot behavior is not a maintained default. Gold API is spot-only.
- The annual World Bank CMO path and the caller-side world-reference synthesis remain annual and
  separate. Annual data, futures, ETFs, domestic quotes, and USD crosses are not daily XAU/USD
  history substitutes.

The requested window cannot be served by the existing adapter under its current local guards:
its `1,100`-day per-call cap rejects the whole span and its conservative `COVERAGE_START =
2024-03-02` check rejects requests before that implementation boundary. These are facts about the
current adapter, not proof that a provider/source lacks earlier dates. Removing the guard or splitting
the request would not by itself establish provider coverage, and neither change is authorized by
this packet.

## Evidence and unit accounting

Each **source qualification unit** is the tuple
`(owner, canonical host/path, route/version, operation)`. A public landing page, software repository,
package manifest, package mirror, fallback host, API documentation page, and data operation are
separate units. Static-document reading is not a candidate data dispatch.

An **evidence unit** is exactly one tuple
`(evidence_id, owner, canonical host/path, route/version, operation)`. Each retained row below has
one path, one route/version and one operation; no row bundles a repository landing page, a generator,
a workflow, a manifest, or multiple provider routes. Static evidence never upgrades into
response-backed data, permission, or coverage. The repository root `package.json` and the published
npm package page are distinct units; neither grants rights to underlying rate data.

For every candidate operation below, no candidate data request was dispatched. The exact candidate
ledger is:

```text
logical_units / physical_dispatches / pages_or_chunks / retries /
redirects / compressed_bytes / decompressed_bytes = 0 / 0 / 0 / 0 / 0 / 0 / 0
```

Static-read traffic is a different ledger. Its value is `NOT_RETAINED` for every row below: no
static request count, browser subresource count, or raw transport detail is being asserted. The
candidate dispatch column is the only zero ledger. A static read therefore cannot be mistaken for a
candidate data call or a fabricated `SourceAttempt`.

### Retained static evidence-unit ledger

For a static document with no published route version, the route/version cell is explicitly `unversioned`; content type belongs in the operation cell, not the route/version cell.

| Evidence ID | Owner | Canonical host/path | Route/version | Operation | Static-read traffic | Candidate data dispatch |
| --- | --- | --- | --- | --- | --- | --- |
| `FZ-REPO-README` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/README.md` | `main` | repository route/documentation description | `NOT_RETAINED` | `0` |
| `FZ-REPO-GENERATOR` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/currscript.js` | `main` | generator source description | `NOT_RETAINED` | `0` |
| `FZ-REPO-WORKFLOW` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/.github/workflows/run.yml` | `main` | publication workflow description | `NOT_RETAINED` | `0` |
| `FZ-REPO-PACKAGE` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/package.json` | `main` | repository root package manifest | `NOT_RETAINED` | `0` |
| `FZ-REPO-LICENSE` | fawazahmed0 | `github.com/fawazahmed0/exchange-api/LICENSE` | `main` | repository licence document | `NOT_RETAINED` | `0` |
| `FZ-NPM-PACKAGE` | fawazahmed0 | `npmjs.com/package/@fawazahmed0/currency-api` | `unversioned` | package identity page only | `NOT_RETAINED` | `0` |
| `FZ-JSDELIVR-USD-V1` | fawazahmed0/jsDelivr | `cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/usd.json` | `GET; @{date}/v1` | date-pinned USD document; candidate field `usd.xau` | `NOT_RETAINED` | `0` |
| `FZ-CF-USD-V1` | fawazahmed0/Cloudflare | `{date}.currency-api.pages.dev/v1/currencies/usd.json` | `GET; v1; date host` | date-pinned USD fallback document; candidate field `usd.xau` | `NOT_RETAINED` | `0` |
| `JSDELIVR-TERMS` | jsDelivr | `www.jsdelivr.com/terms/terms-of-use` | `unversioned` | CDN service terms document | `NOT_RETAINED` | `0` |
| `STQ-OPERATOR` | Stooq | `stooq.pl/stooq/` | `unversioned` | operator identity page | `NOT_RETAINED` | `0` |
| `STQ-TERMS` | Stooq | `stooq.pl/terms.html` | `unversioned` | terms page | `NOT_RETAINED` | `0` |
| `STQ-ROBOTS` | Stooq | `stooq.com/robots.txt` | `unversioned` | robots policy document | `NOT_RETAINED` | `0` |
| `STQ-CSV-XAUUSD-DAILY` | Stooq | `stooq.com/q/d/l/` | `unversioned; GET` | daily CSV; XAU/USD operation signature `s=xauusd`, `i=d` | `NOT_RETAINED` | `0` |
| `PERTH-HIST-PAGE` | Perth Mint | `perthmint.com/invest/information-for-investors/metal-prices/historical-metal-prices/` | `unversioned` | historical-CSV link description | `NOT_RETAINED` | `0` |
| `PERTH-GRAPH-PAGE` | Perth Mint | `perthmint.com/invest/information-for-investors/metal-prices/historical-metal-prices/` | `unversioned` | spot-graph link description | `NOT_RETAINED` | `0` |
| `LBMA-PRICES` | LBMA/IBA | `lbma.org.uk/prices-and-data/lbma-precious-metal-prices` | `unversioned` | benchmark price description | `NOT_RETAINED` | `0` |
| `LBMA-FAQ` | LBMA/IBA | `lbma.org.uk/prices-and-data/lbma-gold-price/lbma-gold-price` | `unversioned` | Gold Price identity/licensing FAQ | `NOT_RETAINED` | `0` |
| `WGC-PRICE` | World Gold Council | `gold.org/goldhub/data/gold-prices` | `unversioned` | price-data description | `NOT_RETAINED` | `0` |
| `WGC-METHODOLOGY` | World Gold Council | `gold.org/data/gold-price/methodology` | `unversioned` | methodology document | `NOT_RETAINED` | `0` |
| `WGC-TERMS` | World Gold Council | `gold.org/terms-and-conditions` | `unversioned` | reuse terms document | `NOT_RETAINED` | `0` |
| `FRED-API-DOCS` | Federal Reserve Bank of St. Louis | `fred.stlouisfed.org/docs/api/fred/v2/` | `unversioned` | API documentation | `NOT_RETAINED` | `0` |
| `FRED-TERMS` | Federal Reserve Bank of St. Louis | `fred.stlouisfed.org/docs/api/terms_of_use.html` | `unversioned` | API terms document | `NOT_RETAINED` | `0` |
| `FRED-REMOVAL` | Federal Reserve Bank of St. Louis | `news.research.stlouisfed.org/2022/01/ice-benchmark-administration-ltd-iba-data-to-be-removed-from-fred/` | `unversioned` | daily-LBMA removal notice | `NOT_RETAINED` | `0` |
| `WB-CMO` | World Bank | `worldbank.org/en/research/commodity-markets` | `unversioned` | CMO monthly/annual operation description | `NOT_RETAINED` | `0` |

No `SourceAttempt`, retry, redirect, byte total, MIME value, truncation marker, live value, or
provider exception prose is fabricated. Static reading may establish owner or product-description
facts, but it cannot supply a response-backed data identity, transport contract, or permission.

### Candidate matrix

Each row below is one candidate **data operation**, not a landing page or package artefact. The
matrix uses `COVERAGE_UNPROVEN` when no provider-declared bound or qualified response was retained;
`COVERAGE_GAP` is reserved for a provider or qualified response that explicitly excludes an interval.

| Unit (owner; canonical operation) | Static evidence retained | Missing decisive axes | Total disposition |
| --- | --- | --- | --- |
| **Currency API CDN history** — fawazahmed0; date-pinned USD document at `.../v1/currencies/usd.json` with `usd.xau` field operation | The official repository documents date selectors, GET JSON documents, daily publication mechanics, metals in its currency universe, a CC0 repository licence and a CDN route. A date tag is an alias rather than a cryptographic content pin and upstream data provenance is not established. Existing local runtime research identifies the current `usd.xau` inversion and lower implementation boundary `2024-03-02`; this round does not re-probe it. | No retained response-backed XAU/date/field identity; no provider-declared 2018 bound, correction/retention contract, package/CDN data-rights lineage, automation, caller return, cache, derivative or redistribution terms. The repository code licence does not itself clear underlying rate data. | `COVERAGE_UNPROVEN` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| **Currency API Cloudflare fallback** — fawazahmed0; date-pinned USD document at `{date}.currency-api.pages.dev/v1/currencies/usd.json` fallback operation | The official repository describes a fallback host for the same date/version shape. | No retained response identity, exact 2018 bound, WAF/redirect/byte semantics, rate/concurrency policy, or reuse/redistribution grant. It cannot inherit coverage or permission from jsDelivr. | `COVERAGE_UNPROVEN` + `LEGAL_GAP` + `TRANSPORT_INCONCLUSIVE` |
| **Stooq daily CSV** — Stooq; daily XAU/USD operation at the canonical path with fixed signature `s=xauusd`, `i=d` | Official operator/terms pages identify Stooq/Tomasz Kulawik; terms disclaim completeness/continuous availability and prohibit redistribution without consent; robots policy disallows generic user agents. | No retained XAU/USD instrument/unit/date/close response contract, 2018-current provider bound, correction/retention rule, no-login automation permission or finite rate policy. Existing opt-in support is only a technical lead. | `COVERAGE_UNPROVEN` + `LEGAL_GAP` + `RATE_POLICY_GAP` + `TRANSPORT_INCONCLUSIVE` |
| **Perth Mint historical CSV** — Perth Mint; historical CSV operation | Official page describes downloadable historical gold files, including a 2016–2021 publication description. | No exact stable automated route, response identity, continuous requested bound, current publication/revision semantics, finite machine-access policy, or OSS caller-return/redistribution grant. | `COVERAGE_UNPROVEN` + `LEGAL_GAP` + `TRANSPORT_INCONCLUSIVE` |
| **Perth Mint spot-price graph** — Perth Mint; graph/download operation described from June 2020 | Official page describes a separate daily graph publication from June 2020 onward and spot/trade-date concepts. | The graph is not a response-backed daily XAU/USD history unit for the requested range; exact route, revisions, transport, finite access policy and OSS reuse rights are not retained. | `COVERAGE_UNPROVEN` + `LEGAL_GAP` + `TRANSPORT_INCONCLUSIVE` |
| **LBMA Gold Price** — LBMA/ICE Benchmark Administration; twice-daily benchmark operation | Official pages identify USD/troy-ounce benchmark, AM/PM auctions, UK-bank-holiday nonpublication and historical-data licensing through IBA. | Licensed benchmark fixing is not an admitted no-key XAU/USD spot operation. No OSS automation, storage, caller-return, derivative or redistribution right is cleared. | `LEGAL_GAP` + `IDENTITY_GAP` |
| **World Gold Council gold-price data** — WGC; official reference-price publication/download operation | Official page describes frequencies and currencies, says daily data may exist where available, quotes currency per troy ounce, and records historical LBMA removal. Methodology/terms identify proprietary inputs and restrict copying/scraping/distribution. | No complete daily XAU/USD 2018-current response route, exact row/revision contract, provider bound, or unrestricted OSS redistribution. | `COVERAGE_UNPROVEN` + `LEGAL_GAP` + `FIELD_GAP` |
| **FRED LBMA series/API** — Federal Reserve Bank of St. Louis; official series/API operation | FRED API documentation supports historical observations; terms require a key and state that series may be third-party-owned; the official notice records removal of daily LBMA series in 2022. | Not no-login; no current exact requested-range operation with cleared series identity, downstream rights, provider bound or response contract is retained. | `COVERAGE_UNPROVEN` + `LEGAL_GAP` + `IDENTITY_GAP` + `RATE_POLICY_GAP` |
| **World Bank CMO/Pink Sheet** — World Bank; official monthly/annual commodity-price operation | Official commodity-markets page exposes monthly and annual price files; the existing in-repo CMO adapter is an annual world-gold source. | Wrong cadence and field for daily history; it remains the existing annual path and is never a daily fallback. | `FIELD_GAP` |

The repository root package manifest, published npm package page, CDN delivery, fallback host and candidate data operation
remain distinct units even when they share an owner. No evidence-only unit is silently promoted to a
candidate source.

### Axis ledger

The matrix is intentionally conservative. `NR` means `NOT_RETAINED`; `NP` means the candidate
operation was `NOT_PROBED`. A static page's visible text is not upgraded into a positive data or
rights claim. No current candidate row below has a provider-declared bound sufficient for
`COVERAGE_GAP`.

| Unit | owner/route | response identity + fields | coverage/date/revision | auth/UA/WAF/status/MIME/redirect | rate/retry/bytes/budget | rights: automation/cache/return/storage/derivative/commercial/redistribution | disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Currency API CDN | owner/repo and route pattern known; version/operation response `NR`; date selector is not a content hash | `NR` | local implementation lower boundary `2024-03-02`; provider bound `NR`; `2018-current` `COVERAGE_UNPROVEN` | `NP/NP/NP/NP/NP/NP` | `NR` | repo CC0 observed; upstream/data provenance and package/CDN rights `NR` | `COVERAGE_UNPROVEN` |
| Currency API fallback | owner/path pattern known; response `NR` | `NR` | provider bound `NR`; cannot inherit CDN coverage | `NP/NP/NP/NP/NP/NP` | `NR` | `NR` | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| Stooq CSV | operator/path lead known; fixed signature `s=xauusd`, `i=d`; response `NR` | `NR` | provider bound `NR` | generic-user-agent robots restriction observed; API/UA/session/MIME `NP` | `NR` | terms prohibit redistribution without consent; automation and other rights `NR` | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| Perth historical CSV | official owner/page known; exact automated file route `NR` | static publication description; response `NR` | 2016–2021 description; exact requested bound and revision `NR` | `NP/NP/NP/NP/NP/NP` | `NR` | reference/as-is notice; reuse axes `NR` | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| Perth spot graph | official owner/page known; separate graph route `NR` | static spot description; response `NR` | June 2020 description; exact requested bound and revision `NR` | `NP/NP/NP/NP/NP/NP` | `NR` | reference/as-is notice; reuse axes `NR` | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| LBMA/IBA | owner/benchmark known; response route `NR` | benchmark identity static; requested spot operation `IDENTITY_GAP` | auction schedule/nonpublication static; historical route/license `NR` | `NP/NP/NP/NP/NP/NP` | `NR` | historical/redistribution licence required; no OSS grant | `LEGAL_GAP` |
| WGC | owner/page known; data operation `NR` | static price description; exact daily row `NR` | frequencies “where available”; requested bound `NR` | `NP/NP/NP/NP/NP/NP` | `NR` | proprietary/limited-extract/attribution posture; broad redistribution `NR` | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| FRED | owner/API docs known; series observation `NR` | series owner/identity `NR` | exact requested series bound `NR`; daily LBMA removal is not a qualified current operation | API key required; other transport `NP` | adjustable limits; exact route budget `NR` | third-party series restrictions; no permission for downstream use | `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| World Bank CMO | owner/cadence known | annual gold identity exists locally; daily field `FIELD_GAP` | monthly/annual, not daily | `NP` | `NR` | existing annual terms remain in existing source docs; not a daily operation | `FIELD_GAP` |

The `owner/route` column is not a claim that the provider has authorized this library. The rights
columns stay unresolved unless an exact provider licence or written owner permission covers the
operation and intended downstream use.

### Coverage disposition vocabulary

- `COVERAGE_UNPROVEN` means no provider-declared bound or qualified response was retained for the
  exact operation. It is an evidence gap, not absence, empty data, a zero count, or a partial result.
- `COVERAGE_GAP` is reserved for a provider or qualified response that explicitly establishes that
  a requested interval is outside its declared bound. No current candidate earns this disposition.
- `QUALIFIED_PARTIAL` is permitted only after a provider-declared narrower bound and reconciled
  served/unserved/unknown accounting. A local implementation boundary is not a provider bound.

## Required future qualification contract

This section is a reopen contract, not a public API or runtime model. A future source is qualified
only if all applicable predicates pass for **one exact unit**. A candidate may be `QUALIFIED_PARTIAL`
only when the provider itself declares a narrower, reconciled bound; a caller or library cannot
turn a missing bound into a partial result.

### Identity, units, and rows

- The response must identify the exact product/instrument as XAU/USD spot or another explicitly
  accepted world-gold operation. A benchmark fixing, futures contract, ETF NAV, domestic quote, or
  USD-converted proxy is not relabeled as spot history.
- Every accepted row carries one provider-backed plain date, not request order, retrieval date,
  filename/tag, or a timezone guessed from a timestamp. The provider must document session/calendar,
  timezone/date-cutoff, publication lag, correction/revision, and no-publication rules.
- The response must prove price meaning and units: USD per troy ounce. `usd.xau` may be inverted
  only when the exact provider documentation and response identity establish “troy ounces per one
  USD”; no cross-source or caller-inferred inversion is accepted.
- Prices are finite, strictly positive, non-boolean numerics. Duplicate dates, conflicting values,
  malformed dates, wrong product/currency/unit, unexplained nulls, and mismatched response identity
  fail atomically. No fill, zero, interpolation, forward/backfill, or synthesized USD cross.
- `source` is a canonical producer/operation token from the qualified unit. It is not a URL token,
  caller label, package mirror, or top-level token that erases segment provenance.

### Coverage and no-false-absence

`FULL` requires one provider-owned unit whose declared eligible sessions cover the requested
interval; all provider-declared totals/pages/chunks reconcile; there are no unexplained gaps or
conflicts; history start/end and current publication lag are proven; and the calendar rule for
weekends/holidays is provider-backed. A weekday heuristic alone is not completeness evidence.

`QUALIFIED_PARTIAL` requires the same reconciliation plus provider-declared narrower bounds and
exact served/unserved bounds/counts. It may not claim `2018-01-01..2026-08-21` coverage.

Dates before a provider-declared bound may be described as explicitly unserved only when the
qualified source contract proves that meaning. This report retains no such bound for the current
candidates, so their earlier dates remain `COVERAGE_UNPROVEN`, not provider absence. A documented
provider 404 or no-publication response is an authoritative missing session only when the exact
source contract proves that meaning. A timeout, WAF/challenge, rate limit, unexpected status or
complete MIME, redirect failure, malformed document, unknown retention, identity mismatch, or
budget exhaustion is unknown/fatal, never a skippable missing day and never an empty/zero result.

Same-source chunks, if later authorized, must be deterministic, non-overlapping except for a
validated seam, independently identity-checked, and atomically reconciled. Any failed or unknown
chunk prevents `FULL`; private partial rows are discarded unless a separately approved partial
contract exists.

### Legal and runtime axes

The exact owner or licence must positively cover, for the exact route and fields:

1. automated no-login access (or a written permission/paid entitlement explicitly approved later);
2. request rate, concurrency, retry, pagination, redirect, WAF/UA/session, and byte constraints;
3. caller return of normalized observations;
4. transient cache/storage, retention, deletion, and correction/revision handling;
5. attribution, commercial and derivative use; and
6. redistribution/resale, amendment, revocation, and any third-party data-owner restrictions.

“Public”, “free”, “no rate limit” in a README, robots visibility, a browser page, a package mirror,
or HTTP success is not a redistribution or automation grant. A repository software licence does
not automatically license provider data. Any missing axis is a `LEGAL_GAP` or `RATE_POLICY_GAP`.

## Atomic budget and diagnostics contract

No numeric ceilings are frozen now. Once a source owner publishes applicable limits, one invocation
must use one sequential global ledger across all source units and chunks:

```text
logical_units, physical_dispatches, pages_or_chunks, retries,
redirects, compressed_bytes, decompressed_bytes
```

Each reservation is atomic and occurs before dispatch. A retry and followed redirect are real
physical operations and reserve their own counters. Compressed bytes are charged while the body is
streamed; decompressed bytes are charged after decoding. A reservation failure dispatches nothing.
Every attempted status/MIME/identity/parse failure consumes its real reservation and accepts no
rows. Any dimension exhaustion is globally fatal: discard every private accumulator and return no
history, partial history, zero-filled history, or false absence. Reconcile
`reserved = charged + released` per dimension without decrementing charged work.

Future bounded diagnostics may retain only sanitized finite class tokens and real counters. They
must not contain a query, raw URL, body/header/cookie, token, secret, live value, or provider prose.
Never fabricate a `SourceAttempt` or `diagnostics_truncated` event when no dispatch occurred, and
never claim that a zero ledger means a source had zero rows or zero website traffic.

## Cross-source composition boundary

Single-source qualification remains the source gate, and no current source unit qualifies. A later
API/model decision may explicitly authorize a deterministic `SegmentPlan`; it is not automatic
failover and is not authorized by this packet. Every segment must independently qualify its owner,
route/version/operation, response identity, plain-date rule, USD/oz semantics, precision, revision,
provider-eligible coverage and legal/reuse axes. Same-source pagination/chunking remains inside its
segment and must be retained in the manifest; cross-source segments are never collapsed into one
anonymous source.

A future `SegmentPlan` is valid only when its ordered entries carry `segment_id`, exact source unit,
route/version, requested and served bounds, provider-eligible calendar, same-source chunk manifest,
real `fetched_at_utc`, bounded warnings/attempts, identity/unit/revision/legal evidence, and any
provider-declared unserved interval. The plan is deterministic, non-overlapping except for a declared
seam overlap, and gap-free over the provider-eligible request interval. A missing middle segment,
unknown transport/identity/budget outcome, or conflicting overlap is an atomic failure; no source is
skipped and no private partial rows escape.

The future aggregate contract is explicit:

- `FULL` means every requested provider-eligible session is covered by independently qualified
  segments, every segment/chunk total reconciles, seams agree under a frozen precision/date rule,
  there is no unknown interval, and `fetched_at_utc = max(real segment retrieval timestamps)`.
- `QUALIFIED_PARTIAL` means the ordered plan covers a provider-declared narrower bound with exact
  served and unserved counts and no unknown interval. It is never a claim of the full requested
  span.
- `COVERAGE_UNPROVEN` means any segment lacks a provider bound or response-backed evidence; it is
  not a partial or empty result. The top-level `source` would be a deterministic sanitized
  composite token ordered by the plan only after a future public contract freezes that rule, while
  segment provenance remains visible.

An incompatible fixing, futures series, ETF, domestic quote, annual/monthly observation, or derived
USD cross cannot be relabeled as one daily XAU/USD history. The current source-gap outcome therefore
keeps the new chain empty.

## Reopen criteria and lifecycle

Reopen only when all conditions below are available together (conjunctive, not “any one axis”):

1. one named owner/route/version/operation supplies a response-backed XAU/USD identity, USD/oz
   meaning, plain date, daily cadence, correction/revision behavior, and required fields;
2. the same exact unit declares 2018-01-01..2026-08-21 coverage, or a narrower `QUALIFIED_PARTIAL`
   bound with reconciled served/unserved/unknown counts;
3. the owner/licence clearly covers no-login automation or approved access, rate/retry/concurrency,
   cache/storage/retention, caller return, attribution, derivative/commercial use,
   redistribution/resale, and amendment/revocation;
4. transport evidence defines expected status and complete MIME, redirects, UA/WAF/session behavior,
   pagination/document bounds, compressed/decompressed byte ceilings, and finite numeric budgets;
5. a separate API/model decision freezes compatibility, immutable provenance/coverage/attempt
   carriers, no-false-absence semantics, same-source chunk manifests, and whether the exact
   deterministic `SegmentPlan`/aggregate contract above is allowed; and
6. the exact merged docs/source design passes blacklist, secret, diff, clean-tree, full offline,
   build, ancestry/path, and reviewer exact-SHA gates.

The lifecycle is immutable: **source qualification → API/model freeze → separate RED authorization
permits failing tests only → reviewer verifies RED and authorizes implementation → GREEN → code
review → exact approved publication**. This source-gap closure authorizes none of the later stages.

## Primary references

- [fawazahmed0 exchange-api repository](https://github.com/fawazahmed0/exchange-api) — official route pattern, fallback host, README claims, and repository licence link.
- [exchange-api generator](https://github.com/fawazahmed0/exchange-api/blob/main/currscript.js) and [publication workflow](https://github.com/fawazahmed0/exchange-api/blob/main/.github/workflows/run.yml) — daily publication/date-tag mechanics; not a coverage or source-data licence.
- [exchange-api CC0 licence](https://github.com/fawazahmed0/exchange-api/blob/main/LICENSE) — repository Work licence; not assumed to clear underlying rate data.
- [exchange-api root package manifest](https://github.com/fawazahmed0/exchange-api/blob/main/package.json) — root repository metadata; not the published package page.
- [npm package page for `@fawazahmed0/currency-api`](https://www.npmjs.com/package/@fawazahmed0/currency-api) — published package identity only; no underlying data rights are inferred.
- [jsDelivr terms](https://www.jsdelivr.com/terms/terms-of-use) — CDN use is subject to its own abuse/availability terms; not an unlimited crawl or data-rights grant.
- [The Perth Mint historical metal prices](https://www.perthmint.com/invest/information-for-investors/metal-prices/historical-metal-prices/) — official historical files, spot definitions, and disclaimer.
- [Stooq official site](https://stooq.com/) and [official daily-download path](https://stooq.com/q/d/l/) — route lead only; no OSS data-rights grant was retained.
- [Stooq operator page](https://stooq.pl/stooq/), [terms](https://stooq.pl/terms.html), and [robots policy](https://stooq.com/robots.txt) — operator and reuse/automation boundary; not a qualification response.
- [LBMA precious metal prices](https://www.lbma.org.uk/prices-and-data/lbma-precious-metal-prices) — benchmark identity, schedule, and licensing boundary.
- [LBMA Gold Price FAQ](https://www.lbma.org.uk/prices-and-data/lbma-gold-price/lbma-gold-price) — USD/troy-ounce benchmark identity and IBA licensing language.
- [World Gold Council gold prices](https://www.gold.org/goldhub/data/gold-prices) — frequency/unit description and ICE historical-data restriction.
- [World Gold Council methodology](https://www.gold.org/data/gold-price/methodology) and [terms](https://www.gold.org/terms-and-conditions) — vendor/frequency and reuse restrictions.
- [FRED API documentation](https://fred.stlouisfed.org/docs/api/fred/v2/) and [FRED API terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html) — API-key and third-party-rights boundary.
- [FRED notice on removal of daily LBMA series](https://news.research.stlouisfed.org/2022/01/ice-benchmark-administration-ltd-iba-data-to-be-removed-from-fred/) — current-availability boundary.
- [World Bank Commodity Markets](https://www.worldbank.org/en/research/commodity-markets) — official monthly/annual CMO cadence; not a daily substitute.
- Local current behavior: [`vnfin/gold/currency_api.py`](../../vnfin/gold/currency_api.py), [`docs/sources/gold-adapters.md`](../sources/gold-adapters.md), and [`docs/sources/gold-world-reference.md`](../sources/gold-world-reference.md).

## Bottom summary

- Disposition: **`SOURCE-GAP CLOSURE`**; no new multi-year gold chain is admitted.
- Current Currency API, Gold API, Stooq opt-in, failover, and annual World Bank behavior remain unchanged.
- No candidate proves response identity, 2018-current daily coverage, finite runtime, and OSS rights together.
- The current Currency API is constrained by its local `COVERAGE_START = 2024-03-02` guard and existing 1,100-day cap; this is not provider coverage or source absence, and chunking is not authorized.
- Stooq, Perth Mint, LBMA/IBA, WGC, FRED, and CMO retain explicit coverage/legal/identity gaps; no candidate dispatch was made.
- Future work requires conjunctive owner, identity, coverage, rights, transport, byte, and atomic-budget evidence.
- No probe, RED, API/model freeze, code, push, or close is authorized by this packet.
- Need from Boss: **nothing**; return the exact merged docs/backlog SHA for design review.
