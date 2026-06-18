"""Offline secret-scan regression (P0.1).

Scans every git-tracked text file and fails if it finds committed credential
material:

1. JWT-like strings (``eyJ`` followed by 20+ base64url chars), which is the
   shape of the FireAnt guest bearer JWT and similar tokens.
2. A non-placeholder ``Authorization: Bearer <realtoken>`` header — i.e. a
   Bearer header whose value is an actual token rather than a redaction
   placeholder such as ``<redacted>`` / ``<token>`` / ``<JWT>``.

This is a pure-offline test: it uses ``git ls-files`` to enumerate tracked
files and never touches the network. It guards against re-introducing the
redacted secrets (and any new ones) in future commits.
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

# "Authorization: Bearer <something>" where <something> is a REAL token, i.e.
# it begins with a token character (NOT "<"). Placeholder forms always start
# with "<" (e.g. "<redacted>", "<token>", "<JWT>", "<REDACTED-...>"), so they
# are intentionally NOT matched here and remain allowed.
BEARER_REAL_RE = re.compile(
    r"[Aa]uthorization:\s*Bearer\s+[A-Za-z0-9][A-Za-z0-9._~+/=-]{7,}"
)

# Files we deliberately skip: this test itself (it documents the patterns) and
# anything that is clearly binary or vendored.
_SKIP_RELPATHS = {
    "tests/test_no_secrets.py",
}
_BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
    ".zip", ".gz", ".tar", ".whl", ".so", ".pyc", ".woff", ".woff2",
    ".ttf", ".eot", ".parquet", ".xlsx",
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
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in _SKIP_RELPATHS:
            continue
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


def test_no_jwt_like_strings_in_tracked_files() -> None:
    offenders: list[str] = []
    for path in _scannable_text_files():
        text = _read_text(path)
        if text is None:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
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
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if BEARER_REAL_RE.search(line):
                offenders.append(f"{rel}:{lineno}")
    assert not offenders, (
        "Non-placeholder 'Authorization: Bearer <realtoken>' found — replace "
        "the token with a placeholder like <redacted>:\n" + "\n".join(offenders)
    )


def test_research_docs_have_no_redacted_secrets() -> None:
    """Regression guard for docs/research/*: the credential / anti-circumvention
    secrets we redacted (JWT, static sign-token, AES decryption passphrase, and
    the public widget keys) must not reappear in the research docs.

    Scoped to docs/research/ on purpose: that is the P0.1 lane's surface. The
    high-value JWT and Bearer scans above run tree-wide; the public widget keys
    that still live in source code (e.g. as a documented public-widget config
    value) are a separate lane's concern and not asserted here.
    """
    known_secrets = [
        # FireAnt guest JWT prefix (assembled to avoid self-match).
        _JWT_PREFIX + "0eXAiOiJKV1Qi",
        # Wichart static sign-token.
        "REDACTED",
        # Wichart / fundamentals AES decryption passphrase.
        "***REDACTED-KEY***",
        # BTMC public widget key.
        "3kd8ub1llcg9t45hnoh8hmn7t5kc2v",
        # DOJI public widget key.
        "REDACTED",
    ]
    research_dir = REPO_ROOT / "docs" / "research"
    offenders: list[str] = []
    for path in _scannable_text_files():
        if research_dir not in path.parents:
            continue
        text = _read_text(path)
        if text is None:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        for secret in known_secrets:
            if secret in text:
                offenders.append(f"{rel}: contains a redacted secret")
                break
    assert not offenders, (
        "Previously-redacted secret material reappeared in docs/research/:\n"
        + "\n".join(offenders)
    )
