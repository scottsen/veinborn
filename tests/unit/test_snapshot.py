"""build_snapshot: plain data with the derived numbers the sidebar shows."""
import json

import pytest

from core.character_class import CharacterClass
from core.game import Game
from core.loot import LootGenerator
from core.snapshot import build_snapshot

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=11)
    return g


def test_snapshot_is_json_serializable(game):
    json.dumps(build_snapshot(game.state).to_dict())


def test_player_totals_include_equipped_gear(game):
    p = game.state.player
    p.inventory.clear()
    p.equipped_weapon = p.equipped_armor = p.equipped_shield = None
    bare = build_snapshot(game.state).player
    sword = LootGenerator.get_instance().create_item('long_sword')
    p.equipped_weapon = sword
    snap = build_snapshot(game.state).player
    assert snap.attack == p.get_total_attack() > bare.attack
    assert snap.weapon.name == sword.name and snap.armor is None
    assert (snap.hp, snap.max_hp, snap.level) == (p.hp, p.max_hp, p.get_stat('level', 1))
    assert snap.xp_next == p.xp_for_next_level()


def test_inventory_and_capacity(game):
    p = game.state.player
    p.inventory.clear()
    p.add_to_inventory(LootGenerator.get_instance().create_item('dagger'))
    view = build_snapshot(game.state).player
    assert [i.name for i in view.inventory] == [p.inventory[0].name]
    assert view.inventory_capacity == p.get_stat('inventory_capacity', 20)


def test_entities_exclude_the_viewer_and_match_state(game):
    game.state.reveal_map = True      # fog has its own tests (test_fog.py)
    snap = build_snapshot(game.state)
    ids = {e.entity_id for e in snap.entities}
    assert game.state.player.entity_id not in ids
    assert ids == set(game.state.entities) - {game.state.player.entity_id}
    monsters = [e for e in snap.entities if e.entity_type == 'monster']
    assert monsters and snap.entity_at(monsters[0].x, monsters[0].y, 'monster') is not None


def test_map_and_turn_fields(game):
    game.state.reveal_map = True
    snap = build_snapshot(game.state)
    m = game.state.dungeon_map
    assert (snap.map.width, snap.map.height) == (m.width, m.height)
    assert snap.map.tiles == m.to_dict()['tiles']
    assert (snap.turn, snap.floor, snap.game_over) == (
        game.state.turn_count, game.state.current_floor, game.state.game_over)


def test_ability_cooldown_counts_down_to_ready():
    g = Game()
    g.start_new_game(seed=11, character_class=CharacterClass.MAGE)
    p = g.state.player
    view = build_snapshot(g.state).player.abilities[0]
    assert view.ready
    p.set_stat('cooldowns', {view.name: g.state.turn_count + 5})
    view = build_snapshot(g.state).player.abilities[0]
    assert view.cooldown_remaining == 5 and not view.ready


# -- crafting at a forge and usable items (VB-109, protocol 6) ----------------

def _at_forge(game):
    from core.base.entity import EntityType
    player = game.state.player
    forge = game.context.get_entities_by_type(EntityType.FORGE)[0]
    player.x, player.y = forge.x + 1, forge.y
    player.inventory.clear()
    return player, forge


def _copper(n):
    from core.entity_loader import EntityLoader
    vein = EntityLoader().create_ore_vein('copper', 0, 0, floor=1)
    return [vein.get_ore_item() for _ in range(n)]


def test_no_recipes_away_from_a_forge(game):
    player, forge = _at_forge(game)
    player.x, player.y = forge.x + 5, forge.y + 5
    view = build_snapshot(game.state).player
    assert view.forge_id is None and view.recipes == []


def test_recipes_listed_next_to_a_forge_craftable_first(game):
    player, forge = _at_forge(game)
    for ore in _copper(3):
        player.add_to_inventory(ore)
    view = build_snapshot(game.state).player
    assert view.forge_id == forge.entity_id
    assert view.recipes and view.recipes[0].craftable and view.recipes[0].stats
    assert all(r.reason for r in view.recipes if not r.craftable)
    flags = [r.craftable for r in view.recipes]
    assert flags == sorted(flags, reverse=True)            # craftable ones first


