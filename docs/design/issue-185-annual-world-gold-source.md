# Design note — #185 annual world-gold source (unblocks vf-advisor's live gold chart)

**Status:** **DESIGN APPROVED** by reviewer LEAD gate 2026-06-21 04:53 — D1–D6 all ratified; gate notes
**N1** (defensive magnitude guard) + **N2** (SourceError-subclass fail-loud/fail-over discipline) folded in
below. **CODE is deferred behind #186** (the core VN-Index blocker) per the reviewer's confirmed sequencing.
**Issue:** #185 (follow-up to closed #178). **Reviewer spec:** `reviews/spec-202606210205-issue185-annual-world-gold-source.md`.
**Process:** design note → reviewer LEAD gate ✅ → (after #186) TDD (red-first) → Codex×2 (it changes the #178 synthesis internals) → on APPROVE push + close #185 → ping vf-advisor.

---

## 1. Problem & goal

`world_reference_history_vnd` (`vnfin/gold/world_reference.py:177-232`) builds the annual VND/lượng
world-gold reference as `annual-avg(gold USD/oz) × annual-avg(USD/VND) × 37.5/31.1035`. Its **world-gold
(XAU/USD) leg** is fetched daily via `CurrencyApiGoldSource → StooqGoldSource` and then averaged to annual.
**From a datacenter host that leg is unfetchable:** CurrencyApi is sparse (~28% of trading days) + ~1100-day
capped, and Stooq is anti-bot-blocked. The 50% coverage gate (`FailoverGoldClient`) correctly rejects the
sparse data and fails safe — so the synthesis can't run server-side, and vf-advisor's live gold chart is
stuck on `sample:true`. **Do NOT relax the coverage gate** (it is working as designed).

Since #178's OUTPUT is **annual**, the fix is an **annual** world-gold source that works server-side.

---

## 2. Recommended source — World Bank CMO "Pink Sheet" annual gold (verified clean + server-reachable)

> **CODE-TIME ACQUISITION FINDINGS (2026-06-21, supersede the design assumptions below):**
> A primary-source agent resolved + downloaded the real current vintage and verified its contents.
> Two material corrections, folded into D2/D4/§6:
> 1. **Full vintage hash is the 32-char `74e8be41ceb20fa0da750cda2f6b9e4e`** — the truncated `74e8be41`
>    from earlier notes **404s**. Confirmed current URL (HTTP 200, 3,177,955-byte xlsx, `PK\x03\x04`,
>    43 zip members, `testzip` clean):
>    `https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Annual.xlsx`
> 2. **The gold header is SPLIT across two cells** (no single combined string): name cell `Gold`
>    (sharedString idx 26) at row 7 / col 67, and units cell `($/troy oz)` (idx 186) directly below at
>    row 8 / same col 67. So D2's "match by header text" must match `Gold` on the name row **and**
>    `($/troy oz)` on the units row of the **same column**, not one cell. Sheet `Annual Prices (Nominal)`
>    → `r:id=rId2` → `xl/worksheets/sheet2.xml`. Descriptor (idx 310) confirms the LBMA basis: "Gold,
>    spot average of daily rates, from June 2025; previously (UK), 99.5% fine, London afternoon fixing…".
> Contents verified: year in col 0; **1960–2025, 66 points, no gaps**; 1960=35.27, 2023=1942.67,
> 2024=2387.70, 2025=3441.51. Fixture on disk (to be committed): `tests/fixtures/cmo/CMO-Historical-Data-Annual.xlsx`,
> SHA256 `9fbcb348f40ecdb02eb1bcf858a2965383d2aaf3445e8920dd7d60ae7b04af51`. No prior-vintage fallback
> located (the only known fragment was this current vintage, truncated) → `_CMO_ANNUAL_URLS` is a
> single-element ordered list for v1; backfill a prior vintage when WB next rotates the hash. Reachability:
> clean GET from the datacenter host, no anti-bot; **HEAD reports `size=0`** (no Content-Length on HEAD) so
> the fetcher must GET + check `PK\x03\x04` magic, not gate on HEAD length (D3's `_request_bytes` already GETs).

- **Distribution:** World Bank Commodity Markets "Pink Sheet", historical data, **annual `.xlsx`**.
- **URL (vintage-coded — see §4):**
  `https://thedocs.worldbank.org/en/doc/<vintage-hash>-0050012026/related/CMO-Historical-Data-Annual.xlsx`
  (the `<vintage-hash>` segment is a per-release digest that shifts between vintages; the concrete
  current URL is resolved above. The #185 code makes a deliberate secret-scanner decision for the
  pinned `_CMO_ANNUAL_URLS` list at its gate — a public CC-BY data URL, not a secret.)
- **Series:** sheet `Annual Prices (Nominal)` (→ `xl/worksheets/sheet2.xml`); **match the gold column BY
  HEADER TEXT (split `Gold` name row + `($/troy oz)` units row, same column), NOT a fixed column index**
  (position shifts between vintages). Year in column 0.
- **Coverage:** 1960–2025 annual, **no gaps** (66 points; e.g. 1960=35.27, 2024=2387.70, 2025=3441.51).
- **License:** keyless, **CC-BY 4.0** (clean for runtime fetch + commercial use, attribution only).
- **Reachability:** verified `HTTP 200` from this datacenter on 2026-06-21 (no anti-bot, unlike Stooq/
  currency-api). Same provider (World Bank) + same 1960 start as the FX leg `PA.NUS.FCRF`.
- **Basis match (why it's a lossless drop-in):** CMO annual gold IS "spot average of daily rates"
  (LBMA-sourced) — i.e. already an **annual average of daily spot**. So `CMO-annual-gold × WB-annual-FX ×
  factor` preserves the #178 `annual-avg × annual-avg` basis EXACTLY; the daily→annual averaging step is
  simply replaced by reading CMO's annual value.
- **NOT in the WB indicators JSON API** (only reserve/holdings indicators are) → it is a separate **xlsx**
  distribution (this is what forces the binary-fetch + xlsx-parse decisions below).

Alternatives if CMO snags: FRED `GOLDPMGBD228NLBM` (BYOK only — keyless `fredgraph.csv` is bot-blocked from
datacenter IPs), LBMA direct (license-gated; CMO already redistributes LBMA's number under CC-BY). Prefer CMO.

---

## 3. Locked design decisions (recommendations for the LEAD gate to ratify)

### D1 — New standalone source `WorldBankCmoGoldSource(HttpDataSource)`
- **Inherits `HttpDataSource`** (for retry/timeout/IPv4/UA + the new `_request_bytes`), **NOT `GoldSource`** —
  mirroring `WorldBankFXHistorySource` (`vnfin/fx/history_worldbank.py`), which is a standalone *history*
  source, not a spot-capable adapter. CMO is annual-history-only; making it a `GoldSource` would force a
  bogus `get_quotes` spot contract and (worse) tempt putting it in `FailoverGoldClient`, whose daily
  coverage gate would reject an annual series (see D5). *Alternative:* inherit `GoldSource` with
  `provides_spot=False` + `get_quotes` raising — rejected as more coupling for no gain.
- **API:** `get_history(start: date, end: date) -> GoldHistory`. Validates bounds (fail-closed, before any
  network call). Returns `GoldHistory(product="XAU", unit="USD/oz", value_unit="USD/oz", currency="USD",
  source="worldbank_cmo_gold", bars=…, fetched_at_utc=…)` with **one `GoldBar(date=date(year,1,1),
  price=usd_per_oz)` per calendar year** in the requested `[start.year, end.year]` span (Jan-1 stamp matches
  the FX annual convention and the synthesis output).
- **Data-integrity guards (mirror the strictest sibling — [[new-source-must-mirror-sibling-data-integrity-guards]]):**
  reject non-finite / `<= 0` prices → `InvalidData`; reject a non-monotonic / duplicate year → `InvalidData`.
- **GATE NOTE N1 (reviewer APPROVE 04:53 — defense against a silent stdlib-OOXML column-misparse):** ALSO
  reject a parsed value outside a **plausible gold band (~20 .. 10000 USD/oz)** → `InvalidData`. The
  header-text match (D2) is the primary defense; this magnitude guard is the backstop so a mis-resolved
  shared-string index / wrong column can never feed a wrong gold number into the synthesis. (Band is
  generous — 1960 gold ≈ 35, 2025 ≈ 3441 — it only catches gross misparses, not legitimate values.)

### D2 — xlsx parse: **stdlib `zipfile` + `xml.etree`** (no new dependency)
- vnfin's only core dep is `httpx` (`pyproject.toml`); `pandas` is an *optional* extra and `openpyxl` is
  absent. An xlsx is a zip of OOXML. A **scoped** stdlib parser reads exactly what CMO needs:
  1. `xl/workbook.xml` → map sheet name `Annual Prices (Nominal)` → its `r:id` (real vintage: `rId2`);
  2. `xl/_rels/workbook.xml.rels` → resolve that `r:id` → `xl/worksheets/sheetN.xml` (real vintage: `sheet2.xml`);
  3. `xl/sharedStrings.xml` → the shared-string table (header/text cells are indices into it);
  4. walk the sheet rows: locate the gold column by its **split** header — the column whose name-row cell
     is `Gold` (exact, trimmed) **and** whose units-row cell directly below is `($/troy oz)` — then read
     `(year, value)` from the year column (col 0) + the matched gold column. Resolve column position from
     the header match, never a hard-coded index (the real file has gold at col 67, but that shifts).
     A data row is one whose col-0 cell parses as a 4-digit year; rows above the data block (title/metadata,
     the two header rows) are skipped. Numeric cells may be stored as raw numbers (not shared strings).
- **Why stdlib over the optional-extra (reviewer's option b):** the synthesis is a **core accessor** whose
  whole purpose here is to **unblock a live product server-side**. Gating it behind `vnfin[gold-history]`→
  openpyxl means the chart stays broken on any install that didn't add the extra — fragile for the exact
  goal. Stdlib keeps core lean (reviewer's lean-core preference) **and** works out-of-the-box everywhere.
  Cost: ~120 LOC of bounded OOXML parsing, fully testable offline (the test builds a minimal valid xlsx with
  stdlib `zipfile` — see §6). *Alternative (b):* optional extra → openpyxl, source raises a clear
  `InvalidData`/import-error if missing. **My pick: stdlib (a).** ⚠️ This is the biggest call — explicitly
  for the LEAD gate to confirm or flip to (b). **GATE: RATIFIED (reviewer 04:53)** — stdlib, NO new dep; the
  Codex×2 will hard-scrutinize the parser and the test plan includes a **real-CMO-vintage parse test**
  (parse an actual committed CMO xlsx fixture, assert known year values e.g. 2024≈2387.70, 2025≈3441.51).

### D3 — Binary transport: add `_request_bytes` to `HttpDataSource`
- xlsx is **binary**; the existing `_request_text` returns `str` and `_default_http_get` returns `resp.text`.
  `_fetch_with_retry` is already type-agnostic (it returns whatever `http_get` returns, and `_request_json`
  already tolerates `bytes`). Minimal additive change:
  - `_default_http_get(..., binary=False)` → `return resp.content if binary else resp.text`;
  - `_fetch_with_retry(..., binary=False)` → when calling the **default** fetcher, pass `binary`; an
    **injected** `http_get` returns bytes for the binary endpoint (tests return a synthetic xlsx as `bytes`);
  - `_request_bytes(url, params=None, headers=None) -> bytes` → `_fetch_with_retry(..., binary=True)`, assert
    bytes (else `InvalidData`), no JSON/text decode, no caching (single-shot large payload).
- Backward compatible: new keyword-only `binary` defaults to `False`; every existing call + test stub is
  unchanged. Transport errors still wrap to `SourceUnavailable` with secret redaction (unchanged path).

### D4 — Vintage-coded URL robustness: pinned current + ordered fallback list
- The `…74e8be41ceb20fa0da750cda2f6b9e4e-0050012026…` path segment is vintage-coded. Pin an **ordered tuple**
  `_CMO_ANNUAL_URLS = (current, …)`; try each in order; on a per-URL 404/anti-bot/non-xlsx/parse-failure
  continue to the next; **all-fail → `SourceUnavailable`** (fail safe, like the existing sources).
  **Code-time:** the confirmed current URL is the full-32-char-hash one in §2; **no prior-vintage fallback
  was reproducible** (the earlier "prior vintages still 200" note did not hold — the only known fragment
  was this current vintage, truncated), so v1 ships a **single-element** tuple. Keep the iterate-and-continue
  structure so a prior vintage can be prepended/appended when WB next rotates. Document the URL + its vintage
  in `docs/sources/`. *Deferred enhancement (NOT v1):* scrape the Commodity Markets HTML page to
  auto-discover the current link — adds HTML-parse fragility for marginal gain; a pinned list updated when WB
  rotates the vintage is a small maintenance task.

### D5 — Integration: pure synthesis stays **byte-identical**; swap ONLY the gold-leg acquisition
- **Key finding:** `_synthesize_world_reference` (`world_reference.py:84-174`) aggregates the gold leg by
  `bar.date.year` via `sum/count` (lines 93-99). Feeding it CMO **annual** bars (one per year) yields
  `mean(one) = that value` — so **the pure synthesis function is unchanged** (no edit to lines 84-174). Its
  `_ANNUAL_BASIS_NOTE` text ("annual-average world gold (USD/oz) × …") stays accurate because CMO *is* the
  annual average of daily spot.
- **Only `world_reference_history_vnd` lines 218-224 change** — the gold-leg fetch becomes:
  **CMO primary (fetched directly, bypassing the daily coverage gate), daily `FailoverGoldClient`
  (CurrencyApi→Stooq) as fallback** so behavior is **never worse than #178**:
  ```python
  try:
      gold_hist = WorldBankCmoGoldSource(http_get=http_get, timeout=timeout).get_history(
          year_start, year_end
      )
  except SourceError:                      # CMO unreachable/blocked/malformed -> old path
      gold_hist = FailoverGoldClient(
          [CurrencyApiGoldSource(http_get=http_get, timeout=timeout),
           StooqGoldSource(http_get=http_get, timeout=timeout)],
          max_attempts=max_attempts,
      ).get_history(year_start, year_end)
  ```
  - **Why CMO bypasses `FailoverGoldClient`:** that client's 50% gate counts covered vs *expected weekday
    trading days*; an annual series (1 bar/year) is legitimately <1% of weekdays and would be wrongly
    rejected. CMO self-validates instead (D1 guards + EmptyData if no years in span). CMO can therefore NOT
    be a peer source inside the daily `FailoverGoldClient`.
  - **Never-silent fallback:** when the CMO path fails over to daily, append a
    `world_reference_gold_source_fallback: CMO annual source unavailable; used daily-averaging path`
    warning so the switch is disclosed (consistent with the leg-warning-forwarding discipline already in the
    synthesis). The result still carries the daily leg's `world_reference_gold_leg_*` warnings too.
  - **GATE NOTE N2 (reviewer APPROVE 04:53 — fail-loud vs fail-over discipline):** the `except` catches
    **`SourceError`** (the base of `SourceUnavailable`/`InvalidData`/`EmptyData`/`StaleData`), NOT bare
    `Exception` — so every *recoverable* CMO failure (unreachable/blocked → `SourceUnavailable`; malformed
    xlsx / out-of-band value → `InvalidData`; no years in span → `EmptyData`) reliably engages the daily
    fallback, while a **non-`SourceError` programmer bug propagates (fails loud)** instead of being silently
    swallowed into the fallback. CMO's `get_history` must therefore raise ONLY `SourceError` subclasses for
    all expected/recoverable conditions (tested in §6).
- **Everything else in #178 is preserved unchanged:** gold∩FX year intersection, `EmptyData`-on-no-overlap,
  the finiteness/positivity guard, ALL warnings (`_PREMIUM_NOTE` + `_ANNUAL_BASIS_NOTE` always;
  `world_reference_partial_year_coverage` when years are dropped; the `world_reference_trailing_year_incomplete`
  guard keyed on `current_year in common`), and `world_reference_gold_leg_*` / `world_reference_fx_leg_*`
  forwarding. With CMO (annual, published with a lag) the current in-progress year simply won't appear, so the
  trailing-year guard correctly stays quiet — keep it exactly as shipped (robust on direct `_synthesize` calls).
- **`gold.world()` daily history path is UNCHANGED** — only the annual synthesis switches to CMO primary.

### D6 — Provenance, attribution, surface
- `source="worldbank_cmo_gold"`; the new `docs/sources/cmo-gold-annual.md` documents endpoint/contract/
  semantics/CC-BY-4.0 attribution ("Source: The World Bank — Commodity Markets (Pink Sheet)"), following the
  `docs/sources/fx-history-worldbank.md` template. The synthesis result already credits the FX leg; its
  provenance/docs now credit **both** WB CMO (gold) + WB FX.
- **Public-API surface:** the accessor signature and `GoldHistory` output shape are unchanged; the new source
  class stays **internal** (not exported in the public surface) → `public_api_v0_2_0.json` stays **FROZEN**.
  ([[public-api-snapshot-is-release-time-not-per-feature]] — confirm surface test additive-green; do not regen.)

---

## 4. Three open questions → resolved (LEAD gate may override)

1. **xlsx-parse dependency** → **stdlib `zipfile`+`xml.etree`** (D2). Rationale: core accessor must work
   server-side out-of-the-box; keeps core lean. (Alt: optional `vnfin[gold-history]`→openpyxl.)
2. **Binary fetch** (surfaced during design; not in the spec) → **add `_request_bytes` + `binary=` to the
   transport** (D3), backward compatible.
3. **Vintage-coded URL** → **pinned current + ordered fallback list**, all-fail → `SourceUnavailable` (D4);
   HTML auto-discovery deferred.

---

## 5. Integration plan (files)

- **NEW** `vnfin/gold/worldbank_cmo.py` — `WorldBankCmoGoldSource(HttpDataSource)` + the scoped stdlib xlsx
  parser (`_parse_cmo_annual_gold(raw: bytes) -> dict[int, float]`) + `_CMO_ANNUAL_URLS`.
- **EDIT** `vnfin/transport.py` — add `_request_bytes` + `binary=` kwarg on `_fetch_with_retry` /
  `_default_http_get` (D3).
- **EDIT** `vnfin/gold/world_reference.py` lines 218-224 only — CMO-primary + daily-fallback + fallback
  warning (D5). `_synthesize_world_reference` UNCHANGED.
- **NEW** `docs/sources/cmo-gold-annual.md`; **EDIT** `docs/sources/gold-world-reference.md` (note the new
  primary annual source), `CHANGELOG.md`, and the `vnfin` skill if it documents the synthesis source.

## 6. Test plan (offline, synthetic — TDD red-first; [[fork-echoes-context-use-fresh-agent-for-delegated-impl]])

- **xlsx parser:** build a **minimal valid xlsx in-test via stdlib `zipfile`** (workbook.xml + rels +
  sharedStrings.xml + one worksheet shaped like `Annual Prices (Nominal)` — with the **split** `Gold` /
  `($/troy oz)` header on two rows, same column) → assert `{year: usd_per_oz}` parsed, **gold column matched
  by the split header text**. Robustness: missing `Gold` name cell / missing `($/troy oz)` units cell /
  `Gold` present but units mismatched (must NOT match — guards against a non-troy-oz gold column) / shifted
  gold column (parser still finds it by text) / malformed sheet / non-numeric value → `InvalidData`; non-xlsx
  (HTML/empty/truncated-zip) body → `InvalidData`/`SourceUnavailable`.
- **Source:** inject `http_get` returning the synthetic xlsx **bytes** for the CMO URL → `get_history` returns
  annual `GoldHistory` (one Jan-1 bar/year, USD/oz); HTTP 404/anti-bot → `SourceUnavailable`; **URL-fallback
  exercised** (first URL raises, second serves). Non-finite/`<=0`/duplicate-year price → `InvalidData`.
  **N1 magnitude guard:** a parsed value < 20 or > 10000 USD/oz → `InvalidData`. **N1 real-vintage parse:**
  parse the committed real CMO xlsx fixture `tests/fixtures/cmo/CMO-Historical-Data-Annual.xlsx`
  (SHA256 `9fbcb348…af51`), assert known year values (1960≈35.27, 2024≈2387.70, 2025≈3441.51) and
  66 points 1960–2025 with no gaps — this is the test that proves the parser handles the REAL split-header
  layout (it is exactly the surprise a synthetic-only test would miss).
- **N2 SourceError-subclass discipline:** assert every recoverable CMO failure raises a `SourceError`
  subclass (unreachable→`SourceUnavailable`, malformed/out-of-band→`InvalidData`, empty-span→`EmptyData`) so
  the `except SourceError` fallback engages; assert a non-`SourceError` bug propagates (NOT swallowed).
- **Transport:** `_request_bytes` returns bytes from an injected stub; default-path binary mode covered where
  feasible; transport error → `SourceUnavailable`; existing `_request_text`/`_request_json` callers unaffected.
- **Synthesis (the #178-internals change):** with CMO bytes + a synthetic WB-FX envelope, assert
  `bar.price == CMO[y] × FX[y] × OZ_TO_LUONG`, Jan-1 stamps, **all #178 warnings still fire**
  (premium/annual-basis always; partial-coverage on dropped years; trailing-year guard via injected
  `_today`), and the **CMO→daily fallback** path (CMO raises → daily serves) emits the fallback warning.
- **Clean-room:** the only new source is WB CMO xlsx (+ existing WB FX); **zero VNStock**.

## 7. Risks & mitigations
- **OOXML parse fiddliness** (shared strings, inline vs shared cell types, rels mapping) → scope the parser to
  exactly CMO's shape, cover edge cases in tests, and keep `InvalidData` on anything unexpected (fail safe).
- **WB rotates the vintage URL** → ordered fallback list + documented vintage; a 404-on-all is a clean
  `SourceUnavailable` (synthesis then falls over to the daily path with disclosure).
- **CMO format change** (header text / sheet name) → header-text matching (not index) + `InvalidData` on a
  missing `Gold ($/troy oz)` header; never serve a mis-parsed column.

---

**LEAD gate verdict (2026-06-21 04:53):** ✅ **APPROVE — D1–D6 all ratified**, with gate notes N1 (magnitude
guard) + N2 (SourceError-subclass discipline) now folded in above. Next: complete **#186** (core VN-Index
blocker) first, then return here for #185 TDD (red-first) → Codex×2 → push + close → ping vf-advisor.
