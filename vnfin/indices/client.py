"""High-level index client.

``IndexClient`` composes the existing ``FailoverPriceClient`` over index-aware UDF
sources (part a — index VALUE history) and wraps the SSI constituents source
(part b — membership). It deliberately does NOT modify the price sources; it builds
its own failover chain over index-specific adapters so index values stay in points.

Failover order for index values: VPS (deepest history, widest symbol set) -> SSI
(deep, enveloped) -> VNDIRECT (shallower, good cross-check). VPS is first because it
is the only source that serves UPCOM correctly and covers all sector indices.
"""
from __future__ import annotations

from datetime import date
from typing import Optional, Union

from .._resample import apply_interval
from ..client import FailoverPriceClient
from ..exceptions import InvalidData, VnfinError
from ..models import AdjustmentPolicy, Interval, PriceHistory
from .._contracts import (
    canonical_security_symbol,
    is_known_index,
    is_value_history_index,
    resolve_index_alias,
)
from ..validation import validate_date_range, validate_non_empty_string
from .models import IndexConstituents
from .sources import (
    IndexConstituentsSource,
    SSIIndexSource,
    VNDirectIndexSource,
    VPSIndexSource,
)

# Default index-value failover chain (deepest/widest first).
_DEFAULT_INDEX_SOURCE_CLASSES = (VPSIndexSource, SSIIndexSource, VNDirectIndexSource)


def default_index_sources(http_get=None, timeout: float = 25.0):
    """Instantiate the default index-value failover chain (values in points)."""
    return [c(http_get=http_get, timeout=timeout) for c in _DEFAULT_INDEX_SOURCE_CLASSES]


def _validate_index_selector(value, name: str = "index") -> str:
    """Issue #75/#9: an index selector is a canonical security/index identifier —
    reject non-string/bytes/blank/whitespace/punctuation/internal-space before any
    URL/provider call; normalize padded/lowercase (e.g. " vn30 " -> "VN30")."""
    return canonical_security_symbol(value, name)


def _unservable_index_error(symbol: str) -> InvalidData:
    """Issue #174: build the rejection for a symbol the index path cannot serve, branching
    on whether it is a RECOGNIZED index (deny-list) vs a genuinely unknown / equity symbol.

    The bug this fixes is a contradictory routing LOOP: a deny-only identifier (a known index
    that is not value-history-servable, e.g. the HOSE sector indices, VN100, VNDIAMOND, …) was
    told to "use prices.history() for stocks", but the price path correctly rejects it as an
    index and points back here — bouncing the caller between the two namespaces forever. So:

    * recognized index but no served value-history -> a TERMINAL diagnostic that names it as an
      index and does NOT mention ``prices.history``/"for stocks" (serving these is a tracked
      enhancement, not this path's job).
    * genuinely unknown / equity symbol -> the original route-to-prices guidance, which is
      correct ONLY here.

    Called on the ALREADY alias-resolved symbol, so served aliases (HNX -> HNXINDEX) never reach
    it. Single source so both ``index_history`` and ``index_history_stitched`` stay identical.
    """
    if is_known_index(symbol):
        return InvalidData(
            f"symbol {symbol} is a recognized market index, but its value history is not "
            f"supported in this version (no served source); it is not available via "
            f"index_history()."
        )
    return InvalidData(
        f"symbol {symbol} is not a known market index; "
        "use vnfin.prices.history() for stocks"
    )


