"""
Unit tests for Message Protocol.

Tests the message serialization and protocol:
- Message creation
- Serialization/deserialization
- All message types
- Message validation
"""
import pytest
import json
from server.messages import Message, MessageType


pytestmark = pytest.mark.unit


# ============================================================================
# Message Type Tests
# ============================================================================

def test_message_types_defined():
    """Test all message types are defined."""
    # Client to server
    assert MessageType.AUTH.value == "auth"
    assert MessageType.RECONNECT.value == "reconnect"
    assert MessageType.ACTION.value == "action"
    assert MessageType.CHAT.value == "chat"
    assert MessageType.JOIN_GAME.value == "join_game"
    assert MessageType.CREATE_GAME.value == "create_game"
    assert MessageType.LEAVE_GAME.value == "leave_game"
    assert MessageType.READY.value == "ready"

    # Server to client
    assert MessageType.AUTH_SUCCESS.value == "auth_success"
    assert MessageType.AUTH_FAILURE.value == "auth_failure"
    assert MessageType.STATE.value == "state"
    assert MessageType.DELTA.value == "delta"
    assert MessageType.CHAT_MESSAGE.value == "chat_message"
    assert MessageType.SYSTEM.value == "system"
    assert MessageType.ERROR.value == "error"
    assert MessageType.GAME_START.value == "game_start"
    assert MessageType.PLAYER_JOINED.value == "player_joined"
    assert MessageType.PLAYER_LEFT.value == "player_left"
    assert MessageType.PLAYER_DISCONNECTED.value == "player_disconnected"
    assert MessageType.PLAYER_RECONNECTED.value == "player_reconnected"


# ============================================================================
# Message Serialization Tests
# ============================================================================

def test_message_to_json():
    """Test message serialization to JSON."""
    msg = Message(
        type="test",
        data={"key": "value"},
        timestamp=None
    )

    json_str = msg.to_json()

    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["type"] == "test"
    assert parsed["data"] == {"key": "value"}


def test_message_from_json():
    """Test message deserialization from JSON."""
    json_str = json.dumps({
        "type": "test",
        "data": {"key": "value"},
        "timestamp": None
    })

    msg = Message.from_json(json_str)

    assert msg.type == "test"
    assert msg.data == {"key": "value"}
    assert msg.timestamp is None


def test_message_roundtrip():
    """Test message survives serialization roundtrip."""
    original = Message(
        type="test_type",
        data={"nested": {"data": [1, 2, 3]}, "string": "test"},
        timestamp=1234567890.0
    )

    json_str = original.to_json()
    restored = Message.from_json(json_str)

    assert restored.type == original.type
    assert restored.data == original.data
    assert restored.timestamp == original.timestamp


# ============================================================================
# Auth Messages Tests
# ============================================================================

def test_auth_message():
    """Test authentication request message."""
    msg = Message.auth("TestPlayer")

    assert msg.type == MessageType.AUTH.value
    assert msg.data["player_name"] == "TestPlayer"


def test_auth_success_message():
    """Test authentication success message."""
    msg = Message.auth_success("session123", "player456")

    assert msg.type == MessageType.AUTH_SUCCESS.value
    assert msg.data["session_id"] == "session123"
    assert msg.data["player_id"] == "player456"


def test_auth_failure_message():
    """Test authentication failure message."""
    msg = Message.auth_failure("Invalid credentials")

    assert msg.type == MessageType.AUTH_FAILURE.value
    assert msg.data["reason"] == "Invalid credentials"


# ============================================================================
# Game Messages Tests
# ============================================================================

def test_create_game_message():
    """Test create game message."""
    msg = Message.create_game("My Game", max_players=4, player_class="warrior")

    assert msg.type == MessageType.CREATE_GAME.value
    assert msg.data["game_name"] == "My Game"
    assert msg.data["max_players"] == 4
    assert msg.data["player_class"] == "warrior"


