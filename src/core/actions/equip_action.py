"""
EquipAction - equip or unequip weapons and armor.

This completes the crafting loop:
- Player mines ore (MineAction)
- Player brings ore to forge
- Player crafts equipment (CraftAction)
- Player equips gear (EquipAction) ← YOU ARE HERE
- Player fights with better stats

Design:
- Equip items from inventory
- Unequip items back to inventory
- Validates equipment slot (weapon/armor)
- Handles swapping (unequip old, equip new)
"""

import logging
from dataclasses import dataclass
from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from ..entities import Player
from ..equipment import SLOT_ATTR, SLOT_STAT, gear_bonus, gear_slot

logger = logging.getLogger(__name__)


@dataclass
class EquipAction(Action):
    """Equip or unequip an item."""

    free = True  # never uses up the player's action for the round

    actor_id: str
    item_id: str  # Item to equip from inventory

    def validate(self, context: GameContext) -> bool:
        """Check if equipping is valid."""
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False

        # Must be a Player
        if not isinstance(actor, Player):
            self._log_validation_failure("only players can equip items", actor_id=self.actor_id)
            return False

        # Validate item is equippable from inventory
        item = self._find_item_in_inventory(actor)
        if not item:
            return False

        equipment_slot = self._validate_equipment_slot(item)
        if not equipment_slot:
            return False

        self._log_validation_success(
            "validated successfully",
            actor_name=actor.name,
            item_name=item.name,
            equipment_slot=equipment_slot
        )
        return True

    def _find_item_in_inventory(self, actor):
        """Find and validate item exists in actor's inventory."""
        for inv_item in actor.inventory:
            if inv_item.entity_id == self.item_id:
                return inv_item

        self._log_validation_failure(
            "item not in inventory",
            actor_id=self.actor_id,
            item_id=self.item_id
        )
        return None

    def _validate_equipment_slot(self, item) -> str:
        """The item's wearable slot ('weapon' or 'armor'), or None (and a logged reason)."""
        equipment_slot = gear_slot(item)
        if not equipment_slot:
            self._log_validation_failure(
                "item is not equippable",
                item_id=self.item_id,
                item_name=item.name,
                item_type=item.get_stat('item_type')
            )
        return equipment_slot

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute equipment action."""
        if not self.validate(context):
            logger.warning("EquipAction execution failed validation",
                        extra={'actor_id': self.actor_id, 'item_id': self.item_id})
            return ActionOutcome.failure("Cannot equip item")

        actor = self._get_actor(context)
        item = self._find_item_in_inventory(actor)
        if not item:
            return ActionOutcome.failure("Item not found")

        logger.info("EquipAction started",
                   extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                         'item_id': self.item_id, 'item_name': item.name})

        # Handle equipping based on slot
        equipment_slot = gear_slot(item)
        messages = self._equip_item(actor, item, equipment_slot)

        # Add total stats summary
        messages.append(f"Total stats: Attack {actor.get_total_attack()}, Defense {actor.get_total_defense()}")

        outcome = ActionOutcome.success(took_turn=False)
        outcome.messages.extend(messages)
        self._add_equip_event(outcome, equipment_slot)

        return outcome

    def _equip_item(self, actor, item, equipment_slot: str) -> list:
        """Wear `item`; the item worn in that slot goes back to the pack.

        The new item leaves the pack first, so the old one always has a slot:
        the other order dropped the old gear when the pack was full.
        """
        attr = SLOT_ATTR[equipment_slot]
        stat = SLOT_STAT[equipment_slot]
        old = getattr(actor, attr)

        actor.remove_from_inventory(item)
        messages = []
        if old:
            actor.add_to_inventory(old)
            messages.append(f"Unequipped {old.name}")
            logger.debug(f"Unequipped {equipment_slot}: {old.name}")

        setattr(actor, attr, item)
        bonus = gear_bonus(item, equipment_slot)
        messages.append(f"Equipped {item.name} (+{bonus} {stat})")
        logger.info(f"Equipped {equipment_slot}: {item.name} with +{bonus} {stat}")
        return messages

    def _add_equip_event(self, outcome: ActionOutcome, equipment_slot: str):
        """Add equipment event to outcome."""
        outcome.events.append({
            'type': 'equipment_equipped',
            'actor_id': self.actor_id,
            'item_id': self.item_id,
            'equipment_slot': equipment_slot,
        })

    def to_dict(self) -> dict:
        return {
            'action_type': 'EquipAction',
            'actor_id': self.actor_id,
            'item_id': self.item_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EquipAction':
        return cls(
            actor_id=data['actor_id'],
            item_id=data['item_id'],
        )
