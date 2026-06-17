import vnfin
from vnfin.models import AdjustmentPolicy, Interval
from vnfin.sources.registry import (
    DEFAULT_CHAIN_CLASSES,
    all_sources,
    default_sources,
)


def test_default_chain_is_provider_adjusted_only():
    for cls in DEFAULT_CHAIN_CLASSES:
        assert cls.ADJUSTMENT_POLICY is AdjustmentPolicy.PROVIDER_ADJUSTED


def test_default_order():
    assert [s.name for s in default_sources()] == ["ssi", "vndirect", "vps", "pinetree"]


def test_kis_excluded_from_default_but_registered():
    assert "kis" not in [s.name for s in default_sources()]
    assert "kis" in [s.name for s in all_sources()]


def test_all_sources_support_daily():
    for s in all_sources():
        assert s.supports(Interval.D1)


def test_default_client_factory():
    client = vnfin.default_client()
    assert client.max_attempts == 3
    assert [s.name for s in client.sources] == ["ssi", "vndirect", "vps", "pinetree"]
