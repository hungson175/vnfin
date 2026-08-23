# #208 design note — canonical annual operating profit

**Packet:** reviewer-repo packet `/home/hungson175/tools/vnfin-oss-reviewer/tasks/208-annual-operating-profit-spec.md`
at reviewer commit `3699ae52c03bfa9be52aee0d54ae669d8a8071db` (not a builder-repo relative path)
**Design phase:** source/design gate only
**Disposition:** **SOURCE-GAP CLOSURE**
**Production status:** no RED tests, production code, new mapping, push, or issue closure.

The source evidence is in
[docs/research/2026-08-23-annual-operating-profit-source-vetting.md](../docs/research/2026-08-23-annual-operating-profit-source-vetting.md).
This note binds the future selector, accounting identity, API compatibility, diagnostics, and reopen
contract without claiming that the capability exists.

## 1. Decision and hard boundary

No current source/template cell passes every required axis: response-backed symbol and template,
exact annual accounting identity, source-namespaced item code, entity/consolidation scope, raw-VND
unit/scale, legal/runtime permission, bounded request policy, and public compatibility.

VNDirect generic corporate model 2 exposes the strongest structural candidate: itemCode=23110
appears across two issuers and multiple annual periods. No reproducible audited four-cell receipt is
accepted in this commit. The provider row has no semantic line label, unit, entity, or
consolidation-scope field, and no explicit automation, retention, caching, or caller-facing
redistribution grant was found. CafeF is transport-inconclusive for the fresh generic probes and
its previously observed special-template rows lack sufficient identity/template/scale proof.

Therefore:

- MetricId.OPERATING_PROFIT remains exactly one of the existing 26 IDs;
- its kind remains RAW_MAPPED, not DERIVED, PROVIDER_NATIVE, a ratio, or a formula;
- codes_by_source["vndirect"].corporate_code remains None, so current corporate output stays
  BLOCKED;
- AppliesTo.CORPORATE and the bank NOT_APPLICABLE result remain unchanged;
- the #205 quarterly source gap remains closed and an annual code must never resolve a quarter;
- the default source roles and source precedence remain unchanged;
- metrics fetch income, balance, and cashflow only: StatementType.RATIOS calls remain zero and
  ratio_status=NOT_REQUESTED;
- no VN30 universe, breadth, ranking, session, signal, screener, or advice behavior is in scope;
- the annotated v0.2.0 tag predates the metrics API. No tagged-v0.2.0 capability claim is made.

This is a source-gap resolution, not a partial annual release. A later design PASS would be a
separate transition before RED-first TDD.

## 2. Exact operating-profit identity

For a qualified generic corporate income template, operating_profit is the provider-observed
row-30 concept **Lợi nhuận thuần từ hoạt động kinh doanh**, not any adjacent label or formula
substitute:

~~~text
row 30 = row 20 + row 21 - row 22 + row 24 - row 25 - row 26
~~~

The same issuer and fiscal date must prove the complete identity tuple:

~~~text
(source namespace, statement=income, provider template/model, entity scope,
 cadence=annual, exact source-namespaced item code, currency=VND,
 unit/scale=raw VND, fiscal-period basis, consolidation scope)
~~~

The current structural candidate is:

~~~text
source       = vndirect
statement   = income
template    = generic corporate modelType=2
entity      = is_bank=False
cadence     = Period.ANNUAL / reportType=ANNUAL
item_code   = "23110"
concept     = candidate row 30, Lợi nhuận thuần từ hoạt động kinh doanh
unit        = raw VND, only after the source/filing scale gate passes
~~~

23110 is a candidate binding, not a current catalog value. The provider response exposes numeric
itemCode and numericValue, but no human line label, explicit unit, entity scope, or consolidation
scope. No audited four-cell comparison receipt is accepted in this source-gap round; any filing
label remains unverified provenance, never a selector.

The following are explicit negatives:

| Candidate | Why it cannot resolve operating_profit |
| --- | --- |
| 23100 | Generic corporate gross profit / row 20, not row 30 |
| 23110 | Candidate only; exact tuple and rights still gate qualification |
| 23500 | Generic corporate profit attributable to non-controlling interests |
| 23800 | Generic corporate profit before tax / row 50 |
| 14000 in corporate model 1 | Owners' equity in the corporate balance template; the old shortcut is disproved |
| 14000 in bank model 101 | Owners' equity in the bank balance template; the old shortcut is disproved |
| 23110 in bank, securities, insurer, foreign, or mismatched template | Numeric equality cannot cross templates |
| B02-CTCK row 70 formula | Filing cross-check only; a RAW_MAPPED runtime value cannot be calculated |
| CafeF string labels/codes | Must be independently qualified in the cafef namespace; none is qualified here |

