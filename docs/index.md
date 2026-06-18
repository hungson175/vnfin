# vnfin documentation

Welcome. This documentation is organized for **end users first**: people installing `vnfin` and
trying to fetch data correctly. Start broad, then drill down only when you need more detail.

## Recommended path

1. **[README](../README.md)** — install and three-minute quickstart.
2. **[Getting started](getting-started.md)** — 10-minute walkthrough with first results and
   DataFrame conversion.
3. Pick the tutorial matching your job.
4. Use how-to guides when you hit operational questions.
5. Use reference docs for exact API, units, source provenance, and stability policy.

## Tutorials

Task-based guides with copy-paste examples:

- **[Stock prices](tutorials/stock-prices.md)** — daily OHLCV, failover, pandas.
- **[Fundamentals](tutorials/fundamentals.md)** — income/balance/cashflow/ratios, raw VND units.
- **[Funds and indices](tutorials/funds-and-indices.md)** — Fmarket funds, NAV, VNINDEX, constituents.
- **[Macro and FX](tutorials/macro-and-fx.md)** — GDP/CPI/inflation plus VND FX rates.
- **[Gold and crypto](tutorials/gold-and-crypto.md)** — VN gold, world gold, BTC/ETH OHLCV.

## How-to guides

Focused answers for common operational tasks:

- **[Use pandas DataFrames](how-to/pandas-dataframes.md)** — install extras, metadata in `df.attrs`.
- **[Handle errors and failover](how-to/errors.md)** — exception types and retry strategy for callers.
- **[Use caching and retries](how-to/cache-retry.md)** — reuse clients, opt-in transport cache/retry.
- **[Use FRED BYOK](how-to/byok-fred.md)** — optional macro key without changing no-key defaults.
- **[Run live tests](how-to/live-tests.md)** — real network checks, environment guard, diagnostics.

## Reference

- **[Public API](api.md)** — domain factories, facade names, and exact entry points.
- **[Units](units.md)** — canonical unit per domain; read this before comparing numbers.
- **[Sources](sources/)** — provider endpoints, terms/rate-limit notes, clean-room provenance.
- **[Stability](stability.md)** — SemVer policy and public API snapshot gate.
- **[Roadmap](roadmap.md)** and **[CHANGELOG](../CHANGELOG.md)** — release notes and planned work.
- **[Reference index](reference/index.md)** — compact list of reference-only pages.

## For AI agents

AI-facing material is intentionally separate from the human path:

- [AI usage guide](ai-usage.md)
- [llms.txt](../llms.txt)
- [Anthropic-style skill](../skills/vnfin/SKILL.md)

Those files are useful when you want an agent to call `vnfin`, but humans should start from the
README and task tutorials above.

## Maintainer-only context

The following folders preserve design/research history. They are **not** the starting point for
normal users:

- `docs/design/`
- `docs/research/`
- `docs/steps/`
- `tasks/`, `context/`, and maintainer scripts
