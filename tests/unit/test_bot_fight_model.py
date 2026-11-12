"""TacticalDecisionService.can_win_fight uses the game's dice and monster speed (VB-68)."""
import pytest

from core.game import Game
from tests.fuzz.services.perception_service import PerceptionService
from tests.fuzz.services.tactical_decision_service import CombatConfig, TacticalDecisionService

pytestmark = pytest.mark.unit


@pytest.fixture
def setup():
    game = Game()
    game.start_new_game(seed=8)
    perception = PerceptionService()
    return game, TacticalDecisionService(perception, combat_config=CombatConfig(safety_margin=1.0))


def monster(game, monster_id, **stats):
    m = game.entity_loader.create_monster(monster_id, 1, 1)
    for k, v in stats.items():
        setattr(m, k, v)
    game.context.add_entity(m)
    return m


def test_a_faster_monster_is_judged_more_dangerous(setup):
    game, decisions = setup
    player = game.state.player
    slow = monster(game, "orc")
    fast = monster(game, "orc")
    fast.set_stat('ai_params', {'move_speed': 3.0})
    player.hp = player.max_hp
    # Find a monster HP where the slow one is beatable and the fast one is not
    for hp in range(1, 200):
        slow.hp = fast.hp = hp
        if decisions.can_win_fight(game, slow) and not decisions.can_win_fight(game, fast):
            return
    pytest.fail("speed never changed the verdict")


def test_an_unhittable_monster_is_not_a_winnable_fight(setup):
    game, decisions = setup
    tank = monster(game, "troll", defense=60, attack=12, hp=40)
    assert not decisions.can_win_fight(game, tank)


def test_a_harmless_monster_is_winnable(setup):
    game, decisions = setup
    weak = monster(game, "goblin", attack=0, hp=3)
    assert decisions.can_win_fight(game, weak)
