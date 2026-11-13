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
from typing import List, Dict, Optional

from ..config import GameConfig
from ..entity_loader import EntityLoader
from ..rng import GameRNG
from ..geometry import chebyshev
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
        self._validate_spawn_tables()
        logger.debug("EntitySpawner initialized")

    def _validate_spawn_tables(self) -> None:
        """Every id in a spawn-weight band must be a defined monster / ore.

        Without this a typo surfaces only when a player first reaches that band.
        """
        checks = (
            ('monster_spawns.yaml', self.config.monster_spawns['spawn_weights'],
             set(self.entity_loader.get_monster_ids())),
            ('ore_veins.yaml', self.config.ore_veins['spawn_weights'],
             set(self.entity_loader.get_ore_ids())),
        )
        for filename, bands, known in checks:
            for band, weights in bands.items():
                unknown = sorted(k for k, v in weights.items()
                                 if isinstance(v, int) and k not in known)
                if unknown:
                    raise ContentValidationError(
                        f"{filename} spawn_weights.{band} names undefined ids: {unknown}",
                        band=band, unknown=unknown,
                    )

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
            monster_type = self._weighted_random_choice(spawn_weights, dungeon_map.rng)
            monster = self.entity_loader.create_monster(monster_type, x, y, floor=floor)
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

    def spawn_wandering_monster(
        self,
        floor: int,
        player_level: int,
        dungeon_map: Map,
        player_positions: List[tuple],
        occupied: set,
        rng: GameRNG,
    ) -> Optional[Monster]:
        """
        Spawn one monster mid-floor (VB-52), out of the players' reach.

        Difficulty tier is (floor + player_level) // 2 (NetHack's formula,
        minimum 1) so it follows both depth and how strong the player is.

        Args:
            floor: Current floor number
            player_level: Average level of the living players
            dungeon_map: Map to spawn into
            player_positions: (x, y) of every living player
            occupied: Tiles already holding an entity
            rng: The game's RNG (keeps seeded games reproducible)

        Returns:
            The new Monster (not yet added to the world), or None if no tile
            far enough from every player was free.
        """
        min_dist = self.config.get_ongoing_spawn_config().get('min_distance_from_player', 8)
        candidates = [
            (x, y)
            for x in range(dungeon_map.width)
            for y in range(dungeon_map.height)
            if dungeon_map.is_walkable(x, y)
            and (x, y) not in occupied
            and all(chebyshev(x, y, px, py) >= min_dist for px, py in player_positions)
        ]
        if not candidates:
            return None

        x, y = rng.choice(candidates)
        tier = max(1, (floor + player_level) // 2)
        monster_type = self._weighted_random_choice(
            self.config.get_monster_spawn_weights(tier), rng
        )
        monster = self.entity_loader.create_monster(monster_type, x, y, floor=floor)
        logger.debug(f"Wandering {monster.name} appeared at ({x}, {y}) [floor {floor}, tier {tier}]")
        return monster

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
            ore_type = self._weighted_random_choice(ore_weights, dungeon_map.rng)
            ore_vein = self.entity_loader.create_ore_vein(ore_type, x, y, floor, rng=dungeon_map.rng)
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

    def _weighted_random_choice(self, weights: Dict[str, int], rng: GameRNG) -> str:
        """
        Choose random item based on weights.

        Filters out non-numeric entries (like 'description' in YAML)
        and performs weighted random selection.

        Args:
            weights: Dictionary of item -> weight
            rng: The RNG instance for the game this spawn belongs to
                 (VB-18: must be the calling map's own instance, not the
                 process-global singleton, so concurrent multiplayer games
                 don't stomp each other's randomness)

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

        return rng.choice(items)

    @staticmethod
    def _claim_free_tile(entity, occupied: set, dungeon_map: Map, max_radius: int = 8) -> bool:
        """
        Make `entity` the sole occupant of a tile, moving it if its tile is taken.

        Moves to the nearest walkable, unoccupied tile (breadth-first, 8-directional,
        within `max_radius`). Records the final tile in `occupied`.

        Returns:
            False if no free tile was found (caller should drop the entity).
        """
        start = (entity.x, entity.y)
        if start not in occupied:
            occupied.add(start)
            return True

        seen = {start}
        frontier = [start]
        for _ in range(max_radius):
            next_frontier = []
            for x, y in frontier:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        tile = (x + dx, y + dy)
                        if tile in seen:
                            continue
                        seen.add(tile)
                        if not dungeon_map.in_bounds(*tile):
                            continue
                        if dungeon_map.is_walkable(*tile) and tile not in occupied:
                            entity.x, entity.y = tile
                            occupied.add(tile)
                            return True
                        next_frontier.append(tile)
            frontier = next_frontier
        logger.warning(f"No free tile near {start} for {getattr(entity, 'name', entity)}; dropped")
        return False

    def spawn_all_for_floor(self, floor: int, dungeon_map: Map) -> Dict[str, List]:
        """Spawn everything a floor gets: regular entities plus special-room extras.

        Single entry point for game start, single-player descent and multiplayer
        descent, so they can't drift apart on what a floor contains (VB-25).

        Returns:
            {'monsters': [...], 'ore_veins': [...], 'forges': [...]}
        """
        monsters = self.spawn_monsters_for_floor(floor, dungeon_map)
        ore_veins = self.spawn_ore_veins_for_floor(floor, dungeon_map)
        forges = self.spawn_forges_for_floor(floor, dungeon_map)

        special_entities = self.spawn_special_room_entities(floor, dungeon_map)

        # Each spawner picks tiles without knowing about the others: the forge always
        # lands on the first ore vein's tile, and special-room extras pick random room
        # tiles. Resolve overlaps here, after generation, so the RNG sequence (and so
        # seeded floors) is unchanged and no entity is lost. Earlier groups keep their
        # tile; later ones move to the nearest free walkable tile.
        occupied = {(e.x, e.y) for e in monsters + ore_veins}
        for entity in forges:
            self._claim_free_tile(entity, occupied, dungeon_map)
        for den_monster in special_entities['monsters']:
            if self._claim_free_tile(den_monster, occupied, dungeon_map):
                monsters.append(den_monster)
        for bonus_ore in special_entities['ores']:
            if self._claim_free_tile(bonus_ore, occupied, dungeon_map):
                ore_veins.append(bonus_ore)

        return {'monsters': monsters, 'ore_veins': ore_veins, 'forges': forges}

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
        rng = dungeon_map.rng

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

            ore_type = self._weighted_random_choice(ore_weights, rng)
            ore = self.entity_loader.create_ore_vein(ore_type, x, y, floor, rng=rng)

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
        rng = dungeon_map.rng

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

            monster_type = self._weighted_random_choice(spawn_weights, rng)
            monster = self.entity_loader.create_monster(monster_type, x, y, floor=floor)

            # Boost stats from config
            monster.max_hp = int(monster.max_hp * stat_boost)
            monster.hp = monster.max_hp
            monster.attack = int(monster.attack * stat_boost)

            monsters.append(monster)
            logger.debug(f"Spawned den monster {monster_type} at ({x}, {y})")

        return monsters

    def _spawn_ore_chamber(self, room, floor: int, dungeon_map: Map) -> List[OreVein]:
        """Spawn multiple high-quality ore veins in an ore chamber."""
        rng = dungeon_map.rng

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

            ore_type = self._weighted_random_choice(ore_weights, rng)
            ore = self.entity_loader.create_ore_vein(ore_type, x, y, floor, rng=rng)

            # Boost purity from config
            ore.purity = min(100, rng.randint(
                chamber_config['ore_purity']['min'],
                chamber_config['ore_purity']['max']
            ))

            ores.append(ore)
            logger.debug(f"Spawned chamber ore {ore_type} (purity:{ore.purity}) at ({x}, {y})")

        return ores

