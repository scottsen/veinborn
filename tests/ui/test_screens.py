"""Keyboard screens (VB-109): craft at a forge, choose what to use or drop, keys help, confirm."""
import asyncio

import pytest

from core.base.entity import EntityType
from core.character_class import CharacterClass
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
        from core.crafting import ore_rating, ORE_PROPERTIES
        rating = ore_rating({n: ore.get_stat(n) for n in ORE_PROPERTIES})
        assert f"Copper Ore (ore) Q{rating} P{ore.get_stat('purity')} H{ore.get_stat('hardness')}" in panel
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
        assert "Uses: Copper Ore Q" in screen.render_panel().plain and " P95 " in screen.render_panel().plain   # the default is the best ore, named
        assert "1 more to choose from: o" in screen.render_panel().plain
        await pilot.press("o")
        await pilot.pause()
        assert isinstance(app.screen, OrePickScreen)
        picker = app.screen
        assert len(picker.picked) == 2
        from core.crafting import ore_rating
        ratings = [ore_rating(r.ore) for r in picker.rows()]
        assert ratings == sorted(ratings, reverse=True) and len(ratings) == 3   # best ore first
        picker.picked = []                                          # start over: pick the two worst (rows 1 and 2)
        picker.cursor = 1
        await pilot.press("space", "down", "space")
        await pilot.pause()
        assert "->" in picker.render_panel().plain                  # preview once 2 are picked
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, OrePickScreen)
        assert ores[2] in player.inventory and ores[0] not in player.inventory
        assert any(i.get_stat('recipe_id') == 'copper_sword' for i in player.inventory)
    run(scenario)


def test_forge_always_hints_at_choosing_ore_even_with_no_spare():
    async def scenario(app, pilot, game):
        stand_at_forge(game, ore=2)                  # exactly what a copper sword needs: nothing to choose between
        await pilot.press("f")
        await pilot.pause()
        screen = app.screen
        screen.cursor = next(n for n, r in enumerate(screen.rows()) if r.recipe_id == 'copper_sword')
        panel = screen.render_panel().plain
        assert "(o: choose which ore)" in panel and "more to choose from" not in panel
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


def _forge_with_parts(game, parts):
    """At the forge holding crafted parts `[(part_id, ore_type, ore_count)]`; returns the items."""
    from core.actions.craft_action import CraftAction
    player, _ = stand_at_forge(game, ore=0)
    manager = CraftAction.get_recipe_manager()
    made = []
    for part_id, ore_type, count in parts:
        vein = EntityLoader().create_ore_vein(ore_type, 0, 0, floor=12)
        part = manager.create_part(part_id, [vein.get_ore_item() for _ in range(count)])
        assert player.add_to_inventory(part)
        made.append(part)
    return player, made


def test_part_picker_assembles_the_hand_picked_parts():
    from ui.textual.craft_screen import PartPickScreen

    async def scenario(app, pilot, game):
        player, (weak, strong, hilt) = _forge_with_parts(
            game, [('blade', 'copper', 2), ('blade', 'adamantite', 2), ('hilt', 'iron', 1)])
        await pilot.press("f")
        await pilot.pause()
        screen = app.screen
        screen.cursor = next(n for n, r in enumerate(screen.rows()) if r.recipe_id == 'sword')
        assert "Adamantite Blade" in screen.render_panel().plain         # default: the best blade
        await pilot.press("o")
        await pilot.pause()
        assert isinstance(app.screen, PartPickScreen)
        picker = app.screen
        assert set(picker.picked) == {strong.entity_id, hilt.entity_id}
        rows = picker.rows()
        picker.cursor = next(n for n, r in enumerate(rows) if r.entity_id == weak.entity_id)
        await pilot.press("space")                                        # swaps the head slot
        await pilot.pause()
        assert set(picker.picked) == {weak.entity_id, hilt.entity_id}
        assert "->" in picker.render_panel().plain
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, PartPickScreen)
        sword = next(i for i in player.inventory if i.get_stat('recipe_id') == 'sword')
        assert sword.name == 'Copper-Iron Sword'
        assert strong in player.inventory and weak not in player.inventory
    run(scenario)


