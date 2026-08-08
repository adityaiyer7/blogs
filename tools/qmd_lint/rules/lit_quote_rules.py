"""Category Q — literature-quote Obsidian callouts -> the ``.lit-quote`` block.

A running log of quoted lines worth remembering — from a movie, a book, a
poem, a song — gets one shared block, distinguished only by a small kind
badge. The callout *type* selects the kind (``[!moviequote]``, ``[!bookquote]``,
``[!poemquote]``, ``[!songquote]`` — see ``config.LITERATURE_QUOTE_TYPES``);
none of them map onto one of Quarto's five native callout types the way N1
maps ``[!note]``/``[!tip]``/etc. — a quote isn't an admonition, so it converts
into a bespoke ``.lit-quote`` fenced div with its own layout, styled in
``blogposts/styles.css`` rather than borrowing the callout system's chrome.

The Obsidian callout title carries both the source title and the date the
quote was noted, written ``<Title> — YYYY-MM-DD``. Q1 parses that apart into a
small meta line (kind badge + source title + date) followed by the quote
itself as an ordinary Markdown blockquote; Q2 flags a title that doesn't match
so it is never silently mis-parsed.
"""

from __future__ import annotations

import html
import re

from ..config import LITERATURE_QUOTE_TYPES
from ..model import Finding, Fix, Severity, rule
from ..parser import Document

_TITLE_RE = re.compile(r"^(.+?)\s+—\s+(\d{4}-\d{2}-\d{2})$")


def _lit_quote_callouts(doc: Document):
    for c in doc.obsidian_callouts:
        if c.depth == 1 and c.ctype.lower() in LITERATURE_QUOTE_TYPES:
            yield c


def _build_div(kind: str, source: str, date: str) -> str:
    meta = (
        '<div class="lit-quote-meta">'
        f'<span class="lit-quote-kind">{html.escape(kind)}</span>'
        f'<span class="lit-quote-source">{html.escape(source)}</span>'
        f'<span class="lit-quote-date">{html.escape(date)}</span>'
        "</div>"
    )
    return "\n".join(["::: {.lit-quote}", meta, ""])


@rule("Q1", "Q", Severity.WARNING, fixable=True)
def q1_convert_lit_quote(doc: Document) -> list[Finding]:
    """Detect (and convert) top-level literature-quote callouts into .lit-quote divs."""
    out = []
    for c in _lit_quote_callouts(doc):
        kind = LITERATURE_QUOTE_TYPES[c.ctype.lower()]
        m = _TITLE_RE.match(c.title)
        if not m:
            # Malformed title: reported here, detailed by Q2, never guessed at.
            out.append(
                Finding(
                    "Q1",
                    Severity.WARNING,
                    c.marker_line,
                    f"Obsidian callout [!{c.ctype}] -> .lit-quote (title malformed, not converted)",
                )
            )
            continue
        source, date = m.group(1), m.group(2)
        body = [doc.line_text(n) for n in c.body_lines]
        block_lines = [_build_div(kind, source, date), *body, ":::"]
        fix = Fix(line=c.marker_line, new_text="\n".join(block_lines))
        # The original blockquote body lines are removed as part of the same fix.
        extra = [Fix(line=n, delete=True) for n in c.body_lines]
        out.append(
            Finding(
                "Q1",
                Severity.WARNING,
                c.marker_line,
                f"Obsidian callout [!{c.ctype}] -> .lit-quote ({kind}: {source} — {date})",
                fixable=True,
                fix=fix,
                extra_fixes=extra,
            )
        )
    return out


@rule("Q2", "Q", Severity.WARNING)
def q2_malformed_title(doc: Document) -> list[Finding]:
    out = []
    for c in _lit_quote_callouts(doc):
        if not _TITLE_RE.match(c.title):
            out.append(
                Finding(
                    "Q2",
                    Severity.WARNING,
                    c.marker_line,
                    f'[!{c.ctype}] title must be "<title> — YYYY-MM-DD" '
                    f"(got {c.title!r}) — convert by hand",
                )
            )
    return out
