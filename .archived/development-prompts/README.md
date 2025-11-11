# Development Prompts Archive

**Purpose:** Historical implementation prompts and progress tracking documents

**Date Archived:** 2025-11-11

---

## What's Here

This directory contains implementation prompts and progress tracking documents that were used during active development. These features are now **complete** and integrated into the main codebase.

### Completed Implementations

1. **LUA_INTEGRATION_PROMPT.md**
   - Phase 1: Custom Actions (Fireball example)
   - Status: ✅ Complete
   - See: `src/core/scripting/` for implementation

2. **LUA_EVENT_SYSTEM_PROMPT.md**
   - Phase 3: Event System (handlers, achievements, quests)
   - Status: ✅ Complete
   - Tests: 80+ tests passing
   - See: `src/core/scripting/events/` for implementation

3. **LUA_AI_BEHAVIORS_PROMPT.md**
   - Phase 2: AI Behaviors (Berserker, Sniper examples)
   - Status: ✅ Foundation complete
   - See: `src/core/scripting/ai/` for implementation

4. **DUNGEON_GENERATION_PROMPT.md**
   - Dungeon generation system design
   - Status: ✅ Complete
   - See: `src/core/world.py` and `data/balance/dungeon_generation.yaml`

5. **EVENT_SYSTEM_IMPLEMENTATION_SUMMARY.md**
   - Summary of event system implementation
   - Status: ✅ Complete, superseded by actual implementation

6. **LUA_TEST_FIXES_PROGRESS.md**
   - Progress tracking for Lua test fixes
   - Status: ✅ Complete (all tests passing)

---

## Why Archived

These documents served their purpose during development but are no longer needed as primary documentation because:

1. **Features are complete** - No longer "prompts" but actual working code
2. **Better docs exist** - See `docs/LUA_API.md`, `docs/LUA_EVENT_MODDING_GUIDE.md`, etc.
3. **Cluttered main directory** - Implementation prompts don't belong in root
4. **Historical value** - Useful to understand development process, not current state

---

## Where to Find Current Documentation

### For Lua Integration
- **API Reference:** `docs/LUA_API.md`
- **Event Modding:** `docs/LUA_EVENT_MODDING_GUIDE.md`
- **AI Modding:** `docs/LUA_AI_MODDING_GUIDE.md`

### For Current Project Status
- **What's Done:** `docs/PROJECT_STATUS.md`
- **What's Next:** `docs/MVP_CURRENT_FOCUS.md`
- **Reality Check:** `REALITY_CHECK.md` (comprehensive audit)

### For Architecture
- **Overview:** `docs/architecture/00_ARCHITECTURE_OVERVIEW.md`
- **Lua Strategy:** `docs/architecture/LUA_INTEGRATION_STRATEGY.md`

---

## Historical Context

These prompts were created during:
- **Lua Phase 1:** October-November 2025 (Custom Actions)
- **Lua Phase 2:** November 2025 (AI Behaviors)
- **Lua Phase 3:** November 2025 (Event System)

All phases are now complete and fully integrated into the game.

---

**If you need to understand how Lua integration was implemented, these documents provide the original design and implementation plans. For using Lua features, consult the current documentation in `docs/`.**
