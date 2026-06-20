# Design — Bank fundamentals item-code mapping (#157 base-layer mislabel fix)

- Status: **APPROVED_WITH_NOTES (reviewer Codex×2, review-202606201700) — Q1 probe PASS; implementing**
- Date: 2026-06-20
- Issue: #157 bank data-integrity input (reviewer-reproduced, review-202606201553)
- Related: `docs/design/fundamentals-metrics.md` (the canonical-metrics layer builds ON the corrected base)

## 1. Problem & root cause

`get_financials(symbol, statement, period, is_bank=True)` returns **systematically WRONG human
labels** for bank line items. Two compounding mechanisms in `vnfin/fundamentals/itemcodes.py`:

**(A) Wrong `_BANK` entries.** Several hard-coded bank labels point at the wrong code:
`412000`→"Tổng tài sản" (it is *loans*), `413100`→"Tiền gửi của khách hàng" (it is a small
sub-line, not headline deposits), `411600`→"Cho vay khách hàng" (it is ~0), `22070`→"Thu nhập lãi
thuần" (it is an ~8T sub-line, not NII), `421601`→"Lợi nhuận sau thuế" (it is not PAT).

**(B) Corporate-template fallback contaminates bank codes.** `item_name` falls back to the
`_CORPORATE` map for any code absent from `_BANK`, even when `is_bank=True`:

```python
def item_name(item_code, *, is_bank=False):
    code = str(item_code)
    if is_bank and code in _BANK:
        return _BANK[code]
    if code in _CORPORATE:      # <-- bank codes get a CORPORATE label here (BUG)
        return _CORPORATE[code]
    if code in _BANK:
        return _BANK[code]
    return f"item_{code}"
```

The same numeric code means different things in the corporate vs bank template, so the fallback
mislabels: bank-balance `13000` → corporate "Chi phí bán hàng" (it is *total liabilities*);
bank-balance `14000` → corporate "Lợi nhuận thuần từ HĐKD" (it is *total equity*); bank-income
`23000` → corporate "Tài sản ngắn hạn" (it is *PAT*). This is the cross-statement "leak" the
reporter saw.

Net effect: headline bank values (assets, loans, deposits, NII, PBT, PAT) are off by 5–7× or
hidden under raw codes, and several values carry a **confidently wrong** human label.

## 2. Evidence — gated live probe (VCB, CTG, BID) + official figures

Reviewer-sanctioned one-off probe via the project's own clean-room VNDirect adapter (`is_bank=True`,
`annual`, fiscal_date 2025-12-31). Values in **VND trillion**. Official VCB FY2025 figures from a
clean-room research pass (Báo Chính Phủ / Vietnambiz / Alpha Spread; **no VNStock**). Confidence is
anchored by the **accounting identity** (liabilities + equity = total assets) holding exactly, plus
cross-bank consistency and the official cross-check.

### Balance sheet (model_type 101)

| Code | Provider label (WRONG) | VCB | CTG | BID | **Correct canonical** | Proof / confidence |
|---|---|---|---|---|---|---|
| `12700` | *(raw)* | 2,442.28 | 2,767.70 | *(absent)* | **Tổng tài sản** (total assets) | identity 13000+14000=12700 (VCB 2,217.72+224.56=2,442.28 ✓); official ~2,480 — **HIGH** |
| `13000` | "Chi phí bán hàng" | 2,217.72 | 2,588.04 | 3,157.27 | **Nợ phải trả** (total liabilities) | identity; corp-fallback leak — **HIGH** |
| `14000` | "Lợi nhuận thuần…" | 224.56 | 179.66 | 173.55 | **Vốn chủ sở hữu** (total equity) | identity; official VCB equity ~224.5 ✓; corp-fallback leak — **HIGH** |
| `412000` | "Tổng tài sản" | 1,648.55 | 1,957.46 | 2,338.01 | **Cho vay khách hàng** (customer loans) | official VCB loans ~1,660 ✓; cross-bank — **HIGH** |
| `413300` | *(raw)* | *(absent)* | 1,793.73 | 2,222.99 | **Tiền gửi của khách hàng** (customer deposits) | CTG/BID deposit magnitude; cross-bank disambiguates from loans — **HIGH (when present)** |
| `412100` | *(raw)* | 1,673.53 | 1,992.27 | 2,372.96 | *(loans gross/related sub-line)* | ≈412000 + provision; gross-vs-net unconfirmed — **leave RAW** |
| `411600` | "Cho vay khách hàng" | — | 0.23 | 0.00 | *(NOT loans)* | ~0 → remove wrong label, RAW |
| `413100` | "Tiền gửi của khách hàng" | — | 144.59 | 218.83 | *(NOT headline deposits)* | small sub-line → remove wrong label, RAW |

