# #208 annual operating profit — source vetting

**Date:** 23 August 2026 (UTC+7)
**Packet:** `tasks/208-annual-operating-profit-spec.md` (reviewer packet `3699ae5`)
**Requested API:** existing `vnfin.fundamentals.metrics(..., period="annual")`
**Decision:** **SOURCE-GAP CLOSURE** — no annual operating-profit mapping, RED test, production
code, push, or issue closure is authorized by this note.

This is a clean-room source, accounting-identity, legal, and compatibility review. It does not add a
provider, infer a formula at runtime, change the 26-metric catalog, fetch ratios, or turn a source
failure into `MISSING` or zero. The current `MetricId.OPERATING_PROFIT` remains
`RAW_MAPPED` with no verified code and therefore remains `BLOCKED`.

## 1. Clean-room boundary and scope

Before this research I ran the repository checklist at
[`docs/vnstock-blacklist.md`](../vnstock-blacklist.md). Every search used this exact exclusion:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted source, derivative artifact, endpoint map, schema, code, test, package, or behavior
was opened, cited, compared, or used. Evidence below is limited to the named first-party
VNDirect/CafeF routes, official issuer/exchange filings, and already-reviewed repository source
notes. Raw responses, live statement values, screenshots, cookies, and response bodies were not
written to the repository.

The product boundary is one provider-observed annual income-statement value for
`operating_profit`, with exact fiscal date and complete source/template lineage. This round does
not cover VN30 membership, breadth, ranking, signals, futures sessions, advice, ratios, EBITDA,
EBIT inferred from another line, gross profit, profit before tax, net income, cashflow formulas, or
any locally calculated proxy.

## 2. Current API invariants

| Existing contract | Required preservation |
| --- | --- |
| Catalog | Exactly 26 `MetricId` members; do not add an alias or second operating-profit metric. |
| Metric kind | `MetricId.OPERATING_PROFIT` remains `MetricKind.RAW_MAPPED`; no formula or provider ratio. |
| Current mapping | `codes_by_source["vndirect"].corporate_code is None`; this is `BLOCKED`, not upstream `MISSING`. |
| Entity | `AppliesTo.CORPORATE` remains unchanged; banks receive `NOT_APPLICABLE`. |
| Cadence | Annual qualification must not make the existing quarterly path resolve. Quarterly remains the #205 source gap. |
| Sources | Probe only the existing `VNDirectFundamentalSource` and `CafeFFundamentalSource`; no new source. |
| Calls | Metrics fetch income, balance, and cashflow only. `StatementType.RATIOS` calls remain exactly zero and `ratio_status=NOT_REQUESTED`. |
| Provenance | `MetricInput` must carry statement, exact source-namespaced item code, value/unit, fiscal date, source, and provider line name. |
| Release line | The annotated `v0.2.0` tag predates the metrics surface; current master still declares package version `0.2.0`. No tagged-v0.2.0 capability claim is allowed. |

The implementation currently has only the VNDirect namespace in the catalog. A future CafeF
mapping, if ever qualified, must be a separately namespaced field and may never occupy a VNDirect
numeric slot.

## 3. Bounded direct-probe protocol

The fresh probes ran on 23 August 2026 with a new process, IPv4, the project desktop-Chrome
User-Agent, no authentication, no key, no cookie/session, no proxy, no browser challenge bypass,
and no retry. The probe retained only status, effective route, MIME/envelope markers, provider
identity/template tags, item-code presence, distinct fiscal dates, and bounded counts.

