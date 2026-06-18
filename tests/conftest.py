"""Shared pytest helpers for the qmd_lint test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the repo root (containing the `tools` package) is importable.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.qmd_lint.engine import collect_findings, fix_document  # noqa: E402
from tools.qmd_lint.parser import parse  # noqa: E402

FRONT_MATTER = '---\ntitle: "T"\ndate: 2026-06-18\ncategories: [Test]\n---\n\n'


def _write(tmp_path: Path, body: str, with_front_matter: bool = True) -> Path:
    text = (FRONT_MATTER + body) if with_front_matter else body
    p = tmp_path / "index.qmd"
    p.write_text(text, encoding="utf-8")
    return p


@pytest.fixture
def write_qmd(tmp_path):
    def _factory(body: str, with_front_matter: bool = True) -> Path:
        return _write(tmp_path, body, with_front_matter)

    return _factory


@pytest.fixture
def lint(write_qmd):
    def _lint(body: str, with_front_matter: bool = True):
        return collect_findings(parse(write_qmd(body, with_front_matter)))

    return _lint


@pytest.fixture
def rule_ids(lint):
    def _ids(body: str, with_front_matter: bool = True) -> set[str]:
        return {f.rule_id for f in lint(body, with_front_matter)}

    return _ids


@pytest.fixture
def fix(write_qmd):
    def _fix(body: str, with_front_matter: bool = True):
        path = write_qmd(body, with_front_matter)
        applied, remaining = fix_document(path)
        return path.read_text(encoding="utf-8"), applied, remaining

    return _fix
