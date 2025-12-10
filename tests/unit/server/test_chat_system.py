"""
Unit tests for Multiplayer Chat System.

Tests the chat functionality added in Phase 3:
- Chat message handling
- Message broadcasting to all players in game
- Chat message validation
- Player authentication for chat
- Message serialization/deserialization
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from server.messages import Message, MessageType
from server.websocket_server import VeinbornServer
from server.auth import AuthManager, Session


pytestmark = pytest.mark.unit


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def auth_manager():
    """Create an auth manager with test sessions."""
    manager = AuthManager()
    # Create test sessions
    token1, session1 = manager.create_session("Player1")
    token2, session2 = manager.create_session("Player2")

    # Set up game IDs
    session1.game_id = "test-game-1"
    session2.game_id = "test-game-1"

    return manager


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.remote_address = ("127.0.0.1", 12345)
    ws.closed = False
    return ws


@pytest.fixture
async def server_with_players(auth_manager):
    """Create a server with authenticated players."""
    server = VeinbornServer()
    server.auth_manager = auth_manager

    # Get sessions
    sessions = list(auth_manager._sessions.values())

    # Mock connections
    for session in sessions:
        ws = AsyncMock()
        ws.closed = False
        server.connections[session.session_id] = ws
        server.session_to_player[session.session_id] = session.player_id

    return server


# ============================================================================
# Message Creation Tests
# ============================================================================

def test_chat_message_creation():
    """Test creating a chat message."""
    msg = Message.chat_message("player1", "Alice", "Hello, world!")

    assert msg.type == MessageType.CHAT_MESSAGE.value
    assert msg.data["player_id"] == "player1"
    assert msg.data["player_name"] == "Alice"
    assert msg.data["message"] == "Hello, world!"


def test_chat_message_serialization():
    """Test chat message can be serialized to JSON."""
    msg = Message.chat_message("player1", "Alice", "Test message")
    json_str = msg.to_json()

    assert isinstance(json_str, str)
    assert "player1" in json_str
    assert "Alice" in json_str
    assert "Test message" in json_str


def test_chat_message_deserialization():
    """Test chat message can be deserialized from JSON."""
    original = Message.chat_message("player1", "Alice", "Test")
    json_str = original.to_json()

    restored = Message.from_json(json_str)

    assert restored.type == original.type
    assert restored.data == original.data


def test_empty_chat_message():
    """Test creating a chat message with empty text."""
    msg = Message.chat_message("player1", "Alice", "")

    assert msg.type == MessageType.CHAT_MESSAGE.value
    assert msg.data["message"] == ""


def test_long_chat_message():
    """Test creating a chat message with long text."""
    long_text = "A" * 1000
    msg = Message.chat_message("player1", "Alice", long_text)

    assert msg.type == MessageType.CHAT_MESSAGE.value
    assert msg.data["message"] == long_text
    assert len(msg.data["message"]) == 1000


def test_chat_message_with_special_characters():
    """Test chat message with special characters."""
    special_text = "Hello! 🎮 <script>alert('xss')</script> \n\t"
    msg = Message.chat_message("player1", "Alice", special_text)

    assert msg.data["message"] == special_text


# ============================================================================
# Chat Request Message Tests
# ============================================================================

def test_chat_request_message_type():
    """Test chat request message has correct type."""
    msg = Message(
        type=MessageType.CHAT.value,
        data={"message": "Hello"}
    )

    assert msg.type == MessageType.CHAT.value


def test_chat_request_deserialization():
    """Test deserializing a chat request from client."""
    import json

    json_str = json.dumps({
        "type": "chat",
        "data": {"message": "Hello everyone!"},
        "timestamp": None
    })

    msg = Message.from_json(json_str)

    assert msg.type == "chat"
    assert msg.data["message"] == "Hello everyone!"


# ============================================================================
# Server Chat Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_handle_chat_basic(server_with_players, auth_manager):
    """Test basic chat message handling."""
    server = server_with_players
    sessions = list(auth_manager._sessions.values())
    session = sessions[0]

    # Create chat message from client
    chat_msg = Message(
        type=MessageType.CHAT.value,
        data={"message": "Hello!"}
    )

    # Mock broadcast method to capture sent messages
    sent_messages = []

    async def mock_broadcast(game_id, message):
        sent_messages.append((game_id, message))

    server.broadcast_to_game = mock_broadcast

    # Handle the chat message
    await server.handle_chat(session.session_id, session, chat_msg)

    # Verify broadcast was called
    assert len(sent_messages) == 1
    game_id, broadcasted_msg = sent_messages[0]

    assert game_id == session.game_id
    assert broadcasted_msg.type == MessageType.CHAT_MESSAGE.value
    assert broadcasted_msg.data["player_id"] == session.player_id
    assert broadcasted_msg.data["player_name"] == session.player_name
    assert broadcasted_msg.data["message"] == "Hello!"


@pytest.mark.asyncio
async def test_handle_chat_not_in_game(server_with_players, auth_manager):
    """Test chat fails when player not in game."""
    server = server_with_players
    sessions = list(auth_manager._sessions.values())
    session = sessions[0]
    session.game_id = None  # Not in a game

    chat_msg = Message(
        type=MessageType.CHAT.value,
        data={"message": "Hello!"}
    )

    # Mock send_error to capture error
    error_sent = []

    async def mock_send_error(session_id, error_msg):
        error_sent.append(error_msg)

    server.send_error = mock_send_error

    # Handle the chat message
    await server.handle_chat(session.session_id, session, chat_msg)

    # Verify error was sent
    assert len(error_sent) == 1
    assert "Not in a game" in error_sent[0]


@pytest.mark.asyncio
async def test_handle_chat_empty_message(server_with_players, auth_manager):
    """Test empty chat message is ignored."""
    server = server_with_players
    sessions = list(auth_manager._sessions.values())
    session = sessions[0]

    chat_msg = Message(
        type=MessageType.CHAT.value,
        data={"message": ""}
    )

    sent_messages = []

    async def mock_broadcast(game_id, message):
        sent_messages.append((game_id, message))

    server.broadcast_to_game = mock_broadcast

    # Handle empty chat message
    await server.handle_chat(session.session_id, session, chat_msg)

    # Verify no broadcast occurred
    assert len(sent_messages) == 0


@pytest.mark.asyncio
async def test_handle_chat_missing_message_field(server_with_players, auth_manager):
    """Test chat with missing message field."""
    server = server_with_players
    sessions = list(auth_manager._sessions.values())
    session = sessions[0]

    chat_msg = Message(
        type=MessageType.CHAT.value,
        data={}  # No message field
    )

    sent_messages = []

    async def mock_broadcast(game_id, message):
        sent_messages.append((game_id, message))

    server.broadcast_to_game = mock_broadcast

    # Handle chat message without message field
    await server.handle_chat(session.session_id, session, chat_msg)

    # Verify no broadcast occurred
    assert len(sent_messages) == 0


# ============================================================================
# Broadcasting Tests
# ============================================================================

@pytest.mark.asyncio
async def test_broadcast_to_all_players_in_game(server_with_players, auth_manager):
    """Test chat message is broadcast to all players in the same game."""
    server = server_with_players

    # Create a mock game with players
    from server.game_session import GameSession
    game = GameSession("test-game-1", "Test Game", max_players=4)

    # Add players to game
    sessions = list(auth_manager._sessions.values())
    for session in sessions:
        await game.add_player(session.player_id, session.player_name)

    server.game_manager._games["test-game-1"] = game

    # Track messages sent to each session
    messages_by_session = {}

    async def mock_send_to_session(session_id, message):
        if session_id not in messages_by_session:
            messages_by_session[session_id] = []
        messages_by_session[session_id].append(message)

    server.send_message_to_session = mock_send_to_session

    # Broadcast a chat message
    chat_msg = Message.chat_message("player1", "Alice", "Hello everyone!")
    await server.broadcast_to_game("test-game-1", chat_msg)

    # Verify all players received the message
    assert len(messages_by_session) == 2  # Both players
    for session_id, messages in messages_by_session.items():
        assert len(messages) == 1
        assert messages[0].type == MessageType.CHAT_MESSAGE.value
        assert messages[0].data["message"] == "Hello everyone!"


@pytest.mark.asyncio
async def test_chat_isolation_between_games(server_with_players, auth_manager):
    """Test chat messages are isolated to specific games."""
    server = server_with_players

    # Create two different games
    from server.game_session import GameSession
    game1 = GameSession("game-1", "Game 1", max_players=4)
    game2 = GameSession("game-2", "Game 2", max_players=4)

    # Create additional sessions for game 2
    token3, session3 = auth_manager.create_session("Player3")
    token4, session4 = auth_manager.create_session("Player4")
    session3.game_id = "game-2"
    session4.game_id = "game-2"

    # Assign players to different games
    sessions = list(auth_manager._sessions.values())
    sessions[0].game_id = "game-1"
    sessions[1].game_id = "game-1"

    await game1.add_player(sessions[0].player_id, sessions[0].player_name)
    await game1.add_player(sessions[1].player_id, sessions[1].player_name)
    await game2.add_player(session3.player_id, session3.player_name)
    await game2.add_player(session4.player_id, session4.player_name)

    server.game_manager._games["game-1"] = game1
    server.game_manager._games["game-2"] = game2

    # Add websocket connections for new sessions
    for session in [session3, session4]:
        ws = AsyncMock()
        ws.closed = False
        server.connections[session.session_id] = ws
        server.session_to_player[session.session_id] = session.player_id

    # Track messages
    messages_by_session = {}

    async def mock_send_to_session(session_id, message):
        if session_id not in messages_by_session:
            messages_by_session[session_id] = []
        messages_by_session[session_id].append(message)

    server.send_message_to_session = mock_send_to_session

    # Send chat to game-1
    chat_msg = Message.chat_message("player1", "Alice", "Hello Game 1!")
    await server.broadcast_to_game("game-1", chat_msg)

    # Verify only game-1 players received it
    game1_sessions = [sessions[0].session_id, sessions[1].session_id]
    game2_sessions = [session3.session_id, session4.session_id]

    # Game 1 players should have received the message
    for session_id in game1_sessions:
        assert session_id in messages_by_session
        assert len(messages_by_session[session_id]) == 1

    # Game 2 players should NOT have received the message
    for session_id in game2_sessions:
        assert session_id not in messages_by_session


@pytest.mark.asyncio
async def test_chat_message_ordering():
    """Test that chat messages maintain order."""
    server = VeinbornServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    # Create session and game
    token, session = auth_manager.create_session("Player1")
    session.game_id = "test-game"

    from server.game_session import GameSession
    game = GameSession("test-game", "Test Game")
    await game.add_player(session.player_id, session.player_name)
    server.game_manager._games["test-game"] = game

    # Add connection
    ws = AsyncMock()
    server.connections[session.session_id] = ws
    server.session_to_player[session.session_id] = session.player_id

    # Track messages in order
    received_messages = []

    async def mock_send_to_session(session_id, message):
        received_messages.append(message.data["message"])

    server.send_message_to_session = mock_send_to_session

    # Send multiple chat messages
    messages = ["First", "Second", "Third", "Fourth"]
    for msg_text in messages:
        chat_msg = Message.chat_message(session.player_id, session.player_name, msg_text)
        await server.broadcast_to_game("test-game", chat_msg)

    # Verify order is maintained
    assert received_messages == messages


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_chat_with_disconnected_player_connection():
    """Test chat when player's websocket is disconnected."""
    server = VeinbornServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    # Create sessions
    token1, session1 = auth_manager.create_session("Player1")
    token2, session2 = auth_manager.create_session("Player2")
    session1.game_id = "test-game"
    session2.game_id = "test-game"

    from server.game_session import GameSession
    game = GameSession("test-game", "Test Game")
    await game.add_player(session1.player_id, session1.player_name)
    await game.add_player(session2.player_id, session2.player_name)
    server.game_manager._games["test-game"] = game

    # Player 1 connected, Player 2 disconnected
    ws1 = AsyncMock()
    server.connections[session1.session_id] = ws1
    server.session_to_player[session1.session_id] = session1.player_id
    # Note: No connection for session2

    # Track sent messages
    sent_to_ws1 = []

    async def mock_send_message(ws, message):
        sent_to_ws1.append(message)

    server.send_message = mock_send_message

    # Broadcast chat message
    chat_msg = Message.chat_message("player1", "Alice", "Hello!")
    await server.broadcast_to_game("test-game", chat_msg)

    # Verify only connected player received message (no errors for disconnected)
    assert len(sent_to_ws1) == 1