def test_uncraftable_recipe_says_what_is_missing(game):
    player, _ = _at_forge(game)
    view = build_snapshot(game.state).player
    assert view.recipes and not any(r.craftable for r in view.recipes)
    assert all('ore' in r.reason or 'floor' in r.reason or 'Requires' in r.reason for r in view.recipes)


def test_craft_intent_from_a_listed_recipe_works(game):
    player, forge = _at_forge(game)
    for ore in _copper(3):
        player.add_to_inventory(ore)
    recipe = build_snapshot(game.state).player.recipes[0]
    game.handle_player_action('craft', forge_id=forge.entity_id, recipe_id=recipe.recipe_id)
    assert any(i.get_stat('recipe_id') == recipe.recipe_id for i in player.inventory)


def test_items_know_whether_they_are_usable(game):
    p = game.state.player
    p.inventory.clear()
    loot = LootGenerator.get_instance()
    p.add_to_inventory(loot.create_item('potion_healing'))
    p.add_to_inventory(loot.create_item('long_sword'))
    potion, sword = build_snapshot(game.state).player.inventory
    assert potion.usable and not sword.usable


def test_recipes_survive_the_wire(game):
    from core.snapshot import Snapshot
    player, _ = _at_forge(game)
    for ore in _copper(3):
        player.add_to_inventory(ore)
    snap = build_snapshot(game.state)
    back = Snapshot.from_dict(json.loads(json.dumps(snap.to_dict())))
    assert back.player.recipes == snap.player.recipes and back.player.forge_id == snap.player.forge_id


# -- ore quality (VB-111) -------------------------------------------------------

def test_ore_carries_its_quality_and_lists_as_ore(game):
    from core.crafting import ore_label
    p = game.state.player
    p.inventory.clear()
    ore = _copper(1)[0]
    p.add_to_inventory(ore)
    p.add_to_inventory(LootGenerator.get_instance().create_item('long_sword'))
    ore_view, sword_view = build_snapshot(game.state).player.inventory
    assert ore_view.item_type == 'ore' and ore_view.ore['purity'] == ore.get_stat('purity')
    assert sword_view.ore is None
    assert ore_label(ore_view.ore).startswith(f"P{ore.get_stat('purity')} H{ore.get_stat('hardness')}")
    assert ore.get_stat('item_type', None) is None        # display only: autopickup rules unchanged


def test_ore_label_stars_jackpot_ore():
    from core.crafting import ore_label
    best = dict(purity=90, hardness=85, malleability=80, conductivity=99, density=81)
    assert ore_label(best).endswith("★")
    assert "★" not in ore_label({**best, 'density': 79})
    assert ore_label(None) == ""


def test_crafted_gear_is_not_ore(game):
    from core.crafting import ore_properties
    player, forge = _at_forge(game)
    for o in _copper(3):
        player.add_to_inventory(o)
    game.handle_player_action('craft', forge_id=forge.entity_id, recipe_id='copper_chestplate')
    made = next(i for i in player.inventory if i.get_stat('recipe_id'))
    assert ore_properties(made) is None


# -- choosing the ore a craft spends (VB-112) ------------------------------------

def _copper_with(**props):
    ore = _copper(1)[0]
    for k, v in props.items():
        ore.set_stat(k, v)
    return ore


def test_default_craft_spends_the_best_ore_not_the_first(game):
    player, forge = _at_forge(game)
    poor = [_copper_with(purity=10, hardness=10) for _ in range(2)]
    good = [_copper_with(purity=95, hardness=95) for _ in range(2)]
    for o in poor + good:                                   # the poor ore comes first in the pack
        player.add_to_inventory(o)
    recipe = next(r for r in build_snapshot(game.state).player.recipes if r.recipe_id == 'copper_sword')
    assert recipe.ore_ids == [o.entity_id for o in good] and len(recipe.ore_choices) == 4
    game.handle_player_action('craft', forge_id=forge.entity_id, recipe_id='copper_sword')
    assert all(o in player.inventory for o in poor) and not any(o in player.inventory for o in good)


