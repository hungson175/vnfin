# Issue #204 design/source gate — SSI/TCX fundamentals

**Status:** `BLOCKED` at the source/template/legal gate; design only
**Date:** 22 August 2026 (UTC+7)
**Packet:** `/home/hungson175/tools/vnfin-oss-reviewer/tasks/204-fundamentals-ssi-tcx-spec.md`
**Evidence:** [`docs/research/2026-08-22-fundamentals-ssi-tcx-source-vetting.md`](../docs/research/2026-08-22-fundamentals-ssi-tcx-source-vetting.md)

## 1. Decision and boundary

This round delivers only a source-vetting report and an additive future API design. It does not
implement an adapter, change the metric catalog, add a source, add a reporter/failover oracle,
or claim SSI/TCX production fundamentals. No live response body or credential is committed.

The mandatory repository blacklist was applied. Only official VNDirect, CafeF, SSI, TCBS,
VSDC, and related primary pages were used. Existing named provider routes were probed
independently; a failover miss is not a coverage or historical-absence oracle.

**Source outcome:** neither `SSI` nor `TCX` has a qualified lawful source path in the accepted
tree. The honest per-symbol result is `NO_QUALIFIED_SOURCE`, with `MetricId.NET_INCOME`
remaining `BLOCKED`. This does not claim either symbol lacks history.

## 2. Required named matrix — final disposition

