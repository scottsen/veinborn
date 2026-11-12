# Event System Architecture

**Status:** ✅ Implemented
**Phase:** MVP (Phase 2-ready)
**Date:** 2025-11-06

---

## Overview

The event system implements a lightweight pub/sub pattern that integrates seamlessly with the existing `ActionOutcome.events` field. It follows the **event-ready pattern** from `EVENTS_ASYNC_OBSERVABILITY_GUIDE.md`.

### Key Design Principles

1. **MVP-ready:** Works with Python subscribers now
2. **Extensible:** content modules subscribe through `@event_handler` / `@on(...)` with no core changes
3. **Phase 2-ready:** Events can publish to NATS message bus for multiplayer
4. **Event-ready pattern:** Actions return structured result objects that become events

---

## Architecture Components

### 1. EventBus (`src/core/events.py`)

The central pub/sub hub for game events.

```python
from src.core.events import EventBus, GameEventType

# Create event bus
event_bus = EventBus()

# Subscribe to events
def on_attack(event: GameEvent):
    print(f"Attack dealt {event.data['damage']} damage!")

event_bus.subscribe(GameEventType.ATTACK_RESOLVED, on_attack)

# Publish events (from ActionOutcome)
outcome = action.execute(context)
event_bus.publish_all(outcome.events)
```

