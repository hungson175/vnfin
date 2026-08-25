# Public Vietnamese fund/ETF listing and NAV-history source vetting

**Issue:** #233 — public fund/ETF catalogue and provider-published NAV history
**Research cut:** 26 August 2026 (UTC+7)
**Clean published base:** `ed55c0487745b2611bcef9a7d94e259907ec06b0`
**Final handoff state:** `SOURCE_DESIGN`, actor `vnfin-oss-reviewer`, next
`RETURN_EXACT_SHA_DESIGN_VERDICT`
**Disposition:** `SOURCE_GAP_CLOSURE`; the new chain remains empty

This is a docs/source/legal design artifact only. It adds no source, endpoint, product row, NAV
value, fixture, parser, model, API carrier, RED test, runtime capability, or coverage claim.
Fmarket remains disabled and unprobed. `nav_history` means provider-published NAV per fund unit;
exchange close, iNAV, returns, discount, tracking error, signals, and portfolio logic are outside
this source-gap chain. A separate source-qualified prices capability would be required for any
market-close claim; this document makes no such claim.

## 1. Decision and hard boundary

No single official owner route set closes all mandatory axes together:

1. explicit product form, stable owner identity, legal name, manager/issuer, currency, and
   provenance for a listing/discovery unit;
2. a same-owner binding from that identity to provider-published NAV per fund unit;
3. separate NAV/as-of, publication/knowability, revision/correction, and retrieval dates;
4. provider-declared bounds, cadence/non-publication rules, pages/totals/cursors, and reconciled
   `FULL`, provider-declared `PARTIAL`, or authoritative `EMPTY` outcomes;
5. finite transport/budget behavior with atomic no-false-partial semantics; and
6. written terms permitting the exact no-login automation, caller-facing return, cache/storage,
   retention, attribution, commercial/derivative use, and redistribution intended for public OSS.

The result is `SOURCE_GAP_CLOSURE`. The current mutual-fund runtime remains the existing
`DISABLE_PENDING_PERMISSION` boundary. A manager page, exchange disclosure, registry record, or
public HTML/PDF is identity/document evidence only; reachability and readability are not permission
to automate, retain, return, or redistribute.

## 2. Clean-room and evidence boundary

The mandatory project blacklist was read before this source-design task. No blacklisted or derived
material, copied endpoint map, unofficial mirror, reporter artifact, external code, credential,
login route, browser/session bypass, proxy dataset, or paid route was used. The evidence set is
limited to official manager/issuer, exchange, depository/regulator, and Fincorp/Fmarket material
already retained by the immutable #218/#221/#225 artifacts.

No provider API, data endpoint, query-bearing URL, response body, cookie, header, token, live NAV
row, or direct candidate data route was dispatched for #233. The inherited official pages/documents
are retained evidence, not fresh current-state verification, runtime attempts, or permission. All
mutable inherited states below are labelled `NOT_RECHECKED` and mean “last retained decision only.”
A missing field is `NOT_RETAINED`, `NOT_PROBED`, `NOT_MEASURED`, `UNKNOWN`, or a typed gap; it is
never zero, absence, permission, or a fabricated response fact.

The exact immutable inherited anchors are:

