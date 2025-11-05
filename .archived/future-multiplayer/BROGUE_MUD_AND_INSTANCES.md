# Brogue: MUD Lessons & Diablo-Style Instances

**Date:** 2025-10-21
**Session:** icy-temple-1021
**Revelation:** "This is a MUD, right?" + "I like the Diablo mechanic - my map, invite friends"

---

## 🎮 Wait, This IS a MUD!

**User's realization: We've been designing a graphical MUD!**

### What's a MUD?

**MUD = Multi-User Dungeon**
- Text-based multiplayer RPGs
- Originated 1978 (MUD1 at University of Essex)
- Peaked in the 1990s
- Still running today (yes, really!)

**Core Features:**
- Terminal/text interface
- Dungeon crawling
- Real-time multiplayer
- Persistent worlds
- Classes, combat, loot
- Social systems (chat, guilds)

**Sound familiar?** That's literally what we've been designing!

---

## 🌍 MUDs Still Exist (And Thrive!)

### Active MUDs in 2025

**Achaea, Dreams of Divine Lands**
- Running since 1997 (28 years!)
- 500+ concurrent players at peak
- Complex class system (20+ classes)
- Player-run cities and politics
- Economy with player trading
- Regular updates, active devs

**Aetolia, The Midnight Age**
- Sister game to Achaea
- Vampire vs Undead themes
- Active RP community
- Persistent political systems

**Aardwolf**
- Running since 1996
- 200+ areas, 30,000+ rooms
- Active player base (~200 concurrent)
- Complex crafting system
- Frequent events

**BatMUD**
- Running since 1990 (35 years!)
- One of the longest-running MUDs
- Complex skill/stat system
- Hardcore difficulty
- Loyal community

**TEC (The Eternal City)**
- Historically-themed (Ancient Rome)
- Permadeath
- Intense RP focus
- Small but dedicated playerbase

**Threshold RPG**
- Running since 1996
- Focuses on storytelling
- Guild system (like classes)
- Achievement-based progression

### MUD Stats (2025)

- **Active MUDs:** ~200+ with regular players
- **Total MUDs ever created:** 1000s
- **Largest communities:** 300-500 concurrent players
- **Niche but stable:** Loyal playerbases, low churn

**Why they still exist:**
- Zero graphics = accessible anywhere (SSH in)
- Deep gameplay (30+ years of refinement)
- Strong communities (players know each other)
- Low bandwidth (works on terrible internet)
- Nostalgia factor (players from 90s still playing)

---

## 📚 30+ Years of MUD Design Lessons

### Lesson 1: Text Interface Isn't a Limitation

**What MUDs learned:**
- Text can convey complex information efficiently
- Good descriptions > flashy graphics
- Players' imagination fills gaps
- Terminal UIs can be beautiful (ASCII art, color)

**For Brogue:**
- Embrace the terminal aesthetic
- Use color strategically
- Clear, concise descriptions
- Let gameplay shine, not graphics

---

### Lesson 2: Community > Content

**What MUDs learned:**
- Players stay for the community
- Social features are critical
- Guilds/clans create retention
- Player-driven content > scripted content

**MUD social features that work:**
- Global chat channels
- Guild/clan systems
- Player housing
- In-game mail
- Player-run shops/economies
- Mentorship systems (veterans help newbies)

**For Brogue:**
- Make partying easy (friend invites)
- Guild system for Legacy Vault sharing
- In-game chat is CRITICAL
- Leaderboards (competitive community)
- Player trading (ore marketplace)

---

### Lesson 3: Persistence Creates Investment

**What MUDs learned:**
- Players invest in persistent characters
- Long-term progression keeps players
- BUT: Too much grind = burnout

**Successful progression systems:**
- Achaea: Skills improve with use (organic)
- Aardwolf: Achievement-based bonuses
- BatMUD: Complex multiclassing

