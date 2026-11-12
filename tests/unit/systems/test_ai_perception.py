"""Engine perception and provocation (VB-60, ADR-019).

perceive(): a player within aggro_range and in line of sight, or one the monster
saw or was attacked by within memory_turns. Provocation comes from
ATTACK_RESOLVED events. The contract test runs every registered behaviour.
"""

import pytest

from core.base.entity import EntityType
from core.character_class import CharacterClass
from core.events import create_attack_event
from core.events.events import GameEventType
from core.extensions import ai_behaviors
from core.game import Game
from core.world import Tile, TileType

pytestmark = pytest.mark.unit

PX, PY = 20, 12  # player position in the open arena


def arena(character_class=None):
    """A game on an open floor (walls only on the border), no monsters, no obstacles."""
    g = Game()
    g.start_new_game(seed=42, character_class=character_class)
    m = g.state.dungeon_map
    for x in range(1, m.width - 1):
        for y in range(1, m.height - 1):
            m.tiles[x][y] = Tile(TileType.FLOOR)
    for e in list(g.state.entities.values()):
        if e.entity_type in (EntityType.MONSTER, EntityType.ORE_VEIN, EntityType.FORGE):
            g.context.remove_entity(e.entity_id)
    p = g.state.player
    p.x, p.y = PX, PY
    g.state.messages.clear()
    return g


@pytest.fixture
def game():
    return arena()


def add(game, dx, dy=0, monster_id="goblin", ai_type=None, **params):
    mon = game.entity_loader.create_monster(monster_id, PX + dx, PY + dy)
    if ai_type:
        mon.set_stat('ai_type', ai_type)
    if params:
        mon.set_stat('ai_params', params)
    game.context.add_entity(mon)
    return mon


def ai(game):
    return game.context.get_system('ai')


def perceive(game, mon):
    return ai(game).perceive(mon, ai(game).params_for(mon))


def wall(game, x, y0=1, y1=None):
    m = game.state.dungeon_map
    for y in range(y0, (y1 or m.height - 2) + 1):
        m.tiles[x][y] = Tile(TileType.WALL)


def tick(game, turns=1):
    for _ in range(turns):
        game.state.turn_count += 1
        ai(game).update()


# --- sight ----------------------------------------------------------------------

def test_sees_a_player_within_aggro_range_in_line_of_sight(game):
    mon = add(game, 5, aggro_range=6)
    assert perceive(game, mon) is game.state.player


def test_does_not_see_beyond_aggro_range(game):
    mon = add(game, 7, aggro_range=6)
    assert perceive(game, mon) is None


def test_aggro_range_is_8_way_so_diagonals_count_once(game):
    mon = add(game, 5, 5, aggro_range=5)
    assert perceive(game, mon) is game.state.player


def test_walls_block_sight(game):
    mon = add(game, 4, aggro_range=10)
    wall(game, PX + 2)
    assert perceive(game, mon) is None


def test_monster_yaml_aggro_range_is_used(game):
    troll = add(game, 7, monster_id="troll")  # troll aggro_range 6 in monsters.yaml
    orc = add(game, -7, monster_id="orc")      # orc aggro_range 10
    assert perceive(game, troll) is None
    assert perceive(game, orc) is game.state.player


# --- memory ---------------------------------------------------------------------

def test_remembers_a_seen_player_after_losing_sight(game):
    mon = add(game, 4, aggro_range=6, memory_turns=3)
    assert perceive(game, mon) is game.state.player
    wall(game, PX + 2)
    game.state.turn_count += 3
    assert perceive(game, mon) is game.state.player


def test_forgets_after_memory_turns(game):
    mon = add(game, 4, aggro_range=6, memory_turns=3)
    perceive(game, mon)
    wall(game, PX + 2)
    game.state.turn_count += 4
    assert perceive(game, mon) is None
    assert mon.get_stat('target_id') is None


def test_aggressive_monster_follows_around_a_wall_it_remembers(game):
    mon = add(game, 3, ai_type='aggressive', aggro_range=6, memory_turns=20)
    perceive(game, mon)
    wall(game, PX + 2, PY - 3, PY + 3)  # short wall: blocks sight, can be walked around
    assert perceive(game, mon) is game.state.player  # by memory, not sight
    tick(game, 10)
    assert mon.is_adjacent(game.state.player)


# --- provocation ----------------------------------------------------------------

