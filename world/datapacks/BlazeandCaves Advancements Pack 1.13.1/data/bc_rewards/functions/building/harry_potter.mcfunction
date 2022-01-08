execute if score challenge bac_settings matches 1 run function bc_rewards:msg/building/harry_potter
execute if score challenge bac_settings matches -1 unless score blazeandcave:building/harry_potter bac_obtained matches 1.. run function bc_rewards:msg/building/harry_potter

execute if score trophy bac_settings matches 1 run function bc_rewards:trophy/building/harry_potter
execute if score trophy bac_settings matches -1 unless score blazeandcave:building/harry_potter bac_obtained matches 1.. run function bc_rewards:trophy/building/harry_potter
execute if score reward bac_settings matches 1 run function bc_rewards:reward/building/harry_potter
execute if score reward bac_settings matches -1 unless score blazeandcave:building/harry_potter bac_obtained matches 1.. run function bc_rewards:reward/building/harry_potter
execute if score exp bac_settings matches 1 run function bc_rewards:exp/building/harry_potter
execute if score exp bac_settings matches -1 unless score blazeandcave:building/harry_potter bac_obtained matches 1.. run function bc_rewards:exp/building/harry_potter

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:building/harry_potter bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:building/harry_potter bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:building/harry_potter