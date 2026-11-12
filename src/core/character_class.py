"""
Character Class System

Defines character classes with starting stats, abilities, and progression.

Usage:
    from src.core.character_class import CharacterClass, create_player_from_class

    # Create warrior player
    player = create_player_from_class(
        CharacterClass.WARRIOR,
        x=10, y=10,
        name="Alice"
    )
"""

from dataclasses import dataclass
from typing import Dict, List, TYPE_CHECKING
from enum import Enum

from .exceptions import DataError

if TYPE_CHECKING:
    from .base.entity import Entity


class CharacterClass(Enum):
    """
    Available character classes.

    Each class has unique starting stats, abilities, and progression.
    """
    WARRIOR = "warrior"
    ROGUE = "rogue"
    MAGE = "mage"
    HEALER = "healer"

    @classmethod
    def from_string(cls, value: str) -> 'CharacterClass':
        """
        Get class from string (case-insensitive).

        Args:
            value: Class name string

        Returns:
            CharacterClass enum

        Raises:
            ValueError: If class name is invalid

        Example:
            >>> CharacterClass.from_string("warrior")
            CharacterClass.WARRIOR
        """
        value_lower = value.lower()
        for class_type in cls:
            if class_type.value == value_lower:
                return class_type
        raise DataError(
            f"Invalid character class: {value}",
            value=value,
            available_classes=[c.value for c in cls]
        )


@dataclass
class ClassTemplate:
    """
    Character class template with starting stats and items.

    Defines the initial state and progression for each class.

    Attributes:
        name: Display name
        description: Class description
        hp: Starting HP
        attack: Starting attack
        defense: Starting defense
        starting_items: items.yaml IDs given (and equipped) at game start
        hp_per_level: Average HP gained per level (rolled; see Player._level_up)
        attack_per_level: Attack gained per level
        defense_per_level: Defense gained per level
        abilities: Implemented class abilities (force_bolt, heal, backstab)
    """

    name: str
    description: str

    # Starting stats
    hp: int
    attack: int
    defense: int

    # Starting items (equipped on creation)
    starting_items: List[str]

    # Class-specific progression
    hp_per_level: int
    attack_per_level: int
    defense_per_level: int

    # Special abilities
    abilities: List[str]


# Class definitions
#
# Growth is NetHack-shaped: levels give HP and +1 attack (accuracy and damage),
# never defense -- protection comes from crafted armor. With the doubling XP
# curve, levels 2-5 arrive within the first few floors, so larger per-level
# gains compound fast: +2 attack/level made a level-3 warrior beat a troll
# 100% of the time, and +2 defense/level made a level-7 healer unhittable.
# Measure changes with scripts/sim_duels.py --level N.
#
# Starting gear is stat-neutral: `attack`/`defense` are the base stats and the
# equipped starting items add the rest, so totals match the pre-equipment
# balance. `abilities` lists only what is implemented (see AbilityAction and
# AttackAction); fireball, teleport, dodge, protect, regeneration and
# power_strike are still unbuilt (VB-53).
CLASS_TEMPLATES: Dict[CharacterClass, ClassTemplate] = {
    CharacterClass.WARRIOR: ClassTemplate(
        name="Warrior",
        description="Strong melee fighter with high HP and attack",
        hp=30,
        attack=2,   # + short sword (+3) = 5
        defense=1,  # + leather armor (+2) = 3
        starting_items=["short_sword", "leather_armor"],
        hp_per_level=5,
        attack_per_level=1,
        defense_per_level=0,
        abilities=[],
    ),

    CharacterClass.ROGUE: ClassTemplate(
        name="Rogue",
        description="Agile explorer with high speed and critical hits",
        hp=20,
        attack=2,  # + dagger (+2) = 4
        defense=2,
        starting_items=["dagger"],
        hp_per_level=3,
        attack_per_level=1,
        defense_per_level=0,
        abilities=["backstab"],
    ),

    CharacterClass.MAGE: ClassTemplate(
        name="Mage",
        description="Arcane spellcaster with low HP but powerful magic",
        hp=15,
        attack=3,  # weak in melee; force bolt is the real attack
        defense=1,
        starting_items=[],
        hp_per_level=3,
        attack_per_level=1,
        defense_per_level=0,
        abilities=["force_bolt"],
    ),

    CharacterClass.HEALER: ClassTemplate(
        name="Healer",
        description="Support specialist with high defense and sustainability",
        hp=25,
        attack=3,
        defense=4,
        starting_items=[],
        hp_per_level=4,
        attack_per_level=1,
        defense_per_level=0,
        abilities=["heal"],
    ),
}


