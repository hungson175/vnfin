# #233 public fund/ETF listing and NAV-history design note

**Phase:** `SOURCE_DESIGN`
**Disposition:** `SOURCE_GAP_CLOSURE`
**Clean published base:** `ed55c0487745b2611bcef9a7d94e259907ec06b0`
**Packet:** `tasks/233-public-fund-etf-listing-nav-spec.md` @ `f426e85322d565f85efd25b00b39807c628124f7`
**Public triage:** `issuecomment-5415312502`
**Final actor/next:** `vnfin-oss-reviewer` / `RETURN_EXACT_SHA_DESIGN_VERDICT`

## Decision

The public fund/ETF listing plus provider-published NAV-history chain remains empty. No exact
owner-backed route set closes product identity, NAV semantics, coverage, finite atomic transport,
and public-OSS reuse rights conjunctively. This is a source-gap result, not an API or capability
claim.

The companion report
`docs/research/2026-08-26-public-fund-etf-listing-nav-source-vetting.md` is the exact evidence
record. It separates last-retained #218/#221/#225 facts from the #233 no-probe delta, names one
unit per operation/product class, and carries the full transport/budget/legal ledger. This note
freezes the compatible design boundary without adding a provider, endpoint, product row, NAV value,
fixture, model, API carrier, RED test, or runtime capability.

## Delta and evidence status

| Baseline | Immutable anchors | Last-retained disposition | #233 status |
|---|---|---|---|
| #218 ETF discovery/NAV | `e78ddf7201fbadad7a24090e29ef63aa4868b980`; `412ada80705ecf08b2da4e27d882dbf3bc256327` | `SOURCE_GAP_CLOSURE` | `NOT_RECHECKED`; VinaCapital VN100 ETF and ETF-context units only; SSIAM open-ended units bind to #225 |
| #221 Fmarket terms/runtime | `6949a53ecd46dc61197afb9eee8dd245109ef95c`; `eaace3d6e3049b3546b82c5da6a2dfdcb31e9b11` | `DISABLE_PENDING_PERMISSION` for four operations | Runtime boundary preserved; legal terms `NOT_RECHECKED` |
| #225 equity-fund listing/NAV | `35fd9ceb871ba3e7aab0a87f3924d37342652420` | `SOURCE_GAP_CLOSURE` | `NOT_RECHECKED`; SSIAM open-ended, VinaCapital open-ended, VCBF, Eastspring, Manulife, Dragon DCDS/DCDE, VSDC, and SSC units; retain route-local restrictions |
| #233 combined primitive | This note and the companion report | New source design | `SOURCE_GAP_CLOSURE`; empty chain |

No provider/API route was called. “Last retained” is not a current-term assertion. The packet
imposes no historical interval; the declared inception context of an inherited candidate is not
promoted into a #233 coverage failure. VinaCapital ETF evidence remains #218; SSIAM open-ended
evidence and VLGF remain #225. SSIAM is not moved into the ETF baseline, and VLGF product form
stays `NOT_RETAINED`.

## Product and compatibility boundary

`nav_history` means provider-published NAV per fund unit. Exchange close and iNAV remain prices,
not NAV, and cannot repair missing dates. Missing stays missing: no zero-fill, forward-fill,
interpolation, proxy, close/iNAV substitution, cross-owner repair, or inferred publication time.

Preserve the current public signatures and aliases until a qualified source receives a separate
API/model review:

```python
vnfin.funds.source(http_get=None, timeout=25.0)
source.list_funds(asset_type=None, search="", page_size=100, include_metadata=True) -> FundList
source.nav_history(product_id: int, from_date=None, to_date=None) -> NavHistory
vnfin.funds.client  # alias of source with the same signatures
```

`Fund.asset_type` is the current Fmarket `dataFundAssetType.code` asset-class field, such as
`STOCK`, `BOND`, or `BALANCED`. It does not distinguish ETF, open-ended, closed-end, or other legal
product form. A caller filter is not response evidence. A future typed `product_type` (or equivalent)
requires a fresh API/model decision and is not frozen here.

