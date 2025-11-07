# Brogue Lua API Reference

This document describes the Lua API available for scripting custom actions in Brogue.

## Overview

Brogue exposes game functionality through the global `brogue` table in Lua. All game state access and modification goes through this API.

## API Methods

### Entity Queries

#### `brogue.get_player()`
Returns the player entity as a Lua table.

**Returns:** Entity table with fields:
- `id` (string): Entity ID
- `name` (string): Entity name
- `entity_type` (string): Type ("PLAYER", "MONSTER", etc.)
- `x`, `y` (number): Position
- `hp`, `max_hp` (number): Hit points
- `attack`, `defense` (number): Combat stats
- `is_alive` (boolean): Alive status
- `stats` (table): Custom stats (e.g., `mana`)

**Example:**
```lua
local player = brogue.get_player()
print("Player at", player.x, player.y)
print("HP:", player.hp, "/", player.max_hp)
```

#### `brogue.get_entity(entity_id)`
Get entity by ID.

**Parameters:**
- `entity_id` (string): Entity ID to look up

**Returns:** Entity table or `nil` if not found

#### `brogue.get_entity_at(x, y)`
Get entity at position.

**Parameters:**
- `x`, `y` (number): Coordinates

**Returns:** Entity table or `nil`

#### `brogue.get_entities_in_range(x, y, radius)`
Get all entities within radius of position.

**Parameters:**
- `x`, `y` (number): Center coordinates
- `radius` (number): Search radius

**Returns:** Lua table (1-indexed array) of entity tables

**Example:**
```lua
local targets = brogue.get_entities_in_range(10, 10, 5)
for i = 1, #targets do
    local entity = targets[i]
    print("Found:", entity.name)
end
```

#### `brogue.get_entities_by_type(type_name)`
Get all entities of a specific type.

**Parameters:**
- `type_name` (string): Entity type ("MONSTER", "PLAYER", "ITEM", etc.)

**Returns:** Lua table of entities

### Map Queries

#### `brogue.is_walkable(x, y)`
Check if position is walkable.

**Returns:** `true` if walkable, `false` otherwise

#### `brogue.in_bounds(x, y)`
Check if position is within map bounds.

**Returns:** `true` if in bounds, `false` otherwise

### Game State

#### `brogue.add_message(message)`
Add message to game log.

**Parameters:**
- `message` (string): Message text

#### `brogue.get_turn_count()`
Get current turn number.

**Returns:** (number) Turn count

#### `brogue.get_floor()`
Get current floor number.

**Returns:** (number) Floor number

### Entity Manipulation

#### `brogue.modify_stat(entity_id, stat_name, delta)`
Modify an entity's stat by a delta.

**Parameters:**
- `entity_id` (string): Entity ID
- `stat_name` (string): Stat name ("hp", "mana", "attack", etc.)
- `delta` (number): Amount to add (can be negative)

**Returns:** `true` if successful

**Example:**
```lua
-- Deduct 10 mana
brogue.modify_stat("player_1", "mana", -10)

-- Deal 15 damage
brogue.modify_stat("monster_1", "hp", -15)
```

#### `brogue.deal_damage(entity_id, amount)`
Deal damage to entity (respects defense).

**Returns:** (number) Actual damage dealt

#### `brogue.heal(entity_id, amount)`
Heal entity.

**Returns:** (number) Actual amount healed

#### `brogue.is_alive(entity_id)`
Check if entity is alive.

**Returns:** `true` if alive, `false` otherwise

## AI Behavior API

Custom AI behaviors control monster decision-making during gameplay. AI behaviors are defined in Lua scripts and registered with the AI system.

### AI Behavior Structure

```lua
-- scripts/ai/my_behavior.lua

function update(monster, config)
    -- Decision logic here

    return {
        action = "attack",  -- Action type
        target_id = "player_1"  -- Optional parameters
    }
end
```

### AI Helper Methods

#### `brogue.ai.get_target(monster_id)`
Get monster's current target (usually player).

**Parameters:**
- `monster_id` (string): Monster entity ID

**Returns:** Target entity table or `nil`

#### `brogue.ai.is_adjacent(monster_id, target_id)`
Check if monster is adjacent to target.

**Parameters:**
- `monster_id` (string): Monster entity ID
- `target_id` (string): Target entity ID

**Returns:** `true` if adjacent (within 1 tile), `false` otherwise

#### `brogue.ai.distance_to(monster_id, target_id)`
Calculate Manhattan distance between entities.

**Parameters:**
- `monster_id` (string): Monster entity ID
- `target_id` (string): Target entity ID

**Returns:** (number) Manhattan distance (|dx| + |dy|)

**Example:**
```lua
local distance = brogue.ai.distance_to(monster.id, player.id)
if distance <= 5 then
    -- Player is within 5 tiles
end
```

#### `brogue.ai.get_config(ai_type)`
Get behavior configuration from YAML.

**Parameters:**
- `ai_type` (string): AI behavior type name

**Returns:** Configuration table

