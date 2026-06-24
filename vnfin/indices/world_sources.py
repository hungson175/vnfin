"""World/US equity-index value sources (#177, extended #193).

Two clean-room, failover-safe daily-history adapters that return the shared
:class:`~vnfin.models.PriceHistory` (NOT a VN-index result). They form their OWN
failover chain (``default_world_index_sources`` / ``default_world_index_client``)
and never touch the VN HOSE/HNX ``index_history`` path.

(a) :class:`AlphaVantageIndexSource` — PRIMARY (and only server-usable) source,
    **bring-your-own-key (BYOK)**. Official Alpha Vantage ``TIME_SERIES_DAILY`` JSON
    for one of **5 allowlisted symbols**, ALL served in USD (every served instrument
    is a US-listed ETF) via the declarative ``WORLD_INDEX_SPECS`` table (#193):
    ``SPY``→SPY and ``QQQ``→QQQ are direct (caller asked the ETF, got the ETF); the
    three Asian indices are **loudly-labeled USD ETF proxies** — ``^N225``→EWJ,
    ``^SSEC``→FXI, ``^STI``→EWS — never silently the raw index. A proxy result
    carries both the ``PriceHistory.proxy_for`` field and a ``proxy_substitution``
    warning (emitted in the client). NOTE: the proxy ETFs are not even precise
    trackers (EWJ=MSCI Japan ≠ Nikkei 225; FXI=FTSE China 50 ≠ SSE Composite;
    EWS=MSCI Singapore ≠ STI) and embed USD/local FX. The key is read from
    ``api_key`` or ``ALPHAVANTAGE_API_KEY`` (the SAME key as the #140 news source) and
    is **redacted from every error**. With no key the source is cleanly skippable:
    ``has_key``/``supports`` are ``False`` and any data call raises
    :class:`~vnfin.exceptions.SourceUnavailable` BEFORE any network call (exact FRED
    BYOK pattern).

(b) :class:`StooqIndexSource` — FALLBACK, keyless best-effort (**residential-only**).
    Stooq's daily ``^spx`` CSV (the S&P 500 **index level**, in *points*). Anti-bot
    HTML/403 challenges — structural from datacenter IPs since ~2020-12 — surface as
    :class:`~vnfin.exceptions.SourceUnavailable` (never a hard crash), so the chain
    falls through. Effectively dead from servers/cloud/CI; works from residential IPs.
    Result unit: ``index points`` / ``points``.

With no key on a datacenter host BOTH legs are legitimately unavailable, so
``vnfin.indices.world(...)`` raises :class:`~vnfin.exceptions.MissingKey` (naming
``ALPHAVANTAGE_API_KEY`` + the symbol) — the actionable config signal. Set
``ALPHAVANTAGE_API_KEY`` to use world-index server-side. (``AllSourcesFailed`` is
reserved for the case where a key WAS set but AV still failed.) See
``docs/sources/indices-world.md``.

**Cross-instrument note:** SPY (USD/share) and ^SPX (index points) are different
instruments whose magnitudes differ ~10x. Only one leg is ever returned per call
(a disclosed failover-pick, not a merge); when the ^SPX leg is served instead of
the requested SPY, the world-index client appends a mechanical
``fallback_instrument_served`` warning (see :mod:`vnfin.indices.world_client`).

AV response-status mapping (failover-critical):
- ``"Error Message"`` (bad params/key)            -> ``InvalidData`` (redacted)
- ``"Note"`` / ``"Information"`` (free-tier throttle) -> ``SourceUnavailable``
  (best-effort; the chain falls over to Stooq, never crashes)
- non-dict / missing series / non-finite OHLC      -> ``InvalidData``

Clean-room: the endpoints, params, column order and units were taken only from
Alpha Vantage's and Stooq's own official documentation / servers and the project's
research/design notes. No vnstock or derivative was consulted.
"""
from __future__ import annotations

import csv as _csv
import io
import math
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

from ..coerce import parse_provider_float, parse_provider_int
from ..exceptions import EmptyData, InvalidData, SourceUnavailable, VnfinError
from ..models import AdjustmentPolicy, Interval, PriceBar, PriceHistory
from ..transport import DEFAULT_UA, HttpDataSource
from ..validation import validate_date_range, validate_iso_date_string

