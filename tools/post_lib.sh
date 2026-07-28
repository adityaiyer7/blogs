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

# --- asset mirroring -------------------------------------------------------

# Write a basename<TAB>path index of every file under $1 into the file at $2.
index_assets() {
    local root="$1"
    local index_file="$2"
    : > "$index_file"
    local f
    while IFS= read -r f; do
        printf '%s\t%s\n' "$(basename "$f")" "$f" >> "$index_file"
    done < <(find "$root" -type f ! -name '.gitkeep' | sort)
}

# Print the indexed paths whose basename is $2, excluding the path $3 (may be empty).
# The comparison is an exact string match, so regex metacharacters in a filename
# (., +, [ …) cannot cause a false hit.
lookup_indexed_assets() {
    awk -F'\t' -v base="$2" -v skip="$3" '$1 == base && $2 != skip { print $2 }' "$1"
}

index_asset_add() {
    printf '%s\t%s\n' "$(basename "$2")" "$2" >> "$1"
}

index_asset_remove() {
    awk -F'\t' -v path="$2" '$2 != path' "$1" > "$1.tmp" && mv "$1.tmp" "$1"
}

# Delete the duplicate an earlier additive sync left behind at $2 (the incoming
# path), de-indexing it from the index file $1. $3 is the label to print.
drop_stale_duplicate() {
    local index_file="$1"
    local dest_path="$2"
    local label="$3"
    [ -f "$dest_path" ] || return 0
    rm -f "$dest_path"
    index_asset_remove "$index_file" "$dest_path"
    echo "   🧹 Removed the stale duplicate at '$label'"
}

# Image extensions that get routed into assets/imgs/. Deliberately narrow: build
# inputs that legitimately sit flat in assets/ (e.g. the .tex/.aux/.dvi/.log LaTeX
# sources in the attention-mechanism post) must keep their place.
POST_IMAGE_EXTENSIONS="png jpg jpeg gif svg webp avif bmp tif tiff"

