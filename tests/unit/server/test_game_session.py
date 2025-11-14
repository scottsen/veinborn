"""
Unit tests for Game Session Management.

Tests game session functionality:
- Game session creation
- Player management (add/remove)
- Game lifecycle (start/finish)
- Turn management
- State management
- Session manager operations
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from server.game_session import (
    GameSession,
    GameSessionManager,
    PlayerInfo,
    ConnectionStatus
)


pytestmark = pytest.mark.unit


# ============================================================================
# GameSession Initialization Tests
# ============================================================================

def test_game_session_creation():
    """Test creating a new game session."""
    game = GameSession(
        game_id="game1",
        game_name="Test Game",
        max_players=4,
        actions_per_round=4
    )

    assert game.game_id == "game1"
    assert game.game_name == "Test Game"
    assert game.max_players == 4
    assert game.actions_per_round == 4
    assert len(game.players) == 0
    assert not game.is_started
    assert not game.is_finished


def test_game_session_default_values():
    """Test game session with default values."""
    game = GameSession("game1", "Test")

    assert game.max_players == 4
    assert game.actions_per_round == 4


# ============================================================================
# Player Management Tests
# ============================================================================

@pytest.mark.asyncio
async def test_add_player_success():
    """Test successfully adding a player to game."""
    game = GameSession("game1", "Test Game", max_players=4)

    success = await game.add_player("player1", "Alice", "warrior")

    assert success
    assert "player1" in game.players
    assert game.players["player1"].player_name == "Alice"
    assert game.players["player1"].player_class == "warrior"
    assert "player1" in game.player_order


@pytest.mark.asyncio
async def test_add_multiple_players():
    """Test adding multiple players to game."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")
    await game.add_player("player3", "Charlie", "rogue")

    assert game.get_player_count() == 3
    assert len(game.player_order) == 3


@pytest.mark.asyncio
async def test_add_player_when_full():
    """Test adding player when game is full."""
    game = GameSession("game1", "Test Game", max_players=2)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    # Try to add third player
    success = await game.add_player("player3", "Charlie", "rogue")

    assert not success
    assert game.get_player_count() == 2


@pytest.mark.asyncio
async def test_add_duplicate_player():
    """Test adding same player twice."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    success = await game.add_player("player1", "Alice", "mage")

    assert not success
    assert game.get_player_count() == 1


@pytest.mark.asyncio
async def test_add_player_after_game_started():
    """Test cannot add player after game started."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    game.is_started = True

    success = await game.add_player("player2", "Bob", "mage")

    assert not success


@pytest.mark.asyncio
async def test_remove_player():
    """Test removing a player from game."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    success = await game.remove_player("player1")

    assert success
    assert "player1" not in game.players
    assert "player1" not in game.player_order
    assert game.get_player_count() == 1


@pytest.mark.asyncio
async def test_remove_nonexistent_player():
    """Test removing player not in game."""
    game = GameSession("game1", "Test Game", max_players=4)

    success = await game.remove_player("nonexistent")

    assert not success


@pytest.mark.asyncio
async def test_remove_last_player_finishes_game():
    """Test removing last player marks game as finished."""
    game = GameSession("game1", "Test Game", max_players=4)
    game.is_started = True

    await game.add_player("player1", "Alice", "warrior")
    await game.remove_player("player1")

    assert game.is_finished


# ============================================================================
# Game Lifecycle Tests
# ============================================================================

@pytest.mark.asyncio
async def test_can_join_new_game():
    """Test can join a new game."""
    game = GameSession("game1", "Test Game", max_players=4)

    assert game.can_join()


@pytest.mark.asyncio
async def test_cannot_join_full_game():
    """Test cannot join when game is full."""
    game = GameSession("game1", "Test Game", max_players=2)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    assert not game.can_join()


@pytest.mark.asyncio
async def test_cannot_join_started_game():
    """Test cannot join after game has started."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    game.is_started = True

    assert not game.can_join()


@pytest.mark.asyncio
async def test_cannot_join_finished_game():
    """Test cannot join a finished game."""
    game = GameSession("game1", "Test Game", max_players=4)

    game.is_finished = True

    assert not game.can_join()


@pytest.mark.asyncio
async def test_start_game():
    """Test starting a game."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    success = await game.start_game()

    assert success
    assert game.is_started
    assert game.mp_game_state is not None


@pytest.mark.asyncio
async def test_cannot_start_game_twice():
    """Test cannot start game that's already started."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.start_game()

    success = await game.start_game()

    assert not success


@pytest.mark.asyncio
async def test_cannot_start_game_without_players():
    """Test cannot start game with no players."""
    game = GameSession("game1", "Test Game", max_players=4)

    success = await game.start_game()

    assert not success


@pytest.mark.asyncio
async def test_start_game_initializes_player_entities():
    """Test starting game creates player entities."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    await game.start_game()

    # Verify entity IDs were assigned
    for player_info in game.players.values():
        assert player_info.entity_id is not None


# ============================================================================
# Ready Status Tests
# ============================================================================

@pytest.mark.asyncio
async def test_set_player_ready():
    """Test setting player ready status."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")

    success = await game.set_player_ready("player1", True)

    assert success
    assert game.players["player1"].is_ready


