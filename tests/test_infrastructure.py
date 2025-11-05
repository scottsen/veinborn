"""Infrastructure smoke tests to verify test framework is working.

This file contains basic tests to ensure pytest, fixtures, and configuration
are working correctly.
"""
import pytest


@pytest.mark.smoke
def test_pytest_is_working():
    """Verify pytest can run tests."""
    assert True


@pytest.mark.smoke
def test_fixtures_are_available(fresh_player, weak_goblin, copper_ore):
    """Verify conftest.py fixtures are available."""
    # Test player fixture
    assert fresh_player is not None
    assert fresh_player.name == "Player"  # Default name
    assert fresh_player.hp == 20

    # Test monster fixture
    assert weak_goblin is not None
    assert weak_goblin.name == "Goblin"
    assert weak_goblin.hp == 5

    # Test ore fixture
    assert copper_ore is not None
    assert copper_ore.ore_type == "copper"
    assert copper_ore.get_stat('hardness') == 50


@pytest.mark.smoke
def test_game_state_fixture(simple_game_state):
    """Verify GameState fixture works."""
    assert simple_game_state is not None
    assert simple_game_state.player is not None
    assert len(simple_game_state.entities) == 1
    assert simple_game_state.turn_count == 0
    assert not simple_game_state.game_over


@pytest.mark.smoke
def test_new_game_fixture(new_game):
    """Verify new game fixture creates a playable game."""
    assert new_game is not None
    assert new_game.state is not None
    assert new_game.state.player is not None
    assert new_game.state.dungeon_map is not None
    # Should have player + monsters + ore veins
    assert len(new_game.state.entities) > 1


@pytest.mark.smoke
def test_context_fixtures_available(game_context, combat_context, mining_context):
    """Verify all GameContext fixtures are available."""
    assert game_context is not None
    assert combat_context is not None
    assert mining_context is not None


# Test that markers are working
@pytest.mark.unit
def test_unit_marker():
    """Test that unit marker works."""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """Test that integration marker works."""
    assert True


@pytest.mark.slow
def test_slow_marker():
    """Test that slow marker works."""
    import time
    time.sleep(0.001)  # Simulate slow operation
    assert True
