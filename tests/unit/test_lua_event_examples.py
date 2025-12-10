"""
Unit tests for example Lua event handlers.

Tests cover:
- Validate example handler scripts load
- Test achievements.lua logic
- Test quest_tracker.lua logic
- Test dynamic_loot.lua logic
- Template completeness
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from core.events.lua_event_handler import LuaEventHandler
from core.events.lua_event_registry import LuaEventRegistry
from core.events.events import EventBus, GameEvent, GameEventType
from core.scripting.lua_runtime import LuaRuntime
from core.scripting.game_context_api import GameContextAPI
from core.base.game_context import GameContext


@pytest.fixture
def lua_runtime():
    """Create LuaRuntime instance."""
    return LuaRuntime()


@pytest.fixture
def event_bus():
    """Create EventBus instance."""
    return EventBus()


@pytest.fixture
def registry(lua_runtime, event_bus):
    """Create LuaEventRegistry instance."""
    return LuaEventRegistry(lua_runtime, event_bus)


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
def api(game_context, lua_runtime, event_bus, registry):
    """Create GameContextAPI with full event support."""
    # Pass event_bus and registry during init so _register_api() can use them
    # This ensures veinborn table is available in Lua environment
    api = GameContextAPI(game_context, lua_runtime.lua, event_bus, registry)
    return api


@pytest.fixture
def examples_dir():
    """Get path to examples directory."""
    return Path(__file__).parent.parent.parent / "scripts" / "events"


class TestTemplateFile:
    """Test _template.lua example."""

    def test_template_exists(self, examples_dir):
        """Test that template file exists."""
        template_file = examples_dir / "_template.lua"
        assert template_file.exists()

    def test_template_is_valid_lua(self, lua_runtime, examples_dir):
        """Test that template is valid Lua syntax."""
        template_file = examples_dir / "_template.lua"

        with open(template_file, 'r') as f:
            script_content = f.read()

        # Should not raise syntax error
        lua_runtime.execute_script(script_content)

    def test_template_has_documentation(self, examples_dir):
        """Test that template has comprehensive documentation."""
        template_file = examples_dir / "_template.lua"

        with open(template_file, 'r') as f:
            content = f.read()

        # Check for key documentation elements
        assert "Event Handler Template" in content or "template" in content.lower()
        assert "subscribe" in content.lower()
        assert "function" in content


class TestAchievementsExample:
    """Test achievements.lua example handler."""

    def test_achievements_file_exists(self, examples_dir):
        """Test that achievements.lua exists."""
        achievements_file = examples_dir / "achievements.lua"
        assert achievements_file.exists()

    def test_achievements_loads(self, lua_runtime, examples_dir):
        """Test that achievements handler loads successfully."""
        achievements_file = examples_dir / "achievements.lua"

        handler = LuaEventHandler(
            str(achievements_file),
            "on_entity_died",
            lua_runtime
        )

        assert handler.load() is True

    def test_achievements_has_required_handlers(self, lua_runtime, examples_dir):
        """Test that achievements has all required handler functions."""
        achievements_file = examples_dir / "achievements.lua"

        with open(achievements_file, 'r') as f:
            lua_runtime.execute_script(f.read())

        # Check for required handler functions
        required_handlers = [
            "on_entity_died",
            "on_floor_changed",
            "on_item_crafted",
            "on_turn_ended"
        ]

        for handler_name in required_handlers:
            handler_func = lua_runtime.get_global(handler_name)
            assert handler_func is not None, f"Missing handler: {handler_name}"
            assert callable(handler_func), f"Handler not callable: {handler_name}"

    def test_achievements_tracks_kills(self, api, lua_runtime, examples_dir):
        """Test that achievements tracks player kills correctly."""
        achievements_file = examples_dir / "achievements.lua"

        handler = LuaEventHandler(
            str(achievements_file),
            "on_entity_died",
            lua_runtime
        )
        handler.load()

        # Simulate 100 kills
        for i in range(100):
            event = GameEvent(
                event_type=GameEventType.ENTITY_DIED,
                data={'entity_id': f'goblin_{i}', 'killer_id': 'player_1'},
                turn=i + 1
            )
            handler.handle(event)

        # Check that kills are tracked using export function
        get_stats = lua_runtime.get_global("get_stats")
        stats = get_stats()
        assert stats is not None
        assert stats['player_kills'] == 100

    def test_achievements_ignores_non_player_kills(self, api, lua_runtime, examples_dir):
        """Test that achievements ignores kills by other entities."""
        achievements_file = examples_dir / "achievements.lua"

        handler = LuaEventHandler(
            str(achievements_file),
            "on_entity_died",
            lua_runtime
        )
        handler.load()

        # Simulate non-player kill
        event = GameEvent(
            event_type=GameEventType.ENTITY_DIED,
            data={'entity_id': 'goblin_1', 'killer_id': 'other_monster'},
            turn=1
        )
        handler.handle(event)

        # Check that kill wasn't counted using export function
        get_stats = lua_runtime.get_global("get_stats")
        stats = get_stats()
        assert stats['player_kills'] == 0

    def test_achievements_tracks_floors(self, api, lua_runtime, examples_dir):
        """Test that achievements tracks floor progression."""
        achievements_file = examples_dir / "achievements.lua"

        handler = LuaEventHandler(
            str(achievements_file),
            "on_floor_changed",
            lua_runtime
        )
        handler.load()

        # Simulate descending to floor 15
        event = GameEvent(
            event_type=GameEventType.FLOOR_CHANGED,
            data={'from_floor': 1, 'to_floor': 15, 'player_id': 'player_1'},
            turn=100
        )
        handler.handle(event)

        # Check deepest floor using export function
        get_stats = lua_runtime.get_global("get_stats")
        stats = get_stats()
        assert stats['deepest_floor'] == 15

    def test_achievements_tracks_crafting(self, api, lua_runtime, examples_dir):
        """Test that achievements tracks item crafting."""
        achievements_file = examples_dir / "achievements.lua"

        handler = LuaEventHandler(
            str(achievements_file),
            "on_item_crafted",
            lua_runtime
        )
        handler.load()

        # Simulate crafting 50 items
        for i in range(50):
            event = GameEvent(
                event_type=GameEventType.ITEM_CRAFTED,
                data={'item_id': f'item_{i}', 'crafter_id': 'player_1'},
                turn=i + 1
            )
            handler.handle(event)

        # Check crafting count using export function
        get_stats = lua_runtime.get_global("get_stats")
        stats = get_stats()
        assert stats['items_crafted'] == 50


class TestQuestTrackerExample:
    """Test quest_tracker.lua example handler."""

    def test_quest_tracker_file_exists(self, examples_dir):
        """Test that quest_tracker.lua exists."""
        quest_file = examples_dir / "quest_tracker.lua"
        assert quest_file.exists()

    def test_quest_tracker_loads(self, lua_runtime, examples_dir):
        """Test that quest tracker handler loads successfully."""
        quest_file = examples_dir / "quest_tracker.lua"

        handler = LuaEventHandler(
            str(quest_file),
            "on_entity_died",
            lua_runtime
        )

        assert handler.load() is True

    def test_quest_tracker_has_required_handlers(self, lua_runtime, examples_dir):
        """Test that quest tracker has required handler functions."""
        quest_file = examples_dir / "quest_tracker.lua"

        with open(quest_file, 'r') as f:
            lua_runtime.execute_script(f.read())

        # Check for required handlers
        required_handlers = ["on_entity_died", "on_game_started"]

        for handler_name in required_handlers:
            handler_func = lua_runtime.get_global(handler_name)
            assert handler_func is not None
            assert callable(handler_func)

    def test_quest_tracker_has_quest_data(self, api, lua_runtime, examples_dir):
        """Test that quest tracker defines quests."""
        quest_file = examples_dir / "quest_tracker.lua"

        with open(quest_file, 'r') as f:
            lua_runtime.execute_script(f.read())

        # Check for quests table using export function
        get_quests = lua_runtime.get_global("get_quests")
        quests = get_quests()
        assert quests is not None
        assert 'goblin_slayer' in quests

    def test_quest_tracker_progress(self, api, lua_runtime, examples_dir):
        """Test that quest tracker updates progress on kills."""
        quest_file = examples_dir / "quest_tracker.lua"

        handler = LuaEventHandler(
            str(quest_file),
            "on_entity_died",
            lua_runtime
        )
        handler.load()

        # Get quest and activate it using export function
        get_quests = lua_runtime.get_global("get_quests")
        quests = get_quests()
        quests['goblin_slayer']['active'] = True

        # Simulate killing 3 goblins
        for i in range(3):
            event = GameEvent(
                event_type=GameEventType.ENTITY_DIED,
                data={
                    'entity_id': f'goblin_{i}',
                    'entity_name': f'Goblin Warrior {i}',
                    'killer_id': 'player_1'
                },
                turn=i + 1
            )
            handler.handle(event)

        # Check quest progress using export function
        quests = get_quests()
        progress = quests['goblin_slayer']['progress']
        assert progress == 3

    def test_quest_tracker_completion(self, api, lua_runtime, examples_dir):
        """Test that quest completes when target reached."""
        quest_file = examples_dir / "quest_tracker.lua"

        handler = LuaEventHandler(
            str(quest_file),
            "on_entity_died",
            lua_runtime
        )
        handler.load()

        # Activate quest using export function
        get_quests = lua_runtime.get_global("get_quests")
        quests = get_quests()
        quests['goblin_slayer']['active'] = True

        # Kill 5 goblins (target)
        for i in range(5):
            event = GameEvent(
                event_type=GameEventType.ENTITY_DIED,
                data={
                    'entity_id': f'goblin_{i}',
                    'entity_name': f'Goblin {i}',
                    'killer_id': 'player_1'
                },
                turn=i + 1
            )
            handler.handle(event)

        # Check quest completed using export function
        quests = get_quests()
        completed = quests['goblin_slayer']['completed']
        assert completed is True


class TestDynamicLootExample:
    """Test dynamic_loot.lua example handler."""

    def test_dynamic_loot_file_exists(self, examples_dir):
        """Test that dynamic_loot.lua exists."""
        loot_file = examples_dir / "dynamic_loot.lua"
        assert loot_file.exists()

    def test_dynamic_loot_loads(self, lua_runtime, examples_dir):
        """Test that dynamic loot handler loads successfully."""
        loot_file = examples_dir / "dynamic_loot.lua"

        handler = LuaEventHandler(
            str(loot_file),
            "on_entity_died",
            lua_runtime
        )

        assert handler.load() is True

    def test_dynamic_loot_has_required_handlers(self, lua_runtime, examples_dir):
        """Test that dynamic loot has required handler functions."""
        loot_file = examples_dir / "dynamic_loot.lua"

        with open(loot_file, 'r') as f:
            lua_runtime.execute_script(f.read())

        # Check for required handlers
        required_handlers = [
            "on_entity_died",
            "on_floor_changed",
            "on_turn_ended"
        ]

        for handler_name in required_handlers:
            handler_func = lua_runtime.get_global(handler_name)
            assert handler_func is not None
            assert callable(handler_func)

    def test_dynamic_loot_tracks_kill_streak(self, api, lua_runtime, examples_dir):
        """Test that dynamic loot tracks kill streaks."""
        loot_file = examples_dir / "dynamic_loot.lua"

        handler = LuaEventHandler(
            str(loot_file),
            "on_entity_died",
            lua_runtime
        )
        handler.load()

        # Simulate 3 quick kills (within streak timeout)
        for i in range(3):
            event = GameEvent(
                event_type=GameEventType.ENTITY_DIED,
                data={
                    'entity_id': f'goblin_{i}',
                    'entity_name': 'Goblin',
                    'entity_type': 'monster',
                    'floor': 1,
                    'position': {'x': i, 'y': 1},
                    'killer_id': 'player_1'
                },
                turn=i + 1
            )
            handler.handle(event)

        # Check kill streak using export function
        get_loot_state = lua_runtime.get_global("get_loot_state")
        loot_state = get_loot_state()
        streak = loot_state['kill_streak']
        assert streak == 3

    def test_dynamic_loot_floor_tracking(self, api, lua_runtime, examples_dir):
        """Test that dynamic loot tracks floor changes."""
        loot_file = examples_dir / "dynamic_loot.lua"

        handler = LuaEventHandler(
            str(loot_file),
            "on_floor_changed",
            lua_runtime
        )
        handler.load()

        # Simulate floor change to floor 15
        event = GameEvent(
            event_type=GameEventType.FLOOR_CHANGED,
            data={'from_floor': 1, 'to_floor': 15, 'player_id': 'player_1'},
            turn=100
        )
        handler.handle(event)

        # Check current floor using export function
        get_loot_state = lua_runtime.get_global("get_loot_state")
        loot_state = get_loot_state()
        current_floor = loot_state['current_floor']
        assert current_floor == 15


class TestExampleIntegration:
    """Test integration between example handlers and registry."""

    def test_registry_loads_achievements(self, registry, examples_dir):
        """Test that registry can load achievements handler."""
        count = registry.load_from_directory(str(examples_dir))

        # Should load multiple handlers from achievements.lua
        assert count >= 4  # entity_died, floor_changed, item_crafted, turn_ended

    def test_all_examples_load_without_errors(self, lua_runtime, examples_dir):
        """Test that all example files load without syntax errors."""
        example_files = [
            "achievements.lua",
            "quest_tracker.lua",
            "dynamic_loot.lua"
        ]

        for example_file in example_files:
            file_path = examples_dir / example_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()

                # Should not raise
                lua_runtime.execute_script(content)

    def test_examples_have_annotations(self, examples_dir):
        """Test that all examples have @subscribe annotations."""
        example_files = [
            "achievements.lua",
            "quest_tracker.lua",
            "dynamic_loot.lua"
        ]

        for example_file in example_files:
            file_path = examples_dir / example_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()

                assert "@subscribe:" in content, f"{example_file} missing @subscribe annotation"
