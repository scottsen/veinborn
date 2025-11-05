"""
Base classes for Brogue game architecture.

This module provides foundational classes that enable:
- Clean entity system with uniform API
- Serializable actions for testing and future multiplayer
- Modular systems for game logic
- Safe game context for controlled state access
"""

from .entity import Entity, EntityType
from .action import Action, ActionResult, ActionOutcome
from .system import System
from .game_context import GameContext

__all__ = [
    'Entity',
    'EntityType',
    'Action',
    'ActionResult',
    'ActionOutcome',
    'System',
    'GameContext',
]
