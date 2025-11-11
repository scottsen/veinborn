# Brogue Lua Integration - Phase 2: AI Behaviors

**Date:** 2025-11-06
**Project:** Brogue Roguelike Game
**Target:** Lua-scriptable monster AI behaviors
**Timeline:** 1 week (6-8 hours focused work)
**Scope:** Phase 2 - Custom AI Behaviors
**Follows:** PR #16 (Phase 1 - Custom Actions) ✅

---

## Executive Summary

Extend Lua integration to support custom monster AI behaviors. Building on the excellent Phase 1 foundation, enable modders to create custom AI logic in Lua while maintaining compatibility with the existing 5 Python AI behaviors.

**Phase 2 Goal:** Enable Lua scripts to register custom AI behaviors that control monster decision-making seamlessly.

**Success Criteria:**
1. Lua AI behavior registration system working
2. AI behaviors can be defined in Lua scripts
3. Lua behaviors integrate with existing AISystem
4. Example "Berserker" AI works end-to-end
5. Comprehensive documentation and error handling
6. All 710 existing tests still pass + 25+ new tests

---

## Current State Assessment

### Excellent Foundation from Phase 1 ✅

**Lua Runtime (src/core/scripting/lua_runtime.py - 288 lines):**
- ✅ Sandbox configured and tested
- ✅ Timeout protection (3 seconds)
- ✅ lupa library integrated
- ✅ 39 tests passing
- **Ready for AI behavior scripts**

**GameContext API (src/core/scripting/game_context_api.py - 407 lines):**
- ✅ 15+ methods exposed to Lua
- ✅ Entity queries working (`get_player`, `get_entities_in_range`, etc.)
- ✅ Entity manipulation (`modify_stat`, `deal_damage`, `heal`)
- ✅ 27 tests passing
- **Needs:** Monster-specific queries for AI

**Test Infrastructure:**
- ✅ 710 tests passing (604 original + 106 Lua)
- ✅ Comprehensive test patterns established
- ✅ Integration tests for Fireball working
- **Ready for AI behavior tests**

### Existing AI System Analysis

**AISystem (src/core/systems/ai_system.py - 323 lines):**

**Current Architecture:**
- System-based: Runs during game update loop
- Behavior dispatch: `_execute_behavior()` calls `_behavior_{ai_type}()`
- 5 Python behaviors: aggressive, defensive, passive, coward, guard
- YAML configuration: `data/balance/ai_behaviors.yaml`

**Behavior Pattern:**
```python
def _behavior_aggressive(self, monster, config: Dict[str, Any]) -> None:
    """Aggressive: Chase and attack player."""
    player = self.context.get_player()
    # Decision logic...
    if monster.is_adjacent(player):
        self._attack_target(monster, player)
    elif distance <= chase_range:
        self._move_towards(monster, player)
    else:
        self._wander(monster)
```

**AI Helpers Available:**
- `_attack_target(monster, target)` - Execute attack action
- `_move_towards(monster, target)` - Pathfinding movement
- `_flee_from(monster, target)` - Move away from target
- `_wander(monster)` - Random movement

**Extension Point:**
- `_execute_behavior()` uses `getattr(self, f'_behavior_{ai_type}', None)`
- **Perfect for dynamic registration** - just need to inject Lua behaviors

**Configuration (data/balance/ai_behaviors.yaml):**
```yaml
behaviors:
  aggressive:
    chase_range: 10
    attack_on_sight: true
    flee_threshold: 0.0
```

**Monster AI Assignment:**
```yaml
default_ai_by_type:
  rat: passive
  bat: coward
  goblin: aggressive
```

---

## Phase 2: Lua AI Behaviors Tasks

### Task 1: Extend GameContext API for AI (1.5 hours)

**Goal:** Add AI-specific methods to GameContext API for Lua behaviors

**New Methods Needed:**

```lua
-- Get monster's current target (usually player)
local target = brogue.ai.get_target(monster_id)

-- Check if monster is adjacent to target
local adjacent = brogue.ai.is_adjacent(monster_id, target_id)

-- Calculate distance between entities
local distance = brogue.ai.distance_to(monster_id, target_id)

-- Get configuration for this AI behavior
local config = brogue.ai.get_config(ai_type)

-- AI Action Helpers (return action_type, params)
-- These queue actions for execution
brogue.ai.attack(monster_id, target_id)
brogue.ai.move_towards(monster_id, target_id)
brogue.ai.flee_from(monster_id, target_id)
brogue.ai.wander(monster_id)
brogue.ai.idle(monster_id)
```

