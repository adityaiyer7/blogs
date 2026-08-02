#!/usr/bin/env python3
"""Convert lightweight blog citation tags into Quarto/Pandoc citations."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


CITATION_RE = re.compile(r"\{citation:([A-Za-z0-9_-]+)\}")
SOURCE_RE = re.compile(r"^\s*[-*]\s+\{([A-Za-z0-9_-]+)\}:\s+\[([^\]]+)\]\s*\(([^)]+)\)\s*$")
SLUG_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class Source:
    handle: str
    title: str
    url: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_target(target: str) -> Path:
    root = repo_root()
    if target.endswith(".qmd"):
        path = Path(target)
        return path if path.is_absolute() else root / path
    if not SLUG_RE.fullmatch(target):
        raise SystemExit(f"error: invalid target {target!r} (expected a slug or .qmd path)")
    return root / "blogposts" / "posts" / target / "index.qmd"


def frontmatter_bounds(lines: list[str]) -> tuple[int, int]:
    if not lines or lines[0].strip() != "---":
        raise SystemExit("error: post must start with YAML front matter")
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return 0, idx
    raise SystemExit("error: YAML front matter is missing its closing ---")


def in_code_fence_flags(lines: list[str]) -> list[bool]:
    flags: list[bool] = []
    in_fence = False
    fence_marker: str | None = None
    for line in lines:
        stripped = line.lstrip()
        opens_or_closes = stripped.startswith("```") or stripped.startswith("~~~")
        flags.append(in_fence)
        if opens_or_closes:
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = None
    return flags


def find_sources_heading(lines: list[str], start: int) -> int | None:
    code_flags = in_code_fence_flags(lines)
    matches = [
        idx
        for idx in range(start, len(lines))
        if not code_flags[idx] and lines[idx].strip().lower() == "# sources"
    ]
    if len(matches) > 1:
        display = ", ".join(str(idx + 1) for idx in matches)
        raise SystemExit(f"error: expected exactly one # Sources heading, found lines {display}")
    return matches[0] if matches else None


def find_next_top_heading(lines: list[str], start: int) -> int:
    code_flags = in_code_fence_flags(lines)
    for idx in range(start, len(lines)):
        if not code_flags[idx] and re.match(r"^#\s+", lines[idx]):
            return idx
    return len(lines)


def collect_citations(lines: list[str], start: int, end: int) -> list[str]:
    code_flags = in_code_fence_flags(lines)
    handles: list[str] = []
    seen: set[str] = set()
    for idx in range(start, end):
        if code_flags[idx]:
            continue
        for handle in CITATION_RE.findall(lines[idx]):
            if handle not in seen:
                seen.add(handle)
                handles.append(handle)
    return handles


def parse_sources(lines: list[str], start: int, end: int) -> dict[str, Source]:
    sources: dict[str, Source] = {}
    for idx in range(start, end):
        line = lines[idx]
        if not line.strip():
            continue
        match = SOURCE_RE.match(line)
        if not match:
            continue
        handle, title, url = (part.strip() for part in match.groups())
        if handle in sources:
            raise SystemExit(f"error: duplicate source handle {handle!r} at line {idx + 1}")
        sources[handle] = Source(handle=handle, title=title, url=url)
    return sources


def replace_citation_tags(lines: list[str], start: int, end: int) -> list[str]:
    code_flags = in_code_fence_flags(lines)
    out = lines[:]
    for idx in range(start, end):
        if not code_flags[idx]:
            out[idx] = CITATION_RE.sub(r"[@\1]", out[idx])
    return out


def ensure_frontmatter(lines: list[str]) -> list[str]:
    _, fm_end = frontmatter_bounds(lines)
    frontmatter = lines[1:fm_end]

    def set_key(items: list[str], key: str, value: str) -> list[str]:
        key_re = re.compile(rf"^\s*{re.escape(key)}\s*:")
        for idx, line in enumerate(items):
            if key_re.match(line):
                items[idx] = f"{key}: {value}"
                return items
        items.append(f"{key}: {value}")
        return items

    frontmatter = set_key(frontmatter, "inline-citations", "true")
    frontmatter = set_key(frontmatter, "bibliography", "references.bib")
    return ["---", *frontmatter, "---", *lines[fm_end + 1 :]]


def bibtex_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def write_references(post_path: Path, handles: list[str], sources: dict[str, Source]) -> None:
    blocks = []
    for handle in handles:
        source = sources[handle]
        blocks.append(
            "\n".join(
                [
                    f"@online{{{source.handle},",
                    f"  title = {{{bibtex_escape(source.title)}}},",
                    f"  url   = {{{bibtex_escape(source.url)}}}",
                    "}",
                ]
            )
        )
    (post_path.parent / "references.bib").write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def convert(path: Path, check: bool = False) -> int:
    if not path.is_file():
        raise SystemExit(f"error: file not found: {path}")

    original_text = path.read_text(encoding="utf-8")
    had_newline = original_text.endswith("\n")
    lines = original_text.splitlines()
    _, fm_end = frontmatter_bounds(lines)

    source_heading = find_sources_heading(lines, fm_end + 1)
    citation_end = source_heading if source_heading is not None else len(lines)
    handles = collect_citations(lines, fm_end + 1, citation_end)
    ignored_after_sources: list[str] = []
    if source_heading is not None:
        ignored_after_sources = collect_citations(lines, find_next_top_heading(lines, source_heading + 1), len(lines))
        if ignored_after_sources:
            joined = ", ".join(ignored_after_sources)
            print(
                f"warning: citation tag(s) after # Sources were ignored: {joined}",
                file=sys.stderr,
            )
    if not handles:
        print(f"{path}: no citation tags found before # Sources")
        return 0
    if source_heading is None:
        raise SystemExit("error: citation tags found, but no # Sources heading exists")

    source_end = find_next_top_heading(lines, source_heading + 1)
    sources = parse_sources(lines, source_heading + 1, source_end)
    missing = [handle for handle in handles if handle not in sources]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"error: missing # Sources entries for cited handle(s): {joined}")

    unused = [handle for handle in sources if handle not in handles]
    if unused:
        joined = ", ".join(unused)
        print(f"warning: source handle(s) listed but not cited before # Sources: {joined}", file=sys.stderr)

    updated = replace_citation_tags(lines, fm_end + 1, citation_end)
    tail = updated[source_end:]
    while tail and not tail[0].strip():
        tail = tail[1:]
    source_block = ["# Sources", "", "::: {#refs}", ":::"]
    updated = updated[:source_heading] + source_block + ([""] + tail if tail else [])
    updated = ensure_frontmatter(updated)

    output_text = "\n".join(updated)
    if had_newline:
        output_text += "\n"

    if check:
        changed = output_text != original_text or not (path.parent / "references.bib").is_file()
        print(f"{path}: {'would convert citations' if changed else 'citations already converted'}")
        return 1 if changed else 0

    path.write_text(output_text, encoding="utf-8")
    write_references(path, handles, sources)
    mapping = ", ".join(f"{handle}->{sources[handle].title}" for handle in handles)
    print(f"{path}: converted {len(handles)} citation source(s): {mapping}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert {citation:handle} tags in a blog post.")
    parser.add_argument("target", help="post slug or path to index.qmd")
    parser.add_argument("--check", action="store_true", help="report whether conversion would change files")
    args = parser.parse_args(argv)

    return convert(resolve_target(args.target), check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
