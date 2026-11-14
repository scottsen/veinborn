"""The UI plays any GameDriver (plan D6, VB-100): LocalDriver, and a stand-in for a remote one."""
import asyncio

import pytest

from core.game import Game
from core.loot import LootGenerator
from core.snapshot import build_snapshot
from ui.driver import LocalDriver
from ui.textual.app import VeinbornApp
from ui.textual.equipment_screen import EquipmentScreen

pytestmark = pytest.mark.unit


def started_driver(seed=5):
    driver = LocalDriver(Game())
    driver.start(seed=seed, player_name="Solo")
    return driver


# --- LocalDriver --------------------------------------------------------------

def test_local_driver_has_no_snapshot_before_start():
    assert LocalDriver(Game()).snapshot() is None


def test_submit_returns_the_actions_lines_and_notifies():
    driver = started_driver()
    updates = []
    driver.on_update(lambda: updates.append(driver.snapshot().turn))
    asyncio.run(driver.submit('wait'))
    assert updates == [1]
    assert driver.snapshot().turn == 1

    p = driver.game.state.player
    p.inventory.clear()
    assert asyncio.run(driver.submit('drop')) == ["You have nothing to drop."]


def test_note_goes_to_the_log_and_the_snapshot():
    driver = started_driver()
    driver.note("hello")
    assert driver.snapshot().messages[-1] == "hello"


def test_submit_after_game_over_does_nothing():
    driver = started_driver()
    driver.game.state.game_over = True
    assert asyncio.run(driver.submit('wait')) == []
    assert driver.snapshot().turn == 0


# --- the app on a driver that is not a local Game -----------------------------

class FakeDriver:
    """A remote-like driver: a fixed snapshot, records intents, cannot save."""

    can_save = False

    def __init__(self, snapshot):
        self._snapshot = snapshot
        self.submitted = []
        self.notes = []
        self._callbacks = []

    def snapshot(self):
        return self._snapshot

    async def submit(self, intent, **args):
        self.submitted.append((intent, args))
        for cb in self._callbacks:
            cb()
        return [f"sent {intent}"]

    def note(self, line):
        self.notes.append(line)
        self._snapshot.messages.append(line)

    def on_update(self, callback):
        self._callbacks.append(callback)


def fake_app():
    game = Game()
    game.start_new_game(seed=5, player_name="Remote")
    p = game.state.player
    p.inventory.clear()
    p.add_to_inventory(LootGenerator.get_instance().create_item('long_sword'))
    return VeinbornApp(driver=FakeDriver(build_snapshot(game.state))), p


def test_keys_become_intents_and_the_screen_draws_the_drivers_snapshot():
    async def scenario():
        app, player = fake_app()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert not hasattr(app, 'game')
            assert app.status_bar.render().plain.startswith(f"HP: {player.hp}/{player.max_hp}")
            await pilot.press("l", "e", "d", "g", ".", "s", ">")
            await pilot.pause()
            assert app.driver.submitted == [
                ('move', {'dx': 1, 'dy': 0}), ('use', {}), ('drop', {}), ('pickup', {}),
                ('wait', {}), ('survey', {}), ('descend', {}),
            ]
            await pilot.press("i")
            await pilot.pause()
            assert any("Long Sword" in line for line in app.driver.notes)
            assert "Long Sword (weapon)" in app.message_log.render().plain
    asyncio.run(scenario())


def test_save_load_restart_are_refused_without_a_local_run():
    async def scenario():
        app, _ = fake_app()
        async with app.run_test() as pilot:
            await pilot.press("S", "L", "r")
            await pilot.pause()
            assert app.driver.notes == [
                "Saving is only available in single-player.",
                "Loading is only available in single-player.",
                "Restarting is only available in single-player.",
            ]
            assert app.driver.submitted == []
    asyncio.run(scenario())


def test_equipment_screen_submits_equip_and_shows_the_reply():
    async def scenario():
        app, player = fake_app()
        async with app.run_test() as pilot:
            await pilot.press("w")
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, EquipmentScreen)
            assert "Long Sword" in screen.render_panel().plain
            assert player.equipped_weapon is None      # classless: the sword is the only row
            await pilot.press("enter")
            await pilot.pause()
            assert app.driver.submitted == [('equip', {'item_id': player.inventory[0].entity_id})]
            assert screen.feedback == "sent equip"
            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app.screen, EquipmentScreen)
    asyncio.run(scenario())


def test_restart_keeps_name_and_class_on_a_fresh_seed():
    from core.character_class import CharacterClass
    game = Game()
    game.start_new_game(seed=1, player_name="Zed", character_class=CharacterClass.MAGE)
    first_seed = game.state.seed if hasattr(game.state, "seed") else None
    LocalDriver(game).restart()
    assert game.state.player_name == "Zed"
    assert game.state.player.stats["class_type"] == "mage"
    if first_seed is not None:
        assert game.state.seed != first_seed


def test_reveal_map_is_kept_across_restart():
    game = Game()
    game.start_new_game(seed=1, reveal_map=True)
    assert game.state.reveal_map
    LocalDriver(game).restart()
    assert game.state.reveal_map
