# #201 design note — Vietnamese equity foreign-investor daily flow

**Status:** `BLOCKED — source-gap closure; no source enabled; exact closure round pending re-review`
**Reviewer gate:** exact closure BLOCK at reviewer commit `4d91560`; report
`reviews/review-202608221518-issue201-exact-closure-review.md`
**Issue:** #201; public triage `issuecomment-5378368603`
**Research evidence:** `docs/research/2026-08-22-vn-foreign-flow-source-vetting.md`
**Clean-room:** primary official exchange/regulator pages and first-party UI/Swagger inspection only; the mandatory repository blacklist was applied to every search and no excluded material was opened or used.
**Authorization boundary:** this entire note is a future, non-authoritative design artifact. It authorizes no parser, adapter, public model, facade, source chain, runtime request, cache, production code, push, or issue close.

## 0. Source-gap closure disposition

No candidate currently satisfies the accepted source gate. The current default source chain is
**empty**. The only permitted work before a new design gate is source-owner evidence collection,
correction of this packet, and deterministic offline contract planning.

| Candidate | Technical reachability | Coverage | Response identity/date | Units/fields | Legal/reuse | Operational/TLS | Disposition |
|---|---|---|---|---|---|---|---|
| HOSE `tradingresult/{code}` | `TECHNICAL_REACHABILITY_PASS` observed without credentials | `HISTORICAL_COVERAGE_SAMPLED_ONLY`; three names do not prove market-wide completeness | Symbol is returned; epoch/session-date semantics `UNRESOLVED` | Raw scale, shares/VND meaning, field stability `UNRESOLVED` | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | Strict TLS control `PASS`; rate/SLA/cache unresolved | `DISABLED` |
| HOSE `foreign/{code}` | HTTP reachability observed | History sampled | `RESPONSE_IDENTITY_MISSING_REJECTED`; response does not echo symbol | Units/field stability unresolved | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | Strict TLS control `PASS`; no fallback | `DISABLED; not a fallback` |
| HNX listed report | Historical HTTP observation; current strict-client access fails | Historical samples only; no range/completeness proof | `RESPONSE_DATE_IDENTITY_UNRESOLVED`; request-date coupling is not returned identity | VND label present; volume scale/field stability unresolved | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `TLS_CHAIN_VERIFICATION_FAIL`; strict verified chain required to reopen | `DISABLED` |
| HNX UPCoM report | Historical HTTP observation; current strict-client access fails | `HISTORICAL_COVERAGE_FAIL`; historical date inputs were ignored | `RESPONSE_DATE_IDENTITY_UNRESOLVED`; unchanged snapshots do not prove requested date | VND label present; volume semantics unresolved | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `TLS_CHAIN_VERIFICATION_FAIL`; strict verified chain required to reopen | `DISABLED` |

The HNX operational axis is separate from the earlier HTTP observations: on the current strict
standard-client recheck, `hnx.vn` produced `curl` error 60 and Python
`CERTIFICATE_VERIFY_FAILED` because the observed chain lacked a verifiable issuer path. HOSE passed
the same control. Historical 200 responses therefore remain historical evidence only; no probe may
use `--insecure` or `-k`, and neither HNX route can reopen until its certificate chain verifies.

Status vocabulary is independent:

* `PASS` means the named property was positively evidenced for that route;
* `FAIL` means the probe demonstrated that the property does not hold;
* `UNRESOLVED` means evidence is absent or insufficient, not that a prohibition was proved;
* `SAMPLED_ONLY` means observations are not a market-wide or completeness guarantee;
* `DISABLED` is the engineering disposition, not a source fact.

The candidate boundary is therefore **pending source-owner clearance**, not “HOSE-first after
legal sign-off.” Legal permission alone would not authorize implementation: identity, units,
date semantics, coverage, field stability, and operational terms must also pass.

## 1. Future, non-authoritative API sketch

> **Not approved for implementation.** The following signatures and models specify the correction
> target only. With no enabled source, every call must fail before provider access with a typed
> coverage/identity error. They must not be added to the package, API snapshot, docs surface,
> skill, or changelog until a later design gate passes.

### 1.1 One obvious single-symbol facade

The future public entry remains `vnfin.equities.foreign_flow`:

```python
from datetime import date

from vnfin import Interval
from vnfin.equities import foreign_flow

# Illustrative only. With the current empty chain this raises typed coverage/identity
# failure; it is not a live usage example or a promise of coverage.
history = foreign_flow(
    "FPT",
    start=date(2018, 1, 1),
    end=date.today(),
    interval=Interval.D1,
    exchange="HOSE",
)
```

Exact future signature:

```python
def foreign_flow(
    symbol: str,
    start: date,
    end: date,
    interval: Interval = Interval.D1,
    *,
    exchange: Exchange,
    require_full: bool = False,
    http_get=None,                  # deterministic synthetic-fixture seam only
    timeout: float = 25.0,
    max_source_attempts: int = 2,
    max_transport_retries: int = 1,
) -> ForeignFlowHistory: ...
```

Preflight rules, before any network call:

1. `symbol` is a non-empty canonical security identifier using the repository's shared grammar;
   trim and uppercase exactly once.
2. `start` and `end` are plain `datetime.date` objects, not `datetime`; require
   `start <= end` and reject a future `end` using Vietnam time.
3. `interval is Interval.D1`; every other interval fails with typed `InvalidData` before
   source selection. No resampling or intraday interpretation is hidden here.
4. `exchange` is mandatory and exactly `HOSE`, `HNX`, or `UPCOM`; a source response may never
   override it. `exchange=None`, omission, symbol suffixes, and guessed boards fail preflight
   before HTTP.
5. An invalid, omitted, or conflicting board fails preflight with shared `InvalidData` before
   budget reservation or HTTP. A valid board with no enabled source returns
   `ForeignFlowCoverageError(code="exchange_unavailable")` naming the board and evidence-backed
   gap; it never falls through to another exchange. `coverage_gap` is reserved for an attempted
   source that cannot satisfy the requested coverage.
6. `max_source_attempts` is an integer in `1..2`; `max_transport_retries` is an integer in
   `0..1`. Their diagnostics are distinct and redacted.

The result is immutable, one-source homogeneous, and never fills non-trading dates, invents
listing history, or merges source segments.

### 1.2 Reusable future client and exact bulk facade

