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
def test_attack_execution_on_monster(game_context, weak_goblin):
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
def test_attack_deals_damage_to_living_target(game_context, weak_goblin):
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
