# Design: no-key-first macro + bring-your-own-key (BYOK)

**Date:** 2026-06-18  **Status:** PROPOSAL for reviewer (pre-implementation of macro redundancy).
**Evidence:** `docs/research/2026-06-18-macro-no-key-byok.md`.

## Principle (applies library-wide)

1. **No-key-first** — every domain defaults to no-auth sources so `pip install` + import just works; no shared-key rate-limiting, ever.
2. **BYOK optional** — keyed sources are opt-in; the *user* supplies their own key via env var / constructor param. The library **never bundles, ships, or commits a key**. Missing key ⇒ that source is skipped, never an error.
3. The generic `FailoverClient` (with the unit-homogeneity guard) chains *no-key primary → optional user-key backup*, so a missing key is invisible to default users.

## Macro module plan (`vnfin/macro/`)

Default no-key chain, per indicator (failover only combines sources that emit the **same indicator unit** — guard enforced):

- **Cross-country incl. Vietnam (annual):** `WorldBankMacroSource` (have it) → `IMFDataMapperSource` (new) → `DBnomicsSource` (new, broad).
- **US high-frequency / rates:** `TreasuryFiscalDataSource` (new, no-key) + `BLSSource` v1 (new, no-key).
- **Germany / euro-area:** `ECBSource` / `EurostatSource` (new, no-key) — optional.

Optional **BYOK** sources (env var; graceful skip when unset):
- `BLSSource` auto-upgrades to v2 when `BLS_API_KEY` is set.
- `BEASource` (`BEA_API_KEY`) for US GDP.
- `FREDSource` via the **official API only** (`FRED_API_KEY`) — replace the current stub; **never** `fredgraph.csv` (ToU forbids scraping).

## Licensing posture (with Apache-2.0 code license)

- Runtime fetch only; **no bundled macro data** or cached-data artifacts in the package.
- **Attribution** emitted on every result + documented: World Bank (CC BY 4.0 — "Source: World Bank"), Eurostat ("Source: Eurostat"), ECB, OECD, IMF, DBnomics (ODbL + upstream).
- IMF/OECD are all-rights-reserved → on-demand API fetch is fine; do not redistribute their data as files.

## Why this fully answers the key-sharing problem

Published users get complete macro coverage (incl. Vietnam) with **zero keys**. FRED/BEA/BLS-v2 are opt-in upgrades keyed to the *user's own* free key — so no one shares a quota and no key is ever in the repo or the wheel.

## For the reviewer

Please review before I implement: (1) source list + default chain order, (2) BYOK env-var contract + graceful-skip, (3) no-FRED-scraping rule, (4) attribution/licensing posture, (5) whether GSO/SBV VN scrapers are in-scope now (proposed: defer as BETA).
