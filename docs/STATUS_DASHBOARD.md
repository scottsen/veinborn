# Veinborn Status Dashboard 🎯

**Last Updated:** 2026-09-22 (full code review + urgent-fix pass, then 4 of 5 high-priority MP-architecture findings closed same day; see `TASKS.md` `VB-16`–`VB-32`)
**Quick View:** One-page status overview

---

## 🚦 Current Status

| Category | Status | Details |
|----------|--------|---------|
| **Single-Player core** | 🟢 Healthy | All tests pass |
| **Multiplayer** | 🟡 8 critical/urgent/high bugs fixed 2026-09-22, playtest still pending | `VB-16`–`VB-23` all fixed and test-covered this session (dead-actor redirect, Lua sandbox RCE, process-global RNG cross-contamination, save/load data loss, chat delta desync after 20 messages, Pickup/Wait actions unusable in MP, reconnect race, 3-way player storage). Still no real two-client playtest. `VB-24` (SP/MP separate post-action pipelines) is done as of 2026-09-23: MP shares the outcome pipeline (messages, events, took_turn) and HP regen, the party plays on while any player is alive, and co-op runs are scored per player on their own leaderboard (`data/highscores_multiplayer.json`, no viewer yet — see `tt list --project veinborn`). |
| **Test Health** | ✅ Green | 1185 collected: 1185 passing / 0 failing / 0 skipped (verified 2026-09-23) — up from 1067/1065/0/2 baseline; the 2 previously-skipped Lua timeout tests now genuinely pass (see `VB-17`), and the flaky planner tests are seeded (`VB-34`) / given a walkable arena (`test_get_smart_action_prioritizes_forced_combat` still failed ~25% of runs after seeding) |
| **Current Phase** | 🎮 MP hardening + playtest | No open high-priority findings; the next milestone is the first real two-client playtest |
| **Playability** | ✅ SP playable / 🟡 MP no longer has known exploitable bugs, still unplaytested | |

