# vnfin-oss roadmap

Ordered by Boss (2026-06-18), optimized for long-term investing. Domains are largely
independent → researched/built in parallel via workflows (and worktrees when adapters
are written concurrently). Each step follows the rhythm: **research → design → discuss
with reviewer → TDD implement → document → commit.**

### v0.1.0 — shipped (2026-06-18)

| Step | Domain | Why | Status |
|------|--------|-----|--------|
| 1 | **Daily prices** (OHLCV) | technical analysis base | ✅ done (broker adapters, failover client) |
| 2 | **Fundamental reports** (income / balance / cashflow / ratios) | core of long-term valuation | ✅ done (VNDirect → CafeF) |
| 3 | **Funds & indices** (NAV, holdings; index values + constituents) | **most important for long-term investing** | ✅ done |
| 4 | **Gold** (VN domestic + world XAU) | macro hedge / allocation | ✅ done |
| 5 | **Macro indicators** (cross-country: GDP, CPI, rates, FX, M2, trade) | macroeconomic context | ✅ done (World Bank → IMF → DBnomics, no-key) |
| 6 | **Major crypto** (BTC, ETH, … — USD) | cross-asset allocation | ✅ done (Binance → Coinbase) |

### v0.2.0 — in progress (2026-06-18)

| Item | Why | Status |
|------|-----|--------|
| **API stability gate** (public-surface snapshot + SemVer/deprecation policy) | protect the just-published API from accidental breaking changes | ✅ done |
| **Upstream health monitoring** (opt-in `vnfin/_health.py` + `scripts/healthcheck.py`) | early-warning on upstream schema/unit drift or outage | ✅ done |
| **FX** (daily/current VND rates, no-key) | convert world gold/crypto → VND; daily FX for analysis | ✅ implemented (open.er-api → Vietcombank) |
| **Corporate actions / dividends** | total return for long-term investors | 📝 design only (deferred to v0.3.1 — after security master) |

### v0.3.0+ — planned

| Item | Why |
|------|-----|
| **Security master / company profile / shares outstanding** | per-share metrics, market cap, total-return audits (must precede dividends) |
| **Dividends / corporate actions** | implement against VNDirect finfo `/v4/events` (designed) |
| **VN interest rates / bond yields**, **ETF iNAV/holdings**, **intraday prices** | depth for macro + passive investing |
| Historical FX (BYOK) | paid ExchangeRate-API / ECB for non-VND |

## Principles

- Clean-room throughout; VNStock fully blacklisted.
- Prefer exchange/broker-native and official/government sources; record provenance, auth, rate limits, terms, redistribution for every source.
- Daily/EOD granularity guaranteed; finer granularity best-effort and capability-gated.
- Runtime fetch only; no bundled data or real-data fixtures committed.
- Reviewer reviews each step's code (read code, run tests, coverage) and does a whole-architecture review every 2–3 steps.

## Source notes

- **Macro (Step 5):** Boss directs us to use **FRED** (`api.stlouisfed.org`), key in `~/dev/.env`. ⚠️ As of 2026-06-18 no FRED-named var is present in `~/dev/.env` (vars checked by name) — resolve the key before Step 5 macro implementation. Meanwhile the **World Bank API** (`api.worldbank.org/v2`, no key) is the no-key cross-country fallback.

## Parallelization

Research/probe (read-only) fans out now across Steps 3–5 simultaneously (independent).
Implementation is sequenced per domain through design + reviewer sign-off; independent
adapter builds may use git worktrees to avoid write conflicts.
