"""RecipeManager.preview_stats is exactly what a craft makes; bots craft only upgrades (VB-73)."""
import pytest

from core.actions.craft_action import CraftAction
from core.base.entity import EntityType
from core.entity_loader import EntityLoader
from core.game import Game
from tests.fuzz.services.perception_service import PerceptionService

pytestmark = pytest.mark.unit


@pytest.fixture
def forge_game():
    game = Game()
    game.start_new_game(seed=3, player_name="Crafter")
    player = game.state.player
    forge = game.context.get_entities_by_type(EntityType.FORGE)[0]
    player.x, player.y = forge.x + 1, forge.y
    player.inventory.clear()
    return game, player, forge


def ore(ore_type, n, floor=1):
    vein = EntityLoader().create_ore_vein(ore_type, 0, 0, floor=floor)
    return [vein.get_ore_item() for _ in range(n)]


@pytest.mark.parametrize('recipe_id', ['copper_dagger', 'copper_chestplate'])
def test_preview_matches_the_craft(forge_game, recipe_id):
    game, player, forge = forge_game
    for item in ore('copper', 3):            # one more than any copper recipe needs
        player.add_to_inventory(item)
    manager = CraftAction.get_recipe_manager()
    preview = manager.preview_stats(recipe_id, player.inventory)
    assert preview
    CraftAction(player.entity_id, forge.entity_id, recipe_id).execute(game.context)
    made = next(i for i in player.inventory if i.get_stat('recipe_id') == recipe_id)
    for stat, value in preview.items():
        assert made.get_stat(stat) == value, stat


def test_preview_needs_enough_ore(forge_game):
    _, player, _ = forge_game
    player.add_to_inventory(ore('copper', 1)[0])
    assert CraftAction.get_recipe_manager().preview_stats('copper_chestplate', player.inventory) is None


def test_bot_picks_only_an_upgrade(forge_game):
    game, player, _ = forge_game
    for item in ore('copper', 2):
        player.add_to_inventory(item)
    perception = PerceptionService()
    choice = perception.has_craftable_ore(game)
    assert choice is not None                                  # beats what is worn
    manager = CraftAction.get_recipe_manager()
    recipe = manager.get_recipe(choice)
    stat = 'attack_bonus' if recipe.equipment_slot == 'weapon' else 'defense_bonus'
    gain = manager.preview_stats(choice, player.inventory)[stat]
    # Wear something far better in both slots: nothing copper can make is an upgrade now
    from core.loot import LootGenerator
    for item_id, slot in (('battle_axe', 'equipped_weapon'), ('plate_mail', 'equipped_armor')):
        item = LootGenerator.get_instance().create_item(item_id)
        item.set_stat('attack_bonus' if slot == 'equipped_weapon' else 'defense_bonus', gain + 50)
        setattr(player, slot, item)
    assert perception.has_craftable_ore(game) is None
