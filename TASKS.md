---
project: veinborn
schema_version: '1.0'
id_prefix: VB
next_id: 88
archival: inline
areas: {}
---

## TASK-VB-1 · Floor-11 KeyError crash: get_monster_spawn_weights() references nonexistent 'floors_11_plus' key

```yaml
status: done
priority: urgent
effort: 30m
tags: [bug, crash]
created: '2026-08-05T06:31:18Z'
updated: '2026-08-05T06:50:15Z'
session: yaeger-zealot-0804
links:
  commits:
  - b7635c2b027fa716a7969ab9e735588060499e99
notes_next: 2
```

config_loader.py:92 does weights['floors_11_plus'] but data/balance/monster_spawns.yaml only has floors_11_15/floors_16_plus keys. Reproduced directly: config.get_monster_spawn_weights(11) raises KeyError. Uncaught anywhere in the call chain (entity_spawner.py -> floor_manager.py -> game.py:282 -> UI descend handler). Blocks ~90% of the game's intended floor range (victory_floor=100).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T06:50:15Z session:neural-queen-0804] config_loader now matches actual floors_11_15/floors_16_plus keys


## TASK-VB-2 · Multiplayer reconnection is non-functional end-to-end

```yaml
status: done
priority: urgent
effort: 4h
tags: [bug, multiplayer]
created: '2026-08-05T06:31:18Z'
updated: '2026-08-05T06:55:17Z'
session: yaeger-zealot-0804
links:
  references:
  - docs/PROJECT_REVIEW_2026-04-17.md
  commits:
  - b7635c2b027fa716a7969ab9e735588060499e99
  - 8622a113d7e431fada7187bd1f4f514cc96a41b5
notes_next: 3
```

AuthManager.create_session (auth.py:52-78) always mints a new player_id/session_id; verify_token() is dead code, never called; auth_token generated but never sent to client (websocket_server.py Message.auth_success). handle_reconnect (websocket_server.py:342-378) rejects any reconnect because session.game_id is None on the fresh session. All disconnect-timeout/AI-takeover machinery in game_session.py (lines 191-296, 422-486) is unreachable dead functionality from the client's perspective.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T06:55:01Z session:neural-queen-0804] auth resume via auth_token wired into authenticate_connection; client gained reconnect()
- [#2 2026-08-05T06:55:17Z session:neural-queen-0804] auth resume via auth_token wired into authenticate_connection; client gained reconnect()


## TASK-VB-3 · Seeded multiplayer game creation crashes: GameRNG.seed property called as a method

```yaml
status: done
priority: high
effort: 15m
tags: [bug, multiplayer]
created: '2026-08-05T06:31:18Z'
updated: '2026-08-05T06:50:15Z'
session: yaeger-zealot-0804
links:
  commits:
  - b7635c2b027fa716a7969ab9e735588060499e99
notes_next: 2
```

multiplayer_game_state.py:94 calls rng.seed(self.seed) but GameRNG.seed (rng.py:123) is a read-only @property, not a method -> TypeError: 'NoneType' object is not callable. Reproduced directly. Not hit by the live websocket flow today (no client passes a seed), but GameSession.start_game(seed=...) passes it straight through -- landmine for the first seeded/competitive-match feature.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T06:50:15Z session:neural-queen-0804] seed via GameRNG.initialize() instead of calling read-only seed property


## TASK-VB-4 · Multiplayer state sync silently drops monster/map data and never diffs floor changes

```yaml
status: done
priority: high
effort: 1d
tags: [bug, multiplayer]
created: '2026-08-05T06:31:18Z'
updated: '2026-08-05T16:56:36Z'
session: yaeger-zealot-0804
links:
  commits:
  - 0b227d37278c7840c04c7ca9078fbba02747fadb
notes_next: 2
```

get_state_dict() (multiplayer_game_state.py:233-303) never includes monster or dungeon-map data at all. StateDelta.compute_delta (state_delta.py:34-101) never diffs current_floor. After the first full-state broadcast, clients have no wire-protocol channel for monster positions or floor changes -- real desync gap.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T16:56:36Z session:runic-sword-0805] Fixed: monster/floor spawning wired into MP, descend_floor event wired, state_delta diffs floor/monsters/map, client applies deltas


## TASK-VB-5 · game_over never propagates to GameSession.is_finished -- finished MP sessions leak

```yaml
status: done
priority: medium
effort: 1h
tags: [bug, multiplayer]
created: '2026-08-05T06:31:18Z'
updated: '2026-08-05T06:50:15Z'
session: yaeger-zealot-0804
links:
  commits:
  - b7635c2b027fa716a7969ab9e735588060499e99
notes_next: 2
```

multiplayer_game_state.py:333-344 sets game_state.game_over=True when all players die, but nothing propagates it into GameSession.is_finished (game_session.py). Session lingers in GameSessionManager._games indefinitely unless every player also explicitly leaves.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T06:50:15Z session:neural-queen-0804] game_over now propagates to session.is_finished in process_action paths


## TASK-VB-6 · Stale future-multiplayer/ and ~/Archive doc references across 9+ docs

```yaml
status: done
priority: medium
effort: 2h
tags: [docs]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T17:27:11Z'
session: yaeger-zealot-0804
links:
  references:
  - docs/architecture/00_ARCHITECTURE_OVERVIEW.md
  commits:
  - a8758e12a11293bbc7c27981d8f8996d141f044d
notes_next: 2
```

docs/architecture/00_ARCHITECTURE_OVERVIEW.md and 8 other docs still point at docs/future-multiplayer/, which does not exist in the repo. ~9 docs (INDEX.md, PROJECT_STATUS.md, architecture/DECISIONS.md, etc.) cite repo-external ~/Archive/... paths not portable for contributors. docs/README.md:154 already flags this as an open trust-restore item.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T17:27:11Z session:beige-twilight-0805] Fixed banner text in DECISIONS.md/README.md/MVP_TESTING_GUIDE.md/MVP_DEVELOPMENT_GUIDELINES.md to stop exposing the non-portable ~/Archive/... machine-local path (pointed to docs/INDEX.md instead, which already documents the archival policy correctly). Annotated/rewrote ~25 individual dead docs/future-multiplayer/... references across those 4 docs plus 00_ARCHITECTURE_OVERVIEW.md to point at docs/design/MULTIPLAYER_DESIGN_2025.md (the design that actually shipped) instead of a nonexistent path. Also updated STATUS_DASHBOARD.md/docs/README.md to reflect completion.


## TASK-VB-7 · BALANCE_REVIEW.md ore-scarcity claim is stale/wrong

```yaml
status: done
priority: medium
effort: 30m
tags: [docs, balance]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T17:22:22Z'
session: yaeger-zealot-0804
links:
  references:
  - docs/development/BALANCE_REVIEW.md
  commits:
  - fd25477f821486309dae4c0b9faaa0fabd61c956
notes_next: 2
```

Doc claims 'only 1 ore vein on floors 1-9' as the #1 critical balance concern. Real value is 8+ per floor (data/balance/ore_veins.yaml, base:8, confirmed as the actually-loaded config via config_loader.py:104). The '1 vein' figure matches a dead/unused block in game_constants.yaml (spawning.ore_vein_scaling) that nothing reads. Correct the doc before it drives design decisions.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T17:22:22Z session:beige-twilight-0805] Resource Availability table and Configuration Summary bullet still had the stale '1 vein/floor' figures even though Summary/Potential Balance Issues were already corrected in a prior session. Replaced table with real per-tier vein counts and spawn weights from ore_veins.yaml/config_loader.py.


## TASK-VB-8 · PROJECT_STATUS.md still marked under revalidation, never revalidated

```yaml
status: done
priority: low
effort: 1h
tags: [docs]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T17:48:46Z'
session: yaeger-zealot-0804
links:
  references:
  - docs/PROJECT_STATUS.md
  commits:
  - 4a6209501ba1fcd46b9416ca589b310bcb6ea749
notes_next: 2
```

Linked from START_HERE.md and INDEX.md as 'comprehensive status' but flagged under revalidation since the 2026-04-17 PROJECT_REVIEW. Either revalidate its claims against current code/tests or fold it into STATUS_DASHBOARD.md and archive it.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T17:48:46Z session:steel-sunbeam-0805] Archived docs/PROJECT_STATUS.md to docs/.archived/PROJECT_STATUS_2026-01-13.md (never rewritten since the 2026-04-17 revalidation flag; STATUS_DASHBOARD.md + PROJECT_REVIEW_2026-04-17.md already cover accurate current status). Repointed ~30 live references across 12 docs to STATUS_DASHBOARD.md and cleaned up stale 'under revalidation' phrasing.


## TASK-VB-9 · Extract shared Bresenham line-of-sight helper (triplicated in pathfinding.py/perception.py x2)

```yaml
status: done
priority: medium
effort: 2h
tags: [refactor, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T17:14:37Z'
session: yaeger-zealot-0804
links:
  commits:
  - 4b2c89424efaec11bab07cf9bf309eb0d05936a1
notes_next: 2
```

pathfinding.py:187, perception.py:127, perception.py:351 each hand-roll the same Bresenham stepping loop with different signatures. A fix to one (e.g. an off-by-one) won't propagate to the others.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T17:14:37Z session:beige-twilight-0805] Extracted bresenham_line() and has_line_of_sight() into new src/core/geometry.py. pathfinding._line_of_sight, perception.VisibilitySystem._has_line_of_sight, and perception.PerceptionSystem._has_line_of_sight all now delegate to the shared helper instead of hand-rolling the stepping loop. Added tests/unit/test_geometry.py (10 tests); all 60 targeted tests (geometry+perception+pathfinding) pass. No circular imports introduced (reveal imports:// verified).


## TASK-VB-10 · user_config.py deprecation path is a no-op (self.replace bug + duplicate CONFIG_PATHS)

```yaml
status: done
priority: low
effort: 15m
tags: [bug, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T17:12:40Z'
session: yaeger-zealot-0804
links:
  commits:
  - 00089faeef4425f5cdcd5f4297cc0e80cd965bb9
  - 1c4bb022f5c90b932817237d170c59d3b5ec2ea8
notes_next: 3
```

user_config.py ~line 95: new_path = str(path).replace('veinborn','veinborn') replaces a string with itself. CONFIG_PATHS lists the same 3 paths twice under 'preferred' and 'legacy' labels with identical values -- the deprecation warning always fires with a nonsensical message.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T17:12:26Z session:beige-twilight-0805] user_config.py: legacy CONFIG_PATHS/legacy_paths were clobbered to identical veinborn paths by the brogue->veinborn rename (33399a1), making the deprecation warning always no-op. Restored legacy paths to .broguerc/etc and fixed the replace() call. Added 2 regression tests to test_config.py.
- [#2 2026-08-05T17:12:40Z session:beige-twilight-0805] Corrected commit reference to the actual fix commit.


## TASK-VB-11 · Split Game god-object into bootstrap/Lua-integration/orchestration

```yaml
status: done
priority: low
effort: 1d
tags: [refactor, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T18:19:50Z'
session: yaeger-zealot-0804
links:
  commits:
  - 891873e33509c6e19d520f5f78d26325643dfbd0
notes_next: 2
```

game.py: 1 class, 20 methods, 23 imports, 5 mixed responsibilities (bootstrap, event wiring, Lua integration, turn orchestration, persistence). handle_player_action is a single chokepoint for all 7 UI callers.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T18:19:50Z session:fowevado-0805] Split game.py (584 lines, 20 methods, 5 mixed responsibilities) via composition: GameBootstrapper (src/core/game_bootstrap.py, world/subsystem construction) and GameLuaIntegration (src/core/game_lua_integration.py, event wiring + Lua). Game keeps all public attrs/methods unchanged (game.turn_processor/floor_manager etc still direct attrs, matching what app.py's 7 UI callers and tests/integration/test_phase5_integration.py depend on). game.py 584->362 lines. 1094/2 tests pass; manual smoke test of start_new_game->handle_player_action->save_game->load_game round trip confirmed all subsystems wire correctly.


## TASK-VB-12 · Split game_session.py: PlayerConnectionState + GameSession + GameSessionManager

```yaml
status: done
priority: low
effort: 1d
tags: [refactor, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T18:13:55Z'
session: yaeger-zealot-0804
links:
  commits:
  - 6a842fc9a0bb4dea16fa9630030cb177cf021d60
notes_next: 2
```

760 lines, 4 classes in one file, worst nesting in the repo (depth 4-5). process_action has exactly 1 caller yet complexity 13 -- the complexity is not reused/amortized, just deeply nested inline logic.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T18:13:55Z session:fowevado-0805] Split game_session.py (775 lines, 4 classes) into src/server/game_session/ package: player_info.py (ConnectionStatus+PlayerInfo), session.py (GameSession), manager.py (GameSessionManager); __init__.py re-exports all four so existing import paths are unchanged. Also fixed process_action's complexity (13->clean, nesting 5->clean) by extracting shared _advance_round_if_complete/_apply_floor_transitions helpers, deduping logic that was also inline-copied in process_disconnected_player_action. cleanup_expired_disconnections nesting fixed with a guard clause. 1094/2 tests pass, no import cycles, all 148 game_session/websocket/reconnection/chat/multiplayer tests pass.


## TASK-VB-13 · Move Map's entity-placement policy (find_monster/ore/player positions) out of world.py into src/core/spawning/

```yaml
status: done
priority: low
effort: 3h
tags: [refactor, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T18:01:37Z'
session: yaeger-zealot-0804
links:
  commits:
  - 10f03440c279bf469657f3eb27c525f2c871dc29
notes_next: 2
```

world.py's Map mixes BSP dungeon-generation algorithm with domain-specific spawn policy (find_player_spawn_positions, find_monster_positions, find_ore_vein_positions, assign_special_rooms, place_stairs). Couples dungeon generation to every future entity type.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T18:01:37Z session:fowevado-0805] Extracted find_player_spawn_positions/find_monster_positions/find_ore_vein_positions/assign_special_rooms/place_stairs_down/place_stairs_up + helpers into src/core/spawning/spawn_policy.py; Map keeps thin delegating methods (lazy-imported to avoid circular import). Also fixed a latent NameError (undefined logger) found during the move. 1094/2 tests pass, no import cycles.


## TASK-VB-14 · Quick-win code cleanup: silent except swallow, stale version string, unused/duplicate imports

```yaml
status: done
priority: low
effort: 1h
tags: [code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T17:44:56Z'
session: yaeger-zealot-0804
links:
  commits:
  - 7e2e9c3354852feab4cfd8f5f995ddefc4561553
notes_next: 2
```

websocket_server.py:509 except Exception: pass with zero logging around socket close. server/__init__.py __version__='0.1.0' vs pyproject.toml 0.4.0. ~32 unused imports (I001) and 7 duplicate imports (I005) confirmed via reveal check, zero risk to remove.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T17:44:56Z session:steel-sunbeam-0805] Fixed silent except swallow (logged instead), synced __version__ to pyproject.toml, removed 33 dead/duplicate imports (kept 6 reveal false-positives — function-local re-imports needed per-scope to avoid circular imports). Full test suite passes (1094 passed, 2 skipped).


## TASK-VB-15 · Lua/Python boundary cleanup: coercion helper for _table_to_outcome

```yaml
status: done
priority: low
effort: 2h
tags: [refactor, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T18:07:47Z'
session: yaeger-zealot-0804
links:
  commits:
  - c29e7024e32e3ecc2dd0ffa751d69f44308e09d1
notes_next: 2
```

lua_action.py:241 _table_to_outcome uses 5 separate nested try/except blocks (cx16-19, depth 6) instead of one lua_table_get(table, key, default, coerce) helper. lua_event_handler.py load/handle look like they'd benefit from the same helper.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-08-05T18:07:47Z session:fowevado-0805] Added src/core/scripting/lua_utils.py (lua_table_get, lua_array_to_list); rewrote lua_action.py's _table_to_outcome to use them, dropping nesting 6->3 and complexity 19->8 (reveal C901/C905/C902 all now clean). lua_event_handler.py checked but doesn't have the repeated pattern, left as-is. 1094/2 tests pass.


## TASK-VB-16 · Dead multiplayer player's actions move the host's character

```yaml
status: done
priority: urgent
effort: small
tags: [multiplayer, bug, security]
created: '2026-09-23T05:25:41Z'
updated: '2026-09-23T05:35:07Z'
session: earthly-god-0922
notes_next: 2
```

core/base/action.py:147-171 (and mine_action.py:81, craft_action.py:172, attack_action.py:86) fall back to context.get_player() when an actor lookup fails. Dead entities are purged from 'entities' each round, so an action sent for a dead player's ID silently redirects to the host. Reproduced: killed player 2, sent MoveAction with player 2's id, host moved instead. Fix: reject actions whose actor isn't alive in session.py:process_action; remove the get_player() fallback from Action._get_actor/_get_and_validate_actor and fail validation instead. Add a regression test.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T05:35:07Z session:earthly-god-0922] Fixed: Action._get_actor()/_get_and_validate_actor() only fall back to context.get_player() when actor_id genuinely equals the player's own entity_id, not for any unresolved actor. Removed duplicate _get_actor overrides in mine_action.py/craft_action.py (now inherit the fixed base). Fixed attack_action.py's _get_attacker_and_target to stop falling back to the player for a missing target too. Aligned player_entity.entity_id with its logical dict key in multiplayer_game_state.add_player() (host='player', guests='player_xxxx') so the fix doesn't break legitimate host action resolution. Added regression test test_process_action_dead_guest_does_not_redirect_to_host (tests/unit/server/test_game_session.py) and rewrote the stale test_get_actor_fallback_to_player test that had codified the bug as expected behavior. All targeted suites pass (183 tests: actions, stairs_descent, game_session, multiplayer_game_state, multiplayer_flow integration, equipment_system).


## TASK-VB-17 · Lua sandbox exposes python bridge — arbitrary Python execution from scripts

```yaml
status: done
priority: urgent
effort: small
tags: [security, lua]
created: '2026-09-23T05:25:45Z'
updated: '2026-09-23T05:47:46Z'
session: earthly-god-0922
notes_next: 2
```

