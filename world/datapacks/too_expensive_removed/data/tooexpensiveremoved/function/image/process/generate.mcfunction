#> tooexpensiveremoved:image/generate
#
# This function generates the image data.

data modify storage tooexpensiveremoved:image current.image_data set from storage tooexpensiveremoved:image image_data
data modify storage tooexpensiveremoved:image current.description set from storage tooexpensiveremoved:image description
data modify storage tooexpensiveremoved:image current.pixel_character set \
  from storage tooexpensiveremoved:image pixel_character.pixel

# Reset index score
scoreboard players set $index.image_data tooexpensiveremoved.image 0
# Set width
execute store result score $width tooexpensiveremoved.image run data get storage tooexpensiveremoved:image width
# Set height
execute store result score $height tooexpensiveremoved.image run data get storage tooexpensiveremoved:image height
# Set length
scoreboard players operation $length tooexpensiveremoved.image = $width tooexpensiveremoved.image
scoreboard players operation $length tooexpensiveremoved.image *= $height tooexpensiveremoved.image
# Clear remaining entries in tellraw
data remove storage tooexpensiveremoved:image tellraw

# Add spacing on top
function tooexpensiveremoved:image/process/append/line_break
# Loop over image data
function tooexpensiveremoved:image/process/loop_over_image_data
# Add spacing on bottom
function tooexpensiveremoved:image/process/append/line_break
