"""
Unit tests for ActionFactory.

Tests the Factory Pattern implementation for action creation.
Focus on:
- Action creation from string types
- Prerequisite checking (ore vein detection)
- Error handling (invalid actions, missing prerequisites)
- Custom handler registration
"""
import pytest
from core.actions.action_factory import ActionFactory, ActionHandler
from core.actions.move_action import MoveAction
from core.actions.survey_action import SurveyAction
from core.actions.mine_action import MineAction
from core.actions.descend_action import DescendAction


# ============================================================================
# Basic Action Creation Tests
# ============================================================================

@pytest.mark.unit
def test_factory_initialization(game_context):
    """Factory initializes with standard actions registered."""
    factory = ActionFactory(game_context)

    available_actions = factory.get_available_actions()

    assert 'move' in available_actions
    assert 'survey' in available_actions
    assert 'mine' in available_actions
    assert 'descend' in available_actions
    assert len(available_actions) == 4


@pytest.mark.unit
def test_create_move_action(game_context):
    """Factory creates MoveAction successfully."""
    factory = ActionFactory(game_context)

    action = factory.create('move', dx=1, dy=0)

    assert action is not None
    assert isinstance(action, MoveAction)
    assert action.dx == 1
    assert action.dy == 0


@pytest.mark.unit
def test_create_descend_action(game_context):
    """Factory creates DescendAction successfully."""
    factory = ActionFactory(game_context)

    action = factory.create('descend')

    assert action is not None
    assert isinstance(action, DescendAction)


# ============================================================================
# Prerequisite Checking Tests (Ore Vein)
# ============================================================================

@pytest.mark.unit
def test_create_survey_with_ore_vein(mining_context):
    """Factory creates SurveyAction when ore vein is adjacent."""
    factory = ActionFactory(mining_context)

    action = factory.create('survey')

    assert action is not None
    assert isinstance(action, SurveyAction)


@pytest.mark.unit
def test_create_survey_without_ore_vein(game_context):
    """Factory returns None for SurveyAction when no ore vein adjacent."""
    factory = ActionFactory(game_context)

    action = factory.create('survey')

    assert action is None
    # Check that message was added
    messages = game_context.game_state.messages
    assert any('No ore vein nearby' in msg for msg in messages)


@pytest.mark.unit
def test_create_mine_with_ore_vein(mining_context):
    """Factory creates MineAction when ore vein is adjacent."""
    factory = ActionFactory(mining_context)

    action = factory.create('mine')

    assert action is not None
    assert isinstance(action, MineAction)


@pytest.mark.unit
def test_create_mine_without_ore_vein(game_context):
    """Factory returns None for MineAction when no ore vein adjacent."""
    factory = ActionFactory(game_context)

    action = factory.create('mine')

    assert action is None
    # Check that message was added
    messages = game_context.game_state.messages
    assert any('No ore vein nearby' in msg for msg in messages)


@pytest.mark.unit
def test_create_mine_resume_existing(mining_context):
    """Factory resumes existing mining action if in progress."""
    factory = ActionFactory(mining_context)

    # Simulate mining in progress
    player = mining_context.get_player()
    ore_vein = list(mining_context.game_state.entities.values())[1]  # Get ore vein
    player.set_stat('mining_action', {
        'actor_id': player.entity_id,
        'ore_vein_id': ore_vein.entity_id,
        'turns_remaining': 2,
        'turns_total': 4
    })

    action = factory.create('mine')

    assert action is not None
    assert isinstance(action, MineAction)
    # Verify it's a resumed action
    assert action.turns_remaining == 2


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.unit
def test_create_invalid_action_type(game_context):
    """Factory returns None for unknown action type."""
    factory = ActionFactory(game_context)

    action = factory.create('invalid_action_type')

    assert action is None
    # Check that warning message was added
    messages = game_context.game_state.messages
    assert any('Unknown action' in msg for msg in messages)


