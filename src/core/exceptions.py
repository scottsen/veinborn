"""
Veinborn exception hierarchy.

This module defines all custom exceptions used throughout the Veinborn codebase,
following a structured hierarchy for better error handling and logging.

See Also:
    docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md - Error Handling Standards
"""

from typing import Any, Dict


class VeinbornError(Exception):
    """Base exception for all Veinborn errors with structured data support.

    All Veinborn exceptions inherit from this base class and support
    structured context data for better logging and debugging.

    Args:
        message: Human-readable error message
        **context: Additional context data (e.g., entity_id, position, etc.)

    Example:
        >>> raise InvalidActionError(
        ...     "Cannot move to occupied position",
        ...     position=(5, 10),
        ...     entity_id="player_1"
        ... )
    """

    def __init__(self, message: str, **context: Any) -> None:
        """Initialize exception with message and context.

        Args:
            message: Human-readable error message
            **context: Additional context data for debugging
        """
        super().__init__(message)
        self.message = message
        self.context = context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to structured format for logging.

        Returns:
            Dictionary with error_type, message, and all context data

        Example:
            >>> error = InvalidActionError("Cannot move", position=(5, 10))
            >>> error.to_dict()
            {'error_type': 'InvalidActionError', 'message': 'Cannot move', 'position': (5, 10)}
        """
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            **self.context,
        }


# =============================================================================
# Game Logic Errors (Recoverable)
# =============================================================================


class GameError(VeinbornError):
    """Error in game logic (usually recoverable).

    These errors represent invalid game states or actions that can typically
    be handled gracefully (e.g., invalid move attempts, rule violations).
    """
    pass


class InvalidActionError(GameError):
    """Action cannot be performed in current game state.

    Raised when a player or AI attempts an invalid action (e.g., moving to
    an occupied position, attacking out of range, using unavailable ability).

    Example:
        >>> raise InvalidActionError(
        ...     "Cannot move to occupied position",
        ...     position=(5, 10),
        ...     entity_id="player_1",
        ...     blocker_id="monster_42"
        ... )
    """
    pass


class InvalidStateError(GameError):
    """Game state is invalid or corrupted.

    Raised when the game reaches an inconsistent state (e.g., entity HP < 0,
    missing required components, invalid floor layout).

    Example:
        >>> raise InvalidStateError(
        ...     "Entity HP cannot be negative",
        ...     entity_id="player_1",
        ...     hp=-5
        ... )
    """
    pass


# =============================================================================
# Data Errors (Loading/Validation)
# =============================================================================


class DataError(VeinbornError):
    """Error loading or validating data.

    These errors occur during data loading, parsing, or validation
    (e.g., invalid YAML, missing content files, schema validation failures).
    """
    pass


class ContentValidationError(DataError):
    """Content file validation failed.

    Raised when content YAML fails to load or validate against schema
    (e.g., missing required fields, type mismatches, invalid references).

    Example:
        >>> raise ContentValidationError(
        ...     "Monster content not found: goblin",
        ...     monster_id="goblin",
        ...     path="/content/monsters/goblin.yaml"
        ... )
    """
    pass


# =============================================================================
# System Errors (Usually Not Recoverable)
# =============================================================================


class VeinbornSystemError(VeinbornError):
    """System-level error (usually not recoverable).

    Note: Named VeinbornSystemError to avoid conflict with Python's built-in
    SystemError. These errors represent system-level failures (I/O errors,
    network failures, resource exhaustion).
    """
    pass


class SaveLoadError(VeinbornSystemError):
    """Failed to save or load game state.

    Raised when save/load operations fail due to I/O errors, permissions,
    corrupted data, or incompatible versions.

    Example:
        >>> raise SaveLoadError(
        ...     "Failed to save game state",
        ...     save_path="/saves/game_001.json",
        ...     original_error="Permission denied"
        ... )
    """
    pass


class NetworkError(VeinbornSystemError):
    """Network communication failed.

    Raised when network operations fail (e.g., multiplayer communication,
    online leaderboard sync, remote content loading).

    Example:
        >>> raise NetworkError(
        ...     "Failed to sync leaderboard",
        ...     endpoint="https://api.veinborn.com/leaderboard",
        ...     status_code=503
        ... )
    """
    pass


# =============================================================================
# Export all exception classes
# =============================================================================

__all__ = [
    'VeinbornError',
    'GameError',
    'InvalidActionError',
    'InvalidStateError',
    'DataError',
    'ContentValidationError',
    'VeinbornSystemError',
    'SaveLoadError',
    'NetworkError',
]
