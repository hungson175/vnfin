"""World gold daily-history backup — stooq ``xauusd`` CSV (no key).

Stooq publishes a daily OHLCV CSV for the world gold spot pair XAU/USD at
``https://stooq.com/q/d/l/?s=xauusd&i=d``. The body is a header row followed by one
line per trading day::

    Date,Open,High,Low,Close,Volume
    2024-03-05,2126.3,2141.7,2120.0,2128.2,0
    ...

``Close`` is the EOD price in **USD per troy ounce**, so this is a same-unit backup
for :class:`vnfin.gold.CurrencyApiGoldSource` (both ``USD/oz``) and slots straight
into the world-gold failover chain.

Failover-safe error mapping (never leak a raw exception):

* transport/network/non-2xx -> :class:`~vnfin.exceptions.SourceUnavailable`
  (handled by the shared :class:`~vnfin.transport.HttpDataSource`).
* the anti-bot **JavaScript proof-of-work challenge** some IPs receive instead of CSV
  -> :class:`~vnfin.exceptions.SourceUnavailable` (treated as "source unreachable
  from here", so the failover client moves on rather than failing the whole chain).
* malformed CSV (bad number / bad date / missing ``Close`` column)
  -> :class:`~vnfin.exceptions.InvalidData`.
* no rows in the requested window / ``No data`` sentinel
  -> :class:`~vnfin.exceptions.EmptyData`.

Endpoint, column order and units were taken from the provider's own server and the
project's research doc (docs/research/2026-06-18-gold-world.md). Clean-room; no vnstock.
"""
from __future__ import annotations

import csv as _csv
import io
import math
from datetime import date, datetime, timezone

from ..exceptions import EmptyData, InvalidData, SourceUnavailable
from ..validation import validate_iso_date_string
from .base import GoldSource
from .models import GoldBar, GoldHistory, GoldQuote

_USD_PER_OZ = "USD/oz"
_BASE_URL = "https://stooq.com/q/d/l/"
_SYMBOL = "xauusd"


class StooqGoldSource(GoldSource):
    """Daily XAU/USD EOD history (and last-bar spot) from the stooq CSV feed."""

    name = "stooq"
    provides_spot = True
    provides_history = True
    #: Declared unit for the failover unit-homogeneity guard (world gold = USD/oz).
    unit = _USD_PER_OZ

    def _fetch_csv(self) -> str:
        text = self._request_text(
            _BASE_URL, params={"s": _SYMBOL, "i": "d"}, headers=None
        )
        if isinstance(text, (bytes, bytearray)):
            text = text.decode("utf-8-sig", "replace")
        stripped = text.lstrip("﻿").lstrip()
        # Some IPs get an HTML JS proof-of-work challenge instead of CSV. Treat that
        # as "unreachable from here" so the failover client falls through.
        head = stripped[:512].lower()
        if head.startswith("<!doctype") or head.startswith("<html") or "<noscript" in head:
            raise SourceUnavailable(
                f"{self.name}: anti-bot challenge page (no CSV body returned)"
            )
        return stripped

    def _parse(self, text: str) -> list[GoldBar]:
        sentinel = text.strip().lower()
        if not sentinel or sentinel == "no data":
            raise EmptyData(f"{self.name}: empty CSV body")
        reader = _csv.reader(io.StringIO(text))
        rows = [r for r in reader if r and any(cell.strip() for cell in r)]
        if not rows:
            raise EmptyData(f"{self.name}: empty CSV body")
        header = [h.strip().lower() for h in rows[0]]
        required = ("date", "open", "high", "low", "close")
        try:
            di = header.index("date")
            oi = header.index("open")
            hi = header.index("high")
            li = header.index("low")
            ci = header.index("close")
        except ValueError as exc:
            raise InvalidData(
                f"{self.name}: missing one of {required} columns in header {rows[0]!r}"
            ) from exc
        bars: list[GoldBar] = []
        seen_dates: set = set()  # Issue #66: reject duplicate observation dates in one response
        for row in rows[1:]:
            if len(row) <= max(di, oi, hi, li, ci):
                raise InvalidData(f"{self.name}: short CSV row {row!r}")
            d = self._parse_date(row[di].strip())
            if d in seen_dates:
                raise InvalidData(f"{self.name}: duplicate observation date {d.isoformat()}")
            seen_dates.add(d)
            # Issue #53: validate the full OHLC row so a malformed high/low range
            # does not silently produce an untrustworthy close price.
            op = self._parse_price(row[oi].strip(), "Open")
            hp = self._parse_price(row[hi].strip(), "High")
            lp = self._parse_price(row[li].strip(), "Low")
            cp = self._parse_price(row[ci].strip(), "Close")
            if not (lp <= op <= hp and lp <= cp <= hp and lp <= hp):
                raise InvalidData(
                    f"{self.name}: OHLC invariant violated on {d.isoformat()}"
                )
            bars.append(GoldBar(date=d, price=cp))
        return bars

    def _parse_date(self, raw: str) -> date:
        try:
            return validate_iso_date_string(raw, label="date")
        except InvalidData as exc:
            raise InvalidData(f"{self.name}: bad date {raw!r}") from exc

    def _parse_price(self, raw: str, label: str = "Close") -> float:
        if raw == "" or raw.upper() == "N/A":
            raise InvalidData(f"{self.name}: missing {label} value")
        try:
            price = float(raw)
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"{self.name}: malformed {label} {raw!r}") from exc
        if not math.isfinite(price) or price <= 0:
            raise InvalidData(f"{self.name}: non-positive {label} {raw!r}")
        return price

    def get_quotes(self) -> tuple[GoldQuote, ...]:
        return (self.get_quote(),)

    def get_quote(self) -> GoldQuote:
        bars = self._parse(self._fetch_csv())
        if not bars:
            raise EmptyData(f"{self.name}: no rows for spot")
        bars.sort(key=lambda b: b.date)
        last = bars[-1]
        now = datetime.now(timezone.utc)
        tm = datetime(last.date.year, last.date.month, last.date.day, tzinfo=timezone.utc)
        return GoldQuote(
            time=tm,
            product="XAU",
            buy=last.price,
            sell=last.price,
            unit=_USD_PER_OZ,
            currency="USD",
            source=self.name,
            fetched_at_utc=now,
        )

    def get_history(self, start: date, end: date) -> GoldHistory:
        lo, hi = self._range(start, end)
        bars = self._parse(self._fetch_csv())
        bars = [b for b in bars if lo <= b.date <= hi]
        if not bars:
            raise EmptyData(f"{self.name}: no daily data in {lo}..{hi}")
        bars.sort(key=lambda b: b.date)
        return GoldHistory(
            product="XAU",
            unit=_USD_PER_OZ,
            value_unit=_USD_PER_OZ,
            currency="USD",
            source=self.name,
            bars=tuple(bars),
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _range(self, start: date, end: date):
        # Issue #42: reject malformed/non-date bounds before any network call.
        if not isinstance(start, (date, datetime)):
            raise InvalidData(f"{self.name}: start must be a date or datetime, got {type(start).__name__}")
        if not isinstance(end, (date, datetime)):
            raise InvalidData(f"{self.name}: end must be a date or datetime, got {type(end).__name__}")

        def as_date(x):
            return x.date() if isinstance(x, datetime) else x

        lo, hi = as_date(start), as_date(end)
        # Issue #6: a reversed window is a caller error, not something to silently swap.
        if lo > hi:
            raise InvalidData(f"{self.name}: start {lo} is after end {hi}")
        return lo, hi
