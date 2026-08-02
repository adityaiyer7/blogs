"""Command-line interface for the qmd linter."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .config import POST_DIR_TEMPLATE, POSTS_GLOB
from .engine import collect_findings, fix_document
from .model import Finding, Severity
from .parser import parse
from .report import format_file_report, format_json
from .util import find_repo_root

_SLUG_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _resolve_targets(targets: list[str], repo_root: Path) -> list[Path]:
    if not targets:
        return sorted(repo_root.glob(POSTS_GLOB))
    paths: list[Path] = []
    for t in targets:
        if t.endswith(".qmd"):
            paths.append(Path(t).resolve())
        elif _SLUG_RE.match(t):
            paths.append((repo_root / POST_DIR_TEMPLATE.format(slug=t)).resolve())
        else:
            print(f"error: invalid target {t!r} (expected a slug or a .qmd path)", file=sys.stderr)
            raise SystemExit(2)
    return paths


def _split_csv(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {tok.strip() for tok in value.split(",") if tok.strip()}


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _exit_code(findings: list[Finding], strict: bool) -> int:
    if any(f.severity == Severity.ERROR for f in findings):
        return 1
    if strict and any(f.severity == Severity.WARNING for f in findings):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="qmd_lint",
        description="Deterministic format checker for Quarto blog posts.",
    )
    parser.add_argument("targets", nargs="*", help="post slug(s), .qmd path(s), or nothing for all posts")
    parser.add_argument("--fix", action="store_true", help="apply safe fixes without prompting")
    parser.add_argument("--check", action="store_true", help="report only; never prompt (CI mode)")
    parser.add_argument("--strict", action="store_true", help="warnings also cause a non-zero exit")
    parser.add_argument("--only", help="comma-separated rule ids or category letters to run")
    parser.add_argument("--skip", help="comma-separated rule ids or category letters to skip")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="output format")
    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    only = _split_csv(args.only)
    skip = _split_csv(args.skip)

    paths = _resolve_targets(args.targets, repo_root)
    missing = [p for p in paths if not p.is_file()]
    for p in missing:
        print(f"error: file not found: {_rel(p, repo_root)}", file=sys.stderr)
    paths = [p for p in paths if p.is_file()]
    if not paths:
        return 2

    results: dict[Path, list[Finding]] = {}
    for path in paths:
        results[path] = collect_findings(parse(path), only=only, skip=skip)

    if args.format == "json":
        print(format_json({_rel(p, repo_root): f for p, f in results.items()}))
        all_findings = [f for fs in results.values() for f in fs]
        return _exit_code(all_findings, args.strict)

    blocks = [format_file_report(_rel(p, repo_root), results[p]) for p in paths]
    print("\n\n".join(blocks))

    all_findings = [f for fs in results.values() for f in fs]
    fixable_count = sum(1 for f in all_findings if f.fixable)

    should_fix = False
    if args.check:
        should_fix = False
    elif args.fix:
        should_fix = fixable_count > 0
    elif fixable_count > 0 and sys.stdin.isatty():
        try:
            answer = input(f"\nAuto-fix {fixable_count} fixable issue(s)? [y/N] ").strip().lower()
        except EOFError:
            answer = ""
        should_fix = answer in ("y", "yes")

    if should_fix:
        print()
        remaining_all: list[Finding] = []
        for path in paths:
            applied, remaining = fix_document(path)
            remaining_all.extend(remaining)
            if applied:
                print(f"{_rel(path, repo_root)}: applied {applied} fix(es)")
        leftover = [f for f in remaining_all if f.fixable]
        manual = len(remaining_all) - len(leftover)
        print(f"\nDone. {len(remaining_all)} issue(s) remain ({manual} need manual attention).")
        return _exit_code(remaining_all, args.strict)

    return _exit_code(all_findings, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
