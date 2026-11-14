"""
Tests for save/load system.

Coverage:
- Saving game state
- Loading game state
- RNG state preservation
- Entity serialization
- Map serialization
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil

from src.core.save_load import SaveSystem, SaveLoadError
from src.core.game_state import GameState
from src.core.entities import Player, Monster, OreVein, Forge
from src.core.base.entity import Entity
from src.core.world import Map, TileType
from src.core.rng import GameRNG


pytestmark = pytest.mark.unit

@pytest.fixture
def temp_save_dir():
    """Create temporary directory for save files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def save_system(temp_save_dir):
    """Create save system with temp directory."""
    return SaveSystem(save_dir=temp_save_dir)


@pytest.fixture
def sample_state():
    """Create a sample game state."""
    GameRNG.initialize(42)

    # Create player
    player = Player(
        entity_id='player1',
        name='TestPlayer',
        x=10,
        y=10,
        hp=20,
        max_hp=20,
        attack=5,
        defense=2,
    )

    # Create map
    dungeon_map = Map(width=40, height=20)

    # Create state
    state = GameState(
        player=player,
        dungeon_map=dungeon_map,
        turn_count=50,
        current_floor=3,
        seed=42,
        player_name="TestPlayer",
    )

    # Add some entities
    monster = Monster(
        entity_id='m1',
        name='Goblin',
        x=15,
        y=15,
        hp=10,
        max_hp=10,
        attack=3,
        defense=1,
    )
    state.entities['m1'] = monster

    ore = OreVein(
        entity_id='ore1',
        name='Copper Vein',
        x=12,
        y=12,
    )
    state.entities['ore1'] = ore

    # Add messages
    state.add_message("Test message 1")
    state.add_message("Test message 2")

    return state


class TestSaveGame:
    """Test saving game state."""

    def test_save_creates_file(self, save_system, sample_state, temp_save_dir):
        """Save creates a JSON file."""
        save_path = save_system.save_game(sample_state, "test_save")

        assert save_path.exists()
        assert save_path.suffix == ".json"
        assert save_path.parent == temp_save_dir

    def test_save_contains_valid_json(self, save_system, sample_state):
        """Save file contains valid JSON."""
        save_path = save_system.save_game(sample_state, "test_save")

        with open(save_path, 'r') as f:
            data = json.load(f)

        assert data is not None
        assert isinstance(data, dict)

    def test_save_includes_metadata(self, save_system, sample_state):
        """Save file includes metadata."""
        save_path = save_system.save_game(sample_state, "test_save")

        with open(save_path, 'r') as f:
            data = json.load(f)

        assert "_metadata" in data
        metadata = data["_metadata"]
        assert "version" in metadata
        assert "timestamp" in metadata
        assert metadata["player_name"] == "TestPlayer"
        assert metadata["floor"] == 3
        assert metadata["turns"] == 50

    def test_save_includes_player(self, save_system, sample_state):
        """Save file includes player data."""
        save_path = save_system.save_game(sample_state, "test_save")

        with open(save_path, 'r') as f:
            data = json.load(f)

        assert "player" in data
        player = data["player"]
        assert player["name"] == "TestPlayer"
        assert player["x"] == 10
        assert player["y"] == 10
        assert player["hp"] == 20

    def test_save_includes_entities(self, save_system, sample_state):
        """Save file includes all entities."""
        save_path = save_system.save_game(sample_state, "test_save")

        with open(save_path, 'r') as f:
            data = json.load(f)

        assert "entities" in data
        entities = data["entities"]
        assert len(entities) == 2  # Monster + Ore
        assert "m1" in entities
        assert "ore1" in entities

    def test_save_includes_map(self, save_system, sample_state):
        """Save file includes map data."""
        save_path = save_system.save_game(sample_state, "test_save")

        with open(save_path, 'r') as f:
            data = json.load(f)

        assert "dungeon_map" in data
        dungeon_map = data["dungeon_map"]
        assert dungeon_map["width"] == 40
        assert dungeon_map["height"] == 20
        assert "tiles" in dungeon_map
        assert "rooms" in dungeon_map

    def test_save_overwrites_existing(self, save_system, sample_state):
        """Saving to same slot overwrites."""
        # First save
        save_system.save_game(sample_state, "test_save")

        # Modify state
        sample_state.turn_count = 100

        # Second save
        save_path = save_system.save_game(sample_state, "test_save")

        # Check it was overwritten
        with open(save_path, 'r') as f:
            data = json.load(f)

        assert data["turn_count"] == 100