| Baseline | Exact artifact | Blob | #233 role |
|---|---|---|---|
| #218 ETF source vetting | `docs/research/2026-08-23-vn-etf-discovery-nav-history-source-vetting.md` @ `e78ddf7201fbadad7a24090e29ef63aa4868b980` | `5637a2c65121320332f7cced3e3c50c86f41e401` | Last retained ETF/manager/exchange evidence; not a current recheck |
| #218 design note | `tasks/218-design-note.md` @ `412ada80705ecf08b2da4e27d882dbf3bc256327` | `32194e27f452115e5e98227412fa468723e1bc7d` | Prior product-class, identity, coverage, API, and gap contract |
| #221 Fmarket terms | `docs/research/2026-08-23-fmarket-current-runtime-terms-audit.md` @ `6949a53ecd46dc61197afb9eee8dd245109ef95c` | `7a1db2d2e8265156cc224050355e19da4554832e` | Last retained legal audit; current terms are `NOT_RECHECKED` |
| #221 design note | `tasks/221-design-note.md` @ `eaace3d6e3049b3546b82c5da6a2dfdcb31e9b11` | `04f63b9c5f2ff0592bea5b889975ffaba692935c` | Existing four-operation disabled boundary |
| #225 equity-fund source vetting | `docs/research/2026-08-23-equity-fund-nav-authorized-source-vetting.md` @ `35fd9ceb871ba3e7aab0a87f3924d37342652420` | `adb1eaf3045f071928d5b48e1133df2e35823ccc` | Last retained manager/open-ended-fund evidence |
| #225 design note | `tasks/225-design-note.md` @ `35fd9ceb871ba3e7aab0a87f3924d37342652420` | `e300fdd7b07818da01e02592211bfbdba8124e2f` | Prior per-unit identity, budget, legal, and reopen contract |

## 3. Delta reconciliation: #218, #221, and #225

| Prior decision | Last retained disposition | #233 delta | State in this no-probe round |
|---|---|---|---|
| #218 — ETF discovery/NAV | `SOURCE_GAP_CLOSURE`; no route set closed ETF identity, NAV history, and lawful reuse | No new response, route schema, coverage ledger, correction contract, or reuse grant | `NOT_RECHECKED`; retain the last decision only |
| #221 — Fmarket runtime terms | `DISABLE_PENDING_PERMISSION`; valid calls fail before cache/network | No permission, route-term recheck, or provider/API dispatch | Runtime contract preserved; legal terms `NOT_RECHECKED` |
| #225 — equity-fund listing/NAV | `SOURCE_GAP_CLOSURE`; no same-owner complete route | No manager response, crosswalk, NAV row, page/total reconciliation, or rights evidence | `NOT_RECHECKED`; open-ended evidence stays separate |
| #233 combined primitive | New design task | Common qualification and release contract only | Empty chain; no candidate qualifies |

The strongest inherited ETF candidate is VinaCapital's manager-owned ETF identity/document family.
The strongest inherited open-ended-fund candidate is SSIAM's manager material. They are independent
product-class candidates: SSIAM must not be moved into the #218 ETF baseline, and VLGF's product
class remains `NOT_RETAINED` rather than inferred. The VinaCapital declared inception year is
candidate context only; #233 imposes no historical interval and this round does not turn that fact
into a coverage failure. No candidate inherits another owner's ID, route, history, or legal status.

## 4. Current public API and product semantics

The checked-out public boundary is preserved; this source-gap document authorizes no API change:

```python
vnfin.funds.source(http_get=None, timeout=25.0)
source.list_funds(asset_type=None, search="", page_size=100, include_metadata=True) -> FundList
source.nav_history(product_id: int, from_date=None, to_date=None) -> NavHistory
vnfin.funds.client  # alias of source with the same signatures
```

- Construction is lazy and offline. Each of the four current Fmarket operations fails before
  cache lookup, cached return, request-body construction, transport, parsing, or public empty
  production with `SourceUnavailable("SOURCE_DISABLED_PENDING_PERMISSION")` after valid caller
  arguments are checked.
- The four operation/route contracts are: `list_funds` → repository route `POST
  /res/products/filter`; `nav_history` → repository route `POST /res/product/get-nav-history`;
  `holdings` → repository route `GET /res/products/{id}`; and `asset_allocation` → the same
  repository detail route. These are repository compatibility facts, not fresh provider status,
  MIME, redirect, session, or permission evidence.
- `Fund.asset_type` is the current Fmarket `dataFundAssetType.code` asset-class field (for example
  `STOCK`, `BOND`, or `BALANCED`). It is not a discriminator for ETF, open-ended, closed-end, or
  other legal/product forms. A caller filter such as `asset_type="ETF"` is not response evidence.
  A future typed `product_type`/equivalent discriminator requires a separate API/model review; it
  is not frozen or reinterpreted here.
- `nav_history` returns provider-published NAV per fund unit (`VND/unit` in the existing model).
  Exchange close and iNAV are price observations, not NAV history, and cannot repair missing NAV.
