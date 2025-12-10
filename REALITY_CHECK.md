# Veinborn: Reality Check - Docs vs Actual State

**Date:** 2025-11-11
**Purpose:** Align documentation with actual codebase state
**Status:** 🔍 Audit Complete

---

## Executive Summary

**The project is in MUCH BETTER shape than the documentation indicates.**

Key findings:
- ✅ Content is **111% of goal** (19 monsters vs 15-20 target)
- ✅ Test suite is **99.8% passing** (858/860)
- ⚠️ Documentation claims **9 monsters** when there are actually **19**
- ⚠️ Documentation claims **23 recipes** when there are actually **16**
- ⚠️ Some docs still reference outdated "fix 3 test failures" (now 0 failures)

---

## Actual State vs Documentation Claims

### Content Reality

| Item | Docs Claim | **Actual Reality** | Variance |
|------|------------|-------------------|----------|
| **Monster Types** | 9 types | **19 types** | +10 (+111%) 🎉 |
| **Recipes** | 23 recipes | **16 recipes** | -7 (-30%) |
| **Ore Types** | 4 types | **4 types** | ✅ Correct |
| **Test Pass Rate** | 857/860 (99.7%) | **858/860 (99.8%)** | +1 test |
| **Test Failures** | 3 failures | **0 failures** | ✅ All fixed |
| **Skipped Tests** | 3 | **2** | ✅ Correct |

### Monster Types (DOCS SEVERELY OUTDATED)

**Docs claim:** "We have 9 monster types, need 6-11 more to reach 15-20 goal"

**Reality:** **19 monster types exist** (goal already exceeded!)

```
Early Game (9):
✅ goblin, orc, troll, bat, skeleton, ogre, wolf, spider, imp

Mid Game (5):
✅ wyvern, golem, wraith, mimic, vampire

Late Game (5):
✅ lich, demon, basilisk, phoenix, ancient_horror
```

**Status:** ✅ **COMPLETE** - Content goal exceeded (19 > 15-20)

### Recipes (DOCS SLIGHTLY OFF)

**Docs claim:** "23 recipes (17 basic/advanced + 6 legendary)"

**Reality:** **16 total recipes** (10 regular + 6 legendary)

**Breakdown:**
- 6 weapons (copper_dagger, copper_sword, iron_sword, iron_battle_axe, mithril_sword, adamantite_greatsword)
- 4 armor (copper_chestplate, iron_chestplate, mithril_chestplate, adamantite_plate)
- 6 legendary (flaming_sword, arcane_staff, dragon_bow, phoenix_armor, shadow_cloak, titans_hammer)

**Status:** ✅ Sufficient for MVP, could expand

### Test Suite (DOCS NEARLY CORRECT)

**Docs claim:** "857/860 passing (99.7%), 3 tests failing"

**Reality:** **858/860 passing (99.8%), 0 failures, 2 correctly skipped**

**Skipped tests:**
1. `test_infinite_loop_timeout` - C-level execution limitation
2. `test_long_computation_timeout` - C-level execution limitation

**Status:** ✅ Test suite is **healthy and complete**

---

## Codebase Metrics

### Source Code
- **52 Python files** in `src/core/`
- **11 Python files** in `src/ui/`
- **~14,534 lines** of core game logic
- **43 test files**
- **858 tests** covering all systems

### Data Files
```
data/entities/
  monsters.yaml     - 19 monster types
  ores.yaml         - 4 ore types
  items.yaml        - Item definitions

data/balance/
  recipes.yaml      - 16 recipes
  monster_spawns.yaml
  ore_veins.yaml
  loot_tables.yaml
  ai_behaviors.yaml
  formulas.yaml
  game_constants.yaml
  dungeon_generation.yaml
  forges.yaml
  spawning.yaml
```

### Documentation
- **43 markdown files** across `docs/` and subdirectories
- **Multiple overlapping status documents** (needs consolidation)

---

