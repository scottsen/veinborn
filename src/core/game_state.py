"""
GameState - holds all game state in one place.

This class:
- Centralizes all mutable game state
- Makes save/load easier
- Provides clean separation for GameContext
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging

from .entities import Player
from .base.entity import Entity
from .world import Map

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """
    Central game state container.

    Design principles:
    - All mutable state in one place
    - Easy to serialize for save/load
    - Clear ownership of entities
    """

    # Primary entities
    player: Player
    entities: Dict[str, Entity] = field(default_factory=dict)

    # World
    dungeon_map: Map = field(default_factory=lambda: Map(80, 24))

    # Game progress
    turn_count: int = 0
    current_floor: int = 1

    # Randomness (for reproducibility)
    seed: Optional[Union[int, str]] = None
    rng_state: Optional[tuple] = None

    # Message log
    messages: List[str] = field(default_factory=list)

    # Game state
    game_over: bool = False
    victory: bool = False

    # Player identity (Phase 5: for high scores)
    player_name: str = "Anonymous"

    def add_message(self, message: str) -> None:
        """Add message to log (max 100 messages)."""
        self.messages.append(message)
        if len(self.messages) > 100:
            self.messages.pop(0)
        logger.info(f"Game message: {message}")

    def get_recent_messages(self, count: int = 10) -> List[str]:
        """Get most recent messages."""
        return self.messages[-count:]

    def cleanup_dead_entities(self) -> None:
        """Remove dead entities from the game."""
        dead_ids = [
            entity_id
            for entity_id, entity in self.entities.items()
            if not entity.is_alive
        ]

        for entity_id in dead_ids:
            entity = self.entities[entity_id]
            logger.debug(f"Removing dead entity: {entity.name} ({entity_id})")
            del self.entities[entity_id]
