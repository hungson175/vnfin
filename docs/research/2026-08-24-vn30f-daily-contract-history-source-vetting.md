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
reviewer approval, retain an empty new source chain, and reopen only on the conjunctive evidence in
§12. This is not a claim that no data exists. It is a claim that no source unit in this bounded
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
| HNX — [`/vi-vn/phai-sinh/san-pham.html`](https://www.hnx.vn/vi-vn/phai-sinh/san-pham.html) | Official derivatives product/navigation control; it identifies the stock-index futures product family and links model-contract/trading-calendar material. It is not a returned per-contract D1 history. | `contract_code`, response-backed expiry rows, OHLC/volume/OI/settlement history, bounds, pages/revisions, runtime and reuse rights | `FIELD_GAP` |
| HNX — [`/vi-vn/phai-sinh/ket-qua-giao-dich.html`](https://www.hnx.vn/vi-vn/phai-sinh/ket-qua-giao-dich.html) | Official date-filtered current-result table route. Its published table headings expose product, identity-related columns, expiry month, high/low/open/close, market-volume subcolumns, OI and settlement concepts. This is a selected-day surface; no live row is retained. | No proved bulk historical cursor/retention, provider-declared 2018-to-current bounds, revision/duplicate contract, response MIME/status contract, or automation/storage/caller-return/redistribution grant | `COVERAGE_GAP` |
| HNX — [`/vi-vn/phai-sinh.html`](https://hnx.vn/vi-vn/phai-sinh.html) | Official derivatives landing/navigation surface with product and market-data links. | No exact history operation, field envelope, bounds, page totals, or reuse terms | `NOT_PROBED` |
| HNX — [`portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html`](https://portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html) | Official derivatives announcements/publication index. It is a document/disclosure control, not a reconciled all-contract D1 history source. | No single history operation, row schema, complete contract/session totals, revision policy, or library-use grant | `COVERAGE_GAP` |
| HNX — [`/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html`](https://hnx.vn/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html) | Official derivatives information-service catalogue. It exposes separate end-of-day, statistics, publication and historical-data package categories; reviewed package evidence names per-contract EOD concepts and an Excel/InfoFile delivery route. | Historical tab contents, retention/backfill, exact VN30F universe, revisions, technical schema, rate, automation and reuse rights are not publicly bound | `COVERAGE_GAP` |
| HNX — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html) | Official information-service/technical-guide lead for market-data messaging, including derivatives. It establishes a service family, not a free no-login OSS route. | Exact public route/version, registration/contract terms for this use, historical response schema, bounds, rate, caller return and redistribution | `LEGAL_GAP` |
| HNX — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html) | Official registration flow says a customer requests information, receives fees and a contract template, and proceeds after agreement/signing. | No public OSS entitlement, historical span, field specification, rate, retention or caller-return/redistribution right | `LEGAL_GAP` |
| HNX — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html) | Official service overview says derivatives data is supplied as an information service and fees are package-based. | Contract-specific delivery, historical retention, automation, storage and redistribution remain unresolved | `LEGAL_GAP` |
| HNX — [2026 data-package and service-price document](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf) | Official package/pricing document describes derivatives market-data package concepts, including contract code, prices, settlement, OI and volume/value fields. It is commercial/service evidence, not a granted public API. | Exact package entitlement, automation, storage, caller return, redistribution, commercial and rate rights for this library are not granted in the reviewed material; full historical bounds/revisions are not proved | `LEGAL_GAP` |
| HNX — [`banggia.hnx.vn`](https://banggia.hnx.vn/) | Official current market-board control with derivatives identity/price concepts. Current board output is not a historical per-contract D1 operation. | Historical coverage, session totals, OI/settlement revision, bounded pagination, and OSS reuse rights | `COVERAGE_GAP` |
| VSDC — [`/en/thong-tin-san-pham`](https://www.vsd.vn/en/thong-tin-san-pham) | Official product information identifies VN30 Index Futures, HNX ticker allocation, multiplier/contract size, listing/trading/delivery facts, tick size, last trading date, cash settlement, and DSP/FSP concepts. It does not publish the requested all-contract OHLC/volume/OI D1 history. | History route, per-session OHLC/volume/OI rows, provider-declared bounds/revisions, pagination, automation, caller-return, storage and redistribution | `FIELD_GAP` |
| VSDC — [historical contract-list notice](https://vsd.vn/en/ad/141951) | Official notice table binds a VN30 futures product to securities code/ISIN and first/last/final payment dates for a dated contract-list publication. No exact live row is retained. | It is metadata/list publication, not a per-session D1 bar/volume/OI/settlement history; no route-wide coverage, revision, runtime or OSS reuse grant | `FIELD_GAP` |
| VSDC — [`/gia-thanh-toan/search`](https://www.vsd.vn/gia-thanh-toan/search) | Undocumented UI action route associated with the official DSP/FSP table; its visible table uses a product identifier and a payment-date filter. It is retained only as an uncalled route lead, not as an API contract. | No documented history API, identity join to derivatives code/ISIN, proof that payment date is trading session, OHLC/volume/OI, bounds, rate or reuse rights | `TRANSPORT_INCONCLUSIVE` |
| VSDC — [`/lich-dao-han-thanh-toan/changepage`](https://www.vsd.vn/lich-dao-han-thanh-toan/changepage) | Undocumented UI action route for paginated maturity/final-payment metadata. | Metadata schedule is not per-session D1 history; page contract, field identity, coverage, transport and reuse rights are unproved | `FIELD_GAP` |

### 3.1 What the official evidence does and does not prove

- HNX's date-filtered current-result surface is the strongest same-owner public lead because its official table labels
  the product/expiry, OHLC, market-volume, OI, and settlement concepts. A current table is not a
  history endpoint. It cannot prove retention from `2018-01-01`, a complete session/contract
  universe, page reconciliation, or revisions.
- HNX's catalogue, service guides, registration flow and 2026 package document show that richer
  derivatives data is a fee/package/contract-controlled information service. The package evidence
  is the strongest field match (`PS.EOD01`-style per-contract EOD concepts delivered through the
  service), but it does not grant this OSS library a free automated route, storage right,
  caller-return right, redistribution right, or rate policy. Written confirmation is still needed
  for the exact delivery channel and historical retention.
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
  automation and downstream-use permission. No rights are inferred from a public page.

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
   are evidence to review with the owner; neither is a free reuse grant.
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
- A logical unit is one exact owner/route/version/operation reservation. Every network dispatch,
  including a followed redirect or retry, reserves a physical dispatch before sending. A page or
  cursor response charges one page only after its page identity is known. A retry reserves a retry
  and a new physical dispatch; a redirect follow-up reserves a redirect and a new physical dispatch.
- The reservation is atomic: under one request lock, check every applicable finite ceiling and apply
  the complete reservation or none. A failed reservation dispatches nothing. No counter may be
  incremented by a later cleanup path after a failed reservation.
- Compressed bytes are charged from bytes received before decompression; decompressed bytes are
  charged after decoding. Each stream has a hard finite cap; crossing either cap aborts the request,
  discards private rows, and cannot yield a partial public result. No `Content-Length` is trusted as
  the only byte guard.
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
  or revocation posture is not explicit for this library.

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
5. deterministic sanitized fixtures and RED cases covering identity, field types/units, full versus
   declared partial, authoritative versus inconclusive empty, pagination/counts, revisions, byte and
   global-budget exhaustion, atomic no-partial behavior, source identity, public diagnostics and
   blacklist/secret/query/path/object/clean-tree/build gates.

All five groups are conjunctive. A VSDC metadata success cannot repair an HNX row failure; a current
HNX table cannot repair missing history; and a legal or budget gap keeps the runtime chain empty.
After a qualified unit, request a fresh design/API decision and then a separate RED-first
implementation review. This packet does not authorize either.

## 10. Future API boundary

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
public snapshots, and sanitized errors before any implementation.

## 11. Lifecycle and publication gate

The intake lifecycle was recorded in local commit `7b70a5c79cc6d730e86c518d304df24f67ecfcc5` from
published base `001cfd1`. It records `#226` as `SOURCE_DESIGN`, actor `vnfin-oss`, next
`PREPARE_EXACT_SHA_SOURCE_DESIGN`, packet anchor `31d75d5687b18f64659a933d9ff3c829646d6abe`, and
public receipt `issuecomment-5390575929`.

The two artifact files in this handoff are the only source/design files for #226. The matching
backlog lifecycle must be updated only after these docs are committed and gates pass, with the exact
content SHA/range, reviewer-owned `DESIGN_REVIEW` phase, actor `vnfin-oss-reviewer`, next
`RETURN_EXACT_SHA_DESIGN_VERDICT`, and the clean `origin/master` base recorded. No push or issue
close occurs before exact-SHA design approval.

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
