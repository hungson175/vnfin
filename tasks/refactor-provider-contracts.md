# Refactor: provider-boundary + typed-result contracts

Source plan: `~/tools/vnfin-oss-reviewer/reviews/review-202606191803-technical-debt-refactor-plan.md`
(reviewer, 2026-06-19). Boss directive: refactoring is first priority; GitHub bug fixing is
paused (log only) until the contract foundation lands.

## Why

The same malformed-provider-data bug family keeps recurring because provider-boundary parsing,
identity/key/shape validation, and result acceptance are implemented ad hoc in every adapter and
failover client. Root causes: (1) truthiness collapse (`row.get(x) or ""` erases present-malformed
to absent), (2) broad stringification (`str(raw).strip()` makes containers/bools/floats/padded
strings into plausible keys), (3) adapter-local boundary policy (fixing one doesn't protect
siblings), (4) giant `_validate_*_result()` validators repeating common rules, (5) no formal
"provider contract" object answering "is missing allowed? present-null? which shape is canonical?".

**Goal:** make malformed-provider-data classes structurally hard to reintroduce, with **no public
API change** and **behavior-preserving except fail-closed on malformed provider data**.

## Architecture (3 layers)

1. **Provider-boundary contracts** — `vnfin/_contracts/` private package: reusable field/row/
   envelope parsers defining absent-vs-present semantics, type/shape checks, canonicalization,
   duplicate-key policy — used by adapters instead of raw `.get()` + `or` + `str()`.
2. **Typed-result contracts** — composable rule lists replacing the giant `_validate_*_result()`
   functions (container, metadata, provenance, fetched_at_utc, warnings, identity, rows, sorting,
   duplicate keys, units, domain invariants).
3. **Shared contract test matrices** — `tests/contracts/` parametrized negative/positive cases so
   every adapter inherits the same malformed-shape regression suite.

Key semantic rule that prevents most recent bugs: **missing key** may be legacy-compatible;
**present malformed key/value fails closed** unless the contract explicitly says present-null is
meaningful.

## Phases (one phase per reviewer checkpoint; small commits; full suite + gates each)

- **Phase 0 — freeze + docs (this doc).** WIP stashed (`stash@{0}`), tree clean at `5c05566`,
  suite green, nothing pushed/closed. Backlog "Paused bugs — after refactor" section added.
  → **Checkpoint A** (reviewer) after docs.
- **Phase 1 — contract primitive foundation (private, tests only, NO adapter change).**
  Create `vnfin/_contracts/{__init__,fields,keys,rows}.py` + `tests/test_contract_{fields,keys,
  rows}.py`. Functions: `require_object`, `require_list`, `has_present_key`, `require_present`,
  `optional_present`, `require_non_empty_str`, `optional_present_non_empty_str`,
  `canonical_provider_key`, `canonical_enum_tag`, `reject_duplicate`. Tests cover absent vs
  present-null vs present-blank separately. Public API snapshot unchanged.
  → **Checkpoint B** (reviewer) — review naming/semantics BEFORE any adapter migration.
- **Phase 2 — fundamentals migration (VNDirect + CafeF) onto the primitives.** Encode the
  reportType/ReportType/code/Symbol/itemCode/Code/ratioCode rules as contracts; matrix-driven
  field tests. This naturally subsumes the paused #44/#45/#21/#26 — but framed as migration;
  close those issues only after reviewer agrees migration is complete. → **Checkpoint C** (most
  important).
  - Phase-2 note (poller 18:10): **#45** CafeF `ReportType`/period contract must cover the
    **ratio path** too, not just statements.
  - Phase-2 note (poller 18:10): **#21** a present-blank top-level `Symbol` must NOT mask a
    contradictory `Data.Symbol` — validate the contradiction, don't short-circuit on the blank.
- **Phase 3 — typed-result contract extraction.** Decompose `_validate_*_result()` in price/
  crypto/gold/macro/fundamentals into shared composable rules (`vnfin/_contracts/results.py`,
  `timeseries.py`). Behavior-preserving (no intentional bug fixes). → **Checkpoint D**.
- **Phase 4 — other adapter migrations** (one domain per small batch): Fmarket funds → macro
  (WB/DBnomics/FRED/IMF) → UDF → gold (GoldApi/CurrencyApi/Stooq/BTMC/PNJ) → FX/crypto.
  → **Checkpoint E** (each domain or every 2).
