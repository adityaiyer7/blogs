"""Per-rule detection tests, including negative (must-not-fire) cases."""

from __future__ import annotations

import pytest


# --- Category A: math -------------------------------------------------------

def test_a1_unbalanced_inline_dollar(rule_ids):
    assert "A1" in rule_ids("This has $x + y unclosed.\n")


def test_a1_balanced_ok(rule_ids):
    assert "A1" not in rule_ids("This has $x + y$ closed.\n")


def test_a1_currency_not_flagged(rule_ids):
    assert "A1" not in rule_ids("It cost $5 and then $10 total.\n")


def test_a4_unbalanced_braces(rule_ids):
    assert "A4" in rule_ids("$$\n\\frac{1}{2\n$$\n")


def test_a6_begin_end_mismatch(rule_ids):
    assert "A6" in rule_ids("$$\n\\begin{align} a \\end{aligned}\n$$\n")


def test_a7_mismatched_parens(rule_ids):
    # The ($f_i)$ artifact: a ')' inside math with no matching '('.
    assert "A7" in rule_ids("only feature ($f_i)$ here\n")


def test_a_clean_math_no_findings(rule_ids):
    ids = rule_ids("$$\n\\begin{align} a &= b \\\\ c &= d \\end{align}\n$$\n")
    assert not (ids & {"A1", "A2", "A4", "A5", "A6", "A7"})


# --- Category B: tables -----------------------------------------------------

def test_b1_inconsistent_columns(rule_ids):
    assert "B1" in rule_ids("| A | B |\n| - | - |\n| 1 |\n")


def test_b4_br_in_cell(rule_ids):
    assert "B4" in rule_ids("| A | B |\n| - | - |\n| x<br>y | 2 |\n")


def test_b7_stray_text(rule_ids):
    assert "B7" in rule_ids("| A | B |\n| - | - |\n| 1 | 2 |\narc\n")


def test_b7_normal_prose_after_blank_ok(rule_ids):
    ids = rule_ids("| A | B |\n| - | - |\n| 1 | 2 |\n\nThis is normal prose.\n")
    assert "B7" not in ids


# --- Category C: structure --------------------------------------------------

def test_c2_double_space_heading(rule_ids):
    assert "C2" in rule_ids("##  Design Choices\n")


def test_c1_missing_blank_before_heading(rule_ids):
    assert "C1" in rule_ids("Some text.\n# Heading\n")


# --- Category E: obsidian artifacts -----------------------------------------

def test_e1_wikilink(rule_ids):
    assert "E1" in rule_ids("See [[Other Note]] for details.\n")


def test_e2_highlight(rule_ids):
    assert "E2" in rule_ids("This is ==important== text.\n")


def test_e6_mermaid_fence_detected(rule_ids):
    assert "E6" in rule_ids("```mermaid\nflowchart TB\n  A --> B\n```\n")


def test_e6_quarto_mermaid_not_flagged(rule_ids):
    # Already in Quarto executable-cell form — must be left alone (idempotence).
    assert "E6" not in rule_ids("```{mermaid}\nflowchart TB\n  A --> B\n```\n")


def test_e6_plain_code_block_not_flagged(rule_ids):
    # A bare ``mermaid`` word inside another language's block must not misfire.
    assert "E6" not in rule_ids("```python\nx = 'mermaid'\n```\n")


# --- Category F: front matter -----------------------------------------------

def test_f1_missing_key(write_qmd, lint):
    body = "---\ntitle: \"T\"\n---\n\n# H\n"
    path = write_qmd(body, with_front_matter=False)
    from tools.qmd_lint.engine import collect_findings
    from tools.qmd_lint.parser import parse

    ids = {f.rule_id for f in collect_findings(parse(path))}
    assert "F1" in ids


def test_f_clean_front_matter_ok(rule_ids):
    assert "F1" not in rule_ids("# Heading\n")


def _series_ids(write_qmd, front_matter: str) -> set[str]:
    return {finding.rule_id for finding in _series_findings(write_qmd, front_matter)}


