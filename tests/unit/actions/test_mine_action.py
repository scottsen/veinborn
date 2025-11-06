"""
Unit tests for MineAction.

Tests the multi-turn mining action, focusing on:
- Mining workflow from start to completion
- Multi-turn progression and state tracking
- Inventory management (adding ore, handling full inventory)
- Validation (adjacency, entity type, ore vein existence)
- Serialization (to_dict/from_dict)
- Edge cases (interruptions, non-player actors)
"""
import pytest
from core.actions.mine_action import MineAction
from core.entities import OreVein, Monster, Player, EntityType
from core.base.entity import Entity


# ============================================================================
# Validation Tests
# ============================================================================

pytestmark = pytest.mark.unit

@pytest.mark.unit
def test_validate_requires_ore_vein_exists(mining_context):
    """Mining fails if ore vein doesn't exist."""
    player = mining_context.get_player()

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id="nonexistent_ore"
    )

    assert not action.validate(mining_context)


@pytest.mark.unit
def test_validate_requires_ore_vein_type(mining_context):
    """Mining fails if target is not an ore vein."""
    player = mining_context.get_player()

    # Create a non-ore entity
    monster = Monster(
        name="Goblin",
        x=player.x + 1,
        y=player.y,
        hp=10,
        max_hp=10,
        attack=5,
        defense=2
    )
    mining_context.add_entity(monster)

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=monster.entity_id
    )

    assert not action.validate(mining_context)


@pytest.mark.unit
def test_validate_requires_adjacency(mining_context, copper_ore):
    """Mining fails if player is not adjacent to ore vein."""
    player = mining_context.get_player()

    # Move ore vein far away
    copper_ore.x = player.x + 5
    copper_ore.y = player.y + 5

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id
    )

    assert not action.validate(mining_context)


@pytest.mark.unit
def test_validate_succeeds_when_adjacent(mining_context, copper_ore):
    """Mining validates successfully when all conditions met."""
    player = mining_context.get_player()

    # Ensure ore is adjacent
    copper_ore.x = player.x + 1
    copper_ore.y = player.y

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id
    )

    assert action.validate(mining_context)


# ============================================================================
# Mining Workflow Tests
# ============================================================================

@pytest.mark.unit
def test_mining_initialization_sets_turns(mining_context, copper_ore):
    """First mining turn initializes turns_remaining from ore hardness."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y
    copper_ore.set_stat('mining_turns', 5)

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=0  # First turn
    )

    outcome = action.execute(mining_context)

    # After initialization and first turn, should be 4 remaining
    assert action.turns_remaining == 4
    assert outcome.is_success
    assert outcome.took_turn


@pytest.mark.unit
def test_mining_progress_message(mining_context, copper_ore):
    """Mining in progress shows remaining turns message."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y
    copper_ore.set_stat('mining_turns', 3)

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=0
    )

    outcome = action.execute(mining_context)

    # Should show progress message
    assert any("Mining..." in msg for msg in outcome.messages)
    assert any("turn(s) remaining" in msg for msg in outcome.messages)


@pytest.mark.unit
def test_mining_progress_stores_state(mining_context, copper_ore):
    """Mining progress stores state on actor for interruption handling."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=2  # Mid-mining
    )

    outcome = action.execute(mining_context)

    # Mining state should be stored on player
    mining_state = player.get_stat('mining_action')
    assert mining_state is not None
    assert mining_state['ore_vein_id'] == copper_ore.entity_id
    assert mining_state['turns_remaining'] == 1


@pytest.mark.unit
def test_mining_progress_creates_event(mining_context, copper_ore):
    """Mining progress creates mining_progress event."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=2
    )

    outcome = action.execute(mining_context)

    # Check for mining_progress event
    progress_events = [e for e in outcome.events if e['type'] == 'mining_progress']
    assert len(progress_events) == 1
    assert progress_events[0]['data']['ore_vein_id'] == copper_ore.entity_id
    assert progress_events[0]['data']['turns_remaining'] == 1


@pytest.mark.unit
def test_mining_completion_adds_ore_to_inventory(mining_context, copper_ore):
    """Completed mining adds ore item to player inventory."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y

    initial_inventory_count = len(player.inventory)

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=1  # Will complete this turn
    )

    outcome = action.execute(mining_context)

    # Ore should be added to inventory
    assert len(player.inventory) == initial_inventory_count + 1
    assert any("Added" in msg and "inventory" in msg for msg in outcome.messages)


@pytest.mark.unit
def test_mining_completion_removes_ore_vein(mining_context, copper_ore):
    """Completed mining removes ore vein from world."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y
    ore_vein_id = copper_ore.entity_id

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=ore_vein_id,
        turns_remaining=1
    )

    outcome = action.execute(mining_context)

    # Ore vein should be removed
    assert mining_context.get_entity(ore_vein_id) is None