def test_part_picker_refuses_an_unfilled_slot():
    from ui.textual.craft_screen import PartPickScreen

    async def scenario(app, pilot, game):
        player, (blade, hilt) = _forge_with_parts(game, [('blade', 'iron', 2), ('hilt', 'iron', 1)])
        await pilot.press("f")
        await pilot.pause()
        screen = app.screen
        screen.cursor = next(n for n, r in enumerate(screen.rows()) if r.recipe_id == 'sword')
        await pilot.press("o")
        await pilot.pause()
        picker = app.screen
        picker.picked = [blade.entity_id]                                 # no grip
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, PartPickScreen) and "grip" in picker.render_panel().plain
        assert hilt in player.inventory and blade in player.inventory
    run(scenario)


def test_enter_on_an_assembly_crafts_the_best_parts():
    async def scenario(app, pilot, game):
        player, _ = _forge_with_parts(game, [('plates', 'iron', 3), ('lining', 'iron', 1)])
        await pilot.press("f")
        await pilot.pause()
        screen = app.screen
        screen.cursor = next(n for n, r in enumerate(screen.rows()) if r.recipe_id == 'chestplate')
        await pilot.press("enter")
        await pilot.pause()
        assert any(i.get_stat('recipe_id') == 'chestplate' for i in player.inventory)
    run(scenario)


def _drop_items_here(game, item_ids):
    """Put these items on the player's tile (pack emptied); returns them."""
    player = game.state.player
    player.inventory.clear()
    items = []
    for item_id in item_ids:
        item = LootGenerator.get_instance().create_item(item_id)
        item.x, item.y = player.x, player.y
        game.context.add_entity(item)
        items.append(item)
    return items


def test_g_with_several_items_lets_you_choose_one():
    from ui.textual.pack_screen import GroundScreen

    async def scenario(app, pilot, game):
        gold, potion, ration = _drop_items_here(game, ['gold_pile_small', 'potion_healing', 'ration'])
        await pilot.press("g")
        await pilot.pause()
        assert isinstance(app.screen, GroundScreen)
        screen = app.screen
        names = [r.name for r in screen.rows()]
        screen.cursor = next(n for n, r in enumerate(screen.rows()) if r.entity_id == potion.entity_id)
        await pilot.press("enter")
        await pilot.pause()
        player = game.state.player
        assert potion in player.inventory and gold not in player.inventory and ration not in player.inventory
        assert player.gold == 0
        assert len(screen.rows()) == len(names) - 1                  # the rest still lie here
        await pilot.press("a")
        await pilot.pause()
        assert player.gold == gold.get_stat('gold_amount') > 0      # gold is counted, never carried
        assert gold not in player.inventory and ration in player.inventory
        assert not isinstance(app.screen, GroundScreen)
    run(scenario)


def test_g_with_one_item_takes_it_at_once():
    from ui.textual.pack_screen import GroundScreen

    async def scenario(app, pilot, game):
        (potion,) = _drop_items_here(game, ['potion_healing'])
        await pilot.press("g")
        await pilot.pause()
        assert not isinstance(app.screen, GroundScreen)
        assert potion in game.state.player.inventory
    run(scenario)


def test_pickup_intent_can_name_the_item():
    from core.actions.pickup_action import PickupAction
    assert PickupAction.from_dict(PickupAction('a', 'x').to_dict()) == PickupAction('a', 'x')
    assert PickupAction.from_dict({'actor_id': 'a'}) == PickupAction('a')       # old saved intents


def test_x_examine_lists_nearest_first_and_remembers_survey_numbers():
    from ui.textual.examine_screen import ExamineScreen

    async def scenario(app, pilot, game):
        player = game.state.player
        veins = game.context.get_entities_by_type(EntityType.ORE_VEIN)
        vein = min(veins, key=lambda v: abs(v.x - player.x) + abs(v.y - player.y))
        player.x, player.y = vein.x - 1, vein.y
        game.state.reveal_map = True
        await pilot.press("x")
        await pilot.pause()
        assert isinstance(app.screen, ExamineScreen)
        screen = app.screen
        rows = screen.rows()
        assert [r.distance for r in rows] == sorted(r.distance for r in rows)
        row = next(r for r in rows if r.entity_id == vein.entity_id)
        assert "not surveyed" in row.text and "press s" in row.detail
        await pilot.press("escape")
        await pilot.pause()
        vein.set_stat('surveyed', True)                      # what pressing s does
        await pilot.press("x")
        await pilot.pause()
        row = next(r for r in app.screen.rows() if r.entity_id == vein.entity_id)
        assert "surveyed" in row.text and "not" not in row.text
        assert f"P{vein.get_stat('purity')}" in row.detail and "mining takes" in row.detail
    run(scenario)


