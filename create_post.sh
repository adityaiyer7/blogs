#!/usr/bin/env bash

# navigate to the directory where this script resides, so we always work relative to blogs/
cd "$(dirname "$0")"

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

if [ -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' already exists."
    exit 1
fi

# Create directory structure
mkdir -p "$ASSETS_DIR"
touch "$ASSETS_DIR/.gitkeep"

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
        
        echo "✅ Copied '$MD_DRAFT' to '$TARGET_DIR/_draft.md'"
        echo "✅ Appended draft content to '$TARGET_DIR/index.qmd'"
    else
        echo "⚠️ Warning: Draft file '$MD_DRAFT' not found. Skipping file import."
        echo -e "# Introduction\n\nWrite your post content here...\n\nTo embed an image, use: \`![](assets/imgs/your-image.png)\`" >> "$TARGET_DIR/index.qmd"
    fi
else
    echo -e "# Introduction\n\nWrite your post content here...\n\nTo embed an image, use: \`![](assets/imgs/your-image.png)\`" >> "$TARGET_DIR/index.qmd"
fi

echo "✅ Created new post structure at '$TARGET_DIR'"
echo "✅ Assets folder created at '$ASSETS_DIR'"