Current date inputs remain backward-compatible: `datetime.date` is accepted; `datetime.datetime`
is converted with `.date()`; and a string is stripped with `.strip()` before the strict zero-padded
`YYYY-MM-DD` check. These inclusive bounds validate before cache/network; a breaking change needs a
separate API review. `page_size` never authorizes an unreconciled first page; a qualified adapter
drains and reconciles pagination under one finite atomic budget or returns no partial result.

## Four-operation Fmarket boundary

All four existing operations remain disabled and unprobed:

| Operation | Repository compatibility route | Disabled contract |
|---|---|---|
| `list_funds` | `POST /res/products/filter` | `SourceUnavailable("SOURCE_DISABLED_PENDING_PERMISSION")` before cache/network |
| `nav_history` | `POST /res/product/get-nav-history` | Same exact exception/reason before cache/network |
| `holdings` | `GET /res/products/{id}` | Same exact exception/reason before cache/network |
| `asset_allocation` | `GET /res/products/{id}` | Same exact exception/reason before cache/network |

The route/method labels are repository compatibility facts; provider status, MIME, redirect,
session, UA/WAF, and permission are `NOT_PROBED` or `NOT_RECHECKED`. The direct class, factory, and
alias paths retain zero-call behavior. Written permission must name all four operations, exact host
and routes, automation, caller return, cache/storage/retention, attribution, commercial/derivative
use, redistribution, rate/retry/WAF/session, version, amendment, revocation, and correction.

## Independent ledger and qualification contract

The companion report has 36 rows, one for every exact owner/operator, canonical path, route-version,
operation, and product-class unit. The ETF and open-ended SSIAM classes are separate; VEOF, VESAF,
and VDEF each have listing and NAV units; DCDS and DCDE each have listing and NAV units. No row
inherits another row's evidence. The table's semicolon-delimited named fields are independently
parseable and binding:

- transport: observation/method, status, complete `Content-Type`, redirect/effective identity,
  auth/session/UA/WAF;
- identity: provider ID/code, name, manager/issuer, explicit product form, currency, NAV value
  kind/unit, NAV date, publication date, revision date, retrieval timestamp;
- coverage: provider/observed bounds, cadence/non-publication, points/funds, totals, pages/cursors,
  gaps, duplicates/conflicts, truncation, and outcome;
- budget: static-read markers, logical, physical, documents, pages, retries, redirects, compressed
  bytes, decompressed bytes, concurrency, rate window, backoff, per-unit atomic reservation, and
  total/global reservation; and
- legal: automation, transient use, cache/storage/retention/deletion, caller return, attribution,
  commercial, derivative, redistribution/resale, rate/retry/concurrency, amendment, revocation,
  correction, retained restriction, and exact inherited legal reference.

The #233 candidate dispatch tuple is genuinely zero because no route was called. Static-read
telemetry is independently `NOT_RETAINED`/`NOT_MEASURED`; it is never represented as zero runtime
attempts. `FULL` needs provider-declared bounds plus complete reconciliation; `PARTIAL` needs a
provider-declared narrower boundary plus reconciliation; `EMPTY` needs an authoritative,
identity-matched, supported empty response; otherwise the result is `UNKNOWN`/failure, not absence.

The exact table preserves route-local inherited legal restrictions: #218's VinaCapital ETF and
HOSE/Dragon ETF-context units retain `LEGAL_GAP` rather than a reuse grant; #225's SSIAM units retain
the no-public-API/caller-return/cache/retention/redistribution gap; VinaCapital retains its
copyright-only/no-OSS-grant gap; VCBF retains all-rights-reserved/no-public-licence; Eastspring
retains consent-required copying/circulation/distribution; Manulife retains consent-required reuse;
Dragon DCDS/DCDE retain the independent-NAV-owner gap; and #221 Fmarket rows bind `F221` to each
exact operation's `DISABLE_PENDING_PERMISSION` terms. `NOT_RECHECKED` does not erase any of those
negative route-local facts.

## Runtime, legal, and future RED gates

No numeric source budget is authorized. A future scheduler reserves all budget dimensions atomically
before dispatch, charges retries to the same ledger, charges compressed and decompressed bytes
separately, bounds redirects and diagnostics, and discards all private partial state on exhaustion,
unreconciled pages, identity/MIME/status/revision failure, or any fatal diagnostic. It never
fabricates an attempt or truncation marker and never exposes raw URL/query, body, headers, cookies,
session, credentials, provider prose, or unbounded IDs.

