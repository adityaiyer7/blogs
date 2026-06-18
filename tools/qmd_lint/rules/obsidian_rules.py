"""Category E — Obsidian artifacts (non-callout)."""

from __future__ import annotations

import re

from ..model import Finding, Fix, Severity, rule
from ..parser import Document

_WIKILINK_RE = re.compile(r"!?\[\[")
_HIGHLIGHT_RE = re.compile(r"==([^=\n]+)==")
_COMMENT_RE = re.compile(r"%%(.*?)%%")
_TAG_RE = re.compile(r"^#[A-Za-z][\w/-]*(\s|$)")
_BLOCKREF_RE = re.compile(r"\s+\^[\w-]+\s*$")


def _body_lines(doc: Document):
    for ln in doc.lines:
        if ln.in_code or ln.in_front_matter:
            continue
        yield ln


@rule("E1", "E", Severity.ERROR)
def e1_wikilinks(doc: Document) -> list[Finding]:
    out = []
    for ln in _body_lines(doc):
        m = _WIKILINK_RE.search(ln.raw)
        if m:
            out.append(Finding("E1", Severity.ERROR, ln.number, "Obsidian wikilink/embed [[…]] won't render in Quarto", col=m.start()))
    return out


@rule("E2", "E", Severity.WARNING, fixable=True)
def e2_highlight(doc: Document) -> list[Finding]:
    out = []
    for ln in _body_lines(doc):
        if ln.in_display_math:
            continue
        if _HIGHLIGHT_RE.search(ln.raw):
            new = _HIGHLIGHT_RE.sub(r"**\1**", ln.raw)
            out.append(
                Finding(
                    "E2",
                    Severity.WARNING,
                    ln.number,
                    "Obsidian highlight ==text== — converting to **bold**",
                    fixable=True,
                    fix=Fix(line=ln.number, new_text=new),
                )
            )
    return out


@rule("E3", "E", Severity.WARNING, fixable=True)
def e3_comments(doc: Document) -> list[Finding]:
    out = []
    for ln in _body_lines(doc):
        if _COMMENT_RE.search(ln.raw):
            new = _COMMENT_RE.sub("", ln.raw).rstrip()
            out.append(
                Finding(
                    "E3",
                    Severity.WARNING,
                    ln.number,
                    "Obsidian comment %%…%% — stripping",
                    fixable=True,
                    fix=Fix(line=ln.number, new_text=new) if new.strip() else Fix(line=ln.number, delete=True),
                )
            )
    return out


@rule("E4", "E", Severity.WARNING)
def e4_inline_tag(doc: Document) -> list[Finding]:
    out = []
    for ln in _body_lines(doc):
        if _TAG_RE.match(ln.raw):
            out.append(Finding("E4", Severity.WARNING, ln.number, "line starts with '#tag' (missing space for a heading?)"))
    return out


@rule("E5", "E", Severity.WARNING, fixable=True)
def e5_block_refs(doc: Document) -> list[Finding]:
    out = []
    for ln in _body_lines(doc):
        if _BLOCKREF_RE.search(ln.raw):
            new = _BLOCKREF_RE.sub("", ln.raw)
            out.append(
                Finding(
                    "E5",
                    Severity.WARNING,
                    ln.number,
                    "Obsidian block reference ^id — stripping",
                    fixable=True,
                    fix=Fix(line=ln.number, new_text=new),
                )
            )
    return out
