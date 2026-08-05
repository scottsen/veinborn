"""
Entity-placement policy for the dungeon map.

Decides *where* players, monsters, ore veins, special rooms, and stairs go.
Kept separate from `Map`'s BSP dungeon-generation algorithm (world.py) so
generation and placement policy can evolve independently — new entity
types shouldn't require touching the BSP splitter/corridor code, and vice
versa.

Functions take the `Map` instance as their first argument (duck-typed on
its public query surface: rooms, tiles, config, is_walkable/is_wall/
in_bounds) rather than being methods on Map itself.
"""
import logging
from typing import List, Tuple, Optional, TYPE_CHECKING

from ..rng import GameRNG
from ..world import RoomType, Tile, TileType

if TYPE_CHECKING:
    from ..world import Map, Room

logger = logging.getLogger(__name__)


def _find_first_walkable_in_room(game_map: 'Map', room: 'Room') -> Optional[Tuple[int, int]]:
    """
    Find the first walkable position in a room.

    Args:
        room: The room to search

    Returns:
        (x, y) tuple if found, None otherwise
    """
    for x in range(room.x, room.x + room.width):
        for y in range(room.y, room.y + room.height):
            if game_map.is_walkable(x, y):
                return (x, y)
    return None


def find_player_spawn_positions(game_map: 'Map', count: int) -> List[Tuple[int, int]]:
    """
    Find spawn positions for multiple players in different rooms.

    Players spawn in the first N rooms, centered or near the center.
    This ensures they start in different areas of the dungeon.

    Args:
        count: Number of spawn positions to find

    Returns:
        List of (x, y) tuples for player spawn positions
    """
    positions = []

    # Use the first N rooms for player spawns
    for room in game_map.rooms[:count]:
        if len(positions) >= count:
            break

        # Try room center first
        cx, cy = room.center
        if game_map.is_walkable(cx, cy):
            positions.append((cx, cy))
        else:
            # Center isn't walkable, find any walkable tile in room
            pos = _find_first_walkable_in_room(game_map, room)
            if pos:
                positions.append(pos)

    # Fallback if we don't have enough rooms
    if len(positions) < count:
        logger.warning(f"Only found {len(positions)} spawn positions, requested {count}")

    return positions


def find_monster_positions(game_map: 'Map', count: int) -> List[Tuple[int, int]]:
    """
    Find walkable positions for monsters.

    Returns room centers, but only if they're actually walkable.
    Falls back to finding any walkable tile in the room if center isn't walkable.
    """
    positions = []
    for room in game_map.rooms[1:]:  # Skip first room (player starts there)
        if len(positions) >= count:
            break

        # Try room center first
        cx, cy = room.center
        if game_map.is_walkable(cx, cy):
            positions.append((cx, cy))
        else:
            # Center isn't walkable, find any walkable tile in room
            pos = _find_first_walkable_in_room(game_map, room)
            if pos:
                positions.append(pos)

    return positions


def _is_adjacent_to_wall(game_map: 'Map', x: int, y: int) -> bool:
    """Check if position is adjacent to at least one wall."""
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            if game_map.is_wall(x + dx, y + dy):
                return True
    return False


def _is_valid_ore_position(game_map: 'Map', x: int, y: int) -> bool:
    """Check if position is valid for ore vein spawning."""
    # Must be in bounds
    if not game_map.in_bounds(x, y):
        return False

    # Must be walkable floor
    if not game_map.is_walkable(x, y):
        return False

    # Must be adjacent to at least one wall
    return _is_adjacent_to_wall(game_map, x, y)


def _get_ore_spawn_probability(game_map: 'Map') -> float:
    """Get ore spawn probability from config."""
    if game_map.config:
        ore_pos_config = game_map.config.get_ore_positioning_config()
        return ore_pos_config['wall_adjacency_probability']
    return 0.1  # Default


def _find_ore_positions_in_room(
    game_map: 'Map', room: 'Room', needed_count: int, spawn_prob: float
) -> List[Tuple[int, int]]:
    """
    Find valid ore positions within a single room.

    Args:
        room: The room to search for ore positions
        needed_count: Maximum number of positions to find
        spawn_prob: Probability threshold for ore spawning

    Returns:
        List of (x, y) positions found in this room (up to needed_count)
    """
    rng = GameRNG.get_instance()
    positions = []

    for x in range(room.x, room.x + room.width):
        for y in range(room.y, room.y + room.height):
            if len(positions) >= needed_count:
                break  # Found enough in this room
            if _is_valid_ore_position(game_map, x, y) and rng.random() < spawn_prob:
                positions.append((x, y))

    return positions


