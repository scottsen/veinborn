"""Multiplayer-aware GameState wrapper.

Extends the single-player GameState to support multiple players
while maintaining compatibility with existing single-player code.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

from core.game_state import GameState
from core.entities import Player
from core.rng import GameRNG
from core.world import Map
from core.config import ConfigLoader
from core.entity_loader import EntityLoader
from core.spawning import EntitySpawner
from core.turn_scheduler import RoundScheduler

logger = logging.getLogger(__name__)


@dataclass
class PlayerSlot:
    """Represents a player slot in a multiplayer game."""

    player_id: str  # Unique player ID from session
    player_name: str
    player_entity: Player
    entity_id: str  # The entity ID in the game state
    is_active: bool = True
    is_alive: bool = True


class MultiplayerGameState:
    """Wrapper around GameState for multiplayer support.

    This class:
    - Manages multiple players in a single game
    - Routes actions to the correct player entities
    - Maintains compatibility with single-player GameState
    - Handles player-specific views and state
    """

    def __init__(self, seed: Optional[int] = None, max_players: int = 4):
        """Initialize multiplayer game state.

        Args:
            seed: Random seed for dungeon generation
            max_players: Maximum number of players
        """
        self.max_players = max_players

        # Player management
        self.player_slots: Dict[str, PlayerSlot] = {}
        self.entity_to_player: Dict[str, str] = {}  # entity_id -> player_id

        # Core game state (initially single-player)
        # We'll initialize this when first player joins
        self.game_state: Optional[GameState] = None
        self.seed = seed

        # Entity spawning (monsters/ore veins/forges) - shared config/loader,
        # cheap to construct, so build it eagerly rather than lazily
        self.config = ConfigLoader.load()
        self.spawner = EntitySpawner(self.config, EntityLoader())

        # Multiplayer state
        self.is_multiplayer = True
        self.scheduler = RoundScheduler()

        # Spawn positions (calculated after dungeon generation)
        self.spawn_positions: List[tuple] = []

    def add_player(
        self, player_id: str, player_name: str, player_class: str = "warrior"
    ) -> bool:
        """Add a player to the game.

        Args:
            player_id: Unique player ID
            player_name: Display name
            player_class: Player class (warrior, mage, rogue, healer)

        Returns:
            True if player was added successfully
        """
        from core.character_class import CharacterClass, create_player_from_class
        if len(self.player_slots) >= self.max_players:
            logger.warning(f"Cannot add player {player_name}: game is full")
            return False

        if player_id in self.player_slots:
            logger.warning(f"Player {player_id} already in game")
            return False

        # If this is the first player, initialize GameState with dungeon generation
        if self.game_state is None:
            # VB-18: construct a dedicated GameRNG instance for THIS game
            # rather than calling GameRNG.initialize(), which reassigns the
            # process-global singleton. Two multiplayer games starting
            # concurrently on the same server used to share (and each
            # re-seed) that one singleton, corrupting each other's
            # in-flight combat/loot/dungeon-gen randomness. This instance
            # is threaded explicitly through dungeon_map.rng/state.rng
            # instead, so it's never affected by another game's setup.
            game_rng = GameRNG(self.seed)
            logger.info(f"Initialized dedicated RNG with seed: {self.seed}")

            # Create temporary player entity at (0, 0) to initialize GameState
            temp_player = Player(name=player_name, x=0, y=0)
            self.game_state = GameState(
                player=temp_player,
                dungeon_map=Map(rng=game_rng),
                seed=self.seed,
                player_name=player_name,
                rng=game_rng,
            )

            # Generate spawn positions for all potential players
            self.spawn_positions = self.game_state.dungeon_map.find_player_spawn_positions(
                self.max_players
            )
            logger.info(f"Generated {len(self.spawn_positions)} spawn positions for multiplayer game")

            # Populate floor 1 with monsters/ore veins/forges (VB-4: MP previously
            # never spawned any entities at all - AISystem ran every round over an
            # empty entities dict)
            self._spawn_floor_entities(self.game_state.current_floor)

        # Get spawn position for this player
        player_index = len(self.player_slots)
        if player_index < len(self.spawn_positions):
            spawn_x, spawn_y = self.spawn_positions[player_index]
        else:
            # Fallback to first room center if we run out of spawn positions
            spawn_x, spawn_y = self.game_state.dungeon_map.find_starting_position()
            logger.warning(f"No spawn position available for player {player_index}, using fallback")

        # Create player entity at spawn position with class
        try:
            class_type = CharacterClass.from_string(player_class)
            player_entity = create_player_from_class(
                class_type=class_type,
                x=spawn_x,
                y=spawn_y,
                name=player_name
            )
            logger.info(f"Created {player_class} player entity for {player_name}")
        except Exception as e:
            logger.error(f"Failed to create player with class {player_class}: {e}, using default")
            player_entity = Player(name=player_name, x=spawn_x, y=spawn_y)

        # Assign entity ID and add to game state
        if player_index == 0:
            # First player uses "player" as ID and replaces the temp player
            entity_id = "player"
            player_entity.entity_id = entity_id
            self.game_state.player = player_entity
        else:
            # Additional players get unique IDs
            entity_id = f"player_{player_id[:8]}"
            player_entity.entity_id = entity_id
            # Add to entities dict
            self.game_state.entities[entity_id] = player_entity

        # Create player slot
        slot = PlayerSlot(
            player_id=player_id,
            player_name=player_name,
            player_entity=player_entity,
            entity_id=entity_id,
        )

        self.player_slots[player_id] = slot
        self.entity_to_player[entity_id] = player_id

        logger.info(f"Added player {player_name} (ID: {player_id}, entity: {entity_id}) at position ({spawn_x}, {spawn_y})")
        return True

    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the game.

        Args:
            player_id: Player to remove

        Returns:
            True if player was removed
        """
        if player_id not in self.player_slots:
            return False

        slot = self.player_slots[player_id]
        slot.is_active = False

        # Mark entity as inactive (don't remove for game integrity)
        # In future, this could trigger player death or spectator mode

        logger.info(f"Removed player {slot.player_name} (ID: {player_id})")
        return True

    def get_player_entity(self, player_id: str) -> Optional[Player]:
        """Get the entity for a specific player.

        Args:
            player_id: Player ID

        Returns:
            Player entity or None
        """
        slot = self.player_slots.get(player_id)
        if not slot:
            return None

        return slot.player_entity

    def get_player_entity_id(self, player_id: str) -> Optional[str]:
        """Get the entity ID for a player.

        Args:
            player_id: Player ID

        Returns:
            Entity ID or None
        """
        slot = self.player_slots.get(player_id)
        if not slot:
            return None

        return slot.entity_id

    def get_all_players(self) -> List[PlayerSlot]:
        """Get all active players.

        Returns:
            List of active player slots
        """
        return [slot for slot in self.player_slots.values() if slot.is_active]

    def get_player_count(self) -> int:
        """Get number of active players."""
        return sum(1 for slot in self.player_slots.values() if slot.is_active)

    def add_message(self, message: str) -> None:
        """Add a message to the game log.

        Args:
            message: Message to add
        """
        if self.game_state:
            self.game_state.add_message(message)

    @property
    def round_number(self) -> int:
        return self.scheduler.round_number

    @property
    def actions_this_round(self) -> int:
        """Seats that have taken their action this round."""
        return len(self.scheduler.acted)

    def waiting_on(self) -> List[str]:
        """player_ids the round is still waiting for."""
        return [
            self.entity_to_player[eid]
            for eid in self.scheduler.waiting_on()
            if eid in self.entity_to_player
        ]

    def living_entity_ids(self) -> List[str]:
        return [
            slot.entity_id for slot in self.player_slots.values()
            if slot.player_entity and slot.player_entity.is_alive
        ]

    def update_player_alive_status(self) -> List[PlayerSlot]:
        """Update alive status for all players based on their entities.

        Only syncs the slots; ending the run (every player dead) is the engine's
        job (TurnProcessor.check_game_over publishes run_ended).

        Returns:
            Slots whose player died since the last call (for per-player scoring).
        """
        newly_dead = []
        for slot in self.player_slots.values():
            if slot.player_entity:
                was_alive = slot.is_alive
                slot.is_alive = slot.player_entity.is_alive
                if was_alive and not slot.is_alive:
                    newly_dead.append(slot)

        return newly_dead

    def _spawn_floor_entities(self, floor: int) -> None:
        """Spawn monsters, ore veins, and forges for the given floor.

        Args:
            floor: Floor number to spawn entities for
        """
        spawned = self.spawner.spawn_all_for_floor(floor, self.game_state.dungeon_map)
        monsters = spawned['monsters']
        ore_veins = spawned['ore_veins']
        forges = spawned['forges']

        for entity in [*monsters, *ore_veins, *forges]:
            self.game_state.entities[entity.entity_id] = entity

        logger.info(
            f"Spawned floor {floor} entities: {len(monsters)} monsters, "
            f"{len(ore_veins)} ore veins, {len(forges)} forges"
        )
