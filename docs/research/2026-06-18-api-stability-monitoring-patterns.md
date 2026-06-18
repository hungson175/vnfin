# API Stability and Upstream Monitoring Patterns for a Python Data-Client Library

**Date:** 2026-06-18
**Scope:** vnfin-oss — a thin OSS Python client over third-party financial HTTP APIs.
**VNStock exclusion:** All research and recommendations are VNStock-free (primary/license-clear sources only).

---

## Part A — Keeping YOUR Public Python API Stable

### Problem statement

A data-client library evolves rapidly (new endpoints, renamed fields, model refactors). Without guardrails, maintainers accidentally remove parameters, rename classes, or change return types — which silently breaks downstream user code. The goal is to make such regressions immediately visible in CI, not after a user files a bug.

---

### A1. Define and Protect the Public Surface First

Before you can test API stability, you must define what is public.

**Recommended approach (griffe guidance, [Griffe public-APIs](https://mkdocstrings.github.io/griffe/guide/users/recommendations/public-apis/)):**

1. Prefix every internal module and helper with `_` (e.g., `_http.py`, `_parser.py`).
2. Expose only stable symbols through `src/vnfin/__init__.py` using an explicit `__all__`.
3. Never expose internal module paths in your public docs — reorganizing internals should be a non-event for users.

```python
# src/vnfin/__init__.py
from vnfin._market import MarketClient
from vnfin._company import CompanyClient
from vnfin.models import PriceBar, FinancialStatement

__all__ = [
    "MarketClient",
    "CompanyClient",
    "PriceBar",
    "FinancialStatement",
]
```

**Outcome:** griffe and stubtest both honour `__all__` and `_`-prefixing when determining what is public. Internal changes are invisible to both tools.

---

### A2. Golden-File / Surface-Snapshot Tests

**Concept:** Enumerate every public symbol (classes, functions, dataclass fields, type signatures) and commit the list as a text fixture. On every PR, re-enumerate and diff. A mismatch fails CI.

**Tools:**

| Tool | What it checks | Maturity |
|------|---------------|---------|
| `griffe check` | Structural breaking changes (removed objects, changed parameter kinds/defaults) against a git tag or PyPI release | Active, production-ready ([griffe PyPI](https://pypi.org/project/griffe/)) |
| `mypy stubtest` | Stubs (`.pyi`) match the live runtime — catches stub-vs-impl drift | Shipped with mypy; stable ([mypy stubtest docs](https://mypy.readthedocs.io/en/stable/stubtest.html)) |
| `importlib` introspection (custom) | Enumerate `__all__` + dataclass `__dataclass_fields__`, write to a `.txt` golden file, diff in test | Zero external deps; fully custom |
| `syrupy` / `inline-snapshot` | General-purpose pytest snapshot assertions; can snap any serializable object | Active ([syrupy TIL](https://til.simonwillison.net/pytest/syrupy)) |

---

### A3. Recommended Pattern: griffe in CI (primary) + importlib golden file (secondary)

**Step 1 — griffe check in every PR (prevents regressions)**

```yaml
# .github/workflows/api-check.yml
name: API Breaking-Change Check
on: [pull_request]

jobs:
  api-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # full history needed to compare against tags
      - uses: astral-sh/setup-uv@v6
      - run: uvx griffe check --search src --format github vnfin
```

`griffe check` ([Griffe checking docs](https://mkdocstrings.github.io/griffe/guide/users/checking/)) compares HEAD against the latest git tag and exits non-zero on any of 13+ detected breakage categories:
- Object removed, parameter removed/made-required, parameter kind changed (positional → keyword-only), attribute value changed, class base removed, etc.

**Pros:** Zero config beyond `__all__` hygiene; GitHub annotations show exactly which line is broken; covers the most dangerous accidental changes.

**Cons:** Does not detect return-type changes (currently unsupported); requires at least one git tag to compare against.

**Step 2 — importlib golden-file test (catches symbol set changes)**

```python
# tests/test_public_api_surface.py
import importlib, inspect, json, pathlib
import vnfin

GOLDEN = pathlib.Path("tests/fixtures/public_api_surface.json")

def _enumerate_surface(pkg):
    surface = {}
    for name in pkg.__all__:
        obj = getattr(pkg, name)
        if inspect.isclass(obj):
            fields = list(getattr(obj, "__dataclass_fields__", {}).keys())
            methods = [
                m for m in dir(obj)
                if not m.startswith("_") and callable(getattr(obj, m))
            ]
            surface[name] = {"kind": "class", "fields": fields, "methods": sorted(methods)}
        elif callable(obj):
            sig = str(inspect.signature(obj))
            surface[name] = {"kind": "callable", "signature": sig}
        else:
            surface[name] = {"kind": "attribute"}
    return surface

def test_public_surface_unchanged():
    current = _enumerate_surface(vnfin)
    if not GOLDEN.exists():
        GOLDEN.write_text(json.dumps(current, indent=2))
        return  # first run: create baseline
    baseline = json.loads(GOLDEN.read_text())
    assert current == baseline, (
        "Public API surface changed. "
        "If intentional, update tests/fixtures/public_api_surface.json and bump the version."
    )
```

Commit `tests/fixtures/public_api_surface.json`. Any accidental rename, field addition/removal, or method deletion fails the test. Intentional changes require updating the golden file — which is visible in the PR diff.

**Pros:** Catches symbol-set changes griffe misses (e.g., a class moving from public to private); requires no extra tools; the golden file is human-readable.
**Cons:** Brittle for large frequent changes if maintainers are sloppy about updating it; needs discipline.

**Step 3 — mypy stubtest (optional, high-value if you ship `.pyi` stubs)**

```bash
python -m mypy.stubtest vnfin --allowlist tests/stubtest_allowlist.txt
```

Checks that your published stubs match the actual runtime signatures. Critical if you ship typed stubs. The `--allowlist` suppresses known false positives ([mypy stubtest docs](https://mypy.readthedocs.io/en/stable/stubtest.html)).

---

### A4. SemVer + Deprecation-Window Conventions

**Standard for Python libraries** ([Python Packaging — Versioning](https://packaging.python.org/en/latest/discussions/versioning/), [pyOpenSci package guide](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-versions.html)):

| Change type | Version bump | Minimum deprecation window |
|-------------|-------------|---------------------------|
| Backward-compatible new feature | MINOR (1.x.0) | None required |
| Backward-compatible bug fix | PATCH (1.0.x) | None required |
| Breaking public API change | MAJOR (2.0.0) | 1–2 MINOR releases with `DeprecationWarning` |
| Experimental/unstable feature | Use `0.x.y` or document as `beta` | None (0.x is exempt) |

**Griffe-guided deprecation workflow** ([griffe checking](https://mkdocstrings.github.io/griffe/guide/users/checking/)):

When griffe detects a pending break (e.g., removing a parameter), instead of removing it immediately:

```python
import warnings

def get_price(ticker: str, exchange: str = None, *, market: str = None):
    if exchange is not None:
        warnings.warn(
            "The 'exchange' parameter is deprecated; use 'market' instead. "
            "It will be removed in v2.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        market = exchange
    ...
```

Keep the old parameter for at least one MINOR release cycle. Document the removal in `CHANGELOG.md` with an estimated version. Announce in release notes.

**Recommended minimum window for a data library:** 60–90 days or 2 MINOR releases (whichever is longer), aligning with industry guidance ([Deprecations via warnings — HN discussion](https://news.ycombinator.com/item?id=46195679)).

---

## Part B — Monitoring Upstream Endpoint Stability

### Problem statement

Third-party financial HTTP APIs silently:
- Change JSON key names or nesting depth
- Change units (e.g., price in VND → thousands VND)
- Drop fields without notice
- Return HTTP 200 with different auth-required error shapes
- Go offline or switch base URLs

Your unit tests mock the HTTP layer and will never catch this. You need a separate, live canary that runs on a schedule and screams when upstream changes shape or breaks.

---

### B1. Concept: Contract Testing vs Synthetic Canary Monitoring

| Approach | What it is | When to use |
|----------|-----------|-------------|
| **Contract testing** | Assert a static JSON schema (Pydantic model or jsonschema dict) against the response; fail if it drifts | Best when upstream provides OpenAPI/spec; catches structural drift |
| **Synthetic canary** | A scheduled live job that calls the real endpoint with real credentials, validates the response, and reports pass/fail | Best for undocumented or spec-less APIs (common in VN finance); catches outages, auth failures, and silent shape changes |
| **Golden key-set diffing** | Store the expected set of top-level keys (or a full schema hash) as a committed fixture; compare each canary run against it | Lightweight middle ground; easy to implement, catches key removals/additions |

For a VN financial data library hitting undocumented or minimally-documented APIs, the **synthetic canary with golden key-set diffing** is the most practical approach.

---

### B2. Recommended Pattern: pytest-based Canary, Env-Gated, Scheduled in CI

**Core philosophy (from CI best practices):**

- Unit tests (mocked HTTP via `responses` or `pytest-httpserver`): run on every commit, fast, deterministic.
- Canary/live tests: run on a schedule (nightly or weekly), skipped in normal CI unless explicitly opted in.

**Implementation:**

```python
# tests/canary/conftest.py
import os
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "canary: marks tests that hit live upstream endpoints (deselected by default)"
    )

def pytest_collection_modifyitems(config, items):
    if not os.getenv("RUN_CANARY_TESTS"):
        skip_canary = pytest.mark.skip(reason="Set RUN_CANARY_TESTS=1 to run live canary tests")
        for item in items:
            if "canary" in item.keywords:
                item.add_marker(skip_canary)
```

```python
# tests/canary/test_upstream_price_endpoint.py
"""
Canary tests: validate live upstream endpoint shape.
These tests call real APIs with real network. Never run in normal CI.
Run via: RUN_CANARY_TESTS=1 pytest tests/canary/ -v
Or via the scheduled GitHub Actions job: .github/workflows/canary.yml
"""
import json, pathlib, pytest, httpx

GOLDEN_SCHEMA = pathlib.Path("tests/canary/fixtures/price_response_keys.json")

@pytest.mark.canary
def test_price_endpoint_reachable_and_schema_stable():
    """Hit the live endpoint; validate HTTP 200 + key-set matches golden fixture."""
    resp = httpx.get("https://upstream-api.example.com/api/v1/price?ticker=VCB", timeout=10)
    assert resp.status_code == 200, f"Upstream returned {resp.status_code}"

    data = resp.json()
    current_keys = sorted(data.keys())  # or recurse for nested schemas

    if not GOLDEN_SCHEMA.exists():
        GOLDEN_SCHEMA.write_text(json.dumps(current_keys, indent=2))
        pytest.skip("Golden fixture created on first run; commit it.")

    baseline_keys = json.loads(GOLDEN_SCHEMA.read_text())
    added = set(current_keys) - set(baseline_keys)
    removed = set(baseline_keys) - set(current_keys)

    assert not removed, f"Upstream REMOVED keys: {removed}. Check for breaking change."
    if added:
        pytest.warns(UserWarning, match="Upstream ADDED keys")  # non-fatal: new keys are OK
```

**Pydantic-based approach (stronger, when you maintain response models):**

```python
# src/vnfin/_models/price.py
from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal

class PriceBarRaw(BaseModel):
    """Strict model for upstream JSON shape. Any missing required field = ValidationError."""
    ticker: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    date: str
    model_config = {"extra": "allow"}  # 'ignore' to be lenient, 'forbid' to be strict

# In canary test:
@pytest.mark.canary
def test_price_model_validates():
    resp = httpx.get("https://upstream-api.example.com/api/v1/price?ticker=VCB", timeout=10)
    data = resp.json()
    # ValidationError here means upstream changed shape
    bar = PriceBarRaw.model_validate(data)
    assert bar.ticker == "VCB"
```

**jsonschema approach (useful when you want a committed JSON schema file):**

```python
import jsonschema, json, pathlib

SCHEMA_FILE = pathlib.Path("tests/canary/fixtures/price_schema.json")

@pytest.mark.canary
def test_price_response_matches_schema():
    resp = httpx.get("...", timeout=10)
    schema = json.loads(SCHEMA_FILE.read_text())
    jsonschema.validate(instance=resp.json(), schema=schema)
    # Raises jsonschema.ValidationError on drift
```

Commit the schema file. Update it intentionally when the upstream changes shape knowingly.

---

### B3. Scheduled GitHub Actions Canary Job

```yaml
# .github/workflows/canary.yml
name: Upstream Canary Monitor

on:
  schedule:
    - cron: "0 1 * * *"   # 01:00 UTC (08:00 Vietnam time) daily
  workflow_dispatch:        # allow manual trigger

jobs:
  canary:
    runs-on: ubuntu-latest
    env:
      RUN_CANARY_TESTS: "1"
      # Secrets injected from GitHub repo secrets:
      UPSTREAM_API_KEY: ${{ secrets.UPSTREAM_API_KEY }}

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --group dev
      - name: Run canary tests
        run: |
          uv run pytest tests/canary/ -v --tb=short \
            --junit-xml=reports/canary-results.xml
        continue-on-error: false   # fail the job if any endpoint breaks

      - name: Upload canary report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: canary-report-${{ github.run_id }}
          path: reports/canary-results.xml

      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v2
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            { "text": "Upstream canary FAILED — check GitHub Actions for schema drift or outage." }
```

**Key design decisions:**
- `continue-on-error: false` — the canary job fails the workflow if upstream breaks.
- Secrets (`UPSTREAM_API_KEY`) are injected via GitHub Secrets — never committed.
- The `RUN_CANARY_TESTS=1` env var gates the canary tests; the normal `pytest` run (no env var) skips them entirely.
- `workflow_dispatch` allows triggering manually when you suspect a change.

---

### B4. Keeping Canary OUT of Normal Unit CI

**pytest.ini / pyproject.toml configuration:**

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "-m 'not canary'"    # default: never run canary tests
markers = [
    "canary: hits live upstream endpoints; requires RUN_CANARY_TESTS=1",
]
testpaths = ["tests"]
```

This ensures `pytest` (or `uv run pytest`) in the standard unit-test job never touches canary tests. The canary job explicitly overrides with `RUN_CANARY_TESTS=1` and targets `tests/canary/`.

---

### B5. Status Page / Reporting

For lightweight OSS projects without a dedicated uptime service:

**Option 1 — GitHub Actions badge:** The canary workflow status badge in `README.md` serves as a live status indicator.

```markdown
![Upstream Canary](https://github.com/org/vnfin/actions/workflows/canary.yml/badge.svg)
```

**Option 2 — Committed JSON report:** Write a `docs/upstream-status.json` from the canary job and commit it to a `status` branch. A static site or GitHub Pages page renders it.

**Option 3 — Gatus / Upptime (OSS uptime monitors):** [Gatus](https://github.com/TwiN/gatus) or [Upptime](https://github.com/upptime/upptime) can run a minimal uptime page from a GitHub repo at zero cost. They support custom HTTP endpoint checks with response body assertions.

---

## Summary of Recommended Toolchain

| Layer | Tool | Notes |
|-------|------|-------|
| Define public surface | `__all__` + `_`-prefix convention | Required before any tooling works |
| Break-detection in PR | `griffe check --format github` | Primary guard; CI fails on break |
| Symbol-set snapshot | `importlib` + golden JSON file | Secondary; zero deps |
| Stub consistency | `mypy stubtest` | Add when/if `.pyi` stubs ship |
| Deprecation | `DeprecationWarning` + 60-90 day window | MAJOR bump for removals |
| Upstream schema guard | Pydantic `model_validate()` on canary response | Preferred if models exist |
| Upstream key-set diff | Golden JSON key-set committed to repo | Lightweight fallback |
| Canary gating | `pytest -m 'not canary'` default; `RUN_CANARY_TESTS=1` to enable | Hard separation from unit suite |
| Scheduled canary | GitHub Actions `schedule: cron` + `workflow_dispatch` | Daily at 08:00 Vietnam time |
| Canary status page | GitHub Actions badge in README | Zero-cost for OSS |

---

## References

- [Griffe — Checking for Breaking Changes](https://mkdocstrings.github.io/griffe/guide/users/checking/)
- [Griffe — Public API Recommendations](https://mkdocstrings.github.io/griffe/guide/users/recommendations/public-apis/)
- [griffe on PyPI](https://pypi.org/project/griffe/)
- [mypy stubtest documentation](https://mypy.readthedocs.io/en/stable/stubtest.html)
- [Python Packaging — Versioning](https://packaging.python.org/en/latest/discussions/versioning/)
- [pyOpenSci — Package Versions Guide](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-versions.html)
- [Deprecations via warnings — HN thread 2025](https://news.ycombinator.com/item?id=46195679)
- [DEV — Snapshot Testing Is the Secret Weapon for API Stability](https://dev.to/kreya/why-snapshot-testing-is-the-secret-weapon-for-api-stability-4797)
- [Automated Contract Testing: Detect API Drift Before Production, Apr 2026](https://medium.com/@instatunnel/automated-contract-testing-how-to-detect-api-drift-before-it-reaches-production-6c2a77baa2a3)
- [API Schema Drift Detection Tools Compared 2026](https://dev.to/flarecanary/api-schema-drift-detection-tools-compared-2026-1ib4)
- [Pydantic JSON Schema docs](https://docs.pydantic.dev/latest/api/json_schema/)
- [How to Keep Unit and Integration Tests Separate — pythontutorials.net](https://www.pythontutorials.net/blog/how-to-keep-unit-tests-and-integrations-tests-separate-in-pytest/)
- [Syrupy snapshot testing — Simon Willison TIL](https://til.simonwillison.net/pytest/syrupy)
