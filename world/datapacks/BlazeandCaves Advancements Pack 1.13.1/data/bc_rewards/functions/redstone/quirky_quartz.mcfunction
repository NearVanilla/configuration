execute if score task bac_settings matches 1 run function bc_rewards:msg/redstone/quirky_quartz
execute if score task bac_settings matches -1 unless score blazeandcave:redstone/quirky_quartz bac_obtained matches 1.. run function bc_rewards:msg/redstone/quirky_quartz
execute if score reward bac_settings matches 1 run function bc_rewards:reward/redstone/quirky_quartz
execute if score reward bac_settings matches -1 unless score blazeandcave:redstone/quirky_quartz bac_obtained matches 1.. run function bc_rewards:reward/redstone/quirky_quartz
execute if score exp bac_settings matches 1 run function bc_rewards:exp/redstone/quirky_quartz
execute if score exp bac_settings matches -1 unless score blazeandcave:redstone/quirky_quartz bac_obtained matches 1.. run function bc_rewards:exp/redstone/quirky_quartz

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:redstone/quirky_quartz bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:redstone/quirky_quartz bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:redstone/quirky_quartz