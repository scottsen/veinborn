"""
Tests for ConfigLoader - game configuration loading.

Tests:
- AI behavior configuration loading
- Formula configuration loading
- Config accessor methods
"""

import pytest
from src.core.config.config_loader import ConfigLoader, GameConfig


pytestmark = pytest.mark.unit


class TestConfigLoaderInitialization:
    """Test ConfigLoader initialization."""

    def test_config_loader_loads_successfully(self):
        """ConfigLoader loads all configuration files."""
        config = ConfigLoader.load()

        assert config is not None
        assert isinstance(config, GameConfig)
        assert config.monster_spawns is not None
        assert config.ore_veins is not None
        assert config.game_constants is not None
        assert config.spawning is not None
        assert config.ai_behaviors is not None
        assert config.formulas is not None

    def test_config_loader_singleton(self):
        """ConfigLoader returns same instance."""
        config1 = ConfigLoader.load()
        config2 = ConfigLoader.load()

        assert config1 is config2

    def test_config_loader_get_config(self):
        """ConfigLoader.get_config() returns instance."""
        config = ConfigLoader.get_config()

        assert config is not None
        assert isinstance(config, GameConfig)


class TestAIBehaviorConfiguration:
    """Test AI behavior configuration loading and access."""

    def test_ai_behaviors_loaded(self):
        """AI behaviors configuration is loaded."""
        config = ConfigLoader.get_config()

        assert 'behaviors' in config.ai_behaviors

    def test_aggressive_behavior_config(self):
        """Aggressive AI behavior has correct configuration."""
        config = ConfigLoader.get_config()

        aggressive = config.get_ai_behavior_config('aggressive')

        assert aggressive is not None
        # Perception (aggro_range) decides what it chases; no separate chase range
        assert 'chase_range' not in aggressive
        assert 'flee_threshold' in aggressive
        assert aggressive['flee_threshold'] == 0.0

    def test_defensive_behavior_config(self):
        """Defensive AI behavior has correct configuration."""
        config = ConfigLoader.get_config()

        defensive = config.get_ai_behavior_config('defensive')

        assert defensive is not None
        assert 'chase_range' in defensive
        assert defensive['chase_range'] == 5
        assert 'flee_threshold' in defensive
        assert defensive['flee_threshold'] == 0.3

    def test_neutral_behavior_config(self):
        """Neutral AI behavior has correct configuration."""
        config = ConfigLoader.get_config()

        neutral = config.get_ai_behavior_config('neutral')

        assert neutral is not None
        assert neutral['flee_threshold'] == 0.5

    def test_universal_defaults(self):
        """Every monster's universal AI parameters have defaults."""
        config = ConfigLoader.get_config()

        defaults = config.ai_behaviors['defaults']
        assert {'aggro_range', 'memory_turns', 'move_speed', 'flee_threshold'} <= set(defaults)

    def test_coward_behavior_config(self):
        """Coward AI behavior has correct configuration."""
        config = ConfigLoader.get_config()

        coward = config.get_ai_behavior_config('coward')

        assert coward is not None
        assert 'flee_threshold' in coward
        assert coward['flee_threshold'] == 1.0
        assert 'flee_range' in coward
        assert coward['flee_range'] == 8

    def test_guard_behavior_config(self):
        """Guard AI behavior has correct configuration."""
        config = ConfigLoader.get_config()

        guard = config.get_ai_behavior_config('guard')

        assert guard is not None
        assert 'guard_radius' in guard
        assert guard['guard_radius'] == 4
        assert 'chase_range' in guard
        assert guard['chase_range'] == 6

    def test_unknown_behavior_falls_back(self):
        """Unknown AI type falls back to aggressive."""
        config = ConfigLoader.get_config()

        unknown = config.get_ai_behavior_config('unknown_type')

        # Should fall back to aggressive
        assert unknown == config.get_ai_behavior_config('aggressive')


