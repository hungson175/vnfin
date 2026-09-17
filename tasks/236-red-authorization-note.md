# #236 RED-authorization packet — SGP IMF country gate

**Date:** 17 September 2026 (+07)

**Phase:** `RED_AUTHORIZATION` — test authorization request only

**Status:** `PROPOSED_FOR_REVIEW`; RED is **not authorized** and this packet contains no feature
test, fixture, implementation, runtime/API/model change, or capability claim

**Clean published base:** `8d450a40cd9763a58bdb85c5f125edcc18d182da`

**Source/design prerequisite:** APPROVE_WITH_NOTES at exact
`631410a2d95cf27aaff43791e5b041fc853b9de2`, delivery `e750b5a5`, reviewer `b9ae587`.

**API/model prerequisite:** PASS at exact
`5bfb8575352bb1ff4e5233ad49fbf1f0b3723435`, delivery `5215cb5b`, reviewer `8742ffe`, report
`review-202609172105-issue236-scanner-api-model-PASS.md`. The PASS approves the corrected decision
in `tasks/236-api-model-decision-note.md` and its complete twelve-case matrix. Backlog commit
`e4e0f387f40d395651ffb4d78a67c4ff0bf19d35` records the PASS before this packet.

## Exact authorization requested

Authorize one later, separately committed **RED test manifest** implementing only the tests named
below. That future commit must:

1. add/modify only offline tests and minimal synthetic helpers;
2. keep every `CURRENT_CHARACTERIZATION` test green on the pre-implementation tree;
3. make every `MUST_FAIL_AT_RED` test fail for the exact missing SGP-gate/API/docs reason below;
4. run and record the focused current-characterization and intended-failure groups separately;
5. contain no production, runtime, public-snapshot baseline, documentation, provider, or network
   change; and
6. return its exact SHA for a distinct reviewer verdict before any implementation.

Implementation, refactor, provider access, source registration, snapshot regeneration, push,
capability claim, and issue close remain separately gated. This packet does not itself authorize or
write RED.

## Clean-room, fixture, and zero-network boundary

`docs/vnstock-blacklist.md` remains binding. No blacklisted package, repository, endpoint map,
schema, fixture, name, behavior, or derived material is used. No research or provider request is
performed for this packet.

Every future test in this manifest is hermetic:

- use only fabricated values, display names, dates, and minimal response envelopes;
- retain official identifiers only where routing/identity itself is the contract (`SGP`, exact WDI
  and IMF codes); never copy a real provider observation row;
- inject `http_get` and record every call; no default transport may be reachable;
- for preflight/direct guards, also replace the instance's `_request_text` with a raising tripwire
  so a raw-cache lookup fails the test even if the HTTP counter stays empty;
- never use live cassettes, keys, logins, redirects, DNS, sockets, or provider endpoints; and
- do not convert retained source/legal/bounds evidence into invented runtime validation.

`0 transport/cache` below means both the injected HTTP calls list remains `[]` and the raising
`_request_text` tripwire is untouched. `1 injected response` is not a network call.

## Classification and exact carrier vocabulary

- `CURRENT_CHARACTERIZATION`: must pass before implementation and remain green afterward. A failure
  is a regression or a bad test, not intended RED evidence.
- `MUST_FAIL_AT_RED`: asserts approved new behavior that the current implementation lacks. It must
  fail before production code, for the reason named in the ledger.

The exact new direct-route exception is:

```text
InvalidData("imf_datamapper: {indicator} route is not qualified for country=SGP")
```

where `{indicator}` is exactly `gdp_growth`, `inflation`, or `unemployment`.

The exact new IMF-only public carrier is:

```python
AllSourcesFailed(f"SGP/{indicator.value}", None, ())
```

with exact string
`all sources failed for SGP/{indicator.value} None -> no sources attempted`.

For a WDI-empty default request, the sole attempt is exactly:

