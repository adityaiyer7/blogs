"""Core data types and the rule registry.

A *rule* is a function ``(Document) -> list[Finding]`` registered with the
``@rule`` decorator. The CLI collects every registered rule, runs it over the
parsed document, and turns the resulting findings into terminal output and
optional auto-fixes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .parser import Document


class Severity(IntEnum):
    """Ordered so the highest-severity finding is easy to pick out."""

    INFO = 1
    WARNING = 2
    ERROR = 3

    @property
    def label(self) -> str:
        return {Severity.INFO: "INFO", Severity.WARNING: "WARN", Severity.ERROR: "ERROR"}[self]


@dataclass
class Fix:
    """A single, line-oriented edit produced by a fixable rule.

    ``new_text`` replaces the existing line (``None`` deletes it). If
    ``insert_before`` is set, those line(s) are inserted ahead of ``line``
    without removing it (used for blank-line insertions like C1/B5/N9).
    """

    line: int  # 1-based line number this fix targets
    new_text: str | None = None
    insert_before: str | None = None
    delete: bool = False


@dataclass
class Finding:
    rule_id: str
    severity: Severity
    line: int
    message: str
    col: int | None = None
    fixable: bool = False
    fix: Fix | None = None
    extra_fixes: list[Fix] = field(default_factory=list)  # additional edits for one finding

    def all_fixes(self) -> list[Fix]:
        fixes = [self.fix] if self.fix is not None else []
        fixes.extend(self.extra_fixes)
        return fixes


@dataclass
class RuleMeta:
    id: str
    category: str  # single letter: A, B, C, D, E, F, N
    severity: Severity
    fixable: bool
    fn: Callable[["Document"], list[Finding]]


# Ordered category labels for grouping in the report.
CATEGORY_LABELS = {
    "A": "Math (A)",
    "B": "Tables (B)",
    "C": "Structure (C)",
    "D": "Links & images (D)",
    "E": "Obsidian artifacts (E)",
    "F": "Front matter (F)",
    "N": "Obsidian callouts (N)",
}
CATEGORY_ORDER = list(CATEGORY_LABELS.keys())

REGISTRY: dict[str, RuleMeta] = {}


def rule(
    id: str,
    category: str,
    severity: Severity,
    fixable: bool = False,
) -> Callable[[Callable[["Document"], list[Finding]]], Callable[["Document"], list[Finding]]]:
    """Register a rule function in the global registry."""

    def deco(fn: Callable[["Document"], list[Finding]]) -> Callable[["Document"], list[Finding]]:
        if id in REGISTRY:
            raise ValueError(f"duplicate rule id: {id}")
        REGISTRY[id] = RuleMeta(id=id, category=category, severity=severity, fixable=fixable, fn=fn)
        return fn

    return deco


def effective_severity(rule_id: str, default: Severity) -> Severity:
    """Apply any user override from config for a rule's severity."""
    # Imported lazily to avoid a circular import (config imports Severity).
    from .config import SEVERITY_OVERRIDES

    return SEVERITY_OVERRIDES.get(rule_id, default)