# Echo the path an incoming asset should land on inside the post's assets/ folder,
# given its path $1 relative to the source assets root $2.
#
# Obsidian vaults keep images flat at the top of assets/, but the repo convention
# (check_post.sh rule D2) is that images live under assets/imgs/. Routing them on
# the way in means rewrite_obsidian_embeds resolves ![[foo.png]] straight to
# assets/imgs/foo.png — no manual move plus path fixup after every sync, and D2
# never fires (it is a warning the linter cannot fix, since fixes are line edits
# and this needs a file move).
#
# Only top-level image files move; anything already in a subfolder keeps the layout
# it was authored with. A flat file is also left alone when the source ships its
# own imgs/<name> too, because routing would collapse two distinct incoming files
# onto one path — that stays a real collision for sync_assets_tree to resolve.
route_asset_relpath() {
    local rel="$1"
    local src_root="$2"

    # Already in a subfolder — respect the author's layout.
    case "$rel" in
        */*) printf '%s\n' "$rel"; return 0 ;;
    esac

    local ext="${rel##*.}"
    # No extension at all ("${rel##*.}" returns the whole name) — not an image.
    if [ "$ext" = "$rel" ]; then
        printf '%s\n' "$rel"
        return 0
    fi
    ext="$(printf '%s' "$ext" | tr '[:upper:]' '[:lower:]')"

    case " $POST_IMAGE_EXTENSIONS " in
        *" $ext "*) ;;
        *) printf '%s\n' "$rel"; return 0 ;;
    esac

    # Routing this would land on top of a different incoming file.
    if [ -e "$src_root/imgs/$rel" ]; then
        printf '%s\n' "$rel"
        return 0
    fi

    printf '%s\n' "imgs/$rel"
}

# Mirror an Obsidian project's assets/ tree into a post's assets/ folder one file
# at a time, resolving same-basename collisions instead of stacking duplicates.
#
#   sync_assets_tree <src_assets_dir> <dest_assets_dir> <policy>
#
# Top-level images are routed into <dest>/imgs/ on the way in (see
# route_asset_relpath), so the post keeps the assets/imgs/ layout check_post.sh
# expects no matter how the Obsidian vault was organized.
#
# A collision is an incoming file whose basename already exists in the post's
# assets tree at a *different* relative path — e.g. the repo keeps
# assets/diagrams/foo.png while Obsidian ships foo.png, which routes to
# assets/imgs/foo.png. Landing on the path a file already occupies is an ordinary
# in-place update, not a collision, which is why routing a flat image onto the
# post's existing assets/imgs/ copy needs no decision at all.
#
# Duplicate basenames are exactly what makes rewrite_obsidian_embeds give up on a
# ![[foo.png]] embed (leaving an E1 for check_post.sh), so each one is resolved:
#
#   override       write the incoming version into the existing repo path,
#                  keeping the repo's layout (images stay under assets/imgs/)
#   keep-existing  discard the incoming copy, leave the repo file untouched
#   keep-both      copy both and leave the embed ambiguous (the old behavior)
#   ask            prompt per collision; A/B/C applies the answer to the rest
#
# Byte-identical collisions resolve to keep-existing without asking. Under `ask`
# with no tty, collisions fall back to keep-both and say so. Under override and
# keep-existing any stale duplicate a previous sync left at the incoming path is
# removed, so an already-duplicated tree is cleaned up rather than just frozen.
#
# Like cp -R before it, this is additive: assets deleted in Obsidian are not
# removed from the post.
sync_assets_tree() {
    local src="$1"
    local dest="$2"
    local policy="${3:-ask}"

    [ -d "$src" ] || return 0
    mkdir -p "$dest"

    # Buffer the source walk into an array rather than piping it into the loop,
    # so stdin stays free for the interactive prompt below.
    local sources=()
    local asset
    while IFS= read -r asset; do
        sources+=("$asset")
    done < <(find "$src" -type f ! -name '.gitkeep' | sort)

    if [ "${#sources[@]}" -eq 0 ]; then
        echo "ℹ️ No asset files found in '$src'."
        return 0
    fi

    local index
    index="$(mktemp)"
    index_assets "$dest" "$index"

    local interactive=0
    [ -t 0 ] && interactive=1

    local dest_label
    dest_label="$(basename "$dest")"

    local copied=0 identical=0 overridden=0 kept_existing=0 kept_both=0 failed=0
    local routed=0
    local warned_no_tty=0
    local rel routed_rel base dest_path incoming_label matches match match_count
    local existing existing_label effective choice is_new stale_path routed_onto_existing

    for asset in "${sources[@]}"; do
        rel="${asset#"$src"/}"
        routed_rel="$(route_asset_relpath "$rel" "$src")"
        base="$(basename "$asset")"
        dest_path="$dest/$routed_rel"
        incoming_label="$dest_label/$routed_rel"
        # The duplicate to clean up once a collision resolves away from the incoming
        # copy. Only the unrouted path can be one: a routed file's target is the
        # post's canonical location, never something to delete.
        stale_path="$dest_path"
        routed_onto_existing=0

        if [ "$routed_rel" != "$rel" ]; then
            echo "📁 Routed '$rel' into '$incoming_label' (images belong under assets/imgs/)"
            routed=$((routed + 1))
            stale_path=""
            # A copy at the unrouted path is this same file from a sync that predates
            # routing; the routed copy supersedes it.
            drop_stale_duplicate "$index" "$dest/$rel" "$dest_label/$rel"
            if [ -f "$dest_path" ]; then
                routed_onto_existing=1
            fi
        fi

        matches="$(lookup_indexed_assets "$index" "$base" "$dest_path")"

        if [ -n "$matches" ] && [ "$routed_onto_existing" -eq 1 ]; then
            # The canonical imgs/ copy already exists, so this is an in-place update;
            # the other copies are strays that predate this sync. Overwriting or
            # deleting one would be a guess, so update in place and report them.
            echo "⚠️  '$base' also exists elsewhere in the post:"
            while IFS= read -r match; do
                printf '      - %s/%s\n' "$dest_label" "${match#"$dest"/}"
            done <<< "$matches"
            echo "      Updating '$incoming_label' in place and leaving those alone — the embed stays unresolved (E1). Resolve manually."
            matches=""
        fi

        if [ -z "$matches" ]; then
            is_new=0
            [ -f "$dest_path" ] || is_new=1
            mkdir -p "$(dirname "$dest_path")"
            if cp "$asset" "$dest_path"; then
                copied=$((copied + 1))
                [ "$is_new" -eq 1 ] && index_asset_add "$index" "$dest_path"
            else
                echo "⚠️  Failed to copy '$asset' to '$dest_path'"
                failed=$((failed + 1))
            fi
            continue
        fi

        match_count="$(printf '%s\n' "$matches" | wc -l | tr -d '[:space:]')"
        existing="$(printf '%s\n' "$matches" | head -n 1)"
        existing_label="$dest_label/${existing#"$dest"/}"

        if [ "$match_count" -eq 1 ] && cmp -s "$asset" "$existing"; then
            echo "↩️  '$base' is identical to '$existing_label' — keeping existing"
            drop_stale_duplicate "$index" "$stale_path" "$incoming_label"
            identical=$((identical + 1))
            continue
        fi

        if [ "$match_count" -gt 1 ]; then
            # The post's own tree is already ambiguous; picking a winner here would
            # be a guess. Report it and leave the manual fixup to the author.
            echo "⚠️  Asset name collision: '$base' already exists at several paths in the post:"
            while IFS= read -r match; do
                printf '      - %s/%s\n' "$dest_label" "${match#"$dest"/}"
            done <<< "$matches"
            echo "      Leaving every copy in place — the embed stays unresolved (E1). Resolve manually."
            effective="keep-both"
        else
            effective="$policy"
        fi

        if [ "$effective" = "ask" ] && [ "$interactive" -eq 0 ]; then
            if [ "$warned_no_tty" -eq 0 ]; then
                echo "⚠️  Not running interactively — asset name collisions will keep both copies."
                echo "      Re-run in a terminal, or pass --on-collision=override|keep-existing|keep-both."
                warned_no_tty=1
            fi
            effective="keep-both"
        fi

        while [ "$effective" = "ask" ]; do
            echo ""
            echo "⚠️  Asset name collision: '$base'"
            echo "      incoming (Obsidian): $incoming_label"
            echo "      existing (repo):     $existing_label"
            echo "   a) Override      — write the Obsidian version into $existing_label"
            echo "   b) Keep existing — discard the incoming copy"
            echo "   c) Keep both     — leaves the embed unresolved (E1) for manual fixup"
            if ! read -r -p "Choose [a/b/c] (A/B/C applies to all remaining): " choice; then
                echo ""
                echo "   Input closed without an answer — keeping both copies."
                effective="keep-both"
                continue
            fi
            case "$choice" in
                a) effective="override" ;;
                b) effective="keep-existing" ;;
                c) effective="keep-both" ;;
                A) effective="override"; policy="override" ;;
                B) effective="keep-existing"; policy="keep-existing" ;;
                C) effective="keep-both"; policy="keep-both" ;;
                *) echo "   Please answer a, b, or c (uppercase to apply to all remaining)." ;;
            esac
        done

        case "$effective" in
            override)
                if cp "$asset" "$existing"; then
                    echo "✏️  Overrode '$existing_label' with the Obsidian version of '$base'"
                    overridden=$((overridden + 1))
                    drop_stale_duplicate "$index" "$stale_path" "$incoming_label"
                else
                    echo "⚠️  Failed to override '$existing' with '$asset'"
                    failed=$((failed + 1))
                fi
                ;;
            keep-existing)
                echo "🛡️  Kept the repo version of '$base' at '$existing_label'"
                kept_existing=$((kept_existing + 1))
                drop_stale_duplicate "$index" "$stale_path" "$incoming_label"
                ;;
            keep-both)
                is_new=0
                [ -f "$dest_path" ] || is_new=1
                mkdir -p "$(dirname "$dest_path")"
                if cp "$asset" "$dest_path"; then
                    echo "⚠️  Kept both copies of '$base' — its ![[…]] embed will be left unresolved (E1)"
                    kept_both=$((kept_both + 1))
                    [ "$is_new" -eq 1 ] && index_asset_add "$index" "$dest_path"
                else
                    echo "⚠️  Failed to copy '$asset' to '$dest_path'"
                    failed=$((failed + 1))
                fi
                ;;
        esac
    done

    rm -f "$index"

    echo "ℹ️ Assets: $copied copied, $identical identical, $overridden overridden, $kept_existing kept-existing, $kept_both kept-both ($routed routed into imgs/)."

    [ "$failed" -eq 0 ]
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
