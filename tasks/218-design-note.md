# #218 design note — ETF discovery and provider-published NAV history

**Status:** `SOURCE-GAP CLOSURE`; exact-SHA source/design only; no RED, code, source registration,
model/accessor change, push, or close
**Packet:** `tasks/218-etf-discovery-nav-history-spec.md` at reviewer `5acb355`
**Research:** [`docs/research/2026-08-23-vn-etf-discovery-nav-history-source-vetting.md`](../docs/research/2026-08-23-vn-etf-discovery-nav-history-source-vetting.md)
**Requested inclusive span:** `2018-01-01..2026-08-19`
**Published base:** `8350329d3d881e34df62937aacf7ea4d74f99f91`
**Current published tree:** `8d1490fbda0aaaf217d9b98a51cd38c84dfaee16`
**Local activation:** `77671d42d9be16d1c4264397cf9939c266f6b4d8` (backlog-only and unpushed)

This note is the exact design handoff for a documentation-only source-gap closure. It does not
authorize a new ETF token, public model, parser, source registration, runtime call, RED test, or
coverage assertion. The current Fmarket surface remains open-ended mutual funds. Discount,
first-difference, replay, strategy, and VN30F comparison stay caller-side.

## 1. Decision and source-gap boundary

`SOURCE-GAP CLOSURE` is the only qualified disposition for the requested Fmarket-backed capability.
The reviewed official Fmarket catalogue and product pages describe open-ended funds; the official
Fmarket terms restrict software collection/copying/monitoring and do not grant API automation,
caller return, storage, or redistribution rights. Fmarket's own ETF explainer establishes only a
conceptual distinction, not an ETF product row or data route.

Official manager/exchange documents corroborate that Vietnamese ETFs and provider-published NAV
reports exist, but they do not bind those products to Fmarket's `product_id` or route and do not
provide an OSS runtime/redistribution grant. Cross-source ticker matching is not allowed to repair
that gap. No candidate therefore passes the complete source unit:

```text
owner + exact route/version + response-backed ETF product identity
+ code/product/detail/NAV binding + provider-published NAV semantics
+ requested or declared partial coverage + bounded runtime
+ lawful automation/caller-return/storage/redistribution posture
```

The future daily/caller-side calculations are not part of this source gap and no existing annual or
other fund behavior is changed.

## 2. Current API and compatibility contract

The exact v0.2.0/current comparison leaves these public seams unchanged:

```python
src = vnfin.funds.source()
listing = src.list_funds(
    asset_type="ETF", search="E1VFVN30", include_metadata=True
)
history = src.nav_history(
    product_id, from_date="2018-01-01", to_date="2026-08-19"
)
```

The snippet is a future compatibility target, not a working capability. In the current adapter:

- `list_funds()` is documented for the provider's existing mutual-fund asset classes;
- the current adapter forwards an asset string to `fundAssetTypes`, but no official evidence proves
  that `ETF` is a provider token or that it means product type rather than investment asset class;
- an empty `ETF` result is not confirmed empty and must not be broadened to all funds or fuzzy-matched
  locally;
- `nav_history()` requires a response-backed provider product ID and currently serves the existing
  open-ended-fund contract only; no ETF ID is known;
- `Fund.asset_type` is a provider asset-class field, not a proven ETF product-type field; and
- `Fund`, `FundList`, `NavPoint`, and `NavHistory` remain byte-compatible and unchanged in this note.

A future implementation may translate a normalized public `asset_type="ETF"` selector to a
provider-specific token only after official response/docs proof. It must preserve existing arbitrary
legacy asset strings and must not silently reinterpret an empty filter. If the provider cannot prove
that selector, a future implementation must return a typed source/selector outcome before network
rather than `EmptyData`; the exact public exception/message requires a fresh RED/API review and is
not frozen here.

For future ETF code inputs, the design-only grammar is: trim ASCII spaces, uppercase, require one
ASCII letter followed by at most 15 ASCII letters/digits, and reject punctuation, internal/control
characters, blank values, and overlong values before network. This is a future validation contract,
not a change to the current fund-code helper. Legacy fund asset strings remain compatibility-sensitive.

## 3. Qualification unit and identity predicates

Discovery and NAV history are separate route units but qualify only conjunctively for the same
selected product. A future positive fixture must prove:

1. the provider response accepted the ETF selector or exact code search and identifies product type
   `ETF` independently from an investment asset class such as equity or bond;
2. the selected row contains a public code, legal fund name, manager, provider `product_id`, and
   exchange/listing identity where the owner publishes it;
3. a detail response, if used, repeats the same provider ID/code/name/product type without duplicate,
   renamed, delisted, share-class, or cross-product ambiguity;
