# Lua Scripting: Architectural Impact Analysis

**Session**: bamizogi-1023
**Date**: 2025-10-23
**Question**: "If we assume Lua scripting will eventually be needed, what architectural decisions should we make differently now?"

---

## Executive Summary

**Finding**: Your architecture already mentions Lua as Phase 2 (see `docs/architecture/00_ARCHITECTURE_OVERVIEW.md:97-98`):
> **Future:** Scripting (Lua/Python) for complex behavior.

**Recommendation**: **Make 5 key architectural decisions NOW** that enable painless Lua integration later, without over-engineering for a future that may never come.

**Impact**: Medium effort now (2-3 days), saves 2-4 weeks of refactoring later.

---

## Current State Analysis

### What You Have Now (MVP Phase)

**Architecture Pattern**: Direct function calls, Python-only logic

**Content Definition**:
```python
# entities.py - Hardcoded dictionaries
HEALING_ITEMS = {
    'health_potion': {'heal': 10, 'common': True},
    'bandage': {'heal': 5, 'common': True},
}

WEAPONS = {
    'sword': {'damage': 6, 'skill': 'melee'},
    'dagger': {'damage': 4, 'skill': 'melee'},
}
```

**Monster AI**:
```python
# game.py:120 - Inline Python logic
def handle_monster_turns(self):
    for monster in self.state.monsters:
        # Simple AI: move toward player or attack if adjacent
        dx = self.state.player.x - monster.x
        dy = self.state.player.y - monster.y
        if abs(dx) <= 1 and abs(dy) <= 1:
            self.handle_combat(monster, self.state.player)
        else:
            # Move toward player...
```

**Combat System**:
```python
# game.py:106 - Direct damage calculation
def handle_combat(self, attacker, defender):
    damage = max(1, attacker.attack - defender.defense)
    defender.take_damage(damage)
```

**Item Effects**:
```python
# entities.py:134 - If/else branches
def apply_item_effect(item: Item, target):
    if item.item_type == 'healing':
        heal_amount = HEALING_ITEMS.get(item.name, {}).get('heal', 0)
        target.heal(heal_amount)
    elif item.item_type == 'equipment':
        pass  # TODO
```

---

## Where Lua Would Touch

### 1. **Content Definition** (High Impact)

**Now**: Hardcoded Python dictionaries
**With Lua**: YAML data + Lua behavior scripts

**Example Future State**:
```yaml
# data/items/health_potion.yaml
id: health_potion
name: "Health Potion"
type: healing
stats:
  heal_amount: 10
  common: true
behavior: items/health_potion.lua
```

```lua
-- data/items/health_potion.lua
function on_use(item, target, game_state)
    local heal = item.stats.heal_amount

    -- Custom behavior: bonus heal if below 30% HP
    if target.hp / target.max_hp < 0.3 then
        heal = heal * 1.5
        game_state:add_message("Critical heal! Extra potent!")
    end

    target:heal(heal)
    game_state:add_message(string.format("Healed %d HP", heal))
end
```

---

### 2. **Monster AI** (High Impact)

**Now**: Simple pathfinding in Python
**With Lua**: Custom AI scripts per monster type

**Example Future State**:
```yaml
# data/monsters/goblin_shaman.yaml
id: goblin_shaman
name: "Goblin Shaman"
stats:
  hp: 8
  attack: 2
  defense: 1
ai_script: monsters/goblin_shaman.lua
```

```lua
-- data/monsters/goblin_shaman.lua
function take_turn(monster, game_state)
    local player = game_state.player
    local distance = game_state:distance(monster, player)

    -- Shaman stays at range 3-5, casts spells
    if distance < 3 then
        -- Too close! Retreat
        game_state:move_away_from(monster, player)
    elseif distance > 5 then
        -- Too far! Approach
        game_state:move_toward(monster, player)
    else
        -- Perfect range! Cast spell
        cast_spell(monster, player, game_state)
    end
end

function cast_spell(caster, target, game_state)
    -- 50% chance to heal ally or damage player
    if math.random() < 0.5 and has_wounded_ally(caster, game_state) then
        heal_weakest_ally(caster, game_state)
    else
        game_state:deal_damage(caster, target, caster.attack * 2)
        game_state:add_message("The shaman hurls a bolt of energy!")
    end
end
```

