#!/usr/bin/env bash

# Re-sync an existing post from its Obsidian source. Obsidian is the source of
# truth for the post body; the repo-managed YAML frontmatter in index.qmd is
# preserved. Rendering is not run — use `quarto preview` or push to let CI render.
#
#   ./sync_post.sh <slug> --project /path/to/obsidian-project-dir
#
# The project dir must contain exactly one top-level .md file (the draft) and,
# optionally, an assets/ folder. This overwrites _draft.md and regenerates the
# body of index.qmd, re-running the same Obsidian-embed rewrite and heading
# normalization as create_post.sh.

# navigate to the directory where this script resides, so we always work relative to blogs/
cd "$(dirname "$0")"

# Shared helpers: normalize_markdown_for_quarto, rewrite_obsidian_embeds, extract_frontmatter.
source tools/post_lib.sh

# Parse arguments: a `--project <dir>` flag plus the positional post slug.
PROJECT_DIR=""
POSITIONAL=()
while [ $# -gt 0 ]; do
    case "$1" in
        --project)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --project=*)
            PROJECT_DIR="${1#*=}"
            shift
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done
set -- "${POSITIONAL[@]}"

POST_SLUG="$1"

if [ -z "$POST_SLUG" ]; then
    echo "Usage: ./sync_post.sh <slug> --project /path/to/obsidian-project-dir"
    exit 1
fi

if [[ ! "$POST_SLUG" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Error: Invalid post slug. Only alphanumeric characters, dashes, and underscores are allowed."
    exit 1
fi

if [ -z "$PROJECT_DIR" ]; then
    echo "Error: --project <dir> is required (the Obsidian project folder to sync from)."
    exit 1
fi

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory '$PROJECT_DIR' does not exist."
    exit 1
fi

TARGET_DIR="blogposts/posts/$POST_SLUG"
INDEX_QMD="$TARGET_DIR/index.qmd"

# The post must already exist — this script syncs, it does not create.
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Post directory '$TARGET_DIR' does not exist."
    echo "       Use ./create_post.sh to create a new post first."
    exit 1
fi

if [ ! -f "$INDEX_QMD" ]; then
    echo "Error: '$INDEX_QMD' not found — cannot determine frontmatter to preserve."
    exit 1
fi

# Preserve the existing repo-managed frontmatter block.
FRONTMATTER_FILE="$(mktemp)"
if ! extract_frontmatter "$INDEX_QMD" > "$FRONTMATTER_FILE"; then
    rm -f "$FRONTMATTER_FILE"
    echo "Error: '$INDEX_QMD' has no YAML frontmatter block (--- ... ---) to preserve."
    exit 1
fi

# Discover the single top-level .md inside the project directory.
MD_MATCHES=()
while IFS= read -r md; do
    MD_MATCHES+=("$md")
done < <(find "$PROJECT_DIR" -maxdepth 1 -type f -name "*.md")

if [ "${#MD_MATCHES[@]}" -eq 0 ]; then
    rm -f "$FRONTMATTER_FILE"
    echo "Error: No .md file found at the top level of '$PROJECT_DIR'."
    exit 1
elif [ "${#MD_MATCHES[@]}" -gt 1 ]; then
    rm -f "$FRONTMATTER_FILE"
    echo "Error: Expected exactly one .md file at the top level of '$PROJECT_DIR', found ${#MD_MATCHES[@]}:"
    printf '  - %s\n' "${MD_MATCHES[@]}"
    exit 1
fi

MD_DRAFT="${MD_MATCHES[0]}"

# Overwrite the preserved draft with the latest Obsidian source.
cp "$MD_DRAFT" "$TARGET_DIR/_draft.md"
echo "✅ Synced '$MD_DRAFT' to '$TARGET_DIR/_draft.md'"

# Mirror the source assets/ tree additively (preserving subfolders). Note: this
# does not delete repo assets that were removed in Obsidian.
if [ -d "$PROJECT_DIR/assets" ]; then
    cp -R "$PROJECT_DIR/assets/." "$TARGET_DIR/assets/"
    echo "✅ Synced assets from '$PROJECT_DIR/assets' to '$TARGET_DIR/assets'"
else
    echo "⚠️ Warning: No 'assets' folder found in '$PROJECT_DIR'. Skipping asset sync."
fi

# Rebuild index.qmd: preserved frontmatter + blank line + fresh draft body.
{
    cat "$FRONTMATTER_FILE"
    echo ""
    cat "$TARGET_DIR/_draft.md"
} > "$INDEX_QMD"
rm -f "$FRONTMATTER_FILE"

# Re-apply the same transforms create_post.sh uses on the generated body.
rewrite_obsidian_embeds "$INDEX_QMD" "$TARGET_DIR/assets" "$TARGET_DIR"
echo "✅ Rewrote Obsidian image embeds (![[…]]) into Quarto links"
normalize_markdown_for_quarto "$INDEX_QMD"
echo "✅ Normalized markdown for Quarto (blank lines before headings)"

echo "✅ Regenerated '$INDEX_QMD' (frontmatter preserved, body synced from Obsidian)"

# Regenerating from the raw Obsidian draft reverts Quarto-specific fixes (e.g.
# ```mermaid -> ```{mermaid}, callout conversion). Re-apply the safe ones so the
# output is render-ready in one command, matching the create -> check workflow.
echo ""
echo "🔧 Applying Quarto format fixes via check_post.sh…"
./check_post.sh "$POST_SLUG" --fix

echo ""
echo "ℹ️ Run 'cd blogposts && quarto preview' to preview, or push to render via CI."