**Implementation Steps:**

1. **Extend GameContextAPI** (`src/core/scripting/game_context_api.py`)
   - Add `brogue.ai` table for AI-specific methods
   - Implement helper methods that wrap AISystem utilities
   - Return action descriptors (not execute directly)

2. **Action Descriptor Format:**
   ```lua
   return {
       action = "attack",  -- or "move", "flee", "wander", "idle"
       target_id = "player_1",  -- optional, for attack/move/flee
       dx = 1, dy = 0  -- optional, for explicit movement
   }
   ```

3. **Create tests** (`tests/unit/test_game_context_api.py` - extend)
   - Test AI helper methods
   - Test action descriptor creation
   - Test distance/adjacency calculations
   - Test config retrieval

**Deliverables:**
- Extended `src/core/scripting/game_context_api.py` (+80 lines)
- 8 new tests in `tests/unit/test_game_context_api.py`
- All tests passing (710 → 718)

---

### Task 2: Lua AI Behavior Registration System (2 hours)

**Goal:** Enable Lua scripts to register as AI behaviors in AISystem

**Design:**

```python
# src/core/systems/ai_behavior_registry.py (NEW)

class AIBehaviorRegistry:
    """
    Registry for custom AI behaviors (Python and Lua).

    Enables dynamic registration of AI behavior functions.
    Lua behaviors are wrapped and integrated seamlessly.
    """

    def __init__(self):
        self._behaviors: Dict[str, Callable] = {}

    def register_python_behavior(self, ai_type: str, behavior_fn: Callable):
        """Register Python behavior function."""
        self._behaviors[ai_type] = behavior_fn

    def register_lua_behavior(self, ai_type: str, lua_runtime: LuaRuntime,
                            script_path: str):
        """
        Register Lua behavior from script.

        Lua behavior must implement:
            function update(monster, context, config)
                return {action="...", ...}
            end
        """
        # Load and wrap Lua script
        wrapper = LuaBehaviorWrapper(lua_runtime, script_path)
        self._behaviors[ai_type] = wrapper.execute

    def get_behavior(self, ai_type: str) -> Optional[Callable]:
        """Get behavior function by type."""
        return self._behaviors.get(ai_type)

    def has_behavior(self, ai_type: str) -> bool:
        """Check if behavior is registered."""
        return ai_type in self._behaviors
```

**LuaBehaviorWrapper:**

```python
# src/core/systems/lua_ai_behavior.py (NEW)

class LuaBehaviorWrapper:
    """
    Wraps Lua AI behavior script for execution in AISystem.

    Converts between Python/Lua types and handles errors.
    """

    def __init__(self, lua_runtime: LuaRuntime, script_path: str):
        self.lua_runtime = lua_runtime
        self.script_path = script_path
        self._load_script()

    def _load_script(self):
        """Load Lua script and validate structure."""
        self.lua_runtime.load_script_file(self.script_path)

        # Validate required function exists
        if not self.lua_runtime.has_function("update"):
            raise ValueError(f"Lua AI behavior must define update() function")

    def execute(self, monster, context, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Lua behavior and return action descriptor.

        Args:
            monster: Monster entity
            context: GameContext
            config: Behavior configuration from YAML

        Returns:
            Action descriptor dict: {action: str, ...}
        """
        # Prepare API
        api = GameContextAPI(context, self.lua_runtime.lua)

        # Convert monster to Lua table
        monster_table = api._entity_to_lua(monster)

        # Call Lua update() function
        result = self.lua_runtime.call_function(
            "update",
            monster_table,
            config
        )

        # Convert result to action descriptor
        return self._parse_action_descriptor(result)
```

**Integration with AISystem:**

