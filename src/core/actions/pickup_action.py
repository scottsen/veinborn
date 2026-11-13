"""
PickupAction - manually pick up items from the ground.

Handles:
- Item pickup at player's position
- Inventory capacity checks
- Multiple items on same tile
"""

import logging
from dataclasses import dataclass
from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from ..base.entity import EntityType

logger = logging.getLogger(__name__)


def items_at(context: GameContext, x: int, y: int) -> list:
    """Live items lying on (x, y)."""
    return context.get_entities_at(x, y, entity_type=EntityType.ITEM, alive_only=True)


def take_item(actor, item, outcome: ActionOutcome, position) -> bool:
    """Move item into actor's inventory and record the item_picked_up event.

    Shared by manual pickup (PickupAction) and walking over items (MoveAction
    autopickup). Returns False, changing nothing, when the inventory is full.
    """
    if not actor.add_to_inventory(item):
        return False
    outcome.events.append({
        'type': 'item_picked_up',
        'actor_id': actor.entity_id,
        'item_id': item.entity_id,
        'item_name': item.name,
        'position': position,
    })
    return True


def _pickup_messages(picked_up: list, failed: list) -> list:
    messages = []
    if len(picked_up) == 1:
        messages.append(f"Picked up {picked_up[0]}")
    elif picked_up:
        messages.append(f"Picked up {len(picked_up)} items: {', '.join(picked_up)}")
    if len(failed) == 1:
        messages.append(f"Inventory full! Could not pick up {failed[0]}")
    elif failed:
        messages.append(f"Inventory full! Could not pick up {len(failed)} items")
    return messages


@dataclass
class PickupAction(Action):
    """Pick up all items at actor's position."""

    actor_id: str

    def validate(self, context: GameContext) -> bool:
        """Check if pickup is valid (player only)."""
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False

        # Only players can manually pick up items
        from ..entities import Player
        if not isinstance(actor, Player):
            self._log_validation_failure(
                "non-player entity cannot pick up items",
                actor_name=actor.name
            )
            return False

        self._log_validation_success(
            "validated successfully",
            actor_name=actor.name,
            position=(actor.x, actor.y)
        )
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute pickup."""
        actor = self._get_actor(context)
        if not actor:
            logger.error("PickupAction execution failed: actor not found",
                        extra={'actor_id': self.actor_id})
            return ActionOutcome.failure("Actor not found")

        items_here = items_at(context, actor.x, actor.y)
        if not items_here:
            outcome = ActionOutcome.success(took_turn=False)
            outcome.messages.append("There are no items here to pick up.")
            logger.debug(f"No items to pick up at ({actor.x}, {actor.y})")
            return outcome

        outcome = ActionOutcome.success(took_turn=True)
        picked_up, failed = [], []
        for item in items_here:
            if take_item(actor, item, outcome, (actor.x, actor.y)):
                picked_up.append(item.name)
                logger.info(f"Pickup: {actor.name} picked up {item.name}")
            else:
                failed.append(item.name)
                logger.debug(f"Pickup failed: inventory full for {item.name}")

        # Nothing was taken (inventory full): a no-op shouldn't cost a turn
        outcome.took_turn = bool(picked_up)
        outcome.messages.extend(_pickup_messages(picked_up, failed))

        logger.info(
            f"PickupAction executed: {actor.name}",
            extra={
                'actor_id': self.actor_id,
                'actor_name': actor.name,
                'position': (actor.x, actor.y),
                'picked_up': len(picked_up),
                'failed': len(failed),
            }
        )

        return outcome

    def to_dict(self) -> dict:
        return {
            'action_type': 'PickupAction',
            'actor_id': self.actor_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PickupAction':
        return cls(
            actor_id=data['actor_id'],
        )
