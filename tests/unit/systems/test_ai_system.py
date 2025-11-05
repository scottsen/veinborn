"""
Tests for AI system - monster behavior, state machines, pathfinding.

Coverage goals:
- State machine transitions (IDLE ↔ CHASING)
- Wandering behavior (25% move chance)
- Chase behavior (attack when adjacent, pathfind otherwise)
- Line-of-sight checks
- Vision radius checks
- Pathfinding integration

NOTE: Most tests in this file are for future state machine AI implementation.
Current MVP AI is simple aggressive chase-and-attack without state machines.
"""

import pytest
from src.core.systems.ai_system import AISystem
from src.core.entities import Player, Monster, AIState
from src.core.world import Map, TileType, Tile
from src.core.game_state import GameState
from src.core.base.game_context import GameContext


pytestmark = pytest.mark.unit

class TestAISystemInitialization:
    """Test AI system initialization."""

    def test_ai_system_creates_successfully(self, game_context):
        """AI system initializes with context."""
        ai_system = AISystem(game_context)

        assert ai_system is not None
        assert ai_system.context == game_context


@pytest.mark.skip(reason="State machine AI not yet implemented - MVP uses simple aggressive AI")
class TestAggressiveAIStateMachine:
    """Test aggressive AI state machine transitions."""

    def test_idle_monster_stays_idle_when_player_far(self):
        """Monster stays IDLE when player is out of vision range."""
        # Create simple map
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Player far away (20 tiles)
        player = Player(entity_id='player', x=5, y=5, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=25,  # 20 tiles away
            y=25,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 10.0  # Can only see 10 tiles
        monster.ai_state = AIState.IDLE

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)
        ai_system.update()

        # Monster should stay IDLE (player out of range)
        assert monster.ai_state == AIState.IDLE

    def test_idle_to_chasing_when_player_comes_into_view(self):
        """Monster transitions IDLE → CHASING when player enters vision."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Player within vision range
        player = Player(entity_id='player', x=5, y=5, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=10,  # 5 tiles away
            y=5,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 10.0
        monster.ai_state = AIState.IDLE

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)
        ai_system.update()

        # Monster should transition to CHASING
        assert monster.ai_state == AIState.CHASING
        assert monster.last_seen_position == (5, 5)

    def test_chasing_to_idle_when_player_leaves_view(self):
        """Monster transitions CHASING → IDLE when player leaves vision."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Place wall blocking line of sight
        for y in range(40):
            dungeon_map.tiles[7][y] = Tile(TileType.WALL)

        # Player on one side, monster on other
        player = Player(entity_id='player', x=5, y=10, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=10,  # Behind wall
            y=10,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 10.0
        monster.ai_state = AIState.CHASING  # Was chasing

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)
        ai_system.update()

        # Monster should lose sight and go IDLE
        assert monster.ai_state == AIState.IDLE
        assert monster.last_seen_position is None

    def test_chasing_stays_chasing_while_player_visible(self):
        """Monster stays CHASING while player remains visible."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=5, y=5, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=10,
            y=5,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 10.0
        monster.ai_state = AIState.CHASING

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)
        ai_system.update()

        # Monster should stay CHASING
        assert monster.ai_state == AIState.CHASING


@pytest.mark.skip(reason="State machine AI not yet implemented - MVP uses simple aggressive AI")
class TestWanderingBehavior:
    """Test idle wandering behavior."""

    def test_wandering_monster_sometimes_moves(self):
        """Wandering monsters have chance to move each turn."""
        import random
        random.seed(123)  # Different seed for movement

        from src.core.rng import GameRNG
        GameRNG.initialize(123)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Player far away (so monster stays IDLE)
        player = Player(entity_id='player', x=5, y=5, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=30,
            y=30,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 5.0  # Short vision - won't see player
        monster.ai_state = AIState.IDLE

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)

        # Run many turns, should move at least once (25% per turn)
        start_pos = (monster.x, monster.y)
        moved = False

        for _ in range(50):  # 50 turns, very high probability of movement
            ai_system.update()
            if (monster.x, monster.y) != start_pos:
                moved = True
                break

        # Should have moved at least once in 50 turns (probability > 99.99%)
        assert moved

    def test_wandering_respects_walkability(self):
        """Wandering monsters don't walk through walls."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.WALL)

        # Create small 3x3 room
        for x in range(10, 13):
            for y in range(10, 13):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Player far away
        player = Player(entity_id='player', x=5, y=5, hp=10, max_hp=10, attack=5, defense=2)

        # Monster in middle of room
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=11,
            y=11,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 2.0  # Won't see player
        monster.ai_state = AIState.IDLE

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)

        # Run many turns
        for _ in range(50):
            ai_system.update()
            # Monster should stay in 3x3 room
            assert 10 <= monster.x <= 12
            assert 10 <= monster.y <= 12


