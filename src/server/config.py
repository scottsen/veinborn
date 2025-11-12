"""Server configuration and settings."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerConfig:
    """Server configuration settings."""

    # Network settings
    host: str = "0.0.0.0"
    port: int = 8765

    # Security
    max_connections: int = 100
    max_players_per_game: int = 8
    auth_token_expiry: int = 86400  # 24 hours in seconds

    # Performance
    tick_rate: int = 10  # Game updates per second
    max_message_size: int = 1024 * 1024  # 1MB

    # Timeouts
    connection_timeout: int = 30
    action_timeout: int = 60
    idle_timeout: int = 300  # 5 minutes

    # Game settings
    actions_per_round: int = 4
    min_players: int = 1
    max_players: int = 4

    # Database (for future use)
    db_url: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("BROGUE_HOST", "0.0.0.0"),
            port=int(os.getenv("BROGUE_PORT", "8765")),
            max_connections=int(os.getenv("BROGUE_MAX_CONNECTIONS", "100")),
            log_level=os.getenv("BROGUE_LOG_LEVEL", "INFO"),
        )


# Global config instance
config = ServerConfig()
