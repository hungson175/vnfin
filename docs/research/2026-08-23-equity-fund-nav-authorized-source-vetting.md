# #225 authorized equity-fund NAV — source and legal vetting

**Artifact:** `docs/research/2026-08-23-equity-fund-nav-authorized-source-vetting.md`
**Research date:** 24 August 2026 (UTC+07); the packet fixes the `2026-08-23` filename.
**Packet:** `tasks/225-equity-fund-nav-authorized-source-spec.md` at reviewer `7b7fe0b`
**Requested inclusive interval:** `2018-01-01..2026-08-19`
**Disposition:** **`SOURCE-GAP CLOSURE`** — no one owner/route unit currently proves identity, coverage,
bounded lawful automation, and downstream reuse together.

This is a clean-room source/design record, not a runtime capability. The current funds API and
Fmarket fail-closed boundary remain unchanged. No provider data/API route was dispatched, no live
fund list or NAV value was retained, and no RED test, production code, source registration, model
change, public API claim, push, or issue closure is authorized by this artifact.

## 1. Decision and qualification boundary

The requested primitive is valid in scope, but a source is qualified only when the following tuple
is proven by one owner-backed route set for its own declared fund universe:

```text
one owner + one canonical route/version + no-login automation terms
+ response-backed open-ended equity-fund identity
+ stable fund code and provider product identifier
+ discovery-to-history identifier binding owned by that source
+ provider-published NAV/unit, exact NAV date, currency and units
+ publication/revision/correction semantics kept distinct from retrieval time
+ reconciled requested or owner-declared partial coverage
+ finite source-approved transport/rate/retry/byte budget
+ caller-return, cache/storage, retention, attribution, commercial and redistribution rights
```

No candidate passes the tuple. The deterministic outcome is `SOURCE-GAP CLOSURE`, not
`QUALIFIED FOR TDD` and not `QUALIFIED_PARTIAL`. The empty new source chain is intentional:

- no new fund asset-type token, source registry entry, provider ID type, model field, accessor,
  diagnostic enum, or result carrier is added;
- no market-wide universe is inferred from one manager's catalogue;
- no ETF, balanced, bond, money-market, pension, closed-end, or private-fund product is accepted
  as an equity mutual fund substitute;
- no NAV date is treated as the time at which the value became knowable;
- no manager, registry, exchange, or document route is stitched to another owner's history; and
- a blank page, HTML/WAF response, timeout, missing document, or unreconciled response is not an
  absence oracle.

A future shorter history can be `QUALIFIED_PARTIAL` only when the same qualified provider declares
and reconciles its supported boundary. It cannot be called `FULL` for the requested interval.

## 2. Clean-room, no-probe, and evidence-channel rules

Before this research I read [`docs/vnstock-blacklist.md`](../vnstock-blacklist.md). Every web
search used this mandatory exclusion:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted result, page, code, documentation, schema, endpoint map, package, test, or derived
behavior was opened, cited, compared, or used. Evidence below is limited to official manager,
regulator, depository, exchange, provider-terms, and repository-contract material. No unofficial
mirror, copied endpoint map, paid feed, login/session route, proxy, reporter artifact, or old
third-party implementation was used.

Two evidence channels are kept separate:

1. **Static official-document research.** Official pages, catalogues, terms, PDFs, and local
   reviewed source/legal artifacts were read. The research tool did not retain a transport log for
   those documents, so static logical/physical/page/retry counters are
   `NOT_RETAINED`/`NOT_MEASURED`, never zero. Query-bearing navigation strings are not retained in
   this report; canonical paths and parameter intent are separate.
2. **Candidate data/API dispatch.** No Fmarket, SSIAM, VinaCapital, VSDC, SSC, or other candidate
   data/API route was called. Candidate dispatch is exactly `0 / 0 / 0 / 0` for
   logical targets / physical calls / page-or-cursor calls / retries. No response body, fund list,
   NAV value, header block, cookie, credential, redirect result, MIME observation, response digest,
   or provider exception is stored.

| Channel | Logical | Physical | Pages/cursors | Retries | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| Static official pages/documents | `NOT_RETAINED` / `NOT_MEASURED` | `NOT_RETAINED` / `NOT_MEASURED` | `NOT_RETAINED` | `NOT_RETAINED` | Evidence inventory only; not a candidate dispatch |
| Candidate fund discovery/history routes | `0` | `0` | `0` | `0` | No provider data/API request was made |
| Fmarket/Fincorp | `0` | `0` | `0` | `0` | Explicitly prohibited by the #221 pending-permission boundary |
| Credentials, cookies, login/session bypass, proxy, challenge solving | `0` | `0` | `0` | `0` | None |

`NOT_RETAINED` means that the field was not obtained or transport-measured in this design round;
it is not a negative response, an empty result, a coverage claim, or a permission inference.

## 3. Existing runtime and compatibility boundary

The current public shapes remain the only compatibility baseline:

```python
vnfin.funds.source().list_funds(asset_type="STOCK")
vnfin.funds.source().nav_history(product_id, from_date=None, to_date=None)
```

Current facts relevant to this packet:

| Surface | Current truth | #225 boundary |
| --- | --- | --- |
| `vnfin.funds.source()` / `client()` | Lazy construction; valid Fmarket operations fail before cache/network with `SourceUnavailable("SOURCE_DISABLED_PENDING_PERMISSION")` | Preserve exactly; no alternate route may bypass it |
| `FundList` / `Fund` | Existing typed list and fund fields; `Fund.id` is the current integer provider-ID shape | No new ID coercion or model widening in a source-gap packet |
| `NavHistory` / `NavPoint` | Existing product-ID history, date, NAV, currency/unit and provenance shape | No new publication/revision carrier or source field now |
| Existing Fmarket parser tests | Synthetic private fixtures only | They are not provider permission, identity, coverage, or reuse evidence |
| #218 ETF evidence | Separate ETF source-gap record | It cannot qualify open-ended equity mutual funds or be generalized |

The current Fmarket result is a **policy-disabled source**, not an available candidate. The
approved #221 audit remains the legal/runtime record: Fincorp's public terms did not grant
`api.fmarket.vn` software automation, caller-facing return, storage/retention, commercial use,
or redistribution. No Fmarket request was made in this round. A fresh written owner response must
bind the exact host and listing/NAV operations plus automated access, caller return, storage,
retention, commercial use, attribution, redistribution, rate/retry/WAF/session, version/effective
date, amendment, and revocation before that disposition can be reconsidered.

## 4. Official evidence inventory

### 4.1 SSIAM manager-owned route family — promising but not qualified

The official SSI Asset Management pages are the strongest candidate found for a bounded,
manager-owned unit. The query-free canonical references are:

