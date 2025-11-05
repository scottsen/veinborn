"""Unit tests for core game entities.

Tests for Player, Monster, and OreVein classes.
Following MVP_TESTING_GUIDE.md patterns.
"""
import pytest
from core.entities import Player, Monster, OreVein, EntityType
from core.base.entity import Entity


# ============================================================================
# Player Tests
# ============================================================================

class TestPlayerCreation:
    """Tests for Player initialization."""

    @pytest.mark.unit
    def test_player_default_creation(self):
        """Player can be created with defaults."""
        player = Player()

        assert player is not None
        assert player.entity_type == EntityType.PLAYER
        assert player.name == "Player"
        assert player.hp == 20
        assert player.max_hp == 20
        assert player.attack == 5
        assert player.defense == 2
        assert player.is_alive
        assert player.is_active

    @pytest.mark.unit
    def test_player_custom_creation(self, fresh_player):
        """Player can be created with custom stats."""
        assert fresh_player.hp == 20
        assert fresh_player.max_hp == 20
        assert fresh_player.attack == 5
        assert fresh_player.defense == 2
        assert fresh_player.x == 10
        assert fresh_player.y == 10

    @pytest.mark.unit
    def test_player_initial_inventory_empty(self, fresh_player):
        """Player starts with empty inventory."""
        assert fresh_player.inventory == []
        assert len(fresh_player.inventory) == 0

    @pytest.mark.unit
    def test_player_initial_stats(self, fresh_player):
        """Player starts at level 1 with 0 XP."""
        assert fresh_player.get_stat('level') == 1
        assert fresh_player.get_stat('xp') == 0


class TestPlayerDamage:
    """Tests for Player damage mechanics."""

    @pytest.mark.unit
    def test_player_takes_damage(self, fresh_player):
        """Player HP decreases when damaged."""
        initial_hp = fresh_player.hp
        damage_taken = fresh_player.take_damage(5)

        assert damage_taken == 5
        assert fresh_player.hp == initial_hp - 5
        assert fresh_player.hp == 15
        assert fresh_player.is_alive

    @pytest.mark.unit
    def test_player_takes_zero_damage(self, fresh_player):
        """Player taking 0 damage has no effect."""
        initial_hp = fresh_player.hp
        damage_taken = fresh_player.take_damage(0)

        assert damage_taken == 0
        assert fresh_player.hp == initial_hp

    @pytest.mark.unit
    def test_player_hp_cannot_go_negative(self, fresh_player):
        """Player HP stops at 0, not negative."""
        damage_taken = fresh_player.take_damage(100)

        assert fresh_player.hp == 0
        # Bug fixed! Now returns actual damage taken, not requested
        assert damage_taken == 20  # Only had 20 HP to lose

    @pytest.mark.unit
    def test_player_death_at_zero_hp(self, fresh_player):
        """Player is marked dead when HP reaches 0."""
        assert fresh_player.is_alive

        fresh_player.take_damage(20)

        assert fresh_player.hp == 0
        assert not fresh_player.is_alive

    @pytest.mark.unit
    def test_player_death_from_overkill(self, fresh_player):
        """Player dies even from massive overkill damage."""
        fresh_player.take_damage(1000)

        assert fresh_player.hp == 0
        assert not fresh_player.is_alive

    @pytest.mark.unit
    def test_dead_player_takes_no_damage(self, fresh_player):
        """Dead player doesn't take additional damage."""
        fresh_player.take_damage(20)  # Kill player
        assert fresh_player.hp == 0

        additional_damage = fresh_player.take_damage(10)

        assert additional_damage == 0
        assert fresh_player.hp == 0


