# High Score System Design

**Date**: 2025-10-25
**Session**: xogicuca-1025
**Status**: 🎨 **DESIGN PHASE**

---

## Overview

Design a comprehensive high score system that:
- Tracks player achievements and scores
- Supports player names
- Separates seeded vs random runs
- Persists across sessions
- Displays in readable format

---

## Core Questions to Answer

### 1. What Makes a "Score"?

**Option A: Simple Score (Time Survived)**
```
Score = turns_survived
Simple, but doesn't reward depth/skill
```

**Option B: Weighted Score (Multi-factor)**
```python
score = (
    floor_reached * 1000 +      # Depth matters most
    monsters_killed * 10 +       # Combat skill
    ore_mined * 5 +              # Resource gathering
    turns_survived +             # Time survived
    (xp_gained / 10)             # Overall progression
)
```

**Option C: Classic Roguelike (End Score)**
```python
# Only matters at death/victory
score = (
    final_floor * 5000 +
    total_xp * 10 +
    inventory_value * 100 +
    victory_bonus (50000 if won)
)
```

**Recommendation**: **Option B (Weighted)** - Rewards multiple playstyles

### 2. What Data to Track?

**Essential Metrics**:
```python
@dataclass
class HighScoreEntry:
    # Identity
    player_name: str
    timestamp: str  # ISO format

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
    death_cause: Optional[str]

    # Reproducibility
    seed: Optional[Union[int, str]]
    is_seeded: bool
```

**Optional Metrics** (Future):
- Inventory value
- Floors per hour (speed)
- Ore by type breakdown
- Most dangerous floor
- Longest combat streak

### 3. How to Categorize Scores?

**Categories**:

1. **All Runs** - Combined leaderboard
2. **Random Runs** - Only unseeded games
3. **Seeded Runs** - Only seeded games
   - Further: By specific seed?
4. **Victory Runs** - Only completed games
5. **Daily/Weekly** - Time-based leaderboards

**Recommendation**: Start with **All Runs**, **Random**, **Seeded** categories

### 4. How Many to Keep?

**Options**:
- **Top 10**: Classic, fits one screen
- **Top 100**: More history, good for communities
- **Unlimited**: Keep everything (large files)

**Recommendation**: **Top 100 per category** (300 total entries max)

### 5. Where to Store?

**Option A: JSON File**
```
data/highscores.json
Simple, human-readable, easy to edit
```

**Option B: SQLite Database**
```
data/highscores.db
Queryable, scalable, overkill for now
```

**Option C: YAML File**
```
data/highscores.yaml
Designer-friendly, consistent with entities
```

**Recommendation**: **JSON** (simple, standard, easy to parse)

---

## Proposed Architecture

### 1. HighScoreEntry (Dataclass)

```python
# src/core/highscore.py

from dataclasses import dataclass, asdict
from typing import Optional, Union
from datetime import datetime

@dataclass
class HighScoreEntry:
    """
    Single high score entry.

    Tracks all relevant game statistics for leaderboard display
    and analysis.
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

    @classmethod
    def from_game_state(cls, game_state, player_name: str) -> 'HighScoreEntry':
        """Create high score entry from current game state."""
        # Calculate score
        score = cls.calculate_score(game_state)

        return cls(
            player_name=player_name,
            timestamp=datetime.now().isoformat(),
            score=score,
            floor_reached=game_state.current_floor,
            turns_survived=game_state.turn_count,
            player_level=game_state.player.level,
            xp_gained=game_state.player.xp,
            monsters_killed=game_state.player.stats.get('monsters_killed', 0),
            damage_dealt=game_state.player.stats.get('damage_dealt', 0),
            damage_taken=game_state.player.stats.get('damage_taken', 0),
            ore_mined=game_state.player.stats.get('ore_mined', 0),
            ore_surveyed=game_state.player.stats.get('ore_surveyed', 0),
            best_ore_purity=game_state.player.stats.get('best_ore_purity', 0),
            victory=game_state.victory,
            death_cause=game_state.player.stats.get('death_cause'),
            seed=game_state.seed,
            is_seeded=game_state.seed is not None,
        )

    @staticmethod
    def calculate_score(game_state) -> int:
        """
        Calculate score from game state.

        Formula:
        - Floor reached: 1000 points per floor
        - Monsters killed: 10 points each
        - Ore mined: 5 points each
        - Turns survived: 1 point each
        - XP gained: 0.1 points per XP
        - Victory bonus: 50,000 points
        """
        score = 0

        # Depth progression (most important)
        score += game_state.current_floor * 1000

        # Combat
        score += game_state.player.stats.get('monsters_killed', 0) * 10

        # Mining
        score += game_state.player.stats.get('ore_mined', 0) * 5

        # Survival
        score += game_state.turn_count

        # Experience
        score += int(game_state.player.xp * 0.1)

        # Victory bonus
        if game_state.victory:
            score += 50000

        return score

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'HighScoreEntry':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)
```

### 2. HighScoreManager (Singleton)

