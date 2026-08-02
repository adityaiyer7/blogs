## Authoring Blog Posts

This repository contains a simplified directory structure for generating blog content using Quarto under `blogposts/`.

To create a new blog post, use the included helper script from the root of the repository:

```bash
./create_post.sh "my-post-name"
```
Or to automatically import an existing Markdown draft:
```bash
./create_post.sh "my-post-name" "/path/to/your/draft.md"
```
Or to import a whole **project directory** (a single `.md` plus an `assets/` folder), copying the assets across and rewriting Obsidian image embeds automatically:
```bash
./create_post.sh "my-post-name" --project "/path/to/your/project-dir"
```

**What the script does:**
1. It creates a new folder for the post under `blogposts/posts/<post-slug>/`.
2. It sets up an isolated assets folder `assets/imgs/`.
3. It prompts for a post type (`full-research`, `mini-research`, `explanatory`, or `misc`) that determines the post's homepage section, separately from topical categories such as `Interpretability`.
4. If you provided a path to a draft `.md` file, it copies the `.md` file into the folder as `_draft.md` (to preserve your original work), appends the contents into an `index.qmd` file with pre-filled YAML front matter, and normalizes the result for Quarto (inserts blank lines before `#` headings when missing—common after tables in Obsidian exports).
5. If no `.md` draft is provided, it simply creates a starter `index.qmd` file with pre-filled front matter.

**Project mode (`--project <dir>`):** point the script at a directory that contains exactly one top-level `.md` file and an `assets/` folder. In addition to the draft-import behavior above, it:
- mirrors the source `assets/` tree into the post's `assets/` folder, preserving any subfolders (`imgs/`, `diagrams/`, …) and routing top-level images into `assets/imgs/` (see [Where images land](#where-images-land));
- rewrites Obsidian image embeds — `![[image.png]]` and `![[image.png|caption]]` — into working Quarto links like `![](assets/imgs/image.png)`, resolving each file by basename against the copied assets;
- leaves an embed untouched and prints a warning if no matching asset is found, or if the same filename exists in multiple folders (ambiguous) — nothing is silently dropped or guessed.

The original draft is always preserved verbatim in `_draft.md`; the rewrite only applies to the generated `index.qmd`.

Inside your newly generated `index.qmd`, you can include manually copied images using the relative path `![](assets/imgs/your-image.png)`.

### Syncing a Live Post

For a post you keep editing in Obsidian (e.g. a "live" document), `create_post.sh` is a one-time import — re-running it errors because the post already exists. To pull later Obsidian edits back into an existing post, use the sync script:

```bash
./sync_post.sh my-post-slug --project "/path/to/your/project-dir"
```

The `--project` directory is the same shape as in project mode: exactly one top-level `.md` file plus an optional `assets/` folder.

**What the script does:**
1. Overwrites `_draft.md` with the latest Obsidian draft.
2. Re-mirrors the source `assets/` tree into the post's `assets/` folder, one file at a time — routing top-level images into `assets/imgs/` (see [Where images land](#where-images-land)) and asking what to do whenever an incoming filename already exists elsewhere in the post (see [Asset name collisions](#asset-name-collisions)).
3. Regenerates the **body** of `index.qmd` from the fresh draft, re-running the same Obsidian-embed rewriting and heading normalization as `create_post.sh`.
4. Runs `check_post.sh <slug> --fix` to apply the safe, deterministic fixes (Obsidian ` ```mermaid ` blocks → Quarto ` ```{mermaid} `, `[!NOTE]`-style callouts → `::: {.callout-note}`, etc.) so the regenerated body is render-ready, not just re-imported.

**What it preserves and overwrites:**
- The existing YAML **frontmatter** in `index.qmd` (title, date, categories, …) is preserved untouched — it is repo-managed and is *not* re-derived from Obsidian. The `date:` field is not auto-bumped.
- The post **body** is fully regenerated from the Obsidian source on every sync. Obsidian is the single source of truth for body content, so any manual edits made directly to the `index.qmd` body will be overwritten — make body changes in Obsidian, not in `index.qmd`.

**Caveat:** the asset sync is additive. Images removed in Obsidian are not deleted from the post's `assets/` folder; remove those manually if you want them gone.

#### Where images land

Obsidian vaults usually keep images flat at the top of `assets/`, but posts in this repo expect them under `assets/imgs/` — `check_post.sh` reports anything else as a `D2` warning, and `D2` is one it cannot fix for you (a fix would have to move the file, not just edit a line). So both scripts route on the way in: an image sitting at the top level of the source `assets/` folder is written to `assets/imgs/` instead, and the embed rewrite picks up the new path on its own. Sync a post whose Obsidian assets are flat and you get `![](assets/imgs/tube.png)` with no manual move or path fixup afterwards.

