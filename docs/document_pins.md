# Pinned Posts — Design and Implementation Record

Implements [#24](https://github.com/adityaiyer7/blogs/issues/24). This is the
bookkeeping record for *why* pinning is built the way it is. Author-facing
instructions live in [`README.md`](../README.md#pinning-posts); this document
covers the decisions, the evidence behind them, and the things a future change
should be careful not to undo.

> **Note on the two `docs/` folders.** This file lives in `docs/` at the repo
> root, which holds project documentation. It is unrelated to
> `blogposts/docs/`, which is Quarto's rendered site output. Neither is
> deployed by `publish.yml` — that renders fresh and pushes to the `gh-pages`
> branch.

## What pinning does

A post opts in through its own front matter:

```yaml
pinned: true
pin-order: 10   # optional
```

Pinned posts sort above unpinned ones in the homepage listings. Pinning is
editorial metadata and is deliberately independent of `categories` (topical
tags), `kind` (post-type sections), and `date` (chronology).

Ordering, applied wherever pinning applies:

1. Pinned posts with an explicit `pin-order`, ascending
2. Pinned posts without a `pin-order`, by `date desc`
3. Unpinned posts, by `date desc`

## Decisions

### D1 — Defaults come from project metadata, not per-post front matter

**Decision.** `pinned` and `pin-order` defaults live in
`blogposts/_pin_defaults.yml`, registered under `metadata-files:` in
`_quarto.yml`. No post was edited, and `create_post.sh` was not touched.

**Why this was in question.** Quarto's multi-field listing sort needs the
fields to exist on every item. Posts that omit them have nothing to sort on,
and missing-field handling is not guaranteed to group cleanly. #40 established
that project-level metadata reaches a listing's `include:` filter — that is how
`sections-active` works — but `sort:` is a different code path, so it could not
be assumed.

**Evidence.** Tested first, before anything else was built, against Quarto
1.9.36. With `pinned: false` supplied *only* as project metadata and
`pinned: true` added to one post's front matter, that post moved from last
position to first. Two things follow: project metadata is visible to `sort:`,
and document front matter correctly overrides it.

This was confirmed a second way. A throwaway EJS listing template printing
`item.pinned` and `item['pin-order']` showed `pinned="false"`
`pinorder="999999"` on every post that declared neither — the defaults are
genuinely present on each item, not merely honoured by the comparator.

**Consequence.** The change is a few lines of configuration rather than a
backfill across every post plus the creation script.

### D2 — `pin-order` defaults to a sentinel, not to nothing

**Decision.** `_pin_defaults.yml` sets `pin-order: 999999`.

**Why.** It collapses all three ordering rules into one native sort:

```yaml
sort: ["pinned desc", "pin-order asc", "date desc"]
```

A pinned post with no `pin-order` inherits the sentinel, which under
`pin-order asc` places it after every explicitly numbered pin, where
`date desc` then orders it. Unpinned posts all carry the sentinel too, so they
also fall through to `date desc`. No special-casing, no client-side
reordering, and no branch anywhere for the "nothing is pinned" case.

**Constraint this imposes.** Do not use a `pin-order` at or above the
sentinel. Real values should stay far below it — the gap convention (10, 20,
30) leaves plenty of room.

### D3 — `pin-order` is compared numerically

**Verified, not assumed.** Two posts were pinned with `pin-order: 20` and
`pin-order: 100`. They rendered in that order. A lexicographic comparison
would have inverted them, since `"100" < "20"` as strings. Authors can
therefore use natural numbers without zero-padding.

### D4 — RSS stays chronological, and needed no structural change

**Decision.** `feed: true` stays on the `all-posts` listing. No separate
feed-only listing was added.

**Why this looked like a problem.** The feed rides on the same listing that
pinning primarily targets, so a pin-aware sort there looked certain to reorder
the feed — which would contradict the requirement in #35 that RSS ordering
stay chronological.

**Evidence that it is not.** The feed does not currently generate at all:
Quarto warns `Unable to create a feed as the required 'site > title' property
is missing`, and no `index.xml` has ever been produced. To settle the question
rather than reason about it, `website.title` was temporarily added, the site
rendered, and `index.xml` inspected. The page rendered in pin order while the
feed came out in pure `date desc`. **Quarto builds the feed in date order
regardless of the listing's display sort.** The probe was then reverted.

So RSS is chronological by construction. If `website.title` is added later and
the feed starts generating, pinning will not disturb it. Re-check this if
Quarto's feed generation changes.

### D5 — The badge is injected after render, not rendered by a custom template

**Decision.** `blogposts/scripts/inject_pin_badges.py` runs as a Quarto
`post-render` step and inserts one `<div class="listing-pinned-badge">Pinned</div>`
into the cards of pinned posts. Styling lives in `blogposts/styles.css`.

**This deviates from #24**, which proposed a custom EJS listing template. The
deviation is deliberate and is the one judgement call in this change worth
revisiting if circumstances change.

**Why the built-in listing cannot do it.** Adding `pinned` to a listing's
`fields:` renders nothing. Quarto's default listing draws a fixed field set
and silently ignores custom ones — `pinned` is registered in the search
`valueNames` and nowhere else. There is also no DOM hook to hang CSS on:
Quarto emits `data-listing-<field>-sort` attributes only for its own sortable
fields (`date`, `file-modified`, `date-modified`, `reading-time`,
`word-count`), never for custom metadata. A CSS-only badge is therefore not
possible either.

**Why not the EJS template.** A probe template showed that a custom template
does not fill in the card interior — it *replaces* the card entirely. Quarto
stops emitting the `quarto-post` wrapper and its payload, including the
base64 `data-categories` attribute and the `quartoListingCategory` click
handler that the category filter depends on. Matching today's output would
mean reimplementing the card — title, description, categories, date,
reading-time — across all five listings, and then keeping it in step with
Quarto's listing JS. #24 explicitly warns against depending on
version-specific behaviour, and CI runs `quarto-dev/quarto-actions/setup@v2`
unpinned, installing whatever release is current. A hand-rolled template is
precisely that dependency.

Post-render injection inverts the risk. Every byte of Quarto's own markup
survives; the script adds one element and touches nothing else. Its coupling
is limited to the `quarto-post` wrapper and the post link inside it.

**Failure mode, and the guard.** The obvious objection to patching HTML is
that it can silently stop matching. So the script raises if a page contains
`quarto-post` markup but yields no parsed cards, which is what a Quarto markup
change would look like. It is also idempotent, so reprocessing cannot
double-badge. Both behaviours are covered in `tests/test_pin_badges.py`.

**If this is revisited.** The natural trigger is #35: if a custom template
gets built for series labels anyway, the badge should move into it rather than
two mechanisms coexisting. #24 makes the same point in reverse — do not build
two separate templates for the same cards.

### D6 — Shipped with nothing pinned

No post carries pin metadata on merge. The mechanism is live; pinning is an
editorial act taken whenever wanted. Verified that with nothing pinned the
rendered homepage is unchanged apart from the inert badge CSS.

### D7 — `create_post.sh` untouched

Pinning is a post-hoc editorial decision, not a property known when a post is
created, so there is no prompt and no default written into new posts. Posts
inherit `pinned: false` from project metadata, so nothing needs to be written
at creation time for the sort to work. This follows #24 directly.

## Interaction with existing behaviour

**Kind visibility wins.** A pinned post whose `kind` is disabled stays hidden.
Pinning is a sort; visibility is enforced upstream by Quarto drafts generated
into `_hidden_posts.yml`. Verified: with `misc` disabled, a pinned `misc` post
appeared in no listing and received no badge.

**Both layouts.** The same sort is on all five listings. In the chronological
`all-posts` view pins are global across topics; in the sectioned view they
apply independently inside each kind, and the fixed section order is
unaffected because it comes from document structure, not from the listings.

**Out of scope.** Series listings (#35) are not pinned — a series is
sequential and ordered by `series-order asc`. Pin metadata and series metadata
may coexist on a post. Reader-controlled pin toggling is #41.

## Verification performed

Against Quarto 1.9.36, reading the rendered `blogposts/docs/index.html`
directly rather than eyeballing a preview:

| Case | Result |
| --- | --- |
| Nothing pinned | Homepage semantically identical to baseline; `date desc` throughout |
| One post pinned, no `pin-order` | Oldest post moved to the top |
| `pin-order` 20 vs 100 | Ordered 20 then 100 — numeric, not lexicographic |
| Mixed numbered and unnumbered pins | Numbered first, then unnumbered by `date desc`, then unpinned by `date desc` |
| All pins unnumbered | Pins in `date desc`, above unpinned in `date desc` |
| Two kinds enabled | Pins applied per section; section order unchanged |
| Pinned post in a disabled kind | Hidden, no badge |
| Feed ordering | `date desc` while the page was in pin order |
| Search index, sitemap, post pages | Unchanged |

## Known fragilities

- **`tests/test_real_posts.py` asserts hardcoded line numbers.** Adding
  `pinned:` to a post's front matter shifts every line below it and breaks
  those assertions. This is pre-existing and unrelated to pinning, but pinning
  a post is now a likely way to trigger it. Whoever pins a post first will
  need to bump those line numbers.
- **The injector tracks Quarto's card markup.** Guarded by the loud failure
  described in D5, but a Quarto upgrade that restructures listing cards will
  need `CARD_RE` updated.
