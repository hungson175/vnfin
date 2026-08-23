# #208 design note — canonical annual operating profit

**Packet:** tasks/208-annual-operating-profit-spec.md (reviewer 3699ae5)
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

VNDirect generic corporate model 2 exposes the strongest technical candidate: itemCode=23110
matches the audited row-30 operating result for two issuers and two annual periods. It is still a
candidate because the provider row has no semantic line label or unit field and no explicit
automation, retention, caching, or caller-facing redistribution grant was found. CafeF is
transport-inconclusive for the fresh generic probes and its previously observed special-template
rows lack sufficient identity/template/scale proof.

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

The current technical candidate is:

~~~text
source       = vndirect
statement   = income
template    = generic corporate modelType=2
entity      = is_bank=False
cadence     = Period.ANNUAL / reportType=ANNUAL
item_code   = "23110"
concept     = audited row 30, Lợi nhuận thuần từ hoạt động kinh doanh
unit        = raw VND, only after the source/filing scale gate passes
~~~

23110 is a candidate binding, not a current catalog value. The provider response exposes numeric
itemCode and numericValue, but no human line label or explicit unit. The label is provenance from
the official audited filing cross-check only; it is never a selector.

The following are explicit negatives:

| Candidate | Why it cannot resolve operating_profit |
| --- | --- |
| 23100 | Generic corporate gross profit / row 20, not row 30 |
| 23110 | Candidate only; exact tuple and rights still gate qualification |
| 23500 | Generic corporate profit attributable to non-controlling interests |
| 23800 | Generic corporate profit before tax / row 50 |
| 14000 | Owners' equity in the balance template; the old shortcut is disproved |
| 23110 in bank, securities, insurer, foreign, or mismatched template | Numeric equality cannot cross templates |
| B02-CTCK row 70 formula | Filing cross-check only; a RAW_MAPPED runtime value cannot be calculated |
| CafeF string labels/codes | Must be independently qualified in the cafef namespace; none is qualified here |

A generic mapping requires at least two annual periods and two issuers with different business
profiles. The current cross-check is FPT (technology/services) and HPG (steel/manufacturing) for
2024 and 2025. VNM is a third technical observation but is not counted as an independently retained
filing cross-check in this round.

## 3. Source/template disposition

The complete sanitized matrix is in the research note. The design disposition is:

| Source/template cell | Current evidence | API disposition |
| --- | --- | --- |
| VNDirect generic corporate model 2, FPT/HPG | HTTP 200 JSON; response symbol, ANNUAL, model 2; 23110 candidate across observed dates; audited row-30 cross-check | LEGAL_GAP; no TDD mapping |
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
5. use the successful report's exact source, statement_type, period, model_type, is_bank,
   provider_symbol, currency, and fiscal date as lineage;
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

If this additive field is implemented later, public snapshot field order, trailing constructor
compatibility, repr/equality, serialization, DataFrame lineage/attrs, docs, skill reference,
CHANGELOG.md, and release/version decisions must be reviewed in one change. No such API change
is authorized here.

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

## 7. Conjunctive reopen gate

The source gap stays closed if any single item fails. Reopen requires one design review to prove:

1. written owner permission or a clear licence for exact route automation, pacing, retries,
   caching/storage, retention, attribution, caller-facing return, redistribution, and commercial use;
2. fresh strict transport with canonical host/path, exact MIME/envelope, no redirect/challenge
   identity substitution, and a documented conservative rate/pacing policy;
3. response-backed requested symbol, statement income, annual cadence, provider template/model,
   entity/consolidation scope, fiscal date, raw-VND unit/scale, and exact source-namespaced code;
4. generic VNDirect 23110 identity cross-checked against two annual periods and two different
   issuers/business profiles, including sign, full-dong scale, consolidated/separate scope, and the
   row-30 concept in official audited filings;
5. CafeF independently proves two issuers/two annual periods, response identity or a documented
   identity envelope, annual marker, exact string code, unit/scale, scope, and accounting concept;
6. every current default-chain role is classified independently as capable, unqualified, not served,
   empty, transport-failed, or identity-failed, with no historical-absence inference;
7. foreign VNDirect 89/90/91, securities templates, bank templates, insurer/special templates, and
   any future CafeF template are independently qualified or remain fail-closed;
8. the typed binding selector keeps corporate_code=None, blocks quarterly/YTD/TTM/unknown,
   preserves bank NOT_APPLICABLE, and rejects wrong namespace/code/template/entity/scope;
9. fiscal dates, maximum honest history, missing-date semantics, newest-first order, and bounded
   source/page/retry calls are proven without hidden retries or fabricated coverage;
10. exactly 26 metric IDs, RAW_MAPPED, public lineage, source precedence, direct/chain parity,
    per-statement diagnostics, limit, zero ratio calls, and tagged-v0.2.0 distinction remain
    compatible;
11. public snapshots, constructors, repr/equality, serialization, DataFrame columns/attrs, docs,
    skills, CHANGELOG.md, release/version decision, blacklist/secret scans, and error
    sanitization are reviewed together; and
12. a new exact-SHA design PASS authorizes a separate RED-first synthetic test transition. This
    source-gap commit never authorizes tests or production code.

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

- old 14000 shortcut; same label with wrong code; 23100, 23500, and 23800; same code in wrong
  source, statement, model/template, entity, cadence, currency, unit, scale, or consolidation scope;
- annual-qualified binding requested quarterly/YTD/TTM/unknown response mismatches fail closed;
- bank fixture remains exact NOT_APPLICABLE; securities/insurance/foreign templates never inherit
  generic corporate codes;
- VNDirect 89/90/91, unknown/missing/bool/fractional/padded model ids, response/report template
  mismatch, cross-symbol/provider-symbol mismatch, and mixed-template rows fail closed;
- qualified mapping but absent line is MISSING; unqualified map is BLOCKED; explicit numeric zero is
  available zero; null/blank/string/bool/non-finite/unsafe-magnitude values fail validation;
- duplicate item code/date, duplicate/conflicting fiscal periods, out-of-order/truncated
  pagination, wrong identity, malformed envelope, partial page/count reconciliation, empty/failure
  outcomes never fabricate coverage; and
- malicious/long source names, labels, URLs, response text, and exception strings are fully
  sanitized on direct and chain paths.

### 8.3 API, calls, documentation, and release

- exactly 26 catalog ids; operating_profit stays RAW_MAPPED; no proxy/formula/ratio/signal or
  VN30 helper and no changed derived formulas;
- existing signatures/exports, source precedence, empty effective-chain behavior, incapable-role
  zero-call skips, all-empty EmptyData, per-statement coverage, DataFrame columns/attrs,
  dataclass construction, equality/repr, and public snapshots remain compatible;
- exactly zero StatementType.RATIOS calls; income/balance/cashflow fetch counts and
  ratio_status=NOT_REQUESTED remain unchanged;
- any shipped capability updates fundamentals design/API/tutorial docs, skills/vnfin reference,
  public API contracts, and CHANGELOG.md together, with fabricated examples and exact
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

The two requested documents are ready for exact-SHA design review. This is SOURCE-GAP CLOSURE:
no RED tests, production code, push, or issue closure is authorized until a later explicit design
PASS and transition.
