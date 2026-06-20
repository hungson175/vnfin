# Design — Bank fundamentals item-code mapping (#157 base-layer mislabel fix)

- Status: **DESIGN — awaiting reviewer convergence (design gate; no code yet)**
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
| `421900` | *(raw)* | 58.77 | 66.45 | *(absent)* | **Thu nhập lãi thuần** (NII) | official VCB NII 58.4 ✓; cross-bank — **HIGH** |
| `22070` | "Thu nhập lãi thuần" | 8.82 | 8.57 | 7.36 | *(NOT NII)* | ~8T sub-line → remove wrong label, RAW |
| `421601` | "Lợi nhuận sau thuế" | 5.27 | 11.77 | 16.25 | *(NOT PAT)* | not PAT → remove wrong label, RAW |
| `23003` | *(raw)* | 35.20 | 34.87 | 30.43 | *(≈PAT near-dup)* | near-duplicate of 23000 → **leave RAW** (avoid double-label) |

### Cash flow (model_type 103)
The standard aggregate codes `32000`/`33000`/`34000`/`35000` currently receive corporate labels via
the fallback and appear structurally correct for banks too (VCB `35000`=111.07 "cash at end",
`34000`=-3.78 "net change"). Everything else is `431xxx`/`43xxxx` and is unverified. **Proposal:
v1 leaves bank cash flow RAW except the four standard aggregates (MEDIUM); see open question Q3.**

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
    103: {...},   # BANK cashflow — v1: 32000/33000/34000/35000 only (or empty; see Q3)
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
  out of scope. (Open question Q2: keep an `is_bank` shim for any external caller, or hard-switch.)
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

## 8. Open questions for the reviewer
- **Q1 (confidence gate):** the HIGH set is anchored by the accounting identity + official VCB + 3
  banks. Do you want the map **validated against 1–2 more banks of a different structure** (e.g. a
  joint-stock retail bank) via one more gated probe BEFORE coding, or is the 3-bank + identity +
  official evidence sufficient? (I lean: one more probe on a non-SOCB bank is cheap insurance.)
- **Q2 (signature):** hard-switch `item_name(code, *, model_type=)` (sole internal caller), or keep
  an `is_bank=` shim mapping to a representative model_type for back-compat?
- **Q3 (bank cashflow):** map the four standard aggregates `32000/33000/34000/35000` for model_type
  103 at MEDIUM confidence, or leave bank cash flow fully RAW in v1 (follow-up)?
- **Q4 (diagnostic home):** coverage diagnostic in the #157 metric layer (`explain_metric_coverage`)
  vs a dedicated `bank_itemcode_coverage` helper now?
- **Q5 (412100 / 23003):** leave the near-duplicate gross-loan / PAT-adjacent codes RAW (my pick) or
  attempt a gross-vs-net split now?