def test_attack_event_provokes_the_defender(game):
    mon = add(game, 30, aggro_range=2)  # far out of sight range
    p = game.state.player
    game.event_bus.publish_dict(create_attack_event(p.entity_id, mon.entity_id, damage=3, killed=False))
    assert ai(game).provoked_by(mon, ai(game).params_for(mon)) is p
    assert perceive(game, mon) is p


def test_provocation_wears_off_after_memory_turns(game):
    mon = add(game, 30, aggro_range=2, memory_turns=5)
    p = game.state.player
    game.event_bus.publish_dict(create_attack_event(p.entity_id, mon.entity_id, damage=3, killed=False))
    game.state.turn_count += 6
    assert ai(game).provoked_by(mon, ai(game).params_for(mon)) is None
    assert perceive(game, mon) is None


def test_force_bolt_provokes_a_short_sighted_mimic_end_to_end():
    game = arena(CharacterClass.MAGE)
    mimic = add(game, 5, monster_id="mimic")  # mimic aggro_range 1
    assert perceive(game, mimic) is None
    assert game.handle_player_action('ability', ability='force_bolt')
    assert mimic.get_stat('provoked_by') == game.state.player.entity_id


def test_reloading_a_game_does_not_leave_a_stale_ai_listening(game, tmp_path, monkeypatch):
    monkeypatch.setattr(game.save_system, 'save_dir', tmp_path, raising=False)
    before = game.event_bus.get_subscriber_count(GameEventType.ATTACK_RESOLVED)
    assert game.save_game("t") and game.load_game("t")
    assert game.event_bus.get_subscriber_count(GameEventType.ATTACK_RESOLVED) == before


# --- behaviours on top of perception -----------------------------------------------

def test_neutral_ignores_an_adjacent_player_until_attacked(game):
    p = game.state.player
    mon = add(game, 1, ai_type='neutral')
    tick(game, 5)
    assert p.hp == p.max_hp
    game.event_bus.publish_dict(create_attack_event(p.entity_id, mon.entity_id, damage=1, killed=False))
    mon.x, mon.y = PX + 1, PY
    hp_before, msgs_before = p.hp, len(game.state.messages)
    tick(game, 5)
    assert p.hp < hp_before or len(game.state.messages) > msgs_before


def test_defensive_engages_only_close_players_unless_attacked(game):
    p = game.state.player
    mon = add(game, 7, ai_type='defensive', aggro_range=10)  # sees at 7, engages within 5
    tick(game)
    assert ai(game).distance(mon, p) >= 6  # only wandered (at most one step)
    game.event_bus.publish_dict(create_attack_event(p.entity_id, mon.entity_id, damage=1, killed=False))
    start = ai(game).distance(mon, p)
    tick(game, 3)
    assert ai(game).distance(mon, p) < start


# --- contract: every registered behaviour respects perception ------------------------

def _shipped_behaviours():
    return sorted(n for n in ai_behaviors.names() if not n.startswith('_'))


@pytest.fixture
def spy(game, monkeypatch):
    """Record every toolkit call a behaviour makes with the player as the target."""
    calls = []
    system = ai(game)
    p = game.state.player
    for name in ('attack', 'move_towards', 'flee_from'):
        real = getattr(system, name)

        def wrapper(monster, target, *a, _real=real, _name=name, **k):
            if target is p:
                calls.append(_name)
            return _real(monster, target, *a, **k)
        monkeypatch.setattr(system, name, wrapper)
    real_summon = system.summon
    monkeypatch.setattr(system, 'summon', lambda *a, **k: calls.append('summon') or real_summon(*a, **k))
    return calls


@pytest.mark.parametrize("behaviour", _shipped_behaviours())
def test_contract_an_unperceived_player_is_left_alone(game, spy, behaviour):
    add(game, 12, ai_type=behaviour, monster_id="orc", aggro_range=6)
    tick(game, 5)
    assert spy == [], f"{behaviour} acted on a player it cannot perceive: {spy}"
    assert game.state.player.hp == game.state.player.max_hp


@pytest.mark.parametrize("behaviour", _shipped_behaviours())
def test_contract_a_perceived_attacker_gets_a_reaction(game, spy, behaviour):
    """Positive control for the test above: the spy does see reactions."""
    p = game.state.player
    mon = add(game, 1, ai_type=behaviour, monster_id="orc", aggro_range=6)
    game.event_bus.publish_dict(create_attack_event(p.entity_id, mon.entity_id, damage=1, killed=False))
    tick(game, 2)
    assert spy, f"{behaviour} ignored an adjacent player who attacked it"