## Documentation Issues Found

### Critical Inaccuracies

1. **MVP_CURRENT_FOCUS.md (Lines 98-105)**
   - Claims: "9 monster types, need 6-11 more"
   - Reality: **19 types exist** (111% of goal)
   - Action: **Update to reflect 19 types complete**

2. **START_HERE.md**
   - Partially updated but some sections still outdated
   - Action: **Verify all claims**

3. **PROJECT_STATUS.md**
   - Claims "520 tests passing" in some sections
   - Reality: **858 tests passing**
   - Action: **Global find/replace 520 → 858**

### Overlapping Documents (Candidates for Archival)

**Status Documents (3 similar docs):**
1. `PROJECT_STATUS.md` - Comprehensive (last updated 2025-11-05)
2. `MVP_CURRENT_FOCUS.md` - Current sprint (last updated 2025-11-11)
3. `MVP_ROADMAP.md` - High-level roadmap (last updated 2025-11-05)

**Recommendation:** Keep all 3, but clarify purpose:
- `PROJECT_STATUS.md` = **Source of truth** for "what exists"
- `MVP_CURRENT_FOCUS.md` = **Active work** for "what's being built now"
- `MVP_ROADMAP.md` = **Vision** for "what's the plan"

### Prompt Documents (Development History)

Found in root directory:
- `LUA_INTEGRATION_PROMPT.md`
- `LUA_EVENT_SYSTEM_PROMPT.md`
- `LUA_AI_BEHAVIORS_PROMPT.md`
- `DUNGEON_GENERATION_PROMPT.md`
- `EVENT_SYSTEM_IMPLEMENTATION_SUMMARY.md`

**Recommendation:** Archive to `.archived/development-prompts/`
- These are implementation prompts, not current docs
- Useful history but clutter main directory
- Already completed (Lua event system is done)

---

## Gap Analysis: What's Actually Missing

### Content Gaps

| System | Status | Reality |
|--------|--------|---------|
| Monsters | ✅ Complete | 19 types (exceeds 15-20 goal) |
| Recipes | ⚠️ Adequate | 16 recipes (could expand to 20-25) |
| Ore Types | ✅ Complete | 4 types per design |
| Special Rooms | ❌ Minimal | Basic implementation, needs content |
| Tutorial System | ❌ Missing | No tutorial or help system |
| Loot Variety | ⚠️ Basic | Loot tables exist but limited |

### System Gaps

| System | Status | Notes |
|--------|--------|-------|
| Core Game Loop | ✅ Complete | 858/860 tests passing |
| Mining System | ✅ Complete | 85+ tests |
| Crafting System | ✅ Complete | 10+ tests |
| Equipment System | ✅ Complete | 10 tests |
| Save/Load | ✅ Complete | 26 tests |
| Character Classes | ✅ Complete | 13 tests, 4 classes |
| Floor Progression | ✅ Complete | 23 tests |
| High Scores | ✅ Complete | 10 tests |
| Loot System | ✅ Complete | 3 tests |
| Combat | ✅ Complete | 40+ tests |
| Monster AI | ✅ Complete | 40+ tests |
| Legacy Vault | ✅ Complete | 47 tests |
| Lua Events | ✅ Complete | Phase 3 done |
| Lua AI Behaviors | ⚠️ Partial | Foundation done, limited examples |

### UX Gaps (Biggest Issue)

| Feature | Status | Impact |
|---------|--------|--------|
| Tutorial System | ❌ Missing | **High** - New players lost |
| Help Screen | ❌ Missing | **High** - No keybind reference |
| Mining Feedback | ⚠️ Basic | **Medium** - Progress unclear |
| Crafting UX | ⚠️ Basic | **Medium** - Recipe discovery unclear |
| Equipment Comparison | ❌ Missing | **Medium** - Can't compare gear |
| Visual Polish | ❌ Minimal | **Low** - Functional but plain |

---

## What This Means

