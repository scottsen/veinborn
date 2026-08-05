# Veinborn Status Dashboard 🎯

**Last Updated:** 2026-04-17 (validated against code & tests; see `PROJECT_REVIEW_2026-04-17.md`)
**Quick View:** One-page status overview

---

## 🚦 Current Status

| Category | Status | Details |
|----------|--------|---------|
| **Single-Player core** | 🟢 Healthy | All tests pass; action factory drift fixed (0449d66) |
| **Multiplayer** | 🟡 Server tests green, playtest pending | `WaitAction` created, `GameSession` uses `GameContext`, lock-reentrancy deadlock fixed, leave-game semantics unified (0449d66 + 33d72f7). No real two-client playtest yet. |
| **Test Health** | ✅ Green | 1067 collected: 1065 passing / 0 failing / 2 skipped (verified 2026-04-17 after commit 33d72f7) |
| **Current Phase** | 🎮 MP playtest + polish | Run real two-client session to validate end-to-end; continue SP polish |
| **Playability** | ✅ SP playable / 🟡 MP ready for playtest | |

See `docs/PROJECT_REVIEW_2026-04-17.md` for full evidence.

**Codebase Stats:**
- **114+ Python files**
- **~17,400 lines of code**
- **11 new multiplayer files** (~2,400 lines)

---

## 🎯 Top 3 Priorities (What to Work On NOW)

### 1️⃣ **Extended Multiplayer Testing** 🔴 CRITICAL
- Test 30+ minutes of 2-player co-op
- Validate combat balance with multiple players
- Document edge cases and bugs
- **Why:** Phase 2 just completed, needs validation

### 2️⃣ **Single-Player Balance Tuning** 🟡 HIGH
- Playtest extensively (30-60 min sessions)
- Tune monster difficulty progression
- Balance ore spawn rates and crafting formulas
- **Why:** Core gameplay needs refinement

### 3️⃣ **Tutorial System** 🟢 MEDIUM
- First-run tutorial for new players
- Help screen (H key)
- Keybind reference
- **Why:** Usability and onboarding

---

## ✅ What's Working (Complete Systems)

### Single-Player (100% Complete)
- ✅ Mining system (survey ore, mine over turns)
- ✅ Crafting system (recipes, stat calculation)
- ✅ Equipment system (weapons, armor, bonuses)
- ✅ Save/Load system (game state persistence)
- ✅ Character classes (4 classes with different stats)
- ✅ Floor progression (stairs, difficulty scaling)
- ✅ Legacy Vault (meta-progression)
- ✅ Combat system (turn-based tactical)
- ✅ Monster AI (pathfinding, aggression)
- ✅ Lua Event System (Phase 3 complete)

### Multiplayer (Phase 2 Complete - 2025-11-14)
- ✅ WebSocket server infrastructure
- ✅ 2+ player co-op working
- ✅ Shared dungeon generation
- ✅ Distributed player spawning
- ✅ Turn system ("4 actions per round")
- ✅ Monster AI integration
- ✅ Nearest-player targeting

---

## 🚧 What's In Progress

### Track A: Single-Player Polish
- [ ] Balance tuning
- [ ] Tutorial system
- [ ] Special room types (treasure, shrine, trap)
- [ ] Polish & UX improvements

### Track B: Multiplayer Phase 3
- [ ] Extended co-op testing (30+ min)
- [ ] Combat balance for multiplayer
- [ ] Delta compression (performance)
- [ ] Reconnection handling
- [ ] Class selection on join
- [ ] Personal loot system

---

## 📅 Recent Milestones (November 2025)

| Date | Milestone | Impact |
|------|-----------|--------|
| **Nov 14** | 🎉 Multiplayer Phase 2 Complete | +2,400 lines, 11 new files |
| **Nov 13** | Monster AI targeting (nearest player) | Smart co-op AI |
| **Nov 12** | Distributed player spawning | Players start in different rooms |
| **Nov 11** | Multiplayer game functionality | Turn system working |
| **Nov 10** | Multiplayer design finalized | Clear roadmap |
| **Nov 5** | Documentation cleanup | Truth alignment |

---

## 🗺️ Phase Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 0** | ✅ Complete | Foundation (movement, combat, map gen) |
| **Phase 1** | ✅ Complete | MVP Core (mining, crafting, classes) |
| **Phase 2** | ✅ Complete | Multiplayer infrastructure (co-op working!) |
| **Phase 3** | 🔨 Current | Testing + Polish (both tracks) |
| **Phase 4** | 📅 Future | Advanced features (persistence, bosses) |

---

## 🎮 How to Play

### Single-Player
```bash
./veinborn              # Normal mode
./veinborn --debug      # Debug logging
./veinborn --safe       # Terminal reset on crash
```

