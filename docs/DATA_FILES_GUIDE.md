# Veinborn Data Files Guide

**Last Updated:** 2025-11-05
**For:** Content creators, designers, and modders

---

## Overview

Veinborn uses **YAML files** for all game content, making it easy to add monsters, recipes, and balance the game **without touching code**.

This guide explains every data file, its schema, and how to modify it safely.

---

## 📁 Data File Organization

```
data/
├── entities/          # What things ARE (definitions)
│   ├── monsters.yaml  # Monster stats, behavior, appearance
│   ├── ores.yaml      # Ore types, quality ranges
│   └── items.yaml     # Items (potions, weapons, etc.)
│
└── balance/           # When/where things SPAWN (rules)
    ├── game_constants.yaml    # Core game settings
    ├── recipes.yaml           # Crafting recipes
    ├── loot_tables.yaml       # Monster drop tables
    ├── monster_spawns.yaml    # Spawn rules by floor
    ├── ore_veins.yaml         # Ore spawn rules
    └── forges.yaml            # Forge placement rules
```

**Key Principle:**
- `entities/` = WHAT (definitions)
- `balance/` = WHERE/WHEN/HOW (rules)

---

## 🗂️ File Reference

### Quick Navigation

| File | Purpose | Complexity | Edit Frequency |
|------|---------|------------|----------------|
| [`monsters.yaml`](#monstersyaml) | Monster definitions | ⭐⭐ Medium | High |
| [`recipes.yaml`](#recipesyaml) | Crafting recipes | ⭐⭐⭐ Complex | Medium |
| [`ores.yaml`](#oresyaml) | Ore type definitions | ⭐⭐ Medium | Low |
| [`items.yaml`](#itemsyaml) | Item definitions | ⭐⭐ Medium | Medium |
| [`game_constants.yaml`](#game_constantsyaml) | Core game balance | ⭐ Easy | High |
| [`loot_tables.yaml`](#loot_tablesyaml) | Drop rates | ⭐⭐ Medium | Medium |
| [`monster_spawns.yaml`](#monster_spawnsyaml) | Spawn rules | ⭐ Easy | Medium |
| [`ore_veins.yaml`](#ore_veinsyaml) | Ore spawn rules | ⭐ Easy | Low |
| [`forges.yaml`](#forgesyaml) | Forge placement | ⭐ Easy | Low |

---

## 📄 monsters.yaml

**Path:** `data/entities/monsters.yaml`
**Purpose:** Define what monsters ARE (stats, appearance, behavior)

### Schema

```yaml
monsters:
  monster_id:
    # Display (what player sees)
    name: "Monster Name"
    description: "Flavor text for player"
    symbol: "g"          # Single character
    color: "green"       # Textual color name

    # Core stats
    stats:
      hp: 10             # Hit points
      attack: 5          # Attack power
      defense: 2         # Defense (reduces damage)
      xp_reward: 15      # XP given when killed

    # AI behavior
    ai:
      type: "aggressive"     # aggressive, passive, defensive, fleeing
      move_speed: 1.0        # Movement speed multiplier
      aggro_range: 8         # Detection range (tiles)
      description: "AI behavior notes"

    # Gameplay tags
    tags:
      - "weak"           # For filtering/logic
      - "tutorial"

    # Loot (references loot_tables.yaml)
    loot_table: "goblin"   # null for no drops

    # Design notes (optional)
    notes: |
      Multi-line design notes
      for developers
```

### Example: Adding a New Monster

```yaml
wyvern:
  name: "Wyvern"
  description: "A flying serpent with venomous fangs."
  symbol: "W"
  color: "dark_green"

  stats:
    hp: 80
    attack: 18
    defense: 8
    xp_reward: 200

  ai:
    type: "aggressive"
    move_speed: 1.2  # Faster than player!
    aggro_range: 12  # Spots you from far away
    description: "Fast flying predator"

  tags:
    - "flying"
    - "boss"
    - "floors_7_9"

  loot_table: "elite_enemy"  # Reference to loot_tables.yaml

  notes: |
    Wyvern is designed for floors 7-9.
    High mobility makes it dangerous in open rooms.
    Reward is substantial (200 XP).
```

### Available Colors

```yaml
# Standard colors (Textual color names)
"red", "green", "blue", "yellow", "magenta", "cyan", "white"
"dark_red", "dark_green", "dark_blue", "brown", "purple", "grey"
"copper" (brownish orange), "silver" (light grey)
```

### Testing

```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('data/entities/monsters.yaml'))"

# Run entity loader tests
pytest tests/unit/test_entity_loader.py -v

# Playtest: Run game, check monster spawns on appropriate floors
python3 run_textual.py
```

---

## 📄 recipes.yaml

**Path:** `data/balance/recipes.yaml`
**Purpose:** Define crafting recipes (ore → equipment)

### Schema

```yaml
weapons:  # or armor, accessories
  recipe_id:
    # Display
    display_name: "Item Name"
    description: "Item description"
    symbol: ")"
    color: "silver"
    item_type: "weapon"
    equipment_slot: "weapon"  # weapon, body, head, hands, feet, ring

    # Recipe requirements
    requirements:
      ore_type: "iron"      # copper, iron, mithril, adamantite
      ore_count: 2          # How many ores needed
      min_floor: 4          # Minimum floor to discover/craft
      requires_forge: true  # Must be at forge to craft

    # Stat formulas (evaluated at craft time)
    stat_formulas:
      attack_bonus: "hardness * 0.1 + purity * 0.05"
      defense_bonus: 0
      durability: "malleability * 0.5"
      weight: "density * 0.02"

    # Class bonuses (optional)
    class_bonuses:
      warrior: 1.2  # Warriors get 20% bonus to all stats
      rogue: 1.0
```

### Formula Syntax

**Variables Available:**
- `hardness` (0-100) - Weapon damage, armor defense
- `conductivity` (0-100) - Magic power, spell efficiency
- `malleability` (0-100) - Durability, repair ease
- `purity` (0-100) - Quality multiplier
- `density` (0-100) - Weight, encumbrance

**Operators:**
- `+` `-` `*` `/` - Basic math
- `**` - Power (e.g., `hardness ** 2`)
- `()` - Grouping

**Functions:**
- `avg(a, b, ...)` - Average of values
- `min(a, b)` - Minimum value
- `max(a, b)` - Maximum value

**Examples:**
```yaml
# Simple linear scaling
attack_bonus: "hardness * 0.1"  # hardness=80 → +8 attack

# Quality multiplier
attack_bonus: "hardness * purity / 100"  # hardness=80, purity=90 → +72 attack

# Average of two properties
defense_bonus: "avg(hardness, malleability) * 0.15"

# Complex formula
attack_bonus: "(hardness * 0.15 + conductivity * 0.05) * (purity / 100)"
```

### Example: Adding a New Recipe

```yaml
mithril_sword:
  display_name: "Mithril Longsword"
  description: "A blade forged from legendary mithril ore"
  symbol: ")"
  color: "cyan"
  item_type: "weapon"
  equipment_slot: "weapon"

  requirements:
    ore_type: "mithril"
    ore_count: 2
    min_floor: 7
    requires_forge: true

  stat_formulas:
    attack_bonus: "hardness * 0.15 + purity * 0.1"  # Better than iron!
    defense_bonus: 0
    durability: "malleability * 0.8"  # More durable
    weight: "density * 0.015"  # Lighter than iron

  class_bonuses:
    warrior: 1.2
    rogue: 1.1
    mage: 1.0
    healer: 1.0
```

### Testing Formulas

```bash
# Test formula calculation
python3 -c "hardness=80; purity=90; print('Result:', hardness * 0.15 + purity * 0.1)"

# Run crafting tests
pytest tests/integration/test_equipment_system.py -v

# Playtest: Mine mithril, craft at forge, check stats
python3 run_textual.py
```

---

## 📄 ores.yaml

**Path:** `data/entities/ores.yaml`
**Purpose:** Define ore types and quality ranges

### Schema

```yaml
ore_types:
  ore_id:
    # Display
    name: "Ore Name"
    description: "Flavor text"
    symbol: "~"
    color: "copper"

    # Tier
    tier: 1              # 1=Common, 2=Uncommon, 3=Rare, 4=Legendary
    tier_name: "Common"

    # Floor availability
    floor_range:
      min: 1             # First floor it appears
      max: 3             # Last floor it appears
      optimal: [1, 2, 3] # Best floors for this ore

    # Quality ranges (0-100)
    quality:
      min: 20            # Worst quality
      max: 50            # Best quality
      average: 35        # Typical quality

    # Property ranges (rolled independently)
    properties:
      hardness: [20, 50]
      conductivity: [20, 50]
      malleability: [20, 50]
      purity: [20, 50]
      density: [20, 50]

    # Mining difficulty
    mining:
      base_turns: 3           # Base mining time
      hardness_modifier: true # Higher hardness = more turns

    # Crafting info
    crafting:
      tier: 1
      equipment_level: [1, 3]
```

### Example: Adding a New Ore

```yaml
dragon_ore:
  name: "Dragon Ore"
  description: "Legendary ore infused with dragon essence."
  symbol: "~"
  color: "red"

  tier: 5
  tier_name: "Mythic"

  floor_range:
    min: 15
    max: 20
    optimal: [17, 18, 19]

  quality:
    min: 85
    max: 100
    average: 92

  properties:
    hardness: [85, 100]
    conductivity: [85, 100]
    malleability: [85, 100]
    purity: [90, 100]  # Always high purity!
    density: [85, 100]

  mining:
    base_turns: 8  # Very hard to mine
    hardness_modifier: true

  crafting:
    tier: 5
    equipment_level: [15, 20]
```

---

## 📄 game_constants.yaml

**Path:** `data/balance/game_constants.yaml`
**Purpose:** Core game balance settings

### Key Sections

#### Player Settings
```yaml
player:
  starting_stats:
    hp: 20
    max_hp: 20
    attack: 5
    defense: 2

  progression:
    xp_per_level: 100
    hp_gain_per_level: 5
    attack_gain_per_level: 1
```

#### Combat Settings
```yaml
combat:
  damage_formula: "max(1, attacker_attack - defender_defense)"
  min_damage: 1
  bump_to_attack: true
```

#### Spawning & Difficulty
```yaml
spawning:
  monster_scaling:
    base_count: 2
    floor_divisor: 3  # Add 1 monster every 3 floors

  ore_vein_scaling:
    base_count: 5
    floor_divisor: 5
```

### Common Tweaks

```yaml
# Make game easier
player:
  starting_stats:
    hp: 30  # Was 20
    attack: 7  # Was 5

# Make game harder
spawning:
  monster_scaling:
    base_count: 3  # Was 2
    floor_divisor: 2  # Was 3 (more monsters per floor)

# Faster progression
player:
  progression:
    xp_per_level: 50  # Was 100 (level up faster)
```

---

## 📄 loot_tables.yaml

**Path:** `data/balance/loot_tables.yaml`
**Purpose:** Define what monsters drop when killed

### Schema

```yaml
monster_id:  # Must match monster ID in monsters.yaml
  description: "Drop table description"

  # Each category is rolled independently
  gold:
    drop_chance: 0.70  # 70% chance
    items:
      - id: gold_pile_small
        weight: 80  # 80% of gold drops
        amount_range: [5, 15]
      - id: gold_pile_medium
        weight: 20
        amount_range: [15, 30]

  weapons:
    drop_chance: 0.20  # 20% chance
    items:
      - id: dagger
        weight: 60  # 60% of weapon drops
      - id: short_sword
        weight: 40
```

### Example: Adding Loot Table

```yaml
wyvern:
  description: "Elite enemy - great loot!"

  gold:
    drop_chance: 0.90  # Almost always drops gold
    items:
      - id: gold_pile_large
        weight: 50
        amount_range: [50, 100]
      - id: gold_pile_huge
        weight: 50
        amount_range: [100, 200]

  weapons:
    drop_chance: 0.40  # Good weapon drop rate
    items:
      - id: mithril_sword
        weight: 30
      - id: battle_axe
        weight: 40
      - id: enchanted_bow
        weight: 30

  special:
    drop_chance: 0.10  # 10% chance for rare item
    items:
      - id: legendary_recipe
        weight: 100
```

---

## 📄 monster_spawns.yaml

**Path:** `data/balance/monster_spawns.yaml`
**Purpose:** Control which monsters spawn on which floors

### Schema

```yaml
floors:
  floor_1_3:  # Floor range ID
    floor_range: [1, 3]
    description: "Early game"

    monster_weights:
      goblin: 60   # 60% spawn chance
      rat: 30      # 30% spawn chance
      bat: 10      # 10% spawn chance

    total_weight: 100  # Must sum to 100
```

### Example

```yaml
floors:
  floor_7_9:
    floor_range: [7, 9]
    description: "Mid-game challenge"

    monster_weights:
      orc: 25
      ogre: 25
      wyvern: 30  # New monster!
      troll: 15
      skeleton: 5

    total_weight: 100
```

---

## 🔍 Common Tasks

### Task: Balance Monster Difficulty

**File:** `data/entities/monsters.yaml`

1. Find monster to adjust
2. Modify stats:
   ```yaml
   stats:
     hp: 15  # Increase survivability
     attack: 8  # Increase damage
     defense: 3  # Increase tankiness
   ```
3. Test: `python3 run_textual.py`
4. Fight monster, see if balance feels right

### Task: Add Recipe for New Ore Tier

**File:** `data/balance/recipes.yaml`

1. Copy similar recipe
2. Change ore requirements:
   ```yaml
   requirements:
     ore_type: "dragon_ore"
     ore_count: 3
     min_floor: 15
   ```
3. Adjust stat formulas (higher tier = better multipliers)
4. Test: `pytest tests/integration/test_equipment_system.py`

### Task: Adjust Drop Rates

**File:** `data/balance/loot_tables.yaml`

1. Find monster loot table
2. Adjust drop_chance values:
   ```yaml
   weapons:
     drop_chance: 0.35  # Was 0.20 (now drops more often)
   ```
3. Test: Kill monsters in-game, verify drop rates feel right

---

## ⚠️ Common Mistakes

### 1. Invalid YAML Syntax

```yaml
# ❌ WRONG - Missing colon
name "Goblin"

# ✅ CORRECT
name: "Goblin"
```

### 2. Formula Syntax Errors

```yaml
# ❌ WRONG - Missing multiplication operator
attack_bonus: "hardness 0.1"

# ✅ CORRECT
attack_bonus: "hardness * 0.1"
```

### 3. Mismatched References

```yaml
# In monsters.yaml
loot_table: "wyvern"

# ❌ WRONG - loot_tables.yaml has no 'wyvern' entry

# ✅ CORRECT - Add wyvern entry to loot_tables.yaml
```

### 4. Invalid Weights

```yaml
# ❌ WRONG - Weights don't sum to 100
monster_weights:
  goblin: 60
  orc: 30
# Total: 90 (missing 10)

# ✅ CORRECT
monster_weights:
  goblin: 60
  orc: 30
  bat: 10
```

---

## 🧪 Testing Data Changes

### After Editing monsters.yaml
```bash
pytest tests/unit/test_entity_loader.py -v
python3 run_textual.py  # Playtest monster behavior
```

### After Editing recipes.yaml
```bash
pytest tests/integration/test_equipment_system.py -v
# Playtest: Mine ore, craft item, verify stats
```

### After Editing game_constants.yaml
```bash
pytest tests/ -v  # Run full test suite
python3 run_textual.py  # Verify game behavior
```

### After Editing loot_tables.yaml
```bash
pytest tests/integration/test_loot_drops.py -v
# Playtest: Kill 20 monsters, verify drop rates
```

---

## 🔧 Validation Tools

### Validate YAML Syntax

```bash
# Check single file
python3 -c "import yaml; yaml.safe_load(open('data/entities/monsters.yaml'))"

# Check all data files
for file in data/**/*.yaml; do
  echo "Checking $file..."
  python3 -c "import yaml; yaml.safe_load(open('$file'))"
done
```

### Formula Calculator

```python
# Test recipe formula
python3 << EOF
# Ore properties
hardness = 80
conductivity = 30
malleability = 65
purity = 85
density = 50

# Formula
attack_bonus = hardness * 0.15 + purity * 0.1
print(f"Attack Bonus: +{attack_bonus}")
EOF
```

---

## 📚 Related Documentation

- **CONTENT_CREATION.md** - Step-by-step content creation guide
- **QUICK_REFERENCE.md** - File locations and commands
- **MECHANICS_REFERENCE.md** - Exact game formulas
- **PROJECT_STATUS.md** - What systems are implemented

---

## 💡 Best Practices

1. **Always validate YAML** after editing
2. **Test with appropriate tests** (see Testing sections above)
3. **Playtest your changes** (automated tests don't catch everything)
4. **Keep notes in YAML** (use `notes:` or `description:` fields)
5. **Back up before major changes** (`cp monsters.yaml monsters.yaml.bak`)
6. **Use consistent naming** (snake_case for IDs, Title Case for display names)
7. **Reference existing examples** (copy working entries, then modify)

---

**Happy content creating!** 🎨

Need help? Check **CONTENT_CREATION.md** for step-by-step guides.
