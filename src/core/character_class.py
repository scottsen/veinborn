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
        starting_items: List of starting item IDs (future)
        hp_per_level: HP gained per level (future)
        attack_per_level: Attack gained per level (future)
        defense_per_level: Defense gained per level (future)
        abilities: List of class abilities (future)
    """

    name: str
    description: str

    # Starting stats
    hp: int
    attack: int
    defense: int

    # Starting items (future feature)
    starting_items: List[str]

    # Class-specific progression (future feature)
    hp_per_level: int
    attack_per_level: int
    defense_per_level: int

    # Special abilities (future feature)
    abilities: List[str]


# Class definitions
CLASS_TEMPLATES: Dict[CharacterClass, ClassTemplate] = {
    CharacterClass.WARRIOR: ClassTemplate(
        name="Warrior",
        description="Strong melee fighter with high HP and attack",
        hp=30,
        attack=5,
        defense=3,
        starting_items=["iron_sword", "leather_armor"],
        hp_per_level=5,
        attack_per_level=2,
        defense_per_level=1,
        abilities=["power_strike"],
    ),

    CharacterClass.ROGUE: ClassTemplate(
        name="Rogue",
        description="Agile explorer with high speed and critical hits",
        hp=20,
        attack=4,
        defense=2,
        starting_items=["dagger", "lockpick"],
        hp_per_level=3,
        attack_per_level=1,
        defense_per_level=1,
        abilities=["backstab", "dodge"],
    ),

    CharacterClass.MAGE: ClassTemplate(
        name="Mage",
        description="Arcane spellcaster with low HP but powerful magic",
        hp=15,
        attack=2,
        defense=1,
        starting_items=["wand", "spellbook"],
        hp_per_level=2,
        attack_per_level=1,
        defense_per_level=0,
        abilities=["fireball", "teleport"],
    ),

    CharacterClass.HEALER: ClassTemplate(
        name="Healer",
        description="Support specialist with high defense and sustainability",
        hp=25,
        attack=3,
        defense=4,
        starting_items=["healing_staff", "bandages"],
        hp_per_level=4,
        attack_per_level=1,
        defense_per_level=2,
        abilities=["heal", "protect", "regeneration"],
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

    # Future: Add starting items
    # for item_id in template.starting_items:
    #     item = create_item(item_id)
    #     player.add_to_inventory(item)

    # Future: Add class abilities
    # for ability in template.abilities:
    #     player.add_ability(ability)

    return player


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
        lines.append(
            f"   HP: {template.hp}  "
            f"Attack: {template.attack}  "
            f"Defense: {template.defense}"
        )
        lines.append(f"   Abilities: {', '.join(template.abilities)}")
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