| Owner route | Probe budget and cells | Sanitized result |
| --- | --- | --- |
| VNDirect `/v4/financial_statements` | 8 symbols × two direct annual model filters (`modelType=2` and `102`), `size=640&page=1`: 16 physical GETs; caller history `limit` was not asserted; no facade or failover winner | All completed with HTTP 200 JSON. Corporate model 2 returned structured rows for FPT, HPG, and VNM; bank model 102 returned structured rows for VCB and ACB. Accepted model filters for SSI, TCX, and BVH returned empty JSON envelopes. The row/page bound is a probe budget, not a public history promise. |
| CafeF `FinanceReport.ashx` | Direct annual income attempts for FPT and HPG, `Type=1&TotalRow=32&EndDate=2026&ReportType=NAM&Sort=DESC`; caller history `limit` was not asserted; two bounded physical GETs | Both attempts timed out without a response body. No redirect, MIME, envelope, symbol, row, or date claim is made. This is `TRANSPORT_INCONCLUSIVE`, not historical absence; `TotalRow=32` is only a transport bound. |
| Previously reviewed special-template evidence | #204/#205 direct SSI/TCX observations, cited below and not re-fetched into this report | VNDirect foreign streams 89/90/91 and CafeF annual candidate rows remain independently unqualified; no stream is promoted by this annual round. |

A VNDirect `totalElements` value counts tall line-item rows, not fiscal periods. The date counts
below are the distinct provider `fiscalDate` values in the bounded response. No older-year
absence is inferred from an empty route, a timeout, a truncated probe, or a budget ceiling.

## 4. Accounting identity and candidate code

The official audited consolidated income statements for FPT and Hòa Phát identify row 30 as
**Lợi nhuận thuần từ hoạt động kinh doanh** (net operating profit). Their published row identity is
the operating-activities result, distinct from gross profit, other income, profit before tax, and
net income:

```text
row 30 = row 20 + row 21 - row 22 + row 24 - row 25 - row 26
```