---

### 3. **Combat System** (Medium Impact)

**Now**: Direct damage calculation
**With Lua**: Hooks for abilities, special effects, status conditions

**Example Future State**:
```python
# game.py - Modified combat with hooks
def handle_combat(self, attacker, defender):
    # Calculate base damage (Python)
    damage = max(1, attacker.attack - defender.defense)

    # Pre-damage hook (Lua)
    if self.lua_bridge.has_script(attacker, "on_attack"):
        damage = self.lua_bridge.call(attacker, "on_attack", damage, defender)

    # Apply damage
    defender.take_damage(damage)

    # Post-damage hook (Lua)
    if self.lua_bridge.has_script(defender, "on_damaged"):
        self.lua_bridge.call(defender, "on_damaged", damage, attacker)
```

```lua
-- Vampire ability: heal on hit
function on_attack(damage, target)
    local heal_amount = math.floor(damage * 0.5)
    self:heal(heal_amount)
    game_state:add_message("Vampire drains " .. heal_amount .. " HP!")
    return damage  -- Return modified damage
end
```

---

### 4. **Crafting Recipes** (Medium Impact)

**Now**: YAML with Python formula evaluation (planned)
**With Lua**: Lua for complex crafting logic

**Example Future State**:
```yaml
# data/recipes/flaming_sword.yaml
id: flaming_sword
name: "Flaming Sword"
tier: legendary
required_ore: 3
ore_types: [mithril, fire_crystal]
crafting_script: recipes/flaming_sword.lua
```

```lua
-- data/recipes/flaming_sword.lua
function calculate_stats(ores, player_class)
    local base_damage = 10

    -- Ore contributions
    local hardness_avg = average(ores, "hardness")
    local purity_avg = average(ores, "purity")

    -- Base calculation
    local damage = base_damage + (hardness_avg * purity_avg / 100)

    -- Class bonuses
    if player_class == "Warrior" then
        damage = damage * 1.3
    end

    -- Special: Fire crystal bonus
    if has_ore_type(ores, "fire_crystal") then
        return {
            damage = damage,
            fire_damage = damage * 0.5,  -- +50% fire
            on_hit = "apply_burn_status"  -- Status effect!
        }
    end

    return {damage = damage}
end
```

---

### 5. **Event System** (High Impact)

**Now**: Direct function calls
**With Lua**: Event bus with Lua subscribers

**Example Future State**:
```python
# Event-driven architecture (supports Lua)
class GameEventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.lua_subscribers = defaultdict(list)

    def publish(self, event_type: str, data: dict):
        # Python subscribers
        for callback in self.subscribers[event_type]:
            callback(data)

        # Lua subscribers
        for lua_script in self.lua_subscribers[event_type]:
            self.lua_bridge.call_event_handler(lua_script, data)

# Usage
game.events.publish("monster_died", {
    "monster_id": "goblin_1",
    "killer": "player",
    "floor": 5
})
```

```lua
-- Custom content: Achievement system in Lua
function on_monster_died(event)
    -- Track goblin kills for achievement
    if event.monster_type == "goblin" then
        player_data.goblin_kills = player_data.goblin_kills + 1

        if player_data.goblin_kills == 100 then
            unlock_achievement("goblin_slayer")
            game_state:add_message("Achievement: Goblin Slayer!")
        end
    end
end

-- Register event handler
game:subscribe("monster_died", on_monster_died)
```

---

## 5 Key Architectural Decisions to Make NOW

### Decision 1: **Separate Data from Logic** (Do This Week!)

**Current Problem**: Content hardcoded in Python dictionaries (`entities.py:109-124`)

**Lua-Ready Solution**: Move to YAML + Python loaders NOW

**What to Change**:
```python
# ❌ NOW: Hardcoded
HEALING_ITEMS = {
    'health_potion': {'heal': 10, 'common': True},
}

# ✅ BETTER: YAML data files
# data/items/health_potion.yaml
id: health_potion
stats:
  heal_amount: 10
  common: true
# (No Lua script yet, but structure ready)
```

**Implementation**:
1. Create `data/items/`, `data/monsters/` directories
2. Write YAML schemas for items, monsters, recipes
3. Build Python loaders (week 1 work)
4. Future: Add `behavior_script: path/to/script.lua` field (trivial!)