core/scripting/lua_runtime.py:52 builds lupa.LuaRuntime with defaults (register_eval/register_builtins) and no attribute_filter; io/os are removed but the python bridge is left live. Reproduced: execute_script("return python.eval('__import__(\"os\").getcwd()')") returned the real working directory. Also call_function's timeout param (:233) is read but never enforced — _execute_with_timeout uses SIGALRM (main-thread only) and truncates to whole seconds. Fix: LuaRuntime(register_eval=False, register_builtins=False, attribute_filter=...), nil out python/string.dump/collectgarbage/rawset on metatables, replace signal-based timeout with an instruction-count hook. Must fix before shipping any user/mod scripts or server-side Lua.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T05:47:46Z session:earthly-god-0922] Fixed all three parts. (1) RCE: LuaRuntime now built with register_eval=False, register_builtins=False, closing the python.eval() bridge. (2) Dunder-attribute sandbox escape: added attribute_filter blocking any underscore-prefixed attribute (obj.__class__ etc.) on any Python object/bound method handed to Lua -- this was a second, independent escape route since every veinborn.* API method is a live bound method. (3) Timeout enforcement was fully broken, not just imprecise: proved a signal-based timeout cannot interrupt a tight Lua loop with no Python callbacks (a 'while true do end' script ran past a 300s SIGALRM wall-clock timeout without ever raising). Replaced it with a debug.sethook() instruction-count hook (fires every 1000 VM instructions regardless of what the script is doing), with pcall/xpcall hardened to detect-and-re-raise the timeout sentinel so a script can't neutralize it via 'while true do pcall(fn) end' retry-loops. Wired the same deadline into call_function(), which previously accepted a timeout kwarg but never enforced it. Un-skipped the two long-standing timeout tests in test_lua_runtime.py (previously skip-reasoned 'signal-based timeout doesn't work reliably') -- they now pass for real; this was the documented 'C-level execution limitation (acceptable)' in STATUS_DASHBOARD.md's known issues, now actually fixed rather than accepted. Added 5 new regression tests (RCE, builtins, dunder-walk, pcall-evasion). Full suite run: 421 tests across lua_*, server, actions, stairs_descent, multiplayer_flow, equipment_system -- all pass.


## TASK-VB-18 · Process-global RNG singleton cross-contaminates concurrent multiplayer games

```yaml
status: done
priority: urgent
effort: medium
tags: [multiplayer, bug, rng]
created: '2026-09-23T05:25:50Z'
updated: '2026-11-13T01:09:07Z'
session: earthly-god-0922
notes_next: 3
```

GameRNG is a class-level singleton (core/rng.py:75-112). multiplayer_game_state.py:100-102 calls GameRNG.initialize(self.seed) unconditionally when the first player joins a new game, which replaces the shared process-wide instance. Every dungeon-gen/spawn/loot call site (world.py, entity_spawner.py, spawn_policy.py, entity_loader.py:242, entities.py:322) reads via GameRNG.get_instance() -- the same shared object. Two games running concurrently on one server stomp each other's RNG stream: starting game B mid-session silently rewires game A's in-flight combat rolls, loot, and future dungeon-gen to draw from game B's seed. Breaks per-game determinism/reproducibility. Fix: give each GameState its own GameRNG instance threaded through GameSession/MultiplayerGameState and exposed via ctx.rng; also remove ai_system.py's direct stdlib random module usage (lines ~436,441) which never replays from a seed either.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T05:56:31Z session:earthly-god-0922] Fixed: each game now gets its own dedicated GameRNG instance instead of every generation/spawn call reaching for the process-global GameRNG.get_instance() singleton. Map now holds self.rng (captured at construction, defaults to the singleton only for back-compat callers); world.py's split_node/create_rooms/connect_rooms, spawn_policy.py's ore-position/special-room functions, and entity_spawner.py's weighted-choice/treasure-room/monster-den/ore-chamber methods all read the owning map's .rng instead of calling GameRNG.get_instance() fresh. entity_loader.create_ore_vein() takes an explicit rng param now (falls back to the singleton only when omitted). multiplayer_game_state.add_player() constructs GameRNG(seed) directly and threads it through GameState.rng/dungeon_map.rng, instead of calling GameRNG.initialize(seed) which reassigned the shared class-level singleton out from under any other concurrent game; descend_floor() reuses the same instance for the next floor. Added GameState.rng field and GameContext.get_rng(); ai_system.py's _wander() now uses context.get_rng() instead of stdlib random (removed the direct import). save_load.py's _deserialize_state() restores RNG state into a dedicated per-load instance (state.rng/dungeon_map.rng) instead of writing into the global singleton, so a loaded game's continued play can't be corrupted by another concurrent game either -- required updating two existing tests (test_rng_state_restored, test_seeded_run_continues_correctly) that had asserted against GameRNG.get_instance() by design. Added test_concurrent_games_do_not_share_rng_stream (tests/unit/server/test_multiplayer_game_state.py) proving two concurrently-started MultiplayerGameStates get independent RNG streams and dungeon layouts. Full suite: 1102 tests pass (up from 1067 baseline; net new/updated tests from this work plus VB-16/17).
- [#2 2026-11-13T01:09:07Z session:quantum-energy-1112] Leftover fixed 45ea525 (quantum-energy-1112): Player._level_up still rolled HP from GameRNG.get_instance(), so level-up HP after a load / in multiplayer came from the global stream (runtime-confirmed: global advanced, game RNG untouched). gain_xp now takes rng=context.get_rng(). Remaining global fallbacks are only when no rng is passed (generate_loot, create_ore_vein, Map) and create_player_from_class/create_item at character creation.


## TASK-VB-19 · Save/load silently drops inventory, equipment, run_type; Forge deserializes as plain Entity

```yaml
status: done
priority: urgent
effort: medium
tags: [bug, save-load]
created: '2026-09-23T05:26:04Z'
updated: '2026-09-23T06:02:20Z'
session: earthly-god-0922
notes_next: 2
```

save_load.py: _serialize_entity (219-237) skips inventory, equipped_weapon, equipped_armor, and blocks_movement; _serialize_state (200-217) skips run_type. _deserialize_entity (325-366) has a hard-coded class switch so Forge entities come back as plain Entity. Reproduced round-trip: inventory 1 -> 0, run_type legacy -> pure, Forge -> Entity. VERSION field exists (save_load.py:45) but a version mismatch only logs a warning -- migration is a literal TODO (132-134). Loading also creates two separate player objects; only game.py:336 re-links them, a hidden requirement for any other caller of SaveSystem. A second serializer (Entity.to_dict/from_dict in core/base/entity.py:220,226) exists in parallel and can drift further. Fix: serialize through each class's own to_dict/from_dict via a type registry, add a version migration chain, add a round-trip property test.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T06:02:20Z session:earthly-god-0922] Fixed the concrete data-loss bugs. _serialize_entity now includes inventory (recursively serialized), equipped_weapon, equipped_armor, and blocks_movement, plus type-specific fields needed to reconstruct the right subclass: OreVein's ore_type/hardness/conductivity/malleability/purity/density and Forge's forge_type. _deserialize_entity gained a Forge branch (previously fell through to a plain, non-interactable Entity) and now passes the type-specific fields into each subclass's constructor so __post_init__ derives correct name/stats instead of reverting to defaults (a loaded ore vein previously silently became a default 50-quality copper vein regardless of what was actually mined). _serialize_state/_deserialize_state now round-trip run_type. Also found and fixed a second, separate bug while testing: _deserialize_state had its own inline stripped-down Player reconstruction (entity_id/name/x/y/hp/max_hp/attack/defense/stats/is_alive/content_id only) completely independent of _deserialize_entity's Player branch -- so even after fixing _deserialize_entity, the PRIMARY player (state.player, as opposed to player-type entities in state.entities) still lost inventory/equipment/blocks_movement on every load. Fixed by having _deserialize_state delegate to _deserialize_entity instead of duplicating the logic. Added 7 regression tests (TestVB19DataFidelity in tests/unit/test_save_load.py) covering inventory, equipped weapon/armor, empty-equipment-stays-none, run_type, OreVein properties with non-default values, Forge type identity, and blocks_movement. Full suite: 1109 tests pass. NOT done: the version-migration chain (VERSION mismatch still just logs a warning) -- out of scope for this pass since there's only ever been one save format version (1.0.0) shipped, so there's nothing to migrate from yet; worth a follow-up once a v2 format is actually introduced.


## TASK-VB-20 · Multiplayer chat/message log silently stops syncing after 20 messages

```yaml
status: done
priority: high
effort: small
tags: [multiplayer, bug]
created: '2026-09-23T05:26:08Z'
updated: '2026-09-23T06:28:23Z'
session: earthly-god-0922
notes_next: 2
```

state_delta.py compute_delta (98-104) sends new log lines only when len(new_messages) > len(old_messages), assuming recent_messages only grows. But multiplayer_game_state.py:325 caps it via get_recent_messages(20), and game_state.py:67-69 keeps only a fixed-size sliding window. Once a game passes 20 total messages, both snapshots are permanently 20 items long, so the length check is always False and no further chat/log messages are ever delta-broadcast for the rest of the game. Only a full-state resync (e.g. reconnect) briefly shows the latest 20-message window. Will reproduce deterministically in the pending 2-client playtest. Fix: track messages by an incrementing index/sequence rather than list length, or send an explicit new-message-count/cursor in the delta protocol.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T06:28:23Z session:glowing-pulsar-0922] Fixed: GameState now tracks a monotonic message_count (incremented in add_message, never trimmed, unlike the capped-at-100 messages list). Included in multiplayer_game_state.get_state_dict(). state_delta.compute_delta now diffs message_count instead of len(recent_messages) -- the old check went permanently blind once >20 messages had ever been sent, since recent_messages is capped at 20 for broadcast and both snapshots stayed the same length forever after. apply_delta propagates message_count forward too. Added 3 regression tests in test_state_delta.py reproducing the exact >20-message blind spot.


## TASK-VB-21 · Server and core action registries have drifted: Pickup and Lua actions don't work in multiplayer

```yaml
status: done
priority: high
effort: small
tags: [multiplayer, bug, architecture]
created: '2026-09-23T05:26:12Z'
updated: '2026-09-23T06:32:41Z'
session: earthly-god-0922
notes_next: 2
```

server/action_handler.py's ActionRegistry (26-34) registers 7 actions. core/actions/action_factory.py's ActionFactory._register_standard_actions (145, 433-480) additionally has PickupAction and LuaAction. Result: pickup and every Lua-scripted action silently can't be used in multiplayer. Fix: keep a single type-to-class map in core; server deserializes actions through it instead of maintaining its own registry. Add a parity test that fails if the two registries diverge again.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T06:32:41Z session:glowing-pulsar-0922] Fixed the Pickup half, plus a third self-discovered gap: WaitAction (used by the MP disconnected-player fallback) was ALSO missing from both registries -- same drift pattern, not in the original finding. Root cause: core/actions/__init__.py and server/action_handler.py each hand-maintained their own separate import list; new action files (pickup_action.py, wait_action.py) got added to action_factory.py (SP, verb-keyed) but not to either of those. Fix: core/actions/__init__.py now exports one canonical ACTION_TYPES: Dict[str, Type[Action]] map; server/action_handler.py's ActionRegistry._register_standard_actions() iterates it instead of hand-listing imports, so there's only one list to keep in sync. Added tests/unit/server/test_action_handler.py: an exact-match parity test plus one that walks Action.__subclasses__() and fails if any concrete action class exists outside ACTION_TYPES without an explicit, documented exclusion. NOT fixed: LuaAction. Its from_dict() can't reconstruct a bound LuaRuntime from wire data (raises NotImplementedError by design), and multiplayer doesn't construct a LuaRuntime anywhere at all yet -- confirmed via grep, only core/game.py (single-player) does. Lua-in-MP needs per-game routing through ActionFactory once VB-24 gives multiplayer a real Lua/EventBus-aware pipeline; tracked there, not re-opened as a separate ticket.


## TASK-VB-22 · Reconnect race can strand a player: inputs rejected, outputs dropped, no error

```yaml
status: done
priority: high
effort: medium
tags: [multiplayer, bug]
created: '2026-09-23T05:26:17Z'
updated: '2026-09-23T06:25:06Z'
session: earthly-god-0922
notes_next: 2
```

websocket_server.py:106 registers self.connections[session_id] = websocket on connect; reconnect reuses the same session_id (verify_token, 127-178) and overwrites the entry with the new live socket. If the original socket's recv() hadn't yet observed the drop, its finally block later calls disconnect_client (473-525) unconditionally -- with no check that the dying websocket is still the one currently registered for that session. This (a) marks the player disconnected in GameSession (game_session/session.py:353-354), causing the server to reject that player's real actions with 'Player is disconnected -- AI is controlling this character', and (b) pops the live websocket out of self.connections, so send_message_to_session (546-548) silently no-ops for all further server->client sends to that player. A brief network blip + fast reconnect leaves the player's inputs rejected and outputs undelivered with no visible error until reconnection-timeout cleanup intervenes. Fix: guard disconnect_client with an identity check (only disconnect if self.connections.get(session_id) is the socket that just closed).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T06:25:06Z session:glowing-pulsar-0922] Fixed: disconnect_client now takes an optional websocket param; handle_connection's finally block passes its own socket. If self.connections[session_id] no longer points at that socket (a fast reconnect already replaced it), disconnect_client is a no-op instead of tearing down the live connection and re-marking the player disconnected. Re-checked identity again before the final pop to guard against the awaits (disconnect_player/broadcast_to_game) letting a reconnect race in mid-call. Added 2 regression tests in test_websocket_server.py.


## TASK-VB-23 · Players are stored three different ways (root cause of VB-16's fallback bug)

```yaml
status: done
priority: high
effort: medium
tags: [architecture, multiplayer]
created: '2026-09-23T05:26:21Z'
updated: '2026-09-23T06:41:33Z'
session: earthly-god-0922
notes_next: 2
```

Single-player: the player is in both state.player and entities. Multiplayer host: id 'player', stored only in state.player (multiplayer_game_state.py:147-150). Multiplayer guests: stored only in entities (153-155). GameContext.get_entity (game_context.py:37-39) reads only entities, so the host is found only through the Action._get_actor fallback that causes VB-16. Lua get_entity('player') returns nil for the host in multiplayer. get_all_players (45-64) has to merge the two sources by hand. Fix: make entities the single store; GameState.player becomes a derived property looked up by a local_player_id. Medium effort -- many call sites use .player directly.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T06:41:33Z session:glowing-pulsar-0922] Fixed with a lower-risk design than the ticket's literal suggestion. Ticket proposed making GameState.player a fully derived property backed by a new local_player_id field; instead GameState.__post_init__ + a __setattr__ override keep .player synced INTO entities (insert on construction, insert-and-remove-stale-entry on reassignment) every time .player is set. This preserves every existing call site verbatim -- all ~50 GameState(player=...) constructor calls and ~29 .player read sites across core/server/ui/tests needed zero changes -- while establishing the same invariant the ticket wanted: entities is now the single store every lookup reads from, and the local/host player is always in it under its own entity_id.

  Downstream fixes that fell out of this: GameContext.get_all_players() no longer hand-merges .player with entities (was the ticket's own cited symptom); Action._get_actor() no longer needs the VB-16 fallback since context.get_entity() now finds the host directly (fallback removed, VB-16's regression test still passes since the observable behavior is identical); Lua's get_entity('player') is fixed for free since GameContextAPI._get_entity delegates straight to context.get_entity(). save_load.py's _serialize_state now excludes the player's entity_id from the generic 'entities' block (on-disk format unchanged, avoids double-storing the player under two object instances on load).

  Verified get_entity_at/get_entities_in_range now actually find the host at their own tile (previously a real, live blind spot for monster AI targeting the host specifically -- not just the VB-16 fallback bug). Did NOT touch cleanup_dead_entities: confirmed via test_process_action_dead_guest_does_not_redirect_to_host that purging a dead player from entities each round is existing, intentional, tested behavior (matches dead monster cleanup), not a bug -- a dead player disappearing from entities-based lookups while remaining resolvable via context.get_player() (still reads live .player, untouched by cleanup) is a deliberate and now-consistent distinction between host and guest, not a regression.

  Added tests/unit/test_game_state.py (5 tests on the sync mechanism itself) and 4 new tests in test_multiplayer_game_state.py (host findable via get_entity/get_entity_at, get_all_players clean). Fixed one now-incorrect test assumption (test_save_load.py::test_load_restores_entities expected entities to exclude the player; updated to 3, not 2, with an explicit assertion the player is included) and one already-stale comment (test_wait_action.py, predated VB-16, now also tightened to a real assertion). Full suite: 1109 -> 1127 passing, 0 failing, 0 skipped.


## TASK-VB-24 · Single-player and multiplayer run separate post-action pipelines -- root cause of repeated MP feature drift

```yaml
status: done
priority: high
effort: medium
tags: [architecture, multiplayer]
created: '2026-09-23T05:26:26Z'
updated: '2026-09-23T17:19:57Z'
session: earthly-god-0922
links:
  commits:
  - c8ff2f8c6c1bfc504434a033761280e9f6a8f9e9
notes_next: 4
```

