"""Crafting v2 phase 1 (VB-114): combat reads accuracy, max_hp_bonus and spell_power from worn gear.

Each is 0 on plain gear and monsters, so nothing changes until crafted parts carry them.
"""
import pytest

from core.actions.attack_action import AttackAction
from core.content.abilities.force_bolt import roll_damage
from core.equipment import gear_total
from core.game import Game
from core.loot import LootGenerator

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=13)
    p = g.state.player
    p.inventory.clear()
    p.equipped_weapon = p.equipped_armor = p.equipped_shield = None
    return g


def give(game, item_id, **stats):
    item = LootGenerator.get_instance().create_item(item_id)
    for k, v in stats.items():
        item.set_stat(k, v)
    assert game.state.player.add_to_inventory(item)
    return item


def equip(game, item):
    game.handle_player_action('equip', item_id=item.entity_id)


def monster(game):
    p = game.state.player
    m = game.entity_loader.create_monster("orc", p.x + 1, p.y)
    game.context.add_entity(m)
    return m


# -- accuracy -----------------------------------------------------------------

def test_accuracy_raises_hit_chance_and_zero_changes_nothing():
    base = AttackAction.hit_chance(3, 3)
    assert AttackAction.hit_chance(3, 3, 0) == base
    assert AttackAction.hit_chance(3, 3, 4) > base


def test_natural_one_still_misses_with_any_accuracy():
    to_hit = {'die': 20, 'formula': "roll + attacker_attack + attacker_accuracy >= 10 + defender_defense",
              'natural_miss': 1, 'natural_hit': 20}
    assert not AttackAction._hits_on(1, 0, 0, to_hit, accuracy=99)
    assert AttackAction._hits_on(2, 0, 0, to_hit, accuracy=99)


def test_worn_weapon_accuracy_reaches_the_attack(game):
    target = monster(game)
    target.defense = 20                  # so the player misses often and accuracy can show
    player = game.state.player
    plain = AttackAction.expected_damage(player, target)
    equip(game, give(game, 'long_sword', accuracy=0))
    no_acc = AttackAction.expected_damage(player, target)
    player.equipped_weapon.set_stat('accuracy', 5)
    assert player.get_total_accuracy() == 5 and AttackAction._accuracy(player) == 5
    assert AttackAction.expected_damage(player, target) > no_acc >= plain


def test_monsters_have_no_accuracy(game):
    assert AttackAction._accuracy(monster(game)) == 0


# -- max HP while worn ----------------------------------------------------------

def test_max_hp_bonus_comes_and_goes_with_the_armor(game):
    p = game.state.player
    base_max, hp = p.max_hp, p.hp
    vest = give(game, 'chainmail', max_hp_bonus=6)
    equip(game, vest)
    assert p.max_hp == base_max + 6 and p.hp == hp          # not topped up
    p.hp = p.max_hp
    game.handle_player_action('unequip', slot='armor')
    assert p.max_hp == base_max and p.hp == base_max        # clamped to the new maximum


def test_swapping_armor_applies_the_difference_once(game):
    p = game.state.player
    base_max = p.max_hp
    equip(game, give(game, 'chainmail', max_hp_bonus=6))
    equip(game, give(game, 'chainmail', max_hp_bonus=2))
    assert p.max_hp == base_max + 2


def test_losing_the_bonus_never_kills(game):
    p = game.state.player
    equip(game, give(game, 'chainmail', max_hp_bonus=p.max_hp + 10))
    p.hp = 1
    game.handle_player_action('unequip', slot='armor')
    assert p.hp == 1 and p.max_hp >= 1


def test_saved_max_hp_is_not_bonused_twice(game, tmp_path):
    from core.save_load import SaveSystem
    p = game.state.player
    equip(game, give(game, 'chainmail', max_hp_bonus=6))
    system = SaveSystem(save_dir=tmp_path)
    system.save_game(game.state, "hp")
    loaded = system.load_game("hp").player
    assert loaded.max_hp == p.max_hp
    assert loaded.equipped_armor.get_stat('max_hp_bonus') == 6


# -- spell power -------------------------------------------------------------------

def test_spell_power_adds_to_direct_damage_spells(game):
    p = game.state.player
    config = {'damage': 4}
    assert roll_damage(game.context, p, config) == 4
    equip(game, give(game, 'long_sword', spell_power=3))
    assert gear_total(p, 'spell_power') == 3
    assert roll_damage(game.context, p, config) == 7


def test_monster_spells_ignore_spell_power(game):
    assert roll_damage(game.context, monster(game), {'damage': 4}) == 4