**For Brogue:**
- Legacy Vault (persistent across deaths)
- Account-level achievements
- Character stats that persist
- But keep runs short (1-2 hours, not weeks)

---

### Lesson 4: Combat Needs Depth

**What MUDs learned:**
- Pure stat-based combat is boring
- Skills/abilities add strategy
- Class identity is crucial
- Combos and synergies = engagement

**MUD combat evolution:**
- Early: "kill goblin" (auto-attack)
- Mid: Skills and cooldowns
- Modern: Complex rotations, combos, positioning

**For Brogue:**
- We already have this! (4 classes, abilities)
- Turn allocation adds strategic layer
- Positioning matters (flanking, backstabs)
- Class synergies (tank/DPS/heal)

---

### Lesson 5: Economy Needs Sinks

**What MUDs learned:**
- Inflation destroys economies
- Need gold sinks (repairs, taxes, etc.)
- Player trading creates community
- BUT: Scams and exploits happen

**Successful MUD economies:**
- Repair costs (gold sink)
- Player shops (trading hub)
- Auction houses (transparent pricing)
- Crafting consumes materials (item sink)

**For Brogue:**
- Ore consumed when crafting (material sink)
- Repair costs for equipment (gold sink)
- Player trading (social interaction)
- Legacy Ore tradeable? (creates economy)

---

### Lesson 6: Permadeath Works (If Done Right)

**What MUDs learned:**
- Permadeath creates tension
- BUT: Total loss = rage quit
- Meta-progression softens the blow

**MUDs with permadeath:**
- TEC (The Eternal City): Full permadeath, RP-focused
- Players invest in stories, not stats
- Community mourns character deaths

**For Brogue:**
- Permadeath per run (roguelike)
- Legacy Ore persists (meta-progression)
- Pure Victory = street cred (opt-in hardcore)
- Resurrection ability (safety valve)

---

### Lesson 7: Accessibility Matters

**What MUDs learned:**
- Screen reader support is critical
- Text is accessible by default
- Colorblind-friendly color schemes
- Keybinds > mouse (for speed)

**For Brogue:**
- Terminal = screen reader compatible
- Color coding + symbols (colorblind mode)
- Full keyboard controls
- Configurable keybinds

---

### Lesson 8: Code Quality = Longevity

**What MUDs learned:**
- MUDs from 1990s still running
- Clean code survives decades
- Documentation critical
- Modular design allows updates

**MUD codebases:**
- DikuMUD, CircleMUD (C)
- LPMud (LPC language)
- RoM (ROM MUD - C)
- Evennia (Python! Modern MUD framework)

**For Brogue:**
- Python (readable, maintainable)
- Microservices (modular)
- Good documentation
- Open source (community can help)

---

### Lesson 9: Griefers Gonna Grief

**What MUDs learned:**
- PvP attracts griefers
- Need moderation tools
- Player reporting systems
- Temp bans > perma bans

**MUD anti-grief systems:**
- Safe zones (no PvP)
- Reputation systems
- Admin tools (kick, mute, ban)
- Player ignore lists

**For Brogue:**
- Co-op only (no PvP, less griefing)
- Kick player (party leader control)
- Report system (if public servers)
- Private instances (invite-only)

---

### Lesson 10: Updates Keep Players

**What MUDs learned:**
- Static games die
- Regular content updates critical
- Seasonal events create hype
- Balance patches show you care

**Achaea's model:**
- Monthly updates (new areas, features)
- Seasonal events (Halloween, Christmas)
- Class rebalancing
- Player suggestions implemented

**For Brogue:**
- New Legacy Ore types (seasonal)
- New classes (expansions)
- Balance patches (ore stats, class abilities)
- Community-driven content

---

## 🎮 Pivot: The Diablo Model

**User's insight: "I like the Diablo mechanic. My map. I can bring others onto my map and blow their minds (they get to keep loot drops!)."**

### This Changes EVERYTHING (For The Better!)

