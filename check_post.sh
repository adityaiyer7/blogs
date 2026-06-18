#!/usr/bin/env bash

# Deterministic format checker for Quarto blog posts. Reports formatting issues
# grouped by category and, if any are auto-fixable, offers to fix them.
#
#   ./check_post.sh                      # check every post
#   ./check_post.sh my-post-slug         # check one post
#   ./check_post.sh my-post-slug --fix   # check and apply safe fixes without prompting
#   ./check_post.sh --check              # report only, never prompt (CI)

# navigate to the directory where this script resides, so we always work relative to blogs/
cd "$(dirname "$0")"

# If the first argument looks like a bare slug (no leading dash, not a path),
# validate it the same way create_post.sh does.
if [ -n "$1" ] && [[ "$1" != -* ]] && [[ "$1" != *.qmd ]]; then
    if [[ ! "$1" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "Error: Invalid post slug. Only alphanumeric characters, dashes, and underscores are allowed."
        exit 1
    fi
fi

exec uv run python -m tools.qmd_lint "$@"
