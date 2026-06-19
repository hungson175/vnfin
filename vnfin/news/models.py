"""Typed models for the news domain (#140) — headline metadata only.

These carry provider-supplied headline/sentiment **metadata** (title, link, source,
timestamp, tickers/topics, optional provider summary + sentiment) — never full article
text. All datetimes are tz-aware UTC.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class NewsItem:
    """One headline's metadata (link + provenance + optional provider sentiment)."""

    title: str
    url: str
    source: str  # publisher/source name from the provider, NOT the adapter name
    published_at_utc: datetime  # tz-aware UTC
    tickers: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    summary: str | None = None  # provider-supplied short snippet only (never scraped body)
    provider_id: str | None = None
    overall_sentiment_score: float | None = None
    overall_sentiment_label: str | None = None
    source_adapter: str = "alpha_vantage"


@dataclass(frozen=True)
class NewsResult:
    """A query result: a tuple of :class:`NewsItem` plus provenance metadata."""

    items: tuple[NewsItem, ...]
    source: str = "alpha_vantage"
    fetched_at_utc: datetime | None = None
    warnings: tuple[str, ...] = field(default=())

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)
