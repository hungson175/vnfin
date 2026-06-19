"""World gold daily-history adapter — fawazahmed0 currency-api (CDN, no key).

This is the only verified world source that exposes **daily history**: each calendar
date is published as a separate date-pinned document on the jsdelivr CDN. We read the
``usd`` base document and take ``usd.xau`` (troy ounces of gold per 1 USD), then invert
it to get USD per troy ounce. So:

    USD/oz = 1 / usd.xau

* :meth:`get_quote` — latest spot (``@latest`` tag), USD/oz.
* :meth:`get_history` — builds a daily EOD series by fetching one date-pinned document
  per day in ``[start, end]``. Missing days (weekends/holidays/pre-coverage) simply 404
  and are skipped; if *every* day is missing the series is empty -> ``EmptyData``.

History coverage is ~2024-03 onward (per the research doc). Shape/units/endpoints from
docs/research/2026-06-18-gold-world.md (clean-room; no vnstock).
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone

from ..coerce import parse_provider_float
from ..exceptions import EmptyData, InvalidData, SourceUnavailable
from ..validation import validate_iso_date_string
from .base import GoldSource
from .models import GoldBar, GoldHistory, GoldQuote

_USD_PER_OZ = "USD/oz"
# Date-pinned npm tag (history) and @latest (spot), via jsdelivr CDN.
_CDN = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{tag}/v1/currencies/usd.json"
# Safety cap so a pathological range can't fan out into thousands of requests.
_MAX_DAYS = 1100


class CurrencyApiGoldSource(GoldSource):
    """Daily XAU/USD EOD history (and latest spot) by inverting ``usd.xau``."""

    name = "currency-api"
    provides_spot = True
    provides_history = True
    #: Declared unit for the failover unit-homogeneity guard (world gold = USD/oz).
    unit = _USD_PER_OZ

    def _url(self, tag: str) -> str:
        return _CDN.format(tag=tag)

    def _fetch_doc(self, tag: str) -> dict:
        url = self._url(tag)
        # Transport errors (incl. a 404 for a missing date) surface as
        # SourceUnavailable from the shared base; get_history catches that to skip
        # missing days.
        parsed = self._request_json(url, params=None, headers=None)
        if not isinstance(parsed, dict):
            raise InvalidData(f"{self.name}: unexpected payload type")
        return parsed

    def _usd_per_oz(self, doc: dict) -> float:
        try:
            usd_xau = doc["usd"]["xau"]
        except (KeyError, TypeError) as exc:
            raise InvalidData(f"{self.name}: missing usd.xau") from exc
        rate = parse_provider_float(usd_xau, label="usd.xau", source=self.name)
        if not math.isfinite(rate) or rate <= 0:
            # rate == 0 would divide-by-zero; surface as InvalidData (failover-safe).
            raise InvalidData(f"{self.name}: non-positive usd.xau {usd_xau!r}")
        return 1.0 / rate

    def get_quotes(self) -> tuple[GoldQuote, ...]:
        return (self.get_quote(),)

    def get_quote(self) -> GoldQuote:
        doc = self._fetch_doc("latest")
        price = self._usd_per_oz(doc)
        d = self._doc_date(doc)
        now = datetime.now(timezone.utc)
        tm = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) if d else now
        return GoldQuote(
            time=tm,
            product="XAU",
            buy=price,
            sell=price,
            unit=_USD_PER_OZ,
            currency="USD",
            source=self.name,
            fetched_at_utc=now,
        )

    def get_history(self, start: date, end: date) -> GoldHistory:
        lo, hi = self._range(start, end)
        now = datetime.now(timezone.utc)
        bars: list[GoldBar] = []
        d = lo
        while d <= hi:
            tag = d.isoformat()
            try:
                doc = self._fetch_doc(tag)
            except SourceUnavailable:
                # Missing date (404) / transient transport miss for this day -> skip it.
                d += timedelta(days=1)
                continue
            # Data-integrity check: the date-pinned document must know its own
            # date. If it claims a different date, something is wrong with the
            # CDN/publisher and stamping the requested date would silently poison
            # a returns series.
            doc_date = self._doc_date(doc)
            if doc_date is not None and doc_date != d:
                raise InvalidData(
                    f"{self.name}: document date {doc_date} does not match requested {d}"
                )
            price = self._usd_per_oz(doc)
            bars.append(GoldBar(date=d, price=price))
            d += timedelta(days=1)

        if not bars:
            raise EmptyData(f"{self.name}: no daily data in {lo}..{hi}")
        bars.sort(key=lambda b: b.date)
        return GoldHistory(
            product="XAU",
            unit=_USD_PER_OZ,
            value_unit=_USD_PER_OZ,  # world gold series is USD per troy ounce
            currency="USD",
            source=self.name,
            bars=tuple(bars),
            fetched_at_utc=now,
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
        if (hi - lo).days > _MAX_DAYS:
            raise InvalidData(f"currency-api: range too wide (> {_MAX_DAYS} days)")
        return lo, hi

    def _doc_date(self, doc: dict):
        raw = doc.get("date")
        if not raw:
            return None
        try:
            return validate_iso_date_string(raw, label="date")
        except InvalidData as exc:
            raise InvalidData(f"{self.name}: malformed date {raw!r}") from exc
