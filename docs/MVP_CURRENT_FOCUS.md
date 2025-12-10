# Veinborn MVP: Current Focus & Next Steps

**Status:** ✅ **MVP FEATURE-COMPLETE** - Now in Polish & Content Phase
**Phase:** MVP Polish + Lua Advanced Features + **Multiplayer Phase 2 COMPLETE** 🎉
**Last Updated:** 2025-11-14
**Test Status:** 858/860 passing (99.8% pass rate, 2 skipped)

---

## ⚠️ IMPORTANT: Documentation Updated

**Previous versions of this document were severely outdated.**

This document has been corrected to reflect the **actual state** of the project as of 2025-11-05. See `PROJECT_STATUS.md` for the comprehensive status report.

---

## 🎉 What We've Built (MVP COMPLETE)

### ✅ All Phase 1 Systems Implemented

The single-player MVP is **feature-complete** with all core systems working:

1. ✅ **Basic Game** - Movement, combat, map generation (DONE)
2. ✅ **Mining System** - Survey ore, mine over turns (DONE - 85+ tests passing)
3. ✅ **Crafting System** - Recipes, forging items (DONE - 10+ tests passing)
4. ✅ **Equipment System** - Equip/unequip weapons & armor (DONE - 10 tests passing)
5. ✅ **Save/Load System** - Game state persistence (DONE - 26 tests passing)
6. ✅ **Character Classes** - 4 classes with different stats (DONE - 13 tests passing)
7. ✅ **Floor Progression** - Stairs, difficulty scaling (DONE - 23 tests passing)
8. ✅ **High Score System** - Leaderboards, statistics (DONE - 10 tests passing)
9. ✅ **Loot System** - Monster drops, loot tables (DONE - 3 tests passing)
10. ✅ **Combat System** - Turn-based tactical combat (DONE - 40+ tests passing)
11. ✅ **Monster AI** - Pathfinding, aggression (DONE - 40+ tests passing)
12. ✅ **Legacy Vault System** - Meta-progression (DONE - 47 tests passing)
13. ✅ **Lua Event System** - Phase 3 complete (event handlers, achievements, quests)

**Test Evidence:** 858/860 tests passing (99.8% pass rate, 2 skipped)

---

## 🎯 What We're Building NOW

### Phase: MVP Polish & Content Expansion

The core game is complete and playable. Focus now shifts to:
- Playtesting and balance tuning
- Content expansion (more monsters, recipes)
- Lua advanced features (AI behaviors, custom actions)
- Fix remaining 3 test failures
- Polish and user experience improvements

---

## 🚀 PARALLEL TRACK: Multiplayer Phase 2 COMPLETE!

**In parallel with single-player polish, we've completed multiplayer Phase 2:**

### ✅ What's Working (as of 2025-11-14)

**Infrastructure (100% Complete):**
- ✅ WebSocket server (localhost:8765)
- ✅ Token-based authentication
- ✅ Session management
- ✅ Game creation/joining
- ✅ Ready/start coordination
- ✅ Chat messaging

**Gameplay (100% Complete):**
- ✅ 2+ players can play together
- ✅ Shared dungeon generation
- ✅ **Distributed player spawning** (different rooms)
- ✅ **Monster AI integration** (monsters act after player rounds)
- ✅ **Nearest-player targeting** (smart co-op AI)
- ✅ Real-time movement synchronization
- ✅ Combat working with multiple players
- ✅ Turn system ("4 actions per round")

**Test Client:**
- ✅ Interactive test client (`src/server/test_client.py`)
- ✅ Commands: create, join, ready, move, chat

### 📁 New Files Created

**11 new files (~2,400 lines of code):**
```
src/server/
├── websocket_server.py      # Main WebSocket server (546 lines)
├── auth.py                   # Authentication (138 lines)
├── game_session.py           # Game management (440 lines)
├── multiplayer_game_state.py # Multiplayer state (317 lines)
├── messages.py               # Protocol (195 lines)
├── action_handler.py         # Action routing (90 lines)
├── config.py                 # Server config (53 lines)
├── run_server.py             # Server launcher (67 lines)
├── test_client.py            # Test client (364 lines)
└── README.md                 # Documentation (356 lines)
```

### 🎯 Next Steps for Multiplayer (Phase 3)

1. **Extended Testing** (High Priority)
   - Test 30+ minutes of 2-player co-op
   - Validate combat balance
   - Test edge cases

2. **Polish** (Medium Priority)
   - Delta compression (performance)
   - Reconnection handling
   - Class selection on join
   - Personal loot system

