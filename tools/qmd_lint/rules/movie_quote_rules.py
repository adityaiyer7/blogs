"""Category Q — the ``[!moviequote]`` Obsidian callout -> the ``.movie-quote`` block.

A dedicated callout type for the running movie-quotes post. It does not map onto
one of Quarto's five native callout types the way N1 maps ``[!note]``/``[!tip]``/
etc. — a movie quote isn't an admonition, so it converts into a bespoke
``.movie-quote`` fenced div with its own layout, styled in
``blogposts/styles.css`` rather than borrowing the callout system's chrome.

The Obsidian callout title carries both the movie name and the date the quote
was seen, written ``<Movie> — YYYY-MM-DD``. Q1 parses that apart into a small
meta line (movie title + date) followed by the quote itself as an ordinary
Markdown blockquote; Q2 flags a title that doesn't match so it is never
silently mis-parsed.
"""

from __future__ import annotations

import html
import re

from ..config import MOVIE_QUOTE_OBSIDIAN_TYPE
from ..model import Finding, Fix, Severity, rule
from ..parser import Document

_TITLE_RE = re.compile(r"^(.+?)\s+—\s+(\d{4}-\d{2}-\d{2})$")


def _movie_quote_callouts(doc: Document):
    for c in doc.obsidian_callouts:
        if c.depth == 1 and c.ctype.lower() == MOVIE_QUOTE_OBSIDIAN_TYPE:
            yield c


def _build_div(movie: str, date: str) -> str:
    meta = (
        '<div class="movie-quote-meta">'
        f'<span class="movie-quote-title">{html.escape(movie)}</span>'
        f'<span class="movie-quote-date">{html.escape(date)}</span>'
        "</div>"
    )
    return "\n".join(["::: {.movie-quote}", meta, ""])


@rule("Q1", "Q", Severity.WARNING, fixable=True)
def q1_convert_movie_quote(doc: Document) -> list[Finding]:
    """Detect (and convert) top-level [!moviequote] callouts into .movie-quote divs."""
    out = []
    for c in _movie_quote_callouts(doc):
        m = _TITLE_RE.match(c.title)
        if not m:
            # Malformed title: reported here, detailed by Q2, never guessed at.
            out.append(
                Finding(
                    "Q1",
                    Severity.WARNING,
                    c.marker_line,
                    f"Obsidian callout [!{c.ctype}] -> .movie-quote (title malformed, not converted)",
                )
            )
            continue
        movie, date = m.group(1), m.group(2)
        body = [doc.line_text(n) for n in c.body_lines]
        block_lines = [_build_div(movie, date), *body, ":::"]
        fix = Fix(line=c.marker_line, new_text="\n".join(block_lines))
        # The original blockquote body lines are removed as part of the same fix.
        extra = [Fix(line=n, delete=True) for n in c.body_lines]
        out.append(
            Finding(
                "Q1",
                Severity.WARNING,
                c.marker_line,
                f"Obsidian callout [!{c.ctype}] -> .movie-quote ({movie} — {date})",
                fixable=True,
                fix=fix,
                extra_fixes=extra,
            )
        )
    return out


@rule("Q2", "Q", Severity.WARNING)
def q2_malformed_title(doc: Document) -> list[Finding]:
    out = []
    for c in _movie_quote_callouts(doc):
        if not _TITLE_RE.match(c.title):
            out.append(
                Finding(
                    "Q2",
                    Severity.WARNING,
                    c.marker_line,
                    f'[!{MOVIE_QUOTE_OBSIDIAN_TYPE}] title must be "<Movie> — YYYY-MM-DD" '
                    f"(got {c.title!r}) — convert by hand",
                )
            )
    return out