class TestFormulaConfiguration:
    """Test formula configuration loading and access."""

    def test_formulas_loaded(self):
        """Formulas configuration is loaded."""
        config = ConfigLoader.get_config()

        assert 'combat' in config.formulas
        assert 'mining' in config.formulas
        assert 'crafting' in config.formulas

    def test_damage_formula(self):
        """Damage formula is accessible."""
        config = ConfigLoader.get_config()

        formula = config.get_damage_formula()

        assert formula is not None
        assert 'damage_roll' in formula
        assert 'defender_defense' in formula
        assert 'max' in formula

    def test_combat_dice_config(self):
        """To-hit roll and damage spread are configured (NetHack-style combat)."""
        config = ConfigLoader.get_config()

        to_hit = config.get_to_hit_config()
        assert to_hit['die'] == 20
        assert 'roll' in to_hit['formula']
        assert to_hit['natural_miss'] == 1
        assert to_hit['natural_hit'] == 20
        assert 0 < config.get_damage_spread() < 1

    def test_min_damage(self):
        """Minimum damage value is accessible."""
        config = ConfigLoader.get_config()

        min_damage = config.get_min_damage()

        assert min_damage == 1

    def test_mining_formulas(self):
        """Mining formulas are accessible."""
        config = ConfigLoader.get_config()

        formula = config.get_mining_turns_formula()
        base_turns = config.get_mining_base_turns()
        min_turns = config.get_mining_min_turns()
        max_turns = config.get_mining_max_turns()

        assert formula is not None
        assert 'min_turns' in formula
        assert 'hardness' in formula
        assert base_turns == 3
        assert min_turns == 3
        assert max_turns == 5

    def test_tier_multipliers(self):
        """Crafting tier multipliers are accessible."""
        config = ConfigLoader.get_config()

        copper_mult = config.get_tier_multiplier('copper')
        iron_mult = config.get_tier_multiplier('iron')
        steel_mult = config.get_tier_multiplier('steel')
        adamantite_mult = config.get_tier_multiplier('adamantite')

        assert copper_mult == 1.0
        assert iron_mult == 1.3
        assert steel_mult == 1.6
        assert adamantite_mult == 2.0

    def test_unknown_tier_multiplier(self):
        """Unknown tier defaults to 1.0."""
        config = ConfigLoader.get_config()

        unknown_mult = config.get_tier_multiplier('unknown_ore')

        assert unknown_mult == 1.0


class TestConfigVersioning:
    """Test configuration versioning and metadata."""

    def test_ai_behaviors_meta(self):
        """AI behaviors config has metadata."""
        config = ConfigLoader.get_config()

        assert 'meta' in config.ai_behaviors
        meta = config.ai_behaviors['meta']
        assert 'version' in meta
        assert meta['version'] == '1.0.0'

    def test_formulas_meta(self):
        """Formulas config has metadata."""
        config = ConfigLoader.get_config()

        assert 'meta' in config.formulas
        meta = config.formulas['meta']
        assert 'version' in meta
        assert meta['version'] == '1.0.0'


class TestDungeonGenerationConfiguration:
    """Test dungeon generation configuration loading and access."""

    def test_dungeon_generation_loaded(self):
        """Dungeon generation configuration is loaded."""
        config = ConfigLoader.get_config()

        assert config.dungeon_generation is not None
        assert 'bsp' in config.dungeon_generation
        assert 'rooms' in config.dungeon_generation
        assert 'corridors' in config.dungeon_generation

    def test_bsp_configuration(self):
        """BSP algorithm parameters are accessible."""
        config = ConfigLoader.get_config()

        min_split_size = config.get_bsp_min_split_size()
        aspect_ratio = config.get_bsp_aspect_ratio_threshold()
        split_ratio_min, split_ratio_max = config.get_bsp_split_ratio_range()

        assert min_split_size == 6
        assert aspect_ratio == 1.25
        assert split_ratio_min == 0.33
        assert split_ratio_max == 0.67

    def test_room_configuration(self):
        """Room parameters are accessible."""
        config = ConfigLoader.get_config()

        min_size = config.get_room_min_size()
        padding = config.get_room_padding()

        assert min_size == 4
        assert padding == 1

    def test_corridor_configuration(self):
        """Corridor parameters are accessible."""
        config = ConfigLoader.get_config()

        style = config.get_corridor_style()
        direction_prob = config.get_corridor_direction_probability()

        assert style == "l_shaped"
        assert direction_prob == 0.5

    def test_floor_overrides_empty_by_default(self):
        """Floor overrides return empty dict when none configured."""
        config = ConfigLoader.get_config()

        overrides = config.get_dungeon_floor_overrides(1)

        # Default config has no overrides
        assert overrides == {}

    def test_dungeon_presets(self):
        """Dungeon presets are accessible."""
        config = ConfigLoader.get_config()

        standard = config.get_dungeon_preset('standard')
        small = config.get_dungeon_preset('small_cramped')
        large = config.get_dungeon_preset('large_open')
        maze = config.get_dungeon_preset('maze')

        assert standard is not None
        assert 'bsp' in standard
        assert 'rooms' in standard

        assert small is not None
        assert small['bsp']['min_split_size'] == 5
        assert small['rooms']['min_size'] == 3

        assert large is not None
        assert large['bsp']['min_split_size'] == 10
        assert large['rooms']['min_size'] == 6

        assert maze is not None
        assert maze['bsp']['min_split_size'] == 4

    def test_unknown_preset_returns_empty(self):
        """Unknown preset returns empty dict."""
        config = ConfigLoader.get_config()

        unknown = config.get_dungeon_preset('nonexistent')

        assert unknown == {}

    def test_dungeon_generation_meta(self):
        """Dungeon generation config has metadata."""
        config = ConfigLoader.get_config()

        assert 'meta' in config.dungeon_generation
        meta = config.dungeon_generation['meta']
        assert 'version' in meta
        assert meta['version'] == '1.0.0'
