"""Tests for the shared time-series base/mixin (P1.2) and the explicit unit model (P0.3).

All data here is SYNTHETIC: obviously-fake symbols (FAKE/XXXTEST/ZZZ) and fabricated
numbers. No real provider rows or live values are committed.

Two things are exercised:

(a) ``vnfin.timeseries.TimeSeriesResult`` — the shared __len__/__iter__/to_dataframe
    mixin every domain result container now uses. We assert each migrated container
    is a subclass and produces the same DataFrame shape via the mixin path.

(b) The explicit ``value_unit`` field on every time-series result, and that each
    domain's SOURCE emits unit/currency directly (not via post-hoc patching):
      - equity prices: value_unit/currency "VND"
      - indices:       value_unit "points" (currency kept "points", not money)
      - crypto:        value_unit == currency (the quote asset)
      - macro:         value_unit mirrors the per-indicator `unit`
      - gold:          value_unit mirrors the per-source `unit`
      - funds NAV:     value_unit "VND/unit"
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from vnfin.timeseries import TimeSeriesResult

UTC = timezone.utc
DAY_MS = 86_400_000


# --------------------------------------------------------------------------- #
# (a) Shared mixin contract                                                    #
# --------------------------------------------------------------------------- #


def test_every_timeseries_result_uses_the_shared_mixin():
    from vnfin.models import PriceHistory
    from vnfin.crypto.models import CryptoHistory
    from vnfin.funds.models import NavHistory
    from vnfin.gold.models import GoldHistory
    from vnfin.macro.models import IndicatorSeries

    for cls in (PriceHistory, CryptoHistory, NavHistory, GoldHistory, IndicatorSeries):
        assert issubclass(cls, TimeSeriesResult), cls.__name__
        # The mixin contract: each declares the row-tuple attr, index column and columns.
        assert isinstance(cls._items_attr, str) and cls._items_attr
        assert isinstance(cls._index_column, str) and cls._index_column
        assert cls._index_column in cls._df_columns


def test_mixin_len_iter_and_dataframe_on_a_minimal_subclass():
    """A tiny synthetic subclass proves the mixin's behavior in isolation."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _Pt:
        when: date
        v: float

    @dataclass(frozen=True)
    class _Series(TimeSeriesResult):
        rows: tuple
        source: str = "synthetic"
        value_unit: str = "widgets"

        _items_attr = "rows"
        _index_column = "when"
        _df_columns = ("when", "v")

        def _row_record(self, p):
            return {"when": p.when, "v": p.v}

        def _df_attrs(self):
            return {"source": self.source, "value_unit": self.value_unit}

    pts = (_Pt(date(2099, 1, 1), 1.0), _Pt(date(2099, 1, 2), 2.0), _Pt(date(2099, 1, 3), 3.0))
    s = _Series(rows=pts)
    assert len(s) == 3
    assert [p.v for p in s] == [1.0, 2.0, 3.0]

    import pandas as pd
    df = s.to_dataframe()
    assert list(df.columns) == ["v"]
    assert df.index.name == "when"
    assert df.attrs["source"] == "synthetic"
    assert df.attrs["value_unit"] == "widgets"
    assert isinstance(df, pd.DataFrame)


def test_mixin_dataframe_empty_series_keeps_attrs():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _Series(TimeSeriesResult):
        rows: tuple = ()
        _items_attr = "rows"
        _index_column = "when"
        _df_columns = ("when", "v")

        def _row_record(self, p):  # pragma: no cover - no rows
            return {"when": p.when, "v": p.v}

        def _df_attrs(self):
            return {"source": "empty"}

    import pandas  # noqa: F401
    s = _Series()
    assert len(s) == 0
    df = s.to_dataframe()
    assert len(df) == 0
    assert df.attrs["source"] == "empty"


# --------------------------------------------------------------------------- #
# (b) Explicit unit model — equity                                            #
# --------------------------------------------------------------------------- #