**Diablo/Path of Exile model:**
```
1. Player creates game (generates dungeon)
2. Invites friends to their instance
3. Everyone has their own loot drops
4. Host controls the instance
5. Leave and instance is gone (or saved)
```

**Why this is BETTER than persistent MMO:**
- ✅ Simpler to implement (no persistent world DB)
- ✅ No server costs (host runs instance)
- ✅ Private games (less moderation needed)
- ✅ No griefing (invite-only)
- ✅ Faster to market (MVP in weeks, not months)
- ✅ Scales naturally (each game is isolated)

---

## 🏗️ Diablo-Style Instance Design

### Game Creation Flow

```
┌─ CREATE GAME ──────────────────────┐
│ Host: Alice                        │
│                                    │
│ Dungeon Name: "Dragon Slayers"    │
│ Password: [optional]               │
│ Max Players: 4                     │
│ Difficulty: Normal / Hard / Pure   │
│                                    │
│ [Create] [Cancel]                  │
└────────────────────────────────────┘

Alice's game is created
  → Dungeon generated (seed: 1234567)
  → Alice can invite friends
  → Or make public (appears in lobby)
```

### Invite System

```
Alice (host):
  /invite Bob
  /invite Carol
  /invite Dave

Bob receives:
  "Alice invited you to 'Dragon Slayers'"
  [Join] [Decline]

Bob joins → Spawns in dungeon at safe room
  "Bob has joined the game!"
```

### Loot System: Diablo-Style

**Everyone gets their own loot!**

```
Goblin dies → Loot drops:

Server generates loot for EACH player:
  Alice: Iron Ore (H:78, C:45)
  Bob: Iron Ore (H:65, C:82)  ← Different stats!
  Carol: Health Potion
  Dave: Nothing (bad RNG)

Each player sees ONLY their own loot:
  Alice sees: "Iron Ore (H:78)" with Green highlight
  Bob sees: "Iron Ore (H:65)" with Green highlight
  Carol sees: "Health Potion" with Green highlight
  Dave sees: Nothing

No loot competition! No fighting over ore!
```

**Legacy Ore:**
```
Legacy Ore drops (rare!)

Server: One Legacy Ore for EVERYONE
  → All 4 players get "Starforged Iron" added to vault
  → Big announcement: "LEGACY ORE FOUND!"
  → Shared reward for party cooperation
```

### Instance Persistence

**Option 1: Session-Based (Diablo 2 style)**
```
Game exists while host is online
Host leaves → Game is destroyed
  → Progress lost (unless saved)

Pros: Simple, no storage needed
Cons: Must finish in one session
```

**Option 2: Saved Instances (Diablo 3 style)**
```
Game autosaves progress
Host can leave and resume later
Friends can rejoin saved game

Pros: Can take breaks, continue later
Cons: Need storage (save dungeon state)
```

**Option 3: Checkpoint System (Hybrid)**
```
Dungeon has checkpoints (every 3 floors)
Reach checkpoint → Progress saved
Can resume from last checkpoint

Pros: Balance of convenience + challenge
Cons: Need checkpoint implementation
```

**Recommendation:** Option 3 (checkpoints)

### Host Controls

```
Host has special powers:
  /kick <player>     → Remove player from game
  /pause             → Pause game (all players frozen)
  /save              → Save current state
  /difficulty hard   → Change difficulty mid-game
  /allow-join true   → Allow new players to join
```

### Public vs Private Games

**Private Game:**
```
Invite-only
Password protected (optional)
Appears in friends' "Joinable Games" list

Good for: Playing with known friends
```

**Public Game:**
```
Appears in public lobby
Anyone can join
Host can still kick griefers

Good for: Finding random party members
```

### Lobby System

```
┌─ PUBLIC GAMES ─────────────────────┐
│ Name              Host    Players  │
│ Dragon Slayers    Alice   3/4      │
│ Hardcore Run      Eve     2/4      │
│ Ore Farming       Frank   1/4      │
│ Newbie Friendly   Grace   4/4 FULL │
│                                    │
│ [Refresh] [Create Game]            │
└────────────────────────────────────┘

Click to join → Spawns in that instance
```

