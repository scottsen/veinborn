"""
Unit tests for EventBus Lua integration.

Tests cover:
- Lua subscription to EventBus
- Python + Lua subscribers coexist
- Lua handler errors don't crash EventBus
- Event ordering (Python first, then Lua)
- Lua-specific EventBus methods
"""

import pytest
from unittest.mock import Mock, MagicMock
import tempfile
from pathlib import Path

from core.events.events import EventBus, GameEvent, GameEventType
from core.events.lua_event_handler import LuaEventHandler
from core.scripting.lua_runtime import LuaRuntime


@pytest.fixture
def event_bus():
    """Create EventBus instance."""
    return EventBus()


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


class TestLuaSubscription:
    """Test Lua subscription functionality."""

    def test_subscribe_lua_handler(self, event_bus, lua_runtime, temp_script_dir):
        """Test subscribing a Lua handler to EventBus."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_test_event(event)
    -- Test handler
end
""")

        handler = LuaEventHandler(
            str(script_file),
            "on_test_event",
            lua_runtime
        )
        handler.load()

        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler)

        assert event_bus.get_lua_subscriber_count(GameEventType.ENTITY_DIED) == 1

    def test_subscribe_multiple_lua_handlers(self, event_bus, lua_runtime, temp_script_dir):
        """Test subscribing multiple Lua handlers to same event."""
        script_file1 = temp_script_dir / "handler1.lua"
        script_file1.write_text("""
function on_test_event(event)
    -- Handler 1
end
""")

        script_file2 = temp_script_dir / "handler2.lua"
        script_file2.write_text("""
function on_test_event(event)
    -- Handler 2
end
""")

        handler1 = LuaEventHandler(str(script_file1), "on_test_event", lua_runtime)
        handler2 = LuaEventHandler(str(script_file2), "on_test_event", lua_runtime)

        handler1.load()
        handler2.load()

        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler1)
        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler2)

        assert event_bus.get_lua_subscriber_count(GameEventType.ENTITY_DIED) == 2

    def test_unsubscribe_lua_handler(self, event_bus, lua_runtime, temp_script_dir):
        """Test unsubscribing a Lua handler from EventBus."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_test_event(event)
    -- Test handler
end
""")

        handler = LuaEventHandler(str(script_file), "on_test_event", lua_runtime)
        handler.load()

        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler)
        assert event_bus.get_lua_subscriber_count(GameEventType.ENTITY_DIED) == 1

        result = event_bus.unsubscribe_lua(GameEventType.ENTITY_DIED, handler)
        assert result is True
        assert event_bus.get_lua_subscriber_count(GameEventType.ENTITY_DIED) == 0

    def test_unsubscribe_nonexistent_handler(self, event_bus, lua_runtime):
        """Test unsubscribing handler that isn't subscribed."""
        handler = LuaEventHandler("test.lua", "on_test_event", lua_runtime)

        result = event_bus.unsubscribe_lua(GameEventType.ENTITY_DIED, handler)
        assert result is False


class TestPythonAndLuaCoexistence:
    """Test Python and Lua subscribers working together."""

    def test_python_and_lua_subscribers_both_called(
        self, event_bus, lua_runtime, temp_script_dir
    ):
        """Test that both Python and Lua subscribers receive events."""
        # Create Python subscriber
        python_calls = []
        def python_subscriber(event):
            python_calls.append(event)

        event_bus.subscribe(GameEventType.ENTITY_DIED, python_subscriber)

        # Create Lua subscriber
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
lua_calls = {}

function on_entity_died(event)
    table.insert(lua_calls, event.type)
end
""")

        handler = LuaEventHandler(str(script_file), "on_entity_died", lua_runtime)
        handler.load()
        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler)

        # Publish event
        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1', 'killer_id': 'player_1'},
            turn=1
        )
        event_bus.publish(event)

        # Verify both were called
        assert len(python_calls) == 1
        assert python_calls[0].event_type == GameEventType.ENTITY_DIED

        lua_calls = lua_runtime.get_global("lua_calls")
        assert len(lua_calls) == 1

    def test_python_called_before_lua(
        self, event_bus, lua_runtime, temp_script_dir
    ):
        """Test that Python subscribers are called before Lua subscribers."""
        call_order = []

        # Create Python subscriber
        def python_subscriber(event):
            call_order.append("python")

        event_bus.subscribe(GameEventType.ENTITY_DIED, python_subscriber)

        # Create Lua subscriber that adds to call_order
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event)
    -- Lua handler executed (we'll track via handler.handle being called)
end
""")

        # Mock handler to track call order
        handler = LuaEventHandler(str(script_file), "on_entity_died", lua_runtime)
        handler.load()

        original_handle = handler.handle
        def tracked_handle(event):
            call_order.append("lua")
            original_handle(event)
        handler.handle = tracked_handle

        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler)

        # Publish event
        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1'},
            turn=1
        )
        event_bus.publish(event)

        # Verify order
        assert call_order == ["python", "lua"]

    def test_subscriber_counts_separate(self, event_bus, lua_runtime, temp_script_dir):
        """Test that Python and Lua subscriber counts are tracked separately."""
        # Add Python subscribers
        event_bus.subscribe(GameEventType.ENTITY_DIED, lambda e: None)
        event_bus.subscribe(GameEventType.ENTITY_DIED, lambda e: None)

        # Add Lua subscribers
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event)
    -- Test handler
