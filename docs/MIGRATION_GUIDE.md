# Brogue Documentation Migration Guide

**Last Updated:** 2025-11-05
**Purpose:** Clarify which docs are accurate vs. outdated

---

## ⚠️ IMPORTANT: Documentation Audit Results

On 2025-11-05, we audited all documentation and found **significant discrepancies** between what the docs claim and what actually exists in the codebase.

**The Problem:**
- Many docs say "TODO: Mining System" → **FALSE** - Mining is complete (85+ tests passing)
- MVP_ROADMAP.md has unchecked boxes → **MISLEADING** - Most systems are done
- MVP_CURRENT_FOCUS.md says "Next: Implement mining" → **WRONG** - Already implemented months ago

**This guide fixes that confusion.**

---

## 📊 Documentation Accuracy Matrix

### ✅ 100% ACCURATE (Trust These)

| Document | Accuracy | Last Verified | Status |
|----------|----------|---------------|--------|
| **PROJECT_STATUS.md** | 💯 100% | 2025-11-05 | Comprehensive, accurate |
| **BROGUE_CONSOLIDATED_DESIGN.md** | 95% | 2025-11-05 | Design vision matches implementation |
| **README.md** | 90% | 2025-11-05 | Good overview, minor outdated sections |
| **architecture/00_ARCHITECTURE_OVERVIEW.md** | 90% | 2025-10-24 | Technical architecture accurate |
| **architecture/BASE_CLASS_ARCHITECTURE.md** | 95% | Recent | Matches implementation |
| **architecture/ACTION_FACTORY_COMPLETE.md** | 95% | Recent | Pattern documented correctly |

**Recommendation:** Start here. These docs reflect reality.

---

### ⚠️ PARTIALLY OUTDATED (Use With Caution)

| Document | Accuracy | Issue | Fix |
|----------|----------|-------|-----|
| **START_HERE.md** | 70% | Says "Mining is TODO" | **FALSE** - Mining is complete |
| **MVP_ROADMAP.md** | 40% | All checkboxes unchecked | **MISLEADING** - Most are done |
| **MVP_CURRENT_FOCUS.md** | 35% | Says "Next: Mining" | **WRONG** - Mining finished long ago |
| **UI_FRAMEWORK.md** | 80% | Textual UI info accurate | Some outdated references |

**Recommendation:** Read but verify against `PROJECT_STATUS.md`.

---

### ❌ ARCHIVED / OUTDATED (Don't Read)

