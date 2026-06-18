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
