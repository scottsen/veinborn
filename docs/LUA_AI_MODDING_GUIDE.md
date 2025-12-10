# Lua AI Behavior Modding Guide

**Complete guide to creating custom AI behaviors for Veinborn**

## Table of Contents

1. [Getting Started](#getting-started)
2. [AI Behavior Basics](#ai-behavior-basics)
3. [Creating Your First AI Behavior](#creating-your-first-ai-behavior)
4. [AI Behavior Patterns](#ai-behavior-patterns)
5. [Advanced Topics](#advanced-topics)
6. [Testing Your AI](#testing-your-ai)
7. [Common Pitfalls](#common-pitfalls)
8. [Examples](#examples)

---

## Getting Started

### What Are AI Behaviors?

AI behaviors control how monsters make decisions during gameplay:
- When to attack vs flee
- How far to chase the player
- Special abilities or tactics
- Personality and character

Each behavior is a Lua script with an `update(monster, config)` function that returns action descriptors.

### Prerequisites

- Basic Lua knowledge
- Familiarity with Veinborn game mechanics
- Understanding of entity positions and ranges

### Directory Structure

```
veinborn/
├── scripts/
│   └── ai/
│       ├── _template.lua         # Template for new behaviors
│       ├── berserker.lua         # Example: Enrage mechanic
│       ├── sniper.lua            # Example: Range maintenance
│       └── summoner.lua          # Example: Support role
├── data/
│   └── balance/
│       └── ai_behaviors.yaml     # Behavior configurations
└── docs/
    ├── LUA_API.md                # API reference
    └── LUA_AI_MODDING_GUIDE.md   # This guide
```

---

## AI Behavior Basics

### The update() Function

Every AI behavior must define an `update()` function:

```lua
function update(monster, config)
    -- AI decision logic
    return {action = "...", ...}
end
```

**Parameters:**
- `monster`: Monster entity table with properties:
  - `id`: Entity ID (string)
  - `name`: Monster name (string)
  - `x`, `y`: Position (number)
  - `hp`, `max_hp`: Health (number)
  - `attack`, `defense`: Combat stats (number)
  - `stats`: Custom stats dictionary (table)

- `config`: Behavior configuration from YAML (table)
  - Contains parameters like `chase_range`, `flee_threshold`, etc.

**Returns:** Action descriptor table

### Action Descriptors

Action descriptors tell the AI system what the monster should do:

| Action | Parameters | Description |
|--------|------------|-------------|
| `attack` | `target_id` | Attack target entity |
| `move_towards` | `target_id` | Move toward target |
| `flee_from` | `target_id` | Move away from target |
| `wander` | None | Random movement |
| `idle` | None | Do nothing |

### Available API Methods

See [LUA_API.md](LUA_API.md#ai-behavior-api) for complete API reference.

**Common methods:**
```lua
veinborn.get_player()                          -- Get player entity
veinborn.ai.distance_to(monster_id, target_id) -- Calculate distance
veinborn.ai.is_adjacent(monster_id, target_id) -- Check adjacency
veinborn.add_message(text)                     -- Add game message
veinborn.modify_stat(entity_id, stat, delta)   -- Modify stat
veinborn.get_turn_count()                      -- Get current turn
```

---

## Creating Your First AI Behavior

### Step 1: Create Lua Script

Create a new file `scripts/ai/my_behavior.lua`:

```lua
-- Simple aggressive behavior
function update(monster, config)
    local player = veinborn.get_player()

    -- Check if player exists
    if not player or not player.is_alive then
        return {action = "wander"}
    end

    -- Check if adjacent
    if veinborn.ai.is_adjacent(monster.id, player.id) then
        return {action = "attack", target_id = player.id}
    end

    -- Chase player
    local distance = veinborn.ai.distance_to(monster.id, player.id)
    if distance <= config.chase_range then
        return {action = "move_towards", target_id = player.id}
    end

    -- Wander if out of range
    return {action = "wander"}
end
```

### Step 2: Add Configuration

Edit `data/balance/ai_behaviors.yaml`:

```yaml
behaviors:
  my_behavior:
    description: "My custom AI behavior"
    chase_range: 10
```

### Step 3: Register Behavior

In game initialization code (e.g., `Game.__init__` or system setup):

```python
# Assuming you have ai_system and lua_runtime available
ai_system.register_lua_behavior("my_behavior", "scripts/ai/my_behavior.lua")
```

### Step 4: Assign to Monster

In monster YAML configuration:

```yaml
# data/monsters/orc.yaml
orc:
  name: "Orc"
  hp: 30
  attack: 8
  ai_type: my_behavior  # Use your custom behavior
```

Or dynamically in code:
```python
monster.set_stat('ai_type', 'my_behavior')
```

---

## AI Behavior Patterns

### Pattern 1: State-Based AI

Use monster stats to track state across turns:

```lua
function update(monster, config)
    local state = monster.stats.ai_state or "patrol"

    if state == "patrol" then
        -- Patrol behavior
        local player = veinborn.get_player()
        local distance = veinborn.ai.distance_to(monster.id, player.id)

        if distance <= config.alert_range then
            veinborn.modify_stat(monster.id, "ai_state", "alert")
            veinborn.add_message(monster.name .. " is alerted!")
        end

        return {action = "wander"}

    elseif state == "alert" then
        -- Combat behavior
        local player = veinborn.get_player()

        if veinborn.ai.is_adjacent(monster.id, player.id) then
            return {action = "attack", target_id = player.id}
        else
            return {action = "move_towards", target_id = player.id}
        end

    elseif state == "fleeing" then
        -- Flee behavior
        local player = veinborn.get_player()
        local hp_ratio = monster.hp / monster.max_hp

        if hp_ratio > 0.5 then
            veinborn.modify_stat(monster.id, "ai_state", "alert")
        end

        return {action = "flee_from", target_id = player.id}
    end
end
```

### Pattern 2: Range-Based AI

Different behavior at different ranges:

```lua
function update(monster, config)
    local player = veinborn.get_player()
    if not player then return {action = "wander"} end

    local distance = veinborn.ai.distance_to(monster.id, player.id)

    -- Melee range (0-2)
    if distance <= 2 then
        if veinborn.ai.is_adjacent(monster.id, player.id) then
            return {action = "attack", target_id = player.id}
        else
            return {action = "move_towards", target_id = player.id}
        end

    -- Chase range (3-10)
    elseif distance <= 10 then
        return {action = "move_towards", target_id = player.id}

    -- Out of range (10+)
    else
        return {action = "wander"}
    end
end
```

### Pattern 3: HP-Based AI

React to damage and health changes:

```lua
function update(monster, config)
    local player = veinborn.get_player()
    if not player then return {action = "wander"} end

    local hp_ratio = monster.hp / monster.max_hp
    local distance = veinborn.ai.distance_to(monster.id, player.id)

    -- Critical HP - flee
    if hp_ratio < 0.2 then
        veinborn.add_message(monster.name .. " looks desperate!")
        return {action = "flee_from", target_id = player.id}

    -- Low HP - defensive
    elseif hp_ratio < 0.5 then
        if veinborn.ai.is_adjacent(monster.id, player.id) then
            return {action = "attack", target_id = player.id}
        else
            return {action = "flee_from", target_id = player.id}
        end

    -- Healthy - aggressive
    else
        if veinborn.ai.is_adjacent(monster.id, player.id) then
            return {action = "attack", target_id = player.id}
        elseif distance <= 10 then
            return {action = "move_towards", target_id = player.id}
        else
            return {action = "wander"}
        end
    end
end
```

### Pattern 4: Cooldown-Based Abilities

Track abilities with turn counters:

```lua
function update(monster, config)
    local player = veinborn.get_player()
    if not player then return {action = "wander"} end

    local current_turn = veinborn.get_turn_count()
    local last_ability = monster.stats.last_ability_turn or 0
    local cooldown = config.ability_cooldown or 5

    -- Check if ability is off cooldown
    if (current_turn - last_ability) >= cooldown then
        local distance = veinborn.ai.distance_to(monster.id, player.id)

        if distance <= config.ability_range then
            -- Use ability
            veinborn.modify_stat(monster.id, "last_ability_turn", current_turn)
            veinborn.add_message(monster.name .. " uses special ability!")
            return {action = "idle"}  -- Ability turn
        end
    end

    -- Normal behavior when ability on cooldown
    if veinborn.ai.is_adjacent(monster.id, player.id) then
        return {action = "attack", target_id = player.id}
    else
        return {action = "move_towards", target_id = player.id}
    end
end
```

---

## Advanced Topics

### Persistent State

Store data in monster stats that persists across turns:

```lua
function update(monster, config)
    -- Initialize on first update
    if not monster.stats.initialized then
        veinborn.modify_stat(monster.id, "patrol_x", monster.x)
        veinborn.modify_stat(monster.id, "patrol_y", monster.y)
        veinborn.modify_stat(monster.id, "initialized", true)
    end

    -- Access later
    local patrol_x = monster.stats.patrol_x
    local patrol_y = monster.stats.patrol_y

    -- AI logic using persistent data...
end
```

### Team Coordination

Query nearby allies for pack tactics:

```lua
function update(monster, config)
    local player = veinborn.get_player()
    if not player then return {action = "wander"} end

    -- Count nearby allies
    local allies = veinborn.get_entities_in_range(monster.x, monster.y, 5)
    local ally_count = 0

    for i = 1, #allies do
        if allies[i].entity_type == "MONSTER" and allies[i].id ~= monster.id then
            ally_count = ally_count + 1
        end
    end

    -- Use pack tactics if allies nearby
    if ally_count >= 2 then
        -- Aggressive with backup
        if veinborn.ai.is_adjacent(monster.id, player.id) then
            return {action = "attack", target_id = player.id}
        else
            return {action = "move_towards", target_id = player.id}
        end
    else
        -- Cautious when alone
        local hp_ratio = monster.hp / monster.max_hp
        if hp_ratio < 0.5 then
            return {action = "flee_from", target_id = player.id}
        else
            return {action = "wander"}
        end
    end
end
```

### Dynamic Messaging

Provide feedback based on AI state:

```lua
function update(monster, config)
    local player = veinborn.get_player()
    local hp_ratio = monster.hp / monster.max_hp

    -- First-time enrage message
    if hp_ratio < 0.3 and not monster.stats.enraged then
        veinborn.modify_stat(monster.id, "enraged", true)
        veinborn.add_message(monster.name .. " becomes enraged!")
    end

    -- Victory taunt when player hurt
    if player.hp < player.max_hp * 0.3 and not monster.stats.taunted then
        veinborn.modify_stat(monster.id, "taunted", true)
        veinborn.add_message(monster.name .. " senses victory!")
    end

    -- AI logic...
end
```

---

## Testing Your AI

### Manual Testing

1. **Run the game:**
   ```bash
   python3 run_textual.py
   ```

2. **Find monster with your AI:**
   - Look for monsters with `ai_type` set to your behavior
   - Or modify a monster in a test scenario

3. **Observe behavior:**
   - Watch movement patterns
   - Check messages for debugging
   - Verify state transitions

4. **Test edge cases:**
   - Monster at 1 HP
   - Player far away
   - Multiple monsters with same AI
   - No valid moves available

### Unit Testing

Create tests in `tests/integration/test_my_behavior.py`:

```python
def test_my_behavior_basic():
    # Create test scenario
    context = create_test_context()
    monster = create_monster(ai_type="my_behavior")
    player = context.get_player()

    # Position entities
    monster.x, monster.y = 10, 10
    player.x, player.y = 15, 10

    # Run AI update
    ai_system = AISystem(context, lua_runtime)
    ai_system.update()

    # Assert expected behavior
    # (e.g., monster moved toward player)
```

### Debug Logging

Add debug messages to your Lua code:

```lua
function update(monster, config)
    veinborn.add_message("DEBUG: Monster at " .. monster.x .. "," .. monster.y)

    local player = veinborn.get_player()
    local distance = veinborn.ai.distance_to(monster.id, player.id)

    veinborn.add_message("DEBUG: Distance to player: " .. distance)

    -- AI logic...
end
```

---

## Common Pitfalls

### ❌ Don't Modify Monster Directly

```lua
-- BAD - doesn't work
monster.hp = 100
monster.x = 20
```

### ✅ Use API Methods

```lua
-- GOOD
veinborn.modify_stat(monster.id, "hp", -10)
-- Movement handled by action descriptors
```

### ❌ Don't Execute Actions Directly

```lua
-- BAD - Lua doesn't have Action classes
AttackAction().execute()
```

### ✅ Return Action Descriptors

```lua
-- GOOD
return {action = "attack", target_id = player.id}
```

### ❌ Don't Assume Player Exists

```lua
-- BAD - player might be nil
local player = veinborn.get_player()
local distance = veinborn.ai.distance_to(monster.id, player.id)  -- Crash!
```

### ✅ Always Check Nil

```lua
-- GOOD
local player = veinborn.get_player()
if not player or not player.is_alive then
    return {action = "wander"}
end
local distance = veinborn.ai.distance_to(monster.id, player.id)
```

### ❌ Don't Forget Return Statement

```lua
-- BAD - no return
function update(monster, config)
    local player = veinborn.get_player()
    -- logic but no return!
end
```

### ✅ Always Return Action Descriptor

```lua
-- GOOD
function update(monster, config)
    -- logic...
    return {action = "idle"}  -- Always return something
end
```

---

## Examples

### Complete Examples Included

1. **Berserker** (`scripts/ai/berserker.lua`)
   - Aggressive when healthy
   - Enrages when wounded (<70% HP)
   - Increased chase range when enraged
   - Message on first enrage

2. **Sniper** (`scripts/ai/sniper.lua`)
   - Maintains distance (4-6 tiles)
   - Moves away if too close
   - "Attacks" from ideal range
   - Flees when low HP

3. **Summoner** (`scripts/ai/summoner.lua`)
   - Stays away from player
   - Periodic "summoning" with cooldown
   - Flees when threatened
   - Support role (no direct attacks)

4. **Template** (`scripts/ai/_template.lua`)
   - Starting point for new behaviors
   - Commented sections
   - Basic decision tree

### Study the Examples

Read the example files to learn:
- How to structure your code
- Common patterns and techniques
- Configuration usage
- Message feedback
- State management

### Start Simple

Begin with a simple behavior:
1. Copy `_template.lua`
2. Implement basic chase-and-attack
3. Test thoroughly
4. Add complexity incrementally
5. Test each addition

---

## Tips for Success

1. **Start with existing behaviors:** Study `berserker.lua` before creating your own

2. **Test incrementally:** Test each feature as you add it

3. **Use messages for debugging:** `veinborn.add_message()` is your friend

4. **Keep it simple:** Complex AI can be hard to debug

5. **Use configuration:** Put numbers in YAML, not hardcoded in Lua

6. **Think about edge cases:** What if player is dead? Monster cornered?

7. **Watch for infinite loops:** Always return from `update()`

8. **Respect the sandbox:** No file I/O or OS calls

9. **Read the API docs:** [LUA_API.md](LUA_API.md) has all available functions

10. **Join the community:** Share your AI behaviors with other modders!

---

## Next Steps

1. **Read the API Reference:** [LUA_API.md](LUA_API.md)
2. **Study Examples:** Look at `scripts/ai/*.lua`
3. **Create Your First AI:** Use `_template.lua` as starting point
4. **Test Thoroughly:** Manual and automated testing
5. **Share Your Work:** Contribute back to the community!

Happy modding! 🎮✨