```python
def foreign_flow_client(
    *,
    sources: Sequence[ForeignFlowSource] = (),  # empty until a gate-approved source exists
    http_get=None,
    timeout: float = 25.0,
    max_source_attempts: int = 2,
    max_transport_retries: int = 1,
) -> ForeignFlowClient: ...


class ForeignFlowClient:
    def history(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: Interval = Interval.D1,
        *,
        exchange: Exchange,
        require_full: bool = False,
    ) -> ForeignFlowHistory: ...

    def history_bulk(
        self,
        symbols: Iterable[str | IndexMember] | IndexConstituents,
        start: date,
        end: date,
        interval: Interval = Interval.D1,
        *,
        exchange: Exchange | None = None,  # only when every input carries its own exchange
        require_full: bool = False,
        max_concurrency: Literal[1] = 1,
        max_symbols: int = 100,
        max_total_source_attempts: int = 100,
        max_total_pages: int = 5_000,
        max_total_requests: int = 6_000,
    ) -> ForeignFlowBulk: ...
```

The matching one-shot facade is:

```python
def foreign_flow_bulk(
    symbols: Iterable[str | IndexMember] | IndexConstituents,
    start: date,
    end: date,
    interval: Interval = Interval.D1,
    *,
    exchange: Exchange | None = None,  # only when every input carries its own exchange
    require_full: bool = False,
    http_get=None,
    timeout: float = 25.0,
    max_source_attempts: int = 2,
    max_transport_retries: int = 1,
    max_concurrency: Literal[1] = 1,
    max_symbols: int = 100,
    max_total_source_attempts: int = 100,
    max_total_pages: int = 5_000,
    max_total_requests: int = 6_000,
) -> ForeignFlowBulk: ...
```

The two facades must share exact validation, source ordering, coverage ranking, error codes,
redaction, request accounting, and result models. No default source is constructed while the
source chain is empty.

#### 1.2.1 Whole-result failover and coverage selection

A future client may evaluate only sources that have passed the same design/legal gate and match
the requested exchange and units:

* A source attempt requests the complete `[start, end]` range. It is rejected for malformed
  envelope, response identity/date, units, duplicate dates, arithmetic conflict, schema drift,
  page inconsistency, or budget truncation.
* `coverage_status=` `full` requires an approved provider completeness marker or an approved
  exchange calendar, every expected session exactly once, no internal gap, and a publication-lag
  check for the requested end. Without that proof the result cannot claim full coverage.
* `coverage_status=` `partial_known` or `partial_unknown` is valid only when at least one
  structurally valid row exists, all returned rows are within the request, identity and units
  pass, and truncation did not occur. It carries explicit served bounds, a bounded ordered reason
  tuple, and the count fields/invariants in §2.4.
* An internal gap is listed when an approved calendar identifies missing sessions. If no approved
  calendar exists, internal completeness is `UNOBSERVABLE`; the result remains partial, never
  full. Missing dates are never filled.
* A source returning partial coverage does not stop the chain: compatible enabled sources are
  tried. The first valid `full` result wins. If no full result exists, `partial_known` ranks above
  `partial_unknown`; otherwise candidates are compared by the executable `coverage_rank()` tuple
  in §2.4: least uncovered-session count, then least internal-gap count, then configured source
  priority. Among unknown partials, only configured source priority breaks the tie. Row count alone
  is never a quality tie-break.
* `require_full=True` rejects all partial results with `coverage_gap`. No source rows
  are stitched, appended, or used to repair another source.
* Attempt statuses are retained in lowercase: `transport_failed`, `schema_rejected`,
  `identity_rejected`, `units_rejected`, `empty`, `coverage_rejected`, `valid_partial`, or
  `valid_full`. A disabled or capability-incompatible source is not an attempt and is omitted from
  the attempt tuple.
* If all compatible sources fail, raise the one public flow exception,
  `ForeignFlowCoverageError(code="all_sources_failed")`, carrying immutable, redacted attempts.
  An unsupported board never falls through to another board.

The source protocol is internal until a future public adapter is approved:

```python
class ForeignFlowSource(Protocol):
    name: ForeignFlowSourceName
    source_type: ForeignFlowSourceType
    dataset_id: ForeignFlowDatasetId
    supported_exchanges: frozenset[Exchange]

    def get_history(
        self,
        symbol: str,
        start: date,
        end: date,
        *,
        exchange: Exchange,
        interval: Interval,
        require_full: bool,
        budget_ledger: RequestBudgetLedger,
    ) -> ForeignFlowHistory: ...
```

`budget_ledger` is the single invocation-owned ledger created by the bulk scheduler and passed
unchanged to every compatible source. A source must use it for every discovered logical page and
physical transport call; it may not copy limits into a private budget or maintain an unshared retry
counter.

> **Future, non-authoritative design sketch — not approved for implementation.** Every type alias,
> model, field, warning token, exception, dataset identifier, and invariant below is provisional
> until source-owner clearance and a new design gate pass.

## 2. Future typed models and invariants

### 2.1 Bounded provenance and source identity

```python
Exchange = Literal["HOSE", "HNX", "UPCOM"]
Frequency = Literal["daily"]
VolumeUnit = Literal["shares"]
ValueUnit = Literal["VND"]
ForeignFlowSourceType = Literal[
    "official_exchange",
    "official_regulator",
    "licensed_vendor",
]
ForeignFlowSourceName = Literal[
    "hsx_market_tradingresult_v1",
    "hnx_report_ny_v1",
    "hnx_report_uc_v1",
]
ForeignFlowDatasetId = Literal[
    "hsx.market.securities.tradingresult.v1.0",
    "hnx.report.stocketfs.tradingresult.listed.v1",
    "hnx.report.stocketfs.tradingresult.upcom.v1",
]
```

The exact immutable provenance tuple is
`(source, dataset_id, source_type, exchange)`. The only permitted mappings are:

| source | dataset_id | source_type | exchange | current status |
|---|---|---|---|---|
| `hsx_market_tradingresult_v1` | `hsx.market.securities.tradingresult.v1.0` | `official_exchange` | `HOSE` | disabled; semantics/legal reopen required |
| `hnx_report_ny_v1` | `hnx.report.stocketfs.tradingresult.listed.v1` | `official_exchange` | `HNX` | disabled; date identity/legal reopen required |
| `hnx_report_uc_v1` | `hnx.report.stocketfs.tradingresult.upcom.v1` | `official_exchange` | `UPCOM` | disabled; historical coverage/legal reopen required |

The rejected HOSE `foreign/{code}` route has no source name in this contract and cannot enter the
chain unless first-party response-backed symbol identity is proven in a new gate.

### 2.2 Field-level provenance and signed arithmetic

```python
class ForeignFlowFieldOrigin(str, Enum):
    SOURCE_PUBLISHED = "source_published"
    DERIVED = "derived"
    MISSING = "missing"


@dataclass(frozen=True)
class ForeignFlowProvenance:
    foreign_buy_volume: ForeignFlowFieldOrigin
    foreign_sell_volume: ForeignFlowFieldOrigin
    foreign_net_volume: ForeignFlowFieldOrigin
    foreign_buy_value_vnd: ForeignFlowFieldOrigin
    foreign_sell_value_vnd: ForeignFlowFieldOrigin
    foreign_net_value_vnd: ForeignFlowFieldOrigin
```

