# #235 API/model-decision packet: macro identity and policy-rate hazard

**Phase:** `API_MODEL_DECISION` — exact decision packet for review

**Status:** `PROPOSED_FOR_REVIEW`; no implementation authorization

**Source/design approval:** exact `429870c252f4920422d071398a3ef169c15e1466`, reviewer
delivery `7d65f45a`, report `reviews/review-202608312046-issue235-final-design-approval.md`

**Published base:** `origin/master` at `472cfe6d42ba43ab535a2ff676220896d5aaaacd`

**Scope:** decide the existing `IndicatorSeries.indicator_code` compatibility contract and the
USA `POLICY_RATE` SBV-label/diagnostic boundary. This packet does not qualify a new provider,
change a source chain, add a model/export, authorize RED, or implement code.

## Decision boundary

The approved source-design result remains `PARTIAL_COHORT`: the frozen cohort and its
`PROVEN_EXISTING`/`PARTIAL`/`SEMANTICS_GAP`/`NOT_PROBED` outcomes are unchanged (`5/6/1/38`),
the new North America chain remains empty, and current annual World Bank behavior is unchanged.
The source-design PASS authorizes this separate API/model decision only.

The clean-room exclusion remains binding. `docs/vnstock-blacklist.md` was read for the source
design; no blacklisted package, repository, endpoint map, schema, fixture, or behavior is used.
No provider endpoint, login, key, payment, raw response, raw row, or external source is accessed by
this packet.

## Proposed decisions

### D1 — Preserve full provider-series identity in `indicator_code`

**Decision:** retain the current field without imposing one global identity interpretation. A source
that declares a provider identity uses its exact response-backed provider code/name; a bare or
caller-supplied source that does not declare one uses the canonical code/name. Do not truncate a
declared provider identity to a concept suffix, and do not add a parallel model field in this
decision.

The exact route-specific contract is:

| Provider family | `IndicatorSeries.indicator_code` contract | Identity check |
|---|---|---|
| DBnomics/IMF IFS | Full returned series ID, including frequency, provider country dimension, and concept; e.g. `M.US.FPOLM_PA` or `M.US.PCPI_PC_CP_A_PT` | Requested series ID and response `series_code` must be the same exact string before a result is returned. |
| World Bank WDI | Existing WDI indicator concept code, e.g. `NY.GDP.MKTP.CD`; the response-backed country identity remains the separate `country` field and row tuple `(countryiso3code, indicator.id, date)` | Returned country and indicator identity must reconcile to the request; do not manufacture a URL-shaped code or fold the country into this existing field. |
| Declared future provider or caller-supplied source | The exact provider-specific code/name declared by `indicator_identity(country_iso3, indicator)` | The returned code must equal the declared code; when the declaration includes a name, the returned name must equal it. A route template or caller echo is not sufficient. |
| Undeclared bare/custom source | Canonical `indicator_code` and `indicator_name` for the requested logical indicator | The returned pair must equal `canonical_indicator_code(indicator)` and `canonical_indicator_name(indicator)`; a custom source remains eligible and is not redefined as provider-opaque. |

The current DBnomics implementation is the decisive compatibility evidence:

- `DBnomicsSource.indicator_identity(country_iso3, indicator)` constructs
  `f"{freq}.{cc}.{concept}"` and returns that full code with the display name.
- `DBnomicsSource.get_indicator()` constructs the same `series_id`, requests the corresponding
  route, requires response `series_code == series_id`, and sets
  `IndicatorSeries.indicator_code=series_id` (`vnfin/macro/dbnomics.py:192-211,227-254,284-294`).
- `MacroClient` validates a declared source identity exactly; it does not convert a provider code to
  `canonical_indicator_code()`.
- The public `sources=` seam is also part of the contract: a caller-supplied source with
  `indicator_identity(country_iso3, indicator)` uses the exact declared code/name, while a source
  without that callable must return the canonical code/name. A mismatch in either branch is a
  typed, failover-safe rejection, never silent relabelling.

The canonical input identity remains separate: `MacroIndicator.POLICY_RATE` normalizes to
`policy_rate`, and `canonical_indicator_name(MacroIndicator.POLICY_RATE)` remains `Policy Rate`.
Those canonical values are selector/registry values, not permission to overwrite a returned
provider-series identity.

#### D1 compatibility and migration rules

1. Existing DBnomics serialized values, equality, `repr`, DataFrame attrs, and callers that treat
   `indicator_code` as an opaque string remain compatible. `M.US.FPOLM_PA` is not rewritten to
   `FPOLM_PA`.
2. Existing bare/custom sources remain compatible: no declared identity means exact canonical code
   and name, while a declared identity means exact declared code/name. Neither branch is relabelled.
3. Existing WDI code values remain concept codes with `country` separate. The full-identity rule is
   route-specific and does not change WDI's current model shape.
