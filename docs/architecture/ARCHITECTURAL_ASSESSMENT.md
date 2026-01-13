# Veinborn Architectural Assessment

**Document Type:** Architectural Analysis
**Audience:** Architects, Lead Developers
**Status:** Active
**Last Updated:** 2026-01-13 (consolidated from COMPREHENSIVE_ANALYSIS.md dated 2025-11-06)
**Source:** Extracted from archived comprehensive analysis

---

## Overview

This document provides architectural assessment of the Veinborn codebase, covering:
- Coupling analysis (tight vs loose coupling patterns)
- Data-driven vs hardcoded design decisions
- Extensibility points for scripting integration
- Architectural strengths and weaknesses
- Recommendations for improvement

**Companion documents:**
- `BASE_CLASS_ARCHITECTURE.md` - Core design patterns
- `LUA_INTEGRATION_STRATEGY.md` - Scripting integration plans
- `00_ARCHITECTURE_OVERVIEW.md` - High-level architecture

---

## Table of Contents

1. [Coupling Analysis](#coupling-analysis)
2. [Data vs Code Analysis](#data-vs-code-analysis)
3. [Extensibility & Scripting Points](#extensibility--scripting-points)
4. [Architectural Strengths](#architectural-strengths)
5. [Architectural Weaknesses](#architectural-weaknesses)
6. [Recommendations for Improvement](#recommendations-for-improvement)

---

## Coupling Analysis

### Tight Coupling (Issues)

**1. ActionFactory ↔ Specific Action Classes**
```python
# In action_factory.py
from .move_action import MoveAction
from .attack_action import AttackAction
from .mine_action import MineAction
...

# To add new action, must modify ActionFactory
```
**Impact:** Medium - Factory pattern alleviates this somewhat
**Solution:** Dynamic action registration (already supports via `register_handler()`)

**2. TurnProcessor ↔ HighScoreManager + LegacyVault**
```python
def _check_game_over():
    self._record_high_score()      # Tight coupling
    self._save_legacy_ore()        # Tight coupling
    self._record_defeat()          # Tight coupling
```
**Impact:** Low - These are game-over side effects
**Solution:** Event system would decouple (Phase 2)

**3. Game ↔ All Subsystems**
```python
# game.py creates and owns everything
self.spawner = EntitySpawner(...)
self.turn_processor = TurnProcessor(...)
self.floor_manager = FloorManager(...)
self.action_factory = ActionFactory(...)
```
**Impact:** Low - This is the orchestrator pattern
**Solution:** Dependency injection works fine

**4. AttackAction ↔ LootGenerator**
```python
# Direct instantiation
loot = LootGenerator.get_instance().generate_loot(...)
```
**Impact:** Low - Singleton pattern makes this reasonable
**Solution:** Could pass via GameContext

**5. EntityLoader ↔ YAML file paths**
```python
# Hardcoded path
entities_path = project_root / "data" / "entities"
```
**Impact:** Low - Configurable via parameter
**Solution:** Already supports custom paths

### Loose Coupling (Strengths)

**GameContext:** All systems use this, not GameState directly
**ActionOutcome:** Systems don't need to know about each other's results
**SystemInterface:** Systems are registered, not hardcoded
**Entity IDs:** Actions reference entities by ID, not object references

---

## Data vs Code Analysis

### What's Data-Driven (GOOD)

```
✅ Monster definitions         → data/entities/monsters.yaml
✅ Ore type definitions        → data/entities/ores.yaml
✅ Item definitions            → data/entities/items.yaml
✅ Crafting recipes            → data/balance/recipes.yaml
✅ Loot tables                 → data/balance/loot_tables.yaml
✅ Monster spawn rates          → data/balance/monster_spawns.yaml
✅ Forge definitions           → data/balance/forges.yaml
✅ Game constants              → data/balance/game_constants.yaml (config_loader)
```

### What's Hardcoded (NEEDS ATTENTION)

```
❌ BSP dungeon generation      → world.py (algorithm hardcoded)
❌ Damage calculation          → attack_action.py (formula hardcoded)
❌ Monster count per floor     → entity_spawner.py (logic hardcoded)
❌ Spawn position logic        → entity_spawner.py (hardcoded)
❌ Room type distribution      → entity_spawner.py (hardcoded)
❌ Turn length                 → constants.py (could be data)
❌ HP regeneration rate        → turn_processor.py (hardcoded)
❌ Equipment bonus calculation → crafting.py (uses formulas, partially data-driven)
```

### Magic Numbers in Code

**Examples:**
```python
# constants.py
PLAYER_STARTING_HP = 20
PLAYER_STARTING_ATTACK = 5
PLAYER_STARTING_DEFENSE = 2

GOBLIN_HP = 6
GOBLIN_ATTACK = 3
GOBLIN_DEFENSE = 1

MINING_MIN_TURNS = 3
MINING_MAX_TURNS = 5

HP_REGEN_INTERVAL_TURNS = 10
HP_REGEN_AMOUNT = 1

# Should these be in game_constants.yaml?
```

**Recommendation:** Consider moving these to `data/balance/game_constants.yaml` for easier balance tuning.

---

## Extensibility & Scripting Points

### Where Lua Would Fit Naturally

**Tier 1 - Immediate Integration (100% compatible):**

1. **Custom Actions** - Register new action types
   ```lua
   -- custom_spell.lua
   local action = veinborn.actions.CustomSpell()
   action:validate(context)  -- returns boolean
   action:execute(context)   -- returns ActionOutcome
   ```

2. **AI Behaviors** - Custom monster AI
   ```lua
   -- troll_ai.lua
   function aggressive_with_retreat(monster, player)
       if monster.hp < monster.max_hp / 2 then
           -- Flee behavior
       else
           -- Attack behavior
       end
   end
   ```

3. **Item/Recipe Creation** - Extend crafting
   ```lua
   -- legendary_recipe.lua
   veinborn.recipes.register('legendary_sword', {
       requirements = { ore_type = 'adamantite', count = 3 },
       stat_formulas = {
           attack_bonus = 'hardness * 0.5 + purity * 0.3'
       }
   })
   ```

4. **Dungeon Generators** - Custom map generation
   ```lua
   -- dungeon_generator.lua
   function generate_floor(floor_number)
       local map = veinborn.Map.new(80, 24)
       -- Custom generation logic
       return map
   end
   ```

**Tier 2 - Medium Integration (requires minor refactoring):**

1. **Event Handlers** - Respond to game events
   ```lua
   veinborn.events:on('entity_died', function(event)
       -- Handle entity death
   end)
   ```

2. **Game Over Hooks** - Custom end-of-game logic
   ```lua
   veinborn.game:on_game_over(function(game_state)
       -- Custom scoring
   end)
   ```

3. **Custom Systems** - Register new game systems
   ```lua
   local weather_system = veinborn.System.new()
   veinborn.context:register_system('weather', weather_system)
   ```

**Tier 3 - Complex Integration (requires architecture changes):**

1. **Complete Procedural Generation** - Replace BSP
2. **Multiplayer Synchronization** - Custom netcode
3. **Persistent World State** - Save/load hooks

### Current Extensibility Points

**ActionFactory:**
```python
# External code can add custom actions:
factory.register_handler('custom_action', ActionHandler(
    name='custom_action',
    create_fn=create_custom_action,
    description='A custom action'
))
```

**GameContext API:**
- All systems access game state through this interface
- Actions validate and execute through context
- Perfect bridge for Lua integration

**System Registration:**
```python
# Custom systems can be registered
context.register_system('custom_system', my_system)
```

---

## Architectural Strengths

1. **Clean Separation of Concerns**
   - GameState (data) ← GameContext (API) ← Actions/Systems
   - UI is completely decoupled
   - Easy to test each layer independently

2. **Action/Outcome Pattern**
   - All state changes go through actions
   - Outcomes are event-ready
   - Perfect for serialization (multiplayer, replay)
   - Natural fit for Lua integration

3. **Factory Pattern for Actions**
   - Open/Closed Principle
   - Easy to extend with custom actions
   - No hardcoded action types

4. **Data-Driven Design**
   - Entities, recipes, loot, spawning all use YAML
   - Easy for designers to modify
   - No code recompilation for balance changes

5. **Type-Safe**
   - Python 3.10+ with type hints
   - Entity types are enums
   - Action types are registered

6. **Testable**
   - Comprehensive fixtures in conftest.py
   - Systems can be tested in isolation
   - GameContext can be mocked
   - YAML data is version-controlled

7. **Well-Documented**
   - Code has docstrings
   - Architecture docs in place
   - Design decisions recorded

---

## Architectural Weaknesses

1. **Event System Missing**
   - Events are defined in ActionOutcome but not published
   - TurnProcessor has side effects (scoring, vault) not as events
   - **Note:** Event system architecture documented in `EVENT_SYSTEM.md` and `EVENTS_ASYNC_OBSERVABILITY_GUIDE.md`

2. **Limited AI Flexibility**
   - Only one AI type implemented
   - Would benefit from behavior registry

3. **Hardcoded Generation**
   - BSP dungeon generation not data-driven
   - Spawning logic has magic numbers

4. **No Reactive System**
   - Systems don't respond to events
   - Hard to add new behaviors without modifying core code

5. **Singleton Pattern Overuse**
   - LootGenerator, HighScoreManager use singletons
   - Could use dependency injection instead

---

## Recommendations for Improvement

### Immediate (Before Lua)

1. **Extract Event System**
   ```python
   # Create EventBus
   class EventBus:
       def publish(event: dict)
       def subscribe(event_type: str, handler: Callable)

   # TurnProcessor publishes events
   bus.publish({'type': 'entity_died', 'entity_id': ...})
   ```

2. **Move Magic Numbers to Data**
   ```yaml
   # game_constants.yaml
   combat:
     damage_variance: 2
   spawning:
     monsters_per_floor: [3, 8]
   ```

3. **Refactor Spawning**
   - Make monster/ore count configurable
   - Move to YAML configuration

### Before Multiplayer (Phase 2)

1. **Complete Event System**
   - All game changes as events
   - Handler registration
   - Event replaying for multiplayer

2. **Network Serialization**
   - Action serialization (already exists)
   - GameState serialization for sync

3. **Permission Model**
   - GameContext checks permissions
   - Multiplayer validation

### With Lua Integration

1. **API Stability**
   - Lock down GameContext interface
   - Version compatibility

2. **Sandbox Security**
   - Restrict Lua capabilities
   - Timeout protection

3. **Hot Reload**
   - Load/reload scripts without restart
   - Error recovery

---

## Current State (2026-01-13)

**Test Coverage**: 1063 tests, 100% pass rate

**Code Quality**:
- Complexity violations resolved (Phase 1-3 refactoring)
- Helper method pattern applied consistently
- Clean architecture maintained

**Recent Improvements**:
- Phase 3 refactoring (world.py: 60% nesting reduction)
- Regression fixes (constant imports restored)
- Documentation consolidation (this doc restored from archive)

---

## References

- [BASE_CLASS_ARCHITECTURE.md](./BASE_CLASS_ARCHITECTURE.md) - Core patterns
- [LUA_INTEGRATION_STRATEGY.md](./LUA_INTEGRATION_STRATEGY.md) - Scripting plans
- [EVENT_SYSTEM.md](./EVENT_SYSTEM.md) - Event architecture
- [00_ARCHITECTURE_OVERVIEW.md](./00_ARCHITECTURE_OVERVIEW.md) - High-level overview
- [RANDOMNESS_ANALYSIS.md](./RANDOMNESS_ANALYSIS.md) - RNG and seeding analysis

---

**Document Status**: Consolidated from archived COMPREHENSIVE_ANALYSIS.md (2025-11-06)
**Consolidation Date**: 2026-01-13
**Consolidation Session**: ultimate-blaster-0113
**Unique Content**: Coupling analysis, data vs code breakdown, extensibility assessment

---

*This document was extracted from archived documentation during the 2026-01-13 consolidation effort to preserve unique architectural insights not captured in other active documentation.*
