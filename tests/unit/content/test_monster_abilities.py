"""Active monster abilities (VB-64): built and disabled in monsters.yaml until enabled.

Each test enables one ability on its own monster (as a monsters.yaml edit would)
and checks it does what its description says.
"""

import copy

import pytest

from core.base.entity import EntityType
from core.extensions import abilities
from tests.unit.systems.test_ai_perception import PX, PY, add, ai, arena, tick

pytestmark = pytest.mark.unit

ACTIVE = ["fire_bolt", "death_bolt", "aerial_dive", "dive_bomb", "hellfire", "reality_warp",
          "bat_swarm", "summon_undead", "summon_horrors"]


@pytest.fixture
def game():
    g = arena()
    g.state.player.max_hp = g.state.player.hp = 500  # survive the big numbers
    return g


@pytest.fixture
def enable(game):
    saved = {}

    def _enable(monster_id, name):
        saved.setdefault(monster_id, copy.deepcopy(game.entity_loader.monsters[monster_id]))
        game.entity_loader.monsters[monster_id]['abilities'][name]['enabled'] = True

    yield _enable
    for monster_id, definition in saved.items():
        game.entity_loader.monsters[monster_id] = definition


def test_every_active_ability_is_registered_with_an_ai_hint():
    for name in ACTIVE:
        assert name in abilities, name
        assert abilities.get(name).should_use is not None, name


@pytest.mark.parametrize("monster_id, name, dist", [
    ("imp", "fire_bolt", 4),
    ("lich", "death_bolt", 5),
    ("wyvern", "aerial_dive", 1),
    ("phoenix", "dive_bomb", 1),
])
def test_direct_damage_abilities_hit_for_their_listed_damage(game, enable, monster_id, name, dist):
    enable(monster_id, name)
    p = game.state.player
    mon = add(game, dist, monster_id=monster_id, aggro_range=8, flee_threshold=0, move_speed=1.0)
    damage = game.entity_loader.monsters[monster_id]['abilities'][name]['damage']
    tick(game)
    assert p.max_hp - p.hp == damage
    assert any(name.replace('_', ' ') in m for m in game.state.messages)
    assert name in mon.get_stat('cooldowns')


def test_a_strike_needs_adjacency(game, enable):
    enable("wyvern", "aerial_dive")
    p = game.state.player
    mon = add(game, 3, monster_id="wyvern")
    assert ai(game).abilities_for(mon)
    tick(game)
    assert not any("aerial dive" in m for m in game.state.messages)


@pytest.mark.parametrize("monster_id, name", [("demon", "hellfire"), ("ancient_horror", "reality_warp")])
def test_blasts_hit_every_hostile_in_the_radius(game, enable, monster_id, name):
    from core.entities import Player
    enable(monster_id, name)
    p = game.state.player
    ally = Player(name="Ally", x=PX, y=PY + 1, hp=500, max_hp=500, attack=3, defense=1)
    far = Player(name="Far", x=PX, y=PY - 8, hp=500, max_hp=500, attack=3, defense=1)
    for e in (ally, far):
        game.context.add_entity(e)
    add(game, 4, monster_id=monster_id, flee_threshold=0, move_speed=1.0)
    damage = game.entity_loader.monsters[monster_id]['abilities'][name]['damage']
    tick(game)
    assert p.max_hp - p.hp == damage
    assert ally.max_hp - ally.hp == damage
    assert far.hp == far.max_hp


@pytest.mark.parametrize("monster_id, name", [
    ("vampire", "bat_swarm"), ("lich", "summon_undead"), ("ancient_horror", "summon_horrors"),
])
def test_summon_abilities_call_their_listed_minions(game, enable, monster_id, name):
    enable(monster_id, name)
    cfg = game.entity_loader.monsters[monster_id]['abilities'][name]
    mon = add(game, 5, monster_id=monster_id, flee_threshold=0, move_speed=1.0)
    for other in ai(game).abilities_for(mon):
        if other != name:  # only the ability under test
            pytest.fail(f"unexpected ability {other}")
    tick(game)
    minions = [game.context.get_entity(i) for i in mon.get_stat('minion_ids', [])]
    assert len(minions) == cfg['count']
    assert {m.content_id for m in minions} <= set(cfg['minion_types'])


def test_shipped_monsters_still_have_no_abilities(game):
    for monster_id in game.entity_loader.monsters:
        mon = game.entity_loader.create_monster(monster_id, 1, 1)
        assert ai(game).abilities_for(mon) == {}, monster_id
