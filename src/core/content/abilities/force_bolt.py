"""Direct-damage abilities: force bolt (mage) and the monster bolts and strikes.

All auto-hit and ignore defense. Damage is `damage` when given, else
randint(damage_min, damage_max); plus damage_per_level * (level - 1).
Kills get the same death handling as melee (died event, XP for players,
loot for monsters).

- force_bolt (formulas.yaml abilities.force_bolt): range 6.
- fire_bolt, death_bolt (monsters.yaml): ranged, `range` from config.
- aerial_dive, dive_bomb (monsters.yaml): a heavy blow on an adjacent target.
"""

import logging

from ...actions.attack_action import AttackAction
from ...base.action import ActionOutcome
from ...events import create_attack_event
from ...extensions import ability
from ...targeting import aim, valid_target

logger = logging.getLogger(__name__)


def roll_damage(context, actor, config) -> int:
    if 'damage' in config:
        damage = config['damage']
    else:
        damage = context.get_rng().randint(config['damage_min'], config['damage_max'])
    return damage + int(config.get('damage_per_level', 0) * (actor.get_stat('level', 1) - 1))


def hit_for(context, actor, target, damage: int, label: str, outcome: ActionOutcome) -> int:
    """Deal damage directly (no to-hit, no defense), with messages, events and death handling."""
    dealt = target.take_damage(damage)
    outcome.messages.append(f"{actor.name}'s {label} hits {target.name} for {dealt} damage!")
    outcome.events.append(create_attack_event(
        attacker_id=actor.entity_id,
        defender_id=target.entity_id,
        damage=dealt,
        killed=not target.is_alive,
    ))
    if not target.is_alive:
        AttackAction(actor.entity_id, target.entity_id)._handle_target_death(
            context, actor, target, outcome
        )
    return dealt


def _direct(name: str, default_range: int):
    label = name.replace('_', ' ')

    def worthwhile(context, actor, config, target):
        return valid_target(context, actor, target, config.get('range', default_range))

    @ability(name, should_use=worthwhile)
    def effect(context, actor, config, target=None) -> ActionOutcome:
        target = aim(context, actor, target, config.get('range', default_range))
        if target is None:
            return ActionOutcome.failure(f"No target for {label}.")
        outcome = ActionOutcome.success(took_turn=True)
        dealt = hit_for(context, actor, target, roll_damage(context, actor, config), label, outcome)
        logger.info(label.capitalize(), extra={
            'actor_id': actor.entity_id, 'target_id': target.entity_id, 'damage': dealt})
        return outcome

    effect.__name__ = name
    return effect


force_bolt = _direct("force_bolt", default_range=6)
fire_bolt = _direct("fire_bolt", default_range=5)
death_bolt = _direct("death_bolt", default_range=6)
aerial_dive = _direct("aerial_dive", default_range=1)
dive_bomb = _direct("dive_bomb", default_range=1)
