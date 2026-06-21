# #163 B2 fix-2 spec — net-of-tax + dot-decimal + alt-tranche + cross-line (round-2 BLOCK union)

**One localized parser fix** to `vnfin/corp_actions/vsdc.py` :: `parse_announcement` (the cash/ratio
block, lines ~254–321) + 2 module helpers. B1 + NOTE-1 are already VERIFIED-FIXED (do not touch).
Everything below surfaces via the EXISTING `vsdc_parse_degraded` token — **NO new warning token, NO
#180/#188 change, NO snapshot regen.** TDD: every defect below is EMPIRICALLY confirmed on edc9898
(actuals given); write the fail-first test, confirm RED, then apply the fix, confirm GREEN.

## Defects (all = silent WRONG/DROPPED data; same class)

| ID | Page (no `Mệnh giá` unless noted — real VSDC pages have NO par) | edc9898 ACTUAL (wrong) | Required |
|----|----|----|----|
| **D-REV** (reviewer, headline) | `Tỷ lệ 8.5%/cổ phiếu (…được nhận 850 đồng)` | `ratio=85.0` (10×), not degraded | `ratio=8.5` |
| **D1** (verifier) | `…sau thuế: 10%/cổ phiếu (…được nhận 1.200 đồng)` | `ratio=10.0` (net), not degraded | `ratio=None` + degrade |
| **D2** (verifier) | `12%/cổ phiếu; thực nhận sau thuế 11,4%/cổ phiếu (…1.140 đồng)` | `ratio=11.4` (net), not degraded | `ratio=None` + degrade |
| **D3** (verifier) | 2 tranches; tranche-2 = `…số tiền 1.200 đồng/cổ phiếu` | `cash=800,ratio=8`, **not degraded** | degrade (drop disclosed) |
| **NOTE** (reviewer) | ratio on a different `<br>` line than the cash anchor | `ratio=None`, **not degraded** | degrade |
| **L1** (verifier, minor) | par 10.000 + `10%; sau điều chỉnh 10,04% (…1.000 đồng)` | `ratio=10.04` (order-dep) | degrade |
| **SECONDARY** (reviewer, low) | implausible/stray par mis-confirms | — | only trust par ≥ 1000 |

Root cause: (a) ratio % parsed with `_parse_vn_number` (`.`=thousands) → `8.5`→85; (b) the pipeline
can't tell a net-of-tax candidate from a gross one; (c) multi-tranche count only sees the `được nhận`
phrasing; (d) a ratio off the cash line is silently unpaired.

## EXACT edits

### 1. Two module-level constants + a ratio parser (add right after `_parse_vn_number`, ~line 136)
```python
# Net-of-tax markers (accent-stripped): a "%" candidate or cash qualified by one of these is an
# AFTER-TAX figure, never the gross dividend ratio.
_NET_MARKERS = ("sau thue", "thuc nhan", "thuc linh", "thuc lanh", "sau khi tru thue")

# A per-share cash amount in EITHER VSDC phrasing — "…được nhận 1.200 đồng" OR
# "…số tiền 1.200 đồng/cổ phiếu". Used only to COUNT tranches (multi-tranche detection); the
# primary cash value is still extracted via _CASH_RE. Non-overlapping findall counts a single
# "được nhận X đồng/cổ phiếu" once; a bare "10.000 đồng" (no anchor, no /cổ phiếu) is NOT matched,
# so a par/face-value mention never inflates the count.
_CASH_MENTION_RE = re.compile(
    r"(?:được\s+nhận\s+|số\s+tiền\s+)[\d.]+\s*đồng|[\d.]+\s*đồng\s*/\s*(?:cổ\s*phiếu|cp)\b",
    re.IGNORECASE,
)


def _parse_ratio_pct(token: str) -> Optional[float]:
    """Parse a dividend RATIO percentage. Unlike a VND cash amount, a percentage never uses a
    thousands separator — both '.' and ',' are DECIMAL points ('8.5' and '8,5' -> 8.5). (Cash keeps
    _parse_vn_number, where '.' is thousands: '1.200' -> 1200.)"""
    try:
        return float(token.replace(",", "."))
    except ValueError:
        return None
```

