# FX source — Vietcombank public XML feed (`vietcombank`)

**Adapter:** `vnfin.fx.VietcombankFXSource` · **Role:** FX failover · **Auth:** none (no key).

## Endpoint

```
GET https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10
```

XML. Each `<Exrate CurrencyCode Buy Transfer Sell/>` is **VND per 1 unit of the foreign currency**.
The adapter uses `Transfer` as the rate, `Buy`→`bid`, `Sell`→`ask`. Values carry thousands commas
(`"26,111.00"`) → parsed via `float(v.replace(",", ""))`. Entries with `Transfer = 0` (no transfer
quote) are skipped. `<DateTime>` is VN-local (Asia/Ho_Chi_Minh, UTC+7) → normalized to UTC.

## Units / convention

Canonical vnfin unit: **VND per 1 unit of the base** — same convention as the primary, so the
failover unit-homogeneity guard accepts the chain with no inversion. ~20 currencies.

> **`Transfer` is a commercial-bank telegraphic-transfer / reference quote — NOT the SBV central
> rate.** It tracks the SBV central rate only loosely (within a band) and must not be labelled as
> the central rate in code or docs.

## Behaviour / limits

- Intraday updates on VN business days; no weekend/holiday data; **spot only** (no history).
- Self-declared cadence: **"only one request every 5 minutes"** — respect it; FX is excluded from
  the default scheduled health sweep for this reason.
- Historically reachable from non-VN IPs but no SLA; verify reachability before relying on it from
  overseas infrastructure.

## Terms / provenance

- Feed is marked **"For reference only"** with **no explicit open-data licence**. Conservative
  posture: runtime-fetch only, **no republishing/bundling** of the raw feed.
- Research provenance: [`docs/research/2026-06-18-fx-rates-sources.md`](../research/2026-06-18-fx-rates-sources.md).
