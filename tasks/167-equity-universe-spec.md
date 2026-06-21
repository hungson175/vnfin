# #167 — VN equity universe (SSI iBoard) — IMPLEMENTATION SPEC (build against THIS file)

**Status:** design-gated APPROVE-WITH-CHANGES (reviewer 08:21–08:27, 2026-06-21). All decisions locked.
**Issue:** https://github.com/hungson175/vnfin/issues/167
**Mandate:** TDD (Red→Green→Refactor), synthetic fixtures only, no real provider rows committed,
clean-room (SSI iBoard host only, ZERO VNStock). You implement ONE scoped job, stay in scope, return a
diff + summary. Do NOT push, do NOT close the issue, do NOT message the reviewer.

---

## 1. Scope (data primitive only)
Enumerate the investable VN equity universe per board with source-backed per-symbol reference metadata
+ honest coverage diagnostics. NOT a screener/ranker/advisor. Ship `universe()` only.

## 2. New domain: `vnfin.equities` (gate decision (a))
Create a new domain package `vnfin/equities/` with `__init__.py`, `sources.py`, `models.py`.
Register it in `vnfin/__init__.py`: add `equities` to the `from . import (...)` block AND to `__all__`
(alphabetical-ish, near `crypto`/`fundamentals`). Follow the **funds single-source pattern**
(`vnfin/funds/__init__.py:45-56`): `client = source` (no failover — single source).

### Public surface (`vnfin/equities/__init__.py`)
```python
def source(http_get=None, timeout: float = 25.0) -> SsiIboardUniverseSource: ...
client = source  # single-source domain, mirror funds
def universe(exchange=None, *, http_get=None, timeout: float = 25.0) -> EquityUniverse: ...
__all__ = ["EquitySecurity", "EquityUniverse", "SsiIboardUniverseSource", "client", "source", "universe"]
```
- `universe(exchange=None)` → merges ALL 3 boards (gate decision (c)); `universe("HOSE")` → one board.
- `profile(symbol)` is **DEFERRED** (gate decision (b)) — do NOT implement. Document in the domain
  docstring + tutorial: "to get one symbol, call `universe(exchange=...)` and filter."

## 3. Source: `SsiIboardUniverseSource` (`vnfin/equities/sources.py`)
Subclass `HttpDataSource` (`vnfin/transport.py`). **Mirror `IndexConstituentsSource`
(`vnfin/indices/sources.py:145-261`) exactly** for envelope/fail-closed/canonicalize/dedup — but with
its own `NAME` and its own field helpers (see §6 NAME-mislabel fix).

- `NAME = "ssi_iboard_universe"`
- `BASE_URL = "https://iboard-query.ssi.com.vn"` (confirm exact base + path vs IndexConstituentsSource's
  `BASE_URL`/`GROUP_PATH`; the constituents source uses `GET {BASE_URL}{GROUP_PATH}/{group}` — reuse the
  same host; endpoint is the group/stock-list one per the design note `GET /stock/group/{token}`).
- **Board-token map (NON-OBVIOUS — plain HOSE/HNX/UPCOM return empty):**
  ```python
  _BOARD_TOKENS = {"HOSE": "VNINDEX", "HNX": "HnxIndex", "UPCOM": "HNXUpcomIndex"}
  ```
  Normalize input board (upper/strip) → token. Unknown board → `InvalidData` (or a clear ValueError
  before network, matching how the lib rejects bad input pre-network).
- Fetch via `self._request_json(url, params, headers)` with `DEFAULT_UA` (inherited).
- **SUCCESS-envelope guard (mirror lines 178-192):**
  - `parsed.get("code") != "SUCCESS"` → `InvalidData(f"{self.name}: code={code}")`
  - `data = parsed.get("data")`; not a list → `InvalidData(f"{self.name}: 'data' is not a list")`
  - empty list → `EmptyData(f"{self.name}: no equities for board {board}")`
- **Filter `row.get("stockType") == "s"`** (equities only — drop warrants `w` / ETFs `e` / funds `m`).
  Rows failing the filter are silently skipped (NOT an error — they are simply not equities).
- Per kept row: `canonical_security_symbol(require_present(row, "stockSymbol", ctx), ctx)` then
  `reject_duplicate(sym, seen, ctx)` (within a SINGLE board — a dup *inside one board* IS a contract
  violation → `InvalidData`; cross-BOARD dup is handled in §5, NOT here).
- Imports: `from .._contracts import canonical_security_symbol, reject_duplicate, require_present`.

### Fields to extract per `EquitySecurity` (payload keys confirmed in reviewer source report)
| Field | Payload key | Notes |
|---|---|---|
| `symbol` (required) | `stockSymbol` | canonicalized |
| `exchange` (required) | `exchange` (+`market`) | `.upper()` |
| `company_name_en` | `companyNameEn` | optional → None if absent/blank |
| `company_name_vi` | `companyNameVi` | optional → None |
| `isin` | `isin` | optional → None |
| `listing_status` | `adminStatus` | optional → None |
| `par_value` | `parValue` | parse to number via the lib's existing numeric parser (find how IndexConstituents/prices parse provider floats); None if absent/`0`-as-missing per provider semantics |
| `currency` | `tradingCurrencyISOCode` | optional → None |

