# #222 design note — VN100 D1 index-value history

**Date:** 2026-08-23 (UTC+7)
**Packet:** `tasks/222-vn100-index-history-source-spec.md` at reviewer `001ad85`
**Phase:** `SOURCE_DESIGN` / docs-only
**Disposition:** **SOURCE-GAP CLOSURE**
**Current VN100 value-history chain:** empty
**Companion evidence:** [`docs/research/2026-08-23-vn100-index-history-source-vetting.md`](../docs/research/2026-08-23-vn100-index-history-source-vetting.md)

This note binds the design gate only. It authorizes no source registration, enum change, adapter,
model, RED test, public token, API capability, proxy, constituent basket, downstream signal, push, or
issue close before exact-SHA design review.

## 1. Clean-room and current boundary

`docs/vnstock-blacklist.md` was read before the source review. The required exclusion was applied:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited or derivative source, reporter endpoint, copied dataset, login/session bypass, paid
feed, raw response, live value, query-bearing URL, cookie, header, credential, or response digest is
retained. The companion report uses only official HOSE, VPS, SSI, and VNDIRECT evidence.

On the current runtime line, `VN100` is in the recognized index deny-list but absent from the value-
history allow-list. Both `index_history` and `index_history_stitched` therefore fail typed and
zero-network with the shared recognized-index/no-served-source diagnostic. The existing VPS → SSI →
VNDIRECT order remains the default for already-served indices; it is not a VN100 qualification.

Exact tag `2fe50df4f27064140ff9f7a680227a2b337ec74a` predates the current registry/value-history
allow-list. Its `IndexClient.index_history` passes a validated symbol to the default failover and
must not be described as today's VN100 deny guard. This is a release-compatibility observation, not
source evidence.

## 2. Qualification unit and decision

One future qualification unit is:

```text
owner + exact route/version + provider VN100 identity
+ exact D1 token and point/volume/time semantics
+ requested coverage and pagination/revision contract
+ bounded automation/rate/retry/byte policy
+ attribution/storage/commercial/derivative/redistribution rights
```

Every member of the tuple must pass in the same unit. HOSE owner methodology, a provider UI label,
a generic API method, VN30/VNMidcap agreement, an ETF, a constituent basket, or a quote/futures
page cannot fill a missing response or rights axis.

| Unit | Positive evidence | Blocking axes | Decision |
|---|---|---|---|
| HOSE owner route | Official factsheets summarize VN100 as VN30 plus VNMidcap and give base date/value, price/TRI forms, cadence, method, and ownership contact | no retained no-login D1 history response, full-span/page/revision contract, or redistribution grant | `SOURCE-GAP` |
| VPS `vps_index` | provider-owned candidate host/path and official SmartOne VN100 UI recognition | response identity, transport/envelope, coverage, semantics, rate policy, legal/reuse | `SOURCE-GAP` |
| SSI `ssi_index` / FastConnect | official generic index summary/OHLC docs and typed API models | account/key/approval gate; no VN100 response identity, span, semantics, or redistribution contract | `SOURCE-GAP` |
| VNDIRECT `vndirect_index` | official VN100 quote/futures recognition and provider-owned chart candidate | no response-backed D1 history/schema, coverage, bounds, policy, or reuse contract | `SOURCE-GAP` |

The new chain is empty. No candidate is `QUALIFIED FOR TDD` or `QUALIFIED_PARTIAL`.

## 3. Evidence ledger and fail-closed interpretation

No provider/API data route was probed in this docs-only design pass. For each candidate, the exact
qualifying data ledger is `1` planned logical unit, `0` qualifying logical/physical dispatches,
`0` pages/cursors, and `0` retries. Status, complete Content-Type, normalized MIME, redirect,
response envelope, and response identity are `NOT_PROBED`. Official documentation/page reads are
research traffic whose per-request transport fields are `NOT_RETAINED`; they are not counted as
provider data dispatches and do not prove service or absence.

The terms are strict:

- `NOT_PROBED` = the route was deliberately not called;
- `NOT_RETAINED` = a read did not preserve a deterministic transport record;
- `NOT_ESTABLISHED` = official material did not prove the axis;
- `SOURCE-GAP` = the conjunctive qualification failed; and
- none of these is a claim that historical data does not exist.