```python
# Modify src/core/systems/ai_system.py

class AISystem(System):
    def __init__(self, context):
        super().__init__(context)
        self.config = ConfigLoader.get_config()
        self.registry = AIBehaviorRegistry()  # NEW
        self._register_builtin_behaviors()  # NEW

    def _register_builtin_behaviors(self):
        """Register Python AI behaviors in registry."""
        self.registry.register_python_behavior("aggressive", self._behavior_aggressive)
        self.registry.register_python_behavior("defensive", self._behavior_defensive)
        self.registry.register_python_behavior("passive", self._behavior_passive)
        self.registry.register_python_behavior("coward", self._behavior_coward)
        self.registry.register_python_behavior("guard", self._behavior_guard)

    def register_lua_behavior(self, ai_type: str, script_path: str):
        """Register Lua AI behavior from script."""
        # Assumes lua_runtime is available (passed in or created)
        self.registry.register_lua_behavior(ai_type, self.lua_runtime, script_path)

    def _execute_behavior(self, monster, ai_type: str, behavior_config: Dict[str, Any]):
        """Execute AI behavior (Python or Lua)."""
        behavior_fn = self.registry.get_behavior(ai_type)

        if not behavior_fn:
            logger.warning(f"Unknown AI type: {ai_type}, using aggressive")
            behavior_fn = self.registry.get_behavior("aggressive")

        # Execute behavior (returns None for Python, action descriptor for Lua)
        result = behavior_fn(monster, behavior_config)

        # Handle action descriptor from Lua behaviors
        if result:
            self._execute_action_descriptor(monster, result)
```

**Implementation Steps:**

1. Create `src/core/systems/ai_behavior_registry.py` (~120 lines)
2. Create `src/core/systems/lua_ai_behavior.py` (~180 lines)
3. Modify `src/core/systems/ai_system.py` (+60 lines)
4. Create tests:
   - `tests/unit/test_ai_behavior_registry.py` (~150 lines)
   - `tests/unit/test_lua_ai_behavior.py` (~180 lines)

**Deliverables:**
- `src/core/systems/ai_behavior_registry.py` (120 lines)
- `src/core/systems/lua_ai_behavior.py` (180 lines)
- Modified `src/core/systems/ai_system.py` (+60 lines)
- `tests/unit/test_ai_behavior_registry.py` (150 lines)
- `tests/unit/test_lua_ai_behavior.py` (180 lines)
- All tests passing (718 → 730)

---

### Task 3: Example "Berserker" AI Behavior (1 hour)

**Goal:** Create working example of Lua AI behavior

**Behavior Design:**

**Berserker AI:**
- Aggressive when healthy (>70% HP)
- **Enraged** when damaged (<70% HP)
  - Increased chase range
  - Always attacks (no fleeing)
  - Bonus damage when enraged
- Reckless: Doesn't flee even at low HP

**Implementation:**

```lua
-- scripts/ai/berserker.lua

--[[
Berserker AI Behavior

Characteristics:
- Aggressive when healthy (>70% HP)
- Enraged when damaged (<70% HP):
  * Increased chase range
  * Never flees
  * Higher aggression
- Suitable for: Orcs, Barbarians, Berserkers

Configuration (in ai_behaviors.yaml):
  berserker:
    description: "Aggressive fighter, enraged when wounded"
    chase_range: 8
    enraged_chase_range: 15
    enrage_threshold: 0.7  # Enrage when HP < 70%
    attack_on_sight: true
--]]

-- Behavior update function
-- Called each turn for monsters with ai_type="berserker"
function update(monster, config)
    -- Get player (primary target)
    local player = brogue.get_player()

    if not player or not player.is_alive then
        -- No target - wander
        return {action = "wander"}
    end

    -- Calculate HP ratio
    local hp_ratio = monster.hp / monster.max_hp
    local is_enraged = hp_ratio < config.enrage_threshold

    -- Determine chase range based on enrage state
    local chase_range = config.chase_range
    if is_enraged then
        chase_range = config.enraged_chase_range

        -- Visual feedback for enraged state (first time only)
        if not monster.stats.was_enraged then
            brogue.add_message(monster.name .. " enters a BERSERK RAGE!")
            brogue.modify_stat(monster.id, "was_enraged", true)
        end
    end

    -- Calculate distance to player
    local distance = brogue.ai.distance_to(monster.id, player.id)

    -- Attack if adjacent
    if brogue.ai.is_adjacent(monster.id, player.id) then
        return {
            action = "attack",
            target_id = player.id
        }
    end

    -- Chase if in range
    if distance <= chase_range then
        return {
            action = "move_towards",
            target_id = player.id
        }
    end

    -- Wander if out of range
    return {action = "wander"}
end
```

**YAML Configuration:**

```yaml
# Add to data/balance/ai_behaviors.yaml

behaviors:
  # ... existing behaviors ...

  berserker:
    description: "Aggressive fighter, enraged when wounded"
    chase_range: 8
    enraged_chase_range: 15
    enrage_threshold: 0.7
    attack_on_sight: true
```

**Register in Game:**

