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

No retained exact owner/route unit currently establishes all of identity, expiry, session, OHLC,
contract volume, OI, settlement, requested bounds, revision, finite transport, and lawful
automation/storage/caller-return/redistribution. The correct design result is `SOURCE-GAP CLOSURE`;
it is not a claim that no commercial or private data exists.

Before this research, `docs/vnstock-blacklist.md` was read and every web search used:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited material was opened or used. Only official HNX/VSDC pages/documents are admitted.

## 2. Exact candidate units and dispositions

Each row is an independent owner + exact route + operation. Static research is not a candidate
HTTP dispatch; all candidate discovery/history dispatch counts are `0 / 0` logical/physical.
In the table, “not established in retained evidence” is a bounded evidence disposition, not a
claim that the provider has no private, commercial, or separately licensed data.

| Unit | What it can establish | Why it cannot qualify this primitive | Disposition |
| --- | --- | --- | --- |
| HNX product page — [`/vi-vn/phai-sinh/san-pham.html`](https://www.hnx.vn/vi-vn/phai-sinh/san-pham.html) | Official stock-index futures product/navigation control | Per-session rows, complete fields, bounds, revisions, and reuse rights are not established in retained evidence | `FIELD_GAP` |
| HNX current result — [`/vi-vn/phai-sinh/ket-qua-giao-dich.html`](https://www.hnx.vn/vi-vn/phai-sinh/ket-qua-giao-dich.html) | Date-filtered official table labels product/expiry, OHLC, volume concepts, OI and settlement | A selected-day table does not establish bulk historical retention, complete contract/session totals, page/revision semantics, or OSS rights | `COVERAGE_GAP` |
| HNX derivatives landing — [`/vi-vn/phai-sinh.html`](https://hnx.vn/vi-vn/phai-sinh.html) | Official derivatives navigation | Exact history operation, envelope, bounds, pages, and reuse terms are not established in retained evidence | `NOT_PROBED` |
| HNX publication index — [`portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html`](https://portal.hnx.vn/vi-vn/phai-sinh/thong-tin-cong-bo.html) | Official disclosure/document navigation | Documents are not a reconciled all-contract D1 response; machine-reuse permission is not established in retained evidence | `COVERAGE_GAP` |
| HNX data-service catalogue — [`/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html`](https://hnx.vn/vi-vn/dich-vu-cctt/du-lieu-cung-cap-der.html) | Official derivatives package catalogue; the reviewed EOD package evidence names per-contract OHLC/settlement/OI/volume/status concepts and Excel/InfoFile delivery | Historical retention, exact VN30F universe, revision, rate, automation, and reuse are not established in retained evidence | `COVERAGE_GAP` |
| HNX information-service guide — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-YCKT.html) | Official market-data service family lead; it does not by itself establish a free no-login OSS route | Exact route, entitlement, schema, history, rate, and reuse rights are not established in retained evidence | `LEGAL_GAP` |
| HNX registration guide — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html) | Official request/fee/contract-signing flow | OSS entitlement, historical span, rate, retention, and redistribution right are not established in retained evidence | `LEGAL_GAP` |
| HNX service overview — [`/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html`](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html) | Official fee/package information-service posture | Exact history route, retention, automation, storage, and redistribution are not established in retained evidence | `LEGAL_GAP` |
| HNX 2026 package/price document — [official PDF](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf) | Official derivatives field/package and commercial-service evidence; retained text does not establish a granted public API | Free library permission, exact historical route, and coverage contract are not established in retained evidence | `LEGAL_GAP` |
| HNX current board — [`banggia.hnx.vn`](https://banggia.hnx.vn/) | Official current market-board control | Not historical D1; requested bounds, revisions, and reuse contract are not established in retained evidence | `COVERAGE_GAP` |
| VSDC product page — [`/en/thong-tin-san-pham`](https://www.vsd.vn/en/thong-tin-san-pham) | VN30 futures identity, multiplier, delivery/settlement concepts, DSP/FSP navigation | Same-owner OHLC/volume/OI history and library-use permission are not established in retained evidence | `FIELD_GAP` |
| VSDC contract-list notice — [`/en/ad/141951`](https://vsd.vn/en/ad/141951) | Official code/ISIN/first-last-final-payment metadata for a dated list | Metadata list is not a per-session OHLC/volume/OI/settlement history; broader route rights are not established in retained evidence | `FIELD_GAP` |
| VSDC DSP/FSP UI action — [`/gia-thanh-toan/search`](https://www.vsd.vn/gia-thanh-toan/search) | Undocumented official UI action lead for a payment-date-filtered DSP/FSP table; not called as an API | Identifier join to derivatives code/ISIN, payment-date versus trading-session, OHLC/volume/OI, bounds, and rights are not established in retained evidence | `TRANSPORT_INCONCLUSIVE` |
| VSDC maturity UI action — [`/lich-dao-han-thanh-toan/changepage`](https://www.vsd.vn/lich-dao-han-thanh-toan/changepage) | Undocumented official UI action lead for paginated maturity/final-payment metadata | Metadata schedule is not per-session D1 history; page contract, field identity, coverage, transport, and reuse are not established in retained evidence | `FIELD_GAP` |

The matching sanitized evidence ledger is research §3.2 and is normative for every row in this
inventory. For each exact unit, candidate dispatch is `NOT_PROBED` with
`logical/physical/pages/retries/redirects/compressed_bytes/decompressed_bytes = 0/0/0/0/0/0/0`;
the first candidate route/transport slot `route_version` is `NOT_RETAINED`, as are method, status
class, complete MIME, effective route, redirect, auth/session/UA/WAF/rate, and unproven rights axes;
they remain explicit `NOT_RETAINED` rather than positive evidence. The design note
does not promote an uncalled UI action or static document into a data response.

The later API gate must use `(session, contract_code)` as the unique composite row key and order
validated rows by `session ASC, contract_code ASC`, using the exact canonical contract-code string.
Identical or conflicting repeated keys fail atomically. A qualification unit must structurally serve
`session`, `contract_code`, `product`, `expiry`, all OHLC fields, `volume`, `open_interest`, and
`settlement`; a structurally absent field is `FIELD_GAP`, not a globally not-applicable nullable
field. A null is allowed only for an individual row with a provider-documented finite
nonpublication/not-applicable state for that field, never parser loss, unknown identity, truncation,
budget exhaustion, or an omitted schema field.

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

One request owns one sequential (`max_concurrency = 1`, single-flight) atomic ledger with distinct counters:

```text
logical_units, physical_dispatches, discovery_pages, history_pages,
retries, redirects, compressed_bytes, decompressed_bytes
```

Reserve each logical page/cursor before its request is sent, and reserve every applicable
logical/physical/page/retry/redirect unit atomically under one request lock. After dispatch, the
returned page/cursor identity must match the reservation before any row is accepted. A malformed or
mismatched response still consumes the attempted page and physical dispatch and accepts no rows.
Every redirect/retry is a real physical operation and is counted separately. Only streamed bytes
charge after dispatch: compressed bytes charge before decompression and decompressed bytes after
decoding. Crossing either finite stream cap aborts and discards all private rows. A failed
reservation dispatches nothing. The later source-specific design PASS must pin finite numeric
ceilings tied to the owner's rate/terms; this source-gap packet freezes no unsupported number or
retry timing. Exhaustion preserves only real, bounded sanitized attempts and never fabricates an
attempt or returns authoritative empty.

The exact legal gate covers automation, rate/retry/concurrency, transient/cache/storage/retention/
delete, attribution, commercial use, derivative use, caller return, redistribution/resale,
amendment and revocation. HNX service/package evidence and VSDC page visibility are observed facts,
not permission slots; their retained text does not establish a free OSS license.

## 6. Conjunctive reopen gate and future implementation gate

Reopen only when one exact owner/route/version/operation proves every identity/field/unit/coverage/
revision/transport/budget/legal axis above, with a source-only sanitized evidence packet and an
explicit no-false-absence contract. The complete evidence must include exact requested/full or
declared-partial bounds, reconciled pages/totals, authoritative versus inconclusive empty,
redirect/MIME/status/byte behavior, an atomic global-budget ledger, and owner rights evidence. No
RED test, public model, API snapshot, or release artifact is a source reopen prerequisite.

After that source-specific design PASS, hold a separate API/model decision that freezes only the
public contract; it does not authorize tests or code. The public contract includes row/result types,
signatures, coverage/diagnostics, units, and docs. Only a subsequent, separately approved RED-first
review authorizes tests; implementation/code still requires green results and code review. The
complete future API/RED/release matrix is §7 below; it is not authorized now.

## 7. Future API/RED/release matrix (not authorized)

This is a later gate copied into the design boundary so source reopening cannot be confused with API
or TDD authorization. No RED test, fixture, parser, mapping, model, source registration, or runtime
capability is created by this correction.

| Future gate | Required cases after source qualification and separate API decision |
| --- | --- |
| All-contract/exact-contract success | All-contract and exact-contract success; inclusive date bounds; caller-malformed bounds/product/contract/date inputs fail before cache lookup and network, with the later RED asserting an untouched cache; malformed provider responses are evaluated only after dispatch and fail before cache insertion or public return; exact `VN30F` identity and optional contract validation. |
| Identity/fields | Response-backed product, code, expiry, Vietnam session/calendar, source, units/scale/precision, OHLC finite/non-bool invariants, non-negative integral contract volume/OI, settlement/DSP/FSP meaning, ordering, `(session, contract_code)` identity, identical/conflicting duplicates, structural required-field absence, per-row nullability and revisions. |
| Coverage/no-false-absence | `FULL`, provider-declared `QUALIFIED_PARTIAL`, expired-contract retention, current-date lag, nonpublication, authoritative empty, unknown/inconclusive empty, totals/pages/cursors, page identity mismatch, gaps, duplicate/conflict, boundaries and revisions. |
| Wrong/malformed negatives | Wrong/mixed product or contract, cash index, continuous/rolled/front-month, tape/intraday, inferred expiry/session, malformed envelope/MIME/status/redirect/WAF, missing identity, invalid dates/expiry, bool/non-finite/broken OHLC, negative/non-integral counts, unit mismatch, structurally absent required field and invalid per-row null. |
| Atomic runtime/diagnostics | Sequential `max_concurrency=1`; logical/physical/page/retry/redirect reservation and charge; compressed/decompressed byte caps; global-budget exhaustion; malformed/mismatched page consumption; atomic no-partial behavior; one-source-win/no-stitch; bounded sanitized attempts/warnings; retrieval timestamp; no raw URL/query/body/header/cookie/provider prose/secret. |
| API/units/docs gate | Later public signatures and API snapshots; exact session/date-input semantics; price/volume/OI/settlement units, scales, precision, and nullability; source/provenance and sanitized error/warning carriers; explicit `docs/api.md` and `docs/units.md` contracts plus examples/tutorial/architecture/skill/CHANGELOG consistency; no undocumented public token. |
| Model/API/compatibility/release | Later immutable row/result and coverage decision; DataFrame attrs/provenance; serialization/repr/equality; model/export/error snapshots; existing-domain compatibility; release artifacts; focused/full offline tests; import/version; isolated wheel/sdist; blacklist/secret/diff/path/object/clean-tree and exact remote scope/ancestry gates. |

Source qualification comes first. A new API/model decision then specifies and freezes the public
carriers and units/docs contract; it is separate from RED authorization. Only a later RED-first
approval authorizes tests; after RED/GREEN and code review, implementation may proceed. No public
model, warning, exception, export or release claim is frozen here.

## 8. Lifecycle handoff

Intake is durably recorded in `7b70a5c79cc6d730e86c518d304df24f67ecfcc5` from published
`origin/master` `001cfd1cafc0d0554640c5b9672dc09029b388b2`. The prior design BLOCK was recorded first
in backlog commit `09f7aea`, for reviewed merged HEAD `eb1c8cefe42556220507a242d0aa6de58c98e385`,
report `reviews/review-202608241126-issue226-design-source-gate.md`, reviewer `c57fc9d`, and
delivery `#5112ed77`. This correction must return one exact merged SHA whose lifecycle binds that
prior HEAD, the clean `001cfd1` base, and the exact base-to-correction range. #227 remains queued
after verified #226 closure.

The disposition remains `SOURCE-GAP CLOSURE`: #202 is separate, the chain remains empty, and no
probe, RED, code, push or close is authorized by this correction.

## Sources

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
