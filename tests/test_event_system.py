"""
Tests for event system (EventBus, GameEvent, Telemetry).

Tests the event-ready pattern implementation from
EVENTS_ASYNC_OBSERVABILITY_GUIDE.md.
"""

import pytest
from src.core.events import (
    EventBus,
    GameEvent,
    GameEventType,
    create_attack_event,
    create_entity_died_event,
    create_ore_mined_event,
    create_floor_changed_event,
)
from src.core.telemetry import StatsTracker, GameTelemetry


class TestEventBus:
    """Test EventBus pub/sub functionality."""

    def test_subscribe_and_publish(self):
        """Test basic subscribe and publish."""
        event_bus = EventBus()
        received_events = []

        def subscriber(event: GameEvent):
            received_events.append(event)

        event_bus.subscribe(GameEventType.ATTACK_RESOLVED, subscriber)

        # Create and publish event
        event_dict = create_attack_event(
            attacker_id="player",
            defender_id="goblin_1",
            damage=10,
            killed=True
        )
        event_bus.publish_dict(event_dict)

        # Verify subscriber received event
        assert len(received_events) == 1
        assert received_events[0].event_type == GameEventType.ATTACK_RESOLVED
        assert received_events[0].data['damage'] == 10
        assert received_events[0].data['killed'] == True

    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event."""
        event_bus = EventBus()
        subscriber1_count = []
        subscriber2_count = []

        def subscriber1(event):
            subscriber1_count.append(1)

        def subscriber2(event):
            subscriber2_count.append(1)

        event_bus.subscribe(GameEventType.ATTACK_RESOLVED, subscriber1)
        event_bus.subscribe(GameEventType.ATTACK_RESOLVED, subscriber2)

        # Publish event
        event_dict = create_attack_event(
            attacker_id="player",
            defender_id="goblin_1",
            damage=5,
            killed=False
        )
        event_bus.publish_dict(event_dict)

        # Both subscribers should receive event
        assert len(subscriber1_count) == 1
        assert len(subscriber2_count) == 1

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        event_bus = EventBus()
        received_events = []

        def subscriber(event):
            received_events.append(event)

        event_bus.subscribe(GameEventType.ATTACK_RESOLVED, subscriber)
        event_bus.unsubscribe(GameEventType.ATTACK_RESOLVED, subscriber)

        # Publish event
        event_dict = create_attack_event(
            attacker_id="player",
            defender_id="goblin_1",
            damage=5,
            killed=False
        )
        event_bus.publish_dict(event_dict)

        # Subscriber should not receive event
        assert len(received_events) == 0

    def test_publish_all(self):
        """Test publishing multiple events at once."""
        event_bus = EventBus()
        received_events = []

        def subscriber(event):
            received_events.append(event)

        event_bus.subscribe(GameEventType.ATTACK_RESOLVED, subscriber)
        event_bus.subscribe(GameEventType.ENTITY_DIED, subscriber)

        # Publish multiple events (like ActionOutcome.events)
        events = [
            create_attack_event("player", "goblin_1", 10, True),
            create_entity_died_event("goblin_1", "Goblin", killer_id="player"),
        ]
        event_bus.publish_all(events)

        # Should receive both events
        assert len(received_events) == 2
        assert received_events[0].event_type == GameEventType.ATTACK_RESOLVED
        assert received_events[1].event_type == GameEventType.ENTITY_DIED

    def test_event_history(self):
        """Test event history tracking."""
        event_bus = EventBus()
        event_bus.enable_history = True

        # Publish events
        event_dict1 = create_attack_event("player", "goblin_1", 10, False)
        event_dict2 = create_attack_event("player", "goblin_2", 15, True)
        event_bus.publish_dict(event_dict1)
        event_bus.publish_dict(event_dict2)

        # Check history
        assert len(event_bus.event_history) == 2
        attack_events = event_bus.get_events_by_type(GameEventType.ATTACK_RESOLVED)
        assert len(attack_events) == 2
        assert attack_events[0].data['damage'] == 10
        assert attack_events[1].data['damage'] == 15


class TestStatsTracker:
    """Test StatsTracker event subscriber."""

    def test_attack_resolved_tracking(self):
        """Test tracking attack events."""
        stats = StatsTracker()

        # Create attack event
        event = GameEvent.from_dict(create_attack_event(
            attacker_id="player",
            defender_id="goblin_1",
            damage=10,
            killed=False
        ))

        # Handle event
        stats.on_attack_resolved(event)

        # Verify stats updated
        assert stats.attacks_made == 1
        assert stats.total_damage_dealt == 10
        assert stats.monsters_killed == 0

    def test_kill_tracking(self):
        """Test tracking monster kills."""
        stats = StatsTracker()

        # Create attack with kill
        event = GameEvent.from_dict(create_attack_event(
            attacker_id="player",
            defender_id="goblin_1",
            damage=15,
            killed=True
        ))

        stats.on_attack_resolved(event)

        # Verify kill counted
        assert stats.monsters_killed == 1
        assert stats.total_damage_dealt == 15

    def test_ore_mined_tracking(self):
        """Test tracking ore mining."""
        stats = StatsTracker()

        # Create ore mined event
        event = GameEvent.from_dict(create_ore_mined_event(
            ore_id="ore_1",
            miner_id="player",
            ore_type="copper",
            properties={'hardness': 50, 'purity': 80}
        ))

        stats.on_ore_mined(event)

        # Verify ore counted
        assert stats.ore_mined == 1

    def test_floor_changed_tracking(self):
        """Test tracking floor changes."""
        stats = StatsTracker()

        # Create floor changed event
        event = GameEvent.from_dict(create_floor_changed_event(
            from_floor=1,
            to_floor=2,
            player_id="player"
        ))

        stats.on_floor_changed(event)

        # Verify floor descent counted
        assert stats.floors_descended == 1

    def test_event_bus_integration(self):
        """Test StatsTracker integrated with EventBus."""
        event_bus = EventBus()
        stats = StatsTracker()

        # Subscribe stats tracker to events
        event_bus.subscribe(GameEventType.ATTACK_RESOLVED, stats.on_attack_resolved)
        event_bus.subscribe(GameEventType.ORE_MINED, stats.on_ore_mined)

        # Publish events through bus
        event_bus.publish_all([
            create_attack_event("player", "goblin_1", 10, True),
            create_attack_event("player", "goblin_2", 15, False),
            create_ore_mined_event("ore_1", "player", "iron", {'purity': 90}),
        ])

        # Verify stats updated correctly
        assert stats.attacks_made == 2
        assert stats.total_damage_dealt == 25
        assert stats.monsters_killed == 1
        assert stats.ore_mined == 1

    def test_get_session_stats(self):
        """Test getting session statistics summary."""
        stats = StatsTracker()

        # Simulate some gameplay
        stats.on_attack_resolved(GameEvent.from_dict(
            create_attack_event("player", "goblin_1", 10, True)
        ))
        stats.on_ore_mined(GameEvent.from_dict(
            create_ore_mined_event("ore_1", "player", "copper", {})
        ))
        stats.on_floor_changed(GameEvent.from_dict(
            create_floor_changed_event(1, 2, "player")
        ))

        # Get summary
        summary = stats.get_session_stats()

        assert summary['monsters_killed'] == 1
        assert summary['damage_dealt'] == 10
        assert summary['ore_mined'] == 1
        assert summary['floors_descended'] == 1


class TestEventBuilders:
    """Test event builder helper functions."""

    def test_create_attack_event(self):
        """Test attack event builder."""
        event_dict = create_attack_event(
            attacker_id="player",
            defender_id="goblin_1",
            damage=10,
            killed=True,
            turn=5
        )

        assert event_dict['type'] == GameEventType.ATTACK_RESOLVED.value
        assert event_dict['data']['attacker_id'] == "player"
        assert event_dict['data']['defender_id'] == "goblin_1"
        assert event_dict['data']['damage'] == 10
        assert event_dict['data']['killed'] == True
        assert event_dict['turn'] == 5

    def test_create_entity_died_event(self):
        """Test entity died event builder."""
        event_dict = create_entity_died_event(
            entity_id="goblin_1",
            entity_name="Goblin",
            killer_id="player",
            cause="combat"
        )

        assert event_dict['type'] == GameEventType.ENTITY_DIED.value
        assert event_dict['data']['entity_id'] == "goblin_1"
        assert event_dict['data']['entity_name'] == "Goblin"
        assert event_dict['data']['killer_id'] == "player"
        assert event_dict['data']['cause'] == "combat"

    def test_create_ore_mined_event(self):
        """Test ore mined event builder."""
        event_dict = create_ore_mined_event(
            ore_id="ore_1",
            miner_id="player",
            ore_type="iron",
            properties={'hardness': 70, 'purity': 85}
        )

        assert event_dict['type'] == GameEventType.ORE_MINED.value
        assert event_dict['data']['ore_id'] == "ore_1"
        assert event_dict['data']['miner_id'] == "player"
        assert event_dict['data']['ore_type'] == "iron"
        assert event_dict['data']['properties']['hardness'] == 70

    def test_create_floor_changed_event(self):
        """Test floor changed event builder."""
        event_dict = create_floor_changed_event(
            from_floor=1,
            to_floor=2,
            player_id="player"
        )

        assert event_dict['type'] == GameEventType.FLOOR_CHANGED.value
        assert event_dict['data']['from_floor'] == 1
        assert event_dict['data']['to_floor'] == 2
        assert event_dict['data']['player_id'] == "player"


class TestGameEvent:
    """Test GameEvent data structure."""

    def test_to_dict(self):
        """Test event serialization."""
        event = GameEvent(
            event_type=GameEventType.ATTACK_RESOLVED,
            data={'damage': 10},
            turn=5
        )

        event_dict = event.to_dict()

        assert event_dict['type'] == 'attack_resolved'
        assert event_dict['data']['damage'] == 10
        assert event_dict['turn'] == 5
        assert 'timestamp' in event_dict

    def test_from_dict(self):
        """Test event deserialization."""
        event_dict = {
            'type': 'attack_resolved',
            'data': {'damage': 15},
            'turn': 3,
            'timestamp': 123456.789
        }

        event = GameEvent.from_dict(event_dict)

        assert event.event_type == GameEventType.ATTACK_RESOLVED
        assert event.data['damage'] == 15
        assert event.turn == 3
        assert event.timestamp == 123456.789


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