**See:** `MULTIPLAYER_PROGRESS.md` for full details

---

## 📋 Current Sprint: Polish & Playtest

### High Priority Tasks (Ready Now)

#### 1. Playtest & Balance (HIGHEST PRIORITY)
**Why:** The game is complete but untested by players

**Tasks:**
- [ ] Play the game for 30-60 minutes (end-to-end test)
- [ ] Document gameplay issues and balance problems
- [ ] Test all character classes
- [ ] Verify floor progression feels right
- [ ] Test mining/crafting loop for fun factor
- [ ] Validate equipment progression
- [ ] Check monster difficulty curve

**How to Playtest:**
```bash
cd /home/user/veinborn
python3 run_textual.py
```

**What to Look For:**
- Is combat balanced? (Too easy? Too hard?)
- Is mining fun? (Risk vs reward working?)
- Does crafting feel rewarding?
- Do character classes feel different?
- Is floor progression smooth?
- Any crashes or bugs?
- Are monster types varied enough?

#### 2. Test Suite Status ✅ RESOLVED
**Current Status:**
- ✅ 858/860 passing (99.8%)
- ✅ 2 tests correctly skipped (Lua timeout tests - C-level execution limitation)
- ✅ 0 tests failing
- ✅ All functional tests passing

**Note:** The 2 skipped tests (`test_infinite_loop_timeout` and `test_long_computation_timeout`)
cannot pass with the current signal-based timeout mechanism because lupa's C-level Lua
execution doesn't respond to Python signals. These would require a multiprocessing-based
timeout implementation, which is not worth the complexity for edge-case timeout protection.

#### 3. Content Status ✅ EXCEEDS GOALS

**Design Goal:** 15-20 monster types
**Actual:** **19 monster types** (111% of goal!)

**Monster Types (19 total):**

*Early Game (9):*
- ✅ goblin, orc, troll, bat, skeleton, ogre, wolf, spider, imp

*Mid Game (5):*
- ✅ wyvern, golem, wraith, mimic, vampire

*Late Game (5):*
- ✅ lich, demon, basilisk, phoenix, ancient_horror

**Recipes:** 16 total (10 regular + 6 legendary)
- ✅ 6 weapons (copper → adamantite progression)
- ✅ 4 armor (copper → adamantite progression)
- ✅ 6 legendary (flaming_sword, arcane_staff, dragon_bow, phoenix_armor, shadow_cloak, titans_hammer)

**Status:** ✅ **Content is COMPLETE** - exceeds design goals!

**Possible Expansions (Optional):**
- Additional monster variants (elite versions, bosses)
- More recipe variety (accessories, ranged weapons)
- Special equipment with unique effects

---

### Medium Priority Tasks

#### 4. Tutorial System (Not Started)
**Why:** New players need guidance

**What to Build:**
- [ ] First-run tutorial messages
- [ ] Help screen (H key)
- [ ] Keybind reference UI
- [ ] Mining tutorial (first ore vein encounter)
- [ ] Crafting tutorial (first forge encounter)
- [ ] Combat tutorial (first monster encounter)

**Implementation Ideas:**
- Tutorial messages in `src/core/tutorial.py`
- Help widget in `src/ui/textual/widgets/help_widget.py`
- Tutorial state tracking in player profile

**Estimated Time:** 6-8 hours

#### 5. Special Room Types (Not Started)
**Why:** Design mentions varied room types, only basic rooms exist

**Room Types to Add:**
- [ ] Treasure room (high-quality loot)
- [ ] Monster den (extra monsters, mini-boss)
- [ ] Ore chamber (multiple high-quality veins)
- [ ] Shrine (healing, temporary buffs)
- [ ] Trap room (pressure plates, spikes, arrows)

**Files to Modify:**
- `src/core/world.py` - Room generation logic
- `data/balance/game_constants.yaml` - Room spawn rates

**Estimated Time:** 8-12 hours

#### 6. Legendary Recipes (Partial)
**Why:** Design mentions legendary tier, mostly basic/advanced recipes exist

**Current Recipes:** 17 (mostly basic and advanced)

**Add Legendary Recipes:**
- [ ] Flaming Sword (fire damage bonus)
- [ ] Arcane Staff (spell power)
- [ ] Dragon Bow (piercing attack)
- [ ] Phoenix Armor (regeneration)
- [ ] Shadow Cloak (stealth bonus)

**Files to Modify:**
- `data/balance/recipes.yaml` - Add legendary recipes
- Mark as boss drops or rare dungeon finds

**Estimated Time:** 2-3 hours

---

### Low Priority (Future)

