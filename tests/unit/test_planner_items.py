"""ActionPlanner drinks potions when low and collects potions and food nearby."""

import pytest

from core.base.entity import EntityType
from core.character_class import CharacterClass
from core.loot import LootGenerator
from tests.fuzz.services import action_planner as planner_module
from tests.unit.test_planner_abilities import make

pytestmark = pytest.mark.unit


def potion(item_id='potion_healing'):
    return LootGenerator.get_instance().create_item(item_id)


def warrior():
    game, planner = make("warrior")  # no heal ability, so drinking is the only heal
    for e in list(game.state.entities.values()):
        if e.entity_type == EntityType.ITEM:
            game.context.remove_entity(e.entity_id)
    return game, planner


def drop_beside_player(game, item, dist=2):
    p = game.state.player
    for dx in range(dist, 0, -1):
        for sx in (1, -1):
            x, y = p.x + sx * dx, p.y
            if game.state.dungeon_map.is_walkable(x, y):
                item.x, item.y = x, y
                game.context.add_entity(item)
                return item
    pytest.skip("no open tile beside the player")


def test_drinks_when_low():
    game, planner = warrior()
    player = game.state.player
    bottle = potion()
    player.add_to_inventory(bottle)
    player.hp = int(player.max_hp * planner_module.DRINK_BELOW)
    monster_in_sight(game)               # with nothing in sight it would rest instead (VB-107)
    assert planner.get_smart_action(game) == ('use', {'item_id': bottle.entity_id})


def monster_in_sight(game, min_dist=3, max_dist=5):
    from core.fog import can_see
    p = game.state.player
    m = game.state.dungeon_map
    for x in range(p.x - max_dist, p.x + max_dist + 1):
        for y in range(p.y - max_dist, p.y + max_dist + 1):
            d = max(abs(x - p.x), abs(y - p.y))
            if min_dist <= d <= max_dist and m.in_bounds(x, y) and m.is_walkable(x, y) \
                    and can_see(m, p.x, p.y, x, y):
                mon = game.entity_loader.create_monster("goblin", x, y)
                game.context.add_entity(mon)
                return mon
    pytest.skip("no tile in sight for a monster")


def test_rests_when_hurt_with_nothing_in_sight_until_nearly_full():
    game, planner = warrior()
    player = game.state.player
    player.hp = int(player.max_hp * 0.5)
    assert planner.get_smart_action(game) == ('wait', {}) and planner.resting
    player.hp = int(player.max_hp * 0.8)         # above REST_BELOW but already resting: keep going
    assert planner.get_smart_action(game) == ('wait', {})
    player.hp = int(player.max_hp * 0.95)
    assert planner.get_smart_action(game) != ('wait', {}) and not planner.resting


def test_does_not_start_resting_when_only_slightly_hurt():
    game, planner = warrior()
    player = game.state.player
    player.hp = int(player.max_hp * 0.8)
    assert planner.get_smart_action(game) != ('wait', {}) and not planner.resting


def test_a_monster_in_sight_ends_the_rest():
    game, planner = warrior()
    player = game.state.player
    player.hp = int(player.max_hp * 0.5)
    assert planner.get_smart_action(game) == ('wait', {})
    monster_in_sight(game)
    planner.perception._cache.clear()          # the bot loop clears the perception cache every turn
    assert planner.get_smart_action(game) != ('wait', {}) and not planner.resting


def test_does_not_drink_above_the_threshold():
    game, planner = warrior()
    player = game.state.player
    player.add_to_inventory(potion())
    player.hp = player.max_hp - 1
    assert planner.drink_action(game) is None


def test_picks_up_a_potion_underfoot():
    game, planner = warrior()
    p = game.state.player
    item = potion()
    item.x, item.y = p.x, p.y
    game.context.add_entity(item)
    assert planner.collect_action(game) == ('pickup', {})


def test_walks_to_a_nearby_potion():
    game, planner = warrior()
    item = drop_beside_player(game, potion())
    action, kwargs = planner.collect_action(game)
    p = game.state.player
    assert action == 'move'
    assert max(abs(p.x + kwargs['dx'] - item.x), abs(p.y + kwargs['dy'] - item.y)) < \
        max(abs(p.x - item.x), abs(p.y - item.y))


def test_ignores_items_it_cannot_use():
    game, planner = warrior()
    drop_beside_player(game, potion('scroll_mapping'))
    assert planner.collect_action(game) is None


def test_does_not_collect_with_a_full_pack():
    game, planner = warrior()
    player = game.state.player
    while len(player.inventory) < planner_module.INVENTORY_MAX:
        player.add_to_inventory(potion('scroll_mapping'))
    drop_beside_player(game, potion())
    assert planner.collect_action(game) is None


def test_no_detour_for_an_item_with_a_monster_near():
    game, planner = warrior()
    item = drop_beside_player(game, potion())
    orc = game.entity_loader.create_monster("orc", item.x, item.y + 1)
    game.context.add_entity(orc)
    assert planner.collect_action(game) is None


