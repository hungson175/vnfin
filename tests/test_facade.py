"""P1.4 facade smoke tests — import + construct each domain entry.

These assert the coherent top-level facade and naming standard: ``vnfin.<domain>`` is
reachable for every domain, each exposes the standard ``client(...)`` / ``source(...)``
factory verbs, and constructing each entry yields the expected primary type WITHOUT any
network call (a fake ``http_get`` is injected). They also guard that the additive facade
did not break any pre-existing import path.

Synthetic only: no real symbols, no real provider data — construction-only, offline.
"""
from __future__ import annotations

import pytest

import vnfin


def _fake_get(url, params=None, headers=None):  # pragma: no cover - never invoked here
    raise AssertionError("facade construction must not perform any network call")


# ---------------------------------------------------------------------------
# Top-level facade surface
# ---------------------------------------------------------------------------

DOMAINS = ["prices", "fundamentals", "funds", "indices", "gold", "crypto", "macro"]


@pytest.mark.parametrize("domain", DOMAINS)
def test_domain_namespace_is_reachable(domain):
    """``import vnfin`` exposes each domain as an attribute and in ``__all__``."""
    ns = getattr(vnfin, domain)
    assert ns.__name__ == f"vnfin.{domain}"
    assert domain in vnfin.__all__


def test_legacy_top_level_surface_preserved():
    """The long-standing top-level price symbols are still exported (additive change)."""
    for name in (
        "AdjustmentPolicy",
        "Interval",
        "PriceBar",
        "PriceHistory",
        "SourceAttempt",
        "FailoverClient",
        "FailoverPriceClient",
        "default_client",
        "exceptions",
    ):
        assert hasattr(vnfin, name), name
        assert name in vnfin.__all__, name


# ---------------------------------------------------------------------------
# Per-domain entry construction (offline)
# ---------------------------------------------------------------------------

def test_prices_entry():
    from vnfin.client import FailoverPriceClient
    from vnfin.sources.ssi import SSIiBoardSource

    c = vnfin.prices.client(http_get=_fake_get)
    assert isinstance(c, FailoverPriceClient)
    # prices keeps the one-shot convenience verb as well
    assert callable(vnfin.prices.history)
    # source() = the PRIMARY single broker source (first of the default chain: SSI)
    assert isinstance(vnfin.prices.source(http_get=_fake_get), SSIiBoardSource)
    # facade client matches the long-standing top-level factory type
    assert isinstance(vnfin.default_client(http_get=_fake_get), FailoverPriceClient)


def test_fundamentals_entry():
    from vnfin.fundamentals import FailoverFundamentalClient, VNDirectFundamentalSource

    # client() = multi-source failover (consistent with prices); source() = primary
    assert isinstance(vnfin.fundamentals.client(http_get=_fake_get), FailoverFundamentalClient)
    assert isinstance(vnfin.fundamentals.source(http_get=_fake_get), VNDirectFundamentalSource)
    assert callable(vnfin.fundamentals.get_financials)


def test_funds_entry():
    from vnfin.funds import FmarketFundSource

    assert isinstance(vnfin.funds.client(http_get=_fake_get), FmarketFundSource)
    assert isinstance(vnfin.funds.source(http_get=_fake_get), FmarketFundSource)


def test_indices_entry():
    from vnfin.indices import IndexClient
    from vnfin.indices.sources import VPSIndexSource

    assert isinstance(vnfin.indices.client(http_get=_fake_get), IndexClient)
    # source() = the PRIMARY single index source (first of the default chain: VPS)
    assert isinstance(vnfin.indices.source(http_get=_fake_get), VPSIndexSource)
    assert callable(vnfin.indices.index_history)


def test_crypto_entry():
    from vnfin.crypto import BinanceCryptoSource, FailoverCryptoClient

    # client() = Binance->Coinbase failover (USD); source() = primary Binance
    assert isinstance(vnfin.crypto.client(http_get=_fake_get), FailoverCryptoClient)
    assert isinstance(vnfin.crypto.source(http_get=_fake_get), BinanceCryptoSource)


