"""Shared synthetic fixtures. No real broker data — synthetic UDF payloads only."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from vnfin.models import AdjustmentPolicy, Interval, PriceBar, PriceHistory

# (date, open, high, low, close, volume) — prices in THOUSANDS of VND (UDF convention)
_DAILY = [
    ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1_000_000),
    ("2024-01-03", 72.3, 73.0, 72.1, 72.8, 1_200_000),
    ("2024-01-04", 72.8, 73.2, 72.5, 73.0, 900_000),
]


def _ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _bare(rows=None, status="ok") -> str:
    rows = _DAILY if rows is None else rows
    return json.dumps(
        {
            "s": status,
            "t": [_ts(r[0]) for r in rows],
            "o": [r[1] for r in rows],
            "h": [r[2] for r in rows],
            "l": [r[3] for r in rows],
            "c": [r[4] for r in rows],
            "v": [r[5] for r in rows],
        }
    )


def _env(rows=None, status="ok") -> str:
    inner = json.loads(_bare(rows, status))
    inner["nextTime"] = None
    return json.dumps({"code": "SUCCESS", "message": "ok", "status": "ok", "data": inner})


def _static_get(text):
    def _g(url, params, headers):
        return text

    return _g


def _raising_get(exc):
    def _g(url, params, headers):
        raise exc

    return _g


def _make_history(source="fake", n=2):
    bars = tuple(
        PriceBar(
            time=datetime(2024, 1, 2 + i, tzinfo=timezone.utc),
            open=72.0,
            high=73.0,
            low=71.0,
            close=72.5,
            volume=1000 + i,
        )
        for i in range(n)
    )
    return PriceHistory(
        symbol="FPT",
        interval=Interval.D1,
        adjustment_policy=AdjustmentPolicy.PROVIDER_ADJUSTED,
        source=source,
        bars=bars,
        exchange="HOSE",
        provider_symbol="FPT",
    )


@pytest.fixture
def synth():
    return SimpleNamespace(
        ts=_ts,
        DAILY=_DAILY,
        bare=_bare,
        env=_env,
        static_get=_static_get,
        raising_get=_raising_get,
        make_history=_make_history,
    )
