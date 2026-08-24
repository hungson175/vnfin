# SSI/TCX annual operating-cash-flow and net-income source vetting

**Observation date:** 24 August 2026 (UTC+7)
**Issue:** [#231](https://github.com/hungson175/vnfin/issues/231)
**Packet:** `5d499a050dfc7c57302d0abe8ab19953954551ad`
**Published base:** `dbeea0e897e2c6688dd0b01b1cafbf4f04cd358c`
**Disposition:** `SOURCE_GAP_CLOSURE`; the new SSI/TCX source chain remains empty

## 1. Decision and boundary

This is a source/design note only. It does not add a provider, run a new provider probe, add
RED tests, change a parser or model, or claim production coverage. The bounded provider
observations below are inherited from the approved #204 research note dated 22 August 2026;
this #231 round performed static official-page and terms review only. Raw response bodies,
cookies, headers, credentials, and live provider rows remain outside the repository.

The only requested data primitives are annual `MetricId.OPERATING_CASH_FLOW` and
`MetricId.NET_INCOME` for `SSI` and `TCX`. The 26-metric catalog, existing public signatures,
per-statement provenance, current diagnostics, cache/source-selection behavior, annual cadence,
and #204 negative boundary are unchanged. Foreign-flow replay, a 20-pair rule, cohort selection,
cash-accrual scoring, VN30 membership, thresholds, portfolios, and report generation remain caller
composition and are not evidence or acceptance criteria here.

**Result:** none of the four `(symbol, metric)` cells is qualified. The exact disposition is:

| Symbol | `operating_cash_flow` | `net_income` | Why this is not an absence claim |
|---|---|---|---|
| `SSI` | `BLOCKED` / `SOURCE_GAP` | `BLOCKED` / `SOURCE_GAP` | Provider template, item identity, unit, rights, and/or response identity are unproven; no history is declared absent. |
| `TCX` | `BLOCKED` / `SOURCE_GAP` | `BLOCKED` / `SOURCE_GAP` | The same gates remain unproven; observed date gaps in one foreign stream do not prove issuer-history gaps. |

No value is mapped into the current corporate code `32000`, corporate `23003`, or bank `23000`
slots for these securities-company symbols. `modelType=89`, `90`, and `91` remain independent
negative evidence, not a new template. The qualified source chain is `()`.

## 2. Clean-room and evidence classes

The repository blacklist was applied before this research. Every search used the required
exclusion suffix:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted or derived source, code, schema, endpoint map, example, test, package, or
comparison was opened, cited, copied, or used. `finkit` was also excluded. The evidence classes
are deliberately separate:

1. **Official issuer evidence:** SSI and TCBS/TCX financial-report pages and audited annual
   filings establish issuer identity, statement family, fiscal date, accounting concepts, and
   VND cross-checks. They do not grant permission to automate or redistribute a provider route.
2. **Previously retained provider observations:** the #204 note records bounded, no-credential
   observations on 22 August 2026 for the already-approved VNDirect and CafeF candidate surfaces.
   They are not re-probed here and do not become live fixtures.
3. **Official terms/runtime posture:** owner terms, disclaimers, robots, and data-tool pages are
   legal and transport evidence only. Public reachability or `robots.txt` is not a reuse license.

The prior evidence is linked for auditability in [the #204 SSI/TCX source-vetting note](2026-08-22-fundamentals-ssi-tcx-source-vetting.md).

## 3. Official issuer cross-checks

### 3.1 SSI

SSI's official [financial-report index](https://www.ssi.com.vn/en/investor-relation/financial-report)
lists the 2025 audited consolidated financial statements. The linked [official audited
consolidated statement](https://www.ssi.com.vn/upload/files/IR/20260327_SSI_The_2025_Audited_Consolidated_Financial_Statements.pdf)
identifies a securities-company statement for the year ended **31 December 2025** and gives
`Currency: VND`. The filing distinguishes total consolidated profit after tax from parent
attributable profit and non-controlling interests; those distinctions are cross-check evidence,
not a provider item-code authorization. SSI's [2025 annual-report disclosure](https://www.ssi.com.vn/en/investor-relation/information-disclosure/detail/disclosure-of-the-2025-annual-report-and-2025-sustainable-development-report)
also identifies the issuer and ticker `SSI`.

The official audited cash-flow statement establishes the accounting concept “net cash generated
from operating activities” within the securities-company cash-flow statement. It does **not** bind
that concept to the current adapter's numeric code `32000`, to a VNDirect model, or to a legal
right to retrieve and redistribute provider values.

The issuer-line anchors are recorded separately from provider mappings:

| Issuer filing | Official statement/template and date | Issuer line anchor | Unit and use |
|---|---|---|---|
| SSI audited consolidated filing | `B02-CTCK/HN` income statement and `B03b-CTCK/HN` cash-flow statement; year ended 31 December 2025 | Code `200` total profit after tax; code `60`, net cash flows used in operating activities; exact amount `NOT_RETAINED` | `VND`; issuer semantic/scale cross-check only, never a provider item code |
| TCX annual report/audited statement | `B02-CTCK` and `B03-CTCK`; year ended 31 December 2025 | Code `200` total profit after tax; code `60` is the operating-cash-flow concept; the exact 2025 code-60 amount was `NOT_RETAINED`; code `500` is a separate shareholder-appropriation line | `VND`; no amount or provider mapping is inferred |

The SSI code `60` and TCX code `60` are issuer-template line numbers. They do not authorize
current provider code `32000`, and they cannot be copied into a source adapter without a
response-backed provider namespace, item identity, and rights review.

### 3.2 TCX / Techcom Securities

TCBS's official [investor-relations page](https://www.tcbs.com.vn/en/investors/) identifies
Techcom Securities Joint Stock Company and ticker `TCX`; its official [2025 audited-statement
disclosure](https://www.tcbs.com.vn/en/investor-relations/financial-report/information-disclosure-on-tcbss-audited-financial-statements-for-2025-and-audited-financial-safety-ratio-report-as-at-31st-december-2025/)
announces the audited fiscal-year 2025 statements. The linked [official audited statement](https://www.tcbs.com.vn/wp-content/uploads/2026/03/TCX-Audited-Financial-Statements-for-2025.pdf)
uses the securities-company statement family, the year ended **31 December 2025**, and VND.
The filing's total profit-after-tax line and its separate ordinary-shareholder appropriation
line are not interchangeable. That distinction blocks label-only mapping to `net_income`.

The official annual report's cash-flow section is a statement-concept cross-check only. It does
not prove a provider template, item namespace, response identity, retention right, or
redistribution permission.

### 3.3 Cross-check limits

An issuer filing can prove that an annual securities-company statement has a VND fiscal concept.
It cannot prove all of the following provider-side facts: response-backed `symbol`, route version,
template/model, source-namespaced item code, provider scale, revision semantics, complete
requested coverage, no-login automation posture, or package redistribution rights. Therefore the
issuer documents support identity and semantic reopen work but cannot close the source gap.

## 4. Independent source-unit matrix

The tuple key is exactly:

```text
(symbol, source owner, canonical host/path, route/version, operation,
 statement, cadence, requested window, provider template/model)
```

The following **12 request units are independent**; no model numbers, statement operations, or
symbols are flattened. The two CafeF capability rows below are deliberately separate from the
four CafeF direct request units. `#231 dispatches` is zero for every row: this round performed
no provider endpoint probe. The inherited outcomes are bounded observations from #204, not current
runtime claims. `NOT_RETAINED` means that the earlier observation did not preserve that dimension;
it is not a success or a zero.

| Unit | Symbol | Owner / canonical route | Operation / exact non-secret request shape | Statement / cadence / window | Template or model | Inherited bounded outcome | #231 dispatches | Disposition |
|---|---|---|---|---|---|---|---:|---|
| `VD-SSI-I-2` | `SSI` | VNDirect, `api-finfo.vndirect.com.vn/v4/financial_statements` | `GET`; `code=SSI`, `reportType=ANNUAL`, `modelType=2`, `sort=fiscalDate:desc`, `size=640`, `page=1` | income / annual / provider-declared stream; window unproven | `2` | #204 bounded observation: HTTP 200 empty data envelope; response identity/item namespace/unit not accepted | 0 | `SOURCE_GAP`; no absence inference |
| `VD-SSI-I-102` | `SSI` | VNDirect, same canonical route | `GET`; `code=SSI`, `reportType=ANNUAL`, `modelType=102`, same sort/size/page | income / annual / provider-declared stream; window unproven | `102` | #204 bounded observation: HTTP 200 empty data envelope; response identity/item namespace/unit not accepted | 0 | `SOURCE_GAP`; no absence inference |
| `VD-SSI-C-3` | `SSI` | VNDirect, same canonical route | `GET`; `code=SSI`, `reportType=ANNUAL`, `modelType=3`, same sort/size/page | cashflow / annual / provider-declared stream; window unproven | `3` | #204 bounded observation: HTTP 200 empty data envelope; cashflow template/item/unit not accepted | 0 | `SOURCE_GAP`; do not map `32000` |
| `VD-SSI-C-103` | `SSI` | VNDirect, same canonical route | `GET`; `code=SSI`, `reportType=ANNUAL`, `modelType=103`, same sort/size/page | cashflow / annual / provider-declared stream; window unproven | `103` | #204 bounded observation: HTTP 200 empty data envelope; cashflow template/item/unit not accepted | 0 | `SOURCE_GAP`; do not map `32000` |
| `VD-TCX-I-2` | `TCX` | VNDirect, same canonical route | `GET`; `code=TCX`, `reportType=ANNUAL`, `modelType=2`, same sort/size/page | income / annual / provider-declared stream; window unproven | `2` | #204 bounded observation: HTTP 200 empty data envelope; response identity/item namespace/unit not accepted | 0 | `SOURCE_GAP`; no absence inference |
| `VD-TCX-I-102` | `TCX` | VNDirect, same canonical route | `GET`; `code=TCX`, `reportType=ANNUAL`, `modelType=102`, same sort/size/page | income / annual / provider-declared stream; window unproven | `102` | #204 bounded observation: HTTP 200 empty data envelope; response identity/item namespace/unit not accepted | 0 | `SOURCE_GAP`; no absence inference |
| `VD-TCX-C-3` | `TCX` | VNDirect, same canonical route | `GET`; `code=TCX`, `reportType=ANNUAL`, `modelType=3`, same sort/size/page | cashflow / annual / provider-declared stream; window unproven | `3` | #204 bounded observation: HTTP 200 empty data envelope; cashflow template/item/unit not accepted | 0 | `SOURCE_GAP`; do not map `32000` |
| `VD-TCX-C-103` | `TCX` | VNDirect, same canonical route | `GET`; `code=TCX`, `reportType=ANNUAL`, `modelType=103`, same sort/size/page | cashflow / annual / provider-declared stream; window unproven | `103` | #204 bounded observation: HTTP 200 empty data envelope; cashflow template/item/unit not accepted | 0 | `SOURCE_GAP`; do not map `32000` |
| `CF-SSI-I-1` | `SSI` | CafeF, `cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx` | `GET`; `Type=1`, `Symbol=SSI`, `TotalRow=32`, `EndDate=2026`, `ReportType=NAM`, `Sort=DESC` | income / annual / observed candidate dates only; complete history unproven | `Type=1` statement summary | #204 bounded response had `Success=true`, 15 objects for candidate dates 2011–2025; no echoed `Symbol`; observed `K` tags fail current parser | 0 | `SOURCE_GAP`; no typed mapping |
| `CF-SSI-C-3` | `SSI` | CafeF, same canonical handler | `GET`; `Type=3`, `Symbol=SSI`, same bounded parameters | cashflow / annual / accepted window unproven | `Type=3` statement summary | #204 direct observation returned an empty value set; this is not an absence proof | 0 | `SOURCE_GAP`; direct observation only |
| `CF-TCX-I-1` | `TCX` | CafeF, same canonical handler | `GET`; `Type=1`, `Symbol=TCX`, `TotalRow=32`, `EndDate=2026`, `ReportType=NAM`, `Sort=DESC` | income / annual / observed candidate dates only; complete history unproven | `Type=1` statement summary | #204 bounded response had `Success=true`, two objects for 2024–2025; no echoed `Symbol`; observed `K` tags fail current parser | 0 | `SOURCE_GAP`; no typed mapping |
| `CF-TCX-C-3` | `TCX` | CafeF, same canonical handler | `GET`; `Type=3`, `Symbol=TCX`, same bounded parameters | cashflow / annual / accepted window unproven | `Type=3` statement summary | #204 direct observation returned an empty value set; this is not an absence proof | 0 | `SOURCE_GAP`; direct observation only |

These two rows are **capability evidence, not direct request tuples** and have zero physical
provider dispatches in the current adapter:

| Capability unit | Symbol | Operation | Logical evidence | Physical dispatch | Outcome |
|---|---|---|---:|---:|---|
| `CF-SSI-CAP-CASHFLOW` | `SSI` | current adapter cashflow capability for `Type=3` | 1 | 0 | typed `NOT_SERVED` capability; not evidence about direct CafeF `Type=3` |
| `CF-TCX-CAP-CASHFLOW` | `TCX` | current adapter cashflow capability for `Type=3` | 1 | 0 | typed `NOT_SERVED` capability; not evidence about direct CafeF `Type=3` |

The inherited VNDirect foreign streams remain six independent negative rows, separate from the
12 target request units. Each row repeats the complete non-secret route shape and binds to the
specific #204 section/table that retained the observation. `Physical pages / dispatches` counts
provider HTTP pages, not logical model candidates. The model-89/90 rows are only page-one
observations; model 91 was paginated to its provider-declared page count. No row is a statement
candidate.

| Unit | Symbol | Exact canonical route and non-secret request shape | Physical pages / dispatches | Evidence binding | Statement/template/item/unit | Inherited bounded outcome | #231 dispatches | Disposition |
|---|---|---|---|---|---|---|---:|---|
| `VD-SSI-89` | `SSI` | `GET https://api-finfo.vndirect.com.vn/v4/financial_statements`; `q=code:SSI~reportType:ANNUAL~modelType:89`, `sort=fiscalDate:desc`, `size=640`, `page=1` | `1 / 1` | #204 §5.1 raw VNDirect foreign model-stream observations and page-one totals table | statement `UNPROVEN`; template `UNPROVEN`; item `UNPROVEN`; unit `UNPROVEN` | page-one response-backed `code=SSI`, `reportType=ANNUAL`, `modelType=89`; no complete pagination retained | 0 | negative; do not map |
| `VD-SSI-90` | `SSI` | `GET https://api-finfo.vndirect.com.vn/v4/financial_statements`; `q=code:SSI~reportType:ANNUAL~modelType:90`, `sort=fiscalDate:desc`, `size=640`, `page=1` | `1 / 1` | #204 §5.1 raw VNDirect foreign model-stream observations and page-one totals table | statement `UNPROVEN`; template `UNPROVEN`; item `UNPROVEN`; unit `UNPROVEN` | page-one response-backed `code=SSI`, `reportType=ANNUAL`, `modelType=90`; no complete pagination retained | 0 | negative; do not map |
| `VD-SSI-91` | `SSI` | `GET https://api-finfo.vndirect.com.vn/v4/financial_statements`; `q=code:SSI~reportType:ANNUAL~modelType:91`, `sort=fiscalDate:desc`, `size=640`, `page=1..6` (one GET per page) | `6 / 6` | #204 §5.1 raw VNDirect foreign model-stream pagination table | statement `UNPROVEN`; template `UNPROVEN`; item `UNPROVEN`; unit `UNPROVEN` | provider-declared six-page stream-91 sequence; response-backed `code=SSI`; no statement identity or unit | 0 | negative; do not map |
| `VD-TCX-89` | `TCX` | `GET https://api-finfo.vndirect.com.vn/v4/financial_statements`; `q=code:TCX~reportType:ANNUAL~modelType:89`, `sort=fiscalDate:desc`, `size=640`, `page=1` | `1 / 1` | #204 §5.1 raw VNDirect foreign model-stream observations and page-one totals table | statement `UNPROVEN`; template `UNPROVEN`; item `UNPROVEN`; unit `UNPROVEN` | page-one response-backed `code=TCX`, `reportType=ANNUAL`, `modelType=89`; no complete pagination retained | 0 | negative; do not map |
| `VD-TCX-90` | `TCX` | `GET https://api-finfo.vndirect.com.vn/v4/financial_statements`; `q=code:TCX~reportType:ANNUAL~modelType:90`, `sort=fiscalDate:desc`, `size=640`, `page=1` | `1 / 1` | #204 §5.1 raw VNDirect foreign model-stream observations and page-one totals table | statement `UNPROVEN`; template `UNPROVEN`; item `UNPROVEN`; unit `UNPROVEN` | page-one response-backed `code=TCX`, `reportType=ANNUAL`, `modelType=90`; no complete pagination retained | 0 | negative; do not map |
| `VD-TCX-91` | `TCX` | `GET https://api-finfo.vndirect.com.vn/v4/financial_statements`; `q=code:TCX~reportType:ANNUAL~modelType:91`, `sort=fiscalDate:desc`, `size=640`, `page=1..4` (one GET per page) | `4 / 4` | #204 §5.1 raw VNDirect foreign model-stream pagination table | statement `UNPROVEN`; template `UNPROVEN`; item `UNPROVEN`; unit `UNPROVEN` | provider-declared four-page stream-91 sequence; response-backed `code=TCX`; fiscal-date gaps are stream-local only | 0 | negative; do not map |

The retained #204 page accounting is therefore `1 + 1 + 6 + 1 + 1 + 4 = 14` foreign HTTP
pages/dispatches, in addition to the 12 target request dispatches (`4 + 4 + 2 + 2`), for a
bounded inherited total of 26 provider dispatches. This arithmetic uses the explicit #204
page ranges above; if a future audit cannot prove that the model-91 discovery page is the same
retained page 1 used in the complete sequence, the affected aggregate must be `NOT_RETAINED`,
not invented. No current #231 dispatch is implied.

### 4.1 Historical attempt and evidence ledger

The following ledger separates the 12 independent request units, two capability checks, six
inherited negative rows, and the finite static evidence units. Logical units are not physical
HTTP calls; retries, redirects, bytes, rate windows, concurrency, and deterministic waits are
separate dimensions. A static read is not a provider-data dispatch.

| Evidence family | Logical units | Historical physical pages / dispatches | Retries | Redirects | Compressed bytes | Decompressed bytes | Rate window / concurrency / backoff | HTTP/MIME retained | Identity / result | #231 physical dispatches |
|---|---:|---:|---:|---|---|---|---|---|---|---:|
| VNDirect income request units (`SSI`/`TCX` × `2`/`102`) | 4 | 4 pages / 4 dispatches | 0 | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` / `NOT_RETAINED` / `NOT_RETAINED` | 200 + JSON empty envelopes retained in #204 | no accepted response identity/item/unit | 0 |
| VNDirect cashflow request units (`SSI`/`TCX` × `3`/`103`) | 4 | 4 pages / 4 dispatches | 0 | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` / `NOT_RETAINED` / `NOT_RETAINED` | 200 + JSON empty envelopes retained in #204 | no accepted statement/template/unit | 0 |
| CafeF income direct request units (`SSI`/`TCX` × `Type=1`) | 2 | 2 pages / 2 dispatches | 0 | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` / `NOT_RETAINED` / `NOT_RETAINED` | 200 + `text/plain; charset=utf-8` retained in #204 | `Success=true`; response symbol absent; `K` cadence rejected | 0 |
| CafeF cashflow direct request units (`SSI`/`TCX` × `Type=3`) | 2 | 2 pages / 2 dispatches | 0 | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` / `NOT_RETAINED` / `NOT_RETAINED` | 200 + application envelope retained in #204 | empty value set; not absence proof | 0 |
| CafeF adapter capability checks (`SSI`/`TCX`) | 2 | 0 pages / 0 dispatches | 0 | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_APPLICABLE` / `NOT_APPLICABLE` / `NOT_APPLICABLE` | `NOT_APPLICABLE` | typed `NOT_SERVED`; no HTTP call | 0 |
| Inherited foreign negative rows (`89`/`90`/`91` × `SSI`/`TCX`) | 6 | 14 pages / 14 dispatches | 0 | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` / `NOT_RETAINED` / `NOT_RETAINED` | response-backed stream identity only | statement/template/item/unit `UNPROVEN` | 0 |
| Static official evidence units `S01`–`S14` below | 14 | 0 pages / 0 provider-data dispatches | 0 | per-row below | per-row below | per-row below | per-row below | per-row below | legal/semantic cross-check only; never runtime rows | 0 |

The historical physical totals are therefore `4 + 4 + 2 + 2 + 0 + 14 = 26` provider dispatches
plus 14 static evidence reads. No attempt row is synthesized for `diagnostics_truncated`; no
current runtime budget, provider quota, retry promise, or current endpoint behavior is claimed.
The old inherited dispatches are evidence of what was observed on 22 August 2026, not a promise
that a route is available or stable on 24 August 2026.

The 14 static evidence units are finite and individually bounded. `OBSERVED_PAGE` means only that
the official page was used for a cited issuer/terms/transport cross-check; it does not mean a
current no-login API or retained raw response. `NOT_RETAINED` is used rather than inferred MIME,
final URL, redirect, session, UA, WAF, quota, or legal permission.

| Static unit | Canonical official URL | Purpose | HTTP method | HTTP status | Observation mode | Application outcome | MIME | Final identity | Redirects | Retries | Auth | Session | UA | WAF | Rate window | Concurrency | Backoff/wait | Cache | Retention | Deletion | Caller return | Attribution | Commercial | Derivative | Redistribution/resale | Amendment | Revocation | Evidence retention |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S01 | [SSI financial-report index](https://www.ssi.com.vn/en/investor-relation/financial-report) | issuer/report index | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | issuer identity and report-family cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S02 | [SSI 2025 audited consolidated statements](https://www.ssi.com.vn/upload/files/IR/20260327_SSI_The_2025_Audited_Consolidated_Financial_Statements.pdf) | official statement/template/date/VND cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PDF_READ | issuer filing cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S03 | [SSI 2025 annual-report disclosure](https://www.ssi.com.vn/en/investor-relation/information-disclosure/detail/disclosure-of-the-2025-annual-report-and-2025-sustainable-development-report) | issuer/ticker and disclosure cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | issuer disclosure cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S04 | [SSI disclaimer](https://www.ssi.com.vn/en/disclaimer) | publication/reproduction restriction | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | terms cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | NOT_APPLICABLE | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S05 | [TCBS investor relations](https://www.tcbs.com.vn/en/investors/) | TCX owner/ticker/report-family cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | issuer identity cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S06 | [TCBS 2025 audited-statement disclosure](https://www.tcbs.com.vn/en/investor-relations/financial-report/information-disclosure-on-tcbss-audited-financial-statements-for-2025-and-audited-financial-safety-ratio-report-as-at-31st-december-2025/) | audited disclosure cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | issuer disclosure cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S07 | [TCX 2025 audited financial statements](https://www.tcbs.com.vn/wp-content/uploads/2026/03/TCX-Audited-Financial-Statements-for-2025.pdf) | statement/template/date/VND cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PDF_READ | issuer filing cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S08 | [TCBS Terms of Use](https://www.tcbs.com.vn/en/about-us/tcbs-terms-of-use/) | legal/reuse/amendment/revocation cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | terms cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | OBSERVED_RESTRICTION | OBSERVED_RESTRICTION | citation URL and bounded notes only |
| S09 | [VNDIRECT terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) | route owner/legal posture cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | terms cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S10 | [VNDirect API robots](https://api-finfo.vndirect.com.vn/robots.txt) | robots document citation only | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | robots citation only; no directive scope retained | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | citation URL only; directive user-agent/path scope and response body NOT_RETAINED |
| S11 | [CafeF data-tool guidance](https://cafef.vn/du-lieu/ScreenerHelper.aspx) | data-tool/owner posture cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | guidance cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S12 | [CafeF robots](https://cafef.vn/robots.txt) | robots document citation only | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | robots citation only; no directive scope retained | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | citation URL only; directive user-agent/path scope and response body NOT_RETAINED |
| S13 | [CafeF SSI financial documents](https://cafef.vn/du-lieu/hose/ssi-tai-lieu.chn) | symbol/document identity cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | document-page cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |
| S14 | [CafeF TCX financial documents](https://cafef.vn/du-lieu/hose/tcx-cong-ty-co-phan-chung-khoan-ky-thuong.chn) | symbol/document identity cross-check | NOT_RETAINED | NOT_RETAINED | STATIC_PAGE_READ | document-page cross-check only | NOT_RETAINED | NOT_RETAINED; citation URL only | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | UNKNOWN | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | GAP | GAP | UNKNOWN | GAP | UNKNOWN | GAP | GAP | GAP | UNKNOWN | UNKNOWN | citation URL and bounded notes only |

Every static row now distinguishes HTTP method/status from observation mode and application outcome.
No S01-S14 row retains a MIME, final identity, redirect, session, UA, WAF, rate, concurrency, or
backoff fact; `final identity=NOT_RETAINED; citation URL only` is not a final-URL claim. For S10 and
S12, the robots response, user-agent directive, path scope, and final identity are all
`NOT_RETAINED`; neither row says that crawling is allowed. Robots is not a license.

### 4.2 Foreign VNDirect stream boundary

The six `VD-SSI/TCX-{89,90,91}` rows above are separate inherited evidence units, not one
combined fallback. The prior note observed response-backed `code`, annual cadence, and separate
`modelType=89`, `90`, and `91` streams for both symbols. Each row retains only that bounded
observation; statement, template, item, and unit remain `UNPROVEN`. The detailed stream-91
observation also had TCX fiscal-date gaps; that is evidence about stream 91 only, not streams 89/90
or issuer history. No stream may be selected by `is_bank`, human label, industry, neighboring code,
or apparent filing value. The six rows are not an authorization to restate #204 evidence beyond
its cited table.

## 5. Identity, statement, date, unit, and lineage contract

### 5.1 Metric identity

* `operating_cash_flow` means provider-backed **net cash generated from operating activities**.
  Cash balance, investing cash flow, financing cash flow, net cash flow, EBITDA, and a derived
  proxy are different concepts and fail closed.
* `net_income` means the provider-backed total consolidated net income under a qualified template.
  Parent-attributable net income, ordinary-shareholder appropriation, profit before tax, and a
  human-label neighbor are distinct concepts.
* A positive mapping must bind all of `(symbol, source namespace, exact statement, annual cadence,
  provider template/model, source item code, entity scope, fiscal date, value unit)` in one
  response-backed lineage. `is_bank=False` cannot establish a securities-company template.
* The current catalog's `32000`, `23003`, and `23000` values are current adapter namespaces, not
  evidence that SSI or TCX can use them. CafeF string codes cannot occupy a VNDirect numeric slot.

### 5.2 Date, scale, and coverage

* A fiscal date must be provider-backed and annual. Publication, retrieval, effective, quarter,
  YTD, TTM, or restatement dates cannot be relabeled as fiscal year-end.
* Values must be finite raw VND after explicit provider scale or a repeatable exact filing
  cross-check. No guessed `1`, `1_000`, or `1_000_000` multiplier, conversion, rounding, or
  apparent-value matching is allowed.
* `FULL` means every requested annual period inside the provider-declared inclusive bounds is
  present, identity-safe, and reconciled; a missing middle year is not full. `QUALIFIED_PARTIAL`
  is allowed only when the provider declares the bounds and every returned row passes identity,
  statement, cadence, unit, and revision checks. It is not a label for an arbitrary timeout or
  an empty page.
* Unproven bounds are `COVERAGE_UNPROVEN`; identity, date, unit, legal, rate-policy, and
  transport failures remain typed source-gap dimensions. No dimension becomes `MISSING` merely
  because a route returned an empty envelope.

### 5.3 Per-value lineage

Every future available value must retain the existing `MetricInput` fields:

```text
(statement, item_code, value, value_unit, fiscal_date, source, name)
```

`source` must be the canonical source role that actually produced the validated statement, and
must agree with that statement's `MetricReport.statement_sources`. Income and cashflow may use
different qualified sources in a future design; no single report-level source may erase that
distinction. No current source qualifies, so no new lineage is published by #231.

## 6. Legal, runtime, and reuse posture

| Axis | VNDirect candidate | CafeF candidate | Issuer filing cross-check | Current result |
|---|---|---|---|---|
| Public/no-login observation | The inherited #204 observation used HTTPS without credentials or cookies; current/formal no-login, session, UA, and automation posture remains unproven; #231 did not re-probe | Same bounded prior observation; current/formal no-login, session, UA, and automation posture remains unproven; #231 did not re-probe | Public issuer pages/PDFs are reachable as documents | Observation only, not a current uptime or permission claim |
| Owner/identity | VNDirect route owner is the provider host; accepted 2/102/3/103 cells were empty; foreign 89/90/91 identity is not statement identity | CafeF route is public, but tested envelope did not echo `Symbol` | SSI/TCBS pages identify the issuer and ticker | Provider response identity/template gap |
| Automation/caller-return | [VNDIRECT terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) provide website disclaimers and data-collection terms, not an OSS API or redistribution grant | [CafeF data-tool guidance](https://cafef.vn/du-lieu/ScreenerHelper.aspx) describes reference data and no-liability posture, not an OSS/API license | Filing access is not provider-route permission | `LEGAL_GAP` |
| Robots/rate policy | Prior note cited [VNDirect API robots](https://api-finfo.vndirect.com.vn/robots.txt); directive scope and no numeric quota were not retained | [CafeF robots](https://cafef.vn/robots.txt) was cited, but directive user-agent/path scope and response identity were not retained; no crawling permission is inferred | Not applicable | Robots is not a license; future route needs finite self-budget and owner approval |
| Retention/redistribution | No written permission for cached rows, bundled values, derivative redistribution, or resale was found | No written permission for cached rows, bundled values, derivative redistribution, or resale was found | SSI [disclaimer](https://www.ssi.com.vn/en/disclaimer) says site materials are reference-only and restricts publication/reproduction/distribution without written consent | `LEGAL_GAP`; no raw rows or cache |
| Owner amendment/revocation | No route-specific amendment/revocation terms for library reuse were retained | No route-specific amendment/revocation terms for library reuse were retained | TCBS [Terms of Use](https://www.tcbs.com.vn/en/about-us/tcbs-terms-of-use/) reserve changes and prohibit reproduction/distribution/republication/modification without prior written consent; use is personal/non-commercial | Reopen requires written, version-bounded permission and revocation handling |
| Rate/concurrency/backoff | No provider numeric quota was published in the retained evidence | No provider numeric quota was published in the retained evidence | Not applicable | `RATE_POLICY_GAP`; do not invent a quota or retry promise |

The official [TCBS Terms of Use](https://www.tcbs.com.vn/en/about-us/tcbs-terms-of-use/) are an
explicit blocker for package redistribution: they protect website content and permit access only
for personal, non-commercial purposes absent prior written consent. SSI's [disclaimer](https://www.ssi.com.vn/en/disclaimer)
similarly does not grant package rights. The absence of a numeric rate limit is not permission to
choose an unbounded scheduler. No candidate therefore clears the legal/runtime/reuse gate.

## 7. Per-symbol/source-gap disposition

### `SSI`

* **Operating cash flow:** `BLOCKED`. VNDirect accepted cashflow candidates are empty under the
  current contract; foreign streams 89/90/91 lack statement/template/unit identity. CafeF's
  current capability does not serve cashflow. The issuer filing proves the concept and VND only;
  it does not provide a provider item code or reuse permission.
* **Net income:** `BLOCKED`. VNDirect candidate streams are not qualified; CafeF's candidate
  income objects lack response-backed symbol identity and use an observed unsupported `K` tag.
  The issuer filing distinguishes total from parent-attributable income, but cannot authorize
  `LNSTTNDN`/`NetIncome` as a runtime mapping.

### `TCX`

* **Operating cash flow:** `BLOCKED`. The same VNDirect template/unit/rights gaps and CafeF
  not-served cashflow boundary apply. TCBS's B03 evidence is a semantic cross-check only.
* **Net income:** `BLOCKED`. CafeF's candidate rows cover only the observed 2024 and 2025 objects,
  lack response-backed symbol identity, and use the unsupported `K` tag. The TCBS filing's total
  profit-after-tax and separate ordinary-shareholder line must not be merged. The foreign VNDirect
  stream-91 date gaps are not historical absence evidence.

The result for all four cells is `SOURCE_GAP_CLOSURE`, not `MISSING`, `NOT_APPLICABLE`, or a
coverage percentage. The new chain stays empty, and #204's independent negative `89`/`90`/`91`
fixtures and blocked `NET_INCOME` boundary remain authoritative.

## 8. Conjunctive reopen gate

Reopen is per `(symbol, source, statement, metric)` and is conjunctive. A future owner must first
provide written runtime/automation, caller-return, cache/retention, attribution, derivative,
commercial/redistribution, amendment, and revocation permission, or a license that explicitly
covers those uses. Then a fresh design must prove every item below without a new cross-source
inference:

1. **Route and identity:** canonical owner/host/path/version is stable and no-login or uses an
   explicitly approved credential; the response echoes the requested symbol; redirects, mixed
   symbols, and response/request mismatches fail closed.
2. **Statement/template:** income and cashflow are evaluated separately. Provider documentation
   and response fields bind exact securities-company template/model and statement semantics;
   `modelType=89`, `90`, and `91` must each be independently qualified or remain negative.
3. **Metric item:** one source-namespaced provider item code for total consolidated net income and
   one exact operating-cash-flow item are response-backed and cross-checked against an official
   filing for both symbols. Parent-attributable income, profit before tax, cash balance,
   investing/financing/net cash, and neighboring labels remain negative fixtures.
4. **Date/scale:** provider fiscal dates are exact annual dates; units/scale are explicit or
   repeatably cross-checked; raw VND is finite and unrounded. Publication, YTD, TTM, and
   restatement dates fail closed.
5. **Coverage/revision:** provider-declared inclusive bounds and revision/supersession semantics
   are retained. `FULL` requires all requested annual periods, `QUALIFIED_PARTIAL` requires
   declared bounds and reconciled returned pages, and missing middle years remain visible rather
   than fabricated.
6. **Budget/transport:** a deterministic finite global reservation covers logical source units,
   physical pages, redirects, retries, compressed bytes, decompressed bytes, a request-rate window,
   a concurrency ceiling, and deterministic backoff/wait accounting before dispatch. Each logical
   and physical charge occurs exactly once; a later source cannot erase prior private/internal sanitized accounting; public v0.2.0 models expose no failed-attempt trail;
   rate, concurrency, wait, byte, page, or retry exhaustion is atomic and fail-loud. Numeric
   provider limits remain deferred, but these dimensions and their failure behavior are mandatory.
   No numeric provider quota or retry promise may be invented from the current evidence.
7. **API/release:** freeze the existing 26-metric API and public snapshots before RED; prove no
   ratio/extra statement calls, fail-before-cache/network caller validation, validated-result-only
   cache writes, direct/chain parity, stable sanitized diagnostics, imports/version, docs, full
   offline tests, blacklist/secret/diff, and isolated wheel/sdist gates.

Only a future design PASS that closes all seven axes can authorize a separate RED-first review.
This #231 source-gap design does not authorize TDD or production code.

## 9. Deferred RED and release matrix

The following is a future authorization contract, not a test commit. All fixtures are synthetic
offline fixtures; no live symbol may be paired with a live provider value. The matrix is complete
for the current 26-metric public boundary and does not authorize RED, API/model work, or runtime
code in this source-gap round.

### Positive identity rows after qualification

* Each of the 12 request units is evaluated independently: `SSI|TCX` × VNDirect
  `modelType=2|102|3|103` and CafeF direct `Type=1|3`; the two adapter capability checks are
  separate zero-dispatch rows. No model or operation is merged across a symbol or provider.
* Each qualified income and cashflow result has response-backed symbol, exact statement,
  securities-company template/model, provider item code, annual fiscal date, finite raw VND,
  revision identity, complete `MetricInput`, and per-statement provenance.
* Total consolidated net income is distinct from parent-attributable/ordinary-shareholder income
  and profit before tax; operating cash flow is distinct from cash balance, investing, financing,
  and net cash flow.
* Provider-declared complete bounds produce `FULL`; declared, reconciled limited bounds produce
  `QUALIFIED_PARTIAL`; no fabricated year or silent zero is emitted.

### Required scenario rows

| Row | Synthetic positive/negative contract |
|---|---|
| `API-01 zero-qualified-source` | When no source is qualified, both target statements remain typed unavailable/source-gap; `explain_metric_coverage` is non-fatal and truthful, no cache write occurs, and no absence or zero is fabricated. |
| `API-02 explicit multi-source chain/failover` | A caller-provided chain dispatches only capable sources in declared order; source selection and per-statement provenance are preserved, with no hidden fallback or extra statement call. Any sanitized attempt ledger is private/internal test and budget state only; the public v0.2.0 report remains trail-free. |
| `API-03 partial per-statement success` | Income success plus cashflow failure, and the inverse, preserve the successful statement and sanitized failure independently; the failed statement does not erase or downgrade the other. |
| `API-04 all-sources-failed` | Every attempted source failure yields a bounded sanitized public aggregate; private/internal budget state may retain bounded sanitized accounting, but the public v0.2.0 report has no attempt trail, no cache write, no false absence, no silent zero, and no unbounded exception text. |
| `API-05 formula and statement isolation` | Freeze all 26 IDs, catalog order, public shape, and existing guards. `net_margin = net_income / net_revenue` and `operating_cash_flow_margin = operating_cash_flow / net_revenue` follow those existing formulas only when their validated inputs and non-zero guards pass; the remaining 22 unrelated metrics retain values/statuses/order/source behavior, and statement-level mapping cannot rewrite unrelated source items. |
| `API-06 direct/chain source selection and cache` | Direct-source precedence and explicit-chain behavior are deterministic; a validated cache hit avoids dispatch, only a fully validated result writes cache, and cache keys remain compatible. |
| `API-07 v0.2.0 compatibility` | Imports, version, public signatures, constructors, 26-ID catalog/order, DataFrame columns/attrs, serialization, warnings/status vocabulary, and public snapshots remain exactly compatible with v0.2.0. |
| `API-08 failure isolation and later-source preservation` | Income and cashflow failures are isolated; a later source cannot erase prior private/internal sanitized accounting or public warning/source outcomes, while public `MetricReport`, `StatementProvenance`, reprs, DataFrame attrs, and raised messages remain trail-free and v0.2.0-compatible. |
| `API-09 rate/concurrency/backoff ledger` | Every dispatch reserves rate-window tokens and a concurrency slot, records deterministic backoff/wait, and charges logical/physical/pages/retries/redirects/compressed/decompressed bytes exactly once; any exhaustion atomically discards incomplete results and fails closed. Numeric ceilings are set only in a later qualified-source design. |

### Identity, payload, and coverage negatives

* Wrong/absent/contradictory symbol, redirect to another owner, mixed source, wrong statement,
  wrong cadence, wrong template/model, wrong source namespace, wrong item code, and each of
  `89`/`90`/`91` independently fail closed.
* Parent-attributable income, profit before tax, cash balance, investing/financing/net cash,
  EBITDA, derived ratios, neighboring human labels, and issuer code `60` without provider
  namespace cannot satisfy either target metric.
* Missing/mixed VND unit or scale, non-finite values, duplicate/conflicting dates, publication or
  YTD/TTM dates, wrong revision, missing middle year, newest-first pagination errors, empty
  envelopes, malformed payloads, and unbounded pages fail closed without false absence.
* Provider bounds absent, contradictory, or unreconciled cannot be labeled `FULL` or
  `QUALIFIED_PARTIAL`; a page timeout, WAF response, redirect, or empty page is not an empty
  history.
* Static-document visibility, browser-rendered text, or a robots response cannot be promoted to
  response identity, current no-login permission, MIME/final-URL identity, provider unit, or reuse
  rights without retained evidence.

### API, budget, diagnostic, and release negatives

* Malformed caller input fails before cache/network; malformed provider responses fail after
  dispatch but before cache/return; cache writes occur only after complete validation.
* Global reservation is deterministic and atomic across logical units, physical pages, retries,
  redirects, compressed/decompressed bytes, rate-window tokens, concurrency slots, and backoff
  waits. No retry or fallback exceeds the reservation or loses earlier private/internal sanitized accounting; public diagnostics remain the bounded v0.2.0 aggregate.
* Ratio calls remain zero; no extra statement calls, cross-source value stitching, provider rows,
  secrets, cookies, raw headers, URLs with secrets, local paths, provider exception prose, or
  private/internal attempt records enter public models or diagnostics.
* Existing 26 IDs/catalog ordering, signatures, exports, dataclass construction, DataFrame
  columns/attrs, serialization, warning/status vocabulary, cache keys, and #204 SSI/TCX negative
  snapshots remain compatible.

### Required release gates

The future implementation must run focused and full offline tests, import/version checks, docs/API
and units checks, `git diff --check`, blacklist and secret scans, isolated wheel/sdist builds, and
exact merged-tree ancestry/path gates. The test plan must include every row above, including zero
qualified sources, explicit chains, partial statement success, all-sources-failed, the two
existing dependent formulas and their guards (`net_margin = net_income / net_revenue` and
`operating_cash_flow_margin = operating_cash_flow / net_revenue`), the remaining 22 unrelated
metrics with statement-level isolation, cache behavior, v0.2.0 snapshots, and atomic
rate/concurrency/backoff exhaustion. A source-gap PASS instead authorizes only docs/source-gap publication and resolution; it
never transitions to RED or TDD.

## 10. Handoff and no-capability statement

This report is the research artifact for #231 and intentionally closes the new source chain as
empty. It does not claim that SSI or TCX lacks annual statements, and it does not publish provider
rows. The next design artifact binds this matrix to the unchanged API and lifecycle. The durable #232 queue entry remains in the corrected backlog and is closure-gated after #231; only local receipt `a2ccd393f9f3283cc54eb33f4ec3e9d4804d243c` is excluded from the #231 publish ancestry. Before exact
design PASS: no probe, RED, API-model change, production code, push, or issue close. After a
source-gap design PASS: rerun merged docs/full/build/blacklist/secret/diff gates, publish only the
approved research/design/backlog paths, verify exact ancestry, post a clean no-capability
resolution, and close/re-read #231. TDD requires a later, separate qualified-source design PASS.

## Sources

* [SSI financial-report index](https://www.ssi.com.vn/en/investor-relation/financial-report)
* [SSI 2025 audited consolidated financial statements](https://www.ssi.com.vn/upload/files/IR/20260327_SSI_The_2025_Audited_Consolidated_Financial_Statements.pdf)
* [SSI 2025 annual-report disclosure](https://www.ssi.com.vn/en/investor-relation/information-disclosure/detail/disclosure-of-the-2025-annual-report-and-2025-sustainable-development-report)
* [SSI disclaimer](https://www.ssi.com.vn/en/disclaimer)
* [TCBS investor relations](https://www.tcbs.com.vn/en/investors/)
* [TCBS 2025 audited-statement disclosure](https://www.tcbs.com.vn/en/investor-relations/financial-report/information-disclosure-on-tcbss-audited-financial-statements-for-2025-and-audited-financial-safety-ratio-report-as-at-31st-december-2025/)
* [TCX 2025 audited financial statements](https://www.tcbs.com.vn/wp-content/uploads/2026/03/TCX-Audited-Financial-Statements-for-2025.pdf)
* [TCBS Terms of Use](https://www.tcbs.com.vn/en/about-us/tcbs-terms-of-use/)
* [VNDIRECT terms of use](https://www.vndirect.com.vn/dieu-khoan-su-dung/)
* [VNDirect API robots](https://api-finfo.vndirect.com.vn/robots.txt)
* [CafeF data-tool guidance](https://cafef.vn/du-lieu/ScreenerHelper.aspx)
* [CafeF robots](https://cafef.vn/robots.txt)
* [CafeF SSI financial documents](https://cafef.vn/du-lieu/hose/ssi-tai-lieu.chn)
* [CafeF TCX financial documents](https://cafef.vn/du-lieu/hose/tcx-cong-ty-co-phan-chung-khoan-ky-thuong.chn)
