"""
DescendAction - go down stairs to next floor.

Handles:
- Validation (must be standing on stairs)
- Floor transition
- Map regeneration
"""

import logging
from dataclasses import dataclass
from ..base.action import Action, ActionOutcome, ActionResult
from ..base.game_context import GameContext
from ..world import TileType

logger = logging.getLogger(__name__)


@dataclass
class DescendAction(Action):
    """Descend stairs to next floor."""

    actor_id: str

    def validate(self, context: GameContext) -> bool:
        """Check if actor is standing on stairs down."""
        # Use base class helper for actor validation
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False

        # Check if standing on stairs down
        tile = context.game_state.dungeon_map.tiles[actor.x][actor.y]
        if tile.tile_type != TileType.STAIRS_DOWN:
            self._log_validation_failure(
                "not on stairs",
                actor_name=actor.name,
                position=(actor.x, actor.y),
                tile_type=tile.tile_type.name
            )
            return False

        self._log_validation_success(
            "validated successfully",
            actor_name=actor.name,
            position=(actor.x, actor.y)
        )
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Descend to next floor."""
        if not self.validate(context):
            logger.error(
                f"DescendAction execution failed validation",
                extra={'actor_id': self.actor_id}
            )
            return ActionOutcome.failure("You must be standing on stairs to descend")

        actor = self._get_actor(context)
        old_floor = context.game_state.current_floor
        new_floor = old_floor + 1

        logger.info(
            f"DescendAction executed - descending to floor {new_floor}",
            extra={
                'actor_id': self.actor_id,
                'actor_name': actor.name,
                'from_floor': old_floor,
                'to_floor': new_floor,
            }
        )

        outcome = ActionOutcome.success(
            took_turn=True,
            message=f"You descend to floor {new_floor}..."
        )
        self._add_descend_event(outcome, old_floor)

        return outcome

    def _add_descend_event(self, outcome: ActionOutcome, from_floor: int):
        """Add descend event to trigger floor transition."""
        outcome.events.append({
            'type': 'descend_floor',
            'actor_id': self.actor_id,
            'from_floor': from_floor,
        })

    def to_dict(self) -> dict:
        return {
            'action_type': 'DescendAction',
            'actor_id': self.actor_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DescendAction':
        return cls(actor_id=data['actor_id'])
