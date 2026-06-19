# Get daily financial-news headlines (BYOK)

`vnfin.news` returns **daily/historical headline metadata** (links, source, timestamp,
tickers/topics, optional provider sentiment) from Alpha Vantage's official
`NEWS_SENTIMENT` API. It is **bring-your-own-key** and returns metadata only — no scraped
article bodies, no full text, no real-time feed.

## Set up the key

Pass `api_key=` explicitly or set the `ALPHAVANTAGE_API_KEY` environment variable. There is
no no-key default; a missing key raises `SourceUnavailable` before any network call.

## Search headlines

```python
import vnfin
from datetime import date

res = vnfin.news.search(
    tickers=("AAPL",),          # canonical US tickers, <= 10
    topics=("finance",),        # official Alpha Vantage topic allow-list
    start=date(2025, 1, 1),
    end=date(2025, 1, 31),      # daily window (inverted ranges rejected)
    sort="latest",              # latest | earliest | relevance
    limit=50,                   # <= 100
    api_key="...",              # or ALPHAVANTAGE_API_KEY
)
for item in res:
    print(item.published_at_utc, item.source, item.title, item.url, item.overall_sentiment_label)
```

You must provide at least one of `tickers` / `topics` (to avoid an unbounded pull). Each
`NewsItem` is link + provenance + optional provider sentiment; `summary` is the provider's
own snippet only. Empty results raise `EmptyData`; provider rate-limit/invalid-key
envelopes raise `SourceUnavailable` (with the key redacted).

> Scope note: this is a daily/headline-metadata API, not a real-time monitor. See the
> [news-sources design notes](../design/news-sources.md) for source/legal rationale.
