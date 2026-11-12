#!/usr/bin/env python3
"""
Rogue Bot - Shadowstep the Swift

Agile exploration-focused bot with strategic combat engagement.
Plays as Rogue class with balanced stats and high mobility.

Play: the shared ActionPlanner (tests/fuzz/services) with this class's CombatConfig below
(flee threshold, safety margin, engagement range). Intended style:
- Exploration: Prioritizes discovering the map and finding valuable resources
- Tactical: Picks fights carefully, avoids unfavorable combat
- Opportunistic: Seeks mining opportunities and strategic positioning
- Evasive: Quick to retreat when threatened

Usage:
    python tests/fuzz/rogue_bot.py                # 100 games
    python tests/fuzz/rogue_bot.py --games 50 -v  # 50 verbose games
"""

import pytest


import sys
from pathlib import Path

# Add src to path
pytestmark = pytest.mark.fuzz

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import sys
from pathlib import Path

# Add tests directory to path for service imports
tests_path = Path(__file__).parent.parent
sys.path.insert(0, str(tests_path))

from core.character_class import CharacterClass
from veinborn_bot import VeinbornBot, main
from fuzz.services.tactical_decision_service import CombatConfig


class RogueBot(VeinbornBot):
    """Tactical Rogue-class bot - Shadowstep the Swift."""

    def __init__(self, verbose: bool = False):
        """Initialize Rogue bot with tactical combat configuration."""
        # Rogue config: cautious combat, high safety margin, balanced engagement
        rogue_combat = CombatConfig(
            health_threshold=0.35,  # Flee at 35% HP (vs 30% default) - cautious
            safety_margin=2.0,      # Conservative combat (vs 1.5 default)
            engagement_range=4.0,   # Shorter pursuit range (vs 5.0 default)
            flee_priority=8         # High flee priority
        )

        super().__init__(
            verbose=verbose,
            mode='strategic',
            player_name='Shadowstep',
            combat_config=rogue_combat
        )
        self.character_class = CharacterClass.ROGUE


if __name__ == "__main__":
    # Run rogue bot using shared main() from veinborn_bot
    main(bot_class=RogueBot, default_class=CharacterClass.ROGUE)
