"""RED contract for the #221 fail-closed Fmarket transition.

All payloads and URLs in this file are synthetic contract fixtures.  The tests must
fail against the current enabled adapter and must never contact Fmarket.
"""
from __future__ import annotations

import inspect
import json

import pytest

from vnfin.exceptions import InvalidData, SourceUnavailable
from vnfin.funds import FmarketFundSource, client, source
from vnfin.transport import HttpDataSource


DISABLED = "SOURCE_DISABLED_PENDING_PERMISSION"


def _forbidden_http_get(calls):
    def _get(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("disabled Fmarket call must not reach transport")

    return _get


def _constructors(http_get):
    return (
        ("direct", FmarketFundSource(http_get=http_get)),
        ("source", source(http_get=http_get)),
        ("client", client(http_get=http_get)),
    )


@pytest.mark.parametrize(
    "operation",
    (
        ("list_funds", lambda src: src.list_funds()),
        ("nav_history", lambda src: src.nav_history(20)),
        ("holdings", lambda src: src.holdings(20)),
        ("asset_allocation", lambda src: src.asset_allocation(20)),
    ),
)
def test_disabled_valid_operation_fails_before_transport(operation):
    name, invoke = operation
    calls = []
    for entrypoint, src in _constructors(_forbidden_http_get(calls)):
        with pytest.raises(SourceUnavailable) as exc_info:
            invoke(src)
        assert str(exc_info.value) == DISABLED, (entrypoint, name)
    assert calls == []


def test_disabled_construction_is_lazy_and_client_is_source_alias():
    calls = []
    for entrypoint, src in _constructors(_forbidden_http_get(calls)):
        assert isinstance(src, FmarketFundSource), entrypoint
    assert client is source
    assert calls == []


@pytest.mark.parametrize(
    "invoke",
    (
        lambda src: src.list_funds(page_size=0),
        lambda src: src.nav_history(0),
        lambda src: src.holdings(0),
        lambda src: src.asset_allocation(0),
    ),
)
def test_invalid_arguments_keep_validation_precedence_and_zero_transport(invoke):
    calls = []
    src = FmarketFundSource(http_get=_forbidden_http_get(calls))
    with pytest.raises(InvalidData):
        invoke(src)
    assert calls == []


def test_direct_positive_cache_entry_is_not_returned_when_disabled():
    calls = []
    now = 1000.0
    src = FmarketFundSource(
        http_get=_forbidden_http_get(calls),
        cache_ttl=60.0,
        clock=lambda: now,
    )
    body = {
        "types": ["NEW_FUND", "TRADING_FUND"],
        "sortField": "navTo6Months",
        "sortOrder": "DESC",
        "page": 1,
        "pageSize": 100,
        "isIpo": False,
        "fundAssetTypes": [],
        "searchField": "",
    }
    url = "https://api.fmarket.vn/res/products/filter"
    key = HttpDataSource._cache_key(url, None, body, None)
    src._cache[key] = (
        now + 60.0,
        json.dumps(
            {
                "status": 200,
                "data": {
                    "rows": [
                        {
                            "id": 20,
                            "code": "FAKE",
                            "name": "Fabricated test fund",
                            "nav": 10000,
                        }
                    ]
                },
            }
        ),
    )

    with pytest.raises(SourceUnavailable) as exc_info:
        src.list_funds()
    assert str(exc_info.value) == DISABLED
    assert calls == []


def test_direct_positive_retry_budget_is_not_attempted_when_disabled():
    calls = []
    sleeps = []
    src = FmarketFundSource(
        http_get=_forbidden_http_get(calls),
        max_retries=3,
        sleep=sleeps.append,
    )
    with pytest.raises(SourceUnavailable) as exc_info:
        src.nav_history(20)
    assert str(exc_info.value) == DISABLED
    assert calls == []
    assert sleeps == []


def test_factory_signatures_do_not_gain_cache_or_retry_knobs():
    assert client is source
    source_signature = inspect.signature(source)
    client_signature = inspect.signature(client)
    assert source_signature == client_signature
    assert tuple(source_signature.parameters) == ("http_get", "timeout")
    assert "cache_ttl" not in source_signature.parameters
    assert "max_retries" not in source_signature.parameters


def test_source_unavailable_documents_policy_disabled_sources():
    assert "policy-disabled" in (SourceUnavailable.__doc__ or "").lower()
