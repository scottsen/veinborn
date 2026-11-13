"""Monster stats scale with floor (VB-75): monster_spawns.yaml floor_scaling."""
import dataclasses

import pytest

from core.config.config_loader import ConfigLoader
from core.entity_loader import EntityLoader
from core.exceptions import ContentValidationError
from core.game import Game

pytestmark = pytest.mark.unit


@pytest.fixture
def scaling(monkeypatch):
    """Set floor_scaling on the shared game config for one test."""
    config = ConfigLoader.get_config()

    def set_scaling(per_floor, stats=('hp', 'attack', 'defense')):
        monkeypatch.setitem(config.monster_spawns, 'floor_scaling',
                            {'per_floor': per_floor, 'stats': list(stats)})
        return config
    return set_scaling


def base_stats(monster_id):
    s = EntityLoader().monsters[monster_id]['stats']
    return s['hp'], s['attack'], s['defense']


def stats(monster):
    return monster.max_hp, monster.attack, monster.defense


def test_multiplier_is_one_on_floor_one_and_linear_after(scaling):
    config = scaling(0.05)
    assert config.monster_floor_multiplier(1) == 1.0
    assert config.monster_floor_multiplier(21) == pytest.approx(2.0)


def test_floor_one_and_zero_rate_leave_stats_alone(scaling):
    scaling(0.05)
    assert stats(EntityLoader().create_monster('troll', 0, 0, floor=1)) == base_stats('troll')
    scaling(0.0)
    assert stats(EntityLoader().create_monster('troll', 0, 0, floor=50)) == base_stats('troll')


def test_stats_scale_and_round(scaling):
    scaling(0.05)                                   # floor 21 -> x2.0, floor 4 -> x1.15
    hp, atk, dfn = base_stats('troll')
    troll = EntityLoader().create_monster('troll', 0, 0, floor=21)
    assert stats(troll) == (hp * 2, atk * 2, dfn * 2)
    assert troll.hp == troll.max_hp
    orc_hp, orc_atk, orc_def = base_stats('orc')
    orc = EntityLoader().create_monster('orc', 0, 0, floor=4)
    assert stats(orc) == (round(orc_hp * 1.15), round(orc_atk * 1.15), round(orc_def * 1.15))


def test_only_listed_stats_scale(scaling):
    scaling(0.05, stats=['hp'])
    hp, atk, dfn = base_stats('troll')
    assert stats(EntityLoader().create_monster('troll', 0, 0, floor=21)) == (hp * 2, atk, dfn)


def test_boss_with_floor_scaling_false_keeps_its_stats(scaling):
    scaling(0.05)
    assert EntityLoader().monsters['ancient_horror'].get('floor_scaling') is False
    boss = EntityLoader().create_monster('ancient_horror', 0, 0, floor=99)
    assert stats(boss) == base_stats('ancient_horror')


@pytest.mark.parametrize('section', [
    {'per_floor': -0.1},
    {'per_floor': 'lots'},
    {'per_floor': 0.02, 'stats': ['hp', 'speed']},
])
def test_bad_config_fails_at_load(section):
    config = ConfigLoader.get_config()
    spawns = {**config.monster_spawns, 'floor_scaling': section}
    with pytest.raises(ContentValidationError):
        dataclasses.replace(config, monster_spawns=spawns)


def test_shipped_config_loads():
    scaling_cfg = ConfigLoader.get_config().get_monster_floor_scaling()
    assert scaling_cfg['per_floor'] >= 0


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=5)
    return g


def test_floor_spawns_use_the_floor(scaling, game):
    scaling(0.05)
    monsters = game.spawner.spawn_monsters_for_floor(21, game.state.dungeon_map)
    assert monsters
    for m in monsters:
        hp, _, _ = base_stats(m.content_id)
        assert m.max_hp == hp * 2, m.content_id


def test_summons_use_the_current_floor(scaling, game):
    scaling(0.05)
    game.state.current_floor = 21
    caller = game.spawner.spawn_monsters_for_floor(21, game.state.dungeon_map)[0]
    game.context.add_entity(caller)
    minion = game.ai_system.summon(caller, 'skeleton')
    if minion is None:
        pytest.skip("no free tile beside the summoner")
    hp, _, _ = base_stats('skeleton')
    assert minion.max_hp == hp * 2
