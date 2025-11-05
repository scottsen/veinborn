"""
Loot generation system - NetHack-style drops from monsters.

Handles:
- Loading item definitions from YAML
- Loading loot tables from YAML
- Generating random loot based on monster type
- Creating item entities for dropped loot

Design Goals:
- Data-driven (no hardcoded loot tables)
- NetHack feel (diverse items, exciting drops)
- Balanced reward structure
- Easy modding (edit YAML files)
"""

import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base.entity import Entity, EntityType
from .rng import GameRNG

logger = logging.getLogger(__name__)


class LootGenerator:
    """
    Generates loot drops from monsters.

    PERFORMANCE: Singleton pattern - YAML loaded once and cached.

    Usage:
        generator = LootGenerator.get_instance()
        items = generator.generate_loot("goblin", floor_number=1)
    """

    _instance: Optional['LootGenerator'] = None

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize loot generator.

        PERFORMANCE: Use get_instance() instead of direct instantiation
        to reuse cached YAML data.

        Args:
            data_dir: Path to data directory (defaults to project data/)
        """
        if data_dir is None:
            # Default to project data directory
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data"

        self.data_dir = Path(data_dir)

        # PERFORMANCE FIX: Load YAML once and cache
        # Previously: Created new LootGenerator for every loot drop (24x in 3 games)
        # Now: Singleton pattern - load once, reuse forever
        self.items = self._load_items()
        self.loot_tables = self._load_loot_tables()

        logger.info(
            f"LootGenerator initialized",
            extra={
                'num_items': self._count_items(),
                'num_loot_tables': len(self.loot_tables),
            }
        )

    @classmethod
    def get_instance(cls, data_dir: Optional[Path] = None) -> 'LootGenerator':
        """
        Get or create singleton LootGenerator instance.

        PERFORMANCE: Singleton ensures YAML is loaded once, not every loot drop.

        Args:
            data_dir: Path to data directory (only used on first call)

        Returns:
            Cached LootGenerator instance
        """
        if cls._instance is None:
            cls._instance = cls(data_dir)
            logger.debug("Created singleton LootGenerator instance")
        return cls._instance

    def _load_items(self) -> Dict[str, Dict[str, Any]]:
        """Load all item definitions from items.yaml."""
        items_file = self.data_dir / "entities" / "items.yaml"

        if not items_file.exists():
            logger.warning(f"Items file not found: {items_file}")
            return {}

        with open(items_file, 'r') as f:
            data = yaml.safe_load(f)

        # Flatten all item categories into single dict
        # {item_id: item_definition}
        items = {}

        # Extract items from each category
        for category in ['weapons', 'armor', 'potions', 'scrolls', 'food', 'rings', 'currency']:
            if category in data:
                for item_id, item_def in data[category].items():
                    items[item_id] = item_def
                    items[item_id]['category'] = category

        logger.info(f"Loaded {len(items)} item definitions")
        return items

    def _load_loot_tables(self) -> Dict[str, Dict[str, Any]]:
        """Load all loot tables from loot_tables.yaml."""
        loot_file = self.data_dir / "balance" / "loot_tables.yaml"

        if not loot_file.exists():
            logger.warning(f"Loot tables file not found: {loot_file}")
            return {}

        with open(loot_file, 'r') as f:
            data = yaml.safe_load(f)

        # Remove schema_version from tables
        tables = {k: v for k, v in data.items() if k != 'schema_version'}

        logger.info(f"Loaded {len(tables)} loot tables")
        return tables

    def _count_items(self) -> int:
        """Count total items across all categories."""
        return len(self.items)

    def generate_loot(
        self,
        monster_type: str,
        floor_number: int = 1,
        rng: Optional[GameRNG] = None
    ) -> List[Entity]:
        """
        Generate loot drops for a killed monster.

        Args:
            monster_type: Type of monster (goblin, orc, troll)
            floor_number: Dungeon floor (for future scaling)
            rng: Random number generator (uses default if None)

        Returns:
            List of item entities to drop
        """
        if rng is None:
            rng = GameRNG()

        # Get loot table for this monster
        loot_table = self.loot_tables.get(monster_type)
        if not loot_table:
            logger.warning(
                f"No loot table found for monster type: {monster_type}",
                extra={'monster_type': monster_type}
            )
            return []

        dropped_items = []

        # Roll for each loot category (gold, weapons, armor, etc.)
        for category, category_data in loot_table.items():
            if category == 'description':
                continue  # Skip description field

            # Check if this category drops (based on drop_chance)
            drop_chance = category_data.get('drop_chance', 0.0)
            if not rng.random() < drop_chance:
                continue  # This category didn't drop

            # Select which item from this category
            item_id = self._select_item_from_category(category_data, rng)
            if not item_id:
                continue

            # Create the item entity
            item_entity = self._create_item_entity(item_id, category_data, rng)
            if item_entity:
                dropped_items.append(item_entity)
                logger.debug(
                    f"Generated loot drop",
                    extra={
                        'monster_type': monster_type,
                        'item_id': item_id,
                        'category': category,
                    }
                )

        logger.info(
            f"Generated loot for {monster_type}",
            extra={
                'monster_type': monster_type,
                'floor_number': floor_number,
                'num_items_dropped': len(dropped_items),
            }
        )

        return dropped_items

    def _select_item_from_category(
        self,
        category_data: Dict[str, Any],
        rng: GameRNG
    ) -> Optional[str]:
        """
        Select a specific item from a category based on weights.

        Args:
            category_data: Category data with items and weights
            rng: Random number generator

        Returns:
            Item ID or None
        """
        items = category_data.get('items', [])
        if not items:
            return None

        # Build weighted selection
        total_weight = sum(item['weight'] for item in items)
        roll = rng.random() * total_weight

        current = 0
        for item in items:
            current += item['weight']
            if roll <= current:
                return item['id']

        # Fallback to last item if rounding issues
        return items[-1]['id']

    def _create_item_entity(
        self,
        item_id: str,
        category_data: Dict[str, Any],
        rng: GameRNG
    ) -> Optional[Entity]:
        """
        Create an Entity object for a dropped item.

        Args:
            item_id: Item ID from items.yaml
            category_data: Category data (may have amount_range for gold)
            rng: Random number generator

        Returns:
            Entity object or None
        """
        item_def = self.items.get(item_id)
        if not item_def:
            logger.warning(f"Unknown item ID: {item_id}")
            return None

        # Create base entity
        entity = Entity(
            entity_type=EntityType.ITEM,
            name=item_def.get('display_name', item_def.get('name', 'Unknown Item')),
            content_id=item_id,
            # Items start with no position (will be placed on ground when dropped)
            x=None,
            y=None,
            # Items don't have combat stats on the entity itself
            hp=0,
            max_hp=0,
            attack=0,
            defense=0,
        )

        # Store item-specific data in stats dict
        entity.set_stat('item_type', item_def.get('item_type', 'misc'))
        entity.set_stat('description', item_def.get('description', ''))
        entity.set_stat('symbol', item_def.get('symbol', '?'))
        entity.set_stat('color', item_def.get('color', 'white'))
        entity.set_stat('weight', item_def.get('weight', 1))
        entity.set_stat('value', item_def.get('value', 0))

        # Store item stats (attack_bonus, defense_bonus, heal_amount, etc.)
        if 'stats' in item_def:
            for stat_name, stat_value in item_def['stats'].items():
                entity.set_stat(stat_name, stat_value)

        # Store effect type if present
        if 'effect' in item_def:
            entity.set_stat('effect', item_def['effect'])

        # Store tags
        if 'tags' in item_def:
            entity.set_stat('tags', item_def['tags'])

        # Handle gold amount randomization
        if item_def.get('item_type') == 'gold':
            # Check if category_data has amount_range for this item
            amount_range = None
            for item_data in category_data.get('items', []):
                if item_data['id'] == item_id:
                    amount_range = item_data.get('amount_range')
                    break

            if amount_range:
                min_gold, max_gold = amount_range
                gold_amount = rng.randint(min_gold, max_gold)
            else:
                # Fallback to item definition
                gold_amount = item_def.get('stats', {}).get('gold_amount', 10)

            entity.set_stat('gold_amount', gold_amount)
            # Update display name with amount
            entity.name = f"{gold_amount} gold coins"

        logger.debug(
            f"Created item entity",
            extra={
                'item_id': item_id,
                'item_name': entity.name,
                'item_type': entity.get_stat('item_type'),
            }
        )

        return entity

    def get_item_info(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item definition by ID (for debugging/testing)."""
        return self.items.get(item_id)

    def get_loot_table(self, monster_type: str) -> Optional[Dict[str, Any]]:
        """Get loot table for monster type (for debugging/testing)."""
        return self.loot_tables.get(monster_type)
