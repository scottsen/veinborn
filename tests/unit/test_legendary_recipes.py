"""Legendary recipes (VB-75): loaded, gated on a boss material, which the craft consumes.

recipes.yaml `legendary` needs requirements.special_requirement, an items.yaml
`materials` item that a boss drops (loot_tables.yaml). Before this, RecipeManager
loaded only weapons and armor, so the six legendaries did not exist in the game.
"""
import pytest
import yaml

from core.actions.craft_action import CraftAction
from core.actions.drop_action import ORE, usefulness
from core.base.entity import EntityType
from core.crafting import RecipeManager
from core.entity_loader import EntityLoader
from core.game import Game
from core.loot import LootGenerator
from core.rng import GameRNG

pytestmark = pytest.mark.unit

LEGENDARIES = {'flaming_sword', 'arcane_staff', 'dragon_bow', 'phoenix_armor', 'shadow_cloak', 'titans_hammer'}


def mithril(n):
    vein = EntityLoader().create_ore_vein('mithril', 0, 0, floor=8)
    return [vein.get_ore_item() for _ in range(n)]


def material(item_id):
    return LootGenerator.get_instance().create_item(item_id)


@pytest.fixture
def forge_game():
    game = Game()
    game.start_new_game(seed=3, player_name="Crafter")
    ctx, player = game.context, game.state.player
    forge = ctx.get_entities_by_type(EntityType.FORGE)[0]
    player.x, player.y = forge.x + 1, forge.y
    player.inventory.clear()
    game.state.current_floor = 12                    # arcane_staff min_floor
    return ctx, player, forge


def test_all_legendary_recipes_load():
    ids = {r.recipe_id for r in RecipeManager().get_all_recipes()}
    assert LEGENDARIES <= ids


def test_ore_alone_is_not_enough():
    rm = RecipeManager()
    ok, reason = rm.can_craft('arcane_staff', mithril(4), 12)
    assert not ok and 'lich_phylactery' in reason
    assert 'arcane_staff' not in {r.recipe_id for r in rm.get_craftable_recipes(mithril(4), 12)}


def test_ore_and_boss_material_craft():
    rm = RecipeManager()
    inventory = mithril(4) + [material('lich_phylactery')]
    assert rm.can_craft('arcane_staff', inventory, 12) == (True, None)
    assert 'arcane_staff' in {r.recipe_id for r in rm.get_craftable_recipes(inventory, 12)}
    assert rm.can_craft('arcane_staff', inventory, 11)[0] is False      # floor gate still holds


def test_craft_consumes_the_material_and_the_ore(forge_game):
    ctx, player, forge = forge_game
    for item in mithril(4) + [material('lich_phylactery')]:
        assert player.add_to_inventory(item)

    outcome = CraftAction(player.entity_id, forge.entity_id, 'arcane_staff').execute(ctx)

    assert outcome.result.value == 'success'
    assert [i.get_stat('recipe_id') for i in player.inventory] == ['arcane_staff']
    staff = player.inventory[0]
    assert staff.get_stat('equipment_slot') == 'weapon' and staff.get_stat('attack_bonus') > 10


def test_craft_without_the_material_is_refused(forge_game):
    ctx, player, forge = forge_game
    for item in mithril(4):
        player.add_to_inventory(item)
    action = CraftAction(player.entity_id, forge.entity_id, 'arcane_staff')
    assert not action.validate(ctx)
    assert len(player.inventory) == 4                                   # ore untouched


def test_every_special_requirement_is_an_item_some_monster_drops():
    with open(LootGenerator.get_instance().data_dir / 'balance' / 'loot_tables.yaml') as f:
        tables = yaml.safe_load(f)
    dropped = {entry['id'] for table in tables.values() if isinstance(table, dict)
               for cat in table.values() if isinstance(cat, dict) for entry in cat.get('items', [])}
    items = LootGenerator.get_instance().items
    required = {r.get_special_requirement() for r in RecipeManager().get_all_recipes()} - {None}
    assert required, "no recipe needs a material"
    for item_id in required:
        assert item_id in items, f"{item_id} not in items.yaml"
        assert item_id in dropped, f"no loot table drops {item_id}"
    materials = {i for i, d in items.items() if d.get('category') == 'materials'}
    assert materials == required, "a material no recipe uses, or a requirement that is not a material"


@pytest.mark.parametrize('boss, item_id', [
    ('lich', 'lich_phylactery'), ('phoenix', 'phoenix_essence'), ('phoenix', 'phoenix_feather'),
    ('ancient_horror', 'ancient_horror_core'),
])
def test_bosses_always_drop_their_material(boss, item_id):
    drops = LootGenerator.get_instance().generate_loot(boss, floor_number=20, rng=GameRNG(1))
    assert item_id in [d.content_id for d in drops]


def test_materials_are_kept_like_ore(fresh_player):
    assert usefulness(fresh_player, material('wraith_essence')) == ORE
