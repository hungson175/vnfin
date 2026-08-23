# VN stock-dividend and bonus-share source vetting

**Date:** 23 August 2026 (Vietnam time, UTC+7)
**Owner:** `vnfin-oss`
**Issue:** #215
**Disposition:** `SOURCE-GAP CLOSURE` — no new source is qualified or enabled
**Requested inclusive window:** 13 August 2018 through 19 August 2026 (`2018-08-13..2026-08-19`)

## Published-boundary evidence

The annotated historical `v0.2.0` boundary is exact commit
`2fe50df4f27064140ff9f7a680227a2b337ec74a`. That commit has no `vnfin/corp_actions` tree and is
not the current cash behavior. The reviewed current published base is exact
`origin/master` `8126dd5510b6390f91c9feeb43e047b2b9b88bc1`, which contains the cash-only corporate-
actions surface. #215 changes neither boundary and grants no legal clearance to the existing cash
adapter.

## Clean-room and evidence boundary

This is a clean-room source/legal review of official VSDC, VNDIRECT, HOSE, and HNX material only.
Before the research pass, `docs/vnstock-blacklist.md` was read on 23 August 2026. Every web-search
query carried the repository's mandatory negative exclusions; no excluded result was opened, cited,
or used. No blacklisted code, endpoint map, schema, fixture, package, or conclusion was consulted.

The observations below are bounded snapshots, not a provider SLA, complete archive crawl, legal
opinion, or production authorization. No raw provider payload, cookie, token, query-bearing URL,
live event ratio/date/value, screenshot, or response digest is retained. The only numerical examples
in this report are synthetic and explicitly labelled. The two candidate event kinds are evaluated
independently; agreement between sources cannot repair a missing axis in either source.

## Executive decision

The direct probes found useful official material, but no single no-login source unit proves all of
these axes together for both requested kinds over `2018-08-13..2026-08-19`:

1. response-backed legal-issuer and symbol identity;
2. an explicit provider event token that distinguishes `STOCK_DIVIDEND` from `BONUS_SHARE`;
3. a response-backed ex/effective date (never a date inferred from record date, announcement date,
   pay date, or settlement rules);
4. an exact `shares_per_100` unit and its orientation, including rounding/fraction rules;
5. stable event and revision/cancellation identity;
6. reconciled full-window pagination and exact `FULL`/`PARTIAL`/`UNKNOWN` coverage;
7. finite, lawful runtime, retry, cache, attribution, and redistribution posture.

The result is a source gap, not a claim that no such events exist:

```text
VSDC stock-dividend unit = SOURCE_GAP
VSDC bonus-share unit    = SOURCE_GAP
VNDIRECT stock-dividend unit = SOURCE_GAP
VNDIRECT bonus-share unit    = SOURCE_GAP
HOSE/HNX exchange units   = NOT_SERVED / TRANSPORT_OR_SCHEMA_INCONCLUSIVE
new share-distribution chain = EMPTY_AND_DISABLED
runtime capability        = NOT_AUTHORIZED
current cash VSDC surface = PRESERVED_BYTE_FOR_BYTE
```

The current `vnfin.corp_actions.dividends()` / `CashDividendEvent(kind="CASH")` surface remains
unchanged. This report authorizes only a later design re-review if the conjunctive reopen evidence
in the companion note is obtained. A docs-only source-gap PASS may publish the approved docs/backlog
range, post the clean no-capability resolution, and close/re-read #215; it does not authorize models, accessors,
parsing, RED tests, a new source token, a cache, or runtime capability.

## Candidate matrix

`Coverage` below is the requested window, not the provider's most recent rows. `SourceAttempt` counts
are the bounded direct-probe ledger in section 4; they are not provider row counts.

