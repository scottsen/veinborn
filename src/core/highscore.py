"""
High Score System

Tracks and persists player achievements across games.

Features:
- Weighted scoring formula (floor, combat, mining, survival)
- Separate categories (all, random, seeded, victories)
- JSON persistence
- Top 100 entries per category
- Seed-specific leaderboards

Usage:
    from src.core.highscore import HighScoreManager, HighScoreEntry

    # On game over
    entry = HighScoreEntry.from_game_state(game.state, "Alice")
    hsm = HighScoreManager.get_instance()
    rank = hsm.add_score(entry)

    # Display leaderboard
    scores = hsm.get_all_scores(10)
    print(hsm.format_leaderboard(scores))
"""

from dataclasses import dataclass, asdict
from typing import Optional, Union, List, TYPE_CHECKING
from datetime import datetime
from pathlib import Path
import json
import logging

if TYPE_CHECKING:
    from .game_state import GameState
    from .config import GameConfig

logger = logging.getLogger(__name__)


@dataclass
class HighScoreEntry:
    """
    Single high score entry.

    Tracks all relevant game statistics for leaderboard display
    and post-game analysis.

    Attributes:
        player_name: Player's name
        timestamp: ISO 8601 timestamp of game completion
        score: Calculated score (weighted formula)
        floor_reached: Deepest floor reached
        turns_survived: Total turns played
        player_level: Final player level
        xp_gained: Total XP earned
        monsters_killed: Monsters defeated
        damage_dealt: Total damage output
        damage_taken: Total damage received
        ore_mined: Ore successfully mined
        ore_surveyed: Ore veins surveyed
        best_ore_purity: Highest purity ore found
        victory: True if game was won
        death_cause: How the player died (if applicable)
        seed: Game seed (for reproducibility)
        is_seeded: True if game used a seed
    """

    # Identity
    player_name: str
    timestamp: str  # ISO 8601 format

    # Core stats
    score: int
    floor_reached: int
    turns_survived: int

    # Progression
    player_level: int
    xp_gained: int

    # Combat
    monsters_killed: int
    damage_dealt: int
    damage_taken: int

    # Mining
    ore_mined: int
    ore_surveyed: int
    best_ore_purity: int

    # Outcome
    victory: bool
    death_cause: Optional[str] = None

    # Reproducibility
    seed: Optional[Union[int, str]] = None
    is_seeded: bool = False

    # Victory type (meta-progression)
    victory_type: str = "pure"  # "pure" or "legacy"

    @classmethod
    def from_game_state(cls, game_state: 'GameState', player_name: str) -> 'HighScoreEntry':
        """
        Create high score entry from game state.

        Args:
            game_state: Current game state
            player_name: Player's name for leaderboard

        Returns:
            HighScoreEntry instance

        Example:
            >>> entry = HighScoreEntry.from_game_state(game.state, "Alice")
            >>> entry.score
            15450
        """
        # Calculate score
        score = cls.calculate_score(game_state)

        # Get stats from player (with safe defaults)
        player = game_state.player
        stats = player.stats if hasattr(player, 'stats') else {}

        return cls(
            player_name=player_name,
            timestamp=datetime.now().isoformat(),
            score=score,
            floor_reached=getattr(game_state, 'current_floor', 1),
            turns_survived=getattr(game_state, 'turn_count', 0),
            player_level=getattr(player, 'level', 1) if hasattr(player, 'level') else stats.get('level', 1),
            xp_gained=getattr(player, 'xp', 0) if hasattr(player, 'xp') else stats.get('xp', 0),
            monsters_killed=stats.get('monsters_killed', 0),
            damage_dealt=stats.get('damage_dealt', 0),
            damage_taken=stats.get('damage_taken', 0),
            ore_mined=stats.get('ore_mined', 0),
            ore_surveyed=stats.get('ore_surveyed', 0),
            best_ore_purity=stats.get('best_ore_purity', 0),
            victory=getattr(game_state, 'victory', False),
            death_cause=stats.get('death_cause'),
            seed=getattr(game_state, 'seed', None),
            is_seeded=hasattr(game_state, 'seed') and game_state.seed is not None,
            victory_type=getattr(game_state, 'run_type', 'pure'),
        )

    @staticmethod
    def calculate_score(game_state: 'GameState') -> int:
        """
        Calculate score from game state.

        Formula (weighted multi-factor):
        - Floor reached: 1000 points per floor (depth is most important)
        - Monsters killed: 10 points each (combat skill)
        - Ore mined: 5 points each (mining skill)
        - Turns survived: 1 point each (survival time)
        - XP gained: configurable multiplier per XP (overall progression)
        - Victory bonus: 50,000 points (winning is huge!)

        Args:
            game_state: Game state to score

        Returns:
            Calculated score (integer)
        """
        # Load config for scoring weights
        from .config import ConfigLoader
        config = ConfigLoader.load()
        xp_multiplier = config.game_constants['highscore']['scoring']['xp_multiplier']

        score = 0
        player = game_state.player
        stats = player.stats if hasattr(player, 'stats') else {}

        # Depth progression (most important)
        score += getattr(game_state, 'current_floor', 1) * 1000

        # Combat
        score += stats.get('monsters_killed', 0) * 10

        # Mining
        score += stats.get('ore_mined', 0) * 5

        # Survival
        score += getattr(game_state, 'turn_count', 0)

        # Experience (uses config value)
        xp = getattr(player, 'xp', 0) if hasattr(player, 'xp') else stats.get('xp', 0)
        score += int(xp * xp_multiplier)

        # Victory bonus
        if getattr(game_state, 'victory', False):
            score += 50000

        return score

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'HighScoreEntry':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


