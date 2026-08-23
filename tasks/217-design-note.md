# #217 design note — daily CNY/VND FX history

**Status:** SOURCE-GAP CLOSURE; docs/source evidence only; correction after BLOCK at exact
`55f0b1b4d46ece6cab30b647d4c443a4cc3338d6`
**Packet:** `tasks/217-daily-cnyvnd-fx-history-spec.md` at reviewer `4159d74`
**Research:** [`docs/research/2026-08-23-daily-cnyvnd-fx-history-source-vetting.md`](../docs/research/2026-08-23-daily-cnyvnd-fx-history-source-vetting.md)
**Requested span:** inclusive `2018-01-01..2026-08-19`
**Current source chain:** empty; no daily CNY/VND capability

This is one docs/backlog-only correction for the reviewer B1-B5 block. It does not authorize
RED tests, a source registration, a model/accessor change, production code, a provider token,
a push, or issue closure. After a final docs-only PASS, the three-path range may be published
and #217 may be resolved/closed as SOURCE-GAP. A fresh implementation review is required only
if a source later qualifies.

## 1. Decision and compatibility boundary

`SOURCE-GAP CLOSURE` is the only honest disposition. No same-provider unit proves direct
CNY/VND identity, one economic basis, exact scale, requested coverage, bounded runtime, and
lawful reuse. The evidence is not a licence to combine:

- SBV USD/VND central-rate data with any CNY/USD data;
- ECB EUR/CNY with a VND leg;
- BIS USD-bilateral series with another provider;
- any VCB cash/transfer/sell or XML Buy/Transfer/Sell field with another field or basis; or
- current/spot values with historical observations.

The daily chain therefore remains `()`. Existing annual `USD`/`VND` World Bank behavior,
signature, source token, period-average semantics, diagnostics, documentation, repr/equality,
serialization, and DataFrame behavior remain unchanged. Unsupported pair/frequency/bounds
continue to fail before network under the current contract.

## 2. Qualification unit

One candidate is qualified only as this complete tuple:

```text
provider_token + exact owner route/version + response-backed base=CNY, quote=VND
+ one provider field/basis + VND per 1 CNY direction and proven scale
+ observation/publication/calendar/revision semantics + full or declared partial coverage
+ lawful automated-access, caller-return, storage, redistribution, and runtime contract
```

Every element is conjunctive. A valid number with unknown field direction, date meaning,
scale, rate policy, or reuse right is a source-gap axis, not `QUALIFIED` or `PARTIAL`. A value
quoted per 100 CNY may be divided by 100 only when the same owner response/documentation proves
the scale. Reversal, midpoint, interpolation, fill, resampling, nearest-date matching, and
cross-rate arithmetic are rejected. No public basis token or `rate_basis` field is frozen by
this note.

## 3. Candidate disposition matrix

### 3.1 VCB six-cell matrix

Each provider-observed field/basis is an independent unit. Shared HTTP observations do not
make the cells one candidate and do not multiply the call ledger.

