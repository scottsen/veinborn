# Veinborn Project Review

**Date:** 2026-04-17  
**Reviewer:** Codex  
**Scope:** Repository docs, code quality, architecture, testing posture, and next-step recommendations

**Follow-up (2026-08-04):** This review's Priority 1 multiplayer-correctness fixes (`GameSession`/`GameContext`, `WaitAction`) shipped same-day and were re-verified as clean. A follow-up code review + bug hunt on 2026-08-04 found new critical issues this review didn't cover (a floor-11+ crash, and confirmed multiplayer reconnection is still non-functional). All findings from both reviews are now tracked in `TASKS.md` (`tt list --project veinborn`) — treat that as the current source of truth for open issues, not this document.

## Executive Summary

Veinborn has a real game codebase with a credible architecture foundation: `GameState` + `GameContext` + action/system separation is a good shape for continued development, and representative synchronous tests still pass. The main problem is not that the project lacks substance. The main problem is that the documentation now overstates accuracy and implementation status, especially around test health, multiplayer completeness, and current controls/UI behavior.

Single-player core quality is moderate-to-good. Multiplayer quality is materially lower and currently should be treated as experimental, not "Phase 2 complete." Documentation quality is mixed: there is a lot of it, but too much of it is stale, redundant, or internally contradictory.

## Review Method

- Read top-level docs, status docs, architecture docs, testing docs, and server docs.
- Compared doc claims against current code in `src/core/`, `src/ui/`, and `src/server/`.
- Ran a representative synchronous test subset:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/unit/actions/test_move_action.py tests/unit/test_config_loader.py tests/unit/test_entity_loader.py tests/unit/test_save_load.py tests/unit/server/test_messages.py -q -o addopts=''`
  - Result: `127 passed, 1 warning`
- Collected broader suite metadata with plugin autoload disabled:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ --collect-only -q`
  - Result: `917 tests collected, 5 collection errors`

## Highest-Signal Findings

### 1. Documentation is not currently trustworthy as a source of truth

Multiple active docs still claim exact counts like `1063 tests passing (100%)` and describe `PROJECT_STATUS.md` as "100% accurate", but current test collection does not support that claim. See:

- [docs/START_HERE.md](/home/scottsen/src/projects/veinborn/docs/START_HERE.md:22)
- [docs/INDEX.md](/home/scottsen/src/projects/veinborn/docs/INDEX.md:35)
- [README.md](/home/scottsen/src/projects/veinborn/README.md:198)

Current reality:

- `pytest.ini` enables `--strict-markers` but does not register an `asyncio` marker, which breaks collection of async server tests. See [pytest.ini](/home/scottsen/src/projects/veinborn/pytest.ini:11) and [pytest.ini](/home/scottsen/src/projects/veinborn/pytest.ini:17).
- With plugin autoload disabled to avoid sandbox/plugin socket issues, the suite stops at `917 collected, 5 errors` due to missing `asyncio` marker configuration.

### 2. Multiplayer is documented as complete, but the implementation still has critical breakpoints

Two concrete issues make the "Phase 2 complete" claim too strong:

- `GameSession.process_action()` executes actions against a raw `GameState`, not the `GameContext` required by the action API. See [src/server/game_session.py](/home/scottsen/src/projects/veinborn/src/server/game_session.py:396).
- Disconnected-player fallback imports `core.actions.wait_action.WaitAction`, but no `wait_action.py` exists under `src/core/actions/`. See [src/server/game_session.py](/home/scottsen/src/projects/veinborn/src/server/game_session.py:444).

This means multiplayer action handling is not aligned with the single-player action architecture, and at least one reconnection/disconnected-player path is broken by construction.

### 3. Player-facing controls docs are out of sync with the live Textual app

Current UI bindings are:

- `s` = survey
- `i` = show inventory
- `w` = equip
- `g` = pickup
- `.`/`space` = wait
- `>` = descend
- `c` = chat

See [src/ui/textual/app.py](/home/scottsen/src/projects/veinborn/src/ui/textual/app.py:125).

But active player docs still say:

- `m` = mine
- `c` = craft
- `e` = equip

See [QUICKSTART.md](/home/scottsen/src/projects/veinborn/QUICKSTART.md:37) and [HOW_TO_PLAY.md](/home/scottsen/src/projects/veinborn/HOW_TO_PLAY.md:39).

At minimum, the docs need to explain that mining is currently bump-to-mine and that `c` is no longer a single-player craft binding in the current UI.

