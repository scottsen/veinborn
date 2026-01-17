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
from typing import TYPE_CHECKING, List

from .world import Map
from .entities import Monster, OreVein, Forge
from .spawning import EntitySpawner
from .highscore import HighScoreManager, HighScoreEntry
from .legacy import get_vault

if TYPE_CHECKING:
    from .base.game_context import GameContext
    from .game_state import GameState

logger = logging.getLogger(__name__)


class FloorManager:
    """
    Handles floor transitions and progression.

    Design principles:
    - Single responsibility (floor management only)
    - Uses EntitySpawner (delegation)
    - Testable in isolation
    - Clear victory condition logic
    """

    def __init__(self, context: 'GameContext', spawner: EntitySpawner):
        """
        Initialize floor manager.

        Args:
            context: Game context for safe state access
            spawner: Entity spawner for creating entities
        """
        self.context = context
        self.game_state = context.game_state
        self.spawner = spawner
        logger.debug("FloorManager initialized")

    def descend_floor(self) -> None:
        """
        Descend to the next floor.

        Process:
        1. Check for victory condition
        2. Generate new map
        3. Move player to stairs up
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

        # Place player at stairs up
        self._place_player_at_stairs()

        # Clear old entities
        self.game_state.entities.clear()

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
        Check if player has reached victory floor.

        Args:
            floor: Floor number to check

        Returns:
            True if victory achieved, False otherwise
        """
        try:
            victory_floor = self.spawner.config.game_constants['progression']['victory_floor']
            # Handle mocked config in tests (MagicMock returns MagicMock)
            if not isinstance(victory_floor, int):
                victory_floor = 100  # Default from game_constants.yaml
        except (AttributeError, KeyError, TypeError):
            victory_floor = 100  # Fallback for mocked spawner in tests

        if floor >= victory_floor:
            self.game_state.victory = True
            self.game_state.game_over = True

            # Record high score with victory bonus (Phase 5)
            self._record_high_score()

            # Record victory in Legacy Vault (Phase 6)
            self._record_victory()

            self.game_state.add_message("🎉 VICTORY! You've escaped the dungeon!")

            logger.info(
                f"GAME WON! Player reached floor {victory_floor}",
                extra={
                    'floor': floor,
                    'player_level': self.game_state.player.get_stat('level', 1),
                    'player_hp': self.game_state.player.hp,
                }
            )
            return True

        return False

    def _record_high_score(self) -> None:
        """
        Record high score for this game (Phase 5).

        Creates a high score entry and adds it to the leaderboard.
        Displays rank to player. Victory adds 50,000 point bonus!
        """
        try:
            # Create high score entry from game state
            entry = HighScoreEntry.from_game_state(
                self.game_state,
                self.game_state.player_name
            )

            # Add to leaderboard
            hsm = HighScoreManager.get_instance()
            rank = hsm.add_score(entry)

            # Display rank to player
            if rank > 0:
                self.game_state.add_message(f"Final Score: {entry.score} (+50,000 victory bonus!)")
                if rank <= 10:
                    self.game_state.add_message(f"🏆 New High Score! Rank #{rank}")
                else:
                    self.game_state.add_message(f"You ranked #{rank}")

                logger.info(
                    f"High score recorded: {self.game_state.player_name} "
                    f"scored {entry.score} (rank #{rank}, VICTORY!)"
                )
            else:
                logger.warning("High score not saved (rank -1)")

        except Exception as e:
            logger.error(f"Failed to record high score: {e}", exc_info=True)
            # Don't crash on high score failure - game over should still work

    def _record_victory(self) -> None:
        """
        Record victory in Legacy Vault (Phase 6).

        Tracks Pure vs Legacy victories for meta-progression stats.
        """
        try:
            vault = get_vault()
            run_type = self.game_state.run_type
            vault.record_run(run_type, victory=True)

            # Display victory type to player
            if run_type == "pure":
                self.game_state.add_message("🏆 PURE VICTORY! (No Legacy gear used)")
            else:
                self.game_state.add_message("⚔️ LEGACY VICTORY! (Legacy gear used)")

            logger.info(
                f"Victory recorded in Legacy Vault: {run_type}",
                extra={
                    'run_type': run_type,
                    'total_pure_victories': vault.total_pure_victories,
                    'total_legacy_victories': vault.total_legacy_victories
                }
            )

        except Exception as e:
            logger.error(f"Failed to record victory in Legacy Vault: {e}", exc_info=True)
            # Don't crash on vault failure - game over should still work

    def _generate_new_floor(self) -> None:
        """Generate a new dungeon floor."""
        map_width = self.spawner.config.game_constants['map']['default_width']
        map_height = self.spawner.config.game_constants['map']['default_height']

        self.game_state.dungeon_map = Map(
            width=map_width,
            height=map_height,
            config=self.spawner.config  # Pass config from spawner
        )
        logger.debug(
            f"Generated new map: {map_width}x{map_height}"
        )

    def _place_player_at_stairs(self) -> None:
        """Place player at stairs up position."""
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
        dungeon_map = self.game_state.dungeon_map

        # Spawn monsters
        monsters = self.spawner.spawn_monsters_for_floor(floor, dungeon_map)
        for monster in monsters:
            self.context.add_entity(monster)

        # Spawn ore veins
        ore_veins = self.spawner.spawn_ore_veins_for_floor(floor, dungeon_map)
        for ore_vein in ore_veins:
            self.context.add_entity(ore_vein)

        # Spawn forges (crafting stations)
        forges = self.spawner.spawn_forges_for_floor(floor, dungeon_map)
        for forge in forges:
            self.context.add_entity(forge)

        logger.debug(
            f"Spawned entities for floor {floor}: "
            f"{len(monsters)} monsters, {len(ore_veins)} ore veins, {len(forges)} forges"
        )

        return monsters, ore_veins, forges
