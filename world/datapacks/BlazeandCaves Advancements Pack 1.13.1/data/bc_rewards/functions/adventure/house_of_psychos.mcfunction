execute if score task bac_settings matches 1 run function bc_rewards:msg/adventure/house_of_psychos
execute if score task bac_settings matches -1 unless score blazeandcave:adventure/house_of_psychos bac_obtained matches 1.. run function bc_rewards:msg/adventure/house_of_psychos
execute if score reward bac_settings matches 1 run function bc_rewards:reward/adventure/house_of_psychos
execute if score reward bac_settings matches -1 unless score blazeandcave:adventure/house_of_psychos bac_obtained matches 1.. run function bc_rewards:reward/adventure/house_of_psychos
execute if score exp bac_settings matches 1 run function bc_rewards:exp/adventure/house_of_psychos
execute if score exp bac_settings matches -1 unless score blazeandcave:adventure/house_of_psychos bac_obtained matches 1.. run function bc_rewards:exp/adventure/house_of_psychos

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:adventure/house_of_psychos bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:adventure/house_of_psychos bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:adventure/house_of_psychos