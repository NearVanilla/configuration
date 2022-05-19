execute if score task bac_settings matches 1 run function bc_rewards:msg/farming/a_seedy_place
execute if score task bac_settings matches -1 unless score minecraft:husbandry/plant_seed bac_obtained matches 1.. run function bc_rewards:msg/farming/a_seedy_place

execute if score reward bac_settings matches 1 run function bc_rewards:reward/farming/a_seedy_place
execute if score reward bac_settings matches -1 unless score minecraft:husbandry/plant_seed bac_obtained matches 1.. run function bc_rewards:reward/farming/a_seedy_place
execute if score exp bac_settings matches 1 run function bc_rewards:exp/farming/a_seedy_place
execute if score exp bac_settings matches -1 unless score minecraft:husbandry/plant_seed bac_obtained matches 1.. run function bc_rewards:exp/farming/a_seedy_place

scoreboard players add @s bac_advancements 1
execute unless score minecraft:husbandry/plant_seed bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add minecraft:husbandry/plant_seed bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only minecraft:husbandry/plant_seed