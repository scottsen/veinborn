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
