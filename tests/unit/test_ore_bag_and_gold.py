"""Separate ore bag and gold counter (VB-131, VB-74).

Ore and boss materials count against an ore bag (30), everything else against the pack (20);
both live in `player.inventory`, so crafting, saves and the forge read them as before.
Gold is a number on the player, never an item.
"""
import json

import pytest

from core.actions.mine_action import MineAction
from core.base.entity import Entity, EntityType
from core.entities import Player
from core.game import Game
from core.loot import LootGenerator
from core.snapshot import Snapshot

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=23)
    p = g.state.player
    p.inventory.clear()
    p.gold = 0
    return g


def item(item_id):
    return LootGenerator.get_instance().create_item(item_id)


def ore(game, kind='copper'):
    return game.entity_loader.create_ore_vein(kind, 0, 0, floor=1).get_ore_item()


def fill_pack(game):
    p = game.state.player
    while p.has_room():
        assert p.add_to_inventory(item('bread'))


def fill_bag(game):
    p = game.state.player
    while p.ore_count() < p.MAX_ORE_BAG:
        assert p.add_to_inventory(ore(game))


# --- the two capacities are independent --------------------------------------------------

def test_sizes():
    assert (Player.MAX_INVENTORY, Player.MAX_ORE_BAG) == (20, 30)


def test_a_full_pack_still_takes_ore(game):
    p = game.state.player
    fill_pack(game)
    assert not p.has_room() and p.pack_count() == 20
    assert not p.add_to_inventory(item('bread'))
    mined = ore(game)
    assert p.has_room(mined) and p.add_to_inventory(mined)
    assert p.ore_count() == 1 and p.pack_count() == 20


def test_a_full_ore_bag_still_takes_pack_items(game):
    p = game.state.player
    fill_bag(game)
    assert p.ore_count() == 30 and p.has_room()
    assert not p.has_room(ore(game)) and not p.add_to_inventory(ore(game))
    assert p.add_to_inventory(item('long_sword'))
    assert p.pack_count() == 1 and p.ore_count() == 30


def test_boss_materials_use_the_ore_bag(game):
    p = game.state.player
    fill_pack(game)
    material = item('phoenix_essence')
    assert p.uses_ore_bag(material) and p.add_to_inventory(material)
    assert p.ore_count() == 1 and p.pack_count() == 20


def test_crafted_gear_and_parts_use_the_pack_not_the_bag(game):
    p = game.state.player
    gear = item('long_sword')
    gear.set_stat('ore_type', 'copper')            # old crafted gear carried an ore_type tag
    gear.set_stat('equipment_slot', 'weapon')
    assert not p.uses_ore_bag(gear)
    assert p.add_to_inventory(gear) and (p.pack_count(), p.ore_count()) == (1, 0)


def test_removing_ore_frees_a_bag_slot_not_a_pack_slot(game):
    p = game.state.player
    fill_bag(game)
    p.remove_from_inventory(p.inventory[0])
    assert p.has_room(ore(game)) and p.ore_count() == 29


# --- mining ------------------------------------------------------------------------------

def _mine(game, vein):
    p = game.state.player
    game.context.add_entity(vein)
    action = MineAction(actor_id=p.entity_id, ore_vein_id=vein.entity_id, turns_remaining=1)
    return action.execute(game.context)


def _vein(game):
    p = game.state.player
    vein = game.entity_loader.create_ore_vein('copper', p.x + 1, p.y, floor=1)
    return vein


def test_mining_with_a_full_pack_puts_the_ore_in_the_bag(game):
    p = game.state.player
    fill_pack(game)
    outcome = _mine(game, _vein(game))
    assert p.ore_count() == 1 and not any('full' in m.lower() for m in outcome.messages)


def test_mining_with_a_full_bag_drops_the_ore_on_the_floor(game):
    p = game.state.player
    fill_bag(game)
    outcome = _mine(game, _vein(game))
    assert p.ore_count() == 30
    assert any('full' in m.lower() for m in outcome.messages)
    here = [i for i in game.context.get_entities_by_type(EntityType.ITEM) if (i.x, i.y) == (p.x, p.y)]
    assert any(i.get_stat('ore_type') for i in here)


def test_ore_in_the_bag_is_still_what_crafting_uses(game):
    from core.crafting import RecipeManager
    p = game.state.player
    fill_pack(game)
    p.add_to_inventory(ore(game))
    manager = RecipeManager()
    assert manager.can_craft('copper_dagger', p.inventory, 1)[0]


# --- gold --------------------------------------------------------------------------------

def test_gold_is_counted_not_carried(game):
    p = game.state.player
    pile = item('gold_pile_small')
    amount = pile.get_stat('gold_amount')
    assert p.add_to_inventory(pile)
    assert p.gold == amount > 0 and pile not in p.inventory and p.pack_count() == 0
    assert not pile.is_alive


def test_gold_stacks_and_never_needs_room(game):
    p = game.state.player
    fill_pack(game)
    fill_bag(game)
    total = 0
    for pile_id in ('gold_pile_small', 'gold_pile_medium', 'gold_pile_large', 'gold_pile_small'):
        pile = item(pile_id)
        total += pile.get_stat('gold_amount')
        assert p.add_to_inventory(pile)
    assert p.gold == total and (p.pack_count(), p.ore_count()) == (20, 30)