class TestPlayerHealing:
    """Tests for Player healing mechanics."""

    @pytest.mark.unit
    def test_player_heals(self, damaged_player):
        """Player HP increases when healed."""
        initial_hp = damaged_player.hp
        healing_done = damaged_player.heal(5)

        assert healing_done == 5
        assert damaged_player.hp == initial_hp + 5
        assert damaged_player.hp == 15

    @pytest.mark.unit
    def test_player_cannot_overheal(self, damaged_player):
        """Player cannot heal beyond max HP."""
        healing_done = damaged_player.heal(50)

        assert healing_done == 10  # Only had 10 HP missing
        assert damaged_player.hp == damaged_player.max_hp
        assert damaged_player.hp == 20

    @pytest.mark.unit
    def test_full_hp_player_cannot_heal(self, fresh_player):
        """Player at full HP gains no healing."""
        assert fresh_player.hp == fresh_player.max_hp

        healing_done = fresh_player.heal(10)

        assert healing_done == 0
        assert fresh_player.hp == fresh_player.max_hp

    @pytest.mark.unit
    def test_dead_player_cannot_heal(self, fresh_player):
        """Dead player cannot be healed."""
        fresh_player.take_damage(100)  # Kill player
        assert not fresh_player.is_alive

        healing_done = fresh_player.heal(10)

        assert healing_done == 0
        assert fresh_player.hp == 0
        assert not fresh_player.is_alive


class TestPlayerMovement:
    """Tests for Player movement mechanics."""

    @pytest.mark.unit
    def test_player_move_to_absolute(self, fresh_player):
        """Player can move to absolute position."""
        fresh_player.move_to(15, 20)

        assert fresh_player.x == 15
        assert fresh_player.y == 20

    @pytest.mark.unit
    def test_player_move_by_relative(self, fresh_player):
        """Player can move by relative offset."""
        initial_x = fresh_player.x
        initial_y = fresh_player.y

        fresh_player.move_by(3, -2)

        assert fresh_player.x == initial_x + 3
        assert fresh_player.y == initial_y - 2
        assert fresh_player.x == 13
        assert fresh_player.y == 8

    @pytest.mark.unit
    def test_player_distance_calculation(self, fresh_player, weak_goblin):
        """Player can calculate distance to other entities."""
        # Player at (10, 10), Goblin at (11, 10)
        distance = fresh_player.distance_to(weak_goblin)

        assert distance == 1.0  # Adjacent horizontally

    @pytest.mark.unit
    def test_player_adjacency_check(self, fresh_player, weak_goblin):
        """Player can check if adjacent to other entity."""
        # Player at (10, 10), Goblin at (11, 10) - should be adjacent
        assert fresh_player.is_adjacent(weak_goblin)

        # Move goblin far away
        weak_goblin.move_to(20, 20)
        assert not fresh_player.is_adjacent(weak_goblin)


class TestPlayerInventory:
    """Tests for Player inventory management."""

    @pytest.mark.unit
    def test_player_can_add_item_to_inventory(self, fresh_player, copper_ore):
        """Player can add items to inventory."""
        assert len(fresh_player.inventory) == 0

        success = fresh_player.add_to_inventory(copper_ore)

        assert success
        assert len(fresh_player.inventory) == 1
        assert copper_ore in fresh_player.inventory

    @pytest.mark.unit
    def test_added_item_removed_from_world(self, fresh_player, copper_ore):
        """Items added to inventory are removed from world."""
        assert copper_ore.x is not None
        assert copper_ore.y is not None

        fresh_player.add_to_inventory(copper_ore)

        assert copper_ore.x is None
        assert copper_ore.y is None

    @pytest.mark.unit
    def test_player_can_remove_item_from_inventory(self, fresh_player, copper_ore):
        """Player can remove items from inventory."""
        fresh_player.add_to_inventory(copper_ore)
        assert len(fresh_player.inventory) == 1

        success = fresh_player.remove_from_inventory(copper_ore)

        assert success
        assert len(fresh_player.inventory) == 0
        assert copper_ore not in fresh_player.inventory

    @pytest.mark.unit
    def test_removing_nonexistent_item_returns_false(self, fresh_player, copper_ore):
        """Removing item not in inventory returns False."""
        assert len(fresh_player.inventory) == 0

        success = fresh_player.remove_from_inventory(copper_ore)

        assert not success
        assert len(fresh_player.inventory) == 0

    @pytest.mark.unit
    def test_inventory_has_max_capacity(self, fresh_player):
        """Inventory has maximum capacity of 20 items."""
        # Fill inventory to max
        for i in range(20):
            ore = OreVein(ore_type="copper", x=i, y=0,
                         hardness=50, conductivity=50, malleability=50,
                         purity=50, density=50)
            success = fresh_player.add_to_inventory(ore)
            assert success

        assert len(fresh_player.inventory) == 20

        # Try to add 21st item
        extra_ore = OreVein(ore_type="iron", x=99, y=99,
                           hardness=75, conductivity=60, malleability=65,
                           purity=70, density=85)
        success = fresh_player.add_to_inventory(extra_ore)

        assert not success
        assert len(fresh_player.inventory) == 20
        assert extra_ore not in fresh_player.inventory


