"""Phase 1 contract primitives — object/list guards + duplicate policy (#refactor)."""
from __future__ import annotations

import pytest

from vnfin._contracts import reject_duplicate, require_list, require_object
from vnfin.exceptions import InvalidData

CTX = "test row"


@pytest.mark.parametrize("bad", ["a string", 123, None, [1, 2], 4.5, True])
def test_require_object_rejects_non_dict(bad):
    with pytest.raises(InvalidData, match="expected an object"):
        require_object(bad, CTX)


def test_require_object_returns_dict():
    d = {"k": "v"}
    assert require_object(d, CTX) is d


@pytest.mark.parametrize("bad", ["a string", 123, None, {"k": 1}, 4.5, True])
def test_require_list_rejects_non_list(bad):
    with pytest.raises(InvalidData, match="expected a list"):
        require_list(bad, CTX)


def test_require_list_returns_list():
    rows = [1, 2, 3]
    assert require_list(rows, CTX) is rows


# --- reject_duplicate (atomic check+add) ------------------------------------
def test_reject_duplicate_adds_then_rejects():
    seen: set = set()
    reject_duplicate("11000", seen, CTX)   # first: recorded
    assert "11000" in seen
    with pytest.raises(InvalidData, match="duplicate key"):
        reject_duplicate("11000", seen, CTX)  # second: rejected


def test_reject_duplicate_distinct_keys_all_accepted():
    seen: set = set()
    for k in ("a", "b", "c"):
        reject_duplicate(k, seen, CTX)
    assert seen == {"a", "b", "c"}
