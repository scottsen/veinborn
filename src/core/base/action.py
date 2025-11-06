"""
Action base class - serializable player/monster actions.

Critical for:
- Multiplayer (actions serialize to NATS messages)
- Testing (create actions directly, verify outcomes)
- Replay (save action history)
- Lua integration (scripts return Action objects)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union, Set
from enum import Enum
import logging

if TYPE_CHECKING:
    from .game_context import GameContext
    from .entity import Entity

logger = logging.getLogger(__name__)


class ActionResult(Enum):
    """Result of action execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    INVALID = "invalid"
    BLOCKED = "blocked"


@dataclass
class ActionOutcome:
    """
    Result of an action execution.

    This is an "event-ready" pattern - the outcome contains event data
    that can be published to an EventBus in Phase 2, with zero refactoring.
    """
    result: ActionResult
    took_turn: bool  # Did this consume a game turn?
    messages: list[str]  # Messages to display
    events: list[dict]  # Events to publish (Phase 2)

    @property
    def is_success(self) -> bool:
        """Check if action succeeded."""
        return self.result == ActionResult.SUCCESS

    @staticmethod
    def success(took_turn: bool = True, message: str = "") -> 'ActionOutcome':
        """Create success outcome."""
        return ActionOutcome(
            result=ActionResult.SUCCESS,
            took_turn=took_turn,
            messages=[message] if message else [],
            events=[],
        )

    @staticmethod
    def failure(message: str = "") -> 'ActionOutcome':
        """Create failure outcome."""
        return ActionOutcome(
            result=ActionResult.FAILURE,
            took_turn=False,
            messages=[message] if message else [],
            events=[],
        )


class Action(ABC):
    """
    Base class for all game actions.

    Actions are serializable, testable, and replayable.

    Design principles:
    - Small, focused classes (one action type per class)
    - Separate validate() from execute() (server can validate client actions)
    - Return structured outcomes (event-ready pattern)
    """

    def __init__(self, actor_id: str):
        """
        Args:
            actor_id: Entity ID of the actor performing this action
        """
        self.actor_id = actor_id

    @abstractmethod
    def validate(self, context: 'GameContext') -> bool:
        """
        Check if action is valid before execution.

        Returns:
            True if action can be executed, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, context: 'GameContext') -> ActionOutcome:
        """
        Execute the action.

        Returns:
            ActionOutcome describing what happened
        """
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Serialize action (for multiplayer, save/replay)."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> 'Action':
        """Deserialize action."""
        pass

    def get_action_type(self) -> str:
        """Return action type for serialization."""
        return self.__class__.__name__

    # ========================================================================
    # Validation Helper Methods
    # ========================================================================
    # These methods reduce duplicate validation code across all Action subclasses.
    # Instead of repeating the same actor lookup/validation logic in every action,
    # subclasses can call these helpers for consistent, DRY validation.

    def _get_actor(self, context: 'GameContext') -> Optional['Entity']:
        """
        Get actor entity (simple lookup, no validation).

        This helper eliminates the common boilerplate pattern:
            actor = context.get_entity(self.actor_id)
            if not actor:
                actor = context.get_player()

        Use this when you need the actor but will do custom validation.
        For standard validation (is_alive check), use _get_and_validate_actor().

        Returns:
            Entity if found, None otherwise
        """
        actor = context.get_entity(self.actor_id)
        if not actor:
            actor = context.get_player()
        return actor

    def _get_and_validate_actor(self, context: 'GameContext') -> Optional['Entity']:
        """
        Get actor entity and perform basic validation.

        This helper eliminates the common boilerplate pattern:
            actor = context.get_entity(self.actor_id) or context.get_player()
            if not actor:
                logger.warning(...)
                return False
            if not actor.is_alive:
                logger.warning(...)
                return False

        Returns:
            Entity if valid, None if validation fails
        """
        # Try to get from entities dict first, then fall back to player
        actor = context.get_entity(self.actor_id)
        if not actor:
            actor = context.get_player()

        if not actor:
            self._log_validation_failure("actor not found")
            return None

        if not actor.is_alive:
            self._log_validation_failure("actor is dead", actor_name=actor.name)
            return None

        return actor

    def _log_validation_failure(self, reason: str, **extra_data):
        """
        Log validation failure with consistent format.

        Args:
            reason: Human-readable reason for failure
            **extra_data: Additional context to log (actor_name, position, etc.)
        """
        action_type = self.get_action_type()
        logger.warning(
            f"{action_type} validation failed: {reason}",
            extra={'actor_id': self.actor_id, **extra_data}
        )

    def _log_validation_success(self, message: str = "validation successful", **extra_data):
        """
        Log validation success with consistent format.

        Args:
            message: Success message
            **extra_data: Additional context to log
        """
        action_type = self.get_action_type()
        logger.debug(
            f"{action_type} {message}",
            extra={'actor_id': self.actor_id, **extra_data}
        )

    def _validate_entity(
        self,
        context: 'GameContext',
        entity_id: str,
        expected_type: 'Union[EntityType, Set[EntityType]]',
        entity_name: str = "entity",
        require_adjacency: bool = False,
        require_alive: bool = False
    ) -> Optional['Entity']:
        """
        Validate entity exists, has correct type, and meets requirements.

        This helper eliminates the common 10-15 line pattern:
            entity = context.get_entity(self.entity_id)
            if not entity:
                self._log_validation_failure("entity not found")
                return False
            if entity.entity_type != expected_type:
                self._log_validation_failure("wrong type")
                return False
            if not actor.is_adjacent(entity):
                self._log_validation_failure("not adjacent")
                return False

        Args:
            context: Game context
            entity_id: Entity ID to validate
            expected_type: Expected EntityType or set of EntityTypes
            entity_name: Name for logging (e.g., "forge", "ore_vein", "target")
            require_adjacency: If True, check actor is adjacent
            require_alive: If True, check entity is alive

        Returns:
            Entity if valid, None if validation failed (already logged)
        """
        # Import here to avoid circular import
        from .entity import EntityType

        entity = context.get_entity(entity_id)

        if not entity:
            # Log at DEBUG level for entity not found - this is common when
            # entities die/despawn and is not an error condition
            action_type = self.get_action_type()
            logger.debug(
                f"{action_type} validation failed: {entity_name} not found",
                extra={'actor_id': self.actor_id, f"{entity_name}_id": entity_id}
            )
            return None

        # Support both single type and set of types
        expected_types = expected_type if isinstance(expected_type, set) else {expected_type}
        if entity.entity_type not in expected_types:
            type_names = ", ".join(t.name for t in expected_types)
            self._log_validation_failure(
                f"target is not a valid {entity_name} (expected: {type_names})",
                **{f"{entity_name}_id": entity_id, "actual_type": entity.entity_type.name}
            )
            return None

        if require_alive and not entity.is_alive:
            # Log at DEBUG level for dead entities - this is common during combat
            action_type = self.get_action_type()
            logger.debug(
                f"{action_type} validation failed: {entity_name} is dead",
                extra={'actor_id': self.actor_id, f"{entity_name}_name": entity.name}
            )
            return None

        if require_adjacency:
            actor = self._get_actor(context)
            if actor and not actor.is_adjacent(entity):
                self._log_validation_failure(
                    f"not adjacent to {entity_name}",
                    actor_name=actor.name,
                    actor_pos=(actor.x, actor.y),
                    **{f"{entity_name}_name": entity.name,
                       f"{entity_name}_pos": (entity.x, entity.y)}
                )
                return None

        return entity
