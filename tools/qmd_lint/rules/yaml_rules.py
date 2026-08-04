"""Category F — YAML front matter rules."""

from __future__ import annotations

import datetime as _dt
import re

from ..config import REQUIRED_FRONT_MATTER_KEYS
from ..model import Finding, Severity, rule
from ..parser import Document

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SERIES_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SERIES_KEYS = ("series-id", "series", "series-order")


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


@rule("F5", "F", Severity.WARNING)
def f5_series_metadata(doc: Document) -> list[Finding]:
    """Series metadata is optional, but a partial or malformed set fails silently.

    A post carrying `series:` without `series-id:` renders perfectly and is
    simply absent from its landing page — nothing errors and nothing looks
    wrong, so the only way to notice is to go looking. Same for a `series-order`
    that YAML read as a string: the landing page then sorts it lexicographically
    against the integers. Hence a warning rather than trusting authors to
    remember. See docs/design/series.md.
    """
    if not doc.front_matter:
        return []

    present = [key for key in _SERIES_KEYS if key in doc.front_matter]
    if not present:
        return []

    line = _fm_start(doc)
    out = []

    missing = [key for key in _SERIES_KEYS if key not in doc.front_matter]
    if missing:
        out.append(
            Finding(
                "F5",
                Severity.WARNING,
                line,
                "series metadata is incomplete: has "
                + ", ".join(present)
                + " but is missing "
                + ", ".join(missing),
            )
        )

    series_id = doc.front_matter.get("series-id")
    if series_id is not None and not _SERIES_ID_RE.match(str(series_id).strip()):
        out.append(
            Finding(
                "F5",
                Severity.WARNING,
                line,
                f"series-id should be lowercase kebab-case, got: {series_id!r}",
            )
        )

    order = doc.front_matter.get("series-order")
    # bool is an int subclass, and `series-order: true` is never intended.
    if order is not None and (isinstance(order, bool) or not isinstance(order, int)):
        out.append(
            Finding(
                "F5",
                Severity.WARNING,
                line,
                f"series-order should be an integer, got: {order!r}",
            )
        )

    return out
