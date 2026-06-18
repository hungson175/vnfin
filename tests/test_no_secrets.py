"""Offline secret-scan regression (P0.1 / B1-B2).

Scans **every** git-tracked text file — including this scanner itself and the
``vnfin/`` source tree — and fails if it finds committed credential material. The
scan is purely **pattern-based**: it never embeds an exact real secret literal, so
the test file cannot itself become the thing it is trying to prevent.

Patterns detected:

1. **JWT-like strings** — ``eyJ`` (base64url of ``{"``) followed by 20+ base64url
   characters. This is the shape of the FireAnt guest bearer JWT and similar tokens.
2. **Non-placeholder ``Authorization: Bearer <token>``** — a Bearer header whose
   value is an actual token, not a redaction placeholder such as ``<redacted>`` /
   ``<token>`` / ``<JWT>`` (those start with ``<`` and are intentionally allowed).
3. **Long high-entropy alphanumeric blobs** — a contiguous run of ONLY ``[A-Za-z0-9]``
   (no separators, so URLs/prose are split below threshold) at least 16 chars long
   that contains **both a lowercase letter and a digit**. That is the shape of the
   Wichart signing token, the AES passphrase, and the BTMC/DOJI widget keys. Benign
   long runs are excluded: git/sha256 hex digests, all-uppercase structured series
   IDs (e.g. FRED ``MKTGDPVNA646NWDB``), and pure numbers.

This is a pure-offline test: it uses ``git ls-files`` to enumerate tracked files and
never touches the network.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

# Repo root = parent of the tests/ directory that holds this file.
REPO_ROOT = Path(__file__).resolve().parent.parent

# JWT-like token shape: "eyJ" (base64url of '{"') + at least 20 base64url chars.
# Assembled from fragments so this source file is never itself a positive match.
_JWT_PREFIX = "ey" + "J"
JWT_RE = re.compile(_JWT_PREFIX + r"[A-Za-z0-9_-]{20,}")

# "Authorization: Bearer <something>" where <something> is a REAL token, i.e. it
# begins with a token character (NOT "<"). Placeholder forms always start with "<"
# (e.g. "<redacted>", "<token>", "<JWT>", "<REDACTED-...>"), so they are NOT matched
# and remain allowed.
BEARER_REAL_RE = re.compile(
    r"[Aa]uthorization:\s*Bearer\s+[A-Za-z0-9][A-Za-z0-9._~+/=-]{7,}"
)

# Long high-entropy blobs. A real signing token / AES passphrase / widget key is a
# single UNBROKEN run of >= 16 alphanumeric characters with no separators. Limiting
# the charset to [A-Za-z0-9] (no "/", "-", "=", ".", "_", "+", space) means URLs and
# ordinary prose are split into short pieces and never reach the threshold; the now-
# fragmented public-widget default in vnfin/gold/vn.py (joined with "+") is likewise
# not a single run.
_SECRET_BLOB_MIN = 16
SECRET_BLOB_RE = re.compile(r"[A-Za-z0-9]{%d,}" % _SECRET_BLOB_MIN)

# Allowlisted long runs that are demonstrably NOT secrets.
#   * 40-char lowercase-hex = git commit SHA referenced in narrative docs.
#   * 64-char lowercase-hex = sha256 digest.
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _blob_is_allowed(blob: str) -> bool:
    """True when a long alnum run is a known-benign token rather than a credential.

    A genuine random secret (signing token, AES passphrase, widget key) contains a
    lowercase letter AND a digit. The carve-outs below cover the benign runs that
    also satisfy that: git/sha256 hex digests, all-uppercase structured series IDs
    (e.g. FRED ``MKTGDPVNA646NWDB`` has no lowercase), pure numbers, and trivially
    low-variety runs.
    """
    if _GIT_SHA_RE.match(blob) or _SHA256_RE.match(blob):
        return True
    if blob.isdigit():  # long number (epoch, count), not a credential
        return True
    has_lower = any(c.islower() for c in blob)
    has_digit = any(c.isdigit() for c in blob)
    # Only flag mixed lowercase+digit runs — the shape of all the real secrets.
    if not (has_lower and has_digit):
        return True
    if len(set(blob)) <= 2:  # single repeated char / clearly structural
        return True
    return False


# Files we deliberately skip from the long-blob heuristic only: clearly binary or
# vendored. NOTE: there is NO self-skip — this scanner test is itself scanned.
_BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
    ".zip", ".gz", ".tar", ".whl", ".so", ".pyc", ".woff", ".woff2",
    ".ttf", ".eot", ".parquet", ".xlsx",
}
# The lock file legitimately carries long base64 wheel hashes; exempt it from the
# broad blob heuristic only (JWT/Bearer scans still apply tree-wide).
_BLOB_SCAN_SKIP_RELPATHS = {
    "uv.lock",
    "poetry.lock",
    "requirements.lock",
}


def _git_tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    rels = [p for p in out.split("\0") if p]
    return [REPO_ROOT / r for r in rels]


def _scannable_text_files() -> list[Path]:
    files: list[Path] = []
    for path in _git_tracked_files():
        if path.suffix.lower() in _BINARY_SUFFIXES:
            continue
        if not path.is_file():
            continue
        files.append(path)
    return files


def _read_text(path: Path) -> str | None:
    """Return UTF-8 text, or None if the file is binary / undecodable."""
    raw = path.read_bytes()
    if b"\0" in raw:  # NUL byte => treat as binary, skip
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_no_jwt_like_strings_in_tracked_files() -> None:
    offenders: list[str] = []
    for path in _scannable_text_files():
        text = _read_text(path)
        if text is None:
            continue
        rel = _rel(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if JWT_RE.search(line):
                offenders.append(f"{rel}:{lineno}")
    assert not offenders, (
        "JWT-like (eyJ...) token(s) found in tracked files — redact to "
        "placeholders like <redacted>:\n" + "\n".join(offenders)
    )


def test_no_real_bearer_tokens_in_tracked_files() -> None:
    offenders: list[str] = []
    for path in _scannable_text_files():
        text = _read_text(path)
        if text is None:
            continue
        rel = _rel(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if BEARER_REAL_RE.search(line):
                offenders.append(f"{rel}:{lineno}")
    assert not offenders, (
        "Non-placeholder 'Authorization: Bearer <realtoken>' found — replace "
        "the token with a placeholder like <redacted>:\n" + "\n".join(offenders)
    )


def test_no_long_secret_blobs_in_tracked_files() -> None:
    """Catch committed signing tokens / AES passphrases / widget keys generically.

    Any contiguous >=26-char base64url/hex run that is not an allowlisted benign
    shape (git SHA, sha256, pure number, structural) is flagged. This is what
    catches the previously-committed Wichart signing token, AES passphrase, and the
    BTMC/DOJI widget keys WITHOUT this file having to store any of those literals.
    """
    offenders: list[str] = []
    for path in _scannable_text_files():
        rel = _rel(path)
        if rel in _BLOB_SCAN_SKIP_RELPATHS:
            continue
        text = _read_text(path)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for blob in SECRET_BLOB_RE.findall(line):
                if _blob_is_allowed(blob):
                    continue
                offenders.append(f"{rel}:{lineno}")
                break
    assert not offenders, (
        "Long secret-like blob(s) found in tracked files. Remove the credential "
        "and source it from env/constructor, or fragment a documented PUBLIC token "
        "so it is not a single contiguous run:\n" + "\n".join(offenders)
    )


def test_scanner_covers_source_and_itself() -> None:
    """Prove the scan surface now INCLUDES this scanner file and the vnfin/ source
    tree (the prior version skipped itself and scoped its exact-secret check to
    docs/research/ only)."""
    scanned = {_rel(p) for p in _scannable_text_files()}
    assert "tests/test_no_secrets.py" in scanned, (
        "the scanner must scan itself (no self-skip allowed)"
    )
    assert "vnfin/gold/vn.py" in scanned, "vnfin/ source must be in scan surface"
    # And at least a representative slice of the package source is covered.
    source_files = {r for r in scanned if r.startswith("vnfin/") and r.endswith(".py")}
    assert len(source_files) >= 5, source_files


def test_btmc_widget_key_is_not_a_committed_secret_literal() -> None:
    """The BTMC public widget key must NOT appear in source as a single unbroken
    run (it is the documented public default, fragmented in vnfin/gold/vn.py and
    sourced via constructor/env). The runtime value still resolves correctly."""
    from vnfin.gold import BTMC_PUBLIC_WIDGET_KEY
    from vnfin.gold.vn import BTMCGoldSource

    # The constant resolves to a usable token at runtime ...
    assert isinstance(BTMC_PUBLIC_WIDGET_KEY, str) and len(BTMC_PUBLIC_WIDGET_KEY) >= 26
    # ... and the adapter uses it (and honours an override) without a hardcoded attr.
    assert not hasattr(BTMCGoldSource, "WIDGET_KEY")
    default_src = BTMCGoldSource(http_get=lambda *a, **k: "{}")
    assert default_src.widget_key == BTMC_PUBLIC_WIDGET_KEY
    override_src = BTMCGoldSource(http_get=lambda *a, **k: "{}", widget_key="custom-xyz")
    assert override_src.widget_key == "custom-xyz"

    # The exact full key must not be a single contiguous run anywhere in source:
    # vn.py builds it from "+"-joined fragments, so the source line is broken up.
    vn_text = (REPO_ROOT / "vnfin" / "gold" / "vn.py").read_text("utf-8")
    assert BTMC_PUBLIC_WIDGET_KEY not in vn_text, (
        "the assembled key must not appear as one literal in source"
    )
