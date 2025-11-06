# Brogue Lua Integration - Phase 1: Foundation

**Date:** 2025-11-06
**Project:** Brogue Roguelike Game
**Target:** Lua scripting support for custom actions
**Timeline:** 1 week (6-8 hours focused work)
**Scope:** Phase 1 - Foundation + Custom Actions

---

## Executive Summary

Implement Lua scripting support for Brogue to enable modding and custom content creation. The architecture is **5/5 Lua-ready** with excellent foundations already in place:

- ✅ GameContext provides safe API facade
- ✅ ActionFactory supports dynamic registration via `register_handler()`
- ✅ Action/Outcome pattern is serializable and script-friendly
- ✅ Data-driven design (100% YAML-based configuration)
- ✅ Clean architecture with minimal coupling

**Phase 1 Goal:** Enable Lua scripts to register custom actions that integrate seamlessly with the game engine.

**Success Criteria:**
1. Lua runtime integrated with Python via mlua
2. GameContext API exposed to Lua with safety guarantees
3. Custom actions can be registered and executed from Lua
4. Example "Fireball" action works end-to-end
5. Comprehensive documentation and error handling
6. All 604 existing tests still pass

---

## Current Architecture State

### Excellent Foundations

**GameContext (src/core/base/game_context.py - 205 lines):**
- Safe API facade for game state access
- Entity queries: `get_entity()`, `get_entities_by_type()`, `get_entity_at()`
- Map queries: `is_walkable()`, `in_bounds()`, `get_map()`
- Game state: `get_turn_count()`, `get_floor()`, `add_message()`
- System registration: `register_system()`
- **Perfect for Lua exposure** - already designed as safe API

**ActionFactory (src/core/actions/action_factory.py - 403 lines):**
- Factory pattern for action creation
- **Already extensible**: `register_handler()` method exists
- Handlers defined as `ActionHandler(name, create_fn, description)`
- Used by Game class to create all actions
- **Perfect for Lua integration** - just need Lua-compatible handlers

**Action Pattern (src/core/base/action.py):**
- Base class: `validate()` → `execute()` → `ActionOutcome`
- Serializable via `to_dict()` / `from_dict()`
- Outcomes contain events for future pub/sub
- Type-safe with Python 3.10+ type hints
- **Perfect for Lua wrapping** - clear interface

**Current Actions (7 types):**
1. MoveAction - dx/dy movement
2. AttackAction - combat with target
3. MineAction - multi-turn ore mining
4. SurveyAction - inspect ore properties
5. CraftAction - forge + recipe crafting
6. EquipAction - equip items from inventory
7. DescendAction - stairs to next floor

### Project Health

**Tests:** 604 passing
**Architecture Quality:** 4.8/5 (Excellent)
**Lua Readiness:** 5/5 (Ready)
**Config Files:** 10 YAML files in `data/balance/`
**Working Directory:** Clean, all commits pushed

**Recent Work (November 2025):**
- PR #11: Spawning configuration (YAML-driven)
- PR #12: EventBus system (pub/sub ready)
- PR #13: AI behaviors + formulas (5 AI types)
- PR #14: Bot equipment intelligence
- PR #15: Dungeon generation configuration

**Current Branch:** `main`
**Repository:** `/home/scottsen/src/projects/brogue`

---

## Phase 1: Lua Integration Tasks

### Task 1: Lua Runtime Setup (2 hours)

**Goal:** Integrate mlua (Python-Lua bridge) and verify basic functionality

**Steps:**

1. **Add mlua dependency**
   ```bash
   # Add to requirements.txt
   echo "mlua==0.2.0" >> requirements.txt
   pip install mlua
   ```

2. **Create LuaRuntime wrapper** (`src/core/scripting/lua_runtime.py`)
   - Initialize mlua Lua instance
   - Set up sandbox environment (safe globals only)
   - Implement timeout protection (3 seconds max per script)
   - Add error handling and logging
   - Support script loading from `scripts/` directory

3. **Create basic tests** (`tests/unit/test_lua_runtime.py`)
   - Test Lua initialization
   - Test simple script execution (`return 2 + 2`)
   - Test timeout protection (infinite loop detection)
   - Test error handling (syntax errors, runtime errors)
   - Test sandbox (blocked access to `os`, `io`, etc.)

