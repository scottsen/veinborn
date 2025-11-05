# Brogue MVP Development Guidelines

**Document Type:** Development Standards (MVP Phase)
**Audience:** Developers implementing MVP
**Status:** Active
**Last Updated:** 2025-10-24

---

## Overview

This document defines development standards for the Brogue MVP (single-player Python game).

**For Phase 2 (multiplayer) guidelines:** See `/docs/future-multiplayer/DEVELOPMENT_GUIDELINES.md`

---

## Technology Stack (MVP Only)

### Core Dependencies

```txt
# requirements.txt (MVP)

# ===== Core Infrastructure =====
python>=3.10

# ===== UI =====
textual>=0.45.0            # Terminal UI framework
rich>=13.7.0               # Rich terminal output

# ===== Data & Content =====
pyyaml>=6.0                # YAML content loading
pydantic>=2.0              # Type-safe models (optional)

# ===== Development & Testing =====
pytest>=7.4.0
pytest-cov>=4.1.0
```

**What we're NOT using yet:**
- ❌ NATS (Phase 2 - multiplayer messaging)
- ❌ PostgreSQL (Phase 2 - database)
- ❌ WebSockets (Phase 2 - client-server)
- ❌ Prometheus (Phase 2 - metrics)

---

## Project Structure

```
projects/brogue/
├── src/
│   └── core/
│       ├── game.py           # Game loop, state management
│       ├── entities.py       # Player, monsters, items
│       ├── world.py          # Map generation (BSP algorithm)
│       ├── recipes.py        # Crafting system (TODO)
│       ├── legacy.py         # Legacy Vault (TODO)
│       └── save.py           # Save/load (TODO)
│
├── data/
│   ├── recipes/              # Recipe YAML files (TODO)
│   ├── monsters/             # Monster YAML files (TODO)
│   └── saves/                # Save games (TODO)
│
├── tests/                    # pytest tests
│   ├── test_entities.py
│   ├── test_world.py
│   └── test_mining.py
│
├── run_textual.py            # Main entry point
└── requirements.txt
```

---

## Code Style

### Python Version & Type Hints (Required)

```python
# ✅ Good - typed
def process_move(player: Player, dx: int, dy: int) -> bool:
    """Move player by offset.

    Args:
        player: The player entity
        dx: X offset (-1, 0, or 1)
        dy: Y offset (-1, 0, or 1)

    Returns:
        True if move was successful, False otherwise
    """
    new_x = player.x + dx
    new_y = player.y + dy

    if not is_walkable(new_x, new_y):
        return False

    player.x = new_x
    player.y = new_y
    return True

# ❌ Bad - untyped
def process_move(player, dx, dy):
    # No type hints, no docstring
    new_x = player.x + dx
    new_y = player.y + dy
    if not is_walkable(new_x, new_y):
        return False
    player.x = new_x
    player.y = new_y
    return True
```

### Formatting Standards

**Use Python standard conventions:**
- **PEP 8** style guide
- **4 spaces** for indentation (never tabs)
- **Line length**: 120 characters max
- **Imports**: Standard library → Third-party → Local
- **Blank lines**: 2 before classes, 1 before methods

### Naming Conventions

```python
# Classes: PascalCase
class OreVein:
    pass

# Functions: snake_case
def generate_dungeon(width: int, height: int):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_DUNGEON_SIZE = 100

# Private: _leading_underscore
def _internal_helper():
    pass
```

---

## Testing Strategy

### Unit Tests (Primary)

Test game logic in isolation using pytest:

```python
# tests/test_entities.py
import pytest
from src.core.entities import Player, Monster

def test_player_takes_damage():
    """Player HP decreases when damaged."""
    player = Player(hp=100, max_hp=100)
    player.take_damage(30)
    assert player.hp == 70

def test_player_cannot_go_below_zero_hp():
    """Player HP stops at 0."""
    player = Player(hp=10, max_hp=100)
    player.take_damage(50)
    assert player.hp == 0
    assert not player.is_alive

def test_monster_pathfinding():
    """Monster moves toward target."""
    monster = Monster(x=0, y=0)
    target_x, target_y = 5, 5

    # Move toward target
    dx, dy = monster.get_move_direction(target_x, target_y)

    assert dx in (-1, 0, 1)
    assert dy in (-1, 0, 1)
    # Should move closer (not perfect, just closer)
```

