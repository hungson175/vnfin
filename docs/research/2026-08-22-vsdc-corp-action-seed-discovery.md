# VSDC corporate-action seed-discovery source vetting

**Date:** 22/08/2026 (Vietnam time, UTC+7)
**Owner:** `vnfin-oss`
**Issue:** #203 — corporate-action seed discovery
**Status:** research only; no new C1-C3 source is enabled; legacy C4 remains active and no production code is authorized

## Clean-room and evidence boundary

This report is a clean-room review of first-party VSDC material only. The mandatory repository
blacklist was applied before every search; excluded repositories, packages, sites, endpoint maps,
schemas, and derived material were not searched, opened, cited, or used. Search results were
restricted to official `vsd.vn` pages and the negative exclusions required by the repository policy.
The probes used ordinary HTTPS requests, a strict certificate verifier, no login, no browser session,
no paid key, no proxy, and synthetic parser reasoning. Any route discovered from first-party inline
JavaScript is marked **observed first-party route**, not a published API contract.

The observations below are a snapshot taken on 22/08/2026. A reachable page is not evidence of a
licence, a redistribution grant, complete historical coverage, or permission to automate it.

## Executive disposition

VSDC exposes technically reachable, no-login HTML pages that can be investigated for corporate-action
seed discovery:

1. the official search page can find announcement links and security-detail links;
2. an issuer/security detail page carries a strong response-backed ticker/issuer identity and embeds
   a related-rights listing route; and
3. an announcement page carries a second response-backed identity check.

The strongest *new* technical candidate is the issuer-detail → rights-list route (`C2` below), not a
blind numeric-ID scan. C1-C3 are **not enabled**. The merged runtime still performs the legacy C4
numeric scan when no explicit seed is supplied; that scan is bounded and non-authoritative and is
preserved for compatibility. The inspected official pages expose no public machine-readable data
licence or redistribution grant, the related-list routes are only observed from first-party
JavaScript, and provider rate/concurrency/retention terms were not disclosed. The lawful engineering
disposition is therefore:

> **`NO_SOURCE_ENABLED / SOURCE_GAP_LEGAL_AND_CONTRACT`** — preserve the existing explicit-seed
> adapter path and legacy C4 behavior, keep the new C1-C3 chain empty, record bounded discovery as
> source-gap evidence only, and require written VSDC owner clearance plus a new design gate before
> any new runtime discovery request or public claim.

### Current merged-runtime truth

The shipped no-seed adapter path is not empty: with no `seed_id`, it scans downward from `latest_id`
over `min(max_fetch, DEFAULT_MAX_FETCH)` numeric announcement IDs, then runs the existing
same-organisation BFS when a seed is found. `max_fetch` remains the caller's existing positive-int
parameter; this report does not redefine its range or physical-request meaning. The result retains
the existing `corp_action_source_partial`, `corp_action_seed_not_found`,
`coverage_truncated_at_max_fetch`, and bounded-count `corp_action_fetch_incomplete` behavior. This
research does not authorize changing that runtime contract.

## 1. Official owner and route inventory

