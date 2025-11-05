"""
Tests for Character Class System

Validates:
- CharacterClass enum functionality
- ClassTemplate dataclass
- Class template retrieval
- Player creation from class
- Class selection utilities
"""

import pytest
from src.core.character_class import (
    CharacterClass,
    ClassTemplate,
    CLASS_TEMPLATES,
    get_class_template,
    create_player_from_class,
    format_class_selection,
    get_class_from_choice,
)
from src.core.base.entity import EntityType
from src.core.exceptions import DataError


class TestCharacterClass:
    """Test CharacterClass enum."""

    def test_class_values(self):
        """Should have correct enum values."""
        assert CharacterClass.WARRIOR.value == "warrior"
        assert CharacterClass.ROGUE.value == "rogue"
        assert CharacterClass.MAGE.value == "mage"
        assert CharacterClass.HEALER.value == "healer"

    def test_from_string_valid(self):
        """Should convert string to enum."""
        assert CharacterClass.from_string("warrior") == CharacterClass.WARRIOR
        assert CharacterClass.from_string("rogue") == CharacterClass.ROGUE
        assert CharacterClass.from_string("mage") == CharacterClass.MAGE
        assert CharacterClass.from_string("healer") == CharacterClass.HEALER

    def test_from_string_case_insensitive(self):
        """Should handle different cases."""
        assert CharacterClass.from_string("WARRIOR") == CharacterClass.WARRIOR
        assert CharacterClass.from_string("Rogue") == CharacterClass.ROGUE
        assert CharacterClass.from_string("MaGe") == CharacterClass.MAGE
        assert CharacterClass.from_string("HeAlEr") == CharacterClass.HEALER

    def test_from_string_invalid(self):
        """Should raise DataError for invalid class."""
        with pytest.raises(DataError, match="Invalid character class"):
            CharacterClass.from_string("paladin")

    def test_all_classes_exist(self):
        """Should have exactly 4 classes."""
        assert len(CharacterClass) == 4


class TestClassTemplates:
    """Test CLASS_TEMPLATES definitions."""

    def test_all_templates_defined(self):
        """Each class should have a template."""
        assert CharacterClass.WARRIOR in CLASS_TEMPLATES
        assert CharacterClass.ROGUE in CLASS_TEMPLATES
        assert CharacterClass.MAGE in CLASS_TEMPLATES
        assert CharacterClass.HEALER in CLASS_TEMPLATES
        assert len(CLASS_TEMPLATES) == 4

    def test_warrior_stats(self):
        """Warrior should have high HP and attack."""
        warrior = CLASS_TEMPLATES[CharacterClass.WARRIOR]
        assert warrior.name == "Warrior"
        assert warrior.hp == 30
        assert warrior.attack == 5
        assert warrior.defense == 3
        assert "power_strike" in warrior.abilities

    def test_rogue_stats(self):
        """Rogue should be balanced with dodge."""
        rogue = CLASS_TEMPLATES[CharacterClass.ROGUE]
        assert rogue.name == "Rogue"
        assert rogue.hp == 20
        assert rogue.attack == 4
        assert rogue.defense == 2
        assert "backstab" in rogue.abilities
        assert "dodge" in rogue.abilities

    def test_mage_stats(self):
        """Mage should have low HP but magic abilities."""
        mage = CLASS_TEMPLATES[CharacterClass.MAGE]
        assert mage.name == "Mage"
        assert mage.hp == 15
        assert mage.attack == 2
        assert mage.defense == 1
        assert "fireball" in mage.abilities
        assert "teleport" in mage.abilities

    def test_healer_stats(self):
        """Healer should have high defense and support abilities."""
        healer = CLASS_TEMPLATES[CharacterClass.HEALER]
        assert healer.name == "Healer"
        assert healer.hp == 25
        assert healer.attack == 3
        assert healer.defense == 4
        assert "heal" in healer.abilities
        assert "protect" in healer.abilities
        assert "regeneration" in healer.abilities

    def test_progression_defined(self):
        """All classes should have progression defined."""
        for template in CLASS_TEMPLATES.values():
            assert template.hp_per_level > 0
            assert template.attack_per_level >= 0
            assert template.defense_per_level >= 0

    def test_starting_items_defined(self):
        """All classes should have starting items."""
        for template in CLASS_TEMPLATES.values():
            assert len(template.starting_items) > 0

    def test_abilities_defined(self):
        """All classes should have abilities."""
        for template in CLASS_TEMPLATES.values():
            assert len(template.abilities) > 0