### 4. The architecture is better than the docs suggest, but the architecture docs are themselves stale

The codebase has already moved beyond some architecture docs:

- `Game` is no longer just a simple MVP-only controller; it owns event bus, telemetry, Lua runtime, spawner, turn processor, floor manager, and save/load orchestration.
- `EntityLoader`, action factory, event bus, telemetry, and multiplayer modules exist.

But the architecture docs still frame the repo as MVP-only and repeatedly point to `docs/future-multiplayer/`, which does not exist in this repo. See:

- [docs/architecture/00_ARCHITECTURE_OVERVIEW.md](/home/scottsen/src/projects/veinborn/docs/architecture/00_ARCHITECTURE_OVERVIEW.md:10)
- [docs/architecture/README.md](/home/scottsen/src/projects/veinborn/docs/architecture/README.md:16)

### 5. There are signs of documentation process debt, not just stale content

The repo contains documentation about documentation consolidation, plus references to archive locations outside the repo:

- [docs/INDEX.md](/home/scottsen/src/projects/veinborn/docs/INDEX.md:91)
- `docs/future-multiplayer/` referenced in multiple docs, but absent from the working tree
- active docs describe archive paths under `~/Archive/...`, which are not portable for contributors

This makes the documentation system fragile and repo-external.

## Documentation Review

### Accurate or Mostly Useful

- `docs/development/README.md`: useful as an index, though some linked docs are incomplete.
- `docs/architecture/ARCHITECTURAL_ASSESSMENT.md`: more useful than the overview docs because it discusses actual patterns and tradeoffs, even if some specifics are stale.
- `src/server/README.md`: useful as a historical/protocol sketch, but status sections are outdated.

### Needs Update for Accuracy

- `README.md`
  - stale metrics
  - stale multiplayer status
  - references missing `MULTIPLAYER_PROGRESS.md`
- `QUICKSTART.md`
  - wrong controls and interaction flow
- `HOW_TO_PLAY.md`
  - wrong controls and likely wrong forge/crafting interaction description
- `docs/START_HERE.md`
  - still claims authoritative current status with outdated test counts and missing-file references
- `docs/STATUS_DASHBOARD.md`
  - stale test counts and status claims
- `docs/PROJECT_STATUS.md`
  - claims "100% accurate" but current suite evidence does not support that
- `docs/MVP_CURRENT_FOCUS.md`
  - mixes stale status claims with still-useful backlog items
- `docs/MVP_ROADMAP.md`
  - internally contradictory: says multiplayer is both current/future and already complete
- `tests/README.md`
  - substantially obsolete relative to actual test tree and volume
- `docs/architecture/00_ARCHITECTURE_OVERVIEW.md`
  - outdated phase framing and project structure
- `docs/architecture/README.md`
  - repeatedly points to non-existent `future-multiplayer/`

### Should Be Archived or Moved Out of the Active Path

These are not harmful as historical records, but they should not sit in the active navigation path:

- `docs/DOCUMENTATION_CONSOLIDATION_2026-01-13.md`
- `docs/CONSOLIDATION_ANALYSIS.md`
- `docs/development/CODE_REVIEW_AND_REFACTORING_PLAN.md`
  - useful historically, but no longer reflects the current code shape
- `tests/README.md`
  - either rewrite completely or archive and replace
- `docs/architecture/00_ARCHITECTURE_OVERVIEW.md`
  - archive after replacing with a current overview

### Should Be Consolidated

Status/planning docs should be reduced to a smaller, stricter set:

- Keep one canonical status document: `docs/PROJECT_STATUS.md`
- Keep one short dashboard: `docs/STATUS_DASHBOARD.md`
- Keep one current-work document: `docs/MVP_CURRENT_FOCUS.md`
- Merge or delete overlapping status prose from:
  - `README.md`
  - `docs/START_HERE.md`
  - `docs/INDEX.md`
  - `docs/MVP_ROADMAP.md`

## Code Quality Review

### Strengths

- Clear architectural intent in the single-player core.
- Good modular decomposition in many places:
  - `GameState`
  - `GameContext`
  - action classes
  - `TurnProcessor`
  - `FloorManager`
  - `EntityLoader`
- The project is test-heavy by game-project standards.
- Representative sync tests pass cleanly.
- Data-driven content approach is already in place for important areas.

### Weaknesses

- Multiplayer/server code is less integrated and appears less exercised than the single-player core.
- The codebase still carries older patterns in parallel with newer ones:
  - constants + YAML
  - factory methods + entity loader
  - old docs + new architecture
