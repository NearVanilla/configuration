execute if score task bac_settings matches 1 run function bc_rewards:msg/animal/milk_does_your_body_good
execute if score task bac_settings matches -1 unless score blazeandcave:animal/milk_does_your_body_good bac_obtained matches 1.. run function bc_rewards:msg/animal/milk_does_your_body_good
execute if score reward bac_settings matches 1 run function bc_rewards:reward/animal/milk_does_your_body_good
execute if score reward bac_settings matches -1 unless score blazeandcave:animal/milk_does_your_body_good bac_obtained matches 1.. run function bc_rewards:reward/animal/milk_does_your_body_good
execute if score exp bac_settings matches 1 run function bc_rewards:exp/animal/milk_does_your_body_good
execute if score exp bac_settings matches -1 unless score blazeandcave:animal/milk_does_your_body_good bac_obtained matches 1.. run function bc_rewards:exp/animal/milk_does_your_body_good

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:animal/milk_does_your_body_good bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:animal/milk_does_your_body_good bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:animal/milk_does_your_body_good