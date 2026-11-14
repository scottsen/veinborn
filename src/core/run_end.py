"""Single-player end-of-run records: high score and Legacy Vault.

The engine publishes RUN_ENDED (TurnProcessor on defeat, FloorManager on victory);
who records what is the host's choice. Single-player installs
`SinglePlayerRunRecorder` (personal high score + Legacy Vault); a multiplayer
session subscribes its own co-op scoring instead.
"""

import logging

from .events import EventBus, GameEventType
from .highscore import HighScoreManager, HighScoreEntry
from .legacy import get_vault

logger = logging.getLogger(__name__)


class SinglePlayerRunRecorder:
    """Records the finished run, in the order the single-player game always has."""

    def __init__(self, game_state):
        self.game_state = game_state

    def on_run_ended(self, event) -> None:
        record_single_player_run_end(self.game_state, bool(event.data.get('victory')))

    def install(self, event_bus: EventBus) -> "SinglePlayerRunRecorder":
        event_bus.subscribe(GameEventType.RUN_ENDED, self.on_run_ended,
                            subscriber_name="SinglePlayerRunRecorder.on_run_ended")
        return self

    def uninstall(self, event_bus: EventBus) -> None:
        event_bus.unsubscribe(GameEventType.RUN_ENDED, self.on_run_ended)


def single_player_bus(game_state) -> EventBus:
    """A bus with the single-player recorder already subscribed (tests, headless runs)."""
    bus = EventBus()
    SinglePlayerRunRecorder(game_state).install(bus)
    return bus


def record_single_player_run_end(game_state, victory: bool) -> None:
    """Record the finished run, in the order the single-player game always has.

    Death: high score, rare ore into the vault, defeat tally.
    Victory: high score (with the victory bonus), victory tally.
    Each step logs and swallows its own failure: ending the run must not crash.
    """
    if victory:
        _record_victory_high_score(game_state)
        _record_victory(game_state)
    else:
        _record_death_high_score(game_state)
        _save_legacy_ore(game_state)
        _record_defeat(game_state)


def _record_death_high_score(game_state) -> None:
    """
    Record high score for this game (Phase 5).

    Creates a high score entry and adds it to the leaderboard.
    Displays rank to player.
    """
    try:
        # Create high score entry from game state
        entry = HighScoreEntry.from_game_state(
            game_state,
            game_state.player_name
        )

        # Add to leaderboard
        hsm = HighScoreManager.get_instance()
        rank = hsm.add_score(entry)

        # Display rank to player
        if rank > 0:
            game_state.add_message(f"Final Score: {entry.score}")
            if rank <= 10:
                game_state.add_message(f"🏆 New High Score! Rank #{rank}")
            else:
                game_state.add_message(f"You ranked #{rank}")

            logger.info(
                f"High score recorded: {game_state.player_name} "
                f"scored {entry.score} (rank #{rank})"
            )
        else:
            logger.warning("High score not saved (rank -1)")

    except Exception as e:
        logger.error(f"Failed to record high score: {e}", exc_info=True)
        # Don't crash on high score failure - game over should still work


def _save_legacy_ore(game_state) -> None:
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
            game_state.player.inventory,
            game_state.current_floor
        )

        if ores_saved > 0:
            game_state.add_message(
                f"💎 {ores_saved} rare ore{'s' if ores_saved != 1 else ''} "
                f"saved to Legacy Vault!"
            )

            logger.info(
                f"Legacy Vault: Saved {ores_saved} ore(s) from player inventory",
                extra={
                    'ores_saved': ores_saved,
                    'floor': game_state.current_floor,
                    'vault_size': vault.get_ore_count()
                }
            )
        else:
            logger.debug("No rare ore (80+ purity) found in player inventory")

    except Exception as e:
        logger.error(f"Failed to save ore to Legacy Vault: {e}", exc_info=True)
        # Don't crash on vault failure - game over should still work


def _record_defeat(game_state) -> None:
    """
    Record defeat in Legacy Vault (Phase 6).

    Tracks total runs for stats purposes.
    """
    try:
        vault = get_vault()
        run_type = game_state.run_type
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


def _record_victory_high_score(game_state) -> None:
    """
    Record high score for this game (Phase 5).

    Creates a high score entry and adds it to the leaderboard.
    Displays rank to player. Victory adds 50,000 point bonus!
    """
    try:
        # Create high score entry from game state
        entry = HighScoreEntry.from_game_state(
            game_state,
            game_state.player_name
        )

        # Add to leaderboard
        hsm = HighScoreManager.get_instance()
        rank = hsm.add_score(entry)

        # Display rank to player
        if rank > 0:
            game_state.add_message(f"Final Score: {entry.score} (+50,000 victory bonus!)")
            if rank <= 10:
                game_state.add_message(f"🏆 New High Score! Rank #{rank}")
            else:
                game_state.add_message(f"You ranked #{rank}")

            logger.info(
                f"High score recorded: {game_state.player_name} "
                f"scored {entry.score} (rank #{rank}, VICTORY!)"
            )
        else:
            logger.warning("High score not saved (rank -1)")

    except Exception as e:
        logger.error(f"Failed to record high score: {e}", exc_info=True)
        # Don't crash on high score failure - game over should still work


def _record_victory(game_state) -> None:
    """
    Record victory in Legacy Vault (Phase 6).

    Tracks Pure vs Legacy victories for meta-progression stats.
    """
    try:
        vault = get_vault()
        run_type = game_state.run_type
        vault.record_run(run_type, victory=True)

        # Display victory type to player
        if run_type == "pure":
            game_state.add_message("🏆 PURE VICTORY! (No Legacy gear used)")
        else:
            game_state.add_message("⚔️ LEGACY VICTORY! (Legacy gear used)")

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