4. every NAV row either carries the same provider ID or is provably scoped to the selected ID; a
   present wrong, null, boolean, or malformed ID fails closed;
5. code, product ID, legal name, manager, and listing identity are all response-backed; no name-only
   fuzzy match, market quote, or cross-source join can complete a missing field; and
6. a second discovery row with the same canonical code or ID is an identity failure, not a dedupe.

The existing provider route baseline is:

| Unit | Existing repository route baseline | Future required proof | Current disposition |
| --- | --- | --- | --- |
| ETF discovery | `POST https://api.fmarket.vn/res/products/filter` | Official selector/token, exact body, success envelope, response identity, totals/pages, MIME, redirect/WAF and legal permission | `SOURCE-GAP` |
| Selected-product detail | `GET https://api.fmarket.vn/res/products/{id}` | Stable ID-to-code/product/manager/type/listing binding, exact MIME, legal permission | `SOURCE-GAP` |
| ETF NAV history | `POST https://api.fmarket.vn/res/product/get-nav-history` | Same product ID, provider-published NAV field, date/unit/currency/revision semantics, pages/totals/cadence, legal permission | `SOURCE-GAP` |

The route names above are current repository assumptions for mutual funds, not current ETF API proof.
No direct API dispatch was made because the official terms did not grant automated collection.

## 4. Provider-published NAV contract

A future qualified NAV row must be the provider's NAV per fund certificate/unit in VND. The source
must document or response-bind:

- whether `navDate` is valuation, publication, or effective date;
- publication timestamp and timezone, if any;
- unit and currency, with no per-100 or per-lot ambiguity;
- whether the value is end-of-day NAV, not iNAV, exchange close, trade price, adjusted price, or
  a locally derived number;
- correction, cancellation, restatement, duplicate, and same-date conflict semantics; and
- the relationship between ETF market price, iNAV, and provider-published NAV.

The official HOSE document and manager pages show why these axes must stay separate: an ETF report
can publish NAV per fund certificate while the listed certificate also has an exchange price and
an intraday iNAV concept. None of those values may be substituted for another. Current Fmarket
mutual-fund NAV documentation cannot be inherited by an ETF without fresh proof.

## 5. Coverage contract and no-false-absence rules

The requested interval is inclusive `2018-01-01..2026-08-19`. A future result must retain separate:

```text
requested_start/end
provider_declared_served_start/end
provider_total/page/cursor/revision evidence
observed_start/end and distinct in-range count
provider cadence and confirmed non-publication calendar
```

`FULL` requires provider-served bounds covering the request, reconciled pages/totals/cursors,
response-backed product identity on every row, distinct ordered observations after explicit revision
handling, and provider status for every non-publication gap. `PARTIAL` requires provider-declared
narrower bounds plus exact page/total reconciliation; it must not be mislabeled as requested full
coverage. `UNKNOWN` is mandatory for any unreconciled bound, page, identity, cadence, or revision.

The following are distinct and cannot be collapsed:

- `UNVERIFIED_SELECTOR`: no official proof that `ETF` is accepted by the route;
- `UNSERVED`: the owner declares the route/catalogue does not serve ETFs;
- `CONFIRMED_EMPTY`: the exact ETF selector is accepted, the success envelope is valid, totals are
  reconciled, and the scoped result is genuinely zero; and
- `UNKNOWN`: a blank/HTML/WAF/error/timeout/missing-page response or unsupported scope.

These are design outcomes only; no new public enum or exception is added in this source-gap closure.
A blank Fmarket filter response, open-ended-only page, or missing route is never proof that no ETF
exists.

## 6. Exact bounded runtime design for a future qualified source

No runtime is implemented now. If a source later qualifies, the future scheduler uses one sequential
request-scoped ledger with these deterministic design ceilings:

| Reservation | Ceiling | Rule |
| --- | ---: | --- |
| Discovery pages | 2 | At most two provider pages; no unbounded broad search |
| Selected-product detail | 1 | One detail dispatch for the selected ID |
| NAV pages | 8 | At most eight provider pages/cursors; no date fan-out or source stitch |
| Logical targets | 11 | Two discovery + one detail + eight NAV page targets |
| Retries | 11 | At most one retry per logical target, same page/cursor only |
| Physical dispatches | 22 | Eleven initial reservations plus at most eleven retries |
| Decompressed bytes per response | 4,000,000 | Charge each streamed chunk atomically |
| Decompressed bytes per request | 16,000,000 | Global request ledger; no raw payload retention |

A reservation is atomic before dispatch. A capability skip creates no attempt and consumes no budget.
`reservation_budget_exhausted` is pre-dispatch, with no attempt row and no physical charge.
`stream_byte_cap_exhausted` is post-dispatch, retains the real sanitized attempt and physical charge,
and returns no partial history. A retry increments retry and physical counters but not logical page
count. No source failover, cross-source stitch, product fan-out, or M1-style helper is permitted.