```python
SourceAttempt(
    "worldbank",
    False,
    "EmptyData: worldbank: no observations in requested window "
    f"for SGP/{wdi_code}",
)
```

Skipped IMF is absent from attempts and warnings. It is never `NO_DATA`, `EmptyData`,
`SourceUnavailable`, or an IMF failure.

## Normative twelve-case ledger

Every approved matrix case in `tasks/236-api-model-decision-note.md` is present. A row with both
statuses deliberately separates existing compatibility from the new behavior; it does not allow a
current assertion to be counted as an intended RED failure.

| Case | Status | Exact future test(s) | Exact carrier / intended RED reason | Zero-network seam |
|---|---|---|---|---|
| 1. Eight WDI primaries | `CURRENT_CHARACTERIZATION` | `tests/test_macro_worldbank.py::test_sgp_eight_wdi_primaries_preserve_exact_contract`; `tests/test_docs_contract.py::test_issue236_sgp_wdi_bounds_and_historical_rate_caveats_are_retained` | Successful WDI `IndicatorSeries`; retained bounds/revision/lag statements are static evidence, not runtime rows | One fabricated injected WDI response per parameter; no live call. Docs test reads repository files only |
| 2A. WDI malformed/empty paths | `CURRENT_CHARACTERIZATION` | Retain existing named WDI guards; add `tests/test_macro_worldbank.py::test_sgp_wdi_boolean_value_keeps_invalid_data_carrier` | Existing `InvalidData`/`EmptyData` carriers remain exact; null observations remain skipped and are not redefined | One fabricated injected response; no live call |
| 2B. Gated WDI failure | `MUST_FAIL_AT_RED` | `tests/test_macro_failover.py::test_sgp_gated_wdi_failure_has_only_wdi_attempt_and_no_imf_transport` | Current tree reaches IMF; required result is `AllSourcesFailed` with the one exact WDI attempt above | WDI gets one fabricated empty response; IMF `_request_text` tripwire and HTTP counter remain untouched |
| 3A. IMF provider predicate/API | `MUST_FAIL_AT_RED` | `tests/test_macro_imf.py::test_sgp_gated_supports_country_is_quiet_false`; `::test_imf_supports_country_quiet_false_for_malformed_or_unmapped_inputs`; `::test_imf_supports_country_preserves_eligible_pairs`; `::test_imf_three_entrypoints_share_one_canonical_pair_predicate` | Current class lacks `supports_country()` and the shared pair gate | Pure calls/spies; 0 transport/cache |
| 3B. Direct IMF fetch and identity | `MUST_FAIL_AT_RED` | `tests/test_macro_imf.py::test_sgp_gated_direct_fetch_rejects_canonical_country_forms_before_cache_transport`; `::test_sgp_gated_identity_rejects_canonical_country_forms`; `tests/test_macro_contracts.py::test_imf_identity_mapped_indicator_newly_validates_country` | Current calls dispatch/advertise tuples; required carrier is exact route `InvalidData`, or existing exact ISO3 `InvalidData` for malformed mapped identity | Raising `_request_text` plus HTTP counter for fetch; identity is pure; all 0 |
| 3C. Existing precedence/compatibility | `CURRENT_CHARACTERIZATION` | `tests/test_macro_imf.py::test_imf_fetch_mixed_invalid_remains_country_first_before_transport`; `::test_imf_identity_mixed_invalid_remains_indicator_mapping_first`; `::test_imf_eligible_non_sgp_identity_tuple_is_unchanged`; `::test_sgp_imf_gdp_remains_unit_filtered_without_transport` | Current exact `InvalidData` precedence and eligible tuples stay green; GDP keeps zero-attempt public carrier after unit filter | Pure validation or raising transport; 0 transport/cache |
| 3D. Public IMF-only/cache path | `MUST_FAIL_AT_RED` | `tests/test_macro_failover.py::test_sgp_gated_imf_only_has_exact_zero_attempt_carrier_before_cache_transport` | Current tree calls IMF; required exact empty-attempt `AllSourcesFailed` | Test-only cache-enabled IMF instance; raising `_request_text`; HTTP list `[]` |
| 4. Non-SGP IMF projections | `CURRENT_CHARACTERIZATION` | Modify/rename existing projection tests to `tests/test_macro_imf.py::test_non_sgp_projection_boundary_warning_and_latest_are_exact` and `::test_non_sgp_historical_series_has_no_projection_boundary` | Successful non-SGP IMF `IndicatorSeries`; exact projection warning and `latest()` behavior unchanged | Frozen clock and one fabricated injected IMF response; no live call |
| 5. No repair/stitching | `CURRENT_CHARACTERIZATION` | `tests/test_macro_failover.py::test_macro_failover_never_stitches_partial_wdi_and_imf_points`; `::test_non_sgp_wdi_failure_returns_whole_imf_series_not_mixed_points`; retain the three existing unit-filter/relabel guards named below | Whole first successful provider series only; no point repair, fill, relabel, frequency conversion, or cross-source merge | Synthetic sources/injected responses only; call-order counters |
| 6. Missing SGP monthly CPI YoY | `CURRENT_CHARACTERIZATION` | `tests/test_macro_failover.py::test_sgp_cpi_yoy_default_chain_has_exact_zero_attempt_carrier_before_cache_transport` | Exact `AllSourcesFailed("SGP/cpi_yoy", None, ())`; exact no-sources string; no SingStat attempt | Every built-in `_request_text` is a raising tripwire; all HTTP lists `[]` |
| 7. Missing SGP policy rate | `CURRENT_CHARACTERIZATION` | `tests/test_macro_failover.py::test_sgp_policy_rate_default_chain_has_exact_zero_attempt_carrier_and_no_proxy_route`; docs half in case 12 | Exact `AllSourcesFailed("SGP/policy_rate", None, ())`; exact no-sources string; no proxy source/attempt | Every built-in `_request_text` is a raising tripwire; all HTTP lists `[]` |
| 8A. Country-aware custom monthly/false hook | `CURRENT_CHARACTERIZATION` | `tests/test_macro_failover.py::test_sgp_missing_monthly_cells_accept_truthful_country_aware_custom_source`; `::test_sgp_false_country_hook_is_skipped_before_fetch_cache_transport_and_attempt_accounting` | Truthful custom result stays eligible; false-hook source makes no attempt | Synthetic custom source only; false hook has raising fetch/cache tripwires |
| 8B. Country-aware custom after annual WDI failure | `MUST_FAIL_AT_RED` | `tests/test_macro_failover.py::test_sgp_gated_annual_imf_skip_preserves_truthful_custom_source_and_attempt_trail` | Current tree reaches IMF; required result is custom, IMF absent, warning exactly WDI failure then custom `ok` | WDI one fabricated empty response; IMF tripwire/HTTP `[]`; custom one synthetic call |
| 9. Hookless custom | `CURRENT_CHARACTERIZATION` | `tests/test_macro_failover.py::test_sgp_hookless_custom_source_remains_eligible_in_caller_order` | Existing hookless eligibility plus canonical unit/identity/result guards remain green | Synthetic custom only; 0 provider/cache/HTTP |
| 10. Other countries | `CURRENT_CHARACTERIZATION` | `tests/test_macro_failover.py::test_non_sgp_three_percent_indicators_keep_wdi_to_imf_fallback`; retain the four named VNM policy tests; eligible identity is covered by case 3C | WDI empty attempt then successful whole IMF series; exact percent/annual identity; VNM route unchanged | Fabricated WDI/IMF responses and counters only; no live call |
| 11. SingStat boundary | `CURRENT_CHARACTERIZATION` | `tests/test_macro_failover.py::test_singstat_remains_absent_from_default_source_registry_and_exports`; `tests/test_public_api_surface.py::test_singstat_remains_absent_from_live_and_committed_public_surface` | No source, module export, registry member, or public-surface entry; the alternate full SingStat contract is not selected | Static introspection/files only; 0 provider/cache/HTTP |
| 12A. Additive IMF method surface | `MUST_FAIL_AT_RED` | `tests/test_public_api_surface.py::test_imf_supports_country_is_frozen_as_exact_additive_surface` | Live class currently lacks the approved method; later exact signature is `(self, country_iso3, indicator) -> bool`, additive with zero breaking changes | Introspection/surface builder only; 0 network |
| 12B. Runtime docs/skill/CHANGELOG | `MUST_FAIL_AT_RED` | `tests/test_docs_contract.py::test_issue236_sgp_imf_gate_docs_skill_and_changelog_are_in_lockstep`; `::test_issue236_sgp_missing_monthly_cells_remain_missing_without_proxy_substitution` | Runtime docs do not yet disclose the three-pair exception, skipped-attempt meaning, identity narrowing, and missing-without-proxy boundary | Repository text only; 0 network |
| 12C. Existing hermetic/security gates | `CURRENT_CHARACTERIZATION` | Existing public-surface, secret-scan, warning-token, VNStock-blacklist, docs, and full-suite tests; exact commands below | Must remain green; these are gates, not intended RED failures | Local files/synthetic tests only; provider access forbidden |