| Document | Status | Reason |
|----------|--------|--------|
| **docs/Archive/** (entire directory) | ❌ Outdated | Rejected design visions from Oct 2025 |
| **docs/Archive/DEVELOPMENT_ROADMAP.md** | ❌ Obsolete | Superseded by MVP_ROADMAP.md |
| **docs/Archive/COMPREHENSIVE_DESIGN.md** | ❌ Rejected | Merged into BROGUE_CONSOLIDATED_DESIGN.md |
| **docs/Archive/development-history/** | ℹ️ Historical | Phase completion summaries (reference only) |

**Recommendation:** Ignore completely. Read `BROGUE_CONSOLIDATED_DESIGN.md` instead.

---

## 🔍 What's Actually Complete vs. What Docs Say

### Mining System

**Docs Say:** "TODO: Implement mining system"
**Reality:** ✅ **COMPLETE** (85+ tests passing)

**Evidence:**
- `src/core/actions/mine_action.py` - Full implementation
- `src/core/actions/survey_action.py` - Survey ore action
- `tests/unit/actions/test_mine_action.py` - 85+ comprehensive tests
- Multi-turn mining works, vulnerability during mining works, ore veins spawn correctly

**Where Docs Are Wrong:**
- `START_HERE.md` line 374: "Mining/Crafting (Phase 1 - TODO)"
- `MVP_ROADMAP.md`: Task 1.1-1.5 all show unchecked boxes

---

### Crafting System

**Docs Say:** "TODO: Implement crafting"
**Reality:** ✅ **COMPLETE** (10+ tests passing)

**Evidence:**
- `src/core/crafting.py` - Full implementation
- `src/core/actions/craft_action.py` - Craft action
- `data/balance/recipes.yaml` - 17 recipes defined
- `tests/integration/test_equipment_system.py` - Comprehensive tests
- YAML loading works, stat calculation works, forges work

**Where Docs Are Wrong:**
- `START_HERE.md`: Says crafting is TODO
- `MVP_ROADMAP.md`: Task 2.1-2.4 unchecked

---

### Equipment System

**Docs Say:** Not mentioned in roadmap
**Reality:** ✅ **COMPLETE** (10 tests passing)

**Evidence:**
- `src/core/actions/equip_action.py` - Equip/unequip actions
- Stat bonuses work in combat
- Equipment slots implemented
- Full integration tested

**Where Docs Are Wrong:**
- Not listed in MVP_ROADMAP.md at all!
- START_HERE.md doesn't mention it

---

### Save/Load System

**Docs Say:** "TODO: Save/load system"
**Reality:** ✅ **COMPLETE** (26 tests passing)

**Evidence:**
- `src/core/save_load.py` - Full serialization
- RNG state persistence works
- Multiple save slots work
- Corrupted save detection works
- `tests/unit/test_save_load.py` - 26 comprehensive tests

**Where Docs Are Wrong:**
- `MVP_ROADMAP.md`: Task 5.1-5.4 unchecked
- Says "Week 5: Save/Load" but it's already done

---

### Character Class System

**Docs Say:** Not in roadmap
**Reality:** ✅ **COMPLETE** (13 tests passing)

**Evidence:**
- `src/core/character_class.py` - Full implementation
- 4 classes: Warrior, Rogue, Mage, Healer
- Class-specific stats and bonuses
- Starting items per class
- `tests/unit/test_character_class.py` - 13 tests

**Where Docs Are Wrong:**
- Not mentioned in MVP_ROADMAP.md
- START_HERE.md mentions it but unclear status

---

### Floor Progression

**Docs Say:** Not clearly documented
**Reality:** ✅ **COMPLETE** (23 tests passing)

**Evidence:**
- `src/core/floor_manager.py` - Full implementation
- `src/core/actions/descend_action.py` - Stairs work
- Difficulty scaling works
- Monster count increases per floor
- Ore quality increases per floor
- `tests/unit/test_stairs_descent.py` - 23 tests

**Where Docs Are Wrong:**
- Not in MVP_ROADMAP.md
- No dedicated design doc

---

### High Score System

**Docs Say:** Not documented
**Reality:** ✅ **COMPLETE** (10 tests passing)

**Evidence:**
- `src/core/highscore.py` - Full leaderboard system
- Score calculation on death/victory
- Pure vs Legacy victory tracking
- JSON persistence
- `tests/integration/test_phase5_integration.py` - 10 tests

**Where Docs Are Wrong:**
- Not mentioned anywhere in roadmap
- Not in START_HERE.md

---

## 📋 Migration Checklist

If you're reading old docs, use this checklist:

### When Reading START_HERE.md

- ✅ Ignore "What's Next" section (outdated)
- ✅ Trust "What Exists" section (mostly accurate)
- ⚠️ Verify any "TODO" claims against PROJECT_STATUS.md
- ✅ File structure is accurate
- ✅ Development workflow is accurate

### When Reading MVP_ROADMAP.md

- ❌ Don't trust checkbox status (all wrong)
- ⚠️ Tasks 1.1-5.4 are actually complete
- ✅ Overall structure is good (just status is wrong)
- ➡️ Use PROJECT_STATUS.md instead for truth

### When Reading MVP_CURRENT_FOCUS.md

- ❌ Ignore "What We're Building NOW" (outdated)
- ✅ Test count is accurate (474 passing)
- ✅ System completion list is mostly accurate
- ➡️ Check last updated date (2025-11-05 version is accurate)

---

## 🎯 Which Doc to Read When

### "I'm new to the project"
👉 **Read:** `README.md` → `START_HERE.md` → `PROJECT_STATUS.md`

### "I want to understand the game design"
👉 **Read:** `BROGUE_CONSOLIDATED_DESIGN.md`

### "I want to know what's already built"
👉 **Read:** `PROJECT_STATUS.md` (100% accurate)

### "I want to add content"
👉 **Read:** `CONTENT_CREATION.md` → `DATA_FILES_GUIDE.md`

### "I want to understand the architecture"
👉 **Read:** `architecture/00_ARCHITECTURE_OVERVIEW.md` → `architecture/BASE_CLASS_ARCHITECTURE.md`

### "I want to know what to build next"
👉 **Read:** `MVP_CURRENT_FOCUS.md` (2025-11-05 version) → `PROJECT_STATUS.md`

### "I want to understand multiplayer plans"
👉 **Read:** `future-multiplayer/README.md` (but remember: NOT current work)

---

## 🔄 Documentation Update Plan

### High Priority (Need Update)

1. **MVP_ROADMAP.md**
   - Mark completed tasks with ✅
   - Update checkboxes to reflect reality
   - Add "Last Verified: 2025-11-05"

2. **START_HERE.md**
   - Remove "TODO" from completed systems
   - Update "What's Next" section
   - Fix "implementation in progress" language

3. **MVP_CURRENT_FOCUS.md**
   - Already updated (2025-11-05 version is accurate)
   - Keep this version as canonical

### Medium Priority (Nice to Have)

4. **README.md**
   - Update Phase 1 completion percentage
   - Mark remaining tasks more clearly

5. **Create New Guides**
   - ✅ QUICK_REFERENCE.md (done)
   - ✅ DATA_FILES_GUIDE.md (done)
   - ✅ CONTENT_CREATION.md (done)
   - ⏳ SYSTEM_INTERACTIONS.md (in progress)
   - ⏳ MECHANICS_REFERENCE.md (in progress)

---

## 📝 How Docs Got Outdated

**Timeline:**
1. **Oct 2025:** Documentation created with TODO markers
2. **Oct-Nov 2025:** Systems implemented rapidly (474 tests written)
3. **Documentation lag:** Docs not updated as features completed
4. **Result:** Large discrepancy between docs and reality

**Lesson:** Update docs as features complete, not after the fact.

---

## ✅ Verification Commands

**Want to verify claims yourself?**

```bash
# Check if mining is implemented
ls -la src/core/actions/mine_action.py
pytest tests/unit/actions/test_mine_action.py -v

# Check if crafting is implemented
ls -la src/core/crafting.py
pytest tests/integration/test_equipment_system.py -v

# Check if save/load is implemented
ls -la src/core/save_load.py
pytest tests/unit/test_save_load.py -v

# Count total passing tests
pytest tests/ -v | grep "passed"

# Run the game to verify it works
python3 run_textual.py
```

---

## 🚨 Red Flags in Documentation

If you see these phrases, be skeptical:

- ❌ "TODO: Mining System" → Check if already done
- ❌ "Phase 1 - upcoming" → Phase 1 is complete
- ❌ "Not yet implemented" → Verify against PROJECT_STATUS.md
- ❌ Unchecked checkboxes in roadmaps → May be misleading
- ❌ "Next: Implement X" → X might already exist

**Always verify against:**
- `PROJECT_STATUS.md` (ground truth)
- Actual code in `src/`
- Test files in `tests/`

---

## 💡 How to Use This Guide

### Scenario 1: "I read START_HERE.md and it says mining is TODO"

**Answer:** START_HERE.md is outdated on that point. Mining is complete.

**Evidence:**
- `PROJECT_STATUS.md` - Mining listed as 100% complete
- 85+ tests passing in `test_mine_action.py`
- Code exists in `src/core/actions/mine_action.py`

**What to Read Instead:** `PROJECT_STATUS.md` section "Mining System (100% Complete)"

### Scenario 2: "MVP_ROADMAP.md says 'Week 1-2: Mining System' with unchecked boxes"

**Answer:** That's misleading. Mining was completed months ago.

**Evidence:**
- `PROJECT_STATUS.md` shows 474 passing tests
- Mining tests were written and passed long ago
- Game has been playable with mining for weeks

**What to Read Instead:** `MVP_CURRENT_FOCUS.md` (2025-11-05 version) for current priorities

### Scenario 3: "A doc mentions 'Phase 1 is coming soon'"

**Answer:** Phase 1 is complete. We're in Phase 2 (Polish).

**Evidence:**
- `PROJECT_STATUS.md` - "MVP is essentially feature-complete"
- All 11 Phase 1 systems implemented and tested
- Current phase is "MVP Polish & Content Expansion"

**What to Read Instead:** `MVP_CURRENT_FOCUS.md` for what's actually being built now

---

## 📞 Still Confused?

**Priority 1 (Ground Truth):**
- `PROJECT_STATUS.md` - Comprehensive, 100% accurate report

**Priority 2 (Mostly Accurate):**
- `BROGUE_CONSOLIDATED_DESIGN.md` - Design vision (95% accurate)
- `README.md` - Overview (90% accurate)

**Priority 3 (Verify Before Trusting):**
- Other docs - Check against PROJECT_STATUS.md first

---

## 🔄 Last Updated

**This Guide:** 2025-11-05
**Status:** Accurate as of commit 966885d

**Next Update:** When significant implementation changes occur

---

**When in doubt, trust PROJECT_STATUS.md over other docs.** 📋✅
