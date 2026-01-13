# Veinborn

**NetHack + SWG Mining + Multiplayer Co-op**

A mechanical roguelike where you and your bros dive into procedural dungeons, hunt for perfect ore spawns, craft legendary gear, and fight your way deeper.

---

## Installation

### From PyPI (Recommended)

```bash
pip install veinborn
veinborn              # Launch the game
```

### From Source

```bash
# Clone and run directly
git clone https://github.com/scottsen/veinborn
cd veinborn
pip install -e .
veinborn
```

---

## Quick Start

### Play the Game

```bash
# If installed via pip
veinborn

# Or run from source
./veinborn

# Advanced options
./veinborn --debug    # Debug mode with logging
./veinborn --safe     # Safe mode (terminal reset)
./veinborn --help     # Show help
```

**New to Veinborn?** 👉 **[QUICKSTART.md](QUICKSTART.md)** - Get playing in 5 minutes ⚡

**Full guide:** [HOW_TO_PLAY.md](HOW_TO_PLAY.md) - Complete gameplay guide

**Quick Controls:**
- `Arrows/HJKL`: Move
- `YUBN`: Diagonal movement
- `s`: Survey ore
- `m`: Mine ore
- `c`: Craft (at forge)
- `e`: Equip items
- `>`: Descend stairs
- `R`: Restart game
- `Q`: Quit

**Gameplay Loop:** Explore → Mine ore → Craft equipment → Fight monsters → Go deeper → Die → Learn → Repeat!

### Understanding the Legacy Vault

When you die, all ore with **purity 80+** is saved to your Legacy Vault (`~/.veinborn/legacy_vault.json`).

**Starting a new run:**
- Choose **Pure Victory** (no vault, harder, more prestige)
- Or **Legacy Victory** (withdraw 1 ore, easier start)

Both paths are valid! Use the vault to learn or overcome bad luck.

### Documentation

**Choose your path:**
- 🎮 **Player?** → [QUICKSTART.md](QUICKSTART.md) - Start playing now
- 🎨 **Content creator?** → [docs/CONTENT_CREATION.md](docs/CONTENT_CREATION.md) - Add monsters/items
- 🔧 **Modder?** → [docs/LUA_API.md](docs/LUA_API.md) - Lua modding API
- 👨‍💻 **Developer?** → [docs/START_HERE.md](docs/START_HERE.md) - Contributing guide

**Full documentation hub:** [docs/README.md](docs/README.md)

**Quick lookup:**
- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) - What's implemented (858/860 tests ✅)
- [docs/MVP_ROADMAP.md](docs/MVP_ROADMAP.md) - What's next
- [docs/INDEX.md](docs/INDEX.md) - Complete documentation index

---

## Project Status

### ✅ Phase 0: Foundation (COMPLETE)

**Working Now:**
- Turn-based movement and combat
- BSP dungeon generation (procedural rooms + corridors)
- Monster AI (pathfinding, attack)
- Textual UI (map, status bar, sidebar, message log)
- Death and restart flow

**Try it:** `python3 run_textual.py`

### 🔨 Phase 1: MVP (98% Complete)

**✅ Core Systems Implemented:**
- Mining system (ore veins, survey action, multi-turn mining)
- Crafting system (recipes, forges, equipment crafting)
- Equipment system (equip/unequip, stat bonuses)
- Save/load system (game state persistence)
- Bot testing framework (warrior bot, 2x performance improvement)

**✅ Architecture Improvements (Nov 2025):**
- EventBus system (pub/sub pattern, Phase 2/3 ready)
- AI behavior system (5 behavior types: aggressive, defensive, passive, coward, guard)
- Data-driven spawning (YAML configuration)
- Centralized formula system (damage, mining, crafting balance)
- Bot equipment intelligence (stat-based upgrade detection)

**📊 Project Health:**
- **858/860 tests passing** (99.8% pass rate, comprehensive coverage)
- **5 of 5 architectural improvements complete**
- **Lua-ready architecture** (5/5 extensibility score)
- **Multiplayer Phase 2 complete** (2+ player co-op working!)

**✅ Legacy Vault System (Complete):**
- Meta-progression system (preserves purity 80+ ore across runs)
- Dual victory paths (Pure vs Legacy runs)
- Vault UI and integration

**See:** [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md)

### 🚀 Phase 2: Multiplayer (COMPLETE! 🎉)

**Working Now (as of 2025-11-14):**
- ✅ 2+ player co-op (WebSocket server functional!)
- ✅ "4 actions per round, anyone can take them" (implemented!)
- ✅ Shared dungeon generation (distributed player spawning)
- ✅ Monster AI integration (nearest-player targeting)
- ✅ Turn system working (real-time synchronization)
- ✅ Test client for validation

