# #181 — additive `Fund.nav_as_of` (per-fund NAV freshness date)

**Worktree:** `/home/hungson175/dev/vnfin-oss-wt-181` (branch `issue-181-fund-nav-asof`, off master). Work ONLY in this worktree. TDD: failing tests FIRST, then the minimum field+parse, then refactor on green. Scope is DELIBERATELY SMALL — one additive field. Do NOT add a warning, a token, or a staleness diagnostic (that was SPLIT into a deferred follow-up).

## What & why (probe-confirmed, reviewer-approved)
The Fmarket filter row already carries a per-fund NAV date — nested at **`row["extra"]["lastNAVDate"]`**, an epoch-**millisecond** value at VN-local midnight (e.g. `1781802000000` → a VN calendar date). It pairs with `extra.lastNAV`/`extra.currentNAV`, which equal the top-level `nav` we already parse. Today `Fund.nav` has no as-of date — callers can't tell if a NAV is fresh. Add the provider's OWN date as an additive optional field; never fabricate.

**Use ONLY `extra.lastNAVDate`.** IGNORE the distractors: top-level `row["updateAt"]` (fund-record edit time; varies 2024–2026) and `row["productNavChange"]["updateAt"]` (nav-stats compute time; ~today for all funds). Neither is the NAV date.

## The change (additive, never-fabricated)
1. **`vnfin/funds/models.py`** — add a trailing optional field to the frozen `Fund` dataclass (after `currency: str = "VND"`):
   ```python
   nav_as_of: Optional[date] = None
   ```
   `date` and `Optional` are already imported (models.py:10-11). Extend the `Fund` docstring: "`nav_as_of` is the provider's own NAV date (the date `nav` is as-of), or `None` when the provider omits it — never fabricated."

2. **`vnfin/funds/fmarket.py`** — in `_parse_fund(row)`, parse the date and pass it to the `Fund(...)` constructor. Reuse the EXISTING epoch-ms converter `_parse_update_at` (fmarket.py:105-125) — do NOT invent a new converter. It returns a tz-aware **UTC** datetime (or None). Convert to the VN calendar date:
   ```python
   extra = row.get("extra")
   nav_as_of = None
   if isinstance(extra, dict):
       dt = _parse_update_at(extra.get("lastNAVDate"))  # epoch-ms -> tz-aware UTC or None
       if dt is not None:
           nav_as_of = dt.astimezone(VN_TZ).date()
   ```
   Then add `nav_as_of=nav_as_of` to the `Fund(...)` call. Find `VN_TZ` (grep `VN_TZ =` across `vnfin/` — it is the canonical VN tzinfo, e.g. in a timeutils module) and import it into fmarket.py if not already imported. `_parse_update_at` already rejects bool / non-positive / non-integral-float / out-of-range epoch → returns None, so absent/null/garbage/non-positive `lastNAVDate` → `nav_as_of = None` with NO raise (a missing nav date must never blow up the whole list).

## Must-hold invariants
- Never fabricate: absent `extra` / absent `lastNAVDate` / null / non-positive / garbage → `nav_as_of is None`, never `now()`, never a raise.
- Use only `extra.lastNAVDate`; never the two distractor `updateAt` fields.
- VN-tz boundary: an epoch at **17:00 UTC maps to the NEXT VN calendar day** (00:00 +07). Pin this in a test — proves the conversion uses VN tz, not naive UTC.
- The value pairs with the parsed `nav` (same fund row).
- Frozen-dataclass additive: existing `Fund(...)` callers/tests that don't pass `nav_as_of` keep working (default `None`).

## Public-API snapshot — FROZEN, do NOT regen
A new trailing optional field on `Fund` is ADDITIVE. Run `tests/test_public_api_surface.py`: it MUST be green (additive classification is allowed + printed). Do **NOT** edit/regen `tests/snapshots/public_api_v0_2_0.json`.

## #180 guard — UNCHANGED, do NOT touch
This change adds NO warning token (the staleness warning was SPLIT to a follow-up). Do NOT touch `tests/test_docs_contract.py` or the SKILL/docs token tables.

## TDD test matrix (synthetic fixtures ONLY — no real provider rows)
Find the existing Fmarket `list_funds` tests (grep for `list_funds`, `_parse_fund`, or the synthetic filter-payload helper) and add these in the same file, matching the existing synthetic-row style (a minimal valid fund row + an injected `http_get`/`_post` stub). Write ALL to FAIL FIRST (the field doesn't exist yet), then implement:
1. **Happy path:** a row with `extra.lastNAVDate` epoch-ms (at VN midnight) → `fund.nav_as_of == date(Y, M, D)` (the VN calendar date), and it co-exists with the existing parsed `nav`.
2. **VN-tz boundary:** `lastNAVDate` at exactly 17:00 UTC → `nav_as_of` is the NEXT VN calendar day (proves VN-tz, not naive UTC). Add a companion at 16:59:59 UTC → previous VN day, to bracket the boundary.
3. **Absent `extra`** (no `extra` key) → `nav_as_of is None`, no raise.
4. **Absent `lastNAVDate`** (extra present, key missing) → `None`.
5. **Null / non-positive (0 or negative) / garbage (string, NaN float, bool) `lastNAVDate`** → `None`, no raise.
6. **Back-compat:** an existing-style row without the new handling still parses; `Fund(...)` constructed without `nav_as_of` defaults to `None`.

## Scope guard (do NOT touch)
ONLY: `vnfin/funds/models.py` (the field), `vnfin/funds/fmarket.py` (parse), and the funds test file (add tests). Do NOT touch `vnfin/sources/udf.py`, `vnfin/equities/*`, `vnfin/indices/*`, `tests/test_docs_contract.py`, the snapshot JSON, SKILL/docs token tables. CHANGELOG: add a one-line `Added` entry for `Fund.nav_as_of` under the unreleased section.

## Done = all green in the worktree
Run the FULL suite from the worktree root: `python -m pytest -q`. All pass (incl. the new tests). Report: files changed, the test names added, the final `N passed` line, and confirmation the surface test is green WITHOUT regenerating the snapshot. Do NOT commit, push, close issues, or message anyone — return a summary to the orchestrator.
