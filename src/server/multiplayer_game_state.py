"""Seat bookkeeping for a multiplayer run.

The run's GameState is built once, from every seated player, when the game
starts (plan D1). The rules live in core.engine.Engine; this class only maps
seats (player_id) to their entities and holds the round scheduler.
"""

from collections import deque
from typing import Dict, List, Optional, Sequence
from dataclasses import dataclass
import logging

from core.game_state import GameState
from core.entities import Player
from core.rng import GameRNG
from core.config import ConfigLoader
from core.entity_loader import EntityLoader
from core.floor_manager import generate_floor_map
from core.spawning import EntitySpawner
from core.turn_scheduler import RoundScheduler

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Seat:
    """A player seated in the lobby, as the run is started with it."""

    player_id: str
    player_name: str
    player_class: str = "warrior"


def seat_entity_id(player_id: str, taken=()) -> str:
    """The entity id for a seat: the same scheme for every seat, no host special case.

    Short for logs; falls back to the full player_id on a prefix collision.
    """
    short = f"player_{player_id[:8]}"
    return short if short not in taken else f"player_{player_id}"


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
    """The run's GameState plus seat bookkeeping (player_id <-> entity, round scheduler).

    Built once from every seated player (plan D1): one map, every player on
    their own spawn position, the floor populated. `game_state.player` is the
    first seat only for the single-player compatibility reads that remain
    (log lines, `build_snapshot`'s default viewer); multiplayer always names
    the viewer or actor explicitly.
    """

    def __init__(self, seats: Sequence[Seat], seed: Optional[int] = None, max_players: int = 4):
        """Build the run for these seats.

        Args:
            seats: The seated players, in seat order (at least one)
            seed: Random seed for dungeon generation
            max_players: Seat limit of the game

        Raises:
            ValueError: no seats, more seats than max_players, or a player seated twice
        """
        if not seats:
            raise ValueError("a multiplayer run needs at least one seat")
        if len(seats) > max_players:
            raise ValueError(f"{len(seats)} seats for a game of {max_players}")
        if len({s.player_id for s in seats}) != len(seats):
            raise ValueError("a player is seated twice")

        self.max_players = max_players
        self.seed = seed
        self.is_multiplayer = True
        self.scheduler = RoundScheduler()

        # Spawning (monsters/ore veins/forges): shared config/loader
        self.config = ConfigLoader.load()
        self.spawner = EntitySpawner(self.config, EntityLoader())

        # VB-18: a dedicated GameRNG for THIS game, never the process-global
        # singleton, so concurrent games on one server cannot reseed each other.
        # It is threaded through dungeon_map.rng / state.rng.
        rng = GameRNG(seed)
        dungeon_map = generate_floor_map(self.config, rng)
        positions = dungeon_map.find_player_spawn_positions(len(seats))

        self.player_slots: Dict[str, PlayerSlot] = {}
        self.entity_to_player: Dict[str, str] = {}  # entity_id -> player_id
        players: List[Player] = []
        for index, seat in enumerate(seats):
            x, y = positions[index] if index < len(positions) else dungeon_map.find_starting_position()
            entity = _create_player(seat, x, y)
            entity.entity_id = seat_entity_id(seat.player_id, taken=self.entity_to_player)
            players.append(entity)
            self.player_slots[seat.player_id] = PlayerSlot(
                player_id=seat.player_id,
                player_name=seat.player_name,
                player_entity=entity,
                entity_id=entity.entity_id,
            )
            self.entity_to_player[entity.entity_id] = seat.player_id
            logger.info(
                f"Seated {seat.player_name} (ID: {seat.player_id}, entity: {entity.entity_id}) at ({x}, {y})"
            )

        self.game_state = GameState(
            player=players[0],
            dungeon_map=dungeon_map,
            seed=seed,
            player_name=players[0].name,
            rng=rng,
        )
        for entity in players[1:]:
            self.game_state.entities[entity.entity_id] = entity

        # Populate floor 1 (VB-4: MP once spawned nothing, so AI ran over an empty floor)
        self._spawn_floor_entities(self.game_state.current_floor)

    def drop_seat(self, player_id: str) -> bool:
        """The seat leaves the run (plan D7 "dropped"): left, or its reconnect grace expired.

        Its character leaves the floor (the entity object, with hp, level, inventory
        and gear, stays on the slot for a later rejoin) and the round stops owing it
        an action. Returns True if that completes the current round.
        """
        slot = self.player_slots.get(player_id)
        if slot is None or not slot.is_active:
            return False
        slot.is_active = False
        self.game_state.entities.pop(slot.entity_id, None)
        logger.info(f"Dropped seat {slot.player_name} (ID: {player_id}, entity: {slot.entity_id})")
        return self.scheduler.drop(slot.entity_id)

    def dropped_seats(self) -> List[PlayerSlot]:
        """Seats that left or timed out and can be taken back (plan D7 "dropped")."""
        return [slot for slot in self.player_slots.values() if not slot.is_active]

    def rekey_seat(self, old_id: str, new_id: str) -> None:
        """A seat now belongs to another player id; seat order is kept."""
        self.player_slots = {
            (new_id if pid == old_id else pid): slot for pid, slot in self.player_slots.items()
        }
        slot = self.player_slots[new_id]
        slot.player_id = new_id
        self.entity_to_player[slot.entity_id] = new_id

    def rejoin_seat(self, player_id: str) -> bool:
        """A dropped seat comes back (plan D7 "rejoin").

        The kept character returns to the current floor next to a living party member
        and the round owes it an action from the next round on (the scheduler is not
        touched: `next_round` takes the living seats). A dead character comes back
        as a spectator, as a dead player who stayed would be.
        Returns False if there is no dropped seat for `player_id`.
        """
        slot = self.player_slots.get(player_id)
        if slot is None or slot.is_active:
            return False
        slot.is_active = True
        entity = slot.player_entity
        if entity.is_alive:
            x, y = self._free_tile_near_party(exclude=slot.entity_id)
            entity.move_to(x, y)
            self.game_state.entities[slot.entity_id] = entity
        logger.info(f"Rejoined seat {slot.player_name} (ID: {slot.player_id}, entity: {slot.entity_id})")
        return True

    def _free_tile_near_party(self, exclude: str) -> tuple:
        """The closest walkable, unoccupied tile to a living party member (breadth-first).

        Falls back to the floor's starting position if the party is nowhere to be found.
        """
        state = self.game_state
        dungeon_map = state.dungeon_map
        occupied = {(e.x, e.y) for eid, e in state.entities.items() if eid != exclude}
        anchors = [
            (slot.player_entity.x, slot.player_entity.y)
            for slot in self.player_slots.values()
            if slot.is_active and slot.entity_id != exclude
            and slot.is_alive and slot.entity_id in state.entities
        ]
        seen = set(anchors)
        queue = deque(anchors)
        while queue:
            x, y = queue.popleft()
            if dungeon_map.is_walkable(x, y) and (x, y) not in occupied:
                return x, y
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                step = (x + dx, y + dy)
                if step not in seen and dungeon_map.in_bounds(*step):
                    seen.add(step)
                    queue.append(step)
        return dungeon_map.find_starting_position()

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
        """Seats the round owes an action: alive and not dropped."""
        return [
            slot.entity_id for slot in self.player_slots.values()
            if slot.is_active and slot.player_entity and slot.player_entity.is_alive
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


def _create_player(seat: Seat, x: int, y: int) -> Player:
    """The seat's character at (x, y); an unknown class falls back to a classless Player."""
    from core.character_class import CharacterClass, create_player_from_class
    try:
        return create_player_from_class(
            class_type=CharacterClass.from_string(seat.player_class), x=x, y=y, name=seat.player_name
        )
    except Exception as e:
        logger.error(f"Unknown class {seat.player_class!r} for {seat.player_name}: {e}; using the default")
        return Player(name=seat.player_name, x=x, y=y)
