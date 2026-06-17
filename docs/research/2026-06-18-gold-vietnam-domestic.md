# Step research — Gold — Vietnam domestic (SJC bar, PNJ, DOJI, BTMC buy/sell prices)

**Date:** 2026-06-18  **Domain:** Gold — Vietnam domestic (SJC bar, PNJ, DOJI, BTMC buy/sell prices)  **Working sources:** 4

VNStock clean-room exclusion applied; endpoints from providers' own servers + public protocols.

> Four working no-auth VN gold sources verified by live curl: (1) BTMC public JSON API (api.btmc.vn) — SJC bar, nhẫn tròn trơn, VRTL bar, all 24k, plus silver, WITH intraday history baked into one response (83 timestamps). (2) PNJ edge-api JSON (edge-api.pnj.io) — clean spot prices for SJC, PNJ nhẫn, Kim Bảo, Phúc Lộc Tài, jewelry grades. (3) DOJI XML feed (giavang.doji.vn/api/giavang) — DOJI HN/HCM retail+wholesale buy/sell + USD/VND, spot. (4) webgia.com/gia-vang/sjc HTML — SJC official bar/nhẫn quotes (robots Disallow empty = allow-all), best practical SJC source since sjc.com.vn itself is Cloudflare-JS-challenge blocked. All three machine sources agreed: SJC 14,880,000 buy / 15,130,000 sel

> ⚠️ Redistribution: no published grant on these endpoints — personal/internal research, runtime-fetch only, no bundled data.

