"""
Unit tests for Personal Loot System (Phase 3).

Tests the multiplayer personal loot feature:
- Single-player mode: Loot drops on ground (backward compatible)
- Multiplayer mode: Each player gets personal loot in inventory
- Inventory management: Full inventory handling
- Serialization: Inventory included in state
"""
import pytest
from unittest.mock import Mock
from core.actions.attack_action import AttackAction
from core.entities import Monster, Player
from core.base.entity import Entity, EntityType
from core.loot import LootGenerator


pytestmark = pytest.mark.unit


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_loot_generator():
    """Mock loot generator that returns predictable items."""
    generator = Mock(spec=LootGenerator)

    def generate_mock_loot(monster_type, floor_number=1):
        """Generate mock loot - returns a simple item."""
        item = Entity(
            entity_type=EntityType.ITEM,
            name=f"Mock Loot from {monster_type}",
            content_id="mock_loot",
            x=None,
            y=None,
        )
        item.stats['value'] = 10
        return [item]

    generator.generate_loot = Mock(side_effect=generate_mock_loot)
    return generator


@pytest.fixture
def multiplayer_context(game_context):
    """Create a game context with multiple players."""
    # Add second player
    player2 = Player(name="Player2", x=12, y=10)
    game_context.add_entity(player2)

    return game_context


@pytest.fixture
def weak_goblin_with_loot(weak_goblin):
    """Create a weak goblin that will drop loot."""
    weak_goblin.content_id = "goblin"  # Ensure it has a type for loot generation
    return weak_goblin


# ============================================================================
# Single-Player Mode Tests (Backward Compatibility)
# ============================================================================

@pytest.mark.unit
def test_single_player_loot_drops_on_ground(game_context, weak_goblin_with_loot, mock_loot_generator):
    """Single-player mode: Loot should drop on ground at monster position."""
    game_context.add_entity(weak_goblin_with_loot)
    player = game_context.get_player()

    # Kill the monster
    weak_goblin_with_loot.hp = 1  # Make it die in one hit

    action = AttackAction(
        actor_id=player.entity_id,
        target_id=weak_goblin_with_loot.entity_id,
        loot_generator=mock_loot_generator
    )

    outcome = action.execute(game_context)

    # Monster should be dead
    assert not weak_goblin_with_loot.is_alive

    # Loot should be generated
    assert mock_loot_generator.generate_loot.called

    # In single-player, loot should be placed on ground (not in inventory)
    # Check that items were added to world at monster's position
    items_at_monster_pos = game_context.get_entities_at(
        weak_goblin_with_loot.x,
        weak_goblin_with_loot.y,
        entity_type=EntityType.ITEM
    )

    assert len(items_at_monster_pos) > 0, "Loot should be on ground in single-player mode"
    assert len(player.inventory) == 0, "Player inventory should be empty in single-player loot drop"


# ============================================================================
# Multiplayer Mode Tests (Personal Loot)
# ============================================================================

@pytest.mark.unit
def test_multiplayer_loot_goes_to_inventory(multiplayer_context, weak_goblin_with_loot, mock_loot_generator):
    """Multiplayer mode: Loot should go directly to player inventories."""
    multiplayer_context.add_entity(weak_goblin_with_loot)
    player1 = multiplayer_context.get_player()

    # Get all players
    all_players = multiplayer_context.get_all_players()
    assert len(all_players) == 2, "Should have 2 players for multiplayer test"

    # Kill the monster
    weak_goblin_with_loot.hp = 1

    action = AttackAction(
        actor_id=player1.entity_id,
        target_id=weak_goblin_with_loot.entity_id,
        loot_generator=mock_loot_generator
    )

    outcome = action.execute(multiplayer_context)

    # Monster should be dead
    assert not weak_goblin_with_loot.is_alive

    # Each alive player should have received loot
    alive_players = [p for p in all_players if p.is_alive]

    # Mock generator is called once per alive player
    assert mock_loot_generator.generate_loot.call_count == len(alive_players)

    # Each player should have items in inventory
    for player in alive_players:
        assert len(player.inventory) > 0, f"{player.name} should have received loot in inventory"


