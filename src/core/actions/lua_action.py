"""
LuaAction - action implemented via Lua script.

This module enables custom actions to be defined in Lua scripts
and executed within the game engine.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
import lupa

from ..base.action import Action, ActionOutcome, ActionResult
from ..base.game_context import GameContext
from ..scripting.lua_runtime import LuaRuntime
from ..scripting.game_context_api import GameContextAPI

logger = logging.getLogger(__name__)


class LuaAction(Action):
    """
    Action implemented in Lua script.

    The Lua script must define two functions:
    - validate(actor_id, params) -> boolean
    - execute(actor_id, params) -> outcome_table

    Example Lua script:
        function validate(actor_id, params)
            local player = brogue.get_player()
            return player.hp > 0
        end

        function execute(actor_id, params)
            brogue.add_message("Lua action executed!")
            return {
                success = true,
                took_turn = true,
                messages = {},
                events = {}
            }
        end
    """

    def __init__(
        self,
        actor_id: str,
        action_type: str,
        lua_runtime: LuaRuntime,
        script_path: Optional[Path] = None,
        script_code: Optional[str] = None,
        **params
    ):
        """
        Initialize Lua action.

        Args:
            actor_id: Entity ID of actor
            action_type: Action type identifier
            lua_runtime: Shared LuaRuntime instance
            script_path: Path to Lua script file (mutually exclusive with script_code)
            script_code: Lua script code string (mutually exclusive with script_path)
            **params: Parameters to pass to Lua script
        """
        super().__init__(actor_id)
        self.action_type = action_type
        self.lua_runtime = lua_runtime
        self.script_path = script_path
        self.script_code = script_code
        self.params = params
        self._script_loaded = False

        if not script_path and not script_code:
            raise ValueError("Either script_path or script_code must be provided")

        logger.debug(
            f"LuaAction created: {action_type}",
            extra={"actor_id": actor_id, "params": params}
        )

    def _load_script(self) -> None:
        """
        Load Lua script into runtime.

        Raises:
            FileNotFoundError: If script file doesn't exist
            lupa.LuaError: If script has syntax errors
        """
        if self._script_loaded:
            return

        try:
            if self.script_path:
                logger.debug(f"Loading Lua script: {self.script_path}")
                self.lua_runtime.load_script_file(str(self.script_path))
            elif self.script_code:
                logger.debug(f"Executing inline Lua script for {self.action_type}")
                self.lua_runtime.execute_script(self.script_code)

            # Verify required functions exist
            if not self._verify_script_functions():
                raise ValueError(
                    f"Lua script for {self.action_type} missing validate() or execute() function"
                )

            self._script_loaded = True
            logger.debug(f"Lua script loaded successfully: {self.action_type}")

        except Exception as e:
            logger.error(f"Failed to load Lua script for {self.action_type}: {e}")
            raise

    def _verify_script_functions(self) -> bool:
        """
        Verify that required functions exist in Lua script.

        Returns:
            True if validate and execute functions exist
        """
        try:
            lua_globals = self.lua_runtime.lua.globals()
            # Access Lua table items with bracket notation, not .get()
            has_validate = lua_globals["validate"] is not None
            has_execute = lua_globals["execute"] is not None

            if not has_validate:
                logger.error(f"Lua script missing validate() function: {self.action_type}")
            if not has_execute:
                logger.error(f"Lua script missing execute() function: {self.action_type}")

            return has_validate and has_execute
        except (KeyError, AttributeError):
            # Function doesn't exist
            logger.error(f"Lua script missing validate() or execute() function: {self.action_type}")
            return False
        except Exception as e:
            logger.error(f"Error verifying Lua functions: {e}")
            return False

    def validate(self, context: GameContext) -> bool:
        """
        Validate action by calling Lua validate() function.

        Args:
            context: Game context

        Returns:
            True if action is valid, False otherwise
        """
        try:
            # Load script if not already loaded
            self._load_script()

            # Register GameContext API in Lua
            api = GameContextAPI(context, self.lua_runtime.lua)

            # Convert params to Lua table
            lua_params = self._params_to_lua()

            # Call validate function
            result = self.lua_runtime.call_function(
                "validate",
                self.actor_id,
                lua_params
            )

            is_valid = bool(result)
            logger.debug(
                f"Lua action validation: {self.action_type} = {is_valid}",
                extra={"actor_id": self.actor_id}
            )

            return is_valid

        except Exception as e:
            logger.error(
                f"Error in Lua validate() for {self.action_type}: {e}",
                exc_info=True
            )
            return False

    def execute(self, context: GameContext) -> ActionOutcome:
        """
        Execute action by calling Lua execute() function.

        Args:
            context: Game context

        Returns:
            ActionOutcome from Lua script
        """
        try:
            # Validate before executing
            if not self.validate(context):
                logger.warning(f"Lua action validation failed: {self.action_type}")
                return ActionOutcome.failure(f"{self.action_type} action is not valid")

            # Register GameContext API in Lua
            api = GameContextAPI(context, self.lua_runtime.lua)

            # Convert params to Lua table
            lua_params = self._params_to_lua()

            # Call execute function
            outcome_table = self.lua_runtime.call_function(
                "execute",
                self.actor_id,
                lua_params
            )

            # Convert Lua table to ActionOutcome
            outcome = self._table_to_outcome(outcome_table)

            logger.debug(
                f"Lua action executed: {self.action_type} -> {outcome.result.name}",
                extra={"actor_id": self.actor_id}
            )

            return outcome

        except Exception as e:
            logger.error(
                f"Error in Lua execute() for {self.action_type}: {e}",
                exc_info=True
            )
            return ActionOutcome.failure(f"Error executing {self.action_type}: {e}")

    def _params_to_lua(self) -> Any:
        """
        Convert Python params dict to Lua table.

        Returns:
            Lua table with parameters
        """
        lua_table = self.lua_runtime.lua.table()
        for key, value in self.params.items():
            lua_table[key] = value
        return lua_table

    def _table_to_outcome(self, outcome_table: Any) -> ActionOutcome:
        """
        Convert Lua outcome table to ActionOutcome.

        Expected Lua table format:
        {
            success = true/false,
            took_turn = true/false,
            messages = {"message1", "message2"},
            events = {{type="damage", ...}, ...}
        }

        Args:
            outcome_table: Lua table with outcome data

        Returns:
            ActionOutcome instance
        """
        try:
            # Handle simple boolean return (backward compatibility)
            if isinstance(outcome_table, bool):
                if outcome_table:
                    return ActionOutcome.success()
                else:
                    return ActionOutcome.failure()

            # Extract fields from Lua table (use try/except for optional fields)
            try:
                success = bool(outcome_table["success"])
            except (KeyError, TypeError):
                success = True

            try:
                took_turn = bool(outcome_table["took_turn"])
            except (KeyError, TypeError):
                took_turn = True

            # Extract messages
            messages = []
            try:
                lua_messages = outcome_table["messages"]
                if lua_messages:
                    # Lua tables are 1-indexed
                    for i in range(1, len(lua_messages) + 1):
                        msg = lua_messages[i]
                        if msg:
                            messages.append(str(msg))
            except (KeyError, TypeError):
                pass

            # Extract events
            events = []
            try:
                lua_events = outcome_table["events"]
            except (KeyError, TypeError):
                lua_events = None

            if lua_events:
                for i in range(1, len(lua_events) + 1):
                    event = lua_events[i]
                    if event:
                        # Convert Lua table to Python dict
                        events.append(self._lua_table_to_dict(event))

            # Determine result
            result = ActionResult.SUCCESS if success else ActionResult.FAILURE

            return ActionOutcome(
                result=result,
                took_turn=took_turn,
                messages=messages,
                events=events
            )

        except Exception as e:
            logger.error(f"Error converting Lua outcome to ActionOutcome: {e}")
            return ActionOutcome.failure("Error processing action outcome")

    def _lua_table_to_dict(self, lua_table: Any) -> Dict[str, Any]:
        """
        Convert Lua table to Python dictionary.

        Args:
            lua_table: Lua table

        Returns:
            Python dictionary
        """
        result = {}
        try:
            # Iterate over Lua table (both array and hash parts)
            for key, value in lua_table.items():
                # Check if value is a Lua table (has .items() method)
                if hasattr(value, 'items'):
                    result[str(key)] = self._lua_table_to_dict(value)
                else:
                    result[str(key)] = value
        except Exception as e:
            logger.warning(f"Error converting Lua table to dict: {e}")

        return result

    def to_dict(self) -> dict:
        """
        Serialize Lua action.

        Returns:
            Dictionary representation
        """
        return {
            "action_type": "lua_action",
            "actor_id": self.actor_id,
            "lua_action_type": self.action_type,
            "script_path": str(self.script_path) if self.script_path else None,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LuaAction':
        """
        Deserialize Lua action.

        Note: This requires access to LuaRuntime which isn't serialized.
        For proper deserialization, use a factory that provides the runtime.

        Args:
            data: Serialized action data

        Returns:
            LuaAction instance
        """
        # This is a placeholder - in practice, deserialization would need
        # access to the LuaRuntime instance from the game
        raise NotImplementedError(
            "LuaAction deserialization requires LuaRuntime context. "
            "Use ActionFactory.create() instead."
        )

    def get_action_type(self) -> str:
        """Return action type for serialization."""
        return f"lua_{self.action_type}"
