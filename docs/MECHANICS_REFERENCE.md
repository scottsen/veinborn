# Veinborn Mechanics Reference

**Last Updated:** 2026-11-11 (combat dice + XP curve)
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

### Attack Resolution (to-hit, then damage)

Every swing, player or monster, goes through `AttackAction` and rolls twice,
NetHack-style. Config: `data/balance/formulas.yaml` → `combat`. There are no
critical hits.

**1. To-hit roll (d20):**
```python
roll = d20
if roll == 1:   miss                    # natural 1 always misses
elif roll == 20: hit                    # natural 20 always hits
else: hit if roll + attacker_attack >= 10 + defender_defense
```
A miss still takes the turn ("Goblin misses Player.").

| Attack vs Defense | Hit on | Chance |
|---|---|---|
| 5 vs 1 (warrior vs goblin) | 6+ | 75% |
| 3 vs 3 (goblin vs warrior) | 10+ | 55% |
| 3 vs 1 (goblin vs mage) | 8+ | 65% |
| 5 vs 6 (warrior vs golem) | 11+ | 50% |
| far above defense | 2+ | 95% |
| far below defense | 20 | 5% |

**2. Damage roll:**
```python
damage_roll = uniform(ceil(attack * 0.5), floor(attack * 1.5))   # spread 0.5
damage = max(1, damage_roll - defender_defense)
```
The average stays near `attack - defense`, so monster stat blocks keep their
meaning; the spread adds the swing. Attack 4 rolls 2-6; attack 3 rolls 2-4.

**Details:**
- **Attacker Attack** = Base Attack + Equipment Bonuses
- **Defender Defense** = Base Defense + Equipment Bonuses
- **Defense counts twice**: it lowers the chance to be hit *and* the damage taken
- **Minimum Damage** = 1 on a hit

**Measure a change:** `python3 scripts/sim_duels.py [--levels 1,4] [--monsters ...]`
runs hundreds of duels per class x monster x level on an open arena. The monster
is driven by the real `AISystem` (perception, morale, speed, abilities) and both
sides use the real `AttackAction`/`AbilityAction`. It prints win%, timeouts, HP
lost, rounds, and how much of the player's damage came from monster melee,
monster abilities or summoned minions. `--abilities both` compares monster
abilities off (as shipped) and on, and `--set lich.death_bolt.damage=8` tries a
number before it goes into the YAML. `--json` writes the table.

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

### Class Abilities

Config: `data/balance/formulas.yaml` → `abilities`. Code:
`src/core/actions/ability_action.py` (active), `AttackAction._is_backstab`
(passive). Key **z** (`handle_player_action('ability')`) uses the class's first
active ability. There is no mana: abilities have turn cooldowns, and a use that
fails (no target, on cooldown, full HP) costs no turn.

| Class | Ability | Effect | Cooldown |
|---|---|---|---|
| Mage | `force_bolt` | Nearest monster in line of sight within 6 tiles; never misses, ignores defense; damage `randint(2, 6)` plus 0.5 per level above 1 (rounded down); kills give XP and loot like melee | 3 turns |
| Healer | `heal` | Heal self 6 HP (+1 per level above 1) | 12 turns |
| Rogue | `backstab` (passive) | First hit on a monster at full HP does x2 damage | none |
| Warrior | none yet | | |

**Starting gear** is equipped at creation and is stat-neutral: the template
base stats plus the gear equal the pre-gear values (warrior 5/3 = base 2/1 +
short sword +3 + leather armor +2; rogue 4/2 = base 2/2 + dagger +2). Mage and
healer start with nothing.

Unbuilt: fireball, teleport, dodge, protect, regeneration, power strike (VB-53).

**Monsters use abilities too** (VB-63): a monster's abilities come from its behaviour (the
sniper's `ranged_attack`: a normal attack from 4-6 tiles; the summoner's `summon`: a goblin
every 10 turns, at most 3 alive) and from `enabled: true` entries in its `abilities:` block in
`monsters.yaml` (all disabled today; VB-64 turns them on). Each action, after morale, it uses the
first ready one that is worthwhile against the player it perceives.

### Monster Perception

