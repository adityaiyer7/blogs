# Design Docs

One doc per feature, named `<feature_name>.md`, recording the choices made while
building it. These exist for bookkeeping: six months on, the diff still shows
*what* changed, but only this folder shows *why* — and what was considered and
rejected along the way.

Not to be confused with `blogposts/docs/`, which is generated Quarto output.

## When a doc is required

Required for new features: new user-facing capabilities, new scripts or tools,
new `qmd_lint` rules, changes to a script's contract or defaults, new workflows,
and anything establishing a convention others must follow.

Skipped for trivial and non-feature PRs: typo and copy fixes, blog post content,
pure refactors, dependency bumps, and obvious bug fixes with no design choice.

The full rule, including what to do when you are unsure, is in
[`agent_instructions.md`](../../agent_instructions.md).

## Conventions

- **One doc per feature.** When the feature changes, update its doc in place and
  note what changed — do not add a second doc for the same feature.
- **Written in the same PR as the feature**, not afterwards.
- **Linked both ways:** the PR links the doc, the doc links the PR.
- Keep it short. A page of real reasoning beats five pages of restated diff.

## Template

```markdown
# <Feature name>

**Status:** active | superseded by `<doc>.md` | removed
**Last updated:** YYYY-MM-DD
**PRs:** #<n>

## Problem

What was broken, missing, or impossible before this. Be concrete — the symptom,
not the abstraction.

## Decision

What was built, and why this approach. The reasoning matters more than the
description; the code already describes itself.

## Alternatives considered

What else was on the table and why it was rejected. This is the section that
saves the most time later — it stops the next person from re-proposing a dead
end. Include options rejected for practical reasons, not just technical ones.

## Behavior and contract

What a user or caller can rely on: inputs, outputs, defaults, failure modes.
Anything deliberately left undefined should say so explicitly.

## Known gaps and follow-ups

What this does not handle, and what was consciously deferred. An empty section
is fine; a missing one reads as "nothing was left out", which is rarely true.
```
