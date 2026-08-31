# #235 RED-authorization packet: frozen macro identity/policy-rate matrix

**Phase:** `RED_AUTHORIZATION` — failing-tests authorization request only

**Status:** `PROPOSED_FOR_REVIEW`; no RED tests have been written by this packet

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

The following eleven groups map one-to-one to the approved matrix rows. No additional feature,
provider, indicator, source chain, enum, model field, warning, exception, or coverage claim is
inside this authorization request.

### RED-01 — Full DBnomics identity

**Planned location:** `tests/test_macro_dbnomics.py`.

Use only a minimal synthetic response and an HTTP spy. Pin the existing DBnomics identity contract:

- A request whose full identity is `M.US.FPOLM_PA` may succeed only when the synthetic response
  `series_code` and returned `indicator_code` are exactly `M.US.FPOLM_PA`, with the declared
  name also matching when the source declares one.
- Each of these must fail closed as a typed source failure before a result is returned:
  suffix-only `FPOLM_PA`; wrong country; wrong frequency; wrong concept; blank identity;
  null identity; missing provider identity replaced only by a caller echo; and code/name mismatch.
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

### RED-06 — Direct DBnomics source guard

**Planned location:** `tests/test_macro_dbnomics.py`.

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

- The existing VNM proxy fixture retains its full series ID, explicit SBV-proxy display name,
  existing units, frequency, and existing warning behavior.
- The legacy VNM proxy remains explicitly a proxy and is not relabelled as an announced rate.
- The existing `ZZZ` success fixture is deliberately inverted into a RED expectation for the
  non-VNM guard; it is not deleted or generalized into a public capability.
- Annual World Bank indicators, selectors, exports, and unrelated macro sources remain unchanged.

### RED-08 — Exact country-aware diagnostic

**Planned location:** `tests/test_diagnostics.py`.

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

### RED-09 — Future USA qualification seam

**Planned location:** `tests/test_macro_failover.py`.

Use a wholly synthetic, caller-supplied country-correct source; do not register or contact a provider:

- A hypothetical exact national route is eligible only when it supplies a full response-backed
  series identity, country-correct name/semantics, unit/frequency, bounds, and separately
  qualified legal/source provenance in the test declaration.
- It may return through the existing custom-source seam and pass the existing identity/unit/returned
  response guards.
- A source inheriting `FPOLM_PA`, the SBV-proxy name, or another country's identity must fail.
- This is a contract seam test only. It does not claim USA coverage, add a source, or authorize
  provider discovery.

### RED-10 — Failover and cache ordering/safety

**Planned location:** `tests/test_macro_failover.py` and the existing transport/cache contract
tests.

With injected offline transports and a synthetic cache:

- The caller country guard runs before both cache lookup/use and network dispatch for non-VNM
  DBnomics policy-rate requests.
- A malformed provider identity is rejected after the source was dispatched but before the value
  is cached or returned; the test distinguishes this from caller preflight and asserts the
  appropriate existing typed failure path.
- Cache identity remains isolated when nested URL-query, params, JSON-body, or header values
  contain secrets; redaction is deterministic and the secret-bearing identities do not collide.
  Cache remains off by default.
- Existing multi-attempt warning grammar
  `failover: {attempt.name}:{attempt.reason}; ...` remains stable and distinct from semantic
  qualification.
- All transports are spies; no source request or raw response is used.

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
- Approved API/model packet: commit `64bfdc5628428b00634655f988cf01b5aa292a6d`, blob
  `9282ed7497224b3f6d02785ce6db721a00fd3cfc`.
- Source/design PASS: exact `429870c252f4920422d071398a3ef169c15e1466`; research/design blobs
  `4e9440803d9a72fa8cda161f5294de11976a0a3a` /
  `597e057d5725ffe915ee1dd499d1e487b38ca9e9`.
- Clean base: `472cfe6d42ba43ab535a2ff676220896d5aaaacd`; source/design and API/model artifacts
  remain unchanged by this packet.
- Requested next action: `RETURN_EXACT_RED_AUTHORIZATION_VERDICT`; reviewer owns the verdict.
- This artifact is a request for authorization, not evidence that RED is authorized or that a
  capability exists.

## Bottom summary

- API/model PASS is recorded before this separate RED-authorization packet.
- Scope is exactly the approved matrix rows 269-286; no new source or API design is added.
- RED would mean offline failing tests with synthetic fixtures only, after reviewer authorization.
- No tests, fixtures, probes, provider calls, credentials, raw rows, or production code were added.
- VNM proxy, annual World Bank, PARTIAL_COHORT 5/6/1/38, and empty chain stay unchanged.
- Non-VNM policy-rate behavior is only a future test contract, not a current capability claim.
- Next step is exact reviewer RED-authorization verdict; implementation remains separately gated.
- Need from reviewer: explicit RED AUTHORIZED or a precise correction report.
