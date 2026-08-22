# #201 design note — Vietnamese equity foreign-investor daily flow

**Status:** source-gated design → **requesting reviewer PASS**; no production code in this change
**Issue:** #201
**Reviewer packet:** `~/tools/vnfin-oss-reviewer/tasks/201-vn-equity-foreign-flow-spec.md`, reviewer commit `62e1e32`
**Public triage:** `issuecomment-5378368603`
**Research evidence:** `docs/research/2026-08-22-vn-foreign-flow-source-vetting.md`
**Clean-room:** primary official exchange/regulator pages and first-party UI/Swagger inspection only; the mandatory repository blacklist was applied to every search and no excluded material was opened or used.

## 0. Gate result and recommendation

The design is ready for review, but source/legal clearance is not yet PASS:

* **HOSE:** technically viable for a bounded 2018-current request using the official
  date-filtered market API. The same-host unbounded foreign route is a fallback. Both require
  written confirmation of OSS/runtime use, attribution, caching, and redistribution terms
  before code is enabled.
* **HNX listed:** the official page exposes the right columns and its underlying no-auth POST
  returned sampled historical dates in 2018–2026 when the `default-date` request token matched
  the requested session. This is an undocumented per-session HTML seam, not a date-range API,
  and HNX's official fee/catalogue material points to paid data services.
* **UPCoM:** the official endpoint returned the same current snapshot for current, 2018, and
  2000 date inputs, so it remains a historical source gap.
* **Recommended implementation boundary:** HOSE-first after legal sign-off; preserve the
  public contract's exchange field and typed unavailable/partial failures so adding HNX/UPCoM
  later does not require cross-source stitching.

If the reviewer interprets #201 as requiring all three boards before any implementation, this
note recommends **BLOCK pending HNX rights/contract and UPCoM source-gap closure**. The library
must not turn an undocumented HNX seam or a current UPCoM snapshot into an unqualified
historical series.

## 1. Public API

### 1.1 One obvious single-symbol facade

The public entry is `vnfin.equities.foreign_flow`:

```python
from datetime import date

from vnfin import Interval
from vnfin.equities import foreign_flow

history = foreign_flow(
    "FPT",
    start=date(2018, 1, 1),
    end=date.today(),
    interval=Interval.D1,
)
```

Exact signature:

```python
def foreign_flow(
    symbol: str,
    start: date,
    end: date,
    interval: Interval = Interval.D1,
    *,
    exchange: str | None = None,       # HOSE | HNX | UPCOM; None = configured chain
    http_get=None,                     # deterministic test seam, never a public token
    timeout: float = 25.0,
    max_attempts: int = 2,
) -> ForeignFlowHistory: ...
```

Rules before any network call:

1. `symbol` is a non-empty canonical security identifier using the repository's shared
   security-symbol grammar; trim and uppercase exactly once.
2. `start` and `end` are plain `datetime.date` objects, not `datetime`; require
   `start <= end` and reject a future `end` using Vietnam time.
3. `interval is Interval.D1`; every other interval fails with `InvalidData` before source
   selection. No resampling or intraday interpretation is hidden behind this facade.
4. `exchange`, when present, is one of `HOSE`, `HNX`, or `UPCOM`. It restricts the source chain;
   it is never inferred from a symbol suffix or silently changed after a source response.
5. The default chain is the set of legally enabled sources only. The design candidate is
   `HSXTradingResultSource` followed by `HSXForeignHistorySource`; HNX/UPCoM adapters are not
   enabled until their history and rights gates pass.

`foreign_flow` returns one immutable `ForeignFlowHistory`. It never returns a dataframe by
   default, never fills non-trading dates, and never merges source segments.

### 1.2 Reusable failover client

