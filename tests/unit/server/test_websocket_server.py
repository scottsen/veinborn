"""
Unit tests for WebSocket Server.

Tests the WebSocket server functionality:
- Server startup and shutdown
- Connection handling
- Authentication flow
- Message routing
- Error handling
- Connection tracking
- Broadcasting
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from server.websocket_server import BrogueServer
from server.messages import Message, MessageType
from server.auth import AuthManager, Session
from server.game_session import GameSessionManager, GameSession


pytestmark = pytest.mark.unit


# ============================================================================
# Server Initialization Tests
# ============================================================================

def test_server_initialization_default():
    """Test server initializes with default settings."""
    server = BrogueServer()

    assert server.host is not None
    assert server.port is not None
    assert isinstance(server.auth_manager, AuthManager)
    assert isinstance(server.game_manager, GameSessionManager)
    assert server.connections == {}
    assert server.session_to_player == {}
    assert not server.is_running


def test_server_initialization_custom():
    """Test server initializes with custom host and port."""
    server = BrogueServer(host="0.0.0.0", port=9999)

    assert server.host == "0.0.0.0"
    assert server.port == 9999


# ============================================================================
# Authentication Tests
# ============================================================================

@pytest.mark.asyncio
async def test_authenticate_connection_success():
    """Test successful connection authentication."""
    server = BrogueServer()
    ws = AsyncMock()

    # Mock receiving auth message
    auth_msg = Message.auth("TestPlayer")
    ws.recv = AsyncMock(return_value=auth_msg.to_json())

    session_id = await server.authenticate_connection(ws)

    assert session_id is not None
    assert server.auth_manager.get_session(session_id) is not None


@pytest.mark.asyncio
async def test_authenticate_connection_timeout():
    """Test authentication timeout."""
    server = BrogueServer()
    ws = AsyncMock()

    # Mock timeout
    async def timeout_recv():
        await asyncio.sleep(10)
        return ""

    ws.recv = timeout_recv

    session_id = await server.authenticate_connection(ws)

    assert session_id is None


@pytest.mark.asyncio
async def test_authenticate_connection_wrong_message_type():
    """Test authentication fails with wrong message type."""
    server = BrogueServer()
    ws = AsyncMock()

    # Send non-auth message
    wrong_msg = Message(type=MessageType.CHAT.value, data={"message": "Hello"})
    ws.recv = AsyncMock(return_value=wrong_msg.to_json())

    session_id = await server.authenticate_connection(ws)

    assert session_id is None


@pytest.mark.asyncio
async def test_authenticate_connection_invalid_player_name():
    """Test authentication fails with invalid player name."""
    server = BrogueServer()
    ws = AsyncMock()

    # Send auth with empty player name
    invalid_msg = Message(type=MessageType.AUTH.value, data={"player_name": ""})
    ws.recv = AsyncMock(return_value=invalid_msg.to_json())

    session_id = await server.authenticate_connection(ws)

    assert session_id is None


@pytest.mark.asyncio
async def test_authenticate_connection_missing_player_name():
    """Test authentication fails with missing player name."""
    server = BrogueServer()
    ws = AsyncMock()

    # Send auth without player_name field
    invalid_msg = Message(type=MessageType.AUTH.value, data={})
    ws.recv = AsyncMock(return_value=invalid_msg.to_json())

    session_id = await server.authenticate_connection(ws)

    assert session_id is None


@pytest.mark.asyncio
async def test_authenticate_connection_invalid_json():
    """Test authentication fails with invalid JSON."""
    server = BrogueServer()
    ws = AsyncMock()

    # Send invalid JSON
    ws.recv = AsyncMock(return_value="not valid json {{{")

    session_id = await server.authenticate_connection(ws)

    assert session_id is None


@pytest.mark.asyncio
async def test_authenticate_connection_sends_success_response():
    """Test authentication sends success response."""
    server = BrogueServer()
    ws = AsyncMock()

    auth_msg = Message.auth("TestPlayer")
    ws.recv = AsyncMock(return_value=auth_msg.to_json())

    sent_messages = []

    async def mock_send(message):
        sent_messages.append(message)

    ws.send = mock_send

    session_id = await server.authenticate_connection(ws)

    # Verify success message was sent
    assert len(sent_messages) > 0

    # Parse the sent message
    sent_data = json.loads(sent_messages[0])
    assert sent_data["type"] == MessageType.AUTH_SUCCESS.value
    assert "session_id" in sent_data["data"]
    assert "player_id" in sent_data["data"]


# ============================================================================
# Message Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_handle_message_updates_activity():
    """Test handle_message updates session activity."""
    server = BrogueServer()

    # Create session
    token, session = server.auth_manager.create_session("TestPlayer")
    original_timestamp = session.last_activity

    # Wait a bit
    await asyncio.sleep(0.01)

    # Handle a message
    msg = Message(type=MessageType.CHAT.value, data={"message": "test"})
    session.game_id = "game1"

    # Mock handlers
    async def mock_handler(*args):
        pass

    server.handle_chat = mock_handler

    await server.handle_message(session.session_id, msg)

    # Verify activity was updated
    updated_session = server.auth_manager.get_session(session.session_id)
    assert updated_session.last_activity > original_timestamp


@pytest.mark.asyncio
async def test_handle_message_invalid_session():
    """Test handle_message with invalid session."""
    server = BrogueServer()

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    msg = Message(type=MessageType.CHAT.value, data={"message": "test"})
    await server.handle_message("invalid-session", msg)

    assert len(errors) == 1
    assert "invalid session" in errors[0].lower()


@pytest.mark.asyncio
async def test_handle_message_routes_create_game():
    """Test message routing for create game."""
    server = BrogueServer()
    token, session = server.auth_manager.create_session("TestPlayer")

    called = []

    async def mock_handle_create_game(session_id, session_obj, msg):
        called.append("create_game")

    server.handle_create_game = mock_handle_create_game

    msg = Message(type=MessageType.CREATE_GAME.value, data={"game_name": "Test"})
    await server.handle_message(session.session_id, msg)

    assert "create_game" in called


@pytest.mark.asyncio
async def test_handle_message_routes_join_game():
    """Test message routing for join game."""
    server = BrogueServer()
    token, session = server.auth_manager.create_session("TestPlayer")

    called = []

    async def mock_handle_join_game(session_id, session_obj, msg):
        called.append("join_game")

    server.handle_join_game = mock_handle_join_game

    msg = Message(type=MessageType.JOIN_GAME.value, data={"game_id": "game1"})
    await server.handle_message(session.session_id, msg)

    assert "join_game" in called


@pytest.mark.asyncio
async def test_handle_message_routes_action():
    """Test message routing for action."""
    server = BrogueServer()
    token, session = server.auth_manager.create_session("TestPlayer")

    called = []

    async def mock_handle_action(session_id, session_obj, msg):
        called.append("action")

    server.handle_action = mock_handle_action

    msg = Message(type=MessageType.ACTION.value, data={"action_data": {}})
    await server.handle_message(session.session_id, msg)

    assert "action" in called


@pytest.mark.asyncio
async def test_handle_message_unknown_type():
    """Test handling unknown message type."""
    server = BrogueServer()
    token, session = server.auth_manager.create_session("TestPlayer")

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    msg = Message(type="UNKNOWN_TYPE", data={})
    await server.handle_message(session.session_id, msg)

    assert len(errors) == 1
    assert "unknown" in errors[0].lower()


# ============================================================================
# Message Sending Tests
# ============================================================================

@pytest.mark.asyncio
async def test_send_message_to_websocket():
    """Test sending message to WebSocket."""
    server = BrogueServer()
    ws = AsyncMock()

    msg = Message.system("Test message")
    await server.send_message(ws, msg)

    ws.send.assert_called_once()
    sent_data = ws.send.call_args[0][0]
    assert "Test message" in sent_data


@pytest.mark.asyncio
async def test_send_message_to_session():
    """Test sending message to specific session."""
    server = BrogueServer()

    # Create session and connection
    token, session = server.auth_manager.create_session("TestPlayer")
    ws = AsyncMock()
    server.connections[session.session_id] = ws

    msg = Message.system("Test")
    await server.send_message_to_session(session.session_id, msg)

    ws.send.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_to_session_no_connection():
    """Test sending message to session without connection."""
    server = BrogueServer()

    msg = Message.system("Test")

    # Should not raise error
    await server.send_message_to_session("nonexistent-session", msg)


@pytest.mark.asyncio
async def test_send_error_message():
    """Test sending error message."""
    server = BrogueServer()

    token, session = server.auth_manager.create_session("TestPlayer")
    ws = AsyncMock()
    server.connections[session.session_id] = ws

    await server.send_error(session.session_id, "Test error")

    ws.send.assert_called_once()
    sent_data = ws.send.call_args[0][0]
    parsed = json.loads(sent_data)

    assert parsed["type"] == MessageType.ERROR.value
    assert "Test error" in parsed["data"]["message"]


# ============================================================================
# Broadcasting Tests
# ============================================================================

@pytest.mark.asyncio
async def test_broadcast_to_game():
    """Test broadcasting message to all players in a game."""
    server = BrogueServer()

    # Create sessions
    token1, session1 = server.auth_manager.create_session("Player1")
    token2, session2 = server.auth_manager.create_session("Player2")
    token3, session3 = server.auth_manager.create_session("Player3")

    # Create game
    game = GameSession("game1", "Test Game")
    await game.add_player(session1.player_id, "Player1")
    await game.add_player(session2.player_id, "Player2")
    server.game_manager._games["game1"] = game

    # Add connections
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    ws3 = AsyncMock()
    server.connections[session1.session_id] = ws1
    server.connections[session2.session_id] = ws2
    server.connections[session3.session_id] = ws3

    # Broadcast message
    msg = Message.system("Broadcast test")
    await server.broadcast_to_game("game1", msg)

    # Verify only game players received message
    ws1.send.assert_called_once()
    ws2.send.assert_called_once()
    ws3.send.assert_not_called()  # Not in game


@pytest.mark.asyncio
async def test_broadcast_to_nonexistent_game():
    """Test broadcasting to nonexistent game."""
    server = BrogueServer()

    msg = Message.system("Test")

    # Should not raise error
    await server.broadcast_to_game("nonexistent-game", msg)


@pytest.mark.asyncio
async def test_broadcast_game_state_full():
    """Test broadcasting full game state."""
    server = BrogueServer()

    # Create game and session
    token, session = server.auth_manager.create_session("Player1")
    game = GameSession("game1", "Test Game")
    await game.add_player(session.player_id, "Player1")
    server.game_manager._games["game1"] = game

    ws = AsyncMock()
    server.connections[session.session_id] = ws

    # Broadcast full state
    await server.broadcast_game_state("game1", force_full_state=True)

    # Verify state message was sent
    ws.send.assert_called_once()
    sent_data = ws.send.call_args[0][0]
    parsed = json.loads(sent_data)

    assert parsed["type"] in [MessageType.STATE.value, MessageType.DELTA.value]


@pytest.mark.asyncio
async def test_broadcast_game_state_delta():
    """Test broadcasting delta game state."""
    server = BrogueServer()

    # Create game
    token, session = server.auth_manager.create_session("Player1")
    game = GameSession("game1", "Test Game")
    await game.add_player(session.player_id, "Player1")
    server.game_manager._games["game1"] = game

    # Enable delta compression
    game.use_delta_compression = True
    game.last_state = {"test": "data"}

    ws = AsyncMock()
    server.connections[session.session_id] = ws

    # Broadcast delta
    await server.broadcast_game_state("game1", force_full_state=False)

    ws.send.assert_called_once()


# ============================================================================
# Connection Management Tests
# ============================================================================

@pytest.mark.asyncio
async def test_disconnect_client_closes_websocket():
    """Test disconnect closes WebSocket connection."""
    server = BrogueServer()

    token, session = server.auth_manager.create_session("TestPlayer")
    ws = AsyncMock()
    ws.closed = False
    server.connections[session.session_id] = ws
    server.session_to_player[session.session_id] = session.player_id

    await server.disconnect_client(session.session_id, "Test disconnect", preserve_session=False)

    ws.close.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect_client_removes_from_tracking():
    """Test disconnect removes client from connection tracking."""
    server = BrogueServer()

    token, session = server.auth_manager.create_session("TestPlayer")
    ws = AsyncMock()
    ws.closed = False
    server.connections[session.session_id] = ws
    server.session_to_player[session.session_id] = session.player_id

    await server.disconnect_client(session.session_id, "Test", preserve_session=False)

    assert session.session_id not in server.connections
    assert session.session_id not in server.session_to_player


@pytest.mark.asyncio
async def test_disconnect_nonexistent_client():
    """Test disconnecting nonexistent client."""
    server = BrogueServer()

    # Should not raise error
    await server.disconnect_client("nonexistent", "Test", preserve_session=False)


# ============================================================================
# Game Lifecycle Tests
# ============================================================================

@pytest.mark.asyncio
async def test_handle_create_game():
    """Test creating a game."""
    server = BrogueServer()

    token, session = server.auth_manager.create_session("Player1")

    sent_messages = []

    async def mock_send(session_id, msg):
        sent_messages.append(msg)

    async def mock_broadcast_state(game_id):
        pass

    server.send_message_to_session = mock_send
    server.broadcast_game_state = mock_broadcast_state

    msg = Message.create_game("My Game", max_players=4, player_class="warrior")
    await server.handle_create_game(session.session_id, session, msg)

    # Verify game was created
    assert server.game_manager.get_active_game_count() == 1

    # Verify session has game_id
    assert session.game_id is not None

    # Verify success message sent
    success_msgs = [m for m in sent_messages if m.type == MessageType.SYSTEM.value]
    assert len(success_msgs) >= 1


@pytest.mark.asyncio
async def test_handle_join_game():
    """Test joining an existing game."""
    server = BrogueServer()

    # Create game
    game = await server.game_manager.create_game("Test Game", max_players=4)

    # Create player
    token, session = server.auth_manager.create_session("Player2")

    sent_messages = []

    async def mock_send(session_id, msg):
        sent_messages.append(msg)

    async def mock_broadcast(game_id, msg):
        sent_messages.append(msg)

    async def mock_broadcast_state(game_id):
        pass

    server.send_message_to_session = mock_send
    server.broadcast_to_game = mock_broadcast
    server.broadcast_game_state = mock_broadcast_state

    msg = Message.join_game(game.game_id, player_class="mage")
    await server.handle_join_game(session.session_id, session, msg)

    # Verify player joined
    assert session.game_id == game.game_id
    assert game.get_player_count() == 1


@pytest.mark.asyncio
async def test_handle_join_game_missing_game_id():
    """Test joining game without providing game_id."""
    server = BrogueServer()

    token, session = server.auth_manager.create_session("Player1")

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    msg = Message(type=MessageType.JOIN_GAME.value, data={})  # No game_id
    await server.handle_join_game(session.session_id, session, msg)

    assert len(errors) == 1
    assert "missing game_id" in errors[0].lower()


@pytest.mark.asyncio
async def test_handle_join_nonexistent_game():
    """Test joining a game that doesn't exist."""
    server = BrogueServer()

    token, session = server.auth_manager.create_session("Player1")

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    msg = Message.join_game("nonexistent-game")
    await server.handle_join_game(session.session_id, session, msg)

    assert len(errors) == 1


