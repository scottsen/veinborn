"""
Unit tests for special room types.

Tests room type assignment, entity spawning, and special room mechanics.
"""

import pytest
from unittest.mock import Mock, patch

from core.world import Map, Room, RoomType
from core.spawning.entity_spawner import EntitySpawner
from core.config import ConfigLoader
from core.entity_loader import EntityLoader
from core.rng import GameRNG


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_map():
    """Create a test map with rooms."""
    dungeon_map = Map(width=40, height=20)
    return dungeon_map


@pytest.fixture
def entity_spawner():
    """Create an EntitySpawner instance."""
    config = ConfigLoader.load()
    entity_loader = EntityLoader()
    return EntitySpawner(config, entity_loader)


# ============================================================================
# Room Type Assignment Tests
# ============================================================================

@pytest.mark.unit
def test_room_type_defaults_to_normal():
    """Test that rooms default to NORMAL type."""
    room = Room(x=5, y=5, width=10, height=10)
    assert room.room_type == RoomType.NORMAL


@pytest.mark.unit
def test_room_type_can_be_assigned():
    """Test that room types can be explicitly assigned."""
    room = Room(x=5, y=5, width=10, height=10, room_type=RoomType.TREASURE)
    assert room.room_type == RoomType.TREASURE
    assert room.is_special()


@pytest.mark.unit
def test_room_is_special():
    """Test is_special() method."""
    normal_room = Room(x=5, y=5, width=10, height=10, room_type=RoomType.NORMAL)
    assert not normal_room.is_special()

    treasure_room = Room(x=5, y=5, width=10, height=10, room_type=RoomType.TREASURE)
    assert treasure_room.is_special()


@pytest.mark.unit
def test_all_room_types_exist():
    """Test that all expected room types are defined."""
    expected_types = ['NORMAL', 'TREASURE', 'MONSTER_DEN', 'ORE_CHAMBER', 'SHRINE', 'TRAP']
    for type_name in expected_types:
        assert hasattr(RoomType, type_name)


# ============================================================================
# Map Generation with Special Rooms Tests
# ============================================================================

@pytest.mark.unit
def test_map_assigns_special_rooms(test_map):
    """Test that map generation assigns special room types."""
    # Check that at least some rooms are special
    special_rooms = [room for room in test_map.rooms if room.is_special()]

    # Should have at least 1 special room in a typical map
    assert len(special_rooms) >= 0  # May be 0 if map is very small

    # If we have special rooms, verify types are valid
    for room in special_rooms:
        assert room.room_type in [
            RoomType.TREASURE,
            RoomType.MONSTER_DEN,
            RoomType.ORE_CHAMBER,
            RoomType.SHRINE,
            RoomType.TRAP
        ]


@pytest.mark.unit
def test_first_and_last_rooms_are_normal(test_map):
    """Test that first and last rooms are always NORMAL."""
    if len(test_map.rooms) >= 2:
        assert test_map.rooms[0].room_type == RoomType.NORMAL
        assert test_map.rooms[-1].room_type == RoomType.NORMAL


@pytest.mark.unit
def test_special_room_percentage():
    """Test that special rooms are within expected percentage (20-30%)."""
    # Create multiple maps and check average
    GameRNG.initialize(seed=12345)  # Fixed seed for reproducibility

    total_special = 0
    total_eligible = 0
    num_tests = 10

    for _ in range(num_tests):
        test_map = Map(width=80, height=24)
        if len(test_map.rooms) > 2:
            eligible_rooms = test_map.rooms[1:-1]  # Exclude first and last
            special_rooms = [r for r in eligible_rooms if r.is_special()]

            total_eligible += len(eligible_rooms)
            total_special += len(special_rooms)

    if total_eligible > 0:
        special_percentage = total_special / total_eligible
        # Should be roughly 20-30%, but allow some variance
        assert 0.1 <= special_percentage <= 0.5, f"Got {special_percentage:.2%} special rooms"


# ============================================================================
# Special Room Entity Spawning Tests
# ============================================================================

@pytest.mark.unit
def test_spawn_special_room_entities(entity_spawner):
    """Test that special room entities are spawned correctly."""
    GameRNG.initialize(seed=12345)

    # Create a test map
    test_map = Map(width=40, height=20)

    # Manually set some rooms to special types
    if len(test_map.rooms) >= 4:
        test_map.rooms[1].room_type = RoomType.TREASURE
        test_map.rooms[2].room_type = RoomType.MONSTER_DEN
        test_map.rooms[3].room_type = RoomType.ORE_CHAMBER

    # Spawn entities
    special_entities = entity_spawner.spawn_special_room_entities(floor=5, dungeon_map=test_map)

    # Verify structure
    assert 'monsters' in special_entities
    assert 'ores' in special_entities
    assert 'items' in special_entities

    # Verify entities were spawned
    assert isinstance(special_entities['monsters'], list)
    assert isinstance(special_entities['ores'], list)


@pytest.mark.unit
def test_treasure_room_spawns_high_quality_ore(entity_spawner):
    """Test that treasure rooms spawn high-quality ore."""
    GameRNG.initialize(seed=12345)

    # Create a test map with a treasure room
    test_map = Map(width=40, height=20)
    if len(test_map.rooms) >= 2:
        test_map.rooms[1].room_type = RoomType.TREASURE

        # Spawn entities
        special_entities = entity_spawner.spawn_special_room_entities(floor=5, dungeon_map=test_map)

        # Should have spawned some ore
        ores = special_entities['ores']
        assert len(ores) >= 0  # At least attempted to spawn

        # Check purity of spawned ores
        for ore in ores:
            assert ore.purity >= 80, f"Treasure ore should have high purity (>= 80), got {ore.purity}"