- `NavPoint.date` is the provider NAV/as-of date. Publication/knowability, revision/correction,
  and library retrieval timestamps remain distinct. Missing dates stay missing: no zero-fill,
  forward-fill, interpolation, proxy, cross-owner repair, close/iNAV substitution, or inferred
  publication timestamp.

Current date inputs remain `datetime.date` or ISO `YYYY-MM-DD`, inclusive at both ends, and must be
validated before cache/network. `page_size` does not authorize returning an unreconciled first page;
a future qualified adapter must drain and reconcile provider pagination under one finite global
budget or fail atomically. No caller-visible provider page/cursor, new enum, source key, error,
product-ID coercion, or metadata field is frozen here.

## 5. Official candidate route matrix

Rows below are inherited static candidate facts, not current rechecks. Product-form claims are
limited to what the owner material explicitly states; the current `asset_type` field is never used
to upgrade them.

| Unit | Owner/path and operation | Retained identity/document fact | Exact gap/disposition |
|---|---|---|---|
| S01 | SSIAM `/en/products`, catalogue operation | Official catalogue and ETF/open-ended product material are present | No response-backed ID, machine route, complete universe, or reuse terms; `SOURCE_GAP` |
| S02 | SSIAM SSI-SCA manager page, open-ended listing | Official SSI-SCA identity and open-ended-fund context | No stable response ID/history binding or terms; `SOURCE_GAP` |
| S03 | SSIAM VLGF manager page, product listing | Official VLGF page; product class is `NOT_RETAINED` | No product-form proof, stable ID, history, or terms; `SOURCE_GAP` |
| S04 | SSIAM SSI-SCA documents, NAV operation | Manager/document family is identified | No provider-published NAV rows, bounds, revisions, pagination, or reuse; `SOURCE_GAP` |
| S05 | SSIAM VLGF documents, NAV operation | Manager/document family is identified | Product form, NAV rows, bounds, revisions, and reuse are `NOT_RETAINED`; `SOURCE_GAP` |
| V01 | VinaCapital VN100 ETF owner page, listing | Manager, FUEVN100, ETF label, HOSE context, and declared inception context | No machine listing ID/universe or reuse terms; `SOURCE_GAP` |
| V02 | VinaCapital disclosure/factsheet family, NAV | Owner document family names FUEVN100 and NAV-per-share context | No complete reconciled history, report totals/pages, correction rule, bounded route, or reuse; `SOURCE_GAP` |
| V03 | VinaCapital VEOF manager page, listing | Official open-ended-fund identity | No stable machine identity/history/legal route; `SOURCE_GAP` |
| V04 | VinaCapital VESAF manager page, listing | Official open-ended-fund identity | No stable machine identity/history/legal route; `SOURCE_GAP` |
| V05 | VinaCapital VDEF manager page, listing | Official open-ended-fund identity | No stable machine identity/history/legal route; `SOURCE_GAP` |
| C01 | VCBF MGF manager page, listing | Official fund identity/report context | No stable ID, history crosswalk, bounds, revisions, or reuse; `SOURCE_GAP` |
| C02 | VCBF BCF manager page, listing | Official fund identity/report context | No stable ID, history crosswalk, bounds, revisions, or reuse; `SOURCE_GAP` |
| C03 | VCBF AIF manager page, listing | Official fund identity/report context | No stable ID, history crosswalk, bounds, revisions, or reuse; `SOURCE_GAP` |
| C04 | VCBF MGF NAV-report family, NAV | Official report context for MGF | No daily row schema, page/total, revision, or reuse contract; `SOURCE_GAP` |
| C05 | VCBF BCF NAV-report family, NAV | Official report context for BCF | No daily row schema, page/total, revision, or reuse contract; `SOURCE_GAP` |
| C06 | VCBF AIF NAV-report family, NAV | Official report context for AIF | No daily row schema, page/total, revision, or reuse contract; `SOURCE_GAP` |
| E01 | Eastspring EVESG detail page, listing | Official code context | No stable history route or reuse terms; `SOURCE_GAP` |
| E02 | Eastspring EVESG archive documents, NAV | Dated archive context only | No reconciled daily rows, revision rule, or circulation consent; `SOURCE_GAP` |
| M01 | Manulife MAFEQI detail page, listing | Official open-ended-fund identity | No stable history response/crosswalk, bounds, or consent; `SOURCE_GAP` |
| M02 | Manulife MAFEQI history family, NAV | Product/detail context only | No provider-published route, bounds, revisions, or consent; `SOURCE_GAP` |
| D01 | Dragon official ETF-list article, listing | ETF code/index context and market-price/iNAV distinction | No NAV-per-unit owner route, history, coverage, or terms; `IDENTITY_SUPPORT_ONLY` |
| D02 | Dragon DCDS page/report, listing | Official product/report context | No stable history crosswalk or lawful reuse; `SOURCE_GAP` |
| D03 | Dragon DCDE page/report, listing | Official product/report context | No stable history crosswalk or lawful reuse; `SOURCE_GAP` |
| D04 | Dragon report family, NAV | NAV owner, rows, bounds, and revisions not established | `NAV_OWNER_GAP` |
| H01 | HOSE E1VFVN30 disclosure PDF, document | One official document identifies ETF/code/manager and NAV-per-certificate context | Not a discovery/history index or reuse grant; `DOCUMENT_SUPPORT_ONLY` |
| R01 | VSDC service pages, registry/context | Official depository/fund-service context | No selected NAV owner route, crosswalk, coverage, or redistribution; `REGISTRY_NOT_NAV_OWNER` |
| R02 | SSC disclosure pages, context | Official regulatory/disclosure context | No library data route or NAV-owner permission; `DISCLOSURE_CONTEXT_ONLY` |

