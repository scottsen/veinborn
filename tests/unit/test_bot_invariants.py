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
