"""Force bolt: ranged, never misses, ignores defense. Config: formulas.yaml abilities.force_bolt.

Any actor can cast it (the mage on z; a monster given it in monsters.yaml).
"""

import logging

from ...actions.attack_action import AttackAction
from ...base.action import ActionOutcome
from ...events import create_attack_event
from ...extensions import ability
from ...targeting import aim, valid_target

logger = logging.getLogger(__name__)


def _worth_casting(context, actor, config, target):
    return valid_target(context, actor, target, config['range'])


@ability("force_bolt", should_use=_worth_casting)
def force_bolt(context, actor, config, target=None) -> ActionOutcome:
    target = aim(context, actor, target, config['range'])
    if target is None:
        return ActionOutcome.failure("No target in sight for a force bolt.")

    level = actor.get_stat('level', 1)
    damage = context.get_rng().randint(config['damage_min'], config['damage_max'])
    damage += int(config.get('damage_per_level', 0) * (level - 1))
    dealt = target.take_damage(damage)

    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append(f"{actor.name}'s force bolt hits {target.name} for {dealt} damage!")
    outcome.events.append(create_attack_event(
        attacker_id=actor.entity_id,
        defender_id=target.entity_id,
        damage=dealt,
        killed=not target.is_alive,
    ))
    if not target.is_alive:
        # Same death handling as melee: message, died event, XP (players), loot (monsters)
        AttackAction(actor.entity_id, target.entity_id)._handle_target_death(
            context, actor, target, outcome
        )
    logger.info(
        "Force bolt",
        extra={'actor_id': actor.entity_id, 'target_id': target.entity_id, 'damage': dealt},
    )
    return outcome
