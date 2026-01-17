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

logger = logging.getLogger(__name__)


@dataclass
class EquipAction(Action):
    """Equip or unequip an item."""

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
        """Validate item has a valid equipment slot."""
        # Check equipment_slot first, fallback to item_type
        equipment_slot = item.get_stat('equipment_slot') or item.get_stat('item_type')
        if not equipment_slot:
            self._log_validation_failure(
                "item is not equippable",
                item_id=self.item_id,
                item_name=item.name
            )
            return None

        if equipment_slot not in ['weapon', 'armor']:
            self._log_validation_failure(
                "invalid equipment slot",
                item_id=self.item_id,
                equipment_slot=equipment_slot
            )
            return None

        return equipment_slot

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute equipment action."""
        if not self.validate(context):
            logger.error("EquipAction execution failed validation",
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
        # Check equipment_slot first, fallback to item_type
        equipment_slot = item.get_stat('equipment_slot') or item.get_stat('item_type')
        messages = self._equip_item(actor, item, equipment_slot)

        # Add total stats summary
        messages.append(f"Total stats: Attack {actor.get_total_attack()}, Defense {actor.get_total_defense()}")

        outcome = ActionOutcome.success(took_turn=False)
        outcome.messages.extend(messages)
        self._add_equip_event(outcome, equipment_slot)

        return outcome

    def _equip_item(self, actor, item, equipment_slot: str) -> list:
        """Equip item to appropriate slot, handling unequip of old item."""
        messages = []

        if equipment_slot == 'weapon':
            messages.extend(self._equip_weapon(actor, item))
        elif equipment_slot == 'armor':
            messages.extend(self._equip_armor(actor, item))

        return messages

    def _equip_weapon(self, actor, item) -> list:
        """Equip weapon, unequipping old weapon if present."""
        messages = []

        if actor.equipped_weapon:
            old_weapon = actor.equipped_weapon
            actor.add_to_inventory(old_weapon)
            messages.append(f"Unequipped {old_weapon.name}")
            logger.debug(f"Unequipped weapon: {old_weapon.name}")

        actor.equipped_weapon = item
        actor.remove_from_inventory(item)
        attack_bonus = item.get_stat('attack_bonus', 0)
        messages.append(f"Equipped {item.name} (+{attack_bonus} attack)")
        logger.info(f"Equipped weapon: {item.name} with +{attack_bonus} attack")

        return messages

    def _equip_armor(self, actor, item) -> list:
        """Equip armor, unequipping old armor if present."""
        messages = []

        if actor.equipped_armor:
            old_armor = actor.equipped_armor
            actor.add_to_inventory(old_armor)
            messages.append(f"Unequipped {old_armor.name}")
            logger.debug(f"Unequipped armor: {old_armor.name}")

        actor.equipped_armor = item
        actor.remove_from_inventory(item)
        defense_bonus = item.get_stat('defense_bonus', 0)
        messages.append(f"Equipped {item.name} (+{defense_bonus} defense)")
        logger.info(f"Equipped armor: {item.name} with +{defense_bonus} defense")

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
