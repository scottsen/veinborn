---
project: veinborn
schema_version: '1.0'
id_prefix: VB
next_id: 45
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
updated: '2026-09-23T05:56:31Z'
session: earthly-god-0922
notes_next: 2
```

GameRNG is a class-level singleton (core/rng.py:75-112). multiplayer_game_state.py:100-102 calls GameRNG.initialize(self.seed) unconditionally when the first player joins a new game, which replaces the shared process-wide instance. Every dungeon-gen/spawn/loot call site (world.py, entity_spawner.py, spawn_policy.py, entity_loader.py:242, entities.py:322) reads via GameRNG.get_instance() -- the same shared object. Two games running concurrently on one server stomp each other's RNG stream: starting game B mid-session silently rewires game A's in-flight combat rolls, loot, and future dungeon-gen to draw from game B's seed. Breaks per-game determinism/reproducibility. Fix: give each GameState its own GameRNG instance threaded through GameSession/MultiplayerGameState and exposed via ctx.rng; also remove ai_system.py's direct stdlib random module usage (lines ~436,441) which never replays from a seed either.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T05:56:31Z session:earthly-god-0922] Fixed: each game now gets its own dedicated GameRNG instance instead of every generation/spawn call reaching for the process-global GameRNG.get_instance() singleton. Map now holds self.rng (captured at construction, defaults to the singleton only for back-compat callers); world.py's split_node/create_rooms/connect_rooms, spawn_policy.py's ore-position/special-room functions, and entity_spawner.py's weighted-choice/treasure-room/monster-den/ore-chamber methods all read the owning map's .rng instead of calling GameRNG.get_instance() fresh. entity_loader.create_ore_vein() takes an explicit rng param now (falls back to the singleton only when omitted). multiplayer_game_state.add_player() constructs GameRNG(seed) directly and threads it through GameState.rng/dungeon_map.rng, instead of calling GameRNG.initialize(seed) which reassigned the shared class-level singleton out from under any other concurrent game; descend_floor() reuses the same instance for the next floor. Added GameState.rng field and GameContext.get_rng(); ai_system.py's _wander() now uses context.get_rng() instead of stdlib random (removed the direct import). save_load.py's _deserialize_state() restores RNG state into a dedicated per-load instance (state.rng/dungeon_map.rng) instead of writing into the global singleton, so a loaded game's continued play can't be corrupted by another concurrent game either -- required updating two existing tests (test_rng_state_restored, test_seeded_run_continues_correctly) that had asserted against GameRNG.get_instance() by design. Added test_concurrent_games_do_not_share_rng_stream (tests/unit/server/test_multiplayer_game_state.py) proving two concurrently-started MultiplayerGameStates get independent RNG streams and dungeon layouts. Full suite: 1102 tests pass (up from 1067 baseline; net new/updated tests from this work plus VB-16/17).


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
updated: '2026-09-23T16:54:07Z'
session: earthly-god-0922
notes_next: 2
```

Static-analysis heuristic flagged 33 uncalled functions; most (action_factory.py 8 _create_* methods, ai_system.py 5 _behavior_* methods) are almost certainly dict/registry-dispatched and not actually dead -- confirm via reveal 'calls://src?target=_create_move_action&depth=2' before touching. Genuinely worth investigating: telemetry.py:311/349 (log_combat, log_player_death -- hooks that may just not be wired up yet) and perception.py:205-268 (four get_visible_*/get_nearby_ore/get_entities_at_distance helpers, all uncalled -- possibly superseded by update_visibility's internal logic, or dead API surface left from a refactor). run_server.py flagged as 'not imported anywhere' is a false positive (CLI entry point) -- ignore.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T16:54:07Z session:sultry-drizzle-0923] Investigated 2026-09-23, nothing deleted -- each remaining item needs a product call. (1) src/core/perception.py: FogOfWar/TileVisibility/PerceptionSystem have NO production caller (only referenced inside the file); tests/unit/test_perception.py (786 lines) tests it, and docs/development/BOT_* describe it, but the fuzz bots use their own tests/fuzz/services/perception_service.py. So get_visible_monsters/get_nearby_ore/get_entities_at_distance are dead as part of a wholly unwired module: decide wire-in (fog of war / bot API) vs delete module+tests. (2) telemetry.py GameTelemetry.log_combat/log_player_death: never called; Game builds game_telemetry but nothing writes to it. StatsTracker IS wired via EventBus subscribers, but see VB-33 -- most action events fail to publish, so even that is mostly silent. Decide alongside VB-33. (3) Action-factory _create_* and ai_system _behavior_* are registry-dispatched, not dead; run_server.py is a CLI entry point. Not dead.


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
updated: '2026-09-23T17:29:04Z'
session: crimson-jewel-0923
links:
  references:
  - VB-24
  - src/core/highscore.py
notes_next: 2
```

VB-24 writes per-player co-op scores to data/highscores_multiplayer.json but nothing displays them (no client message, CLI, or screen). Legacy Vault (rare-ore save on death) is still single-player only; get_vault() is a process-wide singleton, so wiring it into a server needs a per-player persistence decision first. Per-player stats (monsters_killed etc.) are also read from player.stats, which nothing appears to write in either mode - check before designing a co-op scoring UI.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
- [#1 2026-09-23T17:29:04Z session:crimson-jewel-0923] Update 2026-09-23: the 'player.stats never written' concern is resolved by VB-38 (d16aa49) - co-op scores now include kills/damage/ore per player, so a leaderboard viewer is now worth building.


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
updated: '2026-09-23T17:41:24Z'
session: crimson-jewel-0923
links:
  references:
  - src/ui/multiplayer_client.py
  - src/ui/textual/app.py
  - src/server/test_client.py
```

The first real two-client playtest (scripted, headless) worked after VB-39..43, but the only thing that can send move/attack/mine over the wire is the dev tool src/server/test_client.py. ui/multiplayer_client.MultiplayerClient has connect/chat/create/join/ready and delta merging but no send_action; ui/textual/app.py only wires chat. A human two-client playtest needs a multiplayer game view in the TUI (render players/monsters/map from the merged state, send MoveAction/AttackAction/... with the entity_id from state). Design question: reuse the single-player map widget with a state adapter, or a new read-only renderer.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_
