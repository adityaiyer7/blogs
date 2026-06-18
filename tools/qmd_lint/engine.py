"""Run rules over a document and apply fixes.

Keeps the orchestration (collect findings, apply severity overrides, apply
fixes, re-verify idempotence) separate from both the rules and the CLI.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from . import rules as _rules  # noqa: F401  (registers all rules)
from .model import REGISTRY, Finding, Fix, effective_severity
from .parser import Document, parse


def collect_findings(doc: Document, only: set[str] | None = None, skip: set[str] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for meta in REGISTRY.values():
        if not _rule_enabled(meta.id, meta.category, only, skip):
            continue
        for f in meta.fn(doc):
            f.severity = effective_severity(f.rule_id, f.severity)
            findings.append(f)
    findings.sort(key=lambda f: (f.line, f.rule_id))
    return findings


def _rule_enabled(rule_id: str, category: str, only: set[str] | None, skip: set[str] | None) -> bool:
    if only:
        if rule_id not in only and category not in only:
            return False
    if skip:
        if rule_id in skip or category in skip:
            return False
    return True


def apply_fixes(raw_lines: list[str], fixes: list[Fix]) -> list[str]:
    """Apply line-oriented fixes, producing a new list of lines."""
    replaced: dict[int, str | None] = {}
    inserts: dict[int, list[str]] = defaultdict(list)
    for f in fixes:
        idx = f.line - 1
        if f.insert_before is not None:
            inserts[idx].append(f.insert_before)
        elif f.delete:
            replaced[idx] = None
        elif f.new_text is not None:
            replaced[idx] = f.new_text
    out: list[str] = []
    for idx, line in enumerate(raw_lines):
        for ins in inserts.get(idx, []):
            out.append(ins)
        if idx in replaced:
            val = replaced[idx]
            if val is None:
                continue
            out.extend(val.split("\n"))
        else:
            out.append(line)
    return out


def fix_document(path: Path, max_passes: int = 6) -> tuple[int, list[Finding]]:
    """Apply all fixable findings to ``path`` until stable.

    Returns (number_of_fixes_applied, remaining_findings).
    """
    doc = parse(path)
    total_applied = 0
    for _ in range(max_passes):
        findings = collect_findings(doc)
        fixes = [fix for f in findings if f.fixable for fix in f.all_fixes()]
        if not fixes:
            break
        new_lines = apply_fixes(doc.raw_lines, fixes)
        total_applied += len(fixes)
        text = "\n".join(new_lines)
        if doc.ends_with_newline:
            text += "\n"
        path.write_text(text, encoding="utf-8")
        doc = parse(path)
    else:
        # Did not converge; surface remaining state rather than looping forever.
        pass
    remaining = collect_findings(doc)
    return total_applied, remaining