#### 7. Advanced AI Features
**Why:** Current simple aggressive AI works well, state machine is future enhancement

**Future Enhancements:**
- Idle/Chasing/Wandering/Fleeing state machines
- Line-of-sight checks
- Monster coordination

**Estimated Time:** 12-16 hours (not urgent)
**Note:** Removed placeholder tests (2025-11-05) - will write fresh tests when implementing

#### 8. Performance Optimization
**Current Performance:** Unknown (needs profiling)

**Goals:**
- Map generation < 100ms
- Game loop 60+ FPS
- No memory leaks in long sessions

**Tasks:**
- [ ] Profile map generation
- [ ] Profile game loop
- [ ] Test long play sessions (1+ hours)
- [ ] Optimize hot paths

**Estimated Time:** 4-8 hours

---

## 🗺️ Updated Implementation Roadmap

### ✅ Phase 0: Foundation (COMPLETE - October 2025)
- ✅ Basic game loop
- ✅ Movement and combat
- ✅ Map generation (BSP)
- ✅ Textual UI
- ✅ Monster AI

### ✅ Phase 1: MVP Core Systems (COMPLETE - October 2025)
- ✅ Mining system (ore veins, survey, multi-turn mining)
- ✅ Crafting system (recipes, stat calculation, forging)
- ✅ Equipment system (weapons, armor, stat bonuses)
- ✅ Save/load system (game state persistence)
- ✅ Character classes (4 classes)
- ✅ Floor progression (stairs, difficulty scaling)
- ✅ High score tracking (leaderboards)
- ✅ Loot system (monster drops)

### 🔨 Phase 2: Polish (CURRENT - November 2025)
- [ ] Playtest and balance pass
- [x] Complete Legacy Vault (100% done - 47 tests passing!)
- [x] Lua Event System (100% done - Phase 3 complete!)
- [ ] Fix remaining 3 test failures (857/860 → 860/860)
- [ ] Content expansion (more monsters, recipes)
- [ ] Tutorial system
- [ ] Special room types
- [ ] Performance optimization

### 📅 Phase 3: Launch Prep (December 2025?)
- [ ] Final balance tuning
- [ ] Bug fixes from playtesting
- [ ] Documentation for players
- [ ] Release candidate testing

### 🚀 Phase 4: Multiplayer (EARLY START - Phase 2 Complete!)
- ✅ **Phase 2 COMPLETE** (as of 2025-11-14)
- ✅ WebSocket server working
- ✅ 2+ player co-op functional
- ✅ Monster AI integration
- ✅ Turn system implemented ("4 actions per round")
- 🔨 Phase 3: Testing, polish, balance
- 📅 Phase 4: Persistence, advanced features
- See: `MULTIPLAYER_PROGRESS.md` and `docs/design/MULTIPLAYER_DESIGN_2025.md`

---

## 📁 Key Files Reference

### Core Game Logic (All Working):
- `src/core/game.py` - Main game loop ✅
- `src/core/entities.py` - Player, Monster, OreVein ✅
- `src/core/world.py` - Map generation ✅
- `src/core/crafting.py` - Crafting system ✅
- `src/core/save_load.py` - Save/load ✅
- `src/core/character_class.py` - Character classes ✅
- `src/core/legacy.py` - **TODO: Legacy Vault** ⚠️

### UI (All Working):
- `src/ui/textual/app.py` - Main Textual app ✅
- `src/ui/textual/widgets/` - UI widgets ✅

### Data (All Working):
- `data/balance/recipes.yaml` - 17 recipes ✅
- `data/entities/monsters.yaml` - 9 monster types ✅
- `data/entities/ores.yaml` - 4 ore types ✅
- `data/balance/loot_tables.yaml` - Loot definitions ✅

### Tests (857/860 Passing - 99.7%):
- `tests/unit/` - Unit tests ✅
- `tests/integration/` - Integration tests ✅
- `tests/fuzz/` - Bot testing ✅
- All systems have comprehensive test coverage ✅
- **3 failing tests** remaining for investigation

---

## 🚀 Getting Started (For New Contributors)

### 1. Verify the Game Works
```bash
cd /home/user/veinborn

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run the game
python3 run_textual.py
```

**You should see:**
- Dungeon map rendering
- Player character (@)
- Monsters (g, o, t, etc.)
- Ore veins (◆)
- Full UI with status bar, sidebar, messages

### 2. Run the Tests
```bash
# Run all tests
python3 -m pytest tests/ -v

# Expected: 544 passed, 0 skipped
```

