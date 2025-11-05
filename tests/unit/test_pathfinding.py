"""
Unit tests for A* pathfinding.

Tests:
- Heuristic functions
- Simple paths (straight line, L-shaped)
- Complex paths (maze navigation)
- Edge cases (no path, walls, out of bounds)
- Different movement modes (4-dir, 8-dir)
- Performance (large maps)
"""

import pytest
from core.pathfinding import (

    find_path, get_next_step, get_direction, distance,
    Heuristic, get_neighbors
)
from core.world import Map, Tile, TileType


class SimpleMockMap:
    """Simple test map for pathfinding."""

    def __init__(self, width=10, height=10, walls=None):
        self.width = width
        self.height = height
        self.walls = set(walls or [])

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and (x, y) not in self.walls


# ============================================================================
# Heuristic Tests
# ============================================================================

class TestHeuristics:
    """Test distance heuristics."""

    def test_manhattan_distance(self):
        """Manhattan distance is sum of absolute differences."""
        assert Heuristic.manhattan((0, 0), (3, 4)) == 7
        assert Heuristic.manhattan((5, 5), (5, 5)) == 0
        assert Heuristic.manhattan((0, 0), (1, 1)) == 2

    def test_euclidean_distance(self):
        """Euclidean distance is straight-line distance."""
        assert Heuristic.euclidean((0, 0), (3, 4)) == 5.0
        assert Heuristic.euclidean((0, 0), (0, 0)) == 0.0
        assert abs(Heuristic.euclidean((0, 0), (1, 1)) - 1.414) < 0.01

    def test_chebyshev_distance(self):
        """Chebyshev distance is maximum of absolute differences."""
        assert Heuristic.chebyshev((0, 0), (3, 4)) == 4
        assert Heuristic.chebyshev((0, 0), (5, 5)) == 5
        assert Heuristic.chebyshev((0, 0), (3, 2)) == 3

    def test_diagonal_distance(self):
        """Diagonal distance accounts for diagonal move cost."""
        # Pure diagonal: 5 diagonal steps = 5 * sqrt(2)
        result = Heuristic.diagonal((0, 0), (5, 5))
        expected = 5 * 1.414  # sqrt(2) ≈ 1.414
        assert abs(result - expected) < 0.1

        # Pure cardinal: (0,0) to (5,0) = 5
        assert Heuristic.diagonal((0, 0), (5, 0)) == 5.0


# ============================================================================
# Neighbor Generation Tests
# ============================================================================

class TestGetNeighbors:
    """Test neighbor generation."""

    def test_neighbors_8_directional(self):
        """8-directional movement returns 8 neighbors."""
        neighbors = get_neighbors((5, 5), allow_diagonals=True)
        assert len(neighbors) == 8
        assert (4, 4) in neighbors  # Top-left
        assert (6, 6) in neighbors  # Bottom-right
        assert (5, 4) in neighbors  # Top
        assert (5, 6) in neighbors  # Bottom

    def test_neighbors_4_directional(self):
        """4-directional movement returns 4 neighbors."""
        neighbors = get_neighbors((5, 5), allow_diagonals=False)
        assert len(neighbors) == 4
        assert (5, 4) in neighbors  # North
        assert (5, 6) in neighbors  # South
        assert (4, 5) in neighbors  # West
        assert (6, 5) in neighbors  # East
        # Diagonals should NOT be included
        assert (4, 4) not in neighbors
        assert (6, 6) not in neighbors


# ============================================================================
# Basic Pathfinding Tests
# ============================================================================

