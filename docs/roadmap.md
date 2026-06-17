# vnfin-oss roadmap

Ordered by Boss (2026-06-18), optimized for long-term investing. Domains are largely
independent → researched/built in parallel via workflows (and worktrees when adapters
are written concurrently). Each step follows the rhythm: **research → design → discuss
with reviewer → TDD implement → document → commit.**

| Step | Domain | Why | Status |
|------|--------|-----|--------|
| 1 | **Daily prices** (OHLCV) | technical analysis base | ✅ done (5 broker adapters, failover client) |
| 2 | **Fundamental reports** (income stmt / balance sheet / cash flow / ratios) | core of long-term valuation | 🔬 research in progress |
| 3 | **Funds & indices** (fund list, NAV history, holdings; index values + constituents/weights) | **most important for long-term investing** | ⏳ research queued |
| 4 | **Gold** (VN domestic SJC/PNJ/DOJI + world XAU) | macro hedge / allocation | ⏳ research queued |
| ★ | **Architecture review** (reviewer) | generalize the source/port abstraction now that we span prices + fundamentals + funds + indices + gold | ⏳ after Step 4 |
| 5 | **Macro indicators** (VN, US, China, Japan, Germany, … : GDP, CPI, rates, FX, M2, trade) | macroeconomic context | ⏳ research queued |
| 6 | **Major crypto** (BTC, ETH, top coins — USD + VND where available) | cross-asset allocation | ⏳ research queued |
| 7+ | TBD | — | — |

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
