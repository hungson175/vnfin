"""Public-API surface snapshot test (v0.2 stability gate).

Two things are verified here:

1. A **compatibility-aware comparator** (`compare_surfaces`) that classifies the diff
   between two API-surface descriptions as ``breaking`` (removed/renamed/reordered/
   type-changed/required-param-added/unit-default-changed) or ``additive`` (new export,
   new optional param, new enum member, appended-defaulted field). This is unit-tested
   below against small synthetic surfaces.

2. The committed **baseline snapshot** of the shipped public surface vs. the *live*
   introspected surface: the live surface must introduce **no breaking changes** relative
   to the baseline. Additive changes are allowed (and printed), then folded into the
   baseline consciously at release time.

The introspection + comparator live in ``scripts/dump_api_surface.py`` (import-safe).
"""
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib

import pytest

_REPO = pathlib.Path(__file__).resolve().parents[1]
_SCRIPT = _REPO / "scripts" / "dump_api_surface.py"
_BASELINE = _REPO / "tests" / "snapshots" / "public_api_v0_1_0.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("dump_api_surface", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


das = _load_module()
build_surface = das.build_surface
compare_surfaces = das.compare_surfaces


# ---------------------------------------------------------------------------
# synthetic surface fixtures for the comparator
# ---------------------------------------------------------------------------
def _base() -> dict:
    return {
        "version": "0.1.0",
        "modules": {
            "vnfin": {
                "all": ["Color", "Bar", "make", "Engine"],
                "members": {
                    "Color": {"kind": "enum", "members": {"RED": "red", "BLUE": "blue"}},
                    "Bar": {
                        "kind": "dataclass",
                        "frozen": True,
                        "fields": [
                            {"name": "t", "type": "datetime", "has_default": False, "default_repr": None},
                            {"name": "value_unit", "type": "str", "has_default": True, "default_repr": "'VND'"},
                        ],
                    },
                    "make": {
                        "kind": "function",
                        "params": [
                            {"name": "x", "kind": "POSITIONAL_OR_KEYWORD", "has_default": False},
                            {"name": "y", "kind": "KEYWORD_ONLY", "has_default": True},
                        ],
                        "returns": "Bar",
                    },
                    "Engine": {
                        "kind": "class",
                        "methods": {
                            "run": {
                                "params": [
                                    {"name": "self", "kind": "POSITIONAL_OR_KEYWORD", "has_default": False},
                                    {"name": "n", "kind": "POSITIONAL_OR_KEYWORD", "has_default": True},
                                ],
                                "returns": "int",
                            }
                        },
                    },
                },
            }
        },
    }


def _severities(diffs) -> set[str]:
    return {d["severity"] for d in diffs}


def test_identical_surfaces_have_no_diffs():
    s = _base()
    assert compare_surfaces(s, copy.deepcopy(s)) == []


# ---- exports -------------------------------------------------------------
def test_removed_export_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["all"].remove("Bar")
    del new["modules"]["vnfin"]["members"]["Bar"]
    diffs = compare_surfaces(old, new)
    assert "breaking" in _severities(diffs)
    assert any("Bar" in d["path"] for d in diffs if d["severity"] == "breaking")


def test_added_export_is_additive():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["all"].append("Baz")
    new["modules"]["vnfin"]["members"]["Baz"] = {"kind": "function", "params": [], "returns": "None"}
    diffs = compare_surfaces(old, new)
    assert "breaking" not in _severities(diffs)
    assert "additive" in _severities(diffs)


def test_removed_module_is_breaking():
    old = _base()
    old["modules"]["vnfin.gold"] = {"all": [], "members": {}}
    new = copy.deepcopy(old)
    del new["modules"]["vnfin.gold"]
    assert "breaking" in _severities(compare_surfaces(old, new))


