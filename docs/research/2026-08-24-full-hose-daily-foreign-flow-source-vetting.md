# Full-HOSE daily foreign-investor flow source vetting — #227

**Access date:** 24 August 2026 (UTC+7)
**Packet:** `tasks/227-full-hose-daily-foreign-flow-spec.md`, reviewer anchor `29206690269215dba1a35bb13ee7c621055e7fca`
**Published base:** `origin/master` `483ff56522e713ae8495dc515e4e4f5915655bd7`
**Phase:** source/design only
**Disposition:** **`SOURCE-GAP CLOSURE`**
**Runtime chain:** empty; no provider is registered or callable

## Decision

Official HOSE/HSX material proves that HOSE publishes foreign-investor trading summaries and
offers market-data services, but it does **not** prove one lawful, no-login, full-current-HOSE,
per-symbol daily-history operation with response identity, historical bounds, pagination, finite
runtime policy, and caller-return/redistribution rights. The closest public pages are aggregate or
top-five summaries; the richer webservice is contract/login-oriented. No candidate therefore meets
the packet's conjunctive gate, and no `QUALIFIED_PARTIAL` disposition is justified.

This is not a claim that HOSE has no commercial or private data. It is a bounded source-gap result.
No live API request was made, no live row was retained, and no third-party code was run.

## Clean-room boundary

Before research, `docs/vnstock-blacklist.md` was read. Every web search used this exact exclusion:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result or derivative material was opened, cited, compared, installed, or used. Only
official exchange/regulator/provider pages and documents, plus dated local evidence, are retained
below. No query-bearing URL, raw body/header,
cookie, token, response digest, provider exception, live universe, live flow value, or source-derived
fixture is committed.

## Evidence accounting

Static pages/documents are research evidence, not runtime dispatches. Candidate flow dispatches are
`0` logical and `0` physical. `0` means no request was made; it does not mean zero rows, zero traffic,
source absence, or permission. Static transport counters are `NOT_RETAINED`, not invented.