**Key Features:**
- Type-safe event types via `GameEventType` enum
- Multiple subscribers per event type
- Error handling (subscriber errors don't break event flow)
- Optional event history for debugging/testing

---

### 2. GameEvent (`src/core/events.py`)

Structured event data class.

```python
@dataclass
class GameEvent:
    event_type: GameEventType
    data: Dict[str, Any]
    timestamp: float
    turn: Optional[int]
```

**Event Types (26 total):**
- **Combat:** `ATTACK_RESOLVED`, `ENTITY_DAMAGED`, `ENTITY_DIED`, `ENTITY_HEALED`
- **Movement:** `ENTITY_MOVED`, `PLAYER_MOVED`
- **Mining:** `ORE_SURVEYED`, `ORE_MINED`, `MINING_STARTED`, `MINING_COMPLETED`
- **Crafting:** `ITEM_CRAFTED`, `CRAFTING_STARTED`, `CRAFTING_FAILED`
- **Items:** `ITEM_PICKED_UP`, `ITEM_DROPPED`, `ITEM_EQUIPPED`, `ITEM_UNEQUIPPED`, `ITEM_USED`
- **Floor:** `FLOOR_CHANGED`, `FLOOR_GENERATED`
- **Turn:** `TURN_STARTED`, `TURN_ENDED`
- **Game:** `GAME_STARTED`, `GAME_OVER`

---

### 3. Event Builder Helpers (`src/core/events.py`)

Type-safe helper functions for creating events.

```python
from src.core.events import (
    create_attack_event,
    create_entity_died_event,
    create_ore_mined_event,
    create_floor_changed_event,
)

# In an action's execute() method:
outcome = ActionOutcome.success(took_turn=True)
outcome.messages.append("You hit the goblin for 10 damage!")
outcome.events.append(create_attack_event(
    attacker_id=self.actor_id,
    defender_id=self.target_id,
    damage=10,
    killed=False,
))
```

**Benefits:**
- Type safety (catches missing fields at development time)
- Consistent event format
- Self-documenting code
- Easy to refactor

---

### 4. StatsTracker (`src/core/telemetry.py`)

Event subscriber that tracks game statistics.

```python
class StatsTracker:
    def on_attack_resolved(self, event: GameEvent) -> None:
        """Track combat statistics."""
        self.attacks_made += 1
        self.total_damage_dealt += event.data['damage']
        if event.data['killed']:
            self.monsters_killed += 1
```

**Tracked Statistics:**
- Combat: damage dealt/taken, kills, attacks made
- Mining: ore mined, ore surveyed, turns spent mining
- Crafting: items crafted, crafting failures
- Exploration: floors descended, tiles explored, turns played
- Deaths: player death records with context

**Event-Ready Pattern:**
```python
# MVP: Direct calls
result = combat_system.resolve_attack(attacker, defender)
stats.on_attack_resolved(result)

# Phase 2: Event subscription (SAME METHOD!)
event_bus.subscribe(ATTACK_RESOLVED, stats.on_attack_resolved)
# No more direct calls needed - automatic!
```

---

### 5. Game Integration (`src/core/game.py`)

The Game class integrates everything:

```python
class Game:
    def __init__(self):
        # Event system and telemetry
        self.event_bus = EventBus()
        self.stats_tracker = StatsTracker()

    def _initialize_subsystems(self):
        # Subscribe telemetry to events
        self._subscribe_event_handlers()

    def _subscribe_event_handlers(self):
        """Subscribe event handlers to EventBus."""
        self.event_bus.subscribe(
            GameEventType.ATTACK_RESOLVED,
            self.stats_tracker.on_attack_resolved,
        )
        # ... more subscriptions ...

    def handle_player_action(self, action_type: str, **kwargs) -> bool:
        action = self.action_factory.create(action_type, **kwargs)
        outcome = action.execute(self.context)

        # Publish events to EventBus
        if outcome.events:
            self.event_bus.publish_all(outcome.events)

        # Add messages, process turn, etc.
        # ...
```

---

## Usage Examples

### Example 1: Track Combat Statistics

```python
from src.core.events import EventBus, GameEventType
from src.core.telemetry import StatsTracker

# Setup
event_bus = EventBus()
stats = StatsTracker()
event_bus.subscribe(GameEventType.ATTACK_RESOLVED, stats.on_attack_resolved)

# Game runs, events publish automatically
# ...

# Get statistics
session_stats = stats.get_session_stats()
print(f"Monsters killed: {session_stats['monsters_killed']}")
print(f"Damage dealt: {session_stats['damage_dealt']}")
```

### Example 2: Custom Achievement System

```python
class AchievementTracker:
    def __init__(self):
        self.centurion_unlocked = False

    def on_entity_died(self, event: GameEvent):
        """Track kills for achievements."""
        if event.data.get('killer_id') == 'player':
            # Check for Centurion achievement (100 kills)
            if self.kill_count >= 100 and not self.centurion_unlocked:
                print("🏆 Achievement: Centurion (100 kills)")
                self.centurion_unlocked = True

# Subscribe to events
event_bus.subscribe(GameEventType.ENTITY_DIED, achievements.on_entity_died)
```

### Example 3: Debug Event Logging

```python
# Enable event history for debugging
game.event_bus.enable_history = True

# Play game...
# ...

# Review events
attack_events = game.event_bus.get_events_by_type(GameEventType.ATTACK_RESOLVED)
for event in attack_events:
    print(f"Turn {event.turn}: {event.data['damage']} damage")
```

---

## Action Implementation Guide

### Adding Events to Actions

**Step 1:** Import event builders
```python
from ..events import create_attack_event, create_entity_died_event
```

**Step 2:** Create events in execute() method
```python
def execute(self, context: GameContext) -> ActionOutcome:
    # ... perform action logic ...

    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append("You hit the goblin!")

    # Add events
    outcome.events.append(create_attack_event(
        attacker_id=self.actor_id,
        defender_id=self.target_id,
        damage=actual_damage,
        killed=not target.is_alive,
    ))

    return outcome
```

**Step 3:** That's it! Events auto-publish via Game.handle_player_action()

---

## Event Flow

```
┌─────────────┐
│   Action    │ Creates structured events
│  execute()  │ via event builder helpers
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ ActionOutcome   │ events: list[dict]
│   .events       │ (ready to publish)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Game.handle_    │ Publishes events
│ player_action() │ to EventBus
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   EventBus      │ Distributes to
│  .publish_all() │ subscribers
└──────┬──────────┘
       │
       ├──────────┐
       │          │
       ▼          ▼
┌─────────┐  ┌─────────┐
│ Stats   │  │ Custom  │
│Tracker  │  │ Systems │
└─────────┘  └─────────┘
```

---

## Future Extensions

### Phase 2: Multiplayer (NATS Integration)

```python
class EventBus:
    def publish(self, event: GameEvent):
        # Python subscribers (now)
        for subscriber in self.subscribers[event.event_type]:
            subscriber(event)

        # NATS pub/sub (Phase 2 - just add this!)
        if self.nats_client:
            self.nats_client.publish(
                f"game.events.{event.event_type.value}",
                event.to_dict()
            )
```

**Zero refactoring needed** - just add NATS publishing!

---

### Content event handlers (implemented)

Game content subscribes through `@event_handler` classes in `src/core/content/events/`
(achievements, quests, kill streaks). `Game` installs one instance of each per game
and subscribes every `@on(...)` method to the bus. See [../EXTENDING.md](../EXTENDING.md).
Lua subscribers were built and then removed (ADR-018 in `DECISIONS.md`).

**Events the single-player `Game` publishes:** every `ActionOutcome.events` entry,
plus `game_started` (once), `turn_ended` (after every processed turn) and
`floor_changed` (after a descent).

---

## Testing

### Unit Tests

```python
# Test EventBus
def test_subscribe_and_publish():
    event_bus = EventBus()
    received = []

    event_bus.subscribe(GameEventType.ATTACK_RESOLVED,
                       lambda e: received.append(e))

    event_dict = create_attack_event("player", "goblin", 10, False)
    event_bus.publish_dict(event_dict)

    assert len(received) == 1
    assert received[0].data['damage'] == 10
```

### Integration Tests

```python
def test_game_integration():
    """Test events flow through real game."""
    game = Game()
    game.start_new_game()

    initial_stats = game.stats_tracker.get_session_stats()
    assert initial_stats['monsters_killed'] == 0

    # Perform attack action
    game.handle_player_action('attack', target_id='goblin_1')

    # Stats should update automatically via events!
    final_stats = game.stats_tracker.get_session_stats()
    assert final_stats['monsters_killed'] > 0
```

---

## Performance Considerations

### Event Bus Overhead

- **Subscriber lookup:** O(1) dictionary lookup
- **Event dispatch:** O(n) where n = number of subscribers
- **Typical case:** 3-5 subscribers per event type
- **Overhead:** < 1ms per event (negligible)

### Memory Usage

- **Event storage:** Only if `enable_history=True`
- **Typical session:** 1000-5000 events = ~1MB
- **Recommendation:** Keep history disabled in production

### Optimization Tips

1. **Don't create events unnecessarily**
   - Only create events for gameplay-significant actions
   - Not every HP change needs an event

2. **Batch event processing**
   - `publish_all()` is more efficient than individual publishes
   - Actions already return batched events

3. **Subscriber efficiency**
   - Keep subscriber callbacks fast (< 1ms)
   - Don't do expensive work in subscribers
   - Use async processing for slow operations (Phase 2)

---

## Troubleshooting

### Events Not Received

**Problem:** Subscriber doesn't receive events

**Solutions:**
1. Check subscriber is registered before events publish
   ```python
   # ❌ BAD - subscribe after event
   event_bus.publish_dict(event)
   event_bus.subscribe(EVENT_TYPE, subscriber)

   # ✅ GOOD - subscribe before event
   event_bus.subscribe(EVENT_TYPE, subscriber)
   event_bus.publish_dict(event)
   ```

2. Check event type matches
   ```python
   # Event uses wrong type
   event_dict = {'type': 'attack'}  # Should be 'attack_resolved'
   ```

3. Check Game._subscribe_event_handlers() was called
   ```python
   # In Game.__init__ or start_new_game()
   self._initialize_subsystems()  # This calls _subscribe_event_handlers()
   ```

---

### Subscriber Errors Breaking Game

**Problem:** Subscriber throws exception, game crashes

**Solution:** EventBus catches subscriber errors automatically
```python
# EventBus.publish() catches exceptions
try:
    subscriber(event)
except Exception as e:
    logger.error(f"Error in subscriber: {e}")
    # Game continues!
```

---

## Best Practices

### ✅ DO

1. **Use event builder helpers**
   ```python
   outcome.events.append(create_attack_event(...))  # Type-safe!
   ```

2. **Keep subscribers fast**
   ```python
   def on_attack(event):
       self.damage_dealt += event.data['damage']  # Fast!
   ```

3. **Subscribe in initialization**
   ```python
   def _subscribe_event_handlers(self):
       self.event_bus.subscribe(EVENT_TYPE, handler)
   ```

### ❌ DON'T

1. **Don't create raw event dicts**
   ```python
   # ❌ BAD - no type safety
   outcome.events.append({'type': 'attack', 'damage': 10})

   # ✅ GOOD - use helper
   outcome.events.append(create_attack_event(...))
   ```

2. **Don't do expensive work in subscribers**
   ```python
   # ❌ BAD - blocks event loop
   def on_attack(event):
       time.sleep(5)  # NEVER!
       save_to_database()  # Use async in Phase 2
   ```

3. **Don't subscribe in tight loops**
   ```python
   # ❌ BAD - creates duplicate subscriptions
   for i in range(100):
       event_bus.subscribe(EVENT_TYPE, handler)
   ```

---

## Summary

The event system provides:

✅ **MVP functionality** - Stats tracking, telemetry, achievements
✅ **Extensible** - Content modules subscribe with `@event_handler` / `@on(...)` (see EXTENDING.md)
✅ **Phase 2-ready** - Can publish to NATS with 5 lines of code
✅ **Type-safe** - Event builders catch errors at development time
✅ **Testable** - Easy to unit test and mock
✅ **Performant** - < 1ms overhead per event

**Key Files:**
- `src/core/events.py` - EventBus, GameEvent, event builders
- `src/core/telemetry.py` - StatsTracker, GameTelemetry
- `src/core/game.py` - Integration and subscription setup
- `tests/test_event_system.py` - Comprehensive tests
- `docs/architecture/EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` - Design guide

---

**Next Steps:**
1. Add more event types as needed (quest events, status effects, etc.)
2. Create custom event subscribers for specific features
3. Phase 2: Add NATS publishing for multiplayer
4. ✅ Content event handlers in Python (replaced the Lua subscriber plan; ADR-018)

**Questions?** See `EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` for detailed patterns.