## Exact case details and test data

### Cases 1–2 — WDI remains the primary and sole recorded failing attempt

`test_sgp_eight_wdi_primaries_preserve_exact_contract` is parameterized exactly as follows:

| Indicator | WDI code | Unit | Currency |
|---|---|---|---|
| `GDP` | `NY.GDP.MKTP.CD` | `current US$` | `USD` |
| `GDP_GROWTH` | `NY.GDP.MKTP.KD.ZG` | `%` | `None` |
| `CPI` | `FP.CPI.TOTL` | `index` | `None` |
| `INFLATION` | `FP.CPI.TOTL.ZG` | `%` | `None` |
| `UNEMPLOYMENT` | `SL.UEM.TOTL.ZS` | `%` | `None` |
| `LENDING_RATE` | `FR.INR.LEND` | `%` | `None` |
| `DEPOSIT_RATE` | `FR.INR.DPST` | `%` | `None` |
| `REAL_INTEREST_RATE` | `FR.INR.RINR` | `%` | `None` |

Each parameter gets two fabricated newest-first rows carrying exact `countryiso3code="SGP"` and
the exact indicator code, plus a fabricated display name. Assert one injected call to the exact WDI
route; `source="worldbank"`; annual frequency; exact unit/currency; finite, ascending, unique Jan-1
points; and no projection boundary. No observed Singapore values are fixtures.

