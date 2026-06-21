# #163 B2 fix-3 spec — robust net-of-tax detection (round-3 BLOCK, convergent)

**One localized rewrite** of net detection in `vnfin/corp_actions/vsdc.py` :: `parse_announcement`
(the cash/ratio loop) + one new module helper. Closes the 3rd silent-wrong-ratio path (same class)
found CONVERGENTLY by the reviewer (`reviews/review-202606211402-163-vsdc-rereview-BLOCK3.md`) and my
parallel verifier. **Everything surfaces via the EXISTING `vsdc_parse_degraded` token — NO new token,
NO #180/#188 change, NO snapshot regen, tuple stays 43.** TDD: write each fail-first test, confirm RED
on `c0f5f70`, apply the fix, confirm GREEN.

## The defect (3 mechanisms, ONE class: a net rate served as the gross `ratio_pct`)
1. **Fragile allowlist** — `_NET_MARKERS` (5 fixed strings) misses canonical VN tax phrasings:
   `khấu trừ thuế` (THE canonical term), `đã trừ thuế`, `sau khi khấu trừ thuế` (note: the listed
   `sau khi tru thue` is NOT a substring of `sau khi khau tru thue` — verified False), `thuế TNCN`,
   `NET`, `ròng`. → the net rate enters `gross_cands` and is served, no degrade.
2. **Placement** — net detection scans only `prefix[prev_end:rm.start()]` (text BEFORE each `%`).
   A marker TRAILING the candidate (`12%/cổ phiếu sau thuế (…1.140đ)`) is never seen → leaks.
3. **par-confirms-net (worst)** — a net candidate that escaped (1)/(2) is still in `gross_cands`, so
   the par cross-check ACTIVELY confirms it (`Mệnh giá 10.000` + net cash 1.000: 10%×10000=1000=cash
   → serves net 10%). The safety net rubber-stamps the wrong number.

All empirically verified on `c0f5f70`. Worst observed: `11,4%/cổ phiếu sau thuế` (no par) → `ratio=11.4`
undegraded; and the par path confirming the net.

## Fix (structural — token-based detection, NOT more strings)
**Net detection must be (a) robust to phrasing, (b) token-boundary safe** — `thực hiện` (on EVERY page),
`trước thuế` (= GROSS), `internet`, `trong` must NOT register as net — **and (c) placement-aware** (a
trailing marker on the last candidate counts), and **(d) net candidates are excluded from `gross_cands`
hence automatically from the par cross-check** (closes mechanism 3 at its source — par only ever sees
gross candidates).

### EDIT 1 — replace the `_NET_MARKERS` tuple + comment (lines 138–140) with the helper
```python
def _segment_is_net(text: str) -> bool:
    """True when a ratio segment is qualified by a net-of-tax phrase, so its `%` is an AFTER-TAX
    figure that must NEVER be served as the gross dividend ratio. Detected by TOKEN co-occurrence
    (word-boundary, accent-stripped) — NOT substring — so 'thực hiện' (every page), 'trước thuế'
    (gross), 'internet', 'trong' do NOT register as net:
      - thực nhận / thực lĩnh / thực lãnh  (net received)
      - sau … thuế                          (after tax; incl. 'sau khi … thuế')
      - thuế + trừ / khấu / TNCN            (đã trừ / khấu trừ thuế, thuế TNCN)
      - a standalone NET / ròng token
    """
    toks = set(re.findall(r"[a-z0-9]+", _strip_accents(text)))
    if "thuc" in toks and toks & {"nhan", "linh", "lanh"}:
        return True
    if "sau" in toks and "thue" in toks:
        return True
    if "thue" in toks and toks & {"tru", "khau", "tncn"}:
        return True
    if toks & {"net", "rong"}:
        return True
    return False
```
(`_strip_accents` already lowercases, so `[a-z0-9]+` tokenizes the stripped text. Remove the old
`_NET_MARKERS` tuple entirely — it has no other references, verified by grep.)