```python
# src/core/highscore.py

from typing import List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class HighScoreManager:
    """
    Manages high score persistence and queries.

    Features:
    - Load/save high scores to JSON
    - Add new entries
    - Query by category (all, random, seeded)
    - Maintain top N entries per category
    """

    _instance: Optional['HighScoreManager'] = None

    def __init__(self, filepath: Optional[Path] = None):
        """Initialize high score manager."""
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
        """Get singleton instance."""
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

        except (json.JSONDecodeError, KeyError) as e:
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

        Returns:
            Rank (1-based) in the all-time leaderboard, or -1 if not in top N
        """
        self.scores.append(entry)

        # Sort by score (descending)
        self.scores.sort(key=lambda e: e.score, reverse=True)

        # Trim to max entries
        if len(self.scores) > self.max_entries_per_category * 3:  # All, Random, Seeded
            # Keep top entries from each category
            all_scores = self.get_all_scores()[:self.max_entries_per_category]
            random_scores = self.get_random_scores()[:self.max_entries_per_category]
            seeded_scores = self.get_seeded_scores()[:self.max_entries_per_category]

            # Combine and deduplicate
            keep = set(all_scores + random_scores + seeded_scores)
            self.scores = list(keep)
            self.scores.sort(key=lambda e: e.score, reverse=True)

        # Save to disk
        self.save()

        # Return rank
        try:
            rank = self.scores.index(entry) + 1
            return rank
        except ValueError:
            return -1

    def get_all_scores(self, limit: int = 10) -> List[HighScoreEntry]:
        """Get top N scores (all categories)."""
        return self.scores[:limit]

    def get_random_scores(self, limit: int = 10) -> List[HighScoreEntry]:
        """Get top N unseeded scores."""
        random_scores = [s for s in self.scores if not s.is_seeded]
        return random_scores[:limit]

    def get_seeded_scores(self, limit: int = 10) -> List[HighScoreEntry]:
        """Get top N seeded scores."""
        seeded_scores = [s for s in self.scores if s.is_seeded]
        return seeded_scores[:limit]

    def get_scores_by_seed(self, seed: Union[int, str], limit: int = 10) -> List[HighScoreEntry]:
        """Get top N scores for specific seed."""
        seed_scores = [s for s in self.scores if s.seed == seed]
        seed_scores.sort(key=lambda e: e.score, reverse=True)
        return seed_scores[:limit]

    def get_victory_scores(self, limit: int = 10) -> List[HighScoreEntry]:
        """Get top N victory runs."""
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
            return True  # Not full yet

        return score > scores[-1].score

    def format_leaderboard(self, scores: List[HighScoreEntry], title: str = "HIGH SCORES") -> str:
        """
        Format leaderboard for display.

        Returns:
            Formatted string ready for terminal display
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"{title:^80}")
        lines.append("=" * 80)
        lines.append(f"{'Rank':<6} {'Name':<16} {'Score':>10} {'Floor':>6} {'Turns':>8} {'Seed':<16}")
        lines.append("-" * 80)

        for i, entry in enumerate(scores, 1):
            seed_str = str(entry.seed)[:14] if entry.seed else "random"
            lines.append(
                f"{i:<6} {entry.player_name[:15]:<16} {entry.score:>10} "
                f"{entry.floor_reached:>6} {entry.turns_survived:>8} {seed_str:<16}"
            )

        lines.append("=" * 80)
        return "\n".join(lines)
```

### 3. Integration with Game

```python
# src/core/game.py

from .highscore import HighScoreManager, HighScoreEntry

class Game:
    # ... existing code ...

    def handle_game_over(self, player_name: str) -> int:
        """
        Handle game over, record high score.

        Args:
            player_name: Name to record for this run

        Returns:
            Rank in all-time leaderboard (1-based), or -1 if not in top N
        """
        if not self.state.game_over:
            return -1

        # Create high score entry
        entry = HighScoreEntry.from_game_state(self.state, player_name)

        # Add to leaderboard
        hsm = HighScoreManager.get_instance()
        rank = hsm.add_score(entry)

        logger.info(
            f"Game over for {player_name}: score={entry.score}, "
            f"floor={entry.floor_reached}, rank={rank}"
        )

        return rank
```

### 4. Player Name in GameState

```python
# src/core/game_state.py

@dataclass
class GameState:
    # ... existing fields ...

    # Player identity
    player_name: Optional[str] = None  # Set at game over
```

---

## User Flow

### Game Start

```
1. Start new game
   - Optionally: Enter name upfront?
   - Or: Prompt for name only at game over?
```

