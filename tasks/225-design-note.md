# #225 design note — authorized equity-fund discovery and NAV history

**Packet:** `tasks/225-equity-fund-nav-authorized-source-spec.md` at reviewer `7b7fe0b`
**Design phase:** source/design only
**Requested inclusive interval:** `2018-01-01..2026-08-19`
**Disposition:** **`SOURCE-GAP CLOSURE`**
**Research:** [`equity-fund NAV source vetting`](../docs/research/2026-08-23-equity-fund-nav-authorized-source-vetting.md)
**Published base:** `bdfe06bba330bdf36fec0cf7c18bb79e96e5c28e`
**Clean correction base:** `bdfe06bba330bdf36fec0cf7c18bb79e96e5c28e`; local activation `ae8087d` is excluded and is not an ancestor.

This is a documentation-only source/legal design. It does not add a source, model, accessor,
asset-type token, diagnostic carrier, RED test, production code, API capability, fund list, NAV
value, push, or issue closure. The current mutual-fund runtime and the #221 Fmarket disabled
boundary remain unchanged.

## 1. Decision and API boundary

The library may eventually expose the existing compatible primitives:

```python
vnfin.funds.source().list_funds(asset_type="STOCK")
vnfin.funds.source().nav_history(product_id, from_date=None, to_date=None)
```

No current provider proves the complete qualification tuple. Therefore this packet keeps the new
chain empty and chooses `SOURCE-GAP CLOSURE`:

- current `vnfin.funds.source()` / `client()` behavior remains lazy and Fmarket valid calls fail
  before cache/network with `SourceUnavailable("SOURCE_DISABLED_PENDING_PERMISSION")`;
- `Fund`, `FundList`, `NavPoint`, and `NavHistory` remain unchanged; current `Fund.id: int` is not
  widened or silently coerced for an unqualified provider;
- the existing synthetic Fmarket parser fixtures are not permission, coverage, identity, or
  redistribution evidence;
- #218 ETF evidence remains separate and cannot qualify open-ended equity mutual funds; and
- no source registration, new enum/error, public provider field, market-wide basket, fallback,
  stitch, batch, correlation, return, manifest, signal, or VN30F helper is introduced.

A source-gap design PASS authorizes only the three-path documentation publication/resolution/close
sequence. It does **not** authorize TDD or production code. A future qualified source must receive
a new source-specific design PASS, then a RED-first implementation/API review.

The legal identity gate is stricter than a product label: official securities-law material treats
"equity fund" as an investment-objective/category label, while open-ended funds, closed-ended funds,
member funds, and ETFs are distinct legal/product forms. An ETF is not an open-ended equity mutual
fund substitute. The manager calculates NAV and the supervisory bank confirms it; VSDC registration
or disclosure metadata cannot silently become the manager's NAV-history owner or a reuse licence.

## 2. Candidate decisions

Each row is one exact owner/route/operation/product-class unit. No wildcard route, grouped fund,
or cross-source identity is a qualification unit. A static page is not a provider response, a
registry is not a NAV owner, and a manager product page is not a market-wide universe.

