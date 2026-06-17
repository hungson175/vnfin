# Source provenance — VN market indices (value history + constituents)

Clean-room. VNStock and all derivatives were excluded from research and
implementation. Endpoints below were discovered by hitting each provider's own
server directly and the public TradingView-UDF protocol; confirmed empirically with
`curl -4` + a browser User-Agent. See `docs/research/2026-06-18-indices.md` for the
full research log.

## (a) Index VALUE history — reuses the price stack, values in POINTS

Index OHLCV is served by the same broker TradingView-UDF feeds used for stocks, but
**index values are quoted in points** (e.g. VNINDEX close ~1290.67), not thousands
of VND. The stock adapters apply `PRICE_SCALE = 1000.0` (thousands-of-VND → VND),
which would silently multiply index values by 1000. The index adapters
(`vnfin/indices/sources.py`) therefore subclass the broker UDF adapters and override
only:

- `PRICE_SCALE = 1.0` — values already in points,
- `CURRENCY = "points"` — an index level is not a money amount,
- `ADJUSTMENT_POLICY = RAW` — index levels are not split/dividend adjusted,
- per-source symbol aliasing,
- a distinct `NAME` for clean failover diagnostics.

The underlying price sources are **not modified** — composition/subclassing only.

| Adapter | Host | Path | Envelope | Notes |
|---|---|---|---|---|
| `VPSIndexSource` (`vps_index`) | `histdatafeed.vps.com.vn` | `/tradingview/history` | bare UDF | Deepest history (from 2000-07-28), widest symbol set, only source serving UPCOM correctly. **First in chain.** |
| `SSIIndexSource` (`ssi_index`) | `iboard-api.ssi.com.vn` | `/statistics/charts/history` | `{data:{...}}` | Deep history; UPCOM via SSI is unreliable (returns wrong 0.1 values). |
| `VNDirectIndexSource` (`vndirect_index`) | `dchart-api.vndirect.com.vn` | `/dchart/history` | bare UDF | Shallower (from 2017); good cross-check. |

Default failover order: `vps_index → ssi_index → vndirect_index`.

### Symbol aliasing (canonical → provider)

Canonical symbols accepted: `VNINDEX, VN30, HNXINDEX, HNX30, UPCOM, VNALLSHARE`
(plus any other symbol each provider serves passes through uppercased).

- `UPCOM` → VPS/SSI `UPCOMINDEX`; VNDIRECT `UPCOM`.
- `VNALLSHARE` → `VNALL` on all three.
- `HNXINDEX` works as-is on VPS/SSI (SSI is case-sensitive: `HNXINDEX`, not `HNXIndex`).

Auth: none. Networking: force IPv4 (`local_address="0.0.0.0"`) + browser UA + 25s
timeout (VN hosts hang over IPv6) — inherited from `UDFSource`.

## (b) Index CONSTITUENTS (members) — SSI iBoard query

`IndexConstituentsSource` (`ssi_iboard_query`):

```
GET https://iboard-query.ssi.com.vn/stock/group/{GROUP}
```

Returns `{"code":"SUCCESS","data":[{stockSymbol, exchange, companyNameEn, isin, ...}]}`,
one object per member. Verified groups: VN30(30), HNX30, VN100, VNMID, VNSML,
VNDIAMOND, VNFINLEAD, VNFINSELECT, plus full-exchange membership VNINDEX(673 HOSE)
and `HNXIndex`(300). Group aliasing: canonical `HNXINDEX` → provider `HNXIndex`
(case-sensitive).

Auth: none. IPv4 + browser UA.

### Weights are NOT available here

This endpoint exposes **membership only — no per-stock index weights**. `IndexMember.weight`
is therefore always `None` and `IndexConstituents.has_weights` is `False`; a
`weights_not_available` warning is attached. The research found no clean JSON weights
API (HOSE / VietStock / CafeF / finfo all dead-ended); official weighted baskets
exist only in HOSE periodic PDF/Excel. Weights are flagged, never fabricated.

## Compliance / redistribution

No published redistribution grant on any of these endpoints (no robots.txt — 404 on
all four hosts; pure JSON API backends). Treat as **read-only reference, runtime
fetch only** — no bundled/cached data, no redistribution of provider rows. Rate-limit
politely. Tests use only hand-crafted synthetic fixtures; no real provider rows are
committed.
