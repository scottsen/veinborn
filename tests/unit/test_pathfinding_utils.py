"""
Tests for pathfinding utility functions.

Tests the helper functions for combat AI:
- get_adjacent_positions()
- find_closest_adjacent_position()
"""

import pytest
from src.core.pathfinding import (
    get_adjacent_positions,
    find_closest_adjacent_position,
)


class SimpleMockMap:
    """Simple test map."""

    def __init__(self, width=20, height=20, walls=None):
        self.width = width
        self.height = height
        self.walls = set(walls or [])

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and (x, y) not in self.walls


class TestGetAdjacentPositions:
    """Test get_adjacent_positions() utility."""

    def test_get_adjacent_8_directional(self):
        """Returns 8 positions around center with diagonals."""
        adjacent = get_adjacent_positions((5, 5), allow_diagonals=True)

        assert len(adjacent) == 8
        assert (4, 4) in adjacent  # Top-left
        assert (5, 4) in adjacent  # Top
        assert (6, 4) in adjacent  # Top-right
        assert (4, 5) in adjacent  # Left
        assert (6, 5) in adjacent  # Right
        assert (4, 6) in adjacent  # Bottom-left
        assert (5, 6) in adjacent  # Bottom
        assert (6, 6) in adjacent  # Bottom-right

        # Center should NOT be included
        assert (5, 5) not in adjacent

    def test_get_adjacent_4_directional(self):
        """Returns 4 cardinal positions without diagonals."""
        adjacent = get_adjacent_positions((5, 5), allow_diagonals=False)

        assert len(adjacent) == 4
        assert (5, 4) in adjacent  # North
        assert (4, 5) in adjacent  # West
        assert (6, 5) in adjacent  # East
        assert (5, 6) in adjacent  # South

        # Diagonals should NOT be included
        assert (4, 4) not in adjacent
        assert (6, 6) not in adjacent

    def test_get_adjacent_origin(self):
        """Works correctly at map origin."""
        adjacent = get_adjacent_positions((0, 0), allow_diagonals=True)

        assert len(adjacent) == 8
        assert (-1, -1) in adjacent  # May be out of bounds, but that's OK
        assert (0, 1) in adjacent
        assert (1, 0) in adjacent

    def test_get_adjacent_large_coords(self):
        """Works with large coordinate values."""
        adjacent = get_adjacent_positions((100, 200), allow_diagonals=True)

        assert len(adjacent) == 8
        assert (99, 199) in adjacent
        assert (100, 199) in adjacent
        assert (101, 201) in adjacent


class TestFindClosestAdjacentPosition:
    """Test find_closest_adjacent_position() utility."""

    def test_find_closest_basic(self):
        """Finds closest walkable adjacent position."""
        game_map = SimpleMockMap(width=20, height=20)

        # Target at (10, 10), source at (5, 5)
        target = (10, 10)
        source = (5, 5)

        result = find_closest_adjacent_position(game_map, target, source)

        assert result is not None
        # Should be southwest of target (closest to source)
        assert result == (9, 9)

        # Verify it's adjacent to target
        dx = abs(result[0] - target[0])
        dy = abs(result[1] - target[1])
        assert dx <= 1 and dy <= 1
        assert (dx, dy) != (0, 0)  # Not the target itself

    def test_find_closest_source_east_of_target(self):
        """Source is east of target."""
        game_map = SimpleMockMap(width=20, height=20)

        target = (10, 10)
        source = (15, 10)

        result = find_closest_adjacent_position(game_map, target, source)

        assert result is not None
        # Should be east of target (closest to source)
        assert result == (11, 10)

    def test_find_closest_source_north_of_target(self):
        """Source is north of target."""
        game_map = SimpleMockMap(width=20, height=20)

        target = (10, 10)
        source = (10, 5)

        result = find_closest_adjacent_position(game_map, target, source)

        assert result is not None
        # Should be north of target (closest to source)
        assert result == (10, 9)

    def test_find_closest_with_walls(self):
        """Finds walkable position when some adjacent tiles are walls."""
        # Block some adjacent tiles
        walls = [
            (9, 9),   # Southwest
            (10, 9),  # North
            (11, 9),  # Northeast
        ]
        game_map = SimpleMockMap(width=20, height=20, walls=walls)

        target = (10, 10)
        source = (5, 5)  # Southwest of target

        result = find_closest_adjacent_position(game_map, target, source)

        assert result is not None
        # Should NOT be any of the walls
        assert result not in walls
        # Should still be adjacent
        dx = abs(result[0] - target[0])
        dy = abs(result[1] - target[1])
        assert dx <= 1 and dy <= 1

    def test_find_closest_completely_surrounded(self):
        """Returns None when target is completely surrounded."""
        # Wall all around target
        walls = [
            (9, 9), (10, 9), (11, 9),
            (9, 10),         (11, 10),
            (9, 11), (10, 11), (11, 11),
        ]
        game_map = SimpleMockMap(width=20, height=20, walls=walls)

        target = (10, 10)
        source = (5, 5)

        result = find_closest_adjacent_position(game_map, target, source)

        assert result is None  # Unreachable

    def test_find_closest_at_map_edge(self):
        """Handles target at map edge correctly."""
        game_map = SimpleMockMap(width=10, height=10)

        # Target at edge
        target = (0, 0)
        source = (5, 5)

        result = find_closest_adjacent_position(game_map, target, source)

        assert result is not None
        # Should be one of the valid adjacent positions
        # (0,0) has only 3 valid adjacent in 10x10 map: (1,0), (0,1), (1,1)
        assert result in [(1, 0), (0, 1), (1, 1)]

    def test_find_closest_4_directional(self):
        """Works with 4-directional movement."""
        game_map = SimpleMockMap(width=20, height=20)

        target = (10, 10)
        source = (5, 5)

        result = find_closest_adjacent_position(
            game_map, target, source, allow_diagonals=False
        )

        assert result is not None
        # Should be one of the 4 cardinal directions
        assert result in [
            (10, 9),   # North
            (9, 10),   # West
            (11, 10),  # East
            (10, 11),  # South
        ]


