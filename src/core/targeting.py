"""
Targeting helpers shared by abilities and the AI (ADR-019).

Hostility comes from GameContext.is_hostile; range is the game's one metric
(geometry.chebyshev); sight is geometry.has_line_of_sight on the map.
"""

from typing import Optional

from .geometry import chebyshev, has_line_of_sight


def in_range_and_sight(context, actor, target, max_range: int, min_range: int = 0) -> bool:
    """True if target is within [min_range, max_range] 8-way steps of actor and visible."""
    if target is None or actor.x is None or target.x is None:
        return False
    dist = chebyshev(actor.x, actor.y, target.x, target.y)
    if dist > max_range or dist < min_range:
        return False
    game_map = context.get_map()
    return has_line_of_sight(actor.x, actor.y, target.x, target.y, game_map.is_transparent)


def valid_target(context, actor, target, max_range: int, min_range: int = 0) -> bool:
    """A living hostile within range and sight."""
    return (
        target is not None
        and target.is_alive
        and context.is_hostile(actor, target)
        and in_range_and_sight(context, actor, target, max_range, min_range)
    )


def nearest_hostile_in_sight(context, actor, max_range: int, min_range: int = 0) -> Optional[object]:
    """The closest living hostile within range and line of sight, or None."""
    best, best_dist = None, None
    for other in context.hostiles_of(actor):
        dist = chebyshev(actor.x, actor.y, other.x, other.y)
        if best_dist is not None and dist >= best_dist:
            continue
        if in_range_and_sight(context, actor, other, max_range, min_range):
            best, best_dist = other, dist
    return best


def aim(context, actor, target, max_range: int, min_range: int = 0):
    """The given target if it is valid, else (when none was given) the nearest valid one."""
    if target is not None:
        return target if valid_target(context, actor, target, max_range, min_range) else None
    return nearest_hostile_in_sight(context, actor, max_range, min_range)
