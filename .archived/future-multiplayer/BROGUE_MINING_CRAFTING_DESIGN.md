# Brogue Mining & Crafting System Design

**Date:** 2025-10-21
**Session:** icy-temple-1021
**Status:** Design Phase
**Inspiration:** Star Wars Galaxies resource/crafting mechanics

---

## 🎯 Core Concept

Add a SWG-inspired ore property system to Brogue where:
- Ore deposits have random stat properties (0-100 scale)
- Properties affect crafted equipment differently for each class
- Resource hunting becomes a strategic mini-game
- Deeper floors spawn better ore (with occasional early jackpots)

---

## ⛏️ Mining Mechanics

### Basic Flow

1. **Encounter Ore** - Solid wall tiles can be ore deposits
2. **Survey** - Examine ore properties (1 turn action)
3. **Decide** - Mine or keep searching?
4. **Mine** - Takes 3-5 turns, player vulnerable to attacks
5. **Collect** - Ore goes to inventory, tile becomes floor

### Turn-Based Mining

```
Turn 1: Player moves into ore → "You start mining the iron ore..."
Turn 2: Monsters move/attack → "You continue mining..."
Turn 3: Monsters move/attack → "You continue mining..."
Turn 4: Complete → "You extract the iron ore!" (→ inventory)
```

**Risk/Reward:** Mining takes time, you can't dodge/fight while mining. High-quality ore worth the risk?

### Mining Duration

- Base: 3 turns
- Modified by ore hardness: Harder ore = +1-2 turns
- Modified by tool: Bare hands vs pickaxe
- Status shown: "Mining... (2/4 turns remaining)"

---

## 💎 Ore Property System

### Five Core Properties (0-100 scale)

Each ore deposit spawns with random values:

```python
class OreDeposit:
    ore_type: str      # "Iron", "Copper", "Mithril", "Gold", "Adamantite"

    # Stats (rolled randomly on spawn)
    hardness: int      # 0-100 → Weapon damage / Armor defense
    conductivity: int  # 0-100 → Magical enhancement / Mana efficiency
    malleability: int  # 0-100 → Durability / Repair efficiency
    purity: int        # 0-100 → Overall quality multiplier (affects all)
    density: int       # 0-100 → Weight / Encumbrance trade-off

    # Derived
    mining_time: int   # Higher hardness = more turns to mine
    spawn_depth: int   # Floor it was found on
```

### Example Ore Spawn

```
═══════════════════════════════════
  Iron Ore Vein
═══════════════════════════════════
  Hardness:      78  ████████░░
  Conductivity:  23  ██░░░░░░░░
  Malleability:  65  ██████░░░░
  Purity:        82  ████████░░
  Density:       45  █████░░░░░
═══════════════════════════════════
  Quality: High (warrior-friendly)
  Mining Time: 4 turns
═══════════════════════════════════
  [M]ine  [L]eave
```

---

## 🗡️ Class System & Synergies

### Warrior (Physical Damage Specialist)

**Prioritizes:**
- **Hardness** → Direct damage bonus on weapons
- **Density** → Armor protection (can handle heavy armor)
- **Malleability** → Equipment durability (less repairs)

**Example Crafting:**
```
High Hardness Iron (78) + Longsword Recipe
→ Iron Longsword: +6 damage (instead of base +4)
→ "Forged from exceptionally hard iron"
```

### Mage (Magical Enhancement Specialist)

**Prioritizes:**
- **Conductivity** → Spell damage amplification
- **Low Density** → Reduces spell-casting fatigue
- **Purity** → Mana efficiency on equipment

**Example Crafting:**
```
High Conductivity Mithril (91) + Staff Recipe
→ Mithril Channeling Staff: +45% spell power
→ "Thrums with magical energy"
```

### Ranger (Versatile Hybrid)

**Prioritizes:**
- **Balanced Hardness/Conductivity** → Enchanted arrows
- **High Malleability** → Field repairs without forge
- **Low Density** → Movement speed bonus

**Example Crafting:**
```
Balanced Copper (H:60, C:55, M:70) + Bow Recipe
→ Copper-Reinforced Longbow
→ Arrows can be elemental OR physical damage
→ Can repair in the field (malleability > 60)
```

