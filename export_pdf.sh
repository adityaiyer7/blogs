#!/usr/bin/env bash
# Usage: ./export_pdf.sh my-post-slug

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    read -p "Enter the post slug (e.g. sae-for-monosemanticity): " POST_SLUG
else
    POST_SLUG="$1"
fi

POST_PATH="blogposts/posts/$POST_SLUG/index.qmd"
OUTPUT_HTML="blogposts/docs/posts/$POST_SLUG/index.html"
OUTPUT_PDF="blogposts/posts/$POST_SLUG/$POST_SLUG.pdf"

if [ ! -f "$POST_PATH" ]; then
    echo "Error: Post '$POST_SLUG' not found at '$POST_PATH'."
    exit 1
fi

# Render the post to HTML
echo "Rendering '$POST_SLUG'..."
quarto render "$POST_PATH"

if [ ! -f "$OUTPUT_HTML" ]; then
    echo "Error: Rendered HTML not found at '$OUTPUT_HTML'. Render may have failed."
    exit 1
fi

# Resolve absolute path for Chrome
ABS_HTML="$(pwd)/$OUTPUT_HTML"
ABS_PDF="$(pwd)/$OUTPUT_PDF"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [ ! -f "$CHROME" ]; then
    echo "Error: Google Chrome not found at '$CHROME'."
    exit 1
fi

echo "Exporting to PDF..."
"$CHROME" \
    --headless \
    --disable-gpu \
    --no-sandbox \
    --print-to-pdf="$ABS_PDF" \
    --print-to-pdf-no-header \
    "file://$ABS_HTML" 2>/dev/null

if [ -f "$OUTPUT_PDF" ]; then
    echo "✅ PDF saved to $OUTPUT_PDF"
else
    echo "Error: PDF was not created. Something went wrong."
    exit 1
fi
