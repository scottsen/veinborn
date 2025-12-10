"""Server configuration and settings."""

import os
import warnings
from dataclasses import dataclass
from typing import Optional


def _get_env_with_fallback(new_key: str, old_key: str, default: str) -> str:
    """Get environment variable with backward compatibility.

    Checks new key first (VEINBORN_*), then falls back to old key (BROGUE_*)
    with a deprecation warning, finally uses the default value.

    Args:
        new_key: New environment variable name (VEINBORN_*)
        old_key: Old environment variable name (BROGUE_*)
        default: Default value if neither is set

    Returns:
        The environment variable value or default
    """
    value = os.getenv(new_key)
    if value is not None:
        return value

    value = os.getenv(old_key)
    if value is not None:
        warnings.warn(
            f"{old_key} is deprecated, use {new_key} instead. "
            f"Support for {old_key} will be removed in v0.5.0.",
            DeprecationWarning,
            stacklevel=3
        )
        return value

    return default


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
        """Load configuration from environment variables.

        Supports both VEINBORN_* (preferred) and BROGUE_* (deprecated) variables.
        BROGUE_* variables will emit deprecation warnings and will be removed in v0.5.0.
        """
        return cls(
            host=_get_env_with_fallback("VEINBORN_HOST", "BROGUE_HOST", "0.0.0.0"),
            port=int(_get_env_with_fallback("VEINBORN_PORT", "BROGUE_PORT", "8765")),
            max_connections=int(_get_env_with_fallback("VEINBORN_MAX_CONNECTIONS", "BROGUE_MAX_CONNECTIONS", "100")),
            log_level=_get_env_with_fallback("VEINBORN_LOG_LEVEL", "BROGUE_LOG_LEVEL", "INFO"),
        )


# Global config instance
config = ServerConfig()