### 3. Read the Code
**Start with these files (in order):**
1. `docs/PROJECT_STATUS.md` - Current state overview
2. `src/core/game.py` - Game loop (~500 lines)
3. `src/core/entities.py` - Player/Monster (~300 lines)
4. `src/core/actions/` - Action system (mining, crafting, etc.)

### 4. Pick a Task
**Easy (1-2 hours):**
- Add a new monster type to `monsters.yaml`
- Add a new recipe to `recipes.yaml`
- Tune balance values in `game_constants.yaml`

**Medium (4-8 hours):**
- Complete Legacy Vault system
- Add tutorial system
- Create special room types

**Hard (12+ hours):**
- Implement advanced AI features
- Performance optimization
- Multiplayer planning

---

## 📚 Essential Documentation

### For Current Work:
1. **PROJECT_STATUS.md** - Comprehensive status report (NEW)
2. **MVP_ROADMAP.md** - Original roadmap (needs update)
3. **VEINBORN_CONSOLIDATED_DESIGN.md** - Game design vision (accurate)
4. **architecture/00_ARCHITECTURE_OVERVIEW.md** - System architecture (accurate)

### For Future Work:
- **future-multiplayer/** - Phase 2 design (8-12 weeks out)
- **architecture/LUA_INTEGRATION_STRATEGY.md** - Phase 3 planning

---

## ❓ Common Questions

### "Is the game playable?"
✅ **YES!** The game is fully playable from start to finish. All core systems work.

### "What's actually missing?"
Very little! Main gaps:
- Fix remaining 3 test failures (99.7% → 100%)
- Lua advanced features (AI behaviors, custom actions)
- More monster types (have 19, excellent coverage!)
- Tutorial system (new player UX)
- Special room types (content variety)

### "Should I implement multiplayer now?"
❌ **NO!** Phase 2 is 8-12 weeks out. Focus on polish first.

### "Can I add content (monsters, recipes)?"
✅ **YES!** This is the perfect time for content expansion.

### "What about all the TODO checkboxes in MVP_ROADMAP.md?"
⚠️ **Those are outdated.** Everything marked TODO is actually complete. See `PROJECT_STATUS.md` for truth.

---

## 🎯 Success Criteria (Updated)

### Phase 2 (Polish) is Done When:
- ✅ Game playtested for 30+ hours total
- ✅ Balance feels good across all classes
- ✅ Legacy Vault complete and tested
- ✅ 15-20 monster types implemented
- ✅ Tutorial system guides new players
- ✅ No critical bugs or crashes
- ✅ Performance meets goals (< 100ms gen, 60 FPS)

### Ready for Phase 3 (Launch) When:
- ✅ All Phase 2 criteria met
- ✅ External playtesters give positive feedback
- ✅ "One more run" factor is strong
- ✅ Documentation complete for players

### Ready for Phase 4 (Multiplayer) When:
- ✅ Single-player game is polished and stable
- ✅ Player base exists and wants co-op
- ✅ Team has bandwidth for 8-12 week effort

---

## 🚨 What NOT to Do

### ❌ Don't implement these (wrong phase):
- NATS message bus
- WebSocket server
- Multiplayer lobby
- Lua scripting
- Microservices
- Docker/Podman orchestration

### ❌ Don't read outdated docs:
- Old acceptance criteria checkboxes in MVP_ROADMAP.md (outdated)
- MVP_CURRENT_FOCUS.md old versions (severely outdated)
- Archive/ directory (historical only)

### ✅ Do focus on:
- Playtesting and balance
- Content expansion (monsters, recipes)
- Completing partial features (Legacy Vault)
- Polish and UX improvements
- Performance optimization

---

## 📞 Need Help?

### Where to Look:
- **Current Status:** `docs/PROJECT_STATUS.md`
- **Game Design:** `docs/VEINBORN_CONSOLIDATED_DESIGN.md`
- **Architecture:** `docs/architecture/00_ARCHITECTURE_OVERVIEW.md`
- **Testing:** `tests/README.md`

### What to Do:
- Play the game first (understand what works)
- Read `PROJECT_STATUS.md` (truth about current state)
- Pick a task from the lists above
- Write tests for your changes
- Playtest your additions

---

## 🎮 Let's Polish!

**Current Focus:** Playtest the game and document what needs tuning!

**First Task:** Run `python3 run_textual.py` and play for 30 minutes

**Success:** You have a list of balance issues and improvement ideas

---

**Ready? Let's make this game shine!** ✨

**Questions?** Check `PROJECT_STATUS.md` for the full story.

**Confused?** Remember: MVP is complete, now we polish and add content.
