# VN30F daily contract-history source vetting — #226

**Date:** 2026-08-24 (UTC+7)
**Packet:** `tasks/226-vn30f-daily-contract-history-spec.md` at reviewer anchor
`31d75d5687b18f64659a933d9ff3c829646d6abe`
**Published base:** `origin/master` `001cfd1cafc0d0554640c5b9672dc09029b388b2`
**Phase:** source/design gate only
**Disposition:** **`SOURCE-GAP CLOSURE`**
**Runtime chain:** empty; no provider is registered or callable
**Requested scope:** one provider-owned, per-contract VN30F daily history unit; the caller may
request `2018-01-01..date.today()` or a narrower interval after a future qualification.

## Decision

No reviewed unit proves the complete conjunction of VN30F identity, contract and expiry identity,
Vietnam trading-session date, OHLC, volume, open interest, settlement, requested historical bounds,
revision behavior, bounded transport, and lawful automation/storage/caller-return/redistribution.
HNX public surfaces establish useful product and current-table controls, while VSDC surfaces establish
contract and settlement metadata. Neither surface is a single qualified D1 history owner, and their
metadata cannot be joined to another owner's bars under this packet.

The honest result is `SOURCE-GAP CLOSURE`: publish only this research/design/backlog range after
reviewer approval, retain an empty new source chain, and reopen only on the source-only conjunctive
evidence in §9. This is not a claim that no data exists. It is a claim that no source unit in this bounded
clean-room review is qualified for a public capability.

The issue is separate from closed #202. #202 concerns matched trades, sub-minute data, and
order-flow/tape semantics; #226 concerns one row per VN30F contract and Vietnam trading session.
No tape, continuous/front/roll series, calendar spread, basket, signal, backtest, or trading helper is
included here.

## 1. Clean-room and repository boundary

Before research, `docs/vnstock-blacklist.md` was read. The exact exclusion applied to every web
search was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result or derivative material was opened, cited, compared, installed, or used. Only
official HNX/VSDC pages and official HNX documents are retained below. No unofficial endpoint map,
copied dataset, notebook, wrapper, paid/login feed, private endpoint, broker credential, proxy
workaround, reporter archive, raw body, raw header, cookie, token, response digest, query-bearing
URL, live price, or live contract row is committed.

