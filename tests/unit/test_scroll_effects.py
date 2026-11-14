"""Scrolls a human can read (VB-128 follow-up): enchant, teleport, identify."""
import pytest

from core.actions.use_item_action import UseItemAction, usable_effect
from core.base.entity import EntityType
from core.game import Game
from core.loot import LootGenerator

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=3, player_name="Reader")
    g.state.player.inventory.clear()
    return g


def scroll(game, item_id):
    item = LootGenerator.get_instance().create_item(item_id)
    assert game.state.player.add_to_inventory(item)
    return item


def read(game, item):
    return UseItemAction(game.state.player.entity_id, item.entity_id).execute(game.context)


@pytest.mark.parametrize('item_id', ['scroll_enchant_weapon', 'scroll_enchant_armor',
                                     'scroll_teleport', 'scroll_identify'])
def test_scrolls_are_usable(item_id):
    assert usable_effect(LootGenerator.get_instance().create_item(item_id)) == \
        LootGenerator.get_instance().items[item_id]['effect']        # positive control: it has one


def test_enchant_weapon_adds_to_the_worn_weapon_and_is_used_up(game):
    p = game.state.player
    from core.equipment import wear
    wear(p, 'weapon', LootGenerator.get_instance().create_item('dagger'))
    before = p.equipped_weapon.get_stat('attack_bonus', 0)
    atk = p.get_total_attack()
    s = scroll(game, 'scroll_enchant_weapon')
    out = read(game, s)
    assert out.is_success and out.took_turn
    assert p.equipped_weapon.get_stat('attack_bonus') == before + 1
    assert p.get_total_attack() == atk + 1 and s not in p.inventory


def test_enchant_armor_adds_defense(game):
    p = game.state.player
    p.equipped_armor = LootGenerator.get_instance().create_item('leather_armor')
    before = p.equipped_armor.get_stat('defense_bonus')
    read(game, scroll(game, 'scroll_enchant_armor'))
    assert p.equipped_armor.get_stat('defense_bonus') == before + 1


def test_enchant_with_nothing_worn_keeps_the_scroll_and_the_turn(game):
    p = game.state.player
    p.equipped_weapon = None
    s = scroll(game, 'scroll_enchant_weapon')
    out = read(game, s)
    assert not out.is_success
    assert s in p.inventory                                            # not used up


def test_teleport_moves_to_a_free_walkable_tile(game):
    p = game.state.player
    start = (p.x, p.y)
    s = scroll(game, 'scroll_teleport')
    out = read(game, s)
    assert out.is_success and (p.x, p.y) != start
    assert game.state.dungeon_map.is_walkable(p.x, p.y)
    others = [e for e in game.state.entities.values()
              if e is not p and e.x == p.x and e.y == p.y and e.entity_type != EntityType.ITEM]
    assert others == []


def test_identify_surveys_nearby_veins_only(game):
    p = game.state.player
    veins = game.context.get_entities_by_type(EntityType.ORE_VEIN)
    near = [v for v in veins if max(abs(v.x - p.x), abs(v.y - p.y)) <= 8]
    far = [v for v in veins if max(abs(v.x - p.x), abs(v.y - p.y)) > 8]
    assert near and far, "fixture needs veins on both sides of the radius"
    out = read(game, scroll(game, 'scroll_identify'))
    assert out.is_success
    assert all(v.get_stat('surveyed') for v in near)
    assert not any(v.get_stat('surveyed') for v in far)


def test_identify_with_nothing_to_learn_is_not_used_up(game):
    p = game.state.player
    for v in game.context.get_entities_by_type(EntityType.ORE_VEIN):
        v.set_stat('surveyed', True)
    s = scroll(game, 'scroll_identify')
    assert not read(game, s).is_success and s in p.inventory


def test_strength_potion_adds_attack_for_its_duration(game):
    from core.snapshot import build_snapshot
    from core.status_effects import tick_effects
    p = game.state.player
    base = p.get_total_attack()
    out = read(game, scroll(game, 'potion_strength'))
    assert out.is_success and p.get_total_attack() == base + 2
    view = build_snapshot(game.state).player
    assert view.attack == base + 2
    effect = next(e for e in view.effects if e.name == 'strength')
    assert effect.label == 'Strength' and not effect.per_turn and effect.turns_left == 100
    for _ in range(100):
        tick_effects(game.context, p)
    assert p.get_total_attack() == base                               # it wore off


def test_regeneration_is_still_per_turn(game):
    from core.snapshot import build_snapshot
    p = game.state.player
    p.hp = 1
    read(game, scroll(game, 'potion_regeneration'))
    assert next(e for e in build_snapshot(game.state).player.effects if e.name == 'regeneration').per_turn