**Deliverables:**
- `src/core/scripting/lua_runtime.py` (~150 lines)
- `tests/unit/test_lua_runtime.py` (~100 lines)
- Updated `requirements.txt`
- All tests passing (604 → 610+)

**Implementation Notes:**
```python
# Example LuaRuntime structure
class LuaRuntime:
    def __init__(self):
        self.lua = mlua.Lua()
        self._setup_sandbox()

    def _setup_sandbox(self):
        # Remove dangerous globals
        self.lua.execute("os = nil; io = nil; load = nil")

    def execute_script(self, script: str, timeout: float = 3.0):
        # Execute with timeout protection
        pass

    def load_script_file(self, path: str):
        # Load from scripts/ directory
        pass
```

---

### Task 2: GameContext Lua API Bridge (2 hours)

**Goal:** Expose GameContext methods to Lua in a safe, typed manner

**Steps:**

1. **Create GameContextAPI wrapper** (`src/core/scripting/game_context_api.py`)
   - Wrap GameContext methods for Lua exposure
   - Convert Python objects → Lua tables
   - Convert Lua tables → Python objects
   - Handle Entity serialization (id, name, position, stats)
   - Provide simplified API for common queries

2. **Expose core methods to Lua:**
   ```lua
   -- Lua API examples
   local player = brogue.get_player()
   local entities = brogue.get_entities_in_range(x, y, radius)
   local entity = brogue.get_entity_at(x, y)
   local walkable = brogue.is_walkable(x, y)
   brogue.add_message("Hello from Lua!")
   ```

3. **Create entity table format:**
   ```lua
   -- Entity table format in Lua
   entity = {
       id = "player_1",
       name = "Player",
       x = 5,
       y = 10,
       hp = 50,
       max_hp = 100,
       entity_type = "PLAYER"
   }
   ```

4. **Create tests** (`tests/unit/test_game_context_api.py`)
   - Test entity serialization (Entity → Lua table)
   - Test API method calls from Lua
   - Test error handling (invalid coordinates, missing entities)
   - Test type conversions (Python ↔ Lua)

**Deliverables:**
- `src/core/scripting/game_context_api.py` (~200 lines)
- `tests/unit/test_game_context_api.py` (~120 lines)
- All tests passing (610+ → 620+)

**Implementation Notes:**
```python
class GameContextAPI:
    """Lua-safe wrapper for GameContext"""

    def __init__(self, context: GameContext, lua: mlua.Lua):
        self.context = context
        self.lua = lua
        self._register_api()

    def _register_api(self):
        # Register brogue.* methods in Lua
        brogue_table = self.lua.table()
        brogue_table["get_player"] = self._get_player
        brogue_table["get_entity_at"] = self._get_entity_at
        # ... more methods
        self.lua.globals()["brogue"] = brogue_table

    def _get_player(self) -> dict:
        player = self.context.get_player()
        return self._entity_to_lua(player)

    def _entity_to_lua(self, entity: Entity) -> dict:
        return {
            "id": entity.entity_id,
            "name": entity.name,
            "x": entity.x,
            "y": entity.y,
            "hp": entity.get_stat("hp"),
            "max_hp": entity.get_stat("max_hp"),
            "entity_type": entity.entity_type.name
        }
```

---

### Task 3: Lua Action Registration System (2 hours)

**Goal:** Enable Lua scripts to register custom actions via ActionFactory

**Steps:**

1. **Create LuaAction wrapper** (`src/core/actions/lua_action.py`)
   - Python Action subclass that executes Lua scripts
   - Calls Lua `validate(context)` function
   - Calls Lua `execute(context)` function
   - Converts ActionOutcome from Lua table → Python object
   - Handles errors gracefully (script crashes → failure outcome)

2. **Extend ActionFactory for Lua registration**
   - Add `register_lua_action(action_type, script_path)` method
   - Create ActionHandler that wraps LuaAction
   - Load Lua scripts from `scripts/actions/` directory
   - Validate script structure (must have validate + execute functions)

