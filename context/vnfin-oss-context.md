# vnfin-oss first-boot context

Created: 2026-06-17
Owner: Boss/SonPH
Workspace: ~/dev/vnfin-oss
Agent/session/role: vnfin-oss

## Boss directive

Boss has already published the prior finkit project, but research showed it overlaps too much with the Python library named VNStock / vnstock. Boss now wants a fresh, clean-room rewrite from scratch as a similar open-source library, while avoiding VNStock throughout all research and implementation.

## Mission

Rewrite a new open-source Python financial-data library from scratch, avoiding VNStock, for:

1. long-term investors,
2. macroeconomic analysts,
3. developers who want to build financial-advisor tools.

The library should prioritize stable, lawful, well-documented Python APIs over short-term trading automation. It should be suitable for AI agents and humans, with clean schemas, type-safe behavior, tests, docs, and clear licensing.

## Absolute VNStock blacklist / clean-room rule

Throughout all research, design, implementation, docs, examples, tests, and API naming:

- Treat VNStock / vnstock as BLACKLISTED.
- Do not search for VNStock-specific materials.
- Do not browse, read, cite, clone, install, import, or depend on VNStock.
- Do not use VNStock GitHub repos, websites, docs, PyPI pages, agent guides, notebooks, snippets, examples, API names, endpoint maps, schemas, or tests as sources.
- If search results contain VNStock/Vnstock/vnstocks.com/vnstock-hq/thinh-vu/vnstock/vnstock-agent/etc., skip them and search again with exclusions.
- Use negative search terms where appropriate: `-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq`.
- Do not compare against VNStock source behavior. Do not port from VNStock. Do not use VNStock for validation.
- If a task seems to require VNStock knowledge, stop and find alternative primary sources, or ask Boss.

Reason: Boss is concerned about overlap/copyright/licensing issues and wants a clean-room OSS project.

## Allowed research directions

Use primary and legally safe sources only, such as:

- Official public data provider docs/APIs and terms of use.
- Official regulator/exchange/government/macroeconomic data portals and documentation.
- Licensed open-data sources with clear redistribution/use terms.
- General Python packaging/testing/docs best practices.
- Financial-domain literature and public standards that are not VNStock-derived.

For any web/API data source, record provenance, license/terms, rate limits, authentication requirements, and whether redistribution is allowed.

## First tasks

1. Read CLAUDE.md/AGENTS.md and this context file.
2. Write `docs/plan.md` with a clean-room research and rewrite plan.
3. Create a blacklist checklist in `docs/vnstock-blacklist.md` and use it before every research task.
4. Draft the target product/API scope in `docs/mission.md`.
5. Stand by for Boss; do not start copying or reusing any prior finkit code until Boss explicitly asks for migration strategy.
