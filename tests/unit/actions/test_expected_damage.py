"""AttackAction.hit_chance / expected_damage agree with the real dice."""
import pytest

from core.actions.attack_action import AttackAction
from core.base.game_context import GameContext
from core.character_class import CharacterClass, create_player_from_class
from core.entity_loader import EntityLoader
from core.game_state import GameState
from core.rng import GameRNG

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("attack,defense,chance", [(5, 1, 0.75), (3, 3, 0.55), (0, 40, 0.05), (40, 0, 0.95)])
def test_hit_chance_matches_the_formula_examples(attack, defense, chance):
    assert AttackAction.hit_chance(attack, defense) == pytest.approx(chance)


@pytest.mark.parametrize("monster_id", ["goblin", "orc", "troll"])
def test_expected_damage_matches_many_real_swings(monster_id):
    GameRNG.initialize(3)
    loader = EntityLoader()
    swings = 8000
    total = 0
    expected = None
    for _ in range(swings // 500):
        player = create_player_from_class(CharacterClass.WARRIOR, 0, 0, name="w")  # no damage modifiers
        player.max_hp = player.hp = 10 ** 9
        monster = loader.create_monster(monster_id, 1, 0)
        state = GameState(player=player)
        state.entities[player.entity_id] = player
        state.entities[monster.entity_id] = monster
        ctx = GameContext(state)
        expected = AttackAction.expected_damage(monster, player)
        for _ in range(500):
            before = player.hp
            AttackAction(monster.entity_id, player.entity_id).execute(ctx)
            total += before - player.hp
    assert total / swings == pytest.approx(expected, rel=0.08)
