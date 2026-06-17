from datetime import timedelta

import pytest

from vnfin.models import AdjustmentPolicy, Interval


def test_interval_is_intraday():
    assert Interval.H1.is_intraday is True
    assert Interval.M1.is_intraday is True
    assert Interval.D1.is_intraday is False
    assert Interval.W1.is_intraday is False


def test_adjustment_members():
    assert AdjustmentPolicy.PROVIDER_ADJUSTED.value == "provider_adjusted"
    assert {a.value for a in AdjustmentPolicy} == {"provider_adjusted", "raw", "mixed", "unknown"}


def test_pricehistory_len_and_iter(synth):
    h = synth.make_history(n=3)
    assert len(h) == 3
    assert len(list(h)) == 3
    assert h.currency == "VND"
    assert h.exchange == "HOSE"


def test_to_dataframe(synth):
    pd = pytest.importorskip("pandas")
    df = synth.make_history(source="ssi", n=3).to_dataframe()
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 3
    assert df.index.name == "time"
    assert df.attrs["source"] == "ssi"
    assert df.attrs["currency"] == "VND"
    assert df.attrs["adjustment_policy"] == "provider_adjusted"


def test_to_dataframe_empty(synth):
    pytest.importorskip("pandas")
    df = synth.make_history(n=0).to_dataframe()
    assert len(df) == 0
    assert df.attrs["source"] == "fake"
