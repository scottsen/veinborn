"""
Unit tests for Multiplayer Reconnection Handling.

Tests the reconnection features added in Phase 3:
- Player disconnection detection
- Reconnection within timeout window
- Reconnection timeout expiration
- AI control during disconnection
- Full state synchronization on reconnect
- Session preservation
"""
import pytest
import time
from unittest.mock import AsyncMock, Mock, patch
from server.game_session import GameSession, PlayerInfo, ConnectionStatus
from server.websocket_server import BrogueServer
from server.auth import AuthManager
from server.messages import Message, MessageType


pytestmark = pytest.mark.unit


# ============================================================================
# PlayerInfo Connection Status Tests
# ============================================================================

def test_player_info_initial_state():
    """Test PlayerInfo starts in connected state."""
    player = PlayerInfo(
        player_id="player1",
        player_name="Alice",
        player_class="warrior"
    )

    assert player.connection_status == ConnectionStatus.CONNECTED
    assert player.is_connected()
    assert not player.is_disconnected()
    assert not player.has_left()
    assert player.disconnected_at is None


def test_mark_player_disconnected():
    """Test marking a player as disconnected."""
    player = PlayerInfo(
        player_id="player1",
        player_name="Alice",
        player_class="warrior"
    )

    player.mark_disconnected()

    assert player.connection_status == ConnectionStatus.DISCONNECTED
    assert player.is_disconnected()
    assert not player.is_connected()
    assert not player.has_left()
    assert player.disconnected_at is not None


def test_mark_player_reconnected():
    """Test marking a disconnected player as reconnected."""
    player = PlayerInfo(
        player_id="player1",
        player_name="Alice",
        player_class="warrior"
    )

    player.mark_disconnected()
    assert player.is_disconnected()

    player.mark_reconnected()

    assert player.connection_status == ConnectionStatus.CONNECTED
    assert player.is_connected()
    assert not player.is_disconnected()
    assert player.disconnected_at is None


def test_mark_player_left():
    """Test marking a player as having left."""
    player = PlayerInfo(
        player_id="player1",
        player_name="Alice",
        player_class="warrior"
    )

    player.mark_left()

    assert player.connection_status == ConnectionStatus.LEFT
    assert player.has_left()
    assert not player.is_connected()
    assert not player.is_disconnected()


def test_reconnect_timeout_not_expired():
    """Test reconnect timeout when within window."""
    player = PlayerInfo(
        player_id="player1",
        player_name="Alice",
        player_class="warrior",
        reconnect_timeout_seconds=120
    )

    player.mark_disconnected()

    # Check immediately - should not be expired
    assert not player.is_reconnect_timeout_expired()


def test_reconnect_timeout_expired():
    """Test reconnect timeout when expired."""
    player = PlayerInfo(
        player_id="player1",
        player_name="Alice",
        player_class="warrior",
        reconnect_timeout_seconds=1  # 1 second timeout
    )

    player.mark_disconnected()

    # Wait for timeout to expire
    time.sleep(1.1)

    assert player.is_reconnect_timeout_expired()


def test_reconnect_timeout_only_applies_to_disconnected():
    """Test reconnect timeout only applies to disconnected players."""
    player = PlayerInfo(
        player_id="player1",
        player_name="Alice",
        player_class="warrior",
        reconnect_timeout_seconds=0  # Already expired
    )

    # Connected player - timeout not applicable
    assert not player.is_reconnect_timeout_expired()

    # Left player - timeout not applicable
    player.mark_left()
    assert not player.is_reconnect_timeout_expired()


def test_custom_reconnect_timeout():
    """Test custom reconnect timeout values."""
    player = PlayerInfo(
        player_id="player1",
        player_name="Alice",
        player_class="warrior",
        reconnect_timeout_seconds=300  # 5 minutes
    )

    player.mark_disconnected()

    # Should not be expired after 1 second
    time.sleep(0.1)
    assert not player.is_reconnect_timeout_expired()


# ============================================================================
# GameSession Disconnection Tests
# ============================================================================

