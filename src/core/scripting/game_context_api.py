"""
GameContext Lua API Bridge.

This module exposes GameContext methods to Lua scripts in a safe,
typed manner with proper serialization.
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import lupa

from ..base.game_context import GameContext
from ..base.entity import Entity, EntityType

if TYPE_CHECKING:
    from ..events import EventBus, GameEventType
    from ..events.lua_event_registry import LuaEventRegistry

logger = logging.getLogger(__name__)


class GameContextAPI:
    """
    Lua-safe wrapper for GameContext.

    Provides the 'brogue' global table in Lua with game state access methods.
    Handles Python <-> Lua type conversions and entity serialization.

    Example Lua usage:
        local player = brogue.get_player()
        local entities = brogue.get_entities_in_range(x, y, 5)
        brogue.add_message("Hello from Lua!")
        brogue.modify_stat(player.id, "hp", -10)
    """

    def __init__(
        self,
        context: GameContext,
        lua: lupa.LuaRuntime,
        event_bus: Optional['EventBus'] = None,
        lua_event_registry: Optional['LuaEventRegistry'] = None
    ):
        """
        Initialize GameContext API bridge.

        Args:
            context: GameContext instance to wrap
            lua: Lua runtime to register API in
            event_bus: Optional EventBus for event subscription (Phase 3)
            lua_event_registry: Optional LuaEventRegistry for event management (Phase 3)
        """
        self.context = context
        self.lua = lua
        self.event_bus = event_bus
        self.lua_event_registry = lua_event_registry
        self._register_api()
        logger.debug("GameContextAPI registered in Lua environment")

    def _register_api(self) -> None:
        """
        Register brogue.* methods in Lua globals.

        Creates a 'brogue' table with all API methods.
        """
        # Create brogue table
        brogue_table = self.lua.table()

        # Register entity query methods
        brogue_table["get_player"] = self._get_player
        brogue_table["get_entity"] = self._get_entity
        brogue_table["get_entity_at"] = self._get_entity_at
        brogue_table["get_entities_in_range"] = self._get_entities_in_range
        brogue_table["get_entities_by_type"] = self._get_entities_by_type

        # Register map query methods
        brogue_table["is_walkable"] = self._is_walkable
        brogue_table["in_bounds"] = self._in_bounds

        # Register game state methods
        brogue_table["add_message"] = self._add_message
        brogue_table["get_turn_count"] = self._get_turn_count
        brogue_table["get_floor"] = self._get_floor

        # Register entity manipulation methods
        brogue_table["modify_stat"] = self._modify_stat
        brogue_table["deal_damage"] = self._deal_damage
        brogue_table["heal"] = self._heal
        brogue_table["is_alive"] = self._is_alive

        # Register AI-specific methods in brogue.ai table
        ai_table = self.lua.table()
        ai_table["get_target"] = self._ai_get_target
        ai_table["is_adjacent"] = self._ai_is_adjacent
        ai_table["distance_to"] = self._ai_distance_to
        ai_table["get_config"] = self._ai_get_config
        ai_table["attack"] = self._ai_attack
        ai_table["move_towards"] = self._ai_move_towards
        ai_table["flee_from"] = self._ai_flee_from
        ai_table["wander"] = self._ai_wander
        ai_table["idle"] = self._ai_idle
        brogue_table["ai"] = ai_table

        # Register event methods in brogue.event table (Phase 3)
        event_table = self.lua.table()
        event_table["subscribe"] = self._event_subscribe
        event_table["unsubscribe"] = self._event_unsubscribe
        event_table["get_types"] = self._event_get_types
        event_table["emit"] = self._event_emit
        brogue_table["event"] = event_table

        # Set brogue table as global
        self.lua.globals()["brogue"] = brogue_table
        logger.debug(
            "Registered brogue API with %d methods (%d AI, %d event methods)",
            len(brogue_table), len(ai_table), len(event_table)
        )

    # Entity serialization

    def _entity_to_lua(self, entity: Entity) -> Dict[str, Any]:
        """
        Convert Entity to Lua table.

        Args:
            entity: Entity to convert

        Returns:
            Dictionary with entity data (Lua-compatible)
        """
        if entity is None:
            return None

        lua_entity = {
            "id": entity.entity_id,
            "name": entity.name,
            "entity_type": entity.entity_type.name,
            "x": entity.x,
            "y": entity.y,
            "hp": entity.hp,
            "max_hp": entity.max_hp,
            "attack": entity.attack,
            "defense": entity.defense,
            "is_alive": entity.is_alive,
            "is_active": entity.is_active,
            "attackable": entity.attackable,
            "blocks_movement": entity.blocks_movement,
        }

        # Add custom stats
        if entity.stats:
            lua_entity["stats"] = dict(entity.stats)

        return lua_entity

    def _entities_to_lua(self, entities: List[Entity]) -> List[Dict[str, Any]]:
        """
        Convert list of entities to Lua tables.

        Args:
            entities: List of entities to convert

        Returns:
            List of Lua-compatible entity dictionaries
        """
        # Create a Lua table (1-indexed)
        lua_table = self.lua.table()
        for i, entity in enumerate(entities, 1):
            lua_table[i] = self._entity_to_lua(entity)
        return lua_table

    # Entity query methods

    def _get_player(self) -> Dict[str, Any]:
        """Get player entity as Lua table."""
        try:
            player = self.context.get_player()
            return self._entity_to_lua(player)
        except Exception as e:
            logger.error(f"Error getting player: {e}")
            return None

    def _get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get entity by ID.

        Args:
            entity_id: Entity ID to look up

        Returns:
            Entity as Lua table, or None if not found
        """
        try:
            entity = self.context.get_entity(entity_id)
            return self._entity_to_lua(entity)
        except Exception as e:
            logger.error(f"Error getting entity {entity_id}: {e}")
            return None

    def _get_entity_at(self, x: int, y: int) -> Optional[Dict[str, Any]]:
        """
        Get entity at position.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Entity as Lua table, or None if no entity at position
        """
        try:
            entity = self.context.get_entity_at(int(x), int(y))
            return self._entity_to_lua(entity)
        except Exception as e:
            logger.error(f"Error getting entity at ({x}, {y}): {e}")
            return None

    def _get_entities_in_range(
        self, x: int, y: int, radius: int
    ) -> List[Dict[str, Any]]:
        """
        Get entities within radius of position.

        Args:
            x: X coordinate
            y: Y coordinate
            radius: Search radius

        Returns:
            Lua table (1-indexed) of entity tables
        """
        try:
            entities = self.context.get_entities_in_range(
                int(x), int(y), int(radius)
            )
            return self._entities_to_lua(entities)
        except Exception as e:
            logger.error(f"Error getting entities in range: {e}")
            return self.lua.table()  # Empty table

    def _get_entities_by_type(self, type_name: str) -> List[Dict[str, Any]]:
        """
        Get all entities of a specific type.

        Args:
            type_name: Entity type name (e.g., "MONSTER", "ITEM")

        Returns:
            Lua table (1-indexed) of entity tables
        """
        try:
            entity_type = EntityType[type_name.upper()]
            entities = self.context.get_entities_by_type(entity_type)
            return self._entities_to_lua(entities)
        except KeyError:
            logger.error(f"Invalid entity type: {type_name}")
            return self.lua.table()
        except Exception as e:
            logger.error(f"Error getting entities by type: {e}")
            return self.lua.table()

    # Map query methods

    def _is_walkable(self, x: int, y: int) -> bool:
        """
        Check if position is walkable.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if walkable, False otherwise
        """
        try:
            return self.context.is_walkable(int(x), int(y))
        except Exception as e:
            logger.error(f"Error checking walkability: {e}")
            return False

    def _in_bounds(self, x: int, y: int) -> bool:
        """
        Check if position is in map bounds.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if in bounds, False otherwise
        """
        try:
            return self.context.in_bounds(int(x), int(y))
        except Exception as e:
            logger.error(f"Error checking bounds: {e}")
            return False

    # Game state methods

    def _add_message(self, message: str) -> None:
        """
        Add message to game log.

        Args:
            message: Message text to add
        """
        try:
            self.context.add_message(str(message))
        except Exception as e:
            logger.error(f"Error adding message: {e}")

    def _get_turn_count(self) -> int:
        """
        Get current turn number.

        Returns:
            Current turn count
        """
        try:
            return self.context.get_turn_count()
        except Exception as e:
            logger.error(f"Error getting turn count: {e}")
            return 0

    def _get_floor(self) -> int:
        """
        Get current floor number.

        Returns:
            Current floor number
        """
        try:
            return self.context.get_floor()
        except Exception as e:
            logger.error(f"Error getting floor: {e}")
            return 1

    # Entity manipulation methods

    def _modify_stat(self, entity_id: str, stat_name: str, delta: float) -> bool:
        """
        Modify an entity's stat by a delta.

        Args:
            entity_id: Entity ID
            stat_name: Stat name (e.g., "hp", "mana", "attack")
            delta: Amount to add (can be negative)

        Returns:
            True if successful, False otherwise
        """
        try:
            entity = self.context.get_entity(entity_id)
            if entity is None:
                logger.warning(f"Entity not found: {entity_id}")
                return False

            # Handle core stats
            if stat_name == "hp":
                entity.hp = max(0, min(entity.max_hp, entity.hp + int(delta)))
                if entity.hp == 0:
                    entity.is_alive = False
            elif stat_name == "max_hp":
                entity.max_hp = max(1, entity.max_hp + int(delta))
            elif stat_name == "attack":
                entity.attack = max(0, entity.attack + int(delta))
            elif stat_name == "defense":
                entity.defense = max(0, entity.defense + int(delta))
            else:
                # Handle custom stats
                current = entity.stats.get(stat_name, 0)
                entity.stats[stat_name] = current + delta

            logger.debug(f"Modified {entity_id}.{stat_name} by {delta}")
            return True
        except Exception as e:
            logger.error(f"Error modifying stat: {e}")
            return False

    def _deal_damage(self, entity_id: str, amount: int) -> int:
        """
        Deal damage to an entity.

        Args:
            entity_id: Entity ID
            amount: Damage amount

        Returns:
            Actual damage dealt
        """
        try:
            entity = self.context.get_entity(entity_id)
            if entity is None:
                logger.warning(f"Entity not found: {entity_id}")
                return 0

            actual_damage = entity.take_damage(int(amount))
            logger.debug(f"Dealt {actual_damage} damage to {entity_id}")
            return actual_damage
        except Exception as e:
            logger.error(f"Error dealing damage: {e}")
            return 0

    def _heal(self, entity_id: str, amount: int) -> int:
        """
        Heal an entity.

        Args:
            entity_id: Entity ID
            amount: Healing amount

        Returns:
            Actual amount healed
        """
        try:
            entity = self.context.get_entity(entity_id)
            if entity is None:
                logger.warning(f"Entity not found: {entity_id}")
                return 0

            old_hp = entity.hp
            entity.hp = min(entity.max_hp, entity.hp + int(amount))
            actual_heal = entity.hp - old_hp

            logger.debug(f"Healed {entity_id} for {actual_heal}")
            return actual_heal
        except Exception as e:
            logger.error(f"Error healing: {e}")
            return 0

    def _is_alive(self, entity_id: str) -> bool:
        """
        Check if entity is alive.

        Args:
            entity_id: Entity ID

        Returns:
            True if alive, False otherwise
        """
        try:
            entity = self.context.get_entity(entity_id)
            return entity.is_alive if entity else False
        except Exception as e:
            logger.error(f"Error checking if alive: {e}")
            return False

    # AI-specific methods

    def _ai_get_target(self, monster_id: str) -> Optional[Dict[str, Any]]:
        """
        Get monster's current target (usually the player).

        Args:
            monster_id: Monster entity ID

        Returns:
            Target entity as Lua table, or None if no target
        """
        try:
            # For now, AI monsters always target the player
            # Future: Could support custom target tracking
            player = self.context.get_player()
            return self._entity_to_lua(player)
        except Exception as e:
            logger.error(f"Error getting AI target: {e}")
            return None

    def _ai_is_adjacent(self, monster_id: str, target_id: str) -> bool:
        """
        Check if monster is adjacent to target.

        Args:
            monster_id: Monster entity ID
            target_id: Target entity ID

        Returns:
            True if adjacent (within 1 tile), False otherwise
        """
        try:
            monster = self.context.get_entity(monster_id)
            target = self.context.get_entity(target_id)

            if not monster or not target:
                return False

            dx = abs(monster.x - target.x)
            dy = abs(monster.y - target.y)

            # Adjacent means within 1 tile (including diagonals)
            return dx <= 1 and dy <= 1 and (dx + dy) > 0
        except Exception as e:
            logger.error(f"Error checking adjacency: {e}")
            return False

    def _ai_distance_to(self, monster_id: str, target_id: str) -> int:
        """
        Calculate Manhattan distance between monster and target.

        Args:
            monster_id: Monster entity ID
            target_id: Target entity ID

        Returns:
            Manhattan distance (|dx| + |dy|), or 999 if error
        """
        try:
            monster = self.context.get_entity(monster_id)
            target = self.context.get_entity(target_id)

            if not monster or not target:
                return 999

            return abs(monster.x - target.x) + abs(monster.y - target.y)
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return 999

    def _ai_get_config(self, ai_type: str) -> Dict[str, Any]:
        """
        Get AI behavior configuration from YAML.

        Args:
            ai_type: AI behavior type name

        Returns:
            Configuration dict for the AI type
        """
        try:
            config = self.context.config.get_ai_behavior_config(ai_type)
            # Convert to Lua table
            lua_config = self.lua.table()
            for key, value in config.items():
                lua_config[key] = value
            return lua_config
        except Exception as e:
            logger.error(f"Error getting AI config: {e}")
            return self.lua.table()  # Empty table

    def _ai_attack(self, monster_id: str, target_id: str) -> Dict[str, Any]:
        """
        Create attack action descriptor.

        Args:
            monster_id: Monster entity ID
            target_id: Target entity ID

        Returns:
            Action descriptor: {action = "attack", target_id = ...}
        """
        return {
            "action": "attack",
            "target_id": target_id
        }

    def _ai_move_towards(self, monster_id: str, target_id: str) -> Dict[str, Any]:
        """
        Create move-towards action descriptor.

        Args:
            monster_id: Monster entity ID
            target_id: Target entity ID

        Returns:
            Action descriptor: {action = "move_towards", target_id = ...}
        """
        return {
            "action": "move_towards",
            "target_id": target_id
        }

    def _ai_flee_from(self, monster_id: str, target_id: str) -> Dict[str, Any]:
        """
        Create flee action descriptor.

        Args:
            monster_id: Monster entity ID
            target_id: Target entity ID

        Returns:
            Action descriptor: {action = "flee_from", target_id = ...}
        """
        return {
            "action": "flee_from",
            "target_id": target_id
        }

    def _ai_wander(self, monster_id: str) -> Dict[str, str]:
        """
        Create wander action descriptor.

        Args:
            monster_id: Monster entity ID

        Returns:
            Action descriptor: {action = "wander"}
        """
        return {"action": "wander"}

    def _ai_idle(self, monster_id: str) -> Dict[str, str]:
        """
        Create idle action descriptor.

        Args:
            monster_id: Monster entity ID

        Returns:
            Action descriptor: {action = "idle"}
        """
        return {"action": "idle"}

    # Event system methods (Phase 3)

    def _event_subscribe(
        self,
        event_type: str,
        script_path: str,
        handler_function: Optional[str] = None
    ) -> bool:
        """
        Subscribe Lua script to event type.

        Called from Lua as: brogue.event.subscribe("entity_died", "scripts/events/achievements.lua")

        Args:
            event_type: Event type name (e.g., "entity_died")
            script_path: Path to Lua script containing handler
            handler_function: Handler function name (default: "on_<event_type>")

        Returns:
            True if successfully subscribed, False otherwise
        """
        if self.event_bus is None or self.lua_event_registry is None:
            logger.error(
                "Event subscription not available - EventBus or Registry not initialized"
            )
            return False

        try:
            # Import here to avoid circular dependency
            from ..events import GameEventType

            # Convert event type string to enum
            try:
                event_enum = GameEventType(event_type)
            except ValueError:
                logger.error(f"Invalid event type: {event_type}")
                return False

            # Default handler function name
            if handler_function is None:
                handler_function = f"on_{event_type}"

            # Register handler
            success = self.lua_event_registry.register(
                event_enum,
                script_path,
                handler_function
            )

            if success:
                logger.info(
                    f"Lua event subscription: {script_path}::{handler_function} → {event_type}"
                )
            else:
                logger.warning(
                    f"Failed to subscribe: {script_path}::{handler_function} → {event_type}"
                )

            return success

        except Exception as e:
            logger.error(f"Error subscribing to event: {e}", exc_info=True)
            return False

    def _event_unsubscribe(self, event_type: str, script_path: str) -> bool:
        """
        Unsubscribe Lua script from event type.

        Called from Lua as: brogue.event.unsubscribe("entity_died", "scripts/events/achievements.lua")

        Args:
            event_type: Event type name
            script_path: Path to script to unsubscribe

        Returns:
            True if successfully unsubscribed, False otherwise
        """
        if self.event_bus is None or self.lua_event_registry is None:
            logger.error(
                "Event unsubscription not available - EventBus or Registry not initialized"
            )
            return False

        try:
            from ..events import GameEventType

            # Convert event type string to enum
            try:
                event_enum = GameEventType(event_type)
            except ValueError:
                logger.error(f"Invalid event type: {event_type}")
                return False

            # Unregister handler
            success = self.lua_event_registry.unregister(event_enum, script_path)

            if success:
                logger.info(f"Unsubscribed: {script_path} from {event_type}")
            else:
                logger.warning(f"Failed to unsubscribe: {script_path} from {event_type}")

            return success

        except Exception as e:
            logger.error(f"Error unsubscribing from event: {e}", exc_info=True)
            return False

    def _event_get_types(self) -> List[str]:
        """
        Get list of all available event types.

        Called from Lua as: local types = brogue.event.get_types()

        Returns:
            Lua table (1-indexed) of event type strings
        """
        try:
            from ..events import GameEventType

            # Get all event type values
            event_types = [event_type.value for event_type in GameEventType]

            # Convert to Lua table (1-indexed)
            lua_table = self.lua.table()
            for i, event_type in enumerate(event_types, 1):
                lua_table[i] = event_type

            return lua_table

        except Exception as e:
            logger.error(f"Error getting event types: {e}", exc_info=True)
            return self.lua.table()  # Empty table

    def _event_emit(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Manually emit an event (for testing/debugging).

        Called from Lua as: brogue.event.emit("entity_died", {entity_id = "goblin_1"})

        Args:
            event_type: Event type name
            data: Event data dictionary

        Returns:
            True if successfully emitted, False otherwise
        """
        if self.event_bus is None:
            logger.error("Event emission not available - EventBus not initialized")
            return False

        try:
            from ..events import GameEvent, GameEventType

            # Convert event type string to enum
            try:
                event_enum = GameEventType(event_type)
            except ValueError:
                logger.error(f"Invalid event type: {event_type}")
                return False

            # Convert Lua table to Python dict if needed
            if hasattr(data, 'items'):
                # Already a dict or dict-like
                event_data = dict(data)
            else:
                event_data = {}

            # Create and publish event
            event = GameEvent(
                event_type=event_enum,
                data=event_data,
                turn=self.context.get_turn_count()
            )

            self.event_bus.publish(event)
            logger.debug(f"Manually emitted event: {event_type}")
            return True

        except Exception as e:
            logger.error(f"Error emitting event: {e}", exc_info=True)
            return False
