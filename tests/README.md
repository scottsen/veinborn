# Brogue Testing Framework

**Status:** ✅ Infrastructure Complete | 🚧 Tests In Progress
**Coverage:** 35% baseline → Target 70%+
**Test Count:** 8 smoke tests (infrastructure verification)

---

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific markers
pytest -m smoke      # Smoke tests only
pytest -m unit       # Unit tests only
pytest -m integration # Integration tests only

# Run specific file
pytest tests/test_infrastructure.py

# Run with verbose output
pytest -v

# Run with print output visible
pytest -s
```

---

## Directory Structure

```
tests/
├── README.md                      # This file
├── conftest.py                    # Shared fixtures (IMPORTANT!)
├── pytest.ini                     # Pytest configuration
├── .coveragerc                    # Coverage configuration
│
├── test_infrastructure.py         # Smoke tests (verify framework works)
│
├── unit/                          # Unit tests (80% of tests)
│   ├── test_entities.py           # TODO: Entity tests
│   ├── test_game_state.py         # TODO: GameState tests
│   ├── test_world.py              # TODO: Map generation tests
│   ├── actions/
│   │   ├── test_move_action.py    # TODO: Movement tests
│   │   ├── test_attack_action.py  # TODO: Combat tests
│   │   ├── test_survey_action.py  # TODO: Survey tests
│   │   └── test_mine_action.py    # TODO: Mining tests
│   └── systems/
│       └── test_ai_system.py      # TODO: AI behavior tests
│
├── integration/                   # Integration tests (15% of tests)
│   ├── test_game_workflows.py     # TODO: Complete game flows
│   ├── test_mining_workflow.py    # TODO: Survey → Mine → Inventory
│   └── test_combat_workflow.py    # TODO: Combat → XP → Level up
│
├── ui/                            # UI tests
│   └── manual_playtesting.md      # TODO: Playtesting checklist
│
├── fixtures/                      # Test data
│   └── sample_maps.py             # TODO: Pre-built maps for testing
│
└── legacy/                        # Old smoke tests (moved here)
    ├── smoke_widgets.py
    └── smoke_textual.py
```

---

## Available Fixtures (conftest.py)

Fixtures make writing tests easy! All fixtures are in `tests/conftest.py`.

### Entity Fixtures

```python
def test_my_feature(fresh_player, weak_goblin, copper_ore):
    """All fixtures are automatically available!"""
    assert fresh_player.hp == 20
    assert weak_goblin.hp == 5
    assert copper_ore.ore_type == "copper"
```

**Available Fixtures:**
- `fresh_player` - Player at full health (20 HP)
- `damaged_player` - Player at 50% health (10/20 HP)
- `weak_goblin` - Weak monster (5 HP, 2 attack)
- `strong_orc` - Strong monster (20 HP, 8 attack)
- `copper_ore` - Copper ore vein (moderate properties)
- `iron_ore` - Iron ore vein (higher hardness)
- `mithril_ore` - Mithril ore vein (high quality)

### Map Fixtures

- `empty_map` - Empty 80x24 map (all walls)
- `simple_room_map` - Map with a 10x10 walkable room

### GameState Fixtures

- `simple_game_state` - Minimal game state (player only)
- `game_state_with_monster` - Game state with player + monster
- `game_state_with_ore` - Game state with player + ore vein
- `new_game` - Fully initialized game (ready to play)

### GameContext Fixtures

- `game_context` - Basic context for action testing
- `combat_context` - Context ready for combat tests
- `mining_context` - Context ready for mining tests

---

## Test Markers

Use markers to run specific test categories:

```python
@pytest.mark.unit
def test_player_movement():
    """Fast, isolated unit test."""
    pass

@pytest.mark.integration
def test_complete_mining_workflow():
    """Integration test across systems."""
    pass

@pytest.mark.smoke
def test_basic_functionality():
    """Smoke test for critical features."""
    pass

@pytest.mark.slow
def test_performance_benchmark():
    """Slow test (> 1 second)."""
    pass
```

**Run tests by marker:**
```bash
pytest -m unit          # Fast unit tests only
pytest -m integration   # Integration tests only
pytest -m smoke         # Smoke tests only
pytest -m "not slow"    # Exclude slow tests
```

---

## Writing Tests - Best Practices

### 1. Test Behavior, Not Implementation

```python
# ✅ GOOD - Tests what should happen
def test_player_dies_at_zero_hp(fresh_player):
    """Player should be dead when HP reaches 0."""
    fresh_player.take_damage(100)
    assert not fresh_player.is_alive

# ❌ BAD - Tests internal implementation
def test_player_hp_math(fresh_player):
    """Check HP subtraction."""
    fresh_player.take_damage(5)
    assert fresh_player.hp == fresh_player.max_hp - 5  # Brittle!
```

### 2. Use Fixtures

```python
# ✅ GOOD - Use fixtures
def test_combat(fresh_player, weak_goblin):
    result = attack(fresh_player, weak_goblin)
    assert not weak_goblin.is_alive

