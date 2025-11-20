#!/usr/bin/env python3
"""
Warrior Bot - Grimbash the Unstoppable

Aggressive melee-focused bot that seeks combat and tanks damage.
Plays as Warrior class with high HP and attack.

Strategy:
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

from core.game import Game
from core.character_class import CharacterClass
from veinborn_bot import BrogueBot, BotStats, main
from fuzz.services.tactical_decision_service import CombatConfig, MiningConfig


class WarriorBot(BrogueBot):
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

    def get_smart_action(self, game: Game) -> tuple:
        """
        Warrior decision tree: Combat-first, but mines when safe.

        Priority order:
        0. Continue active mining (if already started)
        1. Descend if ready
        2. Fight adjacent enemies (forced combat)
        3. Pursue visible monsters within 7 tiles (aggressive)
        4. Opportunistic mining (purity 50+, monsters >5 tiles away)
        5. Flee if critically wounded (<15% HP)
        6. Survey adjacent ore (when safe)
        7. Hunt distant monsters (within 15 tiles)
        8. Survey remaining unsurveyed ore (before descent)
        9. Mine valuable surveyed ore (before descent)
        10. Seek stairs (only after mining done)
        11. Explore randomly
        """
        player = game.state.player

        # Priority 0: Continue active mining (multi-turn action)
        mining_state = player.get_stat('mining_action')
        if mining_state and mining_state.get('turns_remaining', 0) > 0:
            turns_left = mining_state.get('turns_remaining', 0)
            self.log(f"⛏️  Finishing mining... {turns_left} turns remaining")
            return ('mine', {})

        # Priority 1: Descend if ready
        if self.decisions.should_descend(game):
            return ('descend', {})

        # Priority 2: Forced combat (monster adjacent)
        adjacent = self.perception.is_adjacent_to_monster(game)
        if adjacent:
            threat = self.get_monster_threat_level(adjacent)
            self.log(f"⚔️  GRIMBASH ATTACKS {adjacent.name} ({threat})!")
            return self.planner.move_towards(game, adjacent)

        # Priority 3: SEEK COMBAT (Warriors are aggressive)
        if self.decisions.should_fight(game):
            nearby = self.perception.monster_in_view(game, distance=7.0)
            if nearby:
                dist = player.distance_to(nearby)
                self.log(f"🗡️  Charging {nearby.name}! (distance: {dist:.1f})")
                return self.planner.move_towards(game, nearby)

        # Priority 4: OPPORTUNISTIC MINING (no immediate threats)
        # Warriors actively seek valuable ore when no monsters nearby (>5 tiles)
        # Combat still takes priority, but will grab good ore when safe
        if not self.decisions.is_low_health(game):
            nearest_monster = self.perception.find_nearest_monster(game)
            monster_dist = player.distance_to(nearest_monster) if nearest_monster else 999

            if monster_dist > 5:
                # Try for perfect jackpot first (all properties 80+)
                jackpot = self.perception.find_jackpot_ore(game)
                if jackpot:
                    if player.is_adjacent(jackpot):
                        purity = jackpot.get_stat('purity', 0)
                        self.log(f"💎 GRIMBASH MINES PERFECT JACKPOT! Purity: {purity}")
                        return ('mine', {})
                    else:
                        dist = player.distance_to(jackpot)
                        if dist <= 5:
                            self.log(f"💎 Moving to jackpot ore (purity: {jackpot.get_stat('purity', 0)})")
                            return self.planner.move_towards_adjacent(game, jackpot)

                # Fallback: Seek and mine valuable ore (50+ purity = top 30% quality)
                # When coast is clear (monsters >5 tiles), actively seek good ore
                ore_veins = self.perception.find_ore_veins(game)
                valuable_ore = [ore for ore in ore_veins
                               if ore.get_stat('surveyed') and ore.get_stat('purity', 0) >= 50]

                if valuable_ore:
                    # Find closest valuable ore
                    closest_ore = min(valuable_ore, key=lambda o: player.distance_to(o))
                    dist = player.distance_to(closest_ore)

                    if player.is_adjacent(closest_ore):
                        purity = closest_ore.get_stat('purity', 0)
                        self.log(f"⛏️  GRIMBASH MINES VALUABLE ORE! Purity: {purity}")
                        return ('mine', {})
                    elif dist <= 10:
                        # Seek nearby valuable ore when safe
                        purity = closest_ore.get_stat('purity', 0)
                        self.log(f"⛏️  Seeking valuable ore! Purity: {purity}, Distance: {dist:.1f}")
                        return self.planner.move_towards_adjacent(game, closest_ore)

        # Priority 5: Flee only if critically wounded
        if player.hp / player.max_hp < 0.15:
            stairs_pos = self.perception.find_level_exit(game)
            if stairs_pos and self.perception.on_stairs(game):
                self.log(f"🚨 Emergency retreat! (HP: {player.hp}/{player.max_hp})")
                return ('descend', {})

            if stairs_pos:
                from core.base.entity import Entity, EntityType
                stairs_entity = Entity(
                    entity_type=EntityType.PLAYER,
                    name="Stairs",
                    x=stairs_pos[0],
                    y=stairs_pos[1],
                )
                self.log(f"💀 Retreating to stairs! (HP: {player.hp}/{player.max_hp})")
                return self.planner.move_towards(game, stairs_entity)

        # Priority 6: Survey ore when exploring (to find valuable ore)
        # Only when no monsters nearby (>5 tiles) - stay combat-ready
        nearest_monster = self.perception.find_nearest_monster(game)
        monster_dist = player.distance_to(nearest_monster) if nearest_monster else 999
        if monster_dist > 5:
            unsurveyed = self.perception.find_unsurveyed_ore_nearby(game, max_distance=2.0)
            if unsurveyed and player.is_adjacent(unsurveyed):
                self.log(f"🔍 Surveying ore while exploring")
                return ('survey', {})

        # Priority 7: Seek nearest monster (only if close enough)
        # Don't hunt monsters that are too far - allow mining when monsters are distant
        nearest = self.perception.find_nearest_monster(game)
        if nearest:
            dist = player.distance_to(nearest)
            # Only actively hunt if monster is within reasonable range (15 tiles)
            # Beyond that, prioritize mining/exploration
            if dist <= 15:
                self.log(f"🔍 Hunting {nearest.name} (distance: {dist:.1f})")
                return self.planner.move_towards(game, nearest)

        # Priority 8: Mine/survey remaining unsurveyed ore before descending
        # Once floor is cleared, check for any ore worth investigating
        unsurveyed = self.perception.find_unsurveyed_ore_nearby(game, max_distance=20.0)
        if unsurveyed:
            if player.is_adjacent(unsurveyed):
                self.log(f"🔍 Surveying remaining ore before descent")
                return ('survey', {})
            else:
                self.log(f"🔍 Checking unsurveyed ore before descent (dist: {player.distance_to(unsurveyed):.1f})")
                return self.planner.move_towards_adjacent(game, unsurveyed)

        # Priority 9: Mine valuable surveyed ore before descending
        ore_veins = self.perception.find_ore_veins(game)
        valuable_ore = [ore for ore in ore_veins
                       if ore.get_stat('surveyed') and ore.get_stat('purity', 0) >= 50]
        if valuable_ore:
            closest_ore = min(valuable_ore, key=lambda o: player.distance_to(o))
            if player.is_adjacent(closest_ore):
                purity = closest_ore.get_stat('purity', 0)
                self.log(f"⛏️  Mining valuable ore before descent! Purity: {purity}")
                return ('mine', {})
            else:
                purity = closest_ore.get_stat('purity', 0)
                dist = player.distance_to(closest_ore)
                self.log(f"⛏️  Seeking valuable ore before descent! Purity: {purity}, Distance: {dist:.1f}")
                return self.planner.move_towards_adjacent(game, closest_ore)

        # Priority 10: Floor cleared - seek stairs (only after mining done)
        stairs_pos = self.perception.find_level_exit(game)
        if stairs_pos:
            from core.base.entity import Entity, EntityType
            stairs_entity = Entity(
                entity_type=EntityType.PLAYER,
                name="Stairs",
                x=stairs_pos[0],
                y=stairs_pos[1],
            )
            self.log("Floor cleared! Seeking stairs!")
            return self.planner.move_towards(game, stairs_entity)

        # Priority 9: Random exploration
        return self.planner.get_random_action(game)


if __name__ == "__main__":
    # Run warrior bot using shared main() from veinborn_bot
    main(bot_class=WarriorBot, default_class=CharacterClass.WARRIOR)
