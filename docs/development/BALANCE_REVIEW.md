# Veinborn Balance Review

**Purpose:** Pre-playtest analysis of balance configuration
**Status:** ⚠️ Configuration reviewed, needs playtesting validation
**Date:** 2026-01-08

---

## Summary

Balance configuration appears **intentionally challenging** but not obviously broken. Key concerns require playtesting validation:

⚠️ **5 areas to watch during playtest:**
1. Troll encounters on floors 6-10 (potentially unbeatable without crafting)
2. Ore scarcity (only 1 vein on floors 1-9)
3. Mining vulnerability (3-5 turns exposed to 3-12 monsters)
4. Slow health regeneration (1 HP per 10 turns)
5. Equipment power curve vs monster scaling

---

## Combat Math (Level 1, No Equipment)

### Player Starting State
- **HP:** 20
- **Attack:** 5
- **Defense:** 2
- **Damage formula:** `max(1, ATK - DEF)`

### Monster Balance Analysis

| Monster | HP | ATK | DEF | Player DMG | Monster DMG | Hits to Kill | Player Takes | Outcome |
|---------|----|----|-----|-----------|------------|-------------|-------------|---------|
| **Goblin** | 6 | 3 | 1 | 4 | 1 | 2 | 2 HP | ✅ Easy win |
| **Bat** | 4 | 2 | 0 | 5 | 1 | 1 | 0 HP | ✅ Trivial |
| **Orc** | 12 | 5 | 2 | 3 | 3 | 4 | 12 HP | ⚠️ Challenging |
| **Skeleton** | 10 | 4 | 1 | 4 | 2 | 3 | 6 HP | ✅ Fair |
| **Wolf** | 8 | 4 | 1 | 4 | 2 | 2 | 4 HP | ✅ Fair |
| **Troll** | 20 | 7 | 3 | 2 | 5 | 10 | 50 HP | 🔴 **UNWINNABLE** |

**Critical finding:** Troll requires 10 hits and would deal 50 damage to kill. Player only has 20 HP.

### Troll Spawn Analysis
- **Floors 6-10:** 5% spawn weight (low but possible)
- **Floors 11-15:** 15% spawn weight (common)
- **Floors 16+:** 30% spawn weight (very common)

**Implication:** Player MUST craft better equipment before floor 6, or avoid trolls.

---

## Crafting Progression

### Weapon Tiers (Base weapon = Sword, 3 ATK)

| Tier | Material | Multiplier | ATK (100% purity) | Player DMG vs Troll |
|------|----------|------------|-------------------|---------------------|
| 1 | Copper | 1.0x | 3 | 2 (10 hits) |
| 2 | Iron | 1.3x | ~4 | 3 (7 hits) |
| 3 | Steel | 1.6x | ~5 | 4 (5 hits) |
| 4 | Adamantite | 2.0x | 6 | 5 (4 hits) |

**Note:** Formula is `base * (1 + purity/100) * tier_mult`

### Armor Tiers (Base armor = Leather, 2 DEF)

| Tier | Material | Multiplier | DEF (100% purity) | Troll DMG to Player |
|------|----------|------------|-------------------|---------------------|
| None | - | - | 2 | 5 HP/hit |
| 1 | Copper | 1.0x | 2 | 5 HP/hit |
| 2 | Iron | 1.3x | ~3 | 4 HP/hit |
| 3 | Steel | 1.6x | ~3 | 4 HP/hit |
| 4 | Adamantite | 2.0x | 4 | 3 HP/hit |

**Observation:** Armor has less impact than weapons due to rounding in formula.

---

## Resource Availability

### Ore Vein Spawns

| Floor Range | Ore Veins per Floor | Material Types Available |
|-------------|---------------------|--------------------------|
| 1-9 | 1 | Copper, Iron |
| 10-19 | 2 | Iron, Steel, Mithril |
| 20-29 | 3 | Steel, Mithril, Adamantite |
| 30+ | 4 | Mithril, Adamantite |

**Concern:** Only 1 ore vein on early floors. If player doesn't find it or mining gets interrupted, they may not have materials for crafting before troll encounters.

### Mining Mechanics
- **Base time:** 3-5 turns (based on hardness)
- **During mining:** Player is VULNERABLE (can be attacked)
- **Interruption:** Loses progress if attacked (needs validation)

