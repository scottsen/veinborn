"""items_here, inventory_listing and the message text the TUI shows."""
import pytest

from core.game import Game
from core.item_listing import (
    ground_messages, inventory_listing, inventory_messages, items_here,
)
from core.loot import LootGenerator

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=11)
    g.state.player.inventory.clear()
    return g


def make(item_id):
    return LootGenerator.get_instance().create_item(item_id)


def test_empty_pack_and_empty_ground(game):
    p = game.state.player
    assert inventory_listing(p) == []
    assert inventory_messages(p) == ["Your inventory is empty."]
    assert ground_messages([]) == ["There are no items on the ground here."]


def test_inventory_messages_are_numbered_in_pack_order(game):
    p = game.state.player
    p.add_to_inventory(make('dagger'))
    p.add_to_inventory(make('potion_healing'))
    msgs = inventory_messages(p)
    assert msgs[0].startswith("=== Full Inventory (2/")
    assert msgs[1].startswith("  1. ") and msgs[2].startswith("  2. ")
    assert [l.name for l in inventory_listing(p)] == [m.split('. ', 1)[1].rsplit(' (', 1)[0] for m in msgs[1:3]]


def test_items_here_finds_only_living_items_on_the_players_tile(game):
    st, p = game.state, game.state.player
    here, elsewhere = make('dagger'), make('long_sword')
    here.x, here.y = p.x, p.y
    elsewhere.x, elsewhere.y = p.x + 1, p.y
    st.entities[here.entity_id] = here
    st.entities[elsewhere.entity_id] = elsewhere
    found = items_here(st)
    assert [l.entity_id for l in found] == [here.entity_id]
    msgs = ground_messages(found)
    assert msgs[0] == "=== Items on the ground (1) ===" and found[0].text in msgs[1]
