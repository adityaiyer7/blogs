"""Category N — Obsidian callouts → Quarto callouts.

Obsidian writes callouts as blockquotes (``> [!note] Title`` + ``> body``),
which Quarto does not render. The canonical Quarto form is a fenced div
``::: {.callout-note} … :::``. Because the ``> [!type]`` form is unambiguous,
N1 converts it automatically (carrying the title and fold state). The remaining
rules check the well-formedness of callouts that are already in Quarto syntax.
"""

from __future__ import annotations

from ..config import OBSIDIAN_TO_QUARTO, QUARTO_CALLOUT_TYPES
from ..model import Finding, Fix, Severity, rule
from ..parser import Document, ObsCallout


def _strip_blockquote(text: str) -> str:
    """Remove one level of leading '>' (and a following space) from a body line."""
    stripped = text.lstrip()
    if stripped.startswith(">"):
        stripped = stripped[1:]
        if stripped.startswith(" "):
            stripped = stripped[1:]
    return stripped


def _build_div(callout: ObsCallout, quarto_type: str) -> str:
    attrs = f".callout-{quarto_type}"
    if callout.title:
        attrs += f' title="{callout.title}"'
    if callout.fold == "-":
        attrs += ' collapse="true"'
    elif callout.fold == "+":
        attrs += ' collapse="false"'
    lines = [f"::: {{{attrs}}}"]
    return "\n".join(lines)


@rule("N1", "N", Severity.WARNING, fixable=True)
def n1_convert_obsidian_callout(doc: Document) -> list[Finding]:
    """Detect (and convert) top-level Obsidian callouts to Quarto callout divs."""
    out = []
    for c in doc.obsidian_callouts:
        if c.depth != 1:
            continue  # nested callouts handled by N5
        quarto_type = OBSIDIAN_TO_QUARTO.get(c.ctype.lower())
        target = f"::: {{.callout-{quarto_type}}}" if quarto_type else "a Quarto callout"
        msg = f"Obsidian callout [!{c.ctype}] -> {target}"
        if quarto_type is None:
            # Unmapped type: report but don't guess a conversion (see N4).
            out.append(Finding("N1", Severity.WARNING, c.marker_line, msg, fixable=False))
            continue
        body = [_strip_blockquote(doc.line_text(n)) for n in c.body_lines]
        block_lines = [_build_div(c, quarto_type), *body, ":::"]
        fix = Fix(line=c.marker_line, new_text="\n".join(block_lines))
        # The original blockquote body lines are removed as part of the same fix.
        extra = [Fix(line=n, delete=True) for n in c.body_lines]
        out.append(Finding("N1", Severity.WARNING, c.marker_line, msg, fixable=True, fix=fix, extra_fixes=extra))
    return out


@rule("N4", "N", Severity.WARNING)
def n4_unknown_obsidian_type(doc: Document) -> list[Finding]:
    out = []
    for c in doc.obsidian_callouts:
        if c.ctype.lower() not in OBSIDIAN_TO_QUARTO:
            out.append(
                Finding(
                    "N4",
                    Severity.WARNING,
                    c.marker_line,
                    f"Obsidian callout type [!{c.ctype}] has no Quarto mapping — convert by hand",
                )
            )
    return out


@rule("N5", "N", Severity.WARNING)
def n5_nested_callout(doc: Document) -> list[Finding]:
    out = []
    for c in doc.obsidian_callouts:
        if c.depth > 1:
            out.append(
                Finding("N5", Severity.WARNING, c.marker_line, "nested Obsidian callout — convert manually")
            )
    return out


@rule("N6", "N", Severity.ERROR)
def n6_unclosed_callout(doc: Document) -> list[Finding]:
    out = []
    for c in doc.unclosed_callouts:
        out.append(Finding("N6", Severity.ERROR, c.open_line, "callout div ::: is never closed"))
    return out


@rule("N7", "N", Severity.WARNING)
def n7_fence_length(doc: Document) -> list[Finding]:
    out = []
    for c in doc.callouts:
        if c.close_len is not None and c.close_len != c.open_len:
            out.append(
                Finding(
                    "N7",
                    Severity.WARNING,
                    c.close_line or c.open_line,
                    f"callout fence length mismatch (opened with {c.open_len}, closed with {c.close_len})",
                )
            )
    return out


@rule("N8", "N", Severity.WARNING)
def n8_unknown_quarto_type(doc: Document) -> list[Finding]:
    out = []
    for c in doc.callouts:
        if c.ctype is not None and c.ctype not in QUARTO_CALLOUT_TYPES:
            out.append(
                Finding("N8", Severity.WARNING, c.open_line, f"unknown Quarto callout type: .callout-{c.ctype}")
            )
    return out


@rule("N9", "N", Severity.WARNING, fixable=True)
def n9_blank_around_callout(doc: Document) -> list[Finding]:
    out = []
    for c in doc.callouts:
        before = c.open_line - 1
        if before >= 1 and doc.line_text(before).strip() != "":
            out.append(
                Finding(
                    "N9",
                    Severity.WARNING,
                    c.open_line,
                    "no blank line before callout",
                    fixable=True,
                    fix=Fix(line=c.open_line, insert_before=""),
                )
            )
        if c.close_line is not None:
            after = c.close_line + 1
            if after <= len(doc.lines) and doc.line_text(after).strip() != "":
                out.append(
                    Finding(
                        "N9",
                        Severity.WARNING,
                        c.close_line,
                        "no blank line after callout",
                        fixable=True,
                        fix=Fix(line=after, insert_before=""),
                    )
                )
    return out
