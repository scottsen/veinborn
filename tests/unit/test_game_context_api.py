"""
Unit tests for GameContextAPI.

Tests cover:
- Entity serialization
- API method calls from Lua
- Error handling
- Type conversions (Python <-> Lua)
"""

import pytest
from unittest.mock import Mock, MagicMock
import lupa

from core.scripting.lua_runtime import LuaRuntime
from core.scripting.game_context_api import GameContextAPI
from core.base.entity import Entity, EntityType
from core.base.game_context import GameContext


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
def lua_runtime():
    """Create LuaRuntime."""
    return LuaRuntime()


@pytest.fixture
def api(game_context, lua_runtime):
    """Create GameContextAPI."""
    return GameContextAPI(game_context, lua_runtime.lua)


class TestAPIRegistration:
    """Test API registration in Lua."""

    def test_brogue_global_exists(self, api, lua_runtime):
        """Test that 'brogue' global is registered."""
        result = lua_runtime.execute_script("return brogue ~= nil")
        assert result is True

    def test_api_methods_registered(self, api, lua_runtime):
        """Test that API methods are registered."""
        methods = [
            "get_player",
            "get_entity",
            "get_entity_at",
            "get_entities_in_range",
            "is_walkable",
            "add_message",
            "modify_stat",
        ]

        for method in methods:
            # Check that method exists and is callable
            result = lua_runtime.execute_script(
                f"return brogue.{method} ~= nil"
            )
            assert result is True, f"Method {method} not registered"


class TestEntitySerialization:
    """Test entity serialization to Lua."""

    def test_entity_to_lua_basic(self, api):
        """Test basic entity serialization."""
        entity = Entity(
            entity_id="test_123",
            name="Test Entity",
            entity_type=EntityType.MONSTER,
            x=5,
            y=10,
            hp=50,
            max_hp=100,
            attack=10,
            defense=5,
        )

        lua_entity = api._entity_to_lua(entity)

        assert lua_entity["id"] == "test_123"
        assert lua_entity["name"] == "Test Entity"
        assert lua_entity["entity_type"] == "MONSTER"
        assert lua_entity["x"] == 5
        assert lua_entity["y"] == 10
        assert lua_entity["hp"] == 50
        assert lua_entity["max_hp"] == 100
        assert lua_entity["attack"] == 10
        assert lua_entity["defense"] == 5

    def test_entity_to_lua_with_stats(self, api):
        """Test entity serialization with custom stats."""
        entity = Entity(
            entity_id="mage_1",
            name="Mage",
            stats={"mana": 100, "max_mana": 150, "intelligence": 20}
        )

        lua_entity = api._entity_to_lua(entity)

        assert lua_entity["stats"]["mana"] == 100
        assert lua_entity["stats"]["max_mana"] == 150
        assert lua_entity["stats"]["intelligence"] == 20

    def test_entity_to_lua_none(self, api):
        """Test serializing None entity."""
        result = api._entity_to_lua(None)
        assert result is None