**Risk:** With 3-12 monsters per floor, mining might be too dangerous without clearing enemies first.

---

## Monster Scaling

### Monster Counts by Floor

| Floor | Monster Count | Formula |
|-------|---------------|---------|
| 1 | 3 | 3 + (1 // 2) |
| 3 | 4 | 3 + (3 // 2) |
| 5 | 5 | 3 + (5 // 2) |
| 7 | 7 | 5 + (7 // 3) |
| 10 | 8 | 5 + (10 // 3) |
| 15 | 10 | 5 + (15 // 3) |
| 20 | 12 | min(12, 8 + (20 // 10)) |

**Analysis:** Gradual scaling, caps at 12. Reasonable progression.

### Spawn Weight Progression

Floor 1: **80% Goblins** → Tutorial floor ✅
Floor 2: **50% Goblins, 20% Orcs** → Difficulty ramp ✅
Floors 6-10: **5% Trolls** → Skill check (requires crafting) ⚠️
Floors 16+: **30% Trolls** → Late game, expect good gear ✅

---

## Health & Sustain

### Regeneration System
- **In combat:** No regeneration
- **Out of combat:** 1 HP per 10 turns
- **HP per level:** +5 HP

**Math:**
- Take 12 damage from Orc → Need 120 turns (12 * 10) to fully heal
- At ~1 turn per second → **2 minutes of waiting** to heal

**Concern:** This might feel grindy. Players may need to:
1. Play very conservatively (kite, retreat)
2. Find healing items (if they exist)
3. Accept attrition deaths

**Playtest question:** Does healing feel too slow?

---

## Critical Hit System
- **Chance:** 10%
- **Multiplier:** 2x damage

**Impact examples:**
- Goblin (4 dmg) → 8 dmg crit (one-shot with crit)
- Troll (5 dmg) → 10 dmg crit (player loses half HP in one hit)

**Analysis:** 10% adds excitement without being swingy. Good RNG.

---

## Floor Difficulty Tiers

| Tier | Floors | Expected State |
|------|--------|----------------|
| **Tutorial** | 1-3 | No equipment needed, learn basics |
| **Early Game** | 4-6 | Need basic crafting (copper/iron gear) |
| **Mid Game** | 7-10 | Need good gear (steel), trolls appear |
| **Late Early** | 11-15 | Strong gear expected, troll-heavy |
| **Late Game** | 16+ | Elite gear, many trolls and ogres |

**Design intent:** Forces crafting loop by floor 4-5 to survive troll encounters.

---

## Potential Balance Issues (Requires Playtesting)

### 🔴 CRITICAL: May break the game

1. **Ore scarcity + Troll wall**
   - If player doesn't find the 1 ore vein on floors 1-5
   - And encounters a troll on floor 6
   - **Result:** Unwinnable encounter, run ends
   - **Mitigation needed?** More ore veins, or guaranteed ore on early floors

### ⚠️ HIGH: May feel unfair/frustrating

2. **Mining vulnerability**
   - 3-5 turns exposed while mining
   - 3-12 monsters wandering
   - **Potential outcome:** Mining becomes too risky, crafting inaccessible
   - **Question:** Can player mine safely? Clear enemies first?

3. **Health regeneration grind**
   - 1 HP per 10 turns = very slow
   - Encourages waiting/grinding vs playing
   - **Question:** Does downtime feel tedious?

4. **Orc damage spike**
   - Goblins deal 1 dmg, Orcs deal 3 dmg (3x jump)
   - Floor 2 introduces Orcs at 20% weight
   - **Question:** Is floor 2 difficulty spike too harsh?

### 📝 MEDIUM: Might need tuning

5. **Critical hit swingyness**
   - 10% chance for 2x damage is good
   - But troll crit (10 dmg) could feel unfair
   - **Question:** Do crits feel exciting or punishing?

6. **Monster count scaling**
   - Caps at 12 monsters on floor 21+
   - **Question:** Does late game feel chaotic or manageable?

7. **Armor effectiveness**
   - Armor gives less benefit than weapons due to formula
   - **Question:** Do players prioritize weapons over armor?

---

## Class Balance (Not Validated)

### Starting Stats by Class

| Class | HP | ATK | DEF | Special |
|-------|----|----|-----|---------|
| Warrior | ? | Higher? | Higher? | Tanky? |
| Mage | ? | Magic? | Lower? | Spells? |
| Rogue | ? | Medium? | Lower? | Fast? |
| Healer | ? | Lower? | Medium? | Heals? |

**Note:** Class stats not found in reviewed config files. Need to check entity data.

**Playtest question:** Do classes feel meaningfully different?

---

## Playtesting Focus Areas

### During Session 1 (Warrior Baseline), track:

1. **Floors 1-3:**
   - Can player learn without dying?
   - Is goblin difficulty appropriate?
   - How many ore veins found?
   - Was mining interrupted? How often?

2. **Floor 4-6 (First Skill Check):**
   - Did player craft equipment?
   - What tier? (Copper/Iron/Steel)
   - Orc difficulty?
   - **If Troll encountered:** Winnable? Stats when encountered?

3. **Deaths:**
   - Which floor?
   - Which monster type?
   - Player stats at death?
   - Had crafted gear?

4. **Crafting Loop:**
   - Time from "need gear" to "found forge"?
   - Was ore available?
   - Did crafting feel rewarding?

---

## Specific Metrics to Track

### Combat Metrics
- Average hits to kill each monster type
- Average damage taken per floor
- Number of "close call" fights (< 5 HP remaining)
- Number of deaths to each monster type

### Resource Metrics
- Ore veins found per floor
- Ore veins successfully mined (vs interrupted)
- Time between crafting opportunities
- Forge encounter rate

### Progression Metrics
- Floor reached on each run
- Equipment tier when encountering first troll
- HP/ATK/DEF at floors 1, 3, 5, 7, 10

### Feeling Metrics (Qualitative)
- Did mining feel dangerous or tedious?
- Did healing feel too slow?
- Did crafting feel rewarding?
- Did trolls feel like "skill checks" or "unfair walls"?

---

## Configuration Summary

**What looks good:**
- ✅ Monster variety and progression (19 types)
- ✅ Clear difficulty tiers
- ✅ Intentional "gear check" design (trolls)
- ✅ Simple, understandable formulas
- ✅ Good critical hit balance (10%, 2x)

**What needs validation:**
- ⚠️ Ore scarcity on early floors
- ⚠️ Mining risk vs reward
- ⚠️ Health regeneration speed
- ⚠️ Troll encounter timing vs player power
- ⚠️ Class differentiation

**Overall assessment:** **Intentionally challenging design.** Not broken, but several "might be too harsh" areas that need human playtesting to validate.

---

## Recommended Playtest Approach

1. **Session 1:** Play Warrior with notes on every ore/forge/troll encounter
2. **After Session 1:** Review this document and mark findings
3. **Session 2-3:** Test other classes, specifically look for:
   - "Mining too dangerous" moments
   - "Healing too slow" moments
   - "Trolls feel unfair" moments
   - "Crafting feels bad" moments

4. **Analysis:** If 2+ sessions confirm any concern, plan balance patch

---

## Quick Reference: Monster Threat Levels (Level 1 Player)

| Threat | Monsters | Floor | Strategy |
|--------|----------|-------|----------|
| 🟢 **Trivial** | Bat, Goblin | 1-3 | Free kills, learn combat |
| 🟡 **Fair** | Skeleton, Wolf | 3-6 | Tactical positioning |
| 🟠 **Challenging** | Orc | 2-10 | Requires full HP |
| 🔴 **Requires Gear** | Troll, Ogre | 6+ | MUST have crafted weapon |
| 🟣 **Unknown** | Imp, Spider, Others | 6+ | Need playtesting |

---

## Next Steps

1. ✅ Configuration reviewed
2. ⏳ Execute PLAYTEST_PROTOCOL.md (Session 1-5)
3. ⏳ Validate each "⚠️" concern
4. ⏳ Create balance patch based on findings
5. ⏳ Re-test with adjusted values

**Blocker:** Cannot validate without human playtesting (10-20 hours)

---

**Last updated:** 2026-01-08
**Status:** Awaiting playtest validation
**Next:** Start Session 1 (Warrior Baseline) per PLAYTEST_PROTOCOL.md
