"""Crafting v2 (VB-115): parts from any metal, assemblies from carried parts."""
import pytest

from core.actions.craft_action import CraftAction
from core.base.entity import EntityType
from core.entity_loader import EntityLoader
from core.equipment import gear_total
from core.game import Game

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


def give(player, items):
    for item in items:
        assert player.add_to_inventory(item)


def craft(game, player, forge, recipe_id, **kw):
    out = CraftAction(player.entity_id, forge.entity_id, recipe_id, **kw).execute(game.context)
    assert out.success, recipe_id
    return out


def test_assembly_slots_are_validated_at_load():
    manager = CraftAction.get_recipe_manager()
    assert manager.get_recipe('sword').kind == 'assembly'
    assert manager.get_recipe('blade').part_slot == 'head'
    assert manager.get_recipe('blade').accepted_ore_types() == list(manager.METALS)


def test_a_part_takes_any_metal_and_the_ore_sets_its_tier(forge_game):
    game, player, forge = forge_game
    give(player, ore('copper', 2) + ore('adamantite', 2, floor=20))
    manager = CraftAction.get_recipe_manager()
    copper, adamantite = ore('copper', 2), ore('adamantite', 2, floor=20)
    weak = manager.create_part('blade', copper).get_stat('part_stats')['attack_bonus']
    strong = manager.create_part('blade', adamantite).get_stat('part_stats')['attack_bonus']
    assert strong > 3 * weak


def test_part_craft_consumes_ore_and_makes_a_part_item(forge_game):
    game, player, forge = forge_game
    give(player, ore('iron', 3))
    craft(game, player, forge, 'blade')
    parts = [i for i in player.inventory if i.get_stat('item_type') == 'part']
    assert len(parts) == 1 and parts[0].get_stat('part_id') == 'blade'
    assert parts[0].get_stat('part_ore_type') == 'iron'
    assert len([i for i in player.inventory if i.get_stat('ore_type')]) == 1   # 2 of 3 spent
    assert not parts[0].get_stat('equipment_slot')                              # not wearable


def test_assembly_sums_parts_and_preview_matches(forge_game):
    game, player, forge = forge_game
    give(player, ore('iron', 3))
    craft(game, player, forge, 'blade')
    craft(game, player, forge, 'hilt')
    manager = CraftAction.get_recipe_manager()
    preview = manager.preview_stats('sword', player.inventory)
    assert preview and 'attack_bonus' in preview and 'accuracy' in preview
    craft(game, player, forge, 'sword')
    sword = next(i for i in player.inventory if i.get_stat('recipe_id') == 'sword')
    for stat, value in preview.items():
        assert sword.get_stat(stat) == value, stat
    assert sword.name == 'Iron Sword' and sword.get_stat('equipment_slot') == 'weapon'
    assert not [i for i in player.inventory if i.get_stat('item_type') == 'part']   # consumed


def test_mixed_ore_names_the_sword_from_both(forge_game):
    game, player, forge = forge_game
    give(player, ore('mithril', 2, floor=10) + ore('iron', 1))
    craft(game, player, forge, 'blade')
    craft(game, player, forge, 'hilt')
    craft(game, player, forge, 'sword')
    assert next(i for i in player.inventory if i.get_stat('recipe_id') == 'sword').name == 'Mithril-Iron Sword'


def test_assembly_needs_every_required_part(forge_game):
    game, player, forge = forge_game
    give(player, ore('iron', 2))
    craft(game, player, forge, 'blade')
    ok, reason = CraftAction.get_recipe_manager().can_craft('sword', player.inventory, 1)
    assert not ok and 'grip' in reason


def test_hand_picked_parts_choose_which_part_is_used(forge_game):
    game, player, forge = forge_game
    give(player, ore('copper', 2) + ore('iron', 1) + ore('adamantite', 1, floor=20))
    manager = CraftAction.get_recipe_manager()
    copper_blade = manager.create_part('blade', ore('copper', 2))
    good_blade = manager.create_part('blade', ore('adamantite', 2, floor=20))
    hilt = manager.create_part('hilt', ore('iron', 1))
    player.inventory.clear()
    give(player, [copper_blade, good_blade, hilt])
    best = manager.preview_stats('sword', player.inventory)
    picked = manager.preview_stats('sword', player.inventory,
                                   [copper_blade.entity_id, hilt.entity_id])
    assert picked['attack_bonus'] < best['attack_bonus']
    craft(game, player, forge, 'sword', part_ids=[copper_blade.entity_id, hilt.entity_id])
    assert good_blade in player.inventory                       # the unpicked part stays


