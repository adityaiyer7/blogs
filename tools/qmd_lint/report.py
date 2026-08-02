"""Plain-text, per-category terminal report (no emojis)."""

from __future__ import annotations

import json
from collections import defaultdict

from .model import CATEGORY_LABELS, CATEGORY_ORDER, Finding, REGISTRY, Severity


def _category_of(rule_id: str) -> str:
    meta = REGISTRY.get(rule_id)
    return meta.category if meta else rule_id[:1]


def format_file_report(rel_path: str, findings: list[Finding]) -> str:
    if not findings:
        return f"{rel_path}: no issues"

    by_cat: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_cat[_category_of(f.rule_id)].append(f)

    lines = [rel_path, ""]
    max_line = max(f.line for f in findings)
    line_width = len(str(max_line))
    for cat in CATEGORY_ORDER:
        items = by_cat.get(cat)
        if not items:
            continue
        lines.append(f"  {CATEGORY_LABELS[cat]}")
        for f in sorted(items, key=lambda f: (f.line, f.rule_id)):
            sev = f.severity.label.ljust(5)
            loc = f"line {str(f.line).rjust(line_width)}"
            suffix = "  (fixable)" if f.fixable else ""
            lines.append(f"    {sev}  {f.rule_id.ljust(3)}  {loc}  {f.message}{suffix}")
        lines.append("")

    errors = sum(1 for f in findings if f.severity == Severity.ERROR)
    warns = sum(1 for f in findings if f.severity == Severity.WARNING)
    infos = sum(1 for f in findings if f.severity == Severity.INFO)
    fixable = sum(1 for f in findings if f.fixable)
    parts = []
    if errors:
        parts.append(f"{errors} error{'s' if errors != 1 else ''}")
    if warns:
        parts.append(f"{warns} warning{'s' if warns != 1 else ''}")
    if infos:
        parts.append(f"{infos} info")
    summary = ", ".join(parts) if parts else "no issues"
    fix_note = f"  ({fixable} fixable)" if fixable else ""
    lines.append(f"  Summary: {summary}{fix_note}")
    return "\n".join(lines)


def format_json(results: dict[str, list[Finding]]) -> str:
    payload = {
        rel: [
            {
                "rule": f.rule_id,
                "severity": f.severity.label,
                "line": f.line,
                "col": f.col,
                "message": f.message,
                "fixable": f.fixable,
            }
            for f in findings
        ]
        for rel, findings in results.items()
    }
    return json.dumps(payload, indent=2)
