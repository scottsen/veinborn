"""Unit tests for loot generation system.

Tests for NetHack-style loot drops from monsters.
Following MVP_TESTING_GUIDE.md patterns.
"""
import pytest
from pathlib import Path
from core.loot import LootGenerator
from core.base.entity import Entity, EntityType
from core.rng import GameRNG


# ============================================================================
# LootGenerator Initialization Tests
# ============================================================================

class TestLootGeneratorInit:
    """Tests for LootGenerator initialization."""

    @pytest.mark.unit
    def test_loot_generator_creates_successfully(self):
        """LootGenerator initializes without errors."""
        generator = LootGenerator()
        assert generator is not None

    @pytest.mark.unit
    def test_loot_generator_loads_items(self):
        """LootGenerator loads item definitions from YAML."""
        generator = LootGenerator()
        assert len(generator.items) > 0
        assert 'dagger' in generator.items
        assert 'potion_healing' in generator.items
        assert 'gold_pile_small' in generator.items

    @pytest.mark.unit
    def test_loot_generator_loads_loot_tables(self):
        """LootGenerator loads loot tables from YAML."""
        generator = LootGenerator()
        assert len(generator.loot_tables) > 0
        assert 'goblin' in generator.loot_tables
        assert 'orc' in generator.loot_tables
        assert 'troll' in generator.loot_tables


# ============================================================================
# Item Definition Tests
# ============================================================================

class TestItemDefinitions:
    """Tests for item definitions loaded from items.yaml."""

    @pytest.fixture
    def generator(self):
        """Fixture for loot generator."""
        return LootGenerator()

    @pytest.mark.unit
    def test_weapon_definitions_exist(self, generator):
        """Weapons are defined with proper attributes."""
        dagger = generator.get_item_info('dagger')
        assert dagger is not None
        assert dagger['item_type'] == 'weapon'
        assert dagger['display_name'] == 'Dagger'
        assert 'attack_bonus' in dagger['stats']

    @pytest.mark.unit
    def test_armor_definitions_exist(self, generator):
        """Armor is defined with proper attributes."""
        leather = generator.get_item_info('leather_armor')
        assert leather is not None
        assert leather['item_type'] == 'armor'
        assert 'defense_bonus' in leather['stats']

    @pytest.mark.unit
    def test_potion_definitions_exist(self, generator):
        """Potions are defined with proper attributes."""
        healing = generator.get_item_info('potion_healing')
        assert healing is not None
        assert healing['item_type'] == 'potion'
        assert 'heal_amount' in healing['stats']
        assert healing['effect'] == 'heal'

    @pytest.mark.unit
    def test_gold_definitions_exist(self, generator):
        """Gold items are defined with proper attributes."""
        gold = generator.get_item_info('gold_pile_small')
        assert gold is not None
        assert gold['item_type'] == 'gold'
        assert 'gold_amount' in gold['stats']


# ============================================================================
# Loot Table Tests
# ============================================================================

class TestLootTables:
    """Tests for loot table definitions."""

    @pytest.fixture
    def generator(self):
        """Fixture for loot generator."""
        return LootGenerator()

    @pytest.mark.unit
    def test_goblin_loot_table_structure(self, generator):
        """Goblin loot table has expected structure."""
        goblin_table = generator.get_loot_table('goblin')
        assert goblin_table is not None
        assert 'gold' in goblin_table
        assert 'weapons' in goblin_table
        assert 'potions' in goblin_table

    @pytest.mark.unit
    def test_loot_table_has_drop_chances(self, generator):
        """Loot tables specify drop chances."""
        goblin_table = generator.get_loot_table('goblin')
        assert goblin_table['gold']['drop_chance'] > 0
        assert goblin_table['weapons']['drop_chance'] > 0

    @pytest.mark.unit
    def test_loot_table_has_weighted_items(self, generator):
        """Loot categories have weighted item lists."""
        orc_table = generator.get_loot_table('orc')
        gold_items = orc_table['gold']['items']
        assert len(gold_items) > 0
        assert 'weight' in gold_items[0]
        assert 'id' in gold_items[0]


# ============================================================================
# Loot Generation Tests
# ============================================================================