def find_ore_vein_positions(game_map: 'Map', count: int) -> List[Tuple[int, int]]:
    """
    Find positions for ore veins.

    Ore veins spawn adjacent to walls (along room edges).
    This gives them a "embedded in rock" feel.
    """
    positions = []
    spawn_prob = _get_ore_spawn_probability(game_map)

    for room in game_map.rooms:
        needed = count - len(positions)
        if needed <= 0:
            break  # Found enough positions

        room_positions = _find_ore_positions_in_room(game_map, room, needed, spawn_prob)
        positions.extend(room_positions)

    return positions


def _get_special_room_config(game_map: 'Map'):
    """
    Get special room configuration with defaults.

    Returns:
        tuple: (special_types, min_pct, max_pct)
            - special_types: List of (RoomType, weight) tuples
            - min_pct: Minimum percentage of rooms to make special
            - max_pct: Maximum percentage of rooms to make special
    """
    if game_map.config:
        assignment_config = game_map.config.get_special_room_assignment_config()
        room_weights = assignment_config['room_type_weights']
        special_types = [
            (RoomType.TREASURE, room_weights['treasure_room']),
            (RoomType.MONSTER_DEN, room_weights['monster_den']),
            (RoomType.ORE_CHAMBER, room_weights['ore_chamber']),
            (RoomType.SHRINE, room_weights['shrine']),
            (RoomType.TRAP, room_weights['trap_room']),
        ]
        percentage_config = assignment_config['percentage']
        min_pct = percentage_config['min']
        max_pct = percentage_config['max']
    else:
        # Default values if no config provided
        special_types = [
            (RoomType.TREASURE, 2),
            (RoomType.MONSTER_DEN, 2),
            (RoomType.ORE_CHAMBER, 3),
            (RoomType.SHRINE, 1),
            (RoomType.TRAP, 1),
        ]
        min_pct = 0.2
        max_pct = 0.3

    return special_types, min_pct, max_pct


def assign_special_rooms(game_map: 'Map'):
    """
    Assign special room types to some rooms.

    Special rooms provide unique gameplay elements:
    - Treasure rooms: High-quality loot
    - Monster dens: Extra monsters and challenges
    - Ore chambers: Multiple high-quality ore veins
    - Shrines: Healing and buffs
    - Trap rooms: Environmental hazards

    Rules:
    - First room (starting room) is always NORMAL
    - Last room (stairs room) is always NORMAL
    - 20-30% of other rooms become special
    """
    if len(game_map.rooms) <= 2:
        # Not enough rooms for special types
        return

    rng = GameRNG.get_instance()
    special_types, min_pct, max_pct = _get_special_room_config(game_map)

    # Calculate how many special rooms to create
    # Exclude first and last room
    eligible_rooms = game_map.rooms[1:-1]
    num_special = max(1, int(len(eligible_rooms) * rng.uniform(min_pct, max_pct)))

    # Randomly select rooms to make special
    special_rooms = rng.sample(eligible_rooms, min(num_special, len(eligible_rooms)))

    # Assign types using weighted random selection
    for room in special_rooms:
        types, weights = zip(*special_types)
        room.room_type = rng.choices(types, weights=weights)[0]


def place_stairs_down(game_map: 'Map') -> Optional[Tuple[int, int]]:
    """
    Place stairs down in the last room.

    Returns:
        Position of stairs, or None if no rooms
    """
    if not game_map.rooms:
        return None

    # Place in last room (furthest from start)
    last_room = game_map.rooms[-1]
    x, y = last_room.center

    game_map.tiles[x][y] = Tile(TileType.STAIRS_DOWN)

    # PERFORMANCE: Cache position immediately (avoid 1,290 searches per game!)
    game_map._stairs_down_cache = (x, y)

    return (x, y)


def place_stairs_up(game_map: 'Map') -> Optional[Tuple[int, int]]:
    """
    Place stairs up in the first room.

    Returns:
        Position of stairs, or None if no rooms
    """
    if not game_map.rooms:
        return None

    # Place in first room (where player starts)
    first_room = game_map.rooms[0]
    x, y = first_room.center

    game_map.tiles[x][y] = Tile(TileType.STAIRS_UP)

    # PERFORMANCE: Cache position immediately
    game_map._stairs_up_cache = (x, y)

    return (x, y)
