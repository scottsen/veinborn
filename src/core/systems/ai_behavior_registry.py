"""
AI Behavior Registry.

Manages registration and lookup of AI behaviors (Python and Lua).
Enables dynamic registration of custom AI behavior functions.
"""

import logging
from typing import Dict, Callable, Optional

logger = logging.getLogger(__name__)


class AIBehaviorRegistry:
    """
    Registry for custom AI behaviors (Python and Lua).

    Enables dynamic registration of AI behavior functions.
    Lua behaviors are wrapped and integrated seamlessly with Python behaviors.

    Example:
        registry = AIBehaviorRegistry()
        registry.register_python_behavior("aggressive", aggressive_fn)
        registry.register_lua_behavior("berserker", lua_runtime, "scripts/ai/berserker.lua")

        behavior = registry.get_behavior("aggressive")
        behavior(monster, config)
    """

    def __init__(self):
        """Initialize empty behavior registry."""
        self._behaviors: Dict[str, Callable] = {}
        logger.debug("AIBehaviorRegistry initialized")

    def register_python_behavior(
        self,
        ai_type: str,
        behavior_fn: Callable
    ) -> None:
        """
        Register Python behavior function.

        Args:
            ai_type: Behavior type name (e.g., "aggressive", "defensive")
            behavior_fn: Function with signature (monster, config) -> None
        """
        if ai_type in self._behaviors:
            logger.warning(f"Overwriting existing behavior: {ai_type}")

        self._behaviors[ai_type] = behavior_fn
        logger.debug(f"Registered Python behavior: {ai_type}")

    def register_lua_behavior(
        self,
        ai_type: str,
        lua_runtime,
        script_path: str
    ) -> None:
        """
        Register Lua behavior from script.

        Lua behavior must implement:
            function update(monster, config)
                return {action="...", ...}
            end

        Args:
            ai_type: Behavior type name (e.g., "berserker", "sniper")
            lua_runtime: LuaRuntime instance
            script_path: Path to Lua script file

        Raises:
            ValueError: If Lua script doesn't define update() function
            FileNotFoundError: If script_path doesn't exist
        """
        from .lua_ai_behavior import LuaBehaviorWrapper

        if ai_type in self._behaviors:
            logger.warning(f"Overwriting existing behavior: {ai_type}")

        try:
            wrapper = LuaBehaviorWrapper(lua_runtime, script_path)
            self._behaviors[ai_type] = wrapper.execute
            logger.info(f"Registered Lua behavior: {ai_type} from {script_path}")
        except Exception as e:
            logger.error(f"Failed to register Lua behavior {ai_type}: {e}")
            raise

    def unregister_behavior(self, ai_type: str) -> bool:
        """
        Unregister a behavior.

        Args:
            ai_type: Behavior type name to remove

        Returns:
            True if behavior was removed, False if not found
        """
        if ai_type in self._behaviors:
            del self._behaviors[ai_type]
            logger.debug(f"Unregistered behavior: {ai_type}")
            return True
        return False

    def get_behavior(self, ai_type: str) -> Optional[Callable]:
        """
        Get behavior function by type.

        Args:
            ai_type: Behavior type name

        Returns:
            Behavior function, or None if not found
        """
        return self._behaviors.get(ai_type)

    def has_behavior(self, ai_type: str) -> bool:
        """
        Check if behavior is registered.

        Args:
            ai_type: Behavior type name

        Returns:
            True if behavior exists, False otherwise
        """
        return ai_type in self._behaviors

    def list_behaviors(self) -> list[str]:
        """
        List all registered behavior types.

        Returns:
            List of behavior type names
        """
        return list(self._behaviors.keys())

    def clear(self) -> None:
        """Clear all registered behaviors."""
        count = len(self._behaviors)
        self._behaviors.clear()
        logger.debug(f"Cleared {count} behaviors from registry")