### EDIT 2 — rewrite the candidate loop (lines 314–325) for token-detection + last-candidate tail
Replace exactly this block:
```python
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
```
with:
```python
                # A net marker binds to the candidate it sits beside: the gap BEFORE a candidate
                # taints THAT candidate (a leading marker, e.g. "thực nhận sau thuế 10%"); the text
                # AFTER the LAST candidate (up to the cash anchor) taints the last candidate (a
                # trailing marker, e.g. "12%/cổ phiếu sau thuế (…)"). A marker BETWEEN two candidates
                # binds to the following one (leading) — this is what lets a clean gross "12%; …sau
                # thuế 10%" recover 12 via par. Net-tainted candidates are EXCLUDED from gross_cands,
                # so they are never served AND never par-confirmed.
                matches = list(_RATIO_RE.finditer(prefix))
                gross_cands: list[float] = []
                net_present = False
                for i, rm in enumerate(matches):
                    pct = _parse_ratio_pct(rm.group("pct"))
                    left_start = matches[i - 1].end() if i > 0 else 0
                    seg = prefix[left_start : rm.start()]
                    if i == len(matches) - 1:
                        seg = seg + " " + prefix[rm.end() :]
                    if _segment_is_net(seg):
                        net_present = True
                        continue
                    if pct is not None and 0 < pct <= 100:
                        gross_cands.append(pct)
                had_ratio_token = bool(matches)
```
**Do NOT change** the par cross-check (`confirmed = sorted({c for c in gross_cands …})` / unique-confirm /
twins→`ratio_uncertain`), the no-par branch (`elif len(gross_cands) == 1 and not net_present:`), the
`ratio_pct = chosen` / `had_ratio_token and chosen is None → ratio_uncertain`, or the degrade block
(`cross_line_unpaired`, `cash_anchor_count`). They are correct once detection feeds them clean pools.

## Tests — add to `tests/test_corp_actions_vsdc.py` after #9.36 (reuse `_justify_page`)
Each fail-first on `c0f5f70` EXCEPT the two negative guards (correct on both — they guard the new path).
- **#9.37** trailing net, single net candidate, NO par: `11,4%/cổ phiếu sau thuế (…1.140 đồng)` →
  `ratio_pct is None` + degraded, `!= 11.4` (the literal net never served).
- **#9.38** trailing net + par cannot confirm: `12%/cổ phiếu; 11,4%/cổ phiếu sau thuế (…1.140)` +
  `Mệnh giá 10.000` → `ratio_pct is None` + degraded (par must NOT confirm the net 11.4).
- **#9.39** par-confirms-net guard: `sau thuế 10%/cổ phiếu (…1.000 đồng)` + `Mệnh giá 10.000` (net cash
  1.000, 10%×10000=1000) → `ratio_pct is None` + degraded (net excluded from `gross_cands` → par never
  sees it). [mechanism 3, the worst case]
- **#9.40** unlisted phrasing `khấu trừ thuế`: `… đã khấu trừ thuế 10%/cổ phiếu (…1.000)` no par →
  `None` + degraded.
- **#9.41** unlisted `đã trừ thuế`: `… đã trừ thuế: 10%/cổ phiếu (…1.000)` no par → `None` + degraded.
- **#9.42 (NEGATIVE)** trailing `trước thuế` (BEFORE tax = gross): `12%/cổ phiếu trước thuế (…1.200)`
  no par → `ratio_pct == 12.0`, NOT degraded (tail-scan must not over-match `trước thuế`).

## Must-stay-green (run the WHOLE file + suite; if any flips, STOP and report — do NOT edit the test)
#9.1/#9.2/#9.3/#9.19/#9.21/#9.22/#9.23/#9.24/#9.26 and the round-2 set #9.27–#9.36 (esp. #9.22/#9.19
par-recovers-12, #9.34 twins, #9.35 clean-gross-serves, #9.36 leading-trước-thuế-serves). All were
hand-traced against the new detection; none should flip.

## Out of scope (do NOT do)
No new warning token. No snapshot regen / `dump_api_surface.py`. No push, no issue close, no tm-send,
no git. NOTE fast-follows tracked separately (backlog), NOT in this commit: (a) malformed `8.5.0%`
parses to 5.0; (b) `…/cp` accepted by `_CASH_MENTION_RE` but not `_RATIO_RE` (silent ratio drop — not
wrong data). Return a unified diff + the RED→GREEN pytest summary (failing-then-passing).
