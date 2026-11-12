"""Engine morale step (VB-61, ADR-019): flee_threshold applies before every behaviour."""

import pytest

from core.extensions import ai_behavior, ai_behaviors
from core.systems.ai_system import AISystem
from tests.unit.systems.test_ai_perception import PX, PY, add, ai, arena, tick

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    return arena()


def hurt(mon, fraction):
    mon.hp = max(1, int(mon.max_hp * fraction))


def test_hurt_defensive_monster_flees_a_perceived_player(game):
    p = game.state.player
    mon = add(game, 3, ai_type='defensive', aggro_range=8)  # defensive flee_threshold 0.3
    hurt(mon, 0.2)
    start = ai(game).distance(mon, p)
    tick(game, 3)
    assert ai(game).distance(mon, p) > start
    assert p.hp == p.max_hp


def test_aggressive_never_breaks(game):
    p = game.state.player
    mon = add(game, 1, ai_type='aggressive')
    hurt(mon, 0.05)
    tick(game, 4)
    assert mon.is_adjacent(p)


def test_guards_hold_their_post_when_hurt(game):
    mon = add(game, 1, monster_id='golem')  # guard
    hurt(mon, 0.1)
    tick(game, 4)
    assert mon.is_adjacent(game.state.player)


def test_a_monster_override_gives_any_behaviour_morale(game):
    p = game.state.player
    mon = add(game, 2, ai_type='aggressive', flee_threshold=0.5)
    hurt(mon, 0.3)
    start = ai(game).distance(mon, p)
    tick(game, 3)
    assert ai(game).distance(mon, p) > start


def test_no_perceived_target_means_no_flight_and_the_behaviour_runs(game):
    seen = []

    @ai_behavior("_test_morale", replace=True)
    def capture(ai_, monster, config):
        seen.append(monster.entity_id)

    try:
        mon = add(game, 30, ai_type='_test_morale', aggro_range=3, flee_threshold=0.9)
        hurt(mon, 0.1)
        game.context.register_system('ai', AISystem(game.context, game.entity_loader))
        tick(game)
        assert seen == [mon.entity_id]
    finally:
        ai_behaviors.unregister("_test_morale")


def test_a_new_behaviour_gets_morale_without_writing_it(game):
    """The point of an engine step: content cannot forget to flee."""
    seen = []

    @ai_behavior("_test_brave", replace=True)
    def brave(ai_, monster, config):
        seen.append(monster.entity_id)  # never flees on its own

    try:
        mon = add(game, 2, ai_type='_test_brave', flee_threshold=0.5)
        hurt(mon, 0.2)
        game.context.register_system('ai', AISystem(game.context, game.entity_loader))
        start = ai(game).distance(mon, game.state.player)
        tick(game)
        assert seen == []  # behaviour skipped: the monster fled instead
        assert ai(game).distance(mon, game.state.player) > start
    finally:
        ai_behaviors.unregister("_test_brave")
