"""
DropAction - put an item from inventory on the floor.

Without it a 20-slot pack filled with things that cannot be used (gold piles,
shields, scrolls, worse weapons) and nothing could leave it, so mined ore had
nowhere to go and crafting stopped (VB-73). A dropped item is marked with who
dropped it, and autopickup skips it for that player (an explicit pickup still
takes it).

`least_useful_item` is the shared answer to "what should go first": the TUI's
drop key and the bots both use it.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from .use_item_action import usable_effect

logger = logging.getLogger(__name__)

GEAR_SLOTS = ('weapon', 'armor')

# least_useful_item tiers, most droppable first
NO_USE, WORSE_GEAR, ORE, OTHER, HEALING = range(5)


def gear_slot(item) -> Optional[str]:
    """'weapon' or 'armor' if the item can be equipped (EquipAction's rule), else None."""
    slot = item.get_stat('equipment_slot') or item.get_stat('item_type')
    return slot if slot in GEAR_SLOTS else None


def gear_bonus(item, slot) -> int:
    """The bonus that makes gear better in its slot: attack for weapons, defense for armor."""
    return item.get_stat('attack_bonus' if slot == 'weapon' else 'defense_bonus', 0)


def usefulness(actor, item) -> int:
    """How much an item is worth carrying, as a tier (lower drops first).

    NO_USE      no built effect, not equippable, not ore (gold, shields, scrolls, rings)
    WORSE_GEAR  a weapon or armor no better than what is equipped in its slot
    ORE         crafting material
    OTHER       better gear, other usable items
    HEALING     potions and food that heal
    """
    if item.get_stat('ore_type'):
        return ORE
    slot = gear_slot(item)
    if slot:
        worn = getattr(actor, 'equipped_weapon' if slot == 'weapon' else 'equipped_armor', None)
        if worn is not None and gear_bonus(item, slot) <= gear_bonus(worn, slot):
            return WORSE_GEAR
        return OTHER
    effect = usable_effect(item)
    if effect in ('heal', 'heal_full', 'eat'):
        return HEALING
    if effect:
        return OTHER
    return NO_USE


def least_useful_item(actor, max_tier: int = HEALING):
    """The carried item to drop first, or None if nothing is at or below `max_tier`.

    Lowest tier first; within a tier the lowest items.yaml `value` (ore: lowest
    purity), so the rare and good stays.
    """
    candidates = []
    for item in getattr(actor, 'inventory', []):
        tier = usefulness(actor, item)
        if tier <= max_tier:
            worth = item.get_stat('purity', 0) if tier == ORE else item.get_stat('value', 0)
            candidates.append((tier, worth, item))
    if not candidates:
        return None
    return min(candidates, key=lambda c: (c[0], c[1]))[2]


@dataclass
class DropAction(Action):
    """Drop one item from the actor's inventory onto its tile."""

    actor_id: str
    item_id: str

    def _find_item(self, actor):
        for item in getattr(actor, 'inventory', []):
            if item.entity_id == self.item_id:
                return item
        return None

    def validate(self, context: GameContext) -> bool:
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False
        if self._find_item(actor) is None:
            self._log_validation_failure("item not in inventory",
                                         actor_id=self.actor_id, item_id=self.item_id)
            return False
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        if not self.validate(context):
            return ActionOutcome.failure("You don't have that item.")
        actor = self._get_actor(context)
        item = self._find_item(actor)

        actor.remove_from_inventory(item)
        item.x, item.y = actor.x, actor.y
        item.set_stat('dropped_by', actor.entity_id)   # autopickup leaves it for this player
        context.add_entity(item)

        outcome = ActionOutcome.success(took_turn=True)
        outcome.messages.append(f"You drop the {item.name}.")
        outcome.events.append({
            'type': 'item_dropped',
            'actor_id': actor.entity_id,
            'item_id': item.entity_id,
            'item_name': item.name,
            'position': (actor.x, actor.y),
        })
        logger.info("Item dropped", extra={'actor_id': actor.entity_id, 'item_name': item.name})
        return outcome

    def to_dict(self) -> dict:
        return {'action_type': 'DropAction', 'actor_id': self.actor_id, 'item_id': self.item_id}

    @classmethod
    def from_dict(cls, data: dict) -> 'DropAction':
        return cls(actor_id=data['actor_id'], item_id=data['item_id'])
