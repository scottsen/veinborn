"""
Integration tests for Multiplayer Flow.

Tests complete multiplayer scenarios:
- Full game lifecycle from creation to completion
- Multiple players interacting
- Chat during gameplay
- Player disconnection and reconnection
- Complete end-to-end workflows
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from server.websocket_server import BrogueServer
from server.messages import Message, MessageType
from server.game_session import GameSession


pytestmark = pytest.mark.integration


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def server():
    """Create a server instance."""
    return BrogueServer()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    ws = AsyncMock()
    ws.remote_address = ("127.0.0.1", 12345)
    ws.closed = False
    return ws


# ============================================================================
# Complete Game Flow Tests
# ============================================================================

@pytest.mark.asyncio
async def test_complete_two_player_game_flow(server):
    """Test complete flow: create game, join, ready, start."""
    # Player 1 creates game
    ws1 = AsyncMock()
    ws1.recv = AsyncMock(return_value=Message.auth("Player1").to_json())

    session_id1 = await server.authenticate_connection(ws1)
    assert session_id1 is not None

    session1 = server.auth_manager.get_session(session_id1)
    server.connections[session_id1] = ws1
    server.session_to_player[session_id1] = session1.player_id

    # Mock methods
    async def mock_broadcast_state(game_id, force_full_state=False):
        pass

    server.broadcast_game_state = mock_broadcast_state

    # Create game
    create_msg = Message.create_game("Test Game", max_players=2, player_class="warrior")
    await server.handle_create_game(session_id1, session1, create_msg)

    game_id = session1.game_id
    assert game_id is not None

    # Player 2 joins
    ws2 = AsyncMock()
    ws2.recv = AsyncMock(return_value=Message.auth("Player2").to_json())

    session_id2 = await server.authenticate_connection(ws2)
    session2 = server.auth_manager.get_session(session_id2)
    server.connections[session_id2] = ws2
    server.session_to_player[session_id2] = session2.player_id

    join_msg = Message.join_game(game_id, player_class="mage")
    await server.handle_join_game(session_id2, session2, join_msg)

    # Verify both players in game
    game = await server.game_manager.get_game(game_id)
    assert game.get_player_count() == 2

    # Both players ready
    ready_msg = Message(type=MessageType.READY.value, data={"ready": True})

    async def mock_broadcast(game_id, msg):
        pass

    server.broadcast_to_game = mock_broadcast

    await server.handle_ready(session_id1, session1, ready_msg)
    await server.handle_ready(session_id2, session2, ready_msg)

    # Game should start
    assert game.all_players_ready()


@pytest.mark.asyncio
async def test_chat_during_game(server):
    """Test players can chat during game."""
    # Setup: Create game with 2 players
    token1, session1 = server.auth_manager.create_session("Player1")
    token2, session2 = server.auth_manager.create_session("Player2")

    game = await server.game_manager.create_game("Test Game")
    await server.game_manager.join_game(game.game_id, session1.player_id, "Player1")
    await server.game_manager.join_game(game.game_id, session2.player_id, "Player2")

    session1.game_id = game.game_id
    session2.game_id = game.game_id

    # Add connections
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    server.connections[session1.session_id] = ws1
    server.connections[session2.session_id] = ws2

    # Player 1 sends chat
    chat_msg = Message(type=MessageType.CHAT.value, data={"message": "Hello!"})

    received_messages = []

    async def mock_broadcast(game_id, message):
        received_messages.append(message)

    server.broadcast_to_game = mock_broadcast

    await server.handle_chat(session1.session_id, session1, chat_msg)

    # Verify chat was broadcast
    assert len(received_messages) == 1
    assert received_messages[0].type == MessageType.CHAT_MESSAGE.value
    assert received_messages[0].data["message"] == "Hello!"
    assert received_messages[0].data["player_name"] == "Player1"


@pytest.mark.asyncio
async def test_player_disconnect_and_reconnect_flow(server):
    """Test complete disconnect/reconnect flow."""
    # Create game with player
    token, session = server.auth_manager.create_session("Player1")

    game = await server.game_manager.create_game("Test Game")
    await server.game_manager.join_game(game.game_id, session.player_id, "Player1")
    session.game_id = game.game_id

    ws = AsyncMock()
    ws.closed = False
    server.connections[session.session_id] = ws
    server.session_to_player[session.session_id] = session.player_id

    # Mock broadcast
    async def mock_broadcast(game_id, msg):
        pass

    server.broadcast_to_game = mock_broadcast

    # Disconnect player (preserve session)
    await server.disconnect_client(session.session_id, "Connection lost", preserve_session=True)

    # Verify player marked as disconnected
    player_info = game.players[session.player_id]
    assert player_info.is_disconnected()

    # Verify session still exists but inactive
    restored_session = server.auth_manager.get_session(session.session_id)
    assert restored_session is not None
    assert not restored_session.is_active

    # Reconnect player
    new_ws = AsyncMock()
    server.connections[session.session_id] = new_ws

    async def mock_broadcast_state(game_id, force_full_state=False):
        pass

    server.broadcast_game_state = mock_broadcast_state

    reconnect_msg = Message(type=MessageType.RECONNECT.value, data={})
    await server.handle_reconnect(session.session_id, restored_session, reconnect_msg)

    # Verify player reconnected
    assert player_info.is_connected()
    assert restored_session.is_active


@pytest.mark.asyncio
async def test_multiple_games_isolation(server):
    """Test multiple games run independently."""
    # Create two games
    game1 = await server.game_manager.create_game("Game 1")
    game2 = await server.game_manager.create_game("Game 2")

    # Create 4 players
    sessions = []
    for i in range(4):
        token, session = server.auth_manager.create_session(f"Player{i+1}")
        sessions.append(session)

    # Players 0,1 join game1
    await server.game_manager.join_game(game1.game_id, sessions[0].player_id, "Player1")
    await server.game_manager.join_game(game1.game_id, sessions[1].player_id, "Player2")

    # Players 2,3 join game2
    await server.game_manager.join_game(game2.game_id, sessions[2].player_id, "Player3")
    await server.game_manager.join_game(game2.game_id, sessions[3].player_id, "Player4")

    # Verify games are separate
    assert game1.get_player_count() == 2
    assert game2.get_player_count() == 2

    player1_game = await server.game_manager.get_player_game(sessions[0].player_id)
    player3_game = await server.game_manager.get_player_game(sessions[2].player_id)

    assert player1_game.game_id == game1.game_id
    assert player3_game.game_id == game2.game_id


@pytest.mark.asyncio
async def test_player_leave_during_game(server):
    """Test player voluntarily leaving during game."""
    # Setup game with 2 players
    token1, session1 = server.auth_manager.create_session("Player1")
    token2, session2 = server.auth_manager.create_session("Player2")

    game = await server.game_manager.create_game("Test Game")
    await server.game_manager.join_game(game.game_id, session1.player_id, "Player1")
    await server.game_manager.join_game(game.game_id, session2.player_id, "Player2")

    session1.game_id = game.game_id
    session2.game_id = game.game_id

    ws1 = AsyncMock()
    server.connections[session1.session_id] = ws1

    # Mock broadcast
    async def mock_broadcast(game_id, msg):
        pass

    async def mock_broadcast_state(game_id):
        pass

    server.broadcast_to_game = mock_broadcast
    server.broadcast_game_state = mock_broadcast_state

    # Player 1 leaves
    leave_msg = Message(type=MessageType.LEAVE_GAME.value, data={})
    await server.handle_leave_game(session1.session_id, session1, leave_msg)

    # Verify player left
    assert session1.game_id is None
    player_info = game.players[session1.player_id]
    assert player_info.has_left()

    # Game should still exist (player 2 still there)
    assert not game.is_finished
    assert game.get_player_count() == 2  # Both still in players dict


@pytest.mark.asyncio
async def test_game_cleanup_when_empty(server):
    """Test game is cleaned up when all players leave."""
    # Create game with one player
    token, session = server.auth_manager.create_session("Player1")

    game = await server.game_manager.create_game("Test Game")
    await server.game_manager.join_game(game.game_id, session.player_id, "Player1")

    game_id = game.game_id

    # Player leaves
    await server.game_manager.leave_game(session.player_id)

    # Game should be removed
    retrieved_game = await server.game_manager.get_game(game_id)
    assert retrieved_game is None


@pytest.mark.asyncio
async def test_maximum_players_limit(server):
    """Test game enforces maximum player limit."""
    # Create game with max 2 players
    game = await server.game_manager.create_game("Test Game", max_players=2)

    # Add 2 players successfully
    success1, _ = await server.game_manager.join_game(
        game.game_id, "player1", "Player1", "warrior"
    )
    success2, _ = await server.game_manager.join_game(
        game.game_id, "player2", "Player2", "mage"
    )

    assert success1
    assert success2

    # Third player should fail
    success3, error3 = await server.game_manager.join_game(
        game.game_id, "player3", "Player3", "rogue"
    )

    assert not success3
    assert error3 is not None


@pytest.mark.asyncio
async def test_ready_status_sync(server):
    """Test ready status synchronization."""
    game = await server.game_manager.create_game("Test Game")

    # Add players
    await server.game_manager.join_game(game.game_id, "p1", "Player1", "warrior")
    await server.game_manager.join_game(game.game_id, "p2", "Player2", "mage")

    # Initially not ready
    assert not game.all_players_ready()

    # One player ready
    await game.set_player_ready("p1", True)
    assert not game.all_players_ready()

    # Both ready
    await game.set_player_ready("p2", True)
    assert game.all_players_ready()

    # One unready
    await game.set_player_ready("p1", False)
    assert not game.all_players_ready()


@pytest.mark.asyncio
async def test_sequential_chat_messages(server):
    """Test multiple chat messages in sequence."""
    # Setup game
    token, session = server.auth_manager.create_session("Player1")

    game = await server.game_manager.create_game("Test Game")
    await server.game_manager.join_game(game.game_id, session.player_id, "Player1")
    session.game_id = game.game_id

    # Track messages
    received_messages = []

    async def mock_broadcast(game_id, message):
        received_messages.append(message.data["message"])

    server.broadcast_to_game = mock_broadcast

    # Send multiple chat messages
    messages = ["First", "Second", "Third"]
    for msg_text in messages:
        chat_msg = Message(type=MessageType.CHAT.value, data={"message": msg_text})
        await server.handle_chat(session.session_id, session, chat_msg)

    # Verify all messages received in order
    assert received_messages == messages


@pytest.mark.asyncio
async def test_error_recovery(server):
    """Test system handles errors gracefully."""
    token, session = server.auth_manager.create_session("Player1")

    errors = []

    async def mock_send_error(session_id, error_msg):
        errors.append(error_msg)

    server.send_error = mock_send_error

    # Try to join nonexistent game
    join_msg = Message.join_game("nonexistent-game")
    await server.handle_join_game(session.session_id, session, join_msg)

    assert len(errors) > 0

    # Try to chat when not in game
    chat_msg = Message(type=MessageType.CHAT.value, data={"message": "Hello"})
    await server.handle_chat(session.session_id, session, chat_msg)

    assert len(errors) > 1


# ============================================================================
# Stress and Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_rapid_player_joins(server):
    """Test handling rapid player join requests."""
    game = await server.game_manager.create_game("Test Game", max_players=10)

    # Create many sessions
    tasks = []
    for i in range(20):
        task = server.game_manager.join_game(
            game.game_id, f"player{i}", f"Player{i}", "warrior"
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    # Only first 10 should succeed
    successful = sum(1 for success, _ in results if success)
    assert successful == 10
    assert game.get_player_count() == 10


@pytest.mark.asyncio
async def test_concurrent_game_creations(server):
    """Test concurrent game creation."""
    tasks = [
        server.game_manager.create_game(f"Game {i}")
        for i in range(10)
    ]

    games = await asyncio.gather(*tasks)

    assert len(games) == 10
    assert server.game_manager.get_active_game_count() == 10

    # All games should have unique IDs
    game_ids = [g.game_id for g in games]
    assert len(set(game_ids)) == 10


@pytest.mark.asyncio
async def test_player_reconnect_timeout_scenario(server):
    """Test complete reconnection timeout scenario."""
    # Create game with player
    token, session = server.auth_manager.create_session("Player1")

    game = await server.game_manager.create_game("Test Game")
    await server.game_manager.join_game(game.game_id, session.player_id, "Player1")
    session.game_id = game.game_id

    # Set short timeout
    game.players[session.player_id].reconnect_timeout_seconds = 1

    # Disconnect player
    await game.disconnect_player(session.player_id)

    # Wait for timeout
    await asyncio.sleep(1.1)

    # Try to reconnect after timeout
    success, error = await game.reconnect_player(session.player_id)

    assert not success
    assert "timeout" in error.lower()


@pytest.mark.asyncio
async def test_available_games_list(server):
    """Test getting list of available games."""
    # Create various games
    game1 = await server.game_manager.create_game("Game 1", max_players=4)
    game2 = await server.game_manager.create_game("Game 2", max_players=2)
    game3 = await server.game_manager.create_game("Game 3", max_players=4)

    # Fill game2
    await server.game_manager.join_game(game2.game_id, "p1", "P1", "warrior")
    await server.game_manager.join_game(game2.game_id, "p2", "P2", "mage")

    # Start game3
    await server.game_manager.join_game(game3.game_id, "p3", "P3", "warrior")
    game3.is_started = True

    # Get available games
    available = server.game_manager.get_available_games()

    # Only game1 should be available
    assert len(available) == 1
    assert available[0]["game_id"] == game1.game_id
    assert available[0]["game_name"] == "Game 1"
    assert available[0]["player_count"] == 0
    assert available[0]["max_players"] == 4


@pytest.mark.asyncio
async def test_full_multiplayer_session_lifecycle(server):
    """Test complete multiplayer session from start to finish."""
    # Phase 1: Game creation
    token1, session1 = server.auth_manager.create_session("Alice")

    async def mock_broadcast_state(game_id, force_full_state=False):
        pass

    server.broadcast_game_state = mock_broadcast_state

    create_msg = Message.create_game("Epic Quest", max_players=3, player_class="warrior")
    await server.handle_create_game(session1.session_id, session1, create_msg)

    game_id = session1.game_id
    assert game_id is not None

    # Phase 2: Players join
    token2, session2 = server.auth_manager.create_session("Bob")
    token3, session3 = server.auth_manager.create_session("Charlie")

    join_msg2 = Message.join_game(game_id, player_class="mage")
    join_msg3 = Message.join_game(game_id, player_class="rogue")

    await server.handle_join_game(session2.session_id, session2, join_msg2)
    await server.handle_join_game(session3.session_id, session3, join_msg3)

    game = await server.game_manager.get_game(game_id)
    assert game.get_player_count() == 3

    # Phase 3: Chat before game starts
    for session in [session1, session2, session3]:
        ws = AsyncMock()
        server.connections[session.session_id] = ws

    chat_messages = []

    async def mock_broadcast(game_id, msg):
        if msg.type == MessageType.CHAT_MESSAGE.value:
            chat_messages.append(msg.data["message"])

    server.broadcast_to_game = mock_broadcast

    chat1 = Message(type=MessageType.CHAT.value, data={"message": "Ready?"})
    await server.handle_chat(session1.session_id, session1, chat1)

    assert len(chat_messages) == 1

    # Phase 4: Players ready up
    ready_msg = Message(type=MessageType.READY.value, data={"ready": True})

    for session in [session1, session2, session3]:
        await server.handle_ready(session.session_id, session, ready_msg)

    assert game.all_players_ready()

    # Phase 5: Game starts (when all ready)
    # This would normally be triggered in handle_ready

    # Phase 6: One player disconnects
    await server.disconnect_client(session2.session_id, "Connection lost", preserve_session=True)

    player2_info = game.players[session2.player_id]
    assert player2_info.is_disconnected()

    # Phase 7: Player reconnects
    reconnect_msg = Message(type=MessageType.RECONNECT.value, data={})
    await server.handle_reconnect(session2.session_id, session2, reconnect_msg)

    assert player2_info.is_connected()

    # Phase 8: One player leaves voluntarily
    leave_msg = Message(type=MessageType.LEAVE_GAME.value, data={})
    await server.handle_leave_game(session3.session_id, session3, leave_msg)

    player3_info = game.players[session3.player_id]
    assert player3_info.has_left()

    # Verify final state
    assert not game.is_finished  # Still has active players
    assert game.get_player_count() == 3  # All in players dict