A generic mapping requires at least two annual periods and two issuers with different business
profiles. The current structural observation set is FPT (technology/services) and HPG
(steel/manufacturing) for 2024 and 2025, but no audited four-cell filing receipt is accepted in
this round. VNM is a third technical observation and also has no accepted filing receipt.

## 3. Source/template disposition

The complete sanitized matrix is in the research note. The design disposition is:

| Source/template cell | Current evidence | API disposition |
| --- | --- | --- |
| VNDirect generic corporate model 2, FPT/HPG | HTTP 200 JSON; response symbol, ANNUAL, model 2; 23110 structural candidate across observed dates; no accepted audited four-cell receipt; provider unit/entity/scope unresolved | IDENTITY_GAP + LEGAL_GAP; no TDD mapping |
| VNDirect generic corporate model 2, VNM | Same technical candidate pattern; no retained second filing cross-check | IDENTITY_GAP + LEGAL_GAP |
| CafeF annual corporate, FPT/HPG | Fresh direct annual requests timed out before envelope parsing | TRANSPORT_INCONCLUSIVE + LEGAL_GAP |
| VNDirect bank model 102, VCB/ACB | Response-backed bank templates and annual dates; no corporate operating-profit mapping | NOT_APPLICABLE |
| VNDirect securities SSI/TCX | Accepted 2/102 queries empty; 89/90/91 foreign streams remain separate and unqualified | TEMPLATE_GAP + LEGAL_GAP |
| CafeF securities SSI/TCX | Prior observations have no response symbol/model and unsupported annual tags; no exact target code | IDENTITY_GAP + TEMPLATE_GAP + LEGAL_GAP |
| VNDirect insurer/special BVH | Accepted corporate/bank model probes empty; no insurer template proof | TEMPLATE_GAP + LEGAL_GAP |

These are not coverage percentages. An empty or timed-out route never proves historical absence or
authorizes COVERAGE_GAP. COVERAGE_GAP is available only after a qualified source response family,
complete bounded retrieval, and provider-backed missing-date semantics.

The research matrix is also the per-cell audit ledger. Every row binds normalized requested symbol,
`statement=income`, `cadence=annual`, the requested public `limit` posture, source role, canonical
route, auth/session/redirect result, exact MIME/envelope result, bounded logical/physical calls,
response-backed provider symbol, statement/cadence marker, template/model, entity/consolidation
scope, fiscal dates, item count, currency, raw unit/scale, source namespace, candidate code and
provider label (label as provenance only), observed newest/oldest dates/count, and separate
ownership, automation, pacing, caching/storage, caller-return, attribution, and redistribution
rights. `not exposed`, `not observed`, timeout, empty, and identity failure are recorded as gaps or
typed dispositions; none is promoted to coverage or historical absence. The bounded observations
were one direct VNDirect page per cell (`size=640`, 16 total GETs, no retry) and one CafeF request
per fresh generic cell (`TotalRow=32`, two total GETs, no retry); these are evidence budgets, not
provider SLAs or public history limits.

Current default-role classification is explicit: VNDirect is transport-capable but unqualified for
the generic annual mapping; accepted model-filter cells for SSI, TCX, and BVH are empty observations.
CafeF is the backup and is transport-inconclusive/transport-failed for the fresh generic annual
cells, not served for cashflow, and identity/template-unqualified for the prior SSI/TCX observations.
Neither role is an absence oracle, and no facade/failover winner supplies identity or retention proof.
The research note's §3.1 enumerates all 16 VNDirect physical requests, including the five empty
cross-template negatives omitted by the original matrix; §6 carries the separate finite rights
ledger for each source/template family.

## 4. Compatibility-safe typed selector

The existing MetricSourceCodes.corporate_code is cadence-neutral and cannot carry this annual
candidate. If a later source/legal gate passes, add one trailing defaulted immutable binding rather
than populating that field:

~~~python
@dataclass(frozen=True)
class MetricCodeBinding:
    item_code: str
    period: Period
    is_bank: bool
    model_type: int | None

@dataclass(frozen=True)
class MetricSourceCodes:
    corporate_code: str | None = None  # preserve existing field semantics
    bank_code: str | None = None
    bindings: tuple[MetricCodeBinding, ...] = ()
~~~

The binding does not itself expose the promised provider identity. A future additive/defaulted
lineage extension must preserve existing positional construction while making the audit fields
public:

~~~python
@dataclass(frozen=True)
class MetricLineage:
    provider_symbol: str | None = None
    provider_template: str | None = None
    model_type: int | None = None
    entity_scope: str | None = None
    currency: str | None = None
    unit_scale: str | None = None
    consolidation_scope: str | None = None
    provider_tags_verified: bool = False

@dataclass(frozen=True)
class MetricInput:
    # Existing fields remain in their current order.
    statement: StatementType
    item_code: str
    value: float
    value_unit: str
    fiscal_date: date
    source: str
    name: str
    lineage: MetricLineage = MetricLineage()
~~~

For a qualified annual mapping, `provider_tags_verified=True` requires response-backed requested
symbol, exact `reportType=ANNUAL`, exact provider model/template, and any exposed entity and
consolidation scope. VNDirect requires present `code`, `reportType`, and `modelType`; absent tags
cannot be filled from request arguments. Request-derived period/model/provider-symbol metadata is
not identity evidence. CafeF requires an equivalent response identity and annual marker or remains
an identity gap. Missing unit, scale, entity, or consolidation scope leaves the lineage field unset
and the binding `BLOCKED`.

The future VNDirect binding is exactly:

~~~text
source=vndirect
statement=income
period=ANNUAL
is_bank=False
model_type=2
item_code="23110"
~~~

The runtime selector must:

1. validate source role, statement, provider template/model, entity taxonomy, and cadence before
   looking up the item code;
2. require exact Period.ANNUAL and provider reportType=ANNUAL;
3. canonicalize the provider numeric code to a non-padded string only after strict finite,
   integral, non-boolean validation;
4. reject duplicate or ambiguous bindings at catalog validation;
5. require response-backed `MetricLineage` with `provider_tags_verified=True`, carrying exact source,
   statement, provider template/model, entity scope, provider symbol, currency, unit/scale,
   consolidation scope, and fiscal date;
6. use LineItem.name only as provenance, never identity;
7. return BLOCKED for an unqualified/mismatched template or binding, MISSING only when a
   qualified exact code is absent from an otherwise valid report, NOT_APPLICABLE for bank
   entities, and available numeric zero only when the exact mapped line returns numeric zero; and
8. never fall back from a missing/malformed/foreign template to generic corporate, by ticker, label,
   sector, is_bank=False, or numeric-code resemblance.

A future CafeF binding must be stored only under codes_by_source["cafef"]. CafeF has no
response-backed symbol/model/template/scale proof for this target in the current round; no string
code is proposed. A special-template binding requires an additive typed template identity when the
provider's existing model_type=None cannot audit the template. Template identity may not hide in
a warning or free-form error.

If these additive fields are implemented later, public snapshot field order, trailing constructor
compatibility, repr/equality, serialization, `MetricReport`/`MetricValue.inputs` snapshots,
DataFrame lineage columns/attrs, and derived-input behavior must be reviewed together. Derived
metrics preserve each input's lineage and never synthesize or copy provider identity; blocked or
unverified inputs keep existing derived-input `BLOCKED` behavior. Coverage's mapped-code set must
flatten reviewed `bindings[*].item_code` alongside legacy corporate/bank slots, with RED tests
proving reviewed bindings are counted and unqualified bindings are not silently mapped. Docs,
source docs, skill reference, CHANGELOG.md, and release/version decisions are part of that future
change. No such API change is authorized here.

## 5. Annual history and source-call contract

A future annual result must satisfy all of these:

- period="annual" means one provider-identified annual flow period; never TTM, YTD, quarter,
  unknown, or an annualized value;
- MetricInput.fiscal_date is the provider fiscal date, with source, exact code, provider name,
  raw value/unit, template/model, and entity/scope lineage from the same income report;
- results are provider-observed, unique, newest first, within limit, and may contain only the
  maximum honest history; no 2016–2025 completeness promise is made;
- non-calendar fiscal year ends remain intact when the provider exposes them;
- no fill, interpolation, adjacent-period construction, cross-date join, cross-symbol join,
  consolidated/separate join, or cross-source stitching is allowed;
- fetched_at_utc remains retrieval time only and cannot support a strict-prior publication claim;
- direct source= and single-role/default sources= paths produce identical values, availability,
  lineage, dates, warnings, and bounded diagnostics;
- incapable roles are skipped with zero calls; a failed capable primary may reach only a separately
  qualified same-semantic backup; and
- existing income/balance/cashflow request counts and source precedence remain unchanged. No ratio
  call is added.

