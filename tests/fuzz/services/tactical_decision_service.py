"""
TacticalDecisionService - Makes tactical decisions based on perception.

Responsibility: Answer "What should I do?"
- Make decisions based on perception data
- Use configuration for customization
- No logging (decisions, not reporting)
- Stateless except for configuration

Phase 2 Service Extraction - Step 2
"""

import logging
from typing import Optional
from dataclasses import dataclass

# Configure logger for buffered I/O (5-10% performance improvement in verbose mode)
logger = logging.getLogger(__name__)


@dataclass
class CombatConfig:
    """Configuration for combat decisions."""
    health_threshold: float = 0.3      # When is health "low"?
    safety_margin: float = 1.5         # Combat win calculation multiplier
    engagement_range: float = 5.0      # How far to pursue enemies
    flee_priority: int = 6             # Priority in decision tree


@dataclass
class MiningConfig:
    """Configuration for mining decisions."""
    min_purity: int = 50               # Minimum purity worth mining (top 30% quality)
    jackpot_purity: int = 80           # Drop everything for this (Legacy Vault quality)
    survey_distance: float = 3.0       # How far to seek unsurveyed ore
    max_survey_distance: float = 2.0  # How close for surveying


class TacticalDecisionService:
    """Makes tactical decisions based on perception and configuration."""

    def __init__(
        self,
        perception,  # PerceptionService
        combat_config: Optional[CombatConfig] = None,
        mining_config: Optional[MiningConfig] = None,
        verbose: bool = False
    ):
        """
        Initialize tactical decision service.

        Args:
            perception: PerceptionService instance
            combat_config: Combat decision configuration
            mining_config: Mining decision configuration
            verbose: Enable verbose decision logging
        """
        self.perception = perception
        self.combat_config = combat_config or CombatConfig()
        self.mining_config = mining_config or MiningConfig()
        self.verbose = verbose

    # ========================================================================
    # Health Assessment
    # ========================================================================

    def is_low_health(self, game, threshold: Optional[float] = None) -> bool:
        """
        Check if player health is below threshold.

        Args:
            game: Game instance
            threshold: Health threshold (uses config if not provided)

        Returns:
            True if health is below threshold
        """
        if threshold is None:
            threshold = self.combat_config.health_threshold

        player = game.state.player
        if player.max_hp == 0:
            return True
        return (player.hp / player.max_hp) < threshold

    # ========================================================================
    # Combat Decisions
    # ========================================================================

    def can_win_fight(self, game, monster) -> bool:
        """
        Estimate if player can win fight against monster.

        Uses safety margin from config for risk assessment.

        Args:
            game: Game instance
            monster: Monster entity

        Returns:
            True if estimated to win fight
        """
        player = game.state.player

        # Calculate effective power (attack - enemy defense)
        player_power = max(1, player.attack - monster.defense)
        monster_power = max(1, monster.attack - player.defense)

        # Estimate turns to kill each other
        turns_to_kill_monster = max(1, monster.hp / player_power)
        turns_to_die = max(1, player.hp / monster_power)

        # Can win if we kill them before they kill us (with safety margin)
        can_win = turns_to_kill_monster < (turns_to_die * self.combat_config.safety_margin)

        if self.verbose:
            logger.debug(f"can_win_fight vs {monster.name}: {can_win} "
                  f"(kill={turns_to_kill_monster:.1f} vs die={turns_to_die:.1f}*{self.combat_config.safety_margin})")

        return can_win

    def should_fight(self, game) -> bool:
        """
        Decide whether to engage in combat.

        Returns True if:
        - Monster is adjacent (forced combat)
        - We're at good health and can win
        - Within engagement range

        Args:
            game: Game instance

        Returns:
            True if should engage in combat
        """
        player = game.state.player
        monster = self.perception.is_adjacent_to_monster(game)
        if monster:
            # Already in melee - must fight!
            if self.verbose:
                logger.debug(f" should_fight: True (forced - {monster.name} adjacent)")
            return True

        nearby = self.perception.monster_in_view(game, distance=self.combat_config.engagement_range)
        if not nearby:
            if self.verbose:
                logger.debug(f" should_fight: False (no monsters in range {self.combat_config.engagement_range})")
            return False

        # Don't fight if low health
        if self.is_low_health(game):
            if self.verbose:
                logger.debug(f" should_fight: False (low HP: {player.hp}/{player.max_hp})")
            return False

        # Fight if we estimate we can win
        can_win = self.can_win_fight(game, nearby)
        if self.verbose and can_win:
            logger.debug(f" should_fight: True (can win vs {nearby.name})")
        return can_win

    def should_flee(self, game) -> bool:
        """
        Decide whether to flee from combat.

        Returns True if:
        - Low health and monster nearby
        - Can't win the fight

        Args:
            game: Game instance

        Returns:
            True if should flee
        """
        player = game.state.player
        nearby = self.perception.monster_in_view(game, distance=self.combat_config.engagement_range)
        if not nearby:
            if self.verbose:
                logger.debug(f" should_flee: False (no monsters nearby)")
            return False

        # Flee if low health and monster nearby
        if self.is_low_health(game):
            if self.verbose:
                logger.debug(f" should_flee: True (low HP: {player.hp}/{player.max_hp}, {nearby.name} nearby)")
            return True

        # Flee if we can't win
        if not self.can_win_fight(game, nearby):
            if self.verbose:
                logger.debug(f" should_flee: True (cannot win vs {nearby.name})")
            return True

        if self.verbose:
            logger.debug(f" should_flee: False (HP good, can win)")
        return False

    # ========================================================================
    # Mining Decisions
    # ========================================================================

    def should_mine_strategically(self, game, ore_vein) -> bool:
        """
        Decide if this ore is worth mining NOW vs later.

        Uses config thresholds for quality assessment.

        Rules:
        - Always mine Legacy Vault quality (80+ purity)
        - Mine high quality if safe (70+)
        - Skip low-quality ore (<min_purity)

        Args:
            game: Game instance
            ore_vein: Ore vein entity

        Returns:
            True if should mine this ore
        """
        if not ore_vein.get_stat('surveyed'):
            # Can't assess quality without surveying first
            return False

        purity = ore_vein.get_stat('purity', 0)

        # Always mine Legacy Vault quality (80+)
        if purity >= 80:
            return True

        # Mine high quality if safe (>= min_purity)
        if purity >= self.mining_config.min_purity and not self.is_low_health(game):
            return True

        # Skip low-quality ore
        return False

    def should_survey_ore(self, game) -> Optional:
        """
        Check if there's unsurveyed ore nearby worth surveying.

        Uses config max_survey_distance for range.

        Args:
            game: Game instance

        Returns:
            Ore entity to survey, or None
        """
        ore_veins = self.perception.find_ore_veins(game)

        # Find unsurveyed ore within range
        unsurveyed = [
            ore for ore in ore_veins
            if not ore.get_stat('surveyed')
            and game.state.player.distance_to(ore) <= self.mining_config.max_survey_distance
        ]

        if unsurveyed:
            return min(unsurveyed, key=lambda o: game.state.player.distance_to(o))

        return None

    # ========================================================================
    # Progression Decisions
    # ========================================================================

    def should_descend(self, game) -> bool:
        """
        Decide whether to descend to next floor.

        Returns True if:
        - Standing on stairs
        - Floor cleared OR good health (allows escaping unreachable monsters)

        Args:
            game: Game instance

        Returns:
            True if should descend
        """
        # Must be on stairs
        if not self.perception.on_stairs(game):
            return False

        # Check if floor is cleared
        monsters_alive = len(self.perception.find_monsters(game))
        player = game.state.player

        # Descend if floor cleared
        if monsters_alive == 0:
            if self.verbose:
                logger.debug(f" should_descend: True (floor cleared)")
            return True

        # Descend anyway if HP is good (escape unreachable monsters)
        # Use 0.5 threshold (more lenient than combat threshold)
        if not self.is_low_health(game, threshold=0.5):
            if self.verbose:
                logger.debug(f" should_descend: True ({monsters_alive} monsters remain, but HP good: {player.hp}/{player.max_hp})")
            return True

        # Low health + monsters alive = don't descend
        if self.verbose:
            logger.debug(f" should_descend: False ({monsters_alive} monsters remain, HP: {player.hp}/{player.max_hp})")
        return False

    # ========================================================================
    # Crafting Decisions
    # ========================================================================

    def should_craft(self, game) -> bool:
        """
        Decide if bot should prioritize crafting.

        Craft if:
        - Have craftable ore
        - Forge exists on this floor
        - Not in immediate danger

        Args:
            game: Game instance

        Returns:
            True if should prioritize crafting
        """
        if self.is_low_health(game):
            return False

        if self.perception.is_adjacent_to_monster(game):
            return False

        craftable = self.perception.has_craftable_ore(game)
        if not craftable:
            return False

        # Check if there's a forge on this floor
        forge = self.perception.find_nearest_forge(game)
        if not forge:
            return False

        # Prioritize crafting regardless of distance - better gear is worth the walk!
        # (Previously limited to distance <= 8, which was too restrictive)
        return True
