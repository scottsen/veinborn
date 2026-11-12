"""Healing consumables: potions (heal, heal_full) and food (eat).

The amount is the item's ``heal_amount`` stat from items.yaml. Food also has
``nutrition``; there is no hunger yet, so eating only heals.
"""
from ...base.action import ActionOutcome
from ...extensions import item_effect


def _heal_by(actor, item, amount, verb):
    if actor.hp >= actor.max_hp:
        return ActionOutcome.failure("You are already at full health.")
    healed = actor.heal(amount)
    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append(f"{actor.name} {verb} the {item.name} and recovers {healed} HP.")
    return outcome


@item_effect("heal")
def heal(context, actor, item) -> ActionOutcome:
    return _heal_by(actor, item, item.get_stat('heal_amount', 0), "drinks")


@item_effect("heal_full")
def heal_full(context, actor, item) -> ActionOutcome:
    return _heal_by(actor, item, actor.max_hp, "drinks")


@item_effect("eat")
def eat(context, actor, item) -> ActionOutcome:
    return _heal_by(actor, item, item.get_stat('heal_amount', 0), "eats")