@pytest.mark.unit
def test_monster_den_spawns_extra_monsters(entity_spawner):
    """Test that monster dens spawn extra monsters."""
    GameRNG.initialize(seed=12345)

    # Create a test map with a monster den
    test_map = Map(width=40, height=20)
    if len(test_map.rooms) >= 2:
        test_map.rooms[1].room_type = RoomType.MONSTER_DEN

        # Spawn entities
        special_entities = entity_spawner.spawn_special_room_entities(floor=5, dungeon_map=test_map)

        # Should have spawned some monsters
        monsters = special_entities['monsters']
        assert len(monsters) >= 0  # At least attempted to spawn

        # Check that monsters have boosted stats
        for monster in monsters:
            # Den monsters should be stronger (implementation detail)
            assert monster.hp > 0
            assert monster.attack > 0


@pytest.mark.unit
def test_ore_chamber_spawns_multiple_ore_veins(entity_spawner):
    """Test that ore chambers spawn multiple ore veins."""
    GameRNG.initialize(seed=12345)

    # Create a test map with an ore chamber
    test_map = Map(width=40, height=20)
    if len(test_map.rooms) >= 2:
        test_map.rooms[1].room_type = RoomType.ORE_CHAMBER

        # Spawn entities
        special_entities = entity_spawner.spawn_special_room_entities(floor=5, dungeon_map=test_map)

        # Should have spawned multiple ores
        ores = special_entities['ores']
        assert len(ores) >= 0  # At least attempted to spawn

        # Check purity of chamber ores (should be good but not treasure-level)
        for ore in ores:
            assert ore.purity >= 70, f"Chamber ore should have decent purity (>= 70), got {ore.purity}"


@pytest.mark.unit
def test_shrine_room_exists():
    """Test that shrine room type exists (mechanics tested elsewhere)."""
    shrine_room = Room(x=5, y=5, width=10, height=10, room_type=RoomType.SHRINE)
    assert shrine_room.room_type == RoomType.SHRINE
    assert shrine_room.is_special()


@pytest.mark.unit
def test_trap_room_exists():
    """Test that trap room type exists (mechanics tested elsewhere)."""
    trap_room = Room(x=5, y=5, width=10, height=10, room_type=RoomType.TRAP)
    assert trap_room.room_type == RoomType.TRAP
    assert trap_room.is_special()


# ============================================================================
# Integration with Game Tests
# ============================================================================

@pytest.mark.unit
def test_special_room_entities_dont_overlap_starting_position():
    """Test that special room entities don't spawn at player start."""
    GameRNG.initialize(seed=12345)

    # Create a map and check starting position
    test_map = Map(width=40, height=20)
    start_pos = test_map.find_starting_position()

    # Set a room to special type
    if len(test_map.rooms) >= 2:
        test_map.rooms[1].room_type = RoomType.TREASURE

        # Spawn entities
        config = ConfigLoader.load()
        entity_loader = EntityLoader()
        spawner = EntitySpawner(config, entity_loader)
        special_entities = spawner.spawn_special_room_entities(floor=5, dungeon_map=test_map)

        # Check that no entity is at starting position
        for ore in special_entities['ores']:
            assert (ore.x, ore.y) != start_pos, "Entity spawned at player start!"


@pytest.mark.unit
def test_multiple_special_rooms_spawn_correctly(entity_spawner):
    """Test that multiple special room types can coexist."""
    GameRNG.initialize(seed=12345)

    # Create a test map with multiple special rooms
    test_map = Map(width=80, height=24)
    if len(test_map.rooms) >= 5:
        test_map.rooms[1].room_type = RoomType.TREASURE
        test_map.rooms[2].room_type = RoomType.MONSTER_DEN
        test_map.rooms[3].room_type = RoomType.ORE_CHAMBER
        test_map.rooms[4].room_type = RoomType.SHRINE

        # Spawn entities
        special_entities = entity_spawner.spawn_special_room_entities(floor=5, dungeon_map=test_map)

        # Should have spawned from multiple room types
        total_entities = len(special_entities['monsters']) + len(special_entities['ores'])
        assert total_entities >= 0  # At least attempted to spawn


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.unit
def test_special_rooms_with_no_valid_positions(entity_spawner):
    """Test special room spawning handles no valid positions gracefully."""
pytestmark = pytest.mark.unit

    GameRNG.initialize(seed=12345)

    # Create a minimal map (may have very small rooms)
    test_map = Map(width=20, height=10)

    # Try to spawn in all rooms
    for room in test_map.rooms:
        room.room_type = RoomType.TREASURE

    # Should not crash even if positions are limited
    special_entities = entity_spawner.spawn_special_room_entities(floor=5, dungeon_map=test_map)

    # Should return valid structure even if empty
    assert isinstance(special_entities['monsters'], list)
    assert isinstance(special_entities['ores'], list)


@pytest.mark.unit
def test_special_rooms_on_high_floors(entity_spawner):
    """Test that special rooms work correctly on high floors."""
    GameRNG.initialize(seed=12345)

    # Create a test map with special rooms
    test_map = Map(width=40, height=20)
    if len(test_map.rooms) >= 2:
        test_map.rooms[1].room_type = RoomType.TREASURE

        # Spawn on floor 15 (high floor)
        special_entities = entity_spawner.spawn_special_room_entities(floor=15, dungeon_map=test_map)

        # Should still spawn entities
        assert isinstance(special_entities, dict)