### 2. Par plausibility guard (replace the par block, lines 254–262)
```python
        # Par value ("Mệnh giá") for the cash↔ratio cross-check (cash ≈ ratio/100 × par). NOTE:
        # real VSDC pages do NOT carry a par field, so the no-par branch below is the real-world
        # path; par-confirm is a defensive bonus for the rare page that includes it. Trust only a
        # plausible par (≥ 1000 VND) so a stray small number never mis-confirms (SECONDARY).
        par: Optional[float] = None
        par_raw = fields.get("Mệnh giá:")
        if par_raw:
            par_num = re.search(r"[\d.]+", par_raw)
            if par_num:
                par_val = _parse_vn_number(par_num.group(0))
                if par_val is not None and par_val >= 1000:
                    par = par_val
```

### 3. The cash/ratio loop + degrade (replace lines 270–321)
```python
        # Multi-tranche: a page listing >1 per-share cash amount (đợt 1 + đợt 2, in EITHER phrasing)
        # is a single CashDividendEvent in v1 that surfaces only the FIRST tranche — the dropped
        # tranche(s) are DISCLOSED via the degraded token rather than silently lost.
        cash_anchor_count = sum(len(_CASH_MENTION_RE.findall(line)) for line in lines)
        # A ratio token may live on a different justify line than the cash anchor; track whether the
        # page states ANY ratio so a cash-found-but-unpaired result degrades (never silent).
        any_ratio_token = any(_RATIO_RE.search(line) for line in lines)
        for line in lines:
            cash_m = _CASH_RE.search(line)
            if cash_m and cash_per_share is None:
                cash_per_share = _parse_vn_number(cash_m.group("cash"))
                prefix = line[: cash_m.start()]
                # Candidate ratios are the `%/cổ phiếu` tokens BEFORE the cash parenthetical, parsed
                # DECIMAL-aware (8.5% -> 8.5, not 85) and bounded to a plausible ratio (0 < pct ≤
                # 100). A candidate preceded (since the previous candidate) by a net-of-tax marker
                # is flagged net and NEVER served as the gross ratio.
                gross_cands: list[float] = []
                net_present = False
                prev_end = 0
                for rm in _RATIO_RE.finditer(prefix):
                    pct = _parse_ratio_pct(rm.group("pct"))
                    seg = _strip_accents(prefix[prev_end : rm.start()])
                    prev_end = rm.end()
                    if any(mk in seg for mk in _NET_MARKERS):
                        net_present = True
                        continue
                    if pct is not None and 0 < pct <= 100:
                        gross_cands.append(pct)
                had_ratio_token = _RATIO_RE.search(prefix) is not None
                chosen: Optional[float] = None
                if par is not None and cash_per_share is not None:
                    # par cross-check: confirm a gross candidate against the shown cash. A UNIQUE
                    # confirmed value is served; >1 distinct confirmed value is ambiguous (degrade).
                    tol = max(1.0, 0.005 * cash_per_share)
                    confirmed = sorted(
                        {c for c in gross_cands if abs(c / 100.0 * par - cash_per_share) <= tol}
                    )
                    if len(confirmed) == 1:
                        chosen = confirmed[0]
                    elif len(confirmed) > 1:
                        ratio_uncertain = True
                elif len(gross_cands) == 1 and not net_present:
                    # no par to cross-check: serve a single unambiguous gross candidate ONLY when no
                    # net-of-tax marker is on the line (else the shown cash may be net → degrade).
                    chosen = gross_cands[0]
                # par present but nothing confirms, OR no par with an ambiguous / net-qualified line:
                # leave ratio None rather than fabricate/mis-pair — disclosed via the degraded token.
                ratio_pct = chosen
                if had_ratio_token and chosen is None:
                    ratio_uncertain = True
            pay_m = _PAY_LINE_RE.search(line)
            if pay_m and pay_date is None:
                pay_date = _parse_dmy(pay_m.group("date"))

        warnings: list[str] = [EX_DATE_UNAVAILABLE]
        # Degradation (never-silent): surface the event with affected fields None + the token when a
        # PRIMARY field is unparseable (record date, or both ratio AND cash), the cash↔ratio pairing
        # is ambiguous/net-qualified, a ratio is stated on the page but NOT on the cash line
        # (cross-line, unpaired), or the page lists multiple cash tranches (only the first surfaced).
        cross_line_unpaired = (
            cash_per_share is not None and ratio_pct is None and any_ratio_token
        )
        if (
            record_date is None
            or (cash_per_share is None and ratio_pct is None)
            or ratio_uncertain
            or cross_line_unpaired
            or cash_anchor_count > 1
        ):
            warnings.append(VSDC_PARSE_DEGRADED)
```
(Keep the existing `cash_per_share/ratio_pct/ratio_uncertain/pay_date` declarations + `lines =
self._justify_lines(html)` immediately above this block; only the loop body + degrade change.)

