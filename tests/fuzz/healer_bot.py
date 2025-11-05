#!/usr/bin/env python3
"""
Healer Bot - Lifebinder the Steadfast

Defensive survival specialist focused on sustainability and patience.
Plays as Healer class with high defense and support abilities.

Strategy:
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

from core.game import Game
from core.character_class import CharacterClass
from brogue_bot import BrogueBot, BotStats, main
from fuzz.services.tactical_decision_service import CombatConfig, MiningConfig


class HealerBot(BrogueBot):
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

    def get_smart_action(self, game: Game) -> tuple:
        """
        Healer decision tree prioritizes sustainable, defensive play.

        Uses services but has a defensive, methodical priority order:
        1. Descend if floor cleared (patient progression)
        2. Fight adjacent enemies (defensive stance)
        3. Flee only if critically endangered
        4. Mine jackpot ore (worthwhile opportunity)
        5. Engage manageable monsters (steady XP)
        6. Mine/survey resources (patient gathering)
        7. Seek and clear remaining monsters (methodical)
        8. Seek stairs when done
        9. Patient exploration
        """
        player = game.state.player

        # Priority 1: Descend when floor is properly cleared
        if self.decisions.should_descend(game):
            monsters_alive = len(self.perception.find_monsters(game))
            self.log(f"✨ Floor cleared ({monsters_alive} monsters)! Descending!")
            return ('descend', {})

        # Priority 2: Fight adjacent enemies (defensive stance)
        adjacent = self.perception.is_adjacent_to_monster(game)
        if adjacent:
            if self.decisions.should_fight(game):
                threat = self.get_monster_threat_level(adjacent)
                self.log(f"🛡️  Defending against {adjacent.name} ({threat})!")
                return self.planner.move_towards(game, adjacent)
            elif player.hp / player.max_hp < 0.25:
                # Critical health - flee
                self.log(f"🚨 Critically wounded! Retreating from {adjacent.name}!")
                return self.planner.flee_from(game, adjacent)
            else:
                # Can't win but not critical - maintain distance
                self.log(f"⚠️  Strong opponent {adjacent.name}! Repositioning!")
                return self.planner.flee_from(game, adjacent)

        # Priority 3: Flee if critically endangered
        if self.decisions.should_flee(game):
            stairs_pos = self.perception.find_level_exit(game)
            if stairs_pos and self.perception.on_stairs(game):
                self.log(f"🚨 Emergency descent! (HP: {player.hp}/{player.max_hp})")
                return ('descend', {})

            if stairs_pos:
                from core.base.entity import Entity, EntityType
                stairs_entity = Entity(
                    entity_type=EntityType.PLAYER,
                    name="Stairs",
                    x=stairs_pos[0],
                    y=stairs_pos[1],
                )
                dist = player.distance_to(stairs_entity)
                self.log(f"🛡️  Seeking sanctuary! (HP: {player.hp}/{player.max_hp}, distance: {dist:.1f})")
                return self.planner.move_towards(game, stairs_entity)

            nearby = self.perception.monster_in_view(game, distance=5.0)
            if nearby:
                self.log(f"🛡️  Tactical retreat from {nearby.name}!")
                return self.planner.flee_from(game, nearby)

        # Priority 4: Jackpot ore (always good value)
        jackpot = self.perception.find_jackpot_ore(game)
        if jackpot:
            # Check health (50% threshold for mining)
            if player.hp / player.max_hp > 0.5:
                dist = player.distance_to(jackpot)
                if dist <= 1:
                    self.log(f"💎 JACKPOT! Mining {jackpot.ore_type} (purity: {jackpot.get_stat('purity')})")
                    self.stats.jackpot_ore_found += 1
                    return ('mine', {})
                elif dist <= 5:
                    self.log(f"💎 Seeking jackpot ore! Distance: {dist:.1f}")
                    return self.planner.move_towards(game, jackpot)

        # Priority 5: Engage manageable monsters (steady progression)
        if self.decisions.should_fight(game):
            nearby = self.perception.monster_in_view(game, distance=5.0)
            if nearby:
                dist = player.distance_to(nearby)
                threat = self.get_monster_threat_level(nearby)
                self.log(f"🛡️  Methodically engaging {nearby.name} ({threat}, distance: {dist:.1f})")
                return self.planner.move_towards(game, nearby)

        # Priority 6: Mine valuable ore (patient resource gathering)
        valuable_ore = self.perception.find_valuable_ore(game)
        if valuable_ore:
            # Check health using config threshold
            if player.hp / player.max_hp > self.decisions.combat_config.health_threshold:
                dist = player.distance_to(valuable_ore)
                if dist <= 1:
                    if valuable_ore.get_stat('surveyed'):
                        if self.decisions.should_mine_strategically(game, valuable_ore):
                            purity = valuable_ore.get_stat('purity', 0)
                            self.log(f"⛏️  Patiently mining {valuable_ore.ore_type} (purity: {purity})")
                            return ('mine', {})
                    else:
                        self.log(f"🔍 Surveying {valuable_ore.ore_type}...")
                        return ('survey', {})
                elif dist <= 4 and valuable_ore.get_stat('purity', 0) >= 80:
                    self.log(f"⛏️  Seeking quality ore! Distance: {dist:.1f}")
                    return self.planner.move_towards(game, valuable_ore)

        # Survey nearby ore
        unsurveyed_ore = self.decisions.should_survey_ore(game)
        if unsurveyed_ore:
            # Check health using config threshold
            if player.hp / player.max_hp > self.decisions.combat_config.health_threshold:
                dist = player.distance_to(unsurveyed_ore)
                if dist <= 1:
                    self.log(f"🔍 Surveying {unsurveyed_ore.ore_type}...")
                    return ('survey', {})

        # Priority 7: Seek remaining monsters (methodical clearing)
        nearest = self.perception.find_nearest_monster(game)
        if nearest:
            dist = player.distance_to(nearest)
            threat = self.get_monster_threat_level(nearest)
            self.log(f"🔍 Methodically seeking {nearest.name} ({threat}, distance: {dist:.1f})")
            return self.planner.move_towards(game, nearest)

        # Priority 8: Floor cleared - seek stairs
        stairs_pos = self.perception.find_level_exit(game)
        if stairs_pos:
            from core.base.entity import Entity, EntityType
            stairs_entity = Entity(
                entity_type=EntityType.PLAYER,
                name="Stairs",
                x=stairs_pos[0],
                y=stairs_pos[1],
            )
            self.log("✨ Floor cleared! Seeking stairs!")
            return self.planner.move_towards(game, stairs_entity)

        # Priority 9: Patient exploration
        self.log("🛡️  Steady exploration...")
        return self.planner.get_random_action(game)


if __name__ == "__main__":
    # Run healer bot using shared main() from brogue_bot
    main(bot_class=HealerBot, default_class=CharacterClass.HEALER)
