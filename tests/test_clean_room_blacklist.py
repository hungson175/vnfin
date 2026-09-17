"""Exact clean-room contamination gate for the issue #236 changed surfaces."""
from __future__ import annotations

from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
_FAMILY_LOWER = "vn" + "stock"
_FAMILY_TITLE = "VN" + "Stock"
_FAMILY_MIXED = "Vn" + "stock"
_POLICY_PATH = "docs/" + _FAMILY_LOWER + "-blacklist.md"

BLACKLIST_NEEDLES = (("vn" + "stock").casefold(),)

SCAN_PATHS = (
    "vnfin/macro/imf.py",
    "vnfin/macro/client.py",
    "tests/test_macro_worldbank.py",
    "tests/test_macro_imf.py",
    "tests/test_macro_failover.py",
    "tests/test_macro_contracts.py",
    "tests/test_public_api_surface.py",
    "tests/test_docs_contract.py",
    "tests/test_no_secrets.py",
    "tests/test_clean_room_blacklist.py",
    "README.md",
    "CHANGELOG.md",
    _POLICY_PATH,
    "docs/api.md",
    "docs/how-to/byok-fred.md",
    "docs/tutorials/macro-and-fx.md",
    "docs/sources/macro-imf.md",
    "docs/sources/macro-worldbank.md",
    "docs/sources/macro-dbnomics.md",
    "docs/sources/macro-fred.md",
    "docs/ai-usage.md",
    "docs/units.md",
    "docs/roadmap.md",
    "docs/architecture/system-overview.md",
    "docs/architecture/data-domains.md",
    "skills/vnfin/reference/domains.md",
)

ALLOWED_POLICY_REFERENCES = (
    (_POLICY_PATH, f"# {_FAMILY_TITLE} Blacklist Checklist"),
    (
        _POLICY_PATH,
        f"- [ ] Search queries exclude {_FAMILY_TITLE} using negative terms where possible.",
    ),
    (
        _POLICY_PATH,
        f"- [ ] No {_FAMILY_TITLE}/{_FAMILY_MIXED}/{_FAMILY_LOWER}-hq/"
        f"{_FAMILY_LOWER}s.com/thinh-vu/{_FAMILY_LOWER}/{_FAMILY_LOWER}-agent result was opened.",
    ),
    (
        _POLICY_PATH,
        f"- [ ] No {_FAMILY_TITLE} code, docs, API examples, endpoint maps, tests, notebooks, "
        "package metadata, or behavior was used.",
    ),
    (
        _POLICY_PATH,
        f'-{_FAMILY_LOWER} -"{_FAMILY_TITLE}" -{_FAMILY_LOWER}s.com '
        f'-"thinh-vu/{_FAMILY_LOWER}" -{_FAMILY_LOWER}-hq -"{_FAMILY_LOWER}-agent"',
    ),
    (
        _POLICY_PATH,
        f"If avoiding {_FAMILY_TITLE} makes the task impossible, stop and ask Boss for direction.",
    ),
    (
        "README.md",
        f"- **Clean-room policy.** The project does not use {_FAMILY_TITLE}/{_FAMILY_LOWER}-derived "
        "code, docs, schemas, or",
    ),
    (
        "README.md",
        f"endpoint maps. See [docs/{_FAMILY_LOWER}-blacklist.md]"
        f"(docs/{_FAMILY_LOWER}-blacklist.md).",
    ),
    (
        "docs/sources/macro-imf.md",
        "**Clean-room:** endpoint + response shape learned only from the provider's own server "
        "(`www.imf.org/external/datamapper/api/v1`) and "
        "`docs/research/2026-06-18-macro-no-key-byok.md` / "
        f"`docs/research/2026-06-18-macro-vietnam.md`. No {_FAMILY_LOWER}/derivative source consulted.",
    ),
    (
        "docs/sources/macro-worldbank.md",
        "**Clean-room:** endpoints learned only from the provider's own server + "
        "`docs/research/2026-06-18-macro-global-cross-country.md` and "
        f"`docs/research/2026-06-18-macro-vietnam.md`. No {_FAMILY_LOWER}/derivative source consulted.",
    ),
    (
        "docs/sources/macro-dbnomics.md",
        "**Clean-room:** endpoint + response shape learned only from DBnomics' own public API "
        "(`api.db.nomics.world/v22`) and `docs/research/2026-06-18-macro-no-key-byok.md`. "
        f"No {_FAMILY_LOWER}/derivative source consulted.",
    ),
    (
        "docs/sources/macro-fred.md",
        f"`docs/research/2026-06-18-macro-no-key-byok.md`. No {_FAMILY_LOWER}/derivative source.",
    ),
    ("docs/roadmap.md", f"- Clean-room throughout; {_FAMILY_TITLE} fully blacklisted."),
    (
        "docs/architecture/system-overview.md",
        f"developers**. All sources are lawful and license-clear; {_FAMILY_TITLE}/{_FAMILY_LOWER} "
        "and any derived",
    ),
    (
        "docs/architecture/system-overview.md",
        f"material are permanently blacklisted (`docs/{_FAMILY_LOWER}-blacklist.md`).",
    ),
    (
        "CHANGELOG.md",
        f"already fetches via `vnfin.indices` (no {_FAMILY_LOWER}; no `industryID`/"
        "`industryIDv2`/`industry_name`). New",
    ),
)


def test_issue236_changed_surfaces_have_zero_blacklist_contamination():
    actual_pairs = []
    # Record each physical line once even if a future needle tuple has overlap.
    for relative_path in SCAN_PATHS:
        path = REPO_ROOT / relative_path
        assert path.is_file(), f"required scan path is missing: {relative_path}"
        text = path.read_text(encoding="utf-8")
        for raw_line in text.splitlines():
            folded = raw_line.casefold()
            if any(needle in folded for needle in BLACKLIST_NEEDLES):
                actual_pairs.append((relative_path, raw_line.strip()))

    actual_counts = Counter(actual_pairs)
    allowed_counts = Counter(ALLOWED_POLICY_REFERENCES)
    residual_counts = actual_counts - allowed_counts
    residual_contamination = list(residual_counts.elements())

    assert actual_counts == allowed_counts
    assert residual_contamination == []
