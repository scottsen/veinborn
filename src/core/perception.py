"""
Perception System - manages what entities can see and know about the game world.

Provides:
- Visibility/line-of-sight calculations
- Entity perception (what can you see?)
- Fog of war (explored vs visible tiles)
- Clean API for AI/bots (no cheating with raw game state)

Design principles:
- Separation of concerns (what exists vs what you know)
- Information hiding (can't see through walls)
- Fair AI (bots use same perception as players would)
"""

from typing import List, Optional, Tuple, Set
from enum import Enum
from .base.entity import Entity, EntityType
from .entities import Monster, OreVein


class TileVisibility(Enum):
    """Visibility state of a tile for fog of war."""
    UNEXPLORED = 0  # Never seen (black)
    EXPLORED = 1    # Seen before but not currently visible (dimmed/grayed)
    VISIBLE = 2     # Currently visible (normal colors)


class FogOfWar:
    """
    Tracks which tiles have been explored and which are currently visible.

    This creates the classic roguelike fog of war effect where:
    - Unexplored areas are black/hidden
    - Explored but not visible areas are dimmed/grayed out
    - Currently visible areas show normal colors
    """

    def __init__(self, width: int, height: int):
        """
        Initialize fog of war for a map.

        Args:
            width: Map width
            height: Map height
        """
        self.width = width
        self.height = height

        # Track which tiles have ever been explored
        # Initially all False (unexplored)
        self.explored = [[False for _ in range(height)] for _ in range(width)]

        # Track which tiles are currently visible
        # Updated each turn based on player position
        self.visible = [[False for _ in range(height)] for _ in range(width)]

    def get_tile_visibility(self, x: int, y: int) -> TileVisibility:
        """
        Get visibility state of a tile.

        Args:
            x, y: Tile coordinates

        Returns:
            TileVisibility enum value
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return TileVisibility.UNEXPLORED

        if self.visible[x][y]:
            return TileVisibility.VISIBLE
        elif self.explored[x][y]:
            return TileVisibility.EXPLORED
        else:
            return TileVisibility.UNEXPLORED

    def update_visibility(self, observer_x: int, observer_y: int, radius: float, dungeon_map) -> None:
        """
        Update which tiles are currently visible from observer position.

        Uses line-of-sight (Bresenham) to check visibility.
        Marks visible tiles as explored.

        Args:
            observer_x, observer_y: Observer position (usually player)
            radius: Vision radius
            dungeon_map: DungeonMap instance
        """
        # PERFORMANCE FIX: Clear existing array instead of recreating!
        # OLD: self.visible = [[False] * height] * width  ← Allocates 1,920 bools
        # NEW: Reuse existing array (575 updates per game = 1M saved allocations!)
        for x in range(self.width):
            for y in range(self.height):
                self.visible[x][y] = False

        # Observer's position is always visible
        if 0 <= observer_x < self.width and 0 <= observer_y < self.height:
            self.visible[observer_x][observer_y] = True
            self.explored[observer_x][observer_y] = True

        # Check all tiles within vision radius
        min_x = max(0, int(observer_x - radius))
        max_x = min(self.width - 1, int(observer_x + radius))
        min_y = max(0, int(observer_y - radius))
        max_y = min(self.height - 1, int(observer_y + radius))

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                # Skip observer position (already marked)
                if x == observer_x and y == observer_y:
                    continue

                # Check distance
                dx = x - observer_x
                dy = y - observer_y
                distance = (dx * dx + dy * dy) ** 0.5

                if distance > radius:
                    continue

                # Check line of sight
                if self._has_line_of_sight(observer_x, observer_y, x, y, dungeon_map):
                    self.visible[x][y] = True
                    self.explored[x][y] = True

    def _has_line_of_sight(self, x0: int, y0: int, x1: int, y1: int, dungeon_map) -> bool:
        """
        Check if there's unobstructed line of sight between two points.

        Uses Bresenham's line algorithm.

        Args:
            x0, y0: Start position
            x1, y1: End position
            dungeon_map: DungeonMap instance

        Returns:
            True if line of sight is clear
        """
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        x, y = x0, y0

        while True:
            # Don't check starting or ending position
            if (x, y) != (x0, y0) and (x, y) != (x1, y1):
                # Check if this tile blocks line of sight
                if not dungeon_map.is_transparent(x, y):
                    return False

            # Reached target
            if x == x1 and y == y1:
                break

            # Bresenham step
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        return True


class PerceptionSystem:
    """
    Manages entity perception and visibility.

    Future enhancements:
    - Line of sight (Bresenham algorithm)
    - Fog of war (explored vs visible)
    - Noise/sound propagation
    - Scent trails
    """

    def get_visible_entities(
        self,
        game,
        observer: Entity,
        radius: float = 10.0,
        line_of_sight: bool = True,
    ) -> List[Entity]:
        """
        Get all entities visible to observer.

        Args:
            game: Game instance
            observer: Entity doing the observing (usually player)
            radius: Maximum visibility distance
            line_of_sight: If True, check line of sight (default: True for realistic vision)

        Returns:
            List of visible entities

        Example:
            >>> perception = PerceptionSystem()
            >>> visible = perception.get_visible_entities(game, player, radius=8.0)
            >>> monsters = [e for e in visible if isinstance(e, Monster)]
        """
        visible = []

        for entity in game.state.entities.values():
            # Can't see yourself
            if entity == observer:
                continue

            # Skip entities without position (in inventory)
            if entity.x is None or entity.y is None:
                continue

            # Check distance
            distance = observer.distance_to(entity)
            if distance > radius:
                continue

            # Check line of sight (default enabled for realistic fog of war)
            if line_of_sight:
                if not self._has_line_of_sight(game, observer, entity):
                    continue

            visible.append(entity)

        return visible

    def get_visible_monsters(self, game, observer: Entity, radius: float = 10.0) -> List[Monster]:
        """
        Get living monsters visible to observer.

        Args:
            game: Game instance
            observer: Observer entity
            radius: Visibility range

        Returns:
            List of visible living monsters
        """
        visible = self.get_visible_entities(game, observer, radius)
        return [
            entity for entity in visible
            if isinstance(entity, Monster) and entity.is_alive
        ]

    def get_visible_items(self, game, observer: Entity, radius: float = 10.0) -> List[Entity]:
        """
        Get items visible to observer.

        Args:
            game: Game instance
            observer: Observer entity
            radius: Visibility range

        Returns:
            List of visible items
        """
        visible = self.get_visible_entities(game, observer, radius)
        return [
            entity for entity in visible
            if entity.entity_type == EntityType.ITEM
        ]

    def get_nearby_ore(self, game, observer: Entity, radius: float = 10.0) -> List[OreVein]:
        """
        Get ore veins visible to observer.

        Args:
            game: Game instance
            observer: Observer entity
            radius: Visibility range

        Returns:
            List of visible ore veins
        """
        visible = self.get_visible_entities(game, observer, radius)
        return [
            entity for entity in visible
            if isinstance(entity, OreVein)
        ]

    def get_entities_at_distance(
        self,
        game,
        observer: Entity,
        min_distance: float = 0.0,
        max_distance: float = 5.0
    ) -> List[Entity]:
        """
        Get entities within a distance range.

        Useful for:
        - Nearby threats (distance <= 3)
        - Mid-range targets (3 < distance <= 8)
        - Distant sightings (distance > 8)

        Args:
            game: Game instance
            observer: Observer entity
            min_distance: Minimum distance (inclusive)
            max_distance: Maximum distance (inclusive)

        Returns:
            Entities within distance range
        """
        entities = []

        for entity in game.state.entities.values():
            if entity == observer:
                continue

            if entity.x is None or entity.y is None:
                continue

            distance = observer.distance_to(entity)
            if min_distance <= distance <= max_distance:
                entities.append(entity)

        return entities

    def find_nearest(self, game, observer: Entity, entity_type: type) -> Optional[Entity]:
        """
        Find nearest entity of specific type.

        Args:
            game: Game instance
            observer: Observer entity
            entity_type: Type to search for (Monster, OreVein, etc.)

        Returns:
            Nearest entity of that type, or None

        Example:
            >>> nearest_monster = perception.find_nearest(game, player, Monster)
        """
        candidates = [
            e for e in game.state.entities.values()
            if isinstance(e, entity_type) and e != observer
            and e.x is not None and e.y is not None
        ]

        if not candidates:
            return None

        return min(candidates, key=lambda e: observer.distance_to(e))

    def _has_line_of_sight(self, game, observer: Entity, target: Entity) -> bool:
        """
        Check if observer has unobstructed line of sight to target.

        Uses Bresenham's line algorithm to check for walls.

        Args:
            game: Game instance
            observer: Observing entity
            target: Target entity

        Returns:
            True if line of sight is clear
        """
        dungeon_map = game.state.dungeon_map

        # Bresenham's line algorithm
        x0, y0 = int(observer.x), int(observer.y)
        x1, y1 = int(target.x), int(target.y)

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        x, y = x0, y0

        while True:
            # Don't check the observer's starting position or target's final position
            if (x, y) != (x0, y0) and (x, y) != (x1, y1):
                # Check if this tile blocks line of sight (walls block)
                if not dungeon_map.is_transparent(x, y):
                    return False

            # Reached target
            if x == x1 and y == y1:
                break

            # Bresenham step
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        return True

    def get_perception_info(self, game, observer: Entity) -> dict:
        """
        Get comprehensive perception information for observer.

        Useful for debugging and AI decision-making.

        Returns:
            Dictionary with visibility stats:
            - total_visible: Total entities visible
            - monsters_visible: Living monsters
            - items_visible: Items on ground
            - ore_visible: Ore veins
            - nearest_threat: Nearest living monster
            - nearest_item: Nearest item
        """
        visible = self.get_visible_entities(game, observer, radius=10.0)
        monsters = [e for e in visible if isinstance(e, Monster) and e.is_alive]
        items = [e for e in visible if e.entity_type == EntityType.ITEM]
        ore_veins = [e for e in visible if isinstance(e, OreVein)]

        nearest_monster = min(monsters, key=lambda m: observer.distance_to(m)) if monsters else None
        nearest_item = min(items, key=lambda i: observer.distance_to(i)) if items else None

        return {
            'total_visible': len(visible),
            'monsters_visible': len(monsters),
            'items_visible': len(items),
            'ore_visible': len(ore_veins),
            'nearest_threat': nearest_monster,
            'nearest_item': nearest_item,
            'visibility_radius': 10.0,
        }