---

## ⚔️ Legacy Ore System (Meta-Progression)

### Core Concept

**Legacy Ore** - Special, named ore that persists across deaths. Allows gradual progression toward legendary gear while maintaining roguelike street cred for purists.

### How It Works

**Finding Legacy Ore:**
- Very rare spawns (1-2% chance per floor)
- Always exceptional quality (95-100 stats)
- Has unique names and lore
- Glows with distinctive color/animation
- Announced when found: "You've discovered STARFORGED IRON!"

**Death & Persistence:**
```
Run 1: Find "Starforged Iron" → Die
       → Starforged Iron saved to Legacy Vault

Run 2: Find "Moonsilver Mithril" → Die
       → Moonsilver Mithril added to vault
       → Now have 2 Legacy Ore pieces

Run 3: Craft Legacy Sword from Starforged Iron
       → Start run with Legacy Sword equipped
       → Much easier run, but...
       → No street cred if you win
```

**Legacy Ore Examples:**

```
STARFORGED IRON
  Hardness: 98 (legendary!)
  Purity: 97
  Lore: "Iron from a fallen star, never dulls"
  Crafts: Starforged Blade (+15 dmg, unbreakable)

MOONSILVER MITHRIL
  Conductivity: 99 (legendary!)
  Purity: 96
  Lore: "Mined from ancient moon temple ruins"
  Crafts: Moonsilver Staff (+60% spell power)

DRAGONBONE ADAMANTITE
  Hardness: 96, Conductivity: 95 (balanced!)
  Purity: 98
  Lore: "Infused with dragon essence"
  Crafts: Dragonbone Bow (elemental shots)

VOID CRYSTAL
  Conductivity: 100 (perfect!)
  Purity: 99
  Lore: "Crystalized from pure void energy"
  Crafts: Void Armor (magic immunity)
```

### The Legacy Vault

**Persistent Storage:**
```
┌─ LEGACY VAULT ─────────────────────────┐
│ Collected across 7 deaths              │
│                                        │
│ [1] Starforged Iron (H:98, P:97)      │
│     ↳ Can craft: Starforged Blade     │
│                                        │
│ [2] Moonsilver Mithril (C:99, P:96)   │
│     ↳ Can craft: Moonsilver Staff     │
│                                        │
│ [3] Bloodstone (H:95, C:94, P:97)     │
│     ↳ Can craft: Bloodstone Ring      │
│                                        │
│ Total Legacy Runs: 3                  │
│ Total Pure Runs: 4                    │
└────────────────────────────────────────┘
```

### Legacy Crafting

**At Game Start:**
```
┌─ NEW GAME ─────────────────────────────┐
│ Choose your path:                      │
│                                        │
│ [P] Pure Run (street cred!)           │
│     → Start with nothing              │
│     → Victory = "Pure Victory" badge  │
│                                        │
│ [L] Legacy Kit                        │
│     → Craft from Legacy Vault         │
│     → Easier run, no street cred      │
└────────────────────────────────────────┘
```

**If choosing Legacy Kit:**
```
┌─ CRAFT LEGACY GEAR ────────────────────┐
│ Available Legacy Ore: 3                │
│                                        │
│ [1] Starforged Blade (Warrior)        │
│     Uses: Starforged Iron             │
│     Stats: +15 dmg, unbreakable       │
│                                        │
│ [2] Moonsilver Staff (Mage)           │
│     Uses: Moonsilver Mithril          │
│     Stats: +60% spell power           │
│                                        │
│ [3] Save for later                    │
│                                        │
│ Craft and start run? (Ore consumed)   │
└────────────────────────────────────────┘
```

### Street Cred System

**Victory Types:**

**PURE VICTORY** - No Legacy gear used
```
════════════════════════════════════════
        🏆 PURE VICTORY! 🏆
════════════════════════════════════════
  You defeated the dungeon without
  relying on Legacy gear!

  Street Cred: MAXIMUM
  Badge: "Purist" ⭐⭐⭐

  Legacy Vault remains untouched.
════════════════════════════════════════
```

