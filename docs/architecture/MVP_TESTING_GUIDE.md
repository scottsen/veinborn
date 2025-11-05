# Brogue MVP Testing Guide

**Document Type:** Testing Guide (MVP Phase)
**Audience:** Developers implementing MVP
**Status:** Active
**Last Updated:** 2025-10-24

---

## Overview

This guide explains how to test the Brogue MVP (single-player Python game).

**For Phase 2 (async, integration, load testing):** See `/docs/future-multiplayer/DEVELOPMENT_GUIDELINES.md`

---

## Testing Strategy

### Test Pyramid

```
         /\
        /  \     E2E Tests (Manual)
       /----\    - Play the game!
      /      \   - Does it feel good?
     /--------\
    /   Unit   \ Integration Tests
   /   Tests    \ - Systems working together
  /--------------\
```

**Bottom (Unit Tests - 80% of tests):**
- Fast, isolated, many tests
- Test game logic directly
- No UI, no file I/O

**Middle (Integration Tests - 15% of tests):**
- Test systems working together
- Simulate game workflows
- Test critical paths

**Top (E2E Tests - 5% of tests):**
- Manual playtesting
- Full game experience
- Fun factor assessment

---

## Unit Testing

### Test Philosophy

**Test behavior, not implementation:**

```python
# ✅ Good - tests behavior
def test_player_dies_at_zero_hp():
    """Player should be dead when HP reaches 0."""
    player = Player(hp=10, max_hp=100)
    player.take_damage(15)
    assert not player.is_alive

# ❌ Bad - tests implementation
def test_player_hp_math():
    """Check HP subtraction math."""
    player = Player(hp=10, max_hp=100)
    player.take_damage(5)
    assert player.hp == player.max_hp - 95  # Brittle!
```

---

### Testing Entities

```python
# tests/test_entities.py
import pytest
from src.core.entities import Player, Monster, OreVein

class TestPlayer:
    """Tests for Player entity."""

    def test_player_creation(self):
        """Player initializes with correct values."""
        player = Player(hp=20, max_hp=20, attack=5, defense=2)
        assert player.hp == 20
        assert player.max_hp == 20
        assert player.is_alive

    def test_player_takes_damage(self):
        """Player HP decreases when damaged."""
        player = Player(hp=100, max_hp=100)
        player.take_damage(30)
        assert player.hp == 70

    def test_player_hp_cannot_go_negative(self):
        """Player HP stops at 0, not negative."""
        player = Player(hp=10, max_hp=100)
        player.take_damage(50)
        assert player.hp == 0

    def test_player_death_at_zero_hp(self):
        """Player is dead when HP reaches 0."""
        player = Player(hp=1, max_hp=100)
        assert player.is_alive
        player.take_damage(1)
        assert not player.is_alive

    def test_player_healing(self):
        """Player can heal but not exceed max HP."""
        player = Player(hp=50, max_hp=100)
        player.heal(30)
        assert player.hp == 80

        player.heal(50)  # Over-heal
        assert player.hp == 100  # Capped at max

class TestMonster:
    """Tests for Monster entity."""

    def test_monster_moves_toward_target(self):
        """Monster calculates move direction toward target."""
        monster = Monster(x=0, y=0)

        # Target is east and south
        dx, dy = monster.get_move_direction(target_x=5, target_y=5)

        # Should move toward target (not perfect pathing)
        assert dx in (-1, 0, 1)
        assert dy in (-1, 0, 1)
        assert not (dx == 0 and dy == 0)  # Should move

    def test_monster_attacks_when_adjacent(self):
        """Monster attacks when next to player."""
        monster = Monster(x=5, y=5, attack=10)
        player = Player(x=6, y=5, hp=50, max_hp=50, defense=2)

        # Monster is adjacent
        assert monster.is_adjacent_to(player.x, player.y)

        # Attack
        damage = monster.calculate_damage(player)
        assert damage > 0  # Should do some damage

class TestOreVein:
    """Tests for OreVein entity."""

    def test_ore_vein_properties_in_range(self):
        """Ore properties are within 0-100 range."""
        ore = OreVein(
            hardness=75,
            conductivity=60,
            malleability=80,
            purity=90,
            density=50
        )

        assert 0 <= ore.hardness <= 100
        assert 0 <= ore.conductivity <= 100
        assert 0 <= ore.malleability <= 100
        assert 0 <= ore.purity <= 100
        assert 0 <= ore.density <= 100

    def test_ore_quality_calculation(self):
        """Ore quality is average of all properties."""
        ore = OreVein(
            hardness=100,
            conductivity=100,
            malleability=100,
            purity=100,
            density=100
        )
        assert ore.average_quality == 100

        ore2 = OreVein(
            hardness=50,
            conductivity=50,
            malleability=50,
            purity=50,
            density=50
        )
        assert ore2.average_quality == 50

    def test_ore_vein_starts_unsurveyed(self):
        """Ore veins start in unsurveyed state."""
        ore = OreVein.generate_random()
        assert not ore.is_surveyed
        assert not ore.is_mined

    def test_ore_vein_survey_reveals_properties(self):
        """Surveying reveals exact properties."""
        ore = OreVein.generate_random()
        ore.survey()

        assert ore.is_surveyed
        # Properties should be visible now
        assert ore.hardness is not None
```

