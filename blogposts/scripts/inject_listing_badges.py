#!/usr/bin/env python3
"""Annotate Quarto listing cards with pin badges and series labels.

*Ordering* is native Quarto in both cases: the homepage listings in index.qmd
sort on `pinned`/`pin-order` (defaults from _pin_defaults.yml), and each series
landing page sorts on `series-order`. Ordering therefore needs no help here.

The labels do. Quarto's built-in listing renders a fixed set of fields and
silently ignores any custom one, so neither `pinned` nor `series` ever reaches
the card markup -- they are registered for the search index and nothing else.
The documented way around that is a custom EJS template, but a template owns
the *whole* card: Quarto stops emitting `quarto-post` wrappers and their
`data-categories` payload, so the category filter, the search columns, and the
reading-time field would all have to be reimplemented and then kept in step
with Quarto's listing JS -- and CI installs whatever Quarto release is current.

Injecting after the fact keeps every byte of Quarto's own markup and adds one
element per annotation. The coupling is limited to the `quarto-post` wrapper
and the post link inside it.

Both annotations share this one pass deliberately. Two scripts would mean two
copies of that coupling and two places to fix when Quarto's card markup moves.
See docs/document_pins.md and docs/design/series.md.
"""

from __future__ import annotations

import html
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = PROJECT_DIR.parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from tools.series_metadata import parse_series_metadata


POSTS_DIR = PROJECT_DIR / "posts"
# Quarto hands post-render scripts the real output directory. Fall back to the
# configured one so the script is still runnable by hand.
OUTPUT_DIR = PROJECT_DIR / os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "docs")

BADGE_CLASS = "listing-pinned-badge"
BADGE_HTML = f'<div class="{BADGE_CLASS}">Pinned</div>\n'
SERIES_CLASS = "listing-series-label"
EMPTY_CLASS = "series-empty-state"
EMPTY_HTML = (
    f'<p class="{EMPTY_CLASS}">'
    "No posts in this series have been published yet.</p>\n"
)
SERIES_LISTING_ID = "listing-series-posts"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
PINNED_RE = re.compile(r"^pinned:\s*(true|false)\s*(?:#.*)?$", re.MULTILINE)
# Cards are emitted as <div class="quarto-post ..."> ... and the post they link
# to is the first href inside. Matching the opening tag plus that href is
# enough to identify the card without parsing the whole document.
CARD_RE = re.compile(
    r'<div class="quarto-post[^"]*"[^>]*>\s*(?:<div class="thumbnail">.*?</div>\s*)?'
    r'<div class="body">\s*',
    re.DOTALL,
)
# The leading group is the path prefix the page uses to reach posts/ -- "./" on
# the homepage, "../../" from a series page. Reusing it keeps injected links
# correct at any depth (see series_label_html).
HREF_RE = re.compile(r'href="([^"]*?)posts/([^/"]+)/index\.html"')
EMPTY_SERIES_LISTING_RE = re.compile(
    rf'(<div(?=[^>]*\bid="{SERIES_LISTING_ID}")[^>]*>\s*'
    r'<div class="list quarto-listing-default">)\s*(</div>)',
    re.DOTALL,
)
SERIES_LISTING_START_RE = re.compile(
    rf'<div(?=[^>]*\bid="{SERIES_LISTING_ID}")[^>]*>\s*'
    r'<div class="list quarto-listing-default">',
    re.DOTALL,
)
LISTING_NO_MATCHING_RE = re.compile(r'<div class="listing-no-matching\b')


@dataclass(frozen=True)
class PostMeta:
    """The listing-relevant front matter of a single post."""

    pinned: bool = False
    series_id: str | None = None
    series_title: str | None = None
    series_order: int | None = None

    @property
    def has_complete_series(self) -> bool:
        return (
            self.series_id is not None
            and self.series_title is not None
            and self.series_order is not None
        )


def post_metadata() -> dict[str, PostMeta]:
    """Map each post slug to the front-matter fields the cards care about."""
    meta: dict[str, PostMeta] = {}
    errors: list[str] = []
    for post_path in sorted(POSTS_DIR.rglob("index.qmd")):
        front_matter = FRONT_MATTER_RE.match(post_path.read_text(encoding="utf-8"))
        if front_matter is None:
            continue
        block = front_matter.group(1)

        pinned = PINNED_RE.search(block)
        series, series_errors = parse_series_metadata(block)
        errors.extend(f"{post_path}: {error}" for error in series_errors)

        meta[post_path.parent.name] = PostMeta(
            pinned=bool(pinned) and pinned.group(1) == "true",
            series_id=series.series_id if series else None,
            series_title=series.title if series else None,
            series_order=series.order if series else None,
        )

    if errors:
        raise SystemExit(
            "inject_listing_badges: invalid series metadata:\n  "
            + "\n  ".join(errors)
        )
    return meta


