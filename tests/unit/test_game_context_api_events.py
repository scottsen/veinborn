"""
Unit tests for GameContextAPI event methods.

Tests cover:
- veinborn.event.subscribe() from Lua
- veinborn.event.unsubscribe()
- veinborn.event.get_types()
- veinborn.event.emit() for testing
- Invalid event type handling
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from core.scripting.lua_runtime import LuaRuntime
from core.scripting.game_context_api import GameContextAPI
from core.base.game_context import GameContext
from core.events.events import EventBus, GameEventType
from core.events.lua_event_registry import LuaEventRegistry


@pytest.fixture
def mock_game_state():
    """Create mock game state."""
    game_state = Mock()
    game_state.entities = {}
    game_state.messages = []
    game_state.turn_count = 1
    game_state.current_floor = 1
    return game_state


@pytest.fixture
def game_context(mock_game_state):
    """Create GameContext with mock state."""
    return GameContext(mock_game_state)


@pytest.fixture
def event_bus():
    """Create EventBus instance."""
    return EventBus()


@pytest.fixture
def lua_runtime():
    """Create LuaRuntime."""
    return LuaRuntime()


@pytest.fixture
def registry(lua_runtime, event_bus):
    """Create LuaEventRegistry."""
    return LuaEventRegistry(lua_runtime, event_bus)


@pytest.fixture
def api(game_context, lua_runtime, event_bus, registry):
    """Create GameContextAPI with event support."""
    # Pass event_bus and registry during init so _register_api() can use them
    api = GameContextAPI(game_context, lua_runtime.lua, event_bus, registry)
    return api


@pytest.fixture
def temp_script_dir(tmp_path):
    """Create temporary directory for test scripts."""
    script_dir = tmp_path / "scripts" / "events"
    script_dir.mkdir(parents=True)
    return script_dir


class TestEventSubscribe:
    """Test veinborn.event.subscribe() functionality."""

    def test_subscribe_from_lua(self, api, lua_runtime, temp_script_dir):
        """Test subscribing to event from Lua."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event)
    -- Test handler
end
""")

        # Call subscribe from Lua
        result = lua_runtime.execute_script(f"""
            return veinborn.event.subscribe("entity_died", "{script_file}")
        """)

        assert result is True

    def test_subscribe_with_explicit_handler_name(self, api, lua_runtime, temp_script_dir):
        """Test subscribing with explicit handler function name."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function custom_handler_name(event)
    -- Test handler with custom name
end
""")

        # Call subscribe with explicit handler name
        result = lua_runtime.execute_script(f"""
            return veinborn.event.subscribe("entity_died", "{script_file}", "custom_handler_name")
        """)

        assert result is True

    def test_subscribe_invalid_event_type(self, api, lua_runtime, temp_script_dir):
        """Test subscribing to invalid event type."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_invalid_event(event)
    -- Test handler
end
""")

        # Call subscribe with invalid event type
        result = lua_runtime.execute_script(f"""
            return veinborn.event.subscribe("invalid_event_type", "{script_file}")
        """)

        assert result is False

    def test_subscribe_without_eventbus(self, game_context, lua_runtime):
        """Test subscribing when EventBus is not initialized."""
        api = GameContextAPI(game_context, lua_runtime.lua)
        # Don't set event_bus or registry

        result = lua_runtime.execute_script("""
            return veinborn.event.subscribe("entity_died", "test.lua")
        """)

        assert result is False


class TestEventUnsubscribe:
    """Test veinborn.event.unsubscribe() functionality."""

    def test_unsubscribe_from_lua(self, api, lua_runtime, temp_script_dir):
        """Test unsubscribing from event from Lua."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event)
    -- Test handler
end
""")

        # Subscribe first
        lua_runtime.execute_script(f"""
            veinborn.event.subscribe("entity_died", "{script_file}")
        """)

        # Unsubscribe
        result = lua_runtime.execute_script(f"""
            return veinborn.event.unsubscribe("entity_died", "{script_file}")
        """)

        assert result is True

    def test_unsubscribe_invalid_event_type(self, api, lua_runtime):
        """Test unsubscribing from invalid event type."""
        result = lua_runtime.execute_script("""
            return veinborn.event.unsubscribe("invalid_event_type", "test.lua")
        """)

        assert result is False

    def test_unsubscribe_nonexistent_handler(self, api, lua_runtime):
        """Test unsubscribing handler that isn't subscribed."""
        result = lua_runtime.execute_script("""
            return veinborn.event.unsubscribe("entity_died", "nonexistent.lua")
        """)

        assert result is False