An empty, failed, capped, recent-only, WAF/403, timed-out, or uncalled route never proves historical
absence. Do not fabricate a `SourceAttempt` for an uncalled provider or convert a missing MIME,
page total, response symbol, or rights field into zero/success.

## 4. Current API and no-capability contract

The following current behavior is preserved byte-for-byte by this design:

- recognized identifiers stay in the index namespace and cannot fall through to equity prices;
- `VN100` fails before network in both strict and opt-in stitched calls;
- the current served indices retain their existing strict D1/points/RAW behavior and source order;
- no VN100 enum/mapping/source registration/model/API response is added; and
- no proxy, local index calculation, basket, ETF, TRI substitution, or downstream signal is exposed.

A source-gap design PASS, if granted, authorizes only merged source/design/backlog publication,
exact-anchor remote verification, a clean no-capability resolution, and issue close/re-read. It does
not authorize TDD, RED, or runtime implementation.

## 5. Future contract only after an independent qualification PASS

This section is a design boundary, not a current public API.

### 5.1 Input and identity

A future implementation may accept only the canonical `VN100` value-history selector and exact D1
under an explicitly reviewed compatibility change. It must reject malformed, punctuation, proxy,
unknown, constituent, TRI-only, non-D1, and price-path inputs before network. The provider identity
must remain VN100 from request through response and public provenance; a provider alias may be
retained only as bounded internal provenance with a documented canonical mapping.

A qualified response must establish, in one response/route unit:

- provider symbol, owner, exchange/index type, and price-index versus VN100TRI distinction;
- explicit rejection/identity negatives for request or response values `VN30`, `VNMID`,
  `VNALLSHARE`, `VNALL`, `VNXALL`, and `VNXALLSHARE`; none may canonicalize, map, or be accepted
  as `VN100`, even though some are current served aliases or recognized deny-only identifiers;
- strictly positive finite point/OHLC values and point scale (the typed unit is `points`, never
  VND price); zero, negative, non-finite, and malformed values are RED negatives;
- local trading date, timezone/session/close meaning, and adjustment policy `RAW`;
- OHLC structural rules, if OHLC is served; and
- volume presence/unit/nullability/meaning. Current `PriceHistory` requires a whole non-negative
  integer volume; a qualified response that omits volume is therefore unqualified unless a separate
  model/API PASS authorizes an optional carrier. Never invent zero or a stock-volume interpretation.

### 5.2 Coverage and one-source atomicity

The requested window is inclusive `2018-01-01..2026-08-20`. `FULL` may be used only when the one
provider declares/serves the requested boundary, returns all required distinct normalized D1 rows,
and reconciles page/cursor/window totals, duplicates, conflicts, revision/as-of behavior, and
trading-calendar gaps. A provider-declared supported subrange may be `PARTIAL` only if its start/end
and pages reconcile and the public result is explicitly partial. Unexplained gaps, conflicting
rows, unreconciled pages, or truncation are terminal unknown/failure.

Strict history is one provider for the whole request. There is no cross-provider stitch, constituent
reconstruction, ETF/other-index proxy, silent strict-to-stitched route, or basket. The existing
stitched API remains opt-in and unchanged. If a future qualification/API PASS authorizes VN100 in
that existing path, it must preserve calendar-year segmentation, inclusive year boundaries,
per-segment validation, identical/conflicting seam behavior, atomic mid-range failure, and canonical
segment provenance. After each segment passes validation, it must supply a timezone-aware UTC
`fetched_at_utc`; the aggregate result uses exactly `max(segment.fetched_at_utc)` over the validated
segment stamps. Missing, naive, or non-UTC segment timestamps fail the aggregate atomically. The
global identity/history ledger still charges every identity/page/retry/redirect/byte reservation;
the path cannot invent a helper or silently route strict calls to stitched history.

### 5.3 Atomic budget and diagnostics design

No numeric public ceiling is frozen until a qualified route's written/public rate policy supplies
one. A future implementation must nevertheless obey this ledger shape:

