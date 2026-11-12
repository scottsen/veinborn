"""Pathfinding around entity-blocked tiles (ore veins, forges): the `blocked` argument."""

from core.pathfinding import find_path, get_direction


class OpenMap:
    def __init__(self, width=10, height=10, walls=None):
        self.width, self.height, self.walls = width, height, set(walls or [])

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and (x, y) not in self.walls


def test_blocked_tile_is_routed_around():
    path = find_path(OpenMap(), (0, 5), (8, 5), blocked={(4, 5)})
    assert path and (4, 5) not in path and path[-1] == (8, 5)


def test_blocked_blocks_line_of_sight_shortcut():
    # Straight line is clear terrain; only the blocked set forbids it.
    assert (3, 3) in find_path(OpenMap(), (0, 3), (6, 3))
    assert (3, 3) not in find_path(OpenMap(), (0, 3), (6, 3), blocked={(3, 3)})


def test_one_tile_corridor_with_blocker_has_no_path():
    walls = {(x, y) for x in range(10) for y in range(10) if y != 5}
    assert find_path(OpenMap(walls=walls), (0, 5), (9, 5)) is not None
    assert find_path(OpenMap(walls=walls), (0, 5), (9, 5), blocked={(4, 5)}) is None


def test_goal_tile_is_never_blocked():
    path = find_path(OpenMap(), (0, 0), (5, 0), blocked={(5, 0)})
    assert path and path[-1] == (5, 0)


def test_get_direction_passes_blocked_through():
    assert get_direction(OpenMap(), (3, 5), (6, 5), blocked={(4, 5)}) != (1, 0)
