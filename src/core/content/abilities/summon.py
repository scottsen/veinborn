"""Summon: call minions onto free tiles nearby.

Registered as `summon` (the summoner behaviour) and as the monster abilities
bat_swarm (vampire), summon_undead (lich) and summon_horrors (ancient horror).

Config (from the user's behaviour or monsters.yaml abilities block):
minion_type or minion_types (monsters.yaml ids; a list is drawn from at random),
count (minions per use, default 1), max_minions (living at once), range (summon
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


def summon(context, actor, config, target=None) -> ActionOutcome:
    minions = living_minions(context, actor)
    room = config.get('max_minions', 3) - len(minions)
    if room <= 0:
        return ActionOutcome.failure("Enough minions already.")
    ai = context.get_system('ai')
    if ai is None:
        return ActionOutcome.failure("Nothing answers the call.")
    kinds = config.get('minion_types') or [config.get('minion_type', 'goblin')]
    rng = context.get_rng()
    called = []
    for _ in range(min(room, config.get('count', 1))):
        minion = ai.summon(actor, kinds[0] if len(kinds) == 1 else rng.choice(kinds))
        if minion is None:
            break  # no free tile left
        called.append(minion)
    if not called:
        return ActionOutcome.failure("No room for a minion.")
    actor.set_stat('minion_ids', minions + [m.entity_id for m in called])
    outcome = ActionOutcome.success(took_turn=True)
    names = ", ".join(m.name for m in called)
    outcome.messages.append(f"{actor.name} chants, and {names} appear{'s' if len(called) == 1 else ''}!")
    return outcome


for _name in ("summon", "bat_swarm", "summon_undead", "summon_horrors"):
    ability(_name, should_use=_worth_summoning)(summon)
