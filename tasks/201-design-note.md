# #201 design note — Vietnamese equity foreign-investor daily flow

**Status:** `BLOCKED — source-gap closure; no source enabled; correction round pending re-review`
**Reviewer gate:** design BLOCK at reviewer commit `e5ed626`; report
`reviews/review-202608221350-issue201-design-gate.md`
**Issue:** #201; public triage `issuecomment-5378368603`
**Research evidence:** `docs/research/2026-08-22-vn-foreign-flow-source-vetting.md`
**Clean-room:** primary official exchange/regulator pages and first-party UI/Swagger inspection only; the mandatory repository blacklist was applied to every search and no excluded material was opened or used.
**Authorization boundary:** this entire note is a future, non-authoritative design artifact. It authorizes no parser, adapter, public model, facade, source chain, runtime request, cache, production code, push, or issue close.

## 0. Source-gap closure disposition

No candidate currently satisfies the accepted source gate. The current default source chain is
**empty**. The only permitted work before a new design gate is source-owner evidence collection,
correction of this packet, and deterministic offline contract planning.

| Candidate | Technical reachability | Coverage | Response identity/date | Units/fields | Legal/reuse | Disposition |
|---|---|---|---|---|---|---|
| HOSE `tradingresult/{code}` | `TECHNICAL_REACHABILITY_PASS` observed without credentials | `HISTORICAL_COVERAGE_SAMPLED_ONLY`; three names do not prove market-wide completeness | Symbol is returned; epoch/session-date semantics `UNRESOLVED` | Raw scale, shares/VND meaning, field stability `UNRESOLVED` | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `DISABLED` |
| HOSE `foreign/{code}` | HTTP reachability observed | History sampled | `RESPONSE_IDENTITY_MISSING_REJECTED`; response does not echo symbol | Units/field stability unresolved | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `DISABLED; not a fallback` |
| HNX listed report | `TECHNICAL_CANDIDATE_UNDOCUMENTED` | Historical samples only; no range/completeness proof | `RESPONSE_DATE_IDENTITY_UNRESOLVED`; request-date coupling is not returned identity | VND label present; volume scale/field stability unresolved | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `DISABLED` |
| HNX UPCoM report | Current snapshot reachable | `HISTORICAL_COVERAGE_FAIL`; historical date inputs were ignored | `RESPONSE_DATE_IDENTITY_UNRESOLVED`; unchanged snapshots do not prove requested date | VND label present; volume semantics unresolved | `LEGAL_UNRESOLVED_PERMISSION_REQUIRED` | `DISABLED` |

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
5. When the explicit exchange has no enabled source, the call returns
   `exchange_unavailable` or `coverage_gap` naming the board and evidence-backed gap; it never falls through to
   another exchange.
6. `max_source_attempts` and `max_transport_retries` are positive bounded integers; their
   diagnostics are distinct and redacted.

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
        max_concurrency: int = 1,
        max_symbols: int = 100,
        max_total_source_attempts: int = 60,
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
    max_concurrency: int = 1,
    max_symbols: int = 100,
    max_total_source_attempts: int = 60,
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
  pass, and truncation did not occur. It carries explicit served bounds and a bounded coverage
  reason.
* An internal gap is listed when an approved calendar identifies missing sessions. If no approved
  calendar exists, internal completeness is `UNOBSERVABLE`; the result remains partial, never
  full. Missing dates are never filled.
* A source returning partial coverage does not stop the chain: compatible enabled sources are
  tried. The first valid `full` result wins. If no full result exists, `partial_known` ranks above
  `partial_unknown`; among known partials, least uncovered-session count, then least internal-gap
  count, then configured source priority wins. Among unknown partials, configured source priority
  wins. Row count alone is never a quality tie-break.
* `require_full=True` rejects all partial results with `coverage_gap`. No source rows
  are stitched, appended, or used to repair another source.
* Attempt statuses are retained: `DISABLED`, `TRANSPORT_FAILED`, `SCHEMA_REJECTED`,
  `IDENTITY_REJECTED`, `UNITS_REJECTED`, `EMPTY`, `COVERAGE_REJECTED`,
  `VALID_PARTIAL`, or `VALID_FULL`.