class TestEventGetTypes:
    """Test veinborn.event.get_types() functionality."""

    def test_get_types_from_lua(self, api, lua_runtime):
        """Test getting event types from Lua."""
        result = lua_runtime.execute_script("""
            local types = veinborn.event.get_types()
            return #types > 0
        """)

        assert result is True

    def test_get_types_contains_known_types(self, api, lua_runtime):
        """Test that get_types() includes known event types."""
        result = lua_runtime.execute_script("""
            local types = veinborn.event.get_types()
            local found = false

            for i = 1, #types do
                if types[i] == "entity_died" then
                    found = true
                    break
                end
            end

            return found
        """)

        assert result is True

    def test_get_types_returns_all_types(self, api, lua_runtime):
        """Test that get_types() returns all event types."""
        # Get count from Python
        expected_count = len(GameEventType)

        # Get count from Lua
        result = lua_runtime.execute_script("""
            local types = veinborn.event.get_types()
            return #types
        """)

        assert result == expected_count


class TestEventEmit:
    """Test veinborn.event.emit() functionality."""

    def test_emit_from_lua(self, api, lua_runtime, temp_script_dir):
        """Test manually emitting event from Lua."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
received_events = {}

function on_entity_died(event)
    table.insert(received_events, event.data.entity_id)
end
""")

        # Subscribe handler
        lua_runtime.execute_script(f"""
            veinborn.event.subscribe("entity_died", "{script_file}")
        """)

        # Emit event
        result = lua_runtime.execute_script("""
            return veinborn.event.emit("entity_died", {entity_id = "test_goblin"})
        """)

        assert result is True

        # Verify handler was called
        received_events = lua_runtime.get_global("received_events")
        assert len(received_events) == 1
        assert received_events[1] == "test_goblin"

    def test_emit_invalid_event_type(self, api, lua_runtime):
        """Test emitting invalid event type."""
        result = lua_runtime.execute_script("""
            return veinborn.event.emit("invalid_event_type", {})
        """)

        assert result is False

    def test_emit_with_complex_data(self, api, lua_runtime, temp_script_dir):
        """Test emitting event with complex nested data."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
received_data = nil

function on_item_crafted(event)
    received_data = event.data
end
""")

        # Subscribe handler
        lua_runtime.execute_script(f"""
            veinborn.event.subscribe("item_crafted", "{script_file}")
        """)

        # Emit event with complex data
        lua_runtime.execute_script("""
            veinborn.event.emit("item_crafted", {
                item_id = "sword_1",
                stats = {
                    attack = 10,
                    defense = 5
                }
            })
        """)

        # Verify data was passed correctly
        received_data = lua_runtime.get_global("received_data")
        assert received_data is not None
        assert received_data['item_id'] == "sword_1"
        assert received_data['stats']['attack'] == 10

    def test_emit_without_eventbus(self, game_context, lua_runtime):
        """Test emitting when EventBus is not initialized."""
        api = GameContextAPI(game_context, lua_runtime.lua)
        # Don't set event_bus

        result = lua_runtime.execute_script("""
            return veinborn.event.emit("entity_died", {entity_id = "test"})
        """)

        assert result is False


class TestEventAPIIntegration:
    """Test integration between event API methods."""

    def test_subscribe_emit_unsubscribe_workflow(
        self, api, lua_runtime, temp_script_dir
    ):
        """Test complete workflow: subscribe → emit → unsubscribe."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
call_count = 0

function on_entity_died(event)
    call_count = call_count + 1
end
""")

        # Subscribe
        subscribe_result = lua_runtime.execute_script(f"""
            return veinborn.event.subscribe("entity_died", "{script_file}")
        """)
        assert subscribe_result is True

        # Emit event - handler should be called
        lua_runtime.execute_script("""
            veinborn.event.emit("entity_died", {entity_id = "test"})
        """)

        call_count_1 = lua_runtime.get_global("call_count")
        assert call_count_1 == 1

        # Unsubscribe
        unsubscribe_result = lua_runtime.execute_script(f"""
            return veinborn.event.unsubscribe("entity_died", "{script_file}")
        """)
        assert unsubscribe_result is True

        # Emit again - handler should NOT be called
        lua_runtime.execute_script("""
            veinborn.event.emit("entity_died", {entity_id = "test2"})
        """)

        call_count_2 = lua_runtime.get_global("call_count")
        assert call_count_2 == 1  # Still 1, not incremented
