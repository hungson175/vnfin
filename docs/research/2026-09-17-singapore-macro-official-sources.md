# #236 official-source research — Singapore macro coverage

**Research date:** 17 September 2026 (+07)  
**Target base:** `origin/master` `8d450a40cd9763a58bdb85c5f125edcc18d182da`  
**Issue:** `hungson175/vnfin#236`  
**Public intake:** `issuecomment-5714070058`  
**Phase:** source/API design only; no RED tests or production code

## Clean-room declaration

This research excludes VNStock and every VNStock-derived source. Every discovery query uses:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result may be opened, cited, compared, or used. Evidence is limited to repository
state at the target base and official World Bank, IMF, Singapore Department of Statistics
(SingStat), Monetary Authority of Singapore (MAS), and data.gov.sg surfaces. A government-owned
host is not treated as a permission grant; technical access and legal permission are evaluated
separately.

## Research question and frozen scope

Determine which of the ten existing provider-independent `MacroIndicator` cells can be supported
honestly for `SGP` without changing the public primitive:

```python
vnfin.macro.get_indicator("SGP", indicator) -> IndicatorSeries
```

The cells are `GDP`, `GDP_GROWTH`, `CPI`, `INFLATION`, `UNEMPLOYMENT`, `CPI_YOY`,
`POLICY_RATE`, `LENDING_RATE`, `DEPOSIT_RATE`, and `REAL_INTEREST_RATE`. The analysis retains
concept, returned identity, route behavior, coverage, revisions, units, actual/projection status,
and legal/runtime posture independently for every cell. No proxy, substitute, interpolation,
cross-source point stitch, hidden endpoint discovery, rendered-page scraping, or missing-value fill
is allowed.

## Pre-transport request ledger and hard ceilings

This plan was written before any #236 provider data-route dispatch. Three official-domain
search-engine discovery queries had already been made to locate public documentation; they were not
provider API/data requests and returned no retained provider rows. Discovery results remain subject
to direct official-page verification.

All provider probes below are sequential, `GET` only, have no retries, use a 5-second connection
timeout and 25-second total timeout, accept only an expected complete MIME, and stop on unexpected
authentication, WAF/HTML, redirect ownership, pagination, identity, or byte behavior. Redirects may
not leave the source owner's official host family. Each request has a 4 MiB compressed / 16 MiB
decompressed project safety ceiling unless a smaller route-specific ceiling is recorded. These are
local fail-closed ceilings, not provider-declared allowances. Only sanitized summaries and hashes
may be retained; no raw provider rows or response bodies are committed.

| Surface | Logical reservation | Physical ceiling | Purpose and stop rule |
|---|---:|---:|---|
| World Bank WDI v2 | 16 | 16 | One metadata plus one `SGP` observation request for each of the eight existing annual codes; no pagination follow-up |
| IMF DataMapper | 3 | 3 | One existing-adapter observation route for each supported annual fallback concept; no alternate endpoint discovery |
| SingStat | 7 | 7 | One machine-readable catalog/OpenAPI request plus at most six exact-table requests selected by stable table/series key |
| MAS | 4 | 4 | One official API/catalog contract request plus at most three exact candidate routes; stop before any subscription/Corppass/session path |
| data.gov.sg | 4 | 4 | At most two exact dataset metadata requests and their two documented download/data requests; no catalog dump |
| **Provider total** | **34** | **34** | Zero retries; an exhausted or failed reservation does not fall through to an unreserved route |
| Official docs/terms | 18 | 18 | Direct official documentation and terms pages only; no provider-row payloads |
| Search discovery | 6 | 6 | Official-domain queries only, including the three completed baseline queries; not counted as provider probes |

Logical usage is incremented when an exact candidate is reserved. Physical usage is incremented only
when transport is dispatched. A redirect hop counts as another physical request; because redirects
are not separately budgeted, any redirect requiring a second dispatch stops that route. If one
request contains more than one exact series, each series consumes a logical reservation but the
single dispatch consumes one physical reservation; unused physical capacity is not reused for a new
candidate. The final report must give observed logical and physical counts per surface.

## Required evidence schema

Every one of the ten final cell rows independently retains:

```text
indicator; exact concept/code; owner; route operator/version/method; requested/returned identity;
status and complete MIME; redirect/final host; auth/session/key; frequency; unit/currency/base;
level/rate/growth semantics; actual/estimate/projection; provider-declared and observed bounds;
count/nulls/interior gaps/duplicates/revisions/current lag; rate/concurrency/retry/page/byte limits;
terms version/effective date; automation; caller return; cache/storage/retention/deletion;
attribution; commercial/derivative use; redistribution; amendment/revocation.
```

Unknown or unretained evidence is stated as `NOT_RETAINED`/`NOT_CLEARED`; it is never converted to
zero, empty, denied, or permitted. Final statuses use the accepted vocabulary:
`QUALIFIED_EXISTING`, `QUALIFIED_NEW_SOURCE`, `PARTIAL`, `SEMANTICS_GAP`, `LEGAL_GAP`,
`ROUTE_GAP`, and `NO_DATA`.

## Evidence results

Pending bounded official-source inspection and sequential route probes.

## Legal and operational findings

Pending exact official terms and route-contract review.

## Candidate expansion ranking

Pending. Additional primitives are design candidates only and cannot add enum/model/API surface in
this phase.

## Request ledger result

Pending. The final ledger will report logical and physical usage, status, MIME, bytes, redirect
behavior, and stop reason without retaining provider rows.

## Sources

Pending direct official-page verification.