Single-player (core/game.py:160-242, turn_processor.py:54-91): publishes outcome.events to the EventBus, adds outcome.messages, respects took_turn, applies HP regen, AI, cleanup, game-over and high-score/Legacy hooks. Multiplayer (server/game_session/session.py:363-373, 317-330, 451-470): never publishes to the EventBus (Lua event handlers and telemetry never fire in MP), only reads messages on failure, calls increment_actions() without checking took_turn, and has no HP regen. It also builds a fresh GameContext per action (365, 410), so systems registered on self.game_context (296) aren't visible from inside actions. The server never references Lua, EventBus, TurnProcessor, FloorManager, or SaveSystem anywhere outside docstrings. This is the structural cause of VB-16 (dead-actor fallback), VB-21 (action registry drift), and VB-25 (duplicated floor progression) -- every new post-action rule has to be built twice and MP is the copy that gets forgotten. Fix: extract a core TurnEngine.apply(action, ctx) -> outcome that owns publish/messages/transitions/turn-processing with hooks for what legitimately differs (floor policy, end-of-run); have both Game and GameSession call it.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T06:44:18Z session:glowing-pulsar-0922] Investigated 2026-09-22 (session glowing-pulsar-0922), not started -- deferred pending a design decision, see below. TurnProcessor.process_turn() (core/turn_processor.py:54-91), the thing SP's Game calls after every action, is NOT a clean drop-in for MP: _apply_hp_regeneration (line 93) heals game_state.player specifically (one player), _check_game_over (line 132) checks 'not game_state.player.is_alive' (one player dying ends the game), cascading into _record_high_score/_save_legacy_ore/_record_defeat -- all single-player-shaped. MultiplayerGameState already has its OWN, different game-over rule (update_player_alive_status: ends only when ALL players are dead). A literal 'extract TurnEngine, have both Game and GameSession call it' requires actually deciding and implementing N-player HP regen and N-player game-over semantics, and whether high-score/Legacy Vault recording applies per-player in MP at all (it doesn't exist there today, so there's no existing behavior to preserve, only new behavior to design) -- a game-design decision, not a mechanical refactor. User chose to pause here rather than guess at those rules. Recommended split when resumed: (1) a smaller, safe-to-do-mechanically slice first -- extract shared EventBus-publish/took_turn/cleanup/floor-transition handling and wire MP into it (closes 'Lua event handlers and telemetry never fire in MP' with no game-design judgment calls needed), (2) HP-regen/game-over/high-score unification as a separate, explicitly-scoped follow-up once N-player rules are decided with the user. This session also closed VB-16/17/18/19 (prior session) plus VB-20/21/22/23 (this session, commits 246ec3b..9ff7965) -- VB-23 in particular removed the storage-model asymmetry that made VB-16's fallback necessary, so GameContext.get_entity/get_entity_at now work correctly for the host, which may simplify some of what TurnEngine needs to handle.
- [#2 2026-09-23T16:37:42Z session:sultry-drizzle-0923] Slice 1 done (ca475b8): core/action_pipeline.py::process_action_outcome now shared by Game and GameSession. MP now records success messages in the shared log, publishes events to session.event_bus, and only counts took_turn actions toward the round quota. Still open: HP regen / game-over / high-score unification (needs N-player design decisions), and MP has no TurnProcessor-equivalent for floor policy. Spun off VB-33 (events fail to publish: schema mismatch).
- [#3 2026-09-23T17:19:57Z session:crimson-jewel-0923] Co-op rules decided with the user 2026-09-23: party plays on while any player is alive (already MP's rule); one shared HP regen (apply_hp_regeneration) applied to every living player at monster-turn cadence; co-op runs scored per player on a SEPARATE leaderboard (data/highscores_multiplayer.json via HighScoreManager.get_multiplayer_instance()) - each player at death, survivors at game end. Not done, filed separately: Legacy Vault in MP, viewing the co-op leaderboard, SP wait bypassing the pipeline.


## TASK-VB-25 · Floor progression logic duplicated between FloorManager and MultiplayerGameState

```yaml
status: done
priority: medium
effort: medium
tags: [architecture, multiplayer]
created: '2026-09-23T05:26:30Z'
updated: '2026-09-23T16:46:26Z'
session: earthly-god-0922
links:
  relates_to:
  - VB-24
  commits:
  - 437eaf4a52ba923fa8cc821c2e7f66185fac35b6
notes_next: 2
```

multiplayer_game_state.py:377-469 (descend_floor, _spawn_floor_entities, _get_victory_floor) duplicates core/floor_manager.py:54-273. Its own docstring (439-442) says this is because FloorManager assumes a single player. Fix: make FloorManager handle a whole party, with end-of-run hooks injected from outside; fold into the VB-24 TurnEngine extraction.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T16:46:26Z session:sultry-drizzle-0923] Shared: spawn_all_for_floor, clear_floor_entities, generate_floor_map, get_victory_floor. Found+fixed 2 bugs: SP descent evicted the player from entities (VB-23 regression) and skipped special rooms after floor 1. Remaining legit differences left separate: player placement (1 vs N spawn positions) and end-of-run hooks (SP high score/Legacy Vault vs MP none) -- the latter belongs to VB-24's game-over slice.


## TASK-VB-26 · state_delta.apply_delta: highest-complexity function in repo, no sequencing, mutates shared dict state

```yaml
status: backlog
priority: medium
effort: medium
tags: [multiplayer, architecture, quality]
created: '2026-09-23T05:26:36Z'
updated: '2026-09-23T16:48:43Z'
session: earthly-god-0922
notes_next: 2
```

state_delta.py:225 apply_delta has complexity 27 / nesting depth 6, the single worst production function in the codebase; compute_delta (16) is complexity 17. session.py:509-513 keeps one last_state per session shared by every client, and there's no sequence number or base-version in the delta protocol -- one dropped WS message leaves a client desynced until the next full-state broadcast. reset_state_tracking (session.py:533) is never called; reconnect instead broadcasts full state to everyone (websocket_server.py:383). Also apply_delta shallow-copies current_state (245) then mutates nested dicts in place (272-274, 304-306) -- a latent aliasing hazard for any future caller that retains a reference to a prior snapshot (replay/debug tooling). The client also depends directly on the server package for the protocol (ui/multiplayer_client.py:13-14), leaking a protocol dependency into the UI layer. Fix: move messages.py/state_delta.py into a shared protocol/ package; add seq/base_seq to deltas with a per-client baseline; have the client request a resync on a detected gap.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T16:48:43Z session:sultry-drizzle-0923] Done (commit 7e871d2): apply_delta complexity 27->10, no longer mutates its input (aliasing hazard), 9 characterization tests. STILL OPEN from this ticket: seq/base_seq + per-client baseline, client resync on gap, moving messages.py/state_delta.py into a shared protocol/ package. Those are protocol-design changes; do them together.


## TASK-VB-27 · cleanup_task busy-loops with no backoff if cleanup raises every iteration

```yaml
status: done
priority: medium
effort: small
tags: [bug, multiplayer]
created: '2026-09-23T05:26:39Z'
updated: '2026-09-23T16:40:56Z'
session: earthly-god-0922
links:
  commits:
  - a46f39b0abaf2a1e05d7bd6a1c9b95272d3da6cd
notes_next: 2
```

websocket_server.py:599-640: await asyncio.sleep(10) (line 637) is only reached on the success path. except Exception (639-640) falls straight back to while self.is_running with no backoff -- if cleanup_expired_sessions/cleanup_expired_disconnections raises every iteration, this spins a CPU core and floods logs indefinitely. Fix: move the sleep into a finally, or add exponential backoff on repeated failures.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T16:40:56Z session:sultry-drizzle-0923] cleanup_task split into _cleanup_once + loop that always sleeps; exponential backoff (10s base, 300s cap) resets on success; CancelledError re-raised; task handle held and cancelled in stop(). 6 tests in tests/unit/server/test_cleanup_task.py. The older test_server_cleanup_task_removes_expired_players re-implements the loop body rather than calling it; new tests call _cleanup_once directly.


## TASK-VB-28 · PickupAction has zero test coverage (highest-complexity single-player action untested)

```yaml
status: done
priority: medium
effort: small
tags: [test-coverage]
created: '2026-09-23T05:26:43Z'
updated: '2026-09-23T16:39:27Z'
session: earthly-god-0922
links:
  commits:
  - 9afac2041080f508ac6ed6873abd576bf1116b6c
notes_next: 2
```

core/actions/pickup_action.py:47 execute has complexity 14, the highest of any single-player action, and no unit or integration test references PickupAction anywhere in tests/. attack/mine/move/wait/action_factory all have dedicated unit tests; craft/equip are covered indirectly via test_equipment_system.py. Fix: add tests/unit/actions/test_pickup_action.py covering normal pickup, inventory-full, and stacking edge cases.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T16:39:27Z session:sultry-drizzle-0923] 10 tests in tests/unit/actions/test_pickup_action.py. Stacking does not exist in PickupAction (only inventory-full handling). Bug found+fixed: pickup that took nothing still consumed a turn.


## TASK-VB-29 · Duplicate imports crept back in since VB-14 was closed

```yaml
status: done
priority: low
effort: small
tags: [cleanup, quality]
created: '2026-09-23T05:26:46Z'
updated: '2026-09-23T16:52:29Z'
session: earthly-god-0922
links:
  commits:
  - a7b1f9b51e975e933ace36365f3961bc8cf22df8
notes_next: 2
```

VB-14 (fixed, 1c4bb02) previously removed 33 dead/duplicate imports, but I005 duplicate-import instances have reappeared: attack_action.py:213, mine_action.py:221, move_action.py:200, game_context.py:87, game_context_api.py:695,728 -- all 'imported once at module scope, re-imported inside a function' pattern. Cheap cleanup pass. Separately, ~25 I006 import-inside-function instances scattered through core/actions/* and core/base/game_context.py look like deliberate circular-import avoidance (matches constants.py:56's TODO on factory-method phase-out) -- worth a pass to confirm which are load-bearing vs habit before touching.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T16:52:29Z session:sultry-drizzle-0923] Hoisted Player/OreVein to module scope in attack/mine/move actions (import order verified from 6 entry points, suite green). The other I005 hits (game_context.py get_players/get_entities_at, game_context_api.py x2) are NOT duplicates: each is a function-local import in a different function, with a TYPE_CHECKING-only module import / documented circular-avoidance, so they are load-bearing and left alone.


## TASK-VB-30 · VeinbornServer self-subclasses itself as a dead deprecated alias

```yaml
status: done
priority: low
effort: small
tags: [cleanup]
created: '2026-09-23T05:26:49Z'
updated: '2026-09-23T16:52:28Z'
session: earthly-god-0922
links:
  commits:
  - a7b1f9b51e975e933ace36365f3961bc8cf22df8
notes_next: 2
```

websocket_server.py:667 defines class VeinbornServer(VeinbornServer), a 'deprecated alias' of itself, with a circular warning message ('VeinbornServer is deprecated, use VeinbornServer instead'). Leftover from a rename; shadows the real class name. Just delete it.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T16:52:28Z session:sultry-drizzle-0923] Deleted the alias; also removes a DeprecationWarning emitted on every server construction (test warnings 78 -> 3).


## TASK-VB-31 · Architecture docs reference stale/nonexistent source paths

```yaml
status: done
priority: low
effort: small
tags: [docs]
created: '2026-09-23T05:26:53Z'
updated: '2026-09-23T16:53:23Z'
session: earthly-god-0922
links:
  commits:
  - d2ed03e657aa63847beda69399ad7c8a16ece4f0
notes_next: 2
```

docs/architecture/00_ARCHITECTURE_OVERVIEW.md:30-31 points to src/scripting/ and src/content/entity_loader.py, which don't exist -- real paths are src/core/scripting/ and src/core/entity_loader.py. Its 'Current Game Loop' section (59-86) shows a Game that owns self.ui; the real code (post VB-11 split into GameBootstrapper/GameLuaIntegration) is better than the doc describes -- the doc is just stale, not aspirational. BASE_CLASS_ARCHITECTURE.md also still labels GameContext 'Phase 2' (1279) though it's fully implemented (only outline-checked, medium confidence). Fix: update paths and the game-loop description to match current code.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T16:53:23Z session:sultry-drizzle-0923] 00_ARCHITECTURE_OVERVIEW: fixed src/scripting + src/content paths, replaced the fictional Game.run() loop with the real handle_player_action -> process_action_outcome -> TurnProcessor flow (and MP's round-based variant), rewrote the project-structure tree, added rows for action_pipeline/turn_processor/floor_manager, refreshed test count. BASE_CLASS_ARCHITECTURE: GameContext and GameEvent no longer labelled Phase 2 (both implemented).


## TASK-VB-32 · Confirm and clean up suspected dead code: perception helpers, telemetry hooks

```yaml
status: held
priority: low
effort: small
tags: [cleanup, quality]
created: '2026-09-23T05:26:58Z'
updated: '2026-11-12T20:14:10Z'
session: earthly-god-0922
notes_next: 3
```

Static-analysis heuristic flagged 33 uncalled functions; most (action_factory.py 8 _create_* methods, ai_system.py 5 _behavior_* methods) are almost certainly dict/registry-dispatched and not actually dead -- confirm via reveal 'calls://src?target=_create_move_action&depth=2' before touching. Genuinely worth investigating: telemetry.py:311/349 (log_combat, log_player_death -- hooks that may just not be wired up yet) and perception.py:205-268 (four get_visible_*/get_nearby_ore/get_entities_at_distance helpers, all uncalled -- possibly superseded by update_visibility's internal logic, or dead API surface left from a refactor). run_server.py flagged as 'not imported anywhere' is a false positive (CLI entry point) -- ignore.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T16:54:07Z session:sultry-drizzle-0923] Investigated 2026-09-23, nothing deleted -- each remaining item needs a product call. (1) src/core/perception.py: FogOfWar/TileVisibility/PerceptionSystem have NO production caller (only referenced inside the file); tests/unit/test_perception.py (786 lines) tests it, and docs/development/BOT_* describe it, but the fuzz bots use their own tests/fuzz/services/perception_service.py. So get_visible_monsters/get_nearby_ore/get_entities_at_distance are dead as part of a wholly unwired module: decide wire-in (fog of war / bot API) vs delete module+tests. (2) telemetry.py GameTelemetry.log_combat/log_player_death: never called; Game builds game_telemetry but nothing writes to it. StatsTracker IS wired via EventBus subscribers, but see VB-33 -- most action events fail to publish, so even that is mostly silent. Decide alongside VB-33. (3) Action-factory _create_* and ai_system _behavior_* are registry-dispatched, not dead; run_server.py is a CLI entry point. Not dead.
- [#2 2026-11-12T20:14:10Z session:warming-squall-1112] Design question surfaced 2026-11-12 (VB-68): players have no fog of war (TUI draws every monster), while monsters since ADR-019 need LOS + memory. FogOfWar/PerceptionSystem here are the unused implementation; deciding whether players get FOV is Scott's call before deleting them.


## TASK-VB-33 · Action events mostly fail to publish to EventBus: flat dicts lack 'data', some types not in GameEventType

```yaml
status: done
priority: high
tags: [events, lua, telemetry]
created: '2026-09-23T16:37:36Z'
updated: '2026-09-23T17:01:53Z'
session: sultry-drizzle-0923
links:
  references:
  - src/core/events/events.py
  - src/core/action_pipeline.py
  commits:
  - d395c61c4bc98c008eebc07baf31df1a9c008d97
notes_next: 2
```

Found during VB-24. logs/veinborn.log holds ~769 'Failed to publish event from dict' errors: 717 KeyError 'data' (actions emit flat dicts like {'type':'entity_moved','entity_id':..}, GameEvent.from_dict requires event_dict['data']), plus ValueErrors for types absent from GameEventType (mining_progress, loot_dropped, descend_floor, equipment_equipped, actor_waited). Net: Lua event handlers and telemetry subscribers miss most action events in single-player, and now MP too since VB-24 wired it to publish. Fix needs a decision on the event schema (normalise action dicts vs. tolerate flat dicts in from_dict) and a check that subscribers cope with events they have never received before. Also: publish_dict logs unknown types at ERROR with traceback per action - noisy.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:01:53Z session:sultry-drizzle-0923] GameEvent.from_dict accepts flat action dicts; 7 action-emitted types added to GameEventType (Lua get_types() auto-exposes them). Live check: SP move/survey now deliver entity_moved/ore_surveyed, StatsTracker.ore_surveyed increments, 0 ERROR logs. Caveats: (1) Game.handle_player_action special-cases 'wait' without an Action, so SP wait emits no actor_waited event and no 'X waits.' message, unlike MP's WaitAction path -- another SP/MP drift for VB-24. (2) GameTelemetry.log_* still unwired, see VB-32. Lua event handlers under scripts/events now receive these events for the first time -- watch for surprises.


## TASK-VB-34 · Flaky test: test_action_planner::test_get_smart_action_prioritizes_forced_combat

```yaml
status: done
priority: low
tags: [tests, flaky]
created: '2026-09-23T16:37:36Z'
updated: '2026-09-23T17:01:32Z'
session: sultry-drizzle-0923
links:
  references:
  - tests/unit/test_action_planner.py
  commits:
  - d165e3b4747f71abec6054a1f4d23276d683774e
notes_next: 2
```

Failed once in a full-suite run (1137 passed/1 failed) during VB-24 work, then passed 3x in isolation and in a second full run. Probably RNG- or ordering-dependent; not touched by VB-24 changes.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:01:32Z session:sultry-drizzle-0923] Root cause: start_new_game() unseeded + hard-coded entity coordinates on a random map (also test_flee_from_maximizes_distance). Measured 2 failures in 195 runs; now seed=42 everywhere in the file (13 calls). test_perception_service and test_tactical_decision_service: 660 runs, no flakes.


## TASK-VB-35 · Co-op leaderboard has no viewer; Legacy Vault not wired for MP

```yaml
status: backlog
priority: medium
tags: [multiplayer, highscore]
created: '2026-09-23T17:19:57Z'
updated: '2026-09-23T17:42:48Z'
session: crimson-jewel-0923
links:
  references:
  - VB-24
  - src/core/highscore.py
notes_next: 3
```