**LEGACY VICTORY** - Used Legacy gear
```
════════════════════════════════════════
        ⚔️ LEGACY VICTORY ⚔️
════════════════════════════════════════
  You defeated the dungeon with help
  from your ancestors' Legacy gear.

  Legacy Kit Used:
    • Starforged Blade

  Street Cred: Low
  (But hey, you won!)
════════════════════════════════════════
```

### Achievements & Badges

**Tracked Stats:**
```
PLAYER RECORD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total Runs: 27

  Pure Victories: 2 ⭐⭐⭐
  Legacy Victories: 5 ⚔️
  Deaths: 20 💀

  Pure Win Rate: 7.4% (respectable!)
  Legacy Win Rate: 18.5%

  Legacy Ore Collected: 8 unique pieces
  Legacy Gear Crafted: 12 items
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BADGES EARNED:
  ⭐ First Pure Victory
  ⭐⭐ 5 Pure Victories
  ⭐⭐⭐ 10 Pure Victories

  💎 Legendary Hunter (found all Legacy Ore)
  🔨 Master Crafter (crafted all recipes)
  ⚔️ Legacy Warrior (won with Legacy Kit)
```

**Community Bragging Rights:**
```
"I beat Brogue pure, no Legacy!"
vs
"I'm working toward my first pure win,
 using Legacy to learn the game"
```

### Design Philosophy

**Accessibility vs Mastery:**
- **New players:** Use Legacy gear, learn mechanics, eventually try pure
- **Veterans:** Pure runs for prestige
- **Everyone:** Enjoy finding rare Legacy Ore (dopamine hit!)

**No Pressure:**
- Legacy gear isn't required
- It's a choice at game start
- Pure victories clearly marked (no ambiguity)

**Collection Fun:**
- Hunt for all unique Legacy Ores
- Each has lore and personality
- Build up vault over time
- "Gotta catch 'em all" appeal

### Legacy Ore Spawn Rules

