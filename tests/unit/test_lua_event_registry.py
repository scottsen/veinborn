"""
Unit tests for LuaEventRegistry.

Tests cover:
- Handler registration and deregistration
- Duplicate prevention
- Directory loading
- Annotation parsing (@subscribe comments)
- Registry state management
"""

import pytest
from pathlib import Path
import tempfile

from core.events.lua_event_registry import LuaEventRegistry
from core.events.events import EventBus, GameEventType
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
def registry(lua_runtime, event_bus):
    """Create LuaEventRegistry instance."""
    return LuaEventRegistry(lua_runtime, event_bus)


@pytest.fixture
def temp_script_dir(tmp_path):
    """Create temporary directory for test scripts."""
    script_dir = tmp_path / "scripts" / "events"
    script_dir.mkdir(parents=True)
    return script_dir


class TestRegistryInitialization:
    """Test registry initialization."""

    def test_initialization(self, lua_runtime, event_bus):
        """Test basic registry initialization."""
        registry = LuaEventRegistry(lua_runtime, event_bus)

        assert registry.lua_runtime is lua_runtime
        assert registry.event_bus is event_bus
        assert len(registry.handlers) == 0
        assert len(registry.subscriptions) == 0
        assert len(registry.script_events) == 0


class TestHandlerRegistration:
    """Test handler registration functionality."""

    def test_register_handler(self, registry, temp_script_dir):
        """Test registering a handler."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event)
    -- Test handler
end
""")

        result = registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file),
            "on_entity_died"
        )

        assert result is True
        assert registry.get_subscription_count(GameEventType.ENTITY_DIED) == 1

    def test_register_multiple_handlers_same_event(self, registry, temp_script_dir):
        """Test registering multiple handlers for same event."""
        script_file1 = temp_script_dir / "handler1.lua"
        script_file1.write_text("""
function on_entity_died(event)
    -- Handler 1
end
""")

        script_file2 = temp_script_dir / "handler2.lua"
        script_file2.write_text("""
function on_entity_died(event)
    -- Handler 2
end
""")

        registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file1),
            "on_entity_died"
        )
        registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file2),
            "on_entity_died"
        )

        assert registry.get_subscription_count(GameEventType.ENTITY_DIED) == 2

    def test_register_duplicate_handler(self, registry, temp_script_dir):
        """Test that duplicate registration is prevented."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event)
    -- Test handler
end
""")

        # Register once
        result1 = registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file),
            "on_entity_died"
        )
        assert result1 is True

        # Try to register again
        result2 = registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file),
            "on_entity_died"
        )
        assert result2 is False

        # Should still be only 1 subscription
        assert registry.get_subscription_count(GameEventType.ENTITY_DIED) == 1

    def test_register_invalid_script(self, registry):
        """Test registering handler with invalid script path."""
        result = registry.register(
            GameEventType.ENTITY_DIED,
            "/nonexistent/script.lua",
            "on_entity_died"
        )

        assert result is False

    def test_register_missing_function(self, registry, temp_script_dir):
        """Test registering handler with missing function."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function different_function(event)
    -- Wrong function name
end
""")

        result = registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file),
            "on_entity_died"  # This function doesn't exist
        )

        assert result is False


class TestHandlerUnregistration:
    """Test handler unregistration functionality."""

    def test_unregister_handler(self, registry, temp_script_dir):
        """Test unregistering a handler."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event)
    -- Test handler
end
""")

        # Register handler
        registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file),
            "on_entity_died"
        )

        assert registry.get_subscription_count(GameEventType.ENTITY_DIED) == 1

        # Unregister handler
        result = registry.unregister(GameEventType.ENTITY_DIED, str(script_file))

        assert result is True
        assert registry.get_subscription_count(GameEventType.ENTITY_DIED) == 0

    def test_unregister_nonexistent_handler(self, registry):
        """Test unregistering handler that doesn't exist."""
        result = registry.unregister(
            GameEventType.ENTITY_DIED,
            "/nonexistent/script.lua"
        )

        assert result is False


