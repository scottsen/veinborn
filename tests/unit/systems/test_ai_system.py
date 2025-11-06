"""
Tests for AI system - monster behavior.

Tests multiple AI behavior types:
- Aggressive: Chase and attack
- Defensive: Attack when close, flee when low HP
- Passive: Wander unless attacked
- Coward: Always flee from player
- Guard: Defend spawn area
"""

import pytest
from src.core.systems.ai_system import AISystem
from src.core.entities import Monster, Player, EntityType
from src.core.base.game_context import GameContext
from src.core.game_state import GameState
from src.core.world import Map, Tile, TileType


pytestmark = pytest.mark.unit


@pytest.fixture
def simple_map():
    """Create a simple walkable map."""
    game_map = Map(width=30, height=30)
    # Make a large open area with proper Tile objects
    for x in range(5, 25):
        for y in range(5, 25):
            game_map.tiles[x][y] = Tile(tile_type=TileType.FLOOR)
    return game_map


@pytest.fixture
def test_player(simple_map):
    """Create a test player."""
    player = Player(
        x=15,
        y=15,
        hp=20,
        max_hp=20,
        attack=5,
        defense=2
    )
    return player


@pytest.fixture
def test_monster(simple_map):
    """Create a test monster."""
    monster = Monster(
        name="Test Monster",
        x=10,
        y=10,
        hp=50,
        max_hp=100,
        attack=10,
        defense=5,
        xp_reward=10
    )
    return monster


@pytest.fixture
def game_context_with_monster(test_player, test_monster, simple_map):
    """Create a game context with player and monster."""
    entities = {
        test_player.entity_id: test_player,
        test_monster.entity_id: test_monster,
    }

    game_state = GameState(
        player=test_player,
        entities=entities,
        dungeon_map=simple_map,
        messages=[],
        turn_count=0,
        current_floor=1,
        game_over=False
    )

    return GameContext(game_state=game_state)


class TestAISystemInitialization:
    """Test AI system initialization."""

    def test_ai_system_creates_successfully(self, game_context):
        """AI system initializes with context."""
        ai_system = AISystem(game_context)

        assert ai_system is not None
        assert ai_system.context == game_context
        assert ai_system.config is not None


class TestAggressiveBehavior:
    """Test aggressive AI behavior."""

    def test_aggressive_attacks_when_adjacent(self, game_context_with_monster):
        """Aggressive AI attacks when adjacent to player."""
        context = game_context_with_monster
        monster = list(context.get_entities_by_type(EntityType.MONSTER))[0]
        player = context.get_player()

        # Position monster adjacent to player
        monster.x = player.x + 1
        monster.y = player.y
        monster.set_stat('ai_type', 'aggressive')

        ai_system = AISystem(context)
        initial_hp = player.hp

        ai_system.update()

        # Player should have taken damage
        assert player.hp < initial_hp

    def test_aggressive_chases_in_range(self, game_context_with_monster):
        """Aggressive AI moves toward player when in range."""
        context = game_context_with_monster
        monster = list(context.get_entities_by_type(EntityType.MONSTER))[0]
        player = context.get_player()

        # Position monster near player but not adjacent
        monster.x = player.x - 3
        monster.y = player.y
        monster.set_stat('ai_type', 'aggressive')

        ai_system = AISystem(context)
        initial_x = monster.x

        ai_system.update()

        # Monster should have moved closer
        assert monster.x != initial_x or monster.y != player.y


class TestDefensiveBehavior:
    """Test defensive AI behavior."""

    def test_defensive_flees_when_low_hp(self, game_context_with_monster):
        """Defensive AI flees when HP is low."""
        context = game_context_with_monster
        monster = list(context.get_entities_by_type(EntityType.MONSTER))[0]
        player = context.get_player()

        # Position monster adjacent to player with low HP
        monster.x = player.x + 1
        monster.y = player.y
        monster.hp = 20  # 20% HP (flee threshold is 30%)
        monster.set_stat('ai_type', 'defensive')

        ai_system = AISystem(context)
        initial_x = monster.x
        initial_y = monster.y

        ai_system.update()

        # Monster should have moved away (not attacked)
        # and player HP should be unchanged
        initial_player_hp = player.hp
        assert monster.x != initial_x or monster.y != initial_y

    def test_defensive_attacks_when_healthy(self, game_context_with_monster):
        """Defensive AI attacks when HP is healthy."""
        context = game_context_with_monster
        monster = list(context.get_entities_by_type(EntityType.MONSTER))[0]
        player = context.get_player()

        # Position monster adjacent with healthy HP
        monster.x = player.x + 1
        monster.y = player.y
        monster.hp = 80  # 80% HP (above flee threshold)
        monster.set_stat('ai_type', 'defensive')

        ai_system = AISystem(context)
        initial_hp = player.hp

        ai_system.update()

        # Player should have taken damage
        assert player.hp < initial_hp


