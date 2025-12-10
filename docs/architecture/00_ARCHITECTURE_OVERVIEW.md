# Veinborn MVP Architecture Overview

**Document Type:** Architecture Overview
**Audience:** Developers implementing the MVP
**Status:** Active - Current Development Phase
**Last Updated:** 2025-10-24

---

## ⚠️ IMPORTANT: This is MVP Architecture

**Current Phase:** MVP (Single-Player)
**Timeline:** 4-6 weeks
**Focus:** Get mining/crafting working in single-player

**NOT building yet:**
- ❌ Multiplayer (Phase 2, 8-12 weeks out)
- ❌ NATS message bus (Phase 2)
- ❌ Microservices (Phase 2)
- ❌ Lua scripting (Phase 3)
- ❌ WebSocket clients (Phase 2)

**For Phase 2 architecture:** See `/docs/future-multiplayer/`

---

## Executive Summary

**Veinborn MVP** is a single-player terminal roguelike with mining and crafting systems.

**Architecture Principles:**
- **Simple Python Game Loop** - Direct function calls, no message bus
- **Textual UI** - Terminal-based interface (already working)
- **YAML-Driven Content** - Recipes, monsters defined in YAML
- **Clean Code** - Type hints, clear separation of concerns
- **Testable** - Unit tests for game logic

**Technology Stack:**
- Python 3.10+ (type hints, dataclasses)
- Textual (terminal UI framework)
- PyYAML (content loading)
- pytest (testing)

---

## Core Architecture

### Current Game Loop

```python
# src/core/game.py (simplified)
class Game:
    def __init__(self):
        self.player = Player()
        self.map = generate_dungeon()
        self.monsters = spawn_monsters(self.map)
        self.turn_count = 0

    def run(self):
        while self.player.is_alive:
            # 1. Get player input
            action = self.ui.get_input()

            # 2. Process player action
            self.handle_player_action(action)

            # 3. Monsters take turns
            for monster in self.monsters:
                self.handle_monster_turn(monster)

            # 4. Update UI
            self.ui.refresh()

            self.turn_count += 1
```

**Key Characteristics:**
- ✅ Simple and direct
- ✅ Easy to understand
- ✅ Easy to debug
- ✅ No network complexity
- ✅ Works perfectly for single-player

---

## Project Structure

```
projects/veinborn/
├── src/
│   ├── core/              # Game logic
│   │   ├── game.py        # Game loop, state management
│   │   ├── entities.py    # Player, monsters, items
│   │   ├── world.py       # Map generation (BSP algorithm)
│   │   ├── recipes.py     # Crafting system (TODO)
│   │   ├── legacy.py      # Legacy Vault (TODO)
│   │   └── save.py        # Save/load (TODO)
│   │
│   └── ui/
│       └── textual/       # Textual UI widgets
│           ├── app.py
│           └── widgets/
│
├── data/
│   ├── recipes/           # Recipe YAML files (TODO)
│   └── saves/             # Save games (TODO)
│
├── tests/                 # pytest tests
│
└── run_textual.py         # Main entry point
```

---

## Core Systems

### 1. Game State Management

**File:** `src/core/game.py`

```python
@dataclass
class GameState:
    """Complete game state (can be serialized for save/load)"""
    player: Player
    monsters: list[Monster]
    map: Map
    inventory: list[Item]
    turn_count: int
    floor: int

    def to_dict(self) -> dict:
        """Serialize for saving"""
        return {
            'player': self.player.to_dict(),
            'monsters': [m.to_dict() for m in self.monsters],
            # ...
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """Deserialize from save file"""
        # ...
```

**Why simple state management:**
- Easy to save/load (just serialize to JSON)
- Easy to test (create GameState, test logic)
- Easy to understand (no hidden state)
- Can refactor to message-based later (Phase 2)

### 2. Entity System

**File:** `src/core/entities.py`