@pytest.mark.parametrize('bad', ['dup', 'two_heads', 'missing_grip', 'foreign'])
def test_wrong_part_picks_are_rejected(forge_game, bad):
    game, player, forge = forge_game
    manager = CraftAction.get_recipe_manager()
    b1 = manager.create_part('blade', ore('iron', 2))
    b2 = manager.create_part('blade', ore('iron', 2))
    hilt = manager.create_part('hilt', ore('iron', 1))
    plates = manager.create_part('plates', ore('iron', 3))
    give(player, [b1, b2, hilt, plates])
    picks = {'dup': [b1.entity_id, b1.entity_id, hilt.entity_id],
             'two_heads': [b1.entity_id, b2.entity_id, hilt.entity_id],
             'missing_grip': [b1.entity_id],
             'foreign': [b1.entity_id, hilt.entity_id, plates.entity_id]}[bad]
    assert manager.parts_for(manager.get_recipe('sword'), player.inventory, picks) == []
    assert not CraftAction(player.entity_id, forge.entity_id, 'sword', part_ids=picks).validate(game.context)


def test_gem_is_optional_and_adds_spell_power(forge_game):
    game, player, forge = forge_game
    manager = CraftAction.get_recipe_manager()
    blade = manager.create_part('blade', ore('mithril', 2, floor=10))
    hilt = manager.create_part('hilt', ore('mithril', 1, floor=10))
    gem = manager.create_part('focus_gem', ore('mithril', 1, floor=10))
    give(player, [blade, hilt, gem])
    assert 'spell_power' not in manager.preview_stats('sword', player.inventory)   # auto: no gem
    ids = [blade.entity_id, hilt.entity_id, gem.entity_id]
    assert manager.preview_stats('sword', player.inventory, ids)['spell_power'] > 0
    craft(game, player, forge, 'sword', part_ids=ids)
    sword = next(i for i in player.inventory if i.get_stat('recipe_id') == 'sword')
    assert sword.get_stat('spell_power') > 0 and gem not in player.inventory


def test_gem_rejects_copper(forge_game):
    game, player, forge = forge_game
    give(player, ore('copper', 2))
    ok, reason = CraftAction.get_recipe_manager().can_craft('focus_gem', player.inventory, 1)
    assert not ok


def test_assembled_gear_is_worn_like_any_gear(forge_game):
    game, player, forge = forge_game
    give(player, ore('iron', 6))
    craft(game, player, forge, 'plates')
    craft(game, player, forge, 'lining')
    craft(game, player, forge, 'chestplate')
    chest = next(i for i in player.inventory if i.get_stat('recipe_id') == 'chestplate')
    before = gear_total(player, 'defense_bonus')
    from core.equipment import wear
    wear(player, 'armor', chest)
    assert gear_total(player, 'defense_bonus') == before + chest.get_stat('defense_bonus')
    assert chest.get_stat('max_hp_bonus') > 0


def test_craft_action_round_trips_part_ids():
    action = CraftAction('a', 'f', 'sword', part_ids=['p1', 'p2'])
    assert CraftAction.from_dict(action.to_dict()) == action


def test_bots_are_never_suggested_parts_or_assemblies(forge_game):
    _, player, _ = forge_game
    give(player, ore('iron', 6))
    suggested = CraftAction.get_recipe_manager().suggest_recipe(player.inventory, 5)
    assert CraftAction.get_recipe_manager().get_recipe(suggested).kind == 'item'


