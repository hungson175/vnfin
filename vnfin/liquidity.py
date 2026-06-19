"""Daily liquidity & position sizing for allocation workflows (issue #146).

An additive, **offline** helper that turns an existing daily :class:`~vnfin.PriceHistory`
into liquidity/marketability stats and a max-order estimate. It is explicitly an
**approximation**: traded value is ``close * volume`` (``value_kind=
"close_x_volume_estimate"``), NOT a provider-published turnover field. It never fabricates
provider turnover, free float, market cap, foreign room, lot sizes, or transaction costs —
those need separate source/legal/provenance design (future issues).

    import vnfin
    from datetime import date

    prof = vnfin.liquidity.profile("FPT", date(2025, 1, 1), date(2025, 3, 31),
                                   capital_vnd=1_000_000_000)
    print(prof.avg_daily_value_vnd, prof.max_order_value_vnd, prof.warnings)
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import date, datetime

from ._contracts import canonical_security_symbol
from .exceptions import InvalidData
from .models import Interval, PriceBar, PriceHistory
from .validation import validate_date_range

__all__ = [
    "LiquidityPoint",
    "LiquidityProfile",
    "from_price_history",
    "profile",
]

_VALUE_KIND = "close_x_volume_estimate"
_ESTIMATE_WARNING = "traded_value_estimated_from_close_x_volume"


@dataclass(frozen=True)
class LiquidityPoint:
    """One day's marketability estimate. ``daily_value_vnd`` is ``close * volume`` — an
    ESTIMATE of traded value, not a provider-published turnover figure."""

    date: date
    close: float
    volume: int
    daily_value_vnd: float
    value_kind: str = _VALUE_KIND


@dataclass(frozen=True)
class LiquidityProfile:
    """Liquidity stats + max-order sizing derived from a daily equity PriceHistory."""

    symbol: str
    start: date
    end: date
    points: tuple[LiquidityPoint, ...]
    avg_daily_value_vnd: float
    median_daily_value_vnd: float
    avg_daily_volume: float
    median_daily_volume: float
    adv_fraction: float
    max_order_value_vnd: float
    capital_vnd: float | None = None
    capital_as_avg_daily_value_pct: float | None = None
    max_order_as_capital_pct: float | None = None
    value_kind: str = _VALUE_KIND
    source: str = ""
    currency: str = "VND"
    warnings: tuple[str, ...] = field(default=())

    def __len__(self) -> int:
        return len(self.points)


def _check_adv_fraction(adv_fraction) -> float:
    if isinstance(adv_fraction, bool) or not isinstance(adv_fraction, (int, float)):
        raise InvalidData(f"liquidity: adv_fraction must be a number, got {adv_fraction!r}")
    f = float(adv_fraction)
    if not math.isfinite(f) or not (0.0 < f <= 1.0):
        raise InvalidData(f"liquidity: adv_fraction must be in (0, 1], got {adv_fraction!r}")
    return f


def _check_capital(capital_vnd):
    if capital_vnd is None:
        return None
    if isinstance(capital_vnd, bool) or not isinstance(capital_vnd, (int, float)):
        raise InvalidData(f"liquidity: capital_vnd must be a number, got {capital_vnd!r}")
    c = float(capital_vnd)
    if not math.isfinite(c) or c <= 0:
        raise InvalidData(f"liquidity: capital_vnd must be a positive finite number, got {capital_vnd!r}")
    return c


def _bar_point(bar) -> LiquidityPoint:
    if not isinstance(bar, PriceBar):
        raise InvalidData(f"liquidity: bar is not a PriceBar, got {type(bar).__name__}")
    t = bar.time
    # B1: the bar key must be a timezone-AWARE datetime (the PriceBar.time contract); a
    # naive datetime or non-datetime is malformed (would corrupt the daily date key).
    if not isinstance(t, datetime) or t.utcoffset() is None:
        raise InvalidData(f"liquidity: bar time {t!r} must be a timezone-aware datetime")
    d = t.date()
    close = bar.close
    # B2: close inherits price positivity (close > 0); zero/negative/non-finite is malformed.
    # A zero VOLUME day is still allowed (no trades, valid price).
    if isinstance(close, bool) or not isinstance(close, (int, float)) or not math.isfinite(close) or close <= 0:
        raise InvalidData(f"liquidity: close must be a positive finite number, got {close!r} on {d}")
    vol = bar.volume
    if isinstance(vol, bool) or not isinstance(vol, int) or vol < 0:
        raise InvalidData(f"liquidity: malformed volume {vol!r} on {d}")
    return LiquidityPoint(date=d, close=float(close), volume=vol, daily_value_vnd=float(close) * vol)


def from_price_history(
    history,
    *,
    adv_fraction: float = 0.10,
    capital_vnd: float | None = None,
) -> LiquidityProfile:
    """Offline: compute a :class:`LiquidityProfile` from a daily equity PriceHistory."""
    frac = _check_adv_fraction(adv_fraction)
    cap = _check_capital(capital_vnd)
    if not isinstance(history, PriceHistory):
        raise InvalidData(f"liquidity: expected a PriceHistory, got {type(history).__name__}")
    if history.interval is not Interval.D1:
        raise InvalidData(f"liquidity: only daily (D1) history is supported, got {history.interval}")
    # Equity money series only — reject index point series / crypto / non-VND units.
    if history.currency != "VND" or history.value_unit != "VND":
        raise InvalidData(
            f"liquidity: requires a VND equity money series (currency/value_unit == 'VND'), "
            f"got currency={history.currency!r} value_unit={history.value_unit!r}"
        )
    if not history.bars:
        raise InvalidData("liquidity: empty price history")

    points = tuple(_bar_point(b) for b in history.bars)
    # B1: daily keys must be strictly ascending — a duplicate date would double-count and
    # an unsorted series would make start > end. (PriceHistory bars are documented
    # strictly-ascending; enforce it here too.)
    for i in range(len(points) - 1):
        if not (points[i].date < points[i + 1].date):
            raise InvalidData(
                f"liquidity: daily bars are not strictly ascending by date "
                f"({points[i + 1].date} after {points[i].date})"
            )
    values = [p.daily_value_vnd for p in points]
    volumes = [p.volume for p in points]
    avg_val = statistics.fmean(values)
    med_val = float(statistics.median(values))
    avg_vol = statistics.fmean(volumes)
    med_vol = float(statistics.median(volumes))
    max_order = avg_val * frac

    warnings = list(history.warnings) + [_ESTIMATE_WARNING]
    cap_pct = None
    max_order_cap_pct = None
    if avg_val <= 0:
        warnings.append("zero_liquidity: average daily value is 0 over the window")
    if cap is not None:
        cap_pct = (cap / avg_val * 100.0) if avg_val > 0 else None
        max_order_cap_pct = (max_order / cap * 100.0) if cap > 0 else None

    return LiquidityProfile(
        symbol=history.symbol,
        start=points[0].date,
        end=points[-1].date,
        points=points,
        avg_daily_value_vnd=avg_val,
        median_daily_value_vnd=med_val,
        avg_daily_volume=avg_vol,
        median_daily_volume=med_vol,
        adv_fraction=frac,
        max_order_value_vnd=max_order,
        capital_vnd=cap,
        capital_as_avg_daily_value_pct=cap_pct,
        max_order_as_capital_pct=max_order_cap_pct,
        source=history.source,
        currency=history.currency,
        warnings=tuple(warnings),
    )


def profile(
    symbol: str,
    start,
    end,
    *,
    adv_fraction: float = 0.10,
    capital_vnd: float | None = None,
    client=None,
    http_get=None,
    timeout: float = 25.0,
) -> LiquidityProfile:
    """Fetch daily history (via the price client) and compute a LiquidityProfile.

    Validates ``symbol``/dates/params BEFORE any provider call, so malformed inputs make
    zero client/source calls. ``client`` is injectable for deterministic offline tests.
    """
    sym = canonical_security_symbol(symbol, "symbol")
    validate_date_range(start, end, name="liquidity.profile")
    _check_adv_fraction(adv_fraction)
    _check_capital(capital_vnd)
    if client is None:
        from . import default_client

        client = default_client(http_get=http_get, timeout=timeout)
    history = client.get_history(sym, Interval.D1, start, end)
    return from_price_history(history, adv_fraction=adv_fraction, capital_vnd=capital_vnd)
