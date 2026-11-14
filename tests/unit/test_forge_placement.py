"""A forge never seals off part of a floor (VB-125).

Forges block movement and cannot be mined; relocation used to take the nearest free walkable
tile, which could be the only corridor between two rooms.
"""
import logging
from collections import deque

import pytest

from core.base.entity import EntityType
from core.entities import Forge
from core.game import Game
from core.spawning.entity_spawner import EntitySpawner, _ring_order
from core.world import Map, Room, Tile, TileType

pytestmark = pytest.mark.unit


def two_rooms():
    """Room A (x 1-3) <- corridor y=3, x 4-8 -> room B (x 9-12); stairs up in A, down in B.

        ##############
        #...#####....#
        #...#####....#
        #<.........>.#
        #...#####....#
        #...#####....#
        ##############
    """
    m = Map(width=14, height=7)           # the constructor carves a dungeon: start from rock
    m.tiles = [[Tile() for _ in range(m.height)] for _ in range(m.width)]
    m._stairs_up_cache = m._stairs_down_cache = None
    for x, y in [(x, y) for x in range(1, 4) for y in range(1, 6)] + \
                [(x, y) for x in range(9, 13) for y in range(1, 6)] + \
                [(x, 3) for x in range(4, 9)]:
        m.tiles[x][y] = Tile(TileType.FLOOR)
    m.tiles[1][3] = Tile(TileType.STAIRS_UP)
    m.tiles[11][3] = Tile(TileType.STAIRS_DOWN)
    m.rooms = [Room(1, 1, 3, 5), Room(9, 1, 4, 5)]
    return m


def reachable(m, start, blocked):
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n not in seen and n not in blocked and m.in_bounds(*n) and m.is_walkable(*n):
                    seen.add(n)
                    q.append(n)
    return seen


def test_the_old_rule_would_have_plugged_the_corridor():
    """Positive control: from a corridor tile the old search's first free tile is the corridor."""
    m = two_rooms()
    first_free = next(t for t in _ring_order((5, 3), m, 8) if t != (5, 3))
    assert first_free == (4, 3)
    assert (11, 3) not in reachable(m, (1, 3), {first_free})


def test_forge_is_placed_where_it_seals_nothing():
    m = two_rooms()
    forge = Forge(forge_type="basic_forge", x=5, y=3)
    occupied = {(5, 3)}                     # an ore vein holds the forge's first tile
    assert EntitySpawner._claim_forge_tile(forge, occupied, m)
    tile = (forge.x, forge.y)
    assert m.is_walkable(*tile) and tile in occupied and tile != (5, 3)
    whole = reachable(m, (1, 3), set())
    assert reachable(m, (1, 3), {tile}) == whole - {tile}


def test_forge_never_takes_a_stairs_tile():
    m = two_rooms()
    forge = Forge(forge_type="basic_forge", x=1, y=3)       # starts on the up stairs
    occupied = set()
    assert EntitySpawner._claim_forge_tile(forge, occupied, m)
    assert m.tiles[forge.x][forge.y].tile_type == TileType.FLOOR


def test_a_free_safe_first_tile_is_kept():
    m = two_rooms()
    forge = Forge(forge_type="basic_forge", x=10, y=1)      # corner of room B: seals nothing
    assert EntitySpawner._claim_forge_tile(forge, set(), m)
    assert (forge.x, forge.y) == (10, 1)


def test_seed_1006_floor_2_is_no_longer_cut():
    """The floor found by the 480-floor sweep: the forge cut off 162 tiles there."""
    logging.disable(logging.CRITICAL)
    try:
        g = Game()
        g.start_new_game(seed=1006)
        g.descend_floor()
    finally:
        logging.disable(logging.NOTSET)
    st = g.state
    m, p = st.dungeon_map, st.player
    forges = {(e.x, e.y) for e in st.entities.values() if e.entity_type == EntityType.FORGE}
    whole = reachable(m, (p.x, p.y), set())
    assert reachable(m, (p.x, p.y), forges) == whole - forges
