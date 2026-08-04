# Agent Instructions

Repository-wide working agreement for AI coding agents. It is model-agnostic:
`AGENTS.md` and `CLAUDE.md` at the repository root are thin pointers to this
file so that whichever tool auto-loads its own filename still lands here. **This
file is the single source of truth.** If a pointer file and this file ever
disagree, this file wins and the pointer should be fixed.

Read this before your first edit in a session.

## Scope and precedence

Supplemental instruction files cover specific domains. They add detail within
their domain; they do not override anything here.

| File | Applies to |
| --- | --- |
| `agent instructions/marimo_instructions.md` | Installing, authoring, exporting, or publishing marimo applications |
| `citation_instruction_agent.md` | Converting a post's `{citation:handle}` tags into Quarto/Pandoc citations |
| `citation_instruction_user.md` | The authoring convention behind the above (human-facing, read for context) |

To add a new supplemental file: put it next to its peers, and add a row to the
table above. A supplemental file that nothing points to will not be found.

## Repository map

This started as a blog and grew into a small writing platform. Knowing which
parts are authored and which are generated prevents most of the damage an agent
can do here.

- `blogposts/` — the Quarto site **source**. Posts live in
  `blogposts/posts/<slug>/index.qmd`, with images under `assets/imgs/`.
- `blogposts/docs/` — **generated output.** Produced by `quarto render`
  (`output-dir: docs`). It is committed, but it is never hand-edited. If it
  looks wrong, fix the source and re-render.
- `blogposts/posts/<slug>/_draft.md` — the author's original Obsidian draft,
  preserved verbatim. Never edit it; it is the upstream source, not a copy.
- `*.sh` at the root — the author-facing scripts (`create_post.sh`,
  `sync_post.sh`, `check_post.sh`, `delete_post.sh`, `export_pdf.sh`), with
  shared helpers in `tools/post_lib.sh`.
- `tools/qmd_lint/` — the `.qmd` format checker behind `check_post.sh`. Rules in
  `tools/qmd_lint/rules/`, tunable thresholds in `tools/qmd_lint/config.py`.
- `tests/` — pytest suite for the tooling. Run with `uv run pytest`.
- `docs/design/` — design docs for features (see below). Unrelated to
  `blogposts/docs/`; do not confuse the two.
- `.github/workflows/` — `publish.yml` renders and deploys on pushes to `master`
  that touch `blogposts/**`, `pyproject.toml`, `uv.lock`, or itself.
  `pr-review.yml` runs an automated review on every PR.
- `llm_work_flows/`, `llm-from-scratch/` — **deprecated**, unmaintained. Do not
  extend them, and do not use them as a pattern to copy.

`README.md` is the human-facing guide to the scripts and their behavior. When
you change a script's user-visible behavior, update `README.md` in the same PR.

## Branch naming

Branch off `master`. One branch per logical change.

Rules:

1. **No tool or model prefixes.** Not `claude/`, not `codex/`, not `ai/`,
   not `bot/`. The branch describes the work, not what produced it.
2. **No random suffixes.** No session IDs or hashes appended to the name.
3. **Describe the problem being solved**, not the shape of the edit. Someone
   reading `git log` a year from now should be able to guess what the branch was
   for without opening the diff.
4. **Lowercase kebab-case.**
5. **If an issue is linked in the conversation, lead with it:**
   `issue-<number>-<short-description>`.

| Good | Bad | Why |
| --- | --- | --- |
| `issue-13-sync-post-asset-collisions` | `claude/sync-post-asset-collisions-fgfo45` | Tool prefix and session suffix carry no information |
| `reading-group-session-7-visualization` | `update-stuff` | Says nothing about the problem |
| `qmd-lint-callout-conversion` | `fix` | Same |
| `issue-40-homepage-section-visibility` | `issue-40` | The number alone is not readable in a branch list |

The existing history contains branches that violate this. It predates the
convention — follow the rules above, not the history.

## Commits

- Imperative mood, present tense: "Route incoming top-level images into
  `assets/imgs/` during sync".
- Explain **why** in the body when the reason is not obvious from the diff.
- Do not put model names, agent names, tool identifiers, or session URLs in
  commit messages.
