# Start Here: Brogue Developer Guide

**Welcome to Brogue!** This guide will get you up to speed in 15 minutes.

---

## ⚠️ IMPORTANT: Current Development Phase

**We are in MVP Polish Phase (Single-Player)**

**What we've COMPLETED:**
- ✅ Single-player roguelike (fully playable!)
- ✅ Mining and crafting systems (85+ tests passing)
- ✅ Equipment system (10 tests passing)
- ✅ Save/load system (26 tests passing)
- ✅ Character classes (13 tests passing)
- ✅ Floor progression (23 tests passing)
- ✅ Legacy Vault system (47 tests passing)
- ✅ Lua Event System (Phase 3 complete!)
- **858/860 tests passing (99.8%)!** (2 skipped due to C-level execution limitations)

**What we're building NOW (Polish Phase):**
- 🔨 Playtesting and balance tuning
- 🔨 Content expansion (more monsters, recipes)
- 🔨 Tutorial system
- 🔨 Lua advanced features (AI behaviors, actions)
- ✅ Test suite at 99.8% (858/860) - 2 skipped tests are expected

**What we're NOT building yet:**
- ❌ Multiplayer (Phase 4, multiple months out)
- ❌ NATS message bus, microservices

**For current status:** See `PROJECT_STATUS.md` (comprehensive report)
**For next steps:** See `MVP_CURRENT_FOCUS.md` (updated 2025-11-05)
**For future multiplayer:** See `../.archived/future-multiplayer/` directory (Phase 2 designs)

---

## What is Brogue?

**Brogue = NetHack + SWG Mining + Multiplayer Co-op**

A mechanical roguelike where you dive into procedural dungeons, hunt for perfect ore spawns, craft legendary gear, and fight monsters. Think NetHack's tactical combat meets Star Wars Galaxies' resource hunting.

**Design Philosophy:**
- Tight mechanics over narrative
- "Git gud" difficulty
- Social play (bros playing together)
- Replayability through randomization

---

## Quick Start (5 minutes)

### 1. Run the Game

```bash
# Easy way (recommended)
./brogue

# Or install system-wide (then run from anywhere)
./install.sh
brogue

# Advanced options
./brogue --debug    # Debug logging
./brogue --safe     # Terminal reset on crash
./brogue --help     # Show help

# Old way (still works)
python3 run_textual.py
```

**Controls:**
- **Arrows / HJKL:** Move
- **YUBN:** Diagonal movement
- **R:** Restart game
- **Q:** Quit

### 2. Learn How to Play

👉 **[Read HOW_TO_PLAY.md](../HOW_TO_PLAY.md)** - Complete 5-minute guide!

