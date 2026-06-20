# Explain source coverage (diagnostics)

`vnfin.diagnostics` is a small **offline** helper that explains *source coverage* and
source-limit gaps for allocation workflows — so you can understand a coverage gap or a
single-source leg **without** firing a large, doomed network fan-out.

It is **metadata / preflight only**: it makes no network call, never fabricates missing
rows or index weights, and is **not** a live health monitor (for live checks use
`scripts/healthcheck.py` / `vnfin._health`).

## List known source capabilities

```python
import vnfin

for cap in vnfin.diagnostics.source_capabilities():
    print(cap.domain, cap.source, cap.is_default, cap.coverage_start, cap.limitations)
```

Each record is an immutable `SourceCapability` (domain, endpoint, source, instruments,
granularity, coverage bounds, default/opt-in/single-source flags, limitations, a
suggested action). Coverage bounds are conservative *known lower bounds*, not promises.

## Preflight a world-gold history window

```python
from datetime import date
import vnfin

d = vnfin.diagnostics.explain_world_gold_history(date(2024, 1, 1), date(2024, 12, 31))
print(d.status)            # "coverage_gap" | "partial_coverage" | "window_too_wide" | "ok"
print(d.notes)
print(d.suggested_actions)
```

A window entirely before the default source's known coverage start is `coverage_gap`
(the live `vnfin.gold.world(...).get_history(...)` call now also **fails fast** with
`EmptyData` instead of issuing one doomed request per day); a window wider than the
source's max range (`_MAX_DAYS`) is `window_too_wide` (the live call raises `InvalidData`;
the diagnostic suggests chunking) — when both apply, both blockers are reported; a window straddling the
start is `partial_coverage`; an otherwise-covered window is `ok`.

## Preflight index constituents

```python
import vnfin

d = vnfin.diagnostics.explain_index_constituents("vn30")
print(d.request["index"])  # "VN30" — canonicalized like the live call
print(d.status)            # "single_source"
print(d.notes)             # membership only, no weights, no clean no-auth fallback
```

The selector is validated/canonicalized with the same identifier contract as the live
call, so a malformed selector raises before any work.

> See also: [Handle errors and failover](errors.md), and the internal
> [provider-contracts architecture](../architecture/provider-contracts.md).