def test_walking_over_gold_adds_it_and_removes_the_pile_from_the_world(game):
    p, m = game.state.player, game.state.dungeon_map
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = p.x + dx, p.y + dy
        if m.is_walkable(x, y) and not any(e.x == x and e.y == y for e in game.state.entities.values()):
            break
    else:
        pytest.skip("no free tile")
    pile = item('gold_pile_medium')
    pile.x, pile.y = x, y
    game.context.add_entity(pile)
    game.handle_player_action('move', dx=dx, dy=dy)
    assert p.gold == 25
    game.engine.tick()
    assert pile.entity_id not in game.state.entities       # not left behind as a dead item


def test_a_gold_pile_taken_with_g_counts_too(game):
    p = game.state.player
    pile = item('gold_pile_large')
    pile.x, pile.y = p.x, p.y
    game.context.add_entity(pile)
    game.handle_player_action('pickup')
    assert p.gold == 50


def test_monster_gold_drops_count_when_picked_up(game):
    """Loot gold from a real kill ends up in the counter."""
    from core.rng import GameRNG
    p = game.state.player
    loot = LootGenerator.get_instance()
    for seed in range(200):
        drops = [i for i in loot.generate_loot('goblin', 1, GameRNG(seed)) if i.get_stat('item_type') == 'gold']
        if drops:
            break
    assert drops
    for d in drops:
        p.add_to_inventory(d)
    assert p.gold == sum(d.get_stat('gold_amount') for d in drops)


def test_quick_drop_never_drops_gold(game):
    """`d` used to drop gold first (a no-use pack item); gold is a counter now, so there is nothing to drop."""
    from core.actions.drop_action import least_useful_item
    p = game.state.player
    p.add_to_inventory(item('gold_pile_large'))
    assert least_useful_item(p) is None and p.gold == 50
    p.add_to_inventory(item('potion_healing'))
    game.handle_player_action('drop', item_id=least_useful_item(p).entity_id)
    assert p.gold == 50                                  # dropped the potion, not the gold


# --- save / load -------------------------------------------------------------------------

def _round_trip(player):
    from core.save_load import SaveSystem
    system = SaveSystem.__new__(SaveSystem)
    return system, system._deserialize_entity(json.loads(json.dumps(system._serialize_entity(player))))


def test_gold_and_the_bag_survive_a_save(game):
    p = game.state.player
    p.add_to_inventory(item('gold_pile_large'))
    for _ in range(5):
        p.add_to_inventory(ore(game))
    p.add_to_inventory(item('long_sword'))
    _, back = _round_trip(p)
    assert back.gold == 50
    assert (back.ore_count(), back.pack_count()) == (5, 1)


def test_an_old_save_with_gold_items_converts_them_to_gold(game):
    p = game.state.player
    pile = item('gold_pile_medium')
    p.inventory.append(pile)            # how the old game carried gold: as pack items
    p.inventory.append(item('long_sword'))
    system, _ = _round_trip(p)
    data = system._serialize_entity(p)
    data.pop('gold')                    # and it had no gold counter
    back = system._deserialize_entity(json.loads(json.dumps(data)))
    assert back.gold == 25 and [i.content_id for i in back.inventory] == ['long_sword']


# --- snapshot and wire -------------------------------------------------------------------

def test_snapshot_splits_pack_and_bag_and_carries_gold(game):
    p = game.state.player
    p.add_to_inventory(item('gold_pile_medium'))
    p.add_to_inventory(item('long_sword'))
    p.add_to_inventory(item('potion_healing'))
    for _ in range(4):
        p.add_to_inventory(ore(game))
    p.add_to_inventory(item('phoenix_essence'))
    view = game.engine.snapshot().player
    assert view.gold == 25 and view.ore_capacity == 30 and view.inventory_capacity == 20
    assert len(view.pack) == 2 and len(view.bag) == 5
    assert all(i.in_ore_bag for i in view.bag) and not any(i.in_ore_bag for i in view.pack)
    back = Snapshot.from_dict(json.loads(json.dumps(game.engine.snapshot().to_dict()))).player
    assert (back.gold, back.ore_capacity, len(back.pack), len(back.bag)) == (25, 30, 2, 5)


def test_inventory_messages_report_pack_bag_and_gold(game):
    from core.item_listing import inventory_messages
    p = game.state.player
    p.add_to_inventory(item('gold_pile_small'))
    p.add_to_inventory(item('long_sword'))
    p.add_to_inventory(ore(game))
    head = inventory_messages(game.engine.snapshot().player)[0]
    assert "1/20 items" in head and "ore bag 1/30" in head and "10 gold" in head


# --- the screens -------------------------------------------------------------------------

def test_pack_screen_and_sidebar_show_gold_and_both_counts():
    import asyncio
    from ui.textual.app import VeinbornApp
    from ui.textual.pack_screen import PackScreen

    async def scenario():
        app = VeinbornApp(seed=5)
        async with app.run_test() as pilot:
            p = app.driver.game.state.player
            p.inventory.clear()
            p.gold = 0
            p.add_to_inventory(item('gold_pile_large'))
            p.add_to_inventory(item('long_sword'))
            for _ in range(3):
                p.add_to_inventory(ore(app.driver.game))
            await pilot.press("i")
            await pilot.pause()
            assert isinstance(app.screen, PackScreen)
            header = app.screen.header()
            assert "Pack 1/20" in header and "Ore bag 3/30" in header and "Gold 50" in header

    asyncio.run(scenario())


def test_ore_summary_gives_average_and_best_quality():
    from core.crafting import ore_summary
    lo = {'purity': 40, 'hardness': 40, 'malleability': 40, 'conductivity': 40, 'density': 40}
    hi = {k: 80 for k in lo}
    assert ore_summary([lo, hi, None]) == "Ore Q avg 60, best 80"
    assert ore_summary([]) == ""