class TestDirectoryLoading:
    """Test loading handlers from directory."""

    def test_load_from_directory(self, registry, temp_script_dir):
        """Test loading handlers from directory with annotations."""
        # Create handler with annotation
        handler_file = temp_script_dir / "achievements.lua"
        handler_file.write_text("""
-- @subscribe: entity_died
-- @handler: on_entity_died

function on_entity_died(event)
    -- Achievement handler
end
""")

        count = registry.load_from_directory(str(temp_script_dir))

        assert count == 1
        assert registry.get_subscription_count(GameEventType.ENTITY_DIED) == 1

    def test_load_multiple_handlers(self, registry, temp_script_dir):
        """Test loading multiple handlers from directory."""
        # Create first handler
        handler1 = temp_script_dir / "achievements.lua"
        handler1.write_text("""
-- @subscribe: entity_died
-- @handler: on_entity_died

function on_entity_died(event)
    -- Handler 1
end
""")

        # Create second handler
        handler2 = temp_script_dir / "quest_tracker.lua"
        handler2.write_text("""
-- @subscribe: entity_died, item_crafted
-- @handler: on_entity_died, on_item_crafted

function on_entity_died(event)
    -- Handler 2
end

function on_item_crafted(event)
    -- Handler 2 for crafting
end
""")

        count = registry.load_from_directory(str(temp_script_dir))

        # Should load 3 subscriptions total (1 from handler1, 2 from handler2)
        assert count == 3
        assert registry.get_subscription_count(GameEventType.ENTITY_DIED) == 2
        assert registry.get_subscription_count(GameEventType.ITEM_CRAFTED) == 1

    def test_load_skips_template_files(self, registry, temp_script_dir):
        """Test that files starting with _ are skipped."""
        # Create template file
        template = temp_script_dir / "_template.lua"
        template.write_text("""
-- @subscribe: entity_died
-- @handler: on_entity_died

function on_entity_died(event)
    -- Template handler
end
""")

        count = registry.load_from_directory(str(temp_script_dir))

        # Should skip template
        assert count == 0

    def test_load_from_nonexistent_directory(self, registry):
        """Test loading from directory that doesn't exist."""
        count = registry.load_from_directory("/nonexistent/directory")

        assert count == 0


class TestAnnotationParsing:
    """Test annotation parsing functionality."""

    def test_parse_simple_annotation(self, registry):
        """Test parsing simple annotation."""
        script_content = """
-- @subscribe: entity_died
-- @handler: on_entity_died

function on_entity_died(event)
    -- Handler
end
"""
        annotations = registry._parse_annotations(script_content)

        assert 'entity_died' in annotations['subscribe']
        assert 'on_entity_died' in annotations['handler']

    def test_parse_multiple_events(self, registry):
        """Test parsing annotation with multiple events."""
        script_content = """
-- @subscribe: entity_died, item_crafted, floor_changed
-- @handler: on_entity_died, on_item_crafted, on_floor_changed

function on_entity_died(event) end
function on_item_crafted(event) end
function on_floor_changed(event) end
"""
        annotations = registry._parse_annotations(script_content)

        assert len(annotations['subscribe']) == 3
        assert 'entity_died' in annotations['subscribe']
        assert 'item_crafted' in annotations['subscribe']
        assert 'floor_changed' in annotations['subscribe']

        assert len(annotations['handler']) == 3

    def test_parse_infers_handler_names(self, registry, temp_script_dir):
        """Test that handler names are inferred if not specified."""
        handler_file = temp_script_dir / "test.lua"
        handler_file.write_text("""
-- @subscribe: entity_died, item_crafted

function on_entity_died(event) end
function on_item_crafted(event) end
""")

        count = registry.load_from_directory(str(temp_script_dir))

        # Should infer on_entity_died and on_item_crafted
        assert count == 2


class TestRegistryState:
    """Test registry state management."""

    def test_get_handlers(self, registry, temp_script_dir):
        """Test getting handlers for event type."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event)
    -- Test handler
end
""")

        registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file),
            "on_entity_died"
        )

        handlers = registry.get_handlers(GameEventType.ENTITY_DIED)

        assert len(handlers) == 1
        assert handlers[0].script_path == str(script_file)

    def test_get_all_subscriptions(self, registry, temp_script_dir):
        """Test getting all subscriptions."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event) end
function on_item_crafted(event) end
""")

        registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file),
            "on_entity_died"
        )
        registry.register(
            GameEventType.ITEM_CRAFTED,
            str(script_file),
            "on_item_crafted"
        )

        subscriptions = registry.get_all_subscriptions()

        assert 'entity_died' in subscriptions
        assert 'item_crafted' in subscriptions
        assert len(subscriptions['entity_died']) == 1
        assert len(subscriptions['item_crafted']) == 1

    def test_clear_registry(self, registry, temp_script_dir):
        """Test clearing all registrations."""
        script_file = temp_script_dir / "test_handler.lua"
        script_file.write_text("""
function on_entity_died(event) end
""")

        registry.register(
            GameEventType.ENTITY_DIED,
            str(script_file),
            "on_entity_died"
        )

        assert registry.get_subscription_count(GameEventType.ENTITY_DIED) == 1

        registry.clear()

        assert registry.get_subscription_count(GameEventType.ENTITY_DIED) == 0
        assert len(registry.handlers) == 0
        assert len(registry.subscriptions) == 0
