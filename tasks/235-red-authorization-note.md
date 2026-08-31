# #235 RED-authorization packet: frozen macro identity/policy-rate matrix

**Phase:** `RED_AUTHORIZATION` — failing-tests authorization request only

**Status:** `BLOCKED_FOR_RED_REVIEW`; RED is **NOT AUTHORIZED** at the prior handoff and no RED
tests have been written by this packet

**Decision prerequisite:** API/model decision **PASS** at exact
`7e9cc38c7b043c4ec1c64d4c539b06e6c3405168`, delivery `54f31f52`, report
`reviews/review-202608312120-issue235-corrected-api-model-decision.md`. The approved API/model
packet is commit `64bfdc5628428b00634655f988cf01b5aa292a6d`, blob
`9282ed7497224b3f6d02785ce6db721a00fd3cfc`; `7e9cc38` records the corrected packet and
decision lifecycle.

**Clean base:** `472cfe6d42ba43ab535a2ff676220896d5aaaacd`

**Source/design prerequisite:** exact PASS `429870c252f4920422d071398a3ef169c15e1466`;
approved research blob `4e9440803d9a72fa8cda161f5294de11976a0a3a`; approved design blob
`597e057d5725ffe915ee1dd499d1e487b38ca9e9`.

**Prior RED review:** BLOCK at exact `2528fcfe1350289f3c2ba0f75809e8526b449f37`, delivery
`e56a4bff`, report `reviews/review-202608312139-issue235-red-authorization.md`. The BLOCK was
recorded before this correction in backlog commit `e3ea916c7121baaa5a190da3ea6e58d83d082b12`;
the prior packet blob was `c631bd1d0cb669340e22cfd266344006478255cf`. This document is the
single packet/backlog-only correction and requests a fresh exact RED-authorization verdict.

## Exact authorization requested

This packet asks the reviewer to authorize **only** a later RED commit containing failing,
offline, synthetic tests for the frozen matrix in
`tasks/235-api-model-decision-note.md:269-286`. It does not itself contain tests, fixtures,
runtime changes, provider requests, or a capability claim.

If authorized, RED means:

1. write the failing tests and their minimal synthetic fixtures first;
2. commit that RED state and return its exact SHA for reviewer verification;
3. do not make the tests pass by adding implementation, refactor, source registration, provider
   request, raw-data capture, API/model edit, publication, or issue close in that RED commit.

Implementation requires a second explicit reviewer authorization after RED verification. The current
source chain remains empty. The source-design disposition remains `PARTIAL_COHORT`, with the
50-cell `5/6/1/38` outcomes, current annual World Bank behavior, and all current public API
behavior unchanged.

## Clean-room and network boundary

`docs/vnstock-blacklist.md` was read for this handoff. All blacklisted package, repository, endpoint,
schema, fixture, naming, and behavior material remains excluded. No provider endpoint, login, key,
payment, live response, raw row, or third-party source is accessed or included.

Every proposed RED test is deterministic and offline:

- HTTP is mocked or replaced by an injected transport spy.
- Fixtures are minimal synthetic contract payloads created in the test tree, not copied provider rows.
- A network spy must assert zero calls for every preflight, direct-guard, and diagnostic case that is
  specified as pre-network.
- No live cassette, endpoint fixture, credential, paid route, or source registration is permitted.
- No test may infer, fill, substitute, relabel, or claim coverage for a source.

## Frozen scope: one test group per approved matrix row

The approved matrix has ten executable RED groups plus one separately gated Release row. The ten
groups below map one-to-one to the executable matrix rows; the ledger deliberately separates tests
that characterize current green behavior from tests that must fail before implementation. No
additional feature, provider, indicator, source chain, enum, model field, warning, exception, or
coverage claim is inside this authorization request.

### Exact RED disposition ledger

This ledger is normative for the future RED commit. `CURRENT_CHARACTERIZATION` means the named
existing test is expected to remain green and is not evidence of a RED failure. `MUST_FAIL_AT_RED`
means the named new assertion is absent from the current implementation and must fail for the stated
contract reason before any implementation is allowed. Every call below is an injected synthetic
call; `0 provider` means the transport spy must record zero provider dispatches.

