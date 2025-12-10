---
project: veinborn
document_type: quick-reference
analysis_date: 2025-11-06
status: production-ready
beth_topics: [architecture, quick-reference, extensibility-checklist, lua-roadmap, pain-points, design-patterns]
keywords: [roguelike, architecture-scorecard, extensibility, lua-integration, critical-paths]
---

# VEINBORN ARCHITECTURE - QUICK REFERENCE

**Status:** Production-ready for MVP | Scripting-ready | Well-architected

---

## KEY FINDINGS AT A GLANCE

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Architecture Quality** | ⭐⭐⭐⭐⭐ | Clean separation, action pattern, factory pattern |
| **Code Organization** | ⭐⭐⭐⭐⭐ | Clear module structure, single responsibility |
| **Type Safety** | ⭐⭐⭐⭐⭐ | Python 3.10+ with comprehensive type hints |
| **Data-Driven Design** | ⭐⭐⭐⭐☆ | 80% data-driven, some procedural generation hardcoded |
| **Coupling** | ⭐⭐⭐⭐⭐ | Minimal, action-based, GameContext API |
| **Testability** | ⭐⭐⭐⭐⭐ | Comprehensive fixtures, easy to mock |
| **Lua Readiness** | ⭐⭐⭐⭐⭐ | ActionFactory, GameContext, event-ready patterns |

---

## ARCHITECTURE PATTERN

**Clean Architecture (Onion Model):**

```
UI (Textual)
    ↓
Game Controller
    ↓
GameState ← GameContext (Safe API)
    ↓
Actions/Systems/Subsystems
    ↓
Data (YAML)
```

---

## STRENGTHS (5/5)

✅ **Action/Outcome Pattern** - Serializable, event-ready, Lua-compatible  
✅ **GameContext Facade** - Safe API for sandboxed code  
✅ **Data-Driven Entities** - YAML-based monster, ore, item definitions  
✅ **Factory Pattern** - Easy to extend with custom actions  
✅ **Type-Safe** - Full type hints, enum-based type checking  
✅ **Comprehensive Tests** - Unit, integration, fuzz testing framework  
✅ **Well-Structured** - Clear module responsibilities  

---

## PAIN POINTS (3/5 severity)

⚠️ **Dungeon Generation Hardcoded** - BSP algorithm not data-driven (LOW impact)  
⚠️ **Spawning Logic Hardcoded** - Monster counts, room distribution (LOW impact)  
⚠️ **AI System Limited** - Only one behavior type (MEDIUM - easy to extend)  
⚠️ **Event System Missing** - Events in ActionOutcome but no pub/sub (MEDIUM)  
⚠️ **Magic Numbers** - Some constants scattered (LOW - use constants.py)  

---

## RECOMMENDED IMPROVEMENTS

**Before Lua (Priority):**
1. Extract Event System (2-3 days)
2. Move spawning to YAML config (1-2 days)
3. Add missing AI types (1 day)

**For Lua Integration:**
1. Set up mlua runtime (2 days)
2. Map GameContext → Lua API (2 days)
3. Support custom actions (1 day)
4. Add hot reload (1 day)

**Total effort for basic Lua support:** 2-3 weeks  
**Total effort for full Lua platform:** 6-8 weeks

---

## FILE GUIDE - WHAT TO READ FIRST

| When You Want to... | Read This | Why |
|--------------------|-----------|----|
| Understand overall structure | `src/core/game.py` | Game controller (382 lines) |
| Learn action system | `src/core/base/action.py` | Base action class + outcome pattern |
| See factory pattern | `src/core/actions/action_factory.py` | How actions are created |
| Understand safe API | `src/core/base/game_context.py` | GameContext interface |
| Learn entity system | `src/core/entities.py` | Player, Monster, OreVein |
| See data-driven design | `data/entities/*.yaml` | Monster/ore/item definitions |
| Understand crafting | `src/core/crafting.py` + `data/balance/recipes.yaml` | Formula-based stat calculation |
| Learn AI system | `src/core/systems/ai_system.py` | Monster behavior (97 lines, simple) |
| Understand turn flow | `src/core/turn_processor.py` | Turn execution logic |

---

## KEY STATISTICS

- **Total Core Code:** 3,550 lines (Python)
- **Number of Modules:** 25 core modules
- **Number of Actions:** 8 action types
- **Number of Entity Types:** 6 types (Player, Monster, Item, Ore, Forge, Projectile)
- **YAML Config Files:** 8 balance/entity definition files
- **Test Coverage:** Unit, integration, fuzz testing
- **Game Constants:** 20+ magic numbers (in constants.py)

---

## COUPLING SCORECARD

| Component Pair | Coupling | Can Fix | Notes |
|---|---|---|---|
| ActionFactory ↔ Action Classes | **Tight** | ✅ Yes | Use register_handler() - already supported |
| TurnProcessor ↔ HighScore/Vault | **Tight** | ✅ Yes | Use events (Phase 2) |
| AttackAction ↔ LootGenerator | **Loose** | ✅ Yes | Singleton pattern is fine |
| Systems ↔ GameState | **Loose** | ✅ N/A | GameContext mediates access |
| Actions ↔ Each Other | **None** | ✅ N/A | Completely independent |
| Game ↔ All Systems | **Loose** | ✅ N/A | Orchestrator pattern is correct |

