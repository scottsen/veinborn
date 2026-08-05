"""Tests for MultiplayerClient state merging (VB-4).

Exercises _handle_message directly rather than opening a real websocket
connection - unit-level coverage for the delta-merge fix.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest

from ui.multiplayer_client import MultiplayerClient
from server.messages import Message
from server.state_delta import StateDelta


def _client():
    return MultiplayerClient(host="localhost", port=8765)


@pytest.mark.asyncio
async def test_full_state_message_replaces_cached_state():
    client = _client()
    state = {"current_floor": 1, "monsters": [], "players": []}

    await client._handle_message(Message.state(state))

    assert client._game_state == state


@pytest.mark.asyncio
async def test_delta_message_merges_onto_cached_state():
    client = _client()
    old_state = {
        "current_floor": 1,
        "players": [],
        "monsters": [{"entity_id": "m1", "x": 0, "y": 0, "hp": 10}],
    }
    new_state = {
        "current_floor": 2,
        "players": [],
        "monsters": [{"entity_id": "m2", "x": 1, "y": 1, "hp": 8}],
    }
    await client._handle_message(Message.state(old_state))

    delta = StateDelta.compute_delta(old_state, new_state)
    await client._handle_message(Message.delta(delta))

    assert client._game_state["current_floor"] == 2
    assert [m["entity_id"] for m in client._game_state["monsters"]] == ["m2"]


@pytest.mark.asyncio
async def test_delta_message_reaches_state_update_callback():
    client = _client()
    received = []
    client.on_state_update = lambda state: received.append(state)

    old_state = {"current_floor": 1, "players": [], "monsters": []}
    await client._handle_message(Message.state(old_state))

    new_state = {"current_floor": 2, "players": [], "monsters": []}
    delta = StateDelta.compute_delta(old_state, new_state)
    await client._handle_message(Message.delta(delta))

    assert received[-1]["current_floor"] == 2
