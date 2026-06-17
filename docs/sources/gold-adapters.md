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

| Adapter | Host | Auth | History |
|---|---|---|---|
| `GoldApiSource` | `api.gold-api.com/price/{XAU,XAG}` | none | **spot only** (single tick; `?date=` unsupported) |
| `CurrencyApiGoldSource` | `cdn.jsdelivr.net/.../@fawazahmed0/currency-api` | none | **daily EOD history** (~2024-03 → today) + latest spot |

`CurrencyApiGoldSource` reads the `usd` base doc and inverts `usd.xau`
(`USD/oz = 1 / usd.xau`). History fans out one date-pinned doc per day in `[start, end]`;
missing days (weekends/holidays/pre-coverage) 404 and are skipped; all-missing →
`EmptyData`. Range capped at ~1100 days to bound request fan-out.

## Failover safety

All adapters wrap transport errors as `SourceUnavailable`, non-JSON / malformed
scalars / non-finite / negative prices / divide-by-zero (`usd.xau == 0`) as
`InvalidData`, and no-data / no-match as `EmptyData` — all `vnfin.exceptions` subclasses,
so a future failover layer can fail over cleanly.
