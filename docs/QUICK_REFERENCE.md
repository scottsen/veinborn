# Veinborn Quick Reference

**Last Updated:** 2025-11-11
**For:** Players & Developers

---

## 🎮 For Players: How to Play

👉 **[Read HOW_TO_PLAY.md](../HOW_TO_PLAY.md)** - Complete 5-minute gameplay guide!

### Quick Controls Reference

**Movement:**
- `Arrows` or `HJKL`: Move in 4 directions
- `YUBN`: Move diagonally
- Hold `Shift`: Fast movement

**Actions:**
- Walk into monster: Attack (bump-to-attack)
- Walk into ore vein: Mine (bump-to-mine, takes 3-5 turns)
- `s`: Survey nearby ore (check properties)
- `g`: Pick up items
- `i`: View inventory
- `w`: Wield/wear (equip) — `W` cycles equipment
- `:`: Look at ground
- `.` or `space`: Wait / pass turn
- `c` or `enter`: Chat (multiplayer)
- `>`: Descend stairs
- `S` / `L`: Save / Load
- `r`: Restart — `q`: Quit

**Pro Tips:**
- Survey before mining (check if ore is worth it!)
- Clear monsters before mining (you're vulnerable!)
- Purity 80+ ore saves to Legacy Vault on death
- Wield crafted items with `w` — crafting happens automatically on forge tiles

---

## 🚀 For Developers: Essential Commands

### Running the Game
```bash
# Easy launcher (recommended)
./veinborn

# With options
./veinborn --debug    # Debug logging
./veinborn --safe     # Safe mode (terminal reset)
./veinborn --help     # Show help

# Old way (still works)
python3 run_textual.py
python3 scripts/run_debug.py
python3 scripts/run_safe.py

# Terminal stuck? Fix it:
reset
```

### Testing
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/unit/actions/test_mine_action.py -v

# Run tests by keyword
python3 -m pytest tests/ -k "mining" -v

# Run with coverage
python3 -m pytest tests/ --cov=src --cov-report=html

# Common test paths:
pytest tests/unit/                    # Unit tests
pytest tests/integration/             # Integration tests
pytest tests/unit/actions/            # Action tests
pytest tests/unit/systems/            # System tests
```

### Development
```bash
# Check Python syntax
python3 -m py_compile src/core/game.py

# Find TODO comments
grep -r "TODO" src/

# Count lines of code
find src/ -name "*.py" | xargs wc -l

# View game logs
tail -f logs/veinborn.log
```

---

## 📁 File Location Cheat Sheet

### "I want to add/modify..."

| Task | File Location | Type |
|------|---------------|------|
| **Monster** | `data/entities/monsters.yaml` | YAML |
| **Recipe** | `data/balance/recipes.yaml` | YAML |
| **Ore type** | `data/entities/ores.yaml` | YAML |
| **Item** | `data/entities/items.yaml` | YAML |
| **Loot drops** | `data/balance/loot_tables.yaml` | YAML |
| **Game constants** | `data/balance/game_constants.yaml` | YAML |
| **Monster spawns** | `data/balance/monster_spawns.yaml` | YAML |
| **Ore veins** | `data/balance/ore_veins.yaml` | YAML |
| **Forges** | `data/balance/forges.yaml` | YAML |

### Core Game Logic

| System | File | Lines |
|--------|------|-------|
| **Game loop** | `src/core/game.py` | ~400 |
| **Game state** | `src/core/game_state.py` | ~200 |
| **Entities** | `src/core/entities.py` | ~500 |
| **Map generation** | `src/core/world.py` | ~800 |
| **Crafting** | `src/core/crafting.py` | ~300 |
| **Save/Load** | `src/core/save_load.py` | ~400 |
| **Actions** | `src/core/actions/*.py` | ~100 each |
| **AI System** | `src/core/systems/ai_system.py` | ~200 |
| **Floor Manager** | `src/core/floor_manager.py` | ~300 |

### UI Components

| Component | File |
|-----------|------|
| **Main app** | `src/ui/textual/app.py` |
| **Map widget** | `src/ui/textual/widgets/map_widget.py` |
| **Status bar** | `src/ui/textual/widgets/status_bar.py` |
| **Sidebar** | `src/ui/textual/widgets/sidebar.py` |
| **Message log** | `src/ui/textual/widgets/message_log.py` |

---

## 🎮 Game Controls

| Key | Action |
|-----|--------|
| **H/J/K/L** | Move (vi keys) |
| **Arrow keys** | Move (cardinal) |
| **Y/U/B/N** | Move (diagonal) |
| **S** | Survey ore vein |
| **M** | Mine ore vein |
| **C** | Craft at forge |
| **E** | Equip item |
| **I** | Open inventory |
| **>** | Descend stairs |
| **<** | Ascend stairs |
| **R** | Restart game |
| **Q** | Quit |

---

## 🏗️ Architecture Quick Map

```
Game
├── GameState (holds all mutable state)
│   ├── Player
│   ├── Monsters
│   ├── Map
│   └── Inventory
├── GameContext (safe API for actions/systems)
├── Systems
│   ├── AISystem (monster behavior)
│   ├── TurnProcessor (turn management)
│   ├── FloorManager (stairs, progression)
│   └── EntitySpawner (spawn monsters/ore)
├── Actions (all state changes)
│   ├── MoveAction
│   ├── AttackAction
│   ├── MineAction
│   └── CraftAction
└── ActionFactory (creates actions)
```

**Data Flow:**
```
User Input → Action → GameContext → Modify State → Update UI
```

---

## 🧪 Test Organization

```
tests/
├── unit/              # Isolated component tests
│   ├── actions/       # Action tests (mine, attack, etc.)
│   ├── systems/       # System tests (AI, floor, etc.)
│   └── test_*.py      # Core logic tests
├── integration/       # Multi-component tests
│   ├── test_equipment_system.py
│   ├── test_loot_drops.py
│   └── test_phase5_integration.py
└── fuzz/              # Property-based tests
```

**Test Naming Convention:**
- `test_<system>_<specific_behavior>.py`
- Example: `test_mine_action_multi_turn_progress.py`

**What to Test When:**
- Changed action logic → Run `tests/unit/actions/`
- Changed system → Run `tests/unit/systems/`
- Changed entities → Run `tests/unit/test_entities.py`
- Changed crafting → Run `tests/integration/test_equipment_system.py`
- Changed YAML → Run relevant entity loader tests
- Changed anything → Run full suite before commit

---

## 🔧 Common Tasks

### Add a New Monster (5 minutes)

1. Edit `data/entities/monsters.yaml`
2. Add monster definition:
   ```yaml
   wyvern:
     name: "Wyvern"
     description: "A flying serpent"
     symbol: "W"
     color: "green"
     hp: 80
     attack: 15
     defense: 5
     xp_value: 150
   ```
3. Test: `pytest tests/unit/test_entity_loader.py`
4. Playtest: Run game, check floor 7+

### Add a New Recipe (10 minutes)

1. Edit `data/balance/recipes.yaml`
2. Add recipe under appropriate section:
   ```yaml
   mithril_sword:
     display_name: "Mithril Sword"
     requirements:
       ore_type: "mithril"
       ore_count: 2
       min_floor: 7
     stat_formulas:
       attack_bonus: "hardness * 0.15 + purity * 0.1"
   ```
3. Test formula: `python -c "h=80; p=90; print(h*0.15 + p*0.1)"`
4. Test: `pytest tests/integration/test_equipment_system.py`
5. Playtest: Mine mithril, craft at forge

### Debug a Failed Test

```bash
# Run with verbose output
pytest tests/unit/actions/test_mine_action.py -v

# Run single test
pytest tests/unit/actions/test_mine_action.py::test_mining_completes -v

# Run with print statements
pytest tests/unit/actions/test_mine_action.py -v -s

# Drop into debugger on failure
pytest tests/unit/actions/test_mine_action.py --pdb
```

### Profile Performance

```python
# In your code:
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
game.generate_dungeon()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

---

## 📚 Documentation Map

**Start Here:**
- `README.md` - Project overview
- `docs/START_HERE.md` - 15-minute onboarding
- `docs/STATUS_DASHBOARD.md` - Current state (validated)
- `docs/PROJECT_REVIEW_2026-04-17.md` - Trust-restore audit (current)

**Development:**
- `docs/MVP_CURRENT_FOCUS.md` - What to build now
- `docs/development/` - Testing, debugging guides
- `docs/architecture/` - Technical architecture

**Design:**
- `docs/VEINBORN_CONSOLIDATED_DESIGN.md` - Game design vision
- `docs/systems/` - System-specific designs

**Multiplayer:**
- `docs/design/MULTIPLAYER_DESIGN_2025.md` - Current MP design

---

## 🐛 Common Issues

### Terminal Messed Up After Crash
```bash
reset
# or
stty sane
```

### Import Errors
```bash
# Make sure you're in project root
cd /home/user/veinborn

# Verify Python path
python3 -c "import sys; print(sys.path)"
```

### Tests Fail with "GameContext not found"
```bash
# Run from project root, not tests/ directory
cd /home/user/veinborn
pytest tests/
```

### YAML Parsing Errors
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('data/entities/monsters.yaml'))"
```

### Game Won't Start
```bash
# Check logs
cat logs/veinborn.log

# Run with debug
python3 scripts/run_debug.py

# Check dependencies
pip install -r requirements.txt
```

---

## 💡 Quick Wins

**30 seconds:**
- Add a monster: Copy goblin template, change stats

**5 minutes:**
- Add a recipe: Copy copper_dagger, change ore type

**10 minutes:**
- Tweak balance: Edit game_constants.yaml

**30 minutes:**
- Add special room type: Modify world.py generation

**1 hour:**
- Add new action: Copy mine_action.py structure

---

## 🎯 Key Classes Reference

### Entity
```python
# Base class for all game objects
class Entity:
    def take_damage(amount: int) -> int
    def heal(amount: int) -> int
    def distance_to(other: Entity) -> float
```

### Action
```python
# Base class for all actions
class Action:
    def can_perform(context: GameContext) -> tuple[bool, str]
    def perform(context: GameContext) -> ActionResult
```

### GameContext
```python
# Safe API for actions/systems
context = GameContext(state, systems)
player = context.get_player()
monsters = context.get_monsters()
context.add_message("Mining complete!")
```

---

## 📊 Project Stats (Current)

- **Files:** 103 Python files
- **Tests:** 544 passing (0 skipped)
- **Pass Rate:** 100%
- **Lines of Code:** ~15,000+
- **Data Files:** 9 YAML files
- **Monsters:** 9 types (need 15-20)
- **Recipes:** 17 items
- **Ore Types:** 4 (copper, iron, mithril, adamantite)

---

## 🚨 Before You Commit

```bash
# 1. Run tests
pytest tests/ -v

# 2. Check you didn't break the game
python3 run_textual.py
# Play for 2 minutes, verify basic functionality

# 3. Check for obvious errors
python3 -m py_compile src/core/*.py

# 4. Review your changes
git diff

# 5. Commit with clear message
git add .
git commit -m "Add wyvern monster type to floor 7-9"
git push
```

---

## 📞 Need More Help?

| Question | Check |
|----------|-------|
| "How does X work?" | `docs/VEINBORN_CONSOLIDATED_DESIGN.md` |
| "Where is X implemented?" | `docs/STATUS_DASHBOARD.md` |
| "How do I test X?" | `tests/README.md` |
| "What's the architecture?" | `docs/architecture/00_ARCHITECTURE_OVERVIEW.md` |
| "Is X complete?" | `docs/STATUS_DASHBOARD.md` |

---

**Keep this doc bookmarked for instant reference!** 🔖
