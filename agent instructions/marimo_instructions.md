# Project-Level Marimo Instructions

This document defines the repository-wide rules for installing, configuring,
authoring, exporting, and publishing marimo applications. Apply it to every
task involving marimo in this repository. The default architecture is a
separate marimo Python file exported to a browser-executable WebAssembly
application and embedded in a Quarto blog post.

The instructions intentionally separate:

1. the repository environment used by authors and CI;
2. the dependencies required by an individual marimo application; and
3. the static files delivered to the reader's browser.

## Applicability and repository constraints

An agent must read this file before installing marimo, creating or editing a
marimo application, changing marimo dependencies, or changing marimo build and
publishing behavior. This file supplements the active repository agent
instructions; it does not override them.

- Do not install packages or change project files unless the user has explicitly
  authorized the work.
- Run downloads in the foreground. Never start `uv`, marimo, Quarto, or other
  download/install operations in the background unless the user explicitly asks
  for that.
- Do not create temporary files or copies as part of setup or patching. Use the
  final intended paths.
- Before proposing or creating tests, explain the utility of each test and read
  `agent_instructions.md` for the project's testing policy. If that file cannot
  be found, stop and ask for direction before creating tests.
- A normal marimo setup does not require adding tests automatically.

### Instruction discovery

This is a supplemental instruction file. Its directory name does not, by
itself, make Codex or another agent load it automatically. The repository's
root instruction mechanism must point agents to this file for marimo-related
tasks.

That pointer now exists: root `agent_instructions.md` is the single source of
truth for this repository and indexes this file under "Scope and precedence".
The root `AGENTS.md` and `CLAUDE.md` are pointers to it, so a tool that
auto-loads either filename reaches these instructions. Register any new
supplemental instruction file the same way — through `agent_instructions.md`,
and only with authorization to modify it.

## Mental model

The recommended publishing path is:

```text
marimo source app.py
        |
        | marimo export html-wasm
        v
static HTML + JavaScript + WebAssembly assets
        |
        | embedded by a relative iframe URL
        v
Quarto blog post
        |
        | quarto render / GitHub Actions
        v
GitHub Pages
```

The reader does not connect to a Python server. Python executes inside the
reader's browser through Pyodide/WebAssembly.

The marimo source is still shipped as part of the browser application. Hiding
code improves presentation, but it is not a security boundary. Never put
secrets, private credentials, private URLs, or sensitive data in a marimo app.

The separate-file iframe workflow does not require the Quarto-marimo extension.
That extension is needed only for inline `{python .marimo}` cells.

## Required integration contract

A separate marimo application is correctly wired into this repository only when
all of the following are true:

1. `marimo` is declared in the root `pyproject.toml` and resolved in `uv.lock`.
2. The app source lives at
   `blogposts/posts/POST_SLUG/interactive/APP_NAME/app.py`.
3. App-only dependencies are declared in that file's PEP 723 metadata.
4. `marimo export html-wasm` writes to the app's permanent `dist/` directory.
5. The post front matter publishes that `dist/` directory through `resources`.
6. The article body embeds `dist/index.html` with a relative iframe URL.
7. The iframe markup lives in the Obsidian source when the post is synced from
   Obsidian.
8. GitHub Actions exports every marimo app after `uv sync --frozen` and before
   Quarto publishes the site.
9. The post has a useful non-interactive fallback.

Omitting any one of these connections can produce a local-only app, a missing
deployment artifact, a stale visualization, or a broken production iframe.

## First-time installation

### Prerequisites

This repository already uses `uv` and Quarto. Confirm that both commands are
available:

```bash
uv --version
quarto --version
```

The repository currently requires Python 3.11 or newer in `pyproject.toml`.
Keep marimo applications compatible with that requirement unless there is a
specific reason to use a different version.

### Add marimo to the repository environment

Run this once from the repository root:

```bash
uv add marimo
```

This updates both `pyproject.toml` and `uv.lock`. Commit those two files when the
marimo installation is intentionally added to the project.

Do not install marimo with a separate global `pip install` for routine repository
work. Using `uv add` keeps local development and GitHub Actions on the same
resolved version.

For a fresh checkout after marimo has already been added to the project, use:

