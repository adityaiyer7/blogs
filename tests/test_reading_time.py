"""Tests for the post-render reading-time tool.

Quarto is not installed in CI for these tests, so they run against fixture HTML
shaped like real rendered output: the post-page header comes from
blogposts/docs/posts/*/index.html, the listing card from the published
homepage (sort attributes plus a `.listing-reading-time` div inside `.metadata`).
"""

from __future__ import annotations

import json

import pytest

from tools.reading_time.count import (
    DISPLAY_EQUATION_WORDS,
    INLINE_EQUATION_WORDS,
    WORDS_PER_MINUTE,
    ReadingTime,
    count_html,
)
from tools.reading_time.patch import (
    PatchError,
    patch_listing,
    patch_post_page,
    patch_search_index,
)


def post_page(body: str, reading_time: str | None = None) -> str:
    """A rendered post page, optionally already carrying a reading-time div."""
    injected = f'\n<div class="reading-time">{reading_time}</div>\n' if reading_time else ""
    return f"""<!DOCTYPE html>
<html><head><title>T</title><script src="site_libs/quarto-nav/quarto-nav.js"></script></head>
<body>
<nav id="TOC"><ul><li><a href="#intro">Introduction to the sidebar table of contents</a></li></ul></nav>
<main class="content" id="quarto-document-content">

<header id="title-block-header" class="quarto-title-block default">
<div class="quarto-title"><h1 class="title">A Walkthrough of Attention</h1></div>
<div><div class="description">A GPT-2 style walkthrough of causal self-attention.</div></div>
<div class="quarto-title-meta">
<div><div class="quarto-title-meta-heading">Published</div>
<div class="quarto-title-meta-contents"><p class="date">June 5, 2026</p></div></div>
</div>
</header>
{injected}
{body}
<script>window.goatcounter = {{ path: function(p) {{ return location.pathname; }} }};</script>
</main>
</body></html>"""


def card(slug: str, minutes: int = 12, words: int = 2246, reading_time: str | None = "12 min read") -> str:
    """A homepage listing card, matching Quarto's default listing markup."""
    time_div = f'\n<div class="listing-reading-time">{reading_time}</div>' if reading_time else ""
    return f"""<div class="quarto-post image-right" data-index="0" data-categories="SW50" \
data-listing-date-sort="1781308800000" data-listing-file-modified-sort="1784962701327" \
data-listing-reading-time-sort="{minutes}" data-listing-word-count-sort="{words}">
<div class="body">
<h3 class="no-anchor listing-title">
<a href="./posts/{slug}/index.html" class="no-external">Some Title</a>
</h3>
</div>
<div class="metadata">
<a href="./posts/{slug}/index.html" class="no-external">
<div class="listing-date">
Jun 13, 2026
</div>{time_div}
</a>
</div>
</div>"""


def listing(*cards: str) -> str:
    return (
        '<main class="content" id="quarto-document-content">\n'
        '<div class="quarto-listing quarto-listing-container-default" id="listing-listing">\n'
        '<div class="list quarto-listing-default">\n' + "\n".join(cards) + "\n</div>\n</div>\n</main>"
    )


# ── Counting ─────────────────────────────────────────────────────────────


def test_counts_prose_in_the_body_only():
    reading = count_html(post_page("<p>one two three four five</p>"))
    assert reading.prose_words == 5  # title block, TOC, and scripts excluded


def test_counts_code_like_prose():
    body = "<p>one two</p><pre><code>def f(x):\n    return x + 1</code></pre>"
    assert count_html(post_page(body)).prose_words == 2 + 6


def test_math_is_credited_not_tallied_from_latex():
    body = (
        '<p>see</p>'
        '<span class="math display">\\[ \\frac{\\partial \\mathcal{L}}{\\partial \\theta} = 0 \\]</span>'
        '<span class="math inline">\\(x_t\\)</span>'
    )
    reading = count_html(post_page(body))
    assert reading.prose_words == 1  # no LaTeX source counted
    assert (reading.display_equations, reading.inline_equations) == (1, 1)
    assert reading.words == 1 + DISPLAY_EQUATION_WORDS + INLINE_EQUATION_WORDS


def test_existing_reading_time_div_is_not_counted():
    body = "<p>one two three</p>"
    assert count_html(post_page(body, "9.9 min read")) == count_html(post_page(body))