| Unit | Exact route and retained evidence | Deterministic result |
| --- | --- | --- |
| Fmarket listing/discovery | Fincorp; `POST https://api.fmarket.vn/res/products/filter`; current valid calls are disabled before cache/network | `DISABLE_PENDING_PERMISSION`; no probe |
| Fmarket NAV history | Fincorp; `POST https://api.fmarket.vn/res/product/get-nav-history`; current valid calls are disabled before cache/network | `DISABLE_PENDING_PERMISSION`; no probe |
| SSIAM SSI-SCA discovery | `https://ssiam.com.vn/en/fund-information-ssi-sca`; official page identifies `SSI-SCA`, code, manager, and `Mutual Equity Fund`; response ID/bounds not retained | `SOURCE-GAP` |
| SSIAM SSI-SCA NAV history | `https://ssiam.com.vn/en/fund-information-ssi-sca`; daily NAV-report concepts are visible, but response schema/reconciliation/rights are not proven | `SOURCE-GAP` |
| SSIAM VLGF discovery | `https://ssiam.com.vn/en/ssiam/fund-information-vlgf`; official manager product route, response class/ID and bounds not retained | `SOURCE-GAP` |
| SSIAM VLGF NAV history | `https://ssiam.com.vn/en/ssiam/fund-information-vlgf`; exact history crosswalk, requested coverage and reuse terms not retained | `SOURCE-GAP` |
| SSIAM SSIBF discovery control | `https://ssiam.com.vn/en/products`; official catalogue identifies a bond product, not the requested equity class | `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| SSIAM SSIBF NAV-history control | `https://ssiam.com.vn/en/products`; no requested equity-mutual-fund history unit | `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| SSIAM FUESS product-row discovery control | `https://ssiam.com.vn/en/products`; official catalogue separates ETF rows from open-ended mutual funds | `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| SSIAM FUESS product-row NAV-history control | `https://ssiam.com.vn/en/products`; ETF rows are not silently mapped to `STOCK` | `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| VinaCapital VEOF discovery | `https://vinacapital.com/investment-solutions/onshore-funds/veof/`; official manager equity identity, provider ID and response fields not retained | `SOURCE-GAP / DOCUMENT_SUPPORT_ONLY` |
| VinaCapital VEOF NAV history | `https://vinacapital.com/investment-solutions/onshore-funds/veof/`; monthly document support is not daily history reconciliation | `SOURCE-GAP` |
| VinaCapital VESAF discovery | `https://vinacapital.com/investment-solutions/onshore-funds/vesaf/`; official open-ended equity identity, provider ID and response fields not retained | `SOURCE-GAP` |
| VinaCapital VESAF NAV history | `https://vinacapital.com/investment-solutions/onshore-funds/vesaf/`; dated reports do not prove a reconciled daily history | `SOURCE-GAP` |
| VinaCapital VDEF discovery | `https://vinacapital.com/investment-solutions/onshore-funds/vdef/`; official open-ended equity identity, provider ID and response fields not retained | `SOURCE-GAP` |
| VinaCapital VDEF NAV history | `https://vinacapital.com/investment-solutions/onshore-funds/vdef/`; dated reports do not prove a reconciled daily history | `SOURCE-GAP` |
| VCBF MGF discovery | `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-midcap-growth-fund/`; official equity page, response ID and bounds not retained | `SOURCE-GAP` |
| VCBF MGF NAV history | `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-midcap-growth-fund/`; report schema, pages, bounds and revision not reconciled | `SOURCE-GAP` |
| VCBF BCF discovery | `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-blue-chip-fund/`; official equity page, response ID and bounds not retained | `SOURCE-GAP` |
| VCBF BCF NAV history | `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-blue-chip-fund/`; report schema, pages, bounds and revision not reconciled | `SOURCE-GAP` |
| VCBF AIF discovery | `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-active-income-fund/`; official equity page, response ID and bounds not retained | `SOURCE-GAP` |
| VCBF AIF NAV history | `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-active-income-fund/`; report schema, pages, bounds and revision not reconciled | `SOURCE-GAP` |
| Eastspring EVESG discovery | `https://www.eastspring.com/vn/en/funds/enf/funddetails/eastspring-investments-vietnam-esg-equity-fund/evesg`; official equity page/report code | `SOURCE-GAP` |
| Eastspring EVESG NAV history | `https://www.eastspring.com/vn/en/funds/archive-documents/investor-relations/evesg`; dated archive exists, machine reconciliation and reuse consent are not proven | `SOURCE-GAP` |
| Manulife MAFEQI discovery | `https://www.manulifeim.com.vn/funds/fund-details.fid-MAFEQI.html`; official open-ended equity identity | `SOURCE-GAP` |
| Manulife MAFEQI NAV history | `https://www.manulifeim.com.vn/funds/fund-details.fid-MAFEQI.html`; history response/crosswalk and terms are not proven | `SOURCE-GAP` |
| Dragon Capital DCDS discovery | `https://dautu.dragoncapital.com.vn/dcds`; official equity product identity | `SOURCE-GAP` |
| Dragon Capital DCDS NAV history | `https://dautu.dragoncapital.com.vn/dcds`; public material attributes NAV sourcing externally; independent owner not proven | `SOURCE-GAP / NAV_OWNER_GAP` |
| Dragon Capital DCDE discovery | `https://dautu.dragoncapital.com.vn/`; official catalogue equity product identity | `SOURCE-GAP` |
| Dragon Capital DCDE NAV history | `https://dautu.dragoncapital.com.vn/tin-tuc/chuyen-muc/bao-cao-quy`; periodic reports do not prove a reconciled daily history | `SOURCE-GAP` |
| VSDC registry context | `https://vsd.vn/en/`; official registry/service context, not a same-owner NAV response | `SOURCE-GAP / REGISTRY_NOT_NAV_OWNER` |
| SSC disclosure context | `https://ssc.gov.vn/`; official regulatory/disclosure context, not a library NAV response | `SOURCE-GAP / DISCLOSURE_CONTEXT_ONLY` |
| Unreviewed, copied, paid, login, private, proxy, or reporter routes | No evidence admitted; no request made | `EXCLUDED`; never fallback |