| Case | Current status | Existing/new/modified test | Intended RED failure reason | Network calls |
|---|---|---|---|---|
| C01 DBnomics returned-series mismatch | `CURRENT_CHARACTERIZATION` | Existing `tests/test_macro_dbnomics.py:105-110`, retain | Existing typed `InvalidData` rejection stays green; not a RED failure | 1 injected response; no live call |
| C02 DBnomics malformed/blank/null series code | `CURRENT_CHARACTERIZATION` | Existing `tests/test_macro_dbnomics.py:113-119`, retain | Existing typed rejection stays green; not a RED failure | 1 injected response; no live call |
| C03 declared and undeclared custom identity | `CURRENT_CHARACTERIZATION` | Existing `tests/test_macro_failover.py:1091-1117,1142-1166`, retain | Existing exact canonical/declared success and mismatch guards stay green | 0 provider; synthetic source only |
| C04 WDI country/indicator identity | `CURRENT_CHARACTERIZATION` | Existing `tests/test_macro_worldbank.py:579-599,877-895`, retain | Existing response identity guards stay green | 1 injected response; no live call |
| C05 identity carriers/public snapshot | `CURRENT_CHARACTERIZATION` | Existing `tests/test_public_api_surface.py:273-286` and macro carrier tests, retain | Existing `IndicatorSeries`/snapshot compatibility stays green | 0 provider |
| C06 secret cache identity/redaction | `CURRENT_CHARACTERIZATION` | Existing `tests/test_transport.py:369-429,496-623`, retain | Existing raw cache secret isolation stays green | 0 provider; injected transport only |
| C07 static diagnostic no-arg baseline | `CURRENT_CHARACTERIZATION` | Existing `tests/test_diagnostics.py:162-174` baseline, retain | Current no-arg diagnostic remains unchanged; old local counter is not zero-network evidence | 0 provider |
| C08 VNM policy-rate happy path | `CURRENT_CHARACTERIZATION` | **Modified** `tests/test_macro_dbnomics.py::test_policy_rate_monthly_happy_path` (345-359) | Migrate its current ZZZ fixture to VNM; it must stay green and is not a RED failure | 1 injected response; no live call |
| C09 VNM policy-rate declared identity | `CURRENT_CHARACTERIZATION` | **Modified** `tests/test_macro_dbnomics.py::test_policy_rate_identity_keyed_to_code_not_display` (362-372) | Migrate ZZZ/`M.ZZ.FPOLM_PA` to VNM/`M.VN.FPOLM_PA`; preserve green proxy identity | 0 provider; synthetic identity only |
| C10 VNM stale-warning path | `CURRENT_CHARACTERIZATION` | **Modified** `tests/test_macro_dbnomics.py::test_get_indicator_emits_series_end_gap_when_stale` (440-451) | Migrate request/fixture to VNM; preserve warning and metadata behavior | 1 injected response; no live call |
| C11 VNM default failover path | `CURRENT_CHARACTERIZATION` | **Modified** `tests/test_macro_failover.py::test_policy_rate_resolves_dbnomics_only_monthly` (1194-1202) | Migrate ZZZ/`M.ZZ.FPOLM_PA` to VNM/`M.VN.FPOLM_PA`; preserve result | 1 injected response; no live call |
| C12 VNM finalize-warning path | `CURRENT_CHARACTERIZATION` | **Modified** `tests/test_macro_failover.py::test_series_end_gap_warning_survives_failover_finalize` (1223-1235) | Migrate ZZZ/`M.ZZ.FPOLM_PA` to VNM/`M.VN.FPOLM_PA`; preserve finalized warning | 3 injected responses (World Bank empty, IMF empty, DBnomics synthetic); no live call |
| M01 non-VNM public preflight | `MUST_FAIL_AT_RED` | New parametrized `tests/test_macro_failover.py` case for USA/CHN/JPN/DEU/ZZZ | Missing `_country_eligible_sources` guard dispatches DBnomics or returns the wrong carrier instead of zero-attempt `AllSourcesFailed` | Expected 0 provider; spy must prove it |
| M02 custom fallback/preflight ordering | `MUST_FAIL_AT_RED` | New `tests/test_macro_failover.py` DBnomics-plus-qualified-custom case | Missing provider-scoped preflight fails to skip DBnomics and call custom once | Expected DBnomics 0, custom 1; synthetic spies only |
| M03 hookless custom eligibility | `CURRENT_CHARACTERIZATION` | New characterization adjacent to `tests/test_macro_failover.py` custom cases | Hookless custom remains eligible; any failure is a regression, not a RED target | 0 provider; custom synthetic call only |
| M04 direct non-VNM `get_indicator` guard | `MUST_FAIL_AT_RED` | New parametrized `tests/test_macro_dbnomics.py` case | Missing direct guard constructs/dispatches the route instead of exact `InvalidData` before transport | Expected 0 provider |
| M05 direct non-VNM `indicator_identity` guard | `MUST_FAIL_AT_RED` | New parametrized `tests/test_macro_dbnomics.py` case | Missing identity guard advertises a non-VNM SBV identity instead of exact `InvalidData` | Expected 0 provider |
| M06 ZZZ-to-VNM inversion | `MUST_FAIL_AT_RED` | New explicit ZZZ cases in preflight/direct-guard tests | Current ZZZ policy-rate success must be rejected; the five migrated VNM characterizations must not be deleted | Expected 0 provider for each guard |
| M07 diagnostic country signature/payload | `MUST_FAIL_AT_RED` | New parametrized `tests/test_diagnostics.py` cases for VNM and USA/CHN/JPN/DEU/ZZZ | Current callable lacks the additive keyword and exact non-VNM payload | Expected 0 provider |
| M08 connected diagnostic no-network guard | `MUST_FAIL_AT_RED` | **Modified** diagnostic offline test with an actual transport guard | Existing counter is disconnected; the new signature/payload test must fail before implementation while a raising transport seam proves zero dispatch | Expected 0 provider; raising guard must not fire |
| M09 direct malformed-response carrier | `CURRENT_CHARACTERIZATION` | Existing DBnomics mismatch cases, plus exact carrier assertion | Direct adapter already raises `InvalidData`; keep it green and do not convert it to public aggregation | 1 injected response; no live call |
| M10 public one-attempt failure carrier | `CURRENT_CHARACTERIZATION` | New exact `MacroClient` synthetic malformed-response characterization | Public path must retain one `SourceAttempt` and `AllSourcesFailed`; this is a carrier pin, not an implementation RED failure | 1 injected source/transport call |
| M11 raw transport cache boundary | `CURRENT_CHARACTERIZATION` | Existing cache tests plus one exact raw-text cache assertion | Raw response-text caching remains unchanged; no parsed-result cache is introduced | 1 injected fetch then raw-cache hit |
| M12 guard-before-cache | `MUST_FAIL_AT_RED` | New cache-enabled non-VNM preflight case in `tests/test_macro_failover.py` | Missing caller guard permits cache lookup/use or transport before the country rejection | Expected 0 provider and 0 cache use |
| M13 future USA custom runtime seam | `CURRENT_CHARACTERIZATION` | New synthetic custom identity characterization under RED-02/RED-09 | Exact custom country/identity/unit/failover eligibility remains possible; legal/source qualification is not a runtime assertion | 0 provider; custom synthetic call only |

