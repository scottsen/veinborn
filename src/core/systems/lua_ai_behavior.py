"""
Lua AI Behavior Wrapper.

Wraps Lua AI behavior scripts for execution in AISystem.
Handles type conversions and error handling.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..scripting.game_context_api import GameContextAPI

logger = logging.getLogger(__name__)


class LuaBehaviorWrapper:
    """
    Wraps Lua AI behavior script for execution in AISystem.

    Converts between Python/Lua types and handles errors gracefully.
    Lua behaviors are called with monster and config, and return action descriptors.

    Expected Lua interface:
        function update(monster, config)
            -- AI decision logic
            return {action = "attack", target_id = "player_1"}
        end

    Action descriptors:
        {action = "attack", target_id = "..."}
        {action = "move_towards", target_id = "..."}
        {action = "flee_from", target_id = "..."}
        {action = "wander"}
        {action = "idle"}
    """

    def __init__(self, lua_runtime, script_path: str):
        """
        Initialize Lua behavior wrapper.

        Args:
            lua_runtime: LuaRuntime instance
            script_path: Path to Lua behavior script

        Raises:
            FileNotFoundError: If script doesn't exist
            ValueError: If script doesn't define update() function
        """
        self.lua_runtime = lua_runtime
        self.script_path = script_path
        self._validate_script_path()
        self._load_script()
        logger.info(f"Loaded Lua AI behavior from {script_path}")

    def _validate_script_path(self) -> None:
        """
        Validate that script path exists.

        Raises:
            FileNotFoundError: If script doesn't exist
        """
        path = Path(self.script_path)
        if not path.exists():
            raise FileNotFoundError(f"Lua AI script not found: {self.script_path}")

    def _load_script(self) -> None:
        """
        Load Lua script and validate structure.

        Raises:
            ValueError: If script doesn't define update() function
        """
        try:
            # Load the script file
            self.lua_runtime.load_script_file(self.script_path)

            # Validate required function exists
            if not self.lua_runtime.has_function("update"):
                raise ValueError(
                    f"Lua AI behavior must define update(monster, config) function: "
                    f"{self.script_path}"
                )

            logger.debug(f"Validated Lua AI behavior: {self.script_path}")
        except Exception as e:
            logger.error(f"Failed to load Lua AI behavior {self.script_path}: {e}")
            raise

    def execute(self, monster, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute Lua behavior and return action descriptor.

        This method is called by AISystem during monster AI updates.
        It converts Python objects to Lua, calls the update() function,
        and converts the result back to Python.

        Args:
            monster: Monster entity
            config: Behavior configuration from YAML

        Returns:
            Action descriptor dict: {action: str, ...}
            None if error occurs (caller should handle fallback)

        Raises:
            No exceptions - errors are logged and None is returned
        """
        try:
            # Get context from monster (available via entity manager)
            context = monster.context if hasattr(monster, 'context') else None
            if not context:
                logger.error("Monster has no context - cannot execute Lua AI")
                return None

            # Prepare GameContext API for Lua
            api = GameContextAPI(context, self.lua_runtime.lua)

            # Convert monster to Lua table
            monster_table = api._entity_to_lua(monster)

            # Convert config to Lua table
            config_table = self._config_to_lua(config)

            # Call Lua update() function
            result = self.lua_runtime.call_function(
                "update",
                monster_table,
                config_table
            )

            # Parse and validate result
            action_descriptor = self._parse_action_descriptor(result)

            if action_descriptor:
                logger.debug(
                    f"Lua AI {self.script_path} returned: {action_descriptor['action']}"
                )

            return action_descriptor

        except Exception as e:
            logger.error(f"Error executing Lua AI behavior {self.script_path}: {e}")
            return None

    def _config_to_lua(self, config: Dict[str, Any]) -> Any:
        """
        Convert Python config dict to Lua table.

        Args:
            config: Configuration dictionary

        Returns:
            Lua table with config values
        """
        lua_table = self.lua_runtime.lua.table()
        for key, value in config.items():
            lua_table[key] = value
        return lua_table

    def _parse_action_descriptor(
        self,
        result: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Parse and validate action descriptor from Lua.

        Args:
            result: Return value from Lua update() function

        Returns:
            Validated action descriptor dict, or None if invalid
        """
        if result is None:
            logger.warning(f"Lua AI {self.script_path} returned nil")
            return None

        # Convert Lua table to Python dict
        if hasattr(result, 'items'):
            # lupa.LuaTable - convert to dict
            action_dict = dict(result.items())
        elif isinstance(result, dict):
            # Already a dict
            action_dict = result
        else:
            logger.error(
                f"Lua AI {self.script_path} returned invalid type: {type(result)}"
            )
            return None

        # Validate action field exists
        if 'action' not in action_dict:
            logger.error(
                f"Lua AI {self.script_path} returned descriptor without 'action' field"
            )
            return None

        # Validate action type
        valid_actions = {'attack', 'move_towards', 'flee_from', 'wander', 'idle'}
        action = action_dict.get('action')

        if action not in valid_actions:
            logger.warning(
                f"Lua AI {self.script_path} returned unknown action: {action}"
            )

        return action_dict

    def __repr__(self) -> str:
        """String representation."""
        return f"LuaBehaviorWrapper({self.script_path})"
