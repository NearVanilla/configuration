execute if score task bac_settings matches 1 run function bc_rewards:msg/potion/hyper_healing
execute if score task bac_settings matches -1 unless score blazeandcave:potion/hyper_healing bac_obtained matches 1.. run function bc_rewards:msg/potion/hyper_healing
execute if score reward bac_settings matches 1 run function bc_rewards:reward/potion/hyper_healing
execute if score reward bac_settings matches -1 unless score blazeandcave:potion/hyper_healing bac_obtained matches 1.. run function bc_rewards:reward/potion/hyper_healing
execute if score exp bac_settings matches 1 run function bc_rewards:exp/potion/hyper_healing
execute if score exp bac_settings matches -1 unless score blazeandcave:potion/hyper_healing bac_obtained matches 1.. run function bc_rewards:exp/potion/hyper_healing

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:potion/hyper_healing bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:potion/hyper_healing bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:potion/hyper_healing