- Large modules remain:
  - `src/core/game.py`
  - `src/core/world.py`
  - `src/server/game_session.py`
  - `src/server/websocket_server.py`
  - `src/ui/textual/app.py`
- Some doc and warning polish issues indicate insufficient maintenance loops:
  - deprecation warning path replacement is a no-op in [src/core/config/user_config.py](/home/scottsen/src/projects/veinborn/src/core/config/user_config.py:95)

### Quality Rating

- Single-player core: `7.5/10`
- Multiplayer/server: `4.5/10`
- Test posture: `6/10`
- Documentation quality: `4/10`
- Overall maintainability: `6.5/10`

## Architecture Review

### What Is Working Well

The core architecture is directionally sound:

- `GameState` centralizes mutable state.
- `GameContext` gives a controlled access layer that helps testing and future scripting/multiplayer.
- Actions are first-class and serializable.
- Systems are separated from UI and from the main `Game` loop.
- Entity/content loading is moving in a data-driven direction.

That is a respectable design for a turn-based roguelike.

### Where the Design Is Straining

- `Game` still acts as a large composition root plus runtime coordinator plus integration point for Lua/events/telemetry.
- Multiplayer duplicates or bypasses some of the single-player architectural contract instead of reusing it cleanly.
- The documentation still describes earlier architecture snapshots, which makes it harder for new contributors to understand the current system.

### Architectural Conclusion

The single-player architecture is good enough to continue building on. The right move is not a rewrite. The right move is to:

1. stabilize test/config correctness,
2. repair multiplayer integration against the existing action/context model,
3. reduce documentation drift,
4. keep extracting focused services from large files as features evolve.

## Is Continued Development Well Documented?

Partially.

There is plenty of documentation, but it does not currently provide a reliable, low-friction development map. A new contributor will hit these problems quickly:

- conflicting status claims
- broken/missing references
- outdated controls and workflows
- architecture guides describing repo states that no longer exist

The backlog itself is documented. The trustworthy path to execute that backlog is not.

## Recommended Next Steps

### Priority 0: Restore factual accuracy

1. Fix test metadata:
   - add/register the `asyncio` marker
   - ensure async test dependencies/config are declared
   - rerun collection and update counts from real output only
2. Remove all "100% accurate" and exact passing-count claims until revalidated.
3. Remove or replace all references to:
   - `MULTIPLAYER_PROGRESS.md`
   - `docs/future-multiplayer/`
   - repo-external `~/Archive/...` paths

### Priority 1: Repair multiplayer correctness

1. Fix `GameSession` to execute actions against `GameContext`, not raw `GameState`.
2. Implement or remove the missing `WaitAction` path.
3. Re-run the server test suite after fixing pytest async configuration.
4. Downgrade multiplayer status in docs until the above passes.

### Priority 2: Update the player/developer entry docs

1. Rewrite controls in:
   - `README.md`
   - `QUICKSTART.md`
   - `HOW_TO_PLAY.md`
2. Clarify actual current interactions:
   - mining
   - equipping
   - chat
   - crafting flow
3. Rewrite `docs/START_HERE.md` to be an onboarding doc, not a status report.

### Priority 3: Consolidate docs

1. Replace `docs/architecture/00_ARCHITECTURE_OVERVIEW.md` with a current overview.
2. Rewrite `tests/README.md` from scratch or archive it.
3. Move process-history docs into `docs/.archived/`.
4. Keep `docs/INDEX.md` as a navigator only, not a truth-claim document.

### Priority 4: Continue development on the actual product

After the above, the best development track is:

1. single-player UX/playability polish
2. content expansion
3. multiplayer stabilization
4. docs maintenance tied to shipped behavior, not planned behavior

## Suggested Documentation Model

Use this structure:

- `README.md`: short project overview + exact run/install basics + links
- `docs/START_HERE.md`: contributor onboarding only
- `docs/PROJECT_STATUS.md`: canonical status and validated evidence
- `docs/MVP_CURRENT_FOCUS.md`: active backlog
- `docs/architecture/00_ARCHITECTURE_OVERVIEW.md`: current architecture only
- `docs/.archived/`: historical plans, consolidation writeups, superseded designs

Each of those should declare:

- last verified date
- verification method
- whether it is authoritative or historical

## Bottom Line

This project is worth continuing. The codebase has enough architectural discipline and test investment to support further work. The immediate blocker is not code collapse. It is trust collapse between docs and implementation. Fix that first, then continue shipping against the current architecture instead of the historical one.
