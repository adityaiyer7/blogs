#!/usr/bin/env python3
"""Add a "Pinned" badge to the listing cards of pinned posts.

Pin *ordering* is native Quarto: the listings in index.qmd sort on `pinned`
and `pin-order`, with defaults supplied project-wide by _pin_defaults.yml.
Ordering therefore needs no help from this script.

The badge does. Quarto's built-in listing renders a fixed set of fields and
silently ignores any custom one, so `pinned` never reaches the card markup --
it is registered for the search index and nothing else. The documented way
around that is a custom EJS template, but a template owns the *whole* card:
Quarto stops emitting `quarto-post` wrappers and their `data-categories`
payload, so the category filter, the search columns, and the reading-time
field would all have to be reimplemented and then kept in step with Quarto's
listing JS -- and CI installs whatever Quarto release is current.

Injecting the badge after the fact keeps every byte of Quarto's own markup and
adds one element per pinned card. The coupling is limited to the
`quarto-post` wrapper and the post link inside it. See docs/document_pins.md.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = PROJECT_DIR / "posts"
# Quarto hands post-render scripts the real output directory. Fall back to the
# configured one so the script is still runnable by hand.
OUTPUT_DIR = PROJECT_DIR / os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "docs")

BADGE_CLASS = "listing-pinned-badge"
BADGE_HTML = f'<div class="{BADGE_CLASS}">Pinned</div>\n'

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
HREF_RE = re.compile(r'href="[^"]*?posts/([^/"]+)/index\.html"')


def pinned_slugs() -> set[str]:
    """Slugs of every post whose front matter opts into pinning."""
    slugs: set[str] = set()
    for post_path in sorted(POSTS_DIR.rglob("index.qmd")):
        front_matter = FRONT_MATTER_RE.match(post_path.read_text(encoding="utf-8"))
        if front_matter is None:
            continue
        match = PINNED_RE.search(front_matter.group(1))
        if match and match.group(1) == "true":
            slugs.add(post_path.parent.name)
    return slugs


def badge_page(html: str, slugs: set[str]) -> tuple[str, int]:
    """Insert the badge into each card belonging to a pinned post."""
    out: list[str] = []
    cursor = 0
    added = 0
    cards = 0

    for card in CARD_RE.finditer(html):
        cards += 1
        # The card's own href is the first one after its opening tag.
        href = HREF_RE.search(html, card.end(), card.end() + 2000)
        out.append(html[cursor : card.end()])
        cursor = card.end()
        if href is None or href.group(1) not in slugs:
            continue
        # Guard against double-badging if a page is processed twice.
        if html.startswith(BADGE_HTML, card.end()):
            continue
        out.append(BADGE_HTML)
        added += 1

    out.append(html[cursor:])

    # A listing page that yielded no cards means Quarto's markup moved and the
    # patterns above no longer match. Fail loudly rather than quietly shipping
    # a page with every badge missing.
    if cards == 0 and 'class="quarto-post' in html:
        raise SystemExit(
            "inject_pin_badges: found quarto-post markup but matched no cards; "
            "Quarto's listing output has changed and CARD_RE needs updating."
        )

    return "".join(out), added


def main() -> None:
    slugs = pinned_slugs()
    total = 0
    for page in sorted(OUTPUT_DIR.rglob("*.html")):
        html = page.read_text(encoding="utf-8")
        if "quarto-listing" not in html:
            continue
        updated, added = badge_page(html, slugs)
        if added:
            page.write_text(updated, encoding="utf-8")
            total += added

    if slugs:
        print(
            f"Pinned posts: {', '.join(sorted(slugs))} "
            f"({total} listing badge{'' if total == 1 else 's'})",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