Public reachability, PDF availability, exchange disclosure, registry context, robots, or a working
browser request is not reuse permission. The legal route gate remains conjunctive and route-local.

After a qualified-source design PASS only, a fresh RED/API review must cover: lazy construction;
invalid filter/product/date/page inputs before cache/network; preserve `datetime.date`,
`datetime.datetime` to `.date()`, and surrounding whitespace around strict zero-padded ISO while
rejecting malformed forms; product-form positives and unknown/missing/contradictory negatives;
same-owner binding and cross-owner rejection; NAV versus close/iNAV; bool/non-finite/non-positive/
malformed values; malformed top-level/provider envelopes separately from malformed numeric values;
date/order/duplicate/revision cases; `FULL`/`PARTIAL`/`EMPTY`/`UNKNOWN`; pages/totals/cursors;
complete MIME parsing after the first colon; status/redirect/WAF/timeout/connection; retry/backoff;
rate-window exhaustion; logical, physical, document/page, compressed/decompressed-byte, and
total/global atomic-budget exhaustion; atomic no-partial results; sanitized source/attempt/error/
warning/coverage carriers; UTC-aware retrieval metadata, DataFrame attrs, `repr`, equality,
serialization; all four disabled Fmarket operations through direct/factory/alias paths; and full
docs/build/security/snapshot gates.
These are deferred tests only; no RED, API/model freeze, or code is authorized now.

## Lifecycle and post-PASS transition

The BLOCK was recorded first in clean-base backlog commit
`e6b777671eedc531d23aed6eff64113864c1b269`, targeting reviewed `6a97eb7` with report commit
`93b368d0628917c81903b30d0c7334f85db5a38b`. Its immutable actor field says
`vnfin-oss-reviewer`, but that historical expected correction actor is erroneous: a BLOCK continues
to the builder, so the expected actor for `DOCS_ONLY_CORRECTION_FROM_CLEAN_BASE` was `vnfin-oss`.
The immutable commit cannot be rewritten; this explicit correction keeps recovery reconstructable.
The packet anchor is `f426e85322d565f85efd25b00b39807c628124f7` and public triage is
`issuecomment-5415312502`. The latest BLOCK target is
`d94049c6c7697a865b2593769bf729843297b328`, delivery `f72e3483`, report
`reviews/review-202608260237-issue233-corrected-design-rereview.md`, reviewer commit
`029e330988ee3b68656c251f81fb527f25f0d70c`. The current correction actor is `vnfin-oss`; after
this correction the final handoff actor/next is `vnfin-oss-reviewer` /
`RETURN_EXACT_SHA_DESIGN_VERDICT`, with clean base `ed55c048...`.

Before exact design PASS, preserve the empty chain, current API, four-operation Fmarket disablement,
NAV-only semantics, and no probe/RED/API-model/code/source/push/close gate. The backlog correction
also restores #232's published `DONE/CLOSED` facts before final handoff.

If this source-gap design passes, publication is not an informal “docs-only close.” The exact
allowed transition is: (1) rerun merged exact-anchor gates; (2) push only the exact approved
three-path lineage; (3) verify remote HEAD, base ancestry, and paths; (4) post a clean public
SOURCE-GAP/no-capability resolution; and (5) close and re-read #233 `CLOSED/COMPLETED`. This still
does not authorize provider probes, RED, API/model decisions, source registration, production code,
runtime capability, or coverage claims.

### Bottom summary

- #233 remains `SOURCE_GAP_CLOSURE` with an empty listing/NAV chain.
- Inherited #218/#221/#225 facts are last-retained and `NOT_RECHECKED`, with VinaCapital ETF bound to #218 and SSIAM open-ended evidence bound to #225.
- `asset_type` is an asset-class code, not an ETF/open-ended product discriminator.
- All four Fmarket operations remain disabled and unprobed with the exact zero-call boundary.
- Per-unit transport, identity, coverage, budget, and legal axes are explicit and independent.
- NAV-only and missing-stays-missing semantics remain binding.
- Final actor/next are `vnfin-oss-reviewer` / `RETURN_EXACT_SHA_DESIGN_VERDICT`.
- No probe, RED, API/model, code, source, push, or close before exact design PASS.
