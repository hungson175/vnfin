# #213 design note — VNREAL daily sector-index history

**Issue:** #213
**Date:** 2026-08-23 (UTC+7)
**Phase:** `SOURCE_DESIGN` / docs-only
**Builder:** `vnfin-oss`
**Requested:** canonical `VNREAL`, D1, inclusive `2018-01-01..2026-08-19`
**Disposition:** **SOURCE-GAP CLOSURE**
**Review gate:** exact-SHA design review required before TDD, production code, push, or close

The fresh source evidence is in
[`docs/research/2026-08-23-vnreal-sector-index-history-source-vetting.md`](../docs/research/2026-08-23-vnreal-sector-index-history-source-vetting.md).
This note binds the future design boundary but does not authorize runtime capability.

## 1. Current behavior and release boundary

Current master keeps `VNREAL` in the private index deny namespace but not in the value
history allow-list. Consequently:

- `prices.history("VNREAL", ...)` remains a typed wrong-namespace rejection before
  network;
- `indices.index_history("VNREAL", ...)` remains a typed terminal unsupported-history
  diagnostic before network;
- `indices.index_history_stitched("VNREAL", ...)` has the same empty-chain behavior;
- existing served indices, other deny-only sectors, points units, and existing stitched
  provenance remain unchanged; and
- this docs-only source-gap round adds no source, endpoint, credential, cache, fixture,
  dataset, or public capability.

The annotated `v0.2.0` tag is
`2fe50df4f27064140ff9f7a680227a2b337ec74a`. It is a historical release boundary and is
not evidence that VNREAL was served. The current registry/zero-network behavior is read
from current master `5ad0ad6ae6a19d9827a61e354177b3ae91bac9fc`; do not mix tag-era files
with current-master behavior in a later implementation review.

## 2. Decision table

| Source unit | Fresh response-backed identity | Fixed-window observation | Technical disposition | Legal/runtime disposition |
|---|---|---|---|---|
| `vps_index` history + same-owner symbols metadata | Yes: history echoed `VNREAL`; metadata returned `symbol=ticker=name=VNREAL`, index point scale, timezone, and daily capability | 1,649 raw / 1,615 distinct local dates; first `2020-03-03`, last `2026-08-19`; 34 duplicates, including 33 conflicting; requested start unserved | `PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + PAGINATION_GAP` | `LEGAL_GAP + RATE_POLICY_GAP`; browser-UA dependency remains unclosed |
| `ssi_index` history + same-owner charts metadata | Yes via same-provider metadata; history envelope has no symbol echo | 2,148 raw / 2,147 distinct; first `2018-01-02`, last `2026-08-19`; one identical duplicate; requested literal start unproven; no provider total | `PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + PAGINATION_GAP` | `LEGAL_GAP + RATE_POLICY_GAP`; cookie header observed but no reuse |
| `vndirect_index` history + same-owner symbol route | No: history lacks symbol and same-owner identity route returned HTTP 404 | 2,152 raw / 2,152 distinct; first `2018-01-02`, last `2026-08-19`; requested literal start unproven | `IDENTITY_GAP + COVERAGE_GAP + TIMESTAMP_GAP + PAGINATION_GAP` | `LEGAL_GAP + RATE_POLICY_GAP`; normalized history MIME is `text/plain` |

No row is a qualified release candidate. The source units are not interchangeable: VPS
permission cannot qualify SSI data, SSI metadata cannot repair VNDirect identity, and a
matching date range is not selector identity.

## 3. Future registry and strict contract (not implemented)

Only after a later exact design PASS on a qualified source may the implementation:

1. add exactly `VNREAL` to `_VALUE_HISTORY_INDICES`, leaving its price-path deny entry
   and every other deny-only identifier unchanged;
2. accept only exact `Interval.D1` after typed canonical selector/range validation;
3. enforce source capability per `(role, VNREAL, D1)` for both default and injected
   chains before transport; an incapable role is a skip, not an attempt;
4. require same-provider response identity, exact full Content-Type normalization,
   success envelope/status, aligned finite D1 point bars, aligned non-null volume, a
   documented timezone/session/timestamp convention, and `AdjustmentPolicy.RAW`;
5. return one provider's complete validated `PriceHistory` with
   `currency=value_unit="points"`, canonical `source`, and bounded sanitized warnings;
6. fail closed on an unproven fixed-window boundary, duplicate/conflicting date,
   missing/null volume, wrong MIME/envelope, symbol mismatch, invalid OHLC, or any
   unresolved legal/rate/pagination axis; and
7. never substitute `VNFIN`, another sector, a basket, an equity/ETF proxy, or another
   provider's bars inside strict history.

The default strict order may remain VPS → SSI → VNDirect, but only a fully qualified
source unit can be attempted. A source capability skip consumes no logical or physical
budget and creates no fabricated attempt record.

## 4. Fixed versus stitched history

The strict request is one provider, one identity unit, one validated full window. It must
not silently call the opt-in stitcher. The existing `index_history_stitched()` entrypoint
remains D1-only, calendar-year segmented, and explicitly multi-source in provenance.

For this requested range it has nine segments (`2018` through `2026`, inclusive). It may
be considered only after strict VNREAL qualification. Each segment must pass absolute
D1/points/RAW/canonical-symbol checks; identical seam bars may be deduplicated and
conflicting seams are fatal. If any segment fails or is unqualified, the public call is
atomic and returns no partial series. Strict history never uses stitching to mask a
source or legal gap.

