# Changelog

All notable changes to `vnfin` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/) — see [`docs/stability.md`](docs/stability.md).

## [Unreleased] — 0.2.0 (release-ready, not yet released)

### Added
- **API stability gate** — `tests/test_public_api_surface.py` introspects the public surface
  (per-module `__all__`, factory/method signatures, frozen-dataclass fields, enum members/values,
  public-class constructors, and canonical unit/currency defaults) and diffs it against a committed
  baseline (`tests/snapshots/public_api_v0_1_0.json`) with a **compatibility-aware** comparator
  (`scripts/dump_api_surface.py`). Accidental breaking changes fail the suite; additive changes are
  reported. SemVer + deprecation policy documented in [`docs/stability.md`](docs/stability.md).
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

[Unreleased]: https://github.com/hungson175/vnfin/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hungson175/vnfin/releases/tag/v0.1.0
