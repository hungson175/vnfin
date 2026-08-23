# #220 design note — annual ROE ratio history

**Date:** 2026-08-23 (UTC+7)
**Packet:** `tasks/220-annual-roe-ratio-history-spec.md` at
`314cd53b4a7f3a0c36f6a1bb45efed2611733f4a`
**Phase:** `SOURCE_DESIGN` / docs-only
**Disposition:** **SOURCE-GAP CLOSURE**
**Current source chain:** empty
**Implementation:** no ROE mapping, cadence change, parser, failover, model, RED, API, or runtime
capability.

The companion evidence is
[`docs/research/2026-08-23-annual-roe-ratio-history-source-vetting.md`](../docs/research/2026-08-23-annual-roe-ratio-history-source-vetting.md).
This note binds the design gate only; it authorizes no implementation.

## 1. Clean-room and current boundary

`docs/vnstock-blacklist.md` was read before this task. The required exclusion was applied:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited or derivative source, reporter artifact, copied dataset, unofficial endpoint map,
login/session bypass, paid feed, proxy, raw value, body, digest, cookie, header, credential, or
query-bearing URL is retained.

The existing public call remains unchanged:

```python
vnfin.fundamentals.client().get_financials(
    symbol, StatementType.RATIOS, Period.ANNUAL, limit=8
)
```

Current VNDirect and CafeF ratio reports intentionally return `Period.UNKNOWN`. The requested
annual period must never be echoed unless a response-backed annual fiscal identity is proven. The
26-metric API continues to make zero ratio calls and keeps ROE/ROA/ROIC blocked. No ROE is derived,
scaled, stitched, or substituted.

## 2. Candidate decision

| Unit | Evidence | Blocking seam | Decision |
|---|---|---|---|
| VNDirect `/v4/ratios` corporate/bank | 200 JSON, symbol/`ratioCode`/`itemCode`/`reportDate` shape | no annual marker, fiscal-date/definition/scale/revision/reuse proof | `SOURCE-GAP` |
| CafeF ratio AJAX corporate/bank | 200 JSON envelope with period fields | `ReportType=NAM` is request-side; nullable/absent cadence tags and current `Period.UNKNOWN` remain | `SOURCE-GAP` |
| SSI FastConnect/iBoard | official docs and archive | API key/secret/account access; own-use terms restrict third-party publication/reproduction | `SOURCE-GAP` |
| TCBS/TCInvest | official UI/docs | dashboard transport gate and API key + OTP/JWT; no response-backed annual ROE schema, semantics, or rights | `SOURCE-GAP` |
| Exchange/issuer filings | official annual documents | not a single multi-symbol ROE provider; extraction/derivation is out of scope | `SOURCE-GAP` |

Qualification is conjunctive. No source is registered and no source is added to a failover chain.

The candidate name `/v4/ratios/latest` was not requested and has no retained response or semantic
evidence; it is `NOT_PROBED`, never a current/latest assertion. The TCInvest URL is likewise only a
candidate landing page: its retained direct result is 403 HTML, with no retained official text or
document path proving ROE semantics, so those semantics are `NOT_PROBED`.

The companion report's dated transport ledger is the only retained dispatch accounting. It binds each
retained ratio cohort to logical/physical counts, method, pages, retries, redirects, status, complete
and normalized MIME, effective route, UA/session/WAF, and bytes. Missing fields are explicitly
`NOT_RETAINED`; they are not zeros or inferred successes. The four direct VNDirect/CafeF rows are one
logical/physical dispatch per caller-selected category, and no global total or per-provider `2+2`
response count is claimed. Unretained documentation, page, browser, and subresource traffic cannot
increase coverage, identity, or budget counts.

## 3. Qualification unit

One future unit is:

```text
owner + exact route/version + exact ROE code/definition/scale
+ annual cadence/fiscal-date/publication/revision semantics
+ symbol/template coverage + bounded runtime + written reuse rights
```

