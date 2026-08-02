"""Tests for the segmentation layer — the riskiest component."""

from __future__ import annotations

from tools.qmd_lint.parser import parse


def test_front_matter_parsed(write_qmd):
    doc = parse(write_qmd("# Heading\n"))
    assert doc.front_matter["title"] == "T"
    assert doc.front_matter_range == (1, 5)


def test_code_fence_suppresses_classification(write_qmd):
    body = "```\n$ not math $ | not | a | table\n# not a heading\n```\n"
    doc = parse(write_qmd(body))
    code_lines = [ln for ln in doc.lines if ln.in_code]
    assert len(code_lines) == 4  # the two fences plus two content lines
    assert doc.tables == []
    # No inline math spans should be detected inside the code fence.
    assert all(s.kind != "inline_math" for s in doc.inline_spans)


def test_dollar_inside_inline_code_not_math(write_qmd):
    doc = parse(write_qmd("Use `$PATH` in your shell.\n"))
    assert all(s.kind != "inline_math" for s in doc.inline_spans)


def test_currency_not_inline_math(write_qmd):
    # No closing '$' -> not treated as a math span (avoids $5 / $10 false hits).
    doc = parse(write_qmd("It cost $5 yesterday.\n"))
    assert all(s.kind != "inline_math" for s in doc.inline_spans)


def test_table_detection(write_qmd):
    body = "| A | B |\n| - | - |\n| 1 | 2 |\n"
    doc = parse(write_qmd(body))
    assert len(doc.tables) == 1
    t = doc.tables[0]
    assert t.col_counts == [2, 2, 2]


def test_pipe_in_inline_math_not_a_table(write_qmd):
    doc = parse(write_qmd("The set $\\{a \\mid a > 0\\}$ is fine.\n"))
    assert doc.tables == []


def test_callout_fence_depth(write_qmd):
    body = ":::: {.callout-note}\nouter\n::: {.callout-tip}\ninner\n:::\n::::\n"
    doc = parse(write_qmd(body))
    assert len(doc.callouts) == 2
    assert doc.unclosed_callouts == []


def test_obsidian_callout_parsed(write_qmd):
    body = "> [!note]- Title here\n> body one\n> body two\n"
    doc = parse(write_qmd(body))
    assert len(doc.obsidian_callouts) == 1
    c = doc.obsidian_callouts[0]
    assert c.ctype == "note"
    assert c.fold == "-"
    assert c.title == "Title here"
    assert len(c.body_lines) == 2


def test_display_math_region(write_qmd):
    body = "$$\nx = 1\n$$\n"
    doc = parse(write_qmd(body))
    assert len(doc.display_math) == 1
    assert "x = 1" in doc.display_math[0].text
