"""Category C — heading / structure rules."""

from __future__ import annotations

import re

from ..model import Finding, Fix, Severity, rule
from ..parser import Document
from ..util import heading_level

_MULTISPACE_HEADING_RE = re.compile(r"^(#{1,6}) {2,}(\S)")


def _body_lines(doc: Document):
    for ln in doc.lines:
        if ln.in_code or ln.in_front_matter:
            continue
        yield ln


@rule("C1", "C", Severity.WARNING, fixable=True)
def c1_blank_before_heading(doc: Document) -> list[Finding]:
    out = []
    for ln in doc.lines:
        if ln.in_code or ln.in_front_matter:
            continue
        if heading_level(ln.raw) is None:
            continue
        if ln.number == 1:
            continue
        prev = doc.line_text(ln.number - 1)
        if prev.strip() != "":
            out.append(
                Finding(
                    "C1",
                    Severity.WARNING,
                    ln.number,
                    "missing blank line before heading",
                    fixable=True,
                    fix=Fix(line=ln.number, insert_before=""),
                )
            )
    return out


@rule("C2", "C", Severity.WARNING, fixable=True)
def c2_heading_spacing(doc: Document) -> list[Finding]:
    out = []
    for ln in _body_lines(doc):
        m = _MULTISPACE_HEADING_RE.match(ln.raw)
        if m:
            new = re.sub(r"^(#{1,6}) {2,}", r"\1 ", ln.raw)
            out.append(
                Finding(
                    "C2",
                    Severity.WARNING,
                    ln.number,
                    "multiple spaces after '#'",
                    fixable=True,
                    fix=Fix(line=ln.number, new_text=new),
                )
            )
    return out


@rule("C3", "C", Severity.WARNING)
def c3_heading_jump(doc: Document) -> list[Finding]:
    out = []
    prev_level = None
    for ln in doc.lines:
        if ln.in_code or ln.in_front_matter:
            continue
        level = heading_level(ln.raw)
        if level is None:
            continue
        if prev_level is not None and level > prev_level + 1:
            out.append(
                Finding("C3", Severity.WARNING, ln.number, f"heading level jumps from H{prev_level} to H{level}")
            )
        prev_level = level
    return out


@rule("C4", "C", Severity.WARNING, fixable=True)
def c4_trailing_whitespace(doc: Document) -> list[Finding]:
    out = []
    for ln in doc.lines:
        if ln.in_code or ln.in_front_matter:
            continue
        if ln.raw != ln.raw.rstrip():
            out.append(
                Finding(
                    "C4",
                    Severity.WARNING,
                    ln.number,
                    "trailing whitespace",
                    fixable=True,
                    fix=Fix(line=ln.number, new_text=ln.raw.rstrip()),
                )
            )
    return out


@rule("C5", "C", Severity.WARNING, fixable=True)
def c5_excess_blank_lines(doc: Document) -> list[Finding]:
    out = []
    run = 0
    for ln in doc.lines:
        is_blank = ln.raw.strip() == "" and not ln.in_code
        if is_blank:
            run += 1
            if run >= 3:  # keep the first two, delete the rest
                out.append(
                    Finding(
                        "C5",
                        Severity.WARNING,
                        ln.number,
                        "more than two consecutive blank lines",
                        fixable=True,
                        fix=Fix(line=ln.number, delete=True),
                    )
                )
        else:
            run = 0
    return out


@rule("C6", "C", Severity.WARNING, fixable=True)
def c6_tabs(doc: Document) -> list[Finding]:
    out = []
    for ln in doc.lines:
        if ln.in_code or ln.in_front_matter:
            continue
        if "\t" in ln.raw:
            out.append(
                Finding(
                    "C6",
                    Severity.WARNING,
                    ln.number,
                    "tab character",
                    fixable=True,
                    fix=Fix(line=ln.number, new_text=ln.raw.replace("\t", "    ")),
                )
            )
    return out


@rule("C7", "C", Severity.WARNING)
def c7_missing_heading(doc: Document) -> list[Finding]:
    for ln in doc.lines:
        if ln.in_code or ln.in_front_matter:
            continue
        if heading_level(ln.raw) is not None:
            return []
    start = (doc.front_matter_range[1] + 1) if doc.front_matter_range else 1
    return [Finding("C7", Severity.WARNING, start, "post has no headings")]
