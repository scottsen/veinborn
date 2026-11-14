"""
GameState - holds all game state in one place.

This class:
- Centralizes all mutable game state
- Makes save/load easier
- Provides clean separation for GameContext
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging

from .entities import Player
from .base.entity import Entity
from .world import Map
from .rng import GameRNG

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """
    Central game state container.

    Design principles:
    - All mutable state in one place
    - Easy to serialize for save/load
    - Clear ownership of entities
    """

    # Primary entities
    player: Player
    entities: Dict[str, Entity] = field(default_factory=dict)

    # World
    dungeon_map: Map = field(default_factory=lambda: Map(80, 24))

    # Game progress
    turn_count: int = 0
    current_floor: int = 1

    # Randomness (for reproducibility)
    seed: Optional[Union[int, str]] = None
    rng_state: Optional[tuple] = None
    # VB-18: the live RNG instance this game's randomness draws from. Not
    # serialized (rng_state above is the save/load snapshot) -- a live
    # object reference so callers (world gen, spawning, AI) use this game's
    # own stream rather than the process-global GameRNG singleton, which
    # multiplayer's concurrent games would otherwise share and corrupt.
    # None only for legacy construction paths that haven't been updated to
    # pass one explicitly; get_rng() below falls back to the singleton.
    rng: Optional[GameRNG] = None

    # Message log
    messages: List[str] = field(default_factory=list)
    # VB-20: total messages ever added, monotonic and never trimmed (unlike
    # `messages`, which is capped at 100). Lets a host tell whether an action
    # added log lines even after the message list itself stops growing in
    # length (e.g. to report a refused action's message to its sender).
    message_count: int = 0

    # Game state
    game_over: bool = False
    victory: bool = False

    # Player identity (Phase 5: for high scores)
    player_name: str = "Anonymous"

    # VB-105 development switch: send every viewer the whole floor (read by build_snapshot only)
    reveal_map: bool = False

    # Run type (Phase 6: for Legacy Vault tracking)
    run_type: str = "pure"  # "pure" or "legacy"

    def __post_init__(self) -> None:
        # VB-23: entities is the single store every lookup reads from
        # (GameContext.get_entity/get_entity_at/get_entities_in_range/
        # get_all_players all scan entities only). Previously the local
        # player lived ONLY in .player -- invisible to every one of those,
        # so the multiplayer host couldn't be found at their own tile and
        # Action._get_actor() needed a special-case fallback (VB-16) just
        # to resolve actor_id == the player's own id. __setattr__ below
        # keeps this in sync for every later reassignment of .player too
        # (e.g. save/load or a test swapping in a different player).
        if self.player is not None:
            self.entities[self.player.entity_id] = self.player

    def __setattr__(self, name: str, value) -> None:
        if name == "player" and value is not None and "entities" in self.__dict__:
            old_player = self.__dict__.get("player")
            if old_player is not None and old_player.entity_id != value.entity_id:
                # Drop the stale entry so reassigning .player (e.g. a
                # placeholder player made real at its spawn position)
                # doesn't leave an orphaned duplicate entity behind.
                self.entities.pop(old_player.entity_id, None)
            self.entities[value.entity_id] = value
        super().__setattr__(name, value)

    def add_message(self, message: str) -> None:
        """Add message to log (max 100 messages)."""
        self.messages.append(message)
        self.message_count += 1
        if len(self.messages) > 100:
            self.messages.pop(0)
        logger.info(f"Game message: {message}")

    def get_recent_messages(self, count: int = 10) -> List[str]:
        """Get most recent messages."""
        return self.messages[-count:]

    def clear_floor_entities(self, keep_ids=()) -> None:
        """Remove everything left over from the previous floor.

        The player (and any ids in keep_ids, e.g. other multiplayer players)
        survive; wiping the whole dict would evict them from the world.
        """
        keep = set(keep_ids)
        keep.add(self.player.entity_id)
        for entity_id in [eid for eid in self.entities if eid not in keep]:
            del self.entities[entity_id]

    def cleanup_dead_entities(self) -> None:
        """Remove dead entities from the game."""
        dead_ids = [
            entity_id
            for entity_id, entity in self.entities.items()
            if not entity.is_alive
        ]

        for entity_id in dead_ids:
            entity = self.entities[entity_id]
            logger.debug(f"Removing dead entity: {entity.name} ({entity_id})")
            del self.entities[entity_id]