Retain these existing WDI characterization tests by exact name:

- `test_worldbank_observation_country_mismatch_raises_invalid`
- `test_wb_rejects_mismatched_observation_indicator_id`
- `test_null_obs_value_skipped_not_invalid`
- `test_all_null_values_raise_empty`
- `test_malformed_scalar_value_raises_invalid`
- `test_nan_value_raises_invalid`
- `test_out_of_window_year_raises_empty`
- `test_wb_rejects_duplicate_observation_date`

The docs characterization pins retained statements for observed bounds, no observed interior gaps,
revision lineage `NOT_RETAINED`, and the three 2021-ending rate series as historical-only. It does
not add runtime gap, revision, staleness, or completeness semantics. Specifically, interior null
observations remain skipped by the current adapter; that behavior is not silently inverted.

For case 2B, parameterize only the gated triple and exact code pairs:

```text
gdp_growth   -> NY.GDP.MKTP.KD.ZG -> NGDP_RPCH
inflation    -> FP.CPI.TOTL.ZG    -> PCPIPCH
unemployment -> SL.UEM.TOTL.ZS    -> LUR
```

WDI returns a fabricated empty envelope. A fabricated successful IMF payload is installed only as a
sentinel demonstrating that the current tree would wrongly reach it. Required RED assertion is the
exact one-WDI-attempt carrier in the vocabulary section and `imf_calls == []`.

