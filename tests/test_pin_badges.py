"""Tests for blogposts/scripts/inject_pin_badges.py.

The script rewrites Quarto's rendered listing HTML, so the fixtures here are
trimmed copies of that markup rather than synthetic tags -- the card wrapper,
the `body` div, and the post link are exactly what the script keys off, and a
change in any of them is the failure mode worth catching.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "blogposts" / "scripts" / "inject_pin_badges.py"

spec = importlib.util.spec_from_file_location("inject_pin_badges", SCRIPT)
pin_badges = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pin_badges)


def card(slug: str) -> str:
    return (
        '<div class="quarto-post image-right" data-index="0" '
        'data-categories="SW50ZXJwcmV0YWJpbGl0eQ==" data-listing-date-sort="1774828800000">\n'
        '<div class="body">\n'
        '<h3 class="no-anchor listing-title">\n'
        f'<a href="./posts/{slug}/index.html" class="no-external">A Title</a>\n'
        "</h3>\n"
        "</div>\n"
        '<div class="metadata">\n'
        f'<a href="./posts/{slug}/index.html" class="no-external">\n'
        '<div class="listing-date">\nMar 30, 2026\n</div>\n'
        "</a>\n</div>\n</div>\n"
    )


def page(*slugs: str) -> str:
    body = "".join(card(s) for s in slugs)
    return f'<div class="quarto-listing" id="listing-all-posts">\n{body}</div>\n'


def test_badges_only_pinned_cards():
    html, added = pin_badges.badge_page(page("alpha", "beta"), {"alpha"})
    assert added == 1
    alpha, beta = html.split('<div class="quarto-post')[1:]
    assert pin_badges.BADGE_CLASS in alpha
    assert pin_badges.BADGE_CLASS not in beta


def test_badge_precedes_the_title_inside_body():
    html, _ = pin_badges.badge_page(page("alpha"), {"alpha"})
    assert '<div class="body">\n<div class="listing-pinned-badge">Pinned</div>' in html


def test_badge_text_is_visible_not_icon_only():
    html, _ = pin_badges.badge_page(page("alpha"), {"alpha"})
    assert ">Pinned</div>" in html


def test_no_pinned_posts_leaves_page_untouched():
    original = page("alpha", "beta")
    html, added = pin_badges.badge_page(original, set())
    assert added == 0
    assert html == original


def test_quarto_markup_is_otherwise_preserved():
    original = page("alpha")
    html, _ = pin_badges.badge_page(original, {"alpha"})
    assert html.replace(pin_badges.BADGE_HTML, "") == original


def test_reprocessing_does_not_double_badge():
    once, _ = pin_badges.badge_page(page("alpha"), {"alpha"})
    twice, added = pin_badges.badge_page(once, {"alpha"})
    assert added == 0
    assert twice.count(pin_badges.BADGE_CLASS) == 1


def test_unmatched_card_markup_fails_loudly():
    # The wrapper is present but the inner structure has drifted, so no card
    # matches. Silently badging nothing is the bug this guards against.
    drifted = '<div class="quarto-post"><section>no body div</section></div>'
    with pytest.raises(SystemExit, match="listing output has changed"):
        pin_badges.badge_page(drifted, {"alpha"})


def test_page_without_listings_is_not_an_error():
    html, added = pin_badges.badge_page("<p>a post page</p>", {"alpha"})
    assert added == 0
    assert html == "<p>a post page</p>"


@pytest.mark.parametrize(
    "front_matter, expected",
    [
        ("pinned: true", True),
        ("pinned: false", False),
        ("", False),
        ("pinned: true  # featured", True),
    ],
)
def test_pinned_slugs_reads_front_matter(tmp_path, monkeypatch, front_matter, expected):
    post = tmp_path / "posts" / "slug"
    post.mkdir(parents=True)
    (post / "index.qmd").write_text(
        f'---\ntitle: "T"\ndate: 2026-01-01\n{front_matter}\nkind: misc\n---\n\nbody\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(pin_badges, "POSTS_DIR", tmp_path / "posts")
    assert ("slug" in pin_badges.pinned_slugs()) is expected


def test_pinned_field_in_body_is_ignored(tmp_path, monkeypatch):
    post = tmp_path / "posts" / "slug"
    post.mkdir(parents=True)
    (post / "index.qmd").write_text(
        '---\ntitle: "T"\nkind: misc\n---\n\nprose mentioning\npinned: true\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(pin_badges, "POSTS_DIR", tmp_path / "posts")
    assert pin_badges.pinned_slugs() == set()