def _series_findings(write_qmd, front_matter: str):
    from tools.qmd_lint.engine import collect_findings
    from tools.qmd_lint.parser import parse

    body = f'---\ntitle: "T"\ndate: 2026-06-18\ncategories: [Test]\n{front_matter}---\n\n# H\n'
    path = write_qmd(body, with_front_matter=False)
    return collect_findings(parse(path))


_COMPLETE_SERIES = 'series-id: representational-geometry\nseries: "RG"\nseries-order: 10\n'


def test_f5_complete_series_metadata_is_clean(write_qmd):
    assert "F5" not in _series_ids(write_qmd, _COMPLETE_SERIES)


def test_f5_no_series_metadata_is_clean(write_qmd):
    assert "F5" not in _series_ids(write_qmd, "")


def test_f5_partial_series_metadata(write_qmd):
    from tools.qmd_lint.model import Severity

    findings = [
        finding
        for finding in _series_findings(
            write_qmd, 'series: "RG"\nseries-order: 10\n'
        )
        if finding.rule_id == "F5"
    ]
    assert findings
    assert all(finding.severity == Severity.ERROR for finding in findings)


def test_f5_non_kebab_series_id(write_qmd):
    assert "F5" in _series_ids(
        write_qmd, 'series-id: Representational Geometry\nseries: "RG"\nseries-order: 10\n'
    )


def test_f5_non_integer_series_order(write_qmd):
    assert "F5" in _series_ids(
        write_qmd, 'series-id: rg\nseries: "RG"\nseries-order: "10"\n'
    )


@pytest.mark.parametrize(
    "front_matter",
    [
        "series-id:\nseries:\nseries-order:\n",
        "series-id: rg\nseries: null\nseries-order: 10\n",
        "series-id: rg\nseries: RG\nseries-order: true\n",
        "series-id: rg\nseries: RG\nseries-order: 10.5\n",
        "series-id: rg\nseries: [RG]\nseries-order: 10\n",
    ],
)
def test_f5_rejects_blank_null_collection_and_non_integer_values(
    write_qmd, front_matter
):
    assert "F5" in _series_ids(write_qmd, front_matter)


def test_f5_accepts_inline_comments_and_quoted_titles(write_qmd):
    front_matter = (
        "series-id: representational-geometry # stable URL\n"
        'series: "Representational \\"Geometry\\"" # display title\n'
        "series-order: 10 # conceptual order\n"
    )
    assert "F5" not in _series_ids(write_qmd, front_matter)


# --- Category N: obsidian callouts ------------------------------------------

def test_n1_detects_obsidian_callout(rule_ids):
    assert "N1" in rule_ids("> [!note] Title\n> body\n")


def test_n4_unknown_type(rule_ids):
    assert "N4" in rule_ids("> [!frobnicate] Title\n> body\n")


def test_n5_nested_callout(rule_ids):
    assert "N5" in rule_ids("> > [!note] Nested\n> > body\n")


def test_n6_unclosed_quarto_callout(rule_ids):
    assert "N6" in rule_ids("::: {.callout-note}\nbody with no close\n")


def test_n8_unknown_quarto_type(rule_ids):
    assert "N8" in rule_ids("::: {.callout-bogus}\nbody\n:::\n")


# --- Category Q: movie quotes -------------------------------------------------

def test_q1_detects_movie_quote_callout(rule_ids):
    ids = rule_ids('> [!moviequote] The Dark Knight — 2026-08-08\n> "Why so serious?"\n')
    assert "Q1" in ids
    assert "Q2" not in ids


def test_q2_malformed_title_missing_date(rule_ids):
    ids = rule_ids('> [!moviequote] The Dark Knight\n> "Why so serious?"\n')
    assert "Q2" in ids


def test_q2_malformed_title_wrong_date_format(rule_ids):
    ids = rule_ids('> [!moviequote] The Dark Knight — Aug 8 2026\n> "Why so serious?"\n')
    assert "Q2" in ids


def test_q_ignores_other_callout_types(rule_ids):
    ids = rule_ids("> [!note] Title\n> body\n")
    assert not ({"Q1", "Q2"} & ids)
