"""
Entity base class - unified base for all game objects.

Provides:
- Unique ID for each entity (critical for multiplayer)
- Common stats and position
- Serialization support (save/load)
- Uniform API for Lua integration (future)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class EntityType(Enum):
    """Types of entities in the game."""
    PLAYER = "player"
    MONSTER = "monster"
    ITEM = "item"
    ORE_VEIN = "ore_vein"
    FORGE = "forge"
    NPC = "npc"


@dataclass
class Entity:
    """
    Base class for all game entities.

    Design principles:
    - Unique ID for multiplayer sync
    - Position for spatial entities (None for inventory items)
    - Stats dictionary for flexible attributes
    - Type for polymorphism

    Operational excellence:
    - Small, focused methods (< 20 lines each)
    - Single responsibility (entity state management)
    - Clear error handling
    """

    # Identity
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType = EntityType.PLAYER
    name: str = "Unknown"

    # Spatial (None if not in world, e.g., inventory items)
    x: Optional[int] = None
    y: Optional[int] = None

    # Core stats (all entities have these, but many are 0)
    hp: int = 0
    max_hp: int = 0
    attack: int = 0
    defense: int = 0

    # Flexible attributes (different entities need different things)
    stats: Dict[str, Any] = field(default_factory=dict)

    # State flags
    is_alive: bool = True
    is_active: bool = True
    attackable: bool = False  # Can this entity be attacked in combat?
    blocks_movement: bool = False  # Does this entity block movement?

    # Content reference (for YAML-loaded entities)
    content_id: Optional[str] = None

    def take_damage(self, amount: int) -> int:
        """
        Apply damage to this entity.

        Args:
            amount: Damage amount to apply

        Returns:
            Actual damage taken (for combat log)
        """
        if self.hp <= 0:
            return 0

        # Clamp damage to available HP (can't take more damage than HP remaining)
        actual_damage = min(max(0, amount), self.hp)
        self.hp -= actual_damage

        if self.hp == 0:
            self.is_alive = False

        return actual_damage

    def heal(self, amount: int) -> int:
        """
        Heal this entity.

        Args:
            amount: Healing amount

        Returns:
            Actual healing done
        """
        if not self.is_alive or self.hp >= self.max_hp:
            return 0

        actual_healing = min(amount, self.max_hp - self.hp)
        self.hp += actual_healing
        return actual_healing

    def move_to(self, x: int, y: int) -> None:
        """Move entity to absolute position."""
        self.x = x
        self.y = y

    def move_by(self, dx: int, dy: int) -> None:
        """Move entity by offset."""
        if self.x is not None and self.y is not None:
            self.x += dx
            self.y += dy

    def distance_to(self, other: 'Entity') -> float:
        """Calculate distance to another entity."""
        if self.x is None or other.x is None:
            return float('inf')

        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5

    def is_adjacent(self, other: 'Entity') -> bool:
        """Check if adjacent to another entity (8-directional)."""
        if self.x is None or other.x is None:
            return False

        return abs(self.x - other.x) <= 1 and abs(self.y - other.y) <= 1

    def get_stat(self, stat_name: str, default: Any = 0) -> Any:
        """Get a stat value with fallback."""
        return self.stats.get(stat_name, default)

    def set_stat(self, stat_name: str, value: Any) -> None:
        """Set a stat value."""
        self.stats[stat_name] = value

    def to_dict(self) -> dict:
        """Serialize to dictionary (for save/load, multiplayer)."""
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type.value,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'attack': self.attack,
            'defense': self.defense,
            'stats': self.stats.copy(),
            'is_alive': self.is_alive,
            'is_active': self.is_active,
            'content_id': self.content_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Entity':
        """Deserialize from dictionary."""
        return cls(
            entity_id=data['entity_id'],
            entity_type=EntityType(data['entity_type']),
            name=data['name'],
            x=data.get('x'),
            y=data.get('y'),
            hp=data['hp'],
            max_hp=data['max_hp'],
            attack=data['attack'],
            defense=data['defense'],
            stats=data.get('stats', {}).copy(),
            is_alive=data['is_alive'],
            is_active=data['is_active'],
            content_id=data.get('content_id'),
        )
