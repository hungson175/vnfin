# VNREAL D1 sector-index history source vetting — #213

**Date:** 2026-08-23 (UTC+7)
**Phase:** source/design gate only; no runtime capability is enabled by this report
**Requested selector:** canonical `VNREAL`
**Requested inclusive window:** `2018-01-01..2026-08-19` (Vietnam local dates)
**Disposition:** **SOURCE-GAP CLOSURE**
**Capability status:** the new VNREAL source chain remains empty; no TDD, production code,
cache, archive, bundled data, or public foreign/source claim is authorized.

## 1. Boundary, method, and clean-room record

This is a fresh, provider-by-provider review of the Real Estate sector-index value
history. It is not a claim that a broker chart route is the official exchange feed, and
it does not turn a no-login observation into a licence to automate, cache, or redistribute
rows.

Before this research, `docs/vnstock-blacklist.md` was read. The exact exclusion applied to
every search was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result or derivative material was opened, cited, compared, installed, or
used. The evidence below is limited to provider-owned VPS, SSI, and VNDirect routes,
official HOSE material, official provider terms/contact pages, the public UDF protocol,
and the repository's current clean-room adapter boundary. The prior VNFIN review is
methodology context only; its data, identity, or permission conclusions are not reused
for VNREAL.

The bounded observation was run on 2026-08-23 using direct HTTPS GETs, a sequential
no-login client, no `Authorization` header, no credential, no proxy, no browser
automation, no challenge-solving, and no cookie/session reuse. The client used this
browser-like User-Agent because the routes were observed with it:

```text
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36
```

That User-Agent dependency is a transport/access risk, not evidence of public
automation permission. Provider `Set-Cookie` headers observed during the round were not
retained or sent on another request. Temporary response bodies were discarded after
sanitized shape, identity, date, and quality checks. No raw payload, live bar/value,
query-bearing URL, cookie, token, screenshot, short/live content digest, or provider
dataset is committed here.

### Current tree and annotated release boundary

The current review tree is `master` at `5ad0ad6ae6a19d9827a61e354177b3ae91bac9fc`.
In this tree, `VNREAL` is present in the private `_KNOWN_INDEX_IDENTIFIERS` deny set but
absent from `_VALUE_HISTORY_INDICES`. Therefore the price namespace still rejects it as
an index, while both `index_history("VNREAL", ...)` and
`index_history_stitched("VNREAL", ...)` fail with the shared typed terminal diagnostic
before network access. This report does not change that boundary.

The annotated `v0.2.0` release boundary is the exact tag
`2fe50df4f27064140ff9f7a680227a2b337ec74a`. That historical tag predates the current
private `vnfin/_contracts/index_registry.py` path, so it is not evidence of current
VNREAL registry behavior or of a capability. The tag is recorded to prevent mixing
release-era behavior with current-master behavior; all qualification claims in this
report are about the current provider observations and current tree boundary.

## 2. Official identifier evidence

Official HOSE annual reports list `VNREAL` within the exchange's sector-index family.
That establishes the exchange namespace/sector meaning only. It does not bind any
broker route to HOSE, prove a complete historical archive, or grant permission to
return provider rows from an OSS API.

