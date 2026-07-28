"""Word counting for a rendered Quarto post page.

There is exactly one word count per post, and it is taken from the final
rendered HTML rather than from the Pandoc AST or Quarto's internal listing
calculation. Counting the rendered page is what keeps the post page and the
homepage listing from drifting apart: both displays are derived from this
single number.

What is counted, and why:

  - Prose and code inside ``<main id="quarto-document-content">``. Code is
    tallied like prose even though ``code-fold: true`` collapses it on load.
  - Math is *not* counted from its source. MathJax typesets in the browser, so
    the rendered HTML still carries raw LaTeX inside ``.math`` spans; tallying
    that inflates math-heavy posts (the bug this module replaces). Instead each
    equation is credited a fixed cost: a display equation reads as
    ``DISPLAY_EQUATION_WORDS`` words, an inline span as
    ``INLINE_EQUATION_WORDS``.
  - The title block, scripts, styles, and any previously injected
    ``.reading-time`` div are skipped, so re-running over an already-patched
    page yields the same count.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from html.parser import HTMLParser

WORDS_PER_MINUTE = 200
DISPLAY_EQUATION_WORDS = 8
INLINE_EQUATION_WORDS = 1

# The homepage listing is deliberately coarser than the post page: it rounds to
# the nearest multiple of LISTING_ROUND_TO so the two surfaces are read as
# different summaries of one number, not as two numbers that ought to match.
LISTING_ROUND_TO = 5
LISTING_MINIMUM = 5

CONTENT_ID = "quarto-document-content"

# Subtrees inside the content that carry no reader-visible prose.
SKIP_TAGS = frozenset({"script", "style", "noscript"})
SKIP_IDS = frozenset({"title-block-header"})
SKIP_CLASSES = frozenset({"reading-time"})

# Void elements never see an end tag, so they must not move the depth stack.
VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


@dataclass(frozen=True)
class ReadingTime:
    """One post's word count and the two displays derived from it."""

    prose_words: int
    display_equations: int
    inline_equations: int

    @property
    def words(self) -> int:
        """Total effective words, equations included at their fixed cost."""
        return (
            self.prose_words
            + self.display_equations * DISPLAY_EQUATION_WORDS
            + self.inline_equations * INLINE_EQUATION_WORDS
        )

    @property
    def minutes(self) -> float:
        return self.words / WORDS_PER_MINUTE

    @property
    def post_text(self) -> str:
        """Precise display for the post's own page, e.g. ``15.9 min read``."""
        return f"{max(0.1, self.minutes):.1f} min read"

    @property
    def listing_minutes(self) -> int:
        """Minutes rounded to the nearest LISTING_ROUND_TO, floored."""
        # Explicit half-up: round() is banker's rounding, which sends 12.5 to 10.
        rounded = math.floor(self.minutes / LISTING_ROUND_TO + 0.5) * LISTING_ROUND_TO
        return max(LISTING_MINIMUM, rounded)

    @property
    def listing_text(self) -> str:
        """Coarse display for the homepage listing card, e.g. ``15 min read``."""
        return f"{self.listing_minutes} min read"


class _ContentCounter(HTMLParser):
    """Tallies words in the document body of a rendered Quarto page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.prose_words = 0
        self.display_equations = 0
        self.inline_equations = 0
        self._stack: list[str] = []
        self._content_depth: int | None = None
        self._skip_depth: int | None = None
        self._finished = False

    @property
    def _counting(self) -> bool:
        return self._content_depth is not None and self._skip_depth is None

    def handle_startendtag(self, tag, attrs):  # <img/>, <br/> — no children
        return

    def handle_starttag(self, tag, attrs):
        if self._finished or tag in VOID_TAGS:
            return

        self._stack.append(tag)
        depth = len(self._stack)
        attrs_by_name = dict(attrs)

        if self._content_depth is None:
            if tag == "main" and attrs_by_name.get("id") == CONTENT_ID:
                self._content_depth = depth
            return

        if self._skip_depth is not None:
            return  # already inside a skipped subtree

        classes = (attrs_by_name.get("class") or "").split()
        if tag in SKIP_TAGS or attrs_by_name.get("id") in SKIP_IDS:
            self._skip_depth = depth
        elif SKIP_CLASSES.intersection(classes):
            self._skip_depth = depth
        elif "math" in classes:
            # Credit the equation, then skip its LaTeX source.
            if "display" in classes:
                self.display_equations += 1
            else:
                self.inline_equations += 1
            self._skip_depth = depth

    def handle_endtag(self, tag):
        if self._finished or tag in VOID_TAGS or tag not in self._stack:
            return

        # Pop to the matching open tag, tolerating unclosed elements.
        while self._stack:
            depth = len(self._stack)
            popped = self._stack.pop()
            if self._skip_depth is not None and depth <= self._skip_depth:
                self._skip_depth = None
            if self._content_depth is not None and depth <= self._content_depth:
                self._content_depth = None
                self._finished = True  # one body per page; stop counting
            if popped == tag:
                break

    def handle_data(self, data):
        if self._counting:
            self.prose_words += len(data.split())


def count_html(html: str) -> ReadingTime:
    """Count one rendered post page."""
    counter = _ContentCounter()
    counter.feed(html)
    counter.close()
    return ReadingTime(
        prose_words=counter.prose_words,
        display_equations=counter.display_equations,
        inline_equations=counter.inline_equations,
    )
