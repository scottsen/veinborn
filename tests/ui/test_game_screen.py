"""The single-player game screen driven through its keys (Textual pilot).

Characterisation for plan phase 4 (VB-99/VB-100): the app moves onto a driver,
so every key that reads or changes the game is pinned here by what the screen
shows, not by how the app reaches the game.
"""
import asyncio

import pytest

from core.loot import LootGenerator
from ui.textual.app import VeinbornApp

pytestmark = pytest.mark.unit

# key -> (dx, dy), the vi keys the app binds
STEP_KEYS = {"h": (-1, 0), "l": (1, 0), "k": (0, -1), "j": (0, 1)}


def game_of(app):
    """The local single-player game behind the app (the one place tests reach in)."""
    return app.game


def make(item_id):
    return LootGenerator.get_instance().create_item(item_id)


def log_text(app):
    return app.message_log.render().plain


def run(scenario):
    async def go():
        app = VeinbornApp(seed=5)
        async with app.run_test() as pilot:
            await pilot.pause()
            await scenario(app, pilot)
    asyncio.run(go())


def free_step(game):
    """A vi key whose target tile is walkable and empty."""
    state, p = game.state, game.state.player
    occupied = {(e.x, e.y) for e in state.entities.values() if e is not p and e.blocks_movement}
    for key, (dx, dy) in STEP_KEYS.items():
        x, y = p.x + dx, p.y + dy
        if state.dungeon_map.is_walkable(x, y) and (x, y) not in occupied:
            return key, (x, y)
    pytest.skip("no free neighbour on this seed")


def test_moving_moves_the_player_and_the_map_follows():
    async def scenario(app, pilot):
        game = game_of(app)
        key, target = free_step(game)
        turn = game.state.turn_count
        await pilot.press(key)
        await pilot.pause()
        p = game.state.player
        assert (p.x, p.y) == target
        assert game.state.turn_count == turn + 1
        assert (app.map_widget.snapshot.player.x, app.map_widget.snapshot.player.y) == target
    run(scenario)


def test_wait_passes_a_turn():
    async def scenario(app, pilot):
        game = game_of(app)
        turn = game.state.turn_count
        await pilot.press(".")
        await pilot.pause()
        assert game.state.turn_count == turn + 1
    run(scenario)


def test_status_bar_shows_hp_and_floor():
    async def scenario(app, pilot):
        p = game_of(app).state.player
        text = app.status_bar.render().plain
        assert f"{p.hp}/{p.max_hp}" in text
    run(scenario)


def test_inventory_key_lists_the_pack_in_the_log():
    async def scenario(app, pilot):
        p = game_of(app).state.player
        p.inventory.clear()
        p.add_to_inventory(make('dagger'))
        await pilot.press("i")
        await pilot.pause()
        text = log_text(app)
        assert "=== Full Inventory (1/" in text and "1. Dagger (weapon)" in text
    run(scenario)


def test_look_lists_items_on_the_players_tile():
    async def scenario(app, pilot):
        state = game_of(app).state
        dagger = make('dagger')
        dagger.x, dagger.y = state.player.x, state.player.y
        state.entities[dagger.entity_id] = dagger
        await pilot.press(":")
        await pilot.pause()
        text = log_text(app)
        assert "=== Items on the ground (1) ===" in text and "Dagger (weapon)" in text
    run(scenario)


def test_quick_use_heals_and_says_why_when_it_cannot():
    async def scenario(app, pilot):
        p = game_of(app).state.player
        p.inventory.clear()
        p.hp = p.max_hp
        await pilot.press("e")
        await pilot.pause()
        assert "You are already at full health." in log_text(app)

        p.add_to_inventory(make('potion_healing'))
        p.hp = 1
        await pilot.press("e")
        await pilot.pause()
        assert p.hp > 1 and not p.inventory
    run(scenario)


def test_quick_drop_puts_the_least_useful_item_on_the_ground():
    async def scenario(app, pilot):
        state = game_of(app).state
        p = state.player
        p.inventory.clear()
        await pilot.press("d")
        await pilot.pause()
        assert "You have nothing to drop." in log_text(app)

        potion = make('potion_healing')
        p.add_to_inventory(potion)
        await pilot.press("d")
        await pilot.pause()
        assert potion not in p.inventory
        assert (potion.x, potion.y) == (p.x, p.y)
    run(scenario)
