# #211 design note — no-login Vietnamese company-news metadata

**Date:** 23 August 2026 (UTC+7)
**Packet:** `/home/hungson175/tools/vnfin-oss-reviewer/tasks/211-vn-company-news-source-spec.md`
**Packet commit:** `44bc597`
**Companion evidence:** [`docs/research/2026-08-23-vn-company-news-source-vetting.md`](../docs/research/2026-08-23-vn-company-news-source-vetting.md)
**Disposition:** **SOURCE-GAP CLOSURE**
**Production status:** no RED tests, production code, provider token, source-chain change, push, or issue closure is authorized

## 1. Decision and immutable boundary

No examined no-login Vietnamese candidate passes the one-unit gate for response-backed issuer
identity, item identity, publication time, requested-window coverage, deterministic pagination,
rights, rate policy, diagnostics, and public compatibility at the same time. The VSDC route is a
technically reachable issuer/depository listing, but it is not a qualified general company-news
source; HNX/HOSE are candidate owner routes with no admissible structured response contract in this
pass; issuer feeds and licensed aggregators do not form one proven source unit.

The correct action is documentation-only source-gap closure:

- keep the new source chain empty;
- keep `provider="alpha_vantage"` as the default and preserve its BYOK/missing-key/limit/one-request
  behavior byte-for-byte;
- leave `NewsItem`/`NewsResult` unchanged and do not add a provider token or fields now;
- keep `NewsItem.source` as publisher identity, separate from adapter/result source identity;
- keep sentiment `None` for any unqualified Vietnamese metadata;
- do not fetch bodies, attachments, media, archives, or article pages;
- do not add a signal, VN30 historical-news claim, automatic failover, cross-source merge, sentiment
  normalization, or one-feed-per-issuer scraper; and
- after exact-SHA design review, allow only the approved docs/source-gap resolution path—not TDD or
  runtime capability.

Before research, `docs/vnstock-blacklist.md` was read and every search used:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted or derivative material was opened, cited, compared, installed, or used.

## 2. Current API and release compatibility

The current source is read-only and remains the compatibility anchor:

```text
news.source(provider="alpha_vantage", *, api_key=None, http_get=None, timeout=25.0)
news.search(*, tickers=None, topics=None, start=None, end=None,
            sort="latest", limit=50, provider="alpha_vantage",
            api_key=None, http_get=None, timeout=25.0)
```

The current Alpha adapter validates its inputs, sends one request, uses public `limit <= 100`,
redacts the key, and raises missing-key `SourceUnavailable` before network. A future no-login
provider must never be selected by missing Alpha credentials or by failover. `api_key` behavior for
a future explicit no-login token is exact: it must be `None`; a non-`None` value raises a typed input
error before network, without echoing or logging the value. The no-login adapter never transmits,
stores, or redacts an `api_key` because it never receives one.

A future provider, if separately qualified, would require a new finite token, exact
`NewsResult.source`, and exact `NewsItem.source_adapter`. It would preserve publisher
`NewsItem.source`, provider-owned ID only, safe HTTPS URL, and all existing Alpha defaults. No token
or additive field is authorized by this note.

The annotated `v0.2.0` release peels to `2fe50df4f27064140ff9f7a680227a2b337ec74a` and has no
`vnfin/news/` path. No #211 capability is attributed to that release.

## 3. Qualification unit and candidate verdicts

The unit is:

```text
(owner/provider, exact route+method+version, VN ticker namespace,
 issuer identity, item schema/provider ID, publication-time semantics,
 pagination/total/revision contract, sentiment lineage if claimed,
 automation/rate/storage/redistribution rights)
```

Every field must be proven for the same unit. The sanitized matrix is in the companion research
artifact. The binding verdict is:

