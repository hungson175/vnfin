# Quarterly operating-profit and derived-margin source vetting

**Date of observation:** 22 August 2026 (UTC+7)<br>
**Issue:** [#205](https://github.com/hungson175/vnfin/issues/205)<br>
**Disposition:** source-gap closure; no production capability or metric claim

## 1. Decision and clean-room boundary

There is no qualified runtime cell for `SSI` or `TCX` in the two named adapters at this
anchor. The correct outcome is **SOURCE-GAP CLOSURE**. No provider row is promoted to
`operating_profit`, `gross_margin`, `net_margin`, or `operating_cash_flow_margin`.

This note records a direct, bounded observation of `VNDirectFundamentalSource` and
`CafeFFundamentalSource` routes. It does not use the default failover result as an absence
oracle, does not infer retention from an empty response, and does not implement a new source,
template, metric map, ratio call, or reporter. Raw responses and live financial values were
used transiently only; neither is committed as a fixture or bundled dataset.

The mandatory repository blacklist in [`docs/vnstock-blacklist.md`](../vnstock-blacklist.md) was
applied before research; prohibited vendor/derived material was excluded from every search and
citation. Only the two named provider owners' public routes, official issuer disclosures, and
official terms/contact pages were used. No credential, cookie, browser session, private route,
anti-bot bypass, or third-party fixture was used.

### 1.1 Result at a glance

| Runtime target | Qualified | Partial runtime cell | Current disposition |
|---|---:|---:|---|
| `operating_profit` | 0 | 0 | `BLOCKED` / source-gap closure |
| `gross_margin` | 0 | 0 | `BLOCKED` until template/entity and basis are qualified; B02-CTCK gross-profit candidate is not applicable only after that template is bound |
| `net_margin` | 0 | 0 | `BLOCKED` because net-income and revenue identities are not qualified for these streams |
| `operating_cash_flow_margin` | 0 | 0 | `BLOCKED`; CafeF is not served and the VNDirect cashflow stream is foreign/unqualified |

The issuer filings prove what the accounting concept means. They do **not** prove that an
adapter response has the same source namespace, template, entity scope, unit, period basis, or
redistribution rights.

## 2. Probe protocol, budget, and observations

All requests below were HTTPS GETs on 22 August 2026, with a browser user-agent, no credentials,
no cookies, and no login. The HTTP client followed redirects; every request ended on the exact
requested canonical host/path, so `redirected=no` is an observation, not a promise of future
stability. No request was retried.

The bounded research budget was:

* **VNDirect, per symbol and logical statement:** two page-one candidate requests, one
  corporate and one bank template. `size=640` is the adapter's bounded row budget for
  `limit=8`; `page=1`, `sort=fiscalDate:desc`, and `reportType=QUARTER` were fixed. The
  supplementary foreign-template observation was exactly one page each for `modelType=89`,
  `90`, and `91` per symbol; it was not paginated and is not a history/absence claim.
* **CafeF, per symbol and statement:** one request with `TotalRow=32`, `EndDate=3-2026`,
  `ReportType=QUY`, and `Sort=DESC` for each `Type=1`, `2`, and the direct diagnostic `3`.
  The named adapter itself does not issue the `Type=3` request because its static capability
  contract marks cashflow not served.
* **Total:** 24 provider GETs, no retries, no crawl beyond the stated page-one observations.
  Issuer PDFs were consulted separately for accounting cross-checks and their numeric contents
  are not reproduced here.

The current adapter candidates are: VNDirect income `{2,102}`, balance `{1,101}`, cashflow
`{3,103}`; CafeF income `Type=1`, balance `Type=2`, and no named cashflow capability.

## 3. Official accounting identity for operating profit

Official Q1 2026 issuer statements establish the same securities-company concept for two issuers:

* [SSI's official Q1 2026 consolidated disclosure](https://www.ssi.com.vn/en/investor-relation/information-disclosure/detail/disclosure-of-the-1st-quarter-of-2026-consolidated-financial-statements)
  links the [official consolidated statement PDF](https://www.ssi.com.vn/upload/files/IR/20260423_SSI_The_1st_Quarter_of_2026_Consolidated_Financial_Statements.pdf).
  It identifies `B02-CTCK/HN`, `Currency: VND`, and line `70 OPERATING PROFIT`.
* [TCBS's official Q1 2026 disclosure](https://www.tcbs.com.vn/en/investor-relations/financial-report/information-disclosure-on-q1-2026-financial-statements/)
  links the [official TCX statement PDF](https://www.tcbs.com.vn/wp-content/uploads/2026/04/TCBS-BCTC-QI.2026-EN.pdf).
  It identifies `B02-CTCK`, `Currency: VND`, and the same line `70 OPERATING PROFIT`.
* The [official SSI FY2025 audited consolidated statement](https://www.ssi.com.vn/upload/files/IR/20260327_SSI_The_2025_Audited_Consolidated_Financial_Statements.pdf)
  and [official TCX FY2025 audited statement](https://www.tcbs.com.vn/wp-content/uploads/2026/03/TCX-Audited-Financial-Statements-for-2025.pdf)
  provide the annual B02-CTCK(/HN) comparison. These annual documents are cross-check evidence,
  not provider permission or bundled data.

The exact issuer-template identity is:

```text
operating_profit = row 70
                 = row 20 total operating income/revenue
                 + row 50 total financial income
                 - row 40 total operating expenses
                 - row 60 total financial expenses
                 - row 62 general and administrative expenses
```

The statement then separates row `80` other operating profit/loss and computes row `90` profit
before tax as `70 + 80`. Therefore `profit_before_tax`, `other_profit`, `gross_profit`,
`net_income`, and cashflow's “operating profit before changes” are not interchangeable with
`operating_profit`.

The future identity key must be the full tuple:

```text
(source namespace, statement=income, provider template/model, entity scope,
 cadence, exact item code or exact same-report formula, currency, flow basis)
```

A provider label is provenance only. A positive mapping requires the exact code/formula to agree
with the issuer concept, sign, raw-VND scale, consolidation scope, and fiscal date for at least
two periods and at least two issuers using the same non-symbol-specific template. The issuer
documents above prove the accounting concept across two issuers, but no named provider response
proves this complete tuple. No `operating_profit` code is therefore authorized.

**Explicit negative:** `14000` is the existing owners'-equity balance code. Its appearance in a
foreign VNDirect balance stream is not operating profit and must remain a RED test, never a
fallback mapping.

## 4. Source ownership, access, and legal posture

| Source | Owner evidence and contact path | Access/automation observation | Caching/storage | Runtime redistribution | Gate |
|---|---|---|---|---|---|
| VNDirect | [official VNDIRECT terms/contact page](https://www.vndirect.com.vn/dieu-khoan-su-dung/) identifies VNDIRECT and exposes its support/contact path | Public HTTPS GETs returned `200` without auth, cookies, or session; API host/path had no redirect in this probe | No explicit API data-retention grant found | No explicit structured-data redistribution grant found | `LEGAL_GAP` |
| CafeF | [official CafeF data guide](https://cafef.vn/du-lieu/huong-dan-su-dung.chn) and [official data page/contact footer](https://cafef.vn/du-lieu/truongson/thong-tin-chung.chn) identify the data surface and a data contact (`dulieu@cafef.vn`) | Public HTTPS GETs returned `200` without auth, cookies, or session; `Content-Type` was `text/plain; charset=utf-8`; no redirect in this probe | Public availability/robots is not a license; no structured-report caching grant found | The [official RSS terms](https://cafef.vn/index.rss) require attribution for reused RSS content, but do not grant redistribution of these structured financial rows | `LEGAL_GAP` |
| SSI/TCBS filings | Official issuer disclosure pages and PDFs above | Cross-check only; not a new runtime adapter | Not copied into the package | Not a provider license for either named adapter | Evidence only |

The contact paths are escalation paths for written permission, not evidence of permission. Before
any implementation, the owner must grant runtime fetching, automation, retention/caching,
attribution, and downstream redistribution separately or provide a license that clearly covers
all five.

## 5. Exact 12-cell matrix at `Period.QUARTER`

Notation used below:

* `∅` means the typed adapter accepted no report; it never means the issuer has no history.
* `identity=absent` means the response did not expose a requested-symbol identity field; a
  symbol in the request URL is not response-backed identity.
* `basis=UNKNOWN` means a date/cadence marker exists but discrete-quarter versus YTD/trailing
  semantics are not proven.
* Labels are provenance only. The exact observed item-code sets are listed without values.
* The final disposition is one of the packet's allowed cell outcomes; secondary gaps are listed
  in the evidence column and do not become a positive claim.

| Cell | Request, access, redirect, and bounded budget | Transport/application result | Response identity, template/entity, dates, unit, and target codes | Legal and disposition |
|---|---|---|---|---|
| `SSI · vndirect · income` | `financial_statements`; `code:SSI~reportType:QUARTER~modelType:{2,102}`; `size=640&page=1`; no auth/cookie/session; redirect=no; 2 candidate requests | Both candidates: HTTP `200`, `application/json`, empty `data`, provider totals zero; typed result `EmptyData` | No accepted row, so no returned symbol/statement/date/unit. Supplementary `modelType=90` page-one rows had `code=SSI`, `reportType=QUARTER`, exact `fiscalDate` fields, and target-like codes `21001,23000,23003,23100,23800`, but the model is foreign to the current contract and has no entity/unit/basis semantics. | VNDirect terms do not grant structured-data reuse. `IDENTITY_GAP` (also legal and period-basis gaps); no target metric is qualified |
| `SSI · vndirect · balance` | `financial_statements`; `code:SSI~reportType:QUARTER~modelType:{1,101}`; same access/redirect/budget | Both candidates: HTTP `200`, `application/json`, empty `data`; typed `EmptyData` | No accepted row. Supplementary `modelType=89` rows had `code=SSI`, `reportType=QUARTER`, fiscal dates, and observed `14000`; this is an unqualified foreign balance stream and is explicitly **not** operating profit. No unit/scope/basis proof. | `IDENTITY_GAP`; balance is not a target input, but the negative `14000` boundary is preserved |
| `SSI · vndirect · cashflow` | `financial_statements`; `code:SSI~reportType:QUARTER~modelType:{3,103}`; same access/redirect/budget | Both candidates: HTTP `200`, `application/json`, empty `data`; typed `EmptyData` | No accepted row. Supplementary `modelType=91` rows had `code=SSI`, `reportType=QUARTER`, fiscal dates, and observed `32000`; stream semantics, unit, entity scope, and discrete/YTD basis remain unresolved. | `IDENTITY_GAP`; `operating_cash_flow_margin` stays `BLOCKED` |
| `TCX · vndirect · income` | `financial_statements`; `code:TCX~reportType:QUARTER~modelType:{2,102}`; same access/redirect/budget | Both candidates: HTTP `200`, `application/json`, empty `data`; typed `EmptyData` | No accepted row. Supplementary `modelType=90` rows had `code=TCX`, `reportType=QUARTER`, fiscal dates, and observed `21001,23000,23003,23100,23800`; no qualified template/entity/unit/basis. | `IDENTITY_GAP`; no target metric is qualified |
| `TCX · vndirect · balance` | `financial_statements`; `code:TCX~reportType:QUARTER~modelType:{1,101}`; same access/redirect/budget | Both candidates: HTTP `200`, `application/json`, empty `data`; typed `EmptyData` | No accepted row. Supplementary `modelType=89` rows had `code=TCX`, `reportType=QUARTER`, fiscal dates, and observed `14000`; foreign/unqualified balance evidence only. | `IDENTITY_GAP`; `14000` remains a negative operating-profit fixture |
| `TCX · vndirect · cashflow` | `financial_statements`; `code:TCX~reportType:QUARTER~modelType:{3,103}`; same access/redirect/budget | Both candidates: HTTP `200`, `application/json`, empty `data`; typed `EmptyData` | No accepted row. Supplementary `modelType=91` rows had `code=TCX`, `reportType=QUARTER`, fiscal dates, and observed `32000`; no unit/entity/basis proof. | `IDENTITY_GAP`; `operating_cash_flow_margin` stays `BLOCKED` |
| `SSI · cafef · income` | `FinanceReport.ashx`; `Type=1&Symbol=SSI&TotalRow=32&EndDate=3-2026&ReportType=QUY&Sort=DESC`; no auth/cookie/session; redirect=no; 1 request | HTTP `200`, `text/plain; charset=utf-8`, JSON envelope `Success=true`; `Count=41`, returned 32 period objects | `identity=absent`; no model discriminator; page markers include `Time=Q2-2026`, `Year=2026`, `Quater=2`, response `ReportType=H`; observed codes `DTTBHCCDV,LNTC,TotalProfit,LNSTTNDN,NetIncome,LNK`; no exact row 70, no explicit unit/scale, scope, or flow basis. `H` is not promoted to cadence. | `IDENTITY_GAP` (also unit, basis, and legal gaps); no target metric is qualified |
| `SSI · cafef · balance` | `FinanceReport.ashx`; `Type=2&Symbol=SSI&TotalRow=32&EndDate=3-2026&ReportType=QUY&Sort=DESC`; same access/redirect/budget | HTTP `200`, `text/plain; charset=utf-8`, `Success=true`; `Count=41`, returned 32 period objects | `identity=absent`; no model discriminator; page markers include Q2-2026 and response `ReportType=H`; observed codes `ShortTermFloatingCapital,TotalAsset,TotalShortTermDebt,TotalDebt,TotalOwnerCapital`; no target metric input, unit/scale, scope, or flow basis is qualified. | `IDENTITY_GAP`; balance is not target evidence |
| `SSI · cafef · cashflow` | Direct diagnostic only: `Type=3&Symbol=SSI&TotalRow=32&EndDate=3-2026&ReportType=QUY&Sort=DESC`; no auth/cookie/session; redirect=no; 1 diagnostic request | HTTP `200`, `text/plain; charset=utf-8`, `Success=true`, `Count=41`, `Value=[]`; named adapter makes zero HTTP calls for this cell | No returned symbol, date, code, unit, or basis; current static capability says cashflow is not served. | `NOT_SERVED`; do not reclassify the empty diagnostic as historical absence |
| `TCX · cafef · income` | `FinanceReport.ashx`; `Type=1&Symbol=TCX&TotalRow=32&EndDate=3-2026&ReportType=QUY&Sort=DESC`; same access/redirect/budget | HTTP `200`, `text/plain; charset=utf-8`, `Success=true`; `Count=7`, returned 7 period objects | `identity=absent`; no model discriminator; page markers include Q2-2026, `Year=2026`, `Quater=2`, response `ReportType=N`; observed codes `DTTBHCCDV,LNTC,TotalProfit,LNSTTNDN,NetIncome,LNK`; no exact row 70, explicit unit/scale, entity scope, or flow basis. `N` is not promoted to cadence. | `IDENTITY_GAP` (also unit, basis, and legal gaps); no target metric is qualified |
| `TCX · cafef · balance` | `FinanceReport.ashx`; `Type=2&Symbol=TCX&TotalRow=32&EndDate=3-2026&ReportType=QUY&Sort=DESC`; same access/redirect/budget | HTTP `200`, `text/plain; charset=utf-8`, `Success=true`; `Count=7`, returned 7 period objects | `identity=absent`; no model discriminator; page markers include Q2-2026 and response `ReportType=N`; observed codes `ShortTermFloatingCapital,TotalAsset,TotalShortTermDebt,TotalDebt,TotalOwnerCapital`; no target metric input, unit/scale, scope, or flow basis is qualified. | `IDENTITY_GAP`; balance is not target evidence |
| `TCX · cafef · cashflow` | Direct diagnostic only: `Type=3&Symbol=TCX&TotalRow=32&EndDate=3-2026&ReportType=QUY&Sort=DESC`; no auth/cookie/session; redirect=no; 1 diagnostic request | HTTP `200`, `text/plain; charset=utf-8`, `Success=true`, `Count=7`, `Value=[]`; named adapter makes zero HTTP calls for this cell | No returned symbol, date, code, unit, or basis; current static capability says cashflow is not served. | `NOT_SERVED`; `operating_cash_flow_margin` remains `BLOCKED` |

The VNDirect foreign observations are three **independent** streams. They are not a universal
securities template, and one stream may not borrow another stream's item meanings. The CafeF
`ReportType` response markers `H`, `N`, and the previously observed annual `K` are recorded as
provider markers only; they are not silently treated as the requested `QUY`/`NAM` cadence.
The non-empty quarterly probes included the latest provider date marker `2026-06-30` (CafeF
`Time=Q2-2026`, `Year=2026`, `Quater=2`; VNDirect `fiscalDate=2026-06-30`). This is a
response-backed date observation, not proof that the flow values are discrete rather than YTD.

## 6. Quarterly discrete-versus-YTD contract

`Period.QUARTER` means one discrete fiscal quarter for every flow metric in this issue. A matching
quarter-end date alone is insufficient.

The official issuer Q1 statements visibly have separate `Quarter 1` and `Accumulated` columns.
Q1 equality is expected and does not prove that a provider's Q2/Q3/Q4 object is discrete. The
current CafeF response supplies `Time`/`Year`/`Quater`, which can locate a candidate fiscal end,
but does not expose a trusted start date or a discrete/YTD basis. The current VNDirect foreign
rows supply `fiscalDate` and `reportType=QUARTER`, but no basis or period start/end. The existing
source research also records a distinct VNDirect `QUARTER2` cumulative stream; it must never be
relabeled as `QUARTER` ([prior source note](2026-06-18-vn-fundamental-data-sources.md)).

Before any implementation, the additive immutable report/lineage slice must carry these fields,
appended after all existing fields so old positional constructors remain valid:

```python
class FlowBasis(str, Enum):
    QUARTER_ONLY = "quarter_only"
    YEAR_TO_DATE = "year_to_date"
    TRAILING = "trailing"
    ANNUAL = "annual"
    INSTANT = "instant"
    UNKNOWN = "unknown"

# defaulted fields on FinancialReport and MetricInput, after current fields
period_start: date | None = None
period_end: date | None = None
flow_basis: FlowBasis = FlowBasis.UNKNOWN
template_id: str | None = None
consolidation_scope: str = "unknown"  # only qualified values: consolidated/separate/unknown
```

Required invariants:

1. Income/cashflow flow rows may enter a requested quarter only with
   `period_end == fiscal_date`, a real `period_start`, and `flow_basis=quarter_only`.
2. Balance rows use `flow_basis=instant` and `period_end=fiscal_date`; they never supply a flow
   numerator or denominator.
3. `year_to_date`, `trailing`, `annual`, and `unknown` are rejected from quarterly margin joins.
   No adjacent-quarter subtraction is allowed without a separate reviewed restatement contract.
4. `gross_margin` and `net_margin` join numerator and denominator from the same qualified income
   report, symbol, scope, template, fiscal date, unit, and flow basis.
5. `operating_cash_flow_margin` additionally requires the cashflow and income reports to share
   the same qualified discrete-quarter basis and scope. End-date equality alone does not pass.
6. Template/model, scope, period bounds, and basis propagate into `MetricInput` lineage and are
   validated before calculation. Unknown or mismatched values fail closed as `BLOCKED`.

## 7. Four-metric derived-input gap analysis

The current 26-metric catalog and source namespace remain unchanged. The existing VNDirect
corporate slots are evidence boundaries, not permission to apply them to a foreign template:

| Input/metric | Existing generic code contract | SSI/TCX source result | Honest future classification |
|---|---|---|---|
| `operating_profit` | No corporate code; exact row 70 identity required | No provider code/template/period-basis tuple | `BLOCKED` until a qualified source-specific mapping or formula |
| `gross_margin` | `gross_profit=23100` divided by `net_revenue=21001`, same income report/date/basis | B02-CTCK has no generic gross-profit row; current provider cells do not bind to B02-CTCK or prove discrete basis | `NOT_APPLICABLE` is allowed only after an exact B02-CTCK template is bound; at this source-gap anchor it is `BLOCKED` |
| `net_margin` | `net_income=23003` divided by `net_revenue=21001`, same income report/date/basis | Foreign VNDirect `90` contains target-like codes but no qualified semantics; CafeF has `LNSTTNDN`/`NetIncome` and no qualified net-revenue identity | `BLOCKED`; never infer `MISSING` from empty or rejected rows |
| `operating_cash_flow_margin` | `operating_cash_flow=32000` divided by `net_revenue=21001`, same discrete flow basis across cashflow/income | CafeF cashflow is `NOT_SERVED`; foreign VNDirect `91` contains `32000` but no qualified statement/unit/basis identity | `BLOCKED` until both statement inputs are qualified with common discrete basis |

For every symbol and requested quarter, the future implementation must report each input as
`AVAILABLE`, `MISSING`, `BLOCKED`, or `NOT_APPLICABLE`, while retaining statement-level
`SOURCE_ERROR`/`NOT_SERVED` diagnostics. A qualified mapping with an absent line may be
`MISSING`; an unqualified template, code, scope, unit, or basis is `BLOCKED`. No percentage,
18/30 breadth target, universe floor, or global source claim is defined here.

## 8. Conjunctive reopen criteria

The source gap can reopen only when **all** of the following hold for each source, symbol,
statement, template, and metric scope; one passing axis cannot compensate for another:

1. The source owner gives written permission or a license covering runtime fetch, automation,
   caching/retention, attribution, and downstream redistribution.
2. The response carries exact requested-symbol identity and exact statement/entity/template
   identity. URL-only identity, absent identity, mixed rows, redirects not covered by the owner,
   or a model mismatch fail closed.
3. VNDirect `89`, `90`, and `91` are qualified independently. A future design must bind each to
   one statement/template/entity scope, prove its own item namespace, and never treat the bank
   boolean, a symbol branch, a label, or another stream as its discriminator.
4. CafeF proves the meaning of `H`, `N`, `K`, and `QUY`/`NAM` separately, exposes or authorizes
   response identity, and proves source unit/scale and consolidation scope. Type 3 remains
   `NOT_SERVED` unless a separately documented capability is approved.
5. The exact operating-profit row/code or same-report formula is cross-checked against official
   issuer filings for at least two periods and two issuers on the same template, including sign,
   raw VND scale, scope, and date. A code that merely resembles `14000` or a provider label is
   rejected.
6. Annual and quarterly behavior are both proven wherever the mapping is not explicitly
   cadence-qualified. Every quarterly flow has immutable start/end and `quarter_only` basis;
   YTD/annual/trailing/unknown responses remain blocked.
7. The four target metrics have complete, source-namespaced input lineage. Gross-profit absence
   is `NOT_APPLICABLE` only for a proven securities-company template; all economically meaningful
   but unverified inputs remain `BLOCKED`.
8. A deterministic future request plan is approved before code: one atomic reservation per
   logical cell, a fixed page ceiling and fixed retry ledger, retry only for explicitly allowed
   transport statuses, no retry on identity/schema failures, and a terminal diagnostic that
   distinguishes transport, empty, malformed, identity, basis, legal, and not-served outcomes.
   The present evidence budget is observation-only and is not a runtime quota promise.
9. The implementation begins with RED tests using synthetic fixtures only, including direct/chain
   parity, zero ratio calls, `14000`, all foreign `89/90/91`, CafeF `K/H/QUY` boundaries,
   discrete/YTD mismatches, unit/scope mismatches, and no physical CafeF cashflow call.

Until all nine criteria are evidenced and reviewed, the only permitted change is another
docs/source-gap correction. No production code, API expansion, push, or issue close is authorized
by this note.

## 9. Compatibility boundary

The following remain unchanged at the source-gap anchor:

* exactly 26 metric IDs; `operating_profit` remains `RAW_MAPPED` with no corporate code;
* `gross_margin`, `net_margin`, and `operating_cash_flow_margin` remain offline `DERIVED` metrics;
* `metrics()` fetches income, balance, and cashflow only; `StatementType.RATIOS` physical call
  count is zero and `ratio_status=NOT_REQUESTED`;
* `14000` is owners' equity, never operating profit;
* VNDirect `89/90/91` remain fail-closed and cannot be collapsed; CafeF cashflow remains
  `NOT_SERVED`;
* no VN30, breadth, ranking, screening, universe, or investment-rule API is added; and
* source errors remain bounded typed diagnostics without URLs, response bodies, exception text,
  or failed-attempt trails in public models.

This is the complete source/design evidence for #205. It authorizes design review only, not TDD
implementation.
