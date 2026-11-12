"""No two spawned entities (monsters, ore veins, forges) may share a tile on any seeded floor.

Regression for VB-46: the forge always landed on the first ore vein, and special-room
extras (dens, ore chambers, treasure rooms) landed on anything.
"""

import pytest

from src.core.config import ConfigLoader
from src.core.entity_loader import EntityLoader
from src.core.rng import GameRNG
from src.core.spawning import EntitySpawner
from src.core.world import Map


@pytest.mark.parametrize("seed", range(1, 25))
@pytest.mark.parametrize("floor", [1, 6, 12])
def test_spawned_entities_never_share_a_tile(seed, floor):
    rng = GameRNG.initialize(seed)
    dungeon_map = Map(width=60, height=30, rng=rng)
    spawned = EntitySpawner(ConfigLoader.get_config(), EntityLoader()).spawn_all_for_floor(floor, dungeon_map)
    tiles = [(e.x, e.y) for group in spawned.values() for e in group]
    assert len(tiles) == len(set(tiles))
    assert all(dungeon_map.is_walkable(x, y) for x, y in tiles)