---

## 🎯 How This Fits Our Design

### Mining System: Perfect Fit!

**Diablo model solves loot competition:**

```
Party finds ore vein

Old model (shared loot):
  → Everyone races to mine it
  → First player gets it
  → Others frustrated

New model (instance loot):
  → Each player can mine it
  → Gets their own ore (different stats!)
  → Everyone happy

Example:
  Alice mines → Iron Ore (H:90! Amazing!)
  Bob mines → Iron Ore (H:45, meh)
  Carol mines → Iron Ore (H:78, good)
  Dave mines → Copper Ore (different type!)

Same vein, different loot for everyone!
```

**Mining feels collaborative, not competitive!**

### Legacy Ore: Shared Reward

```
Legacy Ore vein discovered

Server: Everyone gets the SAME Legacy Ore
  → "Starforged Iron" added to all 4 vaults
  → Encourages teamwork
  → Shared celebration moment
  → "We found it together!"

Creates bonding experience!
```

### Classes: Natural Party Formation

```
Creating game:
  Alice: Warrior
  Bob: Mage
  Carol: Rogue
  Dave: Healer

Balanced party ready to go!

Or:
  4 Warriors: "YOLO RUSH MODE"
  4 Healers: "We'll never die... but never kill anything"

Emergent strategies from composition
```

### Turn System: Works Perfectly

```
4 actions per round, hosted instance:
  → Host's server handles turn resolution
  → No latency issues (local or dedicated)
  → Clean implementation

Host disconnects:
  → Save state
  → Migrate to new host (seamless)
  → Or pause game, wait for reconnect
```

---

## 🏛️ Modern MUD Framework: Evennia

**If we wanted to use existing MUD infrastructure:**

**Evennia (Python MUD framework)**
- Modern (actively maintained)
- Python (matches our stack!)
- WebSocket support (perfect for Textual client)
- Built-in admin tools
- Database abstraction
- Player account system

**Benefits:**
- Don't reinvent wheel (combat, commands, etc.)
- Proven at scale
- Active community
- Good documentation

**Drawbacks:**
- Learning curve (framework overhead)
- May be overkill for instances
- Designed for persistent worlds

**Verdict:** Good reference, but we can build lighter for instanced model

---

## 📊 Comparison: MUD vs Diablo Model

| Feature | Persistent MUD | Diablo Instances |
|---------|----------------|------------------|
| **World** | Single shared world | Private instances |
| **Players** | 100s simultaneously | 4-8 per instance |
| **Persistence** | World persists forever | Instance temporary |
| **Infrastructure** | Requires server 24/7 | Host-based or VPS |
| **Complexity** | High (world state) | Low (session state) |
| **Moderation** | Critical (public world) | Minimal (private) |
| **Cost** | $20-100/month | Free (host) or $5-20 |
| **Development** | 6+ months | 4-8 weeks |
| **Scaling** | Vertical (bigger server) | Horizontal (more instances) |
| **Community** | Single large community | Many small groups |

**For Brogue:** Diablo model wins!

---

## 🎮 Hybrid Model: Best of Both Worlds

**Combine MUD lessons with Diablo instances:**

### Hub Town (Persistent, MUD-style)

```
┌─────────────────────────────────────┐
│        BROGUE TOWN (HUB)            │
│  Persistent social space            │
│                                     │
│  - Chat with all online players    │
│  - Trade in marketplace             │
│  - Show off Legacy gear             │
│  - Form parties                     │
│  - Check leaderboards               │
│                                     │
│  Players: 47 online                 │
│  [Enter Dungeon] (creates instance) │
└─────────────────────────────────────┘
```

### Dungeon Runs (Instanced, Diablo-style)

