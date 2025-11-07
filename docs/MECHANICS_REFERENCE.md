# Brogue Mechanics Reference

**Last Updated:** 2025-11-05
**For:** Balance tuning, playtesting, and understanding exact game mechanics

---

## Overview

This document contains **exact formulas** for all game mechanics. Use this for:
- Balance tuning
- Playtesting verification
- Understanding "why did that happen?"
- Content creation

---

## ⚔️ Combat Mechanics

### Damage Calculation

**Formula:**
```python
damage = max(1, attacker_attack - defender_defense)
```

**Details:**
- **Attacker Attack** = Base Attack + Equipment Bonuses
- **Defender Defense** = Base Defense + Equipment Bonuses
- **Minimum Damage** = 1 (always deal at least 1 damage)

**Example 1: Player vs Goblin**
```
Player:
  Base Attack: 5
  Weapon Bonus: +12 (Iron Sword)
  Total Attack: 17

Goblin:
  Defense: 1

Damage = max(1, 17 - 1) = 16 damage
```

**Example 2: Goblin vs Player**
```
Goblin:
  Attack: 3

Player:
  Base Defense: 2
  Armor Bonus: +5 (Iron Armor)
  Total Defense: 7

Damage = max(1, 3 - 7) = max(1, -4) = 1 damage (minimum)
```

**Example 3: Equal Match**
```
Orc Attack: 5
Player Defense: 5

Damage = max(1, 5 - 5) = 1 damage (minimum guarantees progress)
```

### Equipment Bonuses

**Player Stats Calculation:**
```python
# Attack
total_attack = base_attack + weapon.attack_bonus

# Defense
total_defense = base_defense + armor.defense_bonus + shield.defense_bonus
```

**Equipment Slots:**
- **Weapon:** Adds `attack_bonus`
- **Body Armor:** Adds `defense_bonus`
- **Shield:** Adds `defense_bonus`
- **Ring/Accessories:** Adds misc bonuses

**Example:**
```
Player Base Stats:
  Attack: 5
  Defense: 2

Equipped:
  Iron Sword: +12 attack
  Iron Armor: +8 defense

Final Stats:
  Total Attack: 5 + 12 = 17
  Total Defense: 2 + 8 = 10
```

### Death and XP

**Death Detection:**
```python
if entity.hp <= 0:
    entity.is_alive = False
```

**XP Award:**
```python
xp_gained = monster.xp_reward  # Defined in monsters.yaml
player.xp += xp_gained

# Level up check
if player.xp >= (player.level * 100):
    player.level_up()
```

**Leveling Formula:**
```
XP needed for level N = N * 100

Level 1 → 2: 100 XP
Level 2 → 3: 200 XP
Level 3 → 4: 300 XP
```

**Level Up Bonuses:**
```
HP: +5 per level
Attack: +1 per level
Defense: +1 per level
```

---

## ⛏️ Mining Mechanics

### Mining Time Calculation

**Formula:**
```python
base_turns = ore_type.base_mining_turns  # From ores.yaml
hardness_modifier = ore.properties['hardness'] // 25
total_turns = base_turns + hardness_modifier
```

**By Ore Type:**
```
Copper:   base_turns = 3
Iron:     base_turns = 3
Mithril:  base_turns = 4
Adamantite: base_turns = 5
```

**Example: Mining Iron Ore**
```
Iron Ore Properties:
  hardness: 78

Calculation:
  base_turns = 3 (iron)
  hardness_modifier = 78 // 25 = 3
  total_turns = 3 + 3 = 6 turns

Result: Player must mine for 6 turns to complete
```

**Hardness Ranges:**
```
Hardness 0-24   → +0 turns
Hardness 25-49  → +1 turn
Hardness 50-74  → +2 turns
Hardness 75-99  → +3 turns
Hardness 100    → +4 turns
```

### Mining Progress

