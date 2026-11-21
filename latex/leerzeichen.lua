-- Puts a space character before every interword glue at shipout, followed
-- by a kern of the same negative width, so that the layout stays unchanged
-- but tools extracting text from the PDF find the word boundaries.

local GLYPH, GLUE = node.id('glyph'), node.id('glue')
local SPACESKIP, XSPACESKIP = 13, 14
local width = {}

local function space_width(f)
  if width[f] == nil then
    local c = font.getfont(f).characters[32]
    width[f] = c and c.width or false
  end
  return width[f]
end

local function walk(head)
  local f
  for n in node.traverse(head) do
    if n.id == GLYPH then
      f = n.font
    elseif n.head then
      n.head = walk(n.head)
    elseif n.id == GLUE and f and (n.subtype == SPACESKIP
        or n.subtype == XSPACESKIP) and space_width(f) then
      local g = node.new(GLYPH)
      g.font, g.char = f, 32
      local k = node.new('kern')
      k.kern = -space_width(f)
      head = node.insert_before(head, n, g)
      head = node.insert_before(head, n, k)
    end
  end
  return head
end

luatexbase.add_to_callback('pre_shipout_filter', function(head)
  return walk(head)
end, 'leerzeichen')