```python
# In Game initialization or AI system setup
ai_system.register_lua_behavior("berserker", "scripts/ai/berserker.lua")
```

**Implementation Steps:**

1. Create `scripts/ai/berserker.lua` (~80 lines)
2. Update `data/balance/ai_behaviors.yaml` (+8 lines)
3. Add registration in game initialization
4. Create integration test `tests/integration/test_berserker_ai.py` (~200 lines)
   - Test normal behavior (chase, attack)
   - Test enrage trigger (HP < 70%)
   - Test enraged state (increased range)
   - Test message generation
   - Test wandering when out of range

**Deliverables:**
- `scripts/ai/berserker.lua` (80 lines)
- `scripts/ai/_template.lua` (60 lines) - AI behavior template
- Updated `data/balance/ai_behaviors.yaml` (+8 lines)
- `tests/integration/test_berserker_ai.py` (200 lines)
- All tests passing (730 → 738)

---

### Task 4: Additional Example AI Behaviors (1 hour)

**Goal:** Demonstrate variety of AI behavior patterns

**Create 2 more example behaviors:**

#### **1. Sniper AI** (`scripts/ai/sniper.lua`)

**Behavior:**
- Maintains distance from player
- Moves away if player gets too close
- "Attacks" from range (projectile simulation)
- Flees when cornered

```lua
-- scripts/ai/sniper.lua
--[[
Sniper AI - Maintains range, attacks from distance

Characteristics:
- Prefers to stay at medium range (4-6 tiles)
- Moves away if player too close (<4 tiles)
- "Attacks" when in ideal range (4-6 tiles)
- Flees when cornered or low HP

Suitable for: Archers, Ranged enemies
--]]

local IDEAL_RANGE_MIN = 4
local IDEAL_RANGE_MAX = 6
local FLEE_THRESHOLD = 0.3

function update(monster, config)
    local player = brogue.get_player()

    if not player or not player.is_alive then
        return {action = "wander"}
    end

    local distance = brogue.ai.distance_to(monster.id, player.id)
    local hp_ratio = monster.hp / monster.max_hp

    -- Flee if low HP
    if hp_ratio < FLEE_THRESHOLD then
        return {
            action = "flee_from",
            target_id = player.id
        }
    end

    -- Too close - back away
    if distance < IDEAL_RANGE_MIN then
        return {
            action = "flee_from",
            target_id = player.id
        }
    end

    -- In ideal range - "attack" (for now just simulate)
    if distance >= IDEAL_RANGE_MIN and distance <= IDEAL_RANGE_MAX then
        -- Future: Create projectile action
        -- For now: message + stay in position
        brogue.add_message(monster.name .. " takes aim from afar!")
        return {action = "idle"}
    end

    -- Too far - move closer (but not too close)
    if distance > IDEAL_RANGE_MAX then
        return {
            action = "move_towards",
            target_id = player.id
        }
    end

    return {action = "idle"}
end
```

#### **2. Summoner AI** (`scripts/ai/summoner.lua`)