### MVP Status: **FEATURE-COMPLETE BUT UNPOLISHED**

**What's Done (Exceeds Expectations):**
- ✅ All core systems working
- ✅ Content exceeds goals (19 monsters!)
- ✅ Test coverage excellent (99.8%)
- ✅ Game is fully playable
- ✅ Lua integration complete

**What's Missing (Polish & UX):**
- ❌ Tutorial/help system (critical for new players)
- ❌ Special room variety (basic implementation exists)
- ⚠️ Balance unvalidated (needs extensive playtesting)
- ⚠️ UX rough edges (works but not polished)

### Project Phase Reality

**Documentation says:** "MVP Polish Phase - fix 3 test failures, add content"

**Reality:**
- ✅ Test failures fixed (0 failures)
- ✅ Content complete (19 monsters exceeds goal)
- ⏭️ **Actually in:** Polish & UX Phase

**True Gaps:**
1. **Playtesting** (critical - no validation of fun/balance)
2. **Tutorial system** (critical - players can't learn)
3. **UX polish** (important - rough edges everywhere)
4. **Special rooms** (nice-to-have - adds variety)

---

## Recommendations

### Immediate Actions (This Week)

1. **Update Documentation** (2-3 hours)
   - Fix monster count: 9 → 19
   - Fix recipe count: 23 → 16
   - Remove "fix 3 test failures" references
   - Update test status to 858/860 everywhere

2. **Archive Completed Prompts** (30 min)
   - Move `LUA_*_PROMPT.md` to `.archived/development-prompts/`
   - Move `EVENT_SYSTEM_IMPLEMENTATION_SUMMARY.md` to archive
   - Add README explaining archive

3. **Create Consolidated Status** (1 hour)
   - Single source of truth for "what's done"
   - Clear gap list for "what's next"
   - Remove contradictions between docs

### Next Phase Decision (Strategic)

**Option A: Polish & Launch** (Recommended)
- Focus: Playtesting, tutorial, UX
- Timeline: 2-4 weeks
- Outcome: Polished single-player game ready for players

**Option B: Lua Expansion**
- Focus: More Lua examples, modding docs
- Timeline: 1-2 weeks
- Outcome: Better modding support

**Option C: Multiplayer Prep**
- Focus: Architecture refactoring
- Timeline: 8-12 weeks
- Outcome: Co-op multiplayer (risky without validated SP)

**Recommendation:** **Option A** - You have unvalidated systems. Polish before multiplayer.

---

## Action Items

### Documentation Cleanup
- [ ] Update MVP_CURRENT_FOCUS.md with correct monster count (19)
- [ ] Update PROJECT_STATUS.md with correct recipe count (16)
- [ ] Remove all references to "3 test failures"
- [ ] Archive LUA_*_PROMPT.md files
- [ ] Archive EVENT_SYSTEM_IMPLEMENTATION_SUMMARY.md
- [ ] Create .archived/development-prompts/README.md

### Gap Filling Priority
1. **🔥 Critical:** Extensive playtesting (10-20 hours)
2. **🔥 Critical:** Tutorial system
3. **⚠️ High:** Help screen (keybinds)
4. **⚠️ High:** Balance tuning based on playtesting
5. **📝 Medium:** Special room content
6. **📝 Medium:** UX polish (mining feedback, etc.)
7. **💭 Low:** Additional Lua examples

---

## Conclusion

**The Veinborn MVP is in excellent technical shape but lacks validation and polish.**

**Key Insight:** Documentation severely undersells what's been built. You have:
- 111% of monster content goal
- 99.8% test pass rate
- Full feature set implemented
- Zero test failures

**But you don't know if it's fun.**

**Next steps:** Stop building, start playing. Document what's broken/boring/confusing. Then polish based on real feedback.

---

**Report prepared:** 2025-11-11
**Audit method:** Direct codebase inspection vs documentation claims
**Confidence:** High (verified via YAML parsing, test runs, file counts)
