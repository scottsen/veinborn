"""Two-client co-op session over real websocket connections.

The other multiplayer integration tests drive VeinbornServer with mock websockets, which is
how a handshake that failed on every real connection (websockets >= 13 no longer passes
`path`), a lobby->started transition that never reached clients as a full state, and
monster-turn messages that never reached deltas all went unnoticed.

The clients here ARE `ui.multiplayer_client.MultiplayerClient`: the test decodes server
messages with the code a player runs, so the two cannot drift apart.
"""

import asyncio

import pytest

from protocol.messages import Message
from ui.multiplayer_client import MultiplayerClient
from server.websocket_server import VeinbornServer


class _Client:
    """A real MultiplayerClient plus the few conveniences the tests read."""

    def __init__(self, name):
        self.name = name
        self.client = MultiplayerClient(host="127.0.0.1")

    async def connect(self, port, token=None):
        self.client.port = port
        assert await self.client.connect(self.name, auth_token=token)

    @property
    def ws(self):
        return self.client.ws

    @property
    def player_id(self):
        return self.client.state.player_id

    @property
    def session_id(self):
        return self.client.state.session_id

    @property
    def token(self):
        return self.client.state.auth_token

    @property
    def game_id(self):
        return self.client.state.game_id

    @property
    def errors(self):
        return self.client.state.errors

    @property
    def snapshot(self):
        return self.client.snapshot

    @property
    def game_started(self):
        return self.client.snapshot is not None

    @property
    def entity_id(self):
        return self.snapshot.player.entity_id if self.snapshot else None

    def position_of(self, entity_id):
        """Where this client sees an entity (itself, or something in its world)."""
        snap = self.snapshot
        if snap.player.entity_id == entity_id:
            return snap.player.x, snap.player.y
        for e in snap.entities:
            if e.entity_id == entity_id:
                return e.x, e.y

    async def send(self, msg):
        await self.ws.send(msg.to_json())

    async def move(self, dx, dy):
        await self.client.submit("move", dx=dx, dy=dy)

    async def close(self):
        if self.client.ws is not None:
            await self.client.disconnect()


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

        # Each client learns the game started, and who it is, from its own snapshot
        await _until(lambda: alice.game_started and bob.game_started)
        assert alice.entity_id != bob.entity_id
        assert alice.client.game_info["is_started"] and bob.client.game_info["is_started"]
        assert [m.name for m in alice.snapshot.party] == ["Alice", "Bob"]

        # Drive actions from both clients; each is accepted or cleanly refused
        game = await server.game_manager.get_game(alice.game_id)
        for i in range(40):
            await (alice if i % 2 == 0 else bob).move(*[(1, 0), (0, 1), (-1, 0), (0, -1)][i % 4])
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.3)

        assert game.mp_game_state.round_number > 0
        assert not [e for e in alice.errors + bob.errors if "not match" in e or "not found" in e]

        # What each client holds is exactly what the server would show that player now
        for client in (alice, bob):
            assert client.snapshot == game.snapshot_for(client.player_id), client.name
    finally:
        for client in (alice, bob):
            await client.close()
        await server.stop()


@pytest.mark.asyncio
async def test_dropped_client_reconnects_with_a_snapshot_sent_to_it_alone(caplog):
    server = VeinbornServer("127.0.0.1", 0)
    await server.start()
    port = server.server.sockets[0].getsockname()[1]
    alice, bob = _Client("Alice"), _Client("Bob")
    bob2 = None
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
        bob_entity, bob_token, bob_player = bob.entity_id, bob.token, bob.player_id

        with caplog.at_level("ERROR"):
            await bob.ws.close()  # abrupt drop, no leave_game
            await _until(lambda: game.players[bob_player].is_disconnected())
            for i in range(8):
                await alice.move(*[(1, 0), (0, 1), (-1, 0), (0, -1)][i % 4])
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.2)
            alice_seq = alice.client.last_seq

            bob2 = _Client("Bob")
            await bob2.connect(port, token=bob_token)
            await bob2.send(Message.reconnect(bob2.session_id))
            await _until(lambda: bob2.snapshot is not None)
            await asyncio.sleep(0.2)

        assert bob2.player_id == bob_player
        assert bob2.entity_id == bob_entity
        assert bob2.client.game_info["is_started"]
        assert bob2.snapshot == game.snapshot_for(bob_player)
        assert not game.players[bob_player].is_disconnected()
        assert alice.client.last_seq == alice_seq  # the catch-up went to Bob alone
        assert caplog.text == ""  # no server-side tracebacks for a normal disconnect
    finally:
        for client in (alice, bob, bob2):
            if client is not None:
                await client.close()
        await server.stop()