**Behavior:**
- Stays away from player
- "Summons" allies when player nearby
- Teleports away when threatened
- Support role (doesn't attack directly)

```lua
-- scripts/ai/summoner.lua
--[[
Summoner AI - Summons allies, avoids combat

Characteristics:
- Maintains distance from player
- "Summons" nearby monsters periodically
- Flees when player gets close
- Never attacks directly

Suitable for: Necromancers, Shamans, Cultists
--]]

local SUMMON_DISTANCE = 8  -- Summon when player within 8 tiles
local FLEE_DISTANCE = 4    -- Flee when player within 4 tiles
local SUMMON_COOLDOWN = 10 -- Summon every 10 turns

function update(monster, config)
    local player = brogue.get_player()

    if not player or not player.is_alive then
        return {action = "wander"}
    end

    local distance = brogue.ai.distance_to(monster.id, player.id)

    -- Track turns since last summon
    local last_summon_turn = monster.stats.last_summon_turn or 0
    local current_turn = brogue.get_turn_count()
    local turns_since_summon = current_turn - last_summon_turn

    -- Flee if player too close
    if distance < FLEE_DISTANCE then
        brogue.add_message(monster.name .. " retreats to safety!")
        return {
            action = "flee_from",
            target_id = player.id
        }
    end

    -- Summon if conditions met
    if distance <= SUMMON_DISTANCE and turns_since_summon >= SUMMON_COOLDOWN then
        -- Update summon timestamp
        brogue.modify_stat(monster.id, "last_summon_turn", current_turn)

        -- Visual feedback
        brogue.add_message(monster.name .. " chants an incantation!")

        -- Future: Actually spawn monsters nearby
        -- For now: Just message and cooldown
        return {action = "idle"}
    end

    -- Maintain distance
    if distance < SUMMON_DISTANCE then
        return {
            action = "flee_from",
            target_id = player.id
        }
    end

    -- Wander when safe
    return {action = "wander"}
end
```

**Implementation Steps:**

1. Create `scripts/ai/sniper.lua` (~70 lines)
2. Create `scripts/ai/summoner.lua` (~80 lines)
3. Update `data/balance/ai_behaviors.yaml` (+16 lines, both configs)
4. Create tests:
   - `tests/integration/test_sniper_ai.py` (~120 lines)
   - `tests/integration/test_summoner_ai.py` (~120 lines)

**Deliverables:**
- `scripts/ai/sniper.lua` (70 lines)
- `scripts/ai/summoner.lua` (80 lines)
- Updated `data/balance/ai_behaviors.yaml` (+16 lines)
- `tests/integration/test_sniper_ai.py` (120 lines)
- `tests/integration/test_summoner_ai.py` (120 lines)
- All tests passing (738 → 748)

---

### Task 5: Documentation (45 minutes)

**Goal:** Comprehensive documentation for AI behavior modding

**Create AI Behavior Documentation:**

#### **1. Update LUA_API.md** (extend existing)

Add AI-specific section:

```markdown
## AI Behavior API

Custom AI behaviors control monster decision-making during gameplay.

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

#### `brogue.ai.is_adjacent(monster_id, target_id)`
Check if monster is adjacent to target.

#### `brogue.ai.distance_to(monster_id, target_id)`
Calculate Manhattan distance between entities.

#### `brogue.ai.get_config(ai_type)`
Get behavior configuration from YAML.

### Action Descriptors

AI behaviors return action descriptors to control monster actions:

**Attack Action:**
```lua
return {
    action = "attack",
    target_id = "player_1"
}
```

**Move Towards:**
```lua
return {
    action = "move_towards",
    target_id = "player_1"
}
```

**Flee From:**
```lua
return {
    action = "flee_from",
    target_id = "player_1"
}
```

**Wander:**
```lua
return {action = "wander"}
```

**Idle (do nothing):**
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

### Example: Berserker AI

See `scripts/ai/berserker.lua` for complete example.
```

#### **2. Create LUA_AI_MODDING_GUIDE.md** (new file)

```markdown
# Lua AI Behavior Modding Guide

## Getting Started

### What Are AI Behaviors?

AI behaviors control how monsters make decisions during gameplay:
- When to attack vs flee
- How far to chase the player
- Special abilities or tactics
- Personality and character

### Creating Your First AI Behavior

**Step 1: Create Lua script**

```lua
-- scripts/ai/my_behavior.lua

function update(monster, config)
    local player = brogue.get_player()

    -- Simple aggressive behavior
    if brogue.ai.is_adjacent(monster.id, player.id) then
        return {action = "attack", target_id = player.id}
    else
        return {action = "move_towards", target_id = player.id}
    end
end
```

**Step 2: Add configuration**

Edit `data/balance/ai_behaviors.yaml`:

```yaml
behaviors:
  my_behavior:
    description: "My custom AI"
    chase_range: 10
```

**Step 3: Register behavior**

In game code:
```python
ai_system.register_lua_behavior("my_behavior", "scripts/ai/my_behavior.lua")
```

**Step 4: Assign to monster**

In monster YAML:
```yaml
goblin:
  ai_type: my_behavior
```

## AI Behavior Patterns

### Pattern 1: State-Based AI

Use monster stats to track state:

```lua
function update(monster, config)
    local state = monster.stats.ai_state or "patrol"

    if state == "patrol" then
        -- Patrol logic
    elseif state == "alert" then
        -- Combat logic
    elseif state == "fleeing" then
        -- Flee logic
    end
end
```

### Pattern 2: Range-Based AI

Different behavior at different ranges:

```lua
function update(monster, config)
    local distance = brogue.ai.distance_to(monster.id, player.id)

    if distance <= 2 then
        return {action = "attack", target_id = player.id}
    elseif distance <= 8 then
        return {action = "move_towards", target_id = player.id}
    else
        return {action = "wander"}
    end
end
```

### Pattern 3: HP-Based AI

React to damage:

```lua
function update(monster, config)
    local hp_ratio = monster.hp / monster.max_hp

    if hp_ratio < 0.3 then
        -- Low HP - flee
        return {action = "flee_from", target_id = player.id}
    else
        -- Healthy - attack
        return {action = "attack", target_id = player.id}
    end
end
```

## Testing Your AI

**Manual Testing:**
1. Run game: `python3 run_textual.py`
2. Find monster with your AI
3. Observe behavior
4. Check messages for debugging

**Unit Testing:**
```python
def test_my_behavior():
    # Create test scenario
    # Execute AI update
    # Assert expected action
```

## Common Pitfalls

❌ **Don't modify monster directly in Lua**
```lua
monster.hp = 100  -- BAD - doesn't work
```

✅ **Use API methods**
```lua
brogue.modify_stat(monster.id, "hp", -10)  -- GOOD
```

❌ **Don't execute actions directly**
```lua
AttackAction().execute()  -- BAD - Lua doesn't have Action classes
```

✅ **Return action descriptors**
```lua
return {action = "attack", target_id = player.id}  -- GOOD
```

## Advanced Topics

### Persistent State

Store data in monster stats:

```lua
-- Initialize on first update
if not monster.stats.initialized then
    brogue.modify_stat(monster.id, "patrol_x", monster.x)
    brogue.modify_stat(monster.id, "initialized", true)
end

-- Access later
local patrol_x = monster.stats.patrol_x
```

### Cooldowns

Track abilities with turn counters:

```lua
local current_turn = brogue.get_turn_count()
local last_ability = monster.stats.last_ability_turn or 0

if current_turn - last_ability >= COOLDOWN then
    -- Use ability
    brogue.modify_stat(monster.id, "last_ability_turn", current_turn)
end
```

### Team Coordination

Query nearby allies:

```lua
local allies = brogue.get_entities_in_range(monster.x, monster.y, 5)
local ally_count = 0

for i = 1, #allies do
    if allies[i].entity_type == "MONSTER" then
        ally_count = ally_count + 1
    end
end

-- Use pack tactics if allies nearby
if ally_count >= 2 then
    -- Aggressive
else
    -- Cautious
end
```

## Examples

See `scripts/ai/` for complete examples:
- `berserker.lua` - Enrage mechanic
- `sniper.lua` - Range maintenance
- `summoner.lua` - Support role
- `_template.lua` - Starting template
```

**Implementation Steps:**

1. Extend `docs/LUA_API.md` (+100 lines, AI section)
2. Create `docs/LUA_AI_MODDING_GUIDE.md` (~400 lines)
3. Create `scripts/ai/_template.lua` (60 lines, boilerplate)
4. Add inline documentation to all AI scripts

**Deliverables:**
- Updated `docs/LUA_API.md` (+100 lines)
- New `docs/LUA_AI_MODDING_GUIDE.md` (400 lines)
- New `scripts/ai/_template.lua` (60 lines)

---

### Task 6: Integration & Testing (45 minutes)

**Goal:** Ensure AI integration doesn't break existing functionality

**Test Plan:**

1. **Run full test suite**
   ```bash
   cd /home/scottsen/src/projects/brogue
   pytest -v
   ```
   - Verify all 710 original tests still pass
   - Verify all new AI tests pass (~38 new tests)
   - Total expected: ~748 passing

2. **Manual testing**
   ```bash
   python3 run_textual.py
   ```
   - Play game with Python AI behaviors (verify no regression)
   - Test Berserker AI (enrage mechanic)
   - Test Sniper AI (range maintenance)
   - Test Summoner AI (flee behavior)
   - Check logs for Lua errors

3. **Performance testing**
   - Run bot stress test (5k turns)
   - Verify Lua AI overhead is minimal (<10% performance impact)
   - Check memory usage (no Lua memory leaks)
   - Profile AI update() calls

4. **Integration verification**
   - Python AI behaviors still work ✓
   - Lua AI behaviors work ✓
   - Mixed AI types in same game ✓
   - YAML configuration loaded correctly ✓
   - Error handling works (invalid Lua scripts) ✓

**Deliverables:**
- All tests passing (~748 total)
- Performance benchmark results
- Clean test output with no warnings
- Working integration demonstration

---

## Technical Requirements

### Dependencies

No new dependencies needed! ✅
- lupa already installed (Phase 1)
- All infrastructure ready

### Safety Guarantees

**Sandbox (already configured):**
- ✅ No file I/O
- ✅ No OS access
- ✅ No dynamic code loading
- ✅ 3-second timeout per behavior update

**AI-Specific Safety:**
- AI behaviors cannot execute actions directly (return descriptors only)
- Invalid action descriptors handled gracefully
- Lua errors don't crash game (fallback to default behavior)
- Infinite loops protected by timeout

### File Structure

```
brogue/
├── src/
│   └── core/
│       ├── systems/
│       │   ├── ai_system.py              # MODIFIED (+60 lines)
│       │   ├── ai_behavior_registry.py   # NEW (120 lines)
│       │   └── lua_ai_behavior.py        # NEW (180 lines)
│       └── scripting/
│           └── game_context_api.py       # MODIFIED (+80 lines, AI methods)
│
├── scripts/
│   └── ai/                               # NEW
│       ├── _template.lua                 # Template (60 lines)
│       ├── berserker.lua                 # Example (80 lines)
│       ├── sniper.lua                    # Example (70 lines)
│       └── summoner.lua                  # Example (80 lines)
│
├── data/
│   └── balance/
│       └── ai_behaviors.yaml             # MODIFIED (+24 lines)
│
├── docs/
│   ├── LUA_API.md                        # MODIFIED (+100 lines)
│   └── LUA_AI_MODDING_GUIDE.md           # NEW (400 lines)
│
└── tests/
    ├── unit/
    │   ├── test_ai_behavior_registry.py  # NEW (150 lines)
    │   ├── test_lua_ai_behavior.py       # NEW (180 lines)
    │   └── test_game_context_api.py      # MODIFIED (+50 lines)
    └── integration/
        ├── test_berserker_ai.py          # NEW (200 lines)
        ├── test_sniper_ai.py             # NEW (120 lines)
        └── test_summoner_ai.py           # NEW (120 lines)
```

---

## Success Criteria

### Must Have (Phase 2)

✅ **Lua AI behavior registration**
- Registry system working
- Python and Lua behaviors coexist
- Dynamic registration from scripts

✅ **AI behaviors defined in Lua**
- update(monster, config) interface
- Action descriptor return format
- Access to AI helper methods

✅ **Integration with AISystem**
- Lua behaviors execute seamlessly
- Python behaviors unchanged
- Fallback to default behavior on error

✅ **Example behaviors working**
- Berserker (enrage mechanic)
- Sniper (range maintenance)
- Summoner (support role)

✅ **Documentation complete**
- Extended LUA_API.md (AI section)
- LUA_AI_MODDING_GUIDE.md (complete guide)
- AI behavior template

✅ **Tests passing**
- All 710 original tests still pass
- 38+ new AI tests added and passing
- Integration tests demonstrate behaviors

---

## Implementation Strategy

### Day 1: API + Registry (3.5 hours)
- Task 1: Extend GameContext API for AI (1.5h)
- Task 2: Lua AI behavior registration system (2h)

### Day 2: Examples (2 hours)
- Task 3: Berserker AI (1h)
- Task 4: Sniper + Summoner AI (1h)

### Day 3: Documentation + Testing (1.5 hours)
- Task 5: Documentation (45m)
- Task 6: Integration & testing (45m)

**Total:** 7 hours focused work

---

## Risk Mitigation

### Risk 1: Performance Impact
**Concern:** Lua AI called every turn for every monster
**Mitigation:**
- Profile AI update calls
- Cache Lua function references
- Optimize hot paths in GameContextAPI
- Timeout protection (3 seconds)

### Risk 2: Breaking Python AI Behaviors
**Concern:** Refactoring AISystem breaks existing behaviors
**Mitigation:**
- Comprehensive regression tests
- Registry preserves Python behavior methods
- Fallback to default on errors

### Risk 3: Complex Action Descriptors
**Concern:** Descriptor format might be insufficient for complex actions
**Mitigation:**
- Start simple (attack, move, flee, wander, idle)
- Extensible format (can add fields later)
- Document limitations clearly

### Risk 4: Lua Error Handling
**Concern:** Lua script errors crash game or cause monsters to freeze
**Mitigation:**
- Wrap all Lua calls in try/catch
- Log errors and fallback to wander
- Timeout protection
- Validation on script load

---

## Commit Strategy

**Recommended Commits:**

1. "Extend GameContext API with AI helper methods for Lua behaviors"
2. "Add AI behavior registry and Lua behavior wrapper"
3. "Integrate Lua AI behaviors with AISystem"
4. "Add Berserker example AI behavior with enrage mechanic"
5. "Add Sniper and Summoner example AI behaviors"
6. "Add comprehensive AI behavior documentation and modding guide"
7. "Add integration tests for Lua AI behaviors"

**Branch Strategy:**
- Create feature branch: `feature/lua-ai-behaviors-phase2`
- Commit incrementally (atomic commits)
- Create PR when complete
- Squash merge to main after review

---

## Definition of Done

### Code Complete
- [ ] All 6 tasks implemented
- [ ] Code follows existing patterns (type hints, logging, docstrings)
- [ ] No hardcoded paths (use config/constants)
- [ ] Error handling comprehensive
- [ ] Python AI behaviors unchanged

### Tests Complete
- [ ] All original 710 tests still pass
- [ ] 38+ new AI tests added and passing
- [ ] Integration tests demonstrate all 3 example behaviors
- [ ] Manual testing completed (Python + Lua AI in same game)

### Documentation Complete
- [ ] `docs/LUA_API.md` extended (AI section)
- [ ] `docs/LUA_AI_MODDING_GUIDE.md` created (complete guide)
- [ ] `scripts/ai/_template.lua` - AI behavior template
- [ ] Inline code comments and docstrings

### Quality Checks
- [ ] No regressions (original functionality intact)
- [ ] Performance acceptable (<10% overhead)
- [ ] No memory leaks
- [ ] Clean git history (atomic commits)
- [ ] Python + Lua AI coexist in same game

### Ready for PR
- [ ] Branch rebased on latest main
- [ ] All tests passing
- [ ] Documentation reviewed
- [ ] Example behaviors working
- [ ] Ready for code review

---

## Context for Agent

### Repository Location
```bash
cd /home/scottsen/src/projects/brogue
```

### Current State
- **Branch:** main
- **Tests:** 710 passing
- **Recent PR:** #16 (Lua Actions - Phase 1) ✅ merged
- **Lua Runtime:** Ready and tested (lupa library)
- **GameContext API:** Ready with 15+ methods

### Key Files to Study First
1. `src/core/scripting/lua_runtime.py` - Lua runtime (288 lines)
2. `src/core/scripting/game_context_api.py` - API bridge (407 lines)
3. `src/core/systems/ai_system.py` - Current AI system (323 lines)
4. `data/balance/ai_behaviors.yaml` - AI configurations (62 lines)
5. `scripts/actions/fireball.lua` - Example Lua action (good reference)

### Run Tests
```bash
cd /home/scottsen/src/projects/brogue
pytest -v
pytest tests/unit/test_ai_behavior_registry.py -v  # After creating
```

### Useful TIA Commands
```bash
tia read src/core/systems/ai_system.py       # Smart file reading
tia search all "AISystem"                    # Search codebase
tia beth explore "brogue ai system"          # Knowledge graph search
```

---

## Questions for Clarification

If you encounter ambiguity, ask the user:

1. **Action Descriptors:** Should we support custom action types beyond (attack, move, flee, wander, idle)?
2. **Performance:** What's acceptable Lua AI execution time per monster? (default: <10ms)
3. **Python Behaviors:** Should Python behaviors also use action descriptors for consistency?
4. **Error Recovery:** Should invalid Lua AI fall back to wander or aggressive?
5. **Hot Reload:** Should we support reloading AI scripts without restarting? (defer to Phase 4?)

---

## References

**Phase 1 Documentation:**
- `/home/scottsen/src/projects/brogue/LUA_INTEGRATION_PROMPT.md` (820 lines)
- `/home/scottsen/src/projects/brogue/docs/LUA_API.md` (225 lines)
- `/home/scottsen/src/projects/brogue/scripts/actions/fireball.lua` (150 lines)

**Current Architecture:**
- `/home/scottsen/src/projects/brogue/src/core/systems/ai_system.py` (323 lines)
- `/home/scottsen/src/projects/brogue/data/balance/ai_behaviors.yaml` (62 lines)

**Prior Session:**
- `/home/scottsen/src/tia/sessions/aqua-dawn-1106/` (this session)
- `/home/scottsen/src/tia/sessions/descending-cosmos-1106/README_2025-11-06_15-36.md`

---

**Agent: You are now implementing Phase 2 of Lua integration. Build on the excellent Phase 1 foundation (710 tests passing). Focus on AI behavior registration, example implementations, and thorough testing. The architecture is ready for this work. Good luck!** 🚀
