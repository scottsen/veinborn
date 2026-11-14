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
