# vnfin

**Clean-room Python library for Vietnam financial-market data.**

`vnfin` is for investors, analysts, and developers who want one small Python package for
Vietnam-related market data: stocks, fundamentals, mutual funds, indices, gold, FX, macro
indicators, and major crypto. It is **no-key-first**, returns **typed objects with explicit
units**, and uses source failover where a clean same-unit backup exists.

```bash
pip install git+https://github.com/hungson175/vnfin.git
```

> `vnfin` is an API client. Fetched data is for personal/internal research unless you have the
> provider's redistribution license. Code is Apache-2.0; provider data remains provider data.

## Start here

If you are new, read in this order:

1. **This README** — install, first examples, and which docs to read next.
2. **[Getting started](docs/getting-started.md)** — the 10-minute walkthrough: install, first
   stock price, first financial statement, DataFrame output, errors.
3. **[Tutorials](docs/index.md#tutorials)** — task-based guides for stocks, fundamentals,
   funds/indices, macro/FX, gold/crypto.
4. **[How-to guides](docs/index.md#how-to-guides)** — caching/retry, pandas, BYOK FRED,
   live tests, errors.
5. **[Reference](docs/index.md#reference)** — public API, units, source provenance, stability.

Need an overview of all docs? Go to **[docs/index.md](docs/index.md)**.

Using an AI agent? See the separate **[AI usage guide](docs/ai-usage.md)**, **[llms.txt](llms.txt)**,
or **[skills/vnfin](skills/vnfin/SKILL.md)**. Human docs are the primary path above.

## Use vnfin with your coding agent

`vnfin` is built to be an **agent-ready financial-data source** for Claude Code / Codex-style
agents. Paste this prompt to point your agent at it:

```text
Use https://github.com/hungson175/vnfin as the financial-data source for Vietnam-related,
long-term investment research. Install it with:
pip install "vnfin[pandas] @ git+https://github.com/hungson175/vnfin.git". Before coding, read
README.md, docs/index.md, docs/api.md, docs/units.md, and llms.txt. Use vnfin for data
retrieval and calculated metrics only; preserve units, currencies, source names, coverage
warnings, and provenance. Prefer daily/periodic data, do not assume unsupported real-time
coverage, and do not provide personalized investment advice.
```

## Install

Install directly from GitHub:

```bash
pip install git+https://github.com/hungson175/vnfin.git
```

Install with pandas support for `.to_dataframe()`:

```bash
pip install "vnfin[pandas] @ git+https://github.com/hungson175/vnfin.git"
```

Install from a clone for local development:

```bash
git clone https://github.com/hungson175/vnfin.git
cd vnfin
pip install -e ".[pandas]"
```

Requires Python 3.10 or newer. The default path of every domain works without an API key.

## 3-minute quickstart

```python
from datetime import date
import vnfin

# Daily stock prices: VND OHLCV bars, with broker failover.
prices = vnfin.prices.history("FPT", date(2024, 1, 1), date(2024, 6, 30))
print(prices.source, prices.value_unit, prices.bars[-1].close)

# Annual financial statement: raw VND line items.
reports = vnfin.fundamentals.get_financials("FPT", "income", "annual")
latest = reports[0]
print(latest.fiscal_date, latest.currency, len(latest.items))

# FX: VND per 1 USD. Reuse one client when fetching multiple currencies.
fx = vnfin.fx.client()
print(fx.get_rate("USD").rate)

# Macro: no-key Vietnam CPI/GDP/etc. from public macro sources.
cpi = vnfin.macro.get_indicator("VNM", vnfin.macro.MacroIndicator.CPI)
print(cpi.unit, cpi.latest())
```

## Common jobs

| I want to... | Start with |
|--------------|------------|
| Fetch daily stock prices and convert to pandas | [Tutorial: stock prices](docs/tutorials/stock-prices.md) |
| Read financial statements and ratios | [Tutorial: fundamentals](docs/tutorials/fundamentals.md) |
| List mutual funds, NAV, index levels, constituents | [Tutorial: funds and indices](docs/tutorials/funds-and-indices.md) |
| Fetch USD/VND, EUR/VND, GDP, CPI, inflation | [Tutorial: macro and FX](docs/tutorials/macro-and-fx.md) |
| Fetch domestic/world gold or BTC/ETH OHLCV | [Tutorial: gold and crypto](docs/tutorials/gold-and-crypto.md) |
| Understand VND vs thousand-VND vs points | [Units reference](docs/units.md) |
| Handle provider outages and exceptions | [How to handle errors](docs/how-to/errors.md) |
| Use pandas DataFrames | [How to use DataFrames](docs/how-to/pandas-dataframes.md) |
| Run real network checks | [How to run live tests](docs/how-to/live-tests.md) |

## Domains at a glance

Most domains expose two factories:

- `vnfin.<domain>.client()` — recommended failover client.
- `vnfin.<domain>.source()` — primary single-source adapter.

`gold` is the deliberate exception because Vietnam domestic gold (`VND/lượng`) and world gold
(`USD/oz`) are different unit families; use `vnfin.gold.vn()` or `vnfin.gold.world()`.

| Domain | Main entry | Default no-key sources | Canonical unit |
|--------|------------|------------------------|----------------|
| Stocks | `vnfin.prices.history()` / `vnfin.prices.client()` | SSI → VNDirect → VPS → Pinetree | VND |
| Fundamentals | `vnfin.fundamentals.get_financials()` | VNDirect → CafeF | raw VND; ratios per line |
| Funds | `vnfin.funds.source()` | Fmarket | VND/unit |
| Indices | `vnfin.indices.index_history()` | VPS → SSI → VNDirect | points |
| FX | `vnfin.fx.get_rate()` / `vnfin.fx.client()` | open.er-api → Vietcombank | VND per 1 base |
| Macro | `vnfin.macro.get_indicator()` | World Bank → IMF → DBnomics | per indicator |
| Gold | `vnfin.gold.vn()` / `vnfin.gold.world()` | BTMC/PNJ; CurrencyApi | VND/lượng; USD/oz |
| Crypto | `vnfin.crypto.client().get_klines()` | Binance → Coinbase | USD |

For exact public APIs, see [docs/api.md](docs/api.md). For unit rules, see
[docs/units.md](docs/units.md).

## Keys, failover, and data safety

- **No key by default.** The optional keyed source is FRED for macro (`FRED_API_KEY`), and it is
  excluded from the default chain. Gold also accepts `VNFIN_BTMC_WIDGET_KEY` to override a public
  token.
- **Failover is bounded.** Where backups exist, clients try a small same-unit chain and reject unit
  mismatches instead of silently mixing scales.
- **No bundled market data.** Tests use synthetic fixtures; live checks are opt-in.
- **Clean-room policy.** The project does not use VNStock/vnstock-derived code, docs, schemas, or
  endpoint maps. See [docs/vnstock-blacklist.md](docs/vnstock-blacklist.md).

## Development and tests

```bash
pip install -e ".[dev]"
pytest
pytest --cov=vnfin --cov-fail-under=85
VNFIN_LIVE=1 pytest live_tests/
```

Default tests are offline and deterministic. Live tests are real network checks and are kept out of
the default suite.

## Project status

`vnfin` is released as GitHub-installable beta software. The public API is guarded by a snapshot
test and documented in [docs/stability.md](docs/stability.md). See [CHANGELOG.md](CHANGELOG.md) for
release notes and [docs/roadmap.md](docs/roadmap.md) for planned work.

Have a feature request or a new data-source request? Open a GitHub issue with the use case,
desired API shape, expected data frequency, and source/licensing notes. Features are prioritized
for long-term investing and financial-advisor / developer workflows.