What a monster knows about you (`AISystem.perceive`, VB-60):

- **Sight:** it notices a player within its `aggro_range` (`monsters.yaml`, default 8)
  counted in 8-way steps, if no wall blocks the line between you.
- **Memory:** once it has seen you it keeps after you for `memory_turns` (default 10)
  after losing sight, pathing around walls.
- **Provocation:** attacking a monster (melee or force bolt) makes it remember you as its
  target, however far away you are; a `neutral` monster only fights back when attacked.

**Speed:** a monster takes `move_speed` actions per round on average (`monsters.yaml`;
an energy counter): a bat (1.5) acts 3 times every 2 rounds, a golem (0.6) 3 times every 5.
The player always acts once per round.

**Morale:** a monster below its `flee_threshold` of max HP (defensive 0.3, neutral 0.5,
sniper 0.3; aggressive monsters and guards never) flees from what it perceives instead of
acting.

What it does about it is its behaviour (`ai: type:`): aggressive monsters close in on
anything they perceive; defensive ones only engage within their `chase_range` (5) unless
attacked; guards engage within `chase_range` (6) without leaving `guard_radius`; cowards
flee. Parameters: `data/balance/ai_behaviors.yaml` (`defaults` and per behaviour).
Design: [architecture/AI_ARCHITECTURE.md](architecture/AI_ARCHITECTURE.md).

### Death and XP

**Death Detection:**
```python
if entity.hp <= 0:
    entity.is_alive = False
```

**XP Award:**
```python
xp_gained = monster.xp_reward  # Defined in monsters.yaml
player.gain_xp(xp_gained)      # may grant several levels at once
```

**Leveling curve (NetHack-style doubling):** `game_constants.yaml` →
`player.progression.xp_curve`. Thresholds are **total** XP:

```
Level 2: 20    Level 3: 40    Level 4: 80    Level 5: 160
Level 6: 320   Level 7: 640   ...            Level 11: 10240
then +10000 per level
```

With today's monster XP, a player who clears floors reaches level 2 on floor 2,
level 4 around floor 3-4, level 5-6 by floor 6-8.

**Level Up Bonuses** (per class, `src/core/character_class.py`):

| Class | HP per level (rolled) | Attack | Defense |
|---|---|---|---|
| Warrior | 3-7 (avg 5) | +1 | +0 |
| Rogue | 2-4 (avg 3) | +1 | +0 |
| Mage | 2-4 (avg 3) | +1 | +0 |
| Healer | 2-6 (avg 4) | +1 | +0 |
| no class | 3-7 (avg 5) | +1 | +0 |

The HP gain is added to current HP as well as max HP; levelling is **not** a
full heal. Defense never grows with level: it comes from crafted armor.

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

**Ongoing spawns (VB-52):** after the floor is made, every turn has a 2%
chance (`spawning.yaml` → `ongoing_spawns`) of one new monster appearing at
least 8 tiles (Chebyshev: 8-way steps) from every living player, up to 12 living monsters on
the floor. Its type is drawn from the spawn weights of tier
`(floor + average player level) // 2` (minimum 1), NetHack's formula, so idling
costs you and a high-level player draws tougher wanderers. Code:
`TurnProcessor._maybe_spawn_wanderer`, `EntitySpawner.spawn_wandering_monster`.

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

The Legacy Vault is Veinborn's meta-progression system that preserves high-quality ore (purity 80+) across runs, allowing players to withdraw 1 ore at the start of a new run.

**Design Philosophy:**
- Pure Victory: No vault ore used (higher prestige, challenge)
- Legacy Victory: Used 1 vault ore (accessibility, learning)
- Both paths are valid!

### How It Works

**On Death:**
- All ore with purity ≥ 80 is saved to Legacy Vault
- Max capacity: 50 ores
- Stored in `~/.veinborn/legacy_vault.json`
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
- **STATUS_DASHBOARD.md** - Implementation status

---

**Use this reference for:**
- Verifying expected behavior
- Balance tuning
- Bug reports ("goblin should do X damage, but does Y")
- Content creation (designing balanced monsters/recipes)

---

**All formulas verified against implementation as of 2025-11-05**
