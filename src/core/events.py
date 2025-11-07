"""
Event system for game events and observability.

This implements a lightweight pub/sub pattern that:
- Works with ActionOutcome.events field (already present)
- Supports Python subscribers now
- Can add Lua subscribers in Phase 3 (zero refactoring)
- Enables multiplayer in Phase 2 (events → NATS messages)

Design principles:
- Event-ready pattern (from EVENTS_ASYNC_OBSERVABILITY_GUIDE.md)
- Simple dict-based events (easy to serialize)
- Type-safe event types via enum
- Subscribers are callables (easy to mock/test)
"""

from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Any, Optional, TYPE_CHECKING
from enum import Enum
from collections import defaultdict
import logging
import time

if TYPE_CHECKING:
    from .events.lua_event_handler import LuaEventHandler

logger = logging.getLogger(__name__)


class GameEventType(Enum):
    """
    Types of game events that can be published.

    These events flow through the EventBus and can be subscribed to by:
    - Python systems (now)
    - Lua scripts (Phase 3)
    - NATS pub/sub (Phase 2 multiplayer)
    """
    # Combat events
    ATTACK_RESOLVED = "attack_resolved"
    ENTITY_DAMAGED = "entity_damaged"
    ENTITY_DIED = "entity_died"
    ENTITY_HEALED = "entity_healed"

    # Movement events
    ENTITY_MOVED = "entity_moved"
    PLAYER_MOVED = "player_moved"

    # Mining events
    ORE_SURVEYED = "ore_surveyed"
    ORE_MINED = "ore_mined"
    MINING_STARTED = "mining_started"
    MINING_COMPLETED = "mining_completed"

    # Crafting events
    ITEM_CRAFTED = "item_crafted"
    CRAFTING_STARTED = "crafting_started"
    CRAFTING_FAILED = "crafting_failed"

    # Item events
    ITEM_PICKED_UP = "item_picked_up"
    ITEM_DROPPED = "item_dropped"
    ITEM_EQUIPPED = "item_equipped"
    ITEM_UNEQUIPPED = "item_unequipped"
    ITEM_USED = "item_used"

    # Floor events
    FLOOR_CHANGED = "floor_changed"
    FLOOR_GENERATED = "floor_generated"

    # Turn events
    TURN_STARTED = "turn_started"
    TURN_ENDED = "turn_ended"

    # Game events
    GAME_STARTED = "game_started"
    GAME_OVER = "game_over"