- **Phase 5 — test/doc cleanup.** Shared test factories; `docs/architecture/provider-contracts.md`
  (layer boundaries, absent-vs-present policy, key canonicalization, adapter migration checklist);
  keep human progressive-disclosure + AI/skill internal-only mention.
- **Phase 6 — unfreeze paused bugs + close loop.** Re-apply/reimplement the stashed WIP through the
  new contracts; verify #44/#45/#21/#26 against contract tests; close with refactor commit refs;
  resume normal poller bug fixing.

## Phase 3 design — typed-result contract extraction (responsibility map)

**Behavior-preserving** decomposition of the giant `_validate_*_result()` functions into composable
rules. Each rule returns a rejection **reason string** (recorded as a failover `SourceAttempt`
reason) or `None`. **Reason text must stay byte-exact** (existing tests assert messages), so rules
are **parameterized** (entity noun, key accessor, message) rather than hard-coded — and any drift is
caught by the full suite. **Critical ordering rule:** where a validator checks several properties of
the *same row in one loop* (e.g. gold checks bar-object then bar-date per bar), the extracted rule
must keep that per-row order — do NOT split into separate all-rows passes (that changes which reason
wins for a multi-malformed input).

New files: `vnfin/_contracts/results.py` (result-level) + `vnfin/_contracts/timeseries.py` (row/key).

Old → new map (proposed):

