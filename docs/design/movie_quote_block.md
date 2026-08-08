# Movie quote block

**Status:** active
**Last updated:** 2026-08-08
**PRs:** (none yet — add the PR link when this is opened)

## Problem

There was no good way to keep a running log of movie quotes (the line, the
movie, and the date it was seen) that (a) still syncs from Obsidian like every
other post, and (b) doesn't look like generic advice-box UI. The only
formatting available for this was a plain Markdown blockquote (`>`), which
carries no structure for the movie name or date, or an Obsidian `[!quote]`
callout — which `config.py` already silently maps to Quarto's `.callout-note`,
giving it the exact same chrome as every other note/tip/warning admonition on
the site.

## Decision

Added a sixth Obsidian-callout conversion path, parallel to but independent of
the existing `[!note]`/`[!tip]`/etc. mapping in `N1`/`config.OBSIDIAN_TO_QUARTO`:

- A new Obsidian callout type, `[!moviequote]` (`config.MOVIE_QUOTE_OBSIDIAN_TYPE`),
  authored as `> [!moviequote] <Movie> — <YYYY-MM-DD>` followed by the quote as
  ordinary callout body lines.
- A new `qmd_lint` rule category, `Q` (`tools/qmd_lint/rules/movie_quote_rules.py`):
  - `Q1` converts a well-formed callout into a `::: {.movie-quote}` fenced div
    containing a small `<div class="movie-quote-meta">` line (movie title +
    date, HTML-escaped) followed by the quote text left as a plain Markdown
    blockquote (`> ...`), so it still renders as `<blockquote>`.
  - `Q2` reports (never guesses at) a title that doesn't match
    `<Movie> — YYYY-MM-DD` exactly.
- A dedicated `.movie-quote` CSS block in `blogposts/styles.css`: a bordered
  card with the movie title and date on one line and the quote itself set in
  larger italic serif type, no left-border blockquote styling.
- This runs automatically as part of `check_post.sh --fix`, which
  `sync_post.sh` already calls — no new script or manual step. Same syncing
  workflow as every other post.

## Alternatives considered

- **Reuse `[!quote]` → `.callout-note`.** Zero new code, but the result is
  visually indistinguishable from any other note callout — no room to show the
  movie name or date, and no way to give the block its own identity.
- **Target one of Quarto's five native callout classes (e.g. add
  `.callout-quote` to `QUARTO_CALLOUT_TYPES`).** Native callout classes carry
  Quarto's own icon/color chrome by design (an admonition), which is the wrong
  visual language for "a line worth remembering" — rejected for the same
  reason as reusing `[!quote]`.
- **Parse `<Movie>` and `<date>` as separate Obsidian callout metadata fields**
  (e.g. two lines, or a nested structure) instead of one delimited title.
  Obsidian callouts only carry a single title string after `[!type]`, so
  anything more structured would need hand-written HTML/comments in the vault
  note — worse authoring ergonomics for no real gain. A single ` — `-delimited
  title, parsed with a regex anchored on the trailing ISO date, is simple to
  type and unambiguous to parse even if a movie title itself contains a dash.

## Behavior and contract

- Callout type must be exactly `moviequote` (case-insensitive), depth 1 (not
  nested — nested callouts of any type are already reported by `N5`).
- Title must be `<Movie Title> — <YYYY-MM-DD>`, separated by an em dash (`—`)
  with a space on each side; the date must be strict ISO `YYYY-MM-DD`. This is
  what `Q1`'s regex anchors on, so it degrades safely even if the movie title
  itself contains a dash elsewhere.
- A malformed title is left as an unconverted Obsidian callout and reported
  (`Q1` non-fixable + `Q2` with the expected format) rather than guessed at or
  silently dropped.
- Movie title and date are HTML-escaped before being written into the
  `<span>` elements, since they land in a raw HTML block inside the rendered
  `.qmd`.
- Quote body lines are carried through unchanged (still `>`-prefixed), so they
  render as a real Markdown blockquote inside the div — this is what lets the
  `.movie-quote blockquote` CSS rule target them.
- This is intended for one running "live" post (synced repeatedly from an
  Obsidian note), the same convention as `hundred-day-retrospective` — not a
  new post-per-quote workflow.

## Known gaps and follow-ups

- The `.movie-quote` div is not picked up by `N6`/`N9` (unclosed-callout /
  blank-line-around-callout), because the parser's callout-fence detector only
  tracks fences whose attrs contain `.callout-` or the literal substring
  `callout`. This is harmless for output produced by `Q1` (it always emits a
  balanced div with the right spacing), but a `.movie-quote` div written by
  hand directly in `index.qmd`, without going through the `[!moviequote]`
  callout, gets no structural linting. Not fixed here since body edits made
  directly in `index.qmd` are already overwritten on the next sync (see
  `agent_instructions.md`) — there's no supported path that hand-writes this
  div directly.
- No post using this block exists yet; this PR only adds the conversion rule
  and the CSS. Creating the actual running post is a separate step.
