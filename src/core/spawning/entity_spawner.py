"""
EntitySpawner - handles all entity creation and placement.

Responsibilities:
- Spawn monsters based on floor configuration
- Spawn ore veins based on floor configuration
- Handle weighted random selection
- Create entities using EntityLoader (data-driven)

This class extracts spawning logic from the Game class,
following Single Responsibility Principle.

Phase 3: Now uses EntityLoader for data-driven entity creation.
"""

import logging
from typing import List, Dict

from ..config import GameConfig
from ..entity_loader import EntityLoader
from ..rng import GameRNG
from ..entities import Monster, OreVein, Forge
from ..world import Map
from ..exceptions import ContentValidationError

logger = logging.getLogger(__name__)


class EntitySpawner:
    """
    Handles entity spawning for the game.

    Design principles:
    - Single responsibility (spawning only)
    - Configuration-driven (uses GameConfig)
    - Testable in isolation (no Game dependencies)
    - Reusable helper methods
    """

    def __init__(self, config: GameConfig, entity_loader: EntityLoader):
        """
        Initialize spawner with configuration.

        Args:
            config: Game configuration for spawn rules
            entity_loader: EntityLoader for creating entities from YAML
        """
        self.config = config
        self.entity_loader = entity_loader
        logger.debug("EntitySpawner initialized")

    def spawn_monsters_for_floor(self, floor: int, dungeon_map: Map) -> List[Monster]:
        """
        Spawn monsters for a given floor.

        Args:
            floor: Floor number (1-based)
            dungeon_map: Map to spawn monsters in

        Returns:
            List of spawned Monster entities
        """
        # Get spawn configuration
        monster_count = self.config.get_monster_count_for_floor(floor)
        spawn_weights = self.config.get_monster_spawn_weights(floor)

        # Find positions
        positions = dungeon_map.find_monster_positions(monster_count)

        monsters = []
        for x, y in positions:
            # Choose monster type based on weights
            monster_type = self._weighted_random_choice(spawn_weights)
            monster = self.entity_loader.create_monster(monster_type, x, y)
            monsters.append(monster)

            logger.debug(
                f"Spawned {monster.name} at ({x}, {y}) "
                f"[floor {floor}, type: {monster_type}]"
            )

        logger.info(
            f"Spawned {len(monsters)} monsters on floor {floor} "
            f"(types: {set(m.name for m in monsters)})"
        )

        return monsters

    def spawn_ore_veins_for_floor(self, floor: int, dungeon_map: Map) -> List[OreVein]:
        """
        Spawn ore veins for a given floor.

        Args:
            floor: Floor number (1-based)
            dungeon_map: Map to spawn ore veins in

        Returns:
            List of spawned OreVein entities
        """
        # Get spawn configuration
        ore_count = self.config.get_ore_vein_count_for_floor(floor)
        ore_weights = self.config.get_ore_spawn_weights(floor)

        # Find positions
        positions = dungeon_map.find_ore_vein_positions(ore_count)

        ore_veins = []
        for x, y in positions:
            # Choose ore type based on weights
            ore_type = self._weighted_random_choice(ore_weights)
            ore_vein = self.entity_loader.create_ore_vein(ore_type, x, y, floor)
            ore_veins.append(ore_vein)

            logger.debug(
                f"Spawned {ore_vein.name} at ({x}, {y}) "
                f"[floor {floor}, type: {ore_type}, "
                f"avg quality: {ore_vein.average_quality:.1f}]"
            )

        logger.info(
            f"Spawned {len(ore_veins)} ore veins on floor {floor} "
            f"(types: {set(v.stats.get('ore_type') for v in ore_veins)})"
        )

        return ore_veins

    def spawn_forges_for_floor(self, floor: int, dungeon_map: Map) -> List[Forge]:
        """
        Spawn forges for a given floor.

        Forges are crafting stations - core to Brogue's unique hook.
        Always spawn 1 forge per floor (consistent access to crafting).

        Args:
            floor: Floor number (1-based)
            dungeon_map: Map to spawn forges in

        Returns:
            List of spawned Forge entities (always length 1)
        """
        # Determine forge type based on floor tiers from config
        tiers = self.config.game_constants['spawning']['floor_tiers']
        if floor <= tiers['tier1_max']:
            forge_type = "basic_forge"
        elif floor <= tiers['tier2_max']:
            forge_type = "iron_forge"
        else:
            forge_type = "master_forge"

        # Find position (1 forge per floor)
        # Use ore vein positions as proxy (forges spawn similarly)
        positions = dungeon_map.find_ore_vein_positions(1)

        if not positions:
            logger.warning(f"No valid positions for forge on floor {floor}")
            return []

        x, y = positions[0]

        # Create forge
        forge = Forge(
            forge_type=forge_type,
            x=x,
            y=y,
        )

        logger.info(
            f"Spawned {forge.name} at ({x}, {y}) on floor {floor}"
        )

        return [forge]

    def _weighted_random_choice(self, weights: Dict[str, int]) -> str:
        """
        Choose random item based on weights.

        Filters out non-numeric entries (like 'description' in YAML)
        and performs weighted random selection.

        Args:
            weights: Dictionary of item -> weight

        Returns:
            Randomly chosen item based on weights

        Raises:
            ContentValidationError: If no valid choices in weights
        """
        # Filter out non-numeric entries (like 'description')
        choices = {k: v for k, v in weights.items() if isinstance(v, int) and v > 0}

        if not choices:
            raise ContentValidationError(
                f"No valid choices in weights: {weights}",
                weights=weights
            )

        # Create weighted list (simple but effective)
        items = []
        for item, weight in choices.items():
            items.extend([item] * weight)

        return GameRNG.get_instance().choice(items)