### Income statement (model_type 102)

| Code | Provider label (WRONG) | VCB | CTG | BID | **Correct canonical** | Proof / confidence |
|---|---|---|---|---|---|---|
| `23800` | *(raw)* | 44.02 | 43.44 | 37.79 | **Lợi nhuận trước thuế** (PBT) | official VCB PBT 44.02 ✓✓✓; cross-bank — **HIGH** |
| `23000` | "Tài sản ngắn hạn" | 35.18 | 34.60 | 29.90 | **Lợi nhuận sau thuế** (PAT) | official VCB PAT 35.2 ✓; corp-fallback leak — **HIGH** |
| `421900` | *(raw)* | 58.77 | 66.45 | 63.30 | **Thu nhập lãi thuần** (NII) | official VCB NII 58.4 ✓; cross-bank (BID 63.30 **present**) — **HIGH** |
| `22070` | "Thu nhập lãi thuần" | 8.82 | 8.57 | 7.36 | *(NOT NII)* | ~8T sub-line → remove wrong label, RAW |
| `421601` | "Lợi nhuận sau thuế" | 5.27 | 11.77 | 16.25 | *(NOT PAT)* | not PAT → remove wrong label, RAW |
| `23003` | *(raw)* | 35.20 | 34.87 | 30.43 | *(≈PAT near-dup)* | near-duplicate of 23000 → **leave RAW** (avoid double-label) |

### Cash flow (model_type 103) — FULLY RAW in v1 (reviewer Q3)
Even the standard aggregates are unreliable for banks (`32000`=116T investing-CF is implausible), so
v1 maps **no** bank cashflow code — the 103 table is empty and every bank cashflow line stays raw
`item_<code>`. Bank cashflow labels are deferred.

