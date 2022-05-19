execute if score goal bac_settings matches 1 run function bc_rewards:msg/mining/flint_miner
execute if score goal bac_settings matches -1 unless score blazeandcave:mining/flint_miner bac_obtained matches 1.. run function bc_rewards:msg/mining/flint_miner
execute if score reward bac_settings matches 1 run function bc_rewards:reward/mining/flint_miner
execute if score reward bac_settings matches -1 unless score blazeandcave:mining/flint_miner bac_obtained matches 1.. run function bc_rewards:reward/mining/flint_miner
execute if score exp bac_settings matches 1 run function bc_rewards:exp/mining/flint_miner
execute if score exp bac_settings matches -1 unless score blazeandcave:mining/flint_miner bac_obtained matches 1.. run function bc_rewards:exp/mining/flint_miner

scoreboard players add @s bac_advancements 1
execute unless score blazeandcave:mining/flint_miner bac_obtained matches 1.. run scoreboard players add @s bac_advfirst 1
scoreboard players add blazeandcave:mining/flint_miner bac_obtained 1
execute if score coop bac_settings matches 1 run advancement grant @a only blazeandcave:mining/flint_miner