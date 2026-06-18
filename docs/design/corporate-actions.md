# Corporate actions / dividends — source vetting & design (DESIGN ONLY)

**Status:** design only. **No adapter code ships in v0.2.** Per the v0.2 plan and reviewer
ordering, implementation is deferred to **v0.3.1+**, *after* the security master / company
profile (v0.3) — per-share ratios, total-return audits, and corporate-action validation need a
security master first. This document captures the vetted source + design so implementation can
start cleanly later.
Source research: [`docs/research/2026-06-18-corporate-actions-dividends-sources.md`](../research/2026-06-18-corporate-actions-dividends-sources.md).
**Clean-room:** VNStock/vnstock fully excluded; the single viable source was found by direct
probing of the provider's own endpoint.

## Vetted source (single)

| Source | Endpoint | Auth | Reachable (non-VN IP) | Clean-room risk | Redistribution |
|--------|----------|------|----------------------|-----------------|----------------|
| VNDirect finfo `/v4/events` | `GET https://api-finfo.vndirect.com.vn/v4/events?q=code:FPT~type:DIVIDEND&size=50&sort=effectiveDate:desc&q=...locale:EN_GB` | none | probed from a VN IP — **non-VN/overseas reachability must be verified before implementation** | **LOW** | **MEDIUM** — no published data license; runtime-fetch only, no bundling (same posture as all domains) |

This is the **same host we already use for fundamentals** (`api-finfo.vndirect.com.vn`), so the
adapter reuses the existing `HttpDataSource` transport. **Single-source** (an accepted pattern,
like `funds`/Fmarket) — all other providers failed vetting (SSI FastConnect has no dividend
endpoints; CafeF no AJAX; VPS/Pinetree/DNSE 404; HOSE `api.hsx.vn` blocks non-VN IPs).

## Proposed public model

```python
class CorporateActionType(enum.Enum):
    CASH_DIVIDEND = "cash_dividend"   # VNDirect DIVIDEND
    STOCK_DIVIDEND = "stock_dividend" # VNDirect STOCKDIV
    BONUS_SHARE = "bonus_share"       # VNDirect KINDDIV
    # (LISTED/MEETING/rights handled later; v0.3.1 starts with the three dividend types)

@dataclass(frozen=True)
class CorporateAction:
    symbol: str
    type: CorporateActionType
    ex_date: date | None          # VNDirect effectiveDate
    record_date: date | None      # VNDirect expiredDate
    payment_date: date | None     # VNDirect actualDate (None for future events)
    cash_per_share_vnd: float | None   # DIVIDEND: VND/share absolute
    ratio_pct_of_par: float | None     # cash: % of 10,000 VND par
    shares_per_100: float | None       # STOCKDIV/KINDDIV: new shares per 100 held
    currency: str = "VND"
    confirmed: bool = True        # group == "investorRight" (vs scheduled "schedEvent")
    fiscal_year: int | None = None
    note: str = ""
    source: str = "vndirect"

@dataclass(frozen=True)
class CorporateActionHistory:   # TimeSeriesResult-style, value_unit = "VND" (cash)
    symbol: str
    actions: tuple[CorporateAction, ...]
    source: str
    fetched_at_utc: datetime
```

## Field mapping & units (from research)

- `effectiveDate` → **ex_date**; `expiredDate` → **record_date**; `actualDate` → **payment_date**.
- `dividend` (cash) → `cash_per_share_vnd` — **VND per share, absolute** (e.g. `1000.0` = 1,000 VND/share).
- `ratio` is **type-dependent**: cash → % of par (par = 10,000 VND; `ratio=10` ⇒ 1,000 VND/share,
  cross-checks `dividend`); STOCKDIV/KINDDIV → new shares per 100 held (`ratio=15` ⇒ 100:15).
  The adapter must route `ratio` to the right field per `type` (a classic units pitfall).
- Filter `locale:EN_GB` to avoid duplicate VN/EN rows; map `group` → `confirmed`.

## Design notes

- Facade: `vnfin.corporate_actions` (or fold into `vnfin.fundamentals`? — **decide at impl**;
  leaning standalone domain for clean units). Verbs: `source()` (single), `get_actions(symbol,
  type=None, since=None)`, plus `get_dividends(symbol)` convenience.
- Query builder: `q=code:{SYM}~type:{TYPE}~locale:EN_GB`, `sort=effectiveDate:desc`, paginate
  `page`/`size` until `currentPage >= totalPages`.
- History depth ~2021→ (provider limit) — document as a coverage/completeness caveat (a
  long-term-investor total-return caveat the reviewer flagged).
- Reuse `HttpDataSource` (IPv4, UA, retry, `redact_secrets`); no key.

## Testing plan (when implemented)

- Synthetic fixtures only (fabricated rows, not a real provider snapshot): cash dividend, stock
  dividend, bonus share, a future event with null `actualDate`, multi-page.
- Unit tests: type mapping, date mapping, ratio routing per type (the units trap), pagination,
  `confirmed` flag, empty/garbage → `SourceError`.
- Opt-in live test: fetch FPT dividends, assert ex-dates parse and cash amounts are positive VND.

## Why deferred (not in v0.2)

Higher semantic/legal/source-risk than FX, single-source, and dependent on a security master for
validation/total-return. Shipping it without a profile/shares-outstanding context would invite
the exact unit/semantic mistakes this library is meant to avoid. Sequenced after v0.3 security
master.
