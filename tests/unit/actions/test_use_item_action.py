"""UseItemAction: drink and eat from inventory through @item_effect content."""
import yaml
import pytest

from core.actions import ACTION_TYPES
from core.actions.use_item_action import UseItemAction, best_healing_item, usable_effect
from core.extensions import item_effects
from core.game import Game
from core.loot import LootGenerator


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=11)
    return g


def give(game, item_id):
    item = LootGenerator.get_instance().create_item(item_id)
    assert game.state.player.add_to_inventory(item)
    return item


def use(game, item):
    return game.handle_player_action('use', item_id=item.entity_id)


def test_potion_heals_its_amount_and_is_consumed(game):
    player = game.state.player
    player.hp = 3
    potion = give(game, 'potion_healing')
    assert use(game, potion) is True  # takes the turn
    assert player.hp == min(player.max_hp, 13)
    assert potion not in player.inventory


def test_full_healing_restores_max_hp(game):
    player = game.state.player
    player.hp = 1
    use(game, give(game, 'potion_full_healing'))
    assert player.hp == player.max_hp


def test_food_heals_over_time_not_at_once(game):
    from core.status_effects import has_effect
    from core.base.entity import EntityType
    for e in list(game.state.entities.values()):
        if e.entity_type == EntityType.MONSTER:
            game.context.remove_entity(e.entity_id)
    game.engine.turn_processor.hp_regen_amount = 0      # only the effect heals here
    game.engine.turn_processor.hp_regen_percent = 0
    player = game.state.player
    player.hp = 5
    use(game, give(game, 'bread'))
    # the use turn itself already ticked once: bread is 1 HP a turn for 6 turns
    assert has_effect(player, 'regeneration') and player.hp == 6
    for _ in range(10):
        game.engine.tick()
    assert player.hp == 11 and not has_effect(player, 'regeneration')


def test_at_full_health_nothing_is_used_and_no_turn_passes(game):
    player = game.state.player
    potion = give(game, 'potion_healing')
    turn = game.state.turn_count
    assert use(game, potion) is False
    assert potion in player.inventory and game.state.turn_count == turn


def test_unbuilt_effect_keeps_the_item(game):
    scroll = give(game, 'scroll_mapping')
    game.state.player.hp = 1
    assert use(game, scroll) is False
    assert scroll in game.state.player.inventory


def test_use_publishes_item_used(game):
    seen = []
    from core.events import GameEventType
    game.event_bus.subscribe(GameEventType.ITEM_USED, seen.append, 'test')
    game.state.player.hp = 2
    use(game, give(game, 'potion_healing'))
    assert len(seen) == 1


def test_best_healing_item_wastes_least(game):
    player = game.state.player
    small, big, full = give(game, 'potion_healing'), give(game, 'potion_extra_healing'), give(game, 'potion_full_healing')
    player.hp = player.max_hp - 2
    assert best_healing_item(player) is small          # healing (10) covers 2
    player.hp = player.max_hp - 15
    assert best_healing_item(player) is big            # cheapest that covers 15 (not the rare full)
    player.hp = 1
    big.set_stat('heal_amount', 5)
    assert best_healing_item(player) is full           # only full covers 19
    player.hp = player.max_hp
    assert best_healing_item(player) is None


def test_best_healing_item_ignores_unusable_items(game):
    give(game, 'scroll_mapping')
    game.state.player.hp = 1
    assert best_healing_item(game.state.player) is None


def test_every_healing_item_in_yaml_has_a_built_effect():
    with open('data/entities/items.yaml') as f:
        items = yaml.safe_load(f)
    healing = [i for cat in ('potions', 'food') for i in items[cat].values()
               if isinstance(i, dict) and 'heal_amount' in (i.get('stats') or {})]
    assert healing
    for item in healing:
        assert item['effect'] in item_effects, item['display_name']


def test_use_item_round_trips_for_multiplayer():
    action = UseItemAction('p1', 'i1')
    assert ACTION_TYPES['UseItemAction'].from_dict(action.to_dict()) == action


def test_instant_healers_come_before_over_time_ones(game):
    player = game.state.player
    bread, regen, potion = give(game, 'bread'), give(game, 'potion_regeneration'), give(game, 'potion_healing')
    player.hp = 1
    assert best_healing_item(player) is potion
    assert best_healing_item(player, instant_only=True) is potion
    player.remove_from_inventory(potion)
    assert best_healing_item(player) is regen          # the one that heals most (30 over 10 turns)
    assert best_healing_item(player, instant_only=True) is None


def test_regeneration_potion_heals_three_a_turn_for_ten_turns(game):
    from core.base.entity import EntityType
    from core.status_effects import effects_of
    for e in list(game.state.entities.values()):
        if e.entity_type == EntityType.MONSTER:
            game.context.remove_entity(e.entity_id)
    game.engine.turn_processor.hp_regen_amount = 0
    game.engine.turn_processor.hp_regen_percent = 0
    player = game.state.player
    player.max_hp, player.hp = 100, 10
    use(game, give(game, 'potion_regeneration'))
    assert player.hp == 13 and effects_of(player)[0]['turns_left'] == 9
    for _ in range(20):
        game.engine.tick()
    assert player.hp == 40 and effects_of(player) == []     # 10 + 30