| Unit | Exact current observation | Verdict |
|---|---|---|
| Alpha Vantage | Official `NEWS_SENTIMENT` requires an API key; it remains the existing baseline, not a no-login Vietnamese source. | `NOT_SERVED` for #211; preserve Alpha unchanged. |
| HNX listed/UPCoM | Strict local TLS-chain verification failed before an admissible response, so no HNX response shape or schema claim is made. | `TRANSPORT_INCONCLUSIVE`; identity, time, pagination, coverage, legal, and rate posture remain unproven. |
| VSDC issuer category | Official HTML `GET /en/alo/ISSUER` returns a broad listing; observed full MIME is `text/html; charset=utf-8`; first-party paging uses the same route with a current-page JSON field. | Technical `PARTIAL` listing only; `IDENTITY_GAP + TIME_GAP + COVERAGE_GAP + PAGINATION_GAP + SENTIMENT_GAP + LEGAL_GAP + RATE_POLICY_GAP`; not a qualified source. |
| VSDC general news | Official category page mixes issuer/depository/member/VSDC/carbon content and exposes update timestamps, not a complete issuer-news identity/coverage contract. | `NOT_SERVED + IDENTITY_GAP + TIME_GAP + COVERAGE_GAP + LEGAL_GAP + RATE_POLICY_GAP`. |
| FPT issuer-owned pages | FPT identity and a year-indexed disclosure page are strong issuer-reference evidence, but the public terms limit extraction/sharing to personal/non-commercial use unless FPT gives written consent. | `PARTIAL` reference only; `LEGAL_GAP + RATE_POLICY_GAP + PAGINATION_GAP + COVERAGE_GAP`; no cohort source. |
| Vingroup issuer-owned page | Official disclosure UI has year/count controls but mixes issuer, bond, and exchange/depository documents; no common item/time/rights contract was accepted. | `PARTIAL` reference only; `IDENTITY_GAP + TIME_GAP + LEGAL_GAP + RATE_POLICY_GAP + COVERAGE_GAP`. |
| HOSE disclosure/issuer UI | Official page routes exist, but the bounded response is a JavaScript application without an accepted no-login response envelope; no guessed API or login path is allowed. | `TRANSPORT_INCONCLUSIVE + IDENTITY_GAP + TIME_GAP + PAGINATION_GAP + COVERAGE_GAP + LEGAL_GAP + RATE_POLICY_GAP`. |
| SSC disclosure material | Official regulator/legal material is not a returned company-news provider. | `NOT_SERVED + LEGAL_GAP + PAGINATION_GAP + COVERAGE_GAP`. |
| Issuer-owned feeds | No single owner, schema, route/version, bulk contract, or common rights policy covers the cohort. | `NOT_SERVED + LEGAL_GAP + RATE_POLICY_GAP + COVERAGE_GAP`. |
| FiinGroup API Datafeed | General official product/terms page identifies a licensed-data candidate; no exact news schema/version is admitted. | `LEGAL_GAP + RATE_POLICY_GAP + PAGINATION_GAP + COVERAGE_GAP + IDENTITY_GAP`; licensed lead only. |
| GDELT metadata | Official terms permit use/redistribution with attribution, but the global source does not prove Vietnamese issuer/ticker identity or complete 30-cell coverage. | `IDENTITY_GAP + COVERAGE_GAP + PAGINATION_GAP + SENTIMENT_GAP`; no fallback. |
| Other licensed aggregator | No named provider with explicit no-login automation, item/title/link/sentiment rights, and redistribution terms was accepted. | `NOT_SERVED + LEGAL_GAP + RATE_POLICY_GAP + IDENTITY_GAP`. |

These verdicts do not say that a candidate returned no news. They say the evidence is insufficient
to serve a lawful, identity-safe, complete-looking public result.

## 4. Count-only observation and evidence accounting

The required observation label is:

```text
C211-VN30-current-2026-08-23-count-only
```

It is one current SSI count observation, with `row_count=30`, `unique_symbol_count=30`, provider
`as_of=None`, `SUCCESS`, `application/json; charset=utf-8`, and identity fields
`stockSymbol/exchange/stockType`. The values and tuple/hash are not published because no provider
reproduction/redistribution grant was accepted. Its durable identity is
`COHORT_IDENTITY_GAP`; it is not a reviewable or frozen manifest, not historical VN30 membership,
and it does not establish issuer existence or news coverage in 2018.

No per-symbol ledger or independently retained position is claimed. For every candidate, the
source-level zero-call or gate-skip disposition is recorded without fabricating `0 articles`,
`0 coverage`, or `confirmed_empty`. A full 30-symbol run requires a newly authorized, reviewable
manifest supplied by the owner or caller, with 30 distinct canonical symbols, provenance, retrieval
time, and a digest or equivalent content identity.

The evidence protocol was route-level and bounded: no body/article fetch, no attachment fetch, no
page loop, no retry after transport/identity failure, no cookie/token reuse, no insecure TLS, no
search facade, and no guessed API. VSDC route observations are not a history or coverage promise.

## 5. Coverage API deliberately deferred

