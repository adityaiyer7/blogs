"""Auto-fix behavior and idempotence."""

from __future__ import annotations


def test_obsidian_callout_conversion(fix):
    text, applied, remaining = fix("> [!info]- My Title\n> line one\n> line two\n")
    assert '::: {.callout-note title="My Title" collapse="true"}' in text
    assert "line one" in text and "line two" in text
    assert ":::" in text.split('callout-note')[1]
    assert "[!info]" not in text


def test_highlight_conversion(fix):
    text, _, _ = fix("This is ==bold== text.\n")
    assert "**bold**" in text
    assert "==bold==" not in text


def test_inline_math_spacing(fix):
    text, _, _ = fix("Value $ x + y$ here.\n")
    assert "$x + y$" in text


def test_double_space_heading(fix):
    text, _, _ = fix("##  Title\n")
    assert "## Title" in text


def test_idempotent_second_pass_no_op(write_qmd):
    from tools.qmd_lint.engine import fix_document

    body = (
        "Some text.\n# Heading\n\n"
        "> [!note] T\n> body\n\n"
        "This is ==hi== and  trailing.   \n"
    )
    path = write_qmd(body)
    applied_first, _ = fix_document(path)
    assert applied_first > 0
    applied_second, remaining = fix_document(path)
    assert applied_second == 0
    assert all(not f.fixable for f in remaining)


def test_unknown_callout_not_converted(fix):
    text, _, remaining = fix("> [!frobnicate] X\n> body\n")
    assert "[!frobnicate]" in text  # left untouched for manual handling
    assert any(f.rule_id == "N4" for f in remaining)


def test_stray_text_not_autofixed(write_qmd):
    # B7 surfaces the stray token on the initial report; the auto-fixer must
    # never delete it. (The B5 blank-line insertion then separates it from the
    # table, so it becomes a normal paragraph rather than an adjacent stray.)
    from tools.qmd_lint.engine import collect_findings, fix_document
    from tools.qmd_lint.parser import parse

    path = write_qmd("| A | B |\n| - | - |\n| 1 | 2 |\narc\n")
    assert any(f.rule_id == "B7" for f in collect_findings(parse(path)))
    fix_document(path)
    assert "arc" in path.read_text()  # never deleted automatically