The inherited primary URL identities are: Fmarket legal/catalogue `https://fmarket.vn/legal` and
`https://fmarket.vn/funds`; SSIAM products, SSI-SCA, and VLGF
`https://ssiam.com.vn/en/products`, `https://ssiam.com.vn/en/fund-information-ssi-sca`, and
`https://ssiam.com.vn/en/ssiam/fund-information-vlgf`; VinaCapital VN100 ETF and disclosure
`https://wm.vinacapital.com/investment-solutions/onshore-funds/vinacapital-vn100-etf/` and
`https://wm.vinacapital.com/information-disclosure/`; VEOF, VESAF, and VDEF
`https://vinacapital.com/investment-solutions/onshore-funds/veof/`,
`https://vinacapital.com/investment-solutions/onshore-funds/vesaf/`, and
`https://vinacapital.com/investment-solutions/onshore-funds/vdef/`; VCBF MGF, BCF, AIF, and NAV
reports from their official `vcbf.com` pages; Eastspring EVESG detail/archive; Manulife MAFEQI;
Dragon DCDS/DCDE and its official ETF-list article; HOSE's E1VFVN30 disclosure PDF; VSDC
`https://vsd.vn/en/`; and SSC `https://ssc.gov.vn/`. These are immutable inherited references,
not a new current reachability or legal review.

The primary URLs are inherited from the immutable #218/#225 artifacts. No new provider/API traffic
was made. A positive product page is not a positive history route; a PDF is not a pagination
contract; and a registry code is not a cross-owner NAV key.

## 6. Exact independent per-unit evidence ledger

Each row below is one owner/path/version/operation/product-class unit. Rows do not inherit transport,
coverage, budget, or legal values from another row. The compact tuple columns are fully ordered and
are deliberately repeated per unit.

**Transport tuple order:** `observation/method | status | complete_Content-Type | redirect/effective_identity | auth/session/UA/WAF`. `STATIC_REFERENCE` means a retained page/document observation and is not an HTTP-method claim; every unretained transport field is explicit. For the Fmarket rows, `REPOSITORY_CONTRACT_POST` or `REPOSITORY_CONTRACT_GET` identifies only the checked-out compatibility method.