```python
def foreign_flow_client(
    *,
    sources=None,                     # injected source sequence for tests/approved adapters
    http_get=None,
    timeout: float = 25.0,
    max_attempts: int = 2,
) -> ForeignFlowClient: ...


class ForeignFlowClient:
    def history(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: Interval = Interval.D1,
        *,
        exchange: str | None = None,
    ) -> ForeignFlowHistory: ...

    def history_bulk(
        self,
        symbols,
        start: date,
        end: date,
        interval: Interval = Interval.D1,
        *,
        exchange: str | None = None,
        max_concurrency: int = 4,
        max_symbols: int = 100,
    ) -> ForeignFlowBulk: ...
```

The matching one-shot bulk facade is:

```python
def foreign_flow_bulk(
    symbols,
    start: date,
    end: date,
    interval: Interval = Interval.D1,
    *,
    exchange: str | None = None,
    http_get=None,
    timeout: float = 25.0,
    max_attempts: int = 2,
    max_concurrency: int = 4,
    max_symbols: int = 100,
) -> ForeignFlowBulk: ...
```

`foreign_flow_bulk` constructs the same default client as `foreign_flow`; callers that need a
custom source chain use `foreign_flow_client().history_bulk(...)`. The two facades must share
the exact validation, source ordering, error redaction, and result model.

Failover is whole-result and coverage-compatible:

* A source is attempted for the complete requested `[start, end]` range.
* A source that returns malformed identity, units, date keys, duplicate dates, conflicting
  arithmetic, or an exceeded page ceiling is rejected and recorded as a failed
  `SourceAttempt`.
* The first validated result wins. The client never appends rows from a second source to repair
  a gap in the first result.
* The result's `source` and `dataset_id` identify the successful source; `attempts` records
  every tried source and a redacted reason. A failed source is not hidden merely because a
  later source succeeds.
* If all compatible sources fail, raise the repository's typed all-sources failure carrying
  the immutable attempt diagnostics. If a board has no enabled source, raise a typed coverage
  error naming the board and the evidence-backed gap; do not fall through to another board.

The source protocol is internal until a public adapter is approved:

```python
class ForeignFlowSource(Protocol):
    name: ForeignFlowSourceName
    supported_exchanges: frozenset[Exchange]

    def get_history(
        self, symbol: str, start: date, end: date, *, interval: Interval
    ) -> ForeignFlowHistory: ...
```

The source name is bounded to prevent arbitrary provider strings in a stable result:

```python
ForeignFlowSourceName = Literal[
    "hsx_market_tradingresult_v1",
    "hsx_market_foreign_v1",
    "hnx_report_ny_v1",       # future, disabled pending history/legal gate
    "hnx_report_uc_v1",       # future, disabled pending history/legal gate
]
Exchange = Literal["HOSE", "HNX", "UPCOM"]
```

## 2. Typed models and invariants

### 2.1 Field-level provenance

Gross buy/sell and net are not interchangeable. The result must show whether a value came from
the source or was calculated by vnfin:

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

For the HOSE `tradingresult` route, buy/sell totals are sums of its published order-matching
and put-through components, so all four gross totals are `DERIVED`; both net values are also
`DERIVED`. If the HOSE fallback's published total volume is used, that volume may be
`SOURCE_PUBLISHED` only after the component arithmetic agrees. A missing source component
produces `None` and `MISSING`; a present zero is never converted to missing.

### 2.2 One daily row

```python
@dataclass(frozen=True)
class ForeignFlowRow:
    session_date: date
    foreign_buy_volume: int | None       # shares
    foreign_sell_volume: int | None      # shares
    foreign_net_volume: int | None       # shares; buy - sell
    foreign_buy_value_vnd: int | None
    foreign_sell_value_vnd: int | None
    foreign_net_value_vnd: int | None    # VND; buy - sell
    provenance: ForeignFlowProvenance
```

Row invariants:

* `session_date` is a plain date and rows are strictly ascending by it.
* One date appears at most once. An identical duplicate may be deduplicated only if the full
  normalized row is identical; a conflicting duplicate rejects the entire source result.
* Volumes and VND values are finite, non-negative, whole-valued numbers at the provider
  boundary. Exact integral floats may be normalized to `int`; fractional values, strings with
  an unknown scale, negative gross values, and overflow fail closed.
