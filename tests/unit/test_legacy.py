"""
Unit tests for Legacy Vault system (Phase 6).

Tests the meta-progression system that saves rare ore on death
and tracks Pure vs Legacy victories.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from core.legacy import (
    LegacyVault,
    LegacyOre,
    get_vault,
    reset_vault,
    PURITY_THRESHOLD,
    MAX_VAULT_SIZE
)
from core.entities import OreVein


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_vault_path(tmp_path):
    """Create a temporary vault path for testing."""
    vault_path = tmp_path / "legacy_vault.json"
    with patch('core.legacy.LEGACY_VAULT_PATH', vault_path):
        yield vault_path


@pytest.fixture
def fresh_vault(temp_vault_path):
    """Create a fresh Legacy Vault for testing."""
    vault = LegacyVault()
    return vault


@pytest.fixture
def rare_copper_ore():
    """Create a rare (80+ purity) copper ore."""
    return OreVein(
        ore_type="copper",
        x=10,
        y=10,
        hardness=85,
        conductivity=82,
        malleability=88,
        purity=90,  # Legacy-worthy!
        density=75
    )


@pytest.fixture
def legendary_mithril_ore():
    """Create a legendary (95+ purity) mithril ore."""
    return OreVein(
        ore_type="mithril",
        x=15,
        y=15,
        hardness=95,
        conductivity=98,
        malleability=92,
        purity=99,  # Legendary!
        density=88
    )


@pytest.fixture
def common_iron_ore():
    """Create a common (< 80 purity) iron ore."""
    return OreVein(
        ore_type="iron",
        x=12,
        y=12,
        hardness=60,
        conductivity=55,
        malleability=65,
        purity=50,  # Not legacy-worthy
        density=70
    )


# ============================================================================
# LegacyOre Tests
# ============================================================================

@pytest.mark.unit
def test_legacy_ore_creation(rare_copper_ore):
    """Test creating LegacyOre from OreVein."""
    legacy_ore = LegacyOre.from_ore_vein(rare_copper_ore, floor=5)

    assert legacy_ore.ore_type == "copper"
    assert legacy_ore.hardness == 85
    assert legacy_ore.conductivity == 82
    assert legacy_ore.malleability == 88
    assert legacy_ore.purity == 90
    assert legacy_ore.density == 75
    assert legacy_ore.floor_found == 5
    assert legacy_ore.timestamp != ""


@pytest.mark.unit
def test_legacy_ore_is_legacy_worthy(rare_copper_ore, common_iron_ore):
    """Test purity threshold check."""
    rare_ore = LegacyOre.from_ore_vein(rare_copper_ore)
    common_ore = LegacyOre.from_ore_vein(common_iron_ore)

    assert rare_ore.is_legacy_worthy()  # 90 purity
    assert not common_ore.is_legacy_worthy()  # 50 purity


@pytest.mark.unit
def test_legacy_ore_quality_tiers():
    """Test quality tier classification."""
    # Test all tier boundaries
    tiers = [
        (25, "Poor"),
        (40, "Common"),
        (60, "Uncommon"),
        (80, "Rare"),
        (90, "Epic"),
        (99, "Legendary")
    ]

    for purity, expected_tier in tiers:
        ore = LegacyOre(
            ore_type="test",
            hardness=50,
            conductivity=50,
            malleability=50,
            purity=purity,
            density=50
        )
        assert ore.get_quality_tier() == expected_tier


@pytest.mark.unit
def test_legacy_ore_serialization(rare_copper_ore):
    """Test converting LegacyOre to/from dict."""
    legacy_ore = LegacyOre.from_ore_vein(rare_copper_ore, floor=3)

    # Convert to dict
    ore_dict = legacy_ore.to_dict()
    assert isinstance(ore_dict, dict)
    assert ore_dict['ore_type'] == 'copper'
    assert ore_dict['purity'] == 90
    assert ore_dict['floor_found'] == 3

    # Convert back from dict
    restored_ore = LegacyOre.from_dict(ore_dict)
    assert restored_ore.ore_type == legacy_ore.ore_type
    assert restored_ore.purity == legacy_ore.purity
    assert restored_ore.floor_found == legacy_ore.floor_found


# ============================================================================
# LegacyVault Basic Tests
# ============================================================================

@pytest.mark.unit
def test_vault_initialization(fresh_vault):
    """Test vault starts empty with zero stats."""
    assert fresh_vault.get_ore_count() == 0
    assert fresh_vault.total_pure_victories == 0
    assert fresh_vault.total_legacy_victories == 0
    assert fresh_vault.total_runs == 0
    assert not fresh_vault.is_full()


@pytest.mark.unit
def test_vault_add_ore_success(fresh_vault, rare_copper_ore):
    """Test adding legacy-worthy ore to vault."""
    added = fresh_vault.add_ore(rare_copper_ore, floor=5)

    assert added is True
    assert fresh_vault.get_ore_count() == 1

    ores = fresh_vault.get_ores()
    assert ores[0].ore_type == "copper"
    assert ores[0].purity == 90
    assert ores[0].floor_found == 5


@pytest.mark.unit
def test_vault_add_ore_reject_low_purity(fresh_vault, common_iron_ore):
    """Test vault rejects ore below purity threshold."""
    added = fresh_vault.add_ore(common_iron_ore)

    assert added is False
    assert fresh_vault.get_ore_count() == 0


@pytest.mark.unit
def test_vault_withdraw_ore(fresh_vault, rare_copper_ore, legendary_mithril_ore):
    """Test withdrawing ore from vault."""
    # Add two ores
    fresh_vault.add_ore(rare_copper_ore, floor=3)
    fresh_vault.add_ore(legendary_mithril_ore, floor=7)
    assert fresh_vault.get_ore_count() == 2

    # Withdraw first ore (copper)
    ore = fresh_vault.withdraw_ore(0)
    assert ore is not None
    assert ore.ore_type == "copper"
    assert fresh_vault.get_ore_count() == 1

    # Withdraw second ore (mithril)
    ore = fresh_vault.withdraw_ore(0)
    assert ore is not None
    assert ore.ore_type == "mithril"
    assert fresh_vault.get_ore_count() == 0


@pytest.mark.unit
def test_vault_withdraw_invalid_index(fresh_vault, rare_copper_ore):
    """Test withdrawing with invalid index."""
    fresh_vault.add_ore(rare_copper_ore)

    # Try invalid indices
    assert fresh_vault.withdraw_ore(-1) is None
    assert fresh_vault.withdraw_ore(1) is None  # Out of range
    assert fresh_vault.withdraw_ore(999) is None

    # Ore should still be there
    assert fresh_vault.get_ore_count() == 1


# ============================================================================
# Vault Overflow Tests (FIFO)
# ============================================================================

@pytest.mark.unit
def test_vault_max_capacity(fresh_vault):
    """Test vault enforces max capacity with FIFO."""
    # Create 12 ores (exceeds max of 10)
    for i in range(12):
        ore = OreVein(
            ore_type=f"test_type_{i}",
            x=i,
            y=i,
            hardness=80,
            conductivity=80,
            malleability=80,
            purity=85,  # Legacy-worthy
            density=80
        )
        fresh_vault.add_ore(ore, floor=i)

    # Should have exactly 10 ores
    assert fresh_vault.get_ore_count() == MAX_VAULT_SIZE
    assert fresh_vault.is_full()

    # First two ores should be removed (FIFO)
    ores = fresh_vault.get_ores()
    assert ores[0].floor_found == 2  # First ore (floor 0, 1) removed
    assert ores[-1].floor_found == 11  # Last ore kept


@pytest.mark.unit
def test_vault_fifo_order(fresh_vault):
    """Test oldest ore is removed first when vault is full."""
    # Fill vault to max capacity
    for i in range(MAX_VAULT_SIZE):
        ore = OreVein(
            ore_type=f"ore_{i}",
            x=i, y=i,
            hardness=80, conductivity=80, malleability=80,
            purity=85, density=80
        )
        fresh_vault.add_ore(ore, floor=i)

    # Add one more ore - should push out oldest
    new_ore = OreVein(
        ore_type="new_ore",
        x=99, y=99,
        hardness=90, conductivity=90, malleability=90,
        purity=95, density=90
    )
    fresh_vault.add_ore(new_ore, floor=100)

    ores = fresh_vault.get_ores()
    assert ores[0].floor_found == 1  # ore_0 removed, ore_1 is now first
    assert ores[-1].ore_type == "new_ore"  # New ore added to end


# ============================================================================
# Victory/Defeat Tracking Tests
# ============================================================================

@pytest.mark.unit
def test_vault_record_pure_victory(fresh_vault):
    """Test recording a Pure Victory."""
    fresh_vault.record_run("pure", victory=True)

    assert fresh_vault.total_runs == 1
    assert fresh_vault.total_pure_victories == 1
    assert fresh_vault.total_legacy_victories == 0


@pytest.mark.unit
def test_vault_record_legacy_victory(fresh_vault):
    """Test recording a Legacy Victory."""
    fresh_vault.record_run("legacy", victory=True)

    assert fresh_vault.total_runs == 1
    assert fresh_vault.total_pure_victories == 0
    assert fresh_vault.total_legacy_victories == 1


@pytest.mark.unit
def test_vault_record_defeat(fresh_vault):
    """Test recording a defeat (no victory credit)."""
    fresh_vault.record_run("pure", victory=False)

    assert fresh_vault.total_runs == 1
    assert fresh_vault.total_pure_victories == 0
    assert fresh_vault.total_legacy_victories == 0


@pytest.mark.unit
def test_vault_multiple_runs(fresh_vault):
    """Test tracking multiple runs."""
    # 2 pure victories, 1 legacy victory, 5 defeats
    fresh_vault.record_run("pure", victory=True)
    fresh_vault.record_run("pure", victory=True)
    fresh_vault.record_run("legacy", victory=True)
    fresh_vault.record_run("pure", victory=False)
    fresh_vault.record_run("pure", victory=False)
    fresh_vault.record_run("legacy", victory=False)
    fresh_vault.record_run("legacy", victory=False)
    fresh_vault.record_run("pure", victory=False)

    assert fresh_vault.total_runs == 8
    assert fresh_vault.total_pure_victories == 2
    assert fresh_vault.total_legacy_victories == 1


# ============================================================================
# Inventory Integration Tests
# ============================================================================

@pytest.mark.unit
def test_vault_add_from_inventory(fresh_vault, rare_copper_ore, legendary_mithril_ore, common_iron_ore):
    """Test adding ores from player inventory."""
    # Simulate player inventory with mixed quality ores
    inventory = [rare_copper_ore, legendary_mithril_ore, common_iron_ore]

    added_count = fresh_vault.add_ores_from_inventory(inventory, current_floor=8)

    # Should add 2 legacy-worthy ores (copper and mithril), not iron
    assert added_count == 2
    assert fresh_vault.get_ore_count() == 2

    ores = fresh_vault.get_ores()
    ore_types = {ore.ore_type for ore in ores}
    assert "copper" in ore_types
    assert "mithril" in ore_types
    assert "iron" not in ore_types


@pytest.mark.unit
def test_vault_add_from_empty_inventory(fresh_vault):
    """Test adding from empty inventory."""
    added_count = fresh_vault.add_ores_from_inventory([], current_floor=1)

    assert added_count == 0
    assert fresh_vault.get_ore_count() == 0


@pytest.mark.unit
def test_vault_add_from_inventory_no_rare_ore(fresh_vault, common_iron_ore):
    """Test adding from inventory with no rare ore."""
    inventory = [common_iron_ore]

    added_count = fresh_vault.add_ores_from_inventory(inventory, current_floor=3)

    assert added_count == 0
    assert fresh_vault.get_ore_count() == 0


# ============================================================================
# Utility Method Tests
# ============================================================================

@pytest.mark.unit
def test_vault_get_best_ore(fresh_vault, rare_copper_ore, legendary_mithril_ore):
    """Test finding the highest purity ore."""
    fresh_vault.add_ore(rare_copper_ore)  # 90 purity
    fresh_vault.add_ore(legendary_mithril_ore)  # 99 purity

    best = fresh_vault.get_best_ore()
    assert best is not None
    assert best.ore_type == "mithril"
    assert best.purity == 99


@pytest.mark.unit
def test_vault_get_best_ore_empty(fresh_vault):
    """Test getting best ore from empty vault."""
    best = fresh_vault.get_best_ore()
    assert best is None


@pytest.mark.unit
def test_vault_get_ores_by_type(fresh_vault):
    """Test filtering ores by type."""
    # Add multiple copper and iron ores
    for i in range(3):
        copper = OreVein(
            ore_type="copper",
            x=i, y=i,
            hardness=85, conductivity=85, malleability=85,
            purity=90, density=85
        )
        fresh_vault.add_ore(copper)

    for i in range(2):
        iron = OreVein(
            ore_type="iron",
            x=i+10, y=i+10,
            hardness=80, conductivity=80, malleability=80,
            purity=85, density=80
        )
        fresh_vault.add_ore(iron)

    copper_ores = fresh_vault.get_ores_by_type("copper")
    iron_ores = fresh_vault.get_ores_by_type("iron")

    assert len(copper_ores) == 3
    assert len(iron_ores) == 2
    assert all(ore.ore_type == "copper" for ore in copper_ores)
    assert all(ore.ore_type == "iron" for ore in iron_ores)


@pytest.mark.unit
def test_vault_get_stats(fresh_vault, rare_copper_ore):
    """Test getting vault statistics."""
    fresh_vault.add_ore(rare_copper_ore)
    fresh_vault.record_run("pure", victory=True)
    fresh_vault.record_run("legacy", victory=True)

    stats = fresh_vault.get_stats()

    assert stats['total_runs'] == 2
    assert stats['total_pure_victories'] == 1
    assert stats['total_legacy_victories'] == 1
    assert stats['total_victories'] == 2
    assert stats['ores_in_vault'] == 1
    assert stats['vault_capacity'] == MAX_VAULT_SIZE
    assert stats['vault_full'] is False


@pytest.mark.unit
def test_vault_clear_vault(fresh_vault, rare_copper_ore, legendary_mithril_ore):
    """Test clearing all ores from vault."""
    fresh_vault.add_ore(rare_copper_ore)
    fresh_vault.add_ore(legendary_mithril_ore)
    assert fresh_vault.get_ore_count() == 2

    fresh_vault.clear_vault()

    assert fresh_vault.get_ore_count() == 0
    assert not fresh_vault.is_full()


# ============================================================================
# Persistence Tests
# ============================================================================

@pytest.mark.unit
def test_vault_save_and_load(temp_vault_path, rare_copper_ore, legendary_mithril_ore):
    """Test saving vault to disk and loading it back."""
    # Create vault, add data, and save
    vault1 = LegacyVault()
    vault1.add_ore(rare_copper_ore, floor=3)
    vault1.add_ore(legendary_mithril_ore, floor=7)
    vault1.record_run("pure", victory=True)
    vault1.save()

    # Create new vault instance and load
    vault2 = LegacyVault()

    # Verify data was restored
    assert vault2.get_ore_count() == 2
    assert vault2.total_runs == 1
    assert vault2.total_pure_victories == 1

    ores = vault2.get_ores()
    assert ores[0].ore_type == "copper"
    assert ores[1].ore_type == "mithril"


@pytest.mark.unit
def test_vault_persistence_path(temp_vault_path):
    """Test vault saves to correct location."""
    vault = LegacyVault()
    vault.save()

    assert temp_vault_path.exists()
    assert temp_vault_path.is_file()


@pytest.mark.unit
def test_vault_json_structure(temp_vault_path, rare_copper_ore):
    """Test vault JSON has correct structure."""
    vault = LegacyVault()
    vault.add_ore(rare_copper_ore, floor=5)
    vault.record_run("pure", victory=True)
    vault.save()

    # Read and parse JSON
    with open(temp_vault_path, 'r') as f:
        data = json.load(f)

    # Verify structure
    assert 'ores' in data
    assert 'total_pure_victories' in data
    assert 'total_legacy_victories' in data
    assert 'total_runs' in data
    assert 'vault_info' in data

    assert len(data['ores']) == 1
    assert data['total_runs'] == 1
    assert data['vault_info']['max_size'] == MAX_VAULT_SIZE
    assert data['vault_info']['purity_threshold'] == PURITY_THRESHOLD


@pytest.mark.unit
def test_vault_load_corrupted_file(temp_vault_path):
    """Test vault handles corrupted JSON gracefully."""
    # Write invalid JSON
    with open(temp_vault_path, 'w') as f:
        f.write("invalid json {{{")

    # Should create empty vault instead of crashing
    vault = LegacyVault()
    assert vault.get_ore_count() == 0
    assert vault.total_runs == 0


@pytest.mark.unit
def test_vault_load_missing_file(temp_vault_path):
    """Test vault creates new file if missing."""
    # Ensure file doesn't exist
    if temp_vault_path.exists():
        temp_vault_path.unlink()

    vault = LegacyVault()

    # Should create empty vault
    assert vault.get_ore_count() == 0
    assert temp_vault_path.exists()


# ============================================================================
# Singleton Pattern Tests
# ============================================================================

@pytest.mark.unit
def test_get_vault_singleton(temp_vault_path):
    """Test get_vault returns same instance."""
    reset_vault()  # Clear any existing instance

    vault1 = get_vault()
    vault2 = get_vault()

    assert vault1 is vault2  # Same object instance


@pytest.mark.unit
def test_reset_vault(temp_vault_path):
    """Test reset_vault clears singleton."""
    vault1 = get_vault()
    vault1.total_runs = 100

    reset_vault()
    vault2 = get_vault()

    # Should be new instance with fresh data
    assert vault1 is not vault2
    assert vault2.total_runs == 0


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.unit
def test_vault_add_ore_at_threshold(fresh_vault):
    """Test ore exactly at purity threshold is accepted."""
    ore = OreVein(
        ore_type="threshold_test",
        x=10, y=10,
        hardness=80, conductivity=80, malleability=80,
        purity=PURITY_THRESHOLD,  # Exactly 80
        density=80
    )

    added = fresh_vault.add_ore(ore)
    assert added is True
    assert fresh_vault.get_ore_count() == 1


@pytest.mark.unit
def test_vault_add_ore_below_threshold(fresh_vault):
    """Test ore just below threshold is rejected."""
    ore = OreVein(
        ore_type="below_test",
        x=10, y=10,
        hardness=80, conductivity=80, malleability=80,
        purity=PURITY_THRESHOLD - 1,  # 79
        density=80
    )

    added = fresh_vault.add_ore(ore)
    assert added is False
    assert fresh_vault.get_ore_count() == 0


@pytest.mark.unit
def test_vault_withdraw_from_empty(fresh_vault):
    """Test withdrawing from empty vault."""
    ore = fresh_vault.withdraw_ore(0)
    assert ore is None


@pytest.mark.unit
def test_vault_get_ores_returns_copy(fresh_vault, rare_copper_ore):
    """Test get_ores returns a copy, not reference."""
    fresh_vault.add_ore(rare_copper_ore)

    ores1 = fresh_vault.get_ores()
    ores2 = fresh_vault.get_ores()

    # Modifying returned list shouldn't affect vault
    ores1.clear()

    assert len(ores2) == 1  # Second call gets fresh copy
    assert fresh_vault.get_ore_count() == 1  # Vault unchanged
