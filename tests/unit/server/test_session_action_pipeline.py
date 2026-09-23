"""VB-24: GameSession must run actions through the same post-action pipeline as Game."""

import pytest

from core.actions.wait_action import WaitAction
from core.base.action import ActionOutcome
from server.game_session import GameSession


class _FreeAction:
    """Duck-typed action that succeeds without consuming a turn.

    Deliberately not an Action subclass: the registry-completeness test walks
    Action.__subclasses__() and would flag a test-only stub.
    """

    def __init__(self, actor_id):
        self.actor_id = actor_id

    def get_action_type(self):
        return "_FreeAction"

    def execute(self, context):
        return ActionOutcome.success(took_turn=False, message="That was free.")


async def _started_session():
    game = GameSession("game1", "Test Game", max_players=4, actions_per_round=4)
    await game.add_player("player1", "Alice", "warrior")
    await game.start_game(seed=42)
    return game


@pytest.mark.asyncio
async def test_successful_action_message_reaches_shared_log():
    game = await _started_session()
    before = game.mp_game_state.game_state.message_count

    success, error = await game.process_action("player1", WaitAction(actor_id="player"))

    assert success, error
    state = game.mp_game_state.game_state
    assert state.message_count == before + 1
    assert state.get_recent_messages(1)[0].endswith("waits.")


@pytest.mark.asyncio
async def test_action_events_are_published_to_session_event_bus():
    game = await _started_session()
    published = []
    game.event_bus.publish_all = published.extend

    await game.process_action("player1", WaitAction(actor_id="player"))

    assert [e["type"] for e in published] == ["actor_waited"]


@pytest.mark.asyncio
async def test_turn_taking_action_counts_toward_round_quota():
    game = await _started_session()

    await game.process_action("player1", WaitAction(actor_id="player"))

    assert game.mp_game_state.actions_this_round == 1


@pytest.mark.asyncio
async def test_free_action_does_not_consume_round_quota():
    game = await _started_session()

    success, error = await game.process_action("player1", _FreeAction(actor_id="player"))

    assert success, error
    assert game.mp_game_state.actions_this_round == 0


@pytest.mark.asyncio
async def test_disconnected_player_wait_goes_through_pipeline():
    game = await _started_session()
    await game.disconnect_player("player1")
    before = game.mp_game_state.game_state.message_count

    success, error = await game.process_disconnected_player_action("player1")

    assert success, error
    assert game.mp_game_state.game_state.message_count == before + 1
    assert game.mp_game_state.actions_this_round == 1
