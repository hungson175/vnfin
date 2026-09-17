# #236 API/model-decision packet — SGP IMF fallback boundary

**Date:** 17 September 2026 (+07)

**Phase:** `API_MODEL_DECISION`

**Status:** `PROPOSED_FOR_REVIEW`; no RED or implementation authorization

**Source/design approval:** exact `631410a2d95cf27aaff43791e5b041fc853b9de2`, delivery
`e750b5a5`, reviewer commit `b9ae587`, report
`review-202609172026-issue236-final-design-approval.md`

**Published base:** clean `origin/master` at
`8d450a40cd9763a58bdb85c5f125edcc18d182da`

**Scope:** decide only the request-scoped treatment of the three legally uncleared IMF fallbacks
for Singapore. This packet uses retained evidence only. It does not access a provider or the
network, qualify IMF reuse, register SingStat or another source, add a public macro result model,
authorize RED, change runtime/source/model code, push, claim capability, or close the issue.

## Decision boundary

The approved source result remains unchanged: all eight annual `SGP` cells have exact, qualified
World Bank WDI primary legs; five complete default chains qualify; and `GDP_GROWTH`, `INFLATION`,
and `UNEMPLOYMENT` remain `PARTIAL` because their automatic IMF fallbacks are not legally cleared
for an OSS default. SingStat `M213781` remains unregistered behind `ROUTE_GAP + LEGAL_GAP`, and
`POLICY_RATE` remains blocked behind `SEMANTICS_GAP + SOURCE_LOCATOR_GAP`.

The clean-room exclusion remains binding. No blacklisted package, repository, endpoint map,
schema, fixture, name, or behavior is used. This packet performs no new research and relies only on
the exact retained source/design evidence approved at `631410a`.

## Chosen decision

Choose **provider-scoped, country-and-indicator gating**:

```text
IMF DataMapper is ineligible only for:
  SGP / gdp_growth   (NGDP_RPCH)
  SGP / inflation    (PCPIPCH)
  SGP / unemployment (LUR)
```

The gate is evaluated after canonical request validation and the existing unit filter, but before
`FailoverClient` construction, source-attempt accounting, response-cache lookup, URL dispatch, or
transport. It is also enforced by direct IMF source calls before URL construction/cache/transport.
This is a conservative request eligibility rule, not `NO_DATA`, a provider failure, or a legal
qualification of IMF for any country.

The chosen rule does **not**:

- remove IMF from `default_macro_sources()` or change its World Bank -> IMF -> DBnomics order;
- change the eight WDI primary mappings or allow a different primary;
- gate IMF for another country or for `SGP/GDP`;
- make IMF `NGDPD` a GDP fallback (its `USD bn` unit remains noncanonical for current-US$ GDP);
- alter projection classification, `latest()`, source warnings, unit/identity guards, or failover;
- special-case or remove a caller-supplied country-aware or hookless source; or
- qualify, register, derive, relabel, fill, or stitch a Singapore monthly series or policy proxy.

After a later separately approved implementation, the effective built-in chains for the three
cells are WDI-only for `SGP`. The configured source inventory remains unchanged; eligibility is
computed per request.

## Exact future seam

### D1 — Reuse the existing country preflight unchanged

The sole client preflight remains:

```python
MacroClient._country_eligible_sources(
    sources, country_iso3, indicator
) -> list
```

Its current order remains binding:

1. validate and normalize the country and indicator;
2. run `eligible_sources(sources, indicator)` for canonical unit compatibility;
3. run `_country_eligible_sources(...)`;
4. if the list is empty, raise the existing zero-attempt `AllSourcesFailed` carrier;
5. otherwise construct and run `FailoverClient` over only the survivors.

The existing optional protocol remains `source.supports_country(country_iso3, indicator) -> bool`.
A source declaring the hook must affirm the pair; a source without the hook remains eligible and is
still subject to the existing unit, returned-identity, result, and rejection guards. No client
control-flow redesign or IMF-specific type/name check is chosen.

### D2 — Add one IMF capability declaration

A later implementation may add exactly one compatibility-preserving provider method:

```python
IMFDataMapperSource.supports_country(country_iso3, indicator) -> bool
```

Its exact behavior is:

