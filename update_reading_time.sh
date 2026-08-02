#!/usr/bin/env bash

# Recompute every post's reading time from the rendered HTML under
# blogposts/docs/ and patch the post pages, the homepage listing, and the
# search index so they all show the same number.
#
#   ./update_reading_time.sh                 # every rendered post
#   ./update_reading_time.sh my-post-slug    # one post
#   ./update_reading_time.sh --check         # report drift, write nothing (CI)
#
# blogposts/_quarto.yml runs this automatically after every `quarto render`,
# so it is rarely needed by hand.

# navigate to the directory where this script resides, so we always work relative to blogs/
cd "$(dirname "$0")" || exit 1

exec uv run python -m tools.reading_time "$@"
