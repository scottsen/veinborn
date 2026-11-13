"""
UnequipAction - take a worn weapon or armor off and put it in the pack.

The counterpart of EquipAction. Takes no turn, like equipping. Fails (and the
gear stays on) when nothing is worn in the slot or the pack is full, so gear
is never destroyed.
"""

import logging
from dataclasses import dataclass

from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from ..entities import Player
from ..equipment import GEAR_SLOTS, SLOT_ATTR

logger = logging.getLogger(__name__)


@dataclass
class UnequipAction(Action):
    """Remove the item worn in one slot ('weapon' or 'armor')."""

    actor_id: str
    slot: str

    def validate(self, context: GameContext) -> bool:
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False
        if not isinstance(actor, Player):
            self._log_validation_failure("only players can unequip items", actor_id=self.actor_id)
            return False
        if self.slot not in GEAR_SLOTS:
            self._log_validation_failure("unknown equipment slot", slot=self.slot)
            return False
        if getattr(actor, SLOT_ATTR[self.slot]) is None:
            self._log_validation_failure("nothing worn in that slot", slot=self.slot)
            return False
        if not actor.has_room():
            self._log_validation_failure("pack is full", actor_id=self.actor_id)
            return False
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        if not self.validate(context):
            return ActionOutcome.failure(self._why_not(context))

        actor = self._get_actor(context)
        attr = SLOT_ATTR[self.slot]
        item = getattr(actor, attr)
        setattr(actor, attr, None)
        actor.add_to_inventory(item)
        logger.info(f"Unequipped {self.slot}: {item.name}")

        outcome = ActionOutcome.success(took_turn=False)
        outcome.messages.append(f"Removed {item.name}")
        outcome.messages.append(f"Total stats: Attack {actor.get_total_attack()}, Defense {actor.get_total_defense()}")
        outcome.events.append({
            'type': 'equipment_unequipped',
            'actor_id': self.actor_id,
            'item_id': item.entity_id,
            'equipment_slot': self.slot,
        })
        return outcome

    def _why_not(self, context: GameContext) -> str:
        """The player-facing reason validate() said no."""
        actor = self._get_actor(context)
        if actor is not None and self.slot in GEAR_SLOTS:
            if getattr(actor, SLOT_ATTR[self.slot], None) is None:
                return f"You have no {self.slot} equipped."
            if isinstance(actor, Player) and not actor.has_room():
                return "Your pack is full: drop something first."
        return "Cannot remove that."

    def to_dict(self) -> dict:
        return {'action_type': 'UnequipAction', 'actor_id': self.actor_id, 'slot': self.slot}

    @classmethod
    def from_dict(cls, data: dict) -> 'UnequipAction':
        return cls(actor_id=data['actor_id'], slot=data['slot'])
