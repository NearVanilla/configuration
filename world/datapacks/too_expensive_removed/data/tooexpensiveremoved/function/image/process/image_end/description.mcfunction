# Append blank
function tooexpensiveremoved:image/process/append/blank

data modify storage tooexpensiveremoved:image tellraw append \
  from storage tooexpensiveremoved:image current.description_text

# Append blank
function tooexpensiveremoved:image/process/append/blank

# Append line_break
execute unless score $index.image_data tooexpensiveremoved.image = $length tooexpensiveremoved.image \
  run function tooexpensiveremoved:image/process/append/line_break

# Remove first element from the description
data remove storage tooexpensiveremoved:image current.description[0]