VB-24 writes per-player co-op scores to data/highscores_multiplayer.json but nothing displays them (no client message, CLI, or screen). Legacy Vault (rare-ore save on death) is still single-player only; get_vault() is a process-wide singleton, so wiring it into a server needs a per-player persistence decision first. Per-player stats (monsters_killed etc.) are also read from player.stats, which nothing appears to write in either mode - check before designing a co-op scoring UI.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:29:04Z session:crimson-jewel-0923] Update 2026-09-23: the 'player.stats never written' concern is resolved by VB-38 (d16aa49) - co-op scores now include kills/damage/ore per player, so a leaderboard viewer is now worth building.
- [#2 2026-09-23T17:42:48Z session:crimson-jewel-0923] 0851b8f: added the veinborn-scores CLI (--coop, --limit, --file) - the first way to see either leaderboard (neither mode had a viewer). Still open on this ticket: an in-game/TUI high score screen, and the Legacy Vault decision for MP.


## TASK-VB-36 · Single-player 'wait' bypasses the action pipeline (no actor_waited event, no message)

```yaml
status: backlog
priority: low
tags: [events, singleplayer]
created: '2026-09-23T17:19:57Z'
updated: '2026-09-23T17:19:57Z'
session: crimson-jewel-0923
links:
  references:
  - VB-24
  - VB-33
  - src/core/game.py
```

Game.handle_player_action special-cases 'wait' (calls _process_turn directly), so SP wait emits no actor_waited event or 'X waits.' message unlike MP's WaitAction path. Routing it through WaitAction would add a message per rest keypress - decide whether that log spam is wanted.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-37 · Damage formula never evaluates: 'max' passed as a name, simpleeval needs functions=

```yaml
status: done
priority: low
tags: [combat, bug]
created: '2026-09-23T17:19:57Z'
updated: '2026-09-23T17:29:04Z'
session: crimson-jewel-0923
links:
  references:
  - src/core/actions/attack_action.py
  - data/balance/formulas.yaml
  commits:
  - d16aa49e93fcdc6d8e42eec495834ff1db1fd6d8
notes_next: 2
```

attack_action._calculate_and_apply_damage passes max/min in simple_eval's names= so every attack raises 'Function max not defined' and uses the hardcoded fallback max(1, atk-def) (88 errors in logs/veinborn.log). Result is identical for the current default formula, but any balance change to the configured damage formula is silently ignored. Fix: functions={'max': max, 'min': min}. Also check min_damage is applied.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:29:04Z session:crimson-jewel-0923] functions={'max','min'} in simple_eval; configured formula and min_damage now honored; 2 regression tests in test_attack_action.py.


## TASK-VB-38 · High scores ignored combat and mining: run stats were never written to player.stats

```yaml
status: done
priority: high
tags: [highscore, bug]
created: '2026-09-23T17:28:55Z'
updated: '2026-09-23T17:29:03Z'
session: crimson-jewel-0923
links:
  references:
  - src/core/highscore.py
  commits:
  - d16aa49e93fcdc6d8e42eec495834ff1db1fd6d8
notes_next: 2
```

HighScoreEntry reads monsters_killed/damage_dealt/damage_taken/ore_mined/ore_surveyed/best_ore_purity/death_cause from player.stats; nothing wrote them, so every score (SP and co-op) was floor*1000 + turns + xp. Found while building VB-24 co-op scoring. Fixed by recording the stats inside AttackAction/MineAction/SurveyAction on the acting Player.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:29:03Z session:crimson-jewel-0923] Actions record run stats on the acting/targeted Player; 8 tests in tests/unit/actions/test_run_stats.py plus a co-op per-player score test.


## TASK-VB-39 · MP server rejected every real websocket connection (websockets >= 13: handler has no 'path')

```yaml
status: done
priority: urgent
tags: [multiplayer, playtest]
created: '2026-09-23T17:38:05Z'
updated: '2026-09-23T17:38:05Z'
session: crimson-jewel-0923
links:
  commits:
  - f0d0d7d09c24ca8e3e967d41a65007a1dae5011c
notes_next: 2
```

Found by the first real two-client playtest. handle_connection(websocket, path) raised TypeError on the installed websockets 15.0.1, closing every connection with 1011; only mock-websocket tests existed. Also VeinbornServer(port=0) fell back to config.port.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:38:05Z session:crimson-jewel-0923] Fixed in f0d0d7d with regression tests; see tests/integration/test_multiplayer_real_sockets.py


## TASK-VB-40 · Lobby->started transition sent as a delta: clients never got is_started/entity_id, could not act

```yaml
status: done
priority: urgent
tags: [multiplayer, playtest]
created: '2026-09-23T17:38:05Z'
updated: '2026-09-23T17:38:05Z'
session: crimson-jewel-0923
links:
  commits:
  - f0d0d7d09c24ca8e3e967d41a65007a1dae5011c
notes_next: 2
```

compute_delta only diffs a fixed field set. The state after start was a delta, so clients never learned entity_id (every action rejected 'Action actor does not match player') or is_started/initialized. Now full state on is_started/is_finished/initialized/is_multiplayer changes.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:38:05Z session:crimson-jewel-0923] Fixed in f0d0d7d with regression tests; see tests/integration/test_multiplayer_real_sockets.py


## TASK-VB-41 · Monster-turn messages never reached MP deltas (GameContext.add_message skipped message_count)

```yaml
status: done
priority: high
tags: [multiplayer, playtest]
created: '2026-09-23T17:38:05Z'
updated: '2026-09-23T17:38:06Z'
session: crimson-jewel-0923
links:
  commits:
  - f0d0d7d09c24ca8e3e967d41a65007a1dae5011c
notes_next: 2
```

GameContext.add_message appended to state.messages directly: message_count never advanced (deltas key off it) and the 100-message cap was bypassed. Now delegates to GameState.add_message.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:38:06Z session:crimson-jewel-0923] Fixed in f0d0d7d with regression tests; see tests/integration/test_multiplayer_real_sockets.py


## TASK-VB-42 · Dead players' actions hit 'Actor not found' at ERROR; wall bumps logged at ERROR

```yaml
status: done
priority: low
tags: [multiplayer, playtest]
created: '2026-09-23T17:38:05Z'
updated: '2026-09-23T17:38:06Z'
session: crimson-jewel-0923
links:
  commits:
  - f0d0d7d09c24ca8e3e967d41a65007a1dae5011c
notes_next: 2
```

Dead players get an explicit 'You are dead' rejection in GameSession.process_action; action validation failures now log WARNING instead of ERROR so ops error counts mean something.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:38:06Z session:crimson-jewel-0923] Fixed in f0d0d7d with regression tests; see tests/integration/test_multiplayer_real_sockets.py


## TASK-VB-43 · disconnect_client raised AttributeError on every client drop (websockets asyncio API has no .closed)

```yaml
status: done
priority: high
tags: [multiplayer, playtest]
created: '2026-09-23T17:40:59Z'
updated: '2026-09-23T17:40:59Z'
session: crimson-jewel-0923
links:
  commits:
  - 9b504c187305eee767e8438521b89028b051fc1f
notes_next: 2
```

Found by the reconnect playtest. Every abrupt drop hit 'ServerConnection object has no attribute closed' in disconnect_client's finally block, and a broadcast racing the drop logged an ERROR. Added WebSocketServer._is_closed (works for both websockets APIs) and treat ConnectionClosed on send as info.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:40:59Z session:crimson-jewel-0923] Regression test: test_dropped_client_reconnects_with_a_full_state_and_no_server_errors


## TASK-VB-44 · No gameplay client: MultiplayerClient can't send actions; the TUI only does chat/lobby

```yaml
status: backlog
priority: high
tags: [multiplayer, ui]
created: '2026-09-23T17:41:24Z'
updated: '2026-11-13T01:46:46Z'
session: crimson-jewel-0923
links:
  references:
  - src/ui/multiplayer_client.py
  - src/ui/textual/app.py
  - src/server/test_client.py
notes_next: 2
```

The first real two-client playtest (scripted, headless) worked after VB-39..43, but the only thing that can send move/attack/mine over the wire is the dev tool src/server/test_client.py. ui/multiplayer_client.MultiplayerClient has connect/chat/create/join/ready and delta merging but no send_action; ui/textual/app.py only wires chat. A human two-client playtest needs a multiplayer game view in the TUI (render players/monsters/map from the merged state, send MoveAction/AttackAction/... with the entity_id from state). Design question: reuse the single-player map widget with a state adapter, or a new read-only renderer.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-13T01:46:46Z session:mustard-sunset-1112] Design answer (2026-11-12, session mustard-sunset-1112): reuse the single-player map widget via a state adapter is the wrong shape; render from a shared snapshot instead (VB-78) so the TUI, server state and any future client use one contract. get_state_dict today omits derived stats (total attack/defense, equipment, XP, cooldowns) that the single-player sidebar shows, so a multiplayer view built on it would be incomplete. Suggest sequencing VB-77 -> VB-78 -> this task.


## TASK-VB-45 · Disconnected-player 'AI control' is never invoked (process_disconnected_player_action has no caller)

```yaml
status: backlog
priority: low
tags: [multiplayer]
created: '2026-09-23T17:43:16Z'
updated: '2026-09-23T17:43:16Z'
session: crimson-jewel-0923
links:
  references:
  - src/server/game_session/session.py
```

GameSession.process_disconnected_player_action (a defensive WaitAction) is called from nowhere in src, yet process_action tells rejected clients 'AI is controlling this character'. In a headless playtest a dropped player's character just stood still and died. Either wire it into a timer/round hook (what should the AI do beyond wait? retreat to stairs?) or delete it and fix the message. Product call.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-46 · Spawner stacks ore veins, forges and (rarely) monsters on one tile

```yaml
status: done
priority: medium
effort: 2h
tags: [spawning, bug]
created: '2026-11-11T23:02:13Z'
updated: '2026-11-12T02:55:59Z'
session: kinetic-fusion-1111
links:
  commits:
  - ec6b05a09e4ef1c4f33d038ade7e1ee24ce82697
notes_next: 3
```

Found by scripts/sim_mob_movement.py + tests/unit/test_spawn_no_overlap.py. Across seeds 1-24 x floors 1/6/12, spawn_all_for_floor puts ore-on-ore (~27), forge-on-ore (6) and monster-on-ore (7) on the same tile. Monster-on-monster (den monsters) is fixed in spawn_all_for_floor; ore/forge/regular-monster overlaps are not. Dropping or relocating the later entity changes ore counts, so check balance first.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T01:49:50Z session:kinetic-fusion-1111] Fixed in spawn_all_for_floor: forge/den monsters/bonus ores now relocate to the nearest free walkable tile (no entities dropped, RNG sequence unchanged). test_spawn_no_overlap.py covers monsters+ore+forges, 24 seeds x 3 floors.
- [#2 2026-11-12T02:39:01Z session:kinetic-fusion-1111] Fix is in the working tree (spawn_all_for_floor relocation + test_spawn_no_overlap.py); close with --commit after the commit


## TASK-VB-47 · AI architecture (ADR-019): engine owns perception/morale/speed, behaviours are tactics, abilities work for any actor

```yaml
status: backlog
priority: medium
tags: [ai, design, architecture]
created: '2026-11-11T23:02:15Z'
updated: '2026-11-12T19:08:18Z'
session: kinetic-fusion-1111
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  - docs/architecture/DECISIONS.md
  - docs/EXTENDING.md
notes_next: 4
```

Umbrella for the AI redesign in docs/architecture/AI_ARCHITECTURE.md (ADR-019). Replaced the original knob-by-knob list (passive never triggers, aggro_range/move_speed unread, guard flee_threshold unused, default_ai_by_type dead, Manhattan vs 8-way). Children carry the work. The engine phases (VB-58..VB-63) are done; close this when VB-64 (enable monster abilities, needs Scott), VB-65 (status effects) and VB-67 (passive triggers) are done or split out. Each child that changes gameplay ends with a bot before/after comparison (tests/fuzz, 4 classes x 8 games x 3000 turns).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T05:11:44Z session:turquoise-mosaic-1111] Lua half resolved 2026-11-11: Lua removed (ADR-018); berserker/sniper/summoner ported to Python content (src/core/content/ai/) with a real ranged attack (AttackAction ranged=True) and real summoning (AISystem.summon). No shipped monster uses them yet: assigning them changes balance, so it needs a play-test first (sniper in particular is deadly: random-walk bots died in ~30 turns when every monster got one). Still open: items 2-5 of the description (passive, aggro_range/move_speed, guard flee_threshold, default_ai_by_type).
- [#2 2026-11-12T17:39:31Z session:vevine-1112] Investigated 2026-11-12 (session vevine-1112): all original items confirmed in code; design written up in docs/architecture/AI_ARCHITECTURE.md; work split into child tasks.
- [#3 2026-11-12T19:08:18Z session:vevine-1112] 2026-11-12 vevine-1112: VB-58..VB-63 and VB-66 done (commits 8394cef..294cf9a). Open: VB-64 (blocked on Scott: which abilities and numbers), VB-65, VB-67 (filed this session).


## TASK-VB-48 · Early balance: mage loses to a goblin; 100 XP/level vs 5 XP goblin means nobody levels

```yaml
status: done
priority: medium
effort: 3h
tags: [balance]
created: '2026-11-12T01:33:21Z'
updated: '2026-11-12T03:35:43Z'
session: kinetic-fusion-1111
links:
  commits:
  - 20c36cb5092246b3488a745920ebe191644e3102
notes_next: 2
```

Bot comparison (8 games x 4 classes, 3000-turn cap, old vs new mob AI): 0 of 64 games reached level 2 (up to 8 kills). gain_xp needs 100*level XP; goblin gives 5, orc 15. Mage deals 1 damage to a goblin and takes 2 per hit; 4 of 8 mages died to goblins/orcs on floor 1 in both trees, 'Killed by Goblin' within 15-80 turns. Decide target kills-per-level and mage starting attack.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T03:35:29Z session:nebular-eclipse-1111] Done: d20 to-hit (roll+atk >= 10+def, nat 1/20) + damage roll atk±50% in AttackAction (formulas.yaml combat; dead crit/accuracy blocks removed). NetHack doubling XP curve 20/40/80..10240 then +10000 (game_constants xp_curve), multi-level gains, HP gain rolled and added to current HP (no full heal). Class growth from templates; attack +1/level, defense 0 for all (at +2 atk / +2 def, L3 warrior beat trolls 100% and L7 healer was unhittable). Mage attack 2->4 until spells. scripts/sim_duels.py measures win%/HP lost per class x monster x level. Bots 8 games x 4 classes x 3000 turns vs ec6b05a baseline: mage deaths 4/6 -> 1/8, avg level 1.0 -> 1.5-2.0 (max 3-4), 0 crashes; floors unchanged (~1.5, bots explore slowly). Still unverified: human feel; spells (mage), ongoing spawns.


## TASK-VB-49 · Fuzz bots: thousands of non-adjacent mine attempts, repeated 'Crafted Copper Dagger!', stalls on floors 1-2

```yaml
status: done
priority: low
effort: 3h
tags: [bots, tests]
created: '2026-11-12T01:33:23Z'
updated: '2026-11-12T02:55:59Z'
session: kinetic-fusion-1111
links:
  commits:
  - ec6b05a09e4ef1c4f33d038ade7e1ee24ce82697
notes_next: 3
```

In 3000-turn runs bots reach floor 1-2 and kill ~3 monsters. Logs show up to ~19k 'MineAction validation failed: not adjacent to ore_vein' per run and one mage run logged 139 'Crafted Copper Dagger!' with 5 ore mined -- check whether CraftAction consumes ore or the bot loops. Bot result JSON kills/damage were hardcoded 0 (fixed to read player.stats).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T01:49:49Z session:kinetic-fusion-1111] Root causes found and fixed: (1) crafted equipment carried ore_type so it counted as ore -- a forge turned daggers into daggers forever (is_ore_item + crafted_ore_type); (2) craft validation failure raised TypeError (reason= kwarg collision); (3) stale mining_action state after walking away wedged 'mine' permanently, no turn passed, bots froze. Tests: test_craft_consumes_ore.py, test_action_factory.py stale-mining cases.
- [#2 2026-11-12T02:39:01Z session:kinetic-fusion-1111] All three root causes fixed in the working tree; close with --commit after the commit


## TASK-VB-50 · data/highscores.json is 300 test 'Anonymous' entries; decide whether to reset the shipped leaderboard

```yaml
status: done
priority: low
effort: 30m
tags: [highscores]
created: '2026-11-12T01:33:24Z'
updated: '2026-11-12T03:51:20Z'
session: kinetic-fusion-1111
links:
  commits:
  - a20bef8d5fd974eccea732d208be44585b5176fc
notes_next: 2
```

All 300 committed entries are 'Anonymous' (8 distinct names) dated 2025-10-25..11-07, written by tests through the real singleton. add_score trim crashed at 300 (fixed) and tests now isolate the single-player board in conftest. The file itself is still the junk board; clearing it is a product call.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T03:51:20Z session:turquoise-mosaic-1111] Reset to []; loader verified; suite leaves it untouched.


## TASK-VB-51 · Class abilities and starting items are unimplemented: mage has no spells (fireball/teleport), rogue no backstab/dodge, healer no heal; starting_items commented out in create_player_from_class

```yaml
status: done
priority: medium
effort: 6h
tags: [balance, classes]
created: '2026-11-12T03:43:29Z'
updated: '2026-11-12T04:03:31Z'
session: nebular-eclipse-1111
links:
  commits:
  - f9c11e5c5fa6340389e092e9b503a695978286c9
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T04:03:31Z session:turquoise-mosaic-1111] Shipped: force_bolt (z), heal (z), backstab (passive), warrior/rogue starting gear (stat-neutral), mage attack 4->3. sim_duels --start-distance models bolts. Unbuilt abilities filed as a follow-up. Wand/spellbook/staff/bandages/lockpick dropped (not in items.yaml).


## TASK-VB-52 · Monsters only spawn at floor creation: add NetHack-style ongoing spawns (small per-turn chance, difficulty from depth + player level) so XP isn't a fixed pool and slow play has a cost

```yaml
status: done
priority: low
effort: 3h
tags: [balance, spawning]
created: '2026-11-12T03:43:31Z'
updated: '2026-11-12T03:50:32Z'
session: nebular-eclipse-1111
links:
  commits:
  - 9f92a4148e1dc2bb0982920991eedee40bb51274
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T03:50:32Z session:turquoise-mosaic-1111] TurnProcessor._maybe_spawn_wanderer; config spawning.yaml ongoing_spawns; 8 tests. Bot re-run not done.


