"""
Configuration loader - loads game configuration from YAML files.

Provides centralized access to all game configuration:
- Monster spawn weights and counts
- Ore vein distribution
- Game constants and balance values

Usage:
    config = ConfigLoader.load()
    monster_count = config.get_monster_count_for_floor(5)
    spawn_weights = config.get_monster_spawn_weights(5)
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..exceptions import ContentValidationError

logger = logging.getLogger(__name__)


@dataclass
class GameConfig:
    """
    Game configuration container.

    Provides high-level API for accessing configuration data
    loaded from YAML files.
    """

    monster_spawns: Dict[str, Any]
    ore_veins: Dict[str, Any]
    game_constants: Dict[str, Any]
    spawning: Dict[str, Any]

    def get_monster_count_for_floor(self, floor: int) -> int:
        """
        Calculate how many monsters should spawn on a given floor.

        Args:
            floor: Floor number (1-based)

        Returns:
            Number of monsters to spawn
        """
        counts = self.monster_spawns['monster_counts']

        if 1 <= floor <= 6:
            # Floors 1-6: base + (floor // divisor)
            config = counts['floors_1_6']
            return config['base'] + (floor // config['divisor'])

        elif 7 <= floor <= 20:
            # Floors 7-20: base + (floor // divisor)
            config = counts['floors_7_20']
            return config['base'] + (floor // config['divisor'])

        else:
            # Floors 21+: min(max, base + (floor // divisor))
            config = counts['floors_21_plus']
            count = config['base'] + (floor // config['divisor'])
            return min(config['max'], count)

    def get_monster_spawn_weights(self, floor: int) -> Dict[str, int]:
        """
        Get monster spawn weights for a given floor.

        Args:
            floor: Floor number (1-based)

        Returns:
            Dictionary of monster_type -> weight
        """
        weights = self.monster_spawns['spawn_weights']

        if floor == 1:
            return weights['floor_1']
        elif floor == 2:
            return weights['floor_2']
        elif 3 <= floor <= 5:
            return weights['floors_3_5']
        elif 6 <= floor <= 10:
            return weights['floors_6_10']
        else:
            return weights['floors_11_plus']

    def get_ore_vein_count_for_floor(self, floor: int) -> int:
        """
        Calculate how many ore veins should spawn on a given floor.

        Args:
            floor: Floor number (1-based)

        Returns:
            Number of ore veins to spawn
        """
        config = self.ore_veins['ore_vein_counts']
        # Formula: base + (floor - 1)
        return config['base'] + (floor - 1)

    def get_ore_spawn_weights(self, floor: int) -> Dict[str, int]:
        """
        Get ore type spawn weights for a given floor.

        Args:
            floor: Floor number (1-based)

        Returns:
            Dictionary of ore_type -> weight
        """
        weights = self.ore_veins['spawn_weights']

        if 1 <= floor <= 3:
            return weights['floors_1_3']
        elif 4 <= floor <= 6:
            return weights['floors_4_6']
        else:
            return weights['floors_7_plus']

    def get_constant(self, path: str, default: Any = None) -> Any:
        """
        Get a constant value by dot-separated path.

        Args:
            path: Dot-separated path (e.g., 'player.starting_stats.hp')
            default: Default value if path not found

        Returns:
            Value at path or default
        """
        parts = path.split('.')
        value = self.game_constants

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def get_special_room_config(self, room_type: str) -> Dict[str, Any]:
        """
        Get spawning configuration for a special room type.

        Args:
            room_type: Type of special room (treasure_room, monster_den, ore_chamber)

        Returns:
            Dictionary containing spawn configuration for that room type
        """
        return self.spawning['special_rooms'].get(room_type, {})

    def get_ore_positioning_config(self) -> Dict[str, Any]:
        """
        Get ore vein positioning configuration.

        Returns:
            Dictionary containing ore positioning rules
        """
        return self.spawning['ore_positioning']

    def get_special_room_assignment_config(self) -> Dict[str, Any]:
        """
        Get special room assignment configuration.

        Returns:
            Dictionary containing room assignment rules and weights
        """
        return self.spawning['special_room_assignment']

    def get_monster_density_multiplier(self, floor: int) -> float:
        """
        Get the monster density multiplier for a given floor.

        This allows global or tier-based adjustments to monster counts.

        Args:
            floor: Floor number (1-based)

        Returns:
            Multiplier to apply to monster counts
        """
        density_config = self.spawning['monster_density']
        global_mult = density_config['global_multiplier']

        # Check tier-specific multipliers
        tier_mults = density_config['tier_multipliers']
        if 1 <= floor <= 6:
            tier_mult = tier_mults['early_game']['multiplier']
        elif 7 <= floor <= 20:
            tier_mult = tier_mults['mid_game']['multiplier']
        else:
            tier_mult = tier_mults['late_game']['multiplier']

        return global_mult * tier_mult


class ConfigLoader:
    """
    Loads game configuration from YAML files.

    Singleton pattern - loads configuration once and caches it.
    """

    _instance: Optional[GameConfig] = None

    @classmethod
    def load(cls, config_dir: Optional[Path] = None) -> GameConfig:
        """
        Load configuration from YAML files.

        Args:
            config_dir: Path to data/balance directory (auto-detected if None)

        Returns:
            GameConfig instance
        """
        if cls._instance is not None:
            return cls._instance

        if config_dir is None:
            # Auto-detect config directory (assume we're in src/core/config/)
            this_file = Path(__file__)
            project_root = this_file.parent.parent.parent.parent
            config_dir = project_root / "data" / "balance"

        logger.info(f"Loading configuration from {config_dir}")

        # Load YAML files
        monster_spawns = cls._load_yaml(config_dir / "monster_spawns.yaml")
        ore_veins = cls._load_yaml(config_dir / "ore_veins.yaml")
        game_constants = cls._load_yaml(config_dir / "game_constants.yaml")
        spawning = cls._load_yaml(config_dir / "spawning.yaml")

        cls._instance = GameConfig(
            monster_spawns=monster_spawns,
            ore_veins=ore_veins,
            game_constants=game_constants,
            spawning=spawning,
        )

        logger.info("Configuration loaded successfully")
        return cls._instance

    @classmethod
    def reload(cls, config_dir: Optional[Path] = None) -> GameConfig:
        """
        Force reload of configuration (for testing).

        Args:
            config_dir: Path to data/balance directory

        Returns:
            Newly loaded GameConfig instance
        """
        cls._instance = None
        return cls.load(config_dir)

    @staticmethod
    def _load_yaml(file_path: Path) -> Dict[str, Any]:
        """
        Load a YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML data as dictionary

        Raises:
            ContentValidationError: If file doesn't exist
            yaml.YAMLError: If YAML is malformed
        """
        if not file_path.exists():
            raise ContentValidationError(
                f"Config file not found: {file_path}",
                path=str(file_path)
            )

        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        logger.debug(f"Loaded config file: {file_path}")
        return data or {}
