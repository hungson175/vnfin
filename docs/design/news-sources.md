# News sources — design, legal & provenance (#140)

`vnfin.news` is a **BYOK, daily/historical headline-metadata** API. It returns links and
provider-supplied metadata/sentiment — never raw-scraped article bodies, full text, or
real-time feeds.

## Source choice (v1)

**Alpha Vantage `NEWS_SENTIMENT`** is the single v1 source — an official, documented,
bring-your-own-key API (https://www.alphavantage.co/documentation/#news-sentiment). The
caller supplies the key (`api_key=` or `ALPHAVANTAGE_API_KEY`); there is no no-key default
and no shipped/demo key.

Deferred (not implemented in v1):

- **Finnhub company news** — also viable BYOK; kept out of v1 to avoid a multi-source
  failover/provenance design.
- **GDELT** — open but not finance-specific and global/real-time; possibly useful later for
  macro/news analytics, not a first US finance-news source.

## Explicitly excluded (clean-room / licensing / safety)

- **No raw web/RSS scraping** and **no fetching of article pages** — licensing,
  redistribution, anti-scraping, and injection concerns.
- **No full article text** stored or redistributed — links + provider metadata only;
  `summary` is the provider's own snippet, nothing more.
- **No real-time / minute-second feed semantics** — the API is daily-window oriented.
- **No vnfin-built sentiment model** — provider sentiment metadata is passed through with
  provenance, never recomputed or rebranded.
- No VNStock or derived material was consulted (clean-room).

## Safety properties

- API key required; missing key fails closed with `SourceUnavailable` before any network.
- The key is redacted from every exception/attempt message.
- Inputs are validated before network: canonical US tickers (`[A-Z][A-Z0-9.-]{0,15}`, ≤10),
  an official topic allow-list, validated/inverted date windows, a bounded `limit` (≤100),
  and at least one of `tickers`/`topics` to avoid unbounded pulls.
- Default tests are offline with synthetic fixtures only (no real article rows committed);
  an optional live test is gated by `VNFIN_LIVE=1` + `ALPHAVANTAGE_API_KEY`.