class TestBasicPathfinding:
    """Test basic pathfinding scenarios."""

    def test_straight_line_path(self):
        """Path from (0,0) to (5,0) is a straight line."""
        game_map = SimpleMockMap(width=10, height=10)
        path = find_path(game_map, (0, 0), (5, 0))

        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (5, 0)
        assert len(path) == 6  # 0,1,2,3,4,5

    def test_diagonal_path(self):
        """Diagonal path from (0,0) to (5,5)."""
        game_map = SimpleMockMap(width=10, height=10)
        path = find_path(game_map, (0, 0), (5, 5))

        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (5, 5)
        # With diagonals, should be ~6 steps
        assert len(path) <= 7

    def test_l_shaped_path(self):
        """L-shaped path around obstacle."""
        # Create vertical wall at x=3
        walls = [(3, y) for y in range(5)]
        game_map = SimpleMockMap(width=10, height=10, walls=walls)

        path = find_path(game_map, (0, 2), (6, 2))

        assert path is not None
        assert path[0] == (0, 2)
        assert path[-1] == (6, 2)
        # Path must go around wall
        assert all((3, 2) != pos for pos in path)

    def test_no_path_exists(self):
        """Returns None when no path exists."""
        # Create complete wall barrier
        walls = [(3, y) for y in range(10)]
        game_map = SimpleMockMap(width=10, height=10, walls=walls)

        path = find_path(game_map, (0, 0), (9, 0))

        assert path is None

    def test_start_equals_goal(self):
        """Returns single-element path when start == goal."""
        game_map = SimpleMockMap(width=10, height=10)
        path = find_path(game_map, (5, 5), (5, 5))

        assert path == [(5, 5)]


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_start_out_of_bounds(self):
        """Returns None if start is out of bounds."""
        game_map = SimpleMockMap(width=10, height=10)
        path = find_path(game_map, (-1, 0), (5, 5))

        assert path is None

    def test_goal_out_of_bounds(self):
        """Returns None if goal is out of bounds."""
        game_map = SimpleMockMap(width=10, height=10)
        path = find_path(game_map, (5, 5), (20, 20))

        assert path is None

    def test_start_not_walkable(self):
        """Returns None if start position is a wall."""
        walls = [(0, 0)]
        game_map = SimpleMockMap(width=10, height=10, walls=walls)
        path = find_path(game_map, (0, 0), (5, 5))

        assert path is None

    def test_goal_not_walkable(self):
        """Returns None if goal position is a wall."""
        walls = [(5, 5)]
        game_map = SimpleMockMap(width=10, height=10, walls=walls)
        path = find_path(game_map, (0, 0), (5, 5))

        assert path is None

    def test_surrounded_by_walls(self):
        """Returns None if completely boxed in."""
        # Surround position (5, 5)
        walls = [
            (4, 4), (5, 4), (6, 4),
            (4, 5),         (6, 5),
            (4, 6), (5, 6), (6, 6),
        ]
        game_map = SimpleMockMap(width=10, height=10, walls=walls)
        path = find_path(game_map, (5, 5), (0, 0))

        assert path is None


# ============================================================================
# Helper Function Tests
# ============================================================================

class TestHelperFunctions:
    """Test convenience helper functions."""

    def test_get_next_step_basic(self):
        """get_next_step returns second position in path."""
        game_map = SimpleMockMap(width=10, height=10)
        next_pos = get_next_step(game_map, (0, 0), (5, 0))

        assert next_pos is not None
        # Should be one step towards goal
        assert next_pos[0] == 1  # x increases
        assert next_pos[1] == 0  # y stays same

    def test_get_next_step_no_path(self):
        """get_next_step returns None when no path exists."""
        walls = [(3, y) for y in range(10)]
        game_map = SimpleMockMap(width=10, height=10, walls=walls)
        next_pos = get_next_step(game_map, (0, 0), (9, 0))

        assert next_pos is None

    def test_get_direction_basic(self):
        """get_direction returns direction vector."""
        game_map = SimpleMockMap(width=10, height=10)
        direction = get_direction(game_map, (5, 5), (8, 5))

        assert direction is not None
        # Should move right (+x)
        assert direction[0] > 0
        # Should stay on same y
        assert direction[1] == 0

    def test_get_direction_diagonal(self):
        """get_direction can return diagonal direction."""
        game_map = SimpleMockMap(width=10, height=10)
        direction = get_direction(game_map, (0, 0), (5, 5))

        assert direction is not None
        # Should move diagonally (both dx and dy positive)
        assert direction[0] >= 0
        assert direction[1] >= 0

    def test_distance_helper(self):
        """distance() helper works with different metrics."""
        assert distance((0, 0), (3, 4), metric='manhattan') == 7
        assert distance((0, 0), (3, 4), metric='euclidean') == 5.0
        assert distance((0, 0), (3, 4), metric='chebyshev') == 4