The five modified policy-rate success cases in C08-C12 are the complete current ZZZ-based success
set identified by the review. Their exact migration is:

| Existing test and fixture | Future RED-commit migration |
|---|---|
| `tests/test_macro_dbnomics.py::test_policy_rate_monthly_happy_path` (345-359), request `ZZZ`, response `M.ZZ.FPOLM_PA` | Request `VNM`, response `M.VN.FPOLM_PA`; preserve `% per annum`, proxy display, points, and no-gap warning |
| `tests/test_macro_dbnomics.py::test_policy_rate_identity_keyed_to_code_not_display` (362-372), identity request `ZZZ` | Identity request `VNM`; expected code `M.VN.FPOLM_PA`; preserve the explicit proxy display/name split |
| `tests/test_macro_dbnomics.py::test_get_indicator_emits_series_end_gap_when_stale` (440-451), request/response `ZZZ`/`M.ZZ.FPOLM_PA` | Request/response `VNM`/`M.VN.FPOLM_PA`; preserve stale warning and fetched timestamp assertions |
| `tests/test_macro_failover.py::test_policy_rate_resolves_dbnomics_only_monthly` (1194-1202), request/response `ZZZ`/`M.ZZ.FPOLM_PA` | Request/response `VNM`/`M.VN.FPOLM_PA`; preserve default failover result and monthly unit |
| `tests/test_macro_failover.py::test_series_end_gap_warning_survives_failover_finalize` (1223-1235), request/response `ZZZ`/`M.ZZ.FPOLM_PA` | Request/response `VNM`/`M.VN.FPOLM_PA`; preserve final warning after failover |