class TestLoadGame:
    """Test loading game state."""

    def test_load_restores_player(self, save_system, sample_state):
        """Load restores player data."""
        save_system.save_game(sample_state, "test_save")

        loaded_state = save_system.load_game("test_save")

        assert loaded_state.player.name == "TestPlayer"
        assert loaded_state.player.x == 10
        assert loaded_state.player.y == 10
        assert loaded_state.player.hp == 20
        assert loaded_state.player.max_hp == 20

    def test_load_restores_entities(self, save_system, sample_state):
        """Load restores all entities.

        VB-23: entities is now the single store for every entity including
        the player (kept in sync by GameState), so the loaded count is the
        2 saved non-player entities plus the player itself.
        """
        save_system.save_game(sample_state, "test_save")

        loaded_state = save_system.load_game("test_save")

        assert len(loaded_state.entities) == 3
        assert "m1" in loaded_state.entities
        assert "ore1" in loaded_state.entities
        assert loaded_state.player.entity_id in loaded_state.entities

        monster = loaded_state.entities["m1"]
        assert monster.name == "Goblin"
        assert monster.x == 15

    def test_load_restores_map(self, save_system, sample_state):
        """Load restores map structure."""
        save_system.save_game(sample_state, "test_save")

        loaded_state = save_system.load_game("test_save")

        assert loaded_state.dungeon_map.width == 40
        assert loaded_state.dungeon_map.height == 20
        assert len(loaded_state.dungeon_map.rooms) > 0

    def test_load_restores_game_progress(self, save_system, sample_state):
        """Load restores turn count and floor."""
        save_system.save_game(sample_state, "test_save")

        loaded_state = save_system.load_game("test_save")

        assert loaded_state.turn_count == 50
        assert loaded_state.current_floor == 3
        assert loaded_state.player_name == "TestPlayer"

    def test_load_restores_messages(self, save_system, sample_state):
        """Load restores message log."""
        save_system.save_game(sample_state, "test_save")

        loaded_state = save_system.load_game("test_save")

        assert len(loaded_state.messages) == 2
        assert "Test message 1" in loaded_state.messages
        assert "Test message 2" in loaded_state.messages

    def test_load_nonexistent_raises_error(self, save_system):
        """Loading nonexistent save raises SaveLoadError."""
        with pytest.raises(SaveLoadError, match="Save file not found"):
            save_system.load_game("nonexistent")

    def test_load_corrupted_raises_error(self, save_system, temp_save_dir):
        """Loading corrupted save raises SaveLoadError."""
        # Create corrupted save file
        corrupted_path = temp_save_dir / "corrupted.json"
        with open(corrupted_path, 'w') as f:
            f.write("not valid json {{{")

        with pytest.raises(SaveLoadError, match="Corrupted save file"):
            save_system.load_game("corrupted")


class TestRNGStatePersistence:
    """Test that RNG state is properly saved and restored."""

    def test_rng_state_saved(self, save_system, sample_state):
        """RNG state is included in save."""
        # Get current RNG state
        rng = GameRNG.get_instance()
        rng_state = rng.getstate()
        sample_state.rng_state = rng_state

        save_path = save_system.save_game(sample_state, "test_save")

        with open(save_path, 'r') as f:
            data = json.load(f)

        assert "rng_state" in data
        assert data["rng_state"] is not None

    def test_rng_state_restored(self, save_system, sample_state):
        """RNG state is restored on load."""
        # Set RNG state
        rng = GameRNG.get_instance()
        sample_state.rng_state = rng.getstate()

        # Generate some random numbers (these advance the RNG state)
        before_values = [rng.randint(1, 100) for _ in range(5)]

        # Save (saves state AFTER generating those 5 numbers)
        sample_state.rng_state = rng.getstate()  # Update state after generation
        save_system.save_game(sample_state, "test_save")

        # Generate next 5 numbers (what should come next)
        expected_next = [rng.randint(1, 100) for _ in range(5)]

        # Reset RNG (different sequence)
        GameRNG.reset()
        GameRNG.initialize(99999)

        # Load (should restore RNG state to after first 5 numbers)
        loaded_state = save_system.load_game("test_save")

        # VB-18: RNG state is restored into the loaded GameState's own
        # dedicated instance (loaded_state.rng), not the process-global
        # singleton -- so a loaded game's randomness can no longer be
        # clobbered by another concurrent game re-seeding the singleton.
        rng = loaded_state.rng

        # Generate next 5 numbers - should match expected_next
        after_values = [rng.randint(1, 100) for _ in range(5)]

        # Should match the sequence that would have come next
        assert after_values == expected_next


