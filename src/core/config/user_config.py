"""
User Configuration Manager

NetHack-style configuration system with ENV VAR overrides.

Features:
- Multiple config file locations (~/.veinbornrc, XDG, /etc)
- ENV VAR overrides (VEINBORN_PLAYER_NAME, etc.)
- INI format (human-readable)
- Type-safe getters (get, get_bool, get_int)
- Save/create functionality
"""

from pathlib import Path
from typing import Optional, Any
import configparser
import logging
import os

from ..exceptions import DataError

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages user configuration (NetHack-style .veinbornrc).

    Priority order for resolution:
    1. ENV VARs (VEINBORN_*)
    2. Config file (~/.veinbornrc or XDG)
    3. Defaults

    Example:
        >>> config = ConfigManager.get_instance()
        >>> name = config.get('player.name', 'Anonymous')
        >>> autopickup = config.get_bool('game.autopickup', True)
    """

    _instance: Optional['ConfigManager'] = None

    CONFIG_PATHS = [
        Path.home() / ".veinbornrc",                        # Classic Unix style (preferred)
        Path.home() / ".config" / "veinborn" / "config",    # XDG style (preferred)
        Path("/etc/veinbornrc"),                            # System-wide (preferred)
        # Legacy paths (deprecated, will be removed in v0.5.0)
        Path.home() / ".veinbornrc",                          # Legacy Unix style
        Path.home() / ".config" / "veinborn" / "config",      # Legacy XDG style
        Path("/etc/veinbornrc"),                              # Legacy system-wide
    ]

    def __init__(self):
        """Initialize config manager and load configuration."""
        self.config = configparser.ConfigParser()
        self.config_file: Optional[Path] = None
        self.load()

    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """
        Get singleton instance.

        Returns:
            ConfigManager singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (for testing)."""
        cls._instance = None

    def load(self) -> None:
        """Load config from first available file."""
        import warnings

        # Legacy config paths (for deprecation warnings)
        legacy_paths = {
            Path.home() / ".veinbornrc",
            Path.home() / ".config" / "veinborn" / "config",
            Path("/etc/veinbornrc"),
        }

        for path in self.CONFIG_PATHS:
            if path.exists():
                try:
                    self.config.read(path)
                    self.config_file = path
                    logger.info(f"Loaded config from {path}")

                    # Warn if using legacy config file
                    if path in legacy_paths:
                        new_path = str(path).replace("veinborn", "veinborn")
                        warnings.warn(
                            f"Config file {path} is deprecated. "
                            f"Please rename it to {new_path}. "
                            f"Support for legacy config files will be removed in v0.5.0.",
                            DeprecationWarning,
                            stacklevel=2
                        )

                    return
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

        logger.info("No config file found, using defaults")

    def get(self, key: str, default: Any = None) -> Optional[str]:
        """
        Get config value by dot-separated key.

        Priority:
        1. ENV VAR (VEINBORN_PLAYER_NAME for player.name)
        2. Config file value
        3. Default parameter

        Args:
            key: Config key (e.g., 'player.name', 'game.default_seed')
            default: Default value if not found

        Returns:
            Config value or default

        Example:
            >>> config.get('player.name')
            'Alice'
            >>> config.get('player.name', 'Anonymous')
            'Alice' or 'Anonymous' if not set
        """
        # Check ENV VAR override first (convert key to ENV format)
        # player.name -> VEINBORN_PLAYER_NAME
        env_key = f"VEINBORN_{key.upper().replace('.', '_')}"
        if env_value := os.getenv(env_key):
            return env_value

        # Parse section.key
        if '.' not in key:
            return default

        section, option = key.split('.', 1)

        if not self.config.has_section(section):
            return default

        if not self.config.has_option(section, option):
            return default

        value = self.config.get(section, option)
        # Return default if value is empty string
        return value if value else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get boolean config value.

        Recognizes: true/yes/1/on as True (case-insensitive)

        Args:
            key: Config key
            default: Default value

        Returns:
            Boolean value
        """
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ('true', 'yes', '1', 'on')

    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get integer config value.

        Args:
            key: Config key
            default: Default value

        Returns:
            Integer value or default if conversion fails
        """
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}")
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set config value (in-memory only, use save() to persist).

        Args:
            key: Config key (e.g., 'player.name')
            value: Value to set

        Example:
            >>> config.set('player.name', 'Alice')
            >>> config.save()
        """
        if '.' not in key:
            raise DataError(
                f"Invalid config key: {key} (must be section.option)",
                key=key
            )

        section, option = key.split('.', 1)

        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, option, str(value))

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save config to file.

        Args:
            path: File path (default: first writable path)
        """
        if path is None:
            # Use existing config file or first writable path
            if self.config_file and self.config_file != Path("/etc/veinbornrc"):
                path = self.config_file
            else:
                # Try first two paths (skip /etc - read-only)
                for p in self.CONFIG_PATHS[:2]:
                    try:
                        p.parent.mkdir(parents=True, exist_ok=True)
                        path = p
                        break
                    except PermissionError:
                        continue

        if path is None:
            logger.error("No writable config path found")
            return

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                self.config.write(f)
            self.config_file = path
            logger.info(f"Saved config to {path}")
        except IOError as e:
            logger.error(f"Failed to save config: {e}")

    def create_default_config(self, path: Optional[Path] = None) -> None:
        """
        Create default config file with comments.

        Args:
            path: File path (default: ~/.veinbornrc)

        Example:
            >>> config.create_default_config()
            # Creates ~/.veinbornrc with default sections
        """
        if path is None:
            path = Path.home() / ".veinbornrc"

        default_config = """# Veinborn Configuration File
# Lines starting with # are comments

[player]
# Your player name (appears in high scores)
name =

# Default character class (warrior, rogue, mage)
default_class =

[game]
# Default seed for all games (leave empty for random)
default_seed =

# Autopickup settings
autopickup = true
autopickup_types = ore,food,weapon,gold

[display]
# Show damage numbers in combat
show_damage_numbers = true

# Color scheme (classic, modern, colorblind)
color_scheme = classic

[ui]
# Layout style (default, compact)
# See data/ui/layouts/README.md for details
# default: Classic stacked sidebar layout (RECOMMENDED)
layout = default

[keys]
# Custom keybindings (future feature)
# move_north = k
# move_south = j
"""

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write(default_config)
            self.config_file = path
            logger.info(f"Created default config at {path}")
            print(f"✅ Created default config at {path}")
            print(f"💡 Edit this file to set your player name and preferences")
        except IOError as e:
            logger.error(f"Failed to create default config: {e}")
            raise


def get_player_name(args=None) -> str:
    """
    Resolve player name with priority:
    1. ENV VAR (VEINBORN_PLAYER_NAME)
    2. Config file (~/.veinbornrc)
    3. Command-line argument (--name)
    4. Interactive prompt (if TTY)
    5. Default: "Anonymous"

    Args:
        args: Parsed command-line arguments (with 'name' attribute)

    Returns:
        Player name string
    """
    # 1. Check environment variable
    if name := os.getenv('VEINBORN_PLAYER_NAME'):
        return name

    # 2. Check config file
    config = ConfigManager.get_instance()
    if name := config.get('player.name'):
        return name

    # 3. Check CLI argument (if provided)
    if args and hasattr(args, 'name') and args.name:
        return args.name

    # 4. Interactive prompt (if terminal)
    import sys
    if sys.stdin.isatty():
        try:
            name = input("Enter your name (or press Enter for 'Anonymous'): ").strip()
            if name:
                return name
        except (EOFError, KeyboardInterrupt):
            pass

    # 5. Default
    return "Anonymous"