### Action Descriptors

AI behaviors return action descriptors to control monster actions:

#### Attack Action
```lua
return {
    action = "attack",
    target_id = "player_1"
}
```

#### Move Towards
```lua
return {
    action = "move_towards",
    target_id = "player_1"
}
```

#### Flee From
```lua
return {
    action = "flee_from",
    target_id = "player_1"
}
```

#### Wander
```lua
return {action = "wander"}
```

#### Idle (do nothing)
```lua
return {action = "idle"}
```

### Configuration

Define behavior configuration in `data/balance/ai_behaviors.yaml`:

```yaml
behaviors:
  my_behavior:
    description: "Custom behavior description"
    chase_range: 10
    custom_param: 42
```

Access in Lua:
```lua
function update(monster, config)
    local range = config.chase_range  -- 10
    local param = config.custom_param  -- 42
end
```

### Complete AI Example

See `scripts/ai/berserker.lua` for a complete working example.

## Action Script Structure

Every Lua action script must define two functions:

### `validate(actor_id, params)`
Check if action can be executed.

**Parameters:**
- `actor_id` (string): ID of entity performing action
- `params` (table): Action parameters

**Returns:** `true` if valid, `false` otherwise

**Example:**
```lua
function validate(actor_id, params)
    local player = brogue.get_player()
    if player.stats.mana < 10 then
        brogue.add_message("Not enough mana!")
        return false
    end
    return true
end
```

### `execute(actor_id, params)`
Execute the action.

**Returns:** Outcome table with fields:
- `success` (boolean): Did action succeed?
- `took_turn` (boolean): Does this consume a turn?
- `messages` (table): Array of message strings
- `events` (table): Array of event tables

**Example:**
```lua
function execute(actor_id, params)
    brogue.add_message("Action executed!")
    return {
        success = true,
        took_turn = true,
        messages = {},
        events = {}
    }
end
```

## Event Format

Events are Lua tables that describe what happened during action execution.

**Common event types:**
- `damage`: Damage dealt
- `heal`: Healing applied
- `death`: Entity died
- `spell_cast`: Spell was cast

**Example event:**
```lua
{
    type = "damage",
    source = "fireball",
    target_id = "monster_1",
    target_name = "Goblin",
    amount = 15
}
```

## Complete Example

See `scripts/actions/fireball.lua` for a complete working example of a Lua action.

## Sandboxing

For security, the following Lua features are disabled:
- File I/O (`io.*`)
- OS access (`os.*`)
- Dynamic code loading (`load`, `loadfile`, `dofile`)
- Debug library (`debug.*`)
- Package management (`require`, `package.*`)

Available libraries:
- `math.*` - Mathematical functions
- `string.*` - String manipulation
- `table.*` - Table operations

---

# Event System API (Phase 3)

The Event System allows Lua scripts to subscribe to and respond to game events, enabling achievements, quests, dynamic systems, and custom game modes.

## Event Subscription

### brogue.event.subscribe(event_type, script_path, [handler_function])

Subscribe a Lua script to a game event.

**Parameters:**
- `event_type` (string): Event type to subscribe to (e.g., `"entity_died"`)
- `script_path` (string): Path to Lua script containing handler
- `handler_function` (string, optional): Handler function name (default: `"on_<event_type>"`)

**Returns:** `true` if successful, `false` otherwise

**Example:**
```lua
-- Subscribe achievements.lua to entity_died events
brogue.event.subscribe("entity_died", "scripts/events/achievements.lua")

-- Explicitly specify handler function name
brogue.event.subscribe("entity_died", "scripts/events/achievements.lua", "on_entity_died")
```

### brogue.event.unsubscribe(event_type, script_path)

Unsubscribe a script from an event type.

**Parameters:**
- `event_type` (string): Event type to unsubscribe from
- `script_path` (string): Path to script to unsubscribe

**Returns:** `true` if successful, `false` otherwise

**Example:**
```lua
brogue.event.unsubscribe("entity_died", "scripts/events/achievements.lua")
```

### brogue.event.get_types()

Get list of all available event types.

**Returns:** Lua table (1-indexed) of event type strings

**Example:**
```lua
local types = brogue.event.get_types()
for i = 1, #types do
    print("Event type:", types[i])
end
```

### brogue.event.emit(event_type, data)

Manually emit an event (for testing/debugging).

**Parameters:**
- `event_type` (string): Event type name
- `data` (table): Event data

**Returns:** `true` if successful, `false` otherwise

**Example:**
```lua
brogue.event.emit("entity_died", {
    entity_id = "goblin_1",
    entity_name = "Goblin",
    killer_id = "player_1",
    cause = "combat"
})
```

## Event Handler Structure

Event handlers receive an event table with the following structure:

```lua
event = {
    type = "entity_died",          -- Event type string
    data = {                        -- Event-specific data
        entity_id = "goblin_1",
        entity_name = "Goblin",
        killer_id = "player_1",
        cause = "combat",
    },
    turn = 42,                      -- Turn number when event occurred
    timestamp = 1699234567.123,     -- Unix timestamp (seconds)
}
```

