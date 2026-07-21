# Provenance — corporate itemCode + pagination verification probe (2026-07-20, revised 2026-07-21)

Dated evidence artifact for the #198 P0 corporate-fundamentals fix. Revised to satisfy reviewer
round-1 gate `reviews/gate-202607202233-issue198-design-note.md` (`0345fcc`) and round-2 gate
`reviews/gate-202607212049-issue198-regate-round2.md` (`bf60ecb`) — exact-VND residuals (no
tolerance), an **official-filing cross-check per retained code** (FPT FY2025 matrix now read directly
from the audited PDF, incl. `12000`; FY2024 balance reproduced for all four tickers), reconciled
evidence counts (23 named codes), and the full cash-flow audit. Binding spec
`reviews/triage-202607202156-issue198-corporate-fundamentals.md` (`d794c71`). Mirrors
`docs/design/bank-itemcodes-probe-20260620.md` (#157). Companion: `tasks/198-design-note.md`.

## Method

- **Source (clean-room):** the project's own VNDirect api-finfo endpoint
  (`api-finfo.vndirect.com.vn/v4/financial_statements`) via **three legs** — a **raw** query leg
  (LEG A: bypasses the adapter, proves template/code semantics independent of the currently-inverted
  routing), an **adapter routing** leg (LEG B: `VNDirectFundamentalSource`, asserts the full
  provenance tuple, proves the shipped path is fixed), and a **pagination completeness oracle** leg
  (LEG C: raw-fetches the full newest fiscal-date group and requires the adapter to reproduce it
  exactly). No vnstock / no derived material.
- **Script:** `scripts/probe_corporate_itemcodes.py`, gated behind `VNFIN_LIVE=1`, not collected by
  pytest. Re-runnable: `VNFIN_LIVE=1 ./.venv/bin/python scripts/probe_corporate_itemcodes.py`.
- **Tickers:** FPT, VIC, HPG, VNM (tech / conglomerate / steel / consumer).
- **Runs:** 2026-07-20 and 2026-07-21, latest annual fiscal period each ticker exposes (all
  FY2025, fiscalDate `2025-12-31`); balance identity additionally cross-checked on FY2024.
- **Exactness:** every identity residual is an **exact integer `0`** in full VND dong (the probe
  checks `sum(addends) - rhs == 0`, not a relative tolerance).

## 1. modelType identity — which template is which (raw leg, exact VND)

`GET /v4/financial_statements?q=code:{T}~reportType:ANNUAL~modelType:{1|2|3}&sort=fiscalDate:desc&size=300`

### modelType 1 = BALANCE SHEET

Retained codes (FY2025, VND): total assets `12700`, total liabilities `13000`, owners' equity
`14000`, current assets `11000`, non-current assets `12000`, current liabilities `13100`, long-term
liabilities `13300`, cash & equivalents `11100`. Exact FY2025 values:

| Ticker | `12700` total assets | `13000` total liab | `14000` equity | `11000` cur. assets | `11100` cash |
|---|---:|---:|---:|---:|---:|
| FPT | 88,141,991,634,625 | 44,393,950,887,086 | 43,748,040,747,539 | 58,137,438,254,908 | 10,522,105,729,992 |
| VIC | 1,118,622,625,000,000 | 967,133,690,000,000 | 151,488,935,000,000 | 658,772,464,000,000 | 73,542,242,000,000 |
| HPG | 257,899,200,817,547 | 126,679,189,940,972 | 131,220,010,876,575 | 103,659,402,759,724 | 8,300,890,304,205 |
| VNM | 53,312,370,717,301 | 18,829,355,431,194 | 34,483,015,286,107 | 36,261,180,908,033 | 1,794,879,718,871 |

Identities — **residual `0` on all four (FY2025), all exact**:
`13000+14000==12700`; `11000+12000==12700`; `13100+13300==13000`; `14100+14300==14000`;
`11100+11200+11300+11400+11500==11000`.

**FY2024 balance identity `13000+14000==12700` — residual `0` on all four (reproduced by the probe's
second-newest bucket, reviewer R4):**

| Ticker | FY2024 `12700` total assets | `13000` total liab | `14000` equity | residual |
|---|---:|---:|---:|:--:|
| FPT | 71,999,995,678,620 | 36,272,455,573,820 | 35,727,540,104,800 | **0** |
| VIC | 836,603,903,000,000 | 682,769,422,000,000 | 153,834,481,000,000 | **0** |
| HPG | 224,489,707,553,981 | 109,842,249,570,282 | 114,647,457,983,699 | **0** |
| VNM | 55,049,061,537,061 | 18,874,658,707,398 | 36,174,402,829,663 | **0** |

That is 4 tickers × 2 fiscal years = **8 reproducible exact balance checks** (FPT FY2024 also matches
its own official AR comparative, §3). `scripts/probe_corporate_itemcodes.py` LEG A now checks both
the newest and second-newest balance bucket, so this count is reproducible, not asserted.

### modelType 2 = INCOME STATEMENT

Retained codes (FY2025, VND): net revenue `21001`, COGS `22100`, gross profit `23100`, PBT `23800`,
income tax `22070`, PAT total `23003`, PAT parent `23000`, PAT NCI `23500`.

| Ticker | `21001` net rev | `23100` gross profit | `23800` PBT | `23003` PAT total | `23000` PAT parent | `23500` PAT NCI |
|---|---:|---:|---:|---:|---:|---:|
| FPT | 70,112,825,100,710 | 25,888,529,512,413 | 13,043,632,833,797 | 11,232,339,450,734 | 9,376,127,629,501 | 1,856,211,821,233 |
| VIC | 331,837,561,000,000 | 52,682,807,000,000 | 26,437,375,000,000 | 11,064,814,000,000 | 11,349,934,000,000 | −285,120,000,000 |
| HPG | 156,116,094,618,482 | 24,497,788,183,182 | 18,040,591,977,880 | 15,514,931,571,606 | 15,453,174,006,223 | 61,757,565,383 |
| VNM | 63,645,886,756,227 | 26,209,474,194,531 | 11,649,985,224,938 | 9,413,589,732,469 | 9,410,201,646,692 | 3,388,085,777 |

Identities — **residual `0` on all four, all exact**: `21001−22100==23100`; `23800−22070==23003`;
`23000+23500==23003`. The last independently confirms `23000`=parent-attributable PAT and
`23500`=NCI PAT (note VIC's NCI is negative — a genuine loss-making-NCI case, see §3 official
cross-check).

### modelType 3 = CASH FLOW (full audit — reviewer B4)

Retained codes (FY2025, VND): operating `32000`, investing `33000`, financing `34000`, net change
`35000`, begin-cash `36000`, FX effect `36100`, end-cash `37000`. `31000` does not exist in the
probed periods.

| Ticker | `32000` operating | `33000` investing | `34000` financing | `35000` net change | `37000` end cash |
|---|---:|---:|---:|---:|---:|
| FPT | 10,136,043,915,911 | −11,624,743,591,629 | 2,801,322,869,532 | 1,312,623,193,814 | 10,522,105,729,992 |
| VIC | 69,244,889,000,000 | −139,928,403,000,000 | 101,619,123,000,000 | 30,935,609,000,000 | 73,542,242,000,000 |
| HPG | 17,365,859,056,591 | −25,814,392,868,698 | 9,861,932,844,491 | 1,413,399,032,384 | 8,300,890,304,205 |
| VNM | 8,668,137,048,520 | 1,976,101,215,676 | −11,081,926,065,337 | −437,687,801,141 | 1,794,879,718,871 |

Identities — **residual `0` on all four, all exact**: `32000+33000+34000==35000` (three sections sum
to net change) and `35000+36000+36100==37000` (net change + begin-cash + FX = end-cash — the standard
IAS-7 reconciliation). Cross-statement tie-out: `37000` (end cash) exactly equals balance-sheet
`11100` (cash & equivalents) on all four, proving the current `CASH_END_OF_PERIOD=35000` mapping is
wrong (`35000` is net-change, a different, smaller line). The identities prove the three sections sum
correctly but do not by themselves name which is operating vs investing vs financing — that is settled
by the official cross-check in §3.

## 2. Adapter regression leg + pagination (reviewer B10)

- **Pre-fix (current `master`), adapter leg FAILS by design:** `get_financials(..., BALANCE)` routes
  to modelType 2 (real income) and `get_financials(..., INCOME)` routes to modelType 1 (real balance,
  truncated), so none of the headline codes resolve on either side. Post-fix the leg must PASS. The
  probe reports LEG A (raw identities), LEG B (adapter routing), LEG C (pagination) separately, so it
  is never a single opaque pass/fail.
- **Pagination truncation (live 2026-07-21):** VIC balance page 1 (`size=80`) returns 80 rows all for
  `2025-12-31` (of 142 for that date); `14000` (owners' equity) is **absent**. `page=2` returns the
  remaining 62 rows of `2025-12-31` then the start of `2024-12-31` — dates are **contiguous and
  strictly descending**, never interleaved (the load-bearing assumption behind the stop condition).
- **Metadata quirk (live 2026-07-21):** page-1 envelope keys are
  `['currentPage','size','totalElements','totalPages']` (`totalPages=33`); **page ≥2 keys are
  `['currentPage','size']` only** — `totalPages`/`totalElements` are omitted. The loop caches
  `totalPages` from page 1; on later pages it requires equality only if the field is present
  (omission is allowed). `currentPage` is present on every page.

## 3. Official-filing cross-check (clean-room; primary issuer sources only)

An accounting identity proves operands participate in a relationship; it does not name them. Each
retained code below is cross-checked to the issuer's own audited consolidated financial statements
(no aggregators; vnstock excluded).

### VIC — Vingroup FY2024 audited consolidated statements (EY, signed 2025-03-29)

Source: Vingroup **Annual Report 2024 (English)**, audited Consolidated Balance Sheet + Income
Statement, PDF pp.123–125 —
`https://ircdn.vingroup.net/storage/Uploads/0_Bao%20cao%20thuong%20nien/2024/ENG_%20Vingroup%20AR24_250418.pdf`;
corroborated by the 2025 AGM materials —
`https://ircdn.vingroup.net/storage/Uploads/0_Quan%20he%20co%20dong/0_Vingroup_2025/T4/DHCD/20250402%20-%20VIC%20-%20Tai%20lieu%20hop%20DHDCD%20-%20EN.pdf`.
Vingroup presents in VND million; provider values ÷1,000,000 compared. **All EXACT:**

| Provider code | Official line (statement code) | Official (VND mn) | Provider ÷1e6 | Verdict |
|---|---|---:|---:|:--:|
| `12700` | TOTAL ASSETS (270) | 836,603,903 | 836,603,903 | **EXACT** |
| `13000` | C. LIABILITIES (300) | 682,769,422 | 682,769,422 | **EXACT** |
| `14000` | D. OWNERS' EQUITY (400) | 153,834,481 | 153,834,481 | **EXACT** |
| `13100` | I. Current liabilities (310) | 505,292,040 | 505,292,040 | **EXACT** |
| `13300` | II. Non-current liabilities (330) | 177,477,382 | 177,477,382 | **EXACT** |
| `21001` | Net revenue from sale of goods & services (10) | 189,068,040 | 189,068,040 | **EXACT** |
| `23800` | Accounting profit before tax (50) | 16,738,706 | 16,738,706 | **EXACT** |
| `23003` | Net profit after tax (60) | 5,276,058 | 5,276,058 | **EXACT** |
| `23000` | Net PAT attributable to shareholders of the parent (61) | 11,903,028 | 11,903,028 | **EXACT** |
| `23500` | **Net LOSS after tax attributable to NCI (62)** | **(6,626,970)** | −6,626,970 | **EXACT (sign + magnitude)** |

Tie-out: `23000 + 23500` = 11,903,028 + (−6,626,970) = **5,276,058** = `23003` ✓. Vingroup's statement
explicitly labels the NCI line a **"loss"** — an audited adversarial negative-NCI case confirming the
parent/NCI split semantics (reviewer B3, ruling ACCEPT Q2).

### FPT — FY2025 audited consolidated statements (PwC, signed 2026-03-18)

Source: FPT Corporation's own IR filing "CÔNG TY CỔ PHẦN FPT — BÁO CÁO TÀI CHÍNH HỢP NHẤT CHO NĂM TÀI
CHÍNH KẾT THÚC NGÀY 31 THÁNG 12 NĂM 2025" (73 pp., Mẫu B01/B02/B03-DN/HN, auditor PwC Vietnam,
published 2026-03-19) —
`https://fpt.com/-/media/project/fpt-corporation/fpt/ir/information-disclosures/year-report/2026/march/20260319---fpt---bctc-hop-nhat-nam-2025-da-kiem-toan.pdf`.
Figures printed in full VND. (Entity confirmed FPT Corporation, HOSE — a similarly-named `fpt.vn` PDF
is FPT Telecom, a different listed subsidiary, and was discarded.) **Every retained code EXACT — this
is the complete-matrix issuer that also fixes the operating/investing/financing SECTION labels
(reviewer B4):**

| Provider code | Official line (VN, mã) | Official value (VND) | Verdict |
|---|---|---:|:--:|
| `12700` total assets | TỔNG TÀI SẢN (270) | 88,141,991,634,625 | **EXACT** |
| `11000` current assets | TÀI SẢN NGẮN HẠN (100) | 58,137,438,254,908 | **EXACT** |
| `12000` non-current assets | TÀI SẢN DÀI HẠN (200) | 30,004,553,379,717 | **EXACT** |
| `11100` cash & equiv. | Tiền và các khoản tương đương tiền (110) | 10,522,105,729,992 | **EXACT** |
| `13000` total liabilities | NỢ PHẢI TRẢ (300) | 44,393,950,887,086 | **EXACT** |
| `13100` current liabilities | Nợ ngắn hạn (310) | 41,524,928,721,230 | **EXACT** |
| `13300` long-term liabilities | Nợ dài hạn (330) | 2,869,022,165,856 | **EXACT** |
| `14000` owners' equity | VỐN CHỦ SỞ HỮU (400) | 43,748,040,747,539 | **EXACT** |
| `21001` net revenue | Doanh thu thuần (10) | 70,112,825,100,710 | **EXACT** |
| `22100` COGS | Giá vốn hàng bán (11) | 44,224,295,588,297 | **EXACT** |
| `23100` gross profit | Lợi nhuận gộp (20) | 25,888,529,512,413 | **EXACT** |
| `23800` profit before tax | Tổng lợi nhuận kế toán trước thuế (50) | 13,043,632,833,797 | **EXACT** |
| `22070` income tax expense | current (51) 1,916,998,192,442 − deferred benefit (52) 105,704,809,379 | 1,811,293,383,063 | **EXACT (net of two disclosed lines)** |
| `23003` PAT total | Lợi nhuận sau thuế TNDN (60) | 11,232,339,450,734 | **EXACT** |
| `23000` PAT parent | Cổ đông của công ty mẹ (61) | 9,376,127,629,501 | **EXACT** |
| `23500` PAT NCI | Cổ đông không kiểm soát (62) | 1,856,211,821,233 | **EXACT** |
| `32000` operating CF | LC tiền thuần từ hoạt động kinh doanh (20) | 10,136,043,915,911 | **EXACT** |
| `33000` investing CF | LC tiền thuần từ hoạt động đầu tư (30) | −11,624,743,591,629 | **EXACT** |
| `34000` financing CF | LC tiền thuần từ hoạt động tài chính (40) | 2,801,322,869,532 | **EXACT** |
| `35000` net change | Lưu chuyển tiền thuần trong năm (50) | 1,312,623,193,814 | **EXACT** |
| `36000` begin cash | Tiền và tương đương tiền đầu năm (60) | 9,315,440,438,884 | **EXACT** |
| `36100` FX effect | Ảnh hưởng của thay đổi tỷ giá (61) | −105,957,902,706 | **EXACT** |
| `37000` end cash | Tiền và tương đương tiền cuối năm (70) | 10,522,105,729,992 | **EXACT** |

**Honest count (reviewer R4):** 23 named provider codes. **22 of them map 1:1 to a single printed
official line** at the exact VND; **`22070` is the sole exception** — the audited statement prints no
single "total tax expense" line, so `22070` is the exact net of two disclosed lines (current tax mã
51 `1,916,998,192,442` − deferred-tax benefit mã 52 `105,704,809,379` = `1,811,293,383,063`),
consistent with the identity `23800−22070==23003`. The operating/investing/financing SECTION
identities are thus officially named, not merely algebraically summed (reviewer B4).

**Provenance (reviewer R7):** the recorded basis for this FPT matrix is a **direct read of FPT's own
official PwC-audited consolidated PDF** — balance sheet (Mẫu B01-DN/HN, report pp.5–8), income
statement (Mẫu B02-DN/HN, p.9), and cash-flow statement (Mẫu B03-DN/HN, pp.10–11) — every value above
was transcribed from those pages, not from any web-search snippet or aggregator. (A separate research
pass that located the URL used non-exclusion-filtered searches and is **not** relied on as evidence;
the numbers here stand on the official filing alone, and independently on the exact-VND accounting
identities in §1.)

## 4. Evidence-count reconciliation (reviewer B1)

- Balance identity `13000+14000==12700`: 4 tickers × (FY2025 + FY2024) = **8 exact checks** (all 8
  tabulated in §1, reproduced by the probe's two-bucket LEG A), plus the four component identities
  (`11000+12000`, `13100+13300`, `14100+14300`, current-asset sum) each exact on 4 tickers (FY2025).
- Income identities (gross-profit, PBT−tax=PAT, parent+NCI=PAT): each **4/4 exact** (FY2025).
- Cash-flow identities (sections=net-change, net-change+begin+FX=end): each **4/4 exact** (FY2025).
- **Official cross-check coverage:** FPT FY2025 covers the **complete retained matrix — 23 named
  codes** (22 map 1:1 to an official PwC-audited line; `22070` is the exact net of mã 51 − mã 52),
  incl. non-current assets `12000` and the cash-flow section labels; VIC FY2024 covers the 10
  balance/income anchors incl. the parent/NCI split. Every retained `MetricId` code therefore has at
  least one exact official-filing cross-check (the two issuers combined), alongside the 4-ticker
  algebraic checks — satisfying reviewer B1.
- No `xxx`, rounded-trillion, or "matches" placeholder is used under any "exact VND" claim; every
  headline value above is the full-dong integer returned by the provider, and every residual is `0`.