```
Party formed in hub → Create instance

┌─────────────────────────────────────┐
│      DUNGEON INSTANCE #42           │
│  Private to Alice's party           │
│                                     │
│  - Alice, Bob, Carol, Dave          │
│  - Own loot drops                   │
│  - Temporary (2 hour session)       │
│  - Can save at checkpoints          │
│                                     │
│  [Return to Town]                   │
└─────────────────────────────────────┘
```

**Benefits:**
- Social hub (MUD community feel)
- Private dungeons (Diablo loot system)
- Best of both worlds!

---

## 🚀 Implementation Path

### MVP: Pure Diablo Model (Simplest)

**Week 1-2:**
- Host creates game (local server)
- Friends connect via IP
- Instance-based dungeons
- Personal loot

**Week 3-4:**
- Add lobby (find public games)
- Save/load instances
- Checkpoint system

**Success:** Friends can party up and play!

### Phase 2: Add Hub (MUD Influence)

**Week 5-8:**
- Persistent hub town
- Global chat
- Trading marketplace
- Leaderboards

**Success:** Community forms!

### Phase 3: Full Social (MUD Features)

**Week 9-12:**
- Guild system
- Player housing (show off gear)
- Achievement system
- Seasonal events

**Success:** Players stick around long-term!

---

## 💡 Key Insights from MUDs

### What to Take:

✅ **Text interface works** - 30+ years prove it
✅ **Community > graphics** - Social features critical
✅ **Persistence creates investment** - Legacy Vault
✅ **Combat needs depth** - Classes, abilities, positioning
✅ **Economy needs balance** - Sinks and trading
✅ **Regular updates** - Keep players engaged
✅ **Accessibility** - Terminal = screen readers work

### What to Avoid:

❌ **Too much grind** - Keep runs 1-2 hours max
❌ **Stat bloat** - Keep progression meaningful
❌ **Pay-to-win** - Cosmetics only
❌ **Ignoring griefers** - Kick system + reports
❌ **Stale content** - Regular updates needed

---

## 🎯 Final Design: Diablo MUD Hybrid

**Core Experience:**

1. **Hub Town** (persistent, MUD-style)
   - Social space
   - Trading
   - Party formation

2. **Dungeon Instances** (temporary, Diablo-style)
   - Private parties (4 players)
   - Personal loot drops
   - Host-created

3. **Legacy Vault** (persistent, roguelite-style)
   - Meta-progression
   - Shared party rewards
   - Street cred tracking

**Why this works:**
- Social without griefing (private instances)
- Community without overhead (hub is lightweight)
- Loot without competition (everyone gets drops)
- Simple to build (instances are isolated)
- Scales naturally (more instances = more players)

---

## 📚 MUD Resources

**Active MUDs to Study:**
- Achaea.com - Modern MUD, great UX
- Aardwolf.com - Complex systems
- BatMUD.org - Hardcore difficulty

**MUD Development:**
- Evennia (Python framework)
- MudBytes.net (resources)
- r/MUD (active community)

**What to test:**
1. Play Achaea for 2 hours (see modern MUD UX)
2. Check their chat systems (guild, global, party)
3. Study their economy (player shops, trading)
4. Learn from 28 years of iteration

---

## ✅ Decision: Diablo-Style Instances + MUD Lessons

**Architecture:**
- Diablo: Instanced dungeons, host-based
- MUD: Hub town, social features, persistence

**Loot:**
- Diablo: Personal loot drops (everyone gets their own)
- MUD: Player trading in hub

**Progression:**
- Diablo: Runs are temporary
- MUD: Legacy Vault persists, achievements

**Social:**
- Diablo: Private parties (invite friends)
- MUD: Hub chat, guilds, community

**This is the best of both worlds!**

---

**User was right on both counts:**
1. "This is a MUD" → Yes! Learn from 30 years of design
2. "Diablo mechanic (my map, invite friends)" → Perfect fit!

Combining them = Unique game no one else has made! 🎮