The complete 12-cell matrix, exact request parameters, HTTP/application results, identity,
template, dates, units, and typed adapter outcomes are in the [source-vetting report](../docs/research/2026-08-22-fundamentals-ssi-tcx-source-vetting.md#5-independent-2-x-2-x-3-matrix).

| Source | `SSI` income/balance/cashflow | `TCX` income/balance/cashflow | Gate result |
|---|---|---|---|
| VNDirect | Current adapter candidates `2/102`, `1/101`, `3/103`: HTTP 200 empty envelopes and `EmptyData`; unrestricted annual route exposes independently foreign `modelType=89/90/91` streams | Same current-candidate failures; foreign streams expose response-backed `code=TCX`; only the observed `modelType=91` stream has raw annual dates missing FY2020 and FY2013 | **Blocked:** provider streams are foreign/unpartitioned; no safe `is_bank` or corporate-code reuse |
| CafeF | Income/balance HTTP 200 `Success=true`, 15 annual objects for 2011–2025, no response `Symbol`, current parser rejects observed `ReportType=K`; cashflow not served | Income/balance HTTP 200 `Success=true`, two annual objects for 2024–2025, no response `Symbol`, current parser rejects `K`; cashflow not served | **Blocked:** response identity, current cadence tag, source namespace, and rights gaps |

### 2.1 Issuer cross-check

- Official SSI audited consolidated `B02-CTCK/HN` evidence: year ended 31 December 2025,
  `Currency: VND`, code 200 total PAT `4,106,880,733,899 VND`, code 201 parent PAT
  `4,106,090,416,749 VND`, code 203 non-controlling interests `790,317,150 VND`.
- Official TCBS/TCX audited standalone `B02-CTCK` evidence: year ended 31 December 2025,
  `Currency: VND`, code 200 PAT `5,683,331,855,108 VND`; code 500 ordinary-shareholder
  appropriation is a separate `5,683,331,855,109 VND` line.

These prove issuer-level securities-company template, fiscal date, units, and line semantics;
they do not prove provider response identity, provider model/item-code identity, or reuse rights.

## 3. Source qualification contract

No source becomes eligible merely because it returns rows. A future source/template candidate
must satisfy every axis below for each symbol and statement:

1. **Transport/access:** official HTTPS route, no-login or explicitly approved credentials,
   bounded request/page budget, and no invented retry/quota promise.
2. **Response identity:** response-backed requested symbol; URL parameter alone is insufficient.
   Mixed, redirected, absent, or contradictory identity fails closed.
3. **Template/schema:** exact provider model/template bound to `(symbol, statement, annual
   cadence)`. For VNDirect, observed `modelType=89`, `90`, and `91` are independently foreign
   and unqualified; do not collapse them into one template, force `is_bank=False`, reuse models
   1/2/3 or 101/102/103, or infer from labels/industry.
4. **Cadence/date:** use provider fiscal dates; CafeF `Time`/`Year` plus `Quater=0` may be
   converted to 31 December only after annual semantics and identity are proven. Never turn a
   publication date into a fiscal date and never fabricate a missing year.
5. **Unit/scale:** provider unit/scale must be explicit or independently reproducible against
   the exact official filing. Emit raw VND only after that proof; no guessed multiplier,
   rounding, or mixed scale.
6. **Metric identity:** resolve by `(statement, source namespace, provider template, item
   code)`, not human label alone. Total PAT and parent-attributable PAT remain distinct.
7. **Rights/retention:** source owner must grant runtime use, retention, attribution, and
   downstream redistribution, or an explicit license must cover all four. No-auth access and
   `robots.txt` are not a data license.
8. **Evidence:** exact official filing cross-check per symbol/template version; no raw provider
   rows in fixtures. Until all axes pass, close the source gap per symbol.

### 3.1 Source-specific mapping rule

The current catalog's VNDirect numeric `corporate_code`/`bank_code` slots remain unchanged.
Future mappings must be additive and independently qualified per statement, conceptually:

```text
(source="vndirect", stream="<verified income stream>", template="<verified income template>", statement="income", concept="total_pat")
(source="vndirect", stream="<verified income stream>", template="<verified income template>", statement="income", concept="parent_pat")
(source="vndirect", stream="<verified balance stream>", template="<verified balance template>", statement="balance", concept="<verified concept>")
(source="vndirect", stream="<verified cashflow stream>", template="<verified cashflow template>", statement="cashflow", concept="<verified concept>")
(source="cafef", template="statement-summary", statement="income", concept="total_pat")
(source="cafef", template="statement-summary", statement="income", concept="parent_pat")
```

These are design-key placeholders, not approved mappings; no `securities:91` income mapping is
authorized. The `89`, `90`, and `91` streams must each earn a statement-specific provider
template and item identity. `LNSTTNDN` and `NetIncome` must remain in a CafeF namespace and
cannot occupy a VNDirect numeric slot. The CafeF map stays `BLOCKED` until response identity,
`K` cadence handling, template semantics, unit scale, legal posture, and the total/parent
distinction are all re-verified.

`MetricInput` must retain statement, item code, source namespace, raw provider line name, fiscal
date, value, and unit. If a template id is needed, add it through a new immutable provenance
field without changing the meaning of existing positional fields.

## 4. Exact future diagnostics design

This defect is independent of whether a source later qualifies.

### 4.1 `metrics()`

- At the public wrapper boundary, validate and canonicalize the symbol once before any source or
  ratio call. Pass that canonical symbol to all three logical statement fetches and pure
  transformers in fixed order `(income, balance, cashflow)`. Invalid or malformed input fails
  before any physical call. Do not fetch ratios.
- If at least one validated statement supplies a fiscal date, preserve partial tolerance and
  return aligned `MetricReport`s with existing per-metric unavailable statuses/reasons.
- If the union of usable fiscal dates is empty after the three recoverable outcomes, raise the
  existing typed `EmptyData` with this exact bounded message:

  ```text
  no usable {cadence} fiscal periods for symbol '{SYMBOL}'; call explain_metric_coverage()
  ```

  `{cadence}` is the lowercase normalized cadence (`annual` or `quarter`) and `SYMBOL` is the
  normalized symbol. The message is trail-free: no raw body, URL, secret, source-attempt list,
  or historical-absence assertion. Invalid caller input and contract violations keep their typed
  behavior; a source-level `InvalidData`/schema failure is a recoverable `SourceError` outcome
  and is sanitized by the source-error mapping below.

### 4.2 `explain_metric_coverage()`

Append after the current `MetricCoverage(symbol, period, periods, notes)` fields:

```python
statement_fetches: tuple[StatementProvenance, ...] = ()
```

The field is exactly three aggregate outcomes in fixed order `(income, balance, cashflow)` even
when `periods == ()`.

| Status | Meaning | `source` | Stable `detail` |
|---|---|---|---|
| `OK` | validated reports accepted | matching canonical role | `None` |
| `MISSING` | allowed-role direct source completed with no usable requested fiscal period | `None` | `no usable {cadence} fiscal periods` |
| `SOURCE_ERROR` | recoverable transport/application/source failure | `None` | `recoverable source error` |
| `NOT_SERVED` | no resolved source capability serves the requested statement | bounded composite canonical role(s) | `statement {statement} not served by source '{source}'` |

Every public `SOURCE_ERROR` detail is exactly the bounded, trail-free string
`recoverable source error`. Apply this same allow-list to aggregate `statement_fetches`,
per-period `statement_provenance`, `MetricValue.reason`, and the `detail` field in DataFrame
attrs. URL/query tokens, response bodies, exception text, provider page counts, and failed-source
attempt trails never enter public models. Internal diagnostics may retain richer data outside
public models; source names may identify the responsible source but may not carry a secret URL.

For every unavailable metric whose statement outcome is `SOURCE_ERROR`, the public
`MetricValue.reason` is exactly `statement {statement} unavailable: recoverable source error`,
where `{statement}` is the normalized statement enum value. The aggregate/per-period
`StatementProvenance.detail` remains the bare allow-listed `recoverable source error`; the
wrapper template is never replaced by arbitrary provider text.

Before capability resolution and any physical call, apply one total source-role and routing
algorithm. The atomic canonical role allow-list is exactly
`{"vndirect", "cafef", "custom"}`; no raw source name is emitted publicly.

1. Resolve a source object's role by exact name equality, without registration or text rewriting:
   an object whose `name` is the exact string `"vndirect"` or `"cafef"` keeps that role, including
   duck-typed/injected test sources; every missing/raising attribute, non-string, empty,
   URL-bearing, overlong, or other name resolves to the fixed safe role `custom` (six ASCII
   characters).
2. For a single direct `source=`, invoke the original object only when its canonical role serves
   the requested statement. A direct allowed-role completion returning `()` is the reachable
   `MISSING` outcome; a custom or incapable role returns `NOT_SERVED` with zero physical calls.
   An explicit empty `sources=[]` is a typed caller-validation error before any call.
3. For an explicit `sources=` chain, resolve every member, then filter out every incapable role
   before constructing/running failover. Only the original source objects whose canonical role
   serves the requested statement may be invoked; a custom member can never become a fallback
   after an allowed source fails. The default chain resolves to `vndirect,cafef` as usual.
4. A non-empty accepted result must have every returned report's `source` exactly equal to the
   resolved canonical role of the object that produced it. A mismatch is rejected/fail-closed as
   sanitized `SOURCE_ERROR`; it is never silently relabeled. `OK` provenance and `MetricInput`
   lineage use that same matching atomic role.
5. For `NOT_SERVED`, encode the responsible roles as a deduplicated, configured-order comma join
   of atomic roles, with no whitespace and an exact maximum of 21 ASCII characters
   (`vndirect,cafef,custom`). This bounded composite is the only multi-role public source value;
   it is used identically in `StatementFetchResult.source`, `StatementProvenance.source`,
   `statement_fetches`, DataFrame attrs, and the exact detail
   `statement {statement} not served by source '{source}'`.

No name sanitization may truncate or echo arbitrary text. A future custom adapter must explicitly
register a bounded canonical role before it can serve a statement.

The existing per-period `statement_provenance` keeps its shape when periods exist, but uses the
same public source-error mapping. When no period exists, the exact invariant is:

```python
coverage.periods == ()
coverage.notes == ("no_fiscal_periods",)
len(coverage.statement_fetches) == 3
```

`to_dataframe().attrs["statement_fetches"]` is a deterministic tuple of exactly three
`(statement.value, status.value, source, detail)` tuples. The new defaulted field is appended so
old positional and keyword constructors remain valid. No attempt trail, raw response, secret, or
unbounded provider diagnostics are exposed.

The aggregate transformer is total and pure over typed outcomes; it never parses an exception or
`SourceAttempt.reason` string. For each logical statement, apply this precedence:

1. non-empty validated reports → `OK`, with the producing source;
2. a capability skip → `NOT_SERVED`, with the bounded composite canonical role and the exact
   bounded `statement {statement} not served by source '{source}'` detail;
3. an accepted allowed-role direct completion with an empty validated report tuple → `MISSING`,
   with `source=None` and detail `no usable {cadence} fiscal periods`;
4. a caught source/failover failure, including `EmptyData` inside the default failed chain →
   `SOURCE_ERROR`, with `source=None` and detail exactly `recoverable source error`.

Thus a direct `source=` result with no reports is never `OK`, while a failed default chain is not
reclassified as `MISSING` by inspecting human-readable reasons. `explain_metric_coverage()` uses
this pure mapping and remains non-fatal; `metrics()` may still raise the exact all-empty
`EmptyData` message.

## 5. Reopen and implementation gates

Reopen is conjunctive per symbol/source. The owner must first provide written reuse permission or
an explicit data/API license. Then a future design review must demonstrate:

- response-backed identity and no mixed/redirected payload;
- for each statement separately, provider-documented stream/template semantics for income,
  balance, or cashflow, without using the bank flag as a proxy; `modelType=89`, `90`, and `91`
  must each be qualified independently and may not be collapsed into one template;
- exact annual fiscal dates and explicit missing-year handling;
- verified raw-VND scale;
- separate total and parent-attributable mappings with exact line-code lineage;
- official filing cross-checks for both symbols and template versions; and
- deterministic bounded request/page/backoff behavior without claiming undisclosed provider
  quotas.

Only after a design PASS may production TDD begin. The first failing tests must cover:

- three recoverable failures => exact `EmptyData`, non-fatal coverage, exact note, and three
  top-level logical outcomes;
- one-success/two-failure alignment and per-period/top-level provenance consistency;
- static CafeF cashflow `NOT_SERVED` without exception-text heuristics;
- allowed-role direct empty completion => aggregate `MISSING`, default failed-chain `EmptyData` =>
  sanitized `SOURCE_ERROR`, and no `SourceAttempt.reason` parsing;
- URL/query-token, JSON/body, and long-sentinel source exceptions are absent from aggregate and
  per-period provenance, metric reasons, DataFrame attrs, and raised all-empty messages;
- RED source-role cases inject an unregistered `source.name` containing a URL/query token plus a
  1,000-character sentinel; assert zero physical calls, only the bounded `custom` role in every
  public source field/detail and DataFrame attr, and no token/sentinel leakage;
- allowed-role duck-typed/injected sources named exactly `vndirect` or `cafef` remain callable;
  an exact-role direct source returning `()` reaches aggregate `MISSING` rather than being skipped;
- a mixed chain `[failing vndirect, malicious custom]` filters `custom` before failover, makes no
  custom call, and leaks neither its token nor its long name; a `cafef + custom` cashflow chain
  returns `NOT_SERVED` with exact composite source `cafef,custom` (maximum 21 characters);
- a non-empty report whose `source` differs from the producing canonical role is rejected/fails
  closed rather than silently relabeled;
- for each source-error metric, bind the exact reason
  `statement {statement} unavailable: recoverable source error`, not the bare detail string;
- exact message/status/detail strings, symbol/cadence normalization, constructor compatibility,
  equality/repr/snapshot, and DataFrame attrs;
- exactly three logical statement outcomes and zero ratio calls; explicit CafeF makes two physical
  source calls with no cashflow HTTP call, while an all-statement source makes three physical
  source calls, with internal failover/pagination/retry work counted separately;
- normalized padded/lowercase/malformed symbols, with malformed input proving zero physical calls;
- normalized `SSI`/`TCX` diagnostics fixtures using injected empty/failure outcomes only; every
  `modelType=89`, `90`, and `91` response fixture remains negative/fail-closed until a later
  conjunctive reopen and additive entity/template design; and
- reject cross-symbol, wrong-cadence, mixed, duplicate, non-finite, malformed, wrong-unit, and
  wrong-scale payloads;
- source-specific CafeF namespace remains `BLOCKED` until the full gate passes.

## 6. Stop condition and handoff

This note intentionally stops at the source-gap closure. The exact cited matrix and legal/source
evidence are in the linked research report. No code, push, or issue close is authorized before
reviewer PASS.
