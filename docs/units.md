# Units — canonical per domain + cross-source verification

Every result object states its unit/currency explicitly so callers never guess.

Each domain's `client()` is the **failover client** (multi-source where a homogeneous
backup exists); `source()` is the primary adapter only. The unit-homogeneity guard
keeps every chain on one unit so failover can never mix scales/units.

| Domain | Canonical unit | Source stack (`client()`) |
|--------|----------------|---------------------------|
| Prices (equities) | **VND** | 5-broker failover. Verified identical across all 5 broker sources (72,300 VND for FPT). SSI/VNDirect/VPS feed ×1000; Pinetree/KIS ×1. |
| Indices | **points** | Multi-source failover. NOT VND — index sources use scale 1.0; do not route through the ×1000 price sources. |
| Fundamentals | **raw VND** | **VNDirect (primary) → CafeF (backup).** Unscaled (e.g. total assets in trillions of VND as integer VND). Income/balance/ratios have true redundancy; **cashflow is VNDirect-only** (CafeF summary handlers don't serve it). |
| Funds (NAV) | **VND / fund unit** | **Single-source (Fmarket)** — no clean no-auth backup exists; accepted single-source for v0.1. `client() == source()`. |
| Gold — world | **USD / troy oz** | **currency-api** (default, daily history); **Stooq is opt-in** only (server-IP anti-bot challenge — not a reliable default). gold-api is spot-only (not in the history chain). |
| Gold — VN domestic | **VND/lượng** | **BTMC + PNJ** (2 dealers). Canonical VN gold quote; both normalize to `VND/luong` (1 lượng = 10 chỉ = 37.5 g); silver excluded; weight parsed from product name. Verified by cross-source live test. |
| Crypto | **USD** | **Binance (primary) → Coinbase (backup)** failover. USD / USD-stablecoin pairs only; the result-level USD guard rejects a non-USD (e.g. BTC-quoted) series. |
| Macro | per-indicator `unit` + indicator-specific `currency` (None for non-money) | **No-key: World Bank (primary) → IMF DataMapper → DBnomics**, plus optional **FRED BYOK** (excluded from the no-key default chain). Sources are unit pre-filtered to the canonical unit before failover; unit is indicator-specific (%, USD, USD bn, local-cur, index). |

## Cross-source differential testing

`tests/test_cross_source_live.py` (opt-in, `VNFIN_LIVE=1`, CI-skipped) requires independent
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
5. The cross-source parity test (`tests/test_cross_source_live.py::test_vn_gold_dealers_same_magnitude`)
   is **no longer xfail**; it asserts both dealers are `VND/luong`, inside the per-lượng band,
   and within a <0.5 relative spread.