3. **Define Lua action template:**
   ```lua
   -- scripts/actions/example_action.lua

   -- Validate if action can be executed
   function validate(actor_id, params)
       -- Return true/false
       return true
   end

   -- Execute the action
   function execute(actor_id, params)
       local player = brogue.get_player()
       brogue.add_message("Lua action executed!")

       return {
           success = true,
           events = {},
           interrupted_action = nil
       }
   end
   ```

4. **Create tests** (`tests/unit/test_lua_action.py`)
   - Test LuaAction creation and execution
   - Test Lua script validation
   - Test error handling (missing functions, runtime errors)
   - Test ActionFactory integration
   - Test outcome conversion (Lua table → ActionOutcome)

**Deliverables:**
- `src/core/actions/lua_action.py` (~150 lines)
- Extended `src/core/actions/action_factory.py` (+50 lines)
- `tests/unit/test_lua_action.py` (~150 lines)
- All tests passing (620+ → 630+)

**Implementation Notes:**
```python
class LuaAction(Action):
    """Action implemented in Lua script"""

    def __init__(self, actor_id: str, action_type: str,
                 lua_runtime: LuaRuntime, script_path: str, **params):
        super().__init__(actor_id)
        self.action_type = action_type
        self.lua_runtime = lua_runtime
        self.script_path = script_path
        self.params = params

    def validate(self, context: GameContext) -> bool:
        # Call Lua validate() function
        api = GameContextAPI(context, self.lua_runtime.lua)
        result = self.lua_runtime.lua.globals()["validate"](
            self.actor_id, self.params
        )
        return bool(result)

    def execute(self, context: GameContext) -> ActionOutcome:
        # Call Lua execute() function
        api = GameContextAPI(context, self.lua_runtime.lua)
        outcome_table = self.lua_runtime.lua.globals()["execute"](
            self.actor_id, self.params
        )
        return self._table_to_outcome(outcome_table)
```

---

### Task 4: Example "Fireball" Action (1 hour)

**Goal:** Create working example of Lua custom action

**Steps:**

1. **Create Fireball action script** (`scripts/actions/fireball.lua`)
   - Area-of-effect damage action
   - Targets position (x, y) within range
   - Damages all entities in 2-tile radius
   - Uses mana cost (checks player mana stat)
   - Generates appropriate messages

2. **Register Fireball in game initialization**
   - Add script loading to Game class initialization
   - Register via ActionFactory: `factory.register_lua_action('fireball', 'scripts/actions/fireball.lua')`
   - Add to available actions list

3. **Create integration test** (`tests/integration/test_fireball_action.py`)
   - Test Fireball at monster (damages monster)
   - Test Fireball AOE (damages multiple monsters)
   - Test mana cost (fails if insufficient mana)
   - Test range validation (fails if too far)
   - Test message generation

**Deliverables:**
- `scripts/actions/fireball.lua` (~80 lines)
- `tests/integration/test_fireball_action.py` (~100 lines)
- Updated `src/core/game.py` (script loading, ~20 lines)
- All tests passing (630+ → 635+)

**Example Implementation:**
```lua
-- scripts/actions/fireball.lua

MANA_COST = 10
RANGE = 5
AOE_RADIUS = 2
BASE_DAMAGE = 15

function validate(actor_id, params)
    local player = brogue.get_player()
    local target_x = params.x
    local target_y = params.y

    -- Check mana
    if player.mana < MANA_COST then
        brogue.add_message("Not enough mana for Fireball!")
        return false
    end

    -- Check range
    local dx = target_x - player.x
    local dy = target_y - player.y
    local dist = math.sqrt(dx*dx + dy*dy)

    if dist > RANGE then
        brogue.add_message("Target too far away!")
        return false
    end

    return true
end

function execute(actor_id, params)
    local player = brogue.get_player()
    local target_x = params.x
    local target_y = params.y

    -- Deduct mana
    brogue.modify_stat(actor_id, "mana", -MANA_COST)

    -- Get entities in AOE
    local targets = brogue.get_entities_in_range(target_x, target_y, AOE_RADIUS)

    local events = {}
    for _, target in ipairs(targets) do
        if target.entity_type == "MONSTER" then
            -- Damage calculation
            local damage = BASE_DAMAGE

            -- Deal damage
            brogue.modify_stat(target.id, "hp", -damage)

            table.insert(events, {
                type = "damage",
                target_id = target.id,
                amount = damage,
                source = "fireball"
            })

            brogue.add_message(string.format(
                "Fireball hits %s for %d damage!",
                target.name, damage
            ))
        end
    end

    return {
        success = true,
        events = events,
        interrupted_action = nil
    }
end
```