### Integration Tests (Secondary)

Test multiple systems working together:

```python
# tests/test_mining_workflow.py
from src.core.game import Game

def test_full_mining_workflow():
    """Test complete mining workflow."""
    game = Game()

    # 1. Generate dungeon with ore
    game.generate_new_dungeon()
    ore_vein = game.map.get_ore_at(10, 10)
    assert ore_vein is not None

    # 2. Survey ore
    game.handle_survey_action(10, 10)
    assert ore_vein.is_surveyed

    # 3. Mine ore (takes 4 turns)
    for turn in range(4):
        game.handle_mining_action(10, 10)

    # 4. Ore added to inventory
    assert len(game.player.inventory.ores) == 1
    assert ore_vein.is_mined
```

### Manual Testing (Critical!)

**Play the game frequently:**

```bash
# Run the game
python3 run_textual.py

# Test your feature by playing
# - Does it work as expected?
# - Are there edge cases?
# - Is it fun?
```

**Manual testing checklist:**
- ✅ Feature works in normal case
- ✅ Feature handles edge cases (what if player dies while mining?)
- ✅ Error messages are clear
- ✅ UI updates correctly
- ✅ Game doesn't crash

---

## Running Tests

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test file
python3 -m pytest tests/test_entities.py

# Run specific test
python3 -m pytest tests/test_entities.py::test_player_takes_damage

# Run with coverage
python3 -m pytest --cov=src tests/

# Run with verbose output
python3 -m pytest -v tests/
```

---

## Logging (Simple for MVP)

### Use Python's Built-in Logging

```python
# src/core/game.py
import logging

logger = logging.getLogger(__name__)

class Game:
    def __init__(self):
        logger.info("Game initialized")
        self.player = Player()

    def process_turn(self):
        logger.debug(f"Processing turn {self.turn_count}")
        # ...

    def handle_error(self, error: Exception):
        logger.error(f"Game error: {error}", exc_info=True)
```

### Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Development details | Turn counts, state dumps |
| **INFO** | Normal operations | Game started, level generated |
| **WARNING** | Unusual but not error | High ore quality found |
| **ERROR** | Operation failed | Save failed, map generation error |

### Configure Logging

```python
# run_textual.py
import logging

