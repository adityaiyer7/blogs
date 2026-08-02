"""Single source of truth for blog post reading times.

Reading time used to be computed twice — once by Quarto for the homepage
listing, once by a Pandoc filter for each post page — and the two counts could
disagree. This package computes it once, from the rendered HTML, and writes
that one number into every artifact that shows it.
"""

from .count import ReadingTime, count_html

__all__ = ["ReadingTime", "count_html"]