# ---- enums ---------------------------------------------------------------
def test_removed_enum_member_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    del new["modules"]["vnfin"]["members"]["Color"]["members"]["BLUE"]
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_added_enum_member_is_additive():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["Color"]["members"]["GREEN"] = "green"
    diffs = compare_surfaces(old, new)
    assert "breaking" not in _severities(diffs)
    assert "additive" in _severities(diffs)


def test_changed_enum_value_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["Color"]["members"]["RED"] = "crimson"
    assert "breaking" in _severities(compare_surfaces(old, new))


# ---- dataclass fields ----------------------------------------------------
def test_removed_field_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["Bar"]["fields"] = [
        new["modules"]["vnfin"]["members"]["Bar"]["fields"][0]
    ]
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_reordered_field_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["Bar"]["fields"].reverse()
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_changed_field_type_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["Bar"]["fields"][0]["type"] = "str"
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_appended_defaulted_field_is_additive():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["Bar"]["fields"].append(
        {"name": "extra", "type": "int", "has_default": True, "default_repr": "0"}
    )
    diffs = compare_surfaces(old, new)
    assert "breaking" not in _severities(diffs)
    assert "additive" in _severities(diffs)


def test_appended_required_field_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["Bar"]["fields"].append(
        {"name": "extra", "type": "int", "has_default": False, "default_repr": None}
    )
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_changed_unit_default_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["Bar"]["fields"][1]["default_repr"] = "'USD'"
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_field_losing_default_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    f = new["modules"]["vnfin"]["members"]["Bar"]["fields"][1]
    f["has_default"] = False
    f["default_repr"] = None
    assert "breaking" in _severities(compare_surfaces(old, new))


# ---- functions / methods -------------------------------------------------
def test_new_required_param_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["make"]["params"].append(
        {"name": "z", "kind": "POSITIONAL_OR_KEYWORD", "has_default": False}
    )
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_new_optional_param_is_additive():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["make"]["params"].append(
        {"name": "z", "kind": "KEYWORD_ONLY", "has_default": True}
    )
    diffs = compare_surfaces(old, new)
    assert "breaking" not in _severities(diffs)
    assert "additive" in _severities(diffs)


def test_removed_param_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["make"]["params"] = [
        new["modules"]["vnfin"]["members"]["make"]["params"][0]
    ]
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_param_made_required_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["make"]["params"][1]["has_default"] = False
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_removed_method_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    del new["modules"]["vnfin"]["members"]["Engine"]["methods"]["run"]
    assert "breaking" in _severities(compare_surfaces(old, new))


def test_kind_change_is_breaking():
    old = _base()
    new = copy.deepcopy(old)
    new["modules"]["vnfin"]["members"]["make"] = {"kind": "class", "methods": {}}
    assert "breaking" in _severities(compare_surfaces(old, new))


# ---------------------------------------------------------------------------
# live surface vs committed baseline
# ---------------------------------------------------------------------------
def test_baseline_snapshot_exists():
    assert _BASELINE.exists(), (
        f"baseline missing: {_BASELINE}. Generate with "
        f"`python scripts/dump_api_surface.py`."
    )


def test_live_surface_introduces_no_breaking_changes():
    baseline = json.loads(_BASELINE.read_text())
    live = build_surface()
    diffs = compare_surfaces(baseline, live)
    breaking = [d for d in diffs if d["severity"] == "breaking"]
    additive = [d for d in diffs if d["severity"] == "additive"]
    if additive:
        print("\nADDITIVE (non-breaking) surface changes vs baseline:")
        for d in additive:
            print(f"  + [{d['kind']}] {d['path']}: {d['detail']}")
        print("  -> regenerate the baseline at release: python scripts/dump_api_surface.py")
    assert not breaking, "BREAKING public-API changes vs baseline:\n" + "\n".join(
        f"  ! [{d['kind']}] {d['path']}: {d['detail']}" for d in breaking
    )


def test_build_surface_is_deterministic():
    assert build_surface() == build_surface()
