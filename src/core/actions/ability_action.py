"""
AbilityAction - use an ability (VB-51; any actor since VB-63).

This class is only the dispatcher: it checks that the actor knows the ability
and that it is off cooldown, runs the ability's registered function
(core/content/abilities/, see core.extensions.ability), and starts the cooldown
if the use succeeded. A failed use (no target, on cooldown, full HP) costs no
turn.

Config: players' abilities read data/balance/formulas.yaml `abilities`. The
monster AI passes `config` already resolved for that monster (AISystem.abilities_for),
which also stands for "this monster has the ability".

Passive abilities (rogue backstab) are @damage_modifier content applied by
AttackAction, not actions.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from ..config.config_loader import ConfigLoader
from ..extensions import abilities

logger = logging.getLogger(__name__)


@dataclass
class AbilityAction(Action):
    """Use one of the actor's abilities, optionally aimed at a target."""

    actor_id: str
    ability: str
    target_id: Optional[str] = None
    config: Optional[dict] = None

    def validate(self, context: GameContext) -> bool:
        return self._get_and_validate_actor(context) is not None

    def execute(self, context: GameContext) -> ActionOutcome:
        if not self.validate(context):
            return ActionOutcome.failure("Cannot use abilities now")
        actor = self._get_actor(context)

        effect = abilities.get(self.ability)
        if effect is None:
            return ActionOutcome.failure(f"Unknown ability: {self.ability}")
        if self.config is None and self.ability not in actor.get_stat('abilities', []):
            return ActionOutcome.failure(f"{actor.name} doesn't know {self._label()}.")

        wait = self._cooldown_remaining(actor, context)
        if wait > 0:
            return ActionOutcome.failure(f"{self._label().capitalize()} isn't ready ({wait} more turns).")

        config = self.config if self.config is not None else \
            ConfigLoader.get_config().get_ability_config(self.ability)
        target = context.get_entity(self.target_id) if self.target_id else None
        outcome = effect(context, actor, config, target)
        if outcome.is_success:
            self._start_cooldown(actor, context, config)
        return outcome

    def _label(self) -> str:
        return self.ability.replace('_', ' ')

    def _cooldown_remaining(self, actor, context: GameContext) -> int:
        ready_turn = actor.get_stat('cooldowns', {}).get(self.ability, 0)
        return max(0, ready_turn - context.get_turn_count())

    def _start_cooldown(self, actor, context: GameContext, config: dict) -> None:
        cooldowns = dict(actor.get_stat('cooldowns', {}))
        # +1: a player's action is processed before the turn counter advances, a
        # monster's after; either way `cooldown` whole turns pass between uses
        cooldowns[self.ability] = context.get_turn_count() + config.get('cooldown', 0) + 1
        actor.set_stat('cooldowns', cooldowns)

    def to_dict(self) -> dict:
        return {
            'action_type': 'AbilityAction',
            'actor_id': self.actor_id,
            'ability': self.ability,
            'target_id': self.target_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AbilityAction':
        # config is not serialised: a replayed monster action re-resolves it
        return cls(actor_id=data['actor_id'], ability=data['ability'],
                   target_id=data.get('target_id'))
