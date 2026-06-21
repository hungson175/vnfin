#!/usr/bin/env python3
"""Introspect vnfin's public API surface and compare two surfaces for compatibility.

Two responsibilities, both import-safe (no side effects on import):

* ``build_surface()`` — walk ``vnfin`` and its public domain subpackages and produce a
  deterministic, JSON-able description of the **public** surface (Tier-0): per-module
  ``__all__``, exported symbol kinds, public factory/convenience signatures, public
  frozen-dataclass fields (name/order/type/default-presence/unit-default), public enum
  members+values, and public client/source user-facing methods.

* ``compare_surfaces(old, new)`` — a **compatibility-aware** diff. It returns a list of
  ``{"severity", "kind", "path", "detail"}`` dicts. ``severity`` is ``"breaking"`` for
  removals/renames/reorders/type-changes/required-param-additions/unit-default-changes,
  and ``"additive"`` for backwards-compatible growth (new export, new optional param,
  new enum member, appended-defaulted field).

CLI: ``python scripts/dump_api_surface.py [OUTPUT.json]`` writes the current surface to
the per-release baseline snapshot (default: ``tests/snapshots/public_api_v0_2_0.json``).
"""
from __future__ import annotations

import dataclasses
import enum
import importlib
import inspect
import json
import pathlib
import sys
from typing import Any

# Top-level package + the public domain subpackages reachable as `vnfin.<name>`.
ROOT = "vnfin"
DOMAIN_MODULES = [
    "vnfin",
    "vnfin.exceptions",
    "vnfin.prices",
    "vnfin.equities",
    "vnfin.fundamentals",
    "vnfin.funds",
    "vnfin.indices",
    "vnfin.gold",
    "vnfin.crypto",
    "vnfin.macro",
    "vnfin.fx",
    "vnfin.sources",
    "vnfin.diagnostics",
    "vnfin.news",
    "vnfin.liquidity",
]

# Field names whose *default value* is part of the result's semantic contract.
# Changing one of these defaults is a breaking change (silent unit/currency shift).
_UNIT_FIELD_NAMES = frozenset(
    {"value_unit", "unit", "currency", "quote_currency", "base_currency", "price_unit"}
)


# --------------------------------------------------------------------------- #
# introspection
# --------------------------------------------------------------------------- #
def _normalize_annotation(ann: Any) -> str | None:
    """A stable, module-prefix-free string for a type annotation."""
    if ann is inspect.Signature.empty or ann is inspect.Parameter.empty:
        return None
    if ann is None:
        return "None"
    if isinstance(ann, str):
        text = ann
    else:
        try:
            text = inspect.formatannotation(ann)
        except Exception:
            text = str(ann)
    # strip our own + common stdlib module prefixes for stability
    for prefix in ("vnfin.", "datetime.", "decimal.", "typing."):
        text = text.replace(prefix, "")
    return text.strip()


