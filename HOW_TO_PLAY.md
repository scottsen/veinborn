# How to Play Veinborn

**A 5-minute guide to your first game**

---

## Quick Start

```bash
# Run the game
./veinborn
```

You'll see a dungeon with:
- **@** = You (the player)
- **#** = Walls
- **.** = Floor
- **g, o, T** = Monsters (goblin, orc, troll)
- **◆** = Ore veins (mine these!)
- **>** = Stairs down (go deeper)

---

## Basic Controls

### Movement
```
Arrow Keys or HJKL:
  ↑ k        Move up
← h   l →    Move left/right
  ↓ j        Move down

Diagonal Movement (YUBN):
y   u    Move diagonally
  @
b   n
```

### Actions
- **Walk into a monster** = Attack it (bump-to-attack)
- **s** = Survey ore (see its properties)
- **m** = Mine ore (takes 3-5 turns, you're vulnerable!)
- **c** = Craft equipment (when at a forge)
- **e** = Equip/unequip items
- **i** = View inventory
- **>** = Descend stairs (when standing on them)
- **R** = Restart game (after death)
- **Q** = Quit to menu

### Pro Tips
- **Hold Shift + direction** = Fast movement (be careful!)
- **Wait (.)** = Skip your turn (let monsters come to you)

---

## Your First Game (Step-by-Step)

### Step 1: Move Around (30 seconds)
1. Press **arrow keys** or **h/j/k/l** to move
2. Explore the dungeon
3. Try not to die yet!

### Step 2: Fight Your First Monster (1 minute)
1. Find a **goblin (g)** - they're weak
2. Walk into it to attack
3. Keep attacking until it dies
4. Watch your HP in the top-left corner
5. **If HP gets low, run away!**

### Step 3: Mine Your First Ore (2 minutes)
1. Find an **ore vein (◆)** in a wall
2. Stand next to it
3. Press **s** to survey it (see its properties)
4. Press **m** to mine it
5. Wait 3-5 turns for mining to complete
6. **Warning:** You can't move while mining!

**Ore Properties Explained:**
```
Hardness      78  ████████░░  → Weapon damage / Armor defense
Conductivity  23  ██░░░░░░░░  → Magic power
Malleability  65  ██████░░░░  → Durability
Purity        82  ████████░░  → Quality multiplier (IMPORTANT!)
Density       45  █████░░░░░  → Weight
```

Higher numbers = better! Purity amplifies everything.

### Step 4: Craft Your First Weapon (1 minute)
1. Find a **forge** (special room with anvil symbol)
2. Stand in the forge room
3. Press **c** to open crafting menu
4. Select a recipe (try "Copper Sword")
5. If you have the right ore, craft it!
6. Press **e** to equip your new weapon

### Step 5: Go Deeper
1. Find the **stairs down (>)**
2. Stand on them
3. Press **>** to descend
4. Floor 2 has stronger monsters and better ore!

### Step 6: Die Gloriously
1. Eventually, you'll die (it's a roguelike!)
2. That's okay! You learn from each run
3. Press **R** to restart

---

## Core Gameplay Loop

```
1. Explore dungeon
   ↓
2. Find ore veins
   ↓
3. Survey ore (check quality)
   ↓
4. Mine ore (risky! takes time)
   ↓
5. Find forge
   ↓
6. Craft equipment
   ↓
7. Equip better gear
   ↓
8. Fight stronger monsters
   ↓
9. Go deeper (stairs down)
   ↓
10. Repeat until death or victory!
```

---

## Understanding Stats

### Your Character
- **HP (Hit Points):** Your health. 0 HP = death
- **Attack:** Damage you deal in combat
- **Defense:** Reduces damage from monsters
- **XP (Experience):** Gain by killing monsters
- **Level:** Increases stats when you level up

### Combat Math (Simple)
```
Damage = Your Attack - Enemy Defense
(minimum 1 damage per hit)
```

Example:
- Your attack: 5
- Goblin defense: 1
- You deal: 4 damage per hit
- Goblin HP: 6
- Kills in: 2 hits!

---

## Character Classes

Choose at game start:

