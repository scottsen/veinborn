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

    def create(self, action_type: str, **kwargs) -> Optional[Action]:
        """
        Create an action from string type.

        Args:
            action_type: Type of action ('move', 'mine', 'survey', etc.)
            **kwargs: Action-specific parameters

        Returns:
            Action instance or None if creation failed
        """
        handler = self._handlers.get(action_type)

        if not handler:
            logger.warning(f"Unknown action type: {action_type}")
            self.context.game_state.add_message(f"Unknown action: {action_type}")
            return None

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
        actor_id = context.get_player().entity_id
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

        Requires adjacent ore vein.

        Args:
            context: Game context
            kwargs: Not used

        Returns:
            SurveyAction or None if no adjacent ore vein
        """
        actor_id = context.get_player().entity_id

        # Find adjacent ore vein
        ore_vein = self._find_adjacent_ore_vein(context)

        if not ore_vein:
            logger.debug(
                "Survey action failed: no adjacent ore vein",
                extra={'player_pos': (context.get_player().x, context.get_player().y)}
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
            kwargs: Not used

        Returns:
            MineAction or None if no adjacent ore vein
        """
        actor_id = context.get_player().entity_id
        player = context.get_player()

        # Check if resuming existing mining action
        mining_data = player.get_stat('mining_action')
        if mining_data:
            logger.debug("Resuming multi-turn mining action")
            return MineAction.from_dict(mining_data)

        # Find adjacent ore vein
        ore_vein = self._find_adjacent_ore_vein(context)

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
        actor_id = context.get_player().entity_id
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
        actor_id = context.get_player().entity_id
        target_id = kwargs.get('target_id')

        if not target_id:
            logger.debug("Attack action failed: no target_id provided")
            context.game_state.add_message("No target to attack")
            return None

        return AttackAction(actor_id, target_id)

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
        actor_id = context.get_player().entity_id
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
        actor_id = context.get_player().entity_id
        item_id = kwargs.get('item_id')

        if not item_id:
            logger.debug("Equip action failed: no item_id provided")
            context.game_state.add_message("No item to equip")
            return None

        return EquipAction(actor_id, item_id)

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _find_adjacent_ore_vein(self, context: GameContext):
        """
        Find ore vein adjacent to player.

        Helper method for survey and mine actions.

        Args:
            context: Game context

        Returns:
            OreVein entity or None
        """
        player = context.get_player()
        ore_veins = context.get_entities_by_type(EntityType.ORE_VEIN)

        for ore_vein in ore_veins:
            if player.is_adjacent(ore_vein):
                return ore_vein

        return None
