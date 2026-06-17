# Units — canonical per domain + cross-source verification

Every result object states its unit/currency explicitly so callers never guess.

| Domain | Canonical unit | Notes |
|--------|----------------|-------|
| Prices (equities) | **VND** | Verified identical across all 5 broker sources (72,300 VND for FPT). SSI/VNDirect/VPS feed ×1000; Pinetree/KIS ×1. |
| Indices | **points** | NOT VND. Index sources use scale 1.0; do not route through the ×1000 price sources. |
| Fundamentals | **raw VND** | Unscaled (e.g. total assets in trillions of VND as integer VND). |
| Funds (NAV) | **VND / fund unit** | Fmarket. |
| Gold — world | **USD / troy oz** | currency-api + gold-api. |
| Gold — VN domestic | **VND** (intended `VND/chi`) | ⚠️ **OPEN BUG — see below.** |
| Crypto | **USD** | Binance USDT pairs. |
| Macro | per-indicator `unit` + `currency` | World Bank; unit is indicator-specific (%, USD, local-cur, index). |

## Cross-source differential testing

`tests/test_cross_source_live.py` (opt-in, `VNFIN_LIVE=1`, CI-skipped) requires independent
sources to agree — catching unit/scale mismatches, stale/bad data, with no fixtures.
Tolerances: equity adjusted close <2% (must be unit-identical); magnitude bands elsewhere
(catch order-of-magnitude unit errors without being brittle to market moves).

## OPEN BUG — VN domestic gold unit normalization

Found 2026-06-18 by the cross-source test (BTMC median 26.6M vs PNJ 14.6M "VND/chi", 83% apart).

Root cause: BTMC `api.btmc.vn` returns **934 rows mixing GOLD and SILVER** (`BẠC` = silver),
each quoting the **total price for the product's stated weight** (1 lượng, 5 lượng, 1 kg, 500 g) —
**not** a per-*chỉ* price. The adapter labels every row `VND/chi`, which is wrong for any row
whose weight ≠ 1 chỉ and for all silver rows.

Fix plan (TDD + reviewer):
1. Filter to GOLD products only (exclude `BẠC`/silver).
2. Parse the product weight from the name (lượng/chỉ/kg/gram) and normalize to ONE canonical
   unit — recommend **VND/lượng** (the standard VN gold quote) or consistent VND/chỉ.
3. Re-verify PNJ uses the same normalization.
4. Re-enable the strict VN-gold cross-source parity assertion (currently `xfail`).
