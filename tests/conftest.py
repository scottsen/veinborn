"""Shared test fixtures for Brogue testing.

This module provides reusable test fixtures that make writing tests easy.
All fixtures follow the patterns from docs/architecture/MVP_TESTING_GUIDE.md
"""
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from core.entities import Player, Monster, OreVein, EntityType
from core.game import Game
from core.game_state import GameState
from core.world import Map


# ============================================================================
# Entity Fixtures
# ============================================================================

@pytest.fixture
def fresh_player():
    """Create a standard test player at full health.

    Returns:
        Player: Level 1 player with 20 HP, 5 attack, 2 defense at position (10, 10)

    Example:
        def test_player_movement(fresh_player):
            fresh_player.x += 1
            assert fresh_player.x == 11
    """
    return Player(
        x=10,
        y=10,
        hp=20,
        max_hp=20,
        attack=5,
        defense=2
    )


@pytest.fixture
def damaged_player():
    """Create a player at 50% health.

    Returns:
        Player: Level 1 player with 10/20 HP

    Example:
        def test_healing(damaged_player):
            damaged_player.heal(5)
            assert damaged_player.hp == 15
    """
    return Player(
        x=10,
        y=10,
        hp=10,
        max_hp=20,
        attack=5,
        defense=2
    )


@pytest.fixture
def weak_goblin():
    """Create a weak monster for basic testing.

    Returns:
        Monster: Goblin with 5 HP, 2 attack, 0 defense at (11, 10)

    Example:
        def test_combat(fresh_player, weak_goblin):
            result = attack(fresh_player, weak_goblin)
            assert not weak_goblin.is_alive
    """
    return Monster(
        name="Goblin",
        x=11,
        y=10,
        hp=5,
        max_hp=5,
        attack=2,
        defense=0,
        xp_reward=10
    )


@pytest.fixture
def strong_orc():
    """Create a strong monster for combat testing.

    Returns:
        Monster: Orc Warrior with 20 HP, 8 attack, 3 defense at (12, 10)

    Example:
        def test_tough_combat(fresh_player, strong_orc):
            # This will be a tough fight!
            result = attack(fresh_player, strong_orc)
            assert strong_orc.hp < 20  # Damaged but not dead
    """
    return Monster(
        name="Orc Warrior",
        x=12,
        y=10,
        hp=20,
        max_hp=20,
        attack=8,
        defense=3,
        xp_reward=50
    )


@pytest.fixture
def copper_ore():
    """Create a copper ore vein with moderate properties.

    Returns:
        OreVein: Copper ore with medium hardness and conductivity at (10, 11)

    Example:
        def test_mining(fresh_player, copper_ore):
            fresh_player.x, fresh_player.y = 10, 10  # Move adjacent
            result = mine(fresh_player, copper_ore)
            assert result.success
    """
    return OreVein(
        ore_type="copper",
        x=10,
        y=11,
        hardness=50,
        conductivity=85,
        malleability=70,
        purity=60,
        density=80
    )


@pytest.fixture
def iron_ore():
    """Create an iron ore vein with higher hardness.

    Returns:
        OreVein: Iron ore with high hardness at (11, 11)
    """
    return OreVein(
        ore_type="iron",
        x=11,
        y=11,
        hardness=75,
        conductivity=60,
        malleability=65,
        purity=70,
        density=85
    )


@pytest.fixture
def mithril_ore():
    """Create high-quality mithril ore for testing rare materials.

    Returns:
        OreVein: Mithril ore with very high stats at (10, 12)

    Example:
        def test_rare_ore(mithril_ore):
            assert mithril_ore.average_quality > 90
    """
    return OreVein(
        ore_type="mithril",
        x=10,
        y=12,
        hardness=95,
        conductivity=98,
        malleability=85,
        purity=99,
        density=90
    )


# ============================================================================
# Map Fixtures
# ============================================================================

@pytest.fixture
def empty_map():
    """Create an empty map (all walls) for testing.

    Returns:
        Map: 80x24 map filled with walls

    Example:
        def test_map_size(empty_map):
            assert empty_map.width == 80
            assert empty_map.height == 24
    """
    return Map(width=80, height=24)


@pytest.fixture
def simple_room_map():
    """Create a map with a simple rectangular room for testing.

    Returns:
        Map: 80x24 map with a 10x10 room centered around (10, 10)

    Example:
        def test_room_walkability(simple_room_map):
            assert simple_room_map.is_walkable(10, 10)
    """
    map_obj = Map(width=80, height=24)

    # Create a 10x10 room centered at (10, 10)
    for x in range(5, 16):
        for y in range(5, 16):
            map_obj.tiles[y][x] = 'floor'

    return map_obj