def test_macro_entry():
    from vnfin.macro import MacroClient, WorldBankMacroSource

    # client() = World Bank->IMF->DBnomics no-key failover; source() = primary World Bank
    assert isinstance(vnfin.macro.client(http_get=_fake_get), MacroClient)
    assert isinstance(vnfin.macro.source(http_get=_fake_get), WorldBankMacroSource)


def test_gold_entry_vn_world_source():
    from vnfin.gold import (
        BTMCGoldSource,
        CurrencyApiGoldSource,
        GoldApiSource,
        PNJGoldSource,
    )

    # VN domestic
    assert isinstance(vnfin.gold.vn(http_get=_fake_get), BTMCGoldSource)
    assert isinstance(vnfin.gold.vn("pnj", http_get=_fake_get), PNJGoldSource)
    # world XAU
    assert isinstance(vnfin.gold.world(http_get=_fake_get), CurrencyApiGoldSource)
    assert isinstance(vnfin.gold.world("gold_api", http_get=_fake_get), GoldApiSource)
    # generic provider selector routes to both families
    assert isinstance(vnfin.gold.source("btmc", http_get=_fake_get), BTMCGoldSource)
    assert isinstance(vnfin.gold.source("currency_api", http_get=_fake_get), CurrencyApiGoldSource)


@pytest.mark.parametrize(
    "fn,bad",
    [
        ("vn", "nope"),
        ("world", "nope"),
        ("source", "nope"),
    ],
)
def test_gold_unknown_provider_raises(fn, bad):
    with pytest.raises(ValueError):
        getattr(vnfin.gold, fn)(bad)


# ---------------------------------------------------------------------------
# Naming standard: every domain exposes consistent factory verbs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "domain,verbs",
    [
        ("prices", ("client", "source", "history")),
        ("fundamentals", ("client", "source")),
        ("funds", ("client", "source")),
        ("indices", ("client", "source")),
        ("crypto", ("client", "source")),
        ("macro", ("client", "source")),
        ("gold", ("vn", "world", "source")),
    ],
)
def test_domain_exposes_standard_factory_verbs(domain, verbs):
    ns = getattr(vnfin, domain)
    for verb in verbs:
        assert callable(getattr(ns, verb)), f"vnfin.{domain}.{verb}"
        assert verb in ns.__all__, f"{verb} not in vnfin.{domain}.__all__"


# ---------------------------------------------------------------------------
# Facade surface contract: standard domains have client()+source();
# gold is the deliberate exception (vn/world/source, no client()).
# ---------------------------------------------------------------------------

STANDARD_DOMAINS = ["prices", "fundamentals", "funds", "indices", "crypto", "macro"]


@pytest.mark.parametrize("domain", STANDARD_DOMAINS)
def test_standard_domains_expose_client_and_source(domain):
    """Every standard domain exposes BOTH the failover ``client()`` and primary ``source()``."""
    ns = getattr(vnfin, domain)
    assert callable(getattr(ns, "client", None)), f"vnfin.{domain}.client missing"
    assert callable(getattr(ns, "source", None)), f"vnfin.{domain}.source missing"
    assert "client" in ns.__all__ and "source" in ns.__all__


def test_gold_is_the_facade_exception():
    """GOLD intentionally does NOT expose a domain-standard ``client()``.

    VN VND/lượng and world USD/oz are different unit families, so there is no single
    cross-unit client. Gold uses ``vn()`` / ``world()`` / ``source(provider)`` plus the
    world-only ``default_world_gold_client()``.
    """
    assert not hasattr(vnfin.gold, "client"), "gold must NOT expose a domain-standard client()"
    assert "client" not in vnfin.gold.__all__
    for verb in ("vn", "world", "source", "default_world_gold_client"):
        assert callable(getattr(vnfin.gold, verb)), f"vnfin.gold.{verb} missing"
        assert verb in vnfin.gold.__all__, f"{verb} not in vnfin.gold.__all__"
