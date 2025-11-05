"""
Unit tests for perception.

Tests pure perception functions that query game state without making decisions.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.game import Game
from core.entities import Monster, OreVein, Forge
from core.base.entity import Entity
from tests.fuzz.services.perception_service import PerceptionService, ThreatLevel


@pytest.fixture
def perception():
    """Create PerceptionService instance for tests."""
    return PerceptionService()


class TestMonsterPerception:
    """Tests for monster-related perception."""

    def test_find_monsters_returns_only_living(self, perception):
        """Should return only living monsters."""
        game = Game()
        game.start_new_game()

        # Clear existing entities
        game.state.entities.clear()

        # Add a living monster
        monster1 = Monster(
            name="Goblin",
            content_id="goblin",
            x=5, y=5,
            hp=6, max_hp=6,
            attack=3, defense=1
        )
        monster1.is_alive = True
        game.state.entities[1] = monster1

        # Add a dead monster
        monster2 = Monster(
            name="Dead Orc",
            content_id="orc",
            x=10, y=10,
            hp=0, max_hp=12,
            attack=5, defense=2
        )
        monster2.is_alive = False
        game.state.entities[2] = monster2

        perception = PerceptionService()
        monsters = perception.find_monsters(game)

        assert len(monsters) == 1
        assert monsters[0].name == "Goblin"
        assert monsters[0].is_alive

    def test_find_nearest_monster_returns_closest(self, perception):
        """Should return the closest living monster."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Place player at origin
        player.x, player.y = 0, 0

        # Add nearby monster
        near_monster = Monster(
            name="Near Goblin",
            content_id="goblin",
            x=2, y=2,
            hp=6, max_hp=6,
            attack=3, defense=1
        )
        near_monster.is_alive = True
        game.state.entities[1] = near_monster

        # Add far monster
        far_monster = Monster(
            name="Far Orc",
            content_id="orc",
            x=10, y=10,
            hp=12, max_hp=12,
            attack=5, defense=2
        )
        far_monster.is_alive = True
        game.state.entities[2] = far_monster

        nearest = perception.find_nearest_monster(game)

        assert nearest is not None
        assert nearest.name == "Near Goblin"

    def test_find_nearest_monster_returns_none_when_empty(self, perception):
        """Should return None when no monsters exist."""
        game = Game()
        game.start_new_game()

        # Clear all entities
        game.state.entities.clear()

        nearest = perception.find_nearest_monster(game)

        assert nearest is None

    def test_monster_in_view_returns_monster_within_range(self, perception):
        """Should return monster within viewing distance."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Place player at origin
        player.x, player.y = 0, 0

        # Add monster within view (distance 5)
        monster = Monster(
            name="Visible Goblin",
            content_id="goblin",
            x=3, y=4,  # Distance = 5
            hp=6, max_hp=6,
            attack=3, defense=1
        )
        monster.is_alive = True
        game.state.entities[1] = monster

        result = perception.monster_in_view(game, distance=10.0)

        assert result is not None
        assert result.name == "Visible Goblin"

    def test_monster_in_view_returns_none_when_out_of_range(self, perception):
        """Should return None when monster is too far."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Place player at origin
        player.x, player.y = 0, 0

        # Add monster far away
        monster = Monster(
            name="Far Goblin",
            content_id="goblin",
            x=20, y=20,
            hp=6, max_hp=6,
            attack=3, defense=1
        )
        monster.is_alive = True
        game.state.entities[1] = monster

        result = perception.monster_in_view(game, distance=5.0)

        assert result is None

    def test_is_adjacent_to_monster_handles_diagonals(self, perception):
        """Should correctly detect adjacency including diagonals."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Place player at (5, 5)
        player.x, player.y = 5, 5

        # Add diagonal monster at (6, 6) - adjacent!
        monster = Monster(
            name="Diagonal Goblin",
            content_id="goblin",
            x=6, y=6,
            hp=6, max_hp=6,
            attack=3, defense=1
        )
        monster.is_alive = True
        game.state.entities[1] = monster

        result = perception.is_adjacent_to_monster(game)

        assert result is not None
        assert result.name == "Diagonal Goblin"

    def test_is_adjacent_to_monster_returns_none_when_not_adjacent(self, perception):
        """Should return None when monster is not adjacent."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Place player at (5, 5)
        player.x, player.y = 5, 5

        # Add non-adjacent monster at (10, 10)
        monster = Monster(
            name="Far Goblin",
            content_id="goblin",
            x=10, y=10,
            hp=6, max_hp=6,
            attack=3, defense=1
        )
        monster.is_alive = True
        game.state.entities[1] = monster

        result = perception.is_adjacent_to_monster(game)

        assert result is None