Gross buy/sell fields are non-negative. Net fields are signed and are always
`buy - sell`. A future implementation uses this exact parser bound for every integer field:

```python
MAX_ABS_INTEGER = 2**63 - 1
```

For every numeric field, `value is None` if and only if its origin is `MISSING`. A present
zero is never missing. Gross values must be whole integers in `[0, MAX_ABS_INTEGER]`; net
values must be whole signed integers in `[-MAX_ABS_INTEGER, MAX_ABS_INTEGER]`. The accepted
wire forms are JSON integer tokens or finite `Decimal` values whose value is exactly integral;
the parser checks the bound before conversion. Python `float` values are rejected, including
integral binary floats, so a rounded value near `2**53` or `2**63` cannot pass accidentally.
Boolean values, fractional values, non-finite values, overflow, unknown-scale, or negative gross
values fail closed. If a provider publishes a net field, it must equal the exact derived
difference or the entire source result is rejected. A validated provider-published net keeps
origin `SOURCE_PUBLISHED` and adds the bounded `provider_net_published` warning; a net computed
because the provider did not publish one has origin `DERIVED` and adds `derived_net`. A net is
`None` and `MISSING` whenever either gross operand is missing.

### 2.3 Identity-bearing daily row

```python
@dataclass(frozen=True)
class ForeignFlowRow:
    symbol: str
    exchange: Exchange
    session_date: date
    foreign_buy_volume: int | None       # non-negative shares
    foreign_sell_volume: int | None      # non-negative shares
    foreign_net_volume: int | None       # signed shares
    foreign_buy_value_vnd: int | None    # non-negative VND
    foreign_sell_value_vnd: int | None   # non-negative VND
    foreign_net_value_vnd: int | None    # signed VND
    provenance: ForeignFlowProvenance
```

Symbol and exchange are repeated on each row deliberately, so the hard row identity invariant
does not depend only on homogeneous result metadata. Row invariants:

* `symbol` is canonical and exactly matches the response-backed source symbol;
* `exchange` is the source-bound board and exactly matches the requested board;
* `session_date` is a plain date; rows are strictly ascending;
* one date appears at most once; identical duplicates may be deduplicated only when the complete
  normalized row is identical; a conflict rejects the source result;
* net is calculated with integer arithmetic only, with no rounding or float subtraction;
* no calendar rows are synthesized for weekends, holidays, suspensions, pre-listing dates,
  publication lag, or provider outages.

### 2.4 Immutable history and coverage model

```python
CoverageStatus = Literal["full", "partial_known", "partial_unknown"]
CoverageReason = Literal[
    "complete_requested_sessions",
    "dataset_inception",
    "symbol_inception",
    "publication_lag",
    "source_window",
    "internal_gap",
    "coverage_unverified",
]
CoverageReasonOrder = (
    "dataset_inception",
    "symbol_inception",
    "source_window",
    "publication_lag",
    "internal_gap",
    "coverage_unverified",
    "complete_requested_sessions",
)

@dataclass(frozen=True)
class ForeignFlowCoverage:
    status: CoverageStatus
    reasons: tuple[CoverageReason, ...]
    expected_session_count: int | None
    served_session_count: int
    uncovered_session_count: int | None
    missing_session_dates: tuple[date, ...]
    internal_gap_dates: tuple[date, ...]
    internal_gap_count: int | None
    internal_gap_status: Literal["none", "known", "unobservable"]
    publication_cutoff: date | None
    publication_lag_status: Literal["confirmed", "unresolved"]
```

`reasons` is deduplicated and sorted by `CoverageReasonOrder`; `complete_requested_sessions` is
the only reason allowed on a `full` result. `served_session_count == len(rows)` always. A `full`
result requires `expected_session_count` to be known, `served_session_count` equal to it,
`uncovered_session_count == 0`, no missing or internal-gap dates, `internal_gap_count == 0`, and a
publication check with `publication_lag_status == "confirmed"`, a non-null
`publication_cutoff`, and `requested_end <= publication_cutoff`. A `partial_known` result requires
a non-null expected and uncovered count, `internal_gap_status` of `none` or `known`, a non-null
internal-gap count, at least one reason other than `coverage_unverified`, and
`uncovered_session_count == expected_session_count - served_session_count`.
`missing_session_dates` contains exactly the known uncovered dates: it is sorted and unique and
`len(missing_session_dates) == uncovered_session_count`; `internal_gap_dates` is also sorted and
unique and is a subset of `missing_session_dates`. A `partial_unknown` result has valid rows but
cannot prove complete session coverage, so both expected and uncovered counts are `None`,
`missing_session_dates == ()`, and `coverage_unverified` is present. It may report an
approved-calendar internal gap only under the same `internal_gap_status == "known"`/count/date
invariant; an observed no-gap calendar uses `"none"` with zero and empty dates, and an
unobservable calendar uses `"unobservable"` with a null count and empty dates. These fields do not
enter ranking while the expected count is unknown.
Unresolved publication lag is represented explicitly by `publication_lag_status == "unresolved"`
with `publication_cutoff is None`. A confirmed lag status requires a non-null cutoff;
`publication_lag` as a reason is allowed only with confirmed status. No status may contain a
negative count or duplicate date. `internal_gap_status == "known"` requires a non-null
`internal_gap_count == len(internal_gap_dates)`; `"none"` requires zero and an empty tuple; and
`"unobservable"` requires a null count and an empty tuple, so it is never legal on `partial_known`.
A page-budget stop is a typed failure, not a partial result. An approved calendar
treats weekends/holidays as non-sessions, never as missing rows.

The deterministic ranking key is larger-is-better and uses a lower configured integer as the
higher source priority:

```python
def coverage_rank(coverage: ForeignFlowCoverage, source_priority: int) -> tuple[int, int, int, int]:
    if coverage.status == "full":
        quality = (2, 0, 0)
    elif coverage.status == "partial_known":
        quality = (
            1,
            -coverage.uncovered_session_count,  # non-null by invariant
            -coverage.internal_gap_count,       # non-null by known-gap invariant
        )
    else:
        quality = (0, 0, 0)
    return (*quality, -source_priority)
```

The publication cutoff is the latest owner-confirmed complete session. A request ending after it
may be `partial_known` with `publication_lag`; an unresolved cutoff remains `partial_unknown` and
may not be presented as a known lag date. Every successfully returned partial history contains
exactly one corresponding coverage warning: `coverage_partial_known` for `partial_known` or
`coverage_partial_unknown` for `partial_unknown`; other bounded orthogonal warnings may coexist.
Missing dates are never filled or silently converted into an internal-gap count.

