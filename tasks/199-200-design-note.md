# #199 + #200 design note — native international-index source/design batch

Status: **DESIGN NOTE FOR REVIEWER GATE — no implementation yet**
Date checked: 2026-07-25 +07
Intake/spec (reviewer repo): `tasks/199-bangladesh-main-indices-spec.md` (commit `465d905`),
`tasks/200-canada-indicators-spec.md` (commit `e2cab7a`).
PO handoff: 2026-07-25 17:26, batched as one source/design gate per the shared `vnfin.indices`
native-points architecture question, Bangladesh/Canada evidence kept separate, neither a fallback
for the other.

## 0. Bottom line

Both requested **equity-index** halves are **source-blocked** — no candidate is simultaneously
lawful, technically adequate, and covers the requested indices as native points. Recommendation:
**do not implement either equity-index feature**; close #199 and the equity-index half of #200 as
`source-gap-documented` with explicit reopen criteria (mirrors the #182/#175 precedent), no ETF/CSE
proxy substitution. The **Canada macro** half of #200 is already fully served by the existing
`vnfin.macro.get_indicator(iso3, MacroIndicator)` API on current `master` — no new source, no new
public surface, only a small additive regression-test + docs change is proposed (spec'd in §5
below, gated same as any code change).

Because there is no lawful source to route to, the "additive API/capability routing" question the
PO/specs ask for is answered as: **no new routing is added.** `vnfin.indices.world()`'s existing
`_validate_symbol` gate (`vnfin/indices/world_client.py:269-282`, runs at line 258 strictly before
any client construction or network call) already rejects any symbol outside
`SUPPORTED_WORLD_SYMBOLS` with a typed `InvalidData` enumerating the supported set — `DSEX`,
`DS30`, `DSES`, and `GSPTSE`/`^TSX`/`^GSPTSE`-style Canadian symbols would already hit this
existing guard today, correctly, with zero code change. There is nothing to "wire in" for a source
that doesn't exist; adding a dedicated new entrypoint/registry for zero servable symbols would be
speculative and is explicitly against the "no design for hypothetical requirements" discipline.

## 1. #199 — Bangladesh DSEX / DS30 / DSES

### 1.1 Source-vetting evidence

Full report (research-assistant agent, 2026-07-25, VNStock-exclusion applied throughout):
`/tmp/claude-1000/-home-hungson175-dev-vnfin-oss/67932dd5-d49a-41b1-a9ca-164ad4a51bcb/scratchpad/bd-dse-source-vetting.md`.
Summary, per the spec's required preference order:

| # | Candidate | Coverage (3 indices) | Lawful for OSS BYOK? | Verdict |
|---|---|---|---|---|
| 1 | Official DSE (`dsebd.org`/`dse.com.bd`) | in principle all 3 (per-index live pages found) | unconfirmed — ToS page itself 403'd | **blocked-in-practice**: every probed page (home, `data_archive.php`, `dseX_share.php`) returned `403 Forbidden`; `robots.txt` 404; TLS chain incomplete (`unable to get local issuer certificate`); no bulk *historical* index-series endpoint identified (`data_archive.php` is a per-security lookup tool, not an index-history export); mirrors `backup3.dsebd.org`/`web.dsebd.org` unreachable |
| 2 | TradingView (`DSEBD:` partner data since 2023-06) | DSEX confirmed, DS30/DSES unconfirmed | No public reuse API; ToS restricts scraping/redistribution | rejected |
| 3 | Investing.com (Fusion Media) | all 3 (only candidate with full nominal coverage) | ToS **prohibits automated access entirely** (not just redistribution) | rejected — hard ToS blocker per spec's own rule |
| 4 | Alpha Vantage | 0 (verified via official `LISTING_STATUS`, 14,210 symbols, zero BD/DSE matches) | n/a | rejected, confirmed absent |
| 5 | CEIC Data | catalogs "DSE Index" | enterprise-subscription only, no public API | rejected — not BYOK-shaped |
| 6 | Mendeley Data (CC BY 4.0) | stock-level only, no index data | open license but wrong granularity + static snapshot | rejected |
| 7 | Kaggle dataset | DSEX only, stale (2013–2020), unclear provenance | — | rejected |
| 8 | `dsestocks.com`, `faysal515/bd-stock-api` | — | unofficial mirror/scraper | **excluded per spec rule** (no unofficial scraper/mirror) |
| 9 | BSEC / Bangladesh Bank | no DSE index series found (negative evidence, not exhaustively audited) | — | no adequate source found |

**Caveat on the dsebd.org 403s** (per [[sandbox-probe-false-negative-not-a-source-verdict]]): these
are a *signal*, not a definitive verdict — could be anti-bot/geo gating rather than a hard block. A
maintainer probing from a Bangladesh-region IP, or direct DSE IT contact, could change this
conclusion. Not resolvable from this environment.

### 1.2 Recommendation

**Source-blocked.** No implementation. Close #199 with a resolution comment naming the candidates
checked and this reopen-criteria set (mirrors `tasks/182-close-comment.md`'s structure):

> Reopen if a source appears that meets ALL of: (1) official or a redistribution-permitting
> DSE/regulator publication of DSEX/DS30/DSES; (2) a genuine bulk *historical* index-series
> endpoint/export (not a live-only snapshot); (3) verified reachable from ordinary
> server/datacenter egress with written terms permitting automated runtime retrieval; (4) can
> distinguish all three indices by provider-side identity (no cross-index ambiguity).

## 2. #200 — Canada

### 2.1 Macro (existing API) — CONFIRMED WORKING, no new code needed

Live-probed on current `master` (2026-07-25), no mocks:

```
vnfin.macro.get_indicator("CAN", MacroIndicator.GDP)          -> OK, 66 points, unit="current US$"
vnfin.macro.get_indicator("CAN", MacroIndicator.CPI)           -> OK, 66 points, unit="index"
vnfin.macro.get_indicator("CAN", MacroIndicator.UNEMPLOYMENT)  -> OK, 35 points, unit="%"
vnfin.macro.get_indicator("CAN", MacroIndicator.GDP_GROWTH)    -> OK, 65 points, unit="%"
vnfin.macro.get_indicator("CAN", MacroIndicator.INFLATION)     -> OK, 66 points, unit="%"
```

All five route through the existing keyless country-generic World Bank adapter
(`vnfin/macro/client.py:478-490`, `MacroClient.get_indicator`) — no Canada-specific branching
exists or is needed; the adapter is already ISO3-generic. `CPI` correctly stays an index level and
`INFLATION`/`GDP_GROWTH` stay rates, per the spec's requirement not to conflate them.

**Gap found:** `CAN` is untested. `tests/test_macro_worldbank.py`,
`tests/test_macro_contracts.py`, and `tests/test_macro_failover.py` all parametrize
*format-validation* (bad country codes) thoroughly, but every real-country happy-path test
hardcodes `"VNM"` (macro) or `"USA"`/`"US"` (as WB observation payload country codes in fixtures).
`grep -rn "CAN\b" tests/ docs/` returns zero hits before this change. No test proves the
country-generic path actually serves a second real country end-to-end with a mocked HTTP fixture —
today's confidence rests on the live probe above, which is not part of CI (offline unit/contract
tests only per project policy). Proposed fix in §5.

### 2.2 Equity indices — S&P/TSX Composite / 60 / Venture Composite

Full report (research-assistant agent, 2026-07-25, VNStock-exclusion applied throughout):
`/tmp/claude-1000/-home-hungson175-dev-vnfin-oss/67932dd5-d49a-41b1-a9ca-164ad4a51bcb/scratchpad/can-tsx-source-vetting.md`.
Summary, per the spec's required preference order:

| # | Candidate | Coverage (3 indices) | Lawful for OSS BYOK? | Verdict |
|---|---|---|---|---|
| 1 | S&P Dow Jones Indices (index administrator) | admin only, no data endpoint | no public API/download at all; every `spglobal.com` URL probed 403'd | rejected |
| 2 | TMX Group / TMX Datalinx (exclusive commercial distributor) | **only entity with genuine native data for all 3** | pricing page states explicitly *"Prices are for a single end user, and do not include redistribution rights"*; sign-in-gated Webstore, no BYOK/self-serve key model | **rejected — technically correct source, legally incompatible**: the "end user" under TMX's terms is each downstream consumer of the OSS library, which the license does not permit |
| 3 | Bank of Canada / Statistics Canada | no S&P/TSX series found (T-bill/FX only) | n/a | rejected |
| 4 | Alpha Vantage (existing BYOK provider) | 0 — official Index Data API docs list only 6 US indices (DJI, SPX, COMP, NDX, VIX, Russell 2000); confirmed independently by this project's own `WORLD_INDEX_SPECS` (#193), which never admitted a TSX symbol | n/a | rejected, confirmed absent both ways |
| 5 | Twelve Data | 0 — live `symbol_search?symbol=GSPTSE` returned `{"data":[],...}` | n/a | rejected, confirmed empty |
| 6 | Financial Modeling Prep | no positive evidence (docs anti-bot gated, demo key rejected) | — | inconclusive, no signal found |
| 7 | Marketstack | no confirmed coverage (generic "750+ indices" marketing claim only) | — | inconclusive, not verified |

Per spec, ETF proxy (XIU/XIC), a futures contract, or a neighboring index are explicitly excluded
as substitutes and were not pursued as "solutions."

### 2.3 Recommendation

**Source-blocked** for the equity-index half. No implementation. Fold into the same #200
resolution comment: macro half fully served (see §2.1/§5), equity-index half source-blocked with
reopen criteria:

> Reopen the equity-index request if a source appears that meets ALL of: (1) native S&P/TSX
> Composite/60/Venture Composite index-point data (not an ETF/futures/neighboring-index proxy);
> (2) terms that permit an OSS BYOK library to have each end user retrieve their own data (i.e.
> not a single-end-user/no-redistribution enterprise license); (3) a self-serve or keyless API
> surface, not a sign-in-gated commercial storefront; (4) verified reachable from ordinary
> server/datacenter egress.

## 3. Non-negotiable invariants (both specs)

No code ships for either equity-index feature, so no identity/unit/no-proxy/time/completeness/
provenance invariant is at risk of violation — the existing `_validate_symbol` guard already
rejects `DSEX`/`DS30`/`DSES`/any TSX symbol before network, unchanged. The one code change
proposed (§5, CAN macro regression) touches only test/docs surface, zero production logic, zero
public-API/snapshot change (`get_indicator` already accepts any ISO3 string). "Compatibility"
requirement (existing 8 `indices.world` symbols behaviorally unchanged) is trivially satisfied —
`world_sources.py`/`world_client.py` are untouched by this batch.

## 4. Architecture / capability-routing comparison (required by both specs)

The specs ask the design note to compare "extend `indices.world()`" vs. "new country-specific
entrypoint" vs. "new global-native-index entrypoint." Since there is zero servable symbol for
either country, this comparison has no decision to make right now — building any of the three
options for a source that doesn't exist would be pure speculative architecture with no test able
to prove real behavior (the project's "no design for hypothetical requirements" rule). This
question naturally resurfaces, with a real decision to make, if and when a reopen-criteria source
is later found — flagged as a **fast-follow architecture question**, not resolved here.

## 5. RED-first test/docs matrix — the only proposed change

Everything below is the complete list of proposed changes in this batch; nothing else.

**5.1 Regression test (RED-first).** Add a mocked-HTTP-fixture parametrized happy-path test
proving the country-generic World Bank macro path actually serves a *second* real country
end-to-end, not just format-validated. Proposed location: extend
`tests/test_macro_worldbank.py` (or `tests/test_macro_contracts.py`'s `_SOURCES` matrix) with a
`country="CAN"` case parametrized alongside the existing `"VNM"` happy-path fixture(s), asserting:
canonical unit/currency per indicator (GDP→USD, CPI→index no currency, UNEMPLOYMENT→%), ascending
dates, non-empty points, `country_name`/`country` fields correctly populated for `CAN`. Uses the
existing injected `http_get` fixture pattern (synthetic World Bank JSON payload for Canada,
committed to the repo) — no live network in CI, per project policy. This is a fail-first
regression only in the sense that no test currently proves this path for a country other than
`VNM`/`USA`; it does not change any production code (the adapter is already country-generic), so
it is expected to go green immediately once the country param is threaded through — the value is
closing the untested-path gap, mirroring the batch's own §1.1 "verify directly, don't assume"
discipline.

**5.2 Docs.** Add a Canada example line to `docs/tutorials/macro-and-fx.md`'s "Macro indicators"
section (alongside the existing `VNM` example) to make cross-country support discoverable, e.g.:

```python
canada_gdp = vnfin.macro.get_indicator("CAN", MacroIndicator.GDP)
```

No change needed to `docs/sources/macro-worldbank.md` (already documents `{ISO3}` as a generic
parameter with multiple example codes, not an exhaustive allowlist).

**5.3 No changes** to `docs/sources/indices-world.md`, `vnfin/indices/world_sources.py`,
`vnfin/indices/world_client.py`, `CHANGELOG.md` public-API section, or the public-API snapshot —
nothing new ships to the public surface.

**5.4 Issue resolution comments.** Draft close comments for #199 and #200 (equity-index half)
following the `tasks/182-close-comment.md` structure (candidate table + numbered reopen criteria,
per §1.2/§2.3 above) — to be posted only after this design note is gated and reviewer confirms
disposition (close-now-with-reopen-criteria vs. keep-open-as-source-watch, same open question
`182-close-comment.md` flagged for gold).

## 6. Clean-room record

Both source-vetting passes (Bangladesh §1.1, Canada §2.2) were conducted by fresh research agents
under the mandatory VNStock exclusion, appended to every search query:
`-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"`. No VNStock or
VNStock-derived repository, site, package, snippet, or documentation was searched, opened, read,
cited, or used at any point in either report (see each report's own §5/§4 clean-room statement for
the full source list). Sources actually consulted: official DSE domains, TradingView, Investing.com,
Alpha Vantage, CEIC, Mendeley, Kaggle, BSEC, Bangladesh Bank (Bangladesh); S&P Dow Jones Indices,
TMX Group/TMX Datalinx, Bank of Canada, Statistics Canada, Alpha Vantage, Twelve Data, Financial
Modeling Prep, Marketstack (Canada). All unrelated to and independent of VNStock/finkit.

## 7. Required transition

No implementation before this gate. Requesting design review from `vnfin-oss-reviewer` with the
exact commit SHA of this note. On PASS: implement §5 only (RED-first CAN macro regression + docs),
then route the #199/#200 close-comment disposition question (§5.4) back to the reviewer before
posting/closing either issue — mirrors the still-open `182-close-comment.md` disposition question.