No unrelated ZZZ fixture is globally rewritten. The separate M01/M04/M05/M06 cases explicitly
assert that ZZZ is a non-VNM test sentinel and cannot retain the old policy-rate success path.

### RED-01 — Full DBnomics identity

**Planned location:** `tests/test_macro_dbnomics.py`.

Use only a minimal synthetic response and an HTTP spy. Pin the existing DBnomics identity contract:

- The permitted legacy policy-rate success characterization uses the VNM full identity
  `M.VN.FPOLM_PA`: the synthetic response `series_code` and returned `indicator_code` must be
  exactly `M.VN.FPOLM_PA`, with the declared name also matching when the source declares one.
- `M.US.FPOLM_PA` is a negative non-VNM policy-rate case only. No direct or public USA policy-rate
  call may succeed with it. A non-policy USA identity, if used to exercise generic full-identity
  parsing, is an isolated validator fixture and not an end-to-end USA policy-rate success.
- Each of these must fail closed as a typed source failure before a result is returned:
  suffix-only `FPOLM_PA`; `M.US.FPOLM_PA` for a policy-rate request; wrong country; wrong frequency;
  wrong concept; blank identity; null identity; missing provider identity replaced only by a caller
  echo; and code/name mismatch.
- The assertion is exact identity, not substring matching, suffix repair, normalization, or
  relabelling. The test must not send a real request.

### RED-02 — Declared and undeclared bare/custom identity

**Planned locations:** `tests/test_macro_failover.py` and
`tests/test_macro_dbnomics.py`.

With tiny synthetic custom sources and no network:

- A declared built-in/custom source whose
  `indicator_identity(country_iso3, indicator)` returns `(code, name)` succeeds only when
  the returned code/name equal the declaration exactly.
- A declared code mismatch, declared name mismatch, blank value, or null value is a typed
  failover-safe rejection; it is never silently relabelled.
- An undeclared bare/custom source succeeds only with the canonical code/name for the logical
  indicator; wrong canonical code/name is rejected.
- A custom source remains eligible when it has no optional country hook. A qualified custom source
  may remain eligible through its own country-correct declared identity; the test must prove that
  the preflight does not remove it merely because it is custom or hookless.
- Assertions cover both successful identity branches and both code/name mismatch branches.

### RED-03 — World Bank compatibility

**Planned location:** `tests/test_macro_failover.py` or the existing WDI-focused test module.

Using one minimal synthetic WDI response:

- Preserve `NY.GDP.MKTP.CD` as the indicator concept code and keep response country identity
  separate in the existing model shape.
- Accept only a response whose country identity, indicator identity, and row tuple reconcile to
  the request.
- Reject a URL-shaped invented code, a country-folded code, and a cross-country response identity.
- Do not add a full-series field to WDI and do not alter annual World Bank behavior.

### RED-04 — Existing identity carriers

