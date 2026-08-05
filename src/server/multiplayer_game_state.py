"""Multiplayer-aware GameState wrapper.

Extends the single-player GameState to support multiple players
while maintaining compatibility with existing single-player code.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

from core.game_state import GameState
from core.entities import Player
from core.base.entity import Entity
from core.rng import GameRNG
from core.world import Map
from core.config import ConfigLoader
from core.entity_loader import EntityLoader
from core.spawning import EntitySpawner

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
        self.actions_this_round = 0
        self.round_number = 0

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
            # Initialize RNG with seed if provided
            if self.seed is not None:
                GameRNG.initialize(self.seed)
                logger.info(f"Initialized RNG with seed: {self.seed}")

            # Create temporary player entity at (0, 0) to initialize GameState
            temp_player = Player(name=player_name, x=0, y=0)
            self.game_state = GameState(
                player=temp_player,
                seed=self.seed,
                player_name=player_name,
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
            self.game_state.player = player_entity
        else:
            # Additional players get unique IDs
            entity_id = f"player_{player_id[:8]}"
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

    def is_player_action(self, entity_id: str) -> bool:
        """Check if an entity belongs to a player.

        Args:
            entity_id: Entity ID to check

        Returns:
            True if entity is a player
        """
        return entity_id in self.entity_to_player

    def get_state_dict(self) -> Dict:
        """Get game state as a dictionary for serialization.

        Returns:
            Dictionary representation of game state
        """
        if not self.game_state:
            return {
                "initialized": False,
                "player_count": 0,
            }

        # Build player info
        players_info = []
        for slot in self.player_slots.values():
            player_entity = slot.player_entity
            # Get class from entity stats if available
            player_class = player_entity.stats.get('class', 'Warrior') if hasattr(player_entity, 'stats') else 'Warrior'
            class_type = player_entity.stats.get('class_type', 'warrior') if hasattr(player_entity, 'stats') else 'warrior'

            # Serialize inventory
            inventory_data = []
            if hasattr(player_entity, 'inventory'):
                for item in player_entity.inventory:
                    inventory_data.append({
                        "entity_id": item.entity_id,
                        "content_id": item.content_id,
                        "name": item.name,
                        "entity_type": item.entity_type.value if hasattr(item.entity_type, 'value') else str(item.entity_type),
                        "stats": dict(item.stats) if hasattr(item, 'stats') else {}
                    })

            players_info.append(
                {
                    "player_id": slot.player_id,
                    "player_name": slot.player_name,
                    "player_class": class_type,
                    "player_class_display": player_class,
                    "entity_id": slot.entity_id,
                    "is_active": slot.is_active,
                    "is_alive": slot.is_alive,
                    "position": {
                        "x": player_entity.x,
                        "y": player_entity.y,
                    },
                    "health": {
                        "current": player_entity.hp,
                        "max": player_entity.max_hp,
                    },
                    "stats": {
                        "attack": player_entity.attack,
                        "defense": player_entity.defense,
                    },
                    "inventory": inventory_data
                }
            )

        # Non-player entities (monsters/ore veins/forges) - player entities are
        # already represented above in players_info
        player_entity_ids = set(self.entity_to_player.keys())
        monsters_info = [
            entity.to_dict()
            for entity_id, entity in self.game_state.entities.items()
            if entity_id not in player_entity_ids
        ]

        return {
            "initialized": True,
            "is_multiplayer": self.is_multiplayer,
            "player_count": self.get_player_count(),
            "max_players": self.max_players,
            "players": players_info,
            "monsters": monsters_info,
            "map": self.game_state.dungeon_map.to_dict(),
            "turn_count": self.game_state.turn_count,
            "current_floor": self.game_state.current_floor,
            "round_number": self.round_number,
            "actions_this_round": self.actions_this_round,
            "game_over": self.game_state.game_over,
            "victory": self.game_state.victory,
            "recent_messages": self.game_state.get_recent_messages(20),
        }

    def to_dict(self) -> Dict:
        """Alias for get_state_dict for compatibility."""
        return self.get_state_dict()

    def add_message(self, message: str) -> None:
        """Add a message to the game log.

        Args:
            message: Message to add
        """
        if self.game_state:
            self.game_state.add_message(message)

    def increment_round(self) -> None:
        """Increment the round counter and reset actions."""
        self.round_number += 1
        self.actions_this_round = 0
        logger.debug(f"Round {self.round_number} started")

    def increment_actions(self) -> int:
        """Increment action counter and return current count.

        Returns:
            Current action count for this round
        """
        self.actions_this_round += 1
        return self.actions_this_round

    def update_player_alive_status(self) -> None:
        """Update alive status for all players based on their entities."""
        for slot in self.player_slots.values():
            if slot.player_entity:
                slot.is_alive = slot.player_entity.is_alive

        # Check if all players are dead
        if self.game_state and all(
            not slot.is_alive for slot in self.player_slots.values()
        ):
            self.game_state.game_over = True
            self.add_message("All players have died. Game over!")

    def get_active_player_count(self) -> int:
        """Get count of active, alive players."""
        return sum(
            1
            for slot in self.player_slots.values()
            if slot.is_active and slot.is_alive
        )

    def _spawn_floor_entities(self, floor: int) -> None:
        """Spawn monsters, ore veins, and forges for the given floor.

        Args:
            floor: Floor number to spawn entities for
        """
        dungeon_map = self.game_state.dungeon_map

        monsters = self.spawner.spawn_monsters_for_floor(floor, dungeon_map)
        ore_veins = self.spawner.spawn_ore_veins_for_floor(floor, dungeon_map)
        forges = self.spawner.spawn_forges_for_floor(floor, dungeon_map)

        special_entities = self.spawner.spawn_special_room_entities(floor, dungeon_map)
        monsters.extend(special_entities['monsters'])
        ore_veins.extend(special_entities['ores'])

        for entity in [*monsters, *ore_veins, *forges]:
            self.game_state.entities[entity.entity_id] = entity

        logger.info(
            f"Spawned floor {floor} entities: {len(monsters)} monsters, "
            f"{len(ore_veins)} ore veins, {len(forges)} forges"
        )

    def _get_victory_floor(self) -> int:
        """Get the floor number that triggers victory."""
        try:
            floor = self.config.game_constants['progression']['victory_floor']
            return floor if isinstance(floor, int) else 100
        except (AttributeError, KeyError, TypeError):
            return 100

    def _clear_non_player_entities(self) -> None:
        """Remove monsters/ore veins/forges from the previous floor.

        Cannot use dict.clear() here (unlike single-player FloorManager) -
        MP stores non-host players in game_state.entities too, and wiping
        the whole dict would kick them from the game on every descent.
        """
        player_entity_ids = set(self.entity_to_player.keys())
        for entity_id in list(self.game_state.entities.keys()):
            if entity_id not in player_entity_ids:
                del self.game_state.entities[entity_id]

    def _reposition_players_at_new_floor(self) -> None:
        """Move every player to a spawn position on the newly generated floor."""
        spawn_positions = self.game_state.dungeon_map.find_player_spawn_positions(
            len(self.player_slots)
        )
        self.spawn_positions = spawn_positions

        for index, slot in enumerate(self.player_slots.values()):
            if index < len(spawn_positions):
                x, y = spawn_positions[index]
            else:
                x, y = self.game_state.dungeon_map.find_starting_position()
            slot.player_entity.move_to(x, y)

    def descend_floor(self) -> None:
        """Descend the whole party to the next floor.

        Regenerates the map, repositions all players, and respawns floor
        entities. Kept separate from core.floor_manager.FloorManager since
        that class assumes a single player (entities.clear() would delete
        other MP players) and has single-player-only side effects
        (high scores, Legacy Vault) that don't apply to a shared session.
        """
        if not self.game_state:
            return

        old_floor = self.game_state.current_floor
        new_floor = old_floor + 1

        if new_floor >= self._get_victory_floor():
            self.game_state.victory = True
            self.game_state.game_over = True
            self.add_message("🎉 VICTORY! The party has escaped the dungeon!")
            logger.info(f"Multiplayer game reached victory floor {new_floor}")
            return

        self.game_state.current_floor = new_floor
        self.game_state.dungeon_map = Map(
            width=self.config.game_constants['map']['default_width'],
            height=self.config.game_constants['map']['default_height'],
            config=self.config,
        )

        self._reposition_players_at_new_floor()
        self._clear_non_player_entities()
        self._spawn_floor_entities(new_floor)

        self.add_message(f"The party descends to floor {new_floor}!")
        logger.info(f"Multiplayer descended from floor {old_floor} to floor {new_floor}")
