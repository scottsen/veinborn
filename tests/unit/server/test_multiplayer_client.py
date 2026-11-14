"""MultiplayerClient: decoding what the server sends (VB-97).

Exercises _handle_message directly rather than opening a real websocket
connection; the real-socket tests cover the whole path.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest

from core.game import Game
from core.snapshot import Snapshot
from protocol.messages import Message
from ui.multiplayer_client import MultiplayerClient


def _client():
    return MultiplayerClient(host="localhost", port=8765)


def _snapshot_message(seq, game_id="g1"):
    game = Game()
    game.start_new_game(seed=1, player_name="Solo")
    snap = game.engine.snapshot()
    return Message.snapshot(seq, {"game_id": game_id, "is_started": True}, snap.to_dict()), snap


@pytest.mark.asyncio
async def test_snapshot_message_is_decoded_and_stored():
    client = _client()
    message, snap = _snapshot_message(3)
    seen = []
    client.on_snapshot = seen.append

    await client._handle_message(message)

    assert isinstance(client.snapshot, Snapshot) and client.snapshot == snap
    assert client.last_seq == 3 and seen == [snap]
    assert client.state.game_id == "g1" and client.game_info["is_started"]


@pytest.mark.asyncio
async def test_a_snapshot_with_an_older_or_equal_seq_is_ignored():
    client = _client()
    newer, _ = _snapshot_message(5)
    await client._handle_message(newer)
    held = client.snapshot
    seen = []
    client.on_snapshot = seen.append

    for seq in (5, 4):
        older, _ = _snapshot_message(seq, game_id="other")
        await client._handle_message(older)

    assert client.snapshot is held and client.last_seq == 5 and seen == []
    assert client.state.game_id == "g1"


@pytest.mark.asyncio
async def test_lobby_message_is_stored_and_sets_the_game_id():
    client = _client()
    seen = []
    client.on_lobby = seen.append
    lobby = {"game_id": "g9", "game_name": "N", "is_started": False,
             "players": [{"player_id": "p", "player_name": "A", "player_class": "warrior", "is_ready": False}]}

    await client._handle_message(Message.lobby(lobby))

    assert client.lobby == lobby and seen == [lobby]
    assert client.state.game_id == "g9" and client.snapshot is None


@pytest.mark.asyncio
async def test_error_message_is_recorded():
    client = _client()
    await client._handle_message(Message.error("Waiting for the party: Bob"))
    assert client.state.errors == ["Waiting for the party: Bob"]


@pytest.mark.asyncio
async def test_request_snapshot_when_disconnected_returns_false():
    assert await _client().request_snapshot() is False


@pytest.mark.asyncio
async def test_connect_refuses_a_server_speaking_another_protocol_version(monkeypatch):
    class _FakeWs:
        async def send(self, raw):
            pass

        async def recv(self):
            reply = Message.auth_success("s", "p", "tok")
            reply.v = 0
            return reply.to_json()

    async def _connect(uri):
        return _FakeWs()

    monkeypatch.setattr("ui.multiplayer_client.websockets.connect", _connect)
    client = MultiplayerClient()

    assert await client.connect("Alice") is False
    assert not client.state.is_connected
