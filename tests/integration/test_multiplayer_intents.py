"""Intents over real websockets: the server picks the actor from the session seat."""

import asyncio

import pytest

from protocol.messages import Message
from server.websocket_server import VeinbornServer
from tests.integration.test_multiplayer_real_sockets import _Client, _until


async def _start_two(server, port):
    alice, bob = _Client("Alice"), _Client("Bob")
    await alice.connect(port)
    await bob.connect(port)
    await alice.send(Message.create_game("Intents", max_players=4))
    await _until(lambda: alice.game_id)
    await bob.send(Message.join_game(alice.game_id, player_class="mage"))
    await alice.send(Message(type="ready", data={"ready": True}))
    await bob.send(Message(type="ready", data={"ready": True}))
    await _until(lambda: alice.entity_id and bob.entity_id and alice.game_started)
    return alice, bob


def _pos(client, entity_id):
    return client.position_of(entity_id)


@pytest.mark.asyncio
async def test_intent_moves_the_senders_own_character_and_ignores_a_spoofed_actor():
    server = VeinbornServer("127.0.0.1", 0)
    await server.start()
    port = server.server.sockets[0].getsockname()[1]
    alice = bob = None
    try:
        alice, bob = await _start_two(server, port)
        before_bob = _pos(alice, bob.entity_id)

        # Alice tries to move Bob by naming him as the actor: the payload actor is dropped
        moved = False
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            start = _pos(alice, alice.entity_id)
            await alice.send(Message.intent("move", dx=dx, dy=dy, actor_id=bob.entity_id))
            await asyncio.sleep(0.15)
            if _pos(alice, alice.entity_id) != start:
                moved = True
                break
        assert moved, alice.errors
        assert _pos(alice, bob.entity_id) == before_bob  # Bob never moved
    finally:
        for c in (alice, bob):
            if c:
                await c.close()
        await server.stop()


@pytest.mark.asyncio
async def test_unknown_or_malformed_intent_gets_an_error_not_a_crash():
    server = VeinbornServer("127.0.0.1", 0)
    await server.start()
    port = server.server.sockets[0].getsockname()[1]
    alice = bob = None
    try:
        alice, bob = await _start_two(server, port)
        await alice.send(Message.intent("dance"))
        await alice.send(Message(type="intent", data={"intent": 5, "args": []}))
        await _until(lambda: len(alice.errors) >= 2)
        assert any("Invalid intent" in e for e in alice.errors)
    finally:
        for c in (alice, bob):
            if c:
                await c.close()
        await server.stop()


@pytest.mark.asyncio
async def test_round_waits_for_the_whole_party_and_refuses_a_second_action():
    server = VeinbornServer("127.0.0.1", 0)
    await server.start()
    port = server.server.sockets[0].getsockname()[1]
    alice = bob = None
    try:
        alice, bob = await _start_two(server, port)
        game = await server.game_manager.get_game(alice.game_id)
        mp = game.mp_game_state
        assert mp.round_number == 0

        await alice.send(Message.intent("wait"))
        await _until(lambda: mp.actions_this_round == 1)
        assert mp.round_number == 0  # Bob still owes his action
        assert mp.waiting_on() == [bob.player_id]

        # Alice tries to act again before Bob has: refused, not queued
        await alice.send(Message.intent("wait"))
        await _until(lambda: any("Waiting for the party" in e for e in alice.errors))
        assert any("Bob" in e for e in alice.errors)
        assert mp.actions_this_round == 1

        # Bob acts: monsters move once, the round rolls over, both are owed again
        turn_before = mp.game_state.turn_count
        await bob.send(Message.intent("wait"))
        await _until(lambda: mp.round_number == 1)
        assert mp.game_state.turn_count == turn_before + 1
        assert sorted(mp.waiting_on()) == sorted([alice.player_id, bob.player_id])

        # The clients see who the round is waiting on
        await _until(lambda: alice.snapshot.round.number == 1)
        assert sorted(alice.snapshot.round.waiting_on) == sorted([alice.entity_id, bob.entity_id])
    finally:
        for c in (alice, bob):
            if c:
                await c.close()
        await server.stop()