**Multi-Turn Action:**
```python
Turn 1: mining_progress = 0, target = 6
  → Message: "You start mining... (0/6)"

Turn 2: mining_progress = 1
  → Message: "Mining... (1/6)"

Turn 6: mining_progress = 6 (complete!)
  → Ore added to inventory
  → Ore vein removed from map
  → Message: "Mining complete! You obtained Iron Ore."
```

**Interruption:**
```python
if player.take_damage(amount):
    player.mining_progress = 0
    player.mining_target = None
    # Mining cancelled, must start over
```

### Vulnerability During Mining

**While mining:**
- Player cannot move
- Player cannot attack
- Player cannot dodge
- Monsters can attack normally
- Taking damage interrupts mining (progress lost)

---

## 🔨 Crafting Mechanics

### Stat Calculation

**Formula:**
```python
# From recipe YAML
stat_formula = "hardness * 0.1 + purity * 0.05"

# Evaluate with ore properties
ore_properties = {
    'hardness': 78,
    'conductivity': 30,
    'malleability': 65,
    'purity': 82,
    'density': 50
}

# Calculate stat
attack_bonus = eval_formula(stat_formula, ore_properties)
attack_bonus = 78 * 0.1 + 82 * 0.05
attack_bonus = 7.8 + 4.1
attack_bonus = 11.9 → 12 (rounded to int)
```

**Available Variables:**
- `hardness` (0-100) - Physical strength
- `conductivity` (0-100) - Magical power
- `malleability` (0-100) - Flexibility/durability
- `purity` (0-100) - Quality multiplier
- `density` (0-100) - Weight/mass

**Example Recipes:**

#### Copper Dagger
```yaml
ore_type: copper (hardness: 20-50, purity: 20-50)
formula: "hardness * 0.05 + purity * 0.02"

Low roll (hardness 25, purity 25):
  = 25 * 0.05 + 25 * 0.02
  = 1.25 + 0.5
  = 1.75 → +2 attack

High roll (hardness 50, purity 50):
  = 50 * 0.05 + 50 * 0.02
  = 2.5 + 1.0
  = 3.5 → +4 attack
```

#### Iron Sword
```yaml
ore_type: iron (hardness: 40-70, purity: 40-70)
formula: "hardness * 0.1 + purity * 0.05"

Average roll (hardness 55, purity 55):
  = 55 * 0.1 + 55 * 0.05
  = 5.5 + 2.75
  = 8.25 → +8 attack

Perfect roll (hardness 70, purity 70):
  = 70 * 0.1 + 70 * 0.05
  = 7.0 + 3.5
  = 10.5 → +11 attack
```

#### Mithril Longsword
```yaml
ore_type: mithril (hardness: 60-90, purity: 60-90)
formula: "hardness * 0.15 + purity * 0.1"

Average roll (hardness 75, purity 75):
  = 75 * 0.15 + 75 * 0.1
  = 11.25 + 7.5
  = 18.75 → +19 attack

Perfect roll (hardness 90, purity 90):
  = 90 * 0.15 + 90 * 0.1
  = 13.5 + 9.0
  = 22.5 → +23 attack
```

### Class Bonuses

**Applied After Stat Calculation:**
```python
base_stat = eval_formula(recipe_formula, ore_properties)
final_stat = base_stat * class_bonus

# Example: Warrior crafting Iron Sword
base_attack = 12
class_bonus = 1.2  # Warrior 20% bonus
final_attack = 12 * 1.2 = 14.4 → 14
```

**Class Bonus Values:**
```yaml
warrior: 1.2  # +20% physical weapons
rogue: 1.1    # +10% finesse weapons
mage: 1.2     # +20% magic items
healer: 1.1   # +10% support items
```

---

## 🎲 Ore Generation Mechanics

### Ore Spawn Rules

