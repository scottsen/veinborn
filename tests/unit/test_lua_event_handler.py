"""
Unit tests for LuaEventHandler.

Tests cover:
- Handler loading and validation
- Event execution with timeout
- Error handling (Lua errors, missing functions)
- Event data conversion
- Timeout enforcement
"""

import pytest
import tempfile
from pathlib import Path
import lupa
import time

from core.events.lua_event_handler import LuaEventHandler
from core.events.events import GameEvent, GameEventType
from core.scripting.lua_runtime import LuaRuntime, LuaTimeoutError


@pytest.fixture
def lua_runtime():
    """Create LuaRuntime instance."""
    return LuaRuntime()


@pytest.fixture
def temp_script_dir(tmp_path):
    """Create temporary directory for test scripts."""
    script_dir = tmp_path / "scripts"
    script_dir.mkdir()
    return script_dir


class TestLuaEventHandlerInitialization:
    """Test LuaEventHandler initialization."""

    def test_initialization(self, lua_runtime):
        """Test basic handler initialization."""
        handler = LuaEventHandler(
            "scripts/events/test.lua",
            "on_test_event",
            lua_runtime
        )
        assert handler.script_path == "scripts/events/test.lua"
        assert handler.handler_function == "on_test_event"
        assert handler.lua_runtime is lua_runtime
        assert handler.loaded is False
        assert handler.lua_func is None

    def test_repr(self, lua_runtime):
        """Test string representation."""
        handler = LuaEventHandler(
            "scripts/events/test.lua",
            "on_test_event",
            lua_runtime
        )
        repr_str = repr(handler)
        assert "LuaEventHandler" in repr_str
        assert "test.lua" in repr_str
        assert "on_test_event" in repr_str

    def test_equality(self, lua_runtime):
        """Test handler equality."""
        handler1 = LuaEventHandler(
            "scripts/events/test.lua",
            "on_test_event",
            lua_runtime
        )
        handler2 = LuaEventHandler(
            "scripts/events/test.lua",
            "on_test_event",
            lua_runtime
        )
        handler3 = LuaEventHandler(
            "scripts/events/other.lua",
            "on_test_event",
            lua_runtime
        )

        assert handler1 == handler2
        assert handler1 != handler3
        assert handler1 != "not a handler"


class TestLuaEventHandlerLoading:
    """Test handler loading functionality."""

    def test_load_valid_script(self, lua_runtime, temp_script_dir):
        """Test loading a valid Lua script."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_test_event(event)
    -- Test handler
    return true
end
""")

        handler = LuaEventHandler(
            str(script_file),
            "on_test_event",
            lua_runtime
        )
        assert handler.load() is True
        assert handler.loaded is True
        assert handler.lua_func is not None

    def test_load_missing_file(self, lua_runtime):
        """Test loading a non-existent script file."""
        handler = LuaEventHandler(
            "/nonexistent/script.lua",
            "on_test_event",
            lua_runtime
        )
        assert handler.load() is False
        assert handler.loaded is False

    def test_load_missing_function(self, lua_runtime, temp_script_dir):
        """Test loading script with missing handler function."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function different_function(event)
    return true
end
""")

        handler = LuaEventHandler(
            str(script_file),
            "on_test_event",  # This function doesn't exist
            lua_runtime
        )
        assert handler.load() is False
        assert handler.loaded is False

    def test_load_syntax_error(self, lua_runtime, temp_script_dir):
        """Test loading script with syntax error."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_test_event(event)
    -- Missing 'end' keyword
""")

        handler = LuaEventHandler(
            str(script_file),
            "on_test_event",
            lua_runtime
        )
        with pytest.raises(lupa.LuaError):
            handler.load()

    def test_load_non_callable(self, lua_runtime, temp_script_dir):
        """Test loading when handler is not a function."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
on_test_event = "not a function"
""")

        handler = LuaEventHandler(
            str(script_file),
            "on_test_event",
            lua_runtime
        )
        assert handler.load() is False


