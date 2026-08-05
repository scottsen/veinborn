"""
Game <-> Lua/event-system integration.

Wires the EventBus, StatsTracker, and Lua event registry together so Lua
scripts can subscribe to game events (Phase 3). Extracted from Game to
separate "how does Lua plug into events" from Game's turn-orchestration
role.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

from .base.game_context import GameContext
from .events import EventBus, GameEventType
from .events.lua_event_registry import LuaEventRegistry
from .scripting.game_context_api import GameContextAPI
from .scripting.lua_runtime import LuaRuntime
from .telemetry import StatsTracker

logger = logging.getLogger(__name__)


class GameLuaIntegration:
    """Wires EventBus subscriptions and the Lua event system for a Game instance."""

    def __init__(self, event_bus: EventBus, stats_tracker: StatsTracker, lua_runtime: LuaRuntime):
        self.event_bus = event_bus
        self.stats_tracker = stats_tracker
        self.lua_runtime = lua_runtime

    def subscribe_event_handlers(self) -> None:
        """
        Subscribe event handlers to EventBus.

        This demonstrates the event-ready pattern from EVENTS_ASYNC_OBSERVABILITY_GUIDE.md:
        - StatsTracker methods work as direct calls OR event subscribers
        - Adding new subscribers requires zero refactoring
        - Lua scripts can subscribe in Phase 3 using same pattern
        """
        # Subscribe StatsTracker to combat events
        self.event_bus.subscribe(
            GameEventType.ATTACK_RESOLVED,
            self.stats_tracker.on_attack_resolved,
            subscriber_name="StatsTracker.on_attack_resolved"
        )

        self.event_bus.subscribe(
            GameEventType.ENTITY_DIED,
            self.stats_tracker.on_entity_died,
            subscriber_name="StatsTracker.on_entity_died"
        )

        # Subscribe to mining events
        self.event_bus.subscribe(
            GameEventType.ORE_MINED,
            self.stats_tracker.on_ore_mined,
            subscriber_name="StatsTracker.on_ore_mined"
        )

        self.event_bus.subscribe(
            GameEventType.ORE_SURVEYED,
            self.stats_tracker.on_ore_surveyed,
            subscriber_name="StatsTracker.on_ore_surveyed"
        )

        # Subscribe to crafting events
        self.event_bus.subscribe(
            GameEventType.ITEM_CRAFTED,
            self.stats_tracker.on_item_crafted,
            subscriber_name="StatsTracker.on_item_crafted"
        )

        self.event_bus.subscribe(
            GameEventType.CRAFTING_FAILED,
            self.stats_tracker.on_crafting_failed,
            subscriber_name="StatsTracker.on_crafting_failed"
        )

        # Subscribe to floor events
        self.event_bus.subscribe(
            GameEventType.FLOOR_CHANGED,
            self.stats_tracker.on_floor_changed,
            subscriber_name="StatsTracker.on_floor_changed"
        )

        # Subscribe to turn events
        self.event_bus.subscribe(
            GameEventType.TURN_ENDED,
            self.stats_tracker.on_turn_ended,
            subscriber_name="StatsTracker.on_turn_ended"
        )

        logger.info(f"Event handlers subscribed: {len(self.event_bus.subscribers)} event types")

    def initialize_lua_event_system(
        self, context: Optional[GameContext]
    ) -> Tuple[Optional[LuaEventRegistry], Optional[GameContextAPI]]:
        """
        Initialize Lua event system (Phase 3).

        Creates the LuaEventRegistry and GameContextAPI with event support.

        Returns:
            Tuple of (lua_event_registry, game_context_api), both None on failure
        """
        if context is None:
            logger.warning("Cannot initialize Lua event system without a GameContext")
            return None, None

        try:
            lua_event_registry = LuaEventRegistry(self.lua_runtime, self.event_bus)

            game_context_api = GameContextAPI(
                context,
                self.lua_runtime.lua,
                event_bus=self.event_bus,
                lua_event_registry=lua_event_registry
            )

            logger.info("Lua event system initialized")
            return lua_event_registry, game_context_api

        except Exception as e:
            logger.error(f"Failed to initialize Lua event system: {e}", exc_info=True)
            return None, None

    def load_event_handlers(self, lua_event_registry: Optional[LuaEventRegistry]) -> None:
        """
        Load Lua event handlers from scripts/events/ directory (Phase 3).

        This auto-loads all Lua event handlers with @subscribe annotations.
        Handlers are loaded automatically on game start.
        """
        if lua_event_registry is None:
            logger.debug("Lua event registry not initialized, skipping handler loading")
            return

        try:
            # Determine scripts directory
            scripts_dir = Path(__file__).parent.parent.parent / "scripts" / "events"

            if not scripts_dir.exists():
                logger.info(f"Lua event handler directory not found: {scripts_dir}")
                return

            # Load handlers from directory
            count = lua_event_registry.load_from_directory(str(scripts_dir))

            if count > 0:
                logger.info(f"Loaded {count} Lua event handler(s)")
            else:
                logger.debug("No Lua event handlers found")

        except Exception as e:
            logger.error(f"Failed to load Lua event handlers: {e}", exc_info=True)