class TestOrePerception:
    """Tests for ore-related perception."""

    def test_find_adjacent_ore_returns_ore_when_diagonal(self, perception):
        """Should find ore at diagonal position (tests adjacency bug fix)."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Place player at (5, 5)
        player.x, player.y = 5, 5

        # Add diagonal ore at (6, 6) - adjacent!
        ore = OreVein(
            ore_type="iron",
            content_id="iron",
            x=6, y=6
        )
        game.state.entities[1] = ore

        result = perception.find_adjacent_ore(game)

        assert result is not None
        assert result.ore_type == "iron"

    def test_find_adjacent_ore_returns_none_when_not_adjacent(self, perception):
        """Should return None when ore is not adjacent."""
        game = Game()
        game.start_new_game()

        # Clear existing entities
        game.state.entities.clear()

        player = game.state.player

        # Place player at (5, 5)
        player.x, player.y = 5, 5

        # Add ore at (10, 10) - not adjacent
        ore = OreVein(
            ore_type="iron",
            content_id="iron",
            x=10, y=10
        )
        game.state.entities[1] = ore

        result = perception.find_adjacent_ore(game)

        assert result is None

    def test_find_valuable_ore_prioritizes_legacy_quality(self, perception):
        """Should prioritize 80+ purity ore (Legacy Vault quality)."""
        game = Game()
        game.start_new_game()
        player = game.state.player
        player.x, player.y = 5, 5

        # Add medium-quality ore (closer)
        medium_ore = OreVein(ore_type="iron", content_id="iron", x=6, y=6)
        medium_ore.set_stat('surveyed', True)
        medium_ore.set_stat('purity', 70)
        game.state.entities[1] = medium_ore

        # Add Legacy-quality ore (farther)
        legacy_ore = OreVein(ore_type="mithril", content_id="mithril", x=10, y=10)
        legacy_ore.set_stat('surveyed', True)
        legacy_ore.set_stat('purity', 85)
        game.state.entities[2] = legacy_ore

        result = perception.find_valuable_ore(game)

        assert result is not None
        assert result.ore_type == "mithril"
        assert result.get_stat('purity') == 85

    def test_find_jackpot_ore_requires_all_properties_high(self, perception):
        """Should only return ore with ALL properties 80+."""
        game = Game()
        game.start_new_game()

        # Add jackpot ore (all properties 80+)
        jackpot = OreVein(ore_type="adamantite", content_id="adamantite", x=5, y=5)
        jackpot.set_stat('surveyed', True)
        jackpot.set_stat('hardness', 90)
        jackpot.set_stat('conductivity', 85)
        jackpot.set_stat('malleability', 88)
        jackpot.set_stat('purity', 92)
        jackpot.set_stat('density', 87)
        game.state.entities[1] = jackpot

        # Add non-jackpot ore (one property too low)
        normal_ore = OreVein(ore_type="mithril", content_id="mithril", x=10, y=10)
        normal_ore.set_stat('surveyed', True)
        normal_ore.set_stat('hardness', 90)
        normal_ore.set_stat('conductivity', 85)
        normal_ore.set_stat('malleability', 70)  # Too low!
        normal_ore.set_stat('purity', 92)
        normal_ore.set_stat('density', 87)
        game.state.entities[2] = normal_ore

        result = perception.find_jackpot_ore(game)

        assert result is not None
        assert result.ore_type == "adamantite"

    def test_find_unsurveyed_ore_nearby_respects_distance(self, perception):
        """Should only return unsurveyed ore within max_distance."""
        game = Game()
        game.start_new_game()

        # Clear existing entities
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 5, 5

        # Add nearby unsurveyed ore
        near_ore = OreVein(ore_type="iron", content_id="iron", x=6, y=6)
        near_ore.set_stat('surveyed', False)
        game.state.entities[1] = near_ore

        # Add far unsurveyed ore
        far_ore = OreVein(ore_type="mithril", content_id="mithril", x=20, y=20)
        far_ore.set_stat('surveyed', False)
        game.state.entities[2] = far_ore

        result = perception.find_unsurveyed_ore_nearby(game, max_distance=3.0)

        assert result is not None
        # Check it's the near ore by position (ore_type might default)
        assert result.x == 6 and result.y == 6


class TestEnvironmentPerception:
    """Tests for environment-related perception."""

    def test_on_stairs_returns_true_when_on_stairs(self, perception):
        """Should detect when player is standing on stairs."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Find stairs and move player there
        stairs_pos = game.state.dungeon_map.find_stairs_down()
        if stairs_pos:
            player.x, player.y = stairs_pos

            result = perception.on_stairs(game)

            assert result is True

    def test_on_stairs_returns_false_when_not_on_stairs(self, perception):
        """Should return False when player is not on stairs."""
        game = Game()
        game.start_new_game()
        player = game.state.player

        # Move player away from stairs
        player.x, player.y = 5, 5

        result = perception.on_stairs(game)

        assert result is False