## TASK-VB-53 · Remaining class abilities: fireball/teleport (mage), dodge (rogue), power_strike (warrior), protect/regeneration (healer); warrior has no ability

```yaml
status: backlog
priority: low
tags: [balance, classes]
created: '2026-11-12T04:03:31Z'
updated: '2026-11-12T19:08:18Z'
session: turquoise-mosaic-1111
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T19:08:18Z session:vevine-1112] 2026-11-12: abilities are actor-agnostic now (VB-63: @ability fn(context, actor, config, target=None), should_use, core/targeting). Passive class abilities like regeneration should use VB-67's trigger mechanism.


## TASK-VB-54 · Persist achievement/quest/kill-streak state in save files (content event handlers reset on load_game)

```yaml
status: backlog
priority: low
tags: [content, save]
created: '2026-11-12T05:11:47Z'
updated: '2026-11-12T05:11:47Z'
session: turquoise-mosaic-1111
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-55 · Multiplayer server does not install content event handlers or publish turn_ended/floor_changed/game_started: achievements/quests are single-player only

```yaml
status: backlog
priority: low
tags: [content, multiplayer]
created: '2026-11-12T05:11:48Z'
updated: '2026-11-12T19:08:18Z'
session: turquoise-mosaic-1111
notes_next: 2
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T19:08:18Z session:vevine-1112] 2026-11-12: the server's AISystem now receives the session event bus (VB-60), so monster provocation and monster attack events (VB-66) work in multiplayer. Content handlers (achievements/quests) and turn_ended/floor_changed/game_started are still single-player only.


## TASK-VB-56 · Kill streaks announce but grant nothing: decide whether streaks (and quests) should give real rewards, e.g. an extra LootGenerator roll at the kill

```yaml
status: backlog
priority: low
tags: [content, balance]
created: '2026-11-12T05:11:49Z'
updated: '2026-11-12T05:11:49Z'
session: turquoise-mosaic-1111
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-57 · Fuzz class bots: the per-class get_smart_action trees in tests/fuzz/{warrior,rogue,mage,healer}_bot.py are never called (veinborn_bot calls planner.plan_next_action), so all four bots run the shared planner and differ only by CombatConfig. Either wire the class trees in (e.g. planner delegates to a bot hook) or delete them

```yaml
status: done
priority: low
tags: [fuzz, bots]
created: '2026-11-12T06:56:00Z'
updated: '2026-11-12T20:27:32Z'
session: turquoise-mosaic-1111
links:
  commits:
  - 86ed2e450f4f854c58af41bb0ead20d455933bfd
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T19:08:18Z session:vevine-1112] 2026-11-12: ActionPlanner.ability_action (0fef6be) is the only ability logic the bots use; the per-class trees are still dead.
- [#2 2026-11-12T20:27:32Z session:warming-squall-1112] Deleted the dead per-class trees; behaviour unchanged (they were never called). Class bots = CombatConfig + shared planner.


## TASK-VB-58 · AI: one range metric (Chebyshev) in core/geometry, used by AI, abilities, spawning and guard leash

```yaml
status: done
priority: medium
effort: 1-2h
tags: [ai, architecture]
created: '2026-11-12T17:39:42Z'
updated: '2026-11-12T17:56:46Z'
session: vevine-1112
parent: VB-47
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  commits:
  - 8394cef86087837421a32012b1b3b1fac4e6ec33
notes_next: 3
```

Today: AISystem.distance/nearest_player, guard leash (classic.py) and EntitySpawner.spawn_wandering_monster use Manhattan; force_bolt uses Chebyshev inline; Entity.distance_to is Euclidean. Movement and adjacency are 8-way, so Manhattan makes a 10-tile chase ~5-7 tiles on the diagonal. Add geometry.chebyshev(a, b) and route every range check through it (keep Euclidean dist2 only for choosing a flee step). Balance change: diagonal ranges grow; bot before/after. See AI_ARCHITECTURE.md 'Distance'.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T17:48:24Z session:vevine-1112] geometry.chebyshev; AI ranges, nearest player, guard leash, spawn distance, force bolt now share one metric.
- [#2 2026-11-12T17:56:46Z session:vevine-1112] Bots 8 games x 3000 turns each, before -> after (before = warrior/rogue from turquoise-mosaic-1111, mage/healer from 0fef6be): warrior floor 9.4->6.4 deaths 1->2; rogue 6.8->8.2 deaths 1->0; mage 6.2->6.1 deaths 2->5; healer 9.4->8.4 deaths 1->1. 0 bugs. Direction: monsters reach further on diagonals; 8-game samples are noisy (rogue went up).


## TASK-VB-59 · AI: per-monster AI parameters (monster ai: block overrides behaviour defaults, resolved by content_id) + load-time validation; delete default_ai_by_type

```yaml
status: done
priority: medium
effort: 2-3h
tags: [ai, architecture, content]
created: '2026-11-12T17:39:43Z'
updated: '2026-11-12T17:48:18Z'
session: vevine-1112
parent: VB-47
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  - data/entities/monsters.yaml
  - data/balance/ai_behaviors.yaml
  commits:
  - 5b8b073a301f2c40ead70bd6f9e1a454699b766a
notes_next: 2
```

AISystem.update passes only the behaviour's section of ai_behaviors.yaml; monsters.yaml ai.aggro_range/move_speed are never read (entity_loader.create_monster stores only ai_type). Resolve params = behaviour defaults <- monster ai: block <- optional per-instance stat override, looked up by monster.content_id at runtime (not copied into stats, so YAML tuning reaches existing saves). Validate at load (ContentValidationError, like unknown monster ids): unknown ai.type, unknown ai: keys (allowed = behaviour's default keys + universal set: type, aggro_range, move_speed, flee_threshold, description), enabled abilities with no registered implementation. Delete default_ai_by_type + ConfigLoader.get_default_ai_for_monster + its test lines. Fix ai.description lines that claim unbuilt behaviour. See AI_ARCHITECTURE.md 'Parameters' and 'Validation'.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T17:48:01Z session:vevine-1112] AISystem.params_for + validate_monster_ai (raises ContentValidationError at AISystem construction, SP and MP). No gameplay change: aggro_range/move_speed resolved but unused until VB-60/VB-62.


## TASK-VB-60 · AI: engine perception (aggro_range + line of sight + provocation) via ai.perceive; provocation from ATTACK_RESOLVED in core; passive becomes neutral; contract test over every behaviour

```yaml
status: done
priority: medium
effort: 3-4h
tags: [ai, architecture]
created: '2026-11-12T17:39:53Z'
updated: '2026-11-12T18:18:05Z'
session: vevine-1112
depends_on: [VB-58, VB-59]
parent: VB-47
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  - docs/EXTENDING.md
  relates_to:
  - VB-55
  commits:
  - acd5cdaac935eb1aea9327fa652e6eb02b972473
notes_next: 3
```

Classic behaviours chase by distance only (no line of sight), via nearest_player. Add ai.perceive(monster, params) -> target or None: a player within aggro_range AND in sight, or the monster's provoker. Provocation: AISystem (core, not content: the MP server installs no content handlers, VB-55) subscribes to ATTACK_RESOLVED and records last_attacker_id + provoked_turn on the defender, with a decay window. Needs the event bus passed to AISystem in Game and in server session.py. Behaviours switch nearest_player -> perceive (multiplayer: prefer the provoker). passive -> 'neutral': wanders, fights back when provoked. A parametrized contract test runs every registered @ai_behavior and asserts an unperceived player is neither attacked nor approached. Update EXTENDING.md toolkit list. Bot before/after. See AI_ARCHITECTURE.md 'Perception' and 'Provocation'.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T17:57:57Z session:vevine-1112] perceive/provoked_by/_on_attack in AISystem; defaults block (aggro_range 8, memory_turns 10, move_speed 1.0, flee_threshold 0). Contract test (8 behaviours x positive/negative) + 2 mutation checks (no LOS, perceive=nearest_player) caught. Side fix: wander stepped onto the player's tile = bump attack. Bot comparison in a note.
- [#2 2026-11-12T18:18:05Z session:vevine-1112] Bots 8x3000 at acd5cda (incl. VB-58), vs the VB-58-only run: warrior floor 6.4->9.4 deaths 2->0; rogue 8.2->8.8 deaths 0->0; mage 6.1->7.0 deaths 5->0; healer 8.4->8.6 deaths 1->0. 0 bugs. Line of sight + per-monster aggro ranges make monsters notice less through walls; game got easier for bots.


## TASK-VB-61 · AI: engine morale step (flee_threshold) runs before every behaviour; drop per-behaviour flee checks; guards hold (0)

```yaml
status: done
priority: medium
effort: 1-2h
tags: [ai, architecture]
created: '2026-11-12T17:39:55Z'
updated: '2026-11-12T18:01:35Z'
session: vevine-1112
depends_on: [VB-60]
parent: VB-47
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  commits:
  - f25302d12c8ca9f73cf5cb7b287ff9aafedb2717
notes_next: 2
```

defensive, passive and sniper each re-implement 'flee below X% HP'; guard has flee_threshold 0.2 in YAML but never flees. Move it to AISystem: if hp/max_hp < params.flee_threshold and a target is perceived, flee_from instead of running the behaviour. flee_threshold 0 opts out (guards, aggressive). Remove the per-behaviour checks. See AI_ARCHITECTURE.md 'Morale'.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T18:01:35Z session:vevine-1112] AISystem._morale_breaks; tests/unit/systems/test_ai_morale.py (incl. a new behaviour that never flees is made to flee by the engine).


## TASK-VB-62 · AI: monster speed via an energy counter in AISystem.update (move_speed 0.6-1.5 becomes real)

```yaml
status: done
priority: low
effort: 2h
tags: [ai, architecture, balance]
created: '2026-11-12T17:40:07Z'
updated: '2026-11-12T18:32:49Z'
session: vevine-1112
depends_on: [VB-59]
parent: VB-47
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  commits:
  - d71654b0ea21a2eec58ac0409c0c552d430d7c19
notes_next: 3
```

move_speed is declared for all 19 monsters and never read. Both drivers (TurnProcessor._run_ai_systems single-player, session._process_monster_turn multiplayer) call ai_system.update() once per round, so the scheduler can live in AISystem: each update add move_speed to a per-monster 'energy' stat, act while energy >= 1 (subtract 1 per action). Bat 1.5 acts 3 times per 2 rounds, golem 0.6 acts 3 per 5. Player speed (haste/slow) is out of scope but should reuse the same rule later. Balance change: bot before/after. See AI_ARCHITECTURE.md 'Speed'.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T18:05:41Z session:vevine-1112] Energy counter in AISystem.update/_act; tests/unit/systems/test_ai_speed.py. Bot comparison in a note.
- [#2 2026-11-12T18:32:49Z session:vevine-1112] Bots 8x3000 at 4556232 (VB-58..VB-63, VB-66), vs acd5cda (VB-60): warrior floor 9.4->8.4 deaths 0->0; rogue 8.8->10.0 deaths 0; mage 7.0->7.5 deaths 0->1; healer 8.6->8.4 deaths 0. 0 bugs. Speed + morale: no clear shift beyond 8-game noise.


## TASK-VB-63 · Abilities for any actor: hostility helper on GameContext, actor-agnostic ability targeting, monsters use abilities from their YAML (AI ability step); sniper/summoner become tactics + abilities

```yaml
status: done
priority: low
effort: 1d
tags: [ai, architecture, abilities, content]
created: '2026-11-12T17:40:08Z'
updated: '2026-11-12T18:17:46Z'
session: vevine-1112
depends_on: [VB-60, VB-61]
parent: VB-47
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  - docs/EXTENDING.md
  - data/entities/monsters.yaml
  relates_to:
  - VB-53
  commits:
  - 455623284a11052a9369c53652d289f46401793e
notes_next: 2
```

13 of 19 monsters already declare abilities in monsters.yaml (death_bolt, fire_bolt, bat_swarm, summon_undead, life_drain, regeneration, teleport, ...) all enabled: false. Player abilities (AbilityAction, @ability) are nearly actor-agnostic (abilities + cooldowns are entity stats); the player-only part is target choice (force_bolt picks the nearest monster). Add context.hostiles_of(actor) (also makes move_action's 'monsters don't bump-attack monsters' rule explicit), give @ability a target-selection/should_use hook, add an engine step where a perceiving monster uses a ready enabled ability before its tactics. Re-express sniper as kite-tactics + ranged ability and summoner as keep-away tactics + summon ability. Ships with every monster ability still disabled: no gameplay change. Update EXTENDING.md. See AI_ARCHITECTURE.md 'Abilities for any actor'.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T18:17:46Z session:vevine-1112] No gameplay change by design: test asserts no shipped monster has an ability; sniper/summoner tests unchanged in intent. Mutation (drop _use_ability) fails 8 tests. Also: player-vs-player bump attacks in MP are now blocked (co-op).


## TASK-VB-64 · Turn on monster abilities one at a time (bolts, summons, drains, regeneration) with bot runs + Scott's play-test

```yaml
status: blocked
priority: low
owner: scott
effort: per ability ~1h + play-test
tags: [ai, balance, content, design]
created: '2026-11-12T17:40:20Z'
updated: '2026-11-12T19:31:29Z'
session: vevine-1112
depends_on: [VB-63]
parent: VB-47
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  - data/entities/monsters.yaml
  commits:
  - 294cf9aa9dc4ffa7535b95109dfa328748d80420
notes_next: 4
```

Design/balance work, needs Scott: which abilities, in what order, at what numbers. Suggested first wave (no status effects needed): lich death_bolt + summon_undead, imp fire_bolt, vampire bat_swarm + life_drain, wraith life_drain, troll regeneration, ancient_horror summon_horrors + phase_two (enrage). Each: implement as @ability content, set enabled: true, rewrite that monster's ai.description to match, bot before/after, play-test. Also decides whether any monster keeps berserker/sniper/summoner tactics. See AI_ARCHITECTURE.md 'Monster ability inventory'.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T18:22:07Z session:vevine-1112] Built (disabled) at 294cf9a: the 9 active abilities in AI_ARCHITECTURE.md 'Monster ability inventory'. Waiting on Scott: which to enable and at what numbers (declared values like death_bolt 15 / dive_bomb 20 / reality_warp 25 vs 20 HP players look too high), then bot runs + play-test per ability. Passive ones are VB-67, status effects VB-65.
- [#2 2026-11-12T19:21:53Z session:warming-squall-1112] Data path: VB-68 steps 1+2 (duel sim through AISystem, seeded paired bot runs) can turn the 'which abilities, what numbers' choice into a table with proposed values for Scott to approve.
- [#3 2026-11-12T19:31:29Z session:warming-squall-1112] sim_duels data (a982c4f), imp fire_bolt, start distance 4, 500 fights/cell, HP lost on a win (% max), off -> on at declared damage 4 -> damage 3: L2 warrior 3->42->31, rogue 5->57->44, mage 1->37->28, healer 5->50->41 (rogue/healer win 97% at dmg 4, 100% at 3); L4 2-3 -> 14-43 -> 11-33; L6 1-2 -> 0-35 -> 0-26. Imp spawns floors 11+ only. Fire_bolt does ~99% of an imp's damage once on (it shoots instead of closing). Other 8 abilities' monsters never spawn (VB-69), so imp is the only one that changes a real game now.


## TASK-VB-65 · Status effect system (poison, stun, root/adhesive, petrify) for monster and player abilities

```yaml
status: backlog
priority: medium
effort: 1d
tags: [architecture, abilities, content]
created: '2026-11-12T17:40:22Z'
updated: '2026-11-13T01:57:45Z'
session: vevine-1112
parent: VB-47
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  relates_to:
  - VB-64
  - VB-53
notes_next: 3
```

About 6 declared monster abilities need timed effects on the target: spider poison, wyvern poison_sting, basilisk petrifying_gaze + poison_bite, mimic adhesive. No status-effect primitive exists. Shape: per-entity effects list (name, turns_left, magnitude) ticked by the turn loop in single-player and multiplayer, an @status_effect registry, effects that gate actions (stun/root) checked in the action pipeline, persisted in saves via entity stats. See AI_ARCHITECTURE.md 'Later: status effects'.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T20:47:40Z session:warming-squall-1112] Consumables (52eb525): potion_strength (buff_attack), potion_speed (buff_speed), potion_invisibility have no @item_effect yet; they wait on this system. Add them in src/core/content/items/ (see docs/EXTENDING.md 'Add an item effect'); UseItemAction keeps an item whose effect is unregistered.
- [#2 2026-11-13T01:57:45Z session:mustard-sunset-1112] Priority raised low->medium 2026-11-12 (mustard-sunset-1112): the NetHack-depth review (umbrella VB-81) found status effects are the foundation for identification (VB-82: potion effects), shrines (VB-84) and counterplay monsters. Still no urgency to start before VB-82's scroll effects.


## TASK-VB-66 · AISystem.attack drops the monster attack's outcome.events: monster attacks never reach the event bus

```yaml
status: done
priority: low
effort: 30m
tags: [ai, events, bug]
created: '2026-11-12T17:40:23Z'
updated: '2026-11-12T18:08:59Z'
session: vevine-1112
depends_on: [VB-60]
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  - src/core/systems/ai_system.py
  relates_to:
  - VB-47
  - VB-55
  commits:
  - f72e78fcd440f393221facf463c70b595ad9708c