class TestGetClassTemplate:
    """Test get_class_template function."""

    def test_get_warrior_template(self):
        """Should return warrior template."""
        template = get_class_template(CharacterClass.WARRIOR)
        assert isinstance(template, ClassTemplate)
        assert template.name == "Warrior"
        assert template.hp == 30

    def test_get_rogue_template(self):
        """Should return rogue template."""
        template = get_class_template(CharacterClass.ROGUE)
        assert isinstance(template, ClassTemplate)
        assert template.name == "Rogue"
        assert template.hp == 20

    def test_get_mage_template(self):
        """Should return mage template."""
        template = get_class_template(CharacterClass.MAGE)
        assert isinstance(template, ClassTemplate)
        assert template.name == "Mage"
        assert template.hp == 15

    def test_get_healer_template(self):
        """Should return healer template."""
        template = get_class_template(CharacterClass.HEALER)
        assert isinstance(template, ClassTemplate)
        assert template.name == "Healer"
        assert template.hp == 25

    def test_returns_same_instance(self):
        """Should return same template instance."""
        template1 = get_class_template(CharacterClass.WARRIOR)
        template2 = get_class_template(CharacterClass.WARRIOR)
        assert template1 is template2


class TestCreatePlayerFromClass:
    """Test create_player_from_class function."""

    def test_create_warrior(self):
        """Should create warrior with correct stats."""
        player = create_player_from_class(
            CharacterClass.WARRIOR,
            x=10, y=20,
            name="Alice"
        )

        assert player.name == "Alice"
        assert player.entity_type == EntityType.PLAYER
        assert player.x == 10
        assert player.y == 20
        assert player.hp == 30
        assert player.max_hp == 30
        assert player.attack == 5
        assert player.defense == 3
        assert player.stats['class'] == "Warrior"
        assert player.stats['class_type'] == "warrior"

    def test_create_rogue(self):
        """Should create rogue with correct stats."""
        player = create_player_from_class(
            CharacterClass.ROGUE,
            x=5, y=15,
            name="Bob"
        )

        assert player.name == "Bob"
        assert player.hp == 20
        assert player.max_hp == 20
        assert player.attack == 4
        assert player.defense == 2
        assert player.stats['class'] == "Rogue"

    def test_create_mage(self):
        """Should create mage with correct stats."""
        player = create_player_from_class(
            CharacterClass.MAGE,
            x=7, y=13,
            name="Charlie"
        )

        assert player.name == "Charlie"
        assert player.hp == 15
        assert player.max_hp == 15
        assert player.attack == 2
        assert player.defense == 1
        assert player.stats['class'] == "Mage"

    def test_create_healer(self):
        """Should create healer with correct stats."""
        player = create_player_from_class(
            CharacterClass.HEALER,
            x=3, y=8,
            name="Diana"
        )

        assert player.name == "Diana"
        assert player.hp == 25
        assert player.max_hp == 25
        assert player.attack == 3
        assert player.defense == 4
        assert player.stats['class'] == "Healer"

    def test_default_name(self):
        """Should use 'Anonymous' if no name provided."""
        player = create_player_from_class(
            CharacterClass.WARRIOR,
            x=0, y=0
        )

        assert player.name == "Anonymous"

    def test_player_is_entity(self):
        """Should create proper Entity instance."""
        player = create_player_from_class(
            CharacterClass.WARRIOR,
            x=10, y=10,
            name="Test"
        )

        assert player.stats['char'] == '@'
        assert player.stats['blocks_movement'] is True
        assert player.entity_type == EntityType.PLAYER

    def test_class_description_stored(self):
        """Should store class description in entity data."""
        player = create_player_from_class(
            CharacterClass.WARRIOR,
            x=0, y=0
        )

        assert 'description' in player.stats
        assert "melee fighter" in player.stats['description'].lower()


