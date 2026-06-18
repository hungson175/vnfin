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

    c = vnfin.prices.client(http_get=_fake_get)
    assert isinstance(c, FailoverPriceClient)
    # prices keeps the one-shot convenience verb as well
    assert callable(vnfin.prices.history)
    # facade client matches the long-standing top-level factory type
    assert isinstance(vnfin.default_client(http_get=_fake_get), FailoverPriceClient)


def test_fundamentals_entry():
    from vnfin.fundamentals import VNDirectFundamentalSource

    assert isinstance(vnfin.fundamentals.client(http_get=_fake_get), VNDirectFundamentalSource)
    assert isinstance(vnfin.fundamentals.source(http_get=_fake_get), VNDirectFundamentalSource)
    assert callable(vnfin.fundamentals.get_financials)


def test_funds_entry():
    from vnfin.funds import FmarketFundSource

    assert isinstance(vnfin.funds.client(http_get=_fake_get), FmarketFundSource)
    assert isinstance(vnfin.funds.source(http_get=_fake_get), FmarketFundSource)


def test_indices_entry():
    from vnfin.indices import IndexClient

    assert isinstance(vnfin.indices.client(http_get=_fake_get), IndexClient)
    assert callable(vnfin.indices.index_history)


def test_crypto_entry():
    from vnfin.crypto import BinanceCryptoSource

    assert isinstance(vnfin.crypto.client(http_get=_fake_get), BinanceCryptoSource)
    assert isinstance(vnfin.crypto.source(http_get=_fake_get), BinanceCryptoSource)


def test_macro_entry():
    from vnfin.macro import WorldBankMacroSource

    assert isinstance(vnfin.macro.client(http_get=_fake_get), WorldBankMacroSource)
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
        ("prices", ("client", "history")),
        ("fundamentals", ("client", "source")),
        ("funds", ("client", "source")),
        ("indices", ("client",)),
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
