# Copy current pixel
data modify storage tooexpensiveremoved:image current.pixel_color set \
  from storage tooexpensiveremoved:image current.image_data[0]
data modify storage tooexpensiveremoved:image current.description_text set \
  from storage tooexpensiveremoved:image current.description[0]

scoreboard players add $index.image_data tooexpensiveremoved.image 1

# Calculate column
scoreboard players operation $index.column tooexpensiveremoved.image = $index.image_data tooexpensiveremoved.image
scoreboard players operation $index.column tooexpensiveremoved.image %= $width tooexpensiveremoved.image

# Calculate row
scoreboard players operation $index.row tooexpensiveremoved.image = $index.image_data tooexpensiveremoved.image
scoreboard players operation $index.row tooexpensiveremoved.image /= $width tooexpensiveremoved.image

# Append start spacing
execute if score $index.column tooexpensiveremoved.image matches 1 run \
  function tooexpensiveremoved:image/process/append/blank

# Append colored pixel
execute unless data storage tooexpensiveremoved:image current{pixel_color: ""} run \
  function tooexpensiveremoved:image/process/append/pixel
# Append background pixel
execute if data storage tooexpensiveremoved:image current{pixel_color: ""} run \
  function tooexpensiveremoved:image/process/append/background

# Append description
execute if score $index.column tooexpensiveremoved.image matches 0 run \
    function tooexpensiveremoved:image/process/image_end/description

# Remove first element from the image_data array
data remove storage tooexpensiveremoved:image current.image_data[0]
# Loop over rows
execute if score $index.row tooexpensiveremoved.image < $height tooexpensiveremoved.image run \
  function tooexpensiveremoved:image/process/loop_over_image_data
