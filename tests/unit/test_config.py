"""
Tests for ConfigManager

Validates:
- Config file loading from multiple locations
- ENV VAR overrides
- Type-safe getters (get, get_bool, get_int)
- Save/create functionality
- Player name resolution priority
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.config import ConfigManager, get_player_name
from src.core.exceptions import DataError


pytestmark = pytest.mark.unit

class TestConfigManager:
    """Test ConfigManager functionality."""

    def setup_method(self):
        """Reset singleton before each test."""
        ConfigManager.reset()

    def test_singleton_pattern(self):
        """ConfigManager should be a singleton."""
        config1 = ConfigManager.get_instance()
        config2 = ConfigManager.get_instance()
        assert config1 is config2

    def test_load_nonexistent_config(self):
        """Should handle missing config files gracefully."""
        with patch.object(ConfigManager, 'CONFIG_PATHS', [Path('/nonexistent/path')]):
            config = ConfigManager()
            assert config.config_file is None

    def test_create_default_config(self):
        """Should create default config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.veinbornrc"
            config = ConfigManager()
            config.create_default_config(config_path)

            assert config_path.exists()
            content = config_path.read_text()
            assert '[player]' in content
            assert '[game]' in content
            assert '[display]' in content

    def test_get_default(self):
        """Should return default when key not found."""
        config = ConfigManager()
        assert config.get('nonexistent.key', 'default') == 'default'

    def test_get_invalid_key(self):
        """Should return default for invalid key format."""
        config = ConfigManager()
        assert config.get('invalidkey', 'default') == 'default'

    def test_set_and_get(self):
        """Should set and retrieve values."""
        config = ConfigManager()
        config.set('player.name', 'Alice')
        assert config.get('player.name') == 'Alice'

    def test_set_invalid_key(self):
        """Should raise DataError for invalid key format."""
        config = ConfigManager()
        with pytest.raises(DataError):
            config.set('invalidkey', 'value')

    def test_get_bool(self):
        """Should parse boolean values correctly."""
        config = ConfigManager()

        # True values
        for value in ['true', 'True', 'TRUE', 'yes', 'Yes', '1', 'on']:
            config.set('test.bool', value)
            assert config.get_bool('test.bool') is True

        # False values
        for value in ['false', 'False', 'no', 'No', '0', 'off']:
            config.set('test.bool', value)
            assert config.get_bool('test.bool') is False

        # Default
        assert config.get_bool('nonexistent.bool', True) is True

    def test_get_int(self):
        """Should parse integer values correctly."""
        config = ConfigManager()

        config.set('test.int', '42')
        assert config.get_int('test.int') == 42

        config.set('test.int', '-10')
        assert config.get_int('test.int') == -10

        # Invalid integer - should return default
        config.set('test.int', 'not_a_number')
        assert config.get_int('test.int', 100) == 100

        # Nonexistent key
        assert config.get_int('nonexistent.int', 99) == 99

    def test_save_config(self):
        """Should save config to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.veinbornrc"
            config = ConfigManager()
            config.set('player.name', 'Bob')
            config.save(config_path)

            assert config_path.exists()

            # Reload and verify
            ConfigManager.reset()
            with patch.object(ConfigManager, 'CONFIG_PATHS', [config_path]):
                config2 = ConfigManager()
                assert config2.get('player.name') == 'Bob'

    def test_env_var_override(self):
        """ENV VARs should override config file values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.veinbornrc"

            # Create config with player.name = "Alice"
            config = ConfigManager()
            config.set('player.name', 'Alice')
            config.save(config_path)

            ConfigManager.reset()

            # Set ENV VAR
            with patch.dict(os.environ, {'VEINBORN_PLAYER_NAME': 'Bob'}):
                with patch.object(ConfigManager, 'CONFIG_PATHS', [config_path]):
                    config2 = ConfigManager()
                    # ENV VAR should override file value
                    assert config2.get('player.name') == 'Bob'

    def test_env_var_key_format(self):
        """ENV VAR keys should be properly formatted."""
        config = ConfigManager()

        with patch.dict(os.environ, {'VEINBORN_GAME_DEFAULT_SEED': '12345'}):
            assert config.get('game.default_seed') == '12345'

        with patch.dict(os.environ, {'VEINBORN_DISPLAY_SHOW_DAMAGE_NUMBERS': 'true'}):
            assert config.get_bool('display.show_damage_numbers') is True

    def test_multiple_config_paths(self):
        """Should load from first available config path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "config1"
            path2 = Path(tmpdir) / "config2"

            # Create config2 only
            config = ConfigManager()
            config.set('player.name', 'FromPath2')
            config.save(path2)

            ConfigManager.reset()
            with patch.object(ConfigManager, 'CONFIG_PATHS', [path1, path2]):
                config2 = ConfigManager()
                assert config2.get('player.name') == 'FromPath2'
                assert config2.config_file == path2

    def test_empty_string_returns_default(self):
        """Empty string values should return default."""
        config = ConfigManager()
        config.set('player.name', '')
        assert config.get('player.name', 'Default') == 'Default'


class TestGetPlayerName:
    """Test get_player_name() resolution priority."""

    def setup_method(self):
        """Reset singleton before each test."""
        ConfigManager.reset()

    def test_env_var_priority(self):
        """ENV VAR should have highest priority."""
        with patch.dict(os.environ, {'VEINBORN_PLAYER_NAME': 'EnvName'}):
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = Path(tmpdir) / "test.veinbornrc"
                config = ConfigManager()
                config.set('player.name', 'ConfigName')
                config.save(config_path)

                ConfigManager.reset()
                with patch.object(ConfigManager, 'CONFIG_PATHS', [config_path]):
                    # Create mock with 'name' attribute
                    args = MagicMock()
                    args.name = 'CliName'
                    assert get_player_name(args) == 'EnvName'

    def test_config_priority(self):
        """Config file should be second priority."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.veinbornrc"
            config = ConfigManager()
            config.set('player.name', 'ConfigName')
            config.save(config_path)

            ConfigManager.reset()
            with patch.object(ConfigManager, 'CONFIG_PATHS', [config_path]):
                args = None
                assert get_player_name(args) == 'ConfigName'

    def test_cli_arg_priority(self):
        """CLI arg should be third priority (when no ENV or config)."""
        ConfigManager.reset()
        with patch.object(ConfigManager, 'CONFIG_PATHS', [Path('/nonexistent')]):
            # Create mock with 'name' attribute
            args = MagicMock()
            args.name = 'CliName'
            with patch('sys.stdin.isatty', return_value=False):
                assert get_player_name(args) == 'CliName'

    def test_default_priority(self):
        """Should return 'Anonymous' when nothing is set."""
        ConfigManager.reset()
        with patch.object(ConfigManager, 'CONFIG_PATHS', [Path('/nonexistent')]):
            args = None
            with patch('sys.stdin.isatty', return_value=False):
                assert get_player_name(args) == 'Anonymous'

    def test_interactive_prompt(self):
        """Should prompt user when TTY available."""
        ConfigManager.reset()
        with patch.object(ConfigManager, 'CONFIG_PATHS', [Path('/nonexistent')]):
            args = None
            with patch('sys.stdin.isatty', return_value=True):
                with patch('builtins.input', return_value='InteractiveName'):
                    assert get_player_name(args) == 'InteractiveName'

    def test_interactive_prompt_empty(self):
        """Should return Anonymous when user presses Enter."""
        ConfigManager.reset()
        with patch.object(ConfigManager, 'CONFIG_PATHS', [Path('/nonexistent')]):
            args = None
            with patch('sys.stdin.isatty', return_value=True):
                with patch('builtins.input', return_value=''):
                    assert get_player_name(args) == 'Anonymous'

    def test_interactive_prompt_eof(self):
        """Should return Anonymous on EOF/Ctrl+D."""
        ConfigManager.reset()
        with patch.object(ConfigManager, 'CONFIG_PATHS', [Path('/nonexistent')]):
            args = None
            with patch('sys.stdin.isatty', return_value=True):
                with patch('builtins.input', side_effect=EOFError):
                    assert get_player_name(args) == 'Anonymous'

    def test_interactive_prompt_keyboard_interrupt(self):
        """Should return Anonymous on Ctrl+C."""
        ConfigManager.reset()
        with patch.object(ConfigManager, 'CONFIG_PATHS', [Path('/nonexistent')]):
            args = None
            with patch('sys.stdin.isatty', return_value=True):
                with patch('builtins.input', side_effect=KeyboardInterrupt):
                    assert get_player_name(args) == 'Anonymous'


