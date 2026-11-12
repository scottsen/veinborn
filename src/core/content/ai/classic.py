"""The five classic AI behaviours. Tuning lives in data/balance/ai_behaviors.yaml."""

from ...extensions import ai_behavior
from ...geometry import chebyshev


@ai_behavior("aggressive")
def aggressive(ai, monster, config):
    """Chase and attack the nearest player."""
    player = ai.nearest_player(monster)
    if not player:
        ai.wander(monster)
        return

    if monster.is_adjacent(player):
        ai.attack(monster, player)
    elif ai.distance(monster, player) <= config.get('chase_range', 10):
        ai.move_towards(monster, player)
    else:
        ai.wander(monster)


@ai_behavior("defensive")
def defensive(ai, monster, config):
    """Attack when close, flee when low on HP, otherwise patrol."""
    player = ai.nearest_player(monster)
    if not player:
        ai.wander(monster)
        return

    if monster.hp / monster.max_hp < config.get('flee_threshold', 0.3):
        ai.flee_from(monster, player)
    elif monster.is_adjacent(player):
        ai.attack(monster, player)
    elif ai.distance(monster, player) <= config.get('chase_range', 5):
        ai.move_towards(monster, player)
    else:
        ai.wander(monster)


@ai_behavior("passive")
def passive(ai, monster, config):
    """Wander peacefully; flee when hurt after being attacked."""
    player = ai.nearest_player(monster)
    if not player:
        ai.wander(monster)
        return

    if monster.get_stat('was_attacked_last_turn', False):
        if monster.hp / monster.max_hp < config.get('flee_threshold', 0.5):
            ai.flee_from(monster, player)
            monster.set_stat('was_attacked_last_turn', False)
            return

    ai.wander(monster)


@ai_behavior("coward")
def coward(ai, monster, config):
    """Always flee from the nearest player."""
    player = ai.nearest_player(monster)
    if not player:
        ai.wander(monster)
        return

    if ai.distance(monster, player) <= config.get('flee_range', 8):
        ai.flee_from(monster, player)
    else:
        ai.wander(monster)


class _Spot:
    """A bare position, so a monster can path back to where it spawned."""

    def __init__(self, x, y):
        self.x = x
        self.y = y


@ai_behavior("guard")
def guard(ai, monster, config):
    """Defend the spawn area: attack players inside the radius, never leave it."""
    player = ai.nearest_player(monster)

    spawn_x = monster.get_stat('spawn_x', monster.x)
    spawn_y = monster.get_stat('spawn_y', monster.y)
    guard_radius = config.get('guard_radius', 4)

    from_spawn = chebyshev(monster.x, monster.y, spawn_x, spawn_y)
    if from_spawn > guard_radius:
        ai.move_towards(monster, _Spot(spawn_x, spawn_y))
        return

    if not player:
        ai.wander(monster)
        return

    if monster.is_adjacent(player):
        ai.attack(monster, player)
    elif ai.distance(monster, player) <= config.get('chase_range', 6):
        # Hold the line rather than step out of the leash (no border flip-flop)
        ai.move_towards(monster, player, leash=(spawn_x, spawn_y, guard_radius))
    else:
        ai.wander(monster)
