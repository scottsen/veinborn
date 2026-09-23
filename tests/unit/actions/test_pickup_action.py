"""Unit tests for PickupAction.execute() game logic (VB-28)."""
import pytest

from core.actions.pickup_action import PickupAction
from core.base.entity import Entity, EntityType

pytestmark = pytest.mark.unit

INVENTORY_LIMIT = 20  # Player.add_to_inventory


def _place_item(context, name, x, y, alive=True):
    item = Entity(entity_type=EntityType.ITEM, name=name, x=x, y=y)
    item.is_alive = alive
    context.game_state.entities[item.entity_id] = item
    return item


def _pickup(context):
    player = context.get_player()
    return player, PickupAction(actor_id=player.entity_id).execute(context)


def test_no_items_is_free_and_reports_it(game_context):
    _, outcome = _pickup(game_context)
    assert outcome.is_success
    assert outcome.took_turn is False
    assert outcome.messages == ["There are no items here to pick up."]
    assert outcome.events == []


def test_unknown_actor_fails(game_context):
    outcome = PickupAction(actor_id="does-not-exist").execute(game_context)
    assert not outcome.is_success


def test_picks_up_single_item(game_context):
    player = game_context.get_player()
    item = _place_item(game_context, "Iron Ring", player.x, player.y)

    _, outcome = _pickup(game_context)

    assert outcome.is_success and outcome.took_turn is True
    assert item in player.inventory
    assert (item.x, item.y) == (None, None)
    assert outcome.messages == ["Picked up Iron Ring"]
    assert [e['type'] for e in outcome.events] == ['item_picked_up']
    assert outcome.events[0]['item_id'] == item.entity_id


def test_picks_up_every_item_on_the_tile(game_context):
    player = game_context.get_player()
    items = [_place_item(game_context, n, player.x, player.y) for n in ("A", "B", "C")]

    _, outcome = _pickup(game_context)

    assert all(i in player.inventory for i in items)
    assert len(outcome.events) == 3
    assert outcome.messages == ["Picked up 3 items: A, B, C"]


def test_ignores_items_elsewhere_and_dead_items(game_context):
    player = game_context.get_player()
    elsewhere = _place_item(game_context, "Far", player.x + 1, player.y)
    dead = _place_item(game_context, "Dead", player.x, player.y, alive=False)

    _, outcome = _pickup(game_context)

    assert outcome.took_turn is False
    assert elsewhere not in player.inventory and dead not in player.inventory
    assert elsewhere.x == player.x + 1


def test_ignores_non_item_entities_on_the_tile(game_context):
    player = game_context.get_player()
    ore = Entity(entity_type=EntityType.ORE_VEIN, name="Ore", x=player.x, y=player.y)
    game_context.game_state.entities[ore.entity_id] = ore

    _, outcome = _pickup(game_context)

    assert outcome.took_turn is False
    assert ore not in player.inventory


def test_partial_pickup_when_inventory_nearly_full(game_context):
    player = game_context.get_player()
    for i in range(INVENTORY_LIMIT - 1):
        player.inventory.append(Entity(entity_type=EntityType.ITEM, name=f"Junk{i}"))
    first = _place_item(game_context, "First", player.x, player.y)
    second = _place_item(game_context, "Second", player.x, player.y)

    _, outcome = _pickup(game_context)

    assert outcome.took_turn is True
    assert len(player.inventory) == INVENTORY_LIMIT
    assert sum(i in player.inventory for i in (first, second)) == 1
    left_behind = second if first in player.inventory else first
    assert (left_behind.x, left_behind.y) == (player.x, player.y)
    assert any(m.startswith("Picked up") for m in outcome.messages)
    assert any("Inventory full! Could not pick up" in m for m in outcome.messages)
    assert len(outcome.events) == 1


def test_full_inventory_picks_up_nothing_and_costs_no_turn(game_context):
    player = game_context.get_player()
    for i in range(INVENTORY_LIMIT):
        player.inventory.append(Entity(entity_type=EntityType.ITEM, name=f"Junk{i}"))
    item = _place_item(game_context, "Loot", player.x, player.y)

    _, outcome = _pickup(game_context)

    assert outcome.is_success
    assert outcome.took_turn is False
    assert outcome.events == []
    assert item not in player.inventory
    assert (item.x, item.y) == (player.x, player.y)
    assert outcome.messages == ["Inventory full! Could not pick up Loot"]


def test_full_inventory_multiple_items_message(game_context):
    player = game_context.get_player()
    for i in range(INVENTORY_LIMIT):
        player.inventory.append(Entity(entity_type=EntityType.ITEM, name=f"Junk{i}"))
    _place_item(game_context, "X", player.x, player.y)
    _place_item(game_context, "Y", player.x, player.y)

    _, outcome = _pickup(game_context)

    assert outcome.messages == ["Inventory full! Could not pick up 2 items"]


def test_pickup_round_trip_serialization():
    a = PickupAction(actor_id="p1")
    assert PickupAction.from_dict(a.to_dict()).actor_id == "p1"
