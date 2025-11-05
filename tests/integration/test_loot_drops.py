"""Integration tests for loot drop system.

Tests complete combat → loot drop workflow.
"""

import pytest
from core.entities import Monster, EntityType
from core.actions.attack_action import AttackAction
from core.loot import LootGenerator
from core.base.entity import Entity


pytestmark = pytest.mark.integration

@pytest.mark.integration
def test_loot_system_integration(game_state_with_monster):
    """Complete integration test: monster dies → loot generated → loot appears in world."""
    state = game_state_with_monster
    player = state.player

    # Find the goblin from fixture
    monsters = [e for e in state.entities.values() if e.entity_type == EntityType.MONSTER]
    assert len(monsters) == 1
    goblin = monsters[0]

    # Set goblin content_id for loot generation
    goblin.content_id = "goblin"

    # Record initial count
    initial_entity_count = len(state.entities)

    # Create loot generator
    loot_gen = LootGenerator()

    # Attack monster until dead (player has 5 attack, goblin has 1 defense = 4 damage per hit)
    # Goblin has 6 HP, so need 2 hits
    attack_count = 0
    for _ in range(10):  # Safety limit
        action = AttackAction(
            actor_id=player.entity_id,
            target_id=goblin.entity_id,
            loot_generator=loot_gen
        )

        # Need to create a game context for action execution
        from core.base.game_context import GameContext
        context = GameContext(state)

        outcome = action.execute(context)
        attack_count += 1

        if not goblin.is_alive:
            # Monster died!
            assert "died" in " ".join(outcome.messages).lower()

            # Check if any loot was generated (it's probabilistic)
            # Goblins have 70% gold drop, 20% weapon, 30% potion, etc.
            # So some loot should appear over multiple test runs

            # Check for loot entities
            loot_items = [
                e for e in state.entities.values()
                if e.entity_type == EntityType.ITEM
            ]

            # Note: Loot is probabilistic, so we can't guarantee drops
            # But if there are drops, they should be valid entities
            for item in loot_items:
                assert item.content_id is not None
                assert item.name is not None
                # Loot should be at goblin's death position
                assert item.x == goblin.x
                assert item.y == goblin.y

            # Monster should be dead
            assert not goblin.is_alive

            break

    assert attack_count <= 3, "Should kill goblin in 2-3 hits"


@pytest.mark.integration
def test_loot_generator_produces_valid_items():
    """LootGenerator creates valid item entities."""
    generator = LootGenerator()

    # Generate loot for all monster types
    for monster_type in ['goblin', 'orc', 'troll']:
        items = generator.generate_loot(monster_type)

        # Items may or may not drop (probabilistic)
        for item in items:
            # Each item should be a valid Entity
            assert isinstance(item, Entity)
            assert item.entity_type == EntityType.ITEM
            assert item.content_id is not None
            assert item.name is not None

            # Items should have expected stats
            item_type = item.get_stat('item_type')
            assert item_type in [
                'weapon', 'armor', 'potion', 'scroll',
                'food', 'ring', 'gold', 'shield'
            ]


@pytest.mark.integration
def test_loot_drop_events_logged(game_state_with_monster):
    """Loot drops generate proper events in action outcome."""
    state = game_state_with_monster
    player = state.player

    # Get the monster
    monsters = [e for e in state.entities.values() if e.entity_type == EntityType.MONSTER]
    goblin = monsters[0]
    goblin.content_id = "goblin"

    # Make goblin easy to kill
    goblin.hp = 1

    # Kill it
    from core.base.game_context import GameContext
    context = GameContext(state)

    action = AttackAction(
        actor_id=player.entity_id,
        target_id=goblin.entity_id,
        loot_generator=LootGenerator()
    )

    outcome = action.execute(context)

    # Should have died
    assert not goblin.is_alive

    # Check for death event
    death_events = [e for e in outcome.events if e.get('type') == 'entity_died']
    assert len(death_events) == 1

    # May have loot drop events (probabilistic)
    loot_events = [e for e in outcome.events if e.get('type') == 'loot_dropped']

    for event in loot_events:
        # Loot events should have proper structure
        assert 'monster_id' in event
        assert 'monster_type' in event
        assert 'position' in event
        assert 'items' in event
        assert event['monster_type'] == 'goblin'