**Planned locations:** `tests/test_macro_indicators.py`,
`tests/test_public_api_surface.py`, and the existing macro contract/snapshot tests.

Pin the current `IndicatorSeries` without adding or reinterpreting fields:

- field order, generated `repr`, equality, `to_dataframe()` index/columns, and attrs remain
  exact; `country_name` remains in attrs;
- serialization/export behavior has no new identity field;
- the existing v0.2.0 public snapshot remains the approved `0` breaking / `60` additive
  comparison and is not regenerated in RED;
- `indicator_code` remains the full provider identity where a provider supplies one, while WDI
  keeps its concept-code convention; `indicator_name` remains display text;
- existing `series_end_gap` and failover warning carriers remain distinct from identity
  qualification.

These are offline compatibility pins, not authorization to update the snapshot or public surface.

### RED-05 — Country-scoped public preflight

**Planned location:** `tests/test_macro_failover.py`.

The non-VNM DBnomics cases and the DBnomics-plus-custom ordering case are
`MUST_FAIL_AT_RED` (M01/M02 in the ledger); the hookless-custom preservation case is a green
characterization (M03), not a failure target.

Use a synthetic DBnomics-like source, custom sources, and transport spies:

- Exercise `MacroClient._country_eligible_sources(sources, country_iso3, indicator)` after the
  existing unit `eligible_sources` filter and before `FailoverClient`.
- For `POLICY_RATE`, the DBnomics hook is true for `VNM`, false for each mapped non-VNM
  `USA`, `CHN`, `JPN`, `DEU`, and fixture-only `ZZZ`. The hook remains true for other
  DBnomics indicators.
- With only the DBnomics source and each non-VNM country, assert no transport call and the exact
  public carrier `AllSourcesFailed(f"{ISO3}/policy_rate", None, ())`: symbol, interval, and
  empty attempt tuple are all asserted.
- With DBnomics plus a country-correct custom source, assert DBnomics is skipped, the custom source
  is called once, and its exact returned identity is still validated.
- With a hookless custom source, assert it remains eligible. The preflight is provider- and
  indicator-scoped; it must not become a global policy-rate filter or remove unrelated sources.
- No test may call a provider endpoint or turn `ZZZ` into a capability.

The exact public no-source assertion is `AllSourcesFailed.symbol == f"{ISO3}/policy_rate"`,
`.interval is None`, and `.attempts == ()`; it is not a generic message-only assertion. In the
qualified-custom case, the expected counts are DBnomics zero, custom one, and the custom result
must still pass the normal returned-identity/unit guards.

### RED-06 — Direct DBnomics source guard

**Planned location:** `tests/test_macro_dbnomics.py`.

The non-VNM cases are `MUST_FAIL_AT_RED` (M04/M05/M06 in the ledger); the VNM case is the
characterization retained by the five explicit migrations above.

For direct synthetic `DBnomicsSource` calls:

- `get_indicator()` for `USA`, `CHN`, `JPN`, `DEU`, and fixture-only `ZZZ` with
  `POLICY_RATE` raises the exact sanitized `InvalidData` message
  `dbnomics: policy_rate route is VNM-only; country={ISO3} is not qualified` before URL
  construction or transport.
- `indicator_identity()` exercises the same guard and cannot advertise a non-VNM SBV identity.
- `VNM` remains eligible and retains its existing synthetic proxy fixture and exact identity.
- The transport spy asserts zero calls on every non-VNM guard case. The test must not use a real
  DBnomics response.

### RED-07 — VNM compatibility and fixture-only sentinel

**Planned location:** `tests/test_macro_dbnomics.py` and existing macro failover tests.

Pin the deliberately narrow compatibility boundary:

- The five existing ZZZ-based policy-rate success tests are **modified characterizations**, not
  deleted RED tests: each is migrated exactly from request/fixture `ZZZ`/`M.ZZ.FPOLM_PA` to
  `VNM`/`M.VN.FPOLM_PA` as enumerated in the migration table above. They retain full series ID,
  explicit SBV-proxy display name, existing units, frequency, and existing warning behavior.
