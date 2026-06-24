# #193 BUILD SPEC — `vnfin.indices.world` coverage + keyless-reliability (TDD, gate-binding)

**Authority chain:** design note `tasks/193-world-index-design.md` (commit `9c219b2`) → reviewer GATE
(`~/tools/vnfin-oss-reviewer/reviews/gate-202606241410-issue193-design-note.md`, APPROVED to TDD).
This file is the concrete how; the gate rulings below are **binding**.

**Method:** TDD — Red (failing tests) → Green (min code) → Refactor. Runner: `.venv/bin/python -m pytest`.
**Clean-room:** zero VNStock; runtime-fetch / no bundled data / no redistribution; synthetic fixtures only.
**Snapshot `tests/snapshots/public_api_v0_2_0.json` STAYS FROZEN — every change is additive. Do NOT run `scripts/dump_api_surface.py`.**

---

## Gate rulings (binding — Codex×2 verifies against these)

- **Q1 SHIP ALL 5** symbols, loudly labeled. Document the FX-embedding + "ETF ≠ raw index" caveat PROMINENTLY in `docs/api.md` + `docs/sources/indices-world.md` (not just a token).
- **Q2 BOTH** proxy signals; `proxy_for` is a **MUST-HAVE structured field** (not token-only). Proxy-labeling test FAILS if a proxy is served without BOTH the `proxy_for` field AND the `proxy_substitution` token.
- **Q3 DEFER `adjusted_close`** — do NOT add it to `PriceBar`. Instead document LOUDLY (api.md + source doc) that v1 world series are **PRICE-RETURN, not total-return** (dividends not reinvested; material over 10–25y).
- **Q4** synthetic `http_get=` injection IS the accepted "VCR fixture"; reuse the proven #177 AV `TIME_SERIES_DAILY` shape. One synthetic payload per (symbol, source).
- **Q5** proceed on documented-assumption for AV ETF coverage + **HARD RUNTIME GUARD**: if AV returns empty / error / no-data for an allowlisted symbol → `InvalidData` **naming the symbol**; NEVER an empty or fabricated series.
- **MissingKey vs AllSourcesFailed cleanly branched** (detail below). **Token bijection SWEEP 46→47.** **Snapshot frozen.**

---

## 1. Per-symbol mapping table — single source of truth (in `vnfin/indices/world_sources.py`)

Replace the SPY-pinned constants with a declarative mapping. All 5 series are served via AlphaVantage
`TIME_SERIES_DAILY` in **USD** (US-listed instruments). Suggested frozen spec + dict:

```
@dataclass(frozen=True)
class _WorldIndexSpec:
    symbol: str          # canonical asked symbol (UPPER)
    av_ticker: str       # AV TIME_SERIES_DAILY symbol actually fetched
    value_unit: str      # explicit; all USD
    currency: str        # "USD"
    index_name: str      # human label for warnings/docs
    proxy_for: str | None # None when av_ticker IS the asked instrument; else the asked symbol
    fx_pair: str | None   # e.g. "USD/JPY" for the proxy FX-embed note; None when not a proxy
```

| key (asked) | av_ticker | value_unit | index_name | proxy_for | fx_pair |
|---|---|---|---|---|---|
| `SPY` | `SPY` | `USD/share (SPY ETF, S&P 500 proxy)` | S&P 500 | `None` | `None` |
| `QQQ` | `QQQ` | `USD/share (QQQ ETF, Nasdaq-100 proxy)` | Nasdaq-100 | `None` | `None` |
| `^N225` | `EWJ` | `USD/share (EWJ ETF)` | Nikkei 225 | `^N225` | `USD/JPY` |
| `^SSEC` | `FXI` | `USD/share (FXI ETF)` | SSE Composite | `^SSEC` | `USD/CNY` |
| `^STI` | `EWS` | `USD/share (EWS ETF)` | Straits Times Index | `^STI` | `USD/SGD` |

- **Keep `SPY`'s `value_unit` string EXACTLY** `"USD/share (SPY ETF, S&P 500 proxy)"` (existing tests assert it).
- `SPY`/`QQQ` are NOT proxies (caller asked for the ETF; got the ETF → `proxy_for=None`, no proxy token).
- `^N225`/`^SSEC`/`^STI` ARE proxies (caller asked the index; served a USD ETF → `proxy_for=<asked>` + token).
- Note for docs: EWJ=MSCI Japan ≠ Nikkei 225; FXI=FTSE China 50 ≠ SSE Composite; EWS=MSCI Singapore ≠ STI.

## 2. AlphaVantageIndexSource — fetch the per-symbol AV ticker (currently hard-pinned to SPY)

Today `get_history` hard-pins `params["symbol"] = _PROVIDER_SPY` (`world_sources.py:144`) and hard-codes
`value_unit=SPY_VALUE_UNIT`, `provider_symbol=_PROVIDER_SPY`. Change to:
- Resolve the `_WorldIndexSpec` for the (canonicalized) `symbol`. Unknown/blank symbol → default to the SPY spec
  (preserves `test_av_blank_symbol_arg_defaults_spy` + direct-source tests; the client gates membership).
