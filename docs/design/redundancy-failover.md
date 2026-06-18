# Design: per-domain redundancy via the generic FailoverClient

**Date:** 2026-06-18  **Status:** IMPLEMENTED (was a proposal; shipped 2026-06-18).
**Builds on:** generic `vnfin.failover.FailoverClient` + unit-homogeneity guard (P1.3),
and `docs/design/macro-no-key-byok.md`.

## Goal

Boss's redundancy requirement: no domain should depend on a single source where a
clean-room, no-auth backup exists. The generic `FailoverClient` (sequential, ≤3
attempts, **unit-homogeneity guard**) chains a primary + backup(s) per domain. All
backups are clean-room, no-auth-first; live cross-source tests in `live_tests/`
assert agreement (require `VNFIN_LIVE=1`).

## Implemented coverage

| Domain | `source()` (primary) | `client()` (failover chain) | Unit guard |
|--------|----------------------|-----------------------------|-----------|
| Prices | one broker | 5-broker failover ✅ | VND |
| Indices | one source | multi-source failover ✅ | points |
| **Fundamentals** | VNDirect | **VNDirect → CafeF** ✅ (income/balance/ratios; cashflow is VNDirect-only — CafeF summary handlers don't serve it) | raw VND |
| **Crypto** | Binance | **Binance → Coinbase** ✅ (USD / USD-stablecoin only; result-level USD guard) | USD |
| **Gold (world)** | currency-api | **currency-api** ✅; **Stooq opt-in only** (server-IP anti-bot challenge — not a reliable default) | USD/oz |
| **Gold (VN)** | BTMC | **BTMC + PNJ** (2 dealers, cross-source parity) ✅ | VND/lượng |
| **Macro** | World Bank | **World Bank → IMF DataMapper → DBnomics** (no-key) ✅ + **FRED BYOK** (excluded from no-key default chain) | per-indicator |
| **Funds** | Fmarket | **single-source** (no clean no-auth backup exists — accepted single-source for v0.1; `client() == source()`) | VND/unit |

`client()` returns the failover chain; `source()` returns just the primary adapter.
They are **not** aliases except for the two accepted single-source cases (Funds, and
world-gold history when Stooq is not opted in).

## Wiring

Each domain exposes `default_<domain>_sources()` + a `FailoverClient` (or domain
wrapper). The unit-homogeneity guard prevents mixing scales/units (proven for
prices=VND, indices=points, and now fundamentals=VND, crypto=USD, gold=USD/oz,
macro=per-indicator). Cross-domain models are never funneled through one client
(crypto USD vs prices VND stay separate clients).

Macro is special: the `FailoverClient` is reused **only after** the macro layer
filters sources by a canonical `MacroIndicatorSpec` registry (unit pre-filter) so the
chain serves the SAME canonical indicator across providers — never just "same unit".

## TDD per backup

Each backup adapter ships with synthetic-fixture unit tests (failover-safe errors,
unit correctness) and a `live_tests/` cross-source agreement check (primary vs backup
within tolerance). No real provider rows are committed.

## Resolved open questions

- **Funds:** accepted single-source (Fmarket) for v0.1 (BETA). No fragile per-manager
  NAV scraping.
- **Macro chain order:** no-key trio now (World Bank → IMF DataMapper → DBnomics);
  FRED wired as BYOK opt-in (official API only, never `fredgraph.csv`); BEA/BLS-v2
  deferred.
- **Stooq (world gold):** removed from the default chain (server-IP anti-bot
  challenge); kept as an explicit opt-in backup. See
  `docs/sources/gold-adapters.md`.