@pytest.mark.asyncio
async def test_set_player_not_ready():
    """Test setting player not ready."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.set_player_ready("player1", True)

    success = await game.set_player_ready("player1", False)

    assert success
    assert not game.players["player1"].is_ready


@pytest.mark.asyncio
async def test_set_ready_nonexistent_player():
    """Test setting ready for nonexistent player."""
    game = GameSession("game1", "Test Game", max_players=4)

    success = await game.set_player_ready("nonexistent", True)

    assert not success


@pytest.mark.asyncio
async def test_all_players_ready():
    """Test checking if all players are ready."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    # Not all ready yet
    assert not game.all_players_ready()

    await game.set_player_ready("player1", True)
    assert not game.all_players_ready()

    await game.set_player_ready("player2", True)
    assert game.all_players_ready()


@pytest.mark.asyncio
async def test_all_players_ready_empty_game():
    """Test all_players_ready returns False for empty game."""
    game = GameSession("game1", "Test Game", max_players=4)

    assert not game.all_players_ready()


# ============================================================================
# State Management Tests
# ============================================================================

def test_get_state_dict_before_start():
    """Test getting state dict before game starts."""
    game = GameSession("game1", "Test Game", max_players=4, actions_per_round=4)

    state = game.get_state_dict()

    assert state["game_id"] == "game1"
    assert state["game_name"] == "Test Game"
    assert not state["is_started"]
    assert not state["is_finished"]
    assert state["actions_per_round"] == 4
    assert "players" in state


@pytest.mark.asyncio
async def test_get_state_dict_with_players():
    """Test state dict includes player information."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.add_player("player2", "Bob", "mage")

    state = game.get_state_dict()

    assert len(state["players"]) == 2
    assert any(p["player_name"] == "Alice" for p in state["players"])
    assert any(p["player_name"] == "Bob" for p in state["players"])


@pytest.mark.asyncio
async def test_get_state_dict_after_start():
    """Test state dict after game starts."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.start_game()

    state = game.get_state_dict(use_delta=False)

    assert state["is_started"]
    assert state["game_id"] == "game1"


def test_reset_state_tracking():
    """Test resetting state tracking."""
    game = GameSession("game1", "Test Game")

    game.last_state = {"some": "data"}

    game.reset_state_tracking()

    assert game.last_state is None


# ============================================================================
# Action Processing Tests
# ============================================================================

@pytest.mark.asyncio
async def test_process_action_game_not_started():
    """Test processing action when game not started."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")

    from unittest.mock import Mock
    action = Mock()

    success, error = await game.process_action("player1", action)

    assert not success
    assert "not active" in error.lower()


@pytest.mark.asyncio
async def test_process_action_player_not_in_game():
    """Test processing action for player not in game."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.start_game()

    from unittest.mock import Mock
    action = Mock()

    success, error = await game.process_action("nonexistent", action)

    assert not success
    assert "not in game" in error.lower()


@pytest.mark.asyncio
async def test_process_action_disconnected_player():
    """Test processing action for disconnected player."""
    game = GameSession("game1", "Test Game", max_players=4)

    await game.add_player("player1", "Alice", "warrior")
    await game.disconnect_player("player1")
    await game.start_game()

    from unittest.mock import Mock
    action = Mock()

    success, error = await game.process_action("player1", action)

    assert not success
    assert "disconnected" in error.lower()


# ============================================================================
# GameSessionManager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_manager_create_game():
    """Test manager creates game."""
    manager = GameSessionManager()

    game = await manager.create_game("Test Game", max_players=4, actions_per_round=4)

    assert game.game_name == "Test Game"
    assert game.max_players == 4
    assert manager.get_active_game_count() == 1


@pytest.mark.asyncio
async def test_manager_get_game():
    """Test manager retrieves game by ID."""
    manager = GameSessionManager()

    game1 = await manager.create_game("Game 1")

    retrieved = await manager.get_game(game1.game_id)

    assert retrieved is not None
    assert retrieved.game_id == game1.game_id


@pytest.mark.asyncio
async def test_manager_get_nonexistent_game():
    """Test manager returns None for nonexistent game."""
    manager = GameSessionManager()

    game = await manager.get_game("nonexistent")

    assert game is None


@pytest.mark.asyncio
async def test_manager_join_game():
    """Test manager joins player to game."""
    manager = GameSessionManager()

    game = await manager.create_game("Test Game")

    success, error = await manager.join_game(
        game.game_id, "player1", "Alice", "warrior"
    )

    assert success
    assert error is None
    assert game.get_player_count() == 1


@pytest.mark.asyncio
async def test_manager_join_nonexistent_game():
    """Test manager rejects join to nonexistent game."""
    manager = GameSessionManager()

    success, error = await manager.join_game(
        "nonexistent", "player1", "Alice", "warrior"
    )

    assert not success
    assert "not found" in error.lower()


