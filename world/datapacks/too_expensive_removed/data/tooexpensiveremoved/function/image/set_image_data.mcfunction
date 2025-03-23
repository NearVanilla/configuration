#> tooexpensiveremoved:image/set_image_data
#
# This function sets the image data.
#
# @input $(image_data) {string[][]} The data to set  
# @input $(width) {number} The width of the image  
# @input $(height) {number} The height of the image  
# @input $(background_color) {string} The background color of the image  
# @input $(description) {string[]} The description on the right hand side  
# @writes storage tooexpensiveremoved:image image_data  
# @writes storage tooexpensiveremoved:image width  
# @writes storage tooexpensiveremoved:image height  
# @writes storage tooexpensiveremoved:image background_color  
# @writes storage tooexpensiveremoved:image description  
# @writes storage tooexpensiveremoved:image pixel_character.blank  
# @writes storage tooexpensiveremoved:image pixel_character.chat  
# @writes storage tooexpensiveremoved:image pixel_character.lore

data remove storage tooexpensiveremoved:image image_data
data remove storage tooexpensiveremoved:image width
data remove storage tooexpensiveremoved:image height
data remove storage tooexpensiveremoved:image background_color
data remove storage tooexpensiveremoved:image description

$data modify storage tooexpensiveremoved:image image_data set value $(image_data)
$data modify storage tooexpensiveremoved:image width set value $(width)
$data modify storage tooexpensiveremoved:image height set value $(height)
$data modify storage tooexpensiveremoved:image background_color set value "$(background_color)"
$data modify storage tooexpensiveremoved:image description set value $(description)

data modify storage tooexpensiveremoved:image pixel_character.blank set value '"　"'
data modify storage tooexpensiveremoved:image pixel_character.pixel set value '"▌▌"'
data modify storage tooexpensiveremoved:image pixel_character.line_break set value '"\\n"'

function tooexpensiveremoved:image/process/generate