def series_label_html(prefix: str, series_id: str, series_title: str) -> str:
    """The linked series label for a card whose post link starts with `prefix`.

    The card's own href is `<prefix>posts/<slug>/index.html`, so reusing that
    prefix produces a link that is correct at any page depth and under the
    GitHub Pages subpath, without this script having to know either.
    """
    href = f"{prefix}series/{series_id}/index.html"
    return (
        f'<div class="{SERIES_CLASS}">'
        f'<a href="{html.escape(href, quote=True)}">'
        f"Series: {html.escape(series_title)}</a></div>\n"
    )


def annotate_page(
    html_text: str, meta: dict[str, PostMeta], on_series_page: bool = False
) -> tuple[str, int]:
    """Insert the pin badge and series label into each card that wants them.

    `on_series_page` suppresses the series label: every card on a series
    landing page belongs to that series, so the label would be pure repetition.
    """
    out: list[str] = []
    cursor = 0
    added = 0
    cards = 0

    for card in CARD_RE.finditer(html_text):
        cards += 1
        # The card's own href is the first one after its opening tag.
        href = HREF_RE.search(html_text, card.end(), card.end() + 2000)
        out.append(html_text[cursor : card.end()])
        cursor = card.end()
        if href is None:
            continue
        post = meta.get(href.group(2))
        if post is None:
            continue

        # The badge goes first, so a card carrying both keeps "Pinned" on top.
        insertions = []
        if post.pinned:
            insertions.append(BADGE_HTML)
        # Invalid partial metadata aborts before this pass; requiring the full
        # typed set here keeps direct callers safe as well.
        if not on_series_page and post.has_complete_series:
            assert post.series_id is not None and post.series_title is not None
            insertions.append(series_label_html(href.group(1), post.series_id, post.series_title))

        for markup in insertions:
            # Guard against double-annotating if a page is processed twice.
            if markup in html_text[card.end() : card.end() + 500]:
                continue
            out.append(markup)
            added += 1

    out.append(html_text[cursor:])

    # A listing page that yielded no cards means Quarto's markup moved and the
    # patterns above no longer match. Fail loudly rather than quietly shipping
    # a page with every annotation missing.
    if cards == 0 and 'class="quarto-post' in html_text:
        raise SystemExit(
            "inject_listing_badges: found quarto-post markup but matched no cards; "
            "Quarto's listing output has changed and CARD_RE needs updating."
        )

    return "".join(out), added


def add_series_empty_state(html_text: str) -> tuple[str, bool]:
    """Add the empty-series message to an empty `series-posts` listing."""
    if SERIES_LISTING_ID not in html_text:
        return html_text, False
    if EMPTY_CLASS in html_text:
        return html_text, False

    match = EMPTY_SERIES_LISTING_RE.search(html_text)
    if match is not None:
        updated = html_text[: match.start()] + match.group(1) + "\n" + EMPTY_HTML
        updated += match.group(2) + html_text[match.end() :]
        return updated, True

    listing_start = SERIES_LISTING_START_RE.search(html_text)
    no_matching = (
        LISTING_NO_MATCHING_RE.search(html_text, listing_start.end())
        if listing_start is not None
        else None
    )
    if (
        listing_start is not None
        and no_matching is not None
        and 'class="quarto-post' in html_text[listing_start.end() : no_matching.start()]
    ):
        return html_text, False

    raise SystemExit(
        "inject_listing_badges: found the series-posts listing but could not "
        "match its empty markup; Quarto's listing output has changed."
    )


def is_series_page(page: Path) -> bool:
    """True for output pages living under a `series/` directory."""
    return "series" in page.relative_to(OUTPUT_DIR).parts[:-1]


def main() -> None:
    meta = post_metadata()
    total = 0
    empty_states = 0
    for page in sorted(OUTPUT_DIR.rglob("*.html")):
        html_text = page.read_text(encoding="utf-8")
        if "quarto-listing" not in html_text:
            continue
        series_page = is_series_page(page)
        updated, added = annotate_page(html_text, meta, series_page)
        empty_added = False
        if series_page:
            updated, empty_added = add_series_empty_state(updated)
        if added or empty_added:
            page.write_text(updated, encoding="utf-8")
            total += added
            empty_states += int(empty_added)

    pinned = sorted(slug for slug, post in meta.items() if post.pinned)
    in_series = sorted(slug for slug, post in meta.items() if post.series_id)
    if pinned:
        print(f"Pinned posts: {', '.join(pinned)}", file=sys.stderr)
    if in_series:
        print(f"Series posts: {', '.join(in_series)}", file=sys.stderr)
    if total:
        print(
            f"Injected {total} listing annotation{'' if total == 1 else 's'}",
            file=sys.stderr,
        )
    if empty_states:
        print(
            f"Injected {empty_states} empty series state"
            f"{'' if empty_states == 1 else 's'}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
