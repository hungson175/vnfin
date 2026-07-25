# #199 + #200 design note — native international-index source/design batch

Status: **DESIGN NOTE FOR REVIEWER GATE — no implementation yet**
Date checked: 2026-07-25 +07
Intake/spec (reviewer repo): `tasks/199-bangladesh-main-indices-spec.md` (commit `465d905`),
`tasks/200-canada-indicators-spec.md` (commit `e2cab7a`).
PO handoff: 2026-07-25 17:26, batched as one source/design gate per the shared `vnfin.indices`
native-points architecture question, Bangladesh/Canada evidence kept separate, neither a fallback
for the other.

## 0. Bottom line (revised — round-3, post-gate-2 BLOCK)

**#199 Bangladesh (DSEX/DS30/DSES): source-blocked, unchanged conclusion, on further-corrected
evidence.** Recommend close as `source-gap-documented` with reopen criteria (§1.2), no ETF/CSE
proxy substitution.

**#200 Canada: the round-2 "genuine partial win" was itself overstated — StatCan is technically
real but its reuse rights are NOT established, so it is not buildable now either.** The
reviewer/PO has **resolved the scope question directly** (round-2 gate, "PO disposition" section)
rather than leaving it for a further round-trip:

- **S&P/TSX Venture Composite:** source-blocked, no candidate at all. Close-with-reopen for this
  identifier only (§2.3(i), unchanged).
- **S&P/TSX Composite + S&P/TSX 60 — NOT buildable now.** Statistics Canada Table 10-10-0125-01 is
  technically real, keyless, and directly verified to carry both series as native points, but its
  third-party (TMX-sourced) index values are **not established as reusable** under the Statistics
  Canada Open Licence — the Open Licence FAQ excludes third-party-owned IP, and the table's own
  footnotes name TMX Group (post-2017) / Bank of Canada (pre-2017) as the actual source. The
  decisive problem is **chain of title, not staleness** — even if the staleness were acceptable,
  reuse rights are unresolved. **PO ruling (binding, decided in the round-2 gate, not punted to a
  further round-trip):** IF Statistics Canada or TMX/S&P later confirm reuse/redistribution rights,
  archival monthly Composite/TSX 60 history is **in product scope** — but only as an explicitly
  historical/archival series (frequency, last observation, provenance, and a mechanical end-gap
  warning mandatory; never presented as a current quote; never coerced into `PriceHistory`). That
  conditional approval does **not** clear the present source — close now, reopen only on proof.
  See §2.3(ii).
- **TMX Datalinx:** unchanged from round-2 — **inconclusive/unresolved**, not "legally blocked." A
  real self-serve paid BYOK path plausibly exists (each end user brings their own TMX token, same
  shape as the existing Alpha Vantage pattern), but the decisive EULA text is sign-in-gated and
  unread. See §2.3(iii).