**Effort**: 1-2 days
**Benefit**: When Lua comes, just add script path to YAML—no refactoring!

---

### Decision 2: **Plugin-Based Systems with Clean Interfaces** (Design Pattern)

**Current Problem**: Direct coupling (game.py calls entities.py directly)

**Lua-Ready Solution**: System interfaces with dependency injection

**What to Change**:
```python
# ❌ NOW: Direct calls
def apply_item_effect(item: Item, target):
    if item.item_type == 'healing':
        heal_amount = HEALING_ITEMS.get(item.name, {}).get('heal', 0)
        target.heal(heal_amount)

# ✅ BETTER: System interface
class ItemSystem:
    def apply_effect(self, item: Item, target, context: GameContext):
        # Try Lua handler first (future)
        if self.lua_bridge and self.lua_bridge.has_handler(item, "on_use"):
            return self.lua_bridge.call(item, "on_use", target, context)

        # Fall back to Python (now)
        return self._apply_python_effect(item, target)

    def _apply_python_effect(self, item: Item, target):
        # Same logic as before, but isolated
        if item.item_type == 'healing':
            target.heal(item.stats['heal_amount'])
```

**Benefits**:
- Python logic works now
- Lua hooks drop in seamlessly later
- Easy testing (mock the system)
- Can mix Lua and Python items

**Effort**: Design pattern (no extra code)
**Benefit**: Lua integration is 1-line change per system

---

### Decision 3: **Event Bus Architecture** (Critical for Multiplayer Anyway!)

**Current Problem**: Direct function calls everywhere

**Lua-Ready Solution**: Internal event bus (needed for multiplayer Phase 2 anyway!)

**What to Change**:
```python
# ❌ NOW: Direct coupling
def handle_combat(self, attacker, defender):
    damage = max(1, attacker.attack - defender.defense)
    defender.take_damage(damage)
    if isinstance(defender, Monster) and not defender.is_alive:
        self.state.add_message(f"You killed the {defender.name}!")

# ✅ BETTER: Event-driven
def handle_combat(self, attacker, defender):
    damage = max(1, attacker.attack - defender.defense)
    defender.take_damage(damage)

    # Publish events (Python subscribers now, Lua later)
    self.events.publish("entity_damaged", {
        "attacker": attacker,
        "defender": defender,
        "damage": damage
    })

    if not defender.is_alive:
        self.events.publish("entity_died", {
            "entity": defender,
            "killer": attacker
        })
```

**Why This Matters**:
- **Multiplayer needs events anyway** (NATS messages in Phase 2)
- Lua scripts subscribe to events naturally
- Achievement system, quest system, etc. all plug in
- No refactoring when adding Lua—just new subscribers

**Effort**: 2-3 days to build event bus
**Benefit**: Multiplayer ready + Lua ready + plugin architecture

---

### Decision 4: **Stateless Utility Functions** (Function Design)

**Current Problem**: Methods tied to Game class

**Lua-Ready Solution**: Extract pure functions that Lua can call

**What to Change**:
```python
# ❌ NOW: Method on Game class
class Game:
    def handle_monster_turns(self):
        for monster in self.state.monsters:
            dx = self.state.player.x - monster.x
            # ... inline logic

# ✅ BETTER: Separate AI module with utilities
# src/core/ai_utils.py
def distance_to(entity_a, entity_b) -> float:
    dx = entity_b.x - entity_a.x
    dy = entity_b.y - entity_a.y
    return math.sqrt(dx*dx + dy*dy)

def move_toward(entity, target) -> tuple[int, int]:
    # Returns (dx, dy) to move toward target
    ...

def is_adjacent(entity_a, entity_b) -> bool:
    return abs(entity_a.x - entity_b.x) <= 1 and \
           abs(entity_a.y - entity_b.y) <= 1

# game.py - Uses utilities
class Game:
    def handle_monster_turns(self):
        for monster in self.state.monsters:
            if is_adjacent(monster, self.state.player):
                self.handle_combat(monster, self.state.player)
            else:
                dx, dy = move_toward(monster, self.state.player)
                # ...
```

