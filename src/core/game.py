"""
Main game controller - orchestrates systems, state, and game loop.

Uses clean architecture:
- GameState holds all mutable state
- GameContext provides safe API
- Systems process game logic
- Actions drive all state changes
"""

import logging
from typing import Optional, Dict, Union

from .game_state import GameState
from .base.game_context import GameContext
from .rng import GameRNG
from .base.entity import EntityType
from .entities import Player, Monster, OreVein
from .entity_loader import EntityLoader
from .world import Map
from .systems.ai_system import AISystem
from .actions import MoveAction, AttackAction, SurveyAction, MineAction, DescendAction
from .actions.action_factory import ActionFactory
from .config import ConfigLoader
from .constants import (
    PLAYER_STARTING_HP,
    PLAYER_STARTING_ATTACK,
    PLAYER_STARTING_DEFENSE,
    DEFAULT_MAP_WIDTH,
    DEFAULT_MAP_HEIGHT,
)
from .spawning import EntitySpawner
from .turn_processor import TurnProcessor
from .floor_manager import FloorManager
from .save_load import SaveSystem, SaveLoadError

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

        logger.debug("Game initialized with configuration and entity loader")

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
            seed: Optional seed for reproducible gameplay.
                  Can be int, string, or None (random).
                  Same seed = same game.
            player_name: Player name (for high scores and display)
            character_class: CharacterClass enum (determines starting stats)
            withdrawn_ore: LegacyOre from vault to start with (optional)
            is_legacy_run: Whether this is a legacy run (used vault ore)
        """
        # Initialize RNG with seed (Phase 4: reproducibility)
        rng = GameRNG.initialize(seed)
        logger.info(f"Starting new game with {rng.get_seed_display()}")

        # Create fresh map
        dungeon_map = Map(width=DEFAULT_MAP_WIDTH, height=DEFAULT_MAP_HEIGHT)

        # Get player starting position
        player_pos = dungeon_map.find_starting_position()

        # Create player based on character class (Phase 5: character classes)
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
            # Default player (no class)
            player = Player(
                x=player_pos[0],
                y=player_pos[1],
                hp=PLAYER_STARTING_HP,
                max_hp=PLAYER_STARTING_HP,
                attack=PLAYER_STARTING_ATTACK,
                defense=PLAYER_STARTING_DEFENSE,
            )
            if player_name:
                player.stats['name'] = player_name
                logger.info(f"Created default player: {player_name}")

        # Create game state
        self.state = GameState(
            player=player,
            dungeon_map=dungeon_map,
            seed=rng.original_seed,  # Store for display/save
        )

        # Store player name in game state for high scores (Phase 5)
        self.state.player_name = player_name or "Anonymous"

        # Set run type based on whether legacy ore was used
        self.state.run_type = "legacy" if is_legacy_run else "pure"

        # Create game context (safe API for systems)
        self.context = GameContext(self.state)

        # Add withdrawn ore to player inventory (if provided)
        if withdrawn_ore:
            # Create an OreVein entity from the LegacyOre
            legacy_ore_entity = OreVein(
                x=player.x,  # Same position as player (in inventory)
                y=player.y,
                ore_type=withdrawn_ore.ore_type,
                hardness=withdrawn_ore.hardness,
                conductivity=withdrawn_ore.conductivity,
                malleability=withdrawn_ore.malleability,
                purity=withdrawn_ore.purity,
                density=withdrawn_ore.density,
            )
            # Mark as fully mined so it's in inventory
            legacy_ore_entity.stats['mining_turns_remaining'] = 0
            player.inventory.append(legacy_ore_entity)
            logger.info(f"Added legacy ore to inventory: {withdrawn_ore.ore_type} (Purity: {withdrawn_ore.purity})")

        # Initialize subsystems
        self._initialize_subsystems()

        # Register systems
        ai_system = AISystem(self.context)
        self.context.register_system('ai', ai_system)

        # Spawn initial entities (delegated to spawner)
        floor = self.state.current_floor
        monsters = self.spawner.spawn_monsters_for_floor(floor, dungeon_map)
        ore_veins = self.spawner.spawn_ore_veins_for_floor(floor, dungeon_map)
        forges = self.spawner.spawn_forges_for_floor(floor, dungeon_map)

        # Spawn special room entities
        special_entities = self.spawner.spawn_special_room_entities(floor, dungeon_map)
        monsters.extend(special_entities['monsters'])
        ore_veins.extend(special_entities['ores'])

        # Add entities to game
        for monster in monsters:
            self.context.add_entity(monster)
        for ore_vein in ore_veins:
            self.context.add_entity(ore_vein)
        for forge in forges:
            self.context.add_entity(forge)

        # Initial message
        self.state.add_message("Welcome to Brogue! Mine ore and craft weapons.")
        self.state.add_message("Use arrow keys or HJKL to move. Bump into monsters to attack.")
        if forges:
            self.state.add_message(f"Find the {forges[0].name} to craft equipment!")

        # Add legacy ore message if applicable
        if withdrawn_ore:
            self.state.add_message(f"You start with {withdrawn_ore.get_quality_tier()} {withdrawn_ore.ore_type} ore from the Legacy Vault!")
            self.state.add_message("This is a Legacy run. Good luck!")

        self.running = True
        logger.info(
            f"Game started: Player at {player_pos}, "
            f"{len(self.context.get_entities_by_type(EntityType.MONSTER))} monsters, "
            f"{len(self.context.get_entities_by_type(EntityType.ORE_VEIN))} ore veins"
        )

    # Spawning methods removed - delegated to EntitySpawner

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
            # Factory already logged warning and added message
            return False

        # Execute action
        logger.debug(
            f"Executing action: {action_type}",
            extra={
                'action_class': action.__class__.__name__,
                'turn': self.state.turn_count,
            }
        )
        outcome = action.execute(self.context)

        if not outcome.is_success:
            logger.info(
                f"Action failed: {action_type}",
                extra={
                    'action_class': action.__class__.__name__,
                    'failure_message': outcome.messages[0] if outcome.messages else 'No message',
                }
            )

        # Check for floor transition event
        for event in outcome.events:
            if event.get('type') == 'descend_floor':
                self.descend_floor()

        # Add messages
        for msg in outcome.messages:
            self.state.add_message(msg)

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
        self.turn_processor = TurnProcessor(self.context)
        self.floor_manager = FloorManager(self.context, self.spawner)
        self.action_factory = ActionFactory(self.context)

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
