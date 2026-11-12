"""ActionPlanner uses class abilities: bolt a monster in sight, heal when hurt."""

import pytest

from core.base.entity import EntityType
from core.character_class import CharacterClass
from core.game import Game
from tests.fuzz.services.action_planner import ActionPlanner
from tests.fuzz.services.perception_service import PerceptionService
from tests.fuzz.services.tactical_decision_service import TacticalDecisionService

pytestmark = pytest.mark.unit


def make(player_class):
    g = Game()
    g.start_new_game(seed=42, character_class=CharacterClass(player_class))
    for e in list(g.state.entities.values()):
        if e.entity_type == EntityType.MONSTER:
            g.context.remove_entity(e.entity_id)
    perception = PerceptionService()
    planner = ActionPlanner(perception, TacticalDecisionService(perception))
    return g, planner


def add_monster_in_sight(game, dist=3):
    p = game.state.player
    for dx in range(dist, 0, -1):
        for sx in (1, -1):
            x, y = p.x + sx * dx, p.y
            if game.state.dungeon_map.is_walkable(x, y):
                mon = game.entity_loader.create_monster("goblin", x, y)
                game.context.add_entity(mon)
                return mon
    pytest.skip("no open tile beside the player")


def test_mage_bolts_a_monster_in_sight():
    game, planner = make("mage")
    add_monster_in_sight(game)
    assert planner.get_smart_action(game) == ('ability', {'ability': 'force_bolt'})


def test_mage_does_not_bolt_with_nothing_in_sight():
    game, planner = make("mage")
    assert planner.ability_action(game) is None


def test_mage_does_not_bolt_on_cooldown():
    game, planner = make("mage")
    add_monster_in_sight(game)
    game.state.player.set_stat('cooldowns', {'force_bolt': game.state.turn_count + 2})
    assert planner.ability_action(game) is None


def test_mage_does_not_bolt_out_of_range():
    game, planner = make("mage")
    mon = add_monster_in_sight(game)
    mon.x += 50  # far outside range 6, line of sight irrelevant
    assert planner.ability_action(game) is None


def test_healer_heals_when_hurt():
    game, planner = make("healer")
    p = game.state.player
    p.hp = int(p.max_hp * 0.5)
    assert planner.ability_action(game) == ('ability', {'ability': 'heal'})


def test_healer_does_not_heal_when_healthy_or_on_cooldown():
    game, planner = make("healer")
    p = game.state.player
    assert planner.ability_action(game) is None
    p.hp = int(p.max_hp * 0.5)
    p.set_stat('cooldowns', {'heal': game.state.turn_count + 5})
    assert planner.ability_action(game) is None


def test_classes_without_active_abilities_never_use_one():
    for cls in ("warrior", "rogue"):
        game, planner = make(cls)
        add_monster_in_sight(game)
        game.state.player.hp = 1
        assert planner.ability_action(game) is None


def test_ability_actions_pass_through_the_game():
    game, planner = make("mage")
    mon = add_monster_in_sight(game)
    hp = mon.hp
    action_type, kwargs = planner.get_smart_action(game)
    assert planner.validate_action(game, action_type, kwargs)
    assert game.handle_player_action(action_type, **kwargs)
    assert mon.hp < hp or not mon.is_alive