Only HTTP 200 with a source-approved complete MIME can be data-success. Redirects are not followed.
204, 3xx, 4xx, 5xx, HTML/WAF, DNS/connection/TLS/timeout, wrong MIME, parse, identity, duplicate,
revision, body-limit, page mismatch, and budget outcomes remain distinct internal diagnostics.
Attempts expose only bounded source name, path-only route, target/page/retry ordinals, status,
complete normalized MIME, effective host/path, row count, provider total/bounds, and an outcome token.
Raw query URLs, request/response bodies, headers, cookies, credentials, provider prose, and exception
text never enter a public result or repository fixture.

The exact ceilings are design-only finite guards for a future RED matrix, not a claim that Fmarket
currently supports those pages, retries, MIME values, or byte sizes. A source cannot qualify merely by
fitting the scheduler; it must also prove the owner-approved runtime and legal axes.

## 7. Legal gate and reopen evidence

The official Fmarket terms are a hard blocker for automated reuse until written permission is obtained.
The nine axes are evaluated separately:

| Axis | Required evidence | Current status |
| --- | --- | --- |
| Owner identity | Fincorp/Fmarket owner and route confirmation | Partially identified |
| Automated access | Written permission for bounded software/API access | `LEGAL_GAP` |
| Caller-facing return | Permission to return ETF rows/NAV through vnfin | `LEGAL_GAP` |
| Storage/cache | Retention/cache window and deletion rules | `LEGAL_GAP` |
| Redistribution | OSS caller redistribution and documentation rights | `LEGAL_GAP` |
| Attribution | Required attribution/notice | `LEGAL_GAP` |
| Commercial use | Explicit commercial-use permission | `LEGAL_GAP` |
| Rate/retry | Quota, WAF, retry, and backoff policy | `RATE_POLICY_GAP` |
| Revision/correction | Restatement/cancellation and historical correction policy | `REVISION_GAP` |

The official contact paths are [`hello@fmarket.vn`](https://fmarket.vn/lien-he), `1900 571 299`, and
`028 3636 0755` during 08:30–17:00 Monday–Friday. A written request should name the ETF discovery
and NAV-history routes and ask specifically about automation, finite rate/retry limits, caller return,
storage/cache, attribution, commercial use, redistribution, and corrected historical observations.
No such request was sent in this task.

Reopen requires one same owner/route/basis to provide all of the following conjunctively:

1. written legal permission for all nine axes;
2. official selector/token and route/schema contract;
3. exact ETF code/product/name/manager/listing identity and row/detail/NAV binding;
4. provider-published VND-per-unit NAV semantics, date/timezone, publication, revision, and
   iNAV/market-price exclusion;
5. requested or declared partial coverage with reconciled pages/totals/cursors and cadence/non-
   publication semantics for `2018-01-01..2026-08-19`; and
6. source-approved bounded transport, retry, page, byte, and sanitized-diagnostic behavior.

Only after a fresh exact-SHA design PASS may a TDD task add RED fixtures and production changes. A
source-gap docs PASS authorizes only exact-range documentation publication, clean no-capability
resolution, close, and re-read; it does not authorize TDD or runtime capability.

## 8. Future RED/release matrix (not authorized now)

After a fresh design PASS only, synthetic fixtures must cover:

- exact ETF product/code/name/manager/listing identity positive;
- wrong, duplicate, renamed, delisted, share-class, missing, null, boolean, and cross-product IDs;
- exact `asset_type="ETF"` selector/translation positive, malformed/unsupported selector negatives,
  zero-network rejection, and compatibility with current legacy asset types;
- provider-published VND/unit NAV positive; iNAV, market price, adjusted price, wrong currency/unit,
  wrong product, malformed date/value, negative/non-finite/boolean values fail closed;
- inclusive bounds, provider totals/pages/cursors, first/last endpoints, cadence, duplicates,
  revisions/conflicts, confirmed non-publication, `FULL`/`PARTIAL`/`UNKNOWN`, and no false absence;
- atomic 11/22 logical/physical, one-retry, 4,000,000/16,000,000-byte, reservation versus stream
  exhaustion, sanitized diagnostics, and no partial accumulator after fatal exhaustion; and
- existing fund listing, NAV, holdings, allocation, warnings, DataFrame/API snapshots, import/version,
  all unrelated domains, offline suite, secret/blacklist/path/diff gates, and isolated package build.

No RED, code, model/accessor, source registration, production capability, discount calculation,
first difference, or VN30F logic is part of this source/design handoff.
