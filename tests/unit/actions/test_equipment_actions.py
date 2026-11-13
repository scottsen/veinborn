"""Wear, remove and list gear: EquipAction swap safety, UnequipAction, equipment_listing."""
import pytest

from core.actions import ACTION_TYPES, UnequipAction
from core.base.entity import EntityType
from core.equipment import equipment_listing
from core.game import Game
from core.loot import LootGenerator

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=11)
    p = g.state.player
    p.inventory.clear()
    p.equipped_weapon = p.equipped_armor = None
    return g


def give(game, item_id):
    item = LootGenerator.get_instance().create_item(item_id)
    assert game.state.player.add_to_inventory(item)
    return item


def fill_pack(game):
    p = game.state.player
    while p.has_room():
        give(game, 'potion_healing')


def test_swapping_gear_with_a_full_pack_keeps_the_old_gear(game):
    """The old order added the worn item back before freeing the slot: gone when the pack was full."""
    p = game.state.player
    old = give(game, 'dagger')
    assert game.handle_player_action('equip', item_id=old.entity_id) is False   # no turn
    new = give(game, 'long_sword')
    fill_pack(game)
    assert not p.has_room()

    game.handle_player_action('equip', item_id=new.entity_id)

    assert p.equipped_weapon is new
    assert old in p.inventory
    assert len(p.inventory) <= p.MAX_INVENTORY


def test_unequip_returns_gear_to_the_pack_without_a_turn(game):
    p = game.state.player
    sword = give(game, 'long_sword')
    game.handle_player_action('equip', item_id=sword.entity_id)
    attack_with = p.get_total_attack()
    turn = game.state.turn_count

    assert game.handle_player_action('unequip', slot='weapon') is False
    assert p.equipped_weapon is None
    assert sword in p.inventory
    assert p.get_total_attack() < attack_with
    assert game.state.turn_count == turn


def test_unequip_armor_slot(game):
    p = game.state.player
    mail = give(game, 'chainmail')
    game.handle_player_action('equip', item_id=mail.entity_id)
    game.handle_player_action('unequip', slot='armor')
    assert p.equipped_armor is None and mail in p.inventory


def test_unequip_with_a_full_pack_keeps_the_gear_on(game):
    p = game.state.player
    sword = give(game, 'long_sword')
    game.handle_player_action('equip', item_id=sword.entity_id)
    fill_pack(game)

    game.handle_player_action('unequip', slot='weapon')

    assert p.equipped_weapon is sword
    assert any('pack is full' in m for m in game.state.messages[-3:])


def test_unequip_empty_or_unknown_slot_fails_cleanly(game):
    p = game.state.player
    game.handle_player_action('unequip', slot='armor')
    assert any('no armor equipped' in m for m in game.state.messages[-3:])
    n = len(p.inventory)
    game.handle_player_action('unequip', slot='ring')
    game.handle_player_action('unequip')
    assert len(p.inventory) == n


def test_equip_refuses_non_gear(game):
    item = give(game, 'potion_healing')
    game.handle_player_action('equip', item_id=item.entity_id)
    p = game.state.player
    assert p.equipped_weapon is None and p.equipped_armor is None and p.equipped_shield is None


def test_shield_is_worn_alongside_armor_and_adds_defense(game):
    p = game.state.player
    base = p.get_total_defense()
    mail = give(game, 'chainmail')
    shield = give(game, 'shield')
    game.handle_player_action('equip', item_id=mail.entity_id)
    with_mail = p.get_total_defense()
    game.handle_player_action('equip', item_id=shield.entity_id)

    assert p.equipped_shield is shield and p.equipped_armor is mail   # separate slots
    assert shield not in p.inventory
    assert p.get_total_defense() == with_mail + shield.get_stat('defense_bonus') > base

    game.handle_player_action('unequip', slot='shield')
    assert p.equipped_shield is None and shield in p.inventory
    assert p.get_total_defense() == with_mail


def test_second_shield_swaps_and_the_old_one_returns_to_the_pack(game):
    p = game.state.player
    first, second = give(game, 'shield'), give(game, 'shield')
    second.set_stat('defense_bonus', 5)
    game.handle_player_action('equip', item_id=first.entity_id)
    game.handle_player_action('equip', item_id=second.entity_id)
    assert p.equipped_shield is second and first in p.inventory


def test_a_worse_spare_shield_is_junk_a_better_one_is_not(game):
    from core.actions.drop_action import WORSE_GEAR, usefulness
    p = game.state.player
    worn = give(game, 'shield')
    game.handle_player_action('equip', item_id=worn.entity_id)
    spare = give(game, 'shield')
    assert usefulness(p, spare) == WORSE_GEAR
    spare.set_stat('defense_bonus', worn.get_stat('defense_bonus') + 1)
    assert usefulness(p, spare) != WORSE_GEAR


def test_unequip_action_round_trips_for_the_server():
    action = UnequipAction(actor_id='p1', slot='armor')
    assert ACTION_TYPES['UnequipAction'].from_dict(action.to_dict()) == action


def test_listing_shows_worn_slots_and_only_wearable_pack_items(game):
    p = game.state.player
    dagger = give(game, 'dagger')
    sword = give(game, 'long_sword')
    give(game, 'potion_healing')
    shield = give(game, 'shield')
    game.handle_player_action('equip', item_id=dagger.entity_id)

    worn, carried = equipment_listing(p)

    assert [(l.slot, l.item) for l in worn] == [('weapon', dagger), ('armor', None), ('shield', None)]
    assert [l.item for l in carried] == [sword, shield]         # the potion is not gear
    assert carried[0].change == carried[0].bonus - worn[0].bonus > 0
    assert worn[1].text() == "Armor: (nothing)"
    assert "vs worn" in carried[0].text()


def test_listing_empty_slot_change_is_the_whole_bonus(game):
    mail = give(game, 'chainmail')
    _, carried = equipment_listing(game.state.player)
    assert carried[0].item is mail and carried[0].change == carried[0].bonus
