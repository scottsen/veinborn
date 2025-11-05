"""
Brogue Configuration System

Provides two configuration systems:
1. ConfigLoader - Game balance/data configuration from YAML files
2. ConfigManager - User preferences from ~/.broguerc file

Usage:
    # Game balance config
    game_config = ConfigLoader.load()
    monster_count = game_config.get_monster_count_for_floor(5)

    # User preferences config
    user_config = ConfigManager.get_instance()
    player_name = user_config.get('player.name', 'Anonymous')
"""

from .config_loader import ConfigLoader, GameConfig
from .user_config import ConfigManager, get_player_name

__all__ = [
    'ConfigLoader',
    'GameConfig',
    'ConfigManager',
    'get_player_name',
]
