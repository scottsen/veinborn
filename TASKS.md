---
project: veinborn
schema_version: '1.0'
id_prefix: VB
next_id: 16
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
status: backlog
priority: low
effort: 1d
tags: [refactor, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T06:31:19Z'
session: yaeger-zealot-0804
```

game.py: 1 class, 20 methods, 23 imports, 5 mixed responsibilities (bootstrap, event wiring, Lua integration, turn orchestration, persistence). handle_player_action is a single chokepoint for all 7 UI callers.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-12 · Split game_session.py: PlayerConnectionState + GameSession + GameSessionManager

```yaml
status: backlog
priority: low
effort: 1d
tags: [refactor, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T06:31:19Z'
session: yaeger-zealot-0804
```

760 lines, 4 classes in one file, worst nesting in the repo (depth 4-5). process_action has exactly 1 caller yet complexity 13 -- the complexity is not reused/amortized, just deeply nested inline logic.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


## TASK-VB-13 · Move Map's entity-placement policy (find_monster/ore/player positions) out of world.py into src/core/spawning/

```yaml
status: backlog
priority: low
effort: 3h
tags: [refactor, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T06:31:19Z'
session: yaeger-zealot-0804
```

world.py's Map mixes BSP dungeon-generation algorithm with domain-specific spawn policy (find_player_spawn_positions, find_monster_positions, find_ore_vein_positions, assign_special_rooms, place_stairs). Couples dungeon generation to every future entity type.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_


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
status: backlog
priority: low
effort: 2h
tags: [refactor, code-quality]
created: '2026-08-05T06:31:19Z'
updated: '2026-08-05T06:31:19Z'
session: yaeger-zealot-0804
```

lua_action.py:241 _table_to_outcome uses 5 separate nested try/except blocks (cx16-19, depth 6) instead of one lua_table_get(table, key, default, coerce) helper. lua_event_handler.py load/handle look like they'd benefit from the same helper.

<!-- notes: append-only log; each has a stable #id (see CLI §5) -->
### Notes
_(no notes yet)_