**Ore Type by Floor:**
```python
floor_range = {
    'copper':     (1, 3),   # Floors 1-3
    'iron':       (4, 6),   # Floors 4-6
    'mithril':    (7, 9),   # Floors 7-9
    'adamantite': (10, 99), # Floor 10+
}
```

**Veins Per Floor:**
```python
base_veins = 5
scaling = floor // 5
total_veins = base_veins + scaling

Floor 1: 5 + (1 // 5) = 5 veins
Floor 5: 5 + (5 // 5) = 6 veins
Floor 10: 5 + (10 // 5) = 7 veins
Floor 15: 5 + (15 // 5) = 8 veins
```

### Property Generation

**Each Property Rolled Independently:**
```python
# From ores.yaml
copper_ranges = {
    'hardness': (20, 50),
    'conductivity': (20, 50),
    'malleability': (20, 50),
    'purity': (20, 50),
    'density': (20, 50)
}

# Roll each property
ore_properties = {
    'hardness': random.randint(20, 50),      # e.g., 37
    'conductivity': random.randint(20, 50),  # e.g., 45
    'malleability': random.randint(20, 50),  # e.g., 29
    'purity': random.randint(20, 50),        # e.g., 48
    'density': random.randint(20, 50),       # e.g., 33
}
```

**Result:** Every ore vein is unique!

### Jackpot Spawns

**5% Chance for "Perfect" Ore:**
```python
if random.random() < 0.05:  # 5% chance
    # Boost all properties to high tier
    tier_boost = 2
    quality_range = (80, 100)  # Force high quality

# Example: Floor 3 (normally copper 20-50)
# Jackpot spawn → Mithril ore (60-90) on floor 3!
```

---

## 🏆 Floor Progression

### Monster Scaling

**Monster Count by Floor:**
```python
base_monsters = 2
scaling = floor // 3
monster_count = base_monsters + scaling

Floor 1: 2 + (1 // 3) = 2 monsters
Floor 3: 2 + (3 // 3) = 3 monsters
Floor 6: 2 + (6 // 3) = 4 monsters
Floor 9: 2 + (9 // 3) = 5 monsters
Floor 12: 2 + (12 // 3) = 6 monsters
```

**Monster Type Selection:**
```yaml
# From monster_spawns.yaml
floor_1_3:
  goblin: 60%
  rat: 30%
  bat: 10%

floor_4_6:
  goblin: 30%
  orc: 40%
  skeleton: 20%
  spider: 10%
```

**Selection Process:**
```python
roll = random.randint(1, 100)

if roll <= 60:    # 1-60
    spawn("goblin")
elif roll <= 90:  # 61-90
    spawn("rat")
else:             # 91-100
    spawn("bat")
```

### Difficulty Curve

**Expected Player Power by Floor:**
```
Floor 1-3:  15-20 HP, 5-7 attack, 2-4 defense (starting + copper gear)
Floor 4-6:  20-30 HP, 10-15 attack, 5-10 defense (leveled + iron gear)
Floor 7-9:  30-40 HP, 20-30 attack, 10-20 defense (leveled + mithril gear)
Floor 10+:  40+ HP, 30+ attack, 20+ defense (endgame + adamantite gear)
```

**Expected Monster Power:**
```
Floor 1-3:  5-15 HP, 2-5 attack, 1-2 defense
Floor 4-6:  15-30 HP, 5-10 attack, 2-5 defense
Floor 7-9:  30-80 HP, 10-20 attack, 5-10 defense
Floor 10+:  80-200 HP, 20-40 attack, 10-20 defense
```

---

## 🎁 Loot System

### Drop Rate Calculation

**Each Category Rolls Independently:**
```python
# From loot_tables.yaml
goblin_drops = {
    'gold': {'chance': 0.70, ...},
    'weapons': {'chance': 0.20, ...},
    'armor': {'chance': 0.15, ...}
}

# Roll for each category
if random.random() < 0.70:  # 70% chance
    drop_gold()
if random.random() < 0.20:  # 20% chance
    drop_weapon()
if random.random() < 0.15:  # 15% chance
    drop_armor()
```

