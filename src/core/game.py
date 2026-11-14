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
from .action_pipeline import process_action_outcome
from .turn_processor import TurnProcessor
from .run_end import SinglePlayerRunRecorder
from .floor_manager import FloorManager
from .save_load import SaveSystem, SaveLoadError
from .events import EventBus, create_game_started_event, create_floor_changed_event
from .extensions import install_event_handlers, uninstall_event_handlers
from .telemetry import StatsTracker, GameTelemetry, PerformanceTelemetry
from .game_bootstrap import GameBootstrapper

logger = logging.getLogger(__name__)


class Game:
    """
    Main game controller.

    Responsibilities:
    - Own game/context/subsystem state
    - Coordinate bootstrap (GameBootstrapper) and event wiring
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
        self.run_recorder: Optional[SinglePlayerRunRecorder] = None
        self.floor_manager: Optional[FloorManager] = None
        self.action_factory: Optional[ActionFactory] = None

        # Save/load system
        self.save_system = SaveSystem()

        # Event system and telemetry
        self.event_bus = EventBus()
        self.stats_tracker = StatsTracker()
        self.game_telemetry = GameTelemetry()
        self.perf_telemetry = PerformanceTelemetry()

        self.event_handlers = []  # content event handlers, one instance each, per game
        self.ai_system: Optional[AISystem] = None

        self.bootstrapper = GameBootstrapper(self.config, self.entity_loader)
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
        self._register_ai_system()

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
        self.event_bus.publish_dict(
            create_game_started_event(self.state.player.entity_id, self.state.current_floor)
        )
        logger.info(
            f"Game started: Player at {player_pos}, "
            f"{len(self.context.get_entities_by_type(EntityType.MONSTER))} monsters, "
            f"{len(self.context.get_entities_by_type(EntityType.ORE_VEIN))} ore veins"
        )

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
        took_turn = process_action_outcome(
            outcome,
            action_type,
            add_message=self.state.add_message,
            on_descend_floor=self.descend_floor,
            event_bus=self.event_bus,
        )

        # Process turn if action consumed time
        if took_turn:
            self._process_turn()
            return True

        return False

    def quick_use(self) -> bool:
        """Use the healing item that best covers missing HP (potion or food).

        One intent for every frontend; with nothing to use, a message says why
        and no turn passes. Returns True if a turn was consumed.
        """
        from .actions.use_item_action import best_healing_item
        player = self.state.player
        item = best_healing_item(player)
        if item is not None:
            return self.handle_player_action('use', item_id=item.entity_id)
        if player.hp >= player.max_hp:
            self.state.add_message("You are already at full health.")
        else:
            self.state.add_message("You have nothing to eat or drink.")
        return False

    def quick_drop(self) -> bool:
        """Drop the item least worth carrying; a message says so when there is none."""
        from .actions.drop_action import least_useful_item
        item = least_useful_item(self.state.player)
        if item is None:
            self.state.add_message("You have nothing to drop.")
            return False
        return self.handle_player_action('drop', item_id=item.entity_id)

    def _process_turn(self) -> None:
        """Process one game turn (delegated to TurnProcessor, which announces it)."""
        self.turn_processor.process_turn()

    def restart_game(self) -> None:
        """Restart the game."""
        logger.info("Restarting game")
        self.start_new_game()

    def descend_floor(self) -> None:
        """Descend to next floor (delegated to FloorManager), then announce it."""
        from_floor = self.state.current_floor
        self.floor_manager.descend_floor()
        if self.state.current_floor != from_floor:
            self.event_bus.publish_dict(create_floor_changed_event(
                from_floor, self.state.current_floor,
                self.state.player.entity_id, self.state.turn_count,
            ))

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
            self.bootstrapper.initialize_subsystems(self.context, self.event_bus)
        )

        # Single-player keeps its own high score and Legacy Vault on run_ended
        if self.run_recorder is not None:
            self.run_recorder.uninstall(self.event_bus)
        self.run_recorder = SinglePlayerRunRecorder(self.state).install(self.event_bus)

        # Subscribe telemetry to the event bus (EventBus de-duplicates re-subscription)
        self.stats_tracker.is_player = self._is_player_id
        self.stats_tracker.subscribe_to(self.event_bus)

        # Content event handlers (core/content/events/): fresh instances per
        # (re)initialisation, so a loaded game never double-subscribes old ones
        uninstall_event_handlers(self.event_handlers, self.event_bus)
        self.event_handlers = install_event_handlers(self.context, self.event_bus)

        logger.debug("Subsystems initialized successfully")

    def _is_player_id(self, entity_id) -> bool:
        """True if entity_id is a player in the current game (telemetry attribution)."""
        entity = self.context.get_entity(entity_id) if self.context and entity_id else None
        return entity is not None and entity.entity_type == EntityType.PLAYER

    def _register_ai_system(self) -> None:
        """(Re)create the AI system for the current context, listening to this game's events.

        The previous one (an earlier game or a loaded save) is detached first, so
        stale monsters never receive provocation events.
        """
        if self.ai_system is not None:
            self.ai_system.detach()
        self.ai_system = AISystem(
            self.context, entity_loader=self.entity_loader, event_bus=self.event_bus
        )
        self.context.register_system('ai', self.ai_system)

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
            self._register_ai_system()

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