### 4. SKILL.md — broaden the `vsdc_parse_degraded` row prose (NO new token)
Update the existing row to mention: net-of-tax (`sau thuế`) ambiguity, dot-decimal ratio, alt-phrased
multi-tranche (`số tiền … đồng/cổ phiếu`), and cross-line (ratio off the cash line). Keep it one row;
do NOT add a new token; do NOT touch `_WARNING_TOKENS_180` (stays 43).

## Tests (add to `tests/test_corp_actions_vsdc.py`, after #9.26; each fail-first on edc9898)
Reuse the existing `_mk_page`/`HEAD` style; synthetic only. Number them #9.27–#9.34:
- **#9.27 D-REV** `8.5%/cổ phiếu (…850 đồng)` no par → `ratio_pct == 8.5` AND `!= 85.0` (clean single
  fractional → NOT degraded).
- **#9.28 D-REV comma** `8,5%/cổ phiếu (…850 đồng)` no par → `ratio_pct == 8.5`.
- **#9.29 D1** net-only `…sau thuế: 10%/cổ phiếu (…1.200 đồng)` no par → `ratio_pct is None` + degraded
  (must NOT be 10.0).
- **#9.30 D2 no-par** `12%/cổ phiếu; thực nhận sau thuế 11,4%/cổ phiếu (…1.140 đồng)` no par →
  `ratio_pct is None` + degraded (must NOT be 11.4).
- **#9.31 D2 par** same line + `Mệnh giá: 10.000 đồng` (net cash 1.140) → `ratio_pct is None` +
  degraded (par must NOT confirm the net 11.4).
- **#9.32 D3** 2 tranches, tranche-2 `…số tiền 1.200 đồng/cổ phiếu` → degraded + `cash_per_share ==
  800` (first tranche surfaced, drop disclosed).
- **#9.33 NOTE cross-line** ratio `10%/cổ phiếu` on one `<br>` line, cash `…được nhận 1.000 đồng` on
  the NEXT line → degraded (must NOT silently return `ratio None` undegraded).
- **#9.34 L1** par 10.000 + `10%/cổ phiếu; sau điều chỉnh 10,04%/cổ phiếu (…1.000 đồng)` → degraded +
  `ratio_pct is None` (ambiguous par-confirmed twins, NOT a silent 10.04).

## Must-stay-green (regression guard — run the WHOLE file + suite)
#9.1/#9.2 (_CLEAN/_THOIGIAN par-confirm), #9.3 (_BUNDLED no-par single), #9.19 (par recovers 12),
#9.21 (multi-tranche degrade), #9.22 (sau-thué+par recovers 12), #9.23 (sau-thué no-par degrades),
#9.24 (>100 degrade), #9.26 (combined). The new logic was traced against ALL of these; if any flips,
STOP and report — do not "fix" the test to match.

## Out of scope (do NOT do)
No new warning token. No snapshot regen / `dump_api_surface.py`. No push, no issue close, no tm-send.
No cross-line ratio PAIRING (degrade only). Deeper bonus-vs-cash par disambiguation = fast-follow.
Return a unified diff + the RED→GREEN evidence (paste the failing-then-passing pytest summary).
