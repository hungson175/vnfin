# API stability & versioning policy

`vnfin` is a library other code imports, so its **public API is a contract**. This document
states what that contract covers, how it may change between releases, and how the contract is
enforced automatically.

## Semantic versioning

`vnfin` follows [Semantic Versioning 2.0.0](https://semver.org/) — and it applies **even while
the version is `0.x`** (we do not use the "anything goes before 1.0" escape hatch):

| Bump | Example | May contain |
|------|---------|-------------|
| **patch** | `0.2.0 → 0.2.1` | bug fixes only; **no** public-API change |
| **minor** | `0.2.0 → 0.3.0` | **additive** changes only (new domains, new exports, new optional params, new enum members, new defaulted dataclass fields) |
| **major** | `0.x → 1.0`, `1.x → 2.0` | **breaking** changes (removals, renames, reorders, type changes, new required params, unit/currency-default changes) |

`__version__` (in `vnfin/__init__.py`) and `pyproject.toml`'s `version` are kept in lockstep.

## What is "the public API" (the contract surface)

Tier-0 surface, snapshotted and enforced (see *Enforcement* below):

- `vnfin.__all__` and each public domain package's `__all__` (`prices`, `fundamentals`,
  `funds`, `indices`, `gold`, `crypto`, `macro`, `exceptions`), and the **kind** of each export
  (module / class / function / dataclass / enum).
- **Factory & convenience signatures** — `client()`, `source()`, `history()`,
  `index_history()`, `get_financials()`, `get_indicator()`, `default_client()`, etc.: parameter
  names, kinds, and which parameters are required vs optional.
- **Public frozen-dataclass fields** (result types like `PriceHistory`, `PriceBar`, `CryptoBar`,
  `GoldQuote`, `FinancialReport`, `IndicatorSeries`, …): field **name, order, type, and
  default-presence**.
- **Public enum members and values** (`Interval`, `AdjustmentPolicy`, `StatementType`, `Period`,
  `MacroIndicator`, `Frequency`).
- Public, user-facing methods of client/source classes.
- **Canonical unit/currency defaults** that are part of result semantics — e.g.
  `PriceHistory.value_unit = "VND"`. Changing one of these silently changes the *meaning* of a
  number and is treated as **breaking** (see [units.md](units.md)).

**Not** part of the contract (may change freely in any release): underscore-prefixed names,
endpoint URLs/params, parser internals, the order of sources inside a failover chain, log/warning
wording, docs prose, and the live JSON shape of upstream providers (that is monitored separately —
see [the health harness](#relationship-to-the-health-harness)).

## Breaking vs additive — the exact rules

These are the rules the comparator enforces (`scripts/dump_api_surface.py::compare_surfaces`):

**Breaking (requires a major bump):**

- removing or renaming a module, export, member, or public method;
- changing an export's kind (e.g. function → class);
- removing an enum member, or changing an enum member's value;
- removing, renaming, or **reordering** a dataclass field; changing a field's type; removing a
  field's default (making it required);
- changing a unit/currency default value on a result field;
- adding a **required** parameter to a public callable; removing a parameter; making an existing
  optional parameter required.

**Additive (allowed in a minor bump):**

- a new module, export, member, enum member, or public method;
- a new **optional** parameter (with a default, or `*args`/`**kwargs`);
- a new dataclass field that is **appended** after existing fields **and** has a default.

## Deprecation policy

Before any breaking change ships, the old behavior is deprecated, not deleted:

1. Emit a `DeprecationWarning` (via `warnings.warn(..., DeprecationWarning, stacklevel=2)`) from
   the deprecated path.
2. Document the replacement in the docstring, `CHANGELOG.md`, and (where relevant) the migration
   notes.
3. Keep the deprecated path working for **at least one minor release**, then remove it only in a
   subsequent **major** release.

New, additive API may ship without a deprecation cycle (nothing is being broken).

## Enforcement (automated)

A committed **baseline snapshot** of the public surface lives at
`tests/snapshots/public_api_<version>.json`. On every test run,
`tests/test_public_api_surface.py`:

1. introspects the **live** surface with `build_surface()`;
2. diffs it against the baseline with the **compatibility-aware** `compare_surfaces()`;
3. **fails** if any diff is classified `breaking`; **prints** (does not fail on) `additive` diffs.

So an accidental rename/removal/reorder/unit-change fails CI immediately, forcing a conscious
decision (revert, or accept and do a major bump + deprecation). Intentional additive growth passes;
the baseline is then **regenerated consciously at release**:

```bash
python scripts/dump_api_surface.py tests/snapshots/public_api_<new-version>.json
# then point _BASELINE in tests/test_public_api_surface.py at the new file
```

Old baselines are kept in git so the surface history is auditable.

## Relationship to the health harness

This policy governs **our own** Python API. The separate **health/monitoring harness**
(`vnfin/_health.py` + `scripts/healthcheck.py`) watches the **upstream providers'** endpoints for
shape/unit drift — a different contract we do *not* control. Upstream drift is surfaced as a health
status, never as a CI failure. See [design/redundancy-failover.md](design/redundancy-failover.md).
