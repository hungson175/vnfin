# Changelog

All notable changes to `vnfin` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/) — see [`docs/stability.md`](docs/stability.md).

## [Unreleased]

### Fixed
- **Failover provenance guard** — every domain failover client (price, crypto, gold, macro,
  fundamentals) now verifies that an accepted result's stamped ``source`` matches the source
  that actually produced it. A result whose provenance does not match (e.g. a primary returning
  a result labelled with another provider's name) is recorded as a rejected source attempt and
  the chain fails over — the provenance is never silently relabelled — so audit logs, backtests,
  and reconciliation can trust ``result.source`` / ``report.source``. Implemented as an optional
  engine-level ``provenance_of`` guard with a result-source extractor that also handles composite
  results (the fundamentals report tuple). ([#126](https://github.com/hungson175/vnfin/issues/126))
- **Failover bar time-key type guard** — the price, crypto, and gold failover result guards now
  validate each bar's time key before the ascending-order compare and window/coverage logic.
  ``PriceBar.time`` and ``CryptoBar.time`` must be timezone-aware ``datetime`` values (naive
  datetimes and non-datetime keys are rejected); ``GoldBar.date`` must be a plain ``datetime.date``
  (``datetime`` keys are rejected since they subclass ``date``). A malformed key is recorded as a
  rejected source attempt instead of leaking a raw ``TypeError``/``AttributeError``.
  ([#124](https://github.com/hungson175/vnfin/issues/124))
- **Macro point-key type guard** — the macro failover result guard now rejects an
  ``IndicatorSeries`` whose ``points`` keys are not plain ``datetime.date`` values. ``datetime``
  keys (which subclass ``date`` but carry intraday/timezone meaning), as well as ``str`` /
  ``int`` / ``None`` keys, are rejected before the ascending-order comparison so a malformed key
  is a recorded rejected attempt instead of a leaked ``TypeError``.
  ([#123](https://github.com/hungson175/vnfin/issues/123))
- **Failover malformed result-container guard** — the price, crypto, gold, and macro failover
  result guards now type-check the returned container (``PriceHistory`` / ``CryptoHistory`` /
  ``GoldHistory`` / ``IndicatorSeries``) before reading ``.bars`` / ``.points``. A source
  returning a malformed non-typed result (e.g. a plain ``dict`` or ``None``) is now recorded as
  a rejected source attempt — and the chain fails over to the next source or raises a clean
  ``AllSourcesFailed`` — instead of leaking a raw ``AttributeError`` to the caller.
  ([#125](https://github.com/hungson175/vnfin/issues/125))
- **Fundamental failover line-item guard** — the fundamentals failover result guard now
  validates returned ``LineItem`` fields before accepting a source result: ``item_code`` must
  be a non-empty string, ``name`` must be a string (empty allowed), ``value`` must be a finite
  non-bool number, and duplicate ``item_code`` values in one report are rejected. A custom or
  future source returning ``NaN``/``Infinity``/bool/str values, blank/non-string codes, or
  duplicate-conflicting codes is now rejected and the backup attempted instead.
  ([#122](https://github.com/hungson175/vnfin/issues/122))
- **Provider timestamp coercion** — shared ``parse_provider_int()`` rejects JSON booleans
  before epoch timestamp conversion in UDF, Binance, and Coinbase paths; OpenER bool
  timestamps fall back to now instead of epoch. ([#106](https://github.com/hungson175/vnfin/issues/106))
- **World Bank metadata containers** — reject present non-object ``indicator`` and
  ``country`` observation containers, not just malformed ``value`` fields. ([#101](https://github.com/hungson175/vnfin/issues/101))
- **CafeF fiscal/display metadata** — reject non-string line-item ``Name`` values and
  boolean ``Year``/``Quater`` before integer coercion instead of leaking
  ``AttributeError`` or year-1 reports. ([#94](https://github.com/hungson175/vnfin/issues/94))
- **FX failover rate guard** — reject infinite and boolean main rates in the
  request-aware result guard, matching direct source validation. ([#88](https://github.com/hungson175/vnfin/issues/88))
- **Index member metadata** — reject present non-string ``exchange``, company name,
  and ``isin`` fields instead of silently erasing malformed provider metadata.
  ([#100](https://github.com/hungson175/vnfin/issues/100))
- **BTMC product/karat metadata** — validate ``@n_<row>`` and ``@k_<row>`` types
  before normalization so malformed rows raise ``InvalidData`` instead of leaking
  raw ``TypeError`` or typed non-string ``GoldQuote.karat``. ([#98](https://github.com/hungson175/vnfin/issues/98))
- **Gold failover coverage thresholds** — reject boolean and non-numeric
  ``min_coverage`` / ``warn_coverage`` values so ``False`` cannot silently disable
  the sparse-history guard. ([#96](https://github.com/hungson175/vnfin/issues/96))
- **World Bank descriptive metadata** — reject present non-string
  ``indicator.value``, ``country.value``, and ``unit`` fields instead of letting
  malformed provider metadata enter typed ``IndicatorSeries``. ([#101](https://github.com/hungson175/vnfin/issues/101))
- **FRED units metadata** — reject present non-string top-level ``units`` values instead
  of silently stamping an empty unit label. ([#102](https://github.com/hungson175/vnfin/issues/102))
- **FX failover UTC strictness** — `FailoverFXClient` now rejects timezone-aware `as_of_utc`
  timestamps that are not exactly UTC (e.g. `+07:00`), not only naive datetimes.
- **Macro failover result validation** — `MacroClient` now rejects a returned series whose
  `indicator_code`/`indicator_name` match a different canonical indicator, points that are
  not strictly ascending by date, or non-finite (NaN/inf) point values.
- **Index constituents data envelope** — validate ``data`` is a list before treating
  falsy containers as empty membership; malformed SUCCESS payloads raise
  ``InvalidData`` instead of ``EmptyData``. ([#103](https://github.com/hungson175/vnfin/issues/103))
- **Macro response containment** — FRED and World Bank adapters drop observations
  outside the requested date/year window and raise ``EmptyData`` when no in-window
  points remain. ([#105](https://github.com/hungson175/vnfin/issues/105))
- **DBnomics period/frequency validation** — reject `period_start_day` values that contradict
  the declared observation frequency (annual must be Jan 1; monthly must be month-start).
  ([#104](https://github.com/hungson175/vnfin/issues/104))
- **VN trading calendar** — add missing 2025-05-02 and 2026-08-31 official market closures so
  `expected_latest_trading_day()` no longer treats National Day / Labor Day bridge sessions as
  trading days. ([#92](https://github.com/hungson175/vnfin/issues/92))
- **Health STATUS.md renderer** — escape pipe and newline characters in every Markdown table cell
  so provider/exception text cannot inject forged health rows. ([#89](https://github.com/hungson175/vnfin/issues/89))
- **Secret redaction (`client_secret`)** — classify OAuth-style `client_secret` / `X-Client-Secret`
  names as sensitive for redaction and deterministic cache-key hashing; wrapped transport errors no
  longer leak plaintext credentials. ([#38](https://github.com/hungson175/vnfin/issues/38))
- **Fmarket nested `data` validation** — `list_funds()` and `holdings()` raise `InvalidData` when
  the success envelope carries a non-object `data` payload instead of leaking `AttributeError`.
  ([#91](https://github.com/hungson175/vnfin/issues/91))
- **Provider numeric coercion** — shared `parse_provider_float()` rejects JSON booleans before
  coercion across price, crypto, fund, fundamental, and FX parsers so `true` cannot become
  plausible financial values. ([#87](https://github.com/hungson175/vnfin/issues/87))
- **OpenER USD self-rate anchor** — reject USD-base payloads whose `rates["USD"]` drifts from 1
  before deriving cross-rates, preventing silently wrong USD/VND values. ([#93](https://github.com/hungson175/vnfin/issues/93))
- **FailoverCryptoClient iterator sources** — materialize `sources` before unit-guard and engine
  wiring so generator/iterator chains keep the primary source. ([#95](https://github.com/hungson175/vnfin/issues/95))
- **Fmarket metadata typing** — `list_funds()` and `holdings()` reject non-string fund name,
  manager, asset-type, and industry fields instead of stringifying malformed provider values.
  ([#97](https://github.com/hungson175/vnfin/issues/97), [#99](https://github.com/hungson175/vnfin/issues/99))
- **Fmarket holdings aggregate weight** — reject top-holdings baskets whose weights sum above
  100%. ([#90](https://github.com/hungson175/vnfin/issues/90))
- **Price/crypto failover date window** — reject non-empty histories with no bars inside the
  requested `[start, end]` range so out-of-window results fail over instead of succeeding.
  ([#84](https://github.com/hungson175/vnfin/issues/84))
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
- **UDF envelope/array hardening** — `UDFSource` now validates that the extracted payload is a
  `dict` and that the OHLCV arrays are sequences before indexing/length checks. Malformed
  envelopes, missing `data` keys, and scalar/null arrays raise `InvalidData` instead of leaking
  raw `AttributeError`/`TypeError`/`KeyError`. ([#55](https://github.com/hungson175/vnfin/issues/55))
- **VNDirect ratio row shape safety** — ratio rows that are not JSON objects (list, `None`,
  string, number) now raise `InvalidData` instead of leaking raw `AttributeError`.
  ([#62](https://github.com/hungson175/vnfin/issues/62))
- **Crypto base-asset validation** — `BinanceCryptoSource` and `CoinbaseCryptoSource` now
  validate the base token before any network call, rejecting symbols with spaces, slashes, or
  other non-alphanumeric characters. ([#60](https://github.com/hungson175/vnfin/issues/60))
- **FRED BYOK key redaction** — provider error envelopes from FRED now redact the configured
  `api_key` from `error_message` before raising `InvalidData`, preventing the BYOK secret from
  leaking in exception text. ([#51](https://github.com/hungson175/vnfin/issues/51))
- **IMF input validation** — `IMFDataMapperSource` now validates `country_iso3` as a 3-letter
  alphabetic string and converts unsupported indicator values to `InvalidData` before any
  network call. ([#61](https://github.com/hungson175/vnfin/issues/61))
- **GoldAPI symbol whitelist** — `GoldApiSource` now restricts symbols to the supported world
  spot tickers `XAU` and `XAG`, rejecting unsupported or malformed symbols before the provider
  is contacted. ([#52](https://github.com/hungson175/vnfin/issues/52))
- **Fmarket filter hygiene** — `FmarketFundSource.list_funds()` treats whitespace-only
  `asset_type`/`search` as absent so the provider body never contains blank filters, and the
  invalid `product_id` tests now assert zero transport calls for every rejected value.
  ([#56](https://github.com/hungson175/vnfin/issues/56))
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
