# Design: per-domain redundancy via the generic FailoverClient

**Date:** 2026-06-18  **Status:** PROPOSAL for reviewer (pre-implementation).
**Builds on:** generic `vnfin.failover.FailoverClient` + unit-homogeneity guard (P1.3),
and `docs/design/macro-no-key-byok.md`.

## Goal

Boss's redundancy requirement: no domain should depend on a single source. Use the generic
`FailoverClient` (sequential, ≤3 attempts, **unit-homogeneity guard**) to chain a primary +
backup(s) per domain. All backups are clean-room, no-auth-first; live cross-source tests in
`live_tests/` assert agreement.

## Current coverage vs. plan

| Domain | Today | Add (backup) | Unit guard |
|--------|-------|--------------|-----------|
| Prices | 5 sources, failover ✅ | — | VND |
| Indices | multi-source failover ✅ | — | points |
| **Fundamentals** | VNDirect only | **CafeF** (no-auth AJAX, researched) | raw VND |
| **Crypto** | Binance only | **Coinbase** (`api.exchange.coinbase.com`), opt. Kraken | USD |
| **Gold (world)** | currency-api | **stooq** (`xauusd` CSV) | USD/oz |
| **Gold (VN)** | BTMC + PNJ (2 dealers) | opt. SJC | VND/lượng |
| **Macro** | World Bank only | **IMF DataMapper → DBnomics** (no-key) + BYOK (FRED/BEA/BLS-v2) | per-indicator |
| **Funds** | Fmarket only | *no clean no-auth backup exists* → document as accepted single-source (BETA flag) | VND/unit |

## Wiring

Each domain gets `default_<domain>_sources()` + a `FailoverClient` (or domain wrapper) where a
homogeneous backup exists. The unit-homogeneity guard prevents mixing scales/units (already
proven for prices=VND, indices=points). Cross-domain models are never funneled through one
client (crypto USD vs prices VND stay separate clients).

## TDD per backup

Each new backup adapter ships with synthetic-fixture unit tests (failover-safe errors, unit
correctness) and a `live_tests/` cross-source agreement check (primary vs backup within
tolerance). No real rows committed.

## Open question for reviewer

- Funds: accept single-source (Fmarket) for v0.1 with a BETA flag, or invest in scraping
  individual fund-manager NAV pages (fragile)? Proposed: accept single-source now.
- Order of macro chain + which BYOK sources to wire in v0.1 (proposed: no-key trio now; FRED
  BYOK stub wired, BEA/BLS-v2 deferred).
