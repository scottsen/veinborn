"""
Unit tests for Legacy Vault system.

Tests cover:
- Core vault operations (add, withdraw, persistence)
- Qualification filtering (purity >= 80)
- Capacity management (50 ore max)
- Sorting (best ore first)
- Error handling (corrupted files, invalid indices)
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from src.core.legacy_vault import LegacyVault, VaultOre
from src.core.entities import OreVein


class TestVaultOre:
    """Tests for VaultOre dataclass."""

    def test_vault_ore_creation(self):
        """VaultOre can be created with all required fields."""
        ore = VaultOre(
            ore_type="iron",
            purity=85,
            hardness=70,
            conductivity=60,
            malleability=75,
            density=80,
            run_number=1,
            date_acquired=datetime.now().isoformat()
        )

        assert ore.ore_type == "iron"
        assert ore.purity == 85
        assert ore.run_number == 1

    def test_get_quality_tier_legendary(self):
        """Purity 95+ is Legendary."""
        ore = VaultOre(
            ore_type="adamantite",
            purity=97,
            hardness=95,
            conductivity=95,
            malleability=95,
            density=95,
            run_number=1,
            date_acquired=datetime.now().isoformat()
        )

        assert ore.get_quality_tier() == "Legendary"

    def test_get_quality_tier_epic(self):
        """Purity 90-94 is Epic."""
        ore = VaultOre(
            ore_type="mithril",
            purity=92,
            hardness=90,
            conductivity=90,
            malleability=90,
            density=90,
            run_number=1,
            date_acquired=datetime.now().isoformat()
        )

        assert ore.get_quality_tier() == "Epic"

    def test_get_quality_tier_rare(self):
        """Purity 85-89 is Rare."""
        ore = VaultOre(
            ore_type="iron",
            purity=87,
            hardness=85,
            conductivity=85,
            malleability=85,
            density=85,
            run_number=1,
            date_acquired=datetime.now().isoformat()
        )

        assert ore.get_quality_tier() == "Rare"

    def test_get_quality_tier_common(self):
        """Purity 80-84 is Common."""
        ore = VaultOre(
            ore_type="copper",
            purity=82,
            hardness=80,
            conductivity=80,
            malleability=80,
            density=80,
            run_number=1,
            date_acquired=datetime.now().isoformat()
        )

        assert ore.get_quality_tier() == "Common"

    def test_vault_ore_str(self):
        """VaultOre has readable string representation."""
        ore = VaultOre(
            ore_type="gold",
            purity=90,
            hardness=85,
            conductivity=85,
            malleability=85,
            density=85,
            run_number=5,
            date_acquired=datetime.now().isoformat()
        )

        ore_str = str(ore)
        assert "Epic" in ore_str
        assert "Gold Ore" in ore_str or "gold" in ore_str.lower()
        assert "90" in ore_str


class TestLegacyVaultCore:
    """Core vault functionality tests."""

    def test_vault_creates_empty(self, tmp_path):
        """New vault starts empty when file doesn't exist."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        assert vault.count() == 0
        assert vault.get_ores() == []
        assert not vault.is_full()

    def test_vault_loads_from_disk(self, tmp_path):
        """Vault persists and reloads from disk."""
        vault_file = tmp_path / "vault.json"

        # Create vault and add ore
        vault1 = LegacyVault(vault_path=vault_file)
        ore = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        vault1.add_ore(ore, run_number=1)
        vault1.save()

        # Reload vault
        vault2 = LegacyVault(vault_path=vault_file)

        assert vault2.count() == 1
        ores = vault2.get_ores()
        assert ores[0].ore_type == "iron"
        assert ores[0].purity == 85

    def test_add_qualifying_ore(self, tmp_path):
        """Purity 80+ ore is added to vault."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="copper", purity=80, hardness=50, conductivity=50, malleability=50, density=50)
        result = vault.add_ore(ore, run_number=1)

        assert result is True
        assert vault.count() == 1

    def test_add_high_purity_ore(self, tmp_path):
        """Purity 90+ ore is added to vault."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="adamantite", purity=95, hardness=95, conductivity=95, malleability=95, density=95)
        result = vault.add_ore(ore, run_number=1)

        assert result is True
        assert vault.count() == 1
        ores = vault.get_ores()
        assert ores[0].purity == 95

    def test_reject_low_purity_ore(self, tmp_path):
        """Purity < 80 ore is rejected."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="copper", purity=79, hardness=50, conductivity=50, malleability=50, density=50)
        result = vault.add_ore(ore, run_number=1)

        assert result is False
        assert vault.count() == 0

    def test_reject_very_low_purity_ore(self, tmp_path):
        """Purity 50 ore is rejected."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="copper", purity=50, hardness=50, conductivity=50, malleability=50, density=50)
        result = vault.add_ore(ore, run_number=1)

        assert result is False
        assert vault.count() == 0

    def test_withdraw_ore_removes_from_vault(self, tmp_path):
        """Withdrawing ore decrements count."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore1 = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        ore2 = OreVein(ore_type="copper", purity=82, hardness=60, conductivity=55, malleability=65, density=70)
        vault.add_ore(ore1, run_number=1)
        vault.add_ore(ore2, run_number=1)

        assert vault.count() == 2

        withdrawn = vault.withdraw_ore(0)

        assert withdrawn is not None
        assert vault.count() == 1

    def test_withdraw_returns_correct_ore(self, tmp_path):
        """Withdrawn ore matches requested index."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="gold", purity=90, hardness=85, conductivity=85, malleability=85, density=85)
        vault.add_ore(ore, run_number=5)

        withdrawn = vault.withdraw_ore(0)

        assert withdrawn.ore_type == "gold"
        assert withdrawn.purity == 90
        assert withdrawn.run_number == 5

    def test_withdraw_invalid_index(self, tmp_path):
        """Withdrawing invalid index returns None."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        vault.add_ore(ore, run_number=1)

        # Try to withdraw index 5 (only has index 0)
        withdrawn = vault.withdraw_ore(5)

        assert withdrawn is None
        assert vault.count() == 1  # Ore still in vault

    def test_withdraw_negative_index(self, tmp_path):
        """Withdrawing negative index returns None."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        vault.add_ore(ore, run_number=1)

        withdrawn = vault.withdraw_ore(-1)

        assert withdrawn is None
        assert vault.count() == 1

    def test_ores_sorted_by_purity(self, tmp_path):
        """get_ores() returns highest purity first."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore1 = OreVein(ore_type="copper", purity=82, hardness=60, conductivity=55, malleability=65, density=70)
        ore2 = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        ore3 = OreVein(ore_type="gold", purity=90, hardness=85, conductivity=85, malleability=85, density=85)

        # Add in random order
        vault.add_ore(ore2, run_number=1)
        vault.add_ore(ore1, run_number=1)
        vault.add_ore(ore3, run_number=1)

        ores = vault.get_ores()

        assert ores[0].purity == 90  # Gold (highest)
        assert ores[1].purity == 85  # Iron
        assert ores[2].purity == 82  # Copper (lowest)

    def test_vault_max_capacity(self, tmp_path):
        """Vault enforces max capacity (50 ores)."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        # Add 50 ores
        for i in range(50):
            ore = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
            vault.add_ore(ore, run_number=1)

        assert vault.count() == 50
        assert vault.is_full()

    def test_vault_replaces_lowest_when_full(self, tmp_path):
        """When vault is full, lowest purity ore is removed."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        # Fill vault with purity 80 ores
        for i in range(50):
            ore = OreVein(ore_type="copper", purity=80, hardness=60, conductivity=55, malleability=65, density=70)
            vault.add_ore(ore, run_number=1)

        assert vault.count() == 50

        # Add purity 90 ore (better)
        high_quality_ore = OreVein(ore_type="gold", purity=90, hardness=85, conductivity=85, malleability=85, density=85)
        vault.add_ore(high_quality_ore, run_number=2)

        # Still 50 ores, but now includes the purity 90
        assert vault.count() == 50
        ores = vault.get_ores()
        assert ores[0].purity == 90  # Best ore is now the gold

    def test_clear_empties_vault(self, tmp_path):
        """clear() removes all ores and saves."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        vault.add_ore(ore, run_number=1)
        vault.save()

        vault.clear()

        assert vault.count() == 0
        assert vault_file.exists()  # File still exists, just empty


