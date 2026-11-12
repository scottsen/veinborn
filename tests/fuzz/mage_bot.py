#!/usr/bin/env python3
"""
Mage Bot - Sparkweave the Arcane

Tactical ranged combat specialist with cautious engagement.
Plays as Mage class with low HP but high tactical awareness.

Play: the shared ActionPlanner (tests/fuzz/services) with this class's CombatConfig below
(flee threshold, safety margin, engagement range). Intended style:
- Ranged preference: Avoids melee when possible
- Tactical positioning: Maintains distance from threats
- Glass cannon: Very cautious due to low HP pool
- Calculated risks: Only engages when advantage is overwhelming

Usage:
    python tests/fuzz/mage_bot.py                # 100 games
    python tests/fuzz/mage_bot.py --games 50 -v  # 50 verbose games
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


class MageBot(VeinbornBot):
    """Tactical Mage-class bot - Sparkweave the Arcane."""

    def __init__(self, verbose: bool = False):
        """Initialize Mage bot with extremely cautious combat configuration."""
        # Mage config: glass cannon - very cautious, requires overwhelming advantage
        mage_combat = CombatConfig(
            health_threshold=0.5,   # Flee at 50% HP (vs 30% default) - very cautious
            safety_margin=3.0,      # Very conservative combat (vs 1.5 default)
            engagement_range=3.0,   # Very short range (vs 5.0 default)
            flee_priority=10        # Highest flee priority
        )

        super().__init__(
            verbose=verbose,
            mode='strategic',
            player_name='Sparkweave',
            combat_config=mage_combat
        )
        self.character_class = CharacterClass.MAGE


if __name__ == "__main__":
    # Run mage bot using shared main() from veinborn_bot
    main(bot_class=MageBot, default_class=CharacterClass.MAGE)
