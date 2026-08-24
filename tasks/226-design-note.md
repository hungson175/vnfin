# #226 design note — VN30F daily per-contract history

**Packet:** `tasks/226-vn30f-daily-contract-history-spec.md` at reviewer
`31d75d5687b18f64659a933d9ff3c829646d6abe`
**Published base:** `origin/master` `001cfd1cafc0d0554640c5b9672dc09029b388b2`
**Builder intake:** `7b70a5c79cc6d730e86c518d304df24f67ecfcc5`
**Phase:** source/design only
**Disposition:** **`SOURCE-GAP CLOSURE`**
**New source chain:** empty
**Requested design window:** inclusive `2018-01-01..date.today()`; a narrower caller interval must
still be covered by the same provider-declared bounds and reconciliation contract.

This is a documentation-only clean-room source/legal design. It does not add a derivatives package,
source registration, model, accessor, public symbol, live row, RED test, production code, coverage
claim, push, or issue closure. #202 remains separate: its matched-trade/sub-minute/order-flow scope
is not a source or fallback for daily contract history.

## 1. Boundary and decision

The requested future primitive is illustrative only:

```python
vnfin.derivatives.contract_history(
    product="VN30F",
    start=date(2018, 1, 1),
    end=date.today(),
    contract=None,
)
```

A future all-contract request would need one provider-owned row per VN30F contract and Vietnam
trading session with `session`, `contract_code`, `product`, `expiry`, `open`, `high`, `low`,
`close`, `volume`, `open_interest`, `settlement`, canonical source, UTC retrieval time, and bounded
sanitized diagnostics. An exact-contract filter could be additive only through the same identity and
validation path.

No exact owner/route unit currently proves all of identity, expiry, session, OHLC, contract volume,
OI, settlement, requested bounds, revision, finite transport, and lawful automation/storage/
caller-return/redistribution. The correct design result is `SOURCE-GAP CLOSURE`; it is not a claim
that no commercial or private data exists.

Before this research, `docs/vnstock-blacklist.md` was read and every web search used:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited material was opened or used. Only official HNX/VSDC pages/documents are admitted.

## 2. Exact candidate units and dispositions

Each row is an independent owner + exact route + operation. Static research is not a candidate
HTTP dispatch; all candidate discovery/history dispatch counts are `0 / 0` logical/physical.

