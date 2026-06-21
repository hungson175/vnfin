# #163 — finfo ex-date leg: non-sandboxed probe evidence (build-blocker resolution)

Reviewer assigned the build-blocking probe: confirm the real VNDirect finfo `/v4/events` response
shape (they were egress-blocked). Done — with a **host correction** + a cross-source ex-date proof.

## HOST CORRECTION (important — both my earlier scoping and the source verdict named the wrong host)
- `finfo-api.vndirect.com.vn` = **VNDirect INTERNAL host.** Authoritative public DNS (Google 8.8.8.8
  AND Cloudflare 1.1.1.1 both) returns **`10.210.100.8`** — a private RFC1918 address. NOT publicly
  routable; every probe to it times out. This is a real source fact, NOT a sandbox artifact (confirmed
  via two independent public DoH resolvers). See [[vndirect-public-host-is-api-finfo-not-finfo-api]].
- **Correct PUBLIC host = `api-finfo.vndirect.com.vn`** — CNAME → `apifinfo.trafficmanager.net`
  (Azure Traffic Manager), public IPs in VNDirect's `125.212.254.0/24` block; same public-edge pattern
  as the already-accepted `dchart-api.vndirect.com.vn` (CNAME `dchart-api.trafficmanager.net`). Reachable,
  keyless, JSON. Posture = same MEDIUM risk as the existing `vnfin/sources/vndirect.py`.

## Endpoint + envelope (verified live)
`GET https://api-finfo.vndirect.com.vn/v4/events?q=code:{TICKER}~type:DIVIDEND&size={N}&sort=effectiveDate:desc`
Envelope: `{"data":[...], "currentPage", "size", "totalElements", "totalPages"}`.
`type` values seen: `DIVIDEND`, `MEETING`, `LISTED`. Filter dividends with `~type:DIVIDEND`.

## Record field map (verified)
`id, code, group, type, typeDesc, note, dividend (VND/share float), ratio (% float), divPeriod, divYear,`
`disclosureDate, effectiveDate, expiredDate, actualDate, locale, newsId`. Dates are ISO `YYYY-MM-DD`.

| field | meaning (confirmed) |
|---|---|
| `disclosureDate` | announcement date |
| **`effectiveDate`** | **EX-DATE (ngày GDKHQ)** — the missing VSDC leg |
| `expiredDate` | = pay/execution date in samples |
| `actualDate` | payment/execution date |
| `dividend` / `ratio` | cash VND-per-share / percent |

## Cross-source proof that `effectiveDate` = ex-date (GMD, divYear 2024)
- finfo: `effectiveDate=2025-07-09`, `actualDate=2025-07-17`, `ratio=20.0`, `dividend=2000.0`.
- reviewer's VSDC ground truth: GMD cash **2000đ / record 10-07 / pay 17-07**.
- → finfo `effectiveDate` (07-09) = VSDC record (07-10) **− 1 business day** = the ex-date (VN convention:
  ex = record − 1 trading day). finfo `actualDate` (07-17) = VSDC pay (07-17). ratio/cash match.
**Conclusion (for reviewer to confirm):** VSDC = spine (record/pay/ratio, deep history) + finfo
`effectiveDate` = ex-date leg. Architecture validated.

## History floor (ex-date coverage is SHALLOWER than VSDC)
VNM earliest DIVIDEND `effectiveDate` = **2022-01-10** (~30 div events). GMD = 12. So the finfo ex-date
leg covers **~2022+**; pre-2022 events (VSDC has ~2011) will carry record/pay/ratio but **NO ex-date**
→ needs a warning token (e.g. `ex_date_unavailable`) on those rows, never fabricate.

## Locale duplication (adapter must dedupe)
Every event appears TWICE — `locale: "VN"` and `"EN"` (only `typeDesc` differs: "Cổ tức bằng tiền" vs
"Cash Dividend"). Dedupe by `(code, type, divYear, effectiveDate, ratio)`; pick one locale deterministically.

## Cassette vs no-real-rows reconciliation (reviewer's call)
Project rule: synthetic fixtures committed; real cassettes private/gitignored; no real broker rows
bundled. Reviewer asked to "pin the field map in a committed VCR cassette." Proposed reconciliation:
**commit a SYNTHETIC fixture mirroring this EXACT verified shape** (real keys/structure, synthesized
values + the ~2022 floor) for the contract test; keep any raw real recording **gitignored** for opt-in
replay. That pins the field map per the reviewer's intent without committing real rows. Confirm at gate.