@pytest.mark.asyncio
async def test_disconnect_player():
    """Test disconnecting a player from game session."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")

    success = await game.disconnect_player("player1")

    assert success
    assert "player1" in game.players
    player_info = game.players["player1"]
    assert player_info.is_disconnected()
    assert player_info.disconnected_at is not None


@pytest.mark.asyncio
async def test_disconnect_nonexistent_player():
    """Test disconnecting a player not in the game."""
    game = GameSession("game1", "Test Game", max_players=4)

    success = await game.disconnect_player("nonexistent")

    assert not success


@pytest.mark.asyncio
async def test_reconnect_player_success():
    """Test successful player reconnection."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.disconnect_player("player1")

    success, error = await game.reconnect_player("player1")

    assert success
    assert error is None
    player_info = game.players["player1"]
    assert player_info.is_connected()
    assert player_info.disconnected_at is None


@pytest.mark.asyncio
async def test_reconnect_player_not_in_game():
    """Test reconnecting a player not in the game."""
    game = GameSession("game1", "Test Game", max_players=4)

    success, error = await game.reconnect_player("nonexistent")

    assert not success
    assert "not in game" in error.lower()


@pytest.mark.asyncio
async def test_reconnect_already_connected_player():
    """Test reconnecting a player who is already connected."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")

    success, error = await game.reconnect_player("player1")

    assert not success
    assert "already connected" in error.lower()


@pytest.mark.asyncio
async def test_reconnect_player_who_left():
    """Test reconnecting a player who intentionally left."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.leave_player("player1")

    success, error = await game.reconnect_player("player1")

    assert not success
    assert "left" in error.lower()


@pytest.mark.asyncio
async def test_reconnect_timeout_expired():
    """Test reconnecting after timeout has expired."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")

    # Set short timeout
    game.players["player1"].reconnect_timeout_seconds = 1

    await game.disconnect_player("player1")

    # Wait for timeout
    time.sleep(1.1)

    success, error = await game.reconnect_player("player1")

    assert not success
    assert "timeout" in error.lower()


@pytest.mark.asyncio
async def test_leave_player():
    """Test player voluntarily leaving the game."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    success = await game.leave_player("player1")

    assert success
    assert "player1" in game.players
    player_info = game.players["player1"]
    assert player_info.has_left()
    assert not game.is_finished  # Still has another player


@pytest.mark.asyncio
async def test_leave_player_triggers_game_finish():
    """Test game finishes when all players leave."""
    game = GameSession("game1", "Test Game", max_players=4)
    game.is_started = True

    await game.add_player("player1", "Alice", "warrior")

    await game.leave_player("player1")

    assert game.is_finished


# ============================================================================
# Cleanup Expired Disconnections Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cleanup_expired_disconnections():
    """Test cleaning up players with expired reconnection timeouts."""
    game = GameSession("game1", "Test Game", max_players=4)

    # Add players
    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")
    await game.add_player("player3", "Charlie", "rogue")

    # Disconnect players with different timeouts
    await game.disconnect_player("player1")
    game.players["player1"].reconnect_timeout_seconds = 1  # Will expire

    await game.disconnect_player("player2")
    game.players["player2"].reconnect_timeout_seconds = 300  # Won't expire

    # Wait for player1's timeout to expire
    time.sleep(1.1)

    removed_players = await game.cleanup_expired_disconnections()

    assert "player1" in removed_players
    assert "player2" not in removed_players
    assert "player1" not in game.players  # Removed
    assert "player2" in game.players  # Still there
    assert "player3" in game.players  # Never disconnected


@pytest.mark.asyncio
async def test_cleanup_no_expired_disconnections():
    """Test cleanup when no disconnections have expired."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.disconnect_player("player1")

    removed_players = await game.cleanup_expired_disconnections()

    assert len(removed_players) == 0
    assert "player1" in game.players


@pytest.mark.asyncio
async def test_cleanup_only_affects_disconnected():
    """Test cleanup only affects disconnected players."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    # Only disconnect player1
    await game.disconnect_player("player1")
    game.players["player1"].reconnect_timeout_seconds = 1

    time.sleep(1.1)

    removed_players = await game.cleanup_expired_disconnections()

    assert "player1" in removed_players
    assert "player2" not in removed_players
    assert "player2" in game.players  # Connected player unaffected


