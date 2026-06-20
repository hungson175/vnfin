# Failover engine and validation (internal architecture)

> **Maintainer / internal doc.** This describes the generic failover engine, domain-client
> specializations, transport/cache layer, public input-validation helpers, and the private
> `_contracts` layer. Users see only the `SourceAttempt` / `AllSourcesFailed` surface
> documented in `docs/api.md` and `docs/how-to/errors.md`.

## The generic failover engine (`vnfin/failover.py`)

`FailoverClient` is the domain-agnostic core behind every vnfin failover client. A caller
supplies four small callables; the engine handles the rest:

| Callable param | Purpose |
|----------------|---------|
| `operation(source, *args)` | Fetch from ONE source — called once per attempt |
| `capability(source, *args) -> bool` | Whether a source can serve the request WITHOUT a network call. Incapable sources are skipped and do NOT count against `max_attempts`. |
| `reject(result, *args) -> str | None` | Accept/reject a returned result. Return a reason string to reject; `None` to accept. |
| `unit_of(source) -> hashable | None` | Declared unit/currency. Used by the unit-homogeneity guard at construction. |

Additional options:

| Param | Purpose |
|-------|---------|
| `provenance_of(result)` | Optional callable returning a result's stamped source name. When configured, a mismatch between the claimed provenance and the producing source is a rejected attempt. |
| `finalize(result, attempts, *args)` | Called with the accepted result and the full attempt list before returning. Used to attach attempt diagnostics and coverage warnings. |
| `on_unit_mismatch` | `"raise"` (default) or `"skip"` — what to do when a source in the chain declares a different unit from the chain's canonical unit. |
| `failure_factory` | Callable that builds the exception raised when all attempts are exhausted. |
| `no_capable_factory` | Callable that builds the exception raised when no source is capable of the request. |

### Execution flow

```
run(*args):
  capable = [s for s in sources if capability(s, *args)]
  if not capable: raise no_capable_factory(*args)

  for src in capable:
    if len(attempts) >= max_attempts: break
    try:
        result = operation(src, *args)
    except SourceError:
        record attempt (ok=False, reason=exception message)
        continue
    reason = reject(result, *args)
    if reason:
        record attempt (ok=False, reason=reason)
        continue
    if provenance_of:
        pmis = _provenance_mismatch(provenance_of(result), src.name)
        if pmis:
            record attempt (ok=False, reason=pmis)
            continue
    record attempt (ok=True, reason="ok")
    if finalize: return finalize(result, attempts, *args)
    return result

  raise failure_factory(attempts, *args)
```

```mermaid
flowchart TD
    A([run args]) --> B{any capable<br/>sources?}
    B -- no --> X[raise no-capable-source]
    B -- yes --> C[take next capable source]
    C --> D{attempts &ge; max_attempts?}
    D -- yes --> Z[raise AllSourcesFailed<br/>with recorded attempts]
    D -- no --> E[operation src, *args]
    E -- raises SourceError --> R[record attempt<br/>ok=False, reason] --> C
    E -- returns result --> G{reject reason?<br/>type/empty/identity/<br/>unit/rows/dups}
    G -- reason --> R
    G -- None --> H{provenance_of set<br/>and mismatch?}
    H -- mismatch --> R
    H -- ok --> I[record attempt ok=True]
    I --> J([finalize -> return result])
```

### Unit-homogeneity guard

At construction, `_guard_units` iterates sources and collects declared units (non-`None`
from `unit_of`). If two sources declare different units the behaviour depends on
`on_unit_mismatch`:

- `"raise"` (default): `UnitMismatchError` raised immediately. Makes a unit mix
  structurally impossible, not merely unlikely.
- `"skip"`: sources with mismatched units are silently dropped from the chain.

### Provenance check (issue #126)

When `provenance_of` is configured, the engine verifies that the result's stamped source
matches the source that produced it. Two shapes are accepted:

- A `str` — must equal `source.name`.
- A `frozenset` — the COMPOSITE contract for multi-record results (e.g. fundamentals
  tuple-of-reports); every member must equal `source.name` and the set must be non-empty.

Everything else (missing, bare list, number) is rejected as malformed provenance.

### `_fetched_at_utc_reason` and `_warnings_reason`

Two shared result-metadata guards used by domain clients:

- `_fetched_at_utc_reason(value)` — `None` is allowed (optional metadata); a present
  value must be a timezone-aware UTC `datetime`. Any other type or offset is malformed.
- `_warnings_reason(warnings)` — must be `tuple[str, ...]`. A bare string, list, `None`,
  or a tuple with non-string members is malformed.

## Price client specialization (`vnfin/client.py`)