No candidate is `QUALIFIED FOR TDD` or `QUALIFIED_PARTIAL`. `PARTIAL` is reserved for a future
qualified provider that declares and reconciles a narrower own-history boundary.

### Primary source anchors

- [SSIAM SSI-SCA](https://ssiam.com.vn/en/fund-information-ssi-sca), [VLGF](https://ssiam.com.vn/en/ssiam/fund-information-vlgf),
  [products](https://ssiam.com.vn/en/products), and [terms](https://ssiam.com.vn/en/ssiam/term-condition)
- [VinaCapital VEOF](https://vinacapital.com/investment-solutions/onshore-funds/veof/),
  [VESAF](https://vinacapital.com/investment-solutions/onshore-funds/vesaf/),
  [VDEF](https://vinacapital.com/investment-solutions/onshore-funds/vdef/), and [terms](https://vinacapital.com/terms-and-conditions/)
- [VCBF MGF](https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-midcap-growth-fund/),
  [BCF](https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-blue-chip-fund/), and [NAV reports](https://www.vcbf.com/en/investor-relations/fund-reports/net-asset-value-change-report/)
- [Eastspring EVESG](https://www.eastspring.com/vn/en/funds/enf/funddetails/eastspring-investments-vietnam-esg-equity-fund/evesg)
  and [disclaimer](https://www.eastspring.com/vn/en/disclaimer)
- [Manulife MAFEQI](https://www.manulifeim.com.vn/funds/fund-details.fid-MAFEQI.html) and [terms](https://www.manulifeim.com.vn/terms-of-use.html)
- [Dragon DCDS](https://dautu.dragoncapital.com.vn/dcds) and [catalogue](https://dautu.dragoncapital.com.vn/)
- [VSDC fund services](https://vsd.vn/en/) and [fund managers/registration](https://vsd.vn/en/qlq)
- [SSC official portal](https://ssc.gov.vn/) for the reviewed securities-law/disclosure documents;
  query-bearing document locators are deliberately not retained.

## 3. Evidence and accounting contract

The source-vetting artifact keeps static document research separate from candidate dispatch:

| Channel | Logical | Physical | Pages/cursors | Retries | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| Official static pages/PDFs/terms | `NOT_RETAINED` / `NOT_MEASURED` | `NOT_RETAINED` / `NOT_MEASURED` | `NOT_RETAINED` | `NOT_RETAINED` | Evidence only; no HTTP method or future quota claim |
| Candidate discovery/history dispatch | `0` | `0` | `0` | `0` | No candidate data/API route called |
| Fmarket dispatch | `0` | `0` | `0` | `0` | Explicit no-probe #221 boundary |

All missing route, complete MIME, effective redirect, UA/session/WAF, byte, page, cursor, response
identity, publication, revision, coverage, rate, retry, cache, retention, or reuse fields are
explicitly `NOT_RETAINED`, `NOT_PROBED`, `UNKNOWN`, or a typed gap. They are never replaced with
zero, empty, absence, permission, or a fabricated provider claim.

## 4. One-source qualification contract

A future source unit is qualified only when one named owner and route/version prove all of these
without cross-source repair:

1. **Discovery identity:** stable owner-backed fund code and provider product ID; response-backed
   fund name, manager/issuer, open-ended equity class, currency, and latest NAV/unit identity.
2. **History identity:** the same source supplies the history ID or documents a stable crosswalk
   from its own discovery ID; registry IDs, ISINs, codes, or manager names from another owner do
   not become implicit keys.
3. **Observation identity:** each row is provider-published NAV per fund unit with an exact date,
   finite positive non-boolean numeric value when required by the source, exact currency/unit,
   selected product identity, and ascending unique order.
4. **Time identity:** NAV/as-of date, publication/knowability date, revision/correction date, and
   library `fetched_at_utc` remain separate. Missing publication time is `NOT_RETAINED`; no session,
   UTC cutoff, or same-day availability is fabricated from a NAV date.
5. **Transport identity:** canonical owner host/path/version, method, complete Content-Type,
   normalized MIME, redirect/effective route, status, auth/session/UA/WAF behavior, body/decoded
   byte bounds, page/cursor and retry behavior are explicit.
6. **Legal identity:** automation, rate/retry/concurrency, transient/cache/storage/retention/
   deletion, attribution, commercial use, caller-facing return, derivative use, redistribution,
   resale, amendment, revocation, and data revision/correction terms cover the exact route and
   library use.

### 4.1 Fund-class and ID predicates

- `asset_type="STOCK"` is not a provider query result by itself. Success requires response-backed
  open-ended equity identity.
- ETF, balanced, bond, money-market, pension, closed-end, unknown, missing, contradictory, or
  name-only classifications are not silently mapped to `STOCK`.
- A source-specific route may qualify only the fund IDs it owns and proves. One manager page cannot
  claim a market-wide catalogue.
- Existing `Fund.id` compatibility is protected. A future source needing a different provider-ID
  type must receive an explicit API/model review; no string-to-int, code-to-ID, or registry-to-NAV
  coercion is implied here.

## 5. Coverage and no-false-absence contract

The future public result semantics require a fresh API review, but these qualification predicates
are fixed:

| State | Required evidence | Result rule |
| --- | --- | --- |
| `FULL` | Provider-declared bounds cover the requested interval; points/totals/pages/cursors reconcile; no unexplained interior gaps; cadence/non-publication is declared | Only then is requested coverage full |
| `PARTIAL` | Same qualified provider declares a narrower supported boundary and reconciles all points inside it | Boundary is exposed; never relabeled requested `FULL` |
| `UNKNOWN` | Any missing route, class, ID, publication, revision, page, total, cursor, or legal/runtime axis | Fatal/inconclusive; not empty or absent |
| `EMPTY` | Provider-authoritative, identity-matched, reconciled empty response for a valid supported query | Typed empty is allowed only here |
| `COVERAGE_GAP` | A qualified response or owner declaration proves a boundary excludes requested dates | Never emitted by this no-probe packet |

A blank document, maintenance HTML, WAF/challenge, timeout, connection failure, missing page,
unknown calendar, unreconciled total, or transport truncation is not `EMPTY` or `COVERAGE_GAP`.
It is an inconclusive typed source/coverage failure. An empty result is not unconditionally fatal:
only an unauthoritative, identity-unmatched, unreconciled, or transport-truncated empty response is
fatal. The authoritative-empty and fatal-empty branches are paired future RED cases. Any private
partial accumulator is discarded atomically.

## 6. Future public-call and failure design (not current API)

After a fresh qualified-source design PASS, preserve the current call shapes and carriers where
compatible:

```python
vnfin.funds.source(http_get=None, timeout=25.0)
source.list_funds(asset_type=None, search="", page_size=100, include_metadata=True)
source.nav_history(product_id: int, from_date=None, to_date=None)
# vnfin.funds.client is the source alias with the same signature
```

Current `from_date` and `to_date` each accept `datetime.date` or an ISO `YYYY-MM-DD` string. Bounds
are validated before cache/network. The direct source/factory/client signatures and every optional
`list_funds` parameter remain unchanged in the future RED matrix. Existing metadata carriers are
also fixed: `FundList` carries collection `source`, `currency`, `fetched_at_utc`, and `warnings`;
`Fund` has no per-fund fetched/warnings fields; `NavHistory` carries `product_id`, `code`, `source`,
`currency`, `fetched_at_utc`, and `warnings`; `NavPoint` carries only date/nav. Any per-`Fund`
metadata change is deferred to a fresh API/model review.

The RED-first matrix must establish these exact behaviors before implementation:

- malformed/unsupported asset type, product ID, and either accepted date form fail before cache/network;
- positive discovery requires response-backed equity identity, stable code/product ID, manager/issuer,
  currency and NAV/as-of metadata;
- history requires the same-source product binding, exact NAV date/unit/currency, ordering, revision,
  declared bounds, page/total/cursor reconciliation, and no silent product mixing;
- wrong product/fund/date/unit/currency, bool/non-numeric/non-finite NAV, duplicate/conflicting date,
  malformed total/page/cursor, mixed product, silent revision drift, and out-of-window rows fail
  closed with no partial result;
- provider publication/as-of limits remain visible; no publication timestamp is fabricated;
- current `SourceUnavailable("SOURCE_DISABLED_PENDING_PERMISSION")` remains the exact Fmarket
  disabled carrier and is checked before cache lookup/network for direct/factory/alias calls;
- all new provider diagnostics are bounded and sanitized; raw URLs/queries, bodies, headers,
  cookies, sessions, credentials, provider prose, and unbounded names/IDs never reach public text;
- no public enum, error carrier, batch, correlation, return, manifest, signal, or VN30F helper is
  introduced by this source-gap packet.

Exact public exception/result carriers remain deferred until a qualified owner route and legal
terms are reviewed; no speculative public carrier is frozen now.

## 7. Global budget and transport contract

No numeric budget is source-approved in this source-gap packet. Once one owner route qualifies, the
reviewed scheduler must use one finite sequential global ledger covering logical targets, physical
calls, pages/cursors, retries, redirects, compressed bytes, decompressed bytes, and any approved
pacing.

Rules:

1. Reserve every applicable unit atomically before dispatch. A failed reservation makes zero network
   calls; capability skips consume no dispatch and do not become fake attempts.
2. Owner-approved retries reuse the same logical target and global ledger. Hidden client retries,
   per-date fan-out, unbounded redirects, and cross-source stitching are forbidden.
3. Charge streamed compressed bytes and decompressed bytes as separate counters atomically after
   dispatch/decompression. Either byte ceiling is fatal and discards private partial rows.
4. Redirect/effective-route, status, MIME, page/count/cursor, identity, revision, or any budget
   failure returns no false empty or partial history.
5. Retain only bounded sanitized **real** attempts. Never fabricate a final attempt or a
   `diagnostics_truncated` attempt. Any diagnostic cap requires a separately reviewed bounded carrier.
6. For JSON routes, parse the complete `Content-Type` value after the first colon, normalize it,
   and require the exact approved media type. Generic maintenance HTML is rejected. PDF/document
   routes need a separately reviewed owner-declared media/parser contract.

## 8. Legal reopen gate

A source may leave `SOURCE-GAP CLOSURE` only after a fresh written owner/source review binds one exact
route set to all of the following:

- official owner and product-class identity;
- no-login automation, allowed UA/session/WAF behavior, rate, retry, concurrency, timeout and
  maintenance rules;
- caller-facing typed return, derivative use, cache/storage, retention/deletion, attribution,
  commercial use, redistribution/resale;
- effective version, revision/correction, amendment and revocation/withdrawal handling;
- requested or owner-declared partial coverage, page/count/cursor reconciliation, publication and
  non-publication semantics; and
- finite logical/physical/page/retry ceilings, a finite redirect ceiling, and separate finite
  compressed-byte and decompressed-byte ceilings, with atomic pre-dispatch reservation and atomic
  post-dispatch stream/decompression exhaustion. Any exhaustion returns no false empty or partial.

Fmarket remains a separate `DISABLE_PENDING_PERMISSION` unit. Only a fresh written Fincorp response
that names both exact Fmarket operations, automated access, caller return, storage/retention,
commercial/attribution/redistribution, rate/retry/WAF/session, version/effective date, amendment,
and revocation can reopen it. No other source overrides that state.

## 9. Future RED/release matrix

A source-specific design PASS must precede a separate RED-first implementation line. The future
review must cover:

- SSI-SCA-style equity positive plus ETF/bond/non-equity/unknown/missing/contradictory negatives;
- discovery/history ID binding and cross-source-ID rejection;
- exact NAV date, unit, currency, finite numeric value, publication limitation, revisions,
  duplicates/conflicts, full/partial/empty/unknown, page/count/cursor and requested boundaries;
- status/MIME/redirect/WAF/timeout/connection/retry/byte/global-budget and atomic no-partial cases;
- bounded diagnostics, UTC-aware retrieval metadata, DataFrame attrs, repr/equality/serialization;
- exact permission/rate/cache/retention/revocation enforcement with Fmarket still disabled;
- current imports, models, factories, aliases, diagnostics, public snapshots, all other domains,
  docs/tutorials/AI skill/architecture/CHANGELOG/release notes; and
- full offline tests, isolated sdist/wheel, blacklist/secret/diff/path/object/clean-tree gates.

No live provider rows or real fund basket may be committed as fixtures; future executable tests use
synthetic payloads only.

## 10. Lifecycle and publication boundary

Current lifecycle is reviewer-owned `DESIGN_REVIEW`, actor `vnfin-oss-reviewer`, next
`RETURN_EXACT_SHA_DESIGN_VERDICT`, packet anchor `7b7fe0b`. The prior BLOCK at exact
`24363bfe887a7f4c9e269fe9ac1034a63f959069` is recorded before this correction with report
`reviews/review-202608240153-issue225-design-source-gate.md` at reviewer `d7118d4`. This clean
correction is rebuilt directly from published base `bdfe06bba330bdf36fec0cf7c18bb79e96e5c28e`;
local activation `ae8087d` is excluded and is not an ancestor. The final backlog-only handoff names
the exact content anchor and the final merged review anchor while preserving this reviewer-owned
phase.

If the reviewer grants a documentation-only `SOURCE-GAP CLOSURE` PASS:

1. rerun merged docs/full/build/blacklist/secret/diff/path/object gates;
2. push only the approved exact anchor from the approved ancestry, never the excluded local receipt;
3. verify remote exact HEAD, base ancestry, excluded local objects, and exactly these three paths:
   `docs/research/2026-08-23-equity-fund-nav-authorized-source-vetting.md`,
   `tasks/225-design-note.md`, and `tasks/active-backlog.md`;
4. post a clean no-capability `SOURCE-GAP` resolution, close/re-read #225, and only then activate
   the next queue item according to the reviewer-provided order.

If a qualified-source PASS is granted instead, do not publish or close from this document; transition
to a fresh RED-first implementation/API review. No probe, RED, code, push, or close occurs before
the applicable exact-SHA PASS.

## Bottom summary

- Decision: **`SOURCE-GAP CLOSURE`**; the new equity-fund/NAV chain stays empty.
- SSIAM SSI-SCA is promising official manager evidence, but route schema, history reconciliation, and legal reuse remain gaps.
- VinaCapital is document support only; VSDC/SSC are registry/disclosure context, not NAV owners.
- Fmarket remains `DISABLE_PENDING_PERMISSION` and was not probed; #218 ETF evidence is not generalized.
- Current models, factories, aliases, and disabled-source behavior are unchanged.
- Future qualification requires one-source identity/binding, FULL/PARTIAL proof, atomic budgets, and explicit legal axes.
- No RED, production code, source registration, push, or close is authorized before exact design PASS.