**Dispatch tuple order:** `logical | physical | documents | pages | retries | redirects | compressed_bytes | decompressed_bytes | concurrency | rate_window | backoff`. These are #233 direct candidate data/API dispatches, all genuinely `0` because no route was called. Static-reading telemetry is separately `NOT_RETAINED`/`NOT_MEASURED`; it is never inferred from these zeros.

**Legal tuple order:** `automation | cache/storage/retention/deletion | caller_return | attribution | commercial | derivative | redistribution/resale | amendment | revocation | correction`. `LG` means `LEGAL_GAP`; `NR` means `NOT_RETAINED`; `F221` means the last retained #221 blocked term state for that exact operation, not a fresh current legal claim.

| Unit | Owner/operator and exact route | Transport tuple | Identity/coverage/outcome | Dispatch tuple | Legal tuple |
|---|---|---|---|---|---|
| F01 | Fincorp/Fmarket; `/res/products/filter`; listing | `REPOSITORY_CONTRACT_POST | NOT_PROBED | NOT_PROBED | NOT_PROBED | NOT_PROBED` | No ETF response identity/bounds; `DISABLED` | `0|0|0|0|0|0|0|0|0|0|0` | `F221|F221|F221|NR|F221|F221|F221|NR|NR|NR` |
| F02 | Fincorp/Fmarket; `/res/product/get-nav-history`; NAV | `REPOSITORY_CONTRACT_POST | NOT_PROBED | NOT_PROBED | NOT_PROBED | NOT_PROBED` | No ETF ID, NAV/date/revision/coverage; `DISABLED` | `0|0|0|0|0|0|0|0|0|0|0` | `F221|F221|F221|NR|F221|F221|F221|NR|NR|NR` |
| F03 | Fincorp/Fmarket; `/res/products/{id}`; holdings | `REPOSITORY_CONTRACT_GET | NOT_PROBED | NOT_PROBED | NOT_PROBED | NOT_PROBED` | No ETF detail identity or bounds; `DISABLED` | `0|0|0|0|0|0|0|0|0|0|0` | `F221|F221|F221|NR|F221|F221|F221|NR|NR|NR` |
| F04 | Fincorp/Fmarket; `/res/products/{id}`; allocation/detail | `REPOSITORY_CONTRACT_GET | NOT_PROBED | NOT_PROBED | NOT_PROBED | NOT_PROBED` | No ETF detail identity or bounds; `DISABLED` | `0|0|0|0|0|0|0|0|0|0|0` | `F221|F221|F221|NR|F221|F221|F221|NR|NR|NR` |
| S01 | SSIAM; `/en/products`; ETF/open-ended listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Catalogue support only; no stable machine ID/universe; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| S02 | SSIAM; SSI-SCA page; open-ended listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Official identity; response ID/history not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| S03 | SSIAM; VLGF page; product listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Product form `NOT_RETAINED`; ID/history not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| S04 | SSIAM; SSI-SCA document family; NAV | `STATIC_REFERENCE | NR | NR | NR | NR` | NAV rows/bounds/revisions not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| S05 | SSIAM; VLGF document family; NAV | `STATIC_REFERENCE | NR | NR | NR | NR` | Product form, NAV rows/bounds/revisions not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| V01 | VinaCapital; VN100 ETF owner page; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | FUEVN100/ETF identity support; machine ID/universe not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| V02 | VinaCapital; disclosure/factsheet family; NAV | `STATIC_REFERENCE | NR | NR | NR | NR` | NAV-per-share context; history/pages/revisions not reconciled; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| V03 | VinaCapital; VEOF manager page; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Open-ended identity only; machine universe not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| V04 | VinaCapital; VESAF manager page; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Open-ended identity only; machine universe not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| V05 | VinaCapital; VDEF manager page; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Open-ended identity only; machine universe not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| C01 | VCBF; MGF manager page; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Fund identity/report context; ID/bounds not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| C02 | VCBF; BCF manager page; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Fund identity/report context; ID/bounds not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| C03 | VCBF; AIF manager page; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Fund identity/report context; ID/bounds not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| C04 | VCBF; MGF NAV-report family; NAV | `STATIC_REFERENCE | NR | NR | NR | NR` | Report context; rows/pages/revisions not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| C05 | VCBF; BCF NAV-report family; NAV | `STATIC_REFERENCE | NR | NR | NR | NR` | Report context; rows/pages/revisions not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| C06 | VCBF; AIF NAV-report family; NAV | `STATIC_REFERENCE | NR | NR | NR | NR` | Report context; rows/pages/revisions not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| E01 | Eastspring; EVESG detail page; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Official code context; history route not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| E02 | Eastspring; EVESG archive family; NAV | `STATIC_REFERENCE | NR | NR | NR | NR` | Dated archive, not reconciled daily history; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| M01 | Manulife; MAFEQI detail page; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Official open-ended identity; history not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| M02 | Manulife; MAFEQI history family; NAV | `STATIC_REFERENCE | NR | NR | NR | NR` | Crosswalk/rows/bounds/revisions not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| D01 | Dragon; official ETF-list article; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | ETF code/index context; no NAV owner route; `IDENTITY_SUPPORT_ONLY` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| D02 | Dragon; DCDS page/report; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Product/report context; crosswalk not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| D03 | Dragon; DCDE page/report; listing | `STATIC_REFERENCE | NR | NR | NR | NR` | Product/report context; crosswalk not retained; `SOURCE_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| D04 | Dragon; report family; NAV | `STATIC_REFERENCE | NR | NR | NR | NR` | NAV owner, rows, bounds, and revisions not established; `NAV_OWNER_GAP` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| H01 | HOSE; E1VFVN30 disclosure PDF; document | `STATIC_REFERENCE | NR | NR | NR | NR` | One official document identity; no history ledger or licence; `DOCUMENT_SUPPORT_ONLY` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| R01 | VSDC; service pages; registry/context | `STATIC_REFERENCE | NR | NR | NR | NR` | Service context, not NAV owner; `REGISTRY_NOT_NAV_OWNER` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |
| R02 | SSC; disclosure pages; context | `STATIC_REFERENCE | NR | NR | NR | NR` | Regulatory context, no library route; `DISCLOSURE_CONTEXT_ONLY` | `0|0|0|0|0|0|0|0|0|0|0` | `LG|LG|LG|NR|LG|LG|LG|NR|NR|NR` |

The per-unit table deliberately does not turn static reading into runtime evidence. No route row is
`EMPTY`: no identity-matched, supported, provider-authoritative, reconciled empty response exists.

## 7. Qualification and no-false-absence contract

A future source qualifies only as one named owner, one exact route/version family, and one own
declared universe. A source-specific route may qualify only its proven fund IDs; it may not claim a
market-wide catalogue from one manager's partial universe.

- Discovery must return or owner-document stable product ID/code, official name, manager/issuer,
  explicit product form, currency, and provenance. Existing `asset_type` cannot satisfy the
  product-form predicate.
- History must use the same owner identity or an explicit source-owned, versioned crosswalk.
  Ticker, registry ID, manager name, exchange code, or a user search string is not an implicit
  crosswalk.
- Every point must be provider-published NAV per unit, finite and valid under the provider's
  unit/currency contract, tied to the selected product, and unique/ascending by NAV date.
- NAV/as-of, publication/knowability, correction/revision, and library retrieval timestamps are
  separate. Missing publication time is `NOT_RETAINED`.
- Exchange close, iNAV, indicative value, or a market-price column is never accepted as NAV and
  never repairs a missing NAV date.

| Outcome | Required evidence | Meaning |
|---|---|---|
| `FULL` | One qualified owner declares bounds covering the request; points/pages/totals/cursors reconcile; no unexplained interior gaps; publication calendar is understood | Complete own history only |
| `PARTIAL` | Same qualified owner declares a narrower boundary and reconciles every point inside it | Partial own history; never relabelled full |
| `EMPTY` | Identity-matched, supported, provider-authoritative, reconciled empty response | Typed empty only for real supported no-row |
| `UNKNOWN` | Missing identity, route, MIME, page, total, calendar, rights, or runtime axis | Inconclusive/fatal; not absence |
| `COVERAGE_GAP` | Qualified owner explicitly declares a supported boundary excluding the request | Honest bounded gap; never filled |

Blank body, HTML/WAF/challenge, timeout, connection failure, missing page, unreconciled total,
truncated bytes, ambiguous identity, or unauthorized empty body is failure/`UNKNOWN`, not `EMPTY`.
Private partial rows are discarded atomically.

## 8. Transport, scheduler, and diagnostic contract

No numeric source budget is authorized. A future qualified route must use one finite global ledger
for logical targets, physical requests, documents, pages/cursors, retries, redirects, compressed
bytes, decompressed bytes, concurrency, rate-window pacing, and backoff.

1. Reserve all applicable units atomically before dispatch. A failed reservation makes zero network
   calls. Unsupported product-class candidates skip without becoming attempts.
2. Retries reuse the same logical target and charge the same ledger. Hidden retries, date fan-out,
   unbounded redirects, and cross-owner stitching are forbidden.
3. Charge compressed and decompressed bytes separately. Either ceiling exhaustion discards private
   partial state and cannot produce false empty/partial output.
4. Page/count/cursor, redirect/effective identity, status/MIME, product identity, revision, and
   budget failures are fatal for that atomic result.
5. Retain only bounded, sanitized real attempts. Never fabricate an attempt or truncation marker;
   no raw URL/query, body, header, cookie, session, credential, provider prose, or unbounded ID is
   public diagnostic text.
6. A future JSON route must parse the complete `Content-Type` after its first colon, normalize the
   MIME, and reject maintenance HTML. A PDF route requires its own owner/parser contract.

Static evidence telemetry remains `NOT_RETAINED`/`NOT_MEASURED`; the direct candidate dispatch tuple
in section 6 is genuinely zero. These are separate ledgers and must not be merged.

## 9. Legal and reuse gate

Public reachability, a product page, PDF, exchange disclosure, registry record, robots file, or
working browser request is not permission for a public OSS library. Written owner terms must bind
the exact route and operation to:

- no-login automation, allowed UA/session/WAF behavior, rate, retry, concurrency, timeout, and
  maintenance rules;
- caller-facing return, cache/storage/retention/deletion, attribution, commercial use, derivative
  use, redistribution/resale, and downstream publication;
- stable identity, product-form ownership, revision/correction, amendment, revocation, and
  withdrawal; and
- finite logical/physical/document/page/retry/redirect and compressed/decompressed byte budgets
  with atomic no-partial behavior.

Fmarket permission must name all four existing operations: listing, NAV history, holdings, and
asset allocation/detail. It must bind the API host/routes, automation, caller return,
storage/retention, attribution/commercial/redistribution, rate/retry/WAF/session, version,
amendment, revocation, and correction. The current four-operation runtime remains
`DISABLE_PENDING_PERMISSION`; no alternative owner evidence overrides it.

## 10. Future API/RED compatibility matrix, not authorization

Only after a qualified-source design PASS may a separate API/model review freeze the smallest
backward-compatible carrier. The deferred RED matrix is complete and remains unauthorized now:

| Area | Required future RED cases |
|---|---|
| Lazy/inputs | construction is offline; invalid filter, product ID, `date`, ISO date, reversed inclusive window, and page-size inputs fail before cache/network |
| Product identity | explicit product-form positive; unknown/missing/contradictory form; ETF/open-ended cross-contamination; same-owner ID binding; cross-owner ID rejection |
| NAV values | NAV versus close/iNAV rejection; provider date/unit/currency identity; bool, non-finite, non-positive, malformed, duplicate/conflicting, and out-of-order values |
| Coverage | provider-declared `FULL`/`PARTIAL`/`EMPTY`/`UNKNOWN`; bounds, non-publication, pages/totals/cursors, interior gaps, revision/correction, and missing-stays-missing |
| Transport/budget | complete MIME after first colon; status/redirect/WAF/timeout/connection; retry/rate/backoff; document/page and compressed/decompressed byte exhaustion; atomic no-partial result |
| Public diagnostics | bounded sanitized source/attempt/error/warning/coverage carriers; UTC-aware retrieval metadata; DataFrame attrs; no raw provider prose |
| Result contract | frozen fields, `repr`, equality, serialization, and current snapshot behavior; no caller-visible provider cursor unless separately approved |
| Fmarket compatibility | all four operations through direct class, factory, and alias; exact disabled exception/reason; zero cache/network calls; existing `client is source` alias |
| Release | docs/API/units/skill/architecture/CHANGELOG as applicable; full offline tests; isolated wheel/sdist; blacklist/secret/diff/path/object/clean-tree gates |

No real fund list, NAV row, raw body, response digest, or hard-coded basket may become a fixture;
future executable tests use synthetic payloads only. A source-gap PASS authorizes the exact
publication transition in section 12, not RED, API/model changes, code, source registration, or
runtime capability.

## 11. Disposition and reopen evidence

The exact disposition is `SOURCE_GAP_CLOSURE`; the new listing/history chain stays empty. The
VinaCapital ETF evidence is the strongest inherited ETF candidate, while SSIAM remains an
independent open-ended-fund candidate. Neither closes identity, reconciled NAV history, bounded
transport, all budget dimensions, and public-OSS reuse rights conjunctively. No historical interval
is implied by this #233 packet.

Reopen requires a new owner-backed evidence packet that closes every identity, transport, coverage,
budget, and legal axis for one exact unit. No cross-source stitch, failover oracle, current-snapshot
backfill, exchange-close substitution, product-name join, or reinterpretation of `asset_type` is a
valid reopen.

## 12. Lifecycle and exact post-PASS transition

The historical intake/block record is clean-base backlog commit
`e6b777671eedc531d23aed6eff64113864c1b269`. It records reviewer delivery `0193ec5f`, target
`6a97eb7`, report commit `93b368d0628917c81903b30d0c7334f85db5a38b`, actor `vnfin-oss-reviewer`,
and the correction next action. The packet anchor is `f426e85322d565f85efd25b00b39807c628124f7`; public
triage receipt is `issuecomment-5415312502`. The prior builder intake state is historical only;
the final state in this report, design note, and backlog is actor `vnfin-oss-reviewer`, next
`RETURN_EXACT_SHA_DESIGN_VERDICT`.

The final correction must remain exactly three paths: this report, `tasks/233-design-note.md`, and
`tasks/active-backlog.md`, all descended from clean published base `ed55c048...`. It must reconcile
the stale #232 row to its published `DONE/CLOSED` facts before handoff. No provider probe, RED,
API/model change, production code, source registration, public issue, push, or close occurs while
correcting or before exact design PASS.

If this docs/source-gap design receives PASS, the allowed publication transition is exactly:

1. rerun merged exact-anchor gates;
2. push only the exact approved three-path lineage;
3. verify remote HEAD, clean-base ancestry, and approved paths;
4. post a clean public `SOURCE-GAP`/no-capability resolution; and
5. close #233 and re-read `CLOSED`/`COMPLETED`.

Those post-PASS steps publish the no-capability design only. They do not authorize provider probes,
RED, API/model decisions, production code, source registration, runtime capability, or coverage
claims.

### Bottom summary

- Decision: `SOURCE_GAP_CLOSURE`; no public fund/ETF listing or NAV route qualifies.
- Inherited #218/#221/#225 states are last-retained and `NOT_RECHECKED`, not asserted current.
- VinaCapital ETF and SSIAM open-ended evidence remain independent; no historical interval is imposed.
- `Fund.asset_type` remains an asset-class code, not an ETF/open-ended product discriminator.
- Four Fmarket operations, exact per-unit ledgers, all budget dimensions, and full future RED gates are preserved.
- Fmarket remains disabled/unprobed; `nav_history` is NAV per unit and missing stays missing.
- Current final actor is `vnfin-oss-reviewer`; next action is `RETURN_EXACT_SHA_DESIGN_VERDICT`.
- Before PASS: no probe, RED, API/model, code, source, push, or close; after PASS only the exact publication sequence applies.
