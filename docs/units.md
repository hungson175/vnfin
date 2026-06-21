# Units — canonical per domain + cross-source verification

Every result object states its unit/currency explicitly so callers never guess.

For the **standard domains** (prices, fundamentals, funds, indices, crypto, macro),
`client()` is the **failover client** (multi-source where a homogeneous backup exists)
and `source()` is the primary adapter only. The unit-homogeneity guard keeps every chain
on one unit so failover can never mix scales/units. **`gold` is the exception** — VN
VND/lượng and world USD/oz are different unit families, so gold has no single `client()`;
it uses `vn()` / `world()` / `source(provider)` plus a world-only
`default_world_gold_client()` (see [api.md](api.md)).

| Domain | Canonical unit | Source stack |
|--------|----------------|--------------|
| Prices (equities) | **VND** | `client()` = 4-broker failover (SSI → VNDirect → VPS → Pinetree; KIS excluded, MIXED). `source()` = SSI primary. Verified identical across broker sources (72,300 VND for FPT). SSI/VNDirect/VPS feed ×1000; Pinetree/KIS ×1. |
| Indices | **points** (level); **shares** (volume) | `client()` = multi-source failover (VPS → SSI → VNDirect); `source()` = VPS primary. NOT VND — index sources use scale 1.0; do not route through the ×1000 price sources. The bar `volume` is constituent share volume passed through — a directional proxy only (opaque definition, cross-source-variable; not exact for liquidity/drawdown). See [sources/indices-constituents.md](sources/indices-constituents.md). |
| Fundamentals | **raw VND** for statement money; **per-share VND** for EPS/BV; dimensionless for other ratios | `client()` = **VNDirect (primary) → CafeF (backup)**; `source()` = VNDirect primary. Statement money (income/balance/cashflow) is raw VND. Ratio line items use `LineItem.value_unit`: `"vnd_per_share"` for EPS/BV (money per share), `"ratio"` for dimensionless metrics (PE, ROE, ROA, etc.). Income/balance/ratios have redundancy; **cashflow is VNDirect-only** (CafeF summary handlers don't serve it). |
| Funds (NAV) | **VND / fund unit** | **Single-source (Fmarket)** — no clean no-auth backup exists; accepted single-source for v0.1. `client() == source()`. |
| Gold — world | **USD / troy oz** | `default_world_gold_client()` = **currency-api** (default, daily history); **Stooq is opt-in** only (server-IP anti-bot challenge — not a reliable default). gold-api is spot-only (not in the history chain). |
| Gold — VN domestic | **VND/lượng** | **TWO SEPARATE spot adapters — BTMC and PNJ** (no runtime failover client). Pick one via `vn("btmc")` / `vn("pnj")` (or `source(...)`). Both normalize to `VND/luong` (1 lượng = 10 chỉ = 37.5 g); silver excluded; weight parsed from product name. A live cross-source **parity test** checks the two dealers agree. |
| Crypto | **USD** | `client()` = **Binance (primary) → Coinbase (backup)** failover; `source()` = Binance primary. USD / USD-stablecoin pairs only; the result-level USD guard rejects a non-USD (e.g. BTC-quoted) series. |
| Macro | per-indicator `unit` + indicator-specific `currency` (None for non-money) | `client()` = **No-key: World Bank (primary) → IMF DataMapper → DBnomics**; `source()` = World Bank primary. Optional **FRED BYOK** (excluded from the no-key default chain). Sources are unit pre-filtered to the canonical unit before failover; unit is indicator-specific (%, USD, USD bn, local-cur, index). Level indicators (GDP, CPI) are validated strictly positive; percent/rate indicators may be negative. |

## Cross-source differential testing

`live_tests/test_cross_source_live.py` (opt-in, `VNFIN_LIVE=1`, CI-skipped) requires independent
sources to agree — catching unit/scale mismatches, stale/bad data, with no fixtures.
Tolerances: equity adjusted close <2% (must be unit-identical); magnitude bands elsewhere
(catch order-of-magnitude unit errors without being brittle to market moves).

## RESOLVED — VN domestic gold unit normalization

Found 2026-06-18 by the cross-source test (BTMC median ~26.6M vs PNJ ~14.6M, 83% apart).
**Fixed 2026-06-18** — canonical unit is now **VND/lượng**; BTMC and PNJ agree to ~3% on
live data (BTMC ~150.0M vs PNJ ~145.3M VND/lượng).

Root cause: BTMC `api.btmc.vn` returns ~934 rows **mixing GOLD and SILVER** (`BẠC` = silver)
across many intraday snapshots. Silver rows quote the **total price for the product's stated
weight** (1 lượng, 5 lượng, 1 kg, 500 g); a few partner gold rows are buy-only (`sell == 0`).
The old adapter labeled every row `VND/chi` and never filtered metal/weight, so the median was
dominated by silver total-weight rows.

Fix applied (`vnfin/gold/vn.py`):
1. **Exclude silver** — any product whose accent-stripped name contains `bac` (BẠC) is dropped.
2. **Parse weight** from the product name (lượng / chỉ / kg / gram) and normalize the total to
   the canonical **VND/lượng** (gold rows carry no weight token → treated as per-chỉ = 0.1 lượng).
3. **Skip buy-only rows** (`sell == 0` or `buy == 0`) and keep the latest snapshot per product.
4. **PNJ** converts thousand-VND/chỉ → VND/lượng (×1000 ×10) and emits `unit="VND/luong"`.
5. The cross-source parity test (`live_tests/test_cross_source_live.py::test_vn_gold_dealers_same_magnitude`)
   is **no longer xfail**; it asserts both dealers are `VND/luong`, inside the per-lượng band,
   and within a <0.5 relative spread.
