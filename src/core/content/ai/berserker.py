"""Berserker: aggressive, and enraged (sees farther, announced once) when wounded."""

from ...extensions import ai_behavior


@ai_behavior("berserker")
def berserker(ai, monster, config):
    enraged = monster.hp / monster.max_hp < config.get('enrage_threshold', 0.7)
    if enraged:
        config = {**config, 'aggro_range': max(config.get('aggro_range', 8),
                                                config.get('enraged_aggro_range', 15))}
        if not monster.get_stat('was_enraged', False):
            monster.set_stat('was_enraged', True)
            ai.context.add_message(f"{monster.name} enters a BERSERK RAGE!")

    player = ai.perceive(monster, config)
    if not player:
        ai.wander(monster)
    elif monster.is_adjacent(player):
        ai.attack(monster, player)
    else:
        ai.move_towards(monster, player)