def test_join_game_message():
    """Test join game message."""
    msg = Message.join_game("game123", player_class="mage")

    assert msg.type == MessageType.JOIN_GAME.value
    assert msg.data["game_id"] == "game123"
    assert msg.data["player_class"] == "mage"


def test_player_joined_message():
    """Test player joined notification."""
    msg = Message.player_joined("player1", "Alice", "warrior")

    assert msg.type == MessageType.PLAYER_JOINED.value
    assert msg.data["player_id"] == "player1"
    assert msg.data["player_name"] == "Alice"
    assert msg.data["player_class"] == "warrior"


def test_player_left_message():
    """Test player left notification."""
    msg = Message.player_left("player1", "Alice")

    assert msg.type == MessageType.PLAYER_LEFT.value
    assert msg.data["player_id"] == "player1"
    assert msg.data["player_name"] == "Alice"


def test_game_start_message():
    """Test game start notification."""
    players = [
        {"player_id": "p1", "player_name": "Alice"},
        {"player_id": "p2", "player_name": "Bob"}
    ]

    msg = Message.game_start("game123", players)

    assert msg.type == MessageType.GAME_START.value
    assert msg.data["game_id"] == "game123"
    assert msg.data["players"] == players


# ============================================================================
# State Messages Tests
# ============================================================================

def test_state_message():
    """Test full state message."""
    game_state = {
        "turn": 1,
        "entities": [{"id": "e1", "type": "player"}]
    }

    msg = Message.state(game_state)

    assert msg.type == MessageType.STATE.value
    assert msg.data["state"] == game_state


def test_delta_message():
    """Test delta state message."""
    changes = {
        "type": "delta",
        "updated": {"entity1": {"hp": 10}},
        "removed": ["entity2"]
    }

    msg = Message.delta(changes)

    assert msg.type == MessageType.DELTA.value
    assert msg.data["changes"] == changes


# ============================================================================
# Chat Messages Tests
# ============================================================================

def test_chat_message():
    """Test chat message."""
    msg = Message.chat_message("player1", "Alice", "Hello, world!")

    assert msg.type == MessageType.CHAT_MESSAGE.value
    assert msg.data["player_id"] == "player1"
    assert msg.data["player_name"] == "Alice"
    assert msg.data["message"] == "Hello, world!"


# ============================================================================
# System Messages Tests
# ============================================================================

def test_system_message():
    """Test system message."""
    msg = Message.system("Server maintenance in 5 minutes", "warning")

    assert msg.type == MessageType.SYSTEM.value
    assert msg.data["message"] == "Server maintenance in 5 minutes"
    assert msg.data["level"] == "warning"


def test_system_message_default_level():
    """Test system message with default level."""
    msg = Message.system("Test message")

    assert msg.data["level"] == "info"


def test_error_message():
    """Test error message."""
    msg = Message.error("Something went wrong", code="ERR_123")

    assert msg.type == MessageType.ERROR.value
    assert msg.data["message"] == "Something went wrong"
    assert msg.data["code"] == "ERR_123"


def test_error_message_no_code():
    """Test error message without code."""
    msg = Message.error("Error occurred")

    assert msg.data["message"] == "Error occurred"
    assert msg.data["code"] is None


# ============================================================================
# Reconnection Messages Tests
# ============================================================================

def test_reconnect_message():
    """Test reconnection request."""
    msg = Message.reconnect("session123")

    assert msg.type == MessageType.RECONNECT.value
    assert msg.data["session_id"] == "session123"


def test_player_disconnected_message():
    """Test player disconnected notification."""
    msg = Message.player_disconnected("player1", "Alice")

    assert msg.type == MessageType.PLAYER_DISCONNECTED.value
    assert msg.data["player_id"] == "player1"
    assert msg.data["player_name"] == "Alice"


def test_player_reconnected_message():
    """Test player reconnected notification."""
    msg = Message.player_reconnected("player1", "Alice")

    assert msg.type == MessageType.PLAYER_RECONNECTED.value
    assert msg.data["player_id"] == "player1"
    assert msg.data["player_name"] == "Alice"