def test_equity_price_history_value_unit_and_currency_are_vnd(synth):
    h = synth.make_history(n=2)
    assert h.value_unit == "VND"
    assert h.currency == "VND"


def test_equity_udf_source_emits_vnd_unit_directly(synth):
    """The UDF source sets value_unit/currency='VND' on the result itself (P0.3)."""
    from vnfin.sources.vps import VPSSource
    from vnfin.models import Interval

    s = VPSSource(http_get=synth.static_get(synth.bare()))
    h = s.get_history("FAKESYM", Interval.D1, date(2024, 1, 1), date(2024, 1, 31))
    assert h.value_unit == "VND"
    assert h.currency == "VND"


def test_equity_to_dataframe_carries_value_unit(synth):
    import pandas  # noqa: F401
    df = synth.make_history(n=2).to_dataframe()
    assert df.attrs["value_unit"] == "VND"
    assert df.attrs["currency"] == "VND"


# --------------------------------------------------------------------------- #
# (b) Explicit unit model — indices                                          #
# --------------------------------------------------------------------------- #

_INDEX_WIDE = (date(2024, 6, 1), date(2024, 6, 30))


def _index_bare_udf(status="ok"):
    # Synthetic index OHLCV around 1000 POINTS (not VND); fabricated values.
    def _ts(d):
        return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=UTC).timestamp())

    rows = [
        ("2024-06-10", 1000.0, 1010.0, 995.0, 1005.0, 100_000_000),
        ("2024-06-11", 1005.0, 1020.0, 1002.0, 1018.0, 120_000_000),
    ]
    return json.dumps(
        {
            "symbol": "ZZZINDEX",
            "s": status,
            "t": [_ts(r[0]) for r in rows],
            "o": [r[1] for r in rows],
            "h": [r[2] for r in rows],
            "l": [r[3] for r in rows],
            "c": [r[4] for r in rows],
            "v": [r[5] for r in rows],
        }
    )


def test_index_source_emits_points_value_unit_directly():
    """Index value history has value_unit='points' (an index level is not money)."""
    from vnfin.indices.sources import VPSIndexSource
    from vnfin.models import Interval

    s = VPSIndexSource(http_get=lambda u, p, h: _index_bare_udf())
    hist = s.get_history("ZZZINDEX", Interval.D1, *_INDEX_WIDE)
    assert hist.value_unit == "points"
    # currency stays "points" for backward compatibility (it is NOT a money amount).
    assert hist.currency == "points"
    # Sanity: values were not x1000-scaled into VND.
    assert hist.bars[0].close == pytest.approx(1005.0)


def test_index_to_dataframe_carries_points_value_unit():
    from vnfin.indices.sources import VNDirectIndexSource
    from vnfin.models import Interval

    import pandas  # noqa: F401
    s = VNDirectIndexSource(http_get=lambda u, p, h: _index_bare_udf())
    df = s.get_history("ZZZINDEX", Interval.D1, *_INDEX_WIDE).to_dataframe()
    assert df.attrs["value_unit"] == "points"


# --------------------------------------------------------------------------- #
# (b) Explicit unit model — crypto                                           #
# --------------------------------------------------------------------------- #


def _crypto_payload():
    def _ms(d):
        return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp() * 1000)

    rows = [
        (_ms(date(2026, 6, 15)), "100.00", "110.00", "90.00", "105.00", "1.111"),
        (_ms(date(2026, 6, 16)), "105.00", "120.00", "100.00", "115.00", "2.222"),
    ]
    return json.dumps(
        [[r[0], r[1], r[2], r[3], r[4], r[5], r[0] + DAY_MS - 1, "0", 1, "0", "0", "0"] for r in rows]
    )


def test_crypto_value_unit_equals_quote_currency_usd():
    from vnfin.crypto import BinanceCryptoSource
    from vnfin.models import Interval

    s = BinanceCryptoSource(http_get=lambda u, p, h: _crypto_payload())
    h = s.get_klines("ZZZUSDT", Interval.D1, date(2026, 6, 1), date(2026, 6, 30))
    assert h.currency == "USD"
    assert h.value_unit == "USD"


