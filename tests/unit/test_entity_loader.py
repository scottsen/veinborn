"""
Unit tests for EntityLoader.

Tests:
- Loading entity definitions from YAML
- Creating monsters from definitions
- Creating ore veins from definitions
- Error handling (invalid IDs, missing files)
- Jackpot ore generation
- Getting available entity IDs
"""

import pytest
import random
from pathlib import Path

from src.core.entity_loader import EntityLoader
from src.core.entities import Monster, OreVein
from src.core.base.entity import EntityType
from src.core.exceptions import ContentValidationError


pytestmark = pytest.mark.unit

class TestEntityLoaderInitialization:
    """Test EntityLoader initialization and loading."""

    def test_loader_initializes_with_default_path(self):
        """Test EntityLoader loads with default path."""
        loader = EntityLoader()

        assert loader is not None
        assert len(loader.monsters) > 0
        assert len(loader.ores) > 0

    def test_loader_loads_expected_monsters(self):
        """Test that all expected monsters are loaded."""
        loader = EntityLoader()

        expected_monsters = ['goblin', 'orc', 'troll']
        for monster_id in expected_monsters:
            assert monster_id in loader.monsters
            assert 'name' in loader.monsters[monster_id]
            assert 'stats' in loader.monsters[monster_id]

    def test_loader_loads_expected_ores(self):
        """Test that all expected ore types are loaded."""
        loader = EntityLoader()

        expected_ores = ['copper', 'iron', 'mithril', 'adamantite']
        for ore_id in expected_ores:
            assert ore_id in loader.ores
            assert 'name' in loader.ores[ore_id]
            assert 'quality' in loader.ores[ore_id]


class TestMonsterCreation:
    """Test creating monsters from YAML definitions."""

    def test_create_goblin(self):
        """Test creating a goblin from YAML definition."""
        loader = EntityLoader()
        goblin = loader.create_monster('goblin', x=10, y=20)

        assert isinstance(goblin, Monster)
        assert goblin.name == "Goblin"
        assert goblin.x == 10
        assert goblin.y == 20
        assert goblin.entity_type == EntityType.MONSTER
        assert goblin.content_id == "goblin"

        # Check stats match YAML
        assert goblin.hp == 6
        assert goblin.max_hp == 6
        assert goblin.attack == 3
        assert goblin.defense == 1
        assert goblin.get_stat('xp_reward') == 5
        assert goblin.get_stat('ai_type') == 'aggressive'

    def test_create_orc(self):
        """Test creating an orc from YAML definition."""
        loader = EntityLoader()
        orc = loader.create_monster('orc', x=5, y=15)

        assert isinstance(orc, Monster)
        assert orc.name == "Orc"
        assert orc.hp == 12
        assert orc.attack == 5
        assert orc.defense == 2
        assert orc.get_stat('xp_reward') == 15

    def test_create_troll(self):
        """Test creating a troll from YAML definition."""
        loader = EntityLoader()
        troll = loader.create_monster('troll', x=3, y=7)

        assert isinstance(troll, Monster)
        assert troll.name == "Troll"
        assert troll.hp == 20
        assert troll.attack == 7
        assert troll.defense == 3
        assert troll.get_stat('xp_reward') == 30

    def test_create_monster_invalid_id_raises_error(self):
        """Test that creating monster with invalid ID raises ContentValidationError."""
        loader = EntityLoader()

        with pytest.raises(ContentValidationError) as exc_info:
            loader.create_monster('dragon', x=10, y=10)

        assert "Unknown monster ID: 'dragon'" in str(exc_info.value)
        assert "goblin" in str(exc_info.value)  # Should list available monsters

    def test_create_monster_at_different_positions(self):
        """Test creating monsters at different positions."""
        loader = EntityLoader()

        positions = [(0, 0), (50, 50), (100, 100)]
        for x, y in positions:
            monster = loader.create_monster('goblin', x=x, y=y)
            assert monster.x == x
            assert monster.y == y


