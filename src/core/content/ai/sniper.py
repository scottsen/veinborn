"""Sniper tactics: hold at ideal range. The shot itself is the ranged_attack ability.

ai_behaviors.yaml `sniper.abilities` gives every sniper ranged_attack; the engine
uses it (before these tactics) whenever there is a clear shot.
"""

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
    elif distance > high or not ai.in_sight(monster, player):
        ai.move_towards(monster, player)  # no clear shot: reposition
    # else: in ideal range with a clear shot; hold (the engine shoots when ready)
