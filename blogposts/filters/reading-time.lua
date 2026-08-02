--[[
  reading-time.lua — estimated reading time for individual blog posts.

  Quarto computes reading time natively for listings only
  (see https://github.com/quarto-dev/quarto-cli/discussions/6883). This filter
  surfaces the same estimate on each post page by counting words in the body and
  injecting a "N min read" line into the header, matching Quarto's
  200-words-per-minute calculation.

  Counting: we walk the whole body AST and tally whitespace-separated tokens in
  every text-bearing node — prose, code, math, raw HTML, and (crucially) table
  cells. A plain `pandoc.utils.stringify` drops table content, so table-heavy
  posts would undercount; the walk keeps the estimate within ~1 minute of
  Quarto's listing value (verified against the site's existing posts).

  Scope:
    - HTML output only (any non-HTML format is left untouched).
    - Post pages only: gated on a `date` in the front matter, so the homepage
      listing and standalone pages (which carry no `date`) are skipped.

  No per-post metadata is required; the estimate recomputes on every render.
]]

local WORDS_PER_MINUTE = 200

function Pandoc(doc)
  -- Only annotate HTML post pages that carry a date; leave the homepage
  -- listing, standalone pages, and non-HTML formats unchanged.
  if not quarto.doc.is_format("html:js") then return nil end
  if not doc.meta.date then return nil end

  local words = 0
  local function tally(text)
    for _ in text:gmatch("%S+") do
      words = words + 1
    end
  end

  doc.blocks:walk {
    Str       = function(e) tally(e.text) end,
    Code      = function(e) tally(e.text) end,
    CodeBlock = function(e) tally(e.text) end,
    Math      = function(e) tally(e.text) end,
    RawInline = function(e) tally(e.text) end,
    RawBlock  = function(e) tally(e.text) end,
  }

  local minutes = math.max(1, math.ceil(words / WORDS_PER_MINUTE))
  local reading_time = pandoc.Div(
    pandoc.Plain(pandoc.Str(minutes .. " min read")),
    pandoc.Attr("", { "reading-time" })
  )

  doc.blocks:insert(1, reading_time)
  return doc
end
