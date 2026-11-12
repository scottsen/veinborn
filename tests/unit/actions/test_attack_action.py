"""
Unit tests for AttackAction.

Tests the combat action implementation, focusing on:
- Basic attack validation and execution
- Bug fix: Items cannot be attacked (loot, ore, etc.)
- Combat calculations and damage
- Death handling and loot drops
"""
import pytest
from core.actions.attack_action import AttackAction
from core.entities import Monster, OreVein, EntityType
from core.base.entity import Entity


# ============================================================================
# Bug Fix Tests - Items Cannot Be Attacked
# ============================================================================

pytestmark = pytest.mark.unit

@pytest.mark.unit
def test_cannot_attack_item_loot(game_context):
    """Bug #1: Cannot attack items (loot drops like bread, gold)."""
    # Create a loot item (bread dropped by monster)
    loot_item = Entity(
        entity_type=EntityType.ITEM,
        name="Loaf of Bread",
        x=11,
        y=10,  # Adjacent to player at (10, 10)
        hp=1,
        max_hp=1,
        attack=0,
        defense=0,
    )
    game_context.add_entity(loot_item)

    player = game_context.get_player()
    action = AttackAction(
        actor_id=player.entity_id,
        target_id=loot_item.entity_id
    )

    # Attack should fail validation
    is_valid = action.validate(game_context)
    assert not is_valid, "Should not be able to attack item entities"


@pytest.mark.unit
def test_cannot_attack_ore_vein(game_context, copper_ore):
    """Bug #1: Cannot attack ore veins (they are items)."""
    # Place ore vein adjacent to player
    player = game_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y
    game_context.add_entity(copper_ore)

    action = AttackAction(
        actor_id=player.entity_id,
        target_id=copper_ore.entity_id
    )

    # Attack should fail validation
    is_valid = action.validate(game_context)
    assert not is_valid, "Should not be able to attack ore veins"


@pytest.mark.unit
def test_can_attack_monster(game_context, weak_goblin):
    """Verify monsters can still be attacked normally."""
    game_context.add_entity(weak_goblin)

    player = game_context.get_player()
    action = AttackAction(
        actor_id=player.entity_id,
        target_id=weak_goblin.entity_id
    )

    # Attack should succeed validation
    is_valid = action.validate(game_context)
    assert is_valid, "Should be able to attack monsters"


@pytest.mark.unit
def test_attack_execution_on_monster(game_context, weak_goblin, sure_hit):
    """Test that attack execution works correctly on valid targets."""
    game_context.add_entity(weak_goblin)

    player = game_context.get_player()
    initial_hp = weak_goblin.hp

    action = AttackAction(
        actor_id=player.entity_id,
        target_id=weak_goblin.entity_id
    )

    outcome = action.execute(game_context)

    # Attack should succeed
    assert outcome.success
    assert outcome.took_turn
    assert len(outcome.messages) > 0

    # Goblin should take damage
    assert weak_goblin.hp < initial_hp


# ============================================================================
# Basic Combat Tests
# ============================================================================

@pytest.mark.unit
def test_attack_validation_requires_adjacency(game_context, weak_goblin):
    """Attack validation fails if target is not adjacent."""
    # Place goblin far from player
    weak_goblin.x = 20
    weak_goblin.y = 20
    game_context.add_entity(weak_goblin)

    player = game_context.get_player()
    action = AttackAction(
        actor_id=player.entity_id,
        target_id=weak_goblin.entity_id
    )

    is_valid = action.validate(game_context)
    assert not is_valid, "Attack should fail when target not adjacent"


@pytest.mark.unit
def test_attack_deals_damage_to_living_target(game_context, weak_goblin, sure_hit):
    """Attack successfully damages living targets."""

    game_context.add_entity(weak_goblin)

    player = game_context.get_player()
    initial_hp = weak_goblin.hp

    action = AttackAction(
        actor_id=player.entity_id,
        target_id=weak_goblin.entity_id
    )

    is_valid = action.validate(game_context)
    assert is_valid, "Attack should succeed on living monsters"

    outcome = action.execute(game_context)
    assert weak_goblin.hp < initial_hp, "Target should take damage"


def test_configured_damage_formula_is_evaluated_not_the_fallback(
        game_context, weak_goblin, monkeypatch, caplog, sure_hit):
    """VB-37: max/min were passed as names, so every attack fell back silently."""
    from core.config.config_loader import ConfigLoader

    game_context.add_entity(weak_goblin)
    player = game_context.get_player()
    weak_goblin.hp = weak_goblin.max_hp = 500
    weak_goblin.defense = 0
    monkeypatch.setattr(ConfigLoader.get_config(), 'get_damage_formula',
                        lambda: "attacker_attack * 2 - defender_defense")

    with caplog.at_level("ERROR"):
        AttackAction(actor_id=player.entity_id, target_id=weak_goblin.entity_id).execute(game_context)

    assert "Formula evaluation failed" not in caplog.text
    assert weak_goblin.max_hp - weak_goblin.hp == player.get_total_attack() * 2


