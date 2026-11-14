"""
UseItemAction - drink, eat or read an item from inventory.

The item names its effect (``effect:`` in items.yaml); the effect is content
registered with ``@item_effect`` (core/content/items/). This action finds the
item, runs the effect, and consumes the item when the effect succeeds. An
effect that is not built yet (buffs, scrolls) refuses without using the item
or a turn.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from ..events import GameEvent, GameEventType
from ..extensions import item_effects

logger = logging.getLogger(__name__)


def usable_effect(item) -> Optional[str]:
    """The item's effect name if that effect is built, else None."""
    effect = item.get_stat('effect')
    return effect if effect and effect in item_effects else None


def best_healing_item(actor, instant_only: bool = False):
    """The healing item to use now, or None.

    Instant healers (potions) come first: the cheapest (items.yaml value) one that covers
    the missing HP, else the one that heals most; that keeps rare potions (full healing)
    for when nothing smaller will do. Only without any instant healer does it fall back to
    an over-time item (food, regeneration potion), which is no answer to an emergency:
    pass `instant_only` to refuse those.
    """
    missing = actor.max_hp - actor.hp
    if missing <= 0:
        return None
    instant, over_time = [], []
    for item in getattr(actor, 'inventory', []):
        effect = usable_effect(item)
        if effect == 'heal_full':
            instant.append((actor.max_hp, item))
        elif effect == 'heal' and item.get_stat('heal_amount', 0) > 0:
            instant.append((item.get_stat('heal_amount'), item))
        elif effect in ('eat', 'regenerate') and item.get_stat('heal_amount', 0) > 0:
            (over_time if item.get_stat('regen_turns', 0) > 0 else instant).append(
                (item.get_stat('heal_amount'), item))
    for healing in ((instant,) if instant_only else (instant, over_time)):
        if not healing:
            continue
        covering = [h for h in healing if h[0] >= missing]
        if covering:
            return min(covering, key=lambda h: (h[1].get_stat('value', 0), h[0]))[1]
        return max(healing, key=lambda h: h[0])[1]
    return None


@dataclass
class UseItemAction(Action):
    """Use (and consume) one item from the actor's inventory."""

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

        effect_name = item.get_stat('effect')
        effect = item_effects.get(effect_name) if effect_name else None
        if effect is None:
            return ActionOutcome.failure(f"You can't use the {item.name}.")

        outcome = effect(context, actor, item)
        if outcome.is_success:
            actor.remove_from_inventory(item)
            outcome.events.append(GameEvent(
                event_type=GameEventType.ITEM_USED,
                data={'actor_id': actor.entity_id, 'item_id': item.entity_id,
                      'item_name': item.name, 'effect': effect_name},
                turn=context.get_turn_count(),
            ).to_dict())
            logger.info("Item used", extra={'actor_id': actor.entity_id,
                                            'item_name': item.name, 'effect': effect_name})
        return outcome

    def to_dict(self) -> dict:
        return {'action_type': 'UseItemAction', 'actor_id': self.actor_id, 'item_id': self.item_id}

    @classmethod
    def from_dict(cls, data: dict) -> 'UseItemAction':
        return cls(actor_id=data['actor_id'], item_id=data['item_id'])