# ============================================================================
# GameState Fixtures
# ============================================================================

@pytest.fixture
def simple_game_state(fresh_player, empty_map):
    """Create a minimal GameState with just a player.

    Returns:
        GameState: Empty game state with one player entity

    Example:
        def test_game_state(simple_game_state):
            assert len(simple_game_state.entities) == 1
            assert simple_game_state.player is not None
    """
    return GameState(
        player=fresh_player,
        entities={fresh_player.entity_id: fresh_player},
        dungeon_map=empty_map,
        messages=[],
        turn_count=0,
        current_floor=1,
        game_over=False
    )


@pytest.fixture
def game_state_with_monster(fresh_player, weak_goblin, simple_room_map):
    """Create a GameState with player and one monster.

    Returns:
        GameState: Game state with player and adjacent monster

    Example:
        def test_combat_state(game_state_with_monster):
            monsters = [e for e in game_state_with_monster.entities.values()
                       if e.entity_type == EntityType.MONSTER]
            assert len(monsters) == 1
    """
    entities = {
        fresh_player.entity_id: fresh_player,
        weak_goblin.entity_id: weak_goblin,
    }

    return GameState(
        player=fresh_player,
        entities=entities,
        dungeon_map=simple_room_map,
        messages=[],
        turn_count=0,
        current_floor=1,
        game_over=False
    )


@pytest.fixture
def game_state_with_ore(fresh_player, copper_ore, simple_room_map):
    """Create a GameState with player and one ore vein.

    Returns:
        GameState: Game state with player and adjacent ore vein

    Example:
        def test_mining_state(game_state_with_ore):
            ore_veins = [e for e in game_state_with_ore.entities.values()
                        if e.entity_type == EntityType.ORE_VEIN]
            assert len(ore_veins) == 1
    """
    entities = {
        fresh_player.entity_id: fresh_player,
        copper_ore.entity_id: copper_ore,
    }

    return GameState(
        player=fresh_player,
        entities=entities,
        dungeon_map=simple_room_map,
        messages=[],
        turn_count=0,
        current_floor=1,
        game_over=False
    )


# ============================================================================
# Game Fixtures
# ============================================================================

@pytest.fixture
def new_game():
    """Create a fresh game instance with full initialization.

    Returns:
        Game: Fully initialized game ready to play

    Example:
        def test_full_game(new_game):
            assert new_game.state.player is not None
            assert len(new_game.state.entities) > 1  # Player + monsters/ore
    """
    game = Game()
    game.start_new_game()
    return game


# ============================================================================
# GameContext Fixtures
# ============================================================================

@pytest.fixture
def game_context(simple_game_state):
    """Create a GameContext for action testing.

    Returns:
        GameContext: Context with simple game state

    Example:
        def test_action(game_context):
            from core.actions.move_action import MoveAction
            action = MoveAction(actor_id="test_player", dx=1, dy=0)
            outcome = action.execute(game_context)
            assert outcome.took_turn
    """
    from core.base.game_context import GameContext
    return GameContext(game_state=simple_game_state)


@pytest.fixture
def combat_context(game_state_with_monster):
    """Create a GameContext ready for combat testing.

    Returns:
        GameContext: Context with player and monster

    Example:
        def test_attack_action(combat_context):
            from core.actions.attack_action import AttackAction
            action = AttackAction(actor_id="test_player", target_id="test_goblin")
            outcome = action.execute(combat_context)
            assert outcome.success
    """
    from core.base.game_context import GameContext
    return GameContext(game_state=game_state_with_monster)


@pytest.fixture
def mining_context(game_state_with_ore):
    """Create a GameContext ready for mining testing.

    Returns:
        GameContext: Context with player and ore vein

    Example:
        def test_survey_action(mining_context):
            from core.actions.survey_action import SurveyAction
            action = SurveyAction(actor_id="test_player")
            outcome = action.execute(mining_context)
            assert outcome.success
    """
    from core.base.game_context import GameContext
    return GameContext(game_state=game_state_with_ore)


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def capture_messages(monkeypatch):
    """Capture game messages for assertion.

    Returns:
        list: List that collects all messages added to game state

    Example:
        def test_combat_messages(combat_context, capture_messages):
            # ... perform combat ...
            assert any("hits" in msg for msg in capture_messages)
    """
    messages = []

    def mock_add_message(self, message):
        messages.append(message)

    monkeypatch.setattr("core.game_state.GameState.add_message", mock_add_message)
    return messages


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, multiple systems)"
    )
    config.addinivalue_line(
        "markers", "ui: UI tests (manual or automated)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "smoke: Smoke tests (basic functionality)"
    )