* Net is calculated only when both gross operands are present. The arithmetic is integer
  arithmetic; no rounding or float subtraction is allowed.
* No calendar rows are synthesized for weekends, holidays, suspended sessions, pre-listing
  dates, or provider outages. Missing dates are represented by the requested/served coverage
  fields and warnings, not by zero rows.

### 2.3 Immutable history result

```python
@dataclass(frozen=True)
class ForeignFlowHistory(TimeSeriesResult):
    symbol: str
    exchange: Exchange
    interval: Interval                    # always Interval.D1
    frequency: str                        # always "daily"
    source: ForeignFlowSourceName
    dataset_id: str                       # bounded endpoint/dataset identity
    rows: tuple[ForeignFlowRow, ...]
    requested_start: date
    requested_end: date
    served_start: date | None
    served_end: date | None
    volume_unit: str                       # "shares"
    value_unit: str                        # "VND"
    currency: str                          # "VND"
    fetched_at_utc: datetime               # aware UTC only
    warnings: tuple[str, ...] = ()
    attempts: tuple[SourceAttempt, ...] = ()
```

The concrete model must set `_items_attr = "rows"`, `_index_column = "session_date"`, and an
explicit dataframe column order. `.to_dataframe()` must attach at least:

```text
symbol, exchange, interval, frequency, source, dataset_id,
requested_start, requested_end, served_start, served_end,
volume_unit, value_unit, currency, fetched_at_utc
```

The row-level dataframe columns are the six numeric fields plus six stable `*_origin` columns.
No provider URL containing credentials is placed in dataframe metadata. `fetched_at_utc` must
be timezone-aware UTC, and `warnings`/`attempts` must be tuples.

Stable warning prefixes for the first implementation:

```text
partial_start_coverage
partial_end_coverage
source_listing_or_inception_unknown
derived_total_volume
derived_total_value
derived_net
current_membership_snapshot
```

Warnings disclose facts; they do not turn incomplete history into a successful full-history
promise. The result remains one-source homogeneous even when `attempts` contains failed sources.

### 2.4 Typed bulk result

```python
@dataclass(frozen=True)
class ForeignFlowFailure:
    symbol: str
    error_type: str
    message: str
    attempts: tuple[SourceAttempt, ...]


@dataclass(frozen=True)
class ForeignFlowBulkItem:
    symbol: str
    history: ForeignFlowHistory | None
    failure: ForeignFlowFailure | None


@dataclass(frozen=True)
class ForeignFlowBulk(TimeSeriesResult):
    requested_symbols: tuple[str, ...]
    items: tuple[ForeignFlowBulkItem, ...]
    requested_start: date
    requested_end: date
    interval: Interval
    fetched_at_utc: datetime
    warnings: tuple[str, ...] = ()
```

`ForeignFlowBulkItem` has an XOR invariant: exactly one of `history` and `failure` is non-null.
There is exactly one item per canonical requested symbol, in canonical first-seen input order;
an individual failure is data, not a silent omission. The bulk container's dataframe is a
summary/diagnostics view; callers use each successful `history.to_dataframe()` for rows.

Bulk request rules:

1. Materialize the iterable once. A bare string is invalid; an empty iterable is invalid.
2. Canonicalize each symbol before any network request. Case-fold duplicates such as `fpt` and
   `FPT` are a preflight `InvalidData`, not silently deduplicated.
3. Refuse more than 100 unique symbols and `max_concurrency` outside 1–4 before network.
4. Preserve canonical input order in `requested_symbols` and `items`; internal scheduling may
   be sorted, but output order is stable.
5. HOSE has no native multi-symbol route in the approved candidate, so bulk uses bounded
   individual requests with at most four concurrent workers. A future HNX batch adapter may
   fetch a session table once and filter it, but it cannot be enabled as a historical fallback
   until its date coverage/legal gate passes.
6. A per-symbol page ceiling (`250` pages) and a client-wide bounded worker count prevent an
   accidental unbounded crawl. A symbol that exceeds a ceiling gets a typed failure item, not
   a partial successful history.

