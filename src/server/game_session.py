"""Game session management for multiplayer games."""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import uuid4

from core.game_state import GameState
from core.base.action import Action
from core.base.game_context import GameContext
from core.systems.ai_system import AISystem
from server.messages import Message, MessageType
from server.multiplayer_game_state import MultiplayerGameState
from server.state_delta import StateDelta

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Player connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    LEFT = "left"


@dataclass
class PlayerInfo:
    """Information about a player in a game session."""

    player_id: str
    player_name: str
    player_class: str = "warrior"  # Character class (warrior, mage, rogue, healer)
    entity_id: Optional[str] = None
    is_ready: bool = False
    is_alive: bool = True
    joined_at: float = field(default_factory=time.time)

    # Reconnection handling
    connection_status: ConnectionStatus = ConnectionStatus.CONNECTED
    disconnected_at: Optional[float] = None
    reconnect_timeout_seconds: int = 120  # 2 minutes default

    def mark_disconnected(self) -> None:
        """Mark player as disconnected."""
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.disconnected_at = time.time()
        logger.info(f"Player {self.player_name} marked as disconnected")

    def mark_reconnected(self) -> None:
        """Mark player as reconnected."""
        self.connection_status = ConnectionStatus.CONNECTED
        self.disconnected_at = None
        logger.info(f"Player {self.player_name} reconnected successfully")

    def mark_left(self) -> None:
        """Mark player as having left the game."""
        self.connection_status = ConnectionStatus.LEFT
        logger.info(f"Player {self.player_name} left the game")

    def is_connected(self) -> bool:
        """Check if player is currently connected."""
        return self.connection_status == ConnectionStatus.CONNECTED

    def is_disconnected(self) -> bool:
        """Check if player is disconnected but can rejoin."""
        return self.connection_status == ConnectionStatus.DISCONNECTED

    def has_left(self) -> bool:
        """Check if player has permanently left."""
        return self.connection_status == ConnectionStatus.LEFT

    def is_reconnect_timeout_expired(self) -> bool:
        """Check if reconnection timeout has expired."""
        if not self.is_disconnected() or self.disconnected_at is None:
            return False

        elapsed = time.time() - self.disconnected_at
        return elapsed > self.reconnect_timeout_seconds


