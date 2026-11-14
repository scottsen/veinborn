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
from .engine import Engine
from .config import ConfigLoader
from .run_end import SinglePlayerRunRecorder
from .save_load import SaveSystem, SaveLoadError
from .events import EventBus, create_game_started_event
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

        # The rules loop (created once state/context exist); this class is the
        # single-player host around it
        self.engine: Optional[Engine] = None
        self.run_recorder: Optional[SinglePlayerRunRecorder] = None

        # Save/load system
        self.save_system = SaveSystem()

        # Event system and telemetry
        self.event_bus = EventBus()
        self.stats_tracker = StatsTracker()
        self.game_telemetry = GameTelemetry()
        self.perf_telemetry = PerformanceTelemetry()

        self.bootstrapper = GameBootstrapper(self.config, self.entity_loader)
        logger.debug("Game initialized with configuration, entity loader, and event system")

    # The engine's parts, under the names the UI, bots and tests have always used
    spawner = property(lambda self: self.engine.spawner if self.engine else None)
    turn_processor = property(lambda self: self.engine.turn_processor if self.engine else None)
    floor_manager = property(lambda self: self.engine.floor_manager if self.engine else None)
    action_factory = property(lambda self: self.engine.action_factory if self.engine else None)
    ai_system = property(lambda self: self.engine.ai_system if self.engine else None)
    event_handlers = property(lambda self: self.engine.event_handlers if self.engine else [])

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

        # Initialize the engine (turn processor, floors, AI, content handlers)
        self._initialize_subsystems()

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

        # Build the action (the factory resolves targets and logs why it cannot)
        action = self.engine.make_action(action_type, **kwargs)
        if not action:
            return False

        logger.debug(
            f"Executing action: {action_type}",
            extra={
                'action_class': action.__class__.__name__,
                'turn': self.state.turn_count,
            }
        )
        result = self.engine.execute(action, action_type)

        # A party of one: the world moves after every turn-consuming action
        if result.took_turn:
            self._process_turn()
            return True

        return False

    def quick_use(self) -> bool:
        """Use the healing item that best covers missing HP (potion or food).

        The `use` intent with no item: the factory picks the item, or says why
        there is none (no turn passes). Returns True if a turn was consumed.
        """
        return self.handle_player_action('use')

    def quick_drop(self) -> bool:
        """Drop the item least worth carrying (the `drop` intent with no item)."""
        return self.handle_player_action('drop')

    def _process_turn(self) -> None:
        """Process one game turn (delegated to TurnProcessor, which announces it)."""
        self.engine.tick()

    def restart_game(self) -> None:
        """Restart the game."""
        logger.info("Restarting game")
        self.start_new_game()

    def descend_floor(self) -> None:
        """Descend to the next floor (the engine moves the party and announces it)."""
        self.engine.descend_floor()

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

        # (Re)build the engine; a loaded save replaces the old one, so detach it first
        if self.engine is not None:
            self.engine.close()
        self.engine = Engine(
            self.context, self.config, self.event_bus,
            entity_loader=self.entity_loader, ai_entity_loader=self.entity_loader,
        )

        # Single-player keeps its own high score and Legacy Vault on run_ended
        if self.run_recorder is not None:
            self.run_recorder.uninstall(self.event_bus)
        self.run_recorder = SinglePlayerRunRecorder(self.state).install(self.event_bus)

        # Subscribe telemetry to the event bus (EventBus de-duplicates re-subscription)
        self.stats_tracker.is_player = self._is_player_id
        self.stats_tracker.subscribe_to(self.event_bus)

        logger.debug("Subsystems initialized successfully")

    def _is_player_id(self, entity_id) -> bool:
        """True if entity_id is a player in the current game (telemetry attribution)."""
        entity = self.context.get_entity(entity_id) if self.context and entity_id else None
        return entity is not None and entity.entity_type == EntityType.PLAYER

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

            # Reinitialize the engine with the loaded state
            self._initialize_subsystems()

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