See `docs/PROJECT_REVIEW_2026-04-17.md` for the last full architecture audit, and `TASKS.md` for the 2026-09-22 review's findings (`VB-16` onward).

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
| [PROJECT_REVIEW_2026-04-17.md](PROJECT_REVIEW_2026-04-17.md) | Detailed audit with evidence | 10 min |
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
| ~~Multiplayer state sync drops monster/map data, never diffs floor changes~~ | ~~🟠 High~~ | ✅ Fixed — `VB-4` (`0b227d3`) |
| ~~Finished multiplayer sessions never marked `is_finished` (leak)~~ | ~~🟡 Medium~~ | ✅ Fixed — `VB-5` (`b7635c2`) |
| ~~Stale `future-multiplayer/` and `~/Archive` doc references (9+ docs)~~ | ~~🟡 Medium~~ | ✅ Fixed — `VB-6` (`a8758e1`) |
| ~~`BALANCE_REVIEW.md` ore-scarcity claim is stale (real value is 8+ veins/floor, not 1)~~ | ~~🟡 Medium~~ | ✅ Fixed — `VB-7` (`fd25477`) |
| ~~Triplicated Bresenham line-of-sight (`pathfinding.py`/`perception.py` x2)~~ | ~~🟡 Medium~~ | ✅ Fixed — `VB-9` (`4b2c894`) |
| ~~`user_config.py` legacy-path deprecation warning was a no-op~~ | ~~🟢 Low~~ | ✅ Fixed — `VB-10` (`1c4bb02`) |
| ~~`Map`'s entity-placement policy mixed into BSP dungeon-gen (`world.py`)~~ | ~~🟢 Low~~ | ✅ Fixed — `VB-13` (`10f0344`) |
| ~~`lua_action.py`'s `_table_to_outcome` had 4 nested try/except + 2 manual loops~~ | ~~🟢 Low~~ | ✅ Fixed — `VB-15` (`c29e702`) |
| ~~`game_session.py` was a 775-line, 4-class file~~ | ~~🟢 Low~~ | ✅ Fixed — `VB-12` (`6a842fc`) |
| ~~`Game` god-object mixed bootstrap/event-wiring/Lua/orchestration/persistence~~ | ~~🟢 Low~~ | ✅ Fixed — `VB-11` (`891873e`) |
| ~~2 skipped Lua timeout tests~~ | ~~🟡 Low~~ | ✅ Fixed — `VB-17`: signal-based timeout genuinely could not interrupt a tight Lua loop; replaced with a `debug.sethook` instruction-count hook. Both tests now pass for real. |
| ~~Dead multiplayer player's actions silently moved the host's character~~ | ~~🔴 Critical~~ | ✅ Fixed — `VB-16` |
| ~~Lua sandbox exposed `python.eval` + dunder-attribute walk (RCE)~~ | ~~🔴 Critical~~ | ✅ Fixed — `VB-17` |
| ~~Process-global RNG singleton cross-contaminated concurrent MP games~~ | ~~🔴 Critical~~ | ✅ Fixed — `VB-18` |
| ~~Save/load dropped inventory, equipment, run_type; Forge→plain Entity~~ | ~~🔴 Critical~~ | ✅ Fixed — `VB-19` |
| ~~Multiplayer chat/message log stops syncing after 20 messages~~ | ~~🟠 High~~ | ✅ Fixed — `VB-20`: tracked by a monotonic `message_count` instead of list length, which went blind once `recent_messages` (capped at 20) stopped growing. |
| ~~Server/core action registries drifted (Pickup, Wait actions unusable in MP)~~ | ~~🟠 High~~ | ✅ Fixed — `VB-21`: `core.actions.ACTION_TYPES` is now the single source both registries build from. Lua actions still can't be deserialized in MP (needs `VB-24`'s pipeline work — MP has no `LuaRuntime` instance at all yet). |
| ~~Reconnect race can strand a player (inputs rejected, outputs dropped)~~ | ~~🟠 High~~ | ✅ Fixed — `VB-22`: `disconnect_client` is now a no-op if a fast reconnect already replaced its socket. |
| ~~Players stored 3 different ways (root cause pattern behind `VB-16`)~~ | ~~🟠 High~~ | ✅ Fixed — `VB-23`: `entities` is now the single store every lookup reads from; `GameState` keeps `.player` synced into it. |
| ~~SP/MP run separate post-action pipelines~~ | ~~🟠 High~~ | ✅ Fixed — `VB-24`: outcome handling shared via `core/action_pipeline.py` (`ca475b8`); HP regen shared via `apply_hp_regeneration()`; co-op rule = the party plays on while anyone is alive; per-player scores on a separate co-op leaderboard (`HighScoreManager.get_multiplayer_instance()`). Not done: Legacy Vault in MP, a way to view the co-op leaderboard. |
| ~~Floor progression duplicated between `FloorManager` and MP game state~~ | ~~🟡 Medium~~ | ✅ Fixed — `VB-25`: shared `spawn_all_for_floor` / `clear_floor_entities` / `generate_floor_map` / `get_victory_floor`. Also fixed two bugs it exposed: SP descent evicted the player from `entities`, and skipped special rooms after floor 1. |
| `state_delta` protocol has no sequence numbers / resync | 🟡 Medium | Partly fixed — `VB-26`: `apply_delta` split (complexity 27→10) and no longer mutates its input. Still open: `seq`/`base_seq`, client resync, shared `protocol/` package. |
| ~~`cleanup_task` busy-loops with no backoff on repeated errors~~ | ~~🟡 Medium~~ | ✅ Fixed — `VB-27`: capped exponential backoff. |
| ~~`PickupAction` has zero test coverage~~ | ~~🟡 Medium~~ | ✅ Fixed — `VB-28`: 10 tests; a pickup that took nothing no longer costs a turn. |
| ~~Action events failed to reach the EventBus (flat dicts, unknown types) — Lua/telemetry saw almost nothing~~ | ~~🟠 High~~ | ✅ Fixed — `VB-33` |
| Dead-code candidates (`perception.py` module, `GameTelemetry.log_*`) | 🟢 Low | Held — `VB-32`: need a wire-in-or-delete decision |
| No tutorial for new players | 🟢 Low | Planned for Phase 3 |

**Critical and urgent issues:** 0 open — `VB-1` through `VB-19` all fixed. **No high-priority findings remain open**; `VB-26`'s protocol half, the held `VB-32`, and the follow-ups filed from `VB-24` are what's left — see `tt list --project veinborn` / `TASKS.md`.

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

- **Detailed audit:** [PROJECT_REVIEW_2026-04-17.md](PROJECT_REVIEW_2026-04-17.md)
- **Current work:** [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)
- **Game design:** [VEINBORN_CONSOLIDATED_DESIGN.md](VEINBORN_CONSOLIDATED_DESIGN.md)
- **Architecture:** [architecture/00_ARCHITECTURE_OVERVIEW.md](architecture/00_ARCHITECTURE_OVERVIEW.md)
- **Full doc map:** [INDEX.md](INDEX.md)

---