end
""")

        handler = LuaEventHandler(str(script_file), "on_entity_died", lua_runtime)
        handler.load()
        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler)

        # Verify separate counts
        assert event_bus.get_subscriber_count(GameEventType.ENTITY_DIED) == 2
        assert event_bus.get_lua_subscriber_count(GameEventType.ENTITY_DIED) == 1


class TestErrorIsolation:
    """Test that Lua handler errors don't crash EventBus."""

    def test_lua_error_doesnt_crash_eventbus(
        self, event_bus, lua_runtime, temp_script_dir
    ):
        """Test that Lua errors are caught and don't crash EventBus."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event)
    error("intentional error")
end
""")

        handler = LuaEventHandler(str(script_file), "on_entity_died", lua_runtime)
        handler.load()
        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler)

        # Publish event - should not raise
        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1'},
            turn=1
        )
        event_bus.publish(event)  # Should not crash

    def test_lua_error_doesnt_affect_other_handlers(
        self, event_bus, lua_runtime, temp_script_dir
    ):
        """Test that one Lua handler error doesn't prevent others from running."""
        # Create error handler
        error_script = temp_script_dir / "error_handler.lua"
        error_script.write_text("""
function on_entity_died(event)
    error("intentional error")
end
""")

        # Create working handler
        working_script = temp_script_dir / "working_handler.lua"
        working_script.write_text("""
call_count = 0

function on_entity_died(event)
    call_count = call_count + 1
end
""")

        error_handler = LuaEventHandler(
            str(error_script), "on_entity_died", lua_runtime
        )
        working_handler = LuaEventHandler(
            str(working_script), "on_entity_died", lua_runtime
        )

        error_handler.load()
        working_handler.load()

        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, error_handler)
        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, working_handler)

        # Publish event
        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1'},
            turn=1
        )
        event_bus.publish(event)

        # Verify working handler was still called
        call_count = lua_runtime.get_global("call_count")
        assert call_count == 1

    def test_python_error_doesnt_affect_lua_handlers(
        self, event_bus, lua_runtime, temp_script_dir
    ):
        """Test that Python subscriber errors don't prevent Lua handlers from running."""
        # Create Python subscriber that errors
        def error_subscriber(event):
            raise ValueError("intentional error")

        event_bus.subscribe(GameEventType.ENTITY_DIED, error_subscriber)

        # Create working Lua handler
        script_file = temp_script_dir / "working_handler.lua"
        script_file.write_text("""
call_count = 0

function on_entity_died(event)
    call_count = call_count + 1
end
""")

        handler = LuaEventHandler(str(script_file), "on_entity_died", lua_runtime)
        handler.load()
        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler)

        # Publish event
        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1'},
            turn=1
        )
        event_bus.publish(event)

        # Verify Lua handler was still called despite Python error
        call_count = lua_runtime.get_global("call_count")
        assert call_count == 1


class TestEventPublishing:
    """Test event publishing with Lua handlers."""

    def test_publish_to_lua_handler(self, event_bus, lua_runtime, temp_script_dir):
        """Test publishing event to Lua handler."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
received_events = {}

function on_entity_died(event)
    table.insert(received_events, {
        type = event.type,
        entity_id = event.data.entity_id,
        turn = event.turn
    })
end
""")

        handler = LuaEventHandler(str(script_file), "on_entity_died", lua_runtime)
        handler.load()
        event_bus.subscribe_lua(GameEventType.ENTITY_DIED, handler)

        # Publish event
        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1', 'killer_id': 'player_1'},
            turn=42
        )
        event_bus.publish(event)

        # Verify event was received
        received_events = lua_runtime.get_global("received_events")
        assert len(received_events) == 1
        assert received_events[1]['entity_id'] == 'goblin_1'
        assert received_events[1]['turn'] == 42
