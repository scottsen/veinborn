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

        Forges are crafting stations - core to Veinborn's unique hook.
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

    def spawn_special_room_entities(self, floor: int, dungeon_map: Map):
        """
        Spawn special entities in special rooms.

        This method processes all rooms and spawns appropriate entities
        based on their room type.

        Args:
            floor: Current floor number
            dungeon_map: Map containing rooms

        Returns:
            Dict of entity lists by type: {'monsters': [...], 'ores': [...], 'items': [...]}
        """
        from ..world import RoomType

        monsters = []
        ores = []
        items = []  # For future treasure items

        for room in dungeon_map.rooms:
            if room.room_type == RoomType.TREASURE:
                # Spawn high-quality ore as treasure (future: actual items)
                room_ores = self._spawn_treasure_room(room, floor, dungeon_map)
                ores.extend(room_ores)

            elif room.room_type == RoomType.MONSTER_DEN:
                # Spawn extra monsters
                room_monsters = self._spawn_monster_den(room, floor, dungeon_map)
                monsters.extend(room_monsters)

            elif room.room_type == RoomType.ORE_CHAMBER:
                # Spawn multiple high-quality ore veins
                room_ores = self._spawn_ore_chamber(room, floor, dungeon_map)
                ores.extend(room_ores)

            elif room.room_type == RoomType.SHRINE:
                # Currently no special spawning (shrine effects are in game logic)
                # Future: spawn shrine entity with healing/buff effects
                pass

            elif room.room_type == RoomType.TRAP:
                # Currently no special spawning (traps are in game logic)
                # Future: spawn trap entities
                pass

        logger.info(
            f"Spawned special room entities on floor {floor}: "
            f"{len(monsters)} bonus monsters, {len(ores)} bonus ores"
        )

        return {'monsters': monsters, 'ores': ores, 'items': items}

    def _spawn_treasure_room(self, room, floor: int, dungeon_map: Map) -> List[OreVein]:
        """Spawn treasure in a treasure room (currently high-quality ore)."""
        rng = GameRNG.get_instance()

        # Get configuration from spawning.yaml
        treasure_config = self.config.get_special_room_config('treasure_room')
        num_treasures = rng.randint(
            treasure_config['ore_count']['min'],
            treasure_config['ore_count']['max']
        )

        ores = []
        ore_weights = self.config.get_ore_spawn_weights(floor)

        for _ in range(num_treasures):
            # Find position within the room
            x = rng.randint(room.x + 1, room.x + room.width - 2)
            y = rng.randint(room.y + 1, room.y + room.height - 2)

            # Skip if position is blocked
            if not dungeon_map.is_walkable(x, y):
                continue

            ore_type = self._weighted_random_choice(ore_weights)
            ore = self.entity_loader.create_ore_vein(ore_type, x, y, floor)

            # Boost purity for treasure rooms (from config)
            ore.purity = min(100, rng.randint(
                treasure_config['ore_purity']['min'],
                treasure_config['ore_purity']['max']
            ))

            ores.append(ore)
            logger.debug(f"Spawned treasure ore {ore_type} (purity:{ore.purity}) at ({x}, {y})")

        return ores

    def _spawn_monster_den(self, room, floor: int, dungeon_map: Map) -> List[Monster]:
        """Spawn extra monsters in a monster den."""
        rng = GameRNG.get_instance()

        # Get configuration from spawning.yaml
        den_config = self.config.get_special_room_config('monster_den')
        num_monsters = rng.randint(
            den_config['monster_count']['min'],
            den_config['monster_count']['max']
        )
        stat_boost = den_config['stat_boost_multiplier']

        monsters = []
        spawn_weights = self.config.get_monster_spawn_weights(floor)

        for _ in range(num_monsters):
            # Find position within the room
            x = rng.randint(room.x + 1, room.x + room.width - 2)
            y = rng.randint(room.y + 1, room.y + room.height - 2)

            # Skip if position is blocked
            if not dungeon_map.is_walkable(x, y):
                continue

            monster_type = self._weighted_random_choice(spawn_weights)
            monster = self.entity_loader.create_monster(monster_type, x, y)

            # Boost stats from config
            monster.max_hp = int(monster.max_hp * stat_boost)
            monster.hp = monster.max_hp
            monster.attack = int(monster.attack * stat_boost)

            monsters.append(monster)
            logger.debug(f"Spawned den monster {monster_type} at ({x}, {y})")

        return monsters

    def _spawn_ore_chamber(self, room, floor: int, dungeon_map: Map) -> List[OreVein]:
        """Spawn multiple high-quality ore veins in an ore chamber."""
        rng = GameRNG.get_instance()

        # Get configuration from spawning.yaml
        chamber_config = self.config.get_special_room_config('ore_chamber')
        num_ores = rng.randint(
            chamber_config['ore_count']['min'],
            chamber_config['ore_count']['max']
        )

        ores = []
        ore_weights = self.config.get_ore_spawn_weights(floor)

        for _ in range(num_ores):
            # Find position within the room
            x = rng.randint(room.x + 1, room.x + room.width - 2)
            y = rng.randint(room.y + 1, room.y + room.height - 2)

            # Skip if position is blocked
            if not dungeon_map.is_walkable(x, y):
                continue

            ore_type = self._weighted_random_choice(ore_weights)
            ore = self.entity_loader.create_ore_vein(ore_type, x, y, floor)

            # Boost purity from config
            ore.purity = min(100, rng.randint(
                chamber_config['ore_purity']['min'],
                chamber_config['ore_purity']['max']
            ))

            ores.append(ore)
            logger.debug(f"Spawned chamber ore {ore_type} (purity:{ore.purity}) at ({x}, {y})")

        return ores