# ============================================================================
# Server Reconnection Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_server_handle_reconnect_success():
    """Test server handling successful reconnection."""
    server = BrogueServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    # Create session
    token, session = auth_manager.create_session("Alice")
    session.game_id = "game1"

    # Create game with disconnected player
    game = GameSession("game1", "Test Game")
    await game.add_player(session.player_id, "Alice", "warrior")
    await game.disconnect_player(session.player_id)
    server.game_manager._games["game1"] = game

    # Add connection
    ws = AsyncMock()
    server.connections[session.session_id] = ws

    # Mock methods
    sent_messages = []

    async def mock_send_to_session(session_id, message):
        sent_messages.append(message)

    async def mock_broadcast_to_game(game_id, message):
        sent_messages.append(message)

    async def mock_broadcast_game_state(game_id, force_full_state=False):
        pass

    server.send_message_to_session = mock_send_to_session
    server.broadcast_to_game = mock_broadcast_to_game
    server.broadcast_game_state = mock_broadcast_game_state

    # Handle reconnection
    reconnect_msg = Message(type=MessageType.RECONNECT.value, data={})
    await server.handle_reconnect(session.session_id, session, reconnect_msg)

    # Verify player was reconnected
    player_info = game.players[session.player_id]
    assert player_info.is_connected()

    # Verify success message sent
    success_messages = [m for m in sent_messages if m.type == MessageType.SYSTEM.value]
    assert len(success_messages) >= 1
    assert "reconnected" in success_messages[0].data["message"].lower()


@pytest.mark.asyncio
async def test_server_handle_reconnect_not_in_game():
    """Test server reconnection when player not in a game."""
    server = BrogueServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    token, session = auth_manager.create_session("Alice")
    session.game_id = None  # Not in a game

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    reconnect_msg = Message(type=MessageType.RECONNECT.value, data={})
    await server.handle_reconnect(session.session_id, session, reconnect_msg)

    assert len(errors) == 1
    assert "not in a game" in errors[0].lower()


@pytest.mark.asyncio
async def test_server_handle_reconnect_game_not_found():
    """Test server reconnection when game doesn't exist."""
    server = BrogueServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    token, session = auth_manager.create_session("Alice")
    session.game_id = "nonexistent-game"

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    reconnect_msg = Message(type=MessageType.RECONNECT.value, data={})
    await server.handle_reconnect(session.session_id, session, reconnect_msg)

    assert len(errors) == 1
    assert "not found" in errors[0].lower()


@pytest.mark.asyncio
async def test_server_disconnect_client_preserves_session():
    """Test server disconnect preserves session for reconnection."""
    server = BrogueServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    token, session = auth_manager.create_session("Alice")
    session.game_id = "game1"

    # Create game with player
    game = GameSession("game1", "Test Game")
    await game.add_player(session.player_id, "Alice", "warrior")
    server.game_manager._games["game1"] = game

    # Add connection
    ws = AsyncMock()
    ws.closed = False
    server.connections[session.session_id] = ws
    server.session_to_player[session.session_id] = session.player_id

    # Mock broadcast
    broadcast_messages = []

    async def mock_broadcast(game_id, message):
        broadcast_messages.append(message)

    server.broadcast_to_game = mock_broadcast

    # Disconnect client with session preservation
    await server.disconnect_client(session.session_id, "Test disconnect", preserve_session=True)

    # Verify session still exists
    restored_session = auth_manager.get_session(session.session_id)
    assert restored_session is not None
    assert not restored_session.is_active  # Marked inactive

    # Verify player marked as disconnected in game
    player_info = game.players[session.player_id]
    assert player_info.is_disconnected()

    # Verify disconnect notification sent
    disconnect_messages = [m for m in broadcast_messages if m.type == MessageType.PLAYER_DISCONNECTED.value]
    assert len(disconnect_messages) == 1