```bash
uv sync --frozen
```

Verify the installation:

```bash
uv run marimo --version
```

An optional interactive introduction is available with:

```bash
uv run marimo tutorial intro
```

That command starts a local foreground process and opens a browser-based
tutorial. Stop it with `Ctrl-C` when finished.

### Why marimo belongs in the project dependencies

The repository-level marimo dependency provides the CLI needed to:

- edit applications locally;
- export applications to WebAssembly HTML;
- run export steps in GitHub Actions; and
- keep the exporter version reproducible through `uv.lock`.

Libraries used only by one visualization should normally not be added to the
repository's `pyproject.toml`. They belong in that app's inline dependency
metadata, described below.

## Recommended directory layout

Keep each interactive application beside the post that uses it:

```text
blogposts/posts/<post-slug>/
├── index.qmd
├── _draft.md
├── assets/
└── interactive/
    └── <app-name>/
        ├── app.py
        ├── public/
        │   └── optional-app-data
        └── dist/
            └── generated-browser-app
```

Source files and intentional data files are authored content. The `dist/`
directory is generated build output.

Prefer generating `dist/` locally when previewing and in CI when publishing.
Whether generated output is committed should be decided explicitly for the
repository; do not silently add an ignore rule or change the generated-file
policy.

## Creating a marimo application

In command examples, replace `POST_SLUG` and `APP_NAME` with the real permanent
directory names before running the command. They are placeholders, not shell
variables.

Create the permanent application directory if it does not already exist:

```bash
mkdir -p blogposts/posts/POST_SLUG/interactive/APP_NAME
```

From the repository root, create or open the app in a sandboxed environment:

```bash
uv run marimo edit --sandbox \
  blogposts/posts/POST_SLUG/interactive/APP_NAME/app.py
```

If `app.py` does not exist, marimo creates it at the requested permanent path.
The command remains active while the browser editor is open. Stop it with
`Ctrl-C`.

Use sandbox mode for applications intended for browser export. In sandbox mode,
marimo records package requirements in the Python file using PEP 723 inline
script metadata and runs the notebook in an isolated `uv` environment.

For good WebAssembly startup performance, put this import in its own marimo cell:

```python
import marimo as mo
```

Then put third-party imports such as NumPy in separate cells as appropriate:

```python
import numpy as np
```

### Application design guidance

- Use marimo UI elements for controls and reactive state.
- Prefer lightweight SVG, HTML, or browser-native rendering for explanatory
  diagrams.
- Avoid running large models or expensive training/inference in the browser.
- Precompute expensive artifacts where possible and ship only the small data
  needed for interaction.
- Keep the initial view useful before the reader touches any control.
- Design responsively for both the article container and narrow/mobile layouts.
- Include accessible labels and explanatory text for controls.
- Provide a static image or equivalent explanation for PDF, no-JavaScript, and
  accessibility fallbacks.

## Dependency management with uv

### Two dependency scopes

Keep the scopes distinct:

| Scope | File | Examples | Purpose |
|---|---|---|---|
| Repository/CI | `pyproject.toml` and `uv.lock` | `marimo` | Provides the authoring and export CLI |
| Individual app | PEP 723 header in `app.py` | `numpy`, `pandas`, `plotly` | Declares what that browser app needs |

Do not add every app dependency to the repository-level `pyproject.toml` merely
because one visualization imports it. Inline app metadata keeps each app
reproducible and avoids coupling unrelated posts.

Repository-level dependencies are not automatically available in the browser.
An app must declare every browser runtime dependency in its own PEP 723 metadata
even when the same package also appears in the root `pyproject.toml`.

### Automatic metadata management

PEP 723 is a Python packaging standard for storing a script's Python-version and
dependency requirements directly in comments at the top of that `.py` file. In
this workflow it makes each marimo app self-describing without requiring a
separate requirements file.