### Multiplayer (NEW!)
```bash
# Terminal 1: Start server
python3 src/server/run_server.py

# Terminal 2: Connect player 1
python3 src/server/test_client.py

# Terminal 3: Connect player 2
python3 src/server/test_client.py
```

**Then:** Create game → Join → Ready → Start → Play together!

---

## 📚 Key Documentation

| Doc | Purpose | Time to Read |
|-----|---------|--------------|
| **This file** | At-a-glance status | 2 min |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Comprehensive status | 10 min |
| [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md) | Current priorities | 5 min |
| [design/MULTIPLAYER_DESIGN_2025.md](design/MULTIPLAYER_DESIGN_2025.md) | Multiplayer design | 30 min |
| [README.md](../README.md) | Project overview | 5 min |
| [START_HERE.md](START_HERE.md) | Developer onboarding | 15 min |

---

## 🔥 Quick Stats

**Development Velocity:**
- **5 PRs merged** in November 2025
- **Phase 2 completed** ahead of schedule (was projected 8-12 weeks!)
- **Dual-track development** now active

**Quality Metrics:**
- **100% test pass rate**
- **5/5 architectural improvements complete**
- **5/5 Lua integration readiness**
- **4.8/5 architecture quality**

**Content:**
- **19 monster types** (exceeds 15-20 goal!)
- **23 recipes** (6 legendary)
- **4 character classes**
- **4 ore types**

---

## 🚨 Known Issues

**Full tracker:** `tt list --project veinborn` (see `TASKS.md`) — this table is a summary only.

| Issue | Severity | Status |
|-------|----------|--------|
| ~~Floor 11+ crashes on descend (`KeyError: 'floors_11_plus'` in `config_loader.py:92`)~~ | ~~🔴 Critical~~ | ✅ Fixed — `VB-1` (`b7635c2`) |
| ~~Multiplayer reconnection is non-functional end-to-end (auth never resumes a session)~~ | ~~🔴 Critical~~ | ✅ Fixed — `VB-2` (`8622a11`) |
| ~~Seeded multiplayer game creation crashes (`GameRNG.seed` property called as a method)~~ | ~~🟠 High~~ | ✅ Fixed — `VB-3` (`b7635c2`) |
| Multiplayer state sync drops monster/map data, never diffs floor changes | 🟠 High | `VB-4` |
| ~~Finished multiplayer sessions never marked `is_finished` (leak)~~ | ~~🟡 Medium~~ | ✅ Fixed — `VB-5` (`b7635c2`) |
| Stale `future-multiplayer/` and `~/Archive` doc references (9+ docs) | 🟡 Medium | `VB-6` |
| `BALANCE_REVIEW.md` ore-scarcity claim is stale (real value is 8+ veins/floor, not 1) | 🟡 Medium | `VB-7` |
| 2 skipped Lua timeout tests | 🟡 Low | C-level execution limitation (acceptable) |
| No tutorial for new players | 🟢 Low | Planned for Phase 3 |

**Critical issues:** 0 open — `VB-1` and `VB-2` fixed 2026-08-05. `VB-4` (high) is the highest-priority remaining item.

---

## 💡 For New Contributors

**Want to help? Start here:**

1. **Read this dashboard** (you're doing it!)
2. **Play the game** - `./veinborn`
3. **Pick a priority** from "Top 3 Priorities" above
4. **Read the relevant doc** from "Key Documentation"
5. **Start coding!**

**Easy first tasks:**
- Playtest and document balance issues
- Add new monster types to `data/entities/monsters.yaml`
- Add new recipes to `data/balance/recipes.yaml`
- Test multiplayer co-op and report bugs

---

## 📞 Need More Info?

- **Comprehensive status:** [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Current work:** [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)
- **Game design:** [VEINBORN_CONSOLIDATED_DESIGN.md](VEINBORN_CONSOLIDATED_DESIGN.md)
- **Architecture:** [architecture/00_ARCHITECTURE_OVERVIEW.md](architecture/00_ARCHITECTURE_OVERVIEW.md)
- **Full doc map:** [INDEX.md](INDEX.md)

---

**🎯 TL;DR (2026-08-05):** The floor 11+ crash (`VB-1`) and multiplayer reconnection (`VB-2`) are both fixed and test-covered — single-player and reconnect-after-disconnect should now both work end-to-end. Multiplayer state sync still silently drops monster/map data and never diffs floor changes (`VB-4`, ~1d estimate) — "Phase 2 complete" should not be claimed until that closes too. Full findings and fixes are tracked in `TASKS.md` (`tt list --project veinborn`), not just this dashboard.

---

**Last Updated:** 2026-08-05
**Next Update:** After VB-4 is resolved
