"""Entity spawning system for Veinborn.

This module handles all entity creation and placement logic,
separating spawning concerns from the main Game class.
"""

from .entity_spawner import EntitySpawner
from .spawn_policy import (
    find_player_spawn_positions,
    find_monster_positions,
    find_ore_vein_positions,
    assign_special_rooms,
    place_stairs_down,
    place_stairs_up,
)

__all__ = [
    'EntitySpawner',
    'find_player_spawn_positions',
    'find_monster_positions',
    'find_ore_vein_positions',
    'assign_special_rooms',
    'place_stairs_down',
    'place_stairs_up',
]
