"""Live equity-universe probe — pins the real SSI iBoard stock-group payload shape.

Confirms the live endpoint still returns the SUCCESS envelope + a plausible per-board
equity count, and that the board-token aliasing (HOSE→VNINDEX etc.) still resolves.
No fixtures committed — this is a real-network smoke test only.

Live-only: outside the default ``tests/`` collection; requires ``VNFIN_LIVE=1``
(enforced by ``live_tests/conftest.py``). Run:
``VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/test_equities_universe_live.py``.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_each_board_returns_plausible_equity_count():
    from vnfin.equities import universe

    # per the source provenance: HOSE ~403, HNX ~300, UPCOM ~828 — assert loose lower bounds.
    for board, floor in (("HOSE", 100), ("HNX", 50), ("UPCOM", 100)):
        res = universe(board)
        assert res.board == board
        assert res.source == "ssi_iboard_universe"
        assert len(res) >= floor, f"{board} returned only {len(res)} equities"
        # honest-gap tokens are always present
        prefixes = [w.split(":", 1)[0] for w in res.warnings]
        assert "partial_universe_coverage" in prefixes
        # every security carries a canonical symbol + an exchange
        for sec in res.securities[:5]:
            assert sec.symbol and sec.symbol.upper() == sec.symbol
            assert sec.exchange


def test_merge_all_boards_no_raise_and_attributed_warnings():
    from vnfin.equities import universe

    res = universe()  # merge HOSE + HNX + UPCOM
    assert res.board == "ALL"
    assert len(res) >= 300
    # each board's coverage warning is attributed in the merged result
    for board in ("HOSE", "HNX", "UPCOM"):
        assert any(w.startswith("partial_universe_coverage") and board in w for w in res.warnings)
