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
retry. The request bounds were the existing adapter convention: local Vietnam time
`2020-05-11 00:00:00` through `2026-08-19 23:59:59`, encoded as UTC epoch seconds
`from=1589130000` and `to=1787158799`. The probe ran on 2026-08-23 and is an observation
of the response at that time, not a retention guarantee.

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
  stored. The probe prefixes were `cd0c79bef8d60a85` (VNFIN) versus
  `3b044cecefe4a5c3` (VNINDEX). For comparison, the same control produced
  `e476d9ee85c6485d` versus `cc6528f9b2b99ba1` on VPS and
  `666bb182267b6e87` versus `63d744f93e742c03` on SSI. These fingerprints
  distinguish the bounded control responses but do not prove response-backed
  selector identity, so VNDirect remains `IDENTITY_GAP`.

The same controls are not official-index proof and not a licence. They are only
source-response diagnostics.

### 3.4 Date, resolution, and coverage observations

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
the request. SSI and VNDirect emitted response cookies; the client must not retain or
reuse them as authentication. No `Authorization` header, API key, anti-bot bypass,
private route, or browser automation was used.

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
not an official/reconstructed label.

The private registry design is deliberately narrow:

1. Add `VNFIN` to `_VALUE_HISTORY_INDICES` exactly once. It remains in the stock-price
   deny-list through `_KNOWN_INDEX_IDENTIFIERS`; no other deny-only identifier changes.
2. Add a private symbol-plus-interval predicate. `VNFIN` is capable only for
   `Interval.D1`; every `M1/M5/M15/M30/H1/W1/MN1/Q1/Y1` request is rejected before
   `apply_interval` and before network. A daily alias that resolves to `Interval.D1`
   follows the same rule. Headline-index interval/resampling behavior is unchanged.
3. Lowercase/padded `vnfin` normalizes to `VNFIN`. Malformed selectors/intervals fail
   typed and zero-network. `index_history_stitched("VNFIN", ..., Interval.D1)` may
   become reachable only through its existing D1-only opt-in; it never replaces the
   strict call.
4. The future default chain is a strict whole-window failover. A source either
   returns the complete accepted single-source result or records one bounded failed
   attempt and the next capable source receives the same requested range. No result
   is assembled from multiple sources. `max_attempts` counts actual source calls; an
   incapable source is skipped and contributes no fabricated attempt.
5. Missing/null `v` is `InvalidData` for this VNFIN path and triggers honest failover.
   A present provider integer zero remains `0`. The current shared parser's
   absent/null-to-zero shortcut must not be reused for VNFIN; the future TDD change
   needs a local raw-field-presence check without making other price/index behavior
   silently change.

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

Reopen the design only when all of the following are conjunctively satisfied:

1. A written VPS/SSI/VNDirect permission or an explicit licence covers automated
   retrieval, OSS distribution, caller-facing return, caching/storage policy,
   attribution, rate limits, and any commercial/use restrictions.
2. At least one source has runtime-verifiable selector identity (history echo or a
   documented same-owner metadata binding) and a stable daily points/RAW contract.
3. One source returns both requested boundaries with no unexplained internal gap,
   duplicate/conflicting date, or invalid OHLC row; any exchange closure is proved by
   an official calendar rather than inferred from another vendor.
4. The source response contains an aligned non-null `v` array. Missing/null volume
   fails closed; zero is preserved as zero.
5. The registry guard, strict whole-window failover, exact attempt budget, warning
   sanitization, public snapshots, offline synthetic tests, docs, and build gates
   pass on the merged tree.

Until those gates are met, the current chain remains empty for `VNFIN`, no production
code is authorized, and this issue should be resolved only as a documented source gap.