@pytest.mark.asyncio
async def test_handle_leave_game():
    """Test leaving a game."""
    server = BrogueServer()

    # Create game and add player
    token, session = server.auth_manager.create_session("Player1")
    game = await server.game_manager.create_game("Test Game")
    await server.game_manager.join_game(game.game_id, session.player_id, "Player1")
    session.game_id = game.game_id

    sent_messages = []

    async def mock_send(session_id, msg):
        sent_messages.append(msg)

    async def mock_broadcast(game_id, msg):
        sent_messages.append(msg)

    async def mock_broadcast_state(game_id):
        pass

    server.send_message_to_session = mock_send
    server.broadcast_to_game = mock_broadcast
    server.broadcast_game_state = mock_broadcast_state

    msg = Message(type=MessageType.LEAVE_GAME.value, data={})
    await server.handle_leave_game(session.session_id, session, msg)

    # Verify player left
    assert session.game_id is None


@pytest.mark.asyncio
async def test_handle_leave_game_not_in_game():
    """Test leaving when not in a game."""
    server = BrogueServer()

    token, session = server.auth_manager.create_session("Player1")
    session.game_id = None

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    msg = Message(type=MessageType.LEAVE_GAME.value, data={})
    await server.handle_leave_game(session.session_id, session, msg)

    assert len(errors) == 1
    assert "not in a game" in errors[0].lower()