## Available Event Types

**Combat Events:**
- `attack_resolved` - Attack executed
- `entity_damaged` - Entity took damage
- `entity_died` - Entity died
- `entity_healed` - Entity was healed

**Movement Events:**
- `entity_moved` - Any entity moved
- `player_moved` - Player moved specifically

**Mining Events:**
- `ore_surveyed` - Ore examined
- `ore_mined` - Ore successfully mined
- `mining_started` - Mining action started
- `mining_completed` - Mining action completed

**Crafting Events:**
- `item_crafted` - Item successfully crafted
- `crafting_started` - Crafting started
- `crafting_failed` - Crafting failed

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
- `game_over` - Game ended

## Auto-Loading with Annotations

Event handlers can be auto-loaded using annotation comments:

```lua
-- @subscribe: entity_died, item_crafted
-- @handler: on_entity_died, on_item_crafted

function on_entity_died(event)
    -- Handler implementation
end

function on_item_crafted(event)
    -- Handler implementation
end
```

Place scripts in `scripts/events/` directory for automatic loading on game start.

## Example Event Handlers

### Simple Kill Counter

```lua
-- scripts/events/kill_counter.lua
-- @subscribe: entity_died

local kills = 0

function on_entity_died(event)
    if event.data.killer_id == "player_1" then
        kills = kills + 1
        brogue.add_message("Total kills: " .. kills)
    end
end
```

### Achievement System

```lua
-- scripts/events/achievements.lua
-- @subscribe: entity_died

local achievements = {
    centurion = {unlocked = false, target = 100}
}
local kills = 0

function on_entity_died(event)
    if event.data.killer_id == "player_1" then
        kills = kills + 1

        if kills == 100 and not achievements.centurion.unlocked then
            achievements.centurion.unlocked = true
            brogue.add_message("Achievement Unlocked: Centurion (100 kills)")
        end
    end
end
```

### Quest Tracker

```lua
-- scripts/events/quest.lua
-- @subscribe: entity_died

local quest = {
    active = true,
    progress = 0,
    target = 5,
    name = "Goblin Slayer"
}

function on_entity_died(event)
    if not quest.active then return end

    local entity_name = event.data.entity_name or ""
    if string.find(string.lower(entity_name), "goblin") then
        quest.progress = quest.progress + 1
        brogue.add_message(string.format(
            "Quest: %s [%d/%d]",
            quest.name,
            quest.progress,
            quest.target
        ))

        if quest.progress >= quest.target then
            brogue.add_message("Quest Complete!")
            quest.active = false
        end
    end
end
```

## Best Practices

1. **Early Return:** Check conditions early and return if event doesn't apply
```lua
function on_entity_died(event)
    if event.data.killer_id ~= "player_1" then
        return  -- Not a player kill, ignore
    end
    -- Process player kill
end
```

2. **Error Handling:** Use pcall for risky operations
```lua
function on_entity_died(event)
    local success, err = pcall(function()
        -- Risky code here
    end)
    if not success then
        brogue.add_message("Error: " .. err)
    end
end
```

3. **State Persistence:** Use module-level variables for state
```lua
-- State persists across handler calls (same session)
local state = {
    kills = 0,
    achievements = {}
}

function on_entity_died(event)
    state.kills = state.kills + 1
end
```

4. **Performance:** Keep handlers fast (<3 seconds)
- Avoid expensive loops
- Filter early
- Batch UI updates

## Limitations

- Handler timeout: 3 seconds per handler
- State does NOT persist across game sessions (future enhancement)
- Cannot modify event data
- Cannot create new events from handlers (use `brogue.event.emit()` for testing)

## Testing Lua Handlers

### Accessing Internal State in Tests

Lua event handlers use local variables for proper encapsulation. For testing purposes, handlers should expose getter functions to access internal state:

**In your Lua handler:**
```lua
-- Private state (encapsulated)
local state = {
    kill_count = 0,
    achievements_unlocked = {}
}

function on_entity_died(event)
    state.kill_count = state.kill_count + 1
end

-- Export state for testing
function get_state()
    return state
end
```

**In Python tests:**
```python
# Load and execute handler
lua_runtime.execute_file("scripts/events/my_handler.lua")

# Access state via export function
get_state = lua_runtime.get_global("get_state")
state = get_state()

# Verify state
assert state['kill_count'] == 5
```

### Testing Best Practices

1. **Always use export functions** - Don't try to access local variables directly from Python (impossible by design)

2. **Name export functions consistently** - Use `get_*()` pattern (e.g., `get_stats()`, `get_quests()`, `get_loot_state()`)

3. **Keep exports simple** - Return the raw state table or a shallow copy

4. **Document in comments** - Mark export functions clearly:
```lua
--- Export state for testing
-- @return table Handler state
function get_state()
    return state
end
```

For more details, see `docs/LUA_EVENT_MODDING_GUIDE.md`.
