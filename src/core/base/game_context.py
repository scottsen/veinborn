"""
GameContext - safe, controlled access to game state.

Provides controlled API surface:
- Systems use this instead of accessing GameState directly
- Easy to mock for testing
- Future Lua scripts get this as their API
- Can add permission checks (multiplayer)
"""

from typing import Optional, List, Dict, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .entity import Entity, EntityType
    from .system import System
    from ..game_state import GameState

logger = logging.getLogger(__name__)


class GameContext:
    """
    Facade for game state access.

    Design principles:
    - Controlled API (no direct state manipulation)
    - Safe for untrusted code (future Lua scripts)
    - Easy to test (mock this for unit tests)
    """

    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state
        self.systems: Dict[str, 'System'] = {}

    # Entity queries
    def get_entity(self, entity_id: str) -> Optional['Entity']:
        """Get entity by ID."""
        return self.game_state.entities.get(entity_id)

    def get_player(self) -> 'Entity':
        """Get the player entity."""
        return self.game_state.player

    def get_entities_by_type(self, entity_type: 'EntityType') -> List['Entity']:
        """Get all entities of a type."""
        from .entity import EntityType
        return [e for e in self.game_state.entities.values()
                if e.entity_type == entity_type]

    def get_entity_at(self, x: int, y: int) -> Optional['Entity']:
        """
        Get entity at position.

        Prioritizes combat entities (MONSTER, PLAYER) over items to prevent
        bots from trying to attack loot drops.
        """
        from .entity import EntityType

        # Collect all entities at this position
        entities_here = [
            entity for entity in self.game_state.entities.values()
            if entity.x == x and entity.y == y and entity.is_alive
        ]

        if not entities_here:
            return None

        # Prioritize combat entities (monsters, players) over items/ore/etc
        combat_types = {EntityType.MONSTER, EntityType.PLAYER}
        for entity in entities_here:
            if entity.entity_type in combat_types:
                return entity

        # No combat entities - return first non-combat entity (item, ore, forge, etc.)
        return entities_here[0]

    def get_entities_in_range(self, x: int, y: int, radius: int) -> List['Entity']:
        """Get entities within radius of position."""
        entities = []
        radius_sq = radius * radius

        for entity in self.game_state.entities.values():
            if entity.x is None:
                continue

            dx = entity.x - x
            dy = entity.y - y
            dist_sq = dx * dx + dy * dy

            if dist_sq <= radius_sq:
                entities.append(entity)

        return entities

    def get_entities_at(
        self,
        x: int,
        y: int,
        entity_type: Optional['EntityType'] = None,
        alive_only: bool = False
    ) -> List['Entity']:
        """
        Get all entities at position, optionally filtered.

        This is a more flexible version of get_entity_at() that returns all matches
        instead of just the first prioritized one.

        Args:
            x: X coordinate
            y: Y coordinate
            entity_type: If provided, filter to only this type
            alive_only: If True, only return alive entities

        Returns:
            List of matching entities (may be empty)
        """
        matches = [
            entity for entity in self.game_state.entities.values()
            if entity.x == x and entity.y == y
        ]

        if entity_type:
            matches = [e for e in matches if e.entity_type == entity_type]

        if alive_only:
            matches = [e for e in matches if e.is_alive]

        return matches

    def get_first_entity_at(
        self,
        x: int,
        y: int,
        entity_type: Optional['EntityType'] = None,
        alive_only: bool = False
    ) -> Optional['Entity']:
        """
        Get first entity at position matching criteria.

        Convenience method that wraps get_entities_at() and returns first match.

        Args:
            x: X coordinate
            y: Y coordinate
            entity_type: If provided, filter to only this type
            alive_only: If True, only return alive entities

        Returns:
            First matching entity, or None if no matches
        """
        results = self.get_entities_at(x, y, entity_type, alive_only)
        return results[0] if results else None

    # Entity manipulation
    def add_entity(self, entity: 'Entity') -> None:
        """Add entity to game."""
        self.game_state.entities[entity.entity_id] = entity
        logger.debug(f"Entity added: {entity.name} ({entity.entity_id})")

    def remove_entity(self, entity_id: str) -> None:
        """Remove entity from game."""
        if entity_id in self.game_state.entities:
            entity = self.game_state.entities[entity_id]
            del self.game_state.entities[entity_id]
            logger.debug(f"Entity removed: {entity.name} ({entity_id})")

    # Map queries
    def get_map(self):
        """Get the dungeon map."""
        return self.game_state.dungeon_map

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if position is walkable."""
        return self.game_state.dungeon_map.is_walkable(x, y)

    def in_bounds(self, x: int, y: int) -> bool:
        """Check if position is in map bounds."""
        return self.game_state.dungeon_map.in_bounds(x, y)

    # System access
    def get_system(self, name: str) -> Optional['System']:
        """Get a system by name."""
        return self.systems.get(name)

    def register_system(self, name: str, system: 'System') -> None:
        """Register a system."""
        self.systems[name] = system
        logger.info(f"System registered: {name}")

    # Message log
    def add_message(self, message: str) -> None:
        """Add message to game log."""
        self.game_state.messages.append(message)
        logger.info(f"Game message: {message}")

    # Game state
    def get_turn_count(self) -> int:
        """Get current turn number."""
        return self.game_state.turn_count

    def get_floor(self) -> int:
        """Get current floor number."""
        return self.game_state.current_floor