- The legacy VNM proxy remains explicitly a proxy and is not relabelled as an announced rate.
- New explicit ZZZ preflight/direct-guard cases (M01/M04/M05/M06) are the `MUST_FAIL_AT_RED`
  inversion of the old sentinel behavior; they do not delete the five migrated characterizations
  or generalize ZZZ into a public capability.
- Annual World Bank indicators, selectors, exports, and unrelated macro sources remain unchanged.

### RED-08 — Exact country-aware diagnostic

**Planned location:** `tests/test_diagnostics.py`.

The new country-argument cases are `MUST_FAIL_AT_RED` (M07/M08); the no-argument and VNM legacy
payload assertions are current characterizations that must stay green once the additive signature
is implemented.

Pin the additive signature and exact payload without a network call:

```python
def explain_fixed_income_coverage(
    *, country_iso3: str | None = None
) -> RequestDiagnostic:
```

- No argument returns the current object byte/equality-identically: current domain, endpoint,
  empty request, status, `_FIXED_INCOME_CAPS`, five current notes, and three current suggested
  actions are unchanged.
- `country_iso3="VNM"` returns the same legacy fields, source tuple, notes, and actions, with
  only `request={"country_iso3": "VNM"}`; assert the exact frozen values from the approved
  API/model packet rather than paraphrasing them.
- Each valid non-VNM case `USA`, `CHN`, `JPN`, `DEU`, and fixture-only `ZZZ` returns
  exactly:

```python
RequestDiagnostic(
    domain="rates",
    endpoint="fixed_income_coverage",
    request={"country_iso3": ISO3},
    status="unknown",
    sources=(
        SourceCapability(
            domain="rates",
            endpoint="policy_rate",
            source="(none)",
            instruments=("policy_rate",),
            granularity=None,
            coverage_start=None,
            coverage_end=None,
            is_default=False,
            is_opt_in=False,
            is_single_source=False,
            limitations=(
                "policy_rate is not qualified for the requested country; "
                "the current FPOLM_PA route is VNM-only",
                "no country-correct no-key provider is qualified; "
                "no fallback or substitution is made",
            ),
            suggested_action=None,
        ),
    ),
    notes=(
        f"policy_rate is not qualified for country {ISO3}; missing remains missing",
        "the current FPOLM_PA route is VNM-only; "
        "no provider fallback or substitution is made",
    ),
    suggested_actions=(),
)
```

- Assert no SBV label and no generic policy-rate suggestion in non-VNM payloads. Existing country
  validation and its exact input errors remain the input boundary. The diagnostic is static and
  must make zero transport calls.
- Replace the existing disconnected local `called` counter in
  `tests/test_diagnostics.py:162-174` with a connected raising guard installed before every
  no-argument, VNM, and non-VNM invocation. The RED test must monkeypatch the actual
  `vnfin.transport.HttpDataSource._fetch_with_retry` seam (and may additionally guard the socket
  constructor); any invocation raises immediately and increments the guard, and the final
  assertion requires zero guard calls. This proves the diagnostic's no-network behavior rather
  than merely asserting an unrelated counter.

### RED-09 — Future USA qualification seam

**Planned location:** `tests/test_macro_failover.py`.

This row has two distinct layers. The source-design/reviewer layer is a non-runtime precondition:
before any future source is qualified, the reviewer must independently establish a response-backed
full provider identity, country-correct semantics, exact bounds, and legal/source rights. Those
facts are not runtime fields in `IndicatorSeries`, are not enforced by a global name blacklist,
and are not executable RED assertions. If a new runtime carrier for them is desired, the work
must return to API/model design instead of hiding that change in RED.

The executable RED portion is only the approved runtime seam, using a wholly synthetic,
caller-supplied source and no provider registration or contact:

- A custom source with `supports_country("USA", MacroIndicator.POLICY_RATE) is True`, a declared
  exact code/name, canonical country, and canonical unit remains eligible and passes the existing
  returned-response/failover guards. This is a green characterization (M13), not a MUST_FAIL case.
