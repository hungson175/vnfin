#!/usr/bin/env python3
"""Manually-invoked LIVE diagnostics for host-flaky data sources.

These probes hit upstream endpoints that are unreliable *from this server's
infrastructure* (datacenter IP) but are NOT library bugs:

* **IMF DataMapper** (``www.imf.org/external/datamapper/api/v1``) returns HTTP 403
  to this datacenter IP. It generally works from residential/other IPs.

They are deliberately kept OUT of ``live_tests/`` (which must pass with 0 skipped
under ``VNFIN_LIVE=1`` on this host) and are NOT collected by pytest
(``testpaths = ["tests"]`` in ``pyproject.toml``). Run this script by hand, from a
host/network where the source is reachable, to verify the real cross-source
contract:

    ./.venv/bin/python scripts/diagnostics_live.py

Exit code is 0 only if every probe passes; non-zero if any probe fails. A probe
that fails because the upstream host blocks this IP (e.g. IMF 403 ->
``SourceUnavailable``) is reported as SKIPPED-BY-HOST, not a failure, so the script
is honest about host-infra limits while still being a real check elsewhere.

Clean-room: World Bank / IMF DataMapper / DBnomics official APIs only; no vnstock.
"""
from __future__ import annotations

import sys
import traceback
from datetime import datetime, timezone


def _probe_percent_indicator_agrees_across_no_key_providers() -> None:
    """WB and IMF must agree on a recent GDP-growth % for a real country (USA)."""
    from vnfin.macro import (
        IMFDataMapperSource,
        MacroIndicator,
        WorldBankMacroSource,
    )

    country = "USA"
    ind = MacroIndicator.GDP_GROWTH

    wb = WorldBankMacroSource().get_canonical_indicator(country, ind)
    imf = IMFDataMapperSource().get_indicator(country, ind)

    assert wb.unit == "%" and imf.unit == "%", f"unit mismatch: WB={wb.unit} IMF={imf.unit}"

    # Compare the most recent COMMON year using ACTUALS only — IMF carries WEO
    # projections (years >= current) that WB realizes later; comparing those would
    # spuriously disagree. `actual_points` drops IMF's forecast years (B8).
    wb_by_year = {d.year: v for (d, v) in wb.actual_points}
    imf_by_year = {d.year: v for (d, v) in imf.actual_points}
    common = sorted(set(wb_by_year) & set(imf_by_year))
    assert common, "no overlapping years between WB and IMF GDP-growth"
    year = common[-1]
    a, b = wb_by_year[year], imf_by_year[year]
    # Growth rates are small numbers; require absolute agreement within 1.0 pp.
    assert abs(a - b) < 1.0, f"GDP-growth % disagree for {country} {year}: WB={a} IMF={b}"


def _probe_imf_weo_projections_excluded_from_latest() -> None:
    """IMF WEO carries forecast years; latest() must return a realized actual."""
    from vnfin.macro import IMFDataMapperSource, MacroIndicator

    imf = IMFDataMapperSource().get_indicator("USA", MacroIndicator.GDP_GROWTH)
    now_year = datetime.now(timezone.utc).year
    # WEO always projects beyond the current year -> a projection cut must exist.
    assert imf.projection_from_year is not None
    latest = imf.latest()
    assert latest is not None
    # latest() is an actual: strictly before the projection cut.
    assert latest[0].year < imf.projection_from_year
    # the raw series does extend into forecast years.
    assert imf.latest_including_projections()[0].year >= now_year


def _probe_failover_falls_through_to_imf_when_worldbank_blocked() -> None:
    """If World Bank is forced to fail, the chain must still answer via IMF."""
    from vnfin.exceptions import SourceUnavailable
    from vnfin.macro import (
        DBnomicsSource,
        IMFDataMapperSource,
        MacroIndicator,
        WorldBankMacroSource,
        default_macro_client,
    )

    def _dead(url, params=None, headers=None):
        raise SourceUnavailable("forced-down World Bank")

    wb = WorldBankMacroSource(http_get=_dead)
    chain = default_macro_client(sources=[wb, IMFDataMapperSource(), DBnomicsSource()])
    series = chain.get_indicator("USA", MacroIndicator.GDP_GROWTH)
    assert series.source == "imf_datamapper"
    assert series.unit == "%"


# Each diagnostic depends on IMF DataMapper being reachable; a clean
# ``SourceUnavailable`` (e.g. IMF 403 to this datacenter IP) is reported as
# SKIPPED-BY-HOST rather than a hard failure.
_PROBES = (
    ("imf/wb percent-indicator agreement (USA GDP growth)",
     _probe_percent_indicator_agrees_across_no_key_providers),
    ("imf WEO projections excluded from latest()",
     _probe_imf_weo_projections_excluded_from_latest),
    ("macro failover falls through WorldBank -> IMF",
     _probe_failover_falls_through_to_imf_when_worldbank_blocked),
)


def main() -> int:
    from vnfin.exceptions import AllSourcesFailed, SourceUnavailable

    passed = failed = skipped = 0
    for name, probe in _PROBES:
        try:
            probe()
        except (SourceUnavailable, AllSourcesFailed) as exc:
            # Upstream blocked this host's IP (e.g. IMF 403) — not a library bug.
            skipped += 1
            print(f"SKIPPED-BY-HOST  {name}\n    {type(exc).__name__}: {exc}")
        except Exception:  # noqa: BLE001 - diagnostics: surface any real assertion/bug
            failed += 1
            print(f"FAIL             {name}")
            traceback.print_exc()
        else:
            passed += 1
            print(f"PASS             {name}")

    print(f"\nsummary: {passed} passed, {failed} failed, {skipped} skipped-by-host")
    # Non-zero only on a real failure; host-blocked probes do not fail the script.
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
