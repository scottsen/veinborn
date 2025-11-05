"""
Game constants and balance values.

All magic numbers should be defined here for easy tuning.
This file contains hard-coded values that will eventually
move to YAML configuration files in Phase 1.2.

Note: Values with rationale comments explain game design decisions.
"""

from enum import Enum


# ============================================================================
# PLAYER STATS
# ============================================================================

# Starting stats
PLAYER_STARTING_HP = 20
PLAYER_STARTING_ATTACK = 5
PLAYER_STARTING_DEFENSE = 2

# Progression
XP_PER_LEVEL_MULTIPLIER = 100  # Level 2 needs 100 XP, Level 3 needs 200 XP
HP_GAIN_PER_LEVEL = 5
ATTACK_GAIN_PER_LEVEL = 1
DEFENSE_GAIN_PER_LEVEL = 1

# Health regeneration
HP_REGEN_INTERVAL_TURNS = 10  # Regenerate every N turns
HP_REGEN_AMOUNT = 1  # HP restored per regeneration tick


# ============================================================================
# INVENTORY
# ============================================================================

MAX_INVENTORY_SIZE = 20


# ============================================================================
# GAME PROGRESSION
# ============================================================================

STARTING_FLOOR = 1
VICTORY_FLOOR = 100  # Reach floor 100 to win!


# ============================================================================
# MAP GENERATION
# ============================================================================

DEFAULT_MAP_WIDTH = 80
DEFAULT_MAP_HEIGHT = 24


# ============================================================================
# COMBAT
# ============================================================================

# Damage calculation: max(1, attacker_attack - defender_defense)
MIN_DAMAGE = 1


# ============================================================================
# MONSTER SPAWNING
# ============================================================================

# Monster counts by floor range
# Format: (min_floor, max_floor, base_count, scale_formula)

# Floors 1-6: Gentle introduction (3-6 monsters)
FLOOR_RANGE_EARLY = (1, 6)
EARLY_MONSTER_BASE_COUNT = 3
EARLY_MONSTER_SCALE_DIVISOR = 2  # count = 3 + (floor // 2)

# Floors 7-20: Medium difficulty (5-11 monsters)
FLOOR_RANGE_MEDIUM = (7, 20)
MEDIUM_MONSTER_BASE_COUNT = 5
MEDIUM_MONSTER_SCALE_DIVISOR = 3  # count = 5 + (floor // 3)

# Floors 21+: Hard difficulty (caps at 12)
FLOOR_RANGE_HARD = 21
HARD_MONSTER_BASE_COUNT = 8
HARD_MONSTER_SCALE_DIVISOR = 10  # count = min(12, 8 + (floor // 10))
MAX_MONSTERS_PER_FLOOR = 12


# ============================================================================
# MONSTER TYPES AND STATS
# ============================================================================

class MonsterType(Enum):
    """Standard monster types"""
    GOBLIN = "goblin"
    ORC = "orc"
    TROLL = "troll"


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
# MONSTER SPAWN WEIGHTS BY FLOOR
# ============================================================================
# Note: These will move to YAML in Phase 1.2

# Floor 1: 100% Goblins (tutorial)
FLOOR_1_GOBLIN_WEIGHT = 100
FLOOR_1_ORC_WEIGHT = 0
FLOOR_1_TROLL_WEIGHT = 0

# Floor 2: 67% Goblins, 33% Orcs
FLOOR_2_GOBLIN_MODULO = 3  # if i % 3 != 0
FLOOR_2_ORC_MODULO = 3     # if i % 3 == 0

# Floors 3-5: 50% Goblins, 40% Orcs, 10% Trolls
FLOORS_3_5_TROLL_MODULO = 10  # if i % 10 == 0
FLOORS_3_5_ORC_MODULO = 5     # elif i % 5 < 2
# else: Goblin

# Floors 6-10: Balanced 33/33/33 mix
FLOORS_6_10_DISTRIBUTION_MODULO = 3

# Floors 11+: 66% Trolls, 33% Orcs
FLOORS_11_PLUS_ORC_MODULO = 3  # if i % 3 == 0
# else: Troll


# ============================================================================
# ORE VEINS
# ============================================================================

# Ore vein counts
BASE_ORE_VEIN_COUNT = 8  # Floor 1 starts with 8 veins
# Additional veins per floor: ore_count = 8 + (floor - 1)

# Ore quality ranges (0-100 scale)
ORE_QUALITY_MIN = 0
ORE_QUALITY_MAX = 100

# Ore properties
ORE_PROPERTY_HARDNESS = "hardness"
ORE_PROPERTY_CONDUCTIVITY = "conductivity"
ORE_PROPERTY_MALLEABILITY = "malleability"
ORE_PROPERTY_PURITY = "purity"
ORE_PROPERTY_DENSITY = "density"


class OreType(Enum):
    """Ore types by tier"""
    COPPER = "copper"
    IRON = "iron"
    MITHRIL = "mithril"
    ADAMANTITE = "adamantite"


# Ore tier distribution by floor
# Floors 1-3: Mostly copper
ORE_TIER_1_MAX_FLOOR = 3
ORE_TIER_1_COPPER_WEIGHT = 3
ORE_TIER_1_IRON_WEIGHT = 1

# Floors 4-6: Mostly iron
ORE_TIER_2_MAX_FLOOR = 6
ORE_TIER_2_IRON_WEIGHT = 3
ORE_TIER_2_MITHRIL_WEIGHT = 1

# Floors 7+: Mithril and Adamantite
ORE_TIER_3_MITHRIL_WEIGHT = 2
ORE_TIER_3_ADAMANTITE_WEIGHT = 1

# Ore quality ranges by tier
COPPER_QUALITY_MIN = 20
COPPER_QUALITY_MAX = 50

IRON_QUALITY_MIN = 40
IRON_QUALITY_MAX = 70

MITHRIL_QUALITY_MIN = 60
MITHRIL_QUALITY_MAX = 90

ADAMANTITE_QUALITY_MIN = 80
ADAMANTITE_QUALITY_MAX = 100


# ============================================================================
# MINING
# ============================================================================

# Multi-turn mining durations
MINING_MIN_TURNS = 3
MINING_MAX_TURNS = 5

# Legacy ore (survives death)
LEGACY_ORE_PURITY_THRESHOLD = 80  # Ore with 80+ purity saved to vault


# ============================================================================
# AI TYPES
# ============================================================================

class AIType(Enum):
    """AI behavior types"""
    PASSIVE = "passive"      # Doesn't attack unless attacked
    AGGRESSIVE = "aggressive"  # Moves toward and attacks player
    DEFENSIVE = "defensive"  # Only attacks if player is adjacent
    FLEEING = "fleeing"      # Runs away from player


# Default AI
DEFAULT_AI_TYPE = AIType.AGGRESSIVE


# ============================================================================
# MESSAGE LOG
# ============================================================================

MAX_MESSAGE_LOG_SIZE = 100  # Keep last 100 messages


# ============================================================================
# DEBUG
# ============================================================================

# Enable debug mode features
DEBUG_MODE = False

# Show detailed entity info
DEBUG_SHOW_ENTITY_IDS = False

# Log all action executions
DEBUG_LOG_ACTIONS = True
