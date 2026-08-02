"""Command line entry point: recompute reading time across the rendered site.

Run after `quarto render` (the project's `post-render` hook does this
automatically) or by hand via `./update_reading_time.sh`.

Every dated post is recomputed on every run rather than tracking state, which
keeps single-post renders self-healing: rendering one post still refreshes that
post's card on the homepage, even though Quarto did not rewrite `docs/index.html`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.qmd_lint.parser import parse

from .count import ReadingTime, count_html
from .patch import PatchError, patch_listing, patch_post_page, patch_search_index

REPO_ROOT = Path(__file__).resolve().parents[2]


def _dated_posts(posts_dir: Path, slugs: list[str]) -> list[str]:
    """Post slugs that carry a front-matter `date`, in alphabetical order.

    The `date` gate is the one the retired Lua filter used: standalone pages
    (About, Reading Group) carry no date and never show a reading time.
    """
    found = []
    for source in sorted(posts_dir.glob("*/index.qmd")):
        slug = source.parent.name
        if slugs and slug not in slugs:
            continue
        front_matter = parse(source).front_matter or {}
        if front_matter.get("date"):
            found.append(slug)
    return found


def _write(path: Path, content: str, check: bool) -> bool:
    """Write `content` unless unchanged (or `check`). True if it differed."""
    if path.read_text(encoding="utf-8") == content:
        return False
    if not check:
        path.write_text(content, encoding="utf-8")
    return True


def run(argv: list[str] | None = None, repo_root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(
        prog="update_reading_time",
        description="Recompute reading time from rendered HTML and patch the site.",
    )
    parser.add_argument("slugs", nargs="*", help="only these posts (default: all)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what would change and exit non-zero; write nothing",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="print each post")
    args = parser.parse_args(argv)

    posts_dir = repo_root / "blogposts" / "posts"
    docs_dir = repo_root / "blogposts" / "docs"
    if not docs_dir.is_dir():
        print(f"reading time: no rendered site at {docs_dir}, nothing to do")
        return 0

    values: dict[str, ReadingTime] = {}
    changed: list[str] = []
    warnings: list[str] = []

    for slug in _dated_posts(posts_dir, args.slugs):
        page = docs_dir / "posts" / slug / "index.html"
        if not page.is_file():
            continue  # not rendered yet

        html = page.read_text(encoding="utf-8")
        reading = count_html(html)
        values[slug] = reading

        try:
            patched = patch_post_page(html, reading.post_text)
        except PatchError as exc:
            warnings.append(f"{slug}: {exc}")
            continue

        if _write(page, patched, args.check):
            changed.append(f"posts/{slug}/index.html")
        if args.verbose:
            print(
                f"  {slug}: {reading.words} words "
                f"({reading.display_equations} display / {reading.inline_equations} inline equations) "
                f"→ {reading.post_text} · listing {reading.listing_text}"
            )

    listing = docs_dir / "index.html"
    cards: list[tuple[str, str | None]] = []
    if listing.is_file():
        patched, cards = patch_listing(listing.read_text(encoding="utf-8"), values)
        if _write(listing, patched, args.check):
            changed.append("index.html")

    search = docs_dir / "search.json"
    if search.is_file() and cards:
        texts = [text for _, text in cards if text is not None]
        if len(texts) != len(cards):
            warnings.append("search.json: some listing cards have no reading time; skipped")
        else:
            raw = search.read_text(encoding="utf-8")
            try:
                entries = patch_search_index(json.loads(raw), texts)
            except PatchError as exc:
                warnings.append(f"search.json: {exc}")
            else:
                # Matches Quarto's own formatting: 2-space indent, real UTF-8,
                # no trailing newline.
                if _write(search, json.dumps(entries, indent=2, ensure_ascii=False), args.check):
                    changed.append("search.json")

    for warning in warnings:
        print(f"⚠️  reading time: {warning}", file=sys.stderr)

    if args.check:
        if changed:
            print(f"reading time: {len(changed)} file(s) out of date: {', '.join(changed)}")
            return 1
        print(f"reading time: up to date ({len(values)} post(s))")
        return 0

    # Warnings are surfaced but never fatal: this runs inside `quarto render`,
    # and an unexpected page shape should not fail a build or a publish.
    print(f"reading time: {len(values)} post(s), {len(changed)} file(s) updated")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(argv)
