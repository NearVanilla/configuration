# Function runs once per tick
execute as @a[scores={bac_event_death=1..}] run function blazeandcave:event_horizon_fail

# # Dive Bomb - stand on ground fail
execute as @a[advancements={blazeandcave:technical/dive_bomb_check=true},predicate=blazeandcave:is_on_ground] run advancement revoke @s only blazeandcave:technical/dive_bomb_check

# # Dimension Penetration
execute as @e[type=arrow] at @s run function blazeandcave:dimpen_tag

# # Whack-a-mole and Diver's Dozen counting
execute as @a[scores={bac_whack_a_mole_count=1..}] if predicate blazeandcave:is_on_ground run scoreboard players set @s bac_whack_a_mole_count 0
execute as @a[scores={bac_divers_dozen_count=1..}] unless predicate blazeandcave:is_flying run scoreboard players set @s bac_divers_dozen_count 0