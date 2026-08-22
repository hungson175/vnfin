# VNFIN D1 index-history source vetting — #206

**Date:** 2026-08-23 (UTC+7)
**Requested selector:** canonical `VNFIN`
**Requested inclusive window:** `2020-05-11..2026-08-19`
**Status:** source/design gate only; no production capability is enabled by this note
**Disposition:** **SOURCE-GAP CLOSURE**

## 1. Boundary and clean-room record

This is a bounded clean-room source review, not a claim that any broker feed is the
official exchange feed. The two committed artifacts for #206 are this note and
`tasks/206-design-note.md`; no live response body, OHLCV row, raw exception, cookie,
or provider fixture is committed.

Before research, `docs/vnstock-blacklist.md` was checked. The exact exclusion set was
applied to every web search:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result or derivative material was opened, cited, compared, installed,
or used. Evidence below is limited to the named provider-owned routes and official
HOSE/provider legal pages.

The probe used one no-credential IPv4 request per history route with a bounded 35-second
transport timeout, no `Authorization` header, no login, no browser session, and no
retry. It sent the repository transport's desktop-Chrome `User-Agent` value
`Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36`;
this browser-UA dependency is a separate access/transport axis, not proof of public
automation permission. The request bounds were the existing adapter convention: local
Vietnam time `2020-05-11 00:00:00` through `2026-08-19 23:59:59`, encoded as UTC epoch
seconds `from=1589130000` and `to=1787158799`. The probe ran on 2026-08-23 and is an
observation of the response at that time, not a retention guarantee.

## 2. Official identifier boundary

HOSE annual reports identify `VNFIN` as the Financials sector index among the HOSE
sector-index family. The 2024 report lists `VNFIN` in the “Chỉ số ngành” table; the
2021 report also lists the Financials index under the same code. That establishes the
identifier only. It does **not** make the VPS, SSI, or VNDirect chart routes official,
licensed, or interchangeable with HOSE's publisher.

Primary identity references:

- [HOSE 2024 annual report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896445/B%C3%81O%20C%C3%81O%20TH%C6%AF%E1%BB%9CNG%20NI%C3%8AN%20%28ANUAL%20REPORT%29%202024.pdf)
- [HOSE 2021 annual report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1641899/Bao%20cao%20thuong%20nien%202021.pdf)

The source feeds below remain vendor data. No official/reconstructed label may be
attached to a returned `PriceHistory`.

## 3. Direct probe matrix

### 3.1 Summary

| Source adapter | History route and request selector | HTTP/effective-host observation | Response identity | Raw D1 observation | Data-quality result | Technical disposition | Legal disposition |
|---|---|---|---|---|---|---|---|
| `VPSIndexSource` / `vps_index` | `GET https://histdatafeed.vps.com.vn/tradingview/history?symbol=VNFIN&resolution=D&from=1589130000&to=1787158799` | `200`; zero redirects; effective host/path unchanged; `application/json; charset=utf-8`; no auth challenge | Bare history body echoed `symbol=VNFIN`; same-owner `/tradingview/symbols?symbol=VNFIN` also returned `symbol=ticker=name=VNFIN` | 1,603 rows; 1,569 distinct local dates; first `2020-05-11`, last `2026-08-19`; both boundaries present; 34 duplicate dates; aligned `t/o/h/l/c/v` | `v` present/aligned; positive finite OHLC rows except two invalid-order rows; conflicting same-date rows | **PARTIAL**: current parser served 1,534 bars after quarantining 68 rows and deduping one identical duplicate; it cannot claim an exact clean span | **LEGAL_GAP** |
| `SSIIndexSource` / `ssi_index` | `GET https://iboard-api.ssi.com.vn/statistics/charts/history?resolution=1D&symbol=VNFIN&from=1589130000&to=1787158799` | `200`; zero redirects; effective host/path unchanged; `application/json; charset=utf-8`; no auth challenge | History envelope has no symbol field, but same-owner `/statistics/charts/symbol?symbol=VNFIN` returned a successful `VNFIN`/HOSE/index metadata record | 1,569 rows; 1,569 distinct local dates; first `2020-05-11`, last `2026-08-19`; both boundaries present; no duplicate dates; no provider count (`nextTime=null`) | `v` present/aligned; all observed OHLC rows finite, positive, and ordered; `s=ok` and outer `code=SUCCESS,status=ok` | **QUALIFIED on observed technical axes only**; not end-to-end qualified while the legal/reuse gate is open | **LEGAL_GAP** |
| `VNDirectIndexSource` / `vndirect_index` | `GET https://dchart-api.vndirect.com.vn/dchart/history?symbol=VNFIN&resolution=D&from=1589130000&to=1787158799` | `200`; zero redirects; effective host/path unchanged; body is JSON while normalized MIME is `text/plain;charset=UTF-8`; no auth challenge; response sets a routing cookie that was not sent or retained | Bare history body has no symbol; `/dchart/symbol?symbol=VNFIN` was `404`. A bounded `VNINDEX` control returned a distinct content fingerprint, but this is not a response-backed symbol binding | 1,570 rows; 1,570 distinct local dates; first `2020-05-11`, last `2026-08-19`; both boundaries present; no duplicate dates; no provider count | `v` present/aligned; all observed OHLC rows finite, positive, and ordered; `s=ok` | **IDENTITY_GAP**; do not list as a qualified fallback | **LEGAL_GAP** |

