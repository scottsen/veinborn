"""
Tests for High Score System

Validates:
- Score calculation formula
- HighScoreEntry creation from game state
- HighScoreManager persistence (load/save)
- Leaderboard queries (all, random, seeded, victories)
- Ranking and category management
- Leaderboard formatting
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from datetime import datetime

from src.core.highscore import HighScoreEntry, HighScoreManager


pytestmark = pytest.mark.unit

class TestHighScoreEntry:
    """Test HighScoreEntry dataclass."""

    def test_create_entry(self):
        """Should create valid high score entry."""
        entry = HighScoreEntry(
            player_name="Alice",
            timestamp="2025-10-25T12:00:00",
            score=15000,
            floor_reached=10,
            turns_survived=500,
            player_level=5,
            xp_gained=1000,
            monsters_killed=20,
            damage_dealt=300,
            damage_taken=100,
            ore_mined=15,
            ore_surveyed=30,
            best_ore_purity=85,
            victory=False,
            death_cause="Killed by orc",
            seed=12345,
            is_seeded=True,
        )

        assert entry.player_name == "Alice"
        assert entry.score == 15000
        assert entry.floor_reached == 10
        assert entry.is_seeded is True

    def test_to_dict(self):
        """Should serialize to dictionary."""
        entry = HighScoreEntry(
            player_name="Bob",
            timestamp="2025-10-25T12:00:00",
            score=5000,
            floor_reached=5,
            turns_survived=200,
            player_level=3,
            xp_gained=500,
            monsters_killed=10,
            damage_dealt=150,
            damage_taken=50,
            ore_mined=5,
            ore_surveyed=10,
            best_ore_purity=60,
            victory=False,
        )

        data = entry.to_dict()
        assert isinstance(data, dict)
        assert data['player_name'] == "Bob"
        assert data['score'] == 5000
        assert data['victory'] is False

    def test_from_dict(self):
        """Should deserialize from dictionary."""
        data = {
            'player_name': "Charlie",
            'timestamp': "2025-10-25T12:00:00",
            'score': 10000,
            'floor_reached': 8,
            'turns_survived': 400,
            'player_level': 4,
            'xp_gained': 800,
            'monsters_killed': 15,
            'damage_dealt': 250,
            'damage_taken': 75,
            'ore_mined': 10,
            'ore_surveyed': 20,
            'best_ore_purity': 75,
            'victory': False,
            'death_cause': None,
            'seed': None,
            'is_seeded': False,
        }

        entry = HighScoreEntry.from_dict(data)
        assert entry.player_name == "Charlie"
        assert entry.score == 10000
        assert entry.is_seeded is False

    def test_from_game_state(self):
        """Should create entry from game state."""
        # Mock game state
        game_state = MagicMock()
        game_state.current_floor = 7
        game_state.turn_count = 300
        game_state.victory = False
        game_state.seed = 99999

        # Mock player
        player = MagicMock()
        player.level = 4
        player.xp = 600
        player.stats = {
            'monsters_killed': 12,
            'damage_dealt': 200,
            'damage_taken': 60,
            'ore_mined': 8,
            'ore_surveyed': 16,
            'best_ore_purity': 70,
            'death_cause': "Killed by goblin"
        }
        game_state.player = player

        entry = HighScoreEntry.from_game_state(game_state, "Dave")

        assert entry.player_name == "Dave"
        assert entry.floor_reached == 7
        assert entry.turns_survived == 300
        assert entry.monsters_killed == 12
        assert entry.seed == 99999
        assert entry.is_seeded is True

    def test_calculate_score_basic(self):
        """Should calculate score using weighted formula."""
        game_state = MagicMock()
        game_state.current_floor = 5
        game_state.turn_count = 200
        game_state.victory = False

        player = MagicMock()
        player.xp = 500
        player.stats = {
            'monsters_killed': 10,
            'ore_mined': 5,
        }
        game_state.player = player

        score = HighScoreEntry.calculate_score(game_state)

        # Formula: floor*1000 + kills*10 + ore*5 + turns + xp*0.1
        expected = (5 * 1000) + (10 * 10) + (5 * 5) + 200 + int(500 * 0.1)
        assert score == expected  # 5000 + 100 + 25 + 200 + 50 = 5375

    def test_calculate_score_with_victory(self):
        """Victory should add 50,000 bonus."""
        game_state = MagicMock()
        game_state.current_floor = 10
        game_state.turn_count = 500
        game_state.victory = True  # Victory!

        player = MagicMock()
        player.xp = 1000
        player.stats = {
            'monsters_killed': 20,
            'ore_mined': 10,
        }
        game_state.player = player

        score = HighScoreEntry.calculate_score(game_state)

        # Formula: floor*1000 + kills*10 + ore*5 + turns + xp*0.1 + victory_bonus
        expected = (10 * 1000) + (20 * 10) + (10 * 5) + 500 + int(1000 * 0.1) + 50000
        assert score == expected  # 10000 + 200 + 50 + 500 + 100 + 50000 = 60850


class TestHighScoreManager:
    """Test HighScoreManager functionality."""

    def setup_method(self):
        """Reset singleton before each test."""
        HighScoreManager.reset()

    def test_singleton_pattern(self):
        """Should use singleton pattern."""
        hsm1 = HighScoreManager.get_instance()
        hsm2 = HighScoreManager.get_instance()
        assert hsm1 is hsm2

    def test_load_nonexistent_file(self):
        """Should handle missing file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "nonexistent.json"
            hsm = HighScoreManager(filepath)
            assert hsm.scores == []

    def test_save_and_load(self):
        """Should persist scores to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"

            # Create and save scores
            hsm = HighScoreManager(filepath)
            entry = HighScoreEntry(
                player_name="Test",
                timestamp="2025-10-25T12:00:00",
                score=1000,
                floor_reached=5,
                turns_survived=100,
                player_level=2,
                xp_gained=200,
                monsters_killed=5,
                damage_dealt=50,
                damage_taken=20,
                ore_mined=3,
                ore_surveyed=6,
                best_ore_purity=50,
                victory=False,
            )
            hsm.add_score(entry)

            # Reload from file
            HighScoreManager.reset()
            hsm2 = HighScoreManager(filepath)
            assert len(hsm2.scores) == 1
            assert hsm2.scores[0].player_name == "Test"
            assert hsm2.scores[0].score == 1000

    def test_add_score_returns_rank(self):
        """Should return rank when adding score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            hsm = HighScoreManager(filepath)

            # Add scores (descending scores)
            entry1 = self._create_entry("Alice", 5000)
            entry2 = self._create_entry("Bob", 3000)
            entry3 = self._create_entry("Charlie", 4000)

            rank1 = hsm.add_score(entry1)
            rank2 = hsm.add_score(entry2)
            rank3 = hsm.add_score(entry3)

            assert rank1 == 1  # First score, rank 1
            assert rank2 == 2  # Second score at the time (lowest of 2)
            assert rank3 == 2  # Third score (middle of 3)

            # Final rankings should be correct
            final_scores = hsm.get_all_scores()
            assert final_scores[0].player_name == "Alice"  # 5000 - rank 1
            assert final_scores[1].player_name == "Charlie"  # 4000 - rank 2
            assert final_scores[2].player_name == "Bob"  # 3000 - rank 3

    def test_scores_sorted_by_score(self):
        """Scores should be sorted descending by score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            hsm = HighScoreManager(filepath)

            hsm.add_score(self._create_entry("Alice", 3000))
            hsm.add_score(self._create_entry("Bob", 5000))
            hsm.add_score(self._create_entry("Charlie", 4000))

            scores = hsm.get_all_scores()
            assert scores[0].score == 5000
            assert scores[1].score == 4000
            assert scores[2].score == 3000

    def test_get_random_scores(self):
        """Should filter unseeded scores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            hsm = HighScoreManager(filepath)

            hsm.add_score(self._create_entry("Alice", 5000, seed=None, is_seeded=False))
            hsm.add_score(self._create_entry("Bob", 4000, seed=12345, is_seeded=True))
            hsm.add_score(self._create_entry("Charlie", 3000, seed=None, is_seeded=False))

            random_scores = hsm.get_random_scores()
            assert len(random_scores) == 2
            assert all(not s.is_seeded for s in random_scores)

    def test_get_seeded_scores(self):
        """Should filter seeded scores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            hsm = HighScoreManager(filepath)

            hsm.add_score(self._create_entry("Alice", 5000, seed=None, is_seeded=False))
            hsm.add_score(self._create_entry("Bob", 4000, seed=12345, is_seeded=True))
            hsm.add_score(self._create_entry("Charlie", 3000, seed=99999, is_seeded=True))

            seeded_scores = hsm.get_seeded_scores()
            assert len(seeded_scores) == 2
            assert all(s.is_seeded for s in seeded_scores)

    def test_get_scores_by_seed(self):
        """Should filter by specific seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            hsm = HighScoreManager(filepath)

            hsm.add_score(self._create_entry("Alice", 5000, seed=12345, is_seeded=True))
            hsm.add_score(self._create_entry("Bob", 4000, seed=12345, is_seeded=True))
            hsm.add_score(self._create_entry("Charlie", 3000, seed=99999, is_seeded=True))

            seed_scores = hsm.get_scores_by_seed(12345)
            assert len(seed_scores) == 2
            assert all(s.seed == 12345 for s in seed_scores)

    def test_get_victory_scores(self):
        """Should filter victory runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            hsm = HighScoreManager(filepath)

            hsm.add_score(self._create_entry("Alice", 60000, victory=True))
            hsm.add_score(self._create_entry("Bob", 4000, victory=False))
            hsm.add_score(self._create_entry("Charlie", 55000, victory=True))

            victories = hsm.get_victory_scores()
            assert len(victories) == 2
            assert all(s.victory for s in victories)
            assert victories[0].score == 60000  # Sorted by score

    def test_is_high_score(self):
        """Should check if score qualifies for leaderboard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            hsm = HighScoreManager(filepath)
            hsm.max_entries_per_category = 3

            hsm.add_score(self._create_entry("Alice", 5000))
            hsm.add_score(self._create_entry("Bob", 4000))
            hsm.add_score(self._create_entry("Charlie", 3000))

            assert hsm.is_high_score(5500, 'all') is True  # Better than all
            assert hsm.is_high_score(3500, 'all') is True  # Better than lowest
            assert hsm.is_high_score(2000, 'all') is False  # Worse than all

    def test_format_leaderboard(self):
        """Should format leaderboard for display."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            hsm = HighScoreManager(filepath)

            hsm.add_score(self._create_entry("Alice", 5000))
            hsm.add_score(self._create_entry("Bob", 4000))

            scores = hsm.get_all_scores()
            formatted = hsm.format_leaderboard(scores, "TEST SCORES")

            assert "TEST SCORES" in formatted
            assert "Alice" in formatted
            assert "Bob" in formatted
            assert "5000" in formatted
            assert "4000" in formatted

    def test_format_empty_leaderboard(self):
        """Should handle empty leaderboard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            hsm = HighScoreManager(filepath)

            formatted = hsm.format_leaderboard([], "EMPTY")
            assert "EMPTY" in formatted
            assert "No scores yet!" in formatted

    def _create_entry(self, name: str, score: int, seed=None, is_seeded=False, victory=False) -> HighScoreEntry:
        """Helper to create test entry."""

        return HighScoreEntry(
            player_name=name,
            timestamp=datetime.now().isoformat(),
            score=score,
            floor_reached=score // 1000,
            turns_survived=100,
            player_level=2,
            xp_gained=200,
            monsters_killed=5,
            damage_dealt=50,
            damage_taken=20,
            ore_mined=3,
            ore_surveyed=6,
            best_ore_purity=50,
            victory=victory,
            seed=seed,
            is_seeded=is_seeded,
        )