@pytest.mark.unit
def test_multiplayer_each_player_gets_own_roll(multiplayer_context, weak_goblin_with_loot):
    """Each player should get independent loot rolls."""
    multiplayer_context.add_entity(weak_goblin_with_loot)
    player1 = multiplayer_context.get_player()

    # Create a loot generator that returns different items each time
    call_count = [0]

    def generate_unique_loot(monster_type, floor_number=1):
        call_count[0] += 1
        item = Entity(
            entity_type=EntityType.ITEM,
            name=f"Unique Item {call_count[0]}",
            content_id=f"item_{call_count[0]}",
            x=None,
            y=None,
        )
        return [item]

    generator = Mock(spec=LootGenerator)
    generator.generate_loot = Mock(side_effect=generate_unique_loot)

    # Kill the monster
    weak_goblin_with_loot.hp = 1

    action = AttackAction(
        actor_id=player1.entity_id,
        target_id=weak_goblin_with_loot.entity_id,
        loot_generator=generator
    )

    outcome = action.execute(multiplayer_context)

    # Get all players
    all_players = multiplayer_context.get_all_players()
    alive_players = [p for p in all_players if p.is_alive]

    # Each player should have different items
    item_names = set()
    for player in alive_players:
        assert len(player.inventory) > 0
        for item in player.inventory:
            item_names.add(item.name)

    # Should have unique items for each player
    assert len(item_names) == len(alive_players), "Each player should get unique loot roll"


@pytest.mark.unit
def test_multiplayer_inventory_full_drops_on_ground(multiplayer_context, weak_goblin_with_loot, mock_loot_generator):
    """When inventory is full, loot should drop on ground at player's position."""
    multiplayer_context.add_entity(weak_goblin_with_loot)
    player1 = multiplayer_context.get_player()

    # Fill player1's inventory to capacity
    for i in range(20):  # Max inventory size is 20
        filler_item = Entity(
            entity_type=EntityType.ITEM,
            name=f"Filler {i}",
            content_id="filler",
            x=None,
            y=None,
        )
        player1.add_to_inventory(filler_item)

    assert len(player1.inventory) == 20, "Player inventory should be full"

    # Kill the monster
    weak_goblin_with_loot.hp = 1

    action = AttackAction(
        actor_id=player1.entity_id,
        target_id=weak_goblin_with_loot.entity_id,
        loot_generator=mock_loot_generator
    )

    outcome = action.execute(multiplayer_context)

    # Loot should be dropped on ground at player's position (inventory full)
    items_at_player_pos = multiplayer_context.get_entities_at(
        player1.x,
        player1.y,
        entity_type=EntityType.ITEM
    )

    # Should have items on ground since inventory was full
    assert len(items_at_player_pos) > 0, "Loot should drop on ground when inventory full"

    # Inventory should still be at max capacity
    assert len(player1.inventory) == 20


@pytest.mark.unit
def test_multiplayer_dead_players_dont_get_loot(multiplayer_context, weak_goblin_with_loot, mock_loot_generator):
    """Dead players should not receive loot."""
    multiplayer_context.add_entity(weak_goblin_with_loot)
    player1 = multiplayer_context.get_player()

    # Get all players and kill one
    all_players = multiplayer_context.get_all_players()
    player2 = all_players[1]
    player2.hp = 0  # Kill player 2
    player2.is_alive = False  # Explicitly set is_alive

    assert not player2.is_alive, "Player 2 should be dead"
    assert player1.is_alive, "Player 1 should be alive"

    # Kill the monster
    weak_goblin_with_loot.hp = 1

    action = AttackAction(
        actor_id=player1.entity_id,
        target_id=weak_goblin_with_loot.entity_id,
        loot_generator=mock_loot_generator
    )

    outcome = action.execute(multiplayer_context)

    # Only alive players should get loot
    alive_players = [p for p in all_players if p.is_alive]
    assert len(alive_players) == 1, "Should only have 1 alive player"

    # Mock generator should be called once (only for alive player)
    assert mock_loot_generator.generate_loot.call_count == 1

    # Player 1 should have loot, Player 2 should not
    assert len(player1.inventory) > 0, "Alive player should receive loot"
    assert len(player2.inventory) == 0, "Dead player should not receive loot"


# ============================================================================
# Event and Message Tests
# ============================================================================