There is deliberately no `foreign_flow_bulk("VN30", ...)` overload. The safe current-membership
pattern is:

```python
from vnfin.indices import index_constituents
from vnfin.equities import foreign_flow_bulk

members = index_constituents("VN30")
bundle = foreign_flow_bulk(
    members.symbols,
    start=date(2018, 1, 1),
    end=date.today(),
)
```

`members` is a current snapshot, not a point-in-time VN30 membership history. The caller must
carry `members.warnings`/`members.as_of` alongside the bulk result; docs must repeat the
survivorship warning. The bulk client must never claim that the returned symbols were VN30
members throughout the requested history.

## 3. Source adapters and exact normalization

### 3.1 Approved candidate chain after legal gate

| Adapter name | Official route | Exchange | Request | Dataset identity | Status |
|---|---|---|---|---|---|
| `hsx_market_tradingresult_v1` | `/mk/api/v1/market/securities/tradingresult/{code}` | HOSE | GET `fromDate`, `toDate`, `pageIndex`, `pageSize=20` | `hsx.market.securities.tradingresult.v1.0` | Primary candidate |
| `hsx_market_foreign_v1` | `/mk/api/v1/market/securities/foreign/{code}` | HOSE | GET `pageIndex`, `pageSize=100`; local range filter | `hsx.market.securities.foreign.v1.0` | Same-host fallback candidate |
| `hnx_report_ny_v1` | `Report_MD_TradingResult/ListData_Listed` | HNX | POST web report once per session date; `default-date` must match requested date; HTML pagination | `hnx.report.stocketfs.tradingresult.listed.v1` | Technical candidate; disabled pending rights/contract |
| `hnx_report_uc_v1` | `Report_MD_TradingResult/ListData_UPCoM` | UPCOM | POST web report; observed current snapshot regardless of date | `hnx.report.stocketfs.tradingresult.upcom.v1` | Historical source-gap; disabled |

The first two are not separate economic sources and must not be stitched. The second is only a
fallback for a complete requested result when the primary route is unavailable. The HNX rows are
documented for future source-gate work, not enabled by this note. HNX listed history is a
per-session request seam, not a server-side range query; the legal and operational cost of
walking 2018-current dates must be accepted explicitly before it can enter the default chain.
The current HOSE frontend route under `/mk/api/v1` is canonical for this design; the official
Swagger's `/market-api/api/v1.0` server/route form is retained only as a reachability cross-check,
not as a second dataset or a route to stitch.

### 3.2 HOSE parser

* Request `pageSize=20` regardless of a caller's desired page size; the provider's observed cap
  is a contract guard, not a tunable performance knob.
* Parse `data.list` and `data.paging`; reject a successful envelope with a non-list, missing
  paging, non-positive page count, page-index mismatch, or a page count that changes
  unexpectedly.
* Convert `reportDate` epoch seconds to a UTC-aware date. Reject a non-finite/non-integral
  timestamp or a timestamp outside the requested date attribution.
* Canonicalize `symbol` and require exact equality with the requested symbol. The route host and
  adapter name supply `exchange="HOSE"`; a response cannot override it.
* For the primary route, map `mainBuyForeign*`/`mainSellForeign*` and
  `bigLotBuyForeign*`/`bigLotSellForeign*`, sum components, then derive net. Record field
  origins and `derived_total_*`/`derived_net` warnings.
* For the fallback, map its `mainBuyerForeign*`/`mainSellerForeign*` spellings. Prefer its
  published total volume only when it equals component sums; derive values and net because no
  published total value field was observed. Request `pageSize=100`, validate the provider's
  returned paging metadata, paginate newest-first, and filter locally to `[start, end]` after
  pagination. Because the fallback does not echo a symbol, the canonical path code is its
  identity check. Apply a bounded client page ceiling and fail closed if the requested start is
  not reached.
* The official labels establish the field meanings, but the JSON response has no machine-readable
  multiplier. Do not silently scale raw values. The public model's normative `shares`/`VND` units
  may be enabled only after written provider confirmation of the raw scale; until then the
  adapter must reject the result or expose an explicitly unavailable-unit outcome, rather than
  laundering an inference into the contract.
