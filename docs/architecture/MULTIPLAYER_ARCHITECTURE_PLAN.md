---
title: "Multiplayer architecture plan: one engine, intents in, snapshots out"
type: architecture
status: in-progress
date: 2026-11-13
beth_topics:
  - veinborn
  - multiplayer
  - architecture
  - server
  - protocol
  - snapshot
  - turn-scheduler
---

# Multiplayer architecture plan

**Status:** phases 0-4 built (2026-11-13: VB-88..VB-102; two people can play in the TUI) plus the
drop half of D7; phase 5: rejoin `VB-103` and fog of war `VB-105` built, first human playtest `VB-104` open.
Proposed 2026-11-13 (session chartreuse-filter-1113); rulings in section 6. Section 1 ("Today")
and the "what the measurement found" lists are the record of the code *before* each phase.

**Goal:** single-player and multiplayer run the *same* rules code; the server is a thin
async shell around it; clients send intents and render snapshots; every boundary is a small
typed interface with tests on both sides.

Related: [DECISIONS.md](DECISIONS.md) (ADR-012 server-authoritative, ADR-016 4-actions-per-round, superseded by ADR-020),
[MULTIPLAYER_DESIGN_2025.md](../design/MULTIPLAYER_DESIGN_2025.md) (the original vision),
[ARCHITECTURAL_ASSESSMENT.md](ARCHITECTURAL_ASSESSMENT.md), tasks VB-44, VB-78, VB-26, VB-45,
VB-55, VB-54, VB-35 (`tt show <id>`).

---

## 1. Today (verified in code, 2026-11-13)

### What is already right
- **Server-authoritative** (ADR-012): actions run on the server; clients only receive state.
- **Rules are shared at the action level**: the server executes the same `core.actions`
  classes, and both sides call `core.action_pipeline.process_action_outcome` (VB-24 slice 1).
- **Floor helpers are shared** (VB-25): `generate_floor_map`, `spawn_all_for_floor`,
  `clear_floor_entities`, `get_victory_floor`, `apply_hp_regeneration`.
- **Per-game RNG** (VB-18), session lock around action processing, reconnect handling (VB-22),
  a co-op leaderboard, and solid server unit tests (236).
- **Render snapshot** exists (`core/snapshot.py`, VB-78) and the TUI widgets render from it.

### Where the two paths still diverge

