"""Healer heal: restore the caster's own HP. Config: formulas.yaml abilities.heal."""

from ...base.action import ActionOutcome
from ...extensions import ability


@ability("heal")
def heal(context, actor, config) -> ActionOutcome:
    if actor.hp >= actor.max_hp:
        return ActionOutcome.failure("You are already at full health.")

    amount = config['amount'] + config['heal_per_level'] * (actor.get_stat('level', 1) - 1)
    healed = actor.heal(amount)

    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append(f"{actor.name} heals {healed} HP.")
    return outcome