```python
ForeignFlowWarning = Literal[
    "current_snapshot_only",
    "coverage_partial_known",
    "coverage_partial_unknown",
    "publication_lag",
    "internal_gap",
    "source_listing_or_inception_unknown",
    "provider_net_published",
    "derived_net",
    "tls_chain_verification_fail",
]

@dataclass(frozen=True)
class ForeignFlowHistory(TimeSeriesResult):
    symbol: str
    exchange: Exchange
    interval: Literal[Interval.D1]        # only Interval.D1
    frequency: Frequency                  # always "daily"
    source: ForeignFlowSourceName
    dataset_id: ForeignFlowDatasetId
    source_type: ForeignFlowSourceType
    rows: tuple[ForeignFlowRow, ...]
    requested_start: date
    requested_end: date
    served_start: date | None
    served_end: date | None
    coverage: ForeignFlowCoverage
    volume_unit: VolumeUnit               # "shares", only after scale gate
    value_unit: ValueUnit                 # "VND", only after scale gate
    currency: Literal["VND"]
    fetched_at_utc: datetime               # aware UTC only
    warnings: tuple[ForeignFlowWarning, ...] = ()
    attempts: tuple[ForeignFlowSourceAttempt, ...] = ()
```

The future model must set `_items_attr = "rows"`, `_index_column = "session_date"`, and a
fixed `_df_columns` order. `.to_dataframe()` attaches these attrs:

```text
symbol, exchange, interval, frequency, source, dataset_id, source_type,
requested_start, requested_end, served_start, served_end,
coverage_status, coverage_reasons, expected_session_count, served_session_count,
uncovered_session_count, missing_session_dates, internal_gap_dates, internal_gap_count,
internal_gap_status, publication_cutoff, publication_lag_status,
volume_unit, value_unit, currency, fetched_at_utc
```

Rows have the identity columns, six numeric fields, and six stable `*_origin` columns. No
credential-bearing URL appears in dataframe metadata. `fetched_at_utc` is aware UTC and
`warnings`/attempts are tuples. Every warning is one of the bounded `ForeignFlowWarning` tokens;
provider text never becomes a warning token.

Every row must satisfy `row.symbol == history.symbol` and
`row.exchange == history.exchange`. The result is source-homogeneous: every row inherits the
exact `(source, dataset_id, source_type, exchange)` identity of its enclosing result. Cross-source
row stitching is forbidden.

### 2.5 Attempts, budgets, and bounded diagnostics

```python
ForeignFlowAttemptStatus = Literal[
    "transport_failed", "schema_rejected", "identity_rejected",
    "units_rejected", "empty", "coverage_rejected", "valid_partial", "valid_full",
]

ForeignFlowFailureCode = Literal[
    "unsupported_exchange", "exchange_unavailable", "coverage_gap", "empty_data",
    "all_sources_failed", "source_unavailable", "transport_retry_exhausted",
    "malformed_payload", "schema_drift", "identity_missing", "identity_mismatch",
    "unit_mismatch", "arithmetic_conflict", "pagination_invalid",
    "page_budget_exhausted", "request_budget_exhausted", "attempt_budget_exhausted",
]
ForeignFlowSuccessReason = Literal["accepted_partial", "accepted_full"]
ForeignFlowAttemptReason = ForeignFlowFailureCode | ForeignFlowSuccessReason

@dataclass(frozen=True)
class ForeignFlowSourceAttempt:
    source: ForeignFlowSourceName
    dataset_id: ForeignFlowDatasetId
    source_type: ForeignFlowSourceType
    exchange: Exchange
    status: ForeignFlowAttemptStatus
    source_attempt_number: int
    transport_requests: int
    pages: int
    reason_code: ForeignFlowAttemptReason
```

`source_attempt_number` counts candidate source selections. `transport_requests` counts
actual HTTP requests, including bounded retries. They are never conflated. Transport errors,
HTTP statuses, URLs, symbols, and provider messages are redacted to bounded public error codes.
All status literals are lowercase. Every recorded attempt has one non-null reason code: a
failed/empty/rejected attempt has one `ForeignFlowFailureCode`; `valid_partial` must use
`accepted_partial` and `valid_full` must use `accepted_full`. A capability-incompatible or disabled
candidate is omitted before attempt construction, consumes no budget, and has no reason code. A
success never carries a failure code, and a failure never carries a success reason.

The future public coverage error is named and bounded:

```python
class ForeignFlowCoverageError(VnfinError):
    symbol: str
    exchange: Exchange
    requested_start: date
    requested_end: date
    code: ForeignFlowFailureCode
    attempts: tuple[ForeignFlowSourceAttempt, ...]
```

`ForeignFlowCoverageError` is the one public domain exception for this future flow. Its bounded
codes are `exchange_unavailable` when a valid board has no enabled source, `coverage_gap` when an
attempted source is insufficient or `require_full=True` rejects a partial, `all_sources_failed`
when compatible candidates all fail structurally, and the dimension-specific budget codes below.
`attempts` is the immutable, canonical-order tuple used to explain the error; it is empty for
`exchange_unavailable` because no source was eligible to run.
Invalid/omitted/conflicting board input raises shared preflight `InvalidData` before any budget or
HTTP. Internal source failures are normalized into attempt codes rather than exposing a competing
public exception vocabulary. Per-symbol bulk handling catches only `ForeignFlowCoverageError` and
adapter-wrapped `TimeoutError`, `ConnectionError`, or `OSError`; it never catches arbitrary
`Exception`. Unexpected programming errors escape.

Failure and warning mapping is deterministic and finite:

| Situation | Public result | Attempt/failure code | Warning tokens |
|---|---|---|---|
| Invalid, omitted, or conflicting board | whole-call preflight `InvalidData`; zero HTTP | none | none |
| Valid board with no enabled compatible source | `ForeignFlowCoverageError` | `exchange_unavailable` | none; source-gap evidence is represented by the bounded code only |
| Compatible source attempted but rows/coverage cannot satisfy the request, or `require_full=True` rejects a partial | item failure or `ForeignFlowCoverageError` | `coverage_gap` | `coverage_partial_known` or `coverage_partial_unknown` only when a partial result is retained for diagnostics |
| All compatible sources structurally fail | `ForeignFlowCoverageError` | `all_sources_failed` | none; immutable attempts carry the bounded reasons |
| `as_of is None` membership context | successful bulk context or item result | none | exactly one `current_snapshot_only` |

`ForeignFlowWarning` is the complete warning registry; warning order is the registry order and
duplicates are removed. A warning never substitutes for a failure code, and provider text never
creates a new token.

The limits are immutable, but each bulk invocation owns a mutable, atomic ledger. It is never
shared across client calls or persisted between invocations:

