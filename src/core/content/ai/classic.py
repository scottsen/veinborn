"""The five classic AI behaviours. Tuning lives in data/balance/ai_behaviors.yaml.

Each behaviour asks the engine what the monster knows (ai.perceive: sight within
aggro_range, memory, being attacked) and decides what to do about it. Ranges in
a behaviour's section are engagement policy, not perception.
"""

from ...extensions import ai_behavior
from ...geometry import chebyshev


def _engage(ai, monster, target):
    if monster.is_adjacent(target):
        ai.attack(monster, target)
    else:
        ai.move_towards(monster, target)


@ai_behavior("aggressive")
def aggressive(ai, monster, config):
    """Chase and attack any player it perceives."""
    target = ai.perceive(monster, config)
    if target:
        _engage(ai, monster, target)
    else:
        ai.wander(monster)


@ai_behavior("defensive")
def defensive(ai, monster, config):
    """Engage players that come within chase_range or attack it; flee when low on HP."""
    target = ai.perceive(monster, config)
    if not target:
        ai.wander(monster)
        return

    if monster.hp / monster.max_hp < config.get('flee_threshold', 0.3):
        ai.flee_from(monster, target)
    elif ai.provoked_by(monster, config) is target or ai.distance(monster, target) <= config.get('chase_range', 5):
        _engage(ai, monster, target)
    else:
        ai.wander(monster)


@ai_behavior("neutral")
def neutral(ai, monster, config):
    """Wander peacefully; fight back against whoever attacked it (flee when badly hurt)."""
    attacker = ai.provoked_by(monster, config)
    if not attacker:
        ai.wander(monster)
    elif monster.hp / monster.max_hp < config.get('flee_threshold', 0.5):
        ai.flee_from(monster, attacker)
    else:
        _engage(ai, monster, attacker)


@ai_behavior("coward")
def coward(ai, monster, config):
    """Flee from any player it perceives within flee_range."""
    target = ai.perceive(monster, config)
    if target and ai.distance(monster, target) <= config.get('flee_range', 8):
        ai.flee_from(monster, target)
    else:
        ai.wander(monster)


class _Spot:
    """A bare position, so a monster can path back to where it spawned."""

    def __init__(self, x, y):
        self.x = x
        self.y = y


@ai_behavior("guard")
def guard(ai, monster, config):
    """Defend the spawn area: attack perceived players inside the radius, never leave it."""
    spawn_x = monster.get_stat('spawn_x', monster.x)
    spawn_y = monster.get_stat('spawn_y', monster.y)
    guard_radius = config.get('guard_radius', 4)

    if chebyshev(monster.x, monster.y, spawn_x, spawn_y) > guard_radius:
        ai.move_towards(monster, _Spot(spawn_x, spawn_y))
        return

    target = ai.perceive(monster, config)
    if not target:
        ai.wander(monster)
    elif monster.is_adjacent(target):
        ai.attack(monster, target)
    elif ai.distance(monster, target) <= config.get('chase_range', 6):
        # Hold the line rather than step out of the leash (no border flip-flop)
        ai.move_towards(monster, target, leash=(spawn_x, spawn_y, guard_radius))
    else:
        ai.wander(monster)