The unit must prove transport, response identity, semantics, coverage, legal/runtime, and atomic
failure together. A label, request selector, report date, current snapshot, page title, or annual
issuer PDF cannot repair an unknown axis.

## 4. Required future API contract, if reopened

Preserve the current single-symbol facade and return at most `limit` complete, distinct,
newest-first reports. Each successful report must contain:

- `StatementType.RATIOS`, `Period.ANNUAL`, and provider fiscal-period-end `fiscal_date`;
- exactly one finite non-boolean dimensionless line with canonical `item_code="ROE"`;
- `currency=None`, `value_unit="ratio"`, and exact percent/fraction provenance;
- provider symbol, source, UTC retrieval time, bounded warnings, and revision/as-of metadata where
  available; and
- no current/TTM/quarter/request-echo/proxy/derived ROE or inferred Dec 31 date.

An owner-specific code other than `ROE` needs an explicit identical-definition binding. Negative and
zero ROE may be valid. Bool, non-finite, malformed, wrong-unit, ambiguous-scale, duplicate,
conflicting, missing-code, wrong-symbol, and wrong-cadence rows fail closed.

One source supplies the whole request. There is no cross-source period stitch or repair, and an
incapable source consumes zero dispatches. Existing cadence-agnostic ratio callers remain unchanged
until a separate compatibility/release review authorizes a public transition.

## 5. Coverage and current-VN30 boundary

HOSE's official ground rules define VN30 as 30 constituents, but the dated 2026-08-23 public
membership snapshot was not retained. A bounded probe covered one caller-selected corporate and one
caller-selected bank case for each no-login route family. That proves only route shape for those
caller selections; response-backed template/entity identity, current-VN30 membership, annual
completeness, and legal reuse remain unknown.

Required future evidence is a dated official membership snapshot plus response-backed symbol identity,
provider-declared bounds, eight distinct annual reports, page/count/cursor reconciliation,
gaps/duplicates/conflicts, and corporate/bank/template diversity. No hard-coded VN30 basket enters
the runtime or public API.

## 6. Internal outcomes and diagnostics

This vocabulary is design-only until a fresh API review approves a public carrier:

```text
FULL | PARTIAL | PUBLISHED_EMPTY | NOT_YET_PUBLISHED | MISSING_PERIOD |
COVERAGE_BOUNDARY | NOT_SERVED | TRANSPORT_FAILURE | SCHEMA_DRIFT |
BUDGET_EXHAUSTED | LEGAL_GAP | IDENTITY_GAP
```

`FULL` requires exactly all eight requested distinct annual reports, complete provider-declared bounds,
and reconciled pages. Fewer than eight is not `FULL`; fewer periods can be `PARTIAL` only when the
provider declares that supported boundary and returned pages reconcile. An unexplained gap, missing
ROE, duplicate/conflict, unreconciled page, or truncated transport is failure/unknown. A timeout,
WAF/403, empty body, or missing page is not published empty or confirmed absence. No error outcome
returns a partial accumulator or false-empty history. Raw URLs/queries, bodies, headers, cookies,
arbitrary provider text, and unbounded names never become public diagnostics.

## 7. Atomic budget design

No numeric ceiling is frozen before a qualifying route and published rate policy. The future
implementation must reserve atomically:

1. one logical source attempt before adapter entry;
2. one physical dispatch immediately before each initial/page/cursor/retry/redirect request;
3. separate byte/decompression counters that never count as network dispatches;
4. zero attempt/dispatch for a capability skip; and
5. one request-scoped global ledger with no reset per source, page, or fallback.

Budget or reconciliation exhaustion discards private rows and preserves only bounded sanitized
attempts. The exception-versus-sentinel carrier remains deferred. Current `FinancialReport` and
`Period.UNKNOWN` behavior remains unchanged.

## 8. Future RED/release matrix

No RED is authorized now. If a source qualifies, RED must cover:

