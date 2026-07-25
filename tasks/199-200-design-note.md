# #199 + #200 design note — native international-index source/design batch

Status: **DESIGN NOTE FOR REVIEWER GATE — no implementation yet**
Date checked: 2026-07-25 +07
Intake/spec (reviewer repo): `tasks/199-bangladesh-main-indices-spec.md` (commit `465d905`),
`tasks/200-canada-indicators-spec.md` (commit `e2cab7a`).
PO handoff: 2026-07-25 17:26, batched as one source/design gate per the shared `vnfin.indices`
native-points architecture question, Bangladesh/Canada evidence kept separate, neither a fallback
for the other.

## 0. Bottom line (revised — round-2, post-gate-1 BLOCK)

**#199 Bangladesh (DSEX/DS30/DSES): source-blocked, unchanged conclusion, now on corrected
evidence.** Recommend close as `source-gap-documented` with reopen criteria (§1.2), no ETF/CSE
proxy substitution.

**#200 Canada is NOT a clean source-blocked verdict anymore — round-2 vetting surfaced a genuine
partial candidate the round-1 pass missed.** Three separate dispositions, not one:

- **S&P/TSX Venture Composite:** source-blocked, no candidate at all. Recommend close-with-reopen
  for this identifier only.
- **S&P/TSX Composite + S&P/TSX 60:** a real, free, keyless, Open-Government-Licence source exists
  — **Statistics Canada Table 10-10-0125-01**, native index points, monthly, 1956–2023-09 — but the
  data is **stale (~2.75 years, no update since 2023-09)** and monthly-only, a materially different
  shape than the "headline"/current-sounding index the spec's product framing implies. This is a
  genuine reviewer/Boss **scope decision**, not something this note should decide unilaterally: is
  stale monthly data an acceptable v1 answer to "give me the S&P/TSX Composite," or does the
  spirit of the request require current/daily data this source cannot provide? See §2.3.
- **TMX Datalinx** (the only entity with current/daily data for all 3): downgraded from round-1's
  "legally blocked" to **inconclusive/unresolved** — a real self-serve paid BYOK path plausibly
  exists (each end user brings their own TMX token/account, same shape as the existing Alpha
  Vantage pattern, so the ≈C$164/mo cost floor falls on the end user, not the project), but the
  exact EULA text confirming individual-automated-use permission is sign-in-gated and unread. See
  §2.3(iii).

**Net: still no implementation from this note** (per the gate's "no implementation before design
PASS" instruction) — but #200's equity-index half should NOT be closed outright the way #199 can
be; it needs one more round-trip with the reviewer on the StatCan scope question before either
"build it" or "close it" is decided. The **Canada macro** half of #200 is unaffected and already
fully served by the existing `vnfin.macro.get_indicator(iso3, MacroIndicator)` API on current
`master` — no new source, only a small additive regression-test + docs change (§5).

Because there is no lawful *current/daily* source for either country's equity indices, the
"additive API/capability routing" question the PO/specs ask for is answered as: **no new routing
is added in this note.** `vnfin.indices.world()`'s existing `_validate_symbol` gate
(`vnfin/indices/world_client.py:269-282`, runs at line 258 strictly before any client construction
or network call) already rejects any symbol outside `SUPPORTED_WORLD_SYMBOLS` with a typed
`InvalidData` enumerating the supported set — `DSEX`, `DS30`, `DSES`, and any TSX symbol would
already hit this existing guard today, correctly, with zero code change. If the reviewer/Boss
decide the StatCan monthly data is an acceptable v1 answer, that source's shape (monthly,
long-run historical, government-statistics style) resembles `vnfin.macro`'s per-country
`IndicatorSeries` far more than `indices.world()`'s daily `PriceHistory` — a real architecture
question, but one this note deliberately does NOT resolve speculatively (§4) pending that scope
decision.

## 1. #199 — Bangladesh DSEX / DS30 / DSES