class TestPlayerExperience:
    """Tests for Player XP and leveling mechanics."""

    @pytest.mark.unit
    def test_player_gains_xp(self, fresh_player):
        """Player can gain experience points."""
        initial_xp = fresh_player.get_stat('xp')

        leveled_up = fresh_player.gain_xp(50)

        assert not leveled_up  # Not enough for level up
        assert fresh_player.get_stat('xp') == initial_xp + 50
        assert fresh_player.get_stat('xp') == 50

    @pytest.mark.unit
    def test_player_levels_up_at_100_xp(self, fresh_player):
        """Player levels up when reaching 100 XP."""
        initial_level = fresh_player.get_stat('level')
        initial_max_hp = fresh_player.max_hp
        initial_attack = fresh_player.attack
        initial_defense = fresh_player.defense

        leveled_up = fresh_player.gain_xp(100)

        assert leveled_up
        assert fresh_player.get_stat('level') == initial_level + 1
        assert fresh_player.get_stat('level') == 2
        assert fresh_player.get_stat('xp') == 100

    @pytest.mark.unit
    def test_level_up_increases_stats(self, fresh_player):
        """Leveling up increases player stats."""
        initial_max_hp = fresh_player.max_hp
        initial_attack = fresh_player.attack
        initial_defense = fresh_player.defense

        fresh_player.gain_xp(100)

        assert fresh_player.max_hp == initial_max_hp + 5
        assert fresh_player.attack == initial_attack + 1
        assert fresh_player.defense == initial_defense + 1

    @pytest.mark.unit
    def test_level_up_restores_hp(self, damaged_player):
        """Leveling up fully restores HP."""
        assert damaged_player.hp == 10  # Start damaged
        assert damaged_player.max_hp == 20

        damaged_player.gain_xp(100)

        assert damaged_player.hp == damaged_player.max_hp
        assert damaged_player.hp == 25  # New max HP

    @pytest.mark.unit
    def test_gaining_insufficient_xp_no_level(self, fresh_player):
        """Gaining less than 100 XP doesn't level up."""
        leveled_up = fresh_player.gain_xp(99)

        assert not leveled_up
        assert fresh_player.get_stat('level') == 1
        assert fresh_player.get_stat('xp') == 99

    @pytest.mark.unit
    def test_level_2_requires_200_xp(self, fresh_player):
        """Level 2 → 3 requires 200 XP total."""
        # Reach level 2
        fresh_player.gain_xp(100)
        assert fresh_player.get_stat('level') == 2

        # Need 200 more XP for level 3 (level * 100)
        leveled_up = fresh_player.gain_xp(99)
        assert not leveled_up
        assert fresh_player.get_stat('level') == 2

        leveled_up = fresh_player.gain_xp(1)
        assert leveled_up
        assert fresh_player.get_stat('level') == 3
        assert fresh_player.get_stat('xp') == 200


class TestPlayerStats:
    """Tests for Player stat management."""

    @pytest.mark.unit
    def test_player_can_get_stat(self, fresh_player):
        """Player can retrieve stat values."""
        level = fresh_player.get_stat('level')
        xp = fresh_player.get_stat('xp')

        assert level == 1
        assert xp == 0

    @pytest.mark.unit
    def test_player_can_set_stat(self, fresh_player):
        """Player can set custom stat values."""
        fresh_player.set_stat('custom_stat', 42)

        value = fresh_player.get_stat('custom_stat')
        assert value == 42

    @pytest.mark.unit
    def test_getting_nonexistent_stat_returns_default(self, fresh_player):
        """Getting nonexistent stat returns default value."""
        value = fresh_player.get_stat('nonexistent', 999)

        assert value == 999

    @pytest.mark.unit
    def test_getting_nonexistent_stat_no_default(self, fresh_player):
        """Getting nonexistent stat with no default returns 0."""
pytestmark = pytest.mark.unit

        value = fresh_player.get_stat('nonexistent')

        assert value == 0


# ============================================================================
# Run tests with: pytest tests/unit/test_entities.py -v
# Run coverage: pytest tests/unit/test_entities.py --cov=src/core/entities
# ============================================================================
