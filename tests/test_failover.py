"""Tests for the domain-agnostic FailoverClient and the unit-homogeneity guard.

Synthetic only: fabricated source objects, fake symbols, made-up numbers. No real
provider data and no network. Covers (a) the generic engine independent of any
domain and (b) the unit guard that forbids mixing scales/units across a chain.
"""
from __future__ import annotations

import pytest

from vnfin.exceptions import AllSourcesFailed, SourceUnavailable, UnitMismatchError
from vnfin.failover import FailoverClient


class FakeSrc:
    """A minimal domain-agnostic source: a name, a unit, and a callable result."""

    def __init__(self, name, result, *, unit=None, capable=True):
        self.name = name
        self._result = result  # a value to return or an Exception to raise
        self.unit = unit
        self._capable = capable
        self.calls = 0

    def fetch(self, key):
        self.calls += 1
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def _fetch(src, key):
    return src.fetch(key)


# --- generic engine ------------------------------------------------------- #


def test_generic_returns_first_accepted():
    s1 = FakeSrc("s1", {"v": 1})
    s2 = FakeSrc("s2", {"v": 2})
    fc = FailoverClient([s1, s2], operation=_fetch)
    assert fc.run("ZZZ") == {"v": 1}
    assert s1.calls == 1 and s2.calls == 0


def test_generic_fails_over_on_source_error():
    s1 = FakeSrc("s1", SourceUnavailable("down"))
    s2 = FakeSrc("s2", {"v": 2})
    fc = FailoverClient([s1, s2], operation=_fetch)
    assert fc.run("ZZZ") == {"v": 2}
    assert s1.calls == 1 and s2.calls == 1


def test_generic_reject_predicate_falls_through():
    s1 = FakeSrc("s1", {"rows": []})  # rejected: empty
    s2 = FakeSrc("s2", {"rows": [1, 2]})
    fc = FailoverClient(
        [s1, s2],
        operation=_fetch,
        reject=lambda r, *args, **kwargs: "empty" if not r["rows"] else None,
    )
    assert fc.run("ZZZ") == {"rows": [1, 2]}
    assert s1.calls == 1 and s2.calls == 1


def test_generic_reject_one_arg_lambda_still_works():
    """Review B2: public FailoverClient.reject(result) callbacks must keep working."""

    class S:
        name = "s"

        def fetch(self, key):
            return {"ok": True}

    fc = FailoverClient([S()], operation=lambda src, key: src.fetch(key), reject=lambda r: None)
    assert fc.run("ABC") == {"ok": True}


def test_generic_capability_skips_without_call_or_attempt():
    s1 = FakeSrc("s1", {"v": 1}, capable=False)
    s2 = FakeSrc("s2", {"v": 2})
    fc = FailoverClient(
        [s1, s2],
        operation=_fetch,
        capability=lambda src, key: src._capable,
    )
    assert fc.run("ZZZ") == {"v": 2}
    assert s1.calls == 0  # never called, never counted


def test_generic_max_attempts_caps_calls():
    sources = [FakeSrc(f"s{i}", SourceUnavailable("x")) for i in range(5)]
    fc = FailoverClient(sources, operation=_fetch, max_attempts=2)
    with pytest.raises(AllSourcesFailed) as ei:
        fc.run("ZZZ")
    assert len(ei.value.attempts) == 2
    assert [s.calls for s in sources] == [1, 1, 0, 0, 0]


def test_generic_finalize_receives_attempts():
    s1 = FakeSrc("s1", SourceUnavailable("down"))
    s2 = FakeSrc("s2", {"v": 9})
    seen = {}

    def finalize(result, attempts, key):
        seen["attempts"] = attempts
        seen["key"] = key
        return {**result, "n_attempts": len(attempts)}

    fc = FailoverClient([s1, s2], operation=_fetch, finalize=finalize)
    out = fc.run("ABC")
    assert out == {"v": 9, "n_attempts": 2}
    assert seen["key"] == "ABC"
    assert [a.ok for a in seen["attempts"]] == [False, True]