- Fetch `params["symbol"] = spec.av_ticker`.
- Return `PriceHistory(... value_unit=spec.value_unit, currency=spec.currency, provider_symbol=spec.av_ticker,
  proxy_for=spec.proxy_for, symbol=canonical ...)`.
- **Q5 guard:** the `"Error Message"` envelope branch (`world_sources.py:154`) and the missing-`Time Series (Daily)`
  branch (`:167`) MUST name the asked symbol in the `InvalidData` message (e.g. `f"{NAME}: {symbol}: ..."`). An
  uncovered AV ticker (AV returns an Error envelope / no series) → `InvalidData` naming the symbol, never empty.
  (The existing per-window `EmptyData` "no bars in requested window" stays — that is a legit empty window, distinct.)
- Keep ALL existing value-sanity guards (positivity, OHLC-invariant, dup-date, non-finite, redaction). Do not weaken.

## 3. `PriceHistory.proxy_for` — additive structured field (`vnfin/models.py`)

Add after `attempts` (line 96, last field) — appended + defaulted, so the frozen snapshot stays green:
```
    proxy_for: Optional[str] = None
```
Docstring: "When set, the series is a labeled proxy: the caller asked for this index symbol (e.g. `'^N225'`)
but a US-listed ETF in USD was served (see `provider_symbol` for the actual instrument). `None` for a direct
(non-proxy) result. A consumer detects a proxy via this field — never by regexing `warnings`."
Leave `_df_attrs` unchanged (proxy_for is provenance metadata, like `provider_symbol`, which is also not in it).

## 4. `proxy_substitution` warning token — mirror `fallback_instrument_served` exactly

