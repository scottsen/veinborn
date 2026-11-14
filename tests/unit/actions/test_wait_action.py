"""Unit tests for WaitAction."""
import pytest
from core.actions.wait_action import WaitAction

pytestmark = pytest.mark.unit


def test_wait_validates_for_alive_player(game_context):
    player = game_context.get_player()
    action = WaitAction(actor_id=player.entity_id)
    assert action.validate(game_context)


def test_wait_execute_takes_turn_and_succeeds(game_context):
    player = game_context.get_player()
    action = WaitAction(actor_id=player.entity_id)
    outcome = action.execute(game_context)
    assert outcome.is_success
    assert outcome.took_turn is True
    assert any('waits' in m for m in outcome.messages)
    assert any(e['type'] == 'actor_waited' for e in outcome.events)


def test_wait_execute_fails_for_unknown_actor(game_context):
    """VB-23/VB-16: an actor_id that resolves to nothing must fail cleanly,
    not silently execute as the local player."""
    action = WaitAction(actor_id='does-not-exist')
    outcome = action.execute(game_context)
    assert not outcome.is_success


def test_wait_round_trip_serialization():
    a = WaitAction(actor_id='p1')
    d = a.to_dict()
    assert d == {'action_type': 'WaitAction', 'actor_id': 'p1'}
    restored = WaitAction.from_dict(d)
    assert restored.actor_id == 'p1'


def test_quiet_wait_adds_no_message_but_still_publishes(game_context):
    player = game_context.get_all_players()[0]
    outcome = WaitAction(player.entity_id, quiet=True).execute(game_context)
    assert outcome.took_turn and outcome.messages == []
    assert [e['type'] for e in outcome.events] == ['actor_waited']
