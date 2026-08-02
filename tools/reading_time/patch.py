"""Idempotent patchers for the three artifacts that display reading time.

Every function here takes rendered content and returns rendered content, so
they can be unit-tested without Quarto and re-applied to already-patched output
without drift:

  - ``patch_post_page``   — ``docs/posts/<slug>/index.html``
  - ``patch_listing``     — ``docs/index.html`` (visible text + sort attributes)
  - ``patch_search_index``— ``docs/search.json`` (listing-card text used by search)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .count import ReadingTime

MIN_READ_RE = re.compile(r"\d+(?:\.\d+)? min read")

_POST_DIV_RE = re.compile(r'<div class="reading-time">.*?</div>', re.DOTALL)
_TITLE_BLOCK_RE = re.compile(r'<header id="title-block-header"[^>]*>')

_CARD_MARKER = '<div class="quarto-post '
_CARD_HREF_RE = re.compile(r'href="\.?/?posts/([^/"]+)/index\.html"')
_TIME_SORT_RE = re.compile(r'(data-listing-reading-time-sort=")[^"]*(")')
_WORD_SORT_RE = re.compile(r'(data-listing-word-count-sort=")[^"]*(")')
_LISTING_TIME_RE = re.compile(r'(<div class="listing-reading-time">)([^<]*)(</div>)')
_LISTING_DATE_RE = re.compile(r'<div class="listing-date">.*?</div>', re.DOTALL)


class PatchError(Exception):
    """Raised when an artifact does not have the shape we expect to patch."""


def post_div(text: str) -> str:
    return f'<div class="reading-time">{text}</div>'


def patch_post_page(html: str, text: str) -> str:
    """Set the ``.reading-time`` line on a post page.

    Replaces the div if a previous run left one; otherwise inserts it directly
    after the title block, which is where the retired Lua filter put it and
    what the existing `.reading-time` CSS is written against.
    """
    div = post_div(text)
    if _POST_DIV_RE.search(html):
        return _POST_DIV_RE.sub(lambda _: div, html, count=1)

    header = _TITLE_BLOCK_RE.search(html)
    if not header:
        raise PatchError("no <header id=\"title-block-header\"> to anchor against")

    close = html.find("</header>", header.end())
    if close == -1:
        raise PatchError("title block header is never closed")

    cut = close + len("</header>")
    return f"{html[:cut]}\n{div}\n{html[cut:]}"


def patch_listing(
    html: str, values: dict[str, "ReadingTime"]
) -> tuple[str, list[tuple[str, str | None]]]:
    """Rewrite listing cards from the values computed off the post pages.

    ``values`` maps post slug to a :class:`~tools.reading_time.count.ReadingTime`.
    Cards for posts we did not compute (e.g. a post that has never been
    rendered) are left untouched.

    Returns the patched HTML and the cards in document order as
    ``(slug, visible reading-time text or None)`` — the order `search.json`
    needs to line its listing text up with these cards.
    """
    starts = [m.start() for m in re.finditer(re.escape(_CARD_MARKER), html)]
    if not starts:
        return html, []

    bounds = list(zip(starts, starts[1:] + [len(html)]))
    out = [html[: bounds[0][0]]]
    cards: list[tuple[str, str | None]] = []

    for start, end in bounds:
        segment = html[start:end]
        href = _CARD_HREF_RE.search(segment)
        slug = href.group(1) if href else None
        reading = values.get(slug) if slug else None

        if reading is not None:
            segment = _TIME_SORT_RE.sub(
                lambda m: f"{m.group(1)}{reading.listing_minutes}{m.group(2)}", segment
            )
            segment = _WORD_SORT_RE.sub(
                lambda m: f"{m.group(1)}{reading.words}{m.group(2)}", segment
            )
            segment = _set_card_text(segment, reading.listing_text)

        shown = _LISTING_TIME_RE.search(segment)
        cards.append((slug or "", shown.group(2) if shown else None))
        out.append(segment)

    return "".join(out), cards


def _set_card_text(segment: str, text: str) -> str:
    """Replace the card's visible reading-time text, inserting it if absent."""
    if _LISTING_TIME_RE.search(segment):
        return _LISTING_TIME_RE.sub(lambda m: f"{m.group(1)}{text}{m.group(3)}", segment)

    date = _LISTING_DATE_RE.search(segment)
    if not date:
        return segment  # no metadata block to hang it off; leave the card alone

    div = f'<div class="listing-reading-time">{text}</div>'
    return f"{segment[: date.end()]}\n{div}{segment[date.end() :]}"


def patch_search_index(entries: list[dict], texts: list[str]) -> list[dict]:
    """Rewrite the reading times embedded in the listing page's search text.

    ``texts`` is the listing cards' reading-time text in document order. The
    search entry for the listing page flattens those cards into one blob, so
    the *i*-th ``N min read`` in the blob belongs to the *i*-th card. A blob
    with no reading times at all is left alone (nothing to patch); a blob whose
    count disagrees with the cards is an unexpected shape and raises rather
    than guessing which number belongs where.
    """
    for entry in entries:
        if entry.get("objectID") != "index.html":
            continue

        text = entry.get("text")
        if not isinstance(text, str):
            continue

        found = MIN_READ_RE.findall(text)
        if not found:
            continue
        if len(found) != len(texts):
            raise PatchError(
                f"search.json lists {len(found)} reading times but the listing has {len(texts)} cards"
            )

        remaining = iter(texts)
        entry["text"] = MIN_READ_RE.sub(lambda _: next(remaining), text)

    return entries