| Candidate unit | Direct official observation on 23 August 2026 | Identity and kind evidence | Date and unit evidence | Coverage/pagination and revision | Legal/runtime disposition | Overall |
|---|---|---|---|---|---|---|
| **VSDC — stock dividend** | `GET /vi/search`, `GET /vi/s-detail/{id}`, and canonical `GET /vi/ad/{id}` returned HTTP 200 with exact `text/html; charset=utf-8`; the search/detail/announcement pages are first-party HTML, not a published API. A rights-calendar route returned an empty body in this environment and was not used. | Official VSDC announcements expose issuer name, ticker, ISIN, venue, record-date label, reason/title, and an execution-ratio section. There is an **unqualified official notice observation** with stock-dividend wording at the [STK notice](https://vsd.vn/vi/ad/197036). The sampled response does not provide a stable machine event type or revision contract. | The announcement publishes `Ngày đăng ký cuối cùng` (record date) and an issue/rights ratio, but no response-backed ex/effective field was admitted. VSDC's [rights-date explanation](https://web.vsd.vn/vi/ad/195688) describes how an ex-rights date relates to a record date; deriving one would violate this issue's no-inference rule. Ratio orientation, fractional entitlement, and rounding need a route contract. | First-party page controls and observed AJAX shapes are not a versioned page/total/cursor contract. No exact first/last served effective dates, complete event count, amendment rule, or all-page reconciliation was proven. | VSDC ownership is clear, but the inspected [legal/rules section](https://vsd.vn/vi/lel), [official home/contact navigation](https://vsd.vn/vi/), and pages do not grant automated fetching, caching, derived-row redistribution, or OSS caller redistribution. `robots.txt` redirected to a soft-not-found page. | `SOURCE_GAP`: `IDENTITY_GAP + EFFECTIVE_DATE_GAP + EVENT_TYPE_GAP + RATIO_UNIT_GAP + COVERAGE_GAP + PAGINATION_GAP + REVISION_GAP + LEGAL_GAP + RATE_POLICY_GAP` |
| **VSDC — bonus share** | Same official VSDC route family and response shape as above. There is an **unqualified official notice observation** with capital-from-equity/bonus-like wording at the [BID notice](https://web.vsd.vn/vi/ad1/199049); an older official example explicitly uses “cổ phiếu thưởng” at [VSDC announcement 144935](https://vsd.vn/vi/ad/144935). These are evidence that official notices exist, not a history API. | The notice text can describe capital-from-equity or bonus wording and carries issuer/ticker/ISIN fields, but free text alone is not a stable event-kind token. Mixed reasons and similarly worded rights must be rejected until VSDC supplies an exact type mapping. | The same record-date-only boundary applies. No ex/effective date may be calculated from the record date or from the VSDC explanatory article. A ratio shown in a notice is not accepted as `shares_per_100` until its orientation and rounding semantics are bound to the same provider schema. | No provider-declared complete history, page reconciliation, retention, amendment, cancellation, or supersession rule was found. An empty related-rights table is not proven absence. | Same unresolved VSDC permission, rate, cache, retention, and redistribution axes. | `SOURCE_GAP`: `IDENTITY_GAP + EVENT_TYPE_GAP + EFFECTIVE_DATE_GAP + RATIO_UNIT_GAP + COVERAGE_GAP + PAGINATION_GAP + REVISION_GAP + LEGAL_GAP + RATE_POLICY_GAP` |
| **VNDIRECT finfo — stock dividend** | Two one-page direct GET probes to the official `/v4/events` path returned HTTP 200 and `application/json`. The envelope had `data`, `currentPage`, `size`, `totalElements`, and `totalPages`; the sampled row exposed `id`, `code`, `type`, `group`, `typeDesc`, `effectiveDate`, `expiredDate`, `disclosureDate`, `ratio`, `numberOfShares`, `note`, and `locale`. No query-bearing URL is retained. | `code` and `id` are useful response fields and `STOCKDIV` was observed as an **unqualified** route filter/row kind, but no same-owner public data dictionary or rights contract was found that binds the token to the exact normalized event kind and legal issuer identity for every row. `typeDesc`/`note` cannot be the sole mapping. | `effectiveDate` exists in the row shape, but its ex/effective meaning is not proved. VNDIRECT's official [rights-search guidance](https://support.vndirect.com.vn/hc/vi/articles/32244485001753-H%C6%B0%E1%BB%9Bng-d%E1%BA%ABn-tra-c%E1%BB%A9u-quy%E1%BB%81n) describes account-bound rights and an expected-execution date filter, not a public historical ex-date data dictionary. No record-date/revision semantics or ratio orientation contract was established. | The JSON totals are technical pagination metadata, not proof that all pages cover the requested 2018–2026 window. No retention floor, date-range completeness, duplicate/locale/revision rule, or cancellation semantics was established. | Official [API content signals](https://api-finfo.vndirect.com.vn/robots.txt) say `search=yes,ai-train=no,use=reference`; they do not grant financial-row automation, caching, or redistribution. Direct GETs to [terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) and [support](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/) returned HTTP 403 on 23 August 2026; their content was not read and no permission conclusion is inferred. DStock carries VNDIRECT copyright and a reference-data disclaimer at [DStock](https://dstock.vndirect.com.vn/). | `SOURCE_GAP`: `IDENTITY_GAP + EVENT_TYPE_GAP + EFFECTIVE_DATE_GAP + RATIO_UNIT_GAP + COVERAGE_GAP + REVISION_GAP + LEGAL_GAP + RATE_POLICY_GAP` |
| **VNDIRECT finfo — bonus share** | Same JSON route and bounded one-page observation; `KINDDIV` was observed as an **unqualified** separate route filter/row kind with the same broad field family. | `KINDDIV` is not promoted to `BONUS_SHARE` without a same-owner semantic definition and response-backed issuer/event proof. A free-text note or a code guessed from prior research is insufficient. | Same unproven effective-date, record-date, ratio orientation, fractional-entitlement, and revision axes. | Same unproven full-window and page/revision axes. A current total cannot be converted into exact requested-span coverage. | Same content-signal/terms/support and no redistribution grant posture. | `SOURCE_GAP`: `IDENTITY_GAP + EVENT_TYPE_GAP + EFFECTIVE_DATE_GAP + RATIO_UNIT_GAP + COVERAGE_GAP + REVISION_GAP + LEGAL_GAP + RATE_POLICY_GAP` |
| **HOSE issuer disclosure** | A strict HTTPS GET to the official issuer-disclosure path returned HTTP 200 with `text/html`; the bounded response was an application shell and did not expose an accepted structured event envelope. No guessed API, login route, browser challenge bypass, or article crawl was used. | Official ownership is not a response-backed per-event identity/schema contract. | No accepted ex/effective field, ratio unit, or event-kind mapping. | No accepted page/total/cursor, historical retention, or exact-window coverage contract. | No route-specific public API/reuse terms were established. | `NOT_SERVED`: `TRANSPORT_INCONCLUSIVE + SCHEMA_DRIFT + COVERAGE_GAP + LEGAL_GAP + RATE_POLICY_GAP` |
| **HNX listed / UPCoM disclosure** | Strict certificate verification failed for one bounded GET to each official listed and UPCoM disclosure route on 23 August 2026. No insecure `-k` retry, redirect follow, page loop, or body claim was made. | No response-backed issuer/event identity was admitted. | No date, ratio, or kind evidence was admitted. | No pagination or exact-window evidence was admitted. | Official ownership alone is not an automation or redistribution grant. | `NOT_SERVED`: `TRANSPORT_INCONCLUSIVE + IDENTITY_GAP + EVENT_TYPE_GAP + COVERAGE_GAP + LEGAL_GAP + RATE_POLICY_GAP` |

### Reproducible route and response ledger

The following route inventory is the exact bounded shape used for the 23 August 2026 observations.
Parameters are listed separately so no query-bearing URL is committed. Contact details were read from
the official home-page navigation and do not represent a separate contact dispatch; therefore the
VSDC direct-probe total below is seven, not eight. A route is not qualified merely because this
inventory makes it reproducible.

| Candidate/role | Method and canonical host/path | Non-secret request parameters/body | Response/MIME and redirect | Auth/session/browser/WAF boundary | Probe result |
|---|---|---|---|---|---|
| VSDC search | `GET https://vsd.vn/vi/search` | `text`, `type`, `obj`, `buss`, `fdate`, `tdate`; the bounded observation used a non-empty symbol and rights filter | HTTP 200, exact `text/html; charset=utf-8`, no redirect; page is HTML | No login/key; browser-like UA; no related-list token/cookie reuse in this probe; the page's observed first-party POST flow is not treated as a public API | Identity/search hint only; no page walk or absence claim |
| VSDC security identity | `GET https://vsd.vn/vi/s-detail/{numeric_id}` | Numeric detail identifier from the official page | HTTP 200, exact `text/html; charset=utf-8`, no redirect | No login/key; browser-like UA; no token reuse | Identity fields observed; related rights route remains unqualified |
| VSDC announcement detail | `GET https://vsd.vn/vi/ad/{numeric_id}` | Numeric announcement identifier from an official link | HTTP 200, exact `text/html; charset=utf-8`, no redirect | No login/key; browser-like UA; no attachment fetch | Notice identity/record-date fields observed; no ex/effective proof |
| VSDC rights calendar | `GET https://vsd.vn/vi/lich-giao-dich` | `tab=LICH_THQ` | HTTP 200 with empty body in this strict observation; not interpreted as empty data | No login/key; no retry or alternate route | `TRANSPORT_INCONCLUSIVE`; not used as a source |
| VSDC legal/contact/robots | `GET https://vsd.vn/vi/lel`, `GET https://vsd.vn/vi/`, and `GET https://vsd.vn/robots.txt` | None | Legal/home HTML returned 200; robots returned a redirect and no usable MIME | No login/key; contact details were read from official home navigation only | Ownership/contact evidence, not permission |
| VNDIRECT events | `GET https://api-finfo.vndirect.com.vn/v4/events` | `q` with code/type/locale predicates; `size`, `sort`, optional `page`; no key/cookie/body | HTTP 200, `application/json`, no redirect; envelope fields `data`, `currentPage`, `size`, `totalElements`, `totalPages` | No login/key/cookie observed; browser-like UA; no WAF/interstitial observed | One page each for the two unqualified kind filters; no history crawl |
| VNDIRECT terms/support | `GET https://www.vndirect.com.vn/dieu-khoan-su-dung/` and `GET https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/` | None | HTTP 403, HTML body not read; no permission conclusion | No bypass, retry, or alternate path | Legal posture remains unresolved |
| HOSE issuer disclosure | `GET https://www.hsx.vn/vi/tin-tuc/tin-to-chuc-niem-yet` | None | HTTP 200, `text/html`; application shell, no accepted event envelope | No login/API guess/browser bypass | `SCHEMA_DRIFT`/not served |
| HNX listed and UPCoM disclosure | `GET https://www.hnx.vn/en-gb/thong-tin-cong-bo-ny-hnx.html` and `GET https://www.hnx.vn/en-gb/thong-tin-cong-bo-up-hnx.html` | None | Strict TLS certificate-chain failure before status/MIME/body | No `-k`, proxy, redirect follow, or retry | `TRANSPORT_INCONCLUSIVE`/not served |

The VSDC contact URL rendered by the site's navigation is intentionally not copied here because its
opaque percent-encoded path is not a stable data-route identifier. The official home page is the real
owner contact path for a later written-permission request.

### Kind-specific decision

The existence of official notices for both kinds is not enough to qualify a machine source. The
kind cells remain independent:

| Normalized kind | Minimum admissible provider proof | Current result |
|---|---|---|
| `STOCK_DIVIDEND` | Same-owner stable token or schema says the event is a dividend paid in newly issued shares; response echoes symbol/issuer; exact ratio orientation and response-backed ex/effective date are present; identity, pages, revisions, rights, and requested-window coverage pass. | `SOURCE_GAP` |
| `BONUS_SHARE` | Same-owner stable token or schema says the event is a free/capital-from-equity bonus issue; response echoes symbol/issuer; exact ratio orientation and response-backed ex/effective date are present; identity, pages, revisions, rights, and requested-window coverage pass. | `SOURCE_GAP` |

No cross-source mapping is allowed: VSDC notice wording cannot define a VNDIRECT token, and a
VNDIRECT row cannot fill a missing VSDC date or revision field.

## Response-backed identity, dates, and units

### Identity contract required before qualification

A future qualified unit must prove the requested canonical symbol and legal issuer from the same
response family. The minimum evidence is:

- requested symbol, provider symbol, legal issuer name, exchange/venue, and ISIN (or a documented
  owner-equivalent) agree without fuzzy matching;
- the provider event ID is stable and owner-issued, not a URL hash, local ordinal, title hash, or
  query ticker;
- the event-kind token is an allow-listed provider value with same-owner meaning;
- the announcement/event route is bound to the row that produced the identity, not merely discovered
  by a global search or matching title; and
- a rename, duplicate locale, multi-instrument, wrong-issuer, missing-ID, or conflicting-identity
  response fails closed.

For VNDIRECT, `id`/`code`/`type` are observed fields, not yet a complete identity or revision
contract. For VSDC, a numeric announcement ID and a title/link are not sufficient without the
announcement's own issuer/ticker/ISIN fields and a route-to-row binding.

### Ex/effective-date contract

The public event model may only expose `ex_date` when the provider response explicitly declares an
ex/effective date and the owner documentation fixes its meaning. The following are **not** admissible
substitutes:

- VSDC `Ngày đăng ký cuối cùng` (record date);
- announcement or disclosure date;
- pay/actual date;
- retrieval time;
- a date-only field interpreted as midnight UTC; or
- a calculated prior trading day, even if an official explanatory page describes the market rule.

The date is accepted only after inclusive bound filtering against that provider-backed date. A missing,
ambiguous, inferred, timezone-unclear, or semantically disputed date yields `EFFECTIVE_DATE_GAP`; it
never becomes a row with `None` for a required ex-date.

### Shares-per-100 contract

The normalized unit is **new shares per 100 existing shares**, not cash percent-of-par. A future source
must publish either this unit directly or an explicitly labelled owned-shares:new-shares ratio whose
orientation and rounding rule are provider-backed. A deterministic conversion is permitted only after
that proof.

Synthetic examples only:

- provider-labelled `20:1` (20 held for 1 new) converts to `5` new shares per 100;
- provider-labelled `100:6.25` converts to `6.25` new shares per 100.

The implementation must use an exact finite decimal/rational representation, reject zero, negative,
non-finite, ambiguous-orientation, percent-of-par, and cash-amount inputs, and preserve any provider
rounding/fractional-entitlement rule as metadata. It must not infer stock/bonus kind or ratio from a
free-text note, price adjustment, or a cash dividend.

## Coverage and no-false-absence contract

Coverage is evaluated separately for `STOCK_DIVIDEND` and `BONUS_SHARE` and is always relative to the
inclusive request `2018-08-13..2026-08-19`.

| Status | Executable meaning | Allowed output |
|---|---|---|
| `FULL` | Provider-declared complete history for the exact window; first/last pages, totals/cursors, boundaries, duplicates, locale variants, and revisions reconcile; no capped or skipped page remains. | Rows may be returned only with a non-null response-backed ex/effective date and exact kind/unit. |
| `PARTIAL` | Provider explicitly declares a bounded partial interval or the design proves a boundary, but the requested window is not complete. | Only a typed partial result may be returned later; it must expose served bounds and cannot claim absence/full coverage. |
| `UNKNOWN` | Rows or an empty page were observed but the provider has not proved the requested boundaries/total/absence semantics. | No confirmed empty result; future public facade must return typed diagnostics, not `[]` as proof. |
| `NOT_SERVED` | No admissible no-login source route, or a transport/auth/legal gate prevents use. | No events and a bounded source-gap diagnostic. |

A provider-declared empty result is confirmed empty only when the same qualified unit proves exact
symbol identity, complete pagination, complete requested-window coverage, and an owner-backed empty
semantics. Search misses, empty HTML tables, an empty JSON page, a bounded page cap, an HTTP/TLS
failure, a generic HTML page, or a missing event-kind row are never evidence that no event exists.

### Pagination and revision rules

A future route adapter must:

1. reject page zero, negative pages, changing totals, missing page metadata, and page responses whose
   requested page does not match the response page;
2. reconcile every page/cursor from the provider-declared first page through the final page, with no
   guessed page size or hidden page cap;
3. deduplicate only identical rows with the same owner event ID and revision; conflicting rows with
   the same ID fail closed;
4. require a provider revision/update/cancellation rule before replacing a prior event; “keep first”
   and “keep last” are not revision policies; and
5. return `UNKNOWN`/`PARTIAL` diagnostics rather than silently dropping an unreconciled page.

VSDC's observed HTML/first-party AJAX controls and VNDIRECT's observed JSON totals are technical
observations only. Neither is a qualified complete-history contract for the requested window.

## Legal, reuse, and operational posture

### VSDC

VSDC is the first-party owner of `vsd.vn`, and official notices are technically reachable without an
account in the bounded probe. That proves neither permission nor redistribution rights. The inspected
[legal/rules section](https://vsd.vn/vi/lel), [official home/contact navigation](https://vsd.vn/vi/),
[search page](https://vsd.vn/vi/search), and notice pages did not publish a machine-readable API
licence or a grant to automate, cache, derive normalized events, or redistribute output. The
`https://vsd.vn/robots.txt` probe returned a redirect to a soft-not-found path; that is not permission.

Written VSDC owner clearance would have to cover the exact route family, session/token and cookie
mechanism if any, request frequency/concurrency/retries, response retention/cache, derived
`ShareDistributionEvent` rows, attribution, and caller-facing redistribution. Until then, the new share-distribution VSDC chain remains empty. #215 neither qualifies nor grants legal clearance to the existing cash adapter.

### VNDIRECT

The official finfo event route is technically no-login in the bounded probe, but the official
[API content signals](https://api-finfo.vndirect.com.vn/robots.txt) are limited to content-signal
semantics (`search=yes, ai-train=no, use=reference`) and do not grant this library financial-row
automation, storage, or redistribution rights. The official DStock page identifies VNDIRECT copyright
and describes data as reference information: [DStock](https://dstock.vndirect.com.vn/). The official
support article says the rights feature is accessed in the DStock application after login and uses a
limited expected-execution-date lookup; this does not establish the public finfo history route's
ex-date or archive semantics. Direct terms/support probes returned HTTP 403 on 23 August 2026; no
content-level conclusion is made from those responses.

Written VNDIRECT permission would have to identify the exact `/v4/events` route, automated access,
rate/concurrency/retry, caching/retention, attribution, normalized derived rows, and redistribution.
No such grant was found in the inspected official material.

### HOSE and HNX

The official exchange routes establish owner candidates but did not provide an accepted structured
no-login event contract or a reuse grant in this bounded pass. HNX strict TLS-chain failure means no
body, MIME, identity, coverage, or absence claim is admitted. The HOSE response was an HTML
application shell without an accepted event envelope. No proxy, browser challenge bypass, or insecure
certificate bypass is allowed.

## Bounded direct-probe ledger

Each entry below is one logical route observation and one physical network dispatch. No retry was
used. These counts describe this research pass only and must not be read as source row counts,
coverage counts, or a provider rate limit.

| Candidate/role | Logical | Physical | Observed result | Boundary |
|---|---:|---:|---|---|
| VSDC home, search, security detail, announcement, rights-calendar, legal, robots | 7 | 7 | Four HTML identity/notice surfaces were HTTP 200 with exact HTML MIME; rights-calendar body was empty; robots redirected. Contact details came from home navigation, not a separate dispatch. | No related-list POST, page walk, token reuse, or announcement crawl. |
| VNDIRECT event route, stock-dividend filter | 1 | 1 | HTTP 200 JSON; page metadata and typed field names observed; no row values retained. | One page only; no historical crawl. |
| VNDIRECT event route, bonus-share filter | 1 | 1 | HTTP 200 JSON; page metadata and typed field names observed; no row values retained. | One page only; no historical crawl. |
| VNDIRECT robots | 1 | 1 | HTTP 200 text; content signals reviewed. | No permission inferred beyond the text's narrow signal semantics. |
| VNDIRECT terms lead | 1 | 1 | HTTP 403; body not read. | No terms conclusion. |
| VNDIRECT support lead | 1 | 1 | HTTP 403; body not read. | No support/permission conclusion. |
| HOSE issuer-disclosure route | 1 | 1 | HTTP 200 HTML application shell; no event envelope accepted. | No guessed API or article fetch. |
| HNX listed-disclosure route | 1 | 1 | Strict certificate-chain failure. | No insecure retry or response claim. |
| HNX UPCoM-disclosure route | 1 | 1 | Strict certificate-chain failure. | No insecure retry or response claim. |
| **Total direct probes** | **15** | **15** | **Bounded source-vetting observations only.** | **No source is enabled.** |

The web-search/source-reading pass is separate from this direct-dispatch ledger. No provider page
crawl was performed after a candidate failed its source/legal gate.

## Reopen evidence required

A future design review may reopen a candidate only when all axes below pass for the same owner and
route set, separately for each event kind:

1. **Owner/legal:** written permission covers no-login automation, exact paths, cookies/tokens,
   retries/rate/concurrency, cache/retention, attribution, derived rows, and redistribution.
2. **Route/MIME:** versioned method/path/parameter/body contract; exact normalized MIME; no redirect,
   generic maintenance HTML, login page, or TLS bypass accepted as data.
3. **Identity:** response-backed requested symbol, legal issuer, venue, ISIN/equivalent, stable owner
   event ID, and kind token; all mismatches and duplicates fail closed.
4. **Dates:** explicit response-backed ex/effective date with documented meaning; record/publish/pay
   dates remain separate; no inferred date or UTC/session assumption.
5. **Units:** provider-backed stock/bonus kind, exact `shares_per_100`, ratio orientation, fraction,
   rounding, and cancellation semantics.
6. **Coverage:** exact `2018-08-13..2026-08-19` full/partial/unknown result, first/last served
   boundaries, all-page totals/cursors, duplicate/revision reconciliation, and a typed empty result
   only when the source proves absence.
7. **Budget:** a later qualified-source design defines finite logical/physical/page/retry/byte
   ceilings; one-source sequential execution, atomic reservation, deterministic exhaustion, and
   preserved sanitized attempts pass synthetic RED tests after a separate design PASS. No numeric
   ceiling is frozen by this source-gap packet.
8. **Merged gates:** current cash VSDC tests/docs/API snapshots remain unchanged; no provider payload,
   credential, token, cookie, query-bearing URL, or live value enters the repository; blacklist and
   secret gates remain clean.

## Source list

All sources below are official/provider-owned primary pages. URLs are canonical paths without query
strings; observed request parameters are described in prose only.

- [VSDC home](https://vsd.vn/vi/)
- [VSDC search](https://vsd.vn/vi/search)
- [VSDC security detail](https://vsd.vn/vi/s-detail/166)
- [VSDC announcement example](https://vsd.vn/vi/ad/195957)
- [VSDC stock-dividend notice](https://vsd.vn/vi/ad/197036)
- [VSDC bonus/capital-from-equity notice](https://web.vsd.vn/vi/ad1/199049)
- [VSDC older bonus-share notice](https://vsd.vn/vi/ad/144935)
- [VSDC rights-date explanation](https://web.vsd.vn/vi/ad/195688)
- [VSDC legal/rules](https://vsd.vn/vi/lel)
- [VSDC home and contact navigation](https://vsd.vn/vi/)
- [VSDC rights calendar](https://vsd.vn/vi/lich-giao-dich)
- [VNDIRECT finfo event route](https://api-finfo.vndirect.com.vn/v4/events)
- [VNDIRECT API content signals](https://api-finfo.vndirect.com.vn/robots.txt)
- [VNDIRECT rights-search guidance](https://support.vndirect.com.vn/hc/vi/articles/32244485001753-H%C6%B0%E1%BB%9Bng-d%E1%BA%ABn-tra-c%E1%BB%A9u-quy%E1%BB%81n)
- [VNDIRECT DStock](https://dstock.vndirect.com.vn/)
- [VNDIRECT terms lead](https://www.vndirect.com.vn/dieu-khoan-su-dung/)
- [VNDIRECT support lead](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/)
- [HOSE issuer-disclosure route](https://www.hsx.vn/vi/tin-tuc/tin-to-chuc-niem-yet)
- [HNX listed-disclosure route](https://www.hnx.vn/en-gb/thong-tin-cong-bo-ny-hnx.html)
- [HNX UPCoM-disclosure route](https://www.hnx.vn/en-gb/thong-tin-cong-bo-up-hnx.html)

## Final source-gap statement

This report does not claim that VSDC, VNDIRECT, HOSE, or HNX lack stock-dividend or bonus-share
records. It records that no one candidate currently satisfies the legal, route, identity, date,
unit, revision, coverage, and budget gate as one lawful no-login history source. The only safe current
state is `SOURCE-GAP CLOSURE`, with the new chain empty and the cash-only VSDC surface preserved.