| Candidate cell | Proven | Required before qualification | Disposition |
| --- | --- | --- | --- |
| VCB dated `cash` | Recent CNY object has `cash`; page labels cash purchase | Direct pair/direction, scale, economic basis, historical bounds, revision, rate policy, reuse | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` |
| VCB dated `transfer` | Recent CNY object has `transfer`; page labels transfer purchase | Same independent proof; never average with another field | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` |
| VCB dated `sell` | Recent CNY object has `sell`; page labels sale | Same independent proof; not a central or midpoint rate | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` |
| VCB XML `Buy` | Current CNY `Buy`, complete XML MIME | Historical/date semantics, selected basis, coverage, caller/reuse rights | `BASIS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` |
| VCB XML `Transfer` | Current CNY `Transfer`, complete XML MIME | Same independent current/spot and legal proof | `BASIS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` |
| VCB XML `Sell` | Current CNY `Sell`, complete XML MIME | Same independent current/spot and legal proof | `BASIS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` |

The dated 2018 empty envelope is not absence; the 2020 timeout is transport-unknown. The XML
response is current/spot and its five-minute reference note is not transferred to the dated
route. No field is averaged, inverted, or used as failover for another field.

### 3.2 Other candidates

| Candidate | Correct current evidence | Missing | Disposition |
| --- | --- | --- | --- |
| SBV reference/cross/central routes | Official menu separates products; three direct routes timed out | Response-backed direct CNY/VND schema, scale, date/calendar, coverage, rights | `TRANSPORT_INCONCLUSIVE` + `IDENTITY_GAP` + `LEGAL_GAP` |
| PBOC/CFETS | Shown direct RMB lists omit VND; CFETS terms require written authorization | Public direct pair and permission | `NOT_SERVED` + `LEGAL_GAP` |
| BIS `XRU` | Official VND/USD page; v2 daily keys 404 and monthly keys return monthly VND/USD | Direct CNY/VND identity and daily basis | `NOT_SERVED` + `BASIS_GAP` |
| Frankfurter v2 | No-key CNY/VND route, provider catalogue, historical/range API, default blending and attribution controls | One-owner direct basis, exact requested coverage/cadence, underlying rights/rate policy | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` |
| World Bank WDI | Existing annual USD/VND period-average source | Daily CNY/VND pair/frequency | `NOT_SERVED`; preserve annual |
| H.10/FRED | H.10 HTML has no VND; FRED is USD base / CNY quote | Direct CNY/VND pair; cross-conversion forbidden | `NOT_SERVED` + `BASIS_GAP` |
| Current open-rate API | No-key current/spot only; restrictive raw redistribution terms | Historical retention and lawful historical reuse | `NOT_SERVED` + `LEGAL_GAP` |

Frankfurter v2 is evaluated as a distinct current candidate, not inherited from ECB-v1. Its
public route's `base`/`quote` syntax does not prove one owner, one economic field, or one
underlying licence. Provider filtering would require a new provider-specific qualification.

## 4. Exact evidence ledger

The research artifact records the full reproducible publishable ledger: **17 logical targets,
18 physical calls, one retry**. It separates direct dispatches from page/legal inspections and
identifies complete MIME/effective route for every retained response. Two earlier BIS
exploratory dispatches did not retain complete headers/routes and are explicitly retired,
excluded from this total, and never support absence or qualification. Four exact BIS v2
correction rows supersede them. Frankfurter v2 correction probes were four separate
logical/physical calls, all HTTP 200 JSON, with no retry.

For every future response, `complete_mime` is the complete header value after the first colon;
`effective_route` is the no-follow host/path. A timeout has no effective route. A provider field
observed in a response does not create another logical or physical call.

## 5. Future validation and total coverage contract

There is no new API or model in this change. A future qualified-source implementation must
assign validation to all public seams:

- **Input/facade:** accept only exact plain `datetime.date` bounds and normalized
  `(base=CNY, quote=VND, frequency=daily)`; reject `datetime`, timezone-bearing bounds,
  malformed pair, and unsupported frequency before network.
- **Adapter:** prove response pair, selected field/basis, direction, scale, date meaning,
  page/count/cursor reconciliation, complete MIME, and revision semantics before point
  construction.
- **Model:** defensively reject non-plain observation dates, timezone-bearing observation
  timestamps, wrong pair/unit/value-unit, boolean/non-numeric/non-finite/zero/negative rates,
  duplicates, non-ascending points, and non-UTC `fetched_at_utc`. Retrieval time is not
  publication time. Existing annual construction stays byte-compatible.
- **Result/facade:** recheck one-source/one-basis/exact-date invariants and expose only a
  separately approved finite diagnostic carrier. The current public model has no `rate_basis`
  field; no such field is added or populated here.

The future coverage record keeps distinct:

```text
requested_start/end   provider-served/archive bounds   actual observed_start/end
```

`FULL` requires served bounds covering the request, reconciled pages/counts/cursors, distinct
ordered in-range observations, and provider calendar/status for every non-publication hole.
`PARTIAL` requires provider-declared narrower served bounds plus exact observed bounds and
reconciled pages; it never claims the requested full span. A no-row or malformed page before
reconciliation is a typed coverage failure, not a zero or absence.

