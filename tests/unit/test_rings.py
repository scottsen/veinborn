"""Ring slot (VB-130): ring_protection, ring_strength and ring_regeneration drop, so they must be wearable.

One ring is worn alongside weapon, armor and shield. Strength and protection add to the totals
combat reads; regeneration adds HP to every natural-regeneration tick. The slot is saved,
shown in the snapshot, listed on the equipment screen and worn by the bots like any gear upgrade.
"""
import json

import pytest

from core.actions.drop_action import OTHER, WORSE_GEAR, usefulness
from core.equipment import GEAR_SLOTS, equipment_listing, gear_bonus, gear_slot
from core.game import Game
from core.loot import LootGenerator
from core.snapshot import Snapshot
from core.turn_processor import apply_hp_regeneration

pytestmark = pytest.mark.unit

DROPPED_RINGS = ('ring_protection', 'ring_strength', 'ring_regeneration')


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=17)
    p = g.state.player
    p.inventory.clear()
    p.equipped_weapon = p.equipped_armor = p.equipped_shield = p.equipped_ring = None
    return g


def give(game, item_id, **stats):
    item = LootGenerator.get_instance().create_item(item_id)
    for k, v in stats.items():
        item.set_stat(k, v)
    assert game.state.player.add_to_inventory(item)
    return item


def wear(game, item):
    game.handle_player_action('equip', item_id=item.entity_id)


# --- the data: everything that can drop can be worn and does something ---------------------

def _ring_ids_in_loot_tables():
    ids = set()
    for table in LootGenerator.get_instance().loot_tables.values():
        for category in table.values():
            if isinstance(category, dict):
                ids |= {e['id'] for e in category.get('items', []) if e['id'].startswith('ring_')}
    return ids


def test_every_ring_in_a_loot_table_can_be_worn_and_does_something():
    ids = _ring_ids_in_loot_tables()
    assert ids == set(DROPPED_RINGS)            # a new ring in a table must come with a test here
    for item_id in ids:
        item = LootGenerator.get_instance().create_item(item_id)
        assert gear_slot(item) == 'ring', f"{item_id} drops but cannot be worn"
        assert gear_bonus(item, 'ring') > 0, f"{item_id} grants nothing the game reads"


def test_a_ring_dropped_by_a_troll_can_be_picked_up_and_worn(game):
    from core.rng import GameRNG
    loot = LootGenerator.get_instance()
    dropped = []
    for seed in range(400):
        dropped = [i for i in loot.generate_loot('troll', 1, GameRNG(seed)) if gear_slot(i) == 'ring']
        if dropped:
            break
    assert dropped, "no ring in 400 troll drops (10% chance each)"
    ring = dropped[0]
    assert game.state.player.add_to_inventory(ring)
    wear(game, ring)
    assert game.state.player.equipped_ring is ring


def test_ring_is_a_gear_slot():
    assert 'ring' in GEAR_SLOTS


# --- strength and protection feed the combat totals ----------------------------------------

def test_ring_of_strength_adds_attack_only(game):
    p = game.state.player
    attack, defense = p.get_total_attack(), p.get_total_defense()
    ring = give(game, 'ring_strength')
    wear(game, ring)
    assert p.equipped_ring is ring and ring not in p.inventory
    assert p.get_total_attack() == attack + ring.get_stat('attack_bonus') > attack
    assert p.get_total_defense() == defense


def test_ring_of_protection_adds_defense_only(game):
    p = game.state.player
    attack, defense = p.get_total_attack(), p.get_total_defense()
    ring = give(game, 'ring_protection')
    wear(game, ring)
    assert p.get_total_defense() == defense + ring.get_stat('defense_bonus') > defense
    assert p.get_total_attack() == attack


@pytest.mark.parametrize('item_id, words', [('ring_regeneration', 'regen'), ('ring_strength', '+1 attack'),
                                            ('ring_protection', '+1 defense')])
def test_the_equip_message_says_what_the_ring_grants(game, item_id, words):
    wear(game, give(game, item_id))
    assert any(f"Equipped" in m and words in m for m in game.state.messages[-4:]), game.state.messages[-4:]


def test_a_ring_is_worn_with_weapon_armor_and_shield(game):
    p = game.state.player
    items = [give(game, i) for i in ('long_sword', 'chainmail', 'shield', 'ring_strength')]
    for item in items:
        wear(game, item)
    assert (p.equipped_weapon, p.equipped_armor, p.equipped_shield, p.equipped_ring) == tuple(items)
    assert p.inventory == []


def test_remove_ring_restores_totals_and_returns_it_to_the_pack(game):
    p = game.state.player
    attack = p.get_total_attack()
    ring = give(game, 'ring_strength')
    wear(game, ring)
    game.handle_player_action('unequip', slot='ring')
    assert p.equipped_ring is None and ring in p.inventory
    assert p.get_total_attack() == attack


def test_remove_with_no_ring_worn_fails_cleanly(game):
    game.handle_player_action('unequip', slot='ring')
    assert game.state.player.equipped_ring is None


def test_second_ring_swaps_and_the_old_one_survives_a_full_pack(game):
    p = game.state.player
    first, second = give(game, 'ring_strength'), give(game, 'ring_protection')
    wear(game, first)
    while p.has_room():
        give(game, 'potion_healing')
    wear(game, second)
    assert p.equipped_ring is second and first in p.inventory
    assert len(p.inventory) <= p.MAX_INVENTORY


# --- regeneration ------------------------------------------------------------------------

def test_ring_of_regeneration_adds_to_every_natural_tick(game):
    p = game.state.player
    p.max_hp, p.hp = 100, 10
    apply_hp_regeneration([p], 10, 10, 1)            # 1 HP minimum tick, no percent
    plain = p.hp - 10
    ring = give(game, 'ring_regeneration')
    wear(game, ring)
    p.hp = 10
    apply_hp_regeneration([p], 10, 10, 1)
    assert p.hp - 10 == plain + ring.get_stat('regen_rate') > plain