def test_crypto_value_unit_follows_non_usd_quote_asset():
    from vnfin.crypto import BinanceCryptoSource
    from vnfin.models import Interval

    s = BinanceCryptoSource(http_get=lambda u, p, h: _crypto_payload())
    # ETHBTC -> quote asset BTC; value_unit must reflect BTC, never hard-coded USD.
    h = s.get_klines("ETHBTC", Interval.D1, date(2026, 6, 1), date(2026, 6, 30))
    assert h.currency == "BTC"
    assert h.value_unit == "BTC"
    assert h.to_dataframe().attrs["value_unit"] == "BTC"


# --------------------------------------------------------------------------- #
# (b) Explicit unit model — macro                                            #
# --------------------------------------------------------------------------- #


def _wb_payload(unit="", value="2.5"):
    meta = {"page": 1, "pages": 1, "per_page": 50, "total": 1}
    obs = [
        {
            "indicator": {"id": "XX.FAKE.IND", "value": "Fake indicator"},
            "country": {"id": "ZZ", "value": "Faketopia"},
            "countryiso3code": "ZZZ",
            "date": "2020",
            "value": value,
            "unit": unit,
        }
    ]
    return json.dumps([meta, obs])


def test_macro_value_unit_mirrors_per_indicator_unit():
    from vnfin.macro import WorldBankMacroSource

    s = WorldBankMacroSource(http_get=lambda u, p, h: _wb_payload(unit="annual %"))
    res = s.get_indicator("ZZZ", "XX.FAKE.IND")
    assert res.unit == "annual %"
    assert res.value_unit == "annual %"  # mirrors the per-indicator unit
    assert res.to_dataframe().attrs["value_unit"] == "annual %"


def test_macro_value_unit_defaults_to_unit_when_blank():
    from vnfin.macro import WorldBankMacroSource

    s = WorldBankMacroSource(http_get=lambda u, p, h: _wb_payload(unit=""))
    res = s.get_indicator("ZZZ", "XX.FAKE.IND")
    # Blank provider unit -> value_unit mirrors it (empty string), not None.
    assert res.value_unit == ""


# --------------------------------------------------------------------------- #
# (b) Explicit unit model — gold                                             #
# --------------------------------------------------------------------------- #


def test_gold_history_value_unit_mirrors_unit():
    from vnfin.gold.models import GoldBar, GoldHistory

    hist = GoldHistory(
        product="XAU",
        unit="USD/oz",
        currency="USD",
        source="synthetic",
        bars=(GoldBar(date=date(2026, 6, 1), price=2000.0),),
    )
    assert hist.value_unit == "USD/oz"  # __post_init__ mirrors `unit`
    assert hist.to_dataframe().attrs["value_unit"] == "USD/oz"


def test_gold_history_explicit_value_unit_is_respected():
    from vnfin.gold.models import GoldBar, GoldHistory

    hist = GoldHistory(
        product="XAU",
        unit="USD/oz",
        value_unit="USD per troy ounce",
        currency="USD",
        source="synthetic",
        bars=(GoldBar(date=date(2026, 6, 1), price=2000.0),),
    )
    assert hist.value_unit == "USD per troy ounce"


# --------------------------------------------------------------------------- #
# (b) Explicit unit model — funds NAV                                        #
# --------------------------------------------------------------------------- #


def test_nav_history_value_unit_is_vnd_per_unit():
    from vnfin.funds.models import NavHistory, NavPoint

    hist = NavHistory(
        product_id=999999,
        points=(NavPoint(date=date(2026, 6, 1), nav=12345.0),),
        source="synthetic",
    )
    assert hist.currency == "VND"
    assert hist.value_unit == "VND/unit"
    assert hist.to_dataframe().attrs["value_unit"] == "VND/unit"
