"""Bot state invariants and the combat recorder (VB-68 step 4)."""
import sys
from pathlib import Path

import pytest

from core.events import create_attack_event
from core.game import Game
from core.world import Tile, TileType

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fuzz"))
from veinborn_bot import CombatRecorder, VeinbornBot  # noqa: E402

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=21)
    return g


@pytest.fixture
def bot():
    return VeinbornBot()


def open_tile_next_to_player(game):
    p = game.state.player
    m = game.state.dungeon_map
    m.tiles[p.x + 1][p.y] = Tile(TileType.FLOOR)
    return p.x + 1, p.y


def test_a_fresh_game_has_no_violations(game, bot):
    assert bot.validate_game_state(game) == []


def test_two_actors_on_one_tile_is_a_violation(game, bot):
    p = game.state.player
    mon = game.entity_loader.create_monster("goblin", p.x, p.y)
    game.context.add_entity(mon)
    assert any("share tile" in v for v in bot.validate_game_state(game))


def test_an_actor_in_a_wall_is_a_violation(game, bot):
    x, y = open_tile_next_to_player(game)
    mon = game.entity_loader.create_monster("goblin", x, y)
    game.context.add_entity(mon)
    game.state.dungeon_map.tiles[x][y] = Tile(TileType.WALL)
    assert any("in a wall" in v for v in bot.validate_game_state(game))


def test_a_carried_item_on_the_map_is_a_violation(game, bot):
    from core.loot import LootGenerator
    item = LootGenerator.get_instance().create_item('bread')
    game.state.player.add_to_inventory(item)
    item.x, item.y = 1, 1
    assert any("also lies on the map" in v for v in bot.validate_game_state(game))


def test_recorder_attributes_damage_to_the_monster_type(game):
    recorder = CombatRecorder(game)
    x, y = open_tile_next_to_player(game)
    orc = game.entity_loader.create_monster("orc", x, y)
    game.context.add_entity(orc)
    player = game.state.player
    game.event_bus.publish_all([
        create_attack_event(attacker_id=orc.entity_id, defender_id=player.entity_id, damage=4, killed=False),
        create_attack_event(attacker_id=player.entity_id, defender_id=orc.entity_id, damage=9, killed=False),
        create_attack_event(attacker_id=orc.entity_id, defender_id=player.entity_id, damage=0, killed=False),
    ])
    assert recorder.damage_by == {'orc': 4}
    assert recorder.last_attacker == 'orc'


def test_recorder_counts_usable_pickups_and_carried_items(game):
    from core.loot import LootGenerator
    recorder = CombatRecorder(game)
    player = game.state.player
    loot = LootGenerator.get_instance()
    potion, sword = loot.create_item('potion_healing'), loot.create_item('long_sword')
    for item in (potion, sword):
        game.context.add_entity(item)
        player.add_to_inventory(item)
        game.event_bus.publish_dict({'type': 'item_picked_up', 'actor_id': player.entity_id,
                                     'item_id': item.entity_id, 'item_name': item.name})
    game.event_bus.publish_dict({'type': 'item_picked_up', 'actor_id': 'someone_else',
                                 'item_id': potion.entity_id, 'item_name': potion.name})
    assert recorder.items_picked_up == 1      # the sword has no effect; the other actor is ignored
    assert recorder.carried_usable() == 1


def test_recorder_counts_dropped_usable_items(game):
    from core.loot import LootGenerator
    recorder = CombatRecorder(game)
    player = game.state.player
    potion = LootGenerator.get_instance().create_item('potion_healing')
    game.context.add_entity(potion)
    game.event_bus.publish_dict({'type': 'item_dropped', 'actor_id': player.entity_id,
                                 'item_id': potion.entity_id, 'item_name': potion.name})
    assert recorder.items_dropped == 1


def test_recorder_lists_crafts_and_the_gear_worn_at_the_end(game):
    from core.base.entity import EntityType
    from core.entity_loader import EntityLoader
    recorder = CombatRecorder(game)
    player = game.state.player
    forge = game.context.get_entities_by_type(EntityType.FORGE)[0]
    player.x, player.y = forge.x + 1, forge.y
    player.inventory.clear()
    vein = EntityLoader().create_ore_vein('copper', 0, 0, floor=1)
    for _ in range(2):
        player.add_to_inventory(vein.get_ore_item())
    game.handle_player_action('craft', forge_id=forge.entity_id, recipe_id='copper_sword')
    assert [c['recipe'] for c in recorder.crafts] == ['copper_sword']
    craft = recorder.crafts[0]
    assert craft['floor'] == game.state.current_floor and craft['stats']['attack_bonus'] >= 1
    sword = next(i for i in player.inventory if i.get_stat('recipe_id') == 'copper_sword')
    game.handle_player_action('equip', item_id=sword.entity_id)
    gear = recorder.final_gear()
    assert gear['weapon']['name'] == 'Copper Sword' and gear['weapon']['stats'] == craft['stats']
    assert set(gear) == {'weapon', 'armor', 'shield'}
