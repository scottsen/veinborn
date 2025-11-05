"""
Pathfinding tests for combat scenarios.

Tests the specific case that was causing wall collision spam:
- Pathfinding TO an entity-occupied tile (should fail or path adjacent)
- AI combat pathfinding (path to ADJACENT, not to target itself)
- Entity occupation vs tile walkability
"""

import pytest
from core.pathfinding import find_path, get_direction
from core.world import Map


class EntityOccupiedMap:
    """Mock map that tracks entity positions."""

    def __init__(self, width=10, height=10, walls=None, entities=None):
        self.width = width
        self.height = height
        self.walls = set(walls or [])
        self.entities = set(entities or [])  # Positions with entities

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        """
        Tile walkability - does NOT consider entities.
        This matches the actual Map.is_walkable() behavior.
        """
        return self.in_bounds(x, y) and (x, y) not in self.walls

    def is_walkable_for_pathfinding(self, x, y):
        """
        Enhanced walkability that considers entities.
        This is what pathfinding SHOULD use for combat.
        """
        return self.is_walkable(x, y) and (x, y) not in self.entities


class TestEntityOccupiedTiles:
    """Test pathfinding with entity-occupied tiles."""

    def test_tile_walkable_but_entity_present(self):
        """
        CRITICAL BUG REPRODUCTION:
        Tile is walkable (floor), but entity occupies it.
        Current pathfinding will succeed (checks tile only),
        but move action will fail (checks entity occupation).
        """
        # Monster at (5, 5) on a floor tile
        game_map = EntityOccupiedMap(
            width=10,
            height=10,
            entities=[(5, 5)]
        )

        # Tile itself is walkable (floor, no wall)
        assert game_map.is_walkable(5, 5) is True

        # But entity occupies it - shouldn't path here
        assert game_map.is_walkable_for_pathfinding(5, 5) is False

        # Current pathfinding will SUCCEED (bug!)
        path = find_path(game_map, (0, 0), (5, 5))
        assert path is not None  # This is the problem!

        # The path leads to an occupied tile
        assert path[-1] == (5, 5)

        # When bot tries to move here, MoveAction will fail:
        # "MoveAction validation failed: tile not walkable - Player tried to move to (5,5)"

    def test_path_adjacent_to_target(self):
        """
        CORRECT APPROACH for combat:
        Path to ADJACENT tile, not to target itself.
        """
        # Monster at (5, 5)
        game_map = EntityOccupiedMap(
            width=10,
            height=10,
            entities=[(5, 5)]
        )

        # Path to adjacent position instead
        adjacent_positions = [
            (4, 4), (5, 4), (6, 4),  # Top
            (4, 5),         (6, 5),  # Sides
            (4, 6), (5, 6), (6, 6),  # Bottom
        ]

        # Pick first walkable adjacent tile
        goal = adjacent_positions[0]  # (4, 4)

        path = find_path(game_map, (0, 0), goal)

        assert path is not None
        assert path[-1] == goal
        # Final position is walkable
        assert game_map.is_walkable(*path[-1])

    def test_all_adjacent_tiles_blocked(self):
        """
        Edge case: Target surrounded by walls/entities.
        Should return None (unreachable).
        """
        # Monster at (5, 5), surrounded by walls
        walls = [
            (4, 4), (5, 4), (6, 4),
            (4, 5),         (6, 5),
            (4, 6), (5, 6), (6, 6),
        ]
        game_map = EntityOccupiedMap(
            width=10,
            height=10,
            walls=walls,
            entities=[(5, 5)]
        )

        # Try to path to each adjacent tile
        adjacent_positions = [
            (4, 4), (5, 4), (6, 4),
            (4, 5),         (6, 5),
            (4, 6), (5, 6), (6, 6),
        ]

        paths = [find_path(game_map, (0, 0), pos) for pos in adjacent_positions]

        # All should fail (surrounded)
        assert all(path is None for path in paths)


class TestCombatPathfinding:
    """Test realistic combat pathfinding scenarios."""

    def test_melee_attack_pathfinding(self):
        """
        Melee combat: Path to adjacent tile, not to monster.
        """
        # Player at (0, 0), Monster at (5, 5)
        game_map = EntityOccupiedMap(
            width=10,
            height=10,
            entities=[(5, 5)]
        )

        # Correct: Path to tile adjacent to monster
        # Bot should calculate: "I need to be adjacent to attack"
        attack_range = 1  # Melee range

        # Find closest adjacent walkable tile
        # For simplicity, just pick (4, 5) - directly west of monster
        goal = (4, 5)

        path = find_path(game_map, (0, 0), goal)

        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (4, 5)

        # Verify final position is adjacent to monster (distance ≤ 1.5)
        dx = abs(path[-1][0] - 5)
        dy = abs(path[-1][1] - 5)
        distance = (dx**2 + dy**2) ** 0.5
        assert distance <= 1.5  # Adjacent

    def test_monster_ai_pathfinding_to_player(self):
        """
        Monster AI: Path to player (but player occupies tile).
        Same issue as player-to-monster.
        """
        # Monster at (10, 10), Player at (5, 5)
        game_map = EntityOccupiedMap(
            width=20,
            height=20,
            entities=[(5, 5)]  # Player position
        )

        # Current (buggy) behavior: path to player position
        path_to_player = find_path(game_map, (10, 10), (5, 5))
        assert path_to_player is not None  # Succeeds (tile is floor)

        # Correct behavior: path to adjacent
        goal = (4, 5)  # Adjacent to player
        path_adjacent = find_path(game_map, (10, 10), goal)
        assert path_adjacent is not None
        assert path_adjacent[-1] == (4, 5)


