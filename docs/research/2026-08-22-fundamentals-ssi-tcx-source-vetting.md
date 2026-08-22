# SSI/TCX annual-fundamentals source vetting

**Date of observation:** 22 August 2026 (UTC+7)
**Issue:** [#204](https://github.com/hungson175/vnfin/issues/204)
**Disposition:** documentation/source-gap closure only; no production source or metric claim

## 1. Scope and clean-room boundary

This note answers one question: can the two already-approved, named adapters provide a
lawfully reusable, identity-safe annual statement path for `SSI` and `TCX`, including a
verified `MetricId.NET_INCOME` mapping? It probes each source independently for income,
balance, and cashflow with annual cadence and requested `limit=8`.

It does **not** run the reporter reproduction, use the default failover result as an absence
oracle, add a reporter/failover oracle, implement code, or claim production coverage. Raw
responses were used transiently outside the repository and are not committed. No live rows
are fixtures or bundled datasets.

The mandatory repository blacklist was applied before research. No blacklisted or derivative
source, code, schema, endpoint map, example, or comparison was opened, copied, cited, or used.
Only official provider, issuer, exchange/depository, and regulator surfaces are cited below.

## 2. Decision summary

**No qualified source path exists at the accepted tree for either symbol.** This is a source
gap, not a claim that either issuer lacks historical statements.

| Symbol | What is proven | Blocking axes | Disposition |
|---|---|---|---|
| `SSI` | Official issuer identity and securities-company context; official annual report reports FY2025 ending 31 December 2025 in VND; direct provider probes returned rows in independently foreign/unqualified `modelType=89/90/91` streams; CafeF returned annual income/balance objects | VNDirect statement/template identity is not representable by the current adapter; CafeF current rows use `ReportType=K`, which the current adapter rejects; CafeF response does not echo `Symbol`; no source-specific metric namespace/rights grant | `NO_QUALIFIED_SOURCE` / `MetricId.NET_INCOME=BLOCKED` |
| `TCX` | VSDC and TCBS identify `TCX` as Techcom Securities; official FY2025 filing uses VND and 31 December 2025; direct provider probes returned rows in independently foreign/unqualified `modelType=89/90/91` streams; CafeF returned FY2024–FY2025 income/balance objects | Same template, response-identity, current `K`-tag, source-code, and rights gaps; the raw `modelType=91` date history also has gaps and cannot be promoted or generalized to streams 89/90 | `NO_QUALIFIED_SOURCE` / `MetricId.NET_INCOME=BLOCKED` |

The provider observations below are deliberately retained as **probe outcomes**. An empty
envelope, a parser rejection, or an unrecognized template does not establish issuer absence,
non-existence, or a complete historical date range.

## 3. Official issuer and filing anchors

These sources are cross-check anchors only. They are not permission to copy filing bodies into
the package.

| Symbol | Identity and listing anchor | Filing/template/date anchor | Unit and FY2025 net-income evidence |
|---|---|---|---|
| `SSI` | [SSI disclosure](https://www.ssi.com.vn/en/investor-relation/information-disclosure/detail/disclosure-of-the-2025-annual-report-and-2025-sustainable-development-report) names **SSI Securities Corporation** and ticker `SSI`. | [SSI financial-report page](https://www.ssi.com.vn/en/investor-relation/financial-report) lists the 2025 audited consolidated statement. The [official audited consolidated PDF](https://www.ssi.com.vn/upload/files/IR/20260327_SSI_The_2025_Audited_Consolidated_Financial_Statements.pdf) identifies the securities-company `B02-CTCK/HN` statement for the year ended 31 December 2025 and `Currency: VND`; the [official FY2025 annual report](https://www.ssi.com.vn/upload/files/IR/Reports/SSI_BCTN2025_EN.pdf) is the presentation cross-check. | Audited code 200 total profit after tax is **VND 4,106,880,733,899**; code 201 parent-attributable profit is **VND 4,106,090,416,749**; code 203 non-controlling interests are **VND 790,317,150**. The annual-report summary rounds these to about VND 4,107 billion and VND 4,106 billion. |
| `TCX` | [TCBS investor relations](https://www.tcbs.com.vn/en/investors/) identifies Techcom Securities Joint Stock Company and ticker `TCX`; [VSDC registration](https://vsd.vn/vi/ad/187623) independently identifies `TCX` and the issuer. | [TCBS audited-FS disclosure](https://www.tcbs.com.vn/en/investor-relations/financial-report/information-disclosure-on-tcbss-audited-financial-statements-for-2025-and-audited-financial-safety-ratio-report-as-at-31st-december-2025/) links the [official FY2025 audited statement](https://www.tcbs.com.vn/wp-content/uploads/2026/03/TCX-Audited-Financial-Statements-for-2025.pdf). The report is standalone securities-company `B02-CTCK`, for the year ended 31 December 2025, with `Currency: VND`; the [official annual report](https://www.tcbs.com.vn/wp-content/uploads/2026/03/VIE_TCBS-BAO-CAO-THUONG-NIEN-2025-3.pdf) is an additional cross-check. | Audited code 200 total profit after tax is **VND 5,683,331,855,108**. This standalone report has no parent/non-controlling split; code 500, `NET INCOME APPROPRIATED TO ORDINARY SHAREHOLDERS`, is a separate **VND 5,683,331,855,109** line and differs by VND 1. The provider's equal-looking values cannot be collapsed into one concept. |

The issuer filings prove issuer-level accounting context, date semantics, and currency. They do
**not** by themselves prove that a provider's numeric item code, response template, or
redistribution rights are safe to use.

## 4. Probe protocol and exact routes

All probes were HTTPS GETs made on 22 August 2026 with a browser user-agent, no credentials,
no cookies, and no stored response body. HTTP status and application envelope were recorded
separately. `limit=8` is the requested public adapter limit, not a claim that the provider's
`size` means eight fiscal periods.

### 4.1 VNDirect adapter calls

For both symbols the current `AUTO` path does not classify either symbol as a known bank. Each
logical statement cell therefore attempted the two current template candidates in order:

```text
GET https://api-finfo.vndirect.com.vn/v4/financial_statements
    ?q=code:{SYMBOL}~reportType:ANNUAL~modelType:{1|2|3}
    &sort=fiscalDate:desc&size=640&page=1
GET https://api-finfo.vndirect.com.vn/v4/financial_statements
    ?q=code:{SYMBOL}~reportType:ANNUAL~modelType:{101|102|103}
    &sort=fiscalDate:desc&size=640&page=1
```

`640` is the current adapter's bounded row budget for `limit=8` (`8 * 80`). Every one of the
12 candidate requests returned HTTP `200`, JSON `application/json`, `data=[]`,
`totalElements=0`, and `totalPages=0`; the typed adapter result was
`EmptyData("vndirect: empty data array")`. This is an exact runtime outcome, not proof of no
history.

The unrestricted official observation that found a different template used the same host/path:

```text
GET https://api-finfo.vndirect.com.vn/v4/financial_statements
    ?q=code:{SYMBOL}~reportType:ANNUAL~modelType:91
    &sort=fiscalDate:desc&size=640&page={1..totalPages}
```

It is recorded only to close the source gap, not as an accepted adapter route. The current
adapter's valid statement template sets are `{1,101}` for balance, `{2,102}` for income, and
`{3,103}` for cashflow. `91` is therefore foreign to the current typed contract and must fail
closed until an additive, statement-specific template design proves identity. The later bounded
observations of `89`, `90`, and `91` are three independently foreign streams; none is a combined
securities template and no one stream is evidence for another statement.

### 4.2 CafeF adapter calls

For income and balance the exact bounded requests were:

```text
GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx
    ?Type=1&Symbol={SYMBOL}&TotalRow=32&EndDate=2026&ReportType=NAM&Sort=DESC
GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx
    ?Type=2&Symbol={SYMBOL}&TotalRow=32&EndDate=2026&ReportType=NAM&Sort=DESC
```

`32` is the current adapter's bounded `TotalRow` for `limit=8` (`8 * 4`). Both symbols'
income and balance responses were HTTP `200`, `Content-Type: text/plain; charset=utf-8`, and
JSON with `Success=true`, `Data.Count`, and `Data.Value`. The response had neither a top-level
`Symbol` nor `Data.Symbol`. The current adapter consequently has no response-backed symbol
identity to validate.

For completeness, an independent direct probe of the same official route with
`Type=3&Symbol={SYMBOL}&TotalRow=32&EndDate=2026&ReportType=NAM&Sort=DESC` returned HTTP `200`,
`Success=true`, `Data.Count=15`/`2`, and an empty `Data.Value` for `SSI`/`TCX`. The named
adapter still makes **no HTTP request** for this cell: its static capability contract returns
typed `EmptyData`/`NOT_SERVED` because the summary route does not serve cashflow.

The route is official and independently visible in the [CafeF SSI data page](https://cafef.vn/du-lieu/hose/ssi-tai-lieu.chn),
the [CafeF TCX data page](https://cafef.vn/du-lieu/hose/tcx-cong-ty-co-phan-chung-khoan-ky-thuong.chn),
and the direct [FinanceReport handler](https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx).

## 5. Independent 2 x 2 x 3 matrix

`∅` means no provider fiscal date was accepted by the typed adapter. A CafeF date shown as
`YYYY-12-31*` is derived from response `Time`/`Year` plus annual `Quater=0`; it is not a
provider-supplied ISO fiscal-date field. `raw91` rows are provider observations, not typed
reports. `identity=absent` means the response did not expose a symbol field; the request URL
alone is not response-backed identity.

| Symbol | Source / statement | Official route and exact non-secret parameters | HTTP/application outcome | Identity / template / cadence | Usable rows; fiscal-date set | Unit/scale evidence | Typed adapter result and gap |
|---|---|---|---|---|---|---|---|
| `SSI` | VNDirect / income | `financial_statements`; `q=code:SSI~reportType:ANNUAL~modelType:2`, `sort=fiscalDate:desc`, `size=640`, `page=1`, then `modelType=102` | `200`; empty JSON data envelope | no row identity; no accepted template; request cadence `ANNUAL` | 0; `∅` | no line unit because no rows | `EmptyData`; model/template gap, not no history |
| `SSI` | VNDirect / balance | same path; `modelType=1`, then `101` | `200`; empty JSON data envelope | no row identity; no accepted template; `ANNUAL` | 0; `∅` | none | `EmptyData`; model/template gap, not no history |
| `SSI` | VNDirect / cashflow | same path; `modelType=3`, then `103` | `200`; empty JSON data envelope | no row identity; no accepted template; `ANNUAL` | 0; `∅` | none | `EmptyData`; model/template gap, not no history |
| `SSI` | CafeF / income | `FinanceReport.ashx`; `Type=1`, `Symbol=SSI`, `TotalRow=32`, `EndDate=2026`, `ReportType=NAM`, `Sort=DESC` | `200`; `Success=true`, `Count=15`, `Value` length 15 | `identity=absent`; no `modelType`; annual objects; tags `HK` and `K` | 6 items/object; `2011-12-31*` through `2025-12-31*` | endpoint has no unit field; CafeF page labels result units `(1.000 VNĐ)`; candidate scale ×1000 | `InvalidData`: current parser rejects `ReportType=K`; source identity/template/code/rights remain unqualified |
| `SSI` | CafeF / balance | same path; `Type=2`, other params as above | `200`; `Success=true`, `Count=15`, `Value` length 15 | `identity=absent`; no `modelType`; annual objects; tags `HK` and `K` | 5 items/object; `2011-12-31*` through `2025-12-31*` | same thousand-VND candidate scale; no endpoint unit field | `InvalidData`: current parser rejects `ReportType=K`; source identity/template/rights gap |
| `SSI` | CafeF / cashflow | direct probe: `Type=3`, `Symbol=SSI`, `TotalRow=32`, `EndDate=2026`, `ReportType=NAM`, `Sort=DESC`; adapter makes no request | `200`; `Success=true`, `Count=15`, `Value=[]` | source capability says no cashflow; no identity/template | 0; `∅` | not applicable | `EmptyData` / `NOT_SERVED`; no absence claim |
| `TCX` | VNDirect / income | `financial_statements`; `q=code:TCX~reportType:ANNUAL~modelType:2`, `sort=fiscalDate:desc`, `size=640`, `page=1`, then `modelType=102` | `200`; empty JSON data envelope | no row identity; no accepted template; `ANNUAL` | 0; `∅` | none | `EmptyData`; model/template gap, not no history |
| `TCX` | VNDirect / balance | same path; `modelType=1`, then `101` | `200`; empty JSON data envelope | no row identity; no accepted template; `ANNUAL` | 0; `∅` | none | `EmptyData`; model/template gap, not no history |
| `TCX` | VNDirect / cashflow | same path; `modelType=3`, then `103` | `200`; empty JSON data envelope | no row identity; no accepted template; `ANNUAL` | 0; `∅` | none | `EmptyData`; model/template gap, not no history |
| `TCX` | CafeF / income | `FinanceReport.ashx`; `Type=1`, `Symbol=TCX`, `TotalRow=32`, `EndDate=2026`, `ReportType=NAM`, `Sort=DESC` | `200`; `Success=true`, `Count=2`, `Value` length 2 | `identity=absent`; no `modelType`; annual objects; tag `K` | 6 items/object; `2024-12-31*`, `2025-12-31*` | endpoint has no unit field; official page labels result units `(1.000 VNĐ)`; candidate scale ×1000 | `InvalidData`: current parser rejects `ReportType=K`; source identity/template/code/rights gap |
| `TCX` | CafeF / balance | same path; `Type=2`, other params as above | `200`; `Success=true`, `Count=2`, `Value` length 2 | `identity=absent`; no `modelType`; annual objects; tag `K` | 5 items/object; `2024-12-31*`, `2025-12-31*` | same thousand-VND candidate scale; no endpoint unit field | `InvalidData`: current parser rejects `ReportType=K`; source identity/template/rights gap |
| `TCX` | CafeF / cashflow | direct probe: `Type=3`, `Symbol=TCX`, `TotalRow=32`, `EndDate=2026`, `ReportType=NAM`, `Sort=DESC`; adapter makes no request | `200`; `Success=true`, `Count=2`, `Value=[]` | source capability says no cashflow; no identity/template | 0; `∅` | not applicable | `EmptyData` / `NOT_SERVED`; no absence claim |

### 5.1 Raw VNDirect foreign model-stream observations (not accepted results)

The additional `modelType=91` provider probe was complete to the provider-declared page count,
with the same bounded page size of 640. It proves response-backed `code`, `reportType`, and
`modelType` for **stream 91 only**:

| Symbol | HTTP pages / rows | Response-backed identity | Model/cadence | Complete raw fiscal-date set observed | Interpretation |
|---|---:|---|---|---|---|
| `SSI` | 6 / 3,246 | every row `code=SSI` | `modelType=91.0`, `reportType=ANNUAL` | `2004-12-31` through `2025-12-31` (22 dates) | provider has an unmodeled stream; statement semantics and item identity are unresolved |
| `TCX` | 4 / 2,093 | every row `code=TCX` | `modelType=91.0`, `reportType=ANNUAL` | `2010-12-31` through `2025-12-31` with `2013-12-31` and `2020-12-31` absent | provider has an unmodeled stream; gaps are observations, not historical absence |

The raw rows contain `code`, numeric `itemCode`, `reportType`, `modelType`, `numericValue`,
`fiscalDate`, and provider timestamps, but no statement name or unit field. The presence of
`modelType=91` cannot authorize `is_bank=False`, cannot reuse corporate codes, and cannot be
converted into income/balance/cashflow by item labels or by another library. A raw value that
happens to resemble an issuer filing cross-check is not enough to establish item identity.

A separate bounded official probe of the same annual route also exposed foreign model tags
`89.0`, `90.0`, and `91.0` for both symbols. The observations below are independently filtered
per stream (page-one row count 640 in each stream), not one combined template. Only stream 91 is
paginated to the provider-declared total in the table above; the 89/90 observations remain bounded
observations in this report:

The numeric cells below are the provider-declared `totalElements` values read from the bounded
page-one envelopes; they are not counts of rows paginated by this report. Only stream 91 was then
paginated to its provider-declared total above.

| Symbol | `modelType=89` page-one `totalElements` | `modelType=90` page-one `totalElements` | `modelType=91` page-one `totalElements` |
|---|---:|---:|---:|
| `SSI` | 3,805 | 1,863 | 3,246 |
| `TCX` | 2,594 | 1,273 | 2,093 |

The `modelType=90` stream visibly contains both numeric item codes `23003.0` and `23000.0`,
but no provider semantic field binds them to total versus parent-attributable income. This is
exactly the kind of tempting cross-stream inference the design rejects. The `89` and `90` counts
do not establish the `91` date set, and the `91` TCX FY2020 observation does not govern streams
`89` or `90`. All three streams remain independently foreign, untyped, and fail-closed.

### 5.2 CafeF line identity observations

The current endpoint exposes source-specific string codes, including:

| Symbol | Annual response code | Provider line label | 2025 observed value | Semantic cross-check |
|---|---|---|---:|---|
| `SSI` | `LNSTTNDN` | `Lợi nhuận KT sau thuế TNDN` | `4,106,880,734` (provider thousand-VND candidate) | ×1000 rounds to audited code 200 total `4,106,880,733,899 VND` |
| `SSI` | `NetIncome` | `Lợi nhuận sau thuế của công ty mẹ` | `4,106,090,417` (provider thousand-VND candidate) | ×1000 rounds to audited code 201 parent-attributable `4,106,090,416,749 VND` |
| `TCX` | `LNSTTNDN` | `Lợi nhuận KT sau thuế TNDN` | `5,683,331,855` (provider thousand-VND candidate) | ×1000 rounds to audited code 200 total `5,683,331,855,108 VND` |
| `TCX` | `NetIncome` | `Lợi nhuận sau thuế của công ty mẹ` | `5,683,331,855` (provider thousand-VND candidate) | equal response value is not enough: TCX is standalone and audited code 500 is a separate `5,683,331,855,109 VND` line |

These are source observations, not a shipped mapping. The endpoint itself supplies no unit or
symbol field, and the current adapter rejects the current `K` tag before producing a typed
report. Therefore the apparent value agreement is a **partial cross-check**, not a clean
`MetricId.NET_INCOME` qualification.

For SSI, the audited filing's code 200/201/203 split makes the total-versus-parent distinction
mandatory. For TCX, the standalone code 200 line and the separate code 500 appropriation line
show why even a same-valued provider label cannot be selected by human text alone.

## 6. Source, legal, and runtime qualification

| Axis | VNDirect | CafeF | Required disposition |
|---|---|---|---|
| Transport | HTTPS endpoint accepted the sampled GETs with HTTP 200; no credentials were supplied | HTTPS handler accepted the sampled GETs with HTTP 200; no credentials were supplied | Observation only; no uptime or permission claim |
| Response identity | Independently filtered page-one observations for `89`, `90`, and `91` each carried the requested `code`, annual cadence, and exact requested model; stream `91` is paginated to the provider-declared total above, while `89`/`90` remain bounded observations here | `Symbol` absent at both tested envelope locations | Require response-backed identity for each future typed stream; do not treat bounded `89`/`90` observations as exhaustive |
| Template/schema | `modelType=89`, `90`, and `91` are independently foreign to current 1/2/3 and 101/102/103 contract; no statement partition | no model type; current annual tags include unsupported `K` | Fail closed; add a statement-specific template only after provider + filing evidence |
| Cadence/date | provider gives exact ISO `fiscalDate` on raw `91` rows; the observed TCX `modelType=91` date set has gaps, which is not evidence about streams `89`/`90` or issuer history | provider gives `Time`/`Year` and `Quater=0`; adapter would synthesize 31 December | Never invent years or relabel publication dates |
| Units | `numericValue` has no unit field; no accepted typed report for 91 | endpoint has no unit field; page labels financial table `(1.000 VNĐ)` and ×1000 is only a candidate ingest scale | Require explicit, independently verified scale before raw VND emission |
| Owner/rights | [API robots](https://api-finfo.vndirect.com.vn/robots.txt) says `search=yes,ai-train=no,use=reference`; [VNDIRECT terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) provide disclaimers; no OSS/API redistribution grant found | [CafeF robots](https://cafef.vn/robots.txt) allows `/`; [CafeF data-tool note](https://cafef.vn/du-lieu/ScreenerHelper.aspx) says reference/no liability; no OSS/API redistribution grant found | Runtime-fetch/research only; no bundled rows, cache, or redistribution |
| Rate limits/retry | no numeric API quota published; robots is not a quota | no numeric quota published; robots is not a quota; transient protection can occur | Use a small deterministic self-budget and honor explicit response backoff; do not infer a provider SLA |
| Retention/use | not publicly granted for OSS output retention or bulk reuse | not publicly granted for OSS output retention or bulk reuse | Written owner permission or explicit data/API license is a reopen prerequisite |

The official [TCBS Terms of Use](https://www.tcbs.com.vn/en/about-us/tcbs-terms-of-use/) also
prohibit reproduction/distribution of TCBS website content without prior written consent and
limit use to personal, non-commercial purposes. The audited filing is therefore a cross-check
anchor only; no filing body or provider rows may be redistributed by this package.

## 7. Per-symbol source-gap closure and reopen evidence

### `SSI`

Closed for this round as `NO_QUALIFIED_SOURCE`, with these independent gaps:

1. VNDirect transport works, but the observed annual streams include unmodeled foreign
   `modelType=89/90/91`; the current statement adapter returned `EmptyData` for every accepted
   template candidate.
2. CafeF provides candidate income/balance values, but current `K` report tags fail the
   adapter's cadence validator and the response has no symbol field. Cashflow is explicitly
   not served.
3. The issuer filing cross-check supports VND, year-end, and total-versus-parent semantics but
   cannot prove provider item-code identity or authorize redistribution.
4. `MetricId.NET_INCOME` therefore remains `BLOCKED`; `LNSTTNDN` and `NetIncome` must never be
   placed into the existing VNDirect numeric-code slots.

### `TCX`

Closed for this round as `NO_QUALIFIED_SOURCE`, with these independent gaps:

1. VNDirect returns unmodeled foreign `modelType=89/90/91` streams. The detailed `91` raw
   annual dates include FY2018, FY2019, and FY2021–FY2025 but not FY2020; this is not a claim
   of missing history.
2. CafeF returns only FY2024 and FY2025 candidate income/balance objects, has no response symbol,
   rejects through the current `K` tag, and does not serve cashflow.
3. TCBS official filing evidence proves VND and the securities-company/year-end context, but
   cannot bind the provider's item code/template or grant reuse rights.
4. `MetricId.NET_INCOME` remains `BLOCKED`; equal total/parent-looking 2025 values must not be
   silently merged.

Reopen is **conjunctive per symbol and per source**, not a best-effort score. All of the
following must be true before source implementation review:

- the source owner provides an explicit runtime-use, retention, attribution, and redistribution
  permission, or a license that clearly covers them;
- the response exposes exact requested-symbol identity (or a documented, independently verified
  identity envelope) and the route is stable/no-login or has approved credentials;
- for each statement separately, the provider documents and supports the exact VNDirect stream
  and template for income, balance, or cashflow, with response-backed identity and semantics;
  `modelType=89`, `90`, and `91` must each be qualified independently, never collapsed into one
  template or inferred across statements; foreign, mixed, redirected, or statement-ambiguous
  streams fail closed;
- each target fiscal date is a provider fiscal date, not a publication date; annual cadence is
  independently validated and missing years remain missing;
- provider scale/unit is explicit or proven by a repeatable official filing cross-check, then
  raw VND is emitted without rounding or guessed multiplier;
- for each source/template, total consolidated/company net income and parent-attributable net
  income are separately identified by `(statement, source namespace, template, item code)`;
- at least one official audited filing for each symbol and template version cross-checks the
  exact fiscal date and key values, and all source-specific mappings have fabricated offline
  fixtures rather than live rows; and
- a deterministic bounded request/page budget and conservative backoff policy is documented
  without claiming an unpublished provider quota.

Until every condition is satisfied, the correct status is a typed source gap, not `MISSING`
history and not a production claim.

## 8. Diagnostic/API design that is independent of source qualification

The source gap does not justify silently returning an empty metrics tuple. The accepted future
contract is:

### 8.1 `metrics()` fail-loud boundary

1. At the public wrapper boundary, validate and canonicalize the symbol once before any source or
   ratio call. Pass that canonical symbol to all three logical statement fetches and pure
   transformers. Fetch the statements in stable order: income, balance, cashflow. Never fetch
   ratios for this path. Invalid or malformed input fails before any physical call.
2. If the union of usable fiscal dates is non-empty, preserve today's partial tolerance: return
   aligned `MetricReport`s and represent unavailable statement inputs per metric with the
   existing statuses/reasons.
3. If the union is empty after the three recoverable outcomes, raise the existing typed
   `EmptyData` with this exact bounded message (where `SYMBOL` is normalized and `CADENCE` is
   `annual` or `quarter`):

   ```text
   no usable {CADENCE} fiscal periods for symbol '{SYMBOL}'; call explain_metric_coverage()
   ```

   This message makes no historical-absence claim, contains no raw response, URL, secret,
   provider attempt trail, or exception text, and directs the caller to the non-fatal diagnostic.
   Invalid caller input and contract violations retain their existing typed behavior. A source-level
   `InvalidData`/schema failure is a recoverable `SourceError` outcome and is sanitized by the
   source-error mapping below; this boundary concerns the three recoverable statement outcomes.

### 8.2 Top-level non-fatal coverage

Append this defaulted field **after all existing `MetricCoverage` fields**:

```python
statement_fetches: tuple[StatementProvenance, ...] = ()
```

For `explain_metric_coverage()` the field has exactly three entries in this fixed order:
`(income, balance, cashflow)`, including when `periods == ()`. It is aggregate per statement,
not a failed-source attempt trail.

| Status | Aggregate meaning | `source` | `detail` |
|---|---|---|---|
| `OK` | at least one validated report was accepted | matching canonical role | `None` |
| `MISSING` | an allowed-role direct source completed with no usable requested fiscal period | `None` | exact bounded `no usable {cadence} fiscal periods` |
| `SOURCE_ERROR` | recoverable transport/application/source failure | `None` | exact bounded `recoverable source error` |
| `NOT_SERVED` | no resolved source capability serves the requested statement | bounded composite canonical role(s) | exact bounded `statement {statement} not served by source '{source}'` |

Every public `SOURCE_ERROR` detail uses one allow-listed, bounded, trail-free value exactly equal
to `recoverable source error`. This applies to aggregate `statement_fetches`, per-period
`statement_provenance`, `MetricValue.reason`, and the `detail` field in DataFrame attrs. URL/query
tokens, response bodies, exception text, provider page counts, and failed-source attempt trails
are never copied into public models. Internal diagnostics may retain richer data outside public
models. Source names may identify the responsible source, but never carry a secret-bearing URL.

Before capability resolution and any physical call, apply one total source-role and routing
algorithm. The atomic canonical role allow-list is exactly
`{"vndirect", "cafef", "custom"}`; no raw source name is emitted publicly.

1. Resolve a source object's role by exact name equality, without registration or text rewriting:
   an object whose `name` is the exact string `"vndirect"` or `"cafef"` keeps that role, including
   duck-typed/injected test sources; every missing/raising attribute, non-string, empty,
   URL-bearing, overlong, or other name resolves to the fixed safe role `custom` (six ASCII
   characters).
2. For a single direct `source=`, invoke the original object only when its canonical role serves
   the requested statement. A direct allowed-role completion returning `()` is the reachable
   `MISSING` outcome; a custom or incapable role returns `NOT_SERVED` with zero physical calls.
   An explicit empty `sources=[]` is a typed caller-validation error before any call.
3. For an explicit `sources=` chain, resolve every member, then filter out every incapable role
   before constructing/running failover. Only the original source objects whose canonical role
   serves the requested statement may be invoked; a custom member can never become a fallback
   after an allowed source fails. The default chain resolves to `vndirect,cafef` as usual.
4. A non-empty accepted result must have every returned report's `source` exactly equal to the
   resolved canonical role of the object that produced it. A mismatch is rejected/fail-closed as
   sanitized `SOURCE_ERROR`; it is never silently relabeled. `OK` provenance and `MetricInput`
   lineage use that same matching atomic role.
5. For `NOT_SERVED`, encode the responsible roles as a deduplicated, configured-order comma join
   of atomic roles, with no whitespace and an exact maximum of 21 ASCII characters
   (`vndirect,cafef,custom`). This bounded composite is the only multi-role public source value;
   it is used identically in `StatementFetchResult.source`, `StatementProvenance.source`,
   `statement_fetches`, DataFrame attrs, and the exact detail
   `statement {statement} not served by source '{source}'`.

No name sanitization may truncate or echo arbitrary text. A future custom adapter must explicitly
register a bounded canonical role before it can serve a statement.

For every unavailable metric whose statement outcome is `SOURCE_ERROR`, the public
`MetricValue.reason` is exactly `statement {statement} unavailable: recoverable source error`,
where `{statement}` is the normalized statement enum value. The aggregate/per-period
`StatementProvenance.detail` remains the bare allow-listed `recoverable source error`; the
wrapper template is never replaced by arbitrary provider text.

The existing per-period `statement_provenance` keeps its shape when periods exist, but applies
the same public source-error mapping. When no period exists, the returned object is exactly:

```python
MetricCoverage(
    symbol="SSI",                       # normalized symbol
    period=Period.ANNUAL,
    periods=(),
    notes=("no_fiscal_periods",),
    statement_fetches=(income_outcome, balance_outcome, cashflow_outcome),
)
```

`to_dataframe().attrs["statement_fetches"]` serializes deterministically as exactly:

```python
(
    (statement.value, status.value, source, detail),
    (statement.value, status.value, source, detail),
    (statement.value, status.value, source, detail),
)
```

Existing positional and keyword constructors remain valid because the new defaulted field is
appended after `notes`.

The aggregate transformer is total and pure over typed outcomes; it never parses an exception or
`SourceAttempt.reason` string. For each logical statement, apply this precedence:

1. non-empty validated reports → `OK`, with the producing source;
2. a capability skip → `NOT_SERVED`, with the bounded composite canonical role and the exact
   bounded `statement {statement} not served by source '{source}'` detail;
3. an accepted allowed-role direct completion with an empty validated report tuple → `MISSING`,
   with `source=None` and detail `no usable {cadence} fiscal periods`;
4. a caught source/failover failure, including `EmptyData` inside the default failed chain →
   `SOURCE_ERROR`, with `source=None` and detail exactly `recoverable source error`.

Thus a direct `source=` result with no reports is never `OK`, while a failed default chain is not
reclassified as `MISSING` by inspecting human-readable reasons. `explain_metric_coverage()` uses
this pure mapping and remains non-fatal; `metrics()` may still raise the exact all-empty
`EmptyData` message.

### 8.3 Source-role and metric lineage invariants

- `StatementCoverageStatus.OK/MISSING/SOURCE_ERROR/NOT_SERVED` remain the only statuses.
- `OK` names only the matching atomic role that produced the accepted report; `NOT_SERVED` uses
  the bounded composite role encoding; `MISSING` and `SOURCE_ERROR` do not expose a failed-source
  trail.
- `MetricInput` retains statement, item code, source, raw provider line name, fiscal date,
  value, and unit for every available value.
- A future template-aware extension must add a separate template identity after existing fields
  or under a new immutable provenance object; it must not reinterpret `is_bank=False` as
  securities-company template authorization.
- A source-specific CafeF code belongs only to a CafeF namespace. It can never occupy the
  existing VNDirect numeric `corporate_code` or `bank_code` slots. Until the source/template
  mapping is re-verified, the current `BLOCKED` result is correct.

## 9. Future TDD/verification matrix (no code in this round)

The next implementation review must begin with failing offline tests and synthetic, fabricated
fixtures for both symbols. No live provider row may be committed.

### Diagnostics and compatibility

- three recoverable failures: `metrics()` raises the exact `EmptyData` message; coverage is
  non-fatal with zero periods, exact `("no_fiscal_periods",)`, and exactly three outcomes;
- one success plus two failures: aligned dates still return, per-period provenance and the
  top-level outcome agree, and unavailable metric inputs retain typed reasons;
- CafeF cashflow is `NOT_SERVED`, not exception-text classified;
- RED source-error cases inject URL/query-token, JSON/body, and long-sentinel exception text;
  none may appear in aggregate or per-period provenance, metric reasons, DataFrame attrs, or the
  raised all-empty message;
- RED source-role cases inject an unregistered `source.name` containing a URL/query token plus a
  1,000-character sentinel; assert zero physical calls, only the bounded `custom` role in every
  public source field/detail and DataFrame attr, and no token/sentinel leakage;
- allowed-role duck-typed/injected sources named exactly `vndirect` or `cafef` remain callable;
  an exact-role direct source returning `()` reaches aggregate `MISSING` rather than being skipped;
- a mixed chain `[failing vndirect, malicious custom]` filters `custom` before failover, makes no
  custom call, and leaks neither its token nor its long name; a `cafef + custom` cashflow chain
  returns `NOT_SERVED` with exact composite source `cafef,custom` (maximum 21 characters);
- a non-empty report whose `source` differs from the producing canonical role is rejected/fails
  closed rather than silently relabeled;
- for each source-error metric, bind the exact reason
  `statement {statement} unavailable: recoverable source error`, not the bare detail string;
- exact normalized symbol/cadence strings, status values, detail values, note, repr/equality,
  positional constructor compatibility, and deterministic DataFrame attrs;
- exactly three logical statement outcomes and zero ratio fetches; physical calls are asserted
  separately: explicit CafeF makes two source calls (income/balance) and no cashflow HTTP call,
  while a source that serves all three statements makes three source calls. Adapter-internal
  failover, pagination, and retries are separately bounded physical work, not extra logical
  outcomes.

### Source/template and metric identity

- diagnostics fixtures may use normalized `SSI` and `TCX` symbols with injected empty/failure
  outcomes, but no positive provider row is authorized at this source-gap anchor;
- every `modelType=89`, `90`, and `91` response fixture remains a negative/fail-closed case;
  positive source/template fixtures require a later conjunctive reopen and additive
  entity/template design;
- reject cross-symbol rows, wrong cadence, each foreign/mixed/redirected `89`/`90`/`91` stream,
  malformed/empty envelopes, duplicates, non-finite values, and unit/scale mismatches;
- preserve the observed `modelType=91` annual date set and limit, including absent TCX FY2020;
  do not generalize that stream-91 gap to streams `89`/`90` or to issuer history;
- resolve `NET_INCOME` only from a verified source/template/item-code tuple, in raw VND, with
  exact lineage; keep total and parent-attributable concepts distinct;
- keep an unmapped CafeF namespace `BLOCKED` with the stable source-map reason.

### Repository gates

Run focused injected-HTTP tests, the full offline suite, public API/snapshot/build/import checks,
secret scan, mandatory-blacklist scan, and `git diff --check` on the merged tree. No production
code, push, or issue close is authorized by this note.

## 10. Sources

- [Official VNDirect financial-statements route](https://api-finfo.vndirect.com.vn/v4/financial_statements)
- [VNDirect SSI annual `modelType=91` probe route](https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code%3ASSI~reportType%3AANNUAL~modelType%3A91&sort=fiscalDate:desc&size=640&page=1)
- [VNDirect TCX annual `modelType=91` probe route](https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code%3ATCX~reportType%3AANNUAL~modelType%3A91&sort=fiscalDate:desc&size=640&page=1)
- [VNDirect API robots.txt](https://api-finfo.vndirect.com.vn/robots.txt)
- [VNDirect online-application terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/)
- [Official CafeF FinanceReport route](https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx)
- [CafeF SSI annual income probe route](https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type=1&Symbol=SSI&TotalRow=32&EndDate=2026&ReportType=NAM&Sort=DESC)
- [CafeF TCX annual income probe route](https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type=1&Symbol=TCX&TotalRow=32&EndDate=2026&ReportType=NAM&Sort=DESC)
- [CafeF SSI data page](https://cafef.vn/du-lieu/hose/ssi-tai-lieu.chn)
- [CafeF TCX data page](https://cafef.vn/du-lieu/hose/tcx-cong-ty-co-phan-chung-khoan-ky-thuong.chn)
- [CafeF data-tool guidance](https://cafef.vn/du-lieu/ScreenerHelper.aspx)
- [CafeF robots.txt](https://cafef.vn/robots.txt)
- [CafeF privacy policy](https://cafef.vn/static/chinh-sach-bao-mat.html)
- [SSI FY2025 annual-report disclosure](https://www.ssi.com.vn/en/investor-relation/information-disclosure/detail/disclosure-of-the-2025-annual-report-and-2025-sustainable-development-report)
- [SSI financial-report page](https://www.ssi.com.vn/en/investor-relation/financial-report)
- [SSI FY2025 annual report](https://www.ssi.com.vn/upload/files/IR/Reports/SSI_BCTN2025_EN.pdf)
- [TCBS investor relations](https://www.tcbs.com.vn/en/investors/)
- [VSDC TCX registration](https://vsd.vn/vi/ad/187623)
- [TCBS FY2025 audited-FS disclosure](https://www.tcbs.com.vn/en/investor-relations/financial-report/information-disclosure-on-tcbss-audited-financial-statements-for-2025-and-audited-financial-safety-ratio-report-as-at-31st-december-2025/)
- [TCX FY2025 audited statement](https://www.tcbs.com.vn/wp-content/uploads/2026/03/TCX-Audited-Financial-Statements-for-2025.pdf)
- [TCBS FY2025 annual report](https://www.tcbs.com.vn/wp-content/uploads/2026/03/VIE_TCBS-BAO-CAO-THUONG-NIEN-2025-3.pdf)
- [TCBS Terms of Use](https://www.tcbs.com.vn/en/about-us/tcbs-terms-of-use/)
