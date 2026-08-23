# Vietnamese company-news source vetting — #211

**Date:** 23 August 2026 (UTC+7)
**Packet:** `/home/hungson175/tools/vnfin-oss-reviewer/tasks/211-vn-company-news-source-spec.md`
**Packet commit:** `44bc597`
**Evidence window:** inclusive `2018-08-13..2026-08-19` (2,929 calendar days)
**Disposition:** **SOURCE-GAP CLOSURE** — no new no-login Vietnamese company-news source qualifies
**Implementation status:** no RED tests, production code, source-chain change, push, or issue closure is authorized

This is a source/legal design artifact only. It does not add a Vietnamese provider, archive,
search index, article-body fetch, sentiment model, signal, automatic fallback, historical
constituent reconstruction, or VN30 news claim.

## 1. Clean-room boundary and decision

The existing `vnfin.news` contract is preserved exactly: `alpha_vantage` remains the explicit
default, Alpha Vantage remains BYOK, missing credentials fail before network, and the current
one-request headline-metadata behavior is not widened. A new provider would require a separate
explicit token and a new exact-SHA design pass; no such token is proposed by this note.

Before this research, `docs/vnstock-blacklist.md` was read. Every web search used the repository's
exact exclusion set:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted or derivative material was opened, cited, compared, installed, or used. Evidence is
limited to official provider/exchange/regulator pages, official terms or contact pages, the
repository's already-committed clean-room source notes, and current source inspection. No search
facade, search-engine snippet, issue text, reporter fixture, guessed endpoint map, raw payload,
article body, live title/snippet, cookie value, screenshot, downloaded result set, or query-bearing
URL is committed here.

**Decision:** no candidate is a `QUALIFIED` or implementation-ready `PARTIAL` source for the
requested no-login Vietnamese issuer/company-news lane. The correct public disposition is
`SOURCE-GAP CLOSURE`, not an empty result, fallback, or “no news” claim.

### 1.1 Qualification unit

One unit must bind all of these to the same owner/provider and route version:

- no-login transport and exact HTTPS host/path/method/MIME/envelope;
- response-backed requested ticker, legal issuer name, exchange, and stable owner identifier;
- owner-declared item ID, canonical URL, publisher identity, title, content kind, and any licensed
  summary;
- `published_at` versus `updated_at`, timezone, precision, provider clock, sort and boundary rules;
- page/cursor/total/revision/deletion behavior and a finite physical-call/retry budget;
- per-symbol requested-window coverage and empty-result meaning;
- sentiment scope/model/version/labels/scale when sentiment is claimed; and
- owner/original-publisher rights for automation, storage, derived rows, caller-facing return,
  attribution, retention/deletion, commercial use, and redistribution.

A public page, an official publication duty, or a reachable HTML response is not by itself a
machine-readable contract or a reuse licence. A provider may be useful for human reference and
still fail this qualification unit.

## 2. Existing API and release boundary

Read-only inspection of current master gives the following facts:

| Axis | Current contract that remains unchanged |
|---|---|
| Default provider | `vnfin.news.source()` and `vnfin.news.search()` default to `provider="alpha_vantage"`. Unknown providers raise `ValueError`. |
| Auth | `api_key=` or `ALPHAVANTAGE_API_KEY`; absent key raises `SourceUnavailable` before network. |
| Alpha request | `GET` to the official Alpha Vantage query route with `function=NEWS_SENTIMENT`, validated tickers/topics/date bounds, `sort`, `limit`, and the caller's key. |
| Alpha limit | Public validation remains `1 <= limit <= 100`; no automatic paging or limit broadening. |
| Result identity | `NewsResult.source`/`NewsItem.source_adapter` identify the adapter; `NewsItem.source` remains the provider publisher. |
| Item boundary | Link plus provider metadata and optional provider-owned overall sentiment only; no article-body fetch, HTML, media, local archive, or vnfin-generated sentiment. |
| Models | Existing frozen `NewsItem` and `NewsResult` fields and the v0.2.0 public snapshot are Tier-0. Any future fields would be trailing/defaulted and separately reviewed. |

The annotated `v0.2.0` tag peels to `2fe50df4f27064140ff9f7a680227a2b337ec74a`. The tag has no
`vnfin/news/` path, so it contains no #211 or #140 news implementation to reproduce. That absence
is a release boundary, not a historical provider/source claim. Current-master behavior above is
separate and is the only live Alpha behavior preserved.

