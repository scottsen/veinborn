"""
Legacy Vault System

Preserves high-quality ore (purity 80+) across runs for meta-progression.

Features:
- Persistent storage of rare ore from previous runs
- Automatic qualification filtering (purity >= 80)
- Max capacity enforcement (50 ores)
- Quality-based sorting (best ore first)
- JSON persistence to ~/.brogue/legacy_vault.json

Design Philosophy:
- Pure Victory: No vault ore used (prestige/challenge)
- Legacy Victory: Use 1 vault ore for easier start (accessibility)
- Both paths are valid!

Usage:
    from src.core.legacy_vault import LegacyVault, VaultOre

    # On player death
    vault = LegacyVault()
    for ore in player_inventory:
        if ore.purity >= 80:
            vault.add_ore(ore, run_number=1)
    vault.save()

    # On game start
    vault = LegacyVault()
    if vault.count() > 0:
        # Show UI to select ore
        ore = vault.withdraw_ore(index=0)
        vault.save()
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, TYPE_CHECKING
from pathlib import Path
import json
import logging
from datetime import datetime

if TYPE_CHECKING:
    from .entities import OreVein

logger = logging.getLogger(__name__)


@dataclass
class VaultOre:
    """
    Ore stored in Legacy Vault.

    Represents a preserved ore from a previous run that can be
    withdrawn at the start of a new run.

    All OreVein properties are preserved:
    - ore_type: Base material (copper, iron, mithril, adamantite)
    - purity: Quality multiplier (80-100 for vault-worthy ore)
    - hardness: Weapon damage / Armor defense
    - conductivity: Magic power / Spell efficiency
    - malleability: Durability / Repair ease
    - density: Weight / Encumbrance

    Metadata:
    - run_number: Which run this ore came from
    - date_acquired: When it was added to vault (ISO format)
    """

    # Ore properties (from OreVein)
    ore_type: str
    purity: int
    hardness: int
    conductivity: int
    malleability: int
    density: int

    # Metadata
    run_number: int
    date_acquired: str

    def get_quality_tier(self) -> str:
        """
        Get quality tier based on purity.

        Returns:
            Quality tier string (e.g., "Legendary", "Epic", "Rare")
        """
        if self.purity >= 95:
            return "Legendary"
        elif self.purity >= 90:
            return "Epic"
        elif self.purity >= 85:
            return "Rare"
        else:
            return "Common"

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.get_quality_tier()} {self.ore_type.title()} Ore (Purity: {self.purity})"


class LegacyVault:
    """
    Manages persistent Legacy Vault storage.

    The Legacy Vault preserves high-quality ore (purity 80+) from previous
    runs, allowing players to withdraw 1 ore at the start of a new run.

    Features:
    - Automatic qualification filtering (purity >= 80)
    - Max capacity enforcement (50 ores)
    - Quality-based sorting (best ore first)
    - Atomic save operations
    - Corruption recovery (backup and recreate)

    Design:
    - JSON persistence for human-readable debugging
    - Follows SaveSystem patterns from save_load.py
    - Path.home() for platform-independent paths
    - Graceful handling of missing/corrupted files

    Example:
        >>> vault = LegacyVault()
        >>> vault.add_ore(ore, run_number=1)
        True
        >>> vault.save()
        >>> vault.count()
        1
    """

    MIN_PURITY = 80  # Ore must have purity >= 80 to qualify
    MAX_CAPACITY = 50  # Maximum ores to prevent infinite hoarding

    def __init__(self, vault_path: Optional[Path] = None):
        """
        Initialize Legacy Vault.

        Args:
            vault_path: Custom path for testing (default: ~/.brogue/legacy_vault.json)
        """
        if vault_path is None:
            vault_path = Path.home() / ".brogue" / "legacy_vault.json"

        self.vault_path = Path(vault_path)
        self.ores: List[VaultOre] = []
        self.load()

        logger.debug(f"LegacyVault initialized: {self.vault_path}, {len(self.ores)} ores loaded")

    def load(self) -> None:
        """
        Load vault from disk.

        Creates empty vault if file doesn't exist (first run).
        Handles corrupted files by backing up and starting fresh.
        """
        if not self.vault_path.exists():
            logger.info(f"No vault file found at {self.vault_path}, starting with empty vault")
            self.ores = []
            return

        try:
            with open(self.vault_path, 'r') as f:
                data = json.load(f)

            # Deserialize ores
            self.ores = [VaultOre(**ore_dict) for ore_dict in data.get("ores", [])]

            logger.info(f"Loaded {len(self.ores)} ores from vault")

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # Corrupted vault, backup and start fresh
            logger.error(f"Corrupted vault file: {e}")

            if self.vault_path.exists():
                backup_path = self.vault_path.with_suffix('.json.backup')
                self.vault_path.rename(backup_path)
                logger.warning(f"Backed up corrupted vault to {backup_path}")

            self.ores = []
            logger.info("Started fresh vault after corruption")

    def save(self) -> None:
        """
        Persist vault to disk.

        Uses atomic save operation (temp file → rename) to prevent
        corruption if save is interrupted.
        """
        # Ensure directory exists
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize data
        data = {
            "version": "1.0",
            "ores": [asdict(ore) for ore in self.ores]
        }

        # Atomic save (write to temp, then rename)
        temp_path = self.vault_path.with_suffix('.tmp')

        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Atomic rename
            temp_path.rename(self.vault_path)

            logger.info(f"Saved {len(self.ores)} ores to vault")

        except IOError as e:
            logger.error(f"Failed to save vault: {e}")
            if temp_path.exists():
                temp_path.unlink()  # Clean up temp file

    def add_ore(self, ore: 'OreVein', run_number: int) -> bool:
        """
        Add ore to vault if it qualifies (purity >= 80).

        If vault is full, removes the lowest purity ore to make room.
        This ensures players never lose their best ore.

        Args:
            ore: OreVein entity from game
            run_number: Which run this ore came from (for display)

        Returns:
            True if added, False if rejected (purity too low)

        Example:
            >>> vault.add_ore(ore, run_number=5)
            True  # Added to vault
        """
        # Check if ore qualifies
        if ore.purity < self.MIN_PURITY:
            logger.debug(f"Ore rejected: purity {ore.purity} < {self.MIN_PURITY}")
            return False

        # If vault is full, remove lowest purity ore
        if self.is_full():
            self.ores.sort(key=lambda o: o.purity)
            removed = self.ores.pop(0)
            logger.info(f"Vault full, removed lowest purity ore: {removed.ore_type} (purity {removed.purity})")

        # Create vault ore from OreVein
        vault_ore = VaultOre(
            ore_type=ore.ore_type,
            purity=ore.purity,
            hardness=ore.hardness,
            conductivity=ore.conductivity,
            malleability=ore.malleability,
            density=ore.density,
            run_number=run_number,
            date_acquired=datetime.now().isoformat()
        )

        self.ores.append(vault_ore)
        logger.info(f"Added to vault: {vault_ore}")

        return True

    def withdraw_ore(self, index: int) -> Optional[VaultOre]:
        """
        Remove and return ore at index.

        Caller is responsible for calling save() after withdrawal.

        Args:
            index: Index in sorted ore list (0 = best ore)

        Returns:
            VaultOre if valid index, None otherwise

        Example:
            >>> ore = vault.withdraw_ore(0)  # Withdraw best ore
            >>> vault.save()  # Persist withdrawal
        """
        if 0 <= index < len(self.ores):
            ore = self.ores.pop(index)
            logger.info(f"Withdrew from vault: {ore}")
            return ore

        logger.warning(f"Invalid withdrawal index: {index} (vault has {len(self.ores)} ores)")
        return None

    def get_ores(self) -> List[VaultOre]:
        """
        Get all vault ores, sorted by purity descending.

        Returns:
            List of VaultOre (best ore first)

        Example:
            >>> ores = vault.get_ores()
            >>> print(f"Best ore: {ores[0]}")
        """
        return sorted(self.ores, key=lambda o: o.purity, reverse=True)

    def count(self) -> int:
        """
        Number of ores in vault.

        Returns:
            Count of ores
        """
        return len(self.ores)

    def is_full(self) -> bool:
        """
        Check if vault is at capacity.

        Returns:
            True if vault has MAX_CAPACITY ores
        """
        return len(self.ores) >= self.MAX_CAPACITY

    def clear(self) -> None:
        """
        Empty vault (for testing or player request).

        Automatically saves after clearing.
        """
        self.ores.clear()
        self.save()
        logger.info("Vault cleared")

    def get_stats(self) -> dict:
        """
        Get vault statistics for display.

        Returns:
            Dict with vault stats (count, best_purity, avg_purity, etc.)
        """
        if not self.ores:
            return {
                "count": 0,
                "best_purity": 0,
                "avg_purity": 0,
                "is_full": False,
            }

        purities = [ore.purity for ore in self.ores]

        return {
            "count": len(self.ores),
            "best_purity": max(purities),
            "avg_purity": sum(purities) // len(purities),
            "is_full": self.is_full(),
        }