- Keep unrelated changes in separate commits.

## Pull requests

Write the PR for **a future agent doing git archaeology**, not for a reviewer
who already has the context of this conversation. That reader has the diff and
nothing else — the PR body is where the reasoning has to survive.

A PR body should cover:

- **Problem** — the symptom or gap, concretely. What went wrong, or what was
  impossible before.
- **Approach** — what you did and why this way.
- **Alternatives considered** — what you rejected and the reason. This is
  frequently the most valuable part later; it stops the next agent from
  re-proposing something already ruled out.
- **Scope** — anything deliberately left out, and any known gaps.
- **Verification** — what you ran (tests, `check_post.sh`, a local render) and
  what it showed. State failures plainly rather than omitting them.
- **Links** — `Closes #<n>` when an issue exists, plus a link to the design doc
  when one was added.

The title follows the same standard as the branch name: describe the problem or
the behavior change. "Update sync script" and "Fixes" are not acceptable titles;
"Resolve asset basename collisions during post sync" is.

Do not open a PR unless the human asks for one. Never push directly to `master`.

## Design docs

**Every PR that adds a feature also adds a design doc**, in the same PR. The
point is bookkeeping: capturing the choices made while the reasoning is still
available, so the next person or agent inherits it instead of reconstructing it.

**Location:** `docs/design/<feature_name>.md` — lowercase snake_case or
kebab-case filename matching the feature, one doc per feature. When a feature
evolves, **update its existing doc in place** and note the change; do not add a
second doc for the same feature.

**Required for:** new user-facing capabilities, new scripts or tools, new
rules/checks in `qmd_lint`, changes to a script's contract or defaults, new
workflows, and anything that establishes a convention others must follow.

**Skip for:** typo and copy fixes, blog post content, pure refactors with no
behavior change, dependency bumps, and bug fixes where the fix is the obvious
one and no design choice was made. When you skip, say so in the PR body in one
line and why.

If you are unsure whether something is a feature, write the doc. A short doc
costs little; a missing one costs the reasoning permanently.

The template and required sections live in `docs/design/README.md`. Link the doc
from the PR, and link the PR from the doc.

## Testing policy

Run `uv run pytest` from the repository root. Tests live in `tests/`.

**Tests are expected for:** changes to `tools/qmd_lint/` (every rule change needs
a case that fails before the change and passes after), changes to the logic in
the `*.sh` scripts, and any bug fix in tooling — the regression test comes with
the fix.

**Tests are not expected for:** blog post content, front matter and config
toggles, `README.md` and documentation, and rendered output.

Do not add tests speculatively. Before adding a test file, be able to state in
one sentence what regression it prevents; if you cannot, do not add it. Do not
weaken or delete an existing assertion to make a suite pass — if an assertion is
genuinely stale, say so explicitly in the PR and explain why.

Report results honestly. If tests fail, show the output; if you skipped a check,
say which one.

## Working with posts

- **Post prose belongs to the author.** Do not rewrite, restructure, or
  "improve" a post's writing unless asked. Fix mechanical and formatting issues
  only.
- `_draft.md` is Obsidian's copy and is never edited here. For synced posts,
  body edits made directly in `index.qmd` are overwritten on the next sync — the
  fix belongs upstream in Obsidian.
- After touching a post, run `./check_post.sh <slug>` and resolve what it
  reports. `--fix` applies only the safe deterministic fixes; anything needing
  judgment is reported for a human.
- Never hand-edit anything under `blogposts/docs/`. Regenerate with
  `quarto render` from `blogposts/`.
- A local render is required to preview accurately — CI renders on push to
  `master`, but that does not help anything you are checking locally.

## Working agreements

- Ask before installing packages or adding dependencies. Run installs in the
  foreground.
- Do not create scratch or backup files inside the repository. Write to the
  final intended paths; use a temp directory outside the repo for working files.
- Do not commit generated artifacts beyond what the repo already tracks, and
  never commit PDFs, `.env` files, or credentials.
- Deprecated directories stay deprecated. Do not modernize them incidentally.
- Stay in scope. If you find an unrelated problem, mention it rather than
  fixing it in the same PR.
