"""RoomSweeper: clear every room, then leave (fuzz-bot service)."""

import pytest

from core.base.entity import EntityType
from core.game import Game
from tests.fuzz.services.action_planner import ActionPlanner
from tests.fuzz.services.perception_service import PerceptionService
from tests.fuzz.services.room_sweeper import GIVE_UP_TURNS, MAX_FLOOR_TURNS, RoomSweeper
from tests.fuzz.services.tactical_decision_service import TacticalDecisionService

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=42)
    for e in list(g.state.entities.values()):
        if e.entity_type == EntityType.MONSTER:
            g.context.remove_entity(e.entity_id)
    return g


@pytest.fixture
def sweeper():
    return RoomSweeper(PerceptionService())


def goto(game, room_index):
    cx, cy = game.state.dungeon_map.rooms[room_index].center
    game.state.player.x, game.state.player.y = cx, cy


def add_monster(game, x, y, monster_id="goblin"):
    mon = game.entity_loader.create_monster(monster_id, x, y)
    game.context.add_entity(mon)
    return mon


def visit_all_rooms(game, sweeper):
    for index in range(len(game.state.dungeon_map.rooms)):
        goto(game, index)
        sweeper.next_step(game, fight=None)


# --- the sweep ---------------------------------------------------------------

def test_first_step_leaves_the_start_room_for_the_nearest_other_room(game, sweeper):
    kind, target = sweeper.next_step(game)
    assert kind == 'room'
    rooms = game.state.dungeon_map.rooms
    start = sweeper._room_at(game, game.state.player.x, game.state.player.y)
    others = [r.center for i, r in enumerate(rooms) if i != start]
    p = game.state.player
    nearest = min(others, key=lambda c: abs(c[0] - p.x) + abs(c[1] - p.y))
    assert target == nearest


def test_heads_for_the_stairs_only_after_every_room_is_visited(game, sweeper):
    rooms = game.state.dungeon_map.rooms
    for index in range(len(rooms) - 1):
        goto(game, index)
        step = sweeper.next_step(game)
        assert step is not None and step[0] == 'room', f"rooms left after {index + 1} of {len(rooms)}"
    assert not sweeper.done(game)
    # Walk off the stairs, then visit the last room: now the sweep is done and it says "stairs"
    goto(game, len(rooms) - 1)
    stairs = tuple(game.state.dungeon_map.find_stairs_down())
    game.state.player.x, game.state.player.y = stairs[0] + 1, stairs[1]
    assert sweeper.next_step(game) == ('stairs', stairs)
    assert sweeper.done(game)


def test_no_step_when_already_on_the_stairs_with_the_sweep_done(game, sweeper):
    visit_all_rooms(game, sweeper)
    game.state.player.x, game.state.player.y = game.state.dungeon_map.find_stairs_down()
    assert sweeper.next_step(game) is None


# --- fighting in the room ---------------------------------------------------------

def test_fightable_monster_in_the_current_room_is_the_next_step(game, sweeper):
    room = game.state.dungeon_map.rooms[0]
    goto(game, 0)
    mon = add_monster(game, room.x, room.y)
    step = sweeper.next_step(game, fight=lambda m: True)
    assert step == ('monster', mon)
    assert 0 not in sweeper._finished  # the room is not done while it holds a target


def test_room_is_finished_once_its_monsters_are_dead(game, sweeper):
    room = game.state.dungeon_map.rooms[0]
    goto(game, 0)
    mon = add_monster(game, room.x, room.y)
    assert sweeper.next_step(game, fight=lambda m: True)[0] == 'monster'
    mon.is_alive = False
    game.context.remove_entity(mon.entity_id)
    sweeper.perception.start_turn(1)  # the bot loop does this every turn; it drops cached monsters
    assert sweeper.next_step(game, fight=lambda m: True)[0] == 'room'  # on to another room
    assert 0 in sweeper._finished


def test_a_monster_the_bot_will_not_fight_does_not_hold_up_the_room(game, sweeper):
    room = game.state.dungeon_map.rooms[0]
    goto(game, 0)
    add_monster(game, room.x, room.y)
    assert sweeper.next_step(game, fight=None)[0] == 'room'
    assert 0 in sweeper._finished


def test_a_monster_in_another_room_does_not_block_this_one(game, sweeper):
    rooms = game.state.dungeon_map.rooms
    goto(game, 0)
    far = rooms[-1]
    add_monster(game, far.x, far.y)
    assert sweeper.next_step(game, fight=lambda m: True)[0] == 'room'
    assert 0 in sweeper._finished


# --- giving up and budgets -----------------------------------------------------------

def test_a_room_that_cannot_be_reached_is_written_off(game, sweeper):
    goto(game, 0)
    first = sweeper.next_step(game)
    seen = {first[1]}
    for _ in range(GIVE_UP_TURNS + 2):
        seen.add(sweeper.next_step(game)[1])  # never moves: stuck on the way
    assert len(seen) > 1  # it moved on to another room instead of walking forever


def test_floor_turn_budget_forces_the_exit_even_with_rooms_unvisited(game, sweeper):
    sweeper.next_step(game)
    assert not sweeper.done(game)
    game.state.turn_count += MAX_FLOOR_TURNS
    assert sweeper.done(game)
    assert sweeper.next_step(game)[0] == 'stairs'


def test_a_new_floor_starts_a_new_sweep(game, sweeper):
    visit_all_rooms(game, sweeper)
    assert sweeper.done(game)
    game.descend_floor()
    assert not sweeper.done(game)
    assert sweeper._finished == set()


# --- the descend gate ------------------------------------------------------------------

def make_planner():
    perception = PerceptionService()
    decisions = TacticalDecisionService(perception)
    return ActionPlanner(perception, decisions), decisions


def test_stepping_on_the_stairs_early_does_not_skip_unvisited_rooms(game):
    planner, decisions = make_planner()
    stairs = game.state.dungeon_map.find_stairs_down()
    game.state.player.x, game.state.player.y = stairs
    room = game.state.dungeon_map.rooms[0]
    add_monster(game, room.x, room.y)  # the floor is not clear
    assert decisions.should_descend(game) is False


def test_a_cleared_floor_can_be_left_at_once(game):
    planner, decisions = make_planner()
    game.state.player.x, game.state.player.y = game.state.dungeon_map.find_stairs_down()
    assert decisions.should_descend(game) is True  # no monsters left


def test_with_the_sweep_done_the_stairs_can_be_taken_despite_monsters(game):
    planner, decisions = make_planner()
    visit_all_rooms(game, planner.sweeper)
    room = game.state.dungeon_map.rooms[0]
    add_monster(game, room.x, room.y)
    game.state.player.x, game.state.player.y = game.state.dungeon_map.find_stairs_down()
    assert decisions.should_descend(game) is True


def test_decision_service_without_a_planner_is_unchanged():
    decisions = TacticalDecisionService(PerceptionService())
    assert getattr(decisions, 'descend_gate', None) is None


# --- end to end: with endless spawns the bot still goes down ---------------------------------

def test_planner_keeps_descending_while_monsters_keep_spawning():
    g = Game()
    g.start_new_game(seed=5)
    g.state.player.max_hp = g.state.player.hp = 10 ** 6
    planner, _ = make_planner()
    for _ in range(1500):
        planner.perception.start_turn(g.state.turn_count)
        action, kwargs = planner.plan_next_action(g, mode='strategic')
        g.handle_player_action(action, **kwargs)
        if g.state.current_floor >= 3:
            break
    assert g.state.current_floor >= 3
