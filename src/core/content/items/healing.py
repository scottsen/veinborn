"""Healing consumables: potions heal at once (heal, heal_full); food and the
regeneration potion heal over time (eat, regenerate).

Instant amounts are the item's ``heal_amount`` stat from items.yaml. Over-time items
start the ``regeneration`` status effect: ``regen_amount`` HP a turn for ``regen_turns``
turns (``heal_amount`` is their total, for display and for the bots' choice). Food also
has ``nutrition``; there is no hunger yet.
"""
from ...base.action import ActionOutcome
from ...extensions import item_effect
from ...status_effects import add_effect


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
    # Food that names no regen_turns still heals at once (data written before VB-107)
    if item.get_stat('regen_turns', 0) > 0:
        return _regenerate(actor, item, "eats")
    return _heal_by(actor, item, item.get_stat('heal_amount', 0), "eats")


def _regenerate(actor, item, verb):
    if actor.hp >= actor.max_hp:
        return ActionOutcome.failure("You are already at full health.")
    turns = item.get_stat('regen_turns', 0)
    amount = item.get_stat('regen_amount', 0)
    if turns <= 0 or amount <= 0:
        return ActionOutcome.failure(f"The {item.name} does nothing.")
    add_effect(actor, 'regeneration', turns, amount)
    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append(f"{actor.name} {verb} the {item.name} and starts to recover ({amount} HP a turn).")
    return outcome


@item_effect("regenerate")
def regenerate(context, actor, item) -> ActionOutcome:
    return _regenerate(actor, item, "drinks")