def test_content_outside_main_is_ignored():
    html = post_page("<p>one two</p>") + "<footer><p>lots of extra footer words here</p></footer>"
    assert count_html(html).prose_words == 2


# ── Deriving the two displays ────────────────────────────────────────────


def reading_of(minutes: float) -> ReadingTime:
    return ReadingTime(prose_words=round(minutes * WORDS_PER_MINUTE), display_equations=0, inline_equations=0)


def test_post_page_text_is_precise():
    assert reading_of(15.9).post_text == "15.9 min read"


@pytest.mark.parametrize(
    "minutes,expected",
    [(12.4, 10), (12.5, 15), (15.9, 15), (17.5, 20), (0.2, 5), (2.4, 5)],
)
def test_listing_rounds_half_up_to_five_with_a_floor(minutes, expected):
    assert reading_of(minutes).listing_minutes == expected


def test_empty_post_still_reads_as_a_tenth_of_a_minute():
    assert ReadingTime(0, 0, 0).post_text == "0.1 min read"


# ── Patching the post page ───────────────────────────────────────────────


def test_inserts_the_div_after_the_title_block():
    patched = patch_post_page(post_page("<p>body</p>"), "15.9 min read")
    assert '</header>\n<div class="reading-time">15.9 min read</div>' in patched


def test_replaces_an_existing_div_and_is_idempotent():
    once = patch_post_page(post_page("<p>body</p>", "12.0 min read"), "15.9 min read")
    assert once.count('class="reading-time"') == 1
    assert "12.0 min read" not in once
    assert patch_post_page(once, "15.9 min read") == once


def test_post_page_without_a_title_block_is_reported():
    with pytest.raises(PatchError):
        patch_post_page("<main id='quarto-document-content'><p>hi</p></main>", "1.0 min read")


# ── Patching the listing ─────────────────────────────────────────────────


def test_listing_card_text_and_sort_attributes_follow_the_post():
    html = listing(card("attention-mechanism"), card("hundred-day-retrospective"))
    values = {"attention-mechanism": ReadingTime(prose_words=3000, display_equations=0, inline_equations=0)}

    patched, cards = patch_listing(html, values)

    assert 'data-listing-reading-time-sort="15"' in patched
    assert 'data-listing-word-count-sort="3000"' in patched
    assert '<div class="listing-reading-time">15 min read</div>' in patched
    assert cards == [("attention-mechanism", "15 min read"), ("hundred-day-retrospective", "12 min read")]
    assert patch_listing(patched, values)[0] == patched


def test_listing_card_gets_a_reading_time_div_when_quarto_omitted_it():
    html = listing(card("attention-mechanism", reading_time=None))
    values = {"attention-mechanism": ReadingTime(prose_words=2000, display_equations=0, inline_equations=0)}

    patched, cards = patch_listing(html, values)

    assert '<div class="listing-reading-time">10 min read</div>' in patched
    assert cards == [("attention-mechanism", "10 min read")]


def test_unknown_posts_keep_their_card():
    html = listing(card("never-rendered"))
    patched, _ = patch_listing(html, {})
    assert patched == html


# ── Patching the search index ────────────────────────────────────────────


def search_index(listing_text: str) -> list[dict]:
    return [
        {"objectID": "index.html", "href": "index.html", "text": listing_text},
        {"objectID": "posts/a/index.html", "href": "posts/a/index.html", "text": "body text"},
    ]


def test_search_text_is_patched_positionally():
    entries = search_index("First\n\n12 min read\n\nSecond\n\n41 min read")
    patched = patch_search_index(entries, ["15 min read", "40 min read"])
    assert patched[0]["text"] == "First\n\n15 min read\n\nSecond\n\n40 min read"
    assert patched[1]["text"] == "body text"


def test_search_index_without_reading_times_is_left_alone():
    entries = search_index("First\n\nSecond")
    assert patch_search_index(entries, ["15 min read"])[0]["text"] == "First\n\nSecond"


def test_mismatched_counts_raise_rather_than_guess():
    entries = search_index("First\n\n12 min read")
    with pytest.raises(PatchError):
        patch_search_index(entries, ["15 min read", "40 min read"])


def test_search_index_round_trips_quarto_formatting():
    entries = patch_search_index(search_index("A\n\n12 min read"), ["15 min read"])
    dumped = json.dumps(entries, indent=2, ensure_ascii=False)
    assert json.loads(dumped)[0]["text"] == "A\n\n15 min read"
