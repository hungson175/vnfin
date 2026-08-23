# #224 design note — daily EUR/VND FX history

**Packet:** `tasks/224-daily-eurvnd-fx-history-spec.md` at reviewer `b8ee1e5`
**Design phase:** source/design only
**Disposition:** **SOURCE-GAP CLOSURE**
**Requested window:** inclusive `2018-01-01..2026-08-20`
**Economic identity:** direct EUR base / VND quote, **VND per 1 EUR**
**Research:** [`docs/research/2026-08-23-daily-eurvnd-fx-history-source-vetting.md`](../docs/research/2026-08-23-daily-eurvnd-fx-history-source-vetting.md)

This note records a conservative source/legal design. It does not add a provider, public model
field, diagnostic carrier, RED test, or runtime capability. The daily chain remains empty.

## 1. Decision and compatibility boundary

No provider/route/basis unit proves direct EUR/VND identity, requested coverage, bounded runtime,
and lawful reuse as one conjunction. The correct outcome is source-gap closure:

- no `Frequency.DAILY` EUR/VND implementation or source registration;
- no USD-cross, midpoint, spot, annual, cash/transfer/sell, current-only, forward, fill,
  interpolation, resampling, nearest-match, or cross-provider stitch;
- no API response is treated as an absence oracle; and
- no RED, production code, push, or issue close before an exact design PASS.

The current API boundary stays exact:

| Contract | Required current behavior |
| --- | --- |
| `vnfin.fx.history` | Existing signature and pre-network validation remain unchanged. |
| Default | `Frequency.ANNUAL`. |
| Current source | World Bank WDI `PA.NUS.FCRF`, annual USD/VND period average. |
| Daily EUR/VND | Typed `InvalidData` rejection before source access. |
| Models | Existing `FXPoint`/`FXHistory` remain unchanged; no duplicate model. |
| `Frequency` | No export/snapshot change in this source-gap packet. |
| Accessors | `rate_on()` exact-only; `rate_for_year()` remains annual-only. |
| Diagnostics | Existing offline annual diagnostics remain unchanged; no fabricated attempt carrier. |
| Spot | Existing spot adapters and legal scope are untouched. |

The v0.2.0 tag is `2fe50df4f27064140ff9f7a680227a2b337ec74a` and has spot `get_rate()` only.
The current published base at handoff is `origin/master=728bb99`; the packet's earlier
`c646c37` snapshot is intake context, not a new source or capability.

## 2. Candidate dispositions

| Candidate | Independent result | Disposition |
| --- | --- | --- |
| Vietcombank current/dated family | Current page lists EUR and separate cash/transfer/sell quotes, but no retained historical response, direct basis/date/revision, full span, or reuse/rate policy. | `COVERAGE_GAP` + `BASIS_GAP` + `IDENTITY_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| SBV cross-rate product | Official catalogue describes a weekly VND cross-rate product for tax calculation; no daily direct EUR/VND response or reuse contract. | `COVERAGE_GAP` + `BASIS_GAP` + `IDENTITY_GAP` + `LEGAL_GAP` |
| ECB reference roster | Current official EUR roster has no VND; framework allows USD-cross construction, which fails direct-only identity. | `NOT_SERVED` + `BASIS_GAP` |
| Frankfurter unfiltered | Official facade blends providers by default; VND catalogue presence does not prove one direct owner field/basis or rights. | `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| Frankfurter `ECB` provider | Provider documentation is not a direct ECB VND response, and ECB's inspected roster has no VND. | `NOT_SERVED` or `IDENTITY_GAP`; not qualified |
| BIS bilateral | Official bilateral dataset is against USD and combines sources; wrong pair/basis. | `IDENTITY_GAP` + `BASIS_GAP` |
| World Bank | Annual period-average local currency per US dollar; existing annual source only. | `NOT_SERVED` + `BASIS_GAP` |
| Federal Reserve/FRED | Previously reviewed negative controls are USD-based or wrong-pair; no new request made. | `NOT_SERVED` + `IDENTITY_GAP` |

The candidate matrix is not a failover chain. The daily chain is `()` until one complete unit
qualifies.

## 3. No-probe evidence contract

This handoff performed only bounded page/document reading against official primary sources.
There were **0 logical retrievals, 0 physical API calls, 0 retries, and 0 retained responses**.
No credentials, cookies, browser session, proxy, query-bearing URL, live rate, raw body, raw
headers, exception, digest, or provider artifact is stored.

Evidence fields are typed as follows until a future successful owner response exists:

```text
response_pair       = NOT_RETAINED
response_field      = NOT_RETAINED
response_direction  = NOT_RETAINED
response_scale      = NOT_RETAINED
response_date       = NOT_RETAINED
response_revision   = NOT_RETAINED
served_bounds       = NOT_RETAINED
page_or_cursor      = NOT_RETAINED
complete_mime       = NOT_RETAINED
effective_route     = NOT_RETAINED
```

These values mean “not obtained in this no-probe design round,” never “empty,” “not served,” or
“covered.” `NOT_SERVED` is reserved for official catalogue/roster evidence about the exact unit;
`COVERAGE_GAP` requires a qualified provider's declared or response-backed boundary.