| Concern | Single-player | Multiplayer | Consequence |
|---|---|---|---|
| Who the players are | `GameState.player` (privileged) | first player *is* `state.player` (id `"player"`), the rest are only in `entities` (`MultiplayerGameState.add_player`) | 41 `state.player`/`get_player()` sites in core assume one player. **Fixed (VB-89, VB-94):** party rules read `get_all_players()`; MP builds the run once from the seats, every seat id is `player_<id>`, `state.player` = first seat for compatibility only |
| Turn tick | `TurnProcessor.process_turn`: regen, **wanderer spawns**, AI, cleanup, game over, `turn_ended` event | `GameSession._process_monster_turn`: AI, turn++, regen, cleanup | MP has no wanderers (VB-52), no `turn_ended` |
| Floor change | `FloorManager.descend_floor` + `floor_changed` event | `MultiplayerGameState.descend_floor` | MP has no `floor_changed`; two victory checks |
| Game start | `Game.start_new_game` + `game_started`, content handlers installed | `GameSession.start_game` | achievements/quests SP-only (VB-55) |
| End of run | high score + Legacy Vault inside TurnProcessor/FloorManager | `_record_scores` in the session | end hooks hard-coded on each side |
| Intent -> action | `ActionFactory.create('move', dx=..)` resolves targets (adjacent ore, item here, ...) with `context.get_player()` as actor (15 sites) | client sends a *built* action: `{"action_type": "MoveAction", "actor_id": ...}`; server deserializes with `ActionRegistry` | client must know entity ids and Python class names; actor is client-supplied (then checked) |
| State out | `Snapshot` | `get_state_dict`: hand-built dict + `Entity.to_dict()` + `Map.to_dict()` (per-player part now from the snapshot) | two descriptions of one state |
| Sync | n/a | one `last_state` baseline **per session**, deltas without sequence numbers (VB-26) | a client that joins late or misses one delta is silently wrong forever |
| Client | `VeinbornApp` owns a `Game` | `VeinbornApp` *still* starts a local `Game`; client listener dies with the first event loop (VB-44 note #2) | the multiplayer TUI cannot play |
| Disconnected seat | n/a | after 120 s the seat is deleted, the character stays standing in the world, and `can_join` refuses started games; `process_disconnected_player_action` has no caller (VB-45) | a dropped player can never come back (fixed by VB-103); dead code |

Stale ADRs: ADR-011 (NATS), ADR-013 (PostgreSQL), ADR-014 (Pydantic) are "Designed" and
nothing implements them; the server is one process with a hand-rolled `Message` dataclass.
They should be marked **Deferred** so they stop reading as the plan.

**Pattern:** every MP gap above is the same bug: MP re-implements a step of the SP loop and
the copy lags. Fixing gaps one by one (VB-4, VB-24, VB-25, VB-55, ...) has worked but never
ends. The fix is structural: one loop.

---

## 2. Target architecture

```
                 ┌──────────────────────── src/core (pure, sync, seeded, no I/O) ─────────┐
 intents ──────► │ Engine.submit(actor_id, Intent) -> Outcome                             │
                 │   ActionFactory(actor) -> Action.execute -> process_action_outcome     │
                 │   TurnScheduler.after_action(took_turn) -> maybe world_tick()          │
                 │   world_tick = TurnProcessor (N players) ; FloorManager (N players)    │
                 │   events: game_started, turn_ended, floor_changed, run_ended, ...      │
 snapshots ◄──── │ Engine.snapshot(viewer_id) -> Snapshot                                 │
                 └────────────────────────────────────────────────────────────────────────┘
                        ▲                                   ▲
      src/protocol (pure data, imported by both sides): Envelope{v, seq, type}, Intent,
      Snapshot.to_dict/from_dict, (later) snapshot delta
                        ▲                                   ▲
 ┌── src/server (async shell) ───────────┐    ┌── src/client (frontends) ──────────────────┐
 │ websocket + auth + lobby              │    │ GameDriver: snapshot(), submit(intent),     │
 │ GameSession = Engine + seats          │    │             on_update(cb)                   │
 │   seat: player_id -> entity_id,       │    │  LocalDriver(Engine)   RemoteDriver(ws)     │
 │   connected | grace | dropped         │    │ Textual widgets render Snapshot only        │
 │ per-client seq, full snapshot on join │    └─────────────────────────────────────────────┘
 └───────────────────────────────────────┘
```

Single-player is "an Engine with a party of one and a LocalDriver" (with one seat, the round scheduler ticks after every action).
Multiplayer is "the same Engine with N seats, the same round scheduler, and RemoteDrivers".

---

## 3. Decisions

### D1. One engine, N players natively
- `GameState` gains an ordered `player_ids` list; `state.player` stays only as a
  compatibility property (first player) during migration, then goes away in core rules.
- `GameContext.get_player()` is replaced at each call site by an explicit actor or
  `get_alive_players()`. Single-player behaviour is unchanged because the party has one member.
- `TurnProcessor` and `FloorManager` take the party: regen every living player (already the
  shared `apply_hp_regeneration`), game over = no living player, placement = N spawn
  positions (MP's `_reposition_players_at_new_floor` logic moves into core).
- End-of-run side effects (SP high score, Legacy Vault, MP co-op leaderboard) stop being
  hard-coded: the engine publishes `player_died` / `run_ended`, and each host subscribes the
  handlers it wants. Same for content handlers (achievements, quests): installed by the
  engine, so MP gets them (closes VB-55).
- `MultiplayerGameState` dissolves: rules go to core, seat bookkeeping goes to `GameSession`.

### D2. Turn scheduling is a policy object
```python
class TurnScheduler(Protocol):
    def after_action(self, actor_id, took_turn: bool) -> bool: ...  # True = run world tick now
```
- **Ruled (Scott, 2026-11-13): one action per living player per round.** Monsters act once
  every living, seated player has taken one turn-consuming action. This replaces ADR-016's
  "4 actions, anyone can take them" (today's code: `actions_per_round = 4`).
- `RoundScheduler`: holds the set of seats that still owe an action this round; ticks when
  it is empty, then refills it with the living seats. Free actions (equip, unequip,
  `took_turn=False`) never count. Single-player is the same scheduler with one seat, so
  `EveryActionScheduler` is not needed: a party of one ticks after every action, as today.
- A player who has already acted is told "waiting for the party" and the intent is rejected
  (not queued), so the client can show who the round is waiting on. Snapshot carries
  `round.waiting_on` for that.
- Dead players and dropped seats (D7) leave the owed set immediately, so they never stall a round.
- The world tick is always `TurnProcessor.process_turn`, so MP gains wanderers and
  `turn_ended`, and `_process_monster_turn` is deleted.
- **(Scott, later)** a connected but idle player stalls the round. Options when it matters:
  a per-round timer that auto-waits for them, or a party vote. Not needed for the first
  playable build.

### D3. Intents on the wire, actions stay server-side
- Client sends `{"type": "intent", "intent": "move", "args": {"dx": 1, "dy": 0}}`.
  The server takes the actor from the **session seat**, never from the payload, and calls
  `ActionFactory.create(intent, actor_id=seat.entity_id, **args)`, the exact call
  single-player makes.
- `ActionFactory` gets an explicit `actor_id` parameter (replaces 15 `context.get_player()`).
- Wins: no actor spoofing by construction; the client needs no target ids (mine/attack/
  pickup are resolved server-side, as in SP); the wire format is not Python class names;
  SP and MP share one input path.
- `Action.to_dict/from_dict` and `ActionRegistry` remain for replay logs and saves, not for
  client input. The old `action` message is accepted during migration, then removed.

### D4. Snapshot is the only read contract
- `Engine.snapshot(viewer_id)` builds a `Snapshot` (already in `core/snapshot.py`) for that
  viewer: the viewer's `PlayerView`, other players as entities, monsters, map, messages.
- The server sends snapshots; the client decodes with `Snapshot.from_dict` and the same
  widgets render it. `get_state_dict` and the hand-built player/monster dicts retire.
- **Built (VB-105, 2026-11-13):** `core/fog.py`; each viewer's explored memory lives on the `Map`
  (`Map.explored_by`, so a new floor starts empty, saved with the map); `build_snapshot` hides unseen
  tiles (`' '`), monsters/items out of sight (radius 9, line of sight), keeps ore veins/forges where the
  tile is remembered and other players always; `MapView.lit` lets the widget dim remembered tiles;
  `reveal_map` is `GameState.reveal_map` (`--reveal-map` in `run_textual.py` / `run_multiplayer.py`,
  `create_game` option). Protocol 4. Bots do not use snapshots, so the bot A/B gate is untouched.
  `perception.FogOfWar` stayed unused (its per-instance arrays do not fit per-viewer memory).
- **Ruled (Scott, 2026-11-13): fog of war is on by default**, applied here per viewer
  (`core/perception.FogOfWar` exists and is unused today). A **development reveal switch**
  turns it off to see and test map features: a config/CLI flag (e.g. `--reveal-map`) for
  single-player and a per-game server option for MP dev games, both read by `build_snapshot`
  and nowhere else, so the rules never depend on it. A sidebar marker shows when it is on.
  Turning fog on changes what players see today (the TUI shows every monster on the floor,
  VB-68 note #2), so it ships as its own step with the bot runs unaffected (bots use
  `perception`, not the snapshot).
- VB-79 (semantic render ids instead of terminal glyphs) slots in here later.

### D5. A shared protocol package, versioned and sequenced
- `src/protocol/`: `Envelope{v, seq, type, data}`, the message types, the intent schema,
  snapshot (de)serialization. Server and client import it; the client imports nothing else
  from core except snapshot types. `server/messages.py` and `server/state_delta.py` move here.
- Every server->client state message carries `seq`. Each connection tracks its own last
  acknowledged state.
- **Full snapshots first, deltas later.** Measured 2026-11-13: a full 4-player state message
  is ~11 KB (snapshot ~7 KB); at human action rates that is nothing. Sending full snapshots
  deletes the shared-baseline bug and most of VB-26's complexity. Reintroduce deltas only if
  a measurement shows a need, and then as snapshot diffs with `base_seq` + resync on gap.
- Pydantic (ADR-014) is not needed for this; dataclasses with explicit `to_dict/from_dict`
  and round-trip tests are enough. Revisit if a non-Python client appears.

### D6. Client driver interface
```python
class GameDriver(Protocol):
    def snapshot(self) -> Snapshot: ...
    async def submit(self, intent: str, **args) -> None: ...
    def on_update(self, callback) -> None: ...
```
- `VeinbornApp` takes a driver, not a `Game`; key bindings call `driver.submit('move', dx=..)`;
  redraw on update. `LocalDriver` wraps an Engine (today's behaviour); `RemoteDriver` wraps
  the websocket client.
- The remote client connects inside Textual's event loop (on mount / `run_async`), so there
  is one loop and the listener lives (VB-44 note #2).
- UI-only screens (equipment screen) read the snapshot and submit intents (`equip`,
  `unequip`), so they work remotely for free.

### D7. Seats with a disconnect lifecycle
**Ruled (Scott, 2026-11-13): on disconnect we wait a while; then the player is dropped, but
can rejoin the party.** No AI control of absent players.

`GameSession` holds `seats: player_id -> Seat(entity_id, state, character)`:

```
 connected ──disconnect──► grace (round waits; character stays on the map)
     ▲                       │ reconnect within grace -> connected, nothing lost
     │                       │ grace expires (today 120 s, PlayerInfo.reconnect_timeout_seconds)
     │                       ▼
     └────── rejoin ◄──── dropped (character leaves the floor; the round stops waiting;
                                    character state kept in the session)
```

- **Grace:** the round waits for them (one action per living player), so the party sees
  "waiting for <name> (disconnected, 1:45)". Same as today's reconnect path (VB-22).
- **Dropped:** the character entity is removed from the world but its full state (hp, level,
  inventory, gear) is kept on the seat; the scheduler no longer owes it an action. If every
  seat is dropped the game ends as today.
- **Rejoin:** the player authenticates again and joins the running game by id (or from the
  lobby list, which shows "rejoinable" games). The character is placed near the party on the
  *current* floor and is owed an action from the next round.
- Changes from today: `can_join` refuses started games and `_remove_player_locked` deletes the
  seat while leaving the character standing in the world. Both go.
- `process_disconnected_player_action` and the AI-control idea are deleted (closes VB-45 as
  "won't do, replaced by the drop/rejoin lifecycle").
- **Ruled (Scott, 2026-11-13):** rejoin is for the same identity: the auth token resumes the seat; with no
  token, a name match is allowed only while exactly one dropped seat has that name.
- **Done (2026-11-13, with VB-102): the drop half.** Leaving (`leave_player`) or an expired grace
  (`cleanup_expired_disconnections`) calls `MultiplayerGameState.drop_seat`: the character leaves the
  floor, its entity stays on the slot, the scheduler stops owing it, and if it was the last seat owed
  the world ticks. The party view marks it not connected.
- **Done (2026-11-14, VB-103): the rejoin half.** `join_game` for a started game calls
  `GameSession.rejoin_player`: the seat of the caller's player id (the token resumes it), else a unique
  name match (the seat is re-keyed, `MultiplayerGameState.rekey_seat`). `MultiplayerGameState.rejoin_seat`
  puts the kept character on the nearest free tile to a living party member and leaves the scheduler alone,
  so it is owed from the next round; a dead character returns as a spectator. An expired grace in a started
  game keeps the `PlayerInfo` (`mark_left`) instead of deleting it; `can_join` still means "a new seat in a
  lobby" and the lobby list shows `rejoinable` names. `PartyMemberView.grace_left` (protocol v3) drives
  `Bob (disconnected, 1:45)` in the status bar. The client keeps `{auth_token, game_id}` per server and name
  (`ui/session_store.py`) and `run_multiplayer.py --name X` resumes it (`--no-resume` ignores it).

### D8. Determinism and tests at each boundary
- Engine: synchronous, seeded, no I/O. N-player tests run without a network.
- Protocol: round-trip tests for every message and for `Snapshot.to_dict/from_dict`.
- Server: in-process tests (the existing pattern) plus one test with two `RemoteDriver`s
  playing a few rounds headless.
- Replay: log `(seq, player_id, intent, args)` per game. Replaying the log on a fresh seeded
  engine must reproduce the final snapshot: a golden test for "SP and MP are the same rules".

---

## 4. Migration plan (each step lands green, behaviour-preserving unless stated)

| Phase | Work | Closes / unblocks | Size |
|---|---|---|---|
| **0. Unblock** | Fix the client event loop; add `RemoteDriver.submit` for the current `action` message; headless test. | VB-44 (partial) | S |
| **1. Explicit actor** | `ActionFactory.create(intent, actor_id=None, **kw)`; server accepts `intent` messages and builds actions from the seat. Keep `action` working. | D3 | S-M |
| **2. One engine** | (a) `player_ids` + N-player regen/game over in `TurnProcessor`; (b) `RoundScheduler` (one action per living seat; SP = one seat), server uses `TurnProcessor`; (c) N-player placement in `FloorManager`, delete MP `descend_floor`; (d) `player_died`/`run_ended` events, high score/vault/co-op scores as subscribers, content handlers in MP; (e) extract `Engine` from `Game`, `GameSession` uses it, delete `MultiplayerGameState` rules. | D1, D2, VB-55, VB-54 groundwork | L (5 slices) |
| **3. Protocol** (done; broken down in 4b) | `src/protocol/`, envelope with `v`/`seq`, server sends full per-viewer snapshots, client decodes `Snapshot.from_dict`; retire `get_state_dict` and the session baseline. | D4, D5, VB-26, VB-78 | M |
| **4. Client** (broken down in 4c) | `GameDriver`; `VeinbornApp` on a driver; `LocalDriver` for SP; RemoteDriver renders server snapshots; two-client playtest. | D6, VB-44 | M |
| **5. Later** | Drop/rejoin seat lifecycle (D7, closes VB-45) incl. the client persisting its auth token across a restart, fog per viewer + dev reveal switch (D4), deltas if measured, MP persistence/leaderboard viewer (VB-35, VB-54). | D7 | as needed |

Phase 0 and 1 are independent of the rest and safe to do now. Phase 2 is the core of the
plan and the riskiest; its slices each keep the full suite and the bot baselines green
(`tests/fuzz/README.md`: a single-player bot A/B before and after slice (a)-(c) should be
identical, since a party of one must behave exactly as before).

**Order rationale:** fixing the engine (2) before the protocol (3) means the protocol
describes the real model once, instead of being reshaped after. Doing the client (4) last
means it is built on the final contracts; Phase 0 gives a playable smoke test meanwhile.

### 4a. Phase 2 breakdown (re-measured 2026-11-13, after Phase 0+1)

Phases 0 and 1 are done (VB-88). Measuring the code again changes two assumptions in the
table above, so the slices below replace its Phase 2 cell.

**What the re-measure found**
- **No `player_ids` list is needed.** `GameContext.get_all_players()` / `get_alive_players()`
  already read every `EntityType.PLAYER` from `entities` (VB-23), and `GameState` keeps
  `.player` in that store. Slice (a) is therefore "stop reading `state.player` where a rule
  means *the party*", not "add a list".
- **The single-player assumption is narrower than "41 sites".** Outside `src/ui` there are 21
  `state.player`/`get_player()` reads. Party-rule sites that must change: `TurnProcessor`
  (log line, regen, `_check_game_over`, `_save_legacy_ore`, high score), `FloorManager`
  (`_place_player_at_stairs`, `_check_victory`, log lines). Fine as they are: `snapshot`
  (viewer default), `item_listing`, `highscore` (explicit `player=` already exists),
  `save_load` (single-player saves), `Game` (SP shell), `ActionFactory` (default actor).
- **MP's `descend_floor` differs from SP's in exactly three ways:** it repositions N players
  (`find_player_spawn_positions`), it skips high score/vault, and `clear_floor_entities` must
  keep every player (`clear_floor_entities(keep_ids=...)` already supports it).
- **`TurnProcessor` and the MP monster turn differ only by:** wanderers, `turn_ended`,
  `_check_game_over` (SP: the player is dead; MP: every player is dead).

**Slices (each lands green; SP bot A/B must stay identical through (a)-(c))**

| Slice | Change | Test gate | Size |
|---|---|---|---|
| **2a. Party-aware rules** | `TurnProcessor` regen over `get_alive_players()`, `_check_game_over` = no living player; `FloorManager` victory/placement take the party. End-of-run side effects (SP high score, Legacy Vault) moved to `core/run_end.py` (`SinglePlayerRunRecorder`). **Done (VB-89, VB-92):** the engine publishes `player_died` / `run_ended` / `turn_ended`; single-player subscribes the recorder, multiplayer subscribes co-op scoring. | suite; SP bot A/B identical; new unit tests with a 2-player `GameState` (one dies: game continues; both die: game over, one `run_ended`) | M |
| **2b. RoundScheduler** (done, VB-90) | `core/turn_scheduler.py`: `RoundScheduler(get_living_seats)` with `after_action(actor_id, took_turn) -> bool`. The server calls it instead of `actions_this_round >= actions_per_round`; a second action in the same round is rejected with "waiting for the party"; dead seats leave the owed set. SP uses the same scheduler with one seat. `actions_per_round` is deleted. Server round tick calls `TurnProcessor.process_turn` and `_process_monster_turn` is deleted (MP gains wanderers and `turn_ended`). | suite; SP A/B identical; scheduler unit tests (free action does not count, death mid-round, 1/2/4 seats, dropped seat); real-socket test: 2 clients, one acts twice and is refused | M |
| **2c. N-player floor change** (done, VB-91) | `FloorManager.descend_floor` places the whole party (spawn positions from `find_player_spawn_positions`), keeps all players when clearing (pass every player id as `keep_ids`; SP passes none today); delete `MultiplayerGameState.descend_floor`/`_reposition`/`_spawn_floor_entities`/`_clear_non_player_entities`/`_get_victory_floor`; MP gets `floor_changed`. Descend stays "any one player on the stairs moves the whole party" (existing MP rule); revisit only if you rule otherwise. | suite; SP A/B identical; MP descend test on 3 players; `floor_changed` seen by a subscriber | S-M |
| **2d. Events and handlers** (done, VB-92) | `player_died` / `run_ended` published by the engine; `GameSession` subscribes `_record_scores` (co-op leaderboard); `game_started` published; `install_event_handlers` run for MP (closes VB-55; VB-54 persistence stays separate). | suite; achievement fires in a 2-client test; no double scoring | S-M |
| **2e. Engine extraction** (done, VB-93) | `core/engine.py`: owns state, context, `ActionFactory`, `TurnProcessor`, `FloorManager`, scheduler, event bus; `process(actor_id, intent, **args) -> Result`. `Game` becomes a thin SP shell around it (save/load, restart, quick_use), `GameSession` wraps it (seats, lock, transport). `MultiplayerGameState` keeps seat/slot bookkeeping only; its rules are gone. | suite; SP A/B identical; MP real-socket tests unchanged | L |

**Order and dependencies:** 2a -> 2b -> 2c are sequential (each needs the party-aware rules
before it). 2d can start after 2a (its seam is created there). 2e last, since it only moves
code that 2a-2d have already unified. Rough total: 2-3 working days.

**Where it can go wrong**
- *2a SP drift:* the `run_ended` indirection must publish at the same point `_check_game_over`
  ran, or the SP high score/vault order of side effects changes. A/B covers outcomes, not
  side-effect order, so add a test that SP death still writes exactly one score and one vault record.
- *2b round semantics in SP:* with one seat, `after_action` must return True after every
  turn-consuming action. The A/B detects any difference.
- *2c fairness of "anyone descends":* a player rushing the stairs drags the party down. This is
  today's behaviour; not a regression, but flagged here because the round ruling makes MP
  slower and more deliberate.
- *Session lock:* the scheduler lives inside the existing `GameSession._lock` section, so no new
  concurrency rules.

### 4b. Phase 3 breakdown (re-measured 2026-11-14, after Phase 2)

**What the measurement found**
- **Sizes today (4 players, floor 1):** `get_state_dict` 13.4 KB; a viewer's `Snapshot` 7.9 KB (map 2.0 KB,
  24 entities 5.2 KB). Per action each recipient gets one message, so full snapshots cost ~8 KB x players per
  action: still nothing at human action rates. Deltas are not needed to start.
- **The wire format has almost no consumers.** Outside the server, only `MultiplayerClient` (decodes
  `state`/`delta`, forwards to `on_state_update`, which nothing in `src` listens to) and the dev
  `test_client.py` read it. Tests that touch it: `test_state_delta.py` (69 refs, deleted with the feature),
  and ~40 refs across 7 other files. No widget reads it. So the format can change without a compatibility layer.
- **The snapshot is already per viewer** (`build_snapshot(state, viewer)`, used for the sidebar numbers
  today). Per-viewer sending is the missing piece; it is also the seam fog of war needs later.
- **The client imports the server package** (`ui/multiplayer_client.py`: `server.messages`,
  `server.state_delta`): 15 files import `server.messages` in total.
- **What a snapshot lacks for a party client:** who is in the party (names, class, alive, connected),
  and round info (`round_number`, `waiting_on`). Other players already appear as `EntityView`s, but
  without names of seats. These two belong in the snapshot, not beside it.
- **Dead viewers:** a dead guest's entity is purged from `state.entities` (VB-16) but the slot keeps the
  object, so `build_snapshot(viewer=slot.player_entity)` still works for a spectator.

**Slices (each lands green; MP only, so the SP bot A/B is not needed, except 3b which touches `core/snapshot.py`: TUI tests cover it)**

| Slice | Change | Test gate | Size |
|---|---|---|---|
| **3a. Protocol package** (done, VB-95) | `src/protocol/` with `messages.py` moved from `server/` (`Message` gets `v` and optional `seq`; `PROTOCOL_VERSION = 1`); both sides refuse a version mismatch at auth (a peer that sends no `v` reads as 0); `server/messages.py` deleted, 12 importers updated. `ui/multiplayer_client.py` still imports `server.state_delta` until 3c/3d remove it. | suite; version-mismatch tests (server and client side) | S |
| **3b. Snapshot as a wire model** (done, VB-96) | `Snapshot.from_dict` (and the nested views); `PartyMemberView` (player_id, name, class, entity_id, alive, connected) and `RoundView` (number, waiting_on) added to `Snapshot` as optional fields (empty in single-player); `Engine.snapshot(viewer_id)`. | round-trip test: live state -> `to_dict` -> JSON -> `from_dict` equals the original, for SP and a 3-player party incl. a dead viewer; widget tests unchanged | S-M |
| **3c. Per-viewer snapshots on the wire** (done, VB-97) | New messages `snapshot` (`seq` per game, one per recipient, built by `GameSession` with party + round filled) and `lobby` (before start); `broadcast_game_state` sends each session its own; reconnect sends only to that viewer; `get_snapshot` request for resync; `MultiplayerClient` decodes with `Snapshot.from_dict`, keeps the latest by `seq`, drops older ones; `test_client.py` prints a snapshot; the real-socket `_Client` mirror is rewritten. | real-socket tests: two clients each see their own inventory, the same monsters, `waiting_on`, reconnect gets only a snapshot to the returning viewer, an out-of-order `seq` is ignored | M-L |
| **3d. Delete the delta path** (done, VB-98) | Remove `state_delta.py` and its tests, `MultiplayerGameState.get_state_dict/to_dict`, `GameSession.get_state_dict`, `last_state`, `use_delta_compression`, `reset_state_tracking`, and the `state`/`delta` message types. Closes VB-26 (replaced) and VB-78 (monsters/map now come from the snapshot). | suite; grep shows no references | S |

**Order:** 3a -> 3b -> 3c -> 3d. 3a and 3b are independent and could run in either order; 3c needs both.
Rough total: 1.5-2 working days.

**Deliberately not in Phase 3**
- *Fog of war.* `core/perception.FogOfWar` has no per-viewer explored memory yet, and `Tile.explored`
  is per tile (shared). Fog needs one visibility record per viewer per floor, and it changes what players
  see, so it ships alone (plan phase 5) behind `build_snapshot`, which 3c makes per-viewer. The dev
  reveal switch lands with it.
- *Deltas.* Only if a measurement shows a need, as snapshot diffs with `base_seq`.
- *Spectator view for dead players* (follow a living ally): a viewer choice in `GameSession`, later.

**Where it can go wrong**
- *3c test churn:* the real-socket `_Client` mirrors the client's decoding; rewrite it to use the real
  `MultiplayerClient` decoder (or share one decode function) so the test and the client cannot drift again.
- *Message ordering:* snapshots are built after the action under the session lock, then sent per
  recipient outside it; `seq` is taken inside the lock so a slow send can never reorder state.
- *Hidden consumers:* external scripts using `test_client.py`'s output; none are tracked. Flag in the
  3c commit message.

### 4c. Phase 4 breakdown (re-measured 2026-11-13, after Phase 3 and VB-94)

**What the measurement found**
- **The widgets are not snapshot-driven yet, only snapshot-shaped.** `MapWidget`, `Sidebar`, `StatusBar` and
  `InventoryWidget` take `game_state=` and call `build_snapshot(self.game_state)` themselves; `MessageLog`
  reads `game_state.messages`. A remote client has no `GameState`, so the widgets need a snapshot source.
- **`VeinbornApp` holds a `Game`:** ~48 `self.game` references; `compose()` always `start_new_game()`s; key
  handlers call `game.handle_player_action`, `quick_use`, `quick_drop`; `EquipmentScreen(self.game)`.
- **Some "UI" is rules in `Game`:** `quick_use` (pick the best healing item) and `quick_drop` (least useful
  item) choose server-side state, so a remote client cannot run them. They move into the factory: `use` /
  `drop` with no `item_id` choose the item.
- **Read-only screens need item detail the snapshot lacks:** the equipment screen needs each item's gear
  slot and bonus (`core.equipment.equipment_listing` reads live `Player`s); the ground listing needs
  `item_type` on map items. These go into `ItemView` / `EntityView`, which changes the wire, so
  `PROTOCOL_VERSION` becomes 2.
- **The client side is ready:** `MultiplayerClient.submit`/`request_snapshot`, latest snapshot by `seq`,
  in-loop connect (VB-88, VB-97).
- **No pilot test drove the single-player game screen** (only the equipment screen and the MP connect
  test). 4a's listing change broke the inventory and look keys with the suite still green, so the
  characterisation test (`tests/ui/test_game_screen.py`: move, wait, status, inventory, look, quick use/drop)
  landed in 4a and is 4b's gate.

**Slices**

| Slice | Change | Test gate | Size |
|---|---|---|---|
| **4a. Rules and item detail** (VB-99) | Factory: `use`/`drop` without `item_id` pick the item (messages as today); `Game.quick_use/quick_drop` call them. `ItemView` gains `slot`/`bonus`, `EntityView` gains `item_type`; `equipment_listing`, `inventory_messages`, `ground_messages` also accept views. `PROTOCOL_VERSION = 2`. | suite; SP bot A/B identical (factory change); round-trip test covers the new fields | S-M |
| **4b. Driver, local** (VB-100) | `ui/driver.py`: `GameDriver` (D6) and `LocalDriver(Game)`. Widgets take a snapshot getter; `EquipmentScreen` takes the driver; `VeinbornApp` builds a `LocalDriver` and key bindings call `driver.submit(intent, ...)`. | `tests/ui/test_game_screen.py` + `test_equipment_screen.py` green before and after | M |
| **4c. Driver, remote** (VB-101, done) | `RemoteDriver(MultiplayerClient)`: snapshot = latest received, its log = the server's new lines (told apart by `Snapshot.message_count`) merged with local notes; `submit` = `client.act`, which sends the intent with a `rid` and waits for its `intent_result` (refused + reason, or accepted after the snapshot). App MP mode: no local `Game`; the status bar shows the lobby (game id, seats) and `R` readies up, then the round (`waiting on ...`) and a spectating notice; allies are drawn on the map (they were missing); save/load/restart refused. `test_client.py` sends intents. *Moved to phase 5:* persisting the auth token across a client restart needs the D7 rejoin lifecycle (today a fresh process resumes its auth session but has no way back into its game). | `tests/ui/test_remote_app.py` (real server: lobby, ready, move, refusal, notes, save refused); `act` real-socket test | M |
| **4d. Two clients** (VB-102, done) | `tests/ui/test_two_clients.py`: two apps on one server; Bob joins with the id from Alice's lobby line, both ready, each sees the other's `@`, the round waits on the partner, a second action is refused with the reason in the log. Found on the way: `RoundView.waiting_on` was id-ordered (seat ids are random), now seat order; a seat that left or timed out still held up the round forever (`RoundScheduler.drop` had no caller), so the drop half of D7 landed here (see D7). Playtest guide: `docs/MULTIPLAYER_PLAYTEST.md`. | the pilot test (stable over 15 repeats); then a human playtest | S |

**Order:** 4a -> 4b -> 4c -> 4d. 4a first so 4b's widgets and screens are written against views only.

---

## 5. Risks and how the plan handles them
- **Single-player regressions during Phase 2.** Party-of-one equivalence is checked with the
  seeded bot runs (identical results expected), not just unit tests.
- **`state.player` blast radius** (41 core sites, ~437 test references to `.player`). Keep
  the property as "first player" until the last slice; convert core call sites first, tests last.
- **Scope creep into design-doc features** (tactical mode, pause, NATS, Postgres). Out of
  scope until two humans can play; the seams above (scheduler, seats, protocol envelope)
  are where they would plug in later.
- **Fairness of the round model** is a design choice, not a bug: flagged as **(Scott)** in D2.

## 6. Rulings and open questions

Ruled by Scott, 2026-11-13:
1. **Round:** one action per living player per round (D2). Supersedes ADR-016's "4 actions, anyone".
2. **Disconnect:** wait a grace period, then drop; a dropped player can rejoin the party (D7).
3. **Fog of war:** on by default, with a development reveal switch (D4).

Confirmed by Scott, 2026-11-13 (later):
4. **ADRs:** ADR-011/013/014 Deferred, ADR-016 Superseded, plan recorded as ADR-020 (done in `DECISIONS.md`).
5. **Round quota is strict per player:** each living player gets exactly one turn-consuming action per round.
6. **Idle players:** deferred. When it matters, use a per-round timer that auto-waits for the idle seat
   (`config.action_timeout = 60` and `idle_timeout = 300` exist but nothing reads them; `Session.is_idle` is never called).
7. **Rejoin identity:** same identity. The auth token resumes the seat; with no token, a name match is allowed
   only while exactly one dropped seat has that name. Auth is in-memory and name-only today, so the client
   should persist its token.
