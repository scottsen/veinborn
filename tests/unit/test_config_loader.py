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
        assert 'default_ai_by_type' in config.ai_behaviors

    def test_aggressive_behavior_config(self):
        """Aggressive AI behavior has correct configuration."""
        config = ConfigLoader.get_config()

        aggressive = config.get_ai_behavior_config('aggressive')

        assert aggressive is not None
        assert 'chase_range' in aggressive
        assert aggressive['chase_range'] == 10
        assert 'attack_on_sight' in aggressive
        assert aggressive['attack_on_sight'] is True
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

    def test_passive_behavior_config(self):
        """Passive AI behavior has correct configuration."""
        config = ConfigLoader.get_config()

        passive = config.get_ai_behavior_config('passive')

        assert passive is not None
        assert 'chase_range' in passive
        assert passive['chase_range'] == 0
        assert 'flee_threshold' in passive
        assert passive['flee_threshold'] == 0.5

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
        assert unknown is not None
        assert 'chase_range' in unknown
        assert unknown['chase_range'] == 10  # Aggressive's chase range

    def test_default_ai_for_monster_types(self):
        """Monster types have default AI assignments."""
        config = ConfigLoader.get_config()

        assert config.get_default_ai_for_monster('rat') == 'passive'
        assert config.get_default_ai_for_monster('bat') == 'coward'
        assert config.get_default_ai_for_monster('goblin') == 'aggressive'
        assert config.get_default_ai_for_monster('orc') == 'aggressive'
        assert config.get_default_ai_for_monster('troll') == 'aggressive'
        assert config.get_default_ai_for_monster('dragon') == 'defensive'

    def test_default_ai_for_unknown_monster(self):
        """Unknown monster type defaults to aggressive."""
        config = ConfigLoader.get_config()

        assert config.get_default_ai_for_monster('unknown') == 'aggressive'


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
        assert 'attacker_attack' in formula
        assert 'defender_defense' in formula
        assert 'max' in formula

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
