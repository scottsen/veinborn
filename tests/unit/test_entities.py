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

pytestmark = pytest.mark.unit

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
    """Player XP and leveling: NetHack-style doubling curve (game_constants.yaml)."""

    @pytest.mark.unit
    def test_xp_curve_doubles_then_goes_linear(self):
        """Total XP to reach a level: 20, 40, 80 ... 10240 at 11, then +10000."""
        from core.config.config_loader import ConfigLoader
        config = ConfigLoader.get_config()
        assert config.get_xp_for_level(1) == 0
        assert [config.get_xp_for_level(n) for n in range(2, 7)] == [20, 40, 80, 160, 320]
        assert config.get_xp_for_level(11) == 10240
        assert config.get_xp_for_level(12) == 20240

    @pytest.mark.unit
    def test_player_gains_xp(self, fresh_player):
        """Player can gain experience points."""
        leveled_up = fresh_player.gain_xp(10)

        assert not leveled_up  # Not enough for level up
        assert fresh_player.get_stat('xp') == 10

    @pytest.mark.unit
    def test_player_levels_up_at_20_xp(self, fresh_player):
        """Level 2 needs 20 XP total -- about four goblins."""
        assert not fresh_player.gain_xp(19)
        assert fresh_player.get_stat('level') == 1

        assert fresh_player.gain_xp(1)
        assert fresh_player.get_stat('level') == 2
        assert fresh_player.xp_for_next_level() == 40

    @pytest.mark.unit
    def test_level_3_requires_40_total_xp(self, fresh_player):
        """Thresholds are cumulative: level 3 at 40 total, not 20 more after level 2."""
        fresh_player.gain_xp(20)
        assert not fresh_player.gain_xp(19)
        assert fresh_player.get_stat('level') == 2

        assert fresh_player.gain_xp(1)
        assert fresh_player.get_stat('level') == 3
        assert fresh_player.get_stat('xp') == 40

    @pytest.mark.unit
    def test_one_big_kill_grants_several_levels(self, fresh_player):
        """100 XP at level 1 crosses 20, 40 and 80: straight to level 4."""
        assert fresh_player.gain_xp(100)
        assert fresh_player.get_stat('level') == 4

    @pytest.mark.unit
    def test_classless_level_up_uses_config_growth(self, fresh_player):
        """No class: +1 attack, +0 defense, HP gain rolled in [3, 7] (hp_gain_per_level 5)."""
        initial_max_hp = fresh_player.max_hp
        initial_attack = fresh_player.attack
        initial_defense = fresh_player.defense

        fresh_player.gain_xp(20)

        assert 3 <= fresh_player.max_hp - initial_max_hp <= 7
        assert fresh_player.attack == initial_attack + 1
        assert fresh_player.defense == initial_defense

    @pytest.mark.unit
    def test_class_growth_is_used_on_level_up(self):
        """Each class levels with its own template growth, not a flat +5/+1/+1."""
        from core.character_class import CharacterClass, create_player_from_class, get_class_template
        for cls in CharacterClass:
            template = get_class_template(cls)
            player = create_player_from_class(cls, 0, 0)
            player.gain_xp(20)
            hp_gain = player.max_hp - template.hp
            low = max(1, -(-template.hp_per_level // 2))
            high = template.hp_per_level + template.hp_per_level // 2
            assert low <= hp_gain <= high, cls
            assert player.attack == template.attack + template.attack_per_level, cls
            assert player.defense == template.defense + template.defense_per_level, cls

    @pytest.mark.unit
    def test_level_up_adds_hp_but_does_not_fully_heal(self, damaged_player):
        """Like NetHack: the HP gain goes to current HP too, but it is not a full heal."""
        assert damaged_player.hp == 10
        assert damaged_player.max_hp == 20

        damaged_player.gain_xp(20)

        gained = damaged_player.max_hp - 20
        assert gained >= 1
        assert damaged_player.hp == 10 + gained
        assert damaged_player.hp < damaged_player.max_hp


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

        value = fresh_player.get_stat('nonexistent')

        assert value == 0


# ============================================================================
# Run tests with: pytest tests/unit/test_entities.py -v
# Run coverage: pytest tests/unit/test_entities.py --cov=src/core/entities
# ============================================================================