When an app is opened with `marimo edit --sandbox`, importing a third-party
package causes marimo to add it to the script metadata. A header will resemble:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy==<tested-version>",
#     "pandas==<tested-version>",
# ]
# ///
```

The exact versions should be the versions resolved and tested by `uv`/marimo;
do not copy placeholder versions literally.

Removing an import does not necessarily remove its dependency automatically.
Review the metadata before publishing so unused packages do not increase setup
or browser-loading costs.

### Manage app dependencies from the command line

Add a dependency to one app:

```bash
uv add --script \
  blogposts/posts/POST_SLUG/interactive/APP_NAME/app.py \
  numpy
```

Add multiple dependencies:

```bash
uv add --script \
  blogposts/posts/POST_SLUG/interactive/APP_NAME/app.py \
  numpy pandas
```

Remove an app dependency:

```bash
uv remove --script \
  blogposts/posts/POST_SLUG/interactive/APP_NAME/app.py \
  pandas
```

These commands update the PEP 723 metadata in `app.py`; they do not add those
packages to the root `pyproject.toml`.

### WebAssembly package compatibility

NumPy, pandas, SciPy, scikit-learn, and matplotlib are supported by Pyodide.
Packages with pure-Python wheels on PyPI are generally supported as well.

Not every package works in WebAssembly. Be cautious with packages that require:

- native extensions without Pyodide/WebAssembly wheels;
- a GPU;
- operating-system processes or true multiprocessing;
- arbitrary local filesystem access;
- background services or daemons; or
- system libraries unavailable in the browser.

Test an exported app in the browser before relying on a new dependency. A
package working in the local sandbox does not alone prove that it works in
Pyodide.

For platform-specific dependencies, use PEP 508 markers. For example:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "torch; sys_platform != 'emscripten'",
#     "pyodide-http; sys_platform == 'emscripten'",
# ]
# ///
```

- `sys_platform != 'emscripten'` installs a dependency locally but excludes it
  from the browser.
- `sys_platform == 'emscripten'` installs a dependency only in the Pyodide
  environment.

Do not add a local-only dependency unless the app has a browser-compatible code
path that does not import or use it at runtime.

### Browser performance

Dependencies are installed or loaded into the browser runtime. Even supported
packages can increase the cold-start time and memory footprint.

- Use NumPy only when array operations materially simplify the app.
- Avoid pandas when plain Python data structures are sufficient.
- Avoid matplotlib for UI-like diagrams that can be drawn with SVG/HTML.
- Avoid importing packages that are only used during local development.
- Keep datasets and images appropriately sized for a web page.

WebAssembly notebooks have browser memory and concurrency limitations. Heavy
computation should run ahead of time or on a server rather than in the reader's
tab.

### Private packages and credentials

Do not use private package indexes, authentication tokens, or private Git URLs
inside a public browser application. The notebook and its dependency metadata
are delivered to readers and should be treated as public.

If an application genuinely requires protected computation or protected data,
it needs a backend deployment rather than the static WebAssembly workflow in
this document.

## Data files, images, and other app resources

For app-specific public data, place files in a `public/` directory beside
`app.py`:

```text
interactive/<app-name>/
├── app.py
└── public/
    ├── example.csv
    └── example.png
```

Marimo copies `public/` into the WebAssembly export. Construct paths using
`mo.notebook_location()` so the same code works locally and after export:

```python
data_path = mo.notebook_location() / "public" / "example.csv"
```

Do not duplicate a post asset merely to make it available to marimo without
first deciding which location is the source of truth. When an existing Quarto
asset can be referenced through a stable same-origin URL, prefer referencing it
over making an extra copy. If a copy or hard link appears necessary, ask for
permission before creating it.

Remote data can be fetched over HTTP, but the remote host must permit browser
access through CORS. Do not make a core educational visualization depend on an
unreliable third-party endpoint when the data is small enough to publish with
the app.

## Exporting the app for the browser

From the repository root, export the app in reader/run mode:

```bash
uv run marimo export html-wasm \
  blogposts/posts/POST_SLUG/interactive/APP_NAME/app.py \
  -o blogposts/posts/POST_SLUG/interactive/APP_NAME/dist \
  --mode run \
  --no-show-code
```

The important options are:

- `html-wasm`: creates an interactive browser application with no Python
  backend;
- `--mode run`: prevents readers from editing the notebook in the normal UI;
- `--no-show-code`: presents the application rather than its source cells; and
- `-o`: writes directly to the permanent build-output directory.

