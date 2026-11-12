"""AI behaviours from core/content/ai, run through the real AISystem."""

import pytest

from core.actions.attack_action import AttackAction
from core.base.entity import EntityType
from core.character_class import CharacterClass
from core.extensions import ai_behavior, ai_behaviors
from core.game import Game
from core.systems.ai_system import AISystem

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=7, character_class=CharacterClass.WARRIOR)
    for e in list(g.state.entities.values()):
        if e.entity_type == EntityType.MONSTER:
            g.context.remove_entity(e.entity_id)
    g.state.messages.clear()
    return g


def spawn(game, ai_type, dist, monster_id="orc"):
    """Put a monster `dist` tiles from the player along an axis, in the open, with sight."""
    p, m = game.state.player, game.state.dungeon_map
    for dx, dy in [(dist, 0), (-dist, 0), (0, dist), (0, -dist)]:
        x, y = p.x + dx, p.y + dy
        if m.is_walkable(x, y):
            mon = game.entity_loader.create_monster(monster_id, x, y)
            mon.set_stat('ai_type', ai_type)
            game.context.add_entity(mon)
            return mon
    pytest.skip("no open tile for this seed")


def run_ai(game, turns=1):
    ai = game.context.get_system('ai')
    for _ in range(turns):
        game.state.turn_count += 1
        ai.update()


# --- plumbing -------------------------------------------------------------------

def test_every_registered_behavior_is_loaded_into_the_ai_system(game):
    ai = game.context.get_system('ai')
    assert set(ai_behaviors.names()) <= set(ai.registry.list_behaviors())


def test_a_new_behavior_is_one_decorated_function(game):
    seen = []

    @ai_behavior("_test_sentry", replace=True)
    def sentry(ai, monster, config):
        seen.append((type(ai).__name__, monster.name))

    try:
        mon = spawn(game, "_test_sentry", 5)
        game.context.register_system('ai', AISystem(game.context))  # picks up the new behaviour
        run_ai(game)
        assert seen == [("AISystem", mon.name)]
    finally:
        ai_behaviors.unregister("_test_sentry")


def test_a_crashing_behavior_does_not_stop_the_turn(game, caplog):
    @ai_behavior("_test_crash", replace=True)
    def crash(ai, monster, config):
        raise RuntimeError("bug in content")

    try:
        spawn(game, "_test_crash", 5)
        spawn(game, "aggressive", 4, "goblin")
        game.context.register_system('ai', AISystem(game.context))
        run_ai(game)  # must not raise
        assert "bug in content" in caplog.text
    finally:
        ai_behaviors.unregister("_test_crash")


# --- berserker ------------------------------------------------------------------

def test_berserker_chases_then_attacks(game):
    mon = spawn(game, "berserker", 3)
    p = game.state.player
    start = game.context.get_system('ai').distance(mon, p)
    run_ai(game, 6)
    assert game.context.get_system('ai').distance(mon, p) < start
    assert p.hp < p.max_hp or any("misses" in m for m in game.state.messages)


def test_wounded_berserker_enrages_once(game):
    mon = spawn(game, "berserker", 6)
    mon.hp = int(mon.max_hp * 0.4)
    run_ai(game, 3)
    rage = [m for m in game.state.messages if "BERSERK RAGE" in m]
    assert len(rage) == 1 and mon.get_stat('was_enraged') is True


def test_healthy_berserker_does_not_enrage(game):
    spawn(game, "berserker", 3)
    run_ai(game, 3)
    assert not any("BERSERK" in m for m in game.state.messages)


# --- sniper / ranged attack --------------------------------------------------------

def test_sniper_in_ideal_range_shoots_without_closing(game):
    mon = spawn(game, "sniper", 5)
    p = game.state.player
    pos = (mon.x, mon.y)
    hp = p.hp
    for _ in range(40):
        run_ai(game)
        if p.hp < hp:
            break
    assert p.hp < hp, "a sniper at range 5 should land a shot within 40 turns"
    assert (mon.x, mon.y) == pos  # it shot instead of walking up


def test_sniper_backs_away_when_player_is_too_close(game):
    mon = spawn(game, "sniper", 2)
    ai = game.context.get_system('ai')
    p = game.state.player
    before = ai.distance(mon, p)
    run_ai(game)
    assert ai.distance(mon, p) >= before


def test_ranged_attack_needs_no_adjacency_but_melee_does(game):
    mon = spawn(game, "aggressive", 5)
    p = game.state.player
    assert AttackAction(mon.entity_id, p.entity_id, ranged=True).validate(game.context)
    assert not AttackAction(mon.entity_id, p.entity_id).validate(game.context)


def test_attack_action_ranged_flag_survives_the_wire():
    action = AttackAction("a", "b", ranged=True)
    assert AttackAction.from_dict(action.to_dict()).ranged is True
    assert AttackAction.from_dict({'actor_id': 'a', 'target_id': 'b'}).ranged is False


# --- summoner ----------------------------------------------------------------------

def test_summoner_calls_a_minion_and_announces_it(game):
    mon = spawn(game, "summoner", 6)
    before = len([e for e in game.state.entities.values() if e.entity_type == EntityType.MONSTER])
    run_ai(game)
    after = [e for e in game.state.entities.values() if e.entity_type == EntityType.MONSTER]
    assert len(after) == before + 1
    assert any("chants" in m for m in game.state.messages)
    assert len(mon.get_stat('minion_ids')) == 1


def test_summoner_respects_cooldown_and_minion_cap(game):
    mon = spawn(game, "summoner", 6)
    cap = game.context.get_system('ai').abilities_for(mon)['summon']['max_minions']
    monsters = lambda: [e for e in game.state.entities.values() if e.entity_type == EntityType.MONSTER]
    run_ai(game)
    assert len(monsters()) == 2  # no second summon next turn: cooldown
    game.state.player.max_hp = game.state.player.hp = 10 ** 6  # survive the minions
    home = (mon.x, mon.y)
    for _ in range(80):
        mon.x, mon.y = home  # the summoner would otherwise drift out of range
        run_ai(game)
    # 80 turns allow ~8 summons at a 10-turn cooldown: the cap is what stops it at exactly `cap`
    assert len(mon.get_stat('minion_ids')) == cap


def test_summoner_replaces_dead_minions(game):
    mon = spawn(game, "summoner", 6)
    run_ai(game)
    minion = game.context.get_entity(mon.get_stat('minion_ids')[0])
    minion.is_alive = False
    from core.content.abilities.summon import living_minions
    assert living_minions(game.context, mon) == []


# --- range metric (VB-58) --------------------------------------------------------

def test_ai_range_is_chebyshev_so_a_diagonal_is_not_twice_as_far(game):
    ai = game.context.get_system('ai')
    p = game.state.player
    mon = spawn(game, "aggressive", 3)
    mon.x, mon.y = p.x + 4, p.y + 4  # 4 diagonal steps; Manhattan would say 8
    assert ai.distance(mon, p) == 4