class TestOreVeinCreation:
    """Test creating ore veins from YAML definitions."""

    def test_create_copper_ore(self):
        """Test creating copper ore vein."""
        loader = EntityLoader()

        # Set random seed for predictable test
        random.seed(42)

        copper = loader.create_ore_vein('copper', x=10, y=20, floor=1)

        assert isinstance(copper, OreVein)
        assert copper.ore_type == "copper"
        assert copper.x == 10
        assert copper.y == 20
        assert copper.entity_type == EntityType.ORE_VEIN

        # Check properties are in expected range (20-50 for copper)
        assert 20 <= copper.get_stat('hardness') <= 100  # Could be jackpot
        assert 20 <= copper.get_stat('conductivity') <= 100
        assert 20 <= copper.get_stat('malleability') <= 100
        assert 20 <= copper.get_stat('purity') <= 100
        assert 20 <= copper.get_stat('density') <= 100

    def test_create_iron_ore(self):
        """Test creating iron ore vein."""
        loader = EntityLoader()
        random.seed(42)

        iron = loader.create_ore_vein('iron', x=15, y=25, floor=5)

        assert isinstance(iron, OreVein)
        assert iron.ore_type == "iron"
        # Properties should be in range (40-70 for iron, or 80-100 if jackpot)
        assert 40 <= iron.get_stat('hardness') <= 100

    def test_create_mithril_ore(self):
        """Test creating mithril ore vein."""
        loader = EntityLoader()
        random.seed(42)

        mithril = loader.create_ore_vein('mithril', x=20, y=30, floor=8)

        assert isinstance(mithril, OreVein)
        assert mithril.ore_type == "mithril"
        # Properties should be in range (60-90 for mithril, or 80-100 if jackpot)
        assert 60 <= mithril.get_stat('hardness') <= 100

    def test_create_adamantite_ore(self):
        """Test creating adamantite ore vein."""
        loader = EntityLoader()
        random.seed(42)

        adamantite = loader.create_ore_vein('adamantite', x=25, y=35, floor=15)

        assert isinstance(adamantite, OreVein)
        assert adamantite.ore_type == "adamantite"
        # Properties should be in range (80-100 for adamantite)
        assert 80 <= adamantite.get_stat('hardness') <= 100

    def test_ore_properties_are_randomized(self):
        """Test that ore properties vary between instances."""
        loader = EntityLoader()

        # Create multiple copper ores (without setting seed)
        ores = [
            loader.create_ore_vein('copper', x=i, y=i, floor=1)
            for i in range(10)
        ]

        # Check that not all ores have identical properties
        hardness_values = [ore.get_stat('hardness') for ore in ores]
        assert len(set(hardness_values)) > 1  # At least some variation

    def test_jackpot_ore_has_high_quality(self):
        """Test that jackpot ores have properties in 80-100 range."""
        loader = EntityLoader()

        # Generate many ores, some should be jackpots (5% chance)
        ores = []
        for i in range(200):
            random.seed(i)  # Try different seeds
            ore = loader.create_ore_vein('copper', x=i, y=i, floor=1)
            ores.append(ore)

        # At least one should be a jackpot (all properties >= 80)
        jackpot_ores = [
            ore for ore in ores
            if (ore.get_stat('hardness') >= 80 and
                ore.get_stat('conductivity') >= 80 and
                ore.get_stat('malleability') >= 80 and
                ore.get_stat('purity') >= 80 and
                ore.get_stat('density') >= 80)
        ]

        # With 200 attempts and 5% chance, expect ~10 jackpots
        assert len(jackpot_ores) > 0

    def test_create_ore_invalid_type_raises_error(self):
        """Test that creating ore with invalid type raises ContentValidationError."""
        loader = EntityLoader()

        with pytest.raises(ContentValidationError) as exc_info:
            loader.create_ore_vein('platinum', x=10, y=10, floor=1)

        assert "Unknown ore type: 'platinum'" in str(exc_info.value)
        assert "copper" in str(exc_info.value)  # Should list available ore types


