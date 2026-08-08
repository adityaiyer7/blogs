# Literature quote block

**Status:** active
**Last updated:** 2026-08-08
**PRs:** #55

**History:** shipped first as a movie-only block (`[!moviequote]` ->
`.movie-quote`, file `docs/design/movie_quote_block.md`). Generalized in the
same PR, before merge, to cover any quoted line worth remembering — movie,
book, poem, song — behind one shared block. This doc replaces that one; there
is no separate movie-only doc anymore.

## Problem

There was no good way to keep a running log of quoted lines — the line, the
source, and the date it was noted — that (a) still syncs from Obsidian like
every other post, (b) doesn't look like generic advice-box UI, and (c) isn't
locked to a single kind of source. The only formatting available for this was
a plain Markdown blockquote (`>`), which carries no structure for a title or
date, or an Obsidian `[!quote]` callout — which `config.py` already silently
maps to Quarto's `.callout-note`, giving it the exact same chrome as every
other note/tip/warning admonition on the site.

## Decision

Added a new Obsidian-callout conversion path, parallel to but independent of
the existing `[!note]`/`[!tip]`/etc. mapping in `N1`/`config.OBSIDIAN_TO_QUARTO`:

- A small table of Obsidian callout types, `config.LITERATURE_QUOTE_TYPES`:
  `[!moviequote]` -> "Movie", `[!bookquote]` -> "Book", `[!poemquote]` ->
  "Poem", `[!songquote]` -> "Song". Each is authored as
  `> [!<type>] <Title> — <YYYY-MM-DD>` followed by the quote as ordinary
  callout body lines. Adding a new kind (a TV show, a play, a speech) is one
  new dict entry — no other code change.
- A new `qmd_lint` rule category, `Q` (`tools/qmd_lint/rules/lit_quote_rules.py`),
  shared across every kind in the table:
  - `Q1` converts a well-formed callout into a `::: {.lit-quote}` fenced div
    containing a small `<div class="lit-quote-meta">` line (kind badge +
    source title + date, HTML-escaped) followed by the quote text left as a
    plain Markdown blockquote (`> ...`), so it still renders as `<blockquote>`.
  - `Q2` reports (never guesses at) a title that doesn't match
    `<Title> — YYYY-MM-DD` exactly.
- A dedicated `.lit-quote` CSS block in `blogposts/styles.css`: a bordered
  card with a small uppercase kind badge + source title + date on one line,
  and the quote itself set in larger italic serif type, no left-border
  blockquote styling. The kind badge deliberately reuses the same
  bordered-uppercase-pill look already used for `.listing-pinned-badge`
  elsewhere on the site, rather than inventing a second badge style.
- This runs automatically as part of `check_post.sh --fix`, which
  `sync_post.sh` already calls — no new script or manual step. Same syncing
  workflow as every other post.

## Alternatives considered

- **Reuse `[!quote]` → `.callout-note`.** Zero new code, but the result is
  visually indistinguishable from any other note callout — no room to show a
  title, a date, or which kind of source it came from.
- **Target one of Quarto's five native callout classes** (e.g. add
  `.callout-quote` to `QUARTO_CALLOUT_TYPES`). Native callout classes carry
  Quarto's own icon/color chrome by design (an admonition), which is the wrong
  visual language for "a line worth remembering" — rejected for the same
  reason as reusing `[!quote]`.
- **One `[!quote]` callout type with the kind spelled out in the title**
  (e.g. `The Dark Knight (movie) — 2026-08-08`) instead of one callout type
  per kind. Fewer keywords to remember, but needs a stricter three-part parse
  and the kind still has to be validated against a known set — no real
  parsing simplification over what's already built. A dict of callout types
  mirrors how `OBSIDIAN_TO_QUARTO` already maps many Obsidian aliases, needs
  no new parsing beyond a dict lookup, and each kind is one line to add.
- **A structured author/artist field** (separate from the title) for books,
  poems, and songs, which usually want an attributed author where a movie
  typically doesn't. Rejected: Obsidian callouts only carry a single title
  string after `[!type]`, and the title is free text anyway — an author can
  just be written into it directly (`Fahrenheit 451, Ray Bradbury —
  2026-08-08`) with no schema change and no extra field to remember.

## Behavior and contract

- Callout type must be one of the keys in `LITERATURE_QUOTE_TYPES`
  (case-insensitive), depth 1 (not nested — nested callouts of any type are
  already reported by `N5`).
- Title must be `<Title> — <YYYY-MM-DD>`, separated by an em dash (`—`) with a
  space on each side; the date must be strict ISO `YYYY-MM-DD`. This is what
  `Q1`'s regex anchors on, so it degrades safely even if the title itself
  contains a dash elsewhere.
- A malformed title is left as an unconverted Obsidian callout and reported
  (`Q1` non-fixable + `Q2` with the expected format) rather than guessed at or
  silently dropped.
- Kind label, title, and date are HTML-escaped before being written into the
  `<span>` elements, since they land in a raw HTML block inside the rendered
  `.qmd`.
- Quote body lines are carried through unchanged (still `>`-prefixed), so they
  render as a real Markdown blockquote inside the div — this is what lets the
  `.lit-quote blockquote` CSS rule target them.
- This is intended for one running "live" post (synced repeatedly from an
  Obsidian note), the same convention as `hundred-day-retrospective` — not a
  new post-per-quote workflow. Different kinds are expected to live in the
  same post, interleaved by whatever order they're added in Obsidian.

## Known gaps and follow-ups

- The `.lit-quote` div is not picked up by `N6`/`N9` (unclosed-callout /
  blank-line-around-callout), because the parser's callout-fence detector only
  tracks fences whose attrs contain `.callout-` or the literal substring
  `callout`. This is harmless for output produced by `Q1` (it always emits a
  balanced div with the right spacing), but a `.lit-quote` div written by hand
  directly in `index.qmd`, without going through one of the literature-quote
  callouts, gets no structural linting. Not fixed here since body edits made
  directly in `index.qmd` are already overwritten on the next sync (see
  `agent_instructions.md`) — there's no supported path that hand-writes this
  div directly.
- No post using this block exists yet; this PR only adds the conversion rule
  and the CSS. Creating the actual running post is a separate step.