- [HOSE 2024 annual report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896445/B%C3%81O%20C%C3%81O%20TH%C6%AF%E1%BB%9CNG%20NI%C3%82N%20%28ANUAL%20REPORT%29%202024.pdf)
- [HOSE 2023 annual report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896430/B%C3%A1o%20c%C3%A1o%20th%C6%B0%E1%BB%9Dng%20ni%C3%AAn%202023.pdf)
- [HOSE contact page](https://www1.hsx.vn/vi/lien-he)

The official material is an identifier reference, not a source-selection oracle. No
constituent basket, equity proxy, ETF, screenshot, search snippet, or cross-provider
numeric agreement is used as VNREAL identity.

## 3. Observation ledger and route contract

### 3.1 Exact bounded accounting

There were two sequential observation passes over the same six route cells:

| Quantity | Exact observation |
|---|---:|
| Providers | 3 (`VPS`, `SSI`, `VNDirect`) |
| Requested symbols | 1 (`VNREAL`) |
| Route cells per pass | 6 (history + same-owner identity per provider) |
| Passes | 2 |
| Logical observations | 24 |
| Physical HTTP dispatches | 24 |
| Automatic retries | 0 |
| Redirects followed | 0; effective host/path stayed unchanged for observed routes |
| Cookies retained/reused | 0 |
| Parallel requests | 0 |

In this ledger, one **logical observation** is one named provider route cell for the
requested symbol and window; one **physical dispatch** is one HTTP request. The two
counts are equal because there was no retry, redirect, or hidden identity request. The
ledger is an observation bound, not a runtime quota or a claim that a provider permits
this volume.

The non-secret request contract was provider route + `symbol=VNREAL` + provider D1 token
and local-window `from`/`to` epoch parameters. The exact D1 tokens observed were `D` for
VPS and VNDirect, and `1D` for SSI. No query string is reproduced in this repository.

### 3.2 Provider route and transport matrix

Every row below is a single qualification unit: one provider's history route, its
same-owner identity route, one symbol namespace, and one evidence/legal contract. A
different provider cannot repair a missing axis in that unit.

| Provider / owner | Canonical route pair | D1 token; envelope | Full observed Content-Type → normalized media type | Redirect/auth/WAF/session observation | Rate/retry/cache/legal posture |
|---|---|---|---|---|---|
| VPS / VPS Securities | History [`/tradingview/history`](https://histdatafeed.vps.com.vn/tradingview/history); identity [`/tradingview/symbols`](https://histdatafeed.vps.com.vn/tradingview/symbols) | `D`; bare UDF object | History and identity: `application/json; charset=utf-8` → `application/json` | HTTP 200 on both; no redirect; no auth challenge; no WAF/interstitial observed; metadata reports `session=0900-1500`; browser-like UA required by this observation | No route-specific quota or retry grant established; observation used zero retry; no cache/storage used; [VPS terms](https://vps.com.vn/dieu-khoan-su-dung) do not provide affirmative OSS caller-facing redistribution permission; **LEGAL_GAP + RATE_POLICY_GAP** |
| SSI / SSI Securities Corporation | History [`/statistics/charts/history`](https://iboard-api.ssi.com.vn/statistics/charts/history); identity [`/statistics/charts/symbol`](https://iboard-api.ssi.com.vn/statistics/charts/symbol) | `1D`; `{code,data,message,status}` envelope with UDF data inside | History and identity: `application/json; charset=utf-8` → `application/json` | HTTP 200 on both; no redirect; no auth challenge; no WAF/interstitial observed; identity response proves timezone but does not close a stable session contract; `Set-Cookie` observed and discarded; browser-like UA dependency remains | No route-specific quota or permitted retry policy established; observation used zero retry; no cache/storage used; [SSI service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu) do not provide anonymous chart-row redistribution permission; keyed [SSI developer terms](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments) are not a grant for this route; **LEGAL_GAP + RATE_POLICY_GAP** |
| VNDirect / VNDIRECT Securities | History [`/dchart/history`](https://dchart-api.vndirect.com.vn/dchart/history); identity [`/dchart/symbol`](https://dchart-api.vndirect.com.vn/dchart/symbol) | `D`; bare UDF object | History: `text/plain;charset=UTF-8` → `text/plain`; identity failure: `application/json` → `application/json` | History HTTP 200, identity HTTP 404; no redirect; no auth challenge or WAF/interstitial observed; no same-owner session metadata; browser-like UA dependency remains | No route-specific quota or permitted retry policy established; observation used zero retry; no cache/storage used; [VNDIRECT terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) provide no affirmative route-specific OSS automation/caching/redistribution grant; [VNDIRECT support](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/) is the contact path for written permission; **LEGAL_GAP + RATE_POLICY_GAP** |

The full Content-Type is part of the evidence. A future parser must compare the complete
value after the first header colon, normalize only the media type, and fail closed on an
unexpected parameter/value; it must not accept a generic maintenance HTML response as a
valid chart response. In this observation no redirect was followed and no WAF verdict can
be inferred from a successful browser-UA request. HTTP reachability is not legal,
redistribution, or automation permission.

### 3.3 Response identity and daily semantics

| Provider | Requested selector and response-backed identity | Daily point/volume/time observations | Identity/semantic gaps |
|---|---|---|---|
| VPS | History body included `symbol=VNREAL`; same-owner metadata returned `symbol=ticker=name=VNREAL`, `timezone=Asia/Ho_Chi_Minh`, `session=0900-1500`, `has_daily=true`, `has_no_volume=false`, `pricescale=100`, `pointvalue=1` | History exposed aligned `s,t,o,h,l,c,v` arrays; observed volumes were present, non-null, non-negative, and finite; timestamps mapped to Vietnam-local dates; the metadata is consistent with index points | Same-owner metadata does not document a historical date calendar, timestamp open/close convention, RAW adjustment rule, page/total/cursor semantics, or reuse rights. Conflicting duplicate dates prevent a clean fixed-window result |
| SSI | History envelope had no symbol field. Same-owner identity response returned `symbol=ticker=name=VNREAL`, `exchange=HOSE`, `listed_exchange=HOSE`, `type=Chỉ số`, `timezone=Asia/Ho_Chi_Minh`, `has_daily=true`, `has_no_volume=false`, `pricescale=100`, `pointvalue=1`, and success status | Inner UDF data exposed aligned `s,t,o,h,l,c,v` arrays; observed volumes were present, non-null, non-negative, and finite; timestamps mapped to Vietnam-local dates; `s=ok`, outer `code=SUCCESS`, `status=ok` | The identity-to-history binding is a design contract, not a symbol echo in the history body. `nextTime=null` is not a total-count proof. Session/open-close, RAW adjustment, calendar, pagination, and reuse rights remain unproven |
| VNDirect | History body had no symbol. Same-owner identity route returned HTTP 404 with no usable VNREAL metadata | Bare UDF data exposed aligned `s,t,o,h,l,c,v` arrays; observed volumes were present, non-null, non-negative, and finite; timestamps mapped to Vietnam-local dates; `s=ok`; body MIME remained `text/plain;charset=UTF-8` | No response-backed symbol, exchange/index type, scale/pointvalue, timezone/session, D1 identity, or adjustment proof. A symbol-shaped request alone is not identity |

The data checks are shape observations, not a clean qualification. The desired future
contract is exactly one normalized daily point per served exchange session, finite positive
OHLC values with `low <= open/close <= high`, aligned volume, `value_unit="points"`,
`currency="points"`, and explicit `AdjustmentPolicy.RAW`. None of the three routes
published a complete provider-side statement covering all of those semantics. In
particular, the existing adapter's point/RAW settings are repository design defaults, not
provider legal or historical-adjustment proof.

No provider-declared total, page count, cursor, or window-cap field was observed. SSI's
`nextTime=null` means only that this response did not advertise another cursor; it does
not prove complete history. No missing/internal-date claim is made without an official
exchange trading calendar. A duplicate date is not silently accepted as a second daily
point.

## 4. VNREAL fixed-window coverage

The request was inclusive of the literal local dates `2018-01-01` and `2026-08-19`.
The first date is a boundary observation, not an assertion that a Sunday/holiday must
have a bar. Because no provider supplied a route-specific exchange-calendar contract,
an absent literal boundary is recorded as **unproven**, not as proof that history starts
there or that the source lacks older data.

| Provider | Raw rows | Distinct local dates | Duplicate dates | First observed local date | Last observed local date | Start/end boundary | Fixed-window decision |
|---|---:|---:|---:|---|---|---|---|
| VPS | 1,649 | 1,615 | 34 (33 conflicting, 1 identical) | `2020-03-03` | `2026-08-19` | start absent; end present | **PARTIAL + COVERAGE_GAP**; the requested 2018 span is not served and conflicting dates are not a clean series |
| SSI | 2,148 | 2,147 | 1 identical | `2018-01-02` | `2026-08-19` | start absent; end present | **PARTIAL + COVERAGE_GAP** pending official calendar/boundary and duplicate contract; not an end-to-end winner |
| VNDirect | 2,152 | 2,152 | 0 observed | `2018-01-02` | `2026-08-19` | start absent; end present | **PARTIAL + COVERAGE_GAP + IDENTITY_GAP**; a complete-looking row count cannot repair the missing same-owner identity |

The observations are exact for this bounded request and time, not a provider retention
guarantee. The VPS result is recent-only relative to the requested start. SSI and
VNDirect reach the day after the requested literal start, but no official calendar or
base-date evidence makes that a qualified full-span claim. No provider exposes enough
pagination/total information to distinguish a complete fixed window from a server-side
cap. These are `PAGINATION_GAP` diagnostics, not claims of absence.

### Fixed window versus stitched window

**Fixed window** means one provider qualification unit returns one validated series for
the entire requested range. It cannot be created by taking SSI identity, VPS volume, and
VNDirect dates, and it cannot be inferred from the first and last observed dates.

**Stitched window** is a separate, explicit future operation. The existing
`index_history_stitched()` shape is D1-only and divides `2018..2026` into nine calendar
year segments, validates `D1`/points/RAW/canonical symbol, rejects conflicting seams,
deduplicates only identical seam bars, and labels the wrapper
`source="stitched_index_history"`. It must not be used by strict
`index_history()` and must not be enabled for VNREAL until a strict source unit first
passes all gates. A stitched series is not evidence that any one provider covers the
full span and is not a workaround for missing legal permission.

## 5. Future global-budget and API contract (design-only)

This section is a bounded design contract for a later, separately approved capability.
It is not a runtime promise and does not authorize RED tests or production code now.

### Strict request

If a provider later qualifies, the future strict path may retain the current
VPS → SSI → VNDirect order, but only for a source role that is capable of the exact
VNREAL/D1 history-plus-identity unit. The public capability guard must:

1. accept only canonical `VNREAL` and exact `Interval.D1` after typed selector/range
   validation; malformed, proxy, non-D1, and wrong-namespace requests fail before
   network;
2. keep `VNREAL` in the price-path deny set and add it to the value-history allow set
   only after a design PASS; no other deny-only index changes;
3. require response-backed identity from the same provider, not a request echo alone;
4. return one provider's complete validated `PriceHistory` with
   `value_unit=currency="points"`, `AdjustmentPolicy.RAW`, canonical source role, and
   timezone-aware retrieval metadata; and
5. fail the whole source attempt on missing/null/unproven volume, invalid OHLC, a
   duplicate/conflicting date, an unbound symbol, wrong MIME/envelope/status, or an
   unproven fixed-window boundary. Never synthesize volume zero and never return an
   unlabelled partial.

No strict request may substitute `VNFIN`, another sector, a constituent basket, an
equity/ETF proxy, or another provider's bars. A source skip is not a source attempt and
must not consume an attempt slot or fabricate provenance.

### Exact request-scoped budget

The future VNREAL contract uses one atomic ledger for the entire public call:

| Ledger item | Future design value |
|---|---:|
| Maximum logical source attempts, strict | 3 total (`max_attempts` is bounded to 1–3; greater values fail typed before network) |
| Physical dispatches per logical attempt | at most 2: one same-owner identity dispatch plus one history dispatch |
| Automatic retries | 0 by default; a retry cannot appear without a new rate/legal design review |
| Strict maximum logical/physical | `3 / 6` |
| Stitched calendar segments | 9 (`2018` through `2026`, inclusive) |
| Stitched maximum logical/physical | `27 / 54` across the whole public call |

An identity failure may stop before history, so actual physical use can be lower; the
bound is deterministic and never exceeded. Each identity, history, or future retry
dispatch reserves from the same request ledger **before** dispatch. Reservations are
atomic: an exhausted reservation does not send the request, does not add a fake
`SourceAttempt`, and raises/records a typed `BudgetGlobalExhausted` outcome while
preserving all prior sanitized attempts. Stitched segments cannot reset the counter,
run concurrently, or multiply the cap. No hidden page loop, redirect loop, retry storm,
or per-segment `max_attempts` is permitted.

The logical/physical distinction is public diagnostic design only: a logical attempt is
one `(provider, symbol, interval, segment)` qualification evaluation; physical count is
the number of actual HTTP dispatches. A capability skip is neither. Any later change to
identity ordering, provider retries, pagination, or rate policy must revise the formula
and its tests before implementation.

### Future stitched atomicity and provenance

After strict qualification, stitched mode may issue at most the nine segment calls under
the same `27 / 54` ledger. Every segment must pass the absolute D1/points/RAW/canonical
symbol checks. Identical seam bars may be deduplicated; conflicting seam bars are fatal.
If any segment is missing, unqualified, budget-exhausted, or unreconciled, return no
partial `PriceHistory`. The result must carry `source="stitched_index_history"` and a
finite `stitched_multi_source` warning plus bounded per-segment role/year/bar-count
provenance. It must not expose URLs, query strings, bodies, cursors, cookies, provider
exception text, live values, or fabricated single-source identity.

## 6. No-false-absence diagnostic contract

An empty/failed/recent-only response is a bounded outcome, not proof that VNREAL history
does not exist. The future diagnostic model must separate these axes:

- `IDENTITY_GAP`: response does not bind the requested `VNREAL` to same-provider index
  metadata;
- `COVERAGE_GAP`: observed range does not prove the requested fixed window, including a
  literal boundary without a documented non-trading-calendar explanation;
- `TIMESTAMP_GAP`: timestamps parse but session open/close/timezone/date convention is
  not proved;
- `VOLUME_GAP`: volume is missing, null, misaligned, non-finite, or its unit/meaning is
  unproven;
- `PAGINATION_GAP`: no provider total/page/cursor/window-cap reconciliation exists;
- `LEGAL_GAP`: no written automated OSS/caller-facing/cache/redistribution permission;
- `RATE_POLICY_GAP`: no route-specific rate, retry, and cache policy;
- `TRANSPORT_INCONCLUSIVE`: HTTP/MIME/envelope/redirect/WAF behavior is not sufficient
  to classify the source.

`NO_DATA_OBSERVED` may be emitted only when a valid identity-bound response explicitly
reports no data for the requested window. It must not be inferred from an identity 404,
an empty unbound body, a timeout, a recent-only result, a server cap, or one missing
calendar date. The aggregate result for this batch is `SOURCE-GAP CLOSURE`, not an
assertion of `VNREAL` absence.

The future public attempt record must use only canonical provider roles
`vps_index`, `ssi_index`, and `vndirect_index`, a finite enum outcome, bounded physical
call count, and sanitized axis tokens. It must preserve earlier attempts when a later
source exhausts the global ledger. A budget exhaustion is a typed outcome, not a
synthetic empty attempt. Warning and attempt tuples must be finite and deterministic;
raw provider text, URLs, query strings, cookies, headers, exception reprs, and live
values are never public.

## 7. Legal, reuse, and runtime disposition

No-auth reachability is not a licence. The official provider pages reviewed for this
batch establish the following conservative posture:

| Provider | Official primary evidence | Current decision |
|---|---|---|
| VPS | [VPS terms](https://vps.com.vn/dieu-khoan-su-dung) and [VPS company/contact page](https://vps.com.vn/ve-chung-toi) | No affirmative route-specific permission for automated OSS retrieval, caller-facing return, caching/storage, commercial use, or redistribution; written permission required |
| SSI | [SSI service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu), [SSI network/contact page](https://www.ssi.com.vn/mang-luoi), and separate [developer terms](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments) | Anonymous chart access is not a redistribution grant; keyed/developer terms do not qualify this route; written permission required |
| VNDirect | [VNDIRECT terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) and [support/contact page](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/) | No affirmative chart-route OSS automation, cache, caller-facing, or redistribution grant; written permission and an identity route are required |

Current runtime disposition for all three is no cache, no storage, no bundled rows, no
archive, no bulk export, and no caller-facing source capability. The routes' current
HTTP behavior is an observation only; unknown rate limits are treated as finite/unsafe,
not unlimited.

## 8. Conjunctive reopen criteria

Reopen to a fresh design review, and only then to TDD, when **one same provider** passes
all of these conditions together. Evidence from different providers cannot be joined.

1. **Identity:** a response-backed `VNREAL` symbol, index type, exchange/namespace,
   D1 capability, point scale/value, timezone, and session contract exists on the same
   history/metadata unit. VNDirect needs a working same-owner identity route; SSI must
   bind its envelope/history to the metadata response rather than rely on request echo.
2. **Fixed coverage:** the requested inclusive window is proven against a documented
   exchange calendar/base date, with provider total/page/cursor/window-cap
   reconciliation, one normalized daily point per session, no conflicting duplicates,
   and explicit diagnostics for any partial boundary or internal gap.
3. **Semantics:** every accepted response has finite positive OHLC with the high/low
   envelope, aligned non-null volume with documented unit, exact D1 token, timezone/date
   convention, and a written/provider-backed RAW points declaration. A present integer
   zero volume remains zero; missing or unproven volume fails closed.
4. **Transport:** exact full Content-Type allow-list and parser behavior, stable
   effective host/redirect policy, no unreviewed browser-UA/WAF dependency, explicit
   authentication/session/cookie policy, and no maintenance HTML accepted as data.
5. **Legal/runtime:** written permission covers automated retrieval, OSS use,
   caller-facing return, redistribution, storage/caching, attribution, commercial use,
   rate limits, and retry behavior for the named route. No robots absence or no-login
   success substitutes for this permission.
6. **Budget/atomicity:** the `3 / 6` strict and `27 / 54` stitched global ledger (or a
   newly reviewed replacement) is deterministic, pre-dispatch atomic, and shared by
   identity/history/retry work; strict failover is whole-window, stitched failure is
   whole-call, and no fake attempt/partial result is emitted.
7. **Diagnostics/compatibility:** no-false-absence outcomes, canonical source roles,
   bounded warnings, price-path deny behavior, all other deny-only identifiers, current
   stitched semantics, synthetic offline tests, docs, build, blacklist/secret, and
   merged-tree gates pass without changing existing served indices.

Until all seven conditions are evidenced for the same provider, the correct state is
`SOURCE-GAP CLOSURE`. A later source-gap approval authorizes documentation publication,
clean resolution, remote verification, and close/re-read only; it never authorizes TDD
or production capability.

## 9. Source references and conclusion

Primary protocol and provider route references:

- [TradingView UDF protocol](https://www.tradingview.com/charting-library-docs/latest/connecting_data/UDF/)
- [VPS history route](https://histdatafeed.vps.com.vn/tradingview/history)
- [VPS symbol metadata route](https://histdatafeed.vps.com.vn/tradingview/symbols)
- [SSI history route](https://iboard-api.ssi.com.vn/statistics/charts/history)
- [SSI symbol metadata route](https://iboard-api.ssi.com.vn/statistics/charts/symbol)
- [VNDirect history route](https://dchart-api.vndirect.com.vn/dchart/history)
- [VNDirect symbol metadata route](https://dchart-api.vndirect.com.vn/dchart/symbol)

The direct evidence is sufficient to say that VPS, SSI, and VNDirect returned bounded
no-login VNREAL-shaped daily responses on 2026-08-23. It is not sufficient to say that
any one provider supplies a lawful, response-identified, complete, clean, rate-bounded,
redistributable `2018-01-01..2026-08-19` unit. VPS is recent and conflict-prone; SSI is
identity-compatible but lacks a complete fixed-window/legal/runtime contract; VNDirect
lacks same-owner identity. Therefore **no source qualifies end-to-end**.

The design result is deliberately conservative: preserve the empty VNREAL chain and the
current typed zero-network behavior, record `SOURCE-GAP CLOSURE`, and do not begin RED,
production code, push, or issue closure from this report.