**Result:** Monster can drop multiple items (gold + weapon, etc.)

### Item Selection Within Category

**Weighted Selection:**
```yaml
weapons:
  drop_chance: 0.20
  items:
    - id: dagger
      weight: 60  # 60% of weapon drops
    - id: short_sword
      weight: 40  # 40% of weapon drops
```

**Selection Process:**
```python
total_weight = 60 + 40 = 100
roll = random.randint(1, 100)

if roll <= 60:    # 1-60 (60%)
    drop("dagger")
else:             # 61-100 (40%)
    drop("short_sword")
```

---

## 💾 Save/Load Mechanics

### State Serialization

**GameState to JSON:**
```python
save_data = {
    'version': '1.0',
    'timestamp': '2025-11-05T12:34:56',
    'seed': '12345',
    'floor': 7,
    'turn_count': 342,

    'player': {
        'name': 'Hero',
        'class': 'warrior',
        'hp': 35,
        'max_hp': 40,
        'attack': 25,
        'defense': 15,
        'x': 42,
        'y': 18,
        'inventory': [...],
        'equipped': {...}
    },

    'monsters': [
        {'id': 'm_001', 'type': 'orc', 'hp': 8, 'x': 50, 'y': 20},
        {'id': 'm_002', 'type': 'troll', 'hp': 30, 'x': 45, 'y': 22}
    ],

    'map': {
        'width': 80,
        'height': 24,
        'tiles': [...],
        'entities': [...]
    }
}
```

### RNG State Preservation

**Seed Tracking:**
```python
# At game start
GameRNG.initialize(seed="12345")

# RNG used for all random operations
ore_hardness = rng.randint(40, 70)
monster_spawn = rng.choice(['orc', 'goblin', 'troll'])

# At save
save_data['seed'] = rng.get_seed()

# At load
GameRNG.initialize(seed=save_data['seed'])
# All future random events deterministic from this point
```

**Result:** Seeded runs are reproducible!

---

## 🎯 Balance Targets

### Combat Balance

**Player Should:**
- Take 2-4 hits to kill early monsters (floors 1-3)
- Take 4-8 hits to kill mid monsters (floors 4-6)
- Take 8-15 hits to kill late monsters (floors 7-9)

**Player Should Survive:**
- 8-12 hits from early monsters
- 6-10 hits from mid monsters
- 4-8 hits from late monsters

**Assumes:**
- Player finds ~70% of ore veins
- Player crafts gear every 2-3 floors
- Player uses average quality ore (not perfect)

### Progression Pace

**Expected Timeline:**
```
Turn 0-50:    Floor 1-2   (Tutorial, learn mining)
Turn 50-150:  Floor 3-5   (First crafted gear, comfortable)
Turn 150-300: Floor 6-8   (Mid-game challenge)
Turn 300-500: Floor 9-12  (Late game, high stakes)
Turn 500+:    Floor 13+   (Endgame survival)
```

**Death Points:**
- **70% of deaths:** Floors 4-7 (mid-game difficulty spike)
- **20% of deaths:** Floors 1-3 (learning game)
- **10% of deaths:** Floors 8+ (overconfidence, bad RNG)

---

## 🧮 Quick Calculation Reference

### "Will this kill the monster?"

```
my_attack = 17
monster_hp = 12
monster_defense = 2

damage_per_hit = max(1, 17 - 2) = 15
hits_to_kill = ceil(12 / 15) = 1 hit

Answer: Yes, one-shot kill
```

### "How much damage will I take?"

```
monster_attack = 5
my_defense = 10

damage = max(1, 5 - 10) = 1 (minimum)

Answer: 1 damage per hit (no threat)
```

### "Is this ore worth mining?"

