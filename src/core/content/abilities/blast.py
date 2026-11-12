"""Area blasts: hellfire (demon), reality_warp (ancient horror).

Aimed at a hostile in range and sight; damages every hostile of the caster
within aoe_radius (8-way steps) of that target, auto-hit. Config: damage (or
damage_min/max), aoe_radius, range (default 5), cooldown.
"""

from ...base.action import ActionOutcome
from ...extensions import ability
from ...geometry import chebyshev
from ...targeting import aim, valid_target
from .force_bolt import hit_for, roll_damage


def _blast(name: str):
    label = name.replace('_', ' ')

    def worthwhile(context, actor, config, target):
        return valid_target(context, actor, target, config.get('range', 5))

    @ability(name, should_use=worthwhile)
    def effect(context, actor, config, target=None) -> ActionOutcome:
        center = aim(context, actor, target, config.get('range', 5))
        if center is None:
            return ActionOutcome.failure(f"No target for {label}.")
        radius = config.get('aoe_radius', 1)
        caught = [
            e for e in context.hostiles_of(actor)
            if chebyshev(e.x, e.y, center.x, center.y) <= radius
        ]
        outcome = ActionOutcome.success(took_turn=True)
        damage = roll_damage(context, actor, config)
        for victim in caught:
            hit_for(context, actor, victim, damage, label, outcome)
        return outcome

    effect.__name__ = name
    return effect


hellfire = _blast("hellfire")
reality_warp = _blast("reality_warp")
