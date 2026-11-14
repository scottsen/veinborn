"""Fog of war, per viewer (VB-105, plan D4).

What a viewer has seen of a floor is remembered on the `Map` (`Map.explored_by`, keyed by
the viewer's entity id), so each player has their own memory and a new floor starts empty.
`build_snapshot` is the only reader: it asks `observe` what is lit now and what is
remembered, then hides the rest. The rules (AI, combat) never look at it.
"""

from typing import Set, Tuple

from .geometry import has_line_of_sight

VISION_RADIUS = 9
UNSEEN = ' '        # the tile char a snapshot sends for a tile the viewer has never seen

Cell = Tuple[int, int]


def can_see(game_map, x: int, y: int, tx: int, ty: int, radius: int = VISION_RADIUS) -> bool:
    """Is (tx, ty) within `radius` of (x, y) with nothing opaque in between?"""
    if (tx - x) ** 2 + (ty - y) ** 2 > radius * radius:
        return False
    return has_line_of_sight(x, y, tx, ty, game_map.is_transparent)


def observe(game_map, viewer_id: str, x: int, y: int, radius: int = VISION_RADIUS) -> Set[Cell]:
    """Update `viewer_id`'s memory of `game_map` from (x, y); return the cells lit right now.

    A cell is lit when it is within `radius` (Euclidean) and nothing opaque lies strictly
    between it and the viewer, so the wall that stops the sight is itself seen.
    """
    lit: Set[Cell] = {(x, y)}
    r2 = radius * radius
    for tx in range(max(0, x - radius), min(game_map.width, x + radius + 1)):
        for ty in range(max(0, y - radius), min(game_map.height, y + radius + 1)):
            if (tx - x) ** 2 + (ty - y) ** 2 > r2 or (tx, ty) == (x, y):
                continue
            if has_line_of_sight(x, y, tx, ty, game_map.is_transparent):
                lit.add((tx, ty))
    game_map.explored_by.setdefault(viewer_id, set()).update(lit)
    return lit