@pytest.mark.asyncio
async def test_chat_unicode_support():
    """Test chat supports unicode characters."""
    server = VeinbornServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    token, session = auth_manager.create_session("Player1")
    session.game_id = "test-game"

    # Unicode message
    unicode_msg = "Hello! 你好 🎮 Привет こんにちは"

    chat_msg = Message(
        type=MessageType.CHAT.value,
        data={"message": unicode_msg}
    )

    from server.game_session import GameSession
    game = GameSession("test-game", "Test Game")
    await game.add_player(session.player_id, session.player_name)
    server.game_manager._games["test-game"] = game

    sent_messages = []

    async def mock_broadcast(game_id, message):
        sent_messages.append(message)

    server.broadcast_to_game = mock_broadcast

    await server.handle_chat(session.session_id, session, chat_msg)

    assert len(sent_messages) == 1
    assert sent_messages[0].data["message"] == unicode_msg


@pytest.mark.asyncio
async def test_handle_chat_invalid_session():
    """Test chat handling with invalid session."""
    server = VeinbornServer()

    # Create a session that doesn't exist in auth manager
    fake_session = Session("fake-session", "fake-player", "FakePlayer")
    fake_session.game_id = "test-game"

    chat_msg = Message(
        type=MessageType.CHAT.value,
        data={"message": "Hello"}
    )

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    # This should handle gracefully
    await server.handle_chat("fake-session", fake_session, chat_msg)

    # Should work since we pass the session object directly
    # The actual validation happens in handle_message before handle_chat
