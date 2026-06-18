"""Segmentation layer: turn a .qmd file into a line-annotated ``Document``.

This is the foundation every rule builds on. A single line-by-line state machine
classifies each line (front matter / code fence / table / callout / display math
/ body), and a second inline pass finds code spans, math spans, and link/image
targets on the remaining body lines. Rules consume the structured result rather
than re-scanning raw text, so concerns like "ignore everything inside a code
fence" are handled once, here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml


class Region(Enum):
    FRONT_MATTER = "front_matter"
    CODE_FENCE = "code_fence"
    TABLE = "table"
    CALLOUT_FENCE = "callout_fence"
    DISPLAY_MATH = "display_math"
    BODY = "body"


@dataclass
class Line:
    number: int  # 1-based
    raw: str
    region: Region = Region.BODY
    in_code: bool = False
    in_front_matter: bool = False
    in_display_math: bool = False
    callout_depth: int = 0
    fence_marker: str | None = None  # the literal ``` / ~~~ / ::: if a delimiter


@dataclass
class InlineSpan:
    line: int
    start: int  # column offset, 0-based
    end: int
    kind: str  # inline_code | inline_math | link | image
    text: str  # inner content (math/code) or full match (link/image)
    target: str | None = None  # for link/image: the (...) destination


@dataclass
class MathSpan:
    start_line: int
    end_line: int
    text: str  # inner math content (delimiters stripped)
    is_display: bool


@dataclass
class TableBlock:
    start_line: int  # header line
    separator_line: int | None
    end_line: int
    rows: list[list[str]]  # cells per row, edge pipes stripped (incl. header & sep)
    col_counts: list[int]
    row_lines: list[int]  # source line number for each entry in rows


@dataclass
class CalloutBlock:
    open_line: int
    close_line: int | None
    open_len: int  # number of colons on the opening fence
    close_len: int | None
    attrs: str  # raw text inside the {...}
    ctype: str | None  # the callout-X type
    title: str | None


@dataclass
class ObsCallout:
    """A raw Obsidian callout (``> [!type] title`` blockquote) needing conversion."""

    marker_line: int
    end_line: int
    depth: int  # number of leading '>' (1 = top level, >1 = nested)
    ctype: str
    fold: str  # '', '+', or '-'
    title: str
    body_lines: list[int]


@dataclass
class Document:
    path: Path
    lines: list[Line]
    raw_lines: list[str]  # text only, no trailing newline
    ends_with_newline: bool
    front_matter_raw: str | None = None
    front_matter: dict | None = None
    front_matter_error: str | None = None
    front_matter_range: tuple[int, int] | None = None  # (start, end) line numbers inclusive
    code_fences: list[tuple[int, int]] = field(default_factory=list)
    tables: list[TableBlock] = field(default_factory=list)
    callouts: list[CalloutBlock] = field(default_factory=list)
    unclosed_callouts: list[CalloutBlock] = field(default_factory=list)
    obsidian_callouts: list[ObsCallout] = field(default_factory=list)
    inline_spans: list[InlineSpan] = field(default_factory=list)
    display_math: list[MathSpan] = field(default_factory=list)

    def line_text(self, number: int) -> str:
        return self.raw_lines[number - 1]

    def iter_math(self):
        """Yield every math span (display blocks + inline spans) as MathSpan."""
        yield from self.display_math
        for span in self.inline_spans:
            if span.kind == "inline_math":
                yield MathSpan(span.line, span.line, span.text, is_display=False)


# --- regexes -----------------------------------------------------------------

_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
_CALLOUT_FENCE_RE = re.compile(r"^(\s*)(:{3,})\s*(.*)$")
_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)+\|?\s*$")
_OBS_CALLOUT_RE = re.compile(r"^((?:>\s*)+)\[!([A-Za-z]+)\]([+-]?)\s*(.*)$")
_CALLOUT_TYPE_RE = re.compile(r"\.callout-([A-Za-z]+)")
_CALLOUT_TITLE_RE = re.compile(r'title\s*=\s*"([^"]*)"')


def parse(path: str | Path) -> Document:
    text = Path(path).read_text(encoding="utf-8")
    ends_with_newline = text.endswith("\n")
    raw_lines = text.split("\n")
    if ends_with_newline:
        raw_lines = raw_lines[:-1]  # drop the trailing empty element

    lines = [Line(number=i + 1, raw=raw) for i, raw in enumerate(raw_lines)]
    doc = Document(
        path=Path(path),
        lines=lines,
        raw_lines=raw_lines,
        ends_with_newline=ends_with_newline,
    )

    _classify_structure(doc)
    _detect_callout_fences(doc)
    _detect_display_math(doc)
    _detect_tables(doc)
    _detect_obsidian_callouts(doc)
    _inline_pass(doc)
    return doc


def _classify_structure(doc: Document) -> None:
    """First pass: front matter and code fences (these gate everything else)."""
    lines = doc.lines
    n = len(lines)
    i = 0

    # Front matter: a leading '---' fence.
    if n > 0 and lines[0].raw.strip() == "---":
        end = None
        for j in range(1, n):
            if lines[j].raw.strip() == "---":
                end = j
                break
        if end is not None:
            for j in range(0, end + 1):
                lines[j].region = Region.FRONT_MATTER
                lines[j].in_front_matter = True
            raw = "\n".join(doc.raw_lines[1:end])
            doc.front_matter_raw = raw
            doc.front_matter_range = (1, end + 1)
            try:
                loaded = yaml.safe_load(raw)
                doc.front_matter = loaded if isinstance(loaded, dict) else None
                if loaded is not None and not isinstance(loaded, dict):
                    doc.front_matter_error = "front matter is not a mapping"
            except yaml.YAMLError as exc:
                doc.front_matter = None
                doc.front_matter_error = str(exc).splitlines()[0] if str(exc) else "invalid YAML"
            i = end + 1

    # Code fences.
    in_code = False
    fence_indent = ""
    fence_marker = ""
    start_line = 0
    while i < n:
        line = lines[i]
        if line.in_front_matter:
            i += 1
            continue
        m = _FENCE_RE.match(line.raw)
        if not in_code and m:
            in_code = True
            fence_indent = m.group(1)
            fence_marker = m.group(2)[0] * 3  # normalize to char type
            start_line = line.number
            line.region = Region.CODE_FENCE
            line.in_code = True
            line.fence_marker = m.group(2)
            i += 1
            continue
        if in_code:
            line.region = Region.CODE_FENCE
            line.in_code = True
            # A closing fence: same marker char, length >= opening, indent <= opening.
            if m and m.group(2)[0] * 3 == fence_marker and len(m.group(1)) <= len(fence_indent) + 3:
                if not m.group(3).strip():  # closing fences carry no info string
                    line.fence_marker = m.group(2)
                    doc.code_fences.append((start_line, line.number))
                    in_code = False
            i += 1
            continue
        i += 1

    if in_code:  # unterminated fence runs to EOF
        doc.code_fences.append((start_line, n))


def _body_indices(doc: Document) -> list[int]:
    """Indices of lines eligible for body-level scanning (not code/front matter)."""
    return [i for i, ln in enumerate(doc.lines) if not ln.in_code and not ln.in_front_matter]


def _detect_callout_fences(doc: Document) -> None:
    """Pair up Quarto ``:::`` fences via a stack; record callout divs."""
    stack: list[dict] = []
    depth_so_far = 0
    for i in _body_indices(doc):
        line = doc.lines[i]
        m = _CALLOUT_FENCE_RE.match(line.raw)
        if not m:
            line.callout_depth = len(stack)
            continue
        colons = m.group(2)
        rest = m.group(3).strip()
        if rest.startswith("{") or rest.startswith("."):
            # Opening fence with attributes.
            stack.append({"len": len(colons), "line": line.number, "attrs": rest})
            line.fence_marker = colons
            line.region = Region.CALLOUT_FENCE
        elif rest == "":
            if stack:  # bare ::: closes the most recent open
                opener = stack.pop()
                line.fence_marker = colons
                line.region = Region.CALLOUT_FENCE
                _record_callout(doc, opener, close_line=line.number, close_len=len(colons))
            else:  # stray close or attribute-less open div; treat as open
                stack.append({"len": len(colons), "line": line.number, "attrs": ""})
                line.fence_marker = colons
                line.region = Region.CALLOUT_FENCE
        else:
            # Malformed (e.g. "::: callout-note" without braces) — treat as open.
            stack.append({"len": len(colons), "line": line.number, "attrs": rest})
            line.fence_marker = colons
            line.region = Region.CALLOUT_FENCE
        line.callout_depth = len(stack)

    for opener in stack:  # anything still open at EOF is unclosed
        block = _build_callout_block(opener, close_line=None, close_len=None)
        if block.ctype is not None or "callout" in opener["attrs"]:
            doc.unclosed_callouts.append(block)


def _build_callout_block(opener: dict, close_line: int | None, close_len: int | None) -> CalloutBlock:
    attrs = opener["attrs"]
    type_m = _CALLOUT_TYPE_RE.search(attrs)
    title_m = _CALLOUT_TITLE_RE.search(attrs)
    return CalloutBlock(
        open_line=opener["line"],
        close_line=close_line,
        open_len=opener["len"],
        close_len=close_len,
        attrs=attrs,
        ctype=type_m.group(1) if type_m else None,
        title=title_m.group(1) if title_m else None,
    )


def _record_callout(doc: Document, opener: dict, close_line: int, close_len: int) -> None:
    block = _build_callout_block(opener, close_line, close_len)
    if block.ctype is not None or "callout" in opener["attrs"]:
        doc.callouts.append(block)


def _detect_display_math(doc: Document) -> None:
    """Find ``$$ ... $$`` display-math regions across body lines."""
    open_start: int | None = None
    content: list[str] = []
    for i in _body_indices(doc):
        line = doc.lines[i]
        if line.region == Region.CALLOUT_FENCE:
            continue
        stripped = line.raw.strip()
        count = stripped.count("$$")
        if open_start is None:
            if count == 0:
                continue
            if count >= 2 and stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 3:
                # Self-contained one-line display span.
                inner = stripped[2:-2]
                doc.display_math.append(MathSpan(line.number, line.number, inner, True))
                line.in_display_math = True
                line.region = Region.DISPLAY_MATH
            elif count % 2 == 1:
                open_start = line.number
                content = [stripped[stripped.index("$$") + 2 :]]
                line.in_display_math = True
                line.region = Region.DISPLAY_MATH
        else:
            line.in_display_math = True
            line.region = Region.DISPLAY_MATH
            if count >= 1:
                content.append(stripped[: stripped.index("$$")])
                doc.display_math.append(
                    MathSpan(open_start, line.number, "\n".join(content), True)
                )
                open_start = None
                content = []
            else:
                content.append(line.raw)

    if open_start is not None:  # unterminated $$ — record what we have
        doc.display_math.append(MathSpan(open_start, doc.lines[-1].number, "\n".join(content), True))


def _split_cells(row: str) -> list[str]:
    """Split a Markdown table row into cells on unescaped, non-code pipes."""
    cells: list[str] = []
    buf: list[str] = []
    in_code = False
    i = 0
    while i < len(row):
        ch = row[i]
        if ch == "\\" and i + 1 < len(row):
            buf.append(row[i : i + 2])
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
            buf.append(ch)
            i += 1
            continue
        if ch == "|" and not in_code:
            cells.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    cells.append("".join(buf))
    # Drop the empty leading/trailing cells produced by edge pipes.
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return [c.strip() for c in cells]


def _count_unescaped_pipes(text: str) -> int:
    count = 0
    i = 0
    in_code = False
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        elif ch == "|" and not in_code:
            count += 1
        i += 1
    return count


def _is_pipe_row(line: Line) -> bool:
    if line.in_code or line.in_front_matter or line.in_display_math:
        return False
    if line.region in (Region.CALLOUT_FENCE, Region.CODE_FENCE):
        return False
    stripped = line.raw.strip()
    if stripped == "":
        return False
    # A table row either has edge pipes or at least two interior pipes — this
    # keeps stray inline '|' (e.g. inside $a|b$) from being read as a table.
    return stripped.startswith("|") or stripped.endswith("|") or _count_unescaped_pipes(stripped) >= 2


def _detect_tables(doc: Document) -> None:
    lines = doc.lines
    n = len(lines)
    i = 0
    while i < n:
        sep = lines[i]
        if (
            not sep.in_code
            and not sep.in_front_matter
            and _SEPARATOR_RE.match(sep.raw)
            and i > 0
            and _is_pipe_row(lines[i - 1])
        ):
            header_idx = i - 1
            rows: list[list[str]] = [_split_cells(lines[header_idx].raw), _split_cells(sep.raw)]
            row_lines = [lines[header_idx].number, sep.number]
            j = i + 1
            while j < n and _is_pipe_row(lines[j]):
                rows.append(_split_cells(lines[j].raw))
                row_lines.append(lines[j].number)
                j += 1
            for k in range(header_idx, j):
                lines[k].region = Region.TABLE
            doc.tables.append(
                TableBlock(
                    start_line=lines[header_idx].number,
                    separator_line=sep.number,
                    end_line=lines[j - 1].number,
                    rows=rows,
                    col_counts=[len(r) for r in rows],
                    row_lines=row_lines,
                )
            )
            i = j
            continue
        i += 1


def _detect_obsidian_callouts(doc: Document) -> None:
    lines = doc.lines
    n = len(lines)
    body = set(_body_indices(doc))
    i = 0
    while i < n:
        if i not in body:
            i += 1
            continue
        line = lines[i]
        m = _OBS_CALLOUT_RE.match(line.raw)
        if m:
            gt_run = m.group(1)
            depth = gt_run.count(">")
            ctype = m.group(2)
            fold = m.group(3)
            title = m.group(4).strip()
            body_lines: list[int] = []
            j = i + 1
            while j < n and j in body and lines[j].raw.lstrip().startswith(">"):
                body_lines.append(lines[j].number)
                j += 1
            doc.obsidian_callouts.append(
                ObsCallout(
                    marker_line=line.number,
                    end_line=lines[j - 1].number if j - 1 >= i else line.number,
                    depth=depth,
                    ctype=ctype,
                    fold=fold,
                    title=title,
                    body_lines=body_lines,
                )
            )
            i = j
            continue
        i += 1


# Inline scanning -------------------------------------------------------------

def _inline_pass(doc: Document) -> None:
    for i in _body_indices(doc):
        line = doc.lines[i]
        if line.in_display_math or line.region in (Region.CODE_FENCE, Region.CALLOUT_FENCE):
            continue
        doc.inline_spans.extend(_scan_inline(line.number, line.raw))


def _scan_inline(line_no: int, text: str) -> list[InlineSpan]:
    spans: list[InlineSpan] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == "`":
            # Inline code span: find the matching backtick run.
            run = 1
            while i + run < n and text[i + run] == "`":
                run += 1
            close = text.find("`" * run, i + run)
            if close == -1:
                i += run
                continue
            spans.append(InlineSpan(line_no, i, close + run, "inline_code", text[i + run : close]))
            i = close + run
            continue
        if ch == "$":
            # Inline math: a single '$' opening (not '$$', handled elsewhere).
            if i + 1 < n and text[i + 1] == "$":
                i += 2
                continue
            # Avoid currency: skip if next char is a digit and there's no closing $.
            close = _find_inline_math_close(text, i + 1)
            if close == -1:
                i += 1
                continue
            spans.append(InlineSpan(line_no, i, close + 1, "inline_math", text[i + 1 : close]))
            i = close + 1
            continue
        if ch == "!" and i + 1 < n and text[i + 1] == "[":
            span = _scan_link(line_no, text, i, is_image=True)
            if span:
                spans.append(span)
                i = span.end
                continue
            i += 1
            continue
        if ch == "[":
            span = _scan_link(line_no, text, i, is_image=False)
            if span:
                spans.append(span)
                i = span.end
                continue
            i += 1
            continue
        i += 1
    return spans


def _find_inline_math_close(text: str, start: int) -> int:
    i = start
    n = len(text)
    while i < n:
        if text[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if text[i] == "$":
            return i
        i += 1
    return -1


def _scan_link(line_no: int, text: str, start: int, is_image: bool) -> InlineSpan | None:
    bracket_start = start + 1 if is_image else start
    # Find the closing ] for the label, allowing nested brackets.
    depth = 0
    i = bracket_start
    n = len(text)
    label_end = -1
    while i < n:
        if text[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                label_end = i
                break
        i += 1
    if label_end == -1 or label_end + 1 >= n or text[label_end + 1] != "(":
        return None
    paren_close = text.find(")", label_end + 1)
    if paren_close == -1:
        return None
    target = text[label_end + 2 : paren_close]
    return InlineSpan(
        line=line_no,
        start=start,
        end=paren_close + 1,
        kind="image" if is_image else "link",
        text=text[start : paren_close + 1],
        target=target,
    )
