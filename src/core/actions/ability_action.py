"""
AbilityAction - use a class ability (VB-51).

Active abilities implemented so far:
- force_bolt (mage): ranged, auto-hit, ignores defense, nearest monster in sight
- heal (healer): restore the caster's own HP

Rogue backstab is passive and lives in AttackAction. Abilities have turn
cooldowns (no mana system); a failed use (no target, on cooldown) costs no turn.
Tuning numbers: data/balance/formulas.yaml `abilities`.
"""

import logging
from dataclasses import dataclass

from ..base.action import Action, ActionOutcome
from ..base.entity import EntityType
from ..base.game_context import GameContext
from ..config.config_loader import ConfigLoader
from ..events import create_attack_event
from ..geometry import has_line_of_sight
from .attack_action import AttackAction

logger = logging.getLogger(__name__)

ACTIVE_ABILITIES = ('force_bolt', 'heal')


@dataclass
class AbilityAction(Action):
    """Use one of the actor's class abilities."""

    actor_id: str
    ability: str

    def validate(self, context: GameContext) -> bool:
        return self._get_and_validate_actor(context) is not None

    def execute(self, context: GameContext) -> ActionOutcome:
        if not self.validate(context):
            return ActionOutcome.failure("Cannot use abilities now")
        actor = self._get_actor(context)

        if self.ability not in ACTIVE_ABILITIES:
            return ActionOutcome.failure(f"Unknown ability: {self.ability}")
        if self.ability not in actor.get_stat('abilities', []):
            return ActionOutcome.failure(f"{actor.name} doesn't know {self._label()}.")

        wait = self._cooldown_remaining(actor, context)
        if wait > 0:
            return ActionOutcome.failure(f"{self._label().capitalize()} isn't ready ({wait} more turns).")

        if self.ability == 'force_bolt':
            return self._force_bolt(context, actor)
        return self._heal(context, actor)

    def _label(self) -> str:
        return self.ability.replace('_', ' ')

    def _cooldown_remaining(self, actor, context: GameContext) -> int:
        ready_turn = actor.get_stat('cooldowns', {}).get(self.ability, 0)
        return max(0, ready_turn - context.get_turn_count())

    def _start_cooldown(self, actor, context: GameContext, config: dict) -> None:
        cooldowns = dict(actor.get_stat('cooldowns', {}))
        # +1: the turn this action takes is processed before the next input
        cooldowns[self.ability] = context.get_turn_count() + config['cooldown'] + 1
        actor.set_stat('cooldowns', cooldowns)

    def _force_bolt(self, context: GameContext, actor) -> ActionOutcome:
        config = ConfigLoader.get_config().get_ability_config('force_bolt')
        target = self._nearest_visible_monster(context, actor, config['range'])
        if target is None:
            return ActionOutcome.failure("No target in sight for a force bolt.")

        level = actor.get_stat('level', 1)
        rng = context.get_rng()
        damage = rng.randint(config['damage_min'], config['damage_max'])
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
        self._start_cooldown(actor, context, config)
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

    def _nearest_visible_monster(self, context: GameContext, actor, max_range: int):
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

    def _heal(self, context: GameContext, actor) -> ActionOutcome:
        config = ConfigLoader.get_config().get_ability_config('heal')
        if actor.hp >= actor.max_hp:
            return ActionOutcome.failure("You are already at full health.")

        amount = config['amount'] + config['heal_per_level'] * (actor.get_stat('level', 1) - 1)
        healed = actor.heal(amount)
        self._start_cooldown(actor, context, config)

        outcome = ActionOutcome.success(took_turn=True)
        outcome.messages.append(f"{actor.name} heals {healed} HP.")
        return outcome

    def to_dict(self) -> dict:
        return {
            'action_type': 'AbilityAction',
            'actor_id': self.actor_id,
            'ability': self.ability,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AbilityAction':
        return cls(actor_id=data['actor_id'], ability=data['ability'])