### Case 3 — exact predicate, precedence, direct/public carriers, and cache seam

The approved private implementation seam is frozen for testability as one instance method:

```python
IMFDataMapperSource._supports_country_pair(
    self,
    country_iso3: str,
    indicator: MacroIndicator,
) -> bool
```

It receives only an already-canonical ISO3 and mapped canonical indicator. The shared-predicate RED
test spies on that single method and proves `supports_country()`, `get_indicator()`, and
`indicator_identity()` each pass the same canonical pair; there may be no duplicated three-pair
rule. This private seam is not exported or added to the public snapshot.

The following exact inputs are mandatory:

- all three gated indicators/codes with `"SGP"`, `"sgp"`, and `" SGP "`;
- malformed countries `None`, `""`, and `"SG"` crossed with raw unknown indicator
  `"not_an_indicator"` and canonical-but-unmapped `MacroIndicator.CPI` for both direct methods;
- the same three malformed countries crossed with every mapped gated indicator for the newly
  country-validating identity method;
- eligible country forms `"USA"`, `"usa"`, and `" USA "`, plus `SGP/GDP`.

`supports_country()` returns `False` without raising for every malformed/unknown/unmapped
combination. It returns `False` for the gated SGP triple and `True` for mapped non-SGP pairs and
`SGP/GDP`. The exact direct precedence retained at RED is:

| Call | Exact current and future outcome |
|---|---|
| fetch `(None, "not_an_indicator")` | `InvalidData("imf_datamapper: country must be a 3-letter ISO3 code, got NoneType")` |
| fetch `("SG", "not_an_indicator")` | `InvalidData("imf_datamapper: country must be a 3-letter ISO3 code, got 'SG'")` |
| fetch `("USA", "not_an_indicator")` | `InvalidData("imf_datamapper: unsupported indicator 'not_an_indicator'")` |
| fetch `("USA", CPI)` | `InvalidData("imf_datamapper: unsupported indicator cpi")` |
| identity `(None, "not_an_indicator")` | existing `macro: unknown macro indicator ...` `InvalidData` |
| identity `(None, CPI)` | `InvalidData("imf_datamapper: unsupported indicator cpi")` |
| identity `(None, GDP_GROWTH)` | **new** ISO3 `InvalidData` matching the first row's country carrier |
| direct fetch/identity `(canonicalized SGP, gated)` | **new** exact route-qualification `InvalidData` |

Eligible non-SGP identity tuples remain byte-equal:

```text
NGDP_RPCH / gdp_growth (NGDP_RPCH)
PCPIPCH   / inflation (PCPIPCH)
LUR       / unemployment (LUR)
```

`SGP/GDP` remains `True` at the provider predicate, while the public canonical GDP chain removes
IMF on the existing `USD bn` versus `current US$` unit mismatch and raises the existing
`AllSourcesFailed("SGP/gdp", None, ())` with zero IMF transport when IMF is the only configured
source. No IMF GDP substitution is permitted.

The public/direct cache tests instantiate `IMFDataMapperSource(http_get=fake_get)` normally and
then enable only the existing inherited raw cache on that test instance:

```python
HttpDataSource.__init__(
    source,
    http_get=fake_get,
    timeout=25.0,
    cache_ttl=60.0,
    clock=lambda: 1000.0,
)
```

They then monkeypatch `source._request_text` to raise. The RED commit must not add a cache argument
to the IMF production constructor, introduce a parsed-result cache, or use a disconnected call
counter as cache proof.

### Cases 4–5 and 10 — non-SGP behavior is characterization, never the RED target

Freeze the UTC year in both projection tests. A fabricated non-SGP IMF series spanning the prior,
current, and next years has:

- `projection_from_year == frozen_year`;
- exact warning
  `imf_weo: years >= {year} are WEO projections (forecasts), excluded from latest()`;