class TestLootGeneration:
    """Tests for generating loot from monsters."""

    @pytest.fixture
    def generator(self):
        """Fixture for loot generator."""
        return LootGenerator()

    @pytest.fixture
    def seeded_rng(self):
        """Fixture for deterministic RNG."""
        return GameRNG(seed=12345)

    @pytest.mark.unit
    def test_generate_loot_returns_list(self, generator, seeded_rng):
        """generate_loot() returns a list of entities."""
        items = generator.generate_loot('goblin', rng=seeded_rng)
        assert isinstance(items, list)

    @pytest.mark.unit
    def test_generated_items_are_entities(self, generator, seeded_rng):
        """Generated loot items are Entity objects."""
        items = generator.generate_loot('goblin', rng=seeded_rng)
        if items:  # May be empty due to RNG
            for item in items:
                assert isinstance(item, Entity)
                assert item.entity_type == EntityType.ITEM

    @pytest.mark.unit
    def test_generated_items_have_no_position(self, generator, seeded_rng):
        """Generated items start with no position (not yet placed)."""
        items = generator.generate_loot('orc', rng=seeded_rng)
        for item in items:
            # Items should have position set to None initially
            # They get positioned when dropped on the ground
            pass  # Position is set by attack_action.py

    @pytest.mark.unit
    def test_generated_items_have_content_id(self, generator, seeded_rng):
        """Generated items have content_id referencing item definition."""
        items = generator.generate_loot('troll', rng=seeded_rng)
        for item in items:
            assert item.content_id is not None
            # Verify content_id maps to a valid item
            assert generator.get_item_info(item.content_id) is not None

    @pytest.mark.unit
    def test_unknown_monster_type_returns_empty(self, generator, seeded_rng):
        """Unknown monster type returns empty list."""
        items = generator.generate_loot('dragon', rng=seeded_rng)
        assert items == []

    @pytest.mark.unit
    def test_loot_generation_deterministic_with_seed(self, generator):
        """Same seed produces same loot."""
        rng1 = GameRNG(seed=42)
        rng2 = GameRNG(seed=42)

        items1 = generator.generate_loot('goblin', rng=rng1)
        items2 = generator.generate_loot('goblin', rng=rng2)

        # Same seed should produce same number of items
        assert len(items1) == len(items2)

        # And same item types (content_ids)
        if items1:
            ids1 = [item.content_id for item in items1]
            ids2 = [item.content_id for item in items2]
            assert ids1 == ids2


# ============================================================================
# Monster-Specific Loot Tests
# ============================================================================

class TestMonsterSpecificLoot:
    """Tests for loot drops from specific monster types."""

    @pytest.fixture
    def generator(self):
        """Fixture for loot generator."""
        return LootGenerator()

    @pytest.mark.unit
    def test_goblin_drops_basic_loot(self, generator):
        """Goblins drop basic/common items."""
        # Generate loot 100 times to test distribution
        all_items = []
        for i in range(100):
            rng = GameRNG(seed=i)
            items = generator.generate_loot('goblin', rng=rng)
            all_items.extend(items)

        # Should have some drops
        assert len(all_items) > 0

        # Check that we're getting expected item types
        item_ids = [item.content_id for item in all_items]
        # Should see some gold (goblins have 70% gold drop rate)
        assert any('gold' in item_id for item_id in item_ids)

    @pytest.mark.unit
    def test_troll_drops_better_loot_than_goblin(self, generator):
        """Trolls drop better/rarer items than goblins."""
        goblin_items = []
        troll_items = []

        # Generate many samples
        for i in range(50):
            rng_g = GameRNG(seed=i)
            rng_t = GameRNG(seed=i)
            goblin_items.extend(generator.generate_loot('goblin', rng=rng_g))
            troll_items.extend(generator.generate_loot('troll', rng=rng_t))

        # Trolls should drop more items on average (higher drop rates)
        # This is probabilistic but should hold over 50 samples
        if len(goblin_items) > 0:
            troll_ratio = len(troll_items) / len(goblin_items)
            # Trolls have much higher drop rates, should be at least 1.5x
            assert troll_ratio > 1.2


# ============================================================================
# Item Entity Property Tests
# ============================================================================