**Key insight — per-bank code variability:** `12700` is present for VCB/CTG but absent for BID;
`413300` absent for VCB. A fixed code→name map therefore *will* have per-bank gaps. That is fine
under this design: an absent code emits no label (not a wrong one); the canonical **metrics** layer
(#157) is where "find deposits/assets across candidate codes / detect absence" lives.

## 3. Design principles

1. **Never a wrong human label on a value.** An unmapped/unverified code returns the honest raw
   `item_<code>`, never a guessed or cross-template label.
2. **Per-statement (per-template) membership is enforced structurally** by keying the map on
   `model_type`. A balance code is only ever looked up in the balance template; an income code in a
   balance payload simply isn't found → raw. No cross-template fallback for banks.
3. **Map only high-confidence, verified codes.** The verified headline set above; the unverified
   majority stays raw. Correctness over coverage.
4. **Additive / no public-API break.** `LineItem` shape unchanged; values unchanged; only `name`
   strings and the `item_name` signature change (internal). Corporate behavior unchanged.

## 4. Proposed architecture

Replace the single flat `_BANK` dict + `_CORPORATE` cross-fallback with **per-`model_type` maps**:

```python
_NAMES_BY_MODEL_TYPE = {
    1:   {...},   # corporate income   (unchanged content)
    2:   {...},   # corporate balance  (unchanged content)
    3:   {...},   # corporate cashflow (unchanged content)
    101: {...},   # BANK balance  — verified headline set (12700/13000/14000/412000/413300)
    102: {...},   # BANK income   — verified headline set (421900/23800/23000)
    103: {},      # BANK cashflow — v1 FULLY RAW (reviewer Q3): no codes mapped
}

def item_name(item_code: str, *, model_type: int | None = None) -> str:
    code = str(item_code)
    table = _NAMES_BY_MODEL_TYPE.get(model_type)
    if table and code in table:
        return table[code]
    return f"item_{code}"          # honest raw — NEVER a cross-template guess
```

- **`model_type` is the authoritative key.** Bank-balance `14000` (model_type 101) is looked up in
  the 101 table only → if not present, raw; it can never collide with corporate-income `14000`.
- **Signature change** `is_bank=` → `model_type=`. The sole caller is `vndirect.py:337`
  (`name=item_name(code, is_bank=is_bank)`), where the resolved `model_type` is already in scope —
  change to `item_name(code, model_type=model_type)`. CafeF uses its own `_line_item_name` and is
  out of scope. (Reviewer Q2: HARD-SWITCH — no `is_bank` shim.)
- Corporate codes don't collide across statements, so corporate behavior is byte-identical; we just
  partition the existing `_CORPORATE` entries into the 1/2/3 sub-tables by their statement comment.

## 5. Coverage / diagnostic
Per the spec ("emit raw/coverage diagnostic for unverified codes"): the **base layer** stays minimal
(raw for unmapped). The **diagnostic** — how many codes in a report are mapped vs raw, and which raw
codes carry large values worth attention — is exposed via the #157 metric-coverage layer
(`explain_metric_coverage`) and/or a small offline helper `bank_itemcode_coverage(report)`. Proposed
to live with the metrics work, not in `item_name`. (Open question Q4.)

## 6. Out of scope (handled by the #157 metric layer)
Canonical investor **metrics** (total_assets, customer_loans, customer_deposits, NII, PBT, PAT, …)
map a metric → the verified bank code(s) above, with absence/coverage handling. The base-layer fix
only guarantees **correct-or-raw labels**; the metric layer guarantees **investor-ready values**
keyed to these verified codes. Bank ratios/EPS/BV remain v2 (per metrics design).

## 7. Test plan (synthetic, offline; TDD red-first)
- **Per-statement membership:** bank-balance code `14000` (model_type 101) → "Vốn chủ sở hữu", NOT
  the corporate "Lợi nhuận thuần…"; bank-income `23000` (102) → "Lợi nhuận sau thuế", NOT corporate
  "Tài sản ngắn hạn". (Regression for the reported leak.)
- **Corrected headline labels:** 12700→assets, 13000→liabilities, 412000→loans, 413300→deposits,
  23800→PBT, 421900→NII — for synthetic rows carrying the probe values.
- **Wrong entries removed:** 412000 NOT "Tổng tài sản"; 22070 NOT "Thu nhập lãi thuần"; 421601 NOT
  "Lợi nhuận sau thuế"; 411600 NOT "Cho vay khách hàng"; 413100 NOT headline deposits → all raw.
- **Unmapped → raw:** an unverified bank code → `item_<code>` (never a corporate or guessed label).
- **Corporate unchanged (regression):** corporate model_type 1/2/3 labels byte-identical to today.
- **Identity sanity (doc-level):** 13000 + 14000 == 12700 for the synthetic VCB fixture.
- Anchor fixtures to the cross-verified VCB/CTG/BID values; **no live calls in tests**.

## 8. Reviewer decisions (design gate 202606201700, Codex×2 → APPROVE_WITH_NOTES)

**Q1 — PASS (private-bank probe REQUIRED, then run).** Gated probe
(`scripts/probe_bank_itemcodes.py`, `VNFIN_LIVE=1`) on PRIVATE banks VPB + ACB (controls VCB/CTG),
2026-06-20: every code-of-interest present under the same templates (balance mt=101, income mt=102);
identity `13000+14000==12700` exact to the VND for all four (VPB 1,079.87+180.28=1,260.15; ACB
931.33+94.52=1,025.85). `412000` is customer-loans (VPB 926.47 ≪ assets 1,260.15), `421900` is NII
(VPB 58.66), `23800/23000` are PBT/PAT. → the per-`model_type` map generalizes beyond SOCBs.
Provenance: `docs/design/bank-itemcodes-probe-20260620.md`.

- **Q2 — HARD-SWITCH** `item_name(code, *, model_type=)`, no `is_bank` shim (sole non-test caller is
  `vndirect.py`, which has the resolved `model_type` in scope).
- **Q3 — bank cashflow FULLY RAW** in v1 (model_type 103 table empty); `32000`=116T investing-CF is
  implausible. Deferred.
- **Q4 — coverage diagnostic** lives in the #157 metric layer (`explain_metric_coverage`), not a base
  helper. Base layer stays raw-for-unmapped only.
- **Q5 — `412100` / `23003` stay RAW** (near-dup gross-loan / PAT-adjacent; no gross-vs-net split).

### Implementation checklist (the coding pass)
1. Replace `_BANK` + corporate cross-fallback with `_NAMES_BY_MODEL_TYPE`: {1,2,3 corporate split by
   statement (income/balance/cashflow); **101** bank-balance = {12700,13000,14000,412000,413300};
   **102** bank-income = {23800,23000,421900}; **103** = {} (fully raw)}. Hard-switch
   `item_name(item_code, *, model_type=None)` → look up only the matching template, else raw
   `item_<code>` (NO cross-template fallback).
2. Update the sole caller `vndirect.py` → `name=item_name(code, model_type=model_type)`.
3. **Fix the swapped header comment** `itemcodes.py:55` ("101 income / 102 balance" → "101 balance /
   102 income"; the inner section comments at 57/65 are already correct).
4. **REWRITE (don't extend)** `tests/test_fundamentals.py::test_item_name_maps_expanded_bank_headlines`
   (~L869-877) — it asserts WRONG labels (22070→NII, 412000→assets, 411600→loans, 413100→deposits).
   New asserts (all `model_type=`): 421900→NII, 12700→assets, 412000→loans, 413300→deposits, 23800→
   PBT, 23000→PAT, 13000→liabilities, 14000→equity; demoted codes (22070/411600/413100/421601/22160)
   → raw `item_<code>`.
5. **Update** `test_item_name_maps_expanded_corporate_headlines` to pass `model_type=` (1 income /
   2 balance / 3 cashflow) — under the hard-switch a no-`model_type` call returns raw.
6. **+3 tests (reviewer):** (a) **model_type-mismatch → raw**, e.g. `item_name("12700", model_type=2)`
   (bank-balance code under corp-balance) → raw; (b) **POSITIVE collision** (same code, different
   template, both mapped): `item_name("14000", model_type=1)`→corp "Lợi nhuận thuần…" vs
   `item_name("14000", model_type=101)`→"Vốn chủ sở hữu"; also `item_name("23000", model_type=2)`→
   "Tài sản ngắn hạn" vs `item_name("23000", model_type=102)`→"Lợi nhuận sau thuế"
   (NB the reviewer wrote "14000@mt2"; in our split 14000-corp is income=mt1, so the corp side uses
   mt1 and `14000@mt2`→raw — that is the mismatch case in (a)); (c) **partition-completeness** —
   every code in every sub-table resolves to its own label and to raw under a foreign model_type.
7. **N1 (cross-design, BLOCKING follow-up — DONE in this change):** `fundamentals-metrics.md` §6 bank
   table re-pointed to the verified codes (NII 421900, assets 12700, deposits 413300, loans 412000,
   PAT 23000, PBT 23800, liabilities 13000, equity 14000; unverified-code metrics deferred to v2).
   Bank metrics must NOT ship on the old codes.
8. **N2 (DONE):** dated provenance artifact `docs/design/bank-itemcodes-probe-20260620.md`.
9. Gates: corporate labels **byte-identical** (regression); additive surface (only `name` strings +
   internal signature change — public `LineItem`/values unchanged); full suite green; coverage ≥85%
   on `itemcodes.py`.
