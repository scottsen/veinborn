#!/usr/bin/env python3
"""
Healer Bot - Lifebinder the Steadfast

Defensive survival specialist focused on sustainability and patience.
Plays as Healer class with high defense and support abilities.

Play: the shared ActionPlanner (tests/fuzz/services) with this class's CombatConfig below
(flee threshold, safety margin, engagement range). Intended style:
- Defensive: High defense allows weathering attacks
- Patient: Willing to wait and take time, no rush
- Sustainable: Prioritizes long-term survival over quick wins
- Protective: Avoids unnecessary risks, plays it safe

Usage:
    python tests/fuzz/healer_bot.py                # 100 games
    python tests/fuzz/healer_bot.py --games 50 -v  # 50 verbose games
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


class HealerBot(VeinbornBot):
    """Defensive Healer-class bot - Lifebinder the Steadfast."""

    def __init__(self, verbose: bool = False):
        """Initialize Healer bot with defensive, patient combat configuration."""
        # Healer config: defensive tank - patient, sustainable combat
        healer_combat = CombatConfig(
            health_threshold=0.4,   # Flee at 40% HP (vs 30% default) - moderate caution
            safety_margin=1.3,      # Patient combat (vs 1.5 default) - willing to tank
            engagement_range=5.0,   # Standard range (default)
            flee_priority=4         # Lower flee priority - tanks damage
        )

        super().__init__(
            verbose=verbose,
            mode='strategic',
            player_name='Lifebinder',
            combat_config=healer_combat
        )
        self.character_class = CharacterClass.HEALER


if __name__ == "__main__":
    # Run healer bot using shared main() from veinborn_bot
    main(bot_class=HealerBot, default_class=CharacterClass.HEALER)
