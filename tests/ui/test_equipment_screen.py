"""The equipment screen (VB-72 follow-up): one list to view, wear and remove gear."""
import pytest

from core.loot import LootGenerator
from ui.textual.app import VeinbornApp
from ui.textual.equipment_screen import EquipmentScreen

pytestmark = pytest.mark.unit


def give(player, item_id):
    item = LootGenerator.get_instance().create_item(item_id)
    assert player.add_to_inventory(item)
    return item


async def open_screen(pilot, app):
    await pilot.press("w")
    await pilot.pause()
    assert isinstance(app.screen, EquipmentScreen)
    return app.screen


def test_equipment_screen_wear_remove_and_keys_do_not_leak():
    import asyncio

    async def scenario():
        app = VeinbornApp(seed=5)
        async with app.run_test() as pilot:
            player = app.driver.game.state.player
            player.inventory.clear()
            player.equipped_weapon = player.equipped_armor = None
            sword = give(player, 'long_sword')
            mail = give(player, 'chainmail')
            potion = give(player, 'potion_healing')

            screen = await open_screen(pilot, app)
            panel = screen.render_panel().plain
            assert "Weapon: (nothing)" in panel and "Armor: (nothing)" in panel
            assert "Long Sword" in panel and "Chainmail" in panel
            assert "Potion" not in panel            # not gear: not on the list

            x, y = player.x, player.y
            await pilot.press("l")                   # a map key: must not walk
            await pilot.pause()
            assert (player.x, player.y) == (x, y)

            await pilot.press("enter")               # cursor on the first pack row: wield the sword
            await pilot.pause()
            assert player.equipped_weapon is sword and sword not in player.inventory
            assert "Weapon: Long Sword" in screen.render_panel().plain

            await pilot.press("down", "enter")       # worn weapon is row 0, chainmail row 1
            await pilot.pause()
            # cursor moved to the chainmail row: wear it
            assert player.equipped_armor is mail

            await pilot.press("x")                   # remove: the selected row is worn, so it comes off
            await pilot.pause()
            assert (player.equipped_weapon is None) != (player.equipped_armor is None)
            assert potion in player.inventory

            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app.screen, EquipmentScreen)

    asyncio.run(scenario())