### 1.1 Source-vetting evidence (revised — round-2, post-gate-1 BLOCK corrections)

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
| 8 | CEIC Data | DSEX/DS30 series exist (monthly, not daily); DSES unknown | Paid-subscription-only; even if licensed, granularity (monthly) is coarser than native daily index publication | **not exposed through a lawful API** |
| 9 | Mendeley Data / Kaggle | not freshly re-verified in round-2 | Prior finding: stock-level only (Mendeley) / DSEX-only stale 2013–2020 (Kaggle) | **inconclusive/unresolved** |
| 10 | Unofficial mirrors (`dsestocks.com`, `faysal515/bd-stock-api`, etc.) | — | Named, not opened/used, per spec's exclusion rule; inherit DSE's own copyright restriction regardless of technical feasibility | **not exposed through a lawful API** (excluded per spec rule) |
| 11 | BSEC / Bangladesh Bank | none found | Regulator/central-bank sites reachable; no evidence of an index-data publication (that is DSE's own function) | **confirmed absent** |

**No candidate is "confirmed absent + fully checked" in a way that would let a future maintainer
skip re-verification.** FMP, Marketstack, Stooq, and Mendeley/Kaggle remain genuinely
inconclusive/unresolved (sandbox/tooling-bounded, not confirmed-absent) — see the report's §"what
blocked me" per candidate. The strongest, most direct basis for the overall verdict is DSE's own
`copyright.htm`/`termsacond.htm` text (candidate 1), which independently would block redistribution
even if every other candidate turned out favorable.

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
(`vnfin/macro/client.py:478-497`) that delegates to `MacroClient.get_indicator`
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

### 2.2 Equity indices — S&P/TSX Composite / 60 / Venture Composite (revised — round-2)

Durable report, committed to this repo (addresses gate-1 finding B3):
`docs/research/2026-07-25-can-tsx-source-vetting.md`. Category labels are the same four exact
labels used in §1.1, plus one genuine fifth outcome (StatCan) that doesn't fit any of the four —
labeled explicitly as a **partial confirmed-present** below.

| # | Candidate | Coverage (3 indices) | Evidence | Category |
|---|---|---|---|---|
| 1 | S&P Dow Jones Indices (index administrator) | admin confirmed, no self-serve API found | "API Data Solutions" brochure is institutional/subscriber-oriented, no visible individual signup; every `spglobal.com` URL probed 403'd (evidence bounded by that) | **not exposed through a lawful [self-serve] API** |
| 2 | **Bank of Canada Valet API** | 0 | **Confirmed absent via a full programmatic sweep** of all 15,906 series + 2,524 groups (not a spot-check) — only incidental chart-annotation series match "TSX" in text, no real index series | **confirmed absent** |
| 3 | **Statistics Canada Table 10-10-0125-01** ("Toronto Stock Exchange statistics") | **Composite + TSX 60 present**; Venture Composite absent | **New finding, not identified in round-1.** Free, keyless, documented WDS REST API (`getFullTableDownloadCSV`), Open Government Licence. Directly downloaded+parsed the CSV (2026-07-25): "Standard and Poor's/Toronto Stock Exchange Composite Index" and "...60 Index" both present as distinct series, monthly, 1956-01 through **2023-09** (no update since, ~2.75yr stale); no "Venture" series anywhere in the 25-series table | **partial confirmed-present** (2 of 3 indices, monthly, stale) / **confirmed absent** (Venture) |
| 4 | **TMX Group / TMX Datalinx** (exclusive commercial distributor, current/daily data) | genuine native data for all 3 (per its own product descriptions) | **Corrected — round-1's legal reasoning over-reached (gate-1 finding B2).** Separated 5 questions with direct evidence: (a) code-distribution not restricted; (b) a real self-serve individual account + "Custom Queries — Pay Per Use" product exists (free account signup, ≈C$163.53/mo minimum charge); (c) the "single end user, no redistribution" clause reads as the standard per-seat licensing split (targets reselling to third parties), not a ban on an individual's own automated retrieval — mirrors the existing Alpha Vantage BYOK pattern; (d) a **documented REST API + SFTP with 1-year token auth does exist** (contradicts round-1's assumption of "no automatable API"); (e) genuinely unresolved: the exact EULA text confirming an individual's own script is "permitted use" is sign-in-gated (every TMX domain 403'd direct fetch) | **inconclusive/unresolved** (not "legally blocked" — corrected) |
| 5 | Alpha Vantage | 0 — **corrected**: round-1 wrongly used the six-US-indices doc claim without the right endpoint; round-2 used `INDEX_CATALOG` (317 rows), independently re-verified by me via a fresh `curl` on 2026-07-25 (zero `TSX\|GSPTSE\|Toronto\|Canada` matches) | AV's own documentation enumerates only US indices for the Premium OHLCV suite; `INDEX_CATALOG` catalog confirms no Canadian entry | **confirmed absent** |
| 6 | Twelve Data | 0 native instrument | 6 exact permutations tested (`GSPTSE`, `TSX`, `%5EGSPTSE`, `TSX60`, `TSXV`, `S%26P%2FTSX`) — every non-empty result was an ETF or an index-*linked* structured note, never the index itself | **confirmed absent** |
| 7 | Stooq (existing project fallback for other symbols) | Composite: plausible via cached page title only; 60/Venture: no signal | Every direct probe — including the project's own already-working `^spx` control — hit a site-wide JS proof-of-work bot wall today; Google's cached title for `^TSX` reads "S&P/TSX Composite Index" but this is third-party cache evidence, not a direct read | **inconclusive/unresolved** |
| 8 | Financial Modeling Prep | unresolved — bounded | `demo` key rejected (401, unlike AV's working demo) on every index endpoint tried; docs page 403'd | **inconclusive/unresolved** |
| 9 | Marketstack | unresolved — bounded | `demo` access_key rejected (401); docs mirror is login-gated, no substantive content | **inconclusive/unresolved** |

Per spec, ETF proxy (XIU/XIC), a futures contract, or a neighboring index remain explicitly
excluded as substitutes and were not pursued as "solutions" for any candidate above.

### 2.3 Recommendation (revised — three separate dispositions, not one)

No implementation from this note either way (gate-1 said no implementation before design PASS).
Unlike #199, #200's equity-index half should **not** be closed outright yet — it needs one more
round-trip on a genuine scope question:

**(i) S&P/TSX Venture Composite — source-blocked, clean.** No candidate anywhere. Recommend
close-with-reopen for this identifier specifically:

> Reopen if a source appears with native Venture Composite index points, lawfully retrievable
> (self-serve or a clearly licensed provider API), reachable from ordinary server/datacenter
> egress.

**(ii) S&P/TSX Composite + S&P/TSX 60 — real source found, needs a reviewer/Boss scope call
before either building or closing.** StatCan Table 10-10-0125-01 is free, keyless,
license-clear, and directly verified to carry both series as native points — but monthly and
frozen at 2023-09 (no update in ~2.75 years). This project already has a precedent for serving
honestly-labeled non-current data with a mandatory staleness/frequency disclosure (the
`series_end_gap`/`nav_end_gap`/`current_snapshot_only` pattern from #172/#175/#179), so this is
*technically* buildable without violating any non-negotiable invariant (§3) — the open question is
whether frozen 2023-09 monthly data is what "give me the S&P/TSX Composite" should honestly mean
to a caller, or whether that would be misleading regardless of disclosure. **This note does not
decide that** — it is a product-scope judgment call, not a source/legal one, and belongs with the
reviewer/Boss rather than being resolved unilaterally here (also consistent with "no design for
hypothetical/unconfirmed-shape work": StatCan's monthly/historical shape doesn't fit
`indices.world()`'s daily `PriceHistory` contract, so committing to a signature before this scope
question is answered would be premature — see §4). Proposed next step: reviewer/Boss decide
accept-stale-monthly-as-v1 vs. hold-for-TMX vs. decline entirely; only then does a follow-up
design note pick one and spec the capability-routing/signature.

**(iii) TMX Datalinx — inconclusive/unresolved, reopen criteria (not a closed door).** A
plausible current/daily BYOK path exists but the decisive EULA text is unread:

> Reopens once the specific TMX "Custom Queries" Market Data Services Agreement / EULA text
> (currently sign-in-gated) is obtained and confirms it permits an individual subscriber's own
> automated script to retrieve data under their own account/token for their own use (not
> requiring a separate "distributor" designation). If confirmed, this becomes a normal paid-BYOK
> adapter (each user brings their own TMX account, same shape as the existing Alpha Vantage
> pattern) — the ≈C$163.53/mo cost floor falls on each end user who wants Canada TSX data, not on
> the project, so it is not itself a blocker once the EULA is confirmed.

## 3. Non-negotiable invariants (both specs)

No code ships in this note for either country's equity-index feature — including for StatCan
Composite/60, pending the §2.3(ii) scope call — so no identity/unit/no-proxy/time/completeness/
provenance invariant is at risk of violation this round. The existing `_validate_symbol` guard
already rejects `DSEX`/`DS30`/`DSES`/any TSX symbol before network, unchanged. The one code change
proposed (§5, CAN macro regression) touches only test/docs surface, zero production logic, zero
public-API/snapshot change (`get_indicator` already accepts any ISO3 string). "Compatibility"
requirement (existing 8 `indices.world` symbols behaviorally unchanged) is trivially satisfied —
`world_sources.py`/`world_client.py` are untouched by this batch. If the reviewer/Boss later
approve building StatCan Composite/60, the "never silent partial data" invariant becomes the
central design constraint for that follow-up note: any served value MUST carry an unmissable
frequency (monthly) + staleness (frozen 2023-09) disclosure, never presented as a current/live
quote.

## 4. Architecture / capability-routing comparison (required by both specs)

The specs ask the design note to compare "extend `indices.world()`" vs. "new country-specific
entrypoint" vs. "new global-native-index entrypoint." For Bangladesh and for CAN Venture
Composite, there is zero servable symbol, so this comparison has no decision to make — building
any of the three options for a source that doesn't exist would be pure speculative architecture
with no test able to prove real behavior (the project's "no design for hypothetical requirements"
rule). For CAN Composite/60, a real candidate (StatCan) now exists, but its shape — monthly,
long-run historical, government-statistics-style — does not fit `indices.world()`'s daily
`PriceHistory` contract at all; it more closely resembles `vnfin.macro`'s per-country
`IndicatorSeries` pattern (annual/monthly points, explicit unit, no daily-bar assumption). Picking
a signature now, before §2.3(ii)'s scope question is answered, would still be speculative —
committing to an architecture for a feature that might be rejected on scope grounds wastes design
effort and risks anchoring the reviewer on a shape before the real question (accept-stale-data or
not) is settled. **Flagged as the fast-follow architecture question**, deliberately not resolved
here, to be picked up in a follow-up note only after the scope call.

## 5. Regression-test/docs matrix — the only proposed change (relabeled, was "RED-first")

Everything below is the complete list of proposed changes in this batch; nothing else.

**5.1 Regression test — relabeled per gate-1 finding B5.** This is a **characterization/regression
test**, not a RED-first test (round-1 mislabeled it) — production code is already country-generic
and requires no change, so the new test is expected to pass immediately, not fail first. Its value
is closing an untested-path gap (see §2.1's gap finding), not driving new behavior.

Exact proposed coverage, addressing every point in gate-1 finding B5:
- Add a `country="CAN"` case to `tests/test_macro_worldbank.py`'s happy-path parametrization (or
  `tests/test_macro_contracts.py`'s `_SOURCES` matrix), covering all five indicators the note
  claims are confirmed: GDP, CPI, UNEMPLOYMENT, GDP_GROWTH, INFLATION.
- Uses **injected `http_get`, no network**, per the project's synthetic-fixture policy
  (`docs/design/macro-no-key-byok.md:104-117`, P0.4): the country/indicator identity must stay
  **obviously fabricated** (e.g. `ZZZ`/`Fakeland`-style, matching the established convention in
  `tests/test_macro_worldbank.py:1-33` — country=`ZZZ`, indicator=`FK.TEST.IND.ZG`), never a
  real-`CAN`-looking fixture with real-looking GDP/CPI/unemployment figures. This corrects the
  round-1 note's claim that existing happy paths "hardcode VNM/USA" — they in fact use synthetic
  `ZZZ`/`Fakeland`, and the new CAN-path test must follow the same convention, not real values.
- Assert per indicator: expected `/country/CAN/indicator/{WDI_CODE}` request URL/params were
  actually sent (proves the real country code threads through, not just that *some* request
  fired); `source == "worldbank"`; provider indicator identity + non-empty name; `country == "CAN"`
  + country metadata; canonical `unit`/`value_unit` and indicator-specific `currency` (GDP→USD,
  everything else→`None`, per `CANONICAL_CURRENCY` in `vnfin/macro/indicators.py:127-139`);
  `Frequency.ANNUAL`; Jan-1 dates; ascending, non-empty points.
- Assert **no Canada-specific production branch was added** (the adapter stays purely
  ISO3-generic) and existing failover/chain-order behavior is unchanged for other countries.
- This offline/mocked test proves the *code path*, not live provider availability — it must NOT
  be presented as proof the real World Bank API currently serves CAN. The live-probe evidence in
  §2.1 stays a separate, explicitly-labeled one-off check; if durable live-availability confidence
  is wanted later, that needs a separate opt-in live healthcheck/receipt (existing project pattern
  for other sources), not implied by an offline fixture test.

**5.2 Docs — three corrections, not one addition.**

1. Broaden `docs/tutorials/macro-and-fx.md:3` beyond "Use this guide for Vietnam macro indicators
   and VND FX reference rates" to state the macro API is cross-country (VNM is the running example,
   not the only supported country), and add a Canada example showing all five indicators
   (GDP/CPI/UNEMPLOYMENT/GDP_GROWTH/INFLATION), explicitly contrasting CPI (index **level**) with
   INFLATION (**%** rate) since both apply to the same country:
   ```python
   canada_gdp = vnfin.macro.get_indicator("CAN", MacroIndicator.GDP)             # current US$
   canada_cpi = vnfin.macro.get_indicator("CAN", MacroIndicator.CPI)             # index level
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

**5.4 Issue resolution comments — different shape per issue.** #199: draft a close comment
following the `tasks/182-close-comment.md` structure (candidate table + numbered reopen criteria,
per §1.2), to be posted only after this design note is gated and the reviewer confirms disposition
(close-now-with-reopen-criteria vs. keep-open-as-source-watch, same open question
`182-close-comment.md` flagged for gold). #200: **not a close comment yet** — post an interim
status comment on #200 summarizing the three-way disposition (§2.3: Venture blocked, Composite/60
pending a scope call, TMX pending EULA), and route the §2.3(ii) scope question to the reviewer/Boss
explicitly before drafting any close/build language.

## 6. Clean-room record

Both source-vetting passes were redone in round-2 by fresh research agents under the mandatory
VNStock exclusion, appended to every search query:
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
Datalinx, Bank of Canada Valet, Statistics Canada, Alpha Vantage, Twelve Data, Stooq, FMP,
Marketstack (Canada). All unrelated to and independent of VNStock/finkit. I additionally
independently reproduced the Alpha Vantage `INDEX_CATALOG` evidence myself via a fresh `curl`
before delegating the corrected research passes (317 rows, zero Bangladesh/Canada matches).

## 7. Required transition

No implementation before this gate. Requesting re-gate from `vnfin-oss-reviewer` with the exact
new commit SHA of this revised note, addressing all six gate-1 findings (B1–B6). Open items for
the reviewer beyond a plain PASS/BLOCK verdict:

1. **#200 §2.3(ii) scope call:** does the reviewer (or should this route to Boss) accept
   stale-monthly StatCan data as an acceptable v1 answer for S&P/TSX Composite + S&P/TSX 60, or
   should the request wait for TMX EULA confirmation / stay declined? This determines whether a
   follow-up implementation-design note gets written at all for Canada's equity indices.
2. On PASS (independent of the above): implement §5 only (CAN macro characterization test +
   3-part docs correction), then post the #199 close comment (§5.4) and the #200 interim status
   comment (§5.4) — #200 does not close in this round regardless of the §2.3(ii) answer, since
   even an "accept StatCan" answer still needs its own follow-up design/implementation before
   anything ships.