No `NewsCoverage` type, status enum, constructor field, export, `repr`, snapshot, DataFrame column,
or continuation surface is approved by this source-gap note. A future qualified-source design must
decide, as one compatibility contract, whether coverage attaches to `NewsResult`, how it preserves
the existing date/datetime precision accepted by the facade, how a continuation token is exposed,
whether a qualified zero returns an empty result or raises, and whether direct source and facade calls
have identical behavior. It must also specify serialization, public exports, and backwards-compatible
defaults before any RED test or implementation.

The future release gate may use `full`, `partial_known`, `partial_unknown`, and `confirmed_empty` as
review vocabulary, but those are not current public values. A future ticker-specific sentiment record
must likewise be additive/defaulted and retain exact ticker, relevance, score, label, provider, and
model/version; it cannot overwrite the current overall fields. If the source has no qualified
sentiment, the fields remain `None`.

## 6. Future route and item contract

A later qualified adapter must enforce the following before returning an item:

1. exact explicit provider token and response-backed requested ticker/legal issuer/exchange/stable ID;
2. owner-declared stable `provider_id`, never a URL/local hash or sequence;
3. canonical HTTPS URL with safe host/path, no userinfo, query credentials, controls, padding, or
   body content;
4. exact publisher identity in `NewsItem.source`, adapter token only in `source_adapter`;
5. licensed title and optional licensed snippet only; no body/HTML/media/attachment;
6. `published_at` proven distinct from `updated_at`, with proven timezone/precision; date-only is
   not midnight UTC and `fetched_at_utc` cannot stand in for publication time;
7. deterministic requested-bound inclusion, provider sort/direction, duplicate/revision/deletion
   policy, and all exact ticker associations; and
8. sentiment `None` unless exact article/ticker scope, numeric/label/model/version/reuse axes pass.

A response-backed ticker in a query parameter, title prefix, URL fragment, or current-basket guess is
not identity. Multiple issuer associations must be preserved, not duplicated or relabeled. Cross-
provider title/URL similarity never merges items.

## 7. Future query and audit-global budget, scheduler, and atomic failure

These are safety ceilings and release-gate requirements only; they do not authorize code. A logical
query is one explicit provider request scope: one manifest symbol, or one owner-declared bulk scope
with an exact symbol set. Two ledgers are mandatory: one per `(provider, query_id, symbol_scope)` and
one audit-global ledger for a 30-manifest/source run. The global ledger is not reset between symbols.

| Counter | Per logical query | Per 30-symbol audit-global run |
|---|---:|---:|
| logical queries | 1 scope at a time | 30 maximum |
| pages | 64 maximum | 1,920 maximum (`30 × 64`) |
| retries | 64 maximum (`1/page`) | 1,920 maximum |
| physical calls | 128 maximum (`64 × (1 initial + 1 retry)`) | 3,840 maximum |
| candidate rows | 10,000 maximum | 300,000 maximum (`30 × 10,000`) |
| response body bytes | 8 MiB maximum | 240 MiB maximum (`30 × 8 MiB`) |
| concurrency | exactly 1 | exactly 1 |
| redirects | 0 | 0 |
| TLS | strict chain verification | strict chain verification |

The row counter charges every decoded item object before deduplication. `response body bytes` means
`len(response.content)` after transport decompression and before text decode/schema parsing; headers,
cache, and local serialization do not count. A redirect is never followed and consumes a failed
reservation. The audit-global ceiling applies even when one bulk request covers multiple symbols.

One request-scoped pair of ledgers is created before network. Every initial page and retry atomically
reserves `(audit_id, provider, query_id, symbol_scope, page_ordinal, retry_ordinal)` against both
the query and global counters before dispatch. A duplicate, reversing/missing-middle/cross-query
cursor, provider total drift, or post-exhaustion token is a fatal pagination error and schedules no
next call.

The only retryable classes are a pre-response connect/read timeout, a connection reset before a
response, and HTTP `502`, `503`, or `504`; each gets at most one retry. `401`, `403`, `429`, all
other `4xx`/`5xx`, redirects, TLS failure, MIME/shape drift, login/maintenance/challenge, and
issuer/provider-ID mismatch are terminal and never retried. If any reservation would exceed either
ledger, it fails atomically and no network call is made. A terminal failure in one symbol stops the
audit-global scheduler: no later symbol, page, or retry may be dispatched.

A body-size, row-count, or counter overrun discards the private accumulator atomically. The result is
committed only after all requested pages are reconciled with provider total/exhaustion semantics and
every returned row passes identity/time/content validation. An exhausted ledger is fail-loud and
cannot become an absence claim. The future API must not return a partial `NewsResult` merely because
earlier pages succeeded.

