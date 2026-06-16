# Inline Citations — Author Guide

This blog supports academic-style **inline citations**: a source reference renders as a
small **superscript number**. Clicking the number jumps to a reference entry at the bottom
of the post (which has the clickable link), and hovering shows a preview of the source.

You keep writing plain markdown in Obsidian — no special plugins needed. A short tag
convention plus a one-step agent pass after import does the rest. The rendering itself is
handled automatically by Quarto (configured once in `blogposts/_quarto.yml` +
`blogposts/nature.csl`); you never touch that.

---

## The convention

### 1. Turn the feature on (per post)

Add this to the post's YAML front matter:

```yaml
inline-citations: true
```

Posts without this flag are completely unaffected — nothing changes for them.

### 2. Cite inline

Wherever you reference a source, drop a tag using a short handle you choose:

```markdown
Neural nets pack more features than dimensions via superposition {citation:toymodels}.
```

- Pick short, memorable handles (`toymodels`, `framework`, `gpt2arch`).
- **Reuse freely** — using `{citation:toymodels}` five times is fine; they all collapse to
  the same number.

### 3. List your sources at the bottom

Under a single `# Sources` heading, map each handle to a readable title and a URL:

```markdown
# Sources

- {toymodels}: [Toy Models of Superposition](https://transformer-circuits.pub/2022/toy_model/index.html)
- {framework}: [A Mathematical Framework for Transformer Circuits](https://transformer-circuits.pub/2021/framework/index.html)
```

- The **readable title** is what appears in the rendered reference list.
- The **URL** becomes the clickable link in that entry.
- **Don't hand-number.** The final printed numbers follow the order sources first appear in
  your prose, not the order of this list — so your list order doesn't matter.

## The workflow end-to-end

1. In Obsidian, write the post with `{citation:handle}` tags + a `# Sources` list, and set
   `inline-citations: true` in the front matter.
2. Import it: `./create_post.sh "My Post" /path/to/draft.md`
3. Run the citation agent on the new post (it follows `citation_instruction_agent.md`). It
   builds `references.bib`, swaps your tags to Pandoc citations, and replaces the Sources
   list with an auto-generated reference list.
4. **Skim the diff.** The conversion is LLM-driven, so glance over it before pushing — check
   every tag mapped and your prose is untouched. Your original draft is preserved as
   `_draft.md` if you ever need to start over.
5. Push to `master`. CI renders the post with superscripts, hover previews, and the numbered
   reference list.

## What renders

- Inline: a superscript number (e.g. ¹).
- Click the number → scrolls to the matching entry under **Sources**.
- That entry shows the title and a clickable URL.
- Hover the number → a small preview popup of the source.

## Good to know

- **Ordinary links still work.** Regular `[text](url)` links in your prose are left alone —
  use them for normal hyperlinks and reserve `{citation:handle}` for things you want cited.
- **Tables and embeds are not citations.** Link-heavy tables (e.g. run/dataset link tables)
  and `<iframe>` embeds stay as plain links by design.
- **Every tag needs a Sources entry** (and vice versa). If a handle is missing from the
  Sources list, the agent will stop and tell you instead of guessing.
- **No invented metadata.** Reference entries use only the title and URL you provide, so
  nothing is fabricated. (If you want author/year shown, that's a future enhancement.)