**Phase 3 (Next):**
- Extended testing (30+ min co-op sessions)
- Combat balance for multiplayer
- Class selection on join
- Personal loot system
- Boss fights designed for co-op

**See:** [`MULTIPLAYER_PROGRESS.md`](MULTIPLAYER_PROGRESS.md) and [`docs/design/MULTIPLAYER_DESIGN_2025.md`](docs/design/MULTIPLAYER_DESIGN_2025.md)

---

## Core Features

### The NetHack Part

- **Procedural dungeons** with permadeath
- **Turn-based tactical combat** (think, don't twitch)
- **"Git gud" difficulty** (knowledge > reflexes)
- **Classic roguelike feel** (@ vs monsters)

### The SWG Mining Part

- **Ore veins** with 5 random properties (Hardness, Conductivity, Malleability, Purity, Density)
- **Resource hunting** mini-game ("OMG perfect spawn!")
- **Mining is risky** (takes 3-5 turns, you're vulnerable)
- **Craft gear from ore** (stats = ore properties × recipe)

### The Multiplayer Part (Phase 2)

- **Simultaneous turns:** "4 actions per round, anyone can take them"
- **Co-op strategy:** Let healer take all 4 turns in emergency
- **Personal loot:** Everyone gets their own roll (no fighting!)
- **Class synergies:** Warrior/Mage/Healer/Rogue

### The Meta-Progression Part

- **Legacy Vault** saves rare ore (80+ purity) when you die
- **Pure Victory** (no Legacy gear) for street cred
- **Legacy Victory** (use vault) for accessibility
- **Both are valid**, both are tracked

---

## Documentation

### 🗺️ Documentation Map

👉 **[Complete Documentation Index](docs/INDEX.md)** - Find any document quickly!

### 🎯 Essential Reading (2-30 minutes)

| Document | Time | Purpose |
|----------|------|---------|
| [`docs/STATUS_DASHBOARD.md`](docs/STATUS_DASHBOARD.md) ⭐ | 2 min | **At-a-glance status** (read this first!) |
| [`docs/START_HERE.md`](docs/START_HERE.md) | 15 min | New developer onboarding |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | 10 min | Comprehensive status report (100% accurate) |
| [`docs/MVP_CURRENT_FOCUS.md`](docs/MVP_CURRENT_FOCUS.md) | 5 min | What to build right now |
| [`docs/VEINBORN_CONSOLIDATED_DESIGN.md`](docs/VEINBORN_CONSOLIDATED_DESIGN.md) | 30 min | Master game design vision |

### 📚 Quick Links

**Getting Started:**
- [`docs/START_HERE.md`](docs/START_HERE.md) - Developer guide
- [`docs/QUICK_REFERENCE.md`](docs/QUICK_REFERENCE.md) - Commands, files, common tasks

**Current Work:**
- [`docs/STATUS_DASHBOARD.md`](docs/STATUS_DASHBOARD.md) - ⭐ **At-a-glance status** (2 min, read this first!)
- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) - Comprehensive status (100% accurate!)
- [`docs/MVP_CURRENT_FOCUS.md`](docs/MVP_CURRENT_FOCUS.md) - Current priorities
- [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md) - High-level roadmap

**Game Design:**
- [`docs/VEINBORN_CONSOLIDATED_DESIGN.md`](docs/VEINBORN_CONSOLIDATED_DESIGN.md) - Master design
- [`docs/MECHANICS_REFERENCE.md`](docs/MECHANICS_REFERENCE.md) - Detailed mechanics

**Development:**
- [`docs/development/`](docs/development/) - Testing, debugging guides
- [`docs/architecture/`](docs/architecture/) - Technical architecture
  - [`COMPREHENSIVE_ANALYSIS.md`](docs/architecture/COMPREHENSIVE_ANALYSIS.md) - Complete architectural analysis (40KB)
  - [`ANALYSIS_QUICK_REFERENCE.md`](docs/architecture/ANALYSIS_QUICK_REFERENCE.md) - Quick reference & scorecards
  - [`README_ANALYSIS.md`](docs/architecture/README_ANALYSIS.md) - Architecture documentation index
- [`docs/CONTENT_CREATION.md`](docs/CONTENT_CREATION.md) - Add monsters/items/recipes

**Future Plans:**
- [`docs/future-multiplayer/`](docs/future-multiplayer/) - Phase 2 multiplayer design (not current!)

**Full Index:**
- [`docs/INDEX.md`](docs/INDEX.md) - **Complete documentation map** 🗺️

---

## Project Structure

```
veinborn/
├── run_textual.py          # ⭐ Main entry point
├── run.py                  # Legacy entry point
│
├── src/
│   ├── core/
│   │   ├── game.py         # ⭐ Game loop, state management
│   │   ├── entities.py     # ⭐ Player, monsters, items
│   │   ├── world.py        # ⭐ Map generation (BSP algorithm)
│   │   ├── recipes.py      # TODO: Crafting system
│   │   ├── legacy.py       # TODO: Legacy Vault
│   │   └── save.py         # TODO: Save/load
│   │
│   └── ui/
│       └── textual/        # ⭐ Textual UI widgets
│           ├── app.py
│           └── widgets/
│
├── data/                   # TODO: Game data (recipes, saves)
│
├── docs/
│   ├── START_HERE.md       # 👈 Start here!
│   ├── MVP_ROADMAP.md      # What to build
│   ├── VEINBORN_CONSOLIDATED_DESIGN.md  # Master design
│   ├── development/        # Testing, debugging, dev guides
│   ├── architecture/       # Architecture & technical design
│   ├── systems/            # System-specific docs
│   ├── future-multiplayer/ # Phase 2 design
│   └── Archive/            # ❌ Historical docs
│
├── scripts/
│   ├── run_debug.py        # Debug mode
│   └── run_safe.py         # Safe mode (terminal reset)
│
├── tests/                  # Test files
│
└── requirements.txt        # Python dependencies
```

**⭐ = Essential files**
**❌ = Outdated/archived**

---

## Development

### Run the Game

```bash
# Main game
python3 run_textual.py

# Debug mode (with logging)
python3 scripts/run_debug.py

# Safe mode (terminal reset)
python3 scripts/run_safe.py
```

### Development Workflow

1. **Read:** [`docs/START_HERE.md`](docs/START_HERE.md) (15 minutes)
2. **Understand:** Play the game, read `src/core/game.py`
3. **Pick a task:** [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md)
4. **Implement:** Follow existing patterns
5. **Test:** Play the game, test your feature
6. **Commit:** Descriptive message, atomic commits

### Code Style

- **Python 3.10+** with type hints
- **Follow existing patterns** (see `src/core/game.py`)
- **Keep it simple** (no over-engineering)
- **Test by playing** (manual testing is primary)
- **Document complex logic**

### Using TIA Tools

```bash
# Project dashboard
tia project show veinborn

# Task management
tia task list --project veinborn
tia task add "description" --project veinborn

# Search
tia search all "veinborn"
tia beth explore "veinborn"

# Sessions
tia session recent
tia session search "veinborn"
```

---

## Technology Stack

### Current (Phase 1 - MVP)

- **Language:** Python 3.10+
- **UI:** Textual (terminal UI framework)
- **Persistence:** JSON files (local saves, Legacy Vault)
- **Architecture:** Single-player, single process

### Future (Phase 2 - Multiplayer)

- **Networking:** WebSockets + NATS
- **Database:** PostgreSQL (shared state)
- **Messaging:** Pydantic messages over NATS
- **Proxy:** nginx (tia-proxy)
- **Architecture:** Server-authoritative, instance-based
- **Observability:** structlog + Prometheus

**See:** [`docs/architecture/00_ARCHITECTURE_OVERVIEW.md`](docs/architecture/00_ARCHITECTURE_OVERVIEW.md)

---

## Recent Development Activity

### November 2025: Multiplayer Phase 2 Complete! 🎉

**Major Achievement (Nov 14, 2025):**
- ✅ **Multiplayer Phase 2 COMPLETE** - 2+ player co-op is fully functional!
- ✅ **WebSocket infrastructure** - 11 new files, ~2,400 lines of code
- ✅ **Turn system implemented** - "4 actions per round, anyone can take them"
- ✅ **Monster AI integration** - Monsters act after player rounds, target nearest player
- ✅ **Shared dungeon** - Distributed player spawning across different rooms

**5 Major PRs Merged (Nov 2025):**
- **PR #29** - Documentation updates (reflect Phase 2 completion)
- **PR #28** - Monster AI targeting (nearest-player algorithm)
- **PR #27** - Dungeon generation & distributed spawning
- **PR #26** - Multiplayer game functionality (turn system, co-op)
- **PR #25** - Multiplayer design document (2025)

**Impact:**
- +2,400 lines of multiplayer code
- +200 tests (858/860 passing, 99.8%)
- 11 new server files (WebSocket, auth, game session, state)
- Architecture quality: **4.8/5** (Excellent)
- Multiplayer Phase 2: **COMPLETE** ✅

**Next:** Phase 3 testing + single-player polish (dual-track development)

---

## Design Philosophy

### 1. Mechanical Over Narrative

- **Quest is simple motivation** (rescue your bro)
- **Gameplay loop is the star** (dive, mine, craft, fight)
- **Replayability through mechanics** (not story)

### 2. Simple Rules, Complex Emergence

- **"4 actions per round, anyone can take them"** → infinite strategy
- **5 ore properties** → thousands of combinations
- **Personal loot** → no fighting, yes trading

### 3. Accessibility + Mastery

- **Legacy Vault** for new players (easier runs)
- **Pure Victory** for veterans (street cred)
- **Both are valid**, both are tracked

### 4. Social Play ("Bros")

- **Invite friends** (no randoms)
- **Co-op, not competitive** (help each other)
- **Trade loot** (personal rolls from shared veins)
- **Community sharing** (find perfect ore spawns together)

---

## The Name

**Why "Veinborn"?**

Born from the veins of the earth - a name that captures the essence of mining, ore hunting, and the underground depths where legendary equipment is forged. The game's identity is rooted in discovering perfect ore veins and being reborn stronger with each run.

---

## Design History

### Key Sessions

- **2025-09-30:** Project created
- **2025-10-01:** Core mechanics explored
- **2025-10-14:** Textual UI framework chosen
- **2025-10-16:** Textual UI implemented
- **2025-10-21:** Multiplayer design explosion (9,500+ lines)
- **2025-10-22:** Design consolidation (vision clarified)
- **2025-10-23:** Architecture documentation created
- **2025-10-23:** Project cleanup and MVP alignment

### Major Decisions

**✅ Accepted:**
- NetHack + SWG Mining + Multiplayer
- Textual UI framework (not Blessed)
- 5-property ore system (not 12)
- Simultaneous turn allocation
- Personal loot from shared resources
- Legacy Vault + Pure Victory tracking

**❌ Rejected:**
- Emotional story progression
- Essence mastery system (too complex)
- Memory-based progression
- 12-property materials (over-engineered)

---

## Contributing

### For Developers

1. **Read:** [`docs/START_HERE.md`](docs/START_HERE.md)
2. **Check:** [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md)
3. **Pick a task** from the roadmap
4. **Follow existing patterns** in `src/core/`
5. **Test thoroughly** (play the game!)
6. **Document** new features

### For Designers

1. **Understand the vision:** Mechanical, not narrative
2. **Simple rules, complex emergence**
3. **Ask:** Does this make "one more run" more compelling?
4. **Balance:** Accessibility (Legacy) vs Mastery (Pure)

---

## FAQ

### Q: Can I play it now?

**A:** Yes! Run `python3 run_textual.py`

Currently implemented:
- Turn-based movement and combat
- Procedural dungeon generation
- Monster AI
- Death and restart

Coming soon:
- Mining and crafting systems

### Q: Is multiplayer working?

**A:** Not yet! Multiplayer is Phase 2 (after MVP).

**Current:** Single-player roguelike
**Next:** Mining/crafting systems (Phase 1)
**Later:** 4-player co-op (Phase 2)

### Q: How can I help?

**A:** Pick a task from [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md)!

Good first tasks:
- Task 1.1: Ore vein generation
- Task 4.1: More monster types

### Q: What's in docs/Archive/?

**A:** ❌ **Don't read it!** Old/conflicting designs.

The design was consolidated on 2025-10-22. Everything in Archive/ represents rejected visions:
- Emotional story progression (wrong focus)
- Essence mastery (too complex)
- 12-property materials (over-engineered)

**Read instead:** [`docs/VEINBORN_CONSOLIDATED_DESIGN.md`](docs/VEINBORN_CONSOLIDATED_DESIGN.md)

### Q: Why Python instead of Rust/C++?

**A:** Speed of development > raw performance

- Python is fast enough for turn-based game
- Rich ecosystem (Textual, Pydantic, NATS)
- Async/await for multiplayer
- Type hints provide safety

---

## Related Links

**TIA Integration:**
- Project metadata: [`project.yaml`](project.yaml)
- TIA projects index: [`../../README.md`](../../README.md)

**External Resources:**
- Textual docs: https://textual.textualize.io/
- Roguelike dev: http://www.roguebasin.com/
- BSP algorithm: http://www.roguebasin.com/index.php?title=Basic_BSP_Dungeon_generation

---

## License

**Project Type:** Personal / TIA-integrated
**Status:** Active Development

---

**🎮 Veinborn: Where bros hunt perfect ore spawns together.**

*Git gud, find legendary ore, craft epic gear, dive deeper.*
