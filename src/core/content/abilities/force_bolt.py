"""Mage force bolt: ranged, never misses, ignores defense. Config: formulas.yaml abilities.force_bolt."""

import logging

from ...actions.attack_action import AttackAction
from ...base.action import ActionOutcome
from ...base.entity import EntityType
from ...events import create_attack_event
from ...extensions import ability
from ...geometry import has_line_of_sight

logger = logging.getLogger(__name__)


def _nearest_visible_monster(context, actor, max_range: int):
    game_map = context.get_map()
    best, best_dist = None, None
    for monster in context.get_entities_by_type(EntityType.MONSTER):
        if not monster.is_alive or monster.x is None:
            continue
        dist = max(abs(monster.x - actor.x), abs(monster.y - actor.y))
        if dist > max_range or (best_dist is not None and dist >= best_dist):
            continue
        if has_line_of_sight(actor.x, actor.y, monster.x, monster.y, game_map.is_transparent):
            best, best_dist = monster, dist
    return best


@ability("force_bolt")
def force_bolt(context, actor, config) -> ActionOutcome:
    target = _nearest_visible_monster(context, actor, config['range'])
    if target is None:
        return ActionOutcome.failure("No target in sight for a force bolt.")

    level = actor.get_stat('level', 1)
    damage = context.get_rng().randint(config['damage_min'], config['damage_max'])
    damage += int(config['damage_per_level'] * (level - 1))
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
        # Same death handling as melee: message, died event, XP, loot
        AttackAction(actor.entity_id, target.entity_id)._handle_target_death(
            context, actor, target, outcome
        )
    logger.info(
        "Force bolt",
        extra={'actor_id': actor.entity_id, 'target_id': target.entity_id, 'damage': dealt},
    )
    return outcome