The exact presentation formula differs typographically between filings but the accounting concept
is the same. The [FPT 2025 annual report](https://fpt.com/-/media/project/fpt-corporation/fpt/ir/information-disclosures/year-report/2026/april/bctn-fpt-2025.pdf)
and [FPT consolidated 2024 report](https://fpt.com/-/media/project/fpt-corporation/fpt/ir/information-disclosures/year-report/2025/january/20250124---fpt---bctc-hop-nhat-quy-4-nam-2024.pdf)
show the audited consolidated row and VND unit. The
[Hòa Phát 2025 consolidated report](https://file.hoaphat.com.vn/hoaphat-com-vn/2026/01/20260130-hpg-bao-cao-tai-chinh-hop-nhat-va-giai-trinh-q4-2025.pdf)
and [Hòa Phát 2024 annual report](https://file.hoaphat.com.vn/hoaphat-com-vn/2025/04/bao-cao-thuong-nien-hpg-2024.pdf)
provide the independent second issuer and prior annual period.

The bounded VNDirect model-2 rows contain candidate `itemCode=23110.0` for every observed annual
period of FPT, HPG, and VNM. An out-of-repository cross-check matched `23110` to the official
row-30 result for FPT and HPG in the 2024 and 2025 audited reports above. Only the code, dates,
identity, and cross-check disposition—not any live numeric value—are retained here. The provider
response has no human line label or unit field, so `23110` is a strong generic-template
candidate, not yet a qualified public mapping.

The candidate must not be confused with existing or disproved identities:

| Code/label | Proven meaning or boundary | Operating-profit status |
| --- | --- | --- |
| `23100` | Generic corporate gross profit / row 20 | Not the target |
| `23110` | Candidate generic corporate row-30 operating profit | Candidate only; exact tuple and rights still gate qualification |
| `23500` | Generic corporate profit attributable to non-controlling interests | Not the target |
| `23800` | Generic corporate profit before tax / row 50 | Not the target |
| `14000` | Owners' equity in the generic corporate balance template | Explicit negative; never an operating-profit shortcut |
| B02-CTCK row 70 | Securities-company operating-profit formula cross-check | Never calculate a `RAW_MAPPED` value from it |

## 5. Annual source/template matrix

The matrix is by provider template and source namespace, not merely by symbol or
`is_bank=False`. `∅` means no accepted provider fiscal date in that cell. A row with a
successful response can still be unqualified when the provider template, code semantics, unit, or
legal posture is unresolved.

| Cell | Direct route and response identity | Annual dates/count in bounded observation | Candidate code/line and unit | Legal/runtime posture | Disposition |
| --- | --- | --- | --- | --- | --- |
| VNDirect · generic corporate · FPT | `financial_statements?q=code:FPT~reportType:ANNUAL~modelType:2&sort=fiscalDate:desc&size=640&page=1`; HTTP 200 JSON; response `code=FPT`, `reportType=ANNUAL`, `modelType=2.0` | 587 line-item rows; 24 distinct dates, 2002-12-31..2025-12-31; candidate present across all observed dates | `23110`, audited row-30 cross-check; adapter/source contract emits raw VND, but provider response has no unit field | No route-specific automation, retention, caching, or caller-facing redistribution grant | `LEGAL_GAP` |
| VNDirect · generic corporate · HPG | Same canonical route with `code=HPG`; same response identity and model | 510 line-item rows; 21 distinct dates, 2005-12-31..2025-12-31; candidate present across all observed dates | `23110`, same row-30 candidate cross-checked for 2024/2025 official consolidated reports; raw-VND scale is cross-check evidence, not a provider unit field | Same unproven rights and no numeric provider quota | `LEGAL_GAP` |
| VNDirect · generic corporate · VNM | Same canonical route with `code=VNM`; HTTP 200 JSON, `modelType=2.0`, annual rows | 567 line-item rows; 23 distinct dates, 2003-12-31..2025-12-31; candidate present across all observed dates | `23110` candidate; no second independent filing cross-check retained in this round | Rights, rate policy, and provider semantic label remain unproven | `IDENTITY_GAP + LEGAL_GAP` |
| CafeF · annual corporate · FPT | `FinanceReport.ashx?Type=1&Symbol=FPT&TotalRow=32&EndDate=2026&ReportType=NAM&Sort=DESC`; no response before bounded timeout | ∅; no date/count claim | No code or label claim; no unit/scale claim | Current direct route is transport-inconclusive; [CafeF data guidance](https://cafef.vn/du-lieu/huong-dan-su-dung.chn) is not a structured-data reuse grant | `TRANSPORT_INCONCLUSIVE + LEGAL_GAP` |
| CafeF · annual corporate · HPG | Same route with `Symbol=HPG`; no response before bounded timeout | ∅; no date/count claim | No code or label claim; no unit/scale claim | Same transport and reuse uncertainty | `TRANSPORT_INCONCLUSIVE + LEGAL_GAP` |
| VNDirect · bank income · VCB | Canonical route with `modelType=102`; HTTP 200 JSON, `code=VCB`, `reportType=ANNUAL`, `modelType=102.0` | 536 line-item rows; 22 distinct dates, 2004-12-31..2025-12-31 | No generic corporate `23110` mapping; bank template is a different accounting surface | Runtime observation only; not a corporate metric mapping | `NOT_APPLICABLE` |
| VNDirect · bank income · ACB | Same bank route with `code=ACB`; same bank model identity | 565 line-item rows; 24 distinct dates, 2002-12-31..2025-12-31 | No generic corporate `23110` mapping; `is_bank=True` is not a corporate-template selector | Runtime observation only; not a corporate metric mapping | `NOT_APPLICABLE` |
| VNDirect · securities foreign templates · SSI | Accepted model 2/102 annual queries returned empty JSON; prior bounded streams 89/90/91 are separate foreign templates in the #204/#205 evidence | No accepted typed fiscal date; foreign-stream dates are not promoted here | No generic `23110`; no statement/unit/entity/consolidation proof for 89/90/91 | No provider permission or semantic template contract | `TEMPLATE_GAP + LEGAL_GAP` |
| VNDirect · securities foreign templates · TCX | Same accepted-model empty outcome; prior 89/90/91 streams remain independently foreign and fail-closed | No accepted typed fiscal date; no absence claim for unaccepted streams | No generic `23110`; FY gaps in a foreign stream cannot govern another stream | Same legal and template gap | `TEMPLATE_GAP + LEGAL_GAP` |
| CafeF · securities annual · SSI/TCX | Prior #204/#205 direct route observations returned annual candidate objects but no response symbol/model discriminator; current parser rejects observed `K` tags | SSI/TCX candidate dates are not qualified annual reports in this API contract | String codes remain in the `cafef` namespace; no exact operating-profit code/scale/scope proof | No structured-data reuse grant; cashflow route is not served | `IDENTITY_GAP + TEMPLATE_GAP + LEGAL_GAP` |
| VNDirect · insurer/special · BVH | Both bounded model-2 and model-102 queries returned HTTP 200 empty JSON envelopes | ∅; no insurer-history absence claim | No generic corporate mapping; `is_bank=False` does not prove the insurance template | No exact insurer template or rights contract | `TEMPLATE_GAP + LEGAL_GAP` |

### 5.1 Per-cell audit fields and role classification

Each matrix row is an independent audit record. The following fields are explicit even when the
provider did not expose them; `not exposed` or `not observed` is a gap, never an inferred value:

| Field | VNDirect observed value | CafeF observed value |
| --- | --- | --- |
| Normalized symbol / statement / cadence | Uppercase requested symbol; `income`; request and accepted rows `ANNUAL` | Uppercase requested symbol; `income`/annual was requested; no accepted row |
| Limit and bounded calls | Public history `limit` not asserted; one direct page with `size=640`; one physical GET per cell, 16 total, no retry | Public history `limit` not asserted; `TotalRow=32`; one physical GET per cell for FPT/HPG, two total, no retry |
| Source role / route | Default primary; `api-finfo.vndirect.com.vn/v4/financial_statements` | Default backup; `cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx` |
| Auth / session / redirect | No key, login, cookie, token, or Referer; no redirect observed in completed responses | No key, login, cookie, token, or Referer was sent; timeout prevents any redirect conclusion |
| MIME / envelope | `application/json`; `data/currentPage/size/totalElements/totalPages` envelope | No fresh MIME or envelope reached; prior reviewed shape is not asserted as a fresh annual result |
| Provider identity / template / scope | Response `code`, `reportType`, and `modelType` observed; entity/consolidation scope not exposed by this route | Response symbol/template/scope not observed in the bounded timeout |
| Dates / line-item count / currency / unit / namespace | Counts and date spans are in the matrix; provider rows expose no currency/unit; `vndirect` namespace; adapter contract is raw VND | No dates, count, currency, unit, or code claim from the timed-out cells; `cafef` namespace remains reserved |
| Candidate code / provider label | `23110` candidate; no provider human label; audited filing label is provenance only | No candidate code or label claim |
| Legal axes | Owner is VNDirect route; no route-specific automation, pacing, storage, caller-return, attribution, or redistribution grant established | Owner is CafeF route; no structured-row automation, pacing, storage, caller-return, attribution, or redistribution grant established |

The role-level classification is separate from each cell's disposition: VNDirect is **transport
capable but unqualified** for generic annual mapping; its accepted model-2/102 queries for SSI, TCX,
and BVH are **empty observations**, not absence proofs. CafeF is the default **backup** and is
**transport-inconclusive/transport-failed for the fresh generic annual cells**; its cashflow route
remains **not served**, and prior SSI/TCX observations remain **identity/template-unqualified**.
No role is promoted by a facade or failover winner, and no empty, failed, or identity-failed role is
used as a historical-absence oracle.

The default source roles remain VNDirect primary and CafeF backup. The generic VNDirect route is
technically capable of returning annual corporate reports, but its candidate mapping is not legally
or semantically qualified. CafeF is a named backup route, not an identity or historical-absence
oracle. Failed VNDirect income and CafeF non-service behavior must not be changed by this source-gap
round.

## 6. Source ownership, access, and legal/runtime posture

| Axis | VNDirect | CafeF |
| --- | --- | --- |
| Owner/route | VNDirect finfo API, `api-finfo.vndirect.com.vn/v4/financial_statements`; named source adapter | CafeF data surface, `cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx`; named source adapter |
| Auth/session | Fresh direct probes used no API key, login, cookie, token, or Referer | Same no-login/no-key probe boundary; timeout is not proof of absence |
| Transport | HTTPS; fresh direct probes returned HTTP 200 JSON on the sampled VNDirect cells; browser UA/IPv4 were required by the runtime/source note | HTTPS route is canonical; fresh annual corporate attempts timed out before a response body |
| MIME/envelope | `application/json`; tall `data/currentPage/size/totalElements/totalPages` envelope; `itemCode` and `numericValue` rows | Prior reviewed shape is JSON with `Data.Count/Value`, `Success`; current corporate probes did not reach envelope parsing; prior responses used `text/plain; charset=utf-8` |
| Rate/pacing | No numeric provider quota or retry contract published; 16 requests are a bounded observation, not a safe production budget | No numeric quota published; robots permission is not a rate or reuse grant |
| Robots/terms | Fresh [API robots/content-signal file](https://api-finfo.vndirect.com.vn/robots.txt) says `search=yes,ai-train=no,use=reference` for the general user-agent and explicitly restricts several named AI crawlers. It does not grant financial-row automation, caching, or redistribution. [VNDIRECT terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) were Cloudflare-challenged in this probe; no route-specific open-data licence was established. | Fresh [CafeF robots](https://cafef.vn/robots.txt) allows `/`, but [CafeF data guidance](https://cafef.vn/du-lieu/huong-dan-su-dung.chn) describes the data as reference information and disclaims use risk. No structured-row redistribution or cache licence was found. |
| Contact/reopen path | [VNDIRECT support](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/) / official terms contact path; request written permission for the exact API route, automation, retention, attribution, and redistribution | Official data contact `dulieu@cafef.vn` and data-guide/footer contact path; request written permission for the exact handler and output use |
| Runtime decision | Fetch-on-demand research only; no bundled rows, cache, bulk export, or caller-facing operating-profit capability | Same conservative posture; no new CafeF mapping |

Public/no-login access is not owner permission. `robots.txt`, a webpage, or a statement filing cannot
be treated as an OSS/API redistribution licence. Until written permission or a clearly applicable
licence covers automated retrieval, retention, attribution, and caller-facing return, the legal gate
is closed.

## 7. Compatibility-safe annual mapping design

If a later source/legal review reopens the candidate, the selector must be typed and conjunctive:

```text
(source namespace, statement=income, provider template/model, entity scope,
 cadence=annual, exact source-namespaced item code, currency=VND,
 unit/scale=raw VND, fiscal-period basis, consolidation scope)
```

The minimum additive representation proposed by the packet is:

```python
@dataclass(frozen=True)
class MetricCodeBinding:
    item_code: str
    period: Period
    is_bank: bool
    model_type: int | None

@dataclass(frozen=True)
class MetricSourceCodes:
    corporate_code: str | None = None
    bank_code: str | None = None
    bindings: tuple[MetricCodeBinding, ...] = ()
```

For the sole technical VNDirect candidate, a future reviewed binding would be
`source=vndirect + statement=income + period=ANNUAL + is_bank=False + model_type=2 +
item_code="23110"`. It must remain a binding, not `corporate_code="23110"`, because the existing
cadence-neutral field would silently enable the quarterly path. The binding must reject duplicate or
ambiguous selectors at catalog validation. A future CafeF code, if ever proven, must be in a
separate `cafef` namespace and cannot be copied into the VNDirect slot.

An annual-qualified binding must not resolve `Period.QUARTER`, YTD, TTM, unknown, or a foreign
provider template. A row with the exact mapped code absent is `MISSING`; an unqualified binding or
template is `BLOCKED`; a corporate-only metric on a bank is `NOT_APPLICABLE`; an explicit numeric
zero from the exact mapped row is available zero. No label, ticker, sector, `is_bank=False`, or
same-looking numeric code may select a mapping.

If this additive binding is later implemented, its trailing defaulted field, constructor behavior,
repr/equality, serialization, public snapshot, DataFrame/lineage surfaces, docs, skill reference,
and CHANGELOG/release decision must be reviewed together. The tagged `v0.2.0` distinction remains
explicit: a future capability cannot be described as already present in that tag.

## 8. Conjunctive reopen criteria

The issue remains source-gap closed unless every criterion passes in one design review:

1. **Owner permission:** VNDirect and/or CafeF grants written permission or a clear licence for the
   exact route, automation, pacing, retries, caching/storage, retention, attribution, caller-facing
   return, redistribution, and commercial use.
2. **Transport and identity:** fresh no-login (or explicitly approved credential) responses have
   exact effective host/path, strict MIME/envelope, requested symbol, `statement=income`,
   annual cadence, provider template/model, entity/consolidation scope, and no redirect/challenge
   identity substitution.
3. **Generic VNDirect evidence:** at least two annual periods and two issuers with different business
   profiles prove the same `model_type=2`, exact item code `23110`, raw VND scale, sign, row-30
   concept, and consolidated/separate scope against official audited filings.
4. **CafeF evidence:** at least two issuers on one exact annual template expose response-backed symbol
   or independently verified identity, annual marker, exact source-namespaced operating-profit code,
   unit/scale, scope, and two-period accounting cross-check. No guessed string code is allowed.
5. **Special templates:** bank, securities `89/90/91`, insurer, and any other special template are
   classified independently. No foreign stream inherits generic corporate mapping; no bank
   `NOT_APPLICABLE` change occurs without exact same-concept evidence and explicit API review.
6. **Cadence/history:** provider fiscal dates are annual flow periods, newest-first and unique; no
   TTM/YTD/quarter relabeling, adjacent-period construction, fill, or 2016–2025 completeness promise.
   Missing years remain missing/coverage facts only after a qualified response family.
7. **Runtime budget:** direct and chain paths have deterministic bounded logical/physical calls,
   no hidden retries, and a documented conservative pacing rule. No provider SLA is inferred from
   response success.
8. **Metric contract:** exactly 26 IDs, `RAW_MAPPED`, source namespace, `MetricInput` lineage,
   bank `NOT_APPLICABLE`, current blocked quarterly behavior, direct/chain parity, source
   precedence, per-statement diagnostics, newest-first, and `limit` behavior remain compatible.
9. **No ratios/no proxy:** exactly zero `StatementType.RATIOS` calls; no provider ratio, formula,
   EBITDA/EBIT/gross/PBT/net-income/cashflow substitute, or VN30 behavior.
10. **Bounded diagnostics:** reasons, warnings, `MetricValue`, `MetricReport`, DataFrame attrs,
    reprs, and raised messages contain no URL/query, provider text, raw response, exception, secret,
    live value, or failed-attempt trail.
11. **Reviewer transition:** exact design PASS precedes a separate RED-first synthetic test commit;
    no source-gap document authorizes TDD or production code.

## 9. Future-only RED/release contract

There is intentionally no RED commit in this source-gap range. If and only if the above gate later
passes, synthetic offline tests must cover:

- exact annual `23110` binding for FPT/HPG-like fabricated generic templates, two periods and two
  issuers, raw VND lineage, fiscal dates, source namespace, and explicit zero;
- `corporate_code=None`/unqualified map `BLOCKED`, qualified absent line `MISSING`, bank
  `NOT_APPLICABLE`, wrong `14000`, wrong `23100`/`23500`/`23800`, wrong namespace, wrong
  statement, wrong model, wrong entity, wrong unit/scale, wrong scope, and foreign 89/90/91;
- annual binding requested quarterly/YTD/TTM/unknown, malformed/absent/bool/fractional/padded
  model ids, response/report template mismatch, symbol/provider-symbol mismatch, duplicate dates,
  incomplete pagination, empty responses, and transport failures;
- direct `source=` and explicit/default `sources=` parity, incapable-role zero-call skips,
  source precedence, recoverable partial coverage, all-empty `EmptyData`, newest-first order, and
  `limit`;
- exactly zero ratio calls and unchanged income/balance/cashflow call counts;
- malicious/long labels, source names, URLs, response bodies, and exceptions fail sanitization;
- additive binding public snapshots, constructor/repr/equality/serialization, DataFrame columns/attrs,
  docs/API/skill/CHANGELOG/release decision, import/version checks, blacklist/secret scans,
  `git diff --check`, full offline tests, and isolated sdist/wheel build.

All fixtures must use visibly fabricated symbols, dates, labels, and values. No provider payload or
live statement value may enter tests, docs examples, build artifacts, or history.

## 10. Final disposition

VNDirect exposes a strong technical generic-corporate candidate: model 2, annual `fiscalDate`,
response symbol, and candidate code `23110` that cross-checks to the audited row-30 operating
result for two business profiles and two annual periods. That is not enough to ship: the provider
response lacks a semantic line label/unit field and the route has no explicit automated-use,
retention, or redistribution grant.

CafeF remains unresolved for the requested generic cells because the fresh direct route timed out
and prior special-template observations lack response symbol/model/scale proof. Banks remain
`NOT_APPLICABLE`; securities foreign streams and insurer templates remain unqualified; quarterly
remains the #205 source gap; ratios remain zero-call; and the tagged `v0.2.0` distinction is
preserved.

Therefore #208 is **SOURCE-GAP CLOSURE**. The two requested artifacts may be reviewed and, if
approved, published as a no-capability resolution. No annual operating-profit capability, RED tests,
production code, push, or issue closure is authorized by this report.

## Sources

- [VNDirect annual financial-statements route](https://api-finfo.vndirect.com.vn/v4/financial_statements)
- [VNDirect API robots/content signals](https://api-finfo.vndirect.com.vn/robots.txt)
- [VNDIRECT terms of use](https://www.vndirect.com.vn/dieu-khoan-su-dung/)
- [VNDIRECT support/contact](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/)
- [CafeF FinanceReport handler](https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx)
- [CafeF data guidance](https://cafef.vn/du-lieu/huong-dan-su-dung.chn)
- [CafeF robots.txt](https://cafef.vn/robots.txt)
- [FPT 2025 annual report](https://fpt.com/-/media/project/fpt-corporation/fpt/ir/information-disclosures/year-report/2026/april/bctn-fpt-2025.pdf)
- [FPT audited consolidated 2024 report](https://fpt.com/-/media/project/fpt-corporation/fpt/ir/information-disclosures/year-report/2025/january/20250124---fpt---bctc-hop-nhat-quy-4-nam-2024.pdf)
- [Hòa Phát 2025 consolidated report](https://file.hoaphat.com.vn/hoaphat-com-vn/2026/01/20260130-hpg-bao-cao-tai-chinh-hop-nhat-va-giai-trinh-q4-2025.pdf)
- [Hòa Phát 2024 annual report](https://file.hoaphat.com.vn/hoaphat-com-vn/2025/04/bao-cao-thuong-nien-hpg-2024.pdf)
- [Previously reviewed #204 SSI/TCX source vetting](2026-08-22-fundamentals-ssi-tcx-source-vetting.md)
- [Previously reviewed #205 quarterly source vetting](2026-08-22-quarterly-operating-profit-margin-source-vetting.md)
- [Existing VNDirect source note](../sources/fundamentals-vndirect.md)
- [Existing CafeF source note](../sources/fundamentals-cafef.md)