def test_examine_shows_a_monsters_attack_and_an_items_stats():
    from core.examine import examine_listing
    from core.snapshot import build_snapshot

    async def scenario(app, pilot, game):
        player = game.state.player
        game.state.reveal_map = True
        item = LootGenerator.get_instance().create_item('long_sword')
        item.x, item.y = player.x, player.y
        game.context.add_entity(item)
        lines = examine_listing(build_snapshot(game.state))
        sword = next(l for l in lines if l.entity_id == item.entity_id)
        assert "+5 attack" in sword.detail and sword.distance == 0
        monsters = [l for l in lines if l.kind == 'monster']
        assert monsters and all("attack" in l.detail and "XP" in l.detail for l in monsters)
    run(scenario)


def _mage_with_monsters(game, kinds):
    """Mage with monsters (one per name in `kinds`) on free floor tiles in sight, nearest first."""
    from core.geometry import chebyshev
    player = game.state.player
    for m in game.context.get_entities_by_type(EntityType.MONSTER):     # a clean floor
        del game.state.entities[m.entity_id]
    spots = [(x, y) for x in range(player.x - 3, player.x + 4) for y in range(player.y - 3, player.y + 4)
             if (x, y) != (player.x, player.y) and game.state.dungeon_map.is_transparent(x, y)
             and game.state.dungeon_map.is_walkable(x, y) and game.context.get_entity_at(x, y) is None]
    spots.sort(key=lambda p: chebyshev(player.x, player.y, *p))
    made = []
    for kind, (x, y) in zip(kinds, spots):
        monster = EntityLoader().create_monster(kind, x, y)
        game.context.add_entity(monster)
        made.append(monster)
    return made


def test_z_with_two_targets_asks_which_to_bolt():
    from ui.textual.examine_screen import TargetScreen

    async def main():
        app = VeinbornApp(seed=5, character_class=CharacterClass.MAGE)
        async with app.run_test() as pilot:
            game = app.driver.game
            near, far = _mage_with_monsters(game, ['goblin', 'orc'])
            game.state.reveal_map = True
            app.refresh_ui()
            await pilot.press("z")
            await pilot.pause()
            assert isinstance(app.screen, TargetScreen)
            rows = app.screen.rows()
            assert [r.entity_id for r in rows][:2] == [near.entity_id, far.entity_id]   # nearest first
            hp = far.hp
            app.screen.cursor = 1                                       # the farther one
            await pilot.press("enter")
            await pilot.pause()
            assert not isinstance(app.screen, TargetScreen)
            assert far.hp < hp or not far.is_alive                      # it took the bolt
            assert near.hp == near.max_hp                               # the nearer one did not
    asyncio.run(main())


def test_z_with_one_target_casts_at_once():
    from ui.textual.examine_screen import TargetScreen

    async def main():
        app = VeinbornApp(seed=5, character_class=CharacterClass.MAGE)
        async with app.run_test() as pilot:
            game = app.driver.game
            (only,) = _mage_with_monsters(game, ['goblin'])
            app.refresh_ui()
            await pilot.press("z")
            await pilot.pause()
            assert not isinstance(app.screen, TargetScreen)
    asyncio.run(main())


def test_a_long_pack_list_scrolls_to_the_last_row_instead_of_clipping():
    async def scenario(app, pilot, game):
        player = game.state.player
        player.inventory.clear()
        vein = EntityLoader().create_ore_vein('copper', 0, 0, floor=1)
        for _ in range(25):
            player.add_to_inventory(vein.get_ore_item())
        await pilot.press("i")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, PackScreen)
        shown = screen.render_panel().plain
        assert shown.count("Copper Ore") < 25 and "↓ " in shown.split("\n\n")[-2] and " more" in shown         # clipped list says so
        for _ in range(24):
            await pilot.press("down")
        await pilot.pause()
        assert screen.cursor == 24
        shown = screen.render_panel().plain
        assert "▶ Copper Ore" in shown and "↑ " in shown and " more" in shown and "↓ " not in shown.replace("↑/↓", "") # cursor row is on screen
    run(scenario)


def test_shift_l_asks_before_replacing_the_run_with_the_last_save():
    async def scenario(app, pilot, game):
        player = game.state.player
        await pilot.press("S")                      # save at full health
        await pilot.pause()
        player.hp = 1
        await pilot.press("L")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("n")
        await pilot.pause()
        assert not isinstance(app.screen, ConfirmScreen) and app.driver.game.state.player.hp == 1   # nothing lost

        await pilot.press("L", "y")
        await pilot.pause()
        assert app.driver.game.state.player.hp > 1                                                  # loaded the save
    run(scenario)