```
Iron Ore: hardness 78, purity 82
Recipe: Iron Sword "hardness * 0.1 + purity * 0.05"

Result = 78 * 0.1 + 82 * 0.05 = 7.8 + 4.1 = 11.9 → +12 attack

Current weapon: +8 attack
Upgrade: +4 attack improvement

Answer: Yes, significant upgrade!
```

---

## 🏛️ Legacy Vault System

### Overview

The Legacy Vault is Brogue's meta-progression system that preserves high-quality ore (purity 80+) across runs, allowing players to withdraw 1 ore at the start of a new run.

**Design Philosophy:**
- Pure Victory: No vault ore used (higher prestige, challenge)
- Legacy Victory: Used 1 vault ore (accessibility, learning)
- Both paths are valid!

### How It Works

**On Death:**
- All ore with purity ≥ 80 is saved to Legacy Vault
- Max capacity: 50 ores
- Stored in `~/.brogue/legacy_vault.json`
- FIFO removal when vault is full (oldest ore removed)

**On Run Start:**
- Choose: Pure run (no vault) or Legacy run (withdraw 1 ore)
- Withdrawn ore starts in inventory
- Victory type tracked separately in high scores

### Victory Types

**Pure Victory:**
- No vault ore used
- Higher prestige (marked with * in leaderboard)
- Harder difficulty
- For veterans and challenge seekers

**Legacy Victory:**
- Used 1 vault ore from previous runs
- Easier difficulty (head start with quality ore)
- Learning tool and bad RNG recovery
- Marked with L in leaderboard

### Qualification Rules

**Ore Qualification:**
```python
# Ore qualifies for vault if:
ore.purity >= 80

# Examples:
Copper Ore (purity 79): ❌ Not saved
Iron Ore (purity 80): ✅ Saved
Gold Ore (purity 95): ✅ Saved (Legendary!)
```

**Quality Tiers:**
- Purity 80-84: Common (barely qualifies)
- Purity 85-89: Rare
- Purity 90-94: Epic
- Purity 95+: Legendary

### Vault Capacity Management

**Max Capacity:** 50 ores

**When Vault is Full:**
```python
# FIFO removal (First In, First Out)
if vault.count() >= 50:
    vault.remove(oldest_ore)  # Remove lowest priority ore
    vault.add(new_ore)
```

**Strategy:**
- Save best ores (90+ purity) for "learning runs"
- Use vault to overcome bad RNG streaks
- Pure runs for challenge/bragging rights
- Both paths are equally valid!

### Example Flow

**Scenario: First Death with Rare Ore**
```
Player inventory on death:
  - Copper Ore (purity 75) ❌
  - Iron Ore (purity 85) ✅
  - Gold Ore (purity 92) ✅

Result:
  → 2 ores saved to Legacy Vault
  → Message: "💎 2 rare ore(s) preserved in Legacy Vault!"
```

**Scenario: Next Run Start**
```
Vault contains:
  [1] Gold Ore (Epic, purity 92)
  [2] Iron Ore (Rare, purity 85)

Player chooses:
  Option 1: "Start Pure Run" → No ore, Pure Victory possible
  Option 2: Withdraw Gold Ore → Legacy run, easier start
```

**Scenario: Victory**
```
Pure Victory:
  → High Score shows: "* pure"
  → Higher prestige

Legacy Victory:
  → High Score shows: "L legacy"
  → Valid strategy!
```

---

## 📚 Related Documentation

- **DATA_FILES_GUIDE.md** - YAML schemas and data structure
- **CONTENT_CREATION.md** - Adding monsters, recipes, ore
- **game_constants.yaml** - Adjustable balance values
- **PROJECT_STATUS.md** - Implementation status

---

**Use this reference for:**
- Verifying expected behavior
- Balance tuning
- Bug reports ("goblin should do X damage, but does Y")
- Content creation (designing balanced monsters/recipes)

---

**All formulas verified against implementation as of 2025-11-05**
