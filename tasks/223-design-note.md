# #223 VNCOND D1 index-history source/design note

**Packet:** `tasks/223-vncond-index-history-source-spec.md` at `6939ba4`
**Design date:** 2026-08-24 (UTC+7)
**Clean production base:** `origin/master` `c3921a1a7a31c5de8b21f838173fd1c288b0e698`
**Requested:** provider-published `VNCOND` D1 value history for inclusive local dates
`2018-01-01..2026-08-20`
**Decision:** **SOURCE-GAP CLOSURE**
**Runtime state:** current `VNCOND` deny-only; new source chain empty; no code/API capability.

## 1. Scope and release boundary

The current registry recognizes `VNCOND` as a market-index identifier but does not include it in
the value-history allow-list. Both strict and opt-in stitched index-history entry points fail
typed and zero-network before the failover sources. Preserve this behavior. The tag
`2fe50df4f27064140ff9f7a680227a2b337ec74a` predates the current registry guard and is a historical
boundary only; it does not prove v0.2.0 VNCOND behavior.

This note is source/design evidence only. It adds no enum, source, route, probe, RED test, runtime
code, proxy, basket, downstream signal, cache, archive, dataset, or public coverage claim.

The repository clean-room blacklist was applied before research, with the exact exclusion recorded
in the companion source-vetting report. Only official HOSE, VPS, SSI, and VNDIRECT material and
current repository boundaries were used.

## 2. Identity and qualification gate

The official HOSE 2024 Annual Report is the direct code anchor reviewed for `VNCOND`; it associates
that code with the exchange's consumer-goods sector entry. The official sector factsheet supplies
the VNAllShare Consumer Discretionary family and family-level static metadata—base date
`25/01/2016`, base value `533.49`, real-time frequency, and unit `VND`. These are identity and
methodology facts only: they do not provide a response-backed `VNCOND` D1 history route, response
point scale, or an OSS redistribution grant. The existing VPS/SSI/VNDIRECT paths are candidate
inventory only: this round made zero provider/API dispatches, so response status, complete MIME,
envelope, identity, dates, pages, volume, and effective transport are `NOT_PROBED`/`NOT_RETAINED`.

One provider unit must prove all axes below; cross-provider rows or another sector/index cannot
repair a missing axis:

| Axis | Required evidence | Current #223 disposition |
|---|---|---|
| Owner/route | Official owner, canonical history path, same-owner identity route, non-secret selector and D1 token | HOSE code anchor/owner landing retained but no machine route; VPS/SSI/VNDIRECT candidates have no VNCOND-specific identity pair |
| Response identity | Returned symbol `VNCOND`, exchange/index/sector identity, history-to-identity binding, D1 capability | `IDENTITY_GAP`; no response retained |
| Shape/semantics | Full status/envelope/MIME, finite positive OHLC, point scale, timezone/session, timestamp date/open/close meaning, non-null volume with unit/null policy, explicit RAW | `NOT_PROBED`; no provider semantics may be inferred from current adapter defaults |
| Coverage | Inclusive `2018-01-01..2026-08-20`, provider-declared bounds, observed first/last local dates, rows/distinct rows, requested-bound presence, gaps/duplicates, inception/base-date | `COVERAGE_GAP`; no rows or provider bounds retained |
| Pagination/revision | Total/page/cursor/window reconciliation, revision/as-of and duplicate/conflict rules | `PAGINATION_GAP`; no route response retained |
| Runtime | Authentication/session/WAF, automation, rate, retries, page/byte/physical-request ceilings | `RATE_POLICY_GAP` + `TRANSPORT_INCONCLUSIVE` |
| Rights | Caller use, retention/cache, attribution, commercial use, redistribution | `LEGAL_GAP`; no clear public OSS grant; VNDIRECT terms lead returned HTTP 403/Cloudflare challenge on 2026-08-24 and was not interpreted |

Total status is one of `QUALIFIED`, `PARTIAL`, `NOT_SERVED`, `IDENTITY_GAP`, `COVERAGE_GAP`,
`TIMESTAMP_GAP`, `VOLUME_GAP`, `PAGINATION_GAP`, `LEGAL_GAP`, `RATE_POLICY_GAP`, or
`TRANSPORT_INCONCLUSIVE`. No candidate is `QUALIFIED` or qualified `PARTIAL`.

## 3. Candidate disposition

| Unit | Current repository candidate | Evidence boundary | Total status |
|---|---|---|---|
| HOSE owner | Official annual-report code anchor and factsheet family identity | No machine route or response retained; D1 response, coverage, runtime, pagination, response point scale, and reuse are unproven; detail `NO_ROUTE_RETAINED` | `TRANSPORT_INCONCLUSIVE` |
| VPS | `https://histdatafeed.vps.com.vn/tradingview/history`, adapter token `D` | No VNCOND response or same-owner identity route; SmartOne login/UI and restrictive terms do not close anonymous reuse | `IDENTITY_GAP` |
| SSI | `https://iboard-api.ssi.com.vn/statistics/charts/history`, adapter token `1D` | Generic keyed daily-API docs and VNINDEX/VN30 examples do not prove VNCOND or anonymous reuse | `IDENTITY_GAP` |
| VNDIRECT | `https://dchart-api.vndirect.com.vn/dchart/history`, adapter token `D` | Public index-history UI is not a response-backed VNCOND route; official terms lead returned HTTP 403/Cloudflare challenge on 2026-08-24 and was not interpreted | `IDENTITY_GAP` |

