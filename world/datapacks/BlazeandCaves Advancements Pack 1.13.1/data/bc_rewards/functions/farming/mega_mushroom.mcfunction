execute if score task bac_settings matches 1 run function bc_rewards:msg/farming/mega_mushroom
execute if score task bac_settings matches -1 unless score blazeandcave:farming/mega_mushroom bac_obtained matches 1.. run function bc_rewards:msg/farming/mega_mushroom
execute if score reward bac_settings matches 1 run function bc_rewards:reward/farming/mega_mushroom
execute if score reward bac_settings matches -1 unless score blazeandcave:farming/mega_mushroom bac_obtained matches 1.. run function bc_rewards:reward/farming/mega_mushroom
execute if score exp bac_settings matches 1 run function bc_rewards:exp/farming/mega_mushroom
execute if score exp bac_settings matches -1 unless score blazeandcave:farming/mega_mushroom bac_obtained matches 1.. run function bc_rewards:exp/farming/mega_mushroom

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:farming/mega_mushroom bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:farming/mega_mushroom bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:farming/mega_mushroom