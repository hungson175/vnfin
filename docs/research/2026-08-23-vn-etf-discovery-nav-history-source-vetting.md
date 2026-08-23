# Vietnam ETF discovery and NAV-history source vetting

**Issue:** #218 — public ETF discovery and provider-published NAV history
**Research date:** 23 August 2026
**Disposition:** `SOURCE-GAP CLOSURE` for the requested Fmarket-backed `vnfin.funds` capability
**Requested inclusive span:** `2018-01-01..2026-08-19`
**Current published implementation boundary:** `8d1490fbda0aaaf217d9b98a51cd38c84dfaee16`
**Annotated `v0.2.0` boundary:** `2fe50df4f27064140ff9f7a680227a2b337ec74a`

This is a source and legal design artifact only. It does not add an ETF selector, product model,
parser, source registration, runtime call, RED test, coverage claim, or NAV-discount capability.
Discount, first difference, replay, strategy, and VN30F comparison remain caller-side.

## 1. Executive decision

No single Fmarket-owned source unit currently proves all of the following at once:

1. an ETF product-type response, distinct from Fmarket's open-ended mutual-fund asset classes;
2. a stable response-backed public code, legal fund name, manager, provider `product_id`, and
   exchange/listing identity;
3. a row/detail/NAV binding for that same product;
4. provider-published NAV per fund certificate, in VND, with date, publication, revision, and
   corrected/cancelled-observation semantics;
5. reconciled `2018-01-01..2026-08-19` history, cadence, bounds, pages, totals, and non-publication
   gaps; and
6. permission for bounded automated access, caller return, storage/cache, attribution,
   commercial use, and redistribution.

The official Fmarket catalogue describes open-ended fund products and its terms prohibit software-
based collection, copying, monitoring, aggregation, reproduction, and broad distribution without
permission. The existing repository route assumptions are not an official API contract and were not
live-probed for this task. Therefore an empty `asset_type="ETF"` result, an unserved route, or a
missing page cannot be promoted to confirmed ETF absence.

The conservative result is `SOURCE-GAP CLOSURE`: keep the current mutual-fund surface unchanged,
keep the future ETF capability unserved, and reopen only after Fincorp or another single qualified
owner grants and documents the missing source, identity, coverage, runtime, and legal axes.

## 2. Clean-room protocol and evidence boundary

Before this task, `docs/vnstock-blacklist.md` was read. The mandatory prohibited-source exclusion
was applied to every search. No prohibited library, derivative repository, endpoint map, schema,
code, test, example, or behavior was opened, cited, compared, or reused. Evidence here is limited
to official Fmarket/Fincorp pages and terms, official fund-manager pages, HOSE/VSDC documents, and
this repository's already-published Fmarket adapter contract.

The research used official web pages and documents only. No direct request was made to
`api.fmarket.vn` during this task: Fmarket's terms expressly restrict programs, algorithms, and
software used to collect, copy, or monitor the site, and no public API automation grant was found.
Search/open retrieval of public pages is research evidence, not a permission to automate the API.
No raw response, cookie, token, query-bearing URL, response digest, provider exception text, or live
ETF NAV value/date is retained here.

`NOT_PROBED_BY_DESIGN` means that a direct provider/API dispatch was intentionally not made because
permission to automate was not established. It is not a successful response, a timeout, a 404, or
proof of absence. `UNKNOWN` means the official evidence reviewed does not prove the field.

## 3. Current repository comparison

The exact `v0.2.0` tree and current published tree were compared. The current funds runtime remains
the Fmarket open-ended mutual-fund adapter; the #217 publication changed only research/design/
backlog documentation, not the funds runtime.

| Existing public seam | Current contract | ETF implication | Decision in this task |
| --- | --- | --- | --- |
| `vnfin.funds.source()` | Returns `FmarketFundSource` | No separate ETF provider or failover chain exists | Preserve |
| `list_funds(asset_type=None, search="", page_size=100, include_metadata=True)` | Sends the caller asset string to the existing Fmarket filter body; existing docs describe mutual-fund classes | `"ETF"` is not proven to be a provider asset-class token; an empty result is not ETF absence | Do not map, broaden, or fuzzy-match |
| `nav_history(product_id, from_date=None, to_date=None)` | Uses an existing provider product ID and a broad history request, then filters dates | Existing open-ended NAV semantics cannot be transferred to an ETF without product-type and field proof | Preserve; no ETF call |
| `Fund` / `FundList` | Carries code, name, provider ID, manager, provider asset type, NAV, and metadata | `asset_type` is not a proven ETF product-type field; listing identity is not represented | No model change |
| `NavPoint` / `NavHistory` | Carries date, NAV, VND/unit, product ID, provenance, retrieval time, warnings | Does not prove ETF NAV versus iNAV, market close, adjusted price, or exchange quote | No model change |
| Existing Fmarket paths | `/res/products/filter`, `/res/product/get-nav-history`, `/res/products/{id}` | These are repository baseline assumptions, not a fresh official API contract | No new route or request mapping |

