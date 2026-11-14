"""Fog of war per viewer (VB-105, plan D4)."""

import json

import pytest

from core import fog
from core.entities import Monster
from core.game import Game
from core.snapshot import Snapshot, build_snapshot


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=7)
    return g


def _far_floor_tile(state, away_from, min_dist):
    m = state.dungeon_map
    px, py = away_from
    for x in range(m.width):
        for y in range(m.height):
            if m.is_walkable(x, y) and (x - px) ** 2 + (y - py) ** 2 > min_dist ** 2:
                return x, y
    raise AssertionError("no far tile")


def _put_monster(state, x, y):
    mon = next(e for e in state.entities.values() if isinstance(e, Monster))
    mon.x, mon.y = x, y
    return mon


def test_a_new_viewer_sees_only_nearby_terrain(game):
    snap = build_snapshot(game.state)
    flat = "".join(snap.map.tiles)
    assert fog.UNSEEN in flat and flat.strip()
    px, py = game.state.player.x, game.state.player.y
    assert snap.map.tiles[py][px] != fog.UNSEEN
    assert snap.map.lit[py][px] == "1"
    assert not snap.reveal_map


def test_lit_tiles_are_within_the_vision_radius(game):
    state = game.state
    snap = build_snapshot(state)
    px, py = state.player.x, state.player.y
    lit = [(x, y) for y, row in enumerate(snap.map.lit) for x, c in enumerate(row) if c == "1"]
    assert len(lit) > 1
    assert all((x - px) ** 2 + (y - py) ** 2 <= fog.VISION_RADIUS ** 2 for x, y in lit)


def test_a_wall_blocks_sight_and_is_itself_seen():
    from core.world import Map, Tile, TileType
    m = Map(width=12, height=5)
    for x in range(12):
        for y in range(5):
            m.tiles[x][y] = Tile(TileType.FLOOR)
    m.tiles[5][2] = Tile(TileType.WALL)
    lit = fog.observe(m, "v", 2, 2)
    assert (5, 2) in lit            # the wall that stops the sight is seen
    assert (7, 2) not in lit        # what is behind it is not
    assert (4, 2) in lit


def test_monsters_show_only_while_in_sight(game):
    state = game.state
    p = state.player
    far = _far_floor_tile(state, (p.x, p.y), fog.VISION_RADIUS + 3)
    mon = _put_monster(state, *far)
    assert mon.entity_id not in {e.entity_id for e in build_snapshot(state).entities}

    mon.x, mon.y = p.x, p.y          # on top of the viewer: certainly lit
    assert mon.entity_id in {e.entity_id for e in build_snapshot(state).entities}


def test_memory_remains_after_the_viewer_walks_away(game):
    state = game.state
    p = state.player
    first = build_snapshot(state)
    seen_before = {(x, y) for y, row in enumerate(first.map.tiles)
                   for x, c in enumerate(row) if c != fog.UNSEEN}
    p.x, p.y = _far_floor_tile(state, (p.x, p.y), fog.VISION_RADIUS + 3)
    second = build_snapshot(state)
    seen_after = {(x, y) for y, row in enumerate(second.map.tiles)
                  for x, c in enumerate(row) if c != fog.UNSEEN}
    assert seen_before < seen_after
    # remembered but out of sight: dim, not lit
    x, y = next(iter(seen_before))
    assert second.map.lit[y][x] == "0"


def test_each_viewer_has_their_own_memory(game):
    state = game.state
    p = state.player
    far = _far_floor_tile(state, (p.x, p.y), fog.VISION_RADIUS + 3)
    fog.observe(state.dungeon_map, "someone-else", *far)
    build_snapshot(state)
    mine = state.dungeon_map.explored_by[p.entity_id]
    theirs = state.dungeon_map.explored_by["someone-else"]
    assert far in theirs and far not in mine


def test_ore_veins_are_remembered_and_other_players_always_shown(game):
    from core.entities import OreVein, Player
    state = game.state
    p = state.player
    vein = OreVein.generate_random("iron", p.x, p.y, 1)     # on the viewer's own tile: explored
    state.entities[vein.entity_id] = vein
    buddy = Player(x=0, y=0, name="Buddy")
    state.entities[buddy.entity_id] = buddy
    build_snapshot(state)
    p.x, p.y = _far_floor_tile(state, (p.x, p.y), fog.VISION_RADIUS + 3)
    ids = {e.entity_id for e in build_snapshot(state).entities}
    assert vein.entity_id in ids
    assert buddy.entity_id in ids


def test_reveal_switch_sends_the_whole_floor(game):
    game.state.reveal_map = True
    snap = build_snapshot(game.state)
    assert snap.reveal_map
    assert snap.map.tiles == game.state.dungeon_map.to_dict()["tiles"]
    assert snap.map.lit == []
    monsters = [e for e in snap.entities if e.entity_type == "monster"]
    assert len(monsters) == sum(1 for e in game.state.entities.values() if e.entity_type.value == 'monster')


def test_snapshot_round_trips_with_fog_fields(game):
    snap = build_snapshot(game.state)
    back = Snapshot.from_dict(json.loads(json.dumps(snap.to_dict())))
    assert back.map.lit == snap.map.lit and back.map.tiles == snap.map.tiles
    assert back.reveal_map is False


def test_a_new_floor_starts_with_no_memory(game):
    state = game.state
    build_snapshot(state)
    assert state.dungeon_map.explored_by
    from core.world import Map
    fresh = Map(width=state.dungeon_map.width, height=state.dungeon_map.height)
    assert fresh.explored_by == {}