“Technical” means only that the observed response shape/data checks passed. The
end-to-end disposition remains `SOURCE-GAP CLOSURE` because no provider supplied a
written licence or route-specific permission for automated OSS retrieval plus
caller-facing redistribution, and two candidate source seams remain unqualified.

Each row is one qualification unit: the named provider, its exact history route, and
its same-provider metadata route (or the documented absence of one). Legal permission,
selector identity, date/quality coverage, points/RAW semantics, and aligned volume must
all pass for that same unit. No VPS permission can qualify SSI rows, and no SSI metadata
or volume can repair a VPS or VNDirect history response. The route pairs are not a
cross-provider evidence matrix and cannot be mixed into one returned series.

### 3.2 Response schema, metadata, and units

The following facts are sanitized shape/metadata observations; no live prices or
volumes are recorded.

| Source | History schema | Same-owner identity metadata | Daily/point metadata |
|---|---|---|---|
| VPS | Bare object with `symbol,s,t,o,h,l,c,v` | `/tradingview/symbols?symbol=VNFIN` returned `symbol=ticker=name=VNFIN`, `timezone=Asia/Ho_Chi_Minh`, `session=0900-1500`, `has_daily=true`, `has_no_volume=false`, `pricescale=100`, `pointvalue=1`; `has_weekly_and_monthly=false`, `has_intraday=true` | Provider metadata is compatible with index points and exposes intraday too; the requested capability must therefore be D1-only in the registry |
| SSI | Outer `{code,data,message,status}`; inner `data` has `s,t,o,h,l,c,v,nextTime` and no symbol | `/statistics/charts/symbol?symbol=VNFIN` returned `code=SUCCESS,status=ok`, `symbol=ticker=name=VNFIN`, `exchange=HOSE`, `listed_exchange=HOSE`, `type=Chỉ số`, `timezone=Asia/Ho_Chi_Minh`, `session=0900-1500`, `has_daily=true`, `has_no_volume=false`, `pricescale=100`, `pointvalue=1`; `symbolRef=null` | Same point metadata and daily/intraday exposure; runtime acceptance must not infer an official exchange feed from `exchange=HOSE` |
| VNDirect | Bare object with `s,t,o,h,l,c,v`; response `Content-Type` was `text/plain;charset=UTF-8` although the body was JSON | No usable same-owner symbol route observed: `/dchart/symbol?symbol=VNFIN` returned `404`; the positive/wrong-symbol control is only a bounded diagnostic | No response-backed scale/identity metadata; do not promote the existing `PRICE_SCALE=1.0` adapter setting to source proof |

All three history responses reported `s=ok`. The raw `v` field was present, a list,
and aligned with the OHLC/time arrays in this observation. The provider metadata
`has_no_volume=false` for VPS and SSI is corroborating evidence, not a permanent
contract; a future parser must still validate the actual field on every response.

The current index adapters set `PRICE_SCALE=1.0`, `AdjustmentPolicy.RAW`, and
`value_unit=currency="points"`. The two metadata routes support that interpretation
with `pricescale=100` and `pointvalue=1`; they do not grant reuse rights. VNDirect's
response alone does not close the scale/identity gate.

### 3.3 Selector controls

