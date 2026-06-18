# Changelog

All notable changes to `vnfin` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/) — see [`docs/stability.md`](docs/stability.md).

## [Unreleased]

### Fixed
- **CafeF fundamentals (`Quater=5`)** — annual reports whose older rows carry CafeF's
  `ReportType=NAM` marker `Quater=5` no longer abort the entire response: an annual report's
  fiscal date is the year-end regardless of the `Quater` marker, and a single period-marker
  anomaly is skipped (surfaced via a `warnings` note) rather than failing the whole request.
  Line-item validation stays strict (malformed data still raises). ([#1](https://github.com/hungson175/vnfin/issues/1))
- **Health harness label honesty** — `run_probe` now reports the *actual* serving `source` from
  the typed result, and each default probe targets its **primary single source** directly, so a
  `prices` probe can no longer report `ssi` healthy when a backup actually served the bar.
  ([#1](https://github.com/hungson175/vnfin/issues/1))
- **CafeF unit/scale (`thousand-VND`)** — CafeF reports statement money in **thousand-VND** but it
  was labeled raw VND, so the failover unit-homogeneity guard accepted VNDirect (raw VND) and CafeF
  (thousand-VND) with matching labels but a 1000× scale mismatch. The CafeF adapter now multiplies
  monetary statement lines by **1000** to emit raw VND (ratios unscaled), matching the VNDirect
  primary. Verified via cross-source magnitude. ([#3](https://github.com/hungson175/vnfin/issues/3))
- **CafeF ratios — quarterly EndDate anchor** — `CafeFFundamentalSource.get_financials(...,
  StatementType.RATIOS, Period.QUARTER)` previously sent a quarterly `EndDate` like `"2-2026"`, which
  CafeF's ratio endpoint rejects (`Time sai dinh dang`). The adapter now always sends a plain year
  anchor for ratios (the typed contract treats ratios as period-agnostic `Period.UNKNOWN`).
  ([#4](https://github.com/hungson175/vnfin/issues/4))
- **Fundamental ratio unit labels** — EPS and BV are per-share monetary values, not dimensionless
  ratios. CafeF reports them in **thousand-VND per share**; they were previously emitted with
  `LineItem.value_unit == "ratio"`. The CafeF adapter now scales EPS/BV by **1000** and labels them
  `"vnd_per_share"`, while dimensionless metrics (PE, ROE, ROA, ROS, DAR, GOS) remain `"ratio"`.
  ([#5](https://github.com/hungson175/vnfin/issues/5))
- **Macro level-indicator positivity guard** — canonical level indicators (`GDP`, `CPI`) now reject
  non-positive values as provider drift / parse errors. Percent/rate indicators (`GDP_GROWTH`,
  `INFLATION`, `UNEMPLOYMENT`) continue to allow negative values. Guard applies to World Bank,
  DBnomics, and IMF DataMapper sources. ([#16](https://github.com/hungson175/vnfin/issues/16))
- **VN gold selector validation** — `BTMCGoldSource.get_quote()` and `PNJGoldSource.get_quote()` now
  reject empty, whitespace-only, or non-string product selectors with `VnfinError` before scanning
  the feed, instead of silently returning the first product or leaking `AttributeError`.
  ([#17](https://github.com/hungson175/vnfin/issues/17))
- **Fundamentals string-input parity** — `vnfin.fundamentals.client().get_financials()` and
  `vnfin.fundamentals.source().get_financials()` now accept string `statement` and `period` values
  (e.g. `"income"`, `"annual"`) just like the top-level `get_financials()` convenience function,
  and raise `VnfinError` for unknown strings instead of leaking `AttributeError`/`KeyError`.
  Coercion helpers are shared across all entry points. ([#25](https://github.com/hungson175/vnfin/issues/25))
- **Currency-api gold history date identity** — `CurrencyApiGoldSource.get_history()` now validates
  the date-pinned document's own `date` field against the requested date. A mismatch raises
  `InvalidData` instead of silently stamping the requested date onto the wrong day's price. If the
  document omits `date`, the requested loop date is still used as a documented fallback.
  ([#35](https://github.com/hungson175/vnfin/issues/35))
- **UDF status strictness** — shared `UDFSource` now requires the inner UDF status field `s`
  to equal `"ok"` for success. `"no_data"` / `"error"` still raise `EmptyData`, but missing or
  unknown status values now raise `InvalidData` so a failover chain does not silently treat a
  drifting provider response as valid price data. ([#39](https://github.com/hungson175/vnfin/issues/39))
- **SSI envelope validation** — `SSIiBoardSource` now validates the outer response envelope
  (`code == "SUCCESS"` and `status == "ok"`) before unwrapping `data`. Provider-side failures
  raise `SourceUnavailable`; malformed or missing envelope fields raise `InvalidData`.
  ([#40](https://github.com/hungson175/vnfin/issues/40))
- **Fmarket envelope requirement** — `FmarketFundSource` now requires at least one of the
  application-level envelope fields `status` or `code` in every response. A response missing both
  raises `InvalidData`; non-2xx application statuses continue to raise `SourceUnavailable`.
  ([#41](https://github.com/hungson175/vnfin/issues/41))
- **CafeF statement period-tag honesty** — `CafeFFundamentalSource` now skips rows whose
  `ReportType` disagrees with the requested `Period` (e.g. annual-tagged rows in a quarterly pull),
  surfaced via a `warnings` note, instead of silently relabeling them. Ratios remain period-agnostic.
  ([#45](https://github.com/hungson175/vnfin/issues/45))
- **CafeF statement row ReportType vocabulary** — `CafeFFundamentalSource` now accepts the
  documented response row tags `HK` (annual) and `H` (quarterly) in addition to the request-side
  strings `NAM`/`QUY`, so real CafeF payloads are no longer rejected as `EmptyData`.
  ([#44](https://github.com/hungson175/vnfin/issues/44))
- **CafeF `is_bank` strict validation** — `CafeFFundamentalSource` now resolves `is_bank` through
  `resolve_is_bank()`, rejecting non-boolean values such as the string `"False"` with `VnfinError`
  instead of truthy-coercing them. ([#11](https://github.com/hungson175/vnfin/issues/11))
- **VNDirect statement contract strictness** — `VNDirectFundamentalSource` now skips rows whose
  `reportType` or `modelType` contradicts the request, and raises `InvalidData` on duplicate
  `itemCode` values within the same fiscal period. ([#44](https://github.com/hungson175/vnfin/issues/44),
  [#26](https://github.com/hungson175/vnfin/issues/26))
- **VNDirect ratio units** — EPS and BV are per-share monetary values; the VNDirect adapter now
  labels them `"vnd_per_share"` instead of `"ratio"`. ([#19](https://github.com/hungson175/vnfin/issues/19))
- **`is_bank` strict validation** — `resolve_is_bank()` now rejects non-boolean, non-`AUTO`
  values such as the string `"False"` with `VnfinError`, eliminating truthiness bugs.
  ([#11](https://github.com/hungson175/vnfin/issues/11))
- **Fundamental statement `Period.UNKNOWN` guard** — Both CafeF and VNDirect adapters reject
  `Period.UNKNOWN` for income/balance/cashflow statements (it is only meaningful for ratios).
  ([#10](https://github.com/hungson175/vnfin/issues/10))
- **FRED API-key hygiene** — `FREDMacroSource` now treats whitespace-only or non-string
  `api_key` values as missing, keeping the source cleanly skippable and preventing bytes or
  whitespace from being sent to the provider. ([#58](https://github.com/hungson175/vnfin/issues/58))
- **World Bank indicator-code validation** — `WorldBankMacroSource.get_indicator()` now rejects
  non-string `indicator_code` values (including `bytes`) with `InvalidData` before any URL is built.
  ([#57](https://github.com/hungson175/vnfin/issues/57))
- **Fmarket filter validation** — `FmarketFundSource.list_funds()` now rejects non-string
  `asset_type` and `search` filter values with `InvalidData` before building the provider request.
  ([#56](https://github.com/hungson175/vnfin/issues/56))
- **UDF empty-volume strictness** — `UDFSource` now treats a present-but-empty `v` array as a
  malformed response (`InvalidData`) while still allowing a missing `v` field to default to zero
  volume. ([#55](https://github.com/hungson175/vnfin/issues/55))
- **Index constituents envelope requirement** — `IndexConstituentsSource` now requires
  `code == "SUCCESS"`; missing, null, or non-success codes raise `InvalidData` instead of being
  parsed as a valid basket. ([#54](https://github.com/hungson175/vnfin/issues/54))
- **Stooq OHLC validation** — `StooqGoldSource` now validates the full OHLC row (numeric, positive,
  self-consistent high/low/open/close) and rejects malformed rows as `InvalidData`.
  ([#53](https://github.com/hungson175/vnfin/issues/53))
- **VNDirect ratio row strictness** — `VNDirectFundamentalSource._get_ratios()` now validates that
  `ratioCode` is a non-empty string and `itemName` is a string or `None`, raising `InvalidData` for
  malformed provider rows instead of leaking raw `TypeError`/`AttributeError`. ([#62](https://github.com/hungson175/vnfin/issues/62))
- **IMF year-range validation** — `IMFDataMapperSource` now rejects out-of-range numeric years with
  `InvalidData` instead of leaking raw `ValueError`. ([#61](https://github.com/hungson175/vnfin/issues/61))
- **Coinbase hyphenated quote validation** — `CoinbaseCryptoSource.parse_symbol()` now validates the
  quote leg of hyphenated products against the recognized quote-asset set; unknown quote legs raise
  `InvalidData` before any request. ([#60](https://github.com/hungson175/vnfin/issues/60))
- **Crypto zero-price rejection** — `BinanceCryptoSource` and `CoinbaseCryptoSource` now reject
  zero-price OHLC candles as `InvalidData`; volume may still be zero. ([#59](https://github.com/hungson175/vnfin/issues/59))
- **GoldApi symbol validation** — `GoldApiSource` now validates `symbol` as a non-empty string in the
  constructor, raising `VnfinError` for `None`, non-string, empty, or whitespace-only values.
  ([#52](https://github.com/hungson175/vnfin/issues/52))
- **FRED application-error envelope detection** — `FREDMacroSource` now detects FRED error envelopes
  (`error_code` / `error_message`) and raises `InvalidData` instead of parsing them as data or
  treating them as empty. ([#51](https://github.com/hungson175/vnfin/issues/51))
- **World Bank country validation** — `WorldBankMacroSource.get_indicator()` now validates
  `country_iso3` as a string before any string operation and requires a 3-letter alphabetic ISO3
  code, raising `InvalidData` before network for non-string/malformed values.
  ([#32](https://github.com/hungson175/vnfin/issues/32))
- **World Bank year-bound validation** — `WorldBankMacroSource` now rejects request years outside
  the `datetime.date` supported range `1..9999` with `InvalidData` before contacting the provider,
  complementing the existing out-of-range observation-year guard.
  ([#46](https://github.com/hungson175/vnfin/issues/46),
  [#63](https://github.com/hungson175/vnfin/issues/63))
- **Macro client country validation** — `MacroClient.get_indicator()` validates the country as a
  3-letter ISO3 code before building the failover engine. ([#32](https://github.com/hungson175/vnfin/issues/32))
- **Vietcombank self-rate skip** — `VietcombankFXSource` now skips the provider's VND/VND self-rate.
  ([#47](https://github.com/hungson175/vnfin/issues/47))
- **OpenER timestamp overflow guard** — `OpenErApiFXSource` now catches out-of-range
  `time_last_update_unix` timestamps and falls back to UTC now instead of leaking `OverflowError`.
  ([#43](https://github.com/hungson175/vnfin/issues/43))
- **World gold history date-bound validation** — `CurrencyApiGoldSource.get_history()` and
  `StooqGoldSource.get_history()` now reject non-date `start`/`end` bounds with `InvalidData`
  before any fetch. ([#42](https://github.com/hungson175/vnfin/issues/42))
- **Health macro probe failover path** — the default macro health probe now routes through
  `vnfin.macro.get_indicator()` so `MacroIndicator.CPI` maps to the correct provider series; the
  probe label is updated to `macro/canonical/VNM-CPI` to reflect that it exercises failover.
  ([#36](https://github.com/hungson175/vnfin/issues/36))
- **Index history canonical symbol** — `IndexClient` and index UDF sources now return the
  canonical symbol the caller requested (e.g. "UPCOM") while keeping the provider alias in
  `provider_symbol`. Previously the provider alias leaked into the public `symbol` field.
  ([#64](https://github.com/hungson175/vnfin/issues/64))
- **Index constituents validation** — `IndexConstituentsSource` now rejects empty/whitespace
  normalized member symbols and duplicate symbols as `InvalidData`.
  ([#30](https://github.com/hungson175/vnfin/issues/30))
- **Price interval validation** — `FailoverPriceClient.get_history()` validates that the
  `interval` argument is an `Interval` enum before the failover engine touches it, preventing
  a raw `AttributeError` from malformed caller input.
  ([#23](https://github.com/hungson175/vnfin/issues/23))
- **UDF response identity guard** — `UDFSource` now validates a provider-echoed `symbol` field
  in the response against the requested symbol/alias, raising `InvalidData` on mismatch before
  stamping identifiers onto the result. ([#21](https://github.com/hungson175/vnfin/issues/21))
- **Zero market-observation rejection** — `UDFSource` now rejects zero OHLC prices and
  `FmarketFundSource` rejects zero NAV values as `InvalidData`; volume may still be zero.
  ([#13](https://github.com/hungson175/vnfin/issues/13))
- **Price adjustment-policy guard** — `FailoverPriceClient` now rejects chains that mix declared
  adjustment policies (e.g. `PROVIDER_ADJUSTED` with `RAW`/`MIXED`) at construction time, mirroring
  the existing unit-homogeneity guard. ([#7](https://github.com/hungson175/vnfin/issues/7))

## [0.2.0] — 2026-06-18

> Version bumped and release-ready. **Tag/push/PyPI publish are pending maintainer approval**
> (not yet performed).

### Added
- **API stability gate** — `tests/test_public_api_surface.py` introspects the public surface
  (per-module `__all__`, factory/method signatures, frozen-dataclass fields, enum members/values,
  public-class constructors, and canonical unit/currency defaults) and diffs it against a committed
  per-release baseline snapshot (`tests/snapshots/public_api_v0_2_0.json`; v0.1.0 retained for
  audit) with a **compatibility-aware** comparator (`scripts/dump_api_surface.py`). Accidental
  breaking changes fail the suite; additive changes are reported. SemVer + deprecation policy
  documented in [`docs/stability.md`](docs/stability.md).
- **Upstream health monitoring** (opt-in, private `vnfin/_health.py` + `scripts/healthcheck.py`) —
  typed `SourceHealth` per probe (reachability, schema conformance, value sanity, latency),
  schema-drift detection via required-paths/types, a 5-domain critical probe set, and sanitised
  `STATUS.md`/JSON renderers. Live-only; never runs in CI; never auto-pushed.
- **FX domain** (`vnfin.fx`) — daily/current foreign-exchange reference rates vs VND, no-key
  failover **open.er-api → Vietcombank XML**, canonical unit *VND per 1 unit of base* (USD/VND,
  plus cross-rates EUR/CNY/JPY/…), typed `FXRate`, two-layer unit guard, optional `bid`/`ask`.
  Spot/current only (history deferred to BYOK). Opt-in live USD/VND cross-source parity test;
  opt-in (rate-limit-aware) FX health probe. See [`docs/design/fx-sources.md`](docs/design/fx-sources.md),
  [`docs/sources/fx-open-er-api.md`](docs/sources/fx-open-er-api.md),
  [`docs/sources/fx-vietcombank.md`](docs/sources/fx-vietcombank.md).
- Explicit `__all__` for `vnfin.exceptions`; `vnfin.sources` now covered by the stability snapshot.

### Notes
- Corporate-actions/dividends are **designed only** ([`docs/design/corporate-actions.md`](docs/design/corporate-actions.md));
  implementation deferred to 0.3.1 after the security master.
- No public push / tag / PyPI publish performed — held for maintainer approval.

## [0.1.0] — 2026-06-18

### Added
- Initial clean-room release. No-key-first + optional BYOK across 7 domains: **prices** (daily
  OHLCV, VND), **fundamentals** (statements, VND), **funds** (NAV, VND/unit), **indices** (points),
  **gold** (VN VND/lượng + world USD/oz), **crypto** (USD), **macro** (no-key World Bank → IMF →
  DBnomics; FRED/BEA/BLS BYOK).
- Generic `FailoverClient` with a **unit-homogeneity guard**; typed frozen-dataclass results with
  explicit units/currency; VN trading-calendar staleness checks.
- 750+ offline tests (94% coverage, synthetic fixtures only) + opt-in live cross-source checks;
  CI coverage gate (≥85%). Apache-2.0.

[0.2.0]: https://github.com/hungson175/vnfin/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/hungson175/vnfin/releases/tag/v0.1.0
