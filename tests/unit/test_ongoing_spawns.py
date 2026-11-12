"""NetHack-style ongoing monster spawns (VB-52)."""

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


def _monsters(game):
    return [e for e in game.state.entities.values()
            if e.entity_type == EntityType.MONSTER and e.is_alive]


def _force_roll(game, value):
    """Make the game's RNG return `value` from random()."""
    return patch.object(game.context.get_rng().__class__, 'random', return_value=value)


def test_wanderer_spawns_when_roll_succeeds(game):
    before = len(_monsters(game))
    with _force_roll(game, 0.0):
        game.turn_processor._maybe_spawn_wanderer()
    assert len(_monsters(game)) == before + 1


def test_no_spawn_when_roll_fails(game):
    before = len(_monsters(game))
    with _force_roll(game, 0.99):
        game.turn_processor._maybe_spawn_wanderer()
    assert len(_monsters(game)) == before


def test_wanderer_spawns_far_from_player(game):
    player = game.state.player
    initial = {m.entity_id for m in _monsters(game)}
    with _force_roll(game, 0.0):
        game.turn_processor._maybe_spawn_wanderer()
    spawned = [m for m in _monsters(game) if m.entity_id not in initial]
    assert len(spawned) == 1
    m = spawned[0]
    assert abs(m.x - player.x) + abs(m.y - player.y) >= 8


def test_wanderer_never_shares_a_tile(game):
    for _ in range(20):
        with _force_roll(game, 0.0):
            game.turn_processor._maybe_spawn_wanderer()
    tiles = [(e.x, e.y) for e in game.state.entities.values() if e.x is not None]
    assert len(tiles) == len(set(tiles))


def test_monster_cap_per_floor(game):
    cap = game.config.get_ongoing_spawn_config()['max_monsters_per_floor']
    for _ in range(cap + 10):
        with _force_roll(game, 0.0):
            game.turn_processor._maybe_spawn_wanderer()
    assert len(_monsters(game)) == cap


def test_disabled_config_spawns_nothing(game):
    before = len(_monsters(game))
    with patch.object(type(game.config), 'get_ongoing_spawn_config',
                      return_value={'enabled': False}), _force_roll(game, 0.0):
        game.turn_processor._maybe_spawn_wanderer()
    assert len(_monsters(game)) == before


def test_difficulty_follows_floor_and_level(game):
    seen = []
    real = game.spawner.config.get_monster_spawn_weights
    with patch.object(type(game.spawner.config), 'get_monster_spawn_weights',
                      side_effect=lambda t: seen.append(t) or real(t)):
        game.state.current_floor = 7
        game.state.player.set_stat('level', 5)
        with _force_roll(game, 0.0):
            game.turn_processor._maybe_spawn_wanderer()
    assert seen == [6]  # (7 + 5) // 2


def test_dead_player_blocks_spawns(game):
    game.state.player.is_alive = False
    before = len(_monsters(game))
    with _force_roll(game, 0.0):
        game.turn_processor._maybe_spawn_wanderer()
    assert len(_monsters(game)) == before
