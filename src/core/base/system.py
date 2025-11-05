"""
System base class - game logic processors.

Systems are modular processors that operate on entities:
- CombatSystem: Handles damage, death
- MovementSystem: Handles movement, collision
- AISystem: Runs monster AI
- MiningSystem: Handles ore mining

Benefits:
- Clean separation of concerns
- Easy to test (mock dependencies)
- Can enable/disable systems
- Clear API for Lua integration
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_context import GameContext


class System(ABC):
    """
    Base class for game systems.

    Design principles:
    - Single responsibility (one system, one concern)
    - Stateless where possible (state lives in entities/context)
    - Clear, focused methods
    """

    def __init__(self, context: 'GameContext'):
        self.context = context
        self.enabled = True

    def initialize(self) -> None:
        """Called when system is first created."""
        pass

    def shutdown(self) -> None:
        """Called when system is destroyed."""
        pass

    @abstractmethod
    def update(self, delta_time: float = 0) -> None:
        """
        Called each game tick (for systems that need ticking).

        Args:
            delta_time: Time since last update (0 for turn-based)
        """
        pass