`FailoverPriceClient` wires the price domain into `FailoverClient`:

- `operation` → `source.get_history(symbol, interval, start, end)`
- `capability` → `source.supports(interval)` (interval-capability skip)
- `reject` → `_validate_price_result(...)` (detailed accept/reject logic)
- `unit_of` → `source.unit` (must be `"VND"`)
- `provenance_of` → `hist.source`
- `finalize` → attaches attempts + soft coverage warnings

Additionally, at construction it runs `_adjustment_policy_guard` to reject chains mixing
different adjustment policies (PROVIDER_ADJUSTED vs RAW vs MIXED).

**`_validate_price_result` checks (in order):**

1. `result_type_reason` — must be a `PriceHistory`
2. `non_empty_reason` — must have at least one bar
3. `_fetched_at_utc_reason` — freshness metadata shape
4. `_warnings_reason` — diagnostic metadata shape
5. Symbol and interval identity match
6. Unit and adjustment-policy chain match
7. Optional `exchange`/`provider_symbol` canonical string shape
8. `row_object_and_aware_datetime_reason` — each bar is a `PriceBar` with a tz-aware key
9. `strictly_ascending_reason` — bars strictly ascending by `time`
10. Per-bar OHLCV invariants: positive finite floats; non-negative integer volume; OHLC order
11. At least one bar in the requested date window

Coverage warnings (soft, non-failing) are appended in `_finalize`:
- `partial_start_coverage` — first bar >7 days after requested start
- `partial_end_coverage` — last bar >7 days before the expected latest trading day
  (VN trading-calendar aware via `calendar.expected_latest_trading_day`)
- `trailing_zero_volume_tail` — a trailing run of ≥10 (D1) bars each with `volume == 0` and
  `open == high == low == close` (a flat carried-forward price): a delisted/suspended/forward-filled
  phantom tail. Bars are kept, not dropped (warn-only); intraday is exempt (zero-volume bars are normal
  off-hours). Inherited by `LiquidityProfile.warnings`

## Source-side bad-bar quarantine (`UDFSource._build_bars`, #186)

The list above is the **client-side** backstop (`_validate_price_result`) over a *returned*
`PriceHistory`. The **source-side** UDF parse — `UDFSource._build_bars`, shared by every UDF adapter
behind both `prices.history` and `index_history` — used to `raise InvalidData` on the **first**
bad bar, aborting the whole response. Since one bad bar appears in *every* source for the same date,
that meant a single bad day anywhere in a 10-year window blocked the entire chart (the original #186
report). The parse now **quarantines** instead:

- **Per-row value-quality failures are dropped (kept out of the series) and recorded**, never served:
  unparseable scalar, non-finite OHLCV (post-scale overflow), non-positive price, negative volume,
  fractional volume, OHLC-order violation. Each dropped row is one `(label, reason)` entry in
  `self._quarantined`.
- **Conflicting / duplicate keys drop the WHOLE key, not just the later row** — for a D1 index
  (`_DEDUPE_IDENTICAL_DUPLICATE_BARS`) an *identical* same-date duplicate still dedupes keep-first
  (`deduped_duplicate_daily_index_bars`, not a quarantine); a *conflicting* same-date bar removes the
  entire date (both bars — we cannot tell which is right). For equity / intraday (exact-timestamp
  keying) any duplicate timestamp drops that timestamp entirely. (Generalizes #66/#162's
  never-silently-pick intent from a hard raise to drop-and-record.)
- **The result self-discloses** via a `quarantined_invalid_bars` warning naming the dropped dates +
  reasons, attached in the shared `UDFSource.get_history` (so both equity and index carry it; the
  index dedupe token is appended *after* it).