def test_ring_regeneration_in_the_real_turn_loop_and_never_past_max_hp(game):
    g = game
    g.state.entities.clear()
    p = g.state.player
    g.state.entities[p.entity_id] = p
    p.max_hp, p.hp = 100, 10
    for _ in range(20):
        g.engine.tick()
    plain = p.hp - 10
    wear(g, give(g, 'ring_regeneration'))
    p.hp = 10
    for _ in range(20):
        g.engine.tick()
    assert p.hp - 10 > plain
    p.hp = p.max_hp - 1
    for _ in range(10):
        g.engine.tick()
    assert p.hp == p.max_hp


def test_other_rings_do_not_change_regeneration(game):
    p = game.state.player
    wear(game, give(game, 'ring_protection'))
    p.max_hp, p.hp = 100, 10
    apply_hp_regeneration([p], 10, 10, 1)
    assert p.hp == 11


def test_a_player_without_gear_slots_still_regenerates():
    class Plain:                                  # a stand-in with no equipment attributes at all
        hp, max_hp, is_alive, name = 1, 50, True, 'x'

        def heal(self, n):
            self.hp += n
            return n
    p = Plain()
    apply_hp_regeneration([p], 10, 10, 1)
    assert p.hp == 2


# --- what is worth carrying --------------------------------------------------------------

def test_a_spare_ring_is_worth_wearing_only_if_it_beats_the_worn_one(game):
    p = game.state.player
    assert usefulness(p, give(game, 'ring_strength')) == OTHER          # nothing worn: wear it
    worn = give(game, 'ring_protection')
    wear(game, worn)
    same = give(game, 'ring_strength')                                  # +1 attack vs +1 defense
    assert usefulness(p, same) == WORSE_GEAR
    better = give(game, 'ring_strength', attack_bonus=3)
    assert usefulness(p, better) == OTHER


def test_bots_wear_a_ring_upgrade_and_leave_a_worse_one():
    from tests.fuzz.services.perception_service import PerceptionService
    g = Game()
    g.start_new_game(seed=19)
    p = g.state.player
    p.inventory.clear()
    p.equipped_weapon = p.equipped_armor = p.equipped_shield = p.equipped_ring = None
    ring = give(g, 'ring_strength')
    perception = PerceptionService()
    assert perception.has_unequipped_gear(g) is ring
    wear(g, ring)
    spare = give(g, 'ring_protection')
    assert perception.has_unequipped_gear(g) is None, "an equal ring is not an upgrade"
    spare.set_stat('defense_bonus', 4)
    assert perception.has_unequipped_gear(g) is spare


# --- save / load -------------------------------------------------------------------------

def test_worn_ring_survives_save_and_load_and_old_saves_load_without_one(game):
    from core.save_load import SaveSystem
    system = SaveSystem.__new__(SaveSystem)
    p = game.state.player
    ring = give(game, 'ring_regeneration')
    wear(game, ring)
    data = system._serialize_entity(p)
    back = system._deserialize_entity(json.loads(json.dumps(data)))
    assert back.equipped_ring.name == ring.name
    assert back.equipped_ring.get_stat('regen_rate') == ring.get_stat('regen_rate')
    data.pop('equipped_ring')                                           # a save from before VB-130
    assert system._deserialize_entity(data).equipped_ring is None


def test_ring_bonus_is_not_applied_twice_after_a_load(game):
    from core.save_load import SaveSystem
    system = SaveSystem.__new__(SaveSystem)
    p = game.state.player
    wear(game, give(game, 'ring_strength'))
    attack = p.get_total_attack()
    back = system._deserialize_entity(json.loads(json.dumps(system._serialize_entity(p))))
    assert back.get_total_attack() == attack


# --- snapshot, wire and equipment screen -------------------------------------------------

def test_snapshot_carries_the_worn_ring_over_the_wire(game):
    ring = give(game, 'ring_regeneration')
    wear(game, ring)
    snap = game.engine.snapshot()
    view = snap.player.ring
    assert view.name == ring.name and view.slot == 'ring' and view.stats == {'regen_rate': 2}
    back = Snapshot.from_dict(json.loads(json.dumps(snap.to_dict())))
    assert back.player.ring == view


def test_snapshot_without_a_ring_has_none_and_totals_include_the_ring(game):
    p = game.state.player
    assert game.engine.snapshot().player.ring is None
    wear(game, give(game, 'ring_strength'))
    assert game.engine.snapshot().player.attack == p.get_total_attack()


def test_pack_ring_is_listed_as_wearable_with_a_diff_against_the_worn_one(game):
    wear(game, give(game, 'ring_protection'))
    give(game, 'ring_strength')
    worn, carried = equipment_listing(game.engine.snapshot().player)
    ring_line = next(line for line in worn if line.slot == 'ring')
    assert ring_line.item is not None and 'defense' in ring_line.text()
    assert [c.slot for c in carried] == ['ring']
    assert carried[0].diff == {'attack_bonus': 1, 'defense_bonus': -1}


def test_empty_ring_slot_is_listed_as_nothing(game):
    worn, _ = equipment_listing(game.engine.snapshot().player)
    line = next(line for line in worn if line.slot == 'ring')
    assert line.item is None and line.text() == "Ring: (nothing)"


def test_a_ring_is_not_ore_or_a_part_and_shows_in_the_pack_listing(game):
    ring = give(game, 'ring_strength')
    view = next(i for i in game.engine.snapshot().player.inventory if i.entity_id == ring.entity_id)
    assert view.slot == 'ring' and view.ore is None and view.part is None