- `latest()` equal to the final prior-year point; and
- `latest_including_projections()` equal to the final fabricated forecast.

A historical-only fixture has no projection boundary or warning.

No-stitch tests prove both branches: a nonempty WDI series wins whole and IMF is untouched; after a
non-SGP WDI `EmptyData`, the returned series contains only IMF's fabricated points and preserves the
WDI-failure/IMF-success failover warning. Retain these existing exact unit guards:

- `test_noncanonical_unit_source_is_filtered_out_not_raised`
- `test_reject_reason_refuses_to_relabel_a_drifted_unit`
- `test_default_gdp_chain_does_not_raise_unit_mismatch`

`test_non_sgp_three_percent_indicators_keep_wdi_to_imf_fallback` parameterizes the three gated
indicators over `USA` and fixture-only valid ISO3 `ZZZ`: one injected WDI empty response, then one
injected IMF success, exact IMF identity, `%`, annual frequency, no currency, and no mixed points.
Retain the current VNM policy characterizations:

- `test_policy_rate_resolves_dbnomics_only_monthly`
- `test_policy_rate_direct_non_vnm_guard_fails_before_transport`
- `test_policy_rate_indicator_identity_non_vnm_guard_is_exact`
- `test_policy_rate_non_vnm_guard_runs_before_enabled_cache`

Nothing in these tests legally qualifies IMF elsewhere; they freeze out-of-scope compatibility.

### Cases 6–9 — missing monthly cells and custom-source invariants

Cases 6 and 7 assert exact exception fields and strings, not only exception type. Their tripwires
cover each configured built-in source's inherited cache/transport path. They also assert the result
has no attempts, so a skipped source cannot be misreported as an empty or failed provider.

The case-7 static docs test enumerates forbidden substitutions: SORA, interbank/facility rates,
lending/deposit rates, bond yields, and FX or currency-index proxies. These are documentation
boundaries, not executable source candidates.

The case-8 annual MUST_FAIL test uses `[WDI, IMF, country-aware custom]` and one gated indicator.
WDI supplies the exact empty carrier, IMF is never cache-checked or fetched, custom is called once,
and the returned warning is exactly:

```text
failover: worldbank:EmptyData: worldbank: no observations in requested window for SGP/{wdi_code}; qualified-custom:ok
```

The monthly custom characterization is parameterized over `CPI_YOY` and `POLICY_RATE`. The false
country hook and hookless tests retain the existing optional-hook contract and all identity/unit/
result guards. No custom result is relabelled or exempted from validation.

### Cases 11–12 — absence, public surface, docs, and integration gates

Because no SingStat source is introduced, only the absence branch of matrix case 11 is authorized.
The full alternate SingStat transport/table/row/MIME/redirect/paging contract is not RED scope and
cannot be mocked into a production-source claim.

The additive surface test uses `scripts/dump_api_surface.py`'s in-process builder and asserts only
the approved public method entry on `IMFDataMapperSource`: method kind, exact positional parameters
`self`, `country_iso3`, `indicator`, and return annotation `bool`. It also retains
`test_live_surface_introduces_no_breaking_changes`. The committed v0.2.0 baseline is not regenerated
in RED.

The docs lockstep tests scan the exact current/runtime-facing set that makes generic macro-chain
claims: `README.md`, `docs/api.md`, `docs/how-to/byok-fred.md`,
`docs/tutorials/macro-and-fx.md`, `docs/sources/macro-imf.md`,
`docs/sources/macro-worldbank.md`, `docs/sources/macro-dbnomics.md`,
`docs/sources/macro-fred.md`, `docs/ai-usage.md`, `docs/units.md`, `docs/roadmap.md`,
`docs/architecture/system-overview.md`, `docs/architecture/data-domains.md`,
`skills/vnfin/reference/domains.md`, and the new `CHANGELOG.md` entry. Historical research,
planning, design decisions, and prior changelog entries are not rewritten as if they were current
runtime instructions. Green implementation must disclose or link directly to a disclosure of:

- WDI remains first for all eight SGP annual indicators;
- IMF is country-gated only for the three exact SGP percent fallbacks;
- country-ineligible sources are absent from attempts by design, not `NO_DATA`;
- direct IMF identity newly validates country after indicator/mapping validation;
- non-SGP, VNM policy, custom, and hookless behavior remains unchanged; and
- monthly CPI YoY and policy rate remain missing with no SingStat registration or proxy.

No docs test may claim the feature exists while its MUST_FAIL runtime tests remain red.

After a later implementation commit, but not as part of RED, run these exact merged-tree gates:

```bash
python -m pytest tests/test_macro_worldbank.py tests/test_macro_imf.py \
  tests/test_macro_failover.py tests/test_macro_contracts.py \
  tests/test_public_api_surface.py tests/test_docs_contract.py tests/test_no_secrets.py -q
python -m pytest -q
python -m build --no-isolation
```

Also run the repository's VNStock-blacklist scan, inspect wheel/sdist membership for forbidden raw
evidence/secrets, and import the built wheel in an offline temporary environment. These are later
green/release gates, not additional RED behavior or provider access.

## Exact future RED result partition

The future RED handoff must report two partitions, never one ambiguous failing suite:

1. **Current-characterization partition:** every test marked `CURRENT_CHARACTERIZATION` passes on
   the pre-implementation tree.
2. **Intended RED partition:** only cases 2B, 3A/3B/3D, 8B, 12A, and 12B fail, because the SGP IMF
   predicate, direct/public gate, additive method, and runtime docs are not implemented.

An accidental provider call, a different exception, an unexpected failure in a current
characterization, a passing MUST_FAIL test, or a failure caused only by a missing import/helper is
not acceptable RED evidence. The shared-private-seam test may initially fail because the method is
absent, but the behavioral tests must independently demonstrate the missing gate; the manifest may
not consist only of `AttributeError` failures.

## Explicit non-authorizations

This packet does not authorize:

- production/source/API/model code or public snapshot baseline changes;
- provider/network access, research, live rows, cassettes, keys, or credential use;
- SingStat, MAS, or data.gov.sg adapter/source registration;
- IMF legal qualification, global IMF removal, source-order change, or another-country gate;
- a new diagnostic/status/warning/exception/model field;
- runtime gap/revision/staleness checks not already implemented;
- repair, stitching, interpolation, derivation, relabelling, proxy substitution, or frequency change;
- docs claiming shipped capability before green implementation approval; or
- push, publication, release, capability claim, or issue close.

## Lifecycle and next gate

- API/model PASS was recorded before this packet at exact `e4e0f387f40d395651ffb4d78a67c4ff0bf19d35`.
- Current artifact is docs/backlog only and uses retained evidence; no network is accessed.
- Next actor after commit is `vnfin-oss-reviewer`.
- Next action is `RETURN_EXACT_RED_AUTHORIZATION_VERDICT`.
- Until explicit authorization, no feature RED test or fixture may be written.
- After authorization, RED itself is a separate exact-SHA handoff; implementation remains blocked.

## Bottom summary

- Request authorization only for a later offline synthetic RED test commit.
- All twelve approved matrix cases map to exact tests and named carriers.
- Current WDI, non-SGP IMF, VNM policy, missing-monthly, and custom behavior stay green.
- Intended RED is limited to the SGP IMF skip/direct gate, shared predicate, API method, and docs.
- Gated public failures omit IMF and retain only the exact WDI attempt, or zero attempts for IMF-only.
- Direct gated calls raise the exact approved `InvalidData` before raw-cache lookup or HTTP.
- No SingStat/MAS/data.gov source, proxy, stitching, new model, or legal qualification is introduced.
- RED, implementation, network access, push, capability claim, and close remain unauthorized.
