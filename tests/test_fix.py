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


def test_callout_body_delete_beats_same_line_whitespace_fix(fix):
    # Regression: a callout body line that ALSO needs a cosmetic fix (trailing
    # whitespace) must still be removed when N1 folds it into the div. Previously
    # the C4 whitespace fix clobbered N1's same-line deletion, leaving a stray
    # duplicate blockquote line below the converted callout.
    text, _, _ = fix("> [!note]\n> live blog body   \n")
    assert "::: {.callout-note}" in text
    assert "live blog body" in text  # content preserved inside the div
    assert "> live blog body" not in text  # no stray leftover blockquote
    assert "[!note]" not in text


def test_mermaid_fence_conversion(fix):
    text, _, _ = fix("```mermaid\nflowchart TB\n  A --> B\n```\n")
    assert "```{mermaid}" in text
    assert "flowchart TB" in text and "A --> B" in text  # body preserved
    # The plain Obsidian opening fence is gone (closing ``` legitimately remains).
    assert "```mermaid\n" not in text + "\n"


def test_mermaid_init_directive_survives(fix):
    # ``%%{init}%%`` is also Obsidian's comment syntax (E3), but inside the fence
    # it must be left intact — it's mermaid configuration, not a comment.
    body = '```mermaid\n%%{init: {"themeVariables": {"fontSize": "13px"}} }%%\nflowchart TB\n  A --> B\n```\n'
    text, _, _ = fix(body)
    assert "```{mermaid}" in text
    assert '%%{init:' in text  # directive not stripped


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