| Dimension | Required cases |
|---|---|
| Input | exact annual request, limit, malformed symbol/statement/period, zero-network unsupported input, current quarter compatibility |
| Identity | symbol/provider symbol, canonical `ROE`, alias binding, wrong/missing/duplicate/conflicting code, mixed entity/template |
| Cadence/date | annual marker/fiscal end positive; absent or present-null annual marker, request echo, current, TTM, quarter, publication/retrieval date, missing publication/as-of metadata, inferred date, null/ambiguous date, and fabricated-date no-fabrication negatives |
| Semantics | average/ending equity, attributable/total profit, percent/fraction, negative/zero, bool/non-finite/malformed, wrong unit/currency |
| Coverage | eight reports, newest-first, provider bounds, pages/counts/cursors, `FULL`/declared `PARTIAL`, missing/interior gap/duplicate/unreconciled negative |
| Atomicity | capability skip, one-source whole request, no stitch, page/retry/redirect/byte/global-budget exhaustion |
| Provenance | source/provider symbol/fiscal date/UTC fetch/revision, bounded warnings/attempts, DataFrame attrs, repr/equality/serialization, `get("ROE")` |
| Compatibility | VNDirect/CafeF current ratio behavior, non-ratio statements, failover, 26-metric zero-ratio-fetch |
| Release | docs/skill/CHANGELOG/API snapshot, focused/full offline tests, build, blacklist/secret/diff/path/object/clean-tree |

The public cadence transition must be explicit and versioned; no current `Period.UNKNOWN` result may
be silently relabeled.

## 9. Reopen and completion gate

Reopen requires one fresh primary-source packet proving exact owner route, response-backed symbol and
ROE identity, annual fiscal semantics, definition/scale/revision, provider-declared eight-period
coverage, current-VN30 evidence, bounded transport/budget, and lawful attribution/storage/
commercial/derivative/redistribution rights. A single document, numeric agreement, label, timeout,
secondary dashboard, or derived ratio cannot reopen the gap.

After a docs-only design PASS, the only allowed sequence is merged docs/full/build/blacklist/diff
gates, push of the exact approved three-path anchor, remote verification, clean no-capability
resolution, close/re-read, and local completion. It does not authorize TDD, RED, model, mapping,
source registration, or runtime work. #222, #223, and #224 remain queued behind active #220.

## 10. Primary references

- [VNDirect ratio route](https://api-finfo.vndirect.com.vn/v4/ratios)
- [VNDirect terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/)
- [CafeF ratio route](https://cafef.vn/du-lieu/Ajax/PageNew/GetDataChiSoTaiChinh.ashx)
- [CafeF data-tool guide](https://cafef.vn/du-lieu/huong-dan-su-dung.chn)
- [SSI developer overview](https://developers.ssi.com.vn/docs/getting-started/overview)
- [SSI terms](https://www.ssi.com.vn/en/terms-of-services)
- [TCBS OpenAPI](https://developers.tcbs.com.vn/)
- [TCInvest analysis page](https://tcinvest.tcbs.com.vn/tc-analysis/dashboard)
- HOSE, *VN30 Index Ground Rules*, Decision 747/QĐ-SGDHCM (30 December 2024), official static PDF

## Bottom summary

- #220 disposition: **SOURCE-GAP CLOSURE**; source chain remains empty.
- VNDirect/CafeF ratio routes do not prove annual fiscal identity and lawful reuse together.
- SSI/TCBS paths are credential-gated or lack an annual ROE API contract.
- Current VN30 coverage remains `UNKNOWN`; no runtime basket is added.
- `Period.UNKNOWN` ratio behavior and zero-ratio metric behavior are preserved.
- Only this note, the source-vetting report, and backlog lifecycle are in scope.
- No RED, code, push, close, mapping, or runtime capability is authorized.
- Reviewer needs the exact committed SHA for design review.
