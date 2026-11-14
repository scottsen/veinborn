"""Keyboard screens (VB-109): craft at a forge, choose what to use or drop, keys help, confirm."""
import asyncio

import pytest

from core.base.entity import EntityType
from core.entity_loader import EntityLoader
from core.loot import LootGenerator
from ui.textual.confirm_screen import ConfirmScreen
from ui.textual.craft_screen import CraftScreen
from ui.textual.help_screen import HelpScreen, key_rows
from ui.textual.pack_screen import PackScreen
from ui.textual.app import VeinbornApp

pytestmark = pytest.mark.unit


def run(scenario):
    async def main():
        app = VeinbornApp(seed=5)
        async with app.run_test() as pilot:
            await scenario(app, pilot, app.driver.game)
    asyncio.run(main())


def give(player, item_id):
    item = LootGenerator.get_instance().create_item(item_id)
    assert player.add_to_inventory(item)
    return item


def stand_at_forge(game, ore=3):
    player = game.state.player
    forge = game.context.get_entities_by_type(EntityType.FORGE)[0]
    player.x, player.y = forge.x + 1, forge.y
    player.inventory.clear()
    vein = EntityLoader().create_ore_vein('copper', 0, 0, floor=1)
    for _ in range(ore):
        player.add_to_inventory(vein.get_ore_item())
    return player, forge


def test_f_away_from_a_forge_says_so_and_opens_nothing():
    async def scenario(app, pilot, game):
        player = game.state.player
        forge = game.context.get_entities_by_type(EntityType.FORGE)[0]
        player.x, player.y = forge.x + 6, forge.y + 6
        await pilot.press("f")
        await pilot.pause()
        assert not isinstance(app.screen, CraftScreen)
        assert "No forge in reach" in app.message_log.render().plain
    run(scenario)


def test_f_at_a_forge_crafts_the_selected_recipe_from_the_keyboard():
    async def scenario(app, pilot, game):
        player, _ = stand_at_forge(game)
        await pilot.press("f")
        await pilot.pause()
        assert isinstance(app.screen, CraftScreen)
        panel = app.screen.render_panel().plain
        assert "FORGE" in panel and "copper ore" in panel
        x, y = player.x, player.y
        await pilot.press("l")                         # map keys must not walk while it is open
        await pilot.pause()
        assert (player.x, player.y) == (x, y)

        recipe = app.screen.rows()[0]                  # craftable recipes sort first
        assert recipe.craftable
        before = len(player.inventory)
        await pilot.press("enter")
        await pilot.pause()
        assert any(i.get_stat('recipe_id') == recipe.recipe_id for i in player.inventory)
        assert len(player.inventory) < before + 1      # ore was consumed
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, CraftScreen)
    run(scenario)


def test_an_uncraftable_recipe_explains_itself_and_changes_nothing():
    async def scenario(app, pilot, game):
        player, _ = stand_at_forge(game, ore=0)
        await pilot.press("f", "enter")
        await pilot.pause()
        assert isinstance(app.screen, CraftScreen)
        assert "Requires" in app.screen.render_panel().plain
        assert player.inventory == []
    run(scenario)


def test_pack_screen_uses_the_chosen_item_not_the_best_one():
    async def scenario(app, pilot, game):
        player = game.state.player
        player.inventory.clear()
        small = give(player, 'potion_healing')
        big = give(player, 'potion_full_healing')
        player.hp = 1
        await pilot.press("i")
        await pilot.pause()
        assert isinstance(app.screen, PackScreen)
        await pilot.press("enter")                     # row 0: the small potion, not the best
        await pilot.pause()
        assert small not in player.inventory and big in player.inventory
        await pilot.press("escape")
    run(scenario)


def test_pack_screen_drops_the_chosen_item_and_refuses_gear_use():
    async def scenario(app, pilot, game):
        player = game.state.player
        player.inventory.clear()
        sword = give(player, 'long_sword')
        potion = give(player, 'potion_healing')
        await pilot.press("i", "enter")                # the sword is row 0: not usable
        await pilot.pause()
        assert sword in player.inventory and "can't use" in app.screen.render_panel().plain
        await pilot.press("d")                         # drop the selected one (the sword)
        await pilot.pause()
        assert sword not in player.inventory and potion in player.inventory
    run(scenario)


