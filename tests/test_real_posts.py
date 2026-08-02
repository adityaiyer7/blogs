"""Integration tests over the real blog posts (regression baselines)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.qmd_lint.engine import collect_findings
from tools.qmd_lint.parser import parse

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS = sorted(REPO_ROOT.glob("blogposts/posts/*/index.qmd"))


def _findings_for(slug: str):
    path = REPO_ROOT / "blogposts" / "posts" / slug / "index.qmd"
    return collect_findings(parse(path))


@pytest.mark.parametrize("path", POSTS, ids=lambda p: p.parent.name)
def test_posts_parse_without_crashing(path):
    findings = collect_findings(parse(path))
    assert isinstance(findings, list)


def test_sae_known_artifacts_detected():
    ids_by_line = {(f.rule_id, f.line) for f in _findings_for("sae-for-monosemanticity")}
    rule_hits = {rid for rid, _ in ids_by_line}
    # The known issues we expect to keep catching:
    assert ("B7", 439) in ids_by_line  # stray 'arc'
    assert ("A7", 102) in ids_by_line  # ($f_i)$ mismatched paren
    assert "B4" in rule_hits  # <br> inside WandB table cells
    assert "C2" in rule_hits  # double-space headings (lines 15, 166)


def test_no_errors_in_existing_posts():
    # The current posts render fine, so the linter should not raise hard errors.
    for path in POSTS:
        errors = [f for f in collect_findings(parse(path)) if f.severity.label == "ERROR"]
        assert errors == [], f"{path.parent.name}: unexpected errors {[ (e.rule_id, e.line) for e in errors]}"