**DROP `security_type`** (gate decision #7): it is structurally always `"s"` after the filter →
misleading. Do NOT add it to the model.
**DROP `listing_date`**: `firstTradingDate == '0'` for ~all rows (unusable) → emit the
`listing_date_not_available` warning instead (§4).

## 4. Honest-gap warnings — ALWAYS present, never silent (mirror `weights_not_available`)
Every per-board `EquityUniverse.warnings` carries these 3 tokens (token prefix STABLE; board + detail
after the `:` so the prefix stays matchable per #180):
- `partial_universe_coverage: <BOARD> — index-basket-derived, ~96% of the full SSC roster (not complete)`
- `listing_date_not_available: <BOARD> — provider firstTradingDate is '0' (unusable)`
- `sector_not_available: <BOARD> — sector/industry absent from this payload`

## 5. `exchange=None` merge (gate decision (c) + blocker #2 = warning+keep-first)
Fetch all 3 boards, concatenate securities. **Cross-board duplicate symbol = warning + keep-first, NOT
raise** (a single live-provider glitch must not nuke all 3 boards):
- Dedup across boards by `symbol`, KEEP-FIRST (board order HOSE, HNX, UPCOM).
- On ANY cross-board collision, append (never-silent):
  `cross_board_duplicate_symbol: <SYM> kept from <board_a>, dropped from <board_b>` (one entry per
  collision, or one aggregated entry listing all — your call, prefix stable either way).
- **Per-board warnings stay attributed** in the merged result (they already carry `<BOARD>` in the
  detail from §4 — preserve all of them; the merged `warnings` is the concatenation of every board's
  honest-gap tokens + any `cross_board_duplicate_symbol`).
- `EquityUniverse.exchange`/`board` for a merge = `None` or a sentinel like `"ALL"` (pick one, document
  it; recommend `exchange=None`/`board="ALL"`).

## 6. NAME-mislabel fix (gate must-fix #4)
Do NOT copy `IndexConstituentsSource._optional_member_str` / `_member_company_name` as-is — they hard-code
`IndexConstituentsSource.NAME` (`vnfin/indices/sources.py:240`) and `cls.NAME` (`:255`), which would
mislabel THIS source's errors as `ssi_iboard_query`. Use **instance methods that reference `self.name`**
(so the label is correct by construction), e.g.:
```python
def _optional_str(self, row, key, i, field_name):
    ...
    raise InvalidData(f"{self.name}: member {i} malformed {field_name}")
```
(Lifting a name-parameterized helper into `vnfin/_contracts/` and refactoring IndexConstituentsSource to
use it is an acceptable alternative the gate offered, but it widens blast radius to the index domain and
needs its own no-behavior-change regression — **prefer the self.name instance-method copy for #167**;
note the DRY refactor as a possible future cleanup, do not do it here.)
**Add a test asserting a malformed-field error message contains `ssi_iboard_universe` (NOT
`ssi_iboard_query`).**

## 7. Result models (`vnfin/equities/models.py`) — mirror `vnfin/indices/models.py`
Frozen dataclasses.
```python
@dataclass(frozen=True)
class EquitySecurity:
    symbol: str
    exchange: Optional[str] = None
    company_name_en: Optional[str] = None
    company_name_vi: Optional[str] = None
    isin: Optional[str] = None
    listing_status: Optional[str] = None
    par_value: Optional[float] = None
    currency: Optional[str] = None

@dataclass(frozen=True)
class EquityUniverse:
    board: Optional[str]            # "HOSE"/"HNX"/"UPCOM" or "ALL" for a merge
    source: str
    securities: tuple[EquitySecurity, ...]
    fetched_at_utc: Optional[datetime] = None
    as_of: Optional[datetime] = None
    warnings: tuple[str, ...] = ()
```
Add `__len__`, `__iter__`, `.symbols` property, and `.to_dataframe()` (columns = the EquitySecurity
fields; attach board/source to `df.attrs`) — mirror `IndexConstituents` (`vnfin/indices/models.py:50-87`).
`fetched_at_utc = datetime.now(timezone.utc)` at fetch time (mirror existing); `as_of=None`.

## 8. #180 lockstep — guard 29 → 33 (SAME change)
Add ALL 4 new tokens to BOTH:
- `skills/vnfin/SKILL.md` "Warning tokens" table (4 new rows; accessor `vnfin.equities.universe`,
  issue #167) — keep the table's existing format/grouping.
- `tests/test_docs_contract.py` `_WARNING_TOKENS_180` tuple (append the 4).
New tokens (EXACT strings): `partial_universe_coverage`, `listing_date_not_available`,
`sector_not_available`, `cross_board_duplicate_symbol`.
The bidirectional guard `test_skill_warning_tokens_section_in_lockstep_with_code` must stay GREEN
(every token documented AND emitted as a literal). Gate on the SWEEP, not the count.

## 9. TDD test matrix (`tests/test_equities.py`) — RED first, synthetic fixtures only
Write each test FAILING first, then implement to green. NO real provider rows.
1. mixed-`stockType` fixture → only `s` rows kept (w/e/m dropped).
2. missing `isin`/`parValue`/`companyName*` → None (NOT fabricated).
3. `code != "SUCCESS"` → `InvalidData`; `data` not a list → `InvalidData`; empty `data` → `EmptyData`.
4. duplicate symbol WITHIN one board → `InvalidData` (reject_duplicate).
5. cross-board duplicate (exchange=None) → keep-first + `cross_board_duplicate_symbol` warning, NO raise.
6. the 3 honest-gap tokens ALWAYS present on a single-board result (assert by prefix).
7. board-token aliasing: `universe("HOSE")` hits token `VNINDEX` (assert the URL/token), HNX→HnxIndex,
   UPCOM→HNXUpcomIndex; unknown board → error before network.
8. `exchange=None` merges all 3 boards; per-board honest-gap warnings all attributed in the merged result.
9. malformed-field error message contains `ssi_iboard_universe` (NAME-mislabel regression).
10. `to_dataframe()` columns + dtypes + `.symbols` + `len()`.
11. **CI-skipped opt-in live probe** (`@pytest.mark.skip` or an env-gated skip consistent with how the
    repo marks live tests — check existing live/integration test markers) that hits the real endpoint and
    pins payload shape. MUST be skipped in CI by default.
Use the HTTP injection seam the other source tests use (a fake `http_get` / fixture loader — see
`tests/test_indices.py` for the IndexConstituentsSource fixture pattern and copy it).

## 10. Docs (SAME change — public-API change ⇒ docs + skill + CHANGELOG)
- NEW `docs/sources/equities-universe.md`: provenance (cite reviewer source report — HOSE/VNINDEX=403,
  HNX/HnxIndex=300, UPCOM/HNXUpcomIndex=828; ~96% vs SSC press cross-check; SSI iBoard ToS =
  runtime-fetch / no-redistribution), the 3 honest gaps, board-token aliasing, the keep-first merge.
- `docs/units.md` + `skills/vnfin/reference/domains.md` + `docs/api.md`: add the `vnfin.equities` domain
  (universe()/source(), models, the 4 warning tokens).
- `CHANGELOG.md` Unreleased → Added: `vnfin.equities.universe(...)` + link issue #167.
- Update the facade docstring in `vnfin/__init__.py` (the domain list) to include `vnfin.equities`.

## 11. Snapshot policy (CRITICAL — do NOT regen)
Adding `vnfin.equities` is an ADDITIVE public-surface change. The surface test
(`tests/test_public_api_surface.py`) is **additive-tolerant** (additions are allowed + printed, folded
into the baseline only at RELEASE time). So: **do NOT edit/regen
`tests/snapshots/public_api_v0_2_0.json`.** If the surface test fails for any reason other than a clean
"additive" classification, STOP and report it — do not regen.

## 12. Acceptance criteria (all must hold on the MERGED tree)
- [ ] Full suite green; new `tests/test_equities.py` green; all RED-first proven during dev.
- [ ] `_WARNING_TOKENS_180` guard green at 33 tokens (4 new documented + emitted).
- [ ] Public-API snapshot UNCHANGED (frozen); surface test green as additive.
- [ ] `test_no_secrets` green; no real provider rows committed (synthetic fixtures only).
- [ ] Error labels use `ssi_iboard_universe` (no `ssi_iboard_query` mislabel).
- [ ] Coverage ≥85% on new/changed lines.
- [ ] Clean-room: SSI iBoard host only, zero VNStock anywhere.

## Reference code map (verified via Explore, 2026-06-21)
- `IndexConstituentsSource`: `vnfin/indices/sources.py:145-261` (NAME, envelope guard 178-192, canon/dedup
  203-207, member build 211-219, `_optional_member_str` 231-243 [NAME hardcode :240], `_member_company_name`
  245-260 [:255], `_GROUP_ALIASES`/`normalize_group` 138-165).
- Models: `vnfin/indices/models.py:16-87` (IndexMember, IndexConstituents, to_dataframe).
- `HttpDataSource._request_json`: `vnfin/transport.py:528-543`; `DEFAULT_UA` 190-193; IPv4 force :557.
- `_contracts`: `canonical_security_symbol` `vnfin/_contracts/keys.py:196-198`; `reject_duplicate`
  `vnfin/_contracts/rows.py:29-37`; both re-exported from `vnfin._contracts`.
- Funds `client = source`: `vnfin/funds/__init__.py:45-56`. Domain registration: `vnfin/__init__.py`
  (`from . import (...)` 22-35, `__all__` 46-69). Indices accessor: `vnfin/indices/__init__.py:67-86`.