class TestSaveManagement:
    """Test save file management functions."""

    def test_list_saves_empty(self, save_system):
        """List saves returns empty list when no saves."""
        saves = save_system.list_saves()
        assert saves == []

    def test_list_saves_shows_all(self, save_system, sample_state):
        """List saves shows all save files."""
        save_system.save_game(sample_state, "save1")
        save_system.save_game(sample_state, "save2")
        save_system.save_game(sample_state, "save3")

        saves = save_system.list_saves()

        assert len(saves) == 3
        slot_names = [s["slot_name"] for s in saves]
        assert "save1" in slot_names
        assert "save2" in slot_names
        assert "save3" in slot_names

    def test_list_saves_includes_metadata(self, save_system, sample_state):
        """List saves includes metadata for each save."""
        save_system.save_game(sample_state, "test_save")

        saves = save_system.list_saves()

        assert len(saves) == 1
        save_info = saves[0]
        assert save_info["slot_name"] == "test_save"
        assert save_info["player_name"] == "TestPlayer"
        assert save_info["floor"] == 3
        assert save_info["turns"] == 50
        assert "timestamp" in save_info

    def test_delete_save_removes_file(self, save_system, sample_state):
        """Delete save removes the file."""
        save_system.save_game(sample_state, "test_save")

        success = save_system.delete_save("test_save")

        assert success
        saves = save_system.list_saves()
        assert len(saves) == 0

    def test_delete_nonexistent_returns_false(self, save_system):
        """Deleting nonexistent save returns False."""
        success = save_system.delete_save("nonexistent")
        assert not success


class TestSeededRunPersistence:
    """Test that seeded runs remain deterministic across save/load."""

    def test_seeded_run_continues_correctly(self, save_system):
        """Seeded run produces same results after load."""

        # Initialize with seed
        GameRNG.initialize(seed="test-seed-123")
        rng = GameRNG.get_instance()

        # Create initial state
        player = Player(entity_id='p1', name='Test', x=5, y=5, hp=20, max_hp=20)
        dungeon_map = Map(width=40, height=20)

        # Generate first sequence
        sequence_before = [rng.randint(1, 100) for _ in range(10)]

        # Save state AFTER generating first sequence
        state = GameState(
            player=player,
            dungeon_map=dungeon_map,
            seed="test-seed-123",
            rng_state=rng.getstate(),  # State after 10 numbers
        )
        save_system.save_game(state, "seeded_test")

        # Continue generating (next 10 numbers)
        sequence_continue = [rng.randint(1, 100) for _ in range(10)]

        # Reset and initialize with different seed
        GameRNG.reset()
        GameRNG.initialize(seed="different-seed")

        # Load (should restore to after first 10 numbers)
        loaded_state = save_system.load_game("seeded_test")

        # VB-18: get the restored RNG from the loaded GameState's own
        # instance, not the process-global singleton (see
        # test_rng_state_restored above).
        rng = loaded_state.rng

        # Continue generating from loaded state (should get next 10)
        sequence_after = [rng.randint(1, 100) for _ in range(10)]

        # After-load sequence should match continue sequence
        assert sequence_after == sequence_continue


