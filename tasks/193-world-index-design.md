# #193 — `vnfin.indices.world`: coverage + keyless-from-server reliability — DESIGN NOTE

**Status:** DESIGN-NOTE-FIRST (reviewer gate pending — no build until gated).
**Spec:** `/tmp/spec-193.md` (tech-lead packet). **Tree:** HEAD `5b62b1e`.
**Architecture anchors verified against the live tree** (token count, file:lines) — see §8.

---

## 0. TL;DR / recommendation

The spec's **central unknown — "does any keyless source work from a datacenter server?" — is now empirically answered: NO.** Both reviewer-named candidates are blocked from this server's IP:
- **Yahoo chart v8** (`query1/query2.finance.yahoo.com`): hard **HTTP 429 "Too Many Requests"** on the API hosts, even after a full cookie + `getcrumb` handshake (the consumer `finance.yahoo.com` HTML loads fine at 200 — the block is on the JSON API host, not my request rate).
- **Stooq** (`stooq.com/q/d/l/`): a **JavaScript anti-bot wall** (`"This site requires JavaScript to verify your browser"`) on every ticker — CSV never served.

Per the spec's own decision rule ("**if none works keyless → ship the Axis-B floor only … do not fake a keyless path**"), the recommended outcome is:

- **Axis B (floor, ships regardless):** add a `MissingKey` exception naming `ALPHAVANTAGE_API_KEY`; `world()` raises it (instead of the opaque `AllSourcesFailed: stooq: anti-bot challenge`) when no key is set and the keyless fallback is walled. **AlphaVantage (BYOK) becomes the only server-usable source**, not a "fallback".
- **Axis A (coverage):** extend the allowlist `SPY → SPY, QQQ, ^N225, ^SSEC, ^STI` via a declarative table. SPY/QQQ are US-listed ETFs served directly in USD; the three Asian indices are served as **loudly-labeled US-listed ETF proxies in USD** (`EWJ`/`FXI`/`EWS`) — never silently as the raw index.
- **Honest caveat (key open question Q1):** because the only server-usable source serves **US-listed ETFs in USD**, the spec's hoped-for local-currency units (JPY/CNY/SGD) are **not achievable in v1**, and a USD ETF proxy **embeds USD/local FX** — material for a rebasing chart. Labeling must convey this; or defer the 3 Asian symbols. Reviewer to rule.

---

## 1. Empirical probe (the spec's core deliverable)

**Method:** real server egress (not sandboxed — a sandbox egress allowlist would conflate "sandbox blocked it" with "the source blocked it", the classic false-negative). Read-only GETs, browser UA, signals only (no price rows captured/committed). Scripts: `/tmp/vnfin-193-probe.py`, `/tmp/vnfin-193-probe2.py`.

### 1a. Yahoo chart v8 — `query{1,2}.finance.yahoo.com/v8/finance/chart/<sym>?period1=&period2=&interval=1d`

| Step | Result |
|---|---|
| Bare GET, 7 symbols × 2 hosts | **429** `text/html` 19 bytes, ALL (`SPY QQQ ^GSPC ^NDX ^N225 000001.SS ^STI`) |
| Cookie handshake (`fc.yahoo.com` 404 + `finance.yahoo.com/quote/SPY` 200 + `finance.yahoo.com` 200) | cookies collected: `['A3']` — HTML site reachable |
| `GET /v1/test/getcrumb` (with cookie) | **429** (crumb never issued) |
| `GET chart` (with cookie, no crumb obtainable) | **429 `Too Many Requests`**, ALL 5 allowlist symbols |

