#!/usr/bin/env bash

# navigate to the directory where this script resides, so we always work relative to blogs/
cd "$(dirname "$0")"

if [ -z "$1" ]; then
    read -p "Enter the slug of the post to delete: " POST_SLUG
else
    POST_SLUG="$1"
fi

if [ -z "$POST_SLUG" ]; then
    echo "Post slug cannot be empty. Exiting."
    exit 1
fi

if [[ ! "$POST_SLUG" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Error: Invalid post slug. Only alphanumeric characters, dashes, and underscores are allowed."
    exit 1
fi

POST_DIR="blogposts/posts/$POST_SLUG"
DOCS_DIR="blogposts/docs/posts/$POST_SLUG"

if [ ! -d "$POST_DIR" ]; then
    echo "Error: Post directory '$POST_DIR' does not exist."
    exit 1
fi

echo "⚠️  You are about to permanently delete the post '$POST_SLUG'."
echo "This will remove the source folder and the generated documentation."
read -p "Are you sure? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Remove the source post directory
    rm -rf "$POST_DIR"
    echo "🗑️ Deleted source: $POST_DIR"

    # Remove the orphaned docs if they exist
    if [ -d "$DOCS_DIR" ]; then
        rm -rf "$DOCS_DIR"
        echo "🗑️ Deleted generated docs: $DOCS_DIR"
    else
        echo "ℹ️ No generated docs found to delete at $DOCS_DIR."
    fi

    echo "✅ Post '$POST_SLUG' has been completely removed."

    echo "🔄 Rebuilding site index..."
    (cd blogposts && quarto render)
    echo "✅ Site rebuilt successfully."
else
    echo "❌ Deletion canceled."
    exit 0
fi
