summon chest_minecart ~ ~10 ~ {Tags:["summoned_by_tooexpensiveremoved"]}

$item replace entity @e[tag=summoned_by_tooexpensiveremoved,type=chest_minecart,limit=1] container.0 from entity @s hotbar.$(hotbar_slot)

data modify entity @e[tag=summoned_by_tooexpensiveremoved,type=chest_minecart,limit=1] Items[{Slot:0b}].components.minecraft:repair_cost set value 20

$item replace entity @s hotbar.$(hotbar_slot) from entity @e[tag=summoned_by_tooexpensiveremoved,type=chest_minecart,limit=1] container.0

kill @e[tag=summoned_by_tooexpensiveremoved,type=chest_minecart,limit=1]