@pytest.mark.asyncio
async def test_each_client_sees_its_own_inventory_and_a_stale_snapshot_is_ignored():
    server = VeinbornServer("127.0.0.1", 0)
    await server.start()
    port = server.server.sockets[0].getsockname()[1]
    alice, bob = _Client("Alice"), _Client("Bob")
    try:
        await alice.connect(port)
        await bob.connect(port)
        await alice.send(Message.create_game("Views", max_players=4))
        await _until(lambda: alice.game_id)
        await bob.send(Message.join_game(alice.game_id, player_class="mage"))
        await alice.send(Message(type="ready", data={"ready": True}))
        await bob.send(Message(type="ready", data={"ready": True}))
        await _until(lambda: alice.game_started and bob.game_started)

        # Same world, different viewers: the viewer is never listed among the entities
        assert alice.snapshot.player.entity_id not in {e.entity_id for e in alice.snapshot.entities}
        assert bob.entity_id in {e.entity_id for e in alice.snapshot.entities}
        assert {e.entity_id for e in alice.snapshot.entities if e.entity_type == "monster"} == \
               {e.entity_id for e in bob.snapshot.entities if e.entity_type == "monster"}

        # A snapshot older than what the client holds is dropped
        newest, seq = alice.snapshot, alice.client.last_seq
        stale = Message.snapshot(seq - 1, {"game_id": "x"}, bob.snapshot.to_dict())
        await alice.client._handle_message(stale)
        assert alice.snapshot is newest and alice.client.last_seq == seq

        # ...and the client can ask for a fresh one
        assert await alice.client.request_snapshot()
        await _until(lambda: alice.client.last_seq > seq)
    finally:
        for client in (alice, bob):
            await client.close()
        await server.stop()


async def _start_duo(server, port, alice, bob, name):
    await alice.connect(port)
    await bob.connect(port)
    await alice.send(Message.create_game(name, max_players=4))
    await _until(lambda: alice.game_id)
    await bob.send(Message.join_game(alice.game_id, player_class="mage"))
    await alice.send(Message(type="ready", data={"ready": True}))
    await bob.send(Message(type="ready", data={"ready": True}))
    await _until(lambda: alice.entity_id and bob.entity_id)
    return await server.game_manager.get_game(alice.game_id)


@pytest.mark.asyncio
async def test_expired_seat_rejoins_the_running_game_with_its_token():
    """VB-103: the grace ran out (seat dropped); the same session joins the running game again."""
    server = VeinbornServer("127.0.0.1", 0)
    await server.start()
    port = server.server.sockets[0].getsockname()[1]
    alice, bob = _Client("Alice"), _Client("Bob")
    bob2 = None
    try:
        game = await _start_duo(server, port, alice, bob, "Rejoin")
        bob_entity, bob_token, bob_player = bob.entity_id, bob.token, bob.player_id
        await bob.ws.close()
        await _until(lambda: game.players[bob_player].is_disconnected())
        game.players[bob_player].reconnect_timeout_seconds = -1
        await server._cleanup_once()
        assert game.rejoinable_names() == ["Bob"]
        assert [g["rejoinable"] for g in server.game_manager.get_available_games()] == [["Bob"]]

        bob2 = _Client("Bob")
        await bob2.connect(port, token=bob_token)
        await bob2.send(Message.join_game(game.game_id))
        await _until(lambda: bob2.snapshot is not None)
        await _until(lambda: [m.connected for m in alice.snapshot.party] == [True, True])

        assert bob2.player_id == bob_player and bob2.entity_id == bob_entity
        assert not bob2.errors and game.rejoinable_names() == []
        assert bob2.snapshot == game.snapshot_for(bob_player)
    finally:
        for client in (alice, bob, bob2):
            if client is not None:
                await client.close()
        await server.stop()


@pytest.mark.asyncio
async def test_a_seat_that_left_rejoins_by_name_from_a_fresh_session():
    """VB-103: Bob chose to leave and later came back in a new process (no token)."""
    server = VeinbornServer("127.0.0.1", 0)
    await server.start()
    port = server.server.sockets[0].getsockname()[1]
    alice, bob = _Client("Alice"), _Client("Bob")
    bob2 = None
    try:
        game = await _start_duo(server, port, alice, bob, "Name")
        bob_entity = bob.entity_id
        await bob.send(Message(type="leave_game", data={}))
        await _until(lambda: game.rejoinable_names() == ["Bob"])

        bob2 = _Client("Bob")
        await bob2.connect(port)                           # no token: a new player id
        assert bob2.player_id != bob.player_id
        await bob2.send(Message.join_game(game.game_id))
        await _until(lambda: bob2.snapshot is not None)

        assert bob2.entity_id == bob_entity                # the same character
        assert not bob2.errors
        assert [p.player_id for p in game.mp_game_state.get_all_players()] == [alice.player_id, bob2.player_id]
        assert await server.game_manager.get_player_game(bob2.player_id) is game
        assert await server.game_manager.get_player_game(bob.player_id) is None
    finally:
        for client in (alice, bob, bob2):
            if client is not None:
                await client.close()
        await server.stop()