The future source scheduler must expose a deterministic logical/physical budget per source/template,
with no hidden HTTP-library retries, unbounded pagination, concurrency duplicates, or response-body
trails. The current observation of one-page VNDirect model-2 responses is not a provider SLA or a
production budget. CafeF's TotalRow is a request bound, not a legal or completeness guarantee.

The current VNDirect parser remains compatible with absent response tags and request-derived report
metadata; that existing behavior cannot qualify this annual candidate. The mandatory-present
response-tag/trust rule and `MetricLineage` extension are future-only design requirements, not
implementation authorization in this commit.

## 6. Diagnostics and no-false-absence contract

The current public availability semantics remain the authority:

| Condition | Required outcome |
| --- | --- |
| Corporate metric has no verified source/template binding | MetricAvailability.BLOCKED; preserve the current bounded unmapped-code reason |
| Exact qualified line is absent from a valid report | MetricAvailability.MISSING; never call an unqualified line missing |
| Bank report for this corporate-only metric | MetricAvailability.NOT_APPLICABLE |
| Exact qualified line returns numeric zero | AVAILABLE with value zero |
| Empty/failing/unqualified source or template | BLOCKED, source error, or typed statement status as appropriate; never fake zero |
| Derived input receives this blocked metric | Existing derived-input block semantics; no formula substitution |

Public reason strings and warnings remain bounded and trail-free. They may contain only stable
catalog/source/statement/entity/code identifiers allowed by the existing API contract, never a URL,
query, response body, raw exception, provider free text, credential, cookie, live value, or
failed-source attempt trail. The source matrix disposition tokens are design evidence, not a new
unreviewed public error vocabulary.

Per-statement provenance, recoverable partial coverage, all-empty EmptyData, direct/chain parity,
newest-first ordering, limit, and the default source precedence remain unchanged. CafeF cashflow
remains NOT_SERVED; no empty cashflow diagnostic may become historical absence.

## 7. Provider-conditional reopen gate and docs-only close transition

The source gap stays closed. A later `QUALIFIED FOR TDD` or `PARTIAL` disposition requires **at
least one** complete provider/template binding to pass every applicable gate; VNDirect and CafeF do
not have to qualify together. If one provider qualifies, every other provider/role remains
independently classified and fail-closed. A proposed failover backup must pass its own complete
same-semantic gate, but an unqualified backup is not required merely to reopen a primary.

For each provider/template proposed for enablement, all of these are conjunctive:

1. written owner permission or a clear licence for that exact route's automation, pacing, retries,
   caching/storage, retention, attribution, caller-facing return, redistribution, and commercial use;
2. fresh strict transport with canonical host/path, exact MIME/envelope, response-backed requested
   symbol, income statement, annual cadence, provider template/model, entity/consolidation scope,
   and no redirect/challenge identity substitution; required tags must be present, not request-derived;
3. the same issuer and fiscal date prove sign, raw-VND scale, entity/consolidation scope, and the
   canonical row-30 concept in an exact official audited statement, with a sanitized four-cell
   receipt (issuer, fiscal date, consolidated/separate, sign, scale, exact-match result) and no live
   values;
4. a generic VNDirect or CafeF binding proves at least two annual periods and two issuers with
   different business profiles on one exact template. VNDirect requires exact model 2/23110;
   CafeF requires response identity, annual marker, exact `cafef` namespace code, unit/scale, scope,
   and the same two-period cross-check. No guessed string code is allowed;
5. fiscal dates/history and runtime budgets are deterministic and bounded: no TTM/YTD/quarter
   relabeling, fill, adjacent-period construction, hidden retries, or completeness promise;
6. exactly 26 IDs, `RAW_MAPPED`, response-backed `MetricLineage`, source namespace, bank
   `NOT_APPLICABLE`, blocked quarterly behavior, direct/chain parity, source precedence,
   per-statement diagnostics, newest-first, `limit`, zero ratio calls, and public compatibility
   surfaces remain intact; and
7. public reasons/warnings/reports/DataFrame attrs/reprs/messages remain bounded and trail-free.

All other roles—bank, securities `89/90/91`, insurer/special templates, and any provider that does
not pass its own gate—remain `NOT_APPLICABLE`, `TEMPLATE_GAP`, `IDENTITY_GAP`,
`TRANSPORT_INCONCLUSIVE`, `NOT_SERVED`, or another explicit fail-closed disposition. Empty, timeout,
failed, or identity-failed roles never establish historical absence.

When the chosen disposition remains `SOURCE-GAP CLOSURE`, an exact design PASS authorizes a
docs-only publication/closure transition, not TDD:

1. rerun merged-tree gates against the exact approved docs anchor;
2. push only that approved anchor, verify remote `HEAD`, ancestry, and research/design/backlog paths;
3. post the clean no-capability resolution preserving the empty chain and reopen criteria;
4. close #208 and re-read it as `CLOSED/COMPLETED`; and
5. keep RED tests, production code, and annual capability paused until a later fresh design PASS
   authorizes a separate RED-first TDD transition.

## 8. Future-only RED and release matrix

There is intentionally no RED commit in this design range. If and only if the reopen gate passes,
the next commit must be RED-first and all fixtures must be offline with visibly fabricated symbols,
dates, labels, and values.

### 8.1 Positive qualified-cell rows

- exact annual source/template/item-code resolution returns raw-VND operating_profit with exact
  fiscal date and complete MetricInput lineage;
- at least two fabricated periods and two issuer fixtures exist for each generic-template binding;
- maximum-history and shorter-limit results are newest-first, unique, deterministic, and use only
  existing bounded statement calls;
- direct source= and single-role sources= paths have identical value, availability, lineage,
  statement provenance, and warnings; and
- a recoverable capable primary may fail over only to a separately qualified same-semantic backup,
  without namespace or template mixing.

### 8.2 Identity, applicability, cadence, and value negatives

- old 14000 shortcut in both corporate model 1 and bank model 101; same label with wrong code;
  23100, 23500, and 23800; same code in wrong
  source, statement, model/template, entity, cadence, currency, unit, scale, or consolidation scope;
- annual-qualified binding requested quarterly/YTD/TTM/unknown response mismatches fail closed;
- bank fixture remains exact NOT_APPLICABLE; securities/insurance/foreign templates never inherit
  generic corporate codes;
- VNDirect 89/90/91, unknown/missing/bool/fractional/padded model ids, absent or request-derived
  `reportType`/`modelType`/provider-symbol tags, response/report template mismatch,
  cross-symbol/provider-symbol mismatch, and mixed-template rows fail closed;
- qualified mapping but absent line is MISSING; unqualified map is BLOCKED; explicit numeric zero is
  available zero; null/blank/string/bool/non-finite/unsafe-magnitude values fail validation;
- duplicate item code/date, duplicate/conflicting fiscal periods, out-of-order/truncated
  pagination, wrong identity, malformed envelope, partial page/count reconciliation, empty/failure
  outcomes never fabricate coverage; and
- required provider tags are present and trusted rather than request-derived; missing tags leave
  `provider_tags_verified=False` and fail closed, while response-backed symbol/template/model/entity/
  currency/unit/scale/consolidation fields round-trip through `MetricLineage`; and
- malicious/long source names, labels, URLs, response text, and exception strings are fully
  sanitized on direct and chain paths.

### 8.3 API, calls, documentation, and release

- exactly 26 catalog ids; operating_profit stays RAW_MAPPED; no proxy/formula/ratio/signal or
  VN30 helper and no changed derived formulas;
- existing signatures/exports, source precedence, empty effective-chain behavior, incapable-role
  zero-call skips, all-empty EmptyData, per-statement coverage, DataFrame columns/attrs,
  dataclass construction, equality/repr, public snapshots, derived-input lineage, and binding-aware
  mapped-code coverage diagnostics remain compatible;
- exactly zero StatementType.RATIOS calls; income/balance/cashflow fetch counts and
  ratio_status=NOT_REQUESTED remain unchanged;
- any shipped capability updates fundamentals design/API/tutorial docs, both applicable source docs
  (`docs/sources/fundamentals-vndirect.md` and `docs/sources/fundamentals-cafef.md`), skills/vnfin
  reference, public API contracts, and CHANGELOG.md together, with fabricated examples and exact
  template/annual/coverage limits;
- focused fundamentals/metrics/failover/docs/public-API tests, full offline suite,
  git diff --check, blacklist/secret scans, import/version checks, and isolated sdist/wheel build
  pass on the merged tree; and
- no live rates/rows, raw provider responses, screenshots, credentials, cookies, or prohibited
  material enters fixtures, docs examples, build artifacts, or history.

## 9. Final result

The current public behavior stays honest: 26 metric IDs, operating profit RAW_MAPPED and BLOCKED,
banks NOT_APPLICABLE, quarterly source gap preserved, zero ratio calls, and no tagged-v0.2.0
back-claim.

The two requested documents are ready for exact-SHA re-review. This correction remains
SOURCE-GAP CLOSURE: no RED tests, production code, push, or issue closure is authorized in the
current builder step. After exact design PASS, only the docs-only publication/resolution/close
transition in §7 is authorized; a later fresh design PASS remains mandatory before RED-first TDD.
