"""Tunable configuration for the linter.

Everything a user is likely to want to adjust lives here: which YAML keys are
required, which callout types Quarto understands, how Obsidian callout types map
onto Quarto's smaller set, and per-rule severity overrides.
"""

from __future__ import annotations

from .model import Severity

# Front matter keys every post must declare (rule F1).
REQUIRED_FRONT_MATTER_KEYS = ("title", "date", "categories")

# The five callout types Quarto renders natively (rules N4, N8).
QUARTO_CALLOUT_TYPES = ("note", "tip", "warning", "important", "caution")

# Obsidian ships many callout aliases; Quarto only has five. This maps the
# common Obsidian types onto the closest Quarto type when converting (rule N4).
# Anything not listed here is reported but left for the author to map by hand.
OBSIDIAN_TO_QUARTO = {
    # -> note
    "note": "note",
    "info": "note",
    "abstract": "note",
    "summary": "note",
    "tldr": "note",
    "todo": "note",
    "example": "note",
    "quote": "note",
    "cite": "note",
    # -> tip
    "tip": "tip",
    "hint": "tip",
    "success": "tip",
    "check": "tip",
    "done": "tip",
    "question": "tip",
    "help": "tip",
    "faq": "tip",
    # -> warning
    "warning": "warning",
    "attention": "warning",
    # -> important
    "important": "important",
    # -> caution
    "caution": "caution",
    "failure": "caution",
    "fail": "caution",
    "missing": "caution",
    "danger": "caution",
    "error": "caution",
    "bug": "caution",
}

# Where posts live, relative to the repo root (the dir containing pyproject.toml).
POSTS_GLOB = "blogposts/posts/*/index.qmd"
POST_DIR_TEMPLATE = "blogposts/posts/{slug}/index.qmd"

# Image references are expected to live under this directory inside a post (D2).
EXPECTED_IMAGE_PREFIX = "assets/imgs/"

# Per-rule severity overrides. Each rule declares a default severity at
# registration time; entries here win over that default, so a user can promote a
# warning to an error (or silence it down to info) without touching rule code.
SEVERITY_OVERRIDES: dict[str, Severity] = {}
