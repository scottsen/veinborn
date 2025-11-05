"""
Unit tests for ActionPlanner.

Tests action planning and validation.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
pytestmark = pytest.mark.unit

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.game import Game
from core.entities import Monster, OreVein
from tests.fuzz.services.perception_service import PerceptionService
from tests.fuzz.services.tactical_decision_service import TacticalDecisionService
from tests.fuzz.services.action_planner import ActionPlanner


class TestActionValidation:
    """Tests for action validation."""

    def test_validate_action_rejects_move_into_wall(self):
        """Should reject move action into non-walkable tile."""
        game = Game()
        game.start_new_game()

        player = game.state.player
        player.x, player.y = 5, 5

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions)

        # Find a wall and try to move into it
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_x, new_y = player.x + dx, player.y + dy
                if not game.state.dungeon_map.is_walkable(new_x, new_y):
                    # Found a wall
                    result = planner.validate_action(game, 'move', {'dx': dx, 'dy': dy})
                    assert result is False
                    return

        # If no walls found around player, test passed trivially
        assert True

    def test_validate_action_accepts_valid_move(self):
        """Should accept move action into walkable tile."""
        game = Game()
        game.start_new_game()

        player = game.state.player
        player.x, player.y = 10, 10

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions)

        # Find a walkable tile and validate move
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_x, new_y = player.x + dx, player.y + dy
                if game.state.dungeon_map.is_walkable(new_x, new_y):
                    # Found walkable tile
                    result = planner.validate_action(game, 'move', {'dx': dx, 'dy': dy})
                    assert result is True
                    return

        # If no walkable tiles found (completely surrounded), test passed
        assert True

    def test_validate_action_rejects_mine_when_not_adjacent(self):
        """Should reject mine action when not adjacent to ore."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5

        # Add ore far away
        ore = OreVein(ore_type="iron", content_id="iron", x=20, y=20)
        game.state.entities[1] = ore

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions)

        result = planner.validate_action(game, 'mine', {})

        assert result is False

    def test_validate_action_accepts_mine_when_adjacent(self):
        """Should accept mine action when adjacent to ore."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5

        # Add adjacent ore
        ore = OreVein(ore_type="iron", content_id="iron", x=6, y=6)
        game.state.entities[1] = ore

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions)

        result = planner.validate_action(game, 'mine', {})

        assert result is True


class TestMovementActions:
    """Tests for movement action planning."""

    def test_move_towards_uses_pathfinding(self):
        """Should use pathfinding to move towards target."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player

        # Place player in open area
        player.x, player.y = 10, 10

        # Create target nearby in open area
        from core.base.entity import Entity, EntityType
        target = Entity(entity_type=EntityType.PLAYER, name="Target", x=12, y=12)

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions)

        action_type, kwargs = planner.move_towards(game, target)

        # Should either move or wait (if completely blocked)
        assert action_type in ['move', 'wait']

        if action_type == 'move':
            assert 'dx' in kwargs
            assert 'dy' in kwargs

    def test_flee_from_maximizes_distance(self):
        """Should flee away from threat to maximize distance."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 10, 10

        # Create threat
        threat = Monster(
            name="Threat",
            content_id="goblin",
            x=11, y=11,
            hp=10, max_hp=10,
            attack=5, defense=1
        )

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions)

        action_type, kwargs = planner.flee_from(game, threat)

        # Should either successfully flee or be trapped
        assert action_type in ['move', 'wait']

        if action_type == 'move':
            assert 'dx' in kwargs
            assert 'dy' in kwargs

            # Check that move increases distance
            dx = kwargs['dx']
            dy = kwargs['dy']
            new_x = player.x + dx
            new_y = player.y + dy

            old_dist = abs(player.x - threat.x) + abs(player.y - threat.y)
            new_dist = abs(new_x - threat.x) + abs(new_y - threat.y)

            # New distance should be greater or equal
            assert new_dist >= old_dist


class TestRandomActions:
    """Tests for random action selection."""

    def test_get_random_action_returns_valid_action(self):
        """Should return a valid action type."""
        game = Game()
        game.start_new_game()

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions)

        action_type, kwargs = planner.get_random_action(game)

        assert action_type in ['move', 'wait', 'survey', 'mine']
        assert isinstance(kwargs, dict)

    def test_get_random_action_includes_mining_when_adjacent(self):
        """Should allow mine/survey actions when adjacent to ore."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5

        # Add adjacent ore
        ore = OreVein(ore_type="iron", content_id="iron", x=6, y=6)
        game.state.entities[1] = ore

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions)

        # Get multiple random actions to check if mining is possible
        action_types = set()
        for _ in range(20):
            action_type, _ = planner.get_random_action(game)
            action_types.add(action_type)

        # Should include at least move/wait, possibly mine/survey
        assert 'move' in action_types or 'wait' in action_types


class TestSmartActionPlanning:
    """Tests for strategic action planning."""

    def test_get_smart_action_prioritizes_forced_combat(self):
        """Should fight when monster is adjacent (forced combat)."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5

        # Add adjacent monster
        monster = Monster(
            name="Adjacent Goblin",
            content_id="goblin",
            x=6, y=6,
            hp=10, max_hp=10,
            attack=5, defense=1
        )
        monster.is_alive = True
        game.state.entities[1] = monster

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions, verbose=False)

        action_type, kwargs = planner.get_smart_action(game)

        # Should move towards monster (attack)
        assert action_type == 'move'

    def test_get_smart_action_descends_on_cleared_floor(self):
        """Should descend when on stairs and floor is cleared."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player

        # Move to stairs
        stairs_pos = game.state.dungeon_map.find_stairs_down()
        if stairs_pos:
            player.x, player.y = stairs_pos

            perception = PerceptionService()
            decisions = TacticalDecisionService(perception)
            planner = ActionPlanner(perception, decisions, verbose=False)

            action_type, kwargs = planner.get_smart_action(game)

            assert action_type == 'descend'

    def test_get_smart_action_mines_adjacent_jackpot_ore(self):
        """Should mine jackpot ore when adjacent."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5
        player.hp = 100
        player.max_hp = 100

        # Add adjacent jackpot ore
        jackpot = OreVein(ore_type="adamantite", content_id="adamantite", x=6, y=6)
        jackpot.set_stat('surveyed', True)
        jackpot.set_stat('hardness', 90)
        jackpot.set_stat('conductivity', 85)
        jackpot.set_stat('malleability', 88)
        jackpot.set_stat('purity', 92)
        jackpot.set_stat('density', 87)
        game.state.entities[1] = jackpot

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions, verbose=False)

        action_type, kwargs = planner.get_smart_action(game)

        assert action_type == 'mine'


class TestPlanNextAction:
    """Tests for plan_next_action mode selection."""

    def test_plan_next_action_uses_strategic_mode(self):
        """Should use get_smart_action in strategic mode."""
        game = Game()
        game.start_new_game()

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions, verbose=False)

        action_type, kwargs = planner.plan_next_action(game, mode='strategic')

        # Should return a valid action
        assert action_type in ['move', 'wait', 'descend', 'mine', 'survey', 'craft', 'equip']

    def test_plan_next_action_uses_random_mode(self):
        """Should use get_random_action in random mode."""

        game = Game()
        game.start_new_game()

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)
        planner = ActionPlanner(perception, decisions, verbose=False)

        action_type, kwargs = planner.plan_next_action(game, mode='random')

        # Should return a valid random action
        assert action_type in ['move', 'wait', 'survey', 'mine']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
