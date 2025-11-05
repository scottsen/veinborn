"""
CraftAction - interact with forge to craft equipment from ore.

This is THE core action of Brogue's unique hook:
- Player mines ore (MineAction)
- Player brings ore to forge
- Player crafts equipment (CraftAction) ← YOU ARE HERE
- Player equips gear (EquipAction)
- Player fights with better stats

Design:
- Requires adjacency to forge
- Shows available recipes based on player's ore
- Consumes ore to create equipment
- Adds equipment to inventory
"""

import logging
from dataclasses import dataclass
from typing import Optional
from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from ..base.entity import EntityType
from ..crafting import RecipeManager

logger = logging.getLogger(__name__)


@dataclass
class CraftAction(Action):
    """Craft equipment at a forge using ore."""

    actor_id: str
    forge_id: str
    recipe_id: str  # Which recipe to craft

    # Class-level recipe manager (loaded once, shared by all actions)
    _recipe_manager: Optional[RecipeManager] = None

    @classmethod
    def get_recipe_manager(cls) -> RecipeManager:
        """Get shared recipe manager instance."""
        if cls._recipe_manager is None:
            cls._recipe_manager = RecipeManager()
        return cls._recipe_manager

    def validate(self, context: GameContext) -> bool:
        """Check if crafting is valid."""
        # Validate actor
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False

        # Validate forge (existence, type, adjacency) - replaces 20 lines with 2
        forge = self._validate_entity(
            context, self.forge_id, EntityType.FORGE,
            entity_name="forge", require_adjacency=True
        )
        if not forge:
            return False

        # Validate recipe exists
        recipe_manager = self.get_recipe_manager()
        recipe = recipe_manager.get_recipe(self.recipe_id)
        if not recipe:
            self._log_validation_failure("recipe not found", recipe_id=self.recipe_id)
            return False

        # Validate player can craft (has required ore)
        current_floor = context.get_floor()
        can_craft, reason = recipe_manager.can_craft(
            self.recipe_id, actor.inventory, current_floor
        )
        if not can_craft:
            self._log_validation_failure("cannot craft recipe",
                                        recipe_id=self.recipe_id, reason=reason)
            return False

        self._log_validation_success("validated successfully",
                                    actor_name=actor.name, forge_name=forge.name,
                                    recipe_id=self.recipe_id)
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute crafting."""
        if not self.validate(context):
            logger.error("CraftAction execution failed validation",
                        extra={'actor_id': self.actor_id, 'forge_id': self.forge_id,
                               'recipe_id': self.recipe_id})
            return ActionOutcome.failure("Cannot craft")

        actor = self._get_actor(context)
        forge = context.get_entity(self.forge_id)

        logger.info("CraftAction started",
                   extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                          'forge_id': self.forge_id, 'forge_name': forge.name,
                          'recipe_id': self.recipe_id})

        # Create equipment from recipe
        equipment = self._create_equipment(actor)
        if not equipment:
            return ActionOutcome.failure("Crafting failed")

        # Add to inventory or drop on ground
        success_msg = self._add_equipment_to_actor(context, actor, equipment)

        return self._create_craft_outcome(equipment, success_msg)

    def _create_equipment(self, actor):
        """Create equipment from recipe using actor's ore."""
        recipe_manager = self.get_recipe_manager()
        recipe = recipe_manager.get_recipe(self.recipe_id)

        ore_items = self._find_and_remove_ore(actor, recipe)
        if not ore_items:
            logger.error("Failed to find required ore in inventory")
            return None

        equipment = recipe_manager.create_equipment(self.recipe_id, ore_items)
        if not equipment:
            logger.error(f"Failed to create equipment from recipe {self.recipe_id}")
            return None

        return equipment

    def _add_equipment_to_actor(self, context, actor, equipment):
        """Add equipment to actor's inventory or drop on ground if full."""
        from ..entities import Player

        if not isinstance(actor, Player):
            return f"Crafted {equipment.name}!"

        if actor.add_to_inventory(equipment):
            logger.info("CraftAction completed successfully",
                       extra={'actor_id': self.actor_id, 'equipment_id': equipment.entity_id,
                              'equipment_name': equipment.name})
            return f"Crafted {equipment.name}!"

        # Inventory full - drop on ground
        equipment.x = actor.x
        equipment.y = actor.y
        context.add_entity(equipment)
        logger.warning("Inventory full after crafting, equipment dropped",
                      extra={'equipment_id': equipment.entity_id})
        return f"Crafted {equipment.name}! (Inventory full, dropped on ground)"

    def _create_craft_outcome(self, equipment, success_msg):
        """Create success outcome with messages and events."""
        outcome = ActionOutcome.success(took_turn=True)
        outcome.messages.append(success_msg)

        # Add equipment stats message
        attack_bonus = equipment.get_stat('attack_bonus', 0)
        defense_bonus = equipment.get_stat('defense_bonus', 0)
        outcome.messages.append(f"  Attack: +{attack_bonus}, Defense: +{defense_bonus}")

        # Publish crafting event
        outcome.events.append({
            'type': 'equipment_crafted',
            'actor_id': self.actor_id,
            'forge_id': self.forge_id,
            'recipe_id': self.recipe_id,
            'equipment_id': equipment.entity_id,
        })

        return outcome

    def _get_actor(self, context: GameContext):
        """Get the actor performing the crafting action."""
        actor = context.get_entity(self.actor_id)
        return actor if actor else context.get_player()

    def _find_and_remove_ore(self, actor, recipe) -> list:
        """
        Find and remove required ore from actor's inventory.

        Args:
            actor: Player entity
            recipe: CraftingRecipe

        Returns:
            List of ore items removed from inventory
        """
        required_type = recipe.get_required_ore_type()
        required_count = recipe.get_required_ore_count()

        # Find ore of the required type
        ore_items = []
        for item in actor.inventory[:]:  # Copy to avoid modification during iteration
            if item.get_stat('ore_type') == required_type:
                ore_items.append(item)
                if len(ore_items) >= required_count:
                    break

        # Remove ore from inventory
        for ore_item in ore_items:
            actor.remove_from_inventory(ore_item)

        logger.debug(
            f"Removed {len(ore_items)} {required_type} ore from inventory",
            extra={
                'actor_id': self.actor_id,
                'ore_type': required_type,
                'ore_count': len(ore_items),
            }
        )

        return ore_items

    def to_dict(self) -> dict:
        return {
            'action_type': 'CraftAction',
            'actor_id': self.actor_id,
            'forge_id': self.forge_id,
            'recipe_id': self.recipe_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CraftAction':
        return cls(
            actor_id=data['actor_id'],
            forge_id=data['forge_id'],
            recipe_id=data['recipe_id'],
        )