* If all compatible sources fail, raise a typed future `ForeignFlowCoverageUnavailable` or
  `ForeignFlowAllSourcesFailed` carrying immutable, redacted attempts. An unsupported board
  never falls through to another board.

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
        request_budget: RequestBudget,
    ) -> ForeignFlowHistory: ...
```

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
values must be whole signed integers in `[-MAX_ABS_INTEGER, MAX_ABS_INTEGER]`. Boolean values,
fractional values, non-finite values, overflow, unknown-scale, or negative gross values fail
closed. Exact integral provider floats may be normalized to integers. If a provider publishes a
net field, it must equal the derived difference or the entire source result is rejected; the
normalized net remains `DERIVED` so its signed arithmetic is unambiguous. A net is `None` and
`MISSING` whenever either gross operand is missing.

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

@dataclass(frozen=True)
class ForeignFlowCoverage:
    status: CoverageStatus
    reason: CoverageReason
    expected_session_count: int | None
    served_session_count: int
    missing_session_dates: tuple[date, ...]
    internal_gap_status: Literal["none", "known", "unobservable"]
```

`full` is legal only when pagination is complete, all identities/arithmetic validate, the source
contract proves every requested exchange session is represented, and the current publication lag
is within the owner-confirmed bound. `partial_known` is structurally valid but bounded by a known
dataset/symbol inception, source window, publication lag, or known internal gap. `partial_unknown`
has valid rows but complete session coverage cannot be proved. Any unknown calendar, missing
interior session, stale end, source listing uncertainty, or unresolved publication lag prevents
`full`; a page-budget stop is not a partial result but a typed failure. A source with an
authoritative calendar treats weekends/holidays as non-sessions, never as missing rows.

```python
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
    warnings: tuple[str, ...] = ()
    attempts: tuple[ForeignFlowSourceAttempt, ...] = ()
```

The future model must set `_items_attr = "rows"`, `_index_column = "session_date"`, and a
fixed `_df_columns` order. `.to_dataframe()` attaches these attrs:

```text
symbol, exchange, interval, frequency, source, dataset_id, source_type,
requested_start, requested_end, served_start, served_end,
coverage_status, coverage_reason, expected_session_count, served_session_count,
volume_unit, value_unit, currency, fetched_at_utc
```

Rows have the identity columns, six numeric fields, and six stable `*_origin` columns. No
credential-bearing URL appears in dataframe metadata. `fetched_at_utc` is aware UTC and
`warnings`/attempts are tuples.

Every row must satisfy `row.symbol == history.symbol` and
`row.exchange == history.exchange`. The result is source-homogeneous: every row inherits the
exact `(source, dataset_id, source_type, exchange)` identity of its enclosing result. Cross-source
row stitching is forbidden.

### 2.5 Attempts, budgets, and bounded diagnostics

```python
ForeignFlowAttemptStatus = Literal[
    "disabled", "transport_failed", "schema_rejected", "identity_rejected",
    "units_rejected", "empty", "coverage_rejected", "valid_partial", "valid_full",
]

ForeignFlowFailureCode = Literal[
    "unsupported_exchange", "exchange_unavailable", "coverage_gap", "empty_data",
    "all_sources_failed", "source_unavailable", "transport_retry_exhausted",
    "malformed_payload", "schema_drift", "identity_missing", "identity_mismatch",
    "unit_mismatch", "arithmetic_conflict", "pagination_invalid",
    "page_budget_exhausted", "request_budget_exhausted", "attempt_budget_exhausted",
]

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
    reason_code: ForeignFlowFailureCode
```

`source_attempt_number` counts candidate source selections. `transport_requests` counts
actual HTTP requests, including bounded retries. They are never conflated. Transport errors,
HTTP statuses, URLs, symbols, and provider messages are redacted to bounded public error codes.

The future public coverage error is named and bounded:

```python
class ForeignFlowCoverageError(VnfinError):
    symbol: str
    exchange: Exchange
    requested_start: date
    requested_end: date
    code: ForeignFlowFailureCode
```

Per-symbol bulk handling may catch only source-layer `SourceUnavailable`, `EmptyData`/
`StaleData`, `InvalidData`, `AllSourcesFailed`, `ForeignFlowCoverageError`, and adapter-wrapped
`TimeoutError`, `ConnectionError`, or `OSError`. It must never catch arbitrary `Exception`.
Preflight `InvalidData` remains a whole-call error. Unexpected programming errors escape.

