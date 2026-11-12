"""Sniper: keeps its distance and shoots when the player is in its ideal range."""

from ...extensions import ai_behavior


@ai_behavior("sniper")
def sniper(ai, monster, config):
    player = ai.perceive(monster, config)
    if not player:
        ai.wander(monster)
        return

    distance = ai.distance(monster, player)
    low, high = config.get('ideal_range_min', 4), config.get('ideal_range_max', 6)

    if distance < low:
        ai.flee_from(monster, player)  # a cornered sniper bites back in melee
    elif distance <= high:
        if ai.in_sight(monster, player):
            ai.attack(monster, player, ranged=True)
        else:
            ai.move_towards(monster, player)  # no clear shot: reposition
    else:
        ai.move_towards(monster, player)