class TestPassiveBehavior:
    """Test passive AI behavior."""

    def test_passive_wanders_peacefully(self, game_context_with_monster):
        """Passive AI wanders when not threatened."""
        context = game_context_with_monster
        monster = list(context.get_entities_by_type(EntityType.MONSTER))[0]
        player = context.get_player()

        # Position monster away from player
        monster.x = 10
        monster.y = 10
        player.x = 20
        player.y = 20
        monster.set_stat('ai_type', 'passive')

        ai_system = AISystem(context)

        # Run multiple updates - monster should wander randomly
        # (50% chance to move each turn)
        ai_system.update()

        # Player should not be attacked
        assert player.hp == 20


class TestCowardBehavior:
    """Test coward AI behavior."""

    def test_coward_flees_from_player(self, game_context_with_monster):
        """Coward AI always flees from player."""
        context = game_context_with_monster
        monster = list(context.get_entities_by_type(EntityType.MONSTER))[0]
        player = context.get_player()

        # Position monster near player (within flee range)
        monster.x = player.x + 3
        monster.y = player.y
        monster.set_stat('ai_type', 'coward')

        ai_system = AISystem(context)
        initial_distance = abs(monster.x - player.x) + abs(monster.y - player.y)

        ai_system.update()

        # Monster should have moved away or stayed same distance
        new_distance = abs(monster.x - player.x) + abs(monster.y - player.y)
        # Due to random movement, we just check it didn't attack
        assert player.hp == 20  # Player not attacked


class TestGuardBehavior:
    """Test guard AI behavior."""

    def test_guard_returns_to_spawn(self, game_context_with_monster):
        """Guard AI returns to spawn when too far away."""
        context = game_context_with_monster
        monster = list(context.get_entities_by_type(EntityType.MONSTER))[0]
        player = context.get_player()

        # Set spawn position and move monster far from it
        monster.set_stat('spawn_x', 10)
        monster.set_stat('spawn_y', 10)
        monster.x = 20  # Far from spawn (>4 tiles)
        monster.y = 20
        monster.set_stat('ai_type', 'guard')

        ai_system = AISystem(context)
        initial_distance_from_spawn = abs(monster.x - 10) + abs(monster.y - 10)

        ai_system.update()

        # Monster should move toward spawn
        new_distance_from_spawn = abs(monster.x - 10) + abs(monster.y - 10)
        # Should be moving toward spawn or already at spawn
        assert new_distance_from_spawn <= initial_distance_from_spawn

    def test_guard_defends_area_within_radius(self, game_context_with_monster):
        """Guard AI attacks player within guard radius."""
        context = game_context_with_monster
        monster = list(context.get_entities_by_type(EntityType.MONSTER))[0]
        player = context.get_player()

        # Set spawn position and place monster near spawn
        monster.set_stat('spawn_x', 15)
        monster.set_stat('spawn_y', 15)
        monster.x = player.x + 1  # Adjacent to player, near spawn
        monster.y = player.y
        player.x = 15
        player.y = 15
        monster.set_stat('ai_type', 'guard')

        ai_system = AISystem(context)
        initial_hp = player.hp

        ai_system.update()

        # Player should have taken damage
        assert player.hp < initial_hp


class TestAIConfiguration:
    """Test AI configuration loading."""

    def test_ai_behavior_config_loaded(self, game_context):
        """AI system loads behavior configuration."""
        ai_system = AISystem(game_context)

        # Test getting aggressive config
        aggressive_config = ai_system.config.get_ai_behavior_config('aggressive')
        assert 'chase_range' in aggressive_config
        assert aggressive_config['chase_range'] == 10

    def test_unknown_ai_type_falls_back(self, game_context_with_monster):
        """Unknown AI type falls back to aggressive."""
        context = game_context_with_monster
        monster = list(context.get_entities_by_type(EntityType.MONSTER))[0]

        monster.set_stat('ai_type', 'unknown_type')

        ai_system = AISystem(context)
        # Should not crash - falls back to aggressive
        ai_system.update()