**🎯 TL;DR (2026-08-05):** The floor 11+ crash (`VB-1`), multiplayer reconnection (`VB-2`), and multiplayer state sync (`VB-4`) are all fixed and test-covered. `VB-4` turned out deeper than "sync forgot to include it" — multiplayer never spawned monsters or handled floor descent at all; both are now implemented, with `StateDelta` diffing floor/monster/map changes and `MultiplayerClient` actually merging deltas client-side. All medium-priority follow-ups are also now fixed: stale doc references (`VB-6`), the ore-scarcity doc error (`VB-7`), and the triplicated Bresenham line-of-sight helper (`VB-9`). All low-priority items are now done too: `VB-14` (silent exception swallow now logged, version string synced, 33 dead/duplicate imports removed), `VB-8` (stale `PROJECT_STATUS.md` archived), `VB-13` (`Map`'s spawn/placement policy moved to `src/core/spawning/spawn_policy.py`), `VB-15` (`lua_table_get`/`lua_array_to_list` helpers replace `lua_action.py`'s nested try/except chain), `VB-12` (`game_session.py` split into a `player_info.py`/`session.py`/`manager.py` package), and `VB-11` (`Game` split into `GameBootstrapper` + `GameLuaIntegration` collaborators, `game.py` 584→362 lines). The `tt` tracker (`TASKS.md`) had zero open items until the 2026-09-22 review below.

**🎯 TL;DR (2026-09-22, morning):** A full code review (bug hunt + code quality + architecture, 3 parallel passes) found 17 new issues, filed as `VB-16`–`VB-32`. The 4 urgent/critical ones are now fixed and test-covered: `VB-16` (a dead multiplayer guest's action silently redirected onto the host — `Action._get_actor()`'s fallback to `context.get_player()` fired for ANY unresolved actor, not just the local player; also fixed the same pattern in `attack_action.py`'s target lookup), `VB-17` (Lua sandbox let scripts call `python.eval()` directly, and separately let any Python object handed to Lua be walked via `.__class__`/`.__globals__` dunder attributes — both closed; also discovered the existing signal-based script timeout couldn't interrupt a tight `while true do end` loop at all, confirmed by a 300s hang, and replaced it with a `debug.sethook` instruction-count hook hardened against `pcall`-retry evasion), `VB-18` (`GameRNG` was a process-global singleton that `multiplayer_game_state.add_player()` reseeded on every new game, silently corrupting any other concurrent game's randomness — now each game gets its own `GameRNG` instance threaded through `Map.rng`/`GameState.rng`/`GameContext.get_rng()`), and `VB-19` (save/load dropped inventory, equipped gear, `run_type`, and reconstructed `Forge` as a plain non-interactable `Entity` — plus a second bug found mid-fix: `_deserialize_state` had its own separate, more-stripped-down inline player reconstruction that didn't even go through the entity deserializer). Test suite grew from 1067 to 1109 (all passing, 0 skipped — the 2 previously-skipped Lua timeout tests now genuinely pass).

**🎯 TL;DR (2026-09-22, afternoon):** Closed 4 of the 5 remaining high-priority findings, same day: `VB-20` (chat/log delta went permanently blind once >20 messages had ever been sent — `recent_messages` is capped at 20, so the old `len(new) > len(old)` check stopped firing; now tracked by a monotonic `message_count`), `VB-21` (server's `ActionRegistry` and core's action classes had drifted into 3 separately hand-maintained import lists — Pickup was missing, and self-discovered mid-fix, so was `WaitAction`; now one canonical `core.actions.ACTION_TYPES` map, with a test that fails if a future action class isn't registered or explicitly excluded), `VB-22` (a fast reconnect racing a dying socket's cleanup could strand a player — `disconnect_client` now no-ops if the socket it's closing was already superseded), and `VB-23` (players stored 3 different ways — `entities` is now the single store every lookup reads from; `GameState` keeps `.player` synced into it on construction and reassignment, which also let `Action._get_actor()` drop the VB-16 fallback entirely and fixed a real, live blind spot: `get_entity_at` genuinely couldn't find the multiplayer host at their own tile before this). Test suite grew from 1109 to 1127. `VB-24` (SP/MP separate post-action pipelines) was investigated but deliberately NOT started: it needs an N-player HP-regen/game-over design decision first, not a mechanical refactor — see `tt show VB-24` for the full writeup and a recommended smaller first slice.

---

**Last Updated:** 2026-09-22
**Next Update:** When `VB-24` is picked up (after the design decision it needs), or new work is filed via `tt add --project veinborn`
