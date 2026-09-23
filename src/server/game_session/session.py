"""GameSession — manages a single multiplayer game instance."""

import asyncio
import time
import logging
from typing import Dict, List, Optional

from core.action_pipeline import process_action_outcome
from core.actions.wait_action import WaitAction
from core.base.action import Action
from core.base.game_context import GameContext
from core.events import EventBus
from core.highscore import HighScoreEntry, HighScoreManager
from core.systems.ai_system import AISystem
from server.multiplayer_game_state import MultiplayerGameState
from server.state_delta import StateDelta

from .player_info import PlayerInfo

logger = logging.getLogger(__name__)


class GameSession:
    """Manages a single multiplayer game instance."""

    def __init__(
        self,
        game_id: str,
        game_name: str,
        max_players: int = 4,
        actions_per_round: int = 4,
        high_scores: Optional[HighScoreManager] = None,
    ):
        self.game_id = game_id
        self.game_name = game_name
        self.max_players = max_players
        self.actions_per_round = actions_per_round

        # Player management
        self.players: Dict[str, PlayerInfo] = {}
        self.player_order: List[str] = []

        # Game state (multiplayer-aware)
        self.mp_game_state: Optional[MultiplayerGameState] = None
        self.is_started = False
        self.is_finished = False
        self.created_at = time.time()

        # Game context and systems (initialized when game starts)
        self.game_context: Optional[GameContext] = None
        self.ai_system: Optional[AISystem] = None
        self.event_bus = EventBus()

        # Turn management
        self.actions_this_round = 0
        self.pending_actions: asyncio.Queue = asyncio.Queue()

        # State tracking for delta compression
        self.last_state: Optional[Dict] = None
        self.use_delta_compression = True  # Enable/disable delta compression

        # Co-op scores live on their own leaderboard, one entry per player
        # (resolved lazily so tests and the server can inject a manager).
        self._high_scores = high_scores
        self._scored_player_ids: set = set()

        # Locks
        self._lock = asyncio.Lock()

    def can_join(self) -> bool:
        """Check if the game can accept more players."""
        return (
            len(self.players) < self.max_players
            and not self.is_started
            and not self.is_finished
        )

    async def add_player(
        self, player_id: str, player_name: str, player_class: str = "warrior"
    ) -> bool:
        """Add a player to the game session.

        Args:
            player_id: Unique player ID
            player_name: Player display name
            player_class: Character class (warrior, mage, rogue, healer)

        Returns:
            True if player was added, False otherwise
        """
        async with self._lock:
            if not self.can_join():
                return False

            if player_id in self.players:
                return False

            player_info = PlayerInfo(
                player_id=player_id,
                player_name=player_name,
                player_class=player_class,
            )
            self.players[player_id] = player_info
            self.player_order.append(player_id)

            return True

    async def remove_player(self, player_id: str) -> bool:
        """Remove a player from the game session.

        Args:
            player_id: Player ID to remove

        Returns:
            True if player was removed, False otherwise
        """
        async with self._lock:
            return self._remove_player_locked(player_id)

    def _remove_player_locked(self, player_id: str) -> bool:
        """Remove a player — caller must already hold self._lock."""
        if player_id not in self.players:
            return False

        del self.players[player_id]
        if player_id in self.player_order:
            self.player_order.remove(player_id)

        # If game is running and no connected/disconnected players left, mark as finished
        connected_count = sum(
            1 for p in self.players.values()
            if not p.has_left()
        )
        if self.is_started and connected_count == 0:
            self.is_finished = True

        return True

    async def disconnect_player(self, player_id: str) -> bool:
        """Mark a player as disconnected but keep them in the game.

        Args:
            player_id: Player ID to disconnect

        Returns:
            True if player was marked as disconnected, False otherwise
        """
        async with self._lock:
            if player_id not in self.players:
                return False

            player_info = self.players[player_id]
            player_info.mark_disconnected()

            logger.info(
                f"Player {player_info.player_name} disconnected from game {self.game_id}. "
                f"Will be removed in {player_info.reconnect_timeout_seconds}s if not reconnected."
            )

            return True

    async def reconnect_player(self, player_id: str) -> tuple[bool, Optional[str]]:
        """Reconnect a previously disconnected player.

        Args:
            player_id: Player ID to reconnect

        Returns:
            Tuple of (success, error_message)
        """
        async with self._lock:
            if player_id not in self.players:
                return False, "Player not in game"

            player_info = self.players[player_id]

            if not player_info.is_disconnected():
                if player_info.has_left():
                    return False, "Player has left the game"
                else:
                    return False, "Player is already connected"

            # Check if reconnect timeout has expired
            if player_info.is_reconnect_timeout_expired():
                return False, "Reconnection timeout expired"

            # Mark player as reconnected
            player_info.mark_reconnected()

            logger.info(
                f"Player {player_info.player_name} reconnected to game {self.game_id}"
            )

            return True, None

    async def leave_player(self, player_id: str) -> bool:
        """Mark a player as having voluntarily left the game.

        Args:
            player_id: Player ID

        Returns:
            True if successful, False otherwise
        """
        async with self._lock:
            if player_id not in self.players:
                return False

            player_info = self.players[player_id]
            player_info.mark_left()

            logger.info(
                f"Player {player_info.player_name} left game {self.game_id}"
            )

            # Check if all players have left
            connected_count = sum(
                1 for p in self.players.values()
                if not p.has_left()
            )
            if connected_count == 0:
                self.is_finished = True

            return True

    async def cleanup_expired_disconnections(self) -> List[str]:
        """Remove players whose reconnection timeout has expired.

        Returns:
            List of player IDs that were removed
        """
        removed_players = []

        async with self._lock:
            for player_id, player_info in list(self.players.items()):
                if not player_info.is_reconnect_timeout_expired():
                    continue

                logger.info(
                    f"Removing player {player_info.player_name} from game {self.game_id} "
                    f"due to reconnection timeout"
                )
                if self._remove_player_locked(player_id):
                    removed_players.append(player_id)

        return removed_players

    async def set_player_ready(self, player_id: str, ready: bool = True) -> bool:
        """Set a player's ready status.

        Args:
            player_id: Player ID
            ready: Ready status

        Returns:
            True if status was updated, False otherwise
        """
        async with self._lock:
            if player_id not in self.players:
                return False

            self.players[player_id].is_ready = ready
            return True

    def all_players_ready(self) -> bool:
        """Check if all players are ready to start."""
        if len(self.players) == 0:
            return False
        return all(p.is_ready for p in self.players.values())

    async def start_game(self, seed: Optional[int] = None) -> bool:
        """Start the game session.

        Args:
            seed: Optional random seed for dungeon generation

        Returns:
            True if game was started, False otherwise
        """
        async with self._lock:
            if self.is_started or self.is_finished:
                return False

            if len(self.players) == 0:
                return False

            # Create multiplayer game state
            self.mp_game_state = MultiplayerGameState(
                seed=seed, max_players=self.max_players
            )

            # Add all players to the game
            for player_id, player_info in self.players.items():
                success = self.mp_game_state.add_player(
                    player_id, player_info.player_name, player_info.player_class
                )
                if success:
                    # Store entity ID in player info
                    entity_id = self.mp_game_state.get_player_entity_id(player_id)
                    player_info.entity_id = entity_id
                else:
                    logger.error(f"Failed to add player {player_info.player_name}")

            # Initialize game context and AI system
            if self.mp_game_state.game_state:
                self.game_context = GameContext(self.mp_game_state.game_state)
                self.ai_system = AISystem(self.game_context)
                logger.info("Initialized GameContext and AISystem for multiplayer game")
            else:
                logger.error("Failed to initialize game state for multiplayer game")

            self.is_started = True
            logger.info(f"Game {self.game_id} started with {len(self.players)} players")

            return True

    def _apply_action_outcome(self, outcome, action_type: str) -> bool:
        """Run a successful action's outcome through the pipeline shared with single-player.

        VB-4: floor descent used to be dropped entirely. VB-24: messages and events
        were dropped too, and free actions were counted against the round quota.

        Returns:
            True if the action consumed a turn (and so counts toward the round).
        """
        return process_action_outcome(
            outcome,
            action_type,
            add_message=self.mp_game_state.add_message,
            on_descend_floor=self.mp_game_state.descend_floor,
            event_bus=self.event_bus,
        )

    async def _advance_round_if_complete(self) -> None:
        """Run the monster turn and roll the round counter once the action quota is hit.

        Also updates alive status and propagates game-over into session state
        so the session stops accepting actions and can be cleaned up.
        """
        if self.mp_game_state.actions_this_round >= self.actions_per_round:
            await self._process_monster_turn()
            self.mp_game_state.increment_round()

        newly_dead = self.mp_game_state.update_player_alive_status()
        self._record_scores(newly_dead)

        if self.mp_game_state.game_state.game_over:
            self.is_finished = True
            # Survivors are scored when the run ends (victory or wipe)
            self._record_scores(self.mp_game_state.player_slots.values())

    def _record_scores(self, slots) -> None:
        """Record each given player's run on the multiplayer leaderboard, once.

        Players are scored the moment they die, survivors when the game ends.
        Never raises: a leaderboard failure must not break the game.
        """
        game_state = self.mp_game_state.game_state
        for slot in slots:
            if slot.player_id in self._scored_player_ids or not slot.player_entity:
                continue
            self._scored_player_ids.add(slot.player_id)

            try:
                hsm = self._high_scores or HighScoreManager.get_multiplayer_instance()
                entry = HighScoreEntry.from_game_state(
                    game_state, slot.player_name, player=slot.player_entity
                )
                rank = hsm.add_score(entry)

                if rank > 0:
                    self.mp_game_state.add_message(
                        f"{slot.player_name}'s final score: {entry.score} "
                        f"(co-op rank #{rank})"
                    )
                logger.info(
                    f"Co-op high score recorded: {slot.player_name} scored "
                    f"{entry.score} (rank #{rank}) in game {self.game_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to record co-op high score for {slot.player_name}: {e}",
                    exc_info=True,
                )

    async def process_action(
        self, player_id: str, action: Action
    ) -> tuple[bool, Optional[str]]:
        """Process a player action.

        Args:
            player_id: Player performing the action
            action: Action to process

        Returns:
            Tuple of (success, error_message)
        """
        async with self._lock:
            if not self.is_started or self.is_finished:
                return False, "Game is not active"

            if player_id not in self.players:
                return False, "Player not in game"

            # Check if player is disconnected - reject action from disconnected players
            player_info = self.players[player_id]
            if player_info.is_disconnected():
                return False, "Player is disconnected - AI is controlling this character"

            if not self.mp_game_state or not self.mp_game_state.game_state:
                return False, "Game state not initialized"

            # Validate action belongs to player
            if player_info.entity_id and action.actor_id != player_info.entity_id:
                return False, "Action actor does not match player entity"

            # Execute action against a GameContext (not raw GameState)
            try:
                context = GameContext(self.mp_game_state.game_state)
                outcome = action.execute(context)
                if not outcome.is_success:
                    return False, "; ".join(outcome.messages) or "Action failed"

                if self._apply_action_outcome(outcome, action.get_action_type()):
                    self.mp_game_state.increment_actions()
                await self._advance_round_if_complete()

                return True, None

            except Exception as e:
                logger.error(f"Action execution error: {e}", exc_info=True)
                return False, f"Action execution failed: {str(e)}"

    async def process_disconnected_player_action(
        self, player_id: str
    ) -> tuple[bool, Optional[str]]:
        """Process an AI-controlled action for a disconnected player.

        This method generates a defensive "wait" action for disconnected players.

        Args:
            player_id: Disconnected player ID

        Returns:
            Tuple of (success, error_message)
        """
        async with self._lock:
            if not self.is_started or self.is_finished:
                return False, "Game is not active"

            if player_id not in self.players:
                return False, "Player not in game"

            player_info = self.players[player_id]

            if not player_info.is_disconnected():
                return False, "Player is not disconnected"

            if not self.mp_game_state or not self.mp_game_state.game_state:
                return False, "Game state not initialized"

            try:
                wait_action = WaitAction(actor_id=player_info.entity_id)
                context = GameContext(self.mp_game_state.game_state)
                outcome = wait_action.execute(context)

                if not outcome.is_success:
                    message = "; ".join(outcome.messages) or "AI wait action failed"
                    logger.warning(
                        f"AI action for disconnected player {player_info.player_name} "
                        f"failed: {message}"
                    )
                    return False, message

                if self._apply_action_outcome(outcome, "wait"):
                    self.mp_game_state.increment_actions()

                logger.debug(
                    f"AI executed wait action for disconnected player {player_info.player_name}"
                )

                await self._advance_round_if_complete()

                return True, None

            except Exception as e:
                logger.error(
                    f"Error processing AI action for disconnected player: {e}",
                    exc_info=True
                )
                return False, f"AI action failed: {str(e)}"

    def get_disconnected_players(self) -> List[str]:
        """Get list of disconnected player IDs.

        Returns:
            List of player IDs who are disconnected
        """
        return [
            player_id
            for player_id, player_info in self.players.items()
            if player_info.is_disconnected() and player_info.is_alive
        ]

    async def _process_monster_turn(self) -> None:
        """Process all monster actions for the current round."""
        if not self.mp_game_state or not self.mp_game_state.game_state:
            return

        # Run AI system to process monster turns
        if self.ai_system:
            try:
                self.ai_system.update()
                logger.debug("Processed monster turns via AI system")
            except Exception as e:
                logger.error(f"Error processing monster turns: {e}", exc_info=True)
        else:
            logger.warning("AI system not initialized, skipping monster turn")

        # Increment turn count
        self.mp_game_state.game_state.turn_count += 1

        # Natural HP regeneration for every living player
        self.mp_game_state.apply_hp_regeneration()

        # Clean up dead entities
        self.mp_game_state.game_state.cleanup_dead_entities()

    def get_state_dict(self, use_delta: Optional[bool] = None) -> Dict:
        """Get the current game state as a dictionary.

        Args:
            use_delta: Whether to use delta compression (defaults to self.use_delta_compression)

        Returns:
            Dictionary representation of game state or delta
        """
        base_state = {
            "game_id": self.game_id,
            "game_name": self.game_name,
            "is_started": self.is_started,
            "is_finished": self.is_finished,
            "actions_per_round": self.actions_per_round,
        }

        if self.mp_game_state:
            # Include detailed game state
            game_state = self.mp_game_state.get_state_dict()
            base_state.update(game_state)
        else:
            # Game not started yet
            base_state["players"] = [
                {
                    "player_id": p.player_id,
                    "player_name": p.player_name,
                    "player_class": p.player_class,
                    "is_ready": p.is_ready,
                }
                for p in self.players.values()
            ]

        # Apply delta compression if enabled
        if use_delta is None:
            use_delta = self.use_delta_compression

        if use_delta and self.is_started:
            delta = StateDelta.compute_delta(self.last_state, base_state)

            # Update last state
            self.last_state = base_state.copy()

            # Log compression ratio
            if logger.isEnabledFor(logging.DEBUG):
                StateDelta.estimate_compression_ratio(self.last_state, base_state, delta)

            return delta
        else:
            # First state or delta disabled - send full state
            self.last_state = base_state.copy()
            return base_state

    def get_player_count(self) -> int:
        """Get the number of players in the game."""
        return len(self.players)

    def get_player_names(self) -> List[str]:
        """Get list of player names."""
        return [p.player_name for p in self.players.values()]

    def reset_state_tracking(self) -> None:
        """Reset state tracking for delta compression.

        This forces the next state broadcast to be a full state.
        Useful when a player reconnects and needs the full state.
        """
        self.last_state = None
        logger.debug(f"Reset state tracking for game {self.game_id}")