class TestFormatClassSelection:
    """Test format_class_selection function."""

    def test_returns_string(self):
        """Should return formatted string."""
        result = format_class_selection()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_all_classes(self):
        """Should list all four classes."""
        result = format_class_selection()
        assert "Warrior" in result
        assert "Rogue" in result
        assert "Mage" in result
        assert "Healer" in result

    def test_contains_stats(self):
        """Should show HP, Attack, Defense for each class."""
        result = format_class_selection()
        assert "HP:" in result
        assert "Attack:" in result
        assert "Defense:" in result

    def test_contains_abilities(self):
        """Should list abilities for each class."""
        result = format_class_selection()
        assert "Abilities:" in result
        assert "power_strike" in result
        assert "backstab" in result
        assert "fireball" in result

    def test_formatted_with_box(self):
        """Should have nice box formatting."""
        result = format_class_selection()
        assert "╔" in result
        assert "╚" in result
        assert "CHOOSE YOUR CLASS" in result


class TestGetClassFromChoice:
    """Test get_class_from_choice function."""

    def test_choice_1_warrior(self):
        """Choice 1 should return Warrior."""
        assert get_class_from_choice(1) == CharacterClass.WARRIOR

    def test_choice_2_rogue(self):
        """Choice 2 should return Rogue."""
        assert get_class_from_choice(2) == CharacterClass.ROGUE

    def test_choice_3_mage(self):
        """Choice 3 should return Mage."""
        assert get_class_from_choice(3) == CharacterClass.MAGE

    def test_choice_4_healer(self):
        """Choice 4 should return Healer."""
        assert get_class_from_choice(4) == CharacterClass.HEALER

    def test_invalid_choice_0(self):
        """Choice 0 should raise DataError."""
        with pytest.raises(DataError, match="Invalid class choice"):
            get_class_from_choice(0)

    def test_invalid_choice_5(self):
        """Choice 5 should raise DataError."""
        with pytest.raises(DataError, match="Invalid class choice"):
            get_class_from_choice(5)

    def test_invalid_choice_negative(self):
        """Negative choice should raise DataError."""
        with pytest.raises(DataError, match="Invalid class choice"):
            get_class_from_choice(-1)


class TestClassBalance:
    """Test class balance and design."""

    def test_total_stats_balance(self):
        """Classes should have balanced total stats."""
        warrior = CLASS_TEMPLATES[CharacterClass.WARRIOR]
        rogue = CLASS_TEMPLATES[CharacterClass.ROGUE]
        mage = CLASS_TEMPLATES[CharacterClass.MAGE]

        warrior_total = warrior.hp + warrior.attack + warrior.defense
        rogue_total = rogue.hp + rogue.attack + rogue.defense
        mage_total = mage.hp + mage.attack + mage.defense

        # Warrior should have highest total (tank)
        assert warrior_total >= rogue_total
        assert warrior_total >= mage_total

        # Mage should have lowest total (glass cannon)
        assert mage_total <= rogue_total

    def test_hp_ordering(self):
        """HP should be: Warrior > Rogue > Mage."""
        warrior = CLASS_TEMPLATES[CharacterClass.WARRIOR]
        rogue = CLASS_TEMPLATES[CharacterClass.ROGUE]
        mage = CLASS_TEMPLATES[CharacterClass.MAGE]

        assert warrior.hp > rogue.hp > mage.hp

    def test_all_stats_positive(self):
        """All stats should be positive."""
        for template in CLASS_TEMPLATES.values():
            assert template.hp > 0
            assert template.attack > 0
            assert template.defense >= 0  # Mage can have 0 defense

    def test_progression_total_balance(self):
        """Progression should maintain class identity."""
        warrior = CLASS_TEMPLATES[CharacterClass.WARRIOR]
        mage = CLASS_TEMPLATES[CharacterClass.MAGE]

        # Warrior should gain more HP than mage
        assert warrior.hp_per_level > mage.hp_per_level
