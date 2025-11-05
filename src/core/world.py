"""
Map and world generation for Brogue.
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

from .rng import GameRNG


class TileType(Enum):
    WALL = '#'
    FLOOR = '.'
    DOOR = '+'
    STAIRS_UP = '<'
    STAIRS_DOWN = '>'


@dataclass
class Tile:
    """Individual map tile."""
    tile_type: TileType = TileType.WALL
    walkable: bool = False
    transparent: bool = False
    explored: bool = False

    def __post_init__(self):
        if self.tile_type == TileType.FLOOR:
            self.walkable = True
            self.transparent = True
        elif self.tile_type == TileType.DOOR:
            self.walkable = True
            self.transparent = False
        elif self.tile_type == TileType.STAIRS_DOWN:
            self.walkable = True
            self.transparent = True
        elif self.tile_type == TileType.STAIRS_UP:
            self.walkable = True
            self.transparent = True


@dataclass
class Room:
    """Dungeon room representation."""
    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def intersects(self, other: 'Room') -> bool:
        """Check if this room intersects with another."""
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)


class Map:
    """Game map with BSP generation."""
    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.tiles = [[Tile() for _ in range(height)] for _ in range(width)]
        self.rooms: List[Room] = []

        # PERFORMANCE: Cache stairs positions (searched 1,290x per game!)
        self._stairs_down_cache: Optional[Tuple[int, int]] = None
        self._stairs_up_cache: Optional[Tuple[int, int]] = None

        self.generate()

    def generate(self):
        """Generate the map using BSP algorithm."""
        # Clear the map
        self.rooms = []

        # PERFORMANCE: Clear stairs cache when regenerating map
        self._stairs_down_cache = None
        self._stairs_up_cache = None

        for x in range(self.width):
            for y in range(self.height):
                self.tiles[x][y] = Tile(TileType.WALL)

        # Generate rooms using BSP
        root = BSPNode(0, 0, self.width, self.height)
        self.split_node(root, min_size=6)
        self.create_rooms(root)
        self.connect_rooms(root)
        self.apply_to_map(root)

        # Place stairs down in the last room
        self.place_stairs_down()

    def split_node(self, node: 'BSPNode', min_size: int):
        """Recursively split BSP nodes."""
        if node.width < min_size * 2 or node.height < min_size * 2:
            return

        # Decide split direction
        rng = GameRNG.get_instance()
        split_horizontal = rng.choice([True, False])
        if node.width > node.height * 1.25:
            split_horizontal = False
        elif node.height > node.width * 1.25:
            split_horizontal = True

        # Calculate split position
        if split_horizontal:
            split_pos = rng.randint(node.height // 3, (node.height * 2) // 3)
            node.left = BSPNode(node.x, node.y, node.width, split_pos)
            node.right = BSPNode(node.x, node.y + split_pos,
                               node.width, node.height - split_pos)
        else:
            split_pos = rng.randint(node.width // 3, (node.width * 2) // 3)
            node.left = BSPNode(node.x, node.y, split_pos, node.height)
            node.right = BSPNode(node.x + split_pos, node.y,
                               node.width - split_pos, node.height)

        # Recursively split children
        self.split_node(node.left, min_size)
        self.split_node(node.right, min_size)

    def create_rooms(self, node: 'BSPNode'):
        """Create rooms in leaf nodes."""
        if not node.left and not node.right:  # Leaf node
            padding = 1
            min_room_size = 4

            # Ensure valid range for room dimensions
            rng = GameRNG.get_instance()
            max_width = max(min_room_size, node.width - (padding * 2))
            max_height = max(min_room_size, node.height - (padding * 2))

            room_width = rng.randint(min_room_size, max_width)
            room_height = rng.randint(min_room_size, max_height)

            # Calculate safe positioning
            max_x_offset = max(0, node.width - room_width - padding * 2)
            max_y_offset = max(0, node.height - room_height - padding * 2)

            room_x = node.x + padding + (rng.randint(0, max_x_offset) if max_x_offset > 0 else 0)
            room_y = node.y + padding + (rng.randint(0, max_y_offset) if max_y_offset > 0 else 0)

            node.room = Room(room_x, room_y, room_width, room_height)
            self.rooms.append(node.room)
        else:
            if node.left:
                self.create_rooms(node.left)
            if node.right:
                self.create_rooms(node.right)

    def connect_rooms(self, node: 'BSPNode'):
        """Create corridors between rooms."""
        if node.left and node.right:
            left_room = self.get_room(node.left)
            right_room = self.get_room(node.right)

            if left_room and right_room:
                # Create L-shaped corridor
                rng = GameRNG.get_instance()
                start_x, start_y = left_room.center
                end_x, end_y = right_room.center

                if rng.random() < 0.5:
                    # Horizontal then vertical
                    for x in range(min(start_x, end_x), max(start_x, end_x) + 1):
                        node.corridors.append((x, start_y))
                    for y in range(min(start_y, end_y), max(start_y, end_y) + 1):
                        node.corridors.append((end_x, y))
                else:
                    # Vertical then horizontal
                    for y in range(min(start_y, end_y), max(start_y, end_y) + 1):
                        node.corridors.append((start_x, y))
                    for x in range(min(start_x, end_x), max(start_x, end_x) + 1):
                        node.corridors.append((x, end_y))

            self.connect_rooms(node.left)
            self.connect_rooms(node.right)

    def get_room(self, node: 'BSPNode') -> Optional[Room]:
        """Get a room from a node or its children."""
        if node.room:
            return node.room
        else:
            left_room = self.get_room(node.left) if node.left else None
            right_room = self.get_room(node.right) if node.right else None
            return left_room or right_room

    def apply_to_map(self, node: 'BSPNode'):
        """Apply rooms and corridors to the tile map."""
        # Apply room
        if node.room:
            for y in range(node.room.y, node.room.y + node.room.height):
                for x in range(node.room.x, node.room.x + node.room.width):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.tiles[x][y] = Tile(TileType.FLOOR)

        # Apply corridors
        for x, y in node.corridors:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[x][y] = Tile(TileType.FLOOR)

        # Recursively apply children
        if node.left:
            self.apply_to_map(node.left)
        if node.right:
            self.apply_to_map(node.right)

    def in_bounds(self, x: int, y: int) -> bool:
        """Check if position is within map bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a tile is walkable."""
        if self.in_bounds(x, y):
            return self.tiles[x][y].walkable
        return False

    def is_transparent(self, x: int, y: int) -> bool:
        """Check if a tile is transparent (for line-of-sight)."""
        if self.in_bounds(x, y):
            return self.tiles[x][y].transparent
        return False

    def is_wall(self, x: int, y: int) -> bool:
        """Check if a tile is a wall."""
        if self.in_bounds(x, y):
            return self.tiles[x][y].tile_type == TileType.WALL
        return True

    def find_starting_position(self) -> Tuple[int, int]:
        """Find a good starting position for the player."""
        if self.rooms:
            return self.rooms[0].center
        return (1, 1)

    def find_monster_positions(self, count: int) -> List[Tuple[int, int]]:
        """
        Find walkable positions for monsters.

        Returns room centers, but only if they're actually walkable.
        Falls back to finding any walkable tile in the room if center isn't walkable.
        """
        positions = []
        for room in self.rooms[1:]:  # Skip first room (player starts there)
            if len(positions) >= count:
                break

            # Try room center first
            cx, cy = room.center
            if self.is_walkable(cx, cy):
                positions.append((cx, cy))
            else:
                # Center isn't walkable, find any walkable tile in room
                for x in range(room.x, room.x + room.width):
                    for y in range(room.y, room.y + room.height):
                        if self.is_walkable(x, y):
                            positions.append((x, y))
                            break
                    else:
                        continue
                    break

        return positions

    def find_ore_vein_positions(self, count: int) -> List[Tuple[int, int]]:
        """
        Find positions for ore veins.

        Ore veins spawn adjacent to walls (along room edges).
        This gives them a "embedded in rock" feel.
        """
        positions = []

        for room in self.rooms:
            # Check room perimeter for wall-adjacent floor tiles
            for x in range(room.x, room.x + room.width):
                for y in range(room.y, room.y + room.height):
                    if not self.in_bounds(x, y):
                        continue

                    # Must be floor
                    if not self.is_walkable(x, y):
                        continue

                    # Must be adjacent to at least one wall
                    adjacent_to_wall = False
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            if self.is_wall(x + dx, y + dy):
                                adjacent_to_wall = True
                                break
                        if adjacent_to_wall:
                            break

                    if adjacent_to_wall and GameRNG.get_instance().random() < 0.1:  # 10% chance
                        positions.append((x, y))

                    if len(positions) >= count:
                        return positions

        return positions

    def place_stairs_down(self) -> Optional[Tuple[int, int]]:
        """
        Place stairs down in the last room.

        Returns:
            Position of stairs, or None if no rooms
        """
        if not self.rooms:
            return None

        # Place in last room (furthest from start)
        last_room = self.rooms[-1]
        x, y = last_room.center

        self.tiles[x][y] = Tile(TileType.STAIRS_DOWN)

        # PERFORMANCE: Cache position immediately (avoid 1,290 searches per game!)
        self._stairs_down_cache = (x, y)

        return (x, y)

    def place_stairs_up(self) -> Optional[Tuple[int, int]]:
        """
        Place stairs up in the first room.

        Returns:
            Position of stairs, or None if no rooms
        """
        if not self.rooms:
            return None

        # Place in first room (where player starts)
        first_room = self.rooms[0]
        x, y = first_room.center

        self.tiles[x][y] = Tile(TileType.STAIRS_UP)

        # PERFORMANCE: Cache position immediately
        self._stairs_up_cache = (x, y)

        return (x, y)

    def find_stairs_down(self) -> Optional[Tuple[int, int]]:
        """
        Find position of stairs down.

        PERFORMANCE FIX: Use cached position instead of O(width*height) search.
        Called 1,290 times per game in profiling!
        """
        # Check cache first
        if self._stairs_down_cache is not None:
            return self._stairs_down_cache

        # Cache miss - search and cache result
        for x in range(self.width):
            for y in range(self.height):
                if self.tiles[x][y].tile_type == TileType.STAIRS_DOWN:
                    self._stairs_down_cache = (x, y)
                    return (x, y)

        return None

    def find_stairs_up(self) -> Optional[Tuple[int, int]]:
        """
        Find position of stairs up.

        PERFORMANCE: Use cached position.
        """
        # Check cache first
        if self._stairs_up_cache is not None:
            return self._stairs_up_cache

        # Cache miss - search and cache result
        for x in range(self.width):
            for y in range(self.height):
                if self.tiles[x][y].tile_type == TileType.STAIRS_UP:
                    self._stairs_up_cache = (x, y)
                    return (x, y)

        return None


class BSPNode:
    """Binary Space Partitioning node for map generation."""
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.left: Optional['BSPNode'] = None
        self.right: Optional['BSPNode'] = None
        self.room: Optional[Room] = None
        self.corridors: List[Tuple[int, int]] = []