class TestConfigIntegration:
    """Integration tests for ConfigManager."""

    def setup_method(self):
        """Reset singleton before each test."""
        ConfigManager.reset()

    def test_real_world_usage(self):
        """Test realistic usage scenario."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".veinbornrc"

            # Create default config
            config = ConfigManager()
            config.create_default_config(config_path)

            # User sets their name
            config.set('player.name', 'Alice')
            config.set('player.default_class', 'warrior')
            config.set('game.autopickup', 'true')
            config.save(config_path)

            # Reload from file
            ConfigManager.reset()
            with patch.object(ConfigManager, 'CONFIG_PATHS', [config_path]):
                config2 = ConfigManager()
                assert config2.get('player.name') == 'Alice'
                assert config2.get('player.default_class') == 'warrior'
                assert config2.get_bool('game.autopickup') is True

    def test_xdg_config_path(self):
        """Test XDG config directory support."""

        with tempfile.TemporaryDirectory() as tmpdir:
            xdg_path = Path(tmpdir) / ".config" / "brogue" / "config"

            config = ConfigManager()
            config.set('player.name', 'XdgUser')
            config.save(xdg_path)

            assert xdg_path.exists()
            assert xdg_path.parent.exists()

            # Reload
            ConfigManager.reset()
            with patch.object(ConfigManager, 'CONFIG_PATHS', [xdg_path]):
                config2 = ConfigManager()
                assert config2.get('player.name') == 'XdgUser'