## 4. Future qualification unit

One qualification unit is exactly:

```text
named provider owner + canonical route/version + one response field
 direct EUR/VND identity + one provider economic basis
 VND per 1 EUR direction/scale + observation/publication/revision semantics
 requested or provider-declared partial bounds + legal/runtime contract
```

The response must establish its own identity. A URL, query parameter, title, currency list,
numeric agreement, or caller inversion is insufficient. Cash, transfer, sell, central, bilateral,
period-average, market-close, and blended values are separate bases. A future source cannot be
accepted merely because its unit string can be formatted as `VND per 1 EUR`.

If one unit qualifies, it is the sole source for the whole request. Two-source failover is allowed
only if two independent units prove identical basis, calendar, date, revision, and publication
semantics. Providers are never stitched by date. Until then, do not create `SourceAttempt`,
`rate_basis`, provider metadata, or a source registry entry.

## 5. Future request/result contract (non-authoritative)

After a fresh implementation authorization only, the exact in-scope call is:

```python
vnfin.fx.history(
    "EUR", "VND", date(2018, 1, 1), date(2026, 8, 20),
    frequency=Frequency.DAILY,
)
```

The future design gates are:

1. `base == "EUR"`, `quote == "VND"`, and `frequency == Frequency.DAILY` are validated before
   network; both bounds are required plain `datetime.date` values, inclusive, non-reversed, and
   within the approved request window;
2. malformed, missing, reversed, excessive, unknown, unsupported-pair, and unsupported-frequency
   inputs fail closed before any provider call;
3. every row is a provider observation in the requested window, ascending and unique, with a
   finite positive non-boolean rate and `unit == value_unit == "VND per 1 EUR"`;
4. observation date, publication date, revision date, and `fetched_at_utc` remain distinct;
   `fetched_at_utc` is retrieval time only. Without provider publication timestamps, no same-day
   availability or Vietnam-session cutoff is asserted, and caller documentation uses a
   strict-prior rule;
5. provider-owned calendar/status evidence is required for weekends, holidays, or declared
   nonpublication; unexplained gaps, duplicates, out-of-window rows, missing requested endpoints,
   empty responses, and unreconciled pages fail the whole source with no partial history; and
6. `rate_on()` remains exact-match-only; `rate_for_year()` rejects daily histories and never
   treats a daily Jan-1 point as an annual observation.

Any future public `rate_basis`, coverage result, warning tuple, error carrier, or attempt carrier
requires an additive compatibility review covering constructor defaults/positional callers,
`DataFrame.attrs`, snapshots, repr/equality, serialization, diagnostics, docs, and release
notes. No such field is frozen here.

## 6. Coverage and no-false-absence contract

The future result dispositions are conjunctive:

| Result | Exact meaning |
| --- | --- |
| `FULL` | Provider-served bounds cover both request endpoints; all page/count/cursor and calendar reconciliation passes. |
| `QUALIFIED_PARTIAL` | Provider declares a narrower bound; every other identity, basis, legal, and runtime axis passes; the narrower bound is surfaced and never presented as full requested coverage. |
| `NOT_SERVED` | Official provider catalogue/owner evidence says the exact direct unit is not published; it is not inferred from an empty response. |
| `SOURCE-GAP` | At least one required axis remains unproven; daily chain stays empty. |

These are unresolved failures, not absence:

```text
empty/WAF response; timeout/TLS/connection; redirect/effective-route mismatch;
wrong/missing MIME or unexpected status; schema/identity/basis failure;
page/count/cursor mismatch; duplicate/out-of-window row; budget or byte exhaustion;
missing requested endpoint; unexplained internal gap
```

No unresolved result can be returned as a successful empty series or a coverage warning. No
weekend/holiday row may be fabricated, shifted, forward-filled, backfilled, interpolated,
resampled, or synthesized through USD.

## 7. Future bounded transport and diagnostics

Numeric ceilings remain **unfrozen** until one candidate supplies a documented route, page/cursor
contract, body bound, and rate policy. The mechanics are fixed:

- one request-scoped sequential ledger globally bounds logical source attempts, physical calls,
  pages/cursors, retries, redirects, and decompressed bytes;
- each physical dispatch atomically reserves its source/page/retry/physical units before transport;
  failed reservation means zero network calls;
- streamed decompressed bytes are charged after dispatch; byte overflow returns no partial result;
- hidden client retries, date-per-call fan-out, concurrency, unbounded redirects, and cross-source
  stitching are forbidden;
- exhaustion retains only bounded sanitized real attempts and never fabricates a final attempt or
  `diagnostics_truncated`; and
- an owner-approved rate/pacing policy is a prerequisite, not a number imported from another
  provider or from current spot behavior.

For a future JSON route, parse the complete `Content-Type` value after the first colon, normalize
the media-type portion by trimming/lower-casing, and require exact `application/json`. HTML/XML,
missing/malformed media types, or a colon-suffixed non-JSON media type fail closed. A provider
route using another media type needs a separate exact parser contract.

