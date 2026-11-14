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
- **Walk into an ore vein** = Mine it (bump-to-mine; takes 3-5 turns, you're vulnerable!)
- **s** = Survey nearby ore (see its properties)
- **z** = Use your class ability (mage force bolt, healer heal)
- **g** = Pick up items on your tile (potions and scrolls are not picked up automatically)
- **e** = Eat or drink: uses the cheapest potion or food that covers your missing HP
- **d** = Drop the item least worth carrying: things with no use yet (gold, shields, scrolls,
  rings), then weapons/armor worse than what you wear, then the lowest-purity ore. Press again
  to drop the next. Walking over something you dropped does not pick it back up; **g** does.
- **i** = View inventory
- **w** = Equipment screen: what you wear (weapon, armor, shield) and the weapons/armor/shields in your pack, with each pack item's change vs what you wear. ↑/↓ select, **Enter** wields/wears a pack item or removes a worn one, **x** removes the worn item, **Esc** closes. Swapping and removing take no turn.
- **:** = Look at what's on the ground
- **.** or **space** = Wait / pass turn
- **c** or **enter** = Chat (multiplayer)
- **>** = Descend stairs (when standing on them)
- **S** / **L** = Save / Load game
- **r** = Restart (after death) — **q** = Quit

### Pro Tips
- **Mining happens automatically** when you bump an ore vein — no key needed
- **Crafting** happens contextually at forges (walk onto a forge tile)
- **Wait (.)** = Skip your turn (let monsters come to you). It is also how you **rest**: you heal
  3x faster after a wait when no monster can see you (see *Healing* in docs/MECHANICS_REFERENCE.md)
- **Monsters see, they don't sense:** each notices you only within its own sight range and
  with no wall in the way; once it has seen you it keeps hunting for a while after you break
  line of sight. Some are far-sighted (wraith), some near-sighted (troll, mimic)
- **Hitting a monster makes it come for you**, even from far away (a force bolt included);
  neutral monsters only fight back when attacked
- **Speed differs:** bats get extra moves, golems and ogres lag behind
- **Hurt defensive monsters flee**; aggressive ones and guards fight to the death

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
3. Press **s** to survey nearby veins (see their properties)
4. **Walk into the vein** to start mining (bump-to-mine)
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
1. Find a **forge** (yellow █ tile)
2. Walk onto the forge to trigger the crafting menu
3. Select a recipe (try "Copper Sword")
4. If you have the right ore, craft it!
5. Press **w** to wield your new weapon

### Step 5: Go Deeper
1. Find the **stairs down (>)**
2. Stand on them
3. Press **>** to descend
4. Floor 2 has stronger monsters and better ore!

### Step 6: Die Gloriously
1. Eventually, you'll die (it's a roguelike!)
2. That's okay! You learn from each run
3. Press **r** to restart

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
- **Attack:** How often you hit, and how hard
- **Defense:** How often monsters hit you, and how hard
- **XP (Experience):** Gain by killing monsters (sidebar shows `XP: now/next`)
- **Level:** Each level adds HP and +1 attack. Defense comes from armor.

### Combat Math (Simple)
Every swing rolls a d20 to hit, then rolls damage:
```
Hit if:  d20 + Your Attack >= 10 + Enemy Defense   (1 always misses, 20 always hits)
Damage:  roll around Your Attack (+/- 50%) - Enemy Defense   (minimum 1)
```

Example:
- Your attack: 5, goblin defense: 1
- You hit on a 6 or better (75%)
- Each hit rolls 3-7, minus 1: 2-6 damage
- Goblin HP: 6, usually dead in 2-3 swings

Levels come fast early (20 XP for level 2, 40 for 3, 80 for 4) and then double.

---

## Character Classes

Choose at game start. Starting HP / Attack / Defense: Warrior 30/5/3,
Rogue 20/4/2, Mage 15/3/1, Healer 25/3/4. The warrior starts wearing a short
sword and leather armor, the rogue wielding a dagger (their Attack/Defense
include that gear). Three abilities work today; the rest described below
(area spells, dodge, crits, regeneration) are planned.

- **Mage:** press **z** to cast *force bolt* at the nearest monster in sight
  (6 tiles). It never misses and ignores defense; ready again after 3 turns.
  Open with bolts as monsters approach, melee is weak.
- **Healer:** press **z** to heal yourself (6 HP, +1 per level; ready again
  after 12 turns). Wasted at full health, so it costs no turn then.
- **Rogue:** *backstab* is automatic: your first hit on an unhurt monster does
  double damage.
- **Warrior:** no ability yet; the tough one.

### Warrior (Red @)
- **Best at:** Melee combat, tanking
- **High:** HP, Attack
- **Wants:** High hardness ore (weapon damage)
- **Playstyle:** Get in their face, trade hits

### Mage (Blue @)
- **Best at:** Ranged damage
- **Has:** Force bolt (z)
- **Wants:** High conductivity ore (spell power)
- **Playstyle:** Keep distance, bolt, then finish in melee

### Rogue (Green @)
- **Best at:** Opening strikes
- **Has:** Backstab (double damage on an unhurt monster)
- **Wants:** Balanced ore (versatility)
- **Playstyle:** Pick your fights, strike first

### Healer (Yellow @)
- **Best at:** Survival, support
- **Has:** Heal (z)
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
**Solution:** Press **w** after crafting to wield it

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
MOVEMENT          COMBAT / MINING         ITEMS
↑ k    y  u       Walk into enemy         i - Inventory
← h @ l →         = Attack                w - Equipment (wear/remove)
↓ j    b  n       Walk into ore vein
                  = Mine (bump-to-mine)   g - Pick up
                  s - Survey ore          e - Eat/drink (heal)
                  z - Class ability       d - Drop (least useful)
                                          : - Look at ground

TURN / FLOW       PROGRESSION             GAME
. or space        > - Descend stairs      S - Save   L - Load
  = Wait / pass   (crafting happens       r - Restart
c or enter        on forge tiles)         q - Quit
  = Chat (MP)
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
1. Stand **next to** the ore vein (adjacent, not on it)
2. Press **s** to survey first (optional)
3. **Walk into the vein** — mining starts automatically
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
- Yes, co-op for up to 4 players in the terminal: see [docs/MULTIPLAYER_PLAYTEST.md](docs/MULTIPLAYER_PLAYTEST.md)

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
