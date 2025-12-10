# Changelog

All notable changes to the Veinborn project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