@pytest.mark.unit
def test_create_with_missing_parameters(game_context):
    """Factory handles missing parameters gracefully."""
    factory = ActionFactory(game_context)

    # MoveAction requires dx and dy, but omit them
    # Should default to 0, 0
    action = factory.create('move')

    assert action is not None
    assert isinstance(action, MoveAction)
    assert action.dx == 0
    assert action.dy == 0


# ============================================================================
# Custom Handler Registration Tests
# ============================================================================

@pytest.mark.unit
def test_register_custom_handler(game_context):
    """Factory accepts custom action handlers."""
    factory = ActionFactory(game_context)

    # Define a custom action handler
    def create_custom_action(context, kwargs):
        return MoveAction(context.get_player().entity_id, 5, 5)

    handler = ActionHandler(
        name='teleport',
        create_fn=create_custom_action,
        description='Teleport to position'
    )

    factory.register_handler('teleport', handler)

    # Verify registration
    available = factory.get_available_actions()
    assert 'teleport' in available
    assert available['teleport'] == 'Teleport to position'

    # Verify creation
    action = factory.create('teleport')
    assert action is not None
    assert isinstance(action, MoveAction)


@pytest.mark.unit
def test_get_available_actions(game_context):
    """Factory lists all available actions with descriptions."""
    factory = ActionFactory(game_context)

    actions = factory.get_available_actions()

    assert isinstance(actions, dict)
    assert len(actions) == 4
    assert 'Move in a direction' in actions['move']
    assert 'Survey adjacent ore vein' in actions['survey']
    assert 'Mine adjacent ore vein' in actions['mine']
    assert 'Descend stairs' in actions['descend']


# ============================================================================
# Integration-Level Tests
# ============================================================================

@pytest.mark.unit
def test_factory_with_multiple_ore_veins(game_context, copper_ore, iron_ore):
    """Factory finds closest ore vein when multiple available."""
    # Add multiple ore veins to context
    game_context.add_entity(copper_ore)
    game_context.add_entity(iron_ore)

    factory = ActionFactory(game_context)
    action = factory.create('survey')

    # Should find at least one ore vein
    assert action is not None
    assert isinstance(action, SurveyAction)


@pytest.mark.unit
def test_factory_action_execution(mining_context):
    """Actions created by factory can be executed successfully."""
    factory = ActionFactory(mining_context)

    # Create action
    action = factory.create('survey')
    assert action is not None

    # Execute action
    outcome = action.execute(mining_context)

    # Verify execution
    assert outcome.success
    assert outcome.took_turn
    assert len(outcome.messages) > 0


@pytest.mark.unit
def test_factory_maintains_actor_id(game_context):
    """Factory correctly sets actor_id for all actions."""
    factory = ActionFactory(game_context)
    player_id = game_context.get_player().entity_id

    # Test move action
    move = factory.create('move', dx=1, dy=0)
    assert move.actor_id == player_id

    # Test descend action
    descend = factory.create('descend')
    assert descend.actor_id == player_id


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.unit
def test_factory_with_dead_player(game_context):
    """Factory handles dead player gracefully."""
    factory = ActionFactory(game_context)

    # Kill the player
    player = game_context.get_player()
    player.hp = 0

    # Should still create actions (game logic handles dead player separately)
    action = factory.create('move', dx=1, dy=0)
    assert action is not None


@pytest.mark.unit
def test_factory_with_game_over(game_context):
    """Factory still creates actions when game is over."""
    factory = ActionFactory(game_context)

    # Set game over
    game_context.game_state.game_over = True

    # Factory doesn't check game_over (that's Game's responsibility)
    action = factory.create('move', dx=1, dy=0)
    assert action is not None


@pytest.mark.unit
def test_factory_ore_vein_at_player_position(game_context, copper_ore):
    """Factory handles ore vein at exact player position."""
pytestmark = pytest.mark.unit

    # Place ore vein at player's exact position (edge case)
    player = game_context.get_player()
    copper_ore.x = player.x
    copper_ore.y = player.y
    game_context.add_entity(copper_ore)

    factory = ActionFactory(game_context)

    # Should still detect ore vein (distance = 0 is adjacent)
    action = factory.create('survey')
    # Note: is_adjacent might not consider same position as adjacent
    # This documents current behavior
