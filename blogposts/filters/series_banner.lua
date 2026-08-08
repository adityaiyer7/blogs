--[[
  series_banner.lua — links a post back to the series it belongs to.

  A post opts into a series with three front-matter fields (see
  docs/design/series.md):

      series-id: representational-geometry
      series: "Representational Geometry from First Principles"
      series-order: 10

  This filter turns those into a small banner at the top of the post page. It
  is generated from metadata rather than written into the body on purpose:
  sync_post.sh regenerates post bodies from Obsidian while preserving
  repository-managed front matter, so anything hand-written into the body would
  be lost on the next sync.

  Gating mirrors reading-time.lua: HTML output only, and only documents that
  actually declare a series. Everything else is returned untouched.

  The banner deliberately shows no "part N of M". `series-order` values are
  sparse by convention (10, 20, 30) so posts can be slotted in later, a series
  may be published incomplete, and a post whose kind is disabled drops out of
  listings entirely — so no denominator computed here would be true for long.
  The landing page shows the real sequence.

  Ordering note: this filter is registered *after* reading-time.lua in
  _quarto.yml. Both insert at block 1, so whichever runs last ends up on top —
  which is what puts the series banner above the reading-time line.

  The link is site-root-relative (/series/<id>/). Quarto rewrites those against
  the site root at render time, which is what keeps them correct under the
  GitHub Pages /blogs/ subpath.
]]

function Pandoc(doc)
  if not quarto.doc.is_format("html:js") then return nil end

  local series_id = doc.meta["series-id"]
  local series_title = doc.meta["series"]
  local series_order = doc.meta["series-order"]
  if not series_id or not series_title or not series_order then return nil end

  local id = pandoc.utils.stringify(series_id)
  local title = pandoc.utils.stringify(series_title)
  if id == "" or title == "" then return nil end

  local banner = pandoc.Div(
    pandoc.Plain {
      pandoc.Str("Series:"),
      pandoc.Space(),
      pandoc.Link(pandoc.Str(title), "/series/" .. id .. "/"),
    },
    pandoc.Attr("", { "series-banner" })
  )

  doc.blocks:insert(1, banner)
  return doc
end