| Channel | Logical | Physical | Pages | Retries | Redirects | Compressed/decompressed bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Official pages/documents read statically | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` | `NOT_RETAINED` |
| Candidate HOSE flow dispatches | `0` | `0` | `0` | `0` | `0` | `0/0` |

## Official source units

Each row is an independent owner + route/operation. A UI, PDF, tariff, or protocol document is
not silently promoted to an API or joined to another owner's data.

| Unit and official route | Documented facts | Missing qualification axes | Disposition |
| --- | --- | --- | --- |
| **HOSE foreign-investor statistics — stocks**
  [`/vi/du-lieu-giao-dich/giao-dich-ndtnn/co-phieu`](https://www.hsx.vn/vi/du-lieu-giao-dich/giao-dich-ndtnn/co-phieu) | Public date-range UI; “aggregate trading by security”; volume labels in `100` shares and value labels in million VND; a separate twelve-month monthly summary distinguishes foreign buy/sell from the market. | No published API/schema, response-backed `exchange`/symbol/session identity, exact buy/sell row fields, history retention, page/cursor/totals contract, revision policy, rate policy, or reuse terms. Static HTML currently exposes a JavaScript shell rather than a documented response. | `IDENTITY_GAP`, `FIELD_GAP`, `COVERAGE_GAP`, `PAGINATION_GAP`, `RATE_POLICY_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| **HOSE daily trading-summary PDF series**
  [27 February 2026 official summary](https://staticfile.hsx.vn/Uploads/UploadDocuments/2440741/20260227%20Tong%20hop%20thong%20tin%20giao%20dich.pdf) | A dated two-page official summary labels market-wide foreigner `buying`, `selling`, and `buying-selling`, with trading volume in shares and trading value in billion VND; it also publishes only top-five foreign-trading lists. | Top-five/market aggregate is not every current-HOSE symbol; no full-board history index, pagination, row totals, retention, corrections/revisions, response identity, or OSS reuse contract. | `FIELD_GAP`, `COVERAGE_GAP`, `PAGINATION_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| **HOSE annual/statistical reports**
  [2024 annual report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896445/B%C3%81O%20C%C3%81O%20TH%C6%AF%E1%BB%9CNG%20NI%C3%8AN%20%28ANUAL%20REPORT%29%202024.pdf) | Official annual/monthly foreign-investor statistics identify buy, sell, and buy-minus-sell volume/value; the report explicitly says foreign statistics include order matching and put-through and breaks results down by security type. | Aggregate/report evidence is not a daily per-symbol full-board history route; no machine contract, current universe snapshot, page/revision semantics, runtime policy, or redistribution permission. No report rows are retained. | `FIELD_GAP`, `COVERAGE_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| **HOSE market-data service**
  [`Data feed`](https://www.hsx.vn/vi/data-feed), [`ECM login`](https://ecm.hsx.vn/hoseecm/login), [official information-service tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf) | HOSE advertises a Market Data Feed/Webservice delivered through an HOSE API; the tariff separates display/non-display and online, delayed, and end-of-day products. The public feed entry redirects users to an account/password login. | No public no-login route/version, foreign-flow package/schema, pagination/history/retention, rate/retry/concurrency, caller-return, storage/cache, attribution, or redistribution/OSS permission. Paid service visibility is not a reuse grant. | `LEGAL_GAP`, `RATE_POLICY_GAP`, `TRANSPORT_INCONCLUSIVE`, `NOT_PROBED` |
| **HOSE current-listing/universe lead**
  [`Listed stocks`](https://www.hsx.vn/vi/quan-ly-niem-yet/co-phieu) | Official current listing navigation exists and is separate from foreign-flow statistics. | The public representation is a JavaScript shell in static retrieval; no deterministic snapshot schema, response-backed board identity, count/as-of boundary, listing/delisting history, or flow-response binding is published in retained evidence. | `UNIVERSE_GAP`, `IDENTITY_GAP`, `NOT_PROBED` |

## What is established versus missing

**Established:** HOSE is the owner of the official public pages, PDF summaries, market-data service
catalogue, and protocol lead. HOSE uses foreign buy/sell/net terminology and publishes volume/value
units. Official summaries distinguish aggregate market statistics and top-five lists; official
annual statistics explicitly include matching and put-through.

**Not established:** one exact current-HOSE universe snapshot; one response-backed `(exchange, code,
session)` identity; per-symbol daily gross/net value fields and scale; main-board/put-through scope;
session timezone, publication lag, correction/revision behavior; arbitrary historical retention;
native bulk/per-symbol pagination and reconciliation; no-login automation; rate/retry/concurrency
limits; and rights to cache, store, return to callers, redistribute, or make derivatives.

The official listing page cannot be used to turn today's cohort into historical membership. A symbol
from a separate universe page would not prove the flow response's board or symbol identity.

## SSI, prior-HOSE, and non-HOSE source boundaries

The official SSI [FastConnect API specifications](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)
document a `DailyStockPrice` operation with `Tradingdate`, `Symbol`, date inputs, `market=HOSE`,
pagination inputs, and foreign total buy/sell volume/value fields. The same documentation exposes a
separate `AccessToken` operation. This is a provider schema lead, not a no-login qualification:
the documentation does not provide a public OSS caller-return/redistribution grant, full current-HOSE
history bound, revision contract, native bulk reconciliation, or finite runtime terms. It is
`NOT_SERVED` for this packet's no-login source gate, not a claim that SSI has no licensed product.

The existing `ssi_iboard_universe` source is a separate current snapshot operation. Its local source
contract records runtime-fetch/no-redistribution posture, index-basket-derived partial coverage, and
unavailable listing dates. Those warnings are preserved if it supplies the snapshot; they do not
authorize the SSI flow fields or turn current membership into historical membership. The official
[SSI iBoard terms](https://www.ssi.com.vn/khach-hang-ca-nhan/dieu-khoan-va-chinh-sach-iboard) must
be reviewed separately before any new public caller-return surface broadens that existing contract.

The dated #201 report remains historical evidence. Its HOSE `tradingresult/{code}` sample returned a
symbol and foreign component fields, but only for three sampled names; `reportDate` session meaning,
raw value scale, current-board completeness, rate terms, revision semantics, and reuse rights stayed
unresolved. Its same-host `foreign/{code}` sample lacked a response symbol and is rejected as a
fallback. This #227 round made **zero** candidate data dispatches and does not upgrade those
observations.

HNX/UPCoM per-symbol reports are wrong-board, HNX aggregate PDFs are not HOSE rows, and SSC
publication/statistics pages are aggregate or legal evidence. None may be relabelled HOSE or used to
fill a missing symbol/session. A provider-owned [FiinGroup HOSE Stock V2 description](https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/hose-stock-v2)
names foreign total fields, but its public documentation does not establish no-login automation,
full-current-HOSE bounds, caller return, redistribution, rate, or revision terms; it remains
`NOT_SERVED` for this source gate.

## Sanitized per-unit ledger

Each route below is one owner + canonical route/version + operation. `NR` means `NOT_RETAINED`,
`NP` means `NOT_PROBED`, and `NA` means wrong-board/scope. The ledger is not a fabricated runtime
record: all candidate flow dispatches in this round are zero. A static page or Swagger document
does not create a `SourceAttempt`.

| Unit | Route/method/status/MIME/effective-route/redirect evidence | Logical/physical/pages/retries/redirects/compressed/decompressed | Identity/field/coverage evidence | Access and rights evidence | Total disposition |
| --- | --- | --- | --- | --- | --- |
| `HOSE-TRADINGRESULT` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Historical #201 sample: response symbol + component labels; date/session, scale, full-board bounds, revision and totals unresolved | No retained rate, automation, cache, caller-return, redistribution, amendment, or revocation grant | `SAMPLED_ONLY`, `IDENTITY_DATE_GAP`, `FIELD_UNIT_GAP`, `COVERAGE_GAP`, `LEGAL_GAP`, `RATE_POLICY_GAP` |
| `HOSE-FOREIGN` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Historical response lacked returned symbol and date-bound contract | Same unresolved HOSE rights/rate posture | `IDENTITY_GAP`; rejected, no fallback |
| `HOSE-PUBLIC-STATISTICS` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Static UI/PDF aggregate or top-five evidence; no per-symbol response contract | Public visibility/tariff is not permission | `FIELD_GAP`, `COVERAGE_GAP`, `PAGINATION_GAP`, `LEGAL_GAP`, `NOT_PROBED` |
| `HOSE-MARKET-DATA-SERVICE` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Product/feed existence; exact foreign-flow route, bounds and envelope not retained | Account/tariff-oriented; no no-login OSS/caller-return/cache/redistribution evidence | `LEGAL_GAP`, `RATE_POLICY_GAP`, `TRANSPORT_INCONCLUSIVE`, `NOT_PROBED` |
| `SSI-DAILY-STOCK` | `NR/GET/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Docs name `Tradingdate`, `Symbol`, HOSE selector and foreign fields; response identity/scale/history unproven | AccessToken flow documented; no public no-login or exact data-rights grant retained | `NOT_SERVED`, `LEGAL_GAP`, `COVERAGE_GAP`, `RATE_POLICY_GAP` |
| `SSI-UNIVERSE` | Existing source contract; no new flow dispatch | `0/0/0/0/0/0/0` for this round | Current snapshot only; partial-roster/listing-date warnings preserved; not flow identity | Existing runtime-fetch/no-redistribution contract is not flow permission | `CURRENT_SNAPSHOT_ONLY`, `UNIVERSE_GAP`; separate source |
| `FIINGROUP-HOSE-V2` | `NR/NR/NR/NR/NR/NR`; `NP` | `0/0/0/0/0/0/0` | Provider docs name foreign fields; full-HOSE identity/bounds/revision unproven | Provider rights, no-login automation, caller return and redistribution unretained | `NOT_SERVED`, `LEGAL_GAP`, `COVERAGE_GAP`, `RATE_POLICY_GAP` |
| `HNX/UPCOM` and `SSC` | `NA/NA/NA/NA/NA/NA`; `NP` | `0/0/0/0/0/0/0` | Wrong-board or aggregate-only | No cross-owner rights inference | `SCOPE_FAIL`, `NOT_APPLICABLE` |

The `0` values mean “not dispatched in this research round,” never zero rows, zero traffic, no
source, or permission. A future budget exhaustion preserves prior sanitized real attempts and
never fabricates a `SourceAttempt` or `diagnostics_truncated` record.

## Future qualification contract — design only

If a source reopens, fetch the current HOSE universe once before any flow call and freeze its exact
canonical symbol tuple, `board="HOSE"`, source, real `fetched_at_utc`, optional `as_of`, warnings,
and count. Reject malformed, empty, duplicate/conflicting, non-HOSE, legally blocked, or unbounded
snapshots before flow work. Preserve current-snapshot partial/listing/survivorship warnings; do not
claim a historical statutory roster.

The flow source must independently return/establish canonical code, HOSE board, and plain Vietnam
session date. A request path token, request order, retrieval time, publication timestamp, or guessed
UTC conversion is not identity. Each `(code, session)` gets one terminal design-level outcome:
`SERVED`, `SERVED_DECLARED_PARTIAL`, `EMPTY_AUTHORITATIVE`, `NOT_SERVED`, `IDENTITY_GAP`,
`FIELD_GAP`, `COVERAGE_GAP`, `PAGINATION_GAP`, `TRANSPORT_INCONCLUSIVE`, `CALL_BUDGET_GAP`, or
`NOT_DISPATCHED`. These are not current public enums.

`FULL` requires all frozen snapshot symbols and provider-eligible sessions, provider-declared
bounds, reconciled native totals/pages/cursors, no unexplained conflicts/gaps, and known
listing/retention/nonpublication boundaries. `QUALIFIED_PARTIAL` requires a provider-declared
narrower bound and complete served/unserved/unknown/budget accounting; it may not claim full-HOSE
2018-current. An HTTP 200 blank/HTML/WAF/timeout/unknown total/malformed or identity-mismatched
page is unknown, never authoritative empty or zero.

The future ledger is one sequential invocation-owned budget shared by universe discovery and flow:
`symbols`, `logical_units`, `physical_dispatches`, `pages_or_cursors`, `retries`, `redirects`,
`compressed_bytes`, and `decompressed_bytes`. Reserve atomically before dispatch; retries and
redirects are real physical operations; charge streamed compressed/decompressed bytes at their
respective stages; discard rows on malformed/mismatched/exhausted requests. Freeze no numeric
ceiling until owner rate/pagination evidence exists. Parse complete `Content-Type` after the first
colon and reject generic maintenance HTML or an unexpected MIME even with HTTP 200. No stitch,
fill, aggregate/OHLCV reconstruction, automatic fallback, raw URL/query/body/header/provider prose,
secrets, cookies, tokens, or live values.

## Owner/legal contact and reopen axes

Use only first-party contact/data-service paths: [HOSE contact](https://www.hsx.vn/vi/lien-he),
[HOSE data-feed](https://www.hsx.vn/vi/data-feed), [HOSE tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf),
[SSI FastConnect specs](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs), and
[SSI iBoard terms](https://www.ssi.com.vn/khach-hang-ca-nhan/dieu-khoan-va-chinh-sach-iboard).
The future packet must identify the exact owner/dataset and positively prove automated access,
caller return, cache/storage/retention/deletion, attribution, commercial/derivative use,
redistribution/resale, rate/retry/concurrency, amendment, and revocation. Public page visibility,
Swagger, robots, HTTP 200, a fee catalogue, or a universe contract is not permission.

## Reopen evidence

Reopen only when **one** HOSE-owned route/version/operation supplies all of the following in official
documentation or written owner permission:

1. Full current-HOSE board scope and one immutable snapshot with symbol count, `as_of`, listing/
   delisting boundary, and response-backed exchange/code identity.
2. Daily session date, foreign buy/sell volume and value, exact VND scale, net arithmetic, null/zero
   meaning, matching versus put-through scope, publication lag, and correction/revision semantics.
3. Provider-declared history bounds, eligible sessions, pages/cursors/totals, native bulk or an
   explicitly rate-authorized per-symbol operation, and deterministic reconciliation.
4. Explicit no-false-absence behavior: every snapshot symbol has a terminal typed outcome; WAF,
   timeout, malformed identity, truncation, unknown bounds, and budget exhaustion are not empty.
5. Finite rate/retry/concurrency, redirect, compressed/decompressed-byte, and whole-board budget
   rules, with owner-authorized automation and a bounded diagnostic contract.
6. Legal permission for automation, caller return, cache/storage/retention/deletion, attribution,
   commercial/derivative use, redistribution/resale, amendment, and revocation.

Only after those gates pass may a separate API/model decision and RED-first authorization begin. This
packet freezes no public model, warning grammar, exception, source registration, or runtime behavior.

## Sources

- [HOSE foreign-investor statistics — stocks](https://www.hsx.vn/vi/du-lieu-giao-dich/giao-dich-ndtnn/co-phieu)
- [HOSE foreign-investor statistics — ETF](https://www.hsx.vn/vi/du-lieu-giao-dich/giao-dich-ndtnn/etf)
- [HOSE foreign-investor statistics — index family](https://www1.hsx.vn/vi/du-lieu-giao-dich/giao-dich-ndtnn/bo-chi-so)
- [HOSE daily trading summary, 27 February 2026](https://staticfile.hsx.vn/Uploads/UploadDocuments/2440741/20260227%20Tong%20hop%20thong%20tin%20giao%20dich.pdf)
- [HOSE 2024 annual report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896445/B%C3%81O%20C%C3%81O%20TH%C6%AF%E1%BB%9CNG%20NI%C3%8AN%20%28ANUAL%20REPORT%29%202024.pdf)
- [HOSE data feed](https://www.hsx.vn/vi/data-feed)
- [HOSE ECM login](https://ecm.hsx.vn/hoseecm/login)
- [HOSE information-service tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf)
- [HOSE listed-stock navigation](https://www.hsx.vn/vi/quan-ly-niem-yet/co-phieu)
- [SSI FastConnect API specifications](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)
- [SSI iBoard terms and policy](https://www.ssi.com.vn/khach-hang-ca-nhan/dieu-khoan-va-chinh-sach-iboard)
- [FiinGroup HOSE Stock V2 provider documentation](https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/hose-stock-v2)
- Local dated evidence: `docs/research/2026-08-22-vn-foreign-flow-source-vetting.md` (#201; historical only)
- Local current-universe contract: `docs/sources/equities-universe.md`

## Bottom summary

- Decision: **`SOURCE-GAP CLOSURE`**; no current full-HOSE daily foreign-flow source qualifies.
- HOSE public statistics are aggregate/top-five; the richer feed is account/tariff-oriented.
- Prior HOSE `tradingresult` evidence is sampled only; `foreign/{code}` fails response identity.
- SSI documents daily foreign fields but requires an access-token flow and lacks rights/coverage proof.
- Existing SSI universe is current/partial and remains separate from flow identity and legal scope.
- Candidate dispatches are zero; no live rows, probes, RED tests, code, or runtime capability were added.
- Reopen requires conjunctive identity, coverage, transport/budget, legal, and exact-SHA gates.
- Need from Boss: **nothing**; return this source-gap packet for reviewer design review.
