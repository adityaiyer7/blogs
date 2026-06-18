"""Category A — LaTeX / math rules. Operate only inside parsed math spans."""

from __future__ import annotations

import re

from ..model import Finding, Fix, Severity, rule
from ..parser import Document, Region

_OBSIDIAN_MATH_DELIM_RE = re.compile(r"\\[\(\)\[\]]")


def _scannable_body_lines(doc: Document):
    for ln in doc.lines:
        if ln.in_code or ln.in_front_matter:
            continue
        yield ln


def _count_lone_dollars(text: str) -> int:
    """Count single '$' delimiters (not '$$'), skipping code spans and escapes."""
    i = 0
    n = len(text)
    count = 0
    in_code = False
    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
            i += 1
            continue
        if ch == "$" and not in_code:
            if i + 1 < n and text[i + 1] == "$":
                i += 2
                continue
            count += 1
        i += 1
    return count


@rule("A1", "A", Severity.ERROR)
def a1_unbalanced_inline_dollar(doc: Document) -> list[Finding]:
    out = []
    for ln in _scannable_body_lines(doc):
        if ln.in_display_math:
            continue
        if _count_lone_dollars(ln.raw) % 2 == 1:
            out.append(
                Finding("A1", Severity.ERROR, ln.number, "odd number of '$' — unclosed inline math")
            )
    return out


@rule("A2", "A", Severity.ERROR)
def a2_unbalanced_display_dollar(doc: Document) -> list[Finding]:
    total = 0
    first_line = None
    for ln in _scannable_body_lines(doc):
        c = ln.raw.count("$$")
        if c and first_line is None:
            first_line = ln.number
        total += c
    if total % 2 == 1:
        return [Finding("A2", Severity.ERROR, first_line or 1, "odd number of '$$' — unclosed display math")]
    return []


@rule("A3", "A", Severity.WARNING, fixable=True)
def a3_delimiter_spacing(doc: Document) -> list[Finding]:
    """Stray space just inside inline-math delimiters: $ x$ / $x $."""
    out = []
    # Group inline-math spans by line so one line yields one rebuilt fix.
    by_line: dict[int, list] = {}
    for span in doc.inline_spans:
        if span.kind == "inline_math":
            by_line.setdefault(span.line, []).append(span)
    for line_no, spans in by_line.items():
        needs = [s for s in spans if s.text != s.text.strip() and s.text.strip() != ""]
        if not needs:
            continue
        raw = doc.line_text(line_no)
        # Rebuild right-to-left so offsets stay valid.
        new = raw
        for s in sorted(spans, key=lambda s: s.start, reverse=True):
            if s.text != s.text.strip() and s.text.strip() != "":
                new = new[: s.start] + "$" + s.text.strip() + "$" + new[s.end :]
        out.append(
            Finding(
                "A3",
                Severity.WARNING,
                line_no,
                "stray space inside inline-math delimiter",
                fixable=True,
                fix=Fix(line=line_no, new_text=new),
            )
        )
    return out


@rule("A8", "A", Severity.WARNING)
def a8_display_math_inline(doc: Document) -> list[Finding]:
    """Display '$$' sharing a line with other prose text (renders awkwardly)."""
    out = []
    for ln in _scannable_body_lines(doc):
        stripped = ln.raw.strip()
        if "$$" not in stripped:
            continue
        # A clean display line is exactly the delimiters plus math, nothing else.
        if stripped == "$$":
            continue
        if stripped.startswith("$$") and stripped.endswith("$$") and stripped.count("$$") == 2:
            continue  # self-contained $$ ... $$ is fine
        # Opening or closing delimiter glued to prose on the same physical line.
        if not (stripped.startswith("$$") or stripped.endswith("$$")):
            out.append(
                Finding("A8", Severity.WARNING, ln.number, "display '$$' shares a line with prose text")
            )
    return out


def _strip_escapes(text: str) -> str:
    return re.sub(r"\\[\{\}\(\)\[\]]", "", text)


@rule("A4", "A", Severity.ERROR)
def a4_unbalanced_braces(doc: Document) -> list[Finding]:
    out = []
    for span in doc.iter_math():
        depth = 0
        bad = False
        for ch in _strip_escapes(span.text):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0:
                    bad = True
                    break
        if bad or depth != 0:
            out.append(Finding("A4", Severity.ERROR, span.start_line, "unbalanced '{' / '}' in math"))
    return out


@rule("A5", "A", Severity.ERROR)
def a5_left_right(doc: Document) -> list[Finding]:
    out = []
    for span in doc.iter_math():
        left = len(re.findall(r"\\left\b", span.text))
        right = len(re.findall(r"\\right\b", span.text))
        if left != right:
            out.append(
                Finding("A5", Severity.ERROR, span.start_line, f"\\left/\\right mismatch ({left} vs {right})")
            )
    return out


@rule("A6", "A", Severity.ERROR)
def a6_begin_end(doc: Document) -> list[Finding]:
    out = []
    for span in doc.iter_math():
        stack = []
        ok = True
        for kind, name in re.findall(r"\\(begin|end)\{([^}]*)\}", span.text):
            if kind == "begin":
                stack.append(name)
            else:
                if not stack or stack.pop() != name:
                    ok = False
                    break
        if not ok or stack:
            out.append(
                Finding("A6", Severity.ERROR, span.start_line, "unbalanced or mismatched \\begin/\\end")
            )
    return out


@rule("A7", "A", Severity.WARNING)
def a7_parens(doc: Document) -> list[Finding]:
    out = []
    for span in doc.iter_math():
        text = _strip_escapes(span.text)
        if text.count("(") != text.count(")"):
            out.append(Finding("A7", Severity.WARNING, span.start_line, "mismatched parentheses in math"))
    return out


@rule("A9", "A", Severity.WARNING)
def a9_empty_math(doc: Document) -> list[Finding]:
    out = []
    for span in doc.iter_math():
        if span.text.strip() == "":
            out.append(Finding("A9", Severity.WARNING, span.start_line, "empty math span"))
    return out


@rule("A10", "A", Severity.WARNING)
def a10_obsidian_math_delims(doc: Document) -> list[Finding]:
    out = []
    for ln in _scannable_body_lines(doc):
        if ln.in_display_math:
            continue
        if _OBSIDIAN_MATH_DELIM_RE.search(ln.raw):
            out.append(
                Finding("A10", Severity.WARNING, ln.number, r"Obsidian math delimiter \( \) \[ \] — use $…$ / $$…$$")
            )
    return out


@rule("A11", "A", Severity.WARNING)
def a11_stray_linebreak(doc: Document) -> list[Finding]:
    out = []
    for span in doc.iter_math():
        if "\\\\" in span.text and "\\begin{" not in span.text:
            out.append(
                Finding("A11", Severity.WARNING, span.start_line, "'\\\\' line break outside an environment")
            )
    return out
