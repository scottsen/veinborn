"""
Unit tests for LuaAction.

Tests cover:
- Lua action creation and execution
- Script validation
- Error handling
- ActionFactory integration
- Outcome conversion
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock
import lupa

from core.scripting.lua_runtime import LuaRuntime
from core.actions.lua_action import LuaAction
from core.actions.action_factory import ActionFactory
from core.base.action import ActionResult
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
    player = Entity(
        entity_id="player_1",
        name="Hero",
        entity_type=EntityType.PLAYER,
        hp=100,
        max_hp=100,
        x=10,
        y=10,
        stats={"mana": 50, "max_mana": 100}
    )
    mock_game_state.player = player
    mock_game_state.entities["player_1"] = player
    return GameContext(mock_game_state)


@pytest.fixture
def lua_runtime():
    """Create LuaRuntime with function scope (new runtime per test)."""
    return LuaRuntime()


class TestLuaActionCreation:
    """Test LuaAction creation."""

    def test_create_with_script_code(self, lua_runtime):
        """Test creating LuaAction with inline script code."""
        script = """
        function validate(actor_id, params)
            return true
        end

        function execute(actor_id, params)
            return {success = true, took_turn = true}
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        assert action.actor_id == "player_1"
        assert action.action_type == "test_action"

    def test_create_with_script_path(self, lua_runtime):
        """Test creating LuaAction with script file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "test.lua"
            script_path.write_text("""
                function validate(actor_id, params)
                    return true
                end

                function execute(actor_id, params)
                    return {success = true}
                end
            """)

            action = LuaAction(
                actor_id="player_1",
                action_type="test_action",
                lua_runtime=lua_runtime,
                script_path=script_path
            )

            assert action.script_path == script_path

    def test_create_without_script_raises_error(self, lua_runtime):
        """Test that creating action without script raises error."""
        with pytest.raises(ValueError):
            LuaAction(
                actor_id="player_1",
                action_type="test_action",
                lua_runtime=lua_runtime
            )

    def test_create_with_params(self, lua_runtime):
        """Test creating action with parameters."""
        script = """
        function validate(actor_id, params)
            return true
        end
        function execute(actor_id, params)
            return {success = true}
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script,
            x=5,
            y=10,
            power=20
        )

        assert action.params["x"] == 5
        assert action.params["y"] == 10
        assert action.params["power"] == 20


