local hidden_kinds = {}

local function read_visibility(meta)
  local visibility = meta["post-kind-visibility"]
  if visibility == nil then
    return nil
  end

  for kind, is_visible in pairs(visibility) do
    hidden_kinds[kind] = is_visible == false or pandoc.utils.stringify(is_visible) == "false"
  end
end

local function remove_hidden_section(div)
  local kind = div.attributes["data-post-kind"]
  if kind ~= nil and hidden_kinds[kind] then
    return {}
  end
end

return {
  { Meta = read_visibility },
  { Div = remove_hidden_section }
}