class TestEntityQueries:
    """Test querying available entities and definitions."""

    def test_get_monster_ids(self):
        """Test getting list of all monster IDs."""
        loader = EntityLoader()
        monster_ids = loader.get_monster_ids()

        assert isinstance(monster_ids, list)
        assert 'goblin' in monster_ids
        assert 'orc' in monster_ids
        assert 'troll' in monster_ids
        assert len(monster_ids) >= 3

    def test_get_ore_ids(self):
        """Test getting list of all ore type IDs."""
        loader = EntityLoader()
        ore_ids = loader.get_ore_ids()

        assert isinstance(ore_ids, list)
        assert 'copper' in ore_ids
        assert 'iron' in ore_ids
        assert 'mithril' in ore_ids
        assert 'adamantite' in ore_ids
        assert len(ore_ids) >= 4

    def test_get_monster_definition(self):
        """Test getting raw monster definition."""
        loader = EntityLoader()
        goblin_def = loader.get_monster_definition('goblin')

        assert isinstance(goblin_def, dict)
        assert goblin_def['name'] == "Goblin"
        assert 'stats' in goblin_def
        assert goblin_def['stats']['hp'] == 6
        assert 'ai' in goblin_def

    def test_get_ore_definition(self):
        """Test getting raw ore definition."""
        loader = EntityLoader()
        copper_def = loader.get_ore_definition('copper')

        assert isinstance(copper_def, dict)
        assert copper_def['name'] == "Copper"
        assert 'quality' in copper_def
        assert copper_def['tier'] == 1

    def test_get_definition_invalid_id_raises_error(self):
        """Test that getting definition with invalid ID raises ContentValidationError."""
        loader = EntityLoader()

        with pytest.raises(ContentValidationError):
            loader.get_monster_definition('unicorn')

        with pytest.raises(ContentValidationError):
            loader.get_ore_definition('vibranium')


class TestEntityLoaderReload:
    """Test reloading entity definitions."""

    def test_reload_reloads_definitions(self):
        """Test that reload() reloads entity definitions."""
        loader = EntityLoader()

        initial_monster_count = len(loader.monsters)
        initial_ore_count = len(loader.ores)

        # Reload
        loader.reload()

        # Should still have the same entities loaded
        assert len(loader.monsters) == initial_monster_count
        assert len(loader.ores) == initial_ore_count

        # Verify entities still work after reload
        goblin = loader.create_monster('goblin', x=5, y=5)
        assert goblin.name == "Goblin"


class TestEntityLoaderIntegration:
    """Integration tests for EntityLoader."""

    def test_create_full_monster_party(self):
        """Test creating a full party of different monsters."""
        loader = EntityLoader()

        monsters = [
            loader.create_monster('goblin', x=10, y=10),
            loader.create_monster('orc', x=15, y=15),
            loader.create_monster('troll', x=20, y=20),
        ]

        assert len(monsters) == 3
        assert all(isinstance(m, Monster) for m in monsters)
        assert all(m.is_alive for m in monsters)

        # Verify stats progression (troll > orc > goblin)
        goblin, orc, troll = monsters
        assert troll.hp > orc.hp > goblin.hp
        assert troll.attack > orc.attack > goblin.attack

    def test_create_ore_veins_for_floor(self):
        """Test creating multiple ore veins for a floor."""
        loader = EntityLoader()

        # Floor 1: should be mostly copper
        floor_1_ores = [
            loader.create_ore_vein('copper', x=i, y=i, floor=1)
            for i in range(5)
        ]

        assert len(floor_1_ores) == 5
        assert all(isinstance(ore, OreVein) for ore in floor_1_ores)
        assert all(ore.ore_type == 'copper' for ore in floor_1_ores)

    def test_data_driven_extensibility(self):
        """Test that system is data-driven (ready for modding)."""

        loader = EntityLoader()

        # Verify we can query what's available
        available_monsters = loader.get_monster_ids()
        available_ores = loader.get_ore_ids()

        # Verify we can create any available entity
        for monster_id in available_monsters:
            monster = loader.create_monster(monster_id, x=0, y=0)
            assert monster.content_id == monster_id

        for ore_id in available_ores:
            ore = loader.create_ore_vein(ore_id, x=0, y=0, floor=1)
            assert ore.ore_type == ore_id
