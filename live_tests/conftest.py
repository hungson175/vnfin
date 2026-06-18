"""Live-network test guard.

These tests are intentionally OUTSIDE the default ``tests/`` collection (see
``[tool.pytest.ini_options] testpaths`` in pyproject.toml), so the default suite never
runs or skips them. They are REAL cross-source/integration checks — never mocked.

Run them explicitly:  ``VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/``

Running them WITHOUT ``VNFIN_LIVE=1`` fails clearly (it does not skip) — they require
live network access on purpose.
"""
import os

import pytest


def pytest_configure(config):
    if os.getenv("VNFIN_LIVE") != "1":
        raise pytest.UsageError(
            "live_tests/ require live network access. Set VNFIN_LIVE=1 to run them "
            "(real cross-source/integration checks; never mocked, never skipped)."
        )
