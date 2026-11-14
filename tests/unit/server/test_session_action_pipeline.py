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

    free = True

    def __init__(self, actor_id):
        self.actor_id = actor_id

    def get_action_type(self):
        return "_FreeAction"

    def execute(self, context):
        return ActionOutcome.success(took_turn=False, message="That was free.")


async def _started_session():
    game = GameSession("game1", "Test Game", max_players=4)
    await game.add_player("player1", "Alice", "warrior")
    await game.start_game(seed=42)
    return game


def _seat(game):
    """Alice's entity id (assigned by the seat, never a fixed 'player')."""
    return game.mp_game_state.get_player_entity_id("player1")


@pytest.mark.asyncio
async def test_successful_action_message_reaches_shared_log():
    game = await _started_session()
    before = game.mp_game_state.game_state.message_count

    success, error = await game.process_action("player1", WaitAction(actor_id=_seat(game)))

    assert success, error
    state = game.mp_game_state.game_state
    assert state.message_count == before + 1
    assert state.get_recent_messages(1)[0].endswith("waits.")


@pytest.mark.asyncio
async def test_action_events_are_published_to_session_event_bus():
    game = await _started_session()
    published = []
    game.event_bus.publish_all = published.extend

    await game.process_action("player1", WaitAction(actor_id=_seat(game)))

    assert [e["type"] for e in published] == ["actor_waited"]


@pytest.mark.asyncio
async def test_turn_taking_action_completes_the_round_for_a_party_of_one():
    game = await _started_session()

    await game.process_action("player1", WaitAction(actor_id=_seat(game)))

    assert game.mp_game_state.round_number == 1
    assert game.mp_game_state.actions_this_round == 0
    assert game.mp_game_state.game_state.turn_count == 1  # the world ticked once


@pytest.mark.asyncio
async def test_free_action_does_not_use_up_the_players_action():
    game = await _started_session()

    success, error = await game.process_action("player1", _FreeAction(actor_id=_seat(game)))

    assert success, error
    assert game.mp_game_state.actions_this_round == 0
    assert game.mp_game_state.round_number == 0
    assert game.mp_game_state.game_state.turn_count == 0


@pytest.mark.asyncio
async def test_messages_added_through_context_reach_the_viewers_snapshot():
    """Monster-turn messages go through GameContext.add_message; it used to append to
    .messages directly, skipping message_count (and so what clients are sent)."""
    from core.base.game_context import GameContext

    game = await _started_session()
    count_before = game.mp_game_state.game_state.message_count

    GameContext(game.mp_game_state.game_state).add_message("Goblin hits Alice for 1 damage!")
    snap = game.snapshot_for("player1")

    assert game.mp_game_state.game_state.message_count == count_before + 1
    assert snap.messages[-1] == "Goblin hits Alice for 1 damage!"


def test_context_messages_respect_the_message_cap(simple_game_state):
    from core.base.game_context import GameContext

    state = simple_game_state
    context = GameContext(state)
    for i in range(150):
        context.add_message(f"m{i}")

    assert len(state.messages) == 100
    assert state.message_count == 150


@pytest.mark.asyncio
async def test_use_and_drop_intents_without_an_item_pick_one_for_a_remote_client():
    """Phase 4a: the quick-use / quick-drop keys are plain intents, so a remote client sends them as-is."""
    from core.loot import LootGenerator
    game = await _started_session()
    alice = game.mp_game_state.get_player_entity("player1")
    alice.inventory.clear()
    potion = LootGenerator.get_instance().create_item("potion_healing")
    alice.add_to_inventory(potion)
    alice.hp = 1

    success, error = await game.process_intent("player1", "use")
    assert success, error
    assert alice.hp > 1 and potion not in alice.inventory

    success, error = await game.process_intent("player1", "drop")
    assert not success and error == "You have nothing to drop."
