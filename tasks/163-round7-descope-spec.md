# #163 round-7 — DE-SCOPE the net-vs-gross classifier (TDD-first, exact spec)

**Status:** design gate CONVERGED with `vnfin-oss-reviewer` (de-scope confirmed 14:53, 7-point
re-pass scope locked 14:56). This spec is authoritative — implement it EXACTLY, TDD-first.

## Why (one paragraph)
The VSDC free-text net-vs-gross ratio classifier produced **7 distinct silent-wrong-ratio bugs over 6
rounds** (allowlist → placement → before-guard inversion → fee-verb → multi-tax → independent hunter's
net-first/par-gated bug). It is open-ended NLP on adversarial scraped HTML — a bottomless well. v1
DE-SCOPE: **stop classifying.** Serve `ratio_pct` ONLY from a tax-free ratio context. ANY tax /
withholding signal in the ratio line → `ratio_pct=None` + a NEW `vsdc_ratio_tax_deferred` token. This
permanently removes the silent-wrong-ratio CLASS. Net-vs-gross classification is deferred to v2 behind a
committed test corpus (the accumulated phrasings, now preserved as tests).

## The gate (LINE-level, provably complete — chosen over segment-level)
A ratio context (the justify cash line) is tax-qualified iff, after `_strip_accents` + word-boundary
tokenization (`re.findall(r"[a-z0-9]+", ...)`), the token set contains an explicit **tax noun**
`{thue, tncn}` OR the **withholding verb pair** `khau` AND `tru` together. Line-level (not segment-level)
because a tax token in one candidate's segment must taint the WHOLE line (multi-candidate leak +
hunter bug#7 both proved segment-level leaks). The `khau`+`tru` pair is included so a withholding line
that elides the word "thuế" (`đã thực hiện khấu trừ 10%` — #9.44) is ALSO withheld; verified it never
trips any clean served fixture (probe: all 4 clean cases + the canonical clean fixture → False).

## TDD ORDER (mandatory)
1. Apply ALL test changes below (Section C) FIRST.
2. Run `.venv/bin/python -m pytest tests/test_corp_actions_vsdc.py -q` → confirm RED (current
   classifier code still serves tax ratios / emits the old token). Capture the RED count.
3. Apply the vsdc.py changes (Section A).
4. Re-run that file → GREEN.
5. Apply lockstep (Section B); run `tests/test_docs_contract.py` + full suite → GREEN.

Runner is ALWAYS `.venv/bin/python -m pytest`. **NEVER run `scripts/dump_api_surface.py`**; the
snapshot `tests/snapshots/public_api_v0_2_0.json` must stay UNCHANGED (a warning-token constant is not
a public-API surface symbol — the snapshot test must stay additive-green without regen).

---

## SECTION A — `vnfin/corp_actions/vsdc.py`

### A1. New warning-token constant (add right after `VSDC_PARSE_DEGRADED = "vsdc_parse_degraded"`, ~line 44)
```python
#: Per-result: the ratio context PARSED FINE but carries a tax / withholding signal (thuế / TNCN /
#: khấu trừ), so its `%` is net-vs-gross ambiguous. Under the #163 v1 de-scope we do NOT classify
#: net-vs-gross (an open-ended, silent-wrong-prone problem); the ratio is INTENTIONALLY withheld
#: (ratio_pct=None) and disclosed via this token. Distinct from vsdc_parse_degraded, which means a
#: field could not be PARSED (a data-quality fault). net-vs-gross classification is a v2 scope item.
VSDC_RATIO_TAX_DEFERRED = "vsdc_ratio_tax_deferred"
```

### A2. DELETE lines 138-187 entirely
Remove `_BEFORE_TAX_TOKENS`, `_TAX_NOUN_TOKENS`, AND the whole `_segment_is_net(text)` function (all 6
rounds of net/gross complexity — genuinely deleted, not bypassed). Replace that block with:
```python
# Tax / withholding SIGNAL tokens (accent-stripped). Under the #163 v1 de-scope a ratio from a line
# carrying ANY of these is net-vs-gross ambiguous and is WITHHELD (ratio_pct=None +
# vsdc_ratio_tax_deferred), NOT classified — net-vs-gross is a v2 scope decision.
_RATIO_TAX_NOUNS = frozenset({"thue", "tncn"})  # thuế / TNCN


def _line_has_tax_signal(text: str) -> bool:
    """True when a justify ratio line carries a tax / withholding signal: an explicit tax noun
    (thuế / TNCN) OR the withholding verb pair khấu+trừ ('thuế' is often elided, e.g. 'đã thực hiện
    khấu trừ'). Word-boundary + accent-stripped, so 'thực hiện' (on every page), 'internet', 'trong',
    'trước' (token 'truoc' != 'tru') never register. A line with such a signal has its ratio WITHHELD
    under the v1 de-scope (#163): the `%` could be net-of-tax and we no longer classify net-vs-gross."""
    toks = set(re.findall(r"[a-z0-9]+", _strip_accents(text)))
    return bool(toks & _RATIO_TAX_NOUNS) or ("khau" in toks and "tru" in toks)
```

### A3. Add `ratio_tax_deferred` flag init (alongside `ratio_uncertain = False`, ~line 342)
```python
        ratio_uncertain = False
        ratio_tax_deferred = False
```

### A4. REPLACE the ratio-resolution body (current lines 356-403, inside `if cash_m and cash_per_share is None:`)
Keep `cash_per_share = _parse_vn_number(cash_m.group("cash"))` and `prefix = line[: cash_m.start()]`.
Replace everything from the candidate-loop comment through `if had_ratio_token and chosen is None: ratio_uncertain = True` with:
```python
                # DE-SCOPE (#163 v1): if the ratio line carries ANY tax / withholding signal its `%`
                # is net-vs-gross ambiguous — we do NOT classify it (that was open-ended and
                # silent-wrong-prone). WITHHOLD the ratio and disclose via vsdc_ratio_tax_deferred.
                # A ratio is served ONLY from a fully tax-free line. (v2 = classify behind a corpus.)
                matches = list(_RATIO_RE.finditer(prefix))
                had_ratio_token = bool(matches)
                if _line_has_tax_signal(line):
                    ratio_tax_deferred = True
                else:
                    # Tax-free line: serve a single unambiguous gross %/cổ phiếu, optionally
                    # par-cross-checked (cash ≈ ratio/100 × par). Bounded 0 < pct ≤ 100.
                    gross_cands = [
                        pct
                        for rm in matches
                        if (pct := _parse_ratio_pct(rm.group("pct"))) is not None
                        and 0 < pct <= 100
                    ]
                    chosen: Optional[float] = None
                    if par is not None and cash_per_share is not None:
                        tol = max(1.0, 0.005 * cash_per_share)
                        confirmed = sorted(
                            {c for c in gross_cands if abs(c / 100.0 * par - cash_per_share) <= tol}
                        )
                        if len(confirmed) == 1:
                            chosen = confirmed[0]
                        elif len(confirmed) > 1:
                            ratio_uncertain = True
                    elif len(gross_cands) == 1:
                        chosen = gross_cands[0]
                    ratio_pct = chosen
                    if had_ratio_token and chosen is None:
                        ratio_uncertain = True
```
(Drop the obsolete `net_present` variable and the `and not net_present` condition entirely — the tax
branch handles all net cases now.)

### A5. Degrade block (current lines 408-423)
- `cross_line_unpaired` must NOT fire on a tax-deferred line (the new token already discloses it):
```python
        cross_line_unpaired = (
            cash_per_share is not None
            and ratio_pct is None
            and any_ratio_token
            and not ratio_tax_deferred
        )
```
- Append the new token when tax-deferred (BEFORE the parse_degraded conditional):
```python
        if ratio_tax_deferred:
            warnings.append(VSDC_RATIO_TAX_DEFERRED)
```
- The existing `if (record_date is None or ... or cross_line_unpaired or cash_anchor_count > 1):
  warnings.append(VSDC_PARSE_DEGRADED)` block stays — so a multi-tranche page whose first tranche is
  ALSO tax-qualified emits BOTH tokens (multi-tranche → parse_degraded, tax → ratio_tax_deferred).

### A6. Module docstring (lines 1-26)
Add one sentence after the `vsdc_parse_degraded` sentence: that a recognized ratio carrying a tax /
withholding signal (thuế / TNCN / khấu trừ) is net-vs-gross ambiguous and, under the v1 de-scope, is
WITHHELD (`ratio_pct=None`) + the distinct `vsdc_ratio_tax_deferred` token rather than classified
(net-vs-gross deferred to v2).

---

## SECTION B — lockstep (#180 reverse + #188 forward, bijection must stay green)

### B1. `tests/test_docs_contract.py`
Find the `_WARNING_TOKENS_180` tuple (currently **43** tokens). Add `"vsdc_ratio_tax_deferred"`
→ **44**. Keep alphabetical/grouped order if the tuple has one; place it next to `vsdc_parse_degraded`.

### B2. `skills/vnfin/SKILL.md` "## Warning tokens" table
Add a row for `vsdc_ratio_tax_deferred`: scope = per-result (corp_actions / VSDC); meaning = "ratio line
carries a tax/withholding signal (thuế/TNCN/khấu trừ) so its % is net-vs-gross ambiguous; ratio withheld
(ratio_pct=None), net-vs-gross deferred to v2. Distinct from vsdc_parse_degraded (a parse fault)."
Match the existing table's column format exactly.

### B3. `CHANGELOG.md` (Unreleased / 0.2.0 section)
Add an entry: #163 v1 de-scope — VSDC no longer classifies net-vs-gross dividend ratios; a ratio line
carrying a tax/withholding signal yields `ratio_pct=None` + the new `vsdc_ratio_tax_deferred` token
(net-vs-gross classification deferred to v2). Note it's a conservative pre-1.0 v1-surface shrink.

---

## SECTION C — `tests/test_corp_actions_vsdc.py` transformations

New contract reminders for every case below:
- A tax-qualified single-tranche line → `ev.ratio_pct is None`, `"vsdc_ratio_tax_deferred" in
  ev.warnings`, `"vsdc_parse_degraded" not in ev.warnings`, cash unchanged.
- A NON-tax degrade case → `"vsdc_parse_degraded" in ev.warnings`, `"vsdc_ratio_tax_deferred" not in
  ev.warnings` (distinct semantics).
- A clean tax-free line → ratio served, neither token present.

### C1. INVERT — currently assert tax ratio SERVED (gross), must become WITHHELD
For each: change the ratio assertion to `assert ev.ratio_pct is None`, add `assert
"vsdc_ratio_tax_deferred" in ev.warnings` and `assert "vsdc_parse_degraded" not in ev.warnings`, keep
the cash assertion, and rewrite the docstring to the de-scope contract (the old par-recovery / before-
tax-override mechanism is DELETED — say the line carries a tax signal so the ratio is withheld).
- **#9.22** `test_parse_sau_thue_uses_par_to_recover_gross_ratio` (553) — cash 1200, was 12.0 → None+deferred.
  Rename to `test_parse_sau_thue_with_par_is_withheld_not_classified`.
- **#9.36** `test_parse_before_tax_marker_does_not_trigger_net_exclusion` (811) — cash 1200, was 12.0 →
  None+deferred. Rename to `test_parse_truoc_thue_line_is_withheld_under_descope`.

### C2. TOKEN-CHANGE — currently assert tax ratio None + `vsdc_parse_degraded`, must assert the NEW token
For each: keep `ratio_pct is None` + cash; change `assert "vsdc_parse_degraded" in ev.warnings` →
`assert "vsdc_ratio_tax_deferred" in ev.warnings` and ADD `assert "vsdc_parse_degraded" not in
ev.warnings`; tweak the docstring's mechanism sentence to "carries a tax signal → withheld (de-scope)".
- **#9.23** `test_parse_sau_thue_without_par_degrades_not_wrong_ratio` (577) — cash 1200.
- **#9.29** `test_parse_net_only_ratio_degrades_no_par` (702) — cash 1200.
- **#9.30** `test_parse_gross_plus_net_no_par_degrades` (716) — cash 1140.
- **#9.31** `test_parse_gross_plus_net_with_par_net_cash_degrades` (732) — cash 1140 (par=True).

### C3. #9.26 multi-tranche + tax — assert BOTH tokens
**#9.26** `test_parse_multitranche_with_sau_thue_no_misparse_and_discloses` (621): change
`assert ev.ratio_pct == 12.0` → `assert ev.ratio_pct is None`; ADD `assert "vsdc_ratio_tax_deferred"
in ev.warnings`; KEEP `assert "vsdc_parse_degraded" in ev.warnings` (multi-tranche disclosure). cash
1200. Update docstring: both failure modes now disclosed via distinct tokens — multi-tranche →
parse_degraded, tax line → ratio_tax_deferred; ratio withheld (no longer par-recovered).

### C4. REPLACE the contiguous block #9.37–#9.55 (lines 827–1147)
Delete those 19 tests and replace with the three tests below (they preserve EVERY phrasing as a
parametrized corpus — this is the v2 fixture seed — plus the 3 new attack cases + clean-served +
semantic-distinction). Reuse the existing `_justify_page(body, *, par=False)` helper.

```python
# --------------------------------------------------------------------------- #
# #163 round-7 DE-SCOPE corpus (replaces the deleted net-vs-gross classifier tests #9.37-#9.55).
# Under v1 we no longer classify net-vs-gross: ANY tax/withholding signal in the ratio line →
# ratio withheld (ratio_pct=None) + vsdc_ratio_tax_deferred. These phrasings are the v2 corpus seed.
# --------------------------------------------------------------------------- #
_TAX_DEFERRED_CORPUS = [
    # (id, justify-body, expected_cash, par)
    ("9.37 trailing sau thuế, no par",
     "- Tỷ lệ thực hiện: 11,4%/cổ phiếu sau thuế (01 cổ phiếu được nhận 1.140 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1140.0, False),
    ("9.38 gross + trailing sau thuế + par",
     "- Tỷ lệ thực hiện: 12%/cổ phiếu; 11,4%/cổ phiếu sau thuế "
     "(01 cổ phiếu được nhận 1.140 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1140.0, True),
    ("9.39 leading sau thuế + par confirms net",
     "- Tỷ lệ thực hiện sau thuế 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, True),
    ("9.40 đã khấu trừ thuế",
     "- Tỷ lệ thực hiện đã khấu trừ thuế 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.41 đã trừ thuế",
     "- Tỷ lệ thực hiện đã trừ thuế: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.42 trailing trước thuế (was served gross, now withheld under de-scope)",
     "- Tỷ lệ thực hiện: 12%/cổ phiếu trước thuế (01 cổ phiếu được nhận 1.200 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1200.0, False),
    ("9.43 trước thuế TNCN (was served gross, now withheld)",
     "- Tỷ lệ thực hiện: 12%/cổ phiếu trước thuế TNCN (01 cổ phiếu được nhận 1.200 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1200.0, False),
    ("9.44 bare khấu trừ, thuế elided",
     "- Tỷ lệ thực hiện: đã thực hiện khấu trừ 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.45 chưa khấu trừ thuế (was served gross, now withheld)",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu chưa khấu trừ thuế (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.46 sau thuế + (chưa gồm phí)",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế (chưa gồm phí) "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.47 đã trừ thuế, chưa gồm phí",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu đã trừ thuế, chưa gồm phí "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.48 trước khi khấu trừ thuế (was served gross, now withheld)",
     "- Tỷ lệ thực hiện: 12%/cổ phiếu trước khi khấu trừ thuế "
     "(01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1200.0, False),
    ("9.49 sau thuế (không gồm phí)",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế (không gồm phí) "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.50 sau thuế, miễn phí",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế, miễn phí giao dịch "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.51 sau thuế, trước ngày",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế, dự kiến trả trước ngày 20/04 "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.52 sau thuế (chưa gồm phí) + par",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế (chưa gồm phí) "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, True),
    ("9.53 khấu trừ thuế + fee clause",
     "- Tỷ lệ thực hiện: khấu trừ thuế 10%/cổ phiếu, chưa khấu trừ phí lưu ký "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.54 đã trừ thuế + bare trừ fee",
     "- Tỷ lệ thực hiện: đã trừ thuế 12%/cổ phiếu, chưa trừ phí quản lý "
     "(01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1200.0, False),
    ("9.55 thuế TNCN + không trừ phí",
     "- Tỷ lệ thực hiện: thuế TNCN 8%/cổ phiếu, không trừ phí dịch vụ "
     "(01 cổ phiếu được nhận 800 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 800.0, False),
    # NEW round-7 attack cases (the BLOCK6 multi-tax + hunter bug#7 + multi-candidate leak):
    ("NEW multi-tax (BLOCK6: TNCN + GTGT)",
     "- Tỷ lệ thực hiện: đã khấu trừ thuế TNCN 10%/cổ phiếu, chưa bao gồm thuế GTGT "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("NEW hunter bug#7 (net-first, sau thuế trailing non-last) + par",
     "- Tỷ lệ thực hiện: 8,5%/cổ phiếu sau thuế; 10%/cổ phiếu "
     "(01 cổ phiếu được nhận 850 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 850.0, True),
    ("NEW multi-candidate leak (tax token on candidate A only)",
     "- Tỷ lệ thực hiện: đã khấu trừ thuế TNCN 10%/cổ phiếu, 12%/cổ phiếu "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
]


@pytest.mark.parametrize("label,body,cash,par", _TAX_DEFERRED_CORPUS, ids=[c[0] for c in _TAX_DEFERRED_CORPUS])
def test_parse_tax_qualified_ratio_deferred_never_served(label, body, cash, par):
    """#163 v1 DE-SCOPE — NO tax/withholding-qualified ratio is EVER served. Every accumulated
    phrasing (the 6-round corpus + hunter bug#7 + multi-tax/multi-candidate) yields ratio_pct=None +
    vsdc_ratio_tax_deferred, with cash + dates intact. Single-tranche → NOT vsdc_parse_degraded
    (the two tokens are semantically distinct: intentional withholding vs a parse fault)."""
    ev = VsdcCashDividendSource().parse_announcement(_justify_page(body, par=par))
    assert ev is not None, label
    assert ev.cash_per_share == cash, label
    assert ev.ratio_pct is None, label  # never a net/gross-ambiguous rate served as gross
    assert "vsdc_ratio_tax_deferred" in ev.warnings, label
    assert "vsdc_parse_degraded" not in ev.warnings, label  # distinct token, single-tranche


_CLEAN_SERVED_CORPUS = [
    ("plain integer 10%", "- Tỷ lệ thực hiện: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False, 10.0),
    ("dot decimal 8.5%", "- Tỷ lệ thực hiện: 8.5%/cổ phiếu (01 cổ phiếu được nhận 850 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 850.0, False, 8.5),
    ("comma decimal 8,5%", "- Tỷ lệ thực hiện: 8,5%/cổ phiếu (01 cổ phiếu được nhận 850 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 850.0, False, 8.5),
    ("bonus + cash, par recovers 12%",
     "- Cổ phiếu thưởng 100%/cổ phiếu; cổ tức tiền mặt 12%/cổ phiếu "
     "(01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1200.0, True, 12.0),
]


@pytest.mark.parametrize("label,body,cash,par,expect", _CLEAN_SERVED_CORPUS, ids=[c[0] for c in _CLEAN_SERVED_CORPUS])
def test_parse_clean_ratio_still_served_no_over_degrade(label, body, cash, par, expect):
    """De-scope NEGATIVE guard — the tax-signal gate must NOT over-degrade a clean, tax-free ratio
    line: it is still served and carries NEITHER degrade token."""
    ev = VsdcCashDividendSource().parse_announcement(_justify_page(body, par=par))
    assert ev is not None, label
    assert ev.cash_per_share == cash, label
    assert ev.ratio_pct == expect, label
    assert "vsdc_ratio_tax_deferred" not in ev.warnings, label
    assert "vsdc_parse_degraded" not in ev.warnings, label


def test_parse_tax_and_nontax_degrade_tokens_are_distinct():
    """#163 round-7 semantic distinction (reviewer check #6) — a TAX line emits ONLY
    vsdc_ratio_tax_deferred (intentional withholding, not a parse fault); a NON-tax ambiguous line
    (par-confirmed twins) emits ONLY vsdc_parse_degraded. The two tokens never collapse."""
    tax = VsdcCashDividendSource().parse_announcement(_justify_page(
        "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế (01 cổ phiếu được nhận 1.000 đồng)<br />"
        "- Ngày thanh toán: 10/04/2024<br />"))
    assert tax.ratio_pct is None
    assert "vsdc_ratio_tax_deferred" in tax.warnings
    assert "vsdc_parse_degraded" not in tax.warnings
    nontax = VsdcCashDividendSource().parse_announcement(_justify_page(
        "- Tỷ lệ thực hiện: 10%/cổ phiếu; sau điều chỉnh 10,04%/cổ phiếu "
        "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", par=True))
    assert nontax.ratio_pct is None
    assert "vsdc_parse_degraded" in nontax.warnings
    assert "vsdc_ratio_tax_deferred" not in nontax.warnings
```

### C5. Add semantic-distinction asserts to the NON-tax degrade tests (cheap, direct)
Add `assert "vsdc_ratio_tax_deferred" not in ev.warnings` after the existing
`assert "vsdc_parse_degraded" in ev.warnings` in each of these (they carry NO tax token, so must
NEVER get the new token):
- #9.21 `test_parse_multitranche_discloses_dropped_tranche` (530)
- #9.24 `test_parse_rejects_implausible_over_100_ratio` (599)
- #9.32 `test_parse_alt_phrased_tranche_discloses_dropped` (748)
- #9.33 `test_parse_cross_line_ratio_unpaired_degrades` (763)
- #9.34 `test_parse_par_confirmed_twins_degrade` (780)

### C6. LEAVE UNCHANGED
#9.27/#9.28 (decimal, clean served), #9.35 (clean served), #9.25 (seed-not-found), #9.13 (diagnostic),
and ALL model/discovery/crawl/BFS/fetch tests. `ensure pytest is imported` at top of the file (it is —
the existing parametrized tests use it; verify `import pytest` present).

---

## Acceptance (the reviewer's locked 7-point re-pass — verify ALL before handoff)
1. NO tax-qualified ratio EVER served — all corpus phrasings + bug#7 + multi-tax/multi-candidate →
   ratio_pct=None + vsdc_ratio_tax_deferred.
2. Clean tax-free lines STILL serve (no over-degrade regression).
3. cash_per_share + record/pay dates + BFS discovery + NOTE-1 seed-not-found intact (existing tests green).
4. `_segment_is_net` + `_BEFORE_TAX_TOKENS` + `_TAX_NOUN_TOKENS` genuinely DELETED (grep returns nothing).
5. New token rides #180 reverse + #188 forward; `_WARNING_TOKENS_180` 43→44; bijection green.
6. Clean par/twins/>100/malformed still vsdc_parse_degraded (distinct semantics).
7. Snapshot additive (no dump_api_surface.py run); inverted tests are the intended contract change.

Full suite green on the merged tree. Then STOP — the integrator (main agent) runs gates + adversarial
verify + routes to the reviewer. Do NOT push, close issues, advance state/, or message the reviewer.
