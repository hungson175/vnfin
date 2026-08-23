# #218 design note — ETF discovery and provider-published NAV history

**Status:** `SOURCE-GAP CLOSURE`; exact-SHA source/design only; no RED, code, source registration,
model/accessor change, push, or close
**Packet:** `tasks/218-etf-discovery-nav-history-spec.md` at reviewer `5acb355`
**Research:** [source vetting](../docs/research/2026-08-23-vn-etf-discovery-nav-history-source-vetting.md)
**Requested inclusive span:** `2018-01-01..2026-08-19`
**Published base:** `8d1490fbda0aaaf217d9b98a51cd38c84dfaee16`
**Block record:** `9c48084`; reviewed anchor `ce1db49fe2508a900ed2f68b43054401cb0b8da5`
**Local activation:** `77671d42d9be16d1c4264397cf9939c266f6b4d8` (backlog-only and unpushed)

This is a documentation-only source-gap correction. It does not authorize a new ETF token, public
model, parser, source registration, runtime call, RED test, or coverage assertion. The current
Fmarket surface remains open-ended mutual funds. Discount, first-difference, replay, strategy, and
VN30F comparison stay caller-side.

## 1. Decision and source-gap boundary

`SOURCE-GAP CLOSURE` is the only qualified disposition for the requested capability. Fmarket's
official terms restrict software collection/copying/monitoring and do not grant API automation,
caller return, storage, or redistribution rights. The no-probe decision is therefore preserved.

Alternative official owner route sets were independently reviewed rather than rejected for lacking a
Fmarket ID. VinaCapital's VN100 ETF page plus its linked NAV-document family is a real candidate:
it proves FUEVN100/ETF/HOSE identity, product inception, and named daily/weekly NAV reports. It does
not prove the requested 2018 start, a complete historical index, correction semantics, bounded
machine retrieval, or lawful OSS reuse. HOSE contributes a one-document NAV identity shape; Dragon
and VSDC provide narrower support/context. No owner route set passes all axes, so the new chain stays
empty and SOURCE-GAP remains honest. No cross-owner stitch is permitted.

The complete future qualification unit is:

```text
one owner + one approved bounded route set
+ response/document-backed ETF identity and selected product basis
+ discovery/detail/NAV binding + provider-published NAV semantics
+ requested or declared partial coverage + revision/non-publication rules
+ lawful automation/caller-return/storage/redistribution posture
```

## 2. Current API and compatibility contract

The v0.2.0/current comparison is not identical:

| Seam | v0.2.0 | Current published tree | #218 |
| --- | --- | --- | --- |
| `list_funds` | `asset_type=None, search="", page_size=100` | Adds `include_metadata=True`, validation, and existing warnings | Unchanged |
| `Fund` | Original code/name/id/nav/manager/asset_type/currency fields | Adds optional `nav_as_of`, `management_fee_pct`, `inception_date`, `description` | Unchanged |
| `NavHistory` | Existing product-ID history, VND/unit, optional `code` | Same public shape with current window/diagnostic behavior | Unchanged |
| Code/search seams | Search is free text; response helper is existing | `search` remains free text; `canonical_fund_code` remains current `[A-Z][A-Z0-9]*` response grammar | No ETF grammar |
| Fmarket routes | Mutual-fund filter/detail/NAV baselines | Same provider route family | No ETF route |

The following is a future compatibility sketch, not a working capability:

```python
src = vnfin.funds.source()
listing = src.list_funds(asset_type="ETF", search="E1VFVN30", include_metadata=True)
history = src.nav_history(product_id, from_date="2018-01-01", to_date="2026-08-19")
```

Current `list_funds.search` is free text and `asset_type` is forwarded to
`fundAssetTypes`; no official proof makes `ETF` a selector or product-type token. Current
`nav_history` requires a response-backed mutual-fund product ID. A blank/unserved filter is not
confirmed absence. No new ETF code grammar is frozen: any selector normalization, provider
translation, or future `NavHistory.code` provenance is deferred to source proof plus a fresh
RED/API review. Legacy asset strings and response-code compatibility remain protected.

## 3. Qualification predicates

A future positive fixture must prove, without cross-source joins:

1. the owner route accepted an exact ETF selector/code and identified ETF product type independently
   from an investment asset class;
2. the selected product has response/document-backed code, legal name, manager, owner/product identity,
   and exchange/listing identity;
3. discovery/detail/NAV documents bind the same selected product without duplicate, renamed, delisted,
   share-class, or cross-product ambiguity;
