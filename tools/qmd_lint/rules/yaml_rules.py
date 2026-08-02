"""Category F — YAML front matter rules."""

from __future__ import annotations

import datetime as _dt
import re

from ..config import REQUIRED_FRONT_MATTER_KEYS
from ..model import Finding, Severity, rule
from ..parser import Document

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _fm_start(doc: Document) -> int:
    return doc.front_matter_range[0] if doc.front_matter_range else 1


@rule("F1", "F", Severity.ERROR)
def f1_required_keys(doc: Document) -> list[Finding]:
    out = []
    if doc.front_matter_raw is None:
        return [Finding("F1", Severity.ERROR, 1, "post has no YAML front matter")]
    if doc.front_matter is None:
        msg = doc.front_matter_error or "front matter is not a mapping"
        return [Finding("F1", Severity.ERROR, _fm_start(doc), f"front matter failed to parse: {msg}")]
    for key in REQUIRED_FRONT_MATTER_KEYS:
        if key not in doc.front_matter:
            out.append(Finding("F1", Severity.ERROR, _fm_start(doc), f"missing required front-matter key: {key}"))
    return out


@rule("F2", "F", Severity.WARNING)
def f2_date_format(doc: Document) -> list[Finding]:
    if not doc.front_matter or "date" not in doc.front_matter:
        return []
    val = doc.front_matter["date"]
    if isinstance(val, (_dt.date, _dt.datetime)):
        return []  # YAML already parsed a valid ISO date
    if isinstance(val, str) and _DATE_RE.match(val.strip()):
        return []
    return [Finding("F2", Severity.WARNING, _fm_start(doc), f"date should be YYYY-MM-DD, got: {val!r}")]


@rule("F3", "F", Severity.WARNING)
def f3_unquoted_title_colon(doc: Document) -> list[Finding]:
    if not doc.front_matter_range:
        return []
    start, end = doc.front_matter_range
    for n in range(start + 1, end):
        raw = doc.line_text(n)
        m = re.match(r"^title:\s*(.+?)\s*$", raw)
        if not m:
            continue
        value = m.group(1)
        quoted = (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))
        if ":" in value and not quoted:
            return [Finding("F3", Severity.WARNING, n, "unquoted title contains ':' — wrap it in quotes")]
    return []


@rule("F4", "F", Severity.WARNING)
def f4_categories_list(doc: Document) -> list[Finding]:
    if not doc.front_matter or "categories" not in doc.front_matter:
        return []
    if not isinstance(doc.front_matter["categories"], list):
        return [Finding("F4", Severity.WARNING, _fm_start(doc), "categories should be a list, e.g. [AI, Math]")]
    return []
