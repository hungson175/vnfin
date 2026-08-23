# Vietnam ETF discovery and NAV-history source vetting

**Issue:** #218 — public ETF discovery and provider-published NAV history
**Research date:** 23 August 2026
**Disposition:** `SOURCE-GAP CLOSURE`; no owner route set qualifies the requested capability
**Requested inclusive span:** `2018-01-01..2026-08-19`
**Current published implementation boundary:** `8d1490fbda0aaaf217d9b98a51cd38c84dfaee16`
**Annotated `v0.2.0` boundary:** `2fe50df4f27064140ff9f7a680227a2b337ec74a`
**Correction lifecycle:** prior B1-B6 BLOCK recorded first at `9c48084`; closure-review BLOCK recorded
first at `6f2cfbe`; this artifact is the one docs-only correction after the latter BLOCK

This is a source and legal design artifact only. It does not add an ETF selector, product model,
parser, source registration, runtime call, RED test, coverage claim, or NAV-discount capability.
Discount, first difference, replay, strategy, and VN30F comparison remain caller-side.

> **Post-#221 status:** the Fmarket mutual-fund runtime is now disabled pending permission. This
> #218 artifact predates that implementation and does not authorize an Fmarket call; the current
> mutual-fund compatibility surface fails closed before cache/network.

## 1. Executive decision

No single owner route set currently proves all of the following at once:

1. an ETF product-type response, distinct from an open-ended mutual-fund asset class;
2. a stable response-backed public code, legal fund name, manager, owner/product identity, and
   exchange/listing identity;
3. a discovery/detail/NAV binding for that same selected product;
4. provider-published NAV per fund certificate/unit, in VND, with date, publication, revision, and
   corrected/cancelled-observation semantics;
5. reconciled `2018-01-01..2026-08-19` history, cadence, bounds, pages, totals, and non-publication
   gaps; and
6. permission for bounded automated access, caller return, storage/cache, attribution, commercial use,
   and redistribution.

The Fmarket terms justify **no new Fmarket API or direct provider-data probe**. That decision is
not a dismissal of alternative owners. A separate bounded read-only review of official manager,
exchange, and service pages plus linked public documents is recorded in section 4.1. VinaCapital
provides the strongest alternative route-set candidate, but its owner page/document family still
does not prove the requested start, a complete historical index, correction semantics, bounded
machine retrieval, or reuse rights. HOSE and Dragon provide narrower identity/document evidence only.

The conservative result is `SOURCE-GAP CLOSURE`: keep the current mutual-fund surface unchanged,
keep the new ETF capability unserved, and reopen only after one owner and one coherent route set
document all missing identity, coverage, runtime, and legal axes. Do not stitch an Fmarket product
identity to a manager or exchange NAV document.

## 2. Clean-room protocol and evidence boundary

Before this task, `docs/vnstock-blacklist.md` was read. Every search used this exact mandatory
exclusion string:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited library, derivative repository, endpoint map, schema, code, test, example, or behavior
was opened, cited, compared, or reused. Evidence here is limited to official Fmarket/Fincorp terms,
official fund-manager pages and linked documents, HOSE/VSDC pages/documents, and this repository's
already-published Fmarket adapter contract. Uncertain licensing is recorded as a gap, never inferred
from public reachability.

The research used official web pages and public documents only. No request was made to
`api.fmarket.vn`, and no Fmarket endpoint or other provider API was directly probed. Reading an
official HTML page or linked PDF is research evidence, not permission to automate it. No raw response,
cookie, token, query-bearing URL, response digest, provider exception text, or live ETF NAV value is
retained here. Document identity/date labels are retained only where needed to establish the source
axis; no value series is bundled.

`NOT_PROBED_BY_DESIGN` means that a direct provider/API dispatch was intentionally not made because
permission to automate was not established. It is not a successful response, timeout, 404, or proof
of absence. `UNKNOWN` means the official evidence reviewed does not prove the field.

## 3. Current disabled boundary and pre-#221 compatibility evidence