**Net: still no implementation from this note.** Both issues are now recommended for the SAME
disposition shape as each other (unlike round-2's asymmetric "close #199, hold #200"): close #199
fully, and close #200's equity-index portion as a documented source gap with StatCan/TMX/S&P
reopen criteria — while the **Canada macro** half of #200 proceeds separately and is unaffected
(already fully served by the existing `vnfin.macro.get_indicator(iso3, MacroIndicator)` API,
implement only the regression-test + docs change in §5 after this gate PASSes).

Because there is no lawful, rights-confirmed source to route to for either country's equity
indices, the "additive API/capability routing" question the PO/specs ask for is answered as: **no
new routing is added in this note.** `vnfin.indices.world()`'s existing `_validate_symbol` gate
(`vnfin/indices/world_client.py:269-282`, runs at line 258 strictly before any client construction
or network call) already rejects any symbol outside `SUPPORTED_WORLD_SYMBOLS` with a typed
`InvalidData` enumerating the supported set — `DSEX`, `DS30`, `DSES`, and any TSX symbol would
already hit this existing guard today, correctly, with zero code change. If StatCan/TMX reuse
rights are later proven, the PO has already ruled the shape (archival/historical, not
`PriceHistory`) — see §4 for why this note still does not commit to a concrete signature now.

## 1. #199 — Bangladesh DSEX / DS30 / DSES

### 1.1 Source-vetting evidence (revised — round-2 + round-3 corrections)

Durable report, committed to this repo (not a `/tmp` scratch path — addresses gate-1 finding B3):
`docs/research/2026-07-25-bd-dse-source-vetting.md`. Every category label below is one of the four
exact labels the report uses: **confirmed absent**, **not exposed through a lawful API**,
**inconclusive/unresolved**, **temporarily unreachable**.

| # | Candidate | Coverage (3 indices) | Evidence | Category |
|---|---|---|---|---|
| 1 | Official DSE (`dsebd.org`) | DSEX/DS30 pages confirmed; DSES page unverified | Reachable **HTTP 200** on 2026-07-25 (the round-1 "403" was a local sandbox TLS-trust-store gap, not a server block — corrected finding). `copyright.htm`/`termsacond.htm` fetched verbatim: forbids redistribution and "storing in any other electronic retrieval system" without prior written permission | **not exposed through a lawful API** |
| 2 | TradingView (`DSEBD:` partner since 2023-06) | DSEX/DS30 confirmed listed; DSES unknown | `/policies/` fetched 2026-07-25: forbids "creating products or services based on TradingView content" and states "we do not permit commercial usage of any of our services or APIs" | **not exposed through a lawful API** |
| 3 | Investing.com (Fusion Media) | DSEX confirmed; DS30/DSES unknown | Every direct fetch of the ToS (HTML+PDF, WebFetch+curl) failed with connection resets on 2026-07-25 — could not read first-hand; second-hand search-snippet language (prior-written-consent redistribution ban) noted with that caveat | **temporarily unreachable** for ToS verification; structurally consistent with "not exposed through a lawful API" |
| 4 | Alpha Vantage | 0 — **corrected**: round-1 wrongly used `LISTING_STATUS` (a US stock/ETF catalog, cannot prove index absence); round-2 used the correct `INDEX_CATALOG` endpoint (317 rows, `symbol,name`), independently re-verified by me via a fresh `curl` on 2026-07-25 (317 data rows, zero `DSEX\|DS30\|DSES\|Dhaka\|Bangladesh` matches, first rows `DJI`/`SPX` confirming genuine major-index catalog) | **confirmed absent** |
| 5 | Stooq (existing project fallback source for other symbols) | unresolved — **new in round-2**, not checked in round-1 | `stooq.com/q/d/l/?s={dsex,ds30,dses}&i=d` all returned a client-side JS proof-of-work bot wall, not CSV; `robots.txt: Disallow: /` for generic user-agents (Bing/Google only allowed) | **inconclusive/unresolved** |
| 6 | Financial Modeling Prep | unresolved — **bounded, not vague**: `demo` key rejected outright (unlike AV); docs page (fetched after an initial 403, retried with a browser UA) contains zero Bangladesh/DSEX/DS30/DSES text, but that is docs-prose absence, not a catalog audit | **inconclusive/unresolved** |
| 7 | Marketstack | unresolved — **bounded**: docs render as a JS app, no endpoint content exposed to non-browser fetch; no trial key available to call `indexlist` directly | **inconclusive/unresolved** |
| 8 | CEIC Data | DSEX/DS30 series exist (monthly, not daily); DSES unknown | **Corrected (round-3, gate-2 finding R2-B3.2):** paid ≠ unlawful on its own; what's actually unresolved is exact per-user access terms, whether any self-serve tier exists, and DSES coverage — not attempted directly in this pass | **inconclusive/unresolved** (was wrongly "not exposed through a lawful API") |
| 9 | Mendeley Data / Kaggle | not freshly re-verified in round-2 | Prior finding: stock-level only (Mendeley) / DSEX-only stale 2013–2020 (Kaggle) | **inconclusive/unresolved** |
| 10 | Unofficial mirrors (`dsestocks.com`, `faysal515/bd-stock-api`, etc.) | — | Named, not opened/used, per spec's exclusion rule; inherit DSE's own copyright restriction regardless of technical feasibility | **not exposed through a lawful API** (excluded per spec rule) |
| 11 | BSEC / Bangladesh Bank | none found | **Corrected (round-3, gate-2 finding R2-B3.3):** a targeted search finding no hit is not authoritative-catalog proof of absence | **no source found in the bounded search** (was wrongly "confirmed absent") |

**No candidate is "confirmed absent + fully checked" in a way that would let a future maintainer
skip re-verification.** FMP, Marketstack, Stooq, Mendeley/Kaggle, CEIC, and BSEC/Bangladesh Bank
remain genuinely inconclusive/unresolved or bounded-search-negative (sandbox/tooling/search-depth-
bounded, not confirmed-absent) — see the report's per-candidate "what blocked me" trail. DSE's own
`copyright.htm`/`termsacond.htm` text (candidate 1) is the strongest, most direct basis for the
overall verdict for the official channel specifically; per gate-2 finding R2-B3.4, this does not by
itself rule out a *future, different* provider with separate distribution rights, so the reopen
criterion in §1.2 stays explicitly about a licensed provider, not just DSE.

### 1.2 Recommendation

**Source-blocked**, on corrected evidence. No implementation. Close #199 with a resolution comment
naming the candidates checked and this reopen-criteria set (mirrors `tasks/182-close-comment.md`'s
structure):

> Reopen if a source appears that meets ALL of: (1) official or a redistribution-permitting
> DSE/regulator publication of DSEX/DS30/DSES, OR a clearly licensed provider whose terms
> affirmatively permit automated/redistributable runtime retrieval; (2) a genuine bulk *historical*
> index-series endpoint/export (not a live-only snapshot); (3) verified reachable from ordinary
> server/datacenter egress; (4) can distinguish all three indices by provider-side identity (no
> cross-index ambiguity). Two cheap next actions if this gets revisited: (a) register a free FMP key
> and a Marketstack trial key and re-run the two catalog calls documented in the report (~5 min,
> would convert two "inconclusive" rows to definitive); (b) if lawful access is genuinely wanted,
> contact DSE directly — their own copyright notice names "prior written permission" as the path to
> redistribution.

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

All five route through the existing keyless country-generic World Bank adapter via
`vnfin.macro.get_indicator` — the module-level convenience function
(`vnfin/macro/client.py:478-490`, corrected range per gate-2 finding R2-B5 — round-2 wrote the
impossible `478-497`) that delegates to `MacroClient.get_indicator`
(`vnfin/macro/client.py:194-231`, the class method the round-1 note mislabeled the module-level
function as — corrected here per gate-1 finding B6). No Canada-specific branching exists or is
needed; the adapter is already ISO3-generic. `CPI` correctly stays an index level and
`INFLATION`/`GDP_GROWTH` stay rates, per the spec's requirement not to conflate them. World Bank's
`FP.CPI.TOTL` (`vnfin/macro/worldbank.py:62`) maps CPI to the canonical `"index"` unit and — since
World Bank is first in the default chain order (`WorldBankMacroSource, IMFDataMapperSource,
DBnomicsSource`, `vnfin/macro/client.py:59-63`) and DBnomics only survives `eligible_sources`
filtering when World Bank is absent/ineligible — CPI now resolves via **World Bank**, not
DBnomics (corrected fact for §5.2's docs fix; `docs/sources/macro-worldbank.md:57` currently says
the opposite and needs updating).

**Gap found:** `CAN` is untested. `tests/test_macro_worldbank.py`,
`tests/test_macro_contracts.py`, and `tests/test_macro_failover.py` all parametrize
*format-validation* (bad country codes) thoroughly, but every real-country happy-path test
hardcodes `"VNM"` (macro) or `"USA"`/`"US"` (as WB observation payload country codes in fixtures).
`grep -rn "CAN\b" tests/ docs/` returns zero hits before this change. No test proves the
country-generic path actually serves a second real country end-to-end with a mocked HTTP fixture —
today's confidence rests on the live probe above, which is not part of CI (offline unit/contract
tests only per project policy). Proposed fix in §5.

