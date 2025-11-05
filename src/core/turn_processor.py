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