@pytest.mark.unit
def test_multiplayer_loot_messages(multiplayer_context, weak_goblin_with_loot, mock_loot_generator):
    """Personal loot should generate appropriate messages."""
    multiplayer_context.add_entity(weak_goblin_with_loot)
    player1 = multiplayer_context.get_player()

    # Kill the monster
    weak_goblin_with_loot.hp = 1

    action = AttackAction(
        actor_id=player1.entity_id,
        target_id=weak_goblin_with_loot.entity_id,
        loot_generator=mock_loot_generator
    )

    outcome = action.execute(multiplayer_context)

    # Should have messages about loot
    assert len(outcome.messages) > 0

    # At least one message should mention players receiving loot
    loot_messages = [m for m in outcome.messages if "received" in m.lower()]
    assert len(loot_messages) > 0, "Should have messages about players receiving loot"


@pytest.mark.unit
def test_multiplayer_loot_event(multiplayer_context, weak_goblin_with_loot, mock_loot_generator):
    """Personal loot should generate personal_loot_dropped event."""
    multiplayer_context.add_entity(weak_goblin_with_loot)
    player1 = multiplayer_context.get_player()

    # Kill the monster
    weak_goblin_with_loot.hp = 1

    action = AttackAction(
        actor_id=player1.entity_id,
        target_id=weak_goblin_with_loot.entity_id,
        loot_generator=mock_loot_generator
    )

    outcome = action.execute(multiplayer_context)

    # Should have events
    assert len(outcome.events) > 0

    # Find personal loot event
    loot_events = [e for e in outcome.events if e.get('type') == 'personal_loot_dropped']
    assert len(loot_events) == 1, "Should have one personal_loot_dropped event"

    # Event should have player_loot map
    loot_event = loot_events[0]
    assert 'player_loot' in loot_event
    assert isinstance(loot_event['player_loot'], dict)


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.unit
def test_no_loot_generated_no_error(multiplayer_context, weak_goblin_with_loot):
    """When no loot is generated, should not error."""
    multiplayer_context.add_entity(weak_goblin_with_loot)
    player1 = multiplayer_context.get_player()

    # Create generator that returns no loot
    generator = Mock(spec=LootGenerator)
    generator.generate_loot = Mock(return_value=[])

    # Kill the monster
    weak_goblin_with_loot.hp = 1

    action = AttackAction(
        actor_id=player1.entity_id,
        target_id=weak_goblin_with_loot.entity_id,
        loot_generator=generator
    )

    outcome = action.execute(multiplayer_context)

    # Should succeed without error
    assert outcome.success

    # Players should have empty inventories
    all_players = multiplayer_context.get_all_players()
    for player in all_players:
        assert len(player.inventory) == 0


@pytest.mark.unit
def test_single_player_to_multiplayer_transition(game_context, weak_goblin_with_loot, mock_loot_generator):
    """Test that loot behavior changes correctly when player count changes."""
    game_context.add_entity(weak_goblin_with_loot)
    player1 = game_context.get_player()

    # First kill in single-player mode
    weak_goblin1 = weak_goblin_with_loot
    weak_goblin1.hp = 1

    action1 = AttackAction(
        actor_id=player1.entity_id,
        target_id=weak_goblin1.entity_id,
        loot_generator=mock_loot_generator
    )

    outcome1 = action1.execute(game_context)

    # Loot should be on ground (single-player)
    items_at_pos1 = game_context.get_entities_at(
        weak_goblin1.x,
        weak_goblin1.y,
        entity_type=EntityType.ITEM
    )
    assert len(items_at_pos1) > 0, "Single-player loot should be on ground"

    # Add second player (now multiplayer)
    player2 = Player(name="Player2", x=12, y=10)
    game_context.add_entity(player2)

    # Create second goblin
    weak_goblin2 = Monster(
        name="Goblin2",
        content_id="goblin",
        x=11,
        y=11,
        hp=1,
        max_hp=5,
        attack=2,
        defense=1,
    )
    game_context.add_entity(weak_goblin2)

    # Second kill in multiplayer mode
    action2 = AttackAction(
        actor_id=player1.entity_id,
        target_id=weak_goblin2.entity_id,
        loot_generator=mock_loot_generator
    )

    outcome2 = action2.execute(game_context)

    # Now loot should go to inventories (multiplayer)
    assert len(player1.inventory) > 0 or len(player2.inventory) > 0, \
        "Multiplayer loot should go to inventories"