The request parameter is never treated as identity by itself.

- VPS has two independent positive controls: the history body echoes `symbol=VNFIN`,
  and the same-owner metadata route echoes `symbol=ticker=name=VNFIN`.
- SSI history omits a symbol, but the same-owner metadata route returns a successful
  `VNFIN` index/HOSE record. The runtime design must retain the route pairing as an
  explicit identity contract; if an implementation cannot bind the history body to
  that contract, SSI must be downgraded rather than stamped as `VNFIN`.
- VNDirect history omits a symbol and its metadata route is absent. The bounded
  `VNFIN` versus `VNINDEX` control changed the returned content fingerprint while
  preserving the same bare-UDF shape and date boundary. The fingerprint was computed
  only as `sha256(canonical_json(t,o,h,l,c,v))[:16]` and the live payload was not
  stored. The two control fingerprints were distinct on each provider (including
  VNDirect); the digest values are deliberately not committed because a short
  live-payload digest is not useful public provenance and resembles a credential
  blob to repository secret scans. These fingerprints distinguish the bounded
  control responses but do not prove response-backed selector identity, so VNDirect
  remains `IDENTITY_GAP`.

The same controls are not official-index proof and not a licence. They are only
source-response diagnostics.

### 3.4 Date, resolution, and coverage observations

The literal `2020-05-11..2026-08-19` result is a fixed qualification observation,
not a promise that every arbitrary caller range has those literal endpoints. A runtime
caller may request a weekend/holiday boundary, while the existing stitched helper may
request calendar-year segments beginning January 1 and ending December 31. Those
non-trading boundary dates need not occur in a source response. A future implementation
must choose and document an official trading calendar plus its supported horizon before
turning arbitrary-range coverage into a hard acceptance predicate: it must compare the
first/last expected trading day and internal expected dates, and report an honest
calendar-horizon/partial diagnostic outside that contract. Until that separate design
exists, this note makes no arbitrary-range coverage claim and retains the empty chain.
The future TDD matrix must cover weekend and holiday boundaries, the calendar horizon,
and each stitched year seam without filling or hiding a gap.

The adapter converts provider epoch timestamps to `Asia/Ho_Chi_Minh` dates. The
observed endpoint rows had no weekend dates. No date was labeled a verified exchange
closure in this probe because no official holiday/calendar file was used to classify
the two cross-provider differences below.

| Comparison | Date-set result |
|---|---|
| SSI minus VNDirect | empty |
| VNDirect minus SSI | `2025-05-05` |
| SSI minus raw-VPS unique dates | `2021-06-28` |
| raw-VPS unique dates minus SSI | `2025-05-05` |
| VNDirect minus raw-VPS unique dates | `2021-06-28` |
| raw-VPS unique dates minus VNDirect | empty |

Thus `2025-05-05` and `2021-06-28` are recorded as unexplained provider date
differences, not silently filled and not asserted to be holidays. The two cleanest
observed candidates both include the requested boundaries, but their internal date
sets are not identical. A future exact-coverage claim must either prove the missing
date against an official trading calendar/provider correction or disclose it as a
source gap; it must not assume that cross-provider agreement supplies the calendar.

VPS has a separate daily-row problem. Its 34 duplicate local dates were:

```text
2020-12-25,
2025-05-13, 2025-05-14, 2025-05-15, 2025-05-16, 2025-05-19, 2025-05-20,
2025-05-21, 2025-05-22, 2025-05-23, 2025-05-26, 2025-05-27, 2025-05-28,
2025-05-29, 2025-05-30, 2025-06-02, 2025-06-03, 2025-06-04, 2025-06-05,
2025-06-06, 2025-06-09, 2025-06-10, 2025-06-11, 2025-06-12, 2025-06-13,
2025-06-16, 2025-06-17, 2025-06-18, 2025-06-19, 2025-06-20, 2025-06-23,
2025-06-24, 2025-06-25, 2025-06-26
```

One duplicate date was identical and was deduped. The other 33 dates were conflicting
same-date rows. Two additional rows failed the OHLC ordering invariant on
`2020-08-13` and `2021-07-14`. The current parser therefore returned 1,534 bars,
quarantined 68 rows, and emitted both `quarantined_invalid_bars` and
`deduped_duplicate_daily_index_bars`. This is an honest diagnostic, but it is not the
requested exact clean single-source coverage. No date is forward-filled, backfilled,
interpolated, or reconstructed.