The shared invocation budget is explicit and immutable:

```python
@dataclass(frozen=True)
class RequestBudget:
    max_source_attempts: int = 60
    max_pages: int = 5_000
    max_requests: int = 6_000
    max_transport_retries_per_request: int = 1
```

One source attempt means one `(symbol, source)` invocation; one logical page means one provider
page; one physical request means every transport call, including retries. A transport retry
consumes request budget but never creates a new source attempt. All reservations happen before
the physical call and are shared across the entire bulk invocation, not the client lifetime.

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
    warnings: tuple[str, ...]

ForeignFlowKey = tuple[Exchange | None, str]
```

`foreign_flow_bulk(members, ...)` accepts one `IndexConstituents` object directly; a raw symbol
iterable and typed constituent input are mutually exclusive. It copies
`index`, `source`, `provider_group`, `fetched_at_utc`, `as_of`, and `warnings` into the immutable
`ForeignFlowMembershipContext`; it never fabricates `as_of`. If `as_of is None`, it preserves
the existing stable `current_snapshot_only` warning (and adds no replacement token).

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
unknown; the bulk result must carry `current_snapshot_only` and never claim that returned
symbols belonged to the basket throughout the requested history. Passing `members.symbols`
is a lossy escape hatch and is not the documented VN30 path because it discards that context.

### 3.2 Bulk result, failures, and request budget

```python
@dataclass(frozen=True)
class ForeignFlowFailure:
    symbol: str
    exchange: Exchange | None
    code: ForeignFlowFailureCode
    message: str                    # bounded/redacted, never raw provider text
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
    warnings: tuple[str, ...] = ()
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
`membership_fetched_at_utc`, `membership_as_of`, `membership_warnings`, `current_snapshot_only`,
`fetched_at_utc`, and total source-attempt,
logical-page, physical-request, and retry counts. `status` is only `"success"` or `"failure"`;
failure rows use a bounded `failure_code`, and successful rows expose source/dataset, row count,
and served bounds. Successful histories remain the only row-level data view.

Exact budget rules:

1. `max_symbols` is lowering-only: `1 <= max_symbols <= 100`; values above the hard cap reject
   before network. An input exceeding the selected ceiling is rejected, never silently truncated;
   the parameter cannot raise the safety ceiling.
2. `max_total_source_attempts` is lowering-only from 60; `max_total_pages` is lowering-only
   from 5,000; `max_total_requests` is lowering-only from 6,000. Pages count logical pages and
   requests count every physical page request, initial and retry, across symbols and sources.
3. Per-symbol `max_source_attempts=2` counts source selections; `max_transport_retries=1` counts
   retries of one page. They are reported separately and never multiplied invisibly.
4. `max_concurrency` accepts 1–4 but defaults to 1. No parallel fan-out is authorized until a
   source owner supplies rate/concurrency terms and a later gate approves it.
5. A source has a hard page ceiling of 250, but a ceiling hit is `page_budget_exhausted` or
   `coverage_gap`, never a successful partial result.
6. Before every physical HTTP call, the shared budget reserves source-attempt, logical-page,
   request, and retry capacity. If any global budget is exhausted, no further HTTP call is issued;
   completed items remain; current/truncated items receive `request_budget_exhausted` or
   `page_budget_exhausted`; queued items receive `request_budget_exhausted`; no item is silently
   dropped and no new source attempt starts.

> **Future, non-authoritative design sketch — not approved for implementation.** Source routes and
> parser rules below document reopen conditions; they are not adapter approval.

## 4. Future source boundaries and exact normalization

### 4.1 Technical-candidate table (no enabled chain)

| Source | Official route | Request shape | Source type/dataset | Current status |
|---|---|---|---|---|
| `hsx_market_tradingresult_v1` | `/mk/api/v1/market/securities/tradingresult/{code}` | GET `fromDate`, `toDate`, `pageIndex`, observed `pageSize=20` | official JSON / `hsx.market.securities.tradingresult.v1.0` | reachability pass; semantics/legal unresolved; disabled |
| `hnx_report_ny_v1` | `Report_MD_TradingResult/ListData_Listed` | POST one requested date; `default-date` coupling observed; HTML pagination | official HTML / `hnx.report.stocketfs.tradingresult.listed.v1` | technical candidate; response date identity/legal unresolved; disabled |
| `hnx_report_uc_v1` | `Report_MD_TradingResult/ListData_UPCoM` | POST report; historical date ignored in probe | official HTML / `hnx.report.stocketfs.tradingresult.upcom.v1` | historical coverage fail/legal unresolved; disabled |

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

