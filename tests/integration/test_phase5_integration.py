"""
Integration tests for Phase 5 systems (Config, Classes, High Scores).

Tests the complete flow from game start to high score recording.
"""


import tempfile
from pathlib import Path
import pytest

from src.core.game import Game
from src.core.character_class import CharacterClass
from src.core.highscore import HighScoreManager, HighScoreEntry
from src.core.config.user_config import ConfigManager


pytestmark = pytest.mark.integration

class TestGameStartIntegration:
    """Test game start with player name and character class."""

    def setup_method(self):
        """Reset singletons before each test."""
        ConfigManager.reset()
        HighScoreManager.reset()

    def test_game_start_with_warrior_class(self):
        """Game starts with warrior class and correct stats."""
        game = Game()
        game.start_new_game(
            seed="test_seed",
            player_name="TestWarrior",
            character_class=CharacterClass.WARRIOR
        )

        # Check player was created correctly
        assert game.state.player is not None
        assert game.state.player.hp == 30  # Warrior starting HP
        assert game.state.player.max_hp == 30
        assert game.state.player.attack == 5  # Warrior attack
        assert game.state.player.defense == 3  # Warrior defense

        # Check player name stored
        assert game.state.player_name == "TestWarrior"

        # Check class stored in stats
        assert game.state.player.stats.get('class') == "Warrior"
        # Name is stored in entity.name, not stats
        assert game.state.player.name == "TestWarrior"

    def test_game_start_with_rogue_class(self):
        """Game starts with rogue class and correct stats."""
        game = Game()
        game.start_new_game(
            seed="test_seed",
            player_name="TestRogue",
            character_class=CharacterClass.ROGUE
        )

        # Check rogue stats
        assert game.state.player.hp == 20  # Rogue starting HP
        assert game.state.player.attack == 4
        assert game.state.player.defense == 2

        # Check class stored
        assert game.state.player.stats.get('class') == "Rogue"

    def test_game_start_with_mage_class(self):
        """Game starts with mage class and correct stats."""
        game = Game()
        game.start_new_game(
            seed="test_seed",
            player_name="TestMage",
            character_class=CharacterClass.MAGE
        )

        # Check mage stats
        assert game.state.player.hp == 15  # Mage starting HP
        assert game.state.player.attack == 2
        assert game.state.player.defense == 1

        # Check class stored
        assert game.state.player.stats.get('class') == "Mage"

    def test_game_start_without_class_uses_defaults(self):
        """Game starts without class uses default stats."""
        game = Game()
        game.start_new_game(
            seed="test_seed",
            player_name="TestPlayer",
            character_class=None
        )

        # Check default stats (from constants)
        assert game.state.player.hp == 20  # PLAYER_STARTING_HP
        assert game.state.player.attack == 5  # PLAYER_STARTING_ATTACK
        assert game.state.player.defense == 2  # PLAYER_STARTING_DEFENSE

        # No class stored
        assert 'class' not in game.state.player.stats or game.state.player.stats.get('class') is None

    def test_game_start_with_seed_is_reproducible(self):
        """Same seed produces same dungeon."""
        game1 = Game()
        game1.start_new_game(
            seed="reproducible_seed",
            player_name="Player1",
            character_class=CharacterClass.WARRIOR
        )

        game2 = Game()
        game2.start_new_game(
            seed="reproducible_seed",
            player_name="Player2",
            character_class=CharacterClass.WARRIOR
        )

        # Player positions should be same (same dungeon layout)
        assert game1.state.player.x == game2.state.player.x
        assert game1.state.player.y == game2.state.player.y

        # Seed stored correctly
        assert game1.state.seed == "reproducible_seed"
        assert game2.state.seed == "reproducible_seed"