notes_next: 2
```

AISystem.attack executes AttackAction and adds outcome.messages to the log but discards outcome.events, so ATTACK_RESOLVED/ENTITY_DIED from monster attacks are never published (player attacks are, via process_action_outcome). Not verified yet whether telemetry (damage taken), achievements or anything else expect them. Fix: publish monster outcome events through the same pipeline once AISystem holds the event bus (VB-60 passes it in).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T18:08:59Z session:vevine-1112] Also fixed: StatsTracker counted every attack as the player's and recorded deaths only for entity_id == 'player' (real ids are UUIDs), so deaths/damage_taken were never tracked.


## TASK-VB-67 · Passive ability triggers for monsters and players: per-turn (regeneration, auras, enrage), on-hit (life drain, poison), on-death (rebirth, phylactery); plus teleport, phase_shift, disguise

```yaml
status: backlog
priority: medium
effort: 1d
tags: [ai, architecture, abilities, content]
created: '2026-11-12T18:21:49Z'
updated: '2026-11-13T01:57:45Z'
session: vevine-1112
depends_on: [VB-63]
parent: VB-47
links:
  references:
  - docs/architecture/AI_ARCHITECTURE.md
  - data/entities/monsters.yaml
  relates_to:
  - VB-64
  - VB-65
  - VB-53
notes_next: 2
```

13 of the 27 abilities declared in monsters.yaml are not actions, so the VB-63 engine ability step cannot express them: per-turn (troll/ancient_horror regeneration, demon fire_aura, phoenix flame_aura, ancient_horror phase_two enrage), on-hit (wraith/vampire life_drain; spider poison, wyvern poison_sting, basilisk poison_bite/petrifying_gaze, mimic adhesive need VB-65 too), on-death intercept before removal (phoenix rebirth, lich phylactery), movement (imp/demon teleport, wraith phase_shift through walls) and mimic disguise. Today only @damage_modifier exists (attacker-side, player-only via the abilities stat). Design one trigger mechanism (e.g. @passive(name, on='turn'|'hit'|'death') run by the engine for any actor whose resolved abilities include it, in core so MP gets it), keep it data-driven like abilities_for. Player regeneration/teleport (VB-53) should reuse it. See AI_ARCHITECTURE.md 'Monster ability inventory'.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-13T01:57:45Z session:mustard-sunset-1112] Priority raised low->medium 2026-11-12 (mustard-sunset-1112): passive triggers (regeneration, auras, enrage) are what give monsters distinct learnable rules; see umbrella VB-81.


## TASK-VB-68 · Automated play-testing: duel sim through AISystem, seeded paired bot runs, bot realism, fairness metrics

```yaml
status: in_progress
priority: medium
effort: 8-12h total (steps 1+2 ~half day)
tags: [fuzz, bots, balance, ai, tests]
created: '2026-11-12T19:21:49Z'
updated: '2026-11-13T03:05:56Z'
session: warming-squall-1112
parent: VB-47
links:
  references:
  - scripts/sim_duels.py
  - tests/fuzz/veinborn_bot.py
  - tests/fuzz/services/perception_service.py
  - tests/fuzz/services/tactical_decision_service.py
  - tests/fuzz/services/action_planner.py
  - docs/architecture/AI_ARCHITECTURE.md
  relates_to:
  - VB-64
  - VB-57
  - VB-32
notes_next: 8
```

Goal: turn most of 'play-test' into measurement so VB-64 (and later VB-65/67) become data decisions, and Scott's play-test shrinks to feel questions (fun, fairness feel, message readability, boss feel) on monsters the numbers already call balanced.

Gaps found 2026-11-12 (warming-squall-1112):
- scripts/sim_duels.py duel() hand-rolls the monster turn (step closer, bump AttackAction). It never calls AISystem, so perception, speed (energy), morale and monster abilities are invisible to it: it cannot measure VB-64 at all.
- veinborn_bot.py play_one_game calls game.start_new_game() with no seed (the game supports one), so before/after runs play different dungeons; 8 games x 3000 turns could not resolve speed or morale effects (vevine-1112).
- validate_game_state checks only HP range, bounds, inventory size.
- PerceptionService.find_monsters returns every living monster on the floor. That matches a human: the TUI shows every monster and players have no fog of war (see note #2), so this is not a bot gap.
- TacticalDecisionService.can_win_fight is deterministic atk-def; ignores d20 to-hit, damage spread, monster speed, ranged/summon abilities, morale.
- Bots never drink potions (loot drops them), never break LOS vs ranged monsters or use corridors vs packs.
- Per-class bots are one planner differing by CombatConfig (VB-57).
- GameResult has one death_cause; no per-monster breakdown or ability-damage share.

Path, in order:
1. (~2-3h) Duel/arena sim drives monster turns through AISystem.update (real perception, energy, morale, abilities via abilities_for/_use_ability). Matrix class x level x monster, each monster ability on/off: win%, HP lost, turns-to-kill, share of damage from abilities. Output a table TIA can propose VB-64 numbers from.
2. (~1-2h) --seed-base for bot runs; paired before/after on identical seeds (common random numbers), 32-64 games, report CIs on floor/deaths/turns.
3. (~3-4h) Bot realism: fight model with to-hit/speed/abilities, potion use, break-LOS vs ranged. Resolve VB-57 here (wire class trees as planner hooks or delete them).
4. (~2-3h) Fairness metrics + deeper invariants from the ATTACK_RESOLVED events (VB-66): burst deaths (>50% HP to dead within 2 turns), damage from attackers outside player sight, summon counts vs max_minions, disabled ability firing, cooldowns, actor overlap, actor in wall, monsters that fled and never returned. Per-monster breakdown in GameResult.

Steps 1+2 are the high-value half: do them before asking Scott for VB-64 numbers.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T19:31:29Z session:warming-squall-1112] Step 1 done a982c4f: scripts/sim_duels.py now runs monster turns via AISystem (TrackedAI subclass records damage melee/ability/minion and uses per ability, minion uses prefixed 'minion:'); --abilities off|on|both|m.a, --set m.a.k=v, --json. tests/unit/test_sim_duels.py (5), mutation (drop ctx.register_system('ai')) fails the summon test. Suite 1280. Found VB-69: only imp of the ability monsters is in any spawn table. Steps 2-4 open.
- [#2 2026-11-12T20:13:52Z session:warming-squall-1112] Correction (2026-11-12): bots are NOT more omniscient than humans. The TUI map (map_widget._render_cell) and sidebar show every monster on the floor; players have no fog of war (core/perception.py FogOfWar is unused, VB-32). So 'restrict bot perception to LOS' would make bots less human-like; dropped from step 3. The asymmetry is a design question for Scott: monsters need LOS (ADR-019) but players see all.
- [#3 2026-11-12T20:13:52Z session:warming-squall-1112] Step 2 done (3e8ef58, f378a49, 76222a4): --seed-base/--jobs/--output, scripts/compare_bot_runs.py (paired by class+seed, 95% CI). Found and fixed a core bug on the way: kill loot rolled on a fresh unseeded GameRNG(), so no seeded game replayed past the first kill (test_seeded_replay). Bot high scores now go to logs/, not data/highscores.json. Step 3 (part): potions/food were unusable by anyone -> UseItemAction + @item_effect + key e (52eb525); bots drink at <=40% HP and collect consumables within 6 tiles (38ce94d). Step 4 (part, d4a2505): per-monster damage, killer type, burst deaths, potions used; invariants for overlap/walls/carried-on-map/minion caps. Remaining: fight model (to-hit, speed, abilities), ranged-threat response, VB-57; A/B of potion use running (seeds 1000-1031, 3000 turns).
- [#4 2026-11-12T20:41:40Z session:warming-squall-1112] A/B results (seeds 1000-1031, 3000 turns, 4 classes = 128 pairs, scripts/compare_bot_runs.py). base 76222a4 -> potions d4a2505: deaths unchanged overall but MAGE deaths 7->14/32; rogue +1.3 floors. potions -> fight model (9480506): 125/128 games identical (fights start adjacent, verdict rarely flips with current monsters). Mage ablation: drink-only 6/32 deaths, collect-only 15/32 -> item detours into monsters were the killer; also stuck detection counted melee as stuck (1-HP bot took random 'wait'). Fixed in 15c0fba. base -> fixed 15c0fba: floor 8.44->9.12 (+0.68, CI +0.05..+1.31), deaths 10->7 (mage 7->6, rogue 3->1), rogue +1.31 floors, 0 crashes/errors, 0 burst deaths, 0.91 potions/game. Balance signal: warrior and healer 0/64 deaths in 3000 turns; mage ~20%; orcs deal the most damage (4689 of ~12.7k). Run copies with results JSON: /var/tmp/vb68_base_76222a4, /var/tmp/vb68_fixed_15c0fba (logs/*.json).
- [#5 2026-11-12T21:21:45Z session:serene-cyclone-1112] serene-cyclone-1112: per-monster breakdown in compare report done (paired damage taken per monster type with CI, bd1e44e). Deep starts (--start-floor/--start-level, tests/fuzz/scenario.py) for floors bots never reach; default runs unchanged (6/6 identical seeded games vs 1b5c10d). Remaining: bot response to ranged monsters, which matters once a ranged ability is enabled (VB-64).
- [#6 2026-11-12T21:41:41Z session:serene-cyclone-1112] Floor-stall fix 69c59c0, paired A/B (seeds 1000-1031, 3000 turns, 128 pairs, before 07667a7): floor 9.12 -> 11.70 (+2.59 [+2.16, +3.01]*), level 6.66 -> 7.41*, every class significant (mage +2.12, rogue +3.00, warrior +2.53, healer +2.69); deaths 6 -> 9 of 128 (+0.02 [-0.03, +0.06], mage 6 -> 9 of 32 as it reaches deeper floors), 0 crashes, 0 errors. All earlier floor numbers (incl. 'bots reach ~floor 10') were stall-limited. Results /var/tmp/vb68_stall_{before_07667a7,after_69c59c0}/logs/, compare.json in the after dir. New baseline for future A/Bs: the after_* files.
- [#7 2026-11-13T03:05:56Z session:quantum-energy-1112] a18c7ab: bots fetch boss materials (planner step 4b, MATERIAL_REACH 12, makes room by dropping the lowest-value item up to ore, never a material). Before it, an instrumented 3% run saw 995 material drops but 10 pickups and 2 legendary crafts in 12 warrior games, so the legendary path was unmeasured. Instrumented runner (logs drops, pickups, crafts): /var/tmp/vb75_long_r*_a18c7ab/instrumented.py.


## TASK-VB-69 · Spawn tables: 10 of 19 monsters never spawn (wyvern, vampire, lich, demon, phoenix, ancient_horror, wraith, mimic, golem, basilisk)

```yaml
status: done
priority: medium
owner: scott
tags: [balance, content, spawning]
created: '2026-11-12T19:31:16Z'
updated: '2026-11-13T18:11:57Z'
session: warming-squall-1112
links:
  references:
  - data/balance/monster_spawns.yaml
  - data/entities/monsters.yaml
  - docs/architecture/AI_ARCHITECTURE.md
  relates_to:
  - VB-64
  - VB-47
  - VB-68
  commits:
  - 867b6a418c23ca0df128b542aae6a8b7c0b4f164
notes_next: 6
```

Found 2026-11-12 (VB-68) while measuring monster abilities: data/balance/monster_spawns.yaml spawn_weights only names goblin, bat, orc, skeleton, wolf, spider, troll, ogre, imp. The other 10 monsters (all defined in monsters.yaml, several with ADR-019 abilities built) appear in no spawn table and no other data/balance file except recipe flavour (recipes.yaml 'requires lich/phoenix/ancient_horror kill'). So of the 9 built VB-64 abilities only imp fire_bolt (floors 11+) can affect a real game. Design call for Scott: which floors each monster belongs to, boss placement (ancient_horror as final boss?), weights. Measure each placement with scripts/sim_duels.py at the player level expected on that floor, plus seeded bot runs (VB-68 step 2).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T21:21:40Z session:serene-cyclone-1112] Prep done (serene-cyclone-1112): spawn bands are keyed by floor range (floor_N/floors_A_B/floors_A_plus, core/config/floor_bands.py), validated at load (cover every floor once, ids defined), so placing monsters is YAML only (28f9d9e). Bots can start deep: --start-floor/--start-level (bd1e44e). Baseline at floors 16+ (seeds 2000-2015, 1500 turns, start floor 16 level 8, starting gear only, 64 games): 2 deaths (mage, both troll), 0 crashes/errors; damage mostly troll then ogre; bots descend 0-4 floors. Results /var/tmp/vb69_deep_bd1e44e/logs/deep16_*.json. sim_duels (abilities off, level 7 / 10 win%): mimic/wraith/golem 98-100 at L7; wyvern/vampire 52-100 at L7, ~100 at L10; basilisk/lich 16-96 at L7; phoenix/demon 0-29 at L7, 20-89 at L10; ancient_horror 0 at both. Note wandering monsters use the band for (floor+level)//2, so deep-floor wanderers come from shallower bands.
- [#2 2026-11-12T22:12:00Z session:serene-cyclone-1112] Level/gear-by-floor curve, bots at a336011 (stall + inventory fixed), 24 games x 4 classes, 20000 turns, seeds 3000-3023 (bot_progression; /var/tmp/vb73_inv_a336011/logs/curve.json). Median on arrival: floor 5 L5 atk16/def7; floor 8 L6 26/18; floor 12 L7 36/33; floor 20 L9 38/33; floor 30 L10 39/33; floor 50 L11 40/33; floor 70 (turn ~18.5k) L11. Gear plateaus by floor 12, level ~11 from floor 50 (doubling XP curve). Reached floors: median 75, max 80, of 100. Deaths: 3 of 96, all rogues on floor 2 (orc); none past floor 3 in 1.8M bot turns. Use for placements: sim_duels --levels <curve level> --gear adamantite_greatsword@80,adamantite_plate@80 for floors 12+ (and see VB-75: at that gear every shipped monster is harmless, so placement alone cannot add danger).
- [#3 2026-11-13T01:22:38Z session:quantum-energy-1112] Bots now ignore ~/.veinbornrc (VB-76) and gold autopicks by default (0d1b700); together these reproduced the a336011 runs exactly (128/128 identical games). Superseded by VB-75 floor scaling (bfe5d1f), which changes every game past floor 1: current baselines are /var/tmp/vb75_base_bfe5d1f (3000 turns) and /var/tmp/vb75_long_r02_e25e163 (20000 turns).
- [#4 2026-11-13T01:57:45Z session:mustard-sunset-1112] Design principle to apply when placing monsters (mustard-sunset-1112, umbrella VB-81): prefer fewer monsters that each teach one learnable counterplay rule (like NetHack's floating eye) over enabling all 19 by stat alone; placement by stats cannot add danger while VB-75 stands. VB-64 abilities and VB-67 passives are the way to give monsters rules.
- [#5 2026-11-13T03:05:56Z session:quantum-energy-1112] All 19 monsters spawn (867b6a4): floors_16_plus split into 16-25 / 26-40 / 41-60 / 61+ by rising base strength; wraith and mimic join 11-15; boss-material monsters appear around their legendary recipe floors (wyvern 16+, lich 26+, phoenix 41+). ancient_horror is a single boss on floor 99 via the new monster_spawns.yaml boss_floors (not in any weight band, so dens and wanderers never draw it). Deep-start smoke: 0 errors, every new monster fights. Difficulty past floor 12 comes from VB-75's floor_scaling (rate chosen by long runs).


## TASK-VB-70 · Loot tables: only goblin, orc, troll drop anything; 16 of 19 monsters (bat, skeleton, ogre, wolf, spider, imp, ...) have no loot table

```yaml
status: backlog
priority: medium
owner: scott
tags: [balance, content, loot]
created: '2026-11-12T20:14:28Z'
updated: '2026-11-13T03:05:56Z'
session: warming-squall-1112
links:
  references:
  - data/balance/loot_tables.yaml
  - src/core/loot.py
  relates_to:
  - VB-69
  - VB-68
