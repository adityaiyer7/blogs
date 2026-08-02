"""Category D — image / link rules."""

from __future__ import annotations

from ..config import EXPECTED_IMAGE_PREFIX
from ..model import Finding, Severity, rule
from ..parser import Document
from ..util import is_anchor, is_url


@rule("D1", "D", Severity.ERROR)
def d1_missing_image(doc: Document) -> list[Finding]:
    out = []
    post_dir = doc.path.parent
    for span in doc.inline_spans:
        if span.kind != "image":
            continue
        target = (span.target or "").strip()
        if target == "" or is_url(target) or is_anchor(target):
            continue
        path = (post_dir / target).resolve()
        if not path.exists():
            out.append(Finding("D1", Severity.ERROR, span.line, f"image not found: {target}", col=span.start))
    return out


@rule("D2", "D", Severity.WARNING)
def d2_image_path_prefix(doc: Document) -> list[Finding]:
    out = []
    for span in doc.inline_spans:
        if span.kind != "image":
            continue
        target = (span.target or "").strip()
        if target == "" or is_url(target) or is_anchor(target):
            continue
        if not target.startswith(EXPECTED_IMAGE_PREFIX):
            out.append(
                Finding(
                    "D2",
                    Severity.WARNING,
                    span.line,
                    f"image path not under {EXPECTED_IMAGE_PREFIX!r}: {target}",
                    col=span.start,
                )
            )
    return out


@rule("D3", "D", Severity.WARNING)
def d3_empty_target(doc: Document) -> list[Finding]:
    out = []
    for span in doc.inline_spans:
        if span.kind not in ("link", "image"):
            continue
        if (span.target or "").strip() == "":
            out.append(Finding("D3", Severity.WARNING, span.line, "empty link/image target", col=span.start))
    return out


@rule("D4", "D", Severity.WARNING)
def d4_broken_link(doc: Document) -> list[Finding]:
    """A '](' with no closing ')' on the same line — a malformed link."""
    out = []
    for ln in doc.lines:
        if ln.in_code or ln.in_front_matter or ln.in_display_math:
            continue
        idx = ln.raw.find("](")
        while idx != -1:
            if ln.raw.find(")", idx + 2) == -1:
                out.append(Finding("D4", Severity.WARNING, ln.number, "unclosed link '](...' ", col=idx))
                break
            idx = ln.raw.find("](", idx + 2)
    return out


@rule("D5", "D", Severity.WARNING)
def d5_space_in_path(doc: Document) -> list[Finding]:
    out = []
    for span in doc.inline_spans:
        if span.kind not in ("link", "image"):
            continue
        target = (span.target or "").strip()
        if target and not is_url(target) and " " in target:
            out.append(Finding("D5", Severity.WARNING, span.line, f"space in path: {target}", col=span.start))
    return out
