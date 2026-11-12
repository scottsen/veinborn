"""Heal: restore the caster's own HP. Config: formulas.yaml abilities.heal."""

from ...base.action import ActionOutcome
from ...extensions import ability


def _hurt_enough(context, actor, config, target):
    return actor.hp <= actor.max_hp * config.get('use_below', 0.6)


@ability("heal", should_use=_hurt_enough)
def heal(context, actor, config, target=None) -> ActionOutcome:
    if actor.hp >= actor.max_hp:
        return ActionOutcome.failure("You are already at full health.")

    amount = config['amount'] + config.get('heal_per_level', 0) * (actor.get_stat('level', 1) - 1)
    healed = actor.heal(amount)

    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append(f"{actor.name} heals {healed} HP.")
    return outcome