| Input | Result |
|---|---|
| `SGP` and one of `GDP_GROWTH`, `INFLATION`, `UNEMPLOYMENT` | `False` |
| Any other valid ISO3 and any indicator in `_IMF_MAP` | `True` |
| `SGP/GDP` | `True`; the existing unit filter still removes it from canonical GDP failover |
| Malformed country or unsupported indicator | `False`, without network or transport |

The three-member set is frozen and provider-local. Indicator-only `supports()`, `unit_for()`,
`_IMF_MAP`, source construction, timeout, headers, response parsing, identity values, and the
projection boundary remain unchanged.

`IMFDataMapperSource` is exported and snapshot-inspected, so `supports_country()` is an **additive
public class method** even though the client uses it as a capability hook. This additive snapshot
delta is accepted as the narrow architectural choice; it mirrors the existing
`DBnomicsSource.supports_country()` protocol and avoids coupling generic orchestration to an IMF
type/name special case. No existing method, function, constructor, parameter, enum, export, model
field, serialization shape, or return type changes.

### D3 — Bind the same rule on direct IMF paths

The public client preflight alone is insufficient because callers may instantiate the exported IMF
source directly. A later implementation must use one shared private guard in both:

- `IMFDataMapperSource.get_indicator()`, after existing country/indicator validation and mapping,
  but before URL construction, `_request_json()`, cache lookup, retry, or HTTP; and
- `IMFDataMapperSource.indicator_identity()`, so the source cannot advertise an identity for a
  route that it refuses to serve.

For each gated pair, direct fetch and identity calls raise existing typed `InvalidData` with this
exact sanitized message, substituting the canonical lowercase indicator value:

```text
imf_datamapper: {indicator} route is not qualified for country=SGP
```

Examples substitute `gdp_growth`, `inflation`, or `unemployment`. Malformed direct inputs retain
the existing canonical input-validation errors; unsupported indicators retain the existing
unsupported-indicator error. No new exception type, warning, diagnostic model, or status token is
introduced.

## Exact public behavior and failure carriers

| Request | Required later behavior |
|---|---|
| `SGP` gated cell, healthy WDI | Return the same WDI `IndicatorSeries`; no IMF call or warning. |
| `SGP` gated cell, WDI fails, default built-ins only | Existing `AllSourcesFailed` with the WDI `SourceAttempt` only. IMF is a preflight skip and never appears as an attempt. |
| `SGP` gated cell, IMF is the only configured source | `AllSourcesFailed(f"SGP/{indicator}", None, ())`; zero attempts. |
| `SGP` gated cell, WDI fails and an eligible custom source succeeds | Existing result/finalization behavior; the attempt trail/warning contains only actual attempted sources, never skipped IMF. |
| Direct IMF fetch or identity for a gated pair | Exact `InvalidData` above before URL/cache/transport. |
| Same three indicators for any valid non-SGP country | Existing WDI -> IMF fallback eligibility and behavior remain unchanged. |
| Any other indicator/country route | Existing eligibility, unit filtering, identity, failover, and diagnostics remain unchanged. |

A skipped IMF route is a **capability/legal preflight outcome**. It must never be reclassified as
`EmptyData`, `NO_DATA`, `SourceUnavailable`, an IMF failure attempt, or a successful qualified
chain. If WDI itself returns no usable observations, that existing WDI `EmptyData` may be recorded
as the WDI attempt; the IMF skip remains absent.

`MacroClient.sources` continues to expose the configured source objects, including IMF. The gate
does not mutate that list. `max_attempts` continues to count actual engine attempts under the
existing rules and is not consumed by the preflight skip.

## Compatibility invariants

### WDI and all other countries

- WDI stays first and byte/field-equivalent on success for all eight annual SGP concepts.
- For every country other than `SGP`, the three percent indicators retain their current WDI -> IMF
  eligibility, mapping, identity, error, projection, warning, and `latest()` behavior.
- This SGP-only correction makes no assertion that IMF reuse is legally cleared elsewhere. It
  preserves out-of-scope compatibility rather than granting permission.
- IMF GDP remains `USD bn` and outside the canonical current-US$ GDP failover chain everywhere.
- VNM policy-rate routing, the existing DBnomics VNM-only guard, USA/other-country behavior, FRED
  opt-in behavior, and every non-IMF source mapping remain unchanged.

### Caller-supplied sources

