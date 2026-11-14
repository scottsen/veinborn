"""Bots disengage from a melee they are losing when the stairs are close enough (VB-68)."""

import pytest

from core.game import Game
from core.entities import Monster
from core.world import Tile, TileType
from tests.fuzz.services.action_planner import ActionPlanner
from tests.fuzz.services.perception_service import PerceptionService
from tests.fuzz.services.tactical_decision_service import TacticalDecisionService


def _corridor(game, stairs_x):
    """A straight floor corridor y=5, x=2..14, stairs down at (stairs_x, 5); player at (5, 5)."""
    m = game.state.dungeon_map
    for x in range(m.width):
        for y in range(m.height):
            m.tiles[x][y] = Tile(TileType.WALL)
    for x in range(2, 15):
        m.tiles[x][5] = Tile(TileType.FLOOR)
    m.tiles[stairs_x][5] = Tile(TileType.STAIRS_DOWN)
    m._stairs_down_cache = None
    game.state.entities.clear()
    player = game.state.player
    player.x, player.y = 5, 5
    game.state.entities[player.entity_id] = player


def _setup(stairs_x, monster_hp=500, monster_attack=20):
    game = Game()
    game.start_new_game(seed=42)
    _corridor(game, stairs_x)
    monster = Monster(name="Brute", content_id="goblin", x=4, y=5,
                      hp=monster_hp, max_hp=monster_hp, attack=monster_attack, defense=0)
    monster.is_alive = True
    game.state.entities[monster.entity_id] = monster
    perception = PerceptionService()
    decisions = TacticalDecisionService(perception)
    return game, monster, ActionPlanner(perception, decisions)


def test_a_lost_melee_walks_to_stairs_that_are_close():
    game, monster, planner = _setup(stairs_x=8)          # 3 steps away, brute behind us
    player = game.state.player
    player.hp = player.max_hp = 200                      # survives 3 hits, cannot win
    assert not planner.decisions.can_win_fight(game, monster)
    assert planner.escape_action(game, monster) == ('move', {'dx': 1, 'dy': 0})
    assert planner.get_smart_action(game) == ('move', {'dx': 1, 'dy': 0})


def test_on_the_stairs_a_lost_melee_descends():
    game, monster, planner = _setup(stairs_x=5)
    assert planner.escape_action(game, monster) == ('descend', {})


def test_stairs_too_far_to_survive_the_walk_means_fighting_on():
    game, monster, planner = _setup(stairs_x=14)         # 9 steps
    player = game.state.player
    player.hp = player.max_hp = 40
    assert planner.escape_action(game, monster) is None


def test_a_fight_we_can_win_is_not_run_from():
    game, monster, planner = _setup(stairs_x=8, monster_hp=1, monster_attack=1)
    assert planner.decisions.can_win_fight(game, monster)
    assert planner.escape_action(game, monster) is None


def test_no_stairs_means_fighting_on():
    game, monster, planner = _setup(stairs_x=8)
    m = game.state.dungeon_map
    m.tiles[8][5] = Tile(TileType.FLOOR)
    m._stairs_down_cache = None
    assert planner.escape_action(game, monster) is None
