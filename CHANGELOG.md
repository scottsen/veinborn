# Changelog

All notable changes to the Veinborn project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Entity Rendering**: Forges now display correctly with '&' symbol (were invisible but blocking)
- **Entity Rendering**: Items and NPCs now render properly instead of falling through to terrain

### Changed
- **Mining Mechanics**: Bumping ore veins now starts mining automatically (consistent with bump-to-attack combat)
- **Keybindings**: Removed 'M' key for mining (use bump-to-mine instead)
- **UI Controls**: Updated sidebar hint from "M: Mine Ore" to "Bump ore to mine"

### Added
- **Test Suite**: Comprehensive entity rendering tests (`tests/unit/ui/test_entity_rendering.py`)
- **Test Coverage**: Parametrized test checking all EntityType values render correctly
- **Test Coverage**: Forge visibility regression test
- **Test Coverage**: Ore vein color verification tests
- **Test Coverage**: Forge blocking movement test
- **Documentation**: Entity rendering improvements guide (`docs/development/ENTITY_RENDERING_IMPROVEMENTS.md`)
- **Documentation**: Data-driven rendering architecture proposal (`docs/development/DATA_DRIVEN_RENDERING_POC.md`)
- **Documentation**: Prevention strategy summary (`docs/development/PREVENTION_SUMMARY.md`)
- **Architecture**: Entity Display Properties (`display_symbol`, `display_color`) - centralized rendering logic in Entity base class

### Refactored - Architecture Improvements (Phase 1: divine-centaur-0113)
- **Entity Base Class** (`entity.py`):
  - Added `display_symbol` property - centralized symbol rendering logic (30 lines)
  - Added `display_color` property - centralized color rendering logic (45 lines)
  - Properties check stats dict first (future YAML data), fall back to type-specific defaults
  - Enables future data-driven rendering without code changes

- **MapWidget** (`map_widget.py`):
  - Simplified `_render_cell()` from 43 lines to 28 lines (35% reduction)
  - Removed type-specific rendering methods (`_get_ore_vein_style()`, `_get_forge_style()`)
  - Removed hardcoded ORE_STYLES constant
  - All entity rendering now uses unified `entity.display_symbol` and `entity.display_color` properties
  - Single rendering path for all entity types (reduced from 6 separate code paths)

- **World Generation** (`world.py` - Phase 1):
  - Refactored `find_ore_vein_positions()` - reduced cyclomatic complexity from 14 to ~5
  - Reduced nesting depth from 7 to 5 (closer to target of 4)
  - Extracted helper methods:
    - `_is_adjacent_to_wall()` - checks wall adjacency (eliminates nested loops)
    - `_is_valid_ore_position()` - validates ore spawn location
    - `_get_ore_spawn_probability()` - centralizes config access
  - Improved readability with early returns and clearer logic flow

- **Game Controller** (`game.py` - Phase 1):
  - Refactored `start_new_game()` from 131 lines to 57 lines (56% reduction!)
  - Extracted focused helper methods (each < 30 lines):
    - `_create_player()` - player entity creation (28 lines)
    - `_initialize_game_state()` - state and context setup (16 lines)
    - `_add_legacy_ore()` - legacy ore inventory handling (18 lines)
    - `_spawn_entities()` - entity spawning orchestration (12 lines)
    - `_display_welcome_messages()` - UI messaging (14 lines)
  - Each helper is independently testable and single-responsibility

### Refactored - Complexity Reduction (Phase 2: spectral-kraken-0113)
- **World Generation** (`world.py` - Phase 2):
  - Reduced complexity issues from 7 to 3 (4 issues resolved)
  - Added `_find_first_walkable_in_room()` helper - eliminates nested loops (13 lines)
  - Refactored `find_player_spawn_positions()` - nesting depth 6→4 (33% reduction)
  - Refactored `find_monster_positions()` - nesting depth 6→4 (33% reduction)
  - Added `_create_l_corridor()` helper - extracts corridor creation logic (24 lines)
  - Refactored `connect_rooms()` - nesting depth 5→3 using guard clauses
  - Added `_set_floor_tile()` helper - bounds checking in one place (4 lines)
  - Refactored `apply_to_map()` - nesting depth 5→4

- **Game Controller** (`game.py` - Phase 2):
  - Reduced complexity issues from 11 to 6 (5 issues resolved)
  - Removed 5 unused imports (PLAYER_STARTING_HP, PLAYER_STARTING_ATTACK, PLAYER_STARTING_DEFENSE, DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT)
  - Added `_process_action_outcome()` helper - handles events, messages, floor transitions (30 lines)
  - Refactored `handle_player_action()` from 74 lines to 51 lines (31% reduction)
  - Extracted outcome processing into focused helper with single responsibility