class TestVB19DataFidelity:
    """VB-19: save/load previously silently dropped inventory, equipped
    gear, run_type, and OreVein/Forge-specific fields entirely -- a
    reproduced round-trip went inventory 1 -> 0, run_type legacy -> pure,
    and Forge -> plain Entity. These tests pin the fixed behavior."""

    def test_inventory_round_trips(self, save_system, sample_state):
        item = Entity(entity_id='sword1', name='Iron Sword', hp=0, max_hp=0)
        sample_state.player.inventory.append(item)

        save_system.save_game(sample_state, "inv_test")
        loaded = save_system.load_game("inv_test")

        assert len(loaded.player.inventory) == 1
        assert loaded.player.inventory[0].entity_id == 'sword1'
        assert loaded.player.inventory[0].name == 'Iron Sword'

    def test_equipped_weapon_and_armor_round_trip(self, save_system, sample_state):
        weapon = Entity(entity_id='w1', name='Longsword', attack=10)
        armor = Entity(entity_id='a1', name='Chainmail', defense=8)
        sample_state.player.equipped_weapon = weapon
        sample_state.player.equipped_armor = armor

        save_system.save_game(sample_state, "equip_test")
        loaded = save_system.load_game("equip_test")

        assert loaded.player.equipped_weapon is not None
        assert loaded.player.equipped_weapon.entity_id == 'w1'
        assert loaded.player.equipped_weapon.attack == 10
        assert loaded.player.equipped_armor is not None
        assert loaded.player.equipped_armor.entity_id == 'a1'
        assert loaded.player.equipped_armor.defense == 8

    def test_no_equipped_gear_round_trips_as_none(self, save_system, sample_state):
        assert sample_state.player.equipped_weapon is None
        save_system.save_game(sample_state, "no_equip_test")
        loaded = save_system.load_game("no_equip_test")
        assert loaded.player.equipped_weapon is None
        assert loaded.player.equipped_armor is None

    def test_run_type_round_trips(self, save_system, sample_state):
        sample_state.run_type = "legacy"
        save_system.save_game(sample_state, "run_type_test")
        loaded = save_system.load_game("run_type_test")
        assert loaded.run_type == "legacy"

    def test_ore_vein_properties_round_trip(self, save_system, sample_state):
        # Non-default values -- proves fidelity, not a coincidental match.
        ore = OreVein(
            entity_id='ore_custom',
            x=5, y=5,
            ore_type='adamantite',
            hardness=91, conductivity=88, malleability=77, purity=95, density=60,
        )
        sample_state.entities['ore_custom'] = ore

        save_system.save_game(sample_state, "ore_test")
        loaded = save_system.load_game("ore_test")

        loaded_ore = loaded.entities['ore_custom']
        assert isinstance(loaded_ore, OreVein)
        assert loaded_ore.ore_type == 'adamantite'
        assert loaded_ore.hardness == 91
        assert loaded_ore.conductivity == 88
        assert loaded_ore.malleability == 77
        assert loaded_ore.purity == 95
        assert loaded_ore.density == 60
        assert loaded_ore.name == 'Adamantite Ore Vein'

    def test_forge_round_trips_as_forge_not_plain_entity(self, save_system, sample_state):
        forge = Forge(entity_id='forge1', x=8, y=8, forge_type='master_forge')
        sample_state.entities['forge1'] = forge

        save_system.save_game(sample_state, "forge_test")
        loaded = save_system.load_game("forge_test")

        loaded_forge = loaded.entities['forge1']
        assert isinstance(loaded_forge, Forge)
        assert loaded_forge.forge_type == 'master_forge'
        assert loaded_forge.name == 'Master Forge'
        assert loaded_forge.blocks_movement is True
        assert loaded_forge.get_stat('interactable') is True

    def test_blocks_movement_round_trips(self, save_system, sample_state):
        sample_state.player.blocks_movement = True
        save_system.save_game(sample_state, "blocks_test")
        loaded = save_system.load_game("blocks_test")
        assert loaded.player.blocks_movement is True


def test_equipped_shield_round_trips_and_old_saves_load_without_one(save_system, sample_state):
    from core.loot import LootGenerator
    shield = LootGenerator.get_instance().create_item('shield')
    sample_state.player.equipped_shield = shield
    data = save_system._serialize_entity(sample_state.player)
    assert save_system._deserialize_entity(data).equipped_shield.name == shield.name

    data.pop('equipped_shield')                      # a save from before VB-72
    assert save_system._deserialize_entity(data).equipped_shield is None


def test_fog_memory_survives_save_and_load(save_system, sample_state):
    """VB-105: what a viewer had seen of the floor is saved with the map."""
    sample_state.dungeon_map.explored_by = {"viewer-1": {(1, 2), (3, 4)}}
    save_system.save_game(sample_state, "fog_save")
    loaded = save_system.load_game("fog_save")
    assert loaded.dungeon_map.explored_by == {"viewer-1": {(1, 2), (3, 4)}}