class GameSession:
    """Manages a single multiplayer game instance."""

    def __init__(
        self,
        game_id: str,
        game_name: str,
        max_players: int = 4,
        actions_per_round: int = 4,
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

        # Turn management
        self.actions_this_round = 0
        self.pending_actions: asyncio.Queue = asyncio.Queue()

        # State tracking for delta compression
        self.last_state: Optional[Dict] = None
        self.use_delta_compression = True  # Enable/disable delta compression

        # Locks
        self._lock = asyncio.Lock()

    def can_join(self) -> bool:
        """Check if the game can accept more players."""
        return (
            len(self.players) < self.max_players
            and not self.is_started
            and not self.is_finished
        )

    async def add_player(self, player_id: str, player_name: str, player_class: str = "warrior") -> bool:
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
                if player_info.is_reconnect_timeout_expired():
                    logger.info(
                        f"Removing player {player_info.player_name} from game {self.game_id} "
                        f"due to reconnection timeout"
                    )
                    await self.remove_player(player_id)
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

            # Execute action
            try:
                outcome = action.execute(self.mp_game_state.game_state)
                if not outcome.success:
                    return False, outcome.message

                # Increment action counter
                self.mp_game_state.increment_actions()

                # Check if round is complete
                if self.mp_game_state.actions_this_round >= self.actions_per_round:
                    await self._process_monster_turn()
                    self.mp_game_state.increment_round()

                # Update player alive status
                self.mp_game_state.update_player_alive_status()

                return True, None

            except Exception as e:
                logger.error(f"Action execution error: {e}", exc_info=True)
                return False, f"Action execution failed: {str(e)}"

    async def process_disconnected_player_action(self, player_id: str) -> tuple[bool, Optional[str]]:
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

            # Import WaitAction here to avoid circular imports
            from core.actions.wait_action import WaitAction

            # Generate a defensive wait action for the disconnected player
            try:
                wait_action = WaitAction(actor_id=player_info.entity_id)
                outcome = wait_action.execute(self.mp_game_state.game_state)

                if not outcome.success:
                    logger.warning(
                        f"AI action for disconnected player {player_info.player_name} failed: {outcome.message}"
                    )
                    return False, outcome.message

                # Increment action counter
                self.mp_game_state.increment_actions()

                logger.debug(
                    f"AI executed wait action for disconnected player {player_info.player_name}"
                )

                # Check if round is complete
                if self.mp_game_state.actions_this_round >= self.actions_per_round:
                    await self._process_monster_turn()
                    self.mp_game_state.increment_round()

                # Update player alive status
                self.mp_game_state.update_player_alive_status()

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

        # Clean up dead entities
        self.mp_game_state.game_state.cleanup_dead_entities()

    def get_state_dict(self, use_delta: bool = None) -> Dict:
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


class GameSessionManager:
    """Manages all active game sessions."""

    def __init__(self):
        self._games: Dict[str, GameSession] = {}
        self._player_to_game: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def create_game(
        self,
        game_name: str,
        max_players: int = 4,
        actions_per_round: int = 4,
    ) -> GameSession:
        """Create a new game session.

        Args:
            game_name: Name of the game
            max_players: Maximum number of players
            actions_per_round: Number of actions before monster turn

        Returns:
            Created game session
        """
        async with self._lock:
            game_id = str(uuid4())
            game = GameSession(
                game_id=game_id,
                game_name=game_name,
                max_players=max_players,
                actions_per_round=actions_per_round,
            )
            self._games[game_id] = game
            return game

    async def get_game(self, game_id: str) -> Optional[GameSession]:
        """Get a game session by ID."""
        return self._games.get(game_id)

    async def join_game(
        self, game_id: str, player_id: str, player_name: str, player_class: str = "warrior"
    ) -> tuple[bool, Optional[str]]:
        """Join a player to a game.

        Args:
            game_id: Game to join
            player_id: Player ID
            player_name: Player name
            player_class: Character class (warrior, mage, rogue, healer)

        Returns:
            Tuple of (success, error_message)
        """
        async with self._lock:
            game = self._games.get(game_id)
            if not game:
                return False, "Game not found"

            if not game.can_join():
                return False, "Game is full or already started"

            # Check if player is already in another game
            if player_id in self._player_to_game:
                return False, "Player is already in another game"

            success = await game.add_player(player_id, player_name, player_class)
            if success:
                self._player_to_game[player_id] = game_id
                return True, None
            else:
                return False, "Failed to join game"

    async def leave_game(self, player_id: str) -> tuple[bool, Optional[str]]:
        """Remove a player from their current game.

        Args:
            player_id: Player to remove

        Returns:
            Tuple of (success, error_message)
        """
        async with self._lock:
            game_id = self._player_to_game.get(player_id)
            if not game_id:
                return False, "Player not in any game"

            game = self._games.get(game_id)
            if not game:
                return False, "Game not found"

            success = await game.remove_player(player_id)
            if success:
                del self._player_to_game[player_id]

                # Clean up empty games
                if game.get_player_count() == 0:
                    del self._games[game_id]

                return True, None
            else:
                return False, "Failed to leave game"

    async def get_player_game(self, player_id: str) -> Optional[GameSession]:
        """Get the game a player is currently in.

        Args:
            player_id: Player ID

        Returns:
            Game session or None
        """
        game_id = self._player_to_game.get(player_id)
        if game_id:
            return self._games.get(game_id)
        return None

    def get_available_games(self) -> List[Dict]:
        """Get list of games that can be joined.

        Returns:
            List of game info dictionaries
        """
        return [
            {
                "game_id": game.game_id,
                "game_name": game.game_name,
                "player_count": game.get_player_count(),
                "max_players": game.max_players,
                "is_started": game.is_started,
            }
            for game in self._games.values()
            if game.can_join()
        ]

    def get_active_game_count(self) -> int:
        """Get count of active games."""
        return len(self._games)
