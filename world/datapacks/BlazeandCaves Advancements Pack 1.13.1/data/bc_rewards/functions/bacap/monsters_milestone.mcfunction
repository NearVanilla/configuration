execute if score milestone bac_settings matches 1 run function bc_rewards:msg/bacap/monsters_milestone
execute if score milestone bac_settings matches -1 unless score blazeandcave:bacap/monsters_milestone bac_obtained matches 1.. run function bc_rewards:msg/bacap/monsters_milestone

execute if score trophy bac_settings matches 1 run function bc_rewards:trophy/bacap/monsters_milestone
execute if score trophy bac_settings matches -1 unless score blazeandcave:bacap/monsters_milestone bac_obtained matches 1.. run function bc_rewards:trophy/bacap/monsters_milestone
execute if score reward bac_settings matches 1 run function bc_rewards:reward/bacap/monsters_milestone
execute if score reward bac_settings matches -1 unless score blazeandcave:bacap/monsters_milestone bac_obtained matches 1.. run function bc_rewards:reward/bacap/monsters_milestone
execute if score exp bac_settings matches 1 run function bc_rewards:exp/bacap/monsters_milestone
execute if score exp bac_settings matches -1 unless score blazeandcave:bacap/monsters_milestone bac_obtained matches 1.. run function bc_rewards:exp/bacap/monsters_milestone

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:bacap/monsters_milestone bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:bacap/monsters_milestone bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:bacap/monsters_milestone