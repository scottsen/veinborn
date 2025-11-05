# Brogue MVP: Current Focus & Implementation Guide

**Status:** ⚠️ **ACTIVE DEVELOPMENT** - This is what we're building NOW
**Phase:** MVP (Single-Player)
**Timeline:** 4-6 weeks
**Last Updated:** 2025-10-24

---

## ⭐ START HERE for Implementation

This document is your **implementation hub** for the Brogue MVP. If you're ready to code, you're in the right place!

---

## 🎯 What We're Building (MVP)

**Single-player terminal roguelike with mining and crafting systems**

### Core Features:
1. ✅ **Basic Game** - Movement, combat, map generation (DONE)
2. 🔨 **Mining System** - Survey ore, mine over turns (NEXT)
3. 🔨 **Crafting System** - Recipes, forging items
4. 🔨 **Meta-Progression** - Legacy Vault, save/load
5. 🔨 **Polish** - More monsters, content, balance

### What We're NOT Building Yet:
- ❌ Multiplayer (Phase 2, 8-12 weeks out)
- ❌ NATS message bus
- ❌ Microservices
- ❌ Lua scripting (Phase 3)
- ❌ WebSocket clients

**Why?** MVP focuses on making the single-player game fun. Multiplayer comes later.

---

## 📋 Current Task: Mining System (Week 1-2)

### What to Build:

#### 1. Ore Vein Generation
**File:** `src/core/world.py`

```python
class OreVein:
    """Ore that can be mined"""
    ore_type: str  # "copper", "iron", "mithril", "adamantite"
    x: int
    y: int
    properties: dict[str, int]  # 5 properties (0-100 scale)
    mining_turns: int  # 3-5 turns based on hardness
```

**Task:** Add ore veins to dungeon generation
- Spawn in walls (`#` tiles)
- Render as `◆` symbol
- 5 properties: hardness, conductivity, malleability, purity, density
- Ore tier based on floor depth

#### 2. Survey Action
**File:** `src/core/game.py`

```python
def handle_survey_action(self, target_x: int, target_y: int):
    """Survey ore vein (1 turn, reveals properties)"""
    ore = self.map.get_ore_at(target_x, target_y)
    if ore and self.player.is_adjacent(ore):
        ore.surveyed = True
        self.ui.show_ore_properties(ore)
```

**Task:** Add 's' keybind for surveying
- Must be adjacent to ore
- Takes 1 turn
- Shows ore properties in UI widget

#### 3. Mining Action
**File:** `src/core/game.py`

```python
def handle_mining_action(self):
    """Mine ore (multi-turn, player vulnerable)"""
    if self.player.is_mining:
        self.player.mining_progress += 1
        if self.player.mining_progress >= self.player.mining_target.turns:
            # Mining complete
            ore = self.player.mining_target.collect()
            self.player.inventory.add(ore)
            self.player.stop_mining()
        # Player can't move/attack while mining!
```