- **Code Quality Metrics**:
  - world.py: `find_player_spawn_positions` nesting 6→4, `find_monster_positions` nesting 6→4
  - world.py: `connect_rooms` nesting 5→3, `apply_to_map` nesting 5→4
  - game.py: `handle_player_action` 74→51 lines (31% reduction)
  - Added 4 new helper methods, improved maintainability
  - All helper methods < 30 lines, single responsibility

- **Import Cleanup**:
  - `game.py`: Removed 5 unused constant imports (cleanup across 2 phases)
  - `move_action.py`: Removed unused ActionResult import (phase 1)
  - Kept imports required by deprecated factory methods (backward compatibility)

### Technical Details
- `map_widget.py`: Added rendering cases for FORGE, ITEM, and NPC entity types
- `move_action.py`: Added ore vein collision handler that redirects to MineAction
- Updated move action tests to reflect new bump-to-mine behavior
- Tests now enforce that all entity types have visible rendering symbols
- **Test Results - Phase 1**: 116 critical unit tests passing (entities, UI, actions)
- **Test Results - Phase 2**: 115 core tests verified (63 entity/move tests + 52 game context tests)
- **Code Quality**: Reduced complexity issues from 18 to 9 across 2 files (50% reduction)
- **Maintainability**: Extracted 12 new helper methods total (8 phase 1, 4 phase 2)
- **Lines of Code - Phase 1**: Net reduction of ~70 lines through consolidation
- **Lines of Code - Phase 2**: world.py +29 lines (helpers), game.py +3 lines (helpers), improved structure

### Architecture Impact
- **Single Responsibility**: Entity rendering logic moved from UI layer to domain model
- **Open/Closed**: New entity types automatically get rendering without MapWidget changes
- **Future-Ready**: Display properties prepared for YAML-driven configuration
- **Test Coverage**: Parametrized tests ensure all EntityType values handled
- **Forcing Function**: Test suite catches missing entity rendering automatically

### Future Enhancements

## [0.4.0] - 2025-12-10

### Complete Infrastructure Transition: Brogue → Veinborn

**BREAKING CHANGES** (with backward compatibility):
This release completes the full transition from "Brogue" to "Veinborn" branding. All changes include backward compatibility with deprecation warnings. Deprecated features will be removed in v0.5.0.

#### Changed
- **GitHub Repository**: Renamed from `scottsen/brogue` to `scottsen/veinborn` (automatic redirect in place)
- **Local Directory**: Project directory renamed from `brogue/` to `veinborn/`
- **Server Class**: `BrogueServer` → `VeinbornServer` (deprecated alias provided)
- **Environment Variables**: `BROGUE_*` → `VEINBORN_*` (old names supported with warnings)
- **Config Files**: `~/.broguerc` → `~/.veinbornrc` (old file loaded with warning)
- **Documentation**: Updated all docs to reflect Veinborn branding
- **Test Files**: All tests updated to use new naming conventions

#### Added
- **MIGRATION.md**: Comprehensive migration guide for users and developers
- Backward compatibility layer for all renamed components
- Deprecation warnings for legacy names (scheduled removal in v0.5.0)
- TIA project registry updated with complete transition notes

#### Infrastructure
- Git remote URL updated to new repository name
- All documentation titles updated (MULTIPLAYER_PROGRESS.md, GAPS_AND_NEXT_STEPS.md)
- Test suite updated to use `VeinbornServer` and `VEINBORN_*` variables
- Config system enhanced with legacy path support

#### Technical Details
- Server class provides `BrogueServer` as deprecated alias inheriting from `VeinbornServer`
- Environment variable fallback with `_get_env_with_fallback()` helper
- Config file loader checks new paths first, falls back to legacy with warnings
- All changes maintain 100% backward compatibility for existing users

**Migration**: See MIGRATION.md for complete guide. TL;DR:
- GitHub: Automatic redirect (no action needed)
- CLI: `pip install veinborn` (replaces `brogue`)
- Config: `mv ~/.broguerc ~/.veinbornrc` (optional, auto-loaded with warning)
- Code: Update imports to `VeinbornServer` (old name works with warning)

## [0.3.0] - 2025-11-14

### Phase 3: Core Features Complete

#### Added
- **Personal Loot System**: Each player receives independent loot rolls from monsters
  - Direct-to-inventory distribution
  - No competition for drops in co-op mode
  - Backward compatible with single-player mode