def _jsonable(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _default_repr(value: Any) -> str | None:
    """A stable repr for a JSON-safe scalar/enum/None default; ``None`` otherwise.

    ``None`` here means "no comparable default captured" (either no default at all, or a
    non-scalar default like a factory/sentinel/object we deliberately don't pin)."""
    if value is inspect.Parameter.empty or value is dataclasses.MISSING:
        return None
    if value is None or isinstance(value, (str, int, float, bool, enum.Enum)):
        return repr(_jsonable(value))
    return None


def _describe_signature(obj: Any) -> dict[str, Any] | None:
    try:
        sig = inspect.signature(obj)
    except (ValueError, TypeError):
        return None
    params = []
    for p in sig.parameters.values():
        params.append(
            {
                "name": p.name,
                "kind": p.kind.name,
                "has_default": p.default is not inspect.Parameter.empty,
                "default_repr": _default_repr(p.default),
            }
        )
    return {"params": params, "returns": _normalize_annotation(sig.return_annotation)}


def _describe_dataclass(cls: type) -> dict[str, Any]:
    fields = []
    for f in dataclasses.fields(cls):
        has_default = (
            f.default is not dataclasses.MISSING
            or f.default_factory is not dataclasses.MISSING  # type: ignore[misc]
        )
        # Capture the default repr for scalar/enum/None defaults (incl. an explicit
        # ``None``); ``None`` here means "no comparable default captured" (no default, or a
        # non-scalar default like a factory/sentinel) — see _default_repr.
        default_repr = None
        if f.default is not dataclasses.MISSING:
            default_repr = _default_repr(f.default)
        fields.append(
            {
                "name": f.name,
                "type": _normalize_annotation(f.type),
                "has_default": has_default,
                "default_repr": default_repr,
            }
        )
    frozen = bool(getattr(cls, "__dataclass_params__", None) and cls.__dataclass_params__.frozen)
    return {"kind": "dataclass", "frozen": frozen, "fields": fields}


def _describe_enum(cls: type) -> dict[str, Any]:
    return {
        "kind": "enum",
        "members": {m.name: _jsonable(m.value) for m in cls},  # type: ignore[union-attr]
    }


def _describe_class(cls: type) -> dict[str, Any]:
    methods: dict[str, Any] = {}
    for name in sorted(dir(cls)):
        if name.startswith("_"):
            continue
        try:
            attr = inspect.getattr_static(cls, name)
        except AttributeError:
            continue
        if isinstance(attr, (staticmethod, classmethod)):
            attr = attr.__func__
        if isinstance(attr, property):
            methods[name] = {"property": True}
            continue
        if not (inspect.isfunction(attr) or inspect.ismethod(attr)):
            continue
        sig = _describe_signature(attr)
        if sig is not None:
            methods[name] = sig
    result: dict[str, Any] = {"kind": "class", "methods": methods}
    # public classes are user-instantiable: capture a user-defined __init__ (a generated
    # dataclass __init__ never reaches here — dataclasses are described as "dataclass").
    init = inspect.getattr_static(cls, "__init__", None)
    if isinstance(init, (staticmethod, classmethod)):
        init = init.__func__
    if inspect.isfunction(init):
        ctor = _describe_signature(init)
        if ctor is not None:
            result["constructor"] = ctor
    return result


def _describe_member(obj: Any) -> dict[str, Any]:
    if inspect.ismodule(obj):
        return {"kind": "module"}
    if isinstance(obj, type):
        if issubclass(obj, enum.Enum):
            return _describe_enum(obj)
        if dataclasses.is_dataclass(obj):
            return _describe_dataclass(obj)
        return _describe_class(obj)
    if inspect.isfunction(obj) or inspect.isbuiltin(obj) or callable(obj):
        sig = _describe_signature(obj)
        return {"kind": "function", **(sig or {"params": [], "returns": None})}
    return {"kind": "value", "type": type(obj).__name__}


def _public_names(module: Any) -> list[str]:
    declared = getattr(module, "__all__", None)
    names = list(declared) if declared is not None else [n for n in dir(module) if not n.startswith("_")]
    # `annotations` from `from __future__ import annotations` is not real public API
    return [n for n in names if n != "annotations"]


def build_surface() -> dict[str, Any]:
    """Introspect the live ``vnfin`` package into a deterministic surface dict."""
    root = importlib.import_module(ROOT)
    surface: dict[str, Any] = {
        "version": getattr(root, "__version__", "?"),
        "modules": {},
    }
    for mod_name in DOMAIN_MODULES:
        module = importlib.import_module(mod_name)
        names = _public_names(module)
        members: dict[str, Any] = {}
        for name in names:
            try:
                obj = getattr(module, name)
            except AttributeError:
                members[name] = {"kind": "MISSING"}
                continue
            members[name] = _describe_member(obj)
        entry: dict[str, Any] = {"all": list(names), "members": members}
        if mod_name == ROOT:
            entry["version"] = surface["version"]
        surface["modules"][mod_name] = entry
    return surface


# --------------------------------------------------------------------------- #
# compatibility-aware comparator
# --------------------------------------------------------------------------- #
def _diff(severity: str, kind: str, path: str, detail: str) -> dict[str, str]:
    return {"severity": severity, "kind": kind, "path": path, "detail": detail}


def _compare_enum(old: dict, new: dict, path: str, out: list) -> None:
    om, nm = old.get("members", {}), new.get("members", {})
    for name, val in om.items():
        if name not in nm:
            out.append(_diff("breaking", "enum_member", f"{path}.{name}", "member removed"))
        elif nm[name] != val:
            out.append(
                _diff("breaking", "enum_value", f"{path}.{name}", f"value {val!r} -> {nm[name]!r}")
            )
    for name in nm:
        if name not in om:
            out.append(_diff("additive", "enum_member", f"{path}.{name}", "member added"))


def _compare_fields(old: dict, new: dict, path: str, out: list) -> None:
    of, nf = old.get("fields", []), new.get("fields", [])
    old_by_name = {f["name"]: (i, f) for i, f in enumerate(of)}
    new_by_name = {f["name"]: (i, f) for i, f in enumerate(nf)}
    for name, (idx, f) in old_by_name.items():
        if name not in new_by_name:
            out.append(_diff("breaking", "field", f"{path}.{name}", "field removed"))
            continue
        nidx, nf_f = new_by_name[name]
        if nidx != idx:
            out.append(_diff("breaking", "field", f"{path}.{name}", f"reordered {idx} -> {nidx}"))
        if f.get("type") != nf_f.get("type"):
            out.append(
                _diff("breaking", "field", f"{path}.{name}", f"type {f.get('type')} -> {nf_f.get('type')}")
            )
        if f.get("has_default") and not nf_f.get("has_default"):
            out.append(_diff("breaking", "field", f"{path}.{name}", "lost its default (now required)"))
        od, nd = f.get("default_repr"), nf_f.get("default_repr")
        if f.get("has_default") and nf_f.get("has_default") and od != nd:
            # Any change to a defaulted field's captured default forces a conscious decision
            # (incl. captured->uncaptured, e.g. a scalar default becoming None/a factory). A
            # unit/currency default change additionally changes the meaning of the value.
            kind = "unit_default" if name in _UNIT_FIELD_NAMES else "field_default"
            out.append(_diff("breaking", kind, f"{path}.{name}", f"default {od} -> {nd}"))
    n_old = len(of)
    for name, (idx, f) in new_by_name.items():
        if name in old_by_name:
            continue
        # new field: additive only if appended after all old fields AND defaulted
        if idx >= n_old and f.get("has_default"):
            out.append(_diff("additive", "field", f"{path}.{name}", "appended defaulted field"))
        else:
            out.append(
                _diff("breaking", "field", f"{path}.{name}", "new required or non-appended field")
            )


def _compare_callable(old: dict, new: dict, path: str, out: list) -> None:
    """Compare a function/method/constructor signature: params (presence, order, kind,
    required-ness, default value) AND return annotation."""
    op = old.get("params", []) or []
    np_ = new.get("params", []) or []
    old_by_name = {p["name"]: (i, p) for i, p in enumerate(op)}
    new_by_name = {p["name"]: (i, p) for i, p in enumerate(np_)}
    for name, (i, p) in old_by_name.items():
        if name not in new_by_name:
            out.append(_diff("breaking", "param", f"{path}({name})", "parameter removed"))
            continue
        j, np_p = new_by_name[name]
        if i != j:
            out.append(_diff("breaking", "param", f"{path}({name})", f"reordered {i} -> {j}"))
        if p.get("kind") != np_p.get("kind"):
            out.append(
                _diff("breaking", "param", f"{path}({name})", f"kind {p.get('kind')} -> {np_p.get('kind')}")
            )
        if not p.get("has_default") and np_p.get("has_default"):
            out.append(_diff("additive", "param", f"{path}({name})", "now optional"))
        if p.get("has_default") and not np_p.get("has_default"):
            out.append(_diff("breaking", "param", f"{path}({name})", "now required"))
        od, nd = p.get("default_repr"), np_p.get("default_repr")
        if od is not None and nd is not None and od != nd:
            out.append(_diff("breaking", "param", f"{path}({name})", f"default {od} -> {nd}"))
    for name, (j, p) in new_by_name.items():
        if name in old_by_name:
            continue
        appended = j >= len(op)
        optional = p.get("has_default") or p.get("kind") in ("VAR_POSITIONAL", "VAR_KEYWORD")
        if appended and optional:
            out.append(_diff("additive", "param", f"{path}({name})", "new optional parameter"))
        else:
            out.append(_diff("breaking", "param", f"{path}({name})", "new required or inserted parameter"))
    o_ret, n_ret = old.get("returns"), new.get("returns")
    # changing OR removing a declared return type is breaking; only *adding* one (old None)
    # is non-breaking.
    if o_ret is not None and o_ret != n_ret:
        out.append(_diff("breaking", "return", path, f"return type {o_ret} -> {n_ret}"))


def _compare_methods(old: dict, new: dict, path: str, out: list) -> None:
    om, nm = old.get("methods", {}), new.get("methods", {})
    for name, sig in om.items():
        if name not in nm:
            out.append(_diff("breaking", "method", f"{path}.{name}", "method removed"))
            continue
        if "property" in sig or "property" in nm[name]:
            if ("property" in sig) != ("property" in nm[name]):
                out.append(_diff("breaking", "method", f"{path}.{name}", "property/method kind changed"))
            continue
        _compare_callable(sig, nm[name], f"{path}.{name}", out)
    for name in nm:
        if name not in om:
            out.append(_diff("additive", "method", f"{path}.{name}", "method added"))


def _compare_member(old: dict, new: dict, path: str, out: list) -> None:
    if old.get("kind") != new.get("kind"):
        out.append(
            _diff("breaking", "kind", path, f"kind {old.get('kind')} -> {new.get('kind')}")
        )
        return
    kind = old.get("kind")
    if kind == "enum":
        _compare_enum(old, new, path, out)
    elif kind == "dataclass":
        if old.get("frozen") and not new.get("frozen"):
            out.append(_diff("breaking", "dataclass", path, "no longer frozen"))
        _compare_fields(old, new, path, out)
    elif kind == "function":
        _compare_callable(old, new, path, out)
    elif kind == "class":
        oc, nc = old.get("constructor"), new.get("constructor")
        if oc is not None and nc is None:
            out.append(_diff("breaking", "constructor", path, "constructor signature removed"))
        elif oc is not None and nc is not None:
            _compare_callable(oc, nc, f"{path}.__init__", out)
        elif oc is None and nc is not None:
            # a class that had no captured constructor gains one: breaking only if the new
            # constructor introduces a REQUIRED parameter (beyond self) — that changes how
            # existing call sites can instantiate it.
            required = [
                p
                for p in nc.get("params", [])
                if p.get("name") != "self"
                and not p.get("has_default")
                and p.get("kind") not in ("VAR_POSITIONAL", "VAR_KEYWORD")
            ]
            if required:
                out.append(
                    _diff("breaking", "constructor", path, "gained a required constructor parameter")
                )
        _compare_methods(old, new, path, out)


def compare_surfaces(old: dict, new: dict) -> list[dict[str, str]]:
    """Compatibility-aware diff of two API surfaces (see module docstring)."""
    out: list[dict[str, str]] = []
    old_mods, new_mods = old.get("modules", {}), new.get("modules", {})
    for mod_name, old_mod in old_mods.items():
        if mod_name not in new_mods:
            out.append(_diff("breaking", "module", mod_name, "module removed"))
            continue
        new_mod = new_mods[mod_name]
        old_all = set(old_mod.get("all", []))
        new_all = set(new_mod.get("all", []))
        for name in old_all - new_all:
            out.append(_diff("breaking", "export", f"{mod_name}.{name}", "export removed"))
        for name in new_all - old_all:
            out.append(_diff("additive", "export", f"{mod_name}.{name}", "export added"))
        old_members = old_mod.get("members", {})
        new_members = new_mod.get("members", {})
        for name, old_member in old_members.items():
            if name not in new_members:
                # already reported as removed export if it was in __all__
                if name not in old_all:
                    out.append(_diff("breaking", "member", f"{mod_name}.{name}", "member removed"))
                continue
            _compare_member(old_member, new_members[name], f"{mod_name}.{name}", out)
    for mod_name in new_mods:
        if mod_name not in old_mods:
            out.append(_diff("additive", "module", mod_name, "module added"))
    return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str]) -> int:
    default_out = pathlib.Path(__file__).resolve().parents[1] / "tests" / "snapshots" / "public_api_v0_2_0.json"
    out_path = pathlib.Path(argv[1]) if len(argv) > 1 else default_out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    surface = build_surface()
    out_path.write_text(json.dumps(surface, indent=2, sort_keys=True) + "\n")
    print(f"wrote API surface ({surface['version']}) -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
