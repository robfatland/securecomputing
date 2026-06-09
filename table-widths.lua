-- Pandoc Lua filter: force tables to use full page width with proportional columns
-- and add vertical padding between rows for readability in PDF output.
function Table(tbl)
  -- If the table has no explicit column widths, assign proportional ones
  local dominated_by_default = true
  for _, w in ipairs(tbl.colspecs) do
    if w[2] ~= nil and w[2] ~= 0 then
      dominated_by_default = false
      break
    end
  end
  if dominated_by_default then
    local ncols = #tbl.colspecs
    if ncols == 2 then
      -- 2-column tables (Glossary, Doc tables): narrow left, wide right
      tbl.colspecs[1][2] = 0.18
      tbl.colspecs[2][2] = 0.82
    elseif ncols == 3 then
      tbl.colspecs[1][2] = 0.18
      tbl.colspecs[2][2] = 0.38
      tbl.colspecs[3][2] = 0.44
    elseif ncols == 4 then
      tbl.colspecs[1][2] = 0.15
      tbl.colspecs[2][2] = 0.28
      tbl.colspecs[3][2] = 0.28
      tbl.colspecs[4][2] = 0.29
    else
      -- Equal distribution for 5+ columns
      local w = 1.0 / ncols
      for i, spec in ipairs(tbl.colspecs) do
        spec[2] = w
      end
    end
  end
  return tbl
end
