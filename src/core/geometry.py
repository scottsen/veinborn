"""
Shared 2D grid geometry helpers.

Single source of truth for Bresenham line stepping, previously hand-rolled
separately in pathfinding.py and twice in perception.py, and for the game's
range metric (chebyshev).
"""

from typing import Callable, Iterator, Tuple


def chebyshev(x0: int, y0: int, x1: int, y1: int) -> int:
    """Range between two tiles: the number of 8-way steps, max(|dx|, |dy|).

    The game's one range metric (ADR-019): AI ranges, ability ranges, leashes and
    spawn distances all use it, because movement and adjacency are 8-directional.
    """
    return max(abs(x0 - x1), abs(y0 - y1))


def bresenham_line(x0: int, y0: int, x1: int, y1: int) -> Iterator[Tuple[int, int]]:
    """
    Yield integer grid points from (x0, y0) to (x1, y1) inclusive, via Bresenham's
    line algorithm.

    Args:
        x0, y0: Starting position
        x1, y1: Ending position

    Yields:
        (x, y) tuples along the line, starting with (x0, y0) and ending with (x1, y1)
    """
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    x, y = x0, y0

    while True:
        yield x, y

        if x == x1 and y == y1:
            return

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def has_line_of_sight(
    x0: int, y0: int, x1: int, y1: int, is_transparent: Callable[[int, int], bool]
) -> bool:
    """
    Check whether every grid point strictly between (x0, y0) and (x1, y1) is
    transparent. The two endpoints themselves are never checked.

    Args:
        x0, y0: Observer position
        x1, y1: Target position
        is_transparent: Predicate returning True if a tile does not block sight

    Returns:
        True if no point between the endpoints blocks sight
    """
    start, end = (x0, y0), (x1, y1)
    for point in bresenham_line(x0, y0, x1, y1):
        if point != start and point != end and not is_transparent(*point):
            return False
    return True