def test_default_damage_formula_uses_max_without_error(game_context, weak_goblin, caplog, sure_hit):
    game_context.add_entity(weak_goblin)
    player = game_context.get_player()
    weak_goblin.hp = weak_goblin.max_hp = 500
    weak_goblin.defense = 10_000  # would go negative without max(1, ...)

    with caplog.at_level("ERROR"):
        AttackAction(actor_id=player.entity_id, target_id=weak_goblin.entity_id).execute(game_context)

    assert "Formula evaluation failed" not in caplog.text
    assert weak_goblin.hp == 499


# ============================================================================
# Combat dice: to-hit roll and damage roll (formulas.yaml combat)
# ============================================================================

class _FixedRolls:
    """Stand-in RNG: randint returns queued values in order."""

    def __init__(self, *rolls):
        self.rolls = list(rolls)

    def randint(self, a, b):
        value = self.rolls.pop(0)
        assert a <= value <= b, f"queued roll {value} outside [{a}, {b}]"
        return value


def _swing(game_context, weak_goblin, monkeypatch, *rolls):
    game_context.add_entity(weak_goblin)
    player = game_context.get_player()
    monkeypatch.setattr(game_context, 'get_rng', lambda: _FixedRolls(*rolls))
    return AttackAction(actor_id=player.entity_id, target_id=weak_goblin.entity_id).execute(game_context)


@pytest.mark.unit
def test_natural_one_always_misses(game_context, weak_goblin, monkeypatch):
    """A miss takes the turn, deals no damage, and says so."""
    weak_goblin.defense = -100  # the formula alone would always hit
    start_hp = weak_goblin.hp

    outcome = _swing(game_context, weak_goblin, monkeypatch, 1)

    assert outcome.success and outcome.took_turn
    assert weak_goblin.hp == start_hp
    assert any("misses" in m for m in outcome.messages)
    assert outcome.events[0]['data']['hit'] is False
    assert outcome.events[0]['data']['damage'] == 0


@pytest.mark.unit
def test_natural_twenty_always_hits(game_context, weak_goblin, monkeypatch):
    weak_goblin.hp = weak_goblin.max_hp = 500
    weak_goblin.defense = 10_000  # the formula alone would never hit

    _swing(game_context, weak_goblin, monkeypatch, 20, 5)

    assert weak_goblin.hp == 499  # min damage 1


@pytest.mark.unit
def test_to_hit_formula_uses_attack_and_defense(game_context, weak_goblin, monkeypatch):
    """Attack 5 vs defense 1 needs roll + 5 >= 11: a 5 misses, a 6 hits."""
    weak_goblin.hp = weak_goblin.max_hp = 500
    weak_goblin.defense = 1
    assert game_context.get_player().get_total_attack() == 5

    _swing(game_context, weak_goblin, monkeypatch, 5)
    assert weak_goblin.hp == 500

    _swing(game_context, weak_goblin, monkeypatch, 6, 5)
    assert weak_goblin.hp == 500 - (5 - 1)


@pytest.mark.unit
def test_damage_roll_range_and_no_spread():
    """Spread 0.5 on attack 4 rolls 2..6; spread 0 is the flat attack."""
    from core.rng import GameRNG
    rng = GameRNG(seed=7)
    rolls = {AttackAction._roll_damage(4, 0.5, rng) for _ in range(500)}
    assert rolls == {2, 3, 4, 5, 6}
    assert AttackAction._roll_damage(4, 0.0, rng) == 4
    assert {AttackAction._roll_damage(3, 0.5, rng) for _ in range(300)} == {2, 3, 4}


@pytest.mark.unit
def test_hit_rate_matches_the_formula_over_many_swings(game_context, weak_goblin):
    """Player attack 5 vs goblin defense 1 hits on 6+ of a d20: 75%."""
    from core.rng import GameRNG
    GameRNG.initialize(12345)
    game_context.add_entity(weak_goblin)
    player = game_context.get_player()
    hits = 0
    swings = 2000
    for _ in range(swings):
        weak_goblin.hp = weak_goblin.max_hp = 10_000
        outcome = AttackAction(actor_id=player.entity_id, target_id=weak_goblin.entity_id).execute(game_context)
        hits += outcome.events[0]['data']['hit']
    assert 0.71 <= hits / swings <= 0.79
