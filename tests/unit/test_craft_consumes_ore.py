"""Crafting must consume real ore; finished equipment is never ore.

Regression: create_equipment tagged every crafted item with ore_type, so a Copper
Dagger counted as copper ore and a forge turned daggers into daggers forever
(found by the fuzz bots: 139 'Crafted Copper Dagger!' from 5 mined ore).
"""

import pytest

from src.core.actions.craft_action import CraftAction
from src.core.base.entity import EntityType
from src.core.crafting import RecipeManager, is_ore_item
from src.core.entity_loader import EntityLoader
from src.core.game import Game


pytestmark = pytest.mark.unit


@pytest.fixture
def forge_game():
    game = Game()
    game.start_new_game(seed=3, player_name="Crafter")
    ctx, player = game.context, game.state.player
    forge = ctx.get_entities_by_type(EntityType.FORGE)[0]
    player.x, player.y = forge.x + 1, forge.y
    return ctx, player, forge


def _copper_ore(n):
    vein = EntityLoader().create_ore_vein('copper', 0, 0, floor=1)
    return [vein.get_ore_item() for _ in range(n)]


def _craft(ctx, player, forge, recipe_id='copper_dagger'):
    return CraftAction(player.entity_id, forge.entity_id, recipe_id).execute(ctx)


def test_each_craft_consumes_ore_and_stops_when_out(forge_game):
    ctx, player, forge = forge_game
    for ore in _copper_ore(2):
        player.add_to_inventory(ore)

    assert _craft(ctx, player, forge).result.value == 'success'
    assert _craft(ctx, player, forge).result.value == 'success'

    assert len(player.inventory) == 2                       # two daggers, no ore left
    assert not any(is_ore_item(i) for i in player.inventory)
    third = _craft(ctx, player, forge)
    assert third.result.value != 'success'
    assert len(player.inventory) == 2                       # nothing created from daggers


def test_crafted_equipment_is_not_ore(forge_game):
    ctx, player, forge = forge_game
    player.add_to_inventory(_copper_ore(1)[0])
    _craft(ctx, player, forge)

    dagger = player.inventory[0]
    assert dagger.get_stat('equipment_slot')
    assert not is_ore_item(dagger)
    assert dagger.get_stat('ore_type') in (None, 0)
    assert dagger.get_stat('crafted_ore_type') == 'copper'
    assert RecipeManager().get_craftable_recipes(player.inventory, 1) == []


def test_old_saves_with_tagged_equipment_are_not_ore(forge_game):
    """Equipment saved before the fix still carries ore_type; it must not count."""
    ctx, player, forge = forge_game
    player.add_to_inventory(_copper_ore(1)[0])
    _craft(ctx, player, forge)
    legacy_dagger = player.inventory[0]
    legacy_dagger.set_stat('ore_type', 'copper')

    assert not is_ore_item(legacy_dagger)
    assert _craft(ctx, player, forge).result.value != 'success'