class TestCombatScenarios:
    """Test realistic combat scenarios using new utilities."""

    def test_melee_combat_basic(self):
        """Player paths to attack adjacent monster."""
        game_map = SimpleMockMap(width=20, height=20)

        player_pos = (5, 5)
        monster_pos = (10, 10)

        # Find where player should move to attack
        goal = find_closest_adjacent_position(game_map, monster_pos, player_pos)

        assert goal is not None
        assert goal == (9, 9)  # Closest to player

        # Verify goal is in melee range
        dx = abs(goal[0] - monster_pos[0])
        dy = abs(goal[1] - monster_pos[1])
        distance = (dx**2 + dy**2) ** 0.5
        assert distance <= 1.5  # Adjacent (melee range)

    def test_monster_chases_player(self):
        """Monster paths to chase player."""
        game_map = SimpleMockMap(width=20, height=20)

        monster_pos = (15, 15)
        player_pos = (10, 10)

        # Monster finds where to move
        goal = find_closest_adjacent_position(game_map, player_pos, monster_pos)

        assert goal is not None
        assert goal == (11, 11)  # Closest to monster

    def test_multiple_attackers_different_sides(self):
        """Multiple entities can find different adjacent positions."""
        game_map = SimpleMockMap(width=20, height=20)

        target_pos = (10, 10)

        # Attackers from different directions
        attacker_north = (10, 5)
        attacker_south = (10, 15)
        attacker_west = (5, 10)
        attacker_east = (15, 10)

        goal_north = find_closest_adjacent_position(game_map, target_pos, attacker_north)
        goal_south = find_closest_adjacent_position(game_map, target_pos, attacker_south)
        goal_west = find_closest_adjacent_position(game_map, target_pos, attacker_west)
        goal_east = find_closest_adjacent_position(game_map, target_pos, attacker_east)

        # Each should find different adjacent position
        assert goal_north == (10, 9)   # North side
        assert goal_south == (10, 11)  # South side
        assert goal_west == (9, 10)    # West side
        assert goal_east == (11, 10)   # East side

        # All different
        goals = [goal_north, goal_south, goal_west, goal_east]
        assert len(set(goals)) == 4

    def test_ranged_combat_no_adjacency_needed(self):
        """
        Ranged combat doesn't need adjacency.
        Can path directly to good position (not necessarily adjacent).
        """
        # For ranged combat, you might want to stay at distance 3-5
        # This is handled by higher-level AI logic, not pathfinding utilities
        pass


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_target_out_of_bounds(self):
        """Target outside map returns None."""
        game_map = SimpleMockMap(width=10, height=10)

        target = (20, 20)  # Out of bounds
        source = (5, 5)

        result = find_closest_adjacent_position(game_map, target, source)

        # All adjacent positions would be out of bounds
        assert result is None

    def test_source_equals_target(self):
        """Source and target at same position."""
        game_map = SimpleMockMap(width=20, height=20)

        pos = (10, 10)

        result = find_closest_adjacent_position(game_map, pos, pos)

        # Should return an adjacent position (any of them)
        assert result is not None
        dx = abs(result[0] - pos[0])
        dy = abs(result[1] - pos[1])
        assert dx <= 1 and dy <= 1
        assert result != pos

    def test_tiny_map(self):
        """Works on very small maps."""
pytestmark = pytest.mark.unit

        game_map = SimpleMockMap(width=3, height=3)

        target = (1, 1)  # Center of 3x3
        source = (0, 0)

        result = find_closest_adjacent_position(game_map, target, source)

        assert result is not None
        assert result == (0, 0)  # Closest to source