### 2.2 Equity indices — S&P/TSX Composite / 60 / Venture Composite (revised — round-3)

Durable report, committed to this repo (addresses gate-1 finding B3):
`docs/research/2026-07-25-can-tsx-source-vetting.md`. Category labels are the same four exact
labels used in §1.1, plus one genuine fifth outcome (StatCan) that doesn't fit any of the four.

| # | Candidate | Coverage (3 indices) | Evidence | Category |
|---|---|---|---|---|
| 1 | S&P Dow Jones Indices (index administrator) | admin confirmed, no self-serve API found | "API Data Solutions" brochure is institutional/subscriber-oriented, no visible individual signup; every `spglobal.com` URL probed 403'd (evidence bounded by that) | **not exposed through a lawful [self-serve] API** |
| 2 | **Bank of Canada Valet API** | 0 | **Confirmed absent via a full programmatic sweep** of all 15,906 series + 2,524 groups (not a spot-check) — only incidental chart-annotation series match "TSX" in text, no real index series | **confirmed absent** |
| 3 | **Statistics Canada Table 10-10-0125-01** ("Toronto Stock Exchange statistics") | Composite + TSX 60 technically present; Venture absent | **Corrected — round-2's "openly licensed"/"lawful"/"buildable" claim was wrong (gate-2 finding R2-B1, the decisive blocker).** The applicable instrument is the **Statistics Canada Open Licence** (distinct from the government-wide OGL); its own FAQ excludes third-party-owned IP, and this table's own footnotes name **TMX Group** (post-2017) / Bank of Canada (pre-2017) as the actual data source — nothing in the record proves StatCan's agreement with TMX/S&P grants sublicensing/reuse rights. Independently re-verified 2026-07-25: cube footnote 4 states verbatim *"this table is no longer being updated as of November 1, 2023"* (program status: inactive/discontinued, per gate-2 + my own corroborating footnote read); exact per-series spans (not one cube-wide span, per gate-2 finding R2-B2): Composite close `v122620` 1956-01–2023-09, Composite high/low `v122618`/`v122619` 1976-01–2023-09, TSX 60 `v19457778` 1982-01–2023-09; 11,428 rows/25 series, no pagination; documented WDS rate limits (25 req/s/IP, 50 server-wide) | **technical identity/API confirmed; reuse rights inconclusive** (Composite/60) / **confirmed absent** (Venture) |
| 4 | **TMX Group / TMX Datalinx** (exclusive commercial distributor, current/daily data) | genuine native data for all 3 (per its own product descriptions) | Unchanged from round-2 (gate-2 confirms this is now correctly classified). Separated 5 questions with direct evidence: (a) code-distribution not restricted; (b) a real self-serve individual account + "Custom Queries — Pay Per Use" product exists (free account signup, ≈C$163.53/mo minimum charge); (c) the "single end user, no redistribution" clause reads as the standard per-seat licensing split (targets reselling to third parties), not a ban on an individual's own automated retrieval — mirrors the existing Alpha Vantage BYOK pattern; (d) a **documented REST API + SFTP with 1-year token auth does exist**; (e) genuinely unresolved: the exact EULA text confirming an individual's own script is "permitted use" is sign-in-gated (every TMX domain 403'd direct fetch) | **inconclusive/unresolved** |
| 5 | Alpha Vantage | 0 — round-2 correction unchanged (used `INDEX_CATALOG`, 317 rows, independently re-verified via my own fresh `curl` on 2026-07-25, zero `TSX\|GSPTSE\|Toronto\|Canada` matches) | AV's own documentation enumerates only US indices for the Premium OHLCV suite; `INDEX_CATALOG` catalog confirms no Canadian entry | **confirmed absent** |
| 6 | Twelve Data | 0 native instrument found under 6 tested queries | **Corrected (round-3, gate-2 finding R2-B3.1):** 6 relevance-ranked `symbol_search` permutations (`GSPTSE`, `TSX`, `%5EGSPTSE`, `TSX60`, `TSXV`, `S%26P%2FTSX`) found only ETFs/structured notes, never the index itself — but this does not enumerate Twelve Data's complete index catalog the way Alpha Vantage's `INDEX_CATALOG` pull does, so it cannot support a "confirmed absent" claim | **inconclusive/unresolved** (was wrongly "confirmed absent") |
| 7 | Stooq (existing project fallback for other symbols) | Composite: plausible via cached page title only; 60/Venture: no signal | Every direct probe — including the project's own already-working `^spx` control — hit a site-wide JS proof-of-work bot wall today; Google's cached title for `^TSX` reads "S&P/TSX Composite Index" but this is third-party cache evidence, not a direct read | **inconclusive/unresolved** |
| 8 | Financial Modeling Prep | unresolved — bounded | `demo` key rejected (401, unlike AV's working demo) on every index endpoint tried; docs page 403'd | **inconclusive/unresolved** |
| 9 | Marketstack | unresolved — bounded | `demo` access_key rejected (401); docs mirror is login-gated, no substantive content | **inconclusive/unresolved** |

Per spec, ETF proxy (XIU/XIC), a futures contract, or a neighboring index remain explicitly
excluded as substitutes and were not pursued as "solutions" for any candidate above.

### 2.3 Recommendation (revised — round-3, PO ruling incorporated)

No implementation from this note (gate-1/gate-2 both said no implementation before design PASS).
The reviewer/PO resolved the scope question directly in the round-2 gate rather than leaving it
for a further round-trip — #200's equity-index portion now closes, same as #199, with reopen
criteria:

**(i) S&P/TSX Venture Composite — source-blocked, clean, unchanged.** No candidate anywhere.
Close-with-reopen for this identifier specifically:

> Reopen if a source appears with native Venture Composite index points, lawfully retrievable
> (self-serve or a clearly licensed provider API), reachable from ordinary server/datacenter
> egress.

**(ii) S&P/TSX Composite + S&P/TSX 60 — NOT buildable now; close with a conditional reopen
criterion, not held open pending a scope call.** StatCan Table 10-10-0125-01 is technically real
and keyless, but its reuse rights for the TMX-sourced index values are unresolved (§2.2 row 3) —
this is a chain-of-title problem, not a staleness problem, so the honestly-disclosed-staleness
precedent (`series_end_gap`/`nav_end_gap`/`current_snapshot_only`, #172/#175/#179) does not resolve
it; disclosure cannot cure an unproven licence. **PO ruling (binding):**

> Reopen once (a) Statistics Canada confirms in writing that Table 10-10-0125-01's TMX-sourced
> Composite and TSX 60 series are covered for reuse/redistribution under the Statistics Canada
> Open Licence, or TMX/S&P supplies an equivalent grant directly, OR (b) the TMX Datalinx EULA
> (see (iii)) is confirmed to permit individual automated retrieval, making a paid BYOK path
> viable instead. **If (a) is met:** archival monthly Composite/TSX 60 history is pre-approved as
> in product scope — but only as an explicitly historical/archival series: mandatory frequency +
> last-observation + provenance + a mechanical end-gap warning, never presented as a current quote,
> never coerced into `PriceHistory`. This conditional scope approval does not itself clear the
> present source; it only removes the product-scope question from the reopen path once rights are
> proven.

**(iii) TMX Datalinx — inconclusive/unresolved, reopen criteria, unchanged from round-2.** A
plausible current/daily BYOK path exists but the decisive EULA text is unread:

> Reopens once the specific TMX "Custom Queries" Market Data Services Agreement / EULA text
> (currently sign-in-gated) is obtained and confirms it permits an individual subscriber's own
> automated script to retrieve data under their own account/token for their own use (not
> requiring a separate "distributor" designation). If confirmed, this becomes a normal paid-BYOK
> adapter (each user brings their own TMX account, same shape as the existing Alpha Vantage
> pattern) — the ≈C$163.53/mo cost floor falls on each end user who wants Canada TSX data, not on
> the project, so it is not itself a blocker once the EULA is confirmed.

## 3. Non-negotiable invariants (both specs)

No code ships in this note for either country's equity-index feature — StatCan Composite/60 is
closing as a documented source gap (§2.3(ii)), not proceeding to build — so no identity/unit/
no-proxy/time/completeness/provenance invariant is at risk of violation this round. The existing
`_validate_symbol` guard already rejects `DSEX`/`DS30`/`DSES`/any TSX symbol before network,
unchanged. The one code change proposed (§5, CAN macro regression) touches only test/docs surface,
zero production logic, zero public-API/snapshot change (`get_indicator` already accepts any ISO3
string). "Compatibility" requirement (existing 8 `indices.world` symbols behaviorally unchanged)
is trivially satisfied — `world_sources.py`/`world_client.py` are untouched by this batch. Per the
PO ruling (§2.3(ii)), IF StatCan/TMX reuse rights are later proven, the "never silent partial
data" invariant becomes the central design constraint for that future follow-up note: any served
value MUST carry an unmissable frequency + last-observation + provenance + mechanical end-gap
disclosure, never presented as a current/live quote, never coerced into `PriceHistory` — this is
now a binding constraint on any future build, not an open question.

## 4. Architecture / capability-routing comparison (required by both specs)

The specs ask the design note to compare "extend `indices.world()`" vs. "new country-specific
entrypoint" vs. "new global-native-index entrypoint." For both countries, every candidate is
either non-existent (Bangladesh, CAN Venture Composite) or not rights-confirmed for reuse (CAN
Composite/60, pending §2.3(ii)'s reopen criterion) or EULA-unconfirmed (TMX, §2.3(iii)) — so this
comparison has no decision to make now. Building any of the three options for a source that isn't
yet rights-clear would be pure speculative architecture with no test able to prove real behavior
(the project's "no design for hypothetical requirements" rule). The PO ruling in §2.3(ii) does
pre-decide the *shape* question for a future StatCan build (archival/historical series, mandatory
frequency + last-observation + provenance + end-gap warning, never `PriceHistory` — closer to
`vnfin.macro`'s per-country `IndicatorSeries` pattern than to `indices.world()`'s daily-bar
contract), but a concrete signature/routing decision is still deferred to a follow-up note written
only once (a) or (b) in §2.3(ii)'s reopen criterion is actually met — committing to one now, with
no proven source to build against, would still be speculative.

## 5. Regression-test/docs matrix — the only proposed change (relabeled, was "RED-first")

Everything below is the complete list of proposed changes in this batch; nothing else.

**5.1 Regression test — relabeled per gate-1 finding B5, fixture contract fixed per gate-2 finding
R2-B4.** This is a **characterization/regression test**, not a RED-first test — production code is
already country-generic and requires no change, so the new test is expected to pass immediately,
not fail first. Its value is closing an untested-path gap (see §2.1's gap finding), not driving new
behavior.

**Round-2's fixture plan was internally contradictory** — it asked for a `CAN` request AND a
`/country/CAN/` URL AND a `ZZZ`/Fakeland-style response identity simultaneously, but the World Bank
adapter validates the response's `countryiso3code` against the *requested* country
(`tests/test_macro_worldbank.py:569-576`, `test_worldbank_observation_country_mismatch_raises_invalid`
— a response whose `countryiso3code` doesn't match the request raises `InvalidData`), so a fixture
can't request `CAN` and return a fabricated country code at the same time. Round-2 also said
"either" of two test files instead of pinning one seam.

**Exact proposed coverage (fixed):**
- **One** exact parametrized test, through the **public** seam
  `vnfin.macro.get_indicator("CAN", indicator, http_get=<injected fixture>)` — not an internal
  adapter call, not "either" of two files — covering all five indicators: GDP, CPI, UNEMPLOYMENT,
  GDP_GROWTH, INFLATION. Location: `tests/test_macro_worldbank.py` (matches the existing
  `WorldBankMacroSource`-focused suite; `test_macro_contracts.py`'s cross-source matrix is not the
  right fit since this test is World-Bank-specific, per country/CAN routing).
- **Retain the two real contract identifiers, since identity validation IS the behavior under
  test:** the requested country `"CAN"` (both as the `get_indicator` argument and as the fixture
  response's `countryiso3code`, so the country-mismatch guard passes) and the real per-indicator
  WDI code from `_WB_MAP` (`vnfin/macro/worldbank.py:55-72`, e.g. `NY.GDP.MKTP.CD` for GDP) as the
  URL path segment the test asserts was requested.
- **Fabricate everything else** — country *display* name, indicator *display* name, dates, and
  values — so no real provider row enters a committed fixture, matching the established
  `ZZZ`/`Fakeland`-*display*-name convention (`tests/test_macro_worldbank.py:1-33`) applied to a
  *real* identity rather than a fake one (this is the corrected, non-contradictory version of the
  round-1 claim about "hardcoded VNM/USA" fixtures — the existing suite in fact already mixes a
  real country/indicator identity axis with fabricated display content in some tests; the new CAN
  test follows that same pattern explicitly).
- Assert per indicator: exact requested path/WDI code was sent; `country == "CAN"`; provider
  indicator identity + non-empty fabricated name; `source == "worldbank"`; canonical
  `unit`/`value_unit` and indicator-specific `currency` (GDP→USD, everything else→`None`, per
  `CANONICAL_CURRENCY` in `vnfin/macro/indicators.py:127-139`); `Frequency.ANNUAL`; Jan-1 dates;
  ascending, non-empty points; zero live network calls (spy on `http_get`).
- **"No Canada-specific production branch was added" is a diff-review invariant** (checked by
  reading the diff — the adapter stays purely ISO3-generic), **not a runtime test assertion** —
  round-2 conflated the two.
- This offline/mocked test proves the *code path*, not live provider availability — it must NOT be
  presented as proof the real World Bank API currently serves CAN. The live-probe evidence in §2.1
  stays a separate, explicitly-labeled one-off check; a durable live-availability claim would need
  a separate opt-in live healthcheck/receipt (existing project pattern for other sources).

**5.2 Docs — three corrections, not one addition.**

1. Broaden `docs/tutorials/macro-and-fx.md:3` beyond "Use this guide for Vietnam macro indicators
   and VND FX reference rates" to state the macro API is cross-country (VNM is the running example,
   not the only supported country), and add a Canada example showing **all five** indicators the
   note claims are confirmed (gate-2 finding R2-B5 — round-2's proposed block only showed 3 of 5,
   contradicting its own "all five confirmed" claim), explicitly contrasting CPI (index **level**)
   with INFLATION (**%** rate) since both apply to the same country:
   ```python
   canada_gdp = vnfin.macro.get_indicator("CAN", MacroIndicator.GDP)             # current US$
   canada_cpi = vnfin.macro.get_indicator("CAN", MacroIndicator.CPI)             # index level
   canada_unemployment = vnfin.macro.get_indicator("CAN", MacroIndicator.UNEMPLOYMENT)  # %
   canada_gdp_growth = vnfin.macro.get_indicator("CAN", MacroIndicator.GDP_GROWTH)      # % YoY
   canada_inflation = vnfin.macro.get_indicator("CAN", MacroIndicator.INFLATION) # % YoY — NOT the same as CPI
   ```
2. Correct `docs/sources/macro-worldbank.md:57` — it currently says CPI resolves to DBnomics, but
   World Bank now maps CPI too (`FP.CPI.TOTL`, `vnfin/macro/worldbank.py:62`) and is first in
   chain order, so CPI actually resolves via **World Bank** (see §2.1's corrected fact above).
3. Correct `docs/sources/macro-worldbank.md:41` — the `IndicatorSeries(...)` shape line currently
   shows `currency="USD"` as if it were a general default; per `CANONICAL_CURRENCY`
   (`vnfin/macro/indicators.py:127-139`) only `GDP` carries `"USD"`, every percent/index indicator
   carries `None`. Reword so this isn't read as a universal default.

**5.3 No changes** to `docs/sources/indices-world.md`, `vnfin/indices/world_sources.py`,
`vnfin/indices/world_client.py`, `CHANGELOG.md` public-API section, or the public-API snapshot —
nothing new ships to the public surface in this note.

**5.4 Issue resolution comments — same shape for both issues now (revised, PO ruling incorporated).**
Per the round-2 gate's "immediate issue plan," draft close comments for both, to be posted only
after this design note PASSes:

- **#199:** close comment following the `tasks/182-close-comment.md` structure (candidate table +
  numbered reopen criteria, per §1.2).
- **#200:** the macro half is not closed — it proceeds to implementation (§5.1/§5.2) after this
  gate PASSes, then gets its own resolution comment documenting the confirmed cross-country
  coverage. The equity-index portion closes as a documented source gap with three reopen criteria
  (§2.3(i)/(ii)/(iii): Venture — any lawful native source; Composite/60 — StatCan/TMX rights proof;
  TMX generally — EULA confirmation). Do not park #200 waiting indefinitely for a licence response
  — close now, reopen on proof, per the gate's explicit instruction not to hold either issue open
  pending an unresolved external answer.

## 6. Clean-room record

Both source-vetting passes were redone across round-2 and round-3 by fresh research agents plus my
own direct verification, under the mandatory VNStock exclusion, appended to every search query:
`-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"`. No VNStock or
VNStock-derived repository, site, package, snippet, or documentation was searched, opened, read,
cited, or used at any point in either report (see each report's own clean-room statement). Durable
reports, committed to this repo (gate-1 finding B3 — no longer `/tmp` scratch paths):
`docs/research/2026-07-25-bd-dse-source-vetting.md`,
`docs/research/2026-07-25-can-tsx-source-vetting.md`. Raw responses (curl bodies, CSV downloads)
were not committed — only redacted/summarized evidence and row counts, per the project's
runtime-fetch-only / no-bundled-provider-data policy. Sources actually consulted: official DSE
domains (`dsebd.org`), TradingView, Investing.com, Alpha Vantage, CEIC, Mendeley, Kaggle, BSEC,
Bangladesh Bank, Stooq, FMP, Marketstack (Bangladesh); S&P Dow Jones Indices, TMX Group/TMX
Datalinx, Bank of Canada Valet, Statistics Canada (Open Licence FAQ + program/cube/series metadata
via the WDS REST API), Alpha Vantage, Twelve Data, Stooq, FMP, Marketstack (Canada). All unrelated
to and independent of VNStock/finkit. I independently reproduced the Alpha Vantage `INDEX_CATALOG`
evidence (317 rows, zero Bangladesh/Canada matches), the StatCan Open Licence FAQ's third-party-IP
exclusion, the table's TMX/Bank-of-Canada source footnotes, and its "no longer being updated as of
November 1, 2023" footnote — all via my own direct `curl` calls on 2026-07-25, cross-checked
against the reviewer's independent WDS replay.

## 7. Required transition

No implementation before this gate. Requesting final re-gate from `vnfin-oss-reviewer` with the
exact new commit SHA of this round-3 note, addressing all findings from both prior gates:
gate-1 B1–B6, and gate-2 R2-B1 (StatCan reuse-rights correction), R2-B2 (exact per-vector spans/
inactive status), R2-B3 (Twelve Data/CEIC/BSEC-Bangladesh-Bank/DSE-redistribution category
corrections), R2-B4 (CAN fixture contract fix), R2-B5 (docs completeness + line-range fix). The
scope question that was open after round-2 is now closed — the PO ruling in §2.3(ii) is
incorporated directly, no further round-trip needed on that point. On PASS: implement §5 only (CAN
macro characterization test + 3-part docs correction), then post the #199 close comment and the
#200 macro-implemented + equity-index-closed resolution comment (§5.4) — per the gate-2 "immediate
issue plan," do not park either issue waiting indefinitely for a licence response.