class TestPathfindingWithMapEntityChecking:
    """
    Test if we make pathfinding entity-aware.
    Alternative solution: pass entity positions to pathfinding.
    """

    def test_entity_aware_pathfinding(self):
        """
        Enhanced pathfinding that knows about entities.
        This would require changing pathfinding API.
        """
        # This is a design decision - do we:
        # A) Make pathfinding entity-aware (complex, slower)
        # B) Make callers path to adjacent tiles (simpler, correct)

        # Option B is better for combat because:
        # - You can NEVER occupy same tile as another entity
        # - Cleaner separation: pathfinding = map navigation, AI = combat tactics
        # - Faster (no entity position checks in hot path)

        # So this test documents the decision: NOT making pathfinding entity-aware
        pass


class TestGetAdjacentPositions:
    """Test helper for finding adjacent positions."""

    def test_get_adjacent_positions_8_dir(self):
        """Get all 8 adjacent positions around a target."""
        target = (5, 5)
        adjacent = [
            (target[0] + dx, target[1] + dy)
            for dx in [-1, 0, 1]
            for dy in [-1, 0, 1]
            if (dx, dy) != (0, 0)  # Exclude center
        ]

        assert len(adjacent) == 8
        assert (4, 4) in adjacent  # Top-left
        assert (5, 4) in adjacent  # Top
        assert (6, 4) in adjacent  # Top-right
        assert (4, 5) in adjacent  # Left
        assert (6, 5) in adjacent  # Right
        assert (4, 6) in adjacent  # Bottom-left
        assert (5, 6) in adjacent  # Bottom
        assert (6, 6) in adjacent  # Bottom-right

    def test_find_best_adjacent_position(self):
        """
        Find closest walkable adjacent position.
        This is what bot should do for combat.
        """
        # Monster at (10, 10)
        target = (10, 10)

        # Bot at (5, 5)
        bot_pos = (5, 5)

        # Generate adjacent positions
        adjacent = [
            (target[0] + dx, target[1] + dy)
            for dx in [-1, 0, 1]
            for dy in [-1, 0, 1]
            if (dx, dy) != (0, 0)
        ]

        # Find closest adjacent position to bot
        def distance(p1, p2):
            return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5

        closest = min(adjacent, key=lambda pos: distance(bot_pos, pos))

        # Should be (9, 9) - closest corner to bot
        assert closest == (9, 9)

        # Now path to THIS position instead of monster position
        game_map = EntityOccupiedMap(width=20, height=20)
        path = find_path(game_map, bot_pos, closest)

        assert path is not None
        assert path[0] == bot_pos
        assert path[-1] == closest


class TestRealWorldScenario:
    """Test the actual bug scenario from profiling."""

    def test_reproduce_wall_collision_spam(self):
        """
        Reproduce the exact scenario causing spam:
        "MoveAction validation failed: tile not walkable - Goblin tried to move to (9,18) [WALL]"

        This happens when pathfinding succeeds but move validation fails.
        """
        # Scenario: Goblin at (8, 18), trying to reach player at (9, 18)
        # But (9, 18) has a WALL? Or has the player?

        # Let's test both cases:

        # Case 1: Wall at goal
        walls = [(9, 18)]
        game_map = EntityOccupiedMap(width=20, height=20, walls=walls)

        path = find_path(game_map, (8, 18), (9, 18))

        # Pathfinding should return None (goal is wall)
        assert path is None  # CORRECT - pathfinding catches this

        # Case 2: Entity at goal (player)
        game_map = EntityOccupiedMap(
            width=20,
            height=20,
            entities=[(9, 18)]
        )

        path = find_path(game_map, (8, 18), (9, 18))

        # Pathfinding SUCCEEDS (tile is floor, only entity there)
        assert path is not None  # THIS IS THE BUG!

        # When goblin tries to execute this move, it fails because player is there
        # But pathfinding keeps returning same path, causing infinite spam

    def test_fix_goblin_pathfinding(self):
        """
        Fix: Goblin should path ADJACENT to player, not to player position.
        """
pytestmark = pytest.mark.unit

        # Player at (9, 18)
        player_pos = (9, 18)

        # Goblin at (8, 18)
        goblin_pos = (8, 18)

        game_map = EntityOccupiedMap(
            width=20,
            height=20,
            entities=[player_pos]
        )

        # Find adjacent walkable positions to player
        adjacent = [
            (player_pos[0] + dx, player_pos[1] + dy)
            for dx in [-1, 0, 1]
            for dy in [-1, 0, 1]
            if (dx, dy) != (0, 0)
        ]

        # Filter to walkable
        walkable_adjacent = [
            pos for pos in adjacent
            if game_map.is_walkable(*pos)
        ]

        # Goblin should path to closest adjacent position
        def distance(p1, p2):
            return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

        goal = min(walkable_adjacent, key=lambda pos: distance(goblin_pos, pos))

        path = find_path(game_map, goblin_pos, goal)

        assert path is not None
        # Should path to adjacent tile, not to player tile
        assert path[-1] != player_pos
        assert path[-1] in walkable_adjacent