4. A future concept-only consumer must not reinterpret this field. If a canonical concept field is
   later needed, a separate versioned API/model decision must add it (or define an explicit
   migration) with public snapshot, serialization, DataFrame, docs, and CHANGELOG compatibility
   gates. No silent dual meaning is allowed.
5. Wrong country, wrong frequency, wrong concept, suffix-only identity, blank identity, or a
   request/response mismatch is a source/API failure, not a usable partial result. No fallback may
   repair it by relabelling.

### D2 — Keep USA `POLICY_RATE` outside the current qualified result contract

**Decision:** do not present the current DBnomics/IMF `FPOLM_PA` result as a North American policy
rate. `USA × POLICY_RATE` remains the approved `SEMANTICS_GAP`; no source result, coverage claim,
or new capability is added by this packet.

The current exact implementation facts are:

```text
_DBN_MAP[POLICY_RATE] =
  ("M", "FPOLM_PA", "% per annum", Frequency.MONTHLY,
   "Policy Rate (SBV refinancing-rate proxy, IMF IFS FPOLM_PA)")

USA -> US -> M.US.FPOLM_PA
indicator_name = "Policy Rate (SBV refinancing-rate proxy, IMF IFS FPOLM_PA)"
source = "dbnomics"
```

`FPOLM_PA` is a monetary-policy-related IFS rate and the current display text is an explicit SBV
proxy disclosure. That disclosure is honest for the existing Vietnam proxy path, but it is not a
country-correct identity outside VNM. The current USA result is therefore a known semantic hazard,
not a compatibility promise to preserve as a North American result. The current mapped set is
`USA`, `CHN`, `JPN`, `DEU`, `VNM`, plus synthetic `ZZZ`; the SBV-proxy route is eligible only for
`VNM`. `ZZZ` remains a test sentinel and is never a public capability.

#### D2 public compatibility boundary

The later implementation, if separately authorized, must apply this boundary:

| Case | Decision contract | Compatibility treatment |
|---|---|---|
| Existing `MacroIndicator.POLICY_RATE` selector and canonical `policy_rate`/`Policy Rate` values | Remain unchanged in v0.2.0 | Preserve selector/export compatibility; no new enum or field here. |
| Existing VNM proxy path | May retain the exact current full series identity and explicit SBV-proxy display disclosure | Preserve unrelated VNM behavior; it remains a proxy, not the announced SBV rate. |
| Any current mapped non-VNM route (`USA`, `CHN`, `JPN`, `DEU`; `ZZZ` fixture only) | Must not return an `IndicatorSeries` labelled as that country's policy rate from `FPOLM_PA` | Deliberate semantic correction, not a promise to preserve the misleading legacy output. It requires later RED, code review, release notes, and CHANGELOG treatment. |
| Future response-backed country-correct policy-rate route | May qualify only with its own full provider-series identity, country-correct semantics, and legal/source evidence | It must not inherit `FPOLM_PA`, the SBV label, or another country's identity. |

#### D2 exact country-scoped preflight and carriers

The one chosen country-aware preflight seam is the internal
`MacroClient._country_eligible_sources(sources, country_iso3, indicator) -> list`, called after the
existing unit `eligible_sources(sources, indicator)` filter and before `FailoverClient` is built. It
uses an optional provider hook with the exact shape
`source.supports_country(country_iso3, indicator) -> bool`; sources without that hook, including
bare/custom caller-supplied sources, remain eligible for the existing result and identity guards.
The built-in DBnomics hook returns `False` only when `indicator is MacroIndicator.POLICY_RATE` and
the normalized country is not `VNM`; it returns `True` for its other mapped indicators and for
`VNM`. This is a provider- and country-scoped rule, not a global `POLICY_RATE` filter, so a
caller-supplied or future independently qualified country-correct source remains eligible.

The direct and public carriers are deterministic:

1. `DBnomicsSource.get_indicator(non_vnm, MacroIndicator.POLICY_RATE)` runs the same country guard
   before URL construction or transport and raises the existing typed `InvalidData` with the exact
   sanitized message `dbnomics: policy_rate route is VNM-only; country={ISO3} is not qualified`.
   `indicator_identity()` uses the same guard and cannot advertise a non-VNM SBV identity.
2. `MacroClient.get_indicator(non_vnm, MacroIndicator.POLICY_RATE)` applies
   `_country_eligible_sources` before the engine. If no other eligible source remains, it raises the
   existing zero-attempt carrier
   `AllSourcesFailed(f"{ISO3}/policy_rate", None, ())`; no DBnomics attempt is recorded. If a
   caller-supplied or future country-correct source remains, it is dispatched under the existing
   failover, unit, returned-identity, and rejection guards; it may succeed or contribute a normal
   `SourceAttempt` failure. No custom source is silently removed merely because it lacks the hook.