### BTMC (Bảo Tín Minh Châu) public price API
- **Host:** `api.btmc.vn`
- **Data:** Buy/sell prices for VN gold + silver products: VÀNG MIẾNG SJC, NHẪN TRÒN TRƠN (Vàng Rồng Thăng Long / VRTL), VÀNG MIẾNG VRTL, BẢN VÀNG ĐẮC LỘC, TRANG SỨC 999.9/99.9, plus silver (BẠC) bars. Each row: product name, karat (24k), buy (pb), sell (ps), world-price flag (pt), timestamp (d). Response includes 934 rows = many intraday snapshots (83 distinct timestamps) so intraday history is included.
- **Auth:** None per se, but a fixed query-string 'key' is required (public, embedded in BTMC's own widget): key=3kd8ub1llcg9t45hnoh8hmn7t5kc2v. No login/header token.
- **History:** Intraday only: one call returns ~83 distinct timestamps spanning the day; the SJC-gold product appeared in 8 intraday snapshots (price moved 15,180,000 -> 15,130,000 sell). No multi-day/EOD history. Snapshot every few mi
- **Coverage:** BTMC's own products + SJC bar + partner brands (DOJI/PNJ/Phú Quý buy quote) + market raw gold + silver. National (HCM/HN same quote in feed).
- **Format:** JSON. Shape: {"DataList":{"Data":[ {"@row":"N","@n_N":name,"@k_N":karat,"@h_N":"","@pb_N":buy,"@ps_N":sell,"@pt_N":worldflag,"@d_N":"DD/MM/YYYY HH:MM"}, ...]}}. Index N is appended to every key (n,k,h,pb,ps,pt,d) per row. Prices = VND per CHỈ as integer strings (e.g. "15130000"). karat field e.g. "24k".
- **Endpoints:** http://api.btmc.vn/api/BTMCAPI/getpricebtmc?key={KEY}  (KEY is the fixed public widget key above)
- **Terms:** http://api.btmc.vn/robots.txt returns 200 (no blanket disallow observed for the API path). Public widget endpoint intended for embedding BTMC's own ticker; key is shipped client-side. Lawful read of provider's own publis
```bash
curl -4 -s -m 25 -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'http://api.btmc.vn/api/BTMCAPI/getpricebtmc?key=3kd8ub1llcg9t45hnoh8hmn7t5kc2v'
```
_proof:_ VÀNG MIẾNG SJC (Vàng SJC) | karat 24k | buy 14880000 | sell 15130000 | d 17/06/2026 15:38 ; NHẪN TRÒN TRƠN (Vàng Rồng Thăng Long) | 24k | buy 14880000 | sell 15130000 ; intraday: 17/06/2026 13:59 buy 14980000 sell 15180000 -> 15:38 buy 14880000 sell 15130000

### PNJ ecom-frontend gold-price API
- **Host:** `edge-api.pnj.io`
- **Data:** Current buy (giamua) / sell (giaban) for PNJ gold lines: Vàng miếng SJC, Nhẫn Trơn PNJ 999.9, Vàng Kim Bảo 999.9, Vàng Phúc Lộc Tài 999.9, Vàng PNJ - Phượng Hoàng, Vàng nữ trang 999.9 / 999 / 9920 / 99 and other jewelry grades. Each item: masp (product code), tensp (name), giaban (sell), giamua (buy).
- **Auth:** None. Open JSON GET, no key/header required.
- **History:** Spot only (current snapshot, no history, no timestamp in body).
- **Coverage:** PNJ-branded products nationwide; includes an SJC bar row for cross-check.
- **Format:** JSON: {"data":[{"masp":"SJC","tensp":"Vàng miếng SJC 999.9","giaban":15130,"giamua":14880}, ...]}. Prices are in THOUSAND VND per CHỈ (giaban 15130 == 15,130,000 VND/chỉ). No timestamp field in payload.
- **Endpoints:** https://edge-api.pnj.io/ecom-frontend/v1/get-gold-price  (no params)
- **Terms:** edge-api.pnj.io/robots.txt = 403 (no robots served for the API host). This is PNJ's own ecommerce frontend API powering pnj.com.vn/blog/gia-vang. Lawful read of provider's published prices; attribute PNJ, poll modestly.
```bash
curl -4 -s -m 25 -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://edge-api.pnj.io/ecom-frontend/v1/get-gold-price'
```
_proof:_ {"masp":"SJC","tensp":"Vàng miếng SJC 999.9","giaban":15130,"giamua":14880}, {"masp":"N24K","tensp":"Nhẫn Trơn PNJ 999.9","giaban":15130,"giamua":14830}, {"masp":"24K","tensp":"Vàng nữ trang 999.9","giaban":15030,"giamua":14630}

### DOJI gold-price XML feed
- **Host:** `giavang.doji.vn`
- **Data:** DOJI domestic gold buy/sell: DOJI HN lẻ (retail), DOJI HN buôn (wholesale), DOJI HCM lẻ, DOJI HCM buôn; plus USD/VND rate and a jewelry list. Each <Row> has Name, Key, Sell, Buy.
- **Auth:** None for the feed itself, but an api_key query param is expected (public, embedded in DOJI's widget): api_key=REDACTED.
- **History:** Spot only. (Feed also references a Kitco international gold chart GIF, not data.)
- **Coverage:** DOJI HN + HCM, retail + wholesale.
- **Format:** XML: <GoldList><DGPlist><DateTime>..</DateTime><Row Name='DOJI HN lẻ' Key='..' Sell='151,300' Buy='148,800'/>...</DGPlist><IGPList>(USD/VND)</IGPList><JewelryList>...</JewelryList></GoldList>. UNITS INCONSISTENT: HN rows use comma-grouped values that read 10x (Sell='151,300'); HCM rows read as thousand-VND/chỉ (Sell='15,130'). Strip commas and normalize. DGPlist <DateTime> shows 01/01/1970 (stale 
- **Endpoints:** http://giavang.doji.vn/api/giavang/?api_key={KEY}  (KEY = fixed public widget key above)
- **Terms:** robots.txt = 403 (Apache, not served). DOJI's own public price widget feed. Stale DGPlist timestamp means: do NOT trust the gold-list time; validate prices against BTMC/PNJ before use. Attribute DOJI.
```bash
curl -4 -s -m 25 -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'http://giavang.doji.vn/api/giavang/?api_key=REDACTED'
```
_proof:_ <Row Name='DOJI HN lẻ' Key='dojihanoile' Sell='151,300' Buy='148,800' /> ; <Row Name='DOJI HCM lẻ' Sell='15,130' Buy='14,880' /> ; <Row Name='USD/VND' Sell='22,611' Buy='22,517' /> (IGPList DateTime 22:46 17/06/2026)

### webgia.com gia-vang (SJC + multi-brand HTML, practical SJC source)
- **Host:** `webgia.com`
- **Data:** SJC official bar + nhẫn quotes (Vàng SJC 1L/10L/1KG, SJC 5 chỉ, SJC 0.5/1/2 chỉ, Vàng nhẫn SJC 99,99%), each with buy + sell. Per-brand pages also exist for DOJI, PNJ, Phú Quý, Bảo Tín Minh Châu, Bảo Tín Mạnh Hải, Mi Hồng, Ngọc Thẩm + a world-gold page.
- **Auth:** None. Plain HTML GET.
- **History:** Spot only in static HTML. Chart links suggest up to 1-year history exists but the underlying data endpoint was not exposed in HTML (date/chart URLs 404). Use as SPOT source; treat history as unconfirmed.
- **Coverage:** SJC bar (the practical SJC source because sjc.com.vn is Cloudflare-blocked) + most major VN gold brands; HCM + HN.
- **Format:** Server-rendered HTML <table>; rows like: 'Hồ Chí Minh | Vàng SJC 1L, 10L, 1KG | 14.880.000 | 15.130.000'. Prices = VND per CHỈ, dot-grouped. Must parse table (no JSON in static HTML).
- **Endpoints:** https://webgia.com/gia-vang/sjc/ (SJC) ; https://webgia.com/gia-vang/doji/ ; /gia-vang/pnj/ ; /gia-vang/bao-tin-minh-chau/ ; /gia-vang/phu-quy/ ; /gia-vang/the-gioi/ (world). NOTE: chart subpaths (/bieu-do-1-nam etc.) and arbitrary date paths (/gia-vang/sjc/16-06-2026) return 404 — only today's date is linked; history needs the chart's XHR data endpoint (not identified).
- **Terms:** robots.txt = 'User-agent: *  Disallow:' (empty disallow = everything allowed to crawl). Third-party aggregator (not the issuer), so for authoritative SJC use it as a fallback/cross-check and attribute. Polite scraping (m
```bash
curl -4 -s -m 25 -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36' 'https://webgia.com/gia-vang/sjc/'
```
_proof:_ Hồ Chí Minh | Vàng SJC 1L, 10L, 1KG | 14.880.000 | 15.130.000 ; Vàng nhẫn SJC 99,99% 1 chỉ, 2 chỉ, 5 chỉ | 14.870.000 | 15.120.000 (matches BTMC + PNJ SJC quote 14,880,000/15,130,000 on 17/06/2026)

## Notes

CLEAN-ROOM: vnstock / VNStock and all derivatives (vnstocks.com, docs.vnstock.site, thinh-vu/vnstock, vnstock-hq, vnstock-agent, any wrapper/notebook) were fully excluded. Every endpoint below was discovered by hitting each provider's OWN server directly (BTMC public API, PNJ edge-api, DOJI XML feed) or via the provider site's own network paths (webgia), then verified empirically with curl. No vnstock code, docs, endpoint maps, or schemas were consulted.

KEY UNITS / GOTCHAS:
- BTMC + webgia + DOJI HN print VND per CHỈ (1/10 lượng) in full digits: e.g. 15,130,000 = sell price per chỉ. (10 chỉ = 1 lượng/tael.)
- PNJ edge-api returns price in THOUSAND VND per chỉ: giaban 15130 == 15,130,000 VND/chỉ. Multiply by 1000.
- DOJI XML mixes formats: "DOJI HN lẻ" Sell='151,300' is per-chỉ-in-hundreds quirk while "DOJI HCM lẻ" Sell='15,130' is thousand-VND/chỉ. The DOJI <DateTime> in DGPlist is sta