---

### Testing Game Logic

```python
# tests/test_combat.py
from src.core.entities import Player, Monster
from src.core.combat import CombatSystem

def test_combat_damage_calculation():
    """Damage is attack minus defense, minimum 1."""
    attacker = Player(attack=10, defense=0)
    defender = Monster(attack=0, defense=3)

    combat = CombatSystem()
    damage = combat.calculate_damage(attacker, defender)

    assert damage == 7  # 10 - 3

def test_combat_minimum_damage():
    """Combat always deals at least 1 damage."""
    attacker = Player(attack=5, defense=0)
    defender = Monster(attack=0, defense=10)

    combat = CombatSystem()
    damage = combat.calculate_damage(attacker, defender)

    assert damage >= 1

def test_combat_kills_target():
    """Combat can kill a target."""
    attacker = Player(attack=100, defense=0)
    defender = Monster(hp=10, max_hp=10, attack=0, defense=0)

    combat = CombatSystem()
    combat.resolve_attack(attacker, defender)

    assert not defender.is_alive
```

---

### Testing Map Generation

```python
# tests/test_world.py
from src.core.world import DungeonGenerator

def test_dungeon_generates_correct_size():
    """Dungeon has correct dimensions."""
    gen = DungeonGenerator(width=80, height=24)
    dungeon = gen.generate()

    assert dungeon.width == 80
    assert dungeon.height == 24

def test_dungeon_has_walkable_tiles():
    """Dungeon has at least some walkable floor tiles."""
    gen = DungeonGenerator(width=80, height=24)
    dungeon = gen.generate()

    walkable_count = sum(
        1 for x in range(dungeon.width)
        for y in range(dungeon.height)
        if dungeon.is_walkable(x, y)
    )

    assert walkable_count > 100  # At least 100 walkable tiles

def test_dungeon_has_walls():
    """Dungeon has wall tiles."""
    gen = DungeonGenerator(width=80, height=24)
    dungeon = gen.generate()

    wall_count = sum(
        1 for x in range(dungeon.width)
        for y in range(dungeon.height)
        if not dungeon.is_walkable(x, y)
    )

    assert wall_count > 0

def test_dungeon_spawns_ore_veins():
    """Dungeon generates ore veins."""
    gen = DungeonGenerator(width=80, height=24)
    dungeon = gen.generate()

    ore_veins = dungeon.get_all_ore_veins()
    assert len(ore_veins) > 0  # At least some ore
```

---

### Testing Mining System

```python
# tests/test_mining.py
from src.core.game import Game
from src.core.entities import Player, OreVein

def test_survey_action_reveals_ore_properties():
    """Surveying ore reveals its properties."""
    ore_vein = OreVein.generate_random()
    player = Player()

    assert not ore_vein.is_surveyed

    # Survey the ore
    result = player.survey_ore(ore_vein)

    assert result.success
    assert ore_vein.is_surveyed

def test_mining_requires_survey_first():
    """Cannot mine ore without surveying."""
    ore_vein = OreVein.generate_random()
    player = Player()

    # Try to mine without surveying
    result = player.mine_ore(ore_vein)

    assert not result.success
    assert "survey" in result.message.lower()

def test_mining_takes_four_turns():
    """Mining requires 4 consecutive actions."""
    ore_vein = OreVein.generate_random()
    ore_vein.survey()  # Survey first
    player = Player()

    # Mine for 3 turns - should not complete
    for i in range(3):
        result = player.mine_ore(ore_vein)
        assert not result.success
        assert not ore_vein.is_mined

    # 4th turn - should complete
    result = player.mine_ore(ore_vein)
    assert result.success
    assert ore_vein.is_mined

def test_mined_ore_added_to_inventory():
    """Mined ore is added to player inventory."""
    ore_vein = OreVein.generate_random()
    ore_vein.survey()
    player = Player()

    # Mine ore (4 turns)
    for _ in range(4):
        player.mine_ore(ore_vein)

    assert len(player.inventory.ores) == 1
    assert player.inventory.ores[0].hardness == ore_vein.hardness
```

---

## Integration Testing

### Testing Complete Workflows

