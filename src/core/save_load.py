"""
Save/Load system for Veinborn.

Handles serialization and deserialization of game state.

Features:
- JSON-based save files (human-readable for debugging)
- Full game state persistence
- RNG state preservation (seeded run continuity)
- Automatic save directory creation
- Multiple save slots support
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from .game_state import GameState
from .entities import Player, Monster, OreVein, Forge
from .base.entity import Entity, EntityType
from .world import Map, Tile, TileType, Room
from .rng import GameRNG

logger = logging.getLogger(__name__)


class SaveLoadError(Exception):
    """Base exception for save/load operations."""
    pass


class SaveSystem:
    """
    Handles saving and loading game state.

    Design principles:
    - JSON for human readability
    - Versioned saves for future compatibility
    - Atomic saves (write to temp, then rename)
    - Clear error messages
    """

    VERSION = "1.0.0"

    def __init__(self, save_dir: Optional[Path] = None):
        """
        Initialize save system.

        Args:
            save_dir: Directory for save files (default: ~/.veinborn/saves)
        """
        if save_dir is None:
            save_dir = Path.home() / ".veinborn" / "saves"

        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"SaveSystem initialized: {self.save_dir}")

    def save_game(self, state: GameState, slot_name: str = "quicksave") -> Path:
        """
        Save game state to disk.

        Args:
            state: Current game state
            slot_name: Save slot name (default: "quicksave")

        Returns:
            Path to saved file

        Raises:
            SaveLoadError: If save fails
        """
        try:
            # Serialize game state
            save_data = self._serialize_state(state)

            # Add metadata
            save_data["_metadata"] = {
                "version": self.VERSION,
                "timestamp": datetime.now().isoformat(),
                "player_name": state.player_name,
                "floor": state.current_floor,
                "turns": state.turn_count,
            }

            # Write to file (atomic operation)
            save_path = self.save_dir / f"{slot_name}.json"
            temp_path = save_path.with_suffix('.tmp')

            with open(temp_path, 'w') as f:
                json.dump(save_data, f, indent=2)

            # Atomic rename
            temp_path.rename(save_path)

            logger.info(f"Game saved: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"Save failed: {e}")
            raise SaveLoadError(f"Failed to save game: {e}") from e

    def load_game(self, slot_name: str = "quicksave") -> GameState:
        """
        Load game state from disk.

        Args:
            slot_name: Save slot name

        Returns:
            Loaded game state

        Raises:
            SaveLoadError: If load fails
        """
        save_path = self.save_dir / f"{slot_name}.json"

        if not save_path.exists():
            raise SaveLoadError(f"Save file not found: {save_path}")

        try:
            with open(save_path, 'r') as f:
                save_data = json.load(f)

            # Check version compatibility
            metadata = save_data.get("_metadata", {})
            version = metadata.get("version", "unknown")

            if version != self.VERSION:
                logger.warning(f"Save version mismatch: {version} vs {self.VERSION}")
                # TODO: Add version migration if needed

            # Deserialize state
            state = self._deserialize_state(save_data)

            logger.info(f"Game loaded: {save_path}")
            return state

        except json.JSONDecodeError as e:
            logger.error(f"Invalid save file: {e}")
            raise SaveLoadError(f"Corrupted save file: {e}") from e
        except Exception as e:
            logger.error(f"Load failed: {e}")
            raise SaveLoadError(f"Failed to load game: {e}") from e

    def list_saves(self) -> List[Dict[str, Any]]:
        """
        List all available save files with metadata.

        Returns:
            List of save file info dicts
        """
        saves = []

        for save_file in self.save_dir.glob("*.json"):
            try:
                with open(save_file, 'r') as f:
                    data = json.load(f)

                metadata = data.get("_metadata", {})
                saves.append({
                    "slot_name": save_file.stem,
                    "path": str(save_file),
                    "timestamp": metadata.get("timestamp"),
                    "player_name": metadata.get("player_name", "Unknown"),
                    "floor": metadata.get("floor", 1),
                    "turns": metadata.get("turns", 0),
                })
            except Exception as e:
                logger.warning(f"Failed to read save metadata: {save_file}: {e}")

        # Sort by timestamp (newest first)
        saves.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
        return saves

    def delete_save(self, slot_name: str) -> bool:
        """
        Delete a save file.

        Args:
            slot_name: Save slot to delete

        Returns:
            True if deleted successfully
        """
        save_path = self.save_dir / f"{slot_name}.json"

        if save_path.exists():
            save_path.unlink()
            logger.info(f"Save deleted: {save_path}")
            return True

        return False

    # Serialization helpers

    def _serialize_state(self, state: GameState) -> Dict[str, Any]:
        """Convert GameState to JSON-serializable dict."""
        return {
            "player": self._serialize_entity(state.player),
            # VB-23: state.entities now also contains the player (kept in
            # sync so entity/position lookups can find them), but the save
            # format keeps them separate as it always has -- exclude here
            # to avoid writing (and, on load, deserializing) the player
            # twice under two different object instances.
            "entities": {
                entity_id: self._serialize_entity(entity)
                for entity_id, entity in state.entities.items()
                if entity_id != state.player.entity_id
            },
            "dungeon_map": self._serialize_map(state.dungeon_map),
            "turn_count": state.turn_count,
            "current_floor": state.current_floor,
            "seed": state.seed,
            "rng_state": state.rng_state,
            "messages": state.messages,
            "game_over": state.game_over,
            "victory": state.victory,
            "player_name": state.player_name,
            # VB-19: previously dropped -- a loaded legacy run silently
            # reverted to "pure", changing Legacy Vault eligibility.
            "run_type": state.run_type,
        }

    def _serialize_entity(self, entity: Entity) -> Dict[str, Any]:
        """Convert Entity to JSON-serializable dict.

        VB-19: this previously dropped inventory, equipped_weapon,
        equipped_armor, and blocks_movement entirely, and the type-specific
        fields (OreVein's ore_type/hardness/conductivity/malleability/
        purity/density, Forge's forge_type) needed by _deserialize_entity to
        reconstruct the correct subclass with correct data -- without them
        a loaded ore vein silently reverted to default copper/50-quality
        stats and a loaded Forge came back as a plain, non-interactable
        Entity (see VB-19, _deserialize_entity).
        """
        data = {
            "entity_id": entity.entity_id,
            "entity_type": entity.entity_type.value,
            "name": entity.name,
            "x": entity.x,
            "y": entity.y,
            "hp": entity.hp,
            "max_hp": entity.max_hp,
            "attack": entity.attack,
            "defense": entity.defense,
            "stats": entity.stats,
            "is_alive": entity.is_alive,
            "is_active": entity.is_active,
            "blocks_movement": entity.blocks_movement,
            "content_id": entity.content_id,
            # Specialized fields for different entity types
            "_class": entity.__class__.__name__,
        }

        if isinstance(entity, Player):
            data["inventory"] = [self._serialize_entity(item) for item in entity.inventory]
            data["equipped_weapon"] = (
                self._serialize_entity(entity.equipped_weapon) if entity.equipped_weapon else None
            )
            data["equipped_armor"] = (
                self._serialize_entity(entity.equipped_armor) if entity.equipped_armor else None
            )
            data["equipped_shield"] = (
                self._serialize_entity(entity.equipped_shield) if entity.equipped_shield else None
            )
        elif isinstance(entity, OreVein):
            data["ore_type"] = entity.ore_type
            data["hardness"] = entity.hardness
            data["conductivity"] = entity.conductivity
            data["malleability"] = entity.malleability
            data["purity"] = entity.purity
            data["density"] = entity.density
        elif isinstance(entity, Forge):
            data["forge_type"] = entity.forge_type

        return data

    def _serialize_map(self, dungeon_map: Map) -> Dict[str, Any]:
        """Convert Map to JSON-serializable dict."""
        return {
            "width": dungeon_map.width,
            "height": dungeon_map.height,
            "tiles": [
                [
                    {
                        "tile_type": dungeon_map.tiles[x][y].tile_type.value,
                        "explored": dungeon_map.tiles[x][y].explored,
                    }
                    for y in range(dungeon_map.height)
                ]
                for x in range(dungeon_map.width)
            ],
            "rooms": [
                {
                    "x": room.x,
                    "y": room.y,
                    "width": room.width,
                    "height": room.height,
                }
                for room in dungeon_map.rooms
            ],
            # VB-105: what each viewer has seen of this floor (fog of war memory)
            "explored_by": {
                viewer: sorted([x, y] for x, y in cells)
                for viewer, cells in dungeon_map.explored_by.items()
            },
        }

    # Deserialization helpers

    def _deserialize_state(self, data: Dict[str, Any]) -> GameState:
        """Convert dict to GameState."""
        # Deserialize player. VB-19: this used to duplicate a stripped-down
        # copy of _deserialize_entity's Player reconstruction inline here
        # (missing inventory/equipped_weapon/equipped_armor/blocks_movement
        # entirely) -- delegate to _deserialize_entity so the primary
        # player and any player-type entities in state.entities go through
        # the same, fully correct reconstruction path.
        player = self._deserialize_entity(data["player"])

        # Deserialize entities
        entities = {}
        for entity_id, entity_data in data["entities"].items():
            entity = self._deserialize_entity(entity_data)
            entities[entity_id] = entity

        # Deserialize map
        dungeon_map = self._deserialize_map(data["dungeon_map"])

        # Restore RNG state. VB-18: restore into a dedicated GameRNG
        # instance for this game (not the process-global singleton) and
        # thread it through state.rng/dungeon_map.rng explicitly, same as
        # a freshly-started game -- otherwise a loaded game's continued
        # play (next floor descent, etc.) would silently fall back to
        # GameRNG.get_instance(), which a concurrent multiplayer game could
        # have re-seeded.
        rng = GameRNG(data.get("seed"))
        if data.get("rng_state"):
            rng_state = self._json_to_rng_state(data["rng_state"])
            rng.setstate(rng_state)
        dungeon_map.rng = rng

        # Create game state
        state = GameState(
            player=player,
            entities=entities,
            dungeon_map=dungeon_map,
            turn_count=data["turn_count"],
            current_floor=data["current_floor"],
            seed=data.get("seed"),
            rng_state=data.get("rng_state"),
            rng=rng,
            messages=data["messages"],
            game_over=data["game_over"],
            victory=data["victory"],
            player_name=data["player_name"],
            # VB-19: previously dropped -- see _serialize_state.
            run_type=data.get("run_type", "pure"),
        )

        return state

    def _deserialize_entity(self, data: Dict[str, Any]) -> Entity:
        """Convert dict to Entity (or subclass).

        VB-19: previously every branch here only passed the base Entity
        fields to the constructor, so OreVein-specific properties
        (ore_type/hardness/conductivity/malleability/purity/density) and
        Forge's forge_type were never restored -- a loaded ore vein's
        __post_init__ would re-derive its name/mining-time from default
        field values ("copper", hardness=50) regardless of what was
        actually mined, and Forge had no branch at all so it silently fell
        through to the generic Entity case, becoming a plain,
        non-interactable object.
        """
        entity_type = EntityType(data["entity_type"])
        entity_class = data.get("_class", "Entity")

        # Create appropriate entity class, passing type-specific
        # constructor fields so __post_init__ derives correct data.
        if entity_class == "Player":
            entity = Player(
                entity_id=data["entity_id"],
                name=data["name"],
                x=data["x"],
                y=data["y"],
                hp=data["hp"],
                max_hp=data["max_hp"],
                attack=data["attack"],
                defense=data["defense"],
            )
        elif entity_class == "Monster":
            entity = Monster(
                entity_id=data["entity_id"],
                name=data["name"],
                x=data["x"],
                y=data["y"],
                hp=data["hp"],
                max_hp=data["max_hp"],
                attack=data["attack"],
                defense=data["defense"],
            )
        elif entity_class == "OreVein":
            entity = OreVein(
                entity_id=data["entity_id"],
                x=data["x"],
                y=data["y"],
                ore_type=data.get("ore_type", "copper"),
                hardness=data.get("hardness", 50),
                conductivity=data.get("conductivity", 50),
                malleability=data.get("malleability", 50),
                purity=data.get("purity", 50),
                density=data.get("density", 50),
            )
        elif entity_class == "Forge":
            entity = Forge(
                entity_id=data["entity_id"],
                x=data["x"],
                y=data["y"],
                forge_type=data.get("forge_type", "basic_forge"),
            )
        else:
            # Generic entity
            entity = Entity(
                entity_id=data["entity_id"],
                entity_type=entity_type,
                name=data["name"],
                x=data["x"],
                y=data["y"],
                hp=data["hp"],
                max_hp=data["max_hp"],
                attack=data["attack"],
                defense=data["defense"],
            )

        # Restore common fields
        entity.stats = data["stats"]
        entity.is_alive = data["is_alive"]
        entity.is_active = data["is_active"]
        entity.content_id = data.get("content_id")
        # VB-19: previously dropped -- affects collision after reload.
        if "blocks_movement" in data:
            entity.blocks_movement = data["blocks_movement"]

        # VB-19: previously dropped entirely -- a loaded player's inventory
        # and equipped gear vanished.
        if isinstance(entity, Player):
            entity.inventory = [
                self._deserialize_entity(item_data) for item_data in data.get("inventory", [])
            ]
            entity.equipped_weapon = (
                self._deserialize_entity(data["equipped_weapon"])
                if data.get("equipped_weapon") else None
            )
            entity.equipped_armor = (
                self._deserialize_entity(data["equipped_armor"])
                if data.get("equipped_armor") else None
            )
            entity.equipped_shield = (       # absent in saves from before VB-72
                self._deserialize_entity(data["equipped_shield"])
                if data.get("equipped_shield") else None
            )

        return entity

    def _deserialize_map(self, data: Dict[str, Any]) -> Map:
        """Convert dict to Map."""
        # Create map without generation
        dungeon_map = Map.__new__(Map)
        dungeon_map.width = data["width"]
        dungeon_map.height = data["height"]

        # Restore tiles
        dungeon_map.tiles = []
        for x in range(data["width"]):
            column = []
            for y in range(data["height"]):
                tile_data = data["tiles"][x][y]
                tile = Tile(
                    tile_type=TileType(tile_data["tile_type"]),
                    explored=tile_data["explored"],
                )
                column.append(tile)
            dungeon_map.tiles.append(column)

        # Restore rooms
        dungeon_map.rooms = [
            Room(
                x=room_data["x"],
                y=room_data["y"],
                width=room_data["width"],
                height=room_data["height"],
            )
            for room_data in data["rooms"]
        ]

        dungeon_map.explored_by = {
            viewer: {(x, y) for x, y in cells}
            for viewer, cells in data.get("explored_by", {}).items()
        }

        # Clear stairs cache (will be rebuilt on access)
        dungeon_map._stairs_down_cache = None
        dungeon_map._stairs_up_cache = None

        return dungeon_map

    def _json_to_rng_state(self, json_state):
        """
        Convert RNG state from JSON format to Python tuple format.

        JSON serialization converts tuples to lists, but Python's
        random.setstate() requires a tuple. This reconstructs the
        proper tuple structure.

        RNG state format: (version, tuple_of_ints, None)
        """
        if not json_state or len(json_state) != 3:
            return None

        version = json_state[0]
        state_list = json_state[1]
        gauss = json_state[2]

        # Convert list back to tuple
        state_tuple = tuple(state_list) if state_list else ()

        return (version, state_tuple, gauss)