Official Alpha Vantage documentation requires `function=NEWS_SENTIMENT` and `apikey`, documents
optional ticker/topic/time filters, `LATEST`/`EARLIEST`/`RELEVANCE`, and a documented default limit
of 50 with a provider maximum example of 1,000. The repository's public Alpha limit of 100 and
one-request behavior remain narrower compatibility rules. The [official NEWS_SENTIMENT
documentation](https://www.alphavantage.co/documentation/#news-sentiment) does not supply a
Vietnamese exchange/issuer namespace, a per-item legal-issuer/ISIN binding, a stable provider-ID
contract, an authoritative total/cursor/retention contract, or a caller-facing redistribution grant.
The [official Alpha Vantage terms](https://www.alphavantage.co/terms_of_service/) distinguish
personal/non-commercial use from commercial use and grant a revocable, non-sublicensable,
non-transferable platform licence; they do not constitute permission for this new no-login
Vietnamese lane.

## 3. Current-snapshot count-only observation

The SSI observation is a count-only, non-reproducible observation, not an exact or frozen cohort. It
is **not** historical VN30 membership and must not be used to infer membership or issuer coverage in
2018. The observation is retained only as a bounded source-gap fact; no reviewable member manifest,
digest, or private ledger is carried by this artifact.

```text
observation_label         = C211-VN30-current-2026-08-23-count-only
observation_owner         = SSI iBoard current group observation
provider_route            = GET /stock/group/VN30
provider_host             = iboard-query.ssi.com.vn
retrieved_at_utc          = 2026-08-23T04:18:57Z
provider_as_of            = None
http_status               = 200
full_content_type         = application/json; charset=utf-8
normalized_media_type     = application/json
envelope_code             = SUCCESS
row_count                 = 30
unique_symbol_count       = 30
identity_fields_observed  = stockSymbol, exchange, stockType
snapshot_semantics        = current snapshot only; not point-in-time
manifest_status           = not retained; COHORT_IDENTITY_GAP
required_control_count    = 8
```

The 30 member values and any tuple/hash are intentionally not published: the source note records
no provider grant to reproduce or redistribute that derived list. A row count and unique-count
observation do not provide durable content identity. This artifact therefore cannot verify the
membership, order, or symbol-to-cell mapping later; reopening requires a newly authorized,
reviewable manifest supplied by the owner or caller, with its retrieval provenance and digest.

No all-30 historical news crawl was run. That is deliberate: no candidate first passed the
transport/identity/rights gate, and there is no reviewable 30-symbol manifest. A bounded failed,
unserved, or gate-skipped source unit cannot be converted into a per-symbol coverage zero.

## 4. Bounded evidence protocol

The following is a route-level source-vetting observation, not an archive crawl or provider SLA:

| Candidate family | Direct observation boundary | Pagination/retry/body behavior |
|---|---|---|
| Alpha Vantage | Official documentation and terms only; no credential was used for #211 evidence. | No Alpha request was used as no-login evidence. Existing runtime remains one physical request. |
| HNX listed disclosure | A strict HTTPS request was attempted for the named official listed route; certificate-chain failure in the local strict verifier prevented any admissible status, MIME, body, or response-shape evidence. | No insecure TLS bypass, redirect follow, page loop, or article/attachment fetch. |
| HNX UPCoM disclosure | A strict HTTPS request was attempted for the named official UPCoM route; the same certificate-chain failure prevented any admissible response evidence. | No insecure TLS bypass, redirect follow, page loop, or article/attachment fetch. |
| VSDC issuer announcements | One sanitized observation of the official issuer category route and its first-party page controls. | No page `POST`, numeric-ID walk, cookie/token reuse, article route, attachment, or body fetch was made for this report. |
| VSDC general news | One sanitized observation of the official general-news category route. | No page walk, cookie/token reuse, article route, attachment, or body fetch was made for this report. |
| HOSE issuer disclosures | The official issuer-news route was recorded as a candidate owner path; no admissible structured response was retained in this pass. | No guessed API call, login route, browser/challenge bypass, or article fetch was used. |
| HOSE information disclosure | The official information-disclosure route was recorded as a separate candidate owner path; no admissible structured response was retained in this pass. | No guessed API call, login route, browser/challenge bypass, or article fetch was used. |
| SSC | Official regulator/legal material only. | No regulator page was treated as a company-news feed. |
| SSI count observation | One already-retained no-login count observation, summarized above; it has no reviewable member manifest. | No member values, history query, or news crawl was added. |

These observations are intentionally insufficient to prove historical absence. The exact future
budget and atomic scheduler required before any implementation are in
[`tasks/211-design-note.md`](../../tasks/211-design-note.md).

### 4.1 Direct route and shape observations

| Candidate/unit | Owner and route/method/version | Transport, MIME, envelope, session | Response-backed identity and item shape | Time, ordering, pagination, coverage | Sentiment | Legal/runtime disposition |
|---|---|---|---|---|---|---|---|
| Alpha baseline | Alpha Vantage; official `GET /query`; `function=NEWS_SENTIMENT`; documented provider route, no new version selected | API key required; JSON contract documented by provider; not no-login | Provider docs do not establish Vietnamese legal issuer/ISIN binding or a stable owner `provider_id` for this lane. Existing parser preserves publisher `source` separately. | Provider docs describe publication-time filters, sort, and limit; no documented cursor/total/retention/completeness contract for the requested 2,929-day window. | Current fields are provider-owned overall sentiment only; no new Vietnamese ticker-specific lineage is proven. | **NOT_SERVED for #211 candidate lane**; preserve existing BYOK Alpha. |
| HNX listed disclosure | Hanoi Stock Exchange; `GET /en-gb/thong-tin-cong-bo-ny-hnx.html`; candidate owner route, version not published | Strict local TLS-chain verification failed before any admissible status/MIME/body/shape; no `-k` bypass. | No response-backed issuer, item, or provider-ID evidence is admitted from this route. | No date, page, total, ordering, retention, or requested-window evidence is admitted. | No sentiment fields or licensed model lineage. | **TRANSPORT_INCONCLUSIVE**; identity, schema, coverage, legal, and rate posture remain unproven. |
| HNX UPCoM disclosure | Hanoi Stock Exchange; `GET /en-gb/thong-tin-cong-bo-up-hnx.html`; candidate owner route, version not published | Same strict TLS-chain failure; no insecure retry or alternate response source. | No response-backed issuer, item, or provider-ID evidence is admitted from this route. | No date, page, total, ordering, retention, or requested-window evidence is admitted. | None proven. | **TRANSPORT_INCONCLUSIVE**; identity, schema, coverage, legal, and rate posture remain unproven. |
| VSDC issuer announcements | Vietnam Securities Depository and Clearing Corporation; `GET /en/alo/ISSUER`; first-party script observed an HTML-returning `POST` to the same route with a JSON current-page field; no versioned API contract | Direct `GET` returned `200`, full `Content-Type: text/html; charset=utf-8`, normalized `text/html`, and HTML controls. The server sets an ephemeral HttpOnly token cookie and language cookie; no value is retained or reused. | The page is broad issuer/depository news. It exposes title links such as `/en/ad/<numeric-id>` and a row's update time, but a title/ticker prefix or numeric ID alone is not issuer identity. The category includes rights, dividends, bonds, and member/depository notices, not a complete general company-news namespace. | First page observed 15 rows and a displayed 90,311-record total over 6,021 page controls at observation time. `Date update` is not proven `published_at`; page totals, sort, deletions, retention, arbitrary-date semantics, and complete cohort coverage are unproven. | No exact sentiment field, article-vs-ticker scope, model/version, or reuse right. All sentiment remains `None`. | **PARTIAL technical listing only; not a qualified #211 source**: `IDENTITY_GAP + TIME_GAP + COVERAGE_GAP + PAGINATION_GAP + SENTIMENT_GAP + LEGAL_GAP + RATE_POLICY_GAP`. Legacy numeric VSDC C4 from #203 remains active/non-authoritative for its separate corporate-action scope; it is not a new company-news capability. |
| VSDC general news | VSDC; `GET /en/tin-tuc`; official category page | Public HTML page; no login was supplied. It exposes category sections and update times, but no owner-backed API/reuse contract. | Category sections include depository, issuer, member, VSDC and carbon-market news; category/title text is not a complete response-backed issuer identity. | UI filters exist, but no authoritative company-news page/total/coverage contract for the requested window was proven. | None proven. | **NOT_SERVED + IDENTITY_GAP + TIME_GAP + COVERAGE_GAP + LEGAL_GAP + RATE_POLICY_GAP**. |
| FPT issuer-owned disclosure/news | FPT Corporation; official stock identity and public-disclosure/news routes. The disclosure page exposes year controls reaching 2018; the stock page binds FPT Corporation to ticker `FPT`. | Public HTML/sitemap surfaces are reachable without a login, but no stable machine API, owner item ID, or route-specific rate contract was accepted. | Issuer identity is strong for FPT itself, but a single issuer cannot qualify the 30-symbol cohort. URL is not an owner-declared provider ID. | Public dates are update/date values; no source-wide completeness, stable pagination, retention, or publication-time timezone contract was accepted. | No exact provider sentiment lineage. | **PARTIAL issuer reference only + LEGAL_GAP + RATE_POLICY_GAP + PAGINATION_GAP + COVERAGE_GAP**. FPT's terms permit extraction/sharing for personal, non-commercial use with attribution; commercial copying/distribution requires prior written consent, so OSS caller-facing reuse is not authorized. |
| Vingroup issuer-owned disclosure | Vingroup JSC; official investor disclosure page with year/count controls and linked disclosure documents. | Public HTML is reachable without login; no stable metadata API, item-ID contract, rate policy, or reuse grant was accepted. | The page mixes issuer disclosures and instruments such as bonds and VSDC/HOSE notices; a page-level `VIC` association is not enough for every item. | Page numbers and date labels are observations, not a complete 2018–2026 publication contract; publication/update semantics and retention are unproven. | None proven. | **PARTIAL issuer reference only + IDENTITY_GAP + TIME_GAP + LEGAL_GAP + RATE_POLICY_GAP + COVERAGE_GAP**. No new source unit. |
| HOSE issuer disclosures | Ho Chi Minh City Stock Exchange; `GET /vi/tin-tuc/tin-to-chuc-niem-yet`; official public page route | Official page declares a JavaScript application and, in the bounded observation, did not expose a stable data envelope. No login, browser automation, guessed API, or challenge bypass was used. | Issuer-news is an official category, but no response-backed row identity, provider ID, MIME/envelope, or publisher field was accepted. | Date filters are displayed; exact request/page/total/cursor, `Ngày tạo` versus publication meaning, retention, and arbitrary-window coverage are unproven. | None proven. | **TRANSPORT_INCONCLUSIVE + IDENTITY_GAP + TIME_GAP + PAGINATION_GAP + COVERAGE_GAP + LEGAL_GAP + RATE_POLICY_GAP**. |
| HOSE information-disclosure UI | HOSE; `GET /vi/quy-dinh-hose/cong-bo-thong-tin`; official disclosure UI | JS application; no stable no-login response contract accepted. The separate login route is excluded. | No response-backed issuer/item rows were accepted. | Date filter UI is not a completeness contract. | None proven. | **TRANSPORT_INCONCLUSIVE + IDENTITY_GAP + PAGINATION_GAP + COVERAGE_GAP + LEGAL_GAP + RATE_POLICY_GAP**. |
| SSC regulator material | State Securities Commission; official legal/disclosure portal, not a company-news data route | Official legal/publication pages are not a structured issuer-news API. | Regulatory text establishes disclosure obligations, not a returned item/provider-ID/issuer-news contract. | No no-login news route, pagination, historical total, or per-symbol coverage contract was established. | None. | **NOT_SERVED + LEGAL_GAP + PAGINATION_GAP + COVERAGE_GAP**. |
| Issuer-owned IR/news feeds | Many distinct issuers; no single owner, route, schema, version, or bulk contract identified | A public issuer page or RSS link would need its own exact owner permission and stable structured response. | A 30-feed collection would require independent issuer identity, item IDs, rename rules, timing, and rights for every feed; it is not one qualification unit. | No aggregate source can prove the requested cohort/window without a bulk contract. | Unqualified unless each provider supplies exact lineage. | **NOT_SERVED**; thirty one-off scrapers are out of scope, with `LEGAL_GAP + RATE_POLICY_GAP + COVERAGE_GAP`. |
| FiinGroup licensed datafeed | FiinGroup; official product/terms page identifies a commercial licensed-data candidate, but no exact news schema/version is admitted in this report. | Authentication/entitlement, metadata-only projection, rate, and caller-facing redistribution terms for this library were not established. | No exact response-backed issuer/item/provider-ID schema is admitted without a primary schema artifact and written rights. | No accepted no-login route, 30-cell window coverage, page/total/cursor contract, or timezone/retention receipt. | No exact sentiment/reuse lineage accepted. | **LEGAL_GAP + RATE_POLICY_GAP + COVERAGE_GAP + PAGINATION_GAP + IDENTITY_GAP**; licensed lead only, not #211 no-login qualification. |
| GDELT licensed/open metadata | GDELT Project; official terms state released datasets may be used and redistributed with attribution. | Rights are comparatively clear, but the source is a global news metadata system, not a Vietnamese issuer-owned feed; no exact no-login VN issuer contract was accepted for this issue. | Source/article metadata does not establish response-backed Vietnamese ticker/legal-issuer identity, stable owner issuer ID, or original-publisher title rights for every item. | No accepted 30-cell requested-window completeness, issuer-specific pagination/retention, or absence semantics. | No qualified Vietnamese ticker-specific sentiment lineage. | **IDENTITY_GAP + COVERAGE_GAP + PAGINATION_GAP + SENTIMENT_GAP**; no automatic fallback or cross-source normalization. |
| Licensed publisher/aggregator | No named candidate with an explicit reusable no-login contract was found in the official-only pass | Paid/private/login feeds and copied portals are excluded; no qualified public feed was found. | No provider-owned issuer mapping, stable ID, title/link rights, or original-publisher relationship was proven. | No route, total, pagination, retention, or rate contract accepted. | No licensed sentiment lineage. | **NOT_SERVED + LEGAL_GAP + RATE_POLICY_GAP + IDENTITY_GAP**. |

### 4.1.1 VSDC search-hint boundary

The earlier #203 first-party observations recorded VSDC search-category parameters and page controls
as separate corporate-action discovery hints; no such parameter is adopted as a #211 API contract.
Those observations are not a versioned developer API. A broad or empty HTML section, search row, or
category token does not itself prove the announcement's legal issuer, stable ID, publication
timestamp, or complete coverage. The response-backed issuer/security detail and announcement
identity checks from #203 remain separate corporate-action evidence; they do not turn the new C1–C3
chain into general company news. Legacy numeric C4 remains active/non-authoritative only for its
existing scope.

The VSDC pages were usable with a browser-like user agent in the bounded observation; a no-user-agent
request produced an unusable empty response. This is a transport dependency, not automation
permission or a rate contract. The ephemeral `__VPToken`/cookie flow is not logged, cached, or
republished, and no new runtime request is authorized.

### 4.2 Required count and source-gate attempt accounting

The observation contains a count of 30 rows/unique values, but no reviewable 30-symbol manifest.
It therefore has `COHORT_IDENTITY_GAP`; no per-symbol cell or independently retained position is
claimed. The exact bounded ledger below separates route evidence from a manifest-based cohort crawl.
A route-evidence logical attempt is one named official URL/document request; a physical attempt is
one network dispatch. A cohort logical attempt is one explicit manifest/bulk request scope; its
physical count is the number of network dispatches. No retry occurred in this evidence pass.

| Candidate unit | Route evidence (logical/physical) | Cohort crawl (logical/physical) | Exact source-level disposition |
|---|---:|---:|---|
| Alpha Vantage | 2 / 2 official documentation/terms fetches; 0 API calls | 0 / 0 | `SOURCE_GATE_SKIPPED_NO_LOGIN_EVIDENCE`; existing BYOK baseline is preserved. |
| HNX listed disclosure | 1 / 1 strict route attempt; TLS failed before a usable response | 0 / 0 | `SOURCE_GATE_SKIPPED_TRANSPORT_INCONCLUSIVE`; no response shape or coverage is claimed. |
| HNX UPCoM disclosure | 1 / 1 strict route attempt; TLS failed before a usable response | 0 / 0 | `SOURCE_GATE_SKIPPED_TRANSPORT_INCONCLUSIVE`; no response shape or coverage is claimed. |
| VSDC issuer announcements | 1 / 1 bounded GET observation; no page POST/walk | 0 / 0 | `SOURCE_GATE_SKIPPED_IDENTITY_RIGHTS_GAP`; route-level observation is not per-symbol coverage. |
| VSDC general news | 1 / 1 bounded route observation | 0 / 0 | `SOURCE_GATE_SKIPPED_IDENTITY_RIGHTS_GAP`; no general-news cohort claim. |
| HOSE issuer disclosures | 1 / 1 bounded official-route observation | 0 / 0 | `SOURCE_GATE_SKIPPED_TRANSPORT_SCHEMA_GAP`; no absence claim. |
| HOSE information disclosure | 1 / 1 bounded official-route observation | 0 / 0 | `SOURCE_GATE_SKIPPED_TRANSPORT_SCHEMA_GAP`; no absence claim. |
| SSC regulator material | 1 / 1 bounded official-portal/legal observation | 0 / 0 | `SOURCE_GATE_SKIPPED_NOT_A_COMPANY_NEWS_UNIT`; no issuer-news coverage claim. |
| FPT issuer-owned disclosure/news | 2 / 2 bounded official-page observations | 0 / 0 | `SOURCE_GATE_SKIPPED_COHORT_BREADTH_LEGAL_GAP`; one issuer is not a cohort source. |
| Vingroup issuer-owned disclosure | 1 / 1 bounded official-page observation | 0 / 0 | `SOURCE_GATE_SKIPPED_COHORT_BREADTH_LEGAL_GAP`; no cohort source. |
| Issuer-owned IR/news feeds | 0 / 0; no single feed selected | 0 / 0 | `SOURCE_GATE_SKIPPED_NO_SINGLE_SOURCE_UNIT`; one-off routes are not a source. |
| FiinGroup licensed datafeed | 1 / 1 official product/terms observation; no news schema call | 0 / 0 | `SOURCE_GATE_SKIPPED_RIGHTS_SCHEMA_GAP`; no schema or 30-cell claim. |
| GDELT licensed/open metadata | 1 / 1 official terms observation | 0 / 0 | `SOURCE_GATE_SKIPPED_IDENTITY_COVERAGE_GAP`; rights alone do not qualify the cohort. |
| Other licensed publisher/aggregator | 0 / 0; no named candidate selected | 0 / 0 | `SOURCE_GATE_SKIPPED_NO_QUALIFIED_CANDIDATE`; rights and identity remain unresolved. |

The source-level route count is not a provider row count and does not prove absence. “0 / 0” in the
cohort column means that the source gate prevented a manifest crawl; it does not mean the provider
returned no news. A future reopen must attach a newly authorized reviewable manifest with 30 distinct
canonical symbols, owner/caller provenance, retrieval timestamp, and a digest or equivalent content
identity before any per-symbol coverage accounting begins.

## 5. Identity, time, content, and sentiment gate

### 5.1 Item identity

A future qualified item must prove, in the same response family:

1. normalized requested VN ticker and response-backed ticker;
2. legal issuer name, exchange/market, and stable owner identifier (ISIN or owner equivalent);
3. rename/symbol-change and multi-issuer rules;
4. owner-declared stable `provider_id` (never a URL hash, local sequence, title hash, or query
   ticker); and
5. canonical HTTPS URL, exact publisher identity, licensed title, and content kind.

`NewsItem.source` remains the publisher identity. `NewsItem.source_adapter` and
`NewsResult.source` remain the explicit adapter token. A portal name, query ticker, or adapter token
must never be stamped into the publisher field. Dangerous/padded/control/userinfo URLs, unexpected
hosts, unsafe schemes, unbounded title/publisher values, and an ID belonging to another issuer fail
closed.

### 5.2 Publication time and content boundary

`published_at_utc` may be populated only from a provider field whose meaning, timezone, precision,
and publication-versus-update distinction are documented or response-backed. A date-only value is
not midnight UTC. `fetched_at_utc` is retrieval time only. VSDC's observed `Date update` and any
unverified portal date/time label are not silently promoted to publication instants. No item is mapped
to a VN cash or futures session by this issue.

The library may return metadata only: URL, licensed title, exact publisher, publication instant,
content kind, exact tickers, optional licensed snippet, and provider-owned sentiment. It must reject
or omit bodies, HTML, scripts, media, paywall text, attachments, and article-page content. A title or
snippet is not public domain merely because it is visible on an official page.

### 5.3 Sentiment lineage

All current and candidate-gap results keep sentiment fields `None` unless one qualified provider
supplies all of the following:

- article-wide versus ticker-specific scope;
- exact ticker association for each score;
- finite numeric range, score meaning, and label vocabulary;
- relevance semantics, language, model/provider/version, and update policy; and
- rights to return that sentiment to the caller.

Article-wide sentiment may remain in the existing overall fields but cannot be copied to every
mentioned ticker. A future ticker-specific record would be a trailing/defaulted immutable type;
it cannot overload `tickers` or normalize scores across providers. No title, snippet, price move,
topic, or model inference is sentiment evidence.

## 6. Coverage, pagination, diagnostics, and no-false-absence

### 6.1 Coverage axes (future release-gate vocabulary only)

No public coverage type or field is approved by this source-gap note. In a future qualified-source
design, a reviewable manifest symbol must be measured on these axes independently:

| Axis | Required value or explicit gap |
|---|---|
| requested bounds | inclusive `2018-08-13..2026-08-19`, preserving the existing date/datetime precision contract |
| provider retention | owner-declared floor/ceiling and whether it covers the window |
| observed bounds | first/last qualified publication instants, not retrieval/update timestamps |
| counts | returned rows, distinct provider IDs, distinct URLs, duplicates, revisions, deletions |
| gap status | review vocabulary `full`, `partial_known`, or `partial_unknown`; never an unqualified zero |
| boundary | whether both inclusive edges were returned and identity-validated |
| absence | `confirmed_empty` only when qualified source total/query semantics prove zero |
| truncation | exact page/row/budget reason; any continuation surface must be designed separately |

The future design must explicitly decide whether coverage is attached to `NewsResult`, how
continuation is exposed, whether a qualified zero returns an empty result or raises, how direct and
facade calls behave, and how snapshot/repr/DataFrame/export contracts evolve. Until that separate
design pass, these are review terms only, not a public enum, constructor, field, or API promise.

An empty page, missing ticker tag, failed transport, HTML maintenance/login/challenge page, known
retention clamp, deletion, or exhausted local budget is not proof of no news. An HTTP 200 maintenance
or login page is transport/schema failure, not an empty result. No source is allowed to return an
apparently complete aggregate after a page failure, MIME/schema drift, unreconciled total, or fatal
identity mismatch.

### 6.2 Future finite query and audit-global budgets

No budget below authorizes runtime implementation now. It is the minimum deterministic contract a
future source must satisfy before a new source-gate review. A **logical query** is one explicit
provider request scope: one manifest symbol, or one owner-declared bulk scope with an exact symbol
set. Two ledgers are mandatory: a query ledger for each `(provider, query_id, symbol_scope)` and an
audit-global ledger for one 30-manifest/source run. The global ledger is not reset between symbols.

| Counter | Per logical query | Per 30-symbol audit-global run |
|---|---:|---:|
| logical queries | 1 scope at a time | 30 maximum |
| pages | 64 maximum | 1,920 maximum (`30 × 64`) |
| retries | 64 maximum (`1/page`) | 1,920 maximum |
| physical calls | 128 maximum (`64 × (1 initial + 1 retry)`) | 3,840 maximum |
| candidate rows | 10,000 maximum | 300,000 maximum (`30 × 10,000`) |
| wire body bytes | 8 MiB maximum | 240 MiB maximum (`30 × 8 MiB`) |
| decompressed body bytes | 8 MiB maximum | 240 MiB maximum (`30 × 8 MiB`) |
| concurrency | exactly 1 | exactly 1 |

The row counter charges every decoded item object before deduplication, so duplicates cannot evade a
cap. The transport must use bounded streaming and bounded decompression; it must never call an
unbounded `.content` convenience accessor or allocate a body based only on `Content-Length`. Only
`identity` and one explicitly supported compressed encoding (currently `gzip`) are admissible; any
other or multiple content encoding is terminal. The raw-byte iterator requests chunks no larger than
64 KiB and requests at most `min(64 KiB, remaining_wire_cap + 1)` bytes, so it cannot read an
unbounded overrun. Charge raw wire bytes and decompressed bytes cumulatively against both the query and
audit-global ledgers before retaining either. `Content-Length` is advisory: missing, compressed, or
misleading lengths do not weaken enforcement. Feed compressed chunks through a bounded decompressor;
reserve decompressed output before parsing and allow at most one output-byte overrun sentinel. If
wire or decompressed bytes would exceed either remaining cap, consume at most that one-byte sentinel,
abort the stream, and discard the sentinel plus all raw/decoded buffers. No full oversized body is
ever materialized or parsed. A redirect is never followed and consumes a failed reservation. The
audit-global ceiling applies even when one bulk request covers multiple symbols.

### 6.3 Atomic deterministic scheduler

A future implementation must create both ledgers before the first network call. Every initial page
and retry atomically reserves `(audit_id, provider, query_id, symbol_scope, page_ordinal,
retry_ordinal)` against the query and audit-global counters before dispatch. Reservation order is
lexicographic request order; one physical call consumes one reservation; parsing and local validation
consume zero. A duplicate, reversing, cross-query, malformed, missing-middle, or post-exhaustion
page token is a fatal pagination error with no next call.

The only retryable classes are a pre-response connect/read timeout, a connection reset before a
response, and HTTP `502`, `503`, or `504`; each gets at most one retry. `401`, `403`, `429`, all
other `4xx`/`5xx`, any redirect, TLS failure, MIME/shape drift, login/maintenance/challenge, and
identity mismatch are terminal and never retried. A retry is a new reservation and is charged to
both ledgers.

If any reservation would exceed either ledger, the reservation fails atomically and no network call
is made. A terminal failure in one symbol stops the audit-global scheduler: no later symbol, page, or
retry may be dispatched. A body-size, row-count, or counter overrun discards the private accumulator
atomically. The result is committed only after all requested pages are reconciled with provider
total/exhaustion semantics and every returned row passes identity/time/content validation. An
exhausted ledger is fail-loud and cannot become an absence claim.

### 6.4 Finite sanitized diagnostic vocabulary and budget outcome

Any future public warning/error must use the existing `NewsResult.warnings: tuple[str, ...]` field
shape, with no current model change. The allow-list below contains 19 exact lowercase ASCII tokens;
an adapter may emit at most 8 unique tokens per result, sorted lexicographically, each at most 32
characters. There is no public warning message or provider free text:

```text
transport_failed
strict_tls_failed
redirect_rejected
unexpected_status
mime_mismatch
login_or_challenge
schema_mismatch
issuer_identity_mismatch
provider_id_missing_or_conflict
unsafe_url
publication_time_unproven
pagination_incomplete
provider_total_unreconciled
coverage_partial_known
coverage_partial_unknown
budget_exhausted
sentiment_unavailable
rights_unresolved
source_gap
```

These tokens are design vocabulary only; no new token is added to the current runtime or snapshot by
this commit. `coverage_partial_known` requires authoritative observed bounds and a bounded reason;
it is not an empty-list token. `source_gap` is the current disposition.

This source-gap note intentionally removes the deferred budget-exception contract: it proposes no
fatal budget exception, class name, export, constructor, catch surface, or public message.
`budget_exhausted` is only one bounded warning token in the future review vocabulary; it is not a
current catch surface or public exception message. A later qualified-source design may choose a fatal
outcome, but that is a new design obligation and must first specify the exact module/export,
constructor fields and bounded types, repr/string/snapshot behavior, direct-source propagation,
facade propagation/catch behavior, and interaction with `NewsResult`/`EmptyData`. Until that fresh
design passes, no runtime budget exception or message is authorized.

## 7. Legal, rate, and owner contact closure

### 7.1 Rights findings

The official pages establish who owns or publishes a portal, not permission to automate, cache,
derive, return, or redistribute it. Specifically:

- Alpha's [terms](https://www.alphavantage.co/terms_of_service/) are credentialed and not a
  no-login Vietnamese permission.
- The official [HNX legal index](https://www.hnx.vn/en-gb/van-ban-phap-ly.html) and candidate
  [HNX disclosure routes](https://www.hnx.vn/en-gb/thong-tin-cong-bo-up-hnx.html) identify the
  owner/legal contact surface only. Strict transport failed in this pass, so no HNX response shape,
  data licence, or rate/concurrency contract is claimed.
- The official [HOSE issuer-news route](https://www.hsx.vn/vi/tin-tuc/tin-to-chuc-niem-yet) and
  [HOSE disclosure route](https://www.hsx.vn/vi/quy-dinh-hose/cong-bo-thong-tin) are candidate owner
  paths only; no response shape, reusable API contract, or redistribution grant is claimed here.
- The official [VSDC issuer page](https://vsd.vn/en/alo/ISSUER), [VSDC news page](https://vsd.vn/en/tin-tuc),
  and [VSDC legal page](https://vsd.vn/vi/lel) expose issuer/depository information and legal
  documents, but no public grant was found for automated multi-year retrieval, title/snippet
  storage, derived normalized rows, caller-facing return, retention, or redistribution. This is a
  bounded negative observation, not legal advice.
- [FPT's stock page](https://fpt.com/en/ir/stock-information) binds FPT Corporation to ticker
  `FPT`, and its [public disclosure page](https://fpt.com/en/ir/information-disclosures) exposes
  year controls reaching 2018. Its [terms of use](https://fpt.com/en/terms-of-use) permit viewing,
  extraction, and sharing for personal/non-commercial use with attribution, while commercial
  copying/distribution requires prior written consent; that is not an OSS caller-facing grant.
- [Vingroup's disclosure page](https://www.vingroup.net/quan-he-co-dong/cong-bo-thong-tin) is an
  official issuer reference with year/count controls, but its mixed disclosure/document scope does
  not provide a common item/ticker/time/rights contract for the cohort.
- [FiinGroup's API Datafeed/product terms](https://fiingroup.vn/vi/dieu-khoan-va-dieu-kien.html) are
  a licensed-product lead, not an anonymous no-login source. No exact news schema/version is admitted
  from this general page; licence, metadata-only projection, rate, retention, and redistribution
  terms require direct written confirmation before any design can qualify it.
- [GDELT's official terms](https://www.gdeltproject.org/about.html) permit use and redistribution
  of its released datasets with attribution, but the global metadata source does not prove exact
  Vietnamese issuer/ticker identity or complete cohort coverage. Rights alone do not qualify it.
- The official [SSC portal](https://ssc.gov.vn/) is a regulator/legal source, not a returned
  company-news feed or reuse licence.

Original publisher rights and portal-owner rights must remain separate. A future permission letter
must explicitly cover both where they differ.

### 7.2 Lawful contact paths

These are owner contact routes for a permission/contract question, not data sources and not evidence
that permission exists:

| Owner | Candidate official contact path | Question to ask |
|---|---|---|
| HNX | [HNX contact](https://www.hnx.vn/en-gb/lien-he.html) | Whether the exact issuer-disclosure route permits no-login automated metadata retrieval, rate/concurrency, title/link storage, attribution, retention, and redistribution. |
| HOSE | [HOSE contact](https://www.hsx.vn/vi/lien-he) | Same questions for the issuer-news/disclosure route, including JS/API access and original issuer attachment rights. |
| VSDC | [VSDC contact](https://vsd.vn/vi/ads/tAPN4%47%65z5an%47D8ztNn7I_w) | Permission for exact category route, token/cookie behavior if applicable, rate/concurrency, fields, storage, derived rows, deletion, attribution, and redistribution. |
| Issuer/aggregator | Owner's published legal/IR contact only | Written authorization from both aggregator and original publisher where title/link/sentiment rights differ. |

Until written owner evidence is received and reviewed, `legal_status=UNRESOLVED_PERMISSION_REQUIRED`,
`automation=NOT_GRANTED`, `redistribution=NOT_GRANTED`, and no new source-chain request is authorized.

## 8. Conjunctive reopen criteria

A future #211 reopen is valid only when **all** criteria below pass for one exact provider/route
version and a newly authorized, reviewable 30-symbol manifest. The count-only observation in this
artifact is not a reusable cohort identity.

1. **Owner permission:** written terms cover no-login runtime fetch, allowed method/headers,
   automation, frequency/concurrency/retry, title/link/summary/sentiment storage, derived normalized
   rows, caller-facing return, attribution, retention/deletion, commercial use, and redistribution;
   original-publisher rights are separately confirmed.
2. **Transport:** strict TLS and HTTPS-only host/path, zero redirect, route-specific MIME/envelope and
   schema, no login/session/cookie-only flow, no WAF/challenge bypass, and maintenance/login pages
   rejected as transport/schema failure.
3. **Identity:** every returned row has response-backed requested ticker, legal issuer/exchange/stable
   identifier, provider ID, safe URL, publisher, and content kind; rename/multi-issuer behavior is
   specified and synthetic negative fixtures fail closed.
4. **Time:** published versus updated semantics, timezone, precision, provider clock, inclusive
   boundaries, revision/deletion policy, and `fetched_at_utc` separation are proven.
5. **Coverage:** source retention and arbitrary-window semantics cover the requested range or expose
   exact bounded partial status; all 30 manifest symbols are independently measured; no
   empty/failed/truncated cell is called absent. A separate API design must settle coverage fields,
   continuation, empty-result behavior, precision, direct/facade behavior, and exports before code.
6. **Pagination/budget:** page size, total/cursor/exhaustion, stable sort, duplicate/revision behavior,
   retry/rate policy, atomic reservation, physical ceilings, and no-call-after-failure are executable
   and pass offline tests.
7. **Sentiment:** only claim it if exact article/ticker scope, score/label/model/version/language,
   update, and reuse rights are proven; otherwise all sentiment remains `None`.
8. **Compatibility:** new token is explicit, Alpha defaults/limits/key redaction/one-request behavior
   remain unchanged, source/provider identities remain separate, additive fields are defaulted,
   public API snapshots and docs are updated, and no automatic fallback or cross-source stitch exists.
9. **Review sequence:** design/source PASS first; then a separate RED-first test commit and code review;
   only a later implementation PASS could authorize production capability.

The current evidence fails criteria 1–7 for every candidate, and the count-only observation has a
`COHORT_IDENTITY_GAP`, so the chain remains empty and the source-gap disposition is closed only as
documentation—not as runtime capability.

After an exact-SHA source/design PASS, the docs-only completion sequence is: rerun merged-tree gates
on the clean approved anchor; push only that exact anchor; verify remote `HEAD`, ancestry, and the
approved research/design/backlog paths; post a clean no-capability `SOURCE-GAP` resolution; then
close #211 and re-read it as closed/completed. This transition never authorizes RED tests, TDD,
production code, a provider token, or a company-news capability.

## 9. Sources

- [Alpha Vantage NEWS_SENTIMENT documentation](https://www.alphavantage.co/documentation/#news-sentiment)
- [Alpha Vantage Terms of Service](https://www.alphavantage.co/terms_of_service/)
- [HNX listed-stock information disclosure](https://www.hnx.vn/en-gb/thong-tin-cong-bo-ny-hnx.html)
- [HNX UPCoM information disclosure](https://www.hnx.vn/en-gb/thong-tin-cong-bo-up-hnx.html)
- [HNX legal documents](https://www.hnx.vn/en-gb/van-ban-phap-ly.html)
- [HNX contact](https://www.hnx.vn/en-gb/lien-he.html)
- [HOSE listed-issuer news](https://www.hsx.vn/vi/tin-tuc/tin-to-chuc-niem-yet)
- [HOSE information disclosure](https://www.hsx.vn/vi/quy-dinh-hose/cong-bo-thong-tin)
- [HOSE contact](https://www.hsx.vn/vi/lien-he)
- [VSDC issuer news](https://vsd.vn/en/alo/ISSUER)
- [VSDC news](https://vsd.vn/en/tin-tuc)
- [VSDC legal documents](https://vsd.vn/vi/lel)
- [VSDC contact](https://vsd.vn/vi/ads/tAPN4%47%65z5an%47D8ztNn7I_w)
- [State Securities Commission portal](https://ssc.gov.vn/)
- [FPT stock information](https://fpt.com/en/ir/stock-information)
- [FPT public disclosures](https://fpt.com/en/ir/information-disclosures)
- [FPT Terms of Use](https://fpt.com/en/terms-of-use)
- [Vingroup public disclosures](https://www.vingroup.net/quan-he-co-dong/cong-bo-thong-tin)
- [FiinGroup Terms and Conditions / API Datafeed product](https://fiingroup.vn/vi/dieu-khoan-va-dieu-kien.html)
- [GDELT official terms](https://www.gdeltproject.org/about.html)
- [SSI current group route used only for the count-only observation](https://iboard-query.ssi.com.vn/stock/group/VN30)

All route shapes attributed to page scripts are observations of official pages, not quotations from
an owner-published developer API specification. The report records facts and gaps as of
23 August 2026 (UTC+7); it does not provide legal advice or a provider SLA.