**Recommendation**: Prompt at game over (don't interrupt game start)

### During Game

```
Game tracks statistics automatically:
- Monsters killed (already tracked in Phase 3 bot)
- Ore mined (already tracked in Phase 3 bot)
- Damage dealt/taken (new)
- Best ore purity (already tracked)
```

### Game Over

```
1. Game over (death or victory)
2. Prompt: "Enter your name: "
3. Calculate final score
4. Check if high score
5. If high score:
   - Show: "🎉 New High Score! Rank #X"
   - Save to leaderboard
6. Display final stats
7. Option to view leaderboard
```

### View Leaderboard

```
Main menu or game over:
- "View High Scores"
  - All Runs (top 10)
  - Random Runs (top 10)
  - Seeded Runs (top 10)
  - Victories Only (top 10)
```

---

## File Structure

```
data/
  highscores.json          # High score persistence

src/core/
  highscore.py             # HighScoreEntry + HighScoreManager

tests/unit/
  test_highscore.py        # High score tests

examples/
  demo_highscores.py       # High score demo
```

---

## JSON Format

```json
[
  {
    "player_name": "Alice",
    "timestamp": "2025-10-25T13:30:00",
    "score": 15750,
    "floor_reached": 8,
    "turns_survived": 2500,
    "player_level": 5,
    "xp_gained": 450,
    "monsters_killed": 25,
    "damage_dealt": 1200,
    "damage_taken": 800,
    "ore_mined": 10,
    "ore_surveyed": 30,
    "best_ore_purity": 92,
    "victory": false,
    "death_cause": "Killed by Orc",
    "seed": 12345,
    "is_seeded": true
  },
  {
    "player_name": "Bob",
    "timestamp": "2025-10-25T14:00:00",
    "score": 52500,
    "floor_reached": 10,
    "turns_survived": 5000,
    "player_level": 8,
    "xp_gained": 1200,
    "monsters_killed": 60,
    "damage_dealt": 3500,
    "damage_taken": 2000,
    "ore_mined": 25,
    "ore_surveyed": 80,
    "best_ore_purity": 98,
    "victory": true,
    "death_cause": null,
    "seed": null,
    "is_seeded": false
  }
]
```

---

## Open Questions

### 1. Player Name Input

**When to prompt?**
- A. At game start (annoying, slows start)
- B. At game over (better UX, but if crashes no name)
- C. Optional config (set once, use always)

**Recommendation**: **B (game over) + C (optional config)**

### 2. Default Name

**If player doesn't enter name?**
- "Anonymous"
- "Player"
- "Adventurer_XXXX" (random)
- Require name (no submission without it)

**Recommendation**: "Anonymous" (allow skipping)

### 3. Name Validation

**Rules?**
- Max length: 16 characters
- Allowed chars: alphanumeric + spaces + dashes
- No profanity filter? (overkill for now)

**Recommendation**: Simple validation (length + chars)

### 4. Death Cause Tracking

**Where to store?**
- GameState: death_cause field
- Set on player death
- Examples: "Killed by Orc", "Starved", "Fell into pit"

**Recommendation**: Add to GameState, populate on death

### 5. Damage Tracking

**Where to track?**
- Player stats: damage_dealt, damage_taken
- Increment in AttackAction

**Recommendation**: Add to Player stats, track in combat

---

## Implementation Plan

### Phase 1: Core System

1. Create HighScoreEntry dataclass
2. Create HighScoreManager singleton
3. Add score calculation method
4. Add JSON persistence
5. Write unit tests

### Phase 2: Stat Tracking

1. Add damage_dealt to Player stats
2. Add damage_taken to Player stats
3. Track in AttackAction
4. Add death_cause to GameState
5. Set on player death

### Phase 3: Integration

1. Add handle_game_over() to Game
2. Prompt for player name (terminal)
3. Record high score on game over
4. Display rank/congratulations

### Phase 4: Display

1. Create leaderboard formatter
2. Add "view leaderboard" option
3. Pretty print high scores
4. Add filtering (all/random/seeded)

### Phase 5: Polish

1. Add player_name to GameState (optional config)
2. Name validation
3. Demo script
4. Full documentation

---

## Success Metrics

- [ ] HighScoreEntry stores all relevant stats
- [ ] HighScoreManager persists to JSON
- [ ] Score calculation is meaningful
- [ ] Leaderboard displays correctly
- [ ] Game over flow integrates smoothly
- [ ] Tests cover all functionality
- [ ] Bot can generate high scores automatically

---

## Alternatives Considered

### Database Instead of JSON

**Pros**: Queryable, scalable, relational
**Cons**: Overkill, adds dependency, harder to inspect

**Verdict**: JSON for now, migrate later if needed

### Separate File Per Player

**Pros**: Easy to manage individual players
**Cons**: Hard to query across all players

**Verdict**: Single JSON file

### Steam/Online Leaderboard

**Pros**: Global competition, cloud sync
**Cons**: Requires server, authentication, networking

**Verdict**: Local only for now, online is future enhancement

---

## Next Steps

**Decide**:
1. Score formula - Is weighted approach good?
2. Player name flow - At game over?
3. Categories - All/Random/Seeded sufficient?
4. Max entries - 100 per category?

**Then Implement**:
1. HighScoreEntry + HighScoreManager
2. Stat tracking (damage, death cause)
3. Game over integration
4. Display/formatting
5. Tests

---

What do you think? Any changes to the design before I implement?
