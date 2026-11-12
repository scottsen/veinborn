"""Floor descent invariants shared by single-player and multiplayer (VB-25)."""

from unittest.mock import patch

import pytest

from core.game import Game
from core.base.entity import EntityType

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=42)
    return g


def test_player_stays_in_entities_after_descent(game):
    """VB-23 made entities the single store the player is mirrored into; the
    old entities.clear() on descent silently dropped the player again, so
    get_entity(player_id) returned None from floor 2 on."""
    player = game.state.player

    game.descend_floor()

    assert game.state.current_floor == 2
    assert game.state.entities.get(player.entity_id) is player
    assert game.context.get_entity(player.entity_id) is player


def test_descent_still_clears_previous_floor_entities(game):
    old_ids = {
        e.entity_id
        for e in game.state.entities.values()
        if e.entity_type != EntityType.PLAYER
    }
    assert old_ids

    game.descend_floor()

    assert not old_ids & set(game.state.entities)


def test_descent_spawns_new_floor_entities(game):
    game.descend_floor()

    kinds = {e.entity_type for e in game.state.entities.values()}
    assert EntityType.MONSTER in kinds


def test_descent_spawns_special_room_entities_like_floor_one(game):
    """Floor 1 (via the bootstrapper) spawned special-room entities but
    FloorManager did not, so treasure rooms/monster dens were empty on 2+."""
    spawner = game.floor_manager.spawner
    with patch.object(
        spawner, "spawn_special_room_entities", wraps=spawner.spawn_special_room_entities
    ) as spy:
        game.descend_floor()

    spy.assert_called_once()
    assert spy.call_args.args[0] == 2


def test_clear_floor_entities_keeps_player_and_named_ids(game):
    state = game.state
    others = [e.entity_id for e in state.entities.values() if e.entity_id != state.player.entity_id]
    keep = others[0]

    state.clear_floor_entities(keep_ids=[keep])

    assert set(state.entities) == {state.player.entity_id, keep}


def test_spawn_all_for_floor_includes_special_rooms(game):
    from types import SimpleNamespace
    spawner = game.floor_manager.spawner
    # Off-map positions so the same-tile de-duplication never drops them.
    bonus_monster = SimpleNamespace(x=-1, y=-1)
    bonus_ore = SimpleNamespace(x=-2, y=-2)
    with patch.object(
        spawner,
        "spawn_special_room_entities",
        return_value={'monsters': [bonus_monster], 'ores': [bonus_ore], 'items': []},
    ):
        spawned = spawner.spawn_all_for_floor(2, game.state.dungeon_map)

    assert bonus_monster in spawned['monsters']
    assert bonus_ore in spawned['ore_veins']
    assert set(spawned) == {'monsters', 'ore_veins', 'forges'}


def test_get_victory_floor_reads_config_and_falls_back():
    from types import SimpleNamespace
    from core.floor_manager import get_victory_floor, DEFAULT_VICTORY_FLOOR

    configured = SimpleNamespace(game_constants={'progression': {'victory_floor': 7}})
    assert get_victory_floor(configured) == 7
    assert get_victory_floor(SimpleNamespace(game_constants={})) == DEFAULT_VICTORY_FLOOR
    assert get_victory_floor(object()) == DEFAULT_VICTORY_FLOOR
    bad_type = SimpleNamespace(game_constants={'progression': {'victory_floor': "x"}})
    assert get_victory_floor(bad_type) == DEFAULT_VICTORY_FLOOR
