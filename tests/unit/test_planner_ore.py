"""ActionPlanner ore goals cannot trap the bot on a floor (VB-68).

A bot spent 18,000 of 20,000 turns on one floor: 'seek ore' fired only at Euclidean
distance > 2, so from 2.0 away (two tiles, not adjacent) the room sweep stepped it
back, and from there the ore seek stepped it forward again. These pin the fix.
"""
import sys
from pathlib import Path

import pytest

from core.base.entity import EntityType
from core.loot import LootGenerator
from tests.fuzz.services import action_planner as planner_module
from tests.unit.test_planner_abilities import make

pytestmark = pytest.mark.unit


def with_one_ore(dx=2, purity=85):
    """A warrior with no monsters, no items and one surveyed ore vein dx tiles east."""
    game, planner = make("warrior")
    for e in list(game.state.entities.values()):
        if e.entity_type in (EntityType.ORE_VEIN, EntityType.ITEM):
            game.context.remove_entity(e.entity_id)
    p = game.state.player
    m = game.state.dungeon_map
    for sx in (1, -1):
        if all(m.is_walkable(p.x + sx * i, p.y) for i in range(1, dx + 2)):
            ore = game.entity_loader.create_ore_vein('iron', p.x + sx * dx, p.y)
            ore.set_stat('surveyed', True)
            ore.set_stat('purity', purity)
            game.context.add_entity(ore)
            return game, planner, ore
    pytest.skip("no straight open corridor beside the player")


def test_two_tiles_away_is_not_a_dead_zone():
    game, planner, ore = with_one_ore(dx=2)
    # Lower goals only wait, so reaching the ore is down to the ore logic alone (in the
    # stall the sweep stepped the bot back whenever the ore logic declined)
    planner.sweep_or_leave = lambda game, fight=None: ('wait', {})
    for _ in range(6):
        action, kwargs = planner.get_smart_action(game)
        if action == 'mine':
            assert kwargs == {'ore_vein_id': ore.entity_id}
            return
        game.handle_player_action(action, **kwargs)
    pytest.fail("never reached and mined Legacy-quality ore two tiles away")


def test_gives_up_on_an_ore_it_cannot_reach():
    game, planner, ore = with_one_ore(dx=3)
    for _ in range(planner_module.ORE_SEEK_TURNS):
        assert planner.seek_ore(game, ore, reach=4, label="test") is not None
    assert planner.seek_ore(game, ore, reach=4, label="test") is None


def test_leaving_skips_ore_detours():
    game, planner, ore = with_one_ore(dx=2)
    planner.sweeper.max_floor_turns = 0          # floor budget spent: head for the stairs
    action, _ = planner.get_smart_action(game)
    assert action != 'mine' and ore.entity_id not in planner._ore_seek


def test_no_mining_with_a_full_pack():
    game, planner, ore = with_one_ore(dx=1)
    player = game.state.player
    while len(player.inventory) < planner_module.INVENTORY_MAX:
        player.add_to_inventory(LootGenerator.get_instance().create_item('bread'))
    action, _ = planner.get_smart_action(game)
    assert action != 'mine'


@pytest.mark.slow
def test_seeded_bot_leaves_the_floor_it_used_to_stall_on():
    """Warrior seed 3000 reached floor 8 at turn 1564 and never left (20,000 turns)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fuzz"))
    from warrior_bot import WarriorBot
    stats = WarriorBot().play_one_game(max_turns=2600, seed=3000)
    assert stats['floor'] >= 10