**Task:** Add 'm' keybind for mining
- Takes 3-5 turns (based on hardness)
- Player vulnerable (can't dodge attacks)
- Can cancel with ESC (lose progress)
- Ore added to inventory when complete

### Testing:
```python
# tests/test_mining.py
def test_ore_vein_generation():
    dungeon = generate_dungeon(80, 40)
    ores = dungeon.get_all_ore_veins()
    assert len(ores) > 0  # Should have some ore

def test_survey_reveals_properties():
    ore = OreVein(ore_type="iron", x=10, y=10)
    assert not ore.surveyed
    game.handle_survey_action(10, 10)
    assert ore.surveyed

def test_mining_takes_multiple_turns():
    ore = OreVein(ore_type="iron", x=10, y=10, mining_turns=4)
    game.player.start_mining(ore)

    for i in range(3):
        game.handle_mining_action()
        assert len(game.player.inventory.ores) == 0  # Not done yet

    game.handle_mining_action()  # 4th turn
    assert len(game.player.inventory.ores) == 1  # Mining complete!
```

---

## 🗺️ Implementation Roadmap

### ✅ Phase 0: Foundation (COMPLETE)
- Basic game loop
- Movement and combat
- Map generation (BSP)
- Textual UI
- Monster AI

### 🔨 Phase 1: Mining (Current - Weeks 1-2)
- [ ] Ore vein generation
- [ ] Survey action (1 turn, shows properties)
- [ ] Mining action (3-5 turns, vulnerable)
- [ ] Ore inventory system
- [ ] Ore display UI widget

### 📅 Phase 2: Crafting (Weeks 3-4)
- [ ] Recipe YAML loader
- [ ] Crafting UI
- [ ] Stat calculation (ore properties × recipe)
- [ ] Forge locations
- [ ] Item system

### 📅 Phase 3: Meta-Progression (Weeks 4-5)
- [ ] Legacy Vault (save rare ore on death)
- [ ] Save/load system
- [ ] Statistics tracking
- [ ] Pure vs Legacy victory types

### 📅 Phase 4: Polish (Weeks 5-6)
- [ ] 15-20 monster types
- [ ] Boss encounters
- [ ] Tutorial/help system
- [ ] Balance pass
- [ ] Bug fixes

---

## 📁 Key Files to Know

### Core Game Logic:
- `src/core/game.py` - Main game loop, action handlers
- `src/core/entities.py` - Player, Monster, OreVein classes
- `src/core/world.py` - Map generation
- `src/core/recipes.py` - Crafting system (TODO)

### UI:
- `src/ui/textual/app.py` - Main Textual app
- `src/ui/textual/widgets/` - UI widgets

### Data:
- `data/recipes/` - Recipe YAML files (TODO)
- `data/monsters/` - Monster definitions (TODO)
- `data/saves/` - Save games (TODO)

### Tests:
- `tests/test_entities.py` - Entity tests
- `tests/test_world.py` - Map generation tests
- `tests/test_mining.py` - Mining system tests (TODO)

---

## 🚀 Getting Started

### 1. Play the Current Game
```bash
cd /home/scottsen/src/tia/projects/brogue
python3 run_textual.py
```

**Try it:**
- Move around (arrow keys or HJKL)
- Fight monsters (bump into them)
- Explore the dungeon
- Die and restart (R key)

### 2. Read the Code
Start with these files (in order):
1. `src/core/game.py` - Game loop (~300 lines)
2. `src/core/entities.py` - Player/Monster (~200 lines)
3. `src/core/world.py` - Map generation (~400 lines)

**Look for:**
- How player movement works
- How combat is handled
- How the game loop processes turns

### 3. Pick Your First Task

**Easy:** Add more monster types
- File: `src/core/entities.py`
- Just add new Monster subclasses
- Quick win, builds confidence

**Medium:** Ore vein generation
- File: `src/core/world.py`
- Add OreVein class
- Spawn in dungeon generation
- Good first feature

**Hard:** Mining action system
- File: `src/core/game.py`
- Multi-turn action system
- Player state management
- Requires understanding game loop

### 4. Write a Test First (TDD)
```python
# tests/test_mining.py
def test_ore_vein_spawns_in_dungeon():
    dungeon = generate_dungeon(80, 40)
    ores = dungeon.get_all_ore_veins()
    assert len(ores) > 0, "Dungeon should have ore veins"
```

### 5. Implement Until Test Passes
```python
# src/core/world.py
def generate_dungeon(width, height):
    # ... existing code ...

    # NEW: Spawn ore veins
    ore_veins = []
    for room in rooms:
        if random.random() < 0.3:  # 30% chance per room
            ore = spawn_ore_vein(room)
            ore_veins.append(ore)

    return Map(rooms, corridors, ore_veins)
```

### 6. Manual Test (Play the Game!)
```bash
python3 run_textual.py
```

Look for `◆` symbols in the dungeon. They should be there!

---

## 📚 Essential Documentation

### For Implementation:
1. **MVP_ROADMAP.md** - Detailed task breakdown
2. **architecture/00_ARCHITECTURE_OVERVIEW.md** - How the code works
3. **architecture/DEVELOPMENT_GUIDELINES.md** - Code style, testing
4. **BROGUE_CONSOLIDATED_DESIGN.md** - Game design vision

### For Future Planning:
- **architecture/BASE_CLASS_ARCHITECTURE.md** - Optional: Clean base classes
- **architecture/LUA_INTEGRATION_STRATEGY.md** - Phase 3 planning
- **future-multiplayer/** - Phase 2 architecture (don't build yet!)

---

## ❓ Common Questions

### "Should I use the Entity base class from BASE_CLASS_ARCHITECTURE.md?"

**Optional, but recommended**

Benefits:
- Less code duplication
- Easier to add OreVein (just extend Entity)
- Makes Phase 2 refactor easier

Time cost: 2-3 hours

**Verdict:** Do it in Week 1 if you have time, or Week 3 during cleanup.

### "What about all the NATS/microservice docs?"

**That's Phase 2 (8-12 weeks out)**

For MVP:
- Simple Python game loop (no NATS)
- Direct function calls (no microservices)
- Local only (no networking)

See `future-multiplayer/` for Phase 2 plans, but don't implement yet!

### "Should I load monsters from YAML files?"

**Optional for MVP**

Current approach (hardcoded) works fine:
```python
monsters = [
    Monster("goblin", hp=6, attack=3),
    Monster("orc", hp=12, attack=5),
]
```

YAML approach (better, but more work):
```yaml
# data/monsters/goblin.yaml
name: Goblin
hp: 6
attack: 3
```

**Verdict:** Hardcode for Week 1-2, add YAML in Week 3-4 if you want.

### "How do I know if I'm building the right thing?"

Check these 3 things:
1. ✅ Is it in MVP_ROADMAP.md? (If yes, build it)
2. ✅ Is it simple Python? (No NATS/microservices)
3. ✅ Can I playtest it? (If yes, you're on track)

If you're implementing NATS, WebSockets, or Lua → **STOP! Wrong phase.**

---

## 🎯 Success Criteria

**MVP is done when:**
- ✅ Mining system works (survey ore, mine over turns)
- ✅ Crafting system works (recipes, stat calculation)
- ✅ Legacy Vault works (rare ore survives death)
- ✅ Game saves/loads
- ✅ 15-20 monster types
- ✅ Game is fun and replayable

**How to know you're done:**
- Play for 30+ hours
- Game feels complete (not a demo)
- Friends want to play it
- "One more run" factor is strong

---

## 🚨 Red Flags (Stop If You See These)

### ❌ You're implementing...
- NATS message bus → **WRONG PHASE** (Phase 2)
- WebSocket server → **WRONG PHASE** (Phase 2)
- Lua scripting → **WRONG PHASE** (Phase 3)
- Microservices → **WRONG PHASE** (Phase 2)
- Docker/Podman → **WRONG PHASE** (Phase 2)

### ❌ You're reading docs in...
- `sessions/tesosino-1023/` → Old session, ignore
- `future-multiplayer/` too much → That's Phase 2, not MVP
- Architecture docs about NATS → Phase 2, not relevant

### ✅ You're on track if...
- Building in `src/core/*.py`
- Writing tests in `tests/*.py`
- Playing the game frequently
- Focused on mining/crafting systems
- Code is simple and direct

---

## 🛠️ Development Workflow

### Daily routine:
1. **Pick a task** from MVP_ROADMAP.md
2. **Write a test** (TDD)
3. **Implement** until test passes
4. **Manual test** (play the game!)
5. **Commit** if it works
6. **Repeat**

### Weekly check:
- Am I on schedule? (Week 1-2 = mining, Week 3-4 = crafting)
- Is the game playable?
- Is the code clean?
- Am I having fun building this?

---

## 📞 Need Help?

### Stuck on implementation?
- Read the existing code (it's your best teacher)
- Check MVP_ROADMAP.md for guidance
- Look at architecture/00_ARCHITECTURE_OVERVIEW.md

### Not sure what to build?
- Check MVP_ROADMAP.md (week-by-week tasks)
- Start with "Easy" tasks first
- Build confidence with quick wins

### Tempted to build Phase 2 stuff?
- RESIST! 🛑
- MVP first, multiplayer later
- Simple is better
- YAGNI (You Ain't Gonna Need It)

---

## 🎮 Let's Build!

**Current Task:** Mining System (Week 1-2)

**First Step:** Add OreVein class to `src/core/entities.py`

**Success:** You can see `◆` symbols in the dungeon and survey them!

---

**Ready? Let's go!** 🚀

**Questions?** Check MVP_ROADMAP.md for detailed tasks.

**Lost?** Read architecture/00_ARCHITECTURE_OVERVIEW.md for architecture overview.

**Confused about phases?** MVP = single-player (now), Phase 2 = multiplayer (later).