**Overall Coupling Score:** 4/5 (Excellent)

---

## DATA-DRIVEN SCORECARD

| Component | Data-Driven? | Effort to Fix |
|---|---|---|
| Monster stats | ✅ 100% | Already done |
| Ore properties | ✅ 100% | Already done |
| Item definitions | ✅ 100% | Already done |
| Crafting recipes | ✅ 100% | Already done |
| Loot tables | ✅ 100% | Already done |
| Monster spawning | ⚠️ 50% | 1-2 days |
| Dungeon generation | ❌ 0% | 3-4 days |
| Damage formulas | ❌ 0% | 1 day |
| Combat effects | ❌ 0% (not implemented) | Future phase |
| Ability system | ❌ 0% (not implemented) | Future phase |

**Overall Data-Driven Score:** 4/5 (Good)

---

## EXTENSIBILITY SCORECARD

| Extension Point | Ready? | How to Use |
|---|---|---|
| **Custom Actions** | ✅ **NOW** | `factory.register_handler()` |
| **Custom AI Behaviors** | ⚠️ **Soon** | Extend AISystem, register behaviors |
| **Custom Items/Recipes** | ✅ **NOW** | Add to YAML, use EntityLoader |
| **Custom Systems** | ✅ **NOW** | `context.register_system()` |
| **Event Handlers** | ⚠️ **Phase 2** | Implement EventBus (not yet) |
| **Lua Actions** | ✅ **Soon** | Set up mlua, map GameContext |
| **Lua AI** | ✅ **Soon** | Register behavior functions |
| **Lua Generators** | ⚠️ **Phase 2** | Refactor World class first |

**Overall Extensibility Score:** 5/5 (Excellent)

---

## LUA INTEGRATION ROADMAP

### Phase 1: Foundation (1 week)
- [ ] Set up mlua runtime
- [ ] Map GameContext to Lua API
- [ ] Create Lua sandbox
- [ ] Document API surface
- [ ] Write hello world example

### Phase 2: Actions (1 week)
- [ ] Support registering custom actions
- [ ] Test action serialization/deserialization
- [ ] Add error handling
- [ ] Create action template library

### Phase 3: AI Behaviors (1 week)
- [ ] AI behavior registry
- [ ] Behavior function interface
- [ ] Add conditional behaviors
- [ ] Test monster behavior switching

### Phase 4: Advanced (2+ weeks)
- [ ] Event system + Lua handlers
- [ ] Dungeon generator support
- [ ] Item/recipe creation
- [ ] Configuration hotloading

---

## CRITICAL PATHS (For Scripting Integration)

**To Add Custom Actions:**
1. User creates `scripts/my_action.lua`
2. Script implements `validate()` and `execute()`
3. Registers with `veinborn.actions.register('my_action', script)`
4. Game loads script on boot
5. Player uses action via `factory.create('my_action')`

**To Add Custom AI:**
1. User creates `scripts/my_ai.lua`
2. Script implements `update(monster, context)`
3. Registers with `veinborn.ai.register('my_behavior', script)`
4. Monster uses in YAML: `ai_type: my_behavior`
5. AISystem calls registered behavior function

**To Add Custom Items/Recipes:**
1. Edit `data/entities/items.yaml` or create new
2. Edit `data/balance/recipes.yaml`
3. Game reloads on next boot
4. Items appear in loot, recipes available at forges

---

## GOTCHAS & LIMITATIONS

1. **Entity IDs must be unique** - No automatic deduplication
2. **Positions can be None** - Items in inventory have x/y = None
3. **Mining is multi-turn** - State stored in player.mining_action
4. **RNG is seeded** - Same seed = same game
5. **Monsters die immediately** - Dead entities removed next cleanup
6. **Loot drops at monster position** - Not at player position
7. **Formulas use simpleeval** - Limited to math operations
8. **No floating-point stats** - All truncated to integers
9. **Equipment bonuses are additive** - No multipliers yet
10. **Game constants are hardcoded** - But can be moved to YAML

---

## NEXT STEPS (Recommended)

1. **Read full analysis** → `docs/architecture/COMPREHENSIVE_ANALYSIS.md`
2. **Understand game loop** → Play the game (`python3 run_textual.py`)
3. **Study action system** → Read `src/core/actions/action_factory.py`
4. **Plan improvements** → Use recommendations from analysis
5. **Design Lua integration** → Plan API surface + sandbox
6. **Prototype Lua support** → Start with custom actions
7. **Iterate** → Add AI, dungeon generators, etc.

---

## DOCUMENT GUIDE

- **COMPREHENSIVE_ANALYSIS.md** (this file's full version) - 1,400+ lines, every detail
- **ANALYSIS_QUICK_REFERENCE.md** (this file) - 300 lines, quick lookups
- **00_ARCHITECTURE_OVERVIEW.md** - Original architecture doc
- **SYSTEM_INTERACTIONS.md** - How systems talk to each other
- **MVP_TESTING_GUIDE.md** - Testing patterns and fixtures

---

**Generated:** 2025-11-06  
**Analysis Depth:** Comprehensive (full codebase review)  
**Lua Readiness:** **READY - Begin integration**

