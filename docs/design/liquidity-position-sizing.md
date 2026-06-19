# Liquidity & position sizing — design & approximation notes (#146)

`vnfin.liquidity` turns an existing daily `PriceHistory` into liquidity/marketability
stats and a max-order estimate for long-horizon allocation workflows. It is **offline**
and **additive** — no new external data source.

## Approximation: `close * volume`, NOT provider turnover

The MVP estimates daily traded value as **`close * volume`** and labels it
`value_kind="close_x_volume_estimate"` with the warning
`traded_value_estimated_from_close_x_volume`. This is **not** a provider-published
turnover/traded-value field — clean VN sources currently expose OHLCV only. The labeling
makes the approximation impossible to miss; we never rename it to a turnover field.

## Scope (MVP)

- In: average/median daily traded-value estimate, average/median daily volume, a max-order
  estimate (`avg_daily_value_vnd * adv_fraction`), and capital ratios when `capital_vnd` is
  given.
- Equity money series only: `currency="VND"`, `value_unit="VND"`, daily `Interval.D1`.
  Index point series (`value_unit="points"`), crypto, non-VND, and non-daily are rejected.
- Price-source provenance and existing `PriceHistory.warnings` are preserved.
- A zero-volume window returns a zero-liquidity profile with a `zero_liquidity` warning
  (and `None` capital ratio) rather than dividing by zero.

## Explicitly NOT in this issue (future, separate design issues)

Each of these needs its own source discovery + legal/provenance + unit contracts before
implementation, so they are deliberately out of #146:

- provider-published turnover / traded value ingestion,
- shares outstanding / market cap / free float / foreign room,
- lot-size, transaction-cost, or tax assumptions,
- intraday / real-time liquidity.

No VNStock or derived material was consulted (clean-room).
