#!/usr/bin/env python3
"""
Mage Bot - Sparkweave the Arcane

Tactical ranged combat specialist with cautious engagement.
Plays as Mage class with low HP but high tactical awareness.

Strategy:
- Ranged preference: Avoids melee when possible
- Tactical positioning: Maintains distance from threats
- Glass cannon: Very cautious due to low HP pool
- Calculated risks: Only engages when advantage is overwhelming

Usage:
    python tests/fuzz/mage_bot.py                # 100 games
    python tests/fuzz/mage_bot.py --games 50 -v  # 50 verbose games
"""

import pytest

pytestmark = pytest.mark.fuzz

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import sys
from pathlib import Path

# Add tests directory to path for service imports
tests_path = Path(__file__).parent.parent
sys.path.insert(0, str(tests_path))

from core.game import Game
from core.character_class import CharacterClass
from brogue_bot import BrogueBot, BotStats, main
from fuzz.services.tactical_decision_service import CombatConfig, MiningConfig


class MageBot(BrogueBot):
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

    def get_smart_action(self, game: Game) -> tuple:
        """
        Mage decision tree prioritizes survival and tactical positioning.

        Uses services but has a survival-focused priority order:
        1. Flee if any threat present (paramount)
        2. Descend if ready (escape priority)
        3. Mine jackpot ore only if perfectly safe
        4. Fight only trivial threats when forced
        5. Mine/survey only when completely safe
        6. Seek stairs aggressively
        7. Careful exploration
        """
        player = game.state.player

        # Priority 1: FLEE FIRST (Mage survival instinct)
        if self.decisions.should_flee(game):
            # Emergency descent if on stairs
            if self.perception.on_stairs(game):
                self.log(f"🔮 Tactical escape! (HP: {player.hp}/{player.max_hp})")
                return ('descend', {})

            # Flee to stairs immediately
            stairs_pos = self.perception.find_level_exit(game)
            if stairs_pos:
                from core.base.entity import Entity, EntityType
                stairs_entity = Entity(
                    entity_type=EntityType.PLAYER,
                    name="Stairs",
                    x=stairs_pos[0],
                    y=stairs_pos[1],
                )
                dist = player.distance_to(stairs_entity)
                self.log(f"🔮 Retreating! (HP: {player.hp}/{player.max_hp}, distance: {dist:.1f})")
                return self.planner.move_towards(game, stairs_entity)

            # Flee from threat
            nearby = self.perception.monster_in_view(game, distance=6.0)
            if nearby:
                self.log(f"🔮 Evading {nearby.name}!")
                return self.planner.flee_from(game, nearby)

        # Priority 2: Descend if ready (escape priority)
        if self.decisions.should_descend(game):
            return ('descend', {})

        # Priority 3: Jackpot ore only if perfectly safe (no monsters visible)
        jackpot = self.perception.find_jackpot_ore(game)
        if jackpot:
            nearby_threat = self.perception.monster_in_view(game, distance=8.0)
            if not nearby_threat and player.hp == player.max_hp:
                dist = player.distance_to(jackpot)
                if dist <= 1:
                    self.log(f"💎 JACKPOT! {jackpot.ore_type} (purity: {jackpot.get_stat('purity')})")
                    self.stats.jackpot_ore_found += 1
                    return ('mine', {})
                elif dist <= 4:
                    self.log(f"💎 Cautiously seeking jackpot... Distance: {dist:.1f}")
                    return self.planner.move_towards(game, jackpot)

        # Priority 4: Fight only if forced and can win decisively
        adjacent = self.perception.is_adjacent_to_monster(game)
        if adjacent:
            if player.hp == player.max_hp and self.decisions.should_fight(game):
                threat = self.get_monster_threat_level(adjacent)
                if threat == 'trivial':
                    self.log(f"⚡ Zapping {adjacent.name}!")
                    return self.planner.move_towards(game, adjacent)
            # Can't win or damaged - flee!
            self.log(f"🔮 Escaping melee with {adjacent.name}!")
            return self.planner.flee_from(game, adjacent)

        # Priority 5: Mine/survey only when completely safe
        nearby_threat = self.perception.monster_in_view(game, distance=8.0)
        if not nearby_threat:
            # Mine valuable ore if safe
            valuable_ore = self.perception.find_valuable_ore(game)
            if valuable_ore:
                dist = player.distance_to(valuable_ore)
                if dist <= 1:
                    if valuable_ore.get_stat('surveyed'):
                        if self.decisions.should_mine_strategically(game, valuable_ore):
                            purity = valuable_ore.get_stat('purity', 0)
                            self.log(f"⛏️  Safe mining: {valuable_ore.ore_type} (purity: {purity})")
                            return ('mine', {})
                    else:
                        self.log(f"🔍 Safe surveying: {valuable_ore.ore_type}")
                        return ('survey', {})

            # Survey nearby ore if safe
            unsurveyed_ore = self.decisions.should_survey_ore(game)
            if unsurveyed_ore:
                dist = player.distance_to(unsurveyed_ore)
                if dist <= 1:
                    self.log(f"🔍 Surveying {unsurveyed_ore.ore_type}...")
                    return ('survey', {})

        # Priority 6: Seek stairs aggressively (Mages don't clear floors)
        # Check if low health (70% threshold for mages seeking stairs)
        if not self.perception.find_nearest_monster(game) or player.hp / player.max_hp < 0.7:
            stairs_pos = self.perception.find_level_exit(game)
            if stairs_pos:
                from core.base.entity import Entity, EntityType
                stairs_entity = Entity(
                    entity_type=EntityType.PLAYER,
                    name="Stairs",
                    x=stairs_pos[0],
                    y=stairs_pos[1],
                )
                self.log("Seeking exit...")
                return self.planner.move_towards(game, stairs_entity)

        # Priority 7: Careful exploration (avoid monsters)
        self.log("🔮 Cautious exploration...")
        return self.planner.get_random_action(game)


if __name__ == "__main__":
    # Run mage bot using shared main() from brogue_bot
    main(bot_class=MageBot, default_class=CharacterClass.MAGE)