→ The block is on the API host (`query*`) for this datacenter IP, not a rate-limit I tripped (429 on the very first request) and not the crumb gate (the crumb endpoint itself 429s). **Yahoo chart is NOT keyless-usable from a server.** (And per §2, Yahoo's ToS prohibits automated access anyway.)

### 1b. Stooq — `stooq.com/q/d/l/?s=<ticker>&i=d`

| Tickers probed | Result |
|---|---|
| `spy.us`, `qqq.us`, `^spx`, `^ndq`, `^nkx`, `^shc`, `^sti` | **HTTP 200 but body = JS anti-bot challenge** (796 bytes): `<!DOCTYPE html>…<noscript>This site requires JavaScript to verify your browser…</noscript><script nonce=…>` — CSV header `Date,Open,…` never returned, on EVERY ticker. |

→ Confirms the spec's premise. **Stooq CSV is NOT keyless-usable from a server** (the anti-bot wall is host-level; alternate paths/tickers on `stooq.com` won't bypass it).

### 1c. Other keyless candidates (considered)
- **FRED** (`SP500`, `NIKKEI225` series): close-only, not OHLCV → fails the `PriceHistory` shape contract; also key-gated. Rejected.
- All other free index-OHLCV feeds (Tiingo/TwelveData/FMP/Marketstack/Nasdaq Data Link) are key-gated (BYOK), i.e. not "keyless". Rejected as keyless candidates.

**Probe verdict (signal, not the source verdict — that's the reviewer's): no keyless-from-server OHLCV index source exists. Ship the Axis-B floor.**

---

## 2. Source / legal posture (clean-room; full report in research strand)

VNStock exclusion stated and clean (world/US/Asia indices — zero blacklist exposure).

