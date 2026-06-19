"""News domain (#140) — BYOK daily/historical headline metadata.

One obvious entry: :func:`search` (a convenience over :class:`AlphaVantageNewsSource`).
v1 is a single bring-your-own-key source (Alpha Vantage NEWS_SENTIMENT) returning links
and provider-supplied metadata/sentiment only — **never raw-scraped article text, full
bodies, or real-time feeds**. The API key comes from ``api_key=`` or the
``ALPHAVANTAGE_API_KEY`` env var; there is NO no-key default.

    import vnfin
    from datetime import date

    res = vnfin.news.search(tickers=("AAPL",), topics=("finance",),
                            start=date(2025, 1, 1), end=date(2025, 1, 31), limit=50)
    for item in res:
        print(item.published_at_utc, item.source, item.title, item.url)
"""
from __future__ import annotations

from .alpha_vantage import AlphaVantageNewsSource
from .models import NewsItem, NewsResult

__all__ = [
    "NewsItem",
    "NewsResult",
    "AlphaVantageNewsSource",
    "source",
    "search",
]


def source(provider: str = "alpha_vantage", *, api_key=None, http_get=None, timeout: float = 25.0):
    """Construct a news source. v1 supports only ``provider="alpha_vantage"`` (BYOK)."""
    if provider != "alpha_vantage":
        raise ValueError(f"unknown news provider {provider!r}; supported: 'alpha_vantage'")
    return AlphaVantageNewsSource(api_key=api_key, http_get=http_get, timeout=timeout)


def search(
    *,
    tickers=None,
    topics=None,
    start=None,
    end=None,
    sort: str = "latest",
    limit: int = 50,
    provider: str = "alpha_vantage",
    api_key=None,
    http_get=None,
    timeout: float = 25.0,
) -> NewsResult:
    """One-shot daily/historical headline-metadata search (BYOK). Requires at least one
    of ``tickers``/``topics`` to avoid an unbounded pull."""
    return source(provider, api_key=api_key, http_get=http_get, timeout=timeout).search(
        tickers=tickers, topics=topics, start=start, end=end, sort=sort, limit=limit
    )