1. validate input and capability before network;
2. reserve one logical source attempt before adapter entry, including the same-owner identity route;
3. reserve one physical dispatch immediately before each history or identity initial/page/cursor/
   retry/redirect request;
4. count response/decompression bytes separately from network dispatches, for both history and identity;
5. share one request-scoped ledger across all sources, history calls, identity calls, pages, redirects,
   retries, and bytes, with no reset per source or calendar year; and
6. discard private rows on budget/reconciliation exhaustion and emit one bounded terminal outcome,
   never a partial accumulator or false-empty/full result.

The public outcome/exception carrier is deferred until a future API review. Design-only fixed tokens
may be selected from:

```text
FULL | PARTIAL | NOT_SERVED | TRANSPORT_FAILURE | SCHEMA_DRIFT
IDENTITY_GAP | COVERAGE_GAP | TIMESTAMP_GAP | VOLUME_GAP
PAGINATION_GAP | RATE_POLICY_GAP | LEGAL_GAP | BUDGET_EXHAUSTED
```

Diagnostics may expose only finite source roles, fixed tokens, validated dates, finite counts, and
bounded warnings. Never expose raw provider URL/query, cookies, headers, bodies, live values,
arbitrary provider messages, or unbounded provider names. An uncalled source is not an attempt.

## 6. Future RED/release matrix (not authorized now)

After a fresh source qualification and separate API PASS, RED must use synthetic offline fixtures and
cover:

| Area | Required cases |
|---|---|
| Input/zero network | exact/padded/lowercase VN100; future VN100 qualification/adapter identity-mismatch fixtures for `VN30`, `VNMID`, `VNALLSHARE`, `VNALL`, `VNXALL`, and `VNXALLSHARE` must not be accepted as `VN100` without changing their normal public routing; malformed/proxy/unknown/constituent; D1 positive and all non-D1 negatives |
| Identity | correct/wrong/missing provider symbol, owner, exchange/type, price-vs-TRI, point scale, timezone/session, provenance; explicit `VN30`, `VNMID`, `VNALLSHARE`, `VNALL`, `VNXALL`, and `VNXALLSHARE` request/response/provider-alias negatives with no alias collapse |
| Transport | exact complete-MIME parsing and normalized MIME; expected envelope/status; wrong status, HTML/login, redirect/effective-host, malformed envelope |
| Values | strictly positive finite point/OHLC rows; negative/zero/non-finite/malformed values fail; volume is independently provider-defined whole/non-negative, and omitted volume is unqualified for the current carrier unless a later optional-carrier API PASS; timestamp/date rules, null/unit, RAW; no synthetic volume/adjustment |
| Coverage | requested boundaries, declared partial, provider totals/pages/cursors, trading-calendar exceptions, gaps, duplicate/conflict, revision/no-false-absence |
| Atomicity | one-source whole-window, capability skip, direct identity-call initialization/page/retry/redirect/byte exhaustion, history-only exhaustion, combined history-plus-identity aggregate exhaustion, retry/page/redirect/byte/global-budget charging with no per-source/year reset, no partial return after terminal failure |
| Stitched | existing opt-in single-year/multi-year, inclusive year boundaries, identical/conflicting seams, atomic mid-range failure, segment provenance, per-segment timezone-aware UTC `fetched_at_utc`, aggregate `fetched_at_utc` exactly `max(segment.fetched_at_utc)` after validation, missing/naive/non-UTC timestamp negatives, identity/page/retry charging, global exhaustion, no helper/silent strict fallback |
| Compatibility | current served indices, with explicit assertions that `VN30` and `VNALLSHARE`/`VNALL` remain served; all deny-only indices, price-path guard, strict/stitched behavior, public snapshots/docs/imports |
| Release | docs/skill/CHANGELOG/API snapshot if changed; focused/full offline tests, build, blacklist/secret/diff/path/object/clean-tree gates |

The wrong-index cases are future VN100 qualification/adapter identity-mismatch fixtures, not public
request rejections for already-served selectors. `VN30` and `VNALLSHARE`/`VNALL` retain their
current served behavior; current deny-only identifiers such as `VN100` retain the recognized-but-
not-served zero-network guard.

