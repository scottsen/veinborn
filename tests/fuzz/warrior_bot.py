#!/usr/bin/env python3
"""
Warrior Bot - Grimbash the Unstoppable

Aggressive melee-focused bot that seeks combat and tanks damage.
Plays as Warrior class with high HP and attack.

Play: the shared ActionPlanner (tests/fuzz/services) with this class's CombatConfig below
(flee threshold, safety margin, engagement range). Intended style:
- Aggressive: Seeks combat actively, low flee threshold
- Tank: Can take more damage before retreating (20% HP threshold)
- Melee-focused: Prioritizes close combat over ranged tactics
- Direct: Explores efficiently to find enemies quickly

Usage:
    python tests/fuzz/warrior_bot.py                 # 100 games (fast)
    python tests/fuzz/warrior_bot.py --games 50      # 50 games (production)
    python tests/fuzz/warrior_bot.py --games 10 -v   # 10 games with action logs
    python tests/fuzz/warrior_bot.py --games 1 --debug # Full trace logging
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


class WarriorBot(VeinbornBot):
    """Aggressive Warrior-class bot - Grimbash the Unstoppable."""

    def __init__(self, verbose: bool = False):
        """Initialize Warrior bot with aggressive combat configuration."""
        # Warrior config: aggressive combat, high risk tolerance
        warrior_combat = CombatConfig(
            health_threshold=0.15,  # Flee at 15% HP (vs 30% default)
            safety_margin=1.2,      # Aggressive combat (vs 1.5 default)
            engagement_range=7.0,   # Pursue from farther (vs 5.0 default)
            flee_priority=6         # Standard flee priority
        )

        super().__init__(
            verbose=verbose,
            mode='strategic',
            player_name='Grimbash',
            combat_config=warrior_combat
        )
        self.character_class = CharacterClass.WARRIOR


if __name__ == "__main__":
    # Run warrior bot using shared main() from veinborn_bot
    main(bot_class=WarriorBot, default_class=CharacterClass.WARRIOR)