# ============================================================================
# Movement Mode Tests
# ============================================================================

class TestMovementModes:
    """Test different movement modes."""

    def test_4_directional_movement(self):
        """4-directional mode only uses cardinal directions."""
        game_map = SimpleMockMap(width=10, height=10)
        path = find_path(
            game_map,
            (0, 0),
            (2, 2),
            allow_diagonals=False
        )

        assert path is not None
        # With only cardinal moves, path should be longer
        assert len(path) == 5  # (0,0) -> (1,0) -> (2,0) -> (2,1) -> (2,2)

        # Check that consecutive positions are cardinal (not diagonal)
        for i in range(len(path) - 1):
            dx = abs(path[i+1][0] - path[i][0])
            dy = abs(path[i+1][1] - path[i][1])
            # Cardinal: one of dx or dy is 0, the other is 1
            assert (dx == 0 and dy == 1) or (dx == 1 and dy == 0)

    def test_8_directional_movement(self):
        """8-directional mode uses diagonals."""
        game_map = SimpleMockMap(width=10, height=10)
        path = find_path(
            game_map,
            (0, 0),
            (2, 2),
            allow_diagonals=True
        )

        assert path is not None
        # With diagonals, path should be shorter
        assert len(path) == 3  # (0,0) -> (1,1) -> (2,2)


# ============================================================================
# Real Map Tests
# ============================================================================

class TestWithRealMap:
    """Test pathfinding with actual game Map."""

    def test_pathfinding_on_generated_map(self):
        """Pathfinding works on real BSP-generated map."""
        game_map = Map(width=40, height=20)

        # Find two walkable positions
        start = game_map.find_starting_position()
        monster_positions = game_map.find_monster_positions(1)

        if monster_positions:
            goal = monster_positions[0]
            path = find_path(game_map, start, goal)

            # Should find a path (rooms are connected)
            assert path is not None
            assert path[0] == start
            assert path[-1] == goal

            # Every position in path should be walkable
            for pos in path:
                assert game_map.is_walkable(*pos)

    def test_get_next_step_on_real_map(self):
        """get_next_step works on real map."""
        game_map = Map(width=40, height=20)

        start = game_map.find_starting_position()
        monster_positions = game_map.find_monster_positions(1)

        if monster_positions:
            goal = monster_positions[0]
            next_step = get_next_step(game_map, start, goal)

            assert next_step is not None
            assert game_map.is_walkable(*next_step)


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.slow
class TestPerformance:
    """Test pathfinding performance."""

    def test_large_map_performance(self):
        """Pathfinding completes quickly on large maps."""
        import time

        game_map = Map(width=80, height=24)
        start = game_map.find_starting_position()
        monster_positions = game_map.find_monster_positions(1)

        if monster_positions:
            goal = monster_positions[0]

            start_time = time.time()
            path = find_path(game_map, start, goal)
            elapsed = time.time() - start_time

            # Should complete in under 100ms for 80x24 map
            assert elapsed < 0.1
            assert path is not None

    def test_many_paths(self):
        """Can compute many paths quickly."""

        import time

        game_map = SimpleMockMap(width=50, height=50)

        start_time = time.time()
        for i in range(100):
            find_path(game_map, (0, 0), (49, 49))
        elapsed = time.time() - start_time

        # 100 paths should complete in under 1 second
        assert elapsed < 1.0