```python
# tests/test_game_workflow.py
from src.core.game import Game

def test_new_game_workflow():
    """Test complete new game initialization."""
    game = Game()
    game.new_game()

    # Player created
    assert game.player is not None
    assert game.player.is_alive

    # Map generated
    assert game.map is not None
    assert game.map.width > 0

    # Player placed on walkable tile
    assert game.map.is_walkable(game.player.x, game.player.y)

def test_complete_mining_workflow():
    """Test full mining workflow from start to finish."""
    game = Game()
    game.new_game()

    # Find an ore vein
    ore_vein = game.map.get_nearest_ore_vein(game.player.x, game.player.y)
    assert ore_vein is not None

    # Move player next to ore
    game.player.x = ore_vein.x + 1
    game.player.y = ore_vein.y

    # Survey ore
    game.handle_action("survey", ore_vein.x, ore_vein.y)
    assert ore_vein.is_surveyed

    # Mine ore (4 turns)
    for _ in range(4):
        game.handle_action("mine", ore_vein.x, ore_vein.y)

    # Verify ore in inventory
    assert len(game.player.inventory.ores) == 1
    assert ore_vein.is_mined

def test_combat_until_death_workflow():
    """Test combat leading to player death."""
    game = Game()
    game.new_game()

    # Create strong monster next to player
    monster = Monster(
        x=game.player.x + 1,
        y=game.player.y,
        hp=100,
        max_hp=100,
        attack=999,  # Guaranteed kill
        defense=0
    )
    game.map.add_monster(monster)

    # Player attacks monster
    initial_hp = game.player.hp
    game.handle_action("attack", monster.x, monster.y)

    # Monster counter-attacks
    game.process_monster_turns()

    # Player should be dead
    assert not game.player.is_alive
```

---

## Test Fixtures

### Reusable Test Data

```python
# tests/conftest.py
import pytest
from src.core.entities import Player, Monster, OreVein
from src.core.game import Game

@pytest.fixture
def fresh_player():
    """Create a fresh player for testing."""
    return Player(
        hp=20,
        max_hp=20,
        attack=5,
        defense=2,
        x=0,
        y=0
    )

@pytest.fixture
def weak_monster():
    """Create a weak monster for testing."""
    return Monster(
        name="Test Goblin",
        hp=5,
        max_hp=5,
        attack=2,
        defense=0,
        x=0,
        y=0
    )

@pytest.fixture
def high_quality_ore():
    """Create high-quality ore for testing."""
    return OreVein(
        hardness=95,
        conductivity=90,
        malleability=92,
        purity=98,
        density=88
    )

@pytest.fixture
def new_game():
    """Create a fresh game instance."""
    game = Game()
    game.new_game()
    return game

# Usage in tests:
def test_with_fixtures(fresh_player, weak_monster):
    """Test using fixtures."""
    assert fresh_player.hp == 20
    assert weak_monster.hp == 5
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_entities.py

# Run specific test
pytest tests/test_entities.py::TestPlayer::test_player_takes_damage

# Run with verbose output
pytest -v tests/

# Run with output printed (print statements visible)
pytest -s tests/

# Run tests matching a keyword
pytest -k "mining" tests/
```

### Test Coverage

```bash
# Run with coverage report
pytest --cov=src tests/

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/
# Open htmlcov/index.html in browser

# Check specific coverage threshold
pytest --cov=src --cov-fail-under=80 tests/
```

### Watch Mode (During Development)

```bash
# Install pytest-watch
pip install pytest-watch

# Auto-run tests on file changes
ptw tests/ src/
```

---

## Manual Testing (Critical!)

### Playtesting Checklist

**Every feature should be manually tested by playing the game:**

#### Movement
- [ ] Can move in all 8 directions (hjklyubn or arrow keys)
- [ ] Cannot walk through walls
- [ ] Cannot walk off map edge

#### Combat
- [ ] Can attack adjacent monsters
- [ ] Combat messages appear
- [ ] Monsters die at 0 HP
- [ ] Player dies at 0 HP

#### Mining
- [ ] Ore veins visible on map (◆)
- [ ] Can survey ore vein
- [ ] Survey shows ore properties
- [ ] Mining takes 4 turns
- [ ] Mining progress indicator appears
- [ ] Ore appears in inventory after mining

#### UI
- [ ] Map renders correctly
- [ ] Stats panel shows current HP, attack, defense
- [ ] Message log shows recent messages
- [ ] Inventory displays collected ores
- [ ] Controls are responsive

#### Edge Cases
- [ ] Game handles player death gracefully
- [ ] Can restart after death
- [ ] No crashes during normal play
- [ ] Error messages are clear and helpful

---

## Test-Driven Development (TDD)

### The Red-Green-Refactor Cycle

