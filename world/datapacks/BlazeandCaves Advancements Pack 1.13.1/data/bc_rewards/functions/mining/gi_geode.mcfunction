execute if score task bac_settings matches 1 run function bc_rewards:msg/mining/gi_geode
execute if score task bac_settings matches -1 unless score blazeandcave:mining/gi_geode bac_obtained matches 1.. run function bc_rewards:msg/mining/gi_geode
execute if score reward bac_settings matches 1 run function bc_rewards:reward/mining/gi_geode
execute if score reward bac_settings matches -1 unless score blazeandcave:mining/gi_geode bac_obtained matches 1.. run function bc_rewards:reward/mining/gi_geode
execute if score exp bac_settings matches 1 run function bc_rewards:exp/mining/gi_geode
execute if score exp bac_settings matches -1 unless score blazeandcave:mining/gi_geode bac_obtained matches 1.. run function bc_rewards:exp/mining/gi_geode

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:mining/gi_geode bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:mining/gi_geode bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:mining/gi_geode