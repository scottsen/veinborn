"""
Legacy Vault System - Meta-progression for Brogue.

Saves rare ore (80+ purity) when you die, allowing you to start future runs
with a head-start. This creates two victory paths:
- Pure Victory: No Legacy gear used (street cred!)
- Legacy Victory: Used vault ore (accessibility)

Design Goals:
- Reward hunting for perfect ore spawns
- Add meta-progression without breaking challenge
- Track both victory types separately
- Persist across game sessions
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path


# Constants
LEGACY_VAULT_PATH = Path.home() / ".brogue" / "legacy_vault.json"
PURITY_THRESHOLD = 80
MAX_VAULT_SIZE = 50  # Increased from 10 to 50 per requirements


@dataclass
class LegacyOre:
    """
    A single ore stored in the Legacy Vault.

    Contains all properties needed to recreate the ore in a new run.
    """
    ore_type: str
    hardness: int
    conductivity: int
    malleability: int
    purity: int
    density: int
    floor_found: int = 1
    timestamp: str = ""  # When it was added to vault

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegacyOre':
        """Create LegacyOre from dictionary."""
        return cls(**data)

    @classmethod
    def from_ore_vein(cls, ore_vein, floor: int = 1) -> 'LegacyOre':
        """Create LegacyOre from an OreVein entity."""
        from datetime import datetime

        return cls(
            ore_type=ore_vein.ore_type,
            hardness=ore_vein.hardness,
            conductivity=ore_vein.conductivity,
            malleability=ore_vein.malleability,
            purity=ore_vein.purity,
            density=ore_vein.density,
            floor_found=floor,
            timestamp=datetime.now().isoformat()
        )

    def is_legacy_worthy(self) -> bool:
        """Check if this ore qualifies for Legacy Vault (80+ purity)."""
        return self.purity >= PURITY_THRESHOLD

    def get_quality_tier(self) -> str:
        """Get quality tier name based on purity."""
        if self.purity >= 96:
            return "Legendary"
        elif self.purity >= 86:
            return "Epic"
        elif self.purity >= 71:
            return "Rare"
        elif self.purity >= 51:
            return "Uncommon"
        elif self.purity >= 31:
            return "Common"
        else:
            return "Poor"


@dataclass
class RunStats:
    """Statistics for a single run."""
    run_type: str  # "pure" or "legacy"
    deepest_floor: int
    ores_mined: int
    items_crafted: int
    monsters_killed: int
    ended_in_victory: bool


class LegacyVault:
    """
    Manages the Legacy Vault - persistent storage of rare ore.

    Responsibilities:
    - Load/save vault from disk
    - Add ore on death (if purity >= 80)
    - Withdraw ore at run start
    - Track Pure vs Legacy runs
    - Enforce max vault size (FIFO)
    """

    def __init__(self):
        """Initialize Legacy Vault."""
        self.ores: List[LegacyOre] = []
        self.total_pure_victories: int = 0
        self.total_legacy_victories: int = 0
        self.total_runs: int = 0
        self.load()

    def load(self) -> None:
        """Load vault from disk."""
        if not LEGACY_VAULT_PATH.exists():
            # Create directory if it doesn't exist
            LEGACY_VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.save()  # Create empty vault file
            return

        try:
            with open(LEGACY_VAULT_PATH, 'r') as f:
                data = json.load(f)

            # Load ores
            self.ores = [LegacyOre.from_dict(ore_data) for ore_data in data.get('ores', [])]

            # Load stats
            self.total_pure_victories = data.get('total_pure_victories', 0)
            self.total_legacy_victories = data.get('total_legacy_victories', 0)
            self.total_runs = data.get('total_runs', 0)

        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Warning: Failed to load legacy vault: {e}")
            print("Creating new vault...")
            self.ores = []
            self.total_pure_victories = 0
            self.total_legacy_victories = 0
            self.total_runs = 0

    def save(self) -> None:
        """Save vault to disk."""
        # Ensure directory exists
        LEGACY_VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'ores': [ore.to_dict() for ore in self.ores],
            'total_pure_victories': self.total_pure_victories,
            'total_legacy_victories': self.total_legacy_victories,
            'total_runs': self.total_runs,
            'vault_info': {
                'max_size': MAX_VAULT_SIZE,
                'purity_threshold': PURITY_THRESHOLD,
                'current_size': len(self.ores)
            }
        }

        with open(LEGACY_VAULT_PATH, 'w') as f:
            json.dump(data, f, indent=2)

    def add_ore(self, ore_vein, floor: int = 1) -> bool:
        """
        Add ore to vault if it qualifies (purity >= 80).

        Returns:
            True if ore was added, False if it didn't qualify
        """
        legacy_ore = LegacyOre.from_ore_vein(ore_vein, floor)

        if not legacy_ore.is_legacy_worthy():
            return False

        # Add to vault
        self.ores.append(legacy_ore)

        # Enforce max size (FIFO - remove oldest)
        if len(self.ores) > MAX_VAULT_SIZE:
            self.ores.pop(0)  # Remove oldest ore

        self.save()
        return True

    def add_ores_from_inventory(self, inventory: List, current_floor: int = 1) -> int:
        """
        Add all legacy-worthy ores from inventory (called on death).

        Args:
            inventory: List of items in player inventory
            current_floor: Current floor number

        Returns:
            Number of ores added to vault
        """
        added_count = 0

        for item in inventory:
            # Check if item is an ore
            if hasattr(item, 'ore_type') and hasattr(item, 'purity'):
                if item.purity >= PURITY_THRESHOLD:
                    self.add_ore(item, current_floor)
                    added_count += 1

        return added_count

    def withdraw_ore(self, index: int) -> Optional[LegacyOre]:
        """
        Withdraw ore from vault by index.

        Args:
            index: Index of ore to withdraw (0-based)

        Returns:
            LegacyOre if valid index, None otherwise
        """
        if 0 <= index < len(self.ores):
            ore = self.ores.pop(index)
            self.save()
            return ore
        return None

    def get_ores(self) -> List[LegacyOre]:
        """Get all ores in vault, sorted by purity (best first)."""
        return sorted(self.ores, key=lambda ore: ore.purity, reverse=True)

    def get_ore_count(self) -> int:
        """Get number of ores in vault."""
        return len(self.ores)

    def is_full(self) -> bool:
        """Check if vault is at max capacity."""
        return len(self.ores) >= MAX_VAULT_SIZE

    def record_run(self, run_type: str, victory: bool) -> None:
        """
        Record a completed run.

        Args:
            run_type: "pure" or "legacy"
            victory: True if run ended in victory
        """
        self.total_runs += 1

        if victory:
            if run_type == "pure":
                self.total_pure_victories += 1
            elif run_type == "legacy":
                self.total_legacy_victories += 1

        self.save()

    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics."""
        return {
            'total_runs': self.total_runs,
            'total_pure_victories': self.total_pure_victories,
            'total_legacy_victories': self.total_legacy_victories,
            'total_victories': self.total_pure_victories + self.total_legacy_victories,
            'ores_in_vault': len(self.ores),
            'vault_capacity': MAX_VAULT_SIZE,
            'vault_full': self.is_full()
        }

    def clear_vault(self) -> None:
        """Clear all ores from vault (debug/testing only)."""
        self.ores = []
        self.save()

    def get_best_ore(self) -> Optional[LegacyOre]:
        """Get the highest purity ore in vault."""
        if not self.ores:
            return None
        return max(self.ores, key=lambda ore: ore.purity)

    def get_ores_by_type(self, ore_type: str) -> List[LegacyOre]:
        """Get all ores of a specific type."""
        return [ore for ore in self.ores if ore.ore_type == ore_type]


# Global vault instance
_vault_instance: Optional[LegacyVault] = None


def get_vault() -> LegacyVault:
    """Get the global Legacy Vault instance (singleton pattern)."""
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = LegacyVault()
    return _vault_instance


def reset_vault() -> None:
    """Reset the global vault instance (for testing)."""
    global _vault_instance
    _vault_instance = None