**Quick Start:**
- Move with arrow keys or `HJKL`
- Bump into monsters to attack (`g` = goblin, `o` = orc, `T` = troll)
- Press `s` next to ore veins (◆) to survey properties
- Press `m` to mine ore (takes 3-5 turns, you're vulnerable!)
- Find forges, press `c` to craft equipment
- Press `e` to equip crafted gear
- Watch your HP in the status bar
- Die and learn (it's a roguelike!)

**The guide covers:**
- Complete controls reference
- Your first game step-by-step
- Mining & crafting strategies
- Character classes explained
- Common mistakes to avoid

### 3. Explore the Code

**Core game loop:** `src/core/game.py`
```python
# Main game loop (simplified)
while player.is_alive:
    player_action = get_input()
    process_action(player_action)
    monsters_take_turns()
    update_display()
```

**Map generation:** `src/core/world.py`
```python
# BSP dungeon algorithm
def generate_dungeon():
    partition_space()  # Binary Space Partitioning
    create_rooms()
    connect_rooms()
    spawn_monsters()
```

**UI rendering:** `src/ui/textual/app.py`
- Uses Textual framework (terminal UI)
- Widgets: map, status bar, sidebar, message log
- Refreshes on player action

---

## Project Status

### 📋 Implementation Status

**Current State:** MVP is feature-complete! 857/860 tests passing (99.7%). Game is fully playable.

**What exists (ALL WORKING):**
- ✅ Complete documentation (you're reading it!)
- ✅ Game design finalized
- ✅ Architecture implemented
- ✅ Core game code (COMPLETE - 103 Python files)
- ✅ Comprehensive test suite (857/860 passing tests)
- ✅ Lua Event System (Phase 3 complete!)

**What's been built (MVP Phase 1 - COMPLETE):**
- ✅ Core Game Loop: Turn-based movement and combat
- ✅ Map Generation: BSP dungeon algorithm (rooms + corridors)
- ✅ Monster AI: Monsters pathfind toward player and attack
- ✅ UI: Full Textual interface (map, stats, messages)
- ✅ Death/Restart: Permadeath with quick restart

### ✅ What's Implemented (MVP Systems COMPLETE)

**Mining System** (COMPLETE - 85+ tests):
- ✅ Ore veins in dungeon walls (`◆` tiles)
- ✅ Survey ore to see 5 properties (hardness, conductivity, malleability, purity, density)
- ✅ Mine ore (takes 3-5 turns, you're vulnerable!)
- ✅ Risk/reward: mine now or come back safer?

**Crafting System** (COMPLETE - 10+ tests):
- ✅ YAML-based recipes (17 recipes defined)
- ✅ Craft weapons/armor from ore
- ✅ Stats calculated: `Ore Properties × Recipe × Class Bonus`
- ✅ Forges in special dungeon rooms

**Equipment System** (COMPLETE - 10 tests):
- ✅ Equip/unequip weapons and armor
- ✅ Stat bonuses in combat
- ✅ Equipment slots working

**Save/Load System** (COMPLETE - 26 tests):
- ✅ Game state persistence
- ✅ Multiple save slots
- ✅ RNG state saved (seeded runs continue correctly)

**Character Classes** (COMPLETE - 13 tests):
- ✅ 4 classes: Warrior, Rogue, Mage, Healer
- ✅ Class-specific stats and abilities

**Floor Progression** (COMPLETE - 23 tests):
- ✅ Stairs to descend floors
- ✅ Difficulty scaling with depth
- ✅ Monster and ore progression

**Meta-Progression** (COMPLETE):
- ✅ Legacy Vault (100% complete - 47 tests passing)
- ✅ High Score tracking (COMPLETE - 10 tests)
- ✅ Pure Victory vs Legacy Victory implemented

**See full status:** `docs/PROJECT_STATUS.md` (comprehensive report)

### 🚀 Future (After MVP)

**Multiplayer Phase 2** (8-12 weeks):
- 4-player co-op
- Brilliant turn system: "4 actions per round, anyone can take them"
- 4 classes (Warrior, Mage, Healer, Rogue)
- NATS message bus, WebSocket connections
- See: `../.archived/future-multiplayer/` (archived Phase 2 designs)

---

## Essential Reading

### If you have 5 minutes:
👉 **This file** (you're reading it!)

### If you have 15 minutes:
👉 `docs/MVP_ROADMAP.md` - What to build next

### If you have 30 minutes:
👉 `docs/BROGUE_CONSOLIDATED_DESIGN.md` - Master game design (vision, systems, mechanics)

### If you have 1 hour:
👉 `docs/architecture/00_ARCHITECTURE_OVERVIEW.md` - MVP technical architecture (how it works)

### If you're implementing MVP systems:
👉 **`docs/architecture/BASE_CLASS_ARCHITECTURE.md`** - Core design patterns (45 min)
👉 **`docs/architecture/LUA_INTEGRATION_STRATEGY.md`** - Future-proofing decisions (30 min)

**Why read these?**
- Week 1-2 (mining) is ideal time to implement base classes
- Lua-ready decisions cost nothing now, save weeks later
- Clean architecture makes testing easier

### If you want to implement a feature:
👉 `docs/MVP_ROADMAP.md` - Pick a task and start coding!

---

## Project Structure

```
projects/brogue/
├── src/
│   ├── core/
│   │   ├── game.py         # ⭐ Game loop, state management
│   │   ├── entities.py     # ⭐ Player, monsters, items
│   │   ├── world.py        # ⭐ Map generation (BSP algorithm)
│   │   ├── crafting.py     # ⭐ Crafting system (COMPLETE)
│   │   ├── legacy.py       # ⭐ Legacy Vault (COMPLETE)
│   │   └── save_load.py    # ⭐ Save/load (COMPLETE)
│   │
│   └── ui/
│       └── textual/        # ⭐ Textual UI widgets
│           ├── app.py
│           └── widgets/
│
├── data/
│   ├── balance/            # ⭐ Game balance (recipes, spawning, etc)
│   ├── entities/           # ⭐ Entity definitions (monsters, ores)
│   └── highscores.json     # ⭐ High score persistence
│
├── ~/.brogue/
│   ├── saves/              # ⭐ Save games
│   └── legacy_vault.json   # ⭐ Meta-progression vault
│
├── docs/
│   ├── START_HERE.md       # 👈 You are here
│   ├── MVP_ROADMAP.md      # What to build next
│   ├── MVP_CURRENT_FOCUS.md # Implementation hub
│   ├── BROGUE_CONSOLIDATED_DESIGN.md  # Master design
│   │
│   ├── architecture/       # MVP technical architecture
│   │   ├── README.md       # Navigation guide
│   │   ├── 00_ARCHITECTURE_OVERVIEW.md  # How it works
│   │   ├── BASE_CLASS_ARCHITECTURE.md   # Design patterns
│   │   └── CONTENT_SYSTEM.md            # YAML + scripting
│   │
│   └── systems/            # System-specific documentation
│
├── .archived/              # ❌ Archived documentation (not current focus)
│   ├── Archive/            # Historical designs and summaries
│   └── future-multiplayer/ # Phase 2 multiplayer designs
│
├── scripts/
│   ├── run_debug.py        # Run with debug logging
│   └── run_safe.py         # Run with terminal reset
│
├── tests/                  # Test files
│
└── run_textual.py          # ⭐ Main entry point
```

**⭐ = Essential files to understand**
**❌ = Don't read (outdated)**

---

## Understanding the Code

### Game State Architecture

```python
# Everything lives in GameState
class GameState:
    player: Player
    monsters: list[Monster]
    map: Map
    message_log: list[str]
    turn_count: int
```

**Simple and direct** - No event bus, no NATS, no complexity (yet!)
- Phase 1 (MVP): Direct function calls
- Phase 2 (Multiplayer): Refactor to event-driven architecture

### Core Game Loop

```python
# src/core/game.py (simplified)
def run_game():
    state = GameState()
    state.map = generate_dungeon()
    state.player = spawn_player()
    state.monsters = spawn_monsters()

    while state.player.is_alive:
        # 1. Player acts
        action = get_player_input()
        process_player_action(state, action)

        # 2. Monsters act
        for monster in state.monsters:
            monster_ai(state, monster)

        # 3. Update display
        render(state)
```

### Map Generation (BSP Algorithm)

```python
# src/core/world.py (concept)
def generate_dungeon(width, height):
    # 1. Binary Space Partitioning
    root = create_room(0, 0, width, height)
    split_recursive(root)

    # 2. Create rooms in leaf nodes
    rooms = []
    for leaf in leaves(root):
        room = create_random_room(leaf)
        rooms.append(room)

    # 3. Connect rooms with corridors
    for i in range(len(rooms) - 1):
        connect_rooms(rooms[i], rooms[i+1])

    return Map(rooms, corridors)
```

### Monster AI (Simple Pathfinding)

```python
# src/core/game.py (simplified)
def monster_turn(state, monster):
    # 1. Can we attack player?
    if adjacent(monster, state.player):
        attack(monster, state.player)
        return

    # 2. Move toward player
    direction = get_direction_to(monster.pos, state.player.pos)
    move(monster, direction)
```

---

## Key Concepts

### 1. Turn-Based Gameplay

- **Your turn:** Move, attack, or use item
- **Monster turns:** All monsters move/attack
- **Repeat:** Until you die or win

**Why turn-based?**
- Tactical (think before acting)
- Not twitchy (knowledge > reflexes)
- Classic roguelike feel

### 2. Procedural Generation

Every run is different:
- Random map layout (BSP algorithm)
- Random monster spawns
- Random ore properties (Phase 1)
- Random item drops (Phase 1)

**Replayability:** 1000 runs, 1000 different dungeons

### 3. Permadeath (with meta-progression)

**Permadeath:**
- You die → Run ends → Start over
- No save-scumming

**Meta-progression (Phase 1):**
- Legacy Vault saves rare ore (80+ purity)
- Can withdraw 1 ore per run
- "Pure Victory" (no legacy) vs "Legacy Victory"
- Encourages replay without removing stakes

### 4. Mining/Crafting (Phase 1 - COMPLETE)

**The hook that makes Brogue unique:**

**Mining:**
- Ore veins in walls (`◆` tiles)
- Survey to see properties (1 turn)
- Mine to collect (3-5 turns, vulnerable!)
- Risk: Mine now (dangerous) or later (safer)?

**Ore Properties (0-100):**
```
Hardness      → Weapon damage / Armor defense
Conductivity  → Magic power / Spell efficiency
Malleability  → Durability / Repair ease
Purity        → Quality multiplier (affects all)
Density       → Weight / Encumbrance
```

**Crafting:**
```
Ore Properties × Recipe × Class Bonus = Final Stats

Example:
  Iron Ore: Hardness 78, Purity 82
  Recipe: Longsword (base +4 damage)

  Damage = 4 + (78 × 0.82) = +68 damage sword!
```

**Why this is fun:**
- Resource hunting ("find that 95+ hardness iron!")
- Meaningful decisions (mine risky ore or keep searching?)
- Dopamine hit from perfect spawns
- Every run has different ore quality

---

## Development Workflow

### Adding a New Feature

1. **Read the design:** `docs/BROGUE_CONSOLIDATED_DESIGN.md`
2. **Check the roadmap:** `docs/MVP_ROADMAP.md`
3. **Understand existing code:** Read `src/core/game.py`, `entities.py`, `world.py`
4. **Implement:** Follow existing patterns
5. **Test:** Play the game, make sure it works
6. **Document:** Update relevant docs

### Code Style

- **Python 3.10+** with type hints
- **Follow existing patterns** (look at `src/core/game.py`)
- **Keep it simple** (no over-engineering)
- **Comment complex logic** (especially algorithms)
- **Write tests** for new systems (see `tests/`)

### Testing Strategy

**Manual testing (primary):**
- Run the game (`python3 run_textual.py`)
- Test your feature by playing
- Try edge cases (what if player dies while mining?)
- Check message log for errors

**Automated testing (secondary):**
- Unit tests in `tests/`
- Run with `python3 -m pytest tests/`
- Test game logic, not UI

### Git Workflow

**Branches:**
- `master` - Working game (always playable)
- Feature branches for new work

**Commits:**
- Descriptive messages ("Add ore vein spawning")
- Atomic commits (one feature per commit)
- Test before committing

---

## Common Questions

### Q: Why Python and not Rust/C++?

**A:** Speed of development > raw performance
- Python is fast enough for turn-based game
- Rich ecosystem (Textual, Pydantic, NATS)
- Async/await for multiplayer (Phase 2)
- Type hints give us safety

### Q: Why Textual framework?

**A:** Best terminal UI framework for Python
- Modern (better than curses/Blessed)
- Widget composition (like React)
- Good documentation
- Active development
- See: `docs/UI_FRAMEWORK.md`

### Q: What's in docs/Archive/?

**A:** ❌ **Don't read it!** Wrong design visions.
- Emotional story progression (rejected)
- 15 essence types (too complex)
- 12-property materials (too much)

**Consolidated design (Oct 22):** Merged 3 visions into current design
- Archive = dead ends
- Read `BROGUE_CONSOLIDATED_DESIGN.md` instead

### Q: When does multiplayer happen?

**A:** After MVP is complete (4-6 months from now)
- MVP first: Mining, crafting, meta-progression
- Then: Multiplayer infrastructure
- See: `docs/future-multiplayer/`

### Q: Can I work on multiplayer now?

**A:** Please don't! Focus on MVP.
- Multiplayer requires complete redesign (message-based)
- Need working single-player first
- MVP will inform multiplayer design

### Q: How can I contribute?

**A:** Pick a task from `docs/MVP_ROADMAP.md`!
- Week 1-2: Mining system
- Week 3: Crafting system
- Week 4: Meta-progression
- Week 5-6: Content & polish

---

## Resources

### Documentation Map

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **START_HERE.md** | Onboarding | Right now! |
| **MVP_ROADMAP.md** | What to build | Before implementing |
| **BROGUE_CONSOLIDATED_DESIGN.md** | Game vision | Understanding "why" |
| **architecture/** | Technical specs | Phase 2 (future) |
| **future-multiplayer/** | MP design | Phase 2 (future) |
| **Archive/** | ❌ Don't read | Never |

### Code Map

| File | Purpose | Complexity |
|------|---------|------------|
| `src/core/game.py` | Game loop | ⭐⭐ Medium |
| `src/core/entities.py` | Player/monsters | ⭐ Easy |
| `src/core/world.py` | Map generation | ⭐⭐⭐ Hard |
| `src/ui/textual/app.py` | UI framework | ⭐⭐ Medium |

### External Links

- **Textual docs:** https://textual.textualize.io/
- **Python async:** https://docs.python.org/3/library/asyncio.html
- **Roguelike dev:** http://www.roguebasin.com/
- **BSP algorithm:** http://www.roguebasin.com/index.php?title=Basic_BSP_Dungeon_generation

---

## Your First Task

**Ready to contribute? Start here:**

1. **Play the game** for 10 minutes
   ```bash
   python3 run_textual.py
   ```

2. **Read the code** for 20 minutes
   - `src/core/game.py` - Game loop
   - `src/core/entities.py` - Player and monsters
   - `src/core/world.py` - Map generation

3. **Pick a task** from `docs/MVP_ROADMAP.md`
   - Start with **Task 1.1: Ore Vein Generation** (good first task!)
   - Or **Task 4.1: More Monster Types** (easy content work)

4. **Ask questions** if you're stuck
   - Check existing code for patterns
   - Read design docs for "why"
   - Test frequently (play the game!)

---

## Quick Reference: Running the Game

```bash
# Easy launcher (recommended)
./brogue              # Normal mode
./brogue --debug      # Debug mode (full logging)
./brogue --safe       # Safe mode (terminal reset on crash)
./brogue --help       # Show help

# Install system-wide (optional)
./install.sh          # Installs 'brogue' command to ~/.local/bin

# Old way (still works)
python3 run_textual.py
python3 scripts/run_debug.py
python3 scripts/run_safe.py

# Run tests
python3 -m pytest tests/
python3 -m pytest tests/test_widgets.py
```

**Terminal stuck?** Run `reset` or use `./brogue --safe` next time.

---

## Welcome Aboard!

You're now ready to build Brogue. Start with the MVP roadmap and pick a task.

**Remember:**
- Keep it simple (no over-engineering)
- Follow existing patterns
- Test by playing the game
- Have fun building!

🎮 Happy coding, and may your ore spawns be legendary.

---

**Questions?** Check the docs or ask in the project chat.

**Found a bug?** Play through it, document it, fix it.

**Want to add a feature?** Check the roadmap first!
