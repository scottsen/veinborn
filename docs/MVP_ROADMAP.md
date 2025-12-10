# Veinborn MVP Roadmap

**Last Updated:** 2025-11-14
**Status:** ✅ MVP 100% COMPLETE + Multiplayer Phase 2 Complete! 🎉
**Goal:** Feature-complete single-player roguelike with mining/crafting + 2+ player co-op

---

## ⚠️ IMPORTANT

**All Phase 1 systems are COMPLETE!** This document provides a high-level overview only.

**For current work:** See [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)
**For detailed status:** See [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

## 📊 Phase Overview

### ✅ Phase 0: Foundation (COMPLETE - Oct 2025)

**Core game working:**
- Movement and combat (8-direction, turn-based)
- BSP dungeon generation (rooms + corridors)
- Monster AI (pathfinding, aggression)
- Textual UI (map, status, messages, sidebar)
- Death and restart flow

**Deliverable:** Playable roguelike prototype ✅

---

### ✅ Phase 1: MVP Core Systems (COMPLETE - Oct-Nov 2025)

**All systems implemented and tested:**

| System | Status | Tests | Files |
|--------|--------|-------|-------|
| **Mining** | ✅ Complete | 85+ | `src/core/actions/mine_action.py` |
| **Crafting** | ✅ Complete | 10+ | `src/core/crafting.py`, `data/balance/recipes.yaml` |
| **Equipment** | ✅ Complete | 10 | `src/core/actions/equip_action.py` |
| **Save/Load** | ✅ Complete | 26 | `src/core/save_load.py` |
| **Classes** | ✅ Complete | 13 | `src/core/character_class.py` |
| **Floors** | ✅ Complete | 23 | `src/core/floor_manager.py` |
| **High Scores** | ✅ Complete | 10 | `src/core/highscore.py` |
| **Loot** | ✅ Complete | 3 | `src/core/loot.py` |
| **Legacy Vault** | ✅ Complete | 47 | `src/core/legacy.py` |

**Total:** 858/860 tests passing (99.8% pass rate, 2 skipped)

**Deliverable:** Complete single-player game with all MVP systems ✅

---

### 🔨 Phase 2: Polish & Content (CURRENT - Nov 2025)

**Focus:** Playtesting, balance, content expansion

**Priorities:**
1. **Playtest & Balance** - Test all systems end-to-end
2. **Content Expansion** - 19 monster types ✅, 23 recipes ✅
3. **Legacy Vault UI** - Withdrawal interface for vault ore
4. **Tutorial System** - First-run tutorial, help screens
5. **Special Rooms** - Treasure rooms, monster dens, ore chambers
6. **Polish** - UX improvements, visual effects

**See:** [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md) for detailed current tasks

---

### 📅 Phase 3: Launch Prep (Dec 2025?)

**Goals:**
- Final balance tuning based on playtesting
- Bug fixes from external testing
- Player documentation
- Release candidate testing
- Performance optimization

**Ready when:** Game is polished, balanced, and fun to play repeatedly

---

### 🚀 Phase 4: Multiplayer (2026+)

**Scope:** 8-12 weeks after MVP complete

**Key features:**
- 4-player co-op
- Brilliant turn system: "4 actions per round, anyone can take them"
- NATS message bus + WebSocket architecture
- 4 character classes with synergies
- Party Legacy Vault
- Boss fights designed for 4 players

**See:** [future-multiplayer/](future-multiplayer/) directory for complete design

⚠️ **Not building multiplayer yet!** Focus on single-player polish first.

---

## 🎯 MVP Success Criteria

### ✅ Phase 1 Complete (Achieved!)
- [x] All core systems implemented (mining, crafting, equipment, save/load)
- [x] Character classes with progression
- [x] Floor descent with difficulty scaling
- [x] Meta-progression (Legacy Vault)
- [x] 858/860 tests passing (99.8%)
- [x] Game is fully playable

### ✅ Phase 2 Multiplayer Complete (Achieved - 2025-11-14!)
- [x] WebSocket server infrastructure (11 new files, ~2,400 lines)
- [x] 2+ player co-op functional
- [x] Shared dungeon generation (distributed spawning)
- [x] Turn system: "4 actions per round, anyone can take them"
- [x] Monster AI integration (nearest-player targeting)
- [x] Test client for validation

### 🎯 Phase 3 Goals (In Progress - Dual-Track)

**Single-Player Polish:**
- [ ] 30+ hours of playtesting completed
- [ ] Balance feels good across all classes
- [ ] 19 monster types ✅ (goal: 15-20)
- [ ] Tutorial system guides new players
- [ ] Special room types add variety
- [ ] No critical bugs

**Multiplayer Testing:**
- [ ] 30+ min co-op testing sessions
- [ ] Combat balance for multiplayer validated
- [ ] Delta compression (performance)
- [ ] Reconnection handling
- [ ] Class selection on join
- [ ] Personal loot system

### 🚀 Ready for Phase 4 (Launch Prep)
- [ ] All Phase 3 criteria met
- [ ] External playtesters give positive feedback (both modes)
- [ ] "One more run" factor is strong
- [ ] Performance is good (< 100ms gen, 60 FPS)
- [ ] Multiplayer stress-tested

---

## 🛠️ Development Workflow

### Getting Started
```bash
# Run the game
python3 run_textual.py

# Run tests
python3 -m pytest tests/ -v

# Run with debug logging
python3 scripts/run_debug.py
```

### Adding Content (Easy!)
```bash
# Add a monster: edit data/entities/monsters.yaml
# Add a recipe: edit data/balance/recipes.yaml
# Add an ore type: edit data/entities/ores.yaml
```

**See:** [CONTENT_CREATION.md](CONTENT_CREATION.md) for detailed guides

### Code Structure
```
src/
├── core/              # Game logic
│   ├── game.py        # Game loop
│   ├── entities.py    # Player, monsters, items
│   ├── world.py       # Map generation
│   ├── crafting.py    # Crafting system
│   ├── legacy.py      # Legacy Vault
│   ├── save_load.py   # Save/load
│   └── actions/       # All game actions
└── ui/textual/        # UI widgets
```

---

## 📚 Key Documents

### Essential Reading
- **[README.md](../README.md)** - Project overview (5 min)
- **[START_HERE.md](START_HERE.md)** - Developer onboarding (15 min)
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Comprehensive status (100% accurate)
- **[MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)** - Current priorities

### Game Design
- **[VEINBORN_CONSOLIDATED_DESIGN.md](VEINBORN_CONSOLIDATED_DESIGN.md)** - Master game design
- **[MECHANICS_REFERENCE.md](MECHANICS_REFERENCE.md)** - Detailed mechanics

### Development
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Commands, files, common tasks
- **[architecture/](architecture/)** - Technical architecture
- **[development/](development/)** - Testing, debugging guides

### Future
- **[future-multiplayer/](future-multiplayer/)** - Phase 4 design (not current!)

---

## 🗺️ Historical Roadmap (Reference)

This section preserved for reference. See PROJECT_STATUS.md for current state.

### Week 1-2: Mining System ✅ DONE
- Ore vein generation with 5 properties
- Survey action (view ore properties)
- Mining action (multi-turn, vulnerable)

### Week 3: Crafting System ✅ DONE
- Recipe system (YAML-based)
- Crafting interface
- Forge locations

### Week 4: Meta-Progression ✅ DONE
- Legacy Vault (save rare ore on death)
- Save/load system
- Statistics tracking

### Week 5-6: Polish & Content ✅ MOSTLY DONE
- Monster types expansion (19 types now)
- Recipe expansion (23 recipes now)
- Content variety
- Balance tuning

---

## 📝 Notes

### Architecture Decisions
- **MVP uses direct function calls** (not message-based)
- **Phase 4 will refactor to event-driven** for multiplayer
- **Build cleanly now** → easier refactor later

### Testing Strategy
- Unit tests for game logic
- Integration tests for systems
- Manual playtesting is primary
- Balance testing (is it fun?)

### Performance Goals
- Map generation < 100ms
- Game loop 60+ FPS
- Save/load < 500ms
- No memory leaks

---

## 🎯 Your Next Steps

### New Contributors
1. Read [START_HERE.md](START_HERE.md)
2. Run the game: `python3 run_textual.py`
3. Check [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)
4. Pick a task and start coding!

### Experienced Developers
1. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for gaps
2. Review [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md) priorities
3. Pick a high-priority task
4. Write tests, implement, playtest!

### Content Creators
1. Read [CONTENT_CREATION.md](CONTENT_CREATION.md)
2. Add monsters, recipes, or items
3. Test your additions
4. Playtest for fun factor!

---

**🎮 Let's make Veinborn awesome!**

For questions, check [INDEX.md](INDEX.md) for the complete documentation map.
