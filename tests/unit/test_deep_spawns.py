"""Every monster spawns somewhere, and the final boss appears once on its floor (VB-69/VB-75)."""
import dataclasses

import pytest

from core.config.config_loader import ConfigLoader
from core.entity_loader import EntityLoader
from core.exceptions import ContentValidationError
from core.game import Game
from core.spawning import EntitySpawner

pytestmark = pytest.mark.unit


def weight_bands():
    return ConfigLoader.get_config().monster_spawns['spawn_weights']


def test_every_defined_monster_spawns_somewhere():
    in_bands = {m for band in weight_bands().values() for m, w in band.items() if isinstance(w, int)}
    bosses = set(ConfigLoader.get_config().get_boss_floors().values())
    assert set(EntityLoader().get_monster_ids()) == in_bands | bosses


def test_boss_is_never_a_weighted_spawn():
    """Monster dens and wanderers draw from the weights; a boss must not be in them."""
    in_bands = {m for band in weight_bands().values() for m in band}
    assert not set(ConfigLoader.get_config().get_boss_floors().values()) & in_bands


def test_final_boss_guards_the_floor_before_victory():
    config = ConfigLoader.get_config()
    victory = config.game_constants['progression']['victory_floor']
    assert config.get_boss_for_floor(victory - 1) == 'ancient_horror'


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=7)
    return g


def test_boss_floor_gets_exactly_one_boss(game):
    spawned = game.spawner.spawn_monsters_for_floor(99, game.state.dungeon_map)
    assert [m.content_id for m in spawned].count('ancient_horror') == 1
    # the boss takes the first position: a crowded map drops a normal monster, never the boss
    assert spawned[0].content_id == 'ancient_horror'
    assert len(spawned) <= game.spawner.config.get_monster_count_for_floor(99) + 1


def test_other_floors_get_no_boss(game):
    spawned = game.spawner.spawn_monsters_for_floor(98, game.state.dungeon_map)
    assert 'ancient_horror' not in [m.content_id for m in spawned]


@pytest.mark.parametrize('bosses', [{99: 'no_such_monster'}, {'ninety-nine': 'ancient_horror'}, {0: 'ancient_horror'}])
def test_bad_boss_floors_fail_at_load(bosses):
    config = ConfigLoader.get_config()
    spawns = {**config.monster_spawns, 'boss_floors': bosses}
    with pytest.raises(ContentValidationError):
        bad = dataclasses.replace(config, monster_spawns=spawns)   # floor keys checked here
        EntitySpawner(bad, EntityLoader())                         # monster ids checked here
