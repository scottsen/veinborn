"""
Core game entities - Player, Monster, OreVein.

All inherit from Entity base class for:
- Code reuse (take_damage, heal, distance_to)
- Uniform API (future Lua integration)
- Easy serialization (save/load, multiplayer)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .base.entity import Entity, EntityType
from .rng import GameRNG
from .constants import (
    GOBLIN_HP, GOBLIN_ATTACK, GOBLIN_DEFENSE, GOBLIN_XP_REWARD,
    ORC_HP, ORC_ATTACK, ORC_DEFENSE, ORC_XP_REWARD,
    TROLL_HP, TROLL_ATTACK, TROLL_DEFENSE, TROLL_XP_REWARD,
    MINING_MIN_TURNS, MINING_MAX_TURNS,
)


class AIState(Enum):
    """
    AI state machine states for monsters.

    Note: Currently not used by AISystem (MVP uses simple aggressive AI).
    These states are defined for future state machine implementation.
    """
    IDLE = "idle"
    CHASING = "chasing"
    WANDERING = "wandering"
    FLEEING = "fleeing"


@dataclass
class Player(Entity):
    """
    Player character.

    Extends Entity with player-specific features:
    - Inventory management
    - Experience/leveling
    - Class-specific abilities

    Uses dataclass for clean constructor. All fields have sensible defaults.
    """

    # Override entity defaults for Player
    entity_type: EntityType = EntityType.PLAYER
    name: str = "Player"
    hp: int = 20
    max_hp: int = 20
    attack: int = 5
    defense: int = 2
    attackable: bool = True  # Players can be attacked in combat

    def __post_init__(self):
        """Initialize player-specific attributes."""
        # Player-specific attributes
        self.inventory: List[Entity] = []
        self.equipped_weapon: Optional[Entity] = None
        self.equipped_armor: Optional[Entity] = None
        self.set_stat('xp', 0)
        self.set_stat('level', 1)

    def add_to_inventory(self, item: Entity) -> bool:
        """
        Add item to inventory.

        Returns:
            True if added successfully
        """
        if len(self.inventory) >= 20:  # Max inventory size
            return False

        self.inventory.append(item)
        # Remove from world
        item.x = None
        item.y = None
        return True

    def remove_from_inventory(self, item: Entity) -> bool:
        """Remove item from inventory."""
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False

    def gain_xp(self, amount: int) -> bool:
        """
        Gain experience points.

        Returns:
            True if leveled up
        """
        current_xp = self.get_stat('xp', 0)
        current_level = self.get_stat('level', 1)

        self.set_stat('xp', current_xp + amount)

        # Check for level up (100 XP per level)
        xp_for_next_level = current_level * 100
        if current_xp + amount >= xp_for_next_level:
            self.set_stat('level', current_level + 1)
            # Increase stats on level up
            self.max_hp += 5
            self.hp = self.max_hp
            self.attack += 1
            self.defense += 1
            return True

        return False

    def get_total_attack(self) -> int:
        """
        Get total attack including weapon bonus.

        Returns:
            Base attack + weapon attack bonus (if equipped)
        """
        total = self.attack
        if self.equipped_weapon:
            weapon_bonus = self.equipped_weapon.get_stat('attack_bonus', 0)
            total += weapon_bonus
        return total

    def get_total_defense(self) -> int:
        """
        Get total defense including armor bonus.

        Returns:
            Base defense + armor defense bonus (if equipped)
        """
        total = self.defense
        if self.equipped_armor:
            armor_bonus = self.equipped_armor.get_stat('defense_bonus', 0)
            total += armor_bonus
        return total


@dataclass
class Monster(Entity):
    """
    Monster entity.

    Extends Entity with monster-specific features:
    - AI behavior type
    - Loot table
    - XP reward

    Uses dataclass for clean constructor with all Entity fields having defaults.
    Override entity_type to MONSTER and add monster-specific fields.
    """

    # Override entity_type default
    entity_type: EntityType = EntityType.MONSTER
    attackable: bool = True  # Monsters can be attacked in combat

    # Monster-specific fields
    xp_reward: int = 10
    ai_type: str = 'aggressive'

    def __post_init__(self):
        """Store monster-specific fields in stats dict for compatibility."""
        self.set_stat('xp_reward', self.xp_reward)
        self.set_stat('ai_type', self.ai_type)

    # DEPRECATED (Phase 3): Use EntityLoader.create_monster() instead
    # These factory methods are kept for backward compatibility only.
    # They will be removed in Phase 4.

    @classmethod
    def create_goblin(cls, x: int, y: int) -> 'Monster':
        """
        DEPRECATED: Use EntityLoader.create_monster('goblin', x, y) instead.

        Factory method for goblin (uses constants).
        """
        return cls(
            name="Goblin",
            x=x,
            y=y,
            hp=GOBLIN_HP,
            max_hp=GOBLIN_HP,
            attack=GOBLIN_ATTACK,
            defense=GOBLIN_DEFENSE,
            xp_reward=GOBLIN_XP_REWARD,
            content_id="goblin",
        )

    @classmethod
    def create_orc(cls, x: int, y: int) -> 'Monster':
        """
        DEPRECATED: Use EntityLoader.create_monster('orc', x, y) instead.

        Factory method for orc (uses constants).
        """
        return cls(
            name="Orc",
            x=x,
            y=y,
            hp=ORC_HP,
            max_hp=ORC_HP,
            attack=ORC_ATTACK,
            defense=ORC_DEFENSE,
            xp_reward=ORC_XP_REWARD,
            content_id="orc",
        )

    @classmethod
    def create_troll(cls, x: int, y: int) -> 'Monster':
        """
        DEPRECATED: Use EntityLoader.create_monster('troll', x, y) instead.

        Factory method for troll (uses constants).
        """
        return cls(
            name="Troll",
            x=x,
            y=y,
            hp=TROLL_HP,
            max_hp=TROLL_HP,
            attack=TROLL_ATTACK,
            defense=TROLL_DEFENSE,
            xp_reward=TROLL_XP_REWARD,
            content_id="troll",
        )


@dataclass
class OreVein(Entity):
    """
    Ore vein that can be mined.

    Represents the core mining mechanic - ore veins have 5 properties
    that determine the quality of crafted items.

    Properties (0-100 scale):
    - Hardness: Weapon damage / Armor defense
    - Conductivity: Magic power / Spell efficiency
    - Malleability: Durability / Repair ease
    - Purity: Quality multiplier (affects all stats)
    - Density: Weight / Encumbrance

    Uses dataclass for clean constructor with reduced parameter count.
    """

    # Override entity_type default
    entity_type: EntityType = EntityType.ORE_VEIN
    blocks_movement: bool = True  # Ore veins are embedded in walls and block movement

    # Ore-specific fields
    ore_type: str = "copper"
    hardness: int = 50
    conductivity: int = 50
    malleability: int = 50
    purity: int = 50
    density: int = 50

    def __post_init__(self):
        """Initialize ore vein properties and calculate mining time."""
        # Set name and content_id based on ore_type
        object.__setattr__(self, 'name', f"{self.ore_type.title()} Ore Vein")
        object.__setattr__(self, 'content_id', self.ore_type)

        # Calculate mining time based on hardness
        turns_range = MINING_MAX_TURNS - MINING_MIN_TURNS
        mining_turns = MINING_MIN_TURNS + (self.hardness * turns_range // 100)

        # Store ore properties in stats dict
        self.set_stat('ore_type', self.ore_type)
        self.set_stat('hardness', self.hardness)
        self.set_stat('conductivity', self.conductivity)
        self.set_stat('malleability', self.malleability)
        self.set_stat('purity', self.purity)
        self.set_stat('density', self.density)
        self.set_stat('mining_turns', mining_turns)
        self.set_stat('surveyed', False)

    @property
    def average_quality(self) -> int:
        """Calculate average quality of all properties."""
        props = [
            self.get_stat('hardness'),
            self.get_stat('conductivity'),
            self.get_stat('malleability'),
            self.get_stat('purity'),
            self.get_stat('density'),
        ]
        return sum(props) // len(props)

    # DEPRECATED (Phase 3): Use EntityLoader.create_ore_vein() instead
    # This method is kept for backward compatibility only.
    # It will be removed in Phase 4.

    @classmethod
    def generate_random(
        cls,
        ore_type: str,
        x: int,
        y: int,
        floor: int = 1,
    ) -> 'OreVein':
        """
        DEPRECATED: Use EntityLoader.create_ore_vein(ore_type, x, y, floor) instead.

        Generate ore vein with random properties based on floor.

        Ore tiers:
        - Copper (Floors 1-3): Properties 20-50
        - Iron (Floors 4-6): Properties 40-70
        - Mithril (Floors 7-9): Properties 60-90
        - Adamantite (Floor 10+): Properties 80-100

        5% chance for "jackpot" (2-3 tiers above normal, 80-100 stats)
        """
        # Determine property range based on ore type
        if ore_type == "copper":
            min_prop, max_prop = 20, 50
        elif ore_type == "iron":
            min_prop, max_prop = 40, 70
        elif ore_type == "mithril":
            min_prop, max_prop = 60, 90
        elif ore_type == "adamantite":
            min_prop, max_prop = 80, 100
        else:
            min_prop, max_prop = 20, 50  # Default to copper

        # 5% chance for jackpot (all properties 80-100)
        rng = GameRNG.get_instance()
        if rng.random() < 0.05:
            min_prop, max_prop = 80, 100

        # Generate properties
        hardness = rng.randint(min_prop, max_prop)
        conductivity = rng.randint(min_prop, max_prop)
        malleability = rng.randint(min_prop, max_prop)
        purity = rng.randint(min_prop, max_prop)
        density = rng.randint(min_prop, max_prop)

        return cls(
            ore_type=ore_type,
            x=x,
            y=y,
            hardness=hardness,
            conductivity=conductivity,
            malleability=malleability,
            purity=purity,
            density=density,
        )

    def get_ore_item(self) -> Entity:
        """
        Convert ore vein to inventory item after mining.

        Returns:
            Entity representing the mined ore (for inventory)
        """
        ore_item = Entity(
            entity_type=EntityType.ITEM,
            name=f"{self.ore_type.title()} Ore",
            content_id=f"{self.ore_type}_ore",
            stats=self.stats.copy(),
        )
        return ore_item


@dataclass
class Forge(Entity):
    """
    Forge for crafting equipment from ore.

    Represents the crafting station where players turn mined ore into gear.
    Core part of Brogue's unique hook: mining → crafting → equipment.

    Forge Types:
    - basic_forge: Can craft copper items (floors 1-3)
    - iron_forge: Can craft copper + iron items (floors 4-6)
    - master_forge: Can craft all items (floors 7+)
    """

    # Override entity_type default
    entity_type: EntityType = EntityType.FORGE
    blocks_movement: bool = True  # Forges are large stationary objects that block movement

    # Forge-specific fields
    forge_type: str = "basic_forge"

    def __post_init__(self):
        """Initialize forge properties."""
        # Set name based on forge type
        forge_names = {
            'basic_forge': 'Basic Forge',
            'iron_forge': 'Iron Forge',
            'master_forge': 'Master Forge',
        }
        object.__setattr__(self, 'name', forge_names.get(self.forge_type, 'Forge'))
        object.__setattr__(self, 'content_id', self.forge_type)

        # Store forge type in stats
        self.set_stat('forge_type', self.forge_type)
        self.set_stat('interactable', True)
