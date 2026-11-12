"""No two spawned monsters may share a tile on any seeded floor.

Ore veins and forges still overlap each other (and occasionally a monster) -- see the
spawner overlap task in TASKS.md; this test covers the monster-on-monster case only.
"""

import pytest

from src.core.config import ConfigLoader
from src.core.entity_loader import EntityLoader
from src.core.rng import GameRNG
from src.core.spawning import EntitySpawner
from src.core.world import Map


@pytest.mark.parametrize("seed", range(1, 25))
@pytest.mark.parametrize("floor", [1, 6, 12])
def test_spawned_monsters_never_share_a_tile(seed, floor):
    rng = GameRNG.initialize(seed)
    dungeon_map = Map(width=60, height=30, rng=rng)
    spawned = EntitySpawner(ConfigLoader.get_config(), EntityLoader()).spawn_all_for_floor(floor, dungeon_map)
    tiles = [(m.x, m.y) for m in spawned['monsters']]
    assert len(tiles) == len(set(tiles))
