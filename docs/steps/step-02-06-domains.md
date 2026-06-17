# Steps 2–6 — six data domains (parallel TDD build)

**Date:** 2026-06-18  **Commits:** `c5abe12` (fundamentals), `262be85` (funds/indices/gold/crypto/macro)
**Status:** all 6 domains unit-green; **264 tests pass, 2 skipped, 95% coverage**. Awaiting reviewer (parallel) + architecture review.

## What shipped (public API per domain)

- **`vnfin.fundamentals`** — `get_financials(symbol, statement, period, *, is_bank=False)` → `FinancialReport`s (VNDirect `api-finfo` `/v4/financial_statements` + `/v4/ratios`; long-row pivot; bank vs corporate modelType; raw VND).
- **`vnfin.funds`** — `FmarketFundSource.list_funds() / nav_history(id) / holdings(id)` (Fmarket, no-auth; NAV in VND/unit, history to 2014).
- **`vnfin.indices`** — `index_history(symbol, start, end)` → `PriceHistory` + `index_constituents(index)`. Uses **own POINT-scaled** index sources (see signal #2).
- **`vnfin.gold`** — VN domestic spot (`BTMCGoldSource`, `PNJGoldSource`) + world XAU history (`CurrencyApiGoldSource`); `provides_history` flag distinguishes spot vs series.
- **`vnfin.crypto`** — `BinanceCryptoSource.get_klines(symbol, interval, start, end)` → `CryptoHistory` (USD).
- **`vnfin.macro`** — `WorldBankMacroSource.get_indicator(iso3, code, ...)` → `IndicatorSeries` (no key). FRED adapter stubbed pending `FRED_API_KEY`.

## Architecture signals for the review (refactor-under-green)

1. **Duplicated HTTP infra.** Every domain re-implemented an injectable `http_get` + IPv4 httpx transport + browser UA + error wrapping (`SourceUnavailable`/`InvalidData`/`EmptyData`). → Extract a shared `HttpDataSource`/transport base; each adapter keeps only its endpoint/parse logic.
2. **Scaling is per-(source, instrument), not per-source.** Index values are **points**, but the broker UDF price sources hardcode `PRICE_SCALE=1000` (thousands-of-VND→VND); using the price client for an index returned `1,290,670` instead of `1290.67`. The indices lane correctly built separate POINT-scaled sources. → Generalize scaling to be instrument-aware, or keep the split (document it).
3. **Near-identical result containers.** `PriceHistory`, `CryptoHistory`, `NavHistory`, `IndicatorSeries`, `GoldHistory` all carry source/fetched_at/`to_dataframe()`/len/iter. → A shared `TimeSeries` base or mixin would de-duplicate.
4. **Failover scope.** Only prices have `FailoverPriceClient`. Others are largely single-source (fundamentals=VNDirect, funds=Fmarket, macro=WorldBank, crypto=Binance). Boss wants redundancy → decide which domains add a backup (fundamentals→CafeF, gold-world→stooq, crypto→Coinbase) and whether a **generic** failover client should serve all domains.
5. **Facade.** Users import from subpackages today. → Decide a unified top-level `vnfin` facade.

## Next

Architecture review (with reviewer) → refactor-under-green to unify #1/#3, resolve #2/#4/#5. Then add per-domain failover backups where Boss's redundancy goal needs them.