Hidden or locked code is still sent to the browser. Never rely on these options
to protect source code, credentials, or data.

The exported application must be served over HTTP. Opening its `index.html`
directly with a `file://` URL will not work correctly.

To inspect only the exported application locally, run this foreground command:

```bash
uv run python -m http.server 8000 \
  --directory blogposts/posts/POST_SLUG/interactive/APP_NAME/dist
```

Then open `http://localhost:8000/`. Stop the server with `Ctrl-C`.

## Embedding the separate app in a Quarto post

### Make Quarto publish the generated files

Add the generated directory to the post's YAML front matter:

```yaml
resources:
  - interactive/APP_NAME/dist/**
```

This makes the resource relationship explicit and ensures the exported marimo
files are included in the rendered site.

### Add the iframe to the article body

Embed the app with a relative URL:

```html
<iframe
  src="interactive/APP_NAME/dist/index.html"
  title="Interactive visualization"
  loading="lazy"
  width="100%"
  height="760"
  style="border: 1px solid #ddd; border-radius: 8px;"
></iframe>
```

Use `loading="lazy"` so the WebAssembly runtime is not initialized until the
reader approaches the visualization. Give every iframe a descriptive `title`.
Adjust the height only after checking the rendered app at desktop and mobile
widths.

### Obsidian is the source of truth for the body

`sync_post.sh` regenerates the body of `index.qmd` from the Obsidian draft. Put
the iframe markup and its surrounding explanatory prose in the Obsidian source,
not only in `index.qmd`, or the next sync will overwrite it.

The YAML front matter in `index.qmd` is preserved by the sync workflow, so the
`resources` entry belongs in `index.qmd` front matter.

The separate `interactive/` source directory is not part of the Obsidian asset
mirror and should remain independently maintained in the repository.

### Provide a non-interactive fallback

The article must remain understandable if the application is slow, unavailable,
printed to PDF, or viewed without JavaScript.

- Introduce the visualization in prose immediately before the iframe.
- Provide a static overview image or diagram near the interactive version.
- Give controls text labels rather than relying only on color.
- Ensure the initial app state communicates a complete first step.
- Check the PDF export and decide whether the iframe or the static fallback
  should appear in print.

## Local authoring workflow

For a normal editing session:

1. Synchronize the post from Obsidian if needed.
2. Start the marimo editor in one foreground terminal.
3. Develop and verify the application locally.
4. Export the application to its `dist/` directory.
5. Start Quarto preview in another foreground terminal.
6. Verify the visualization inside the actual blog post.

Commands from the repository root:

```bash
uv run marimo edit --sandbox \
  blogposts/posts/POST_SLUG/interactive/APP_NAME/app.py
```

After saving and stopping or leaving the editor running, export from another
foreground terminal:

```bash
uv run marimo export html-wasm \
  blogposts/posts/POST_SLUG/interactive/APP_NAME/app.py \
  -o blogposts/posts/POST_SLUG/interactive/APP_NAME/dist \
  --mode run \
  --no-show-code
```

Then preview the Quarto site:

```bash
cd blogposts
quarto preview
```

Always re-export after changing `app.py`; Quarto cannot render a newer marimo
application from stale files in `dist/`.

## GitHub Actions integration

The repository's publish workflow already runs `uv sync --frozen` before Quarto
publishes the site. Add marimo export steps after dependency installation and
before the Quarto publish action.

For one app, the workflow step would be conceptually:

```yaml
- name: Export marimo applications
  run: |
    uv run marimo export html-wasm \
      blogposts/posts/POST_SLUG/interactive/APP_NAME/app.py \
      -o blogposts/posts/POST_SLUG/interactive/APP_NAME/dist \
      --mode run \
      --no-show-code
```

The required order is:

```text
checkout
  -> install uv and Python
  -> uv sync --frozen
  -> export every marimo app
  -> Quarto render/publish
```

For multiple applications, keep an explicit list of export commands or create a
single tracked foreground export script after obtaining authorization. Avoid
undocumented globs that may silently omit or unexpectedly include applications.

CI should fail when an export fails. Do not append `|| true` or otherwise hide a
dependency or WebAssembly compatibility error.