```python
class Player:
    """Player character"""
    hp: int
    max_hp: int
    attack: int
    defense: int
    x: int
    y: int
    inventory: list[Item]

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def take_damage(self, amount: int):
        self.hp -= amount

class Monster:
    """Enemy monsters"""
    name: str
    hp: int
    attack: int
    defense: int
    x: int
    y: int

    def move_toward(self, target_x: int, target_y: int):
        # Simple pathfinding
```

**Current state:** ✅ Working
**Next step:** Add OreVein class for mining system

**Future:** Could refactor to use Entity base class (see `BASE_CLASS_ARCHITECTURE.md`) but not required for MVP.

### 3. Map Generation

**File:** `src/core/world.py`

**Algorithm:** Binary Space Partitioning (BSP)

```python
def generate_dungeon(width: int, height: int) -> Map:
    """Generate dungeon using BSP algorithm"""
    # 1. Partition space recursively
    root = Leaf(0, 0, width, height)
    root.split_recursive()

    # 2. Create rooms in leaf nodes
    rooms = []
    for leaf in root.get_leaves():
        room = create_room(leaf)
        rooms.append(room)

    # 3. Connect rooms with corridors
    connect_rooms(rooms)

    return Map(rooms)
```

**Current state:** ✅ Working perfectly
**Next step:** Add ore vein spawning (Week 1-2)

### 4. UI Framework

**Framework:** Textual (terminal UI)

**Widgets:**
- MapWidget: Dungeon viewport
- StatusBar: HP, turn count, position
- MessageLog: Game events
- Sidebar: Player stats, nearby monsters

**Current state:** ✅ Working perfectly
**Next step:** Add crafting widget, ore survey widget

---

## Adding New Systems (MVP Phase 1)

### Week 1-2: Mining System

**New classes:**
```python
# src/core/entities.py
class OreVein:
    """Ore vein that can be mined"""
    ore_type: str  # "copper", "iron", "mithril", "adamantite"
    x: int
    y: int
    properties: dict  # hardness, conductivity, malleability, purity, density
    mining_turns_required: int
```

**New actions:**
```python
# src/core/game.py
def handle_survey_action(self, target_x: int, target_y: int):
    """Survey ore vein (takes 1 turn)"""
    ore = self.map.get_ore_at(target_x, target_y)
    self.ui.show_ore_properties(ore)

def handle_mining_action(self, target_x: int, target_y: int):
    """Mine ore (takes 3-5 turns, player vulnerable)"""
    ore = self.map.get_ore_at(target_x, target_y)
    self.player.start_mining(ore)
    # Player can't move/attack while mining
    # Mining progresses over multiple turns
```

### Week 3: Crafting System

**New files:**
- `data/recipes/*.yaml` - Recipe definitions
- `src/core/recipes.py` - Recipe loader

**Recipe format:**
```yaml
# data/recipes/simple_sword.yaml
name: "Simple Sword"
type: weapon
required_ore: 1
ore_types: [copper, iron]
base_damage: 3
stat_formula: "base_damage + (ore.hardness * ore.purity / 100)"
crafting_time: 2
```

**Integration:**
```python
# src/core/game.py
def handle_craft_action(self, recipe_id: str, ore_id: str):
    """Craft item from recipe + ore"""
    recipe = self.recipes.get(recipe_id)
    ore = self.player.inventory.get_ore(ore_id)

    item = craft_item(recipe, ore)
    self.player.inventory.add(item)
```

### Week 4: Meta-Progression

**New files:**
- `src/core/legacy.py` - Legacy Vault
- `src/core/save.py` - Save/load system

**Legacy Vault:**
```python
class LegacyVault:
    """Persistent storage for rare ore (survives death)"""
    max_ores: int = 10
    ores: list[Ore]

    def save_ore_on_death(self, player_inventory: list[Ore]):
        """Save rare ore (purity >= 80) to vault"""
        rare_ores = [ore for ore in player_inventory if ore.purity >= 80]
        for ore in rare_ores:
            if len(self.ores) < self.max_ores:
                self.ores.append(ore)

    def withdraw_ore(self) -> Optional[Ore]:
        """Withdraw 1 ore at run start"""
        if self.ores:
            return self.ores.pop(0)
        return None
```

