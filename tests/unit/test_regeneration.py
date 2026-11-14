"""Natural regeneration scales with max HP and is faster while resting (VB-107)."""

import pytest

from core.game import Game
from core.entities import Monster
from core.turn_processor import apply_hp_regeneration


class _P:
    def __init__(self, hp, max_hp):
        self.hp, self.max_hp, self.is_alive, self.name = hp, max_hp, True, "p"

    def heal(self, n):
        healed = min(n, self.max_hp - self.hp)
        self.hp += healed
        return healed


def test_a_small_pool_heals_the_minimum_and_a_big_one_a_share():
    small, mid, big = _P(1, 30), _P(1, 48), _P(1, 100)
    apply_hp_regeneration([small, mid, big], 10, 10, 1, percent=0.05)
    assert (small.hp - 1, mid.hp - 1, big.hp - 1) == (1, 2, 5)   # 30 HP: 1; 48: 2; 100: 5


def test_only_every_interval_turn_heals():
    p = _P(1, 100)
    apply_hp_regeneration([p], 7, 10, 1, percent=0.05)
    assert p.hp == 1


def test_resting_multiplies_the_tick_for_the_resting_player_only():
    rester, other = _P(1, 100), _P(1, 100)
    apply_hp_regeneration([rester, other], 10, 10, 1, percent=0.05, rest_multiplier=3,
                          is_resting=lambda p: p is rester)
    assert (rester.hp - 1, other.hp - 1) == (15, 5)


def _game():
    g = Game()
    g.start_new_game(seed=5)
    g.state.entities.clear()
    g.state.entities[g.state.player.entity_id] = g.state.player
    p = g.state.player
    p.max_hp, p.hp = 100, 10
    return g, p


def test_ten_turns_of_resting_heal_three_times_ten_of_walking():
    g, p = _game()
    for _ in range(10):
        g.handle_player_action('wait')
    rested = p.hp - 10
    g2, p2 = _game()
    for _ in range(10):                      # same ten turns, but acting instead of waiting
        p2.set_stat('rested_turn', None)
        g2.engine.tick()
    walked = p2.hp - 10
    assert (walked, rested) == (5, 15)


def test_waiting_with_a_monster_in_sight_is_not_resting():
    from core.world import Tile, TileType
    g, p = _game()
    tp = g.engine.turn_processor
    p.set_stat('rested_turn', g.state.turn_count - 1)
    assert tp._is_resting(p)                              # waited last turn, nobody about

    for dx in range(0, 4):                                # open sight to a monster two tiles away
        g.state.dungeon_map.tiles[p.x + dx][p.y] = Tile(TileType.FLOOR)
    mon = Monster(name="Watcher", content_id="goblin", x=p.x + 2, y=p.y, hp=10, max_hp=10, attack=1, defense=0)
    mon.is_alive = True
    g.state.entities[mon.entity_id] = mon
    assert not tp._is_resting(p)                          # a stand-off, not a rest

    g.state.dungeon_map.tiles[p.x + 1][p.y] = Tile(TileType.WALL)   # wall between: it cannot see us
    assert tp._is_resting(p)

    p.set_stat('rested_turn', g.state.turn_count - 5)     # waited long ago
    assert not tp._is_resting(p)
