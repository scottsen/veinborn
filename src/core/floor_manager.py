"""
FloorManager - handles floor transitions and victory conditions.

Responsibilities:
- Manage floor descending
- Generate new floors
- Check victory conditions
- Handle floor progression logic

This class extracts floor management logic from the Game class,
following Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING, Callable, List, Optional

from .world import Map
from .entities import Monster, OreVein, Forge
from .spawning import EntitySpawner
from .run_end import record_single_player_run_end

if TYPE_CHECKING:
    from .base.game_context import GameContext
    from .game_state import GameState

logger = logging.getLogger(__name__)


DEFAULT_VICTORY_FLOOR = 100  # Matches game_constants.yaml


def get_victory_floor(config) -> int:
    """Floor number that triggers victory (falls back to the default for mocked/partial configs)."""
    try:
        floor = config.game_constants['progression']['victory_floor']
    except (AttributeError, KeyError, TypeError):
        return DEFAULT_VICTORY_FLOOR
    return floor if isinstance(floor, int) else DEFAULT_VICTORY_FLOOR


def generate_floor_map(config, rng) -> Map:
    """Generate a fresh dungeon map.

    VB-18: takes the game's own RNG so descent keeps drawing from the same
    stream instead of the process-global singleton, which a concurrent
    multiplayer game could have re-seeded in the meantime.
    """
    return Map(
        width=config.game_constants['map']['default_width'],
        height=config.game_constants['map']['default_height'],
        config=config,
        rng=rng,
    )


class FloorManager:
    """
    Handles floor transitions and progression.

    Design principles:
    - Single responsibility (floor management only)
    - Uses EntitySpawner (delegation)
    - Testable in isolation
    - Clear victory condition logic
    """

    def __init__(self, context: 'GameContext', spawner: EntitySpawner,
                 on_run_end: Optional[Callable[['GameState', bool], None]] = None):
        """
        Initialize floor manager.

        Args:
            context: Game context for safe state access
            spawner: Entity spawner for creating entities
            on_run_end: Called as (game_state, victory) when the party wins; defaults
                to the single-player score/vault records
        """
        self.context = context
        self.game_state = context.game_state
        self.spawner = spawner
        self.on_run_end = on_run_end or record_single_player_run_end
        logger.debug("FloorManager initialized")

    def descend_floor(self) -> None:
        """
        Descend to the next floor.

        Process:
        1. Check for victory condition
        2. Generate new map
        3. Move the party to the new floor (one player: stairs up)
        4. Spawn new entities
        5. Send messages to player

        Victory condition: Reach floor 100!
        """
        old_floor = self.game_state.current_floor
        new_floor = old_floor + 1

        # Check for victory
        if self._check_victory(new_floor):
            return

        logger.info(f"Descending from floor {old_floor} to floor {new_floor}")

        # Increment floor
        self.game_state.current_floor = new_floor

        # Generate new map
        self._generate_new_floor()

        # Place the party (a party of one: at the stairs up)
        self._place_party()

        # Clear old entities (every player stays in the world)
        self.game_state.clear_floor_entities(
            keep_ids=[p.entity_id for p in self.context.get_all_players()]
        )

        # Spawn new entities
        monsters, ore_veins, forges = self._spawn_floor_entities(new_floor)

        # Add messages
        self.game_state.add_message(f"Welcome to floor {new_floor}!")
        self.game_state.add_message(f"{len(monsters)} monsters roam this level...")
        if forges:
            self.game_state.add_message(f"You spot a {forges[0].name} nearby.")

        logger.info(
            f"Floor {new_floor}: "
            f"Player at ({self.game_state.player.x}, {self.game_state.player.y}), "
            f"{len(monsters)} monsters, {len(ore_veins)} ore veins"
        )

    def _check_victory(self, floor: int) -> bool:
        """
        Check if the party has reached the victory floor.

        Args:
            floor: Floor number to check

        Returns:
            True if victory achieved, False otherwise
        """
        victory_floor = get_victory_floor(self.spawner.config)

        if floor >= victory_floor:
            self.game_state.victory = True
            self.game_state.game_over = True

            # High score with victory bonus (Phase 5) and Legacy Vault tally (Phase 6)
            self.on_run_end(self.game_state, True)

            self.game_state.add_message("🎉 VICTORY! You've escaped the dungeon!")

            logger.info(
                f"GAME WON! Party reached floor {victory_floor}",
                extra={
                    'floor': floor,
                    'player_level': self.game_state.player.get_stat('level', 1),
                    'players_alive': len(self.context.get_alive_players()),
                }
            )
            return True

        return False

    def _generate_new_floor(self) -> None:
        """Generate a new dungeon floor."""
        self.game_state.dungeon_map = generate_floor_map(
            self.spawner.config, self.game_state.rng
        )
        logger.debug("Generated new map")

    def _place_party(self) -> None:
        """Put every player on the new floor.

        One player (single-player, or a party of one): at the stairs up, as always.
        A party: each member on their own spawn position, the same ones a new
        multiplayer game starts on.
        """
        players = self.context.get_all_players()
        if len(players) <= 1:
            self._place_player_at_stairs()
            return

        dungeon_map = self.game_state.dungeon_map
        spawn_positions = dungeon_map.find_player_spawn_positions(len(players))
        for index, player in enumerate(players):
            if index < len(spawn_positions):
                x, y = spawn_positions[index]
            else:
                x, y = dungeon_map.find_starting_position()
            player.move_to(x, y)
        logger.debug(f"Placed a party of {len(players)} on the new floor")

    def _place_player_at_stairs(self) -> None:
        """Place the player at the stairs up position."""
        stairs_up_pos = self.game_state.dungeon_map.place_stairs_up()

        if stairs_up_pos:
            self.game_state.player.move_to(*stairs_up_pos)
            logger.debug(f"Player placed at stairs up: {stairs_up_pos}")
        else:
            # Fallback to starting position
            start_pos = self.game_state.dungeon_map.find_starting_position()
            self.game_state.player.move_to(*start_pos)
            logger.warning(
                f"No stairs up found, placed player at starting position: {start_pos}"
            )

    def _spawn_floor_entities(self, floor: int) -> tuple[List[Monster], List[OreVein], List[Forge]]:
        """
        Spawn monsters, ore veins, and forges for the floor.

        Args:
            floor: Floor number

        Returns:
            Tuple of (monsters, ore_veins, forges)
        """
        spawned = self.spawner.spawn_all_for_floor(floor, self.game_state.dungeon_map)
        monsters = spawned['monsters']
        ore_veins = spawned['ore_veins']
        forges = spawned['forges']

        for entity in [*monsters, *ore_veins, *forges]:
            self.context.add_entity(entity)

        logger.debug(
            f"Spawned entities for floor {floor}: "
            f"{len(monsters)} monsters, {len(ore_veins)} ore veins, {len(forges)} forges"
        )

        return monsters, ore_veins, forges