**Save/Load:**
```python
def save_game(state: GameState, slot: int):
    """Save game to JSON file"""
    data = state.to_dict()
    with open(f'data/saves/save_{slot}.json', 'w') as f:
        json.dump(data, f, indent=2)

def load_game(slot: int) -> GameState:
    """Load game from JSON file"""
    with open(f'data/saves/save_{slot}.json', 'r') as f:
        data = json.load(f)
    return GameState.from_dict(data)
```

---

## Testing Strategy (MVP)

### Unit Tests

**Test game logic in isolation:**

```python
# tests/test_entities.py
def test_player_takes_damage():
    player = Player(hp=100, max_hp=100)
    player.take_damage(30)
    assert player.hp == 70

def test_monster_pathfinding():
    monster = Monster(x=0, y=0)
    monster.move_toward(target_x=5, target_y=5)
    # Assert monster moved closer to target
```

**Test crafting:**
```python
# tests/test_recipes.py
def test_craft_sword_from_ore():
    ore = Ore(ore_type="iron", hardness=78, purity=82)
    recipe = load_recipe("simple_sword")

    sword = craft_item(recipe, ore)

    # base_damage + (hardness * purity / 100)
    # 3 + (78 * 0.82) = 3 + 63.96 = ~67 damage
    assert sword.damage == pytest.approx(67, abs=1)
```

### Integration Tests

**Test multiple systems together:**

```python
# tests/test_mining_workflow.py
def test_full_mining_workflow():
    game = Game()
    ore_vein = game.map.get_ore_at(10, 10)

    # Survey ore
    game.handle_survey_action(10, 10)
    assert ore_vein.is_surveyed

    # Mine ore (takes 4 turns)
    for _ in range(4):
        game.handle_mining_action(10, 10)

    # Ore added to inventory
    assert len(game.player.inventory.ores) == 1
    assert ore_vein.is_mined
```

### Manual Testing

**Playtest the game:**
1. Run `python3 run_textual.py`
2. Test each feature as you build it
3. Check edge cases (what if player dies while mining?)
4. Verify UI updates correctly

**Goal:** Every feature should be playable and fun before moving to next feature.

---

## Content System (YAML-Based)

### Why YAML?

- ✅ Human-readable
- ✅ Easy for non-programmers to edit
- ✅ Safe (no code execution)
- ✅ Git-friendly (version control works)
- ✅ Can be loaded at runtime (no recompile)

### Example: Monster Definitions

```yaml
# data/monsters/goblin.yaml
id: goblin
name: "Goblin"
glyph: "g"
color: green
stats:
  hp: 6
  attack: 3
  defense: 1
loot:
  gold: [1, 5]  # 1-5 gold
  chance: 1.0   # 100% drop rate
```

**Loading:**
```python
# src/core/content.py
def load_monster_data(monster_id: str) -> dict:
    with open(f'data/monsters/{monster_id}.yaml') as f:
        return yaml.safe_load(f)

def spawn_monster(monster_id: str, x: int, y: int) -> Monster:
    data = load_monster_data(monster_id)
    return Monster(
        name=data['name'],
        hp=data['stats']['hp'],
        attack=data['stats']['attack'],
        # ...
    )
```

---

## Development Workflow

### Adding a New Feature

1. **Read the design:** `docs/VEINBORN_CONSOLIDATED_DESIGN.md`
2. **Check the roadmap:** `docs/MVP_ROADMAP.md`
3. **Understand existing code:** Read relevant files in `src/core/`
4. **Write tests first** (TDD): Create test file in `tests/`
5. **Implement:** Add code to make tests pass
6. **Manual test:** Play the game, verify it works
7. **Document:** Update docs if needed

### Code Style

- Python 3.10+ with type hints
- Use dataclasses for data structures
- Keep functions small and focused
- Comment complex logic
- Write docstrings for public APIs

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test file
python3 -m pytest tests/test_entities.py