**Rarity:**
- 1-2% chance per floor (very rare!)
- Deeper floors slightly higher chance
- Always announced/highlighted (don't want to miss it!)

**Uniqueness:**
- 10-15 unique Legacy Ore types total
- Each only drops once per run
- Can't get duplicates in vault (quality guaranteed)

**On Death:**
- Legacy Ore ALWAYS saved to vault
- Even if you die with it unmined (auto-collected)
- Regular ore lost as normal

**Strategic Depth:**
- Do I mine this (5+ turns, dangerous)?
- Or mark location and come back safer?
- Legacy Ore worth ANY risk!

---

## 🔨 Crafting System

### Crafting Locations

**Forges** - Special dungeon rooms
- Fixed locations in dungeon
- Fully functional crafting (100% of ore stats transferred)
- Can combine multiple ore types

**Portable Kit** (Ranger advantage)
- Craft anywhere (if Malleability > 60)
- Reduced efficiency (75% of ore stats)
- Limited to simple items

### Crafting Formula

```
Final Item Stats = (Ore Properties × Recipe Multipliers × Class Bonuses) × Purity

Example (Warrior Sword):
  Iron Ore: Hardness 78, Purity 82
  Recipe: Longsword (base damage +4)
  Class: Warrior (+20% hardness bonus)

  Damage = 4 + (78 × 1.2 × 0.82) = +10.7 → +11 damage
```

### Recipe System

Recipes found as loot or learned from NPCs:

**Basic Recipes** (Start with these):
- Simple Sword, Simple Staff, Simple Bow
- Basic Armor, Basic Shield

**Advanced Recipes** (Found in dungeon):
- Longsword, Greatsword, Rapier
- Battle Staff, Channeling Staff
- Compound Bow, Crossbow
- Full Plate, Mage Robes, Leather Armor

**Legendary Recipes** (Boss drops):
- Flaming Sword (requires high conductivity!)
- Arcane Staff (requires balanced hard/conduct)
- Enchanted Bow (tri-stat requirements)

---

## 🎮 Resource Hunting Loop (SWG-Style!)

### 1. Survey Phase

Press 'x' then click/hover over ore tile:

```
You examine the ore deposit...

Iron Ore Vein
  Hardness: 78 (Excellent for weapons!)
  Conductivity: 23 (Poor for magic)
  Overall Quality: 82/100

  → This would make a strong warrior weapon!
```

### 2. Decision Phase

- **High stats?** → Worth mining despite risk
- **Low stats?** → Skip it, keep exploring
- **Class mismatch?** → Might still be useful for secondary equipment
- **Danger nearby?** → Risk mining with monsters around?

### 3. Comparison

Track best ore found so far:

```
Current Inventory:
  Iron Ore (H:78, C:23, P:82) - BEST for warrior weapons
  Copper Ore (H:45, C:67, P:71) - BEST for mage items

→ Always hunting for that 95+ quality spawn!
```

### 4. Strategic Trade-offs

- Mine now and risk monster ambush?
- Mark location and come back later?
- Settle for good ore vs. hunt for perfect ore?
- Use inventory space on variety vs. specialization?

---

## 📊 Progression & Spawn Rules

### Ore Types by Depth

**Copper** (Floors 1-3):
- Common spawn rate: 30%
- Stat range: 20-50
- Good for: Early game gear, practice crafting

**Iron** (Floors 4-6):
- Common spawn rate: 25%
- Stat range: 40-70
- Good for: Mid-game warrior/ranger gear

**Mithril** (Floors 7-9):
- Rare spawn rate: 15%
- Stat range: 60-90
- Good for: Late-game mage gear, enchanted items

**Adamantite** (Floors 10+):
- Very rare spawn rate: 5%
- Stat range: 80-100
- Good for: Legendary crafting, end-game equipment

### Jackpot Spawns (SWG Excitement!)

**5% chance on any floor:**
- Spawn ore 2-3 tiers above normal
- High-quality stats (80-100)
- Creates "OMG PERFECT SPAWN" moments

Example:
```
Floor 2: Find Mithril Ore with 95 Conductivity!
→ This could carry your mage through mid-game!
→ Worth the risk to mine it NOW
```

### Stat Distribution

Properties rolled independently:

```python
def generate_ore_stats(ore_type, floor):
    base_range = ORE_TIERS[ore_type]  # e.g., (40, 70) for Iron
    floor_bonus = floor * 2  # Deeper = better

    return {
        'hardness': roll(base_range) + floor_bonus,
        'conductivity': roll(base_range) + floor_bonus,
        'malleability': roll(base_range) + floor_bonus,
        'purity': roll(base_range) + floor_bonus,
        'density': roll(base_range),  # Not depth-scaled
    }
```

---

## 🎨 Visual Design

### Ore Tile Rendering

**Color by Type:**
- Copper: `#B87333` (copper orange)
- Iron: `#708090` (slate gray)
- Mithril: `#C0C0C0` (silver)
- Adamantite: `#E5E4E2` (platinum shimmer)

**Quality Indicator:**
- Normal quality (50-74): Dim
- High quality (75-89): Bright
- Exceptional quality (90-100): Bright + pulsing effect

**Symbol:**
- Unmined: `◆` (diamond, indicates ore)
- Currently mining: `⛏` (pickaxe symbol)
- Surveyed: `◆` with stat overlay on hover

### UI Elements

**Inventory Screen:**
```
┌─ INVENTORY ────────────────────┐
│ Ores:                          │
│  [1] Iron Ore (H:78 C:23 P:82) │
│  [2] Copper Ore (H:45 C:67)    │
│                                │
│ Equipment:                     │
│  [e] Iron Sword (+11 dmg)      │
│      ↳ From H:78 P:82 ore      │
└────────────────────────────────┘
```

**Mining Progress:**
```
Mining Iron Ore...
[████░░] 3/5 turns
(Vulnerable to attacks!)
```

---

## 🔧 Implementation Plan

### Phase 1: Basic Mining
- [ ] Add ORE tile types to TileType enum
- [ ] Add ore deposits to map generation (5-10 per floor)
- [ ] Implement mining action (press 'm' or move into ore)
- [ ] Multi-turn mining with progress bar
- [ ] Add ore items to inventory

### Phase 2: Ore Properties
- [ ] Create OreDeposit class with stat properties
- [ ] Generate random stats on ore spawn
- [ ] Implement survey action ('x' + examine)
- [ ] Display ore stats in UI
- [ ] Save ore properties in inventory

### Phase 3: Class System
- [ ] Add class selection at game start
- [ ] Implement class stat bonuses
- [ ] Add class-specific UI hints ("Good for warrior!")

### Phase 4: Crafting
- [ ] Add forge room type to dungeon generation
- [ ] Create crafting menu/UI
- [ ] Implement recipe system
- [ ] Calculate final item stats from ore properties
- [ ] Add crafted items to inventory

### Phase 5: Polish
- [ ] Ore quality visual indicators
- [ ] Inventory comparison tools
- [ ] Stat tooltips and explanations
- [ ] Balance tuning
- [ ] Add legendary recipes

---

## ❓ Open Design Questions

### 1. Starting Class
- **Option A:** Choose class at game start (traditional)
- **Option B:** Develop class through playstyle (craft warrior items → become warrior)
- **Option C:** Hybrid system (choose starting bonus, can pivot later)

### 2. Inventory Weight
- **Option A:** No encumbrance (arcade style)
- **Option B:** High density ore slows movement until crafted
- **Option C:** Inventory slots limited (choose what to carry)

### 3. Forge Locations
- **Option A:** Fixed forge rooms (1 per 3 floors)
- **Option B:** Portable crafting kit item (find as loot)
- **Option C:** Town/safe zone with master forge

### 4. Ore Visibility
- **Option A:** Ore visible from adjacent tiles (easy to spot)
- **Option B:** Ore looks like walls until explored/surveyed
- **Option C:** Ranger has "prospecting" skill to detect ore

### 5. Multi-Ore Crafting
- **Option A:** One ore per item (simple)
- **Option B:** Combine 2-3 ores (average stats, or take max?)
- **Option C:** Primary ore + secondary ore (90%/10% influence)

### 6. Ore Depletion
- **Option A:** Each vein gives 1 ore unit (one-time harvest)
- **Option B:** Veins have 2-5 units (can mine multiple times)
- **Option C:** Respawning ore on floor regeneration

---

## 🎯 Strategic Depth

This system adds multiple layers of gameplay:

1. **Exploration incentive** - Hunt for better ore
2. **Risk assessment** - Mine now (vulnerable) or come back later?
3. **Resource management** - What to carry, what to skip
4. **Build planning** - Do I focus on one stat or collect variety?
5. **Replay value** - Different spawns each game
6. **Class identity** - Warriors want different ore than mages
7. **Knowledge building** - Learn what stats matter for your class

**The SWG Magic:** That dopamine hit when you find a 95 hardness iron spawn on floor 2!

---

## 📚 References

**Star Wars Galaxies Resource System:**
- Resources spawned on planets with random quality stats
- Stats affected crafted item properties
- Resource hunters scanned planets for high-quality spawns
- Created entire gameplay loop around resource hunting
- Community shared resource spawn locations and stats

**Applying to Brogue:**
- Replace planets with dungeon floors
- Replace scanning with survey action
- Keep the random stat excitement
- Add turn-based risk (can't just safely harvest)
- Maintain class specialization benefits

---

## 🚀 Next Steps

1. **Validate design** - Get feedback on core mechanics
2. **Create prototype** - Implement Phase 1 (basic mining)
3. **Test feel** - Is mining fun? Good risk/reward balance?
4. **Iterate on properties** - Do stats feel meaningful?
5. **Build crafting** - See if ore→equipment loop is satisfying

**Success Metrics:**
- Players excited to find high-quality ore
- Meaningful choices (mine this or search for better?)
- Class builds feel distinct
- Crafted items feel powerful/personal

---

**Status:** Ready for implementation
**Next Session:** Start with Phase 1 (basic mining mechanics)

**Related Files:**
- Current code: `/home/scottsen/src/tia/projects/brogue/src/core/world.py`
- Current code: `/home/scottsen/src/tia/projects/brogue/src/core/entities.py`
- Prior session: `explosive-beam-1021` (fixed color bug, game now playable)
