"""Deep-start scenarios (tests/fuzz/scenario.py): a bot game can begin on floor N at level L.

Bots reach about floor 10 in 3000 turns, so monsters placed deeper (VB-69) need this
to be measured at all. It must go through the real paths and stay seed-reproducible.
"""
import sys
from pathlib import Path

import pytest

from core.base.entity import EntityType
from core.config import ConfigLoader
from core.game import Game

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fuzz"))
from fuzz.scenario import advance_to  # noqa: E402
from warrior_bot import WarriorBot  # noqa: E402

pytestmark = pytest.mark.unit


def started(seed=7):
    game = Game()
    game.start_new_game(seed=seed)
    return game


def test_advance_to_floor_and_level_through_real_paths():
    game = started()
    hp_at_1 = game.state.player.max_hp
    advance_to(game, floor=12, level=8)
    player = game.state.player
    assert game.state.current_floor == 12
    assert player.get_stat('level') == 8
    assert player.get_stat('xp') == ConfigLoader.get_config().get_xp_for_level(8)
    assert player.max_hp > hp_at_1 and player.hp == player.max_hp
    # the floor is populated from floor 12's spawn band, not floor 1's
    monsters = {m.content_id for m in game.context.get_entities_by_type(EntityType.MONSTER)}
    assert monsters and monsters <= set(ConfigLoader.get_config().get_monster_spawn_weights(12))


def test_advance_to_is_seed_reproducible():
    def snapshot():
        game = started(seed=3)
        advance_to(game, floor=6, level=5)
        p = game.state.player
        world = sorted((e.name, e.x, e.y, e.hp) for e in game.state.entities.values() if e.x is not None)
        return p.max_hp, p.get_stat('attack'), world
    assert snapshot() == snapshot()


@pytest.mark.parametrize('floor, level', [(0, 1), (100, 1), (5, 0)])
def test_advance_to_rejects_out_of_range(floor, level):
    with pytest.raises(ValueError):
        advance_to(started(), floor=floor, level=level)


def test_bot_game_starts_deep_and_records_it():
    bot = WarriorBot()
    bot.start_floor, bot.start_level = 11, 7
    stats = bot.play_one_game(max_turns=30, seed=1000)
    assert stats['floor'] >= 11 and stats['level'] >= 7
    assert stats['death_reason'] != 'crash'
