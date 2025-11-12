"""Game session management for multiplayer games."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from uuid import uuid4

from core.game_state import GameState
from core.base.action import Action
from server.messages import Message, MessageType
from server.multiplayer_game_state import MultiplayerGameState


@dataclass
class PlayerInfo:
    """Information about a player in a game session."""

    player_id: str
    player_name: str
    entity_id: Optional[str] = None
    is_ready: bool = False
    is_alive: bool = True
    joined_at: float = field(default_factory=time.time)


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

        # Turn management
        self.actions_this_round = 0
        self.pending_actions: asyncio.Queue = asyncio.Queue()

        # Locks
        self._lock = asyncio.Lock()

    def can_join(self) -> bool:
        """Check if the game can accept more players."""
        return (
            len(self.players) < self.max_players
            and not self.is_started
            and not self.is_finished
        )

    async def add_player(self, player_id: str, player_name: str) -> bool:
        """Add a player to the game session.

        Args:
            player_id: Unique player ID
            player_name: Player display name

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

            # If game is running and no players left, mark as finished
            if self.is_started and len(self.players) == 0:
                self.is_finished = True

            return True

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
                    player_id, player_info.player_name
                )
                if success:
                    # Store entity ID in player info
                    entity_id = self.mp_game_state.get_player_entity_id(player_id)
                    player_info.entity_id = entity_id
                else:
                    logger.error(f"Failed to add player {player_info.player_name}")

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

            if not self.mp_game_state or not self.mp_game_state.game_state:
                return False, "Game state not initialized"

            # Validate action belongs to player
            player_info = self.players[player_id]
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

    async def _process_monster_turn(self) -> None:
        """Process all monster actions for the current round."""
        if not self.mp_game_state or not self.mp_game_state.game_state:
            return

        # TODO: Implement monster AI turn processing
        # This will integrate with the existing AI system
        # For now, just increment turn count
        self.mp_game_state.game_state.turn_count += 1
        pass

    def get_state_dict(self) -> Dict:
        """Get the current game state as a dictionary.

        Returns:
            Dictionary representation of game state
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
                    "is_ready": p.is_ready,
                }
                for p in self.players.values()
            ]

        return base_state

    def get_player_count(self) -> int:
        """Get the number of players in the game."""
        return len(self.players)

    def get_player_names(self) -> List[str]:
        """Get list of player names."""
        return [p.player_name for p in self.players.values()]


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
        self, game_id: str, player_id: str, player_name: str
    ) -> tuple[bool, Optional[str]]:
        """Join a player to a game.

        Args:
            game_id: Game to join
            player_id: Player ID
            player_name: Player name

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

            success = await game.add_player(player_id, player_name)
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
