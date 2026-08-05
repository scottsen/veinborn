"""Player connection state within a game session."""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

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