class TestGetPlayer:
    """Test get_player API."""

    def test_get_player_from_lua(self, game_context, lua_runtime, mock_game_state):
        """Test calling get_player from Lua."""
        # Setup player
        player = Entity(
            entity_id="player_1",
            name="Hero",
            entity_type=EntityType.PLAYER,
            hp=100,
            max_hp=100,
        )
        mock_game_state.player = player

        # Register API
        api = GameContextAPI(game_context, lua_runtime.lua)

        # Call from Lua
        result = lua_runtime.execute_script("""
            local player = brogue.get_player()
            return player.name, player.hp
        """)

        assert result == ("Hero", 100)

    def test_get_player_attributes(self, game_context, lua_runtime, mock_game_state):
        """Test accessing player attributes."""
        player = Entity(
            entity_id="player_1",
            name="Warrior",
            x=10,
            y=20,
            attack=15,
            defense=8,
        )
        mock_game_state.player = player

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local p = brogue.get_player()
            return p.x + p.y + p.attack + p.defense
        """)

        assert result == 10 + 20 + 15 + 8


class TestGetEntity:
    """Test get_entity API."""

    def test_get_entity_by_id(self, game_context, lua_runtime, mock_game_state):
        """Test getting entity by ID."""
        entity = Entity(
            entity_id="monster_123",
            name="Goblin",
            entity_type=EntityType.MONSTER,
        )
        mock_game_state.entities["monster_123"] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local entity = brogue.get_entity("monster_123")
            return entity.name
        """)

        assert result == "Goblin"

    def test_get_nonexistent_entity(self, game_context, lua_runtime):
        """Test getting non-existent entity returns nil."""
        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local entity = brogue.get_entity("nonexistent")
            return entity == nil
        """)

        assert result is True


class TestGetEntityAt:
    """Test get_entity_at API."""

    def test_get_entity_at_position(self, game_context, lua_runtime, mock_game_state):
        """Test getting entity at specific position."""
        entity = Entity(
            entity_id="item_1",
            name="Sword",
            x=15,
            y=20,
        )
        mock_game_state.entities["item_1"] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local entity = brogue.get_entity_at(15, 20)
            if entity then
                return entity.name
            else
                return "none"
            end
        """)

        assert result == "Sword"

    def test_get_entity_at_empty_position(self, game_context, lua_runtime):
        """Test getting entity at empty position returns nil."""
        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local entity = brogue.get_entity_at(100, 100)
            return entity == nil
        """)

        assert result is True


class TestGetEntitiesInRange:
    """Test get_entities_in_range API."""

    def test_get_entities_in_range(self, game_context, lua_runtime, mock_game_state):
        """Test getting entities within range."""
        # Create entities at different distances
        entities = [
            Entity(entity_id="e1", name="Close", x=5, y=5, is_alive=True),
            Entity(entity_id="e2", name="Far", x=20, y=20, is_alive=True),
            Entity(entity_id="e3", name="Medium", x=8, y=5, is_alive=True),
        ]

        for entity in entities:
            mock_game_state.entities[entity.entity_id] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        # Get entities within radius 5 of (5, 5)
        result = lua_runtime.execute_script("""
            local entities = brogue.get_entities_in_range(5, 5, 5)
            local count = 0
            for i = 1, #entities do
                count = count + 1
            end
            return count
        """)

        # Should get "Close" and "Medium" (within radius 5)
        assert result == 2

    def test_iterate_entities_in_range(self, game_context, lua_runtime, mock_game_state):
        """Test iterating over entities in range."""
        entities = [
            Entity(entity_id="m1", name="Monster1", x=10, y=10, hp=30, is_alive=True),
            Entity(entity_id="m2", name="Monster2", x=12, y=10, hp=40, is_alive=True),
        ]

        for entity in entities:
            mock_game_state.entities[entity.entity_id] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local entities = brogue.get_entities_in_range(10, 10, 3)
            local total_hp = 0
            for i = 1, #entities do
                total_hp = total_hp + entities[i].hp
            end
            return total_hp
        """)

        assert result == 70


class TestMapQueries:
    """Test map query methods."""

    def test_is_walkable(self, game_context, lua_runtime):
        """Test is_walkable method."""
        # Mock dungeon map
        game_context.game_state.dungeon_map = Mock()
        game_context.game_state.dungeon_map.is_walkable = lambda x, y: x < 50

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local walkable = brogue.is_walkable(10, 10)
            local not_walkable = brogue.is_walkable(100, 10)
            return walkable and not not_walkable
        """)

        assert result is True

    def test_in_bounds(self, game_context, lua_runtime):
        """Test in_bounds method."""
        game_context.game_state.dungeon_map = Mock()
        game_context.game_state.dungeon_map.in_bounds = lambda x, y: 0 <= x < 80 and 0 <= y < 40

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            return brogue.in_bounds(50, 20) and not brogue.in_bounds(100, 20)
        """)

        assert result is True


class TestMessageLog:
    """Test message logging."""

    def test_add_message(self, game_context, lua_runtime, mock_game_state):
        """Test adding messages from Lua."""
        api = GameContextAPI(game_context, lua_runtime.lua)

        lua_runtime.execute_script("""
            brogue.add_message("Test message from Lua")
        """)

        assert "Test message from Lua" in mock_game_state.messages

    def test_add_multiple_messages(self, game_context, lua_runtime, mock_game_state):
        """Test adding multiple messages."""
        api = GameContextAPI(game_context, lua_runtime.lua)

        lua_runtime.execute_script("""
            brogue.add_message("Message 1")
            brogue.add_message("Message 2")
            brogue.add_message("Message 3")
        """)

        assert len(mock_game_state.messages) == 3
        assert "Message 1" in mock_game_state.messages
        assert "Message 2" in mock_game_state.messages
        assert "Message 3" in mock_game_state.messages


class TestGameState:
    """Test game state queries."""

    def test_get_turn_count(self, game_context, lua_runtime, mock_game_state):
        """Test getting turn count."""
        mock_game_state.turn_count = 42
        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("return brogue.get_turn_count()")
        assert result == 42

    def test_get_floor(self, game_context, lua_runtime, mock_game_state):
        """Test getting floor number."""
        mock_game_state.current_floor = 5
        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("return brogue.get_floor()")
        assert result == 5


