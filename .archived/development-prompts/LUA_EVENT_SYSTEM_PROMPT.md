# Brogue Lua Event System - Phase 3

**Project:** Brogue Roguelike
**Phase:** 3 (Event Handlers)
**Prerequisites:** Phase 1 (Custom Actions) ✅, Phase 2 (AI Behaviors) ✅
**Estimated Effort:** 8-10 hours
**Date:** 2025-11-06

---

## Executive Summary

**Objective:** Enable Lua scripts to subscribe to and respond to game events, completing the Lua modding trilogy: Actions → AI → Events.

**Current State:**
- ✅ EventBus fully implemented (`src/core/events.py`) with 26 event types
- ✅ Lua runtime sandbox operational (Phase 1)
- ✅ GameContext API bridge functional (15+ methods)
- ✅ Event system integrated with Game loop
- ⚠️ **Missing:** Lua script event subscription capability

**Deliverable:** Lua scripts can subscribe to game events (entity_died, item_crafted, floor_changed, etc.) and execute custom handlers in response, enabling reactive behaviors, achievements, quests, and dynamic game systems.

**Impact:** Enables community-created content like achievement systems, quest tracking, dynamic difficulty adjustment, loot systems, and custom game modes—all without modifying core game code.

---

## Context & Background

### What We Have (Phases 1 & 2)

**Phase 1 - Custom Actions:**
- Lua scripts can define custom player actions (e.g., Fireball spell)
- `LuaRuntime` provides sandboxed execution (3s timeout)
- `GameContextAPI` exposes game state via `brogue.*` methods
- Example: `scripts/actions/fireball.lua` (150 lines, working)

**Phase 2 - AI Behaviors:**
- Lua scripts can define custom monster AI (e.g., Berserker behavior)
- Action descriptor pattern (Lua returns instructions, Python executes)
- Registry pattern (Python + Lua behaviors coexist)
- Examples: Berserker, Sniper, Summoner (working)