- **Reconnection Handling**: Players can disconnect and reconnect without losing progress (#32)
  - 2-minute disconnect timeout with character preservation
  - Full state sync on reconnection
  - Party notifications for connect/disconnect events
- **Multiplayer Chat System**: Party communication system (#34)
  - Real-time chat messages between players
  - System notifications for important events
- **Delta Compression**: Network optimization for state updates
  - 3-10x bandwidth reduction for action updates
  - Transparent delta computation and application
  - Compression metrics logging
- **Class Selection System**: Players choose character classes on join
  - Four classes: Warrior, Mage, Rogue, Healer
  - Class-specific stats and abilities
  - Balanced starting attributes per class

#### Improved
- Test coverage for edge cases and multiplayer scenarios (#35)
- Network performance with delta compression
- Player experience with reconnection support

## [0.2.0] - 2025-11-13

### Phase 2: Multiplayer Foundation Complete 🎉

#### Added
- **Multiplayer Infrastructure**: Full WebSocket-based multiplayer system (#31)
  - WebSocket server with async/await architecture
  - Token-based authentication and session management
  - Game session management (create, join, leave)
  - Support for 2+ concurrent players
  - Real-time state synchronization
  - ~2,400 lines of new code across 11 files
- **Turn System**: "4 actions per round, anyone can take them" (#26)
  - Hybrid turn-based system
  - Round tracking and action counting
  - Flexible action allocation among players
- **Dungeon Generation for Multiplayer**: Shared dungeon with distributed spawning (#27)
  - BSP-based procedural generation for multiplayer
  - Multiple player spawn positions in different rooms
  - Seeded generation for consistency
  - `find_player_spawn_positions()` method in Map class
- **Monster AI Integration**: Intelligent targeting in multiplayer (#28)
  - Monsters act after player action rounds
  - Nearest-player targeting algorithm
  - Smart handling of player death
  - Integration with existing AI behavior system
- **Test Client**: Interactive CLI client for multiplayer testing
  - Commands: create, join, ready, move, chat
  - Real-time state display
  - Direction mapping for movement

#### Changed
- Updated documentation to reflect Phase 2 completion (#29, #30)
- Monster AI now targets nearest player instead of single player
- Player spawning logic updated for distributed starts
- GameSession wired to AISystem for monster behavior

#### Technical
- Added `websockets>=12.0` dependency
- Server-authoritative architecture
- Type-safe message protocol with Pydantic
- Comprehensive error handling and timeouts
- Full async/await throughout

## [0.1.0] - 2025-11-06

### Phase 1: MVP Complete (98%)

#### Added
- **Legacy Vault System**: Meta-progression across runs (#20)
  - Preserves ore with purity 80+ when player dies
  - Dual victory paths: Pure Victory vs Legacy Victory
  - Vault UI and integration
  - Both victory types tracked separately
- **Lua Event System**: Extensible event-driven architecture (Phase 3)
  - EventBus with pub/sub pattern
  - Event handlers and listeners
  - GameContext API for Lua integration
  - Comprehensive test suite (#19)
- **Lua AI Behaviors**: Custom AI behavior system
  - AI behavior registry and Lua wrapper
  - Example behaviors: Berserker, Sniper, Summoner
  - Integration with AISystem
  - Helper methods in GameContext API
- **AI Behavior System**: Five distinct behavior types
  - Aggressive, Defensive, Passive, Coward, Guard
  - Data-driven configuration
  - Behavior-based monster spawning
- **Equipment Upgrade Intelligence**: Smart bot decision-making
  - Stat-based upgrade detection
  - Equipment comparison logic
  - Integration with bot testing framework
- **Formula System**: Centralized game balance
  - Damage calculations
  - Mining mechanics
  - Crafting formulas
  - Configuration in `data/balance/formulas.yaml`
- **Dungeon Generation Config**: Data-driven dungeon creation
  - YAML configuration for generation parameters
  - Configurable room sizes, corridor widths
  - BSP algorithm settings
  - Config in `data/balance/dungeon_generation.yaml`
- **Spawning Configuration**: Data-driven mob spawning
  - Extracted from hardcoded logic
  - YAML-based spawning rules
  - Floor-based spawn tables
  - Config in `data/balance/spawning.yaml`
- **Special Room Types**: Five unique room types
  - Treasure rooms, forge rooms, shrine rooms
  - Boss rooms, ore-rich rooms
  - Special generation logic per type
- **Highscores Tracking**: Player achievement tracking
  - Score persistence in `highscores.json`
  - Victory tracking (Pure vs Legacy)
  - Deepest floor reached

#### Changed
- Comprehensive project reorganization for clarity
- EventBus pattern implementation (Phase 2/3 ready)
- Refactored World to use dungeon generation config
- Extended ConfigLoader for dungeon generation
- Bot testing framework: 2x performance improvement

#### Fixed
- 10 Legacy Vault integration test failures
- Lua test failures with export functions pattern (#21)
- Incomplete event data in Lua test handlers (#22)
- Difficulty scaling tests for RNG variation
- Pytest marker placement in test files
- Critical documentation inaccuracies (#23)

#### Documentation
- Added comprehensive architecture analysis
  - `docs/architecture/COMPREHENSIVE_ANALYSIS.md` (40KB)
  - `docs/architecture/ANALYSIS_QUICK_REFERENCE.md`
  - Architecture quality score: 4.8/5 (Excellent)
- Added AI behavior documentation and modding guide
- Complete documentation reorganization (#23)
  - Archived outdated docs
  - Updated all references to reflect actual state
- Added comprehensive Lua integration prompts
- Project status synchronized (2025-11-14) (#30)

#### Technical
- **858/860 tests passing** (99.8% pass rate)
- **5/5 architectural improvements complete**
- **Lua-ready architecture** (5/5 extensibility score)
- Python 3.10+ with comprehensive type hints
- Data-driven design patterns throughout

## [0.0.1] - 2025-11-05

### Phase 0: Foundation Complete

#### Added
- **Core Game Engine**: Turn-based roguelike foundation
  - Game loop with state management
  - Turn-based movement and combat system
  - Player entity with stats (HP, attack, defense)
  - Basic inventory system
- **Dungeon Generation**: BSP algorithm implementation
  - Procedural room generation
  - Corridor connections
  - Stair placement for floor transitions
- **Monster AI**: Pathfinding and combat
  - A* pathfinding algorithm
  - Aggressive attack behavior
  - Monster spawning system
- **Combat System**: Turn-based tactical combat
  - Attack calculations with damage rolls
  - Defense mechanics
  - Death handling for player and monsters
- **Textual UI Framework**: Terminal-based interface
  - Map rendering with tiles
  - Status bar (HP, floor, position)
  - Sidebar with stats and inventory
  - Message log for events
  - Death screen and restart flow
- **Mining System Groundwork**: Ore vein mechanics
  - Five ore properties: Hardness, Conductivity, Malleability, Purity, Density
  - Survey action for ore analysis
  - Multi-turn mining mechanic
  - Ore vein generation
- **Crafting System Foundation**: Equipment creation
  - Recipe system
  - Forge locations
  - Equipment crafting mechanics
  - Equipment stats calculation from ore properties
- **Equipment System**: Gear management
  - Equip/unequip actions
  - Stat bonuses from equipment
  - Weapon and armor slots
- **Save/Load System**: Game state persistence
  - JSON-based save format
  - Auto-save on important events
  - Load game on startup
- **Bot Testing Framework**: Automated testing
  - Warrior bot for gameplay testing
  - Performance benchmarking
  - Automated playthrough capability

#### Technical
- Python 3.10+ with type hints
- Textual framework for terminal UI
- JSON-based data persistence
- BSP algorithm for dungeon generation
- A* pathfinding for AI
- Event-driven architecture foundation

#### Documentation
- Initial project documentation
- `README.md` with quick start guide
- `HOW_TO_PLAY.md` for new players
- `docs/START_HERE.md` for developers
- `docs/MVP_ROADMAP.md` for development planning
- `docs/BROGUE_CONSOLIDATED_DESIGN.md` master design document
- Architecture and development guides

---

## Project Phases Overview

### Phase 0: Foundation (Complete ✅)
Core roguelike mechanics, UI, and basic systems

### Phase 1: MVP (98% Complete ✅)
Mining, crafting, equipment, save/load, Legacy Vault, Lua integration

### Phase 2: Multiplayer (Complete ✅)
WebSocket infrastructure, 2+ player co-op, shared dungeons, turn system

### Phase 3: Polish & Enhancement (80% Complete 🚧)
Class selection, delta compression, reconnection, personal loot, combat balance

### Phase 4: Advanced Features (Planned 📋)
PostgreSQL persistence, boss fights, race mode, leaderboards, replays

### Phase 5+: Future (Planned 📋)
PvP arena, guild/async mode, content tools, mobile/web clients

---

## Links

- **Repository**: https://github.com/scottsen/brogue
- **Documentation**: [docs/INDEX.md](docs/INDEX.md)
- **Project Status**: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- **Multiplayer Progress**: [MULTIPLAYER_PROGRESS.md](MULTIPLAYER_PROGRESS.md)
- **How to Play**: [HOW_TO_PLAY.md](HOW_TO_PLAY.md)

---

## Version History Summary

- **v0.3.0** (2025-11-14): Phase 3 core features - Personal loot, reconnection, chat, delta compression, class selection
- **v0.2.0** (2025-11-13): Phase 2 complete - Full multiplayer foundation with 2+ player co-op
- **v0.1.0** (2025-11-06): Phase 1 MVP - Legacy Vault, Lua integration, AI behaviors, comprehensive testing
- **v0.0.1** (2025-11-05): Phase 0 foundation - Core roguelike with mining, crafting, and combat

---

**The Brogue Journey**: From single-player roguelike to multiplayer co-op dungeon crawler in 9 days! 🎮⚔️
