"""Tests for blogposts/scripts/inject_listing_badges.py.

The script rewrites Quarto's rendered listing HTML, so the fixtures here are
trimmed copies of that markup rather than synthetic tags -- the card wrapper,
the `body` div, and the post link are exactly what the script keys off, and a
change in any of them is the failure mode worth catching.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "blogposts" / "scripts" / "inject_listing_badges.py"

spec = importlib.util.spec_from_file_location("inject_listing_badges", SCRIPT)
badges = importlib.util.module_from_spec(spec)
# Register before executing: @dataclass resolves annotations through
# sys.modules[cls.__module__], which is absent for a bare spec load.
sys.modules[spec.name] = badges
spec.loader.exec_module(badges)

PINNED = badges.PostMeta(pinned=True)
IN_SERIES = badges.PostMeta(
    series_id="representational-geometry",
    series_title="Representational Geometry from First Principles",
)
PINNED_IN_SERIES = badges.PostMeta(
    pinned=True,
    series_id="representational-geometry",
    series_title="Representational Geometry from First Principles",
)


def card(slug: str, prefix: str = "./") -> str:
    return (
        '<div class="quarto-post image-right" data-index="0" '
        'data-categories="SW50ZXJwcmV0YWJpbGl0eQ==" data-listing-date-sort="1774828800000">\n'
        '<div class="body">\n'
        '<h3 class="no-anchor listing-title">\n'
        f'<a href="{prefix}posts/{slug}/index.html" class="no-external">A Title</a>\n'
        "</h3>\n"
        "</div>\n"
        '<div class="metadata">\n'
        f'<a href="{prefix}posts/{slug}/index.html" class="no-external">\n'
        '<div class="listing-date">\nMar 30, 2026\n</div>\n'
        "</a>\n</div>\n</div>\n"
    )


def page(*slugs: str, prefix: str = "./") -> str:
    body = "".join(card(s, prefix) for s in slugs)
    return f'<div class="quarto-listing" id="listing-all-posts">\n{body}</div>\n'


# ── Pin badges ──────────────────────────────────────────────────────────────


def test_badges_only_pinned_cards():
    html, added = badges.annotate_page(page("alpha", "beta"), {"alpha": PINNED})
    assert added == 1
    alpha, beta = html.split('<div class="quarto-post')[1:]
    assert badges.BADGE_CLASS in alpha
    assert badges.BADGE_CLASS not in beta


def test_badge_precedes_the_title_inside_body():
    html, _ = badges.annotate_page(page("alpha"), {"alpha": PINNED})
    assert '<div class="body">\n<div class="listing-pinned-badge">Pinned</div>' in html


def test_badge_text_is_visible_not_icon_only():
    html, _ = badges.annotate_page(page("alpha"), {"alpha": PINNED})
    assert ">Pinned</div>" in html


def test_no_annotations_leaves_page_untouched():
    original = page("alpha", "beta")
    html, added = badges.annotate_page(original, {})
    assert added == 0
    assert html == original


def test_quarto_markup_is_otherwise_preserved():
    original = page("alpha")
    html, _ = badges.annotate_page(original, {"alpha": PINNED})
    assert html.replace(badges.BADGE_HTML, "") == original


def test_reprocessing_does_not_double_badge():
    once, _ = badges.annotate_page(page("alpha"), {"alpha": PINNED})
    twice, added = badges.annotate_page(once, {"alpha": PINNED})
    assert added == 0
    assert twice.count(badges.BADGE_CLASS) == 1


def test_unmatched_card_markup_fails_loudly():
    # The wrapper is present but the inner structure has drifted, so no card
    # matches. Silently annotating nothing is the bug this guards against.
    drifted = '<div class="quarto-post"><section>no body div</section></div>'
    with pytest.raises(SystemExit, match="listing output has changed"):
        badges.annotate_page(drifted, {"alpha": PINNED})


def test_page_without_listings_is_not_an_error():
    html, added = badges.annotate_page("<p>a post page</p>", {"alpha": PINNED})
    assert added == 0
    assert html == "<p>a post page</p>"


# ── Series labels ───────────────────────────────────────────────────────────


def test_series_label_only_on_series_cards():
    html, added = badges.annotate_page(page("alpha", "beta"), {"alpha": IN_SERIES})
    assert added == 1
    alpha, beta = html.split('<div class="quarto-post')[1:]
    assert badges.SERIES_CLASS in alpha
    assert badges.SERIES_CLASS not in beta


def test_series_label_links_relative_to_the_cards_own_href():
    # A series page is two levels down, so its cards link to ../../posts/... and
    # the series link has to use the same prefix rather than a site-root path.
    html, _ = badges.annotate_page(page("alpha", prefix="../../"), {"alpha": IN_SERIES})
    assert 'href="../../series/representational-geometry/index.html"' in html

    html, _ = badges.annotate_page(page("alpha"), {"alpha": IN_SERIES})
    assert 'href="./series/representational-geometry/index.html"' in html


def test_series_label_shows_the_reader_facing_title():
    html, _ = badges.annotate_page(page("alpha"), {"alpha": IN_SERIES})
    assert "Series: Representational Geometry from First Principles</a>" in html


def test_series_label_suppressed_on_the_series_landing_page():
    # Every card there belongs to the series, so the label is pure repetition.
    html, added = badges.annotate_page(
        page("alpha", prefix="../../"), {"alpha": IN_SERIES}, on_series_page=True
    )
    assert added == 0
    assert badges.SERIES_CLASS not in html


def test_pinned_badge_still_shows_on_the_series_landing_page():
    html, added = badges.annotate_page(
        page("alpha", prefix="../../"), {"alpha": PINNED_IN_SERIES}, on_series_page=True
    )
    assert added == 1
    assert badges.BADGE_CLASS in html
    assert badges.SERIES_CLASS not in html


def test_badge_and_label_compose_badge_first():
    html, added = badges.annotate_page(page("alpha"), {"alpha": PINNED_IN_SERIES})
    assert added == 2
    body = html.split('<div class="body">')[1]
    assert body.index(badges.BADGE_CLASS) < body.index(badges.SERIES_CLASS)


def test_reprocessing_does_not_double_label():
    once, _ = badges.annotate_page(page("alpha"), {"alpha": PINNED_IN_SERIES})
    twice, added = badges.annotate_page(once, {"alpha": PINNED_IN_SERIES})
    assert added == 0
    assert twice.count(badges.SERIES_CLASS) == 1
    assert twice.count(badges.BADGE_CLASS) == 1


def test_partial_series_metadata_produces_no_label():
    # series-id without a title has nothing to render; rule F5 warns separately.
    partial = badges.PostMeta(series_id="representational-geometry")
    html, added = badges.annotate_page(page("alpha"), {"alpha": partial})
    assert added == 0
    assert badges.SERIES_CLASS not in html


def test_series_title_is_html_escaped():
    risky = badges.PostMeta(series_id="s", series_title='Cats & "Dogs" <b>')
    html, _ = badges.annotate_page(page("alpha"), {"alpha": risky})
    assert "Cats &amp; &quot;Dogs&quot; &lt;b&gt;" in html
    assert "<b>" not in html.split('<div class="listing-series-label">')[1]


# ── Front-matter reading ────────────────────────────────────────────────────


def _write_post(tmp_path, front_matter: str, body: str = "body"):
    post = tmp_path / "posts" / "slug"
    post.mkdir(parents=True)
    (post / "index.qmd").write_text(
        f'---\ntitle: "T"\ndate: 2026-01-01\n{front_matter}\nkind: misc\n---\n\n{body}\n',
        encoding="utf-8",
    )
    return tmp_path / "posts"


@pytest.mark.parametrize(
    "front_matter, expected",
    [
        ("pinned: true", True),
        ("pinned: false", False),
        ("", False),
        ("pinned: true  # featured", True),
    ],
)
def test_post_metadata_reads_pinned(tmp_path, monkeypatch, front_matter, expected):
    monkeypatch.setattr(badges, "POSTS_DIR", _write_post(tmp_path, front_matter))
    assert badges.post_metadata()["slug"].pinned is expected


def test_post_metadata_reads_series_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(
        badges,
        "POSTS_DIR",
        _write_post(
            tmp_path,
            'series-id: representational-geometry\nseries: "Representational Geometry"',
        ),
    )
    meta = badges.post_metadata()["slug"]
    assert meta.series_id == "representational-geometry"
    # The quotes are YAML syntax, not part of the title.
    assert meta.series_title == "Representational Geometry"


def test_post_metadata_ignores_unquoted_and_absent_series(tmp_path, monkeypatch):
    monkeypatch.setattr(badges, "POSTS_DIR", _write_post(tmp_path, "series: Plain Title"))
    meta = badges.post_metadata()["slug"]
    assert meta.series_title == "Plain Title"
    assert meta.series_id is None


def test_metadata_fields_in_body_are_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(
        badges,
        "POSTS_DIR",
        _write_post(tmp_path, "toc: true", body="prose mentioning\npinned: true\nseries-id: x"),
    )
    meta = badges.post_metadata()["slug"]
    assert meta.pinned is False
    assert meta.series_id is None


def test_is_series_page_only_matches_the_series_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(badges, "OUTPUT_DIR", tmp_path)
    assert badges.is_series_page(tmp_path / "series" / "rg" / "index.html")
    assert not badges.is_series_page(tmp_path / "index.html")
    assert not badges.is_series_page(tmp_path / "posts" / "a-post" / "index.html")
    # A post that merely happens to be named "series" is not a landing page.
    assert not badges.is_series_page(tmp_path / "posts" / "series.html")
