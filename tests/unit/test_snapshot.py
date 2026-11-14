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