Confirmed provider non-publication is total: a mixed range returns actual points plus one
finite warning; a range whose every requested date is confirmed non-publication returns a
typed empty result with `points=()`, evaluated full-coverage status, `latest() is None`, and
the warning. `rate_on(d)` remains exact-match-only and raises for a non-published date. An
unconfirmed empty response, timeout, WAF/HTML, redirect, 404, truncation, invalid MIME,
budget exhaustion, or unreconciled page returns no history and cannot claim absence. The
public carrier and exact token names are deferred until a source qualifies, but these rows,
bounds, warning, accessor, and latest semantics are mandatory.

## 6. Future sequential budget and diagnostics contract

No numeric ceiling is frozen before source route, rate, pagination, retry, and body evidence
exists. The future scheduler must nevertheless be:

1. one request-scoped sequential ledger with no per-source reset, date fan-out, cross-source
   stitch, or accidental partial;
2. atomic for source/page/retry/physical reservation before dispatch;
3. byte-safe: response bytes are charged atomically per decompressed streamed chunk to both
   per-response and global counters; overflow aborts before the cap while retaining the
   physical-call charge;
4. retry-safe: a retry validates the same logical page/cursor and increments retry plus
   physical only, never a second logical-page reservation;
5. status-safe: a capability skip has no dispatch record and consumes no budget; budget
   exhaustion is pre-dispatch; only a real reservation creates a dispatch row; and
6. deterministic: every real dispatch records status, complete MIME, effective route,
   row count, and provider cursor/total exactly once, then the source succeeds only after
   all rows reconcile.

Only HTTP 200 with an exact source-approved complete MIME may be data-success. Redirects are
not followed; 204/4xx/5xx, DNS/connection/TLS/timeout, HTML/WAF, parse, MIME, and body-limit
outcomes remain distinct internal categories. Raw URL/query, body, headers, cookies,
credentials, provider prose, and exception text never become public. Exact public error and
warning names, tuple bounds, overflow behavior, and the additive carrier are selected only
after a qualified source and compatibility review; no phantom “empty attempt” or
“diagnostics truncated” record is permitted.

## 7. Legal, spot scope, reopen, and lifecycle

The nine independent legal/runtime axes are owner identity, automated access, caller-facing
return, storage/cache, redistribution, attribution, commercial use, rate/retry, and
revision/correction. Public reachability, no-key access, “reference only,” or a facade is not
a grant. #217 changes no current VCB/open.er-api spot adapter and grants no new spot rights;
the spot observations disqualify only the new historical use.

Reopen requires, for one same provider/route/basis: exact MIME/effective route and bounded
transport; direct pair/basis/scale/date/revision; requested or declared partial bounds with
calendar/non-publication and page reconciliation; owner-approved finite sequential runtime;
all nine legal axes; and an annual-compatible diagnostics/model plan. Only after that design
PASS may a fresh RED-first implementation gate begin.

For a final docs-only PASS, publish exactly these three paths from clean base
`8350329d3d881e34df62937aacf7ea4d74f99f91` through the exact correction anchor returned in the
handoff:

```text
docs/research/2026-08-23-daily-cnyvnd-fx-history-source-vetting.md
tasks/217-design-note.md
tasks/active-backlog.md
```

Then rerun merged gates, verify remote ancestry/paths, post clean SOURCE-GAP/no-capability
resolution, close/re-read #217, and leave #218 queued. No implementation review is needed
for this source-gap closure; it is needed only if a source later qualifies.

## 8. Future RED/release matrix — not authorized now

After a fresh design PASS only: test exact pair/frequency zero-network validation; strict
plain dates and UTC retrieval time; pair/unit/value-unit; ordering/duplicates and
boolean/non-finite/zero/negative rates; direct field/basis/scale and 100-unit cases;
complete MIME/status/effective-route/redirect/WAF/body limits; provider served versus actual
bounds; confirmed non-publication empty/mixed behavior; page/count/cursor reconciliation;
atomic byte/retry/budget behavior; diagnostics sanitization and compatibility; annual
repr/equality/serialization/DataFrame/API snapshots; build, docs, blacklist/secret/diff/path,
full offline tests, and a second exact-SHA review. No RED, code, runtime capability, source
registration, or daily coverage claim is part of this correction.
