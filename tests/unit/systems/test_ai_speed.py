"""Monster speed via an energy counter (VB-62, ADR-019)."""

import pytest

from core.extensions import ai_behavior, ai_behaviors
from core.systems.ai_system import AISystem
from tests.unit.systems.test_ai_perception import add, arena, tick

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    return arena()


@pytest.fixture
def counting(game):
    """A behaviour that only counts its turns; returns the per-monster count dict."""
    counts = {}

    @ai_behavior("_test_count", replace=True)
    def count(ai, monster, config):
        counts[monster.entity_id] = counts.get(monster.entity_id, 0) + 1

    game.context.register_system('ai', AISystem(game.context, game.entity_loader))
    yield counts
    ai_behaviors.unregister("_test_count")


@pytest.mark.parametrize("speed, rounds, actions", [
    (1.0, 10, 10),
    (1.5, 10, 15),
    (0.6, 10, 6),
    (2.0, 3, 6),
    (0.5, 4, 2),
    (0.0, 5, 0),
])
def test_actions_per_round_follow_move_speed(game, counting, speed, rounds, actions):
    mon = add(game, 30, ai_type='_test_count', move_speed=speed)
    tick(game, rounds)
    assert counting.get(mon.entity_id, 0) == actions


def test_yaml_speeds_are_used(game, counting):
    bat = add(game, 30, monster_id='bat', ai_type='_test_count')      # move_speed 1.5
    golem = add(game, -15, monster_id='golem', ai_type='_test_count')  # move_speed 0.6
    tick(game, 10)
    assert counting[bat.entity_id] == 15
    assert counting[golem.entity_id] == 6


def test_energy_carries_over_and_survives_a_save(game, counting):
    mon = add(game, 30, ai_type='_test_count', move_speed=0.5)
    tick(game)
    assert counting.get(mon.entity_id, 0) == 0
    assert mon.get_stat('energy') == 0.5  # an entity stat, so saves keep it
    tick(game)
    assert counting[mon.entity_id] == 1


def test_a_monster_killed_mid_round_stops_acting(game):
    acted = []

    @ai_behavior("_test_suicide", replace=True)
    def suicide(ai, monster, config):
        acted.append(1)
        monster.take_damage(monster.hp)

    try:
        add(game, 30, ai_type='_test_suicide', move_speed=3.0)
        game.context.register_system('ai', AISystem(game.context, game.entity_loader))
        tick(game)
        assert acted == [1]
    finally:
        ai_behaviors.unregister("_test_suicide")