In `world_client.py`, alongside `_substitution_warnings`, add `_proxy_warnings(hist)` appended in `_finalize`
(the failover seam, so it survives like #179). Emit when `hist.proxy_for is not None`. Build from the mapping:
```
f"proxy_substitution: requested {asked} ({index_name}) served as {av_ticker} "
f"(USD ETF proxy, not the raw {index_name} index; embeds {fx_pair} FX) — not a faithful tracker"
```
The literal `"proxy_substitution:` MUST appear in `vnfin/` source (f-string is fine — `_normalize` in
`tests/_warning_token_scan.py` takes the segment before the first `:`, and the #180 lockstep substring check
sees `"proxy_substitution`). Then in the SAME commit:
- Add `"proxy_substitution"` to `_WARNING_TOKENS_180` in `tests/test_docs_contract.py` (46 → **47**).
- Add a row to the `## Warning tokens` table in `skills/vnfin/SKILL.md` (accessor `indices.world`).
- Both `test_skill_warning_tokens_section_in_lockstep_with_code` (#180) AND the #188 forward-scanner must pass.

`_finalize` becomes: `warnings = tuple(hist.warnings) + self._substitution_warnings(hist) + self._proxy_warnings(hist)`.
A proxy result therefore carries BOTH `proxy_for=<asked>` (field) AND a `proxy_substitution:` warning (token).

## 5. `MissingKey` exception + clean branch (`vnfin/exceptions.py` + `world_client.py`)

Add to `exceptions.py` (and `__all__`):
```
class MissingKey(VnfinError):
    """A BYOK source needs an API key that is not set, and no keyless fallback could serve the request."""
    def __init__(self, symbol, env_var="ALPHAVANTAGE_API_KEY"):
        self.symbol = symbol; self.env_var = env_var
        super().__init__(
            f"world index {symbol}: no {env_var} configured and no keyless source is reachable from "
            f"this environment; set {env_var} or pass api_key= to use world-index data server-side")
```
**MUST contain the literal `ALPHAVANTAGE_API_KEY`** and the symbol. **No trail enumeration** (the #157 lesson —
do not fold per-source attempts into the message).

Branch (robust, NOT message-matching): in `FailoverWorldIndexClient.get_history`, wrap `self._engine.run(...)`:
```
try:
    hist = self._engine.run(start, end, interval)
except AllSourcesFailed:
    if not any(getattr(s, "has_key", False) for s in self.sources):
        raise MissingKey(canonical) from None   # no key anywhere + chain failed → config error
    raise                                         # key WAS set but AV genuinely failed → AllSourcesFailed
```
- **No key + walled keyless fallback → `MissingKey`.** **Key set + AV throttle/network fail + fallback down →
  `AllSourcesFailed` (unchanged).** When the (synthetic) keyless fallback SERVES, the chain succeeds → neither
  error (existing fallback-warning behavior preserved). Test BOTH branches.

## 6. `_validate_symbol` — enumerate the full supported set (`world_client.py:202-214`)

Supported set is now the mapping keys: `SPY, QQQ, ^N225, ^SSEC, ^STI`. Both `InvalidData` branches must list the
full set (sorted/stable). Keep case-insensitive canonicalization (`.strip().upper()`); `^` symbols pass through.

## 7. Stale-fact sweep (the "feature flips a stale fact" lesson — repo-wide, pass 1)

Replacing the no-key `AllSourcesFailed` path with `MissingKey`, and SPY-only with 5 symbols, makes several
statements stale. GREP THE WHOLE REPO and fix every hit in this change:
- `vnfin/indices/world_sources.py:24-27` docstring ("world('SPY') raising AllSourcesFailed is the EXPECTED
  outcome") → now `MissingKey`. Also the module/class docstrings that say "S&P 500 only" / "SPY only".
- `vnfin/indices/world_client.py` docstrings ("v1 supports symbol=\"SPY\" only", line 43-46 comment, 178-189).
- `docs/design/world-index-sp500.md`, `docs/sources/indices-world.md`, `docs/api.md`, `skills/vnfin/SKILL.md`.
- Any test/comment asserting "only SPY". Sweep: `grep -rn "only SPY\|SPY only\|AllSourcesFailed.*EXPECTED\|S&P 500 only"`.

## 8. Docs (public-API change ⇒ docs + skill + CHANGELOG in the same change)

- `docs/api.md` `indices.world`: supported-symbol table (asked → served ticker → unit), all-USD note, proxy
  semantics (`proxy_for` + `proxy_substitution`), the **two prominent caveats** — (1) USD ETF proxies embed FX +
  are not faithful trackers (EWJ≠Nikkei etc.); (2) **PRICE-RETURN not total-return** (no dividend reinvestment,
  material over 10–25y) — and the `MissingKey` contract (server needs `ALPHAVANTAGE_API_KEY`; keyless Stooq is
  residential-only / dead from datacenters).
- `docs/sources/indices-world.md`: AV BYOK is the only server-usable source; Stooq residential-only; the two
  caveats; runtime-fetch/no-redistribution disclaimer; terms posture (Yahoo NOT used — ToS prohibits automated
  access + redistribution; Stooq ambiguous/tolerated). No vendored market data.
- `CHANGELOG.md`: one entry (coverage + reliability + MissingKey + proxy labeling).
- `skills/vnfin/SKILL.md`: `proxy_substitution` token row (§4) + update the `world` section (5 symbols, MissingKey,
  proxy, caveats).

## 9. Tests (TDD; `tests/test_indices_world.py` synthetic injection — RED first)

Keep ALL existing SPY/^SPX tests green (the SPY chain + `fallback_instrument_served` behavior is unchanged). Add:
- **Happy path per new symbol** (`QQQ`,`^N225`,`^SSEC`,`^STI`): typed `PriceHistory`, `source="alphavantage"`,
  `currency=="USD"`, correct `value_unit`, `provider_symbol==av_ticker`, and (via a `recorder`) assert the AV
  request used `params["symbol"]==av_ticker` (QQQ→QQQ, ^N225→EWJ, ^SSEC→FXI, ^STI→EWS).
- **Proxy-labeling** (the never-silent guard): for each of `^N225`/`^SSEC`/`^STI`, the result has BOTH
  `proxy_for==<asked>` AND a `warnings` entry starting `"proxy_substitution:"`. FAILS if EITHER is missing.
  For `SPY`/`QQQ`: `proxy_for is None` AND no `proxy_substitution` warning.
- **Unit-correctness**: each symbol's `value_unit` is the USD ETF unit (assert proxies are USD, NOT the local
  currency — guards the ETF-in-USD-vs-index-in-local-currency trap).
- **MissingKey**: no-key AV (`api_key=None`) + anti-bot Stooq → `MissingKey`; assert `"ALPHAVANTAGE_API_KEY"` and
  the symbol are in `str(exc)`. **AllSourcesFailed retained**: keyed AV throttle + anti-bot Stooq → `AllSourcesFailed`
  (the existing `test_both_down_raises_all_sources_failed` already covers this — keep it green).
- **Q5 guard**: AV `"Error Message"` envelope for an allowlisted symbol → `InvalidData` naming the symbol;
  AV missing-`Time Series (Daily)` → `InvalidData` naming the symbol.
- **Unsupported symbol**: update `test_non_spy_symbol_clear_error` — `QQQ` is now VALID (remove it); keep
  `AAPL`,`^GSPC`,`spx`,`""` raising `InvalidData`; assert the message lists the supported set.
- **Token lockstep**: `proxy_substitution` in `_WARNING_TOKENS_180` + SKILL table (the #180/#188 tests enforce).

## 10. Acceptance (green merged tree before reviewer)

1. `.venv/bin/python -m pytest -q` — FULL suite green (incl. `test_docs_contract`, `test_public_api_surface`,
   `test_indices_world`).
2. Snapshot UNCHANGED (no `dump_api_surface.py` run); surface test green proves additivity.
3. Token tuple == 47; `proxy_substitution` in SKILL table; #180 + #188 green.
4. Stale-fact sweep (§7) clean — no "only SPY" / "AllSourcesFailed EXPECTED (no-key)" left.
5. `grep -rni vnstock` in changed files = 0. No secrets. No vendored market rows.
Return a diff/summary; do NOT push, close, or message the reviewer (the orchestrator integrates + routes).