notes_next: 3
```

Found 2026-11-12 (VB-68) in bot logs: every kill of a monster without a table logs WARNING 'No loot table found for monster type: X' (core/loot.py generate_loot). data/balance/loot_tables.yaml has goblin, orc, troll only. Consequence now that potions and food are usable (52eb525): potion supply comes only from goblins/orcs/trolls, which thin out from floor 3 (skeleton/wolf/spider/ogre take over). Design call for Scott: which monsters drop what (animals: meat? undead: nothing?). Once decided, a monster that intentionally drops nothing should have an empty table or a flag so the WARNING means a real gap. Measure with seeded bot runs (scripts/compare_bot_runs.py: potions used, deaths).

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T21:21:41Z session:serene-cyclone-1112] Prep done (9f225e7): monsters.yaml loot_table names a shared table (null = own id), checked at load with every table item id; a description-only table drops nothing without the warning. So 'beasts drop meat' is one table plus loot_table: beast on bat/wolf/spider. Usable drops today: healing potions and food only; potion_strength and every scroll have no @item_effect (UseItemAction refuses them), so putting them in new tables adds dead weight until VB-65 / scroll effects exist.
- [#2 2026-11-13T03:05:56Z session:quantum-energy-1112] Boss materials done (8b5cb77, VB-75): lich, phoenix (essence + feather), ancient_horror always drop theirs; wraith and wyvern 50% (dragon_bone from the wyvern: no dragon exists; Scott may prefer another source). Those tables hold only the material. Still open here: drops for the other 11 monsters, and anything else the bosses drop.


## TASK-VB-71 · Balance knobs nobody reads: spawning.yaml monster_density (global + tier multipliers), ore_veins.yaml ore_types, ores.yaml floor_range; ore vein count grows without bound (8 + floor - 1 = 107 on floor 100)

```yaml
status: backlog
priority: low
effort: 1h
tags: [balance, content, dead-config, spawning]
created: '2026-11-12T21:21:29Z'
updated: '2026-11-12T21:38:47Z'
session: serene-cyclone-1112
links:
  relates_to:
  - VB-69
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T21:21:40Z session:serene-cyclone-1112] Found 2026-11-12 (serene-cyclone-1112) while making spawn bands data-driven (28f9d9e). GameConfig.get_monster_density_multiplier (spawning.yaml monster_density) has no caller: global_multiplier 1.0 'set to 1.5 for 50% more monsters' does nothing. ore_veins.yaml ore_types (floors/quality_range per ore) is read by nothing (entity_loader reads data/entities/ores.yaml ore_types; spawn_weights decides placement); comment added in the YAML. ores.yaml floor_range also unread (reveal src --grep floor_range: 0 hits). get_ore_vein_count_for_floor = base + floor - 1 has no cap: 17 veins on floor 10, 107 on floor 100. Decide per knob: wire it (density via the monster_counts bands; ore count as a band table with max) or delete it, as VB-59 did for the AI knobs.
- [#2 2026-11-12T21:38:47Z session:serene-cyclone-1112] Two more (serene-cyclone-1112): monster_spawns.yaml combat_balance (player_starting_stats, per-monster player_damage/hits_to_kill) is read by nothing in src/ or tests/ and its numbers predate the d20 to-hit model (sim_duels is the live answer now); items.yaml 'tools' (rope, torch, lockpick) is skipped by LootGenerator._load_items (category list lacks it) and no code references the category, so those items cannot be created or dropped.


## TASK-VB-72 · Shields can never be equipped: items.yaml shield has item_type 'shield', EquipAction accepts only weapon/armor; goblin, orc and troll loot tables drop them

```yaml
status: done
priority: medium
effort: 1-2h
tags: [bug, items, equipment, loot]
created: '2026-11-12T21:31:34Z'
updated: '2026-11-13T19:36:58Z'
session: serene-cyclone-1112
links:
  commits:
  - e6984a525a62a0826ef938403defba026d8b680b
notes_next: 5
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T21:31:41Z session:serene-cyclone-1112] Found 2026-11-12 (serene-cyclone-1112) adding sim_duels --gear. Runtime check: LootGenerator.create_item('shield') then EquipAction(...).validate(ctx) -> False, log 'invalid equipment slot' (chainmail -> True as control). reveal src --grep shield: 0 hits, so no off-hand slot exists anywhere. Drops: goblin armor 30%, orc 20%, troll 20% of armor rolls; each one is inventory clutter. Options: (a) off-hand slot (Player.equipped_shield, get_total_defense, save/load VB-19 path, TUI, bot equip logic), (b) retag shield as armor (it then competes with body armor, so nobody wears it), (c) drop shields from loot tables until (a). (a) is the real fix; (c) is a 2-line stopgap. Design call for Scott.
- [#2 2026-11-12T21:53:33Z session:serene-cyclone-1112] VB-73 (d06ac7d) gives a stopgap: shields rank as 'no use' in least_useful_item, so players can drop them with 'd' and bots drop them when the pack is full. The equip slot itself is still open.
- [#3 2026-11-13T19:23:11Z session:unexplored-thruster-1113] f8f2876 centralised the slot rule in core/equipment.py (SLOT_ATTR, gear_slot, GEAR_SLOTS) and the equipment screen lists only weapon/armor. An off-hand slot is now a data change there plus Player.equipped_shield, get_total_defense, save/load; still Scott's call.
- [#4 2026-11-13T19:36:58Z session:unexplored-thruster-1113] Option (a): shield slot. core/equipment.py GEAR_SLOTS/SLOT_ATTR gained 'shield'; Player.equipped_shield feeds get_total_defense; save/load (old saves load with none); sidebar line; equipment screen lists it; bot perception now uses core's worn_item/gear_bonus (any slot). Paired 3000-turn A/B (128 pairs, seeds 1000+): floor +0.15 [+0.02,+0.28], damage taken -1.5, 114/128 identical, so the VB-75 baselines still stand.


## TASK-VB-73 · No way to drop items: the 20-slot pack fills with unusable things (gold piles, shields, scrolls, rings, worse weapons) and then mined ore is lost and crafting stops for the rest of the game

```yaml
status: done
priority: high
effort: 3h
tags: [bug, items, inventory, core, bots]
created: '2026-11-12T21:47:23Z'
updated: '2026-11-12T21:55:52Z'
session: serene-cyclone-1112
links:
  commits:
  - a3360116e3225e62f10a52067e54d4e2469b92d7
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T21:53:33Z session:serene-cyclone-1112] Fixed d06ac7d (core: DropAction 'drop', least_useful_item, TUI d, autopickup skips own drops, RecipeManager.preview_stats) and a336011 (bots: wear looted gear via gear_slot, drop junk/worse gear then healing beyond 6 when full, craft only real upgrades). Cause: no drop action existed; pack filled by floor 4 (gold, unworn loot, scrolls, food) and mining/crafting stopped. Bot side made it worse: looted gear never worn (equipment_slot-only check), crafted non-upgrades endlessly once room existed. Warrior seed 3001 floor 12: atk 18/def 16 before, 36/33 after. Paired A/B and long runs running (a336011).
- [#2 2026-11-12T21:55:52Z session:serene-cyclone-1112] Paired A/B a336011 vs 69c59c0 (seeds 1000-1031, 3000 turns, 128 pairs): damage taken 134.3 -> 35.6 (-98.7 [-110.5, -86.9]*), deaths 9 -> 1 (mage 9 -> 1 of 32, -0.25*), potions used 1.39 -> 0.20*, floor 11.70 -> 11.19 (-0.52 [-0.95, -0.08]*: turns now go to forge trips and crafting), 0 crashes/errors. New A/B baseline: /var/tmp/vb73_inv_a336011/logs/inv_*.json.


## TASK-VB-74 · Gold has no use: gold piles drop from every loot table and fill inventory slots, but nothing reads gold_amount (no purse, not in score, nothing to buy)

```yaml
status: backlog
priority: medium
owner: scott
effort: '-'
tags: [design, items, loot, economy]
created: '2026-11-12T21:53:19Z'
updated: '2026-11-13T01:57:45Z'
session: serene-cyclone-1112
links:
  relates_to:
  - VB-73
notes_next: 5
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T21:53:33Z session:serene-cyclone-1112] Found 2026-11-12 (serene-cyclone-1112) chasing why bot gear stalled (VB-73). reveal src --grep 'gold_amount': only core/loot.py sets it; highscore, game_state, UI never read it. Gold piles take one of 20 slots each (a mage carried 8 by floor 4). Since d06ac7d least_useful_item ranks gold as 'no use' so 'd' drops it first. Options for Scott: (a) purse: pickup adds gold_amount to a player stat, no slot, shown in sidebar and counted in score; (b) remove gold from loot tables; (c) a use for it (shop, shrine, forge fee). (a) is the NetHack convention and cheap; what gold buys is the design question.
- [#2 2026-11-13T01:15:54Z session:quantum-energy-1112] Autopickup and gold (quantum-energy-1112): code default game.autopickup_types is ore,food,weapon, so gold reaches a pack only by manual 'g' (or a user rc adding gold). Bot runs before 1fcbdfd used Scott's ~/.veinbornrc (adds gold), so the 'gold fills slots' evidence in VB-73 came from that config; bots now run on defaults (VB-76). Part of this decision: should gold autopickup by default (game_constants or user default), and does it take a slot at all if it becomes a purse.
- [#3 2026-11-13T01:31:47Z session:quantum-energy-1112] Decided by Scott 2026-11-12: gold autopicks by default. 0d1b700: DEFAULT_AUTOPICKUP_TYPES = ore,food,weapon,gold feeds both the code fallback and the generated config file (they disagreed before). So gold now fills pack slots for every player and bot, as on Scott's machine; the purse question (does gold take a slot) stays open here.
- [#4 2026-11-13T01:57:45Z session:mustard-sunset-1112] Option (c) detail (mustard-sunset-1112): a gold sink via shrines/altars is filed as VB-84 (child of umbrella VB-81). Decide purse vs slot here first; VB-84 depends on that.


## TASK-VB-75 · Crafted gear outscales every monster: bots reach attack ~37 / defense ~33 by floor 12 (monsters top out at defense 8, attack 18), so nothing threatens a crafting player past the early floors

```yaml
status: done
priority: high
owner: scott
effort: '-'
tags: [balance, crafting, design]
created: '2026-11-12T21:53:20Z'
updated: '2026-11-13T04:43:49Z'
session: serene-cyclone-1112
links:
  relates_to:
  - VB-69
  commits:
  - bfe5d1fcae13e0a73f9fb95d5f14aedf021437bf
notes_next: 7
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-12T21:53:33Z session:serene-cyclone-1112] Measured 2026-11-12 (serene-cyclone-1112) after VB-73 let bots wear loot and craft upgrades: warrior/mage seed 3001 reach total attack 36-38 / defense 33 by floor 12 and plateau there (adamantite chestplate/weapon). Strongest shipped monster: ancient_horror attack 18 / defense 8; demon 13/6. With defense 33 most monsters hit for the minimum. Crafted stats come from recipes.yaml formulas on ore properties (hardness, purity, ...), so this is tunable in YAML. Design call: scale crafted gear down, scale monsters by floor, or gate high-tier recipes. Measure a change with paired bot runs. Limitation: sim_duels --gear takes items.yaml ids only, and crafted gear is not in items.yaml, so duels at crafted-gear strength need a --gear option for recipes (craft from synthetic ore of a given purity).
- [#2 2026-11-12T21:54:29Z session:serene-cyclone-1112] sim_duels --gear now crafts recipes (recipe@quality, 83f767f). Level 10, adamantite_greatsword@80 + adamantite_plate@80, start distance 4, 200 fights: warrior and mage beat demon and ancient_horror 100% with 0% HP lost (gearless at level 10: ancient_horror 0% win, demon 20-88%). So with top crafted gear the final boss is harmless.
- [#3 2026-11-12T22:12:00Z session:serene-cyclone-1112] Long runs (a336011, 96 games x 20000 turns) confirm: gear plateaus at median attack 38-40 / defense 33 from floor 12; 0 deaths past floor 3 in 96 games reaching median floor 75. The only real danger is floors 1-3 (3 rogue deaths to orcs on floor 2). Before VB-73 (pack locked, ebb2eb3 run) warriors had defense 3 for the whole game and 5/24 died deep, so the bot's gear loop, not monsters, was the difficulty.
- [#4 2026-11-13T01:57:08Z session:quantum-energy-1112] Lever study 2026-11-12 (quantum-energy-1112), sim_duels at the bots' curve checkpoints (gear reproduces measured atk/def: F5 L5 iron@55 ~15/9, F8 L6 mithril@75 ~24/17, F12/30/50 L7/10/11 adamantite@90 ~35-40/33), 200 fights/cell, abilities off, worst-class win% / mean HP lost on a win. Results + harness: /var/tmp/vb75_duels_6e7ad70 (levers_summary.txt, rate_sweep_summary.txt, run_matrix.py, run_sweep.py). (1) Halving crafted gear bonuses or diminishing-returns defense (to-hit def/2, damage roll*10/(10+def)) barely matter: from F5 on every common monster costs <=8% HP; only ancient_horror rises to ~20-29%. Monsters are weak against level growth alone, so gear is not the whole problem. (2) Monster floor scaling (hp/atk/def x (1 + r*(floor-1))) is the only lever that adds danger past F12, because the player stops growing (gear plateau F12, level ~11 from F50) while the game runs to F100. r=2%: F12-50 trivial, F75 demon 13% HP, F100 lich 94%/20%, demon 60%/51%. r=3%: F50 demon 13%, F75 lich 74%/34%, demon 25%/64%, F100 lich 10%. r=4%: F50 demon 64%/46%, F75 mostly unwinnable. Scaled ancient_horror is unwinnable from F50 (3%) / F75 (2%), so a final boss needs its own fixed stats. 6% (first pass) is a cliff (F30 demon 85%, F50 lich 10%). (3) Linear scaling vs a flat player always ends in a wall; the designed late growth is the legendary recipes (flaming_sword, titans_hammer, phoenix_armor ...), but RecipeManager._load_recipes loads only weapons+armor, so all 6 legendaries are dormant, and special_requirement (boss items) is read by nothing. Proposal for Scott: floor scaling ~2-3%/floor as a data knob (small spawner change), boss excluded/fixed; VB-69 placements for variety; legendary recipes + boss-item drops (VB-70) as the late player growth; then bot long runs for deaths by floor.
- [#5 2026-11-13T01:57:45Z session:mustard-sunset-1112] Design options to add (mustard-sunset-1112, from the NetHack review, umbrella VB-81): besides scaling gear down or monsters up, give crafting downsides as NetHack does for power (impure ore lowers durability or adds a curse chance, gear degrades, high tier needs rare ore). Related: the missing pressure past floor 3 is tracked as VB-83 (pacing clock). Measure any of these with paired bot runs.
- [#6 2026-11-13T04:43:49Z session:quantum-energy-1112] Done. Monster floor scaling (96443a3, rate 2% in bfe5d1f), legendary recipes live and gated on boss materials (8b5cb77), all monsters placed with a floor-99 boss (867b6a4), bots fetch materials and keep one of each (a18c7ab, e25e163). Long runs on e25e163, 4 classes x 24 x 20000 turns: 0% 3/96 deaths (floors 1-3), 2% 59/96 (16 on 41-60, 39 on 61-98, median floor 65.5), 3% 95/96 (85 on 41-60, median 48). Crafted gear still dominates floors 4-40 (same as before; the early game is unchanged on purpose). Follow-ups in VB-87. A/B baseline at bfe5d1f: /var/tmp/vb75_base_bfe5d1f (3000 turns); long baseline: /var/tmp/vb75_long_r02_e25e163 (data identical to bfe5d1f).


## TASK-VB-76 · Bot runs depend on the machine's ~/.veinbornrc: gameplay (MoveAction autopickup) reads per-user ConfigManager, so one seed plays differently per machine

```yaml
status: done
priority: medium
effort: 1h
tags: [bots, reproducibility, config, play-testing]
created: '2026-11-13T01:09:07Z'
updated: '2026-11-13T18:11:57Z'
session: quantum-energy-1112
links:
  commits:
  - 1fcbdfdef09add80e7445defcaea3ed71020499c
notes_next: 3
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-13T01:09:16Z session:quantum-energy-1112] Found 2026-11-12 (quantum-energy-1112). MoveAction._handle_autopickup reads ConfigManager (~/.veinbornrc, ~/.config/veinborn/config, VEINBORN_* env) for game.autopickup / game.autopickup_types. Scott's rc has autopickup_types = ore,food,weapon,gold; code default is ore,food,weapon. Bots pick up only consumables explicitly (ActionPlanner.collect_action), so gold reaches the pack only via autopickup, i.e. only on this machine (relevant to VB-74 'gold fills slots'). Measured, warrior seeds 1000-1002 x 1500 turns at 45ea525^: rc vs VEINBORN_GAME_AUTOPICKUP_TYPES=ore,food,weapon -> ore mined 25/19/16 vs 15/21/19, floor 6/6/6 vs 6/7/7. So the /var/tmp/vb73_inv_a336011 baselines carry gold-autopickup. Options: (a) bot harness pins a hermetic config (ConfigManager.reset + defaults, or set the env var) and regenerate the baseline; (b) move autopickup rules into game data (game_constants.yaml) and keep only the on/off preference per user; multiplayer server currently applies its host's rc to every player. Scott's call on (a)/(b) and on whether gold should autopickup by default (ties to VB-74).
- [#2 2026-11-13T01:22:38Z session:quantum-energy-1112] Option (a) shipped 1fcbdfd: ConfigManager.use_defaults(); bots (per game, covers forked workers) and every test (autouse conftest fixture) run on built-in preferences; VEINBORN_* env still applies on purpose. Then Scott made gold an autopickup default (0d1b700), equal to his rc for bots: a fresh run at 0d1b700 matched the a336011 baseline in 128/128 games, so today's refactors and the level-up RNG fix changed no fresh game. The intermediate no-gold run (1fcbdfd) differed in 127/128 games with no aggregate effect (floor -0.02 [-0.35,+0.31]). Both runs were later deleted: VB-75 floor scaling (bfe5d1f) changes every game, see /var/tmp/vb75_base_bfe5d1f. Not done: the multiplayer server still applies its host's rc to every player (option b: move autopickup rules to game data).


## TASK-VB-77 · Move game logic out of the Textual UI into core (equip list/cycle, look-at-ground, inventory listing, UI-authored messages)

```yaml
status: done
priority: medium
effort: 3-4h
tags: [architecture, refactor, ui]
created: '2026-11-13T01:46:24Z'
updated: '2026-11-13T20:19:12Z'
session: mustard-sunset-1112
links:
  references:
  - src/ui/textual/app.py
  - docs/architecture/ARCHITECTURAL_ASSESSMENT.md
  commits:
  - 91c929fea47681aaef60122a0ccf74b5771d9716
notes_next: 5
```

Found 2026-11-12 (session mustard-sunset-1112, TIA, investigating 'can we have a graphical UI'). src/core has zero UI imports, but src/ui/textual/app.py still holds game rules that any second frontend (graphical client, web client, multiplayer client) would have to copy:
- action_equip_item / action_cycle_equip (~42 lines each, near-identical): both re-derive 'equippable' from inventory (equipment_slot or item_type in weapon/armor), build the listing text, and keep equip_index in the App. Also odd behavior: pressing W equips item 0 immediately and cycling equips each item in turn as it goes.
- action_look_at_ground and action_show_inventory: query game.state.entities / inventory and format message text.
- action_use_item / action_drop_item already delegate the choice to core (best_healing_item, least_useful_item) -- that is the pattern to copy.
- The UI authors player-facing text by calling game.state.add_message(...) directly, so those messages exist only in the single-player game and never reach a server client.
Proposed: intent-level core calls (e.g. Game.equippable_items(), Game.cycle_equipment(), Game.items_here(), Game.inventory_summary()) returning data; the TUI formats and displays. Message-producing UI paths become core actions/outcomes so they go through the same pipeline as everything else. Keep behavior identical; add unit tests for each new core function. Do this before the snapshot task so the snapshot has the right shape.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-13T19:23:11Z session:unexplored-thruster-1113] f8f2876 did the equip part: core/equipment.py equipment_listing() (worn + wearable pack rows with change vs worn), UnequipAction, and the TUI 'w' screen (ui/textual/equipment_screen.py) reads it; the W-cycle and the duplicated listing code in app.py are gone. Still open here: look-at-ground, inventory listing, UI-authored messages.
- [#2 2026-11-13T20:18:17Z session:chartreuse-filter-1113] Look-at-ground and inventory listing done (core/item_listing.py, tests/unit/test_item_listing.py). Still open: UI-authored messages (use_item/drop_item 'nothing to...' texts, debug dump) should come from core outcomes. Full suite needs /usr/bin/python3 (has pytest_asyncio); the python3 wrapper errors on test_chat_system.
- [#3 2026-11-13T20:19:03Z session:chartreuse-filter-1113] quick_use/quick_drop moved into Game (messages now come from core). Audited survey/ability/descend/wait in app.py: thin delegates to handle_player_action, nothing to move. Only the debug-dump message stays UI-side (UI-only).
- [#4 2026-11-13T20:19:03Z session:chartreuse-filter-1113] Equip list (f8f2876), look-at-ground + inventory (item_listing.py), use/drop messages (Game.quick_*) all in core; suite 1453 passed


## TASK-VB-78 · Introduce a render snapshot (view model) shared by the TUI widgets and the server state

```yaml
status: backlog
priority: medium
effort: 1-2d
tags: [architecture, refactor, ui, multiplayer]
created: '2026-11-13T01:46:32Z'
updated: '2026-11-13T20:57:03Z'
session: mustard-sunset-1112
depends_on: [VB-77]
links:
  references:
  - src/ui/textual/widgets/map_widget.py
  - src/ui/textual/widgets/sidebar.py
  - src/server/multiplayer_game_state.py
  - src/server/state_delta.py
  relates_to:
  - VB-44
  - VB-26
  - VB-24
notes_next: 3
```

Found 2026-11-12 (session mustard-sunset-1112). Every Textual widget reads live domain objects (map_widget._get_entity_at walks game_state.entities; _render_cell reads game_map.tiles and imports TileType/EntityType; sidebar calls player.get_total_attack(), xp_for_next_level(), equipped_weapon, cooldowns). There is no render contract between core and UI. Separately, src/server/multiplayer_game_state.get_state_dict is a hand-rolled 85-line serializer that is a second, different description of the same state: it sends base attack/defense only (not totals including gear), no equipped weapon/armor, no XP/level/cooldowns, so a multiplayer client rendering it could not show what the single-player sidebar shows. Two state models also exist (core GameState vs MultiplayerGameState; see VB-24, VB-25 for earlier pipeline/floor duplication).
Proposed: a core function (e.g. Game.snapshot() / a Snapshot dataclass with to_dict) returning plain serializable data for: map tiles and visibility, entities by semantic type + content_id, player stats including derived totals, equipment, inventory, cooldowns, recent messages, turn/floor/game_over. Both the Textual widgets and the server's get_state_dict consume it. Open design points: (1) visibility/fog -- VB-68 note #2 says the TUI map and sidebar show every monster on the floor, so the snapshot should apply what the player may see; (2) delta strategy -- keep StateDelta working on the snapshot dict (see VB-26 about apply_delta complexity); (3) single-player vs multiplayer = same snapshot, different viewer. Payoffs beyond graphics: renderer tests without a live Game, one contract for VB-44, no duplicated serialization. Acceptance: Textual widgets import nothing from core except the snapshot types; server get_state_dict is built from the snapshot; existing TUI and multiplayer tests pass; new tests cover derived stats appearing in the snapshot.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-13T20:55:49Z session:chartreuse-filter-1113] Stage 1 done: core/snapshot.py (build_snapshot -> Snapshot/PlayerView/EntityView/MapView, to_dict, JSON-safe; no fog, same view as before; viewer arg is the hook) and the 4 TUI widgets render from it (map caches one snapshot per refresh_ui). entity-rendering tests rewritten on real state. Stage 2 open: server get_state_dict from the snapshot + state_delta (wire format: players/monsters/map keys are consumed by ui/multiplayer_client + server/test_client). Fog (perception.FogOfWar exists, TUI does not use it) is a gameplay decision, deliberately not in v1.
- [#2 2026-11-13T20:57:03Z session:chartreuse-filter-1113] Stage 2 done (partial): get_state_dict players now built with build_snapshot(viewer=player): stats are gear-inclusive totals + level/xp/xp_next, new equipment + abilities keys, StateDelta diffs them. Existing keys kept so test_client/MultiplayerClient are unchanged. NOT done: monsters/map still Entity.to_dict()/Map.to_dict() (not snapshot), no client renders from it yet (VB-44). Decide whether to close VB-78 or keep it open until get_state_dict's monsters/map also come from the snapshot.


## TASK-VB-79 · Emit semantic render IDs in the snapshot; make glyph/colour a per-frontend data mapping

```yaml
status: backlog
priority: low
effort: 4-6h
tags: [architecture, ui, content]
created: '2026-11-13T01:46:44Z'
updated: '2026-11-13T01:46:44Z'
session: mustard-sunset-1112
depends_on: [VB-78]
links:
  references:
  - src/core/base/entity.py
  - data/ui/layouts/README.md
```

Found 2026-11-12 (session mustard-sunset-1112). Entities carry display_symbol/display_color, so core describes appearance as terminal glyph + colour and the TUI renders it verbatim; terrain glyphs live in MapWidget.MAP_CHARS. A graphical or web frontend needs sprite/tile IDs instead. Proposed: snapshot emits entity_type + content_id (and tile type); a data file (YAML, consistent with the content system) maps those to glyph/colour for the TUI; a future frontend ships its own mapping. Keep display_symbol/display_color as the TUI default mapping source so content files need no mass edit. Only worth doing when a second frontend is real, hence low priority and future-ish. Check data/ui/layouts for an existing data-driven rendering mechanism first (docs/development/DATA_DRIVEN_RENDERING_POC.md, ENTITY_RENDERING_IMPROVEMENTS.md) and extend it rather than inventing a parallel one.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-80 · Spike: graphical frontend prototype on the snapshot (decide pygame/in-process vs browser over websocket)

```yaml
status: backlog
priority: low
effort: 1-2d
tags: [architecture, ui, design]
created: '2026-11-13T01:46:46Z'
updated: '2026-11-13T01:46:46Z'
session: mustard-sunset-1112
depends_on: [VB-78]
links:
  references:
  - src/server/README.md
  - src/ui/multiplayer_client.py
  relates_to:
  - VB-44
```

Found 2026-11-12 (session mustard-sunset-1112). Question from Scott: how possible is a fancy graphics UI. Finding: feasible; core has no UI imports, Game.handle_player_action(action_type, **kwargs) is the single input seam, EventBus has typed serializable events for animation, and a websocket server with JSON messages and StateDelta already exists. Blockers are VB-77 (logic in app.py), VB-78 (no render contract), VB-44 (client cannot send actions). Spike scope after those: pick between (a) in-process pygame/arcade/raylib calling Game directly and (b) a browser canvas/WebGL client over the existing websocket protocol (richest graphics, shareable, but needs the VB-44 action path and the server to host single-player). Output: a short decision note in docs/design/ with a thin vertical slice (map + player move + one monster) proving the snapshot is enough, plus whether the EventBus needs a client-facing animation feed. Do not start before VB-78 lands.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-81 · Umbrella: NetHack-style interaction depth (identification, pressure clock, shrines, bones, counterplay monsters)

```yaml
status: backlog
priority: medium
tags: [design, architecture]
created: '2026-11-13T01:57:27Z'
updated: '2026-11-13T01:57:27Z'
session: mustard-sunset-1112
```

Filed 2026-11-12 (session mustard-sunset-1112) from a design review of what makes NetHack durable. The consolidated design's 'NetHack Part' (docs/VEINBORN_CONSOLIDATED_DESIGN.md) is a generic roguelike checklist; what is thin is interaction depth, knowledge-over-reflexes, and pressure. Key measured fact behind the priorities (VB-75 / VB-69 notes): with crafted gear no shipped monster threatens a bot past floor 3 (0 deaths past floor 3 in 96 games reaching median floor 75), so the game currently has no pressure after the opening. Children carry the work; existing tasks that already cover part of this: VB-65 (status effects), VB-67 (passive triggers), VB-69/VB-64 (monsters), VB-74 (gold use), VB-75 (gear outscales monsters), VB-35 (Legacy Vault in MP). NOT to copy from NetHack: multi-hour runs (Veinborn is quick-restart plus meta-progression), cheap instadeath, wiki-dependence. Close this when its children are done or dropped.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-82 · Consumable identification: randomize potion/scroll appearances per run, give scrolls real effects, add a discoveries log

```yaml
status: backlog
priority: medium
effort: 2-3d
tags: [design, items, content]
created: '2026-11-13T01:57:29Z'
updated: '2026-11-13T01:57:29Z'
session: mustard-sunset-1112
parent: VB-81
links:
  references:
  - data/entities/items.yaml
  - src/core/content/items/healing.py
  - docs/EXTENDING.md
  relates_to:
  - VB-65
  - VB-70
  - VB-68
```

NetHack's core knowledge loop: unidentified potions/scrolls with per-run random appearances, learned by testing, risk and price. Veinborn half-has it: ore properties are hidden and Survey is an identification verb, but consumables are just named. Today potion_strength/speed/invisibility and every scroll have no @item_effect, so UseItemAction refuses them (VB-70 note #1, VB-65 note #1) and they only fill pack slots. Proposed: (1) give scrolls real effects (start with cheap ones: teleport, magic mapping, enchant gear, identify, plus one risky: aggravate/summon); potion effects that need status effects wait on VB-65; (2) per-run seeded mapping of item id -> appearance (e.g. 'murky potion'), stored in the run state and saves, deterministic from the run seed so bot runs stay reproducible (VB-68); (3) first use identifies that item type for the rest of the run; a risky unknown item is the gamble; (4) a discoveries list in the UI. Bots (VB-68) must either drink-test or ignore unknowns; measure with paired seeded runs. Do not bundle with loot-table work: VB-70 decides who drops what, this decides what the items are.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-83 · No pressure past floor 3: add a pacing clock (hunger/food) so mining and crafting trade against time

```yaml
status: backlog
priority: medium
owner: scott
tags: [design, balance]
created: '2026-11-13T01:57:30Z'
updated: '2026-11-13T18:11:31Z'
session: mustard-sunset-1112
parent: VB-81
links:
  relates_to:
  - VB-75
  - VB-70
  - VB-68
notes_next: 2
```

Evidence (VB-75 notes #1-#3, VB-69 note #2): 96 bot games, median floor 75, 0 deaths past floor 3; the only danger is floors 1-3. NetHack's hunger clock is what stops turtling and makes every spent turn (here: mining, crafting, resting) a cost. Veinborn has food but only as healing (UseItemAction). Design call for Scott: (a) gentle hunger: nutrition drains per turn, food restores it, starvation damages rather than instakills; mining costs extra nutrition, so greedy mining is the risk; (b) no clock, fix pressure through monsters/gear only (VB-75); (c) a softer clock such as monsters spawning faster the longer you stay on a floor (spawn_wandering_monster already exists). Hunger also gives food drops (VB-70 'beasts drop meat') a second purpose. Warning from NetHack: a tedious hunger loop is the version to avoid; prototype (c) first as it is cheapest, measure with paired bot runs on turns-per-floor and deaths.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-13T18:11:31Z session:quantum-energy-1112] Context from VB-75 (bfe5d1f, quantum-energy-1112): monsters now get 2% stronger per floor and all 19 spawn, so floors 41-98 kill bots (59/96 long-run games die there; 0% scaling: 3/96, all floors 1-3). Floors 4-40 are unchanged: still no pressure there, which is the part this task's clock would address. Measure any clock against /var/tmp/vb75_base_bfe5d1f (3000 turns) and /var/tmp/vb75_long_r02_e25e163 (20000 turns).


## TASK-VB-84 · Shrines/altars/fountains: gold sink and risk-reward gambles

```yaml
status: backlog
priority: low
tags: [design, content, economy]
created: '2026-11-13T01:57:32Z'
updated: '2026-11-13T01:57:32Z'
session: mustard-sunset-1112
parent: VB-81
links:
  relates_to:
  - VB-74
```

NetHack gives gold and spare items risk/reward outlets (altars, fountains, prayer). Veinborn gold has no use (VB-74, option c names 'shrine'). Proposed as a special-room type via the existing assign_special_rooms / spawn policy (core/spawning): shrine takes gold for a gamble (blessing, heal, enchant, or a curse); fountain quaff = small random effect; an altar identifies cursed/enchanted state if item curses are added (see VB-75 note about crafting downsides). Start with one shrine type that spends gold for a random buff; it also closes VB-74's 'what does gold buy'. Depends on a decision in VB-74 whether gold is a purse. Needs status effects (VB-65) for most buffs.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-85 · Bones: ghost and gear of a dead run appear on a floor of a later run

```yaml
status: backlog
priority: low
tags: [design, multiplayer, legacy]
created: '2026-11-13T01:57:34Z'
updated: '2026-11-13T01:57:34Z'
session: mustard-sunset-1112
parent: VB-81
links:
  relates_to:
  - VB-35
```

NetHack's bones files turn each death into content for the next player. Fits the existing Legacy Vault (rare ore saved on death) and adds asynchronous multiplayer with no live server. Proposed: on death, write a small record (floor, position, name, class, gear snapshot, killer) to a local bones file under the user data dir; a later run may place a ghost/tombstone monster guarding that gear on the matching floor, with a seeded chance so runs stay reproducible; killing it returns the loot. Keep the file format versioned (saves already serialize entities; see core/save_load.py and legacy_vault.py). Decisions: single-player only first (VB-35 notes the Legacy Vault singleton is not MP-safe); whether bones are shared between users is out of scope. Low priority: do after identification and pacing.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-86 · Distinct special floors (vault, shrine, boss floor) instead of uniform floors

```yaml
status: future
priority: low
tags: [design, content, spawning]
created: '2026-11-13T01:57:35Z'
updated: '2026-11-13T04:43:48Z'
session: mustard-sunset-1112
parent: VB-81
links:
  relates_to:
  - VB-69
notes_next: 3
```

NetHack's special levels (Oracle, big rooms, branches) give floors identity. Veinborn floors are BSP rooms + corridors from data/balance/dungeon_generation.yaml; assign_special_rooms already exists (core/spawning/spawn_policy.py) and the VB-69 note says ancient_horror as final boss placement is undecided. Proposed: a small set of named floor templates keyed by floor band (floor_bands.py validated config), e.g. vault floor with guarded ore, shrine floor (Shrines task), boss floor with fixed layout. Mostly YAML plus a template generator hook; check docs/DUNGEON_CONFIGURATION.md first. Future-ish: do not start before the identification and pacing tasks settle.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-13T01:57:45Z session:mustard-sunset-1112] Idea stage; do after identification (VB-82) and pacing (VB-83).
- [#2 2026-11-13T04:43:48Z session:quantum-energy-1112] VB-75 (867b6a4) added monster_spawns.yaml boss_floors: {floor: monster_id} places exactly one boss on that floor on top of its normal monsters (ancient_horror on 99). A designed boss floor here can build on it.


## TASK-VB-87 · Deep balance after VB-75: phoenix is 41 of 59 deaths at 2% floor scaling; Phoenix Armor never crafted; final boss on floor 99 untested

```yaml
status: in_progress
priority: medium
effort: 2-3h
tags: [balance, monsters, crafting, bots]
created: '2026-11-13T04:43:37Z'
updated: '2026-11-13T19:56:27Z'
session: quantum-energy-1112
notes_next: 4
```

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-11-13T04:43:48Z session:quantum-energy-1112] From the VB-75 long runs at 2% (/var/tmp/vb75_long_r02_e25e163, 4 classes x 24 x 20000 turns, instrumented: logs/long_*.jsonl has material drops, pickups, crafts). (1) Phoenix kills 41 of 59 (demon 11, lich 4): base attack 14 (highest after the boss) and weight 30 of 115 in floors_61_plus; candidates: lower its weight or attack, or start it later. Mages die most (22/24), healers least (3/24). (2) No bot crafted Phoenix Armor in any run (needs 6 adamantite at once; bots craft adamantite_plate x4 first); Flaming Sword 15, Arcane Staff 25, Dragon Bow 94. Either the bot needs to save ore for it or 6 is too many. (3) No bot reaches floor 99 in 20000 turns (max 76), so the ancient_horror boss is unmeasured: use --start-floor 98 runs and sim_duels at the curve's level and legendary gear. (4) xp_reward does not scale with floor_scaling; level plateaus ~11 from the doubling curve anyway. (5) Titan's Hammer needs the floor-99 boss's core and the game is won on 100, so it is a trophy unless the core comes from elsewhere. (6) dragon_bone comes from the wyvern (no dragon exists).
- [#2 2026-11-13T18:47:30Z session:unexplored-thruster-1113] Done in cb8ad90 + next commit: (1) phoenix weight 30->15, paired long run (seeds 3000+, 4 classes x 24 x 20000 turns, /var/tmp/vb87_w15/logs): deaths 59->52, phoenix kills 41->34, median floor 65.5->67; phoenix is still the top killer, so the weight is a weak lever. (3) Boss: sim_duels --floor now scales monsters; at level 11 with flaming_sword@90+adamantite_plate@90 ancient_horror (floor_scaling false) is 100% win/0% HP lost, phoenix/demon/lich at floors 61-95 are 88-100% wins. A geared player crushes the late game; bots die for lack of that gear. Open: (2) bots never craft Phoenix Armor (needs 6 adamantite at once), (4) xp unscaled, (5) Titan's Hammer trophy.
- [#3 2026-11-13T19:56:27Z session:unexplored-thruster-1113] Baseline moved: the current 20000-turn baseline is /var/tmp/vb87_w15/logs (phoenix weight 15, before shields); /var/tmp/vb75_long_r02_e25e163 is the phoenix-30 one. Next: bots to save 6 adamantite for Phoenix Armor, then decide boss tuning (floor-99 horror is a pushover at level 11 with adamantite gear).
