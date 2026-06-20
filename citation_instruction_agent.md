# Citation Conversion — Agent Instructions

You are converting an author's lightweight citation tags into native Quarto/Pandoc
citations. The rendering machinery (CSL, hover, links) already lives in
`blogposts/_quarto.yml` and `blogposts/nature.csl` — **you do not touch render config.**
Your job is purely to transform a single post's `index.qmd` and create its `references.bib`.

Read this whole file before acting. When in doubt, **stop and report** rather than guess.

---

## 1. Trigger / scope

- Operate on exactly **one** post's `index.qmd` at a time (path:
  `blogposts/posts/<slug>/index.qmd`).
- Act **only if** the post's YAML front matter contains `inline-citations: true`.
  If the flag is absent or false, **do nothing** and report that the post is not flagged.
- **Never** modify any other file. In particular, never touch `_draft.md` (the author's
  un-converted source of truth), other posts, `_quarto.yml`, or the CSL file.

## 2. Input contract (what the author wrote)

- **Inline**, anywhere in the body prose:
  ```
  …features are packed in superposition {citation:toymodels}
  ```
  The `handle` (`toymodels`) is a short identifier chosen by the author.
- **Bottom of the post**, under a single `# Sources` heading, a markdown list mapping
  each handle to a readable title and a URL:
  ```
  # Sources
  - {toymodels}: [Toy Models of Superposition](https://transformer-circuits.pub/2022/toy_model/index.html)
  - {framework}: [A Mathematical Framework for Transformer Circuits](https://transformer-circuits.pub/2021/framework/index.html)
  ```

## 3. Transform steps

1. **Parse the `# Sources` list.** For each item extract: `handle`, readable `title`,
   and `url`.
2. **Create `blogposts/posts/<slug>/references.bib`** with one minimal entry per handle:
   ```bibtex
   @online{toymodels,
     title = {Toy Models of Superposition},
     url   = {https://transformer-circuits.pub/2022/toy_model/index.html}
   }
   ```
   - Use the **handle verbatim** as the BibTeX key.
   - Use **only** `title` and `url`, copied verbatim from the Sources list. You may add
     `urldate` only if the author supplied an access date; otherwise omit it.
   - **Do not invent** author, year, journal, publisher, or any other field.
3. **Replace every `{citation:handle}` in the body** with `[@handle]` (Pandoc citation
   syntax). Preserve surrounding spacing and punctuation exactly.
4. **Replace the `# Sources` list** with an empty bibliography div so the generated,
   numbered reference list renders under that heading:
   ```
   # Sources

   ::: {#refs}
   :::
   ```
   Remove the hand-written list items entirely. Keep **exactly one** `# Sources` heading.
5. **Add to the front matter** (only if you emitted ≥1 citation):
   ```yaml
   bibliography: references.bib
   ```
   (Path is relative to the post's `index.qmd`.) Leave `inline-citations: true` in place.

## 4. Hard boundaries

- **Do not edit prose.** Only swap tags, the Sources block, and front matter.
- **Do not convert ordinary markdown links.** Plain `[text](url)` links in the body are
  intentional and stay as-is — only `{citation:handle}` tags become citations.
- **Leave data tables and `<iframe>` embeds untouched** (e.g. the WandB/HF link tables and
  the feature-explorer iframe in the SAE post are not citations).
- **Never invent metadata** (see step 2).
- **Avoid leaving a bare `@word` in prose** — Pandoc may try to parse it as a citation.
  Your output should only contain `@handle` inside `[@handle]`.

## 5. Validation & failure handling

Before writing anything, cross-check handles:

- If a `{citation:handle}` in the body has **no matching entry** in the `# Sources` list →
  **stop and report** the orphan handle. Do not guess a URL.
- If a `# Sources` entry is **never cited** in the body → report it (the author may have
  forgotten the inline tag); proceed only after noting it (Pandoc will simply omit
  uncited entries from a numbered list, so an uncited entry will not appear).
- If **duplicate handles** appear in the Sources list → stop and report.
- A handle reused many times in the body is expected and correct — all map to the same
  `[@handle]` and will share one citation number.

After transforming, sanity-check that:
- there is exactly one `# Sources` heading immediately followed by the `::: {#refs} :::` div;
- the `#refs` div is the post's intended final reference location (not sitting above
  unrelated trailing sections);
- no `{citation:...}` tags remain;
- `references.bib` has one entry per distinct cited handle.

## 6. Report back

Summarize: which post, how many distinct sources, the handle→title mapping, any orphans /
uncited / duplicate warnings, and the files created/modified. Remind the author to skim the
diff before pushing (this transform is LLM-driven and not guaranteed deterministic).