* Reject a conflicting duplicate date, a source arithmetic mismatch, or a row whose date is
  outside the requested range after the provider page has been attributed. Never use another
  endpoint to fill the rejected row.

### 3.3 HNX future adapter boundary

If HNX listed history and legal permission are later established, the adapter may normalize one
official per-session HTML response at a time. The request must set the final
`default-date` token equal to the requested `dd/mm/yyyy` session date, paginate at the observed
maximum of 200 rows, and filter the returned `Security code`/ISIN rows to the requested symbol.
The source labels `Buy volume`, `Buy value (VND)`, `Sell volume`, and `Sell value (VND)`;
gross values may carry `SOURCE_PUBLISHED` origins and `net` is `DERIVED`. The route's volume
label is quantity-like but does not explicitly say “shares”; provider confirmation is required
before setting the public `volume_unit="shares"` without a warning.

UPCoM remains disabled: its endpoint returned an identical current snapshot for dates in 2000,
2018, and 2026, so it cannot support the target historical contract. Both HNX dataset IDs must
remain separate, preserve ISIN when the model is extended, and never infer a historical row
from current foreign room or from index/industry PDFs.

## 4. Coverage and legal contract

### 4.1 Coverage truth table

| Dimension | Required behavior |
|---|---|
| Exchange identity | `HOSE`, `HNX`, or `UPCOM` is explicit; source-bound and validated |
| Target period | Request accepts 2018-01-01–current, but served coverage is source/per-symbol truth |
| Dataset inception | Never inferred; `source_listing_or_inception_unknown` remains visible when not published |
| Per-symbol listing | No promise that every symbol existed in 2018; `served_start` records first returned session |
| Gaps | No fill, interpolation, calendar reconstruction, or cross-source backfill |
| Publication delay | `served_end` and `partial_end_coverage` disclose lag; no “latest” promise without a row |
| Frequency | D1 only; one normalized row per source session date |
| VN30 | Current membership only when explicitly supplied by `index_constituents`; never PIT fiction |

The current official SSC consolidated disclosure text says an exchange must publish foreign-
investor trading during market hours and end-of-day per-security trading/ownership information,
with a 24-hour publication window. This establishes a publication obligation, not that a
particular public API is a licensed historical bulk feed. The source-vetting report records the
exact HNX/HOSE probes, commercial fee schedules, and remaining rights/coverage gaps.

### 4.2 Legal gate

Before implementing or enabling an adapter, obtain/record from the source owner:

1. Permission for an open-source client to make no-auth runtime requests.
2. Whether returned rows may be cached in memory, persisted, replayed in tests, or redistributed
   through a downstream package.
3. Required attribution, trademark/use-of-name constraints, retention limits, and rate limits.
4. Whether the official UI/XHR route is an intended public API or only an internal web seam.
5. For HNX specifically, whether the listed `NY.DLCN 2.4`/InfoFile commercial package or an
   OSS-compatible permission is the only lawful route; for HOSE, whether the fee-schedule
   foreign-statistics product governs the public API response.

Until that evidence is committed, v1 behavior is:

* no bundled provider rows, no checked-in real cassettes, no live calls in CI;
* synthetic fixtures only, with source field shapes but invented values;
* no persistent cache and no request fan-out beyond the conservative limits;
* source attribution and `dataset_id` are designed but not a claim of licence;
* HNX listed and UPCoM adapters remain disabled; HNX is a technical candidate pending written
  rights/contract evidence, while UPCoM still lacks historical coverage.

## 5. Invariants and failover acceptance

The merged implementation must reject a source result unless all applicable checks pass:

1. **Identity:** canonical symbol, source-bound exchange, daily interval, and endpoint dataset
   identity agree.
2. **Units:** volume is whole shares; money is whole VND; no implicit scale factor.
3. **Arithmetic:** gross totals equal the documented components; net equals buy minus sell;
   conflicts invalidate the source result.