def test_a_low_mage_drinks_before_bolting():
    from tests.unit.test_planner_abilities import add_monster_in_sight
    game, planner = make("mage")
    player = game.state.player
    bottle = potion()
    player.add_to_inventory(bottle)
    add_monster_in_sight(game)
    player.hp = int(player.max_hp * planner_module.DRINK_BELOW)
    assert planner.get_smart_action(game) == ('use', {'item_id': bottle.entity_id})
    player.hp = player.max_hp
    assert planner.get_smart_action(game) == ('ability', {'ability': 'force_bolt'})


def test_full_pack_drops_junk_before_anything_useful():
    game, planner = warrior()
    player = game.state.player
    player.inventory.clear()
    shield = LootGenerator.get_instance().create_item('gold_pile_small')    # no use
    player.add_to_inventory(shield)
    while len(player.inventory) < planner_module.INVENTORY_MAX:
        player.add_to_inventory(potion())
    action = planner.get_smart_action(game)
    assert action == ('drop', {'item_id': shield.entity_id})


def test_full_pack_drops_healing_only_beyond_the_reserve():
    game, planner = warrior()
    player = game.state.player
    player.inventory.clear()
    while len(player.inventory) < planner_module.INVENTORY_MAX:
        player.add_to_inventory(potion())
    action, kwargs = planner.get_smart_action(game)
    assert action == 'drop'                                           # 20 potions > reserve
    player.inventory[:] = player.inventory[:planner_module.HEALING_RESERVE]
    assert planner.junk_to_drop(game) is None                         # pack has room again


def test_wears_looted_armor():
    """Looted gear has item_type but no equipment_slot; the bot used to ignore it."""
    game, planner = warrior()
    player = game.state.player
    player.equipped_armor = None
    mail = LootGenerator.get_instance().create_item('chainmail')
    assert not mail.get_stat('equipment_slot')
    player.add_to_inventory(mail)
    assert planner.get_smart_action(game) == ('equip', {'item_id': mail.entity_id})


def ore(purity):
    item = potion('dagger')                       # any entity carrying ore stats
    item.set_stat('ore_type', 'iron')
    item.set_stat('purity', purity)
    return item


def test_walks_to_a_boss_material_even_when_leaving():
    game, planner = warrior()
    planner.sweeper.done = lambda g: True         # floor swept: potions and ore are skipped
    item = drop_beside_player(game, potion('lich_phylactery'))
    action, kwargs = planner.get_smart_action(game)
    p = game.state.player
    assert action == 'move'
    assert max(abs(p.x + kwargs['dx'] - item.x), abs(p.y + kwargs['dy'] - item.y)) < \
        max(abs(p.x - item.x), abs(p.y - item.y))


def test_picks_up_a_boss_material_underfoot():
    game, planner = warrior()
    p = game.state.player
    item = potion('phoenix_feather')
    item.x, item.y = p.x, p.y
    game.context.add_entity(item)
    assert planner.material_action(game) == ('pickup', {})


def test_full_pack_drops_its_worst_ore_for_a_boss_material():
    game, planner = warrior()
    player = game.state.player
    player.inventory.clear()
    worst = ore(10)
    player.add_to_inventory(potion("wraith_essence"))     # a material already carried stays
    player.add_to_inventory(worst)
    while len(player.inventory) < planner_module.INVENTORY_MAX:
        player.add_to_inventory(ore(80))
    drop_beside_player(game, potion('dragon_bone'))
    assert planner.material_action(game) == ('drop', {'item_id': worst.entity_id})


def test_full_pack_of_materials_leaves_the_new_one():
    game, planner = warrior()
    player = game.state.player
    player.inventory.clear()
    while len(player.inventory) < planner_module.INVENTORY_MAX:
        player.add_to_inventory(potion('wraith_essence'))
    drop_beside_player(game, potion('dragon_bone'))
    assert planner.material_action(game) is None


def test_no_detour_for_a_material_with_a_monster_near():
    game, planner = warrior()
    item = drop_beside_player(game, potion('lich_phylactery'))
    orc = game.entity_loader.create_monster("orc", item.x, item.y + 1)
    game.context.add_entity(orc)
    assert planner.material_action(game) is None


def test_does_not_fetch_a_material_it_already_carries():
    game, planner = warrior()
    game.state.player.add_to_inventory(potion('dragon_bone'))
    drop_beside_player(game, potion('dragon_bone'))
    assert planner.material_action(game) is None


def test_full_pack_drops_a_second_copy_of_a_material():
    game, planner = warrior()
    player = game.state.player
    player.inventory.clear()
    first, second = potion('wraith_essence'), potion('wraith_essence')
    player.add_to_inventory(first)
    player.add_to_inventory(second)
    while len(player.inventory) < planner_module.INVENTORY_MAX:
        player.add_to_inventory(ore(80))
    assert planner.junk_to_drop(game) is second