---

### Task 5: Documentation & Error Handling (1 hour)

**Goal:** Comprehensive documentation for Lua modders

**Steps:**

1. **Create Lua API documentation** (`docs/LUA_API.md`)
   - Overview of Lua integration
   - GameContext API reference (`brogue.*` functions)
   - Action registration guide
   - Entity table format specification
   - ActionOutcome format specification
   - Example actions (Fireball, Teleport, Heal)
   - Error handling best practices

2. **Create Lua modding guide** (`docs/LUA_MODDING_GUIDE.md`)
   - Getting started (script structure)
   - Action template walkthrough
   - Testing custom actions
   - Debugging tips
   - Common pitfalls and solutions
   - Integration with game systems

3. **Add error handling improvements**
   - Wrap all Lua calls in try/catch
   - Log Lua errors to game log + Python logger
   - Provide helpful error messages to modders
   - Add script validation on load (syntax check)
   - Add function existence checks (validate + execute required)

4. **Create action template** (`scripts/actions/_template.lua`)
   - Boilerplate Lua action structure
   - Heavily commented
   - Example parameter usage
   - Example outcome generation

**Deliverables:**
- `docs/LUA_API.md` (~400 lines)
- `docs/LUA_MODDING_GUIDE.md` (~300 lines)
- `scripts/actions/_template.lua` (~60 lines)
- Enhanced error handling in LuaRuntime and LuaAction

---

### Task 6: Integration & Testing (1 hour)

**Goal:** Ensure Lua integration doesn't break existing functionality

**Steps:**

1. **Run full test suite**
   ```bash
   cd /home/scottsen/src/projects/brogue
   pytest -v
   ```
   - Verify all 604 original tests still pass
   - Verify new Lua tests pass (~30+ new tests)
   - Check test coverage (should be >80%)

2. **Manual testing**
   ```bash
   python3 run_textual.py
   ```
   - Play the game normally (move, attack, mine)
   - Verify no regressions in existing actions
   - Test Fireball action (if UI integration exists)
   - Check logs for Lua errors

3. **Performance testing**
   - Run bot stress test (5k turns)
   - Verify Lua overhead is minimal (<5% performance impact)
   - Check memory usage (no Lua memory leaks)

4. **Create integration example**
   - Add Fireball to bot behavior (optional)
   - Demonstrate action factory registration
   - Show working end-to-end flow

**Deliverables:**
- All tests passing (634+ tests total)
- Performance benchmark results
- Clean test output with no warnings
- Working integration demonstration

---

## Technical Requirements

### Dependencies

```txt
# Add to requirements.txt
mlua==0.2.0
```

**Why mlua?**
- Lightweight Python-Lua bridge
- Supports Lua 5.4 (latest)
- Type conversions (Python ↔ Lua)
- Timeout support
- Active maintenance

### Safety Guarantees

**Sandbox Restrictions:**
- ❌ No file I/O (`io.*` removed)
- ❌ No OS access (`os.*` removed)
- ❌ No dynamic code loading (`load`, `loadfile` removed)
- ❌ No coroutines (can bypass timeout)
- ✅ Math library allowed
- ✅ String library allowed
- ✅ Table library allowed

**Timeout Protection:**
- 3 second max execution per script
- Prevents infinite loops
- Configurable timeout per action

**Error Handling:**
- All Lua errors caught and logged
- Script errors don't crash game
- Helpful error messages for modders
- Validation on script load (syntax check)

### File Structure