- A country-aware custom source returning `True` stays eligible in caller-provided order.
- A country-aware custom source returning `False` is skipped before its cache/transport and creates
  no attempt.
- A legacy/hookless custom source stays eligible; no new hook is required from callers.
- A unit-incompatible source remains filtered before country qualification.
- A declared custom identity must still match its exact declared code/name; a hookless identity
  must still match the canonical code/name. The IMF rule cannot relabel a custom result.

This means a truthful custom source may serve any of the three gated annual SGP cells after WDI
failure. The rule filters the built-in IMF route, not the canonical indicator itself.

### Public API, model, and diagnostics

The following stay exact:

- `vnfin.macro.get_indicator(country_iso3, indicator) -> IndicatorSeries`;
- `MacroClient.get_indicator()` and constructor signatures;
- the frozen `IndicatorSeries` fields/order/equality/`repr`/DataFrame behavior;
- `MacroIndicator`, canonical codes/names/units/currencies/frequencies, and exports;
- the current `AllSourcesFailed`, `SourceAttempt`, and `InvalidData` classes and fields;
- current diagnostic callables and payloads, including fixed-income coverage and health probes;
- warning-token inventory and all existing warning text, including IMF projection warnings; and
- no Singapore helper, coverage object, new status, new model field, or new diagnostic endpoint.

The only public-surface addition accepted by this decision is the provider capability method in
D2, with its synchronized additive API-snapshot entry. Runtime documentation must explain that a
country-ineligible provider is intentionally absent from `attempts`; that absence is not hidden
transport failure or missing provider data.

## Rejected alternatives

1. **Keep the automatic SGP IMF fallback.** Rejected: retained terms do not clear the automatic OSS
   default lifecycle; technical response success cannot substitute for permission.
2. **Remove IMF globally or delete the three mappings.** Rejected: it changes all other countries
   and exceeds the issue-scoped evidence.
3. **Change source order or remove WDI.** Rejected: all eight SGP WDI primary legs are exact and
   qualified.
4. **Add a global canonical-indicator denylist in `MacroClient`.** Rejected: it would also suppress
   truthful custom/future sources and conflate a provider route with the logical indicator.
5. **Special-case `IMFDataMapperSource` by class/name in the client.** Rejected: it duplicates the
   established optional country-capability protocol and couples the generic client to provider
   policy.
6. **Gate only the default client.** Rejected: direct calls on the exported IMF source could still
   reach the same uncleared routes.
7. **Return a warning, `None`, `EmptyData`, or a new status/model.** Rejected: preflight eligibility
   already has deterministic typed carriers and attempt semantics.
8. **Register SingStat or use SORA/rate proxies.** Rejected: their separate route/legal/semantic
   gates remain open.

## Complete deferred twelve-case matrix

No RED or production code is authorized by this packet. Any later #236 behavior or code change must
account for all twelve cases in a separately authorized build packet. The API/model decision makes
the following expectations exact:

1. **Eight WDI primaries:** parameterize exact `SGP` request country/code, returned identity,
   canonical unit/currency/frequency, finite observations, ascending unique dates, and approved
   bounds for all eight annual legs; healthy results remain byte/field-equivalent.
2. **WDI adversarial paths:** reject wrong country/code, null/malformed/non-finite/boolean values,
   empty or out-of-window results, forbidden interior gaps, conflicting duplicates, revisions, and
   stale-rate overclaims. For the three gated cells, preserve the exact WDI attempt and prove no IMF
   attempt follows.
3. **Exact SGP IMF gate:** cover `NGDP_RPCH`, `PCPIPCH`, and `LUR` through public client, direct
   fetch, and identity paths; all gate before cache/transport. Prove there is no IMF GDP
   substitution and that `SGP/GDP` is still excluded by unit, not this gate.
4. **IMF projection compatibility:** use non-SGP synthetic fixtures to freeze the current UTC-year
   projection boundary, exact warning/flag behavior, and `latest()` exclusion.
5. **No repair or stitching:** prove semantic/unit/frequency mismatch cannot stitch, relabel, or
   fail over observations among WDI, IMF, SingStat, MAS, or data.gov.sg.
6. **Missing monthly CPI:** default `SGP/CPI_YOY` continues to make zero built-in source, cache, and
   HTTP attempts while SingStat's route/legal gates fail.