```python
ForeignFlowSourceKey = tuple[Exchange, str, ForeignFlowSourceName]
ForeignFlowPageKey = tuple[Exchange, str, ForeignFlowSourceName, int]
ForeignFlowRequestKey = tuple[ForeignFlowPageKey, int]

@dataclass(frozen=True)
class RequestBudget:
    max_source_attempts: int = 100
    max_pages: int = 5_000
    max_requests: int = 6_000
    max_transport_retries_per_page: int = 1


@dataclass
class RequestBudgetLedger:
    limits: RequestBudget
    used_source_attempts: int = 0
    used_pages: int = 0
    used_requests: int = 0
    reserved_source_attempts: set[ForeignFlowSourceKey]
    reserved_pages: set[ForeignFlowPageKey]
    reserved_requests: set[ForeignFlowRequestKey]
    # One lock/transaction protects every check-and-increment operation.
    _atomic_reservation_lock: Lock

    def reserve_source_attempt(self, source_key: ForeignFlowSourceKey) -> None: ...
    def reserve_page(self, page_key: ForeignFlowPageKey) -> None: ...
    def reserve_request(self, page_key: ForeignFlowPageKey, retry_number: int) -> None: ...
```

Each reservation is an atomic check-and-increment transaction. A source-attempt reservation is
made exactly once for a canonical `(exchange, symbol, source)` selection, before that source is
selected/invoked; retries and pages never increment it. A logical-page reservation is made once
before page `N` is transmitted for the first time; retries of that same page do not reserve another
page. Every physical transport call reserves one request immediately before transmission with a
`retry_number`: `0` is the initial call and `1..max_transport_retries_per_page` are retries.
The ledger records retry numbers by canonical `(exchange, symbol, source, logical_page)` and rejects
a duplicate retry number, a retry beyond the per-page limit, or a retry that is not exactly one
greater than the largest already reserved number for that page. `retry_number=0` is legal only for
the first request of a reserved page; `retry_number > 0` is legal only after the preceding request
number is reserved. The scheduler calls a retry reservation only after that preceding call returns
a bounded retryable transport failure. A retry reservation consumes one retry quota and one
request; failure to reserve either means no call is issued. Capability-incompatible sources are
skipped without an attempt reservation.

The source-gap scheduler is an exact sequential state machine: `max_concurrency` is the literal
value `1`, canonical symbols are processed in first-seen order, sources in configured priority
order, pages in ascending order, and retries immediately after their failed page call. Its barriers
are strict: no input item `N+1` starts before item `N` is finalized; no lower-priority source starts
before the prior source is finalized; no page `N+1` starts before page `N` and all of its permitted
retries are finalized; and no retry `N+1` is reserved before retry `N` has a bounded retryable
failure. A source receives the same shared ledger and performs its own page loop through that
ledger; the scheduler does not pre-create page-2 tickets or speculate about later input positions.
Parallel scheduling is deferred until owner rate terms and a separately executable wave/barrier
design pass; no parallel-concurrency promise exists in this contract. Completed items stay completed;
current and queued items receive one failure record rather than being dropped.

Reservation exhaustion is dimension-specific: failure of a source ticket emits
`attempt_budget_exhausted`; failure of a new logical page emits `page_budget_exhausted`; failure of
a physical request emits `request_budget_exhausted`; and failure of retry quota emits
`transport_retry_exhausted`. The diagnostic and `ForeignFlowCoverageError.code` must name the
actual exhausted dimension, never default every stop to request exhaustion. With the 100-symbol
default and 100 source-attempt default, every canonical item has one first-source ticket; a caller
may raise the attempt limit to the 200 hard cap when two-source failover for all 100 items is
needed, or lower it deliberately.

| Reservation point | Exhaustion code | Effect |
|---|---|---|
| Source key, per-item or invocation cap | `attempt_budget_exhausted` | No source invocation |
| New logical-page key | `page_budget_exhausted` | No physical request |
| `(page_key, retry_number)` request key with total request cap | `request_budget_exhausted` | No physical request |
| Retry number beyond the per-page quota or non-sequential/duplicate retry key | `transport_retry_exhausted` | No retry request |

The RED cases must exercise the shared ledger identity, not only aggregate counters: two sources
must receive the same ledger object; page 1 retry 1 and page 2 retry 1 are both legal; page 1 retry
2 is rejected when the per-page maximum is 1; duplicate source/page/request reservations are
rejected atomically; the observed call sequence is input → source → page → retry; a
`max_concurrency=2` preflight makes zero calls; and every exhausted reservation dimension makes
zero calls for the rejected ticket. These checks are the executable contract for the scheduler,
including lazy page discovery and no speculative future reservations.

> **Future, non-authoritative design sketch — not approved for implementation.** Bulk behavior,
> membership propagation, and budget values below are correction targets only.

## 3. Bulk and VN30 context contract

### 3.1 Typed inputs preserve identity and membership provenance

The input type is intentionally either a typed basket/context or an iterable of strings/member
objects:

```python
from vnfin.indices.models import IndexConstituents, IndexMember

@dataclass(frozen=True)
class ForeignFlowMembershipContext:
    index: str
    source: str
    provider_group: str | None
    fetched_at_utc: datetime | None
    as_of: datetime | None
    membership_warnings: tuple[str, ...]                 # exact upstream descriptions
    membership_warning_prefixes: tuple[str, ...]         # first-seen unique colon prefixes
    flow_warnings: tuple[ForeignFlowWarning, ...]        # bounded normalized flow tokens

ForeignFlowKey = tuple[Exchange | None, str]
```

`foreign_flow_bulk(members, ...)` accepts one `IndexConstituents` object directly; a raw symbol
iterable and typed constituent input are mutually exclusive. It copies `index`, `source`,
`provider_group`, `fetched_at_utc`, and `as_of` into the immutable
`ForeignFlowMembershipContext`; it never fabricates `as_of` and it preserves
`IndexConstituents.warnings` byte-for-byte as `membership_warnings`. For every non-empty upstream
warning, normalization derives the first colon-delimited prefix with
`warning.split(":", 1)[0].strip()` and stores first-seen unique values in
`membership_warning_prefixes`; an empty warning or prefix is preflight `InvalidData`. Descriptive
prefixes such as `weights_not_available` and `current_snapshot_only` remain membership metadata,
not new `ForeignFlowWarning` values.

The normalized bounded `flow_warnings` are a separate tuple. A recognized
`current_snapshot_only` prefix contributes one `current_snapshot_only` flow token. If `as_of is
None` and that prefix is absent upstream, normalization adds the existing prefix to
`membership_warning_prefixes` and exactly one `current_snapshot_only` token to `flow_warnings`; if
it is already present, neither semantic value is duplicated. Thus a directly constructed
`IndexConstituents(as_of=None)` cannot produce a bulk result that omits the invariant warning, no
upstream description is rewritten, and no new date is inferred.