class HighScoreManager:
    """
    Manages high score persistence and queries.

    Singleton pattern ensures single source of truth.

    Features:
    - Load/save high scores to JSON
    - Add new entries with automatic ranking
    - Query by category (all, random, seeded, victories)
    - Maintain top N entries per category
    - Format leaderboards for display

    Example:
        >>> hsm = HighScoreManager.get_instance()
        >>> entry = HighScoreEntry(...)
        >>> rank = hsm.add_score(entry)
        >>> print(f"You ranked #{rank}!")
        >>> scores = hsm.get_all_scores(10)
        >>> print(hsm.format_leaderboard(scores))
    """

    _instance: Optional['HighScoreManager'] = None

    def __init__(self, filepath: Optional[Path] = None):
        """
        Initialize high score manager.

        Args:
            filepath: Path to high scores JSON file (default: data/highscores.json)
        """
        if filepath is None:
            # Default to data/highscores.json
            project_root = Path(__file__).parent.parent.parent
            filepath = project_root / "data" / "highscores.json"

        self.filepath = Path(filepath)
        self.scores: List[HighScoreEntry] = []
        self.max_entries_per_category = 100

        # Load existing scores
        self.load()

    @classmethod
    def get_instance(cls, filepath: Optional[Path] = None) -> 'HighScoreManager':
        """
        Get singleton instance.

        Args:
            filepath: Path to high scores file (only used on first call)

        Returns:
            HighScoreManager singleton instance
        """
        if cls._instance is None:
            cls._instance = cls(filepath)
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (for testing)."""
        cls._instance = None

    def load(self) -> None:
        """Load high scores from JSON file."""
        if not self.filepath.exists():
            logger.info(f"No high score file found at {self.filepath}, starting fresh")
            self.scores = []
            return

        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                self.scores = [HighScoreEntry.from_dict(entry) for entry in data]

            logger.info(f"Loaded {len(self.scores)} high scores from {self.filepath}")

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to load high scores: {e}")
            self.scores = []

    def save(self) -> None:
        """Save high scores to JSON file."""
        # Ensure directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = [entry.to_dict() for entry in self.scores]

            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.scores)} high scores to {self.filepath}")

        except IOError as e:
            logger.error(f"Failed to save high scores: {e}")

    def add_score(self, entry: HighScoreEntry) -> int:
        """
        Add new high score entry.

        Automatically saves to disk after adding.

        Args:
            entry: High score entry to add

        Returns:
            Rank (1-based) in the all-time leaderboard, or -1 if not in top N

        Example:
            >>> rank = hsm.add_score(entry)
            >>> if rank <= 10:
            ...     print(f"Top 10! You're #{rank}!")
        """
        self.scores.append(entry)

        # Sort by score (descending)
        self.scores.sort(key=lambda e: e.score, reverse=True)

        # Trim to max entries (keep top from each category)
        if len(self.scores) > self.max_entries_per_category * 3:
            all_scores = self.get_all_scores(self.max_entries_per_category)
            random_scores = self.get_random_scores(self.max_entries_per_category)
            seeded_scores = self.get_seeded_scores(self.max_entries_per_category)

            # Combine and deduplicate (keep unique entries)
            keep_set = set(all_scores + random_scores + seeded_scores)
            self.scores = list(keep_set)
            self.scores.sort(key=lambda e: e.score, reverse=True)

        # Save to disk
        self.save()

        # Return rank in all-time leaderboard
        try:
            rank = self.scores.index(entry) + 1
            return rank
        except ValueError:
            return -1

    def get_all_scores(self, limit: int = 10) -> List[HighScoreEntry]:
        """
        Get top N scores (all categories).

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of top scores (sorted by score descending)
        """
        return self.scores[:limit]

    def get_random_scores(self, limit: int = 10) -> List[HighScoreEntry]:
        """
        Get top N unseeded scores.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of top unseeded scores
        """
        random_scores = [s for s in self.scores if not s.is_seeded]
        return random_scores[:limit]

    def get_seeded_scores(self, limit: int = 10) -> List[HighScoreEntry]:
        """
        Get top N seeded scores.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of top seeded scores
        """
        seeded_scores = [s for s in self.scores if s.is_seeded]
        return seeded_scores[:limit]

    def get_scores_by_seed(self, seed: Union[int, str], limit: int = 10) -> List[HighScoreEntry]:
        """
        Get top N scores for specific seed.

        Args:
            seed: Specific seed to query
            limit: Maximum number of entries to return

        Returns:
            List of scores for this seed (sorted by score descending)
        """
        seed_scores = [s for s in self.scores if s.seed == seed]
        seed_scores.sort(key=lambda e: e.score, reverse=True)
        return seed_scores[:limit]

    def get_victory_scores(self, limit: int = 10) -> List[HighScoreEntry]:
        """
        Get top N victory runs.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of victorious runs (sorted by score descending)
        """
        victories = [s for s in self.scores if s.victory]
        victories.sort(key=lambda e: e.score, reverse=True)
        return victories[:limit]

    def is_high_score(self, score: int, category: str = 'all') -> bool:
        """
        Check if score would make the leaderboard.

        Args:
            score: Score to check
            category: 'all', 'random', or 'seeded'

        Returns:
            True if score would be in top N for category

        Example:
            >>> if hsm.is_high_score(5000, 'all'):
            ...     print("New high score!")
        """
        if category == 'all':
            scores = self.get_all_scores(self.max_entries_per_category)
        elif category == 'random':
            scores = self.get_random_scores(self.max_entries_per_category)
        elif category == 'seeded':
            scores = self.get_seeded_scores(self.max_entries_per_category)
        else:
            return False

        if len(scores) < self.max_entries_per_category:
            return True  # Not full yet, any score qualifies

        return score > scores[-1].score

    def format_leaderboard(self, scores: List[HighScoreEntry], title: str = "HIGH SCORES") -> str:
        """
        Format leaderboard for terminal display.

        Args:
            scores: List of scores to display
            title: Leaderboard title

        Returns:
            Formatted string ready for terminal display

        Example:
            >>> scores = hsm.get_all_scores(10)
            >>> print(hsm.format_leaderboard(scores, "TOP 10"))
        """
        lines = []
        lines.append("=" * 88)
        lines.append(f"{title:^88}")
        lines.append("=" * 88)
        lines.append(f"{'Rank':<6} {'Name':<16} {'Score':>10} {'Floor':>6} {'Turns':>8} {'Type':<8} {'Seed':<16}")
        lines.append("-" * 88)

        if not scores:
            lines.append(f"{'No scores yet!':^88}")
        else:
            for i, entry in enumerate(scores, 1):
                seed_str = str(entry.seed)[:14] if entry.seed else "random"
                # Get victory type with backward compatibility
                victory_type = getattr(entry, 'victory_type', 'pure')
                type_str = f"{'*' if victory_type == 'pure' else 'L'} {victory_type:<6}"
                lines.append(
                    f"{i:<6} {entry.player_name[:15]:<16} {entry.score:>10} "
                    f"{entry.floor_reached:>6} {entry.turns_survived:>8} {type_str:<8} {seed_str:<16}"
                )

        lines.append("=" * 88)
        return "\n".join(lines)
