# Brogue Multiplayer Co-Op Design

**Date:** 2025-10-21
**Session:** icy-temple-1021
**Status:** Design Phase
**Vision:** 4-player co-op dungeon crawling with class synergies and in-game chat

---

## 🎯 Core Vision

**Four adventurers, one dungeon:**
- Warrior (Red @) - Tank and damage
- Mage (Blue @) - Ranged magic DPS
- Rogue (Green @) - Stealth and criticals
- Healer (Yellow @) - Support and healing

**Gameplay:**
- Real-time movement with tactical pause
- In-game /chat for coordination
- Shared dungeon, individual inventories
- Class synergies and combos
- Shared Legacy Vault (party progression)

---

## 🏗️ Technical Architecture

### Option 1: Server-Client (Recommended)

```
┌─────────────────────────────────────────┐
│         Game Server (Python)            │
│  - Authoritative game state             │
│  - Turn processing                      │
│  - Monster AI                           │
│  - Loot distribution                    │
│  - Chat relay                           │
└─────────────────────────────────────────┘
           ↑  ↑  ↑  ↑
           │  │  │  │  WebSocket/TCP
           │  │  │  │
    ┌──────┘  │  │  └──────┐
    │         │  │         │
┌───▼───┐ ┌──▼──▼───┐ ┌───▼───┐
│Client │ │ Client  │ │Client │
│  P1   │ │   P2    │ │  P3   │
│ (Red) │ │ (Blue)  │ │(Green)│
└───────┘ └─────────┘ └───────┘
```

**Pros:**
- Authoritative (no cheating)
- Handles network issues gracefully
- Can have spectators
- Replay support

**Tech Stack:**
- Server: Python + asyncio + websockets
- Client: Existing Textual UI + network layer
- Protocol: JSON messages over WebSocket

### Option 2: Peer-to-Peer

```
┌─────────┐     ┌─────────┐
│ Player1 │────▶│ Player2 │
│  (Host) │◀────│         │
└─────────┘     └─────────┘
    ↕               ↕
┌─────────┐     ┌─────────┐
│ Player3 │────▶│ Player4 │
└─────────┘     └─────────┘
```

**Pros:**
- No server needed
- Lower latency
- Simpler deployment

**Cons:**
- Host disconnect = game over
- Harder to prevent cheating
- More complex state sync

**Recommendation:** Start with Server-Client for better UX

---

## ⚔️ Four-Player Class System

### Warrior (Red @)

**Role:** Tank & Melee DPS
- High HP pool (starts 20 HP vs 10)
- High defense
- Taunt ability (draw monster aggro)
- Cleave attack (hit multiple adjacent enemies)

