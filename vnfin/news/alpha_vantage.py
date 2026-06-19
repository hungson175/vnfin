"""Alpha Vantage NEWS_SENTIMENT adapter (#140) — BYOK, daily headline metadata.

v1 single BYOK source. Returns links + provider-supplied metadata/sentiment only —
**no raw scraping, no article-body fetch/redistribution, no real-time semantics**.
Synthetic fixtures only in the default suite. The API key is required (explicit arg or
``ALPHAVANTAGE_API_KEY`` env) and is redacted from every error/attempt message.

Clean-room: shape/params/topics learned only from Alpha Vantage's own official
``NEWS_SENTIMENT`` documentation (https://www.alphavantage.co/documentation/#news-sentiment).
"""
from __future__ import annotations

import math
import os
import re
from datetime import date, datetime, timezone
from typing import Optional

from ..exceptions import EmptyData, InvalidData, SourceUnavailable, VnfinError
from ..transport import DEFAULT_UA, HttpDataSource
from .models import NewsItem, NewsResult

# Official Alpha Vantage NEWS_SENTIMENT topic allow-list (per the documentation).
_TOPICS = frozenset(
    {
        "blockchain",
        "earnings",
        "ipo",
        "mergers_and_acquisitions",
        "financial_markets",
        "economy_fiscal",
        "economy_monetary",
        "economy_macro",
        "energy_transportation",
        "finance",
        "life_sciences",
        "manufacturing",
        "real_estate",
        "retail_wholesale",
        "technology",
    }
)
_SORTS = {"latest": "LATEST", "earliest": "EARLIEST", "relevance": "RELEVANCE"}
# US equity ticker grammar (allows '.'/'-' e.g. BRK.B, BF-B); upper-normalized.
_US_TICKER_RE = re.compile(r"[A-Z][A-Z0-9.\-]{0,15}")
# Provider-returned ticker grammar: Alpha Vantage's ticker_sentiment uses the equity
# form PLUS official CRYPTO:/FOREX: prefixes (e.g. CRYPTO:BTC, FOREX:USD).
_PROVIDER_TICKER_RE = re.compile(r"(?:CRYPTO:|FOREX:)?[A-Z][A-Z0-9.\-]{0,15}")
_MAX_TICKERS = 10
_MAX_LIMIT = 100


