"""
Action Factory - centralized action creation following Factory Pattern.

Responsibilities:
- Create actions from string types
- Handle action-specific prerequisites
- Validate action requirements
- Extensible via handler registration

Design Pattern: Factory Pattern (Gang of Four)
SOLID: Open/Closed Principle (add actions without modifying)
"""

import logging
from typing import Optional, Dict, Callable
from dataclasses import dataclass

from ..base.action import Action
from ..base.game_context import GameContext
from ..base.entity import EntityType
from .move_action import MoveAction
from .survey_action import SurveyAction
from .mine_action import MineAction
from .descend_action import DescendAction
from .attack_action import AttackAction
from .craft_action import CraftAction
from .equip_action import EquipAction
from .unequip_action import UnequipAction
from .pickup_action import PickupAction
from .ability_action import AbilityAction
from .use_item_action import UseItemAction
from .drop_action import DropAction
from ..extensions import abilities

logger = logging.getLogger(__name__)


@dataclass
class ActionHandler:
    """
    Handler for creating a specific action type.

    Encapsulates creation logic and prerequisites.
    """
    name: str
    create_fn: Callable[[GameContext, dict], Optional[Action]]
    description: str


class ActionFactory:
    """
    Factory for creating game actions from string identifiers.

    Benefits:
    - Reduces Game class complexity (from 19 → 8)
    - Open/Closed Principle (extend without modifying)
    - Testable action creation
    - Clear separation of concerns

    Usage:
        factory = ActionFactory(context)
        action = factory.create('move', dx=1, dy=0)
        if action:
            outcome = action.execute(context)
    """

    def __init__(self, context: GameContext):
        """
        Initialize factory with game context.

        Args:
            context: Game context for action creation and validation
        """
        self.context = context
        self._handlers: Dict[str, ActionHandler] = {}

        # Register standard game actions
        self._register_standard_actions()

        logger.debug("ActionFactory initialized with standard actions")

    def create(self, action_type: str, actor_id: Optional[str] = None, **kwargs) -> Optional[Action]:
        """
        Create an action from string type.

        Args:
            action_type: Type of action ('move', 'mine', 'survey', etc.)
            actor_id: Entity performing the action. Defaults to the player
                (single-player); the multiplayer server passes the seat's entity.
            **kwargs: Action-specific parameters

        Returns:
            Action instance or None if creation failed
        """
        handler = self._handlers.get(action_type)

        if not handler:
            logger.warning(f"Unknown action type: {action_type}")
            self.context.game_state.add_message(f"Unknown action: {action_type}")
            return None

        actor = self.context.get_entity(actor_id) if actor_id is not None else self.context.get_player()
        if actor is None or not actor.is_alive:
            logger.warning(f"Cannot create {action_type}: unknown or dead actor {actor_id!r}")
            return None
        kwargs['actor_id'] = actor.entity_id

        try:
            action = handler.create_fn(self.context, kwargs)

            if action:
                logger.debug(
                    f"Created action: {action_type}",
                    extra={'action_class': action.__class__.__name__}
                )

            return action

        except Exception as e:
            logger.error(
                f"Failed to create action: {action_type}",
                extra={'error': str(e), 'kwargs': kwargs},
                exc_info=True
            )
            self.context.game_state.add_message(f"Error creating {action_type} action")
            return None

    def register_handler(self, action_type: str, handler: ActionHandler) -> None:
        """
        Register a custom action handler.

        Allows extending the factory without modifying this file.
        Follows Open/Closed Principle.

        Args:
            action_type: String identifier for action
            handler: ActionHandler instance
        """
        self._handlers[action_type] = handler
        logger.info(f"Registered custom action handler: {action_type}")

    def get_available_actions(self) -> Dict[str, str]:
        """
        Get all available action types and descriptions.

        Returns:
            Dict of action_type -> description
        """
        return {
            action_type: handler.description
            for action_type, handler in self._handlers.items()
        }

    # ============================================================================
    # Standard Action Registration
    # ============================================================================

    def _register_standard_actions(self) -> None:
        """Register the standard game actions."""

        self._handlers['move'] = ActionHandler(
            name='move',
            create_fn=self._create_move_action,
            description='Move in a direction'
        )

        self._handlers['survey'] = ActionHandler(
            name='survey',
            create_fn=self._create_survey_action,
            description='Survey adjacent ore vein properties'
        )

        self._handlers['mine'] = ActionHandler(
            name='mine',
            create_fn=self._create_mine_action,
            description='Mine adjacent ore vein (multi-turn)'
        )

        self._handlers['descend'] = ActionHandler(
            name='descend',
            create_fn=self._create_descend_action,
            description='Descend stairs to next floor'
        )

        self._handlers['attack'] = ActionHandler(
            name='attack',
            create_fn=self._create_attack_action,
            description='Attack an adjacent enemy'
        )

        self._handlers['craft'] = ActionHandler(
            name='craft',
            create_fn=self._create_craft_action,
            description='Craft equipment at a forge'
        )

        self._handlers['equip'] = ActionHandler(
            name='equip',
            create_fn=self._create_equip_action,
            description='Equip an item from inventory'
        )

        self._handlers['unequip'] = ActionHandler(
            name='unequip',
            create_fn=self._create_unequip_action,
            description="Take off the worn weapon or armor ('slot')"
        )

        self._handlers['ability'] = ActionHandler(
            name='ability',
            create_fn=self._create_ability_action,
            description='Use a class ability (force bolt, heal)'
        )

        self._handlers['pickup'] = ActionHandler(
            name='pickup',
            create_fn=self._create_pickup_action,
            description='Pick up items from the ground'
        )

        self._handlers['use'] = ActionHandler(
            name='use',
            create_fn=self._create_use_action,
            description='Drink, eat or read an item from inventory'
        )

        self._handlers['drop'] = ActionHandler(
            name='drop',
            create_fn=self._create_drop_action,
            description='Drop an item from inventory onto the floor'
        )

    # ============================================================================
    # Action Creation Handlers
    # ============================================================================

    def _create_move_action(
        self,
        context: GameContext,
        kwargs: dict
    ) -> Optional[Action]:
        """
        Create a move action.

        Args:
            context: Game context
            kwargs: Must contain 'dx' and 'dy'

        Returns:
            MoveAction or None
        """
        actor_id = self._actor(context, kwargs).entity_id
        dx = kwargs.get('dx', 0)
        dy = kwargs.get('dy', 0)

        return MoveAction(actor_id, dx, dy)

    def _create_survey_action(
        self,
        context: GameContext,
        kwargs: dict
    ) -> Optional[Action]:
        """
        Create a survey action.

        Requires adjacent ore vein. With several adjacent, surveys one that has
        not been surveyed yet (otherwise pressing survey again would hit the
        same vein forever and the others could never be surveyed).

        Args:
            context: Game context
            kwargs: Optional 'ore_vein_id' to survey a specific adjacent vein

        Returns:
            SurveyAction or None if no adjacent ore vein
        """
        actor = self._actor(context, kwargs)
        actor_id = actor.entity_id

        # Find adjacent ore vein
        ore_vein = self._find_adjacent_ore_vein(
            context,
            actor,
            ore_vein_id=kwargs.get('ore_vein_id'),
            prefer=lambda vein: not vein.get_stat('surveyed'),
        )

        if not ore_vein:
            logger.debug(
                "Survey action failed: no adjacent ore vein",
                extra={'player_pos': (actor.x, actor.y)}
            )
            context.game_state.add_message("No ore vein nearby to survey")
            return None

        return SurveyAction(actor_id, ore_vein.entity_id)

    def _create_mine_action(
        self,
        context: GameContext,
        kwargs: dict
    ) -> Optional[Action]:
        """
        Create a mine action.

        Requires adjacent ore vein. Handles resuming multi-turn mining.

        Args:
            context: Game context
            kwargs: Optional 'ore_vein_id' to mine a specific adjacent vein

        Returns:
            MineAction or None if no adjacent ore vein
        """
        player = self._actor(context, kwargs)
        actor_id = player.entity_id

        # Resume an in-progress mining action -- but only while the player is still
        # next to that vein. If they walked away, or the vein is gone, the saved
        # state is stale: resuming it fails validation every time, no turn passes,
        # and mining is wedged for the rest of the run (found by the fuzz bots).
        mining_data = player.get_stat('mining_action')
        if mining_data:
            vein = context.get_entity(mining_data.get('ore_vein_id'))
            if vein is not None and vein.entity_type == EntityType.ORE_VEIN \
                    and player.is_adjacent(vein):
                logger.debug("Resuming multi-turn mining action")
                return MineAction.from_dict(mining_data)
            logger.debug("Dropping stale mining state (player moved away or vein gone)")
            player.set_stat('mining_action', None)

        # Find adjacent ore vein
        ore_vein = self._find_adjacent_ore_vein(context, player, ore_vein_id=kwargs.get('ore_vein_id'))

        if not ore_vein:
            logger.debug(
                "Mine action failed: no adjacent ore vein",
                extra={'player_pos': (player.x, player.y)}
            )
            context.game_state.add_message("No ore vein nearby to mine")
            return None

        return MineAction(actor_id, ore_vein.entity_id)

    def _create_descend_action(
        self,
        context: GameContext,
        kwargs: dict
    ) -> Optional[Action]:
        """
        Create a descend action.

        Args:
            context: Game context
            kwargs: Not used

        Returns:
            DescendAction
        """
        actor_id = self._actor(context, kwargs).entity_id
        return DescendAction(actor_id)

    def _create_attack_action(
        self,
        context: GameContext,
        kwargs: dict
    ) -> Optional[Action]:
        """
        Create an attack action.

        Args:
            context: Game context
            kwargs: Must contain 'target_id'

        Returns:
            AttackAction or None
        """
        actor_id = self._actor(context, kwargs).entity_id
        target_id = kwargs.get('target_id')

        if not target_id:
            logger.debug("Attack action failed: no target_id provided")
            context.game_state.add_message("No target to attack")
            return None

        return AttackAction(actor_id, target_id)

    def _create_ability_action(
        self,
        context: GameContext,
        kwargs: dict
    ) -> Optional[Action]:
        """
        Create an ability action.

        Args:
            context: Game context
            kwargs: Optional 'ability' (default: the player's first active
                class ability)

        Returns:
            AbilityAction or None if the player has no active ability
        """
        player = self._actor(context, kwargs)
        ability = kwargs.get('ability')
        if not ability:
            known = [a for a in player.get_stat('abilities', []) if a in abilities]
            if not known:
                context.game_state.add_message(f"{player.name} has no ability to use.")
                return None
            ability = known[0]
        return AbilityAction(player.entity_id, ability)

    def _create_craft_action(
        self,
        context: GameContext,
        kwargs: dict
    ) -> Optional[Action]:
        """
        Create a craft action.

        Args:
            context: Game context
            kwargs: Must contain 'forge_id' and 'recipe_id'

        Returns:
            CraftAction or None
        """
        actor_id = self._actor(context, kwargs).entity_id
        forge_id = kwargs.get('forge_id')
        recipe_id = kwargs.get('recipe_id')

        if not forge_id or not recipe_id:
            logger.debug("Craft action failed: missing forge_id or recipe_id")
            context.game_state.add_message("Cannot craft: missing forge or recipe")
            return None

        return CraftAction(actor_id, forge_id, recipe_id)

    def _create_equip_action(
        self,
        context: GameContext,
        kwargs: dict
    ) -> Optional[Action]:
        """
        Create an equip action.

        Args:
            context: Game context
            kwargs: Must contain 'item_id'

        Returns:
            EquipAction or None
        """
        actor_id = self._actor(context, kwargs).entity_id
        item_id = kwargs.get('item_id')

        if not item_id:
            logger.debug("Equip action failed: no item_id provided")
            context.game_state.add_message("No item to equip")
            return None

        return EquipAction(actor_id, item_id)

    def _create_unequip_action(self, context: GameContext, kwargs: dict) -> Optional[Action]:
        """Create an unequip action. kwargs must contain 'slot' ('weapon' or 'armor')."""
        slot = kwargs.get('slot')
        if not slot:
            context.game_state.add_message("Nothing to remove")
            return None
        return UnequipAction(self._actor(context, kwargs).entity_id, slot)

    def _create_use_action(self, context: GameContext, kwargs: dict) -> Optional[Action]:
        """Create a use-item action. kwargs must contain 'item_id'."""
        item_id = kwargs.get('item_id')
        if not item_id:
            context.game_state.add_message("Nothing to use")
            return None
        return UseItemAction(self._actor(context, kwargs).entity_id, item_id)

    def _create_drop_action(self, context: GameContext, kwargs: dict) -> Optional[Action]:
        """Create a drop action. kwargs must contain 'item_id'."""
        item_id = kwargs.get('item_id')
        if not item_id:
            context.game_state.add_message("Nothing to drop")
            return None
        return DropAction(self._actor(context, kwargs).entity_id, item_id)

    def _create_pickup_action(
        self,
        context: GameContext,
        kwargs: dict
    ) -> Optional[Action]:
        """
        Create a pickup action.

        Args:
            context: Game context
            kwargs: Not used

        Returns:
            PickupAction
        """
        actor_id = self._actor(context, kwargs).entity_id
        return PickupAction(actor_id)

    # ============================================================================
    # Helper Methods
    # ============================================================================

    @staticmethod
    def _actor(context: GameContext, kwargs: dict):
        """The acting entity: kwargs['actor_id'] (set by create), else the player."""
        actor_id = kwargs.get('actor_id')
        actor = context.get_entity(actor_id) if actor_id is not None else None
        return actor if actor is not None else context.get_player()

    def _find_adjacent_ore_vein(self, context: GameContext, actor, ore_vein_id=None, prefer=None):
        """
        Find ore vein adjacent to the actor.

        Helper method for survey and mine actions.

        Args:
            context: Game context
            actor: Entity looking for a vein
            ore_vein_id: If given and that vein is adjacent, return exactly it
            prefer: Optional predicate; the first adjacent vein satisfying it wins,
                falling back to the first adjacent vein

        Returns:
            OreVein entity or None
        """
        player = actor
        adjacent = [
            ore_vein for ore_vein in context.get_entities_by_type(EntityType.ORE_VEIN)
            if player.is_adjacent(ore_vein)
        ]

        if ore_vein_id is not None:
            for ore_vein in adjacent:
                if ore_vein.entity_id == ore_vein_id:
                    return ore_vein

        if prefer is not None:
            for ore_vein in adjacent:
                if prefer(ore_vein):
                    return ore_vein

        return adjacent[0] if adjacent else None