| Old (per-domain, in `_validate_*_result`)                | New rule (parameterized)                                |
|----------------------------------------------------------|---------------------------------------------------------|
| `isinstance(result, T)` → "unexpected result type {n}"   | `results.result_type_reason(result, T)`                 |
| `len(...) == 0` → "empty result" (domain msg)            | `results.non_empty_reason(seq, msg)`                    |
| `_fetched_at_utc_reason` (#127)                          | `results.fetched_at_utc_reason` (move from failover.py) |
| `_warnings_reason` (#128)                                | `results.warnings_reason` (move from failover.py)       |
| per-row object + plain-date check (gold/macro)           | `timeseries.row_object_and_plain_date_reason(noun,key)` |
| per-row object + tz-aware-datetime check (price/crypto)  | `timeseries.row_object_and_aware_dt_reason(noun,key)`   |
| strictly-ascending-by-key (all domains, domain msg)      | `timeseries.strictly_ascending_reason(key, msg)`        |
| duplicate-key (seen-set)                                 | reuse `_contracts.reject_duplicate`                     |

Domain-specific rules stay as small per-validator wrappers (gold product/unit/currency; price OHLCV
+ adjustment; crypto quote-metadata; macro frequency/projection/identity; fundamentals report/line
item). `provenance_of`/provenance check stays in `failover.py` (or moves behind the same API).

**Increment order (one validator per commit, full suite green between):** gold (smallest, ~58 LoC)
→ price → crypto → fundamentals → macro `_reject_reason`. Request **Checkpoint D** after the set
(or after gold as an approach-proof if reviewer prefers). Handoff per checkpoint: commit/range,
exact tests/gates, this old→new map, public-API byte-equality, no-new-bug-scope, no source drift.

## Phase 4 design — adapter migrations (per-domain, Checkpoint E each)

Order: **Fmarket funds** → macro sources (WB/DBnomics/FRED/IMF) → UDF → gold sources → FX/crypto.
Each batch migrates the adapter's provider-field access onto `_contracts` and fail-closed-fixes the
relevant parked bugs; per-batch Checkpoint-E handoff includes commit/range, exact tests/gates,
adapter contract mapping, which parked issues are resolved, and confirmation of no unrelated scope.

**New shared contract needed (funds batch, reused by indices/identifier batches): canonical
security/fund identifier** — for Fmarket `stockCode`/`fundCode` (#34/#33), index constituent
`stockSymbol` (#30), and identifier validation (#9). Proposed grammar (PENDING reviewer confirm):
non-empty, unpadded, upper-normalized, must match `[A-Z][A-Z0-9]*` (letter-start, then uppercase
alnum) → rejects internal space / slash / punctuation / newline / blank / non-string. Open question
for reviewer: do any real VN tickers / Fmarket fund codes contain `.`/`-`/digit-first (e.g. index
codes like `VN30`)? If so, widen the grammar. To live in `_contracts/keys.py` as
`canonical_security_symbol(value, ctx)`.

## Candidate shared test matrices (Phase 1/2)

```
PRESENT_MALFORMED_STR = ["", "   ", None, [], {}, False, True, 123, 1.5]
BAD_PROVIDER_KEYS     = [True, 11000.5, [11000], {"code": 11000}, "", "+11000", "011000", " 11000 "]
BAD_ENUM_TAGS         = ["", "   ", None, [], {}, False, True, 123, "UNKNOWN"]
BAD_SYMBOLS           = ["", "   ", None, [], {}, False, True, 123]
BAD_DATES             = ["2024-1-1", "20240101", "2024/01/01", None, [], {}, False]
```

## Per-phase handoff checklist (every reviewer request)

Phase # + commit/range · exact files changed · behavior unchanged vs fail-closed-changed ·
focused contract tests added · full suite result · public-API snapshot result ·
no-secrets/VNStock/finkit scan · confirm NO GitHub bug closures unless explicitly approved.

## Non-goals

No public API name/signature change · no new features (#140 parked) · no transport rewrite ·
no live-behavior change beyond fail-closed malformed-data boundaries · no accepted-set/policy
questions needing product/legal input (e.g. exact exchange allow-list).

## Status

- **Phase 0: DONE** — docs + backlog freeze; Checkpoint A APPROVE_WITH_NOTES (review-202606191810).
- **Phase 1: IMPLEMENTED (committed, NOT pushed)** — `vnfin/_contracts/{__init__,errors,fields,
  keys,rows}.py` + `tests/test_contract_{fields,keys,rows}.py`. Explicit `MISSING` sentinel;
  key-presence (not truthiness); strict `require_object`/`require_list`; strict
  `require_non_empty_str`/`optional_present_non_empty_str`; `canonical_provider_key`;
  `canonical_enum_tag`; atomic `reject_duplicate`; standardized `contract_error` ctx messages.
  Private package only; no adapter wired; public-API snapshot unchanged; +79 tests; full suite
  2161 green. Checkpoint B BLOCK B1 (canonical_provider_key too permissive) FIXED: reject negatives; non-numeric strings must match `[A-Za-z][A-Za-z0-9_]*` (decimals/punctuation/internal-space rejected). Full suite 2174 green. Checkpoint B PASS (review-202606191821). **Phase 2 DONE** (committed ec69a1e, NOT pushed): VNDirect+CafeF migrated onto _contracts; #44/#45/#21/#26 subsumed (NOT closed — Phase 6). +matrix tests, suite 2234 green, public-API byte-equal. Checkpoint C BLOCK (CafeF+VNDirect+consolidated) FIXED in 5091cbb: VNDirect reportType via canonical_enum_tag {ANNUAL,QUARTER} + present-null modelType fail-closed; CafeF ReportType union {NAM,HK,QUY,H} both paths (ratio cadence-agnostic). +regressions, suite 2263 green, public-API byte-equal. Checkpoint C PASS (review-202606191847). **Phase 1+2 PUSHED** (5c05566..ce84b4b). #44/#45/#21/#26 addressed via migration, kept OPEN for Phase 6 close-loop. Parked #93/#30/#142/#32/#143/#48 (Phase4). **Phase 3 IMPLEMENTED** (gold d32c707 D-lite PASS; rest 9db3eee). All 5 validators (gold/price/crypto/fundamentals/macro) on results.py+timeseries.py rules; byte-exact reasons, first-failing order preserved, macro point-date/ascending kept inline (source-embedded msgs), no bug-fix scope. Suite 2272 green, public-API byte-equal. Checkpoint D PASS (review-202606191908). **Phase 3 PUSHED** (80cf517..7ff76af). **Phase 4 next** (adapter migrations, one domain/batch -> Checkpoint E): Fmarket funds first (parked #34/#33), then macro/UDF/gold/FX/crypto. Parked Phase4 bugs: #93/#30/#142/#32/#143/#48/#34/#33/#9.

- **Phase 4 batch 1 (Fmarket funds): DONE (committed feec8c5, NOT pushed)** — identifier contract + fmarket #33/#34; suite 2337 green; awaiting Checkpoint E. Next: macro sources.
