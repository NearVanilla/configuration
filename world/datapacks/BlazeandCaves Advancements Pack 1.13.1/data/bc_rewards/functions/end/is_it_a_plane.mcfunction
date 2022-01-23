execute if score task bac_settings matches 1 run function bc_rewards:msg/end/is_it_a_plane
execute if score task bac_settings matches -1 unless score minecraft:adventure/spyglass_at_dragon bac_obtained matches 1.. run function bc_rewards:msg/end/is_it_a_plane
execute if score reward bac_settings matches 1 run function bc_rewards:reward/end/is_it_a_plane
execute if score reward bac_settings matches -1 unless score minecraft:adventure/spyglass_at_dragon bac_obtained matches 1.. run function bc_rewards:reward/end/is_it_a_plane
execute if score exp bac_settings matches 1 run function bc_rewards:exp/end/is_it_a_plane
execute if score exp bac_settings matches -1 unless score minecraft:adventure/spyglass_at_dragon bac_obtained matches 1.. run function bc_rewards:exp/end/is_it_a_plane

scoreboard players add @s bac_advancements 1
execute unless score minecraft:adventure/spyglass_at_dragon bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add minecraft:adventure/spyglass_at_dragon bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only minecraft:adventure/spyglass_at_dragon