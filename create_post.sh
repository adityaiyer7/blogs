#!/usr/bin/env bash

# navigate to the directory where this script resides, so we always work relative to blogs/
cd "$(dirname "$0")"

# Shared helpers: normalize_markdown_for_quarto, rewrite_obsidian_embeds.
source tools/post_lib.sh

# Parse arguments: a `--project <dir>` flag (project mode) plus positional
# arguments (title, and the legacy draft path). Project mode discovers the .md
# inside the directory and copies its assets/ folder over; legacy mode is unchanged.
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

# Check if a post title is provided
if [ -z "$1" ]; then
    read -p "Enter the blog post title (e.g. New Model Eval): " POST_TITLE
else
    POST_TITLE="$1"
fi

# Convert to a URL-friendly slug
POST_SLUG=$(echo "$POST_TITLE" | tr '[:upper:]' '[:lower:]' | tr -s ' ' '-' | tr -cd 'a-z0-9_-')

if [ -z "$POST_SLUG" ]; then
    echo "Post slug cannot be empty. Exiting."
    exit 1
fi

if [[ ! "$POST_SLUG" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Error: Invalid post slug. Only alphanumeric characters, dashes, and underscores are allowed."
    exit 1
fi

MD_DRAFT="$2"
TARGET_DIR="blogposts/posts/$POST_SLUG"
ASSETS_DIR="$TARGET_DIR/assets/imgs"

# In project mode, discover the single top-level .md inside the project directory
# and ignore any positional draft path. The asset folder is copied later.
if [ -n "$PROJECT_DIR" ]; then
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "Error: Project directory '$PROJECT_DIR' does not exist."
        exit 1
    fi

    MD_MATCHES=()
    while IFS= read -r md; do
        MD_MATCHES+=("$md")
    done < <(find "$PROJECT_DIR" -maxdepth 1 -type f -name "*.md")

    if [ "${#MD_MATCHES[@]}" -eq 0 ]; then
        echo "Error: No .md file found at the top level of '$PROJECT_DIR'."
        exit 1
    elif [ "${#MD_MATCHES[@]}" -gt 1 ]; then
        echo "Error: Expected exactly one .md file at the top level of '$PROJECT_DIR', found ${#MD_MATCHES[@]}:"
        printf '  - %s\n' "${MD_MATCHES[@]}"
        exit 1
    fi

    MD_DRAFT="${MD_MATCHES[0]}"
fi

if [ -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' already exists."
    exit 1
fi

# Create directory structure
mkdir -p "$ASSETS_DIR"
touch "$ASSETS_DIR/.gitkeep"

# In project mode, mirror the source assets/ tree (preserving subfolders) into the post.
if [ -n "$PROJECT_DIR" ]; then
    if [ -d "$PROJECT_DIR/assets" ]; then
        cp -R "$PROJECT_DIR/assets/." "$TARGET_DIR/assets/"
        echo "✅ Copied assets from '$PROJECT_DIR/assets' to '$TARGET_DIR/assets'"
    else
        echo "⚠️ Warning: No 'assets' folder found in '$PROJECT_DIR'. Skipping asset copy."
    fi
fi

# Get existing categories to suggest to the user
echo ""
echo "--- Existing Categories ---"
EXISTING_CATEGORIES=$(grep -h "^categories:" "blogposts/posts/"*/index.qmd 2>/dev/null | awk -F'[][]' '{print $2}' | tr ',' '\n' | awk '{$1=$1};1' | sort -u)

if [ -z "$EXISTING_CATEGORIES" ]; then
    echo "(No existing categories found - this might be your first post!)"
else
    echo "$EXISTING_CATEGORIES"
fi
echo "---------------------------"

read -p "Enter a category from above, or type a new one (e.g. Math, AI): " SELECTED_CAT
if [ -z "$SELECTED_CAT" ]; then
    SELECTED_CAT="General"
fi
echo ""

# Create a template index.qmd
CURRENT_DATE=$(date +%Y-%m-%d)

cat > "$TARGET_DIR/index.qmd" <<EOF
---
title: "$POST_TITLE"
description: "Brief description of the post."
date: $CURRENT_DATE
categories: [$SELECTED_CAT]
toc: true
---

EOF

# If a Markdown draft is provided, copy it and append its contents
if [ -n "$MD_DRAFT" ]; then
    if [ -f "$MD_DRAFT" ]; then
        # Copy the original file to the target directory
        cp "$MD_DRAFT" "$TARGET_DIR/_draft.md"
        # Append its contents to the index.qmd file
        cat "$MD_DRAFT" >> "$TARGET_DIR/index.qmd"
        # In project mode, rewrite Obsidian embeds against the copied assets before normalizing.
        if [ -n "$PROJECT_DIR" ]; then
            rewrite_obsidian_embeds "$TARGET_DIR/index.qmd" "$TARGET_DIR/assets" "$TARGET_DIR"
            echo "✅ Rewrote Obsidian image embeds (![[…]]) into Quarto links"
        fi
        normalize_markdown_for_quarto "$TARGET_DIR/index.qmd"

        echo "✅ Copied '$MD_DRAFT' to '$TARGET_DIR/_draft.md'"
        echo "✅ Appended draft content to '$TARGET_DIR/index.qmd'"
        echo "✅ Normalized markdown for Quarto (blank lines before headings)"
    else
        echo "⚠️ Warning: Draft file '$MD_DRAFT' not found. Skipping file import."
        echo -e "# Introduction\n\nWrite your post content here...\n\nTo embed an image, use: \`![](assets/imgs/your-image.png)\`" >> "$TARGET_DIR/index.qmd"
    fi
else
    echo -e "# Introduction\n\nWrite your post content here...\n\nTo embed an image, use: \`![](assets/imgs/your-image.png)\`" >> "$TARGET_DIR/index.qmd"
fi

echo "✅ Created new post structure at '$TARGET_DIR'"
echo "✅ Assets folder created at '$ASSETS_DIR'"