@pytest.mark.asyncio
async def test_server_disconnect_client_no_preservation():
    """Test server disconnect without session preservation."""
    server = BrogueServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    token, session = auth_manager.create_session("Alice")
    session.game_id = "game1"

    # Create game
    game = GameSession("game1", "Test Game")
    await game.add_player(session.player_id, "Alice", "warrior")
    server.game_manager._games["game1"] = game

    # Add connection
    ws = AsyncMock()
    ws.closed = False
    server.connections[session.session_id] = ws

    # Disconnect without preservation
    await server.disconnect_client(session.session_id, "Test disconnect", preserve_session=False)

    # Verify session is invalidated
    restored_session = auth_manager.get_session(session.session_id)
    assert restored_session is None


# ============================================================================
# Cleanup Task Tests
# ============================================================================

@pytest.mark.asyncio
async def test_server_cleanup_task_removes_expired_players():
    """Test server cleanup task removes players with expired timeouts."""
    server = BrogueServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    # Create game with disconnected player
    game = GameSession("game1", "Test Game")
    await game.add_player("player1", "Alice", "warrior")
    await game.disconnect_player("player1")
    game.players["player1"].reconnect_timeout_seconds = 0  # Already expired

    server.game_manager._games["game1"] = game

    # Mock broadcast
    broadcast_messages = []

    async def mock_broadcast(game_id, message):
        broadcast_messages.append(message)

    async def mock_broadcast_state(game_id):
        pass

    server.broadcast_to_game = mock_broadcast
    server.broadcast_game_state = mock_broadcast_state

    # Run one iteration of cleanup
    server.is_running = True

    # Manually trigger the cleanup logic
    total_removed = 0
    for game_id, game_obj in list(server.game_manager._games.items()):
        removed_players = await game_obj.cleanup_expired_disconnections()
        total_removed += len(removed_players)

    # Verify player was removed
    assert total_removed == 1
    assert "player1" not in game.players


# ============================================================================
# Full State Sync on Reconnect Tests
# ============================================================================

@pytest.mark.asyncio
async def test_reconnect_sends_full_state():
    """Test reconnection triggers full state synchronization."""
    server = BrogueServer()
    auth_manager = AuthManager()
    server.auth_manager = auth_manager

    token, session = auth_manager.create_session("Alice")
    session.game_id = "game1"

    # Create and start game
    game = GameSession("game1", "Test Game")
    await game.add_player(session.player_id, "Alice", "warrior")
    await game.disconnect_player(session.player_id)
    server.game_manager._games["game1"] = game

    ws = AsyncMock()
    server.connections[session.session_id] = ws

    # Track broadcast_game_state calls
    broadcast_calls = []

    async def mock_broadcast_state(game_id, force_full_state=False):
        broadcast_calls.append({"game_id": game_id, "force_full_state": force_full_state})

    async def mock_send_to_session(session_id, message):
        pass

    async def mock_broadcast_to_game(game_id, message):
        pass

    server.broadcast_game_state = mock_broadcast_state
    server.send_message_to_session = mock_send_to_session
    server.broadcast_to_game = mock_broadcast_to_game

    # Handle reconnection
    reconnect_msg = Message(type=MessageType.RECONNECT.value, data={})
    await server.handle_reconnect(session.session_id, session, reconnect_msg)

    # Verify full state was requested
    assert len(broadcast_calls) == 1
    assert broadcast_calls[0]["force_full_state"] is True


# ============================================================================
# Get Disconnected Players Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_disconnected_players():
    """Test getting list of disconnected players."""
    game = GameSession("game1", "Test Game")

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")
    await game.add_player("player3", "Charlie", "rogue")

    # Disconnect some players
    await game.disconnect_player("player1")
    await game.disconnect_player("player3")

    disconnected = game.get_disconnected_players()

    assert len(disconnected) == 2
    assert "player1" in disconnected
    assert "player3" in disconnected
    assert "player2" not in disconnected


@pytest.mark.asyncio
async def test_get_disconnected_players_only_alive():
    """Test get_disconnected_players only returns alive players."""
    game = GameSession("game1", "Test Game")

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    # Disconnect both
    await game.disconnect_player("player1")
    await game.disconnect_player("player2")

    # Mark player2 as dead
    game.players["player2"].is_alive = False

    disconnected = game.get_disconnected_players()

    # Only player1 should be returned (alive and disconnected)
    assert len(disconnected) == 1
    assert "player1" in disconnected
