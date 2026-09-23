"""Action handling and serialization for multiplayer server."""

import logging
from typing import Optional, Dict, Type

from core.base.action import Action
from core.actions import ACTION_TYPES

logger = logging.getLogger(__name__)


class ActionRegistry:
    """Registry of action types for serialization/deserialization."""

    def __init__(self):
        """Initialize action registry with standard actions."""
        self._action_types: Dict[str, Type[Action]] = {}
        self._register_standard_actions()

    def _register_standard_actions(self):
        """Register standard game actions.

        VB-21: sourced from core.actions.ACTION_TYPES, the single canonical
        map, instead of a separately hand-maintained import list -- that
        drift was exactly how PickupAction and WaitAction ended up silently
        unusable in multiplayer.
        """
        for action_type, action_class in ACTION_TYPES.items():
            self.register(action_type, action_class)

    def register(self, action_type: str, action_class: Type[Action]):
        """Register an action type.

        Args:
            action_type: String identifier for the action
            action_class: Action class
        """
        self._action_types[action_type] = action_class
        logger.debug(f"Registered action type: {action_type}")

    def deserialize(self, action_data: Dict) -> Optional[Action]:
        """Deserialize an action from dictionary.

        Args:
            action_data: Serialized action data

        Returns:
            Action instance or None if deserialization failed
        """
        action_type = action_data.get('action_type')
        if not action_type:
            logger.error("Action data missing 'action_type' field")
            return None

        action_class = self._action_types.get(action_type)
        if not action_class:
            logger.error(f"Unknown action type: {action_type}")
            return None

        try:
            action = action_class.from_dict(action_data)
            logger.debug(f"Deserialized action: {action_type}")
            return action
        except Exception as e:
            logger.error(f"Failed to deserialize {action_type}: {e}", exc_info=True)
            return None

    def serialize(self, action: Action) -> Dict:
        """Serialize an action to dictionary.

        Args:
            action: Action to serialize

        Returns:
            Dictionary representation
        """
        try:
            return action.to_dict()
        except Exception as e:
            logger.error(f"Failed to serialize action: {e}", exc_info=True)
            return {}


# Global action registry instance
action_registry = ActionRegistry()