**1. Red - Write a failing test:**

```python
# tests/test_crafting.py
def test_craft_iron_sword():
    """Crafting iron sword from iron ore."""
    player = Player()
    player.inventory.add_ore(OreVein(hardness=75, ...))  # Iron ore

    result = player.craft_item("iron_sword")

    assert result.success
    assert len(player.inventory.items) == 1
    assert player.inventory.items[0].name == "Iron Sword"
```

**Run test:**
```bash
pytest tests/test_crafting.py::test_craft_iron_sword
# ❌ FAILED - craft_item() doesn't exist yet
```

**2. Green - Write minimum code to pass:**

```python
# src/core/entities.py
class Player:
    # ...
    def craft_item(self, recipe_name: str):
        """Craft an item from recipe."""
        if recipe_name == "iron_sword":
            sword = Item(name="Iron Sword", damage=8)
            self.inventory.items.append(sword)
            return Result(success=True)
        return Result(success=False)
```

**Run test:**
```bash
pytest tests/test_crafting.py::test_craft_iron_sword
# ✅ PASSED
```

**3. Refactor - Improve code:**

```python
# src/core/crafting.py
class CraftingSystem:
    """Handles all crafting logic."""

    def craft(self, player: Player, recipe_name: str):
        recipe = self.load_recipe(recipe_name)
        if not self.has_materials(player, recipe):
            return Result(success=False, message="Missing materials")

        item = self.create_item(recipe)
        player.inventory.add_item(item)
        return Result(success=True)
```

**Run test again:**
```bash
pytest tests/test_crafting.py::test_craft_iron_sword
# ✅ STILL PASSED - refactor successful!
```

---

## Common Testing Patterns

### Testing Randomness

```python
def test_ore_generation_produces_valid_values():
    """Generated ores have valid property ranges."""
    # Generate many ores
    ores = [OreVein.generate_random() for _ in range(100)]

    # Check all are valid
    for ore in ores:
        assert 0 <= ore.hardness <= 100
        assert 0 <= ore.purity <= 100
        # ... etc

def test_ore_generation_produces_variety():
    """Generated ores have variety (not all the same)."""
    ores = [OreVein.generate_random() for _ in range(100)]

    hardness_values = {ore.hardness for ore in ores}
    assert len(hardness_values) > 10  # At least 10 different values
```

### Testing Exceptions

```python
def test_invalid_action_raises_error():
    """Invalid actions raise appropriate errors."""
    game = Game()

    with pytest.raises(ValueError, match="Invalid action"):
        game.handle_action("invalid_action")

def test_mining_far_ore_raises_error():
    """Cannot mine ore that's too far away."""
    player = Player(x=0, y=0)
    ore = OreVein(x=10, y=10)  # Far away

    with pytest.raises(ValueError, match="too far"):
        player.mine_ore(ore)
```

---

## Debugging Tests

### Using print() in Tests

```python
def test_combat_damage(capsys):
    """Test with print debugging."""
    attacker = Player(attack=10)
    defender = Monster(defense=3)

    damage = calculate_damage(attacker, defender)
    print(f"Calculated damage: {damage}")  # Debug output

    captured = capsys.readouterr()
    assert "Calculated damage: 7" in captured.out
```

### Using pytest --pdb

```bash
# Drop into debugger on test failure
pytest --pdb tests/

# Drop into debugger on first test
pytest --pdb -x tests/
```

---

## Performance Testing (Simple)

```python
import time

def test_dungeon_generation_performance():
    """Dungeon generation completes in reasonable time."""
    gen = DungeonGenerator(width=80, height=24)

    start = time.time()
    dungeon = gen.generate()
    duration = time.time() - start

    assert duration < 0.1  # Should take < 100ms

def test_ai_turn_processing_performance():
    """AI can process 100 monster turns quickly."""
    game = Game()
    game.new_game()

    # Add 100 monsters
    for i in range(100):
        monster = Monster(x=i, y=0)
        game.map.add_monster(monster)

    start = time.time()
    game.process_monster_turns()
    duration = time.time() - start

    assert duration < 1.0  # Should take < 1 second
```

---

## Summary

**Test pyramid:**
- 80% unit tests (fast, focused, many)
- 15% integration tests (workflows)
- 5% manual testing (playtesting)

**TDD workflow:**
1. Write failing test (Red)
2. Write minimum code (Green)
3. Improve code (Refactor)
4. Repeat

**Always manual test:**
- Play your feature before committing
- Check edge cases
- Ensure it's fun!

**Quick reference:**
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Manual test
python3 run_textual.py
```

---

**For Phase 2 (async testing, integration, load tests):** See `/docs/future-multiplayer/DEVELOPMENT_GUIDELINES.md`

**Happy testing!** 🧪