### Warrior (Red @)
- **Best at:** Melee combat, tanking
- **High:** HP, Attack
- **Wants:** High hardness ore (weapon damage)
- **Playstyle:** Get in their face, trade hits

### Mage (Blue @)
- **Best at:** Magic, area damage
- **High:** Magic power
- **Wants:** High conductivity ore (spell power)
- **Playstyle:** Keep distance, use spells

### Rogue (Green @)
- **Best at:** Critical hits, mobility
- **High:** Crit chance, dodge
- **Wants:** Balanced ore (versatility)
- **Playstyle:** Hit and run, backstabs

### Healer (Yellow @)
- **Best at:** Survival, support
- **High:** HP regeneration
- **Wants:** High purity ore (quality)
- **Playstyle:** Outlast enemies

---

## Mining Strategy

### Should I Mine This Ore?

**ALWAYS mine if:**
- ✅ Purity 80+ (saves to Legacy Vault on death!)
- ✅ High hardness + high purity (great for weapons)
- ✅ No monsters nearby (safe to mine)

**MAYBE mine if:**
- ⚠️ Purity 60-79 (decent)
- ⚠️ One property very high (specialized use)
- ⚠️ Monsters far away (you have time)

**DON'T mine if:**
- ❌ Purity below 40 (trash ore)
- ❌ Monsters adjacent (you'll die mid-mining!)
- ❌ All properties low (not worth the risk)

### Mining Tips
1. **Survey first** (press **s**) to see if ore is worth it
2. **Clear monsters** before mining (you're vulnerable!)
3. **Look for purity 80+** (saves to Legacy Vault)
4. **Remember:** Mining takes 3-5 turns, you can't move

---

## Crafting Strategy

### Recipe Tiers
- **Basic:** Copper equipment (floors 1-3)
- **Advanced:** Iron/Mithril (floors 4-7)
- **Legendary:** Boss drops (floors 8+)

### What to Craft First
1. **Weapon** - Increases damage (priority!)
2. **Armor** - Reduces damage taken
3. **Accessories** - Special bonuses

### Stat Formulas (For Nerds)
```
Weapon Damage = Base + (Hardness × Purity)
Armor Defense = Base + (Hardness × Purity)
Magic Power = Base + (Conductivity × Purity)
```

Higher purity = MUCH better equipment!

---

## The Legacy Vault (Meta-Progression)

### What Is It?
When you die, any ore with **purity 80+** is saved to your Legacy Vault.

### Starting a New Run
You can choose:
- **Pure Victory** - No vault gear (harder, more prestige!)
- **Legacy Victory** - Withdraw 1 ore from vault (easier start)

Both are valid! The vault helps you learn without being OP.

### Why It's Cool
- Bad luck? Use vault ore to catch up
- Good luck? Save 90+ purity for future runs
- Street cred for Pure Victories
- Accessibility for new players

---

## Death & Progression

### When You Die
1. Game shows your stats (floor reached, monsters killed, etc.)
2. High purity ore (80+) saved to Legacy Vault
3. Press **R** to restart

### What You Keep Between Runs
- ✅ Knowledge (monster patterns, map layouts)
- ✅ Legacy Vault ore (purity 80+)
- ✅ Experience as a player

### What You Lose
- ❌ Current character
- ❌ Current equipment
- ❌ Current dungeon progress
- ❌ All ore below 80 purity

**That's roguelikes!** Each run is fresh, but you get better.

---

## Common Mistakes (Don't Do This!)

### ❌ Mining While Monsters Are Nearby
**Problem:** You're stuck mining for 3-5 turns, monster kills you
**Solution:** Clear the area first, then mine

### ❌ Ignoring Purity
**Problem:** You mine hardness 90, purity 30 ore (actually mediocre!)
**Solution:** Purity multiplies everything. 70 hardness + 90 purity > 90 hardness + 30 purity

### ❌ Not Equipping Crafted Gear
**Problem:** You craft a sword but forget to equip it (still using fists!)
**Solution:** Press **e** after crafting to equip

### ❌ Going Deeper Too Fast
**Problem:** Floor 5 monsters oneshot you
**Solution:** Mine/craft gear on current floor before descending

### ❌ Not Surveying Ore
**Problem:** Wasted 4 turns mining trash ore
**Solution:** Press **s** first, check purity, then decide

---

## Advanced Tips (After 5+ Runs)

### Combat
- Corner monsters (they can't flank you)
- Kite tough enemies (hit and run)
- Use corridors (1v1 instead of 1v3)

### Mining
- Mine on your way back to stairs (safer retreat path)
- Prioritize purity 80+ (Legacy Vault value!)
- Specialized ore = class synergy (hardness for warriors)

### Crafting
- Wait for high purity ore (equipment scales HARD)
- Save legendary recipes for best ore
- Craft armor if HP is low, weapon if HP is fine

### Progression
- Farm current floor until gear is good
- Descend when you can tank 3+ monster hits
- Remember floor layouts (forges, ore clusters)

---

## Keybind Reference Card

```
MOVEMENT          COMBAT            MINING
↑ k    y  u       Walk into enemy   s - Survey ore
← h @ l →    @    = Attack          m - Mine ore
↓ j    b  n                         c - Craft (at forge)

INVENTORY         PROGRESSION       GAME
i - Inventory     > - Descend       R - Restart
e - Equip         < - Ascend        Q - Quit
d - Drop                            ? - Help
```

---

## Your First 3 Runs (Goals)

### Run 1: Learn Movement
- ✅ Move around
- ✅ Kill 1 goblin
- ✅ Die to something stronger

### Run 2: Learn Mining
- ✅ Survey an ore vein
- ✅ Mine an ore vein
- ✅ Check ore properties

### Run 3: Learn Crafting
- ✅ Find a forge
- ✅ Craft your first weapon
- ✅ Equip it
- ✅ Try to reach floor 2

---

## When Things Go Wrong

### "My terminal is broken after crash"
```bash
reset    # Type this and press Enter
```

### "I don't see any ore veins"
Look for **◆** symbols in walls (not floors). They blend in!

### "Mining doesn't work"
1. Stand **next to** the ore (adjacent, not on it)
2. Press **s** to survey first
3. Then press **m** to mine
4. Wait for mining to finish (3-5 turns)

### "I can't craft anything"
- Are you in a forge room? (look for forge symbol)
- Do you have ore in inventory? (press **i** to check)
- Do you have the right ore type? (recipe specifies)

### "Monsters are too hard"
- Farm current floor until you have better gear
- Kite monsters (hit and run)
- Use corridors (1v1 fights)
- Don't descend until ready

---

## What Makes Veinborn Different?

### The Mining Hook (SWG-Style)
Every ore vein has **random properties**. Finding a 95 purity ore is like finding a legendary drop in Diablo!

**"OMG PERFECT SPAWN!"** moments = dopamine hits

### The Risk/Reward
Mining takes 3-5 turns and you **can't move**. Do you mine risky ore now or come back later?

### Meaningful Crafting
Ore properties directly determine equipment stats. That 90 purity ore becomes a +70 damage sword!

### Meta-Progression That Doesn't Break the Game
Legacy Vault lets you save great ore, but only 1 piece per run. You still earn victories.

---

## Next Steps

### After Your First Win (Reach Floor 3+)
1. Try different character classes
2. Learn monster patterns (which are dangerous?)
3. Optimize mining strategy (when to mine, what to mine)
4. Experiment with legendary recipes

### Join the Community
- Share perfect ore spawns (screenshots!)
- Compare Pure Victory times
- Trade crafting strategies
- Help new players learn

---

## Questions?

**"Is there a tutorial?"**
- Not yet! This guide is it for now
- Press **?** in-game for keybind reference

**"Can I save mid-game?"**
- Not yet, but coming soon!

**"Is multiplayer available?"**
- Not yet! Single-player MVP first
- Co-op planned for future (4-player!)

**"Where's the story?"**
- Minimal! You're rescuing your bro from the dungeon
- Gameplay > narrative (it's a roguelike!)

---

## Ready to Play?

```bash
./veinborn
```

**Good luck, delver!** May your ore spawns be legendary. 🎮⚒️

---

**Pro tip:** Your first 5 runs will be learning runs. Embrace the deaths. Knowledge is the true progression!
