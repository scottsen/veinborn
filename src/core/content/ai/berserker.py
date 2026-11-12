"""Berserker: aggressive, and enraged (longer chase, announced once) when wounded."""

from ...extensions import ai_behavior


@ai_behavior("berserker")
def berserker(ai, monster, config):
    player = ai.nearest_player(monster)
    if not player:
        ai.wander(monster)
        return

    enraged = monster.hp / monster.max_hp < config.get('enrage_threshold', 0.7)
    chase_range = config.get('chase_range', 8)
    if enraged:
        chase_range = config.get('enraged_chase_range', 15)
        if not monster.get_stat('was_enraged', False):
            monster.set_stat('was_enraged', True)
            ai.context.add_message(f"{monster.name} enters a BERSERK RAGE!")

    if monster.is_adjacent(player):
        ai.attack(monster, player)
    elif ai.distance(monster, player) <= chase_range:
        ai.move_towards(monster, player)
    else:
        ai.wander(monster)