The existing fund-code helper accepts the repository's canonical security/fund identifier grammar,
which is sufficient for future synthetic tests but is not evidence that Fmarket publishes ETF codes
through the current mutual-fund route. A future ETF design must document a bounded public code grammar
before RED; it must not silently widen the current filter or accept arbitrary name-only matches.

## 4. Official source matrix

The rows below keep discovery and NAV history as separate conjunctive units. A source can prove an
ETF exists without proving that Fmarket serves it, and a NAV document can prove a NAV field without
proving a reusable historical API.

| Candidate / owner | Canonical route or document | What the official evidence proves | What it does not prove | Disposition |
| --- | --- | --- | --- | --- |
| Fincorp / Fmarket catalogue | [`fmarket.vn/funds`](https://fmarket.vn/funds) | Fmarket presents itself as a distributor of open-ended fund certificates and identifies Fincorp and its distribution licence | No response-backed ETF product row, ETF product-type field, provider ID, exchange identity, or ETF history route | `PRODUCT_TYPE_GAP` + `COVERAGE_GAP` |
| Fincorp / Fmarket ETF explainer | [`fmarket.vn/quy-etf-la-gi/`](https://fmarket.vn/quy-etf-la-gi/) | Fmarket distinguishes exchange-traded funds from ordinary open-ended funds as a financial concept | An educational article is not a current product catalogue, API contract, identity row, NAV feed, or reuse grant; it is an older conceptual page and may be stale | `CONCEPT_ONLY` |
| Fincorp / Fmarket product detail family | [`fmarket.vn/quy/DCIP`](https://fmarket.vn/quy/DCIP) as an official open-ended example | Fmarket product pages expose open-ended fund presentation and NAV-oriented product information | The page is not an ETF identity, not proof that every code is served, and not a historical machine-readable NAV contract | `NOT_ETF_PROOF` |
| Fincorp / repository route baseline | `https://api.fmarket.vn/res/products/filter` (`POST`) | The current adapter names a filter route and a non-secret request shape for existing mutual-fund compatibility | No official ETF token, exact request/response schema, current MIME, redirect behavior, totals/page contract, or permission to automate | `ASSET_TOKEN_UNKNOWN` + `LEGAL_GAP` |
| Fincorp / repository route baseline | `https://api.fmarket.vn/res/product/get-nav-history` (`POST`) | The current adapter names a product-ID NAV-history route for existing mutual funds | No current ETF response, provider-published ETF NAV semantics, date/revision contract, pagination, bounds, or legal grant | `IDENTITY_GAP` + `NAV_SEMANTICS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` |
| Fincorp / repository route baseline | `https://api.fmarket.vn/res/products/{id}` (`GET`) | The current adapter uses a product-detail path for existing fund metadata | No ETF detail identity, listing binding, stable ID contract, or permission to retrieve it programmatically | `IDENTITY_GAP` + `LEGAL_GAP` |
| VinaCapital / fund manager | [`VinaCapital VN100 ETF`](https://wm.vinacapital.com/investment-solutions/onshore-funds/vinacapital-vn100-etf/) | An official manager page identifies an ETF, its ticker, HOSE listing, inception, fund structure, dealing cadence, and a series of official factsheet/NAV-document links | It is not Fmarket, does not prove a Fmarket product ID, does not by itself prove complete 2018 coverage, and does not grant vnfin automated retrieval or redistribution rights | `QUALIFIED_PARTIAL` corroboration only |
| Dragon Capital / fund manager | [`DCVFMVN30 ETF`](https://dautu.dragoncapital.com.vn/kien-thuc/danh-sach-quy-etf-tai-viet-nam) | An official manager page identifies an ETF and ticker and distinguishes NAV/unit from market trading context | No Fmarket route, no complete machine-readable history contract, no redistribution/runtime grant | `QUALIFIED_PARTIAL` corroboration only |
| HOSE | [Official ETF NAV disclosure document](https://staticfile.hsx.vn/Uploads/UploadDocuments/2453325/20260415%20-%20E1VFVN30%20-%20NAV%20April%2013%2C%202026.pdf) | An exchange-hosted official disclosure binds an ETF name/code, manager, reporting document, NAV per fund certificate, and VND unit context | A single disclosure is not an Fmarket route, complete requested history, page API, or reuse licence for a library | `QUALIFIED_PARTIAL` corroboration only |
| VSDC | [`VSDC home and fund-services description`](https://www.vsd.vn/vi/) | VSDC identifies fund services covering open-ended funds and ETFs and the official securities-code role | No public ETF NAV-history API, Fmarket binding, coverage ledger, or redistribution grant | `IDENTITY_SUPPORT_ONLY` |

The external ETF rows are deliberately not stitched into Fmarket. Ticker matching, a market quote,
or a manager document cannot repair a missing Fmarket product ID, route, response identity, coverage,
or legal axis.

## 5. Route, transport, and legal ledger

### 5.1 Discovery route

| Axis | Recorded value |
| --- | --- |
| Owner | Fincorp/Fmarket is the site owner identified by official Fmarket pages; ownership of the API host as an automation service is not separately documented |
| Canonical route | `https://api.fmarket.vn/res/products/filter` from the current repository baseline; no new route claim |
| Method / non-secret body | Existing adapter uses `POST` with `types`, sort fields, page, page size, IPO flag, `fundAssetTypes`, and `searchField`; the ETF meaning of `fundAssetTypes` is unproven |
| Redirect/effective host | `NOT_PROBED_BY_DESIGN`; no effective API route is retained |
| Full/normalized MIME | `NOT_PROBED_BY_DESIGN`; no API response was retained |
| HTTP/application envelope | `NOT_PROBED_BY_DESIGN`; no status, code, total, rows, or application shape is asserted as current ETF evidence |
| Auth/cookie/session/browser/WAF | Existing mutual-fund documentation is not an ETF automation grant; current ETF requirements are `UNKNOWN` |
| Direct dispatch ledger | logical `0`, physical `0`, page `0`, retry `0`; no retry policy inferred |
| Identity result | No response-backed ETF code, legal name, manager, provider ID, or listing identity |
| Disposition | `SOURCE-GAP`; never turn an empty/unserved filter into confirmed ETF absence |

### 5.2 NAV-history route

| Axis | Recorded value |
| --- | --- |
| Owner | Fincorp/Fmarket ownership is evidenced for the website; route-level owner/permission is not separately published |
| Canonical route | `https://api.fmarket.vn/res/product/get-nav-history` from the current repository baseline; no new route claim |
| Method / non-secret body | Existing adapter uses `POST` with product ID, broad date bounds, and an all-data flag; exact ETF request semantics are not official evidence |
| Redirect/effective host | `NOT_PROBED_BY_DESIGN` |
| Full/normalized MIME | `NOT_PROBED_BY_DESIGN` |
| HTTP/application envelope | `NOT_PROBED_BY_DESIGN`; no ETF row, total, cursor, page, revision, or publication timestamp is asserted |
| Auth/cookie/session/browser/WAF | `UNKNOWN`; no permission to automate was found and no login/session bypass is allowed |
| Direct dispatch ledger | logical `0`, physical `0`, page `0`, retry `0`; no retry policy inferred |
| Product binding | No Fmarket ETF `product_id` exists in retained evidence; no row-to-detail-to-NAV binding can be tested |
| NAV identity | No Fmarket ETF proof of provider-published NAV per unit, VND currency, date meaning, revision, or correction semantics |
| Disposition | `SOURCE-GAP`; no market close, iNAV, adjusted price, or locally derived value may substitute |

### 5.3 Detail route

`GET https://api.fmarket.vn/res/products/{id}` is retained only as an existing repository baseline
for mutual-fund detail and holdings. It has no fresh ETF identity evidence, so its direct ledger is
also logical `0`, physical `0`, page `0`, retry `0`. A future qualified unit may use it only if the
same response proves the product ID, code, legal name, manager, ETF product type, listing identity,
and the selected NAV route's product binding. A detail page that omits any of those fields is an
identity gap, not a reason to fuzzy-match by name.

## 6. Coverage and no-false-absence contract

The requested window is inclusive: `2018-01-01` through `2026-08-19`. For every candidate, retain
these distinct fields:

```text
requested_start/end
provider_declared_served_start/end and total/page/cursor evidence
observed_start/end and distinct in-range row count
provider publication calendar / confirmed non-publication evidence
```

Current Fmarket ETF values for all four groups are `UNKNOWN` or `NOT_PROBED_BY_DESIGN`; there is no
first/last served date, total, distinct count, page cap, retry count, cadence, duplicate/revision
ledger, or provider-declared holiday/non-publication calendar. The official VinaCapital page shows a
manager-published ETF with official NAV-document links, and the official HOSE document shows that an
ETF NAV disclosure can carry code, manager, report identity, and VND-per-unit context. Neither is a
complete Fmarket history or an authorization to retrieve it.

A future source can report:

- `FULL` only when provider bounds cover the full request, every page/total/cursor reconciles, every
  returned row binds to the selected product, dates are ordered and distinct after explicit
  revision handling, and provider calendar/non-publication semantics explain any missing dates;
- `PARTIAL` only when the provider declares narrower served bounds and those bounds plus all pages,
  totals, and observed endpoints reconcile; it must not be described as full requested coverage; or
- `UNKNOWN` when any bound, page, identity, publication, or revision axis is not proven.

An empty filter response is not `CONFIRMED_EMPTY` unless the provider response proves that the exact
ETF selector was accepted, the response is a valid success envelope, the total is reconciled, and the
scope is the ETF universe rather than only open-ended funds. A missing ETF route or a mutual-fund-only
page is not proof that no ETF exists. `UNSERVED`, `UNVERIFIED_SELECTOR`, and `CONFIRMED_EMPTY` must
remain distinguishable in any future typed outcome; no such new public outcome is added here.

## 7. Legal and runtime posture

Fmarket's official terms provide a decisive conservative boundary:

- access is described as limited and non-exclusive for personal use/access to financial products;
- copying or reproducing site information, retaining copyrighted copies, and distributing site
  content are restricted without permission;
- using programs, algorithms, or software to collect, copy, or monitor the site is prohibited; and
- commercial use requires Fincorp permission.

The official terms are at [`fmarket.vn/legal`](https://fmarket.vn/legal). Fmarket's contact page
lists `hello@fmarket.vn`, `1900 571 299`, and `028 3636 0755`, with stated support hours of 08:30–17:00
Monday–Friday, at [`fmarket.vn/lien-he`](https://fmarket.vn/lien-he). No permission request was sent
as part of this docs-only task.

| Legal/runtime axis | Evidence | Status |
| --- | --- | --- |
| Owner identity | Fincorp/Fmarket legal and contact pages | `PROVIDER_IDENTIFIED` |
| Automated access | Terms restrict software collection/copying/monitoring; no API grant found | `LEGAL_GAP` |
| Caller-facing return | No permission to return Fmarket ETF rows through an OSS library | `LEGAL_GAP` |
| Storage/cache | Retained copies are restricted without owner permission | `LEGAL_GAP` |
| Redistribution | Broad distribution/reproduction is restricted without permission | `LEGAL_GAP` |
| Attribution | No ETF API attribution licence or required notice found | `LEGAL_GAP` |
| Commercial use | Terms require Fincorp permission for commercial use | `LEGAL_GAP` |
| Rate/retry | No source-approved automated quota or retry policy found | `RATE_POLICY_GAP` |
| Revision/correction | No ETF API revision/cancellation contract found | `REVISION_GAP` |

Public reachability, an official website, a distribution licence, or a browser-visible chart is not
an open-data or redistribution grant. The legal gaps alone prevent a qualified runtime source.

## 8. Future bounded design, not implementation authorization

If written permission and complete source evidence later arrive, the future implementation must use
one sequential request-scoped ledger. The following are design ceilings for deterministic RED and
review planning only; they are not current provider promises or public API changes:

| Reservation | Exact ceiling | Accounting |
| --- | ---: | --- |
| Discovery pages | 2 | One logical target per page; no broad fallback search |
| Selected-product detail | 1 | One logical target; must bind code, product ID, manager, product type, and listing identity |
| NAV history pages | 8 | One logical target per provider page/cursor; no date fan-out or source stitch |
| Total logical targets | 11 | `2 discovery + 1 detail + 8 NAV` |
| Retry | 1 per logical target, global maximum 11 | Retry reuses the same logical page/cursor and does not create a second logical target |
| Total physical dispatches | 22 | `11 initial + at most 11 retries`; reservation happens before dispatch |
| Maximum decompressed bytes per response | 4,000,000 | Charge each streamed chunk atomically; keep no raw payload |
| Maximum decompressed bytes per request | 16,000,000 | Global request ledger; failure returns no partial history |

A capability skip creates no dispatch and consumes no budget. A failed reservation is
`reservation_budget_exhausted`, pre-dispatch, with no attempt row or physical charge. A real
response that exceeds a per-response or global decompressed-byte cap is
`stream_byte_cap_exhausted`; it retains the real sanitized attempt and physical charge but returns
no history. An HTTP/application failure, unexpected status, redirect, HTML/WAF page, wrong exact
MIME, parse failure, unreconciled page, identity mismatch, or provider-total conflict is distinct
from confirmed non-publication and cannot become an empty/full result.

Only a future qualified source may freeze public diagnostic names. Internal attempts may contain only
bounded source name, path-only route, logical target type, page/cursor ordinal, retry ordinal, status,
complete normalized MIME, effective host/path, row count, provider total/bounds, and an outcome token.
Raw URL queries, bodies, headers, cookies, tokens, provider prose, and exception text stay private and
are never returned or committed.

## 9. Reopen gate and release boundary

Reopen requires one same-provider, same-route, same-basis source unit to provide all of these
conjunctively:

1. written Fincorp/provider permission covering automated access, rate/retry, caller return,
   storage/cache, attribution, commercial use, and redistribution;
2. an official route/schema contract or written owner confirmation for discovery and NAV history;
3. response-backed ETF product type, code, legal name, manager, provider ID, and listing identity;
4. exact row/detail/NAV product binding with duplicate, rename, share-class, delist, and mismatch
   fail-closed cases;
5. provider-published NAV per unit in VND, date/publication/timezone/revision semantics, and an
   explicit exclusion of iNAV, market price, adjusted price, and local derivation;
6. reconciled requested or provider-declared partial coverage, page/cursor/total bounds, cadence,
   missing-date and correction semantics for `2018-01-01..2026-08-19`; and
7. finite source-approved transport, page, retry, byte, and diagnostics behavior that fits the
   bounded ledger above.

Only after a fresh exact-SHA design PASS may a separate TDD task add RED fixtures, an ETF selector,
a product-type field, parser, source registration, or runtime capability. A docs-only source-gap PASS
publishes only the two design/source artifacts plus the backlog lifecycle record and permits a clean
no-capability resolution; it does not authorize implementation or a coverage claim.

## 10. Sources

All sources below were official/provider-owned or official exchange/regulator/manager sources and were
accessed or checked on 23 August 2026:

- [Fmarket terms](https://fmarket.vn/legal) — owner terms, copying/collection/commercial-use posture.
- [Fmarket fund catalogue](https://fmarket.vn/funds) — current open-ended product presentation and
  Fincorp distribution context.
- [Fmarket ETF explainer](https://fmarket.vn/quy-etf-la-gi/) — conceptual ETF/open-ended distinction,
  treated as non-current product evidence.
- [Fmarket contact](https://fmarket.vn/lien-he) — written-permission contact paths.
- [VinaCapital VN100 ETF](https://wm.vinacapital.com/investment-solutions/onshore-funds/vinacapital-vn100-etf/)
  — official manager identity, listing, cadence, and document links.
- [Dragon Capital DCVFMVN30 ETF](https://dautu.dragoncapital.com.vn/kien-thuc/danh-sach-quy-etf-tai-viet-nam)
  — official manager identity and NAV/unit terminology.
- [HOSE ETF NAV disclosure](https://staticfile.hsx.vn/Uploads/UploadDocuments/2453325/20260415%20-%20E1VFVN30%20-%20NAV%20April%2013%2C%202026.pdf)
  — official exchange-hosted ETF identity and NAV report shape.
- [VSDC](https://www.vsd.vn/vi/) — official ETF/fund-service and securities-code context.

No third-party aggregator, paid feed, login/session bypass, or prohibited derivative source was used.