class TestThreatAssessment:
    """Tests for threat assessment."""

    def test_assess_threat_returns_trivial_for_goblins(self, perception):
        """Goblins should be classified as trivial threat."""
        threat_rankings = {'goblin': 18.0}  # 6*3/1 = 18

        monster = Monster(
            name="Goblin",
            content_id="goblin",
            x=5, y=5,
            hp=6, max_hp=6,
            attack=3, defense=1
        )

        result = perception.assess_threat(monster, threat_rankings)

        assert result == ThreatLevel.TRIVIAL

    def test_assess_threat_returns_manageable_for_orcs(self, perception):
        """Orcs should be classified as manageable threat."""
        threat_rankings = {'orc': 30.0}  # 12*5/2 = 30

        monster = Monster(
            name="Orc",
            content_id="orc",
            x=5, y=5,
            hp=12, max_hp=12,
            attack=5, defense=2
        )

        result = perception.assess_threat(monster, threat_rankings)

        assert result == ThreatLevel.MANAGEABLE

    def test_assess_threat_returns_dangerous_for_trolls(self, perception):
        """Trolls should be classified as dangerous threat."""
        threat_rankings = {'troll': 150.0}  # Adjusted to be in dangerous range

        monster = Monster(
            name="Troll",
            content_id="troll",
            x=5, y=5,
            hp=20, max_hp=20,
            attack=7, defense=3
        )

        result = perception.assess_threat(monster, threat_rankings)

        assert result == ThreatLevel.DANGEROUS

    def test_assess_threat_returns_deadly_for_bosses(self, perception):
        """Boss monsters should be classified as deadly threat."""
        threat_rankings = {'dragon': 500.0}

        monster = Monster(
            name="Dragon",
            content_id="dragon",
            x=5, y=5,
            hp=100, max_hp=100,
            attack=20, defense=4
        )

        result = perception.assess_threat(monster, threat_rankings)

        assert result == ThreatLevel.DEADLY

    def test_assess_threat_returns_unknown_for_no_intelligence(self, perception):
        """Monsters without intelligence data should be unknown."""
        threat_rankings = {}

        monster = Monster(
            name="Mystery",
            content_id=None,
            x=5, y=5,
            hp=10, max_hp=10,
            attack=5, defense=2
        )

        result = perception.assess_threat(monster, threat_rankings)

        assert result == ThreatLevel.UNKNOWN


class TestCraftingPerception:
    """Tests for crafting-related perception."""

    def test_find_forges_returns_all_forges(self, perception):
        """Should return all forges in the game."""
        game = Game()
        game.start_new_game()

        # Clear existing entities
        game.state.entities.clear()

        # Add forges
        forge1 = Forge(name="Forge 1", content_id="forge", x=5, y=5)
        forge2 = Forge(name="Forge 2", content_id="forge", x=10, y=10)
        game.state.entities[1] = forge1
        game.state.entities[2] = forge2

        forges = perception.find_forges(game)

        assert len(forges) == 2

    def test_find_nearest_forge_returns_closest(self, perception):
        """Should return the closest forge."""
        game = Game()
        game.start_new_game()

        # Clear existing entities
        game.state.entities.clear()

        player = game.state.player
        player.x, player.y = 0, 0

        # Add near forge
        near_forge = Forge(name="Near Forge", content_id="forge", x=2, y=2)
        game.state.entities[1] = near_forge

        # Add far forge
        far_forge = Forge(name="Far Forge", content_id="forge", x=20, y=20)
        game.state.entities[2] = far_forge

        result = perception.find_nearest_forge(game)

        assert result is not None
        # Check it's the near forge by position (not name, as Forge may override)
        assert result.x == 2 and result.y == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
