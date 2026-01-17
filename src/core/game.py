"""
Main game controller - orchestrates systems, state, and game loop.

Uses clean architecture:
- GameState holds all mutable state
- GameContext provides safe API
- Systems process game logic
- Actions drive all state changes
"""

import logging
from typing import Optional, Union, Tuple

from .game_state import GameState
from .base.game_context import GameContext
from .rng import GameRNG
from .base.entity import EntityType
from .entities import Player, OreVein
from .entity_loader import EntityLoader
from .world import Map
from .systems.ai_system import AISystem
from .actions.action_factory import ActionFactory
from .config import ConfigLoader
from .spawning import EntitySpawner
from .turn_processor import TurnProcessor
from .floor_manager import FloorManager
from .save_load import SaveSystem, SaveLoadError
from .events import EventBus, GameEventType
from .events.lua_event_registry import LuaEventRegistry
from .scripting.lua_runtime import LuaRuntime
from .scripting.game_context_api import GameContextAPI
from .telemetry import StatsTracker, GameTelemetry, PerformanceTelemetry
from pathlib import Path

logger = logging.getLogger(__name__)


class Game:
    """
    Main game controller.

    Responsibilities:
    - Initialize game state
    - Manage systems
    - Provide action execution interface
    - Handle turn processing
    """

    def __init__(self):
        self.state: Optional[GameState] = None
        self.context: Optional[GameContext] = None
        self.running = False

        # Load configuration
        self.config = ConfigLoader.load()

        # Load entity definitions (Phase 3: data-driven entities)
        self.entity_loader = EntityLoader()

        # Initialize subsystems (created after state is set up)
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

        # Lua event system (Phase 3)
        self.lua_runtime = LuaRuntime()
        self.lua_event_registry: Optional[LuaEventRegistry] = None
        self.game_context_api: Optional[GameContextAPI] = None

        logger.debug("Game initialized with configuration, entity loader, and event system")

    def _create_player(
        self,
        player_pos: Tuple[int, int],
        player_name: Optional[str],
        character_class: Optional['CharacterClass']
    ) -> Player:
        """Create player entity based on class or defaults."""
        if character_class:
            from .character_class import create_player_from_class
            player = create_player_from_class(
                character_class,
                x=player_pos[0],
                y=player_pos[1],
                name=player_name or "Anonymous"
            )
            logger.info(f"Created {character_class.value} player: {player_name}")
        else:
            # Get starting stats from config
            starting_stats = self.config.game_constants['player']['starting_stats']
            starting_hp = starting_stats['hp']
            starting_attack = starting_stats['attack']
            starting_defense = starting_stats['defense']

            player = Player(
                x=player_pos[0],
                y=player_pos[1],
                hp=starting_hp,
                max_hp=starting_hp,
                attack=starting_attack,
                defense=starting_defense,
            )
            if player_name:
                player.stats['name'] = player_name
                logger.info(f"Created default player: {player_name}")
        return player

    def _initialize_game_state(
        self,
        player: Player,
        dungeon_map: Map,
        player_name: Optional[str],
        is_legacy_run: bool,
        seed
    ) -> None:
        """Initialize GameState and GameContext."""
        self.state = GameState(
            player=player,
            dungeon_map=dungeon_map,
            seed=seed,
        )
        self.state.player_name = player_name or "Anonymous"
        self.state.run_type = "legacy" if is_legacy_run else "pure"
        self.context = GameContext(self.state)

    def _add_legacy_ore(self, player: Player, withdrawn_ore: 'LegacyOre') -> None:
        """Add legacy ore from vault to player inventory."""
        legacy_ore_entity = OreVein(
            x=player.x,
            y=player.y,
            ore_type=withdrawn_ore.ore_type,
            hardness=withdrawn_ore.hardness,
            conductivity=withdrawn_ore.conductivity,
            malleability=withdrawn_ore.malleability,
            purity=withdrawn_ore.purity,
            density=withdrawn_ore.density,
        )
        legacy_ore_entity.stats['mining_turns_remaining'] = 0
        player.inventory.append(legacy_ore_entity)
        logger.info(
            f"Added legacy ore to inventory: {withdrawn_ore.ore_type} "
            f"(Purity: {withdrawn_ore.purity})"
        )

    def _spawn_entities(self, floor: int, dungeon_map: Map) -> dict:
        """Spawn all initial entities for the floor."""
        monsters = self.spawner.spawn_monsters_for_floor(floor, dungeon_map)
        ore_veins = self.spawner.spawn_ore_veins_for_floor(floor, dungeon_map)
        forges = self.spawner.spawn_forges_for_floor(floor, dungeon_map)

        # Spawn special room entities
        special_entities = self.spawner.spawn_special_room_entities(floor, dungeon_map)
        monsters.extend(special_entities['monsters'])
        ore_veins.extend(special_entities['ores'])

        return {'monsters': monsters, 'ore_veins': ore_veins, 'forges': forges}

    def _display_welcome_messages(self, forges: list, withdrawn_ore: Optional['LegacyOre']) -> None:
        """Display initial game messages."""
        self.state.add_message("Welcome to Veinborn! Mine ore and craft weapons.")
        self.state.add_message("Use arrow keys or HJKL to move. Bump into monsters to attack.")

        if forges:
            self.state.add_message(f"Find the {forges[0].name} to craft equipment!")

        if withdrawn_ore:
            self.state.add_message(
                f"You start with {withdrawn_ore.get_quality_tier()} "
                f"{withdrawn_ore.ore_type} ore from the Legacy Vault!"
            )
            self.state.add_message("This is a Legacy run. Good luck!")

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
        dungeon_map = Map(width=map_width, height=map_height)
        player_pos = dungeon_map.find_starting_position()

        # Create player
        player = self._create_player(player_pos, player_name, character_class)

        # Initialize game state and context
        self._initialize_game_state(
            player, dungeon_map, player_name, is_legacy_run, rng.original_seed
        )

        # Add player to game context (needed for monster AI to target player)
        self.context.add_entity(player)

        # Add legacy ore if provided
        if withdrawn_ore:
            self._add_legacy_ore(player, withdrawn_ore)

        # Initialize subsystems
        self._initialize_subsystems()

        # Register AI system
        ai_system = AISystem(self.context)
        self.context.register_system('ai', ai_system)

        # Spawn entities
        entities = self._spawn_entities(self.state.current_floor, dungeon_map)

        # Add entities to game
        for monster in entities['monsters']:
            self.context.add_entity(monster)
        for ore_vein in entities['ore_veins']:
            self.context.add_entity(ore_vein)
        for forge in entities['forges']:
            self.context.add_entity(forge)

        # Display welcome messages
        self._display_welcome_messages(entities['forges'], withdrawn_ore)

        self.running = True
        logger.info(
            f"Game started: Player at {player_pos}, "
            f"{len(self.context.get_entities_by_type(EntityType.MONSTER))} monsters, "
            f"{len(self.context.get_entities_by_type(EntityType.ORE_VEIN))} ore veins"
        )

    # Spawning methods removed - delegated to EntitySpawner

    def _process_action_outcome(self, outcome, action_type: str):
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
            # Store current RNG state in game state for serialization
            rng = GameRNG.get_instance()
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

        # Initialize core subsystems
        self.spawner = EntitySpawner(self.config, self.entity_loader)

        # Get HP regen config
        hp_regen_config = self.config.game_constants['player']['health_regeneration']
        hp_regen_interval = hp_regen_config['interval_turns']
        hp_regen_amount = hp_regen_config['amount']

        self.turn_processor = TurnProcessor(self.context, hp_regen_interval, hp_regen_amount)
        self.floor_manager = FloorManager(self.context, self.spawner)
        self.action_factory = ActionFactory(self.context)

        # Initialize Lua event system (Phase 3)
        self._initialize_lua_event_system()

        # Subscribe telemetry systems to events (Phase 2-ready pattern)
        self._subscribe_event_handlers()

        # Load Lua event handlers from scripts/events/ (Phase 3)
        self._load_lua_event_handlers()

        logger.debug("Subsystems initialized successfully")

    def _subscribe_event_handlers(self) -> None:
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

    def _initialize_lua_event_system(self) -> None:
        """
        Initialize Lua event system (Phase 3).

        This creates the LuaEventRegistry and GameContextAPI with event support.
        """
        if not self.state or not self.context:
            logger.warning("Cannot initialize Lua event system without state and context")
            return

        try:
            # Create Lua event registry
            self.lua_event_registry = LuaEventRegistry(self.lua_runtime, self.event_bus)

            # Create GameContextAPI with event support
            self.game_context_api = GameContextAPI(
                self.context,
                self.lua_runtime.lua,
                event_bus=self.event_bus,
                lua_event_registry=self.lua_event_registry
            )

            logger.info("Lua event system initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Lua event system: {e}", exc_info=True)

    def _load_lua_event_handlers(self) -> None:
        """
        Load Lua event handlers from scripts/events/ directory (Phase 3).

        This auto-loads all Lua event handlers with @subscribe annotations.
        Handlers are loaded automatically on game start.
        """
        if self.lua_event_registry is None:
            logger.debug("Lua event registry not initialized, skipping handler loading")
            return

        try:
            # Determine scripts directory
            scripts_dir = Path(__file__).parent.parent.parent / "scripts" / "events"

            if not scripts_dir.exists():
                logger.info(f"Lua event handler directory not found: {scripts_dir}")
                return

            # Load handlers from directory
            count = self.lua_event_registry.load_from_directory(str(scripts_dir))

            if count > 0:
                logger.info(f"Loaded {count} Lua event handler(s)")
            else:
                logger.debug("No Lua event handlers found")

        except Exception as e:
            logger.error(f"Failed to load Lua event handlers: {e}", exc_info=True)

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