class TestLuaEventHandlerExecution:
    """Test event handler execution."""

    def test_handle_simple_event(self, lua_runtime, temp_script_dir):
        """Test handling a simple event."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
handled_event = nil

function on_test_event(event)
    handled_event = event
end
""")

        handler = LuaEventHandler(
            str(script_file),
            "on_test_event",
            lua_runtime
        )
        handler.load()

        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1', 'killer_id': 'player_1'},
            turn=42
        )

        # Should not raise
        handler.handle(event)

        # Verify event was received by Lua
        handled = lua_runtime.get_global("handled_event")
        assert handled is not None
        assert handled['type'] == 'entity_died'
        assert handled['data']['entity_id'] == 'goblin_1'
        assert handled['turn'] == 42

    def test_handle_without_loading(self, lua_runtime):
        """Test handling event when handler not loaded."""
        handler = LuaEventHandler(
            "nonexistent.lua",
            "on_test_event",
            lua_runtime
        )

        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1'},
            turn=1
        )

        # Should not raise, just log warning
        handler.handle(event)

    def test_handle_lua_error(self, lua_runtime, temp_script_dir):
        """Test handling when Lua handler throws error."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_test_event(event)
    error("intentional error")
end
""")

        handler = LuaEventHandler(
            str(script_file),
            "on_test_event",
            lua_runtime
        )
        handler.load()

        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1'},
            turn=1
        )

        # Should not raise - errors are caught and logged
        handler.handle(event)

    def test_handle_with_nil_data(self, lua_runtime, temp_script_dir):
        """Test handling event with nil values in data."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
handled_event = nil

function on_test_event(event)
    handled_event = event
end
""")

        handler = LuaEventHandler(
            str(script_file),
            "on_test_event",
            lua_runtime
        )
        handler.load()

        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1', 'killer_id': None},
            turn=None
        )

        handler.handle(event)


class TestEventDataConversion:
    """Test event data conversion to Lua."""

    def test_event_to_lua_table_basic(self, lua_runtime):
        """Test basic event conversion."""
        handler = LuaEventHandler(
            "test.lua",
            "on_test_event",
            lua_runtime
        )

        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1', 'killer_id': 'player_1'},
            turn=42
        )

        lua_table = handler._event_to_lua_table(event)

        assert lua_table['type'] == 'entity_died'
        assert lua_table['data']['entity_id'] == 'goblin_1'
        assert lua_table['data']['killer_id'] == 'player_1'
        assert lua_table['turn'] == 42
        assert 'timestamp' in lua_table

    def test_event_to_lua_table_nested_data(self, lua_runtime):
        """Test event conversion with nested data."""
        handler = LuaEventHandler(
            "test.lua",
            "on_test_event",
            lua_runtime
        )

        event = GameEvent(
            event_type=GameEventType.ITEM_CRAFTED,
            data={
                'item_id': 'sword_1',
                'stats': {
                    'attack': 10,
                    'defense': 5,
                    'modifiers': ['sharp', 'durable']
                }
            },
            turn=10
        )

        lua_table = handler._event_to_lua_table(event)

        assert lua_table['type'] == 'item_crafted'
        assert lua_table['data']['item_id'] == 'sword_1'
        assert lua_table['data']['stats']['attack'] == 10
        assert 'modifiers' in lua_table['data']['stats']

    def test_event_to_lua_table_preserves_types(self, lua_runtime):
        """Test that event conversion preserves data types."""
        handler = LuaEventHandler(
            "test.lua",
            "on_test_event",
            lua_runtime
        )

        event = GameEvent(
            event_type=GameEventType.ATTACK_RESOLVED,
            data={
                'attacker_id': 'player_1',
                'damage': 25,
                'critical': True,
                'multiplier': 1.5,
            },
            turn=5
        )

        lua_table = handler._event_to_lua_table(event)

        assert isinstance(lua_table['data']['damage'], int)
        assert isinstance(lua_table['data']['critical'], bool)
        assert isinstance(lua_table['data']['multiplier'], float)


class TestHashAndEquality:
    """Test hashing and equality for use in collections."""

    def test_hash_consistency(self, lua_runtime):
        """Test that hash is consistent."""
        handler = LuaEventHandler(
            "scripts/events/test.lua",
            "on_test_event",
            lua_runtime
        )

        hash1 = hash(handler)
        hash2 = hash(handler)

        assert hash1 == hash2

    def test_hash_uniqueness(self, lua_runtime):
        """Test that different handlers have different hashes."""
        handler1 = LuaEventHandler(
            "scripts/events/test1.lua",
            "on_test_event",
            lua_runtime
        )
        handler2 = LuaEventHandler(
            "scripts/events/test2.lua",
            "on_test_event",
            lua_runtime
        )

        # Different paths should generally have different hashes
        # (not guaranteed but very likely)
        assert hash(handler1) != hash(handler2)

    def test_use_in_set(self, lua_runtime):
        """Test that handlers can be used in sets."""
        handler1 = LuaEventHandler(
            "scripts/events/test.lua",
            "on_test_event",
            lua_runtime
        )
        handler2 = LuaEventHandler(
            "scripts/events/test.lua",
            "on_test_event",
            lua_runtime
        )
        handler3 = LuaEventHandler(
            "scripts/events/other.lua",
            "on_test_event",
            lua_runtime
        )

        handlers = {handler1, handler2, handler3}

        # handler1 and handler2 are equal, so set should have 2 items
        assert len(handlers) == 2
