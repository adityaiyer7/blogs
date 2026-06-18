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
