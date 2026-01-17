"""
Game constants and type definitions.

This file contains Enums and type definitions for type safety.
All numeric game balance values have been migrated to YAML configuration files:
- data/balance/game_constants.yaml - Core game constants (player stats, map size, etc.)
- data/balance/formulas.yaml - Game formulas and calculations
- data/entities/monsters.yaml - Monster definitions
- data/entities/ores.yaml - Ore definitions

MIGRATION NOTE (2026-01-13): This file previously contained all hardcoded
game constants. They have been migrated to YAML for easier modding and tuning.
Only type definitions remain here for type safety.
"""

from enum import Enum


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

class MonsterType(Enum):
    """Standard monster types."""
    GOBLIN = "goblin"
    ORC = "orc"
    TROLL = "troll"


class OreType(Enum):
    """Ore types by tier."""
    COPPER = "copper"
    IRON = "iron"
    MITHRIL = "mithril"
    ADAMANTITE = "adamantite"


class AIType(Enum):
    """AI behavior types."""
    PASSIVE = "passive"      # Doesn't attack unless attacked
    AGGRESSIVE = "aggressive"  # Moves toward and attacks player
    DEFENSIVE = "defensive"  # Only attacks if player is adjacent
    FLEEING = "fleeing"      # Runs away from player


# Default AI
DEFAULT_AI_TYPE = AIType.AGGRESSIVE


# ============================================================================
# LEGACY FACTORY METHOD CONSTANTS (Backward Compatibility Only)
# ============================================================================
# These constants are ONLY for backward compatibility with legacy factory methods
# (Monster.create_goblin(), etc.) which are still used in tests.
# NEW CODE SHOULD USE EntityLoader.create_monster() which reads from monsters.yaml
# TODO: Phase out factory methods in favor of EntityLoader

# Goblin stats (weak, tutorial enemy)
GOBLIN_HP = 6
GOBLIN_ATTACK = 3
GOBLIN_DEFENSE = 1
GOBLIN_XP_REWARD = 5

# Orc stats (medium difficulty)
ORC_HP = 12
ORC_ATTACK = 5
ORC_DEFENSE = 2
ORC_XP_REWARD = 15

# Troll stats (hard enemy, unbeatable at level 1)
TROLL_HP = 20
TROLL_ATTACK = 7
TROLL_DEFENSE = 3
TROLL_XP_REWARD = 30


# ============================================================================
# MIGRATION HISTORY
# ============================================================================
# 2026-01-13 (neon-dawn-0113): Constants Migration to YAML
# - Migrated player starting stats → game_constants.yaml (player.starting_stats)
# - Migrated HP regeneration → game_constants.yaml (player.health_regeneration)
# - Migrated inventory max → game_constants.yaml (inventory.max_size)
# - Migrated game progression → game_constants.yaml (progression)
# - Migrated map dimensions → game_constants.yaml (map)
# - Migrated combat constants → game_constants.yaml (combat)
# - Migrated mining constants → formulas.yaml (mining)
# - Migrated message log size → game_constants.yaml (messages.max_size)
# - Migrated debug settings → game_constants.yaml (debug)
# - Monster spawn counts/weights already in YAML (monster_spawns.yaml)
# - Ore spawn counts/weights already in YAML (ores.yaml generation section)
# - Ore quality ranges already in YAML (ores.yaml quality section)
#
# Remaining: Enums for type safety + legacy monster stats for factory methods
