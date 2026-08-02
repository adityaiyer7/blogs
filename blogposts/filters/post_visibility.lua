-- Selects the homepage layout from the switches in _post_visibility.yml.
--
-- With at least one kind enabled, the homepage is sectioned: disabled sections
-- are dropped and the chronological fallback listing is dropped. With every
-- kind disabled, that inverts -- all four sections go and the fallback listing
-- is what remains, so the homepage degrades to a single chronological list
-- rather than rendering empty.
--
-- This filter removes headings, section prose, and the placement divs. It does
-- not and cannot remove the listings themselves: Quarto injects listing markup
-- after every Lua filter phase, so a listing whose placement div was deleted is
-- appended to the end of the page rather than disappearing. Disabled listings
-- are emptied instead -- by drafts for a disabled kind, and by the
-- sections-active gate when no kind is enabled (see
-- scripts/update_post_visibility.py). An emptied listing leaves only an empty
-- container and a d-none "No matching items" node, which render as nothing.

local hidden_kinds = {}
local any_kind_enabled = false

local function read_visibility(meta)
  local visibility = meta["post-kind-visibility"]
  if visibility == nil then
    return nil
  end

  for kind, is_visible in pairs(visibility) do
    local is_hidden = is_visible == false or pandoc.utils.stringify(is_visible) == "false"
    hidden_kinds[kind] = is_hidden
    if not is_hidden then
      any_kind_enabled = true
    end
  end
end

local function select_homepage_sections(div)
  -- The fallback listing survives only when no section is enabled.
  if div.attributes["data-post-fallback"] ~= nil then
    if any_kind_enabled then
      return {}
    end
    return nil
  end

  local kind = div.attributes["data-post-kind"]
  if kind ~= nil and hidden_kinds[kind] then
    return {}
  end
end

return {
  { Meta = read_visibility },
  { Div = select_homepage_sections }
}