def test_a_chosen_set_of_ore_is_what_the_craft_spends(game):
    from core.actions.craft_action import CraftAction
    player, forge = _at_forge(game)
    ores = [_copper_with(purity=p, hardness=p) for p in (10, 20, 95)]
    for o in ores:
        player.add_to_inventory(o)
    pick = [ores[0].entity_id, ores[1].entity_id]
    manager = CraftAction.get_recipe_manager()
    expected = manager.preview_stats('copper_sword', player.inventory, pick)
    game.handle_player_action('craft', forge_id=forge.entity_id, recipe_id='copper_sword', ore_ids=pick)
    made = next(i for i in player.inventory if i.get_stat('recipe_id') == 'copper_sword')
    assert ores[2] in player.inventory and ores[0] not in player.inventory
    assert made.get_stat('attack_bonus') == expected['attack_bonus']


@pytest.mark.parametrize('bad', ['wrong_count', 'repeat', 'not_carried'])
def test_a_wrong_pick_crafts_nothing(game, bad):
    player, forge = _at_forge(game)
    ores = _copper(3)
    for o in ores:
        player.add_to_inventory(o)
    pick = {'wrong_count': [ores[0].entity_id],
            'repeat': [ores[0].entity_id, ores[0].entity_id],
            'not_carried': [ores[0].entity_id, 'nope']}[bad]
    game.handle_player_action('craft', forge_id=forge.entity_id, recipe_id='copper_sword', ore_ids=pick)
    assert all(o in player.inventory for o in ores)
    assert not any(i.get_stat('recipe_id') for i in player.inventory)


def test_preview_from_properties_matches_preview_stats(game):
    from core.actions.craft_action import CraftAction
    from core.crafting import ore_properties
    player, _ = _at_forge(game)
    ores = _copper(2)
    for o in ores:
        player.add_to_inventory(o)
    manager = CraftAction.get_recipe_manager()
    ids = [o.entity_id for o in ores]
    assert manager.preview_from_properties('copper_sword', [ore_properties(o) for o in ores]) == \
        manager.preview_stats('copper_sword', player.inventory, ids)


def test_craft_event_carries_stats_and_ore_quality(game):
    from core.events import GameEventType
    player, forge = _at_forge(game)
    for o in _copper(3):
        player.add_to_inventory(o)
    seen = []
    game.event_bus.subscribe(GameEventType.EQUIPMENT_CRAFTED, seen.append, 'test')
    game.handle_player_action('craft', forge_id=forge.entity_id, recipe_id='copper_sword')
    data = seen[0].data
    assert data['recipe_id'] == 'copper_sword' and data['item_name'] == 'Copper Sword'
    assert data['stats'].get('attack_bonus', 0) >= 1
    assert set(data['ore']) >= {'purity', 'hardness'}


def test_parts_and_assemblies_are_listed_with_their_choices(game):
    from core.actions.craft_action import CraftAction
    player, forge = _at_forge(game)
    player.inventory.clear()
    manager = CraftAction.get_recipe_manager()
    from core.entity_loader import EntityLoader
    vein = EntityLoader().create_ore_vein('iron', 0, 0, floor=6)
    blade = manager.create_part('blade', [vein.get_ore_item() for _ in range(2)])
    hilt = manager.create_part('hilt', [vein.get_ore_item()])
    for part in (blade, hilt):
        player.add_to_inventory(part)
    view = build_snapshot(game.state).player
    sword = next(r for r in view.recipes if r.recipe_id == 'sword')
    assert sword.kind == 'assembly' and sword.craftable and sword.stats
    assert sword.required_slots == ['head', 'grip'] and sword.optional_slots == ['gem']
    assert set(sword.part_ids) == {blade.entity_id, hilt.entity_id}
    assert sword.part_choices['head'] == [blade.entity_id] and sword.part_choices['gem'] == []
    assert next(r for r in view.recipes if r.recipe_id == 'blade').kind == 'part'
    carried = {i.entity_id: i for i in view.inventory}
    assert carried[blade.entity_id].part['slot'] == 'head' and carried[blade.entity_id].part['ore'] == 'iron'
    # the client-side preview of a hand-picked set equals the server's craft
    picks = [carried[i].part for i in sword.part_ids]
    assert manager.preview_from_parts('sword', picks) == sword.stats
    assert manager.preview_from_parts('sword', picks[:1]) is None          # a slot is empty


def test_snapshot_round_trips_recipe_and_part_views(game):
    from core.snapshot import Snapshot
    player, _ = _at_forge(game)
    player.inventory.clear()
    snap = build_snapshot(game.state)
    again = Snapshot.from_dict(snap.to_dict())
    assert again.player.recipes == snap.player.recipes