The normalization is deliberately executable rather than a name-based cast of the live model. The
runtime warning container must remain the shipped `tuple[str, ...]` shape:

```python
def normalize_membership_warnings(
    constituents: IndexConstituents,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[ForeignFlowWarning, ...]]:
    raw_value = constituents.warnings  # IndexConstituents.warnings: tuple[str, ...]
    if not isinstance(raw_value, tuple) or any(
        not isinstance(warning, str) for warning in raw_value
    ):
        raise InvalidData("membership warnings must be tuple[str, ...]")
    if any(not warning.strip() for warning in raw_value):
        raise InvalidData("membership warning must be a non-empty string")
    raw_prefixes = [warning.split(":", 1)[0].strip() for warning in raw_value]
    if any(not prefix for prefix in raw_prefixes):
        raise InvalidData("membership warning prefix must be non-empty")
    raw = tuple(raw_value)
    prefixes = list(dict.fromkeys(raw_prefixes))
    flow: list[ForeignFlowWarning] = []
    if "current_snapshot_only" in prefixes:
        flow.append("current_snapshot_only")
    if constituents.as_of is None and "current_snapshot_only" not in prefixes:
        prefixes.append("current_snapshot_only")
        flow.append("current_snapshot_only")
    return raw, tuple(prefixes), tuple(flow)
```

The returned triple maps to `membership_warnings`, `membership_warning_prefixes`, and
`ForeignFlowMembershipContext.flow_warnings`; `ForeignFlowBulk.warnings` and the
`membership_flow_warnings` dataframe attr expose the last tuple. The raw warning tuple is never
assigned to the bounded flow-warning field, so descriptive text remains losslessly recoverable
without widening the public warning registry.

An `IndexMember` preserves its optional exchange. A plain-string iterable requires the explicit
`exchange=...` argument; omitting it is a whole-call preflight `InvalidData`, not board inference.
A typed `IndexMember`/`IndexConstituents` input may carry an explicit exchange per member; a
member without one becomes an `unsupported_exchange` item and makes no HTTP call. If an explicit
exchange conflicts with an `IndexMember.exchange`, preflight rejects the request. Mixed-board
bulk identity is the pair `(exchange, symbol)`, never symbol alone.

The safe current-membership pattern is:

```python
from vnfin.indices import index_constituents
from vnfin.equities import foreign_flow_bulk

members = index_constituents("VN30")
bundle = foreign_flow_bulk(
    members,                         # preserve source/fetch/as_of/warnings
    start=date(2018, 1, 1),
    end=date.today(),
)
```

This is a current membership basket, not point-in-time VN30 history. `as_of=None` remains
unknown; the membership context, bulk warnings, summary attrs, and `current_snapshot_only=True`
must all carry the exact stable token, and the result must never claim that returned symbols
belonged to the basket throughout the requested history. Passing `members.symbols` is a lossy
escape hatch and is not the documented VN30 path because it discards that context.

`ForeignFlowBulk.warnings` contains the deduplicated bounded `flow_warnings`; its dataframe attrs
also expose `membership_warnings`, `membership_warning_prefixes`, and `membership_flow_warnings`
so the exact upstream descriptions and their semantic projection are both recoverable.

### 3.2 Bulk result, failures, and request budget

```python
@dataclass(frozen=True)
class ForeignFlowFailure:
    symbol: str
    exchange: Exchange | None
    code: ForeignFlowFailureCode
    attempts: tuple[ForeignFlowSourceAttempt, ...]

@dataclass(frozen=True)
class ForeignFlowBulkItem:
    symbol: str
    exchange: Exchange | None
    history: ForeignFlowHistory | None
    failure: ForeignFlowFailure | None

@dataclass(frozen=True)
class ForeignFlowBulk(TimeSeriesResult):
    requested_symbols: tuple[str, ...]
    requested_keys: tuple[ForeignFlowKey, ...]
    items: tuple[ForeignFlowBulkItem, ...]
    membership_context: ForeignFlowMembershipContext | None
    requested_start: date
    requested_end: date
    interval: Interval
    fetched_at_utc: datetime
    warnings: tuple[ForeignFlowWarning, ...] = ()
```

`ForeignFlowBulkItem` has an XOR invariant: exactly one of `history` and `failure` is
non-null. There is exactly one item per canonical requested key, in canonical first-seen input
order. A failure is data, never a silent omission.

Bulk preflight is deterministic and happens before HTTP:

1. Materialize an iterable exactly once. A bare `str`/`bytes` is invalid; an empty input is
   invalid; a typed `IndexConstituents` object is the sole context-bearing basket path.
2. Canonicalize every symbol before scheduling. Duplicate `(exchange, symbol)` keys, including
   case-folded duplicates, reject rather than silently deduplicate.
3. Refuse an input over `max_symbols` and reject malformed exchange/member conflicts before any
   budget reservation or source call.

Because `ForeignFlowBulk` inherits `TimeSeriesResult`, the future implementation must provide
the full mixin contract:

```python
_items_attr = "items"
_index_column = "request_key"
_df_columns = (
    "request_key", "status", "failure_code", "exchange", "source", "dataset_id",
    "row_count", "served_start", "served_end", "attempt_count",
)

def _row_record(item: ForeignFlowBulkItem) -> dict: ...
def _df_attrs(self) -> dict: ...
```

Its summary dataframe has one row per item, a stable `request_key` index
(`"{exchange or '?'}:{symbol}"`), the columns above, and attrs for
`requested_symbols`, `requested_keys`, `requested_start`, `requested_end`, `interval`,
`membership_context`, `membership_index`, `membership_source`, `membership_provider_group`,
`membership_fetched_at_utc`, `membership_as_of`, `membership_warnings`,
`membership_warning_prefixes`, `membership_flow_warnings`, `current_snapshot_only`,
`fetched_at_utc`, and total source-attempt,
logical-page, physical-request, and retry counts. `status` is only `"success"` or `"failure"`;
failure rows use a bounded `failure_code` and immutable attempts; no free-form provider or
generated `message` is part of the public failure model. A caller may render a fixed, static
code-to-template diagnostic outside the data model. Successful rows expose source/dataset, row
count, and served bounds. Successful histories remain the only row-level data view.

Exact budget rules:

1. `max_symbols` is lowering-only: `1 <= max_symbols <= 100`; values above the hard cap reject
   before network. An input exceeding the selected ceiling is rejected, never silently truncated;
   the parameter cannot raise the safety ceiling.
2. `max_total_source_attempts` accepts `1..200` and defaults to 100, so a 100-symbol request has
   one source-selection ticket per canonical symbol; it may be lowered, or raised only to the hard
   cap of 200 when two-source failover is required. `max_total_pages` is lowering-only from 5,000;
   `max_total_requests` is lowering-only from 6,000. Pages count logical pages and requests count
   every physical page request, initial and retry, across symbols and sources.
