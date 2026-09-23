"""Two-client co-op session over real websocket connections.

The other multiplayer integration tests drive VeinbornServer with mock websockets, which is
how a handshake that failed on every real connection (websockets >= 13 no longer passes
`path`), a lobby->started transition that never reached clients as a full state, and
monster-turn messages that never reached deltas all went unnoticed.
"""

import asyncio
import re

import pytest
import websockets

from server.messages import Message
from server.state_delta import StateDelta
from server.websocket_server import VeinbornServer


class _Client:
    def __init__(self, name):
        self.name = name
        self.state = None
        self.game_id = None
        self.player_id = None
        self.errors = []
        self.game_started = False

    async def connect(self, port, token=None):
        self.ws = await websockets.connect(f"ws://127.0.0.1:{port}")
        await self.ws.send(Message.auth(self.name, token).to_json())
        reply = Message.from_json(await self.ws.recv())
        assert reply.type == "auth_success", reply.data
        self.player_id = reply.data["player_id"]
        self.session_id = reply.data["session_id"]
        self.token = reply.data["auth_token"]
        self._reader = asyncio.create_task(self._read())

    async def _read(self):
        # Mirrors ui/multiplayer_client.MultiplayerClient._handle_message
        try:
            async for raw in self.ws:
                msg = Message.from_json(raw)
                if msg.type == "system":
                    found = re.search(r"ID: (\S+)\)", msg.data.get("message", ""))
                    self.game_id = found.group(1) if found else self.game_id
                elif msg.type == "error":
                    self.errors.append(msg.data.get("message"))
                elif msg.type == "game_start":
                    self.game_started = True
                elif msg.type == "state":
                    self.state = msg.data["state"]
                elif msg.type == "delta" and self.state is not None:
                    self.state = StateDelta.apply_delta(self.state, msg.data["changes"])
        except websockets.ConnectionClosed:
            pass

    @property
    def entity_id(self):
        for player in (self.state or {}).get("players", []):
            if player.get("player_id") == self.player_id:
                return player.get("entity_id")
        return None

    async def send(self, msg):
        await self.ws.send(msg.to_json())

    async def move(self, dx, dy):
        await self.send(Message(type="action", data={"action_data": {
            "action_type": "MoveAction", "actor_id": self.entity_id, "dx": dx, "dy": dy}}))


async def _until(predicate, timeout=3.0):
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while not predicate():
        assert loop.time() < deadline, "timed out waiting for the server"
        await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_two_real_clients_can_start_and_play_a_coop_session():
    server = VeinbornServer("127.0.0.1", 0)
    await server.start()
    port = server.server.sockets[0].getsockname()[1]
    alice, bob = _Client("Alice"), _Client("Bob")
    try:
        await alice.connect(port)
        await bob.connect(port)

        await alice.send(Message.create_game("Real Sockets", max_players=4))
        await _until(lambda: alice.game_id)
        await bob.send(Message.join_game(alice.game_id, player_class="mage"))
        await alice.send(Message(type="ready", data={"ready": True}))
        await bob.send(Message(type="ready", data={"ready": True}))

        # Clients learn the game started AND their own entity id from the state they receive
        await _until(lambda: alice.entity_id and bob.entity_id and alice.game_started)
        assert alice.entity_id != bob.entity_id
        assert alice.state["is_started"] and bob.state["is_started"]

        # Drive some actions from both clients; every move must be accepted or cleanly refused
        game = await server.game_manager.get_game(alice.game_id)
        for i in range(40):
            await (alice if i % 2 == 0 else bob).move(*[(1, 0), (0, 1), (-1, 0), (0, -1)][i % 4])
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.2)

        assert game.mp_game_state.round_number > 0
        assert not [e for e in alice.errors + bob.errors if "not match" in e or "not found" in e]

        # What the clients rebuilt from deltas is what the server holds
        truth = game.get_state_dict(use_delta=False)
        for client in (alice, bob):
            assert client.state == truth, client.name
    finally:
        for client in (alice, bob):
            if getattr(client, "ws", None):
                await client.ws.close()
        await server.stop()


@pytest.mark.asyncio
async def test_dropped_client_reconnects_with_a_full_state_and_no_server_errors(caplog):
    server = VeinbornServer("127.0.0.1", 0)
    await server.start()
    port = server.server.sockets[0].getsockname()[1]
    alice, bob = _Client("Alice"), _Client("Bob")
    try:
        await alice.connect(port)
        await bob.connect(port)
        await alice.send(Message.create_game("Drop", max_players=4))
        await _until(lambda: alice.game_id)
        await bob.send(Message.join_game(alice.game_id))
        await alice.send(Message(type="ready", data={"ready": True}))
        await bob.send(Message(type="ready", data={"ready": True}))
        await _until(lambda: alice.entity_id and bob.entity_id)
        game = await server.game_manager.get_game(alice.game_id)
        bob_entity, bob_token = bob.entity_id, bob.token

        with caplog.at_level("ERROR"):
            await bob.ws.close()  # abrupt drop, no leave_game
            await _until(lambda: game.players[bob.player_id].is_disconnected())
            for i in range(8):
                await alice.move(*[(1, 0), (0, 1), (-1, 0), (0, -1)][i % 4])
                await asyncio.sleep(0.01)

            bob2 = _Client("Bob")
            await bob2.connect(port, token=bob_token)
            await bob2.send(Message.reconnect(bob2.session_id))
            await _until(lambda: bob2.state is not None and bob2.entity_id)

        assert bob2.player_id == bob.player_id
        assert bob2.entity_id == bob_entity
        assert bob2.state["is_started"]
        assert not game.players[bob.player_id].is_disconnected()
        assert caplog.text == ""  # no server-side tracebacks for a normal disconnect
    finally:
        for client in (alice, bob, locals().get("bob2")):
            if client is not None and getattr(client, "ws", None):
                await client.ws.close()
        await server.stop()
