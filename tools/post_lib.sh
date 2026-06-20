#!/usr/bin/env bash

# Shared helpers for the post authoring scripts (create_post.sh, sync_post.sh).
# Source this file from a script that has already cd'd to the repo root.

# Pandoc/Quarto require a blank line before ATX headings (# .. ######). Obsidian and
# other editors often omit that after tables or paragraphs, which breaks heading rendering.
normalize_markdown_for_quarto() {
    local file="$1"
    awk '
        BEGIN { in_fence = 0 }
        /^```/ { in_fence = !in_fence; print; prev = $0; next }
        {
            if (!in_fence && $0 ~ /^#{1,6}[[:space:]]/) {
                if (prev != "" && prev !~ /^[[:space:]]*$/) {
                    print ""
                }
            }
            print
            prev = $0
        }
    ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
}

# Rewrite Obsidian image embeds (![[file.png]] / ![[file.png|caption]]) into Quarto
# markdown image links (![](assets/<relpath>) / ![caption](assets/<relpath>)). The
# relative path is resolved from a basename->path map built over the post's copied
# assets tree. Unmapped or ambiguous (duplicate basename) embeds are left untouched
# and reported, so nothing is silently dropped or guessed.
rewrite_obsidian_embeds() {
    local file="$1"
    local assets_root="$2"   # the post's assets dir (e.g. blogposts/posts/slug/assets)
    local post_root="$3"     # the post dir (relpaths are emitted relative to this)

    [ -d "$assets_root" ] || return 0

    local map_file
    map_file="$(mktemp)"

    # Build basename<TAB>relpath map (relpath is relative to post_root, e.g. assets/imgs/foo.png).
    # Mark duplicate basenames as ambiguous via a sentinel relpath of "\0AMBIGUOUS".
    while IFS= read -r asset; do
        local base rel
        base="$(basename "$asset")"
        rel="${asset#"$post_root"/}"
        if grep -q "^${base}	" "$map_file" 2>/dev/null; then
            # Already present: mark ambiguous (overwrite any existing entry for this base).
            grep -v "^${base}	" "$map_file" > "$map_file.tmp" && mv "$map_file.tmp" "$map_file"
            printf '%s\t\001AMBIGUOUS\n' "$base" >> "$map_file"
        else
            printf '%s\t%s\n' "$base" "$rel" >> "$map_file"
        fi
    done < <(find "$assets_root" -type f ! -name '.gitkeep')

    awk -v mapfile="$map_file" '
        BEGIN {
            FS = "\t"
            while ((getline line < mapfile) > 0) {
                split(line, a, "\t")
                map[a[1]] = a[2]
            }
            close(mapfile)
            in_fence = 0
        }
        /^```/ { in_fence = !in_fence; print; next }
        {
            if (in_fence) { print; next }
            line = $0
            out = ""
            while (match(line, /!\[\[[^]]+\]\]/)) {
                pre = substr(line, 1, RSTART - 1)
                tok = substr(line, RSTART, RLENGTH)
                rest = substr(line, RSTART + RLENGTH)
                # strip the ![[ ]] wrapper
                inner = substr(tok, 4, length(tok) - 5)
                name = inner; caption = ""
                bar = index(inner, "|")
                if (bar > 0) {
                    name = substr(inner, 1, bar - 1)
                    caption = substr(inner, bar + 1)
                }
                # trim surrounding whitespace from name
                gsub(/^[ \t]+|[ \t]+$/, "", name)
                if (name in map && map[name] != "\001AMBIGUOUS") {
                    out = out pre "![" caption "](" map[name] ")"
                } else {
                    if (name in map) {
                        printf("⚠️  Ambiguous asset \"%s\" (same basename in multiple folders) — leaving embed untouched\n", name) > "/dev/stderr"
                    } else {
                        printf("⚠️  No asset found for embed \"%s\" — leaving untouched\n", name) > "/dev/stderr"
                    }
                    out = out pre tok
                }
                line = rest
            }
            print out line
        }
    ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"

    rm -f "$map_file"
}

# Print the leading YAML frontmatter block of a .qmd file (both --- fences
# inclusive) to stdout. Exits non-zero if the file does not start with a
# frontmatter block delimited by a pair of --- lines.
extract_frontmatter() {
    local file="$1"
    awk '
        NR == 1 && $0 != "---" { exit 1 }
        /^---$/ { c++; print; if (c == 2) exit 0; next }
        c == 1 { print }
        END { if (c < 2) exit 1 }
    ' "$file"
}