- A synthetic response with the wrong country, declared code/name, or unit is rejected through the
  existing typed runtime guards. It tests only country, identity, unit, and failover behavior; it
  does not assert legal/source/bounds metadata.
- A source inheriting `FPOLM_PA` is rejected only when its returned runtime identity contradicts
  the declared country/identity, not because RED adds a new global SBV/name rule.
- This is a contract seam test only. It does not claim USA coverage, add a source, or authorize
  provider discovery. Legal/source/bounds qualification remains outside runtime RED.

### RED-10 — Failover and cache ordering/safety

**Planned location:** `tests/test_macro_failover.py` and the existing transport/cache contract
tests.

The ledger classifies the exact carriers below: M12 is `MUST_FAIL_AT_RED`; the direct/public/raw
cache assertions are current carrier characterizations unless their named guard is absent. All
transport invocations are injected synthetic calls, never live requests.

| Carrier | Synthetic setup and exact assertion | Expected calls/cache boundary |
|---|---|---|
| Direct malformed response | VNM `DBnomicsSource.get_indicator()` receives `series_code="M.VN.WRONG"`; it raises exactly `InvalidData("dbnomics: returned series_code 'M.VN.WRONG' != requested 'M.VN.FPOLM_PA'")` and returns no `IndicatorSeries` | 1 injected source/transport call; direct carrier is `InvalidData`, not `AllSourcesFailed` |
| Public malformed response | One eligible VNM DBnomics source receives the same synthetic response; `MacroClient` raises `AllSourcesFailed` with `.symbol == "VNM/policy_rate"`, `.interval is None`, and `.attempts == (SourceAttempt("dbnomics", False, "InvalidData: dbnomics: returned series_code 'M.VN.WRONG' != requested 'M.VN.FPOLM_PA'"),)` | Exactly 1 source operation and 1 injected transport call; one rejected `SourceAttempt`, no result |
| Raw transport-text cache | With `cache_ttl=60`, first direct malformed call raises the exact `InvalidData`; a second identical call parses the cached raw synthetic text and raises the same error | First call 1 injected fetch; second call 0 fetches. The raw text cache is unchanged; no parsed-result cache or transport-cache redesign is authorized |
| Guard before cache | Cache-enabled non-VNM policy-rate request patches the actual `HttpDataSource._request_text` cache/transport seam to a raising guard and invokes the public/direct country guard | M12 expects 0 cache lookups, 0 provider calls, and the exact pre-network carrier; the raising cache/transport guard must not fire |
| Secret cache identity and warnings | Existing secret-bearing query/params/JSON/header fixtures and multi-attempt warning fixtures remain exact characterizations | Existing injected call counts, deterministic redaction/hash identity, and `failover: {attempt.name}:{attempt.reason}; ...` grammar remain green |

The caller country guard is therefore tested before both cache lookup/use and network dispatch for
non-VNM DBnomics policy-rate requests. A malformed response is tested **after one dispatch** and
before any parsed result is returned: the raw transport-text cache may retain the raw synthetic
text under the existing cache contract, but no parsed `IndicatorSeries` result is cached or
returned. The public and direct exception carriers above are exact; no shared transport-cache
redesign is hidden in RED, and cache remains off by default.

The connected no-network diagnostic guard is the separate M08 case in RED-08. Its raising
`HttpDataSource._fetch_with_retry` monkeypatch is installed before each diagnostic invocation,
including no-argument, VNM, and every non-VNM case; any actual transport call fails immediately.
All transports remain spies and no source request or raw response is used.

## Release row boundary

The approved matrix's Release row is **not** part of the RED commit. It is a later GREEN/code-review
gate only: after implementation is separately authorized and reaches GREEN, the maintainer must
update the public API docs, skill docs, CHANGELOG, public snapshot, focused/full offline tests,
import/version checks, wheel/sdist, blacklist/secret/diff/path/ancestry/clean-tree gates, and
obtain exact-SHA code review before any publication decision. No release file, snapshot, capability,
or source-chain change is authorized by this packet.

