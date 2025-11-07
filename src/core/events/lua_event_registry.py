"""
Lua Event Registry.

This module manages Lua event handler lifecycle, loading, and registration.
It tracks which scripts are subscribed to which events and provides auto-loading
from the scripts/events/ directory.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict

from ..events import GameEvent, GameEventType, EventBus
from ..scripting.lua_runtime import LuaRuntime
from .lua_event_handler import LuaEventHandler

logger = logging.getLogger(__name__)


class LuaEventRegistry:
    """
    Registry for Lua event handler scripts.

    This class manages the lifecycle of Lua event handlers, including:
    - Loading scripts from directory
    - Tracking subscriptions
    - Preventing duplicates
    - Auto-detecting handlers via annotations

    Example:
        >>> registry = LuaEventRegistry(lua_runtime, event_bus)
        >>> registry.register(
        ...     GameEventType.ENTITY_DIED,
        ...     "scripts/events/achievements.lua",
        ...     "on_entity_died"
        ... )
        >>> count = registry.load_from_directory("scripts/events")
    """

    def __init__(self, lua_runtime: LuaRuntime, event_bus: EventBus):
        """
        Initialize Lua event registry.

        Args:
            lua_runtime: LuaRuntime instance for executing handlers
            event_bus: EventBus instance for subscribing handlers
        """
        self.lua_runtime = lua_runtime
        self.event_bus = event_bus

        # Track handlers by script path
        self.handlers: Dict[str, LuaEventHandler] = {}

        # Track subscriptions: event_type -> list of script paths
        self.subscriptions: Dict[GameEventType, List[str]] = defaultdict(list)

        # Track which scripts are subscribed to which events (reverse index)
        self.script_events: Dict[str, Set[GameEventType]] = defaultdict(set)

    def register(
        self,
        event_type: GameEventType,
        script_path: str,
        handler_function: str
    ) -> bool:
        """
        Register Lua script as event handler.

        This loads the script, validates the handler function exists,
        and subscribes it to the EventBus.

        Args:
            event_type: Event type to subscribe to
            script_path: Path to Lua script
            handler_function: Name of handler function in script

        Returns:
            True if successfully registered, False otherwise
        """
        # Create handler key (script + function)
        handler_key = f"{script_path}::{handler_function}"

        try:
            # Check if already registered for this event
            if script_path in self.subscriptions[event_type]:
                logger.warning(
                    f"Handler already registered: {handler_key} for {event_type.value}"
                )
                return False

            # Create or get existing handler
            if handler_key not in self.handlers:
                handler = LuaEventHandler(
                    script_path,
                    handler_function,
                    self.lua_runtime
                )

                # Load the handler
                if not handler.load():
                    logger.error(f"Failed to load handler: {handler_key}")
                    return False

                self.handlers[handler_key] = handler
            else:
                handler = self.handlers[handler_key]

            # Subscribe to EventBus
            self.event_bus.subscribe_lua(event_type, handler)

            # Track subscription
            self.subscriptions[event_type].append(script_path)
            self.script_events[script_path].add(event_type)

            logger.info(
                f"Registered Lua event handler: {handler_function} "
                f"({script_path}) → {event_type.value}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error registering Lua event handler {handler_key}: {e}",
                exc_info=True
            )
            return False

    def unregister(self, event_type: GameEventType, script_path: str) -> bool:
        """
        Unregister Lua event handler.

        Args:
            event_type: Event type to unsubscribe from
            script_path: Path to script to unsubscribe

        Returns:
            True if successfully unregistered, False if not found
        """
        try:
            if script_path not in self.subscriptions[event_type]:
                logger.warning(
                    f"Handler not found for unregistration: {script_path} "
                    f"for {event_type.value}"
                )
                return False

            # Find the handler to unsubscribe
            # Note: We need to find the handler by script path
            handler_to_remove = None
            for handler_key, handler in self.handlers.items():
                if handler.script_path == script_path:
                    handler_to_remove = handler
                    break

            if handler_to_remove:
                # Unsubscribe from EventBus
                self.event_bus.unsubscribe_lua(event_type, handler_to_remove)

            # Remove from tracking
            self.subscriptions[event_type].remove(script_path)
            self.script_events[script_path].discard(event_type)

            # If script has no more subscriptions, remove handler
            if not self.script_events[script_path]:
                del self.script_events[script_path]
                # Remove handler from handlers dict
                for key in list(self.handlers.keys()):
                    if self.handlers[key] == handler_to_remove:
                        del self.handlers[key]

            logger.info(
                f"Unregistered Lua event handler: {script_path} from {event_type.value}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error unregistering Lua event handler {script_path}: {e}",
                exc_info=True
            )
            return False

    def get_handlers(self, event_type: GameEventType) -> List[LuaEventHandler]:
        """
        Get all Lua handlers for event type.

        Args:
            event_type: Event type to query

        Returns:
            List of LuaEventHandler instances for this event type
        """
        handlers = []
        for script_path in self.subscriptions.get(event_type, []):
            # Find handlers for this script
            for handler in self.handlers.values():
                if handler.script_path == script_path:
                    handlers.append(handler)
        return handlers

    def load_from_directory(self, directory: str) -> int:
        """
        Auto-load all event handlers from directory.

        This scans directory for *.lua files and looks for annotation comments
        to auto-register handlers.

        Annotation format:
            -- @subscribe: entity_died, item_crafted
            -- @handler: on_entity_died

        Args:
            directory: Directory path to scan

        Returns:
            Number of handlers loaded
        """
        dir_path = Path(directory)

        if not dir_path.exists() or not dir_path.is_dir():
            logger.warning(f"Event handler directory not found: {directory}")
            return 0

        logger.info(f"Loading Lua event handlers from: {directory}")

        loaded_count = 0
        for script_file in dir_path.glob("*.lua"):
            # Skip template files
            if script_file.name.startswith("_"):
                logger.debug(f"Skipping template file: {script_file.name}")
                continue

            try:
                loaded_count += self._load_script_with_annotations(script_file)
            except Exception as e:
                logger.error(
                    f"Error loading event handler {script_file}: {e}",
                    exc_info=True
                )

        logger.info(f"Loaded {loaded_count} Lua event handler(s) from {directory}")
        return loaded_count

    def _load_script_with_annotations(self, script_path: Path) -> int:
        """
        Load script and register handlers based on annotations.

        Parses comments like:
            -- @subscribe: entity_died, item_crafted
            -- @handler: on_entity_died, on_item_crafted

        Args:
            script_path: Path to Lua script

        Returns:
            Number of handlers registered from this script
        """
        try:
            with open(script_path, 'r') as f:
                script_content = f.read()

            # Parse annotations
            annotations = self._parse_annotations(script_content)

            if not annotations.get('subscribe'):
                logger.debug(f"No @subscribe annotation in {script_path.name}")
                return 0

            # Get event types and handler functions
            event_types = annotations['subscribe']
            handler_functions = annotations.get('handler', [])

            # If no explicit handler functions, infer from event types
            if not handler_functions:
                handler_functions = [f"on_{event}" for event in event_types]

            # Register handlers
            registered_count = 0
            for i, event_name in enumerate(event_types):
                try:
                    # Convert event name to GameEventType
                    event_type = GameEventType(event_name)

                    # Get handler function (use same index or last one)
                    handler_idx = min(i, len(handler_functions) - 1)
                    handler_function = handler_functions[handler_idx]

                    # Register handler
                    if self.register(
                        event_type,
                        str(script_path),
                        handler_function
                    ):
                        registered_count += 1

                except ValueError:
                    logger.error(
                        f"Invalid event type '{event_name}' in {script_path.name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error registering handler from {script_path.name}: {e}"
                    )

            return registered_count

        except Exception as e:
            logger.error(f"Error loading script {script_path}: {e}", exc_info=True)
            return 0

    def _parse_annotations(self, script_content: str) -> Dict[str, List[str]]:
        """
        Parse annotation comments from Lua script.

        Looks for:
            -- @subscribe: entity_died, item_crafted
            -- @handler: on_entity_died

        Args:
            script_content: Lua script source code

        Returns:
            Dictionary with 'subscribe' and 'handler' keys containing lists
        """
        annotations = {
            'subscribe': [],
            'handler': [],
        }

        # Pattern: -- @key: value1, value2
        pattern = r'--\s*@(\w+):\s*(.+)'

        for match in re.finditer(pattern, script_content):
            key = match.group(1)
            values_str = match.group(2)

            if key in annotations:
                # Split by comma and strip whitespace
                values = [v.strip() for v in values_str.split(',')]
                annotations[key].extend(values)

        return annotations

    def get_subscription_count(self, event_type: GameEventType) -> int:
        """
        Get number of Lua handlers subscribed to event type.

        Args:
            event_type: Event type to check

        Returns:
            Number of Lua handlers subscribed
        """
        return len(self.subscriptions.get(event_type, []))

    def get_all_subscriptions(self) -> Dict[str, List[str]]:
        """
        Get all subscriptions (for debugging).

        Returns:
            Dictionary mapping event type names to list of script paths
        """
        return {
            event_type.value: list(scripts)
            for event_type, scripts in self.subscriptions.items()
        }

    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        # Unsubscribe all handlers from EventBus
        for event_type, script_paths in self.subscriptions.items():
            for handler in self.handlers.values():
                if handler.script_path in script_paths:
                    try:
                        self.event_bus.unsubscribe_lua(event_type, handler)
                    except Exception as e:
                        logger.debug(f"Error unsubscribing handler: {e}")

        self.handlers.clear()
        self.subscriptions.clear()
        self.script_events.clear()
        logger.debug("Cleared all Lua event registrations")
