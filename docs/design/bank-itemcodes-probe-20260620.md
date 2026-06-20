# Provenance — bank itemCode verification probe (2026-06-20)

Dated evidence artifact for the #157 bank-mislabel base-layer fix (reviewer N2). Records the gated
live probe that (a) anchored the corrected bank chart-of-accounts and (b) cleared the Q1 gate
(private banks share the SOCB itemCodes). Companion to `docs/design/bank-fundamentals-itemcodes.md`.

## Method
- **Source (clean-room):** the project's own `VNDirectFundamentalSource` (`api-finfo.vndirect.com.vn
  /v4/financial_statements`) — **no VNStock / no derived material**.
- **Script:** `scripts/probe_bank_itemcodes.py`, gated behind `VNFIN_LIVE=1`, not collected by pytest
  (mirrors `scripts/diagnostics_live.py`). Re-runnable: `VNFIN_LIVE=1 ./.venv/bin/python
  scripts/probe_bank_itemcodes.py`.
- **Query:** `is_bank=True`, `period=ANNUAL`, latest report (fiscalDate desc). Templates: bank balance
  `modelType=101`, bank income `modelType=102`.
- **Run:** 2026-06-20, fiscal_date **2025-12-31** (FY2025 audited annuals).
- **Banks:** controls VCB, CTG (state-owned, anchor); **Q1 targets VPB, ACB (private/joint-stock)**.
  BID values carried from the prior design probe (reviewer Codex×2-verified, review-202606201700).

## Balance sheet — model_type 101 (VND trillion)

| Code | Canonical meaning | VCB | CTG | BID | VPB | ACB |
|---|---|---:|---:|---:|---:|---:|
| `12700` | Total assets (Tổng tài sản) | 2,442.28 | 2,767.70 | *(absent)* | 1,260.15 | 1,025.85 |
| `13000` | Total liabilities (Nợ phải trả) | 2,217.72 | 2,588.04 | 3,157.27 | 1,079.87 | 931.33 |
| `14000` | Total equity (Vốn chủ sở hữu) | 224.56 | 179.66 | 173.55 | 180.28 | 94.52 |
| `412000` | Customer loans (Cho vay khách hàng) | 1,648.55 | 1,957.46 | 2,338.01 | 926.47 | 679.15 |
| `413300` | Customer deposits (Tiền gửi khách hàng) | *(absent)* | 1,793.73 | 2,222.99 | 628.04 | 585.18 |

## Income statement — model_type 102 (VND trillion)

| Code | Canonical meaning | VCB | CTG | BID | VPB | ACB |
|---|---|---:|---:|---:|---:|---:|
| `23800` | Profit before tax (LNTT) | 44.02 | 43.44 | 37.79 | 30.62 | 19.54 |
| `23000` | Profit after tax (LNST) | 35.18 | 34.60 | 29.90 | 23.99 | 15.62 |
| `421900` | Net interest income (Thu nhập lãi thuần) | 58.77 | 66.45 | 63.30 | 58.66 | 26.91 |

## Accounting-identity proof (`13000` + `14000` == `12700`)

| Bank | liabilities + equity | total assets | abs error |
|---|---:|---:|---:|
| VCB | 2,217.72 + 224.56 = 2,442.28 | 2,442.28 | **0** (rel 0.00e+00) |
| CTG | 2,588.04 + 179.66 = 2,767.70 | 2,767.70 | **0** (rel 0.00e+00) |
| VPB | 1,079.87 + 180.28 = 1,260.15 | 1,260.15 | **0** (rel 0.00e+00) |
| ACB | 931.33 + 94.52 = 1,025.85 | 1,025.85 | **0** (rel 0.00e+00) |
| BID | 3,157.27 + 173.55 = 3,330.82 | *(12700 absent)* | n/a (assets code not exposed) |

The identity holds to the exact VND on every bank that exposes `12700` — including both private banks
— proving `12700`=assets, `13000`=liabilities, `14000`=equity are internally consistent and that
`412000` (loans, ≪ assets) and `413300` (deposits) are distinct headline lines, not assets.

## Q1 verdict
**PASS** — VPB and ACB expose all 8 codes-of-interest under the identical templates with the identity
exact. The per-`model_type` bank map generalizes beyond state-owned banks; no whole-bank-class
mislabel risk for the verified set. (`412100`/`23003` remain RAW — near-duplicates, reviewer Q5.)

## Official cross-check (clean-room; no VNStock)
Primary evidence is the probe + identity + cross-bank consistency above. External corroboration of
the headline figures is available from official portals (used read-only for sanity, not ingested):
- **HOSE** disclosure portal — `https://www.hsx.vn` (audited FS / annual reports per ticker).
- **State Bank of Vietnam** — `https://www.sbv.gov.vn`.
- Each bank's investor-relations site (e.g. VCB `https://www.vietcombank.com.vn`, BID
  `https://www.bidv.com.vn`, CTG `https://www.vietinbank.vn`, VPB `https://www.vpbank.com.vn`,
  ACB `https://www.acb.com.vn`).
- VCB FY2025 PBT ≈ 44.0T and NII ≈ 58.4T (clean-room research pass) corroborate `23800`/`421900`.