- [SSIAM SSI-SCA fund information](https://ssiam.com.vn/en/fund-information-ssi-sca)
- [SSIAM products](https://ssiam.com.vn/en/products)
- [SSIAM VLGF fund information](https://ssiam.com.vn/en/ssiam/fund-information-vlgf)
- [SSIAM online-trading terms](https://ssiam.com.vn/en/ssiam/term-condition)

The SSI-SCA page identifies the manager-owned product as a **Mutual Equity Fund**, exposes the
fund code `SSI-SCA`, gives an inception-date field, labels NAV per unit in VND, and presents a
history/document area with daily NAV-report entries. The products page separates open-ended funds
from ETFs and identifies SSI-SCA as an open-ended actively managed product; its SSIBF and FUESS
entries are useful negative controls, not equity-fund positives. The VLGF page is another official
manager page with NAV/document sections, but this no-probe review did not retain a complete
response-backed product-class, ID-binding, or history-boundary record for it.

The SSIAM online-trading terms describe an investor-facing online service and related product
contracts. They do not, in the material reviewed, establish a public developer/API licence for
machine collection, a caller-facing OSS return grant, cache/retention terms, redistribution/resale
rights, an anonymous automation quota, or a revision/withdrawal contract for NAV documents. The
terms are therefore a legal/runtime gap, not permission. A page exposing a document link or a
current NAV label is not a grant to automate and republish it.

### 4.2 Other official manager/issuer route families — candidates, not qualified sources

The static review also covered official route families for VinaCapital, VCBF, Eastspring,
Manulife, and Dragon Capital. Canonical query-free references include:

- [VinaCapital VEOF](https://vinacapital.com/investment-solutions/onshore-funds/veof/),
  [VESAF](https://vinacapital.com/investment-solutions/onshore-funds/vesaf/),
  [VDEF](https://vinacapital.com/investment-solutions/onshore-funds/vdef/), and
  [official channels](https://vinacapital.com/vinacapital-channels/);
- [VCBF MGF](https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-midcap-growth-fund/),
  [BCF](https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-blue-chip-fund/),
  [AIF](https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-active-income-fund/), and
  [VCBF NAV-report index](https://www.vcbf.com/en/investor-relations/fund-reports/net-asset-value-change-report/);
- [Eastspring EVESG](https://www.eastspring.com/vn/en/funds/enf/funddetails/eastspring-investments-vietnam-esg-equity-fund/evesg)
  and its [document archive](https://www.eastspring.com/vn/en/funds/archive-documents/investor-relations/evesg);
- [Manulife MAFEQI](https://www.manulifeim.com.vn/funds/fund-details.fid-MAFEQI.html); and
- [Dragon Capital DCDS](https://dautu.dragoncapital.com.vn/dcds) and its
  [official catalogue](https://dautu.dragoncapital.com.vn/).

These pages identify real open-ended equity products or dated report/document families. VinaCapital
and VCBF primarily expose downloadable reports; Eastspring and Manulife publish explicit reuse
restrictions or require consent; Dragon's public comparison material attributes NAV sourcing to a
third-party platform rather than proving an independent manager-owned history route. None of the
reviewed families supplies, in one no-probe unit, a complete machine-readable history index,
response-backed provider ID crosswalk, reconciled totals/pages/cursors, revision contract, and
positive OSS automation/caller-return/redistribution grant. They remain independent `SOURCE-GAP`
units, not failover candidates.

The [VinaCapital VEOF official factsheet](https://wm.vinacapital.com/wp-content/uploads/2026/06/20260615-VINACAPITAL-VEOF_Monthly-Factsheet_May-2026-EN.pdf)
is an official manager document with equity-fund/NAV-per-unit context, but it is periodic document
support, not proof of a daily history route. The [VinaCapital VN100 ETF page](https://wm.vinacapital.com/investment-solutions/onshore-funds/vinacapital-vn100-etf/)
is retained only as an ETF negative control. The [VinaCapital terms page](https://vinacapital.com/terms-and-conditions/)
and manager copyright notices do not provide a positive machine-use/data-redistribution grant.

The [Eastspring disclaimer](https://www.eastspring.com/vn/en/disclaimer) and [Manulife terms](https://www.manulifeim.com.vn/terms-of-use.html)
are explicit negative evidence against treating a public report as a free redistribution licence.
The VCBF catalogue displays all-rights-reserved material without a public API/data licence in the
reviewed pages. These are legal blockers, not claims that no private permission could ever exist.

### 4.3 Regulatory classification and NAV authority

Official securities-law material distinguishes public, open-ended, closed-ended, member funds, and
ETFs; an ETF is a special open-ended form with listed/traded certificates, so it must not be
treated as the same product class as an unlisted open-ended equity fund. "Equity fund" is an
investment-objective/category label, not by itself a complete legal fund form. The qualification
identity therefore comes from the manager's charter/prospectus/disclosure plus the supervisory-bank
and registration context, not a product name alone. The reviewed legal material also places NAV
calculation with the fund manager and confirmation with the supervisory bank. Disclosure duties and
public accessibility are not downstream reuse authorization.

### 4.4 VSDC and SSC — registry/disclosure context, not a NAV owner route

Primary regulatory/depository references:

- [VSDC fund services](https://vsd.vn/en/)
- [VSDC fund managers and registration](https://vsd.vn/en/qlq)
- [SSC official portal](https://ssc.gov.vn/) — the consolidated disclosure document and Circular 98
  references were reviewed by official document identity; query-bearing document locators are not
  retained in this repository.

VSDC's official pages establish fund-service/registration roles and distinguish listed
closed-end/ETF certificate registration from fund services for open-ended funds. SSC material
establishes disclosure/regulatory context. The manager calculates NAV and the supervisory bank
confirms it; neither VSDC's public registry nor SSC's disclosure portal becomes the manager's
historical NAV owner merely because it publishes registration or disclosure metadata. Neither
review establishes a caller-return API or grants this library redistribution rights. Registry
identity can support a future identity check only if the manager or regulator documents a stable
crosswalk to the same NAV provider ID; it cannot silently repair a manager route or authorize a
different owner's rows.

### 4.4 Fmarket/Fincorp — unchanged pending permission

The local reviewed artifact [`#221 Fmarket audit`](../2026-08-23-fmarket-current-runtime-terms-audit.md)
and the official [Fmarket legal page](https://fmarket.vn/legal) remain the controlling evidence.
The exact current outcome for listing, NAV history, holdings, and allocation is
`DISABLE_PENDING_PERMISSION`. This source-gap packet does not re-open, probe, or modify that
source.

## 5. Candidate matrix: each operation is independently disposed

A qualification unit is one owner, one exact canonical route, one operation, and one product class.
Every discovery and history operation below is a separate row; no grouped fund, wildcard path, or
cross-source stitch is used. `STATIC_DOCUMENT_REFERENCE` means only that an official page/document
was read; it does not mean a candidate response was dispatched. Static product-class controls are
also kept separate from admitted equity-fund units.

| Candidate unit | Owner/exact canonical route | Static identity evidence | History/coverage evidence | Transport/runtime | Legal/reuse and result |
| --- | --- | --- | --- | --- | --- |
| Fmarket listing/discovery | Fincorp; `POST https://api.fmarket.vn/res/products/filter` | Current parser contract only; no provider response | `NOT_PROBED`; no provider boundary | `0/0/0/0`; disabled before cache/network | #221 terms/API/caller-return gap; `DISABLE_PENDING_PERMISSION` |
| Fmarket NAV history | Fincorp; `POST https://api.fmarket.vn/res/product/get-nav-history` | Synthetic product-ID contract only; no provider response | `NOT_PROBED`; no provider boundary | `0/0/0/0`; no fallback | #221 terms/API/caller-return gap; `DISABLE_PENDING_PERMISSION` |
| SSIAM SSI-SCA discovery | SSIAM; `https://ssiam.com.vn/en/fund-information-ssi-sca` | Official page identifies `SSI-SCA`, manager, code, and `Mutual Equity Fund` | Provider ID, served bounds, totals and response identity `NOT_RETAINED` | Static reference; `0/0/0/0`; MIME/effective route/bytes `NOT_RETAINED` | Automation, caller return, cache/retention, commercial, attribution, redistribution, rate/retry, amendment/revocation `LEGAL_GAP` |
| SSIAM SSI-SCA NAV history | SSIAM; `https://ssiam.com.vn/en/fund-information-ssi-sca` | Official page labels NAV/unit and daily NAV-report documents | Requested `2018-01-01..2026-08-19`, totals, pages, gaps, duplicates, revisions `NOT_RETAINED` | No document/data dispatch; `0/0/0/0`; MIME/effective route/bytes `NOT_RETAINED` | No public OSS/API/reuse grant in reviewed terms; `SOURCE-GAP` |
| SSIAM VLGF discovery | SSIAM; `https://ssiam.com.vn/en/ssiam/fund-information-vlgf` | Official manager page and product/document identity support; response ID `NOT_RETAINED` | Open-ended equity proof, served bounds and totals `NOT_RETAINED` | Static reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Automation, caller return, storage, retention, redistribution and revision `LEGAL_GAP` |
| SSIAM VLGF NAV history | SSIAM; `https://ssiam.com.vn/en/ssiam/fund-information-vlgf` | Same exact manager route is the retained history/document unit; crosswalk `NOT_RETAINED` | Requested bounds, page reconciliation, daily rows and revision identity `NOT_RETAINED` | Static reference; `0/0/0/0`; transport fields `NOT_RETAINED` | No public OSS/API/reuse grant in reviewed terms; `SOURCE-GAP` |
| SSIAM SSIBF discovery control | SSIAM; `https://ssiam.com.vn/en/products` | Official catalogue identifies SSIBF as a bond product, not requested equity class | No equity-fund history qualification attempted; `NOT_APPLICABLE` | Static product-class control; no dispatch; `0/0/0/0` | Not an admitted equity candidate; `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| SSIAM SSIBF NAV-history control | SSIAM; `https://ssiam.com.vn/en/products` | Official catalogue control only; no same-owner equity history unit | NAV history for requested equity class `NOT_APPLICABLE` | No dispatch; `0/0/0/0` | Not an admitted equity candidate; `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| SSIAM FUESS product-row discovery control | SSIAM; `https://ssiam.com.vn/en/products` | Official catalogue separates FUESS ETF rows from open-ended mutual funds | ETF control is not an equity-mutual-fund history boundary | Static product-class control; no dispatch; `0/0/0/0` | Not an admitted equity candidate; `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| SSIAM FUESS product-row NAV-history control | SSIAM; `https://ssiam.com.vn/en/products` | Official catalogue control only; ETF rows are not silently mapped to `STOCK` | NAV history for requested equity-mutual-fund class `NOT_APPLICABLE` | No dispatch; `0/0/0/0` | Not an admitted equity candidate; `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| VinaCapital VEOF discovery | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/veof/` | Official manager page identifies VEOF as an open-ended equity product | Provider ID, response fields, bounds and totals `NOT_RETAINED` | Static page reference; `0/0/0/0`; MIME/effective route/bytes `NOT_RETAINED` | Terms/copyright do not grant automation or redistribution; `LEGAL_GAP` |
| VinaCapital VEOF NAV history | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/veof/` | Same exact manager page is the retained history/document unit | Monthly factsheet/report support is not a reconciled daily history; requested bounds `NOT_RETAINED` | Static reference; `0/0/0/0`; no PDF/document dispatch | Automation, caller return, cache/retention, redistribution, rate/retry, revision `LEGAL_GAP` |
| VinaCapital VESAF discovery | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/vesaf/` | Official manager page identifies VESAF as an open-ended equity product | Provider ID, response fields, bounds and totals `NOT_RETAINED` | Static page reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Terms/copyright do not grant automation or redistribution; `LEGAL_GAP` |
| VinaCapital VESAF NAV history | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/vesaf/` | Same exact manager page is the retained history/document unit | Dated reports do not prove a reconciled daily history; requested bounds `NOT_RETAINED` | Static reference; `0/0/0/0`; no document dispatch | Automation, caller return, storage, retention, redistribution and revision `LEGAL_GAP` |
| VinaCapital VDEF discovery | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/vdef/` | Official manager page identifies VDEF as an open-ended equity product | Provider ID, response fields, bounds and totals `NOT_RETAINED` | Static page reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Terms/copyright do not grant automation or redistribution; `LEGAL_GAP` |
| VinaCapital VDEF NAV history | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/vdef/` | Same exact manager page is the retained history/document unit | Dated reports do not prove a reconciled daily history; requested bounds `NOT_RETAINED` | Static reference; `0/0/0/0`; no document dispatch | Automation, caller return, storage, retention, redistribution and revision `LEGAL_GAP` |
| VCBF MGF discovery | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-midcap-growth-fund/` | Official manager page identifies MGF as an equity-fund unit | Provider ID, response fields, bounds and totals `NOT_RETAINED` | Static page reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Copyright/automation/caller-return/redistribution `LEGAL_GAP` |
| VCBF MGF NAV history | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-midcap-growth-fund/` | Same exact manager page/report family; same-owner history crosswalk `NOT_RETAINED` | Report schema, requested bounds, totals, pages, revisions `NOT_RETAINED` | Static reference; `0/0/0/0`; report MIME/bytes/effective route `NOT_RETAINED` | No public API/reuse grant; `SOURCE-GAP` |
| VCBF BCF discovery | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-blue-chip-fund/` | Official manager page identifies BCF as an equity-fund unit | Provider ID, response fields, bounds and totals `NOT_RETAINED` | Static page reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Copyright/automation/caller-return/redistribution `LEGAL_GAP` |
| VCBF BCF NAV history | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-blue-chip-fund/` | Same exact manager page/report family; same-owner history crosswalk `NOT_RETAINED` | Report schema, requested bounds, totals, pages, revisions `NOT_RETAINED` | Static reference; `0/0/0/0`; report MIME/bytes/effective route `NOT_RETAINED` | No public API/reuse grant; `SOURCE-GAP` |
| VCBF AIF discovery | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-active-income-fund/` | Official manager page identifies AIF as an equity-fund unit | Provider ID, response fields, bounds and totals `NOT_RETAINED` | Static page reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Copyright/automation/caller-return/redistribution `LEGAL_GAP` |
| VCBF AIF NAV history | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-active-income-fund/` | Same exact manager page/report family; same-owner history crosswalk `NOT_RETAINED` | Report schema, requested bounds, totals, pages, revisions `NOT_RETAINED` | Static reference; `0/0/0/0`; report MIME/bytes/effective route `NOT_RETAINED` | No public API/reuse grant; `SOURCE-GAP` |
| Eastspring EVESG discovery | Eastspring; `https://www.eastspring.com/vn/en/funds/enf/funddetails/eastspring-investments-vietnam-esg-equity-fund/evesg` | Official page identifies EVESG as an equity fund and report code | Provider ID, response fields and bounds `NOT_RETAINED` | Static page reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Disclaimer/reuse consent gap; `SOURCE-GAP` |
| Eastspring EVESG NAV history | Eastspring; `https://www.eastspring.com/vn/en/funds/archive-documents/investor-relations/evesg` | Official archive identifies dated EVESG reports; source crosswalk `NOT_RETAINED` | Archive dates do not prove machine rows, requested bounds or revision reconciliation | Static archive reference; `0/0/0/0`; document MIME/bytes/effective route `NOT_RETAINED` | Disclaimer requires consent for copying/circulation/distribution; `SOURCE-GAP` |
| Manulife MAFEQI discovery | Manulife; `https://www.manulifeim.com.vn/funds/fund-details.fid-MAFEQI.html` | Official page identifies MAFEQI as an open-ended equity fund | Provider ID, response fields and bounds `NOT_RETAINED` | Static page reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Terms require consent for reuse; `LEGAL_GAP` |
| Manulife MAFEQI NAV history | Manulife; `https://www.manulifeim.com.vn/funds/fund-details.fid-MAFEQI.html` | Same exact fund detail route; history crosswalk and response identity `NOT_RETAINED` | History rows, requested bounds and revision semantics `NOT_RETAINED` | Static reference; `0/0/0/0`; no history dispatch | Terms restrict reuse without consent; `SOURCE-GAP` |
| Dragon Capital DCDS discovery | Dragon Capital; `https://dautu.dragoncapital.com.vn/dcds` | Official page identifies DCDS as an equity product | Provider ID, response fields and bounds `NOT_RETAINED` | Static page reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Independent automation/caller-return/redistribution rights `LEGAL_GAP` |
| Dragon Capital DCDS NAV history | Dragon Capital; `https://dautu.dragoncapital.com.vn/dcds` | Same exact route; public comparison material attributes NAV sourcing externally | No independent manager-owned daily response or reconciled bounds proven | Static reference; `0/0/0/0`; no data dispatch | Independent NAV owner and reuse rights unproven; `SOURCE-GAP / NAV_OWNER_GAP` |
| Dragon Capital DCDE discovery | Dragon Capital; `https://dautu.dragoncapital.com.vn/` | Official catalogue identifies DCDE as an equity product | Provider ID, response fields and bounds `NOT_RETAINED` | Static catalogue reference; `0/0/0/0`; transport fields `NOT_RETAINED` | Independent automation/caller-return/redistribution rights `LEGAL_GAP` |
| Dragon Capital DCDE NAV history | Dragon Capital; `https://dautu.dragoncapital.com.vn/tin-tuc/chuyen-muc/bao-cao-quy` | Official report route is a document unit; same-owner history crosswalk `NOT_RETAINED` | Periodic reports do not prove a daily history or requested-bound reconciliation | Static report reference; `0/0/0/0`; document MIME/bytes/effective route `NOT_RETAINED` | No public API/reuse grant; `SOURCE-GAP` |
| VSDC registry context | VSDC; `https://vsd.vn/en/` | Official registry/service role only; not a NAV response owner | No same-owner NAV route or documented crosswalk retained | Static context reference; `0/0/0/0`; no candidate dispatch | Typed gap `REGISTRY_NOT_NAV_OWNER`; `SOURCE-GAP` |
| SSC disclosure context | SSC; `https://ssc.gov.vn/` | Official regulatory/disclosure context only; not a library NAV response owner | No same-owner NAV route or documented crosswalk retained | Static context reference; `0/0/0/0`; no candidate dispatch | Typed gap `DISCLOSURE_CONTEXT_ONLY`; `SOURCE-GAP` |

No source is promoted because a page number resembles a NAV, because a registry code exists, or
because a document is downloadable. No candidate supplies both a proven discovery ID and a proven
same-owner history ID with lawful caller return in this no-probe round.

## 6. Per-unit transport, identity, and coverage ledgers

### 6.1 Transport and budget ledger

The canonical URLs below contain no query strings. UI selectors, search terms, and document
navigation parameters are not retained as URLs. `STATIC_DOCUMENT_REFERENCE` is deliberately not an
HTTP method claim. The last column counts candidate data/API dispatch only; every row is independently
accounted for.

| Unit | Exact canonical owner/path | Route/version/method | Complete MIME / effective route / redirect | Auth/session/UA/WAF / compressed / decompressed bytes | Candidate logical / physical / pages / retries |
| --- | --- | --- | --- | --- | --- |
| Fmarket listing/discovery | Fincorp; `POST https://api.fmarket.vn/res/products/filter` | `NOT_PROBED`; current source disabled | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| Fmarket NAV history | Fincorp; `POST https://api.fmarket.vn/res/product/get-nav-history` | `NOT_PROBED`; current source disabled | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| SSIAM SSI-SCA discovery | SSIAM; `https://ssiam.com.vn/en/fund-information-ssi-sca` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| SSIAM SSI-SCA NAV history | SSIAM; `https://ssiam.com.vn/en/fund-information-ssi-sca` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| SSIAM VLGF discovery | SSIAM; `https://ssiam.com.vn/en/ssiam/fund-information-vlgf` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| SSIAM VLGF NAV history | SSIAM; `https://ssiam.com.vn/en/ssiam/fund-information-vlgf` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| SSIAM SSIBF discovery control | SSIAM; `https://ssiam.com.vn/en/products` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| SSIAM SSIBF NAV-history control | SSIAM; `https://ssiam.com.vn/en/products` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| SSIAM FUESS product-row discovery control | SSIAM; `https://ssiam.com.vn/en/products` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| SSIAM FUESS product-row NAV-history control | SSIAM; `https://ssiam.com.vn/en/products` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VinaCapital VEOF discovery | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/veof/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VinaCapital VEOF NAV history | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/veof/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VinaCapital VESAF discovery | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/vesaf/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VinaCapital VESAF NAV history | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/vesaf/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VinaCapital VDEF discovery | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/vdef/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VinaCapital VDEF NAV history | VinaCapital; `https://vinacapital.com/investment-solutions/onshore-funds/vdef/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VCBF MGF discovery | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-midcap-growth-fund/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VCBF MGF NAV history | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-midcap-growth-fund/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VCBF BCF discovery | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-blue-chip-fund/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VCBF BCF NAV history | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-blue-chip-fund/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VCBF AIF discovery | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-active-income-fund/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VCBF AIF NAV history | VCBF; `https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-active-income-fund/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| Eastspring EVESG discovery | Eastspring; `https://www.eastspring.com/vn/en/funds/enf/funddetails/eastspring-investments-vietnam-esg-equity-fund/evesg` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| Eastspring EVESG NAV history | Eastspring; `https://www.eastspring.com/vn/en/funds/archive-documents/investor-relations/evesg` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| Manulife MAFEQI discovery | Manulife; `https://www.manulifeim.com.vn/funds/fund-details.fid-MAFEQI.html` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| Manulife MAFEQI NAV history | Manulife; `https://www.manulifeim.com.vn/funds/fund-details.fid-MAFEQI.html` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| Dragon Capital DCDS discovery | Dragon Capital; `https://dautu.dragoncapital.com.vn/dcds` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| Dragon Capital DCDS NAV history | Dragon Capital; `https://dautu.dragoncapital.com.vn/dcds` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| Dragon Capital DCDE discovery | Dragon Capital; `https://dautu.dragoncapital.com.vn/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| Dragon Capital DCDE NAV history | Dragon Capital; `https://dautu.dragoncapital.com.vn/tin-tuc/chuyen-muc/bao-cao-quy` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| VSDC registry context | VSDC; `https://vsd.vn/en/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |
| SSC disclosure context | SSC; `https://ssc.gov.vn/` | `STATIC_DOCUMENT_REFERENCE`; method not retained | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `NOT_RETAINED / NOT_RETAINED / NOT_RETAINED` | `0 / 0 / 0 / 0` |

The zeros count candidate data/API dispatch only. They do not assert a future request allowance.
Static research counters remain `NOT_RETAINED`/`NOT_MEASURED`, never zero.

### 6.2 Identity and coverage ledger

| Unit | Response-backed product identity | NAV/date/unit/publication/revision | Provider bounds/totals/pages/cursors | Actual rows/gaps/duplicates/conflicts | Outcome |
| --- | --- | --- | --- | --- | --- |
| Fmarket listing/discovery | Current parser contract only; no provider response | `NOT_PROBED` | `NOT_PROBED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `DISABLE_PENDING_PERMISSION`; no probe |
| Fmarket NAV history | Synthetic product-ID contract only; no provider response | `NOT_PROBED` | `NOT_PROBED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `DISABLE_PENDING_PERMISSION`; no probe |
| SSIAM SSI-SCA discovery | Official page identifies `SSI-SCA`, manager, code, and `Mutual Equity Fund` | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, served bounds, totals and response identity `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| SSIAM SSI-SCA NAV history | Official page labels NAV/unit and daily NAV-report documents | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Requested `2018-01-01..2026-08-19`, totals, pages, gaps, duplicates, revisions `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| SSIAM VLGF discovery | Official manager page and product/document identity support; response ID `NOT_RETAINED` | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Open-ended equity proof, served bounds and totals `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| SSIAM VLGF NAV history | Same exact manager route is the retained history/document unit; crosswalk `NOT_RETAINED` | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Requested bounds, page reconciliation, daily rows and revision identity `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| SSIAM SSIBF discovery control | Official catalogue identifies SSIBF as a bond product, not requested equity class | `NOT_APPLICABLE` or `NOT_RETAINED` as stated above | No equity-fund history qualification attempted; `NOT_APPLICABLE` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| SSIAM SSIBF NAV-history control | Official catalogue control only; no same-owner equity history unit | `NOT_APPLICABLE` or `NOT_RETAINED` as stated above | NAV history for requested equity class `NOT_APPLICABLE` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| SSIAM FUESS product-row discovery control | Official catalogue separates FUESS ETF rows from open-ended mutual funds | `NOT_APPLICABLE` or `NOT_RETAINED` as stated above | ETF control is not an equity-mutual-fund history boundary | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| SSIAM FUESS product-row NAV-history control | Official catalogue control only; ETF rows are not silently mapped to `STOCK` | `NOT_APPLICABLE` or `NOT_RETAINED` as stated above | NAV history for requested equity-mutual-fund class `NOT_APPLICABLE` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP / PRODUCT_CLASS_MISMATCH` |
| VinaCapital VEOF discovery | Official manager page identifies VEOF as an open-ended equity product | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields, bounds and totals `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VinaCapital VEOF NAV history | Same exact manager page is the retained history/document unit | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Monthly factsheet/report support is not a reconciled daily history; requested bounds `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VinaCapital VESAF discovery | Official manager page identifies VESAF as an open-ended equity product | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields, bounds and totals `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VinaCapital VESAF NAV history | Same exact manager page is the retained history/document unit | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Dated reports do not prove a reconciled daily history; requested bounds `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VinaCapital VDEF discovery | Official manager page identifies VDEF as an open-ended equity product | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields, bounds and totals `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VinaCapital VDEF NAV history | Same exact manager page is the retained history/document unit | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Dated reports do not prove a reconciled daily history; requested bounds `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VCBF MGF discovery | Official manager page identifies MGF as an equity-fund unit | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields, bounds and totals `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VCBF MGF NAV history | Same exact manager page/report family; same-owner history crosswalk `NOT_RETAINED` | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Report schema, requested bounds, totals, pages, revisions `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VCBF BCF discovery | Official manager page identifies BCF as an equity-fund unit | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields, bounds and totals `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VCBF BCF NAV history | Same exact manager page/report family; same-owner history crosswalk `NOT_RETAINED` | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Report schema, requested bounds, totals, pages, revisions `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VCBF AIF discovery | Official manager page identifies AIF as an equity-fund unit | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields, bounds and totals `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VCBF AIF NAV history | Same exact manager page/report family; same-owner history crosswalk `NOT_RETAINED` | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Report schema, requested bounds, totals, pages, revisions `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| Eastspring EVESG discovery | Official page identifies EVESG as an equity fund and report code | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields and bounds `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| Eastspring EVESG NAV history | Official archive identifies dated EVESG reports; source crosswalk `NOT_RETAINED` | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Archive dates do not prove machine rows, requested bounds or revision reconciliation | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| Manulife MAFEQI discovery | Official page identifies MAFEQI as an open-ended equity fund | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields and bounds `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| Manulife MAFEQI NAV history | Same exact fund detail route; history crosswalk and response identity `NOT_RETAINED` | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | History rows, requested bounds and revision semantics `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| Dragon Capital DCDS discovery | Official page identifies DCDS as an equity product | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields and bounds `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| Dragon Capital DCDS NAV history | Same exact route; public comparison material attributes NAV sourcing externally | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | No independent manager-owned daily response or reconciled bounds proven | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| Dragon Capital DCDE discovery | Official catalogue identifies DCDE as an equity product | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Provider ID, response fields and bounds `NOT_RETAINED` | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| Dragon Capital DCDE NAV history | Official report route is a document unit; same-owner history crosswalk `NOT_RETAINED` | Provider NAV/date/unit/publication/revision fields `NOT_RETAINED` | Periodic reports do not prove a daily history or requested-bound reconciliation | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| VSDC registry context | Official registry/service role only; not a NAV response owner | `NOT_APPLICABLE` or `NOT_RETAINED` as stated above | No same-owner NAV route or documented crosswalk retained | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |
| SSC disclosure context | Official regulatory/disclosure context only; not a library NAV response owner | `NOT_APPLICABLE` or `NOT_RETAINED` as stated above | No same-owner NAV route or documented crosswalk retained | No rows retained; duplicates/conflicts `NOT_RETAINED` | `SOURCE-GAP` |

The page evidence can justify a future source-specific re-open investigation only. It cannot claim
`FULL`, `QUALIFIED_PARTIAL`, permission, or a public API. A manager page or document index is not a
reconciled archive.

## 7. Legal and reuse axes

A legal axis is `PROVEN` only when official material expressly covers the exact owner, exact route,
and intended library use. Public reachability, disclosure obligation, robots instructions, or an
investor-facing term is not a grant.

| Unit | Automated access / UA / WAF | Rate / retry / concurrency | Cache / storage / retention / deletion | Caller return / derivative / redistribution / resale | Attribution / commercial | Amendment / revocation / revision | Deterministic disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fmarket listing/discovery | `BLOCKED_PENDING_PERMISSION` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `DISABLE_PENDING_PERMISSION` |
| Fmarket NAV history | `BLOCKED_PENDING_PERMISSION` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `DISABLE_PENDING_PERMISSION` |
| SSIAM SSI-SCA discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| SSIAM SSI-SCA NAV history | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| SSIAM VLGF discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| SSIAM VLGF NAV history | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| SSIAM SSIBF discovery control | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| SSIAM SSIBF NAV-history control | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| SSIAM FUESS product-row discovery control | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| SSIAM FUESS product-row NAV-history control | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VinaCapital VEOF discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VinaCapital VEOF NAV history | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VinaCapital VESAF discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VinaCapital VESAF NAV history | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VinaCapital VDEF discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VinaCapital VDEF NAV history | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VCBF MGF discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VCBF MGF NAV history | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VCBF BCF discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VCBF BCF NAV history | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VCBF AIF discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VCBF AIF NAV history | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| Eastspring EVESG discovery | `LEGAL_GAP` / written-consent restriction | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| Eastspring EVESG NAV history | `LEGAL_GAP` / written-consent restriction | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| Manulife MAFEQI discovery | `LEGAL_GAP` / written-consent restriction | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| Manulife MAFEQI NAV history | `LEGAL_GAP` / written-consent restriction | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| Dragon Capital DCDS discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| Dragon Capital DCDS NAV history | `LEGAL_GAP` / independent owner unproven | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP / NAV_OWNER_GAP` |
| Dragon Capital DCDE discovery | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| Dragon Capital DCDE NAV history | `LEGAL_GAP` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP` |
| VSDC registry context | `TYPED_GAP: REGISTRY_NOT_NAV_OWNER` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP / REGISTRY_NOT_NAV_OWNER` |
| SSC disclosure context | `TYPED_GAP: DISCLOSURE_CONTEXT_ONLY` | `UNKNOWN` | `LEGAL_GAP` | `LEGAL_GAP` | `LEGAL_GAP` | `UNKNOWN` | `SOURCE-GAP / DISCLOSURE_CONTEXT_ONLY` |

The missing legal axes are not silently turned into permission. A future owner response must name
the exact route/version and expressly cover no-login automation, UA/rate/retry/concurrency/WAF,
transient memory/cache, storage/retention/deletion, attribution, commercial use, caller return,
derivative use, redistribution/resale, revision/correction, amendment, and revocation. Fmarket
requires its separate #221 written permission gate for both exact operations.

## 8. No-false-absence and coverage semantics

These are design predicates for a future qualified source, not current public enums or capability
claims:

| Evidence state | Meaning | Allowed result |
| --- | --- | --- |
| No owner route or capability established for the requested operation | Capability is unproven | `SOURCE-GAP` / `UNKNOWN`; no network call |
| Transport, redirect, WAF, timeout, non-authoritative HTML/PDF, MIME, parse, or byte failure | Source state is inconclusive | Typed source error / `UNKNOWN`; never empty or absence |
| Provider response lacks fund class, code, stable ID, or same-source history binding | Identity is unproven | `IDENTITY_GAP`; no fund is silently included |
| Provider declares a supported boundary that excludes part of the request and reconciles it | Qualified narrower history | `PARTIAL`/`QUALIFIED_PARTIAL`; boundary exposed, never `FULL` |
| Provider declares totals/pages/cursors and all expected points reconcile with no unexplained gap | Complete requested source history | `FULL` only if identity, legal, and runtime gates also pass |
| Provider-authoritative, identity-matched, reconciled empty response for a valid supported query | Real empty result | Typed empty only after response identity and empty semantics are proven |
| Unauthoritative, identity-unmatched, unreconciled, or transport-truncated empty response | False-absence risk | Fatal typed source/coverage failure; no rows or empty result |
| Unknown publication calendar, missing page, unreconciled total, or unexplained interior gap | No-false-absence condition | Fatal unknown/coverage error; private partial rows discarded |

An empty result is therefore not unconditionally fatal. Only an unauthoritative,
identity-unmatched, unreconciled, or transport-truncated empty response is fatal. The authoritative
empty and fatal-empty cases are paired future RED fixtures. `COVERAGE_GAP` is reserved for a
qualified provider-declared or response-backed boundary and is not emitted by this no-probe round.
A blank page, broken link, HTML/WAF, or zero-row parser result cannot prove that a fund or history
does not exist.

## 9. Future exact API/transport design (non-authoritative until a source qualifies)

No public API is added here. If a named owner later passes a fresh source/legal review, implementation
must preserve the compatible current shapes and begin with a new exact RED commit. The following is
the reviewed design contract, not an implementation promise.

### 9.1 One-source identity and validation

1. `list_funds(asset_type="STOCK")` may return only a response-backed **open-ended equity** fund
   from the selected owner route. Missing, contradictory, ETF, bond, balanced, money-market,
   pension, closed-end, or unknown class is rejected or excluded with bounded typed diagnostics;
   it is never renamed into `STOCK`.
2. The current compatibility carriers are fixed: `FundList` carries collection `source`,
   `currency`, `fetched_at_utc`, and `warnings`; `Fund` carries no per-fund fetched/warnings
   fields. `NavHistory` carries `product_id`, `code`, `source`, `currency`, `fetched_at_utc`, and
   `warnings`; `NavPoint` carries only `date` and `nav`. Any per-`Fund` additive metadata is
   deferred to a fresh API/model review. `Fund.id: int` is not widened or silently coerced here.
3. `nav_history(product_id, from_date=None, to_date=None)` must use the same owner's documented
   history identifier. A code, ISIN, registry ID, or manager name from another source is not an
   implicit crosswalk. Preserve current inputs exactly: each bound accepts a `datetime.date` or an
   ISO `YYYY-MM-DD` string; bounds are validated before cache/network, inclusive, and reject reversal
   or malformed values. The direct `source(http_get=None, timeout=25.0)`, its `client` alias, and
   `FmarketFundSource` method signatures remain compatible; `list_funds` retains
   `asset_type=None, search="", page_size=100, include_metadata=True`.
4. Every point is provider-published NAV per fund unit with a finite positive non-boolean numeric
   value when required, exact observation/NAV date, exact currency/unit, and source product identity.
   Publication date, revision/correction date, retrieval time, and NAV-as-of date remain separate;
   absent publication time is explicit `NOT_RETAINED`, never fabricated.

### 9.2 Coverage, publication, and atomic failure

- `FULL` requires provider-declared bounds covering both requested endpoints, reconciled totals/pages/
  cursors, all expected provider points, ordered distinct dates, no unexplained interior gaps, and a
  provider-declared cadence/non-publication rule.
- `PARTIAL` requires an owner-declared narrower bound and complete reconciliation inside that bound;
  it exposes the bound and cannot be relabeled as requested full coverage.
- An unauthoritative, identity-unmatched, unreconciled, or transport-truncated empty response is
  fatal. An authoritative, identity-matched, reconciled empty response for a valid supported query
  is a typed empty. Both branches must be paired in future RED fixtures. Duplicate/conflicting date,
  mixed product, wrong unit/currency, malformed total/page/cursor, silent revision drift, or
  transport/MIME/WAF/redirect failure is fatal; private rows are discarded and no false partial is
  returned.
- A provider-published NAV date is not an availability timestamp. The API must not infer a session
  cutoff, UTC publication instant, or same-day knowability from a date-only document.

### 9.3 Bounded scheduler and sanitized diagnostics

The future request uses one finite, sequential, source-approved global ledger for logical targets,
physical calls, pages/cursors, retries, redirects, compressed bytes, decompressed bytes, and any
source-approved pacing. A dispatch atomically reserves all applicable units before transport.
Capability skips consume no dispatch. A reservation failure makes zero network calls. Stream and
decompression byte exhaustion is charged atomically after dispatch and returns no partial result.
Hidden client retries, unbounded redirects, per-date fan-out, concurrency, and cross-source stitching
are forbidden.

For any future JSON route, parse the complete `Content-Type` value after the first colon, trim and
lower-case the media type, and require the exact provider-approved MIME. For a PDF/document route,
the owner must declare that document media type and parser boundary separately; maintenance HTML is
never accepted as a valid fund/NAV response.

Only bounded sanitized real attempts may be retained. Public diagnostics must not contain raw URLs
or queries, bodies, headers, cookies, provider prose, credentials, unbounded fund names/IDs, or
fabricated attempts such as `diagnostics_truncated`. Exact public exception/result carriers remain
deferred until a source-specific API design and RED review; no new public enum or error is added
now. Unknown conditions map to an inconclusive typed failure.

### 9.4 Required future RED/release matrix

A qualified-source handoff must test with committed synthetic fixtures and no live data:

- SSI-SCA-style positive equity identity plus ETF, bond, non-equity, unknown, missing, contradictory,
  mixed-product, and cross-source-ID negatives;
- stable code/product ID, discovery-to-history binding, exact NAV date/unit/currency, publication
  limitation, revision/correction, ordering, duplicate/conflict, bounds, pages/totals/cursors,
  declared partial, authoritative empty, fatal-empty, full, and unknown cases;
- invalid product/date inputs with zero network calls; both `datetime.date` and ISO-string bounds;
  wrong fund/product/date/unit/currency, boolean/non-numeric/non-finite NAV, malformed envelopes,
  redirects, HTML/incorrect MIME, WAF, status, timeout, connection, retry, compressed-byte,
  decompressed-byte, and global-budget failures;
- no-false-absence diagnostics, bounded warning/error text, UTC-aware retrieval metadata,
  compatible `FundList`/`NavHistory` carriers, DataFrame attrs, repr/equality/serialization, and
  atomic no-partial behavior;
- exact owner terms and revocation/permission expiry enforcement, with Fmarket still disabled; and
- current imports, models, factories, aliases, diagnostics, public snapshots, all other domains,
  docs/tutorial/skill/architecture/CHANGELOG/release surfaces, full offline tests, isolated wheel/
  sdist, blacklist/secret/diff/path/object/clean-tree gates on the merged tree.

No future batch, correlation, return, manifest, signal, or VN30F helper is part of this design.

## 10. Conjunctive reopen gate and lifecycle

Reopen from `SOURCE-GAP CLOSURE` only when **one** named owner/route set supplies all of the
following, followed by a fresh exact-SHA design PASS:

1. response-backed open-ended equity identity, stable code/product ID, manager/issuer, NAV/unit,
   exact observation date, and same-source discovery/history binding;
2. exact canonical route/version, method, complete MIME, redirect/effective-route, status, WAF,
   publication/revision behavior, and separate compressed/decompressed byte observations;
3. requested coverage or an owner-declared reconciled partial boundary with no-false-absence rules;
4. finite owner-approved logical/physical/page/retry ceilings, a finite redirect ceiling, and
   separate finite compressed-byte and decompressed-byte ceilings, with atomic pre-dispatch
   reservation and atomic post-dispatch stream/decompression exhaustion; any exhaustion returns no
   false empty or partial result;
5. explicit automation, UA/session, rate/retry/concurrency, cache/storage/retention/deletion,
   attribution, commercial, caller-return, derivative, redistribution/resale, amendment, and
   revocation terms; and
6. a fresh RED/API implementation packet after design PASS. No candidate probe is authorized by
   this source-gap document. Fmarket additionally requires the #221 written permission gate before
   it can be reconsidered.

Current lifecycle is reviewer-owned `DESIGN_REVIEW`, actor `vnfin-oss-reviewer`, next
`RETURN_EXACT_SHA_DESIGN_VERDICT`, packet anchor `7b7fe0b`. The prior BLOCK at exact
`24363bfe887a7f4c9e269fe9ac1034a63f959069` is recorded before this correction with report
`reviews/review-202608240153-issue225-design-source-gate.md` at reviewer `d7118d4`. This clean
correction is rebuilt directly from published base `bdfe06bba330bdf36fec0cf7c18bb79e96e5c28e`;
local activation `ae8087d` is excluded and is not an ancestor. The final backlog-only handoff names
the exact content anchor and preserves the current reviewer-owned phase.

A source-gap design PASS authorizes only merged docs gates, exact-anchor publication, clean
no-capability resolution, and close/re-read. It never authorizes RED, code, source registration,
model/accessor changes, or runtime coverage. A future qualified-source PASS instead transitions to
`RED_FIRST_IMPLEMENTATION_AND_API_REVIEW` and remains open until a separate code review.

## 11. Sources

All URLs are official/primary and query-free. SSC consolidated-law/disclosure documents were
reviewed by official document identity from the [SSC portal](https://ssc.gov.vn/), but their
provider-controlled query-bearing locators are deliberately not retained. No live rows, NAV
values, raw bodies, or query-bearing navigation URLs are retained.

- [SSIAM SSI-SCA fund information](https://ssiam.com.vn/en/fund-information-ssi-sca)
- [SSIAM products and fund-class separation](https://ssiam.com.vn/en/products)
- [SSIAM VLGF fund information](https://ssiam.com.vn/en/ssiam/fund-information-vlgf)
- [SSIAM online-trading terms](https://ssiam.com.vn/en/ssiam/term-condition)
- [SSIAM privacy-terms notice](https://ssiam.com.vn/tin-tuc/cong-bo-thong-tin/thong-bao-ap-dung-dieu-khoan-va-dieu-kien-chung-ve-bao-ve-du-lieu-ca-nhan)
- [VinaCapital information disclosure](https://wm.vinacapital.com/information-disclosure/)
- [VinaCapital VEOF](https://vinacapital.com/investment-solutions/onshore-funds/veof/)
- [VinaCapital VESAF](https://vinacapital.com/investment-solutions/onshore-funds/vesaf/)
- [VinaCapital VDEF](https://vinacapital.com/investment-solutions/onshore-funds/vdef/)
- [VinaCapital terms](https://vinacapital.com/terms-and-conditions/)
- [VinaCapital VEOF official factsheet](https://wm.vinacapital.com/wp-content/uploads/2026/06/20260615-VINACAPITAL-VEOF_Monthly-Factsheet_May-2026-EN.pdf)
- [VinaCapital VN100 ETF page — ETF negative control](https://wm.vinacapital.com/investment-solutions/onshore-funds/vinacapital-vn100-etf/)
- [VCBF MGF](https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-midcap-growth-fund/)
- [VCBF BCF](https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-blue-chip-fund/)
- [VCBF AIF](https://www.vcbf.com/en/open-ended-funds/open-ended-funds-of-vcbf/vcbf-active-income-fund/)
- [VCBF NAV-report index](https://www.vcbf.com/en/investor-relations/fund-reports/net-asset-value-change-report/)
- [Eastspring EVESG](https://www.eastspring.com/vn/en/funds/enf/funddetails/eastspring-investments-vietnam-esg-equity-fund/evesg)
- [Eastspring EVESG archive](https://www.eastspring.com/vn/en/funds/archive-documents/investor-relations/evesg)
- [Eastspring disclaimer](https://www.eastspring.com/vn/en/disclaimer)
- [Manulife MAFEQI](https://www.manulifeim.com.vn/funds/fund-details.fid-MAFEQI.html)
- [Manulife terms](https://www.manulifeim.com.vn/terms-of-use.html)
- [Dragon Capital DCDS](https://dautu.dragoncapital.com.vn/dcds)
- [Dragon Capital catalogue](https://dautu.dragoncapital.com.vn/)
- [VSDC official home/fund services](https://vsd.vn/en/)
- [VSDC fund managers and registration](https://vsd.vn/en/qlq)
- [SSC official portal and legal/disclosure documents](https://ssc.gov.vn/)
- [Fmarket legal page](https://fmarket.vn/legal)
- [Local #221 Fmarket source/legal audit](../2026-08-23-fmarket-current-runtime-terms-audit.md)

## Bottom summary

- Decision: **`SOURCE-GAP CLOSURE`**; no one owner/route qualifies the requested primitive.
- SSIAM SSI-SCA is promising official identity/document evidence, but history reconciliation and all reuse/runtime axes remain unproven.
- VinaCapital, VCBF, Eastspring, Manulife, and Dragon Capital remain independently unqualified; VSDC/SSC provide registry/disclosure context, not a same-owner NAV route.
- Fmarket remains `DISABLE_PENDING_PERMISSION` and was not probed; #218 ETF evidence is not generalized.
- Candidate dispatch is exactly `0 / 0 / 0 / 0`; static research transport is `NOT_RETAINED`/`NOT_MEASURED`.
- No live fund list, NAV value, raw response, API claim, source registration, RED, code, or runtime capability was added.
- Future qualification requires one-source identity/binding, reconciled FULL/PARTIAL coverage, atomic budgets, and explicit legal rights.
