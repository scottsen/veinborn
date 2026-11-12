"""DropAction and least_useful_item (VB-73): the pack can be emptied of what has no use."""
import pytest

from core.actions import ACTION_TYPES
from core.actions.drop_action import (
    DropAction, HEALING, NO_USE, ORE, WORSE_GEAR, least_useful_item, usefulness,
)
from core.base.entity import EntityType
from core.game import Game
from core.loot import LootGenerator

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=11)
    p = g.state.player
    for e in list(g.state.entities.values()):   # an empty tile and a known pack
        if e.entity_type == EntityType.ITEM and e.x == p.x and e.y == p.y:
            g.context.remove_entity(e.entity_id)
    p.inventory.clear()
    return g


def give(game, item_id):
    item = LootGenerator.get_instance().create_item(item_id)
    assert game.state.player.add_to_inventory(item)
    return item


def items_here(game):
    p = game.state.player
    return [e for e in game.state.entities.values()
            if e.entity_type == EntityType.ITEM and e.x == p.x and e.y == p.y]


def test_drop_puts_the_item_on_the_tile_and_takes_a_turn(game):
    shield = give(game, 'shield')
    turn = game.state.turn_count
    assert game.handle_player_action('drop', item_id=shield.entity_id)
    assert shield not in game.state.player.inventory
    assert items_here(game) == [shield]
    assert game.state.turn_count == turn + 1


def test_dropping_what_you_do_not_carry_fails_without_a_turn(game):
    turn = game.state.turn_count
    assert not game.handle_player_action('drop', item_id='no-such-item')
    assert game.state.turn_count == turn


def test_autopickup_leaves_your_own_drop_but_pickup_takes_it(game):
    sword = give(game, 'long_sword')                 # weapons are autopickup by default
    game.handle_player_action('drop', item_id=sword.entity_id)
    p = game.state.player
    m = game.state.dungeon_map
    step = next(((dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                 if m.is_walkable(p.x + dx, p.y + dy)
                 and not any(e.x == p.x + dx and e.y == p.y + dy and e.entity_type != EntityType.ITEM
                             for e in game.state.entities.values() if e.is_alive)), None)
    if step is None:
        pytest.skip("no free tile beside the player")
    game.handle_player_action('move', dx=step[0], dy=step[1])
    game.handle_player_action('move', dx=-step[0], dy=-step[1])
    assert sword not in p.inventory                  # walked back over it: still on the floor
    game.handle_player_action('pickup')
    assert sword in p.inventory


def test_usefulness_tiers(game):
    p = game.state.player
    assert usefulness(p, give(game, 'shield')) == NO_USE          # no slot exists (VB-72)
    assert usefulness(p, give(game, 'scroll_identify')) == NO_USE  # effect not built
    assert usefulness(p, give(game, 'gold_pile_small')) == NO_USE
    assert usefulness(p, give(game, 'potion_healing')) == HEALING
    weak = LootGenerator.get_instance().create_item('dagger')
    if p.equipped_weapon is not None and weak.get_stat('attack_bonus') <= p.equipped_weapon.get_stat('attack_bonus', 0):
        assert usefulness(p, weak) == WORSE_GEAR


def test_least_useful_drops_junk_before_gear_ore_and_healing(game):
    potion = give(game, 'potion_healing')
    shield = give(game, 'shield')                     # value 25
    gold = give(game, 'gold_pile_small')
    p = game.state.player
    first = least_useful_item(p)
    assert first in (shield, gold) and usefulness(p, first) == NO_USE
    p.remove_from_inventory(shield)
    p.remove_from_inventory(gold)
    assert least_useful_item(p, max_tier=WORSE_GEAR) is None    # only healing left
    assert least_useful_item(p) is potion


def test_ore_goes_lowest_purity_first(game):
    p = game.state.player
    ores = []
    for purity in (90, 40, 70):
        item = LootGenerator.get_instance().create_item('dagger')   # any entity carrying ore stats
        item.set_stat('ore_type', 'iron')
        item.set_stat('purity', purity)
        p.add_to_inventory(item)
        ores.append(item)
    assert least_useful_item(p) is ores[1]
    assert usefulness(p, ores[1]) == ORE


def test_drop_round_trips_for_multiplayer():
    action = DropAction('p1', 'i1')
    assert ACTION_TYPES['DropAction'].from_dict(action.to_dict()) == action