No RED, test, fixture, parser, mapping, model, source registration, or runtime capability is created
in #222.

## 7. Conjunctive reopen and completion gates

Reopen requires one fresh primary-source packet that binds all of the following to one provider unit:

1. exact route/version, D1 token, effective host, complete/normalized MIME, envelope/status,
   redirects, auth/session/WAF posture;
2. response-backed VN100 symbol/owner/type, price-vs-TRI, point scale, timezone/session, OHLC/
   volume/RAW semantics;
3. inclusive `2018-01-01..2026-08-20` provider bounds, observed dates, totals, pages/cursors,
   gaps/duplicates/conflicts, and revision behavior;
4. bounded logical/physical/page/retry/byte accounting and route-specific rate/automation policy;
5. attribution, storage/cache, commercial, derivative, and redistribution rights; and
6. atomic whole-window behavior and sanitized diagnostics with no false-absence interpretation.

A factsheet, UI, generic API documentation, current quote, timeout, cross-provider agreement, or
constituent/ETF proxy cannot reopen the gap.

After a docs-only design PASS the allowed sequence is: merged docs/full/build/blacklist/diff gates;
push only the exact approved docs/source/backlog anchor; verify exact remote HEAD, ancestry, and
paths; post a clean no-capability resolution; close and re-read #222; then record local completion.
No later local receipt may cross that approved anchor. #223, #224, and #225 remain queued until the
reviewer authorizes their transition.

## 8. Primary references

- [HOSE official index-data landing page](https://www.hsx.vn/vi/du-lieu-giao-dich/quy-mo-giao-dich/bo-chi-so)
- [HOSE VN100 factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2396611/Form_Factsheet_MCIndices_VN_T08.2025.pdf)
- [HOSE-Index factsheet, January 2026](https://staticfile.hsx.vn/Uploads/UploadDocuments/2438018/Form_Factsheet_MCIndices_VN_T02.2026.pdf)
- [HOSE official index-data presentation](https://www1.hsx.vn/vi/du-lieu-giao-dich/quy-mo-giao-dich/theo-bo-chi-so-tri)
- [VPS SmartOne](https://smartoneweb.vps.com.vn/)
- [VPS SmartOne web guide](https://smartone.vps.com.vn/en-US/Home/BriefUserGuide)
- [VPS account terms](https://motaikhoan-doitac.vps.com.vn/Content/htmlTemp/BoTCHDMTK.htm)
- [SSI overview](https://developers.ssi.com.vn/docs/getting-started/overview)
- [SSI usage and environments](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
- [SSI auth token](https://developers.ssi.com.vn/docs/api-reference/auth-token)
- [SSI Python services](https://developers.ssi.com.vn/docs/sdk/python/service-classes)
- [SSI models](https://developers.ssi.com.vn/docs/sdk/go/utilities)
- [VNDIRECT VN100 futures page](https://support.vndirect.com.vn/hc/vi/articles/51381990427417-Th%C3%B4ng-tin-h%E1%BB%A3p-đ%E1%BB%93ng-t%C6%B0%C6%A1ng-lai-ch%E1%BB%89-s%E1%BB%91-VN100)
- [VNDIRECT VN100 quote page](https://banggia.vndirect.com.vn/chung-khoan/vn100)
- [VNDIRECT application terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/)

## Bottom summary

- #222 is a docs-only **SOURCE-GAP CLOSURE**; the VN100 value-history chain stays empty.
- HOSE identity/methodology is authoritative but lacks a retained licensed no-login D1 history route.
- VPS/VNDIRECT UI evidence and SSI generic authenticated docs do not prove a VN100 history unit.
- Full span, response identity, point/volume/time semantics, budgets, and redistribution all remain conjunctive gaps.
- Current VN100 remains recognized-but-not-served and zero-network; v0.2.0 is not mischaracterized.
- No probe, proxy, basket, RED, code, source registration, push, or close is authorized.
- #223, #224, and #225 remain queued.
- Next step: commit this note, update the lifecycle, run merged docs gates, and request exact-SHA review.