| Unit | What it can establish | Why it cannot qualify this primitive | Disposition |
| --- | --- | --- | --- |
| HNX product page — [`/vi-vn/phai-sinh/san-pham.html`](https://www.hnx.vn/vi-vn/phai-sinh/san-pham.html) | Official stock-index futures product/navigation control | No per-session rows, complete fields, bounds, revisions, or reuse rights | `FIELD_GAP` |
| HNX current result — [`/vi-vn/phai-sinh/ket-qua-giao-dich.html`](https://www.hnx.vn/vi-vn/phai-sinh/ket-qua-giao-dich.html) | Date-filtered official table labels product/expiry, OHLC, volume concepts, OI and settlement | A selected-day table does not prove bulk historical retention, complete contract/session totals, page/revision semantics, or OSS rights | `COVERAGE_GAP` |
| HNX publication index — [`portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html`](https://portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html) | Official disclosure/document navigation | Documents are not a reconciled all-contract D1 response and do not grant machine reuse | `COVERAGE_GAP` |
| HNX data-service catalogue — [`/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html`](https://hnx.vn/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html) | Official derivatives package catalogue; the reviewed EOD package evidence names per-contract OHLC/settlement/OI/volume/status concepts and Excel/InfoFile delivery | Historical retention, exact VN30F universe, revision, rate, automation and reuse are not public | `COVERAGE_GAP` |
| HNX information-service guide — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html) | Official market-data service family lead | Exact no-login route, entitlement, schema, history, rate and reuse rights are not proven | `LEGAL_GAP` |
| HNX registration guide — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html) | Official request/fee/contract-signing flow | No OSS entitlement, historical span, rate, retention or redistribution right | `LEGAL_GAP` |
| HNX 2026 package/price document — [official PDF](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf) | Official derivatives field/package and commercial-service evidence | No free library license or exact historical route/coverage contract | `LEGAL_GAP` |
| HNX current board — [`banggia.hnx.vn`](https://banggia.hnx.vn/) | Official current market-board control | Not historical D1, no requested bounds/revisions/reuse contract | `COVERAGE_GAP` |
| VSDC product page — [`/en/thong-tin-san-pham`](https://www.vsd.vn/en/thong-tin-san-pham) | VN30 futures identity, multiplier, delivery/settlement concepts, DSP/FSP navigation | No same-owner OHLC/volume/OI history or library-use grant | `FIELD_GAP` |
| VSDC contract-list notice — [`/en/ad/141951`](https://vsd.vn/en/ad/141951) | Official code/ISIN/first-last-final-payment metadata for a dated list | Metadata list is not per-session OHLC/volume/OI/settlement history | `FIELD_GAP` |
| VSDC DSP/FSP UI action — [`/gia-thanh-toan/search`](https://www.vsd.vn/gia-thanh-toan/search) | Undocumented official UI action lead for a payment-date-filtered DSP/FSP table; not called as an API | Identifier join to derivatives code/ISIN, payment-date versus trading-session, OHLC/volume/OI, bounds and rights are gaps | `TRANSPORT_INCONCLUSIVE` |
The HNX current table is a promising research lead, not a qualification. The HNX EOD package is the
best full-field candidate but is contract-controlled and lacks a public historical/reuse contract.
VSDC contract and DSP/FSP metadata is not a complete bar source. No candidate is `QUALIFIED` or
`QUALIFIED_PARTIAL` and no TDD transition is authorized.

No other provider route was admitted as a qualification unit: an exact owner, canonical route,
operation, and rights-clear no-login contract would have to be named before it could be researched.
Paid, login, private, copied, proxy, and reporter routes remain excluded and are not fallbacks.

## 3. Required field and identity contract

These are source qualification predicates, not public model/export commitments:

- `session` is the provider's Vietnam trading-session date. It is not request order, fetched-at,
  publication date, or an inferred UTC date.
- `contract_code`, `product=VN30F`, and `expiry` must be response-backed or same-owner documented.
  Code suffixes, list positions, caller labels, and VSDC/HNX cross-owner joins cannot infer identity.
- OHLC values are finite non-boolean numeric prices in a proven quote unit/scale and satisfy
  `low <= open <= high`, `low <= close <= high`, and `low <= high`.
- `volume` and `open_interest` are non-negative integers in documented contract-count units. No
  turnover, market aggregate, change-OI, float coercion, or missing-to-zero substitute is allowed.
- `settlement` is a finite non-boolean price with a proven unit/scale. Day-end and final settlement
  are distinct when the provider distinguishes them.
- Nullable required fields are allowed only for an owner-defined finite nonpublication/not-applicable
  state. Parser loss, identity loss, truncation, conflict and budget exhaustion are fatal.
- `source` is the canonical producer identity; `fetched_at_utc` is retrieval time; warnings and
  attempts are bounded and sanitized. No synthetic attempt is made for an unmade or truncated
  dispatch.

## 4. Coverage, empty, and no-stitch rules

A future `FULL` result requires one qualified provider to declare bounds covering the request,
reconcile every declared contract/session, reconcile pages/cursors/totals, and explain
nonpublication, expiry retention, current lag, conflicts and revisions. A future
`QUALIFIED_PARTIAL` result may expose only a narrower provider-declared boundary with the same
reconciliation. It must never claim the caller's requested interval is full.

An empty result is authoritative only when product/contract identity, interval, provider totals and
calendar, and nonpublication semantics all reconcile. A blank/HTML/WAF/timeout, status/MIME mismatch,
unknown totals, malformed body, transport truncation, conflict, or budget exhaustion is inconclusive,
not empty and not source absence. Accumulators are discarded atomically on any required-axis failure.

No continuous/front/roll/expiry/settlement/OI reconstruction, missing-session fill, resample,
cash-index substitution, tape substitution, basket, cross-provider stitch, or metadata repair is
allowed. One source wins a request; no automatic failover is introduced by this source-gap note.

## 5. Transport, legal, and finite-budget contract

A future exact unit must retain sanitized owner/route/version, method, status, complete
`Content-Type`/normalized MIME, effective route, redirect count, response-shape keys, auth/session/
UA/WAF behavior, page/cursor behavior, compressed/decompressed byte totals, revision behavior, and
rate/retry evidence. Query strings, raw bodies/headers, cookies, provider prose, secrets and live
rows are excluded.

One request owns one atomic ledger with distinct counters:

```text
logical_units, physical_dispatches, discovery_pages, history_pages,
retries, redirects, compressed_bytes, decompressed_bytes
```

Reserve every logical/physical/page/retry/redirect unit before dispatch under one request lock.
Charge compressed bytes before decompression and decompressed bytes after decoding; crossing either
finite stream cap aborts and discards all private rows. Every redirect/retry is a real physical
operation and is counted separately. A failed reservation dispatches nothing. The later
source-specific design PASS must pin finite numeric ceilings tied to the owner's rate/terms; this
source-gap packet freezes no unsupported number or retry timing. Exhaustion preserves only real,
bounded sanitized attempts and never fabricates an attempt or returns authoritative empty.

The exact legal gate covers automation, rate/retry/concurrency, transient/cache/storage/retention/
delete, attribution, commercial use, derivative use, caller return, redistribution/resale,
amendment and revocation. HNX service/package evidence and VSDC page visibility are not a free OSS
license.

## 6. Conjunctive reopen gate and future implementation gate

Reopen only when one exact owner/route/version/operation proves every identity/field/unit/coverage/
revision/transport/budget/legal axis above, with sanitized fixtures and an explicit no-false-absence
contract. The complete evidence must include exact requested/full or declared-partial bounds,
reconciled pages/totals, authoritative versus inconclusive empty, redirect/MIME/status/byte behavior,
and an atomic global-budget ledger.

After that source-specific design PASS, request a new API decision. Only a subsequent RED-first
implementation review may freeze public row/result types, coverage carriers, warnings/exceptions,
exports, DataFrame attrs, serialization, cache behavior, compatibility docs, tests and CHANGELOG.
This note authorizes none of them.

## 7. Lifecycle handoff

Intake is durably recorded in `7b70a5c79cc6d730e86c518d304df24f67ecfcc5` from published
`origin/master` `001cfd1cafc0d0554640c5b9672dc09029b388b2`. The intake row records:

- phase `SOURCE_DESIGN`;
- actor `vnfin-oss`;
- next action `PREPARE_EXACT_SHA_SOURCE_DESIGN`;
- packet anchor `31d75d5687b18f64659a933d9ff3c829646d6abe`;
- public triage receipt `issuecomment-5390575929`; and
- #202 separation, empty chain, and no probe/RED/code/push/close before design PASS.

After the research and this note are committed and merged-tree gates pass, the backlog will record
one reviewer-owned `DESIGN_REVIEW` handoff with the exact content SHA, actor `vnfin-oss-reviewer`,
next `RETURN_EXACT_SHA_DESIGN_VERDICT`, clean base/range, and no push/close. No public runtime
capability is implied.

## Sources

- [HNX derivatives landing](https://hnx.vn/vi-vn/phai-sinh.html)
- [HNX derivatives products](https://www.hnx.vn/vi-vn/phai-sinh/san-pham.html)
- [HNX current derivatives result](https://www.hnx.vn/vi-vn/phai-sinh/ket-qua-giao-dich.html)
- [HNX derivatives publication index](https://portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html)
- [HNX derivatives information-service catalogue](https://hnx.vn/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html)
- [HNX information-service technical guide](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html)
- [HNX information-service registration guide](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html)
- [HNX 2026 information-service package and price document](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf)
- [HNX official market board](https://banggia.hnx.vn/)
- [VSDC product information](https://www.vsd.vn/en/thong-tin-san-pham)
- [VSDC historical VN30 futures contract-list notice](https://vsd.vn/en/ad/141951)
- [VSDC DSP/FSP UI action route](https://www.vsd.vn/gia-thanh-toan/search)