class TestVaultPersistence:
    """Tests for vault save/load operations."""

    def test_save_creates_file(self, tmp_path):
        """save() creates JSON file."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        vault.add_ore(ore, run_number=1)
        vault.save()

        assert vault_file.exists()

    def test_save_creates_directory(self, tmp_path):
        """save() creates parent directories if needed."""
        vault_file = tmp_path / "nested" / "dir" / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        vault.add_ore(ore, run_number=1)
        vault.save()

        assert vault_file.exists()
        assert vault_file.parent.exists()

    def test_save_overwrites_existing(self, tmp_path):
        """save() overwrites existing vault file."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        # First save
        ore1 = OreVein(ore_type="copper", purity=82, hardness=60, conductivity=55, malleability=65, density=70)
        vault.add_ore(ore1, run_number=1)
        vault.save()

        # Second save (overwrites)
        ore2 = OreVein(ore_type="gold", purity=90, hardness=85, conductivity=85, malleability=85, density=85)
        vault.add_ore(ore2, run_number=2)
        vault.save()

        # Reload and verify
        vault2 = LegacyVault(vault_path=vault_file)
        assert vault2.count() == 2

    def test_load_handles_missing_file(self, tmp_path):
        """load() gracefully handles missing file (first run)."""
        vault_file = tmp_path / "nonexistent.json"
        vault = LegacyVault(vault_path=vault_file)

        assert vault.count() == 0
        assert vault.get_ores() == []

    def test_load_handles_corrupted_file(self, tmp_path):
        """load() handles corrupted JSON by backing up and starting fresh."""
        vault_file = tmp_path / "vault.json"

        # Create corrupted file
        with open(vault_file, 'w') as f:
            f.write("{ invalid json }")

        vault = LegacyVault(vault_path=vault_file)

        # Should start with empty vault
        assert vault.count() == 0

        # Backup should exist
        backup_file = tmp_path / "vault.json.backup"
        assert backup_file.exists()

    def test_persistence_round_trip(self, tmp_path):
        """Multiple save/load cycles preserve data."""
        vault_file = tmp_path / "vault.json"

        # Create and save
        vault1 = LegacyVault(vault_path=vault_file)
        ore1 = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        ore2 = OreVein(ore_type="gold", purity=90, hardness=85, conductivity=85, malleability=85, density=85)
        vault1.add_ore(ore1, run_number=1)
        vault1.add_ore(ore2, run_number=2)
        vault1.save()

        # Reload
        vault2 = LegacyVault(vault_path=vault_file)
        assert vault2.count() == 2

        # Add more and save
        ore3 = OreVein(ore_type="adamantite", purity=95, hardness=95, conductivity=95, malleability=95, density=95)
        vault2.add_ore(ore3, run_number=3)
        vault2.save()

        # Reload again
        vault3 = LegacyVault(vault_path=vault_file)
        assert vault3.count() == 3
        ores = vault3.get_ores()
        assert ores[0].purity == 95  # Adamantite