Two things are deliberately left alone:

- **Files already in a subfolder.** `assets/diagrams/flow.png` stays in `diagrams/`; routing never reorganizes a layout you chose.
- **Non-images.** Only `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`, `.avif`, `.bmp`, `.tif`, and `.tiff` move, so build inputs that belong flat next to the images they generate (the `.tex`/`.aux`/`.dvi`/`.log` sources in `attention-mechanism`, for example) keep their place.

A post synced before routing existed cleans itself up on its next sync: the flat copy left behind is removed once the routed copy is written.

#### Asset name collisions

Embeds are resolved by *basename*, so the same filename living in two different folders inside a post makes `![[image.png]]` unresolvable — the embed is left as-is and `check_post.sh` reports it as a non-fixable `E1`. Routing handles the common flat-vs-`imgs/` version of this, but it can still happen when the same filename exists in some *other* folder — say `assets/diagrams/diagram.png` in the repo while Obsidian ships `diagram.png` at the top level.

The sync detects that case per file and resolves it instead of stacking duplicates:

- **Identical files need no decision.** If the incoming file is byte-for-byte the same as the one already in the post, the existing copy wins silently and any leftover duplicate from an earlier sync is cleaned up.
- **Otherwise you're asked**, once per collision:

  ```
  ⚠️  Asset name collision: 'diagram.png'
        incoming (Obsidian): assets/imgs/diagram.png
        existing (repo):     assets/diagrams/diagram.png
     a) Override      — write the Obsidian version into assets/diagrams/diagram.png
     b) Keep existing — discard the incoming copy
     c) Keep both     — leaves the embed unresolved (E1) for manual fixup
  Choose [a/b/c] (A/B/C applies to all remaining):
  ```

  Answering with a capital `A`, `B`, or `C` applies that choice to every remaining collision in the run.

Note that **override writes into the *existing* path**, so the post keeps whatever layout you chose for that file while still picking up the newer bytes from Obsidian.

One case is never resolved for you: if the routed target *and* another folder both already hold the filename, the post is ambiguous in a way no policy can settle without guessing. The incoming file is written to `assets/imgs/` as an ordinary update, the other copies are listed and left untouched, and the `E1` is yours to resolve.

To skip the prompt — in a script, or to fix a whole reorganized post in one pass — pass a policy up front:

```bash
./sync_post.sh my-post-slug --project "/path/to/dir" --on-collision override
```

`--on-collision` accepts `ask` (the default), `override`, `keep-existing`, and `keep-both`. When there's no terminal to prompt on (piped input, CI), `ask` falls back to `keep-both` with a warning, which is the old additive behavior.

Collisions the sync *can't* resolve are still reported rather than guessed at: if a basename already exists at more than one path inside the post, every copy is left in place for you to sort out by hand.

#### Always render after syncing

`sync_post.sh` only rewrites the `.qmd` source — it never touches `docs/`. **You must run `quarto render` (or `quarto preview`) after every sync** to regenerate the HTML, even if you only want to preview locally:

```bash
./sync_post.sh my-post-slug --project "/path/to/your/project-dir"
cd blogposts && quarto render   # or: quarto preview
```

