# Brogue: Consolidated Game Design
**Session:** garnet-pigment-1022
**Date:** 2025-10-22
**Status:** Master Design Document

---

## Core Vision

**Brogue is NetHack + SWG Mining + Multiplayer Co-op**

A mechanical roguelike where you and your bros dive into procedural dungeons, hunt for perfect ore spawns, craft legendary gear, and fight your way deeper to rescue your lost bro.

**Design Philosophy:**
- Tight mechanics over narrative
- "Git gud" difficulty
- Social play (bros playing together)
- Replayability through randomization
- Street cred for skill

---

## The Name & Quest

### Why "Brogue"?
1. Sounds like "Rogue" (the genre)
2. Community is "bros" (multiplayer culture)
3. Quest is to save your bro (simple motivation)

### The Quest
- Your brother went into the dungeon and didn't come back
- You're going in to find him
- **That's it.** No emotional progression, no memory triggers
- Classic quest hook (like "rescue the princess")

### Community Culture
- "Bros playing together"
- Helping each other find perfect ore spawns
- Trading gear
- Street cred for Pure Victories (no Legacy gear)
- Sharing strategies

---

## Core Game (The NetHack Part)

### What Makes a Good Roguelike
```
✓ Procedural generation → Every run different
✓ Permadeath → Stakes are real
✓ Turn-based → Tactical, not twitchy
✓ Items matter → Finding good loot = exciting
✓ Emergent gameplay → Simple rules, complex outcomes
✓ Knowledge > reflexes → Learn patterns, get better
✓ "One more run" factor → Quick restart
```

### Brogue's Core Loop
```
1. Generate dungeon
2. Explore, find ore/loot
3. Mine ore (vulnerable for turns - risky!)
4. Craft gear from ore
5. Fight monsters, go deeper
6. Die or win
7. Restart with new knowledge
```

### Essential Systems (MVP)

