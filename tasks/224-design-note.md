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
| Accessors | `rate_on()` is exact-only. Current facade histories are annual, but `rate_for_year()` is currently Jan-1 sugar over `rate_on()` without a frequency guard; future daily code must add explicit non-annual rejection. |
| Diagnostics | Existing offline annual diagnostics remain unchanged; no fabricated attempt carrier. |
| Spot | Existing spot adapters and legal scope are untouched. |

The v0.2.0 tag is `2fe50df4f27064140ff9f7a680227a2b337ec74a` and has spot `get_rate()` only.
The current published base at handoff is `origin/master=728bb99`; the packet's earlier
`c646c37` snapshot is intake context, not a new source or capability.

## 2. Candidate dispositions

Each row is an independent provider/route/version/basis unit. The full transport and ten-axis
legal ledgers are in the research artifact §§3–4; this design note repeats their deterministic
outcomes so no unit is silently collapsed into a failover candidate.

| Candidate unit | Evidence boundary | Deterministic disposition |
| --- | --- | --- |
| VCB EUR cash / transfer / sell | Current page has distinct quote columns; no historical response identity, direct basis, bounds, or reuse/runtime contract | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` per field |
| SBV central VND/USD and reference-rate units | Official product labels only; no direct daily EUR/VND response or reuse/runtime contract | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` per unit |
| SBV weekly tax cross-rate | Official catalogue says weekly tax-calculation product, not requested daily market history | `NOT_SERVED` + `BASIS_GAP` |
| ECB direct EUR/VND | Current official roster has no VND; USD-cross methodology is forbidden | `NOT_SERVED` + `BASIS_GAP` |
| Frankfurter unfiltered | Default is blended; VND catalogue is not direct owner/field/basis proof | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| Frankfurter `providers=ECB` | No provider-filter response; direct ECB/VND identity and rights remain unproven | `SOURCE-GAP` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| Frankfurter underlying-provider inventory | Complete provider inventory was not independently reviewed for this pair | `SOURCE-GAP` + `IDENTITY_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| BIS bilateral, World Bank annual, H.10, FRED | Wrong pair/basis/cadence or annual-only negative controls | Exact `NOT_SERVED`/`IDENTITY_GAP`/`BASIS_GAP` outcomes recorded in research §3.1 |
| `open.er-api` current endpoint | Current USD anchor, cross-derived, rate-limited, raw redistribution prohibited, no history | `NOT_SERVED` + `IDENTITY_GAP` + `BASIS_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |

`COVERAGE_GAP` is reserved for a qualified unit with an owner-declared or response-backed boundary
that excludes part of the requested range. No no-probe row above uses it. The daily chain is `()`
until one complete unit qualifies.

## 3. No-probe evidence contract

This handoff used two separate channels. Official pages, catalogues, PDFs, and documentation were
read as static evidence, but the research tool did not retain or measure the underlying web
transport log: static-document logical/physical counts are `NOT_RETAINED`/`NOT_MEASURED`, not zero.
No candidate EUR/VND data/API route, page/cursor, or retry was dispatched. Candidate dispatch is
exactly `0 / 0 / 0 / 0` for logical targets / physical calls / page-or-cursor calls / retries.

No credentials, cookies, browser session, proxy, query-bearing URL, live rate, raw body, raw
headers, exception, digest, or provider artifact is stored. Static page references are not HTTP
method claims and candidate zeroes do not describe static traffic or a provider's future allowance.

| Channel | Logical | Physical | Pages/cursors | Retries | Interpretation |
| --- | --- | --- | --- | --- | --- |
| Static official document research | `NOT_RETAINED` / `NOT_MEASURED` | `NOT_RETAINED` / `NOT_MEASURED` | `NOT_RETAINED` | `NOT_RETAINED` | Evidence inventory only |
| Candidate data/API dispatch | `0` | `0` | `0` | `0` | No candidate route was called |

Evidence fields remain typed as follows until a future successful owner response exists:

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

The future validation contract is:

1. `base == "EUR"`, `quote == "VND"`, and `frequency == Frequency.DAILY` are validated before
   network; both bounds are required plain `datetime.date` values, inclusive, non-reversed, and
   within the approved request window;
2. malformed, missing, reversed, excessive, unknown, unsupported-pair, and unsupported-frequency
   inputs fail closed before any provider call;
3. every row is a provider observation in the requested window, ascending and unique, with a
   finite positive non-boolean rate and `unit == value_unit == "VND per 1 EUR"`;
4. observation date, publication date, revision date, and `fetched_at_utc` remain distinct;
   without provider publication timestamps, no same-day availability or Vietnam-session cutoff is
   asserted, and caller documentation uses a strict-prior rule;
5. a provider calendar/status may explain a weekend, holiday, or declared nonpublication, yielding
   `NONPUBLICATION_RECONCILED` and no row. A publication-eligible requested date with no row is
   `missing_requested_endpoint` and fails the whole source. Empty responses, unknown calendar
   status, and unreconciled pages also fail the whole source and return no partial history; and
6. `rate_on()` remains exact-match-only; a future daily implementation must make `rate_for_year()`
   reject non-annual histories.