**EventBus Foundation (PR #12):**
- Pub/sub event system with 26 event types
- Python subscribers functional (e.g., `StatsTracker`)
- Type-safe event builders (`create_attack_event()`, etc.)
- **Already designed for Lua extension** (see `src/core/events.py` lines 330-367)

### What We Need (Phase 3)

**Lua Event Subscription:**
```lua
-- scripts/events/achievements.lua
function on_entity_died(event)
    if event.data.killer_id == "player_1" then
        player_kills = player_kills + 1

        if player_kills == 100 then
            brogue.add_message("🏆 Achievement: Centurion (100 kills)")
            brogue.unlock_achievement("centurion")
        end
    end
end

-- Register handler
brogue.event.subscribe("entity_died", "scripts/events/achievements.lua")
```

**Key Capabilities Unlocked:**
- **Achievements:** Track player milestones across sessions
- **Quests:** React to game events (kill boss, find item, reach floor)
- **Dynamic Systems:** Adjust difficulty based on player performance
- **Loot Tables:** Modify drop rates based on events
- **Story Events:** Trigger narrative based on player actions
- **Statistics:** Custom analytics and player profiling

---

## Architecture Design

### 1. EventBus Extension (Zero Refactoring)

The EventBus already has the architecture needed. We just add Lua subscription support:

**Current (Python only):**
```python
class EventBus:
    def __init__(self):
        self.subscribers: Dict[GameEventType, List[EventSubscriber]] = defaultdict(list)

    def publish(self, event: GameEvent):
        for subscriber in self.subscribers[event.event_type]:
            subscriber(event)  # Call Python function
```

**Phase 3 (Python + Lua):**
```python
class EventBus:
    def __init__(self):
        self.subscribers: Dict[GameEventType, List[EventSubscriber]] = defaultdict(list)
        self.lua_subscribers: Dict[GameEventType, List[LuaEventHandler]] = defaultdict(list)

    def publish(self, event: GameEvent):
        # Python subscribers (existing)
        for subscriber in self.subscribers[event.event_type]:
            subscriber(event)

        # Lua subscribers (NEW)
        for lua_handler in self.lua_subscribers.get(event.event_type, []):
            lua_handler.handle(event)
```

**Key Design Principle:** EventBus doesn't know about Lua. It just calls `LuaEventHandler.handle()`, which bridges to Lua.

---

### 2. LuaEventHandler Component (NEW)

**Purpose:** Bridge between EventBus (Python) and Lua event handlers.

**Responsibilities:**
- Load Lua event handler scripts
- Convert `GameEvent` to Lua table
- Call Lua handler function with event data
- Catch and log Lua errors (don't crash EventBus)
- Enforce timeout (3s per handler, same as actions)

**Interface:**
```python
class LuaEventHandler:
    """Wrapper for Lua event handler scripts."""

    def __init__(self, script_path: str, handler_function: str, lua_runtime: LuaRuntime):
        self.script_path = script_path
        self.handler_function = handler_function
        self.lua_runtime = lua_runtime
        self.lua_func = None  # Loaded from script

    def load(self) -> bool:
        """Load Lua script and find handler function."""
        # Load script, validate function exists
        pass

    def handle(self, event: GameEvent) -> None:
        """Execute Lua handler with event data."""
        try:
            # Convert event to Lua table
            event_table = {
                'type': event.event_type.value,
                'data': event.data,
                'timestamp': event.timestamp,
                'turn': event.turn,
            }

            # Call Lua function (with timeout)
            self.lua_runtime.call_function(
                self.lua_func,
                event_table,
                timeout_seconds=3.0
            )
        except LuaTimeoutError:
            logger.error(f"Lua event handler timeout: {self.script_path}")
        except Exception as e:
            logger.error(f"Lua event handler error: {e}", exc_info=True)
```

**Error Handling Philosophy:** Lua handler errors should NEVER crash the game. Log errors, continue publishing to other subscribers.

---

### 3. GameContext API Extensions

Add event subscription methods to `brogue.*` API:

```python
# In GameContextAPI._register_api()
event_table = self.lua.table()
event_table["subscribe"] = self._event_subscribe
event_table["unsubscribe"] = self._event_unsubscribe
event_table["get_types"] = self._event_get_types
brogue_table["event"] = event_table
```

**API Methods:**

#### `brogue.event.subscribe(event_type, script_path, handler_name)`
Subscribe Lua script to event type.

**Parameters:**
- `event_type` (string): Event type name (e.g., "entity_died", "item_crafted")
- `script_path` (string): Path to Lua script (e.g., "scripts/events/achievements.lua")
- `handler_name` (string): Function name in script (default: "on_<event_type>")

**Example:**
```lua
-- Subscribe achievements.lua to entity_died events
brogue.event.subscribe("entity_died", "scripts/events/achievements.lua", "on_entity_died")

-- Auto-infer handler name (looks for "on_entity_died" function)
brogue.event.subscribe("entity_died", "scripts/events/achievements.lua")
```

#### `brogue.event.unsubscribe(event_type, script_path)`
Unsubscribe script from event type.

#### `brogue.event.get_types()`
Get list of all available event types.

**Returns:** Lua table of event type strings

---

### 4. Event Handler Registry (NEW)

**Purpose:** Manage Lua event handler lifecycle and loading.

**File:** `src/core/events/lua_event_registry.py`

**Responsibilities:**
- Load event handlers from `scripts/events/` directory
- Track which scripts are subscribed to which events
- Prevent duplicate subscriptions
- Hot reload support (future: reload scripts without restart)

**Interface:**
```python
class LuaEventRegistry:
    """Registry for Lua event handler scripts."""

    def __init__(self, lua_runtime: LuaRuntime, event_bus: EventBus):
        self.lua_runtime = lua_runtime
        self.event_bus = event_bus
        self.handlers: Dict[str, LuaEventHandler] = {}  # script_path -> handler
        self.subscriptions: Dict[GameEventType, List[str]] = defaultdict(list)  # event -> scripts

    def register(
        self,
        event_type: GameEventType,
        script_path: str,
        handler_function: str
    ) -> bool:
        """Register Lua script as event handler."""
        # Create LuaEventHandler
        # Load script
        # Subscribe to EventBus
        # Track subscription
        pass

    def unregister(self, event_type: GameEventType, script_path: str) -> bool:
        """Unregister Lua event handler."""
        pass

    def get_handlers(self, event_type: GameEventType) -> List[LuaEventHandler]:
        """Get all Lua handlers for event type."""
        pass

    def load_from_directory(self, directory: str) -> int:
        """Auto-load all event handlers from directory."""
        # Scan scripts/events/*.lua
        # Look for special comment: -- @subscribe: entity_died
        # Auto-register handlers
        pass
```

---

### 5. Integration with Game Loop

**File:** `src/core/game.py`

**Changes Needed:**
```python
class Game:
    def __init__(self):
        # Existing
        self.event_bus = EventBus()
        self.lua_runtime = LuaRuntime()
        self.context_api = GameContextAPI(self.context, self.lua_runtime)

        # NEW
        self.lua_event_registry = LuaEventRegistry(self.lua_runtime, self.event_bus)

    def _initialize_subsystems(self):
        # Existing: subscribe Python handlers
        self._subscribe_event_handlers()

        # NEW: load Lua event handlers
        self._load_lua_event_handlers()

    def _load_lua_event_handlers(self):
        """Load Lua event handlers from scripts/events/ directory."""
        scripts_dir = Path(__file__).parent.parent / "scripts" / "events"
        if scripts_dir.exists():
            count = self.lua_event_registry.load_from_directory(str(scripts_dir))
            logger.info(f"Loaded {count} Lua event handlers")
```

**Philosophy:** Lua event handlers load automatically on game start, just like Python subscribers.

---

## Task Breakdown

### Task 1: Create LuaEventHandler Bridge (2 hours)

**File:** `src/core/events/lua_event_handler.py`

**Deliverables:**
1. `LuaEventHandler` class
   - `__init__(script_path, handler_function, lua_runtime)`
   - `load() -> bool` - Load Lua script and validate handler function
   - `handle(event: GameEvent) -> None` - Execute Lua handler with timeout
   - Error handling (catch all exceptions, log, don't crash)

2. Type conversion helpers
   - `_event_to_lua_table(event: GameEvent) -> dict` - Serialize event for Lua
   - Handle nested data structures
   - Preserve type information

3. Unit tests (15+ tests)
   - Test handler loading
   - Test event execution
   - Test timeout enforcement (handler runs >3s)
   - Test error handling (Lua runtime error, missing function)
   - Test event data conversion

**Success Criteria:**
- ✅ Handler loads Lua script successfully
- ✅ Handler executes Lua function with event data
- ✅ Timeout enforced (handlers can't hang)
- ✅ Errors logged, don't crash EventBus
- ✅ 15+ unit tests passing

**Example Handler Test:**
```python
def test_lua_event_handler_executes():
    """Test Lua handler receives and processes event."""
    lua_runtime = LuaRuntime()
    handler = LuaEventHandler(
        "scripts/events/test_handler.lua",
        "on_entity_died",
        lua_runtime
    )
    assert handler.load()

    event = GameEvent(
        event_type=GameEventType.ENTITY_DIED,
        data={'entity_id': 'goblin_1', 'killer_id': 'player_1'},
        turn=42
    )

    # Should not raise
    handler.handle(event)
```

---

### Task 2: Extend EventBus for Lua Subscribers (2 hours)

**File:** `src/core/events.py` (modify existing)

**Deliverables:**
1. Add Lua subscription support to EventBus
   - `lua_subscribers: Dict[GameEventType, List[LuaEventHandler]]` field
   - Modify `publish()` to call Lua handlers after Python subscribers
   - `subscribe_lua(event_type, handler: LuaEventHandler)` method
   - `unsubscribe_lua(event_type, handler: LuaEventHandler)` method

2. Preserve backward compatibility
   - All existing Python subscribers still work
   - Lua errors don't affect Python subscribers
   - EventBus tests still pass (no regressions)

3. Update tests (10+ new tests)
   - Test Lua subscription
   - Test Lua + Python subscribers coexist
   - Test Lua handler errors don't crash EventBus
   - Test event ordering (Python first, then Lua)

**Success Criteria:**
- ✅ EventBus supports both Python and Lua subscribers
- ✅ Lua handlers execute after Python subscribers
- ✅ Lua errors isolated (don't affect other subscribers)
- ✅ All existing EventBus tests pass (no regressions)
- ✅ 10+ new tests for Lua subscription

**Implementation Guidance:**
```python
# In EventBus.publish()
def publish(self, event: GameEvent) -> None:
    # Store in history
    if self.enable_history:
        self.event_history.append(event)

    # 1. Notify Python subscribers (EXISTING)
    for subscriber in self.subscribers.get(event.event_type, []):
        try:
            subscriber(event)
        except Exception as e:
            logger.error(f"Error in Python subscriber: {e}", exc_info=True)

    # 2. Notify Lua subscribers (NEW)
    for lua_handler in self.lua_subscribers.get(event.event_type, []):
        try:
            lua_handler.handle(event)
        except Exception as e:
            logger.error(f"Error in Lua subscriber: {e}", exc_info=True)
            # Continue to next handler!
```

---

### Task 3: Create LuaEventRegistry (2 hours)

**File:** `src/core/events/lua_event_registry.py`

**Deliverables:**
1. `LuaEventRegistry` class
   - Track Lua event handler subscriptions
   - Prevent duplicate subscriptions
   - Load handlers from directory
   - Auto-detect handler functions via decorators/comments

2. Auto-loading from `scripts/events/`
   - Scan directory for `*.lua` files
   - Parse special comment: `-- @subscribe: entity_died, item_crafted`
   - Auto-register handlers based on annotations

3. Unit tests (12+ tests)
   - Test handler registration
   - Test duplicate prevention
   - Test directory loading
   - Test annotation parsing
   - Test unregistration

**Success Criteria:**
- ✅ Registry loads Lua handlers from directory
- ✅ Duplicate subscriptions prevented
- ✅ Annotation-based registration works
- ✅ 12+ unit tests passing

**Annotation Format:**
```lua
-- @subscribe: entity_died
-- @handler: on_entity_died
function on_entity_died(event)
    -- Handler code
end
```

**Registry should parse comments and auto-register.**

---

### Task 4: Extend GameContextAPI with Event Methods (1.5 hours)

**File:** `src/core/scripting/game_context_api.py` (modify)

**Deliverables:**
1. Add `brogue.event.*` table with methods:
   - `subscribe(event_type, script_path, handler_name?)`
   - `unsubscribe(event_type, script_path)`
   - `get_types()` - Returns list of all event types
   - `emit(event_type, data)` - Manually emit event (for testing)

2. Integration with LuaEventRegistry
   - API methods delegate to registry
   - Handle errors gracefully
   - Validate event type names

3. Unit tests (10+ tests)
   - Test subscribe from Lua
   - Test unsubscribe
   - Test get_types
   - Test invalid event types
   - Test manual event emission

**Success Criteria:**
- ✅ Lua scripts can call `brogue.event.subscribe()`
- ✅ Event type validation works
- ✅ Integration with registry functional
- ✅ 10+ unit tests passing

**Example Usage:**
```lua
-- In a Lua action or initialization script
brogue.event.subscribe("entity_died", "scripts/events/achievements.lua")

-- Check available event types
local types = brogue.event.get_types()
for i = 1, #types do
    print("Event type:", types[i])
end
```

---

### Task 5: Create Example Lua Event Handlers (2 hours)

**Directory:** `scripts/events/`

**Deliverables:**
1. **Template:** `scripts/events/_template.lua` (~80 lines)
   - Complete template with all event types listed
   - Error handling patterns
   - State persistence example
   - Documentation

2. **Achievement System:** `scripts/events/achievements.lua` (~120 lines)
   - Track 5+ achievements:
     - Centurion (100 kills)
     - Explorer (descend 10 floors)
     - Hoarder (collect 1000 gold)
     - Craftsman (craft 50 items)
     - Survivor (survive 1000 turns)
   - Persist achievement state
   - Display unlock messages

3. **Quest Tracker:** `scripts/events/quest_tracker.lua` (~100 lines)
   - Track simple quest: "Kill 5 goblins"
   - Subscribe to entity_died events
   - Check if killed entity is goblin
   - Display progress messages
   - Reward on completion

4. **Loot Modifier:** `scripts/events/dynamic_loot.lua` (~90 lines)
   - Subscribe to entity_died events
   - Modify drop chances based on floor depth
   - Bonus loot on kill streaks
   - Display special loot messages

**Success Criteria:**
- ✅ Template covers all common patterns
- ✅ Achievements track correctly across events
- ✅ Quest tracker demonstrates multi-event coordination
- ✅ Loot modifier shows event-driven game modification
- ✅ All examples are well-documented

**Template Structure:**
```lua
-- scripts/events/_template.lua
--[[
Lua Event Handler Template

This template shows how to create event handlers for Brogue.

Event handlers react to game events like entity deaths, item crafting,
floor changes, etc. They enable achievements, quests, dynamic systems,
and custom game modes.

Usage:
1. Copy this template to scripts/events/your_handler.lua
2. Implement handler functions for events you care about
3. Add @subscribe annotation for auto-loading
4. Restart game to load handler

Event Types Available:
- entity_died, entity_damaged, entity_healed
- attack_resolved
- item_crafted, item_picked_up, item_dropped
- floor_changed, floor_generated
- turn_started, turn_ended
- game_started, game_over
- (see docs/EVENT_SYSTEM.md for complete list)
--]]

-- @subscribe: entity_died, item_crafted
-- @handler: on_entity_died, on_item_crafted

-- State persistence (survives across handler calls)
local state = {
    kills = 0,
    items_crafted = 0,
}

-- Handler for entity_died events
function on_entity_died(event)
    -- Event structure:
    -- event.type = "entity_died"
    -- event.data = {entity_id, entity_name, killer_id, cause}
    -- event.turn = current turn number
    -- event.timestamp = time in seconds

    if event.data.killer_id == "player_1" then
        state.kills = state.kills + 1
        brogue.add_message("Kills: " .. state.kills)
    end
end

-- Handler for item_crafted events
function on_item_crafted(event)
    state.items_crafted = state.items_crafted + 1
    brogue.add_message("Items crafted: " .. state.items_crafted)
end

-- Error handling example
function on_error_prone_event(event)
    -- Wrap risky code in pcall
    local success, err = pcall(function()
        -- Your code here
        local entity = brogue.get_entity(event.data.entity_id)
        -- ...
    end)

    if not success then
        brogue.add_message("Error in event handler: " .. err)
    end
end
```

---

### Task 6: Integration Tests (1.5 hours)

**File:** `tests/integration/test_lua_event_system.py`

**Deliverables:**
1. End-to-end integration tests (25+ tests)
   - Test event flow: Action → EventBus → Lua handler
   - Test achievement unlock on 100 kills
   - Test quest completion
   - Test multiple Lua handlers for same event
   - Test handler errors don't crash game
   - Test event data accuracy

2. Performance tests
   - Test 100+ events/second throughput
   - Test handler timeout enforcement
   - Test memory usage with many handlers

3. Edge cases
   - Handler throws error
   - Handler takes too long (timeout)
   - Invalid event type subscription
   - Handler tries to subscribe to itself
   - Circular event emission

**Success Criteria:**
- ✅ 25+ integration tests passing
- ✅ Full event flow validated (action → event → Lua)
- ✅ Achievement example works end-to-end
- ✅ Performance acceptable (<10ms overhead per event)
- ✅ All edge cases handled gracefully

**Example Integration Test:**
```python
def test_achievement_unlock_on_kills():
    """Test achievement system unlocks Centurion on 100 kills."""
    game = Game()
    game.start_new_game()

    # Load achievement handler
    game.lua_event_registry.register(
        GameEventType.ENTITY_DIED,
        "scripts/events/achievements.lua",
        "on_entity_died"
    )

    # Simulate 100 kills
    for i in range(100):
        game.spawn_monster("goblin", x=10+i, y=10)
        game.handle_player_action("attack", target_id=f"goblin_{i}")

    # Check achievement unlocked
    messages = game.get_recent_messages()
    assert any("Centurion" in msg for msg in messages)
    assert any("100 kills" in msg for msg in messages)
```

---

### Task 7: Documentation (1.5 hours)

**Deliverables:**

1. **Update:** `docs/LUA_API.md` (+150 lines)
   - Add Event API section
   - Document `brogue.event.*` methods
   - Event structure reference
   - Handler function signature
   - Error handling guidelines

2. **New:** `docs/LUA_EVENT_MODDING_GUIDE.md` (~600 lines)
   - Complete event system guide
   - Getting Started tutorial
   - Event handler lifecycle
   - Common patterns:
     - Achievements
     - Quest tracking
     - Dynamic difficulty
     - Loot tables
     - Statistics tracking
   - Advanced topics:
     - State persistence
     - Multi-event coordination
     - Performance optimization
   - Testing event handlers
   - Common pitfalls
   - Troubleshooting guide

3. **Update:** `docs/architecture/EVENT_SYSTEM.md` (+80 lines)
   - Add "Phase 3: Lua Integration" section
   - Document architecture decisions
   - Show code examples
   - Performance considerations

**Success Criteria:**
- ✅ API reference is complete and accurate
- ✅ Modding guide enables community contributions
- ✅ All examples are working and tested
- ✅ Architecture documented for maintainers

**Modding Guide Structure:**
```markdown
# Lua Event System Modding Guide

## Getting Started

### Your First Event Handler

Let's create a simple event handler that tracks player kills.

1. Create `scripts/events/my_tracker.lua`:

```lua
-- @subscribe: entity_died
function on_entity_died(event)
    if event.data.killer_id == "player_1" then
        brogue.add_message("You killed " .. event.data.entity_name .. "!")
    end
end
```

2. Start Brogue - handler loads automatically
3. Kill a monster - see your message!

### Understanding Events

Events are Lua tables with this structure:
... (continue with comprehensive guide)
```

---

## Testing Requirements

### Unit Tests (62+ tests total)

**Distribution:**
- `test_lua_event_handler.py` - 15 tests (handler loading, execution, errors)
- `test_event_bus_lua.py` - 10 tests (Lua subscription to EventBus)
- `test_lua_event_registry.py` - 12 tests (registry management)
- `test_game_context_api_events.py` - 10 tests (Lua API methods)
- `test_lua_event_examples.py` - 15 tests (example handler validation)

### Integration Tests (25+ tests)

**Coverage:**
- End-to-end event flow
- Achievement system
- Quest tracking
- Multiple handlers per event
- Error isolation
- Performance benchmarks

### Total Tests: 87+ new tests

**All tests must pass before PR submission.**

---

## Success Criteria

### Functional Requirements

- ✅ **F1:** Lua scripts can subscribe to game events via `brogue.event.subscribe()`
- ✅ **F2:** Event handlers execute when events are published
- ✅ **F3:** Handlers receive accurate event data (type, data, turn, timestamp)
- ✅ **F4:** Multiple handlers can subscribe to same event
- ✅ **F5:** Python and Lua subscribers coexist without interference
- ✅ **F6:** Handlers auto-load from `scripts/events/` directory
- ✅ **F7:** Annotation-based registration works (`@subscribe` comments)

### Non-Functional Requirements

- ✅ **NF1:** Handler timeout enforced (3s max per handler)
- ✅ **NF2:** Handler errors logged, don't crash game
- ✅ **NF3:** Event overhead <10ms per event with 5 handlers
- ✅ **NF4:** No memory leaks with long-running sessions
- ✅ **NF5:** Backward compatible (all existing tests pass)

### Quality Requirements

- ✅ **Q1:** 87+ tests passing (62 unit + 25 integration)
- ✅ **Q2:** Test coverage >85% for new code
- ✅ **Q3:** No type errors (mypy passes)
- ✅ **Q4:** All examples working and documented
- ✅ **Q5:** Comprehensive modding guide (600+ lines)
- ✅ **Q6:** Code follows existing patterns (type hints, logging, errors)

### Example Requirements

- ✅ **E1:** Achievement system tracks 5+ achievements
- ✅ **E2:** Quest tracker demonstrates multi-event coordination
- ✅ **E3:** Loot modifier shows event-driven game modification
- ✅ **E4:** Template covers all common patterns
- ✅ **E5:** All examples have inline documentation

---

## Technical Specifications

### Event Data Structure (Lua)

```lua
-- Event table passed to handler functions
event = {
    type = "entity_died",  -- Event type string
    data = {               -- Event-specific data
        entity_id = "goblin_1",
        entity_name = "Goblin Warrior",
        killer_id = "player_1",
        cause = "combat",
    },
    turn = 42,             -- Turn number when event occurred
    timestamp = 1699234567.123,  -- Unix timestamp (seconds)
}
```

### Handler Function Signature

```lua
-- Handler functions receive one argument: event table
-- @param event: Event table with type, data, turn, timestamp
-- @return: Nothing (handlers don't return values)
function on_<event_type>(event)
    -- Handler implementation
    -- Can call brogue.* API methods
    -- Can access persistent state (module-level variables)
    -- Should not run >3 seconds (timeout enforced)
end
```

### Timeout Enforcement

- Each handler gets 3 seconds max execution time
- Timeout prevents infinite loops / expensive operations
- Timeout exception logged, handler terminates
- Other handlers still execute (error isolation)

### State Persistence

```lua
-- Module-level variables persist across handler calls
local state = {
    kills = 0,
    achievements = {},
}

function on_entity_died(event)
    state.kills = state.kills + 1
    -- state.kills persists to next event!
end
```

**Note:** State does NOT persist across game sessions (yet). Future enhancement: save/load state.

---

## File Structure

### New Files

```
src/core/events/
├── lua_event_handler.py      # NEW (150 lines) - Lua handler bridge
└── lua_event_registry.py     # NEW (200 lines) - Handler registry

scripts/events/
├── _template.lua              # NEW (80 lines) - Template
├── achievements.lua           # NEW (120 lines) - Achievement system
├── quest_tracker.lua          # NEW (100 lines) - Quest example
└── dynamic_loot.lua           # NEW (90 lines) - Loot modifier

docs/
├── LUA_API.md                 # MODIFY (+150 lines) - Event API docs
├── LUA_EVENT_MODDING_GUIDE.md # NEW (600 lines) - Comprehensive guide
└── architecture/EVENT_SYSTEM.md  # MODIFY (+80 lines) - Architecture update

tests/
├── unit/
│   ├── test_lua_event_handler.py     # NEW (15 tests)
│   ├── test_event_bus_lua.py         # NEW (10 tests)
│   ├── test_lua_event_registry.py    # NEW (12 tests)
│   ├── test_game_context_api_events.py # NEW (10 tests)
│   └── test_lua_event_examples.py    # NEW (15 tests)
└── integration/
    └── test_lua_event_system.py      # NEW (25 tests)
```

### Modified Files

```
src/core/events.py            # Add Lua subscription (~30 lines added)
src/core/scripting/game_context_api.py  # Add event API (~60 lines added)
src/core/game.py              # Load Lua handlers (~20 lines added)
```

**Total New Code:** ~1,600 lines (implementation + examples)
**Total New Tests:** ~870 lines (87 tests)
**Total Documentation:** ~830 lines
**Total:** ~3,300 lines

---

## Implementation Guidance

### Order of Implementation

**Recommended sequence:**

1. **Task 1:** LuaEventHandler (core bridge) - Foundation
2. **Task 2:** EventBus extension - Enable Lua subscription
3. **Task 3:** LuaEventRegistry - Handler management
4. **Task 4:** GameContext API - Lua interface
5. **Task 5:** Example handlers - Demonstrate usage
6. **Task 6:** Integration tests - Validate end-to-end
7. **Task 7:** Documentation - Enable community

**Rationale:** Build foundation → add features → create examples → validate → document.

### Key Design Decisions

**1. Event Ordering: Python First, Then Lua**

**Rationale:** Python subscribers (like StatsTracker) update game state. Lua handlers react to state changes. Python → Lua ensures Lua sees updated state.

**Example:**
```
1. Player kills goblin
2. ENTITY_DIED event published
3. Python StatsTracker updates kills counter (state change)
4. Lua achievements.lua reads updated counter (sees current state)
```

**2. Error Isolation: Handler Errors Don't Crash Game**

**Rationale:** Community-created Lua scripts may have bugs. One broken handler shouldn't crash the game or prevent other handlers from running.

**Implementation:** Wrap each handler call in try/except, log errors, continue.

**3. Timeout: 3 Seconds Per Handler**

**Rationale:** Same as Lua actions. Prevents infinite loops, expensive operations, hanging game.

**4. Auto-Loading: Scan scripts/events/ on Game Start**

**Rationale:** User-friendly. No manual registration needed. Drop script in folder, it works.

**5. Annotation-Based Registration: `@subscribe` Comments**

**Rationale:** Declarative, easy to read, self-documenting. Alternative: convention-based (filename = event type).

**6. State Persistence: Module-Level Variables**

**Rationale:** Simple, familiar Lua pattern. Downsides: state doesn't persist across sessions (future enhancement).

### Common Pitfalls

**Pitfall 1: Forgetting Timeout**
```python
# ❌ BAD - no timeout, handler can hang
self.lua_func(event_table)

# ✅ GOOD - timeout enforced
self.lua_runtime.call_function(self.lua_func, event_table, timeout_seconds=3.0)
```

**Pitfall 2: Not Catching Lua Errors**
```python
# ❌ BAD - Lua error crashes EventBus
def handle(self, event):
    self.lua_func(event_table)

# ✅ GOOD - errors logged, don't crash
def handle(self, event):
    try:
        self.lua_func(event_table)
    except Exception as e:
        logger.error(f"Lua handler error: {e}", exc_info=True)
```

**Pitfall 3: Modifying Event Data in Lua**
```lua
-- ❌ BAD - modifying event data (undefined behavior)
function on_entity_died(event)
    event.data.entity_id = "modified"  -- Don't do this!
end

-- ✅ GOOD - read event data, don't modify
function on_entity_died(event)
    local entity_id = event.data.entity_id  -- Read-only
end
```

**Pitfall 4: Subscribing in Handler**
```lua
-- ❌ BAD - subscribing inside handler (infinite loop risk)
function on_entity_died(event)
    brogue.event.subscribe("entity_died", "scripts/events/achievements.lua")
end

-- ✅ GOOD - subscribe at module level or in init function
brogue.event.subscribe("entity_died", "scripts/events/achievements.lua")
```

---

## Event Type Reference

### All Available Events (26 types)

**Combat Events:**
- `attack_resolved` - Attack executed (before damage applied)
- `entity_damaged` - Entity took damage
- `entity_died` - Entity died
- `entity_healed` - Entity was healed

**Movement Events:**
- `entity_moved` - Any entity moved
- `player_moved` - Player moved (specific)

**Mining Events:**
- `ore_surveyed` - Ore examined
- `ore_mined` - Ore successfully mined
- `mining_started` - Mining action started
- `mining_completed` - Mining action completed

**Crafting Events:**
- `item_crafted` - Item successfully crafted
- `crafting_started` - Crafting started
- `crafting_failed` - Crafting failed (missing materials, etc.)

**Item Events:**
- `item_picked_up` - Item added to inventory
- `item_dropped` - Item removed from inventory
- `item_equipped` - Equipment worn
- `item_unequipped` - Equipment removed
- `item_used` - Consumable used

**Floor Events:**
- `floor_changed` - Player moved to different floor
- `floor_generated` - New floor created

**Turn Events:**
- `turn_started` - New turn began
- `turn_ended` - Turn completed

**Game Events:**
- `game_started` - New game started
- `game_over` - Game ended (victory or death)

**See:** `src/core/events.py` (lines 27-74) for definitive list and data structures.

---

## Example Use Cases

### Use Case 1: Achievement System

**Goal:** Track player achievements like "Kill 100 monsters"

**Events Used:** `entity_died`

**Implementation:**
```lua
-- @subscribe: entity_died
local achievements = {
    centurion = false,  -- 100 kills
    slayer = false,     -- 500 kills
}
local kills = 0

function on_entity_died(event)
    if event.data.killer_id == "player_1" then
        kills = kills + 1

        if kills == 100 and not achievements.centurion then
            brogue.add_message("🏆 Achievement: Centurion (100 kills)")
            achievements.centurion = true
        end

        if kills == 500 and not achievements.slayer then
            brogue.add_message("🏆 Achievement: Slayer (500 kills)")
            achievements.slayer = true
        end
    end
end
```

---

### Use Case 2: Quest Tracking

**Goal:** Track quest progress like "Kill 5 goblins"

**Events Used:** `entity_died`

**Implementation:**
```lua
-- @subscribe: entity_died
local quest = {
    name = "Goblin Slayer",
    description = "Kill 5 goblins",
    target = 5,
    progress = 0,
    completed = false,
}

function on_entity_died(event)
    if quest.completed then return end

    if event.data.entity_name:find("Goblin") and event.data.killer_id == "player_1" then
        quest.progress = quest.progress + 1

        brogue.add_message(string.format("Quest: %d/%d goblins killed",
                                         quest.progress, quest.target))

        if quest.progress >= quest.target then
            brogue.add_message("🎯 Quest Complete: " .. quest.name)
            brogue.add_message("Reward: +100 gold")
            brogue.modify_stat("player_1", "gold", 100)
            quest.completed = true
        end
    end
end
```

---

### Use Case 3: Dynamic Difficulty

**Goal:** Adjust monster stats based on player performance

**Events Used:** `entity_died`, `floor_changed`

**Implementation:**
```lua
-- @subscribe: entity_died, floor_changed
local stats = {
    player_deaths = 0,
    monster_deaths = 0,
    current_floor = 1,
}

function on_entity_died(event)
    if event.data.entity_id == "player_1" then
        stats.player_deaths = stats.player_deaths + 1
    else
        stats.monster_deaths = stats.monster_deaths + 1
    end

    adjust_difficulty()
end

function on_floor_changed(event)
    stats.current_floor = event.data.to_floor
    adjust_difficulty()
end

function adjust_difficulty()
    local death_ratio = stats.player_deaths / math.max(1, stats.monster_deaths)

    if death_ratio > 0.5 then
        -- Player dying too much - reduce difficulty
        brogue.add_message("[Difficulty adjusted: Easier]")
        -- Could reduce monster stats, increase player stats, etc.
    elseif death_ratio < 0.1 and stats.current_floor > 3 then
        -- Player dominating - increase difficulty
        brogue.add_message("[Difficulty adjusted: Harder]")
        -- Could increase monster stats, reduce loot, etc.
    end
end
```

---

### Use Case 4: Statistics Dashboard

**Goal:** Track detailed player statistics

**Events Used:** Multiple (attack_resolved, item_crafted, ore_mined, etc.)

**Implementation:**
```lua
-- @subscribe: attack_resolved, item_crafted, ore_mined, floor_changed
local stats = {
    attacks = 0,
    damage_dealt = 0,
    items_crafted = 0,
    ore_mined = 0,
    deepest_floor = 1,
}

function on_attack_resolved(event)
    stats.attacks = stats.attacks + 1
    stats.damage_dealt = stats.damage_dealt + event.data.damage
end

function on_item_crafted(event)
    stats.items_crafted = stats.items_crafted + 1
end

function on_ore_mined(event)
    stats.ore_mined = stats.ore_mined + 1
end

function on_floor_changed(event)
    stats.deepest_floor = math.max(stats.deepest_floor, event.data.to_floor)
end

-- Call this to display stats
function show_stats()
    brogue.add_message("=== Statistics ===")
    brogue.add_message(string.format("Attacks: %d", stats.attacks))
    brogue.add_message(string.format("Damage dealt: %d", stats.damage_dealt))
    brogue.add_message(string.format("Items crafted: %d", stats.items_crafted))
    brogue.add_message(string.format("Ore mined: %d", stats.ore_mined))
    brogue.add_message(string.format("Deepest floor: %d", stats.deepest_floor))
end
```

---

## Performance Considerations

### Expected Overhead

**Baseline (no Lua handlers):**
- EventBus overhead: <0.1ms per event
- Python subscribers: ~0.5ms per subscriber

**With Lua handlers:**
- Lua handler call: ~2-5ms per handler
- Event serialization: ~0.1ms per event
- Total overhead (5 handlers): ~10-25ms per event

**Acceptable Performance:**
- Target: <10ms overhead per event with 5 handlers
- Events per turn: 5-20 typical
- Total overhead per turn: 50-200ms (acceptable for turn-based game)

### Optimization Tips

**1. Keep Handlers Fast**
```lua
-- ❌ BAD - expensive operation
function on_entity_died(event)
    for i = 1, 1000000 do
        -- Don't do expensive loops
    end
end

-- ✅ GOOD - minimal work
function on_entity_died(event)
    if event.data.killer_id == "player_1" then
        kills = kills + 1
    end
end
```

**2. Filter Early**
```lua
-- ✅ GOOD - early return if not relevant
function on_entity_died(event)
    if event.data.killer_id ~= "player_1" then
        return  -- Not a player kill, ignore
    end

    -- Process player kill
end
```

**3. Batch Updates**
```lua
-- ❌ BAD - update UI every event
function on_entity_died(event)
    show_stats()  -- Expensive!
end

-- ✅ GOOD - update UI on turn_ended
function on_turn_ended(event)
    if event.turn % 10 == 0 then
        show_stats()  -- Only every 10 turns
    end
end
```

---

## Troubleshooting

### Problem: Handler Not Called

**Symptoms:** Event fires, but Lua handler doesn't execute.

**Causes:**
1. Handler not subscribed correctly
2. Event type name mismatch
3. Handler function name wrong
4. Script has syntax error (failed to load)

**Solution:**
```lua
-- Check subscription
brogue.event.subscribe("entity_died", "scripts/events/my_handler.lua", "on_entity_died")

-- Check function name matches
function on_entity_died(event)  -- Must match handler_name parameter
    -- ...
end

-- Check for syntax errors in logs
```

---

### Problem: Handler Timeout

**Symptoms:** Handler stops mid-execution, timeout error in logs.

**Cause:** Handler takes >3 seconds.

**Solution:** Optimize handler code:
```lua
-- ❌ BAD - infinite loop
function on_entity_died(event)
    while true do end  -- Timeout!
end

-- ✅ GOOD - fast execution
function on_entity_died(event)
    kills = kills + 1  -- Quick!
end
```

---

### Problem: Event Data Missing

**Symptoms:** `event.data.some_field` is nil.

**Cause:** Event type has different data structure.

**Solution:** Check event documentation:
```lua
function on_entity_died(event)
    -- Check if field exists before using
    if event.data.killer_id then
        -- Use field
    else
        brogue.add_message("No killer_id in event")
    end
end
```

---

## Quality Checklist

Before submitting PR, verify:

### Code Quality
- [ ] All new code has type hints
- [ ] All functions have docstrings
- [ ] Error handling follows existing patterns
- [ ] Logging uses appropriate levels (debug/info/error)
- [ ] No hardcoded paths (use config/constants)
- [ ] Follows existing code style (Black formatting)

### Testing
- [ ] 87+ tests passing (62 unit + 25 integration)
- [ ] Test coverage >85% for new code
- [ ] All examples tested and working
- [ ] Edge cases covered (errors, timeouts, invalid inputs)
- [ ] Performance benchmarks meet targets (<10ms overhead)

### Documentation
- [ ] LUA_API.md updated with event methods
- [ ] LUA_EVENT_MODDING_GUIDE.md complete and accurate
- [ ] EVENT_SYSTEM.md architecture updated
- [ ] All examples have inline documentation
- [ ] Troubleshooting guide covers common issues

### Compatibility
- [ ] All existing tests pass (no regressions)
- [ ] Python subscribers still work
- [ ] Backward compatible with Phases 1 & 2
- [ ] No breaking changes to existing APIs

### Examples
- [ ] Template covers all patterns
- [ ] Achievement system works end-to-end
- [ ] Quest tracker demonstrates multi-event
- [ ] Loot modifier shows dynamic modification
- [ ] All examples are polished and commented

---

## Deliverable Checklist

### Implementation
- [ ] LuaEventHandler class (150 lines)
- [ ] EventBus Lua extension (~30 lines)
- [ ] LuaEventRegistry class (200 lines)
- [ ] GameContextAPI event methods (~60 lines)
- [ ] Game integration (~20 lines)

### Examples
- [ ] Template (_template.lua, 80 lines)
- [ ] Achievement system (achievements.lua, 120 lines)
- [ ] Quest tracker (quest_tracker.lua, 100 lines)
- [ ] Loot modifier (dynamic_loot.lua, 90 lines)

### Tests
- [ ] 15 tests: test_lua_event_handler.py
- [ ] 10 tests: test_event_bus_lua.py
- [ ] 12 tests: test_lua_event_registry.py
- [ ] 10 tests: test_game_context_api_events.py
- [ ] 15 tests: test_lua_event_examples.py
- [ ] 25 tests: test_lua_event_system.py (integration)

### Documentation
- [ ] LUA_API.md update (+150 lines)
- [ ] LUA_EVENT_MODDING_GUIDE.md (600 lines)
- [ ] EVENT_SYSTEM.md update (+80 lines)

---

## Success Definition

**Phase 3 is complete when:**

1. ✅ Lua scripts can subscribe to game events
2. ✅ Event handlers execute reliably when events fire
3. ✅ Achievement system works end-to-end (example)
4. ✅ Quest tracker works end-to-end (example)
5. ✅ 87+ tests passing (no regressions)
6. ✅ Documentation enables community modding
7. ✅ Code quality matches existing standards
8. ✅ Performance acceptable (<10ms overhead)

**Impact:** Brogue has a complete Lua modding platform enabling community-created achievements, quests, dynamic systems, and custom game modes.

---

## Related Resources

**Existing Code:**
- `src/core/events.py` - EventBus implementation (lines 330-367 show Lua integration design)
- `src/core/scripting/lua_runtime.py` - Lua sandbox and timeout enforcement
- `src/core/scripting/game_context_api.py` - Existing API bridge pattern
- `scripts/actions/fireball.lua` - Example Lua action (reference pattern)
- `scripts/ai/berserker.lua` - Example Lua AI (reference pattern)

**Documentation:**
- `docs/architecture/EVENT_SYSTEM.md` - Event system architecture
- `docs/architecture/EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` - Event design patterns
- `docs/LUA_API.md` - Existing Lua API reference
- `docs/LUA_AI_MODDING_GUIDE.md` - AI modding guide (pattern to follow)

**Prior Work:**
- PR #12 - EventBus implementation
- PR #16 - Lua Actions (Phase 1)
- PR #17 - Lua AI Behaviors (Phase 2)

---

## Questions & Support

If anything is unclear:

1. **Check existing code:** Phases 1 & 2 provide excellent patterns
2. **Read docs:** EVENT_SYSTEM.md has detailed architecture
3. **Ask questions:** Open GitHub issue or comment on PR

**Philosophy:** Follow existing patterns. If Phase 1/2 did it a certain way (error handling, testing, documentation), Phase 3 should do the same.

---

**Ready to Begin!**

Start with Task 1 (LuaEventHandler bridge), build the foundation, then layer on features. Follow the existing patterns from Phases 1 & 2, and you'll create an excellent Phase 3 implementation.

Good luck! 🚀
