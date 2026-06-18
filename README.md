# vnfin

**Clean-room, open-source Python library for Vietnam financial-market data.**

`vnfin` gives long-term investors, macro analysts, and developers a stable, typed, and
**no-key-out-of-the-box** API for Vietnamese stocks, funds, indices, gold, macro indicators,
and major crypto — with multi-source **failover** so a single provider outage doesn't break you.

- ✅ **No API key required** for the default path of every domain. Optional **bring-your-own-key (BYOK)** upgrades are read from env vars and are *never* bundled.
- ✅ **Typed contracts** (frozen dataclasses) with explicit **units/currency** on every result — no guessing VND vs thousand-VND vs points.
- ✅ **Failover redundancy** — each domain chains a primary + backup source through one generic client with a **unit-homogeneity guard** (it cannot silently mix scales).
- ✅ **Clean-room** — built only from providers' own endpoints and public protocols; runtime-fetch only, no bundled market data.
- ✅ **618+ offline tests**, synthetic fixtures only; real cross-source checks live under `live_tests/`.

> ⚠️ **Data use:** `vnfin` is an API *client*. Data fetched is for personal/internal research.
> Redistributing raw provider data may require the provider's/exchange's license — see each
> source's terms and `docs/units.md` / `docs/sources/`.

## Install

```bash
pip install -e .            # core (httpx only)
pip install -e ".[pandas]"  # + pandas, enables .to_dataframe()
```

Requires Python ≥ 3.10.

## Quickstart

```python
from datetime import date
import vnfin

# --- Daily prices (technical) — 5 broker sources, auto-failover, prices in VND ---
client = vnfin.default_client()                       # SSI → VNDirect → VPS → Pinetree
h = client.get_daily("FPT", date(2026, 1, 1), date(2026, 6, 17))
print(h.source, len(h), h.value_unit)                 # e.g. "ssi 110 VND"
df = h.to_dataframe()                                  # pandas, metadata in df.attrs

# --- Fundamentals (long-term valuation) — VNDirect → CafeF failover ---
reports = vnfin.fundamentals.get_financials("FPT", "income", "annual")

# --- Funds & indices ---
funds = vnfin.funds.source().list_funds(asset_type="STOCK")
vni = vnfin.indices.index_history("VNINDEX", date(2026, 1, 1), date(2026, 6, 17))  # points

# --- Macro (no key; covers Vietnam) — World Bank → IMF DataMapper → DBnomics ---
cpi = vnfin.macro.source().get_indicator("VNM", "FP.CPI.TOTL", 2015, 2024)

# --- Gold & crypto ---
gold = vnfin.gold.world().get_history(date(2026, 1, 1), date(2026, 6, 17))          # USD/oz
btc = vnfin.crypto.client().get_klines("BTCUSDT", vnfin.Interval.D1,
                                       date(2026, 1, 1), date(2026, 6, 17))          # USD
```

## Domains & sources

| Domain | Default (no-key) chain | Unit | Optional BYOK |
|--------|------------------------|------|---------------|
| Prices | SSI → VNDirect → VPS → Pinetree (KIS excluded: MIXED adj.) | VND | — |
| Indices | broker index feeds | points | — |
| Fundamentals | VNDirect `api-finfo` → CafeF | raw VND | — |
| Funds | Fmarket | VND/unit | — |
| Gold (VN) | BTMC, PNJ | VND/lượng | — |
| Gold (world) | currency-api (Stooq opt-in) | USD/oz | — |
| Crypto | Binance → Coinbase | USD | — |
| Macro | World Bank → IMF DataMapper → DBnomics | per-indicator | FRED / BEA / BLS-v2 |

### Bring-your-own-key (optional)

The default path needs no key. To enable keyed macro sources, set your **own** free key in the
environment — `vnfin` never ships or shares a key:

```bash
export FRED_API_KEY=...   # FRED official API (never scraped)
export BEA_API_KEY=...    # US GDP (NIPA)
export BLS_API_KEY=...    # BLS v2 (higher limits)
```

Missing key ⇒ that source is simply skipped; the no-key chain still serves you.

## Design

Ports-and-adapters: a typed result per domain, one adapter per source, and a generic
`FailoverClient` (sequential, ≤3 attempts, per-source diagnostics, unit-homogeneity guard).
See `docs/api.md` (facade), `docs/units.md` (canonical units), `docs/design/` and `docs/sources/`.

## Testing

```bash
pip install -e ".[dev]"
pytest                                            # offline, deterministic — 0 skipped / 0 xfail
pytest --cov=vnfin --cov-fail-under=85            # CI release gate (currently ~94%)
VNFIN_LIVE=1 pytest live_tests/                   # real cross-source/network checks — 0 skipped, opt-in
python scripts/diagnostics_live.py                # manual probes for host-flaky upstreams (e.g. IMF)
```

**CI release gate.** `.github/workflows/ci.yml` runs on every push and pull request
(Python 3.10/3.11/3.12): it `pip install -e .[dev]`, then runs the **offline** suite with
`pytest --cov=vnfin --cov-fail-under=85` — the job fails if line coverage drops below
**85%** (the repo currently sits ~94%, so the gate guards against regressions). CI never
sets `VNFIN_LIVE`, so the live network suite is never collected there.

`live_tests/` are real network checks (never mocked) and are kept out of the default suite;
running them without `VNFIN_LIVE=1` fails clearly rather than skipping, and with it they pass
with **0 skipped** (no conditional `pytest.skip`). Probes for upstreams that block this
server's datacenter IP (e.g. IMF DataMapper returns HTTP 403 here) live in
`scripts/diagnostics_live.py` — a manually-invoked script that is *not* collected by pytest, so
the live suite stays reliably green here while those checks remain available on a reachable host.

## Clean-room & license

Implemented clean-room from providers' own servers and public standards. Code is licensed
**Apache-2.0** (see `LICENSE`). Fetched data remains subject to each provider's terms
(e.g. World Bank CC BY 4.0 — attribute "Source: World Bank").