## 8. Public diagnostics and no-false-absence contract

Future public warnings retain the existing `NewsResult.warnings: tuple[str, ...]` field shape; no
current model change is approved. The allow-list below contains 19 exact lowercase ASCII tokens. An
adapter may emit at most 8 unique tokens per result, sorted lexicographically, each at most 32
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

Only bounded counts, enum values, safe source token, and future-approved coverage fields may be
public. Never leak query URLs, raw cursors/tokens/cookies, headers, provider free text, article
titles/snippets, bodies, credentials, exception strings, or a failed-source trail.

The future fatal budget outcome is a design-only catch surface, not a current export:
`NewsBudgetExhausted(VnfinError)` with frozen fields
`scope: Literal["query", "audit"]`,
`limit: Literal["logical_queries", "pages", "retries", "physical_calls", "rows", "response_bytes"]`,
`limit_value: int`, `used_value: int`, `provider: str`, and
`warnings: tuple[str, ...]`. `provider` is an allow-listed adapter token; `limit_value` is one of
the table ceilings; `used_value = min(observed_value, limit_value + 1)`; warnings obey the 8-token
rule. Its sanitized string is exactly
`news budget exhausted: scope=<scope>; limit=<limit>; used=<used>; provider=<provider>` and is
bounded to 128 ASCII characters. It carries no URL, symbol, cursor, response text, header, cookie,
credential, or exception detail. A later qualified-source design must lock this type, export,
snapshot, and catch behavior before implementation.

`confirmed_empty` is only future review vocabulary until the coverage API design is approved. A
qualified source may use it only after its response-backed query scope, authoritative total, and
exhaustion semantics prove zero. Otherwise use the future partial/source-gap disposition; an empty
HTML list, no ticker tag, date clamp, transport failure, maintenance page, login/challenge, deleted
item, or budget exhaustion is never “no news”.

## 9. Legal/runtime reopen gates

All of these are conjunctive for one exact route/provider/version:

1. written owner permission covers automated no-login runtime, route/method/headers, frequency,
   concurrency, retries, title/link/snippet/sentiment storage, derived rows, caller-facing return,
   attribution, retention/deletion, commercial use, and redistribution;
2. original publisher rights are separately confirmed where publisher and aggregator differ;
3. exact route, strict TLS, no redirects, full MIME, response envelope, maintenance/login/challenge
   negatives, and schema are proven;
4. every returned manifest item has response-backed issuer/ticker/legal name/exchange/stable ID,
   provider ID, safe URL, publisher, title, and content kind;
5. publication/update semantics, timezone/precision, source retention, requested boundaries,
   duplicate/revision/deletion, sort, total, page exhaustion, and all 30 manifest cells are proven;
   the coverage API, continuation, qualified-empty behavior, precision, direct/facade behavior, and
   exports are separately designed before implementation;
6. owner rate/retry policy is compatible with the finite scheduler and every budget reservation is
   deterministic and atomic;
7. sentiment is either fully lineage-qualified or explicitly absent (`None`); and
8. RED-first synthetic fixtures, API snapshot, docs-contract, secret/blacklist, build, full-test,
   and exact-SHA design/code reviews pass in sequence.

Owner contact paths for this future evidence are [HNX](https://www.hnx.vn/en-gb/lien-he.html),
[HOSE](https://www.hsx.vn/vi/lien-he), and [VSDC](https://vsd.vn/vi/ads/tAPN4%47%65z5an%47D8ztNn7I_w).
They are permission-request routes, not data sources and not evidence of permission.

## 10. Review request and lifecycle boundary

The two exact packet artifacts are:

1. [`docs/research/2026-08-23-vn-company-news-source-vetting.md`](../docs/research/2026-08-23-vn-company-news-source-vetting.md)
2. this file

Requested review scope: source/legal/identity/time/coverage/pagination/budget/diagnostic/API
compatibility and the empty-chain/source-gap boundary only. After exact-SHA source/design PASS, the
docs-only sequence is: rerun merged-tree gates on the clean approved anchor; push only that exact
anchor; verify remote `HEAD`, ancestry, and approved research/design/backlog paths; post a clean
no-capability `SOURCE-GAP` resolution; then close #211 and re-read it as closed/completed. PASS
never authorizes RED tests, TDD, a provider token, production code, or any company-news capability.
#212 and #213 remain separate queued work.