**Why This Matters**:
- Lua scripts can call `game_state:distance_to(monster, player)`
- Pure functions are testable
- Reusable across Python and Lua
- Clear API surface

**Effort**: Refactor as you build (no extra time)
**Benefit**: Clean Lua API surface automatically

---

### Decision 5: **Content Schema Versioning** (Data Format)

**Current Problem**: No versioning on data structures

**Lua-Ready Solution**: Add version field to all YAML

**What to Change**:
```yaml
# ✅ Add to all YAML files from day 1
version: "1.0"
id: health_potion
# ... rest of content

# Future: Lua support
version: "2.0"  # Signals "has Lua script"
id: advanced_potion
behavior_script: items/advanced_potion.lua
```

**Why This Matters**:
- Can evolve schema without breaking old content
- Loader knows which parser to use
- `version: "1.0"` = Python-only, `version: "2.0"` = Lua-enabled
- Community content can specify compatibility

**Effort**: 0 extra time (just add one field)
**Benefit**: Smooth schema migration path

---

## What You DON'T Need to Do Now

### ❌ Don't: Embed a Lua interpreter yet
- Adds dependency complexity
- Slows iteration speed
- Premature optimization

### ❌ Don't: Design Lua API yet
- You don't know what API you'll need
- Implement features first, extract API later
- Let usage patterns emerge naturally

