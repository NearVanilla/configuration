#> tooexpensiveremoved:app/main.mcfunction
# Execute each minecraft tick

# Listen for help
scoreboard players enable @a help.tooexpensiveremoved
execute as @a if score @s help.tooexpensiveremoved matches 1 run function tooexpensiveremoved:app/help/trigger_help

# Get repair cost
execute as @a store result score @s tooexpensiveremoved.check run data get entity @s SelectedItem.components.minecraft:repair_cost

# Execute replace item
execute as @a[scores={tooexpensiveremoved.check=30..}] run function tooexpensiveremoved:app/item/get_hotbar_slot