7. **Missing policy rate:** default `SGP/POLICY_RATE` likewise makes zero built-in attempts and
   rejects SORA, interbank, facility, lending/deposit, bond-yield, and FX proxies.
8. **Country-aware custom seam:** a truthful custom source may serve each missing monthly cell and
   at least one newly gated annual cell; a false country hook is skipped before cache/transport and
   creates no attempt.
9. **Hookless custom seam:** a legacy/hookless custom source remains eligible with its existing
   canonical unit/identity/result guards and caller order.
10. **Other-country compatibility:** VNM policy-rate routing and its DBnomics guard remain exact;
    non-SGP WDI -> IMF fallback for all three percent indicators remains exact; USA and arbitrary
    other valid-country behavior is unchanged.
11. **SingStat boundary:** prove SingStat remains absent from default sources, exports, and
    registries. If separately approved later, instead exercise its complete GET/table/row/label/
    `Per Cent`/monthly-day-1/base, envelope, MIME/final-host/redirect/auth/paging/size, missing-value,
    malformed-value, duplicate, correction, empty/window, and no-local-YoY contract.
12. **Hermetic integration gates:** use only committed synthetic fixtures and injected HTTP; cover
    the additive provider-method API snapshot, docs/source terms/warnings, no live rows/keys/secrets,
    VNStock-blacklist scan, full merged-tree suite, and wheel/sdist build.

The later RED packet must distinguish current characterization from new must-fail tests. This
packet creates neither.

## Documentation and release boundary

Only after separate API/model approval plus RED/build authorization may implementation update the
IMF source, tests, public snapshot, runtime docs, skill docs, API examples, and CHANGELOG. Generic
"World Bank -> IMF" prose must then disclose the SGP three-indicator exception without implying
that IMF was removed globally. No runtime-facing document is changed now as though the decision had
shipped.

Removing or weakening the gate later requires retained permission that explicitly covers the
intended automated access, caller return, cache/storage, commercial/derivative use, redistribution,
amendment, and revocation lifecycle, followed by a separate source/legal/API/model/release gate.
Provider response success alone is insufficient.

## Risks accepted by this decision

1. Direct SGP IMF calls for the three indicators deliberately change from possible dispatch to
   immediate `InvalidData`; this is the intended conservative compatibility correction.
2. The public attempt list intentionally omits IMF because the provider is skipped before the
   engine. Documentation and tests must prevent that omission from being mistaken for `NO_DATA`.
3. `supports_country()` adds one method to an exported class and therefore needs an additive public
   snapshot update even though top-level APIs and result models do not change.
4. SGP-only gating preserves other-country behavior but does not positively clear IMF rights in
   those other contexts.
5. Direct fetch and identity must share the same guard; implementing only one would create a
   contradictory capability contract.
6. Projection tests must move to non-SGP synthetic cases because the three SGP IMF paths will no
   longer dispatch.

## Lifecycle and next gate

- Intake receipt: `56fa8457`; public anchor `issuecomment-5714070058`.
- Final source/design approval: exact `631410a2d95cf27aaff43791e5b041fc853b9de2`, delivery
  `e750b5a5`, reviewer commit `b9ae587`.
- Current scope is this retained-evidence API/model decision plus the approved N1/N2 wording fixes.
- Independent source/legal/API review is required before any RED or implementation work.
- No provider/network access, RED, runtime/source/model edit, push, capability claim, or close is
  authorized by this packet.

## Bottom summary

- Choose an SGP-only IMF gate for growth, inflation, and unemployment before cache/transport.
- WDI remains primary; healthy WDI results and all eight annual mappings remain unchanged.
- Direct IMF fetch/identity raise exact `InvalidData`; public skips create no IMF attempt.
- Non-SGP IMF behavior, source order, VNM policy routing, and custom/hookless sources are preserved.
- `get_indicator`, `IndicatorSeries`, models, diagnostics, warnings, and status tokens stay exact.
- Accept one additive `IMFDataMapperSource.supports_country()` API-snapshot entry.
- SingStat and a Singapore policy-rate proxy remain unregistered and blocked.
- The complete twelve-case matrix is mandatory after a separate RED/build authorization.
- This packet uses retained evidence only and makes no network, RED, code, push, or close action.