@dataclass
class GameEvent:
    """
    Structured game event.

    This is the "result object" pattern from EVENTS_ASYNC_OBSERVABILITY_GUIDE.md.
    Events are created now, can be published to EventBus when ready.
    """
    event_type: GameEventType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    turn: Optional[int] = None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        This format is ready for:
        - NATS messages (Phase 2)
        - Lua event handlers (Phase 3)
        - Save/replay (future)
        """
        return {
            'type': self.event_type.value,
            'data': self.data.copy(),
            'timestamp': self.timestamp,
            'turn': self.turn,
        }

    @classmethod
    def from_dict(cls, event_dict: dict) -> 'GameEvent':
        """Deserialize from dictionary."""
        return cls(
            event_type=GameEventType(event_dict['type']),
            data=event_dict['data'],
            timestamp=event_dict.get('timestamp', time.time()),
            turn=event_dict.get('turn'),
        )


# Type alias for event subscribers
EventSubscriber = Callable[[GameEvent], None]


class EventBus:
    """
    Lightweight pub/sub event bus for game events.

    Design:
    - Python subscribers now (simple callbacks)
    - Lua subscribers later (LuaBridge integration)
    - NATS pub/sub in Phase 2 (multiplayer)

    Usage:
        # Subscribe to events
        event_bus.subscribe(GameEventType.ATTACK_RESOLVED, on_attack)

        # Publish events (from ActionOutcome)
        for event_data in outcome.events:
            event_bus.publish_dict(event_data)
    """

    def __init__(self):
        """Initialize empty event bus."""
        self.subscribers: Dict[GameEventType, List[EventSubscriber]] = defaultdict(list)
        self.lua_subscribers: Dict[GameEventType, List['LuaEventHandler']] = defaultdict(list)
        self.event_history: List[GameEvent] = []
        self.enable_history = False  # For debugging/testing

    def subscribe(
        self,
        event_type: GameEventType,
        subscriber: EventSubscriber,
        subscriber_name: Optional[str] = None
    ) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            subscriber: Callback function(event: GameEvent) -> None
            subscriber_name: Optional name for debugging
        """
        self.subscribers[event_type].append(subscriber)
        name = subscriber_name or subscriber.__name__
        logger.info(
            f"Subscriber registered: {name} → {event_type.value}",
            extra={'event_type': event_type.value, 'subscriber': name}
        )

    def unsubscribe(
        self,
        event_type: GameEventType,
        subscriber: EventSubscriber
    ) -> bool:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            subscriber: Callback to remove

        Returns:
            True if subscriber was found and removed
        """
        if event_type in self.subscribers and subscriber in self.subscribers[event_type]:
            self.subscribers[event_type].remove(subscriber)
            logger.debug(f"Subscriber removed from {event_type.value}")
            return True
        return False

    def subscribe_lua(
        self,
        event_type: GameEventType,
        handler: 'LuaEventHandler'
    ) -> None:
        """
        Subscribe Lua event handler to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: LuaEventHandler instance
        """
        self.lua_subscribers[event_type].append(handler)
        logger.info(
            f"Lua handler registered: {handler.handler_function} → {event_type.value}",
            extra={'event_type': event_type.value, 'handler': handler.handler_function}
        )

    def unsubscribe_lua(
        self,
        event_type: GameEventType,
        handler: 'LuaEventHandler'
    ) -> bool:
        """
        Unsubscribe Lua event handler from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: LuaEventHandler instance to remove

        Returns:
            True if handler was found and removed
        """
        if event_type in self.lua_subscribers and handler in self.lua_subscribers[event_type]:
            self.lua_subscribers[event_type].remove(handler)
            logger.debug(f"Lua handler removed from {event_type.value}")
            return True
        return False

    def publish(self, event: GameEvent) -> None:
        """
        Publish a structured GameEvent.

        Args:
            event: GameEvent to publish
        """
        # Store in history if enabled
        if self.enable_history:
            self.event_history.append(event)

        # Notify subscribers
        subscribers = self.subscribers.get(event.event_type, [])

        if not subscribers:
            logger.debug(
                f"Event published with no subscribers: {event.event_type.value}",
                extra={'event_type': event.event_type.value, 'data': event.data}
            )
            return

        # Count total subscribers (Python + Lua)
        lua_subscribers = self.lua_subscribers.get(event.event_type, [])
        total_subscribers = len(subscribers) + len(lua_subscribers)

        logger.debug(
            f"Event published: {event.event_type.value} → "
            f"{len(subscribers)} Python + {len(lua_subscribers)} Lua subscribers",
            extra={
                'event_type': event.event_type.value,
                'python_subscribers': len(subscribers),
                'lua_subscribers': len(lua_subscribers)
            }
        )

        # 1. Call Python subscribers (EXISTING)
        for subscriber in subscribers:
            try:
                subscriber(event)
            except Exception as e:
                logger.error(
                    f"Error in Python subscriber for {event.event_type.value}",
                    exc_info=True,
                    extra={
                        'event_type': event.event_type.value,
                        'subscriber': subscriber.__name__,
                        'error': str(e)
                    }
                )

        # 2. Call Lua subscribers (NEW)
        for lua_handler in lua_subscribers:
            try:
                lua_handler.handle(event)
            except Exception as e:
                logger.error(
                    f"Error in Lua subscriber for {event.event_type.value}",
                    exc_info=True,
                    extra={
                        'event_type': event.event_type.value,
                        'handler': lua_handler.handler_function,
                        'script': lua_handler.script_path,
                        'error': str(e)
                    }
                )

    def publish_dict(self, event_dict: dict) -> None:
        """
        Publish event from dictionary (for ActionOutcome.events).

        This is the integration point with existing ActionOutcome.events field.
        Actions create event dicts, we convert to GameEvent and publish.

        Args:
            event_dict: Event dictionary with 'type' and 'data' keys
        """
        try:
            event = GameEvent.from_dict(event_dict)
            self.publish(event)
        except (KeyError, ValueError) as e:
            logger.error(
                f"Failed to publish event from dict: {e}",
                exc_info=True,
                extra={'event_dict': event_dict}
            )

    def publish_all(self, events: List[dict]) -> None:
        """
        Publish multiple events from ActionOutcome.events list.

        This is the main integration point - Game.handle_player_action()
        will call this with outcome.events.

        Args:
            events: List of event dictionaries from ActionOutcome
        """
        for event_dict in events:
            self.publish_dict(event_dict)

    def clear_history(self) -> None:
        """Clear event history (for testing)."""
        self.event_history.clear()

    def get_events_by_type(self, event_type: GameEventType) -> List[GameEvent]:
        """
        Get events from history by type.

        Requires enable_history=True.

        Args:
            event_type: Type of events to retrieve

        Returns:
            List of matching events
        """
        return [e for e in self.event_history if e.event_type == event_type]

    def get_subscriber_count(self, event_type: GameEventType) -> int:
        """
        Get number of subscribers for an event type.

        Useful for debugging and testing.

        Args:
            event_type: Event type to check

        Returns:
            Number of Python subscribers (use get_lua_subscriber_count for Lua)
        """
        return len(self.subscribers.get(event_type, []))

    def get_lua_subscriber_count(self, event_type: GameEventType) -> int:
        """
        Get number of Lua subscribers for an event type.

        Args:
            event_type: Event type to check

        Returns:
            Number of Lua subscribers
        """
        return len(self.lua_subscribers.get(event_type, []))


# ============================================================================
# Event Builder Helpers
# ============================================================================
# These helpers create event dicts that Actions can add to ActionOutcome.events.
# Following the pattern from EVENTS_ASYNC_OBSERVABILITY_GUIDE.md where actions
# return structured result objects with to_dict() methods.


def create_attack_event(
    attacker_id: str,
    defender_id: str,
    damage: int,
    killed: bool,
    turn: Optional[int] = None
) -> dict:
    """
    Create attack resolved event.

    This is what actions add to ActionOutcome.events:
        outcome.events.append(create_attack_event(...))

    Args:
        attacker_id: Entity ID of attacker
        defender_id: Entity ID of defender
        damage: Damage dealt
        killed: Whether defender was killed
        turn: Current turn number (optional)

    Returns:
        Event dict ready for ActionOutcome.events
    """
    return {
        'type': GameEventType.ATTACK_RESOLVED.value,
        'data': {
            'attacker_id': attacker_id,
            'defender_id': defender_id,
            'damage': damage,
            'killed': killed,
        },
        'timestamp': time.time(),
        'turn': turn,
    }


def create_entity_died_event(
    entity_id: str,
    entity_name: str,
    killer_id: Optional[str] = None,
    cause: str = "combat",
    turn: Optional[int] = None
) -> dict:
    """Create entity died event."""
    return {
        'type': GameEventType.ENTITY_DIED.value,
        'data': {
            'entity_id': entity_id,
            'entity_name': entity_name,
            'killer_id': killer_id,
            'cause': cause,
        },
        'timestamp': time.time(),
        'turn': turn,
    }


def create_entity_moved_event(
    entity_id: str,
    from_x: int,
    from_y: int,
    to_x: int,
    to_y: int,
    turn: Optional[int] = None
) -> dict:
    """Create entity moved event."""
    return {
        'type': GameEventType.ENTITY_MOVED.value,
        'data': {
            'entity_id': entity_id,
            'from_x': from_x,
            'from_y': from_y,
            'to_x': to_x,
            'to_y': to_y,
        },
        'timestamp': time.time(),
        'turn': turn,
    }


def create_ore_mined_event(
    ore_id: str,
    miner_id: str,
    ore_type: str,
    properties: Dict[str, Any],
    turn: Optional[int] = None
) -> dict:
    """Create ore mined event."""
    return {
        'type': GameEventType.ORE_MINED.value,
        'data': {
            'ore_id': ore_id,
            'miner_id': miner_id,
            'ore_type': ore_type,
            'properties': properties,
        },
        'timestamp': time.time(),
        'turn': turn,
    }


def create_item_crafted_event(
    item_id: str,
    item_name: str,
    recipe_id: str,
    crafter_id: str,
    stats: Dict[str, Any],
    turn: Optional[int] = None
) -> dict:
    """Create item crafted event."""
    return {
        'type': GameEventType.ITEM_CRAFTED.value,
        'data': {
            'item_id': item_id,
            'item_name': item_name,
            'recipe_id': recipe_id,
            'crafter_id': crafter_id,
            'stats': stats,
        },
        'timestamp': time.time(),
        'turn': turn,
    }


def create_floor_changed_event(
    from_floor: int,
    to_floor: int,
    player_id: str,
    turn: Optional[int] = None
) -> dict:
    """Create floor changed event."""
    return {
        'type': GameEventType.FLOOR_CHANGED.value,
        'data': {
            'from_floor': from_floor,
            'to_floor': to_floor,
            'player_id': player_id,
        },
        'timestamp': time.time(),
        'turn': turn,
    }