@pytest.mark.unit
def test_mining_completion_clears_state(mining_context, copper_ore):
    """Completed mining clears mining state from actor."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y

    # Set initial mining state
    player.set_stat('mining_action', {'test': 'data'})

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=1
    )

    action.execute(mining_context)

    # Mining state should be cleared
    assert player.get_stat('mining_action') is None


@pytest.mark.unit
def test_mining_completion_creates_ore_mined_event(mining_context, copper_ore):
    """Completed mining creates ore_mined event with properties."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=1
    )

    outcome = action.execute(mining_context)

    # Check for ore_mined event
    mined_events = [e for e in outcome.events if e['type'] == 'ore_mined']
    assert len(mined_events) == 1
    assert 'properties' in mined_events[0]['data']
    assert 'ore_id' in mined_events[0]['data']


# ============================================================================
# Full Mining Flow Tests
# ============================================================================

@pytest.mark.unit
def test_complete_mining_workflow(mining_context, copper_ore):
    """Test complete mining from start to finish."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y
    copper_ore.set_stat('mining_turns', 3)

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=0  # Start fresh
    )

    # Turn 1: Initialize
    outcome1 = action.execute(mining_context)
    assert outcome1.is_success
    assert action.turns_remaining == 2

    # Turn 2: Progress
    outcome2 = action.execute(mining_context)
    assert outcome2.is_success
    assert action.turns_remaining == 1

    # Turn 3: Complete
    outcome3 = action.execute(mining_context)
    assert outcome3.is_success
    assert action.turns_remaining == 0
    assert len(player.inventory) > 0
    assert mining_context.get_entity(copper_ore.entity_id) is None


# ============================================================================
# Inventory Full Tests
# ============================================================================

@pytest.mark.unit
def test_mining_completion_drops_ore_when_inventory_full(mining_context, copper_ore):
    """When inventory is full, ore is dropped on ground at player position."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y

    # Fill inventory to max capacity (20 items)
    from core.base.entity import Entity
    for i in range(20):
        dummy_ore = Entity(
            entity_type=EntityType.ITEM,
            name=f"Dummy Ore {i}",
        )
        player.add_to_inventory(dummy_ore)

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=1
    )

    outcome = action.execute(mining_context)

    # Inventory should still be full (20 items)
    assert len(player.inventory) == 20

    # Ore should be dropped on ground
    assert any("Inventory full" in msg for msg in outcome.messages)

    # Verify ore was dropped as an item entity in the world
    items_in_world = mining_context.get_entities_by_type(EntityType.ITEM)
    dropped_ores = [item for item in items_in_world if item.x == player.x and item.y == player.y]
    assert len(dropped_ores) == 1, "Should have exactly one dropped ore at player position"


# ============================================================================
# Serialization Tests
# ============================================================================

@pytest.mark.unit
def test_to_dict_serialization():
    """Test MineAction can serialize to dictionary."""
    action = MineAction(
        actor_id="player_123",
        ore_vein_id="ore_456",
        turns_remaining=3
    )

    data = action.to_dict()

    assert data['action_type'] == 'MineAction'
    assert data['actor_id'] == "player_123"
    assert data['ore_vein_id'] == "ore_456"
    assert data['turns_remaining'] == 3


@pytest.mark.unit
def test_from_dict_deserialization():
    """Test MineAction can deserialize from dictionary."""
    data = {
        'action_type': 'MineAction',
        'actor_id': 'player_123',
        'ore_vein_id': 'ore_456',
        'turns_remaining': 3
    }

    action = MineAction.from_dict(data)

    assert isinstance(action, MineAction)
    assert action.actor_id == "player_123"
    assert action.ore_vein_id == "ore_456"
    assert action.turns_remaining == 3


@pytest.mark.unit
def test_serialization_roundtrip():
    """Test serialize -> deserialize preserves action state."""
    original = MineAction(
        actor_id="player_999",
        ore_vein_id="ore_888",
        turns_remaining=5
    )

    data = original.to_dict()
    restored = MineAction.from_dict(data)

    assert restored.actor_id == original.actor_id
    assert restored.ore_vein_id == original.ore_vein_id
    assert restored.turns_remaining == original.turns_remaining


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.unit
def test_get_actor_fallback_to_player(mining_context, copper_ore):
    """If actor_id is invalid, _get_actor falls back to player."""
    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y

    # Use invalid actor_id - should fall back to player
    action = MineAction(
        actor_id="nonexistent_actor",
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=1
    )

    # This should still work by falling back to player
    outcome = action.execute(mining_context)

    # Should succeed because it fell back to player
    assert outcome.is_success


@pytest.mark.unit
def test_execute_fails_when_validation_fails(mining_context):
    """Execute returns failure when validation fails."""
    player = mining_context.get_player()

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id="nonexistent_ore",
        turns_remaining=1
    )

    outcome = action.execute(mining_context)

    assert not outcome.is_success
    assert "Cannot mine" in outcome.messages[0]


@pytest.mark.unit
def test_mining_completion_message_includes_ore_name(mining_context, copper_ore):
    """Completion message includes the name of the ore mined."""

    player = mining_context.get_player()
    copper_ore.x = player.x + 1
    copper_ore.y = player.y
    copper_ore.name = "Shiny Copper Ore"

    action = MineAction(
        actor_id=player.entity_id,
        ore_vein_id=copper_ore.entity_id,
        turns_remaining=1
    )

    outcome = action.execute(mining_context)

    assert any("Shiny Copper Ore" in msg for msg in outcome.messages)