## 5. Deterministic global budget (design-only)

The future call owns one atomic request ledger. Its exact conservative design values are:

| Contract | Strict | Stitched 2018–2026 |
|---|---:|---:|
| Maximum logical source attempts | 3 total; `max_attempts` is bounded to 1–3 | 27 total across all 9 segments; no segment reset |
| Physical dispatches per logical attempt | at most 2 (identity + history) | at most 2 (identity + history) |
| Automatic retry dispatches | 0 | 0 |
| Maximum physical dispatches | 6 | 54 |

One logical attempt is one `(provider, symbol, interval, segment)` evaluation. One
physical dispatch is one actual HTTP request. Identity failure may avoid history, so the
actual count may be lower, but the cap is never higher. The two bounded observation
passes recorded 24 logical and 24 physical calls with zero retries; they do not authorize
the future runtime budget.

Before every identity or history dispatch, the ledger atomically reserves one physical
slot. If no slot remains, the public strict/stitched call raises the typed future
`BudgetGlobalExhausted` (`VnfinError`) with all previous sanitized attempts and bounded counters;
it sends no request and returns no sentinel or partial `PriceHistory`. There is no hidden
redirect/retry/page dispatch, no concurrent dispatch, no per-segment counter, and no synthetic
attempt for budget exhaustion. Any pagination, redirect, retry, or rate-policy change requires
a new reviewed finite formula.

## 6. Diagnostics and no-false-absence rules

The future public diagnostic must distinguish:

- `IDENTITY_GAP` — no response-backed same-provider VNREAL identity;
- `COVERAGE_GAP` — fixed window not proven, including an unexplained boundary;
- `TIMESTAMP_GAP` — local date is observable but session/open-close convention is not;
- `VOLUME_GAP` — volume absent, null, misaligned, invalid, or unit-unproven;
- `PAGINATION_GAP` — no total/page/cursor/window-cap reconciliation;
- `LEGAL_GAP` — no written automated OSS/caller-facing/cache/redistribution permission;
- `RATE_POLICY_GAP` — no route-specific rate, retry, and cache policy; and
- `TRANSPORT_INCONCLUSIVE` — MIME, redirect, auth, WAF, or envelope behavior is not
  classifiable.

`NO_DATA_OBSERVED` is allowed only for an identity-bound response that explicitly reports
no data for the requested window. It must not be inferred from an identity 404, empty
unbound data, timeout, server cap, recent-only coverage, or one missing literal date.
The aggregate failure is `SOURCE-GAP`, never a successful empty `PriceHistory` and never
a claim that VNREAL history is absent.

Attempt provenance may contain only the canonical role names `vps_index`, `ssi_index`,
and `vndirect_index`, finite outcome tokens, bounded physical-call counts, and sanitized
axis fields. It must preserve earlier attempts before a later budget exhaustion. It must
not expose URLs, query strings, response bodies, cookies, headers, provider exception
text, credentials, or live values. Warning tuples and attempt tuples are finite and
deterministic.

## 7. Conjunctive reopen gate

Reopen to TDD only when one named provider passes all gates below in the same source unit:

1. **Identity:** response-backed `VNREAL`, exchange/index type, point scale/value,
   timezone/session, D1 capability, and exact history/metadata binding. VNDirect needs a
   working identity route; SSI must bind its envelope to the metadata response.
2. **Coverage:** documented exchange calendar/base date, exact requested inclusive
   window, provider total/page/cursor/window-cap reconciliation, one row per session,
   and no conflicting duplicates or silent gaps.
3. **Semantics:** finite positive OHLC and high/low envelope, aligned non-null volume
   with documented unit, exact D1 token, timestamp convention, and provider-backed RAW
   points declaration. Never synthesize zero volume.
4. **Transport:** exact full Content-Type allow-list, stable redirect policy, no
   unreviewed browser-UA/WAF dependency, explicit auth/session/cookie rules, and no
   maintenance HTML accepted as data.
5. **Legal/runtime:** written permission for automated retrieval, OSS use, caller-facing
   return, redistribution, cache/storage, attribution, commercial use, rate, and retry
   behavior on the named route.
6. **Budget/atomicity:** deterministic shared global ledger (`3 / 6` strict and
   `27 / 54` stitched, or a newly reviewed replacement), pre-dispatch reservations,
   whole-window strict failover, whole-call stitched failure, and no fake attempt.
7. **Diagnostics/compatibility:** no-false-absence diagnostics, finite sanitized
   provenance, unchanged price deny behavior and existing index semantics, synthetic
   offline RED tests, docs/build/blacklist/secret checks, and merged-tree gates.

Until all seven conditions pass for one provider, the disposition remains
`SOURCE-GAP CLOSURE`. Evidence from a different provider cannot close a missing axis.

## 8. Delivery boundary

This commit contains only the source vetting report and this design note. It authorizes
only exact-SHA docs/design review. It does **not** authorize:

- RED tests or production code;
- adding `VNREAL` to a runtime allow-list;
- live integration tests, fixtures, cache, archive, or provider rows;
- a cross-source stitch, proxy, basket, signal, or downstream feature;
- push, public resolution, or issue close before design PASS.

If a later design review passes as source-gap closure, the allowed follow-up is docs-only
publication/resolution/remote verification/close-re-read. If a later provider qualifies,
that is a fresh design decision followed by TDD first; this note never pre-authorizes it.