# ❌ BAD - Manual setup
def test_combat():
    player = Player(hp=20, max_hp=20, attack=5, defense=2)
    goblin = Monster(name="Goblin", hp=5, ...)  # Verbose!
    # ... test code
```

### 3. Clear Test Names

```python
# ✅ GOOD - Descriptive names
def test_mining_requires_survey_first():
    """Cannot mine ore without surveying."""
    pass

# ❌ BAD - Vague names
def test_mining():
    """Test mining."""
    pass
```

### 4. One Assertion Per Test (Usually)

```python
# ✅ GOOD - Focused test
def test_player_takes_damage(fresh_player):
    """Player HP decreases when damaged."""
    initial_hp = fresh_player.hp
    fresh_player.take_damage(5)
    assert fresh_player.hp == initial_hp - 5

# ⚠️ OK - Related assertions
def test_player_death(fresh_player):
    """Player dies at 0 HP."""
    fresh_player.take_damage(100)
    assert fresh_player.hp == 0
    assert not fresh_player.is_alive  # Related assertion
```

---

## Test Example Templates

### Unit Test Example

```python
# tests/unit/test_entities.py
import pytest
from core.entities import Player

class TestPlayer:
    """Unit tests for Player entity."""

    def test_player_creation(self, fresh_player):
        """Player initializes with correct values."""
        assert fresh_player.hp == 20
        assert fresh_player.max_hp == 20
        assert fresh_player.is_alive

    def test_player_takes_damage(self, fresh_player):
        """Player HP decreases when damaged."""
        fresh_player.take_damage(5)
        assert fresh_player.hp == 15

    def test_player_hp_cannot_go_negative(self, fresh_player):
        """Player HP stops at 0, not negative."""
        fresh_player.take_damage(100)
        assert fresh_player.hp == 0
```

### Integration Test Example

```python
# tests/integration/test_mining_workflow.py
import pytest
from core.entities import EntityType

@pytest.mark.integration
def test_complete_mining_workflow(new_game):
    """Test full mining from survey to inventory."""
    game = new_game

    # Find ore vein
    ore = next(
        e for e in game.state.entities.values()
        if e.entity_type == EntityType.ORE_VEIN
    )

    # Move player adjacent
    game.state.player.x = ore.x + 1
    game.state.player.y = ore.y

    # Survey ore
    game.handle_player_action('survey')
    assert ore.get_stat('surveyed')

    # Mine ore (3-5 turns)
    turns = 0
    while not ore.get_stat('mined', False) and turns < 10:
        game.handle_player_action('mine')
        turns += 1

    # Verify
    assert len(game.state.player.inventory) > 0
```

---

## Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Check specific threshold
pytest --cov=src --cov-fail-under=70
```

**Current Coverage:** 35.18%
**Target Coverage:** 70%+ for core modules

---

## Next Steps

### Phase 2: Unit Tests (Target: 50% coverage)

1. **Entity Tests** (`tests/unit/test_entities.py`)
   - Player: creation, damage, healing, death, XP, inventory
   - Monster: creation, stats, AI behavior
   - OreVein: properties, surveying, mining

2. **Action Tests** (`tests/unit/actions/`)
   - MoveAction: validation, collision, map boundaries
   - AttackAction: damage calculation, kills, XP rewards
   - SurveyAction: ore revelation, adjacency checks
   - MineAction: multi-turn, progress tracking, inventory

3. **GameState Tests** (`tests/unit/test_game_state.py`)
   - State initialization
   - Entity management
   - Turn counting
   - Game over conditions

### Phase 3: Integration Tests (Target: 70% coverage)

1. **Game Workflows** (`tests/integration/test_game_workflows.py`)
   - New game initialization
   - Complete turn cycles
   - Game over and restart

2. **Feature Workflows**
   - Mining: Survey → Mine (multi-turn) → Inventory
   - Combat: Attack → Death → XP → Level up
   - Movement: Explore → Find ore → Combat monsters

### Phase 4: Performance & Polish

1. Performance benchmarks
2. Edge case testing
3. Manual playtesting checklist
4. Documentation updates

---

## Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Run one test and show print output
pytest tests/unit/test_entities.py::test_player_death -s

# Run tests in verbose mode
pytest -vv

# Show test execution times
pytest --durations=10
```

---

## Continuous Integration (Future)

```yaml
# .github/workflows/test.yml (example)
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Resources

- **Testing Guide:** `docs/architecture/MVP_TESTING_GUIDE.md`
- **Code Standards:** `docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md`
- **Design Doc:** `sessions/clearing-squall-1024/TESTING_FRAMEWORK_DESIGN.md`
- **Pytest Docs:** https://docs.pytest.org/

---

**Questions?** Check `conftest.py` for all available fixtures and examples!

✅ Infrastructure is ready - now let's write tests!
