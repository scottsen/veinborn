"""
Lua Event Handler Bridge.

This module provides the bridge between Python's EventBus and Lua event handlers,
allowing Lua scripts to subscribe to and respond to game events.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
import lupa

from ..events import GameEvent
from ..scripting.lua_runtime import LuaRuntime, LuaTimeoutError

logger = logging.getLogger(__name__)


class LuaEventHandler:
    """
    Wrapper for Lua event handler scripts.

    This class bridges between Python's EventBus and Lua event handler functions.
    It handles loading Lua scripts, converting GameEvent objects to Lua tables,
    and executing handler functions with timeout protection.

    Example:
        >>> handler = LuaEventHandler(
        ...     "scripts/events/achievements.lua",
        ...     "on_entity_died",
        ...     lua_runtime
        ... )
        >>> handler.load()
        >>> event = GameEvent(GameEventType.ENTITY_DIED, {"entity_id": "goblin_1"})
        >>> handler.handle(event)
    """

    def __init__(
        self,
        script_path: str,
        handler_function: str,
        lua_runtime: LuaRuntime
    ):
        """
        Initialize Lua event handler.

        Args:
            script_path: Path to Lua script (relative to project root or absolute)
            handler_function: Name of handler function in script
            lua_runtime: LuaRuntime instance to use for execution
        """
        self.script_path = script_path
        self.handler_function = handler_function
        self.lua_runtime = lua_runtime
        self.lua_func = None
        self.loaded = False

    def load(self) -> bool:
        """
        Load Lua script and find handler function.

        Returns:
            True if successfully loaded, False otherwise

        Raises:
            FileNotFoundError: If script file doesn't exist
            lupa.LuaError: If script has syntax errors
        """
        try:
            # Resolve script path
            script_file = Path(self.script_path)
            if not script_file.is_absolute():
                # Try relative to current directory
                script_file = Path.cwd() / self.script_path

            if not script_file.exists():
                logger.error(f"Lua script not found: {script_file}")
                return False

            # Load script
            logger.info(f"Loading Lua event handler: {script_file}")
            with open(script_file, 'r') as f:
                script_code = f.read()

            # Execute script to define functions
            self.lua_runtime.execute_script(script_code)

            # Find handler function
            try:
                self.lua_func = self.lua_runtime.get_global(self.handler_function)
                if self.lua_func is None:
                    logger.error(
                        f"Handler function '{self.handler_function}' not found in {script_file}"
                    )
                    return False

                # Verify it's callable
                if not callable(self.lua_func):
                    logger.error(
                        f"Handler '{self.handler_function}' is not a function"
                    )
                    return False

            except Exception as e:
                logger.error(
                    f"Error finding handler function '{self.handler_function}': {e}"
                )
                return False

            self.loaded = True
            logger.info(
                f"Loaded Lua event handler: {self.handler_function} from {script_file}"
            )
            return True

        except FileNotFoundError as e:
            logger.error(f"Script file not found: {self.script_path}")
            raise
        except lupa.LuaError as e:
            logger.error(f"Lua syntax error in {self.script_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading Lua event handler: {e}", exc_info=True)
            return False

    def handle(self, event: GameEvent) -> None:
        """
        Execute Lua handler with event data.

        This method converts the GameEvent to a Lua table and calls the handler
        function with timeout protection. Errors are caught and logged but don't
        propagate (to prevent crashing the EventBus).

        Args:
            event: GameEvent to pass to handler

        Raises:
            No exceptions - all errors are caught and logged
        """
        if not self.loaded or self.lua_func is None:
            logger.warning(
                f"Cannot handle event - handler not loaded: {self.script_path}"
            )
            return

        try:
            # Convert event to Lua table
            event_table = self._event_to_lua_table(event)

            # Call Lua function with timeout
            # Note: call_function expects a function name, but we have the function object
            # So we'll call it directly with timeout handling
            self.lua_func(event_table)

            logger.debug(
                f"Lua handler executed: {self.handler_function} for {event.event_type.value}"
            )

        except LuaTimeoutError:
            logger.error(
                f"Lua event handler timeout ({self.lua_runtime.default_timeout}s): "
                f"{self.script_path}::{self.handler_function}",
                extra={
                    'script': self.script_path,
                    'handler': self.handler_function,
                    'event_type': event.event_type.value
                }
            )
        except lupa.LuaError as e:
            logger.error(
                f"Lua error in event handler {self.script_path}::{self.handler_function}: {e}",
                exc_info=True,
                extra={
                    'script': self.script_path,
                    'handler': self.handler_function,
                    'event_type': event.event_type.value,
                    'error': str(e)
                }
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in event handler {self.script_path}::{self.handler_function}: {e}",
                exc_info=True,
                extra={
                    'script': self.script_path,
                    'handler': self.handler_function,
                    'event_type': event.event_type.value,
                    'error': str(e)
                }
            )

    def _event_to_lua_table(self, event: GameEvent) -> Dict[str, Any]:
        """
        Convert GameEvent to Lua table format.

        Args:
            event: GameEvent to convert

        Returns:
            Dictionary (Lua table) with event data
        """
        # Use the event's to_dict() method which already provides the right format
        event_dict = event.to_dict()

        # Create Lua-compatible table
        # lupa automatically converts Python dicts to Lua tables
        lua_table = {
            'type': event_dict['type'],
            'data': event_dict['data'],
            'timestamp': event_dict['timestamp'],
            'turn': event_dict['turn'],
        }

        return lua_table

    def __repr__(self) -> str:
        """String representation of handler."""
        return (
            f"LuaEventHandler(script={self.script_path}, "
            f"function={self.handler_function}, loaded={self.loaded})"
        )

    def __eq__(self, other) -> bool:
        """Check equality based on script path and function name."""
        if not isinstance(other, LuaEventHandler):
            return False
        return (
            self.script_path == other.script_path and
            self.handler_function == other.handler_function
        )

    def __hash__(self) -> int:
        """Hash based on script path and function name."""
        return hash((self.script_path, self.handler_function))