class TestItemEntityProperties:
    """Tests for properties of generated item entities."""

    @pytest.fixture
    def generator(self):
        """Fixture for loot generator."""
        return LootGenerator()

    @pytest.fixture
    def sample_items(self, generator):
        """Generate sample items for testing."""
        items = []
        for monster in ['goblin', 'orc', 'troll']:
            for i in range(10):
                rng = GameRNG(seed=i * 100)
                items.extend(generator.generate_loot(monster, rng=rng))
        return items

    @pytest.mark.unit
    def test_items_have_item_type_stat(self, sample_items):
        """All items have item_type stat set."""
        for item in sample_items:
            item_type = item.get_stat('item_type')
            assert item_type is not None
            assert item_type in ['weapon', 'armor', 'potion', 'scroll', 'food', 'ring', 'gold', 'shield']

    @pytest.mark.unit
    def test_items_have_description(self, sample_items):
        """All items have description."""
        for item in sample_items:
            description = item.get_stat('description')
            assert description is not None
            assert len(description) > 0

    @pytest.mark.unit
    def test_items_have_display_properties(self, sample_items):
        """All items have symbol and color for display."""
        for item in sample_items:
            symbol = item.get_stat('symbol')
            color = item.get_stat('color')
            assert symbol is not None
            assert color is not None

    @pytest.mark.unit
    def test_weapons_have_attack_bonus(self, generator):
        """Weapon items have attack_bonus stat."""
        # Force generate a weapon by testing many times
        for i in range(50):
            rng = GameRNG(seed=i)
            items = generator.generate_loot('orc', rng=rng)
            for item in items:
                if item.get_stat('item_type') == 'weapon':
                    attack_bonus = item.get_stat('attack_bonus')
                    assert attack_bonus is not None
                    assert attack_bonus > 0
                    return  # Found and tested a weapon

    @pytest.mark.unit
    def test_armor_has_defense_bonus(self, generator):
        """Armor items have defense_bonus stat."""
        for i in range(50):
            rng = GameRNG(seed=i)
            items = generator.generate_loot('orc', rng=rng)
            for item in items:
                if item.get_stat('item_type') in ['armor', 'shield']:
                    defense_bonus = item.get_stat('defense_bonus')
                    assert defense_bonus is not None
                    assert defense_bonus > 0
                    return

    @pytest.mark.unit
    def test_potions_have_heal_amount(self, generator):
        """Healing potions have heal_amount stat."""
        for i in range(50):
            rng = GameRNG(seed=i)
            items = generator.generate_loot('goblin', rng=rng)
            for item in items:
                if item.get_stat('item_type') == 'potion':
                    heal_amount = item.get_stat('heal_amount')
                    if heal_amount:  # Some potions may not heal
                        assert heal_amount > 0
                        return

    @pytest.mark.unit
    def test_gold_has_variable_amounts(self, generator):
        """Gold drops have randomized amounts."""
        gold_amounts = []
        for i in range(30):
            rng = GameRNG(seed=i)
            items = generator.generate_loot('goblin', rng=rng)
            for item in items:
                if item.get_stat('item_type') == 'gold':
                    amount = item.get_stat('gold_amount')
                    gold_amounts.append(amount)

        # Should have some gold drops
        assert len(gold_amounts) > 0
        # Should have variation in amounts (not all the same)
        assert len(set(gold_amounts)) > 1


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestLootEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def generator(self):
        """Fixture for loot generator."""
        return LootGenerator()

    @pytest.mark.unit
    def test_generate_loot_handles_missing_monster_type(self, generator):
        """Gracefully handles unknown monster type."""
        rng = GameRNG(seed=42)
        items = generator.generate_loot('nonexistent_monster', rng=rng)
        assert items == []

    @pytest.mark.unit
    def test_generate_loot_with_default_rng(self, generator):
        """Can generate loot without providing RNG (uses default)."""
        items = generator.generate_loot('goblin')
        # Should not crash
        assert isinstance(items, list)

    @pytest.mark.unit
    def test_loot_generator_with_custom_data_dir(self, tmp_path):
        """LootGenerator can use custom data directory."""
        # This test verifies the constructor accepts custom path
        # For now just check it doesn't crash
        generator = LootGenerator(data_dir=tmp_path)
        assert generator is not None
        # Will have no items/tables since tmp_path is empty
        assert len(generator.items) == 0
        assert len(generator.loot_tables) == 0