class TestModifyStat:
    """Test stat modification."""

    def test_modify_hp(self, game_context, lua_runtime, mock_game_state):
        """Test modifying HP."""
        entity = Entity(
            entity_id="test_1",
            hp=100,
            max_hp=100,
        )
        mock_game_state.entities["test_1"] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            brogue.modify_stat("test_1", "hp", -20)
            local entity = brogue.get_entity("test_1")
            return entity.hp
        """)

        assert result == 80

    def test_modify_hp_clamped_at_zero(self, game_context, lua_runtime, mock_game_state):
        """Test that HP can't go below zero."""
        entity = Entity(
            entity_id="test_1",
            hp=50,
            max_hp=100,
        )
        mock_game_state.entities["test_1"] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        lua_runtime.execute_script('brogue.modify_stat("test_1", "hp", -100)')

        assert entity.hp == 0
        assert entity.is_alive is False

    def test_modify_hp_clamped_at_max(self, game_context, lua_runtime, mock_game_state):
        """Test that HP can't exceed max_hp."""
        entity = Entity(
            entity_id="test_1",
            hp=50,
            max_hp=100,
        )
        mock_game_state.entities["test_1"] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        lua_runtime.execute_script('brogue.modify_stat("test_1", "hp", 100)')

        assert entity.hp == 100  # Clamped at max_hp

    def test_modify_custom_stat(self, game_context, lua_runtime, mock_game_state):
        """Test modifying custom stats."""
        entity = Entity(
            entity_id="mage_1",
            stats={"mana": 50, "max_mana": 100}
        )
        mock_game_state.entities["mage_1"] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        lua_runtime.execute_script('brogue.modify_stat("mage_1", "mana", -10)')

        assert entity.stats["mana"] == 40


