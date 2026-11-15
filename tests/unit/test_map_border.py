"""The outer ring of the map is always wall: no floor you can see toward but never cross.

Small BSP cells (3-5 tiles) used to get a min-size room that filled the cell, so about 1 seed in 5
had floor on the last row/column of the map: the screen showed open ground, the move said
"out of bounds". Rooms are now kept inside the map's interior.
"""
from collections import deque

import pytest

from core.game import Game

pytestmark = pytest.mark.unit


def _map(seed):
    g = Game()
    g.start_new_game(seed=seed)
    return g.state.dungeon_map


@pytest.mark.parametrize("seed", range(120))
def test_the_outer_ring_is_wall_and_the_floor_is_one_connected_piece(seed):
    m = _map(seed)
    w, h = m.width, m.height
    border = [(x, y) for x in range(w) for y in range(h)
              if (x in (0, w - 1) or y in (0, h - 1)) and m.is_walkable(x, y)]
    assert border == []

    floor = {(x, y) for x in range(w) for y in range(h) if m.is_walkable(x, y)}
    start = next(iter(floor))
    seen, queue = {start}, deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in floor and n not in seen:
                seen.add(n)
                queue.append(n)
    assert seen == floor
