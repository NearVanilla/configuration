execute if score challenge bac_settings matches 1 run function bc_rewards:msg/building/armor_display
execute if score challenge bac_settings matches -1 unless score blazeandcave:building/armor_display bac_obtained matches 1.. run function bc_rewards:msg/building/armor_display

execute if score trophy bac_settings matches 1 run function bc_rewards:trophy/building/armor_display
execute if score trophy bac_settings matches -1 unless score blazeandcave:building/armor_display bac_obtained matches 1.. run function bc_rewards:trophy/building/armor_display
execute if score reward bac_settings matches 1 run function bc_rewards:reward/building/armor_display
execute if score reward bac_settings matches -1 unless score blazeandcave:building/armor_display bac_obtained matches 1.. run function bc_rewards:reward/building/armor_display
execute if score exp bac_settings matches 1 run function bc_rewards:exp/building/armor_display
execute if score exp bac_settings matches -1 unless score blazeandcave:building/armor_display bac_obtained matches 1.. run function bc_rewards:exp/building/armor_display

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:building/armor_display bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:building/armor_display bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:building/armor_display