The [official VSDC home page](https://vsd.vn/vi/) identifies the Vietnamese Securities Depository
and Clearing Corporation and describes securities registration and rights-execution services. The
site footer states that copyright belongs to VSDC. That establishes first-party ownership of the
host, not an open-data or redistribution licence.

### 1.1 Candidate matrix

| ID | Candidate and exact request shape | Response-backed identity | Coverage / pagination evidence | Technical disposition | Legal / reuse disposition |
|---|---|---|---|---|---|
| C1 | `GET https://vsd.vn/vi/search?text={encoded_symbol}&type=4&obj=0&buss=11021&fdate={from}&tdate={to}`; page 1 is HTML. Subsequent pages use `POST` to the same URL with `Content-Type: application/json;charset=utf-8` and `{"SearchKey":4,"CurrentPage":N}` after the page's ephemeral `__VPToken` is acquired. | Search results are hints only. The result title or fuzzy text is not sufficient; each `/vi/ad/{id}` must be checked against the announcement's ticker, issuer, ISIN, and required fields. | A current rights-filter probe returned 20 links and a server count. Page 2 was returned by the JSON POST, not by a GET `page=` query. Empty and fuzzy results are valid HTML but do not prove issuer coverage or absence. | **Technically promising, non-authoritative, fuzzy.** Blank text must be rejected because it produces a broad global list. | No public automation, caching, or redistribution grant found; written permission required. |
| C2 | `GET https://vsd.vn/vi/search?text={encoded_symbol}&type=5...` to locate security details, then `GET https://vsd.vn/vi/s-detail/{numeric_id}`. The detail page's first-party script posts `{"SearchKey":"{numeric_id}","CurrentPage":N,"RecordOnPage":10}` to `https://vsd.vn/isuisser-thq/search`. | The detail page returns the registered organisation, security name, exact ticker, ISIN when available, security type, and trading venue. The related-rights rows are accepted only after this exact identity anchor. | The FPT example exposed related-rights page controls and seven observed pages. The route is HTML, page-numbered, and must be traversed only to the server-declared bound. Missing or malformed controls are schema drift. | **Strongest technical candidate; observed first-party route only.** | No public route contract or reuse grant found; written permission and owner confirmation required. |
| C3 | Same issuer detail anchor, then the observed first-party `POST https://vsd.vn/isuisser-tcdk/search` with the same JSON paging shape. | The issuer detail identity is usable; each news row still needs announcement-level identity validation. | Broader issuer-news results are noisier than the rights list; page bounds and route shape must be validated independently. | **Fallback candidate only; not a substitute for rights coverage.** | Same unresolved permission and contract posture as C2. |
| C4 | Existing bounded recent numeric-ID scan against `GET https://vsd.vn/vi/ad/{id}`. | An ID alone is not issuer identity. Each response would need the announcement identity check. | A numeric window has no proof that IDs are contiguous, that all relevant announcements are present, or that the requested date range is covered. | **Active legacy fallback, non-authoritative.** Preserve it; do not present it as reliable new discovery. | No licence or permission evidence; no new C4 capability is enabled. |

`type=4` is the observed search-page value for news and `buss=11021` is the observed value for
rights execution. `type=5` is the observed security-code search value. These values come from the
first-party search UI and script, not a versioned developer specification.

### 1.1.1 Additional first-party facilities considered

The following official facilities were also inspected. They are recorded so that a later source
review does not mistake an omitted route for an unsearched route, but none is added to the current
source chain:

| Facility | Observation | Why it is not an enabled source |
|---|---|---|
| `POST https://vsd.vn/search-suggest` with `{"text":"{symbol}","type":"5"}` | First-party JavaScript returns JSON suggestions containing security-detail hrefs. The response can report `success: 0` while still carrying a populated `data` list; no-match responses have no usable candidate. | One hint request has no pagination or total and is not identity/coverage proof. It may only replace, never strengthen, a bounded resolver in a future gate. |
| `GET /vi/lich-giao-dich?tab=LICH_THQ...` plus `POST /lich-thq/search` | First-party page/script submits `SearchKey`, `CurrentPage`, `RecordOnPage`, `OrderBy`, and `OrderType`. The rights-calendar response carries code/ISIN/title/record-date/link fields. | A substring query for `FPT` mixed `FPT`, `CFPT`, `FOX`, `FTS`, and `FRT`; it needs exact-code filtering and independent announcement identity. It has no current owner-backed completeness contract. |
| `GET /vi/id/{issuer_id}` plus `POST /danh-sach-ck/search` | Issuer detail identifies the legal issuer and lists securities; the issuer example's current related-rights section was empty. | Useful corroboration only, not a corporate-action seed source. It cannot establish event coverage. |
| `GET /vi/alo/ISSUER` and `GET /vi/alc/6` | Broad issuer/category announcement lists return HTML and expose page controls. | They are category-wide crawls, not symbol-scoped coverage. They would increase request cost and false-absence risk without an issuer/date proof. |

The observed suggestion and calendar endpoints are therefore **conditional hints**, not replacements
for the response-backed C2 identity anchor. Their route shapes, exact field semantics, legal posture,
and operational limits would need their own source-gate evidence before use.

### 1.2 Search page observations

The [official VSDC search page](https://vsd.vn/vi/search) exposes the following UI choices and
request behavior:

- simple search redirects to `/search?text=...`;
- advanced search composes `text`, `type`, `obj`, `buss`, `fdate`, and `tdate` query parameters;
- page 1 is a server-rendered HTML response;
- pagination is an AJAX `POST` to the same path and query string, with JSON `SearchKey` and
  `CurrentPage` fields;
- the site script copies an ephemeral `__VPToken` meta value to the request header. This token is a
  session/request control, not a reason to treat the route as authenticated or licensed;
- result links observed in the news search are `/vi/ad/{numeric_id}`.

A probe using a non-empty FPT query and the rights filter returned a valid page with 20 results and a
server-reported total. A second page returned older VSDC announcement links. A search for an
unmatched code returned a valid search section with an empty list. A blank `text=` query returned a
large global list. Therefore:

- result text is fuzzy and can include a related code; exact response identity is mandatory;
- an empty search list is not a confirmed empty corporate-action result;
- blank symbol input is a preflight error and must never become a global crawl;
- page 2 is not a GET fallback and must not be guessed when page metadata is absent.

### 1.3 Issuer/security detail observations

The [official FPT security detail example](https://vsd.vn/vi/s-detail/166) returned a server-rendered
HTML page with these identity fields in one response:

- registered organisation name;
- security name;
- exact security code `FPT`;
- ISIN `VN000000FPT1`;
- security type (share);
- trading venue (`HOSE`); and
- registration and VSDC-management fields.

The same page includes related issuer-news and rights controls. The rights request observed in the
page script is:

```text
POST https://vsd.vn/isuisser-thq/search
Content-Type: application/json;charset=utf-8
{"SearchKey":"166","CurrentPage":2,"RecordOnPage":10}
```

The response is an HTML table with the observed headings `STT`, `Ngày đăng ký cuối cùng`, and
`Tên quyền`, plus links whose relative path was `/ad/{id}`. The issuer-news route uses the same
paging shape. A canonical fetch must construct `/vi/ad/{id}` from the numeric ID and must not follow
a redirect from `/ad/{id}`.

The exact FPT page controls showed 20 issuer-news pages and seven rights pages at probe time. Those
numbers are observations, not a coverage promise or a stable API contract.

### 1.4 Announcement observations and identity binding

The [official VSDC announcement example](https://vsd.vn/vi/ad/195957) returned a server-rendered HTML
page titled for an FPT cash-dividend notice. The response included the registered organisation,
security name, ticker, ISIN, record-date/right fields, and event text. A future seed validator must
require the canonical route plus this response-backed identity; a title, link text, numeric ID, or
sidebar relation alone is insufficient.

Semantic validation is required even after HTTP 200: sampled invalid numeric announcement IDs
returned an official empty/removed-article page with no usable title or identity fields. Such a
response is `schema_or_identity_drift` or `valid_non_target`, never a valid seed and never proof of
absence. An anonymous related-list `POST` without the matching page cookie and `__VPToken` header
returned HTTP 400 with an empty body; that is a token/transport contract failure, not an empty list.

The canonical route returned HTTP 200. The same numeric route without the locale prefix,
`https://vsd.vn/ad/195957`, returned HTTP 302 to `/vi/ad/195957`; redirects are not accepted as a
successful seed fetch. Redirects can hide host/path drift and are classified as source-unavailable
or route-drift diagnostics, not as a valid response.

## 2. Transport, schema, and reachability evidence

### 2.1 HTTPS and redirect policy

The successful probes used strict HTTPS-only transport equivalent to:

```text
--proto '=https' --proto-redir '=https' --max-redirs 0
```

No insecure certificate bypass was used. The successful canonical search, detail, and announcement
pages returned HTTP 200. The non-locale announcement path returned a redirect and the HTTP scheme
probe did not provide an acceptable canonical source. The future client must require:

- scheme `https`, host exactly `vsd.vn`, default port 443, and an allow-listed path;
- verified certificate chain, with TLS errors fail-closed;
- no redirect, including same-host locale redirects; and
- one exact response, not a browser-rendered or login-interstitial substitute.

These are probe results from one environment, not a claim that VSDC's service is globally available.

### 2.2 MIME and HTML shape

The successful pages reported `Content-Type: text/html; charset=utf-8`. The future validator must
parse the complete header value after the first header colon, trim only permitted outer whitespace,
normalize ASCII case for comparison, and require exactly `text/html; charset=utf-8`. A value such as
`text/html; charset=utf-8:unexpected`, a duplicate content-type header, missing header, or any other
parameter is rejected. This is deliberately stricter than checking only the media-type prefix.

Each route has a distinct shape contract:

- search `type=4`: the news section, result-list shape, and announcement links must be present;
- search `type=5`: the security-code section and security-detail link shape must be present;
- issuer detail: the identity labels and their values must be present in a coherent page;
- rights list: the exact rights table headings, page metadata, and row-link shape must be present;
- announcement: the identity labels and corporate-action fields must be present.

A generic maintenance page, error page, login page, or HTML with only a matching title is not a
valid empty response. A route-specific declared empty list may be recorded as a bounded search result,
but never as confirmed issuer/date coverage without an owner-backed coverage contract.

The sampled pages also returned `Cache-Control: no-cache, no-store` and `Pragma: no-cache`. These
headers are technical cache directives, not a licence or a complete prohibition; they strengthen the
case for written owner terms rather than answering the legal question.

### 2.3 Token, cookie, and no-login boundary

The observed related-list calls use a session cookie and the `__VPToken` supplied by a preceding
GET. The flow is still no-login in the observed sense: no account, password, paid key, or bearer
credential was supplied. This does not establish permission to automate the flow. A future runtime,
if ever approved, would acquire the ephemeral token at runtime, keep it in process memory, redact it
from logs/diagnostics, and never put it in fixtures, a cache snapshot, or a redistributed artifact.

### 2.4 Errors and negative probes

The following negative evidence is binding for the design, not a claim about every possible VSDC
response:

- blank search text produces a broad global list and is rejected before network;
- unmatched search text produces a valid empty result section but no issuer/date proof;
- `/ad/{id}` redirects to `/vi/ad/{id}` and is not followed;
- HTTP and certificate failures are transport/source failures, not empty data;
- missing route headings, malformed page bounds, conflicting identity, wrong MIME, or a maintenance
  page are schema/identity drift, not no-seed evidence;
- an empty related-rights table without an owner-backed coverage marker is bounded exhaustion, not
  confirmed empty.

## 3. Legal, terms, and operational posture

The [official VSDC contact page](https://vsd.vn/vi/ads/tAPN%34%47ez%35anGD%38ztNn%37I_w) provides real contact
paths, including the Hanoi office at `112 Hoàng Quốc Việt`, the general phone `(+84.24) 3 9747 123`,
the hotline `024 3978 5669`, and an IT contact at `0243 974 7125`. These are the correct owner
routes for a written data-access/licensing question. The footer's webmail link is a login surface,
not a no-login data source.

The [official robots path](https://vsd.vn/robots.txt) redirected to a VSDC not-found path during the
probe; no usable robots policy was observed. A missing/redirecting robots document is not permission.
The inspected home, search, detail, announcement, and contact pages did not publish a machine-readable
open-data licence or a grant to cache, derive, or redistribute data. This is a bounded negative
observation, not legal advice. The status is:

```text
legal_status = UNRESOLVED_PERMISSION_REQUIRED
runtime_status = NO_RUNTIME_REQUESTS_AUTHORIZED
redistribution_status = NOT_GRANTED
```

The official [VSDC legal/rules section](https://vsd.vn/vi/lel) publishes laws, rules, and fee
decisions, but the inspected material did not publish a public API licence or redistribution grant.
The [robots path](https://vsd.vn/robots.txt) and sitemap path similarly redirected to soft-not-found
HTML rather than providing a machine-readable crawl policy; neither absence is permission.

Written owner permission would need to cover automated runtime fetches, the session token/cookie
mechanism, request frequency and concurrency, cache duration, derived normalized event rows,
attribution, and redistribution to library users. Until that is obtained, the source chain remains
empty. No rate, concurrency, SLA, or retention limit was documented in the inspected pages or inline
scripts. The design therefore recommends sequential requests, one in-flight request, a 250 ms minimum
inter-request delay, a 25-second per-request timeout, and one retry maximum for retryable transport
failures. These are conservative library policies, not provider guarantees.

## 4. Coverage and identity conclusion

C2 is the only candidate with a practical response-backed identity anchor before seed acceptance.
C1 and C3 can discover hints, but their links cannot establish that the requested symbol owns the
announcement. C4 supplies neither identity nor coverage.

No candidate currently proves all of the following at once:

1. a documented, reusable, no-login route contract;
2. exact issuer/security identity for every candidate and seed;
3. complete rights coverage over an arbitrary requested date range;
4. deterministic pagination and empty-result semantics;
5. permitted runtime fetching, caching, derived-output redistribution, and attribution; and
6. stable operational limits compatible with a public OSS client.

Consequently, #203 is a source-gap closure/design artifact. It must not be represented as a working
no-seed discovery implementation and must not turn an empty result into `[]` or a false “no dividend”
claim.

## 5. Reopen criteria

A future source-gate re-review may reopen implementation only when all criteria below are evidenced
for the exact route version:

1. written VSDC owner permission covers runtime fetching, token/cookie use, cache policy, derived
   rows, attribution, and redistribution;
2. VSDC confirms the search/detail/rights/announcement route shapes, identity fields, date meaning,
   pagination bound, empty-result meaning, and acceptable request rate/concurrency;
3. strict TLS verification, HTTPS-only/no-redirect policy, exact MIME validation, and route-specific
   shape probes pass on fresh samples;
4. coverage evidence proves the requested date window or explicitly limits the result to bounded
   discovery; `confirmed_empty` is allowed only under that proof;
5. a synthetic fixture suite proves identity, MIME, pagination, empty/error/drift, exact retry/budget,
   no-call-after-exhaustion, explicit-seed compatibility, and no-false-absence diagnostics; and
6. the design gate approves the note before any production code, source-chain entry, push, or issue
   close.

## Sources

- [VSDC home page](https://vsd.vn/vi/)
- [VSDC search page](https://vsd.vn/vi/search)
- [VSDC issuer/security detail example](https://vsd.vn/vi/s-detail/166)
- [VSDC announcement example](https://vsd.vn/vi/ad/195957)
- [VSDC contact page](https://vsd.vn/vi/ads/tAPN%34%47ez%35anGD%38ztNn%37I_w)
- [VSDC legal/rules section](https://vsd.vn/vi/lel)
- [VSDC rights-calendar page](https://vsd.vn/vi/lich-giao-dich?tab=LICH_THQ)
- [VSDC robots path](https://vsd.vn/robots.txt)

The search/detail route shapes and related-list request bodies are observations of the first-party
HTML/JavaScript served by the linked pages on 22/08/2026, not quotations from a public developer
specification.