The exact `v0.2.0` tree and pre-#221 published tree were compared. They are **not identical**:
the pre-#221 tree contains additive mutual-fund metadata changes, while #218 changes none of them.
After #221, the current funds runtime remains the named Fmarket compatibility adapter but is
disabled pending permission; the #218 publication changed only research/design/backlog
documentation and does not reopen that source.

| Public seam | `v0.2.0` boundary | Current published tree | #218 decision |
| --- | --- | --- | --- |
| `list_funds` | `list_funds(asset_type=None, search="", page_size=100)` | Preserved signature/model; current valid calls fail closed before transport | Preserve compatibility; no ETF mapping |
| `Fund` | code/name/id/nav/manager/asset_type/currency | Adds optional `nav_as_of`, `management_fee_pct`, `inception_date`, and `description` | No model change |
| `NavHistory` | Existing product-ID history, `value_unit="VND/unit"`, optional `code` | Same public shape with current diagnostics/window behavior | No ETF `code` provenance is inferred or changed |
| `vnfin.funds.source()` | Returns the Fmarket source | Still returns the lazy named source; valid calls disabled pending permission | Preserve |
| `list_funds.search` | Free-text search input | Still free text; it is not a code grammar or selector proof | Preserve; no local fuzzy matching |
| `list_funds.asset_type` | Provider asset-class filter string | Current valid calls fail before request-body construction; pre-#221 forwarding as `fundAssetTypes` is historical parser evidence only | Do not map, broaden, or call it an ETF selector |
| `nav_history(product_id, ...)` | Existing mutual-fund product-ID history | Pre-#221 historical behavior used a broad provider request plus client-side date filtering; current valid calls fail closed before it | Preserve schema/parser compatibility; no ETF call |
| `canonical_fund_code` | Existing helper was not an ETF contract | Current response-code helper uses the unbounded current `[A-Z][A-Z0-9]*` shape after normalization | Preserve response compatibility; no new ETF ceiling |
| Repository routes | Mutual-fund baseline only | `/res/products/filter`, `/res/products/{id}`, `/res/product/get-nav-history` | No new route or request mapping |

The current-vs-historical boundary is strict: current valid calls fail before request-body
construction, cache lookup, transport dispatch, response parsing, or public `EmptyData` production.
Any row or paragraph below that describes provider forwarding, response parsing, or historical
`EmptyData` behavior is pre-#221 compatibility evidence only; it is not a current runtime seam or
an availability claim.

The future compatibility sketch below is deliberately **not current capability**:

```python
src = vnfin.funds.source()
listing = src.list_funds(asset_type="ETF", search="E1VFVN30", include_metadata=True)
history = src.nav_history(product_id, from_date="2018-01-01", to_date="2026-08-19")
```

It does not authorize a new token, parameter, model, or call. There is no new ETF code grammar in
this source-gap closure. The historical compatibility seams are free-text `search`, the provider
asset-class `fundAssetTypes` translation, and response-side `canonical_fund_code`; none is reached
by a current valid call. Any normalized ETF selector, provider translation, or future
`NavHistory.code` provenance requires source proof and a fresh RED/API design. Legacy mutual-fund
asset strings and current response-code behavior remain compatibility-sensitive historical evidence.

## 4. Official source matrix

Each candidate below is evaluated as its own owner/route set. A source can prove an ETF exists
without proving a reusable historical route, and a NAV document can prove a NAV field without proving
a discovery API or reuse permission.

