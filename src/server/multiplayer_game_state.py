"""Multiplayer-aware GameState wrapper.

Extends the single-player GameState to support multiple players
while maintaining compatibility with existing single-player code.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

from core.game_state import GameState
from core.entities import Player
from core.base.entity import Entity

logger = logging.getLogger(__name__)


@dataclass
class PlayerSlot:
    """Represents a player slot in a multiplayer game."""

    player_id: str  # Unique player ID from session
    player_name: str
    player_entity: Player
    entity_id: str  # The entity ID in the game state
    is_active: bool = True
    is_alive: bool = True


class MultiplayerGameState:
    """Wrapper around GameState for multiplayer support.

    This class:
    - Manages multiple players in a single game
    - Routes actions to the correct player entities
    - Maintains compatibility with single-player GameState
    - Handles player-specific views and state
    """

    def __init__(self, seed: Optional[int] = None, max_players: int = 4):
        """Initialize multiplayer game state.

        Args:
            seed: Random seed for dungeon generation
            max_players: Maximum number of players
        """
        self.max_players = max_players

        # Player management
        self.player_slots: Dict[str, PlayerSlot] = {}
        self.entity_to_player: Dict[str, str] = {}  # entity_id -> player_id

        # Core game state (initially single-player)
        # We'll initialize this when first player joins
        self.game_state: Optional[GameState] = None
        self.seed = seed

        # Multiplayer state
        self.is_multiplayer = True
        self.actions_this_round = 0
        self.round_number = 0

    def add_player(
        self, player_id: str, player_name: str, player_class: str = "warrior"
    ) -> bool:
        """Add a player to the game.

        Args:
            player_id: Unique player ID
            player_name: Display name
            player_class: Player class (warrior, mage, rogue, healer)

        Returns:
            True if player was added successfully
        """
        if len(self.player_slots) >= self.max_players:
            logger.warning(f"Cannot add player {player_name}: game is full")
            return False

        if player_id in self.player_slots:
            logger.warning(f"Player {player_id} already in game")
            return False

        # Create player entity
        # TODO: Use proper player class initialization
        player_entity = Player(name=player_name, x=0, y=0)

        # If this is the first player, initialize GameState
        if self.game_state is None:
            self.game_state = GameState(
                player=player_entity,
                seed=self.seed,
                player_name=player_name,
            )
            entity_id = "player"  # Single player uses "player" as ID
        else:
            # Additional players get unique IDs
            entity_id = f"player_{player_id[:8]}"
            # Add to entities dict
            self.game_state.entities[entity_id] = player_entity

        # Create player slot
        slot = PlayerSlot(
            player_id=player_id,
            player_name=player_name,
            player_entity=player_entity,
            entity_id=entity_id,
        )

        self.player_slots[player_id] = slot
        self.entity_to_player[entity_id] = player_id

        logger.info(f"Added player {player_name} (ID: {player_id}, entity: {entity_id})")
        return True

    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the game.

        Args:
            player_id: Player to remove

        Returns:
            True if player was removed
        """
        if player_id not in self.player_slots:
            return False

        slot = self.player_slots[player_id]
        slot.is_active = False

        # Mark entity as inactive (don't remove for game integrity)
        # In future, this could trigger player death or spectator mode

        logger.info(f"Removed player {slot.player_name} (ID: {player_id})")
        return True

    def get_player_entity(self, player_id: str) -> Optional[Player]:
        """Get the entity for a specific player.

        Args:
            player_id: Player ID

        Returns:
            Player entity or None
        """
        slot = self.player_slots.get(player_id)
        if not slot:
            return None

        return slot.player_entity

    def get_player_entity_id(self, player_id: str) -> Optional[str]:
        """Get the entity ID for a player.

        Args:
            player_id: Player ID

        Returns:
            Entity ID or None
        """
        slot = self.player_slots.get(player_id)
        if not slot:
            return None

        return slot.entity_id

    def get_all_players(self) -> List[PlayerSlot]:
        """Get all active players.

        Returns:
            List of active player slots
        """
        return [slot for slot in self.player_slots.values() if slot.is_active]

    def get_player_count(self) -> int:
        """Get number of active players."""
        return sum(1 for slot in self.player_slots.values() if slot.is_active)

    def is_player_action(self, entity_id: str) -> bool:
        """Check if an entity belongs to a player.

        Args:
            entity_id: Entity ID to check

        Returns:
            True if entity is a player
        """
        return entity_id in self.entity_to_player

    def get_state_dict(self) -> Dict:
        """Get game state as a dictionary for serialization.

        Returns:
            Dictionary representation of game state
        """
        if not self.game_state:
            return {
                "initialized": False,
                "player_count": 0,
            }

        # Build player info
        players_info = []
        for slot in self.player_slots.values():
            player_entity = slot.player_entity
            players_info.append(
                {
                    "player_id": slot.player_id,
                    "player_name": slot.player_name,
                    "entity_id": slot.entity_id,
                    "is_active": slot.is_active,
                    "is_alive": slot.is_alive,
                    "position": {
                        "x": player_entity.x,
                        "y": player_entity.y,
                    },
                    "health": {
                        "current": player_entity.hp,
                        "max": player_entity.max_hp,
                    },
                }
            )

        return {
            "initialized": True,
            "is_multiplayer": self.is_multiplayer,
            "player_count": self.get_player_count(),
            "max_players": self.max_players,
            "players": players_info,
            "turn_count": self.game_state.turn_count,
            "current_floor": self.game_state.current_floor,
            "round_number": self.round_number,
            "actions_this_round": self.actions_this_round,
            "game_over": self.game_state.game_over,
            "victory": self.game_state.victory,
            "recent_messages": self.game_state.get_recent_messages(20),
        }

    def to_dict(self) -> Dict:
        """Alias for get_state_dict for compatibility."""
        return self.get_state_dict()

    def add_message(self, message: str) -> None:
        """Add a message to the game log.

        Args:
            message: Message to add
        """
        if self.game_state:
            self.game_state.add_message(message)

    def increment_round(self) -> None:
        """Increment the round counter and reset actions."""
        self.round_number += 1
        self.actions_this_round = 0
        logger.debug(f"Round {self.round_number} started")

    def increment_actions(self) -> int:
        """Increment action counter and return current count.

        Returns:
            Current action count for this round
        """
        self.actions_this_round += 1
        return self.actions_this_round

    def update_player_alive_status(self) -> None:
        """Update alive status for all players based on their entities."""
        for slot in self.player_slots.values():
            if slot.player_entity:
                slot.is_alive = slot.player_entity.is_alive

        # Check if all players are dead
        if self.game_state and all(
            not slot.is_alive for slot in self.player_slots.values()
        ):
            self.game_state.game_over = True
            self.add_message("All players have died. Game over!")

    def get_active_player_count(self) -> int:
        """Get count of active, alive players."""
        return sum(
            1
            for slot in self.player_slots.values()
            if slot.is_active and slot.is_alive
        )
