# Veinborn Architectural Assessment

> **Historical note (2026-11-11):** this document was written when a Lua scripting layer was planned. Lua was built and then removed (ADR-018 in `DECISIONS.md`); content is now extended in Python via registries (see [../EXTENDING.md](../EXTENDING.md)). References to Lua below describe the old plan and are kept for history.

**Document Type:** Architectural Analysis
**Audience:** Architects, Lead Developers
**Status:** Active. Section "Current Assessment (2026-11-12)" is verified against the code; the sections after it are the 2026-01 analysis, kept for history and annotated where they no longer hold.
**Last Updated:** 2026-11-12 (current assessment); 2026-01-13 (consolidated from COMPREHENSIVE_ANALYSIS.md dated 2025-11-06)
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
- ~~`LUA_INTEGRATION_STRATEGY.md`~~ (removed with Lua; see ADR-018)
- `00_ARCHITECTURE_OVERVIEW.md` - High-level architecture

---

## Current Assessment (2026-11-12)

Measured with reveal on `src/` (106 Python files, ~15.8k code lines). Re-run these to refresh:

```bash
reveal overview://src/                        # components, fan-in, import cycles
reveal 'imports://src/?components'            # cohesion per component
reveal metrics src/ --hotspots                # riskiest files
reveal 'ast://src/?type=function&complexity>12&sort=-complexity'
reveal check src/                             # rule findings (see false positives below)
```

### Structure (healthy)
- No import cycles, no unused imports. `core` never imports `ui` or `server` (layering holds).
- Most-imported files are the small stable base: `core/base/action.py`, `core/base/entity.py`, `core/extensions.py`, `core/base/game_context.py`.
- Single-player (`core/game.py`) and multiplayer (`server/game_session/session.py`) share outcome handling through `core/action_pipeline.process_action_outcome`.
- Content is registered, not hardcoded: `core/content/` is auto-imported (`load_content`) and registers AI behaviours, abilities, event handlers and item effects through `core/extensions.py` (ADR-018). `reveal check` reports these modules as "not imported anywhere" (M102): a false positive, they are loaded by name.
- The event bus is live (`EventBus`, `install_event_handlers`); combat, damage and hit formulas are data in `data/balance/formulas.yaml`.

### Known weaknesses
- **Process singletons remain**: `GameRNG`, `LootGenerator`, `HighScoreManager`, `ConfigManager`. Per-game randomness must come from `context.get_rng()` (VB-18); a call that omits its `rng` argument falls back to the global stream, which a loaded save or a multiplayer game does not use. Game-over scoring still calls `HighScoreManager` directly from `turn_processor` and `floor_manager` rather than through events.
- **User preferences drive gameplay**: autopickup reads `ConfigManager` (`~/.veinbornrc`). Bots and tests pin built-in defaults with `ConfigManager.use_defaults()` (VB-76); the multiplayer server still applies its host's file to every player.
- **Complexity concentrates in a few functions**: `server/state_delta.compute_delta` (VB-26; deleted 2026-11-14 with the delta path, VB-98), `ui/multiplayer_client._handle_message`, `ui/textual/widgets/sidebar.render_content`, `core/systems/ai_system.abilities_for` (scored high by `or {}` defaults; short and readable, left as is).

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

*(2026-01 list. Since then hit and damage moved to `data/balance/formulas.yaml` and spawn bands to `monster_spawns.yaml` (floor_bands); check the code before acting on the rest.)*

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

## Architectural Weaknesses (2026-01, historical)

Status as of 2026-11-12: 1, 2 and 4 are resolved (event bus and content registries exist); 3 is partly resolved (spawn bands and counts are YAML, BSP is still code); 5 still holds (see Current Assessment).

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

## State as of 2026-04-17 (historical)

**Test Coverage** (then): 1067 tests collected; 1065 passing / 0 failing / 2 skipped (verified after commit 33d72f7)

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
- [../EXTENDING.md](../EXTENDING.md) - How content is extended in Python today
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
