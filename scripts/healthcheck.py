#!/usr/bin/env python3
"""Thin CLI over ``vnfin._health`` — probe upstream providers and report health.

This hits the **live network** and is therefore opt-in (like ``live_tests/``); it must never
run in CI. Run it manually or from a scheduled job on a host that can reach the VN providers
(this datacenter cannot reach some — they appear as ``host_blocked``, which is an environment
signal, not a source outage).

Usage::

    python scripts/healthcheck.py                       # table to stdout
    python scripts/healthcheck.py --status-md STATUS.md  # write the status markdown
    python scripts/healthcheck.py --json status.json     # write the sanitised JSON snapshot
    python scripts/healthcheck.py --domain prices --domain crypto   # filter

Exit code: 0 if no probe is ``down``/``degraded``; 1 otherwise (so a scheduled wrapper can
alert). ``host_blocked`` / ``skipped`` do not fail the run. ``--exit-zero`` always exits 0.

Neither STATUS.md nor the JSON is pushed automatically — publishing is a separate, explicit step.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

# make the package importable when run as a loose script
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from vnfin._health import (  # noqa: E402
    HealthStatus,
    default_probes,
    render_status_md,
    run_all,
    to_status_json,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="vnfin upstream source healthcheck")
    p.add_argument("--status-md", type=pathlib.Path, help="write STATUS markdown to this path")
    p.add_argument("--json", type=pathlib.Path, help="write sanitised JSON snapshot to this path")
    p.add_argument("--domain", action="append", default=[], help="only probe these domains")
    p.add_argument("--timeout", type=float, default=25.0)
    p.add_argument("--exit-zero", action="store_true", help="always exit 0 (monitoring mode)")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    probes = default_probes(timeout=args.timeout)
    if args.domain:
        wanted = set(args.domain)
        probes = [p for p in probes if p.domain in wanted]
    healths = run_all(probes)

    md = render_status_md(healths)
    print(md)
    if args.status_md:
        args.status_md.write_text(md)
        print(f"wrote {args.status_md}")
    if args.json:
        args.json.write_text(to_status_json(healths))
        print(f"wrote {args.json}")

    failing = [h for h in healths if h.status in (HealthStatus.DOWN, HealthStatus.DEGRADED)]
    if args.exit_zero:
        return 0
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
