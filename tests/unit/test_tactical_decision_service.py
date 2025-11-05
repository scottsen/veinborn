"""
Unit tests for TacticalDecisionService.

Tests tactical decision-making with configuration.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.game import Game
from core.entities import Monster, OreVein, Forge
from tests.fuzz.services.perception_service import PerceptionService
from tests.fuzz.services.tactical_decision_service import (
    TacticalDecisionService,
    CombatConfig,
    MiningConfig
)


class TestHealthAssessment:
    """Tests for health assessment."""

    def test_is_low_health_respects_config(self):
        """Should use config threshold for health assessment."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Set player to 40% HP
        player.hp = 40
        player.max_hp = 100

        # Config with 50% threshold
        config = CombatConfig(health_threshold=0.5)
        perception = PerceptionService()
        decisions = TacticalDecisionService(perception, combat_config=config)

        result = decisions.is_low_health(game)

        assert result is True  # 40% < 50%

    def test_is_low_health_with_override(self):
        """Should allow threshold override."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Set player to 40% HP
        player.hp = 40
        player.max_hp = 100

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        # Override threshold to 30%
        result = decisions.is_low_health(game, threshold=0.3)

        assert result is False  # 40% > 30%

    def test_is_low_health_returns_true_when_zero_max_hp(self):
        """Should handle edge case of 0 max HP."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        player.hp = 0
        player.max_hp = 0

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.is_low_health(game)

        assert result is True


class TestCombatDecisions:
    """Tests for combat-related decisions."""

    def test_can_win_fight_uses_safety_margin(self):
        """Should apply safety margin to combat calculations."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.hp = 50
        player.max_hp = 50
        player.attack = 10
        player.defense = 5

        # Create even-matched monster
        monster = Monster(
            name="Test Monster",
            content_id="test",
            x=5, y=5,
            hp=30, max_hp=30,
            attack=10, defense=5
        )
        game.state.entities[1] = monster

        perception = PerceptionService()

        # With safety_margin=1.5 (default), should be cautious
        config_cautious = CombatConfig(safety_margin=1.5)
        decisions_cautious = TacticalDecisionService(perception, combat_config=config_cautious)
        result_cautious = decisions_cautious.can_win_fight(game, monster)

        # With safety_margin=1.0, should be more aggressive
        config_aggressive = CombatConfig(safety_margin=1.0)
        decisions_aggressive = TacticalDecisionService(perception, combat_config=config_aggressive)
        result_aggressive = decisions_aggressive.can_win_fight(game, monster)

        # Aggressive should be more willing to fight
        assert result_aggressive is True or result_cautious is False

    def test_should_fight_when_adjacent(self):
        """Should always fight when monster is adjacent (forced combat)."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5
        player.hp = 10  # Low health
        player.max_hp = 100

        # Add adjacent monster
        monster = Monster(
            name="Adjacent Goblin",
            content_id="goblin",
            x=6, y=6,  # Adjacent
            hp=30, max_hp=30,
            attack=10, defense=2
        )
        monster.is_alive = True
        game.state.entities[1] = monster

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.should_fight(game)

        assert result is True  # Must fight when adjacent

    def test_should_not_fight_when_low_health(self):
        """Should not initiate combat when low health."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 0, 0
        player.hp = 20  # Low health
        player.max_hp = 100

        # Add nearby (not adjacent) monster
        monster = Monster(
            name="Nearby Goblin",
            content_id="goblin",
            x=3, y=3,
            hp=10, max_hp=10,
            attack=5, defense=1
        )
        monster.is_alive = True
        game.state.entities[1] = monster

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.should_fight(game)

        assert result is False  # Low health, don't initiate combat

    def test_should_flee_when_low_health_and_monster_nearby(self):
        """Should flee when low health and monster is nearby."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 0, 0
        player.hp = 20  # Low health
        player.max_hp = 100

        # Add nearby monster
        monster = Monster(
            name="Nearby Orc",
            content_id="orc",
            x=3, y=3,
            hp=30, max_hp=30,
            attack=10, defense=3
        )
        monster.is_alive = True
        game.state.entities[1] = monster

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.should_flee(game)

        assert result is True

    def test_should_flee_when_cannot_win(self):
        """Should flee when unable to win fight."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 0, 0
        player.hp = 50  # Good health
        player.max_hp = 50
        player.attack = 3
        player.defense = 1

        # Add strong nearby monster
        monster = Monster(
            name="Strong Troll",
            content_id="troll",
            x=3, y=3,
            hp=100, max_hp=100,
            attack=20, defense=10
        )
        monster.is_alive = True
        game.state.entities[1] = monster

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.should_flee(game)

        assert result is True  # Can't win, should flee


class TestMiningDecisions:
    """Tests for mining-related decisions."""

    def test_should_mine_strategically_requires_survey(self):
        """Should not mine unsurveyed ore."""
        game = Game()
        game.start_new_game()

        ore = OreVein(ore_type="iron", content_id="iron", x=5, y=5)
        ore.set_stat('surveyed', False)

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.should_mine_strategically(game, ore)

        assert result is False

    def test_should_mine_strategically_always_mines_legacy_quality(self):
        """Should always mine 80+ purity ore (Legacy Vault quality)."""
        game = Game()
        game.start_new_game()

        ore = OreVein(ore_type="mithril", content_id="mithril", x=5, y=5)
        ore.set_stat('surveyed', True)
        ore.set_stat('purity', 85)

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.should_mine_strategically(game, ore)

        assert result is True

    def test_should_mine_strategically_respects_min_purity_config(self):
        """Should use min_purity from config."""
        game = Game()
        game.start_new_game()
        player = game.state.player
        player.hp = 50
        player.max_hp = 50  # Good health

        ore = OreVein(ore_type="iron", content_id="iron", x=5, y=5)
        ore.set_stat('surveyed', True)
        ore.set_stat('purity', 65)

        perception = PerceptionService()

        # Config with min_purity=70 (default)
        config_high = MiningConfig(min_purity=70)
        decisions_high = TacticalDecisionService(perception, mining_config=config_high)
        result_high = decisions_high.should_mine_strategically(game, ore)

        # Config with min_purity=50 (lower standard)
        config_low = MiningConfig(min_purity=50)
        decisions_low = TacticalDecisionService(perception, mining_config=config_low)
        result_low = decisions_low.should_mine_strategically(game, ore)

        assert result_high is False  # 65 < 70
        assert result_low is True    # 65 >= 50

    def test_should_not_mine_when_low_health(self):
        """Should not mine non-legacy ore when low health."""
        game = Game()
        game.start_new_game()
        player = game.state.player
        player.hp = 20  # Low health
        player.max_hp = 100

        ore = OreVein(ore_type="iron", content_id="iron", x=5, y=5)
        ore.set_stat('surveyed', True)
        ore.set_stat('purity', 75)

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.should_mine_strategically(game, ore)

        assert result is False

    def test_should_survey_ore_respects_distance_config(self):
        """Should use max_survey_distance from config."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5

        # Add ore at distance 1.5
        ore = OreVein(ore_type="iron", content_id="iron", x=6, y=6)
        ore.set_stat('surveyed', False)
        game.state.entities[1] = ore

        perception = PerceptionService()

        # Config with max_survey_distance=2.0 (should find)
        config_far = MiningConfig(max_survey_distance=2.0)
        decisions_far = TacticalDecisionService(perception, mining_config=config_far)
        result_far = decisions_far.should_survey_ore(game)

        # Config with max_survey_distance=1.0 (should not find)
        config_near = MiningConfig(max_survey_distance=1.0)
        decisions_near = TacticalDecisionService(perception, mining_config=config_near)
        result_near = decisions_near.should_survey_ore(game)

        assert result_far is not None
        assert result_near is None