| Source | Posture | Decision |
|---|---|---|
| **AlphaVantage (BYOK)** | The user supplies their own key → the user's own ToS relationship with AV. Already the project's primary world source (#177); same key as #140 news. | **Primary (and only server-usable) source.** |
| **Stooq** | ToS body not machine-readable in 2026; no explicit permit/prohibit; opaque provenance; daily quota. Runtime-fetch tolerated; redistribution treat-as-prohibited. Already shipped as the #177 keyless fallback. | **Keep the existing fallback** (runtime-fetch/no-redistribution, no bundled data — the HNX posture). It won't work from a server, but it's harmless and already there; removing it is out of scope. |
| **Yahoo chart** | ToS **explicitly prohibits automated access AND redistribution**; data from ICE/LSEG/CSI/S&P/CME (each with own bans); official API discontinued 2017; `yfinance` itself says "personal use only". | **Do NOT add.** Blocked (§1a) AND ToS-prohibited. |

Every runtime source documents terms + a runtime-fetch/no-redistribution disclaimer in `docs/sources/` (mandated by the spec). No vendored market data beyond tiny offline synthetic fixtures.

---

## 3. Axis A — per-symbol source / unit / proxy table

Replace the `SUPPORTED_SYMBOL = "SPY"` string (`world_client.py:46`) with a declarative table. All series are served via **AlphaVantage `TIME_SERIES_DAILY`** (the existing adapter), all in **USD** (US-listed instruments):

| Allowlist symbol | Index (asked) | AV-served ticker | `value_unit` | Proxy? (`proxy_for`) | Note |
|---|---|---|---|---|---|
| `SPY` | S&P 500 | `SPY` | USD | — | the existing v1 semantics (S&P 500 via SPY ETF) |
| `QQQ` | Nasdaq-100 | `QQQ` | USD | — | caller asked for the ETF itself; not a proxy |
| `^N225` | Nikkei 225 (JPY) | `EWJ` | **USD** | `^N225` | `EWJ`=MSCI Japan ETF — ≈ Japan large-cap in **USD**, **not** the JPY index |
| `^SSEC` | SSE Composite (CNY) | `FXI` | **USD** | `^SSEC` | `FXI`=FTSE China 50 ETF — ≈ China large-cap in **USD**, **not** the CNY index |
| `^STI` | Straits Times (SGD) | `EWS` | **USD** | `^STI` | `EWS`=MSCI Singapore ETF — ≈ Singapore in **USD**, **not** the SGD index |

**Two honesty flags baked into the table (the never-silent-wrong-data core):**
1. The proxies are **not even precise trackers** of the asked indices (MSCI Japan ≠ Nikkei 225; FTSE China 50 ≠ SSE Composite; MSCI Singapore ≠ STI). This makes loud labeling *doubly* essential.
2. A USD ETF proxy **embeds USD/local FX** — a rebased `EWJ` series ≠ a rebased Nikkei-in-JPY series (they diverge by the yen's move). For vf-advisor's rebasing chart this is a real distortion — see **Q1**.

---

## 4. value_unit correctness (invariant 2)

`value_unit` **already exists** on `PriceHistory` (`models.py:91`). Per-symbol it is **USD for all 5** (every served instrument is a US-listed ETF). The spec's JPY/CNY/SGD units are **not achievable in v1** (they'd require a raw-index source, all of which are blocked/key-gated/wrong-shape). The result's `value_unit` MUST match the series actually returned (USD), and the proxy label (§5) makes the ETF-in-USD-vs-index-in-local-currency distinction explicit. Unit-correctness test asserts `value_unit == "USD…"` for each symbol.

---

## 5. Proxy labeling (invariant 2 — never silent substitution)

Three independent, already-or-minimally-additive signals make a proxy non-silent:
1. **`provider_symbol`** (exists, `models.py`) carries the actual served ticker (`EWJ`/`FXI`/`EWS`) — ≠ the asked symbol.
2. **`value_unit`** = USD (≠ the asked index's local currency).
3. **NEW warning token `proxy_substitution`** (mirrors the existing `fallback_instrument_served` precedent at `world_client.py:48-51`), e.g.: `proxy_substitution: requested ^N225 (Nikkei 225) served as EWJ (iShares MSCI Japan ETF, USD) — a USD ETF proxy, not the raw index; embeds USD/JPY FX`.

**Recommendation:** the token is the **must-have** (loud, human-readable, already a repo pattern). An additive **`proxy_for: Optional[str] = None`** on `PriceHistory` (machine-readable: the asked index when a proxy was served) is a nice-to-have — **Q2** for the gate. Proxy-labeling test FAILS if a proxy is served without the token (and, if added, the field).

---

## 6. Axis B — `MissingKey` (the floor; ships regardless of §1)

- **Add** `class MissingKey(VnfinError)` to `vnfin/exceptions.py` (none exists today — verified) + `__all__`. Carries the env-var name + actionable message.
- **`world()` raises `MissingKey`** when: the AV source is unavailable *specifically because no key is set* (today it raises `SourceUnavailable("…no ALPHAVANTAGE_API_KEY configured…")`, `world_sources.py:127`) **AND** every keyless fallback failed (Stooq anti-bot). Message names the var and the fix:
  `world index data requires ALPHAVANTAGE_API_KEY in a server environment; the keyless fallback (Stooq) is blocked from datacenter IPs. Set ALPHAVANTAGE_API_KEY or pass api_key=.`
- **Keep `AllSourcesFailed`** for the genuine case: a key WAS provided but AV failed for another reason (throttle/network) — that's a real all-sources failure, semantically distinct from missing-key. (Distinguish by inspecting the AV attempt's reason / a flag on the no-key `SourceUnavailable`.)
- Error-path tests: (a) no key + walled keyless → `MissingKey` whose message contains the literal `ALPHAVANTAGE_API_KEY`; (b) unsupported symbol → `InvalidData` listing the new supported set; (c) anti-bot/empty body with a key set → `AllSourcesFailed` (or fallback), never a fabricated series.

---

## 7. adjusted_close (invariant 1) — AV-tier constraint (Q3)

`PriceBar` has **no `adjusted_close`** field (verified; only `PriceHistory.adjustment_policy = RAW`). AV's **free `TIME_SERIES_DAILY` returns raw OHLCV only**; adjusted close needs `TIME_SERIES_DAILY_ADJUSTED`, which is a **premium** AV endpoint. So:
- **Recommendation:** add an additive `adjusted_close: Optional[float] = None` to `PriceBar` (appended + defaulted → snapshot-safe), populated only when the served payload carries it (premium `DAILY_ADJUSTED`), **`None` otherwise — never fabricated**. v1 with the free tier leaves it `None` and `adjustment_policy=RAW` already documents that. Alternative: defer `adjusted_close` entirely. **Q3** for the gate.

---

## 8. Surface impact (additive; snapshot frozen) — verified anchors

- `world()` `vnfin/indices/world_client.py:166`; `SUPPORTED_SYMBOL` `:46`; `_validate_symbol` enumerates the supported set `:202-214`.
- `PriceHistory` `vnfin/models.py:76` (has `value_unit`/`source`/`provider_symbol`/`warnings`; **no** `adjusted_close`/`proxy_for`); `PriceBar` `:48`.
- Source chain `default_world_index_sources()` `world_client.py:55-69` → `[AlphaVantage(BYOK), Stooq]`; AV key read `world_sources.py:89`; no-key error `:127-128`; `AllSourcesFailed` `vnfin/exceptions.py:71`.
- Exceptions: **no `MissingKey`** (`exceptions.py`, verified) → add it.
- **`_WARNING_TOKENS_180` = 46** (verified by import — NOT 37; the arch-map sub-agent miscounted, caught pre-gate). New `proxy_substitution` token → **46→47**: add to the tuple (`tests/test_docs_contract.py`) + `skills/vnfin/SKILL.md` table + emit as a literal stem at a `warnings=` sink (#188 forward-scanner). **Gate on the bijection SWEEP, not the count.**
- Snapshot `tests/snapshots/public_api_v0_2_0.json` **stays frozen** (no regen): new allowlist symbols = no surface change; `MissingKey` export = additive; new `proxy_for`/`adjusted_close` = additive-appended-defaulted; `proxy_substitution` = test/doc only. **Never run `dump_api_surface.py` mid-feature.**
- Public signature `world(symbol, start, end)` unchanged — additive.

---

## 9. Test matrix (offline-first, never live in CI)

The existing world-index tests use **synthetic `http_get=` injection** with committed synthetic payloads (`tests/test_indices_world.py`), NOT vcrpy cassette files. This already satisfies the spec's intent (deterministic, offline, per-(symbol,source), CI never touches live). **Proposal:** continue this pattern — one synthetic payload per (symbol, source) — which IS the "VCR-style fixture" the spec means, with no new dependency and consistent with the no-real-rows rule. **Q4** for the gate (accept synthetic-injection as the VCR equivalent?). Coverage: happy-path per symbol (USD `value_unit`, `source` set, proxy token where applicable); proxy-labeling test (fails on silent substitution); the 3 error-path tests (§6); unit-correctness test (§4); token lockstep sweep.

---

## 10. Open questions for the reviewer gate

- **Q1 (the big one):** USD ETF proxies for `^N225`/`^SSEC`/`^STI` embed USD/local FX and aren't faithful trackers — for a rebasing chart that's a real distortion. **Ship all 5 with loud labeling (spec's explicit ask), OR ship SPY+QQQ faithful now and defer the 3 Asian symbols** until a raw-index source exists? (My lean: honor the spec — ship all 5, label loudly, document the FX caveat prominently.)
- **Q2:** proxy labeling = warning token only (recommended must-have), or also add the additive `proxy_for` field?
- **Q3:** `adjusted_close` — add additive `Optional[float]` per-bar (populate-when-available, premium), or defer?
- **Q4:** accept the repo's synthetic-`http_get`-injection pattern as the spec's "VCR-style fixtures"?
- **Q5:** I have **no AlphaVantage key** in this env (`ALPHAVANTAGE_API_KEY` unset) → AV's exact coverage of `EWJ`/`FXI`/`EWS` is **documented, not probed**. Confirm the proxy ETF choices, or authorize a keyed AV coverage probe during the build.

**On gate approval → TDD per §9 → merged-tree green + Codex×2 against this spec → push+close on APPROVE.**
