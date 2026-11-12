"""Ranged attack: a normal attack (to-hit, damage, defense) from a distance.

Config (from the user's behaviour or monsters.yaml abilities block): range,
min_range (too close to shoot, default 0), cooldown. Used by the sniper.
"""

from ...actions.attack_action import AttackAction
from ...base.action import ActionOutcome
from ...extensions import ability
from ...targeting import aim, valid_target


def _clear_shot(context, actor, config, target):
    return valid_target(context, actor, target, config['range'], config.get('min_range', 0))


@ability("ranged_attack", should_use=_clear_shot)
def ranged_attack(context, actor, config, target=None) -> ActionOutcome:
    target = aim(context, actor, target, config['range'], config.get('min_range', 0))
    if target is None:
        return ActionOutcome.failure("No clear shot.")
    return AttackAction(actor.entity_id, target.entity_id, ranged=True).execute(context)