## Exact RED commit and review sequence

The expected lifecycle is deliberately two-phase:

1. This packet is reviewed for exact matrix scope and no-network safety.
2. If the reviewer returns **RED AUTHORIZED**, write only the failing tests and synthetic fixtures
   listed above; do not make production code changes.
3. Commit the RED state and return its exact SHA. The reviewer verifies that the tests fail for the
   intended contract reasons, remain offline, and do not broaden scope.
4. Only a separate explicit reviewer authorization permits implementation. Implementation must
   preserve the source-gap/empty-chain boundary.
5. Reach GREEN, obtain exact-SHA code review, and run the merged release gates. Publication/closure
   remains separately gated.

Before the RED verdict, the current tree has no new test files or fixture files from this packet.
The backlog PASS record was committed first at
`1e37c85418c12dfd78d9c0d12bcb55a87677c57e`; the next lifecycle transition is
`RETURN_EXACT_RED_AUTHORIZATION_VERDICT` owned by `vnfin-oss-reviewer` after this handoff.

## Explicit non-authorizations

This packet does **not** authorize:

- any production code, test implementation before RED authorization, API/model modification, or
  source registration;
- provider probes, HTTP calls, live cassettes, raw responses, raw rows, credentials, payment,
  downloads, or contact/enquiry;
- adding a provider, populating the macro source chain, changing annual World Bank behavior, or
  claiming USA/other-country policy-rate coverage;
- changing `PARTIAL_COHORT`, `5/6/1/38`, the current public snapshot, missingness, or
  substitution behavior;
- pushing, publishing, resolving, or closing any issue.

Only the reviewer can grant the next RED or implementation transition.

## Lifecycle binding

- API/model PASS: exact `7e9cc38c7b043c4ec1c64d4c539b06e6c3405168`, delivery `54f31f52`,
  report `reviews/review-202608312120-issue235-corrected-api-model-decision.md`.
- Prior RED-authorization BLOCK: exact `2528fcfe1350289f3c2ba0f75809e8526b449f37`, delivery
  `e56a4bff`, report `reviews/review-202608312139-issue235-red-authorization.md`, recorded first
  in backlog commit `e3ea916c7121baaa5a190da3ea6e58d83d082b12`. RED was not authorized.
- Approved API/model packet: commit `64bfdc5628428b00634655f988cf01b5aa292a6d`, blob
  `9282ed7497224b3f6d02785ce6db721a00fd3cfc`.
- Source/design PASS: exact `429870c252f4920422d071398a3ef169c15e1466`; research/design blobs
  `4e9440803d9a72fa8cda161f5294de11976a0a3a` /
  `597e057d5725ffe915ee1dd499d1e487b38ca9e9`.
- Clean base: `472cfe6d42ba43ab535a2ff676220896d5aaaacd`; source/design and API/model artifacts
  remain unchanged by this packet.
- Requested next action: `RETURN_EXACT_RED_AUTHORIZATION_VERDICT`; reviewer owns the verdict. The
  corrected packet must be reviewed as a new authorization request; no RED work starts before that
  exact verdict.
- This artifact is a request for authorization, not evidence that RED is authorized or that a
  capability exists.

## Bottom summary

- API/model PASS is recorded before this separate RED-authorization packet.
- Scope is exactly the approved matrix rows 269-286; no new source or API design is added.
- RED remains unauthorized until the corrected packet receives an exact reviewer authorization.
- If authorized, RED would mean offline failing tests with synthetic fixtures only.
- No tests, fixtures, probes, provider calls, credentials, raw rows, or production code were added.
- VNM proxy, annual World Bank, PARTIAL_COHORT 5/6/1/38, and empty chain stay unchanged.
- Non-VNM policy-rate behavior is only a future test contract, not a current capability claim.
- Next step is exact reviewer RED-authorization verdict; implementation remains separately gated.
- Need from reviewer: explicit RED AUTHORIZED or a precise correction report.