This matters even when the `.qmd` source already looks correct. Quarto decides whether to inject diagram-rendering JS (e.g. for ` ```{mermaid} ` blocks) at render time, based on what's in the source *at that render*. If `docs/` was last rendered before a post had `` ```{mermaid} `` syntax, the stale HTML page will be missing that script — its Mermaid diagrams will silently show up as plain text instead of rendered diagrams, with no error anywhere. Re-rendering after every sync is what keeps `docs/` consistent with the source. (Pushing to `master` has CI render for you — see "Previewing and Publishing" below — but anything you check locally needs an explicit render first.)

### Inline Citations

Posts can render source references as academic-style superscript citations (click to jump to a numbered reference list, hover for a preview). This is opt-in per post via `inline-citations: true` in the front matter. See [`citation_instruction_user.md`](citation_instruction_user.md) for the authoring convention, and [`citation_instruction_agent.md`](citation_instruction_agent.md) for the agent that performs the conversion after import.

### Showing and Hiding Post Sections

Homepage sections have publish-time visibility switches in `blogposts/_post_visibility.yml`:

```yaml
post-kind-visibility:
  full-research: true
  mini-research: true
  explanatory: true
  misc: false
```

Set a post kind to `false` when you do not want that section or any of its posts published. During `quarto render` or deployment, disabled posts are marked as Quarto drafts through generated metadata in `blogposts/_hidden_posts.yml`, so they are omitted from homepage listings, search results, and the sitemap. The section heading is also omitted from the homepage, and a direct URL for a disabled post renders without its article content.

`quarto preview` can still display draft pages when opened directly, as intended for reviewing unpublished work. The deployed site uses the hidden output from a normal render.

### Deleting Blog Posts

If you want to fully delete a post from your repository, do **not** just delete the source folder, as the generated `.html` files will be left behind in the `docs/` folder. Instead, use the included deletion script:

```bash
./delete_post.sh "my-post-name"
```
Or run interactively:
```bash
./delete_post.sh
```

**What the script does:**
1. It safely asks for confirmation before deleting anything.
2. It permanently deletes your source folder `blogposts/posts/<post-slug>/`.
3. It permanently deletes any generated, orphaned `.html` output files in `blogposts/docs/posts/<post-slug>/`.

After deleting a post, just run `quarto render` in the `blogposts/` directory to instantly update your site's index.

## Checking Post Formatting

Exporting a post from Obsidian to `.qmd` tends to leave predictable formatting artifacts — stray LaTeX spacing, malformed tables, `<br>` inside cells, leftover Obsidian syntax, and Obsidian callouts (`> [!note]`) that don't render in Quarto. The included format checker finds these deterministically and can auto-fix the safe ones.

```bash
./check_post.sh                      # check every post
./check_post.sh my-post-slug         # check a single post
./check_post.sh my-post-slug --fix   # check and apply safe fixes without prompting
./check_post.sh --check              # report only, never prompt (CI-friendly)
```

**What it does:**
1. Reports issues grouped by category (Math, Tables, Structure, Links & images, Obsidian artifacts, Front matter, Obsidian callouts), each with a severity (`ERROR` / `WARN` / `INFO`) and line number.
2. If any issues are auto-fixable, it asks `Auto-fix N fixable issue(s)? [y/N]`. Answering `y` applies only the safe, syntactic fixes (trailing whitespace, heading spacing, blank-line normalization, Obsidian-callout conversion, `==highlight==` → `**bold**`, etc.) and re-verifies.
3. Anything that needs judgment — stray text, wikilinks, unbalanced math, unmapped callout types — is reported but never auto-edited, so no content is lost.

For example, an Obsidian callout like:

```
> [!info]- A Note
> Some content.
```

is converted to the Quarto equivalent:

```
::: {.callout-note title="A Note" collapse="true"}
Some content.
:::
```

The checker is a standalone Python tool under `tools/qmd_lint/` (run via `uv`); its rules can be tuned in `tools/qmd_lint/config.py`. Run its tests with `uv run pytest`.

## Previewing and Publishing

To see a live, auto-updating preview of your blog locally while you write:
```bash
cd blogposts
quarto preview
```

Publishing is fully automated via GitHub Actions. You do **not** need to run `quarto render` before pushing — just push your source changes to `master` and CI will render and deploy to GitHub Pages automatically. The workflow triggers on any push that touches `blogposts/**`, `pyproject.toml`, `uv.lock`, or the workflow file itself.

## Keeping Posts Private

If you want to work on a post locally without it appearing on the live site or in the repository, add its folder to `.gitignore`:

```
blogposts/posts/my-private-post/
```

The post will remain entirely local. When you are ready to publish, remove the entry from `.gitignore` and push to `master` as normal.

## Exporting a Post as PDF

To export a post as a PDF (e.g. to share privately before publishing), use the included export script from the root of the repository:

```bash
./export_pdf.sh my-post-slug
```

Or run it interactively without arguments and it will prompt you for the slug:

```bash
./export_pdf.sh
```

The script renders the post to HTML via Quarto and then uses Chrome in headless mode to print it to PDF. The output is saved alongside the source file at:

```
blogposts/posts/<post-slug>/<post-slug>.pdf
```

**Requirements:**

- **Quarto** — must be installed and available on your `PATH`
- **Google Chrome** — must be installed at the standard macOS path:
  `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`

The PDF will reflect the full site styling (theme, fonts, layout) since it is generated directly from the rendered HTML.

> **Note:** Add `*.pdf` to your `.gitignore` if you do not want PDFs accidentally committed to the repository.

<details>
<summary>Repo Notes</summary>

`llm_work_flows` and `llm-from-scratch` are deprecated and no longer maintained. They were originally created for a Substack blog that is no longer being run, and the blog has shifted to the `blogposts` folder.
</details>