class TestVaultStats:
    """Tests for vault statistics."""

    def test_get_stats_empty_vault(self, tmp_path):
        """get_stats() returns zeros for empty vault."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        stats = vault.get_stats()

        assert stats["count"] == 0
        assert stats["best_purity"] == 0
        assert stats["avg_purity"] == 0
        assert stats["is_full"] is False

    def test_get_stats_with_ores(self, tmp_path):
        """get_stats() returns correct statistics."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore1 = OreVein(ore_type="copper", purity=80, hardness=60, conductivity=55, malleability=65, density=70)
        ore2 = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        ore3 = OreVein(ore_type="gold", purity=90, hardness=85, conductivity=85, malleability=85, density=85)

        vault.add_ore(ore1, run_number=1)
        vault.add_ore(ore2, run_number=1)
        vault.add_ore(ore3, run_number=1)

        stats = vault.get_stats()

        assert stats["count"] == 3
        assert stats["best_purity"] == 90
        assert stats["avg_purity"] == 85  # (80 + 85 + 90) / 3
        assert stats["is_full"] is False


class TestVaultEdgeCases:
    """Edge case tests."""

    def test_withdraw_from_empty_vault(self, tmp_path):
        """Withdrawing from empty vault returns None."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        withdrawn = vault.withdraw_ore(0)

        assert withdrawn is None

    def test_add_ore_with_exact_min_purity(self, tmp_path):
        """Ore with exactly purity 80 qualifies."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="copper", purity=80, hardness=60, conductivity=55, malleability=65, density=70)
        result = vault.add_ore(ore, run_number=1)

        assert result is True
        assert vault.count() == 1

    def test_add_ore_with_purity_79(self, tmp_path):
        """Ore with purity 79 does not qualify (just below threshold)."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(ore_type="copper", purity=79, hardness=60, conductivity=55, malleability=65, density=70)
        result = vault.add_ore(ore, run_number=1)

        assert result is False
        assert vault.count() == 0

    def test_multiple_ores_same_purity(self, tmp_path):
        """Multiple ores with same purity are all stored."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore1 = OreVein(ore_type="iron", purity=85, hardness=70, conductivity=60, malleability=75, density=80)
        ore2 = OreVein(ore_type="copper", purity=85, hardness=65, conductivity=58, malleability=72, density=78)
        ore3 = OreVein(ore_type="gold", purity=85, hardness=75, conductivity=62, malleability=77, density=82)

        vault.add_ore(ore1, run_number=1)
        vault.add_ore(ore2, run_number=1)
        vault.add_ore(ore3, run_number=1)

        assert vault.count() == 3

    def test_ore_properties_preserved(self, tmp_path):
        """All ore properties are preserved through save/load."""
        vault_file = tmp_path / "vault.json"
        vault = LegacyVault(vault_path=vault_file)

        ore = OreVein(
            ore_type="adamantite",
            purity=97,
            hardness=95,
            conductivity=93,
            malleability=96,
            density=94
        )
        vault.add_ore(ore, run_number=42)
        vault.save()

        # Reload and verify
        vault2 = LegacyVault(vault_path=vault_file)
        ores = vault2.get_ores()

        assert ores[0].ore_type == "adamantite"
        assert ores[0].purity == 97
        assert ores[0].hardness == 95
        assert ores[0].conductivity == 93
        assert ores[0].malleability == 96
        assert ores[0].density == 94
        assert ores[0].run_number == 42