3. Per-symbol `max_source_attempts` accepts `1..2` and defaults to `2`; it counts source
   selections. `max_transport_retries` accepts `0..1` and defaults to `1`; it counts sequential
   retries of one logical page. They are reported separately and never multiplied invisibly.
4. `max_concurrency` is exactly `1`; any other value is preflight `InvalidData`. No parallel
   fan-out is part of this source-gap contract. It can be reconsidered only after a source owner
   supplies rate/concurrency terms and a later gate approves a separately specified wave/barrier
   scheduler.
5. A source has a hard page ceiling of 250. A ceiling hit is `page_budget_exhausted` when the
   invocation ledger cannot reserve the next logical page; a source that returns a bounded but
   incomplete result without a budget stop is `coverage_gap` when full coverage is required. A
   ceiling hit is never a successful partial result.
6. The invocation ledger and canonical reservation queue in §2.5 reserve source-attempt, logical-
   page, request, and retry capacity at their distinct points. If a reservation fails, no physical
   HTTP call is issued for that ticket; completed items remain, current/queued items receive the
   actual dimension-specific failure code, and no item is silently dropped.

> **Future, non-authoritative design sketch — not approved for implementation.** Source routes and
> parser rules below document reopen conditions; they are not adapter approval.

## 4. Future source boundaries and exact normalization

### 4.1 Technical-candidate table (no enabled chain)

| Source | Official route | Request shape | source_type / dataset_id | Current status |
|---|---|---|---|---|
| `hsx_market_tradingresult_v1` | `/mk/api/v1/market/securities/tradingresult/{code}` | GET `fromDate`, `toDate`, `pageIndex`, observed `pageSize=20` | `official_exchange` / `hsx.market.securities.tradingresult.v1.0` | reachability pass; semantics/legal unresolved; disabled |
| `hnx_report_ny_v1` | `Report_MD_TradingResult/ListData_Listed` | POST one requested date; `default-date` coupling observed; HTML pagination | `official_exchange` / `hnx.report.stocketfs.tradingresult.listed.v1` | technical candidate; response date identity/legal unresolved; disabled |
| `hnx_report_uc_v1` | `Report_MD_TradingResult/ListData_UPCoM` | POST report; historical date ignored in probe | `official_exchange` / `hnx.report.stocketfs.tradingresult.upcom.v1` | historical coverage fail/legal unresolved; disabled |

There is no default source chain. The rejected HOSE `foreign/{code}` route is intentionally absent
because it does not return the requested symbol. No source row may be stitched with another board
or another endpoint.

### 4.2 HOSE future parser boundary

The official date-filtered route returned a `symbol` field and component names for order
matching and put-through buy/sell volume/value. A future adapter may normalize those fields only
after owner evidence confirms:

* `reportDate` epoch, timezone, and exchange-session-date mapping;
* raw multiplier and exact shares/VND meaning;
* stable field names, error envelopes, invalid-symbol/empty behavior, and intended automated use;
* publication cadence/current-session lag, pagination ceilings, and rate/concurrency terms.

Once reopened, the parser must request the observed fixed `pageSize=20`. Page 1 establishes the
expected `(totalCount, totalPages, pageSize)` tuple. Every subsequent page must return the same
tuple, and `pageIndex` must equal the requested page number. The client requests every page from
1 through `totalPages` exactly once: a non-final page is non-empty and contains exactly
`pageSize` rows; the final page contains exactly the remaining `totalCount` rows; gathered row
count equals `totalCount`. Repeated pages, missing pages, early-empty pages, changed metadata,
cross-page identity conflicts, or `totalPages > 250` reject the entire source result. No partial
history is returned after pagination truncation. Global logical-page and physical-request budgets
are enforced before each call.

It must canonicalize and compare returned `symbol`. `reportDate` is retained as an observed
integral/epoch-like field; no epoch unit, timezone, or exchange-session mapping is selected before
owner evidence. After a future gate confirms those three facts, conversion must use that confirmed
mapping, not the local machine timezone and not a preselected UTC convention. RED cases must place
the same candidate value on both sides of a UTC/Vietnam date boundary, exercise every claimed epoch
unit, and verify that an unresolved mapping remains unresolved rather than becoming a session date.
A date outside the inclusive request range, or missing/malformed date identity after the owner-
confirmed mapping is known, rejects the source.

Buy/sell totals are derived by exact integer addition of the four published components; net is
signed `buy - sell`. If a provider total/net is also published, it is compared and conflicts
reject the source. No implicit scale factor is ever applied.

### 4.3 Rejected HOSE route

The observed `foreign/{code}` route has no date bound and does not echo a symbol. The path token
proves only the request, not the response. It is removed from the source protocol and cannot be
a whole-result fallback. It may return only as a future candidate if first-party evidence adds
response-backed symbol identity and the entire source gate is reopened.

### 4.4 HNX future boundary

The listed HNX POST returned HTML rows with security code/ISIN and buy/sell fields, but the
request-date/`default-date` coupling is not authoritative response identity. A future adapter
must reject the response unless the response itself contains an owner-confirmed session marker
equal to the requested date (or equivalent response-backed proof). Missing, malformed, or
mismatched response date identity is a hard rejection; it must not derive `session_date` from the
request alone.

The VND value label is explicit; the volume label is quantity-like but does not establish shares.
The adapter remains disabled until the owner confirms the raw volume scale, field stability,
pagination, publication cadence, intended automated use, and reuse terms. UPCoM is
`HISTORICAL_COVERAGE_FAIL` and `RESPONSE_DATE_IDENTITY_UNRESOLVED`: identical snapshots were
returned for current, historical, and very old date inputs, so they must not be interpreted as
historical data.

## 5. Coverage, legal gate, and reopen evidence

### 5.1 Coverage truth

| Dimension | Future contract |
|---|---|
| Exchange identity | Explicit requested/source-bound `HOSE`, `HNX`, or `UPCOM`; unknown exchange fails before HTTP |
| Target period | Caller may request 2018-current; served bounds are source/per-symbol truth |
| Dataset inception/listing | Never inferred; first row is `served_start`, not a backfill |
| Expected sessions | Only an owner-approved provider completeness marker or approved calendar can establish them |
| Publication lag | Owner-confirmed cadence and lag required; unresolved lag means partial, never full |
| Internal gaps | Known missing dates are listed; an unavailable calendar is `unobservable`, never “complete” |
| Missing dates | No fill, interpolation, calendar reconstruction, or cross-source backfill |
| Frequency | D1 only; one normalized row per authoritative source session date |
| VN30 | Current membership context only; never point-in-time fiction |

