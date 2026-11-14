"""The Engine is the one rules loop; single-player and multiplayer are hosts around it (VB-93)."""

from core.engine import Engine
from core.events import EventBus
from core.game import Game


def _game():
    game = Game()
    game.start_new_game(seed=11, player_name="E")
    return game


def test_game_is_a_shell_over_one_engine():
    game = _game()
    assert isinstance(game.engine, Engine)
    assert game.turn_processor is game.engine.turn_processor
    assert game.floor_manager is game.engine.floor_manager
    assert game.action_factory is game.engine.action_factory
    assert game.ai_system is game.engine.ai_system
    assert game.context.get_system('ai') is game.engine.ai_system


def test_execute_reports_took_turn_and_leaves_the_tick_to_the_host():
    game = _game()
    turn = game.state.turn_count
    action = game.engine.make_action('wait')
    result = game.engine.execute(action, 'wait')
    assert result.took_turn and result.outcome.is_success
    assert game.state.turn_count == turn  # no tick until the host asks
    game.engine.tick()
    assert game.state.turn_count == turn + 1


def test_log_failures_decides_whether_a_failed_action_reaches_the_shared_log():
    game = _game()
    descend = game.engine.make_action('descend')  # not standing on stairs
    before = game.state.message_count

    result = game.engine.execute(descend, 'descend')
    assert not result.outcome.is_success and not result.took_turn
    assert game.state.message_count > before  # single-player logs the refusal

    quiet = Engine(game.context, game.config, EventBus(), spawner=game.spawner, log_failures=False)
    before = game.state.message_count
    assert not quiet.execute(descend, 'descend').outcome.is_success
    assert game.state.message_count == before  # multiplayer reports it to the sender only
    quiet.close()


def test_make_action_takes_an_explicit_actor():
    game = _game()
    assert game.engine.make_action('wait', actor_id='nobody') is None
    assert game.engine.make_action('wait', actor_id=game.state.player.entity_id).actor_id == game.state.player.entity_id


def test_close_detaches_handlers_and_ai_from_the_bus():
    game = _game()
    bus = game.event_bus
    engine = game.engine
    n = sum(len(v) for v in bus.subscribers.values())
    assert engine.event_handlers
    engine.close()
    assert engine.event_handlers == []
    assert sum(len(v) for v in bus.subscribers.values()) < n


def test_reinitialising_replaces_the_engine_without_double_subscribing():
    game = _game()
    first = game.engine
    game._initialize_subsystems()
    assert game.engine is not first
    kinds = [type(h).__name__ for h in game.event_handlers]
    assert len(kinds) == len(set(kinds))
