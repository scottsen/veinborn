"""
Tests for shared grid geometry helpers (src/core/geometry.py).

Validates:
- bresenham_line() point stepping
- has_line_of_sight() endpoint-exclusion and blocking behavior
"""

import pytest

from src.core.geometry import bresenham_line, has_line_of_sight

pytestmark = pytest.mark.unit


class TestBresenhamLine:
    def test_horizontal_line(self):
        assert list(bresenham_line(0, 0, 3, 0)) == [(0, 0), (1, 0), (2, 0), (3, 0)]

    def test_vertical_line(self):
        assert list(bresenham_line(0, 0, 0, 3)) == [(0, 0), (0, 1), (0, 2), (0, 3)]

    def test_diagonal_line(self):
        assert list(bresenham_line(0, 0, 3, 3)) == [(0, 0), (1, 1), (2, 2), (3, 3)]

    def test_single_point(self):
        assert list(bresenham_line(5, 5, 5, 5)) == [(5, 5)]

    def test_reverse_direction(self):
        assert list(bresenham_line(3, 3, 0, 0)) == [(3, 3), (2, 2), (1, 1), (0, 0)]

    def test_first_and_last_points_are_endpoints(self):
        points = list(bresenham_line(1, 2, 8, 5))
        assert points[0] == (1, 2)
        assert points[-1] == (8, 5)


class TestHasLineOfSight:
    def test_clear_path_returns_true(self):
        assert has_line_of_sight(0, 0, 3, 0, is_transparent=lambda x, y: True)

    def test_blocked_path_returns_false(self):
        blocked = {(1, 0)}
        assert not has_line_of_sight(
            0, 0, 3, 0, is_transparent=lambda x, y: (x, y) not in blocked
        )

    def test_opaque_endpoints_are_not_checked(self):
        # Both start and end are "opaque" (e.g. observer/target standing in a
        # doorway) -- only points strictly between them should be checked.
        assert has_line_of_sight(0, 0, 3, 0, is_transparent=lambda x, y: (x, y) not in {(0, 0), (3, 0)})

    def test_same_position_always_visible(self):
        assert has_line_of_sight(5, 5, 5, 5, is_transparent=lambda x, y: False)