The current regulator disclosure rule establishes a publication obligation, not an open historical
consumer feed or a licence. The report's official legal references are evidence for the source
owner discussion, not permission.

### 5.2 Owner and legal evidence

The owner paths and full conjunctive reopen checklist are maintained in
`docs/research/2026-08-22-vn-foreign-flow-source-vetting.md §7`. The actual first-party contact
channels are the [HOSE contact page](https://www.hsx.vn/vi/lien-he) and [HNX contact page](https://www.hnx.vn/vi-vn/lien-he.html).
Before any implementation gate, record the official contact/channel, date, responding owner/team,
written artifact/reference, and exact dataset/endpoint. Evidence must cover:

1. no-paid automated OSS runtime use and intended UI/XHR/API use;
2. exact endpoint/dataset, attribution, retention, caching, replay, and downstream redistribution;
3. raw volume multiplier, shares meaning, exact VND semantics, and no display scaling ambiguity;
4. returned symbol and returned session-date identity, including epoch/timezone convention;
5. stable fields and documented invalid/empty/error/schema-drift shapes;
6. listing/delisting/rename/board-transfer/corporate-action identity;
7. inception, publication cadence, current-session lag, and missing-session meaning;
8. pagination, rate/concurrency limits, retries, cache/retention, and change notification.

Until then, behavior is source-gap closure only:

* no source is enabled and the default chain is empty;
* no provider rows, real cassettes, persistent cache, runtime call, or live CI test;
* only synthetic fixtures may use invented values and schematic field names;
* no parser/model/facade may be added to the package;
* no source attribution text is a licence claim.

> **Future, non-authoritative design sketch — not approved for implementation.** This matrix is a
> future RED-first contract and not a claim that tests or production code exist.

## 6. Verification and future implementation/release gates

This section is a future RED → GREEN → REFACTOR matrix, not a claim that tests were added.

All adapter tests must use committed synthetic JSON/HTML fixtures with invented values. No real
provider rows or bundled datasets are permitted. Live endpoint tests are opt-in and untracked.

| Area | Required offline checks |
|---|---|
| Preflight | D1-only, plain dates, ordering, future bound, symbol grammar, explicit/unknown exchange, zero HTTP calls |
| Source gating | empty default chain, disabled-source rejection, bounded source/dataset/type tuple |
| Signed arithmetic | non-negative gross bounds, signed net bounds, exact buy-minus-sell, provider-total/net conflict, validated published-net origin versus derived-net origin |
| Units | explicit shares/lots/thousands and raw/scaled-VND fixtures, acceptance only after gate, unknown/fractional/negative/overflow/boolean rejection |
| HOSE envelope | success flag, list/paging shape, stable page index/size/counts, page-size cap, malformed JSON, provider error |
| Pagination | total-count arithmetic, total-pages arithmetic, repeated/missing/early-empty pages, page-index/page-size drift, ceiling boundary, zero/nonzero truncation both fail, no partial on truncation |
| Identity/date | missing/blank/aggregate/cross-symbol response identity, mismatch, observed integral/epoch-like `reportDate`, owner-confirmed unit/timezone/session mapping only, UTC/Vietnam boundary RED cases, unresolved mapping stays unresolved, out-of-range rows, row exchange mismatch |
| HNX | malformed HTML, request-date coupling rejected without returned marker, missing/renamed/wrong-type/schema-drift fields, current snapshot cannot satisfy historical request |
| Coverage | executable full/partial-known/partial-unknown field invariants, sorted unique missing/internal-gap dates and subset/count relations, reason ordering, confirmed/unresolved publication lag and cutoff, calendar unknown, pre-listing, stale end, matching partial warning, `require_full`, no synthesized dates |
| Failover | partial continues to compatible source, full outranks partial, exact `coverage_rank()` tuple/tie-break, deterministic `exchange_unavailable`/`coverage_gap`/`all_sources_failed`, immutable error attempts, no stitching, capability-incompatible sources omitted, identity/unit/schema attempts retained |
| Attempts | lowercase status/reason invariant, bounded success reasons, capability skips omitted with zero budget, source attempts versus per-page retry ledger, global request accounting, dimension-specific budget codes, caught-exception set, redacted diagnostics |
| Bulk input | iterable materialization, typed `IndexConstituents` context, exact upstream warning preservation, runtime tuple-of-strings validation, bare string/bytes/container rejection, empty warning/derived-prefix rejection, colon-prefix projection, missing-token append/no duplication, separate bounded flow warnings, `current_snapshot_only`, `as_of=None`, mixed-board `(exchange,symbol)`, duplicate/empty/string rejection |
| Bulk budget | atomic ledger passed to sources, strict sequential scheduler, one source/page reservation versus per-page physical requests/retries, 100 default/200 hard-cap source attempts, 5,000-page/6,000-request boundaries, dimension-specific queued failures, no silent drop |
| Bulk result | XOR item invariant (both-null/both-present reject), stable order, bounded failure codes, full `TimeSeriesResult` mixin fields/index/attrs |
| Dataframe | exact row/summary columns, origin columns, attrs, units/source/coverage, duplicate-index backstop |
| Probe reproducibility | official-host-only opt-in command, `set -euo pipefail` with explicit curl-failure capture, exact 200/effective-URL/redirect/body gates, complete `Content-Type` parsing after its first colon, exact normalized MIME (media type before `;`), one-table HNX/UPCoM exact heading-row plus distinct data-row contract, generic/maintenance and unrelated-table/off-table-phrase negatives, colon-suffixed MIME negatives, payload observations gated on accepted transport/body, syntactic-only date markers, sanitized aggregate embedded in manifest, nonzero aggregation/manifest failures, raw output untracked |
| Public/release | docs contract, API snapshot, source/API/architecture docs, AI guidance, skill, changelog, build/wheel/archive inspection, clean-install import smoke |

A future implementation must run focused tests RED-first, then the full merged offline suite before
and after refactoring, coverage/docs/API gates, mandatory blacklist and previous-contamination scan,
no-secrets scan, provider-row scan, `git diff --check`, build, wheel/archive inspection, and
clean-install smoke. No such implementation or test claim is made by this correction packet.

## 7. Re-review request

This correction round is deliberately source-gap closure, not a proposal to choose between HOSE
and HNX. Please review this note and the research report against B1–B2 in
`reviews/review-202608221518-issue201-exact-closure-review.md`. At handoff, the reviewer should spawn
parallel sub-agents for route/body/MIME fail-closed checks and runtime warning-container/prefix
validation.

The required decision is whether the packet now precisely documents the gap and conjunctive reopen
criteria. No parser, adapter, public model, facade, source chain, production code, push, or issue
close is authorized until a later reviewer design gate returns **PASS**.