# ============================================================================
# Ready Status Tests
# ============================================================================

@pytest.mark.asyncio
async def test_handle_ready():
    """Test setting player ready status."""
    server = BrogueServer()

    # Create game with player
    token, session = server.auth_manager.create_session("Player1")
    game = await server.game_manager.create_game("Test Game")
    await server.game_manager.join_game(game.game_id, session.player_id, "Player1")
    session.game_id = game.game_id

    async def mock_broadcast_state(game_id):
        pass

    server.broadcast_game_state = mock_broadcast_state

    msg = Message(type=MessageType.READY.value, data={"ready": True})
    await server.handle_ready(session.session_id, session, msg)

    # Verify player is ready
    player_info = game.players[session.player_id]
    assert player_info.is_ready


@pytest.mark.asyncio
async def test_handle_ready_not_in_game():
    """Test ready status when not in game."""
    server = BrogueServer()

    token, session = server.auth_manager.create_session("Player1")
    session.game_id = None

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    msg = Message(type=MessageType.READY.value, data={"ready": True})
    await server.handle_ready(session.session_id, session, msg)

    assert len(errors) == 1


# ============================================================================
# Server Lifecycle Tests
# ============================================================================

@pytest.mark.asyncio
async def test_server_start_requires_websockets():
    """Test server start fails without websockets library."""
    with patch('server.websocket_server.websockets', None):
        server = BrogueServer()

        with pytest.raises(RuntimeError, match="websockets library not installed"):
            await server.start()


@pytest.mark.asyncio
async def test_server_stop_closes_connections():
    """Test server stop closes all connections."""
    server = BrogueServer()
    server.is_running = True

    # Add mock connections
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    ws1.closed = False
    ws2.closed = False

    server.connections["session1"] = ws1
    server.connections["session2"] = ws2

    # Mock disconnect
    async def mock_disconnect(session_id, reason, preserve_session=True):
        pass

    server.disconnect_client = mock_disconnect

    # Need to mock the server object
    mock_server = AsyncMock()
    server.server = mock_server

    await server.stop()

    assert not server.is_running
    mock_server.close.assert_called_once()