def get_class_template(class_type: CharacterClass) -> ClassTemplate:
    """
    Get class template by type.

    Args:
        class_type: Character class enum

    Returns:
        ClassTemplate for the class

    Example:
        >>> template = get_class_template(CharacterClass.WARRIOR)
        >>> template.hp
        30
    """
    return CLASS_TEMPLATES[class_type]


def create_player_from_class(
    class_type: CharacterClass,
    x: int,
    y: int,
    name: str = "Anonymous"
) -> 'Entity':
    """
    Create player entity with class template.

    Args:
        class_type: Character class
        x: Starting X position
        y: Starting Y position
        name: Player name (default: "Anonymous")

    Returns:
        Player Entity with class stats

    Example:
        >>> player = create_player_from_class(
        ...     CharacterClass.WARRIOR,
        ...     x=10, y=10,
        ...     name="Alice"
        ... )
        >>> player.max_hp
        30
    """
    from .entities import Player

    template = get_class_template(class_type)

    # Create Player entity (not base Entity) with class stats
    player = Player(
        name=name,
        x=x,
        y=y,
        hp=template.hp,
        max_hp=template.hp,
        attack=template.attack,
        defense=template.defense,
    )

    # Store class information and display data in stats
    player.stats['class'] = template.name
    player.stats['class_type'] = class_type.value
    player.stats['description'] = template.description
    player.stats['char'] = '@'
    player.stats['blocks_movement'] = True
    player.stats['blocks_light'] = False

    # Per-level growth, read by Player.gain_xp on level-up
    player.stats['hp_per_level'] = template.hp_per_level
    player.stats['attack_per_level'] = template.attack_per_level
    player.stats['defense_per_level'] = template.defense_per_level

    # Class abilities are read from stats by AbilityAction / AttackAction
    player.stats['abilities'] = list(template.abilities)

    # Starting gear: equipped straight away, not carried
    from .loot import LootGenerator
    loot = LootGenerator.get_instance()
    for item_id in template.starting_items:
        item = loot.create_item(item_id)
        if item is None:
            raise DataError(f"Unknown starting item: {item_id}", value=item_id)
        if item.get_stat('item_type') == 'weapon':
            player.equipped_weapon = item
        else:
            player.equipped_armor = item

    return player


def starting_attack_defense(template: ClassTemplate) -> tuple:
    """Attack and defense a new character of this class actually has,
    including the bonuses of the starting gear it is wearing."""
    from .loot import LootGenerator
    loot = LootGenerator.get_instance()
    attack, defense = template.attack, template.defense
    for item_id in template.starting_items:
        stats = (loot.get_item_info(item_id) or {}).get('stats', {})
        attack += stats.get('attack_bonus', 0)
        defense += stats.get('defense_bonus', 0)
    return attack, defense


def format_class_selection() -> str:
    """
    Format character class selection menu.

    Returns:
        Formatted class selection text

    Example:
        >>> print(format_class_selection())
        1. Warrior - Strong melee fighter
           HP: 30  Attack: 5  Defense: 3
           ...
    """
    lines = []
    lines.append("╔" + "=" * 66 + "╗")
    lines.append("║" + " " * 20 + "CHOOSE YOUR CLASS" + " " * 28 + "║")
    lines.append("╚" + "=" * 66 + "╝")
    lines.append("")

    for i, (class_type, template) in enumerate(CLASS_TEMPLATES.items(), start=1):
        lines.append(f"{i}. {template.name} - {template.description}")
        attack, defense = starting_attack_defense(template)
        lines.append(
            f"   HP: {template.hp}  "
            f"Attack: {attack}  "
            f"Defense: {defense}"
        )
        lines.append(f"   Abilities: {', '.join(template.abilities) or 'none yet'}")
        lines.append("")

    return "\n".join(lines)


def get_class_from_choice(choice: int) -> CharacterClass:
    """
    Get CharacterClass from numeric choice (1-4).

    Args:
        choice: User choice (1=Warrior, 2=Rogue, 3=Mage, 4=Healer)

    Returns:
        CharacterClass enum

    Raises:
        ValueError: If choice is out of range

    Example:
        >>> get_class_from_choice(1)
        CharacterClass.WARRIOR
    """
    class_list = list(CharacterClass)
    if 1 <= choice <= len(class_list):
        return class_list[choice - 1]
    raise DataError(
        f"Invalid class choice: {choice} (must be 1-{len(class_list)})",
        choice=choice,
        valid_range=(1, len(class_list))
    )
