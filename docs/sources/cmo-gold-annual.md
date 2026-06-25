# Source — World Bank CMO "Pink Sheet" annual precious metals (gold · silver · platinum)

**Domains:**
- **gold** (internal) — world-gold annual leg of `vnfin.gold.world_reference_history_vnd` (issue #185)
  · **Source name:** `worldbank_cmo_gold` · **Class:** `WorldBankCmoGoldSource` (internal — not part of
  the public API surface).
- **silver + platinum** (public, issue #196) — `vnfin.metals.history(metal, start, end)` ·
  **Source name:** `worldbank_cmo_metal` · **Class:** `WorldBankCmoMetalSource`.

**Auth:** none (no key). All three read the SAME World Bank Commodity Markets annual `.xlsx` via one
**shared, domain-neutral parser** (`vnfin/_contracts/worldbank_cmo.py`, `parse_cmo_annual(raw, spec)`),
parameterized per metal by a frozen `MetalSpec(product, name_row, min_usd_oz, max_usd_oz, units_row)`.
Gold's observable output is byte-for-byte identical to its pre-extraction (#185) behaviour.

> **Where the gold leg fits:** the gold series is the **annual extended-history primary** in the
> end-to-end gold coverage map — see [`gold-world-reference.md` § End-to-end gold coverage & backup paths](gold-world-reference.md#end-to-end-gold-coverage--backup-paths-171)
> for daily vs annual, primary vs fallback, and the opt-in/backup story across all gold paths.

## Endpoint & contract

Annual world-gold (XAU/USD, USD per troy ounce) history is served by the World Bank **Commodity
Markets** "Pink Sheet" historical-data distribution, as an **`.xlsx`** workbook (it is **not** in
the World Bank Indicators JSON API — only reserve/holdings indicators are — which is what forces a
binary-fetch + xlsx-parse path rather than the JSON envelope the FX leg uses):

```text
GET https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Annual.xlsx
```

The `…74e8be41ceb20fa0da750cda2f6b9e4e-0050012026…` path segment is a **per-release vintage
digest** that shifts each time the World Bank rotates the publication. The adapter pins an
**ordered tuple** `_CMO_ANNUAL_URLS` (currently a single confirmed current vintage), tries each in
order, and on a per-URL 404 / anti-bot / non-xlsx / parse failure falls through to the next;
**all-fail → `SourceUnavailable`**. When the World Bank next rotates the hash, prepend/append the
new vintage URL to that tuple (the iterate-and-continue structure already supports it). The hash is
part of a **public CC-BY data URL — not a credential** (allowlisted by explicit project decision in
`tests/test_no_secrets.py`, sourced from `_CMO_ANNUAL_URLS` at runtime, never embedded as a literal).

> **`HEAD` is unreliable here** — the World Bank docs host returns `size=0` (no `Content-Length`)
> on `HEAD`. The fetcher therefore GETs the body and validates the `PK\x03\x04` zip magic by
> attempting to open the zip, rather than gating on a `HEAD` length.

## Parsing (stdlib only — no openpyxl/pandas)

An `.xlsx` is a zip of OOXML. The adapter reads exactly what CMO needs with **stdlib `zipfile` +
`xml.etree.ElementTree`** (keeping vnfin's core dep set to `httpx` only, so the synthesis works
out-of-the-box server-side):

1. `xl/workbook.xml` → find the `<sheet name="Annual Prices (Nominal)">` and read its `r:id`
   (real vintage: `rId2`).
2. `xl/_rels/workbook.xml.rels` → resolve that `r:id` → the worksheet part path (real vintage:
   `xl/worksheets/sheet2.xml`). **Resolved via the rels, never hard-coded** (the sheet number
   shifts between vintages).
3. `xl/sharedStrings.xml` → the shared-string table (header/text cells hold an index into it;
   `t="s"`).
4. Walk the worksheet rows. The **year is in column 0** (a data row is one whose col-0 cell is a
   4-digit year). Each precious-metal header is **SPLIT across two cells** — there is **no single
   combined string** — so a metal's column is matched by **BOTH** cells of its split header:
   - a name-row cell whose text is exactly the metal name (trimmed) — `Gold` / `Silver` / `Platinum`
     (the `MetalSpec.name_row`), **and**
   - the units-row cell **directly below it, same column**, whose text is exactly `($/troy oz)`
     (the shared `MetalSpec.units_row`).

   The match requires both cells because **all three** precious-metal columns carry the identical
   `($/troy oz)` units string; the **name disambiguates**. The column is located **by this text
   match, never a hard-coded index** (real vintage: Gold = 67 / `BP`, Platinum = 68 / `BQ`,
   Silver = 69 / `BR`, but the indices shift between vintages). Numeric cells (year, price) are
   stored as **raw numbers** (no `t="s"`, often no `t` attr); header cells are shared strings —
   both cell types are handled. The title/metadata rows above the header and the two header rows
   are skipped.

Any malformed/unexpected condition fails safe as `InvalidData`, **naming the metal**: missing name
cell, missing or mismatched `($/troy oz)` units cell, sheet not found, no data rows, non-numeric
price, an out-of-band magnitude (the per-metal band below), or a non-xlsx body (bad zip magic /
truncated / HTML). A metal's column is **never relabelled** as another's — an absent column is an
honest per-metal failure, not a silent wrong-column serve.

## Three precious-metal columns + per-metal plausibility bands

The shared parser reads any one of the three split-header columns by `MetalSpec`. Each metal has its
**own** magnitude band (USD/oz) — a backstop behind the split-header text match — **re-derived per
metal from its own measured 1960–2025 range**, never byte-copied across metals:

| Metal | `product` | column (real vintage) | band (USD/oz) | real range 1960–2025 |
|-------|-----------|------------------------|---------------|----------------------|
| Gold (internal, #185) | `XAU` | 67 / `BP` | `[20.0, 10000.0]` | 34.95 – 3441.51 |
| **Silver** (public, #196) | `XAG` | 69 / `BR` | `[0.10, 75.0]` | 0.91 – 39.80 |
| **Platinum** (public, #196) | `XPT` | 68 / `BQ` | `[50.0, 5000.0]` | 80.93 – 1719.48 |

**Why silver's ceiling sits below platinum's floor.** Silver's all-time annual ceiling (39.80) is
**below** platinum's all-time annual floor (80.93). The bands exploit this: silver `[0.10, 75.0]` is
capped below 80.93 so a **platinum** mis-read (cols 68/69 are adjacent — the realistic off-by-one)
is rejected by magnitude; platinum `[50.0, 5000.0]` has its floor above 39.80 so a **silver**
mis-read is rejected. Gold's range (35–3442) fully overlaps platinum's, so platinum's band **cannot**
reject gold by magnitude — there, the **split-header name-match is the primary defense** and the band
is only the sanity backstop (kept generous, ~2.9× the all-time high, so a real platinum rally is
never false-rejected). Silver's band rejects recent gold (≥1900 ≫ 75) by magnitude as well.

## Semantics

- **Frequency:** annual. Each emitted `GoldBar` is stamped on **Jan 1** of the reference year
  (matching the FX annual convention and the synthesis output).
- **Unit / currency:** `USD/oz` (USD per troy ounce), `currency="USD"`, `product="XAU"`.
- **Coverage:** 1960 → present, **no gaps** (current vintage: 66 points 1960–2025; e.g.
  1960 = 35.27, 2023 = 1942.67, 2024 = 2387.70, 2025 = 3441.51).
- **Basis (why it is a lossless drop-in for the synthesis):** the CMO gold series is *"Gold, spot
  average of daily rates"* (LBMA-sourced; the sheet's own descriptor: *"…from June 2025; previously
  (UK), 99.5% fine, London afternoon fixing…"*) — i.e. it is **already an annual average of daily
  spot**. So `CMO-annual-gold × WB-annual-FX × factor` preserves the #178 `annual-avg × annual-avg`
  basis exactly; no daily→annual averaging step is needed.
- **Silver / platinum** (public, `vnfin.metals`): same frequency (annual, Jan-1-stamped), unit
  (`USD/oz`) and currency (`USD`); `product` is `XAG` / `XPT`. `vnfin.metals.history("silver" | "XAG"
  | "platinum" | "XPT", start, end)` returns a `MetalHistory` of `MetalBar` whose never-silent typed
  fields state `frequency="annual"` and the CC-BY `attribution`. **Gold is NOT served here** —
  `vnfin.metals.history("gold")` raises `InvalidData` routing the caller to `vnfin.gold`; any other
  unsupported metal (`palladium`/`XPD`/`copper`/…) raises `InvalidData` naming it, **before** any
  network call.
- **Integrity / magnitude guards:** reject non-finite / `<= 0` prices, duplicate / non-monotonic
  years, and (gate note **N1**) any value outside the **per-metal** band above — all as
  `InvalidData`. Each band is generous (it only catches gross column misparses, never legitimate
  values) and is a backstop behind the split-header text match.

## Error discipline (gate note N2)

Every **recoverable** failure raises a `SourceError` subclass — unreachable/blocked →
`SourceUnavailable`, malformed/out-of-band → `InvalidData`, no years in the requested span →
`EmptyData` — so the synthesis `except SourceError` fallback engages reliably. A non-`SourceError`
programmer bug **propagates (fails loud)** rather than being swallowed into the fallback.

## Terms / provenance

- **License:** World Bank Commodity Markets ("Pink Sheet") data is **CC-BY 4.0** — attribution
  required: *"Source: The World Bank — Commodity Markets (Pink Sheet)"*.
- **Posture:** **runtime-fetch only — no bundled provider rows.** (CC-BY would permit
  redistribution with attribution, but bundling raw rows is not done; the committed
  `tests/fixtures/cmo/CMO-Historical-Data-Annual.xlsx` is a **test asset**, not a shipped dataset.)
- **Reachability:** verified `HTTP 200` from a datacenter host with no anti-bot challenge (unlike
  Stooq / currency-api), which is the whole reason CMO is the server-side primary.

## Limits

- **Annual only** — CMO publishes annual (and monthly) Pink Sheet workbooks; this adapter reads the
  annual nominal-USD sheet only. `vnfin.metals` serves **silver + platinum** only (no palladium,
  no daily/spot, no broader commodities — deferred).
- **Gold source is internal** — `WorldBankCmoGoldSource` is consumed only by
  `world_reference_history_vnd` (as the primary world-gold leg); it is not exported on the public API
  surface. The silver/platinum source `WorldBankCmoMetalSource` **is** public (via `vnfin.metals`).
- **Vintage-coded URL** — when the World Bank rotates the publication hash the pinned URL 404s; the
  ordered fallback list + a clean `SourceUnavailable` (then the synthesis falls over to the daily
  path with disclosure) keep this fail-safe. Update `_CMO_ANNUAL_URLS` when that happens.
