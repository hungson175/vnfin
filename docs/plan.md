# vnfin-oss Plan

## Current goal

Create a clean-room OSS Python financial-data library for long-term investors, macroeconomic analysts, and developers building financial-advisor tools, while avoiding VNStock/vnstock entirely.

## Assumptions

- The prior finkit project is published but may overlap too much with VNStock research.
- This project starts from scratch unless Boss approves a specific clean-room migration strategy.
- The first phase is research and source/legal scoping, not coding.

## Initial phases

1. **Clean-room charter** — define scope, blacklist, source policy, and API principles.
2. **Source discovery** — find official/license-clear data sources without VNStock results.
3. **Data contracts** — design schemas for prices, fundamentals, macro, company profile, events, and source provenance.
4. **API design** — create a minimal Python-first API for long-term analysis and advisor apps.
5. **Implementation** — build only from approved primary sources with tests and docs.
6. **Release readiness** — packaging, license, README, examples, CI, source terms audit.

## Next action

Wait for Boss's first task. If asked to research, explicitly apply the VNStock blacklist before searching.

## Review protocol (builder ↔ reviewer)

Cross-session handoffs use `tm-send` with **exact session targeting** and the global message prefix. Full rules live in `CLAUDE.md` (§ tm-send routing):

- Builder → reviewer: `tm-send -s '=vnfin-oss-reviewer' vnfin-oss-reviewer "vnfin-oss/vnfin-oss [HH:MM +07]: … - reply via tm-send"`
- Reviewer → builder: `tm-send -s '=vnfin-oss' vnfin-oss "vnfin-oss-reviewer/vnfin-oss-reviewer [HH:MM +07]: … - reply via tm-send"`

Never use bare `tm-send vnfin-oss-reviewer "…"` from the builder session — it falls back to the builder's own pane.

## Dev artifact policy

- **`uv.lock`**: not tracked (local `uv sync` output; listed in `.gitignore`).
- **`coverage_report.md`**: not tracked (generated snapshot; listed in `.gitignore`).
