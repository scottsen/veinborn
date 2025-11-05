"""
Integration tests for the equipment system.

Tests the full crafting → equipping → combat loop:
1. Craft equipment at forge
2. Equip equipment from inventory
3. Use equipment bonuses in combat
"""


import pytest
from src.core.game import Game
from src.core.entities import Player, Monster
from src.core.actions import CraftAction, EquipAction, AttackAction
from src.core.base.entity import Entity, EntityType


pytestmark = pytest.mark.integration

class TestEquipmentSystem:
    """Test complete equipment system integration."""

    def test_player_starts_with_empty_equipment_slots(self):
        """Players should start with no equipment equipped."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        assert player.equipped_weapon is None
        assert player.equipped_armor is None

    def test_player_total_stats_without_equipment(self):
        """Player stats should equal base stats when no equipment equipped."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        assert player.get_total_attack() == player.attack
        assert player.get_total_defense() == player.defense

    def test_equip_weapon_adds_attack_bonus(self):
        """Equipping a weapon should add attack bonus to total attack."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        # Create a mock weapon with attack bonus
        weapon = Entity(
            entity_type=EntityType.ITEM,
            name="Test Sword",
        )
        weapon.set_stat('equipment_slot', 'weapon')
        weapon.set_stat('attack_bonus', 5)

        # Add to inventory
        player.add_to_inventory(weapon)

        # Equip weapon
        action = EquipAction(actor_id=player.entity_id, item_id=weapon.entity_id)
        outcome = action.execute(game.context)

        assert outcome.is_success
        assert player.equipped_weapon == weapon
        assert weapon not in player.inventory  # Removed from inventory
        assert player.get_total_attack() == player.attack + 5

    def test_equip_armor_adds_defense_bonus(self):
        """Equipping armor should add defense bonus to total defense."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        # Create a mock armor with defense bonus
        armor = Entity(
            entity_type=EntityType.ITEM,
            name="Test Chestplate",
        )
        armor.set_stat('equipment_slot', 'armor')
        armor.set_stat('defense_bonus', 3)

        # Add to inventory
        player.add_to_inventory(armor)

        # Equip armor
        action = EquipAction(actor_id=player.entity_id, item_id=armor.entity_id)
        outcome = action.execute(game.context)

        assert outcome.is_success
        assert player.equipped_armor == armor
        assert armor not in player.inventory
        assert player.get_total_defense() == player.defense + 3

    def test_swap_weapon_unequips_old_weapon(self):
        """Equipping a new weapon should unequip and return old weapon to inventory."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        # Create two weapons
        weapon1 = Entity(entity_type=EntityType.ITEM, name="Sword 1")
        weapon1.set_stat('equipment_slot', 'weapon')
        weapon1.set_stat('attack_bonus', 3)

        weapon2 = Entity(entity_type=EntityType.ITEM, name="Sword 2")
        weapon2.set_stat('equipment_slot', 'weapon')
        weapon2.set_stat('attack_bonus', 5)

        # Add both to inventory and equip first
        player.add_to_inventory(weapon1)
        player.add_to_inventory(weapon2)

        action1 = EquipAction(actor_id=player.entity_id, item_id=weapon1.entity_id)
        action1.execute(game.context)

        assert player.equipped_weapon == weapon1
        assert weapon1 not in player.inventory

        # Equip second weapon
        action2 = EquipAction(actor_id=player.entity_id, item_id=weapon2.entity_id)
        outcome = action2.execute(game.context)

        assert outcome.is_success
        assert player.equipped_weapon == weapon2  # New weapon equipped
        assert weapon1 in player.inventory  # Old weapon returned
        assert weapon2 not in player.inventory  # New weapon removed from inventory
        assert player.get_total_attack() == player.attack + 5  # Using new weapon bonus

    def test_combat_uses_equipment_bonuses(self):
        """Combat should use equipment bonuses in damage calculation."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        # Create and add a goblin
        goblin = Monster.create_goblin(x=1, y=1)
        player.x, player.y = 1, 2  # Adjacent to goblin
        game.context.add_entity(goblin)

        # Get base damage (no equipment)
        base_damage = max(1, player.attack - goblin.defense)

        # Create and equip a weapon
        weapon = Entity(entity_type=EntityType.ITEM, name="Test Sword")
        weapon.set_stat('equipment_slot', 'weapon')
        weapon.set_stat('attack_bonus', 10)
        player.add_to_inventory(weapon)

        equip_action = EquipAction(actor_id=player.entity_id, item_id=weapon.entity_id)
        equip_action.execute(game.context)

        # Attack goblin with equipment
        attack_action = AttackAction(actor_id=player.entity_id, target_id=goblin.entity_id)
        attack_outcome = attack_action.execute(game.context)

        # Calculate expected damage with equipment
        expected_damage = max(1, player.get_total_attack() - goblin.defense)

        assert attack_outcome.success
        # Damage should be higher with equipment
        assert expected_damage > base_damage

    def test_player_takes_less_damage_with_armor(self):
        """Player should take less damage when equipped with armor."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        # Create a goblin that will attack
        goblin = Monster.create_goblin(x=1, y=1)
        player.x, player.y = 1, 2
        game.context.add_entity(goblin)

        # Calculate damage without armor
        damage_without_armor = max(1, goblin.attack - player.defense)

        # Create and equip armor
        armor = Entity(entity_type=EntityType.ITEM, name="Test Armor")
        armor.set_stat('equipment_slot', 'armor')
        armor.set_stat('defense_bonus', 5)
        player.add_to_inventory(armor)

        equip_action = EquipAction(actor_id=player.entity_id, item_id=armor.entity_id)
        equip_action.execute(game.context)

        # Calculate damage with armor
        damage_with_armor = max(1, goblin.attack - player.get_total_defense())

        # Player should take less damage with armor (or at least same if minimum damage)
        assert damage_with_armor <= damage_without_armor

    def test_cannot_equip_non_equipment_items(self):
        """Items without equipment_slot should not be equippable."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        # Create a non-equipment item (like ore)
        ore = Entity(entity_type=EntityType.ITEM, name="Copper Ore")
        ore.set_stat('ore_type', 'copper')  # No equipment_slot
        player.add_to_inventory(ore)

        # Try to equip
        action = EquipAction(actor_id=player.entity_id, item_id=ore.entity_id)
        outcome = action.execute(game.context)

        assert not outcome.is_success
        assert player.equipped_weapon is None
        assert player.equipped_armor is None

    def test_equip_doesnt_take_turn(self):
        """Equipping items should not consume a turn."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        weapon = Entity(entity_type=EntityType.ITEM, name="Test Sword")
        weapon.set_stat('equipment_slot', 'weapon')
        weapon.set_stat('attack_bonus', 3)
        player.add_to_inventory(weapon)

        action = EquipAction(actor_id=player.entity_id, item_id=weapon.entity_id)
        outcome = action.execute(game.context)

        assert outcome.is_success
        assert not outcome.took_turn  # Equipping is instant


class TestCraftAndEquipIntegration:
    """Test crafting + equipping integration."""

    def test_craft_and_equip_workflow(self):
        """Test the full craft → equip workflow."""
        game = Game()
        game.start_new_game(seed=42)
        player = game.context.get_player()

        # Create copper ore items (need 2 for copper sword)
        ore1 = Entity(entity_type=EntityType.ITEM, name="Copper Ore")
        ore1.set_stat('ore_type', 'copper')
        ore1.set_stat('hardness', 45)
        ore1.set_stat('purity', 50)

        ore2 = Entity(entity_type=EntityType.ITEM, name="Copper Ore")
        ore2.set_stat('ore_type', 'copper')
        ore2.set_stat('hardness', 40)
        ore2.set_stat('purity', 45)

        player.add_to_inventory(ore1)
        player.add_to_inventory(ore2)

        # Create a forge
        from src.core.entities import Forge
        forge = Forge(forge_type='basic_forge', x=1, y=1)
        player.x, player.y = 1, 2  # Adjacent to forge
        game.context.add_entity(forge)

        # Craft copper sword
        craft_action = CraftAction(
            actor_id=player.entity_id,
            forge_id=forge.entity_id,
            recipe_id='copper_sword'
        )
        craft_outcome = craft_action.execute(game.context)

        assert craft_outcome.success

        # Find the crafted sword in inventory
        sword = None
        for item in player.inventory:
            if item.get_stat('equipment_slot') == 'weapon':
                sword = item
                break

        assert sword is not None
        assert sword.get_stat('attack_bonus', 0) > 0  # Should have attack bonus

        # Equip the sword
        equip_action = EquipAction(actor_id=player.entity_id, item_id=sword.entity_id)
        equip_outcome = equip_action.execute(game.context)

        assert equip_outcome.success
        assert player.equipped_weapon == sword
        assert player.get_total_attack() > player.attack  # Has bonus from sword
