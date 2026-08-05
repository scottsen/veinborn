"""GameSessionManager — manages all active game sessions."""

import asyncio
import logging
from typing import Dict, List, Optional
from uuid import uuid4

from .session import GameSession

logger = logging.getLogger(__name__)


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

    async def mark_player_left(self, player_id: str) -> tuple[bool, Optional[str]]:
        """Mark a player as having left their game (preserving the record).

        Unlike leave_game, this keeps the player in game.players with
        has_left() == True so the game can still track who participated.
        Cleans up the player→game mapping so the player can join a new game.
        Cleans up empty games (no connected or disconnected players remain).
        """
        async with self._lock:
            game_id = self._player_to_game.get(player_id)
            if not game_id:
                return False, "Player not in any game"

            game = self._games.get(game_id)
            if not game:
                return False, "Game not found"

            success = await game.leave_player(player_id)
            if not success:
                return False, "Failed to leave game"

            del self._player_to_game[player_id]

            # Clean up game only if everyone has left (not just disconnected)
            remaining = sum(
                1 for p in game.players.values() if not p.has_left()
            )
            if remaining == 0:
                del self._games[game_id]

            return True, None

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