class TestHighScoreIntegration:
    """Test high score recording on game over."""

    def setup_method(self):
        """Reset singletons and use temp file for high scores."""
        ConfigManager.reset()
        HighScoreManager.reset()

        # Use temporary file for high scores
        self.temp_dir = tempfile.mkdtemp()
        self.highscore_path = Path(self.temp_dir) / "test_highscores.json"

    def test_high_score_recorded_on_player_death(self):
        """High score is recorded when player dies."""
        # Create game with test high score path
        hsm = HighScoreManager.get_instance(filepath=self.highscore_path)

        game = Game()
        game.start_new_game(
            seed="death_test",
            player_name="DeadPlayer",
            character_class=CharacterClass.WARRIOR
        )

        # Simulate game progress
        game.state.turn_count = 100
        game.state.current_floor = 5
        game.state.player.stats['monsters_killed'] = 10
        game.state.player.stats['ore_mined'] = 5

        # Kill player
        game.state.player.take_damage(1000)
        assert not game.state.player.is_alive

        # Process turn (should record high score)
        game.turn_processor.process_turn()

        # Check high score was recorded
        scores = hsm.get_all_scores(10)
        assert len(scores) > 0

        # Verify score data
        entry = scores[0]
        assert entry.player_name == "DeadPlayer"
        assert entry.floor_reached == 5
        # Turn count is incremented before recording (100 + 1 = 101)
        assert entry.turns_survived == 101
        assert entry.monsters_killed == 10
        assert entry.ore_mined == 5
        assert entry.victory is False

    def test_high_score_recorded_on_victory(self):
        """High score is recorded when player wins with victory bonus."""
        hsm = HighScoreManager.get_instance(filepath=self.highscore_path)

        game = Game()
        game.start_new_game(
            seed="victory_test",
            player_name="VictoriousPlayer",
            character_class=CharacterClass.MAGE
        )

        # Simulate progression to victory floor
        game.state.turn_count = 500
        game.state.current_floor = 99  # Almost at victory
        game.state.player.stats['monsters_killed'] = 50
        game.state.player.stats['ore_mined'] = 25

        # Trigger victory (try to descend to floor 100)
        game.floor_manager.descend_floor()

        # Check victory
        assert game.state.victory is True
        assert game.state.game_over is True

        # Check high score was recorded with victory bonus
        scores = hsm.get_all_scores(10)
        assert len(scores) > 0

        entry = scores[0]
        assert entry.player_name == "VictoriousPlayer"
        assert entry.victory is True
        # Victory adds 50,000 points
        assert entry.score >= 50000

    def test_multiple_high_scores_ranked_correctly(self):
        """Multiple games create correctly ranked high scores."""
        hsm = HighScoreManager.get_instance(filepath=self.highscore_path)

        # Play 3 games with different scores
        for i, (name, floor) in enumerate([
            ("LowScore", 2),
            ("HighScore", 10),
            ("MediumScore", 5)
        ]):
            game = Game()
            game.start_new_game(
                seed=f"test_seed_{i}",
                player_name=name,
                character_class=CharacterClass.ROGUE
            )

            # Set floor progress
            game.state.current_floor = floor
            game.state.turn_count = floor * 10

            # Kill player
            game.state.player.take_damage(1000)
            game.turn_processor.process_turn()

        # Check scores are ranked correctly
        scores = hsm.get_all_scores(10)
        assert len(scores) == 3

        # Should be sorted by score (descending)
        assert scores[0].player_name == "HighScore"  # Floor 10
        assert scores[1].player_name == "MediumScore"  # Floor 5
        assert scores[2].player_name == "LowScore"  # Floor 2


class TestEndToEndFlow:
    """Test complete end-to-end flow from game start to high score."""

    def setup_method(self):
        """Reset singletons."""
        ConfigManager.reset()
        HighScoreManager.reset()

        # Use temporary file for high scores
        self.temp_dir = tempfile.mkdtemp()
        self.highscore_path = Path(self.temp_dir) / "test_highscores.json"

    def test_complete_game_flow(self):
        """Test complete flow: start → play → death → high score."""
        # Initialize high score manager with temp file
        hsm = HighScoreManager.get_instance(filepath=self.highscore_path)

        # 1. Start game
        game = Game()
        game.start_new_game(
            seed="e2e_test",
            player_name="E2EPlayer",
            character_class=CharacterClass.WARRIOR
        )

        # Verify game started
        assert game.state.player is not None
        assert game.state.player.hp == 30  # Warrior HP
        assert game.state.player_name == "E2EPlayer"
        assert not game.state.game_over

        # 2. Simulate some gameplay
        game.state.turn_count = 150
        game.state.current_floor = 7
        game.state.player.stats['monsters_killed'] = 15
        game.state.player.stats['ore_mined'] = 8
        game.state.player.stats['damage_dealt'] = 200
        game.state.player.stats['damage_taken'] = 100

        # 3. Player dies
        game.state.player.take_damage(1000)
        assert not game.state.player.is_alive

        # 4. Process turn (records high score)
        game.turn_processor.process_turn()

        # 5. Verify game over
        assert game.state.game_over is True

        # 6. Verify high score recorded
        scores = hsm.get_all_scores(10)
        assert len(scores) == 1

        entry = scores[0]
        assert entry.player_name == "E2EPlayer"
        assert entry.floor_reached == 7
        # Turn count is incremented before recording (150 + 1 = 151)
        assert entry.turns_survived == 151
        assert entry.monsters_killed == 15
        assert entry.ore_mined == 8
        assert entry.damage_dealt == 200
        assert entry.damage_taken == 100
        assert entry.victory is False

        # Verify score calculated correctly
        # Formula: floor*1000 + monsters*10 + ore*5 + turns + xp*0.1
        expected_score_min = 7000 + 151 + 40 + 150  # No XP in this test
        assert entry.score >= expected_score_min