It must canonicalize and compare returned `symbol`. `reportDate` is accepted only as a finite
integral Unix-seconds value and is converted exactly with
`datetime.fromtimestamp(ts, timezone.utc).date()`; local machine timezone conversion is
forbidden. A converted date outside the inclusive request range rejects the source. Missing or
malformed date identity is a hard rejection until owner evidence changes the contract.

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
`docs/research/2026-08-22-vn-foreign-flow-source-vetting.md §7`. Before any implementation gate,
record the official contact/channel, date, responding owner/team, written artifact/reference, and
exact dataset/endpoint. Evidence must cover:

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
| Signed arithmetic | non-negative gross bounds, signed net bounds, exact buy-minus-sell, provider-total/net conflict |
| Units | explicit shares/lots/thousands and raw/scaled-VND fixtures, acceptance only after gate, unknown/fractional/negative/overflow/boolean rejection |
| HOSE envelope | success flag, list/paging shape, stable page index/size/counts, page-size cap, malformed JSON, provider error |
| Pagination | total-count arithmetic, total-pages arithmetic, repeated/missing/early-empty pages, page-index/page-size drift, ceiling boundary, zero/nonzero truncation both fail, no partial on truncation |
| Identity/date | missing/blank/aggregate/cross-symbol response identity, mismatch, returned-date missing/mismatch, epoch timezone/session conversion, out-of-range rows, row exchange mismatch |
| HNX | malformed HTML, request-date coupling rejected without returned marker, missing/renamed/wrong-type/schema-drift fields, current snapshot cannot satisfy historical request |
| Coverage | full proof versus partial, calendar unknown, known internal gap, publication lag, pre-listing, stale end, `require_full`, no synthesized dates |
| Failover | partial continues to compatible source, full outranks partial, exact partial ranking/tie-break, no stitching, fallback remains disabled/rejected, disabled/identity/unit/schema attempts retained |
| Attempts | source attempts versus transport retries, capability skips consume no budget, global request accounting, bounded codes, caught-exception set, redacted diagnostics |
| Bulk input | iterable materialization, typed `IndexConstituents` context, `current_snapshot_only`, `as_of=None`, mixed-board `(exchange,symbol)`, duplicate/empty/string rejection |
| Bulk budget | lowering-only caps, sequential default, max workers, global 60-attempt/5,000-page/6,000-request boundaries, queued budget failures, no silent drop |
| Bulk result | XOR item invariant (both-null/both-present reject), stable order, bounded failure codes, full `TimeSeriesResult` mixin fields/index/attrs |
| Dataframe | exact row/summary columns, origin columns, attrs, units/source/coverage, duplicate-index backstop |
| Probe reproducibility | official-host-only opt-in command, no-secret headers/redirect allowlist, client/repo version, sanitized status/digest/count manifest, raw output untracked |
| Public/release | docs contract, API snapshot, source/API/architecture docs, AI guidance, skill, changelog, build/wheel/archive inspection, clean-install import smoke |

A future implementation must run focused tests RED-first, then the full merged offline suite before
and after refactoring, coverage/docs/API gates, mandatory blacklist and previous-contamination scan,
no-secrets scan, provider-row scan, `git diff --check`, build, wheel/archive inspection, and
clean-install smoke. No such implementation or test claim is made by this correction packet.

## 7. Re-review request

This correction round is deliberately source-gap closure, not a proposal to choose between HOSE
and HNX. Please review this note and the research report against B1–B6 in
`reviews/review-202608221350-issue201-design-gate.md`. At handoff, the reviewer should spawn
three parallel sub-agents: source/legal/reopen evidence, API/identity/coverage semantics, and
bulk/budget/verification adversarial review.

The required decision is whether the packet now precisely documents the gap and conjunctive reopen
criteria. No parser, adapter, public model, facade, source chain, production code, push, or issue
close is authorized until a later reviewer design gate returns **PASS**.