logging.basicConfig(
    level=logging.INFO,  # DEBUG for development, INFO for normal
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('brogue.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
```

**For Phase 2 (structured logging, metrics):** See `/docs/future-multiplayer/LOGGING_OBSERVABILITY.md`

---

## Git Workflow

### Branch Naming

```
feature/add-mining-system
bugfix/fix-combat-crash
refactor/clean-up-entities
docs/update-readme
```

### Commit Messages

```
feat: Add ore vein generation to dungeon

- Implement OreVein class with 5 properties
- Add ore spawning to BSP algorithm
- Configure spawn rates by floor depth

Refs: #123
```

**Format:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring
- `docs:` Documentation
- `test:` Adding tests
- `chore:` Maintenance

### Before Committing

```bash
# 1. Run tests
python3 -m pytest tests/

# 2. Check code still works
python3 run_textual.py

# 3. Review changes
git diff

# 4. Commit
git add src/core/world.py tests/test_world.py
git commit -m "feat: Add ore vein generation"
```

---

## Common Patterns

### Game Loop Pattern

```python
# src/core/game.py
class Game:
    def run(self):
        """Main game loop."""
        while self.player.is_alive:
            # 1. Get player input
            action = self.get_player_input()

            # 2. Process player action
            if action == "move":
                self.handle_move()
            elif action == "mine":
                self.handle_mining()
            # ...

            # 3. Monsters take turns
            self.process_monster_turns()

            # 4. Update display
            self.ui.refresh()

            self.turn_count += 1
```

### Entity Pattern

```python
# src/core/entities.py
from dataclasses import dataclass

@dataclass
class Player:
    """Player character."""
    hp: int
    max_hp: int
    x: int
    y: int

    def take_damage(self, amount: int):
        """Apply damage to player."""
        self.hp = max(0, self.hp - amount)

    @property
    def is_alive(self) -> bool:
        """Check if player is alive."""
        return self.hp > 0
```

### YAML Content Loading

```python
# src/core/content.py
import yaml
from pathlib import Path

def load_monster_data(monster_id: str) -> dict:
    """Load monster definition from YAML."""
    path = Path(f"data/monsters/{monster_id}.yaml")
    with open(path) as f:
        return yaml.safe_load(f)

# Usage
goblin_data = load_monster_data("goblin")
goblin = Monster(
    name=goblin_data["name"],
    hp=goblin_data["stats"]["hp"],
    attack=goblin_data["stats"]["attack"]
)
```

---

## Development Workflow

### Daily Development Loop

1. **Pick a task** from `docs/MVP_ROADMAP.md`
2. **Write a test** (TDD - test first!)
3. **Implement** until test passes
4. **Manual test** (play the game!)
5. **Commit** if it works
6. **Repeat**

### Example: Adding Mining System

```bash
# 1. Create test first
vim tests/test_mining.py
# Write: test_ore_vein_spawns_in_dungeon()

# 2. Run test (it fails)
pytest tests/test_mining.py
# ❌ FAILED - OreVein class doesn't exist

# 3. Implement OreVein
vim src/core/entities.py
# Add: class OreVein

# 4. Run test again
pytest tests/test_mining.py
# ✅ PASSED

# 5. Manual test
python3 run_textual.py
# Look for ◆ symbols in dungeon

# 6. Commit
git add src/core/entities.py tests/test_mining.py
git commit -m "feat: Add OreVein entity class"
```

---

## Performance Guidelines

### Keep It Simple (MVP)

```python
# ✅ Good - simple and clear
def get_monsters_in_range(monsters: list[Monster], x: int, y: int, radius: int):
    """Get monsters within radius."""
    result = []
    for monster in monsters:
        dx = monster.x - x
        dy = monster.y - y
        distance = (dx * dx + dy * dy) ** 0.5
        if distance <= radius:
            result.append(monster)
    return result

# ❌ Don't over-optimize for MVP
# (No need for spatial indexing, quadtrees, etc. unless performance is actually bad)
```

**Optimization rule for MVP:**
- If it runs smoothly (60 FPS), it's fast enough
- Profile before optimizing
- Simple code > clever code

---

## Common Mistakes to Avoid

### ❌ Don't Build Phase 2 Infrastructure

```python
# ❌ Bad - building multiplayer infrastructure in MVP
import nats
import asyncpg

# MVP doesn't need NATS, PostgreSQL, etc.
```

### ❌ Don't Over-Engineer

```python
# ❌ Bad - complex abstraction for simple need
class EntityFactory:
    def __init__(self, registry: EntityRegistry, validator: EntityValidator):
        self.registry = registry
        self.validator = validator

    def create(self, entity_type: EntityType, **kwargs):
        # 50 lines of factory logic...

# ✅ Good - simple and direct
player = Player(hp=10, max_hp=10, x=5, y=5)
```

### ❌ Don't Skip Testing

```python
# ❌ Bad - no tests, just hope it works
def complex_ore_generation(floor, seed, multiplier):
    # 100 lines of complex logic
    # No tests! 🔥

# ✅ Good - test your logic
def test_ore_quality_increases_with_floor():
    ore1 = generate_ore(floor=1)
    ore10 = generate_ore(floor=10)
    assert ore10.average_quality > ore1.average_quality
```

---

## Resources

### Documentation
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Textual Documentation](https://textual.textualize.io/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)

### Brogue Docs
- `docs/START_HERE.md` - Project overview
- `docs/MVP_ROADMAP.md` - What to build next
- `docs/MVP_CURRENT_FOCUS.md` - Current implementation focus
- `docs/architecture/00_ARCHITECTURE_OVERVIEW.md` - Technical architecture

---

## Quick Reference

```bash
# Run game
python3 run_textual.py

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_entities.py::test_player_takes_damage

# Check code works before committing
pytest && python3 run_textual.py
```

---

**For Phase 2 (multiplayer) development:** See `/docs/future-multiplayer/DEVELOPMENT_GUIDELINES.md`

**Questions?** Check the docs or ask in the project chat.

**Happy coding!** 🎮
