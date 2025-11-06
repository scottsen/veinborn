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
from typing import Dict, Any, List, Optional, Tuple
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
    ai_behaviors: Dict[str, Any]
    formulas: Dict[str, Any]
    dungeon_generation: Dict[str, Any]

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

    def get_ai_behavior_config(self, ai_type: str) -> Dict[str, Any]:
        """
        Get configuration for an AI behavior type.

        Args:
            ai_type: Type of AI behavior (aggressive, defensive, passive, etc.)

        Returns:
            Dictionary containing behavior parameters
        """
        behaviors = self.ai_behaviors.get('behaviors', {})
        return behaviors.get(ai_type, behaviors.get('aggressive', {}))

    def get_default_ai_for_monster(self, monster_type: str) -> str:
        """
        Get default AI type for a monster type.

        Args:
            monster_type: Monster type name (rat, goblin, etc.)

        Returns:
            AI type string (defaults to 'aggressive')
        """
        defaults = self.ai_behaviors.get('default_ai_by_type', {})
        return defaults.get(monster_type, 'aggressive')

    def get_damage_formula(self) -> str:
        """Get damage calculation formula."""
        return self.formulas['combat']['damage']['formula']

    def get_min_damage(self) -> int:
        """Get minimum damage value."""
        return self.formulas['combat']['damage']['min_damage']

    def get_mining_turns_formula(self) -> str:
        """Get mining turns calculation formula."""
        return self.formulas['mining']['formula']

    def get_mining_base_turns(self) -> int:
        """Get base mining turns."""
        return self.formulas['mining']['base_turns']

    def get_mining_min_turns(self) -> int:
        """Get minimum mining turns."""
        return self.formulas['mining']['min_turns']

    def get_mining_max_turns(self) -> int:
        """Get maximum mining turns."""
        return self.formulas['mining']['max_turns']

    def get_tier_multiplier(self, ore_type: str) -> float:
        """Get crafting tier multiplier for ore type."""
        return self.formulas['crafting']['tier_multipliers'].get(ore_type, 1.0)

    # Dungeon Generation Configuration Accessors

    def get_bsp_min_split_size(self) -> int:
        """
        Get minimum BSP cell size before stopping splits.

        Returns:
            Minimum size in tiles
        """
        return self.dungeon_generation['bsp']['min_split_size']

    def get_bsp_aspect_ratio_threshold(self) -> float:
        """
        Get aspect ratio threshold for BSP split direction.

        When a BSP cell's aspect ratio exceeds this threshold,
        the split direction is forced to reduce elongation.

        Returns:
            Aspect ratio threshold (e.g., 1.25)
        """
        return self.dungeon_generation['bsp']['aspect_ratio_threshold']

    def get_bsp_split_ratio_range(self) -> Tuple[float, float]:
        """
        Get BSP split position ratio range.

        Returns:
            Tuple of (min_ratio, max_ratio) for split positioning
        """
        split_ratio = self.dungeon_generation['bsp']['split_ratio']
        return (split_ratio['min'], split_ratio['max'])

    def get_room_min_size(self) -> int:
        """
        Get minimum room size.

        Returns:
            Minimum room dimension in tiles
        """
        return self.dungeon_generation['rooms']['min_size']

    def get_room_padding(self) -> int:
        """
        Get padding between rooms and BSP cell boundaries.

        Returns:
            Padding in tiles
        """
        return self.dungeon_generation['rooms']['padding']

    def get_corridor_style(self) -> str:
        """
        Get corridor generation style.

        Returns:
            Corridor style (e.g., 'l_shaped')
        """
        return self.dungeon_generation['corridors']['style']

    def get_corridor_direction_probability(self) -> float:
        """
        Get corridor direction choice probability.

        For L-shaped corridors, this is the probability of
        choosing horizontal-first vs vertical-first.

        Returns:
            Probability (0.0 to 1.0)
        """
        return self.dungeon_generation['corridors']['direction_probability']

    def get_dungeon_floor_overrides(self, floor: int) -> Dict[str, Any]:
        """
        Get dungeon configuration overrides for a specific floor.

        Args:
            floor: Floor number (1-based)

        Returns:
            Dictionary of overrides for the floor, or empty dict if none
        """
        overrides = self.dungeon_generation.get('floor_overrides', {})
        return overrides.get(f'floor_{floor}', {})

    def get_dungeon_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        Get a dungeon generation preset configuration.

        Args:
            preset_name: Name of preset (e.g., 'standard', 'small_cramped', 'maze')

        Returns:
            Dictionary containing preset configuration
        """
        presets = self.dungeon_generation.get('presets', {})
        return presets.get(preset_name, {})


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
        ai_behaviors = cls._load_yaml(config_dir / "ai_behaviors.yaml")
        formulas = cls._load_yaml(config_dir / "formulas.yaml")
        dungeon_generation = cls._load_yaml(config_dir / "dungeon_generation.yaml")

        cls._instance = GameConfig(
            monster_spawns=monster_spawns,
            ore_veins=ore_veins,
            game_constants=game_constants,
            spawning=spawning,
            ai_behaviors=ai_behaviors,
            formulas=formulas,
            dungeon_generation=dungeon_generation,
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

    @classmethod
    def get_config(cls) -> GameConfig:
        """
        Get the current configuration instance.

        If not yet loaded, loads it first.

        Returns:
            GameConfig instance
        """
        if cls._instance is None:
            return cls.load()
        return cls._instance

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
