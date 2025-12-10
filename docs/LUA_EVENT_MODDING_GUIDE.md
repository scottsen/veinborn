# Lua Event System Modding Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Event Handler Basics](#event-handler-basics)
4. [Available Events](#available-events)
5. [Common Patterns](#common-patterns)
6. [Advanced Topics](#advanced-topics)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

The Veinborn Lua Event System allows you to create custom game modifications by responding to game events. This enables:

- **Achievements:** Track player milestones
- **Quests:** Create objectives and rewards
- **Dynamic Difficulty:** Adjust game based on player performance
- **Loot Systems:** Modify drop rates
- **Custom Game Modes:** Create entirely new experiences

## Getting Started

### Your First Event Handler

Let's create a simple event handler that tracks player kills.

**Step 1:** Create `scripts/events/my_tracker.lua`

```lua
-- @subscribe: entity_died
function on_entity_died(event)
    if event.data.killer_id == "player_1" then
        veinborn.add_message("You killed " .. event.data.entity_name .. "!")
    end
end
```

**Step 2:** Start Veinborn - the handler loads automatically

**Step 3:** Kill a monster - see your message!

### How It Works

1. The `@subscribe` annotation tells Veinborn to load this handler
2. The game calls `on_entity_died()` whenever an entity dies
3. Your code checks if the player was the killer
4. If so, displays a message

## Event Handler Basics

### Event Structure

Every event handler receives an event table:

```lua
event = {
    type = "entity_died",          -- Event type string
    data = {                        -- Event-specific data
        entity_id = "goblin_1",
        entity_name = "Goblin",
        killer_id = "player_1",
        cause = "combat",
    },
    turn = 42,                      -- Current turn number
    timestamp = 1699234567.123,     -- Unix timestamp
}
```

### Handler Function Signature

```lua
-- Handler functions receive one argument: the event
function on_<event_type>(event)
    -- Your code here
    -- Can call veinborn.* API methods
    -- Can access module-level state
    -- Must complete within 3 seconds
end
```

### Auto-Loading Annotations

Use annotations to auto-register handlers:

```lua
-- @subscribe: entity_died, item_crafted
-- @handler: on_entity_died, on_item_crafted

function on_entity_died(event)
    -- ...
end

function on_item_crafted(event)
    -- ...
end
```

**Rules:**
- Place scripts in `scripts/events/` directory
- One `@subscribe` line per script
- Handler names default to `on_<event_type>` if not specified
- Files starting with `_` are ignored (templates)

## Available Events

### Combat Events

**entity_died** - Entity was killed
```lua
event.data = {
    entity_id = "goblin_1",
    entity_name = "Goblin Warrior",
    killer_id = "player_1",    -- or nil if environment
    cause = "combat"            -- "combat", "trap", "poison", etc.
}
```

**entity_damaged** - Entity took damage
```lua
event.data = {
    entity_id = "player_1",
    amount = 10,
    source = "goblin_1"
}
```

**entity_healed** - Entity was healed
```lua
event.data = {
    entity_id = "player_1",
    amount = 20,
    source = "potion"
}
```

**attack_resolved** - Attack completed
```lua
event.data = {
    attacker_id = "player_1",
    defender_id = "goblin_1",
    damage = 15,
    killed = true
}
```

### Item Events

**item_crafted** - Item successfully crafted
```lua
event.data = {
    item_id = "sword_1",
    item_name = "Iron Sword",
    recipe_id = "iron_sword_recipe",
    crafter_id = "player_1",
    stats = {attack = 10, durability = 100}
}
```

**item_picked_up** - Item added to inventory
**item_dropped** - Item removed from inventory
**item_used** - Consumable item used

### Floor Events

**floor_changed** - Player moved between floors
```lua
event.data = {
    from_floor = 5,
    to_floor = 6,
    player_id = "player_1"
}
```

**floor_generated** - New floor created

### Turn Events

**turn_started** - New turn beginning
**turn_ended** - Turn completed

### Game Events

**game_started** - New game began
**game_over** - Game ended (victory or death)

## Common Patterns

### Pattern 1: Achievement System

Track player milestones:

```lua
-- @subscribe: entity_died
local achievements = {
    centurion = {unlocked = false, kills_needed = 100}
}
local kills = 0

function on_entity_died(event)
    if event.data.killer_id ~= "player_1" then return end

    kills = kills + 1

    if kills == 100 and not achievements.centurion.unlocked then
        achievements.centurion.unlocked = true
        veinborn.add_message("Achievement Unlocked: Centurion (100 kills)!")
    end
end
```

### Pattern 2: Quest Tracking

Track objectives across events:

```lua
-- @subscribe: entity_died
local quest = {
    name = "Goblin Slayer",
    description = "Kill 5 goblins",
    active = true,
    progress = 0,
    target = 5
}

function on_entity_died(event)
    if not quest.active then return end
    if event.data.killer_id ~= "player_1" then return end

    local entity_name = string.lower(event.data.entity_name or "")
    if string.find(entity_name, "goblin") then
        quest.progress = quest.progress + 1
        veinborn.add_message(string.format(
            "Quest: %s [%d/%d]",
            quest.name,
            quest.progress,
            quest.target
        ))

        if quest.progress >= quest.target then
            veinborn.add_message("Quest Complete: " .. quest.name)
            quest.active = false
        end
    end
end
```

### Pattern 3: Dynamic Difficulty

Adjust game based on performance:

```lua
-- @subscribe: entity_died, turn_ended
local stats = {
    player_deaths = 0,
    monster_kills = 0
}

function on_entity_died(event)
    if event.data.entity_id == "player_1" then
        stats.player_deaths = stats.player_deaths + 1
    elseif event.data.killer_id == "player_1" then
        stats.monster_kills = stats.monster_kills + 1
    end
end

function on_turn_ended(event)
    -- Check difficulty every 100 turns
    if event.turn % 100 ~= 0 then return end

    local death_ratio = stats.player_deaths / math.max(1, stats.monster_kills)

    if death_ratio > 0.5 then
        veinborn.add_message("[Difficulty: Easier mode activated]")
        -- Could modify monster stats here
    elseif death_ratio < 0.1 and event.turn > 300 then
        veinborn.add_message("[Difficulty: Harder mode activated]")
    end
end
```

### Pattern 4: Multi-Event Coordination

Track state across multiple event types:

```lua
-- @subscribe: entity_damaged, entity_healed, turn_ended
local damage_stats = {
    total_damage = 0,
    total_healing = 0
}

function on_entity_damaged(event)
    damage_stats.total_damage = damage_stats.total_damage + (event.data.amount or 0)
end

function on_entity_healed(event)
    damage_stats.total_healing = damage_stats.total_healing + (event.data.amount or 0)
end

function on_turn_ended(event)
    -- Report every 100 turns
    if event.turn % 100 == 0 then
        local net = damage_stats.total_damage - damage_stats.total_healing
        veinborn.add_message(string.format(
            "Combat stats: %d damage, %d healing, %d net",
            damage_stats.total_damage,
            damage_stats.total_healing,
            net
        ))
    end
end
```

## Advanced Topics

### State Persistence

Module-level variables persist across handler calls within the same game session:

```lua
-- This state persists!
local persistent_state = {
    kills = 0,
    achievements = {}
}

function on_entity_died(event)
    persistent_state.kills = persistent_state.kills + 1
    -- State is retained for next call
end
```

**Limitation:** State does NOT persist across game restarts (save/load). This is a future enhancement.

### Error Handling

Always use `pcall` for risky operations:

```lua
function on_entity_died(event)
    local success, err = pcall(function()
        -- Risky operation
        local entity = veinborn.get_entity(event.data.entity_id)
        if not entity then
            error("Entity not found!")
        end
    end)

    if not success then
        veinborn.add_message("Error: " .. tostring(err))
    end
end
```

### Performance Optimization

**1. Early Returns:**
```lua
function on_entity_died(event)
    -- Check conditions early
    if event.data.killer_id ~= "player_1" then
        return  -- Exit early, avoid unnecessary work
    end
    -- Process player kill
end
```

**2. Avoid Expensive Loops:**
```lua
-- BAD - expensive operation
function on_entity_died(event)
    for i = 1, 1000000 do
        -- Don't do this!
    end
end

-- GOOD - minimal work
function on_entity_died(event)
    kills = kills + 1
end
```

**3. Batch UI Updates:**
```lua
-- BAD - update UI every event
function on_entity_died(event)
    show_stats()  -- Expensive!
end

-- GOOD - update UI periodically
function on_turn_ended(event)
    if event.turn % 10 == 0 then
        show_stats()  -- Only every 10 turns
    end
end
```

### Manual Event Subscription

For dynamic subscriptions (less common):

```lua
-- Subscribe programmatically
function init()
    veinborn.event.subscribe("entity_died", "scripts/events/my_handler.lua", "on_entity_died")
end
```

## Testing

### Testing Event Handlers

**1. Emit test events:**
```lua
-- Manually trigger event for testing
veinborn.event.emit("entity_died", {
    entity_id = "test_goblin",
    entity_name = "Test Goblin",
    killer_id = "player_1",
    cause = "test"
})
```

**2. Add debug logging:**
```lua
function on_entity_died(event)
    -- Debug output
    veinborn.add_message("DEBUG: Entity died - " .. event.data.entity_name)

    -- Your handler logic
    kills = kills + 1
end
```

**3. Check event types:**
```lua
-- List all available event types
local types = veinborn.event.get_types()
for i = 1, #types do
    veinborn.add_message("Event type: " .. types[i])
end
```

## Troubleshooting

### Handler Not Called

**Symptom:** Event fires, but handler doesn't execute.

**Causes:**
1. Handler not subscribed correctly
2. Event type name mismatch
3. Handler function name wrong
4. Script has syntax error (failed to load)

**Solution:**
```lua
-- Check subscription
veinborn.event.subscribe("entity_died", "scripts/events/my_handler.lua", "on_entity_died")

-- Check function name matches
function on_entity_died(event)  -- Must match handler_name parameter
    -- ...
end
```

### Handler Timeout

**Symptom:** Handler stops mid-execution, timeout error in logs.

**Cause:** Handler takes >3 seconds.

**Solution:** Optimize handler code (see Performance Optimization above).

### Event Data Missing

**Symptom:** `event.data.some_field` is nil.

**Cause:** Event type has different data structure.

**Solution:** Check event documentation and handle missing fields:
```lua
function on_entity_died(event)
    -- Safely check if field exists
    local killer_id = event.data.killer_id or "unknown"
    if killer_id == "player_1" then
        -- Use field
    end
end
```

### State Not Persisting

**Symptom:** State resets between handler calls.

**Causes:**
1. Using local variables inside function (not module-level)
2. Game was restarted (state doesn't persist across sessions)

**Solution:**
```lua
-- WRONG - state resets each call
function on_entity_died(event)
    local kills = 0  -- This resets to 0 every time!
    kills = kills + 1
end

-- CORRECT - state persists
local kills = 0  -- Module-level variable

function on_entity_died(event)
    kills = kills + 1  -- Persists across calls
end
```

---

## Complete Examples

See the following files for complete working examples:
- `scripts/events/_template.lua` - Template with common patterns
- `scripts/events/achievements.lua` - Achievement system (9 achievements)
- `scripts/events/quest_tracker.lua` - Quest tracking system
- `scripts/events/dynamic_loot.lua` - Dynamic loot modification

## API Reference

For complete API documentation, see:
- `docs/LUA_API.md` - Full API reference
- `docs/architecture/EVENT_SYSTEM.md` - System architecture

## Limitations

- Handler timeout: 3 seconds max per handler
- State does NOT persist across game sessions (future enhancement)
- Cannot modify event data from handlers
- One handler function per event type per script

## Future Enhancements

Planned for future releases:
- State persistence across save/load
- Event priority/ordering control
- Event cancellation (prevent default behavior)
- Custom event types
- Inter-handler communication

---

**Happy Modding!**

For questions or issues, consult the troubleshooting section or check existing example handlers.
