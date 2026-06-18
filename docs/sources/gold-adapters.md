# Gold adapters — provenance & vetting notes

Clean-room: every endpoint, unit and shape below was learned **only** from the
provider's own server and the project research docs
(`docs/research/2026-06-18-gold-vietnam-domestic.md`,
`docs/research/2026-06-18-gold-world.md`). No vnstock / VNStock / derivative was read,
cited, or copied.

> **Redistribution:** none of these endpoints publish a redistribution grant. Treat as
> personal/internal research, **runtime-fetch only** — do not bundle/redistribute data.
> Attribute the provider; poll modestly.

## Port & models (`vnfin/gold/`)

- `GoldSource` (port) — `get_quotes()` (spot, all), optional `get_history(start, end)`;
  capability flags `provides_spot` / `provides_history`. Injectable
  `http_get(url, params, headers) -> text` (default IPv4-forced httpx + browser UA + 25s).
- `GoldQuote(time, product, buy, sell, unit, currency, source, fetched_at_utc, karat, region)`
  — spot buy/sell. `buy == sell` for single-tick world spot. Has `.spread` / `.mid`.
- `GoldBar(date, price)` + `GoldHistory(product, unit, currency, source, bars, ...)`
  — daily EOD series; `.to_dataframe()` indexed by date.

## VN domestic (spot-only, VND per *chỉ*)

| Adapter | Host | Auth | Units | History |
|---|---|---|---|---|
| `BTMCGoldSource` | `api.btmc.vn` | fixed public widget key (query `key=`) | VND/chỉ, full-digit strings | spot only (feed has same-day intraday snapshots, no multi-day EOD) |
| `PNJGoldSource` | `edge-api.pnj.io` | none | **thousand** VND/chỉ → ×1000 | spot only (no timestamp in body) |

Edge cases handled: BTMC `DD/MM/YYYY HH:MM` timestamp → Asia/Ho_Chi_Minh tz; indexed
keys (`@n_N`, `@pb_N`, `@ps_N`, `@d_N`). PNJ `RAW_*` "raw gold purchase" rows have a
**blank sell** (PNJ buys but doesn't sell that grade) — those rows are skipped, not
failed. Cross-checked live: BTMC & PNJ both quote SJC 14,880,000 buy / 15,130,000 sell.

## World (XAU/USD, USD per troy ounce)

| Adapter | Host | Auth | History | Default chain? |
|---|---|---|---|---|
| `GoldApiSource` | `api.gold-api.com/price/{XAU,XAG}` | none | **spot only** (single tick; `?date=` unsupported) | no (spot only) |
| `CurrencyApiGoldSource` | `cdn.jsdelivr.net/.../@fawazahmed0/currency-api` | none | **daily EOD history** (~2024-03 → today) + latest spot | **yes (only default source)** |
| `StooqGoldSource` | `stooq.com/q/d/l/?s=xauusd&i=d` | none | daily EOD CSV (`Date,Open,High,Low,Close,Volume`) | **no — opt-in only** |

`CurrencyApiGoldSource` reads the `usd` base doc and inverts `usd.xau`
(`USD/oz = 1 / usd.xau`). History fans out one date-pinned doc per day in `[start, end]`;
missing days (weekends/holidays/pre-coverage) 404 and are skipped; all-missing →
`EmptyData`. Range capped at ~1100 days to bound request fan-out.

### Default world-gold chain (`default_world_gold_sources` / `default_world_gold_client`)

The **default** daily-history chain contains only reliable, no-key sources that
serve real data from server infrastructure. As of now that is **just
`CurrencyApiGoldSource`** (CDN-hosted, no key, deterministic per-day documents).

### `StooqGoldSource` — opt-in backup, anti-bot caveat (B12)

Stooq publishes a daily XAU/USD OHLCV CSV at `stooq.com/q/d/l/?s=xauusd&i=d` and the
adapter parses the `Close` column as USD/oz, so it *would* be a same-unit backup. It
is **NOT in the default chain** for two reasons:

- **Anti-bot challenge from server IPs.** From server/datacenter IPs Stooq commonly
  returns a JavaScript proof-of-work challenge page (HTML) instead of CSV. The
  adapter detects that body and raises `SourceUnavailable` (so a failover chain moves
  on rather than choking), but it means Stooq is effectively unreachable from many
  hosts — too unreliable to be a *default* backup.
- **No published terms / undocumented redistribution posture.** Treat any Stooq data
  as personal/internal runtime-fetch only; poll modestly; do not bundle/redistribute.

Stooq stays exported (`from vnfin.gold import StooqGoldSource`) as an **explicit
opt-in** source for callers whose network can reach it. To use it as a backup, append
it to the default chain yourself:

```python
from vnfin.gold import (
    default_world_gold_sources, StooqGoldSource, default_world_gold_client,
)

sources = default_world_gold_sources() + [StooqGoldSource()]
client = default_world_gold_client(sources=sources)   # USD/oz, currency-api → stooq
```

Both emit `USD/oz`, so the opt-in chain still satisfies the unit-homogeneity guard.

### Range-coverage acceptance for world-gold history (B11)

`FailoverGoldClient` does **not** accept an arbitrarily-incomplete primary result and
skip the backup. Because `CurrencyApiGoldSource` fans out one request per calendar day
and silently skips days it cannot fetch, a one-day partial result is technically
"non-empty". Acceptance is therefore measured against the **expected trading days**
(Mon-Fri weekdays — XAU/USD has no weekend session) in the requested `[start, end]`:

- coverage `< min_coverage` (default 50%) → **rejected**; the client falls through to
  the next source (backup), so a materially-incomplete primary never pre-empts a
  complete backup;
- `min_coverage ≤` coverage `< warn_coverage` (default 90%) → **accepted with a soft
  `partial_coverage` warning** on `GoldHistory.warnings`;
- coverage `≥ warn_coverage` → accepted silently.

When the requested window contains no weekdays at all (e.g. a single Saturday) any
non-empty result is accepted (there is nothing to be incomplete against).

## Failover safety

All adapters wrap transport errors as `SourceUnavailable`, non-JSON / malformed
scalars / non-finite / negative prices / divide-by-zero (`usd.xau == 0`) as
`InvalidData`, and no-data / no-match as `EmptyData` — all `vnfin.exceptions` subclasses,
so a future failover layer can fail over cleanly.
