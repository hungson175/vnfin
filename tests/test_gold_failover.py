"""World-gold failover + stooq backup tests — synthetic fixtures only.

No real provider rows are committed. The stooq CSV fixtures use the *documented*
column shape (``Date,Open,High,Low,Close,Volume``, USD/oz daily) with obviously-fake
fabricated numbers; the currency-api fixtures reuse the same synthetic shape as
``tests/test_gold.py``. The chain under test is the world-gold failover:

    default_world_gold_sources() == [CurrencyApiGoldSource, StooqGoldSource]

both declaring unit ``USD/oz`` so the unit-homogeneity guard accepts the chain.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import (
    AllSourcesFailed,
    EmptyData,
    InvalidData,
    SourceUnavailable,
    UnitMismatchError,
    VnfinError,
)
from vnfin.gold import (
    CurrencyApiGoldSource,
    GoldBar,
    GoldHistory,
    GoldSource,
    StooqGoldSource,
)
from vnfin.gold import default_world_gold_sources, default_world_gold_client
from vnfin.gold.failover import FailoverGoldClient


# --------------------------------------------------------------------------- #
# Synthetic fixtures                                                          #
# --------------------------------------------------------------------------- #

# stooq daily CSV: documented shape Date,Open,High,Low,Close,Volume (USD/oz).
# SYNTHETIC obviously-fake round numbers; Close is the EOD price we keep.
_STOOQ_CSV = (
    "Date,Open,High,Low,Close,Volume\n"
    "2026-06-15,4000.0,4050.0,3990.0,4010.0,0\n"
    "2026-06-16,4010.0,4030.0,4000.0,4020.0,0\n"
    "2026-06-17,4020.0,4090.0,4015.0,4080.0,0\n"
)


def _currency_usd_json(d="2026-06-17", usd_xau=0.0002313114):
    return json.dumps({"date": d, "usd": {"eur": 0.86, "vnd": 26000.0, "xau": usd_xau}})


def _static_get(text):
    def _g(url, params=None, headers=None):
        return text

    return _g


def _raising_get(exc):
    def _g(url, params=None, headers=None):
        raise exc

    return _g


# --------------------------------------------------------------------------- #
# StooqGoldSource — parsing / units / failover-safe errors                     #
# --------------------------------------------------------------------------- #


def test_stooq_implements_port():
    assert issubclass(StooqGoldSource, GoldSource)


def test_stooq_capability_flags():
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    assert s.provides_history is True
    assert s.unit == "USD/oz"


def test_stooq_history_parses_csv_close_as_usd_oz():
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    hist = s.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert isinstance(hist, GoldHistory)
    assert hist.product == "XAU"
    assert hist.currency == "USD"
    assert hist.unit == "USD/oz"
    assert hist.value_unit == "USD/oz"
    assert hist.source == "stooq"
    assert len(hist) == 3
    dates = [b.date for b in hist.bars]
    assert dates == [date(2026, 6, 15), date(2026, 6, 16), date(2026, 6, 17)]
    # Close column is the EOD price we keep
    assert hist.bars[-1].price == pytest.approx(4080.0)
    assert isinstance(hist.bars[0], GoldBar)


def test_stooq_history_filters_to_requested_range():
    # full CSV spans 06-15..06-17; ask for only 06-16..06-17
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    hist = s.get_history(date(2026, 6, 16), date(2026, 6, 17))
    assert [b.date for b in hist.bars] == [date(2026, 6, 16), date(2026, 6, 17)]


def test_stooq_history_sorted_ascending():
    csv = (
        "Date,Open,High,Low,Close,Volume\n"
        "2026-06-17,4020.0,4090.0,4015.0,4080.0,0\n"
        "2026-06-15,4000.0,4050.0,3990.0,4010.0,0\n"
        "2026-06-16,4010.0,4030.0,4000.0,4020.0,0\n"
    )
    s = StooqGoldSource(http_get=_static_get(csv))
    hist = s.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert [b.date for b in hist.bars] == [
        date(2026, 6, 15),
        date(2026, 6, 16),
        date(2026, 6, 17),
    ]


def test_stooq_accepts_datetime_args():
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    hist = s.get_history(
        datetime(2026, 6, 15, 9, 0), datetime(2026, 6, 17, 17, 0)
    )
    assert len(hist) == 3


def test_stooq_empty_range_raises_empty():
    # CSV has data but none inside the requested window -> EmptyData
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    with pytest.raises(EmptyData):
        s.get_history(date(2025, 1, 1), date(2025, 1, 31))


def test_stooq_header_only_raises_empty():
    s = StooqGoldSource(http_get=_static_get("Date,Open,High,Low,Close,Volume\n"))
    with pytest.raises(EmptyData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_no_data_sentinel_raises_empty():
    # stooq returns the literal "No data" for an unknown symbol
    s = StooqGoldSource(http_get=_static_get("No data\n"))
    with pytest.raises(EmptyData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_malformed_close_raises_invalid():
    bad = (
        "Date,Open,High,Low,Close,Volume\n"
        "2026-06-17,4020.0,4090.0,4015.0,not-a-number,0\n"
    )
    s = StooqGoldSource(http_get=_static_get(bad))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_negative_close_raises_invalid():
    bad = (
        "Date,Open,High,Low,Close,Volume\n"
        "2026-06-17,4020.0,4090.0,4015.0,-5.0,0\n"
    )
    s = StooqGoldSource(http_get=_static_get(bad))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_bad_date_raises_invalid():
    bad = (
        "Date,Open,High,Low,Close,Volume\n"
        "garbage-date,4020.0,4090.0,4015.0,4080.0,0\n"
    )
    s = StooqGoldSource(http_get=_static_get(bad))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_missing_close_column_raises_invalid():
    bad = "Date,Open,High,Low,Volume\n2026-06-17,4020.0,4090.0,4015.0,0\n"
    s = StooqGoldSource(http_get=_static_get(bad))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_js_challenge_html_raises_unavailable():
    # stooq serves a JS proof-of-work challenge (HTML) instead of CSV from some IPs.
    # That must surface as SourceUnavailable so failover moves on, not InvalidData.
    html = (
        "<!DOCTYPE html><html><head></head><body>"
        "<noscript>This site requires JavaScript to verify your browser.</noscript>"
        "</body></html>"
    )
    s = StooqGoldSource(http_get=_static_get(html))
    with pytest.raises(SourceUnavailable):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_transport_error_wrapped():
    s = StooqGoldSource(http_get=_raising_get(ConnectionError("net")))
    with pytest.raises(SourceUnavailable):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_stooq_spot_quote_from_last_bar():
    # backup also satisfies the spot path (last EOD close), USD/oz
    s = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    q = s.get_quote()
    assert q.product == "XAU"
    assert q.currency == "USD"
    assert q.unit == "USD/oz"
    assert q.buy == pytest.approx(4080.0)
    assert q.sell == pytest.approx(4080.0)
    assert q.source == "stooq"


# --------------------------------------------------------------------------- #
# World-gold failover wiring                                                  #
# --------------------------------------------------------------------------- #


def test_default_world_gold_sources_order_and_types():
    sources = default_world_gold_sources()
    assert [type(s) for s in sources] == [CurrencyApiGoldSource, StooqGoldSource]


def test_world_gold_chain_is_usd_oz_homogeneous():
    client = FailoverGoldClient(default_world_gold_sources())
    # both world sources declare USD/oz -> guard keeps both, chain unit is USD/oz
    assert client.unit == "USD/oz"
    assert len(client.sources) == 2


def test_world_gold_mixed_unit_chain_rejected():
    # a fabricated non-USD/oz source must be rejected by the unit guard
    class _BogusUnitSource(StooqGoldSource):
        unit = "VND/luong"

    with pytest.raises(UnitMismatchError):
        FailoverGoldClient(
            [
                CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json())),
                _BogusUnitSource(http_get=_static_get(_STOOQ_CSV)),
            ]
        )


def test_failover_uses_primary_when_healthy():
    primary = CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json(d="2026-06-17")))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(date(2026, 6, 17), date(2026, 6, 17))
    assert hist.source == "currency-api"
    assert hist.unit == "USD/oz"
    # attempts recorded; primary succeeded first
    assert hist.attempts[0].name == "currency-api"
    assert hist.attempts[0].ok is True


def test_failover_falls_through_to_stooq_on_primary_transport_error():
    primary = CurrencyApiGoldSource(http_get=_raising_get(ConnectionError("down")))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert hist.source == "stooq"
    assert len(hist) == 3
    # both attempts recorded: primary failed, backup ok
    names = [a.name for a in hist.attempts]
    assert names == ["currency-api", "stooq"]
    assert hist.attempts[0].ok is False
    assert hist.attempts[-1].ok is True


def test_failover_falls_through_on_primary_empty():
    # primary returns no usable rows (all dates 404) -> EmptyData -> fall through
    def _all_404(url, params=None, headers=None):
        raise FileNotFoundError("404")

    primary = CurrencyApiGoldSource(http_get=_all_404)
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert hist.source == "stooq"


def test_failover_all_sources_failed_raises():
    primary = CurrencyApiGoldSource(http_get=_raising_get(ConnectionError("down")))
    backup = StooqGoldSource(http_get=_raising_get(ConnectionError("down")))
    client = FailoverGoldClient([primary, backup])
    with pytest.raises(AllSourcesFailed):
        client.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_failover_never_leaks_raw_exception():
    # a raw, non-SourceError exception inside a source must not escape as itself;
    # transport wrapping turns it into SourceUnavailable, so the chain handles it.
    primary = CurrencyApiGoldSource(http_get=_raising_get(RuntimeError("weird")))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = FailoverGoldClient([primary, backup])
    hist = client.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert hist.source == "stooq"


def test_default_world_gold_client_factory():
    client = default_world_gold_client()
    assert isinstance(client, FailoverGoldClient)
    assert client.unit == "USD/oz"
    assert len(client.sources) == 2


def test_default_world_gold_client_accepts_injected_sources():
    primary = CurrencyApiGoldSource(http_get=_raising_get(ConnectionError("down")))
    backup = StooqGoldSource(http_get=_static_get(_STOOQ_CSV))
    client = default_world_gold_client(sources=[primary, backup])
    hist = client.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert hist.source == "stooq"
