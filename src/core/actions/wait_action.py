"""
WaitAction - actor does nothing this turn.

Used by:
- Player "wait in place" binding (`.`/space)
- Multiplayer disconnected-player fallback (AI no-op)
"""

import logging
from dataclasses import dataclass
from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext

logger = logging.getLogger(__name__)


@dataclass
class WaitAction(Action):
    """Consume a turn without acting."""

    actor_id: str
    quiet: bool = False     # no "X waits." log line (a local host resting would flood the log)

    def validate(self, context: GameContext) -> bool:
        actor = self._get_and_validate_actor(context)
        return actor is not None

    def execute(self, context: GameContext) -> ActionOutcome:
        actor = self._get_actor(context)
        if not actor:
            return ActionOutcome.failure("Actor not found")

        # Natural regeneration reads this (TurnProcessor): resting speeds it up (VB-107)
        actor.set_stat('rested_turn', context.get_turn_count())
        outcome = ActionOutcome.success(took_turn=True)
        if not self.quiet:
            outcome.messages.append(f"{actor.name} waits.")
        outcome.events.append({
            'type': 'actor_waited',
            'actor_id': self.actor_id,
            'position': (actor.x, actor.y),
        })
        logger.debug(f"WaitAction executed: {actor.name} at ({actor.x}, {actor.y})")
        return outcome

    def to_dict(self) -> dict:
        return {
            'action_type': 'WaitAction',
            'actor_id': self.actor_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WaitAction':
        return cls(actor_id=data['actor_id'])