**Movement & Combat:**
- 8-direction grid movement
- Turn-based (your turn → monsters' turns)
- Melee combat (bump to attack)
- Ranged combat (bows, magic)
- Status effects (burning, frozen, etc.)

**Map Generation:**
- BSP dungeon algorithm
- Rooms + corridors
- Multiple floors (descend stairs)
- Ore veins scattered throughout

**Inventory:**
- Equipment slots (weapon, armor, ring, etc.)
- Consumables (potions, scrolls)
- Crafting materials (ores)
- Limited carry capacity

**Death:**
- Permadeath (lose run progress)
- Legacy Ore saved to vault
- Quick restart
- Learn from mistakes

---

## Extra Stuff #1: SWG-Style Mining/Crafting

### The Mining System

**Core Mechanic:**
- Ore veins appear as special wall tiles (`◆`)
- Survey ore to see properties (1 turn action)
- Mine ore (takes 3-5 turns, you're vulnerable!)
- Risk/reward: Mine now or come back safer?

**Ore Properties (0-100 scale):**
```
Hardness      → Weapon damage / Armor defense
Conductivity  → Magic power / Spell efficiency
Malleability  → Durability / Repair ease
Purity        → Quality multiplier (affects all)
Density       → Weight / Encumbrance
```

**Example Ore:**
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
  Mining Time: 4 turns
  [M]ine  [L]eave
```

**Why This is Fun:**
- Resource hunting mini-game ("find that 95+ hardness iron!")
- Meaningful decisions (mine risky ore now or keep searching?)
- Class specialization (warriors want hardness, mages want conductivity)
- SWG dopamine hit when you find perfect spawn

### The Crafting System

**How It Works:**
```
Ore Properties × Recipe × Class Bonus = Final Item Stats

Example:
  Iron Ore: Hardness 78, Purity 82
  Recipe: Longsword (base +4 damage)
  Class: Warrior (+20% hardness bonus)

  Damage = 4 + (78 × 1.2 × 0.82) = +11 damage
```

**Crafting Locations:**
- Forges (special dungeon rooms)
- Portable kit (Rangers can craft in field)

**Recipes:**
- Basic (start with these): Simple Sword, Staff, Bow
- Advanced (find in dungeon): Longsword, Battle Staff
- Legendary (boss drops): Flaming Sword, Arcane Staff

### Ore Spawning Rules

**Ore Types by Depth:**
- Copper (Floors 1-3): Stats 20-50
- Iron (Floors 4-6): Stats 40-70
- Mithril (Floors 7-9): Stats 60-90
- Adamantite (Floors 10+): Stats 80-100

**Jackpot Spawns:**
- 5% chance per floor for ore 2-3 tiers above normal
- High-quality stats (80-100)
- Creates "OMG PERFECT SPAWN" moments

**Properties Rolled Independently:**
- Each ore gets random roll for each stat
- Sometimes you find high hardness + high conductivity (perfect for hybrid builds)
- Sometimes you find trash (skip it)

---

## Extra Stuff #2: Multiplayer Co-op

### The Brilliant Turn System

**Core Rule:** "4 actions per round, anyone can take them"

**How It Works:**
```
Round 1:
  Warrior presses 'h' → Move action (1/4)
  Mage presses 'f' → Fireball (2/4)
  Warrior presses 'h' again → Move (3/4) [fast player!]
  Healer presses 'h' → Heal Warrior (4/4)

  → Monsters take their turns (all of them)

Round 2:
  Rogue takes 4 stealth moves (scouting ahead)

  → Monsters act

Round 3:
  Healer takes all 4 actions (mass healing emergency!)

  → Monsters act
```

**Why This is Genius:**
- ✅ No waiting (take actions when you want)
- ✅ Cooperative strategy (let healer take all 4 turns)
- ✅ Competitive fun (race for kill)
- ✅ Skill expression (fast vs deliberate players)
- ✅ Emergent teamwork

**Strategic Depth Examples:**

**Scenario: Healer Emergency**
```
Party at low HP after boss AOE
Team: "Everyone HOLD!"
Healer takes all 4 actions:
  1. Heal Warrior
  2. Heal Mage
  3. Heal Rogue
  4. Move to safety
```

**Scenario: Mining Operation**
```
Warrior: "Mining high-quality ore, 4 turns"
Team covers while warrior mines
Warrior takes all 4 actions mining
Team kills monsters that attack
```

**Scenario: Race for Kill**
```
One goblin left, 2 HP
Warrior, Mage, Rogue all MASH keys
First action to land kills it
Others: "Dammit!" (friendly competition)
```

### Four-Player Classes

**Warrior (Red @) - Tank & DPS:**
- High HP (starts 20 vs 10)
- Taunt (draw monster aggro)
- Cleave (hit multiple adjacent)
- Wants: High hardness ore (melee damage)

**Mage (Blue @) - Magic DPS:**
- Low HP (starts 8)
- AOE spells (fireball, lightning)
- Crowd control (freeze, slow)
- Wants: High conductivity ore (spell power)

**Rogue (Green @) - Mobility & Crits:**
- Medium HP (starts 12)
- Backstab (3x damage from behind)
- Stealth (invisible, 5 turn cooldown)
- Trap detection
- Wants: Balanced stats (versatile)

**Healer (Yellow @) - Support:**
- Medium HP (starts 12)
- Heal party members (ranged)
- Buff allies (+defense, +damage)
- Resurrect (1/floor, bring back dead player)
- Wants: High conductivity + purity (healing power)

### Personal Loot System

**The Killer Feature:** Everyone gets their own ore roll from the same vein

```
Same ore vein:
  Alice (Warrior) mines → Iron Ore (H:90! Perfect!)
  Bob (Mage) mines → Iron Ore (C:85! Perfect!)
  Carol (Rogue) mines → Iron Ore (H:45, C:40, meh)
  Dave (Healer) mines → Iron Ore (C:78, good)

Everyone happy! No fighting over loot!
```

**Can still trade:**
- "I'll trade my H:90 for your C:85"
- Negotiate, help each other optimize

### Multiplayer Architecture

**Server-Authoritative:**
- Server validates all actions (no cheating)
- Clients are "dumb" (just render what server says)
- WebSocket for real-time communication

**Instance-Based (Like Diablo):**
- Create party → Get private dungeon instance
- Invite friends only (no random griefing)
- Dungeon persists until party disbands

**Chat System:**
- In-game `/chat` integrated in UI
- Quick commands (`/heal me`, `/wait`, `/ready`)
- Coordination is key

---

## Extra Stuff #3: Meta-Progression

### Legacy Vault System

**The Problem It Solves:**
- Roguelikes are HARD
- New players get discouraged
- Veterans want prestige for skill

**The Solution: Street Cred System**

**Legacy Ore:**
- Very rare (1-2% spawn chance)
- Exceptional quality (95-100 stats)
- Has unique name and lore
- **Survives death** → Saved to Legacy Vault

**Examples:**
```
STARFORGED IRON
  Hardness: 98, Purity: 97
  "Iron from a fallen star, never dulls"
  Crafts: Starforged Blade (+15 dmg, unbreakable)

MOONSILVER MITHRIL
  Conductivity: 99, Purity: 96
  "Mined from ancient moon temple ruins"
  Crafts: Moonsilver Staff (+60% spell power)

DRAGONBONE ADAMANTITE
  Hardness: 96, Conductivity: 95, Purity: 98
  "Infused with dragon essence"
  Crafts: Dragonbone Bow (elemental shots)
```

**At Game Start: Choose Your Path**
```
┌─ NEW GAME ─────────────────────────────┐
│ Choose your path:                      │
│                                        │
│ [P] Pure Run (street cred!)           │
│     → Start with nothing              │
│     → Victory = "Pure Victory" badge  │
│     → Maximum respect                 │
│                                        │
│ [L] Legacy Kit                        │
│     → Craft from Legacy Vault         │
│     → Easier run                      │
│     → No street cred                  │
│     → Still tracked separately        │
└────────────────────────────────────────┘
```

**Victory Types:**

**Pure Victory:**
```
════════════════════════════════════════
        🏆 PURE VICTORY! 🏆
════════════════════════════════════════
  You defeated the dungeon without
  relying on Legacy gear!

  Street Cred: MAXIMUM
  Badge: "Purist" ⭐⭐⭐

  Bragging Rights: EARNED
════════════════════════════════════════
```

**Legacy Victory:**
```
════════════════════════════════════════
        ⚔️ LEGACY VICTORY ⚔️
════════════════════════════════════════
  You defeated the dungeon with help
  from Legacy gear.

  Legacy Kit Used:
    • Starforged Blade

  Street Cred: Low
  (But hey, you won!)
════════════════════════════════════════
```

**Why This Works:**
- New players: Use Legacy gear to learn, eventually try pure
- Veterans: Pure runs for prestige
- Everyone: Collecting all unique Legacy Ores is fun
- No pressure: Choice at game start
- Community: "I beat it pure!" vs "Working toward my first pure win"

### Player Stats Tracking

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
  Deepest Floor Reached: 12

  Highest Quality Ore Found:
    Iron (H:98)
    Mithril (C:99)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BADGES EARNED:
  ⭐ First Pure Victory
  💎 Legendary Hunter (found all Legacy Ore)
  🔨 Master Crafter (all recipes)
```

---

## Technical Architecture (Simplified)

### Phase 1: Single-Player MVP (4-6 weeks)

**Tech Stack:**
- Python 3.10+
- Textual (terminal UI framework)
- SQLite (local persistence)
- No network code yet

**What You Build:**
```
src/
├── core/
│   ├── game.py           # Game loop
│   ├── entities.py       # Player, monsters
│   └── world.py          # Map, dungeons
├── systems/
│   ├── combat.py         # Fight mechanics
│   ├── mining.py         # Ore veins, properties
│   └── crafting.py       # Recipes, stats
├── generation/
│   ├── mapgen.py         # BSP dungeon
│   └── spawning.py       # Monsters, ore
└── ui/
    └── textual/
        ├── app.py        # Main Textual app
        └── widgets/      # Map, status, inventory
```

**Playable in 4-6 weeks:**
- Solo dungeon crawling
- Mining/crafting system
- Legacy Vault
- Death/restart

### Phase 2: Multiplayer (3-6 months)

**Additional Tech:**
- WebSocket server (Python `websockets`)
- PostgreSQL (shared state)
- NATS (optional, for multiple servers)
- nginx (tia-proxy for routing)

**What You Add:**
```
server/
├── game_server.py        # WebSocket server
├── game_instance.py      # Instance manager
└── persistence.py        # Database layer

client/
└── network.py            # Network layer for Textual
```

**Architecture:**
- Server-authoritative (clients are dumb)
- Instance-based (Diablo model)
- Personal loot from shared ore
- 4-player simultaneous turns

---

## Development Roadmap

### Phase 1: Single-Player MVP (4-6 weeks)

**Week 1-2: Core Roguelike**
- [x] Textual UI setup (already done)
- [ ] Movement + combat
- [ ] Map generation (BSP)
- [ ] Basic monsters (3-5 types)
- [ ] Death/restart
- **Milestone:** Playable basic roguelike

**Week 3-4: Mining/Crafting**
- [ ] Ore vein generation
- [ ] Mining mechanic (vulnerable turns)
- [ ] Ore properties (5 stats)
- [ ] Crafting system
- [ ] Recipe discovery
- **Milestone:** Resource hunting loop works

**Week 5-6: Meta-Progression**
- [ ] Legacy Vault system
- [ ] Legacy Ore spawns (rare)
- [ ] Pure vs Legacy tracking
- [ ] Stats/badges
- **Milestone:** Meta-progression complete, MVP DONE

### Phase 2: Multiplayer Expansion (3-6 months)

**Month 1: Networking**
- [ ] WebSocket server
- [ ] Client network layer
- [ ] State synchronization
- [ ] 2-player prototype
- **Milestone:** Two players can see each other

**Month 2: Game Systems**
- [ ] 4-player simultaneous turns
- [ ] Class system (4 classes)
- [ ] Personal loot system
- [ ] Chat integration
- **Milestone:** Full 4-player co-op works

**Month 3: Infrastructure**
- [ ] PostgreSQL persistence
- [ ] Instance management
- [ ] Party system
- [ ] tia-proxy deployment
- **Milestone:** Production-ready

### Phase 3: Polish & Content

- [ ] More ore types
- [ ] More recipes
- [ ] Boss fights
- [ ] More floors
- [ ] Balance tuning
- [ ] Community features

---

## Key Design Principles

### 1. Mechanical Over Narrative
- Quest is simple motivation, not the focus
- Gameplay loop is the star
- Replayability through randomization

### 2. Simple Rules, Complex Emergence
- "4 actions per round, anyone can take them" → infinite strategy
- Ore properties → thousands of combinations
- Personal loot → no fighting, yes trading

### 3. Accessibility + Mastery
- Legacy Vault: Accessible to new players
- Pure Victory: Mastery for veterans
- Both are valid, both are tracked

### 4. Social Play ("Bros")
- Multiplayer co-op, not competitive
- Invite friends, no randoms
- Help each other, trade loot
- Community sharing (ore spawns, strategies)

### 5. "One More Run" Factor
- Quick death/restart
- Always something new (procedural + ore RNG)
- Meta-progression (collecting Legacy Ore)
- Chasing perfect spawns

---

## What We Cut (From Previous Docs)

### ❌ Removed Systems

**Memory-Based Progression:**
- "Remember when Big Bro taught you..."
- Emotional skill unlocks
- Narrative-driven progression
- **Why:** Not the focus, mechanics > story

**Essence Mastery System:**
- 15 essence types (Elemental, Conceptual, Primal)
- Complex combination tables
- 5-level mastery progression
- Reality-shaping endgame
- **Why:** Too complex, wrong game

**Environmental Affinities:**
- Darkness/Water/Fire/Heights/Confined (5 types × 4 levels)
- 20 unlock paths
- **Why:** Too much for MVP, can add later

**Material Mastery:**
- 5-level progression per material
- "Create new materials" endgame
- **Why:** MMO-style grind, not roguelike

**12-Property Material System:**
- Duplicate of ore property system
- Balance, Grain, Luminance, Silence, etc.
- **Why:** Use 5-property system instead

### ✅ What We Kept (Consolidated)

**5-Property Ore System:**
- Hardness, Conductivity, Malleability, Purity, Density
- Clean 0-100 scale
- SWG-proven mechanic

**Weapon Growth (Simplified):**
- Weapons track kills → Bonus damage vs that type
- "Slain 15 dragons: +3 vs dragons"
- No emotional memories, just stats

**Legacy Vault:**
- Meta-progression
- Street cred system
- Collection game

**Simultaneous Turns:**
- Best multiplayer mechanic in all the docs
- Keep exactly as designed

---

## Success Metrics

### MVP Success (Single-Player)
- Game runs smoothly
- Core loop is engaging for 15+ minutes
- Death feels fair and educational
- Restart is quick and motivating
- Mining/crafting feels rewarding

### Multiplayer Success
- 4 players can connect and play
- Turn system feels responsive
- Personal loot = no fighting
- Chat works for coordination
- "Let's run it again!" factor

### Long-Term Success
- Players return for "one more run"
- Community forms around the game
- Pure Victories are celebrated
- Legacy Ore collecting is fun
- Bros help each other optimize builds

---

## Open Questions (To Resolve During Implementation)

### For MVP
1. **Ore visibility:** Visible from adjacent tiles or only when explored?
2. **Inventory weight:** Encumbrance system or no weight limit?
3. **Forge locations:** Fixed rooms or portable kit?
4. **Multi-ore crafting:** One ore per item or combine multiple?

### For Multiplayer
5. **Death mechanics:** Individual (spectate) or party wipe?
6. **Starting class:** Choose at start or develop through play?
7. **Voice chat:** In-game, external (Discord), or text only?
8. **Party size:** Fixed 4 or flexible 2-4?

---

## Conclusion

**Brogue is:**
- NetHack + SWG Mining + Multiplayer Co-op
- Mechanical roguelike with quest hook (save your bro)
- "Bros" playing together, hunting perfect ore spawns
- Street cred for Pure Victories, accessibility with Legacy Vault

**We want:**
- All the systems (mining, crafting, multiplayer, meta-progression)
- Simple rules, complex emergence
- Replayability through randomization
- Social play and community

**Implementation path:**
1. Single-player MVP (4-6 weeks)
2. Prove the core loop is fun
3. Add multiplayer (3-6 months)
4. Polish and expand

**This is the game. Let's build it.** 🎮⚔️