def test_parts_and_assembled_gear_survive_a_save(forge_game, tmp_path):
    from core.save_load import SaveSystem
    game, player, forge = forge_game
    give(player, ore('iron', 3))
    craft(game, player, forge, 'blade')
    craft(game, player, forge, 'hilt')
    craft(game, player, forge, 'sword')
    give(player, ore('iron', 2))
    craft(game, player, forge, 'blade')                      # a part left in the pack
    system = SaveSystem(save_dir=tmp_path)
    system.save_game(game.state, "parts")
    loaded = system.load_game("parts").player
    sword = next(i for i in loaded.inventory if i.get_stat('recipe_id') == 'sword')
    part = next(i for i in loaded.inventory if i.get_stat('item_type') == 'part')
    assert sword.get_stat('assembled_from') == ['blade', 'hilt']
    assert part.get_stat('part_stats')['attack_bonus'] > 0 and part.get_stat('part_id') == 'blade'
    manager = CraftAction.get_recipe_manager()
    assert manager.parts_in(loaded.inventory, 'blade')


def test_picked_parts_are_named_from_the_head_whatever_the_pick_order(forge_game):
    game, player, forge = forge_game
    manager = CraftAction.get_recipe_manager()
    blade = manager.create_part('blade', ore('copper', 2))
    hilt = manager.create_part('hilt', ore('iron', 1))
    give(player, [blade, hilt])
    craft(game, player, forge, 'sword', part_ids=[hilt.entity_id, blade.entity_id])   # grip first
    assert next(i for i in player.inventory if i.get_stat('recipe_id') == 'sword').name == 'Copper-Iron Sword'


def test_quick_drop_never_drops_a_crafted_part_before_ore_or_junk(forge_game):
    """Parts had no usefulness tier, so they ranked as NO_USE and `d` dropped them first."""
    from core.actions.drop_action import least_useful_item
    from core.loot import LootGenerator
    game, player, forge = forge_game
    manager = CraftAction.get_recipe_manager()
    part = manager.create_part('blade', ore('iron', 2))
    gold = LootGenerator.get_instance().create_item('scroll_mapping')     # no built effect: junk
    give(player, [part] + ore('iron', 1) + [gold])
    assert least_useful_item(player) is gold                 # junk first
    player.remove_from_inventory(gold)
    assert least_useful_item(player).get_stat('ore_type')    # then raw ore, still before a part


def test_a_human_sees_every_stat_of_crafted_gear(forge_game):
    """VB-126: the equipment list, the pack and the sidebar totals show accuracy, max HP and
    spell power, not just the slot's attack or defense."""
    from core.equipment import equipment_listing
    from core.snapshot import build_snapshot
    game, player, forge = forge_game
    manager = CraftAction.get_recipe_manager()
    blade = manager.create_part('blade', ore('mithril', 2, floor=10))
    hilt = manager.create_part('hilt', ore('mithril', 1, floor=10))
    gem = manager.create_part('focus_gem', ore('mithril', 1, floor=10))
    give(player, [blade, hilt, gem])
    craft(game, player, forge, 'sword', part_ids=[blade.entity_id, hilt.entity_id, gem.entity_id])
    view = build_snapshot(game.state).player
    sword = next(i for i in view.inventory if i.slot == 'weapon' and i.stats.get('spell_power'))
    assert {'attack_bonus', 'accuracy', 'spell_power'} <= set(sword.stats)
    _, carried = equipment_listing(view)
    line = next(l for l in carried if l.item.entity_id == sword.entity_id)
    assert 'accuracy' in line.text() and 'spell power' in line.text()
    assert 'vs worn' in line.text()
    from core.equipment import wear
    wear(player, 'weapon', next(i for i in player.inventory if i.entity_id == sword.entity_id))
    totals = build_snapshot(game.state).player
    assert totals.spell_power == sword.stats['spell_power'] and totals.accuracy == sword.stats['accuracy']
    worn_line = equipment_listing(totals)[0][0]
    assert 'spell power' in worn_line.text()


def test_gear_stats_diff_names_each_changed_stat():
    from core.equipment import stats_diff
    assert stats_diff({'attack_bonus': 7, 'accuracy': 2}, {'attack_bonus': 4, 'max_hp_bonus': 3}) == \
        {'attack_bonus': 3, 'accuracy': 2, 'max_hp_bonus': -3}
    assert stats_diff({'attack_bonus': 4}, {'attack_bonus': 4}) == {}
