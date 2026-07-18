#!/usr/bin/env bash

# Convert lightweight {citation:handle} tags in a post into Quarto/Pandoc
# citations and build the post-local references.bib.

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON:-python3}"
exec "$PYTHON_BIN" tools/convert_citations.py "$@"