| Candidate / owner | Canonical route or document | What the official evidence proves | What it does not prove | Disposition |
| --- | --- | --- | --- | --- |
| Fincorp / Fmarket catalogue | [`fmarket.vn/funds`](https://fmarket.vn/funds) | Fmarket presents open-ended fund certificates and Fincorp distribution context | No response-backed ETF row, ETF product field, owner/product ID, exchange identity, or ETF history route | `PRODUCT_TYPE_GAP` + `COVERAGE_GAP` |
| Fincorp / Fmarket ETF explainer | [`fmarket.vn/quy-etf-la-gi/`](https://fmarket.vn/quy-etf-la-gi/) | Conceptual distinction between exchange-traded and open-ended funds | Not a current catalogue, response identity, NAV feed, API contract, or reuse grant | `CONCEPT_ONLY` |
| Fincorp / repository route baseline | `https://api.fmarket.vn/res/products/filter` (POST) | Existing adapter names a mutual-fund filter route/body | No ETF token, current schema/MIME/redirect contract, totals/pages, or permission to automate | `ASSET_TOKEN_UNKNOWN` + `LEGAL_GAP` |
| Fincorp / repository route baseline | `https://api.fmarket.vn/res/product/get-nav-history` (POST) | Existing adapter names a mutual-fund product-ID history route | No ETF NAV semantics, date/revision contract, bounds, pagination, or legal grant | `IDENTITY_GAP` + `NAV_SEMANTICS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` |
| VinaCapital / fund manager | [VN100 ETF owner page](https://wm.vinacapital.com/investment-solutions/onshore-funds/vinacapital-vn100-etf/) plus the linked NAV-document family | Official manager identity for FUEVN100, ETF type, HOSE, inception, dealing cadence, and named daily/weekly NAV reports | No complete requested-span history, provider-declared report bounds/totals, revision contract, bounded machine route, or OSS reuse grant | `IDENTITY_PASS` + `NAV_ROUTE_CANDIDATE`; aggregate `SOURCE-GAP` |
| Dragon Capital / fund manager | [Official ETF list article](https://dautu.dragoncapital.com.vn/kien-thuc/danh-sach-quy-etf-tai-viet-nam) | Official article lists ETF codes/indexes and discusses market price/iNAV distinction | No provider-published NAV-per-unit route, complete history, or automation/redistribution grant | `IDENTITY_SUPPORT_ONLY` |
| HOSE | [Official E1VFVN30 NAV disclosure](https://staticfile.hsx.vn/Uploads/UploadDocuments/2453325/20260415%20-%20E1VFVN30%20-%20NAV%20April%2013%2C%202026.pdf) | Official PDF identifies ETF/code/manager/report and NAV per fund certificate in VND context | One document is not a discovery/history index, complete requested span, bounded API, or reuse licence | `DOCUMENT_SUPPORT_ONLY` |
| VSDC | [VSDC home/services](https://www.vsd.vn/vi/) | Official fund-service context for open-ended funds/ETFs and securities-code role | No candidate owner NAV-history route, coverage ledger, or redistribution grant | `SERVICE_CONTEXT_ONLY` |

The alternative rows are not required to bind to Fmarket. They fail because their own route sets
lack one or more required axes, not because they lack a Fmarket `product_id`. No ticker match,
market quote, iNAV, manager document, or VSDC service context may repair an incomplete owner route
set.

### 4.1 Independent official owner-route research (read-only)

This subsection is the required separate alternative-source review. It used only public official HTML
pages and linked public documents on 23 August 2026. It made no Fmarket API call and no direct
provider-data/API probe. For each owner, transport/document identity, requested-span coverage,
revision semantics, and legal/runtime axes are recorded independently.

| Owner route set | Owner/path and document identity | Transport/auth/redirect posture | Requested span, cadence, revision | Rights and disposition |
| --- | --- | --- | --- | --- |
| VinaCapital VN100 ETF | `https://wm.vinacapital.com/investment-solutions/onshore-funds/vinacapital-vn100-etf/` is the manager HTML identity/discovery page. Its primary-trading section names FUEVN100 daily/weekly NAV reports and links fund documents. `https://wm.vinacapital.com/information-disclosure/` is the manager disclosure index. A sampled linked factsheet is the owner PDF `https://wm.vinacapital.com/wp-content/uploads/2026/02/20260212-VINACAPITAL-VN100-ETF_Monthly-Factsheet_Jan-2026-EN.pdf`, identified as `application/pdf` and naming FUEVN100, HOSE, inception 16 June 2020, and NAV-per-share context. | Public HTML/PDF pages were readable without a login. The sampled document is a PDF. Individual daily NAV link status, effective redirect, and MIME were not separately dispatched; no API/schema or pagination contract was retained. `NOT_PROBED_BY_DESIGN` for those transport fields. | The manager page declares product inception `2020-06-16`, so the requested `2018-01-01` start is outside this product's declared life. The page displays recent daily/weekly report labels, including the requested end-date neighborhood, but no earliest report bound, total, cursor/page reconciliation, or non-publication calendar. Aggregate status is `UNKNOWN`, not `FULL` or `PARTIAL`. No correction, cancellation, restatement, or same-date conflict rule was found. | Manager ownership and public identity are positive. No written permission for automated retrieval, caller return, storage/cache, attribution, commercial use, or redistribution was found in the reviewed page/document posture; `LEGAL_GAP` and `RUNTIME_GAP`. This is the strongest alternative candidate but remains `SOURCE-GAP`. |
| HOSE disclosure document set | `https://staticfile.hsx.vn/Uploads/UploadDocuments/2453325/20260415%20-%20E1VFVN30%20-%20NAV%20April%2013%2C%202026.pdf` is an official exchange-hosted PDF disclosure for E1VFVN30. The document identity includes reporting/current-versus-prior disclosure columns and NAV per fund certificate/per lot in VND context. | Public PDF document; no login was required for read-only retrieval. Direct status/redirect policy and a discovery-directory/pagination contract were not separately dispatched. | One sampled disclosure proves only a point/document shape; it gives no requested-span bounds, total, history index, cadence calendar, or correction/version rule. Status `UNKNOWN`; `DOCUMENT_SUPPORT_ONLY`. | Exchange publication is not an OSS/API/reuse grant. No caller-return, storage, redistribution, rate, or revision permission was found; `LEGAL_GAP`. No Dragon/Vina data is stitched into this route set. |
| Dragon Capital manager article | `https://dautu.dragoncapital.com.vn/kien-thuc/danh-sach-quy-etf-tai-viet-nam` is an official HTML educational/list page. It lists ETF ticker/index pairs and discusses the distinction between market price and iNAV. | Public HTML page; it is not a NAV-document/API route. No response schema, pagination, redirect, or automation policy is published in the reviewed page. | No provider-published NAV-per-unit history, served bounds, cadence, revision, or non-publication contract is exposed. Status `UNKNOWN`; `IDENTITY_SUPPORT_ONLY`. The article must not be described as proving a NAV/unit contract. | No automation, caller-return, storage, redistribution, or commercial-use grant found; `LEGAL_GAP`. It cannot complete the HOSE or Vina route sets. |
| VSDC service context | `https://www.vsd.vn/vi/` identifies VSDC's fund services and securities-code role, not a selected ETF data route. | Public HTML service page; no ETF NAV-history endpoint or document family was identified. | No product-specific requested-span, cadence, revision, or page evidence. `SERVICE_CONTEXT_ONLY`. | Regulatory/infrastructure context is not a data reuse grant and is not a candidate owner route set. |

**Alternative-route conclusion:** VinaCapital's manager page plus its linked NAV-document family is
a real, independent route-set candidate and is retained for future owner contact/research. Its
identity evidence does not establish complete `2018-01-01..2026-08-19` history or lawful bounded
automation. HOSE is a document-support route, and Dragon/VSDC are support/context only. No single
owner route set qualifies, so the new chain remains empty.

#### 4.1.1 Retained dispatch ledger: runtime versus evidence reading

The ledger below is for a future provider/data-route runtime, not for the read-only evidence review.
No owner API or direct data route was dispatched, so every runtime ledger is exactly zero. The public
HTML/PDF reads are named separately and do not invent HTTP status, redirect, or unretained MIME data.

| Owner | Runtime logical | Runtime physical | Runtime page | Runtime retry | Read-only evidence distinction |
| --- | ---: | ---: | ---: | ---: | --- |
| VinaCapital | `0` | `0` | `0` | `0` | Three public evidence documents read: manager page, disclosure index, and one linked factsheet PDF; not a runtime attempt; unprobed route fields remain `NOT_PROBED_BY_DESIGN` |
| HOSE | `0` | `0` | `0` | `0` | One official disclosure PDF read; not a history/API dispatch; status/redirect/page fields remain `NOT_PROBED_BY_DESIGN` |
| Dragon Capital | `0` | `0` | `0` | `0` | One official HTML article read; not a NAV/data-route dispatch; status/redirect/schema fields remain `NOT_PROBED_BY_DESIGN` |
| VSDC | `0` | `0` | `0` | `0` | One official HTML service page read; not a product/data-route dispatch; status/redirect/schema fields remain `NOT_PROBED_BY_DESIGN` |

#### 4.1.2 Complete alternative-owner legal/runtime axes

Every alternative owner is evaluated on the same nine axes. A public page or document supplies no
permission by itself, so unsupported rights are explicit gaps rather than omitted cells.

| Axis | VinaCapital | HOSE | Dragon Capital | VSDC |
| --- | --- | --- | --- | --- |
| Owner identity | `PROVIDER_IDENTIFIED` | `PROVIDER_IDENTIFIED` | `PROVIDER_IDENTIFIED` | `UNKNOWN` (service context, not a selected data owner) |
| Automated access | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` |
| Caller-facing return | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` |
| Storage/cache | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` |
| Redistribution | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` |
| Attribution | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` |
| Commercial use | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` |
| Rate/retry | `RATE_POLICY_GAP` | `RATE_POLICY_GAP` | `RATE_POLICY_GAP` | `RATE_POLICY_GAP` |
| Revision/correction | `REVISION_GAP` | `REVISION_GAP` | `REVISION_GAP` | `REVISION_GAP` |

## 5. Existing Fmarket route ledger (zero dispatch)

The following are repository baselines for existing mutual-fund compatibility, not fresh ETF evidence.

### 5.1 Discovery route

| Axis | Recorded value |
| --- | --- |
| Owner | Fincorp/Fmarket website owner; route-level API permission is not separately documented |
| Canonical route | `https://api.fmarket.vn/res/products/filter` from the current repository baseline |
| Method/body | Existing adapter uses POST with types, sort fields, page, page size, IPO flag, `fundAssetTypes`, and `searchField`; ETF meaning is unproven |
| Redirect/effective host | `NOT_PROBED_BY_DESIGN` |
| Full/normalized MIME | `NOT_PROBED_BY_DESIGN` |
| HTTP/application envelope | `NOT_PROBED_BY_DESIGN`; no ETF status/code/total/rows asserted |
| Auth/cookie/session/browser/WAF | `UNKNOWN` for ETF; no login/session bypass |
| Direct dispatch ledger | logical `0`, physical `0`, page `0`, retry `0` |
| Identity/disposition | No response-backed ETF identity; `SOURCE-GAP` |

### 5.2 NAV-history and detail routes

| Route | Baseline | ETF evidence/disposition |
| --- | --- | --- |
| `https://api.fmarket.vn/res/product/get-nav-history` (POST) | Existing product ID, broad dates, all-data flag | No ETF product ID, NAV/unit/date/revision/page proof; ledger zero; `SOURCE-GAP` |
| `https://api.fmarket.vn/res/products/{id}` (GET) | Existing mutual-fund detail/holdings baseline | No ETF identity/listing/binding proof; ledger zero; `SOURCE-GAP` |

No current baseline response can establish ETF product type, code/name/manager/listing identity,
row/detail/NAV binding, or a provider-published ETF NAV contract. A detail page that omits any
identity axis is a gap, not a reason to fuzzy-match by name.

## 6. Coverage and no-false-absence contract

For every independently evaluated candidate, retain these distinct fields:

```text
requested_start/end
provider_declared_product_or_served_start/end
provider_total/page/cursor/revision evidence
observed_start/end and distinct in-range row count
provider cadence and confirmed non-publication evidence
```

A future source can report:

- `FULL` only when provider bounds cover the full request, every page/total/cursor reconciles, every
  returned row binds to the selected product, dates are ordered and distinct after explicit revision
  handling, and provider calendar/non-publication semantics explain missing dates;
- `PARTIAL` only when the provider declares narrower served bounds and those bounds plus all pages,
  totals, and observed endpoints reconcile; it must never be described as full requested coverage; and
- `UNKNOWN` when any bound, page, identity, publication, or revision axis is not proven.

An empty filter response is not `CONFIRMED_EMPTY` unless the exact ETF selector is accepted, the
success envelope is valid, totals are reconciled, and the scope is the ETF universe. A missing route,
mutual-fund-only page, blank/HTML/WAF/error response, or unindexed document is not proof that no ETF
exists. `UNSERVED`, `UNVERIFIED_SELECTOR`, `CONFIRMED_EMPTY`, and `UNKNOWN` remain distinct
future outcomes; no new public enum is added here. For each of these four outcomes, the future public
carrier—typed empty result versus typed error, exact error type, and exact public message—is
explicitly deferred until one source qualifies and a fresh qualified-source API design PASS occurs
before RED. Pre-#221 parser EmptyData behavior remains private historical evidence only; no current
valid call reaches that parser or produces `EmptyData`, and this closure invents no enum, exception,
or result carrier.

## 7. Legal posture and the separate existing-runtime risk

Fmarket's official terms provide a provider-wide conservative boundary:

- access is described as limited and non-exclusive for personal use/access to financial products;
- copying/reproducing, retaining copyrighted copies, and distributing site content are restricted
  without permission;
- programs, algorithms, or software used to collect, copy, or monitor the site are prohibited; and
- commercial use requires Fincorp permission.

The official terms are at [`fmarket.vn/legal`](https://fmarket.vn/legal). The contact page lists
[`hello@fmarket.vn`](https://fmarket.vn/lien-he), `1900 571 299`, and `028 3636 0755`, with
stated support hours of 08:30–17:00 Monday–Friday. No permission request was sent.

These terms are not described as ETF-specific. The pre-#221 mutual-fund adapter automated the same
provider host/route family, so its historical posture must not be silently cleared or ignored; the
current runtime is disabled before that host/route family is reached:

| Durable disposition | Scope | Meaning and next action |
| --- | --- | --- |
| `MUTUAL_RUNTIME_LEGAL_RISK` | Existing published mutual-fund adapter and its runtime caller-return/storage posture | Unresolved provider-wide terms risk; the existing engineering contract remains unchanged in #218, but runtime-fetch-only is not owner permission. Hand back to maintainer/legal triage; do not reinterpret this #218 docs pass as approval or revocation. |
| `ETF_SOURCE_LEGAL_GAP` | New ETF discovery/NAV capability | No written automation, caller-return, storage/cache, attribution, commercial-use, rate/retry, or redistribution permission; no source registration/model/runtime work. |

| Legal/runtime axis | Fmarket status |
| --- | --- |
| Owner identity | `PROVIDER_IDENTIFIED` |
| Automated access | `LEGAL_GAP` |
| Caller-facing return | `LEGAL_GAP` |
| Storage/cache | `LEGAL_GAP` |
| Redistribution | `LEGAL_GAP` |
| Attribution | `LEGAL_GAP` |
| Commercial use | `LEGAL_GAP` |
| Rate/retry | `RATE_POLICY_GAP` |
| Revision/correction | `REVISION_GAP` |

Public reachability, an official website, a distribution licence, a browser-visible chart, or a
manager/exchange disclosure is not an open-data or redistribution grant.

## 8. Future bounded design: invariants now, numbers deferred

No numeric page, retry, physical-dispatch, response-byte, or request-byte ceiling is source-approved
in this source-gap closure. Exact values are `DEFERRED_UNTIL_QUALIFIED_OWNER_ROUTE`; the old
planning numbers are intentionally not a provider promise, public contract, or future RED assertion.

If one owner later qualifies, the route set may contain separate discovery, selected-detail, and NAV
paths, but it must be one owner, one approved bounded route set, and one selected-product/NAV identity
basis. No cross-owner stitch, failover oracle, broad source fan-out, or product-name join is allowed.

Only these structural invariants are frozen for future design:

- one sequential request-scoped ledger with atomic reservation before each dispatch;
- a capability skip creates no attempt and consumes no budget;
- retry, if owner-approved, reuses the same logical target and is charged in the same global ledger;
- streaming/decompression bytes are charged atomically, with bounded sanitized attempts only;
- reservation exhaustion is pre-dispatch; stream-byte exhaustion retains the real attempt and physical
  charge; and
- any fatal exhaustion, status/MIME/parse/page/identity/revision/total conflict returns **no partial
  discovery, detail, or NAV accumulator**.

Only a future qualified source may freeze public diagnostic names, exact finite values, complete MIME
rules, or route-specific status/redirect behavior. Raw queries, bodies, headers, cookies, credentials,
provider prose, and exception text never enter a public result or repository fixture.

## 9. Conjunctive reopen and exact release lifecycle

Reopen requires one owner and one approved bounded route set to provide all of these conjunctively:

1. written permission for automated access, rate/retry, caller return, storage/cache, attribution,
   commercial use, and redistribution;
2. official discovery/detail/NAV route or document contract, including transport, MIME, redirects,
   auth/WAF, and effective-path behavior;
3. response/document-backed ETF product type, code, legal name, manager, owner/product identity, and
   listing identity;
4. exact selected-product/detail/NAV binding, with duplicate, rename, share-class, delist, and
   mismatch failure cases;
5. provider-published NAV per unit in VND, date/publication/timezone, unit, revision/correction, and
   explicit exclusion of iNAV, market price, adjusted price, and local derivation;
6. requested or provider-declared partial coverage with reconciled bounds/pages/totals/cursors,
   cadence, non-publication, and revision semantics for `2018-01-01..2026-08-19`; and
7. owner-approved finite scheduler/byte/diagnostic values and no-partial behavior.

A future docs-only PASS must use published base `8d1490fbda0aaaf217d9b98a51cd38c84dfaee16`, name
the exact range `8d1490f..<approved-anchor>`, and list exactly these three paths:

- `docs/research/2026-08-23-vn-etf-discovery-nav-history-source-vetting.md`
- `tasks/218-design-note.md`
- `tasks/active-backlog.md`

The release sequence is: rerun merged gates; push only the approved anchor; verify remote exact HEAD,
base ancestry, and the three paths; post a clean no-capability `SOURCE-GAP` resolution; close and
re-read #218; only then activate #221. Keep #219 queued until #221's exact source/design handoff
and verified close, then activate #219; keep #220 behind #219. No implementation, RED, model/accessor,
source registration, or runtime capability is authorized by this docs pass.

If a later fresh design PASS authorizes implementation, the separate release matrix must explicitly
cover the packet's fund API, source, diagnostics, tutorial/agent-facing AI docs, maintainer skill,
`CHANGELOG.md`, and release notes, in addition to tests/build/blacklist/secret/diff gates.

## 10. Sources

All sources below were official/provider-owned or official exchange/regulator/manager sources and were
accessed or checked on 23 August 2026:

- [Fmarket terms](https://fmarket.vn/legal) — owner terms and copying/collection/commercial-use posture.
- [Fmarket fund catalogue](https://fmarket.vn/funds) — open-ended product/distribution context.
- [Fmarket ETF explainer](https://fmarket.vn/quy-etf-la-gi/) — conceptual distinction only.
- [Fmarket contact](https://fmarket.vn/lien-he) — written-permission contact paths.
- [VinaCapital VN100 ETF](https://wm.vinacapital.com/investment-solutions/onshore-funds/vinacapital-vn100-etf/) — manager identity and linked NAV reports.
- [VinaCapital information disclosure](https://wm.vinacapital.com/information-disclosure/) — owner disclosure index.
- [VinaCapital VN100 ETF factsheet](https://wm.vinacapital.com/wp-content/uploads/2026/02/20260212-VINACAPITAL-VN100-ETF_Monthly-Factsheet_Jan-2026-EN.pdf) — official PDF identity/field context; no live value series retained.
- [Dragon Capital ETF list](https://dautu.dragoncapital.com.vn/kien-thuc/danh-sach-quy-etf-tai-viet-nam) — ETF code/index and market-price/iNAV context only.
- [HOSE ETF NAV disclosure](https://staticfile.hsx.vn/Uploads/UploadDocuments/2453325/20260415%20-%20E1VFVN30%20-%20NAV%20April%2013%2C%202026.pdf) — official exchange-hosted document shape.
- [VSDC](https://www.vsd.vn/vi/) — official ETF/fund-service and securities-code context.

No third-party aggregator, paid feed, login/session bypass, API probe, raw payload, or prohibited
derivative source was used.