class IndexClient:
    """Stable API for VN market-index data.

    - ``index_history(symbol, start, end)`` -> ``PriceHistory`` with ``currency='points'``.
    - ``constituents(index)`` -> ``IndexConstituents`` (membership; no weights).
    """

    def __init__(
        self,
        sources=None,
        constituents_source: Optional[IndexConstituentsSource] = None,
        max_attempts: int = 3,
        http_get=None,
        timeout: float = 25.0,
    ):
        if sources is None:
            sources = default_index_sources(http_get=http_get, timeout=timeout)
        self._client = FailoverPriceClient(sources, max_attempts=max_attempts)
        # Issue #168: this is the legitimate index value-history path — the underlying
        # price client must NOT reject index symbols here (the IndexClient methods apply
        # their own value-history ALLOW-LIST guard instead). Private flag → no snapshot churn.
        self._client._reject_index_symbols = False
        self._constituents = constituents_source or IndexConstituentsSource(
            http_get=http_get, timeout=timeout
        )

    def index_history(
        self,
        symbol: str,
        start: Union[date, None] = None,
        end: Union[date, None] = None,
        interval: Interval = Interval.D1,
    ) -> PriceHistory:
        """Index VALUE history (OHLCV in index points) with source failover.

        ``start`` and ``end`` are required and validated up front. Omitting either,
        or passing ``start > end``, raises a stable :class:`~vnfin.exceptions.VnfinError`
        BEFORE any source/failover call — never a raw ``TypeError``/``ValueError``.
        """
        # Issue #9/#97: the index-history selector is a canonical security/index
        # identifier — reject malformed shapes before the failover engine runs and
        # normalize to uppercase so identity checks match the sources' canonical form.
        symbol = canonical_security_symbol(symbol, "symbol")
        # Issue #168 (reopen): route a short index alias to its canonical value-history id
        # (e.g. HNX -> HNXINDEX) so the allow-list check AND the fetch use the supported id.
        symbol = resolve_index_alias(symbol)
        # Issue #168: index value-history serves only recognised market indices. A stock
        # (e.g. FPT) or unknown symbol must fail loud BEFORE any network call instead of
        # being fetched and mislabelled as index points.
        # Issue #174: a deny-only index (recognized but not value-history-servable) gets a
        # terminal diagnostic, NOT "use prices.history()" (which loops); see the helper.
        if not is_value_history_index(symbol):
            raise _unservable_index_error(symbol)
        validate_date_range(start, end, name="index_history")
        return apply_interval(
            interval,
            start,
            end,
            lambda iv: self._client.get_history(symbol, iv, start, end),
        )

    def index_history_stitched(
        self,
        symbol: str,
        start: date,
        end: date,
        *,
        interval: Interval = Interval.D1,
    ) -> PriceHistory:
        """Issue #147: opt-in long-window index history stitched from per-CALENDAR-YEAR
        segments, each fetched through the normal failover chain.

        A long window can fail the strict ``index_history`` because *every* source has
        some single OHLC-invariant day in the range. Splitting into calendar-year
        segments lets each year fail over to whichever source is clean for that year;
        the segments are then stitched into one :class:`PriceHistory`.

        D1 only. The result carries ``source="stitched_index_history"`` and a per-segment
        provenance warning (``"segment <year>: <source> (<n> bars)"``). All segments must
        be homogeneous — same ``value_unit``/``currency`` (points), ``adjustment_policy``
        (RAW), and the canonical ``symbol`` — else :class:`~vnfin.exceptions.InvalidData`.
        A conflicting duplicate date across segments is fatal; an identical seam bar is
        deduped. The default strict :meth:`index_history` is unchanged.
        """
        if interval is not Interval.D1:
            raise InvalidData(
                f"index_history_stitched: only daily (D1) is supported, got {interval}"
            )
        symbol = canonical_security_symbol(symbol, "symbol")
        # Issue #168 (reopen): route a short index alias to its canonical id (HNX -> HNXINDEX).
        symbol = resolve_index_alias(symbol)
        # Issue #168: only recognised market indices have value-history; fail loud on a
        # stock/unknown symbol before any segment fetch.
        # Issue #174: a deny-only index gets the terminal diagnostic, not the looping
        # "use prices.history()" guidance (shared helper keeps both call sites identical).
        if not is_value_history_index(symbol):
            raise _unservable_index_error(symbol)
        lo, hi = validate_date_range(start, end, name="index_history_stitched")

        bars: list = []
        warnings: list[str] = []
        seen: dict = {}  # date -> PriceBar (seam dedup / conflict detection)
        for year in range(lo.year, hi.year + 1):
            seg_lo = max(lo, date(year, 1, 1))
            seg_hi = min(hi, date(year, 12, 31))
            seg = self.index_history(symbol, seg_lo, seg_hi, interval)
            # B1: enforce each segment is EXACTLY the required index shape (D1 + index
            # points + RAW + canonical symbol) — absolute, not merely mutually
            # consistent, so a consistently-WRONG metadata set cannot stitch.
            if seg.interval is not Interval.D1:
                raise InvalidData(
                    f"index_history_stitched: segment {year} interval {seg.interval} is not D1"
                )
            if seg.value_unit != "points" or seg.currency != "points":
                raise InvalidData(
                    f"index_history_stitched: segment {year} unit "
                    f"{seg.value_unit!r}/{seg.currency!r} is not index points"
                )
            if seg.adjustment_policy is not AdjustmentPolicy.RAW:
                raise InvalidData(
                    f"index_history_stitched: segment {year} adjustment_policy "
                    f"{seg.adjustment_policy} is not RAW"
                )
            if seg.symbol != symbol:
                raise InvalidData(
                    f"index_history_stitched: segment {year} symbol {seg.symbol!r} "
                    f"!= requested {symbol!r}"
                )
            warnings.append(f"segment {year}: {seg.source} ({len(seg.bars)} bars)")
            for bar in seg.bars:
                d = bar.time.date()
                if d in seen:
                    if seen[d] != bar:
                        raise InvalidData(
                            f"index_history_stitched: conflicting duplicate date "
                            f"{d.isoformat()} across segments"
                        )
                    continue  # identical seam bar -> dedupe
                seen[d] = bar
                bars.append(bar)
        bars.sort(key=lambda b: b.time)
        return PriceHistory(
            symbol=symbol,
            interval=interval,
            adjustment_policy=AdjustmentPolicy.RAW,
            source="stitched_index_history",
            bars=tuple(bars),
            currency="points",
            value_unit="points",
            # B2: explicit token that this series is stitched across (potentially)
            # multiple sources, followed by the per-segment provenance warnings.
            warnings=("stitched_multi_source",) + tuple(warnings),
        )

    def constituents(self, index: str) -> IndexConstituents:
        """Current index membership (no weights from this source)."""
        index = _validate_index_selector(index, "index")
        result = self._constituents.get_constituents(index)
        # Ensure the returned typed object carries the normalized selector.
        if result.index != index:
            from dataclasses import replace

            result = replace(result, index=index)
        return result


def index_history(
    symbol: str,
    start: Union[date, None] = None,
    end: Union[date, None] = None,
    interval: Interval = Interval.D1,
    *,
    http_get=None,
    timeout: float = 25.0,
    max_attempts: int = 3,
) -> PriceHistory:
    """Convenience: one-shot index value history over the default index chain."""
    client = IndexClient(http_get=http_get, timeout=timeout, max_attempts=max_attempts)
    return client.index_history(symbol, start, end, interval)


def index_history_stitched(
    symbol: str,
    start: date,
    end: date,
    *,
    http_get=None,
    timeout: float = 25.0,
    max_attempts: int = 3,
) -> PriceHistory:
    """Convenience (#147): one-shot long-window index history stitched from per-calendar-year
    segments over the default index chain (D1 only; ``source='stitched_index_history'``)."""
    client = IndexClient(http_get=http_get, timeout=timeout, max_attempts=max_attempts)
    return client.index_history_stitched(symbol, start, end)


def index_constituents(
    index: str,
    *,
    http_get=None,
    timeout: float = 25.0,
) -> IndexConstituents:
    """Convenience: one-shot index membership lookup."""
    return IndexClient(http_get=http_get, timeout=timeout).constituents(index)