- **A systematically-broken source still fails over — judged over the requested window only.** The
  requested-range filter runs *inside* `_build_bars`, so out-of-window provider padding is dropped
  **before** the threshold is computed. If `bad_inrange > max(_QUARANTINE_ABS_FLOOR,
  _QUARANTINE_FRACTION × considered)` — where `considered` is the in-range, timestamp-parseable rows
  (counting each calendar date once — identical #162 duplicates don't inflate the denominator) and
  `bad_inrange` is how many of those failed a quality check — the parse raises `InvalidData`
  (a `SourceError`) → the failover client tries the next source; all-sources-bad → `AllSourcesFailed`.
  Bad rows **outside** `[start, end]`, rows whose timestamp is itself unparseable (can't be
  range-attributed), and identical same-date duplicates collapsed by the #162 dedupe are excluded from
  the verdict so a provider's out-of-window junk — or merely sending each date twice — can't spuriously
  fail an otherwise-clean window (reviewer-found regressions of the original fix). Constants:
  `_QUARANTINE_ABS_FLOOR = 3` (a few isolated glitches never block any window), `_QUARANTINE_FRACTION =
  0.10` (a mostly-bad in-range response is untrustworthy). A lone all-bad row drops below the floor →
  zero bars → `EmptyData` (still a `SourceError`).
- **Structural / array-shape faults still HARD-RAISE** (they reach this point as an untrustworthy whole
  response): missing/misaligned/non-sequence arrays, malformed envelope / non-object data / bad status.

## Transport layer (`vnfin/transport.py`)

`HttpDataSource` is the shared HTTP transport base used by every adapter:

- **IPv4-forced httpx** — `local_address="0.0.0.0"` (datacenter IPv6 often blocked by VN/finance providers).
- **Browser User-Agent** — several feeds reject the default httpx UA.
- **Transport errors mapped to `SourceUnavailable`** — so the failover engine can recover.
- **Injectable `http_get`** — every adapter accepts an `http_get` callable for deterministic
  unit tests without network.

**Opt-in cache** (`cache_ttl=N`):
- In-memory dict keyed by `(url, params, json_body, headers)` — order-independent,
  normalized to JSON-sorted form.
- Secret values (api_key, token, Authorization, etc.) are redacted from the loggable
  key; their SHA-256 hashes participate in the key so different credentials never share
  a cached response.
- Default `cache_ttl=None` (no caching) keeps historical single-attempt behavior.

**Opt-in retry with jittered exponential backoff** (`max_retries=N`):
- Default `max_retries=0` (one attempt, no backoff — historical behavior unchanged).
- Transient failures: stdlib `ConnectionError`/`TimeoutError`, `httpx.TransportError`,
  HTTP 429/5xx → retried. Non-transient (4xx other than 429, etc.) → re-raised immediately.
- Delay: `base * 2**attempt` capped at `backoff_max`, then full-jittered.

**Secret redaction** (`redact_secrets`):
- Applied to all error messages, cache-key display portions, and log strings before they
  surface in `SourceUnavailable`.
- Covers URL query-string params, `Authorization` headers, and dict/JSON key-value pairs
  whose names match `SENSITIVE_PARAMS` (case/separator-insensitive).

## Public input validation (`vnfin/validation.py`)

Caller-facing validators that raise `InvalidData` (or `VnfinError`) for malformed inputs
before any source ever sees them:

| Function | Validates |
|----------|-----------|
| `validate_non_empty_string(value, name)` | Non-empty string (strips and checks) |
| `validate_date_range(start, end, *, allow_none, name)` | Both dates present (unless `allow_none`), comparable, and `start <= end` |
| `validate_positive_int(value, name)` | Positive int; rejects `bool` |
| `validate_country_iso3(value)` | Exactly three ASCII letters `[A-Z]{3}` after strip/upper |
| `validate_iso_date_string(value, label)` | `date`/`datetime` object or strict `YYYY-MM-DD` string (zero-padded) |
| `parse_canonical_int(value, label)` | Plain `int` or canonical base-10 string (`0` or `[1-9]\d*` — no sign, leading zeros, or fraction) |

`validate_country_iso3` shares the same `[A-Z]{3}` grammar as the private
`canonical_country_iso3` in `_contracts/keys.py`.

## TimeSeriesResult mixin (`vnfin/timeseries.py`)

A minimal mixin factoring `__len__`, `__iter__`, and `to_dataframe` out of every domain
result container. Concrete dataclasses declare three class attributes and implement two
methods:

- `_items_attr` — name of the field holding the row tuple (e.g. `"bars"`, `"points"`).
- `_index_column` — DataFrame index column name.
- `_df_columns` — full ordered list of DataFrame columns.
- `_row_record(item) -> dict` — map one row to a flat record.
- `_df_attrs() -> dict` — metadata stamped onto `df.attrs`.

`to_dataframe` raises `InvalidData` on duplicate index keys as a backstop (sources are
expected to reject duplicates earlier).

## The `_contracts` private layer

See `docs/architecture/provider-contracts.md` for the full detail. Summary:

- `vnfin/_contracts/` is a private package (underscore prefix); it is NOT public API.
- It provides two categories of tools:
  - **Provider-boundary primitives** (`fields.py`, `keys.py`, `rows.py`): used by adapters
    while parsing a raw provider response.
  - **Typed-result rules** (`results.py`, `timeseries.py`): used by failover clients to
    accept/reject a returned typed object.
- Key semantic invariant: **a missing key may be legacy-compatible; a present malformed
  key/value fails closed** unless the contract explicitly permits present-null.
