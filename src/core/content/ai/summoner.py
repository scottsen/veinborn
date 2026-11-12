"""Summoner tactics: keep away and let minions fight. The summoning is the summon ability.

ai_behaviors.yaml `summoner.abilities` gives every summoner `summon`; the engine
uses it (before these tactics) when it is ready and worthwhile.
"""

from ...extensions import ai_behavior


@ai_behavior("summoner")
def summoner(ai, monster, config):
    player = ai.perceive(monster, config)
    if not player:
        ai.wander(monster)
        return

    distance = ai.distance(monster, player)
    if distance < config.get('summon_distance', 8):
        ai.flee_from(monster, player)  # keep the minions between us
    else:
        ai.wander(monster)
