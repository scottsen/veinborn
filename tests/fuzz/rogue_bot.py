#!/usr/bin/env python3
"""
Rogue Bot - Shadowstep the Swift

Agile exploration-focused bot with strategic combat engagement.
Plays as Rogue class with balanced stats and high mobility.

Strategy:
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

from core.game import Game
from core.character_class import CharacterClass
from brogue_bot import BrogueBot, BotStats, main
from fuzz.services.tactical_decision_service import CombatConfig, MiningConfig


class RogueBot(BrogueBot):
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

    def get_smart_action(self, game: Game) -> tuple:
        """
        Rogue decision tree prioritizes exploration and opportunistic combat.

        Uses services but has an exploration-focused priority order:
        1. Descend if ready
        2. Flee if threatened (Rogue survival instinct)
        3. Mine jackpot ore (opportunistic treasure)
        4. Fight only if adjacent and can win
        5. Mine valuable ore (exploration reward)
        6. Survey nearby ore (information gathering)
        7. Pursue weak monsters for XP
        8. Seek stairs
        9. Explore randomly (primary behavior)
        """
        player = game.state.player

        # Priority 1: Descend if ready
        if self.decisions.should_descend(game):
            return ('descend', {})

        # Priority 2: Flee early if threatened (Rogue survival instinct)
        if self.decisions.should_flee(game):
            # Emergency descent if on stairs
            if self.perception.on_stairs(game):
                self.log(f"🏃 Quick escape! (HP: {player.hp}/{player.max_hp})")
                return ('descend', {})

            # Flee to stairs
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
                self.log(f"🏃 Retreating to safety! (HP: {player.hp}/{player.max_hp}, distance: {dist:.1f})")
                return self.planner.move_towards(game, stairs_entity)

            # Flee from nearest threat
            nearby = self.perception.monster_in_view(game, distance=5.0)
            if nearby:
                self.log(f"🏃 Evading {nearby.name}!")
                return self.planner.flee_from(game, nearby)

        # Priority 3: Jackpot ore (opportunistic treasure hunting)
        jackpot = self.perception.find_jackpot_ore(game)
        if jackpot:
            # Check health using config threshold
            if player.hp / player.max_hp > self.decisions.combat_config.health_threshold:
                dist = player.distance_to(jackpot)
                if dist <= 1:
                    self.log(f"💎 JACKPOT! Mining {jackpot.ore_type} (purity: {jackpot.get_stat('purity')})")
                    self.stats.jackpot_ore_found += 1
                    return ('mine', {})
                elif dist <= 6:
                    self.log(f"💎 Pursuing jackpot ore! Distance: {dist:.1f}")
                    return self.planner.move_towards(game, jackpot)

        # Priority 4: Fight only if forced and advantageous
        adjacent = self.perception.is_adjacent_to_monster(game)
        if adjacent:
            # Check health using config threshold
            if player.hp / player.max_hp > self.decisions.combat_config.health_threshold:
                if self.decisions.should_fight(game):
                    threat = self.get_monster_threat_level(adjacent)
                    self.log(f"⚔️  Backstab {adjacent.name} ({threat})!")
                    return self.planner.move_towards(game, adjacent)

        # Priority 5: Mine valuable ore (exploration reward)
        valuable_ore = self.perception.find_valuable_ore(game)
        if valuable_ore:
            # Check health using config threshold
            if player.hp / player.max_hp > self.decisions.combat_config.health_threshold:
                dist = player.distance_to(valuable_ore)
                if dist <= 1:
                    if valuable_ore.get_stat('surveyed'):
                        if self.decisions.should_mine_strategically(game, valuable_ore):
                            purity = valuable_ore.get_stat('purity', 0)
                            self.log(f"⛏️  Mining {valuable_ore.ore_type} (purity: {purity})")
                            return ('mine', {})
                    else:
                        self.log(f"🔍 Surveying {valuable_ore.ore_type}...")
                        return ('survey', {})
                elif dist <= 5 and valuable_ore.get_stat('purity', 0) >= 80:
                    self.log(f"⛏️  Seeking quality ore! Distance: {dist:.1f}")
                    return self.planner.move_towards(game, valuable_ore)

        # Priority 6: Survey nearby ore (information is power)
        unsurveyed_ore = self.decisions.should_survey_ore(game)
        if unsurveyed_ore:
            # Check health using config threshold
            if player.hp / player.max_hp > self.decisions.combat_config.health_threshold:
                dist = player.distance_to(unsurveyed_ore)
                if dist <= 1:
                    self.log(f"🔍 Surveying {unsurveyed_ore.ore_type}...")
                    return ('survey', {})

        # Priority 7: Pursue weak monsters opportunistically
        if self.decisions.should_fight(game):
            nearby = self.perception.monster_in_view(game, distance=4.0)
            if nearby:
                threat = self.get_monster_threat_level(nearby)
                if threat in ['trivial', 'manageable']:
                    dist = player.distance_to(nearby)
                    self.log(f"🎯 Easy target: {nearby.name} ({threat}, distance: {dist:.1f})")
                    return self.planner.move_towards(game, nearby)

        # Priority 8: Floor cleared - seek stairs
        if not self.perception.find_nearest_monster(game):
            stairs_pos = self.perception.find_level_exit(game)
            if stairs_pos:
                from core.base.entity import Entity, EntityType
                stairs_entity = Entity(
                    entity_type=EntityType.PLAYER,
                    name="Stairs",
                    x=stairs_pos[0],
                    y=stairs_pos[1],
                )
                self.log("Floor cleared! Seeking exit!")
                return self.planner.move_towards(game, stairs_entity)

        # Priority 9: Explore (Rogue primary behavior)
        self.log("🗺️  Exploring...")
        return self.planner.get_random_action(game)


if __name__ == "__main__":
    # Run rogue bot using shared main() from brogue_bot
    main(bot_class=RogueBot, default_class=CharacterClass.ROGUE)