def test_help_lists_every_visible_key_from_the_bindings():
    async def scenario(app, pilot, game):
        await pilot.press("question_mark")
        await pilot.pause()
        assert isinstance(app.screen, HelpScreen)
        panel = app.screen.render_panel().plain
        for needle in ("Craft at a forge", "Pack", "Quick drop", "Quit", "Move / attack / mine"):
            assert needle in panel, needle
        assert "debug" not in panel.lower()
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, HelpScreen)
    run(scenario)


def test_key_rows_fold_the_eight_move_keys_into_one_row():
    rows = key_rows(VeinbornApp.BINDINGS)
    moves = [r for r in rows if r[1].startswith("Move")]
    assert len(moves) == 1 and all(k in moves[0][0] for k in ("up", "h", "y", "n"))


def test_quit_and_restart_ask_first():
    async def scenario(app, pilot, game):
        player = game.state.player
        player.hp = 1
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("n")
        await pilot.pause()
        assert not isinstance(app.screen, ConfirmScreen) and app.driver.game.state.player.hp == 1

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("n")
        await pilot.pause()
        assert app.is_running

        await pilot.press("r", "y")
        await pilot.pause()
        state = app.driver.game.state
        assert state.player.hp == state.player.max_hp
    run(scenario)


def test_stat_labels_are_readable():
    from ui.textual.craft_screen import stats_text
    assert stats_text({'attack_bonus': 4, 'defense_bonus': 0, 'fire_damage': 2}) == "+4 attack  +2 fire damage"


def test_pack_screen_shows_ore_quality_and_the_legend():
    async def scenario(app, pilot, game):
        player = game.state.player
        player.inventory.clear()
        vein = EntityLoader().create_ore_vein('copper', 0, 0, floor=1)
        ore = vein.get_ore_item()
        player.add_to_inventory(ore)
        await pilot.press("i")
        await pilot.pause()
        panel = app.screen.render_panel().plain
        assert f"Copper Ore (ore) P{ore.get_stat('purity')} H{ore.get_stat('hardness')}" in panel
        assert "P purity" in panel
    run(scenario)


def test_ore_picker_crafts_from_the_hand_picked_ore():
    from ui.textual.craft_screen import OrePickScreen

    async def scenario(app, pilot, game):
        player, _ = stand_at_forge(game, ore=0)
        vein = EntityLoader().create_ore_vein('copper', 0, 0, floor=1)
        ores = []
        for purity in (10, 50, 95):
            o = vein.get_ore_item()
            o.set_stat('purity', purity)
            o.set_stat('hardness', purity)
            player.add_to_inventory(o)
            ores.append(o)
        await pilot.press("f")
        await pilot.pause()
        screen = app.screen
        i = next(n for n, r in enumerate(screen.rows()) if r.recipe_id == 'copper_sword')
        screen.cursor = i
        assert "Uses: P95" in screen.render_panel().plain          # the default is the best ore
        await pilot.press("o")
        await pilot.pause()
        assert isinstance(app.screen, OrePickScreen)
        picker = app.screen
        assert len(picker.picked) == 2
        picker.picked = []                                          # start over: pick the two worst
        picker.cursor = 0
        await pilot.press("space", "down", "space")
        await pilot.pause()
        assert "->" in picker.render_panel().plain                  # preview once 2 are picked
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, OrePickScreen)
        assert ores[2] in player.inventory and ores[0] not in player.inventory
        assert any(i.get_stat('recipe_id') == 'copper_sword' for i in player.inventory)
    run(scenario)


def test_ore_picker_refuses_the_wrong_count():
    from ui.textual.craft_screen import OrePickScreen

    async def scenario(app, pilot, game):
        player, _ = stand_at_forge(game, ore=3)
        await pilot.press("f")
        await pilot.pause()
        screen = app.screen
        screen.cursor = next(n for n, r in enumerate(screen.rows()) if r.recipe_id == 'copper_sword')
        await pilot.press("o")
        await pilot.pause()
        picker = app.screen
        picker.picked = picker.picked[:1]
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, OrePickScreen) and "Pick exactly 2" in picker.render_panel().plain
        assert len(player.inventory) == 3
    run(scenario)