The complete per-axis ledger and official links are in
`docs/research/2026-08-23-vncond-sector-index-history-source-vetting.md`. Empty/blocked/capped/
recent-only/WAF outcomes in a later bounded review would prove only that bounded outcome, never
universal absence.

## 4. Future contract (not current API)

Only a new exact design PASS after a qualified source may authorize TDD. If one provider later
meets every conjunctive reopen criterion, the implementation contract is:

1. add `VNCOND` exactly once to `_VALUE_HISTORY_INDICES`; preserve all other deny-only identifiers
   and the price-path type guard;
2. accept exact D1 only; reject wrong/proxy/non-D1 selectors before network;
3. return one provider's complete validated `PriceHistory` with canonical `VNCOND`,
   `currency="points"`, `value_unit="points"`, `AdjustmentPolicy.RAW`, bounded warnings, and no
   synthesized volume or metadata;
4. build a VNCOND capability filter from independently `QUALIFIED` provider roles only. Preserve
   the relative VPS → SSI → VNDIRECT order among qualified roles; exclude every unqualified or
   unknown role before scheduling, creating no call and no `SourceAttempt` for it. If the filtered
   set is empty, return the typed no-qualified-source terminal without a provider call. Never
   silently route strict calls to stitched;
5. permit explicit D1 calendar-year stitching only with independently validated segments,
   identical/conflicting seam rules, source/segment provenance, atomic failure, and every segment
   carrying a non-`None`, timezone-aware `fetched_at_utc` whose `utcoffset() == timedelta(0)`.
   Missing, naive, or non-UTC stamps fail stitching atomically; the aggregate is exactly the
   maximum of validated UTC stamps and is never fabricated; and
6. expose finite sanitized diagnostics only—no raw query, body, cookie, token, unbounded provider
   text, or fabricated attempt record.

## 5. Shared budget and diagnostics (future design only)

One request-scoped atomic ledger must cover identity, history, pagination/cursors, retries, and all
stitched segments. Numeric ceilings must come from a later qualified provider evidence packet; no
number is asserted here. Reserve logical operation, physical dispatch, page, and retry units before
dispatch. Wire bytes and decompressed bytes cannot be known before reading: increment separate
counters for each bounded chunk, abort when the next chunk would exceed its cap, discard the
accumulator, and return a deterministic typed terminal outcome. A non-streaming transport that
cannot enforce incremental caps is not eligible for qualification. Failed pre-dispatch reservation
makes no network call; byte exhaustion returns no partial bars and preserves prior sanitized
attempts. There is no per-source/year reset, hidden concurrency, or retry storm. The exact public
exception/result carrier remains deferred to a later qualified-source API PASS; this source-gap
note specifies only the typed terminal kind and sanitized internal fields. Full Content-Type is
captured before normalization; unexpected status, redirect/effective host, MIME, maintenance HTML,
or malformed envelope fails closed.

## 6. Reopen and future RED/release matrix

Reopen is conjunctive: official owner/path and identity pair; response-backed VNCOND identity;
complete D1 point/volume/time semantics; provider-declared and observed requested coverage with
reconciled pagination; bounded rate/retry/page/byte/physical-request policy; and lawful
attribution/retention/redistribution. One failed axis keeps the chain empty.

After qualification, synthetic offline RED fixtures must cover:

- selector normalization and wrong/proxy/non-D1 zero-network rejection;
- identity, exchange/index/sector, D1, points, timezone/session, MIME/envelope/status, provenance,
  volume, adjustment, and malformed-value negatives;
- full versus partial bounds, inception, duplicates/conflicts, internal gaps, page/total/cursor
  reconciliation, revision, and no-false-absence diagnostics;
- shared logical/physical/page/retry reservation, incremental wire/decompressed byte caps,
  pre-dispatch reservation, chunk-boundary abort/discard, deterministic exhaustion, preserved
  sanitized prior attempts, deferred public carrier, atomic strict and stitched failures, seam
  overlaps, segment provenance, non-`None` UTC-aware zero-offset stamps, exact UTC maximum, and
  missing/naive/non-UTC atomic failures; and
- compatibility of all existing served indices, every deny-only identifier, the price path,
  DataFrame/public snapshots, docs/imports, and D1/non-D1 behavior.

## 7. Disposition and lifecycle

```text
SOURCE-GAP CLOSURE
VNCOND new source chain: EMPTY
current recognized-index deny-only / zero-network behavior: PRESERVED
```

If this note and the companion report receive design PASS, the allowed next step is exact-anchor
docs/source-gap publication verification, a clean no-capability resolution, and issue close/re-read.
That PASS would not authorize a provider probe, RED, TDD, production code, source registration, or
runtime capability. #224 and #225 remain queued behind #223 and are untouched.