```
brogue/
├── src/
│   └── core/
│       ├── scripting/              # NEW
│       │   ├── __init__.py
│       │   ├── lua_runtime.py      # Lua engine wrapper
│       │   └── game_context_api.py # GameContext → Lua bridge
│       └── actions/
│           └── lua_action.py       # NEW - Lua action wrapper
│
├── scripts/                        # NEW
│   └── actions/
│       ├── _template.lua           # Action template
│       └── fireball.lua            # Example action
│
├── docs/
│   ├── LUA_API.md                  # NEW - API reference
│   └── LUA_MODDING_GUIDE.md        # NEW - Modding guide
│
└── tests/
    ├── unit/
    │   ├── test_lua_runtime.py     # NEW
    │   ├── test_game_context_api.py # NEW
    │   └── test_lua_action.py      # NEW
    └── integration/
        └── test_fireball_action.py # NEW
```

---

## Success Criteria

### Must Have (Phase 1)

✅ **Lua runtime integrated**
- mlua working with Python 3.10+
- Sandbox configured (no dangerous globals)
- Timeout protection (3 seconds)
- Error handling (script errors don't crash game)

✅ **GameContext API exposed to Lua**
- `brogue.get_player()` - get player entity
- `brogue.get_entity_at(x, y)` - get entity at position
- `brogue.get_entities_in_range(x, y, radius)` - get nearby entities
- `brogue.is_walkable(x, y)` - check walkability
- `brogue.add_message(text)` - add game message
- `brogue.modify_stat(entity_id, stat, delta)` - modify entity stats

✅ **Custom actions working**
- ActionFactory supports Lua action registration
- LuaAction executes Lua scripts
- Lua scripts can validate and execute actions
- ActionOutcome properly converted from Lua tables

✅ **Example "Fireball" action**
- Validates mana cost and range
- Deals AOE damage to monsters
- Generates appropriate events
- Works with existing game systems

✅ **Documentation complete**
- Lua API reference (`docs/LUA_API.md`)
- Modding guide (`docs/LUA_MODDING_GUIDE.md`)
- Action template (`scripts/actions/_template.lua`)

✅ **Tests passing**
- All 604 original tests still pass
- 30+ new Lua tests added and passing
- Integration tests demonstrate end-to-end flow

### Nice to Have (Future Phases)

⚠️ **Phase 2 - AI Behaviors:**
- Register custom AI behaviors in Lua
- Behavior function interface (`update(monster, context)`)
- AI registry system

⚠️ **Phase 3 - Event System:**
- Event bus integration with Lua
- Event handlers in Lua scripts
- Subscribe/publish pattern

⚠️ **Phase 4 - Hot Reload:**
- Reload Lua scripts without restarting game
- Script file watching
- Error recovery

---

## Implementation Strategy

### Day 1: Foundation (2 hours)
- Task 1: Lua runtime setup
- Basic tests and sandbox configuration

### Day 2: API Bridge (2 hours)
- Task 2: GameContext Lua API
- Entity serialization and API exposure

### Day 3: Action System (2 hours)
- Task 3: Lua action registration
- ActionFactory integration

### Day 4: Example & Documentation (2 hours)
- Task 4: Fireball action
- Task 5: Documentation
- Task 6: Integration testing

### Total: 8 hours focused work

---

## Testing Strategy

### Unit Tests (Fast, isolated)
- `test_lua_runtime.py` - Runtime initialization, sandbox, timeout
- `test_game_context_api.py` - API methods, serialization, type conversion
- `test_lua_action.py` - Action validation, execution, outcome conversion

### Integration Tests (Slow, full stack)
- `test_fireball_action.py` - End-to-end Fireball action
- Verify action factory registration
- Verify game state changes
- Verify event generation

### Manual Tests
- Play the game normally
- Execute custom Lua actions
- Check logs for errors
- Verify performance

---

## Risk Mitigation

### Risk 1: mlua Installation Issues
**Mitigation:** Test on Python 3.10+ first, provide fallback instructions for building from source

### Risk 2: Performance Overhead
**Mitigation:** Benchmark Lua execution time, optimize hot paths, cache compiled scripts

### Risk 3: Breaking Existing Tests
**Mitigation:** Run full test suite after each task, commit incrementally

### Risk 4: Security Vulnerabilities
**Mitigation:** Strict sandbox, timeout protection, no file I/O, code review

### Risk 5: Poor Error Messages
**Mitigation:** Comprehensive error handling, detailed logging, helpful user messages

---

## Commit Strategy

**Recommended Commits:**

1. "Add mlua dependency and LuaRuntime wrapper with sandbox"
2. "Add GameContextAPI for Lua bridge with entity serialization"
3. "Add LuaAction and extend ActionFactory for Lua registration"
4. "Add example Fireball action with integration tests"
5. "Add Lua API documentation and modding guide"
6. "Add comprehensive Lua integration tests"

**Branch Strategy:**
- Create feature branch: `feature/lua-integration-phase1`
- Commit incrementally (atomic commits)
- Create PR when complete
- Squash merge to main after review

---

## Definition of Done

### Code Complete
- [ ] All 6 tasks implemented
- [ ] All code follows existing patterns (type hints, logging, docstrings)
- [ ] No hardcoded paths (use config/constants)
- [ ] Error handling comprehensive

### Tests Complete
- [ ] All original 604 tests still pass
- [ ] 30+ new Lua tests added and passing
- [ ] Integration tests demonstrate end-to-end flow
- [ ] Manual testing completed

### Documentation Complete
- [ ] `docs/LUA_API.md` - API reference
- [ ] `docs/LUA_MODDING_GUIDE.md` - Modding guide
- [ ] `scripts/actions/_template.lua` - Action template
- [ ] Code comments and docstrings

### Quality Checks
- [ ] No regressions (original functionality intact)
- [ ] Performance acceptable (<5% overhead)
- [ ] No memory leaks
- [ ] Clean git history (atomic commits)

### Ready for PR
- [ ] Branch rebased on latest main
- [ ] All tests passing
- [ ] Documentation reviewed
- [ ] Example action working
- [ ] Ready for code review

---

## Context for Agent

### Repository Location
```bash
cd /home/scottsen/src/projects/brogue
```

### Current State
- **Branch:** main
- **Tests:** 604 passing
- **Recent PRs:** #11-15 (architectural improvements)
- **Working Directory:** Clean

### Key Files to Study First
1. `src/core/base/game_context.py` - Safe API facade (205 lines)
2. `src/core/actions/action_factory.py` - Factory pattern (403 lines)
3. `src/core/base/action.py` - Base action class
4. `src/core/actions/attack_action.py` - Example action implementation
5. `docs/architecture/COMPREHENSIVE_ANALYSIS.md` - Architecture overview

### Run Tests
```bash
cd /home/scottsen/src/projects/brogue
pytest -v
pytest tests/unit/test_lua_runtime.py -v  # After creating
```

### Useful TIA Commands
```bash
tia read src/core/base/game_context.py       # Smart file reading
tia search all "ActionFactory"               # Search codebase
tia beth explore "brogue action system"      # Knowledge graph search
```

---

## Questions for Clarification

If you encounter ambiguity, ask the user:

1. **API Surface:** Should we expose more GameContext methods? Which ones?
2. **Performance:** What's acceptable Lua execution time per action? (default: 3s)
3. **Security:** Are there additional sandbox restrictions needed?
4. **UI Integration:** Should Fireball be added to bot behavior? To UI keybindings?
5. **Error Handling:** How verbose should Lua error messages be?

---

## References

**Architecture Documentation:**
- `/home/scottsen/src/projects/brogue/docs/architecture/COMPREHENSIVE_ANALYSIS.md`
- `/home/scottsen/src/projects/brogue/docs/architecture/ANALYSIS_QUICK_REFERENCE.md`

**Prior Session:**
- `/home/scottsen/src/tia/sessions/descending-cosmos-1106/README_2025-11-06_15-36.md`

**Similar Prompt (Dungeon Generation):**
- `/home/scottsen/src/projects/brogue/DUNGEON_GENERATION_PROMPT.md` (reference for prompt structure)

---

**Agent: You are now a diligent engineer implementing Lua integration for Brogue. Work through Tasks 1-6 systematically, commit incrementally, test thoroughly, and document comprehensively. The architecture is excellent and ready for this work. Good luck!** 🚀