No provider-declared total count was present. SSI returned `nextTime=null`; VPS and
VNDirect exposed no count/total field in the observed payload. Counts in this note
are array-row observations only.

## 4. Vendor, runtime, and legal posture

### 4.1 Route ownership and access

The route hosts are subdomains of the named broker/vendor domains. All three history
requests were reachable without credentials and without a login/session cookie in
the request. They used the repository's desktop-Chrome `User-Agent` because the
provider routes may reject an ordinary client; that browser-UA presentation is not
evidence of public automation permission and remains part of the provider/legal gap.
SSI and VNDirect emitted response cookies; the client must not retain or reuse them as
authentication. No `Authorization` header, API key, login, browser automation,
challenge-solving, proxy bypass, private route, or cookie/session reuse was used. The
absence of those mechanisms does not establish that the browser UA is not an access
control; it only records what this bounded probe did.

Observed response headers did not expose a rate-limit budget on these chart routes.
That is **unknown**, not unlimited. The official [SSI developer environment and
limits page](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
documents API-key rate limits and HTTP 429 behavior for its supported API product;
that page does not grant the unauthenticated chart route a quota or redistribution
right. Future runtime work must use a deterministic sequential budget, no hidden
parallel calls, and no retry loop outside the approved attempt budget.

### 4.2 Terms and permission findings

| Vendor | Primary terms/contact evidence | Conservative conclusion |
|---|---|---|
| VPS | [VPS terms](https://vps.com.vn/dieu-khoan-su-dung) state that website products/content are owned by VPS and prohibit copying, transfer, display, distribution, storage, or derivative versions without official written consent; personal download/print is separately described. Contact path: [VPS company page](https://vps.com.vn/ve-chung-toi), `hotrokhachhang@vps.com.vn`, hotline `1900 6457`. | No public permission for an OSS runtime API to return or redistribute chart rows. `LEGAL_GAP`; request written data/API permission. |
| SSI | [SSI service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu) permit personal viewing/analysis/reformatting/printing and prohibit publishing, broadcasting, or reproducing the information to third parties without written SSI consent. Contact path: [SSI network/contact page](https://www.ssi.com.vn/mang-luoi). | The public no-auth response is not a redistribution licence. `LEGAL_GAP`; request written permission covering automated retrieval and caller-facing use. |
| VNDirect | [VNDirect online-application terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) identify the website information/service as VNDIRECT-provided, disclaim accuracy/availability, and state that copyright belongs to VNDIRECT; no route-specific open-data/API redistribution grant was found. Contact path: [VNDIRECT support](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/), `support@vndirect.com.vn`, hotline `1900 5454 09`. | No affirmative automated-use, caching, or redistribution permission. `LEGAL_GAP` (and independently `IDENTITY_GAP`). |

The runtime-safe posture, pending written permission, is **no capability**: no bundled
rows, no cache, no archival snapshot, no bulk export, no public examples containing
live values, and no claim that a no-auth route is lawful to redistribute. A source may
be used for a future implementation only after its permission scope is explicit.

## 5. Proposed API/contract boundary (not implemented)

The existing public call remains the only requested entry point:

```python
index_history("VNFIN", date(2020, 5, 11), date(2026, 8, 19), Interval.D1)
```

No `index_history_stitched` substitution, per-date source merge, forward-fill,
backfill, interpolation, or signal helper is authorized. A successful future result
would have exactly one producing source, `symbol="VNFIN"`, the exact provider symbol,
`Interval.D1`, `AdjustmentPolicy.RAW`, `value_unit=currency="points"`, VN-local
timezone-aware bars, and ordered source attempts. It would carry vendor provenance,
not an official/reconstructed label. The explicit stitched wrapper remains a separate
compatibility path with its existing multi-source provenance grammar; the strict
VNFIN bare-token grammar below must not erase or silently rewrite those warnings.

The private registry and source-capability design is deliberately narrow:

1. Add `VNFIN` to `_VALUE_HISTORY_INDICES` exactly once. It remains in the stock-price
   deny-list through `_KNOWN_INDEX_IDENTIFIERS`; no other deny-only identifier changes.
2. Define a private **request capability** predicate over normalized
   `(symbol, interval)`. `VNFIN` is request-capable only for `Interval.D1`; every
   `M1/M5/M15/M30/H1/W1/MN1/Q1/Y1` request is rejected before `apply_interval` and
   before network. A daily alias that resolves to `Interval.D1` follows the same rule.
   Headline-index interval/resampling behavior is unchanged.
3. Define a separate private **per-source capability** predicate over
   `(source_role, symbol, interval)`. It runs after request capability and before
   transport for both the default chain and every injected source chain. The source
   role must declare the exact VNFIN D1 history/metadata route pair it can enforce;
   an incapable role is skipped, consumes no `max_attempts` slot, makes zero physical
   calls, and creates no `SourceAttempt`. A source becoming request-capable must not
   imply that every source role is capable.
4. Lowercase/padded `vnfin` normalizes to `VNFIN`. Malformed selectors/intervals fail
   typed and zero-network. `index_history_stitched("VNFIN", ..., Interval.D1)` may
   become reachable only through its existing D1-only opt-in; it never replaces the
   strict call.
5. An SSI adapter attempt is one bounded route-pair operation with this exact order:
   first `GET /statistics/charts/symbol?symbol=VNFIN`, then, only if that response is
   successful and matches `code=SUCCESS`, `status=ok`, `symbol=ticker=name=VNFIN`,
   `exchange=listed_exchange=HOSE`, `type=Chỉ số`, `timezone=Asia/Ho_Chi_Minh`,
   `has_daily=true`, and `has_no_volume=false`, one
   `GET /statistics/charts/history?resolution=1D&symbol=VNFIN&from=...&to=...`.
   The history must then pass the same identity, coverage, points/RAW, and volume
   validator. Metadata transport/HTTP/schema/identity failure records one failed SSI
   adapter attempt and makes no history call; history transport/HTTP/schema/quality
   failure records that attempt as failed. The pair has at most two physical
   calls, no retry, no hidden parallel call, and no cookie/session retention or reuse.
   Injected HTTP stubs count each route invocation as one physical call while retaining
   their existing string-returning arity.
6. The future default chain is a strict whole-window failover. A source either
   returns the complete accepted single-source result or records one bounded failed
   adapter attempt and the next capable source receives the same requested range. No
   result is assembled from multiple sources. `max_attempts` counts adapter attempts,
   not SSI's metadata/history subrequests; the SSI route-pair physical budget is
   separately capped at two calls for its one adapter attempt. Tests must prove that
   default and injected incapable sources make zero calls, consume no attempt, and
   fabricate no attempt record.
7. Missing/null `v` is `InvalidData` for this VNFIN path and triggers honest failover.
   Before the shared parser can erase field presence, raw `v` must be a non-string
   `list` or `tuple` whose length exactly equals `len(t)` and every element must be a
   finite, non-negative `int` that is not `bool`. Missing, null, wrong type, wrong
   length, bool, fractional/float, negative, non-finite, or malformed values fail the
   entire source attempt; they are not quarantined and cannot publish a shortened
   series. A genuinely present provider integer zero remains `0`. The current shared
   absent/null-to-zero shortcut must not be reused for VNFIN.

Public diagnostics are mechanically bounded, with separate contracts for the strict
adapter/failover path and the pre-existing explicit stitched wrapper. On the strict
path, `SourceAttempt.reason` and each strict `PriceHistory.warnings` entry must be an
ASCII token matching `^[a-z][a-z0-9_]{0,31}$` (maximum 32 characters) from the exact
allow-list `ok`, `transport_error`, `invalid_data`, `empty_data`, `identity_mismatch`,
`metadata_mismatch`, `coverage_gap`, `coverage_partial`, `calendar_horizon`,
`volume_missing`, `volume_invalid`, `duplicate_conflict`, `unsupported_source`,
`budget_exhausted`, `body_invalid`, `conflicts_many`, `gaps_many`,
`source_failures_many`, and `diagnostics_truncated`. No colon suffix, URL, query
string, body, cookie, credential, raw exception, date sample, or provider/source free
text is permitted. Public strict `SourceAttempt.name` is one of the finite role tokens
`vps_index`, `ssi_index`, `vndirect_index`, or `custom`; an oversized injected name
maps to `custom`, and that same token is used for `PriceHistory.source` after
provenance validation. The strict final producer source is never a raw injected name.

The explicit `index_history_stitched()` compatibility path is not silently forced into
the bare-token grammar. It preserves exactly `stitched_multi_source`, plus one segment
warning per calendar segment matching
`^stitched_segment: [0-9]{4} (vps_index|ssi_index|vndirect_index|custom) \((0|[1-9][0-9]{0,5}|many) bars\)$`.
The year is the segment year, the role is the canonical producer token, and the bar
count is decimal through `999999` or `many`; raw source names, URLs, exception/body
text, cookies, credentials, and other prose are rejected. Its final
`PriceHistory.source` is exactly `stitched_index_history`. Future VNFIN stitched use
is capped at 128 calendar segments and fails before publishing if that cap is exceeded;
it never drops segment provenance or substitutes a truncation warning. The existing
non-VNFIN stitched API is not changed by this packet.

The scheduler has a real attempt ceiling independent of warning truncation:
`effective_attempt_limit = min(max_attempts, 8)`. It makes at most eight actual capable
adapter calls, and every exposed `SourceAttempt` is one actual call with a canonical
role and complete token reason. Skipped or unattempted sources never produce a record.
If the limit is reached while capable sources remain, an accepted result may receive
one `diagnostics_truncated` warning token only; it is never a `SourceAttempt`, does not
consume `max_attempts`, and never enters `AllSourcesFailed.attempts`. Keep the
deterministic first 15 strict warnings and append the sentinel as the 16th when warning
or attempt scheduling truncation occurs. `max_attempts > 8` therefore still makes at
most eight calls, and nine capable injected sources must expose at most eight real
attempts. RED tests must cover those cases, canonical producer identity, oversized
source text, and large conflict/gap sets with complete URL/exception/body/cookie/
credential sanitization.

## 6. Reopen and review decision

This evidence is sufficient to show that `VNFIN` is a real HOSE sector-index
identifier and that VPS/SSI expose technically plausible D1 routes over the requested
boundaries. It is **not** sufficient to authorize production code or a public support
claim because:

- no named vendor grants the required automated OSS/caller-facing reuse rights;
- VPS has material duplicate/conflicting rows and quarantined dates;
- SSI's history body lacks a selector echo and relies on the same-owner metadata
  pairing; and
- VNDirect has no response-backed identity metadata and remains unqualified.

Reopen the design only when all of the following are conjunctively satisfied for one
named provider `P` and its exact history/metadata route pair. A permission from VPS
cannot be combined with SSI identity, SSI coverage, or VNDirect volume; there is one
source winner, not a cross-provider qualification matrix:

1. `P` gives written permission or an explicit licence covering the exact route pair,
   automated retrieval, OSS distribution, caller-facing return, caching/storage policy,
   attribution, rate limits, and any commercial/use restrictions.
2. That same `P` route pair has runtime-verifiable selector identity (history echo or
   a documented same-owner metadata binding) and a stable daily points/RAW contract.
3. For the fixed reviewed observation, that same `P` returns both literal issue
   boundaries with no unexplained internal gap, duplicate/conflicting date, or invalid
   OHLC row; any exchange closure is proved by an official calendar rather than
   inferred from another vendor. This fixed-window result does not by itself qualify
   arbitrary caller ranges or stitched calendar-year segments.
4. For the separately specified runtime range contract, that same `P` has a reviewed
   calendar and supported horizon, or the future design explicitly retains partial/
   calendar-horizon diagnostics instead of claiming hard absence. Weekend/holiday
   boundaries and stitched year seams must be tested without requiring non-trading
   literal endpoints or fabricating bars.
5. That same `P` route pair returns an aligned non-null `v` array of exact length whose
   raw elements are finite non-negative integers excluding bool; any violation fails
   the entire adapter attempt, while a present integer zero remains zero. Missing or
   null volume never becomes a published zero or a shortened result.
6. The request and per-source capability guards, strict whole-window failover, SSI
   at-most-two physical-call budget, exact adapter-attempt budget, warning/attempt token caps,
   public snapshots, offline synthetic tests, docs, and build gates pass on the merged
   tree. Capability skips must be zero-call and absent from `SourceAttempt` records.

Until those gates are met, the current chain remains empty for `VNFIN`, no production
code is authorized, and this issue should be resolved only as a documented source gap.
