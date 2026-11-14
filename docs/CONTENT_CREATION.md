# Veinborn Content Creation Guide

**Last Updated:** 2025-11-05
**For:** Designers and content creators adding monsters, recipes, and content

---

## 🎯 Quick Links

| Task | Time | Jump To |
|------|------|---------|
| **Add a Monster** | 5 min | [↓ Monster Guide](#-adding-a-monster) |
| **Add a Recipe** | 10 min | [↓ Recipe Guide](#-adding-a-recipe) |
| **Add Ore Type** | 15 min | [↓ Ore Guide](#-adding-an-ore-type) |
| **Adjust Balance** | 2 min | [↓ Balance Guide](#-adjusting-game-balance) |
| **Add Loot Table** | 10 min | [↓ Loot Guide](#-creating-loot-tables) |

---

## 📋 Current Content Status

### What We Have
- **Monsters:** 19 types, all spawning (floor bands to 61+, ancient_horror as the floor-99 boss)
- **Recipes:** 16 (10 ore tiers + 6 legendary, each legendary gated on a boss material)
- **Ore Types:** 4 tiers (copper → iron → mithril → adamantite)
- **Loot Tables:** 8 (goblin, orc, troll; boss materials for lich, phoenix, wraith, wyvern, ancient_horror)

### What We Need
- **Loot tables for the other 11 monsters** (VB-70)
- **Monster abilities switched on** (VB-64; built, disabled)
- **Special room types** (medium priority)
- **More item variety** (low priority)

---

## 🐲 Adding a Monster

**Time Required:** 5-10 minutes
**Difficulty:** ⭐⭐ Medium
**Files Modified:** `data/entities/monsters.yaml`, `data/balance/monster_spawns.yaml`, `data/balance/loot_tables.yaml`

### Step 1: Copy Template

Open `data/entities/monsters.yaml` and add your monster:

```yaml
wyvern:
  # Display (what player sees)
  name: "Wyvern"
  description: "A flying serpent with venomous fangs and razor-sharp claws."
  symbol: "W"        # Single character (uppercase for bosses)
  color: "dark_green"

  # Core stats
  stats:
    hp: 80           # Hit points (goblin=6, orc=12, troll=30)
    attack: 18       # Attack power (goblin=3, orc=5, troll=12)
    defense: 8       # Defense (goblin=1, orc=2, troll=5)
    xp_reward: 200   # XP given (goblin=5, orc=15, troll=50)

  # AI behavior
  ai:
    type: "aggressive"  # aggressive, defensive, neutral, coward, guard, berserker, sniper, summoner
    move_speed: 1.2     # 1.0 = normal, 1.2 = 20% more actions per round
    aggro_range: 12     # Notices players this far away, with line of sight (8 = normal)
    description: "Fast flying predator, chases relentlessly"
  # Any key here overrides the behaviour's defaults in data/balance/ai_behaviors.yaml;
  # unknown keys stop the game at start (validation).
  # The planned design (per-monster parameters, perception, speed, monster abilities)
  # is in docs/architecture/AI_ARCHITECTURE.md.

  # Gameplay tags
  tags:
    - "flying"       # For logic/filtering
    - "boss"
    - "floors_7_9"

  # Loot (we'll create this next)
  loot_table: "wyvern"

  # Design notes (for developers)
  notes: |
    Wyvern is an elite enemy for floors 7-9.
    High mobility makes it dangerous in open rooms.
    Player should have mithril equipment by this point.
```

### Step 2: Design Stats

Use this formula to balance stats for target floor:

```python
# Target Floor → Suggested Stats
Floor 1-3 (Easy):    HP: 5-15,   Attack: 2-5,   Defense: 1-2
Floor 4-6 (Medium):  HP: 15-30,  Attack: 5-10,  Defense: 2-5
Floor 7-9 (Hard):    HP: 30-80,  Attack: 10-20, Defense: 5-10
Floor 10+ (Expert):  HP: 80-200, Attack: 20-40, Defense: 10-20

# XP Reward = HP + (Attack * 5) + (Defense * 5)
# Example: Wyvern = 80 + (18*5) + (8*5) = 80 + 90 + 40 = 210 XP
```

**Balancing Tips:**
- Player starts with 20 HP, 5 attack, 2 defense
- Player should fight ~10 enemies per floor
- Boss enemies = 2-3x stronger than regular enemies on that floor
- Fast enemies (speed > 1.0) need lower HP to compensate

### Step 3: Add to Spawn Table

Open `data/balance/monster_spawns.yaml` and add the monster to the `spawn_weights` band(s)
for the floors it belongs on. Each key names its floors (`floor_1`, `floors_6_10`,
`floors_61_plus`); weights are relative and need not sum to 100.

```yaml
spawn_weights:
  floors_26_40:
    troll: 10
    wyvern: 15
    lich: 10
    my_monster: 10     # NEW
```

To give it floors of its own, split a band (`floors_26_40` into `floors_26_30` and
`floors_31_40`); the game checks at load that the bands still cover every floor once.
Its stats grow with depth through `floor_scaling` (set `floor_scaling: false` on the
monster to keep them as written); a one-per-floor boss goes in `boss_floors` instead of
the weights. See [DATA_FILES_GUIDE.md](DATA_FILES_GUIDE.md#-monster_spawnsyaml).

### Step 4: Create Loot Table

Either point the monster at a shared table in `monsters.yaml` (`loot_table: beast`) or add
one keyed by its id to `data/balance/loot_tables.yaml`. Item ids must exist in
`data/entities/items.yaml` (checked at load):

```yaml
wyvern:
  description: "Elite enemy - generous loot"

  gold:
    drop_chance: 0.90
    items:
      - id: gold_pile_large
        weight: 100
        amount_range: [50, 150]

  weapons:
    drop_chance: 0.40
    items:
      - id: long_sword
        weight: 50
      - id: battle_axe
        weight: 50

  potions:
    drop_chance: 0.50
    items:
      - id: potion_extra_healing
        weight: 70
      - id: potion_full_healing
        weight: 30
```

A monster that should drop nothing gets a table with only a `description`.

### Step 5: Test

```bash
# 1. Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('data/entities/monsters.yaml'))"

# 2. Run tests
pytest tests/unit/test_entity_loader.py -v

# 3. Playtest
python3 run_textual.py
# - Get to floor 7
# - Verify wyvern spawns
# - Fight it, check difficulty
# - Verify loot drops
```

### Monster Ideas (Need 6-11 More)

| Monster | Floor | Gimmick |
|---------|-------|---------|
| **Mimic** | 4-6 | Disguised as loot chest |
| **Wraith** | 7-9 | Phases through walls |
| **Golem** | 7-9 | High defense, slow |
| **Vampire** | 10-12 | Life steal attacks |
| **Basilisk** | 10-12 | Petrify status effect |
| **Phoenix** | 13-15 | Respawns once when killed |
| **Lich** | 13-15 | Summons undead minions |
| **Demon** | 16-18 | Fire damage, teleports |
| **Dragon** | 18-20 | Boss-tier, breath attack |
| **Ancient Horror** | 20+ | Final boss |

---

## ⚔️ Adding a Recipe

**Time Required:** 10-15 minutes
**Difficulty:** ⭐⭐⭐ Complex (stat formulas)
**File Modified:** `data/balance/recipes.yaml`

### Step 1: Choose Recipe Type

Recipes are organized by category:
- `weapons:` - Swords, axes, bows, staves
- `armor:` - Body armor, helmets, boots
- `accessories:` - Rings, amulets, cloaks

### Step 2: Copy Template

```yaml
mithril_longsword:
  # Display
  display_name: "Mithril Longsword"
  description: "A masterwork blade forged from legendary mithril ore"
  symbol: ")"
  color: "cyan"
  item_type: "weapon"
  equipment_slot: "weapon"  # weapon, body, head, hands, feet, ring

  # Recipe requirements
  requirements:
    ore_type: "mithril"      # copper, iron, mithril, adamantite
    ore_count: 2             # How many ores needed
    min_floor: 7             # Minimum floor to discover/craft
    requires_forge: true     # Must be at forge (vs portable kit)

  # Stat formulas (evaluated at craft time using ore properties)
  stat_formulas:
    attack_bonus: "hardness * 0.15 + purity * 0.1"
    defense_bonus: 0
    durability: "malleability * 0.8"
    weight: "density * 0.015"

  # Class bonuses (optional)
  class_bonuses:
    warrior: 1.2  # Warriors get 20% bonus
    rogue: 1.1    # Rogues get 10% bonus
    mage: 1.0     # Mages no bonus
    healer: 1.0   # Healers no bonus
```

### Step 3: Design Stat Formulas

**Available Variables:**
- `hardness` (0-100) - Physical strength
- `conductivity` (0-100) - Magical power
- `malleability` (0-100) - Flexibility
- `purity` (0-100) - Quality multiplier
- `density` (0-100) - Weight

**Formula Guidelines by Tier:**

```yaml
# Tier 1: Copper (ore properties 20-50)
attack_bonus: "hardness * 0.05 + purity * 0.02"  # Result: 2-4 damage

# Tier 2: Iron (ore properties 40-70)
attack_bonus: "hardness * 0.1 + purity * 0.05"   # Result: 6-11 damage

# Tier 3: Mithril (ore properties 60-90)
attack_bonus: "hardness * 0.15 + purity * 0.1"   # Result: 15-27 damage

# Tier 4: Adamantite (ore properties 80-100)
attack_bonus: "hardness * 0.2 + purity * 0.15"   # Result: 31-50 damage
```

**Testing Formulas:**

```bash
# Quick formula test
python3 << EOF
# Simulate mithril ore (60-90 range)
hardness = 80
conductivity = 70
malleability = 75
purity = 85
density = 65

# Your formula
attack_bonus = hardness * 0.15 + purity * 0.1
print(f"Attack Bonus: +{attack_bonus}")
# Expected: 80*0.15 + 85*0.1 = 12 + 8.5 = 20.5 → +20 attack
EOF
```

### Step 4: Balance Check

```python
# Weapon Damage Progression Target
Floor 1-3:   +2 to +5 damage
Floor 4-6:   +6 to +12 damage
Floor 7-9:   +15 to +30 damage
Floor 10+:   +30 to +60 damage

# Armor Defense Progression Target
Floor 1-3:   +1 to +3 defense
Floor 4-6:   +4 to +8 defense
Floor 7-9:   +10 to +20 defense
Floor 10+:   +20 to +40 defense
```

### Step 5: Test

```bash
# Run crafting tests
pytest tests/integration/test_equipment_system.py -v

# Playtest:
# 1. Mine appropriate ore
# 2. Go to forge
# 3. Craft item
# 4. Check stats match your formula
# 5. Equip and test in combat
```

### Recipe Ideas (Legendary Tier)

```yaml
# Flaming Sword (fire damage)
flaming_sword:
  display_name: "Flaming Sword of the Phoenix"
  stat_formulas:
    attack_bonus: "(hardness + conductivity) * 0.15"  # Hybrid scaling
    fire_damage: "conductivity * 0.1"  # Bonus fire damage
  requirements:
    ore_type: "adamantite"
    ore_count: 3
    min_floor: 15

# Arcane Staff (spell power)
arcane_staff:
  display_name: "Staff of Arcane Mastery"
  stat_formulas:
    spell_power: "conductivity * 0.2 + purity * 0.15"
    mana_bonus: "conductivity * 0.5"
  requirements:
    ore_type: "mithril"
    ore_count: 2
    min_floor: 12

# Shadow Cloak (stealth)
shadow_cloak:
  display_name: "Cloak of Shadows"
  stat_formulas:
    defense_bonus: "malleability * 0.1"
    stealth_bonus: "purity * 0.3"
  requirements:
    ore_type: "adamantite"
    ore_count: 2
    min_floor: 13
```

---

## 🪨 Adding an Ore Type

**Time Required:** 15-20 minutes
**Difficulty:** ⭐⭐ Medium
**Files Modified:** `data/entities/ores.yaml`, `data/balance/ore_veins.yaml`

### When to Add New Ore

- **Filling a tier gap** (e.g., between mithril and adamantite)
- **Special thematic ore** (dragon ore, shadow ore, celestial ore)
- **Boss reward ore** (only drops from specific boss)

### Step 1: Add Ore Definition

Open `data/entities/ores.yaml`:

```yaml
ore_types:
  dragon_ore:
    # Display
    name: "Dragon Ore"
    description: "Legendary ore infused with dragon essence. Burns with inner fire."
    symbol: "~"
    color: "red"

    # Tier
    tier: 5              # 1-4 taken, 5 = legendary
    tier_name: "Legendary"

    # Floor availability
    floor_range:
      min: 15            # Rare, late-game
      max: 20
      optimal: [17, 18, 19]

    # Quality ranges (0-100 scale)
    quality:
      min: 85            # Always high quality
      max: 100
      average: 92

    # Property ranges (rolled independently)
    properties:
      hardness: [85, 100]      # Excellent for weapons
      conductivity: [85, 100]  # Excellent for magic
      malleability: [85, 100]  # Easy to work with
      purity: [90, 100]        # Nearly perfect
      density: [85, 100]       # Heavy but manageable

    # Mining difficulty
    mining:
      base_turns: 8            # Very hard to mine
      hardness_modifier: true  # Can take 10-12 turns total

    # Crafting info
    crafting:
      tier: 5
      equipment_level: [15, 20]
      description: "Can craft level 15-20 legendary equipment"
```

### Step 2: Add Spawn Rules

Open `data/balance/ore_veins.yaml`:

```yaml
floor_ranges:
  floor_15_20:
    floor_range: [15, 20]
    description: "Legendary ore zone"

    ore_weights:
      mithril: 30      # Still some mithril
      adamantite: 40   # Mostly adamantite
      dragon_ore: 30   # NEW: Dragon ore spawns

    veins_per_floor:
      base: 6
      variance: 2      # 4-8 veins per floor

    jackpot_chance: 0.10  # 10% for perfect stats
```

### Step 3: Test

```bash
# Validate
python3 -c "import yaml; yaml.safe_load(open('data/entities/ores.yaml'))"

# Run tests
pytest tests/unit/test_entity_loader.py -v

# Playtest: Get to floor 15+, find dragon ore, mine it, check properties
```

---

## ⚖️ Adjusting Game Balance

**Time Required:** 2-5 minutes
**Difficulty:** ⭐ Easy
**File Modified:** `data/balance/game_constants.yaml`

### Common Balance Tweaks

#### Make Game Easier

```yaml
player:
  starting_stats:
    hp: 30        # Was 20
    attack: 7     # Was 5
    defense: 3    # Was 2

  health_regeneration:
    interval_turns: 5   # Was 10 (heal faster)
    amount: 2           # Was 1 (heal more)

spawning:
  monster_scaling:
    base_count: 2       # Keep same
    floor_divisor: 4    # Was 3 (fewer monsters per floor)
```

#### Make Game Harder

```yaml
player:
  starting_stats:
    hp: 15        # Was 20
    attack: 4     # Was 5

spawning:
  monster_scaling:
    base_count: 3       # Was 2 (more base monsters)
    floor_divisor: 2    # Was 3 (more monsters per floor)

  ore_vein_scaling:
    base_count: 3       # Was 5 (less ore)
    floor_divisor: 6    # Was 5 (slower scaling)
```

#### Faster Progression

```yaml
player:
  progression:
    xp_curve:
      base: 10             # Was 20 (every level threshold halves)
    hp_gain_per_level: 7   # Was 5 (classless player; classes are in character_class.py)
    attack_gain_per_level: 2  # Was 1 -- careful: compounds fast, check scripts/sim_duels.py
```

---

## 🎁 Creating Loot Tables

**Time Required:** 10 minutes
**Difficulty:** ⭐⭐ Medium
**File Modified:** `data/balance/loot_tables.yaml`

### Template

```yaml
monster_id:  # a monster id, or a shared table named by monsters.yaml `loot_table:`
  description: "Drop table description"

  # Each category rolls independently
  gold:
    drop_chance: 0.70  # 70% chance to drop gold
    items:
      - id: gold_pile_small
        weight: 60       # 60% of gold drops
        amount_range: [10, 30]
      - id: gold_pile_medium
        weight: 40
        amount_range: [30, 60]

  weapons:
    drop_chance: 0.25
    items:
      - id: short_sword   # item ids must exist in data/entities/items.yaml
        weight: 50
      - id: battle_axe
        weight: 50

  armor:
    drop_chance: 0.20
    items:
      - id: leather_armor
        weight: 70
      - id: chainmail
        weight: 30
```

Several monsters can share a table: set `loot_table: <table>` on each in `monsters.yaml`.
A table with only a `description` drops nothing on purpose. The family tables (`beast`,
`undead`, `brute`, `arcane`) are shared this way and hold consumables only. An item entry may
carry `min_floor: N` (default 1) and is then only rolled from floor N down, which is how
healing quality scales with depth; a category whose entries are all closed at the monster's
floor drops nothing. Unknown table names and item ids fail at load; see [DATA_FILES_GUIDE.md](DATA_FILES_GUIDE.md#-loot_tablesyaml).

### Loot Balance Guidelines

```yaml
# Weak enemies (goblin, rat)
gold: 70% chance, 5-30 gold
weapons: 15-20% chance
armor: 10-15% chance

# Medium enemies (orc, skeleton)
gold: 80% chance, 20-60 gold
weapons: 25-30% chance
armor: 20-25% chance

# Strong enemies (troll, ogre)
gold: 85% chance, 50-120 gold
weapons: 35-40% chance
armor: 30-35% chance

# Elite/Boss enemies (wyvern, dragon)
gold: 90% chance, 100-300 gold
weapons: 40-50% chance
armor: 40-50% chance
special: 5-15% chance (legendary items)
```

---

## 🏰 Adding Special Room Types

**Time Required:** 30-60 minutes
**Difficulty:** ⭐⭐⭐ Hard (requires code)
**Files Modified:** `src/core/world.py`

### Concept

Currently, all rooms are generic. We want:
- **Treasure rooms** - Guaranteed loot chest
- **Monster dens** - Extra monsters + mini-boss
- **Ore chambers** - Multiple high-quality veins
- **Shrines** - Healing station
- **Trap rooms** - Dangerous but rewarding

### Implementation (Simplified)

```python
# In src/core/world.py

def generate_special_room(room: Room, floor: int, rng: GameRNG) -> RoomType:
    """10% chance for special room per floor."""

    if rng.random() < 0.10:
        room_types = ["treasure", "monster_den", "ore_chamber", "shrine"]
        room_type = rng.choice(room_types)

        if room_type == "treasure":
            # Spawn loot chest in center
            chest = create_loot_chest(floor)
            room.add_entity(chest, room.center)

        elif room_type == "ore_chamber":
            # Spawn 3-5 high-quality ore veins
            for _ in range(rng.randint(3, 5)):
                vein = create_ore_vein(floor, quality_boost=+20)
                room.add_entity(vein, room.random_wall_pos())

        return room_type

    return "normal"
```

*Note: This requires code changes. See `docs/architecture/` for patterns.*

---

## ✅ Content Creation Checklist

### Before Adding Content

- [ ] Read DATA_FILES_GUIDE.md (understand schemas)
- [ ] Check existing content (avoid duplicates)
- [ ] Have clear design intent (what problem does this solve?)

### After Adding Content

- [ ] Validate YAML syntax
- [ ] Run appropriate tests
- [ ] Playtest in-game
- [ ] Check balance (not too strong/weak)
- [ ] Document design notes in YAML
- [ ] Commit with clear message

### Commit Message Template

```bash
git add data/
git commit -m "Add wyvern monster to floors 7-9

- Elite flying enemy with high mobility
- 80 HP, 18 attack, 8 defense, 200 XP
- Drops high-tier loot (mithril equipment)
- Balanced for players with iron/mithril gear

Tested: Entity loader tests pass, playtested floors 7-9"
```

---

## 🐛 Troubleshooting

### YAML Parsing Error

```bash
# Error: "mapping values are not allowed here"
# Fix: Check for missing colons, incorrect indentation

# Validate:
python3 -c "import yaml; yaml.safe_load(open('data/entities/monsters.yaml'))"
```

### Monster Not Spawning

1. Check `monster_spawns.yaml` - Is monster in the `spawn_weights` band for that floor?
2. Check the band key covers your floor (`floors_11_15` is 11 to 15)
3. Weights are relative: a weight of 5 among bands totalling 100 is rare
4. Bots reach about floor 10; for deeper floors run them with `--start-floor` (`tests/fuzz/README.md`)

### Recipe Not Crafting

1. Check ore type matches (copper/iron/mithril/adamantite)
2. Check min_floor requirement
3. Check requires_forge (are you at a forge?)
4. Check ore count (do you have enough ore?)

### Loot Not Dropping

1. Check loot_table references match monster ID
2. Check drop_chance (0.10 = 10%, not 10%)
3. Kill 10+ monsters to verify drop rates
4. Check weights sum correctly

---

## 📚 Related Documentation

- **DATA_FILES_GUIDE.md** - Detailed schema reference
- **QUICK_REFERENCE.md** - File locations and commands
- **MECHANICS_REFERENCE.md** - Game formulas and calculations
- **STATUS_DASHBOARD.md** - What's implemented

---

## 💡 Content Creation Tips

1. **Start simple** - Copy existing content, modify gradually
2. **Test frequently** - Don't wait until you've added 10 monsters
3. **Balance iteratively** - Too strong? Reduce stats. Too weak? Increase them.
4. **Use notes fields** - Document your design intent
5. **Playtest thoroughly** - Automated tests don't catch "unfun"
6. **Ask for feedback** - Get others to playtest your content

---

**Ready to create? Pick a task above and start building!** 🎨

Questions? Check **DATA_FILES_GUIDE.md** for schema details.