# Run with coverage
python3 -m pytest --cov=src tests/
```

---

## Future Refactoring (Phase 2)

**When MVP is complete**, we'll refactor to support multiplayer:

### Changes for Phase 2:
1. **Replace direct function calls** → Event-driven messages (NATS)
2. **Extract game logic** → GameStateService (microservice)
3. **Add network layer** → ConnectionService (WebSocket gateway)
4. **Add persistence** → PersistenceService (PostgreSQL)
5. **Add Lua scripting** → For entity behaviors

**But for MVP:** Keep it simple! Direct function calls work perfectly for single-player.

**Complete Phase 2 architecture:** See `/docs/future-multiplayer/`

---

## Key Architecture Documents

### For MVP Implementation (Read These)
- `START_HERE.md` - Onboarding guide
- `MVP_ROADMAP.md` - What to build, week by week
- `00_ARCHITECTURE_OVERVIEW.md` (this doc) - How it works
- `BASE_CLASS_ARCHITECTURE.md` - Optional: Clean base classes
- `CONTENT_SYSTEM.md` - YAML content loading
- `DEVELOPMENT_GUIDELINES.md` - Code style, testing

### For Future Planning (Don't Build Yet)
- `future-multiplayer/` - Phase 2 multiplayer architecture
- `LUA_INTEGRATION_STRATEGY.md` - Phase 3 scripting
- `LOGGING_OBSERVABILITY.md` - Phase 2 monitoring

---

## Common Questions

### Q: Why not use the Phase 2 architecture from the start?

**A:** YAGNI (You Ain't Gonna Need It)

Phase 2 architecture adds:
- NATS message bus (complex setup)
- Microservices (deployment complexity)
- WebSocket protocol (network complexity)
- Event-driven design (harder to debug)

**For MVP:** None of this is needed! Simple Python game loop works perfectly.

**When to refactor:** After MVP is complete and we're ready for multiplayer.

### Q: Should I use Entity base class?

**A:** Optional, but recommended

See `BASE_CLASS_ARCHITECTURE.md` for complete design. Main benefits:
- Less code duplication (Player and Monster share code)
- Easier to add OreVein class (just extend Entity)
- Easier to test (uniform interface)
- Makes Phase 2 refactor easier (but works without it)

**Time cost:** 2-3 hours to refactor
**Benefit:** Cleaner code, easier mining implementation

### Q: What about Lua scripting?

**A:** Not for MVP!

Lua scripting is Phase 3 (after multiplayer). For MVP:
- All game logic in Python
- All content in YAML
- No scripting needed

See `LUA_INTEGRATION_STRATEGY.md` for future planning, but don't implement yet.

---

## Success Criteria

**MVP is complete when:**
- ✅ Player can mine ore (survey properties, mine over multiple turns)
- ✅ Player can craft items from ore (recipes loaded from YAML)
- ✅ Crafted items have calculated stats (ore properties × recipe formula)
- ✅ Legacy Vault saves rare ore on death
- ✅ Game can save/load
- ✅ 15-20 monster types across 10+ floors
- ✅ Boss encounters
- ✅ Game is fun and replayable

**Ready for Phase 2 when:**
- ✅ All MVP features complete
- ✅ Code is clean and tested
- ✅ Performance is good (60 FPS)
- ✅ No critical bugs

---

## References

- [START_HERE.md](../START_HERE.md) - Start here if new to project
- [MVP_ROADMAP.md](../MVP_ROADMAP.md) - Implementation tasks
- [VEINBORN_CONSOLIDATED_DESIGN.md](../VEINBORN_CONSOLIDATED_DESIGN.md) - Game design
- [future-multiplayer/](../future-multiplayer/) - Phase 2 architecture
- [BASE_CLASS_ARCHITECTURE.md](./BASE_CLASS_ARCHITECTURE.md) - Optional: Clean base classes
- [CONTENT_SYSTEM.md](./CONTENT_SYSTEM.md) - YAML content system
- [DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md) - Code style

---

**Next Step:** Read `MVP_ROADMAP.md` and pick a task!

🎮 Let's build something awesome (and keep it simple for MVP).