The dereferenced `v0.2.0` tag is
[`2fe50df4f27064140ff9f7a680227a2b337ec74a`](https://github.com/hungson175/vnfin/commit/2fe50df4f27064140ff9f7a680227a2b337ec74a),
and the published master at the packet base is
`001cfd1cafc0d0554640c5b9672dc09029b388b2`. Neither tree has a `vnfin.derivatives` domain,
contract-history model, source registration, or public facade. Existing equity/index OHLC models
therefore do not prove futures expiry, settlement, open-interest, session, quote-unit, or coverage
semantics merely because names such as `open` or `close` overlap.

## 2. Evidence accounting and method

This was bounded static research of official pages/documents. It was not a candidate data/API probe.
A page visible without a login in a browser is not evidence of an automated endpoint, a quota, a
license, or permission to store and return the content.

| Evidence channel | Logical | Physical | Pages/cursors | Retries | Redirects | Bytes | Meaning |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Official static pages and documents | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | Research evidence only; no runtime ledger |
| Candidate discovery/history dispatches | `0` | `0` | `0` | `0` | `0` | `0` | No HNX, VSDC, broker, or private data route was called |
| Future request-scoped history operation | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | No source is qualified and no numeric runtime budget is frozen |

`0` in the candidate row means zero dispatches were made. It does not mean zero rows, zero
contracts, source absence, or permission. Static transport fields such as method, status, complete
MIME, effective route, UA/session/WAF behavior, and byte totals are `NOT_RETAINED`, not invented.
No `SourceAttempt` or `diagnostics_truncated` marker is fabricated for an unmade request.

## 3. Official source units

Every row below is a separate owner + canonical route + operation unit. A navigation page is not
silently promoted to a history API, and a product list is not joined to another owner's bars.
`NOT_PROBED` means no dispatch was made; `COVERAGE_GAP`, `FIELD_GAP`, `LEGAL_GAP`, and
`RATE_POLICY_GAP` describe the missing qualification axes rather than a negative claim about the
provider's private or commercial services.

| Owner / exact route | Operation and retained evidence | Missing axes | Disposition |
| --- | --- | --- | --- |
| HNX — [`/vi-vn/phai-sinh/san-pham.html`](https://www.hnx.vn/vi-vn/phai-sinh/san-pham.html) | Official derivatives product/navigation control; it identifies the stock-index futures product family and links model-contract/trading-calendar material. It is not a returned per-contract D1 history. | `contract_code`, response-backed expiry rows, OHLC/volume/OI/settlement history, bounds, pages/revisions, runtime and reuse rights are not established in retained evidence | `FIELD_GAP` |
| HNX — [`/vi-vn/phai-sinh/ket-qua-giao-dich.html`](https://www.hnx.vn/vi-vn/phai-sinh/ket-qua-giao-dich.html) | Official date-filtered current-result table route. Its published table headings expose product, identity-related columns, expiry month, high/low/open/close, market-volume subcolumns, OI and settlement concepts. This is a selected-day surface; no live row is retained. | Bulk historical cursor/retention, provider-declared 2018-to-current bounds, revision/duplicate contract, response MIME/status contract, and automation/storage/caller-return/redistribution grant are not established in retained evidence | `COVERAGE_GAP` |
| HNX — [`/vi-vn/phai-sinh.html`](https://hnx.vn/vi-vn/phai-sinh.html) | Official derivatives landing/navigation surface with product and market-data links. | Exact history operation, field envelope, bounds, page totals, and reuse terms are not established in retained evidence | `NOT_PROBED` |
| HNX — [`portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html`](https://portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html) | Official derivatives announcements/publication index. It is a document/disclosure control, not a reconciled all-contract D1 history source. | A single history operation, row schema, complete contract/session totals, revision policy, and library-use grant are not established in retained evidence | `COVERAGE_GAP` |
| HNX — [`/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html`](https://hnx.vn/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html) | Official derivatives information-service catalogue. It exposes separate end-of-day, statistics, publication and historical-data package categories; reviewed package evidence names per-contract EOD concepts and an Excel/InfoFile delivery route. | Historical tab contents, retention/backfill, exact VN30F universe, revisions, technical schema, rate, automation and reuse rights are not established in retained evidence | `COVERAGE_GAP` |
| HNX — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html) | Official information-service/technical-guide lead for market-data messaging, including derivatives. It establishes a service family but does not by itself establish a free no-login OSS route. | Exact public route/version, registration/contract terms for this use, historical response schema, bounds, rate, caller return and redistribution are not established in retained evidence | `LEGAL_GAP` |
| HNX — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html) | Official registration flow says a customer requests information, receives fees and a contract template, and proceeds after agreement/signing. | Public OSS entitlement, historical span, field specification, rate, retention and caller-return/redistribution right are not established in retained evidence | `LEGAL_GAP` |
| HNX — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html) | Official service overview says derivatives data is supplied as an information service and fees are package-based. | Contract-specific delivery, historical retention, automation, storage and redistribution are not established in retained evidence | `LEGAL_GAP` |
| HNX — [2026 data-package and service-price document](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf) | Official package/pricing document describes derivatives market-data package concepts, including contract code, prices, settlement, OI and volume/value fields. It is commercial/service evidence; retained text does not establish a granted public API. | Package entitlement, automation, storage, caller return, redistribution, commercial and rate rights for this library are not established in retained material; full historical bounds/revisions are not established | `LEGAL_GAP` |
| HNX — [`banggia.hnx.vn`](https://banggia.hnx.vn/) | Official current market-board control with derivatives identity/price concepts. Current board output is not a historical per-contract D1 operation. | Historical coverage, session totals, OI/settlement revision, bounded pagination, and OSS reuse rights are not established in retained evidence | `COVERAGE_GAP` |
| VSDC — [`/en/thong-tin-san-pham`](https://www.vsd.vn/en/thong-tin-san-pham) | Official product information identifies VN30 Index Futures, HNX ticker allocation, multiplier/contract size, listing/trading/delivery facts, tick size, last trading date, cash settlement, and DSP/FSP concepts. It does not publish the requested all-contract OHLC/volume/OI D1 history in the retained material. | History route, per-session OHLC/volume/OI rows, provider-declared bounds/revisions, pagination, automation, caller-return, storage and redistribution are not established in retained evidence | `FIELD_GAP` |
| VSDC — [historical contract-list notice](https://vsd.vn/en/ad/141951) | Official notice table binds a VN30 futures product to securities code/ISIN and first/last/final payment dates for a dated contract-list publication. No exact live row is retained. | It is metadata/list publication, not a per-session D1 bar/volume/OI/settlement history; route-wide coverage, revision, runtime and OSS reuse grant are not established in retained evidence | `FIELD_GAP` |
| VSDC — [`/gia-thanh-toan/search`](https://www.vsd.vn/gia-thanh-toan/search) | Undocumented UI action route associated with the official DSP/FSP table; its visible table uses a product identifier and a payment-date filter. It is retained only as an uncalled route lead, not as an API contract. | Documented history API, identity join to derivatives code/ISIN, proof that payment date is trading session, OHLC/volume/OI, bounds, rate and reuse rights are not established in retained evidence | `TRANSPORT_INCONCLUSIVE` |
| VSDC — [`/lich-dao-han-thanh-toan/changepage`](https://www.vsd.vn/lich-dao-han-thanh-toan/changepage) | Undocumented UI action route for paginated maturity/final-payment metadata. | Metadata schedule is not per-session D1 history; page contract, field identity, coverage, transport and reuse are not established in retained evidence | `FIELD_GAP` |

### 3.1 What the official evidence does and does not prove

- HNX's date-filtered current-result surface is the strongest same-owner public lead because its official table labels
  the product/expiry, OHLC, market-volume, OI, and settlement concepts. A current table is not a
  history endpoint. It cannot prove retention from `2018-01-01`, a complete session/contract
  universe, page reconciliation, or revisions.
- HNX's catalogue, service guides, registration flow and 2026 package document show that richer
  derivatives data is a fee/package/contract-controlled information service. The package evidence
  is the strongest field match (`PS.EOD01`-style per-contract EOD concepts delivered through the
  service), but the retained evidence does not establish a free automated route, storage right,
  caller-return right, redistribution right, or rate policy for this OSS library. Written
  confirmation is still needed for the exact delivery channel and historical retention.
- VSDC's product page proves VN30 futures contract semantics, including a 2017 product start and
  response/document concepts for DSP/FSP. It does not prove that VSDC owns or exposes HNX's complete
  per-session OHLC, volume, OI, and settlement history for this use. Its DSP/FSP table's visible
  payment-date label is not proven to be a trading-session date, and its product identifier is not
  documented as the HNX derivatives-code/ISIN key. A VSDC contract list cannot be used to infer
  expiry from a code or to repair a missing HNX history row.
- No other provider route was admitted as a qualification unit: an exact owner, canonical route,
  operation, and rights-clear no-login contract would have to be named before it could be researched.
  Paid, login, private, copied, proxy, and reporter routes remain excluded and are not fallbacks.
- Official static visibility and HTTP reachability, if later observed, are separate from legal
  automation and downstream-use permission. No rights are inferred from a public page; the absence
  of retained permission text is not a claim that no separate permission exists.

### 3.2 Per-unit sanitized evidence ledger

The matrix above is also the exact retained-unit inventory. This ledger makes the packet's
per-unit evidence axes explicit instead of relying on one global `NOT_RETAINED` row. `NR` means
`NOT_RETAINED`; `NP` means `NOT_PROBED`. Static page/document facts are retained only in the
`identity/field/coverage` cell. No unretained transport, access, rate, or rights axis is used as a
positive qualification claim. `route_version` is the first candidate route/transport slot and is
`NOT_RETAINED` for every unit.

The research channel did not dispatch any candidate data/history operation. Therefore every unit
has the same candidate-dispatch ledger
`logical/physical/pages/retries/redirects/compressed_bytes/decompressed_bytes = 0/0/0/0/0/0/0`.
The zero is a count of unmade candidate dispatches, not a claim of zero source rows or zero traffic
on the official website used for static reading.

| Unit ID; owner; exact route/operation | Candidate route/transport: route_version/method/status/complete MIME/effective route/redirect | Candidate ledger: L/P/pages/retries/redirects/cbytes/dbytes | Access: auth/session/UA/WAF/rate | Response-backed static identity/fields/coverage facts | Observed non-permission owner facts | Rights axes: automation/caller-return/storage/retention/attribution/commercial/derivative/redistribution/amendment/revocation | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `HNX-PRODUCT-HTML`; HNX; `https://www.hnx.vn/vi-vn/phai-sinh/san-pham.html` / product navigation | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static product/navigation facts retained; no D1 rows, contract/session totals, or history bounds | NR | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `FIELD_GAP` |
| `HNX-RESULT-HTML`; HNX; `https://www.hnx.vn/vi-vn/phai-sinh/ket-qua-giao-dich.html` / date-filtered result table | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static table headings retain product/expiry/OHLC/volume/OI/settlement concepts; selected-day surface, no bulk bounds/revision contract | NR | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `COVERAGE_GAP` |
| `HNX-LANDING-HTML`; HNX; `https://hnx.vn/vi-vn/phai-sinh.html` / derivatives navigation | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static navigation only; no exact history operation or response schema | NR | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `NOT_PROBED` |
| `HNX-PUBLICATION-HTML`; HNX; `https://portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html` / publication index | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static disclosure/document navigation; no reconciled D1 row operation | NR | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `COVERAGE_GAP` |
| `HNX-CATALOGUE-DER-HTML`; HNX; `https://hnx.vn/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html` / derivatives service catalogue | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static catalogue/package categories retained; historical retention/backfill and exact VN30F universe not bound | NR | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `COVERAGE_GAP` |
| `HNX-TECH-YCKT-HTML`; HNX; `https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html` / technical guide | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static service-family/InfoGate/InfoFile lead retained; no route schema or history response | NR | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `LEGAL_GAP` |
| `HNX-REG-SHDK-HTML`; HNX; `https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html` / registration flow | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static request/fee/contract-signing flow retained; no entitlement for this library | Observed fee/contract flow; not permission | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `LEGAL_GAP` |
| `HNX-OVERVIEW-SGTC-HTML`; HNX; `https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html` / service overview | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static fee/package service posture retained; no exact history route or retention | Observed fee/package service posture; not permission | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `LEGAL_GAP` |
| `HNX-PACKAGE-2026-PDF`; HNX; `https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf` / derivatives EOD package description | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static package field concepts retained; historical span, revisions and exact entitlement unretained | Observed commercial package/field pricing; not permission | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `LEGAL_GAP` |
| `HNX-BOARD-HTML`; HNX; `https://banggia.hnx.vn/` / current market board | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static current-board identity/price control; no historical D1 bounds/revisions | NR | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `COVERAGE_GAP` |
| `VSD-PRODUCT-HTML`; VSDC; `https://www.vsd.vn/en/thong-tin-san-pham` / product and DSP/FSP page | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static VN30 futures contract/maturity/settlement concepts retained; no OHLC/volume/OI history | Observed copyright notice; not permission | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `FIELD_GAP` |
| `VSD-CONTRACT-LIST`; VSDC; `https://vsd.vn/en/ad/141951` / historical contract-list notice | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static product/code/ISIN/first-last-final-payment column concepts retained; metadata only | Observed copyright notice; not permission | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `FIELD_GAP` |
| `VSD-DSP-FSP-UI`; VSDC; `https://www.vsd.vn/gia-thanh-toan/search` / undocumented UI action | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static UI route lead only; payment-date/product identifier do not prove trading-session/code join | Observed copyright notice; not permission | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `TRANSPORT_INCONCLUSIVE` |
| `VSD-MATURITY-UI`; VSDC; `https://www.vsd.vn/lich-dao-han-thanh-toan/changepage` / maturity schedule UI action | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | `NR/NR/NR/NR/NR` | Static UI route lead only; maturity/payment metadata, not per-session D1 | Observed copyright notice; not permission | `NR/NR/NR/NR/NR/NR/NR/NR/NR/NR` | `FIELD_GAP` |

The observed non-permission facts column is not one of the rights axes. A fee, package/pricing
description, or copyright notice is evidence to resolve with the owner; it is neither a
permission grant nor a prohibition. Every rights axis remains `NR` in this source-gap packet.

The per-unit ledger intentionally does not claim that the static page read was an authorized data
dispatch. No `SourceAttempt`, page, retry, redirect, byte total, MIME, effective-route, or rate
value is fabricated for a route that was not called. The positive static facts above are product,
navigation, package, or document facts only; they cannot satisfy the missing history, transport, or
rights axes.

## 4. Identity, row, and field acceptance contract

The table below is a research acceptance predicate, not a frozen public model or export. A future
qualified source must prove every row in one response-backed unit; a missing axis closes the source
gap rather than degrading the row.

| Concept | Required response-backed meaning and validation | Current evidence |
| --- | --- | --- |
| `session` | Provider's Vietnam trading-session `date`; not request order, retrieval date, publication date, or a date inferred from UTC timestamp. Calendar/holiday and timezone semantics must be documented or response-backed. | HNX current page shows a date-filtered result surface, but no retained history contract or session calendar/revision proof. `FIELD_GAP`. |
| `contract_code` | Non-empty provider-issued identity for the exact VN30F contract/session row. It must be present in the response or same-owner documented schema; never parse an undocumented code convention or list position. | VSDC contract-list documents establish that codes exist; they do not supply all daily rows. `FIELD_GAP`. |
| `product` | Response-backed product identity exactly matching VN30 Index Futures/VN30F; wrong/mixed VN100, bond futures, cash index, continuous or rolled products fail. | HNX/VSDC product metadata is positive control only; no same-owner D1 history unit. `IDENTITY_GAP`. |
| `expiry` | Response-backed expiry month/date or official same-owner field. A code suffix, current/next-month rule, list position, or caller label alone is insufficient. | VSDC publishes contract-list maturity/payment metadata; no joined bar source is approved. `IDENTITY_GAP`. |
| `open`, `high`, `low`, `close` | Finite, non-boolean numeric contract prices in a proven quote unit and scale. Require `low <= open <= high`, `low <= close <= high`, and `low <= high`; reject non-finite, bool, unit-mismatched, or contradictory values. | HNX current headings advertise these concepts; no response schema/units/revision history is qualified. `FIELD_GAP`. |
| `volume` | Non-negative integer number of contracts in a provider-documented unit; no float coercion, turnover substitution, market-wide aggregate substitution, or missing-to-zero fill. | HNX current/package material advertises volume/value concepts but no qualified history envelope/unit/reuse contract. `FIELD_GAP`. |
| `open_interest` | Non-negative integer number of open contracts in a provider-documented unit; no market-total or change-OI substitution. | HNX current/package material advertises OI concepts; complete per-contract D1 history and units are unproved. `FIELD_GAP`. |
| `settlement` | Finite, non-boolean price with a proven unit/scale; same-day DSP versus final settlement must be response-backed and distinct where applicable. | VSDC documents DSP/FSP concepts and HNX current surface labels settlement; no single history unit proves row semantics/revisions. `FIELD_GAP`. |
| `source` | Canonical producer/route identity from the accepted unit, not a caller label, URL token, or another provider's name. | No unit qualifies. `IDENTITY_GAP`. |
| `fetched_at_utc` | Retrieval instant for the accepted response, timezone-aware UTC; never the session/publication date. | No data dispatch was made. `NOT_APPLICABLE`. |
| warnings/attempts | Bounded, sanitized diagnostics. Attempts, if later needed, must be real dispatches only; no raw URL query, body, header, cookie, provider prose, secret, or synthetic attempt. | No dispatch was made. `NOT_APPLICABLE`. |

The later API gate must treat `(session, contract_code)` as the unique composite row identity. After
identity validation, output ordering is deterministic `session ASC, contract_code ASC` using the
provider's exact canonical contract-code string; no code parsing or case-folding changes the key.
Repeated keys are rejected atomically. Identical duplicates and conflicting duplicates are both
terminal duplicate/conflict failures, not deduplicated or last-write-wins rows.

Every qualification unit must structurally serve all required research fields: `session`,
`contract_code`, `product`, `expiry`, all four OHLC values, `volume`, `open_interest`, and
`settlement`. A response/schema that omits a required field for the operation is `FIELD_GAP` even if
the owner could describe that field as not applicable elsewhere. A null is permitted only for an
individual row when the owner documents a finite nonpublication/not-applicable state for that exact
field; it cannot stand in for a structurally absent field, parser loss, unknown identity, truncated
transport, or budget exhaustion.

Nullable required fields are permitted only when the owner explicitly defines a finite
nonpublication/not-applicable state for that exact field. Parser loss, unknown identity, transport
truncation, budget exhaustion, malformed envelope, or missing unit is fatal and never nullable.

## 5. Coverage and no-false-absence contract

A future result may use the following states only after a separate API review. These are source
qualification rules, not current public tokens.

| State | Conjunctive evidence | Safe interpretation |
| --- | --- | --- |
| `FULL` | One provider-owned unit declares bounds covering the caller interval; every declared contract/session is reconciled; pages/cursors/totals match; no unexplained gaps/conflicts; expiry retention, current-date lag, nonpublication and revision rules are known | Requested coverage only |
| `QUALIFIED_PARTIAL` | The same unit declares a narrower supported start/end or contract boundary and reconciles every declared row/page inside it | Expose the exact provider boundary; never relabel the request as full |
| authoritative empty | Product/contract identity, valid interval, provider totals/calendar and nonpublication semantics all reconcile to zero rows | Typed empty may be returned after API review |
| unknown/inconclusive empty | WAF/challenge/HTML, timeout, status/MIME mismatch, malformed envelope, missing identity, missing totals/calendar, truncation, conflict, or budget exhaustion | No history and no absence claim |
| `COVERAGE_GAP` | Provider declaration or qualified response proves a boundary excludes the requested interval | Explicit gap; not zero and not a fallback |

The source must not infer a missing session, expired contract, settlement, OI, or row from list
position, code spelling, current product roster, a blank document, a failed request, or a neighboring
provider. Every private accumulator is discarded if any required row/page or identity check fails.

## 6. Transport, legal, and diagnostic axes

A future exact unit must retain sanitized, bounded evidence for each of these independent axes:

1. **Owner and route:** canonical host/path/version, operation, method, status class, complete
   `Content-Type` after the first header colon and outer-whitespace normalization, normalized MIME,
   effective route, redirect count, and expected response-shape keys. Query values, raw headers and
   bodies are never retained.
2. **Access:** whether the exact route is public without credentials; login, API key, cookie,
   session, browser-UA, WAF/challenge, consent and registration behavior. A browser-visible page is
   not automation permission.
3. **Data identity:** response-backed product, code, expiry, session, fields, units, scale,
   precision, nullable/nonpublication meaning, revision/correction behavior, and cross-page totals.
4. **Coverage:** provider-declared start/end, contract/session totals, page/cursor semantics,
   duplicate/conflict handling, interior gaps, expired-contract retention and current-date lag.
5. **Rights:** automation, rate/retry/concurrency, transient/cache/storage/retention/deletion,
   attribution, commercial use, derivative use, caller-facing return, redistribution/resale,
   amendment and revocation for the exact route and fields. The HNX package document and VSDC page
   contain observed owner facts to review with the owner; their retained text does not establish a
   free reuse grant.
6. **Diagnostics:** finite status/MIME/redirect/byte/identity/coverage/legal tokens with sanitized
   bounded counts. Unexpected HTML, WAF, timeout, or connection failure is transport inconclusive,
   never a false absence.

## 7. Future request budget and atomic scheduler

No runtime scheduler is added by this packet, but any later qualified implementation must satisfy
this deterministic contract before RED approval:

- One request owns one ledger with counters for `logical_units`, `physical_dispatches`,
  `discovery_pages`, `history_pages`, `retries`, `redirects`, `compressed_bytes`, and
  `decompressed_bytes`. The counters are distinct; a logical route operation is not silently equal
  to a page, a retry, or a byte stream.
- `max_concurrency = 1`: the scheduler is sequential and single-flight. A logical unit is one exact
  owner/route/version/operation reservation. A logical page/cursor is reserved before its request is
  sent. Every network dispatch, including a followed redirect or retry, reserves a physical dispatch
  before sending. A page/cursor reservation, its physical dispatch, the applicable retry/redirect
  counters, and any applicable logical-unit reservation are checked and committed atomically.
- After dispatch, the returned page/cursor identity must match the reservation before any row is
  accepted. A malformed envelope, unexpected page/cursor, identity mismatch, or failed validation
  still consumes the attempted page reservation and physical dispatch; it yields no accepted rows.
  A retry reserves a retry and a new physical dispatch; a redirect follow-up reserves a redirect
  and a new physical dispatch.
- The reservation is atomic: under one request lock, check every applicable finite ceiling and apply
  the complete reservation or none. A failed reservation dispatches nothing. No counter may be
  incremented by a later cleanup path after a failed reservation.
- Only streamed bytes charge after dispatch: compressed bytes are charged as received before
  decompression, and decompressed bytes are charged after decoding. Each stream has a hard finite
  cap; crossing either cap aborts the request, discards private rows, and cannot yield a partial
  public result. No `Content-Length` is trusted as the only byte guard.
- The source-specific design PASS must pin finite numeric ceilings for all applicable counters and
  show their relation to the provider's rate/terms. This source-gap packet deliberately does not
  freeze numbers or promise a `250ms/25s` retry policy for an unqualified route.
- Exhaustion returns a typed internal/publicly reviewed failure only after a fresh API decision;
  this packet freezes no exception name or public error carrier. It preserves only real, bounded,
  sanitized attempts. It never fabricates an attempt to represent truncation and never labels an
  exhausted request as an authoritative empty response.
- A one-source operation is atomic: no cross-source failover or source-by-contract/date stitching.
  If a future qualified chain is authorized, source qualification and one-source-wins semantics
  must be reviewed separately; this packet does not authorize a chain.

## 8. Negative boundaries

The following are explicit non-qualifiers and cannot be fallbacks:

- HNX current-only result/quote/board pages without historical bounds and page reconciliation;
- VSDC contract-list/DSP/FSP metadata without the same-owner OHLC/volume/OI D1 rows;
- cash VN30 index, VN100, government-bond futures, spot data, continuous/rolled/front-month
  reconstructions, expiry/calendar-spread/basket calculations, or tape/intraday rows;
- a code/list-position expiry guess, request echo, inferred session, missing-to-zero volume/OI, or
  provider metadata joined across owners without a reviewed stable crosswalk;
- login, paid, registered, credentialed, private, WAF/session-dependent, unbounded, copied,
  unofficial, proxy, or reporter routes;
- a successful status with wrong/full MIME, maintenance HTML, malformed/truncated body, unknown
  totals, or a blank result that lacks authoritative identity/nonpublication semantics; and
- any route whose automation, storage, caller return, redistribution, commercial, rate, amendment,
  or revocation posture is not established in retained evidence for this library.

## 9. Conjunctive reopen evidence

Reopen the source gap only when one named owner + exact route/version + operation supplies all of the
following in one reviewable evidence packet:

1. response-backed `VN30F` product identity, contract code, official expiry, session date/calendar,
   OHLC, contract volume, OI, settlement, units, scale, precision, nullability and revision rules;
2. provider-declared full bounds covering the caller interval, or an explicit narrower declared
   boundary that supports `QUALIFIED_PARTIAL`, with reconciled contract/session totals, pages/cursors,
   duplicate/conflict and interior-gap behavior;
3. exact transport contract: no-login/credential posture, status, complete MIME, redirects,
   effective route, UA/WAF/session behavior, finite compressed/decompressed byte limits, and a
   bounded route-specific request budget;
4. explicit owner permission for automation, rate/retry/concurrency, transient/cache/storage/
   retention/deletion, attribution, commercial use, derivative use, caller return,
   redistribution/resale, amendment and revocation; and
5. a source-only sanitized evidence packet: provider response/schema evidence for every required
   field, declared bounds/totals/cursors, revision/nonpublication semantics, exact route/MIME/status/
   redirect/byte observations, finite route budget and rate terms, and the owner's rights text or
   written confirmation. No RED test, public model, API snapshot, or release artifact is a source
   reopen prerequisite.

All five groups are conjunctive. A VSDC metadata success cannot repair an HNX row failure; a current
HNX table cannot repair missing history; and a legal or budget gap keeps the runtime chain empty.
Source qualification does not freeze a public API/model contract or authorize tests/code. A separate
API/model decision freezes only that public contract—row/result carriers, signatures, coverage and
diagnostics, units, and docs—and does not authorize tests or code. A separate RED-first approval
authorizes tests only; implementation/code remains gated on green results and code review. The full
future API/RED/release matrix is §10; it is not an evidence prerequisite and is not authorized by
this packet.

## 10. Future API/RED/release matrix (not authorized)

This matrix is preserved from the packet as a later gate. It is intentionally documentation-only in
this correction: no RED test, fixture, parser, mapping, model, source registration, or runtime
capability is created now.

| Future gate | Required synthetic/offline cases after source qualification and a separate API decision |
| --- | --- |
| All-contract and exact-contract success | All-contract history and exact `contract` filter success; inclusive date bounds; caller-malformed bounds/product/contract/date inputs fail before cache lookup and network, with the later RED asserting an untouched cache; malformed provider responses are evaluated only after dispatch and fail before cache insertion or public return; exact `VN30F` product validation and no caller-label identity. |
| Identity and field semantics | Response-backed product, contract code, expiry, Vietnam session/calendar, source, quote unit/scale/precision, OHLC finite/non-bool invariants, non-negative integral contract volume and OI, settlement/DSP/FSP meaning, ordering, `(session, contract_code)` uniqueness, identical/conflicting duplicates, structural required-field absence, per-row finite nullability, and revision/correction cases. |
| Coverage and no-false-absence | Requested `FULL`, provider-declared `QUALIFIED_PARTIAL`, expired-contract retention, current-date lag, nonpublication, authoritative empty, unknown/inconclusive empty, provider totals/pages/cursors, page identity mismatch, gaps, duplicate/conflict, date boundaries, and revision behavior. |
| Wrong and malformed inputs | Wrong/mixed product or contract, cash index, continuous/rolled/front-month, tape/intraday, inferred expiry/session, malformed envelope/MIME/status/redirect/WAF, missing identity, invalid date/expiry, bool/non-finite/broken OHLC, negative/non-integral counts, unit mismatch, structurally absent required field, invalid per-row null, and provider/schema mismatch. |
| Atomic runtime and diagnostics | Sequential `max_concurrency=1`; logical/physical/page/retry/redirect reservation and charge; compressed/decompressed byte caps; global-budget exhaustion; malformed/mismatched page consumption; atomic no-partial behavior; one-source-win/no-stitch; bounded sanitized attempts/warnings; retrieval timestamp; no raw URL/query/body/header/cookie/provider prose/secret; composite-key ordering and duplicate rejection. |
| API/units/docs gate | Later public signatures and API snapshots; exact session/date-input semantics; price/volume/OI/settlement units, scales, precision, and nullability; source/provenance and sanitized error/warning carriers; explicit `docs/api.md` and `docs/units.md` contracts plus examples/tutorial/architecture/skill/CHANGELOG consistency; no undocumented public token. |
| Model/API/release compatibility | Later immutable row/result and coverage decision; DataFrame attrs and provenance; serialization/repr/equality; public model/export/error snapshots; existing-domain compatibility; release artifacts; focused/full offline tests; import/version; isolated wheel/sdist; blacklist/secret/diff/path/object/clean-tree and exact remote-anchor/ancestry/scope gates. |

The source-only reopen in §9 does not require this matrix to pass. Once one source qualifies, a
fresh API/model decision must select and freeze the public carriers and their units/docs contract;
that decision is separate from RED authorization. Only a later RED-first approval may authorize the
executable tests; implementation/code still requires green results and code review. No public API
name, model, warning, exception, export, or release claim is frozen by this matrix.

## 11. Future API boundary

The packet's illustrative spelling is not a public API commitment:

```python
vnfin.derivatives.contract_history(
    product="VN30F",
    start=date(2018, 1, 1),
    end=date.today(),
    contract=None,
)
```

No `vnfin.derivatives` package, model, enum, exception, export, source registration, DataFrame
schema, warning token, cache, live route, RED test, coverage claim, or runtime capability is added.
A later qualified design must decide immutable row/result types, inclusive date semantics, optional
contract validation, coverage bounds, provenance, DataFrame attrs, serialization/repr/equality,
public snapshots, sanitized errors, exact units/scales/precision, and the API/docs contract before
any implementation. Caller-malformed product/contract/date/bounds calls must fail before cache lookup
and network. A malformed provider response can only fail after a real dispatch and must fail before
cache insertion or public return. Both are later API/RED gates, not capabilities added here.

## 12. Lifecycle and publication gate

The intake lifecycle was recorded in local commit `7b70a5c79cc6d730e86c518d304df24f67ecfcc5` from
published base `001cfd1`. The prior design BLOCK was recorded first in backlog commit `09f7aea`,
for reviewed merged HEAD `eb1c8cefe42556220507a242d0aa6de58c98e385`, report
`reviews/review-202608241126-issue226-design-source-gate.md`, reviewer `c57fc9d`, and delivery
`#5112ed77`. This correction must return one exact merged SHA whose lifecycle binds that prior
HEAD, clean base `001cfd1`, and the exact base-to-correction range. `#227` remains queued.

The disposition remains `SOURCE-GAP CLOSURE`: #202 is separate, the new chain stays empty, and no
probe, RED test, production code, push, or issue close is authorized before exact-SHA design
approval. The two artifact files in this handoff are the only source/design files for #226.

## Sources

Only official/primary sources are listed. These links are canonical host/path references without
query parameters; current rows and response bodies are not retained.

- [HNX derivatives landing](https://hnx.vn/vi-vn/phai-sinh.html)
- [HNX derivatives products](https://www.hnx.vn/vi-vn/phai-sinh/san-pham.html)
- [HNX current derivatives result](https://www.hnx.vn/vi-vn/phai-sinh/ket-qua-giao-dich.html)
- [HNX derivatives publication index](https://portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html)
- [HNX derivatives information-service catalogue](https://hnx.vn/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html)
- [HNX information-service technical guide](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html)
- [HNX information-service registration guide](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html)
- [HNX information-service overview](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html)
- [HNX 2026 information-service package and price document](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf)
- [HNX official market board](https://banggia.hnx.vn/)
- [VSDC product information](https://www.vsd.vn/en/thong-tin-san-pham)
- [VSDC historical VN30 futures contract-list notice](https://vsd.vn/en/ad/141951)
- [VSDC DSP/FSP UI action route](https://www.vsd.vn/gia-thanh-toan/search)
- [VSDC maturity/final-payment UI action route](https://www.vsd.vn/lich-dao-han-thanh-toan/changepage)