This binds one direct `InvalidData` path and one public zero-attempt path; there is no later choice
between alternatives. It does not authorize changing the current runtime. Until a separate RED/code
review, the source-design disposition remains `SEMANTICS_GAP`, the new chain remains empty, and the
current behavior is not re-labelled as qualified.

#### D2 diagnostic boundary

The current `explain_fixed_income_coverage()` is a static Vietnam-oriented diagnostic. Its current
`policy_rate` capability says DBnomics/IMF `FPOLM_PA` is an SBV monetary-policy proxy and its
suggested action is generic `vnfin.macro.get_indicator(iso3, 'policy_rate')`.

The one chosen additive callable is exactly:

```python
def explain_fixed_income_coverage(
    *, country_iso3: str | None = None
) -> RequestDiagnostic:
```

`country_iso3` is keyword-only. `None` returns the current zero-argument object byte/equality
identically: `domain="rates"`, `endpoint="fixed_income_coverage"`, `request={}`,
`status="yield_curve_unavailable"`, `sources=_FIXED_INCOME_CAPS`, the current five `notes`, and
the current three `suggested_actions`. The existing `__all__` entry remains unchanged. A supplied
value is passed through the existing `validate_country_iso3`; its exact existing `InvalidData`
messages remain the input contract, and the normalized uppercase ISO3 is used below. No network
call occurs.

For `country_iso3="VNM"`, return the same legacy fields and exact current `sources`, `notes`, and
`suggested_actions`, with only `request={"country_iso3": "VNM"}` identifying the supplied request.
For every other valid ISO3, including mapped `USA`, `CHN`, `JPN`, `DEU`, and test-only `ZZZ`, return
this exact payload (where `{ISO3}` is the normalized request):

```python
RequestDiagnostic(
    domain="rates",
    endpoint="fixed_income_coverage",
    request={"country_iso3": "{ISO3}"},
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
        "policy_rate is not qualified for country {ISO3}; missing remains missing",
        "the current FPOLM_PA route is VNM-only; "
        "no provider fallback or substitution is made",
    ),
    suggested_actions=(),
)
```

The non-VNM payload exposes no SBV label and no generic policy-rate suggestion. The source tuple is
intentionally a one-entry no-qualified-source tuple for the country-specific policy decision; it
does not claim that unrelated annual bank-rate indicators are unavailable. No new `RequestDiagnostic`
field or status token is introduced. The optional keyword is an additive public signature: existing
zero-argument behavior, export, model fields, and snapshots remain unchanged; the later release must
add the signature/payload cases to the public snapshot and update API docs, skill docs, CHANGELOG,
and focused tests without changing the current snapshot in this packet.

A future exact country-correct policy-rate result may use a neutral display name and its full
provider-series `indicator_code`; it must not inherit the SBV proxy label or warning. This exact
diagnostic and pre-network boundary require RED authorization and implementation review; none is
changed in this packet.

## Exact current surface to freeze

The following current surfaces are compatibility constraints for D1/D2, not implementation work:

- `IndicatorSeries` remains the frozen dataclass with its current field order, generated
  `repr`/equality, `to_dataframe()` shape, and attrs. Its attrs include `country_name`.
- `indicator_code` is the full DBnomics series identity where DBnomics supplies one; the current
  WDI concept-code convention remains unchanged.
- `indicator_name` is display text, not the canonical selector identity. The current VNM SBV-proxy
  text remains a disclosed legacy display value only.
- `source` remains the selected provider/operator string; owner/legal provenance stays in the
  source-design evidence tuple.
- The v0.2.0 public snapshot comparison remains exactly `0` breaking / `60` additive; its baseline
  is not regenerated in this packet. No export, enum, model, warning, or exception is added here.
- Existing DBnomics `series_end_gap` and multi-attempt `failover: {attempt.name}:{attempt.reason}; ...`
  warnings remain distinct from identity or semantic qualification.
- The transport cache remains off by default. If enabled later, URL-query secrets are redacted with
  hashed identity, and nested secret-bearing values in params, JSON bodies, and headers are
  recursively redacted while their deterministic identities isolate cache entries. This packet
  does not enable or alter cache behavior.

## Deferred RED and implementation matrix

No RED authorization is requested by this packet. After API/model PASS and a separate RED
authorization, synthetic offline tests must cover at least:

