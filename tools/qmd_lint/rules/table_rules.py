"""Category B — table rules."""

from __future__ import annotations

import re

from ..model import Finding, Fix, Severity, rule
from ..parser import Document, Region, _is_pipe_row

_STRAY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_'.\-]{0,19}$")


@rule("B1", "B", Severity.ERROR)
def b1_inconsistent_columns(doc: Document) -> list[Finding]:
    out = []
    for t in doc.tables:
        header = t.col_counts[0]
        for k in range(2, len(t.col_counts)):  # skip header(0) and separator(1)
            if t.col_counts[k] != header:
                out.append(
                    Finding(
                        "B1",
                        Severity.ERROR,
                        t.row_lines[k],
                        f"table row has {t.col_counts[k]} columns, header has {header}",
                    )
                )
    return out


@rule("B2", "B", Severity.ERROR)
def b2_missing_separator(doc: Document) -> list[Finding]:
    """Runs of pipe rows that never formed a table (no separator row)."""
    out = []
    in_table = {n for t in doc.tables for n in range(t.start_line, t.end_line + 1)}
    run_start = None
    run_len = 0
    for ln in doc.lines:
        if _is_pipe_row(ln) and ln.number not in in_table and ln.region != Region.TABLE:
            if run_start is None:
                run_start = ln.number
            run_len += 1
        else:
            if run_start is not None and run_len >= 2:
                out.append(
                    Finding("B2", Severity.ERROR, run_start, "table-like rows with no '|---|' separator row")
                )
            run_start = None
            run_len = 0
    if run_start is not None and run_len >= 2:
        out.append(Finding("B2", Severity.ERROR, run_start, "table-like rows with no '|---|' separator row"))
    return out


@rule("B3", "B", Severity.ERROR)
def b3_separator_mismatch(doc: Document) -> list[Finding]:
    out = []
    for t in doc.tables:
        if t.col_counts[1] != t.col_counts[0]:
            out.append(
                Finding(
                    "B3",
                    Severity.ERROR,
                    t.separator_line or t.start_line,
                    f"separator has {t.col_counts[1]} columns, header has {t.col_counts[0]}",
                )
            )
    return out


@rule("B4", "B", Severity.WARNING)
def b4_br_in_cell(doc: Document) -> list[Finding]:
    out = []
    for t in doc.tables:
        for cells, line_no in zip(t.rows, t.row_lines):
            if any("<br>" in c.lower() for c in cells):
                out.append(Finding("B4", Severity.WARNING, line_no, "<br> inside a table cell"))
    return out


@rule("B5", "B", Severity.WARNING, fixable=True)
def b5_blank_around_table(doc: Document) -> list[Finding]:
    out = []
    for t in doc.tables:
        before = t.start_line - 1
        if before >= 1:
            prev = doc.line_text(before)
            if prev.strip() != "":
                out.append(
                    Finding(
                        "B5",
                        Severity.WARNING,
                        t.start_line,
                        "no blank line before table",
                        fixable=True,
                        fix=Fix(line=t.start_line, insert_before=""),
                    )
                )
        after = t.end_line + 1
        if after <= len(doc.lines):
            nxt = doc.line_text(after)
            if nxt.strip() != "":
                out.append(
                    Finding(
                        "B5",
                        Severity.WARNING,
                        t.end_line,
                        "no blank line after table",
                        fixable=True,
                        fix=Fix(line=after, insert_before=""),
                    )
                )
    return out


@rule("B6", "B", Severity.WARNING, fixable=True)
def b6_ragged_edges(doc: Document) -> list[Finding]:
    out = []
    for t in doc.tables:
        for line_no in t.row_lines:
            raw = doc.line_text(line_no)
            stripped = raw.strip()
            if not stripped:
                continue
            missing_lead = not stripped.startswith("|")
            missing_trail = not stripped.endswith("|")
            if missing_lead or missing_trail:
                indent = raw[: len(raw) - len(raw.lstrip())]
                new = stripped
                if missing_lead:
                    new = "| " + new
                if missing_trail:
                    new = new + " |"
                out.append(
                    Finding(
                        "B6",
                        Severity.WARNING,
                        line_no,
                        "table row missing edge '|'",
                        fixable=True,
                        fix=Fix(line=line_no, new_text=indent + new),
                    )
                )
    return out


@rule("B7", "B", Severity.WARNING)
def b7_stray_text(doc: Document) -> list[Finding]:
    """A lone short token glued directly above/below a table (the 'arc' case)."""
    out = []
    for t in doc.tables:
        for adj, where in ((t.start_line - 1, "above"), (t.end_line + 1, "below")):
            if adj < 1 or adj > len(doc.lines):
                continue
            raw = doc.line_text(adj)
            stripped = raw.strip()
            if stripped and _STRAY_RE.match(stripped) and not _is_pipe_row(doc.lines[adj - 1]):
                out.append(
                    Finding("B7", Severity.WARNING, adj, f"stray text {stripped!r} {where} a table")
                )
    return out
