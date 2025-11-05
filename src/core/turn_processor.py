"""
TurnProcessor - handles turn progression and related mechanics.

Responsibilities:
- Process game turns (monster AI, cleanup)
- Handle HP regeneration
- Check game over conditions
- Manage turn counter

This class extracts turn processing logic from the Game class,
following Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING

from .constants import HP_REGEN_INTERVAL_TURNS, HP_REGEN_AMOUNT
from .base.entity import EntityType
from .highscore import HighScoreManager, HighScoreEntry
from .legacy import get_vault

if TYPE_CHECKING:
    from .base.game_context import GameContext
    from .game_state import GameState

logger = logging.getLogger(__name__)


class TurnProcessor:
    """
    Handles turn progression and related mechanics.

    Design principles:
    - Single responsibility (turn processing only)
    - Uses GameContext (safe API)
    - Testable in isolation
    - Clear separation of concerns
    """

    def __init__(self, context: 'GameContext'):
        """
        Initialize turn processor.

        Args:
            context: Game context for safe state access
        """
        self.context = context
        self.game_state = context.game_state
        logger.debug("TurnProcessor initialized")

    def process_turn(self) -> None:
        """
        Process one game turn.

        Steps:
        1. Increment turn counter
        2. Apply HP regeneration
        3. Run AI systems (monsters act)
        4. Cleanup dead entities
        5. Check game over conditions
        """
        # Increment turn counter
        self.game_state.turn_count += 1

        logger.debug(
            f"Processing turn {self.game_state.turn_count}",
            extra={
                'turn': self.game_state.turn_count,
                'floor': self.game_state.current_floor,
                'player_hp': f"{self.game_state.player.hp}/{self.game_state.player.max_hp}",
                'monster_count': len([
                    e for e in self.context.get_entities_by_type(EntityType.MONSTER)
                    if e.is_alive
                ]),
            }
        )

        # Apply HP regeneration
        self._apply_hp_regeneration()

        # Run AI system (monsters take turns)
        self._run_ai_systems()

        # Cleanup dead entities
        self._cleanup_dead_entities()

        # Check game over conditions
        self._check_game_over()

    def _apply_hp_regeneration(self) -> None:
        """
        Apply natural HP regeneration to player.

        NetHack-style: 1 HP every 10 turns
        """
        if self.game_state.turn_count % HP_REGEN_INTERVAL_TURNS == 0:
            player = self.game_state.player

            if player.hp < player.max_hp:
                healed = player.heal(HP_REGEN_AMOUNT)

                if healed > 0:
                    logger.debug(
                        f"Player regenerated {healed} HP "
                        f"(turn {self.game_state.turn_count})"
                    )

    def _run_ai_systems(self) -> None:
        """Run all AI systems (monster turns)."""
        ai_system = self.context.get_system('ai')

        if ai_system:
            logger.debug("Running AI system for monster turns")
            ai_system.update()
        else:
            logger.warning("AI system not found, monsters will not act")

    def _cleanup_dead_entities(self) -> None:
        """Remove dead entities from the game."""
        dead_count = len([
            e for e in self.context.game_state.entities.values()
            if not e.is_alive
        ])

        if dead_count > 0:
            logger.debug(f"Cleaning up {dead_count} dead entities")
            self.game_state.cleanup_dead_entities()

    def _check_game_over(self) -> None:
        """Check if game is over (player died)."""
        if not self.game_state.player.is_alive:
            # Record high score (Phase 5)
            self._record_high_score()

            # Save rare ore to Legacy Vault (Phase 6)
            self._save_legacy_ore()

            # Record defeat in Legacy Vault
            self._record_defeat()

            self.game_state.add_message("You died! Press 'r' to restart.")
            self.game_state.game_over = True

            logger.info(
                "Game over - player died",
                extra={
                    'turn': self.game_state.turn_count,
                    'floor': self.game_state.current_floor,
                    'player_level': self.game_state.player.get_stat('level', 1),
                }
            )

    def _record_high_score(self) -> None:
        """
        Record high score for this game (Phase 5).

        Creates a high score entry and adds it to the leaderboard.
        Displays rank to player.
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
                self.game_state.add_message(f"Final Score: {entry.score}")
                if rank <= 10:
                    self.game_state.add_message(f"🏆 New High Score! Rank #{rank}")
                else:
                    self.game_state.add_message(f"You ranked #{rank}")

                logger.info(
                    f"High score recorded: {self.game_state.player_name} "
                    f"scored {entry.score} (rank #{rank})"
                )
            else:
                logger.warning("High score not saved (rank -1)")

        except Exception as e:
            logger.error(f"Failed to record high score: {e}", exc_info=True)
            # Don't crash on high score failure - game over should still work

    def _save_legacy_ore(self) -> None:
        """
        Save rare ore (80+ purity) to Legacy Vault on death.

        Checks player inventory for ore with purity >= 80 and saves them
        to the vault for use in future runs. Displays message to player
        if any ore was saved.
        """
        try:
            vault = get_vault()

            # Get all ore from player inventory
            ores_saved = vault.add_ores_from_inventory(
                self.game_state.player.inventory,
                self.game_state.current_floor
            )

            if ores_saved > 0:
                self.game_state.add_message(
                    f"💎 {ores_saved} rare ore{'s' if ores_saved != 1 else ''} "
                    f"saved to Legacy Vault!"
                )

                logger.info(
                    f"Legacy Vault: Saved {ores_saved} ore(s) from player inventory",
                    extra={
                        'ores_saved': ores_saved,
                        'floor': self.game_state.current_floor,
                        'vault_size': vault.get_ore_count()
                    }
                )
            else:
                logger.debug("No rare ore (80+ purity) found in player inventory")

        except Exception as e:
            logger.error(f"Failed to save ore to Legacy Vault: {e}", exc_info=True)
            # Don't crash on vault failure - game over should still work

    def _record_defeat(self) -> None:
        """
        Record defeat in Legacy Vault (Phase 6).

        Tracks total runs for stats purposes.
        """
        try:
            vault = get_vault()
            run_type = self.game_state.run_type
            vault.record_run(run_type, victory=False)

            logger.info(
                f"Defeat recorded in Legacy Vault: {run_type}",
                extra={
                    'run_type': run_type,
                    'total_runs': vault.total_runs
                }
            )

        except Exception as e:
            logger.error(f"Failed to record defeat in Legacy Vault: {e}", exc_info=True)
            # Don't crash on vault failure - game over should still work
