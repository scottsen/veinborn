"""
Main game controller - orchestrates systems, state, and game loop.

Uses clean architecture:
- GameState holds all mutable state
- GameContext provides safe API
- Systems process game logic
- Actions drive all state changes
"""

import logging
from typing import Optional, Union

from .game_state import GameState
from .base.game_context import GameContext
from .rng import GameRNG
from .base.entity import EntityType
from .entity_loader import EntityLoader
from .world import Map
from .systems.ai_system import AISystem
from .actions.action_factory import ActionFactory
from .config import ConfigLoader
from .spawning import EntitySpawner
from .turn_processor import TurnProcessor
from .floor_manager import FloorManager
from .save_load import SaveSystem, SaveLoadError
from .events import EventBus
from .events.lua_event_registry import LuaEventRegistry
from .scripting.lua_runtime import LuaRuntime
from .scripting.game_context_api import GameContextAPI
from .telemetry import StatsTracker, GameTelemetry, PerformanceTelemetry
from .game_bootstrap import GameBootstrapper
from .game_lua_integration import GameLuaIntegration

logger = logging.getLogger(__name__)


class Game:
    """
    Main game controller.

    Responsibilities:
    - Own game/context/subsystem state
    - Coordinate bootstrap (GameBootstrapper) and event/Lua wiring (GameLuaIntegration)
    - Provide the action-execution/turn-orchestration interface
    - Own persistence (save/load)
    """

    def __init__(self):
        self.state: Optional[GameState] = None
        self.context: Optional[GameContext] = None
        self.running = False

        # Load configuration
        self.config = ConfigLoader.load()

        # Load entity definitions (Phase 3: data-driven entities)
        self.entity_loader = EntityLoader()

        # Subsystems (created by GameBootstrapper after state is set up)
        self.spawner: Optional[EntitySpawner] = None
        self.turn_processor: Optional[TurnProcessor] = None
        self.floor_manager: Optional[FloorManager] = None
        self.action_factory: Optional[ActionFactory] = None

        # Save/load system
        self.save_system = SaveSystem()

        # Event system and telemetry (Phase 2-ready, Lua-ready)
        self.event_bus = EventBus()
        self.stats_tracker = StatsTracker()
        self.game_telemetry = GameTelemetry()
        self.perf_telemetry = PerformanceTelemetry()

        # Lua event system (Phase 3, wired by GameLuaIntegration)
        self.lua_runtime = LuaRuntime()
        self.lua_event_registry: Optional[LuaEventRegistry] = None
        self.game_context_api: Optional[GameContextAPI] = None

        self.bootstrapper = GameBootstrapper(self.config, self.entity_loader)
        self.lua_integration = GameLuaIntegration(
            self.event_bus, self.stats_tracker, self.lua_runtime
        )

        logger.debug("Game initialized with configuration, entity loader, and event system")

    def start_new_game(
        self,
        seed: Optional[Union[int, str]] = None,
        player_name: Optional[str] = None,
        character_class: Optional['CharacterClass'] = None,
        withdrawn_ore: Optional['LegacyOre'] = None,
        is_legacy_run: bool = False
    ) -> None:
        """
        Initialize a new game.

        Args:
            seed: Optional seed for reproducible gameplay
            player_name: Player name (for high scores and display)
            character_class: CharacterClass enum (determines starting stats)
            withdrawn_ore: LegacyOre from vault to start with (optional)
            is_legacy_run: Whether this is a legacy run (used vault ore)
        """
        # Initialize RNG with seed
        rng = GameRNG.initialize(seed)
        logger.info(f"Starting new game with {rng.get_seed_display()}")

        # Create map and find player position
        map_width = self.config.game_constants['map']['default_width']
        map_height = self.config.game_constants['map']['default_height']
        # VB-18: pass this game's own RNG instance explicitly rather than
        # letting Map() default to GameRNG.get_instance() -- correct today
        # since single-player has one game per process, but explicit here
        # so it doesn't depend on that timing coincidence.
        dungeon_map = Map(width=map_width, height=map_height, rng=rng)
        player_pos = dungeon_map.find_starting_position()

        # Create player
        player = self.bootstrapper.create_player(player_pos, player_name, character_class)

        # Initialize game state and context
        self.state, self.context = self.bootstrapper.initialize_game_state(
            player, dungeon_map, player_name, is_legacy_run, rng.original_seed
        )

        # Add player to game context (needed for monster AI to target player)
        self.context.add_entity(player)

        # Add legacy ore if provided
        if withdrawn_ore:
            self.bootstrapper.add_legacy_ore(player, withdrawn_ore)

        # Initialize subsystems
        self._initialize_subsystems()

        # Register AI system
        ai_system = AISystem(self.context)
        self.context.register_system('ai', ai_system)

        # Spawn entities
        entities = self.bootstrapper.spawn_entities(
            self.spawner, self.state.current_floor, dungeon_map
        )

        # Add entities to game
        for monster in entities['monsters']:
            self.context.add_entity(monster)
        for ore_vein in entities['ore_veins']:
            self.context.add_entity(ore_vein)
        for forge in entities['forges']:
            self.context.add_entity(forge)

        # Display welcome messages
        self.bootstrapper.display_welcome_messages(self.state, entities['forges'], withdrawn_ore)

        self.running = True
        logger.info(
            f"Game started: Player at {player_pos}, "
            f"{len(self.context.get_entities_by_type(EntityType.MONSTER))} monsters, "
            f"{len(self.context.get_entities_by_type(EntityType.ORE_VEIN))} ore veins"
        )

    def _process_action_outcome(self, outcome, action_type: str) -> None:
        """
        Process the outcome of an action (events, messages, floor transitions).

        Args:
            outcome: The ActionOutcome from action execution
            action_type: The type of action for logging
        """
        # Log failures
        if not outcome.is_success:
            logger.info(
                f"Action failed: {action_type}",
                extra={
                    'action_class': outcome.__class__.__name__,
                    'failure_message': outcome.messages[0] if outcome.messages else 'No message',
                }
            )

        # Publish events to EventBus
        if outcome.events:
            self.event_bus.publish_all(outcome.events)
            logger.debug(f"Published {len(outcome.events)} events to EventBus")

        # Check for floor transition event (special handling)
        for event in outcome.events:
            if event.get('type') == 'descend_floor':
                self.descend_floor()

        # Add messages to game state
        for msg in outcome.messages:
            self.state.add_message(msg)

    def handle_player_action(
        self,
        action_type: str,
        **kwargs
    ) -> bool:
        """
        Handle player action and process turn.

        Refactored to use ActionFactory pattern (GoF).
        Complexity reduced from 19 → ~8

        Args:
            action_type: Type of action ('move', 'survey', 'mine', etc.)
            **kwargs: Action-specific parameters

        Returns:
            True if action consumed a turn
        """
        if self.state.game_over:
            return False

        # Special case: wait action (consumes turn but no action object)
        if action_type == 'wait':
            logger.debug("Player waiting (rest to heal)")
            self._process_turn()
            return True

        # Create action via factory
        action = self.action_factory.create(action_type, **kwargs)
        if not action:
            return False  # Factory already logged warning

        # Execute action
        logger.debug(
            f"Executing action: {action_type}",
            extra={
                'action_class': action.__class__.__name__,
                'turn': self.state.turn_count,
            }
        )
        outcome = action.execute(self.context)

        # Process outcome (events, messages, floor transitions)
        self._process_action_outcome(outcome, action_type)

        # Process turn if action consumed time
        if outcome.took_turn:
            self._process_turn()
            return True

        return False

    def _process_turn(self) -> None:
        """Process one game turn (delegated to TurnProcessor)."""
        self.turn_processor.process_turn()

    def restart_game(self) -> None:
        """Restart the game."""
        logger.info("Restarting game")
        self.start_new_game()

    def descend_floor(self) -> None:
        """Descend to next floor (delegated to FloorManager)."""
        self.floor_manager.descend_floor()

    def save_game(self, slot_name: str = "quicksave") -> bool:
        """
        Save current game state.

        Args:
            slot_name: Save slot name (default: "quicksave")

        Returns:
            True if save successful
        """
        if not self.state:
            logger.warning("Cannot save: no active game")
            return False

        try:
            # Store current RNG state in game state for serialization.
            # VB-18: use this game's own RNG instance (self.state.rng),
            # not the process-global singleton.
            rng = self.state.rng or GameRNG.get_instance()
            if rng:
                self.state.rng_state = rng.getstate()

            save_path = self.save_system.save_game(self.state, slot_name)
            self.state.add_message(f"Game saved: {slot_name}")
            logger.info(f"Game saved successfully: {save_path}")
            return True

        except SaveLoadError as e:
            self.state.add_message(f"Save failed: {e}")
            logger.error(f"Save failed: {e}")
            return False

    def _initialize_subsystems(self) -> None:
        """
        Initialize game subsystems (called after state/context are set up).

        This method is used by both:
        - start_new_game() - after creating new state
        - load_game() - after loading saved state

        Ensures subsystems are properly initialized regardless of how game starts.
        """
        if not self.state or not self.context:
            raise ValueError("Cannot initialize subsystems without state and context")

        # Initialize core subsystems (spawner, turn processor, floor manager, action factory)
        self.spawner, self.turn_processor, self.floor_manager, self.action_factory = (
            self.bootstrapper.initialize_subsystems(self.context)
        )

        # Initialize Lua event system (Phase 3)
        self.lua_event_registry, self.game_context_api = (
            self.lua_integration.initialize_lua_event_system(self.context)
        )

        # Subscribe telemetry systems to events (Phase 2-ready pattern)
        self.lua_integration.subscribe_event_handlers()

        # Load Lua event handlers from scripts/events/ (Phase 3)
        self.lua_integration.load_event_handlers(self.lua_event_registry)

        logger.debug("Subsystems initialized successfully")

    def load_game(self, slot_name: str = "quicksave") -> bool:
        """
        Load game state from save.

        Args:
            slot_name: Save slot name

        Returns:
            True if load successful
        """
        try:
            # Load state
            self.state = self.save_system.load_game(slot_name)

            # Create game context for loaded state
            self.context = GameContext(self.state)

            # Add player to game context (needed for monster AI to target player)
            self.context.add_entity(self.state.player)

            # Reinitialize subsystems with loaded state
            self._initialize_subsystems()

            # Re-register AI system
            ai_system = AISystem(self.context)
            self.context.register_system('ai', ai_system)

            self.running = True
            logger.info(f"Game loaded successfully: {slot_name}")
            self.state.add_message(f"Game loaded: {slot_name}")
            return True

        except SaveLoadError as e:
            logger.error(f"Load failed: {e}")
            if self.state:
                self.state.add_message(f"Load failed: {e}")
            return False

    def list_saves(self):
        """List available save files."""
        return self.save_system.list_saves()

    def delete_save(self, slot_name: str) -> bool:
        """Delete a save file."""
        return self.save_system.delete_save(slot_name)