The future internal failure vocabulary is closed for design purposes only and is not a current
public API:

```text
ok, unexpected_http_status, mime_mismatch, redirect, effective_route_mismatch,
timeout, tls_error, rate_limited, server_error, waf_challenge, body_limit,
json_parse_error, schema_error, identity_mismatch, basis_mismatch,
duplicate_or_overlap, page_reconciliation_error, out_of_window_date,
missing_requested_endpoint, unexplained_gap, budget_exhausted
```

Raw URL/query, body, header, exception, cookie, credential, provider prose, and live rate never
enter public diagnostics. Public sanitized status/warning names require a fresh API review.

## 8. Legal/runtime reopen gate

All criteria are conjunctive. Reopen only when one named provider/route/basis supplies:

1. official owner identity and response-backed direct EUR/VND field, direction, scale, basis, and
   observation/publication/revision semantics;
2. strict MIME/status/effective-route behavior, bounded body/decompression, no private endpoint,
   proxy bypass, challenge solving, login, or paid credential;
3. requested endpoints or an owner-declared partial boundary, complete page/count/cursor
   reconciliation, duplicate/out-of-window checks, and provider-calendar evidence;
4. finite owner-approved logical/physical/page/retry/redirect/byte ceilings with atomic
   reservation/exhaustion and no-false-partial behavior;
5. explicit answers for automated access, caller-facing return, storage/cache, redistribution,
   attribution, commercial use, rate/retry/pacing, and revision/correction/retention;
6. annual USD/VND compatibility and an additive model/facade/diagnostic plan; and
7. a new exact-SHA source-design PASS followed by a separate RED-first implementation review.

The public SBV/VCB/ECB/Frankfurter pages are contact/evidence leads only. They do not grant
permission. This source-gap design does not authorize a probe, RED, runtime change, push, or
close.

## 9. Publication boundary and lifecycle

If the reviewer grants a docs-only SOURCE-GAP design PASS, publish exactly these three paths from
the clean approved ancestry through the exact returned anchor:

```text
docs/research/2026-08-23-daily-eurvnd-fx-history-source-vetting.md
tasks/224-design-note.md
tasks/active-backlog.md
```

Then rerun merged docs/full/build/blacklist/secret/diff/path gates, verify the exact remote
anchor/ancestry/paths, post a clean no-capability SOURCE-GAP resolution, and close/re-read #224
only under the reviewer-approved sequence. A source-gap docs PASS never authorizes RED, model or
accessor changes, source registration, daily capability, or a new implementation line.

## 10. Sources

- [Vietcombank official rate page](https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia)
- [State Bank of Vietnam official portal](https://www.sbv.gov.vn/)
- [SBV official statistical-product catalogue](https://www.sbv.gov.vn/documents/d/sbv_portal/527697)
- [ECB euro reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
- [ECB reference-rate framework](https://www.ecb.europa.eu/stats/pdf/exchange/Frameworkfortheeuroforeignexchangereferencerates.en.pdf)
- [ECB Data Portal exchange-rate overview](https://data.ecb.europa.eu/key-figures/ecb-interest-rates-and-exchange-rates/exchange-rates)
- [Frankfurter v2 documentation](https://frankfurter.dev/)
- [Frankfurter providers](https://frankfurter.dev/providers/)
- [Frankfurter ECB provider](https://frankfurter.dev/providers/ecb/)
- [Frankfurter currency catalogue](https://frankfurter.dev/currencies/)
- [Frankfurter VND currency page](https://frankfurter.dev/currencies/vnd/)
- [Frankfurter v2 changelog](https://github.com/lineofflight/frankfurter/blob/main/CHANGELOG.md)
- [BIS bilateral exchange-rate overview](https://data.bis.org/topics/XRU)
- [BIS exchange-rate statistics](https://www.bis.org/statistics/dataportal/exr.htm)
- [World Bank `PA.NUS.FCRF`](https://data.worldbank.org/indicator/PA.NUS.FCRF)
- [Federal Reserve H.10](https://www.federalreserve.gov/releases/h10/current/)
- [FRED DEXCHUS](https://fred.stlouisfed.org/series/DEXCHUS)
- [Prior reviewed #217 source note](../docs/research/2026-08-23-daily-cnyvnd-fx-history-source-vetting.md)

## Bottom summary

- Disposition: **SOURCE-GAP CLOSURE**; daily EUR/VND chain remains empty.
- No source route was probed: 0 logical calls, 0 physical calls, 0 retries, no live data.
- Direct VND-per-1-EUR identity, basis, coverage, runtime, and legal axes are unproven.
- Current annual USD/VND facade/models/diagnostics remain unchanged.
- Future budgets stay numeric-unfrozen but require atomic global reservation and fail-closed exhaustion.
- No USD cross, spot/annual substitution, fill, stitch, or false-absence inference is allowed.
- Reopen requires all identity, coverage, runtime, legal, and compatibility gates plus a fresh PASS.
- No RED, code, push, or close before exact design approval.