@pytest.mark.asyncio
async def test_manager_join_already_in_game():
    """Test manager prevents player from joining multiple games."""
    manager = GameSessionManager()

    game1 = await manager.create_game("Game 1")
    game2 = await manager.create_game("Game 2")

    await manager.join_game(game1.game_id, "player1", "Alice", "warrior")
    success, error = await manager.join_game(game2.game_id, "player1", "Alice", "mage")

    assert not success
    assert "already in" in error.lower()


@pytest.mark.asyncio
async def test_manager_leave_game():
    """Test manager removes player from game."""
    manager = GameSessionManager()

    game = await manager.create_game("Test Game")
    await manager.join_game(game.game_id, "player1", "Alice", "warrior")

    success, error = await manager.leave_game("player1")

    assert success
    assert error is None
    assert game.get_player_count() == 0


@pytest.mark.asyncio
async def test_manager_leave_game_not_in_any():
    """Test manager handles leaving when not in any game."""
    manager = GameSessionManager()

    success, error = await manager.leave_game("player1")

    assert not success
    assert "not in any game" in error.lower()


@pytest.mark.asyncio
async def test_manager_leave_game_cleans_up_empty():
    """Test manager removes empty games."""
    manager = GameSessionManager()

    game = await manager.create_game("Test Game")
    await manager.join_game(game.game_id, "player1", "Alice", "warrior")

    await manager.leave_game("player1")

    # Game should be removed
    assert manager.get_active_game_count() == 0


@pytest.mark.asyncio
async def test_manager_get_player_game():
    """Test manager retrieves player's current game."""
    manager = GameSessionManager()

    game = await manager.create_game("Test Game")
    await manager.join_game(game.game_id, "player1", "Alice", "warrior")

    player_game = await manager.get_player_game("player1")

    assert player_game is not None
    assert player_game.game_id == game.game_id


@pytest.mark.asyncio
async def test_manager_get_player_game_not_in_game():
    """Test manager returns None when player not in game."""
    manager = GameSessionManager()

    player_game = await manager.get_player_game("player1")

    assert player_game is None


@pytest.mark.asyncio
async def test_manager_get_available_games():
    """Test manager lists available games."""
    manager = GameSessionManager()

    game1 = await manager.create_game("Game 1", max_players=4)
    game2 = await manager.create_game("Game 2", max_players=2)

    # Fill game2
    await manager.join_game(game2.game_id, "p1", "Player1", "warrior")
    await manager.join_game(game2.game_id, "p2", "Player2", "mage")

    available = manager.get_available_games()

    # Only game1 should be available
    assert len(available) == 1
    assert available[0]["game_id"] == game1.game_id


@pytest.mark.asyncio
async def test_manager_get_available_games_excludes_started():
    """Test manager excludes started games from available list."""
    manager = GameSessionManager()

    game1 = await manager.create_game("Game 1")
    game2 = await manager.create_game("Game 2")

    # Start game2
    await manager.join_game(game2.game_id, "p1", "Player1", "warrior")
    game2.is_started = True

    available = manager.get_available_games()

    # Only game1 should be available
    assert len(available) == 1
    assert available[0]["game_id"] == game1.game_id


def test_manager_get_active_game_count():
    """Test manager counts active games."""
    manager = GameSessionManager()

    assert manager.get_active_game_count() == 0


@pytest.mark.asyncio
async def test_manager_multiple_games():
    """Test manager handles multiple games."""
    manager = GameSessionManager()

    game1 = await manager.create_game("Game 1")
    game2 = await manager.create_game("Game 2")
    game3 = await manager.create_game("Game 3")

    assert manager.get_active_game_count() == 3


# ============================================================================
# Concurrency Tests
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_player_adds():
    """Test concurrent player additions are handled safely."""
    game = GameSession("game1", "Test Game", max_players=4)

    # Try to add players concurrently
    tasks = [
        game.add_player(f"player{i}", f"Player{i}", "warrior")
        for i in range(10)
    ]

    results = await asyncio.gather(*tasks)

    # Should only accept max_players
    successful_adds = sum(1 for r in results if r)
    assert successful_adds == 4
    assert game.get_player_count() == 4


@pytest.mark.asyncio
async def test_concurrent_join_same_game():
    """Test concurrent joins to same game."""
    manager = GameSessionManager()
    game = await manager.create_game("Test Game", max_players=4)

    # Try to join concurrently
    tasks = [
        manager.join_game(game.game_id, f"player{i}", f"Player{i}", "warrior")
        for i in range(10)
    ]

    results = await asyncio.gather(*tasks)

    # Should only accept max_players
    successful_joins = sum(1 for success, _ in results if success)
    assert successful_joins == 4


# ============================================================================
# Helper Method Tests
# ============================================================================

def test_get_player_count():
    """Test getting player count."""
    game = GameSession("game1", "Test Game")

    assert game.get_player_count() == 0


@pytest.mark.asyncio
async def test_get_player_names():
    """Test getting list of player names."""
    game = GameSession("game1", "Test Game")

    await game.add_player("p1", "Alice", "warrior")
    await game.add_player("p2", "Bob", "mage")

    names = game.get_player_names()

    assert len(names) == 2
    assert "Alice" in names
    assert "Bob" in names