def test_generic_failure_factory_used_on_all_fail():
    s1 = FakeSrc("s1", SourceUnavailable("down"))

    class Boom(Exception):
        pass

    fc = FailoverClient(
        [s1],
        operation=_fetch,
        failure_factory=lambda attempts, key: Boom(f"{key}:{len(attempts)}"),
    )
    with pytest.raises(Boom) as ei:
        fc.run("ZZZ")
    assert str(ei.value) == "ZZZ:1"


def test_generic_no_capable_factory_used():
    s1 = FakeSrc("s1", {"v": 1}, capable=False)

    class NoCap(Exception):
        pass

    fc = FailoverClient(
        [s1],
        operation=_fetch,
        capability=lambda src, key: src._capable,
        no_capable_factory=lambda key: NoCap(key),
    )
    with pytest.raises(NoCap):
        fc.run("ZZZ")
    assert s1.calls == 0


# --- unit-homogeneity guard ----------------------------------------------- #


def test_guard_raises_on_mixed_units():
    vnd = FakeSrc("equity", {"v": 1}, unit="VND")
    pts = FakeSrc("index", {"v": 2}, unit="points")
    with pytest.raises(UnitMismatchError) as ei:
        FailoverClient([vnd, pts], operation=_fetch)
    assert "points" in str(ei.value) and "VND" in str(ei.value)


def test_guard_allows_homogeneous_units():
    a = FakeSrc("a", {"v": 1}, unit="VND")
    b = FakeSrc("b", {"v": 2}, unit="VND")
    fc = FailoverClient([a, b], operation=_fetch)
    assert fc.unit == "VND"
    assert len(fc.sources) == 2


def test_guard_treats_undeclared_units_as_compatible():
    # ``None`` unit = undeclared; mixing undeclared with a declared one is allowed.
    a = FakeSrc("a", {"v": 1}, unit=None)
    b = FakeSrc("b", {"v": 2}, unit="VND")
    fc = FailoverClient([a, b], operation=_fetch)
    assert fc.unit == "VND"
    assert len(fc.sources) == 2


def test_guard_skip_mode_drops_mismatched_source():
    vnd = FakeSrc("equity", SourceUnavailable("down"), unit="VND")
    pts = FakeSrc("index", {"v": 2}, unit="points")  # would be dropped
    extra = FakeSrc("equity2", {"v": 3}, unit="VND")
    fc = FailoverClient(
        [vnd, pts, extra], operation=_fetch, on_unit_mismatch="skip"
    )
    assert [s.name for s in fc.sources] == ["equity", "equity2"]
    # points source is gone, so failover from the VND error lands on equity2
    assert fc.run("ZZZ") == {"v": 3}
    assert pts.calls == 0


def test_guard_rejects_bad_on_mismatch_value():
    with pytest.raises(ValueError):
        FailoverClient([], operation=_fetch, on_unit_mismatch="nope")


def test_guard_three_way_mismatch_raises():
    a = FakeSrc("a", {"v": 1}, unit="VND")
    b = FakeSrc("b", {"v": 2}, unit="VND")
    c = FakeSrc("c", {"v": 3}, unit="USD")
    with pytest.raises(UnitMismatchError):
        FailoverClient([a, b, c], operation=_fetch)


# --- B13: max_attempts validation ---------------------------------------- #


@pytest.mark.parametrize("bad", [0, -1, "x", 2.0, None])
def test_max_attempts_rejects_invalid_values(bad):
    s1 = FakeSrc("s1", {"v": 1})
    with pytest.raises(ValueError):
        FailoverClient([s1], operation=_fetch, max_attempts=bad)


def test_max_attempts_rejects_bool_true():
    # bool is an int subclass; True must NOT be accepted as max_attempts=1.
    s1 = FakeSrc("s1", {"v": 1})
    with pytest.raises(ValueError):
        FailoverClient([s1], operation=_fetch, max_attempts=True)


def test_max_attempts_rejects_bool_false():
    s1 = FakeSrc("s1", {"v": 1})
    with pytest.raises(ValueError):
        FailoverClient([s1], operation=_fetch, max_attempts=False)


def test_max_attempts_accepts_positive_int():
    s1 = FakeSrc("s1", {"v": 1})
    fc = FailoverClient([s1], operation=_fetch, max_attempts=1)
    assert fc.max_attempts == 1
    assert fc.run("ZZZ") == {"v": 1}