@pytest.mark.skip(reason="State machine AI not yet implemented - MVP uses simple aggressive AI")
class TestChaseBehavior:
    """Test chase behavior (attacking and pathfinding)."""

    def test_chasing_monster_attacks_when_adjacent(self):
        """Monster attacks player when adjacent."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=10, y=10, hp=100, max_hp=100, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=11,  # Adjacent
            y=10,
            hp=10,
            max_hp=10,
            attack=10,
            defense=1
        )
        monster.vision_radius = 10.0
        monster.ai_state = AIState.CHASING

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)

        initial_hp = player.hp
        ai_system.update()

        # Player should have taken damage
        assert player.hp < initial_hp

    def test_chasing_monster_pathfinds_toward_player(self):
        """Monster moves toward player when not adjacent."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=10, y=10, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=15,  # 5 tiles away
            y=10,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 10.0
        monster.ai_state = AIState.CHASING

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)

        start_distance = monster.distance_to(player)
        ai_system.update()
        end_distance = monster.distance_to(player)

        # Monster should have moved closer
        assert end_distance < start_distance

    def test_chasing_switches_to_idle_when_unreachable(self):
        """Monster gives up (goes IDLE) when player is unreachable."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Surround player with walls (unreachable)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:  # Don't block player's tile
                    dungeon_map.tiles[10 + dx][10 + dy] = Tile(TileType.WALL)

        player = Player(entity_id='player', x=10, y=10, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=15,
            y=15,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 20.0  # Can see player
        monster.ai_state = AIState.CHASING

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)
        ai_system.update()

        # Monster should give up and go IDLE
        assert monster.ai_state == AIState.IDLE


@pytest.mark.skip(reason="State machine AI not yet implemented - MVP uses simple aggressive AI")
class TestLineOfSightChecks:
    """Test AI system's line-of-sight calculations."""

    def test_can_see_player_within_radius_clear_los(self):
        """Monster can see player within radius with clear LOS."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=10, y=10, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=15,  # 5 tiles away
            y=10,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 10.0
        monster.ai_state = AIState.IDLE

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)

        # Check if monster can see player
        can_see = ai_system._can_see_player(monster, player)

        assert can_see is True

    def test_cannot_see_player_outside_radius(self):
        """Monster cannot see player beyond vision radius."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=10, y=10, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=25,  # 15 tiles away
            y=10,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 10.0  # Only 10 tiles
        monster.ai_state = AIState.IDLE

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)

        can_see = ai_system._can_see_player(monster, player)

        assert can_see is False

    def test_cannot_see_player_through_walls(self):
        """Monster cannot see player through walls."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Wall blocking line of sight
        for y in range(40):
            dungeon_map.tiles[12][y] = Tile(TileType.WALL)

        player = Player(entity_id='player', x=10, y=10, hp=10, max_hp=10, attack=5, defense=2)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=15,  # Behind wall
            y=10,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        monster.vision_radius = 10.0

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)

        can_see = ai_system._can_see_player(monster, player)

        assert can_see is False


@pytest.mark.skip(reason="State machine AI not yet implemented - MVP uses simple aggressive AI")
class TestMultipleMonsters:
    """Test AI system with multiple monsters."""

    def test_updates_all_living_monsters(self):
        """AI system updates all living monsters."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=10, y=10, hp=100, max_hp=100, attack=5, defense=2)

        # Two monsters in different positions
        m1 = Monster(entity_id='m1', name='Goblin1', x=12, y=10, hp=10, max_hp=10, attack=3, defense=1)
        m1.vision_radius = 5.0
        m1.ai_state = AIState.IDLE

        m2 = Monster(entity_id='m2', name='Goblin2', x=14, y=10, hp=10, max_hp=10, attack=3, defense=1)
        m2.vision_radius = 5.0
        m2.ai_state = AIState.IDLE

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[m1.entity_id] = m1
        state.entities[m2.entity_id] = m2
        context = GameContext(state)

        ai_system = AISystem(context)
        ai_system.update()

        # Both monsters should have seen player and transitioned to CHASING
        assert m1.ai_state == AIState.CHASING
        assert m2.ai_state == AIState.CHASING

    def test_ignores_dead_monsters(self):
        """AI system skips dead monsters."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=10, y=10, hp=100, max_hp=100, attack=5, defense=2)

        # Dead monster
        dead = Monster(entity_id='m1', name='Dead', x=12, y=10, hp=10, max_hp=10, attack=3, defense=1)
        dead.take_damage(10)  # Kill it
        dead.vision_radius = 5.0

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[dead.entity_id] = dead
        context = GameContext(state)

        ai_system = AISystem(context)

        # Should not crash
        ai_system.update()

        # Dead monster's state shouldn't change
        assert not dead.is_alive


@pytest.mark.skip(reason="State machine AI not yet implemented - MVP uses simple aggressive AI")
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_handles_dead_player(self):
        """AI system handles dead player gracefully."""
        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        for x in range(40):
            for y in range(40):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=10, y=10, hp=10, max_hp=10, attack=5, defense=2)
        player.take_damage(10)  # Kill player

        monster = Monster(entity_id='m1', name='Goblin', x=12, y=10, hp=10, max_hp=10, attack=3, defense=1)
        monster.vision_radius = 5.0
        monster.ai_state = AIState.CHASING

        state = GameState(player=player, dungeon_map=dungeon_map)
        state.entities[monster.entity_id] = monster
        context = GameContext(state)

        ai_system = AISystem(context)

        # Should not crash
        ai_system.update()

    def test_no_monsters_no_crash(self):
        """AI system handles no monsters gracefully."""

        from src.core.rng import GameRNG
        GameRNG.initialize(42)

        dungeon_map = Map(width=40, height=40)
        player = Player(entity_id='player', x=10, y=10, hp=10, max_hp=10, attack=5, defense=2)

        state = GameState(player=player, dungeon_map=dungeon_map)
        context = GameContext(state)

        ai_system = AISystem(context)

        # Should not crash
        ai_system.update()