## Validation checklist

Before publishing an interactive post, verify:

- `uv run marimo --version` succeeds;
- the app opens locally with `marimo edit --sandbox`;
- PEP 723 metadata contains only intentional dependencies;
- `marimo export html-wasm` completes without errors;
- the exported app loads over HTTP rather than `file://`;
- browser developer tools show no failed package or asset requests;
- every control changes the expected output;
- the app loads inside the Quarto page at the final relative URL;
- the iframe fits the article at desktop and narrow widths;
- the app is usable with keyboard controls where applicable;
- the visualization remains understandable through its static fallback;
- no credentials, private data, or private package URLs are present;
- the GitHub Actions export runs before Quarto publish; and
- a fresh or private browser session can load the deployed page.

This is a manual validation checklist, not authorization to create automated
tests. Follow the repository testing policy before adding any test files.

## Troubleshooting

### The exported page is blank when opened from Finder

WebAssembly exports must be served over HTTP. Use Quarto preview or the local
`python -m http.server` command above. Do not test with a `file://` URL.

### NumPy or pandas works locally but fails in the browser

- Confirm the dependency is present in the PEP 723 metadata.
- Re-export after changing dependencies.
- Check the browser console and network panel for package-resolution errors.
- Confirm the pinned version exists for the Pyodide version used by marimo.
- Try a compatible version rather than assuming the latest native CPython wheel
  will run in WebAssembly.

### Another package cannot be installed

Check whether it provides a pure-Python or Pyodide-compatible wheel. If not:

- replace it with a browser-compatible library;
- precompute its output and ship the resulting data;
- isolate it behind `sys_platform != 'emscripten'` and provide a browser code
  path; or
- use a separately hosted backend app instead of static WebAssembly.

### The iframe returns 404 after Quarto render

- Confirm `dist/index.html` exists before running Quarto.
- Confirm the post front matter includes the `resources` glob.
- Confirm the iframe URL is relative to the post's rendered page.
- Inspect the final `blogposts/docs/posts/POST_SLUG/` output.

### The app is stale

The marimo source and the exported app are separate artifacts. Re-run
`marimo export html-wasm`, then reload Quarto preview. If the browser still shows
an older version, perform a normal browser reload and inspect the exported files'
paths before changing cache settings.

### The first load is too slow

- Remove unused packages from the app metadata.
- Replace pandas or matplotlib with lighter data structures/SVG when practical.
- Keep `import marimo as mo` in its own cell.
- Lazy-load the iframe.
- Reduce image and dataset sizes.
- Avoid doing expensive work during the initial reactive evaluation.

### The app needs secrets or private data

Do not put them in the WebAssembly app. Static browser applications cannot keep
secrets. Reconsider the feature as a backend deployment with appropriate
authentication and authorization.

## When inline marimo cells are appropriate

The separate-file workflow is the default for substantial visualizations. Inline
`{python .marimo}` cells in a `.qmd` or Markdown file can be reasonable for a
small control or short calculation.

Use a separate app when:

- the visualization has several cells or helper functions;
- it has its own dependencies or public data;
- it needs independent browser testing;
- it is likely to be reused; or
- embedding the code in the Obsidian article would make the prose difficult to
  maintain.

Use inline cells only after installing and configuring the official
Quarto-marimo extension. Inline cells follow a different build path from the
exported-iframe approach and should not be introduced accidentally into a post
that expects a separate `app.py`.

## Official references

- [Marimo installation](https://docs.marimo.io/getting_started/installation/)
- [Marimo dependency inlining and sandboxing](https://docs.marimo.io/guides/package_management/inlining_dependencies/)
- [Marimo WebAssembly notebooks and package support](https://docs.marimo.io/guides/wasm/)
- [Exporting WebAssembly HTML](https://docs.marimo.io/guides/exporting/webassembly_html/)
- [Embedding marimo in other webpages](https://docs.marimo.io/guides/publishing/embedding/)
- [Self-hosting WebAssembly notebooks](https://docs.marimo.io/guides/publishing/self_host_wasm/)
- [Quarto website resources and HTML options](https://quarto.org/docs/reference/formats/html.html)