**Ore Preferences:**
- High **Hardness** → More melee damage
- High **Density** → Better armor (weight doesn't matter)
- **Malleability** → Equipment lasts longer in battle

**Party Role:**
- Front-line fighter
- Protects squishier party members
- Holds chokepoints
- "I'll tank this room, you flank!"

### Mage (Blue @)

**Role:** Ranged Magic DPS
- Low HP (starts 8 HP)
- High spell damage
- AOE attacks (fireball, lightning)
- Crowd control (slow, freeze)

**Ore Preferences:**
- High **Conductivity** → Spell damage
- Low **Density** → Less casting fatigue
- **Purity** → Mana efficiency

**Party Role:**
- Damage from backline
- Clear clustered enemies
- Control dangerous situations
- "Stand back, I'll nuke them!"

### Rogue (Green @)

**Role:** Mobility & Critical Strikes
- Medium HP (starts 12 HP)
- Backstab multiplier (3x damage from behind)
- Stealth (become invisible, 5 turn cooldown)
- Trap detection & disarm

**Ore Preferences:**
- Balanced **Hardness/Conductivity** → Poison/elemental daggers
- High **Malleability** → Field repairs
- Low **Density** → Fast movement

**Party Role:**
- Flanking attacks
- Scout ahead (stealth)
- Disable traps
- Assassinate priority targets
- "I'll circle around and backstab!"

### Healer (Yellow @)

**Role:** Support & Healing
- Medium HP (starts 12 HP)
- Heal party members (ranged, costs mana)
- Buff allies (+defense, +damage)
- Resurrect (bring back dead players, 1/floor)

**Ore Preferences:**
- High **Conductivity** → Healing potency
- High **Purity** → Buff duration
- **Malleability** → Staff durability

**Party Role:**
- Keep party alive
- Buff before big fights
- Emergency resurrections
- "Stay in range, I'll keep you up!"

**Abilities:**
- **Heal (3 mana):** Restore 8 HP to target
- **Group Heal (8 mana):** Restore 5 HP to all within 5 tiles
- **Blessing (5 mana):** +2 defense for 10 turns
- **Resurrect (15 mana):** Revive dead player at 50% HP (1/floor)

---

## 🎮 Multiplayer Gameplay Mechanics

### Turn System: Hybrid Real-Time/Tactical

**Normal Mode:** Real-time with tick system
```
Every 0.5 seconds = 1 game tick
- Players move freely
- Monsters move on their tick
- Combat resolved instantly
- Fast-paced, action-oriented
```

**Tactical Pause:** Any player can pause
```
Player presses SPACE → Game pauses
- All players see pause state
- Can chat and plan
- Resume when host presses SPACE
- Perfect for "Wait, let me heal first!"
```

**Why Hybrid:**
- Casual exploration: Real-time feels good
- Boss fights: Pause to coordinate
- Best of both worlds

### Movement & Positioning

**Shared Map:**
- All 4 players on same dungeon
- Can see each other's positions
- Can't stack on same tile (push mechanic)

**Positioning Matters:**
```
     W M H    (Warrior front, Mage/Healer back)
       R      (Rogue flanking)

     ###OOO### (Monsters approach)
```

**Friendly Fire:** Optional toggle
- Default OFF (can't hurt party)
- Hardcore mode ON (AOE hits everyone)

### Combat Resolution

**Initiative:** All actions resolve in priority order
1. Player abilities (instant)
2. Player attacks (instant)
3. Monster attacks (on their tick)

**Damage Display:**
```
Red @ attacks Goblin for 6 damage!
Blue @ casts Fireball → 3 Orcs hit for 12 damage each!
Green @ backstabs Troll for 18 damage! (Critical!)
Yellow @ heals Red @ for 8 HP!
```

### Loot Distribution

**Option A: Need/Greed (Classic MMO)**
```
Iron Ore (H:78, C:23, P:82) drops!

[Warrior] NEED (hardness 78, good for me!)
[Mage]    PASS (low conductivity)
[Rogue]   GREED (might be useful)
[Healer]  PASS

→ Warrior wins (Need > Greed)
```

**Option B: Round-Robin**
```
Turn 1: Warrior picks first
Turn 2: Mage picks first
Turn 3: Rogue picks first
Turn 4: Healer picks first
→ Repeat

Fair but less flexible
```

**Option C: Free-for-All (Chaos!)**
```
First to pick it up gets it
Promotes fast reflexes
Can cause arguments ("I needed that!")
```

**Recommendation:** Start with Need/Greed, add others as options

### Chat System

**In-Game Chat:** Integrated into UI
```
┌─ CHAT ─────────────────────────────┐
│ [Red] Warrior: Pull back, low HP! │
│ [Yellow] Healer: Healing you now  │
│ [Blue] Mage: I'll freeze them     │
│ [Green] Rogue: Going stealth      │
└────────────────────────────────────┘

Type /say <message> to chat
or just: /I'll tank this room
```

**Quick Commands:**
```
/heal me     → "[Red] Requesting heal!"
/wait        → "[Red] Wait up!"
/ready       → "[Red] Ready!"
/pull        → "[Red] Pulling enemies!"
```

---

## 🏰 Dungeon Scaling for 4 Players

### Map Size
- Single-player: 80x24
- Multiplayer: 120x40 (bigger dungeon!)
- Rooms 2x larger to fit party

### Monster Count
- Single-player: 3-5 monsters per floor
- Multiplayer: 12-15 monsters per floor
- Spawn in groups (patrol packs)

### Monster Difficulty
- HP scaled 2x
- Damage scaled 1.5x
- More special abilities (AOE attacks, healing)

### Boss Fights
- Every 3 floors
- Requires coordination
- Multiple phases
- Drops guaranteed high-quality ore for everyone

**Example Boss:**
```
TROLL CHIEFTAIN (Floor 3 Boss)
  HP: 200
  Attacks: Cleave (hits 3 tiles), Ground Slam (AOE)

Strategy:
  - Warrior tanks face-to-face
  - Rogue flanks for backstabs
  - Mage nukes from range
  - Healer keeps everyone alive
```

---

## 💾 Shared Legacy Vault

### Party Progression

**Vault Shared Across Party:**
```
┌─ PARTY LEGACY VAULT ───────────────┐
│ Party: "The Dungeon Crawlers"      │
│ Members: Alice, Bob, Carol, Dave   │
│                                    │
│ Legacy Ore Collected: 5            │
│  [1] Starforged Iron (Alice found) │
│  [2] Moonsilver (Bob found)        │
│  [3] Void Crystal (Carol found)    │
│                                    │
│ Pure Victories: 1 ⭐⭐⭐           │
│ Legacy Victories: 3 ⚔️             │
└────────────────────────────────────┘
```

**Victory Types:**

**Pure Victory (Party):**
- No one uses Legacy gear
- Maximum street cred
- "Our party beat it pure!"

**Partial Legacy:**
- Some use Legacy, some don't
- Medium street cred
- Individual tracking

**Full Legacy:**
- Everyone uses Legacy gear
- Still tracked separately from Pure

### Party Persistence

**Party Creation:**
```
Create/Join Party
  Party Name: The Dungeon Crawlers
  Vault: Shared or Individual?

  [Alice] Warrior (host)
  [Bob]   Mage
  [Carol] Rogue
  [Dave]  Healer

  Start New Run? [Y/N]
```

**Session Management:**
- Can play with different parties
- Each party has own Legacy Vault
- Your individual stats tracked across all parties

---

## 🌐 Network Protocol Design

### Message Types

**Player Actions:**
```json
{
  "type": "player_move",
  "player_id": "warrior_alice",
  "from": [5, 10],
  "to": [6, 10],
  "timestamp": 1234567890
}

{
  "type": "player_attack",
  "player_id": "warrior_alice",
  "target": "monster_goblin_1",
  "damage": 8
}

{
  "type": "chat_message",
  "player_id": "mage_bob",
  "message": "I'll freeze them!"
}
```

**Server Updates:**
```json
{
  "type": "game_state",
  "tick": 1523,
  "players": [
    {"id": "warrior_alice", "pos": [6, 10], "hp": 18, "max_hp": 20},
    {"id": "mage_bob", "pos": [4, 10], "hp": 8, "max_hp": 8}
  ],
  "monsters": [
    {"id": "goblin_1", "pos": [10, 10], "hp": 4}
  ],
  "loot": [
    {"id": "ore_1", "pos": [12, 15], "type": "iron_ore"}
  ]
}
```

### Latency Handling

**Client-Side Prediction:**
- Player moves immediately on client
- Server validates and corrects if needed
- Smooth experience even with 100ms latency

**Lag Compensation:**
- Server timestamps all actions
- Resolves in order received (with timestamp priority)
- Rollback if major desync

**Disconnection Handling:**
```
Player disconnects →
  - Character stays in game (AI takes over)
  - Plays defensively (retreat, heal)
  - Can reconnect within 2 minutes
  - After 2 min: Character removed, loot distributed
```

---

## 🎨 UI Changes for Multiplayer

### Split Screen View (Optional)

**Single Screen (Recommended):**
```
┌────────────────────────────────────────────┐
│         DUNGEON MAP (Shared)               │
│  @ (Red)    @ (Yellow)                    │
│             @ (Blue)                       │
│       @ (Green)                            │
│                                            │
│  OOO (Monsters)                            │
└────────────────────────────────────────────┘
┌─ PARTY STATUS ──────────────────────────────┐
│ [Red] Warrior: 18/20 HP ████████░░         │
│ [Blue] Mage: 8/8 HP ████████████           │
│ [Green] Rogue: 10/12 HP ████████░          │
│ [Yellow] Healer: 12/12 HP ██████████       │
└────────────────────────────────────────────┘
┌─ CHAT ─────────────────────────────────────┐
│ [Red] Pull back, low HP!                   │
│ [Yellow] Healing you now                   │
└────────────────────────────────────────────┘
```

**Individual Inventory:**
- Each player has own inventory screen
- Can trade items (right-click → Trade)
- See party members' equipped gear

### Color Coding

**Player @ Symbols:**
- Red @ - Warrior
- Blue @ - Mage
- Green @ - Rogue
- Yellow @ - Healer

**Damage Numbers:**
- Red numbers - Physical damage
- Blue numbers - Magic damage
- Green numbers - Critical hits
- Yellow numbers - Healing

**Status Effects:**
- Borders around @ for buffs/debuffs
- Dim @ when stealthed (Rogue)
- Glowing @ when buffed (Healer blessing)

---

## 🚀 Implementation Roadmap

### Phase 1: Server Foundation
- [ ] Set up Python WebSocket server
- [ ] Implement game state synchronization
- [ ] Basic player connection/disconnection
- [ ] Chat relay system
- [ ] Test with 2 players locally

### Phase 2: Client Updates
- [ ] Network layer in Textual UI
- [ ] Show multiple @ symbols on map
- [ ] Party status panel
- [ ] Chat integration
- [ ] Connection status indicator

### Phase 3: Class System
- [ ] Implement 4 classes with unique abilities
- [ ] Healer healing mechanics
- [ ] Rogue stealth system
- [ ] Mage AOE spells
- [ ] Warrior taunt/cleave

### Phase 4: Combat & Scaling
- [ ] Multiplayer combat resolution
- [ ] Monster scaling (HP, damage, count)
- [ ] Loot distribution (Need/Greed)
- [ ] Boss encounters

### Phase 5: Party Progression
- [ ] Shared Legacy Vault
- [ ] Party stats tracking
- [ ] Pure vs Legacy victory types
- [ ] Achievement system

### Phase 6: Polish
- [ ] Reconnection handling
- [ ] Spectator mode
- [ ] Replay system
- [ ] Balance tuning
- [ ] Public server hosting

---

## ❓ Open Design Questions

### 1. Death Mechanics
- **Option A:** Individual death (wait for party to finish/revive)
- **Option B:** Party death (all die if any dies - hardcore!)
- **Option C:** Permadeath + spectate (watch party continue)

### 2. Dungeon Generation
- **Option A:** Generated when party created (everyone sees same dungeon)
- **Option B:** Generated per floor (procedural as you descend)
- **Option C:** Seed-based (share seed for same dungeon)

### 3. Voice Chat
- **Option A:** Text chat only (in-game /chat)
- **Option B:** Integrated voice (using Python audio)
- **Option C:** External (Discord, etc.)

### 4. Party Size
- **Option A:** Fixed 4 players (balanced around this)
- **Option B:** 2-4 players (scale difficulty)
- **Option C:** Solo with AI companions

### 5. PvP Mode
- **Option A:** Co-op only (no PvP)
- **Option B:** Optional PvP arena (post-dungeon)
- **Option C:** PvP-enabled servers (friendly fire always on)

### 6. Cross-Platform
- **Option A:** PC only (terminal/Textual)
- **Option B:** Web client (HTML5 canvas)
- **Option C:** Mobile support (touch controls)

---

## 🎯 Why This Works for Brogue

### Unique Selling Points

**1. Terminal Co-Op** - Rare in gaming!
- Text-based multiplayer is underexplored
- Nostalgic MUD/BBS vibes
- Low bandwidth requirements

**2. Class Synergies** - Tactical depth
- Must coordinate to survive
- Each class feels essential
- "We need a healer!"

**3. SWG-Inspired Ore** - Multiplayer enhances it!
```
[Blue] Mage: "I found 99 conductivity mithril!"
[Red] Warrior: "Nice! I need high hardness iron though"
[Yellow] Healer: "Anyone seen purity ore?"
[Green] Rogue: "I'll scout ahead for better spawns"
```

**4. Legacy Vault** - Shared progression
- Party bonds over collecting Legacy Ore
- "Remember when we found Starforged Iron on floor 2?"
- Builds community

**5. Accessibility** - SSH into server
- No graphics card needed
- Play from anywhere
- Lightweight networking

### Target Audience

**Primary:**
- Terminal enthusiasts
- Roguelike fans
- Co-op gamers
- Retro gaming communities

**Secondary:**
- Streamers (4-player runs entertaining!)
- Speed-runners (party coordination meta)
- Community servers (hosted dungeons)

---

## 📊 Technical Feasibility

### Current Codebase Readiness

**What We Have:**
- ✅ Game loop (game.py)
- ✅ Turn system (process_turn)
- ✅ Entity management (Player, Monster)
- ✅ Map generation (BSP algorithm)
- ✅ Textual UI (working renderer)

**What We Need:**
- ❌ Network layer (WebSockets)
- ❌ Server architecture (authoritative state)
- ❌ Multi-player entities (4 players simultaneously)
- ❌ Chat system (integrated in UI)
- ❌ Synchronization (state updates)

### Estimated Complexity

**Network Layer:** Medium
- Python `websockets` library (well-documented)
- JSON protocol (simple)
- asyncio for async handling

**Server Logic:** Medium-High
- State management (track 4 players + monsters)
- Action validation (prevent cheating)
- Tick system (fair timing)

**Client Updates:** Low-Medium
- Textual already supports dynamic updates
- Add network message handling
- UI has room for party info

**Testing:** High
- Need 4 people to test properly
- Network edge cases (lag, disconnect)
- Balance (4-player combat tuning)

**Overall:** 3-4 weeks of focused development for MVP

---

## 🎮 Gameplay Example

**Party:** Alice (Warrior), Bob (Mage), Carol (Rogue), Dave (Healer)

```
Floor 3, approaching boss room...

[Red] Alice: "Boss door ahead. Everyone ready?"
[Yellow] Dave: "Mana full, got resurrect ready"
[Blue] Bob: "Let me buff before we go in"
[Green] Carol: "I'll stealth and check it out"

Carol presses 's' (stealth) → Green @ becomes dim
Carol moves into boss room...

Carol (in boss room): "It's a Troll Chieftain, 200 HP!"
[Green] Carol: "And 4 goblin adds. Focus adds first?"
[Red] Alice: "Yeah, I'll tank boss, you guys burn adds"

Party enters boss room...
<Boss music plays>

Alice moves to engage boss
Bob casts Fireball on goblin cluster → 3 goblins hit!
Dave casts Blessing on Alice → +2 defense
Carol backstabs weakened goblin → 18 damage! (Kill!)

Troll Chieftain uses Ground Slam → AOE damage!
[Red] Alice: 15 → 5 HP
[Blue] Bob: 8 → 3 HP
[Yellow] Dave: 12 → 7 HP
[Green] Carol: DODGED (stealth bonus)

[Red] Alice: "HEAL ME!"
Dave casts Heal on Alice → 5 → 13 HP

[Blue] Bob: "I'm low too!"
[Yellow] Dave: "Using group heal!"
Dave casts Group Heal → Everyone +5 HP

...fight continues...

TROLL CHIEFTAIN DEFEATED!

Loot drops:
  - Legacy Ore: DRAGONBONE ADAMANTITE!
  - Iron Ore (H:78)
  - Mithril Ore (C:85)
  - Health Potions x4

[Green] Carol: "I found the Legacy Ore!"
[Red] Alice: "YES! That's our 3rd piece!"
[Blue] Bob: "NEED on the Mithril" (high conductivity)
[Yellow] Dave: "GREED on the Iron"

Party continues to Floor 4...
```

---

## 🎯 Success Metrics

**Multiplayer MVP is successful if:**
1. 4 players can connect and play together
2. Real-time movement feels responsive (<100ms latency)
3. Combat is fair and synchronized
4. Chat works smoothly
5. Disconnection doesn't break the game
6. Players say "This is fun, let's run it again!"

**Long-term success:**
- Community servers emerge
- Twitch/YouTube content created
- Discord communities form around parties
- Speed-running meta develops
- Mod support (custom classes, dungeons)

---

## 🚀 Next Steps

### To Prototype:
1. **Create simple WebSocket server** (Python + websockets)
2. **Modify client to connect** (add network layer)
3. **Sync player positions** (2 players moving around)
4. **Add chat** (prove communication works)
5. **Test with friends** (validate it's fun!)

### To Validate:
- Is real-time + tactical pause the right feel?
- Do 4 classes feel distinct and necessary?
- Is the ore hunting fun with a party?
- Does Legacy Vault work with shared progression?

**Recommendation:** Build network prototype ASAP to validate the feel!

---

**Status:** Ready for prototyping
**Risk:** Medium (networking adds complexity)
**Reward:** High (unique game, strong community potential)

**Related Files:**
- Current code: `/home/scottsen/src/tia/projects/brogue/src/core/game.py`
- Mining design: `BROGUE_MINING_CRAFTING_DESIGN.md`
- Prior session: `explosive-beam-1021`

---

**The vision: Four colored @ symbols, coordinating via /chat, hunting for perfect ore spawns together, building their shared Legacy Vault, chasing that Pure Victory street cred as a party!** 🎮⚔️
