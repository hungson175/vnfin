# How to run live tests

Default tests are offline and deterministic:

```bash
pytest
```

Live tests perform real network checks against providers and are intentionally outside default test
collection. Run them only when you want to verify current upstream behavior:

```bash
VNFIN_LIVE=1 pytest live_tests/
```

Running `live_tests/` without `VNFIN_LIVE=1` fails clearly instead of skipping. This keeps CI and
local default runs at zero skipped tests while preserving real smoke coverage.

Some upstreams may block datacenter IP ranges. Manual diagnostics live in scripts such as
`scripts/diagnostics_live.py`; those scripts are not collected by pytest.