Any future public `rate_basis`, coverage result, warning tuple, error carrier, or provider attempt
carrier must be additive, finite, sanitized, snapshot-tested, and reviewed with annual
constructor/DataFrame/diagnostic compatibility. This source-gap packet does not add or promise one.

## 6. Coverage and no-false-absence contract

`FULL` is possible only when provider-served bounds cover both requested endpoints, or provider
calendar/status evidence proves an endpoint is a nonpublication, and page/count/cursor/calendar
reconciliation succeeds. `QUALIFIED_PARTIAL` requires a qualified provider-declared narrower bound
and all identity, basis, legal, and runtime axes; it must expose that bound and never imply requested
full coverage.

`COVERAGE_GAP` is only a qualified-provider disposition with a declared/response-backed boundary
that excludes part of the requested interval. No page inspection, empty response, timeout, WAF, or
unreconciled no-probe state can establish it. No current candidate is qualified, so this packet uses
`SOURCE-GAP` or exact `NOT_SERVED` instead.

```text
publication-eligible date + no row       -> missing_requested_endpoint (fatal, no series)
provider calendar/status says no publish -> NONPUBLICATION_RECONCILED (no row, not fatal)
unknown calendar/status                  -> unexplained_gap (fatal, no series)
empty/WAF/timeout/connection/unreconciled -> transport/schema failure (no absence claim)
```

No unresolved result can be returned as a successful empty series or as `NOT_SERVED`/`COVERAGE_GAP`.
No weekend/holiday row may be fabricated, shifted, filled, interpolated, resampled, or synthesized
through USD.

## 7. Future bounded transport and diagnostics

Numeric ceilings remain **unfrozen** until one candidate supplies a documented route, page/cursor
contract, body bound, and rate policy. The mechanics are fixed:

- one request-scoped sequential ledger globally bounds logical source attempts, physical calls,
  pages/cursors, retries, redirects, and decompressed bytes;
- each physical dispatch atomically reserves its source/page/retry/physical units before transport;
  a failed reservation performs zero network calls;
- streamed decompressed bytes are charged after dispatch; byte overflow returns no partial result;
- hidden client retries, date-per-call fan-out, concurrency, unbounded redirects, and cross-source
  stitching are forbidden;
- exhaustion retains only bounded sanitized real attempts and never fabricates a final attempt or a
  `diagnostics_truncated` attempt; and
- owner-approved rate/pacing policy is a prerequisite, not an invented number.

For a future JSON route, parse the complete `Content-Type` value after the first colon, trim and
lower-case the media type, and require exact `application/json`. HTML/XML, missing/malformed media
types, or colon-suffixed non-JSON media types fail closed.

The internal vocabulary is explicitly **provisional and non-public**, with deterministic mappings for
the currently named classes:

| Condition | Token/outcome | Rule |
| --- | --- | --- |
| Successful validated response | `ok` | Continue to coverage reconciliation |
| DNS/connect/reset | `connection_error` | No series; not absence |
| TLS / timeout / rate limit | `tls_error` / `timeout` / `rate_limited` | No series; not absence |
| Unexpected status / WAF | `unexpected_http_status` / `waf_challenge` | No series; not absence |
| Redirect/effective-route mismatch | `redirect` / `effective_route_mismatch` | No series |
| Zero-byte body / valid zero-row result | `empty_response` / `empty_result` | No series; no absence claim |
| MIME/parse/schema/identity/basis failure | `mime_mismatch` / `json_parse_error` / `schema_error` / `identity_mismatch` / `basis_mismatch` | No series |
| Duplicate/page/date/gap failure | `duplicate_or_overlap` / `page_reconciliation_error` / `out_of_window_date` / `unexplained_gap` | No series |
| Publication-eligible missing date / calendar-proven nonpublication | `missing_requested_endpoint` / `NONPUBLICATION_RECONCILED` | Fatal / no row and not fatal |
| Body or atomic budget exhaustion | `body_limit` / `budget_exhausted` | No partial series |

A route-qualified implementation must extend this provisional map before introducing a new provider
condition; it must not map an unknown condition to `NOT_SERVED`. These names are not current public
status/warning/error carriers. No raw URL, query, body, header, exception, cookie, credential,
provider prose, or live rate enters public diagnostics.

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
   attribution, commercial use, rate/retry/pacing, terms amendment/revocation, and
   observation/data revision/correction/retention;
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
- [Repository `open.er-api` source contract](../docs/sources/fx-open-er-api.md)
- [Prior reviewed #217 source note](../docs/research/2026-08-23-daily-cnyvnd-fx-history-source-vetting.md)

## Bottom summary

- Disposition: **SOURCE-GAP CLOSURE**; daily EUR/VND chain remains empty.
- Candidate data/API dispatch: 0 logical calls, 0 physical calls, 0 page/cursor calls, 0 retries; static-document transport was not retained or measured.
- Direct VND-per-1-EUR identity, basis, coverage, runtime, and legal axes are unproven.
- Current annual USD/VND facade/models/diagnostics remain unchanged.
- Future budgets stay numeric-unfrozen but require atomic global reservation and fail-closed exhaustion.
- No USD cross, spot/annual substitution, fill, stitch, or false-absence inference is allowed.
- Reopen requires all identity, coverage, runtime, legal, and compatibility gates plus a fresh PASS.
- No RED, code, push, or close before exact design approval.