4. **Shape:** typed immutable rows, plain dates, strict ascending order, atomic duplicate
   handling, bounded pagination, no malformed envelope.
5. **Coverage:** requested and served bounds are distinct; partial/unknown coverage is visible;
   no fill or stitch.
6. **Provenance:** every numeric field has a source-published/derived/missing origin; result
   source and `SourceAttempt` diagnostics are immutable and redacted.
7. **Preflight:** invalid symbol/date/range/interval/exchange/bulk limits fail before HTTP.
8. **Compatibility:** one valid source result is homogeneous; a later fallback cannot change
   units, exchange, or row identity.
9. **VN30 honesty:** a current `index_constituents("VN30")` input is never labelled historical
   membership and never causes the client to fabricate a point-in-time basket.

## 6. Verification matrix (design only; no tests added yet)

All future adapter tests use committed synthetic JSON/HTML fixtures. No real broker rows or
provider datasets are committed. Live endpoint tests, if needed, stay opt-in and untracked.

| Area | Required offline checks |
|---|---|
| Preflight | D1-only, plain dates, ordering, future bound, symbol/exchange grammar; HTTP call count is zero on failure |
| HOSE envelope | success flag, list/paging shape, page-size cap, page loop, page-count mismatch, HTTP/error mapping |
| Field parser | both HOSE spellings, exact integral numeric coercion, `None` vs zero, negative/fractional/overflow rejection |
| Arithmetic | main+big-lot totals, published-total equality, net buy-minus-sell, conflict rejection |
| Identity | padded symbol canonicalization, mismatch rejection, HOSE source-bound exchange, Unix date conversion |
| Rows | date filtering, ascending order, identical duplicate dedupe, conflicting duplicate rejection, no synthetic dates |
| Coverage | requested/served bounds, listing/inception unknown, partial warnings, empty-range typed failure |
| Failover | primary reject → fallback whole-result success; attempts retained; no cross-source stitching; all-failed diagnostics |
| Bulk | iterable materialization, bare-string/empty/duplicate/limit rejection, stable order, max four workers, every failed symbol represented |
| HNX future seam | separate NY/UC dataset IDs, date-coupled per-session POST, 200-row page cap, UPCoM current-snapshot rejection, no index/industry reconstruction |
| Dataframe | exact columns, origin columns, attrs units/source/coverage, duplicate-index backstop |
| Public/docs | API surface snapshot additive check, docs/API examples, CHANGELOG and skill updates in implementation change |
| Safety scans | repository blacklist scan, secret scan, no real-provider-row scan, synthetic fixture provenance scan |

The implementation must follow Red → Green → Refactor and run the full merged suite before and
after refactoring. This design note intentionally adds no production code and therefore does
not claim any test result beyond the sanitized source probes in the research report.

## 7. Open reviewer decisions

1. **Scope:** PASS the bounded HOSE-first source gate after written terms, or require all-board
   archival/licensed evidence before any implementation. Recommendation: HOSE-first plus HNX
   listed as a disabled technical candidate and UPCoM explicitly unavailable.
2. **Fallback:** accept the same-host `foreign/{code}` endpoint as a bounded whole-result
   fallback, or keep only the date-filtered route until the owner documents it. Recommendation:
   accept it as a source adapter only after the same legal gate; never stitch.
3. **Warning vocabulary:** approve the listed stable prefixes before implementation so docs,
   tests, and the warning-token registry can be updated in one public-API change.
4. **Legal evidence:** identify the required owner/terms contact and the minimum written
   permission needed to move `UNKNOWN`/`FAIL` to `APPROVED`; confirm whether paid HOSE/HNX
   products prohibit OSS runtime retrieval or only redistribution.

## 8. Requested design review

Please review this note and `docs/research/2026-08-22-vn-foreign-flow-source-vetting.md` against
the packet. At handoff, the reviewer should spawn its own parallel sub-agents—one for source/
legal evidence, one for API/model/coverage semantics, and one adversarially for failover/bulk
invariants—and return a design decision with exact issue references. No production code, push,
or issue close is authorized until the reviewer returns **PASS**.