class TestProgressionDecisions:
    """Tests for progression-related decisions."""

    def test_should_descend_when_on_stairs_and_floor_cleared(self):
        """Should descend when standing on stairs and floor is cleared."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player

        # Move player to stairs
        stairs_pos = game.state.dungeon_map.find_stairs_down()
        if stairs_pos:
            player.x, player.y = stairs_pos

            perception = PerceptionService()
            decisions = TacticalDecisionService(perception)

            result = decisions.should_descend(game)

            assert result is True

    def test_should_not_descend_when_not_on_stairs(self):
        """Should not descend when not standing on stairs."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5  # Not on stairs

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.should_descend(game)

        assert result is False

    def test_should_descend_with_good_health_despite_monsters(self):
        """Should descend with good health even if monsters remain (unreachable)."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.hp = 60  # Good health
        player.max_hp = 100

        # Move to stairs
        stairs_pos = game.state.dungeon_map.find_stairs_down()
        if stairs_pos:
            player.x, player.y = stairs_pos

            # Add unreachable monster
            monster = Monster(
                name="Unreachable Goblin",
                content_id="goblin",
                x=25, y=25,
                hp=10, max_hp=10,
                attack=5, defense=1
            )
            monster.is_alive = True
            game.state.entities[1] = monster

            perception = PerceptionService()
            decisions = TacticalDecisionService(perception)

            result = decisions.should_descend(game)

            assert result is True  # Good health allows descending


class TestCraftingDecisions:
    """Tests for crafting-related decisions."""

    def test_should_not_craft_when_low_health(self):
        """Should not craft when health is low."""
pytestmark = pytest.mark.unit

        game = Game()
        game.start_new_game()

        player = game.state.player
        player.hp = 20  # Low health
        player.max_hp = 100

        perception = PerceptionService()
        decisions = TacticalDecisionService(perception)

        result = decisions.should_craft(game)

        assert result is False

    def test_should_not_craft_when_adjacent_to_monster(self):
        """Should not craft when monster is adjacent."""
        game = Game()
        game.start_new_game()
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5
        player.hp = 100  # Good health
        player.max_hp = 100

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

        result = decisions.should_craft(game)

        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