# Provenance constants (single source of truth; the client warning references these).
SPY_VALUE_UNIT = "USD/share (SPY ETF, S&P 500 proxy)"
SPX_VALUE_UNIT = "index points"
_AV_DEFAULT_CACHE_TTL = 21600.0  # 6h — AV free tier is 25 req/day; cache same-process calls
_PROVIDER_SPY = "SPY"
_PROVIDER_SPX = "^SPX"


@dataclass(frozen=True)
class _WorldIndexSpec:
    """Declarative per-symbol mapping (single source of truth, #193).

    All 5 series are served via AlphaVantage ``TIME_SERIES_DAILY`` in USD (every
    served instrument is a US-listed ETF). ``proxy_for`` is ``None`` when the
    ``av_ticker`` IS the asked instrument (SPY/QQQ — caller asked the ETF, got the
    ETF); for the three Asian indices the caller asked the raw index but a USD ETF
    proxy was served, so ``proxy_for`` is the asked symbol + ``fx_pair`` is set.
    """

    symbol: str            # canonical asked symbol (UPPER)
    av_ticker: str         # AV TIME_SERIES_DAILY symbol actually fetched
    value_unit: str        # explicit; all USD
    currency: str          # "USD"
    index_name: str        # human label for warnings/docs
    proxy_for: Optional[str]  # None when av_ticker IS the asked instrument; else asked
    fx_pair: Optional[str]    # e.g. "USD/JPY" for a proxy FX-embed note; None when not a proxy


# Per-symbol mapping table — single source of truth (spec §1). Keys are the canonical
# (UPPER) asked symbols; the client gates membership against these keys.
WORLD_INDEX_SPECS: dict[str, _WorldIndexSpec] = {
    "SPY": _WorldIndexSpec("SPY", "SPY", SPY_VALUE_UNIT, "USD", "S&P 500", None, None),
    "QQQ": _WorldIndexSpec(
        "QQQ", "QQQ", "USD/share (QQQ ETF, Nasdaq-100 proxy)", "USD",
        "Nasdaq-100", None, None,
    ),
    "^N225": _WorldIndexSpec(
        "^N225", "EWJ", "USD/share (EWJ ETF)", "USD",
        "Nikkei 225", "^N225", "USD/JPY",
    ),
    "^SSEC": _WorldIndexSpec(
        "^SSEC", "FXI", "USD/share (FXI ETF)", "USD",
        "SSE Composite", "^SSEC", "USD/CNY",
    ),
    "^STI": _WorldIndexSpec(
        "^STI", "EWS", "USD/share (EWS ETF)", "USD",
        "Straits Times Index", "^STI", "USD/SGD",
    ),
}

# The supported (asked) symbol set the client/accessor gates against (stable order).
SUPPORTED_WORLD_SYMBOLS: tuple[str, ...] = tuple(WORLD_INDEX_SPECS)


def world_index_spec(symbol) -> _WorldIndexSpec:
    """Resolve the ``_WorldIndexSpec`` for a (possibly un-canonicalized) symbol.

    Unknown/blank → the SPY spec (membership gating lives in the client/accessor, not
    the source — this preserves the direct-source default-to-SPY contract)."""
    canonical = AlphaVantageIndexSource._canonical_symbol(symbol)
    return WORLD_INDEX_SPECS.get(canonical, WORLD_INDEX_SPECS["SPY"])


def _as_window_date(value, label: str) -> date:
    """Coerce a caller window bound to a plain ``date`` (stable InvalidData on garbage)."""
    return validate_iso_date_string(value, label=label)


