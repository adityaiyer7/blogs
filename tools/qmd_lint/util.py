"""Small shared helpers used across rule modules."""

from __future__ import annotations

import re
from pathlib import Path

ATX_HEADING_RE = re.compile(r"^(#{1,6})(\s*)(.*)$")
_URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")


def heading_level(text: str) -> int | None:
    """Return the heading level (1-6) for an ATX heading line, else None."""
    m = ATX_HEADING_RE.match(text)
    if not m:
        return None
    # A real heading needs a space after the hashes (or be hashes-only).
    rest = text[len(m.group(1)) :]
    if rest == "" or rest.startswith(" ") or rest.startswith("\t"):
        return len(m.group(1))
    return None


def is_url(target: str) -> bool:
    target = target.strip()
    return bool(_URL_SCHEME_RE.match(target)) or target.startswith("//")


def is_anchor(target: str) -> bool:
    return target.strip().startswith("#")


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from ``start`` (or CWD) to the directory containing pyproject.toml."""
    cur = (start or Path.cwd()).resolve()
    for cand in [cur, *cur.parents]:
        if (cand / "pyproject.toml").is_file():
            return cand
    return cur