# ============================================================================
# Action Messages Tests
# ============================================================================

def test_action_message():
    """Test action message."""
    action_data = {
        "action_type": "MoveAction",
        "actor_id": "player1",
        "dx": 1,
        "dy": 0
    }

    msg = Message.action("MoveAction", action_data)

    assert msg.type == MessageType.ACTION.value
    assert msg.data["action_type"] == "MoveAction"
    assert msg.data["action_data"] == action_data


# ============================================================================
# Edge Cases and Validation Tests
# ============================================================================

def test_message_with_empty_data():
    """Test message with empty data dictionary."""
    msg = Message(type="test", data={})

    json_str = msg.to_json()
    restored = Message.from_json(json_str)

    assert restored.data == {}


def test_message_with_complex_nested_data():
    """Test message with complex nested data."""
    complex_data = {
        "level1": {
            "level2": {
                "level3": {
                    "values": [1, 2, 3],
                    "nested_dict": {"key": "value"}
                }
            },
            "array": [{"item": 1}, {"item": 2}]
        }
    }

    msg = Message(type="test", data=complex_data)

    json_str = msg.to_json()
    restored = Message.from_json(json_str)

    assert restored.data == complex_data


def test_message_with_unicode():
    """Test message with unicode characters."""
    unicode_data = {
        "message": "Hello 你好 🎮 Привет",
        "name": "José María"
    }

    msg = Message(type="test", data=unicode_data)

    json_str = msg.to_json()
    restored = Message.from_json(json_str)

    assert restored.data == unicode_data


def test_message_timestamp_optional():
    """Test message timestamp is optional."""
    msg = Message(type="test", data={})

    assert msg.timestamp is None

    json_str = msg.to_json()
    assert "timestamp" in json_str


def test_message_with_timestamp():
    """Test message with timestamp."""
    import time
    timestamp = time.time()

    msg = Message(type="test", data={}, timestamp=timestamp)

    assert msg.timestamp == timestamp

    json_str = msg.to_json()
    restored = Message.from_json(json_str)

    assert restored.timestamp == timestamp


def test_create_game_default_player_class():
    """Test create game with default player class."""
    msg = Message.create_game("Test Game", max_players=4)

    # Should have a default player_class
    assert "player_class" in msg.data


def test_join_game_default_player_class():
    """Test join game with default player class."""
    msg = Message.join_game("game123")

    # Should have a default player_class
    assert "player_class" in msg.data
    assert msg.data["player_class"] == "warrior"


# ============================================================================
# Message Type String Values Tests
# ============================================================================

def test_all_message_types_are_strings():
    """Test all MessageType enum values are strings."""
    for msg_type in MessageType:
        assert isinstance(msg_type.value, str)


def test_message_type_values_are_lowercase():
    """Test all MessageType values are lowercase with underscores."""
    for msg_type in MessageType:
        value = msg_type.value
        # Should be lowercase and only contain letters, numbers, and underscores
        assert value == value.lower()
        assert all(c.isalnum() or c == '_' for c in value)


# ============================================================================
# Serialization Edge Cases
# ============================================================================

def test_deserialize_invalid_json():
    """Test deserializing invalid JSON raises error."""
    with pytest.raises(json.JSONDecodeError):
        Message.from_json("not valid json {{{")


def test_deserialize_missing_required_fields():
    """Test deserializing with missing fields raises error."""
    # Missing 'type' field
    with pytest.raises((KeyError, TypeError)):
        Message.from_json('{"data": {}}')

    # Missing 'data' field
    with pytest.raises((KeyError, TypeError)):
        Message.from_json('{"type": "test"}')


def test_serialize_message_with_none_values():
    """Test serializing message with None values in data."""
    msg = Message(
        type="test",
        data={"key": None, "other": "value"}
    )

    json_str = msg.to_json()
    restored = Message.from_json(json_str)

    assert restored.data["key"] is None
    assert restored.data["other"] == "value"