class AlphaVantageIndexSource(HttpDataSource):
    """BYOK Alpha Vantage ``TIME_SERIES_DAILY`` adapter for the 5 allowlisted world
    symbols, all served in USD (US-listed ETFs) via ``WORLD_INDEX_SPECS`` (#193)."""

    NAME = "alphavantage"
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        api_key: Optional[str] = None,
        http_get=None,
        timeout: float = 25.0,
        *,
        cache_ttl: float | None = _AV_DEFAULT_CACHE_TTL,
    ):
        super().__init__(http_get=http_get, timeout=timeout, cache_ttl=cache_ttl)
        self._api_key = self._normalize_key(api_key) or self._normalize_key(
            os.environ.get("ALPHAVANTAGE_API_KEY")
        )

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

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def has_key(self) -> bool:
        return bool(self._api_key)

    def supports(self, symbol=None) -> bool:
        """Capability probe (no network call): BYOK with no key is NOT capable, so a
        failover chain skips it BEFORE any request (FRED/news C4 contract)."""
        return self.has_key

    def get_history(
        self,
        symbol: str = _PROVIDER_SPY,
        start=None,
        end=None,
        *,
        interval: Interval = Interval.D1,
    ) -> PriceHistory:
        if not self._api_key:
            # BYOK: cleanly skippable -> catchable SourceError, NO network call.
            raise SourceUnavailable(
                f"{self.NAME}: no ALPHAVANTAGE_API_KEY configured (bring-your-own-key); "
                "pass api_key= or set the env var"
            )
        # Resolve the per-symbol spec (#193): SPY/QQQ direct, ^N225/^SSEC/^STI as
        # loudly-labeled USD ETF proxies. Unknown/blank → SPY spec (the client gates
        # membership; the source preserves the default-to-SPY direct-source contract).
        canonical = self._canonical_symbol(symbol)
        spec = world_index_spec(canonical)
        window_start = _as_window_date(start, "start") if start is not None else None
        window_end = _as_window_date(end, "end") if end is not None else None
        if window_start is not None and window_end is not None and window_start > window_end:
            raise InvalidData(
                f"{self.NAME}: start {window_start.isoformat()} is after end "
                f"{window_end.isoformat()}"
            )

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": spec.av_ticker,
            "outputsize": "full",
            "apikey": self._api_key,
            "datatype": "json",
        }
        data = self._fetch_json(params)

        if not isinstance(data, dict):
            raise InvalidData(f"{self.NAME}: {canonical}: response is not a JSON object")
        # AV status envelopes (provider-controlled; redact in case the key is echoed).
        # Q5 hard guard: an error envelope / no series for an ALLOWLISTED symbol means
        # AV does not cover the ticker → InvalidData NAMING the symbol, never empty.
        if "Error Message" in data:
            raise InvalidData(
                f"{self.NAME}: {canonical}: provider error: "
                f"{self._redact_key(str(data.get('Error Message')))}"
            )
        for throttle in ("Note", "Information"):
            if throttle in data:
                # Free-tier rate-limit/throttle -> best-effort skip (NOT a crash) so the
                # chain falls over to Stooq.
                raise SourceUnavailable(
                    f"{self.NAME}: provider {throttle}: {self._redact_key(str(data.get(throttle)))}"
                )

        series = data.get("Time Series (Daily)")
        if not isinstance(series, dict):
            # Q5: missing series for an allowlisted symbol → name it; never fabricate.
            raise InvalidData(
                f"{self.NAME}: {canonical}: missing 'Time Series (Daily)' object "
                f"(AV returned no data for {spec.av_ticker})"
            )

        bars = self._parse_bars(series, window_start, window_end)
        if not bars:
            raise EmptyData(f"{self.NAME}: no daily bars in requested window")

        return PriceHistory(
            symbol=canonical,
            interval=Interval.D1,
            adjustment_policy=AdjustmentPolicy.RAW,
            source=self.NAME,
            bars=tuple(bars),
            currency=spec.currency,
            value_unit=spec.value_unit,
            provider_symbol=spec.av_ticker,
            proxy_for=spec.proxy_for,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    @staticmethod
    def _canonical_symbol(symbol) -> str:
        if isinstance(symbol, str) and symbol.strip():
            return symbol.strip().upper()
        return _PROVIDER_SPY

    def _fetch_json(self, params):
        try:
            return self._request_json(
                self.BASE_URL,
                params=params,
                headers={"User-Agent": DEFAULT_UA, "Accept": "application/json"},
            )
        except VnfinError as exc:
            # Redact the key from the re-raised message. `from None` suppresses the
            # original exception chain in tracebacks; the suppressed __context__ is
            # itself key-safe because the transport layer redacts SENSITIVE_PARAMS, so
            # `from None` is for a clean message here, not the key-safety guarantee.
            raise type(exc)(self._redact_key(str(exc))) from None

    def _parse_bars(self, series, window_start, window_end) -> list[PriceBar]:
        bars: list[PriceBar] = []
        seen: set[date] = set()
        for raw_date, ohlcv in series.items():
            d = self._parse_date(raw_date)
            if window_start is not None and d < window_start:
                continue
            if window_end is not None and d > window_end:
                continue
            if d in seen:
                raise InvalidData(f"{self.NAME}: duplicate observation date {d.isoformat()}")
            seen.add(d)
            if not isinstance(ohlcv, dict):
                raise InvalidData(f"{self.NAME}: malformed bar for {raw_date!r}")
            o = self._field(ohlcv, "1. open", raw_date)
            h = self._field(ohlcv, "2. high", raw_date)
            lo = self._field(ohlcv, "3. low", raw_date)
            c = self._field(ohlcv, "4. close", raw_date)
            v = self._volume(ohlcv.get("5. volume"), raw_date)
            if not (lo <= o <= h and lo <= c <= h and lo <= h):
                raise InvalidData(f"{self.NAME}: OHLC invariant violated on {d.isoformat()}")
            bars.append(
                PriceBar(
                    time=datetime(d.year, d.month, d.day, tzinfo=timezone.utc),
                    open=o,
                    high=h,
                    low=lo,
                    close=c,
                    volume=v,
                )
            )
        bars.sort(key=lambda b: b.time)
        return bars

    def _parse_date(self, raw) -> date:
        try:
            return validate_iso_date_string(raw, label=f"{self.NAME} date")
        except InvalidData as exc:
            raise InvalidData(f"{self.NAME}: bad date {raw!r}") from exc

    def _field(self, ohlcv: dict, key: str, raw_date) -> float:
        if key not in ohlcv:
            raise InvalidData(f"{self.NAME}: missing {key!r} for {raw_date!r}")
        value = parse_provider_float(
            ohlcv.get(key), label=f"{key} for {raw_date}", source=self.NAME
        )
        # parse_provider_float rejects NaN/Inf but not sign; a non-positive price is
        # corrupt and (since all-negative OHLC still satisfies lo<=o<=h) would otherwise
        # be served as the trusted primary. Match the Stooq fallback's positivity guard.
        if value <= 0:
            raise InvalidData(
                f"{self.NAME}: non-positive {key} {value!r} for {raw_date!r}"
            )
        return value

    def _volume(self, raw, raw_date) -> int:
        if raw is None:
            return 0
        return parse_provider_int(raw, label=f"volume for {raw_date}", source=self.NAME)


class StooqIndexSource(HttpDataSource):
    """Keyless best-effort Stooq daily ^SPX CSV adapter (S&P 500 index points).

    Residential-only: structurally anti-bot-blocked from datacenter IPs since ~2020-12,
    so a datacenter ``SourceUnavailable`` from this adapter is expected, not a defect
    (see ``docs/sources/indices-world.md``).
    """

    NAME = "stooq"
    BASE_URL = "https://stooq.com/q/d/l/"

    @property
    def name(self) -> str:
        return self.NAME

    def supports(self, symbol=None) -> bool:
        return True

    def get_history(
        self,
        symbol: str = _PROVIDER_SPY,
        start=None,
        end=None,
        *,
        interval: Interval = Interval.D1,
    ) -> PriceHistory:
        # v1: `symbol` is normalized into the result label only — the CSV fetched below is
        # pinned to ^SPX regardless. SPY-only gating lives in the client/accessor, not here.
        canonical = AlphaVantageIndexSource._canonical_symbol(symbol)
        window_start = _as_window_date(start, "start") if start is not None else None
        window_end = _as_window_date(end, "end") if end is not None else None
        if window_start is not None and window_end is not None and window_start > window_end:
            raise InvalidData(
                f"{self.NAME}: start {window_start.isoformat()} is after end "
                f"{window_end.isoformat()}"
            )

        text = self._fetch_csv()
        bars = self._parse(text, window_start, window_end)
        if not bars:
            raise EmptyData(f"{self.NAME}: no daily bars in requested window")

        return PriceHistory(
            symbol=canonical,
            interval=Interval.D1,
            adjustment_policy=AdjustmentPolicy.RAW,
            source=self.NAME,
            bars=tuple(bars),
            currency="points",
            value_unit=SPX_VALUE_UNIT,
            provider_symbol=_PROVIDER_SPX,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _fetch_csv(self) -> str:
        text = self._request_text(
            self.BASE_URL, params={"s": "^spx", "i": "d"}, headers=None
        )
        if isinstance(text, (bytes, bytearray)):
            text = text.decode("utf-8-sig", "replace")
        stripped = text.lstrip("﻿").lstrip()
        # Some IPs get an HTML JS anti-bot challenge instead of CSV: treat as
        # "unreachable from here" so the chain falls through (never a hard crash).
        head = stripped[:512].lower()
        if head.startswith("<!doctype") or head.startswith("<html") or "<noscript" in head:
            raise SourceUnavailable(
                f"{self.NAME}: anti-bot challenge page (no CSV body returned)"
            )
        return stripped

    def _parse(self, text: str, window_start, window_end) -> list[PriceBar]:
        sentinel = text.strip().lower()
        if not sentinel or sentinel == "no data":
            raise EmptyData(f"{self.NAME}: empty CSV body")
        reader = _csv.reader(io.StringIO(text))
        rows = [r for r in reader if r and any(cell.strip() for cell in r)]
        if not rows:
            raise EmptyData(f"{self.NAME}: empty CSV body")
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
                f"{self.NAME}: missing one of {required} columns in header {rows[0]!r}"
            ) from exc
        vi = header.index("volume") if "volume" in header else None

        bars: list[PriceBar] = []
        seen: set[date] = set()
        for row in rows[1:]:
            need = max(di, oi, hi, li, ci, vi if vi is not None else 0)
            if len(row) <= need:
                raise InvalidData(f"{self.NAME}: short CSV row {row!r}")
            d = self._parse_date(row[di].strip())
            if d in seen:
                raise InvalidData(f"{self.NAME}: duplicate observation date {d.isoformat()}")
            seen.add(d)
            if window_start is not None and d < window_start:
                continue
            if window_end is not None and d > window_end:
                continue
            o = self._price(row[oi].strip(), "Open")
            h = self._price(row[hi].strip(), "High")
            lo = self._price(row[li].strip(), "Low")
            c = self._price(row[ci].strip(), "Close")
            if not (lo <= o <= h and lo <= c <= h and lo <= h):
                raise InvalidData(f"{self.NAME}: OHLC invariant violated on {d.isoformat()}")
            vol = self._volume(row[vi].strip()) if vi is not None else 0
            bars.append(
                PriceBar(
                    time=datetime(d.year, d.month, d.day, tzinfo=timezone.utc),
                    open=o,
                    high=h,
                    low=lo,
                    close=c,
                    volume=vol,
                )
            )
        bars.sort(key=lambda b: b.time)
        return bars

    def _parse_date(self, raw: str) -> date:
        try:
            return validate_iso_date_string(raw, label="date")
        except InvalidData as exc:
            raise InvalidData(f"{self.NAME}: bad date {raw!r}") from exc

    def _price(self, raw: str, label: str) -> float:
        if raw == "" or raw.upper() == "N/A":
            raise InvalidData(f"{self.NAME}: missing {label} value")
        try:
            price = float(raw)
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"{self.NAME}: malformed {label} {raw!r}") from exc
        if not math.isfinite(price) or price <= 0:
            raise InvalidData(f"{self.NAME}: non-positive {label} {raw!r}")
        return price

    def _volume(self, raw: str) -> int:
        if raw == "" or raw.upper() == "N/A":
            return 0
        try:
            return int(float(raw))
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"{self.NAME}: malformed Volume {raw!r}") from exc
