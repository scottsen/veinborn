"""Summon: call a minion onto a free tile nearby.

Config (from the user's behaviour or monsters.yaml abilities block):
minion_type (monsters.yaml id), max_minions (living at once), range (summon
only when the target is this close), min_distance (not when the target is
closer than this), cooldown. Minions are tracked in the user's `minion_ids`
stat. Needs the AI system (AISystem.summon creates the monster).
"""

from ...base.action import ActionOutcome
from ...extensions import ability
from ...geometry import chebyshev


def living_minions(context, actor):
    alive = []
    for entity_id in actor.get_stat('minion_ids', []):
        entity = context.get_entity(entity_id)
        if entity is not None and entity.is_alive:
            alive.append(entity_id)
    return alive


def _worth_summoning(context, actor, config, target):
    if target is None or len(living_minions(context, actor)) >= config.get('max_minions', 3):
        return False
    dist = chebyshev(actor.x, actor.y, target.x, target.y)
    return config.get('min_distance', 0) <= dist <= config.get('range', 8)


@ability("summon", should_use=_worth_summoning)
def summon(context, actor, config, target=None) -> ActionOutcome:
    minions = living_minions(context, actor)
    if len(minions) >= config.get('max_minions', 3):
        return ActionOutcome.failure("Enough minions already.")
    ai = context.get_system('ai')
    if ai is None:
        return ActionOutcome.failure("Nothing answers the call.")
    minion = ai.summon(actor, config.get('minion_type', 'goblin'))
    if minion is None:
        return ActionOutcome.failure("No room for a minion.")
    actor.set_stat('minion_ids', minions + [minion.entity_id])
    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append(f"{actor.name} chants, and a {minion.name} appears!")
    return outcome