4. every NAV row is scoped to that selected product and is provider-published NAV per unit in VND,
   not iNAV, market price, adjusted price, or local derivation;
5. date/publication/timezone, unit, cadence, correction, cancellation, revision, and same-date conflict
   semantics are explicit; and
6. requested or provider-declared partial coverage, pages/totals/cursors, non-publication, and observed
   endpoints reconcile for `2018-01-01..2026-08-19`.

Existing repository route baselines are not ETF proof:

| Unit | Current baseline | Required owner proof | Disposition |
| --- | --- | --- | --- |
| ETF discovery | `POST https://api.fmarket.vn/res/products/filter` | Owner selector/token, success/document identity, totals/pages, transport, legal permission | `SOURCE-GAP` |
| Selected detail | `GET https://api.fmarket.vn/res/products/{id}` | Same owner/product/code/type/listing binding and permission | `SOURCE-GAP` |
| ETF NAV history | `POST https://api.fmarket.vn/res/product/get-nav-history` | Same basis, NAV/unit/date/revision/cadence/bounds, permission | `SOURCE-GAP` |

No Fmarket dispatch was made. The three paths are mutual-fund compatibility assumptions only.

## 4. Independent official route-set evidence

The following evidence is read-only official-page/document research, not Fmarket probing:

| Route set | Identity/document evidence | Coverage/transport/revision/legal disposition |
| --- | --- | --- |
| **VinaCapital owner set**: [manager ETF page](https://wm.vinacapital.com/investment-solutions/onshore-funds/vinacapital-vn100-etf/), [disclosure index](https://wm.vinacapital.com/information-disclosure/), linked report family, and sampled [official PDF](https://wm.vinacapital.com/wp-content/uploads/2026/02/20260212-VINACAPITAL-VN100-ETF_Monthly-Factsheet_Jan-2026-EN.pdf) | The manager page names VinaCapital VN100 ETF/FUEVN100, HOSE, product inception `2020-06-16`, daily dealing, and daily/weekly NAV report labels. The sampled linked document is an official `application/pdf` factsheet with the same ETF identity and NAV-per-share field context. | Product inception is later than requested `2018-01-01`; recent report labels do not prove earliest bound, totals, complete history, or a non-publication calendar. Individual daily-link status/effective redirect/MIME and machine schema were not dispatched. No correction/cancellation contract or owner permission for automation, caller return, storage, or redistribution was found. `UNKNOWN` / `RUNTIME_GAP` / `LEGAL_GAP`; not `FULL` or `PARTIAL`. |
| **HOSE document set**: [official E1VFVN30 disclosure PDF](https://staticfile.hsx.vn/Uploads/UploadDocuments/2453325/20260415%20-%20E1VFVN30%20-%20NAV%20April%2013%2C%202026.pdf) | Official exchange-hosted PDF identity binds ETF/code/manager/report and NAV per fund certificate/per lot in VND context. | One document is not a history index or route set with requested bounds, page/total reconciliation, cadence, revision, or reuse terms. `DOCUMENT_SUPPORT_ONLY` / `LEGAL_GAP`; no Dragon/Vina stitch. |
| **Dragon manager page**: [official ETF list article](https://dautu.dragoncapital.com.vn/kien-thuc/danh-sach-quy-etf-tai-viet-nam) | Official HTML lists ETF ticker/index pairs and discusses market price versus iNAV. | It does not establish a provider-published NAV-per-unit route/history or legal automation grant. Label `IDENTITY_SUPPORT_ONLY`; do not claim it proves NAV/unit. |
| **VSDC context**: [official services page](https://www.vsd.vn/vi/) | Official service page describes fund services and securities-code role. | It is infrastructure context, not an ETF NAV owner route. Label `SERVICE_CONTEXT_ONLY`. |

Each route set is evaluated on its own owner/basis. No row is dismissed for lacking a Fmarket ID; no
row is promoted beyond the evidence it owns. The new source chain remains empty.

## 5. Coverage and no-false-absence contract

Retain these separate fields for every future route set:

```text
requested_start/end
provider_declared_product_or_served_start/end
provider_total/page/cursor/revision evidence
observed_start/end and distinct in-range count
provider cadence and confirmed non-publication evidence
```

`FULL` requires provider bounds covering the request, reconciled pages/totals/cursors, identity on
every row, ordered distinct observations after revision handling, and provider calendar/non-publication
semantics for missing dates. `PARTIAL` requires provider-declared narrower bounds plus exact
reconciliation and must not be called full requested coverage. `UNKNOWN` is mandatory for any
unproven bound, page, identity, publication, cadence, or revision axis.

`UNVERIFIED_SELECTOR`, `UNSERVED`, `CONFIRMED_EMPTY`, and `UNKNOWN` remain distinct. A blank,
HTML/WAF/error/timeout/missing-page response or an open-ended-only page is not proof that no ETF
exists. No new enum or public exception is added in this closure.

## 6. Future runtime invariants; exact budgets deferred

No numeric page, retry, physical-dispatch, response-byte, or request-byte value is source-approved
here. Exact values are `DEFERRED_UNTIL_QUALIFIED_OWNER_ROUTE`; they are not frozen API/RED contracts.

After one owner route set qualifies, the future scheduler must have:

- one sequential request-scoped ledger with atomic reservation before dispatch;
- capability skips that create no attempt and consume no budget;
- owner-approved retries that reuse the same logical target and same global ledger;
- atomic streaming/decompression-byte accounting and bounded sanitized attempts;
- pre-dispatch reservation exhaustion versus post-dispatch stream-byte exhaustion; and
- fatal status/MIME/parse/page/identity/revision/total/budget failure returning no partial discovery,
  selected-detail, or NAV accumulator.

No source failover, cross-owner stitch, product fan-out, or name-only join is allowed. Exact finite
diagnostic names, MIME/status rules, and public error text are deferred until a source-specific
design. Raw URLs with queries, bodies, headers, cookies, credentials, provider prose, and exception
text never enter public results or fixtures.

## 7. Legal gate and separate existing-runtime risk

Fmarket terms are a provider-wide legal blocker, not an ETF-only exemption. The current mutual-fund
adapter is unchanged, but its runtime-fetch-only/no-redistribution posture is engineering behavior,
not an owner permission. Record this separate durable disposition:

```text
MUTUAL_RUNTIME_LEGAL_RISK
  Existing Fmarket mutual-fund automation/caller-return/storage posture is unresolved under
  provider-wide terms. Maintainer/legal triage is required; #218 neither blesses nor revokes it.

ETF_SOURCE_LEGAL_GAP
  New ETF automation/caller-return/storage/redistribution/rate/revision rights are unproven.
```

For a future qualified route, all nine axes remain conjunctive: owner identity, automated access,
caller-facing return, storage/cache, redistribution, attribution, commercial use, rate/retry, and
revision/correction. Public reachability, a page/PDF, or a distribution licence is not a reuse grant.

## 8. Exact lifecycle and release boundary

The blocker was recorded first in backlog commit `9c48084`; correction actor is `vnfin-oss`.
A corrected exact-SHA handoff must retain the published base `8d1490f`, name its exact
`8d1490f..<approved-anchor>` range, and change only:

- `docs/research/2026-08-23-vn-etf-discovery-nav-history-source-vetting.md`
- `tasks/218-design-note.md`
- `tasks/active-backlog.md`

After a future design PASS: rerun merged gates; push only the approved anchor; verify remote exact
HEAD/base ancestry/three paths; post a clean no-capability `SOURCE-GAP` resolution; close and
re-read #218; only then activate #219. #220 remains queued. No later commit may be pushed in that
approved range. A future implementation requires a fresh design PASS and must include fund API/source/
diagnostics/tutorial and agent-facing AI docs, the maintainer skill, `CHANGELOG.md`, release notes,
tests, build, blacklist/secret, diff, and path gates.

## 9. Future RED/release matrix (not authorized now)

After a fresh design PASS only, synthetic fixtures must cover identity positives/negatives, selector
compatibility and zero-network rejection, provider-published VND/unit NAV versus iNAV/market-price/
adjusted-price negatives, inclusive bounds/pages/totals/cursors, cadence/non-publication, revisions,
`FULL`/`PARTIAL`/`UNKNOWN`, no-false-absence, reservation-versus-stream exhaustion, sanitized
diagnostics, and no partial accumulator. The exact numeric ledger values are not specified here.

Existing fund listing/NAV/holdings/allocation/warnings/DataFrame/API snapshots, imports/version,
unrelated domains, offline suite, package build, blacklist/secret/path/diff checks, and the release
documentation/skill/changelog obligations remain required in any later implementation.

No RED, code, model/accessor, source registration, production capability, discount calculation,
first difference, or VN30F logic is part of this handoff.