class TestLuaActionValidation:
    """Test LuaAction validation."""

    def test_validate_returns_true(self, game_context, lua_runtime):
        """Test validation with script that returns true."""
        script = """
        function validate(actor_id, params)
            return true
        end
        function execute(actor_id, params)
            return {success = true}
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        assert action.validate(game_context) is True

    def test_validate_returns_false(self, game_context, lua_runtime):
        """Test validation with script that returns false."""
        script = """
        function validate(actor_id, params)
            return false
        end
        function execute(actor_id, params)
            return {success = true}
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        assert action.validate(game_context) is False

    def test_validate_with_game_context_access(self, game_context, lua_runtime):
        """Test validation accessing game context."""
        script = """
        function validate(actor_id, params)
            local player = brogue.get_player()
            return player.hp > 50
        end
        function execute(actor_id, params)
            return {success = true}
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        # Player has 100 HP, so should validate
        assert action.validate(game_context) is True

        # Lower player HP
        game_context.get_player().hp = 40
        assert action.validate(game_context) is False

    def test_validate_with_params(self, game_context, lua_runtime):
        """Test validation using parameters."""
        script = """
        function validate(actor_id, params)
            return params.required_mana <= 50
        end
        function execute(actor_id, params)
            return {success = true}
        end
        """

        # Should validate with mana cost 30
        action1 = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script,
            required_mana=30
        )
        assert action1.validate(game_context) is True

        # Should fail with mana cost 60
        action2 = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script,
            required_mana=60
        )
        assert action2.validate(game_context) is False


class TestLuaActionExecution:
    """Test LuaAction execution."""

    def test_execute_success(self, game_context, lua_runtime):
        """Test successful execution."""
        script = """
        function validate(actor_id, params)
            return true
        end
        function execute(actor_id, params)
            brogue.add_message("Test action executed!")
            return {
                success = true,
                took_turn = true,
                messages = {},
                events = {}
            }
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS
        assert outcome.took_turn is True
        assert "Test action executed!" in game_context.game_state.messages

    def test_execute_failure(self, game_context, lua_runtime):
        """Test failed execution."""
        script = """
        function validate(actor_id, params)
            return true
        end
        function execute(actor_id, params)
            return {
                success = false,
                took_turn = false,
                messages = {},
                events = {}
            }
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.FAILURE
        assert outcome.took_turn is False

    def test_execute_with_validation_failure(self, game_context, lua_runtime):
        """Test execution when validation fails."""
        script = """
        function validate(actor_id, params)
            return false
        end
        function execute(actor_id, params)
            return {success = true}
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.FAILURE
        assert "not valid" in outcome.messages[0].lower()

    def test_execute_with_messages(self, game_context, lua_runtime):
        """Test execution with outcome messages."""
        script = """
        function validate(actor_id, params)
            return true
        end
        function execute(actor_id, params)
            return {
                success = true,
                took_turn = true,
                messages = {"Message 1", "Message 2", "Message 3"},
                events = {}
            }
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        outcome = action.execute(game_context)

        assert len(outcome.messages) == 3
        assert "Message 1" in outcome.messages
        assert "Message 2" in outcome.messages
        assert "Message 3" in outcome.messages

    def test_execute_with_events(self, game_context, lua_runtime):
        """Test execution with events."""
        script = """
        function validate(actor_id, params)
            return true
        end
        function execute(actor_id, params)
            return {
                success = true,
                took_turn = true,
                messages = {},
                events = {
                    {type = "damage", target_id = "monster_1", amount = 10},
                    {type = "heal", target_id = "player_1", amount = 5}
                }
            }
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        outcome = action.execute(game_context)

        assert len(outcome.events) == 2
        assert outcome.events[0]["type"] == "damage"
        assert outcome.events[0]["target_id"] == "monster_1"
        assert outcome.events[1]["type"] == "heal"

    def test_execute_with_simple_boolean_return(self, game_context, lua_runtime):
        """Test backward compatibility with simple boolean return."""
        script = """
        function validate(actor_id, params)
            return true
        end
        function execute(actor_id, params)
            return true
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS


class TestLuaActionErrors:
    """Test error handling in LuaAction."""

    def test_missing_validate_function(self, game_context, lua_runtime):
        """Test error when validate function is missing."""
        script = """
        function execute(actor_id, params)
            return {success = true}
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        # Should return False and log error
        result = action.validate(game_context)
        assert result is False

    def test_missing_execute_function(self, game_context, lua_runtime):
        """Test error when execute function is missing."""
        script = """
        function validate(actor_id, params)
            return true
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        # Should return failure outcome
        outcome = action.execute(game_context)
        assert outcome.result == ActionResult.FAILURE

    def test_lua_runtime_error_in_validate(self, game_context, lua_runtime):
        """Test handling of Lua runtime error in validate."""
        script = """
        function validate(actor_id, params)
            error("Intentional error in validate")
        end
        function execute(actor_id, params)
            return {success = true}
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        # Should return false and log error
        result = action.validate(game_context)
        assert result is False

    def test_lua_runtime_error_in_execute(self, game_context, lua_runtime):
        """Test handling of Lua runtime error in execute."""
        script = """
        function validate(actor_id, params)
            return true
        end
        function execute(actor_id, params)
            error("Intentional error in execute")
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="test_action",
            lua_runtime=lua_runtime,
            script_code=script
        )

        # Should return failure outcome
        outcome = action.execute(game_context)
        assert outcome.result == ActionResult.FAILURE


class TestActionFactoryIntegration:
    """Test integration with ActionFactory."""

    def test_register_lua_action(self, game_context, lua_runtime):
        """Test registering Lua action with ActionFactory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test Lua script
            lua_runtime.scripts_dir = Path(tmpdir)
            script_path = Path(tmpdir) / "test_spell.lua"
            script_path.write_text("""
                function validate(actor_id, params)
                    return true
                end

                function execute(actor_id, params)
                    brogue.add_message("Spell cast!")
                    return {success = true, took_turn = true}
                end
            """)

            factory = ActionFactory(game_context)
            factory.register_lua_action(
                "test_spell",
                str(script_path),
                lua_runtime,
                "Cast a test spell"
            )

            # Create action through factory
            action = factory.create("test_spell", actor_id="player_1")

            assert action is not None
            assert isinstance(action, LuaAction)

    def test_create_and_execute_via_factory(self, game_context, lua_runtime):
        """Test creating and executing Lua action via factory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lua_runtime.scripts_dir = Path(tmpdir)
            script_path = Path(tmpdir) / "heal.lua"
            script_path.write_text("""
                function validate(actor_id, params)
                    local player = brogue.get_player()
                    return player.hp < player.max_hp
                end

                function execute(actor_id, params)
                    brogue.heal(actor_id, 20)
                    brogue.add_message("You feel better!")
                    return {success = true, took_turn = true}
                end
            """)

            # Lower player HP
            game_context.get_player().hp = 50

            factory = ActionFactory(game_context)
            factory.register_lua_action("heal", str(script_path), lua_runtime)

            action = factory.create("heal", actor_id="player_1")
            outcome = action.execute(game_context)

            assert outcome.result == ActionResult.SUCCESS
            assert game_context.get_player().hp == 70  # 50 + 20
            assert "You feel better!" in game_context.game_state.messages


class TestComplexScenarios:
    """Test complex realistic scenarios."""

    def test_spell_with_mana_cost(self, game_context, lua_runtime):
        """Test spell that costs mana."""
        script = """
        local MANA_COST = 15

        function validate(actor_id, params)
            local player = brogue.get_player()
            if player.stats.mana < MANA_COST then
                brogue.add_message("Not enough mana!")
                return false
            end
            return true
        end

        function execute(actor_id, params)
            -- Deduct mana
            brogue.modify_stat(actor_id, "mana", -MANA_COST)
            brogue.add_message("Magic missile cast!")

            return {
                success = true,
                took_turn = true,
                messages = {"A bolt of energy shoots forth!"},
                events = {
                    {type = "spell_cast", spell = "magic_missile", mana_cost = MANA_COST}
                }
            }
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="magic_missile",
            lua_runtime=lua_runtime,
            script_code=script
        )

        # Player has 50 mana
        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS
        assert game_context.get_player().stats["mana"] == 35  # 50 - 15
        assert "magic_missile" in outcome.events[0]["spell"]

    def test_aoe_damage_spell(self, game_context, lua_runtime):
        """Test AOE damage spell affecting multiple targets."""
        # Add monsters
        monster1 = Entity(
            entity_id="m1",
            name="Goblin",
            entity_type=EntityType.MONSTER,
            x=12,
            y=12,
            hp=30,
            max_hp=30,
            is_alive=True
        )
        monster2 = Entity(
            entity_id="m2",
            name="Orc",
            entity_type=EntityType.MONSTER,
            x=13,
            y=12,
            hp=50,
            max_hp=50,
            is_alive=True
        )
        game_context.game_state.entities["m1"] = monster1
        game_context.game_state.entities["m2"] = monster2

        script = """
        local DAMAGE = 15
        local AOE_RADIUS = 3

        function validate(actor_id, params)
            return params.target_x ~= nil and params.target_y ~= nil
        end

        function execute(actor_id, params)
            local targets = brogue.get_entities_in_range(params.target_x, params.target_y, AOE_RADIUS)
            local hit_count = 0

            for i = 1, #targets do
                local target = targets[i]
                if target.entity_type == "MONSTER" then
                    brogue.modify_stat(target.id, "hp", -DAMAGE)
                    brogue.add_message("Hit " .. target.name .. " for " .. DAMAGE .. " damage!")
                    hit_count = hit_count + 1
                end
            end

            return {
                success = true,
                took_turn = true,
                messages = {"Explosion hits " .. hit_count .. " enemies!"}
            }
        end
        """

        action = LuaAction(
            actor_id="player_1",
            action_type="explosion",
            lua_runtime=lua_runtime,
            script_code=script,
            target_x=12,
            target_y=12
        )

        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS
        assert monster1.hp == 15  # 30 - 15
        assert monster2.hp == 35  # 50 - 15
        assert "2 enemies" in outcome.messages[0]