class AlphaVantageNewsSource(HttpDataSource):
    """BYOK Alpha Vantage NEWS_SENTIMENT — daily/historical headline metadata."""

    NAME = "alpha_vantage"
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None, http_get=None, timeout: float = 25.0):
        super().__init__(http_get=http_get, timeout=timeout)
        self._api_key = self._normalize_key(api_key) or self._normalize_key(
            os.environ.get("ALPHAVANTAGE_API_KEY")
        )

    @property
    def name(self) -> str:
        return self.NAME

    @staticmethod
    def _normalize_key(raw) -> str | None:
        if not isinstance(raw, str):
            return None
        key = raw.strip()
        return key if key else None

    def _redact_key(self, text):
        if self._api_key and isinstance(text, str):
            return text.replace(self._api_key, "***")
        return text

    # --- input validation -------------------------------------------------- #
    @staticmethod
    def _canon_ticker(raw) -> str:
        if not isinstance(raw, str):
            raise InvalidData(
                f"alpha_vantage: ticker must be a string, got {type(raw).__name__}"
            )
        # strip only spaces (NOT \n/\t/control) so a control char is rejected by
        # fullmatch rather than normalized away (B1).
        t = raw.strip(" ").upper()
        if not _US_TICKER_RE.fullmatch(t):
            raise InvalidData(f"alpha_vantage: malformed ticker {raw!r}")
        return t

    @staticmethod
    def _canon_provider_ticker(raw) -> str:
        # Provider ticker_sentiment symbols include official CRYPTO:/FOREX: prefixes
        # (B2). Same space-only strip so control chars fail closed.
        if not isinstance(raw, str):
            raise InvalidData(
                f"alpha_vantage: provider ticker must be a string, got {type(raw).__name__}"
            )
        t = raw.strip(" ").upper()
        if not _PROVIDER_TICKER_RE.fullmatch(t):
            raise InvalidData(f"alpha_vantage: malformed provider ticker {raw!r}")
        return t

    def _validate_tickers(self, tickers):
        if tickers is None:
            return None
        if isinstance(tickers, (str, bytes)) or not hasattr(tickers, "__iter__"):
            raise InvalidData("alpha_vantage: tickers must be a list/tuple of strings")
        out = [self._canon_ticker(t) for t in tickers]
        if not out:
            return None
        if len(out) > _MAX_TICKERS:
            raise InvalidData(f"alpha_vantage: at most {_MAX_TICKERS} tickers, got {len(out)}")
        return tuple(out)

    def _validate_topics(self, topics):
        if topics is None:
            return None
        if isinstance(topics, (str, bytes)) or not hasattr(topics, "__iter__"):
            raise InvalidData("alpha_vantage: topics must be a list/tuple of strings")
        out = []
        for t in topics:
            # space-only strip so a control char (e.g. "finance\n") fails the
            # allow-list check rather than being normalized into a valid topic (B1).
            if not isinstance(t, str) or t.strip(" ").lower() not in _TOPICS:
                raise InvalidData(f"alpha_vantage: unknown topic {t!r}")
            out.append(t.strip(" ").lower())
        return tuple(out) or None

    @staticmethod
    def _as_av_time(value, *, label, end: bool):
        """Map a date/datetime to provider ``YYYYMMDDTHHMM`` (no seconds; day-window edges)."""
        if isinstance(value, datetime):
            # Alpha Vantage's documented format is YYYYMMDDTHHMM (no seconds) (B3).
            return value.strftime("%Y%m%dT%H%M")
        if isinstance(value, date):
            return value.strftime("%Y%m%d") + ("T2359" if end else "T0000")
        raise InvalidData(f"alpha_vantage: {label} must be a date or datetime, got {value!r}")

    @staticmethod
    def _validate_limit(limit) -> int:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise InvalidData(f"alpha_vantage: limit must be a positive integer, got {limit!r}")
        if limit > _MAX_LIMIT:
            raise InvalidData(f"alpha_vantage: limit must be <= {_MAX_LIMIT}, got {limit}")
        return limit

    # --- public search ----------------------------------------------------- #
    def search(
        self,
        *,
        tickers=None,
        topics=None,
        start=None,
        end=None,
        sort: str = "latest",
        limit: int = 50,
    ) -> NewsResult:
        if not self._api_key:
            raise SourceUnavailable(
                "alpha_vantage: no ALPHAVANTAGE_API_KEY configured (bring-your-own-key); "
                "pass api_key= or set the env var"
            )
        tks = self._validate_tickers(tickers)
        tps = self._validate_topics(topics)
        if not tks and not tps:
            raise InvalidData("alpha_vantage: provide at least one of tickers or topics")
        # strip only spaces (NOT \n/\t/control) so 'latest\n' fails closed (B1) rather
        # than being normalized and sent.
        sort_key = sort.strip(" ").lower() if isinstance(sort, str) else None
        if sort_key not in _SORTS:
            raise InvalidData(f"alpha_vantage: sort must be one of {sorted(_SORTS)}, got {sort!r}")
        lim = self._validate_limit(limit)

        params = {"function": "NEWS_SENTIMENT", "apikey": self._api_key, "sort": _SORTS[sort_key], "limit": lim}
        if tks:
            params["tickers"] = ",".join(tks)
        if tps:
            params["topics"] = ",".join(tps)
        if start is not None or end is not None:
            tf = self._as_av_time(start, label="start", end=False) if start is not None else None
            tt = self._as_av_time(end, label="end", end=True) if end is not None else None
            if tf is not None and tt is not None and tf > tt:
                raise InvalidData(f"alpha_vantage: start {tf} is after end {tt}")
            if tf is not None:
                params["time_from"] = tf
            if tt is not None:
                params["time_to"] = tt

        parsed = self._fetch(params)
        items = self._parse_feed(parsed)
        return NewsResult(
            items=items,
            source=self.NAME,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    # --- fetch + parse ----------------------------------------------------- #
    def _fetch(self, params):
        try:
            return self._request_json(self.BASE_URL, params=params, headers={"User-Agent": DEFAULT_UA, "Accept": "application/json"})
        except VnfinError as exc:
            # Never let a provider/transport message leak the key.
            raise type(exc)(self._redact_key(str(exc))) from None

    def _parse_feed(self, parsed) -> tuple[NewsItem, ...]:
        if not isinstance(parsed, dict):
            raise InvalidData(f"{self.NAME}: response is not a JSON object")
        # Alpha Vantage informational/error envelopes (rate-limit / bad key / note).
        for key in ("Error Message", "Information", "Note"):
            if key in parsed:
                raise SourceUnavailable(
                    f"{self.NAME}: provider {key}: {self._redact_key(str(parsed.get(key)))}"
                )
        feed = parsed.get("feed")
        if not isinstance(feed, list):
            raise InvalidData(f"{self.NAME}: missing/non-list 'feed'")
        if not feed:
            raise EmptyData(f"{self.NAME}: empty feed")
        items: list[NewsItem] = []
        seen: dict[str, NewsItem] = {}
        for row in feed:
            item = self._parse_row(row)
            prev = seen.get(item.url)
            if prev is not None:
                if prev != item:
                    raise InvalidData(f"{self.NAME}: conflicting duplicate news url {item.url!r}")
                continue  # identical duplicate -> keep first
            seen[item.url] = item
            items.append(item)
        return tuple(items)

    def _parse_row(self, row) -> NewsItem:
        if not isinstance(row, dict):
            raise InvalidData(f"{self.NAME}: feed row is not an object")
        title = self._req_str(row, "title")
        url = self._req_str(row, "url")
        source = self._req_str(row, "source")
        published = self._parse_time(self._req_str(row, "time_published"))

        summary = row.get("summary")
        if summary is not None and not isinstance(summary, str):
            raise InvalidData(f"{self.NAME}: summary must be a string")

        score = row.get("overall_sentiment_score")
        if score is not None:
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
                raise InvalidData(f"{self.NAME}: malformed overall_sentiment_score {score!r}")
            score = float(score)
        label = row.get("overall_sentiment_label")
        if label is not None and not isinstance(label, str):
            raise InvalidData(f"{self.NAME}: overall_sentiment_label must be a string")

        tickers = self._parse_ticker_sentiment(row.get("ticker_sentiment"))
        topics = self._parse_topics(row.get("topics"))
        return NewsItem(
            title=title,
            url=url,
            source=source,
            published_at_utc=published,
            tickers=tickers,
            topics=topics,
            summary=summary,
            overall_sentiment_score=score,
            overall_sentiment_label=label,
        )

    def _req_str(self, row, key) -> str:
        v = row.get(key)
        if not isinstance(v, str) or not v.strip():
            raise InvalidData(f"{self.NAME}: feed row missing/empty {key}")
        return v

    def _parse_time(self, raw: str) -> datetime:
        try:
            return datetime.strptime(raw, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise InvalidData(f"{self.NAME}: malformed time_published {raw!r}") from exc

    def _parse_ticker_sentiment(self, raw) -> tuple[str, ...]:
        if raw is None:
            return ()
        if not isinstance(raw, list):
            raise InvalidData(f"{self.NAME}: ticker_sentiment must be a list")
        out = []
        for entry in raw:
            if not isinstance(entry, dict) or "ticker" not in entry:
                raise InvalidData(f"{self.NAME}: malformed ticker_sentiment entry")
            out.append(self._canon_provider_ticker(entry["ticker"]))
        return tuple(out)

    @staticmethod
    def _parse_topics(raw) -> tuple[str, ...]:
        if raw is None:
            return ()
        if not isinstance(raw, list):
            raise InvalidData("alpha_vantage: topics must be a list")
        out = []
        for entry in raw:
            if isinstance(entry, dict) and isinstance(entry.get("topic"), str):
                out.append(entry["topic"])
            elif isinstance(entry, str):
                out.append(entry)
            else:
                raise InvalidData("alpha_vantage: malformed topic entry")
        return tuple(out)