| Area | Required future cases | Expected boundary |
|---|---|---|
| Full DBnomics identity | `M.US.FPOLM_PA` success only when request, response `series_code`, and returned `indicator_code` match exactly; reject `FPOLM_PA`, wrong country/frequency/concept, blank, null, and caller-echo-only values | No suffix truncation or relabelling |
| Bare/custom identity seam | Declared built-in/custom source uses exact declared provider code/name; undeclared bare/custom source uses exact canonical code/name; exercise both success paths and mismatches in either code or name | Qualified custom sources remain eligible; mismatches are typed failures, never relabelled |
| WDI compatibility | Existing `NY.GDP.MKTP.CD` concept code with response country identity; reject invented URL-shaped or cross-country codes | Preserve current WDI model shape |
| Identity carriers | `IndicatorSeries` equality/repr, DataFrame index/columns/attrs, serialization absence, snapshot and exports | No new field or silent field reinterpretation |
| Country-scoped public preflight | `_country_eligible_sources` filters only DBnomics `POLICY_RATE` for non-VNM before `FailoverClient`; no other eligible source is removed; no remaining source yields `AllSourcesFailed(f"{ISO3}/policy_rate", None, ())` | Deterministic zero-attempt public carrier; qualified custom/future source remains eligible |
| Direct source guard | Direct DBnomics `POLICY_RATE` calls for `USA`, `CHN`, `JPN`, `DEU`, and fixture-only `ZZZ` fail with the exact sanitized `InvalidData` message before provider dispatch; VNM remains eligible | No non-VNM SBV-labelled result; `ZZZ` never becomes a capability |
| VNM compatibility | VNM proxy fixture retains full series ID, exact explicit SBV-proxy display, existing units, and existing warnings | Proxy remains explicitly non-announced |
| Diagnostic | Exact `explain_fixed_income_coverage(*, country_iso3: str | None = None)` signature; no-arg and VNM payloads are fixed; `USA`/`CHN`/`JPN`/`DEU`/fixture `ZZZ` have the complete `RequestDiagnostic` payload above with `status="unknown"`, one no-source capability, fixed notes, and `suggested_actions=()` | No non-VNM SBV label or generic policy-rate suggestion |
| Future USA qualification | A hypothetical exact national route must supply full series identity, country-correct name/semantics, bounds, legal axes, and source provenance | No inheritance from `FPOLM_PA` |
| Failover/cache | Caller guard before cache/network; malformed provider identity after dispatch before cache/return; secret identity remains isolated; multi-attempt warning remains stable | Preserve existing carriers and cache safety |
| Release | API/docs/skill/CHANGELOG, public snapshot, focused/full offline tests, import/version, wheel/sdist, blacklist/secret/diff/path/ancestry/clean-tree gates | Separate code review before publication |

No live probe, raw row, source registration, production code, RED test, API/model implementation,
public capability claim, push, or issue close is authorized by this matrix.

## Reopen and release sequence

This packet is itself a decision proposal, not a capability claim. The exact sequence is:

1. Reviewer reviews this packet and returns an exact API/model decision verdict.
2. If approved, prepare a separate RED-first handoff for only the cases in the matrix above.
3. Reviewer verifies RED and explicitly authorizes implementation.
4. Implement the approved compatibility/diagnostic boundary with no source-chain expansion.
5. Reach GREEN, obtain exact-SHA code review, rerun merged gates, and only then consider any
   separately authorized publication/closure.

The `PARTIAL_COHORT`, `5/6/1/38` matrix, current annual World Bank behavior, current public
snapshot, and empty new source chain remain in force throughout. A packet PASS cannot qualify a
provider, add coverage, or authorize a probe.

## Lifecycle handoff

Source/design PASS was recorded before this packet in backlog commit
`c032793369d81804bc7080543143070b16cae687`. This packet is the sole substantive API/model artifact
for the next review. The API/model BLOCK was recorded first in backlog commit
`049322c8ae120f2ee84c66162ed7066d6b326f23`, binding reviewed target `abfe418`, delivery `122e728d`,
reviewer `162863d`, and report `reviews/review-202608312106-issue235-api-model-decision.md`.
After this narrow packet/backlog correction is handed off, the backlog actor must be
`vnfin-oss-reviewer` and the next action must be `RETURN_EXACT_API_MODEL_DECISION_VERDICT`; before
that handoff, the correction actor is `vnfin-oss`. The final backlog mirror must bind the corrected
packet blob, clean base `472cfe6d42ba43ab535a2ff676220896d5aaaacd`, source/design PASS `429870c`, and
the exact corrected review target.

## Bottom summary

- D1 preserves declared provider identities exactly and preserves bare/custom canonical code/name.
- D2 applies the VNM-only SBV rule to USA, CHN, JPN, DEU, and fixture-only ZZZ.
- One exact country preflight and deterministic direct/public carriers are bound before RED.
- Diagnostic signature/payload is fixed: keyword-only `country_iso3`, complete fields, no new status.
- `PARTIAL_COHORT`, `5/6/1/38`, annual WDI, and empty new chain remain unchanged.
- No model/export/source/probe/RED/code change is made by this packet.
- Next gate is exact API/model re-review, then separate RED authorization if approved.
- Need from reviewer: exact corrected API/model decision verdict; no Boss decision is required now.