### ❌ Don't: Write sandboxing code
- Security is Phase 3 concern (player content)
- Your own Lua scripts are trusted
- YAGNI (You Ain't Gonna Need It)

### ❌ Don't: Rewrite working code
- Keep your existing game loop
- Add abstractions as you build NEW systems
- Refactor opportunistically, not proactively

---

## Timeline & Integration Path

### MVP Phase (Now - Next 6 Weeks)

**Week 1-2: Mining System**
- ✅ Move item data → YAML (Decision 1)
- ✅ Build `ItemSystem` with clean interface (Decision 2)
- ✅ Extract utility functions as you build (Decision 4)

**Week 3: Crafting System**
- ✅ Recipe YAML format (ready for Lua scripts later)
- ✅ Python formula evaluator (simple expressions)
- ✅ Version field on all schemas (Decision 5)

**Week 4: Meta-Progression**
- ✅ Event bus for achievements (Decision 3)
- ✅ Legacy Vault as event subscriber
- ✅ Statistics tracking via events

**Result**: Lua-ready architecture, zero Lua code

---

### Phase 2: Multiplayer (6-12 Weeks Later)

**Week 1-2: Messaging**
- ✅ Event bus → NATS pub/sub (already event-driven!)
- ✅ Internal events work identically
- ✅ No game logic changes

**Week 3-4: State Sync**
- Continue using event architecture
- NATS carries events to clients

**Result**: Lua still not needed, but architecture supports it

---

### Phase 3: Advanced Content (12+ Weeks)

**Week 1: Lua Integration**
- Install `lupa` (Python-Lua bridge)
- Add Lua script loading to content loaders
- Implement 5-10 Lua API functions (`game_state:add_message()`, etc.)

**Week 2: First Lua Content**
- Port 1-2 Python items to Lua (proof of concept)
- Advanced AI script for boss monster
- Custom recipe logic

**Week 3: Mixed Content**
- Python content keeps working (backward compat)
- Lua content co-exists
- Gradual migration (not forced)

**Result**: Lua drops in seamlessly, no refactoring

---

## Concrete Example: Mining System (Next Week!)

### How to Build Lua-Ready from Day 1

**Task 1.1: Ore Vein Generation** (from MVP roadmap)

#### ❌ Lua-Hostile Approach
```python
# entities.py
class OreVein:
    def __init__(self, ore_type: str):
        self.ore_type = ore_type
        self.properties = self._generate_properties()

    def _generate_properties(self):
        # Hardcoded logic inline
        if self.ore_type == "copper":
            return {"hardness": random.randint(20, 50), ...}
        elif self.ore_type == "iron":
            return {"hardness": random.randint(40, 70), ...}
```

#### ✅ Lua-Ready Approach
```yaml
# data/ores/copper.yaml
version: "1.0"
id: copper
name: "Copper Ore"
spawn_floors: [1, 2, 3]
properties:
  hardness: {min: 20, max: 50}
  conductivity: {min: 30, max: 60}
  # ...
jackpot_chance: 0.05
# Future: generation_script: ores/copper.lua
```

```python
# src/core/ore_system.py
class OreSystem:
    def __init__(self):
        self.ore_types = self._load_ore_types()

    def _load_ore_types(self):
        # Load from YAML (Decision 1)
        return yaml_loader.load_all("data/ores/")

    def generate_vein(self, ore_type_id: str) -> OreVein:
        ore_data = self.ore_types[ore_type_id]

        # Future: Try Lua generator first
        # if ore_data.get("generation_script"):
        #     return self.lua_bridge.call(ore_data["generation_script"], ore_data)

        # Fall back to Python (now)
        return self._generate_python(ore_data)

    def _generate_python(self, ore_data: dict) -> OreVein:
        # Same logic, but isolated and replaceable
        properties = {}
        for prop, ranges in ore_data["properties"].items():
            properties[prop] = random.randint(ranges["min"], ranges["max"])

        # Jackpot check
        if random.random() < ore_data["jackpot_chance"]:
            properties = {k: min(100, v + 30) for k, v in properties.items()}

        return OreVein(ore_data["id"], properties)
```

**Future Lua Script** (drops in trivially):
```lua
-- data/ores/special_mithril.lua
function generate_vein(ore_data, floor_depth)
    local properties = {}

    -- Custom logic: Mithril quality scales with depth
    local depth_bonus = floor_depth * 2

    for prop_name, ranges in pairs(ore_data.properties) do
        local base = math.random(ranges.min, ranges.max)
        properties[prop_name] = math.min(100, base + depth_bonus)
    end

    -- Special: Mithril in even-numbered rooms is purer
    if game_state.current_room_id % 2 == 0 then
        properties.purity = math.min(100, properties.purity * 1.2)
        game_state:add_message("This mithril vein shimmers with unusual purity!")
    end

    return properties
end
```

**Key Point**: Week 1 code (YAML + Python) and Week 50 code (YAML + Lua) use THE SAME ARCHITECTURE!

---

## The Lua Integration Checklist

When you're ready to add Lua (Phase 3), this is the work:

### Step 1: Install Bridge (1 day)
```bash
pip install lupa  # Python-Lua bridge
```

### Step 2: Add LuaBridge Class (2 days)
```python
class LuaBridge:
    def __init__(self):
        from lupa import LuaRuntime
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self._register_api()

    def _register_api(self):
        # Expose Python functions to Lua
        self.lua.globals().game_state = self._build_game_state_api()

    def call(self, script_path: str, function_name: str, *args):
        script = self._load_script(script_path)
        return script[function_name](*args)
```

### Step 3: Add Script Paths to YAML (1 hour)
```yaml
# Just add one field!
behavior_script: items/health_potion.lua
```

### Step 4: Hook into Systems (1 day)
```python
# Already designed with clean interfaces!
class ItemSystem:
    def apply_effect(self, item, target, context):
        if item.behavior_script:  # New!
            return self.lua_bridge.call(item.behavior_script, "on_use", target, context)
        return self._apply_python_effect(item, target)  # Existing code!
```

**Total Effort**: 4-5 days
**Effort if you DIDN'T design for it**: 3-4 weeks (refactor everything!)

---

## Recommendations Summary

### Do This Week (MVP Week 1-2):
1. ✅ **Move to YAML data files** (items, monsters, recipes)
2. ✅ **Build system classes** with clean interfaces (ItemSystem, OreSystem, etc.)
3. ✅ **Add version field** to all YAML schemas
4. ✅ **Extract utility functions** (distance_to, is_adjacent, etc.)

### Do This Month (MVP Week 3-4):
5. ✅ **Build internal event bus** (needed for multiplayer anyway!)
6. ✅ **Use events for achievements**, statistics, quest triggers

### Don't Do Yet:
- ❌ Install Lua interpreter
- ❌ Design Lua API
- ❌ Write any .lua files
- ❌ Build sandboxing

### Future (Phase 3, Week 1 of Lua):
- Install lupa
- Add LuaBridge class (100 lines)
- Hook into existing systems (10 lines each)
- Write first Lua script (prove it works)

---

## Cost/Benefit Analysis

### If You Design Lua-Ready NOW:

**Extra Effort**: 0-2 days
- YAML migration: Already planned (recipes need it)
- System classes: Good design regardless
- Event bus: Needed for multiplayer Phase 2 anyway
- Utility functions: Makes testing easier too

**Benefits**:
- Lua drops in trivially (4-5 days, not 3-4 weeks)
- Better architecture even without Lua
- Multiplayer refactor easier (event-driven)
- Community content possible (Phase 4)

### If You DON'T Design Lua-Ready:

**Savings**: 1-2 days (skip YAML migration? Bad idea anyway)

**Future Cost**:
- 3-4 weeks refactoring when Lua needed
- Break existing content (YAML migration forces content rewrite)
- Multiplayer harder (tight coupling)
- Technical debt accumulates

**Verdict**: Designing Lua-ready NOW is **net positive** even if you never use Lua!

---

## Architecture Principles (General Wisdom)

### The YAGNI Balance

**YAGNI (You Ain't Gonna Need It)** says: Don't build features you don't need.

**BUT**: "Good architecture" ≠ "building features"

**Good architecture IS**:
- ✅ Separating data from logic (makes content iteration faster NOW)
- ✅ Clean interfaces (makes testing easier NOW)
- ✅ Event bus (needed for multiplayer anyway)
- ✅ Utility functions (reduces code duplication NOW)

**Over-engineering is**:
- ❌ Building Lua interpreter integration before you need it
- ❌ Designing Lua API before you know what you need
- ❌ Writing sandboxing code for untrusted scripts (not needed yet)

**The Rule**: Make decisions that improve your code TODAY, with the side effect of enabling Lua tomorrow.

---

## Final Recommendation

**Verdict**: Make 5 architectural decisions this week that cost almost nothing but save weeks later:

1. **YAML data files** (do anyway for recipes)
2. **System classes** (better design regardless)
3. **Event bus** (need for multiplayer Phase 2)
4. **Utility functions** (cleaner code now)
5. **Version fields** (5 seconds per file)

**Don't** install Lua, write Lua API, or write any .lua files yet.

**Result**: When Lua is needed (Phase 3), integration is 4-5 days instead of 3-4 weeks.

**Best Part**: Even if you never add Lua, you'll have better architecture!

---

## Questions to Consider

### 1. Do you expect player-created content?
- **Yes** → Definitely need Lua (sandboxed scripting)
- **No** → Maybe not needed (Python modding could work)

### 2. How complex will monster AI get?
- **Simple** (move toward, flee, patrol) → Python is fine
- **Complex** (coordinated tactics, boss phases) → Lua helps iteration

### 3. Will designers iterate on content?
- **Yes** → Lua lets them tweak without programmer help
- **No** → Python is fine (programmers make changes)

### 4. How important is modding/community?
- **Critical** → Lua is standard for game modding
- **Nice to have** → Could use Python + sandboxing
- **Not important** → Skip Lua entirely

### 5. Are you building a platform or a game?
- **Platform** (Brogue is foundation for many games) → Lua essential
- **Game** (Brogue is one specific game) → Lua optional

---

## Next Steps

1. **Decide**: Review this analysis with your team
2. **Commit**: Choose to design Lua-ready or not (both valid!)
3. **Act**: If yes, implement 5 decisions during Week 1-2 work
4. **Document**: Add "Lua Integration Path" to architecture docs
5. **Revisit**: Check decision at end of MVP (did it help?)

---

**Document Status**: ✅ Complete Analysis

**Strategic Significance**: 8/10 - Architectural decision with long-term impact

**Recommendation**: Implement 5 Lua-ready decisions during MVP Week 1-2 (mining system work)

---

**Files Referenced**:
- `docs/architecture/00_ARCHITECTURE_OVERVIEW.md:97-98` (Lua mentioned)
- `src/core/entities.py` (current hardcoded content)
- `src/core/game.py` (current game loop, combat, AI)
- `docs/MVP_ROADMAP.md` (Week 1-2 tasks)

**For Implementation**:
- Start with Task 1.1 (Ore Vein Generation) using Lua-ready approach
- Create `data/ores/` with YAML schemas
- Build `OreSystem` class with clean interface
- Add event bus during Week 3-4 work

🎮 **Build for tomorrow, code for today.**