class TestDealDamage:
    """Test dealing damage."""

    def test_deal_damage(self, game_context, lua_runtime, mock_game_state):
        """Test dealing damage to entity."""
        entity = Entity(
            entity_id="monster_1",
            hp=100,
            max_hp=100,
            defense=5,
        )
        # Mock take_damage method
        entity.take_damage = Mock(return_value=20)
        mock_game_state.entities["monster_1"] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            return brogue.deal_damage("monster_1", 25)
        """)

        entity.take_damage.assert_called_once_with(25)
        assert result == 20  # Mocked return value


class TestHeal:
    """Test healing."""

    def test_heal_entity(self, game_context, lua_runtime, mock_game_state):
        """Test healing entity."""
        entity = Entity(
            entity_id="player_1",
            hp=50,
            max_hp=100,
        )
        mock_game_state.entities["player_1"] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            return brogue.heal("player_1", 30)
        """)

        assert entity.hp == 80
        assert result == 30  # Actual healing amount

    def test_heal_clamped_at_max(self, game_context, lua_runtime, mock_game_state):
        """Test that healing doesn't exceed max_hp."""
        entity = Entity(
            entity_id="player_1",
            hp=90,
            max_hp=100,
        )
        mock_game_state.entities["player_1"] = entity

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            return brogue.heal("player_1", 50)
        """)

        assert entity.hp == 100
        assert result == 10  # Only healed 10 HP


class TestComplexScenarios:
    """Test complex realistic scenarios."""

    def test_fireball_simulation(self, game_context, lua_runtime, mock_game_state):
        """Test simulating a fireball action."""
        # Setup: player and two monsters
        player = Entity(
            entity_id="player_1",
            entity_type=EntityType.PLAYER,
            x=5,
            y=5,
            stats={"mana": 50, "max_mana": 100}
        )
        monster1 = Entity(
            entity_id="m1",
            name="Goblin",
            entity_type=EntityType.MONSTER,
            x=10,
            y=10,
            hp=30,
            max_hp=30,
            is_alive=True,
        )
        monster2 = Entity(
            entity_id="m2",
            name="Orc",
            entity_type=EntityType.MONSTER,
            x=11,
            y=10,
            hp=50,
            max_hp=50,
            is_alive=True,
        )

        mock_game_state.player = player
        mock_game_state.entities["player_1"] = player
        mock_game_state.entities["m1"] = monster1
        mock_game_state.entities["m2"] = monster2

        api = GameContextAPI(game_context, lua_runtime.lua)

        # Execute fireball-like spell
        lua_runtime.execute_script("""
            -- Fireball parameters
            local MANA_COST = 10
            local TARGET_X = 10
            local TARGET_Y = 10
            local AOE_RADIUS = 2
            local DAMAGE = 15

            -- Get player
            local player = brogue.get_player()

            -- Deduct mana
            brogue.modify_stat(player.id, "mana", -MANA_COST)

            -- Get targets in AOE
            local targets = brogue.get_entities_in_range(TARGET_X, TARGET_Y, AOE_RADIUS)

            -- Damage each target
            for i = 1, #targets do
                local target = targets[i]
                if target.entity_type == "MONSTER" then
                    brogue.modify_stat(target.id, "hp", -DAMAGE)
                    brogue.add_message("Fireball hits " .. target.name .. "!")
                end
            end
        """)

        # Verify results
        assert player.stats["mana"] == 40  # 50 - 10
        assert monster1.hp == 15  # 30 - 15
        assert monster2.hp == 35  # 50 - 15
        assert len(mock_game_state.messages) == 2  # Two hit messages


class TestAIHelperMethods:
    """Test AI-specific helper methods."""

    def test_ai_table_exists(self, api, lua_runtime):
        """Test that brogue.ai table is registered."""
        result = lua_runtime.execute_script("return brogue.ai ~= nil")
        assert result is True

    def test_ai_get_target(self, game_context, lua_runtime, mock_game_state):
        """Test AI getting target (player)."""
        player = Entity(
            entity_id="player_1",
            name="Hero",
            entity_type=EntityType.PLAYER,
            x=10,
            y=10,
        )
        mock_game_state.player = player

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local target = brogue.ai.get_target("monster_1")
            return target.name
        """)

        assert result == "Hero"

    def test_ai_is_adjacent_true(self, game_context, lua_runtime, mock_game_state):
        """Test AI adjacency check - adjacent entities."""
        monster = Entity(entity_id="monster_1", x=5, y=5)
        player = Entity(entity_id="player_1", x=6, y=5)
        mock_game_state.entities["monster_1"] = monster
        mock_game_state.entities["player_1"] = player

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            return brogue.ai.is_adjacent("monster_1", "player_1")
        """)

        assert result is True

    def test_ai_is_adjacent_false(self, game_context, lua_runtime, mock_game_state):
        """Test AI adjacency check - non-adjacent entities."""
        monster = Entity(entity_id="monster_1", x=5, y=5)
        player = Entity(entity_id="player_1", x=10, y=10)
        mock_game_state.entities["monster_1"] = monster
        mock_game_state.entities["player_1"] = player

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            return brogue.ai.is_adjacent("monster_1", "player_1")
        """)

        assert result is False

    def test_ai_distance_to(self, game_context, lua_runtime, mock_game_state):
        """Test AI distance calculation."""
        monster = Entity(entity_id="monster_1", x=5, y=5)
        player = Entity(entity_id="player_1", x=10, y=8)
        mock_game_state.entities["monster_1"] = monster
        mock_game_state.entities["player_1"] = player

        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            return brogue.ai.distance_to("monster_1", "player_1")
        """)

        # Manhattan distance: |10-5| + |8-5| = 5 + 3 = 8
        assert result == 8

    def test_ai_attack_descriptor(self, game_context, lua_runtime):
        """Test AI attack action descriptor."""
        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local action = brogue.ai.attack("monster_1", "player_1")
            return action.action, action.target_id
        """)

        assert result == ("attack", "player_1")

    def test_ai_move_towards_descriptor(self, game_context, lua_runtime):
        """Test AI move_towards action descriptor."""
        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local action = brogue.ai.move_towards("monster_1", "player_1")
            return action.action, action.target_id
        """)

        assert result == ("move_towards", "player_1")

    def test_ai_flee_from_descriptor(self, game_context, lua_runtime):
        """Test AI flee_from action descriptor."""
        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local action = brogue.ai.flee_from("monster_1", "player_1")
            return action.action, action.target_id
        """)

        assert result == ("flee_from", "player_1")

    def test_ai_wander_descriptor(self, game_context, lua_runtime):
        """Test AI wander action descriptor."""
        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local action = brogue.ai.wander("monster_1")
            return action.action
        """)

        assert result == "wander"

    def test_ai_idle_descriptor(self, game_context, lua_runtime):
        """Test AI idle action descriptor."""
        api = GameContextAPI(game_context, lua_runtime.lua)

        result = lua_runtime.execute_script("""
            local action = brogue.ai.idle("monster_1")
            return action.action
        """)

        assert result == "idle"
