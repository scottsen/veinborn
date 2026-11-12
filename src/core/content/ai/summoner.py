"""Summoner: stays away from the player and calls minions to fight for it."""

from ...extensions import ai_behavior


@ai_behavior("summoner")
def summoner(ai, monster, config):
    player = ai.perceive(monster, config)
    if not player:
        ai.wander(monster)
        return

    distance = ai.distance(monster, player)

    if distance < config.get('flee_distance', 4):
        ai.flee_from(monster, player)
        return

    if distance <= config.get('summon_distance', 8) and _ready_to_summon(ai, monster, config):
        minion = ai.summon(monster, config.get('minion_type', 'goblin'))
        if minion:
            minions = _living_minions(ai, monster) + [minion.entity_id]
            monster.set_stat('minion_ids', minions)
            monster.set_stat('last_summon_turn', ai.context.get_turn_count())
            ai.context.add_message(f"{monster.name} chants, and a {minion.name} appears!")
            return

    if distance < config.get('summon_distance', 8):
        ai.flee_from(monster, player)  # keep the minions between us
    else:
        ai.wander(monster)


def _living_minions(ai, monster):
    alive = []
    for entity_id in monster.get_stat('minion_ids', []):
        entity = ai.context.get_entity(entity_id)
        if entity is not None and entity.is_alive:
            alive.append(entity_id)
    return alive


def _ready_to_summon(ai, monster, config) -> bool:
    cooldown = config.get('summon_cooldown', 10)
    since = ai.context.get_turn_count() - monster.get_stat('last_summon_turn', -cooldown)
    return since >= cooldown and len(_living_minions(ai, monster)) < config.get('max_minions', 3)
