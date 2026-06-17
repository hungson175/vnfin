"""Source registry and default failover-chain assembly.

The default chain contains only ``PROVIDER_ADJUSTED`` broker-native sources, ordered
deepest/most-reliable first. KIS is registered and available but excluded from the
default chain because its series adjustment is ``MIXED`` (reviewer note B3) and must
not be silently blended with adjusted series.
"""
from __future__ import annotations

from .kis import KISVietnamSource
from .pinetree import PinetreeSource
from .ssi import SSIiBoardSource
from .vndirect import VNDirectSource
from .vps import VPSSource

# All broker-native adapters.
ALL_SOURCE_CLASSES = (
    SSIiBoardSource,
    VNDirectSource,
    VPSSource,
    PinetreeSource,
    KISVietnamSource,
)

# Default failover order: provider-adjusted only, deepest history first.
DEFAULT_CHAIN_CLASSES = (
    SSIiBoardSource,   # daily back to ~2006
    VNDirectSource,    # daily back to ~2013
    VPSSource,         # daily back to ~2010
    PinetreeSource,    # daily back to ~2010
)


def all_sources(http_get=None, timeout: float = 25.0):
    """Instantiate every registered adapter (KIS included)."""
    return [c(http_get=http_get, timeout=timeout) for c in ALL_SOURCE_CLASSES]


def default_sources(http_get=None, timeout: float = 25.0):
    """Instantiate the default provider-adjusted failover chain (KIS excluded)."""
    return [c(http_get=http_get, timeout=timeout) for c in DEFAULT_CHAIN_CLASSES]
